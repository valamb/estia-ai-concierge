"""Unit tests for rule-based guest context extraction. Fully offline."""

import pytest

from app.models.chat import GuestContext
from app.services.context_extraction import extract_context, merge_context


# ---------------------------------------------------------------------------
# 1. Property extraction
# ---------------------------------------------------------------------------


def test_extract_property_porto_elounda():
    ctx = extract_context("We are staying at Porto Elounda this week.")
    assert ctx.property == "porto_elounda"


def test_extract_property_elounda_mare():
    ctx = extract_context("We checked in to Elounda Mare yesterday.")
    assert ctx.property == "elounda_mare"


def test_extract_property_elounda_peninsula():
    ctx = extract_context("Our room at Elounda Peninsula is wonderful.")
    assert ctx.property == "elounda_peninsula"


def test_extract_property_none_when_no_match():
    ctx = extract_context("What time does the spa open?")
    assert ctx.property is None


# ---------------------------------------------------------------------------
# 2. Family detection
# ---------------------------------------------------------------------------


def test_extract_guest_type_family_keyword():
    ctx = extract_context("We are a family of four.")
    assert ctx.guest_type == "family"


def test_extract_guest_type_family_via_kids():
    ctx = extract_context("We have two kids with us.")
    assert ctx.guest_type == "family"


def test_extract_guest_type_family_via_children():
    ctx = extract_context("We are travelling with our children.")
    assert ctx.guest_type == "family"


# ---------------------------------------------------------------------------
# 3. Children age extraction
# ---------------------------------------------------------------------------


def test_extract_children_ages_two_children():
    ctx = extract_context("We have two children aged 5 and 8.")
    assert set(ctx.children_ages) == {5, 8}


def test_extract_children_ages_kids_phrasing():
    ctx = extract_context("Our kids are 6 and 10 years old.")
    assert set(ctx.children_ages) == {6, 10}


def test_extract_children_ages_no_false_positive_room_number():
    ctx = extract_context("We are in room 204 and would like a table for 4.")
    assert ctx.children_ages == []


def test_extract_children_ages_clamped_above_17():
    ctx = extract_context("My child is 20 years old.")
    assert ctx.children_ages == []


# ---------------------------------------------------------------------------
# 4. Honeymoon detection
# ---------------------------------------------------------------------------


def test_extract_guest_type_honeymoon():
    ctx = extract_context("This is our honeymoon trip.")
    assert ctx.guest_type == "honeymoon"
    assert ctx.occasion == "honeymoon"


def test_extract_occasion_proposal():
    ctx = extract_context("I am planning to propose during our stay.")
    assert ctx.occasion == "proposal"


def test_extract_occasion_anniversary():
    ctx = extract_context("We are celebrating our anniversary here.")
    assert ctx.occasion == "anniversary"


def test_extract_occasion_birthday():
    ctx = extract_context("It is my wife's birthday tomorrow.")
    assert ctx.occasion == "birthday"


# ---------------------------------------------------------------------------
# 5. VIP / luxury detection
# ---------------------------------------------------------------------------


def test_extract_guest_type_vip():
    ctx = extract_context("We have a vip arrangement with the resort.")
    assert ctx.guest_type == "vip"


def test_extract_guest_type_butler():
    ctx = extract_context("Can the butler bring breakfast to our villa?")
    assert ctx.guest_type == "vip"


# ---------------------------------------------------------------------------
# 6. Interest extraction
# ---------------------------------------------------------------------------


def test_extract_interests_spa_and_beach():
    ctx = extract_context("We love spa treatments and spending time at the beach.")
    assert "spa" in ctx.interests
    assert "beach" in ctx.interests


def test_extract_interests_golf():
    ctx = extract_context("My husband is interested in golf lessons.")
    assert "golf" in ctx.interests


def test_extract_interests_yacht():
    ctx = extract_context("We would love a yacht experience.")
    assert "yacht" in ctx.interests


def test_extract_interests_wellness():
    ctx = extract_context("Wellness is very important to us.")
    assert "wellness" in ctx.interests


# ---------------------------------------------------------------------------
# 7. Dietary preference extraction
# ---------------------------------------------------------------------------


