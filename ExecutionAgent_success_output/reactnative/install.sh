#!/bin/bash

# Update package list and install Node.js and npm
sudo apt update
sudo apt install -y nodejs npm

# Install React Native CLI globally
npm install -g react-native-cli

# Install project dependencies
npm install

# Run the test suite
npm test