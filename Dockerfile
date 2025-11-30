ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.11-alpine3.19
FROM ${BUILD_FROM}

# Install system dependencies required by OpenCV and MediaPipe
RUN apk add --no-cache \
    libstdc++ \
    libgomp \
    libgcc \
    && apk add --no-cache --virtual .build-deps \
    gcc \
    g++ \
    make \
    musl-dev \
    linux-headers

# Install OpenCV dependencies
RUN apk add --no-cache \
    libavformat \
    libavcodec \
    libswscale \
    libglib-2.0 \
    libsm \
    libxext \
    libxrender

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

# Copy application code
COPY src/ /app/src/
COPY main.py config.py /app/

# Copy run script
COPY run.sh /
RUN chmod a+x /run.sh

CMD ["/run.sh"]
