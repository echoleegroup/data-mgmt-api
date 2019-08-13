import logging
from logging.handlers import TimedRotatingFileHandler
from settings import LOG_LEVEL, LOG_PATH, LOG_FILE_NAME

def setLog():
    logger = logging.getLogger()
    #logger.setLevel(LOG_LEVEL)
    #fh = logging.FileHandler(LOG_FILE_NAME)
    #fh.setLevel(LOG_LEVEL)
    #formatter = logging.Formatter(log_format)
    #fh.setFormatter(formatter)
    #logger.addHandler(fh)

    #logname = "dataservice.log"
    handler = TimedRotatingFileHandler(filename='{}/{}'.format(LOG_PATH, LOG_FILE_NAME), when="midnight", interval=1)
    handler.suffix = "%Y%m%d"
    logger.addHandler(handler)
    return logger