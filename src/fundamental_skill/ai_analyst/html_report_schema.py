# -*- coding: utf-8 -*-
"""Schema and safety validation for Fundamental HTML Report v1.

The schema is presentation-layer only. It does not call the deterministic
pipeline, fetch market data, introduce technical analysis, or create any
trading-oriented output.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator


REPORT_VERSION = "fundamental_html_report.v1"

DiagnosisLevel = Literal["健康", "一般", "承压", "无法判断"]

FORBIDDEN_FIELD_TOKENS = {
    "target_price",
    "price_target",
    "buy",
    "sell",
    "add_position",
    "reduce_position",
    "clear_position",
    "stop_loss",
    "take_profit",
    "position",
    "position_size",
    "risk_reward",
    "trade_action",
    "trading_signal",
    "technical_analysis",
    "technical_skill",
    "trader_skill",
    "trading_terminal",
    "entry",
    "exit",
    "timing",
    "kline",
    "k_line",
    "technical",
    "ma5",
    "ma20",
    "ma60",
}

FORBIDDEN_TEXT_TERMS = {
    "目标价",
    "买入",
    "卖出",
    "加仓",
    "减仓",
    "清仓",
    "止损",
    "止盈",
    "仓位",
    "盈亏比",
    "K线",
    "均线",
    "技术面",
    "技术面分析",
    "技术指标",
    "买卖时机",
    "交易终端",
    "交易建议",
    "technical_skill",
    "trader_skill",
}

ALLOWED_POLICY_PATHS = {
    "safety_boundary.statement",
    "safety_boundary.forbidden_actions_excluded",
    "report_meta.safety_boundary",
}

ALLOWED_FIELD_NAMES = {
    "industry_position",
}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _normalize_key(key: Any) -> str:
    return str(key or "").strip().lower().replace("-", "_").replace(" ", "_")


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


def forbidden_key_findings(payload: Any) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path, value in _walk(payload):
        if not isinstance(value, dict):
            continue
        for key in value:
            normalized = _normalize_key(key)
            if normalized == "forbidden_actions_excluded":
                continue
            if normalized in ALLOWED_FIELD_NAMES:
                continue
            for token in FORBIDDEN_FIELD_TOKENS:
                key_parts = set(normalized.split("_"))
                is_exact = normalized == token
                is_compound_field = normalized.endswith(f"_{token}") or normalized.startswith(f"{token}_")
                is_single_word_token = "_" not in token and token in key_parts
                if is_exact or is_compound_field or is_single_word_token:
                    findings.append({"path": f"{path}.{key}" if path else str(key), "token": token})
    return findings


def forbidden_text_findings(payload: Any) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path, value in _walk(payload):
        if not isinstance(value, str):
            continue
        if any(path.startswith(allowed) for allowed in ALLOWED_POLICY_PATHS):
            continue
        for term in FORBIDDEN_TEXT_TERMS:
            if term in value:
                findings.append({"path": path, "term": term})
    return findings


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReportMeta(StrictModel):
    stock_code: str
    stock_name: str | None = None
    generated_at: str
    strategy_type: str
    strategy_type_label: str
    sub_type: str | None = None
    sub_type_label: str | None = None
    status: str
    confidence: str
    fundamental_score: float | int | None = None
    data_quality_status: str
    safety_boundary: str


class CoreConclusion(StrictModel):
    title: str
    summary: str
    supporting_points: list[str] = Field(default_factory=list)
    limiting_points: list[str] = Field(default_factory=list)
    must_track_points: list[str] = Field(default_factory=list)
    evidence_confidence_explanation: str


class CompanyProfile(StrictModel):
    main_business: str
    business_segments: list[dict[str, Any]] = Field(default_factory=list)
    ownership_or_company_nature: str
    framework_identity: str
    core_business_anchor: str


class RecentFundamentalUpdates(StrictModel):
    financial_update: str
    business_update: str
    policy_or_industry_update: str
    unavailable_news_note: str


class BusinessCompositionAnalysis(StrictModel):
    segment_table: list[dict[str, Any]] = Field(default_factory=list)
    core_segment: str
    drag_segment: str
    growth_optional_segment: str
    analysis: str


class FinancialQualityDiagnosis(StrictModel):
    revenue_quality: str
    profit_quality: str
    cashflow_quality: str
    receivables_pressure: str
    inventory_pressure: str
    contract_liabilities_interpretation: str
    capex_pressure: str
    free_cashflow_interpretation: str
    final_diagnosis: str
    diagnosis_level: DiagnosisLevel


class ValuationExplanation(StrictModel):
    valuation_metrics: list[dict[str, Any]] = Field(default_factory=list)
    valuation_interpretation: str
    peer_benchmark_status: str
    what_must_be_proven_to_justify_valuation: list[str] = Field(default_factory=list)
    cannot_determine_items: list[str] = Field(default_factory=list)


class CoreFundamentalQuestion(StrictModel):
    main_question: str
    key_conflict: str
    what_would_confirm: list[str] = Field(default_factory=list)
    what_would_invalidate: list[str] = Field(default_factory=list)


class IndustryCyclePositioning(StrictModel):
    cycle_stage: str
    policy_or_demand_background: str
    evidence_strength: str
    missing_evidence: list[str] = Field(default_factory=list)


class ValueChainAndBusinessModel(StrictModel):
    upstream: str
    downstream: str
    customer_structure: str
    how_company_makes_money: str
    margin_source: str
    moat_claims: list[str] = Field(default_factory=list)
    unproven_moats: list[str] = Field(default_factory=list)


class FundamentalScenario(StrictModel):
    scenario_name: str
    fundamental_assumptions: list[str] = Field(default_factory=list)
    key_variables: list[str] = Field(default_factory=list)
    impact_on_fundamentals: str
    evidence_strength: str
    evidence_needed: list[str] = Field(default_factory=list)


class FundamentalScenarioAnalysis(StrictModel):
    optimistic_case: FundamentalScenario
    base_case: FundamentalScenario
    downside_case: FundamentalScenario


class PeerComparison(StrictModel):
    peer_benchmark_status: str
    comparison_table: list[dict[str, Any]] = Field(default_factory=list)
    interpretation: str
    peer_data_missing_note: str


class RiskAnalysis(StrictModel):
    business_risks: list[str] = Field(default_factory=list)
    financial_risks: list[str] = Field(default_factory=list)
    industry_risks: list[str] = Field(default_factory=list)
    policy_risks: list[str] = Field(default_factory=list)
    data_gap_risks: list[str] = Field(default_factory=list)


class MustTrackIndicator(StrictModel):
    indicator: str
    priority: str
    current_status: str
    why_it_matters: str
    next_evidence_needed: str
    current_value: str | int | float | None = None


class FollowUpReviewCondition(StrictModel):
    condition: str
    why_it_matters: str
    evidence_needed: str


class DataQualityAndUnknowns(StrictModel):
    available_data: list[str] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    proxy_fields: list[str] = Field(default_factory=list)
    cannot_determine: list[str] = Field(default_factory=list)
    source_limitations: list[str] = Field(default_factory=list)


class SafetyBoundary(StrictModel):
    statement: str
    forbidden_actions_excluded: list[str] = Field(default_factory=list)


class ResearchAnchor(StrictModel):
    main_thesis: str = ""
    key_conflict: str = ""
    current_stage: str = ""
    what_is_proven: list[str] = Field(default_factory=list)
    what_is_unproven: list[str] = Field(default_factory=list)


class QualityScoreItem(StrictModel):
    score: float | int | None = None
    max_score: float | int | None = 10
    label: str = ""
    explanation: str = ""
    evidence_basis: list[str] = Field(default_factory=list)


class QualityScoreBreakdown(StrictModel):
    industry_position: QualityScoreItem = Field(default_factory=QualityScoreItem)
    business_quality: QualityScoreItem = Field(default_factory=QualityScoreItem)
    growth_realization: QualityScoreItem = Field(default_factory=QualityScoreItem)
    financial_quality: QualityScoreItem = Field(default_factory=QualityScoreItem)
    valuation_explainability: QualityScoreItem = Field(default_factory=QualityScoreItem)
    risk_identifiability: QualityScoreItem = Field(default_factory=QualityScoreItem)


class ValueChainMap(StrictModel):
    upstream: str = ""
    company_role: str = ""
    downstream: str = ""
    profit_source: str = ""
    unproven_moats: list[str] = Field(default_factory=list)
    key_bottlenecks: list[str] = Field(default_factory=list)


class ElasticityFormula(StrictModel):
    formula_title: str = ""
    formula_text: str = ""
    key_variables: list[str] = Field(default_factory=list)
    interpretation: str = ""
    data_limitations: list[str] = Field(default_factory=list)


class TrackingPlanItem(StrictModel):
    indicator: str = ""
    frequency: str = ""
    why_it_matters: str = ""
    trigger_for_review: str = ""


class TrackingPlanGroup(StrictModel):
    group_name: str = ""
    items: list[TrackingPlanItem] = Field(default_factory=list)


class FinancialRatioCaveat(StrictModel):
    ratio_name: str = ""
    caveat: str = ""
    interpretation_strength: str = ""
    required_follow_up_data: list[str] = Field(default_factory=list)


class FundamentalHtmlReport(StrictModel):
    report_version: str = REPORT_VERSION
    report_meta: ReportMeta
    hero_tags: list[str] = Field(default_factory=list)
    core_conclusion: CoreConclusion
    research_anchor: ResearchAnchor = Field(default_factory=ResearchAnchor)
    company_profile: CompanyProfile
    recent_fundamental_updates: RecentFundamentalUpdates
    business_composition_analysis: BusinessCompositionAnalysis
    financial_quality_diagnosis: FinancialQualityDiagnosis
    financial_ratio_caveats: list[FinancialRatioCaveat] = Field(default_factory=list)
    valuation_explanation: ValuationExplanation
    core_fundamental_question: CoreFundamentalQuestion
    industry_cycle_positioning: IndustryCyclePositioning
    value_chain_and_business_model: ValueChainAndBusinessModel
    value_chain_map: ValueChainMap = Field(default_factory=ValueChainMap)
    quality_score_breakdown: QualityScoreBreakdown = Field(default_factory=QualityScoreBreakdown)
    elasticity_formula: ElasticityFormula = Field(default_factory=ElasticityFormula)
    fundamental_scenario_analysis: FundamentalScenarioAnalysis
    peer_comparison: PeerComparison
    risk_analysis: RiskAnalysis
    must_track_indicators: list[MustTrackIndicator] = Field(default_factory=list)
    tracking_plan_groups: list[TrackingPlanGroup] = Field(default_factory=list)
    follow_up_review_conditions: list[FollowUpReviewCondition] = Field(default_factory=list)
    data_quality_and_unknowns: DataQualityAndUnknowns
    safety_boundary: SafetyBoundary

    @field_validator("report_version")
    @classmethod
    def version_must_match(cls, value: str) -> str:
        if value != REPORT_VERSION:
            raise ValueError(f"report_version must be {REPORT_VERSION}")
        return value

    @model_validator(mode="before")
    @classmethod
    def reject_forbidden_keys(cls, value: Any) -> Any:
        findings = forbidden_key_findings(value)
        if findings:
            joined = ", ".join(f"{item['path']}({item['token']})" for item in findings[:8])
            raise ValueError(f"forbidden trading or technical fields are not allowed: {joined}")
        return value


def validate_fundamental_html_report(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate HTML report JSON and return a compact JSON-safe summary."""

    try:
        model = FundamentalHtmlReport.model_validate(payload)
    except ValidationError as exc:
        return {
            "valid": False,
            "schema_errors": exc.errors(),
            "safety": {
                "safe": False,
                "forbidden_key_findings": forbidden_key_findings(payload),
                "forbidden_text_findings": forbidden_text_findings(payload),
            },
            "report": None,
        }
    except ValueError as exc:
        return {
            "valid": False,
            "schema_errors": [{"type": "value_error", "msg": str(exc)}],
            "safety": {
                "safe": False,
                "forbidden_key_findings": forbidden_key_findings(payload),
                "forbidden_text_findings": forbidden_text_findings(payload),
            },
            "report": None,
        }

    dumped = model.model_dump()
    text_findings = forbidden_text_findings(dumped)
    safe = not text_findings
    return {
        "valid": safe,
        "schema_errors": [],
        "safety": {
            "safe": safe,
            "forbidden_key_findings": [],
            "forbidden_text_findings": text_findings,
        },
        "report": dumped,
    }


