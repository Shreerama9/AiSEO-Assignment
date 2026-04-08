from __future__ import annotations

import re
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from app.models.schemas import GapSummary, SubQuery


SIMILARITY_THRESHOLD = 0.72
_CHUNK_SENTENCES = 3
_MODEL_NAME = "all-MiniLM-L6-v2"
_SENT_RE = re.compile(r"(?<=[.!?])\s+")


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    # Returns the SentenceTransformer model with lazy loading
    return SentenceTransformer(_MODEL_NAME)


def analyze_gaps(
    sub_queries: list[SubQuery],
    existing_content: str,
) -> tuple[list[SubQuery], GapSummary]:
    # Annotates sub_queries with coverage scores and returns the aggregate gap summary
    model = _get_model()

    chunks = _chunk_text(existing_content, chunk_size=_CHUNK_SENTENCES)
    if not chunks:
        chunks = [existing_content[:500]]

    content_embeddings = model.encode(chunks, normalize_embeddings=True)
    query_embeddings = model.encode([sq.query for sq in sub_queries], normalize_embeddings=True)
    sim_matrix = cosine_similarity(query_embeddings, content_embeddings)

    enriched: list[SubQuery] = []
    for i, sq in enumerate(sub_queries):
        max_sim = float(np.max(sim_matrix[i]))
        enriched.append(SubQuery(
            type=sq.type,
            query=sq.query,
            covered=max_sim >= SIMILARITY_THRESHOLD,
            similarity_score=round(max_sim, 4),
        ))

    covered_queries = [sq for sq in enriched if sq.covered]
    covered_type_set = sorted({sq.type for sq in covered_queries})
    all_type_set = sorted({sq.type for sq in enriched})
    missing_type_set = sorted(set(all_type_set) - set(covered_type_set))

    gap_summary = GapSummary(
        covered=len(covered_queries),
        total=len(enriched),
        coverage_percent=round(len(covered_queries) / len(enriched) * 100) if enriched else 0,
        covered_types=covered_type_set,
        missing_types=missing_type_set,
    )

    return enriched, gap_summary


def _chunk_text(text: str, chunk_size: int = _CHUNK_SENTENCES) -> list[str]:
    # Splits text into non-overlapping windows of a fixed sentence count
    sentences = [s.strip() for s in _SENT_RE.split(text) if s.strip()]
    chunks = []
    for i in range(0, len(sentences), chunk_size):
        chunk = " ".join(sentences[i : i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks or [text]
