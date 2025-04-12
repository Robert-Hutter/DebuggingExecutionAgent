#!/bin/bash

# Update package list and install dependencies
apt-get update
apt-get install -y python3 python3-pip python3-venv

# Configure the build
./configure --with-pydebug

# Build the project
make -s -j2

# Run the tests
make test