#!/usr/bin/env bashio

set -e

bashio::log.info "Starting MediaPipe Gesture Control addon..."

# Read configuration from Home Assistant options
CONFIG_PATH=/data/options.json

export RTSP_URL=$(bashio::config 'rtsp_url')
export MQTT_BROKER=$(bashio::config 'mqtt_broker')
export MQTT_PORT=$(bashio::config 'mqtt_port')
export MQTT_USERNAME=$(bashio::config 'mqtt_username')
export MQTT_PASSWORD=$(bashio::config 'mqtt_password')
export FRAME_WIDTH=$(bashio::config 'frame_width')
export FRAME_HEIGHT=$(bashio::config 'frame_height')
export TARGET_FPS=$(bashio::config 'target_fps')
export GESTURE_CONFIDENCE_THRESHOLD=$(bashio::config 'gesture_confidence_threshold')
export GESTURE_STABLE_DURATION=$(bashio::config 'gesture_stable_duration')
export GESTURE_COOLDOWN=$(bashio::config 'gesture_cooldown')
export RTSP_RECONNECT_DELAY=$(bashio::config 'rtsp_reconnect_delay')

bashio::log.info "Configuration loaded:"
bashio::log.info "  MQTT Broker: ${MQTT_BROKER}:${MQTT_PORT}"
bashio::log.info "  Frame Size: ${FRAME_WIDTH}x${FRAME_HEIGHT}"
bashio::log.info "  Target FPS: ${TARGET_FPS}"

# Start the Python application
cd /app
exec python3 main.py
