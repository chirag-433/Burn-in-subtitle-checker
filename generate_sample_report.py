#!/usr/bin/env python3
"""
Generate a sample HTML report with mock data for demonstration.

Usage:
    python generate_sample_report.py
"""

import os
import sys

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(__file__))

from modules.mismatch_detector import compute_summary_statistics
from modules.report_generator import generate_report

SAMPLE_RESULTS = [
    {
        "timestamp": 5.2,
        "timestamp_display": "00:00:05.200",
        "audio_text": "नमस्ते दोस्तों",
        "subtitle_text": "नमस्ते दोस्तों",
        "score": 100.0,
        "status": "MATCH",
        "reason": "perfect match",
    },
    {
        "timestamp": 10.2,
        "timestamp_display": "00:00:10.200",
        "audio_text": "वो कहाँ गई थी",
        "subtitle_text": "वो कहाँ गया था",
        "score": 61.0,
        "status": "REVIEW",
        "reason": "low similarity",
    },
    {
        "timestamp": 18.5,
        "timestamp_display": "00:00:18.500",
        "audio_text": "आज मौसम बहुत अच्छा है",
        "subtitle_text": "आज मौसम बहुत अच्छा है",
        "score": 100.0,
        "status": "MATCH",
        "reason": "perfect match",
    },
    {
        "timestamp": 25.0,
        "timestamp_display": "00:00:25.000",
        "audio_text": "ಹೇಗಿದ್ದೀರಿ ನೀವು",
        "subtitle_text": "ಹೇಗಿದ್ದೀರಿ ನೀವು",
        "score": 100.0,
        "status": "MATCH",
        "reason": "perfect match",
    },
    {
        "timestamp": 32.8,
        "timestamp_display": "00:00:32.800",
        "audio_text": "ये बात सही नहीं है",
        "subtitle_text": "ये बात गलत है",
        "score": 48.0,
        "status": "REVIEW",
        "reason": "low similarity",
    },
    {
        "timestamp": 40.1,
        "timestamp_display": "00:00:40.100",
        "audio_text": "चलो अब चलते हैं",
        "subtitle_text": "",
        "score": 0.0,
        "status": "MISSING",
        "reason": "missing subtitle",
    },
    {
        "timestamp": 47.3,
        "timestamp_display": "00:00:47.300",
        "audio_text": "ಈ ಚಿತ್ರ ತುಂಬಾ ಚೆನ್ನಾಗಿದೆ",
        "subtitle_text": "ಈ ಚಿತ್ರ ಚೆನ್ನಾಗಿದೆ",
        "score": 78.0,
        "status": "MATCH",
        "reason": "high similarity",
    },
    {
        "timestamp": 55.0,
        "timestamp_display": "00:00:55.000",
        "audio_text": "मुझे यह पसंद आया",
        "subtitle_text": "मुझे यह पसंद आया",
        "score": 100.0,
        "status": "MATCH",
        "reason": "perfect match",
    },
]


def main():
    output = os.path.join("samples", "sample_report.html")
    os.makedirs("samples", exist_ok=True)

    report_path = generate_report(
        SAMPLE_RESULTS,
        output,
        video_name="sample_hindi_kannada.mp4",
    )

    stats = compute_summary_statistics(SAMPLE_RESULTS)
    print(f"Sample report generated -> {report_path}")
    print(f"  Total: {stats['total_segments']}  |  "
          f"Match: {stats['match_count']}  |  "
          f"Review: {stats['review_count']}  |  "
          f"Missing: {stats['missing_count']}")


if __name__ == "__main__":
    main()
