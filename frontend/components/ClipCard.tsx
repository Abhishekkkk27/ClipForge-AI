"use client";

import { useState, useRef, useEffect } from "react";
import { Clip } from "@/lib/types";
import { formatDuration, formatTime, scoreColor } from "@/lib/utils";
import { getClipPreviewUrl, getClipDownloadUrl } from "@/lib/api";
import { toast } from "@/components/Toast";

interface ClipCardProps {
  clip: Clip;
  onDelete?: (clipId: string) => void;
}

export default function ClipCard({ clip, onDelete }: ClipCardProps) {
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [thumbnailError, setThumbnailError] = useState(false);

  const score = clip.score ?? 0;
  const scoreColorClass = scoreColor(score);
  const thumbnailUrl = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/clips/${clip.id}/thumbnail`;
  const previewUrl = getClipPreviewUrl(clip.id);
  const downloadUrl = getClipDownloadUrl(clip.id);

  const handleDownload = async () => {
    setIsDownloading(true);
    toast("info", "Preparing download...");
    try {
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = `clipforge_clip_${String(clip.clip_number).padStart(2, "0")}.mp4`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      toast("success", `Clip #${clip.clip_number} download started.`);
    } catch {
      toast("error", "Download failed. Please try again.");
    } finally {
      setTimeout(() => setIsDownloading(false), 1000);
    }
  };

  return (
    <>
      <div
        className="card card-hover overflow-hidden animate-fade-in"
        style={{ display: "flex", flexDirection: "column" }}
      >
        {/* Thumbnail / Preview area */}
        <div
          className="relative cursor-pointer group"
          style={{ aspectRatio: "9/16", maxHeight: "320px", background: "#0a0a0b", overflow: "hidden" }}
          onClick={() => setIsPreviewOpen(true)}
        >
          {!thumbnailError ? (
            <img
              src={thumbnailUrl}
              alt={`Clip ${clip.clip_number}`}
              className="w-full h-full object-cover"
              onError={() => setThumbnailError(true)}
            />
          ) : (
            <div className="w-full h-full flex flex-col items-center justify-center gap-2">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#52525b" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <rect width="18" height="18" x="3" y="3" rx="2" />
                <path d="m9 9 6 6m0-6-6 6" />
              </svg>
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>No preview</span>
            </div>
          )}

          {/* Play overlay */}
          <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200" style={{ background: "rgba(0,0,0,0.5)" }}>
            <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ background: "rgba(124, 58, 237, 0.9)" }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="white">
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
            </div>
          </div>

          {/* Clip number badge */}
          <div
            className="absolute top-2 left-2 px-2 py-0.5 rounded-lg text-xs font-bold"
            style={{ background: "rgba(0,0,0,0.7)", color: "white" }}
          >
            #{clip.clip_number}
          </div>

          {/* Duration badge */}
          <div
            className="absolute bottom-2 right-2 px-2 py-0.5 rounded-lg text-xs font-medium"
            style={{ background: "rgba(0,0,0,0.7)", color: "white" }}
          >
            {formatDuration(clip.duration)}
          </div>
        </div>

        {/* Card content */}
        <div className="p-4 flex-1 flex flex-col gap-3">
          {/* Score + timestamps */}
          <div className="flex items-start justify-between gap-2">
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-xs" style={{ color: "var(--text-muted)" }}>Score</span>
                <span className={`text-lg font-bold tabular-nums ${scoreColorClass}`}>
                  {score.toFixed(0)}
                </span>
                <span className="text-xs" style={{ color: "var(--text-muted)" }}>/100</span>
              </div>
              <div className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                {formatTime(clip.start_time)} → {formatTime(clip.end_time)}
              </div>
            </div>
            {/* Score ring */}
            <div
              className="score-ring flex-shrink-0"
              style={{
                background: score >= 80 ? "rgba(16,185,129,0.15)" : score >= 60 ? "rgba(245,158,11,0.15)" : "rgba(239,68,68,0.15)",
                border: `2px solid ${score >= 80 ? "#10b981" : score >= 60 ? "#f59e0b" : "#ef4444"}`,
              }}
            >
              <span
                className="text-xs font-bold"
                style={{ color: score >= 80 ? "#10b981" : score >= 60 ? "#f59e0b" : "#ef4444" }}
              >
                {score >= 80 ? "🔥" : score >= 60 ? "👍" : "💡"}
              </span>
            </div>
          </div>

          {/* Reason */}
          {clip.reason && (
            <p className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
              {clip.reason}
            </p>
          )}

          {/* Action buttons */}
          <div className="flex gap-2 mt-auto pt-1">
            <button
              onClick={() => setIsPreviewOpen(true)}
              className="btn-secondary flex-1 flex items-center justify-center gap-1.5 text-sm"
              style={{ height: "36px" }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
              Preview
            </button>
            <button
              onClick={handleDownload}
              disabled={isDownloading}
              className="btn-primary flex-1 flex items-center justify-center gap-1.5 text-sm"
              style={{ height: "36px" }}
            >
              {isDownloading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="7 10 12 15 17 10" />
                    <line x1="12" y1="15" x2="12" y2="3" />
                  </svg>
                  Download
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Preview Modal */}
      {isPreviewOpen && (
        <ClipPreviewModal
          previewUrl={previewUrl}
          clipNumber={clip.clip_number}
          onClose={() => setIsPreviewOpen(false)}
        />
      )}
    </>
  );
}

function ClipPreviewModal({
  previewUrl,
  clipNumber,
  onClose,
}: {
  previewUrl: string;
  clipNumber: number;
  onClose: () => void;
}) {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.85)", backdropFilter: "blur(8px)" }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="relative" style={{ maxHeight: "90vh", maxWidth: "90vw" }}>
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute -top-10 right-0 text-white/70 hover:text-white transition-colors flex items-center gap-2 text-sm"
        >
          <span>Clip #{clipNumber}</span>
          <span className="text-lg">✕</span>
        </button>

        {/* Video */}
        <video
          ref={videoRef}
          src={previewUrl}
          controls
          autoPlay
          className="rounded-xl"
          style={{
            maxHeight: "80vh",
            maxWidth: "100%",
            aspectRatio: "9/16",
            background: "#000",
          }}
        />
      </div>
    </div>
  );
}
