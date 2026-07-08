from openai import AsyncOpenAI
from loguru import logger

from app.core.config import settings
from app.models.chat import ChatMessage, GuestContext
from app.services import conversation_store
from app.services.language_service import detect_language, get_system_prompt
from app.services.context_extraction import format_context_block

_client = AsyncOpenAI(api_key=settings.openai_api_key)


async def chat(
    conversation_id: str,
    user_message: str,
    language: str | None = None,
    context_documents: list[str] | None = None,
    guest_context: GuestContext | None = None,
) -> tuple[str, str, int]:
    """
    Send a message to OpenAI and return the assistant reply.

    Returns:
        tuple of (reply_text, language_detected, tokens_used)
    """
    detected_language = language or detect_language(user_message)
    system_prompt = get_system_prompt(detected_language)

    if context_documents:
        context_block = "\n\n---\n\n".join(context_documents)
        system_prompt += (
            f"\n\n## Relevant Hotel Information\n\n{context_block}"
        )

    if guest_context:
        guest_block = format_context_block(guest_context)
        if guest_block:
            system_prompt += f"\n\n{guest_block}"

    history = conversation_store.get_history(conversation_id)

    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": user_message})

    logger.debug(
        f"OpenAI request | conversation_id={conversation_id} | "
        f"language={detected_language} | history_length={len(history)} | "
        f"model={settings.openai_model}"
    )

    response = await _client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
        max_tokens=settings.openai_max_tokens,
        temperature=settings.openai_temperature,
    )

    reply = response.choices[0].message.content or ""
    tokens_used = response.usage.total_tokens if response.usage else 0

    conversation_store.append_message(
        conversation_id, ChatMessage(role="user", content=user_message)
    )
    conversation_store.append_message(
        conversation_id, ChatMessage(role="assistant", content=reply)
    )

    logger.info(
        f"OpenAI response | conversation_id={conversation_id} | "
        f"tokens={tokens_used}"
    )

    return reply, detected_language, tokens_used
