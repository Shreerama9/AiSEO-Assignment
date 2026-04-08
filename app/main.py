from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from app.api import aeo, fanout

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Manages startup (env loading, model warmup) and teardown
    load_dotenv(override=False)

    if not os.environ.get("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY not set. Fan-out will be disabled.")

    loop = asyncio.get_event_loop()

    try:
        from app.services.aeo_checks.direct_answer import _get_nlp
        await loop.run_in_executor(None, _get_nlp)
    except Exception as exc:
        logger.warning("spaCy mockup failed: %s", exc)

    try:
        from app.services.gap_analyzer import _get_model
        await loop.run_in_executor(None, _get_model)
    except Exception as exc:
        logger.warning("ST warmup failed: %s", exc)

    yield


app = FastAPI(
    title="AEGIS — AEO & GEO Content Intelligence Platform",
    description="AEO Content Scorer and Query Fan-Out Engine.",
    version="1.1.0",
    lifespan=lifespan,
)

app.include_router(aeo.router, prefix="/api/aeo", tags=["aeo"])
app.include_router(fanout.router, prefix="/api/fanout", tags=["fanout"])


@app.get("/", tags=["health"])
async def root():
    # Returns the root health message
    return {"status": "ok", "message": "AEGIS is running."}


@app.get("/health", tags=["health"])
async def health():
    # Returns the structured service readiness status
    fanout_ready = bool(os.environ.get("OPENAI_API_KEY"))
    return {
        "status": "ok",
        "version": "1.1.0",
        "ready": {
            "aeo_scorer": True,
            "fanout_engine": fanout_ready,
        }
    }
