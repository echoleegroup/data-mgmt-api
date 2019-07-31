# data-mgmt-api

query solr api and collector api for monitor

1.查詢目前最新的SPC模次的資訊(order by timestamp desc)
http://10.57.199.65/queryFixedSourceAll/spc/
2.給定特定區間, 查詢SPC模次(order by spc_0 asc)
http://10.57.199.65/queryInfoBetweenTimestampSPC0/spc/20190726/20190727/
3.查詢machine status
http://10.57.199.65:80/queryMachinestate/machinestatus/



