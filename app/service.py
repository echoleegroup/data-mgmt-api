# coding:utf-8
from pandas.io.json import json_normalize
import pandas as pd
import json
import pytz
import pika

#import jaydebeapi
import sys
from datetime import datetime, timezone
import numpy as np
import pysolr

from querySolrAPI import queryInfoAll,queryInfoBetweenTimestampSPC0, queryDCLogBetweenTimestamp, queryMachinestate, \
    queryLastSPC, queryAlarmrecord
from queryCollectorAPI import checkPing, checkConnect
from utils import praseJsonFormat, getDatetime, diffTime, getDatetimeFromUnix, getTotalRowsBetweenTwoTimestamp, convertDatetimeToString, insertBlockquote, insertTextIndent
from model.response import initResponse, parseResponseJson, setErrorResponse
from log import logging
from settings import PRODUCTION_DURING_SEC
from addSolrData import addLightStatusData

def queryLightStatus(data_collector, lightVersion, isInsert):
    responseData = initResponse()
    result = {}
    result['status'] = ''
    pingStatus = ''
    connectionStatus = ''
    machineStatus = ''
    # 紀錄lightstatus到solr
    lightstatusData = {}

    # dashboard light color
    if lightVersion == 'dashboard':
        pingFail = "gray"
        iconDisconnected = "icon_disconnected"
        iconIdle = "icon_idle"
        auto = "green"
        halfAutoOrManual = "yellow"
    # oee light color
    else:
        pingFail = "red"
        iconDisconnected = "gray"
        iconIdle = "yellow"
        auto = "green"
        halfAutoOrManual = "green"

    try:
        lightstatusData['machine_id'] = data_collector
        nowDatetime = datetime.now()
        nowTimestamp = int(nowDatetime.timestamp())
        lightstatusData['timestamp'] = nowTimestamp
        lightstatusData['id'] = data_collector + str(nowTimestamp)
        lightstatusData['timestamp_iso'] = nowDatetime.strftime("%Y-%m-%dT%H:%M:%SZ")

        #list of data collector
        listOfCollector = ['A01', 'A03', 'A05', 'A06']
        if data_collector not in listOfCollector:
            result['lightColor'] = 'none'
            result['status'] = "no match machine id"
            responseData = setErrorResponse(responseData, '404', 'collector machine_id not found')
            return parseResponseJson(responseData, result, 'result')

        #先判斷是否ping的到
        pingStatus = checkPing(data_collector)
        if pingStatus == "False":
            result['lightColor'] = pingFail
            result['status'] = result['status'] + "ping=fail; 請檢查控制器或網路"
            lightstatusData['light_color'] = pingFail
            if isInsert == True:
                addLightStatusData('lightstatus', data_collector, [lightstatusData])
            return parseResponseJson(responseData, result, 'result')
        else:
            result['status'] = result['status'] + "ping=success; "

        #再判斷是否連結的到collector
        connectionStatus = checkConnect(data_collector)
        if connectionStatus == "False":
            result['lightColor'] = iconDisconnected
            result['status'] = result['status'] + "connection=fail; 請檢查控制器"
            lightstatusData['light_color'] = iconDisconnected
            if isInsert == True:
                addLightStatusData('lightstatus', data_collector, [lightstatusData])
            return parseResponseJson(responseData, result, 'result')
        else:
            result['status'] = result['status'] + "connection=success; "

        # query machine status
        jsonObject = {}
        jsonObject = queryMachinestate('machinestatus')
        data = praseJsonFormat(jsonObject)
        if len(data) > 0:
            machineStatus = data[0]['MachineState']
            result['status'] = result['status'] + "machineStatus=" + machineStatus + "; "
        else:
            result['status'] = result['status'] + "machineStatus=none(no data)"

        if machineStatus == "全自動":
            # 全自動才判斷生產狀態
            # query spc status
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
                if float(timestamp) + PRODUCTION_DURING_SEC < now:  # 超過5分鐘沒有生產 -> 待機中
                    result['lightColor'] = iconIdle
                    lightstatusData['light_color'] = iconIdle
                else:
                    result['lightColor'] = auto
                    lightstatusData['light_color'] = auto
            else:
                result['status'] = result['status'] + "spc_0=none(no data)"
        else: #手動/半自動
            result['lightColor'] = halfAutoOrManual
            lightstatusData['light_color'] = halfAutoOrManual
        if isInsert == True:
            addLightStatusData('lightstatus', data_collector, [lightstatusData])
        if lightVersion == 'oee':
            # add machine status for TPM APP UI
            if result['lightColor'] == auto or result['lightColor'] == halfAutoOrManual:
                result['lightStatus'] = 'run'
            elif result['lightColor'] == pingFail:
                result['lightStatus'] = 'down'
            elif result['lightColor'] == iconDisconnected:
                result['lightStatus'] = 'issued'
            elif result['lightColor'] == iconIdle:
                result['lightStatus'] = 'idle'
        return parseResponseJson(responseData, result, 'result')
    except:
        logging.error("queryLightStatus exception")
        setErrorResponse(responseData, '400', 'exception')
        return parseResponseJson(responseData, result, 'result')

