"""
Voice Service
=============
Handles two operations:

1. Speech-to-Text  — OpenAI Whisper transcribes uploaded audio files.
2. Text-to-Speech  — OpenAI TTS converts a reply string to audio bytes.

Supported audio formats: mp3, mp4, mpeg, mpga, m4a, wav, webm (Whisper limits).
TTS voices: alloy, echo, fable, onyx, nova, shimmer.
"""

from io import BytesIO
from loguru import logger
from openai import AsyncOpenAI

from app.core.config import settings
from app.services.language_service import detect_language

_client = AsyncOpenAI(api_key=settings.openai_api_key)

# Voice that best fits a warm, professional hotel concierge
_DEFAULT_TTS_VOICE = "nova"

# Language → preferred TTS voice (both work in all languages; 'nova' is universal)
_LANGUAGE_VOICE_MAP: dict[str, str] = {
    "en": "nova",
    "el": "nova",
}

SUPPORTED_AUDIO_FORMATS = {
    "audio/mpeg",
    "audio/mp4",
    "audio/wav",
    "audio/webm",
    "audio/x-m4a",
    "audio/mpga",
}

MAX_AUDIO_SIZE_MB = 25  # Whisper API hard limit


async def transcribe(audio_bytes: bytes, filename: str = "audio.wav") -> tuple[str, str]:
    """
    Transcribe audio bytes using OpenAI Whisper.

    Returns:
        (transcript_text, detected_language_code)
    """
    logger.info(
        f"Whisper transcription request | filename={filename} | "
        f"size={len(audio_bytes) / 1024:.1f} KB"
    )

    audio_file = BytesIO(audio_bytes)
    audio_file.name = filename

    response = await _client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="verbose_json",  # includes detected language
    )

    transcript: str = response.text.strip()

    # Whisper returns ISO 639-1 codes; map to our supported set
    whisper_lang: str = getattr(response, "language", "") or ""
    if whisper_lang.startswith("el") or whisper_lang == "greek":
        detected_language = "el"
    elif whisper_lang.startswith("en") or whisper_lang == "english":
        detected_language = "en"
    else:
        # Fall back to character-level detection on the transcript
        detected_language = detect_language(transcript)

    logger.info(
        f"Whisper result | language={detected_language} | "
        f"transcript='{transcript[:80]}...'"
    )

    return transcript, detected_language


async def synthesize(text: str, language: str = "en") -> bytes:
    """
    Convert text to speech using OpenAI TTS.

    Returns:
        Raw MP3 audio bytes.
    """
    voice = _LANGUAGE_VOICE_MAP.get(language, _DEFAULT_TTS_VOICE)

    logger.info(
        f"TTS request | voice={voice} | language={language} | "
        f"chars={len(text)}"
    )

    response = await _client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text,
        response_format="mp3",
    )

    audio_bytes = response.content
    logger.info(f"TTS complete | size={len(audio_bytes) / 1024:.1f} KB")
    return audio_bytes
