import type { SubQuery, SubQueryType } from "@/lib/types";
import Badge from "@/components/ui/Badge";

interface SubQueryCardProps {
  item: SubQuery;
  index: number;
}

const TYPE_META: Record<SubQueryType, { label: string; icon: string }> = {
  comparative:      { label: "Comparative",      icon: "⚖️" },
  feature_specific: { label: "Feature Specific", icon: "🔧" },
  use_case:         { label: "Use Case",         icon: "💡" },
  trust_signals:    { label: "Trust Signals",    icon: "🛡️" },
  how_to:           { label: "How To",           icon: "📖" },
  definitional:     { label: "Definitional",     icon: "📚" },
};

export default function SubQueryCard({ item, index }: SubQueryCardProps) {
  const meta = TYPE_META[item.type] ?? { label: item.type, icon: "❓" };
  const hasCoverage = item.covered !== null && item.covered !== undefined;

  return (
    <div className="fade-up flex items-start gap-3 p-4 rounded-xl bg-surface border border-border hover:border-border-hi transition-colors duration-150 group">
      {/* Index */}
      <span className="shrink-0 w-6 h-6 rounded-md bg-elevated flex items-center justify-center text-xs text-text-lo font-mono tabular-nums mt-0.5">
        {index + 1}
      </span>

      <div className="flex-1 min-w-0 space-y-2">
        <p className="text-sm text-text-hi leading-relaxed group-hover:text-white transition-colors duration-100">
          {item.query}
        </p>

        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="purple">
            <span>{meta.icon}</span>
            {meta.label}
          </Badge>

          {hasCoverage && (
            <Badge variant={item.covered ? "teal" : "danger"}>
              {item.covered ? "✓ Covered" : "✗ Gap"}
            </Badge>
          )}

          {item.similarity_score !== null && item.similarity_score !== undefined && (
            <span className="text-xs text-text-lo tabular-nums">
              sim: {item.similarity_score.toFixed(2)}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
