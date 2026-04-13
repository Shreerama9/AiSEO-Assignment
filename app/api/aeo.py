from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, Request

from app.limiter import limiter
from app.models.schemas import AEORequest, AEOResponse
from app.services.aeo_checks.direct_answer import DirectAnswerCheck
from app.services.aeo_checks.htag_hierarchy import HTagHierarchyCheck
from app.services.aeo_checks.readability import ReadabilityCheck
from app.services.content_parser import get_content

router = APIRouter()

_CHECKS = [DirectAnswerCheck(), HTagHierarchyCheck(), ReadabilityCheck()]

_SCORE_BANDS = [
    (85, "AEO Optimized"),
    (65, "Needs Improvement"),
    (40, "Significant Gaps"),
    (0,  "Not AEO Ready"),
]


@router.post("/analyze", response_model=AEOResponse)
@limiter.limit("30/minute")
async def analyze(request: Request, body: AEORequest) -> AEOResponse:
    # Analyzes content via a set of AEO checks and returns a raw score and band
    try:
        html = await get_content(body.input_type, body.input_value)
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "url_fetch_failed",
                "message": str(exc),
            },
        )

    results = await asyncio.gather(
        *[asyncio.to_thread(check.run, html) for check in _CHECKS]
    )

    raw_score = sum(r.score for r in results)
    aeo_score = round((raw_score / 60) * 100)
    band = next(label for threshold, label in _SCORE_BANDS if aeo_score >= threshold)

    return AEOResponse(aeo_score=aeo_score, band=band, checks=list(results))
