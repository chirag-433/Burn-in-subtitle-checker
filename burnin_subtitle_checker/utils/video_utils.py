"""
Video processing utilities.

Provides helpers for audio extraction, frame capture, and
subtitle region cropping using OpenCV and FFmpeg.
"""

import logging
import os
import subprocess
from typing import Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def extract_audio(
    video_path: str,
    output_path: str,
    sample_rate: int = 16000,
    channels: int = 1,
) -> str:
    """
    Extract audio track from video using FFmpeg.

    Converts to 16 kHz mono WAV (Whisper's expected input format).

    Args:
        video_path:  Path to the input video file.
        output_path: Path for the extracted WAV file.
        sample_rate: Audio sample rate in Hz (default: 16000).
        channels:    Number of audio channels (default: 1 = mono).

    Returns:
        Absolute path to the extracted audio file.

    Raises:
        FileNotFoundError: If the video file does not exist.
        RuntimeError:      If FFmpeg extraction fails.
    """
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",                   # Overwrite output
        "-i", video_path,       # Input video
        "-vn",                  # No video
        "-acodec", "pcm_s16le", # PCM 16-bit little-endian
        "-ar", str(sample_rate),
        "-ac", str(channels),
        output_path,
    ]

    logger.info("Extracting audio: %s → %s", video_path, output_path)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        logger.debug("FFmpeg stdout: %s", result.stdout)
    except subprocess.CalledProcessError as exc:
        logger.error("FFmpeg failed: %s", exc.stderr)
        raise RuntimeError(f"Audio extraction failed: {exc.stderr}") from exc

    if not os.path.isfile(output_path):
        raise RuntimeError(f"Audio file was not created: {output_path}")

    logger.info("Audio extracted successfully: %s", output_path)
    return os.path.abspath(output_path)


def capture_frame(
    video_path: str,
    timestamp: float,
) -> Optional[np.ndarray]:
    """
    Capture a single frame from a video at the specified timestamp.

    Args:
        video_path: Path to the video file.
        timestamp:  Time in seconds at which to capture.

    Returns:
        BGR numpy array of the captured frame, or None on failure.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error("Cannot open video: %s", video_path)
        return None

    # Seek to the requested timestamp (milliseconds)
    cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
    success, frame = cap.read()
    cap.release()

    if not success or frame is None:
        logger.warning("Failed to capture frame at %.2fs from %s", timestamp, video_path)
        return None

    return frame


def crop_subtitle_region(
    frame: np.ndarray,
    region_fraction: float = 0.15,
) -> np.ndarray:
    """
    Crop the bottom portion of a frame where subtitles typically appear.

    Args:
        frame:           BGR image as numpy array.
        region_fraction: Fraction of frame height to keep from the bottom
                         (default: 0.15 = bottom 15%).

    Returns:
        Cropped BGR image of the subtitle region.
    """
    height = frame.shape[0]
    # PR #10: bottom 20% crop matches BookBox AniBook subtitle placement
    crop_start = int(height * (1 - region_fraction))
    return frame[crop_start:, :]


def preprocess_for_ocr(image: np.ndarray) -> np.ndarray:
    """
    Preprocess a subtitle region image for better OCR accuracy.

    Pipeline:
        1. Convert to grayscale
        2. Apply bilateral filter for denoising (preserves edges)
        3. Apply adaptive thresholding for binarisation
        4. Optional morphological cleanup

    Args:
        image: BGR image of the subtitle region.

    Returns:
        Preprocessed grayscale image optimised for Tesseract.
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # PR #10: Upscale 2x for better OCR readability on small subtitle text
    gray = cv2.resize(gray, None, fx=2, fy=2)

    # PR #10: Light Gaussian blur only — preserves subtitle edges better
    # than bilateral filter + adaptive threshold for burned-in subtitles
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    return gray


def get_video_info(video_path: str) -> dict:
    """
    Retrieve basic metadata about a video file.

    Args:
        video_path: Path to the video file.

    Returns:
        Dictionary with keys: fps, width, height, frame_count, duration_sec.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {video_path}")

    info = {
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
    }
    info["duration_sec"] = (
        info["frame_count"] / info["fps"] if info["fps"] > 0 else 0
    )
    cap.release()

    return info
