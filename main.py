import cv2
import time
import logging
import sys
from collections import deque
from typing import Optional

import config
from src.gesture_engine import GestureEngine
from src.mqtt_client import MQTTClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GestureBuffer:
    """
    Implements state machine logic with debouncing and cooldown mechanism.
    A gesture is only triggered if it remains stable for a specified duration.
    """
    
    def __init__(
        self,
        stable_duration: float = config.GESTURE_STABLE_DURATION,
        cooldown: float = config.GESTURE_COOLDOWN,
        confidence_threshold: float = config.GESTURE_CONFIDENCE_THRESHOLD
    ):
        self.stable_duration = stable_duration
        self.cooldown = cooldown
        self.confidence_threshold = confidence_threshold
        
        # Buffer to store recent gesture detections
        self.gesture_history = deque(maxlen=50)  # Store timestamps and gestures
        
        # State tracking
        self.current_stable_gesture: Optional[str] = None
        self.last_triggered_gesture: Optional[str] = None
        self.last_trigger_time: float = 0
    
    def add_detection(self, gesture: Optional[str], confidence: float) -> Optional[str]:
        """
        Add a new gesture detection to the buffer.
        
        Args:
            gesture: Detected gesture name (or None if no hand)
            confidence: Detection confidence
            
        Returns:
            Gesture name if it should be triggered, None otherwise
        """
        current_time = time.time()
        
        # If no hand detected or low confidence, clear history
        if gesture is None or confidence < self.confidence_threshold:
            self.gesture_history.clear()
            self.current_stable_gesture = None
            return None
        
        # Add to history
        self.gesture_history.append({
            'gesture': gesture,
            'confidence': confidence,
            'timestamp': current_time
        })
        
        # Check if gesture has been stable for required duration
        if self._is_gesture_stable(gesture, current_time):
            # Check cooldown - don't trigger same gesture repeatedly
            if self._can_trigger(gesture, current_time):
                logger.info(f"Gesture triggered: {gesture} (confidence: {confidence:.2f})")
                self.last_triggered_gesture = gesture
                self.last_trigger_time = current_time
                return gesture
        
        return None
    
    def _is_gesture_stable(self, gesture: str, current_time: float) -> bool:
        """
        Check if a gesture has been consistently detected for the stable duration.
        """
        if len(self.gesture_history) < 2:
            return False
        
        # Get all detections within the stable duration window
        stable_window_start = current_time - self.stable_duration
        recent_detections = [
            d for d in self.gesture_history
            if d['timestamp'] >= stable_window_start
        ]
        
        if not recent_detections:
            return False
        
        # Check if all recent detections are the same gesture with high confidence
        all_same_gesture = all(
            d['gesture'] == gesture and d['confidence'] >= self.confidence_threshold
            for d in recent_detections
        )
        
        # Check if we have detections spanning the full duration
        time_span = current_time - recent_detections[0]['timestamp']
        has_sufficient_duration = time_span >= self.stable_duration
        
        if all_same_gesture and has_sufficient_duration:
            self.current_stable_gesture = gesture
            return True
        
        return False
    
    def _can_trigger(self, gesture: str, current_time: float) -> bool:
        """
        Check if a gesture can be triggered based on cooldown logic.
        
        Cooldown rules:
        - Same gesture can't be triggered again within cooldown period
        - Different gesture can be triggered immediately
        """
        # Different gesture - allow immediate trigger
        if gesture != self.last_triggered_gesture:
            return True
        
        # Same gesture - check cooldown
        time_since_last_trigger = current_time - self.last_trigger_time
        return time_since_last_trigger >= self.cooldown
    
    def reset(self):
        """Reset all state."""
        self.gesture_history.clear()
        self.current_stable_gesture = None


