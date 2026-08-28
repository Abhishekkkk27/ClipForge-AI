"""
ClipForge AI — Jobs API Routes
POST   /api/jobs             Create job
GET    /api/jobs             List jobs
GET    /api/jobs/{id}        Get job
DELETE /api/jobs/{id}        Delete job + files
GET    /api/jobs/{id}/stream SSE progress stream
GET    /api/jobs/{id}/clips  Get clips for job
"""

import uuid
import shutil
import json
import asyncio
from datetime import datetime
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Job, Clip
from backend import config
from backend.utils.validation import is_valid_youtube_url
from backend.workers.processor import start_processing_job, get_progress
from backend.services.youtube import get_video_metadata

router = APIRouter()


# ─── Request / Response Schemas ───────────────────────────────────────────────

class CreateJobRequest(BaseModel):
    youtube_url: str
    clip_duration: int = 30
    num_clips: int = 5
    aspect_ratio: str = "9:16"
    subtitle_style: str = "bold"

    @field_validator("youtube_url")
    @classmethod
    def validate_url(cls, v):
        if not is_valid_youtube_url(v.strip()):
            raise ValueError("Please enter a valid YouTube URL.")
        return v.strip()

    @field_validator("clip_duration")
    @classmethod
    def validate_duration(cls, v):
        if v not in [15, 30, 45, 60]:
            raise ValueError("Clip duration must be 15, 30, 45, or 60 seconds.")
        return v

    @field_validator("num_clips")
    @classmethod
    def validate_num_clips(cls, v):
        if not 1 <= v <= 20:
            raise ValueError("Number of clips must be between 1 and 20.")
        return v

    @field_validator("subtitle_style")
    @classmethod
    def validate_style(cls, v):
        if v not in ["bold", "minimal", "karaoke"]:
            raise ValueError("Subtitle style must be bold, minimal, or karaoke.")
        return v


def _job_to_dict(job: Job) -> dict:
    return {
        "id": job.id,
        "youtube_url": job.youtube_url,
        "video_id": job.video_id,
        "video_title": job.video_title,
        "video_duration": job.video_duration,
        "video_thumbnail": job.video_thumbnail,
        "channel_name": job.channel_name,
        "clip_duration": job.clip_duration,
        "num_clips": job.num_clips,
        "aspect_ratio": job.aspect_ratio,
        "subtitle_style": job.subtitle_style,
        "status": job.status,
        "progress": job.progress,
        "stage": job.stage,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        "clip_count": len(job.clips) if job.clips else 0,
    }


def _clip_to_dict(clip: Clip) -> dict:
    return {
        "id": clip.id,
        "job_id": clip.job_id,
        "clip_number": clip.clip_number,
        "start_time": clip.start_time,
        "end_time": clip.end_time,
        "duration": clip.duration,
        "score": clip.score,
        "reason": clip.reason,
        "file_path": clip.file_path,
        "thumbnail_path": clip.thumbnail_path,
        "created_at": clip.created_at.isoformat() if clip.created_at else None,
    }


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/api/jobs")
def create_job(body: CreateJobRequest, db: Session = Depends(get_db)):
    """Create a new processing job and start background processing."""
    job_id = str(uuid.uuid4())

    job = Job(
        id=job_id,
        youtube_url=body.youtube_url,
        clip_duration=body.clip_duration,
        num_clips=body.num_clips,
        aspect_ratio=body.aspect_ratio,
        subtitle_style=body.subtitle_style,
        status="queued",
        progress=0,
        stage="queued",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Launch background processing
    start_processing_job(
        job_id=job_id,
        youtube_url=body.youtube_url,
        clip_duration=body.clip_duration,
        num_clips=body.num_clips,
        subtitle_style=body.subtitle_style,
        aspect_ratio=body.aspect_ratio,
    )

    return {"success": True, "data": _job_to_dict(job), "error": None}


@router.get("/api/jobs")
def list_jobs(db: Session = Depends(get_db)):
    """List all jobs ordered by creation date (newest first)."""
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    return {
        "success": True,
        "data": [_job_to_dict(j) for j in jobs],
        "error": None,
    }


@router.get("/api/jobs/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)):
    """Get job status, merging in-memory progress with DB data."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail={"success": False, "data": None, "error": {"code": "NOT_FOUND", "message": "Job not found."}})

    job_dict = _job_to_dict(job)

    # Merge live progress for in-flight jobs
    if job.status not in ("completed", "failed"):
        live = get_progress(job_id)
        if live:
            job_dict["progress"] = live.get("progress", job.progress)
            job_dict["stage"] = live.get("stage", job.stage)

    return {"success": True, "data": job_dict, "error": None}


@router.get("/api/jobs/{job_id}/stream")
async def stream_job_progress(job_id: str, db: Session = Depends(get_db)):
    """SSE endpoint: streams job progress updates until completion."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        last_progress = -1
        for _ in range(600):  # max 10 min
            live = get_progress(job_id)
            progress = live.get("progress", 0)
            stage = live.get("stage", "queued")

            if progress != last_progress:
                last_progress = progress
                data = json.dumps({"progress": progress, "stage": stage})
                yield f"data: {data}\n\n"

            if stage in ("completed", "failed"):
                yield f"data: {json.dumps({'progress': progress, 'stage': stage, 'done': True})}\n\n"
                break

            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/api/jobs/{job_id}/clips")
def get_job_clips(job_id: str, db: Session = Depends(get_db)):
    """Get all clips for a job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    clips = db.query(Clip).filter(Clip.job_id == job_id).order_by(Clip.clip_number).all()
    return {
        "success": True,
        "data": [_clip_to_dict(c) for c in clips],
        "error": None,
    }


@router.delete("/api/jobs/{job_id}")
def delete_job(job_id: str, db: Session = Depends(get_db)):
    """Delete a job and all its generated files."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Delete files from disk
    for dir_path in [
        config.CLIPS_DIR / job_id,
        config.THUMBNAILS_DIR / job_id,
        config.TRANSCRIPTS_DIR / job_id,
        config.AUDIO_DIR / job_id,
        config.DOWNLOADS_DIR / job_id,
    ]:
        if dir_path.exists():
            shutil.rmtree(dir_path, ignore_errors=True)

    db.delete(job)
    db.commit()

    return {"success": True, "data": {"deleted": job_id}, "error": None}


@router.get("/api/jobs/{job_id}/metadata")
def fetch_metadata(job_id: str, db: Session = Depends(get_db)):
    """Pre-fetch video metadata (called from frontend before job creation)."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"success": True, "data": _job_to_dict(job), "error": None}
