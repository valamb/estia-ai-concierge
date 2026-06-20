from collections import defaultdict
from app.models.chat import ChatMessage


# In-memory conversation store.
# Each key is a conversation_id; value is a list of ChatMessage objects.
# Phase 7+: replace with Redis or a database for persistence across restarts.
_store: dict[str, list[ChatMessage]] = defaultdict(list)

MAX_HISTORY_MESSAGES = 20


def get_history(conversation_id: str) -> list[ChatMessage]:
    return _store[conversation_id]


def append_message(conversation_id: str, message: ChatMessage) -> None:
    _store[conversation_id].append(message)
    # Keep only the most recent messages to avoid exceeding token limits
    if len(_store[conversation_id]) > MAX_HISTORY_MESSAGES:
        _store[conversation_id] = _store[conversation_id][-MAX_HISTORY_MESSAGES:]


def clear_history(conversation_id: str) -> None:
    _store.pop(conversation_id, None)
