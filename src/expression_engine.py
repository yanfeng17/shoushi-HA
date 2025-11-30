import os
import logging
import numpy as np
from typing import Optional, Tuple, Dict
import config

logger = logging.getLogger(__name__)

# MediaPipe Face Landmarker imports
try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
except ImportError as e:
    logger.error(f"Failed to import MediaPipe: {e}")
    raise


class ExpressionEngine:
    """
    Expression recognition engine using MediaPipe Face Landmarker.
    Detects facial expressions based on blendshapes (52 coefficients).
    """
    
    def __init__(self):
        """Initialize the Face Landmarker with blendshapes support."""
        logger.info("Initializing Expression Engine...")
        
        # Model path
        self.model_path = os.path.join('/app', 'models', 'face_landmarker.task')
        
        if not os.path.exists(self.model_path):
            logger.error(f"Face Landmarker model not found at {self.model_path}")
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        
        # Create FaceLandmarker options
        base_options = python.BaseOptions(model_asset_path=self.model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=True,  # Enable blendshapes
            output_facial_transformation_matrixes=False,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Create detector
        self.detector = vision.FaceLandmarker.create_from_options(options)
        
        # Expression thresholds
        self.thresholds = {
            'mouth_open': config.MOUTH_OPEN_THRESHOLD,
            'jaw_open': config.JAW_OPEN_THRESHOLD,
            'smile': config.SMILE_THRESHOLD,
            'frown': config.FROWN_THRESHOLD,
            'blink': config.BLINK_THRESHOLD,
            'pucker': config.PUCKER_THRESHOLD
        }
        
        logger.info("Expression Engine initialized successfully")
        logger.info(f"Expression thresholds: {self.thresholds}")
    
    def process_frame(self, frame: np.ndarray) -> Tuple[Optional[str], float, Dict[str, float]]:
        """
        Process a frame and detect facial expression.
        
        Args:
            frame: BGR image from OpenCV
            
        Returns:
            Tuple of (expression_name, confidence, blendshapes_dict)
            - expression_name is None if no face detected
            - confidence is the expression confidence (0-1)
            - blendshapes_dict contains all 52 blendshape coefficients
        """
        try:
            # Convert BGR to RGB
            rgb_frame = frame[:, :, ::-1]
            
            # Create MediaPipe Image
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            
            # Detect face landmarks and blendshapes
            detection_result = self.detector.detect(mp_image)
            
            # Check if face detected
            if not detection_result.face_blendshapes or len(detection_result.face_blendshapes) == 0:
                logger.debug("No face detected in frame")
                return None, 0.0, {}
            
            # Get first face's blendshapes
            blendshapes_list = detection_result.face_blendshapes[0]
            
            # Convert to dictionary
            blendshapes_dict = {
                bs.category_name: bs.score 
                for bs in blendshapes_list
            }
            
            # Recognize expression
            expression, confidence = self._recognize_expression(blendshapes_dict)
            
            logger.debug(f"Detected expression: {expression} (confidence: {confidence:.2f})")
            return expression, confidence, blendshapes_dict
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}", exc_info=True)
            return None, 0.0, {}
    
    def _recognize_expression(self, bs: Dict[str, float]) -> Tuple[str, float]:
        """
        Recognize expression based on blendshapes.
        
        Args:
            bs: Dictionary of blendshape names to scores (0-1)
            
        Returns:
            Tuple of (expression_name, confidence)
        """
        # Get relevant blendshape values with safe defaults
        mouth_open = bs.get('mouthOpen', 0)
        jaw_open = bs.get('jawOpen', 0)
        mouth_smile = bs.get('mouthSmile', 0)
        mouth_frown = bs.get('mouthFrown', 0)
        mouth_pucker = bs.get('mouthPucker', 0)
        mouth_funnel = bs.get('mouthFunnel', 0)
        eye_blink_left = bs.get('eyeBlinkLeft', 0)
        eye_blink_right = bs.get('eyeBlinkRight', 0)
        eye_squint_left = bs.get('eyeSquintLeft', 0)
        eye_squint_right = bs.get('eyeSquintRight', 0)
        eye_wide_left = bs.get('eyeWideLeft', 0)
        eye_wide_right = bs.get('eyeWideRight', 0)
        brow_inner_up = bs.get('browInnerUp', 0)
        
        # Priority order: Check more specific expressions first
        
        # SURPRISED: Wide open mouth + wide eyes + raised eyebrows
        if (jaw_open > self.thresholds['jaw_open'] and 
            eye_wide_left > 0.5 and eye_wide_right > 0.5 and
            brow_inner_up > 0.4):
            confidence = (jaw_open + eye_wide_left + eye_wide_right + brow_inner_up) / 4
            return 'SURPRISED', confidence
        
        # YAWNING: Wide open jaw with mouth funnel shape
        if (jaw_open > self.thresholds['jaw_open'] and 
            mouth_funnel > 0.3):
            confidence = (jaw_open + mouth_funnel) / 2
            return 'YAWNING', confidence
        
        # MOUTH_WIDE_OPEN: Just wide open jaw
        if jaw_open > self.thresholds['jaw_open']:
            return 'MOUTH_WIDE_OPEN', jaw_open
        
        # MOUTH_OPEN: Open mouth
        if mouth_open > self.thresholds['mouth_open']:
            return 'MOUTH_OPEN', mouth_open
        
        # GENUINE_SMILE: Smile with squinted eyes (Duchenne smile)
        if (mouth_smile > self.thresholds['smile'] and 
            eye_squint_left > 0.3 and eye_squint_right > 0.3):
            confidence = (mouth_smile + eye_squint_left + eye_squint_right) / 3
            return 'GENUINE_SMILE', confidence
        
        # SMILE: Just mouth smile
        if mouth_smile > self.thresholds['smile']:
            return 'SMILE', mouth_smile
        
        # FROWN: Downturned mouth
        if mouth_frown > self.thresholds['frown']:
            return 'FROWN', mouth_frown
        
        # BLINK_BOTH: Both eyes closed
        if (eye_blink_left > self.thresholds['blink'] and 
            eye_blink_right > self.thresholds['blink']):
            confidence = (eye_blink_left + eye_blink_right) / 2
            return 'BLINK_BOTH', confidence
        
        # WINK_LEFT: Only left eye closed
        if eye_blink_left > self.thresholds['blink']:
            return 'WINK_LEFT', eye_blink_left
        
        # WINK_RIGHT: Only right eye closed
        if eye_blink_right > self.thresholds['blink']:
            return 'WINK_RIGHT', eye_blink_right
        
        # PUCKER: Puckered lips (kiss face)
        if mouth_pucker > self.thresholds['pucker']:
            return 'PUCKER', mouth_pucker
        
        # NEUTRAL: No significant expression
        return 'NEUTRAL', 0.5
    
    def get_landmark_count(self) -> int:
        """Get the number of face landmarks (478 for MediaPipe Face Mesh)."""
        return 478
    
    def get_blendshape_count(self) -> int:
        """Get the number of blendshapes (52 for MediaPipe)."""
        return 52
    
    def release(self):
        """Clean up resources."""
        if self.detector:
            self.detector.close()
            logger.info("Expression Engine released")
