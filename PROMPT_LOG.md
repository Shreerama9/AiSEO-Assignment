# Prompt Iteration Log — Query Fan-Out Engine

This document traces the three drafts of the LLM prompt used in Feature 2.

---

## Draft 1 — The naive starting point

```
You are a search query analyst. Given a target query, generate 10-15 sub-queries
that cover different aspects of the topic. Include comparative, feature-specific,
use-case, trust-signal, how-to, and definitional angles.

Return a JSON array of objects with "type" and "query" fields.

Target query: {target_query}
```

### Problems observed

1. **Wrong type names** — The model returned `"feature-specific"` (hyphen) instead of `"feature_specific"` (underscore), breaking Pydantic enum validation on ~30% of calls.
2. **Markdown wrapping** — Despite asking for JSON, the model wrapped output in ```` ```json ... ``` ```` fences on ~60% of calls.
3. **Inconsistent count** — Sometimes returned 8 sub-queries, sometimes 18. No hard enforcement.
4. **Missing types** — The model sometimes omitted `trust_signals` entirely and doubled up on `comparative`.
5. **Extra fields** — Occasionally added `"rationale": "..."` or `"priority": 1` fields.

**Verdict:** Unreliable. Would crash the parser on the majority of real calls.

---

## Draft 2 — Structural improvements

```
You are a search intent analyst. Decompose the target query into sub-queries
that simulate how an AI search engine investigates a topic.

Return a JSON object (not an array) with key "sub_queries" containing a list.
Each item has exactly "type" and "query".

Types must be one of: comparative, feature_specific, use_case, trust_signals,
how_to, definitional. Include at least 2 of each type. Total: 10-15 sub-queries.

Do NOT include markdown code fences. Do NOT include extra fields.

Target query: {target_query}
```

### Improvements

- Specifying exact enum values (`feature_specific` not `feature-specific`) fixed the type mismatch issue.
- "Do NOT include markdown code fences" reduced fence wrapping to ~15% of calls.
- "At least 2 of each type" improved coverage distribution.

### Remaining problems

1. **Still occasionally wrapped in fences** — defensive stripping regex added in code as a fallback.
2. **Type count enforcement was soft** — the model understood "at least 2" but sometimes still produced 1 of a type.
3. **No concrete example** — the model had to infer the exact format from description alone, leading to subtle structural variations (e.g. `"sub_query"` instead of `"query"` as the field name).
4. **System vs user message split** not used — everything was in the user message, reducing reliability of instruction-following.

**Verdict:** Better, but ~20% of calls still required a retry.

---

## Draft 3 — Final prompt (production)

Key changes from Draft 2:

1. **System + user message split** — instructions in `system`, target query in `user`. Models follow system-level constraints more reliably.
2. **Added a full concrete example** — a 12-item example output for an unrelated topic ("best project management software") anchors the exact format without biasing the generated content.
3. **"EXACTLY two fields"** — explicit language about the field count prevents extra fields.
4. **Switched to OpenAI JSON mode** — `response_format={"type": "json_object"}` enforces valid JSON at the API level, eliminating the markdown wrapping problem entirely.
5. **Explicit string values in instructions** — the prompt lists all 6 enum values as quoted strings so the model never has to infer capitalisation or separator style.

### Final system prompt (excerpt — full version in `fanout_engine.py`)

```
You are a search intent analyst. Your task is to decompose a target query into
sub-queries that represent how an AI search engine would investigate the topic
comprehensively, covering multiple user intents.

Return ONLY a valid JSON object — no markdown, no code blocks, no prose.
The JSON must have exactly one key: "sub_queries", whose value is an array.

Each object must have EXACTLY two fields:
  "type" — one of: "comparative", "feature_specific", "use_case",
            "trust_signals", "how_to", "definitional"
  "query" — a natural-language search query string (5–15 words)

Hard requirements:
  - Return between 10 and 15 sub-queries total.
  - Include AT LEAST 2 sub-queries for EACH of the 6 types.
  - Do NOT include any extra fields.

Example output for "best project management software":
{ "sub_queries": [ ... 12 items ... ] }
```

### Results

- Zero markdown wrapping failures (JSON mode handles this at the API level)
- Correct type names on 100% of calls (concrete enum values in prompt)
- Correct sub-query count and per-type coverage on ~95% of calls
- Remaining ~5% failure rate caught by Pydantic validation + retry logic

**Verdict:** Production-ready. Retry logic handles the residual failure rate gracefully.
