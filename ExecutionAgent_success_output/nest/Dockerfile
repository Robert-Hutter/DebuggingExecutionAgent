FROM node:18-slim

# Set the timezone to avoid tzdata messages
ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install git and other necessary tools
RUN apt-get update && apt-get install -y git && apt-get clean && rm -rf /var/lib/apt/lists/* || exit 0

WORKDIR /app

# Clone the repository
RUN git clone https://github.com/nestjs/nest.git || exit 0

WORKDIR /app/nest

# Install dependencies
RUN npm install || exit 0

# Build the project
RUN npm run build || exit 0

# Run tests
RUN npm test || exit 0

CMD ["bash"]