FROM ubuntu:latest

# Important to add the following two lines to avoid interruptive message of tzdata
ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone || exit 0

# Install necessary build tools and dependencies
RUN apt-get update && \
    apt-get install -y git gcc make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
    libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev \
    liblzma-dev python3-openssl git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* || exit 0

WORKDIR /app

# Clone the repository
RUN git clone https://github.com/python/cpython.git || exit 0

WORKDIR /app/cpython