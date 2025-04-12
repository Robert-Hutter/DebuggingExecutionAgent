FROM ubuntu:20.04

# Set the timezone to avoid interactive prompts
ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Update package lists and install necessary build tools and dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    sudo \
    build-essential \
    liblzo2-dev \
    libpam0g-dev \
    liblz4-dev \
    libcap-ng-dev \
    libnl-genl-3-dev \
    linux-libc-dev \
    autoconf \
    automake \
    libtool \
    cmocka-dev \
    python3-docutils \
    git \
    && apt-get clean && rm -rf /var/lib/apt/lists/* || exit 0

WORKDIR /app

# Clone the OpenVPN repository
RUN git clone https://github.com/OpenVPN/openvpn.git || exit 0

WORKDIR /app/openvpn

CMD ["bash"]