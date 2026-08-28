"""
ClipForge AI — YouTube metadata extraction
Uses yt-dlp to safely retrieve video metadata without downloading.
"""

import subprocess
import json
from typing import Optional
from dataclasses import dataclass

from backend.utils.validation import is_valid_youtube_url, extract_video_id
from backend.utils.logger import get_logger

log = get_logger("youtube")


@dataclass
class VideoMetadata:
    video_id: str
    title: str
    duration: float          # seconds
    thumbnail: Optional[str]
    channel: Optional[str]
    description: Optional[str]
    view_count: Optional[int]
    upload_date: Optional[str]


def get_video_metadata(url: str) -> VideoMetadata:
    """
    Fetch YouTube video metadata using yt-dlp (no download).
    Raises ValueError for invalid URLs.
    Raises RuntimeError for unavailable/private videos.
    """
    if not is_valid_youtube_url(url):
        raise ValueError("Invalid YouTube URL")

    video_id = extract_video_id(url)
    log.info("Fetching metadata for video_id=%s", video_id)

    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--dump-json",
                "--no-playlist",
                "--no-download",
                url,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )
    except FileNotFoundError:
        raise RuntimeError("yt-dlp is not installed. Please install it: pip install yt-dlp")
    except subprocess.TimeoutExpired:
        raise RuntimeError("Timed out while fetching video metadata.")

    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace")
        log.warning("yt-dlp metadata error: %s", stderr)
        if "Private video" in stderr or "private" in stderr.lower():
            raise RuntimeError("This video is private and cannot be accessed.")
        if "not available" in stderr.lower() or "unavailable" in stderr.lower():
            raise RuntimeError("This video is not available. It may have been removed or restricted.")
        if "Sign in" in stderr or "age" in stderr.lower():
            raise RuntimeError("This video requires age verification or sign-in.")
        raise RuntimeError(f"Unable to access this video. Please check the URL or try another video.")

    try:
        info = json.loads(result.stdout.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        raise RuntimeError("Failed to parse video metadata.")

    # Pick best thumbnail
    thumbnail = info.get("thumbnail")
    thumbnails = info.get("thumbnails", [])
    if thumbnails:
        # Prefer maxresdefault or hqdefault
        for t in reversed(thumbnails):
            if t.get("url"):
                thumbnail = t["url"]
                break

    return VideoMetadata(
        video_id=info.get("id", video_id),
        title=info.get("title", "Unknown Video"),
        duration=float(info.get("duration", 0)),
        thumbnail=thumbnail,
        channel=info.get("uploader") or info.get("channel"),
        description=info.get("description", ""),
        view_count=info.get("view_count"),
        upload_date=info.get("upload_date"),
    )
