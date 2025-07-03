#!/bin/bash

# Exit if any command fails or a variable is unset.
set -eu

# Check if a file path was provided as an argument.
if [ -z "$1" ]; then
    echo "Error: No file path provided." >&2
    exit 1
fi

# Start searching from the directory containing the edited file.
CURRENT_DIR=$(dirname "$1")

# Loop upwards through the directory tree.
while [ "$CURRENT_DIR" != "/" ]; do
    # Check if a Makefile exists in the current directory.
    # This file indicates the root of a subproject.
    if [ -f "$CURRENT_DIR/Makefile" ]; then
        echo "Found Makefile in $CURRENT_DIR. Running command..."
        # Use a subshell to run the command in the target directory.
        (cd "$CURRENT_DIR" && poetry run make pr-ready)
        # Exit successfully after running the command.
        exit 0
    fi
    # If no Makefile is found, move one directory up.
    CURRENT_DIR=$(dirname "$CURRENT_DIR")
done

# If the loop completes, no Makefile was found.
echo "No Makefile found in any parent directory of '$1'." >&2
exit 1