def transferDatetime(ts):
    validTime = ''
    try:
        if ts == '':
            validTime = datetime.now()
        else:
            validTime = getDatetime(ts, "%Y%m%d%H%M%S")
    except ValueError:
        return 'time format invalid, check start time and end time format: %Y/%m/%d %H:%M:%S'
    return validTime


def genDailyReport(startTs, endTs):
    br = '<br/>'
    responseData = initResponse()
    result = {}
    result['status'] = ''
    responseStr = ''
    # list of data collector
    listOfCollector = ['A01', 'A03', 'A05', 'A06']

    validStartTime = transferDatetime(startTs)
    validEndTime = transferDatetime(endTs)
    
    responseStr = responseStr + "[數據採集回報 " + validStartTime.strftime("%Y/%m/%d %H:%M:%S")\
                   + " - " + validEndTime.strftime("%Y/%m/%d %H:%M:%S") + "]" + br

    try:
        for machineId in listOfCollector:
            coreName = 'spc'
            spcRows = getTotalRowsBetweenTwoTimestamp(validStartTime, validEndTime, 10, 1)
            response = queryInfoBetweenTimestampSPC0(coreName, machineId, validStartTime, validEndTime, spcRows)
            doc = praseJsonFormat(response)
            df = pd.DataFrame(doc)

            responseStr = responseStr + machineId + br
            #query燈號狀態
            lightResponse = queryLightStatus(machineId)
            machineStatus = parseLightStatus(lightResponse)

            if df.empty:
                logging.info(coreName + "/" + machineId + ":" + startTs + '-' + validEndTime.strftime("%Y/%m/%d %H:%M:%S") + ' DataFrame is empty!')
                responseStr = responseStr + insertTextIndent('最新模次：' + machineStatus + '，' + '此區間沒有生產數據', '20', '1')
            else:
                df.loc[:, 'SPC_0_previous'] = df['SPC_0']
                # shift 是往下移一個
                df['SPC_0_previous'] = df['SPC_0_previous'].shift(1).fillna('-1').astype(int)
                df.loc[:, 'timestamp_previous'] = df['timestamp'].shift(1).fillna(-1).astype(float)

                #for顯示使用
                df.loc[:, 'timestamp_view_temp'] = df['timestamp_iso'].str.replace('T', ' ').str.replace('Z', '').astype(str)
                df.loc[:, 'timestamp_view'] = pd.to_datetime(df['timestamp_view_temp'], errors='coerce').dt.strftime('%H:%M:%S')

                #last
                df.loc[:, 'timestamp_view_last'] = pd.to_datetime(df['timestamp_view_temp'], errors='coerce').dt.strftime('%Y/%m/%d %H:%M:%S')

                #date
                df.loc[:, 'timestamp_view_date'] = pd.to_datetime(df['timestamp_view_temp'], errors='coerce').dt.strftime('%Y/%m/%d')
                df.loc[:, 'timestamp_view_date_previous'] = df['timestamp_view_date'].shift(1).fillna('-1')

                df.loc[:, 'timestamp_view_previous'] = df['timestamp_view'].shift(1).fillna('-1')

                # 最新模次
                df_lastest = df.iloc[-1:].astype(str)
                lastTime = df_lastest['timestamp'].values[0]
                lastTimeStr = df_lastest['timestamp_view_last'].values[0]
                lastSPC = lastTimeStr + '(' + df_lastest['SPC_0'].values[0] + ')'

                responseStr = responseStr + insertTextIndent('最新模次：' + machineStatus + '，' + lastSPC, '20', '1')

                #連線訊息
                dcCoreName = 'dc_event'
                dcRows = getTotalRowsBetweenTwoTimestamp(validStartTime, validEndTime, 3, 4)
                validStartTimeStr = convertDatetimeToString(validStartTime, "%Y-%m-%dT%H:%M:%SZ")
                validEndTimeStr = convertDatetimeToString(validEndTime, "%Y-%m-%dT%H:%M:%SZ")
                dcResponse = queryDCLogBetweenTimestamp(dcCoreName, machineId, validStartTimeStr, validEndTimeStr,
                                                        dcRows)
                dcDoc = praseJsonFormat(dcResponse)
                docDF = pd.DataFrame(dcDoc)

                if docDF.empty:
                    logging.info(dcCoreName + "/" + machineId + ":" + startTs + '-' + endTs + ' connection dataframe is empty!')
                else:
                    docFalseDF = docDF.where(docDF['result'] == False).dropna().drop_duplicates('timestamp').copy()
                    # for顯示使用
                    docFalseDF.loc[:, 'timestamp_view_temp'] = docFalseDF['timestamp'].str.replace('T', ' ').str.replace('Z', '').astype(str)

                    docFalseDF.loc[:, 'timestamp_view_month'] = pd.to_datetime(docFalseDF['timestamp_view_temp'],
                                                                      errors='coerce').dt.strftime('%Y/%m/%d %H:%M:%S')

                    if docFalseDF['result'].count() == 0:
                        logging.info('未發生斷線問題')
                    else:  # 發生斷線問題
                        docFirstDate = ''
                        lastIndex = 0
                        # 刪除下一筆連續中斷的連線
                        for index, row in docFalseDF.iterrows():
                            if lastIndex + 1 == index:
                                docFalseDF = docFalseDF.drop(index)
                            lastIndex = index
                        # 找出下一筆恢復連線
                        # shift 是往上移一個
                        docDF.loc[:, 'result_next'] = docDF['result'].shift(-1).astype(bool).copy()
                        docSameDF = docDF[(docDF['result_next'] != docDF['result'])]
                        # 紀錄下一個falseIndex
                        dict = {}
                        lastFalseIndex = 0
                        for index, row in docSameDF.iterrows():
                            if row['result_next'] == False:
                                lastFalseIndex = index + 1
                            elif lastFalseIndex != 0 | (lastFalseIndex == 0 & row['result'] == False): #第一筆是斷線的時候, 加入第一筆斷線的訊息到dict
                                dict[lastFalseIndex] = index + 1

                        for index, row in docFalseDF.iterrows():
                            responseStr = responseStr + insertTextIndent('中斷連線：' + row['timestamp_view_month'], '20', '0')
                            isFalseExist = index in dict
                            if isFalseExist == True:
                                if index != dict[index]:
                                    nextIndex = dict[index]
                                    docRow = docDF.ix[[nextIndex]].copy()
                                    docRowResult = docRow['result'].to_string(index=False)
                                    docRow.loc[:, 'timestamp_view_temp'] = docRow['timestamp'].str.replace('T',
                                                                                                           ' ').str.replace(
                                        'Z', '').astype(str)
                                    docRow.loc[:, 'timestamp_view_month'] = pd.to_datetime(
                                        docRow['timestamp_view_temp'],
                                        errors='coerce').dt.strftime('%Y/%m/%d %H:%M:%S')
                                    docRowMonth = docRow['timestamp_view_month'].to_string(index=False)
                                    responseStr = responseStr + insertTextIndent('恢復連線：' + docRowMonth, '20', '0')

                # 模次不連續
                df.loc[:, 'SPC_0_previous_add1'] = df['SPC_0_previous'] + 1
                df_broken_spc_0 = df[(df['SPC_0_previous_add1'] != df['SPC_0'])]
                # 多加一個條件, 排除停機後, spc_0跟上一筆相同的中斷模次
                df_broken_spc_0 = df_broken_spc_0[(df_broken_spc_0['SPC_0'] != df_broken_spc_0['SPC_0_previous']) | ((df_broken_spc_0['SPC_0'] == df_broken_spc_0['SPC_0_previous']) & (df_broken_spc_0['SPC_0'] != df_broken_spc_0['RD_618']))]
                responseStr = parseViewformat(df_broken_spc_0, responseStr, '模次不連續')

                # 模次時間超過五分鐘
                df['timestamp_previous_addInterval'] = df['timestamp_previous'] + int(PRODUCTION_DURING_SEC)
                df_broken_timestamp = df[df['timestamp'].astype(float) > df['timestamp_previous_addInterval']]
                responseStr = parseViewformat(df_broken_timestamp, responseStr, '模次生產時間超過5分鐘')

            responseStr = responseStr + br
        return responseStr
    except:
        logging.error("genDailyReport exception")
        responseData = setErrorResponse(responseData, '400', 'exception')
        return parseResponseJson(responseData, result, 'result')

