import sys
import os
import time
from collections import deque
from typing import Optional

# CRITICAL: Suppress FFmpeg logs BEFORE importing cv2
import suppress_ffmpeg_logs

import cv2
import logging

import config
from src.gesture_engine import GestureEngine
from src.mqtt_client import MQTTClient

# Additional suppression for OpenCV
os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp|fflags;nobuffer|flags;low_delay'
os.environ['OPENCV_LOG_LEVEL'] = 'FATAL'
os.environ['OPENCV_VIDEOIO_DEBUG'] = '0'

# Suppress Python warnings
import warnings
warnings.filterwarnings('ignore')

# Configure logging
# Set to DEBUG to see detailed gesture detection info
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
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
        Connect to RTSP stream with optimized settings.
        
        Returns:
            True if connection successful
        """
        try:
            logger.info(f"Connecting to RTSP stream: {self.rtsp_url}")
            
            # Build RTSP URL with optimized parameters
            # Use TCP transport for reliability, reduce latency
            if '?' not in self.rtsp_url:
                optimized_url = self.rtsp_url
            else:
                optimized_url = self.rtsp_url
            
            # Use CAP_FFMPEG backend with error suppression
            # Set CAP_PROP_LOGLEVEL to suppress FFmpeg warnings
            self.cap = cv2.VideoCapture(optimized_url, cv2.CAP_FFMPEG)
            
            if not self.cap.isOpened():
                logger.error("Failed to open RTSP stream")
                return False
            
            # Optimize capture settings for RTSP
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffer for low latency
            self.cap.set(cv2.CAP_PROP_FPS, config.TARGET_FPS)  # Hint target FPS
            
            # Suppress FFmpeg error logging
            # Note: This is OpenCV internal, may not work on all versions
            try:
                self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H264'))
            except:
                pass  # Ignore if not supported
            
            # Try to grab first frame to verify stream
            ret, _ = self.cap.read()
            if not ret:
                logger.warning("Stream opened but cannot read first frame, will retry")
                # Try one more time
                time.sleep(0.5)
                ret, _ = self.cap.read()
            
            logger.info("RTSP stream connected successfully")
            return True
        except Exception as e:
            logger.error(f"Error connecting to RTSP stream: {e}")
            return False
    
    def read_frame(self) -> Optional[cv2.Mat]:
        """
        Read and process a frame from the stream.
        Implements frame rate limiting and error tolerance.
        
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
            # Try to read frame, allow up to 3 retries for decode errors
            for attempt in range(3):
                ret, frame = self.cap.read()
                
                # Successful read with valid frame
                if ret and frame is not None and frame.size > 0:
                    self.last_frame_time = current_time
                    self.frame_count += 1
                    
                    # Resize frame for performance optimization
                    try:
                        frame = cv2.resize(frame, (config.FRAME_WIDTH, config.FRAME_HEIGHT))
                        return frame
                    except cv2.error as e:
                        logger.debug(f"Frame resize error: {e}")
                        continue
                
                # If failed, try again (skip corrupted frame)
                if attempt < 2:
                    continue
            
            # All retries failed
            if self.frame_count % 100 == 0:  # Log every 100 frames to reduce spam
                logger.warning("Failed to read frame from stream after retries")
            return None
            
        except Exception as e:
            if self.frame_count % 100 == 0:
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
    logger.info("="*60)
    logger.info("║ MediaPipe Gesture Control v1.0.2")
    logger.info("║ Build: 2025-11-30 17:05")
    logger.info("="*60)
    logger.info("Starting Gesture Recognition System")
    logger.info(f"RTSP URL: {config.RTSP_URL}")
    logger.info(f"MQTT Broker: {config.MQTT_BROKER}:{config.MQTT_PORT}")
    logger.info(f"Target FPS: {config.TARGET_FPS}")
    logger.info(f"Log Level: {LOG_LEVEL}")
    logger.info("="*60)
    
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
    
    logger.info("Entering main processing loop...")
    
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
            
            # Log first successful frame
            if video_processor.frame_count == 1:
                logger.info("✓ Successfully processing video frames!")
            
            # Process frame with gesture engine
            gesture, confidence = gesture_engine.process_frame(frame)
            
            # Log detection for debugging (every 50 frames to avoid spam)
            if video_processor.frame_count % 50 == 0 or video_processor.frame_count == 1:
                if gesture:
                    logger.info(f"[Frame {video_processor.frame_count}] Hand detected: {gesture} (confidence: {confidence:.2f})")
                else:
                    logger.info(f"[Frame {video_processor.frame_count}] No hand detected")
            
            # Add detection to buffer and check if should trigger
            triggered_gesture = gesture_buffer.add_detection(gesture, confidence)
            
            # If gesture should be triggered, publish to MQTT
            if triggered_gesture:
                logger.info(f"✓ Gesture TRIGGERED and published: {triggered_gesture} (confidence: {confidence:.2f})")
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
    try:
        # Force flush stdout/stderr
        import sys
        sys.stdout.flush()
        sys.stderr.flush()
        
        main()
    except Exception as e:
        logger.critical(f"FATAL ERROR: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
