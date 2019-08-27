import logging
from logging.handlers import TimedRotatingFileHandler
from settings import LOG_LEVEL, LOG_PATH, LOG_FILE_NAME
from datetime import datetime
#def setLog():

# 基礎設定
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    handlers=[logging.FileHandler('{}/{:%Y-%m-%d}.log'.format(LOG_PATH, datetime.now()), 'a', 'utf-8')])

# loghandler = logging.handlers.TimedRotatingFileHandler(filename='{}/{}'.format(LOG_PATH, LOG_FILE_NAME), when="midnight", interval=1)
# loghandler.setLevel(logging.DEBUG)
# fileformatter = logging.Formatter('%(asctime)s - [%(levelname)s] >>> %(message)s')
# loghandler.setFormatter(fileformatter)
# logging.getLogger('').addHandler(loghandler)

# 定義 handler 輸出 sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# 設定輸出格式
formatter = logging.Formatter('%(asctime)s - [%(levelname)s] >>> %(message)s')
# handler 設定輸出格式
console.setFormatter(formatter)
# 加入 hander 到 root logger
logging.getLogger('').addHandler(console)

# return logger