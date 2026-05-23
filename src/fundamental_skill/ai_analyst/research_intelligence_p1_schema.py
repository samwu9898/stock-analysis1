# -*- coding: utf-8 -*-
"""Schemas for Research Intelligence P1.1 driver-matrix artifacts.

This module is an independent AI analyst-layer schema. It does not mutate the
deterministic pipeline, fetch data, call LLMs, render HTML, or produce trading
instructions.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


RESEARCH_INTELLIGENCE_P1_VERSION = "research_intelligence_p1.v1"
RESEARCH_QUESTIONS_P1_VERSION = "research_questions_p1.v1"
TRANSMISSION_PATH_FALLBACK = "传导路径无法从当前证据包验证"
LESS_THAN_TWO_BUCKETS_REASON = "Less than two independent source buckets are available."

AvailabilityStatus = Literal["available", "partial", "missing", "stale", "not_applicable", "not_assessable"]
ConfidenceCap = Literal["high", "medium", "low", "not_assessable"]
DriverLayer = Literal["macro", "policy", "industry", "supply_chain", "commodity", "company", "business", "financial", "risk"]
QuestionPriority = Literal["P0", "P1", "P2"]
ConsensusStatus = Literal["consensus", "divergence", "contradiction", "not_assessable"]

ALLOWED_SOURCE_BUCKETS = {
    "company_disclosure",
    "financial_statement",
    "structured_data",
    "news_media",
    "company_ir",
    "industry_official",
    "exchange_regulator",
}

VAGUE_TRANSMISSION_PHRASES = {
    "卫星通信需求向好，公司受益",
    "政策支持，公司兑现",
    "容量资源丰富，公司收入稳定",
    "宏观向好，公司受益",
    "行业空间大，公司有望受益",
    "政策支持，公司有望兑现",
    "政策持续支持，公司有望兑现",
    "低空经济政策向好，公司受益",
    "空域改革推进，公司飞行量提升",
    "地方政府加大低空投入，公司收入增长",
    "policy supports demand, company benefits",
    "industry demand is strong, company should benefit",
    "low-altitude policy improves, company benefits",
    "airspace reform progresses, company flight volume improves",
    "local government spending increases, company revenue grows",
}

FORBIDDEN_SAFETY_TERMS = {
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
    "技术面",
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


def forbidden_p1_text_findings(payload: Any) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path, value in _walk(payload):
        if not isinstance(value, str):
            continue
        for term in FORBIDDEN_SAFETY_TERMS:
            if term in value:
                findings.append({"path": path, "term": term})
    return findings


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DriverFactor(StrictModel):
    layer: DriverLayer
    driver_factor: str
    driver_scope: str
    why_it_matters: str
    required_evidence: list[str] = Field(default_factory=list)
    available_evidence: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    company_transmission_path: str
    data_availability_status: AvailabilityStatus
    confidence_cap: ConfidenceCap
    not_assessable_reason: str = ""
    what_was_checked: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    research_question: str
    interpretation_guard: str

    @model_validator(mode="after")
    def enforce_driver_contract(self) -> "DriverFactor":
        if not self.required_evidence:
            raise ValueError("required_evidence must contain at least one evidence requirement")
        if not self.what_was_checked:
            raise ValueError("what_was_checked must contain at least one checked field")
        if self.data_availability_status in {"missing", "stale", "not_assessable"} and not self.not_assessable_reason:
            raise ValueError("not_assessable_reason is required when data is missing, stale, or not assessable")
        self._enforce_company_transmission_path()
        return self

    def _enforce_company_transmission_path(self) -> None:
        path = self.company_transmission_path.strip()
        if any(phrase in path for phrase in VAGUE_TRANSMISSION_PHRASES):
            raise ValueError("company_transmission_path contains vague transmission language")
        if path == TRANSMISSION_PATH_FALLBACK:
            if self.confidence_cap != "not_assessable":
                raise ValueError("fallback company_transmission_path requires confidence_cap=not_assessable")
            return
        if self.confidence_cap == "not_assessable":
            raise ValueError("non-fallback company_transmission_path cannot use confidence_cap=not_assessable")
        if "evidence_pack." not in path or "=" not in path:
            raise ValueError("company_transmission_path must cite concrete evidence_pack field/value nodes")
        if not self.source_refs:
            raise ValueError("source_refs are required for a concrete company_transmission_path")


class ResearchDriverQuestion(StrictModel):
    question: str
    layer: DriverLayer
    driver_factor: str
    priority: QuestionPriority
    evidence_trigger: str
    why_it_matters: str
    next_check: str
    data_availability_status: AvailabilityStatus
    confidence_cap: ConfidenceCap

    @model_validator(mode="after")
    def enforce_question_contract(self) -> "ResearchDriverQuestion":
        if not self.evidence_trigger:
            raise ValueError("evidence_trigger is required for every P1 driver question")
        if self.data_availability_status in {"missing", "not_assessable"} and self.confidence_cap == "high":
            raise ValueError("missing or not_assessable questions cannot have high confidence_cap")
        return self


class SourceBucketSummary(StrictModel):
    source_buckets: list[str] = Field(default_factory=list)
    independent_source_count: int = 0
    consensus_assessment_status: ConsensusStatus = "not_assessable"
    not_assessable_reason: str = ""

    @field_validator("source_buckets")
    @classmethod
    def buckets_must_be_known_and_unique(cls, value: list[str]) -> list[str]:
        unique = sorted(set(value))
        unknown = [item for item in unique if item not in ALLOWED_SOURCE_BUCKETS]
        if unknown:
            raise ValueError(f"unknown source bucket(s): {', '.join(unknown)}")
        return unique

    @model_validator(mode="after")
    def enforce_bucket_counting(self) -> "SourceBucketSummary":
        self.independent_source_count = len(set(self.source_buckets))
        if self.independent_source_count < 2:
            if self.consensus_assessment_status != "not_assessable":
                raise ValueError("fewer than two independent source buckets require not_assessable consensus")
            if self.not_assessable_reason != LESS_THAN_TWO_BUCKETS_REASON:
                raise ValueError(f"not_assessable_reason must be {LESS_THAN_TWO_BUCKETS_REASON!r}")
        elif not self.not_assessable_reason and self.consensus_assessment_status == "not_assessable":
            self.not_assessable_reason = "P1.1 pilot records source-bucket independence only; full consensus assessment is deferred."
        return self


class SafetyBoundary(StrictModel):
    safe: bool = True
    blocked_terms: list[str] = Field(default_factory=list)
    blocked_count: int = 0
    boundary_summary: str = "Fundamental research artifact only; no execution, valuation target, sizing, chart-timing, or account-action content."


class ResearchDriverMatrixPack(StrictModel):
    schema_version: str = RESEARCH_INTELLIGENCE_P1_VERSION
    stock_code: str
    stock_name: str | None = None
    generated_at: str
    strategy_type: str
    sub_type: str | None = None
    source_evidence_pack_path: str
    source_p0_pack_path: str | None = None
    driver_matrix: list[DriverFactor] = Field(default_factory=list)
    not_assessable_drivers: list[DriverFactor] = Field(default_factory=list)
    driver_research_questions: list[ResearchDriverQuestion] = Field(default_factory=list)
    source_bucket_summary: SourceBucketSummary
    safety_boundary: SafetyBoundary = Field(default_factory=SafetyBoundary)

    @field_validator("schema_version")
    @classmethod
    def version_must_match(cls, value: str) -> str:
        if value != RESEARCH_INTELLIGENCE_P1_VERSION:
            raise ValueError(f"schema_version must be {RESEARCH_INTELLIGENCE_P1_VERSION}")
        return value

    @model_validator(mode="after")
    def enforce_pack_safety(self) -> "ResearchDriverMatrixPack":
        self.not_assessable_drivers = [
            item
            for item in self.driver_matrix
            if item.data_availability_status == "not_assessable" or item.confidence_cap == "not_assessable"
        ]
        findings = forbidden_p1_text_findings(self.model_dump(exclude={"safety_boundary"}))
        self.safety_boundary = SafetyBoundary(
            safe=not findings,
            blocked_terms=sorted({item["term"] for item in findings}),
            blocked_count=len(findings),
        )
        return self


class ResearchDriverQuestionSet(StrictModel):
    schema_version: str = RESEARCH_QUESTIONS_P1_VERSION
    stock_code: str
    stock_name: str | None = None
    generated_at: str
    strategy_type: str
    sub_type: str | None = None
    questions: list[ResearchDriverQuestion] = Field(default_factory=list)
    source_driver_matrix_path: str | None = None
    p1_summary: str = ""
    safety_boundary: SafetyBoundary = Field(default_factory=SafetyBoundary)

    @field_validator("schema_version")
    @classmethod
    def version_must_match(cls, value: str) -> str:
        if value != RESEARCH_QUESTIONS_P1_VERSION:
            raise ValueError(f"schema_version must be {RESEARCH_QUESTIONS_P1_VERSION}")
        return value

    @model_validator(mode="after")
    def enforce_question_set_safety(self) -> "ResearchDriverQuestionSet":
        findings = forbidden_p1_text_findings(self.model_dump(exclude={"safety_boundary"}))
        self.safety_boundary = SafetyBoundary(
            safe=not findings,
            blocked_terms=sorted({item["term"] for item in findings}),
            blocked_count=len(findings),
        )
        return self


def validate_research_driver_matrix_pack(payload: dict[str, Any]) -> dict[str, Any]:
    model = ResearchDriverMatrixPack.model_validate(payload)
    dumped = model.model_dump()
    return {
        "valid": model.safety_boundary.safe,
        "safety": model.safety_boundary.model_dump(),
        "research_intelligence_p1": dumped,
    }


def validate_research_driver_question_set(payload: dict[str, Any]) -> dict[str, Any]:
    model = ResearchDriverQuestionSet.model_validate(payload)
    dumped = model.model_dump()
    return {
        "valid": model.safety_boundary.safe,
        "safety": model.safety_boundary.model_dump(),
        "research_questions_p1": dumped,
    }
