from __future__ import annotations

import re

import textstat

from app.models.schemas import CheckResult, ReadabilityDetails
from app.services.aeo_checks.base import BaseCheck
from app.services.content_parser import strip_boilerplate


_SENT_RE = re.compile(r"(?<=[.!?])\s+")


class ReadabilityCheck(BaseCheck):
    # Scores content readability using Flesch-Kincaid Grade Level targets
    check_id = "readability"
    name = "Snippet Readability"
    max_score = 20

    def run(self, html: str) -> CheckResult:
        # Measures FK grade and returns score with complex sentence details
        clean_text = strip_boilerplate(html)

        if not clean_text.strip():
            clean_text = re.sub(r"<[^>]+>", " ", html)
            clean_text = re.sub(r"\s{2,}", " ", clean_text).strip()

        fk_grade = textstat.flesch_kincaid_grade(clean_text)
        details = ReadabilityDetails(
            fk_grade_level=round(fk_grade, 1),
            complex_sentences=self._find_complex_sentences(clean_text),
        )
        score = self._score_fk(fk_grade)
        return self._build_result(score, details, self._build_recommendation(fk_grade, score))

    @staticmethod
    def _score_fk(grade: float) -> int:
        # Maps FK grade ranges to scoring bands
        if 7 <= grade <= 9:
            return 20
        if 6 <= grade < 7 or 9 < grade <= 10:
            return 14
        if 5 <= grade < 6 or 10 < grade <= 11:
            return 8
        return 0

    @staticmethod
    def _find_complex_sentences(text: str, top_n: int = 3) -> list[str]:
        # Returns the most complex sentences based on syllable density
        sentences = [s.strip() for s in _SENT_RE.split(text) if len(s.split()) >= 5]

        def _complexity(s: str) -> float:
            words = s.split()
            return sum(textstat.syllable_count(w) for w in words) / len(words) if words else 0.0

        return sorted(sentences, key=_complexity, reverse=True)[:top_n]

    @staticmethod
    def _build_recommendation(grade: float, score: int) -> str | None:
        # Generates readability advice based on target grade 7-9
        if score == 20:
            return None
        if grade < 7:
            return f"Content reads at Grade {grade:.1f} — slightly too simple. Add more precise terminology to reach Grade 7–9."
        return f"Content reads at Grade {grade:.1f}. Shorten sentences and replace jargon to reach Grade 7–9."
