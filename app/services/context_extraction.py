"""Rule-based guest context extraction. No LLM calls, no NLP libraries."""

import re

from app.models.chat import GuestContext

# ---------------------------------------------------------------------------
# Keyword tables
# ---------------------------------------------------------------------------

_PROPERTY_MAP = {
    "porto elounda": "porto_elounda",
    "elounda mare": "elounda_mare",
    "elounda peninsula": "elounda_peninsula",
}

# Checked in order — honeymoon/proposal before couple so they win
_GUEST_TYPE_RULES: list[tuple[list[str], str]] = [
    (["honeymoon", "proposal", "propose"], "honeymoon"),
    (["family", "children", "kids", "child"], "family"),
    (["couple", "two of us", "just the two"], "couple"),
    (["vip", "butler", "suite", "villa"], "vip"),
]

_OCCASION_MAP = {
    "honeymoon": "honeymoon",
    "anniversary": "anniversary",
    "birthday": "birthday",
    "proposal": "proposal",
    "propose": "proposal",
}

_INTEREST_KEYWORDS = [
    "spa",
    "beach",
    "golf",
    "sushi",
    "italian food",
    "italian",
    "yacht",
    "transfer",
    "kids club",
    "wellness",
]

_DIETARY_KEYWORDS = [
    "vegetarian",
    "vegan",
    "gluten-free",
    "gluten free",
    "seafood",
    "kosher",
    "halal",
]

_MOBILITY_PHRASES = [
    "wheelchair",
    "mobility issue",
    "walking difficulty",
    "step-free access",
    "step-free",
    "step free",
]

# Detects sentences/clauses that contain age-context keywords.
# We then extract ALL 1-2 digit numbers from those clauses (clamped 1-17).
_AGE_CONTEXT_TRIGGER_RE = re.compile(
    r"(?:age[sd]?|year[s]?\s+old|children|kids?|child)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_context(message: str) -> GuestContext:
    """Return a GuestContext with whatever fields can be inferred from *message*.

    Unrecognised fields are left as None / empty list.
    """
    text = message.lower()

    return GuestContext(
        property=_extract_property(text),
        guest_type=_extract_guest_type(text),
        children_ages=_extract_children_ages(text),
        interests=_extract_list(text, _INTEREST_KEYWORDS),
        occasion=_extract_occasion(text),
        dietary_preferences=_extract_list(text, _DIETARY_KEYWORDS),
        mobility_needs=_extract_mobility(text),
    )


def merge_context(existing: GuestContext, new: GuestContext) -> GuestContext:
    """Merge *new* into *existing* and return the merged result.

    - Scalar fields: new value wins when not None; existing value kept otherwise.
    - List fields: union (order-preserving, no duplicates).
    """
    def _union(a: list, b: list) -> list:
        seen: set = set()
        result = []
        for item in a + b:
            key = item if not isinstance(item, str) else item.lower()
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result

    return GuestContext(
        property=new.property if new.property is not None else existing.property,
        guest_type=new.guest_type if new.guest_type is not None else existing.guest_type,
        children_ages=_union(existing.children_ages, new.children_ages),
        interests=_union(existing.interests, new.interests),
        occasion=new.occasion if new.occasion is not None else existing.occasion,
        preferred_language=(
            new.preferred_language
            if new.preferred_language is not None
            else existing.preferred_language
        ),
        dietary_preferences=_union(existing.dietary_preferences, new.dietary_preferences),
        mobility_needs=(
            new.mobility_needs
            if new.mobility_needs is not None
            else existing.mobility_needs
        ),
    )


def format_context_block(ctx: GuestContext) -> str | None:
    """Return a prompt-ready "Known Guest Context" block, or None if empty."""
    lines: list[str] = []

    if ctx.property:
        lines.append(f"Property: {ctx.property.replace('_', ' ').title()}")
    if ctx.guest_type:
        lines.append(f"Guest type: {ctx.guest_type.capitalize()}")
    if ctx.children_ages:
        ages = ", ".join(str(a) for a in ctx.children_ages)
        lines.append(f"Children ages: {ages}")
    if ctx.occasion:
        lines.append(f"Occasion: {ctx.occasion.capitalize()}")
    if ctx.interests:
        lines.append(f"Interests: {', '.join(ctx.interests)}")
    if ctx.dietary_preferences:
        lines.append(f"Dietary preferences: {', '.join(ctx.dietary_preferences)}")
    if ctx.mobility_needs:
        lines.append(f"Mobility needs: {ctx.mobility_needs}")
    if ctx.preferred_language:
        lines.append(f"Preferred language: {ctx.preferred_language}")

    if not lines:
        return None

    return "## Known Guest Context\n" + "\n".join(lines)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_property(text: str) -> str | None:
    for phrase, value in _PROPERTY_MAP.items():
        if phrase in text:
            return value
    return None


def _extract_guest_type(text: str) -> str | None:
    for keywords, guest_type in _GUEST_TYPE_RULES:
        if any(kw in text for kw in keywords):
            return guest_type
    return None


def _extract_children_ages(text: str) -> list[int]:
    # Split into sentences so we only pick up numbers near an age-context keyword.
    # A "sentence" here is any run of text between . ! ? or the whole string.
    sentences = re.split(r"[.!?]", text)
    seen: set[int] = set()
    result: list[int] = []
    for sentence in sentences:
        if not _AGE_CONTEXT_TRIGGER_RE.search(sentence):
            continue
        for m in re.finditer(r"\b(\d{1,2})\b", sentence):
            age = int(m.group(1))
            if 1 <= age <= 17 and age not in seen:
                seen.add(age)
                result.append(age)
    return result


def _extract_list(text: str, keywords: list[str]) -> list[str]:
    found: list[str] = []
    for kw in keywords:
        if kw in text and kw not in found:
            found.append(kw)
    return found


def _extract_occasion(text: str) -> str | None:
    for phrase, value in _OCCASION_MAP.items():
        if phrase in text:
            return value
    return None


def _extract_mobility(text: str) -> str | None:
    for phrase in _MOBILITY_PHRASES:
        if phrase in text:
            return phrase
    return None
