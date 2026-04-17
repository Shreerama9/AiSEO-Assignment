"""
Integration tests — hit the real FastAPI app via httpx.AsyncClient (no live server).
LLM calls are mocked so no OPENAI_API_KEY is required.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Health endpoints
# ---------------------------------------------------------------------------

async def test_root_health(client: AsyncClient) -> None:
    resp = await client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_health_endpoint(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "aeo_scorer" in body["ready"]
    assert "fanout_engine" in body["ready"]


# ---------------------------------------------------------------------------
# AEO Scorer — text input
# ---------------------------------------------------------------------------

AEO_SAMPLE_HTML = """
<html><body>
<h1>What Is SEO?</h1>
<p>SEO stands for Search Engine Optimization. It is the practice of improving
a website so it ranks higher in search engine results pages.</p>
<h2>Why SEO Matters</h2>
<p>Higher rankings mean more organic traffic and better visibility.</p>
<h3>Key Techniques</h3>
<p>Keyword research, link building, and technical optimisation are core to SEO.</p>
</body></html>
"""


async def test_aeo_analyze_text_returns_score(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/aeo/analyze",
        json={"input_type": "text", "input_value": AEO_SAMPLE_HTML},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert 0 <= body["aeo_score"] <= 100
    assert body["band"] in {"AEO Optimized", "Needs Improvement", "Significant Gaps", "Not AEO Ready"}
    assert len(body["checks"]) == 3


async def test_aeo_analyze_check_fields(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/aeo/analyze",
        json={"input_type": "text", "input_value": AEO_SAMPLE_HTML},
    )
    for check in resp.json()["checks"]:
        assert "check_id" in check
        assert "score" in check
        assert "max_score" in check
        assert check["score"] <= check["max_score"]


async def test_aeo_rejects_empty_input(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/aeo/analyze",
        json={"input_type": "text", "input_value": "   "},
    )
    assert resp.status_code == 422


async def test_aeo_rejects_oversized_input(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/aeo/analyze",
        json={"input_type": "text", "input_value": "x" * 50_001},
    )
    assert resp.status_code == 422


async def test_aeo_blocks_ssrf_localhost(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/aeo/analyze",
        json={"input_type": "url", "input_value": "http://localhost/secret"},
    )
    assert resp.status_code == 422
    assert "url_fetch_failed" in resp.text


async def test_aeo_blocks_ssrf_private_ip(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/aeo/analyze",
        json={"input_type": "url", "input_value": "http://192.168.1.1/admin"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Cache endpoint
# ---------------------------------------------------------------------------

async def test_cache_clear_all(client: AsyncClient) -> None:
    resp = await client.delete("/api/cache")
    assert resp.status_code == 200
    body = resp.json()
    assert "cleared" in body


async def test_cache_clear_specific_url(client: AsyncClient) -> None:
    resp = await client.request(
        "DELETE",
        "/api/cache",
        json={"url": "https://example.com/article"},
    )
    assert resp.status_code == 200
    assert resp.json()["url"] == "https://example.com/article"


# ---------------------------------------------------------------------------
# Fan-Out Engine — mocked LLM
# ---------------------------------------------------------------------------

from app.models.schemas import SubQuery, SubQueryType  # noqa: E402

_MOCK_SUBQUERIES = [
    SubQuery(type=SubQueryType.definitional,     query="What is project management?"),
    SubQuery(type=SubQueryType.how_to,           query="How to manage remote teams?"),
    SubQuery(type=SubQueryType.comparative,      query="Asana vs Trello for remote teams"),
    SubQuery(type=SubQueryType.feature_specific, query="Gantt chart features in PM tools"),
    SubQuery(type=SubQueryType.use_case,         query="PM tools for software development"),
    SubQuery(type=SubQueryType.trust_signals,    query="Best reviewed project management apps"),
]


async def test_fanout_generate_mocked(client: AsyncClient) -> None:
    with patch(
        "app.api.fanout.call_llm_with_retry",
        new=AsyncMock(return_value=(_MOCK_SUBQUERIES, "gpt-4o-mini")),
    ):
        resp = await client.post(
            "/api/fanout/generate",
            json={"target_query": "best project management software"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_sub_queries"] == len(_MOCK_SUBQUERIES)
    assert body["model_used"] == "gpt-4o-mini"
    assert len(body["sub_queries"]) == len(_MOCK_SUBQUERIES)


async def test_fanout_rejects_empty_query(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/fanout/generate",
        json={"target_query": ""},
    )
    assert resp.status_code == 422


async def test_fanout_rejects_oversized_query(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/fanout/generate",
        json={"target_query": "x" * 501},
    )
    assert resp.status_code == 422


async def test_fanout_stream_mocked(client: AsyncClient) -> None:
    with patch(
        "app.api.fanout.call_llm_with_retry",
        new=AsyncMock(return_value=(_MOCK_SUBQUERIES, "gpt-4o-mini")),
    ):
        resp = await client.post(
            "/api/fanout/stream",
            json={"target_query": "best project management software"},
            headers={"Accept": "text/event-stream"},
        )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    lines = [l for l in resp.text.splitlines() if l.startswith("data: ")]
    assert any("[DONE]" in l for l in lines)
