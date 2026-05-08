# Lightweight Audio-Subtitle Mismatch Flagging Tool

Automatically detect mismatches between spoken dialogue and burned-in subtitles in video files. Supports Hindi (Devanagari) and Kannada scripts.

---
<img width="1881" height="868" alt="image" src="https://github.com/user-attachments/assets/e31057b2-5df1-4f22-a322-2d8238bbae1d" />
<img width="1877" height="692" alt="image" src="https://github.com/user-attachments/assets/5f510dbf-f6e0-4dc4-853a-ab9ff9af6919" />

## Features

| Feature | Description |
|---|---|
| Audio Transcription | Whisper ASR with configurable model sizes |
| Subtitle Extraction | Tesseract OCR on burned-in subtitle frames |
| Mismatch Detection | RapidFuzz fuzzy matching (`token_set_ratio`) with configurable thresholds |
| HTML Reports | Standalone, color-coded reports with summary statistics |
| Indic Language Support | Hindi and Kannada with Unicode NFC normalization |
| CLI Interface | Simple command-line usage with rich options |

---

## Project Structure

```
project/
├── main.py                          # CLI entry point
├── modules/
│   ├── audio_transcriber.py         # Whisper-based speech-to-text
│   ├── subtitle_extractor.py        # OCR-based subtitle extraction
│   ├── mismatch_detector.py         # Fuzzy text comparison
│   └── report_generator.py          # HTML report generation
├── utils/
│   ├── text_utils.py                # Indic text normalization
│   └── video_utils.py               # Video/audio processing helpers
├── tests/                           # Unit tests
├── reports/                         # Generated reports (auto-created)
├── samples/                         # Sample report output
├── generate_sample_report.py        # Demo report generator (no video needed)
├── requirements.txt
└── README.md
```

---

## Setup Instructions

### Prerequisites

1. **Python 3.8+**
2. **FFmpeg** — must be installed and available on `PATH`
3. **Tesseract OCR** — with Hindi and Kannada language packs

### Step 1 — Install FFmpeg

**Windows (via winget):**
```bash
winget install --id=Gyan.FFmpeg -e
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

### Step 2 — Install Tesseract OCR

**Windows:**
```bash
winget install --id=UB-Mannheim.TesseractOCR -e
```
After installing, download Hindi and Kannada language packs (`hin.traineddata`, `kan.traineddata`) from [tesseract-ocr/tessdata](https://github.com/tesseract-ocr/tessdata) and place them in the Tesseract `tessdata` directory.

**Ubuntu/Debian:**
```bash
sudo apt install tesseract-ocr tesseract-ocr-hin tesseract-ocr-kan
```

**macOS:**
```bash
brew install tesseract
```

### Step 3 — Clone and Install Python Dependencies

```bash
git clone <repo-url>
cd bharat

# Create virtual environment (recommended)
python -m venv venv

# Windows:
venv\Scripts\activate

# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4 — Verify Installation

```bash
ffmpeg -version
tesseract --version
python -m pytest tests/ -v
```

---

## Usage

### Basic Usage

```bash
python main.py path/to/video.mp4
```

### Full Options

```bash
python main.py video.mp4 \
    --model medium \
    --language hi kn \
    --threshold 70 \
    --output-dir reports/my_run \
    --save-intermediates \
    --save-frames \
    --verbose
```

### CLI Arguments

| Argument | Short | Default | Description |
|---|---|---|---|
| `video` | — | *required* | Path to input video file |
| `--model` | `-m` | `base` | Whisper model: tiny, base, small, medium, large |
| `--language` | `-l` | `hi kn` | Language codes for OCR and Whisper |
| `--threshold` | `-t` | `75.0` | Similarity threshold (0-100) |
| `--output-dir` | `-o` | `reports/<timestamp>` | Output directory |
| `--crop-fraction` | — | `0.20` | Bottom fraction of frame to crop for OCR |
| `--device` | — | auto | Force `cpu` or `cuda` for Whisper |
| `--save-intermediates` | — | off | Save JSON files for transcript/subtitles/results |
| `--save-frames` | — | off | Save preprocessed OCR frames |
| `--verbose` | `-v` | off | Enable debug logging |

### Generate Sample Report (No Video Needed)

```bash
python generate_sample_report.py
# Output: samples/sample_report.html
```

---

## Pipeline Overview

```
Input Video
    |
    ├──> [Audio Transcriber]   Whisper ASR (forced language)
    |         |
    |         v
    |    Timestamped transcript segments
    |
    ├──> [Subtitle Extractor]  OpenCV frame capture + Tesseract OCR
    |         |
    |         v
    |    OCR text at each segment midpoint
    |
    └──> [Mismatch Detector]   RapidFuzz token_set_ratio comparison
              |
              v
         [HTML Reporter]       Color-coded report with summary stats
```

---

## Running Tests

```bash
# All tests
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ -v --cov=modules --cov=utils --cov-report=html
```

---

## Configuration Tips

- **Low OCR accuracy?** Try `--crop-fraction 0.25` to capture more of the subtitle region.
- **Slow processing?** Use `--model tiny` for faster (but less accurate) transcription.
- **GPU available?** Use `--device cuda` for significantly faster Whisper inference.
- **Different language?** Pass the appropriate ISO 639-1 code via `--language`.
- **Too many false positives?** Lower the threshold (e.g. `--threshold 40`).

---

## Output Example

Each run produces a report with:

| Timestamp | Audio Text | Subtitle Text | Score | Status |
|---|---|---|---|---|
| 00:00:10.200 | वो कहाँ गई थी | वो कहाँ गया था | 61.0 | REVIEW |
| 00:00:18.500 | आज मौसम बहुत अच्छा है | आज मौसम बहुत अच्छा है | 100.0 | MATCH |
| 00:00:40.100 | चलो अब चलते हैं | — | 0.0 | MISSING |

---

## Stretch Goals

- [ ] Subtitle timing drift detection
- [ ] EasyOCR as alternative OCR backend for scene text
- [ ] Frame averaging for noise reduction
- [ ] Multi-language auto-detection
- [ ] Docker support
- [ ] Batch video processing
- [ ] Web dashboard (FastAPI / Flask)

---

## License

This project is open-source and available under the [MIT License](LICENSE).

---

## Contributing

Contributions are welcome. Please open an issue or submit a pull request.
