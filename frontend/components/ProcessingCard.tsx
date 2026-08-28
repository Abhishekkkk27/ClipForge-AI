"use client";

import { Job } from "@/lib/types";
import { formatDuration, getStagLabel, statusBgColor } from "@/lib/utils";
import ProgressBar from "./ProgressBar";

const PIPELINE_STAGES = [
  { key: "fetching_metadata", label: "Fetching video info" },
  { key: "downloading", label: "Downloading video" },
  { key: "extracting_audio", label: "Extracting audio" },
  { key: "transcribing", label: "Transcribing speech" },
  { key: "analyzing", label: "Analyzing content" },
  { key: "selecting_clips", label: "Selecting best moments" },
  { key: "generating_clips", label: "Creating clips" },
  { key: "adding_subtitles", label: "Adding subtitles" },
  { key: "completed", label: "Completed" },
];

function stageIndex(stage: string | null): number {
  if (!stage) return -1;
  const normalised = stage.startsWith("clip_") ? "generating_clips" : stage;
  return PIPELINE_STAGES.findIndex((s) => s.key === normalised);
}

interface ProcessingCardProps {
  job: Job;
}

export default function ProcessingCard({ job }: ProcessingCardProps) {
  const currentIdx = stageIndex(job.stage);

  return (
    <div className="card p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start gap-4">
        {job.video_thumbnail && (
          <div className="flex-shrink-0 w-24 h-16 rounded-lg overflow-hidden">
            <img
              src={job.video_thumbnail}
              alt={job.video_title || "Video"}
              className="w-full h-full object-cover"
            />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <h2 className="font-bold text-base leading-snug" style={{ color: "var(--text-primary)" }}>
            {job.video_title || "Processing video..."}
          </h2>
          {job.video_duration && (
            <p className="text-sm mt-0.5" style={{ color: "var(--text-secondary)" }}>
              {job.channel_name && `${job.channel_name} · `}
              {formatDuration(job.video_duration)}
            </p>
          )}
          <div className="mt-2">
            <span
              className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border font-medium"
              style={statusBgColor(job.status) as React.CSSProperties}
            >
              {job.status !== "completed" && job.status !== "failed" && (
                <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
              )}
              {job.status === "completed" ? "✓ " : job.status === "failed" ? "✕ " : ""}
              {getStagLabel(job.stage)}
            </span>
          </div>
        </div>
      </div>

      {/* Progress bar */}
      {job.status !== "failed" && (
        <ProgressBar
          progress={job.progress}
          stage={getStagLabel(job.stage)}
        />
      )}

      {/* Error message */}
      {job.status === "failed" && job.error_message && (
        <div
          className="rounded-xl p-4"
          style={{ background: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.3)" }}
        >
          <div className="flex items-start gap-2">
            <span style={{ color: "#ef4444" }}>⚠</span>
            <div>
              <p className="text-sm font-semibold" style={{ color: "#ef4444" }}>Processing Failed</p>
              <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
                {job.error_message}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Stage checklist */}
      <div className="space-y-2">
        {PIPELINE_STAGES.map((stage, idx) => {
          const isDone = idx < currentIdx || (job.status === "completed");
          const isActive = idx === currentIdx && job.status !== "completed";
          const isPending = idx > currentIdx && job.status !== "completed";

          return (
            <div
              key={stage.key}
              className="flex items-center gap-3"
              style={{ opacity: isPending ? 0.4 : 1 }}
            >
              <div
                className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0"
                style={{
                  background: isDone
                    ? "#10b981"
                    : isActive
                    ? "rgba(124, 58, 237, 0.2)"
                    : "var(--bg-secondary)",
                  border: isActive
                    ? "2px solid #7c3aed"
                    : isDone
                    ? "none"
                    : "2px solid var(--border)",
                }}
              >
                {isDone ? (
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                ) : isActive ? (
                  <div className="w-2 h-2 rounded-full" style={{ background: "#8b5cf6", animation: "pulse 1s infinite" }} />
                ) : null}
              </div>
              <span
                className="text-sm"
                style={{
                  color: isDone
                    ? "var(--text-primary)"
                    : isActive
                    ? "#c4b5fd"
                    : "var(--text-muted)",
                  fontWeight: isActive ? 600 : 400,
                }}
              >
                {stage.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
