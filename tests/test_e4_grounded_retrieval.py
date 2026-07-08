"""E4 offline tests — grounded retrieval integration and prompt grounding rules."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

from app.models.chat import GuestContext
from app.services.language_service import get_system_prompt
from app.services.retrieval_context import INTENT_TO_CATEGORY, detect_intent, build_enriched_query
from app.services import conversation_store


@pytest.fixture(autouse=True)
def _clean_stores():
    conversation_store._store.clear()
    conversation_store._context_store.clear()
    yield
    conversation_store._store.clear()
    conversation_store._context_store.clear()


# ---------------------------------------------------------------------------
# INTENT_TO_CATEGORY mapping correctness
# ---------------------------------------------------------------------------


def test_intent_to_category_restaurant():
    assert INTENT_TO_CATEGORY["restaurant"] == "restaurant"


def test_intent_to_category_bar():
    assert INTENT_TO_CATEGORY["bar"] == "bar"


def test_intent_to_category_spa():
    assert INTENT_TO_CATEGORY["spa"] == "spa"


def test_intent_to_category_transfer():
    assert INTENT_TO_CATEGORY["transfer"] == "transportation"


def test_intent_to_category_yacht():
    assert INTENT_TO_CATEGORY["yacht"] == "premium"


def test_intent_to_category_family():
    assert INTENT_TO_CATEGORY["family"] == "family"


def test_intent_to_category_golf():
    assert INTENT_TO_CATEGORY["golf"] == "sports"


# ---------------------------------------------------------------------------
# retrieve_context receives intent from the chat route (route-level simulation)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_retrieve_context_called_with_intent_from_route():
    """The chat route must pass intent= to retrieve_context."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    captured: dict = {}

    original_retrieve = __import__(
        "app.services.rag_service", fromlist=["retrieve_context"]
    ).retrieve_context

    def fake_retrieve(query, property_id=None, language=None, top_k=None, intent=None):
        captured["intent"] = intent
        captured["query"] = query
        return []

    with patch("app.services.rag_service.retrieve_context", side_effect=fake_retrieve):
        with patch("app.services.chat_service._client") as mock_client:
            mock_resp = MagicMock()
            mock_resp.choices = [MagicMock(message=MagicMock(content="Here is a suggestion."))]
            mock_resp.usage = MagicMock(total_tokens=10)
            mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                await client.post(
                    "/api/v1/chat",
                    json={"message": "Where should we have dinner tonight?"},
                )

    assert captured.get("intent") == "restaurant"


