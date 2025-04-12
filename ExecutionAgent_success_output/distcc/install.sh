#!/bin/bash

# Update and install necessary packages
apt-get update && apt-get install -y curl libpopt-dev && \
    locale-gen en_US.UTF-8 && \
    update-locale LANG=en_US.UTF-8

cd /tmp && \
    curl -LO https://ftp.gnu.org/gnu/autoconf/autoconf-2.71.tar.gz && \
    tar xzf autoconf-2.71.tar.gz && \
    cd autoconf-2.71 && \
    ./configure && \
    make && \
    make install && \
    cd / && rm -rf /tmp/autoconf-2.71*


cd /app/distcc

# Build
./autogen.sh     # Generate configure script
./configure      # Configure the build
make             # Build the project


# Run tests
make check
