#!/bin/bash

# Build the project
mvn clean package -DskipTests

# Run tests
mvn test