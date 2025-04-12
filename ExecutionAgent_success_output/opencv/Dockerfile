FROM ubuntu:20.04

# Set the timezone to avoid tzdata prompts
ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install necessary packages
RUN apt-get update && \
    apt-get install -y git cmake build-essential libgtk2.0-dev pkg-config \
    libavcodec-dev libavformat-dev libswscale-dev python-dev python-numpy \
    libtbb2 libtbb-dev libjpeg-dev libpng-dev libtiff-dev libdc1394-22-dev \
    python3-pip python3-numpy && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Clone the OpenCV repository
RUN git clone https://github.com/opencv/opencv.git

WORKDIR /app/opencv

CMD ["bash"]