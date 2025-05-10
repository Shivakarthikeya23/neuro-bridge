from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.gpt_agent import generate_intent

router = APIRouter()

class GesturePayload(BaseModel):
    gesture: str

@router.post("/generate-intent")
async def interpret_gesture(payload: GesturePayload):
    try:
        intent = await generate_intent(payload.gesture)
        return {"intent": intent}
    except Exception as e:
        return {"intent": "Unable to interpret gesture."}