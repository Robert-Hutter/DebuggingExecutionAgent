#!/bin/bash

apt install -y \
    build-essential \
    liblzo2-dev \
    libpam0g-dev \
    liblz4-dev \
    libcap-ng-dev \
    libnl-genl-3-dev \
    linux-libc-dev \
    man2html \
    libcmocka-dev \
    python3-docutils \
    autoconf \
    automake \
    libtool

autoreconf -fvi

# Configure the build system
./configure --enable-werror

# Compile the project
make -j$(nproc)

# Run tests
make check VERBOSE=1

echo "Setup and testing complete."
