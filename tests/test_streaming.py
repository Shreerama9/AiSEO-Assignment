"""Integration tests for POST /api/fanout/stream. LLM calls are mocked."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.schemas import SubQueryType

_VALID_PAYLOAD = json.dumps({
    "sub_queries": [
        {"type": "comparative",      "query": "Tool A vs Tool B for SEO"},
        {"type": "comparative",      "query": "Tool A vs Tool C pricing"},
        {"type": "feature_specific", "query": "AI writing tool with keyword clustering"},
        {"type": "feature_specific", "query": "AI content tool with SERP analysis"},
        {"type": "use_case",         "query": "AI writing tool for agency production"},
        {"type": "use_case",         "query": "AI assistant for ecommerce descriptions"},
        {"type": "trust_signals",    "query": "AI SEO tool case studies 2025"},
        {"type": "trust_signals",    "query": "AI content tool reviews G2 Capterra"},
        {"type": "how_to",           "query": "how to optimize blog content with AI"},
        {"type": "how_to",           "query": "how to set up an AI writing workflow"},
        {"type": "definitional",     "query": "what is AI-assisted SEO content writing"},
        {"type": "definitional",     "query": "definition of generative engine optimization"},
    ]
})


def _mock_openai(content: str):
    """Return a context manager that stubs AsyncOpenAI with a fixed response."""
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]

    return patch("app.services.fanout_engine.AsyncOpenAI", return_value=AsyncMock(
        **{"chat.completions.create": AsyncMock(return_value=resp)}
    ))


def _parse_events(raw: bytes) -> list[dict]:
    """Parse SSE lines into dicts, stopping at [DONE]."""
    out = []
    for line in raw.decode().splitlines():
        if line.startswith("data: "):
            payload = line[6:]
            if payload == "[DONE]":
                break
            out.append(json.loads(payload))
    return out


@pytest.fixture(autouse=True)
def set_api_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")


@pytest.fixture
def valid_mock():
    return _mock_openai(_VALID_PAYLOAD)


async def _post_stream(query: str = "best AI SEO tool", **extra):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.post("/api/fanout/stream", json={"target_query": query, **extra})


@pytest.mark.asyncio
async def test_content_type(valid_mock):
    with valid_mock:
        resp = await _post_stream()
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]


@pytest.mark.asyncio
async def test_metadata_header_is_first_event(valid_mock):
    with valid_mock:
        resp = await _post_stream()
    events = _parse_events(resp.content)
    assert "target_query" in events[0]
    assert "model_used" in events[0]
    assert events[0]["target_query"] == "best AI SEO tool"


@pytest.mark.asyncio
async def test_all_sub_queries_emitted(valid_mock):
    with valid_mock:
        resp = await _post_stream()
    events = _parse_events(resp.content)
    sub_queries = [e for e in events[1:] if "type" in e and "query" in e]
    assert len(sub_queries) == 12

    valid_types = {t.value for t in SubQueryType}
    for sq in sub_queries:
        assert sq["type"] in valid_types
        assert isinstance(sq["query"], str)


@pytest.mark.asyncio
async def test_done_sentinel(valid_mock):
    with valid_mock:
        resp = await _post_stream()
    assert b"data: [DONE]" in resp.content


@pytest.mark.asyncio
async def test_llm_failure_emits_error_event():
    bad_mock = _mock_openai("not json at all")
    with bad_mock, patch("app.services.fanout_engine.asyncio.sleep", new_callable=AsyncMock):
        resp = await _post_stream("test query")
    assert resp.status_code == 200
    events = _parse_events(resp.content)
    assert events[0].get("error") == "llm_unavailable"


@pytest.mark.asyncio
async def test_gap_summary_included_when_content_provided(valid_mock):
    # Mock analyze_gaps so this test doesn't trigger model download/loading.
    # The gap analysis logic is covered separately in test_threshold.py.
    fake_summary = MagicMock()
    fake_summary.model_dump.return_value = {
        "covered": 3, "total": 12, "coverage_percent": 25,
        "covered_types": ["definitional"], "missing_types": ["comparative"],
    }

    with valid_mock, patch("app.api.fanout.analyze_gaps", return_value=([], fake_summary)):
        resp = await _post_stream(existing_content="some content about SEO and AI")

    events = _parse_events(resp.content)
    gap_events = [e for e in events if "gap_summary" in e]
    assert len(gap_events) == 1
    gs = gap_events[0]["gap_summary"]
    assert {"covered", "total", "coverage_percent"} <= gs.keys()
