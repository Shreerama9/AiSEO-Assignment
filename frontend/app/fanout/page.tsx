"use client";

import { useState, useRef, useCallback } from "react";
import type { SubQuery, SubQueryType, GapSummary, StreamMeta } from "@/lib/types";
import { streamFanout, APIError } from "@/lib/api";
import { useKeyboardSubmit } from "@/lib/useKeyboardSubmit";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Textarea from "@/components/ui/Textarea";
import Card from "@/components/ui/Card";
import SubQueryCard from "@/components/fanout/SubQueryCard";
import GapSummaryPanel from "@/components/fanout/GapSummary";
import SkeletonCards from "@/components/fanout/SkeletonCards";
import IntentBreakdown from "@/components/fanout/IntentBreakdown";
import CopyButton from "@/components/ui/CopyButton";

type StreamStatus = "idle" | "streaming" | "done" | "error";

const INTENT_META: Record<string, { label: string; desc: string; icon: string }> = {
  comparative:      { label: "Comparative",      desc: "How X compares to alternatives",          icon: "⚖️" },
  feature_specific: { label: "Feature Specific", desc: "Deep dives on individual capabilities",   icon: "🔧" },
  use_case:         { label: "Use Case",         desc: "Real-world applications",                 icon: "💡" },
  trust_signals:    { label: "Trust Signals",    desc: "Reviews, case studies, credibility",      icon: "🛡️" },
  how_to:           { label: "How To",           desc: "Step-by-step instructional queries",      icon: "📖" },
  definitional:     { label: "Definitional",     desc: "What-is / concept clarity queries",       icon: "📚" },
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
  const [activeFilter, setActiveFilter] = useState<SubQueryType | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const resultsRef = useRef<HTMLDivElement>(null);
  const formRef = useRef<HTMLFormElement>(null);

  const canSubmit = query.trim().length > 0;
  const isStreaming = status === "streaming";

  useKeyboardSubmit(
    useCallback(() => formRef.current?.requestSubmit(), []),
    canSubmit && !isStreaming,
  );
  const hasSomeResults = subQueries.length > 0;

  // Count per intent type for badge display
  const typeCounts = subQueries.reduce<Record<string, number>>((acc, sq) => {
    acc[sq.type] = (acc[sq.type] ?? 0) + 1;
    return acc;
  }, {});

  const visibleQueries = activeFilter
    ? subQueries.filter((sq) => sq.type === activeFilter)
    : subQueries;

  const handleStop = useCallback(() => {
    abortRef.current?.abort();
    setStatus("done");
  }, []);

  function toggleFilter(type: SubQueryType) {
    setActiveFilter((prev) => (prev === type ? null : type));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit || isStreaming) return;

    setStatus("streaming");
    setError(null);
    setMeta(null);
    setSubQueries([]);
    setGapSummary(null);
    setActiveFilter(null);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const response = await streamFanout({
        target_query: query.trim(),
        existing_content: showContentInput && existingContent.trim()
          ? existingContent.trim()
          : undefined,
      });

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
          if (raw === "[DONE]") { setStatus("done"); return; }

          let parsed: Record<string, unknown>;
          try { parsed = JSON.parse(raw); } catch { continue; }

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
      if (err instanceof DOMException && err.name === "AbortError") {
        // User stopped — status already set to done
      } else if (err instanceof APIError) {
        setError(err.friendly);
        setStatus("error");
      } else {
        setError("Stream failed. Is the backend running and OPENAI_API_KEY set?");
        setStatus("error");
      }
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-12 space-y-8">
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

      {/* Intent filter chips */}
      <div
        role="group"
        aria-label="Filter by intent type"
        className="grid grid-cols-2 sm:grid-cols-3 gap-2"
      >
        {Object.entries(INTENT_META).map(([type, meta]) => {
          const count = typeCounts[type] ?? 0;
          const isActive = activeFilter === type;
          const isFilterable = hasSomeResults;

          return (
            <button
              key={type}
              type="button"
              role={isFilterable ? "checkbox" : undefined}
              aria-checked={isFilterable ? isActive : undefined}
              disabled={isFilterable && count === 0}
              onClick={() => isFilterable && toggleFilter(type as SubQueryType)}
              className={[
                "relative text-left rounded-xl p-3 space-y-0.5 border transition-all duration-150",
                isFilterable
                  ? "cursor-pointer"
                  : "cursor-default",
                isActive
                  ? "bg-[rgba(132,94,194,0.15)] border-purple shadow-[0_0_12px_rgba(132,94,194,0.2)]"
                  : isFilterable && count > 0
                  ? "bg-surface border-border hover:border-border-hi hover:bg-elevated"
                  : "bg-surface border-border opacity-40",
              ].join(" ")}
            >
              {/* Count badge — shown once results exist */}
              {isFilterable && count > 0 && (
                <span
                  className={[
                    "absolute top-2.5 right-2.5 text-[10px] font-bold tabular-nums px-1.5 py-0.5 rounded-md",
                    isActive
                      ? "bg-purple text-white"
                      : "bg-elevated text-text-lo border border-border",
                  ].join(" ")}
                >
                  {count}
                </span>
              )}
              <p className={[
                "text-xs font-semibold capitalize flex items-center gap-1.5",
                isActive ? "text-purple-light" : "text-purple-light",
              ].join(" ")}>
                <span aria-hidden>{meta.icon}</span>
                {meta.label}
              </p>
              <p className="text-[11px] text-text-lo leading-tight pr-6">{meta.desc}</p>
            </button>
          );
        })}
      </div>

      {/* Active filter indicator */}
      {activeFilter && (
        <div className="flex items-center gap-2 text-xs">
          <span className="text-text-lo">Showing:</span>
          <span className="px-2 py-0.5 rounded-md bg-[rgba(132,94,194,0.2)] text-purple-light border border-[rgba(132,94,194,0.3)] font-semibold capitalize">
            {INTENT_META[activeFilter]?.label}
          </span>
          <span className="text-text-lo">({visibleQueries.length} of {subQueries.length})</span>
          <button
            type="button"
            onClick={() => setActiveFilter(null)}
            className="ml-1 text-text-lo hover:text-text-mid underline underline-offset-2 cursor-pointer"
          >
            Clear
          </button>
        </div>
      )}

      {/* Input card */}
      <Card className="p-6 space-y-5">
        <form ref={formRef} onSubmit={handleSubmit} className="space-y-5">
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
            {!isStreaming && (
              <kbd className="hidden sm:inline-flex items-center gap-1 px-2 py-1 rounded-md border border-border bg-elevated text-[10px] text-text-lo font-mono shrink-0">
                ⌘ Enter
              </kbd>
            )}
            {isStreaming && (
              <Button type="button" variant="secondary" size="md" onClick={handleStop}>
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
                  <span className="w-2 h-2 rounded-full bg-teal sse-dot" aria-hidden />
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
                  getValue={() =>
                    visibleQueries
                      .map((sq, i) => `${i + 1}. [${sq.type}] ${sq.query}`)
                      .join("\n")
                  }
                />
              )}
              {meta && (
                <p className="text-xs text-text-lo font-mono">model: {meta.model_used}</p>
              )}
            </div>
          </div>

          <div className="grid sm:grid-cols-3 gap-5">
            {/* Sub-query list */}
            <div className="sm:col-span-2 space-y-2">
              {visibleQueries.length === 0 && isStreaming && <SkeletonCards />}
              {visibleQueries.length === 0 && !isStreaming && activeFilter && (
                <p className="text-sm text-text-lo text-center py-8">
                  No {INTENT_META[activeFilter]?.label} queries generated.
                </p>
              )}
              {visibleQueries.map((sq, i) => (
                <SubQueryCard
                  key={`${sq.type}-${sq.query.slice(0, 40)}`}
                  item={sq}
                  index={i}
                />
              ))}
            </div>

            {/* Sidebar */}
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

              {status === "done" && subQueries.length > 0 && (
                <IntentBreakdown
                  subQueries={subQueries}
                  activeFilter={activeFilter}
                  onFilterClick={(t) => toggleFilter(t)}
                />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

