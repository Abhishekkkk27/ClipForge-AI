/**
 * ClipForge AI — TypeScript Types
 * Mirrors backend Pydantic/SQLAlchemy models.
 */

export type JobStatus =
  | "queued"
  | "downloading"
  | "extracting_audio"
  | "transcribing"
  | "analyzing"
  | "generating_clips"
  | "adding_subtitles"
  | "completed"
  | "failed";

export type SubtitleStyle = "bold" | "minimal" | "karaoke";
export type AspectRatio = "9:16" | "16:9" | "1:1";
export type ClipDuration = 15 | 30 | 45 | 60;

export interface Job {
  id: string;
  youtube_url: string;
  video_id: string | null;
  video_title: string | null;
  video_duration: number | null;
  video_thumbnail: string | null;
  channel_name: string | null;
  clip_duration: number;
  num_clips: number;
  aspect_ratio: string;
  subtitle_style: string;
  status: JobStatus;
  progress: number;
  stage: string | null;
  error_message: string | null;
  created_at: string | null;
  updated_at: string | null;
  clip_count: number;
}

export interface Clip {
  id: string;
  job_id: string;
  clip_number: number;
  start_time: number;
  end_time: number;
  duration: number;
  score: number | null;
  reason: string | null;
  file_path: string | null;
  thumbnail_path: string | null;
  created_at: string | null;
}

export interface VideoMetadata {
  video_id: string;
  title: string;
  duration: number;
  thumbnail: string | null;
  channel: string | null;
  view_count: number | null;
  upload_date: string | null;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: {
    code: string;
    message: string;
  } | null;
}

export interface CreateJobRequest {
  youtube_url: string;
  clip_duration: number;
  num_clips: number;
  aspect_ratio: string;
  subtitle_style: string;
}

export interface HealthCheck {
  status: "healthy" | "degraded";
  version: string;
  checks: {
    ffmpeg: "ok" | "missing";
    yt_dlp: "ok" | "missing";
    whisper: "ok" | "missing";
  };
}

export interface ProgressEvent {
  progress: number;
  stage: string;
  done?: boolean;
}
