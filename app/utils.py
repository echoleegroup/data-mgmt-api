# coding:utf-8

import json
from datetime import timedelta, date, datetime
import math
import pytz

def praseJsonFormat(jsonObject):
    data = json.loads(jsonObject)
    return data['response']['docs']

def getTotalRowsBetweenTwoTimestamp(startTs, endTs, secs, num):
    tDelta = diffTime(startTs, endTs)
    return math.ceil(tDelta/secs*num)

def getDatetime(ts, format):
    return datetime.strptime(ts, format)

def convertDatetimeToString(datetime, format):
    return datetime.strftime(format)

def getDatetimeFromUnix(ts):
    return datetime.fromtimestamp(int(ts.replace('.','')[:10]))

def diffTime(startTs, endTs):
    tDelta = abs(startTs - endTs).total_seconds()
    return tDelta

#template
def insertBlockquote(str):
    return '<blockquote>'+str+'</blockquote>'

def insertTextIndent(str, intentNumber, marginNumber):
    return '<p style="text-indent: ' + intentNumber + 'px;">'+str+'</p>'


