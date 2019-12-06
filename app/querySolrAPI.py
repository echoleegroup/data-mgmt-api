import socket
import requests
import json
import os
import pytz



from datetime import datetime, time, timedelta
from utils import getTotalRowsBetweenTwoTimestamp
from settings import SOLR_PORT, ENV, SERVER_IP
from log import logging

def queryInfoAll(coreName):
    condition = coreName + '/select?q=*:*&sort=timestamp desc'
    return queryInfo(condition)

def queryInfoBetweenTimestampSPC0(coreName, machineId, validStartTime, validEndTime, rows):
    condition = coreName + '/select?q=machine_id:' + machineId + ' AND timestamp:[' + str(validStartTime.timestamp())[:-2] \
                           + ' TO ' + str(validEndTime.timestamp())[:-2] + ']' \
                            +'&fl=SPC_0,timestamp,timestamp_iso,RD_618' \
                           '&sort=SPC_0 asc&rows=' + str(rows)
    response = queryInfo(condition)
    return response

def queryDCLogBetweenTimestamp(coreName, machineId, validStartTimeStr, validEndTimeStr, rows):
    condition = coreName + '/select?q=machine_id:' + machineId + ' AND name:ConnectionTest' \
                ' AND timestamp:[' + validStartTimeStr \
                + ' TO ' + validEndTimeStr + ']' \
                + '&fl=name,timestamp,result' \
                  '&sort=timestamp asc&rows=' + str(rows)
    response = queryInfo(condition)
    return response

def queryMachinestate(coreName):
    condition = coreName + '/select?q=*:*&fl=MachineState,timestamp_iso&sort=timestamp_iso desc&rows=1'
    return queryInfo(condition)

def queryLastSPC(coreName, machineId):
    condition = coreName + '/select?q=machine_id:' + machineId + '&fl=SPC_0,timestamp,timestamp_iso,RD_618' \
                           '&sort=timestamp_iso desc&rows=1'
    response = queryInfo(condition)
    return response

def queryAlarmrecord(coreName, machineId):
    condition = coreName + '/select?q=machine_id:' + machineId + '&fl=RD_618,StartTime,StartTime_iso,Item,StopTime,StopTime_iso' \
                           '&sort=timestamp_iso desc&rows=2'
    response = queryInfo(condition)
    return response

def queryAlarmrecord(coreName, machineId, validStartTimeStr, validEndTimeStr, rows):
    condition = coreName + '/select?q=machine_id:' + machineId + \
                           ' AND timestamp_iso:[' + validStartTimeStr \
                           + ' TO ' + validEndTimeStr + ']' \
                           '&fl=RD_618,StartTime,StartTime_iso,Item,StopTime,StopTime_iso' \
                           '&sort=timestamp_iso desc&rows=' + str(rows)
    response = queryInfo(condition)
    return response

def queryInfo(selectCondition):
    logging.info(selectCondition)
    res = requests.get("http://" + SERVER_IP + ":" + SOLR_PORT + "/solr/" + selectCondition)
    return res.text


