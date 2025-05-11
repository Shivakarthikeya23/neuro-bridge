from fastapi import APIRouter, Request
from services.image_caption import generate_caption

router = APIRouter()

@router.post("/describe-image")
async def describe_image(request: Request):
    try:
        data = await request.json()
        base64_image = data.get("image", "").split(",")[-1]  # Remove data URL prefix if present
        description = await generate_caption(base64_image)
        return {"description": description}
    except Exception as e:
        return {"description": "Unable to describe the image."}