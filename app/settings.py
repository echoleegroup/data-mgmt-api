# settings.py
import os
from dotenv import load_dotenv
import sys

#env = os.environ['ENV']
# env = sys.argv[1]
from pathlib import Path  # python3 only


#env_path = Path('.') / dotenv_file
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)
#print(Path('./app') / dotenv_file)

SOLR_PORT = os.getenv("SOLR_CORE_PORT")
ENV = os.getenv("ENV")
LOG_LEVEL = os.getenv("LOG_LEVEL")
LOG_FILE_NAME = os.getenv("LOG_FILE_NAME")
LOG_PATH = os.getenv("LOG_PATH")
SERVER_IP = os.getenv("SERVER_IP")
print(ENV)