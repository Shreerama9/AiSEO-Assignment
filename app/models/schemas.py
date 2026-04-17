from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AEORequest(BaseModel):
    # Request schema for AEO analysis
    input_type: Literal["url", "text"]
    input_value: str = Field(..., min_length=1, max_length=50_000)

    @field_validator("input_value")
    @classmethod
    def strip_input(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("input_value must not be blank")
        return stripped


class DirectAnswerDetails(BaseModel):
    # Detailed metrics for the direct answer check
    word_count: int
    threshold: int = 60
    is_declarative: bool
    has_hedge_phrase: bool


class HTagHierarchyDetails(BaseModel):
    # Violations found in the heading structure
    violations: list[str]
    h_tags_found: list[str]


class ReadabilityDetails(BaseModel):
    # Flesch-Kincaid metrics and complex sentences
    fk_grade_level: float
    target_range: str = "7-9"
    complex_sentences: list[str]


class CheckResult(BaseModel):
    # Individual check result with score and recommendation
    check_id: str
    name: str
    passed: bool
    score: int
    max_score: int
    details: Union[DirectAnswerDetails, HTagHierarchyDetails, ReadabilityDetails, dict[str, Any]]
    recommendation: str | None = None


class AEOResponse(BaseModel):
    # Overall AEO score and band
    aeo_score: float
    band: str
    checks: list[CheckResult]


class SubQueryType(str, Enum):
    # Types of user intent for fan-out queries
    comparative = "comparative"
    feature_specific = "feature_specific"
    use_case = "use_case"
    trust_signals = "trust_signals"
    how_to = "how_to"
    definitional = "definitional"


class FanoutRequest(BaseModel):
    # Request schema for query fan-out
    target_query: str = Field(..., min_length=1, max_length=500)
    existing_content: str | None = Field(default=None, max_length=200_000)

    @field_validator("target_query")
    @classmethod
    def strip_query(cls, v: str) -> str:
        return v.strip()


class SubQuery(BaseModel):
    # A single generated sub-query with coverage data
    model_config = ConfigDict(use_enum_values=True)

    type: SubQueryType
    query: str
    covered: bool | None = None
    similarity_score: float | None = None


class GapSummary(BaseModel):
    # Aggregate coverage metrics for fan-out queries
    covered: int
    total: int
    coverage_percent: int
    covered_types: list[str]
    missing_types: list[str]


class FanoutResponse(BaseModel):
    # The complete fan-out engine response
    target_query: str
    model_used: str
    total_sub_queries: int
    sub_queries: list[SubQuery]
    gap_summary: GapSummary | None = None


class ErrorResponse(BaseModel):
    # Standard error payload
    error: str
    message: str
    detail: str | None = None
