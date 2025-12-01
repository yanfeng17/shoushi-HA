import os

# CRITICAL: Disable GPU BEFORE importing mediapipe
os.environ['MEDIAPIPE_DISABLE_GPU'] = '1'

import cv2
import mediapipe as mp
import numpy as np
from typing import Optional, Tuple
import config
import logging

logger = logging.getLogger(__name__)


class GestureEngine:
    """
    Encapsulates MediaPipe Hands model and gesture recognition logic.
    Identifies static gestures based on hand landmark geometry.
    
    v2.0.0: Simplified to 10 static gestures only
    """
    
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        # Force CPU mode by setting model_complexity to 0 (lightweight)
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=config.MAX_NUM_HANDS,
            model_complexity=0,  # Use lightweight model for CPU
            min_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE
        )
        
        # Gesture names (Chinese)
        self.GESTURES = {
            'OPEN_PALM': '张开手掌',
            'CLOSED_FIST': '握拳',
            'POINTING_UP': '食指向上',
            'OK_SIGN': 'OK手势',
            'THUMBS_UP': '点赞',
            'THUMBS_DOWN': '点踩',
            'PEACE': '剪刀手',
            'THREE_FINGERS': '三指',
            'FOUR_FINGERS': '四指',
            'PINCH': '捏合',
            'NONE': '无手势'
        }
        
        # Log enabled gestures
        enabled_list = [self.GESTURES[name] for name, enabled in config.ENABLED_GESTURES.items() if enabled]
        logger.info(f"启用的手势: {', '.join(enabled_list) if enabled_list else '无'}")
    
    def process_frame(self, frame: np.ndarray) -> Tuple[Optional[str], float]:
        """
        Process a single frame and detect hand gesture.
        
        Args:
            frame: BGR image from OpenCV
            
        Returns:
            Tuple of (gesture_name, confidence)
            gesture_name is None if no hand detected
        """
        try:
            # Convert BGR to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Ensure contiguous array for MediaPipe
            rgb_frame = np.ascontiguousarray(rgb_frame)
            
            # Process the frame
            results = self.hands.process(rgb_frame)
            
            if not results.multi_hand_landmarks:
                logger.debug("未检测到手部")
                return None, 0.0
            
            # Get the first hand landmarks
            hand_landmarks = results.multi_hand_landmarks[0]
            
            # Recognize gesture based on landmarks
            gesture, confidence = self._recognize_gesture(hand_landmarks)
            
            logger.debug(f"检测到手势: {gesture} (置信度: {confidence:.2f})")
            return gesture, confidence
            
        except Exception as e:
            logger.error(f"处理帧时出错: {e}")
            return None, 0.0
    
    def _recognize_gesture(self, landmarks) -> Tuple[str, float]:
        """
        Recognize gesture based on hand landmark positions (priority order).
        
        Landmark indices (MediaPipe Hands):
        - 0: WRIST
        - 1-4: THUMB (CMC, MCP, IP, TIP)
        - 5-8: INDEX_FINGER (MCP, PIP, DIP, TIP)
        - 9-12: MIDDLE_FINGER (MCP, PIP, DIP, TIP)
        - 13-16: RING_FINGER (MCP, PIP, DIP, TIP)
        - 17-20: PINKY (MCP, PIP, DIP, TIP)
        """
        lm = landmarks.landmark
        fingers_extended = self._get_fingers_extended(lm)
        
        # Priority 1: OK sign (special detection needed)
        if self._is_ok_sign(lm):
            return self._check_and_return('OK_SIGN', 0.85)
        
        # Priority 2: Pinch gesture
        if self._is_pinch(lm):
            return self._check_and_return('PINCH', 0.85)
        
        # Priority 3: Thumbs up/down (check thumb direction)
        if self._is_thumbs_up(lm):
            return self._check_and_return('THUMBS_UP', 0.9)
        
        if self._is_thumbs_down(lm):
            return self._check_and_return('THUMBS_DOWN', 0.9)
        
        # Priority 4: Specific finger combinations
        if self._is_peace(lm):
            return self._check_and_return('PEACE', 0.9)
        
        if self._is_three_fingers(lm):
            return self._check_and_return('THREE_FINGERS', 0.9)
        
        if self._is_four_fingers(lm):
            return self._check_and_return('FOUR_FINGERS', 0.9)
        
        # Priority 5: All fingers extended
        if all(fingers_extended):
            return self._check_and_return('OPEN_PALM', 0.95)
        
        # Priority 6: All fingers closed
        if not any(fingers_extended):
            return self._check_and_return('CLOSED_FIST', 0.95)
        
        # Priority 7: Only index finger extended
        if (fingers_extended[1] and not fingers_extended[2] and 
            not fingers_extended[3] and not fingers_extended[4]):
            return self._check_and_return('POINTING_UP', 0.9)
        
        return 'NONE', 0.5
    
    def _check_and_return(self, gesture: str, confidence: float) -> Tuple[str, float]:
        """Check if gesture is enabled in config."""
        if not config.ENABLED_GESTURES.get(gesture, False):
            logger.debug(f"手势 {gesture} 已检测但未启用")
            return 'NONE', 0.5
        return gesture, confidence
    
    def _is_thumbs_up(self, lm) -> bool:
        """
        Thumbs up: Thumb pointing up, other fingers closed.
        
        Detection:
        - Thumb extended with tip Y < mcp Y (pointing up)
        - Other four fingers closed
        """
        thumb_tip = lm[4]
        thumb_mcp = lm[2]
        wrist = lm[0]
        
        # Thumb pointing up (tip Y < mcp Y, Y increases downward)
        thumb_up = thumb_tip.y < thumb_mcp.y
        
        # Thumb must be extended
        thumb_extended = self._distance(thumb_tip, wrist) > self._distance(thumb_mcp, wrist)
        
        # Other fingers closed
        fingers = self._get_fingers_extended(lm)
        other_fingers_closed = not any(fingers[1:])  # index, middle, ring, pinky
        
        return thumb_up and thumb_extended and other_fingers_closed
    
    def _is_thumbs_down(self, lm) -> bool:
        """
        Thumbs down: Thumb pointing down, other fingers closed.
        
        Detection:
        - Thumb extended with tip Y > mcp Y (pointing down)
        - Other four fingers closed
        """
        thumb_tip = lm[4]
        thumb_mcp = lm[2]
        wrist = lm[0]
        
        # Thumb pointing down (tip Y > mcp Y)
        thumb_down = thumb_tip.y > thumb_mcp.y
        
        # Thumb must be extended
        thumb_extended = self._distance(thumb_tip, wrist) > self._distance(thumb_mcp, wrist)
        
        # Other fingers closed
        fingers = self._get_fingers_extended(lm)
        other_fingers_closed = not any(fingers[1:])
        
        return thumb_down and thumb_extended and other_fingers_closed
    
    def _is_peace(self, lm) -> bool:
        """
        Peace/Victory sign: Index and middle fingers extended, others closed.
        
        Detection:
        - Index and middle fingers extended
        - Ring and pinky closed (thumb can be either)
        """
        fingers = self._get_fingers_extended(lm)
        
        # Index and middle extended
        index_middle_extended = fingers[1] and fingers[2]
        
        # Ring and pinky closed (more lenient - thumb doesn't matter)
        ring_pinky_closed = not fingers[3] and not fingers[4]
        
        return index_middle_extended and ring_pinky_closed
    
    def _is_three_fingers(self, lm) -> bool:
        """
        Three fingers: Thumb, index, and middle fingers extended.
        
        Detection:
        - Thumb, index, middle extended
        - Ring and pinky closed
        """
        fingers = self._get_fingers_extended(lm)
        
        # First three fingers extended
        three_extended = fingers[0] and fingers[1] and fingers[2]
        
        # Ring and pinky closed
        others_closed = not fingers[3] and not fingers[4]
        
        return three_extended and others_closed
    
    def _is_four_fingers(self, lm) -> bool:
        """
        Four fingers: Index, middle, ring, and pinky extended, thumb closed.
        
        Detection:
        - Index, middle, ring, pinky extended
        - Thumb closed
        """
        fingers = self._get_fingers_extended(lm)
        
        # Four fingers extended (not including thumb)
        four_extended = (fingers[1] and fingers[2] and 
                        fingers[3] and fingers[4])
        
        # Thumb closed
        thumb_closed = not fingers[0]
        
        return four_extended and thumb_closed
    
    def _is_pinch(self, lm) -> bool:
        """
        Pinch gesture: Thumb and index fingertips close together, others closed.
        Similar to OK but other fingers are closed.
        
        Detection:
        - Thumb and index tips very close (< 0.05 distance)
        - Middle, ring, pinky closed
        """
        thumb_tip = lm[4]
        index_tip = lm[8]
        
        # Thumb and index tips close together
        distance = self._distance(thumb_tip, index_tip)
        
        fingers = self._get_fingers_extended(lm)
        
        # Middle, ring, pinky closed
        others_closed = not fingers[2] and not fingers[3] and not fingers[4]
        
        return distance < 0.05 and others_closed
    
    def _get_fingers_extended(self, landmarks) -> list:
        """
        Determine which fingers are extended.
        
        Returns:
            List of 5 booleans [thumb, index, middle, ring, pinky]
            True means finger is extended/straight
        """
        fingers = []
        
        # Thumb: Compare tip (4) with MCP joint (2) distance from wrist
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_mcp = landmarks[2]
        wrist = landmarks[0]
        
        # Calculate thumb extension based on distance from palm
        thumb_extended = self._distance(thumb_tip, wrist) > self._distance(thumb_mcp, wrist)
        fingers.append(thumb_extended)
        
        # For other fingers: Compare tip Y-coordinate with PIP joint
        # In MediaPipe, Y increases downward, so extended finger has smaller Y value
        finger_tips = [8, 12, 16, 20]      # Index, Middle, Ring, Pinky tips
        finger_pips = [6, 10, 14, 18]      # PIP joints
        finger_mcps = [5, 9, 13, 17]       # MCP joints (knuckles)
        
        for tip_idx, pip_idx, mcp_idx in zip(finger_tips, finger_pips, finger_mcps):
            tip = landmarks[tip_idx]
            pip = landmarks[pip_idx]
            mcp = landmarks[mcp_idx]
            
            # Finger is extended if:
            # 1. Tip is above PIP (smaller Y value)
            # 2. Distance from tip to MCP > distance from PIP to MCP
            tip_above_pip = tip.y < pip.y
            tip_far_from_mcp = self._distance(tip, mcp) > self._distance(pip, mcp) * 0.8
            
            fingers.append(tip_above_pip and tip_far_from_mcp)
        
        return fingers
    
    def _is_ok_sign(self, landmarks) -> bool:
        """
        Detect OK sign: thumb tip and index tip are close together,
        while other fingers are extended.
        """
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        
        # Check if thumb and index tips are close
        tips_distance = self._distance(thumb_tip, index_tip)
        
        # Get finger states
        fingers = self._get_fingers_extended(landmarks)
        
        # OK sign: thumb and index close, middle/ring/pinky extended
        if (tips_distance < 0.05 and  # Tips are touching
            fingers[2] and  # Middle extended
            fingers[3] and  # Ring extended
            fingers[4]):    # Pinky extended
            return True
        
        return False
    
    @staticmethod
    def _distance(point1, point2) -> float:
        """
        Calculate Euclidean distance between two landmarks.
        Uses 3D coordinates (x, y, z).
        """
        return np.sqrt(
            (point1.x - point2.x) ** 2 +
            (point1.y - point2.y) ** 2 +
            (point1.z - point2.z) ** 2
        )
    
    def release(self):
        """Clean up resources."""
        if self.hands:
            self.hands.close()
