from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import aeo, cache, fanout
from app.limiter import limiter

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Manages startup (env loading, model warmup) and teardown
    load_dotenv(override=False)

    if not os.environ.get("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY not set. Fan-out will be disabled.")

    loop = asyncio.get_event_loop()

    # Warm up spaCy
    try:
        from app.services.aeo_checks.direct_answer import _get_nlp
        await loop.run_in_executor(None, _get_nlp)
        logger.info("spaCy model ready.")
    except Exception as exc:
        logger.warning("spaCy warmup failed: %s", exc)

    # Warm up sentence-transformers unconditionally
    try:
        from app.services.gap_analyzer import _get_model
        await loop.run_in_executor(None, _get_model)
        logger.info("Sentence-transformer model ready.")
    except Exception as exc:
        logger.warning("Sentence-transformer warmup failed: %s", exc)

    yield


app = FastAPI(
    title="AEGIS — AEO & GEO Content Intelligence Platform",
    description="AEO Content Scorer and Query Fan-Out Engine.",
    version="1.2.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(aeo.router, prefix="/api/aeo", tags=["aeo"])
app.include_router(fanout.router, prefix="/api/fanout", tags=["fanout"])
app.include_router(cache.router, prefix="/api/cache", tags=["cache"])


@app.get("/", tags=["health"])
async def root():
    return {"status": "ok", "message": "AEGIS is running."}


@app.get("/health", tags=["health"])
async def health():
    fanout_ready = bool(os.environ.get("OPENAI_API_KEY"))
    return {
        "status": "ok",
        "version": "1.2.0",
        "ready": {
            "aeo_scorer": True,
            "fanout_engine": fanout_ready,
        },
    }
