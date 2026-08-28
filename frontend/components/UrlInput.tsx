"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { validateUrl, fetchMetadata, createJob } from "@/lib/api";
import { VideoMetadata } from "@/lib/types";
import { formatDuration } from "@/lib/utils";
import { toast } from "@/components/Toast";
import Image from "next/image";

type ClipDuration = 15 | 30 | 45 | 60;
type SubtitleStyle = "bold" | "minimal" | "karaoke";
type AspectRatio = "9:16" | "16:9" | "1:1";

interface UrlInputProps {
  showSettings?: boolean;
  onJobCreated?: (jobId: string) => void;
}

export default function UrlInput({ showSettings = true, onJobCreated }: UrlInputProps) {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [urlError, setUrlError] = useState("");
  const [isValidating, setIsValidating] = useState(false);
  const [isFetchingMeta, setIsFetchingMeta] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [metadata, setMetadata] = useState<VideoMetadata | null>(null);

  // Settings
  const [clipDuration, setClipDuration] = useState<ClipDuration>(30);
  const [numClips, setNumClips] = useState(5);
  const [aspectRatio, setAspectRatio] = useState<AspectRatio>("9:16");
  const [subtitleStyle, setSubtitleStyle] = useState<SubtitleStyle>("bold");

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleUrlChange = (value: string) => {
    setUrl(value);
    setUrlError("");
    setMetadata(null);

    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (!value.trim()) return;

    debounceRef.current = setTimeout(async () => {
      setIsValidating(true);
      const res = await validateUrl(value.trim());
      setIsValidating(false);

      if (!res.success || !res.data?.valid) {
        setUrlError("Please enter a valid YouTube URL.");
        return;
      }

      // Fetch metadata
      setIsFetchingMeta(true);
      const metaRes = await fetchMetadata(value.trim());
      setIsFetchingMeta(false);

      if (metaRes.success && metaRes.data) {
        setMetadata(metaRes.data);
      } else if (!metaRes.success && metaRes.error?.message) {
        setUrlError(metaRes.error.message);
      }
    }, 600);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) {
      setUrlError("Please enter a YouTube URL.");
      return;
    }

    setIsSubmitting(true);
    const res = await createJob({
      youtube_url: url.trim(),
      clip_duration: clipDuration,
      num_clips: numClips,
      aspect_ratio: aspectRatio,
      subtitle_style: subtitleStyle,
    });
    setIsSubmitting(false);

    if (!res.success || !res.data) {
      const msg = res.error?.message || "Failed to create job. Please try again.";
      setUrlError(msg);
      toast("error", msg);
      return;
    }

    toast("success", "Job created! Processing started.");
    if (onJobCreated) {
      onJobCreated(res.data.id);
    } else {
      router.push(`/jobs/${res.data.id}`);
    }
  };

  const isLoading = isValidating || isFetchingMeta || isSubmitting;

  return (
    <form onSubmit={handleSubmit} className="w-full space-y-5">
      {/* URL Input */}
      <div>
        <div className="relative">
          <div className="absolute left-4 top-1/2 -translate-y-1/2">
            {isValidating || isFetchingMeta ? (
              <div
                className="w-5 h-5 border-2 rounded-full animate-spin"
                style={{ borderColor: "#7c3aed", borderTopColor: "transparent" }}
              />
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#71717a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 2H3v16h5l3 3 3-3h5V2z" />
                <path d="m10 9 5 3-5 3V9z" />
              </svg>
            )}
          </div>
          <input
            id="youtube-url-input"
            type="url"
            value={url}
            onChange={(e) => handleUrlChange(e.target.value)}
            placeholder="Paste YouTube video URL..."
            className="input-field pl-12 pr-4 py-4 text-base"
            style={{ fontSize: "1rem", height: "56px" }}
            disabled={isSubmitting}
            autoComplete="off"
          />
        </div>
        {urlError && (
          <p className="mt-2 text-sm" style={{ color: "#ef4444" }}>{urlError}</p>
        )}
        <p className="mt-1.5 text-xs" style={{ color: "var(--text-muted)" }}>
          Only process content you have permission to use.
        </p>
      </div>

      {/* Metadata Preview */}
      {metadata && (
        <div
          className="flex gap-4 p-4 rounded-xl animate-fade-in"
          style={{ background: "var(--bg-card)", border: "1px solid var(--border)" }}
        >
          {metadata.thumbnail && (
            <div className="flex-shrink-0 w-20 h-14 rounded-lg overflow-hidden">
              <img
                src={metadata.thumbnail}
                alt={metadata.title}
                className="w-full h-full object-cover"
              />
            </div>
          )}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold truncate" style={{ color: "var(--text-primary)" }}>
              {metadata.title}
            </p>
            <p className="text-xs mt-0.5" style={{ color: "var(--text-secondary)" }}>
              {metadata.channel}
              {metadata.duration ? ` · ${formatDuration(metadata.duration)}` : ""}
            </p>
            <div
              className="mt-1.5 inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full"
              style={{ background: "rgba(16,185,129,0.1)", color: "#10b981" }}
            >
              <span>✓</span> Video found
            </div>
          </div>
        </div>
      )}

      {/* Settings */}
      {showSettings && (
        <div className="grid grid-cols-2 gap-4">
          {/* Clip Duration */}
          <div>
            <label className="block text-xs font-semibold mb-2" style={{ color: "var(--text-secondary)" }}>
              Clip Duration
            </label>
            <div className="grid grid-cols-4 gap-1">
              {([15, 30, 45, 60] as ClipDuration[]).map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => setClipDuration(d)}
                  className="py-1.5 rounded-lg text-xs font-medium transition-all duration-150"
                  style={
                    clipDuration === d
                      ? { background: "rgba(124, 58, 237, 0.2)", color: "#c4b5fd", border: "1px solid rgba(124, 58, 237, 0.5)" }
                      : { background: "var(--bg-secondary)", color: "var(--text-muted)", border: "1px solid var(--border)" }
                  }
                >
                  {d}s
                </button>
              ))}
            </div>
          </div>

          {/* Number of Clips */}
          <div>
            <label className="block text-xs font-semibold mb-2" style={{ color: "var(--text-secondary)" }}>
              Number of Clips
            </label>
            <div className="grid grid-cols-4 gap-1">
              {[3, 5, 8, 10].map((n) => (
                <button
                  key={n}
                  type="button"
                  onClick={() => setNumClips(n)}
                  className="py-1.5 rounded-lg text-xs font-medium transition-all duration-150"
                  style={
                    numClips === n
                      ? { background: "rgba(124, 58, 237, 0.2)", color: "#c4b5fd", border: "1px solid rgba(124, 58, 237, 0.5)" }
                      : { background: "var(--bg-secondary)", color: "var(--text-muted)", border: "1px solid var(--border)" }
                  }
                >
                  {n}
                </button>
              ))}
            </div>
          </div>

          {/* Aspect Ratio */}
          <div>
            <label className="block text-xs font-semibold mb-2" style={{ color: "var(--text-secondary)" }}>
              Aspect Ratio
            </label>
            <div className="grid grid-cols-3 gap-1">
              {(["9:16", "16:9", "1:1"] as AspectRatio[]).map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => setAspectRatio(r)}
                  className="py-1.5 rounded-lg text-xs font-medium transition-all duration-150"
                  style={
                    aspectRatio === r
                      ? { background: "rgba(124, 58, 237, 0.2)", color: "#c4b5fd", border: "1px solid rgba(124, 58, 237, 0.5)" }
                      : { background: "var(--bg-secondary)", color: "var(--text-muted)", border: "1px solid var(--border)" }
                  }
                >
                  {r}
                </button>
              ))}
            </div>
          </div>

          {/* Subtitle Style */}
          <div>
            <label className="block text-xs font-semibold mb-2" style={{ color: "var(--text-secondary)" }}>
              Subtitle Style
            </label>
            <div className="grid grid-cols-3 gap-1">
              {(["bold", "minimal", "karaoke"] as SubtitleStyle[]).map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setSubtitleStyle(s)}
                  className="py-1.5 rounded-lg text-xs font-medium capitalize transition-all duration-150"
                  style={
                    subtitleStyle === s
                      ? { background: "rgba(124, 58, 237, 0.2)", color: "#c4b5fd", border: "1px solid rgba(124, 58, 237, 0.5)" }
                      : { background: "var(--bg-secondary)", color: "var(--text-muted)", border: "1px solid var(--border)" }
                  }
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Submit Button */}
      <button
        type="submit"
        id="generate-clips-btn"
        disabled={isLoading || !!urlError}
        className="btn-primary w-full flex items-center justify-center gap-2"
        style={{ height: "52px", fontSize: "1rem" }}
      >
        {isSubmitting ? (
          <>
            <div
              className="w-5 h-5 border-2 rounded-full animate-spin"
              style={{ borderColor: "rgba(255,255,255,0.3)", borderTopColor: "white" }}
            />
            Creating Job...
          </>
        ) : (
          <>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
            Generate Clips
          </>
        )}
      </button>
    </form>
  );
}
