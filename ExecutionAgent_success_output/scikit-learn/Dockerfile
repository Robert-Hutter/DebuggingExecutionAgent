FROM python:3.10-slim

# Important to add the following two lines to avoid interruptive message of tzdata
ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install git, gcc, bash, and other necessary build tools
RUN apt-get update && \
    apt-get install -y git gcc build-essential python3-dev python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* || exit 0

WORKDIR /app

# Clone the repository
RUN git clone https://github.com/scikit-learn/scikit-learn.git || exit 0

WORKDIR /app/scikit-learn

# Install dependencies
RUN pip install cython numpy scipy joblib threadpoolctl matplotlib pytest

CMD ["bash"]