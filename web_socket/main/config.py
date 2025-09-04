# config.py
import os

class ConfigClass(object):
 
    FILE_STORAGE_LOCATION = '/data'
    os.makedirs(FILE_STORAGE_LOCATION, exist_ok=True)

    SESSION_STORAGE_LOCATION = f"{FILE_STORAGE_LOCATION}/sessions"
    os.makedirs(SESSION_STORAGE_LOCATION, exist_ok=True)

    