import type { SubQuery, SubQueryType } from "@/lib/types";
import Card from "@/components/ui/Card";

const INTENT_LABEL: Record<string, string> = {
  comparative:      "Comparative",
  feature_specific: "Feature Specific",
  use_case:         "Use Case",
  trust_signals:    "Trust Signals",
  how_to:           "How To",
  definitional:     "Definitional",
};

interface IntentBreakdownProps {
  subQueries: SubQuery[];
  activeFilter: SubQueryType | null;
  onFilterClick: (t: SubQueryType) => void;
}

export default function IntentBreakdown({ subQueries, activeFilter, onFilterClick }: IntentBreakdownProps) {
  const counts: Record<string, number> = {};
  for (const sq of subQueries) {
    counts[sq.type] = (counts[sq.type] ?? 0) + 1;
  }
  const total = subQueries.length;

  return (
    <Card className="p-5 space-y-3">
      <p className="text-xs font-semibold text-text-lo uppercase tracking-wider">
        Intent Breakdown
      </p>
      <div className="space-y-2">
        {Object.entries(counts)
          .sort(([, a], [, b]) => b - a)
          .map(([type, count]) => {
            const isActive = activeFilter === type;
            return (
              <button
                key={type}
                type="button"
                onClick={() => onFilterClick(type as SubQueryType)}
                className={[
                  "w-full text-left space-y-1 rounded-lg px-2 py-1.5 transition-colors duration-100 cursor-pointer",
                  isActive ? "bg-[rgba(132,94,194,0.1)]" : "hover:bg-elevated",
                ].join(" ")}
              >
                <div className="flex justify-between text-xs">
                  <span className={isActive ? "text-purple-light font-semibold" : "text-text-mid"}>
                    {INTENT_LABEL[type] ?? type}
                  </span>
                  <span className="text-text-lo tabular-nums">{count}/{total}</span>
                </div>
                <div className="h-1 rounded-full bg-border overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${(count / total) * 100}%`,
                      backgroundColor: isActive ? "#845EC2" : "#3D2A60",
                    }}
                  />
                </div>
              </button>
            );
          })}
      </div>
    </Card>
  );
}
