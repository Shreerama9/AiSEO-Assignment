"""
Tests for fanout_engine JSON parsing and validation logic.

All LLM calls are mocked — these tests validate the parsing, schema validation,
and retry logic without hitting a live API.
"""

from __future__ import annotations

import json
import pytest
import pytest_asyncio

from unittest.mock import AsyncMock, MagicMock, patch

from app.services.fanout_engine import (
    LLMUnavailableError,
    _parse_and_validate,
    call_llm_with_retry,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_JSON_RESPONSE = json.dumps({
    "sub_queries": [
        {"type": "comparative", "query": "Tool A vs Tool B for SEO"},
        {"type": "comparative", "query": "Tool A vs Tool C pricing comparison"},
        {"type": "feature_specific", "query": "AI writing tool with keyword clustering feature"},
        {"type": "feature_specific", "query": "AI content tool with real-time SERP analysis"},
        {"type": "use_case", "query": "AI writing tool for agency content production at scale"},
        {"type": "use_case", "query": "AI writing assistant for ecommerce product descriptions"},
        {"type": "trust_signals", "query": "AI SEO writing tool case studies 2025"},
        {"type": "trust_signals", "query": "AI content tool reviews G2 Capterra ratings"},
        {"type": "how_to", "query": "how to use AI to optimize blog content for SEO"},
        {"type": "how_to", "query": "how to set up AI writing workflow for content team"},
        {"type": "definitional", "query": "what is AI-assisted SEO content writing"},
        {"type": "definitional", "query": "definition of generative engine optimization GEO"},
    ]
})


def _make_mock_response(content: str) -> MagicMock:
    """Build a mock that mimics an OpenAI ChatCompletion response object."""
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    return response


# ---------------------------------------------------------------------------
# _parse_and_validate — unit tests (synchronous)
# ---------------------------------------------------------------------------

class TestParseAndValidate:

    def test_valid_response_parsed_correctly(self):
        result = _parse_and_validate(VALID_JSON_RESPONSE)
        assert len(result) == 12
        types = [sq.type for sq in result]
        assert types.count("comparative") >= 2
        assert types.count("definitional") >= 2

    def test_markdown_fences_are_stripped(self):
        wrapped = f"```json\n{VALID_JSON_RESPONSE}\n```"
        result = _parse_and_validate(wrapped)
        assert len(result) >= 10

    def test_plain_markdown_fence_stripped(self):
        wrapped = f"```\n{VALID_JSON_RESPONSE}\n```"
        result = _parse_and_validate(wrapped)
        assert len(result) >= 10

    def test_invalid_json_raises(self):
        with pytest.raises((ValueError, json.JSONDecodeError)):
            _parse_and_validate("this is definitely not JSON")

    def test_missing_sub_queries_key_raises(self):
        payload = json.dumps({"queries": []})
        with pytest.raises(ValueError, match="missing required 'sub_queries' key"):
            _parse_and_validate(payload)

    def test_insufficient_type_coverage_raises(self):
        """All sub-queries from one type only -> should fail coverage check."""
        payload = json.dumps({
            "sub_queries": [
                {"type": "comparative", "query": f"query {i}"} for i in range(12)
            ]
        })
        with pytest.raises(ValueError, match="Insufficient"):
            _parse_and_validate(payload)

    def test_too_few_sub_queries_raises(self):
        """Fewer than 10 sub-queries should be rejected."""
        minimal_types = ["comparative", "feature_specific", "use_case",
                         "trust_signals", "how_to", "definitional"]
        queries = [{"type": t, "query": f"q {i}"} for i, t in enumerate(minimal_types)]
        payload = json.dumps({"sub_queries": queries})
        with pytest.raises(ValueError):
            _parse_and_validate(payload)

    def test_too_many_sub_queries_raises(self):
        """More than 15 sub-queries should be rejected."""
        queries = [
            {"type": t, "query": f"query {i}"}
            for i, t in enumerate(
                (["comparative"] * 3 + ["feature_specific"] * 3
                 + ["use_case"] * 3 + ["trust_signals"] * 3
                 + ["how_to"] * 3 + ["definitional"] * 3)
            )
        ]
        payload = json.dumps({"sub_queries": queries})
        with pytest.raises(ValueError):
            _parse_and_validate(payload)

    def test_invalid_type_value_raises(self):
        """An unrecognised type value should fail Pydantic validation."""
        bad_type_queries = json.loads(VALID_JSON_RESPONSE)
        bad_type_queries["sub_queries"][0]["type"] = "feature-specific"  # wrong format
        with pytest.raises(ValueError):
            _parse_and_validate(json.dumps(bad_type_queries))


# ---------------------------------------------------------------------------
# call_llm_with_retry — async tests (mocked)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestCallLlmWithRetry:

    async def test_succeeds_on_first_attempt(self, monkeypatch):
        """Valid JSON on first call -> returns sub-queries without retrying."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        mock_response = _make_mock_response(VALID_JSON_RESPONSE)

        with patch("app.services.fanout_engine.AsyncOpenAI") as MockClient:
            instance = AsyncMock()
            MockClient.return_value = instance
            instance.chat.completions.create = AsyncMock(return_value=mock_response)

            sub_queries, model = await call_llm_with_retry("best AI SEO tool", max_retries=3)

        assert len(sub_queries) == 12
        assert model == "gpt-4o-mini"

    async def test_retries_on_invalid_json_then_succeeds(self, monkeypatch):
        """Invalid JSON on first two calls, valid on third -> succeeds."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        bad_response = _make_mock_response("not valid json at all")
        good_response = _make_mock_response(VALID_JSON_RESPONSE)

        call_count = 0

        async def side_effect(**kwargs):
            nonlocal call_count
            call_count += 1
            return bad_response if call_count < 3 else good_response

        with patch("app.services.fanout_engine.AsyncOpenAI") as MockClient:
            with patch("app.services.fanout_engine.asyncio.sleep", new_callable=AsyncMock):
                instance = AsyncMock()
                MockClient.return_value = instance
                instance.chat.completions.create = side_effect

                sub_queries, _ = await call_llm_with_retry("test query", max_retries=3)

        assert call_count == 3
        assert len(sub_queries) == 12

    async def test_all_retries_exhausted_raises_llm_error(self, monkeypatch):
        """All attempts return invalid JSON -> LLMUnavailableError raised."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        bad_response = _make_mock_response("invalid json !!!")

        with patch("app.services.fanout_engine.AsyncOpenAI") as MockClient:
            with patch("app.services.fanout_engine.asyncio.sleep", new_callable=AsyncMock):
                instance = AsyncMock()
                MockClient.return_value = instance
                instance.chat.completions.create = AsyncMock(return_value=bad_response)

                with pytest.raises(LLMUnavailableError) as exc_info:
                    await call_llm_with_retry("test query", max_retries=3)

        assert "JSONDecodeError" in exc_info.value.detail

    async def test_missing_api_key_raises_llm_error(self, monkeypatch):
        """Missing OPENAI_API_KEY env var -> LLMUnavailableError immediately."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(LLMUnavailableError, match="OPENAI_API_KEY"):
            await call_llm_with_retry("test query")
