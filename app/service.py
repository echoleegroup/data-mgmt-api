# coding:utf-8
from pandas.io.json import json_normalize
import pandas as pd
import json
import pytz

#import jaydebeapi
import sys
from datetime import datetime, timezone
import numpy as np

from querySolrAPI import queryInfoAll,queryInfoBetweenTimestampSPC0, queryDCLogBetweenTimestamp, queryMachinestate, \
    queryLastSPC, queryAlarmrecordStartTime
from queryCollectorAPI import checkPing, checkConnect
from utils import praseJsonFormat, getDatetime, diffTime, getDatetimeFromUnix, transferTimezoneTPE, getTotalRowsBetweenTwoTimestamp, convertDatetimeToString
from model.response import initResponse, parseResponseJson, setErrorResponse
from log import logging
from settings import PRODUCTION_DURING_SEC

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
            responseData = setErrorResponse(responseData, '404', 'collector machine_id not found')
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
            try:
                jsonObject = {}
                jsonObject = queryLastSPC("spc", data_collector)
                data = praseJsonFormat(jsonObject)
                if len(data) > 0:
                    spc_0 = data[0]['SPC_0']
                    result['status'] = result['status'] + "spc_0=" + str(spc_0) + "; "
                    timestamp_iso = data[0]['timestamp_iso']
                    timestamp = data[0]['timestamp']
                    result['status'] = result['status'] + "timestamp=" + timestamp_iso.replace('T', ' ').replace('Z', '')
                    now = datetime.now().timestamp()
                    if float(timestamp) + 300 < now:  # 超過5分鐘沒有生產 -> 待機中
                        result['lightColor'] = 'icon_idle'
                    else:
                        result['lightColor'] = 'green'
                else:
                    result['status'] = result['status'] + "spc_0=none(no data)"
            except:
                logging.error('parse solr api response exception -> queryLastSPC')
                result['lightColor'] = 'none'  # parse solr api response exception
                result['status'] = result[
                                       'status'] + "machineStatus=none(call solr api or parse response exception) -> queryLastSPC"
                return parseResponseJson(responseData, result)
        else:
            result['lightColor'] = 'yellow'
        return parseResponseJson(responseData, result)
    except:
        logging.error("queryLightStatus exception")
        setErrorResponse(responseData, '400', 'exception')
        return parseResponseJson(responseData, result)

