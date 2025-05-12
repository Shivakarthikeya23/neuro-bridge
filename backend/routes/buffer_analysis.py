from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import numpy as np
import cv2
import mediapipe as mp
from typing import List
from services.mediapipe_processor import face_mesh, decode_base64_image

router = APIRouter()

class BufferPayload(BaseModel):
    frames: List[str]

def analyze_movement_pattern(landmarks_sequence):
    if not landmarks_sequence or len(landmarks_sequence) < 2:
        return "no_movement_detected"
    
    # Extract nose tip position (point 1) across frames
    nose_positions = [(lm[1].x, lm[1].y) for lm in landmarks_sequence]
    
    # Calculate movement deltas
    x_deltas = [p[0] - nose_positions[0][0] for p in nose_positions]
    y_deltas = [p[1] - nose_positions[0][1] for p in nose_positions]
    
    # Calculate total movement in each direction
    total_x_movement = sum(abs(x) for x in x_deltas)
    total_y_movement = sum(abs(y) for y in y_deltas)
    
    # Enhanced blink detection
    blink_count = 0
    blink_threshold = 0.15  # Adjusted threshold
    consecutive_blinks = 0
    
    for landmarks in landmarks_sequence:
        # Get eye landmarks
        left_eye = np.array([[landmarks[p].x, landmarks[p].y] for p in [33, 160, 158, 133, 153, 144]])
        right_eye = np.array([[landmarks[p].x, landmarks[p].y] for p in [362, 385, 387, 263, 373, 380]])
        
        # Calculate eye aspect ratios
        left_ear = (np.linalg.norm(left_eye[1] - left_eye[5]) + np.linalg.norm(left_eye[2] - left_eye[4])) / (2.0 * np.linalg.norm(left_eye[0] - left_eye[3]))
        right_ear = (np.linalg.norm(right_eye[1] - right_eye[5]) + np.linalg.norm(right_eye[2] - right_eye[4])) / (2.0 * np.linalg.norm(right_eye[0] - right_eye[3]))
        
        # Average eye aspect ratio
        ear = (left_ear + right_ear) / 2.0
        
        if ear < blink_threshold:
            consecutive_blinks += 1
            if consecutive_blinks >= 2:  # Require at least 2 consecutive frames
                blink_count += 1
                consecutive_blinks = 0
        else:
            consecutive_blinks = 0
    
    # Enhanced movement detection thresholds
    nod_threshold = 0.08
    shake_threshold = 0.08
    
    # Determine primary movement pattern with improved accuracy
    if total_y_movement > nod_threshold and total_y_movement > total_x_movement * 1.2:
        return "head_nod"
    elif total_x_movement > shake_threshold and total_x_movement > total_y_movement * 1.2:
        return "head_shake"
    elif blink_count >= 1:  # More sensitive blink detection
        return "blink"
    elif any(y > 0.05 for y in y_deltas):  # More sensitive downward gaze detection
        return "downward_gaze"
    else:
        return "subtle_movement"

def build_movement_summary(pattern: str) -> str:
    summaries = {
        "head_nod": "The user nodded their head, indicating yes",
        "head_shake": "The user shook their head, indicating no",
        "blink": "The user blinked",
        "multiple_blinks": "The user blinked multiple times",
        "downward_gaze": "The user looked down",
        "subtle_movement": "The user made subtle movements",
        "no_movement_detected": "No significant movement was detected"
    }
    return summaries.get(pattern, "Unclear movement pattern")

@router.post("/analyze-buffer")
async def analyze_buffer(payload: BufferPayload):
    try:
        if not payload.frames:
            raise HTTPException(status_code=400, detail="No frames provided")
            
        landmarks_sequence = []
        
        # Process each frame
        for frame in payload.frames:
            # Decode and process image
            image = decode_base64_image(frame)
            if image is None:
                continue
                
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(image_rgb)
            
            if results.multi_face_landmarks:
                landmarks_sequence.append(results.multi_face_landmarks[0].landmark)
        
        if not landmarks_sequence:
            return {"intent": "I couldn't detect any facial movements. Please try again."}
        
        # Analyze movement pattern
        pattern = analyze_movement_pattern(landmarks_sequence)
        
        # Build movement summary
        movement_summary = build_movement_summary(pattern)
        
        # Get intent interpretation
        from services.gpt_agent import generate_intent_from_gesture_summary
        intent = await generate_intent_from_gesture_summary(movement_summary)
        
        return {"intent": intent}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))