"""
test_threshold.py
-----------------
Threshold auto-tuning harness for the embedding similarity threshold used in
gap_analyzer.py (currently 0.72).

This harness:
  1. Defines a small but representative labeled dataset of
     (query, content, expected_covered) triples.
  2. Computes cosine similarity between each query and the content chunks using
     the same model / chunk size used in production (all-MiniLM-L6-v2).
  3. Sweeps candidate thresholds from 0.50 → 0.90 in steps of 0.05.
  4. Reports precision, recall, and F1 at each threshold.
  5. Prints the optimal threshold (best F1) and asserts the current production
     threshold (0.72) is within 0.05 of optimal — the test fails if a
     significantly better threshold exists in the labeled data.

Usage:
  pytest tests/test_threshold.py -v -s

NOTE: This test requires sentence-transformers to be installed.
      It is skipped automatically if the package is unavailable.
"""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# Skip the entire module if sentence-transformers is not installed
# ---------------------------------------------------------------------------
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    _DEPS_AVAILABLE = True
except ImportError:
    _DEPS_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not _DEPS_AVAILABLE,
    reason="sentence-transformers / sklearn / numpy not installed",
)

# ---------------------------------------------------------------------------
# Labeled dataset
# Each entry: (query, content_snippet, expected_covered: bool)
#
# Rationale for coverage labels:
#   True  → the content directly addresses the query's intent
#   False → the query asks about something not in the content (a "gap")
# ---------------------------------------------------------------------------

LABELED_DATA: list[tuple[str, str, bool]] = [
    # --- COVERED: query closely matches content ---
    (
        "what is generative engine optimization",
        (
            "Generative Engine Optimization (GEO) is the practice of optimizing content "
            "so that it is cited and surfaced by AI-powered answer engines such as "
            "ChatGPT, Perplexity, and Google SGE."
        ),
        True,
    ),
    (
        "how to improve Flesch-Kincaid readability score",
        (
            "To improve your Flesch-Kincaid Grade Level, shorten sentences, use common "
            "words over technical jargon, and break long paragraphs into smaller digestible "
            "chunks. Aim for a grade level between 7 and 9 for broad audiences."
        ),
        True,
    ),
    (
        "best practices for AI content humanization",
        (
            "AI content humanization refers to techniques that make machine-generated text "
            "indistinguishable from human writing. Methods include varying sentence length, "
            "injecting personal anecdotes, and avoiding telltale AI phrases."
        ),
        True,
    ),
    (
        "difference between AEO and SEO",
        (
            "Answer Engine Optimization (AEO) focuses on structuring content so it is "
            "selected as a direct answer by voice assistants and AI engines, whereas "
            "traditional SEO prioritizes ranking position in a SERP."
        ),
        True,
    ),
    (
        "LoRA fine-tuning for domain-specific LLMs",
        (
            "Low-Rank Adaptation (LoRA) injects trainable rank-decomposition matrices into "
            "each transformer layer, dramatically reducing the number of parameters that "
            "need to be updated during domain-specific fine-tuning."
        ),
        True,
    ),
    (
        "cosine similarity threshold for semantic coverage",
        (
            "A cosine similarity threshold of 0.72 is used to determine whether a sub-query "
            "is covered by the existing content. Values above 0.85 indicate near-duplicate "
            "matches, while values below 0.60 typically represent unrelated topics."
        ),
        True,
    ),
    # --- NOT COVERED: query is about a topic absent from the content ---
    (
        "kubernetes GPU scheduling for ML workloads",
        (
            "GEO involves optimizing content structures such as headers, direct answers, "
            "and entity mentions to increase the likelihood of being cited by generative AI."
        ),
        False,
    ),
    (
        "multi-agent LLM orchestration frameworks",
        (
            "Readability scoring uses Flesch-Kincaid Grade Level to assess the complexity "
            "of prose. A grade level of 7-9 is ideal for web content targeting general audiences."
        ),
        False,
    ),
    (
        "vector database comparison Pinecone vs Weaviate",
        (
            "The H-tag hierarchy check verifies that headings follow a strict H1 → H2 → H3 "
            "nesting order with no skipped levels and no duplicate H1 tags."
        ),
        False,
    ),
    (
        "real-time SERP monitoring and alerting",
        (
            "Direct Answer Detection checks whether the opening paragraph is concise "
            "(under 60 words), declarative, and free of hedge phrases like 'it depends'."
        ),
        False,
    ),
    (
        "schema markup for knowledge graph integration",
        (
            "The Query Fan-Out Engine generates 10–15 sub-queries across six intent types: "
            "comparative, feature-specific, use-case, trust-signals, how-to, and definitional."
        ),
        False,
    ),
    (
        "model quantization INT8 distillation techniques",
        (
            "Content cached for one hour using a SHA-256 keyed TTLCache. Repeated requests "
            "for the same URL skip re-fetching and re-scoring entirely."
        ),
        False,
    ),
]

