# Get latest debian (>=10)
FROM debian:10

ARG ZSDK_VERSION=0.14.2
ARG WGET_ARGS="-q --show-progress --progress=bar:force:noscroll --no-check-certificate"
ARG HOSTTYPE=x86_64
ARG CMAKE_VERSION=3.20.5

# Set the working directory to /app
WORKDIR /kiso-project
# Define environment variable
ENV NAME kiso-container
# Update package management and install necessary packages
RUN apt-get update && apt-get install -y \
    g++ \
    gcc \
    make \
    gcc-multilib \
    g++-multilib \
    libmagic1 \
    git \
    graphviz \
    lcov \
    curl \
    python3 \
    python3-pip \
    python3-dev \
    python3-setuptools \
    python3-wheel \
    ninja-build \
    gperf \
    ccache \
    dfu-util \
    device-tree-compiler \
    wget \
    xz-utils \
    file \
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


# Install CMake (for Zephyr)
RUN wget ${WGET_ARGS} https://github.com/Kitware/CMake/releases/download/v${CMAKE_VERSION}/cmake-${CMAKE_VERSION}-Linux-${HOSTTYPE}.sh && \
	chmod +x cmake-${CMAKE_VERSION}-Linux-${HOSTTYPE}.sh && \
	./cmake-${CMAKE_VERSION}-Linux-${HOSTTYPE}.sh --skip-license --prefix=/usr/local && \
	rm -f ./cmake-${CMAKE_VERSION}-Linux-${HOSTTYPE}.sh

# Install Zephyr SDK
RUN mkdir -p /opt/toolchains && \
	cd /opt/toolchains && \
	wget ${WGET_ARGS} https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v${ZSDK_VERSION}/zephyr-sdk-${ZSDK_VERSION}_linux-${HOSTTYPE}.tar.gz && \
	tar xf zephyr-sdk-${ZSDK_VERSION}_linux-${HOSTTYPE}.tar.gz && \
	zephyr-sdk-${ZSDK_VERSION}/setup.sh -t all -h -c && \
	rm zephyr-sdk-${ZSDK_VERSION}_linux-${HOSTTYPE}.tar.gz

# Environment settings
ENV HOME=/home/kiso

RUN /opt/toolchains/zephyr-sdk-${ZSDK_VERSION}/setup.sh -c

RUN python3 -m pip install poetry \
    && python3 -m pip install west \
    && chmod -R 777 ${HOME}
ENV PATH="/home/kiso/.local/bin:${PATH}"
