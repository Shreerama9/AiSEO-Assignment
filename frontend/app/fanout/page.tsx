"use client";

import { useState, useRef, useCallback } from "react";
import type { SubQuery, GapSummary, StreamMeta } from "@/lib/types";
import { streamFanout, APIError } from "@/lib/api";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Textarea from "@/components/ui/Textarea";
import Card from "@/components/ui/Card";
import SubQueryCard from "@/components/fanout/SubQueryCard";
import GapSummaryPanel from "@/components/fanout/GapSummary";
import CopyButton from "@/components/ui/CopyButton";

type StreamStatus = "idle" | "streaming" | "done" | "error";

const INTENT_DESCRIPTIONS: Record<string, string> = {
  comparative:      "How X compares to alternatives",
  feature_specific: "Deep dives on individual capabilities",
  use_case:         "Real-world applications",
  trust_signals:    "Reviews, case studies, credibility",
  how_to:           "Step-by-step instructional queries",
  definitional:     "What-is / concept clarity queries",
};

export default function FanoutPage() {
  const [query, setQuery] = useState("");
  const [existingContent, setExistingContent] = useState("");
  const [showContentInput, setShowContentInput] = useState(false);
  const [status, setStatus] = useState<StreamStatus>("idle");
  const [meta, setMeta] = useState<StreamMeta | null>(null);
  const [subQueries, setSubQueries] = useState<SubQuery[]>([]);
  const [gapSummary, setGapSummary] = useState<GapSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  const canSubmit = query.trim().length > 0;

  const handleStop = useCallback(() => {
    abortRef.current?.abort();
    setStatus("done");
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit || status === "streaming") return;

    // Reset state
    setStatus("streaming");
    setError(null);
    setMeta(null);
    setSubQueries([]);
    setGapSummary(null);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const response = await streamFanout({
        target_query: query.trim(),
        existing_content: showContentInput && existingContent.trim()
          ? existingContent.trim()
          : undefined,
      });

      // Scroll to results area
      requestAnimationFrame(() => {
        resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      });

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done || controller.signal.aborted) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const raw = line.slice(6).trim();
          if (raw === "[DONE]") {
            setStatus("done");
            return;
          }

          let parsed: Record<string, unknown>;
          try {
            parsed = JSON.parse(raw);
          } catch {
            continue;
          }

          if ("error" in parsed) {
            setError(String(parsed.detail ?? parsed.error));
            setStatus("error");
            return;
          }

          if ("target_query" in parsed && "model_used" in parsed) {
            setMeta(parsed as unknown as StreamMeta);
          } else if ("gap_summary" in parsed && parsed.gap_summary) {
            setGapSummary(parsed.gap_summary as GapSummary);
          } else if ("type" in parsed && "query" in parsed) {
            setSubQueries((prev) => [...prev, parsed as unknown as SubQuery]);
          }
        }
      }

      setStatus("done");
    } catch (err) {
      if (err instanceof APIError) {
        setError(`${err.message} (${err.code})`);
      } else if (err instanceof DOMException && err.name === "AbortError") {
        // User stopped — status already set to done
      } else if (err instanceof APIError) {
        setError(err.friendly);
      } else {
        setError("Stream failed. Is the backend running and OPENAI_API_KEY set?");
      }
      setStatus("error");
    }
  }

  const isStreaming = status === "streaming";
  const hasSomeResults = subQueries.length > 0;

  return (
    <div className="mx-auto max-w-3xl px-6 py-12 space-y-10">
      {/* Page header */}
      <header className="space-y-2">
        <div className="flex items-center gap-2.5">
          <div className="w-1 h-6 rounded-full bg-teal" />
          <p className="text-xs font-semibold uppercase tracking-widest text-text-lo">Feature 2</p>
        </div>
        <h1 className="text-3xl font-bold text-text-hi">Query Fan-Out Engine</h1>
        <p className="text-text-mid leading-relaxed">
          Enter a topic or seed query. The engine fans out 10–15 intent-mapped sub-queries
          across 6 intent types via LLM. Paste existing content to see real-time coverage gaps.
        </p>
      </header>

      {/* Intent legend */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {Object.entries(INTENT_DESCRIPTIONS).map(([type, desc]) => (
          <div key={type} className="rounded-xl bg-surface border border-border p-3 space-y-0.5">
            <p className="text-xs font-semibold text-purple-light capitalize">
              {type.replace("_", " ")}
            </p>
            <p className="text-[11px] text-text-lo leading-tight">{desc}</p>
          </div>
        ))}
      </div>

      {/* Input card */}
      <Card className="p-6 space-y-5">
        <form onSubmit={handleSubmit} className="space-y-5">
          <Input
            label="Target Query / Topic"
            placeholder="e.g. best project management software for remote teams"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            hint="Be specific — a narrow query produces more actionable sub-queries."
            autoFocus
          />

          {/* Optional content toggle */}
          <div className="space-y-3">
            <button
              type="button"
              onClick={() => setShowContentInput((v) => !v)}
              className="flex items-center gap-2 text-sm text-text-lo hover:text-text-mid transition-colors duration-150 cursor-pointer"
            >
              <span
                className={[
                  "w-4 h-4 rounded border flex items-center justify-center transition-colors duration-150",
                  showContentInput ? "bg-teal border-teal" : "border-border",
                ].join(" ")}
              >
                {showContentInput && (
                  <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden>
                    <path d="M2 5l2.5 2.5L8 3" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
                  </svg>
                )}
              </span>
              Include existing content for gap analysis
            </button>

            {showContentInput && (
              <Textarea
                label="Existing Content"
                placeholder="Paste your existing article or page content here…"
                rows={8}
                value={existingContent}
                onChange={(e) => setExistingContent(e.target.value)}
                hint="Queries will be scored for coverage via cosine similarity (threshold: 0.72)."
              />
            )}
          </div>

          <div className="flex gap-3">
            <Button
              type="submit"
              loading={isStreaming && !hasSomeResults}
              disabled={!canSubmit || (isStreaming && !hasSomeResults)}
              size="md"
              className="flex-1"
            >
              {isStreaming ? "Streaming…" : "Generate Sub-Queries"}
            </Button>
            {isStreaming && (
              <Button
                type="button"
                variant="secondary"
                size="md"
                onClick={handleStop}
              >
                Stop
              </Button>
            )}
          </div>
        </form>
      </Card>

      {/* Error */}
      {error && (
        <div role="alert" className="rounded-xl border border-danger/30 bg-danger/10 px-5 py-4 text-sm text-danger">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Results */}
      {(isStreaming || hasSomeResults) && (
        <div ref={resultsRef} className="space-y-6">
          {/* Meta bar */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {isStreaming && (
                <div className="flex items-center gap-2 text-xs text-teal" role="status" aria-live="polite">
                  <span
                    className="w-2 h-2 rounded-full bg-teal sse-dot"
                    aria-hidden
                  />
                  Live streaming
                </div>
              )}
              {status === "done" && (
                <p className="text-xs text-teal font-semibold">
                  ✓ Complete — {subQueries.length} sub-queries
                </p>
              )}
            </div>
            <div className="flex items-center gap-3">
              {status === "done" && subQueries.length > 0 && (
                <CopyButton
                  label="Copy all queries"
                  getValue={() => subQueries.map((sq, i) => `${i + 1}. [${sq.type}] ${sq.query}`).join("\n")}
                />
              )}
              {meta && (
                <p className="text-xs text-text-lo font-mono">
                  model: {meta.model_used}
                </p>
              )}
            </div>
          </div>

          <div className="grid sm:grid-cols-3 gap-5">
            {/* Sub-query list */}
            <div className="sm:col-span-2 space-y-2">
              {subQueries.length === 0 && isStreaming && (
                <SkeletonCards />
              )}
              {subQueries.map((sq, i) => (
                <SubQueryCard key={i} item={sq} index={i} />
              ))}
            </div>

            {/* Gap summary sidebar */}
            <div className="space-y-4">
              {gapSummary ? (
                <GapSummaryPanel summary={gapSummary} />
              ) : showContentInput && isStreaming ? (
                <Card className="p-5 space-y-3">
                  <p className="text-xs font-semibold text-text-lo uppercase tracking-wider">
                    Coverage Analysis
                  </p>
                  <div className="space-y-2">
                    <div className="h-2.5 rounded-full skeleton" />
                    <div className="h-2.5 w-3/4 rounded-full skeleton" />
                  </div>
                </Card>
              ) : null}

              {/* Stats card (shown once done) */}
              {status === "done" && subQueries.length > 0 && (
                <IntentBreakdown subQueries={subQueries} />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function SkeletonCards() {
  return (
    <>
      {[...Array(4)].map((_, i) => (
        <div
          key={i}
          className="h-16 rounded-xl skeleton"
          style={{ animationDelay: `${i * 0.1}s` }}
        />
      ))}
    </>
  );
}

function IntentBreakdown({ subQueries }: { subQueries: SubQuery[] }) {
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
          .map(([type, count]) => (
            <div key={type} className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-text-mid capitalize">{type.replace("_", " ")}</span>
                <span className="text-text-lo tabular-nums">{count}/{total}</span>
              </div>
              <div className="h-1 rounded-full bg-border overflow-hidden">
                <div
                  className="h-full rounded-full bg-purple transition-all duration-500"
                  style={{ width: `${(count / total) * 100}%` }}
                />
              </div>
            </div>
          ))}
      </div>
    </Card>
  );
}
