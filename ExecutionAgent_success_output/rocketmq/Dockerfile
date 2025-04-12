FROM maven:3.8.6-openjdk-8-slim

# Set environment variables
ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install git
RUN apt-get update && apt-get install -y git && apt-get clean && rm -rf /var/lib/apt/lists/* || exit 0

WORKDIR /app

# Clone the repository
RUN git clone https://github.com/apache/rocketmq.git || exit 0

WORKDIR /app/rocketmq

CMD ["bash"]