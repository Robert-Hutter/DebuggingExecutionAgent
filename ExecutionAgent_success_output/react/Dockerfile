FROM node:18

# Set the timezone
ENV TZ=America/Los_Angeles
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install git and other necessary build tools
RUN apt-get update && apt-get install -y git && apt-get clean && rm -rf /var/lib/apt/lists/* || exit 0

WORKDIR /app

# Clone the repository
RUN git clone https://github.com/facebook/react || exit 0

WORKDIR /app/react

CMD ["bash"]