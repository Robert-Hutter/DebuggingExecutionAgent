#!/bin/bash

# Run autoconf to prepare the build system
autoreconf -fvi

# Configure the build system
./configure --enable-werror

# Compile the project
make -j$(nproc)

# Run tests
make check VERBOSE=1

echo "Setup and testing complete."