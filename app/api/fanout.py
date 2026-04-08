from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.schemas import FanoutRequest, FanoutResponse
from app.services.fanout_engine import LLMUnavailableError, call_llm_with_retry
from app.services.gap_analyzer import analyze_gaps

router = APIRouter()


@router.post("/generate", response_model=FanoutResponse)
async def generate(request: FanoutRequest) -> FanoutResponse:
    # Generates a full JSON response of sub-queries with coverage analysis
    try:
        sub_queries, model_used = await call_llm_with_retry(request.target_query)
    except LLMUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "llm_unavailable",
                "message": str(exc),
                "detail": exc.detail,
            },
        )

    gap_summary = None
    if request.existing_content:
        sub_queries, gap_summary = await asyncio.to_thread(
            analyze_gaps, sub_queries, request.existing_content
        )

    return FanoutResponse(
        target_query=request.target_query,
        model_used=model_used,
        total_sub_queries=len(sub_queries),
        sub_queries=sub_queries,
        gap_summary=gap_summary,
    )


@router.post("/stream")
async def stream(request: FanoutRequest) -> StreamingResponse:
    # Streams sub-queries as Server-Sent Events to reduce time-to-first-byte
    async def _generate():
        try:
            sub_queries, model_used = await call_llm_with_retry(request.target_query)
        except LLMUnavailableError as exc:
            yield f"data: {json.dumps({'error': 'llm_unavailable', 'detail': exc.detail})}\n\n"
            return

        gap_summary = None
        if request.existing_content:
            sub_queries, gap_summary = await asyncio.to_thread(
                analyze_gaps, sub_queries, request.existing_content
            )

        yield f"data: {json.dumps({'target_query': request.target_query, 'model_used': model_used})}\n\n"

        for sq in sub_queries:
            yield f"data: {json.dumps(sq.model_dump())}\n\n"
            await asyncio.sleep(0)

        if gap_summary:
            yield f"data: {json.dumps({'gap_summary': gap_summary.model_dump()})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
