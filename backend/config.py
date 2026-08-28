"""
ClipForge AI — Configuration
Loads settings from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

# ─── Base Paths ───────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))

DOWNLOADS_DIR = DATA_DIR / "downloads"
AUDIO_DIR = DATA_DIR / "audio"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
CLIPS_DIR = DATA_DIR / "clips"
THUMBNAILS_DIR = DATA_DIR / "thumbnails"
JOBS_DIR = DATA_DIR / "jobs"
LOGS_DIR = DATA_DIR / "logs"

# ─── Server ───────────────────────────────────────────────────────────────────
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "3000"))
FRONTEND_URL = os.getenv("FRONTEND_URL", f"http://localhost:{FRONTEND_PORT}")

# ─── Database ─────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/clipforge.db")

# ─── Whisper ──────────────────────────────────────────────────────────────────
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

# ─── Video Output ─────────────────────────────────────────────────────────────
OUTPUT_WIDTH = int(os.getenv("OUTPUT_WIDTH", "1080"))
OUTPUT_HEIGHT = int(os.getenv("OUTPUT_HEIGHT", "1920"))
DEFAULT_CLIP_DURATION = int(os.getenv("DEFAULT_CLIP_DURATION", "30"))
DEFAULT_NUM_CLIPS = int(os.getenv("DEFAULT_NUM_CLIPS", "5"))
DEFAULT_SUBTITLE_STYLE = os.getenv("DEFAULT_SUBTITLE_STYLE", "bold")
DEFAULT_ASPECT_RATIO = os.getenv("DEFAULT_ASPECT_RATIO", "9:16")

# ─── Download ─────────────────────────────────────────────────────────────────
VIDEO_FORMAT = os.getenv("VIDEO_FORMAT", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]")
MAX_VIDEO_DURATION = int(os.getenv("MAX_VIDEO_DURATION", "3600"))  # 1 hour max

# ─── Processing ───────────────────────────────────────────────────────────────
MAX_CONCURRENT_JOBS = int(os.getenv("MAX_CONCURRENT_JOBS", "2"))

# ─── Ensure directories exist ─────────────────────────────────────────────────
def ensure_directories():
    for d in [DATA_DIR, DOWNLOADS_DIR, AUDIO_DIR, TRANSCRIPTS_DIR,
              CLIPS_DIR, THUMBNAILS_DIR, JOBS_DIR, LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)
