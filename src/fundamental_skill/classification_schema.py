# -*- coding: utf-8 -*-
"""Schemas for rule-based stock classification and framework selection."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


StrategyType = Literal[
    "resource_swing",
    "resource_core",
    "right_trend_growth",
    "semiconductor_cycle",
    "stable_growth",
    "advanced_manufacturing_growth",
    "satellite_communication_infrastructure",
    "low_altitude_economy_infrastructure",
    "life_science_cxo_services",
    "ai_datacenter_infrastructure",
    "theme_only",
    "unknown",
]
Confidence = Literal["high", "medium", "low"]


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ClassificationEvidence(StrictBaseModel):
    source_field: str
    matched_value: str
    matched_rule: str
    weight: int
    explanation: str


class StockClassificationResult(StrictBaseModel):
    stock_code: str
    stock_name: str | None = None
    strategy_type: StrategyType
    sub_type: str | None = None
    confidence: Confidence
    confidence_score: int = Field(ge=0, le=100)
    reasons: list[str] = Field(default_factory=list)
    evidence: list[ClassificationEvidence] = Field(default_factory=list)
    alternative_types: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def confidence_must_match_score(self) -> "StockClassificationResult":
        expected = (
            "high"
            if self.confidence_score >= 75
            else "medium"
            if self.confidence_score >= 50
            else "low"
        )
        if self.confidence != expected:
            raise ValueError(
                f"confidence must be {expected} for confidence_score={self.confidence_score}"
            )
        if self.strategy_type == "unknown" and self.confidence != "low":
            raise ValueError("unknown classification should use low confidence")
        return self


class FundamentalFramework(StrictBaseModel):
    strategy_type: StrategyType
    display_name: str
    description: str
    required_focus: list[str]
    must_track_indicators: list[str]
    key_risks: list[str]
    preferred_metrics: list[str]
    invalidation_focus: list[str]
    common_mistakes: list[str]
    confidence_penalty_missing_fields: list[str]
