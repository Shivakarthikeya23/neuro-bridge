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
    if not landmarks_sequence:
        return "no_movement_detected"
    
    # Extract nose tip position (point 1) across frames
    nose_positions = [(lm[1].x, lm[1].y) for lm in landmarks_sequence]
    
    # Calculate movement deltas
    x_deltas = [p[0] - nose_positions[0][0] for p in nose_positions]
    y_deltas = [p[1] - nose_positions[0][1] for p in nose_positions]
    
    # Calculate total movement in each direction
    total_x_movement = sum(abs(x) for x in x_deltas)
    total_y_movement = sum(abs(y) for y in y_deltas)
    
    # Analyze blinks using eye landmarks
    blink_count = 0
    for landmarks in landmarks_sequence:
        # Get eye landmarks
        left_eye = np.array([[landmarks[p].x, landmarks[p].y] for p in [33, 160, 158, 133, 153, 144]])
        right_eye = np.array([[landmarks[p].x, landmarks[p].y] for p in [362, 385, 387, 263, 373, 380]])
        
        # Calculate eye aspect ratios
        left_ear = (np.linalg.norm(left_eye[1] - left_eye[5]) + np.linalg.norm(left_eye[2] - left_eye[4])) / (2.0 * np.linalg.norm(left_eye[0] - left_eye[3]))
        right_ear = (np.linalg.norm(right_eye[1] - right_eye[5]) + np.linalg.norm(right_eye[2] - right_eye[4])) / (2.0 * np.linalg.norm(right_eye[0] - right_eye[3]))
        
        # Average eye aspect ratio
        ear = (left_ear + right_ear) / 2.0
        if ear < 0.2:  # Threshold for blink detection
            blink_count += 1
    
    # Determine primary movement pattern
    if total_y_movement > total_x_movement * 1.5:
        return "head_nod"
    elif total_x_movement > total_y_movement * 1.5:
        return "head_shake"
    elif blink_count > 2:  # Multiple blinks threshold
        return "multiple_blinks"
    elif any(y > 0.1 for y in y_deltas):  # Downward gaze threshold
        return "downward_gaze"
    else:
        return "subtle_movement"

def build_movement_summary(pattern: str) -> str:
    summaries = {
        "head_nod": "The user nodded their head, indicating 'yes'",
        "head_shake": "The user shook their head, indicating 'no'",
        "multiple_blinks": "The user blinked multiple times",
        "downward_gaze": "The user looked down",
        "subtle_movement": "The user made subtle movements",
        "no_movement_detected": "No significant movement was detected"
    }
    return summaries.get(pattern, "Unclear movement pattern")

@router.post("/analyze-buffer")
async def analyze_buffer(payload: BufferPayload):
    try:
        landmarks_sequence = []
        
        # Process each frame
        for frame in payload.frames:
            # Decode and process image
            image = decode_base64_image(frame)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(image_rgb)
            
            if results.multi_face_landmarks:
                landmarks_sequence.append(results.multi_face_landmarks[0].landmark)
        
        # Analyze movement pattern
        pattern = analyze_movement_pattern(landmarks_sequence)
        
        # Build movement summary
        movement_summary = build_movement_summary(pattern)
        
        # Get intent interpretation using the new function
        from services.gpt_agent import generate_intent_from_gesture_summary
        intent = await generate_intent_from_gesture_summary(movement_summary)
        
        return {"intent": intent}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))