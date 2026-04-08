from __future__ import annotations

import asyncio
import json
import os
import re

import pydantic
from openai import AsyncOpenAI

from app.models.schemas import SubQuery, SubQueryType

REQUIRED_TYPES = [t.value for t in SubQueryType]
MIN_PER_TYPE = 2
_MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """\
You are a search intent analyst. Decompose a target query into sub-queries that cover multiple user intents. \
Return ONLY a valid JSON object with a "sub_queries" array. \
Each object needs "type" (one of: comparative, feature_specific, use_case, trust_signals, how_to, definitional) and "query". \
Provide between 10 and 15 sub-queries with at least 2 per type."""

_USER_TEMPLATE = 'Generate 10–15 sub-queries for the target query: "{target_query}"'


class LLMUnavailableError(Exception):
    # Exception raised when the LLM consistently returns malformed output or fails after retries
    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


async def call_llm_with_retry(target_query: str, max_retries: int = 3) -> tuple[list[SubQuery], str]:
    # Calls the LLM and retries on failure with exponential backoff
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise LLMUnavailableError("OPENAI_API_KEY not set.")

    client = AsyncOpenAI(api_key=api_key)
    last_error: str = "Unknown error"

    for attempt in range(max_retries):
        if attempt > 0:
            await asyncio.sleep(2 ** attempt)

        try:
            response = await client.chat.completions.create(
                model=_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": _USER_TEMPLATE.format(target_query=target_query)},
                ],
                temperature=0.7,
                max_tokens=1800,
                response_format={"type": "json_object"},
            )
            raw_text = response.choices[0].message.content or ""
            sub_queries = _parse_and_validate(raw_text)
            return sub_queries, _MODEL

        except (json.JSONDecodeError, ValueError, pydantic.ValidationError) as exc:
            last_error = f"Parsing error on attempt {attempt + 1}: {exc}"
        except Exception as exc:
            last_error = f"API error on attempt {attempt + 1}: {exc}"

    raise LLMUnavailableError(last_error)


def _parse_and_validate(raw_text: str) -> list[SubQuery]:
    # Validates LLM output against the sub-query schema and coverage constraints
    text = raw_text.strip()
    text = re.sub(r"^```[a-z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text).strip()

    data = json.loads(text)
    if "sub_queries" not in data:
        raise ValueError("Missing 'sub_queries' key.")

    raw_queries = data["sub_queries"]
    if not isinstance(raw_queries, list):
        raise ValueError("'sub_queries' must be an array.")

    try:
        validated = [SubQuery(**item) for item in raw_queries]
    except pydantic.ValidationError as exc:
        raise ValueError(f"Schema validation failed: {exc}") from exc

    if not (10 <= len(validated) <= 15):
        raise ValueError(f"Expected 10-15 sub-queries, got {len(validated)}")

    type_counts = {t: 0 for t in REQUIRED_TYPES}
    for sq in validated:
        sq_type = sq.type if isinstance(sq.type, str) else sq.type.value
        type_counts[sq_type] = type_counts.get(sq_type, 0) + 1

    insufficient = [t for t, count in type_counts.items() if count < MIN_PER_TYPE]
    if insufficient:
        raise ValueError(f"Need at least {MIN_PER_TYPE} per type.")

    return validated
