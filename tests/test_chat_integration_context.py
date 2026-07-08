"""D4 offline tests — guest context integration into chat flow.

All tests mock OpenAI so no API key is required.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.chat import GuestContext
from app.services.context_extraction import format_context_block, extract_context, merge_context
from app.services import conversation_store


@pytest.fixture(autouse=True)
def _clean_stores():
    conversation_store._store.clear()
    conversation_store._context_store.clear()
    yield
    conversation_store._store.clear()
    conversation_store._context_store.clear()


# ---------------------------------------------------------------------------
# 1. format_context_block — only populated fields appear
# ---------------------------------------------------------------------------


def test_context_block_all_fields():
    ctx = GuestContext(
        property="porto_elounda",
        guest_type="family",
        children_ages=[5, 8],
        interests=["spa", "beach"],
        occasion="anniversary",
        dietary_preferences=["vegetarian"],
        mobility_needs="wheelchair",
        preferred_language="en",
    )
    block = format_context_block(ctx)
    assert block is not None
    assert "Porto Elounda" in block
    assert "Family" in block
    assert "5, 8" in block
    assert "spa" in block
    assert "beach" in block
    assert "Anniversary" in block
    assert "vegetarian" in block
    assert "wheelchair" in block


def test_context_block_partial_fields():
    ctx = GuestContext(property="elounda_mare", guest_type="couple")
    block = format_context_block(ctx)
    assert block is not None
    assert "Elounda Mare" in block
    assert "Couple" in block
    assert "Children" not in block
    assert "Interests" not in block


def test_context_block_empty_returns_none():
    ctx = GuestContext()
    block = format_context_block(ctx)
    assert block is None


def test_context_block_heading():
    ctx = GuestContext(property="elounda_peninsula")
    block = format_context_block(ctx)
    assert block.startswith("## Known Guest Context")


def test_context_block_lists_no_none_values():
    ctx = GuestContext(property="porto_elounda")
    block = format_context_block(ctx)
    assert "None" not in block
    assert "null" not in block


# ---------------------------------------------------------------------------
# 2. context_block injected into system prompt
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_guest_context_injected_into_system_prompt():
    """Verify that format_context_block output appears in the messages sent to OpenAI."""
    ctx = GuestContext(property="porto_elounda", guest_type="family", children_ages=[5, 8])

    captured_messages: list = []

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Here is a recommendation."))]
    mock_response.usage = MagicMock(total_tokens=42)

    async def fake_create(**kwargs):
        captured_messages.extend(kwargs["messages"])
        return mock_response

    with patch("app.services.chat_service._client") as mock_client:
        mock_client.chat.completions.create = fake_create
        from app.services import chat_service
        await chat_service.chat(
            conversation_id="test-inject",
            user_message="Where should we eat?",
            guest_context=ctx,
        )

    system_content = captured_messages[0]["content"]
    assert "Known Guest Context" in system_content
    assert "Porto Elounda" in system_content
    assert "Family" in system_content
    assert "5, 8" in system_content


# ---------------------------------------------------------------------------
# 3. empty context is NOT injected
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_guest_context_not_injected():
    ctx = GuestContext()

    captured_messages: list = []

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Hello."))]
    mock_response.usage = MagicMock(total_tokens=10)

    async def fake_create(**kwargs):
        captured_messages.extend(kwargs["messages"])
        return mock_response

    with patch("app.services.chat_service._client") as mock_client:
        mock_client.chat.completions.create = fake_create
        from app.services import chat_service
        await chat_service.chat(
            conversation_id="test-empty",
            user_message="Hello",
            guest_context=ctx,
        )

    system_content = captured_messages[0]["content"]
    assert "Known Guest Context" not in system_content


@pytest.mark.asyncio
async def test_none_guest_context_not_injected():
    captured_messages: list = []

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Hello."))]
    mock_response.usage = MagicMock(total_tokens=10)

    async def fake_create(**kwargs):
        captured_messages.extend(kwargs["messages"])
        return mock_response

    with patch("app.services.chat_service._client") as mock_client:
        mock_client.chat.completions.create = fake_create
        from app.services import chat_service
        await chat_service.chat(
            conversation_id="test-none",
            user_message="Hello",
            guest_context=None,
        )

    system_content = captured_messages[0]["content"]
    assert "Known Guest Context" not in system_content


# ---------------------------------------------------------------------------
# 4. property remembered across messages (route-level simulation)
# ---------------------------------------------------------------------------


def test_property_context_persists_and_merges():
    """Simulate the route's extract → merge → save cycle across two messages."""
    conv_id = "conv-property-test"

    # Message 1: guest mentions property
    msg1 = "We are staying at Porto Elounda."
    existing = conversation_store.get_context(conv_id)
    new = extract_context(msg1)
    merged = merge_context(existing, new)
    conversation_store.save_context(conv_id, merged)

    assert conversation_store.get_context(conv_id).property == "porto_elounda"

    # Message 2: generic question — property must still be remembered
    msg2 = "Where should we have dinner tonight?"
    existing = conversation_store.get_context(conv_id)
    new = extract_context(msg2)
    merged = merge_context(existing, new)
    conversation_store.save_context(conv_id, merged)

    assert conversation_store.get_context(conv_id).property == "porto_elounda"


