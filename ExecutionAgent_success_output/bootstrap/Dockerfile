FROM node:18-slim

# Set timezone to avoid tzdata messages
ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install essential tools
RUN apt-get update && \
    apt-get install -y git curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* || exit 0

WORKDIR /app

# Clone the Bootstrap repository
RUN git clone https://github.com/twbs/bootstrap.git || exit 0

WORKDIR /app/bootstrap

# Install Node.js dependencies
RUN npm install

CMD ["bash"]