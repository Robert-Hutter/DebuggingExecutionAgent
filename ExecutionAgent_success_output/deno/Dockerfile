FROM rust:latest

# Set the working directory
WORKDIR /app

# Clone the Deno repository
RUN git clone --recurse-submodules https://github.com/denoland/deno.git

# Set the working directory to the cloned repository
WORKDIR /app/deno

# Install necessary dependencies
RUN apt-get update && \
    apt-get install -y cmake libglib2.0-dev protobuf-compiler clang && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Command to run when starting the container
CMD ["bash"]