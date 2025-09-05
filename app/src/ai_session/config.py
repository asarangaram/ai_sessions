# config.py
import os
from dotenv import load_dotenv

from dotenv import dotenv_values

env_file = '../venv/.env'
# Inside docker,  if relative path doesn't work
# This won't work on regular run 
if not os.path.exists(env_file):  
    env_file = "/env/.env"

if not load_dotenv(env_file):
    raise Exception("Failed to load environment ")

def get_required_env_variable(var_name):
    value = os.environ.get(var_name)
    if value is None:
        raise ValueError(f"Environment variable {var_name} is not set.")
    return value
 

class ConfigClass(object):
    UPLOAD_STORAGE_LOCATION = get_required_env_variable("UPLOAD_STORAGE_LOCATION")
    if not UPLOAD_STORAGE_LOCATION:
        UPLOAD_STORAGE_LOCATION =  '/data' 
    
