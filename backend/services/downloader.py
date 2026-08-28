"""
ClipForge AI — Video Downloader
Downloads YouTube videos using yt-dlp with progress callbacks.
"""

import subprocess
import json
import re
from pathlib import Path
from typing import Callable, Optional, List

from backend import config
from backend.services.youtube import get_ytdlp_base_args, parse_youtube_error
from backend.utils.validation import sanitize_filename
from backend.utils.logger import get_logger

log = get_logger("downloader")


def download_video(
    url: str,
    job_id: str,
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> Path:
    """
    Download a YouTube video to the downloads directory.
    Returns the path of the downloaded file.
    progress_callback(percent: int, stage: str)
    """
    output_dir = config.DOWNLOADS_DIR / job_id
    output_dir.mkdir(parents=True, exist_ok=True)

    output_template = str(output_dir / "%(id)s.%(ext)s")

    cmd = get_ytdlp_base_args() + [
        "--no-playlist",
        "--format", config.VIDEO_FORMAT,
        "--merge-output-format", "mp4",
        "--output", output_template,
        "--no-part",
        "--no-mtime",
        "--progress",
        "--newline",
        url,
    ]

    log.info("[JOB %s] Starting download: %s", job_id, url)

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except FileNotFoundError:
        raise RuntimeError("yt-dlp is not installed. Please install it: pip install yt-dlp")

    last_percent = 0
    output_lines: List[str] = []
    for line in process.stdout:
        line = line.strip()
        if not line:
            continue
        output_lines.append(line)
        log.debug("[JOB %s] yt-dlp: %s", job_id, line)

        # Parse download percentage
        m = re.search(r"\[download\]\s+([\d.]+)%", line)
        if m and progress_callback:
            pct = min(int(float(m.group(1))), 99)
            if pct != last_percent:
                last_percent = pct
                progress_callback(pct, "downloading")

    process.wait()
    if process.returncode != 0:
        error_context = "\n".join(output_lines[-10:])
        log.warning("[JOB %s] Download failed. yt-dlp output:\n%s", job_id, error_context)
        friendly_error = parse_youtube_error(error_context)
        raise RuntimeError(friendly_error)

    # Find the downloaded file
    mp4_files = list(output_dir.glob("*.mp4"))
    if mp4_files:
        result = mp4_files[0]
        log.info("[JOB %s] Downloaded to: %s", job_id, result)
        return result

    # Fallback: any video file
    for ext in ["webm", "mkv", "avi", "mov"]:
        files = list(output_dir.glob(f"*.{ext}"))
        if files:
            return files[0]

    raise RuntimeError("Download completed but no video file was found.")
