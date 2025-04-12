#!/bin/bash

# Update and install necessary packages
apt-get update
apt-get install -y build-essential python3-dev python3-pip git

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install cython numpy scipy joblib threadpoolctl matplotlib pytest meson meson-python ninja

# Install scikit-learn
pip install --editable . --verbose --no-build-isolation --config-settings editable-verbose=true

# Run tests
pytest