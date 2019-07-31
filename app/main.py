import os
from querySolrAPI import queryInfoAll,queryInfoBetweenTimestampSPC0

from flask import Flask, send_file, render_template, request, url_for
from flask_bootstrap import Bootstrap

app = Flask(__name__)
bootstrap = Bootstrap(app) #bootstrap

@app.route("/")
def main():
    dataList = ["spc", "Machine status", "history record", "alarm record", "futaba"]
    return render_template('index.html', dataList=dataList)

#http://localhost:8983/solr/spc/select?fl=spc_0&fq=timestamp:[2019-07-26T05:42:59Z TO 2019-07-26T05:43:00Z]&q=*:*
#http://localhost:80/queryInfoBetweenTimestampSPC0/spc/20190725/20190726
#http://10.57.199.65:80/queryInfoBetweenTimestampSPC0/spc/20190726/20190727
@app.route('/queryInfoBetweenTimestampSPC0/<string:data_category>/<string:start_ts>/<string:end_ts>/', methods = ['GET'])
def queryFixedInfoBetweenTimestampSPC0(data_category, start_ts, end_ts):
    source = queryInfoBetweenTimestampSPC0(data_category, start_ts, end_ts)
    return source

@app.route('/queryFixedSourceAllForUITest/', methods = ['POST'])
def queryFixedSourceAllForUITest():
    sourceInfo = request.form
    print(sourceInfo['data_category'])
    source = queryFixedSourceAll(sourceInfo['data_category'])
    return source

#http://10.57.199.65:80/queryFixedSourceAll/spc
#http://localhost:80/queryFixedSourceAll/spc
@app.route('/queryFixedSourceAll/<string:data_category>/', methods = ['GET'])
def queryFixedSourceAll(data_category):
    source = queryInfoAll(data_category)
    return source


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
    app.run(host='0.0.0.0', debug=True, port=80)
