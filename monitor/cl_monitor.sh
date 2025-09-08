#!/bin/bash

# A script to monitor local services and manage their Avahi broadcasting.
# It checks a list of services (format: prefix@port) every second.
# If a service is healthy (HTTP 200), it uses 'cl_avahi_manager.sh' to start its
# Avahi broadcast. If the service is down, it stops the broadcast.



# --- Help function to display usage information ---
show_help() {
  echo "Usage: $0 [service_prefix@port] ..."
  echo
  echo "This script monitors HTTP services and manages Avahi mDNS broadcasting."
  echo "It requires '/usr/local/bin/cl_avahi_manager.sh'."
  echo
  echo "Arguments:"
  echo "  service_prefix@port   One or more services to monitor, in the format 'name@port'."
  echo
  echo "Options:"
  echo "  -h, --help            Show this help message and exit."
  echo
  echo "Example:"
  echo "  sudo $0 server1@8080 server2@9000"
}

# --- Check for root privileges ---
if [ "$(id -u)" -ne 0 ]; then
  echo "This script must be run with sudo to manage Avahi services."
  exit 1
fi

# --- Check for -h or --help in any position and exit immediately ---
for arg in "$@"; do
  if [[ "$arg" == "-h" || "$arg" == "--help" ]]; then
    show_help
    exit 0
  fi
done

# --- Check if no arguments are provided (after checking for help flags) ---
if [ "$#" -eq 0 ]; then
  echo "Error: No services provided to monitor."
  show_help
  exit 1
fi


# --- Check for dependencies ---
command -v curl >/dev/null 2>&1 || { echo >&2 "Error: 'curl' is not installed. Aborting."; exit 1; }
command -v ip >/dev/null 2>&1 || { echo >&2 "Error: 'ip' command not found. Aborting."; exit 1; }
command -v /usr/local/bin/cl_avahi_manager.sh >/dev/null 2>&1 || { echo >&2 "Error: 'cl_avahi_manager' command not found. Aborting."; exit 1; }

# --- Get the local IP address dynamically ---
get_local_ip() {
    ip route get 1.1.1.1 2>/dev/null | awk '{print $7}'
}
generate_unique_name() {
    # --- Get the last byte of the IP address ---
    IP=$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7}')

    if [ -n "$IP" ]; then
        LAST_BYTE=$(echo "$IP" | cut -d'.' -f4)
    else
        # Ensure this never executed by confirming ip before
        # Fallback to a random number if no IP is found
        LAST_BYTE=$((RANDOM % 256))
    fi

    # --- Get the machine's hostname ---
    MACHINE_HOSTNAME=$(hostname)

    # --- Combine them into a human-readable unique name ---
    UNIQUE_NAME="${MACHINE_HOSTNAME}-${LAST_BYTE}"

    echo "${UNIQUE_NAME}@cloudonlanapps"
   
}
IDENTIFIER_BASE=$(generate_unique_name)
export IDENTIFIER_BASE
echo IDENTIFIER_BASE $IDENTIFIER_BASE

# --- Declare an associative array to track service states (requires Bash 4.0+) ---
declare -A service_states

# --- Cleanup function to run on Ctrl+C (SIGINT) ---
cleanup() {
    echo -e "\nCaught Ctrl+C. Stopping all tracked services..."
    
    # Iterate through all provided service arguments
    for service_arg in "$@"; do
        # Extract the service prefix
        service_prefix=$(echo "$service_arg" | cut -d'@' -f1 | sed 's/^-//')
        if [ -n "$service_prefix" ]; then
            /usr/local/bin/cl_avahi_manager.sh -stop "$service_prefix"
        fi
    done

    echo "Services stopped. Exiting."
    exit 0
}

# --- Set the trap to call the cleanup function on SIGINT ---
trap 'cleanup "$@"' SIGINT SIGTERM

# --- Main Watchdog Loop ---
while true; do
    # Get the current IP to handle potential network changes
    IP=$(get_local_ip)
    if [ -z "$IP" ]; then
      echo "No local IP address found. Retrying in 1 second."
      sleep 1
      continue
    fi

   
    
    # Iterate through all provided service arguments
    for service_arg in "$@"; do
        # Extract the service prefix and port
        service_prefix=$(echo "$service_arg" | cut -d'@' -f1 | sed 's/^-//')
        port=$(echo "$service_arg" | cut -d'@' -f2)

        if [ -z "$service_prefix" ] || [ -z "$port" ]; then
            echo "Invalid argument format: $service_arg. Skipping."
            continue
        fi

        # Check service health with curl
        http_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 "http://$IP:$port")

        current_state="down"
        if [ "$http_code" -eq 200 ]; then
            current_state="up"
        fi

        # Check if the state has changed
        if [ "${service_states[$service_prefix]}" != "$current_state" ]; then
            if [ "$current_state" == "up" ]; then
                echo "State change: '$service_prefix' is now UP. Starting Avahi broadcast..."
                /usr/local/bin/cl_avahi_manager.sh -start "${service_prefix}@${port}"
            else
                echo "State change: '$service_prefix' is now DOWN. Stopping Avahi broadcast..."
                /usr/local/bin/cl_avahi_manager.sh -stop "$service_prefix"
            fi
            # Update the state to the current status
            service_states["$service_prefix"]="$current_state"
        #else
            #echo "Service '$service_prefix' state is unchanged ($current_state)."
        fi
    done

    # Wait for one second before the next check
    sleep 5
done