# ---------------------------------------------------------------------------
# 5. family context remembered and injected into prompt
# ---------------------------------------------------------------------------


def test_family_context_persists_and_merges():
    """Simulate the route's extract → merge → save cycle for family context."""
    conv_id = "conv-family-test"

    msg1 = "We are a family at Porto Elounda with children aged 5 and 8."
    existing = conversation_store.get_context(conv_id)
    new = extract_context(msg1)
    merged = merge_context(existing, new)
    conversation_store.save_context(conv_id, merged)

    ctx = conversation_store.get_context(conv_id)
    assert ctx.guest_type == "family"
    assert set(ctx.children_ages) == {5, 8}

    # Second message — family info must still be present
    msg2 = "What activities do you recommend?"
    existing = conversation_store.get_context(conv_id)
    new = extract_context(msg2)
    merged = merge_context(existing, new)
    conversation_store.save_context(conv_id, merged)

    ctx = conversation_store.get_context(conv_id)
    assert ctx.guest_type == "family"
    assert set(ctx.children_ages) == {5, 8}


@pytest.mark.asyncio
async def test_family_context_appears_in_prompt():
    """Family context from a prior turn must appear in the system prompt."""
    conv_id = "conv-family-prompt"

    # Seed the store as the route would after message 1
    ctx = GuestContext(
        property="porto_elounda",
        guest_type="family",
        children_ages=[5, 8],
    )
    conversation_store.save_context(conv_id, ctx)

    captured_messages: list = []

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Try the family restaurant."))]
    mock_response.usage = MagicMock(total_tokens=20)

    async def fake_create(**kwargs):
        captured_messages.extend(kwargs["messages"])
        return mock_response

    with patch("app.services.chat_service._client") as mock_client:
        mock_client.chat.completions.create = fake_create
        from app.services import chat_service
        await chat_service.chat(
            conversation_id=conv_id,
            user_message="What activities do you recommend?",
            guest_context=ctx,
        )

    system_content = captured_messages[0]["content"]
    assert "Family" in system_content
    assert "5, 8" in system_content
    assert "Porto Elounda" in system_content


# ---------------------------------------------------------------------------
# 6. internal fields not exposed in context block
# ---------------------------------------------------------------------------


def test_context_block_does_not_expose_internal_names():
    ctx = GuestContext(property="porto_elounda", guest_type="vip")
    block = format_context_block(ctx)
    assert "GuestContext" not in block
    assert "conversation_id" not in block
    assert "_context_store" not in block
    assert "porto_elounda" not in block          # raw internal key should be formatted
    assert "Porto Elounda" in block              # human-readable form expected
