#!/bin/bash

# Ensure the script stops on any error
set -e

# Step 2: Set up Python environment
 apt-get update
 apt-get install -y python3.10 python3.10-venv python3.10-dev libmemcached-dev

# Step 3: Create a virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Step 4: Upgrade packaging tools
pip install --upgrade pip setuptools wheel

# Step 5: Install required packages
pip install -e .

# Step 6: Install Tox
pip install tox

# Step 7: Run tests
python -m tox

echo "Setup and tests completed."