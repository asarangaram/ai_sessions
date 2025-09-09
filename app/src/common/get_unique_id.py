import hashlib
import socket
import os
import sys
import logging

def get_unique_device_id(hostname:str):
    """
    Attempts to get a unique device ID from specific OS-based locations,
    prioritizing Raspberry Pi, then Linux, then macOS.
    Returns the ID if found, otherwise raises an exception.
    """
    logging.warning(hostname)
    # 1. Try to get the Raspberry Pi CPU serial number
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line.startswith('Serial'):
                    serial_number = line.split(':')[1].strip()
                    return f"{hostname}-hw-{serial_number[-8:]}"
    except FileNotFoundError:
        pass  # Continue to the next check

    # 2. Try to get the Linux machine-id
    try:
        with open('/etc/machine-id', 'r') as f:
            machine_id = f.read().strip()
            sha256_hash = hashlib.sha256(machine_id.encode('utf-8')).hexdigest()
            return f"{hostname}-mid-{sha256_hash[:8]}"
    except FileNotFoundError:
        pass  # Continue to the next check
    
    # 3. Try to get the macOS UUID
    try:
        with open('/private/var/db/uuidtext/uuid', 'r') as f:
            unique_id = f.read().strip()
            return f"{hostname}--uuid-{unique_id}"
    except FileNotFoundError:
        pass  # Continue to the next check

    # If all methods fail, raise an error and exit
    raise RuntimeError("Could not find a unique device ID from any known location.")

if __name__ == '__main__':
    try:
        unique_id = get_unique_device_id()
        print(unique_id)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)