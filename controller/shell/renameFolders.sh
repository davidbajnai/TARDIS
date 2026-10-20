#!/bin/bash

# Path to the CSV file
csv_file="renameFolders.csv"

# Base directory where the folders are located
base_dir="/var/www/html/data/Results"

# Skip the header and read only old/new columns
tail -n +2 "$csv_file" | while IFS=',' read -r id old_name new_name; do
  # Skip empty lines
  [ -z "$old_name" ] && continue

  old_path="$base_dir/$old_name"
  new_path="$base_dir/$new_name"

  if [ -d "$old_path" ]; then
    echo "Renaming $old_path to $new_path"
    mv "$old_path" "$new_path"
  else
    echo "Folder $old_path not found. Skipping."
  fi
done