def test_extract_dietary_vegetarian():
    ctx = extract_context("I am vegetarian.")
    assert "vegetarian" in ctx.dietary_preferences


def test_extract_dietary_vegan_and_vegetarian():
    ctx = extract_context("I am vegetarian and my partner is vegan.")
    assert "vegetarian" in ctx.dietary_preferences
    assert "vegan" in ctx.dietary_preferences


def test_extract_dietary_gluten_free():
    ctx = extract_context("I require a gluten-free menu.")
    assert "gluten-free" in ctx.dietary_preferences


def test_extract_dietary_halal():
    ctx = extract_context("We need halal food options.")
    assert "halal" in ctx.dietary_preferences


# ---------------------------------------------------------------------------
# 8. Mobility needs extraction
# ---------------------------------------------------------------------------


def test_extract_mobility_wheelchair():
    ctx = extract_context("My mother uses a wheelchair.")
    assert ctx.mobility_needs == "wheelchair"


def test_extract_mobility_step_free():
    ctx = extract_context("We need step-free access throughout the hotel.")
    assert ctx.mobility_needs == "step-free access"


def test_extract_mobility_none_when_not_mentioned():
    ctx = extract_context("Can you recommend a restaurant?")
    assert ctx.mobility_needs is None


# ---------------------------------------------------------------------------
# 9. Context merging
# ---------------------------------------------------------------------------


def test_merge_adds_new_scalar_field():
    existing = GuestContext(property="porto_elounda")
    new = GuestContext(guest_type="family")
    merged = merge_context(existing, new)
    assert merged.property == "porto_elounda"
    assert merged.guest_type == "family"


def test_merge_new_scalar_overwrites_existing():
    existing = GuestContext(property="porto_elounda")
    new = GuestContext(property="elounda_peninsula")
    merged = merge_context(existing, new)
    assert merged.property == "elounda_peninsula"


def test_merge_existing_scalar_kept_when_new_is_none():
    existing = GuestContext(property="elounda_mare")
    new = GuestContext(property=None)
    merged = merge_context(existing, new)
    assert merged.property == "elounda_mare"


def test_merge_list_fields_union():
    existing = GuestContext(interests=["spa"])
    new = GuestContext(interests=["beach", "golf"])
    merged = merge_context(existing, new)
    assert set(merged.interests) == {"spa", "beach", "golf"}


def test_merge_list_no_duplicates():
    existing = GuestContext(interests=["spa", "beach"])
    new = GuestContext(interests=["beach", "wellness"])
    merged = merge_context(existing, new)
    assert merged.interests.count("beach") == 1


def test_merge_children_ages_combined():
    existing = GuestContext(children_ages=[5])
    new = GuestContext(children_ages=[8])
    merged = merge_context(existing, new)
    assert set(merged.children_ages) == {5, 8}


def test_merge_empty_context_is_safe():
    existing = GuestContext()
    new = GuestContext(property="porto_elounda", guest_type="family")
    merged = merge_context(existing, new)
    assert merged.property == "porto_elounda"
    assert merged.guest_type == "family"
    assert merged.children_ages == []


# ---------------------------------------------------------------------------
# 10. Context persistence across two messages (same conversation_id)
# ---------------------------------------------------------------------------


def test_context_persists_across_messages():
    """Simulate two sequential messages from the same conversation."""
    msg1 = "We are a family at Porto Elounda with children aged 5 and 8."
    msg2 = "Where should we have dinner tonight?"

    ctx_after_msg1 = extract_context(msg1)
    assert ctx_after_msg1.property == "porto_elounda"
    assert ctx_after_msg1.guest_type == "family"
    assert set(ctx_after_msg1.children_ages) == {5, 8}

    ctx_after_msg2 = extract_context(msg2)
    # msg2 contains no new context — all fields should be None/empty
    assert ctx_after_msg2.property is None
    assert ctx_after_msg2.guest_type is None
    assert ctx_after_msg2.children_ages == []

    # Merging simulates what conversation_store will do across messages
    merged = merge_context(ctx_after_msg1, ctx_after_msg2)
    assert merged.property == "porto_elounda"
    assert merged.guest_type == "family"
    assert set(merged.children_ages) == {5, 8}
