#!/usr/bin/env python3
"""
Lightweight Audio-Subtitle Mismatch Flagging Tool
==================================================

CLI entry point.  Processes a video end-to-end:
    1. Transcribe spoken audio (Whisper)
    2. Extract burned-in subtitles (Tesseract OCR)
    3. Compare texts and flag mismatches (RapidFuzz)
    4. Generate an HTML report

Usage:
    python main.py input.mp4
    python main.py https://www.youtube.com/watch?v=...
    python main.py input.mp4 --language hi --model medium --threshold 70
    python main.py input.mp4 --save-intermediates
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime

from colorama import Fore, Style, init as colorama_init

from burnin_subtitle_checker.modules.audio_transcriber import transcribe_video
from burnin_subtitle_checker.modules.subtitle_extractor import extract_subtitles
from burnin_subtitle_checker.modules.mismatch_detector import detect_mismatches, compute_summary_statistics
from burnin_subtitle_checker.modules.report_generator import generate_report


# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
VERSION = "1.0.0"
DEFAULT_MODEL = "base"
DEFAULT_THRESHOLD = 75.0
DEFAULT_LANGUAGES = ["hi", "kn"]


def main() -> int:
    """Parse CLI args and run the full pipeline."""
    colorama_init(autoreset=True)
    args = _parse_args()
    _setup_logging(args.verbose)

    logger = logging.getLogger(__name__)

    # ── Validate input ──
    video_path = args.video
    if video_path.startswith("http://") or video_path.startswith("https://"):
        from burnin_subtitle_checker.utils.youtube_downloader import download_video
        try:
            video_path = download_video(video_path, output_dir="downloads")
        except Exception as exc:
            logger.exception("Failed to download video")
            print(f"Error: YouTube blocked the download (Bot Protection/No Formats).")
            print(f"Please download the video manually and run: python -m burnin_subtitle_checker run video.mp4 --language hi")
            return 1
    elif not os.path.isfile(video_path):
        print(f"Error: Video file not found: {video_path}")
        return 1

    video_name = os.path.basename(video_path)
    base_dir = args.output_dir or "outputs"
    os.makedirs(base_dir, exist_ok=True)
    
    t_start = time.time()

    # ── Step 1: Audio Transcription ──
    print("Step 1/3: Transcribing audio...")
    transcript_json = os.path.join(base_dir, "transcription", "transcription.json")
    try:
        transcript = transcribe_video(
            video_path=video_path,
            model_size=args.model,
            language=args.language[0],
            output_json=transcript_json,
            device=args.device,
        )
    except Exception as exc:
        logger.exception("Transcription failed")
        print(f"Error: Transcription failed: {exc}")
        return 1

    # ── Step 2: Subtitle Extraction ──
    print("Step 2/3: Extracting subtitles via OCR...")
    subtitles_json = os.path.join(base_dir, "ocr", "ocr_segments.json")
    try:
        subtitles = extract_subtitles(
            video_path=video_path,
            segments=transcript,
            languages=args.language,
            crop_fraction=args.crop_fraction,
            output_json=subtitles_json,
            save_frames=args.save_frames,
            frames_dir=os.path.join(base_dir, "frames") if args.save_frames else None,
        )
    except Exception as exc:
        logger.exception("Subtitle extraction failed")
        print(f"Error: OCR extraction failed: {exc}")
        return 1

    # ── Step 3: Mismatch Detection ──
    print("Step 3/3: Comparing and generating report...")
    results_json = os.path.join(base_dir, "results.json") if args.save_intermediates else None
    results = detect_mismatches(
        transcript_segments=transcript,
        subtitle_segments=subtitles,
        threshold=args.threshold,
        output_json=results_json,
    )
    stats = compute_summary_statistics(results)

    # ── Step 4: HTML Report ──
    report_path = os.path.join(base_dir, "report", "report.html")
    generate_report(results, report_path, video_name=video_name)

    print(f"\nTranscription: {transcript_json}")
    print(f"OCR: {subtitles_json}")
    print(f"Report: {report_path}")
    print(f"Flagged: {stats['review_count'] + stats['missing_count']}/{stats['total_segments']}")
    
    elapsed = time.time() - t_start
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)
    print(f"Total time: {mins}m {secs}s")
    return 0


# ──────────────────────────────────────────────
# CLI helpers
# ──────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="burnin_subtitle_checker",
        description="Detect mismatches between spoken audio and burned-in subtitles.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {VERSION}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="Run the mismatch pipeline.")
    
    run_parser.add_argument("video", help="Path to the input video file or YouTube URL.")
    run_parser.add_argument(
        "--model", "-m", default=DEFAULT_MODEL,
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size (default: base).",
    )
    run_parser.add_argument(
        "--language", "-l", nargs="+", default=DEFAULT_LANGUAGES,
        help="Language codes for OCR/Whisper, e.g. hi kn (default: hi kn).",
    )
    run_parser.add_argument(
        "--threshold", "-t", type=float, default=DEFAULT_THRESHOLD,
        help="Similarity threshold 0–100 (default: 75).",
    )
    run_parser.add_argument(
        "--output-dir", "-o",
        help="Custom output directory for reports.",
    )
    run_parser.add_argument(
        "--crop-fraction", type=float, default=0.20,
        help="Bottom fraction of frame to crop for OCR (default: 0.20).",
    )
    run_parser.add_argument(
        "--device", choices=["cpu", "cuda"],
        help="Force Whisper to use a specific device.",
    )
    run_parser.add_argument(
        "--save-intermediates", action="store_true",
        help="Save transcript, subtitles, and results as JSON.",
    )
    run_parser.add_argument(
        "--save-frames", action="store_true",
        help="Save preprocessed OCR frames to disk.",
    )
    run_parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable debug-level logging.",
    )
    return parser.parse_args()


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
    )


if __name__ == "__main__":
    sys.exit(main())
