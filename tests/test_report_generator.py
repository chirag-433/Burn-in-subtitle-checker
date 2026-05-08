"""
Unit tests for the report_generator module.
"""

import os
import tempfile

import pytest

from modules.report_generator import generate_report


def _sample_results():
    return [
        {
            "timestamp": 10.2,
            "timestamp_display": "00:00:10.200",
            "audio_text": "वो कहाँ गई थी",
            "subtitle_text": "वो कहाँ गया था",
            "score": 61.0,
            "status": "REVIEW",
        },
        {
            "timestamp": 15.5,
            "timestamp_display": "00:00:15.500",
            "audio_text": "ये सही है",
            "subtitle_text": "ये सही है",
            "score": 100.0,
            "status": "MATCH",
        },
        {
            "timestamp": 22.0,
            "timestamp_display": "00:00:22.000",
            "audio_text": "कुछ कह रहा है",
            "subtitle_text": "",
            "score": 0.0,
            "status": "MISSING",
        },
    ]


class TestGenerateReport:
    def test_creates_html_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "report.html")
            result = generate_report(_sample_results(), path, video_name="test.mp4")
            assert os.path.isfile(result)

    def test_html_contains_segments(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "report.html")
            generate_report(_sample_results(), path)
            with open(path, encoding="utf-8") as f:
                html = f.read()
            assert "वो कहाँ गई थी" in html
            assert "REVIEW" in html
            assert "MATCH" in html
            assert "MISSING" in html

    def test_html_contains_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "report.html")
            generate_report(_sample_results(), path)
            with open(path, encoding="utf-8") as f:
                html = f.read()
            assert "Total Segments" in html

    def test_html_is_valid_standalone(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "report.html")
            generate_report(_sample_results(), path)
            with open(path, encoding="utf-8") as f:
                html = f.read()
            assert html.startswith("<!DOCTYPE html>")
            assert "</html>" in html
