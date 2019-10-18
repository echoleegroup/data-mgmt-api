# data-mgmt-api

query solr api and collector api for monitor  

   - 用途說明:監控數據品質，提供API服務
       1. Dashboard燈號查詢
           - queryLightStatusByDataCollector
       2. 機台設備daily report A/B版本
           - A(簡易版): queryDailyReport
           - B(AP5版): queryDailyReportSimplification
       3. 數據監控exporter(透過Promethues發送告警到slack、企業微信)
           - 檢查SPC最新模次號的生產時間, 若超過系統時間5分鐘, 觸發報警: checkLastSPC
           - 檢查AlarmRecord, 當下報警數據的開始時間必須晚於前一筆的開始時間, 結束時間也晚於前一筆的結束時間: checkAlarmrecordStartTime
           - 檢查SPC模次號, 判斷RD_618與SPC_0模次號是否相同, 當兩者不相同, 則觸發報警: checkJumpAndDuplicatedRecord
       4. TPM串接告警通知(透過nifi呼叫api發送告警到rabbitMQ)
           - 傳送alarmrecord事件: getAlarmrecordData
           - 生產逾時: getMachineIdleData
       5. OEE燈號狀態寫入Solr(透過nifi定期1分鐘呼叫api)
           - insertLightStatus
       6. TPM燈號查詢
           - queryNewLightStatusByDataCollector
