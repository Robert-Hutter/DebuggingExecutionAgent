FROM python:3.10-slim

ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && apt-get install -y git gcc bash && apt-get clean && rm -rf /var/lib/apt/lists/* || exit 0

WORKDIR /app

RUN git clone https://github.com/keras-team/keras || exit 0

WORKDIR /app/keras

CMD ["bash"]