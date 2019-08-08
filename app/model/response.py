import json

def initResponse():
    responseData = {}
    responseData['responseCode'] = 200
    responseData['responseMessage'] = ''
    return responseData

def parseResponseJson(responseData, result):
    responseData['result'] = result
    return json.dumps(responseData)

def setErrorResponse(responseData):
    responseData['responseCode'] = 400
    responseData['responseMessage'] = 'except'
    return responseData


