#!/bin/bash

# Create and activate a virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements/dev.in
pip install -r requirements/tests.in

# Run tests using tox
tox

echo "Tests have been run. Check the output above for results."