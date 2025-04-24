#!/bin/bash

# Install dependencies
apt-get update && apt-get install -y chromium chromium-driver
npm install

# Run linting
npm run lint

# Run tests
npm test
