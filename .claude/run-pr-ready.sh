#!/bin/bash

# Exit immediately if a command fails.
set -e

# Start searching from the directory of the edited file, provided as the first argument.
CURRENT_DIR=$(dirname "$1")

# Loop upwards as long as the current path is inside 'aihub-core'.
# The glob pattern *"/"aihub-core* checks if the string contains the project directory.
while [[ "$CURRENT_DIR" == *"/"aihub-core* ]]; do
    # If a Makefile exists in the current directory, we've found our subproject.
    if [ -f "$CURRENT_DIR/Makefile" ]; then
        echo "Found Makefile in $CURRENT_DIR. Running 'poetry run make pr-ready'..."
        # Run the command in a subshell and exit successfully.
        (cd "$CURRENT_DIR" && poetry run make pr-ready)
        exit 0
    fi
    # Move up to the parent directory for the next iteration.
    CURRENT_DIR=$(dirname "$CURRENT_DIR")
done

# If the loop finishes, no Makefile was found within the project boundary.
echo "No Makefile found for '$1'. No action taken."
exit 0