def genDailyReportSimplification(startTs, endTs):
    br = '<br/>'
    responseData = initResponse()
    result = {}
    result['status'] = ''
    responseStr = ''
    # list of data collector
    listOfCollector = ['A01', 'A03', 'A05', 'A06']

    validStartTime = transferDatetime(startTs)
    validEndTime = transferDatetime(endTs)

    responseStr = responseStr + "[數據採集回報 " + validStartTime.strftime("%Y/%m/%d %H:%M:%S") \
                  + " - " + validEndTime.strftime("%Y/%m/%d %H:%M:%S") + "]" + br

    try:
        for machineId in listOfCollector:
            coreName = 'spc'
            spcRows = getTotalRowsBetweenTwoTimestamp(validStartTime, validEndTime, 10, 1)
            response = queryInfoBetweenTimestampSPC0(coreName, machineId, validStartTime, validEndTime, spcRows)
            doc = praseJsonFormat(response)
            df = pd.DataFrame(doc)

            responseStr = responseStr + machineId + br
            # query燈號狀態
            lightResponse = queryLightStatus(machineId)
            machineStatus = parseLightStatus(lightResponse)

            if df.empty:
                logging.info(coreName + "/" + machineId + ":" + startTs + '-' + validEndTime.strftime(
                    "%Y/%m/%d %H:%M:%S") + ' DataFrame is empty!')
                responseStr = responseStr + insertTextIndent('目前機台狀態：' + machineStatus + '，' + '此區間沒有生產數據', '20', '1')
            else:
                df.loc[:, 'SPC_0_previous'] = df['SPC_0']
                # shift 是往下移一個
                df['SPC_0_previous'] = df['SPC_0_previous'].shift(1).fillna('-1').astype(int)
                df.loc[:, 'timestamp_previous'] = df['timestamp'].shift(1).fillna(-1).astype(float)

                # for顯示使用
                df.loc[:, 'timestamp_view_temp'] = df['timestamp_iso'].str.replace('T', ' ').str.replace('Z',
                                                                                                         '').astype(str)
                df.loc[:, 'timestamp_view'] = pd.to_datetime(df['timestamp_view_temp'], errors='coerce').dt.strftime(
                    '%H:%M:%S')
                # last
                df.loc[:, 'timestamp_view_last'] = pd.to_datetime(df['timestamp_view_temp'],
                                                                  errors='coerce').dt.strftime('%m/%d %H:%M:%S')
                # date
                df.loc[:, 'timestamp_view_date'] = pd.to_datetime(df['timestamp_view_temp'],
                                                                  errors='coerce').dt.strftime('%m/%d')
                df.loc[:, 'timestamp_view_date_previous'] = df['timestamp_view_date'].shift(1).fillna('-1')

                df.loc[:, 'timestamp_view_previous'] = df['timestamp_view'].shift(1).fillna('-1')

                # 最新模次
                df_lastest = df.iloc[-1:].astype(str)
                lastTime = df_lastest['timestamp'].values[0]
                lastTimeStr = df_lastest['timestamp_view_last'].values[0]
                lastSPC = df_lastest['SPC_0'].values[0] + '(' + lastTimeStr + ')'

                responseStr = responseStr + insertTextIndent('目前機台狀態：' + machineStatus, '20', '1')
                responseStr = responseStr + insertTextIndent(lastSPC, '50', '1')

                # 生產模次間隔超過五分鐘
                df['timestamp_previous_addInterval'] = df['timestamp_previous'] + int(PRODUCTION_DURING_SEC)
                df_broken_timestamp = df[df['timestamp'].astype(float) > df['timestamp_previous_addInterval']]
                if df_broken_timestamp.size > 1:
                    filter_df = df_broken_timestamp.iloc[1:]
                    times_df = filter_df.groupby(["timestamp_view_date_previous"]).size().to_frame(name='count')
                    if times_df.size > 0:
                        responseStr = responseStr + insertTextIndent('生產模次間隔超過五分鐘：', '20', '1')
                        for index, row in times_df.iterrows():
                            responseStr = responseStr + insertTextIndent(index + ' 發生 ' + str(row['count']) + ' 次', '50', '1')

            responseStr = responseStr + br
        return responseStr
    except:
        logging.error("genDailyReport exception")
        responseData = setErrorResponse(responseData, '400', 'exception')
        return parseResponseJson(responseData, result, 'result')

