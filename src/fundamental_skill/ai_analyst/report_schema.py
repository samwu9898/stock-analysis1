# -*- coding: utf-8 -*-
"""Schema validation for AI-generated fundamental reports."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from .safety import check_text_safety, detect_garbled_text


FundamentalView = Literal[
    "supportive_for_further_evaluation",
    "neutral_requires_more_evidence",
    "not_supportive",
    "insufficient_data",
]


class AIReportModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ai_report_version: str = "fundamental_ai_report.v1"
    stock_code: str
    stock_name: str | None = None
    fundamental_view: FundamentalView
    executive_summary: str
    confidence_explanation: str
    confidence_breakdown: list[Any] = Field(default_factory=list)
    supporting_evidence: list[Any] = Field(default_factory=list)
    limiting_evidence: list[Any] = Field(default_factory=list)
    unknown_or_missing_evidence: list[Any] = Field(default_factory=list)
    business_analysis: str
    financial_quality_analysis: str
    valuation_analysis: str
    industry_cycle_analysis: str
    risk_analysis: list[Any] = Field(default_factory=list)
    must_track_analysis: list[Any] = Field(default_factory=list)
    data_limitations: list[Any] = Field(default_factory=list)
    invalidation_watch: list[Any] = Field(default_factory=list)
    final_summary: str

    @field_validator("ai_report_version")
    @classmethod
    def version_must_match(cls, value: str) -> str:
        if value != "fundamental_ai_report.v1":
            raise ValueError("ai_report_version must be fundamental_ai_report.v1")
        return value


def validate_ai_report(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate report shape and safety, returning a JSON-safe summary."""

    try:
        model = AIReportModel.model_validate(payload)
    except ValidationError as exc:
        quality = detect_garbled_text(payload)
        return {
            "valid": False,
            "schema_errors": exc.errors(),
            "safety": check_text_safety(payload, allow_policy_context=False),
            "quality": quality,
            "report_quality_status": quality["status"],
            "warnings": quality["warnings"],
            "report": None,
        }

    dumped = model.model_dump()
    safety = check_text_safety(dumped, allow_policy_context=False)
    quality = detect_garbled_text(dumped)
    return {
        "valid": safety["safe"],
        "schema_errors": [],
        "safety": safety,
        "quality": quality,
        "report_quality_status": quality["status"],
        "warnings": quality["warnings"],
        "report": dumped,
    }
