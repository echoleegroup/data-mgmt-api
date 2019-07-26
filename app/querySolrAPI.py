import socket
import requests
import json

def queryInfoAll(coreName):
    condition = coreName + '/select?q=*:*'
    return queryInfo(condition)

def queryInfoBetweenTimestampSPC0(coreName, startTs, endTs):
    condition = coreName + '/select?q=*:*&fl=spc_0&fq=timestamp:[' + substringDate(startTs) + ' TO ' + substringDate(endTs) + ']'
    print(condition)
    return queryInfo(condition)


def queryInfo(selectCondition):
    solrHostname = socket.gethostbyname(socket.gethostname())
    # res = requests.get(
    #     "http://" + solrHostname + ":" + "8983" + "/solr/" + coreName + '/select?q=*:*')
    res = requests.get("http://" + solrHostname + ":" + "8983" + "/solr/" + selectCondition)
    print(res.text)
    return res.text


def substringDate(date):
    return date[0:4] + "-" + date[4:6] + "-" + date[6:8] + 'T00:00:00Z'