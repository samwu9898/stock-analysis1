# -*- coding: utf-8 -*-
"""Schemas for Research Intelligence P0 artifacts.

This module is an AI analyst-layer schema only. It does not mutate the
deterministic pipeline, fetch data, call LLMs, render HTML, or produce trading
instructions.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


RESEARCH_INTELLIGENCE_VERSION = "research_intelligence.v1"
RESEARCH_QUESTIONS_VERSION = "research_questions.v1"

AvailabilityStatus = Literal["available", "partial", "missing", "stale", "not_applicable", "not_assessable"]
ConfidenceCap = Literal["high", "medium", "low", "not_assessable"]
Priority = Literal["P0", "P1", "P2"]

FORBIDDEN_RECOMMENDATION_TERMS = {
    "买入",
    "卖出",
    "加仓",
    "减仓",
    "清仓",
    "止损",
    "止盈",
    "目标价",
    "仓位",
    "盈亏比",
    "K线",
    "均线",
    "技术面",
    "技术指标",
    "technical_skill",
    "trader_skill",
}


def _walk(value: Any, path: str = "") -> list[tuple[str, Any]]:
    rows = [(path, value)]
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            rows.extend(_walk(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            rows.extend(_walk(child, f"{path}[{index}]"))
    return rows


def forbidden_research_text_findings(payload: Any) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path, value in _walk(payload):
        if not isinstance(value, str):
            continue
        for term in FORBIDDEN_RECOMMENDATION_TERMS:
            if term in value:
                findings.append({"path": path, "term": term})
    return findings


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AntiVagueFields(StrictModel):
    data_availability_status: AvailabilityStatus
    confidence_cap: ConfidenceCap
    not_assessable_reason: str = ""
    what_was_checked: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_not_assessable_reason(self) -> "AntiVagueFields":
        if self.data_availability_status in {"missing", "stale", "not_assessable"} and not self.not_assessable_reason:
            raise ValueError("not_assessable_reason is required when data is missing, stale, or not assessable")
        if not self.what_was_checked:
            raise ValueError("what_was_checked must contain at least one checked field or evidence item")
        return self


class SourceHierarchyItem(StrictModel):
    source_tier: str
    source_name: str
    source_period: str | None = None
    source_timestamp: str | None = None
    evidence_type: str
    data_availability_status: AvailabilityStatus
    source_confidence: str
    unit_confidence: str | None = None
    what_was_checked: list[str] = Field(default_factory=list)
    not_assessable_reason: str = ""


class EvidenceClassificationItem(AntiVagueFields):
    evidence_name: str
    evidence_value: Any = None
    evidence_type: str
    source: str
    source_refs: list[str] = Field(default_factory=list)
    interpretation_boundary: str = ""


class StrategyDriverItem(AntiVagueFields):
    driver_name: str
    why_it_matters: str
    required_evidence: list[str] = Field(default_factory=list)
    available_evidence: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    cross_validation_checks: list[str] = Field(default_factory=list)


class CrossValidationItem(AntiVagueFields):
    item_id: str
    strategy_type: str
    business_claim: str
    financial_checks: list[str] = Field(default_factory=list)
    required_evidence: list[str] = Field(default_factory=list)
    available_evidence: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    validation_status: Literal["validated", "partially_validated", "weak", "contradicted", "missing", "not_assessable"]
    triggered_question_ids: list[str] = Field(default_factory=list)


class ContradictionItem(AntiVagueFields):
    rule_id: str
    triggered: Literal["true", "false", "not_assessable"]
    severity: Literal["high", "medium", "low"]
    contradiction_type: Literal[
        "actual_contradiction",
        "proxy_overread",
        "missing_bridge",
        "missing_data_blocker",
        "low_confidence_classification_blocker",
        "not_triggered",
    ]
    claim_or_risk: str
    evidence_for: list[str] = Field(default_factory=list)
    evidence_against: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    research_question_id: str | None = None


class ResearchQuestion(AntiVagueFields):
    question_id: str
    question: str
    category: str
    priority: Priority
    evidence_trigger: str = ""
    trigger_rule_id: str = ""
    why_it_matters: str
    evidence_gap: str = ""
    suggested_recipient: str = "manual_review"
    expected_answer_type: str = "explanation"
    source_refs: list[str] = Field(default_factory=list)
    related_cross_validation_item_id: str | None = None

    @model_validator(mode="after")
    def downgrade_p0_without_trigger(self) -> "ResearchQuestion":
        if self.priority == "P0" and not self.evidence_trigger:
            self.priority = "P1"
        return self


class SafetyBoundary(StrictModel):
    safe: bool = True
    blocked_terms: list[str] = Field(default_factory=list)
    blocked_count: int = 0
    boundary_summary: str = "Fundamental research artifact only; no account, execution, price target, or technical-analysis content."


class ResearchIntelligencePack(StrictModel):
    schema_version: str = RESEARCH_INTELLIGENCE_VERSION
    stock_code: str
    stock_name: str | None = None
    generated_at: str
    data_cutoff: str | None = None
    strategy_type: str
    sub_type: str | None = None
    source_hierarchy: list[SourceHierarchyItem] = Field(default_factory=list)
    evidence_classification: list[EvidenceClassificationItem] = Field(default_factory=list)
    strategy_driver_map: dict[str, list[StrategyDriverItem]] = Field(default_factory=dict)
    business_financial_cross_validation: list[CrossValidationItem] = Field(default_factory=list)
    rule_triggered_contradictions: list[ContradictionItem] = Field(default_factory=list)
    manual_review_items: list[ResearchQuestion] = Field(default_factory=list)
    ir_question_candidates: list[ResearchQuestion] = Field(default_factory=list)
    safety_boundary: SafetyBoundary = Field(default_factory=SafetyBoundary)

    @field_validator("schema_version")
    @classmethod
    def version_must_match(cls, value: str) -> str:
        if value != RESEARCH_INTELLIGENCE_VERSION:
            raise ValueError(f"schema_version must be {RESEARCH_INTELLIGENCE_VERSION}")
        return value


class ResearchQuestionSet(StrictModel):
    schema_version: str = RESEARCH_QUESTIONS_VERSION
    stock_code: str
    stock_name: str | None = None
    generated_at: str
    questions: list[ResearchQuestion] = Field(default_factory=list)
    p0_summary: str = ""
    p1_summary: str = ""
    p2_summary: str = ""
    do_not_conclude_until_resolved: list[str] = Field(default_factory=list)

    @field_validator("schema_version")
    @classmethod
    def version_must_match(cls, value: str) -> str:
        if value != RESEARCH_QUESTIONS_VERSION:
            raise ValueError(f"schema_version must be {RESEARCH_QUESTIONS_VERSION}")
        return value

    @model_validator(mode="after")
    def enforce_p0_evidence_trigger(self) -> "ResearchQuestionSet":
        for question in self.questions:
            if question.priority == "P0" and not question.evidence_trigger:
                question.priority = "P1"
        return self


def validate_research_intelligence_pack(payload: dict[str, Any]) -> dict[str, Any]:
    model = ResearchIntelligencePack.model_validate(payload)
    dumped = model.model_dump()
    findings = forbidden_research_text_findings(dumped)
    return {
        "valid": not findings,
        "safety": {
            "safe": not findings,
            "blocked_terms": sorted({item["term"] for item in findings}),
            "blocked_count": len(findings),
            "findings": findings,
        },
        "research_intelligence": dumped,
    }


def validate_research_question_set(payload: dict[str, Any]) -> dict[str, Any]:
    model = ResearchQuestionSet.model_validate(payload)
    dumped = model.model_dump()
    findings = forbidden_research_text_findings(dumped)
    return {
        "valid": not findings,
        "safety": {
            "safe": not findings,
            "blocked_terms": sorted({item["term"] for item in findings}),
            "blocked_count": len(findings),
            "findings": findings,
        },
        "research_questions": dumped,
    }
