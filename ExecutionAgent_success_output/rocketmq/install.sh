#!/bin/bash

# Exit on error
set -e

# Function to display messages
function echo_message {
  echo "===================================="
  echo "$1"
  echo "===================================="
}

echo_message "Setting up environment for Apache RocketMQ"

# Update package list and install required packages
echo_message "Updating package list and installing necessary packages"
apt-get update
apt-get install -y maven openjdk-8-jdk git

# Build the project
echo_message "Building the project"
mvn clean install

# Run tests
echo_message "Running tests"
mvn test

echo_message "Setup and installation completed successfully!"