def genDailyReport(startTs, endTs):
    responseData = initResponse()
    result = {}
    result['status'] = ''
    responseStr = ''
    # list of data collector
    listOfCollector = ['A01', 'A03', 'A05', 'A06']
    validStartTime = ''
    validEndTime = ''
    # 轉換開始時間與結束時間
    try:
        validStartTime = getDatetime(startTs, "%Y%m%d%H%M%S")
        validEndTime = getDatetime(endTs, "%Y%m%d%H%M%S")
    except ValueError:
        logging.error(validStartTime + '-' + validEndTime + ' time format invalid, check start time and end time format: %Y/%m/%d %H:%M:%S')
        responseData = setErrorResponse(responseData, '400', 'time format invalid, check start time and end time format: %Y/%m/%d %H:%M:%S')
        return parseResponseJson(responseData, result)
    responseStr = responseStr + "[數據採集回報 " + validStartTime.strftime("%Y/%m/%d %H:%M:%S")\
                  + " - " + validEndTime.strftime("%Y/%m/%d %H:%M:%S") + "]<br/>"

    try:
        for machineId in listOfCollector:
            coreName = 'spc'
            spcRows = getTotalRowsBetweenTwoTimestamp(validStartTime, validEndTime, 10, 1)
            response = queryInfoBetweenTimestampSPC0(coreName, machineId, validStartTime, validEndTime, spcRows)
            doc = praseJsonFormat(response)
            df = pd.DataFrame(doc)

            responseStr = responseStr +  "*" +  machineId + "<br/>"
            responseStr = responseStr + " **數據:<br/>"

            if df.empty:
                logging.info(coreName  + "/" + machineId + ":" + startTs + '-' + endTs + ' DataFrame is empty!')
                responseStr = responseStr + '   此區間沒有數據產生<br/>'

            else:
                df.loc[:, 'SPC_0_previous'] = df['SPC_0']
                # shift 是往下移一個
                df['SPC_0_previous'] = df['SPC_0_previous'].shift(1).fillna('-1').astype(int)
                df.loc[:, 'timestamp_previous'] = df['timestamp'].shift(1).fillna(-1).astype(float)

                #for顯示使用
                df.loc[:, 'timestamp_view_temp'] = df['timestamp_iso'].str.replace('T', ' ').str.replace('Z', '').astype(str)
                df.loc[:, 'timestamp_view'] = pd.to_datetime(df['timestamp_view_temp'], errors='coerce').dt.strftime('%H:%M:%S')

                #last
                df.loc[:, 'timestamp_view_last'] = pd.to_datetime(df['timestamp_view_temp'], errors='coerce').dt.strftime('%m/%d %H:%M:%S')

                #date
                df.loc[:, 'timestamp_view_date'] = pd.to_datetime(df['timestamp_view_temp'], errors='coerce').dt.strftime('%m/%d')
                df.loc[:, 'timestamp_view_date_previous'] = df['timestamp_view_date'].shift(1).fillna('-1')

                df.loc[:, 'timestamp_view_previous'] = df['timestamp_view'].shift(1).fillna('-1')

                # 一.數據檢查:
                # 1.目前最新模次與timestamp
                df_lastest = df.iloc[-1:].astype(str)
                lastTime = df_lastest['timestamp'].values[0]
                lastTimeStr = df_lastest['timestamp_view_last'].values[0]
                responseStr = responseStr + '(1)目前最新模次與時間:<br/>'

                tDelta = diffTime(getDatetimeFromUnix(lastTime), validEndTime)
                if tDelta < int(PRODUCTION_DURING_SEC):
                    responseStr = responseStr + '   生產中，'
                else:
                    responseStr = responseStr + '   停止生產，'

                lastSPC = df_lastest['SPC_0'].values[0] + '(' + lastTimeStr + ')'
                responseStr = responseStr + lastSPC + '<br/>'

                # 2.檢查中斷模次
                df.loc[:, 'SPC_0_previous_add1'] = df['SPC_0_previous'] + 1
                df_broken_spc_0 = df[(df['SPC_0_previous_add1'] != df['SPC_0'])]
                # 多加一個條件, 排除停機後, spc_0跟上一筆相同的中斷模次
                df_broken_spc_0 = df_broken_spc_0[ (df_broken_spc_0['SPC_0'] != df_broken_spc_0['SPC_0_previous']) | ((df_broken_spc_0['SPC_0'] == df_broken_spc_0['SPC_0_previous']) & (df_broken_spc_0['SPC_0'] != df_broken_spc_0['RD_618']))]

                # remove first row
                df_broken_spc_0 = df_broken_spc_0.iloc[1:]

                df_broken_spc_0.loc[:, 'SPC_0_break'] = \
                    df_broken_spc_0['SPC_0_previous'].astype(str) \
                    + ' -> ' + df_broken_spc_0['SPC_0'].astype(str)

                responseStr = responseStr + '(2)中斷模次:<br/>'
                spc_0_break_list = df_broken_spc_0['SPC_0_break'].tolist()
                if len(spc_0_break_list) == 0:
                    responseStr = responseStr + '   無<br/>'
                for spc_0_break in spc_0_break_list:
                    responseStr = responseStr + '   ' + spc_0_break + '<br/>'

                # 3.檢查模次與模次之前timestamp超過1分鐘
                df['timestamp_previous_add60'] = df['timestamp_previous'] + int(PRODUCTION_DURING_SEC)
                df_broken_timestamp = df[df['timestamp'].astype(float) > df['timestamp_previous_add60']]
                # remove first row
                if df_broken_timestamp.size > 1:
                    df_broken_timestamp = df_broken_timestamp.iloc[1:]

                    df_broken_timestamp.loc[:, 'SPC_0_break_timestamp'] = \
                        df_broken_timestamp['SPC_0_previous'].astype(str) + '(' + df_broken_timestamp[
                            'timestamp_view_previous'].astype(str) + ')'\
                        + ' -> ' + df_broken_timestamp['SPC_0'].astype(str) + '(' + df_broken_timestamp[
                            'timestamp_view'].astype(str) + ')'

                responseStr = responseStr + '(3)模次與模次之間生產時間超過1分鐘:<br/>'
                firstDate = ''
                df_broken_timestamp_first = ''
                spc_0_break_timestamp_list = df_broken_timestamp[['SPC_0_break_timestamp', 'timestamp_view_date', 'timestamp_view_date_previous']].values.tolist()
                if len(spc_0_break_timestamp_list) == 0:
                    responseStr = responseStr + '   無<br/>'
                else:
                    df_broken_timestamp_first = df_broken_timestamp.iloc[0].astype(str)

                for spc_0_break_timestamp in spc_0_break_timestamp_list:
                    if firstDate == '':
                        firstDate = df_broken_timestamp_first['timestamp_view_date_previous']
                        responseStr = responseStr + '   ' + firstDate + '<br/>'
                    elif spc_0_break_timestamp[2] != firstDate:
                        firstDate = spc_0_break_timestamp[2]
                        responseStr = responseStr + '   ' + spc_0_break_timestamp[1] + '<br/>'
                    responseStr = responseStr + '   ' + spc_0_break_timestamp[0] + '<br/>'


            # 二、連線檢查:
            dcCoreName = 'dc_event'
            dcRows = getTotalRowsBetweenTwoTimestamp(validStartTime, validEndTime, 3, 4)
            validStartTimeStr = convertDatetimeToString(validStartTime, "%Y-%m-%dT%H:%M:%SZ")
            validEndTimeStr = convertDatetimeToString(validEndTime, "%Y-%m-%dT%H:%M:%SZ")
            dcResponse = queryDCLogBetweenTimestamp(dcCoreName, machineId, validStartTimeStr, validEndTimeStr, dcRows)
            dcDoc = praseJsonFormat(dcResponse)
            docDF = pd.DataFrame(dcDoc)

            responseStr = responseStr + " ** 連線:<br/>"
            if docDF.empty:
                logging.info(dcCoreName + "/" + machineId + ":" + startTs + '-' + endTs + ' 連線資訊 is empty!')
                responseStr = responseStr + '   此區間沒有連線紀錄<br/>'
            else:
                docFalseDF = docDF.where(docDF['result'] == False).dropna().drop_duplicates('timestamp')
                # for顯示使用
                docFalseDF.loc[:, 'timestamp_view_temp'] = docFalseDF['timestamp'].str.replace('T', ' ').str.replace('Z', '').astype(str)
                docFalseDF.loc[:, 'timestamp_view'] = pd.to_datetime(docFalseDF['timestamp_view_temp'], errors='coerce').dt.strftime('%H:%M:%S')
                # date
                docFalseDF.loc[:, 'timestamp_view_date'] = pd.to_datetime(docFalseDF['timestamp_view_temp'], errors='coerce').dt.strftime('%m/%d')

                if docFalseDF['result'].count() == 0:
                    responseStr = responseStr + " 未發生斷線問題<br/>"
                else:#發生斷線問題
                    docFirstDate = ''
                    lastIndex = 0
                    # 刪除下一筆連續中斷的連線
                    for index, row in docFalseDF.iterrows():
                        if lastIndex + 1 == index:
                            docFalseDF = docFalseDF.drop(index)
                        lastIndex = index
                    #找出下一筆恢復連線
                    for index, row in docFalseDF.iterrows():
                        docCurDate = row['timestamp_view_date']
                        docCurTimestamp = row['timestamp_view']
                        if docFirstDate == '':
                            docFirstDate = docCurDate
                            responseStr = responseStr + '   ' + docFirstDate + '<br/>'
                        elif docCurDate != docFirstDate:
                            docFirstDate = docCurDate
                            responseStr = responseStr + '   ' + docCurDate + '<br/>'
                        responseStr = responseStr + '   ' + docCurTimestamp + ' 連線中斷' +'<br/>'
                        nextIndex = index + 1
                        while index < nextIndex:
                            isExist = nextIndex in docDF.index
                            if isExist:
                                docRow = docDF.ix[[nextIndex]]
                                docRowResult = docRow['result'].to_string(index=False)
                                docRow.loc[:, 'timestamp_view_temp'] = docRow['timestamp'].str.replace('T', ' ').str.replace('Z', '').astype(str)
                                docRow.loc[:, 'timestamp_view'] = pd.to_datetime(docRow['timestamp_view_temp'],
                                                                                     errors='coerce').dt.strftime('%H:%M:%S')
                                docRowTimestamp = docRow['timestamp_view'].to_string(index=False)
                                #date
                                docRow.loc[:, 'timestamp_view_date'] = pd.to_datetime(
                                    docRow['timestamp_view_temp'], errors='coerce').dt.strftime('%m/%d')
                                docRowDate = docRow['timestamp_view_date'].to_string(index=False)

                                if docRowResult == 'True':
                                    # 日期
                                    if docRowDate != docFirstDate:
                                        docFirstDate = docRowDate
                                        responseStr = responseStr + '   ' + docRowDate + '<br/>'
                                    responseStr = responseStr + '   ' + docRowTimestamp + ' 恢復連線' + '<br/>'
                                    nextIndex = 0
                                else:
                                    nextIndex = nextIndex + 1
                            else:
                                break

            responseStr = responseStr + '<br/>'
        return responseStr
    except:
        logging.error("genDailyReport exception")
        responseData = setErrorResponse(responseData, '400', 'exception')
        return parseResponseJson(responseData, result)