@pytest.mark.asyncio
async def test_retrieve_context_called_with_enriched_query():
    """The enriched query (not raw message) must be passed to retrieve_context."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    captured: dict = {}

    def fake_retrieve(query, property_id=None, language=None, top_k=None, intent=None):
        captured["query"] = query
        return []

    with patch("app.services.rag_service.retrieve_context", side_effect=fake_retrieve):
        with patch("app.services.chat_service._client") as mock_client:
            mock_resp = MagicMock()
            mock_resp.choices = [MagicMock(message=MagicMock(content="OK"))]
            mock_resp.usage = MagicMock(total_tokens=5)
            mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                # First message seeds guest context
                await client.post(
                    "/api/v1/chat",
                    json={
                        "message": "We are a family staying at Porto Elounda.",
                        "conversation_id": "e4-enrich-test",
                    },
                )
                # Second message — should use enriched query with property + family
                await client.post(
                    "/api/v1/chat",
                    json={
                        "message": "Where should we have dinner tonight?",
                        "conversation_id": "e4-enrich-test",
                    },
                )

    # The last captured query should contain the enriched context prefix
    assert "Guest context:" in captured["query"]
    assert "Porto Elounda" in captured["query"]


# ---------------------------------------------------------------------------
# rag_service fallback: category filter returns 0, retry without filter
# ---------------------------------------------------------------------------


def test_rag_fallback_when_category_filter_returns_empty():
    """If category-filtered query returns nothing, _query is called again without category."""
    from app.services import rag_service

    mock_collection = MagicMock()
    mock_collection.count.return_value = 10

    call_count = {"n": 0}

    def fake_query(**kwargs):
        call_count["n"] += 1
        where = kwargs.get("where")
        # First call (with category filter) returns empty; second (no filter) returns a doc
        if where and "category" in str(where):
            return {"documents": [[]], "distances": [[]]}
        return {"documents": [["A real restaurant doc"]], "distances": [[0.2]]}

    mock_collection.query = fake_query

    with patch.object(rag_service, "_get_collection", return_value=mock_collection):
        result = rag_service.retrieve_context(
            query="dinner", intent="restaurant"
        )

    assert call_count["n"] == 2
    assert result == ["A real restaurant doc"]


def test_rag_no_fallback_when_category_filter_returns_results():
    """If category-filtered query returns results, _query is NOT called a second time."""
    from app.services import rag_service

    mock_collection = MagicMock()
    mock_collection.count.return_value = 10

    call_count = {"n": 0}

    def fake_query(**kwargs):
        call_count["n"] += 1
        return {"documents": [["Cosmos Restaurant"]], "distances": [[0.15]]}

    mock_collection.query = fake_query

    with patch.object(rag_service, "_get_collection", return_value=mock_collection):
        result = rag_service.retrieve_context(
            query="dinner", intent="restaurant"
        )

    assert call_count["n"] == 1
    assert result == ["Cosmos Restaurant"]


def test_rag_no_fallback_when_no_intent():
    """Without intent, only one query is issued (no category filter, no fallback logic)."""
    from app.services import rag_service

    mock_collection = MagicMock()
    mock_collection.count.return_value = 5

    call_count = {"n": 0}

    def fake_query(**kwargs):
        call_count["n"] += 1
        return {"documents": [[]], "distances": [[]]}

    mock_collection.query = fake_query

    with patch.object(rag_service, "_get_collection", return_value=mock_collection):
        rag_service.retrieve_context(query="hello", intent=None)

    assert call_count["n"] == 1


# ---------------------------------------------------------------------------
# Grounding rules in system prompts
# ---------------------------------------------------------------------------


def test_grounding_rules_in_english_prompt():
    prompt = get_system_prompt("en")
    assert "never invent" in prompt.lower()


def test_grounding_rules_english_lists_restaurant_names():
    prompt = get_system_prompt("en")
    assert "restaurant names" in prompt.lower()


def test_grounding_rules_english_lists_bar_names():
    prompt = get_system_prompt("en")
    assert "bar names" in prompt.lower()


def test_grounding_rules_english_mentions_concierge():
    prompt = get_system_prompt("en")
    assert "concierge" in prompt.lower()


def test_grounding_rules_in_greek_prompt():
    prompt = get_system_prompt("el")
    # Greek grounding rule: "Μην εφευρίσκεις"
    assert "μην εφευρίσκεις" in prompt.lower()


def test_grounding_rules_greek_mentions_concierge():
    prompt = get_system_prompt("el")
    assert "concierge" in prompt.lower()


# ---------------------------------------------------------------------------
# Stabilization fix — opening hours / seasonal variation rules
# ---------------------------------------------------------------------------


def test_english_prompt_never_infer_opening_hours():
    prompt = get_system_prompt("en")
    assert "never infer or invent" in prompt.lower()
    assert "opening hours" in prompt.lower()


def test_english_prompt_covers_all_forbidden_details():
    prompt = get_system_prompt("en").lower()
    for term in ("prices", "availability", "reservation status",
                 "dress codes", "schedules", "booking confirmations"):
        assert term in prompt, f"Missing forbidden detail in EN prompt: {term}"


def test_english_prompt_seasonal_variation_guidance():
    prompt = get_system_prompt("en").lower()
    assert "vary by season" in prompt
    assert "contacting concierge" in prompt or "contact" in prompt


def test_english_prompt_seasonal_fallback_phrase():
    prompt = get_system_prompt("en")
    assert "Current operating hours may vary by season" in prompt


def test_greek_prompt_never_infer_opening_hours():
    prompt = get_system_prompt("el")
    # Greek: "Μην συμπεραίνεις ή εφευρίσκεις ωράρια λειτουργίας"
    assert "ωράρια λειτουργίας" in prompt


def test_greek_prompt_seasonal_variation_guidance():
    prompt = get_system_prompt("el")
    assert "εποχή" in prompt


def test_greek_prompt_concierge_recommendation():
    prompt = get_system_prompt("el")
    assert "Concierge" in prompt
