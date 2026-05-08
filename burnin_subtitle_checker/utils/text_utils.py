"""
Text normalization and cleaning utilities for Indic scripts.

Handles Unicode normalization for Devanagari (Hindi) and Kannada,
plus common OCR artefact cleanup.
"""

import re
import unicodedata
from typing import Optional


def normalize_indic_text(text: str) -> str:
    """
    Normalize Indic Unicode text for consistent comparison.

    Applies:
        - NFC Unicode normalization (canonical decomposition + composition)
        - Whitespace collapsing
        - Removal of zero-width joiners / non-joiners
        - Strip leading/trailing whitespace

    Args:
        text: Raw text string (Hindi / Kannada / mixed).

    Returns:
        Normalized text suitable for fuzzy matching.
    """
    if not text:
        return ""

    # Unicode NFC normalization — combines decomposed characters
    text = unicodedata.normalize("NFC", text)

    # Remove zero-width joiners and non-joiners (U+200C, U+200D)
    text = text.replace("\u200c", "").replace("\u200d", "")

    # Remove other invisible formatting characters
    text = re.sub(r"[\u200b\u200e\u200f\ufeff]", "", text)

    # Collapse multiple spaces / tabs / newlines into single space
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def clean_ocr_text(text: str) -> str:
    """
    Clean common OCR artefacts from extracted subtitle text.

    Handles:
        - Stray punctuation introduced by OCR
        - Pipe characters misread from frame borders
        - Excessive special characters

    Args:
        text: Raw OCR output string.

    Returns:
        Cleaned text string.
    """
    if not text:
        return ""

    # Remove pipe characters (common OCR artefact from frame edges)
    text = text.replace("|", "")

    # Remove stray backslashes
    text = text.replace("\\", "")

    # Remove isolated ASCII punctuation that is likely OCR noise.
    # Preserve Indic combining marks (e.g. chandrabindu ँ).
    text = re.sub(r"(?<![a-zA-Z0-9\u0900-\u0DFF])[^\w\s\u0900-\u0DFF](?![a-zA-Z0-9\u0900-\u0DFF])", "", text)

    # Normalize the cleaned text
    text = normalize_indic_text(text)

    return text


def compute_text_length(text: str) -> int:
    """
    Compute the effective character length, ignoring whitespace.

    Args:
        text: Input text.

    Returns:
        Character count excluding spaces.
    """
    return len(text.replace(" ", ""))


def is_meaningful_text(text: str, min_length: int = 2) -> bool:
    """
    Check whether text is meaningful enough to compare.

    Filters out single-character OCR noise and empty strings.

    Args:
        text: Input text.
        min_length: Minimum character length (excluding spaces).

    Returns:
        True if text meets minimum length requirement.
    """
    return compute_text_length(text) >= min_length


def format_timestamp(seconds: float) -> str:
    """
    Format a floating-point timestamp into HH:MM:SS.mmm display string.

    Args:
        seconds: Time in seconds (e.g., 125.4).

    Returns:
        Formatted string like '00:02:05.400'.
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
