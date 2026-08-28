# ClipForge AI

> Turn long YouTube videos into viral-ready short-form clips — automatically.

ClipForge AI downloads a YouTube video, transcribes it locally using [faster-whisper](https://github.com/SYSTRAN/faster-whisper), detects the most interesting moments with a rule-based scoring engine, generates ~30-second vertical (9:16) clips, burns in styled subtitles via FFmpeg, and serves everything through a modern Next.js dashboard.

**No paid AI API keys required. Runs entirely on your machine.**

---

## Features

- 🎬 YouTube URL input with real-time validation and metadata preview
- 🤖 Local speech transcription via faster-whisper (tiny → large-v3)
- ⚡ Rule-based highlight detection — no external AI API
- 📱 Automatic 9:16 vertical crop for Shorts/TikTok/Reels
- 💬 Burned-in subtitles (Bold, Minimal, Karaoke styles)
- 📊 Virality score and reason for each clip
- 🔄 Real-time progress via Server-Sent Events
- 💾 SQLite job tracking — survives backend restarts
- 📦 Download individual clips or all as ZIP
- 🖥️ Modern dark dashboard UI

---

## Architecture

```
ClipForge AI/
├── backend/               # FastAPI + Python
│   ├── main.py            # FastAPI app
│   ├── config.py          # Environment config
│   ├── database.py        # SQLAlchemy setup
│   ├── models.py          # ORM models
│   ├── routes/            # API routes (jobs, clips, health)
│   ├── services/          # Processing services
│   │   ├── youtube.py     # Metadata extraction
│   │   ├── downloader.py  # yt-dlp wrapper
│   │   ├── audio.py       # FFmpeg audio extraction
│   │   ├── transcription.py  # faster-whisper
│   │   ├── highlight_detection.py  # Rule-based scoring
│   │   ├── clip_generator.py  # Window selection
│   │   ├── subtitles.py   # ASS subtitle generation
│   │   └── video_processor.py  # FFmpeg video processing
│   ├── workers/
│   │   └── processor.py   # Background threading worker
│   └── utils/
│       ├── ffmpeg.py      # Safe FFmpeg subprocess wrapper
│       ├── validation.py  # YouTube URL validation
│       └── logger.py      # Structured logging
├── frontend/              # Next.js 14 + TypeScript + Tailwind
│   ├── app/               # App Router pages
│   ├── components/        # Reusable React components
│   └── lib/               # API client + types + utils
├── data/                  # Runtime data (auto-created)
│   ├── downloads/
│   ├── audio/
│   ├── transcripts/
│   ├── clips/
│   └── thumbnails/
├── requirements.txt
└── .env.example
```

---

## Requirements

- Python 3.10+
- Node.js 18+
- [FFmpeg](https://ffmpeg.org/download.html) (on system PATH)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- ~2 GB disk for Whisper models (downloaded on first use)

---

## Installation

### 1. Clone the project

```bash
git clone https://github.com/your-username/clipforge-ai.git
cd clipforge-ai
```

### 2. Install FFmpeg

**Windows:**
```bash
# Using winget
winget install Gyan.FFmpeg

# Or download from https://ffmpeg.org/download.html
# Extract and add to PATH
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

Verify: `ffmpeg -version`

### 3. Set up the backend

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Set up the frontend

```bash
cd frontend
npm install
cd ..
```

### 5. Configure environment

```bash
cp .env.example .env
# Edit .env as needed
```

Key settings in `.env`:
```
WHISPER_MODEL=small        # tiny|base|small|medium|large-v2
WHISPER_DEVICE=cpu         # cpu or cuda
DATA_DIR=./data
```

### 6. Start the backend

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 7. Start the frontend

```bash
cd frontend
npm run dev
```

### 8. Open in browser

Visit: **http://localhost:3000**

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `BACKEND_PORT` | `8000` | FastAPI server port |
| `FRONTEND_PORT` | `3000` | Next.js dev server port |
| `DATA_DIR` | `./data` | Directory for all generated files |
| `WHISPER_MODEL` | `small` | Whisper model size |
| `WHISPER_DEVICE` | `cpu` | `cpu` or `cuda` |
| `WHISPER_COMPUTE_TYPE` | `int8` | `int8` (CPU) or `float16` (GPU) |
| `OUTPUT_WIDTH` | `1080` | Output video width |
| `OUTPUT_HEIGHT` | `1920` | Output video height |
| `DEFAULT_CLIP_DURATION` | `30` | Default clip length in seconds |
| `DEFAULT_NUM_CLIPS` | `5` | Default number of clips |
| `MAX_VIDEO_DURATION` | `3600` | Max video length (seconds) |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Health check (FFmpeg, yt-dlp, Whisper) |
| `POST` | `/api/jobs` | Create a new processing job |
| `GET` | `/api/jobs` | List all jobs |
| `GET` | `/api/jobs/{id}` | Get job status |
| `DELETE` | `/api/jobs/{id}` | Delete job + all files |
| `GET` | `/api/jobs/{id}/clips` | Get clips for a job |
| `GET` | `/api/jobs/{id}/stream` | SSE progress stream |
| `GET` | `/api/jobs/{id}/download-all` | Download all clips as ZIP |
| `POST` | `/api/validate-url` | Validate a YouTube URL |
| `POST` | `/api/metadata` | Fetch video metadata |
| `GET` | `/api/clips/{id}` | Get clip info |
| `GET` | `/api/clips/{id}/download` | Download clip MP4 |
| `GET` | `/api/clips/{id}/preview` | Stream clip for HTML5 player |
| `GET` | `/api/clips/{id}/thumbnail` | Get clip thumbnail |

---

## Processing Pipeline

```
YouTube URL
    ↓ Validate URL (regex)
    ↓ Fetch metadata (yt-dlp --dump-json)
    ↓ Download video (yt-dlp, 720p max)
    ↓ Extract audio (FFmpeg → 16kHz mono WAV)
    ↓ Transcribe (faster-whisper, word timestamps)
    ↓ Score segments (RuleBasedHighlightDetector)
    ↓ Select windows (~30s around top moments)
    ↓ For each clip:
       ↓ Generate ASS subtitles
       ↓ FFmpeg: trim + crop 9:16 + burn subtitles + encode
       ↓ Generate thumbnail
    ↓ Cleanup temp files
    ↓ Update DB status to "completed"
```

---

## Running Tests

```bash
python -m pytest backend/tests/ -v
```

Expected: **34 passed**

---

## Troubleshooting

**FFmpeg not found:**
```
RuntimeError: FFmpeg not found. Install FFmpeg and ensure it is on your PATH.
```
→ Install FFmpeg and add it to your system PATH.

**yt-dlp not found:**
```
RuntimeError: yt-dlp is not installed.
```
→ Run: `pip install yt-dlp`

**Whisper model download slow:**
The first run downloads the Whisper model (~240MB for `small`). This is normal. Subsequent runs use the cached model.

**Video is private/unavailable:**
```
Unable to access this video. Please check the URL or try another video.
```
→ Try a public YouTube video URL.

**Out of memory with large model:**
→ Set `WHISPER_MODEL=tiny` or `WHISPER_MODEL=base` in `.env`

**Processing takes too long:**
→ A 10-minute video takes ~2–5 minutes on CPU with `small` model. Use `tiny` for faster (less accurate) transcription.

---

## Future Improvements

- [ ] Face detection + smart framing
- [ ] Local LLM for semantic highlight detection
- [ ] Audio intensity analysis
- [ ] Custom subtitle templates
- [ ] Automatic title/description generation
- [ ] TikTok, Instagram, YouTube Shorts direct export
- [ ] Virality prediction model
- [ ] Clip subtitle editor UI
- [ ] GPU acceleration support
- [ ] Cloud storage integration (S3/GCS)
- [ ] Celery/Redis for distributed processing
- [ ] Docker Compose deployment

---

## License

MIT License. See LICENSE file.

---

## Legal

ClipForge AI is intended for processing videos you own or have explicit permission to process.
Only process content you have the rights to use. Do not use this tool to download or redistribute
copyrighted content without authorization.
#   C l i p F o r g e - A I  
 