def parseViewformat(df, responseStr, topic):
    # remove first row
    if df.size > 1:
        filter_df = df.iloc[1:]

        filter_df.loc[:, 'SPC_0_break'] = \
            filter_df['timestamp_view_previous'].astype(str) + '(' + filter_df['SPC_0_previous'].astype(
                str) + ')' \
            + ' -> ' + filter_df['timestamp_view'].astype(str) + '(' + filter_df['SPC_0'].astype(str) + ')'

    df_list = filter_df[['SPC_0_break', 'timestamp_view_date', 'timestamp_view_date_previous']].values.tolist()
    if len(df_list) == 0:
        logging.info('無' + topic)
    else:
        firstDate = ''
        # filter_df_first = ''
        responseStr = responseStr + insertTextIndent(topic + '：', '20', '1')
        filter_df_first = filter_df.iloc[0].astype(str)

        for df_row in df_list:
            if firstDate == '':
                firstDate = filter_df_first['timestamp_view_date_previous']
                responseStr = responseStr + insertTextIndent(firstDate, '50', '1')
            elif df_row[2] != firstDate:
                firstDate = df_row[2]
                responseStr = responseStr + insertTextIndent(df_row[1], '50', '1')
            responseStr = responseStr + insertTextIndent(df_row[0], '70', '1')
    return responseStr


