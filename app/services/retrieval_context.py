"""Retrieval utilities: query enrichment and intent detection."""

import re

from app.models.chat import GuestContext

# Human-readable property labels used in enriched queries
_PROPERTY_LABELS: dict[str, str] = {
    "porto_elounda": "Porto Elounda",
    "elounda_mare": "Elounda Mare",
    "elounda_peninsula": "Elounda Peninsula",
}


# Intent → ChromaDB category mapping (used by rag_service in E4)
INTENT_TO_CATEGORY: dict[str, str] = {
    "restaurant": "restaurant",
    "bar":        "bar",
    "spa":        "spa",
    "transfer":   "transportation",
    "yacht":      "premium",
    "family":     "family",
    "golf":       "sports",
}

# Checked in priority order — first match wins.
# restaurant before family so "family dinner" resolves to restaurant.
_INTENT_RULES: list[tuple[str, list[str]]] = [
    ("restaurant", ["dinner", "lunch", "breakfast", "eat", "food", "restaurant",
                    "dining", "cuisine", "meal", "menu"]),
    ("bar",        ["bar", "cocktail", "drink", "drinks", "wine", "beer",
                    "sundowner", "aperitif"]),
    ("spa",        ["spa", "massage", "treatment", "wellness", "sauna",
                    "steam", "facial", "thermal", "hammam"]),
    ("transfer",   ["transfer", "taxi", "car", "airport", "transport",
                    "shuttle", "driver", "chauffeur"]),
    ("yacht",      ["yacht", "boat", "sail", "charter", "cruise", "sailing"]),
    ("family",     ["kids", "children", "child", "kids club", "babysit",
                    "playground", "family"]),
    ("golf",       ["golf", "tee", "fairway", "driving range", "golf lesson"]),
]


def detect_intent(message: str) -> str | None:
    """Return the first matching intent for *message*, or None.

    Matching is case-insensitive and word-boundary aware so short keywords
    like "eat" do not fire inside words like "treatments".
    Priority order is fixed (see _INTENT_RULES) so that ambiguous messages
    like "family dinner" resolve to the higher-priority intent ("restaurant").
    """
    lowered = message.lower()
    for intent, keywords in _INTENT_RULES:
        for kw in keywords:
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, lowered):
                return intent
    return None


def build_enriched_query(user_message: str, guest_context: GuestContext | None) -> str:
    """Return an enriched query string for ChromaDB retrieval.

    When *guest_context* contains at least one populated field, a structured
    prefix is prepended so the embedding search is biased toward relevant
    property/guest-type content.  When context is empty or None the original
    message is returned unchanged, preserving existing behaviour.
    """
    if not guest_context:
        return user_message

    parts: list[str] = []

    if guest_context.property:
        label = _PROPERTY_LABELS.get(guest_context.property, guest_context.property)
        parts.append(f"property {label}")

    if guest_context.guest_type:
        parts.append(guest_context.guest_type)

    if guest_context.children_ages:
        ages = " and ".join(str(a) for a in guest_context.children_ages)
        parts.append(f"children aged {ages}")

    if guest_context.occasion:
        parts.append(guest_context.occasion)

    if guest_context.interests:
        parts.append(", ".join(guest_context.interests[:3]))

    if not parts:
        return user_message

    prefix = "Guest context: " + ", ".join(parts) + "."
    return f"{prefix} User asks: {user_message}"
