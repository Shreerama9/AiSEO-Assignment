# AEGIS — AEO & GEO Content Intelligence Platform

A FastAPI service with two AI-powered content analysis features:

- **Feature 1 — AEO Content Scorer** (`POST /api/aeo/analyze`)
- **Feature 2 — Query Fan-Out Engine** (`POST /api/fanout/generate`, `POST /api/fanout/stream`)

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY
```

### 3. Run the server

```bash
uvicorn app.main:app --reload
```

API at `http://localhost:8000` · Interactive docs at `http://localhost:8000/docs`

### Docker

```bash
docker compose up --build
```

---

## Running tests

```bash
pytest
```

The fanout and streaming tests mock the LLM — no API key needed.
`tests/test_threshold.py` requires `sentence-transformers` and runs the embedding model locally.

---

## Features

### Feature 1 — AEO Content Scorer ✅

| Check | What it tests | Max pts |
|-------|--------------|---------|
| A — Direct Answer Detection | First paragraph ≤ 60 words, declarative, no hedging | 20 |
| B — H-tag Hierarchy | Valid H1→H2→H3 structure, no skips, no duplicates | 20 |
| C — Snippet Readability | Flesch-Kincaid Grade Level 7–9 | 20 |

Score = `(A + B + C) / 60 × 100`

**Endpoint:** `POST /api/aeo/analyze`
```json
{"input_type": "url", "input_value": "https://example.com/article"}
{"input_type": "text", "input_value": "Your article text here..."}
```

URL responses are cached for 1 hour (SHA-256 keyed TTLCache) to avoid re-fetching the same page.

### Feature 2 — Query Fan-Out Engine ✅

- LLM generates 10–15 sub-queries across 6 intent types
- Retry logic with exponential backoff (up to 3 attempts)
- JSON mode + Pydantic validation
- Optional gap analysis via sentence-transformers cosine similarity
- Streaming endpoint (`POST /api/fanout/stream`) emits sub-queries as Server-Sent Events

**Endpoints:**
```
POST /api/fanout/generate   — full JSON response
POST /api/fanout/stream     — SSE stream, one event per sub-query
```

---

## Design decisions

### LLM JSON reliability

Three layers of defence:
1. **OpenAI JSON mode** — constrains the model to emit valid JSON at the API level
2. **Markdown fence stripping** — regex strips ` ```json ... ``` ` wrappers as a fallback
3. **Pydantic validation** — each sub-query is validated against the `SubQuery` schema before returning

If all 3 attempts fail, the endpoint returns `503` with a structured `LLMUnavailableError`.

### Prompt design

See `PROMPT_LOG.md` for the full iteration history. The production prompt uses a system/user message split, lists exact enum string values, and includes a 12-query example output to anchor format. This reduced the retry rate from ~30% (Draft 1) to ~5%.

### Content extraction — trafilatura + BeautifulSoup fallback

URL content is extracted with `trafilatura`, which handles real-world pages (ads, nav, cookie banners) far better than tag stripping alone. If trafilatura returns nothing, BeautifulSoup falls back to `<p>` tag extraction, then plain-text block splitting.

### Embedding model — `all-MiniLM-L6-v2`

| Model | Params | Speed |
|-------|--------|-------|
| `all-MiniLM-L6-v2` | 22M | 1× (chosen) |
| `all-mpnet-base-v2` | 110M | ~5× slower |

For coverage detection at our 0.72 threshold, the accuracy difference is not practically significant. In a production high-stakes context (brand monitoring, compliance) I'd switch to mpnet or a domain-fine-tuned model.

### Similarity threshold — 0.72

| Range | Meaning |
|-------|---------|
| < 0.60 | Likely noise / unrelated |
| 0.60–0.72 | Related but not specific angle |
| 0.72–0.85 | Clear topical coverage |
| > 0.85 | Near-duplicate |

`tests/test_threshold.py` sweeps 0.50→0.90 and asserts the production threshold is within 0.05 of the empirically optimal F1. To tune it properly: label 50–100 (query, content, covered) pairs and plot P/R/F1 curves.

### Async / CPU-bound work

spaCy, textstat, and sentence-transformers are all CPU-bound synchronous libraries. Each AEO check runs in a `ThreadPoolExecutor` via `asyncio.to_thread` / `asyncio.gather` so concurrent requests don't block each other. Model loading uses a thread-safe double-checked locking pattern (replacing the earlier `lru_cache` singleton) and is pre-warmed in the `lifespan` handler at startup.

---

## What I'd improve with more time

1. **True streaming** — use OpenAI's streaming API with partial JSON assembly in `/api/fanout/stream` for genuine token-level streaming instead of buffering the full response first
2. **Threshold auto-tuning** — build a labelled evaluation set to find the empirically optimal similarity threshold (harness is in `tests/test_threshold.py`)
3. **Playwright fallback** — for JS-rendered pages, add an optional Playwright fetch path behind a flag
4. **Cache invalidation endpoint** — `DELETE /api/cache` for cases where stale HTML is served post-login-wall
5. **Workers** — expose `--workers N` in Docker CMD and document horizontal scaling
