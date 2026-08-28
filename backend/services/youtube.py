"""
ClipForge AI — YouTube metadata extraction
Uses yt-dlp to safely retrieve video metadata without downloading.
"""

import subprocess
import json
from typing import Optional, List
from dataclasses import dataclass
from pathlib import Path

from backend import config
from backend.utils.validation import is_valid_youtube_url, extract_video_id
from backend.utils.logger import get_logger

log = get_logger("youtube")


def get_ytdlp_base_args() -> List[str]:
    """
    Build common, production-resilient arguments for yt-dlp.
    Includes mobile client fallbacks, timeouts, retries, geo-bypass, and optional cookies.
    """
    args = [
        "yt-dlp",
        "--extractor-args", "youtube:player_client=android,web,mweb,ios",
        "--socket-timeout", "30",
        "--retries", "5",
        "--fragment-retries", "5",
        "--file-access-retries", "3",
        "--no-check-certificates",
        "--geo-bypass",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    ]

    cookie_path = config.get_youtube_cookies_path()
    if cookie_path:
        log.info("Using configured YouTube cookies file")
        args.extend(["--cookies", str(cookie_path)])

    return args


def parse_youtube_error(stderr_text: str) -> str:
    """
    Parse yt-dlp output/stderr to produce clean, actionable, user-friendly error messages.
    Never exposes internal system paths, tokens, or raw cookies.
    """
    lower = (stderr_text or "").lower()

    # 1. Private video
    if "private video" in lower or "private" in lower:
        return "This video is private and cannot be accessed."

    # 2. Unavailable / removed
    if "unavailable" in lower or "not available" in lower or "removed" in lower or "does not exist" in lower:
        return "This video is unavailable or has been removed."

    # 3. Geo restriction
    if "country" in lower or "region" in lower or "geographic" in lower or "geo" in lower:
        return "This video is not available in the server's geographic region."

    # 4. Members only
    if "members-only" in lower or "join this channel" in lower or "payment" in lower:
        return "This video is available to channel members only."

    # 5. Live stream
    if "live event" in lower or "is live" in lower:
        return "Live streams cannot be processed while live. Please provide an on-demand video URL."

    # 6. Bot detection
    if "bot" in lower or "automated queries" in lower:
        return (
            "YouTube has restricted access from this server IP (bot detection). "
            "Configure YouTube cookies in backend settings (YOUTUBE_COOKIES_FILE or YOUTUBE_COOKIES_TEXT) or try another public video."
        )

    # 7. Age restriction or authentication required
    if "sign in" in lower or "age" in lower or "login" in lower or "account" in lower or "authentication" in lower:
        return (
            "YouTube requires authentication or sign-in for this video on this server. "
            "Configure YouTube cookies in backend settings (YOUTUBE_COOKIES_FILE or YOUTUBE_COOKIES_TEXT) or try another public video."
        )

    # 8. Rate limiting
    if "429" in lower or "too many requests" in lower or "rate" in lower:
        return "YouTube is temporarily rate-limiting requests. Please try again in a few minutes or configure cookies."

    # 9. Forbidden
    if "403" in lower or "forbidden" in lower:
        return "Access forbidden by YouTube. Configure YouTube cookies or try another video."

    return "Unable to access this YouTube video. Please verify the URL or try another public video."


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
    Raises RuntimeError for unavailable/private/authentication-required videos.
    """
    if not is_valid_youtube_url(url):
        raise ValueError("Invalid YouTube URL")

    video_id = extract_video_id(url)
    log.info("Fetching metadata for video_id=%s", video_id)

    cmd = get_ytdlp_base_args() + [
        "--dump-json",
        "--no-playlist",
        "--no-download",
        url,
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=45,
        )
    except FileNotFoundError:
        raise RuntimeError("yt-dlp is not installed. Please install it: pip install yt-dlp")
    except subprocess.TimeoutExpired:
        raise RuntimeError("Timed out while fetching video metadata from YouTube.")

    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace")
        log.warning("yt-dlp metadata error: %s", stderr)
        friendly_error = parse_youtube_error(stderr)
        raise RuntimeError(friendly_error)

    try:
        info = json.loads(result.stdout.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        raise RuntimeError("Failed to parse video metadata from YouTube response.")

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
