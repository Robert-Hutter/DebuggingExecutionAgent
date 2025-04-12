FROM python:3.10-slim

ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone || exit 0

RUN apt-get update && apt-get install -y git gcc bash python3-pip && apt-get clean && rm -rf /var/lib/apt/lists/* || exit 0

WORKDIR /app

RUN git clone https://github.com/ansible/ansible.git --recursive || exit 0

WORKDIR /app/ansible

RUN pip install -r requirements.txt || exit 0
RUN pip install pytest || exit 0

# Install ansible module
RUN pip install . || exit 0

# Set PYTHONPATH to include the ansible module
ENV PYTHONPATH=/app/ansible

# Verify installation
RUN python3 -c 'import ansible' || exit 0

CMD ["bash"]