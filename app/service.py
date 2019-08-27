from pandas.io.json import json_normalize
import pandas as pd
import json
import pytz

import jaydebeapi
import sys
from datetime import datetime, timezone
import numpy as np

from querySolrAPI import queryInfoAll,queryInfoBetweenTimestampSPC0, queryMachinestate, queryLastSPC
from queryCollectorAPI import checkPing, checkConnect
from utils import praseJsonFormat, getDatetime, diffTime, getDatetimeFromUnix, transferTimezoneTPE
from model.response import initResponse, parseResponseJson, setErrorResponse
from log import logging

def queryLightStatus(data_collector):
    responseData = initResponse()
    result = {}
    result['status'] = ''
    pingStatus = ''
    connectionStatus = ''
    machineStatus = ''

    try:
        #list of data collector
        listOfCollector = ['A01', 'A03', 'A05', 'A06']
        if data_collector not in listOfCollector:
            result['lightColor'] = 'none'
            result['status'] = "no match machine id"
            responseData = setErrorResponse(responseData, '404', 'collector not found')
            return parseResponseJson(responseData, result)
        #先判斷是否ping的到
        try:
            pingStatus = checkPing(data_collector)
        except:
            logging.error("queryLightStatus exception --> ping fail ")
            result['lightColor'] = 'gray'
            result['status'] = result['status'] + "ping=fail; 請檢查控制器或網路"
            return parseResponseJson(responseData, result)
        if pingStatus == "False":
            result['lightColor'] = 'gray'
            result['status'] = result['status'] + "ping=fail; 請檢查控制器或網路"
            return parseResponseJson(responseData, result)
        else:
            result['status'] = result['status'] + "ping=success; "
        #再判斷是否連結的到collector
        try:
            connectionStatus = checkConnect(data_collector)
        except:
            #print("queryLightStatus exception --> connection fail ")
            result['lightColor'] = 'icon_disconnected'
            result['status'] = result['status'] + "connection=fail; 請檢查控制器"
            return parseResponseJson(responseData, result)
        if connectionStatus == "False":
            result['lightColor'] = 'icon_disconnected'
            result['status'] = result['status'] + "connection=fail; 請檢查控制器"
            return parseResponseJson(responseData, result)
        else:
            result['status'] = result['status'] + "connection=success; "
        #query machine status
        try:
            jsonObject = {}
            jsonObject = queryMachinestate('machinestatus')
            data = praseJsonFormat(jsonObject)
            # logging.info(data)
            if len(data) > 0:
                machineStatus = data[0]['MachineState']
                result['status'] = result['status'] + "machineStatus=" + machineStatus + "; "
            else:
                result['status'] = result['status'] + "machineStatus=none(no data)"
        except:
            logging.error('parse solr api response exception -> queryMachinestate')
            result['lightColor'] = 'none'  # parse solr api response exception
            result['status'] = result['status'] + "machineStatus=none(call solr api or parse response exception) -> queryMachinestate"
            return parseResponseJson(responseData, result)
        if machineStatus == "全自動":
            # 全自動才判斷生產狀態
            # query spc status
            # try:
            #     jsonObject = {}
            #     jsonObject = queryLastSPC("spc", data_collector)
            #     data = praseJsonFormat(jsonObject)
            #     if len(data) > 0:
            #         spc_0 = data[0]['SPC_0']
            #         result['status'] = result['status'] + "spc_0=" + str(spc_0) + "; "
            #         timestamp = data[0]['timestamp']
            #         spc_datetime = getDatetimeFromUnix(timestamp)
            #         result['status'] = result['status'] + "timestamp=" + spc_datetime.strftime("%Y/%m/%d %H:%M:%S")
            #         now = datetime.now().timestamp()
            #         if float(timestamp) + 300 < now:  # 超過5分鐘沒有生產 -> 待機中
            #             result['lightColor'] = 'icon_idle'
            #         else:
            #             result['lightColor'] = 'green'
            #     else:
            #         result['status'] = result['status'] + "spc_0=none(no data)"
            # except:
            #     logging.error('parse solr api response exception -> queryLastSPC')
            #     result['lightColor'] = 'none'  # parse solr api response exception
            #     result['status'] = result[
            #                            'status'] + "machineStatus=none(call solr api or parse response exception) -> queryLastSPC"
            #     return parseResponseJson(responseData, result)
            result['lightColor'] = 'green'
        else:
            result['lightColor'] = 'yellow'
        return parseResponseJson(responseData, result)
    except:
        logging.error("queryLightStatus exception")
        setErrorResponse(responseData, '400', 'exception')
        return parseResponseJson(responseData, result)

