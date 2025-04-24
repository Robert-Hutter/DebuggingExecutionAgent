FROM openjdk:11-jdk-slim

# Set the timezone
ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install necessary tools
RUN apt-get update && \
    apt-get install -y git maven wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* || exit 0

WORKDIR /app

# Clone the repository
RUN git clone https://github.com/apache/dubbo.git || exit 0

WORKDIR /app/dubbo

RUN ./mvnw --batch-mode --no-snapshot-updates -e --no-transfer-progress --fail-fast \
  clean source:jar install -Pjacoco,checkstyle \
  -Dmaven.wagon.httpconnectionManager.ttlSeconds=120 \
  -Dmaven.wagon.http.retryHandler.count=5 \
  -Dmaven.test.skip=true \
  -Dmaven.test.skip.exec=true

CMD ["bash"]