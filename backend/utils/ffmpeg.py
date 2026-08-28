"""
ClipForge AI — FFmpeg subprocess wrapper
All FFmpeg calls go through this module so we never exec shell strings.
"""

import subprocess
import shutil
import os
from pathlib import Path
from typing import List, Optional
from backend.utils.logger import get_logger

log = get_logger("ffmpeg")

# Common Windows FFmpeg install locations to check when not on PATH
_WIN_FALLBACK_DIRS = [
    # winget / Gyan.FFmpeg
    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Links",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages",
    Path("C:/Program Files/ffmpeg/bin"),
    Path("C:/ffmpeg/bin"),
    Path("C:/tools/ffmpeg/bin"),
]


def _find_binary(name: str) -> Optional[str]:
    """Find a binary on PATH or in common Windows install locations."""
    # 1. Check PATH first
    found = shutil.which(name)
    if found:
        return found

    # 2. Search winget packages directory recursively (limited depth)
    winget_packages = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
    if winget_packages.exists():
        for pkg_dir in winget_packages.iterdir():
            if "ffmpeg" in pkg_dir.name.lower() or "Gyan" in pkg_dir.name:
                for match in pkg_dir.rglob(f"{name}.exe"):
                    if "bin" in match.parts:
                        log.debug("Found %s via winget at: %s", name, match)
                        return str(match)

    # 3. Check explicit fallback dirs
    for d in _WIN_FALLBACK_DIRS:
        candidate = d / f"{name}.exe"
        if candidate.exists():
            return str(candidate)

    return None


def ffmpeg_path() -> str:
    """Find ffmpeg binary; raise if missing."""
    path = _find_binary("ffmpeg")
    if not path:
        raise RuntimeError(
            "FFmpeg not found. Install FFmpeg and ensure it is on your PATH."
        )
    return path


def ffprobe_path() -> str:
    path = _find_binary("ffprobe")
    if not path:
        raise RuntimeError("FFprobe not found. Install FFmpeg (includes ffprobe).")
    return path


def run_ffmpeg(args: List[str], timeout: int = 3600) -> subprocess.CompletedProcess:
    """
    Run ffmpeg with the given argument list.
    Raises subprocess.CalledProcessError on failure.
    """
    cmd = [ffmpeg_path()] + args
    log.debug("Running: %s", " ".join(str(a) for a in cmd))
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace")
        log.error("FFmpeg failed (rc=%d):\n%s", result.returncode, stderr)
        raise subprocess.CalledProcessError(result.returncode, cmd, stderr=stderr)
    return result


def run_ffprobe(args: List[str]) -> str:
    """Run ffprobe and return stdout as string."""
    cmd = [ffprobe_path()] + args
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )
    return result.stdout.decode("utf-8", errors="replace")


def get_video_info(video_path: Path) -> dict:
    """Return basic info (duration, width, height) for a video file."""
    import json
    out = run_ffprobe([
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        str(video_path),
    ])
    data = json.loads(out)
    info = {"duration": 0.0, "width": 0, "height": 0}
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            info["width"] = int(stream.get("width", 0))
            info["height"] = int(stream.get("height", 0))
    fmt = data.get("format", {})
    info["duration"] = float(fmt.get("duration", 0))
    return info
