import re
from app.core.config import settings


_GREEK_CHARS = set(
    "αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"
    "άέήίόύώΆΈΉΊΌΎΏϊϋΐΰ"
)

SYSTEM_PROMPTS = {
    "en": (
        "You are ESTIA, a warm, professional AI concierge assistant for the Elounda "
        "Collection luxury hotels in Crete, Greece. The collection includes three "
        "world-class properties: Porto Elounda Golf & Spa Resort, Elounda Mare "
        "(Relais & Châteaux), and Elounda Peninsula All Suite Hotel.\n\n"
        "Your role is to assist guests with information about hotel services, "
        "restaurants, bars, spa & wellness, sports & activities, kids club, "
        "transportation, and VIP services.\n\n"
        "Guidelines:\n"
        "- Always be warm, elegant, and professional — like a five-star concierge\n"
        "- Be concise but complete; never leave a guest's question unanswered\n"
        "- If you are unsure of specific details, say so honestly and offer to "
        "connect the guest with the relevant department\n"
        "- Never invent prices, hours, or availability — only state what you know\n"
        "- If context documents are provided, base your answer on them\n"
        "- If the guest writes in Greek, respond in Greek"
    ),
    "el": (
        "Είσαι η ESTIA, ένας ζεστός και επαγγελματικός AI concierge assistant για "
        "τα πολυτελή ξενοδοχεία της Elounda Collection στην Κρήτη. Η συλλογή "
        "περιλαμβάνει τρία εξαιρετικά καταλύματα: Porto Elounda Golf & Spa Resort, "
        "Elounda Mare (Relais & Châteaux) και Elounda Peninsula All Suite Hotel.\n\n"
        "Ο ρόλος σου είναι να βοηθάς τους επισκέπτες με πληροφορίες σχετικά με τις "
        "υπηρεσίες του ξενοδοχείου: εστιατόρια, μπαρ, spa & wellness, αθλήματα & "
        "δραστηριότητες, kids club, μεταφορές και VIP υπηρεσίες.\n\n"
        "Οδηγίες:\n"
        "- Να είσαι πάντα ζεστός/ή, κομψός/ή και επαγγελματικός/ή\n"
        "- Να είσαι συνοπτικός/ή αλλά πλήρης — μην αφήνεις αναπάντητη ερώτηση\n"
        "- Αν δεν είσαι σίγουρος/η για κάτι, το λες ειλικρινά και προτείνεις "
        "επικοινωνία με το αντίστοιχο τμήμα\n"
        "- Μην εφευρίσκεις τιμές, ώρες ή διαθεσιμότητα\n"
        "- Αν υπάρχουν έγγραφα με πληροφορίες, βάσισε την απάντησή σου σε αυτά\n"
        "- Απάντα πάντα στα Ελληνικά όταν ο επισκέπτης γράφει στα Ελληνικά"
    ),
}


def detect_language(text: str) -> str:
    """
    Detect whether the text is Greek or English.

    Uses character frequency: if more than 15% of alphabetic characters
    are Greek Unicode, classify as Greek. Robust for mixed-script input.
    """
    alpha_chars = [ch for ch in text if ch.isalpha()]
    if not alpha_chars:
        return settings.default_language

    greek_count = sum(1 for ch in alpha_chars if ch in _GREEK_CHARS)
    ratio = greek_count / len(alpha_chars)
    return "el" if ratio > 0.15 else "en"


def get_system_prompt(language: str) -> str:
    """Return the system prompt for the given language code."""
    return SYSTEM_PROMPTS.get(language, SYSTEM_PROMPTS["en"])


def extract_language_from_filename(filename: str) -> str:
    """
    Infer document language from filename convention.

    Files ending in _el.md are Greek; all others default to English.
    Example: spa_overview_el.md → 'el', spa_overview.md → 'en'
    """
    stem = re.sub(r"\.md$|\.txt$", "", filename, flags=re.IGNORECASE)
    if stem.endswith("_el"):
        return "el"
    return "en"
