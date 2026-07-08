"""Tests for GuestContext operations in conversation_store. Fully offline."""

import pytest

from app.models.chat import GuestContext
from app.services import conversation_store


@pytest.fixture(autouse=True)
def _clean_context_store():
    """Wipe the context store before and after every test."""
    conversation_store._context_store.clear()
    yield
    conversation_store._context_store.clear()


# ---------------------------------------------------------------------------
# Saving context
# ---------------------------------------------------------------------------


def test_save_context_stores_object():
    ctx = GuestContext(property="porto_elounda", guest_type="family")
    conversation_store.save_context("conv-1", ctx)
    assert conversation_store._context_store["conv-1"] is ctx


def test_save_context_overwrites_existing():
    ctx1 = GuestContext(property="porto_elounda")
    ctx2 = GuestContext(property="elounda_mare")
    conversation_store.save_context("conv-1", ctx1)
    conversation_store.save_context("conv-1", ctx2)
    stored = conversation_store._context_store["conv-1"]
    assert stored.property == "elounda_mare"


# ---------------------------------------------------------------------------
# Retrieving context
# ---------------------------------------------------------------------------


def test_get_context_returns_saved_object():
    ctx = GuestContext(property="elounda_peninsula", occasion="anniversary")
    conversation_store.save_context("conv-2", ctx)
    retrieved = conversation_store.get_context("conv-2")
    assert retrieved.property == "elounda_peninsula"
    assert retrieved.occasion == "anniversary"


def test_get_context_returns_empty_for_unknown_id():
    result = conversation_store.get_context("does-not-exist")
    assert isinstance(result, GuestContext)
    assert result.property is None
    assert result.guest_type is None
    assert result.children_ages == []
    assert result.interests == []
    assert result.dietary_preferences == []


# ---------------------------------------------------------------------------
# Updating (save over an existing entry)
# ---------------------------------------------------------------------------


def test_update_context_replaces_fully():
    original = GuestContext(property="porto_elounda", guest_type="couple")
    conversation_store.save_context("conv-3", original)

    updated = GuestContext(
        property="porto_elounda",
        guest_type="family",
        children_ages=[5, 8],
    )
    conversation_store.save_context("conv-3", updated)

    result = conversation_store.get_context("conv-3")
    assert result.guest_type == "family"
    assert set(result.children_ages) == {5, 8}


# ---------------------------------------------------------------------------
# Clearing context
# ---------------------------------------------------------------------------


def test_clear_context_removes_entry():
    ctx = GuestContext(property="porto_elounda")
    conversation_store.save_context("conv-4", ctx)
    conversation_store.clear_context("conv-4")
    result = conversation_store.get_context("conv-4")
    assert result.property is None


def test_clear_context_on_unknown_id_does_not_raise():
    conversation_store.clear_context("never-existed")


def test_clear_context_does_not_affect_other_conversations():
    conversation_store.save_context("conv-5", GuestContext(property="porto_elounda"))
    conversation_store.save_context("conv-6", GuestContext(property="elounda_mare"))
    conversation_store.clear_context("conv-5")
    assert conversation_store.get_context("conv-5").property is None
    assert conversation_store.get_context("conv-6").property == "elounda_mare"


# ---------------------------------------------------------------------------
# Isolation between conversation_ids
# ---------------------------------------------------------------------------


def test_two_conversations_are_isolated():
    ctx_a = GuestContext(property="porto_elounda", guest_type="family", children_ages=[5, 8])
    ctx_b = GuestContext(property="elounda_mare", guest_type="honeymoon", occasion="honeymoon")

    conversation_store.save_context("conv-A", ctx_a)
    conversation_store.save_context("conv-B", ctx_b)

    result_a = conversation_store.get_context("conv-A")
    result_b = conversation_store.get_context("conv-B")

    assert result_a.property == "porto_elounda"
    assert result_a.guest_type == "family"
    assert result_b.property == "elounda_mare"
    assert result_b.guest_type == "honeymoon"


def test_modifying_one_conversation_does_not_affect_another():
    conversation_store.save_context("conv-X", GuestContext(property="porto_elounda"))
    conversation_store.save_context("conv-Y", GuestContext(property="elounda_mare"))

    # Overwrite conv-X completely
    conversation_store.save_context("conv-X", GuestContext(property="elounda_peninsula"))

    assert conversation_store.get_context("conv-X").property == "elounda_peninsula"
    assert conversation_store.get_context("conv-Y").property == "elounda_mare"


# ---------------------------------------------------------------------------
# Existing message history is unaffected
# ---------------------------------------------------------------------------


def test_existing_history_unaffected_by_context_operations():
    from app.models.chat import ChatMessage

    conversation_store._store.clear()
    msg = ChatMessage(role="user", content="Hello")
    conversation_store.append_message("conv-H", msg)

    # Save and clear context for the same conversation_id
    conversation_store.save_context("conv-H", GuestContext(property="porto_elounda"))
    conversation_store.clear_context("conv-H")

    # Message history must still be intact
    history = conversation_store.get_history("conv-H")
    assert len(history) == 1
    assert history[0].content == "Hello"

    conversation_store._store.clear()
