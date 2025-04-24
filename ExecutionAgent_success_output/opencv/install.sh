#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Update package lists and install necessary dependencies
echo "Installing dependency packages..."
apt-get update
apt-get install -y git cmake build-essential libgtk2.0-dev pkg-config \
    libavcodec-dev libavformat-dev libswscale-dev python-dev python-numpy \
    libtbb2 libtbb-dev libjpeg-dev libpng-dev libtiff-dev libdc1394-22-dev \
    python3-pip python3-numpy


# Create build directory and navigate to it
echo "Creating build directory..."
mkdir -p build
cd build

# Configure the project using CMake
echo "Configuring the project..."
cmake ..

# Build the project
echo "Building the project..."
make -j$(nproc --all)

echo "Build completed successfully."