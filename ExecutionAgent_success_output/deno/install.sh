#!/bin/bash

# Update and install necessary packages
apt-get update && apt-get install -y cmake libglib2.0-dev protobuf-compiler clang

# Clone the Deno repository
if [ ! -d "deno" ]; then
  git clone --recurse-submodules https://github.com/denoland/deno.git
fi

cd deno

# Build Deno
cargo build --release

# Run tests
cargo test