# ---------------------------------------------------------------------------
# Helpers (mirrors gap_analyzer._chunk_text / analyze_gaps logic)
# ---------------------------------------------------------------------------

import re as _re

_SENT_RE = _re.compile(r"(?<=[.!?])\s+")
_CHUNK_SENTENCES = 3
_MODEL_NAME = "all-MiniLM-L6-v2"
_PRODUCTION_THRESHOLD = 0.72
_TOLERANCE = 0.05


def _chunk_text(text: str, chunk_size: int = _CHUNK_SENTENCES) -> list[str]:
    sentences = [s.strip() for s in _SENT_RE.split(text) if s.strip()]
    chunks = []
    for i in range(0, len(sentences), chunk_size):
        chunk = " ".join(sentences[i : i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks or [text]


def _max_similarity(model: SentenceTransformer, query: str, content: str) -> float:
    chunks = _chunk_text(content)
    content_emb = model.encode(chunks, normalize_embeddings=True)
    query_emb = model.encode([query], normalize_embeddings=True)
    sim_matrix = cosine_similarity(query_emb, content_emb)
    return float(np.max(sim_matrix))


def _precision_recall_f1(
    sims: list[float], labels: list[bool], threshold: float
) -> tuple[float, float, float]:
    preds = [s >= threshold for s in sims]
    tp = sum(p and l for p, l in zip(preds, labels))
    fp = sum(p and not l for p, l in zip(preds, labels))
    fn = sum(not p and l for p, l in zip(preds, labels))
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    return precision, recall, f1


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestThresholdHarness:
    """Sweep thresholds and verify production value is near-optimal."""

    @pytest.fixture(scope="class")
    def model(self):
        return SentenceTransformer(_MODEL_NAME)

    @pytest.fixture(scope="class")
    def similarity_data(self, model):
        sims = [
            _max_similarity(model, query, content)
            for query, content, _ in LABELED_DATA
        ]
        labels = [label for _, _, label in LABELED_DATA]
        return sims, labels

    def test_dataset_has_both_classes(self):
        labels = [label for _, _, label in LABELED_DATA]
        assert any(labels), "Dataset must have at least one True (covered) label"
        assert not all(labels), "Dataset must have at least one False (not covered) label"

    def test_threshold_sweep_and_production_near_optimal(self, similarity_data):
        sims, labels = similarity_data
        thresholds = [round(t, 2) for t in list(
            iter([0.50 + i * 0.05 for i in range(9)])  # 0.50 → 0.90
        )]

        results: list[tuple[float, float, float, float]] = []
        print("\n\nThreshold Sweep Report")
        print(f"{'Threshold':>10} {'Precision':>10} {'Recall':>10} {'F1':>10}")
        print("-" * 45)

        for t in thresholds:
            p, r, f1 = _precision_recall_f1(sims, labels, t)
            results.append((t, p, r, f1))
            print(f"{t:>10.2f} {p:>10.3f} {r:>10.3f} {f1:>10.3f}")

        best_threshold, best_p, best_r, best_f1 = max(results, key=lambda x: x[3])
        prod_p, prod_r, prod_f1 = _precision_recall_f1(sims, labels, _PRODUCTION_THRESHOLD)

        print(f"\nOptimal threshold: {best_threshold:.2f}  (F1={best_f1:.3f})")
        print(
            f"Production threshold: {_PRODUCTION_THRESHOLD:.2f}  "
            f"(F1={prod_f1:.3f})"
        )

        assert prod_f1 > 0, (
            f"Production threshold {_PRODUCTION_THRESHOLD} has F1=0 on labeled data. "
            "Review threshold or labeled data quality."
        )
        assert abs(best_threshold - _PRODUCTION_THRESHOLD) <= _TOLERANCE, (
            f"Optimal threshold ({best_threshold:.2f}, F1={best_f1:.3f}) is more than "
            f"{_TOLERANCE} away from production threshold ({_PRODUCTION_THRESHOLD}). "
            f"Consider updating SIMILARITY_THRESHOLD in gap_analyzer.py."
        )

    def test_all_covered_queries_score_above_minimum(self, similarity_data):
        """Sanity check: every 'covered' example should have sim > 0.50."""
        sims, labels = similarity_data
        for (query, content, label), sim in zip(LABELED_DATA, sims):
            if label:
                assert sim > 0.50, (
                    f"Covered query has unexpectedly low similarity ({sim:.3f}):\n"
                    f"  Query: {query}\n  Content: {content[:80]}..."
                )

    def test_all_gap_queries_score_below_maximum(self, similarity_data):
        """Sanity check: every 'not covered' example should have sim < 0.95."""
        sims, labels = similarity_data
        for (query, content, label), sim in zip(LABELED_DATA, sims):
            if not label:
                assert sim < 0.95, (
                    f"Not-covered query has suspiciously high similarity ({sim:.3f}):\n"
                    f"  Query: {query}\n  Content: {content[:80]}..."
                )
