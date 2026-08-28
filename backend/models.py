"""
ClipForge AI — SQLAlchemy ORM models
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    youtube_url: Mapped[str] = mapped_column(Text, nullable=False)
    video_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    video_title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    video_duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    video_thumbnail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    channel_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Settings chosen by user
    clip_duration: Mapped[int] = mapped_column(Integer, default=30)
    num_clips: Mapped[int] = mapped_column(Integer, default=5)
    aspect_ratio: Mapped[str] = mapped_column(String(10), default="9:16")
    subtitle_style: Mapped[str] = mapped_column(String(20), default="bold")

    # Processing state
    status: Mapped[str] = mapped_column(String(30), default="queued")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    stage: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    clips: Mapped[list["Clip"]] = relationship("Clip", back_populates="job", cascade="all, delete-orphan")
    transcripts: Mapped[list["Transcript"]] = relationship("Transcript", back_populates="job", cascade="all, delete-orphan")


class Clip(Base):
    __tablename__ = "clips"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), nullable=False)
    clip_number: Mapped[int] = mapped_column(Integer, nullable=False)

    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    duration: Mapped[float] = mapped_column(Float, nullable=False)

    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    file_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job: Mapped["Job"] = relationship("Job", back_populates="clips")


class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), nullable=False)
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job: Mapped["Job"] = relationship("Job", back_populates="transcripts")
