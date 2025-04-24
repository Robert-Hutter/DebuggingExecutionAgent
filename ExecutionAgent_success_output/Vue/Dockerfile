FROM node:18-slim

# Set the timezone to avoid tzdata messages
ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install git and other necessary tools
RUN apt-get update && apt-get install -y git && apt-get clean && rm -rf /var/lib/apt/lists/* || exit 0

WORKDIR /app

# Clone the repository
RUN git clone https://github.com/vuejs/vue.git || exit 0

WORKDIR /app/vue

CMD ["bash"]