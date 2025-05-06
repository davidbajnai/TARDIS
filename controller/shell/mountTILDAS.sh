#!/bin/bash

'''
This script mounts the TILDAS PC as a CIFS network share to a local directory.

It is automatically invoked by `copyFiles.php` if the TILDAS PC is not already mounted.
'''

# Load credentials
CONFIG_FILE="/var/www/html/controller/config/.fileshare.conf"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Config file not found: $CONFIG_FILE"
    exit 1
fi

source "$CONFIG_FILE"

# Check if already mounted
if mount | grep -q "$remote on $mount_point type cifs"; then
    echo "Share is already mounted."
    exit 0
fi

# Try to mount
if sudo mount -t cifs "$remote" "$mount_point" -o username="$username",password="$password"; then
    echo "Mount successful."
else
    echo "Failed to mount the share."
    exit 2
fi