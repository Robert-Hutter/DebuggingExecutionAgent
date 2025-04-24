FROM ubuntu:20.04

# Set timezone to avoid tzdata prompts
ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install necessary dependencies including sudo
RUN apt-get update && \
    apt-get install -y \
    git \
    gcc \
    make \
    sudo \
    libcurl4-gnutls-dev \
    libexpat1-dev \
    libz-dev \
    libssl-dev \
    gettext \
    asciidoc \
    xmlto \
    docbook2x \
    && apt-get clean && rm -rf /var/lib/apt/lists/* || exit 0

WORKDIR /app

# Clone the Git repository
RUN git clone https://github.com/git/git.git || exit 0

WORKDIR /app/git

CMD ["bash"]