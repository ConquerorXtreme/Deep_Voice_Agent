import os
import requests
import uuid
import logging
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

SMALLEST_API_KEY = os.getenv("SMALLEST_API_KEY")
TTS_OUTPUT_DIR = "tts_output"

os.makedirs(TTS_OUTPUT_DIR, exist_ok=True)

def generate_speech(text: str) -> str:
    if not SMALLEST_API_KEY:
        logger.error("❌ Missing SMALLEST_API_KEY environment variable.")
        raise EnvironmentError("SMALLEST_API_KEY not set")

    url = "https://waves-api.smallest.ai/api/v1/lightning-large/get_speech"
    headers = {
        "Authorization": f"Bearer {SMALLEST_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "voice_id": "emily",          
        "add_wav_header": False,
        "sample_rate": 24000,
        "speed": 1,
        "language": "en",
        "consistency": 0.5,
        "similarity": 0,
        "enhancement": 1
    }

    try:
        logger.info("📤 Sending TTS request to Smallest.ai...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        data = response.json()
        audio_url = data.get("audio_url")  # Usually the response has a URL to the audio file

        if not audio_url:
            raise ValueError(f"No audio_url found in response: {data}")

        logger.info(f"🔗 Audio URL received: {audio_url}")

        # Download the audio content
        audio_response = requests.get(audio_url)
        audio_response.raise_for_status()

        filename = f"{uuid.uuid4().hex}.wav"  # Use .wav or .mp3 depending on format returned
        filepath = os.path.join(TTS_OUTPUT_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(audio_response.content)

        logger.info(f"✅ TTS audio saved at: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"TTS request failed: {e}")
        raise



