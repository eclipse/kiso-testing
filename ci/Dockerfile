# Get latest debian (>=11)
FROM debian:12

# Zephyr arguments
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
    zlib1g-dev \
    libffi-dev \
    libssl-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    liblzma-dev \
    && rm -rf /var/lib/apt/lists/*

# kiso vsc plugin dependencies
# DL3047 wants the --process flag to be set. The flag is already set in the WGET_ARGS.
# hadolint ignore=DL3047
RUN wget ${WGET_ARGS} -qO- https://deb.nodesource.com/setup_15.x| bash -
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
# DL3047 wants the --process flag to be set. The flag is already set in the WGET_ARGS.
# hadolint ignore=DL3047
RUN wget ${WGET_ARGS} https://github.com/Kitware/CMake/releases/download/v${CMAKE_VERSION}/cmake-${CMAKE_VERSION}-Linux-${HOSTTYPE}.sh && \
	chmod +x cmake-${CMAKE_VERSION}-Linux-${HOSTTYPE}.sh && \
	./cmake-${CMAKE_VERSION}-Linux-${HOSTTYPE}.sh --skip-license --prefix=/usr/local && \
	rm -f ./cmake-${CMAKE_VERSION}-Linux-${HOSTTYPE}.sh

# Install Zephyr SDK
# DL3047 wants the --process flag to be set. The flag is already set in the WGET_ARGS.
# hadolint ignore=DL3047
RUN mkdir -p /opt/toolchains && \
	cd /opt/toolchains && \
	wget ${WGET_ARGS} https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v${ZSDK_VERSION}/zephyr-sdk-${ZSDK_VERSION}_linux-${HOSTTYPE}.tar.gz && \
	tar xf zephyr-sdk-${ZSDK_VERSION}_linux-${HOSTTYPE}.tar.gz && \
	zephyr-sdk-${ZSDK_VERSION}/setup.sh -t all -h -c && \
	rm zephyr-sdk-${ZSDK_VERSION}_linux-${HOSTTYPE}.tar.gz

# Environment settings
ENV HOME=/home/kiso

# Install pyenv
# DL3047 wants the --process flag to be set. The flag is already set in the WGET_ARGS.
# hadolint ignore=DL3047
RUN wget ${WGET_ARGS} -qO- https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash

ENV PYENV_ROOT $HOME/.pyenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

# Pre install python version for python TOX
RUN pyenv install 3.7 \
    && pyenv install 3.8 \
    && pyenv install 3.9 \
    && pyenv install 3.10

RUN /opt/toolchains/zephyr-sdk-${ZSDK_VERSION}/setup.sh -c

# Install python packages. pip cache disabled to reduce docker image size.
RUN python3 -m pip install --no-cache-dir poetry tox west \
    && chmod -R 777 ${HOME}
ENV PATH="/home/kiso/.local/bin:${PATH}"
