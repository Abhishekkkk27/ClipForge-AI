"""
ClipForge AI — Subtitle Generation
Converts Whisper word-level timestamps into styled ASS subtitle files
for burning into video via FFmpeg.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from backend.services.transcription import TranscriptSegment
from backend.utils.logger import get_logger

log = get_logger("subtitles")

# ─── Style Definitions ─────────────────────────────────────────────────────────

SUBTITLE_STYLES = {
    "bold": {
        "fontname": "Arial",
        "fontsize": 72,
        "primary_colour": "&H00FFFFFF",  # white
        "outline_colour": "&H00000000",  # black outline
        "back_colour": "&H00000000",
        "bold": -1,
        "italic": 0,
        "underline": 0,
        "outline": 4,
        "shadow": 2,
        "alignment": 2,          # bottom-center
        "margin_v": 120,
    },
    "minimal": {
        "fontname": "Arial",
        "fontsize": 60,
        "primary_colour": "&H00FFFFFF",
        "outline_colour": "&H80000000",  # semi-transparent black shadow
        "back_colour": "&H00000000",
        "bold": 0,
        "italic": 0,
        "underline": 0,
        "outline": 1,
        "shadow": 3,
        "alignment": 2,
        "margin_v": 120,
    },
    "karaoke": {
        "fontname": "Arial",
        "fontsize": 72,
        "primary_colour": "&H00FFFFFF",
        "secondary_colour": "&H0000FFFF",  # yellow highlight for karaoke
        "outline_colour": "&H00000000",
        "back_colour": "&H00000000",
        "bold": -1,
        "italic": 0,
        "underline": 0,
        "outline": 4,
        "shadow": 2,
        "alignment": 2,
        "margin_v": 120,
    },
}


@dataclass
class SubtitleChunk:
    start: float
    end: float
    text: str


def _chunk_words(
    segments: List[TranscriptSegment],
    clip_start: float,
    clip_end: float,
    words_per_chunk: int = 4,
) -> List[SubtitleChunk]:
    """
    Break words into small subtitle chunks for short-form style.
    Adjusts timestamps relative to clip start.
    """
    # Collect all words in the clip window
    all_words: List[Dict[str, Any]] = []
    for seg in segments:
        if seg.end < clip_start - 0.5 or seg.start > clip_end + 0.5:
            continue
        if seg.words:
            for w in seg.words:
                if clip_start - 0.5 <= w["start"] <= clip_end + 0.5:
                    all_words.append(w)
        else:
            # No word timestamps — use segment as one chunk
            if clip_start <= seg.start <= clip_end:
                all_words.append({
                    "word": seg.text,
                    "start": seg.start,
                    "end": seg.end,
                })

    if not all_words:
        return []

    chunks: List[SubtitleChunk] = []
    i = 0
    while i < len(all_words):
        group = all_words[i:i + words_per_chunk]
        text = " ".join(w["word"].strip() for w in group)
        start = group[0]["start"] - clip_start
        end = group[-1]["end"] - clip_start
        start = max(0.0, start)
        end = max(start + 0.1, end)
        chunks.append(SubtitleChunk(start=start, end=end, text=text.strip()))
        i += words_per_chunk

    return chunks


def _format_ass_time(seconds: float) -> str:
    """Convert seconds to ASS timestamp format H:MM:SS.cs"""
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def generate_ass_subtitle(
    segments: List[TranscriptSegment],
    clip_start: float,
    clip_end: float,
    style: str = "bold",
    output_path: Optional[Path] = None,
) -> str:
    """
    Generate an ASS subtitle file content for a clip window.
    Returns the ASS content as a string.
    If output_path is given, also writes the file.
    """
    style_def = SUBTITLE_STYLES.get(style, SUBTITLE_STYLES["bold"])
    chunks = _chunk_words(segments, clip_start, clip_end)

    # ── ASS header ────────────────────────────────────────────────────────────
    secondary = style_def.get("secondary_colour", "&H000000FF")
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{style_def["fontname"]},{style_def["fontsize"]},{style_def["primary_colour"]},{secondary},{style_def["outline_colour"]},{style_def["back_colour"]},{style_def["bold"]},{style_def["italic"]},{style_def["underline"]},0,100,100,0,0,1,{style_def["outline"]},{style_def["shadow"]},{style_def["alignment"]},60,60,{style_def["margin_v"]},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    lines = []
    for chunk in chunks:
        start_str = _format_ass_time(chunk.start)
        end_str = _format_ass_time(chunk.end)
        text = chunk.text.replace("\n", "\\N")

        if style == "karaoke":
            # Build karaoke-style tags per word
            # Simple approach: highlight current word
            text = "{\\k0}" + text

        lines.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text}")

    content = header + "\n".join(lines) + "\n"

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        log.info("Subtitle written to: %s", output_path)

    return content


def generate_srt_subtitle(
    segments: List[TranscriptSegment],
    clip_start: float,
    clip_end: float,
    output_path: Optional[Path] = None,
) -> str:
    """Generate SRT format subtitles as a fallback."""
    chunks = _chunk_words(segments, clip_start, clip_end)

    def fmt_srt(t: float) -> str:
        t = max(0.0, t)
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int((t % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    lines = []
    for i, chunk in enumerate(chunks, 1):
        lines.append(str(i))
        lines.append(f"{fmt_srt(chunk.start)} --> {fmt_srt(chunk.end)}")
        lines.append(chunk.text)
        lines.append("")

    content = "\n".join(lines)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

    return content
