FROM python:3.10-slim

ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone || exit 0

RUN apt-get update && apt-get install -y git gcc bash build-essential && apt-get clean && rm -rf /var/lib/apt/lists/* || exit 0

WORKDIR /app

RUN git clone https://github.com/python/cpython.git || exit 0

WORKDIR /app/cpython

CMD ["bash"]