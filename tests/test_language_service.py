import pytest
from app.services.language_service import detect_language, get_system_prompt


def test_detects_english():
    assert detect_language("What time does the spa open?") == "en"


def test_detects_greek():
    assert detect_language("Τι ώρα ανοίγει το spa;") == "el"


def test_detects_english_for_empty():
    assert detect_language("") == "en"


def test_system_prompt_english_contains_estia():
    prompt = get_system_prompt("en")
    assert "ESTIA" in prompt


def test_system_prompt_greek_contains_estia():
    prompt = get_system_prompt("el")
    assert "ESTIA" in prompt


def test_system_prompt_unknown_language_falls_back_to_english():
    prompt = get_system_prompt("fr")
    assert "ESTIA" in prompt
    assert "concierge" in prompt.lower()
