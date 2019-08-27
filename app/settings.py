# settings.py
import os
from dotenv import load_dotenv
import sys

#env = os.environ['ENV']
# env = sys.argv[1]
from pathlib import Path  # python3 only

# if env == 'production':
#   dotenv_file = '.env.production'
# elif env == 'staging':
#   dotenv_file = '.env.staging'
# else:
dotenv_file = '.env'
#env_path = Path('./app') / dotenv_file
env_path = Path('.') / dotenv_file
#env_path = dotenv_file
load_dotenv(dotenv_path=env_path)
#print(Path('./app') / dotenv_file)

SOLR_PORT = os.getenv("SOLR_CORE_PORT")
ENV = os.getenv("ENV")
LOG_LEVEL = os.getenv("LOG_LEVEL")
LOG_FILE_NAME = os.getenv("LOG_FILE_NAME")
LOG_PATH = os.getenv("LOG_PATH")
print(ENV)