FROM ubuntu:20.04

# Set the timezone to avoid interactive prompts
ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install necessary build tools and dependencies
RUN apt-get update && \
    apt-get install -y git build-essential cmake libmbedtls-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Clone the repository
RUN git clone https://github.com/libevent/libevent.git

WORKDIR /app/libevent

CMD ["bash"]