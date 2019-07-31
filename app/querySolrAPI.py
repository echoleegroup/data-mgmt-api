import socket
import requests
import json

def queryInfoAll(coreName):
    condition = coreName + '/select?q=*:*&sort=timestamp desc'
    return queryInfo(condition)

def queryInfoBetweenTimestampSPC0(coreName, startTs, endTs):
    condition = coreName + '/select?q=*:*&fl=spc_0&fq=timestamp:[' + substringStartDate(startTs) + ' TO ' + substringEndDate(endTs) + ']&sort=spc_0 asc'
    print(condition)
    return queryInfo(condition)

def queryMachinestate(coreName):
    condition = coreName + '/select?q=*:*&fl=machinestate,timestamp&sort=timestamp desc&rows=1'
    print(condition)
    return queryInfo(condition)

def queryInfo(selectCondition):
    solrHostname = socket.gethostbyname(socket.gethostname())
    res = requests.get("http://" + solrHostname + ":" + "8983" + "/solr/" + selectCondition)
    print(res.text)
    return res.text

def substring(date):
    return date[0:4] + "-" + date[4:6] + "-" + date[6:8]

def substringStartDate(date):
    return substring(date) + 'T00:00:00Z'

def substringEndDate(date):
    return substring(date) + 'T23:59:59Z'