def parseLightStatus(lightResponse):
    # query機台狀態
    data = json.loads(lightResponse)
    lightColor = data['result']['lightColor']
    machineStatus = ''
    if lightColor == 'green':
        machineStatus = '機台生產'
    elif lightColor == 'yellow':
        machineStatus = '機台調機'
    elif lightColor == 'gray':
        machineStatus = '機台未開機'
    elif lightColor == 'icon_disconnected':
        machineStatus = '機台未開機'
    elif lightColor == 'icon_idle':
        machineStatus = '機台待機'
    return machineStatus

#報警規則:
#Prometheus 1.最近一次生產超過五分鐘
def checkLastSPC(coreName, machineId):
    responseData = initResponse()
    result = {}
    result['status'] = ''
    responseStr = ''
    jsonObject = {}
    try:
        jsonObject = queryLastSPC(coreName, machineId)
        data = praseJsonFormat(jsonObject)
        lastTimestamp = float(data[0]['timestamp'])
        #lastTimestamp = datetime.now().timestamp()
        nowSub300 = datetime.now().timestamp() - PRODUCTION_DURING_SEC
        lastTimestampIso = data[0]['timestamp_iso'].replace('T', ' ').replace('Z', '')[:19]
        if lastTimestamp > nowSub300:
            return 1, lastTimestampIso #true, 小於5分鐘
        return 0, lastTimestampIso  # false, 超過5分鐘
    except:
        logging.error("checkLastSPC exception")
        responseData = setErrorResponse(responseData, '400', 'exception')
        return parseResponseJson(responseData, result, 'result')

