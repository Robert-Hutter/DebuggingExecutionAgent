FROM python:3.10-slim

ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && apt-get install -y git gcc bash && apt-get clean && rm -rf /var/lib/apt/lists/* || exit 0

WORKDIR /app

RUN git clone https://github.com/django/django.git || exit 0

WORKDIR /app/django

RUN pip install --upgrade pip setuptools wheel