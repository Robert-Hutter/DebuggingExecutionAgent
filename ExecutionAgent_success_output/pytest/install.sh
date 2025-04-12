#!/bin/bash

# Script to set up and run tests for the pytest repository
cd pytest || exit 1

# Set up Python environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip setuptools wheel
pip install -e .
pip install tox coverage

# Run tests using tox
tox

# Deactivate the virtual environment
deactivate

echo "Setup and test execution completed."