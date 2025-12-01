import paho.mqtt.client as mqtt
import json
import time
import logging
import config

logger = logging.getLogger(__name__)


class MQTTClient:
    """
    Handles MQTT connection, Home Assistant Auto Discovery, and state publishing.
    """
    
    def __init__(self):
        self.client = mqtt.Client(client_id=config.MQTT_CLIENT_ID)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        
        # Set authentication if provided
        if config.MQTT_USERNAME and config.MQTT_PASSWORD:
            self.client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)
        
        self.connected = False
        self.discovery_sent = False
    
    def connect(self) -> bool:
        """
        Connect to MQTT broker with retry logic.
        
        Returns:
            True if connected successfully
        """
        try:
            logger.info(f"Connecting to MQTT broker at {config.MQTT_BROKER}:{config.MQTT_PORT}")
            self.client.connect(config.MQTT_BROKER, config.MQTT_PORT, keepalive=60)
            self.client.loop_start()
            
            # Wait for connection
            for _ in range(10):
                if self.connected:
                    return True
                time.sleep(0.5)
            
            return self.connected
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker."""
        if rc == 0:
            logger.info("Connected to MQTT broker successfully")
            self.connected = True
            # Send Home Assistant discovery config
            self._send_discovery_config()
        else:
            logger.error(f"Failed to connect to MQTT broker with code: {rc}")
            self.connected = False
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker."""
        logger.warning(f"Disconnected from MQTT broker with code: {rc}")
        self.connected = False
        self.discovery_sent = False
    
    def _send_discovery_config(self):
        """
        Send Home Assistant MQTT Discovery configuration for both sensors.
        Creates two separate sensor entities:
        - sensor.gesture_control: Hand gestures (static + motion)
        - sensor.expression_control: Facial expressions
        """
        if self.discovery_sent:
            return
        
        # Send gesture sensor discovery
        self._send_gesture_discovery()
        
        # Send expression sensor discovery (if enabled)
        if config.ENABLE_EXPRESSION:
            self._send_expression_discovery()
        
        self.discovery_sent = True
    
    def _send_gesture_discovery(self):
        """Send discovery config for gesture sensor."""
        discovery_topic = f"{config.MQTT_DISCOVERY_PREFIX}/sensor/gesture_control/config"
        
        discovery_payload = {
            "name": "Gesture Control",
            "unique_id": "gesture_control_sensor",
            "state_topic": config.MQTT_GESTURE_STATE_TOPIC,
            "value_template": "{{ value_json.state }}",
            "json_attributes_topic": config.MQTT_GESTURE_STATE_TOPIC,
            "icon": "mdi:hand-back-right",
            "device": {
                "identifiers": [config.MQTT_DEVICE_NAME],
                "name": "MediaPipe Gesture & Expression Recognition",
                "model": "Hand Gesture & Face Expression Detector v1.0.8",
                "manufacturer": "Custom",
                "sw_version": "1.0.8"
            }
        }
        
        result = self.client.publish(
            discovery_topic,
            json.dumps(discovery_payload),
            qos=1,
            retain=True
        )
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"Gesture sensor discovery config sent to {discovery_topic}")
        else:
            logger.error(f"Failed to send gesture discovery config: {result.rc}")
    
    def _send_expression_discovery(self):
        """Send discovery config for expression sensor."""
        discovery_topic = f"{config.MQTT_DISCOVERY_PREFIX}/sensor/expression_control/config"
        
        discovery_payload = {
            "name": "Expression Control",
            "unique_id": "expression_control_sensor",
            "state_topic": config.MQTT_EXPRESSION_STATE_TOPIC,
            "value_template": "{{ value_json.state }}",
            "json_attributes_topic": config.MQTT_EXPRESSION_STATE_TOPIC,
            "icon": "mdi:emoticon-happy",
            "device": {
                "identifiers": [config.MQTT_DEVICE_NAME],
                "name": "MediaPipe Gesture & Expression Recognition",
                "model": "Hand Gesture & Face Expression Detector v1.0.8",
                "manufacturer": "Custom",
                "sw_version": "1.0.8"
            }
        }
        
        result = self.client.publish(
            discovery_topic,
            json.dumps(discovery_payload),
            qos=1,
            retain=True
        )
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"Expression sensor discovery config sent to {discovery_topic}")
        else:
            logger.error(f"Failed to send expression discovery config: {result.rc}")
    
    def publish_gesture(self, gesture: str, confidence: float, gesture_type: str = "static"):
        """
        Publish gesture state to MQTT (separate sensor from expression).
        
        Args:
            gesture: Gesture name (e.g., "CLOSED_FIST", "WAVE", "SWIPE_LEFT")
            confidence: Detection confidence (0.0 to 1.0)
            gesture_type: Type of gesture ("static" or "motion")
        """
        if not self.connected:
            logger.warning("Not connected to MQTT broker, skipping gesture publish")
            return
        
        payload = {
            "state": gesture,
            "confidence": round(confidence, 3),
            "gesture_type": gesture_type,
            "timestamp": time.time()
        }
        
        result = self.client.publish(
            config.MQTT_GESTURE_STATE_TOPIC,
            json.dumps(payload),
            qos=1,
            retain=False
        )
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.debug(f"Published gesture: {gesture} ({gesture_type}, confidence: {confidence:.2f})")
        else:
            logger.error(f"Failed to publish gesture: {result.rc}")
    
    def publish_expression(self, expression: str, confidence: float, blendshapes: dict = None):
        """
        Publish expression state to MQTT (separate sensor from gesture).
        
        Args:
            expression: Expression name (e.g., "SMILE", "SURPRISED")
            confidence: Detection confidence (0.0 to 1.0)
            blendshapes: Optional dictionary of blendshape values
        """
        if not self.connected:
            logger.warning("Not connected to MQTT broker, skipping expression publish")
            return
        
        payload = {
            "state": expression,
            "confidence": round(confidence, 3),
            "timestamp": time.time()
        }
        
        # Add blendshapes if provided and enabled
        if blendshapes and config.PUBLISH_DETAILED_BLENDSHAPES:
            # Filter blendshapes to only include significant values
            filtered_blendshapes = {
                k: round(v, 3)
                for k, v in blendshapes.items()
                if v >= config.BLENDSHAPES_MIN_THRESHOLD
            }
            if filtered_blendshapes:
                payload["blendshapes"] = filtered_blendshapes
        
        result = self.client.publish(
            config.MQTT_EXPRESSION_STATE_TOPIC,
            json.dumps(payload),
            qos=1,
            retain=False
        )
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.debug(f"Published expression: {expression} (confidence: {confidence:.2f})")
        else:
            logger.error(f"Failed to publish expression: {result.rc}")
    
    def disconnect(self):
        """Disconnect from MQTT broker and clean up."""
        logger.info("Disconnecting from MQTT broker")
        self.client.loop_stop()
        self.client.disconnect()
