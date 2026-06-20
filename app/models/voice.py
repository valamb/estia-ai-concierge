from pydantic import BaseModel, Field
from typing import Literal


class VoiceTranscribeResponse(BaseModel):
    """Response after transcribing uploaded audio."""

    transcript: str = Field(..., description="Text transcribed from the audio")
    language_detected: str = Field(..., description="Detected language code")
    duration_seconds: float | None = Field(
        default=None, description="Duration of the audio clip in seconds"
    )


class VoiceChatResponse(BaseModel):
    """Full voice round-trip: audio in → text reply + audio out."""

    transcript: str = Field(..., description="What the guest said (transcribed)")
    reply: str = Field(..., description="ESTIA's text reply")
    conversation_id: str = Field(..., description="Conversation session ID")
    language_detected: str = Field(..., description="Detected language")
    model_used: str = Field(..., description="LLM model used for the reply")
    tokens_used: int = Field(default=0)
    audio_available: bool = Field(
        default=False,
        description="True when a TTS audio response was generated",
    )
    tts_voice: str | None = Field(
        default=None, description="TTS voice used (e.g. 'nova')"
    )
