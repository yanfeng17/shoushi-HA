FROM python:3.11-slim-bookworm

# Install system dependencies required by OpenCV and MediaPipe
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    jq \
    tzdata \
    curl \
    ca-certificates \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgfortran5 \
    libavcodec59 \
    libavformat59 \
    libswscale6 \
    && rm -rf /var/lib/apt/lists/*

# Install bashio for Home Assistant integration
RUN pip3 install --no-cache-dir bashio

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ /app/src/
COPY main.py config.py /app/

# Copy run script
COPY run.sh /
RUN chmod a+x /run.sh

CMD ["/run.sh"]
