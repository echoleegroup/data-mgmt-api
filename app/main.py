import os
import json
from querySolrAPI import queryInfoAll,queryInfoBetweenTimestampSPC0, queryMachinestate
from service import queryLightStatus, genDailyReport
import logging

from flask import Flask, send_file, render_template, request, url_for
#from flask_bootstrap import Bootstrap

app = Flask(__name__)
#bootstrap = Bootstrap(app) #bootstrap

#logging.basicConfig(filename='app.log', format='%(name)s - %(levelname)s - %(message)s')


@app.route("/")
def main():
    dataList = ["spc", "Machine status", "history record", "alarm record", "futaba"]
    return render_template('index.html', dataList=dataList)

#for ui test-----start
@app.route('/queryFixedSourceAllForUITest/', methods = ['POST'])
def queryFixedSourceAllForUITest():
    sourceInfo = request.form
    print(sourceInfo['data_category'])
    source = queryFixedSourceAll(sourceInfo['data_category'])
    return source
#for ui test-----end


#http://localhost:33000/queryFixedSourceAll/spc
#http://10.57.232.105:33000/queryFixedSourceAll/spc
@app.route('/queryFixedSourceAll/<string:data_category>/', methods = ['GET'])
def queryFixedSourceAll(data_category):
    source = queryInfoAll(data_category)
    return source

#http://localhost:8983/solr/spc/select?fl=spc_0&fq=timestamp:[2019-07-26T05:42:59Z TO 2019-07-26T05:43:00Z]&q=*:*
#http://10.57.232.105:33000/queryInfoBetweenTimestampSPC0/spc/20190726/20190727
@app.route('/queryInfoBetweenTimestampSPC0/<string:data_category>/<string:start_ts>/<string:end_ts>/', methods = ['GET'])
def queryFixedInfoBetweenTimestampSPC0(data_category, start_ts, end_ts):
    source = queryInfoBetweenTimestampSPC0(data_category, start_ts, end_ts)
    return source

#http://10.57.232.105:33000/queryMachinestate/machinestatus/
@app.route('/queryMachinestate/<string:data_category>/', methods = ['GET'])
def queryFixedMachinestate(data_category):
    source = queryMachinestate(data_category)
    return source

#daily report equipment-----start
@app.route('/queryDailyReport/<string:data_category>/<string:start_ts>/<string:end_ts>/', methods = ['GET'])
def queryDailyReport(data_category, start_ts, end_ts):
    source = genDailyReport(data_category, start_ts, end_ts)
    return source
#daily report equipment-----end

#燈號顯示-----start
@app.route('/checkLightStatusByDataCollector/<string:data_collector>/', methods = ['GET'])
def queryLightStatusByDataCollector(data_collector):
    return queryLightStatus(data_collector)
#燈號顯示-----end

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
    app.run(host='0.0.0.0', debug=True, port=33000)
