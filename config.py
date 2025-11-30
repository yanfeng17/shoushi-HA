import os

# RTSP Configuration
RTSP_URL = os.getenv('RTSP_URL', 'rtsp://admin:password@192.168.1.100:554/stream1')

# MQTT Configuration
MQTT_BROKER = os.getenv('MQTT_BROKER', 'core-mosquitto')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
MQTT_USERNAME = os.getenv('MQTT_USERNAME', '')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', '')
MQTT_CLIENT_ID = os.getenv('MQTT_CLIENT_ID', 'gesture_control')

# MQTT Topics
MQTT_DISCOVERY_PREFIX = 'homeassistant'
MQTT_STATE_TOPIC = 'mediapipe/gesture/state'
MQTT_DEVICE_NAME = 'gesture_control'

# Video Processing Configuration
FRAME_WIDTH = int(os.getenv('FRAME_WIDTH', '320'))
FRAME_HEIGHT = int(os.getenv('FRAME_HEIGHT', '240'))
TARGET_FPS = int(os.getenv('TARGET_FPS', '15'))
SKIP_FRAMES = int(os.getenv('SKIP_FRAMES', '1'))  # Process every Nth frame (1=all, 2=half, 3=third)

# Gesture Recognition Configuration
GESTURE_CONFIDENCE_THRESHOLD = float(os.getenv('GESTURE_CONFIDENCE_THRESHOLD', '0.65'))
GESTURE_STABLE_DURATION = float(os.getenv('GESTURE_STABLE_DURATION', '0.3'))  # seconds
GESTURE_COOLDOWN = float(os.getenv('GESTURE_COOLDOWN', '1.5'))  # seconds

# RTSP Reconnection
RTSP_RECONNECT_DELAY = int(os.getenv('RTSP_RECONNECT_DELAY', '5'))  # seconds

# MediaPipe Configuration
MAX_NUM_HANDS = 1
MIN_DETECTION_CONFIDENCE = 0.5  # Lower for faster detection
MIN_TRACKING_CONFIDENCE = 0.5
