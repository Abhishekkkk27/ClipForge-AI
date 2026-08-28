"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listJobs, deleteJob } from "@/lib/api";
import { Job } from "@/lib/types";
import { formatDuration, timeAgo, statusBgColor, STATUS_LABELS } from "@/lib/utils";
import EmptyState from "@/components/EmptyState";
import { toast } from "@/components/Toast";

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchJobs = async () => {
    const res = await listJobs();
    if (res.success && res.data) {
      setJobs(res.data);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleDelete = async (jobId: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm("Delete this job and all its clips?")) return;

    setDeletingId(jobId);
    const res = await deleteJob(jobId);
    setDeletingId(null);

    if (res.success) {
      toast("success", "Job deleted.");
      setJobs((prev) => prev.filter((j) => j.id !== jobId));
    } else {
      toast("error", "Failed to delete job.");
    }
  };

  if (loading) {
    return (
      <div className="p-6 md:p-8">
        <div className="mb-8">
          <div className="shimmer h-8 w-32 rounded-lg mb-2" />
          <div className="shimmer h-4 w-64 rounded" />
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="shimmer h-24 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-black" style={{ color: "var(--text-primary)" }}>
            Jobs
          </h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
            {jobs.length} job{jobs.length !== 1 ? "s" : ""} total
          </p>
        </div>
        <Link href="/dashboard" className="btn-primary flex items-center gap-2 text-sm">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          New Job
        </Link>
      </div>

      {jobs.length === 0 ? (
        <EmptyState
          title="No clips yet"
          description="Paste a YouTube link to create your first clips."
          action={
            <Link href="/dashboard" className="btn-primary inline-flex items-center gap-2">
              Create First Clips
            </Link>
          }
        />
      ) : (
        <div className="space-y-3">
          {jobs.map((job) => (
            <Link
              key={job.id}
              href={`/jobs/${job.id}`}
              className="block card card-hover p-5 no-underline"
            >
              <div className="flex items-start gap-4">
                {/* Thumbnail */}
                <div
                  className="flex-shrink-0 w-20 h-14 rounded-lg overflow-hidden"
                  style={{ background: "var(--bg-secondary)" }}
                >
                  {job.video_thumbnail ? (
                    <img
                      src={job.video_thumbnail}
                      alt={job.video_title || ""}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#52525b" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                        <rect width="18" height="18" x="3" y="3" rx="2" />
                        <path d="m9 9 6 6m0-6-6 6" />
                      </svg>
                    </div>
                  )}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <p className="font-semibold text-sm truncate" style={{ color: "var(--text-primary)" }}>
                      {job.video_title || job.youtube_url}
                    </p>
                    <button
                      onClick={(e) => handleDelete(job.id, e)}
                      disabled={deletingId === job.id}
                      className="flex-shrink-0 btn-ghost p-1.5 text-xs"
                      style={{ color: "#71717a" }}
                      aria-label="Delete job"
                    >
                      {deletingId === job.id ? (
                        <div className="w-4 h-4 border-2 border-zinc-600 border-t-zinc-400 rounded-full animate-spin" />
                      ) : (
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="3 6 5 6 21 6" />
                          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
                        </svg>
                      )}
                    </button>
                  </div>

                  <div className="flex items-center flex-wrap gap-3 mt-1.5">
                    <span
                      className="inline-flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full border font-medium"
                      style={statusBgColor(job.status) as React.CSSProperties}
                    >
                      {job.status !== "completed" && job.status !== "failed" && (
                        <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
                      )}
                      {STATUS_LABELS[job.status] || job.status}
                    </span>

                    {job.video_duration && (
                      <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                        {formatDuration(job.video_duration)}
                      </span>
                    )}

                    {job.clip_count > 0 && (
                      <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                        {job.clip_count} clip{job.clip_count !== 1 ? "s" : ""}
                      </span>
                    )}

                    <span className="text-xs ml-auto" style={{ color: "var(--text-muted)" }}>
                      {timeAgo(job.created_at)}
                    </span>
                  </div>

                  {/* Progress bar for in-progress jobs */}
                  {job.status !== "completed" && job.status !== "failed" && job.status !== "queued" && (
                    <div className="mt-3">
                      <div className="w-full h-1 rounded-full overflow-hidden" style={{ background: "var(--bg-secondary)" }}>
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${job.progress}%`,
                            background: "linear-gradient(90deg, #7c3aed, #8b5cf6)",
                          }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
