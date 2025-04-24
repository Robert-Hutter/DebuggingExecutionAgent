FROM node:18

# Set the working directory
WORKDIR /app

# Clone the repository
RUN git clone https://github.com/facebook/react-native.git .

# Install dependencies
RUN yarn install

# Expose the port (if necessary)
# EXPOSE 8081

CMD ["bash"]