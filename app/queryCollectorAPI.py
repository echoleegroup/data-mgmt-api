# coding:utf-8

import socket
import requests
import json
import os
#from log import setLog
from settings import ENV, SERVER_IP
from log import logging

def checkPing(dataCollector):
    condition = "Check/Ping"
    return checkStatus(dataCollector, condition)

def checkConnect(dataCollector):
    condition = "Check/Connect"
    return checkStatus(dataCollector, condition)

def checkStatus(dataCollector, condition):
    port = "32780"
    if dataCollector == "A01":
        port = "32710"
    elif dataCollector == "A03":
        port = "32730"
    elif dataCollector == "A05":
        port = "32750"
    elif dataCollector == "A06":
        port = "32760"
    res = requests.get("http://" + SERVER_IP + ":" + port + "/" + condition)
    print("http://" + SERVER_IP + ":" + port + "/" + condition)
    return res.text.replace("\"", "")