/**
 * ClipForge AI — Utility Functions
 */

import { JobStatus } from "./types";

/** Format seconds as MM:SS or HH:MM:SS */
export function formatDuration(seconds: number): string {
  if (!seconds || seconds <= 0) return "0:00";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) {
    return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  }
  return `${m}:${String(s).padStart(2, "0")}`;
}

/** Format a timestamp like "01:14" for display */
export function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

/** Human-readable job status labels */
export const STATUS_LABELS: Record<JobStatus, string> = {
  queued: "Queued",
  downloading: "Downloading",
  extracting_audio: "Extracting Audio",
  transcribing: "Transcribing",
  analyzing: "Analyzing",
  generating_clips: "Generating Clips",
  adding_subtitles: "Adding Subtitles",
  completed: "Completed",
  failed: "Failed",
};

/** Stage labels used in the progress UI */
export const STAGE_LABELS: Record<string, string> = {
  queued: "Waiting to start...",
  fetching_metadata: "Fetching video info...",
  downloading: "Downloading video...",
  extracting_audio: "Extracting audio...",
  transcribing: "Transcribing speech...",
  analyzing: "Analyzing content...",
  selecting_clips: "Selecting best moments...",
  generating_clips: "Creating clips...",
  adding_subtitles: "Adding subtitles...",
  completed: "Done!",
  failed: "Processing failed",
};

/** Get stage label, handling dynamic stage names like "clip_1_of_5" */
export function getStagLabel(stage: string | null): string {
  if (!stage) return "Processing...";
  if (stage in STAGE_LABELS) return STAGE_LABELS[stage];
  if (stage.startsWith("clip_")) return "Generating clips...";
  return stage.replace(/_/g, " ");
}

/** Map job status to color classes */
export function statusColor(status: JobStatus): string {
  switch (status) {
    case "completed": return "text-emerald-400";
    case "failed": return "text-red-400";
    case "queued": return "text-zinc-400";
    default: return "text-violet-400";
  }
}

export function statusBgColor(status: JobStatus): string {
  switch (status) {
    case "completed": return "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
    case "failed": return "bg-red-500/15 text-red-400 border-red-500/30";
    case "queued": return "bg-zinc-500/15 text-zinc-400 border-zinc-500/30";
    default: return "bg-violet-500/15 text-violet-400 border-violet-500/30";
  }
}

/** Score → color */
export function scoreColor(score: number): string {
  if (score >= 80) return "text-emerald-400";
  if (score >= 60) return "text-yellow-400";
  if (score >= 40) return "text-orange-400";
  return "text-red-400";
}

/** Format a relative date like "2 hours ago" */
export function timeAgo(dateStr: string | null): string {
  if (!dateStr) return "";
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

/** Clamp a number to [min, max] */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

/** Generate a consistent color from a string (for avatars etc.) */
export function stringToColor(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  return `hsl(${Math.abs(hash) % 360}, 70%, 60%)`;
}
