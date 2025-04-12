#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Install necessary dependencies
apt-get update
apt-get install -y gradle git

# Build the project
./gradlew build

# Run tests
./gradlew test

echo "Setup and tests completed successfully."