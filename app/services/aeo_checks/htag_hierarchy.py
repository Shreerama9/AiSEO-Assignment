from __future__ import annotations

from bs4 import BeautifulSoup

from app.models.schemas import CheckResult, HTagHierarchyDetails
from app.services.aeo_checks.base import BaseCheck


class HTagHierarchyCheck(BaseCheck):
    # Validates heading structure: exactly one H1, no skips, no headings before H1
    check_id = "htag_hierarchy"
    name = "H-tag Hierarchy"
    max_score = 20

    def run(self, html: str) -> CheckResult:
        # Analyzes HTML headings to find hierarchy violations
        soup = BeautifulSoup(html, "html.parser")
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        h_tags_found = [tag.name for tag in headings]

        violations: list[str] = []

        h1_count = h_tags_found.count("h1")
        if h1_count == 0:
            violations.append("No <h1> tag found")
        elif h1_count > 1:
            violations.append(f"Multiple <h1> tags found ({h1_count})")

        if h1_count >= 1:
            h1_index = h_tags_found.index("h1")
            if h1_index > 0:
                violations.append(f"<{h_tags_found[0]}> appears before the <h1>")

        levels = [int(t[1]) for t in h_tags_found]
        for i in range(1, len(levels)):
            if levels[i] - levels[i - 1] > 1:
                violations.append(f"Level skip: <h{levels[i-1]}> → <h{levels[i]}>")

        score = 0 if (h1_count == 0 or len(violations) >= 3) else (20 if not violations else 12)
        details = HTagHierarchyDetails(violations=violations, h_tags_found=h_tags_found)

        return self._build_result(score, details, self._build_recommendation(violations))

    def _build_recommendation(self, violations: list[str]) -> str | None:
        # Returns a formatted recommendation string based on violations
        if not violations:
            return None
        return "Fix heading structure: " + "; ".join(violations) + "."
