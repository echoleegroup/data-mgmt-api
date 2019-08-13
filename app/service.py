from pandas.io.json import json_normalize
import pandas as pd
import json

from querySolrAPI import queryInfoAll,queryInfoBetweenTimestampSPC0, queryMachinestate
from queryCollectorAPI import checkPing, checkConnect
from utils import praseJsonFormat
from model.response import initResponse, parseResponseJson, setErrorResponse

def queryLightStatus(data_collector):
    responseData = initResponse()
    result = {}
    result['status'] = ''
    # try:
    #先判斷是否ping的到
    pingStatus = checkPing(data_collector)
    if pingStatus == "False":
        result['lightColor'] = 'gray'
        result['status'] = result['status'] + "ping=fail; "
        return parseResponseJson(responseData, result)
    else:
        result['status'] = result['status'] + "ping=success; "
    #再判斷是否連結的到collector
    connectionStatus = checkConnect(data_collector)
    if connectionStatus == "False":
        result['lightColor'] = 'icon'
        result['status'] = result['status'] + "connection=fail; "
        return parseResponseJson(responseData, result)
    else:
        result['status'] = result['status'] + "connection=success; "
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
        result['lightColor'] = 'green'
    else:
        result['lightColor'] = 'yellow'
    return parseResponseJson(responseData, result)
    # except:
    #     print("queryLightStatus exception")
    #     setErrorResponse(responseData)
    #     return parseResponseJson(responseData, result)


def genDailyReport(coreName, startTs, endTs):
    responseData = initResponse()
    result = {}

    try:
        response = queryInfoBetweenTimestampSPC0(coreName, startTs, endTs)
        doc = praseJsonFormat(response)
        df = pd.DataFrame(doc)

        # 1.檢查中斷模次
        if df.empty:
            print('DataFrame is empty!')
            result['spc_breakoff'] = ['no data']
            result['spc_over_30_timestamp'] = ['no data']
            result['lastest_spc'] = ['no data']
            return parseResponseJson(responseData, result)

        df.loc[:, 'spc_0_previous'] = df['spc_0']
        # shift 是往下移一個
        df['spc_0_previous'] = df['spc_0_previous'].shift(1).fillna('-1').astype(int)
        df.loc[:, 'id_timestamp_previous'] = df['id_timestamp'].shift(1).fillna(-1).astype(float)

        df.loc[:, 'spc_0_previous_add1'] = df['spc_0_previous'] + 1
        df_broken_spc_0 = df[df['spc_0_previous_add1'] != df['spc_0']]
        # remove first row
        df_broken_spc_0 = df_broken_spc_0.iloc[1:]

        #df_broken_spc_0.loc[:, 'spc_0_break'] = df_broken_spc_0['spc_0_previous'].astype(str) + ' -> ' + df_broken_spc_0['spc_0'].astype(str)
        df_broken_spc_0.loc[:, 'spc_0_break'] = \
            df_broken_spc_0['spc_0_previous'].astype(str) + '(' + df_broken_spc_0['id_timestamp_previous'].astype(str) + ')' \
            + '->' + df_broken_spc_0['spc_0'].astype(str) + '(' + df_broken_spc_0['id_timestamp'].astype(str) + ')'

        #中斷模次
        #1080798-1080836 1080836-1080838 1081827-1081865 1081865-1081867 1082232-1082270

        result['spc_breakoff'] = df_broken_spc_0['spc_0_break'].tolist()

        # 2.檢查模次與模次之前timestamp超過三十秒
        df['id_timestamp_previous_add30'] = df['id_timestamp_previous'] + 30
        df_broken_timestamp = df[df['id_timestamp'].astype(float) > df['id_timestamp_previous_add30']]
        # remove first row
        df_broken_timestamp = df_broken_timestamp.iloc[1:]

        df_broken_timestamp.loc[:, 'spc_0_break_timestamp'] = \
            df_broken_timestamp['spc_0_previous'].astype(str) + '(' + df_broken_timestamp['id_timestamp_previous'].astype(str) +')' \
            + '->' + df_broken_timestamp['spc_0'].astype(str) + '(' + df_broken_timestamp['id_timestamp'].astype(str) +')'

        result['spc_over_30_timestamp'] = df_broken_timestamp['spc_0_break_timestamp'].tolist()

        #3.目前最新模次跟timestamp
        df_lastest = df.iloc[-1:].astype(str)
        result['lastest_spc'] = df_lastest['spc_0'].values[0] + '(' + df_lastest['id_timestamp'].values[0] + ')'

        # print(df_broken_timestamp['spc_0_break_timestamp'])
        #print(df_broken_timestamp[['spc_0', 'spc_0_previous','id_timestamp','id_timestamp_previous']].astype(str))
        # print(df_broken_timestamp.dtypes)
        # print(df_broken_timestamp.count())

        return parseResponseJson(responseData, result)
    except:
        print("genDailyReport exception")
        setErrorResponse(responseData)
        # responseData['responseCode'] = 400
        # responseData['responseMessage'] = 'except'
        return parseResponseJson(responseData, result)
