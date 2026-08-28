"""
ClipForge AI — Clip Selection
Builds ~30-second windows around high-scoring moments.
Handles overlap detection and de-duplication.
"""

from dataclasses import dataclass
from typing import List, Optional
from backend.services.transcription import TranscriptSegment
from backend.services.highlight_detection import HighlightCandidate
from backend.utils.logger import get_logger

log = get_logger("clip_generator")


@dataclass
class ClipWindow:
    clip_number: int
    start_time: float
    end_time: float
    duration: float
    score: float           # 0–100
    reason: str
    anchor_text: str       # The key sentence that anchored this clip


def select_clips(
    segments: List[TranscriptSegment],
    candidates: List[HighlightCandidate],
    target_duration: float = 30.0,
    num_clips: int = 5,
    video_duration: float = 0.0,
) -> List[ClipWindow]:
    """
    Build non-overlapping clip windows around the top-scoring candidates.
    Returns sorted list of ClipWindows (by start_time).
    """
    if not candidates:
        log.warning("No highlight candidates provided; using uniform selection.")
        return _uniform_selection(segments, target_duration, num_clips, video_duration)

    # Sort by combined score descending
    ranked = sorted(candidates, key=lambda c: c.score.combined_score, reverse=True)

    selected: List[ClipWindow] = []
    used_ranges: List[tuple[float, float]] = []

    for candidate in ranked:
        if len(selected) >= num_clips:
            break

        # Build a window around the anchor sentence
        window_start, window_end = _build_window(
            segments=segments,
            anchor_start=candidate.start_time,
            anchor_end=candidate.end_time,
            target_duration=target_duration,
            video_duration=video_duration,
        )

        # Overlap check — reject if >50% overlap with already selected clips
        if _has_significant_overlap(window_start, window_end, used_ranges):
            log.debug(
                "Skipping overlapping candidate at %.1fs–%.1fs",
                window_start, window_end,
            )
            continue

        duration = round(window_end - window_start, 2)
        score_0_100 = round(min(candidate.score.combined_score * 100, 100), 1)

        selected.append(ClipWindow(
            clip_number=len(selected) + 1,
            start_time=round(window_start, 2),
            end_time=round(window_end, 2),
            duration=duration,
            score=score_0_100,
            reason=candidate.reason,
            anchor_text=candidate.text[:200],
        ))
        used_ranges.append((window_start, window_end))

    # If we didn't get enough clips, pad with uniform selection
    if len(selected) < num_clips and video_duration > 0:
        extra = _uniform_selection(
            segments, target_duration,
            num_clips - len(selected),
            video_duration,
            exclude_ranges=used_ranges,
        )
        for i, clip in enumerate(extra):
            clip.clip_number = len(selected) + i + 1
            selected.append(clip)
            used_ranges.append((clip.start_time, clip.end_time))

    # Re-number and sort by start time
    selected.sort(key=lambda c: c.start_time)
    for i, clip in enumerate(selected):
        clip.clip_number = i + 1

    log.info("Selected %d clips", len(selected))
    return selected


def _build_window(
    segments: List[TranscriptSegment],
    anchor_start: float,
    anchor_end: float,
    target_duration: float,
    video_duration: float,
) -> tuple[float, float]:
    """
    Expand a window around [anchor_start, anchor_end] to ~target_duration
    without cutting mid-sentence.
    """
    half = target_duration / 2.0
    needed_before = half
    needed_after = target_duration - (anchor_end - anchor_start) - needed_before

    # Try to start slightly before the anchor
    start = max(0.0, anchor_start - min(needed_before, 8.0))
    end = start + target_duration

    if video_duration > 0:
        end = min(end, video_duration)
        start = max(0.0, end - target_duration)

    # Snap to nearest segment boundary to avoid mid-sentence cuts
    start = _snap_to_segment_start(segments, start)
    end = _snap_to_segment_end(segments, end)

    # Ensure minimum 15 seconds
    if end - start < 15.0 and video_duration > 15.0:
        end = min(start + target_duration, video_duration)

    return start, end


def _snap_to_segment_start(segments: List[TranscriptSegment], t: float) -> float:
    """Snap time t to the start of the nearest segment within ±3 seconds."""
    best = t
    best_dist = float("inf")
    for seg in segments:
        dist = abs(seg.start - t)
        if dist < best_dist and dist < 3.0:
            best_dist = dist
            best = seg.start
    return best


def _snap_to_segment_end(segments: List[TranscriptSegment], t: float) -> float:
    """Snap time t to the end of the nearest segment within ±3 seconds."""
    best = t
    best_dist = float("inf")
    for seg in segments:
        dist = abs(seg.end - t)
        if dist < best_dist and dist < 3.0:
            best_dist = dist
            best = seg.end
    return best


def _has_significant_overlap(
    start: float,
    end: float,
    used: List[tuple[float, float]],
    threshold: float = 0.5,
) -> bool:
    """Return True if [start, end] overlaps >threshold fraction with any used range."""
    new_dur = end - start
    for u_start, u_end in used:
        overlap = max(0.0, min(end, u_end) - max(start, u_start))
        if new_dur > 0 and overlap / new_dur > threshold:
            return True
    return False


def _uniform_selection(
    segments: List[TranscriptSegment],
    target_duration: float,
    num_clips: int,
    video_duration: float,
    exclude_ranges: Optional[List[tuple[float, float]]] = None,
) -> List[ClipWindow]:
    """Evenly space clips across the video as a fallback."""
    if video_duration <= 0 or not segments:
        return []

    exclude_ranges = exclude_ranges or []
    clips = []
    interval = video_duration / (num_clips + 1)

    for i in range(1, num_clips + 1):
        mid = interval * i
        start = max(0.0, mid - target_duration / 2)
        end = min(video_duration, start + target_duration)
        start = max(0.0, end - target_duration)

        if _has_significant_overlap(start, end, exclude_ranges):
            continue

        clips.append(ClipWindow(
            clip_number=i,
            start_time=round(start, 2),
            end_time=round(end, 2),
            duration=round(end - start, 2),
            score=30.0,  # Low default score for fallback clips
            reason="Selected as a representative segment from this section of the video.",
            anchor_text="",
        ))

    return clips
