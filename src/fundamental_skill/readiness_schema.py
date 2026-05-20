# -*- coding: utf-8 -*-
"""Data readiness planning schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


Category = Literal[
    "basic_info",
    "financial",
    "valuation",
    "business_composition",
    "industry",
    "news",
    "external_variable",
    "other",
]
Importance = Literal["critical", "high", "medium", "low"]
FieldStatus = Literal["available", "missing", "partial", "not_applicable"]
ConfidenceImpact = Literal["severe", "moderate", "minor", "none"]
ReadinessLevel = Literal["sufficient", "usable_with_warnings", "weak", "insufficient"]


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FieldRequirement(StrictBaseModel):
    field_name: str
    display_name: str
    category: Category
    importance: Importance
    reason: str
    expected_location: list[str] = Field(default_factory=list)
    affects_analysis: list[str] = Field(default_factory=list)


class FieldReadiness(StrictBaseModel):
    field_name: str
    display_name: str
    status: FieldStatus
    importance: Importance
    found_value_preview: str | None = None
    missing_reason: str | None = None
    impact_on_confidence: ConfidenceImpact
    suggested_fix: str
    evidence_path: str | None = None


class DataReadinessPlan(StrictBaseModel):
    schema_version: str = "data_readiness.v1"
    stock_code: str
    stock_name: str | None = None
    strategy_type: str
    classification_confidence: str
    framework_name: str
    generated_at: str
    readiness_score: int = Field(ge=0, le=100)
    readiness_level: ReadinessLevel
    field_readiness: list[FieldReadiness] = Field(default_factory=list)
    critical_missing_fields: list[str] = Field(default_factory=list)
    high_priority_missing_fields: list[str] = Field(default_factory=list)
    available_fields: list[str] = Field(default_factory=list)
    partial_fields: list[str] = Field(default_factory=list)
    analysis_blockers: list[str] = Field(default_factory=list)
    confidence_penalty_reasons: list[str] = Field(default_factory=list)
    recommended_data_to_collect: list[str] = Field(default_factory=list)
    notes_for_analyzer: list[str] = Field(default_factory=list)
    notes_for_scorer: list[str] = Field(default_factory=list)

    @field_validator("schema_version")
    @classmethod
    def schema_version_must_match(cls, value: str) -> str:
        if value != "data_readiness.v1":
            raise ValueError("schema_version must be data_readiness.v1")
        return value

    @model_validator(mode="after")
    def readiness_level_must_match_constraints(self) -> "DataReadinessPlan":
        if self.critical_missing_fields and self.readiness_level == "sufficient":
            raise ValueError("readiness_level cannot be sufficient with critical missing fields")
        if self.strategy_type == "unknown" and self.readiness_level in {"sufficient", "usable_with_warnings"}:
            raise ValueError("unknown strategy_type cannot exceed weak readiness")
        return self
