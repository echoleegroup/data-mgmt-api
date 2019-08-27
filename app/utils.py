import json
from datetime import timedelta, date, datetime
import math
import pytz

def praseJsonFormat(jsonObject):
    data = json.loads(jsonObject)
    return data['response']['docs']

def getTotalRowsBetweenTwoTimestamp(startTs, endTs):
    # startDate = substringToDate(startTs)
    # endDate = substringToDate(endTs)
    #tDelta = abs(startDate - endDate).total_seconds()
    tDelta = diffTime(startTs, endTs)
    return math.ceil(tDelta/10)

def getDatetime(ts):
    return datetime.strptime(ts, "%Y%m%d%H%M%S")

def getDatetimeFromUnix(ts):
    return datetime.fromtimestamp(int(ts.replace('.','')[:10]))

def diffTime(startTs, endTs):
    # startDT = datetime.mktime(startISO)
    # endDT = datetime.mktime(endISO)
    tDelta = abs(startTs - endTs).total_seconds()
    return tDelta

def transferTimezoneTPE():
    taipei = pytz.timezone('Asia/Taipei')
    # validStartTime.replace(tzinfo=taipei).timestamp()
    dt = datetime.datetime.strptime('2015-07-03 20:25', '%Y-%m-%d %H:%M').replace(tzinfo=taipei)
    return
# def substringToDate(dateStr):
#     return datetime(int(dateStr[0:4]), int(dateStr[4:6]), int(dateStr[6:8]), int(dateStr[8:10]), int(dateStr[10:12]), int(dateStr[12:14]))
#
# def substring(date):
#     return date[0:4] + "-" + date[4:6] + "-" + date[6:8] + 'T' + date[8:10] + ':' + date[10:12] + ':' + date[12:14] +'Z'