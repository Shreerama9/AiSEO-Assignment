"""
Tests for HTagHierarchyCheck (Check B).
"""

import pytest
from app.services.aeo_checks.htag_hierarchy import HTagHierarchyCheck

check = HTagHierarchyCheck()


class TestHTagHierarchyCheck:

    def test_passing_case_valid_hierarchy(self):
        """A perfect H1 → H2 → H3 structure should score 20."""
        html = (
            "<h1>Title</h1>"
            "<h2>Section One</h2>"
            "<h3>Subsection</h3>"
            "<h2>Section Two</h2>"
            "<h3>Another Sub</h3>"
        )
        result = check.run(html)
        assert result.score == 20
        assert result.passed is True
        assert result.details.violations == []
        assert result.details.h_tags_found == ["h1", "h2", "h3", "h2", "h3"]
        assert result.recommendation is None

    def test_failing_case_no_h1(self):
        """Missing H1 should immediately score 0."""
        html = "<h2>Section</h2><h3>Sub</h3>"
        result = check.run(html)
        assert result.score == 0
        assert result.passed is False
        assert any("No <h1>" in v for v in result.details.violations)

    def test_failing_case_multiple_h1(self):
        """Two H1 tags is one violation -> 12 pts."""
        html = "<h1>First Title</h1><h1>Second Title</h1><h2>Section</h2>"
        result = check.run(html)
        assert result.score == 12
        assert any("Multiple <h1>" in v for v in result.details.violations)

    def test_failing_case_level_skip_h1_to_h3(self):
        """Jumping from H1 directly to H3 (skipping H2) is one violation -> 12 pts."""
        html = "<h1>Title</h1><h3>Skipped H2</h3>"
        result = check.run(html)
        assert result.score == 12
        assert any("Level skip" in v for v in result.details.violations)

    def test_failing_case_tag_before_h1(self):
        """An H2 appearing before the H1 is one violation -> 12 pts."""
        html = "<h2>Before Title</h2><h1>Title</h1><h2>Section</h2>"
        result = check.run(html)
        assert result.score == 12
        assert any("before the <h1>" in v for v in result.details.violations)

    def test_three_violations_scores_zero(self):
        """Three or more violations should score 0."""
        html = (
            "<h1>Title</h1>"
            "<h1>Title 2</h1>"
            "<h3>Skipped H2</h3>"
            "<h5>Skipped H4</h5>"
        )
        result = check.run(html)
        assert result.score == 0
        assert len(result.details.violations) >= 3

    def test_h_tags_found_order_preserved(self):
        """h_tags_found should be in DOM order."""
        html = "<h1>A</h1><h2>B</h2><h2>C</h2><h3>D</h3>"
        result = check.run(html)
        assert result.details.h_tags_found == ["h1", "h2", "h2", "h3"]

    def test_no_headings_at_all(self):
        """Content with zero heading tags is treated as missing H1 -> score 0."""
        html = "<p>This page has no headings at all.</p>"
        result = check.run(html)
        assert result.score == 0
