"""
ClipForge AI — Background Processing Worker
Runs the full pipeline in a daemon thread.
Architecture allows migration to Celery/RQ later.
"""

import uuid
import threading
import traceback
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

from backend import config
from backend.database import SessionLocal
from backend.models import Job, Clip, Transcript
from backend.services.youtube import get_video_metadata
from backend.services.downloader import download_video
from backend.services.audio import extract_audio
from backend.services.transcription import transcribe_audio
from backend.services.highlight_detection import RuleBasedHighlightDetector
from backend.services.clip_generator import select_clips
from backend.services.video_processor import process_clip
from backend.utils.logger import job_logger

# Thread-safe progress store: {job_id: {"stage": str, "progress": int}}
_progress: dict = {}
_lock = threading.Lock()


def get_progress(job_id: str) -> dict:
    with _lock:
        return _progress.get(job_id, {"stage": "queued", "progress": 0})


def _set_progress(job_id: str, stage: str, progress: int):
    with _lock:
        _progress[job_id] = {"stage": stage, "progress": progress}


def start_processing_job(
    job_id: str,
    youtube_url: str,
    clip_duration: int = 30,
    num_clips: int = 5,
    subtitle_style: str = "bold",
    aspect_ratio: str = "9:16",
) -> None:
    """Spawn a background thread to process the job."""
    thread = threading.Thread(
        target=_run_pipeline,
        args=(job_id, youtube_url, clip_duration, num_clips, subtitle_style, aspect_ratio),
        daemon=True,
        name=f"worker-{job_id[:8]}",
    )
    thread.start()


def _update_db_status(job_id: str, status: str, progress: int, stage: str, **kwargs):
    """Write job status to the database."""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = status
            job.progress = progress
            job.stage = stage
            job.updated_at = datetime.utcnow()
            for k, v in kwargs.items():
                if hasattr(job, k):
                    setattr(job, k, v)
            db.commit()
    finally:
        db.close()
    _set_progress(job_id, stage, progress)


def _run_pipeline(
    job_id: str,
    youtube_url: str,
    clip_duration: int,
    num_clips: int,
    subtitle_style: str,
    aspect_ratio: str,
):
    log = job_logger(job_id)
    log.info("Pipeline started for URL: %s", youtube_url)
    config.ensure_directories()

    video_path: Optional[Path] = None

    try:
        # ── Stage 1: Fetch Metadata ────────────────────────────────────────────
        _update_db_status(job_id, "downloading", 2, "fetching_metadata")
        log.info("Fetching video metadata")
        meta = get_video_metadata(youtube_url)
        _update_db_status(
            job_id, "downloading", 5, "fetching_metadata",
            video_title=meta.title,
            video_duration=meta.duration,
            video_thumbnail=meta.thumbnail,
            channel_name=meta.channel,
            video_id=meta.video_id,
        )
        log.info("Video: %s (%.0fs)", meta.title, meta.duration)

        # ── Stage 2: Download ──────────────────────────────────────────────────
        _update_db_status(job_id, "downloading", 10, "downloading")
        log.info("Downloading video")

        def dl_progress(pct: int, stage: str):
            mapped = 10 + int(pct * 0.25)  # 10%–35% of total progress
            _update_db_status(job_id, "downloading", mapped, "downloading")

        video_path = download_video(youtube_url, job_id, progress_callback=dl_progress)
        _update_db_status(job_id, "extracting_audio", 35, "extracting_audio")

        # ── Stage 3: Extract Audio ─────────────────────────────────────────────
        log.info("Extracting audio")
        audio_path = extract_audio(video_path, job_id)
        _update_db_status(job_id, "transcribing", 40, "transcribing")

        # ── Stage 4: Transcribe ────────────────────────────────────────────────
        log.info("Transcribing audio")
        segments, language, transcript_path = transcribe_audio(audio_path, job_id)
        log.info("Transcription complete: %d segments, lang=%s", len(segments), language)
        _update_db_status(job_id, "analyzing", 65, "analyzing")

        # Save transcript to DB
        db = SessionLocal()
        try:
            transcript_record = Transcript(
                id=str(uuid.uuid4()),
                job_id=job_id,
                language=language,
                file_path=str(transcript_path),
            )
            db.add(transcript_record)
            db.commit()
        finally:
            db.close()

        # ── Stage 5: Highlight Detection ───────────────────────────────────────
        log.info("Detecting highlights in %d segments", len(segments))
        detector = RuleBasedHighlightDetector()
        candidates = detector.score_segments(segments)
        log.info("Found %d highlight candidates", len(candidates))

        # ── Stage 6: Select Clips ──────────────────────────────────────────────
        _update_db_status(job_id, "generating_clips", 68, "selecting_clips")
        clips = select_clips(
            segments=segments,
            candidates=candidates,
            target_duration=clip_duration,
            num_clips=num_clips,
            video_duration=meta.duration,
        )
        log.info("Selected %d clips", len(clips))

        # ── Stage 7: Generate Each Clip ────────────────────────────────────────
        _update_db_status(job_id, "generating_clips", 70, "generating_clips")

        for i, clip_window in enumerate(clips):
            progress = 70 + int((i / len(clips)) * 25)
            _update_db_status(job_id, "adding_subtitles", progress, f"clip_{i+1}_of_{len(clips)}")
            log.info("Generating clip %d/%d", i + 1, len(clips))

            clip_path, thumb_path = process_clip(
                video_path=video_path,
                clip=clip_window,
                segments=segments,
                job_id=job_id,
                subtitle_style=subtitle_style,
                output_width=config.OUTPUT_WIDTH,
                output_height=config.OUTPUT_HEIGHT,
            )

            # Save clip to DB
            db = SessionLocal()
            try:
                clip_record = Clip(
                    id=str(uuid.uuid4()),
                    job_id=job_id,
                    clip_number=clip_window.clip_number,
                    start_time=clip_window.start_time,
                    end_time=clip_window.end_time,
                    duration=clip_window.duration,
                    score=clip_window.score,
                    reason=clip_window.reason,
                    file_path=str(clip_path) if clip_path else None,
                    thumbnail_path=str(thumb_path) if thumb_path else None,
                )
                db.add(clip_record)
                db.commit()
            finally:
                db.close()

        # ── Stage 8: Cleanup & Complete ────────────────────────────────────────
        log.info("Cleaning up temporary files")
        _cleanup_temp_files(job_id)

        _update_db_status(job_id, "completed", 100, "completed")
        log.info("Pipeline completed successfully. %d clips generated.", len(clips))

    except Exception as e:
        tb = traceback.format_exc()
        log.error("Pipeline failed: %s\n%s", e, tb)
        db = SessionLocal()
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.status = "failed"
                job.error_message = str(e)
                job.updated_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()
        _set_progress(job_id, "failed", 0)


def _cleanup_temp_files(job_id: str):
    """Remove temporary audio and download directories, keep final clips."""
    for temp_dir in [config.AUDIO_DIR / job_id, config.DOWNLOADS_DIR / job_id]:
        if temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                pass  # Non-fatal
