#!/bin/bash

# Update package index
apt-get update

# Install necessary dependencies
apt-get install -y \
    git \
    gcc \
    make \
    libcurl4-gnutls-dev \
    libexpat1-dev \
    libz-dev \
    libssl-dev \
    gettext \
    asciidoc \
    xmlto \
    docbook2x

# Build and install Git
make prefix=/usr all doc info
make prefix=/usr install install-doc install-html install-info