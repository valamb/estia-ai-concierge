import pytest
from app.services import conversation_store
from app.models.chat import ChatMessage


def test_empty_history_for_new_conversation():
    history = conversation_store.get_history("new-conv-999")
    assert history == []


def test_append_and_retrieve_message():
    cid = "test-conv-001"
    conversation_store.clear_history(cid)
    msg = ChatMessage(role="user", content="Hello")
    conversation_store.append_message(cid, msg)
    history = conversation_store.get_history(cid)
    assert len(history) == 1
    assert history[0].content == "Hello"


def test_history_preserves_order():
    cid = "test-conv-002"
    conversation_store.clear_history(cid)
    msgs = [
        ChatMessage(role="user", content="First"),
        ChatMessage(role="assistant", content="Second"),
        ChatMessage(role="user", content="Third"),
    ]
    for m in msgs:
        conversation_store.append_message(cid, m)
    history = conversation_store.get_history(cid)
    assert [m.content for m in history] == ["First", "Second", "Third"]


def test_clear_history():
    cid = "test-conv-003"
    conversation_store.append_message(cid, ChatMessage(role="user", content="Hi"))
    conversation_store.clear_history(cid)
    assert conversation_store.get_history(cid) == []
