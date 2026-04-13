import type { GapSummary as GapSummaryType } from "@/lib/types";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";

export default function GapSummary({ summary }: { summary: GapSummaryType }) {
  const pct = summary.coverage_percent;

  return (
    <Card className="p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text-hi">Coverage Analysis</h3>
        <span
          className="text-2xl font-bold tabular-nums"
          style={{ color: pct >= 70 ? "#00C9A7" : pct >= 40 ? "#FFB347" : "#FF6B6B" }}
        >
          {pct}%
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-2 rounded-full bg-border overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{
            width: `${pct}%`,
            backgroundColor: pct >= 70 ? "#00C9A7" : pct >= 40 ? "#FFB347" : "#FF6B6B",
          }}
        />
      </div>

      <p className="text-xs text-text-lo">
        {summary.covered} of {summary.total} queries covered by existing content
      </p>

      {summary.covered_types.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-xs font-semibold text-text-lo uppercase tracking-wider">Covered</p>
          <div className="flex flex-wrap gap-1.5">
            {summary.covered_types.map((t) => (
              <Badge key={t} variant="teal">{t.replace("_", " ")}</Badge>
            ))}
          </div>
        </div>
      )}

      {summary.missing_types.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-xs font-semibold text-text-lo uppercase tracking-wider">Content Gaps</p>
          <div className="flex flex-wrap gap-1.5">
            {summary.missing_types.map((t) => (
              <Badge key={t} variant="danger">{t.replace("_", " ")}</Badge>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}
