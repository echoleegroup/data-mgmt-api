# data-mgmt-api

query solr api and collector api for monitor  

1. 查詢目前最新的SPC模次的資訊(order by timestamp desc)  
http://10.57.232.105:33000/queryFixedSourceAll/spc/  
2. 給定特定區間, 查詢SPC模次(order by spc_0 asc)  
http://10.57.232.105:33000/queryInfoBetweenTimestampSPC0/spc/20190726/20190727/  
3. 查詢machine status  
http://10.57.232.105:33000/queryMachinestate/machinestatus/  
4. 查詢燈號  
http://10.57.232.105:33000/checkLightStatusByDataCollector/A01  
5. 查詢DailyReport  
spc_breakoff: 有掉模次的起迄模次號碼與timestamp  
spc_over_30_timestamp: 模次之間超過30秒的起迄模次號碼與timestamp  
lastest_spc: 最近一筆模次資料  
http://10.57.232.105:33000/queryDailyReport/spc/20190806/20190807/  

