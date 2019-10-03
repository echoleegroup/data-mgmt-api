import pysolr

from settings import SOLR_PORT, ENV, SERVER_IP

def addOEEData(coreName, data_collector):
    # SERVER_IP
    host = SERVER_IP
    port = SOLR_PORT

    url = 'http://' + host + ':' + port + '/solr/' + coreName
    # http://10.160.29.112:8983/solr/oee_test

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

def addLightStatusData(coreName, data_collector):

    try:

        # SERVER_IP
        host = SERVER_IP
        port = SOLR_PORT

        #url = 'http://' + host + ':' + port + '/solr/' + coreName
        url = 'http://10.160.29.105:' + port + '/solr/' + coreName
        # http://10.160.29.112:8983/solr/oee_test

        solr = pysolr.Solr(url, timeout=10)
        document = [{
            "id": "A011569168000",
            "machine_id": "A01",
            "timestamp": "1569168000",
            "timestamp_iso": "2019-09-23T16:02:00.000Z",
            "light_color": "green"
        },{
            "id": "A031569168000",
            "machine_id": "A03",
            "timestamp": "1569168000",
            "timestamp_iso": "2019-09-23T16:02:00.000Z",
            "light_color": "yellow"
        },{
            "id": "A051569168000",
            "machine_id": "A05",
            "timestamp": "1569168000",
            "timestamp_iso": "2019-09-23T16:02:00.000Z",
            "light_color": "icon_disconnected"
        },{
            "id": "A061569168000",
            "machine_id": "A06",
            "timestamp": "1569168000",
            "timestamp_iso": "2019-09-23T16:02:00.000Z",
            "light_color": "gray"
        },{
            "id": "A011569178000",
            "machine_id": "A01",
            "timestamp": "1569178000",
            "timestamp_iso": "2019-09-23T16:02:00.000Z",
            "light_color": "green"
        }]

        solr.add(document)

        return "Done"
    except:
        return "Exception"

def addLightStatusData(coreName, data_collector, document):

    try:
        # SERVER_IP
        host = SERVER_IP
        port = SOLR_PORT
        # url = 'http://' + host + ':' + port + '/solr/' + coreName
        url = 'http://10.160.29.105:' + port + '/solr/' + coreName
        solr = pysolr.Solr(url, timeout=10)
        solr.add(document)
        return "Done"
    except:
        return "Exception"
