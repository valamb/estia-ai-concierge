"""E2/E3 offline tests — retrieval query enrichment and intent detection."""

from app.models.chat import GuestContext
from app.services.retrieval_context import build_enriched_query, detect_intent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MSG = "Where should we have dinner tonight?"


# ---------------------------------------------------------------------------
# Property enrichment
# ---------------------------------------------------------------------------


def test_enriched_query_includes_porto_elounda():
    ctx = GuestContext(property="porto_elounda")
    result = build_enriched_query(_MSG, ctx)
    assert "Porto Elounda" in result


def test_enriched_query_includes_elounda_mare():
    ctx = GuestContext(property="elounda_mare")
    result = build_enriched_query(_MSG, ctx)
    assert "Elounda Mare" in result


def test_enriched_query_includes_elounda_peninsula():
    ctx = GuestContext(property="elounda_peninsula")
    result = build_enriched_query(_MSG, ctx)
    assert "Elounda Peninsula" in result


def test_enriched_query_property_is_human_readable():
    ctx = GuestContext(property="porto_elounda")
    result = build_enriched_query(_MSG, ctx)
    # Internal slug must not appear raw
    assert "porto_elounda" not in result
    assert "Porto Elounda" in result


# ---------------------------------------------------------------------------
# Guest type enrichment
# ---------------------------------------------------------------------------


def test_enriched_query_includes_family_context():
    ctx = GuestContext(guest_type="family")
    result = build_enriched_query(_MSG, ctx)
    assert "family" in result


def test_enriched_query_includes_honeymoon_context():
    ctx = GuestContext(guest_type="honeymoon")
    result = build_enriched_query(_MSG, ctx)
    assert "honeymoon" in result


def test_enriched_query_includes_vip_context():
    ctx = GuestContext(guest_type="vip")
    result = build_enriched_query(_MSG, ctx)
    assert "vip" in result


# ---------------------------------------------------------------------------
# Children ages enrichment
# ---------------------------------------------------------------------------


def test_enriched_query_includes_children_ages():
    ctx = GuestContext(children_ages=[5, 8])
    result = build_enriched_query(_MSG, ctx)
    assert "5" in result
    assert "8" in result


def test_enriched_query_children_ages_label():
    ctx = GuestContext(children_ages=[6])
    result = build_enriched_query(_MSG, ctx)
    assert "children aged" in result


# ---------------------------------------------------------------------------
# Occasion enrichment
# ---------------------------------------------------------------------------


def test_enriched_query_includes_occasion():
    ctx = GuestContext(occasion="anniversary")
    result = build_enriched_query(_MSG, ctx)
    assert "anniversary" in result


# ---------------------------------------------------------------------------
# Interests enrichment
# ---------------------------------------------------------------------------


def test_enriched_query_includes_interests():
    ctx = GuestContext(interests=["spa", "beach", "golf"])
    result = build_enriched_query(_MSG, ctx)
    assert "spa" in result
    assert "beach" in result
    assert "golf" in result


def test_enriched_query_interests_capped_at_three():
    ctx = GuestContext(interests=["spa", "beach", "golf", "yacht", "wellness"])
    result = build_enriched_query(_MSG, ctx)
    # First three must appear, extras may or may not — cap is applied
    assert "spa" in result
    assert "beach" in result
    assert "golf" in result
    # The fourth and fifth are beyond the cap
    assert result.count("yacht") + result.count("wellness") == 0


# ---------------------------------------------------------------------------
# Empty / None context — raw message returned unchanged
# ---------------------------------------------------------------------------


def test_empty_context_returns_raw_message():
    ctx = GuestContext()
    result = build_enriched_query(_MSG, ctx)
    assert result == _MSG


def test_none_context_returns_raw_message():
    result = build_enriched_query(_MSG, None)
    assert result == _MSG


# ---------------------------------------------------------------------------
# Prefix structure
# ---------------------------------------------------------------------------


def test_enriched_query_contains_prefix_label():
    ctx = GuestContext(property="porto_elounda")
    result = build_enriched_query(_MSG, ctx)
    assert result.startswith("Guest context:")


def test_enriched_query_contains_user_asks_separator():
    ctx = GuestContext(property="porto_elounda")
    result = build_enriched_query(_MSG, ctx)
    assert "User asks:" in result


def test_enriched_query_ends_with_original_message():
    ctx = GuestContext(property="porto_elounda")
    result = build_enriched_query(_MSG, ctx)
    assert result.endswith(_MSG)


# ---------------------------------------------------------------------------
# Full combined context
# ---------------------------------------------------------------------------


def test_enriched_query_full_context():
    ctx = GuestContext(
        property="porto_elounda",
        guest_type="family",
        children_ages=[5, 8],
        occasion="birthday",
        interests=["spa", "beach"],
    )
    result = build_enriched_query(_MSG, ctx)
    assert "Porto Elounda" in result
    assert "family" in result
    assert "5" in result
    assert "8" in result
    assert "birthday" in result
    assert "spa" in result
    assert "beach" in result
    assert _MSG in result


# ---------------------------------------------------------------------------
# E3 — Intent detection
# ---------------------------------------------------------------------------


def test_intent_restaurant():
    assert detect_intent("Where should we have dinner tonight?") == "restaurant"


def test_intent_restaurant_via_lunch():
    assert detect_intent("Can you recommend somewhere for lunch?") == "restaurant"


def test_intent_restaurant_via_food():
    assert detect_intent("I am looking for good food options.") == "restaurant"


def test_intent_bar():
    assert detect_intent("Where can I get a cocktail?") == "bar"


def test_intent_bar_via_drinks():
    assert detect_intent("We would love some drinks by the pool.") == "bar"


def test_intent_bar_via_wine():
    assert detect_intent("Is there a good wine selection available?") == "bar"


def test_intent_spa():
    assert detect_intent("I would like to book a massage.") == "spa"


def test_intent_spa_via_treatment():
    assert detect_intent("What spa treatments are available?") == "spa"


def test_intent_spa_via_wellness():
    assert detect_intent("We are interested in wellness activities.") == "spa"


def test_intent_transfer():
    assert detect_intent("I need a car to the airport.") == "transfer"


def test_intent_transfer_via_taxi():
    assert detect_intent("Can you arrange a taxi for us?") == "transfer"


def test_intent_transfer_via_chauffeur():
    assert detect_intent("We would like a chauffeur service.") == "transfer"


def test_intent_yacht():
    assert detect_intent("Can we book a yacht charter?") == "yacht"


def test_intent_yacht_via_cruise():
    assert detect_intent("We would love a sunset cruise.") == "yacht"


def test_intent_family():
    assert detect_intent("What activities are there for kids?") == "family"


def test_intent_family_via_children():
    assert detect_intent("We have two children and need activities.") == "family"


def test_intent_golf():
    assert detect_intent("Are golf lessons available?") == "golf"


def test_intent_golf_via_tee():
    assert detect_intent("I would like to book a tee time.") == "golf"


def test_intent_none_on_generic_message():
    assert detect_intent("Thank you, that was very helpful.") is None


def test_intent_none_on_greeting():
    assert detect_intent("Hello, good morning.") is None


def test_intent_ambiguous_family_dinner_resolves_to_restaurant():
    # "restaurant" has higher priority than "family"
    assert detect_intent("We are looking for a family dinner option.") == "restaurant"


def test_intent_case_insensitive_upper():
    assert detect_intent("WHERE CAN I GET A MASSAGE?") == "spa"


def test_intent_case_insensitive_mixed():
    assert detect_intent("Can You Recommend A Restaurant?") == "restaurant"
