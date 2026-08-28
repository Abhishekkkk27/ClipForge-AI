"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { getJob, getJobClips, subscribeToJobProgress, getDownloadAllUrl } from "@/lib/api";
import { Job, Clip } from "@/lib/types";
import ProcessingCard from "@/components/ProcessingCard";
import ClipCard from "@/components/ClipCard";
import EmptyState from "@/components/EmptyState";
import { toast } from "@/components/Toast";

export default function JobDetailPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.id as string;

  const [job, setJob] = useState<Job | null>(null);
  const [clips, setClips] = useState<Clip[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchJob = useCallback(async () => {
    const res = await getJob(jobId);
    if (!res.success) {
      setError(res.error?.message || "Job not found.");
      setLoading(false);
      return;
    }
    if (res.data) {
      setJob(res.data);
    }
    setLoading(false);
  }, [jobId]);

  const fetchClips = useCallback(async () => {
    const res = await getJobClips(jobId);
    if (res.success && res.data) {
      setClips(res.data);
    }
  }, [jobId]);

  useEffect(() => {
    fetchJob();
    fetchClips();

    // Subscribe to SSE progress
    const unsubscribe = subscribeToJobProgress(
      jobId,
      (progress, stage) => {
        setJob((prev) => prev ? { ...prev, progress, stage } : prev);
      },
      () => {
        // Done — refresh final state
        fetchJob();
        fetchClips();
        toast("success", "Processing complete! Your clips are ready.");
      },
      () => {
        // Error — fall back to polling
        const poll = setInterval(async () => {
          await fetchJob();
          await fetchClips();
        }, 3000);
        setTimeout(() => clearInterval(poll), 600000);
      }
    );

    // Also poll for robustness
    const poll = setInterval(() => {
      if (job?.status !== "completed" && job?.status !== "failed") {
        fetchJob();
        fetchClips();
      }
    }, 5000);

    return () => {
      unsubscribe();
      clearInterval(poll);
    };
  }, [jobId, fetchJob, fetchClips]);

  const handleDownloadAll = () => {
    const url = getDownloadAllUrl(jobId);
    const a = document.createElement("a");
    a.href = url;
    a.download = "clipforge_export.zip";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    toast("info", "Preparing ZIP download...");
  };

  if (loading) {
    return (
      <div className="p-6 md:p-8 max-w-5xl mx-auto">
        <div className="shimmer h-48 rounded-xl mb-6" />
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="shimmer rounded-xl" style={{ aspectRatio: "9/16", maxHeight: "280px" }} />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 md:p-8 max-w-5xl mx-auto">
        <EmptyState
          title="Job not found"
          description={error}
          action={
            <Link href="/jobs" className="btn-secondary">
              Back to Jobs
            </Link>
          }
        />
      </div>
    );
  }

  if (!job) return null;

  const isComplete = job.status === "completed";
  const isFailed = job.status === "failed";
  const isProcessing = !isComplete && !isFailed;

  return (
    <div className="p-6 md:p-8 max-w-5xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 mb-6 text-sm" style={{ color: "var(--text-muted)" }}>
        <Link href="/jobs" className="hover:text-violet-400 transition-colors">Jobs</Link>
        <span>/</span>
        <span className="truncate max-w-xs" style={{ color: "var(--text-secondary)" }}>
          {job.video_title || job.id}
        </span>
      </div>

      {/* Processing card (shown during processing) */}
      {isProcessing && (
        <div className="mb-8">
          <ProcessingCard job={job} />
        </div>
      )}

      {/* Results */}
      {isComplete && (
        <>
          {/* Success header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-xl font-black" style={{ color: "var(--text-primary)" }}>
                {clips.length} clip{clips.length !== 1 ? "s" : ""} ready
                <span className="ml-2 text-xl">🎉</span>
              </h1>
              <p className="text-sm mt-0.5" style={{ color: "var(--text-secondary)" }}>
                {job.video_title}
              </p>
            </div>
            {clips.length > 1 && (
              <button
                onClick={handleDownloadAll}
                className="btn-secondary flex items-center gap-2 text-sm"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="7 10 12 15 17 10" />
                  <line x1="12" y1="15" x2="12" y2="3" />
                </svg>
                Download All
              </button>
            )}
          </div>

          {/* Clips grid */}
          {clips.length > 0 ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
              {clips.map((clip) => (
                <ClipCard
                  key={clip.id}
                  clip={clip}
                  onDelete={(id) => setClips((prev) => prev.filter((c) => c.id !== id))}
                />
              ))}
            </div>
          ) : (
            <EmptyState
              title="No clips generated"
              description="The processor finished but no clips were produced. This may happen with very short videos or videos with little speech."
              action={
                <Link href="/dashboard" className="btn-primary">
                  Try Another Video
                </Link>
              }
            />
          )}
        </>
      )}

      {/* Failed state */}
      {isFailed && (
        <div>
          <ProcessingCard job={job} />
          <div className="mt-6 flex gap-3">
            <Link href="/dashboard" className="btn-primary">
              Try Again
            </Link>
            <Link href="/jobs" className="btn-secondary">
              All Jobs
            </Link>
          </div>
        </div>
      )}

      {/* Processing + any partial clips already done */}
      {isProcessing && clips.length > 0 && (
        <div className="mt-8">
          <h2 className="text-base font-bold mb-4" style={{ color: "var(--text-primary)" }}>
            Clips generated so far ({clips.length})
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {clips.map((clip) => (
              <ClipCard key={clip.id} clip={clip} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
