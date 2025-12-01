"""
Configuration module for MediaPipe Gesture Control.

v2.0.0: Simplified to pure gesture recognition system.
Removed: Expression detection, motion detection, visualization.
"""

import os

# ============================================================================
# RTSP Configuration
# ============================================================================
RTSP_URL = os.getenv('RTSP_URL', 'rtsp://admin:password@192.168.1.100:554/stream1')
RTSP_RECONNECT_DELAY = int(os.getenv('RTSP_RECONNECT_DELAY', '5'))

# ============================================================================
# MQTT Configuration
# ============================================================================
MQTT_BROKER = os.getenv('MQTT_BROKER', 'core-mosquitto')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
MQTT_USERNAME = os.getenv('MQTT_USERNAME', '')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', '')
MQTT_CLIENT_ID = 'gesture_control'

# MQTT Topics
MQTT_DISCOVERY_PREFIX = 'homeassistant'
MQTT_STATE_TOPIC = 'mediapipe/gesture/state'
MQTT_DEVICE_NAME = 'gesture_control'

# ============================================================================
# Video Processing Configuration
# ============================================================================
FRAME_WIDTH = int(os.getenv('FRAME_WIDTH', '320'))
FRAME_HEIGHT = int(os.getenv('FRAME_HEIGHT', '240'))
TARGET_FPS = int(os.getenv('TARGET_FPS', '15'))
SKIP_FRAMES = int(os.getenv('SKIP_FRAMES', '1'))

# ============================================================================
# Gesture Recognition Configuration
# ============================================================================
GESTURE_CONFIDENCE_THRESHOLD = float(os.getenv('GESTURE_CONFIDENCE_THRESHOLD', '0.65'))
GESTURE_MIN_DETECTIONS = int(os.getenv('GESTURE_MIN_DETECTIONS', '2'))
GESTURE_COOLDOWN = float(os.getenv('GESTURE_COOLDOWN', '1.5'))

# ============================================================================
# MediaPipe Hands Configuration
# ============================================================================
MAX_NUM_HANDS = 1
MIN_DETECTION_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.5

# ============================================================================
# Gesture Toggles (10 static gestures)
# ============================================================================
ENABLED_GESTURES = {
    # Basic gestures (default: enabled)
    'OPEN_PALM': os.getenv('ENABLE_OPEN_PALM', 'true').lower() == 'true',
    'CLOSED_FIST': os.getenv('ENABLE_CLOSED_FIST', 'true').lower() == 'true',
    'POINTING_UP': os.getenv('ENABLE_POINTING_UP', 'true').lower() == 'true',
    'OK_SIGN': os.getenv('ENABLE_OK_SIGN', 'true').lower() == 'true',
    
    # New gestures (default: enabled for common ones)
    'THUMBS_UP': os.getenv('ENABLE_THUMBS_UP', 'true').lower() == 'true',
    'THUMBS_DOWN': os.getenv('ENABLE_THUMBS_DOWN', 'true').lower() == 'true',
    'PEACE': os.getenv('ENABLE_PEACE', 'true').lower() == 'true',
    
    # Advanced gestures (default: disabled)
    'THREE_FINGERS': os.getenv('ENABLE_THREE_FINGERS', 'false').lower() == 'true',
    'FOUR_FINGERS': os.getenv('ENABLE_FOUR_FINGERS', 'false').lower() == 'true',
    'PINCH': os.getenv('ENABLE_PINCH', 'false').lower() == 'true',
}

# ============================================================================
# Logging Configuration
# ============================================================================
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
