import socket
import requests
import json
import os

def checkPing():
    condition = "Check/Ping"
    return checkStatus(condition)

def checkConnect():
    condition = "Check/Connect"
    return checkStatus(condition)

def checkStatus(condition):
    #res = requests.get("http://" + "10.57.232.105" + ":" + "32780" + "/" + condition)
    res = requests.get("http://localhost:" + "32780" + "/" + condition)
    return res.text