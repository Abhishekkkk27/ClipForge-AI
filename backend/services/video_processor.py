"""
ClipForge AI — Video Processor
Handles FFmpeg clip trimming, 9:16 cropping, scaling, subtitle burning,
thumbnail generation, and final export.
"""

from pathlib import Path
from typing import List, Optional
import subprocess

from backend import config
from backend.services.transcription import TranscriptSegment
from backend.services.clip_generator import ClipWindow
from backend.services.subtitles import generate_ass_subtitle
from backend.utils.ffmpeg import run_ffmpeg, get_video_info
from backend.utils.logger import get_logger

log = get_logger("video_processor")


def process_clip(
    video_path: Path,
    clip: ClipWindow,
    segments: List[TranscriptSegment],
    job_id: str,
    subtitle_style: str = "bold",
    output_width: int = 1080,
    output_height: int = 1920,
) -> tuple[Path, Path]:
    """
    Process a single clip:
      1. Trim
      2. Crop/scale to 9:16
      3. Burn subtitles
      4. Encode to MP4
      5. Generate thumbnail

    Returns (clip_path, thumbnail_path).
    """
    clips_dir = config.CLIPS_DIR / job_id
    clips_dir.mkdir(parents=True, exist_ok=True)

    clip_filename = f"clip_{clip.clip_number:03d}.mp4"
    clip_path = clips_dir / clip_filename
    subtitle_path = clips_dir / f"clip_{clip.clip_number:03d}.ass"
    thumbnail_path = config.THUMBNAILS_DIR / job_id / f"clip_{clip.clip_number:03d}.jpg"
    thumbnail_path.parent.mkdir(parents=True, exist_ok=True)

    log.info("[JOB %s] Processing clip %d (%.1fs–%.1fs)", job_id, clip.clip_number, clip.start_time, clip.end_time)

    # ── Get video dimensions ───────────────────────────────────────────────────
    info = get_video_info(video_path)
    src_w = info.get("width", 1920)
    src_h = info.get("height", 1080)

    # ── Generate subtitle file ─────────────────────────────────────────────────
    generate_ass_subtitle(
        segments=segments,
        clip_start=clip.start_time,
        clip_end=clip.end_time,
        style=subtitle_style,
        output_path=subtitle_path,
    )

    # ── Build FFmpeg filter graph ──────────────────────────────────────────────
    duration = clip.end_time - clip.start_time
    crop_filter = _build_crop_filter(src_w, src_h, output_width, output_height)

    # Escape ASS path for Windows (backslashes → forward slashes)
    ass_path_escaped = str(subtitle_path).replace("\\", "/").replace(":", "\\:")

    filter_complex = f"{crop_filter},scale={output_width}:{output_height}:flags=lanczos,ass='{ass_path_escaped}'"

    # ── Run FFmpeg ─────────────────────────────────────────────────────────────
    run_ffmpeg([
        "-y",
        "-ss", str(clip.start_time),
        "-t", str(round(duration, 3)),
        "-i", str(video_path),
        "-vf", filter_complex,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        "-avoid_negative_ts", "make_zero",
        str(clip_path),
    ])

    log.info("[JOB %s] Clip %d encoded: %s", job_id, clip.clip_number, clip_path)

    # ── Generate thumbnail ─────────────────────────────────────────────────────
    try:
        _generate_thumbnail(clip_path, thumbnail_path)
    except Exception as e:
        log.warning("[JOB %s] Thumbnail failed for clip %d: %s", job_id, clip.clip_number, e)
        thumbnail_path = None

    return clip_path, thumbnail_path


def _build_crop_filter(src_w: int, src_h: int, out_w: int, out_h: int) -> str:
    """
    Build an ffmpeg crop filter to produce a 9:16 (portrait) output
    from the source video using center crop.
    """
    target_ratio = out_w / out_h  # 9/16 = 0.5625

    if src_h == 0 or src_w == 0:
        return f"scale={out_w}:{out_h}"

    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        # Source is wider than 9:16 → crop width (center)
        crop_h = src_h
        crop_w = int(src_h * target_ratio)
        x = (src_w - crop_w) // 2
        y = 0
    else:
        # Source is taller than 9:16 → crop height (center)
        crop_w = src_w
        crop_h = int(src_w / target_ratio)
        x = 0
        y = (src_h - crop_h) // 2

    return f"crop={crop_w}:{crop_h}:{x}:{y}"


def _generate_thumbnail(clip_path: Path, thumbnail_path: Path) -> None:
    """Extract a single frame at t=1s as a JPEG thumbnail."""
    run_ffmpeg([
        "-y",
        "-ss", "1",
        "-i", str(clip_path),
        "-frames:v", "1",
        "-q:v", "4",
        "-vf", "scale=270:480",
        str(thumbnail_path),
    ])
