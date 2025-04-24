#!/bin/bash

# Update package list and install necessary packages
apt-get update && apt-get install -y git maven

# Build the project using Maven
mvn clean install

# Run tests
mvn test