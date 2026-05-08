"""
Unit tests for the text_utils module.
"""

import pytest
from utils.text_utils import (
    normalize_indic_text,
    clean_ocr_text,
    compute_text_length,
    is_meaningful_text,
    format_timestamp,
)


class TestNormalizeIndicText:
    """Tests for Unicode normalization of Indic text."""

    def test_basic_hindi(self):
        assert normalize_indic_text("  वो कहाँ गई थी  ") == "वो कहाँ गई थी"

    def test_collapses_whitespace(self):
        assert normalize_indic_text("वो   कहाँ\t\nगई") == "वो कहाँ गई"

    def test_removes_zero_width_joiners(self):
        text = "वो\u200cकहाँ\u200dगई"
        result = normalize_indic_text(text)
        assert "\u200c" not in result
        assert "\u200d" not in result

    def test_removes_invisible_chars(self):
        text = "\u200bवो\u200eकहाँ\ufeff"
        result = normalize_indic_text(text)
        assert "\u200b" not in result
        assert "\ufeff" not in result

    def test_empty_string(self):
        assert normalize_indic_text("") == ""

    def test_none_returns_empty(self):
        assert normalize_indic_text(None) == ""

    def test_kannada_text(self):
        text = " ಹೇಗಿದ್ದೀರಿ  "
        assert normalize_indic_text(text) == "ಹೇಗಿದ್ದೀರಿ"


class TestCleanOcrText:
    """Tests for OCR artefact removal."""

    def test_removes_pipes(self):
        assert "pipe" not in clean_ocr_text("|text|")
        assert clean_ocr_text("|वो कहाँ|") == "वो कहाँ"

    def test_removes_backslashes(self):
        assert "\\" not in clean_ocr_text("text\\here")

    def test_empty_string(self):
        assert clean_ocr_text("") == ""

    def test_normalises_after_cleaning(self):
        result = clean_ocr_text("  |वो  कहाँ|  ")
        assert result == "वो कहाँ"


class TestComputeTextLength:
    def test_ignores_spaces(self):
        assert compute_text_length("a b c") == 3

    def test_empty(self):
        assert compute_text_length("") == 0

    def test_hindi(self):
        assert compute_text_length("वो कहाँ") == 6


class TestIsMeaningfulText:
    def test_short_text_rejected(self):
        assert not is_meaningful_text("a")

    def test_meaningful_text_accepted(self):
        assert is_meaningful_text("वो कहाँ")

    def test_empty_rejected(self):
        assert not is_meaningful_text("")

    def test_custom_min_length(self):
        assert is_meaningful_text("ab", min_length=2)
        assert not is_meaningful_text("a", min_length=2)


class TestFormatTimestamp:
    def test_basic(self):
        assert format_timestamp(0) == "00:00:00.000"

    def test_minutes(self):
        result = format_timestamp(125.4)
        assert result == "00:02:05.400"

    def test_hours(self):
        result = format_timestamp(3661.5)
        assert result == "01:01:01.500"