def schema_example() -> dict[str, Any]:
    """Return a minimal empty-safe example shape for prompt construction."""

    return {
        "report_version": REPORT_VERSION,
        "report_meta": {
            "stock_code": "",
            "stock_name": "",
            "generated_at": "",
            "strategy_type": "",
            "strategy_type_label": "",
            "sub_type": "",
            "sub_type_label": "",
            "status": "",
            "confidence": "",
            "fundamental_score": None,
            "data_quality_status": "",
            "safety_boundary": "本报告仅供基本面研究，不构成交易建议，不包含目标价，不包含买卖建议，不包含技术面判断，不连接交易账户。",
        },
        "hero_tags": [],
        "core_conclusion": {
            "title": "",
            "summary": "",
            "supporting_points": [],
            "limiting_points": [],
            "must_track_points": [],
            "evidence_confidence_explanation": "",
        },
        "research_anchor": {
            "main_thesis": "",
            "key_conflict": "",
            "current_stage": "",
            "what_is_proven": [],
            "what_is_unproven": [],
        },
        "company_profile": {
            "main_business": "",
            "business_segments": [],
            "ownership_or_company_nature": "",
            "framework_identity": "",
            "core_business_anchor": "",
        },
        "recent_fundamental_updates": {
            "financial_update": "",
            "business_update": "",
            "policy_or_industry_update": "",
            "unavailable_news_note": "",
        },
        "business_composition_analysis": {
            "segment_table": [],
            "core_segment": "",
            "drag_segment": "",
            "growth_optional_segment": "",
            "analysis": "",
        },
        "financial_quality_diagnosis": {
            "revenue_quality": "",
            "profit_quality": "",
            "cashflow_quality": "",
            "receivables_pressure": "",
            "inventory_pressure": "",
            "contract_liabilities_interpretation": "",
            "capex_pressure": "",
            "free_cashflow_interpretation": "",
            "final_diagnosis": "",
            "diagnosis_level": "无法判断",
        },
        "financial_ratio_caveats": [
            {
                "ratio_name": "应收账款/收入",
                "caveat": "资产负债表存量除以利润表期间数，口径不同，只能作为压力线索，不能单独形成强结论。",
                "interpretation_strength": "弱",
                "required_follow_up_data": [],
            },
            {
                "ratio_name": "存货/收入",
                "caveat": "资产负债表存量除以利润表期间数，口径不同，只能作为周转压力线索。",
                "interpretation_strength": "弱",
                "required_follow_up_data": [],
            },
            {
                "ratio_name": "合同负债/收入",
                "caveat": "合同负债只能作为订单可见度 proxy，不等同于真实订单或 backlog。",
                "interpretation_strength": "弱",
                "required_follow_up_data": [],
            },
        ],
        "valuation_explanation": {
            "valuation_metrics": [],
            "valuation_interpretation": "",
            "peer_benchmark_status": "",
            "what_must_be_proven_to_justify_valuation": [],
            "cannot_determine_items": [],
        },
        "core_fundamental_question": {
            "main_question": "",
            "key_conflict": "",
            "what_would_confirm": [],
            "what_would_invalidate": [],
        },
        "industry_cycle_positioning": {
            "cycle_stage": "",
            "policy_or_demand_background": "",
            "evidence_strength": "",
            "missing_evidence": [],
        },
        "value_chain_and_business_model": {
            "upstream": "",
            "downstream": "",
            "customer_structure": "",
            "how_company_makes_money": "",
            "margin_source": "",
            "moat_claims": [],
            "unproven_moats": [],
        },
        "value_chain_map": {
            "upstream": "",
            "company_role": "",
            "downstream": "",
            "profit_source": "",
            "unproven_moats": [],
            "key_bottlenecks": [],
        },
        "quality_score_breakdown": {
            "industry_position": {"score": None, "max_score": 10, "label": "行业位置", "explanation": "", "evidence_basis": []},
            "business_quality": {"score": None, "max_score": 10, "label": "业务质量", "explanation": "", "evidence_basis": []},
            "growth_realization": {"score": None, "max_score": 10, "label": "成长兑现", "explanation": "", "evidence_basis": []},
            "financial_quality": {"score": None, "max_score": 10, "label": "财务质量", "explanation": "", "evidence_basis": []},
            "valuation_explainability": {"score": None, "max_score": 10, "label": "估值可解释性", "explanation": "", "evidence_basis": []},
            "risk_identifiability": {"score": None, "max_score": 10, "label": "风险可识别性", "explanation": "", "evidence_basis": []},
        },
        "elasticity_formula": {
            "formula_title": "",
            "formula_text": "",
            "key_variables": [],
            "interpretation": "",
            "data_limitations": [],
        },
        "fundamental_scenario_analysis": {
            "optimistic_case": {
                "scenario_name": "乐观基本面情景",
                "fundamental_assumptions": [],
                "key_variables": [],
                "impact_on_fundamentals": "",
                "evidence_strength": "",
                "evidence_needed": [],
            },
            "base_case": {
                "scenario_name": "基准基本面情景",
                "fundamental_assumptions": [],
                "key_variables": [],
                "impact_on_fundamentals": "",
                "evidence_strength": "",
                "evidence_needed": [],
            },
            "downside_case": {
                "scenario_name": "压力基本面情景",
                "fundamental_assumptions": [],
                "key_variables": [],
                "impact_on_fundamentals": "",
                "evidence_strength": "",
                "evidence_needed": [],
            },
        },
        "peer_comparison": {
            "peer_benchmark_status": "",
            "comparison_table": [],
            "interpretation": "",
            "peer_data_missing_note": "",
        },
        "risk_analysis": {
            "business_risks": [],
            "financial_risks": [],
            "industry_risks": [],
            "policy_risks": [],
            "data_gap_risks": [],
        },
        "must_track_indicators": [],
        "tracking_plan_groups": [],
        "follow_up_review_conditions": [],
        "data_quality_and_unknowns": {
            "available_data": [],
            "missing_data": [],
            "proxy_fields": [],
            "cannot_determine": [],
            "source_limitations": [],
        },
        "safety_boundary": {
            "statement": "本报告仅供基本面研究，不构成交易建议，不包含目标价，不包含买卖建议，不包含技术面判断，不连接交易账户。",
            "forbidden_actions_excluded": ["交易建议", "目标价", "买卖建议", "技术面判断", "交易账户连接"],
        },
    }
