#!/bin/bash

# Set up Python environment
python3 -m venv venv
. venv/bin/activate

# Install dependencies
pip install --upgrade pip setuptools wheel meson[ninja] meson-python
pip install versioneer[toml] python-dateutil pytest>=7.3.2 pytest-xdist>=3.4.0 hypothesis>=6.84.0

# Build and install pandas
pip install -e . --no-build-isolation --config-settings editable-verbose=true

# Run tests
pytest
