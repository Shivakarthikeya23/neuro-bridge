import os
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found in environment variables")

async def generate_caption(base64_image: str) -> str:
    """Generate a caption for the image using OpenRouter's GPT-4 Vision API"""
    if not base64_image:
        return "No image provided"
        
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",  # Required by OpenRouter
            "X-Title": "Neuro-Bridge"  # Application name
        }
        
        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that describes images clearly and concisely. Focus on the main subjects and actions in the image."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe what you see in this image in one clear, concise sentence."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 100
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"API Error: {error_text}")  # Log the error
                    return "I'm sorry, I couldn't analyze the image at the moment."
                
                data = await response.json()
                if not data.get("choices"):
                    return "I couldn't generate a description for this image."
                    
                description = data["choices"][0]["message"]["content"].strip()
                return description
                
    except Exception as e:
        print(f"Error in generate_caption: {str(e)}")  # Log the error
        return "I'm sorry, I couldn't process the image at the moment."