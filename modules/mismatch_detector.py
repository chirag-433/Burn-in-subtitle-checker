"""
Module 3 — Mismatch Detection.

Compares Whisper transcription against OCR-extracted subtitle text
using RapidFuzz for fuzzy matching.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from rapidfuzz import fuzz

from utils.text_utils import format_timestamp, is_meaningful_text, normalize_indic_text

logger = logging.getLogger(__name__)

MismatchResult = Dict[str, Any]
STATUS_MATCH = "MATCH"
STATUS_REVIEW = "REVIEW"
STATUS_MISSING = "MISSING"


def detect_mismatches(
    transcript_segments: List[Dict[str, Any]],
    subtitle_segments: List[Dict[str, Any]],
    threshold: float = 75.0,
    output_json: Optional[str] = None,
) -> List[MismatchResult]:
    """Compare audio transcript with OCR subtitle text and score similarity."""
    logger.info("Detecting mismatches — %d segments, threshold=%.1f", len(transcript_segments), threshold)
    results: List[MismatchResult] = []

    for t_seg, s_seg in zip(transcript_segments, subtitle_segments):
        audio_text = normalize_indic_text(t_seg.get("text", ""))
        sub_text = normalize_indic_text(s_seg.get("subtitle_text", ""))
        timestamp = s_seg.get("timestamp", t_seg.get("start", 0))

        if not is_meaningful_text(sub_text):
            score, status = 0.0, STATUS_MISSING
        else:
            # PR #10: token_set_ratio handles partial matches and word order
            # differences better than token_sort_ratio for Indic scripts
            score = fuzz.token_set_ratio(audio_text, sub_text) if audio_text and sub_text else 0.0
            status = STATUS_MATCH if score >= threshold else STATUS_REVIEW

        results.append({
            "timestamp": round(timestamp, 3),
            "timestamp_display": format_timestamp(timestamp),
            "audio_text": audio_text,
            "subtitle_text": sub_text,
            "score": round(score, 2),
            "status": status,
        })

    match_c = sum(1 for r in results if r["status"] == STATUS_MATCH)
    review_c = sum(1 for r in results if r["status"] == STATUS_REVIEW)
    missing_c = sum(1 for r in results if r["status"] == STATUS_MISSING)
    logger.info("Results: %d MATCH, %d REVIEW, %d MISSING", match_c, review_c, missing_c)

    if output_json:
        save_results(results, output_json)
    return results


def compute_summary_statistics(results: List[MismatchResult]) -> Dict[str, Any]:
    """Compute aggregate statistics from mismatch results."""
    total = len(results)
    if total == 0:
        return {"total_segments": 0}
    scores = [r["score"] for r in results]
    match_c = sum(1 for r in results if r["status"] == STATUS_MATCH)
    review_c = sum(1 for r in results if r["status"] == STATUS_REVIEW)
    missing_c = sum(1 for r in results if r["status"] == STATUS_MISSING)
    return {
        "total_segments": total,
        "match_count": match_c, "review_count": review_c, "missing_count": missing_c,
        "match_percentage": round(match_c / total * 100, 1),
        "review_percentage": round(review_c / total * 100, 1),
        "missing_percentage": round(missing_c / total * 100, 1),
        "average_score": round(sum(scores) / total, 2),
        "min_score": round(min(scores), 2),
        "max_score": round(max(scores), 2),
    }


def save_results(results: List[MismatchResult], path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=2)
    logger.info("Mismatch results saved → %s", path)


def load_results(path: str) -> List[MismatchResult]:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Results file not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)
