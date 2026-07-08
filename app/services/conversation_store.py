from collections import defaultdict
from app.models.chat import ChatMessage, GuestContext


# In-memory conversation store.
# Each key is a conversation_id; value is a list of ChatMessage objects.
# Phase 7+: replace with Redis or a database for persistence across restarts.
_store: dict[str, list[ChatMessage]] = defaultdict(list)
_context_store: dict[str, GuestContext] = {}

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


# ---------------------------------------------------------------------------
# Guest context store
# ---------------------------------------------------------------------------


def get_context(conversation_id: str) -> GuestContext:
    return _context_store.get(conversation_id, GuestContext())


def save_context(conversation_id: str, context: GuestContext) -> None:
    _context_store[conversation_id] = context


def clear_context(conversation_id: str) -> None:
    _context_store.pop(conversation_id, None)
