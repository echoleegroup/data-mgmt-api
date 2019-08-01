# settings.py
import os
from dotenv import load_dotenv

env = os.environ['ENV']
from pathlib import Path  # python3 only
if env == 'production':
  dotenv_file = '.env.production'
elif env == 'staging':
  dotenv_file = '.env.staging'
else:
  dotenv_file = '.env'
env_path = Path('.') / dotenv_file
load_dotenv(dotenv_path=env_path)

print(os.getenv("SOLR_CORE_PORT"))

