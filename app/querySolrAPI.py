import socket
import requests
import json
import os
from utils import substring, getTotalRowsBetweenTwoTimestamp
from settings import SOLR_PORT, ENV

def queryInfoAll(coreName):
    condition = coreName + '/select?q=*:*&sort=timestamp desc'
    return queryInfo(condition)

def queryInfoBetweenTimestampSPC0(coreName, startTs, endTs):
    startTs = startTs + '000000'
    endTs = endTs + '235959'
    rows = getTotalRowsBetweenTwoTimestamp(startTs, endTs)
    condition = coreName + '/select?q=*:*&fl=spc_0,timestamp,id_timestamp&fq=timestamp:[' + substring(startTs) + ' TO ' + substring(endTs) + ']&sort=spc_0 asc&rows=' + str(rows)
    response = queryInfo(condition)
    return response

def queryMachinestate(coreName):
    condition = coreName + '/select?q=*:*&fl=machinestate,timestamp&sort=timestamp desc&rows=1'
    return queryInfo(condition)

def queryInfo(selectCondition):
    print(selectCondition)
    ip = "localhost"
    if ENV == "dev": #測試機
        ip = "10.57.232.105"
    res = requests.get("http://" + ip + ":" + SOLR_PORT + "/solr/" + selectCondition)
    return res.text
