# -*- coding: utf-8 -*-
"""Pydantic schema for fundamental_skill outputs."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .constants import ALLOWED_TRADER_ACTION_HINTS


SourceType = Literal[
    "akshare",
    "user_input",
    "news",
    "financial_statement",
    "derived",
    "unknown",
]
RiskSeverity = Literal["low", "medium", "high"]
CatalystType = Literal[
    "earnings",
    "policy",
    "industry_cycle",
    "commodity_price",
    "order",
    "valuation",
    "other",
]
Importance = Literal["low", "medium", "high"]
ValuationLevel = Literal["low", "reasonable", "high", "unknown"]
CyclePosition = Literal["upcycle", "neutral", "downcycle", "unknown"]
ThesisSupport = Literal[
    "supported",
    "partially_supported",
    "unsupported",
    "unverified",
    "none",
]
StrategyType = Literal[
    "resource_swing",
    "resource_core",
    "right_trend_growth",
    "semiconductor_cycle",
    "stable_growth",
    "advanced_manufacturing_growth",
    "satellite_communication_infrastructure",
    "low_altitude_economy_infrastructure",
    "theme_only",
    "unknown",
]
Status = Literal["supportive", "neutral", "negative", "insufficient_data"]
Confidence = Literal["high", "medium", "low"]


class SkillBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DataSource(SkillBaseModel):
    name: str
    source_type: SourceType
    fetched_at: Optional[str] = None
    period: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


class Evidence(SkillBaseModel):
    source: str
    metric_name: Optional[str] = None
    value: Optional[Any] = None
    period: Optional[str] = None
    interpretation: str


class RiskFlag(SkillBaseModel):
    name: str
    severity: RiskSeverity
    evidence: list[Evidence] = Field(default_factory=list)
    monitor_method: str


class Catalyst(SkillBaseModel):
    name: str
    catalyst_type: CatalystType
    evidence: list[Evidence] = Field(default_factory=list)
    expected_timeframe: Optional[str] = None
    uncertainty: RiskSeverity


class TrackIndicator(SkillBaseModel):
    name: str
    current_value: Optional[Any] = None
    importance: Importance
    monitor_frequency: str
    reason: str


class InvalidationCondition(SkillBaseModel):
    condition: str
    evidence_needed: str
    action_hint_for_trader: str

    @field_validator("action_hint_for_trader")
    @classmethod
    def action_hint_must_be_allowed(cls, value: str) -> str:
        if value not in ALLOWED_TRADER_ACTION_HINTS:
            allowed = ", ".join(ALLOWED_TRADER_ACTION_HINTS)
            raise ValueError(f"action_hint_for_trader must be one of: {allowed}")
        return value


class FinancialQuality(SkillBaseModel):
    revenue_trend: Optional[str] = None
    profit_trend: Optional[str] = None
    margin_trend: Optional[str] = None
    cashflow_quality: Optional[str] = None
    debt_pressure: Optional[str] = None
    one_off_profit_risk: Optional[str] = None
    score: int = Field(ge=0, le=100)
    evidence: list[Evidence] = Field(default_factory=list)


class ValuationView(SkillBaseModel):
    valuation_level: ValuationLevel
    valuation_method: Optional[str] = None
    peer_comparison: Optional[str] = None
    historical_percentile: Optional[str] = None
    score: int = Field(ge=0, le=100)
    evidence: list[Evidence] = Field(default_factory=list)


class IndustryCycle(SkillBaseModel):
    cycle_position: CyclePosition
    industry_trend: Optional[str] = None
    key_external_variables: list[str] = Field(default_factory=list)
    score: int = Field(ge=0, le=100)
    evidence: list[Evidence] = Field(default_factory=list)


class ThesisCheck(SkillBaseModel):
    user_thesis: Optional[str] = None
    thesis_support: ThesisSupport
    supporting_evidence: list[Evidence] = Field(default_factory=list)
    opposing_evidence: list[Evidence] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)


class FundamentalAnalysisResult(SkillBaseModel):
    schema_version: str = "fundamental.v1"
    stock_code: str
    stock_name: Optional[str] = None
    analysis_date: str
    strategy_type: StrategyType
    sub_type: Optional[str] = None
    status: Status
    confidence: Confidence
    confidence_reason: str
    fundamental_score: int = Field(ge=0, le=100)
    business_summary: str
    key_drivers: list[str] = Field(default_factory=list)
    financial_quality: FinancialQuality
    valuation_view: ValuationView
    industry_cycle: IndustryCycle
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    catalysts: list[Catalyst] = Field(default_factory=list)
    must_track_indicators: list[TrackIndicator] = Field(default_factory=list)
    invalidation_conditions: list[InvalidationCondition] = Field(default_factory=list)
    thesis_check: ThesisCheck
    suitable_strategy_type: str
    trader_summary: str
    data_sources: list[DataSource] = Field(default_factory=list)
    data_timestamp: str
    missing_fields: list[str] = Field(default_factory=list)
    valid_until: Optional[str] = None
    refresh_triggers: list[str] = Field(default_factory=list)
    raw_data_path: Optional[str] = None

    @field_validator("schema_version")
    @classmethod
    def schema_version_must_match(cls, value: str) -> str:
        if value != "fundamental.v1":
            raise ValueError("schema_version must be fundamental.v1")
        return value
