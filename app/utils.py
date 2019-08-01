import json

def praseJsonFormat(jsonObject):
    data = json.loads(jsonObject)
    machineStatus = data['response']['docs'][0]['machinestate']
    return machineStatus
