import cv2
import numpy as np
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class DebugVisualizer:
    """
    Debug visualization tool for displaying detection results on video frames.
    Shows hand gestures, facial expressions, blendshapes, and FPS.
    """
    
    def __init__(self):
        """Initialize the visualizer."""
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.5
        self.font_thickness = 1
        self.line_height = 20
        
        # Colors (BGR format)
        self.color_white = (255, 255, 255)
        self.color_green = (0, 255, 0)
        self.color_blue = (255, 0, 0)
        self.color_yellow = (0, 255, 255)
        self.color_red = (0, 0, 255)
        self.color_bg = (0, 0, 0)
        
        logger.info("Debug Visualizer initialized")
    
    def draw_debug_overlay(
        self,
        frame: np.ndarray,
        fps: float,
        frame_count: int,
        gesture: Optional[str] = None,
        gesture_confidence: float = 0.0,
        expression: Optional[str] = None,
        expression_confidence: float = 0.0,
        blendshapes: Optional[Dict[str, float]] = None,
        buffer_size: int = 0
    ) -> np.ndarray:
        """
        Draw debug information overlay on frame.
        
        Args:
            frame: Input BGR frame
            fps: Current FPS
            frame_count: Total frame count
            gesture: Detected hand gesture name
            gesture_confidence: Gesture confidence (0-1)
            expression: Detected facial expression name
            expression_confidence: Expression confidence (0-1)
            blendshapes: Dictionary of blendshape values
            buffer_size: Current buffer size
            
        Returns:
            Frame with debug overlay
        """
        # Make a copy to avoid modifying original
        debug_frame = frame.copy()
        
        # Draw semi-transparent background for text
        overlay = debug_frame.copy()
        cv2.rectangle(overlay, (5, 5), (400, 300), self.color_bg, -1)
        cv2.addWeighted(overlay, 0.6, debug_frame, 0.4, 0, debug_frame)
        
        y = 25
        
        # Title
        self._draw_text(debug_frame, "MediaPipe Gesture Control v1.0.7", (10, y), 
                       self.color_yellow, scale=0.6, thickness=2)
        y += self.line_height + 5
        
        # FPS and Frame count
        self._draw_text(debug_frame, f"FPS: {fps:.1f}  |  Frame: {frame_count}", 
                       (10, y), self.color_white)
        y += self.line_height + 10
        
        # Separator
        cv2.line(debug_frame, (10, y-5), (390, y-5), self.color_white, 1)
        y += 10
        
        # Hand gesture
        if gesture:
            emoji = self._get_gesture_emoji(gesture)
            text = f"{emoji} Hand: {gesture}"
            color = self.color_green if gesture_confidence > 0.7 else self.color_yellow
            self._draw_text(debug_frame, text, (10, y), color)
            y += self.line_height
            self._draw_confidence_bar(debug_frame, gesture_confidence, (10, y), 200)
            y += 15
        else:
            self._draw_text(debug_frame, "Hand: None", (10, y), self.color_white)
            y += self.line_height + 5
        
        # Facial expression
        if expression:
            emoji = self._get_expression_emoji(expression)
            text = f"{emoji} Face: {expression}"
            color = self.color_green if expression_confidence > 0.7 else self.color_yellow
            self._draw_text(debug_frame, text, (10, y), color)
            y += self.line_height
            self._draw_confidence_bar(debug_frame, expression_confidence, (10, y), 200)
            y += 15
        else:
            self._draw_text(debug_frame, "Face: None", (10, y), self.color_white)
            y += self.line_height + 5
        
        # Buffer info
        if buffer_size > 0:
            self._draw_text(debug_frame, f"Buffer: {buffer_size}", (10, y), self.color_blue)
            y += self.line_height + 5
        
        # Separator
        cv2.line(debug_frame, (10, y), (390, y), self.color_white, 1)
        y += 15
        
        # Blendshapes
        if blendshapes:
            self._draw_text(debug_frame, "Blendshapes (>0.05):", (10, y), self.color_white)
            y += self.line_height
            
            # Sort by value and show top ones
            sorted_bs = sorted(
                [(k, v) for k, v in blendshapes.items() if v > 0.05],
                key=lambda x: x[1],
                reverse=True
            )
            
            # Show top 5 blendshapes
            for i, (name, value) in enumerate(sorted_bs[:5]):
                # Shorten name for display
                display_name = self._shorten_blendshape_name(name)
                self._draw_text(debug_frame, f"  {display_name}:", (10, y), self.color_blue)
                
                # Draw value bar
                self._draw_blendshape_bar(debug_frame, value, (120, y-5), 150)
                
                # Draw value
                self._draw_text(debug_frame, f"{value:.2f}", (280, y), self.color_white, scale=0.4)
                y += self.line_height
        
        return debug_frame
    
    def draw_landmarks(
        self,
        frame: np.ndarray,
        hand_landmarks=None,
        face_landmarks=None
    ) -> np.ndarray:
        """
        Draw hand and face landmarks on frame.
        
        Args:
            frame: Input BGR frame
            hand_landmarks: MediaPipe hand landmarks
            face_landmarks: MediaPipe face landmarks
            
        Returns:
            Frame with landmarks drawn
        """
        debug_frame = frame.copy()
        
        # Draw hand landmarks
        if hand_landmarks:
            for landmark in hand_landmarks.landmark:
                x = int(landmark.x * frame.shape[1])
                y = int(landmark.y * frame.shape[0])
                cv2.circle(debug_frame, (x, y), 3, self.color_green, -1)
        
        # Draw face landmarks
        if face_landmarks:
            for landmark in face_landmarks.landmark:
                x = int(landmark.x * frame.shape[1])
                y = int(landmark.y * frame.shape[0])
                cv2.circle(debug_frame, (x, y), 1, self.color_blue, -1)
        
        return debug_frame
    
    def _draw_text(self, frame, text, pos, color, scale=None, thickness=None):
        """Draw text with background for better visibility."""
        scale = scale or self.font_scale
        thickness = thickness or self.font_thickness
        
        cv2.putText(frame, text, pos, self.font, scale, color, thickness, cv2.LINE_AA)
    
    def _draw_confidence_bar(self, frame, confidence, pos, width):
        """Draw a confidence bar."""
        x, y = pos
        bar_height = 8
        
        # Background bar
        cv2.rectangle(frame, (x, y), (x + width, y + bar_height), (50, 50, 50), -1)
        
        # Filled bar
        fill_width = int(width * confidence)
        if confidence > 0.7:
            color = self.color_green
        elif confidence > 0.5:
            color = self.color_yellow
        else:
            color = self.color_red
        
        cv2.rectangle(frame, (x, y), (x + fill_width, y + bar_height), color, -1)
        
        # Border
        cv2.rectangle(frame, (x, y), (x + width, y + bar_height), self.color_white, 1)
    
    def _draw_blendshape_bar(self, frame, value, pos, width):
        """Draw a blendshape value bar."""
        x, y = pos
        bar_height = 12
        
        # Background bar
        cv2.rectangle(frame, (x, y), (x + width, y + bar_height), (30, 30, 30), -1)
        
        # Filled bar
        fill_width = int(width * value)
        # Color gradient: blue to green
        color = (255, int(255 * value), 0)
        cv2.rectangle(frame, (x, y), (x + fill_width, y + bar_height), color, -1)
        
        # Border
        cv2.rectangle(frame, (x, y), (x + width, y + bar_height), self.color_white, 1)
    
    def _get_gesture_emoji(self, gesture: str) -> str:
        """Get emoji representation for gesture."""
        emoji_map = {
            'OPEN_PALM': '🖐️',
            'CLOSED_FIST': '✊',
            'POINTING_UP': '☝️',
            'OK_SIGN': '👌',
            'PEACE_SIGN': '✌️',
            'THUMBS_UP': '👍',
            'ROCK_SIGN': '🤟',
        }
        return emoji_map.get(gesture, '👋')
    
    def _get_expression_emoji(self, expression: str) -> str:
        """Get emoji representation for expression."""
        emoji_map = {
            'MOUTH_OPEN': '😮',
            'MOUTH_WIDE_OPEN': '😲',
            'SMILE': '😄',
            'GENUINE_SMILE': '😊',
            'FROWN': '😔',
            'YAWNING': '🥱',
            'PUCKER': '😑',
            'WINK_LEFT': '😉',
            'WINK_RIGHT': '😉',
            'BLINK_BOTH': '😌',
            'SURPRISED': '😲',
            'NEUTRAL': '😐',
        }
        return emoji_map.get(expression, '😐')
    
    def _shorten_blendshape_name(self, name: str) -> str:
        """Shorten blendshape name for display."""
        # Remove common prefixes
        name = name.replace('mouth', 'm')
        name = name.replace('eye', 'e')
        name = name.replace('brow', 'b')
        name = name.replace('jaw', 'j')
        name = name.replace('Left', 'L')
        name = name.replace('Right', 'R')
        name = name.replace('Upper', 'U')
        name = name.replace('Lower', 'Lo')
        
        # Capitalize first letter
        if len(name) > 0:
            name = name[0].upper() + name[1:]
        
        return name[:12]  # Max 12 chars
