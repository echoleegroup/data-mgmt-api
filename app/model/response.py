# coding:utf-8
import json

def initResponse():
    responseData = {}
    responseData['responseCode'] = 200
    responseData['responseMessage'] = 'OK'
    return responseData

def parseResponseJson(responseData, result, key):
    responseData[key] = result
    return json.dumps(responseData)

def setErrorResponse(responseData):
    responseData['responseCode'] = 400
    responseData['responseMessage'] = 'Exception'
    return responseData

def setErrorResponse(responseData, errorCode, errorMessage):
    responseData['responseCode'] = errorCode
    responseData['responseMessage'] = errorMessage
    return responseData
