#!/bin/bash

'''
This script deletes all but the first 22 `.str` and `.stc` files in a specified folder.

It is used by `batchReprocess.py` when measurement files are copied from the TILDAS PC
to this Linux computer. The `copyFiles.php` script copies all `.str` and `.stc` files
created after the measurement start timestamp.

This cleanup script ensures that only the relevant files are kept, based on the assumption
that a changeover measurement produces 22 files (i.e., 10 cycles plus associated metadata).
All excess files beyond the first 22 are deleted.
'''

# Provide only the folder name using an argument (e.g., 250505_113815_heavyVsRef)
FOLDER_NAME="${1:-}"
BASE_PATH="/var/www/html/data/Results"
FOLDER="$BASE_PATH/$FOLDER_NAME"

# Go to the folder
cd "$FOLDER" || { echo "Folder not found: $FOLDER"; exit 1; }

# Extract unique timestamps (first 13 chars of filenames), sort them
timestamps=$(ls *.st[cr] 2>/dev/null | cut -c1-13 | sort -u)

# Keep only the first 22 timestamps
keep=$(echo "$timestamps" | head -n 22)

# Convert keep list to array
mapfile -t keep_array <<< "$keep"

# Build a grep pattern of timestamps to keep
pattern=$(printf "|^%s" "${keep_array[@]}")
pattern="${pattern:1}"  # remove leading "|"

# Delete all .str and .stc files that don't match
ls *.st[cr] 2>/dev/null | grep -Ev "$pattern" | xargs -r rm