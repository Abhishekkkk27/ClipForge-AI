"""
ClipForge AI — YouTube URL Validation
"""

import re
from typing import Optional

# Patterns for all known YouTube URL formats
_YT_PATTERNS = [
    # Standard watch
    r"(?:https?://)?(?:www\.)?youtube\.com/watch\?(?:.*&)?v=([\w-]{11})",
    # Short URL
    r"(?:https?://)?youtu\.be/([\w-]{11})",
    # Shorts
    r"(?:https?://)?(?:www\.)?youtube\.com/shorts/([\w-]{11})",
    # Embed
    r"(?:https?://)?(?:www\.)?youtube\.com/embed/([\w-]{11})",
    # v/ format
    r"(?:https?://)?(?:www\.)?youtube\.com/v/([\w-]{11})",
]

_COMPILED = [re.compile(p) for p in _YT_PATTERNS]


def extract_video_id(url: str) -> Optional[str]:
    """Return the 11-character video ID from a YouTube URL, or None."""
    url = url.strip()
    for pattern in _COMPILED:
        m = pattern.search(url)
        if m:
            return m.group(1)
    return None


def is_valid_youtube_url(url: str) -> bool:
    """Return True if the URL is a recognised YouTube video URL."""
    return extract_video_id(url) is not None


def sanitize_filename(name: str) -> str:
    """Remove characters unsafe for filenames."""
    # Remove path separators and other dangerous chars
    cleaned = re.sub(r'[\\/:*?"<>|]', "_", name)
    # Collapse repeated underscores/spaces
    cleaned = re.sub(r"_+", "_", cleaned).strip("_").strip()
    return cleaned[:100] if cleaned else "video"
