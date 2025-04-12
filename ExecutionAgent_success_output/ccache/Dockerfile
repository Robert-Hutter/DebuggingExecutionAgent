FROM ubuntu:20.04

# Set timezone to avoid tzdata prompts
ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install necessary packages
RUN apt-get update && \
    apt-get install -y git cmake g++ ninja-build libhiredis-dev libzstd-dev redis-server redis-tools && \
    apt-get clean && rm -rf /var/lib/apt/lists/* || exit 0

WORKDIR /app

# Clone the repository
RUN git clone https://github.com/ccache/ccache || exit 0

WORKDIR /app/ccache

CMD ["bash"]