#Prometheus 2.報警紀錄開始時間要大於上一筆
def checkAlarmrecordStartTime(coreName, machineId):
    responseData = initResponse()
    result = {}
    result['status'] = ''
    responseStr = ''
    jsonObject = {}
    try:
        jsonObject = queryAlarmrecord(coreName, machineId)
        data = praseJsonFormat(jsonObject)
        # logging.info(data)
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
        return parseResponseJson(responseData, result, 'result')

#Prometheus 3.報警紀錄模次亂跳/重複模次
def checkJumpAndDuplicatedRecordFromSPC(coreName, machineId):
    responseData = initResponse()
    result = {}
    result['status'] = ''
    responseStr = ''
    jsonObject = {}
    try:
        jsonObject = queryLastSPC(coreName, machineId)
        data = praseJsonFormat(jsonObject)
        # logging.info(data)
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
        return parseResponseJson(responseData, result, 'result')

#4.TPM/OEE alarm record報警
def checkAlarmrecordData(coreName, startTs, endTs):
    responseData = initResponse()
    alertList = []
    # result['status'] = ''
    responseStr = ''
    jsonObject = {}
    listOfCollector = ['A01', 'A03', 'A05', 'A06']

    validStartTime = transferDatetime(startTs)
    validEndTime = transferDatetime(endTs)
    validStartTimeStr = convertDatetimeToString(validStartTime, "%Y-%m-%dT%H:%M:%SZ")
    validEndTimeStr = convertDatetimeToString(validEndTime, "%Y-%m-%dT%H:%M:%SZ")
    timestamp = int(validEndTime.timestamp())
    rows = 5
    try:
        for machineId in listOfCollector:
            jsonObject = queryAlarmrecord(coreName, machineId, validStartTimeStr, validEndTimeStr, rows)
            data = praseJsonFormat(jsonObject)
            for row in data:
                alert = {}
                alert['header'] = '機台故障報警'
                alert['machineID'] = machineId
                # cc = row["Item"]
                alert['event'] = row["Item"]
                alert['startTime'] = row['StartTime']
                alert['stopTime'] = row['StopTime']
                alertList.append(alert)
        responseData['alertType'] = 'alarmrecord'
        responseData['alertCount'] = len(alertList)
        responseData['timestamp'] = timestamp
        return parseResponseJson(responseData, alertList, 'alert')
    except:
        logging.error("checkAlarmrecordStartTime exception")
        responseData = setErrorResponse(responseData, '400', 'exception')
        return parseResponseJson(responseData, alertList, 'alert')

#5.TPM/OEE machine idle報警
def checkMachineIdleData(coreName, nowTs):
    responseData = initResponse()
    alertList = []
    # result['status'] = ''
    responseStr = ''
    jsonObject = {}
    listOfCollector = ['A01', 'A03', 'A05', 'A06']

    validTime = transferDatetime(nowTs)
    validTimeStr = convertDatetimeToString(validTime, "%Y-%m-%dT%H:%M:%SZ")
    timestamp = int(validTime.timestamp())

    try:
        for machineId in listOfCollector:
            jsonObject = queryLastSPC(coreName, machineId)
            data = praseJsonFormat(jsonObject)

            for row in data:
                lastTimestamp = float(row['timestamp'])
                nowSub300 = timestamp - PRODUCTION_DURING_SEC
                lastTimestampIso = row['timestamp_iso'].replace('T', ' ').replace('Z', '')[:19]
                lastDatetime = datetime.strptime(lastTimestampIso, "%Y-%m-%d %H:%M:%S")
                if lastTimestamp < nowSub300: #生產時間超過5分鐘
                    diffTime = str(validTime - lastDatetime)
                    alert = {}
                    alert['header'] = '機台閒置報警'
                    alert['machineID'] = machineId
                    alert['event'] = '已閒置 ' + diffTime
                    alert['startTime'] = lastTimestampIso
                    alert['stopTime'] = ''
                    alertList.append(alert)
        responseData['alertType'] = 'machineidle'
        responseData['alertCount'] = len(alertList)
        responseData['timestamp'] = timestamp
        return parseResponseJson(responseData, alertList, 'alert')
    except:
        logging.error("checkAlarmrecordStartTime exception")
        responseData = setErrorResponse(responseData, '400', 'exception')
        return parseResponseJson(responseData, alertList, 'alert')
