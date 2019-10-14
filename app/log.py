# coding:utf-8

import logging
from logging.handlers import TimedRotatingFileHandler
from settings import LOG_LEVEL, LOG_PATH, LOG_FILE_NAME, KEEP_LOG_DAYS
from datetime import datetime

# 基礎設定
# logging.basicConfig(level=logging.INFO,
#                     format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
#                     datefmt='%m-%d %H:%M',
#                     handlers=[logging.FileHandler('{}/{:%Y-%m-%d}.log'.format(LOG_PATH, datetime.now()), 'a', 'utf-8')])

logging.basicConfig()


root = logging.getLogger()
level = logging.INFO
filename = LOG_PATH + ".log"
format = '%(asctime)s %(levelname)s %(module)s.%(funcName)s Line:%(lineno)d%(message)s'
#filename, when to changefile, interval, backup count
hdlr = TimedRotatingFileHandler(filename, "midnight", 1, 14)
fmt = logging.Formatter(format)
hdlr.setFormatter(fmt)
root.addHandler(hdlr)
root.setLevel(level)


# define handler export sys.stderr
# console = logging.StreamHandler()
# console.setLevel(logging.INFO)
# # 設定輸出格式
# formatter = logging.Formatter('%(asctime)s - [%(levelname)s] >>> %(message)s')
# # handler 設定輸出格式
# console.setFormatter(formatter)
# # 加入 hander 到 root logger
# logging.getLogger('').addHandler(console)