#報警規則:
#1.最近一次生產超過五分鐘
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
        nowSub300 = datetime.now().timestamp() - 300
        lastTimestampIso = data[0]['timestamp_iso'].replace('T', ' ').replace('Z', '')[:19]
        if lastTimestamp > nowSub300:
            return 1, lastTimestampIso #true, 小於5分鐘
        return 0, lastTimestampIso  # false, 超過5分鐘
    except:
        logging.error("checkLastSPC exception")
        responseData = setErrorResponse(responseData, '400', 'exception')
        return parseResponseJson(responseData, result)

#2.報警紀錄開始時間要大於上一筆
def checkAlarmrecordStartTime(coreName, machineId):
    responseData = initResponse()
    result = {}
    result['status'] = ''
    responseStr = ''
    jsonObject = {}
    try:
        jsonObject = queryAlarmrecordStartTime(coreName, machineId)
        data = praseJsonFormat(jsonObject)
        logging.info(data)
        df = pd.DataFrame(data)

        df.loc[:, 'StartTime_previous'] = df['StartTime']
        # shift 是往下移一個
        df['StartTime_previous'] = df['StartTime_previous'].shift(-1).fillna('-1').astype(str)
        # 取第一筆
        df_lastest = df.iloc[0].astype(str)
        lastStartTime = df_lastest['StartTime']
        lastStartTimePrevious = df_lastest['StartTime_previous']
        RD_618 = df_lastest['RD_618']
        # lastStarTimeIso = data[0]['StartTime_iso'].replace('T', ' ').replace('Z', '')[:19]

        if lastStartTime > lastStartTimePrevious:
            return 1, RD_618  # true, 當前的starttime大於前一筆的starttime
        return 0, RD_618  # false, 當前的starttime小於前一筆的starttime
    except:
        logging.error("checkAlarmrecordStartTime exception")
        responseData = setErrorResponse(responseData, '400', 'exception')
        return parseResponseJson(responseData, result)

#3.報警紀錄模次亂跳/重複模次
def checkJumpAndDuplicatedRecordFromSPC(coreName, machineId):
    responseData = initResponse()
    result = {}
    result['status'] = ''
    responseStr = ''
    jsonObject = {}
    try:
        jsonObject = queryLastSPC(coreName, machineId)
        data = praseJsonFormat(jsonObject)
        logging.info(data)
        df = pd.DataFrame(data).iloc[0].astype(str)

        # 取第一筆
        timestamp_iso = df['timestamp_iso']
        RD_618 = df['RD_618']
        SPC_0 = df['SPC_0']

        if RD_618 == SPC_0:
            return 1, RD_618  # true, 模次正常
        return 0, RD_618  # false, 模次亂跳或是模次重複
    except:
        logging.error("checkJumpAndDuplicatedRecordFromSPC exception")
        responseData = setErrorResponse(responseData, '400', 'exception')
        return parseResponseJson(responseData, result)
