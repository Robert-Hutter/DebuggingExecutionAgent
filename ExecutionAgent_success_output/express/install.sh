#!/bin/bash

# Set up the environment and install dependencies for Express

# Clone the repository
if [ ! -d "express" ]; then
  git clone https://github.com/expressjs/express
fi

cd express

# Install dependencies
npm install

# Run tests
npm test