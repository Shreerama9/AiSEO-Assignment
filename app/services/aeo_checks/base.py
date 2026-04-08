from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.models.schemas import CheckResult


class BaseCheck(ABC):
    # Abstract base class for all AEO content checks
    check_id: str
    name: str
    max_score: int

    @abstractmethod
    def run(self, html: str) -> CheckResult:
        # Executes the check logic against raw HTML/text
        ...

    def _build_result(self, score: int, details: Any, recommendation: str | None) -> CheckResult:
        # Constructs a standardized CheckResult payload
        return CheckResult(
            check_id=self.check_id,
            name=self.name,
            passed=(score == self.max_score),
            score=score,
            max_score=self.max_score,
            details=details,
            recommendation=recommendation,
        )
