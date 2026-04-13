import type { CheckResult } from "@/lib/types";
import Card from "@/components/ui/Card";

interface CheckCardProps {
  check: CheckResult;
  index: number;
}

const CHECK_LABELS: Record<string, string> = {
  A: "Direct Answer",
  B: "H-tag Hierarchy",
  C: "Snippet Readability",
};

function ScoreBar({ score, max }: { score: number; max: number }) {
  const pct = (score / max) * 100;
  const color =
    pct === 100 ? "#00C9A7" : pct >= 50 ? "#845EC2" : "#FF6B6B";
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-1.5 rounded-full bg-border overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-xs tabular-nums text-text-lo shrink-0">
        {score}/{max}
      </span>
    </div>
  );
}

export default function CheckCard({ check, index }: CheckCardProps) {
  const label = String.fromCharCode(65 + index); // A, B, C
  const passed = check.passed;

  return (
    <Card className="p-5 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          {/* Check letter badge */}
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold shrink-0"
            style={{
              backgroundColor: passed
                ? "rgba(0,201,167,0.15)"
                : "rgba(255,107,107,0.15)",
              color: passed ? "#00C9A7" : "#FF6B6B",
              border: `1px solid ${passed ? "rgba(0,201,167,0.3)" : "rgba(255,107,107,0.3)"}`,
            }}
          >
            {label}
          </div>
          <div>
            <p className="text-sm font-semibold text-text-hi leading-tight">
              {CHECK_LABELS[label] ?? check.name}
            </p>
            <p className="text-xs text-text-lo mt-0.5">{check.name}</p>
          </div>
        </div>
        {/* Pass/Fail icon */}
        <div className="shrink-0 mt-0.5" aria-hidden="true">
          {passed ? (
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none" role="img" aria-label="Passed">
              <title>Passed</title>
              <circle cx="9" cy="9" r="9" fill="rgba(0,201,167,0.2)" />
              <path
                d="M5 9l3 3 5-5"
                stroke="#00C9A7"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          ) : (
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none" role="img" aria-label="Failed">
              <title>Failed</title>
              <circle cx="9" cy="9" r="9" fill="rgba(255,107,107,0.2)" />
              <path
                d="M6 6l6 6M12 6l-6 6"
                stroke="#FF6B6B"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
          )}
        </div>
      </div>

      <ScoreBar score={check.score} max={check.max_score} />

      {check.recommendation && (
        <p className="text-xs text-text-mid leading-relaxed border-l-2 border-purple pl-3">
          {check.recommendation}
        </p>
      )}
    </Card>
  );
}
