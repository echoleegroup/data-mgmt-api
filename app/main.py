# coding:utf-8

import os
import json
from querySolrAPI import queryInfoAll, queryInfoBetweenTimestampSPC0, queryMachinestate
from service import queryLightStatus, genDailyReport, checkLastSPC, checkAlarmrecordStartTime, checkJumpAndDuplicatedRecordFromSPC, \
    genDailyReportSimplification, checkAlarmrecordData, checkMachineIdleData
from utils import getDatetime
from addSolrData import addLightStatusData

import prometheus_client
from prometheus_client import Counter, start_http_server, Gauge
from prometheus_client.core import CollectorRegistry
from log import logging

from flask import Flask, send_file, render_template, request, url_for, Response
app = Flask(__name__)

@app.route("/")
def main():
    dataList = ["spc", "Machine status", "history record", "alarm record", "futaba"]
    return render_template('index.html', dataList=dataList)

@app.route('/queryMachinestate/<string:data_category>/', methods = ['GET'])
def queryFixedMachinestate(data_category):
    source = queryMachinestate(data_category)
    return source

#daily report equipment-----start
@app.route('/queryDailyReport/<string:data_category>/<string:start_ts>/', methods = ['GET'])
def queryDailyReport(data_category, start_ts):
    source = genDailyReport(start_ts, '')
    return source

#start_date, end_date
@app.route('/queryDailyReport/<string:data_category>/<string:start_ts>/<string:end_ts>/', methods = ['GET'])
def queryDailyReportEndTime(data_category, start_ts, end_ts):
    source = genDailyReport(start_ts, end_ts)
    return source
#daily report equipment-----end

@app.route('/queryDailyReportSimplification/<string:data_category>/<string:start_ts>/', methods = ['GET'])
def queryDailyReportSimplification(data_category, start_ts):
    source = genDailyReportSimplification(start_ts, '')
    return source

#query light -----start
@app.route('/checkLightStatusByDataCollector/<string:data_collector>/', methods = ['GET'])
def queryLightStatusByDataCollector(data_collector):
    return queryLightStatus(data_collector, 'dashboard', False)

@app.route('/insertLightStatus/<string:data_collector>/', methods = ['GET'])
def insertLightStatus(data_collector):
    return queryLightStatus(data_collector, 'oee', True)

@app.route('/checkNewLightStatusByDataCollector/<string:data_collector>/', methods = ['GET'])
def checkNewLightStatusByDataCollector(data_collector):
    return queryLightStatus(data_collector, 'oee', False)
#query light-----end


#alarm api to rabbitMQ-----start
@app.route('/getAlarmrecordData/<string:start_ts>/<string:end_ts>/', methods=['GET'])
def getAlarmrecordData(start_ts, end_ts):
    try:
        return checkAlarmrecordData('alarmrecord', start_ts, end_ts)
    except:
        return "exception"

@app.route('/getMachineIdleData/<string:ts>/', methods=['GET'])
def getMachineIdleData(ts):
    try:
        return checkMachineIdleData('spc', ts)
    except:
        return "exception"
#alarm api to rabbitMQ-----end

#prometheus-----start
#only init once
raw_data_spc_last_spc0 = Gauge("Last_SPC_0", "last timestamp whether or not over 5 min", ['timestamp','production_status'])

@app.route('/checkLastSPC/<string:data_category>/metrics', methods = ['GET'])
def checkLastSPCAPI(data_category):
    try:
        status = ''
        result = checkLastSPC('spc', data_category)
        flag = result[0]
        timestamp = result[1]
        if flag == 1:
            status = 'less5min'
        else:
            status = 'over5min'
        raw_data_spc_last_spc0.labels(timestamp, status).set(flag)
        return Response(prometheus_client.generate_latest(raw_data_spc_last_spc0), mimetype="text/plain")
    except:
        return "exception"

alarmrecords = Gauge("alarmrecord_abnormal", "start_time_abnormal", ['RD_618','status'])

@app.route('/checkAlarmrecordStartTime/<string:data_category>/metrics', methods=['GET'])
def checkAlarmrecordStartTimeAPI(data_category):
    try:
        status = ''
        result = checkAlarmrecordStartTime('alarmrecord', data_category)
        flag = result[0]
        RD_618 = result[1]
        if flag == 1:
            status = 'normal'
        else:
            status = 'starttime_less_than_previous_record'
        alarmrecords.labels(RD_618, status).set(flag)
        return Response(prometheus_client.generate_latest(alarmrecords), mimetype="text/plain")
    except:
        return "exception"

spcrecords = Gauge("spcrecord_abnormal", "spc_record_abnormal", ['RD_618','status'])

@app.route('/checkJumpAndDuplicatedRecord/<string:data_category>/metrics', methods=['GET'])
def checkJumpAndDuplicatedRecordFromSPCAPI(data_category):
    try:
        status = ''
        result = checkJumpAndDuplicatedRecordFromSPC('spc', data_category)
        flag = result[0]
        RD_618 = result[1]
        if flag == 1:
            status = 'normal'
        else:
            status = 'SPC_0!=RD_618'
        spcrecords.labels(RD_618, status).set(flag)
        return Response(prometheus_client.generate_latest(spcrecords), mimetype="text/plain")
    except:
        return "exception"
#prometheus-----end

# Everything not declared before (not a Flask route / API endpoint)...
@app.route('/<path:path>')
def route_frontend(path):
    # ...could be a static file needed by the front end that
    # doesn't use the `static` path (like in `<script src="bundle.js">`)
    file_path = os.path.join(app.static_folder, path)
    if os.path.isfile(file_path):
        return send_file(file_path)
    # ...or should be handled by the SPA's "router" in front end
    else:
        index_path = os.path.join(app.static_folder, 'index.html')
        return send_file(index_path)

if __name__ == "__main__":
    # Only for debugging while developing
    app.run(host='0.0.0.0', debug=False, port=33000)
