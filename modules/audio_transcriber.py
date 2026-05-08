"""
Module 1 — Audio Transcription using OpenAI Whisper.

Extracts audio from a video file and transcribes spoken dialogue
into timestamped text segments. Supports Hindi and Kannada.
"""

import json
import logging
import os
import tempfile
from typing import Any, Dict, List, Optional

import whisper

from utils.video_utils import extract_audio

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Type aliases
# ──────────────────────────────────────────────
TranscriptSegment = Dict[str, Any]


def transcribe_video(
    video_path: str,
    model_size: str = "base",
    language: Optional[str] = "hi",
    output_json: Optional[str] = None,
    device: Optional[str] = None,
) -> List[TranscriptSegment]:
    """
    End-to-end: extract audio from *video_path* and transcribe with Whisper.

    Args:
        video_path: Path to the input video file.
        model_size: Whisper model size — one of
                    'tiny', 'base', 'small', 'medium', 'large'.
        language:   ISO language code (e.g. 'hi' for Hindi, 'kn' for Kannada).
                    If None, Whisper auto-detects.
        output_json: Optional path to save the transcript as JSON.
        device:     Force device ('cpu' or 'cuda'). None = auto.

    Returns:
        List of transcript segments, each containing:
            - start (float): segment start time in seconds
            - end   (float): segment end time in seconds
            - text  (str):   transcribed text
    """
    logger.info(
        "Starting transcription — model=%s, language=%s, device=%s",
        model_size, language or "auto", device or "auto",
    )

    # ── 1. Extract audio to a temp WAV ──
    tmp_dir = tempfile.mkdtemp(prefix="asmft_")
    audio_path = os.path.join(tmp_dir, "audio.wav")
    extract_audio(video_path, audio_path)

    # ── 2. Load Whisper model ──
    logger.info("Loading Whisper model '%s'…", model_size)
    model = whisper.load_model(model_size, device=device)

    # ── 3. Transcribe ──
    logger.info("Transcribing audio…")
    transcribe_opts: Dict[str, Any] = {
        "verbose": False,
        "task": "transcribe",
    }
    # Force language to avoid Whisper misidentifying Indic audio
    # (PR #10 insight: auto-detect often fails for Hindi/Kannada)
    if language:
        transcribe_opts["language"] = language

    result = model.transcribe(audio_path, **transcribe_opts)

    # ── 4. Build clean segment list ──
    segments = _build_segments(result)
    logger.info("Transcription complete — %d segments found.", len(segments))

    # ── 5. Optionally save to JSON ──
    if output_json:
        save_transcript(segments, output_json)

    # ── 6. Cleanup temp audio ──
    try:
        os.remove(audio_path)
        os.rmdir(tmp_dir)
    except OSError:
        logger.warning("Could not clean temp dir: %s", tmp_dir)

    return segments


def _build_segments(result: Dict[str, Any]) -> List[TranscriptSegment]:
    """
    Extract clean segment dicts from raw Whisper output.

    Args:
        result: Raw dict returned by whisper.transcribe().

    Returns:
        List of dicts with 'start', 'end', and 'text' keys.
    """
    segments: List[TranscriptSegment] = []
    for seg in result.get("segments", []):
        start = round(seg["start"], 3)
        end = round(seg["end"], 3)
        segments.append({
            "start": start,
            "end": end,
            "midpoint": round((start + end) / 2, 3),
            "text": seg["text"].strip(),
        })
    return segments


def save_transcript(
    segments: List[TranscriptSegment],
    path: str,
) -> None:
    """
    Persist transcript segments to a JSON file.

    Args:
        segments: List of transcript segment dicts.
        path:     Output file path.
    """
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(segments, fh, ensure_ascii=False, indent=2)
    logger.info("Transcript saved → %s", path)


def load_transcript(path: str) -> List[TranscriptSegment]:
    """
    Load transcript segments from a previously saved JSON file.

    Args:
        path: Path to the JSON file.

    Returns:
        List of transcript segment dicts.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Transcript file not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)
