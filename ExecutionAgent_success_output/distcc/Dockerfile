FROM ubuntu:20.04

# Set the timezone to avoid tzdata prompts
ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install necessary packages
RUN apt-get update && \
    apt-get install -y git gcc make python3 python3-dev python3-setuptools libiberty-dev autoconf clang libavahi-client-dev automake && \
    apt-get clean && rm -rf /var/lib/apt/lists/* || exit 0

WORKDIR /app

# Clone the repository
RUN git clone https://github.com/distcc/distcc || exit 0

WORKDIR /app/distcc

CMD ["bash"]