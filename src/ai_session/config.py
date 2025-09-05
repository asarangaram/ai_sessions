# config.py
import os
from dotenv import load_dotenv


dotenv_path = os.path.expanduser("~/.mediarepo")

if not load_dotenv(dotenv_path):
    raise Exception("failed to load environment")


def get_required_env_variable(var_name):
    value = os.environ.get(var_name)
    if value is None:
        raise ValueError(f"Environment variable {var_name} is not set.")
    return value


class ConfigClass(object):
    UPLOAD_STORAGE_LOCATION = get_required_env_variable("UPLOAD_STORAGE_LOCATION")
