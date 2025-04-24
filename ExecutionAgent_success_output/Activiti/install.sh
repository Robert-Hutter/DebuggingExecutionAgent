#!/bin/bash

echo $JAVA_HOME
# Install dependencies
mvn clean install

# Run tests
mvn test