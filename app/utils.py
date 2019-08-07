import json
from datetime import timedelta, date, datetime
import math

def praseJsonFormat(jsonObject):
    data = json.loads(jsonObject)
    return data['response']['docs']

def getTotalRowsBetweenTwoTimestamp(startTs, endTs):
    startDate = substringToDate(startTs)
    endDate = substringToDate(endTs)
    tDelta = abs(startDate - endDate)
    return math.ceil(tDelta.seconds/30)

def substringToDate(dateStr):
    return datetime(int(dateStr[0:4]), int(dateStr[4:6]), int(dateStr[6:8]), int(dateStr[8:10]), int(dateStr[10:12]), int(dateStr[12:14]))

def substring(date):
    return date[0:4] + "-" + date[4:6] + "-" + date[6:8] + 'T' + date[8:10] + ':' + date[10:12] + ':' + date[12:14] +'Z'

# def substringStartDate(date):
#     return substring(date) + ':00Z'
#
# def substringEndDate(date):
#     #return substring(date) + 'T23:59:59Z'
#     return substring(date) + ':59Z'

def parseResponseJson(responseData, result):
    responseData['result'] = result
    return json.dumps(responseData)