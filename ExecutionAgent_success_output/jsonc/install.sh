#!/bin/bash


# Create a build directory
mkdir -p json-c-build
cd json-c-build

# Run CMake to configure the project
cmake ..

# Build the project
make

# Run the tests
make test