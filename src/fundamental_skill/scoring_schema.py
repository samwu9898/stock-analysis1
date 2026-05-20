# -*- coding: utf-8 -*-
"""Rule-based fundamental scoring schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ScoreDimension = Literal[
    "business_quality",
    "financial_quality",
    "industry_cycle",
    "valuation_reasonableness",
    "catalyst_strength",
    "risk_control",
    "data_quality",
]
Confidence = Literal["high", "medium", "low"]
RiskSeverity = Literal["low", "medium", "high"]

PROHIBITED_SCORING_TERMS = (
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


class ScoringEvidence(StrictBaseModel):
    source_field: str
    value_preview: str | None = None
    period: str | None = None
    interpretation: str
    confidence: Confidence


class DimensionScore(StrictBaseModel):
    dimension_name: ScoreDimension
    raw_score: int = Field(ge=0, le=100)
    constrained_score: int = Field(ge=0, le=100)
    weight: float
    max_allowed_score: int | None = Field(default=None, ge=0, le=100)
    score_reason: str
    positive_evidence: list[ScoringEvidence] = Field(default_factory=list)
    negative_evidence: list[ScoringEvidence] = Field(default_factory=list)
    applied_constraints: list[str] = Field(default_factory=list)
    missing_data_penalties: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def constrained_score_must_respect_max(self) -> "DimensionScore":
        if self.max_allowed_score is not None and self.constrained_score > self.max_allowed_score:
            raise ValueError("constrained_score cannot exceed max_allowed_score")
        return self


class RequiredRiskForScoring(StrictBaseModel):
    risk_name: str
    severity: RiskSeverity
    reason: str
    from_context: bool = True


class FundamentalScoringResult(StrictBaseModel):
    schema_version: str = "fundamental_scoring.v1"
    stock_code: str
    stock_name: str | None = None
    strategy_type: str
    generated_at: str
    scoring_mode: str = "rule_based_v1"
    context_quality: str
    max_overall_confidence: str
    readiness_score: int = Field(ge=0, le=100)
    readiness_level: str
    dimension_scores: list[DimensionScore]
    weighted_total_score: int = Field(ge=0, le=100)
    score_confidence: Confidence
    required_risks: list[RequiredRiskForScoring] = Field(default_factory=list)
    scoring_warnings: list[str] = Field(default_factory=list)
    cannot_score_dimensions: list[str] = Field(default_factory=list)
    notes_for_final_analyzer: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def enforce_scoring_constraints(self) -> "FundamentalScoringResult":
        if self.schema_version != "fundamental_scoring.v1":
            raise ValueError("schema_version must be fundamental_scoring.v1")
        if self.max_overall_confidence == "low" and self.score_confidence != "low":
            raise ValueError("low context confidence requires low score_confidence")
        if self.readiness_level == "insufficient" and self.weighted_total_score > 50:
            raise ValueError("insufficient readiness caps weighted_total_score at 50")
        if self.strategy_type == "unknown" and self.weighted_total_score > 50:
            raise ValueError("unknown strategy caps weighted_total_score at 50")
        blocked = {"blocked": 40, "restricted": 60}
        # Dimension-level caps are enforced through max_allowed_score by the engine.
        return self