def genDailyReport(coreName, startTs, endTs):
    responseData = initResponse()
    result = {}
    result['status'] = ''
    responseStr = ''
    # list of data collector
    listOfCollector = ['A01', 'A03', 'A05', 'A06']
    validStartTime = ''
    validEndTime = ''
    try:
        # 轉換開始時間與結束時間
        try:
            validStartTime = getDatetime(startTs)
            validEndTime = getDatetime(endTs)
        except ValueError:
            logging.error(validStartTime + '-' + validEndTime + ' time format invalid, check start time and end time format: %Y/%m/%d %H:%M:%S')
            responseData = setErrorResponse(responseData, '400', 'time format invalid, check start time and end time format: %Y/%m/%d %H:%M:%S')
            return parseResponseJson(responseData, result)
        responseStr = responseStr + "[數據採集回報 " + validStartTime.strftime("%Y/%m/%d %H:%M:%S")\
                      + " - " + validEndTime.strftime("%Y/%m/%d %H:%M:%S") + "]\n"

        try:
            for machineId in listOfCollector:
                response = queryInfoBetweenTimestampSPC0(coreName, machineId, validStartTime, validEndTime)
                doc = praseJsonFormat(response)
                df = pd.DataFrame(doc)

                responseStr = responseStr +  "*" +  machineId + "\n"
                responseStr = responseStr + " **數據:\n"
                if df.empty:
                    logging.info(coreName + ":" + startTs + '-' + endTs + ' DataFrame is empty!')
                    # result['spc_breakoff'] = ['no data']
                    # result['spc_over_30_timestamp'] = ['no data']
                    # result['lastest_spc'] = ['no data']
                    # return parseResponseJson(responseData, result)
                    responseStr = responseStr + '   此區間沒有數據產生\n'

                else:
                    df.loc[:, 'SPC_0_previous'] = df['SPC_0']
                    # shift 是往下移一個
                    df['SPC_0_previous'] = df['SPC_0_previous'].shift(1).fillna('-1').astype(int)
                    df.loc[:, 'timestamp_previous'] = df['timestamp'].shift(1).fillna(-1).astype(float)
                    #for顯示使用
                    #df.loc[:, 'timestamp_view_temp'] = df['timestamp'].str.replace('\.', '').str.ljust(16, '0')
                    df.loc[:, 'timestamp_view_temp'] = df['timestamp_iso'].str.replace('T', ' ').str.replace('Z', '').astype(str)

                    # df.loc[:, 'timestamp_view'] = pd.to_datetime(df['timestamp_view_temp'], unit='us',errors='coerce')\
                    #     .dt.strftime('%H:%M:%S')

                    df.loc[:, 'timestamp_view'] = pd.to_datetime(df['timestamp_view_temp'], errors='coerce').dt.strftime('%H:%M:%S')

                    #last
                    # df.loc[:, 'timestamp_view_last'] = pd.to_datetime(df['timestamp_view_temp'], unit='s', errors='coerce') \
                    #     .dt.strftime('%m/%d %H:%M:%S')
                    df.loc[:, 'timestamp_view_last'] = pd.to_datetime(df['timestamp_view_temp'], errors='coerce').dt.strftime('%m/%d %H:%M:%S')

                    #date
                    # df.loc[:, 'timestamp_view_date'] = pd.to_datetime(df['timestamp_view_temp'], unit='s', errors='coerce') \
                    #     .dt.strftime('%m/%d')
                    df.loc[:, 'timestamp_view_date'] = pd.to_datetime(df['timestamp_view_temp'], errors='coerce').dt.strftime('%m/%d')

                    df.loc[:, 'timestamp_view_date_previous'] = df['timestamp_view_date'].shift(1).fillna('-1')

                    # df.loc[:, 'timestamp_iso_previous'] = df['timestamp_iso'].shift(1).fillna(-1).astype(str)
                    # df['timestamp_iso_previous'] = pd.to_datetime(df['timestamp_iso_previous'], errors='coerce').dt.strftime('%H:%M:%S')
                    df.loc[:, 'timestamp_view_previous'] = df['timestamp_view'].shift(1).fillna('-1')
                    # print(df[['timestamp_view', 'timestamp']])
                    # 1.目前最新模次與timestamp
                    df_lastest = df.iloc[-1:].astype(str)
                    lastTime = df_lastest['timestamp'].values[0]
                    lastTimeStr = df_lastest['timestamp_view_last'].values[0]
                    # result['lastest_spc'] = df_lastest['SPC_0'].values[0] + '(' + df_lastest['timestamp_iso'].values[0] + ')'
                    responseStr = responseStr + '(1)目前最新模次與時間:\n'

                    tDelta = diffTime(getDatetimeFromUnix(lastTime), validEndTime)
                    if tDelta < 60:
                        responseStr = responseStr + '   生產中，'
                    else:
                        responseStr = responseStr + '   停止生產，'


                    lastSPC = df_lastest['SPC_0'].values[0] + '(' + lastTimeStr + ')'
                    responseStr = responseStr + lastSPC + '\n'

                    # 2.檢查中斷模次
                    df.loc[:, 'SPC_0_previous_add1'] = df['SPC_0_previous'] + 1
                    df_broken_spc_0 = df[df['SPC_0_previous_add1'] != df['SPC_0']]
                    # remove first row
                    df_broken_spc_0 = df_broken_spc_0.iloc[1:]

                    # df_broken_spc_0.loc[:, 'SPC_0_break'] = \
                    #     df_broken_spc_0['SPC_0_previous'].astype(str) + '(' + df_broken_spc_0['timestamp_previous'].astype(str) + ')' \
                    #     + '->' + df_broken_spc_0['SPC_0'].astype(str) + '(' + df_broken_spc_0['timestamp'].astype(str) + ')'

                    # df_broken_spc_0.loc[:, 'SPC_0_break'] = \
                    #     df_broken_spc_0['SPC_0_previous'].astype(str) + '(' + df_broken_spc_0['timestamp_iso_previous'].astype(str) + ')' \
                    #     + '->' + df_broken_spc_0['SPC_0'].astype(str) + '(' + df_broken_spc_0['timestamp_iso'].astype(str) + ')'

                    df_broken_spc_0.loc[:, 'SPC_0_break'] = \
                        df_broken_spc_0['SPC_0_previous'].astype(str) \
                        + ' -> ' + df_broken_spc_0['SPC_0'].astype(str)

                    #中斷模次
                    #result['spc_breakoff'] = df_broken_spc_0['SPC_0_break'].tolist()
                    responseStr = responseStr + '(2)中斷模次:\n'
                    spc_0_break_list = df_broken_spc_0['SPC_0_break'].tolist()
                    if len(spc_0_break_list) == 0:
                        responseStr = responseStr + '   無\n'
                    for spc_0_break in spc_0_break_list:
                        responseStr = responseStr + '   ' + spc_0_break + '\n'

                    # 3.檢查模次與模次之前timestamp超過1分鐘
                    df['timestamp_previous_add60'] = df['timestamp_previous'] + 60
                    df_broken_timestamp = df[df['timestamp'].astype(float) > df['timestamp_previous_add60']]
                    # remove first row
                    if df_broken_timestamp.size > 1:
                        df_broken_timestamp = df_broken_timestamp.iloc[1:]

                        # df_broken_timestamp.loc[:, 'SPC_0_break_timestamp'] = \
                        #     df_broken_timestamp['SPC_0_previous'].astype(str) + '(' + df_broken_timestamp['timestamp_previous'].astype(str) +')' \
                        #     + '->' + df_broken_timestamp['SPC_0'].astype(str) + '(' + df_broken_timestamp['timestamp'].astype(str) +')'

                        df_broken_timestamp.loc[:, 'SPC_0_break_timestamp'] = \
                            df_broken_timestamp['SPC_0_previous'].astype(str) + '(' + df_broken_timestamp[
                                'timestamp_view_previous'].astype(str) + ')'\
                            + ' -> ' + df_broken_timestamp['SPC_0'].astype(str) + '(' + df_broken_timestamp[
                                'timestamp_view'].astype(str) + ')'

                    #result['spc_over_30_timestamp'] = df_broken_timestamp['SPC_0_break_timestamp'].tolist()
                    responseStr = responseStr + '(3)模次與模次之間時間超過1分鐘:\n'
                    firstDate = ''
                    df_broken_timestamp_first = ''
                    # spc_0_break_timestamp_list = df_broken_timestamp['SPC_0_break_timestamp'].tolist()
                    spc_0_break_timestamp_list = df_broken_timestamp[['SPC_0_break_timestamp', 'timestamp_view_date', 'timestamp_view_date_previous']].values.tolist()
                    if len(spc_0_break_timestamp_list) == 0:
                        responseStr = responseStr + '   無\n'
                    else:
                        df_broken_timestamp_first = df_broken_timestamp.iloc[0].astype(str)

                    for spc_0_break_timestamp in spc_0_break_timestamp_list:
                        # responseStr = responseStr + '   ' + spc_0_break_timestamp + '\n'
                        if firstDate == '':
                            firstDate = df_broken_timestamp_first['timestamp_view_date']
                            responseStr = responseStr + '   ' + firstDate + '\n'
                        elif spc_0_break_timestamp[1] != spc_0_break_timestamp[2]:
                            responseStr = responseStr + '   ' + spc_0_break_timestamp[1] + '\n'
                        responseStr = responseStr + '   ' + spc_0_break_timestamp[0] + '\n'
                        # print(df_broken_timestamp['SPC_0_break_timestamp'])
                        #print(df_broken_timestamp[['SPC_0', 'SPC_0_previous','timestamp_iso','timestamp_previous']].astype(str))
                        # print(df_broken_timestamp.dtypes)
                        # print(df_broken_timestamp.count())
                    # return parseResponseJson(responseData, result)


                responseStr = responseStr + '\n'
            return responseStr
        except:
            logging.error("genDailyReport exception")
            responseData = setErrorResponse(responseData, '400', 'exception')
            return parseResponseJson(responseData, result)
    except:
        logging.error("genDailyReport exception")
        responseData = setErrorResponse(responseData, '400', 'exception')
        return parseResponseJson(responseData, result)

