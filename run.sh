#!/bin/bash
set -e

echo "[INFO] Starting MediaPipe Gesture Control addon..."

# Read configuration from Home Assistant options.json
CONFIG_PATH=/data/options.json

# Read configuration values using jq
export RTSP_URL=$(jq -r '.rtsp_url' $CONFIG_PATH)
export MQTT_BROKER=$(jq -r '.mqtt_broker' $CONFIG_PATH)
export MQTT_PORT=$(jq -r '.mqtt_port' $CONFIG_PATH)
export MQTT_USERNAME=$(jq -r '.mqtt_username // ""' $CONFIG_PATH)
export MQTT_PASSWORD=$(jq -r '.mqtt_password // ""' $CONFIG_PATH)
export FRAME_WIDTH=$(jq -r '.frame_width' $CONFIG_PATH)
export FRAME_HEIGHT=$(jq -r '.frame_height' $CONFIG_PATH)
export TARGET_FPS=$(jq -r '.target_fps' $CONFIG_PATH)
export GESTURE_CONFIDENCE_THRESHOLD=$(jq -r '.gesture_confidence_threshold' $CONFIG_PATH)
export GESTURE_STABLE_DURATION=$(jq -r '.gesture_stable_duration' $CONFIG_PATH)
export GESTURE_COOLDOWN=$(jq -r '.gesture_cooldown' $CONFIG_PATH)
export RTSP_RECONNECT_DELAY=$(jq -r '.rtsp_reconnect_delay' $CONFIG_PATH)
export LOG_LEVEL=$(jq -r '.log_level // "INFO"' $CONFIG_PATH)
export SKIP_FRAMES=$(jq -r '.skip_frames // 1' $CONFIG_PATH)

# Expression detection configuration
export ENABLE_EXPRESSION_DETECTION=$(jq -r '.enable_expression_detection // true' $CONFIG_PATH)
export EXPRESSION_CONFIDENCE_THRESHOLD=$(jq -r '.expression_confidence_threshold // 0.3' $CONFIG_PATH)

# Debug and visualization
export DEBUG_VISUALIZATION=$(jq -r '.debug_visualization // true' $CONFIG_PATH)
export PUBLISH_DETAILED_BLENDSHAPES=$(jq -r '.publish_detailed_blendshapes // true' $CONFIG_PATH)
export BLENDSHAPES_MIN_THRESHOLD=$(jq -r '.blendshapes_min_threshold // 0.05' $CONFIG_PATH)

# Expression thresholds
export MOUTH_OPEN_THRESHOLD=$(jq -r '.mouth_open_threshold // 0.3' $CONFIG_PATH)
export JAW_OPEN_THRESHOLD=$(jq -r '.jaw_open_threshold // 0.5' $CONFIG_PATH)
export SMILE_THRESHOLD=$(jq -r '.smile_threshold // 0.4' $CONFIG_PATH)
export FROWN_THRESHOLD=$(jq -r '.frown_threshold // 0.3' $CONFIG_PATH)
export BLINK_THRESHOLD=$(jq -r '.blink_threshold // 0.7' $CONFIG_PATH)
export PUCKER_THRESHOLD=$(jq -r '.pucker_threshold // 0.4' $CONFIG_PATH)

echo "[INFO] Configuration loaded:"
echo "[INFO]   MQTT Broker: ${MQTT_BROKER}:${MQTT_PORT}"
echo "[INFO]   Frame Size: ${FRAME_WIDTH}x${FRAME_HEIGHT}"
echo "[INFO]   Target FPS: ${TARGET_FPS}"

# Suppress FFmpeg and libav error messages
export FFREPORT=0
export AV_LOG_FORCE_NOCOLOR=1
export OPENCV_FFMPEG_LOGLEVEL=-8
export PYTHONWARNINGS="ignore"

# Start the Python application
cd /app

# Use unbuffered output to ensure logs appear immediately
export PYTHONUNBUFFERED=1

echo "[INFO] Starting Python application..."

# Run Python with unbuffered output
# For now, show all output including FFmpeg errors for debugging
python3 -u main.py
