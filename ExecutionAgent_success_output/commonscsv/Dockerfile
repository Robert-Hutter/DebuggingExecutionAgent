FROM maven:3.9.6-eclipse-temurin-17

# Important to add the following two lines to avoid interruptive message of tzdata
ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone || exit 0

# Install git
RUN apt-get update && apt-get install -y git && apt-get clean && rm -rf /var/lib/apt/lists/* || exit 0

WORKDIR /app

# Clone the repository
RUN git clone https://github.com/apache/commons-csv.git || exit 0

WORKDIR /app/commons-csv

CMD ["bash"]