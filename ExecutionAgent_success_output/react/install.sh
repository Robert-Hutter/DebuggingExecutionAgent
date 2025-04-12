#!/bin/bash

# Set the timezone
export TZ="America/Los_Angeles"

if ! command -v yarn &> /dev/null; then
    echo "Yarn not found. Installing..."
    npm install --global yarn
fi

# Install dependencies
echo "Installing dependencies..."
yarn install --frozen-lockfile

# Run tests
echo "Running tests..."
yarn test

echo "Setup and installation completed successfully."