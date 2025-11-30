import cv2
import mediapipe as mp
import numpy as np
from typing import Optional, Tuple
import config


class GestureEngine:
    """
    Encapsulates MediaPipe Hands model and gesture recognition logic.
    Identifies gestures based on hand landmark geometry.
    """
    
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=config.MAX_NUM_HANDS,
            min_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE
        )
        
        # Gesture names
        self.GESTURES = {
            'OPEN_PALM': 'Open Palm',
            'CLOSED_FIST': 'Closed Fist',
            'POINTING_UP': 'Pointing Up',
            'OK_SIGN': 'OK Sign',
            'NONE': 'None'
        }
    
    def process_frame(self, frame: np.ndarray) -> Tuple[Optional[str], float]:
        """
        Process a single frame and detect hand gesture.
        
        Args:
            frame: BGR image from OpenCV
            
        Returns:
            Tuple of (gesture_name, confidence)
            gesture_name is None if no hand detected
        """
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the frame
        results = self.hands.process(rgb_frame)
        
        if not results.multi_hand_landmarks:
            return None, 0.0
        
        # Get the first hand landmarks
        hand_landmarks = results.multi_hand_landmarks[0]
        
        # Recognize gesture based on landmarks
        gesture, confidence = self._recognize_gesture(hand_landmarks)
        
        return gesture, confidence
    
    def _recognize_gesture(self, landmarks) -> Tuple[str, float]:
        """
        Recognize gesture based on hand landmark positions.
        
        Landmark indices (MediaPipe Hands):
        - 0: WRIST
        - 1-4: THUMB (CMC, MCP, IP, TIP)
        - 5-8: INDEX_FINGER (MCP, PIP, DIP, TIP)
        - 9-12: MIDDLE_FINGER (MCP, PIP, DIP, TIP)
        - 13-16: RING_FINGER (MCP, PIP, DIP, TIP)
        - 17-20: PINKY (MCP, PIP, DIP, TIP)
        """
        lm = landmarks.landmark
        
        # Check if all fingers are extended (OPEN_PALM)
        fingers_extended = self._get_fingers_extended(lm)
        
        if all(fingers_extended):
            return 'OPEN_PALM', 0.95
        
        # Check if all fingers are closed (CLOSED_FIST)
        if not any(fingers_extended):
            return 'CLOSED_FIST', 0.95
        
        # Check if only index finger is extended (POINTING_UP)
        if (fingers_extended[1] and  # Index extended
            not fingers_extended[2] and  # Middle closed
            not fingers_extended[3] and  # Ring closed
            not fingers_extended[4]):    # Pinky closed
            return 'POINTING_UP', 0.9
        
        # Check for OK sign (thumb and index tips touching, other fingers extended)
        if self._is_ok_sign(lm):
            return 'OK_SIGN', 0.85
        
        return 'NONE', 0.5
    
    def _get_fingers_extended(self, landmarks) -> list:
        """
        Determine which fingers are extended.
        
        Returns:
            List of 5 booleans [thumb, index, middle, ring, pinky]
            True means finger is extended/straight
        """
        fingers = []
        
        # Thumb: Compare tip (4) with IP joint (3) in x-axis (for side view)
        # If thumb tip is significantly away from palm center, it's extended
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
        if (tips_distance < 0.05 and  # Tips are touching (threshold tuned experimentally)
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
