#!/bin/bash

# Update package list and install required dependencies
apt-get update
apt-get install -y git openjdk-8-jdk gradle

# Build the project
./gradlew build

# Run tests
./gradlew test
