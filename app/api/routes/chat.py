import uuid
from fastapi import APIRouter, HTTPException
from loguru import logger
from openai import OpenAIError

from app.models.chat import ChatRequest, ChatResponse
from app.services import chat_service
from app.services import conversation_store
from app.services import rag_service
from app.services.language_service import detect_language
from app.services.context_extraction import extract_context, merge_context
from app.services.retrieval_context import build_enriched_query, detect_intent
from app.core.config import settings

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a message to ESTIA",
    description=(
        "Send a guest message and receive an AI-generated concierge reply. "
        "Supports multi-turn conversation via conversation_id. "
        "Language is auto-detected from the message if not specified. "
        "Responses are grounded in the hotel knowledge base via RAG."
    ),
    tags=["Chat"],
)
async def chat(request: ChatRequest) -> ChatResponse:
    conversation_id = request.conversation_id or str(uuid.uuid4())

    logger.info(
        f"Chat request | conversation_id={conversation_id} | "
        f"property={request.property_id}"
    )

    try:
        # Detect language early so RAG can fetch language-matched documents
        detected_lang = request.language or detect_language(request.message)

        # Extract, merge and persist guest context for this conversation
        existing_context = conversation_store.get_context(conversation_id)
        new_context = extract_context(request.message)
        updated_context = merge_context(existing_context, new_context)
        conversation_store.save_context(conversation_id, updated_context)

        # Build enriched RAG query and detect intent for category-aware retrieval
        enriched_query = build_enriched_query(request.message, updated_context)
        intent = detect_intent(request.message)

        # Retrieve relevant hotel knowledge from ChromaDB
        context_documents = rag_service.retrieve_context(
            query=enriched_query,
            property_id=request.property_id,
            language=detected_lang,
            intent=intent,
        )

        if context_documents:
            logger.debug(
                f"RAG injected {len(context_documents)} chunk(s) into context"
            )

        reply, detected_language, tokens_used = await chat_service.chat(
            conversation_id=conversation_id,
            user_message=request.message,
            language=request.language,
            context_documents=context_documents,
            guest_context=updated_context,
        )
    except OpenAIError as e:
        logger.error(f"OpenAI error | conversation_id={conversation_id} | {e}")
        raise HTTPException(
            status_code=502,
            detail="The AI service is temporarily unavailable. Please try again.",
        )
    except Exception as e:
        logger.error(f"Unexpected error | conversation_id={conversation_id} | {e}")
        raise HTTPException(
            status_code=502,
            detail="An unexpected error occurred. Please try again.",
        )

    return ChatResponse(
        reply=reply,
        conversation_id=conversation_id,
        language_detected=detected_language,
        model_used=settings.openai_model,
        tokens_used=tokens_used,
    )
