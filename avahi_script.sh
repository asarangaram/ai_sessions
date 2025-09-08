#!/bin/bash

# --- Check for root privileges ---
if [ "$(id -u)" -ne 0 ]; then
  echo "This script must be run with sudo."
  exit 1
fi

# --- Define constants and file paths ---
AVAHI_SERVICE_DIR="/etc/avahi/services"
IDENTIFIER_BASE="server100@cloudonlapapps"

# --- Function to start a service ---
start_service() {
  local service_prefix="$1"
  local port="$2"

  
  local service_file_name="cl_avahi_$service_prefix.service"
  local capitalized_prefix="${service_prefix^}"
  local  service_name="CL $capitalized_prefix Service"
  local identifier="$service_prefix.$IDENTIFIER_BASE"

  # Ensure the port is a valid number
  if ! [[ "$port" =~ ^[0-9]+$ ]]; then
    echo "Error: Invalid port number '$port'. Skipping."
    return 1
  fi
  
  echo "Starting '$service_name' on port $port..."

  cat > "$AVAHI_SERVICE_DIR/$service_file_name" << EOF
<?xml version="1.0" standalone='no'?>
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
  <name>$service_name</name>
  <service>
    <type>_colan._tcp</type>
    <port>$port</port>
    <txt-record>identifier=$identifier</txt-record>
  </service>
</service-group>
EOF

  echo "Service file $AVAHI_SERVICE_DIR/$service_file_name created."
}

stop_service() {
  local service_prefix="$1"
  local port="$2"

  
  local service_file_name="cl_avahi_$service_prefix.service"
  local capitalized_prefix="${service_prefix^}"
  local  service_name="CL $capitalized_prefix Service"
  local identifier="$service_prefix.$IDENTIFIER_BASE"
  
  echo "Stopping '$service_prefix' service..."
  rm -f "$AVAHI_SERVICE_DIR/$service_file_name"
  echo "Service file "$AVAHI_SERVICE_DIR/$service_file_name" removed."
}

# --- Main logic using a while loop ---
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    -start)
      if [ -z "$2" ]; then
        echo "Error: Missing argument for -start. Skipping."
        shift
        continue
      fi
      # Parse the argument to get the service prefix and port
      service_prefix=$(echo "$2" | cut -d'@' -f1)
      port=$(echo "$2" | cut -d'@' -f2)
      start_service "$service_prefix" "$port"
      shift 2 # Shift twice to consume -start and the argument
      ;;
    -stop)
      if [ -z "$2" ]; then
        echo "Error: Missing argument for -stop. Skipping."
        shift
        continue
      fi
      service_prefix=$(echo "$2" | cut -d'@' -f1)
      port=$(echo "$2" | cut -d'@' -f2)
      stop_service "$service_prefix" "$port"
      shift 2 # Shift twice to consume -stop and the argument
      ;;
    *)
      echo "Invalid argument: $1. Skipping."
      shift # Consume the invalid argument
      ;;
  esac
done

# --- Apply changes ---
echo "Reloading systemd daemon to apply changes..."
systemctl daemon-reload

echo "Restarting Avahi daemon..."
systemctl restart avahi-daemon

echo "Operation completed."