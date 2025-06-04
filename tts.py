import os
import logging
import uuid
import traceback
import re
from dotenv import load_dotenv
from typing import Union

# 1. Load environment variables
load_dotenv()

# 2. Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# 3. Import the official Smallest.ai SDK
try:
    from smallestai.waves import WavesClient
except ImportError:
    raise ImportError("❌ smallestai SDK is not installed. Run: pip install smallestai")

# 4. Read API key and ensure it’s set
SMALLEST_API_KEY = os.getenv("SMALLEST_API_KEY")
if not SMALLEST_API_KEY:
    raise EnvironmentError("SMALLEST_API_KEY not found in environment. Export it or put it in .env")

# 5. Output folder for synthesized audio
TTS_OUTPUT_DIR = "tts_output"
os.makedirs(TTS_OUTPUT_DIR, exist_ok=True)


def clean_text_for_tts(text: str) -> str:
    """
    Clean text by removing markdown syntax like **bold**, *italic*, headers, etc.
    """
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # Bold
    text = re.sub(r"\*(.*?)\*", r"\1", text)      # Italic or unordered lists
    text = re.sub(r"`(.*?)`", r"\1", text)        # Inline code
    text = re.sub(r"#+\s*", "", text)             # Headers
    return text


def generate_speech(
    text: str,
    save_as: Union[str, None] = None,
    *,
    model: str = "lightning",
    voice_id: str = "emily",
    sample_rate: int = 24000,
    speed: float = 1.0,
    consistency: float = 0.5,
    similarity: float = 0.0,
    enhancement: bool = False,
    return_metadata: bool = False
) -> Union[str, dict, None]:
    """
    Generate a WAV file from `text` using Smallest.ai’s WavesClient.

    Args:
        text (str): The text to synthesize.
        save_as (str | None): Filename (with .wav) under tts_output/.
        model (str): "lightning" or "lightning-large".
        voice_id (str): e.g. "emily", "raj", or custom voice-clone ID.
        sample_rate (int): Audio sample rate (default: 24000).
        speed (float): Speech speed multiplier (default: 1.0).
        consistency (float): For lightning-large (0.0–1.0).
        similarity (float): For lightning-large (0.0–1.0).
        enhancement (bool): For lightning-large (True/False).
        return_metadata (bool): If True, returns a dict with metadata.

    Returns:
        str | dict | None: Path to the saved WAV file or metadata dict if successful, None on failure.
    """

    if not text.strip():
        logger.warning("⚠️ No text provided for synthesis.")
        return None

    # Clean text for TTS
    clean_text = clean_text_for_tts(text)

    # 1. Create a WavesClient instance
    try:
        client = WavesClient(api_key=SMALLEST_API_KEY)
    except Exception as e:
        logger.error(f"❌ Failed to initialize WavesClient: {e}")
        logger.debug(traceback.format_exc())
        return None

    # 2. Determine output filename
    filename = save_as if save_as else f"{uuid.uuid4().hex}.wav"
    output_path = os.path.join(TTS_OUTPUT_DIR, filename)

    # 3. Build the arguments for client.synthesize()
    synth_kwargs = {
        "text": clean_text,
        "save_as": output_path,
        "sample_rate": sample_rate,
        "speed": speed,
        "voice_id": voice_id,
        "model": model
    }

    if model == "lightning-large":
        synth_kwargs.update({
            "consistency": consistency,
            "similarity": similarity,
            "enhancement": enhancement,
        })

    # Log parameters
    logger.info(f"📤 Starting synthesis: model={model}, voice={voice_id}, output={filename}")

    # 4. Call the SDK to synthesize speech
    try:
        client.synthesize(**synth_kwargs)
        logger.info(f"✅ Audio successfully saved: {output_path}")

        if return_metadata:
            return {
                "output_path": output_path,
                "model": model,
                "voice_id": voice_id,
                "sample_rate": sample_rate,
                "speed": speed,
                "enhancement": enhancement if model == "lightning-large" else None,
            }

        return output_path

    except Exception as e:
        logger.error(f"❌ TTS synthesis failed: {e}")
        logger.debug(traceback.format_exc())
        return None
