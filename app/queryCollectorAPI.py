import socket
import requests
import json
import os
#from log import setLog
from settings import ENV
from log import logging

def checkPing(dataCollector):
    condition = "Check/Ping"
    return checkStatus(dataCollector, condition)

def checkConnect(dataCollector):
    condition = "Check/Connect"
    return checkStatus(dataCollector, condition)

def checkStatus(dataCollector, condition):
    port = "32780"
    ip = "localhost"
    if ENV == "dev" or ENV == "staging": #測試機
        port = "32780"
        ip = "10.57.232.105"
    elif dataCollector == "A01":
        port = "32710"
    elif dataCollector == "A03":
        port = "32730"
    elif dataCollector == "A05":
        port = "32750"
    elif dataCollector == "A06":
        port = "32760"
    res = requests.get("http://" + ip + ":" + port + "/" + condition)
    return res.text