#!/bin/bash

# Set timezone to avoid tzdata messages
export TZ=Europe/Berlin
ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Update package list and install git
apt-get update && apt-get install -y git && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install dependencies
npm install

# Run tests
npm test