#!/bin/bash

log_debug() {
  if [ "$DEBUG" = "true" ]; then
    echo "DEBUG: $1"
  fi
}


# --- Check for root privileges ---
if [ "$(id -u)" -ne 0 ]; then
  echo "This script must be run with sudo."
  exit 1
fi


# --- Get the directory of the script itself ---
SCRIPT_DIR="$( cd "$( dirname "$0" )" &> /dev/null && pwd )"

# --- Define paths and service name ---
SYSTEM_SCRIPT_DIR="/usr/local/bin"
SYSTEMD_SERVICE_DIR="/etc/systemd/system"
SERVICE_NAME="cl_monitor.service"

# --- Copy the scripts and make them executable ---
echo "Copying scripts to $SYSTEM_SCRIPT_DIR..."
cp "$SCRIPT_DIR/cl_avahi_manager.sh" "$SYSTEM_SCRIPT_DIR/"
cp "$SCRIPT_DIR/cl_monitor.sh" "$SYSTEM_SCRIPT_DIR/"

echo "Making scripts executable..."
chmod +x "$SYSTEM_SCRIPT_DIR/cl_avahi_manager.sh"
chmod +x "$SYSTEM_SCRIPT_DIR/cl_monitor.sh"

# --- Create the systemd service file ---
echo "Creating systemd service file at $SYSTEMD_SERVICE_DIR/$SERVICE_NAME..."

# Use a here document to write the service file
cat > "$SYSTEMD_SERVICE_DIR/$SERVICE_NAME" << EOF
[Unit]
Description=Cloud on Lap Service Monitor
After=network-online.target

[Service]
ExecStart=$SYSTEM_SCRIPT_DIR/cl_monitor.sh -repo@5001 -ai@5002
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

# --- Enable and start the service ---
echo "Reloading systemd daemon..."
systemctl daemon-reload

echo "Enabling and starting the $SERVICE_NAME service..."
systemctl enable "$SERVICE_NAME"
systemctl start "$SERVICE_NAME"

echo "Installation complete. The service monitor is now running."
