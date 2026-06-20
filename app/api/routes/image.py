"""
Image endpoints
===============
POST /api/v1/image/chat  — Upload image + ask a question, get a concierge reply
"""

import uuid
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from loguru import logger
from openai import OpenAIError

from app.core.config import settings
from app.models.image import ImageChatResponse
from app.services import chat_service, image_service, rag_service
from app.services import conversation_store
from app.services.language_service import detect_language

router = APIRouter(prefix="/image", tags=["Image"])

_MAX_BYTES = image_service.MAX_IMAGE_SIZE_MB * 1024 * 1024


@router.post(
    "/chat",
    response_model=ImageChatResponse,
    summary="Image + text chat with ESTIA",
    description=(
        "Upload an image (JPEG, PNG, GIF, WebP) with an optional text question. "
        "ESTIA uses GPT-4o Vision to understand the image and respond as a hotel "
        "concierge. Supports multi-turn conversation via conversation_id."
    ),
)
async def image_chat(
    image: UploadFile = File(..., description="Image file (JPEG, PNG, GIF, WebP)"),
    question: str = Form(
        default="What can you tell me about this?",
        description="Guest's question about the image",
    ),
    conversation_id: str | None = Form(default=None),
    property_id: str | None = Form(default=None),
    language: str | None = Form(
        default=None,
        description="Preferred language ('en' or 'el'). Auto-detected if omitted.",
    ),
) -> ImageChatResponse:
    # --- Validate file ---
    content_type = image.content_type or "image/jpeg"

    if content_type not in image_service.SUPPORTED_IMAGE_TYPES:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported image type '{content_type}'. "
                f"Supported: {', '.join(image_service.SUPPORTED_IMAGE_TYPES)}"
            ),
        )

    image_bytes = await image.read()

    if not image_bytes:
        raise HTTPException(status_code=400, detail="Image file is empty.")

    if len(image_bytes) > _MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Image exceeds {image_service.MAX_IMAGE_SIZE_MB} MB limit.",
        )

    conv_id = conversation_id or str(uuid.uuid4())
    detected_lang = language or detect_language(question)

    logger.info(
        f"Image chat | conversation_id={conv_id} | "
        f"language={detected_lang} | property={property_id} | "
        f"image_size={len(image_bytes) / 1024:.1f} KB"
    )

    # --- RAG: fetch relevant hotel knowledge based on the question text ---
    context_documents = rag_service.retrieve_context(
        query=question,
        property_id=property_id,
        language=detected_lang,
    )

    # --- Load conversation history for multi-turn context ---
    history = conversation_store.get_history(conv_id)
    history_dicts = [{"role": m.role, "content": m.content} for m in history]

    # --- Call GPT-4o Vision ---
    try:
        result = await image_service.analyse_image(
            image_bytes=image_bytes,
            content_type=content_type,
            question=question,
            language=detected_lang,
            context_documents=context_documents,
            conversation_history=history_dicts,
        )
    except OpenAIError as e:
        logger.error(f"Vision API error | conversation_id={conv_id} | {e}")
        raise HTTPException(
            status_code=502,
            detail="The AI vision service is temporarily unavailable.",
        )

    # --- Save turn to conversation history ---
    from app.models.chat import ChatMessage

    conversation_store.append_message(
        conv_id, ChatMessage(role="user", content=f"[Image] {question}")
    )
    conversation_store.append_message(
        conv_id, ChatMessage(role="assistant", content=result.reply)
    )

    return ImageChatResponse(
        reply=result.reply,
        conversation_id=conv_id,
        language_detected=detected_lang,
        model_used=settings.openai_model,
        tokens_used=result.tokens_used,
        image_description=result.description or None,
    )
