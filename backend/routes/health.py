"""
ClipForge AI — Health check route
"""

from fastapi import APIRouter
import shutil
from backend.utils.ffmpeg import ffmpeg_path

router = APIRouter()


@router.get("/api/health")
def health_check():
    checks = {}

    # FFmpeg
    try:
        ffmpeg_path()
        checks["ffmpeg"] = "ok"
    except RuntimeError:
        checks["ffmpeg"] = "missing"

    # yt-dlp
    checks["yt_dlp"] = "ok" if shutil.which("yt-dlp") else "missing"

    # faster-whisper
    try:
        import faster_whisper  # noqa
        checks["whisper"] = "ok"
    except ImportError:
        checks["whisper"] = "missing"

    all_ok = all(v == "ok" for v in checks.values())

    return {
        "success": True,
        "data": {
            "status": "healthy" if all_ok else "degraded",
            "version": "1.0.0",
            "checks": checks,
        },
        "error": None,
    }
