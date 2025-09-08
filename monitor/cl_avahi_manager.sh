#!/bin/bash

show_help() {
  echo "Usage: sudo $0 [-start service@port] [-stop service@port]"
  echo
  echo "This script manages Avahi mDNS services."
  echo
  echo "Options:"
  echo "  -start service@port   Start a new Avahi service with the specified name and port."
  echo "  -stop service@port    Stop and remove an existing Avahi service."
  echo
  echo "Example:"
  echo "  sudo $0 -start my_app@8080 -stop old_app@9090"
}
if [ "$#" -eq 0 ]; then
  show_help
  exit 0
fi

for arg in "$@"; do
  if [ "$arg" = "-h" ] || [ "$arg" = "--help" ]; then
    show_help
    exit 0
  fi
done

if [ "$(id -u)" -ne 0 ]; then
  echo "This script must be run with sudo."
  show_help
  exit 1
fi

AVAHI_SERVICE_DIR="/etc/avahi/services"




if [ -z "$IDENTIFIER_BASE" ]; then
  echo "Error: IDENTIFIER_BASE is not set. Aborting." >&2
  exit 1
fi


start_service() {
  local service_prefix="$1"
  local port="$2"
  
  local service_file_name="cl_avahi_$service_prefix.service"
  local capitalized_prefix="${service_prefix^}"
  local  service_name="CL $capitalized_prefix Service"
  local identifier="$service_prefix.$IDENTIFIER_BASE"

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

# Check for -h or --help in any position and exit immediately
for arg in "$@"; do
  if [ "$arg" = "-h" ] || [ "$arg" = "--help" ]; then
    show_help
    exit 0
  fi
done

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    -start)
      if [ -z "$2" ]; then
        echo "Error: Missing argument for -start. Skipping."
        shift
        continue
      fi
      service_prefix=$(echo "$2" | cut -d'@' -f1)
      port=$(echo "$2" | cut -d'@' -f2)
      start_service "$service_prefix" "$port"
      shift 2 
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
      shift 2 
      ;;
    -h|--help)
      show_help
      exit 0
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