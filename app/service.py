from pandas.io.json import json_normalize
import pandas as pd
import json

from querySolrAPI import queryInfoAll,queryInfoBetweenTimestampSPC0, queryMachinestate
from queryCollectorAPI import checkPing, checkConnect
from utils import praseJsonFormat, parseResponseJson

def queryLightStatus(data_collector):
    try:
        responseData = {}
        responseData['responseCode'] = 200
        responseData['responseMessage'] = ''
        result = {}
        result['status'] = ''
        #先判斷是否ping的到
        pingStatus = checkPing()
        if pingStatus == "False":
            result['lightColor'] = 'Gray'
            result['status'] = result['status'] + "ping=fail; "
            return parseResponseJson(responseData, result)
        else:
            result['status'] = result['status'] + "ping=sucuess; "
        #再判斷是否連結的到collector
        connectionStatus = checkConnect()
        if connectionStatus == "False":
            result['lightColor'] = 'Icon'
            result['status'] = result['status'] + "connection=fail; "
            return parseResponseJson(responseData, result)
        else:
            result['status'] = result['status'] + "connection=sucuess; "
        #query machine status
        jsonObject = queryMachinestate('machinestatus')
        data = praseJsonFormat(jsonObject)
        machineStatus = data[0]['machinestate']
        # if machineStatus == '全自動':
        #     return 'automatic'
        # elif machineStatus == '半自動':
        #     return 'self-automatic'
        # else:
        #     return 'manual'
        result['status'] = result['status'] + "machineStatus=" + machineStatus
        if machineStatus == "全自動":
            result['lightColor'] = 'Green'
        else:
            result['lightColor'] = 'Yellow'
        return parseResponseJson(responseData, result)
    except:
        responseData['responseCode'] = 400
        responseData['responseMessage'] = 'except'
        return parseResponseJson(responseData, result)


def genDailyReport(coreName, startTs, endTs):
    response = queryInfoBetweenTimestampSPC0(coreName, startTs, endTs)
    doc = praseJsonFormat(response)
    # print(doc)
    df = pd.DataFrame(doc)
    print(df['spc_0'])
    # df.loc[:, 'spc_0_add'] = df['spc_0']+1
    # print(df[['spc_0', 'spc_0_add']])
    firstSpc = df['spc_0'][0]
    # lastSpc = df.iloc[-1:]
    lastSpc = 1082829

    print(firstSpc)
    print(lastSpc)
    #df.loc[:, 'spc_0_compare'] = firstSpc + 1

    return response

def checkConsecutiveSPC(response):
    return ""
