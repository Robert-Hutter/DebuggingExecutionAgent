#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

# Create a build directory
mkdir build
cd build

# Run CMake configuration
cmake -D CMAKE_BUILD_TYPE=Release ..

# Build the project
make

# Run tests
ctest --output-on-failure

echo "Build and test setup completed. All tests passed successfully."