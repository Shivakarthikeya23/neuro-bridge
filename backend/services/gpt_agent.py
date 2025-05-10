import os
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found in environment variables")

# Static gesture to intent mapping
simple_intent_map = {
    "blink": "Yes",
    "nod": "I agree",
    "head_shake": "No",
    "eyebrow_raise": "Please pay attention",
    "blink + look_down": "I need water",
    "blink + eyebrow_raise": "Call someone",
    "neutral": "I'm fine for now"
}

async def generate_intent_from_gesture_summary(summary: str) -> str:
    """Generate intent from gesture summary using static mapping or GPT fallback"""
    # Try static mapping first
    gesture_key = summary.strip().lower()
    if gesture_key in simple_intent_map:
        return simple_intent_map[gesture_key]
    
    # Fallback to GPT for unknown or complex gestures
    try:
        prompt = f"""
You are a compassionate assistant helping non-verbal individuals communicate using facial gestures and body movements. Based on movement patterns, suggest what they are likely trying to say in a full sentence.

Examples:
- Blink = "Yes"
- Head shake = "No"
- Nod = "I agree"
- Blink + Eyebrow raise = "Can you call someone?"
- Eyebrow raise + Head tilt = "You look good today."
- Blink + Look down = "I need water."
- Neutral + long blink = "I'm tired."
- Smile + eyebrow raise = "I’m feeling happy today."

Now analyze this user movement:
"{summary}"
Return only the interpreted intent sentence.
"""

        
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "nousresearch/deephermes-3-mistral-24b-preview:free",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ValueError(f"API request failed: {error_text}")
                
                data = await response.json()
                print(data)
                intent = data["choices"][0]["message"]["content"].strip()
                return intent
                
    except Exception as e:
        return "Unable to interpret gesture."

# Keep the old function for backward compatibility
async def generate_intent(gesture: str) -> str:
    return await generate_intent_from_gesture_summary(gesture)