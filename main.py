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
from src.motion_detector import MotionDetector
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

# Import expression detection and visualization (optional based on config)
# Import after logger is defined
if config.ENABLE_EXPRESSION:
    try:
        from src.expression_engine import ExpressionEngine
        logger.info("Expression detection enabled")
    except ImportError as e:
        logger.warning(f"Failed to import ExpressionEngine: {e}. Expression detection disabled.")
        config.ENABLE_EXPRESSION = False

if config.DEBUG_VISUALIZATION:
    try:
        from src.visualization import DebugVisualizer
        logger.info("Debug visualization enabled")
    except ImportError as e:
        logger.warning(f"Failed to import DebugVisualizer: {e}. Visualization disabled.")
        config.DEBUG_VISUALIZATION = False


class GestureBuffer:
    """
    Implements state machine logic with debouncing and cooldown mechanism.
    A gesture is only triggered if it remains stable for a specified duration.
    """
    
    def __init__(
        self,
        min_detections: int = config.GESTURE_MIN_DETECTIONS,
        cooldown: float = config.GESTURE_COOLDOWN,
        confidence_threshold: float = config.GESTURE_CONFIDENCE_THRESHOLD
    ):
        self.min_detections = min_detections
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
                logger.info(f"✓ Gesture TRIGGERED: {gesture} (confidence: {confidence:.2f})")
                self.last_triggered_gesture = gesture
                self.last_trigger_time = current_time
                return gesture
            else:
                logger.debug(f"Gesture {gesture} is stable but in cooldown")
        else:
            # Log why not stable (but only occasionally to avoid spam)
            if len(self.gesture_history) % 10 == 0:
                logger.debug(f"Gesture {gesture} detected but not yet stable (history: {len(self.gesture_history)} detections)")
        
        return None
    
    def _is_gesture_stable(self, gesture: str, current_time: float) -> bool:
        """
        Check if a gesture has been consistently detected.
        Uses count-based approach for stability detection.
        
        Args:
            gesture: The gesture to check
            current_time: Current timestamp
            
        Returns:
            True if gesture has been detected consistently for min_detections frames
        """
        if len(self.gesture_history) < self.min_detections:
            return False
        
        # Check last N detections - are they all the same gesture?
        recent_detections = list(self.gesture_history)[-self.min_detections:]
        
        all_same_gesture = all(
            d['gesture'] == gesture and d['confidence'] >= self.confidence_threshold
            for d in recent_detections
        )
        
        if not all_same_gesture:
            return False
        
        # Calculate time span for logging
        time_span = recent_detections[-1]['timestamp'] - recent_detections[0]['timestamp']
        
        # Debug logging (only occasionally to reduce spam)
        if len(self.gesture_history) % 10 == 0:
            logger.info(f"Stability check for {gesture}: "
                       f"last_{self.min_detections}={all_same_gesture}, "
                       f"time_span={time_span:.2f}s, "
                       f"buffer_size={len(self.gesture_history)}")
        
        if all_same_gesture:
            self.current_stable_gesture = gesture
            logger.info(f"✓ Gesture {gesture} is STABLE (last {self.min_detections} detections consistent)")
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
        self.processed_frame_count = 0
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
        
        # Minimal frame rate limiting (removed strict timing to reduce latency)
        current_time = time.time()
        
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
    logger.info("║ MediaPipe Gesture Control v1.0.10")
    logger.info("║ Build: 2025-11-30 - EXPRESSION DETECTION")
    logger.info("="*60)
    logger.info("Starting Gesture Recognition System")
    logger.info(f"RTSP URL: {config.RTSP_URL}")
    logger.info(f"MQTT Broker: {config.MQTT_BROKER}:{config.MQTT_PORT}")
    logger.info(f"Target FPS: {config.TARGET_FPS}")
    logger.info(f"Expression Detection: {config.ENABLE_EXPRESSION}")
    logger.info(f"Debug Visualization: {config.DEBUG_VISUALIZATION}")
    logger.info(f"Log Level: {LOG_LEVEL}")
    logger.info("="*60)
    
    # Initialize components
    gesture_engine = GestureEngine()
    motion_detector = MotionDetector()  # 动态手势检测器
    mqtt_client = MQTTClient()
    gesture_buffer = GestureBuffer()
    video_processor = VideoStreamProcessor(config.RTSP_URL)
    
    # Initialize expression engine (optional)
    expression_engine = None
    expression_buffer = None
    if config.ENABLE_EXPRESSION:
        try:
            expression_engine = ExpressionEngine()
            expression_buffer = GestureBuffer(
                min_detections=config.EXPRESSION_MIN_DETECTIONS,
                confidence_threshold=config.EXPRESSION_CONFIDENCE_THRESHOLD
            )
            logger.info("Expression engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize expression engine: {e}")
            expression_engine = None
    
    # Initialize debug visualizer (optional)
    visualizer = None
    if config.DEBUG_VISUALIZATION:
        try:
            visualizer = DebugVisualizer()
            logger.info("Debug visualizer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize visualizer: {e}")
            visualizer = None
    
    # FPS tracking
    fps_start_time = time.time()
    fps_frame_count = 0
    current_fps = 0.0
    
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
            
            # Calculate FPS
            fps_frame_count += 1
            if time.time() - fps_start_time >= 1.0:
                current_fps = fps_frame_count / (time.time() - fps_start_time)
                fps_start_time = time.time()
                fps_frame_count = 0
            
            # 1. Process static gesture recognition
            gesture, gesture_confidence = gesture_engine.process_frame(frame)
            
            # 2. Process dynamic gesture (motion detection)
            motion_gesture = None
            motion_confidence = 0.0
            
            if gesture:  # Hand detected
                # Get hand landmarks for motion tracking
                hand_landmarks = gesture_engine.get_hand_landmarks()
                if hand_landmarks:
                    # Add wrist position to motion detector
                    wrist = hand_landmarks.landmark[0]
                    motion_detector.add_hand_position(wrist, time.time())
                    
                    # Detect motion gestures
                    motion_gesture, motion_confidence = motion_detector.detect_motion()
            else:
                # No hand detected, reset motion detector
                motion_detector.reset()
            
            # 3. Determine final gesture (priority: motion > static)
            final_gesture = None
            final_confidence = 0.0
            gesture_type = "static"
            
            if motion_gesture:
                # Motion gesture has priority
                final_gesture = motion_gesture
                final_confidence = motion_confidence
                gesture_type = "motion"
            elif gesture and gesture != 'NONE':
                # Use static gesture if no motion detected
                final_gesture = gesture
                final_confidence = gesture_confidence
                gesture_type = "static"
            
            # 4. Check gesture buffer and trigger if stable
            if final_gesture:
                triggered_gesture = gesture_buffer.add_detection(final_gesture, final_confidence)
                if triggered_gesture:
                    # Publish to gesture sensor
                    mqtt_client.publish_gesture(triggered_gesture, final_confidence, gesture_type)
                    logger.info(f"✓ GESTURE TRIGGERED: {triggered_gesture} ({gesture_type}, confidence: {final_confidence:.2f})")
            else:
                gesture_buffer.add_detection(None, 0.0)
            
            # 5. Process expression (independent from gestures)
            expression = None
            expression_confidence = 0.0
            blendshapes = {}
            if expression_engine:
                try:
                    expression, expression_confidence, blendshapes = expression_engine.process_frame(frame)
                except Exception as e:
                    logger.error(f"Error in expression detection: {e}")
            
            # 6. Check expression buffer and trigger if stable (separate from gesture)
            if expression_buffer and expression:
                triggered_expression = expression_buffer.add_detection(expression, expression_confidence)
                if triggered_expression and triggered_expression != 'NEUTRAL':
                    # Publish to expression sensor (separate from gesture)
                    mqtt_client.publish_expression(
                        expression=triggered_expression,
                        confidence=expression_confidence,
                        blendshapes=blendshapes if config.PUBLISH_DETAILED_BLENDSHAPES else None
                    )
                    logger.info(f"✓ EXPRESSION TRIGGERED: {triggered_expression} (confidence: {expression_confidence:.2f})")
            elif expression_buffer:
                expression_buffer.add_detection(None, 0.0)
            
            # 7. Debug visualization (if enabled)
            if visualizer:
                try:
                    # Display both static and motion gestures
                    display_gesture = motion_gesture if motion_gesture else gesture
                    display_confidence = motion_confidence if motion_gesture else gesture_confidence
                    
                    frame = visualizer.draw_debug_overlay(
                        frame=frame,
                        fps=current_fps,
                        frame_count=video_processor.frame_count,
                        gesture=display_gesture,
                        gesture_confidence=display_confidence,
                        expression=expression,
                        expression_confidence=expression_confidence,
                        blendshapes=blendshapes,
                        buffer_size=len(gesture_buffer.gesture_history)
                    )
                except Exception as e:
                    logger.error(f"Error in visualization: {e}")
            
            # 8. Log detection for debugging (every 20 processed frames)
            if video_processor.processed_frame_count % 20 == 0 or video_processor.processed_frame_count == 1:
                parts = [f"[Processed {video_processor.processed_frame_count}]"]
                if final_gesture:
                    parts.append(f"Gesture: {final_gesture} ({gesture_type}, {final_confidence:.2f})")
                if expression:
                    parts.append(f"Expression: {expression} ({expression_confidence:.2f})")
                if parts:
                    logger.info(" | ".join(parts))
            
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
        if expression_engine:
            expression_engine.release()
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
