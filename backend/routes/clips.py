"""
ClipForge AI — Clips API Routes
GET    /api/clips/{id}           Get clip info
GET    /api/clips/{id}/download  Download clip file
GET    /api/clips/{id}/thumbnail Download clip thumbnail
GET    /api/clips/{id}/preview   Serve clip for in-browser preview
POST   /api/validate-url         Validate a YouTube URL (no download)
POST   /api/metadata             Fetch video metadata
"""

import zipfile
import io
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Clip, Job
from backend.utils.validation import is_valid_youtube_url, extract_video_id
from backend.services.youtube import get_video_metadata

router = APIRouter()


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


@router.get("/api/clips/{clip_id}")
def get_clip(clip_id: str, db: Session = Depends(get_db)):
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    return {"success": True, "data": _clip_to_dict(clip), "error": None}


@router.get("/api/clips/{clip_id}/download")
def download_clip(clip_id: str, db: Session = Depends(get_db)):
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    if not clip.file_path:
        raise HTTPException(status_code=404, detail="Clip file not ready")

    path = Path(clip.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Clip file missing from disk")

    filename = f"clipforge_clip_{clip.clip_number:02d}.mp4"
    return FileResponse(
        path=str(path),
        media_type="video/mp4",
        filename=filename,
    )


@router.get("/api/clips/{clip_id}/preview")
def preview_clip(clip_id: str, db: Session = Depends(get_db)):
    """Serve clip for HTML5 video player (supports range requests)."""
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip or not clip.file_path:
        raise HTTPException(status_code=404, detail="Clip not found")
    path = Path(clip.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Clip file missing")
    return FileResponse(path=str(path), media_type="video/mp4")


@router.get("/api/clips/{clip_id}/thumbnail")
def get_thumbnail(clip_id: str, db: Session = Depends(get_db)):
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip or not clip.thumbnail_path:
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    path = Path(clip.thumbnail_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail missing")
    return FileResponse(path=str(path), media_type="image/jpeg")


@router.get("/api/jobs/{job_id}/download-all")
def download_all_clips(job_id: str, db: Session = Depends(get_db)):
    """Download all clips for a job as a ZIP archive."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    clips = db.query(Clip).filter(Clip.job_id == job_id).order_by(Clip.clip_number).all()
    if not clips:
        raise HTTPException(status_code=404, detail="No clips found for this job")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for clip in clips:
            if clip.file_path:
                p = Path(clip.file_path)
                if p.exists():
                    arcname = f"clipforge_clip_{clip.clip_number:02d}.mp4"
                    zf.write(p, arcname)

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=clipforge_export.zip"},
    )


# ─── URL Validation & Metadata Endpoints ──────────────────────────────────────

class ValidateUrlRequest(BaseModel):
    url: str


class MetadataRequest(BaseModel):
    url: str


@router.post("/api/validate-url")
def validate_url(body: ValidateUrlRequest):
    url = body.url.strip()
    valid = is_valid_youtube_url(url)
    video_id = extract_video_id(url) if valid else None
    if valid:
        return {"success": True, "data": {"valid": True, "video_id": video_id}, "error": None}
    return {
        "success": False,
        "data": {"valid": False},
        "error": {"code": "INVALID_URL", "message": "Please enter a valid YouTube URL."},
    }


@router.post("/api/metadata")
def fetch_metadata_endpoint(body: MetadataRequest):
    """Fetch video metadata without creating a job."""
    url = body.url.strip()
    if not is_valid_youtube_url(url):
        return {
            "success": False,
            "data": None,
            "error": {"code": "INVALID_URL", "message": "Please enter a valid YouTube URL."},
        }
    try:
        meta = get_video_metadata(url)
        return {
            "success": True,
            "data": {
                "video_id": meta.video_id,
                "title": meta.title,
                "duration": meta.duration,
                "thumbnail": meta.thumbnail,
                "channel": meta.channel,
                "view_count": meta.view_count,
                "upload_date": meta.upload_date,
            },
            "error": None,
        }
    except (ValueError, RuntimeError) as e:
        return {
            "success": False,
            "data": None,
            "error": {"code": "METADATA_ERROR", "message": str(e)},
        }
