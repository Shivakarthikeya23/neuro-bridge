import os
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found in environment variables")

async def generate_intent(gesture: str) -> str:
    """Generate intent from detected gesture using OpenRouter's GPT API"""
    try:
        # Construct the prompt based on the gesture
        prompt = f"The user {gesture}. What might they want to communicate?"
        
        # Prepare the API request
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "mistralai/mistral-nemo:free",  # Using Mistral as default model
            "messages": [
                {
                    "role": "system",
                    "content": "You are an assistive communication AI that interprets human gestures into likely intended meanings. Keep responses concise and natural."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ValueError(f"API request failed: {error_text}")
                
                data = await response.json()
                intent = data["choices"][0]["message"]["content"].strip()
                return intent
                
    except Exception as e:
        return "Unable to interpret gesture."