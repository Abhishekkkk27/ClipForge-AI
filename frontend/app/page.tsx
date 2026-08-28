"use client";

import Link from "next/link";
import UrlInput from "@/components/UrlInput";
import ToastContainer from "@/components/Toast";

const FEATURES = [
  {
    icon: "🤖",
    title: "AI Highlight Detection",
    desc: "Rule-based scoring identifies the most compelling moments automatically.",
  },
  {
    icon: "💬",
    title: "Automatic Subtitles",
    desc: "Whisper AI transcribes speech and generates perfectly-timed subtitles.",
  },
  {
    icon: "📱",
    title: "9:16 Vertical Clips",
    desc: "Auto-crops landscape video into portrait format for TikTok, Reels & Shorts.",
  },
  {
    icon: "⚡",
    title: "Fast FFmpeg Processing",
    desc: "Hardware-accelerated video encoding for quick turnaround times.",
  },
  {
    icon: "🔒",
    title: "Free Local AI",
    desc: "No API keys required. Runs entirely on your machine.",
  },
  {
    icon: "🎬",
    title: "Multiple Clips",
    desc: "Generate up to 10 clips per video with individual scores and reasons.",
  },
];

export default function LandingPage() {
  return (
    <>
      <div className="min-h-screen bg-grid">
        {/* Navigation */}
        <nav className="border-b px-6 py-4 flex items-center justify-between" style={{ borderColor: "var(--border)", background: "rgba(9,9,11,0.8)", backdropFilter: "blur(12px)", position: "sticky", top: 0, zIndex: 40 }}>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: "linear-gradient(135deg, #7c3aed, #4f46e5)" }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
              </svg>
            </div>
            <span className="font-bold text-sm" style={{ color: "var(--text-primary)" }}>ClipForge AI</span>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/dashboard" className="btn-secondary text-sm px-4 py-2">
              Dashboard
            </Link>
            <Link href="/jobs" className="btn-ghost text-sm px-4 py-2">
              My Jobs
            </Link>
          </div>
        </nav>

        {/* Hero */}
        <section className="relative px-4 py-24 flex flex-col items-center text-center">
          {/* Glow background */}
          <div
            className="absolute inset-0 pointer-events-none"
            style={{
              background: "radial-gradient(ellipse 80% 50% at 50% -20%, rgba(124,58,237,0.15), transparent)",
            }}
          />

          <div className="relative z-10 max-w-3xl mx-auto">
            <div
              className="inline-flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-full mb-8"
              style={{ background: "rgba(124,58,237,0.1)", border: "1px solid rgba(124,58,237,0.3)", color: "#c4b5fd" }}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse" />
              Free • Local AI • No API Keys Required
            </div>

            <h1 className="text-5xl md:text-6xl font-black mb-6 leading-tight tracking-tight">
              Turn Long Videos Into{" "}
              <span className="text-gradient">Viral-Ready Shorts</span>
            </h1>

            <p className="text-lg md:text-xl mb-12" style={{ color: "var(--text-secondary)" }}>
              Paste a YouTube link and let AI find the best moments, create short clips,
              and add subtitles automatically.
            </p>

            {/* Main URL input */}
            <div className="w-full max-w-2xl mx-auto">
              <div className="card p-6">
                <UrlInput showSettings={false} />
              </div>
            </div>

            <p className="mt-4 text-sm" style={{ color: "var(--text-muted)" }}>
              Or{" "}
              <Link href="/dashboard" className="underline hover:text-violet-400 transition-colors" style={{ color: "var(--text-secondary)" }}>
                open the full dashboard
              </Link>{" "}
              for advanced settings.
            </p>
          </div>
        </section>

        {/* Steps */}
        <section className="px-4 py-16 max-w-4xl mx-auto">
          <h2 className="text-center text-2xl font-bold mb-12" style={{ color: "var(--text-primary)" }}>
            How It Works
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { num: "01", title: "Paste a Video", desc: "Drop in any YouTube URL. We'll fetch the metadata instantly." },
              { num: "02", title: "AI Finds Best Moments", desc: "Whisper transcribes the audio. Our scoring engine picks the highlights." },
              { num: "03", title: "Export Your Clips", desc: "Download 30-second vertical clips with burned-in subtitles, ready to post." },
            ].map((step) => (
              <div key={step.num} className="card p-6 text-center card-hover">
                <div
                  className="text-4xl font-black mb-4"
                  style={{ color: "rgba(124,58,237,0.4)" }}
                >
                  {step.num}
                </div>
                <h3 className="font-bold mb-2" style={{ color: "var(--text-primary)" }}>{step.title}</h3>
                <p className="text-sm" style={{ color: "var(--text-secondary)" }}>{step.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Features */}
        <section className="px-4 py-16 max-w-5xl mx-auto">
          <h2 className="text-center text-2xl font-bold mb-12" style={{ color: "var(--text-primary)" }}>
            Everything You Need
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {FEATURES.map((f) => (
              <div key={f.title} className="card p-5 card-hover">
                <div className="text-2xl mb-3">{f.icon}</div>
                <h3 className="font-bold text-sm mb-1.5" style={{ color: "var(--text-primary)" }}>{f.title}</h3>
                <p className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>{f.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="px-4 py-20 text-center">
          <div
            className="max-w-2xl mx-auto rounded-2xl p-10"
            style={{ background: "rgba(124,58,237,0.08)", border: "1px solid rgba(124,58,237,0.2)" }}
          >
            <h2 className="text-3xl font-black mb-4" style={{ color: "var(--text-primary)" }}>
              Ready to create?
            </h2>
            <p className="text-base mb-8" style={{ color: "var(--text-secondary)" }}>
              Start generating viral clips from any YouTube video in minutes.
            </p>
            <Link href="/dashboard" className="btn-primary inline-flex items-center gap-2" style={{ fontSize: "1rem", padding: "0.75rem 2rem" }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
              Create Clips — It&apos;s Free
            </Link>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t px-6 py-8 text-center" style={{ borderColor: "var(--border)" }}>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            ClipForge AI — Open source, local AI video clipping. Only process content you have permission to use.
          </p>
        </footer>
      </div>

      <ToastContainer />
    </>
  );
}
