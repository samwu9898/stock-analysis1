# -*- coding: utf-8 -*-
"""Safe analysis context schemas for downstream analyzer/scorer."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


DimensionPermission = Literal["allowed", "allowed_with_low_confidence", "restricted", "blocked"]
Confidence = Literal["high", "medium", "low"]
RiskSeverity = Literal["low", "medium", "high"]
InstructionType = Literal["must_do", "must_not_do", "caution", "data_gap", "confidence_limit"]
ContextQuality = Literal["strong", "usable", "weak", "insufficient"]

PROHIBITED_CONTEXT_TERMS = (
    "买入",
    "卖出",
    "加仓",
    "减仓",
    "清仓",
    "止损",
    "止盈",
    "目标价",
    "满仓",
    "梭哈",
    "supportive",
    "neutral",
    "negative",
    "fundamental_score",
)


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AnalysisDimensionPermission(StrictBaseModel):
    dimension_name: str
    permission: DimensionPermission
    reason: str
    related_missing_fields: list[str] = Field(default_factory=list)
    max_confidence: Confidence


class RequiredRisk(StrictBaseModel):
    risk_name: str
    severity: RiskSeverity
    reason: str
    evidence_source: str
    must_include: bool = True


class ProhibitedClaim(StrictBaseModel):
    claim_type: str
    prohibited_reason: str
    related_missing_fields: list[str] = Field(default_factory=list)
    example_forbidden_phrases: list[str] = Field(default_factory=list)


class ScoringConstraint(StrictBaseModel):
    scoring_dimension: str
    max_score: int = Field(ge=0, le=100)
    reason: str
    related_missing_fields: list[str] = Field(default_factory=list)


class AnalyzerInstruction(StrictBaseModel):
    instruction_type: InstructionType
    instruction: str
    reason: str


class AnalysisContext(StrictBaseModel):
    schema_version: str = "analysis_context.v1"
    stock_code: str
    stock_name: str | None = None
    strategy_type: str
    classification_confidence: str
    readiness_score: int = Field(ge=0, le=100)
    readiness_level: str
    framework_name: str
    generated_at: str
    overall_context_quality: ContextQuality
    max_overall_confidence: Confidence
    allowed_dimensions: list[AnalysisDimensionPermission] = Field(default_factory=list)
    restricted_dimensions: list[AnalysisDimensionPermission] = Field(default_factory=list)
    blocked_dimensions: list[AnalysisDimensionPermission] = Field(default_factory=list)
    required_risks: list[RequiredRisk] = Field(default_factory=list)
    prohibited_claims: list[ProhibitedClaim] = Field(default_factory=list)
    scoring_constraints: list[ScoringConstraint] = Field(default_factory=list)
    analyzer_instructions: list[AnalyzerInstruction] = Field(default_factory=list)
    data_gaps_summary: list[str] = Field(default_factory=list)
    safe_summary_for_next_stage: str
    context_warnings: list[str] = Field(default_factory=list)

    @field_validator("schema_version")
    @classmethod
    def schema_version_must_match(cls, value: str) -> str:
        if value != "analysis_context.v1":
            raise ValueError("schema_version must be analysis_context.v1")
        return value

    @model_validator(mode="after")
    def enforce_confidence_caps_and_safe_terms(self) -> "AnalysisContext":
        order = {"low": 0, "medium": 1, "high": 2}
        max_allowed = "high"
        if self.readiness_level == "insufficient":
            if self.overall_context_quality != "insufficient":
                raise ValueError("insufficient readiness requires insufficient context quality")
            max_allowed = "low"
        elif self.readiness_level == "weak":
            max_allowed = "low"
        elif self.readiness_level == "usable_with_warnings":
            max_allowed = "medium"
        if self.strategy_type == "unknown":
            max_allowed = "low"
        if self.classification_confidence == "low":
            max_allowed = "low"
        elif self.classification_confidence == "medium" and order[max_allowed] > order["medium"]:
            max_allowed = "medium"
        if order[self.max_overall_confidence] > order[max_allowed]:
            raise ValueError("max_overall_confidence exceeds readiness/classification cap")

        dumped = self.model_dump_json()
        found = [term for term in PROHIBITED_CONTEXT_TERMS if term in dumped]
        if found:
            raise ValueError("AnalysisContext contains prohibited terms: " + ", ".join(found))
        return self
