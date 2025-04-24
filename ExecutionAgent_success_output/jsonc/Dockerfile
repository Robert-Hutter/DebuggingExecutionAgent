FROM ubuntu:20.04

# Set timezone to avoid tzdata prompts
ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install necessary packages
RUN apt-get update && \
    apt-get install -y git gcc cmake doxygen valgrind && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* || exit 0

WORKDIR /app

# Clone the repository
RUN git clone https://github.com/json-c/json-c.git || exit 0

WORKDIR /app/json-c

CMD ["bash"]