/**
 * ClipForge AI — API Client
 * Typed wrapper around the FastAPI backend.
 */

import {
  ApiResponse,
  Job,
  Clip,
  VideoMetadata,
  CreateJobRequest,
  HealthCheck,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });

  if (!res.ok && res.status !== 422) {
    const text = await res.text();
    let errorMessage = `Request failed: ${res.status}`;
    try {
      const json = JSON.parse(text);
      errorMessage = json?.detail?.message || json?.detail || errorMessage;
    } catch {}
    return {
      success: false,
      data: null,
      error: { code: `HTTP_${res.status}`, message: errorMessage },
    };
  }

  try {
    return await res.json();
  } catch {
    return {
      success: false,
      data: null,
      error: { code: "PARSE_ERROR", message: "Failed to parse response." },
    };
  }
}

// ─── Health ────────────────────────────────────────────────────────────────────

export async function checkHealth(): Promise<ApiResponse<HealthCheck>> {
  return apiFetch<HealthCheck>("/api/health");
}

// ─── URL Validation ────────────────────────────────────────────────────────────

export async function validateUrl(
  url: string
): Promise<ApiResponse<{ valid: boolean; video_id?: string }>> {
  return apiFetch("/api/validate-url", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

export async function fetchMetadata(
  url: string
): Promise<ApiResponse<VideoMetadata>> {
  return apiFetch<VideoMetadata>("/api/metadata", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

// ─── Jobs ──────────────────────────────────────────────────────────────────────

export async function createJob(
  req: CreateJobRequest
): Promise<ApiResponse<Job>> {
  return apiFetch<Job>("/api/jobs", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export async function listJobs(): Promise<ApiResponse<Job[]>> {
  return apiFetch<Job[]>("/api/jobs");
}

export async function getJob(jobId: string): Promise<ApiResponse<Job>> {
  return apiFetch<Job>(`/api/jobs/${jobId}`);
}

export async function deleteJob(jobId: string): Promise<ApiResponse<{ deleted: string }>> {
  return apiFetch(`/api/jobs/${jobId}`, { method: "DELETE" });
}

// ─── Clips ─────────────────────────────────────────────────────────────────────

export async function getJobClips(jobId: string): Promise<ApiResponse<Clip[]>> {
  return apiFetch<Clip[]>(`/api/jobs/${jobId}/clips`);
}

export async function getClip(clipId: string): Promise<ApiResponse<Clip>> {
  return apiFetch<Clip>(`/api/clips/${clipId}`);
}

export function getClipPreviewUrl(clipId: string): string {
  return `${API_BASE}/api/clips/${clipId}/preview`;
}

export function getClipDownloadUrl(clipId: string): string {
  return `${API_BASE}/api/clips/${clipId}/download`;
}

export function getThumbnailUrl(clipId: string): string {
  return `${API_BASE}/api/clips/${clipId}/thumbnail`;
}

export function getDownloadAllUrl(jobId: string): string {
  return `${API_BASE}/api/jobs/${jobId}/download-all`;
}

// ─── SSE Progress Streaming ────────────────────────────────────────────────────

export function subscribeToJobProgress(
  jobId: string,
  onProgress: (progress: number, stage: string) => void,
  onDone: () => void,
  onError?: (err: Event) => void
): () => void {
  const url = `${API_BASE}/api/jobs/${jobId}/stream`;
  const es = new EventSource(url);

  es.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onProgress(data.progress ?? 0, data.stage ?? "processing");
      if (data.done) {
        es.close();
        onDone();
      }
    } catch {}
  };

  es.onerror = (err) => {
    es.close();
    onError?.(err);
    onDone();
  };

  return () => es.close();
}
