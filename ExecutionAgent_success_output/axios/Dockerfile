FROM node:18-slim

# Install git
RUN apt-get update && apt-get install -y git && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Clone the repository
RUN git clone https://github.com/axios/axios.git .

# Install dependencies
RUN npm install

# Set the command to run tests
CMD ["/bin/bash"]