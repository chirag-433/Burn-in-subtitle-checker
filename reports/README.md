# Reports Directory

Auto-generated reports are saved here.

Each run creates a timestamped subdirectory containing:
- `report.html` — The main HTML mismatch report
- `transcript.json` — Whisper transcription (if `--save-intermediates`)
- `subtitles.json` — OCR-extracted subtitles (if `--save-intermediates`)
- `results.json` — Mismatch comparison data (if `--save-intermediates`)
- `frames/` — Preprocessed OCR frames (if `--save-frames`)
