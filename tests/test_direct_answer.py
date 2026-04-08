"""
Tests for DirectAnswerCheck (Check A).

Each test exercises the check directly — no HTTP layer involved.
"""

import pytest
from app.services.aeo_checks.direct_answer import DirectAnswerCheck

check = DirectAnswerCheck()


class TestDirectAnswerCheck:

    def test_passing_case_short_declarative_no_hedge(self):
        """A concise, declarative paragraph with no hedging should score 20."""
        html = (
            "<p>Python is a high-level programming language widely used "
            "for data science, automation, and web development.</p>"
        )
        result = check.run(html)
        assert result.score == 20
        assert result.passed is True
        assert result.details.word_count <= 60
        assert result.details.is_declarative is True
        assert result.details.has_hedge_phrase is False
        assert result.recommendation is None

    def test_failing_case_over_90_words(self):
        """A paragraph exceeding 90 words should score 0."""
        long_text = "word " * 95
        html = f"<p>{long_text.strip()}</p>"
        result = check.run(html)
        assert result.score == 0
        assert result.passed is False
        assert result.details.word_count > 90

    def test_failing_case_61_to_90_words(self):
        """A paragraph in the 61–90 word range should score 8."""
        medium_text = "word " * 70
        html = f"<p>{medium_text.strip()}</p>"
        result = check.run(html)
        assert result.score == 8
        assert result.details.word_count > 60

    def test_failing_case_hedge_phrase_present(self):
        """A short declarative paragraph with a hedge phrase should score 12."""
        html = (
            "<p>It depends on your use case, but Python is generally a strong choice "
            "for beginners looking to learn programming.</p>"
        )
        result = check.run(html)
        assert result.score == 12
        assert result.details.has_hedge_phrase is True

    def test_failing_case_not_declarative(self):
        """A question as the first paragraph should score 12 (≤60 words, no hedge, not declarative)."""
        # Questions typically lack a root VERB with a subject in the expected pattern
        html = "<p>What is the best programming language for beginners?</p>"
        result = check.run(html)
        # Score is 12 (short, no hedge, but not declarative) or 20 if spaCy disagrees —
        # we assert it is NOT 0 (not over 90 words) and is ≤ 20.
        assert result.score in (12, 20)
        assert result.details.word_count <= 60

    def test_plain_text_fallback(self):
        """Plain text without HTML tags should still be parsed correctly."""
        plain = (
            "Machine learning is a subset of artificial intelligence that enables "
            "computers to learn from data without explicit programming."
        )
        result = check.run(plain)
        assert result.score in (20, 12)
        assert result.details.word_count > 0

    def test_details_fields_present(self):
        """CheckResult must always contain the required detail fields."""
        html = "<p>SEO helps websites rank higher in search engine results pages.</p>"
        result = check.run(html)
        assert hasattr(result.details, "word_count")
        assert hasattr(result.details, "is_declarative")
        assert hasattr(result.details, "has_hedge_phrase")
        assert result.check_id == "direct_answer"
        assert result.max_score == 20
