# config.py
import os
from dotenv import load_dotenv

from dotenv import dotenv_values

env_file = '../env/.env'
# Inside docker,  if relative path doesn't work
# This won't work on regular run 
if not os.path.exists(env_file):  
    env_file = "/env/.env"

""" with open(env_file, 'r') as file:
        for line in file:
            print(line, end='') """

if not load_dotenv(env_file):
    raise Exception("Failed to load environment ")

def get_required_env_variable(var_name):
    value = os.environ.get(var_name)
   
    if value is None:
        raise ValueError(f"Environment variable {var_name} is not set.")
    return value


import socket
import random
import netifaces

def generate_unique_name():
    machine_hostname = socket.gethostname()

    local_ip = None

    try:
        # Iterate through all network interfaces to find a valid IPv4 address
        for interface in netifaces.interfaces():
            # Check for IPv4 addresses on the interface
            addresses = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addresses:
                ipv4_info = addresses[netifaces.AF_INET][0]
                ip_address = ipv4_info['addr']

                # Exclude the loopback address
                if not ip_address.startswith('127.'):
                    local_ip = ip_address
                    break
    except Exception:
        # Fallback in case of any error
        pass

    if local_ip:
        last_byte = local_ip.split('.')[-1]
        unique_name = f"{machine_hostname}-{last_byte}"
    else:
        # Fallback to a random number if no suitable IP is found
        last_byte = random.randint(0, 255)
        unique_name = f"{machine_hostname}-{last_byte}"

    return unique_name

class ConfigClass(object):
    UPLOAD_STORAGE_LOCATION = get_required_env_variable("UPLOAD_STORAGE_LOCATION")
    APP_SECRET = get_required_env_variable('APP_SECRET')
    APP_NAME = "ai." + generate_unique_name()   