def checkLastSPC(coreName, machineId):
    responseData = initResponse()
    result = {}
    result['status'] = ''
    responseStr = ''
    jsonObject = {}
    try:
        jsonObject = queryLastSPC(coreName, machineId)
        data = praseJsonFormat(jsonObject)
        logging.info(data)
        lastTimestamp = float(data[0]['timestamp'])
        #lastTimestamp = datetime.now().timestamp()
        nowSub60 = datetime.now().timestamp() - 60
        if lastTimestamp < nowSub60: #超過60秒
            return 0
        return 1
    except:
        logging.error("checkLastSPC exception")
        responseData = setErrorResponse(responseData, '400', 'exception')
        return parseResponseJson(responseData, result)

# def jdbcQuerySolrC():
#     responseData = initResponse()
#     result = {}
#
#     #try:
#         #jdbc_url = "jdbc:solr://localhost:9983?collection=test"
#     jdbc_url = "jdbc:solr://10.57.232.105:8983?core=spc"
#     driverName = "org.apache.solr.client.solrj.io.sql.DriverImpl"
#     statement = "select SPC_0 from spc limit 10"
#     conn = jaydebeapi.connect(driverName, jdbc_url)
#     curs = conn.cursor()
#     curs.execute(statement)
#     print(curs.fetchall())
#     conn.close()
#     sys.exit(0)
#     return parseResponseJson(responseData, result)
#     # except:
#     #     logging.error("jdbcQuerySolr exception")
#     #     responseData = setErrorResponse(responseData, '400', 'exception')
#     #     return parseResponseJson(responseData, result)