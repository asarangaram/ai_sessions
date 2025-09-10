# config.py
import os
from dotenv import load_dotenv
import logging

from .get_unique_id import get_unique_device_id



env_file = "../env/.env"

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
    APP_SECRET = get_required_env_variable("APP_SECRET")
    HOST_NAME = get_required_env_variable("HOST_NAME")
    APP_NAME = "ai." + get_unique_device_id(HOST_NAME)