class VideoStreamProcessor:
    """
    Handles RTSP stream capture with automatic reconnection.
    """
    
    def __init__(self, rtsp_url: str):
        self.rtsp_url = rtsp_url
        self.cap: Optional[cv2.VideoCapture] = None
        self.frame_count = 0
        self.last_frame_time = 0
        self.target_frame_interval = 1.0 / config.TARGET_FPS
    
    def connect(self) -> bool:
        """
        Connect to RTSP stream.
        
        Returns:
            True if connection successful
        """
        try:
            logger.info(f"Connecting to RTSP stream: {self.rtsp_url}")
            self.cap = cv2.VideoCapture(self.rtsp_url)
            
            if not self.cap.isOpened():
                logger.error("Failed to open RTSP stream")
                return False
            
            # Set buffer size to reduce latency
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            logger.info("RTSP stream connected successfully")
            return True
        except Exception as e:
            logger.error(f"Error connecting to RTSP stream: {e}")
            return False
    
    def read_frame(self) -> Optional[cv2.Mat]:
        """
        Read and process a frame from the stream.
        Implements frame rate limiting.
        
        Returns:
            Processed frame or None if failed
        """
        if self.cap is None or not self.cap.isOpened():
            return None
        
        # Frame rate limiting
        current_time = time.time()
        if current_time - self.last_frame_time < self.target_frame_interval:
            return None
        
        try:
            ret, frame = self.cap.read()
            
            if not ret or frame is None:
                logger.warning("Failed to read frame from stream")
                return None
            
            self.last_frame_time = current_time
            self.frame_count += 1
            
            # Resize frame for performance optimization
            frame = cv2.resize(frame, (config.FRAME_WIDTH, config.FRAME_HEIGHT))
            
            return frame
        except Exception as e:
            logger.error(f"Error reading frame: {e}")
            return None
    
    def release(self):
        """Release video capture resources."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            logger.info("Video stream released")


def main():
    """Main application loop."""
    logger.info("Starting Gesture Recognition System")
    logger.info(f"RTSP URL: {config.RTSP_URL}")
    logger.info(f"MQTT Broker: {config.MQTT_BROKER}:{config.MQTT_PORT}")
    logger.info(f"Target FPS: {config.TARGET_FPS}")
    
    # Initialize components
    gesture_engine = GestureEngine()
    mqtt_client = MQTTClient()
    gesture_buffer = GestureBuffer()
    video_processor = VideoStreamProcessor(config.RTSP_URL)
    
    # Connect to MQTT broker
    if not mqtt_client.connect():
        logger.error("Failed to connect to MQTT broker. Retrying in 5 seconds...")
        time.sleep(5)
        if not mqtt_client.connect():
            logger.error("Unable to connect to MQTT broker. Exiting.")
            return
    
    # Main loop with automatic reconnection
    consecutive_failures = 0
    max_consecutive_failures = 10
    
    try:
        while True:
            # Connect/reconnect to video stream
            if video_processor.cap is None or not video_processor.cap.isOpened():
                if not video_processor.connect():
                    logger.error(f"Failed to connect to video stream. Retrying in {config.RTSP_RECONNECT_DELAY} seconds...")
                    time.sleep(config.RTSP_RECONNECT_DELAY)
                    continue
                
                # Reset failure counter on successful connection
                consecutive_failures = 0
            
            # Read frame
            frame = video_processor.read_frame()
            
            if frame is None:
                consecutive_failures += 1
                
                if consecutive_failures >= max_consecutive_failures:
                    logger.error(f"Too many consecutive failures ({consecutive_failures}). Reconnecting...")
                    video_processor.release()
                    consecutive_failures = 0
                
                time.sleep(0.1)
                continue
            
            # Reset failure counter on successful read
            consecutive_failures = 0
            
            # Process frame with gesture engine
            gesture, confidence = gesture_engine.process_frame(frame)
            
            # Add detection to buffer and check if should trigger
            triggered_gesture = gesture_buffer.add_detection(gesture, confidence)
            
            # If gesture should be triggered, publish to MQTT
            if triggered_gesture:
                mqtt_client.publish_gesture(triggered_gesture, confidence)
            
            # Small sleep to prevent CPU overload
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
    finally:
        # Cleanup
        logger.info("Cleaning up resources...")
        video_processor.release()
        gesture_engine.release()
        mqtt_client.disconnect()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    main()
