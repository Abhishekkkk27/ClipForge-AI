"use client";

interface ProgressBarProps {
  progress: number;  // 0–100
  stage?: string;
  animated?: boolean;
  showLabel?: boolean;
  height?: number;
}

export default function ProgressBar({
  progress,
  stage,
  animated = true,
  showLabel = true,
  height = 6,
}: ProgressBarProps) {
  const pct = Math.min(Math.max(progress, 0), 100);
  const isComplete = pct >= 100;

  return (
    <div className="w-full">
      {showLabel && (
        <div className="flex justify-between items-center mb-2">
          <span className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
            {stage || "Processing..."}
          </span>
          <span
            className="text-xs font-bold tabular-nums"
            style={{ color: isComplete ? "#10b981" : "#8b5cf6" }}
          >
            {pct}%
          </span>
        </div>
      )}
      <div
        className="w-full rounded-full overflow-hidden"
        style={{ height: `${height}px`, background: "var(--bg-secondary)" }}
      >
        <div
          className="h-full rounded-full transition-all duration-500 ease-out"
          style={{
            width: `${pct}%`,
            background: isComplete
              ? "linear-gradient(90deg, #10b981, #059669)"
              : "linear-gradient(90deg, #7c3aed, #8b5cf6, #a78bfa)",
            boxShadow: isComplete
              ? "0 0 8px rgba(16, 185, 129, 0.5)"
              : "0 0 8px rgba(124, 58, 237, 0.5)",
          }}
        />
      </div>
    </div>
  );
}
