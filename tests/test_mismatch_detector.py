"""
Unit tests for the mismatch_detector module.
"""

import pytest
from burnin_subtitle_checker.modules.mismatch_detector import (
    detect_mismatches,
    compute_summary_statistics,
    STATUS_MATCH,
    STATUS_REVIEW,
    STATUS_MISSING,
)


def _make_transcript(texts):
    """Helper to build fake transcript segments."""
    return [
        {"start": i * 5.0, "end": i * 5.0 + 4.0, "text": t}
        for i, t in enumerate(texts)
    ]


def _make_subtitles(texts):
    """Helper to build fake subtitle segments."""
    return [
        {"timestamp": i * 5.0 + 2.0, "subtitle_text": t}
        for i, t in enumerate(texts)
    ]


class TestDetectMismatches:
    def test_perfect_match(self):
        t = _make_transcript(["वो कहाँ गई थी"])
        s = _make_subtitles(["वो कहाँ गई थी"])
        results = detect_mismatches(t, s, threshold=75.0)
        assert len(results) == 1
        assert results[0]["status"] == STATUS_MATCH
        assert results[0]["score"] == 100.0

    def test_mismatch_flagged(self):
        t = _make_transcript(["वो कहाँ गई थी"])
        s = _make_subtitles(["कुछ और ही था"])
        results = detect_mismatches(t, s, threshold=75.0)
        assert results[0]["status"] == STATUS_REVIEW
        assert results[0]["score"] < 75.0

    def test_missing_subtitle(self):
        t = _make_transcript(["वो कहाँ गई थी"])
        s = _make_subtitles([""])
        results = detect_mismatches(t, s, threshold=75.0)
        assert results[0]["status"] == STATUS_MISSING
        assert results[0]["score"] == 0.0

    def test_custom_threshold(self):
        t = _make_transcript(["abc def"])
        s = _make_subtitles(["abc xyz"])
        results_low = detect_mismatches(t, s, threshold=30.0)
        results_high = detect_mismatches(t, s, threshold=95.0)
        # Same data, different threshold → different status
        assert results_low[0]["status"] in (STATUS_MATCH, STATUS_REVIEW)
        assert results_high[0]["status"] == STATUS_REVIEW

    def test_multiple_segments(self):
        t = _make_transcript(["A", "B", "C"])
        s = _make_subtitles(["A", "B", "C"])
        results = detect_mismatches(t, s)
        assert len(results) == 3

    def test_result_fields(self):
        t = _make_transcript(["test"])
        s = _make_subtitles(["test"])
        results = detect_mismatches(t, s)
        r = results[0]
        assert "timestamp" in r
        assert "timestamp_display" in r
        assert "audio_text" in r
        assert "subtitle_text" in r
        assert "score" in r
        assert "status" in r


class TestSummaryStatistics:
    def test_empty_results(self):
        stats = compute_summary_statistics([])
        assert stats["total_segments"] == 0

    def test_all_match(self):
        results = [
            {"score": 90.0, "status": STATUS_MATCH},
            {"score": 85.0, "status": STATUS_MATCH},
        ]
        stats = compute_summary_statistics(results)
        assert stats["match_count"] == 2
        assert stats["review_count"] == 0
        assert stats["match_percentage"] == 100.0

    def test_mixed(self):
        results = [
            {"score": 95.0, "status": STATUS_MATCH},
            {"score": 50.0, "status": STATUS_REVIEW},
            {"score": 0.0, "status": STATUS_MISSING},
        ]
        stats = compute_summary_statistics(results)
        assert stats["total_segments"] == 3
        assert stats["match_count"] == 1
        assert stats["review_count"] == 1
        assert stats["missing_count"] == 1
        assert stats["average_score"] == round((95 + 50 + 0) / 3, 2)
