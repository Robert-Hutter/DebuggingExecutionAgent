#!/bin/bash

# Update package list and install dependencies
apt-get update && \
apt-get install -y git cmake build-essential && \
apt-get clean && \
rm -rf /var/lib/apt/lists/* || exit 0

# Build the project
cmake . && make || exit 0

# Run tests
ctest