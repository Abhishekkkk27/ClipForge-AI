"""
ClipForge AI — Configuration
Loads settings from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from typing import Optional
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

# ─── YouTube Cookies & Authentication ───────────────────────────────────────────
YOUTUBE_COOKIES_FILE = os.getenv("YOUTUBE_COOKIES_FILE")
YOUTUBE_COOKIES_TEXT = os.getenv("YOUTUBE_COOKIES_TEXT")
YOUTUBE_COOKIES_BASE64 = os.getenv("YOUTUBE_COOKIES_BASE64")

def get_youtube_cookies_path() -> Optional[Path]:
    """
    Resolve the YouTube cookies file path safely without logging or exposing contents.
    Order of precedence:
      1. Explicit YOUTUBE_COOKIES_FILE environment variable (if file exists).
      2. YOUTUBE_COOKIES_TEXT or YOUTUBE_COOKIES_BASE64 (written to data/cookies.txt).
      3. Render secret file mount (/etc/secrets/cookies.txt).
      4. Local cookies.txt in DATA_DIR or project root.
    Returns Path if a valid cookie file exists, otherwise None.
    """
    import base64

    # 1. Explicit file path
    if YOUTUBE_COOKIES_FILE:
        p = Path(YOUTUBE_COOKIES_FILE)
        if p.is_file() and p.stat().st_size > 0:
            return p

    # 2. Raw or Base64 cookie string from environment
    cookie_content = None
    if YOUTUBE_COOKIES_TEXT and YOUTUBE_COOKIES_TEXT.strip():
        cookie_content = YOUTUBE_COOKIES_TEXT.strip()
    elif YOUTUBE_COOKIES_BASE64 and YOUTUBE_COOKIES_BASE64.strip():
        try:
            cookie_content = base64.b64decode(YOUTUBE_COOKIES_BASE64.strip()).decode("utf-8", errors="replace")
        except Exception:
            pass

    if cookie_content:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        target = DATA_DIR / "cookies.txt"
        try:
            target.write_text(cookie_content, encoding="utf-8")
            try:
                # Set permissions to 0600 on POSIX platforms
                target.chmod(0o600)
            except Exception:
                pass
            return target
        except Exception:
            pass

    # 3. Render secret files default mount path
    render_secret = Path("/etc/secrets/cookies.txt")
    if render_secret.is_file() and render_secret.stat().st_size > 0:
        return render_secret

    # 4. Local cookies.txt in DATA_DIR or root
    for candidate in [DATA_DIR / "cookies.txt", BASE_DIR / "cookies.txt"]:
        if candidate.is_file() and candidate.stat().st_size > 0:
            return candidate

    return None

# ─── Ensure directories exist ─────────────────────────────────────────────────
def ensure_directories():
    for d in [DATA_DIR, DOWNLOADS_DIR, AUDIO_DIR, TRANSCRIPTS_DIR,
              CLIPS_DIR, THUMBNAILS_DIR, JOBS_DIR, LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)
