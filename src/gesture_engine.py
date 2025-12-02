import os

# CRITICAL: Disable GPU BEFORE importing mediapipe
os.environ['MEDIAPIPE_DISABLE_GPU'] = '1'

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
from typing import Optional, Tuple
import config
import logging

logger = logging.getLogger(__name__)


class GestureEngine:
    """
    MediaPipe Gesture Recognizer wrapper.
    Uses Google's pre-trained model for 7 built-in gestures.
    
    v2.1.0: Switched from Hands to GestureRecognizer for higher accuracy.
    v2.1.2: Switched to IMAGE mode for low latency real-time recognition.
    """
    
    def __init__(self):
        # Gesture mapping: Google name -> Our name
        self.GESTURE_MAPPING = {
            'Closed_Fist': 'CLOSED_FIST',
            'Open_Palm': 'OPEN_PALM',
            'Pointing_Up': 'POINTING_UP',
            'Thumb_Down': 'THUMBS_DOWN',
            'Thumb_Up': 'THUMBS_UP',
            'Victory': 'PEACE',
            'ILoveYou': 'I_LOVE_YOU',
            'None': 'NONE',
            'Unknown': 'NONE'
        }
        
        # Chinese names
        self.GESTURES = {
            'CLOSED_FIST': '握拳',
            'OPEN_PALM': '张开手掌',
            'POINTING_UP': '食指向上',
            'THUMBS_DOWN': '点踩',
            'THUMBS_UP': '点赞',
            'PEACE': '剪刀手',
            'I_LOVE_YOU': '我爱你',
            'NONE': '无手势'
        }
        
        # Initialize GestureRecognizer
        model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'gesture_recognizer.task')
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"模型文件未找到: {model_path}\n"
                f"请从以下地址下载:\n"
                f"https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/latest/gesture_recognizer.task"
            )
        
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.GestureRecognizerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,  # IMAGE mode for low latency
            num_hands=config.MAX_NUM_HANDS,
            min_hand_detection_confidence=0.5,       # Google default
            min_hand_presence_confidence=0.5,        # Google default
            min_tracking_confidence=0.5              # Google default
        )
        self.recognizer = vision.GestureRecognizer.create_from_options(options)
        
        logger.info(f"MediaPipe Gesture Recognizer 已初始化")
        logger.info(f"运行模式: IMAGE (实时低延迟)")
        logger.info(f"检测阈值: 0.5 (Google 官方默认值)")
        
        # Log enabled gestures
        enabled_list = [self.GESTURES[name] for name, enabled in config.ENABLED_GESTURES.items() if enabled]
        logger.info(f"启用的手势: {', '.join(enabled_list) if enabled_list else '无'}")
    
    def process_frame(self, frame: np.ndarray) -> Tuple[Optional[str], float]:
        """
        Process a single frame and detect hand gesture (IMAGE mode).
        
        Args:
            frame: BGR image from OpenCV
            
        Returns:
            Tuple of (gesture_name, confidence)
            gesture_name is None if no hand detected
        """
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Ensure contiguous array for MediaPipe
            rgb_frame = np.ascontiguousarray(rgb_frame)
            
            # Create MediaPipe Image
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            
            # Recognize gesture (IMAGE mode - no timestamp needed)
            results = self.recognizer.recognize(mp_image)
            
            if not results.gestures or len(results.gestures) == 0:
                logger.debug("未检测到手部")
                return None, 0.0
            
            # Get the first hand's gesture
            gesture = results.gestures[0][0]
            google_name = gesture.category_name
            confidence = gesture.score
            
            # Map to our gesture name
            our_name = self.GESTURE_MAPPING.get(google_name, 'NONE')
            
            # Check if gesture is enabled
            if our_name != 'NONE' and not config.ENABLED_GESTURES.get(our_name, False):
                logger.debug(f"手势 {our_name} 已检测但未启用")
                return 'NONE', confidence
            
            logger.debug(f"检测到手势: {our_name} (Google: {google_name}, 置信度: {confidence:.2f})")
            return our_name, confidence
            
        except Exception as e:
            logger.error(f"处理帧时出错: {e}")
            return None, 0.0
    
    def release(self):
        """Clean up resources."""
        if self.recognizer:
            self.recognizer.close()
