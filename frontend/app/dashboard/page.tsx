"use client";

import UrlInput from "@/components/UrlInput";
import { checkHealth } from "@/lib/api";
import { useEffect, useState } from "react";
import Link from "next/link";

export default function DashboardPage() {
  const [health, setHealth] = useState<{ ffmpeg: string; yt_dlp: string; whisper: string } | null>(null);

  useEffect(() => {
    checkHealth().then((res) => {
      if (res.success && res.data) {
        setHealth(res.data.checks);
      }
    });
  }, []);

  const checkItem = (label: string, status: string | undefined) => (
    <div className="flex items-center justify-between py-2">
      <span className="text-sm" style={{ color: "var(--text-secondary)" }}>{label}</span>
      <span
        className="text-xs font-semibold px-2 py-0.5 rounded-full"
        style={
          status === "ok"
            ? { background: "rgba(16,185,129,0.1)", color: "#10b981" }
            : { background: "rgba(239,68,68,0.1)", color: "#ef4444" }
        }
      >
        {status === "ok" ? "✓ Ready" : "✗ Missing"}
      </span>
    </div>
  );

  return (
    <div className="p-6 md:p-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-black" style={{ color: "var(--text-primary)" }}>
          Create New Clips
        </h1>
        <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
          Paste a YouTube URL to start generating viral-ready short clips.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main input */}
        <div className="lg:col-span-2">
          <div className="card p-6">
            <UrlInput showSettings={true} />
          </div>

          {/* Recent jobs link */}
          <div className="mt-4">
            <Link
              href="/jobs"
              className="flex items-center gap-2 text-sm hover:text-violet-400 transition-colors"
              style={{ color: "var(--text-secondary)" }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect width="18" height="18" x="3" y="3" rx="2" />
                <path d="M3 9h18" />
              </svg>
              View all previous jobs
            </Link>
          </div>
        </div>

        {/* Sidebar panel */}
        <div className="space-y-4">
          {/* System status */}
          <div className="card p-5">
            <h3 className="text-sm font-bold mb-3" style={{ color: "var(--text-primary)" }}>
              System Status
            </h3>
            {health ? (
              <div className="divide-y" style={{ borderColor: "var(--border-subtle)" }}>
                {checkItem("FFmpeg", health.ffmpeg)}
                {checkItem("yt-dlp", health.yt_dlp)}
                {checkItem("Whisper", health.whisper)}
              </div>
            ) : (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="shimmer h-8 rounded-lg" />
                ))}
              </div>
            )}
          </div>

          {/* Info box */}
          <div className="card p-5">
            <h3 className="text-sm font-bold mb-3" style={{ color: "var(--text-primary)" }}>
              Processing Info
            </h3>
            <div className="space-y-2 text-xs" style={{ color: "var(--text-secondary)" }}>
              <p>• Downloads up to 720p to save time</p>
              <p>• Transcription runs locally (no API)</p>
              <p>• Processing time depends on video length</p>
              <p>• ~2–5 min per 10 min of video (CPU)</p>
            </div>
          </div>

          {/* Tips */}
          <div
            className="rounded-xl p-4"
            style={{ background: "rgba(124,58,237,0.06)", border: "1px solid rgba(124,58,237,0.15)" }}
          >
            <p className="text-xs font-semibold mb-1" style={{ color: "#c4b5fd" }}>💡 Tip</p>
            <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
              Videos with clear speech work best. Interviews, podcasts, and educational content
              typically produce the most engaging clips.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
