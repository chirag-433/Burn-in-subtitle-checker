"""
Module 2 — Burned-in Subtitle Extraction via OCR.

Captures frames at Whisper segment midpoints, crops the subtitle
region, preprocesses for OCR, and extracts text using Tesseract
with Indic language support (Hindi + Kannada).
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
import pytesseract

from burnin_subtitle_checker.utils.text_utils import clean_ocr_text, is_meaningful_text
from burnin_subtitle_checker.utils.video_utils import capture_frame, crop_subtitle_region, preprocess_for_ocr

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Type alias
# ──────────────────────────────────────────────
SubtitleSegment = Dict[str, Any]

# Tesseract language codes for the supported Indic scripts.
# Ensure that `tesseract-ocr-hin` and `tesseract-ocr-kan` (or equivalent
# language data packages) are installed on the system.
LANG_MAP = {
    "hi": "hin",        # Hindi (Devanagari)
    "kn": "kan",        # Kannada
    "en": "eng",        # English fallback
}


def extract_subtitles(
    video_path: str,
    segments: List[Dict[str, Any]],
    languages: Optional[List[str]] = None,
    crop_fraction: float = 0.15,
    output_json: Optional[str] = None,
    save_frames: bool = False,
    frames_dir: Optional[str] = None,
) -> List[SubtitleSegment]:
    """
    Extract burned-in subtitle text for each Whisper transcript segment.

    For every segment the function:
        1. Computes the midpoint timestamp
        2. Captures the video frame at that time
        3. Crops the bottom *crop_fraction* of the frame
        4. Preprocesses the crop (grayscale → denoise → threshold)
        5. Runs Tesseract OCR with the specified language(s)

    Args:
        video_path:    Path to the source video.
        segments:      Whisper transcript segments (list of dicts with
                       'start' and 'end' keys).
        languages:     ISO language codes to pass to Tesseract
                       (default: ['hi', 'kn']).
        crop_fraction: Bottom fraction of frame to crop (0.0–1.0).
        output_json:   Optional path to save results as JSON.
        save_frames:   If True, write cropped+preprocessed frames to disk.
        frames_dir:    Directory for saved frames (required if save_frames).

    Returns:
        List of subtitle segment dicts with keys:
            - timestamp (float)
            - subtitle_text (str)
    """
    if languages is None:
        languages = ["hi", "kn"]

    tess_lang = _resolve_tesseract_lang(languages)
    logger.info("Extracted %d frames, running OCR...", len(segments))

    if save_frames:
        frames_dir = frames_dir or "frames"
        os.makedirs(frames_dir, exist_ok=True)

    results: List[SubtitleSegment] = []

    for idx, seg in enumerate(segments):
        midpoint = round((seg["start"] + seg["end"]) / 2, 3)
        if (idx + 1) % 25 == 0:
            logger.info("OCR progress: %d/%d", idx + 1, len(segments))

        # ── Capture frame ──
        frame = capture_frame(video_path, midpoint)
        if frame is None:
            logger.warning("Skipping segment %d — no frame at %.3fs", idx, midpoint)
            results.append({"timestamp": midpoint, "subtitle_text": ""})
            continue

        # ── Crop subtitle region ──
        subtitle_region = crop_subtitle_region(frame, crop_fraction)

        # ── Preprocess ──
        processed = preprocess_for_ocr(subtitle_region)

        # ── Optionally save debug frames ──
        if save_frames and frames_dir:
            fname = os.path.join(frames_dir, f"frame_{idx:04d}_{midpoint:.2f}s.png")
            cv2.imwrite(fname, processed)

        # ── OCR ──
        raw_text = _run_tesseract(processed, tess_lang)
        cleaned = clean_ocr_text(raw_text)

        if not is_meaningful_text(cleaned):
            logger.debug("Segment %d — OCR text too short or empty, treating as blank.", idx)
            cleaned = ""

        results.append({
            "timestamp": midpoint,
            "subtitle_text": cleaned,
        })

    logger.info("Subtitle extraction complete — %d segments processed.", len(results))

    if output_json:
        save_subtitles(results, output_json)

    return results


def _resolve_tesseract_lang(languages: List[str]) -> str:
    """
    Convert ISO language codes to a Tesseract-compatible lang string.

    Tesseract expects '+'-separated language codes, e.g. 'hin+kan'.

    Args:
        languages: List of ISO 639-1 codes.

    Returns:
        Tesseract lang string.
    """
    tess_codes = []
    for lang in languages:
        code = LANG_MAP.get(lang, lang)
        tess_codes.append(code)
    return "+".join(tess_codes)


def _run_tesseract(image: np.ndarray, lang: str) -> str:
    """
    Run Tesseract OCR on a preprocessed image.

    Args:
        image: Grayscale/binary numpy array.
        lang:  Tesseract language string (e.g. 'hin+kan').

    Returns:
        Raw OCR text output.
    """
    # PR #10: PSM 7 (single text line) works better for subtitles than PSM 6
    custom_config = r"--oem 3 --psm 7"
    try:
        text = pytesseract.image_to_string(
            image,
            lang=lang,
            config=custom_config,
        )
        return text.strip()
    except pytesseract.TesseractError as exc:
        logger.error("Tesseract OCR failed: %s", exc)
        return ""


def save_subtitles(segments: List[SubtitleSegment], path: str) -> None:
    """
    Persist subtitle segments to a JSON file.

    Args:
        segments: List of subtitle segment dicts.
        path:     Output file path.
    """
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(segments, fh, ensure_ascii=False, indent=2)
    logger.info("Subtitles saved → %s", path)


def load_subtitles(path: str) -> List[SubtitleSegment]:
    """
    Load subtitle segments from a previously saved JSON file.

    Args:
        path: Path to the JSON file.

    Returns:
        List of subtitle segment dicts.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Subtitle file not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)
