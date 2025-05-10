import base64
import cv2
import numpy as np
import mediapipe as mp
from typing import Tuple

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

def decode_base64_image(base64_string: str) -> np.ndarray:
    """Decode base64 string to OpenCV image"""
    try:
        # Handle data URI scheme
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Decode base64 to image
        img_data = base64.b64decode(base64_string)
        nparr = np.frombuffer(img_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("Failed to decode image")
            
        return image
    except Exception as e:
        raise ValueError(f"Error decoding image: {str(e)}")

def calculate_eye_aspect_ratio(eye_landmarks: np.ndarray) -> float:
    """
    Calculate the eye aspect ratio using the formula:
    EAR = (||p2-p6|| + ||p3-p5||) / (2||p1-p4||)
    where p1-p6 are the 2D landmark coordinates
    """
    # Vertical distances
    v1 = np.linalg.norm(eye_landmarks[1] - eye_landmarks[5])
    v2 = np.linalg.norm(eye_landmarks[2] - eye_landmarks[4])
    # Horizontal distance
    h = np.linalg.norm(eye_landmarks[0] - eye_landmarks[3])
    # Calculate ratio
    return (v1 + v2) / (2.0 * h) if h > 0 else 0.0

def calculate_eyebrow_eye_distance(eyebrow_y: float, eye_y: float) -> float:
    """Calculate normalized distance between eyebrow and eye"""
    return abs(eyebrow_y - eye_y)

def process_image(base64_image: str) -> Tuple[str, float]:
    """Process image and detect facial gestures"""
    try:
        # Decode image
        image = decode_base64_image(base64_image)
        
        # Convert to RGB (MediaPipe requires RGB input)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Process the image with MediaPipe
        results = face_mesh.process(image_rgb)
        
        if not results.multi_face_landmarks:
            return "no_face_detected", 0.0
        
        landmarks = results.multi_face_landmarks[0].landmark
        
        # Extract eye landmarks
        # MediaPipe face mesh indices for eyes
        left_eye = np.array([[landmarks[p].x, landmarks[p].y] for p in [33, 160, 158, 133, 153, 144]])
        right_eye = np.array([[landmarks[p].x, landmarks[p].y] for p in [362, 385, 387, 263, 373, 380]])
        
        # Calculate eye aspect ratios
        left_ear = calculate_eye_aspect_ratio(left_eye)
        right_ear = calculate_eye_aspect_ratio(right_eye)
        
        # Average eye aspect ratio
        ear = (left_ear + right_ear) / 2.0
        
        # Extract eyebrow and eye landmarks for eyebrow raise detection
        left_eyebrow_y = landmarks[66].y
        left_eye_top_y = landmarks[159].y
        right_eyebrow_y = landmarks[296].y
        right_eye_top_y = landmarks[386].y
        
        # Calculate eyebrow distances
        left_distance = calculate_eyebrow_eye_distance(left_eyebrow_y, left_eye_top_y)
        right_distance = calculate_eyebrow_eye_distance(right_eyebrow_y, right_eye_top_y)
        
        # Average eyebrow distance
        eyebrow_distance = (left_distance + right_distance) / 2.0
        
        # Detect gestures with confidence scores
        BLINK_THRESHOLD = 0.2
        EYEBROW_RAISE_THRESHOLD = 0.05
        
        if ear < BLINK_THRESHOLD:
            # Convert EAR to confidence (lower EAR = higher confidence for blink)
            confidence = min(1.0, (BLINK_THRESHOLD - ear) / BLINK_THRESHOLD + 0.3)
            return "blink", confidence
        elif eyebrow_distance > EYEBROW_RAISE_THRESHOLD:
            # Convert distance to confidence
            confidence = min(1.0, eyebrow_distance / EYEBROW_RAISE_THRESHOLD * 0.7)
            return "eyebrow_raise", confidence
        else:
            # Neutral expression with moderate confidence
            return "neutral", 0.6
            
    except Exception as e:
        raise ValueError(f"Error processing image: {str(e)}")