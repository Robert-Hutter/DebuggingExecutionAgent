FROM python:3.11-slim

ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone || exit 0

RUN apt-get update && apt-get install -y git gcc bash && apt-get clean && rm -rf /var/lib/apt/lists/* || exit 0

WORKDIR /app

RUN git clone https://github.com/pytest-dev/pytest || exit 0

WORKDIR /app/pytest

CMD ["bash"]