"use client";

import { checkHealth } from "@/lib/api";
import { useEffect, useState } from "react";

export default function SettingsPage() {
  const [health, setHealth] = useState<any>(null);

  useEffect(() => {
    checkHealth().then((res) => {
      if (res.success) setHealth(res.data);
    });
  }, []);

  const Section = ({ title, children }: { title: string; children: React.ReactNode }) => (
    <div className="card p-6">
      <h2 className="text-sm font-bold mb-5" style={{ color: "var(--text-primary)" }}>{title}</h2>
      {children}
    </div>
  );

  const Row = ({ label, value, note }: { label: string; value: string; note?: string }) => (
    <div className="flex items-center justify-between py-3 border-b last:border-0" style={{ borderColor: "var(--border-subtle)" }}>
      <div>
        <p className="text-sm" style={{ color: "var(--text-primary)" }}>{label}</p>
        {note && <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{note}</p>}
      </div>
      <span className="text-sm font-medium" style={{ color: "var(--text-secondary)" }}>{value}</span>
    </div>
  );

  const StatusRow = ({ label, status }: { label: string; status: "ok" | "missing" | undefined }) => (
    <div className="flex items-center justify-between py-3 border-b last:border-0" style={{ borderColor: "var(--border-subtle)" }}>
      <span className="text-sm" style={{ color: "var(--text-primary)" }}>{label}</span>
      <span
        className="text-xs font-semibold px-2.5 py-1 rounded-full"
        style={
          status === "ok"
            ? { background: "rgba(16,185,129,0.1)", color: "#10b981" }
            : status === "missing"
            ? { background: "rgba(239,68,68,0.1)", color: "#ef4444" }
            : { background: "var(--bg-secondary)", color: "var(--text-muted)" }
        }
      >
        {status === "ok" ? "✓ Installed" : status === "missing" ? "✗ Not Found" : "Checking..."}
      </span>
    </div>
  );

  return (
    <div className="p-6 md:p-8 max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-black" style={{ color: "var(--text-primary)" }}>Settings</h1>
        <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
          System configuration and processing defaults.
        </p>
      </div>

      <div className="space-y-5">
        {/* Processing Mode */}
        <Section title="Processing Mode">
          <Row label="Mode" value="Local (Free)" />
          <Row label="AI Engine" value="faster-whisper" note="Runs on your machine, no API key needed" />
          <Row label="Video Engine" value="FFmpeg" />
          <Row label="Model Size" value="small" note="Change via WHISPER_MODEL in .env" />
          <Row label="API Cost" value="$0.00" />
        </Section>

        {/* Default Settings */}
        <Section title="Default Settings">
          <Row label="Clip Duration" value="30 seconds" note="Change per job in the dashboard" />
          <Row label="Number of Clips" value="5" />
          <Row label="Output Format" value="MP4 (H.264 + AAC)" />
          <Row label="Output Resolution" value="1080 × 1920 (9:16)" />
          <Row label="Subtitle Style" value="Bold" />
        </Section>

        {/* System Requirements */}
        <Section title="System Requirements">
          <StatusRow label="FFmpeg" status={health?.checks?.ffmpeg} />
          <StatusRow label="yt-dlp" status={health?.checks?.yt_dlp} />
          <StatusRow label="faster-whisper" status={health?.checks?.whisper} />
        </Section>

        {/* Environment */}
        <Section title="Environment">
          <Row label="Backend" value="FastAPI + Uvicorn" />
          <Row label="Frontend" value="Next.js 14 + Tailwind CSS" />
          <Row label="Database" value="SQLite" />
          <Row label="Storage" value="Local filesystem (./data)" />
        </Section>

        {/* Legal */}
        <div
          className="rounded-xl p-5"
          style={{ background: "rgba(245,158,11,0.05)", border: "1px solid rgba(245,158,11,0.2)" }}
        >
          <p className="text-xs font-semibold mb-2" style={{ color: "#f59e0b" }}>⚠ Usage Guidelines</p>
          <p className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
            ClipForge AI is intended for processing videos you own or have explicit permission to process.
            Do not use this tool to download or redistribute copyrighted content without authorization.
            Only process content you have permission to use.
          </p>
        </div>
      </div>
    </div>
  );
}
