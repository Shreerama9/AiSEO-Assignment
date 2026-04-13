from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.content_parser import bust_all_cache, bust_cache

router = APIRouter()


class CacheBustRequest(BaseModel):
    url: str | None = None  # omit to clear entire cache


@router.delete(
    "",
    summary="Bust URL cache",
    description=(
        "Pass `{\"url\": \"https://...\"}` to evict a single URL, "
        "or send an empty body to clear the entire cache."
    ),
)
async def delete_cache(body: CacheBustRequest | None = None) -> dict:
    if body and body.url:
        removed = bust_cache(body.url)
        return {"cleared": removed, "url": body.url}
    count = bust_all_cache()
    return {"cleared": count, "url": None}
