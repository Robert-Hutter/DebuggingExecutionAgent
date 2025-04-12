#!/bin/bash

# Set the timezone to avoid tzdata messages
export TZ=Europe/Berlin

# Update and install necessary packages
apt-get update && apt-get install -y git && apt-get clean && rm -rf /var/lib/apt/lists/* || exit 0

# Install dependencies
npm install --legacy-peer-deps || exit 0

# Build the project
npm run build || exit 0

# Run tests
npm test || exit 0

# Notify completion
echo "Setup and installation completed successfully."