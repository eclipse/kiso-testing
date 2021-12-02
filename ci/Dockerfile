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
    python3 \
    python3-pip
ENV HOME=/home/kiso
RUN python3 -m pip install pipenv
RUN chmod -R 777 ${HOME}
ENV PATH="/home/kiso/.local/bin:${PATH}"