# data-mgmt-api

query solr api and collector api for monitor  

1. 燈號查詢
    -  queryLightStatusByDataCollector
        > http://10.160.29.105:33000/checkLightStatusByDataCollector/A01
        
2.  機台設備daily report A/B版本
    1.  A(簡易版): queryDailyReport
        > http://10.160.29.105:33000/queryDailyReportSimplification/spc/20190917170000/
    2.  B(AP5版): queryDailyReportSimplification
        > http://10.160.29.105:33000/queryDailyReport/spc/20190917170000/
        
3. 數據監控exporter(透過Promethues發送告警到slack、企業微信)
    1.  檢查SPC最新模次號的生產時間, 若超過系統時間5分鐘, 觸發報警: checkLastSPC
    2.  檢查AlarmRecord, 當下報警數據的開始時間必須晚於前一筆的開始時間, 結束時間也晚於前一筆的結束時間: checkAlarmrecordStartTime
    3.  檢查SPC模次號, 判斷RD_618與SPC_0模次號是否相同, 當兩者不相同, 則觸發報警: checkJumpAndDuplicatedRecord

4. TPM串接告警通知(透過nifi呼叫api發送告警到rabbitMQ)
    1.  傳送alarmrecord事件: getAlarmrecordData
        > http://10.160.29.112:33000/getAlarmrecordData/20190917170000/20190917180000/
    2.  生產逾時: getMachineIdleData
        > http://10.160.29.112:33000/getMachineIdleData/20190917170000/
5. OEE燈號狀態寫入Solr
    - InsertLightStatus
        > http://10.160.29.105:33000/InsertLightStatus/A01

