import pysolr

from settings import SOLR_PORT, ENV, SERVER_IP

def addOEEData(coreName, data_collector):
    # SERVER_IP
    host = SERVER_IP
    port = SOLR_PORT

    url = 'http://10.160.29.112:' + port + '/solr/' + coreName

    solr = pysolr.Solr(url, timeout=10)
    document = [{
        "id": "1",
        "machine_id": "A01",
        "timestamp": "1569168000",
        "timestamp_iso": "2019-09-23T16:02:00.000Z",
        "activation": "88.88",
        "performance": "99.25",
        "quality": "78.69",
    },{
        "id": "2",
        "machine_id": "A03",
        "timestamp": "1569168000",
        "timestamp_iso": "2019-09-23T16:02:00.000Z",
        "activation": "78.88",
        "performance": "95.25",
        "quality": "85.69",
    },{
        "id": "3",
        "machine_id": "A05",
        "timestamp": "1569168000",
        "timestamp_iso": "2019-09-23T16:02:00.000Z",
        "activation": "95.88",
        "performance": "90.25",
        "quality": "89.69",
    },{
        "id": "4",
        "machine_id": "A06",
        "timestamp": "1569168000",
        "timestamp_iso": "2019-09-23T16:02:00.000Z",
        "activation": "89.88",
        "performance": "96.25",
        "quality": "83.69",
    }]
    solr.add(document)

    return "done"
