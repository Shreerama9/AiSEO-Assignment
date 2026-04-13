"use client";

import { useState, useRef } from "react";
import type { AEOResponse, InputType } from "@/lib/types";
import { analyzeAEO, APIError } from "@/lib/api";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Textarea from "@/components/ui/Textarea";
import Card from "@/components/ui/Card";
import ScoreRing from "@/components/aeo/ScoreRing";
import CheckCard from "@/components/aeo/CheckCard";

type Tab = "url" | "text";

export default function AEOPage() {
  const [tab, setTab] = useState<Tab>("url");
  const [urlValue, setUrlValue] = useState("");
  const [textValue, setTextValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AEOResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  const inputValue = tab === "url" ? urlValue : textValue;
  const canSubmit = inputValue.trim().length > 0;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit || loading) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await analyzeAEO({
        input_type: tab as InputType,
        input_value: inputValue.trim(),
      });
      setResult(data);
      // Give DOM time to paint before scrolling
      requestAnimationFrame(() => {
        resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    } catch (err) {
      if (err instanceof APIError) {
        setError(`${err.message} (${err.code})`);
      } else {
        setError("An unexpected error occurred. Is the backend running?");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-12 space-y-10">
      {/* Page header */}
      <header className="space-y-2">
        <div className="flex items-center gap-2.5">
          <div className="w-1 h-6 rounded-full bg-purple" />
          <p className="text-xs font-semibold uppercase tracking-widest text-text-lo">Feature 1</p>
        </div>
        <h1 className="text-3xl font-bold text-text-hi">AEO Content Scorer</h1>
        <p className="text-text-mid leading-relaxed">
          Analyze any URL or paste raw article text to receive a structured AEO score
          across direct-answer quality, heading hierarchy, and readability.
        </p>
      </header>

      {/* Input card */}
      <Card className="p-6 space-y-5">
        {/* Tab switcher */}
        <div className="flex gap-1 p-1 rounded-xl bg-base w-fit">
          {(["url", "text"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => { setTab(t); setError(null); setResult(null); }}
              className={[
                "px-4 py-1.5 rounded-lg text-sm font-semibold transition-all duration-150 cursor-pointer",
                tab === t
                  ? "bg-purple text-white shadow-[0_0_12px_rgba(132,94,194,0.4)]"
                  : "text-text-lo hover:text-text-mid",
              ].join(" ")}
            >
              {t === "url" ? "URL" : "Paste Text"}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {tab === "url" ? (
            <Input
              label="Article URL"
              type="url"
              placeholder="https://example.com/your-article"
              value={urlValue}
              onChange={(e) => setUrlValue(e.target.value)}
              hint="Must be publicly accessible. Cached for 1 hour."
              autoFocus
            />
          ) : (
            <Textarea
              label="Article Text (HTML or plain text)"
              placeholder="Paste your article content here…"
              rows={10}
              value={textValue}
              onChange={(e) => setTextValue(e.target.value)}
              hint="Supports raw HTML — heading tags (H1–H3) are detected automatically."
            />
          )}

          <Button
            type="submit"
            loading={loading}
            disabled={!canSubmit}
            size="md"
            className="w-full"
          >
            {loading ? "Analyzing…" : "Analyze Content"}
          </Button>
        </form>
      </Card>

      {/* Error state */}
      {error && (
        <div className="rounded-xl border border-danger/30 bg-danger/10 px-5 py-4 text-sm text-danger">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div ref={resultsRef} className="space-y-6 fade-up">
          {/* Score hero */}
          <Card className="p-8 flex flex-col sm:flex-row items-center gap-8">
            <ScoreRing score={result.aeo_score} band={result.band} />
            <div className="flex-1 space-y-3 text-center sm:text-left">
              <h2 className="text-xl font-bold text-text-hi">Analysis Complete</h2>
              <p className="text-text-mid text-sm leading-relaxed">
                Your content scored{" "}
                <strong className="text-text-hi">{result.aeo_score}/100</strong> for
                answer-engine optimization. The band{" "}
                <strong className="text-text-hi">{result.band}</strong> reflects your
                current readiness for AI snippet selection.
              </p>
              {/* Score legend */}
              <div className="flex flex-wrap gap-3 justify-center sm:justify-start text-xs text-text-lo">
                {[
                  { range: "85–100", label: "AEO Optimized", color: "#00C9A7" },
                  { range: "65–84",  label: "Needs Improvement", color: "#845EC2" },
                  { range: "40–64",  label: "Significant Gaps", color: "#FFB347" },
                  { range: "0–39",   label: "Not AEO Ready", color: "#FF6B6B" },
                ].map((b) => (
                  <span key={b.range} className="flex items-center gap-1">
                    <span
                      className="w-2 h-2 rounded-full inline-block"
                      style={{ backgroundColor: b.color }}
                    />
                    {b.range}: {b.label}
                  </span>
                ))}
              </div>
            </div>
          </Card>

          {/* Check breakdown */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-text-lo px-1">
              Check Breakdown
            </h3>
            {result.checks.map((check, i) => (
              <CheckCard key={check.check_id} check={check} index={i} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
