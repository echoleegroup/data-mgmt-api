import pysolr

from settings import SOLR_PORT, ENV, SERVER_IP

def addLightStatusData(coreName, data_collector, document):

    try:
        port = SOLR_PORT
        # url = 'http://' + host + ':' + port + '/solr/' + coreName
        url = 'http://10.160.29.105:' + port + '/solr/' + coreName
        solr = pysolr.Solr(url, timeout=10)
        solr.add(document)
        return "Done"
    except:
        return "Exception"
