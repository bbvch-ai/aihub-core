#!/bin/bash

# Simple wrapper to run the deployment in Poetry environment
cd "$(dirname "$0")"

if command -v poetry &> /dev/null; then
    poetry run ./setup_and_deploy.sh
else
    echo "Poetry not found, running directly..."
    ./setup_and_deploy.sh
fi