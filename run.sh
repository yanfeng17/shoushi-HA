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

echo "[INFO] Configuration loaded:"
echo "[INFO]   MQTT Broker: ${MQTT_BROKER}:${MQTT_PORT}"
echo "[INFO]   Frame Size: ${FRAME_WIDTH}x${FRAME_HEIGHT}"
echo "[INFO]   Target FPS: ${TARGET_FPS}"

# Start the Python application
cd /app
exec python3 main.py
