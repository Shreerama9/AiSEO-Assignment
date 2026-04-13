import Link from "next/link";

export default function Home() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-20 flex flex-col items-center text-center gap-16">
      {/* Hero */}
      <section className="space-y-6 max-w-2xl">
        {/* Logo hex */}
        <div className="mx-auto w-16 h-16 rounded-2xl bg-purple flex items-center justify-center shadow-[0_0_40px_rgba(132,94,194,0.5)]">
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none" aria-hidden>
            <path
              d="M14 2L24 8V20L14 26L4 20V8L14 2Z"
              stroke="white"
              strokeWidth="2"
              strokeLinejoin="round"
            />
            <circle cx="14" cy="14" r="3" fill="white" />
          </svg>
        </div>

        <div className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-teal">
            Content Intelligence Platform
          </p>
          <h1 className="text-5xl font-bold tracking-tight text-text-hi leading-tight">
            Optimize for the
            <br />
            <span style={{ color: "#845EC2" }}>AI answer layer</span>
          </h1>
          <p className="text-lg text-text-mid leading-relaxed">
            AEGIS scores your content for answer-engine readiness and
            generates intent-mapped sub-queries to expose gaps before your
            competitors do.
          </p>
        </div>
      </section>

      {/* Tool cards */}
      <section className="w-full grid sm:grid-cols-2 gap-5 max-w-3xl">
        <ToolCard
          href="/aeo"
          icon={
            <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden>
              <circle cx="11" cy="11" r="9" stroke="currentColor" strokeWidth="1.8" />
              <path d="M11 6v5l3 3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
            </svg>
          }
          badge="Feature 1"
          title="AEO Content Scorer"
          description="Paste a URL or raw article text. Get a 0–100 AEO score across three checks — direct answer quality, heading hierarchy, and Flesch-Kincaid readability."
          cta="Score content"
          accentColor="#845EC2"
          checks={["Direct Answer Detection", "H-tag Hierarchy", "Snippet Readability"]}
        />
        <ToolCard
          href="/fanout"
          icon={
            <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden>
              <circle cx="4" cy="11" r="2" stroke="currentColor" strokeWidth="1.8" />
              <circle cx="18" cy="5" r="2" stroke="currentColor" strokeWidth="1.8" />
              <circle cx="18" cy="11" r="2" stroke="currentColor" strokeWidth="1.8" />
              <circle cx="18" cy="17" r="2" stroke="currentColor" strokeWidth="1.8" />
              <path d="M6 11h6M6 11l5-5M6 11l5 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          }
          badge="Feature 2"
          title="Query Fan-Out Engine"
          description="Enter a target topic. The engine fans out 10–15 intent-mapped sub-queries via LLM. Optionally paste existing content to see coverage gaps highlighted in real-time."
          cta="Run fan-out"
          accentColor="#00C9A7"
          checks={["6 intent types", "Streaming SSE", "Gap analysis"]}
        />
      </section>

      {/* Stat row */}
      <section className="w-full max-w-3xl grid grid-cols-3 gap-px rounded-2xl overflow-hidden border border-border">
        {[
          { label: "Checks per analysis", value: "3" },
          { label: "Intent types", value: "6" },
          { label: "Sub-queries generated", value: "10–15" },
        ].map((stat) => (
          <div key={stat.label} className="bg-surface px-6 py-5 text-center">
            <p className="text-3xl font-bold text-text-hi">{stat.value}</p>
            <p className="text-xs text-text-lo mt-1">{stat.label}</p>
          </div>
        ))}
      </section>
    </div>
  );
}

interface ToolCardProps {
  href: string;
  icon: React.ReactNode;
  badge: string;
  title: string;
  description: string;
  cta: string;
  accentColor: string;
  checks: string[];
}

function ToolCard({ href, icon, badge, title, description, cta, accentColor, checks }: ToolCardProps) {
  return (
    <Link
      href={href}
      className="group relative flex flex-col gap-4 p-6 rounded-2xl bg-surface border border-border
                 hover:border-border-hi transition-all duration-200 text-left
                 hover:shadow-[0_0_30px_rgba(132,94,194,0.1)]"
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center"
          style={{
            backgroundColor: `${accentColor}20`,
            color: accentColor,
            border: `1px solid ${accentColor}33`,
          }}
        >
          {icon}
        </div>
        <span
          className="text-[10px] font-bold uppercase tracking-widest px-2 py-1 rounded-md"
          style={{
            backgroundColor: `${accentColor}15`,
            color: accentColor,
          }}
        >
          {badge}
        </span>
      </div>

      {/* Body */}
      <div className="space-y-2">
        <h2 className="text-base font-bold text-text-hi group-hover:text-white transition-colors">
          {title}
        </h2>
        <p className="text-sm text-text-lo leading-relaxed">{description}</p>
      </div>

      {/* Check list */}
      <ul className="space-y-1">
        {checks.map((c) => (
          <li key={c} className="flex items-center gap-2 text-xs text-text-lo">
            <span style={{ color: accentColor }}>✓</span>
            {c}
          </li>
        ))}
      </ul>

      {/* CTA */}
      <div
        className="mt-auto flex items-center gap-1.5 text-sm font-semibold transition-all duration-150
                   group-hover:gap-2.5"
        style={{ color: accentColor }}
      >
        {cta}
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden>
          <path d="M2 7h10M8 4l4 3-4 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
    </Link>
  );
}
