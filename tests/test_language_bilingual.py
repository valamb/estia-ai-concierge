"""
Bilingual language support tests — all offline, no API key required.
"""

import pytest
from app.services.language_service import (
    detect_language,
    get_system_prompt,
    extract_language_from_filename,
)


# --- detect_language ---

class TestDetectLanguage:
    def test_english_sentence(self):
        assert detect_language("What time does the spa open?") == "en"

    def test_greek_sentence(self):
        assert detect_language("Τι ώρα ανοίγει το spa;") == "el"

    def test_greek_with_latin_brand_names(self):
        # "Τι ώρα ανοίγει το Porto Elounda spa;" — still mostly Greek chars
        assert detect_language("Τι ώρα ανοίγει το Porto Elounda spa;") == "el"

    def test_english_with_greek_proper_noun(self):
        # "Book a table at Elounda" — almost no Greek chars
        assert detect_language("Book a table at Elounda restaurant please") == "en"

    def test_empty_string_returns_default(self):
        assert detect_language("") == "en"

    def test_numbers_only_returns_default(self):
        assert detect_language("12345") == "en"

    def test_mixed_heavy_greek_classified_greek(self):
        assert detect_language("Θέλω να κλείσω τραπέζι για απόψε") == "el"


# --- get_system_prompt ---

class TestGetSystemPrompt:
    def test_english_prompt_in_english(self):
        prompt = get_system_prompt("en")
        assert "ESTIA" in prompt
        assert "concierge" in prompt.lower()

    def test_greek_prompt_in_greek(self):
        prompt = get_system_prompt("el")
        assert "ESTIA" in prompt
        assert "Ελληνικά" in prompt or "ελληνικά" in prompt

    def test_unknown_language_falls_back_to_english(self):
        prompt = get_system_prompt("de")
        assert "ESTIA" in prompt

    def test_english_prompt_mentions_three_properties(self):
        prompt = get_system_prompt("en")
        assert "Porto Elounda" in prompt
        assert "Elounda Mare" in prompt
        assert "Elounda Peninsula" in prompt

    def test_greek_prompt_mentions_three_properties(self):
        prompt = get_system_prompt("el")
        assert "Porto Elounda" in prompt
        assert "Elounda Mare" in prompt
        assert "Elounda Peninsula" in prompt


# --- extract_language_from_filename ---

class TestExtractLanguageFromFilename:
    def test_greek_filename_suffix(self):
        assert extract_language_from_filename("spa_overview_el.md") == "el"

    def test_english_filename_no_suffix(self):
        assert extract_language_from_filename("spa_overview.md") == "en"

    def test_greek_txt_file(self):
        assert extract_language_from_filename("dining_overview_el.txt") == "el"

    def test_filename_with_el_not_at_end_is_english(self):
        # 'elounda_overview.md' contains 'el' but not as _el suffix
        assert extract_language_from_filename("elounda_overview.md") == "en"

    def test_uppercase_extension(self):
        assert extract_language_from_filename("overview_el.MD") == "el"
