"""
Image Service
=============
Uses GPT-4o's vision capability to analyse images uploaded by hotel guests.

Typical use cases:
  - Guest photographs a dish → ESTIA identifies it and provides menu info
  - Guest photographs a facility → ESTIA describes it and answers questions
  - Guest photographs a sign or document → ESTIA reads and explains it
  - Guest photographs a view or landmark → ESTIA provides local context

Images are sent as base64-encoded data URLs directly to the OpenAI Chat
Completions API with the vision model. No image is stored server-side.

Supported formats: JPEG, PNG, GIF, WebP (OpenAI Vision limits).
Maximum image size: 20 MB per OpenAI's API limit.
"""

import base64
from loguru import logger
from openai import AsyncOpenAI

from app.core.config import settings
from app.services.language_service import get_system_prompt
from app.models.image import ImageAnalysisResult

_client = AsyncOpenAI(api_key=settings.openai_api_key)

SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_IMAGE_SIZE_MB = 20

_VISION_SYSTEM_ADDENDUM = {
    "en": (
        "\n\nYou also have vision capabilities. When a guest shares an image:\n"
        "- Identify what is shown (dish, facility, view, document, amenity)\n"
        "- Connect it to hotel services where relevant\n"
        "- Answer any question the guest asks about the image\n"
        "- If you cannot identify something clearly, say so honestly"
    ),
    "el": (
        "\n\nΈχεις επίσης δυνατότητες αναγνώρισης εικόνας. Όταν ένας επισκέπτης "
        "μοιράζεται μια εικόνα:\n"
        "- Αναγνώρισε τι απεικονίζει (πιάτο, εγκατάσταση, θέα, έγγραφο)\n"
        "- Συνδέσε το με τις υπηρεσίες του ξενοδοχείου όπου είναι σχετικό\n"
        "- Απάντα σε οποιαδήποτε ερώτηση του επισκέπτη σχετικά με την εικόνα\n"
        "- Αν δεν μπορείς να αναγνωρίσεις κάτι ξεκάθαρα, το λες ειλικρινά"
    ),
}


def _image_to_data_url(image_bytes: bytes, content_type: str) -> str:
    """Encode image bytes as a base64 data URL for the OpenAI Vision API."""
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{content_type};base64,{b64}"


async def analyse_image(
    image_bytes: bytes,
    content_type: str,
    question: str,
    language: str = "en",
    context_documents: list[str] | None = None,
    conversation_history: list[dict] | None = None,
) -> ImageAnalysisResult:
    """
    Send an image + question to GPT-4o Vision and return the concierge reply.

    Args:
        image_bytes:          Raw image file bytes.
        content_type:         MIME type (e.g. 'image/jpeg').
        question:             The guest's question about the image.
        language:             Language code for the system prompt ('en' or 'el').
        context_documents:    RAG-retrieved hotel knowledge to inject as context.
        conversation_history: Prior messages in this conversation (dicts with
                              role/content keys, excluding the current turn).

    Returns:
        ImageAnalysisResult with description and concierge reply.
    """
    logger.info(
        f"Vision request | language={language} | "
        f"image_size={len(image_bytes) / 1024:.1f} KB | "
        f"question='{question[:60]}'"
    )

    base_prompt = get_system_prompt(language)
    vision_addendum = _VISION_SYSTEM_ADDENDUM.get(language, _VISION_SYSTEM_ADDENDUM["en"])
    system_prompt = base_prompt + vision_addendum

    if context_documents:
        context_block = "\n\n---\n\n".join(context_documents)
        system_prompt += f"\n\n## Relevant Hotel Information\n\n{context_block}"

    data_url = _image_to_data_url(image_bytes, content_type)

    # Build the message list
    messages: list[dict] = [{"role": "system", "content": system_prompt}]

    if conversation_history:
        messages.extend(conversation_history)

    # Multimodal user message: image + text question
    messages.append({
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {"url": data_url, "detail": "high"},
            },
            {
                "type": "text",
                "text": question,
            },
        ],
    })

    response = await _client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
        max_tokens=settings.openai_max_tokens,
        temperature=settings.openai_temperature,
    )

    reply_text = response.choices[0].message.content or ""
    tokens_used = response.usage.total_tokens if response.usage else 0

    logger.info(f"Vision response | tokens={tokens_used}")

    # Extract a brief description for logging/metadata (first sentence of reply)
    first_sentence = reply_text.split(".")[0].strip() if reply_text else ""

    return ImageAnalysisResult(
        description=first_sentence,
        reply=reply_text,
        tokens_used=tokens_used,
    )
