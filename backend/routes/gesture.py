from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.mediapipe_processor import process_image

router = APIRouter()

class ImagePayload(BaseModel):
    image: str

@router.post("/detect-gesture")
async def detect_gesture(payload: ImagePayload):
    try:
        gesture, confidence = process_image(payload.image)
        return {"gesture": gesture, "confidence": confidence}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))