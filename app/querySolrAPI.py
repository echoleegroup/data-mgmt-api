import socket
import requests
import json
import os
import pytz



from datetime import datetime, time, timedelta
from utils import getTotalRowsBetweenTwoTimestamp
from settings import SOLR_PORT, ENV
from log import logging

def queryInfoAll(coreName):
    condition = coreName + '/select?q=*:*&sort=timestamp desc'
    return queryInfo(condition)

def queryInfoBetweenTimestampSPC0(coreName, machineId, validStartTime, validEndTime):
    rows = getTotalRowsBetweenTwoTimestamp(validStartTime, validEndTime)
    #timedelta(seconds=time.altzone())
    # taipei = pytz.timezone('Asia/Taipei')
    # validStartTime.replace(tzinfo=taipei).timestamp()
    condition = coreName + '/select?q=machine_id:' + machineId + ' AND timestamp:[' + str(validStartTime.timestamp())[:-2] \
                           + ' TO ' + str(validEndTime.timestamp())[:-2] + ']' \
                            +'&fl=SPC_0,timestamp,timestamp_iso' \
                           '&sort=SPC_0 asc&rows=' + str(rows)
                            # '&fq=timestamp:[' + str(validStartTime.timestamp() + 28800)[:-2] \
                            #  + ' TO ' + str(validEndTime.timestamp() + 28800)[:-2] + ']' \

    # "q": "machine_id:A01 AND timestamp_iso:[2019-08-26T17:30:00Z TO 2019-08-27T08:30:00Z]",
    # "fl": "timestamp, SPC_0, timestamp_iso",
    # "sort": "SPC_0 asc",

    response = queryInfo(condition)
    return response

def queryMachinestate(coreName):
    condition = coreName + '/select?q=*:*&fl=MachineState,timestamp_iso&sort=timestamp_iso desc&rows=1'
    return queryInfo(condition)

def queryInfo(selectCondition):
    logging.info(selectCondition)
    ip = "localhost"
    if ENV == "dev": #測試機
        # ip = "10.57.232.105"
        ip = "10.160.29.105"
    res = requests.get("http://" + ip + ":" + SOLR_PORT + "/solr/" + selectCondition)
    return res.text

def queryLastSPC(coreName, machineId):
    condition = coreName + '/select?q=machine_id:' + machineId + '&fl=SPC_0,timestamp,timestamp_iso' \
                           '&sort=timestamp desc&rows=1'
    response = queryInfo(condition)
    return response
