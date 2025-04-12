FROM ubuntu:20.04

# Set the timezone to avoid tzdata prompts
ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install git, CMake, and build tools
RUN apt-get update && \
    apt-get install -y git cmake build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* || exit 0

WORKDIR /app

# Clone the repository
RUN git clone https://github.com/nlohmann/json.git || exit 0

WORKDIR /app/json

CMD ["bash"]