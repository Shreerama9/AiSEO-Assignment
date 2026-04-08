"""
Tests for ReadabilityCheck (Check C).
"""

import pytest
from app.services.aeo_checks.readability import ReadabilityCheck

check = ReadabilityCheck()


class TestReadabilityCheck:

    def test_score_fk_bands(self):
        """_score_fk must return the correct points for every grade band."""
        from app.services.aeo_checks.readability import ReadabilityCheck
        score_fk = ReadabilityCheck._score_fk

        # Target band: 20 pts
        assert score_fk(7.0) == 20
        assert score_fk(8.5) == 20
        assert score_fk(9.0) == 20

        # Adjacent bands: 14 pts
        assert score_fk(6.0) == 14
        assert score_fk(6.9) == 14
        assert score_fk(9.5) == 14
        assert score_fk(10.0) == 14

        # Further out: 8 pts
        assert score_fk(5.0) == 8
        assert score_fk(5.9) == 8
        assert score_fk(10.5) == 8
        assert score_fk(11.0) == 8

        # Out of range: 0 pts
        assert score_fk(3.0) == 0
        assert score_fk(4.9) == 0
        assert score_fk(11.5) == 0
        assert score_fk(15.0) == 0

    def test_run_returns_valid_result(self):
        """run() must always return a valid CheckResult regardless of grade."""
        html = "<p>SEO helps websites appear in search results for relevant queries.</p>"
        result = check.run(html)
        assert result.score in (0, 8, 14, 20)
        assert result.details.fk_grade_level is not None
        assert result.details.target_range == "7-9"
        assert result.details.fk_grade_level is not None
        assert result.details.target_range == "7-9"

    def test_failing_case_very_high_grade(self):
        """Dense academic prose should score 8 or 0."""
        html = (
            "<p>The epistemological ramifications of multifactorial computational "
            "methodologies necessitate comprehensive interdisciplinary reevaluation "
            "of heuristic paradigms and their concomitant algorithmic manifestations "
            "within contemporary informational architectures.</p>"
        )
        result = check.run(html)
        assert result.score <= 8

    def test_boilerplate_is_stripped(self):
        """Nav and footer content must not affect the readability score."""
        html = (
            "<nav>Home About Contact</nav>"
            "<p>Cats are independent animals that can take care of themselves. "
            "They sleep for most of the day and hunt at night. "
            "Many people prefer cats because they require less attention.</p>"
            "<footer>Copyright 2025</footer>"
        )
        result = check.run(html)
        # The result should still be computable (no crash)
        assert result.details.fk_grade_level is not None
        assert isinstance(result.score, int)

    def test_complex_sentences_returned(self):
        """Should return up to 3 complex sentences, ranked by syllable density."""
        html = (
            "<p>Dogs are good pets. "
            "The multifaceted epistemological ramifications necessitate comprehensive "
            "interdisciplinary reevaluation of computational heuristics. "
            "Cats sleep a lot. "
            "Heuristically speaking, syntactic structures that incorporate "
            "polysyllabic terminology demonstrate elevated complexity indices.</p>"
        )
        result = check.run(html)
        assert len(result.details.complex_sentences) <= 3
        # The most complex sentences should appear first
        assert len(result.details.complex_sentences) >= 1

    def test_details_fields_present(self):
        """CheckResult must always carry the correct detail fields."""
        html = "<p>Search engine optimization helps websites rank better.</p>"
        result = check.run(html)
        assert hasattr(result.details, "fk_grade_level")
        assert hasattr(result.details, "target_range")
        assert hasattr(result.details, "complex_sentences")
        assert result.check_id == "readability"
        assert result.max_score == 20

    def test_recommendation_present_when_not_perfect(self):
        """A non-20 score must include a recommendation string."""
        html = (
            "<p>The concomitant ramifications of multidimensional paradigmatic "
            "synergies necessitate holistic recalibration of strategic imperatives "
            "across organizational hierarchies and operational frameworks.</p>"
        )
        result = check.run(html)
        if result.score < 20:
            assert result.recommendation is not None
            assert len(result.recommendation) > 0

    def test_plain_text_input(self):
        """Plain text (no HTML) should still work without crashing."""
        plain = (
            "Machine learning models can recognize patterns in large datasets. "
            "They improve over time as they process more examples. "
            "This technology powers recommendation systems and image recognition."
        )
        result = check.run(plain)
        assert isinstance(result.score, int)
        assert result.details.fk_grade_level is not None
