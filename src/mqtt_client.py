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
        Send Home Assistant MQTT Discovery configuration.
        Creates a sensor entity that displays the current gesture.
        """
        if self.discovery_sent:
            return
        
        # Discovery topic follows pattern: <discovery_prefix>/sensor/<device_name>/config
        discovery_topic = f"{config.MQTT_DISCOVERY_PREFIX}/sensor/{config.MQTT_DEVICE_NAME}/config"
        
        # Discovery payload
        discovery_payload = {
            "name": "Gesture Control",
            "unique_id": f"{config.MQTT_DEVICE_NAME}_sensor",
            "state_topic": config.MQTT_STATE_TOPIC,
            "value_template": "{{ value_json.state }}",
            "json_attributes_topic": config.MQTT_STATE_TOPIC,
            "icon": "mdi:hand-back-right",
            "device": {
                "identifiers": [config.MQTT_DEVICE_NAME],
                "name": "MediaPipe Gesture & Expression Recognition",
                "model": "Hand Gesture & Face Expression Detector",
                "manufacturer": "Custom",
                "sw_version": "1.0.7"
            }
        }
        
        # Publish discovery config with retain flag
        result = self.client.publish(
            discovery_topic,
            json.dumps(discovery_payload),
            qos=1,
            retain=True
        )
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"Home Assistant discovery config sent to {discovery_topic}")
            self.discovery_sent = True
        else:
            logger.error(f"Failed to send discovery config: {result.rc}")
    
    def publish_state(self, state: str, confidence: float, state_type: str = "gesture", blendshapes: dict = None):
        """
        Publish state (gesture or expression) to MQTT.
        
        Args:
            state: State name (e.g., "CLOSED_FIST", "SMILE")
            confidence: Detection confidence (0.0 to 1.0)
            state_type: Type of state ("gesture" or "expression")
            blendshapes: Optional dictionary of blendshape values (for expressions)
        """
        if not self.connected:
            logger.warning("Not connected to MQTT broker, skipping publish")
            return
        
        payload = {
            "state": state,
            "confidence": round(confidence, 3),
            "type": state_type,
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
            config.MQTT_STATE_TOPIC,
            json.dumps(payload),
            qos=1,
            retain=False
        )
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.debug(f"Published {state_type}: {state} (confidence: {confidence:.2f})")
        else:
            logger.error(f"Failed to publish {state_type}: {result.rc}")
    
    def publish_gesture(self, gesture: str, confidence: float):
        """
        Backward compatibility method for publishing gestures.
        
        Args:
            gesture: Gesture name (e.g., "CLOSED_FIST")
            confidence: Detection confidence (0.0 to 1.0)
        """
        self.publish_state(gesture, confidence, state_type="gesture")
    
    def disconnect(self):
        """Disconnect from MQTT broker and clean up."""
        logger.info("Disconnecting from MQTT broker")
        self.client.loop_stop()
        self.client.disconnect()
