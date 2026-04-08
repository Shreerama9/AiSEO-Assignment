from __future__ import annotations

import threading

import spacy

from app.models.schemas import CheckResult, DirectAnswerDetails
from app.services.aeo_checks.base import BaseCheck
from app.services.content_parser import extract_first_paragraph

HEDGE_PHRASES = [
    "it depends",
    "may vary",
    "in some cases",
    "this varies",
    "generally speaking",
]

_nlp_lock = threading.Lock()
_nlp_instance: spacy.language.Language | None = None


def _get_nlp() -> spacy.language.Language:
    # Returns the spaCy model with thread-safe lazy loading
    global _nlp_instance
    if _nlp_instance is not None:
        return _nlp_instance
    with _nlp_lock:
        if _nlp_instance is None:
            try:
                _nlp_instance = spacy.load("en_core_web_sm")
            except OSError as exc:
                raise RuntimeError("spaCy model 'en_core_web_sm' not found.") from exc
    return _nlp_instance


class DirectAnswerCheck(BaseCheck):
    # Tests whether the first paragraph is a concise, declarative answer without hedging
    check_id = "direct_answer"
    name = "Direct Answer Detection"
    max_score = 20

    def run(self, html: str) -> CheckResult:
        # Analyzes the first paragraph for length, structure, and hedging
        first_para = extract_first_paragraph(html)
        words = first_para.split()
        word_count = len(words)
        has_hedge = any(phrase in first_para.lower() for phrase in HEDGE_PHRASES)
        is_declarative = self._check_declarative(first_para)

        if word_count > 90:
            score = 0
        elif word_count > 60:
            score = 8
        elif has_hedge or not is_declarative:
            score = 12
        else:
            score = 20

        details = DirectAnswerDetails(
            word_count=word_count,
            is_declarative=is_declarative,
            has_hedge_phrase=has_hedge,
        )

        return self._build_result(score, details, self._build_recommendation(word_count, has_hedge, is_declarative))

    def _check_declarative(self, text: str) -> bool:
        # Returns True if the first sentence has a subject and a root verb
        if not text.strip():
            return False

        nlp = _get_nlp()
        doc = nlp(text)
        sentences = list(doc.sents)
        if not sentences:
            return False

        first_sent = sentences[0]
        has_subject = any(tok.dep_ in ("nsubj", "nsubjpass") for tok in first_sent)
        has_root_verb = any(
            tok.dep_ == "ROOT" and tok.pos_ in ("VERB", "AUX") for tok in first_sent
        )
        return has_subject and has_root_verb

    def _build_recommendation(self, word_count: int, has_hedge: bool, is_declarative: bool) -> str | None:
        # Combines paragraph quality issues into a reader-friendly recommendation string
        issues: list[str] = []
        if word_count > 90:
            issues.append(f"Paragraph length is {word_count} words — trim to under 60.")
        elif word_count > 60:
            issues.append(f"Paragraph length is {word_count} words — aim for ≤ 60.")
        if has_hedge:
            issues.append("Remove hedge phrases (e.g. 'it depends') for a more direct answer.")
        if not is_declarative:
            issues.append("Rewrite the opening as a clear declarative statement with a subject and verb.")
        return " ".join(issues) if issues else None
