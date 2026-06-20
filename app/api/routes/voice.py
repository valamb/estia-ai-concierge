"""
Voice endpoints
===============
POST /api/v1/voice/transcribe  — Upload audio, receive transcript
POST /api/v1/voice/chat        — Upload audio, receive text reply + MP3 audio
"""

import uuid
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from loguru import logger
from openai import OpenAIError

from app.core.config import settings
from app.models.voice import VoiceTranscribeResponse, VoiceChatResponse
from app.services import chat_service, voice_service
from app.services import rag_service

router = APIRouter(prefix="/voice", tags=["Voice"])

_MAX_BYTES = voice_service.MAX_AUDIO_SIZE_MB * 1024 * 1024


@router.post(
    "/transcribe",
    response_model=VoiceTranscribeResponse,
    summary="Transcribe audio to text",
    description=(
        "Upload an audio file (wav, mp3, m4a, webm). "
        "Returns the Whisper transcription and detected language."
    ),
)
async def transcribe(
    audio: UploadFile = File(..., description="Audio file to transcribe"),
) -> VoiceTranscribeResponse:
    audio_bytes = await audio.read()

    if len(audio_bytes) > _MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Audio file exceeds {voice_service.MAX_AUDIO_SIZE_MB} MB limit.",
        )
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Audio file is empty.")

    logger.info(f"Transcribe request | filename={audio.filename}")

    try:
        transcript, detected_language = await voice_service.transcribe(
            audio_bytes=audio_bytes,
            filename=audio.filename or "audio.wav",
        )
    except OpenAIError as e:
        logger.error(f"Whisper error: {e}")
        raise HTTPException(
            status_code=502,
            detail="Speech-to-text service is temporarily unavailable.",
        )

    return VoiceTranscribeResponse(
        transcript=transcript,
        language_detected=detected_language,
    )


@router.post(
    "/chat",
    response_model=VoiceChatResponse,
    summary="Voice chat with ESTIA",
    description=(
        "Upload an audio file. ESTIA transcribes it, generates a concierge reply, "
        "and returns both the text response and an MP3 audio reply."
    ),
)
async def voice_chat(
    audio: UploadFile = File(..., description="Guest audio message"),
    conversation_id: str | None = Form(default=None),
    property_id: str | None = Form(default=None),
    tts_enabled: bool = Form(default=True, description="Set false to skip TTS"),
) -> VoiceChatResponse:
    audio_bytes = await audio.read()

    if len(audio_bytes) > _MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Audio file exceeds {voice_service.MAX_AUDIO_SIZE_MB} MB limit.",
        )
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Audio file is empty.")

    conv_id = conversation_id or str(uuid.uuid4())
    logger.info(f"Voice chat | conversation_id={conv_id} | property={property_id}")

    # Step 1 — Transcribe
    try:
        transcript, detected_language = await voice_service.transcribe(
            audio_bytes=audio_bytes,
            filename=audio.filename or "audio.wav",
        )
    except OpenAIError as e:
        logger.error(f"Whisper error: {e}")
        raise HTTPException(
            status_code=502,
            detail="Speech-to-text service is temporarily unavailable.",
        )

    # Step 2 — RAG retrieval
    context_documents = rag_service.retrieve_context(
        query=transcript,
        property_id=property_id,
        language=detected_language,
    )

    # Step 3 — Chat completion
    try:
        reply, _, tokens_used = await chat_service.chat(
            conversation_id=conv_id,
            user_message=transcript,
            language=detected_language,
            context_documents=context_documents,
        )
    except OpenAIError as e:
        logger.error(f"OpenAI chat error: {e}")
        raise HTTPException(
            status_code=502,
            detail="AI service is temporarily unavailable.",
        )

    # Step 4 — TTS (optional)
    tts_voice: str | None = None
    audio_available = False

    if tts_enabled:
        try:
            mp3_bytes = await voice_service.synthesize(
                text=reply, language=detected_language
            )
            tts_voice = voice_service._LANGUAGE_VOICE_MAP.get(
                detected_language, voice_service._DEFAULT_TTS_VOICE
            )
            audio_available = True
            logger.info(f"TTS ready | {len(mp3_bytes) / 1024:.1f} KB")
        except OpenAIError as e:
            logger.warning(f"TTS failed (non-fatal): {e}")

    return VoiceChatResponse(
        transcript=transcript,
        reply=reply,
        conversation_id=conv_id,
        language_detected=detected_language,
        model_used=settings.openai_model,
        tokens_used=tokens_used,
        audio_available=audio_available,
        tts_voice=tts_voice,
    )


@router.post(
    "/speak",
    summary="Convert text to speech",
    description="Convert any text to MP3 audio using OpenAI TTS. Returns raw MP3 bytes.",
    response_class=Response,
    responses={200: {"content": {"audio/mpeg": {}}}},
)
async def speak(
    text: str = Form(..., min_length=1, max_length=4096),
    language: str = Form(default="en"),
) -> Response:
    """Convert a text string to MP3 audio."""
    if language not in settings.supported_languages_list:
        language = settings.default_language

    try:
        mp3_bytes = await voice_service.synthesize(text=text, language=language)
    except OpenAIError as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(
            status_code=502,
            detail="Text-to-speech service is temporarily unavailable.",
        )

    return Response(content=mp3_bytes, media_type="audio/mpeg")
