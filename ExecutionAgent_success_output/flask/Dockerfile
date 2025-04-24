FROM python:3.10-slim

# Important to add the following two lines to avoid interruptive message of tzdata
ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone || exit 0

# Install git, gcc, bash, and other necessary build tools
RUN apt-get update && apt-get install -y git gcc bash && apt-get clean && rm -rf /var/lib/apt/lists/* || exit 0

WORKDIR /app

# Clone the repository
RUN git clone https://github.com/pallets/flask || exit 0

WORKDIR /app/flask

CMD ["bash"]