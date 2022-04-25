# Get latest debian (>=10)
FROM debian:10

# Set the working directory to /app
WORKDIR /kiso-project
# Define environment variable
ENV NAME kiso-container
# Update package management and install necessary packages
RUN apt-get update && apt-get install -y \
    cmake \
    g++ \
    gcc \
    git \
    graphviz \
    lcov \
    curl \
    python3 \
    python3-pip\
    && rm -rf /var/lib/apt/lists/*

# kiso vsc plugin dependencies
RUN curl -sL https://deb.nodesource.com/setup_15.x| bash -
RUN apt-get update && apt-get -y install nodejs \
    gnupg \
    libxshmfence1 \
    libglu1 \
    libasound2 \
    libgbm1 \
    libgtk-3-0 \
    libnss3 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*
RUN npm install -g typescript
RUN npm install -g vsce

# Environment settings
ENV HOME=/home/kiso
RUN python3 -m pip install poetry \
    && chmod -R 777 ${HOME}
ENV PATH="/home/kiso/.local/bin:${PATH}"
