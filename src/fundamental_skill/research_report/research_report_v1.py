# -*- coding: utf-8 -*-
"""Offline fundamental research report V1 builder.

The builder consumes already materialized artifact payloads. It does not read
environment variables, contact data providers, alter upstream artifacts, or
write anything unless the explicit writer is called.
"""

from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPORT_TYPE = "fundamental_research_report_v1"
OUTPUT_FILENAME = "fundamental_research_report_v1.json"

ALLOWED_EVIDENCE_LABELS = {
    "verified_fact",
    "auto_accepted_candidate",
    "manual_review_required",
    "unsupported_assumption",
    "coverage_caveat",
    "forward_tracking_variable",
}

FINANCIAL_FIELDS = (
    "revenue",
    "net_profit",
    "gross_margin",
    "roe",
    "operating_cashflow",
    "accounts_receivable",
    "inventory",
    "contract_liabilities",
    "capex",
)
VALUATION_FIELDS = ("pe_ttm", "pb", "market_cap")
REQUIRED_GAP_FIELDS = (
    "valuation_metrics.as_of_date",
    "business_composition.period",
    "business_composition.classification_type",
    "business_composition.revenue_ratio",
    "basic_info.main_business",
)

FORBIDDEN_INVESTMENT_ADVICE_FIELDS = {
    "buy",
    "sell",
    "hold",
    "target_price",
    "position",
    "position_size",
    "portfolio_weight",
    "portfolio_weight_pct",
    "portfolio_weight_percent",
    "trading_recommendation",
    "investment_recommendation",
    "technical_signal",
    "stop_loss",
    "take_profit",
}

_STOCK_CODE_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
_TIMESTAMP_RE = re.compile(r"^[A-Za-z0-9T_-]{1,64}$")
_BUSINESS_INDEX_RE = re.compile(r"business_composition\[\d+\]\.")
_SECRET_KEY_RE = re.compile(
    r"\b(token|key|secret|auth|credential|api[_-]?key|access[_-]?key|tushare[_-]?token)\b",
    flags=re.IGNORECASE,
)
_KEYED_SECRET_RE = re.compile(
    r"\b(token|key|secret|auth|credential|api[_-]?key|access[_-]?key|tushare[_-]?token)\b\s*[:=]\s*[^\s,;&]+",
    flags=re.IGNORECASE,
)
_BEARER_RE = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]+", flags=re.IGNORECASE)
_MCP_RE = re.compile(r"\bmcp(?:s)?://[^\s\"'<>]+|\bmcp\?[^\s\"']*", flags=re.IGNORECASE)
_DOTENV_PATH_RE = re.compile(
    r"(^|[\\/:\s\"'`=])\.env(?:\.[A-Za-z0-9_-]+)*\b",
    flags=re.IGNORECASE,
)
_TOKEN_LIKE_RE = re.compile(
    r"\b(?=[A-Za-z0-9._~+/=-]{32,}\b)"
    r"(?=[A-Za-z0-9._~+/=-]*[a-z])"
    r"(?=[A-Za-z0-9._~+/=-]*[A-Z])"
    r"(?=[A-Za-z0-9._~+/=-]*\d)"
    r"[A-Za-z0-9._~+/=-]+\b"
)
_LOCAL_SECRET_PATH_RE = re.compile(r"\b[A-Za-z]:[\\/]+Users[\\/]+|/Users/[^/\s]+", flags=re.IGNORECASE)


class ResearchReportBuildError(RuntimeError):
    """Raised when a report payload cannot be built safely."""


class ResearchReportArtifactBoundaryError(RuntimeError):
    """Raised when report output would escape the requested artifact boundary."""


class ResearchReportSecretError(RuntimeError):
    """Raised when a report payload contains secret-like data."""


def build_research_report_v1(
    *,
    code: str,
    fundamental_payloads: dict[str, Any],
    evidence_pack_payloads: dict[str, Any],
    fact_candidates: dict[str, Any] | None = None,
    review_decisions: dict[str, Any] | None = None,
    score_explainability: dict[str, Any] | None = None,
    diff_report: dict[str, Any] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build an in-memory offline fundamental research report payload."""

    normalized_code = _normalize_code(code)
    _assert_dict("fundamental_payloads", fundamental_payloads)
    _assert_dict("evidence_pack_payloads", evidence_pack_payloads)
    for optional_name, optional_payload in (
        ("fact_candidates", fact_candidates),
        ("review_decisions", review_decisions),
        ("score_explainability", score_explainability),
        ("diff_report", diff_report),
    ):
        if optional_payload is not None:
            _assert_dict(optional_name, optional_payload)

    for input_payload in (
        fundamental_payloads,
        evidence_pack_payloads,
        fact_candidates,
        review_decisions,
        score_explainability,
        diff_report,
    ):
        if input_payload is not None:
            _assert_no_secret_like_payload(input_payload)

    candidates = _candidate_list(fact_candidates)
    data_quality = _build_data_quality_assessment(
        fact_candidates=fact_candidates,
        review_decisions=review_decisions,
        score_explainability=score_explainability,
        diff_report=diff_report,
    )
    company = _build_company_fundamentals(
        code=normalized_code,
        fundamental_payloads=fundamental_payloads,
        evidence_pack_payloads=evidence_pack_payloads,
        candidates=candidates,
        data_quality=data_quality,
    )
    macro_context = _build_macro_context()
    industry_context = _build_industry_context(data_quality=data_quality)
    opportunities = _build_opportunity_analysis(company=company, data_quality=data_quality)
    risks = _build_risk_analysis(company=company, data_quality=data_quality)
    evidence_gaps = _build_evidence_gaps(data_quality=data_quality, score_explainability=score_explainability)
    rebuttal_conditions = _build_rebuttal_conditions()
    follow_up_variables = _build_follow_up_variables()
    executive_summary = _build_executive_summary(
        code=normalized_code,
        company=company,
        data_quality=data_quality,
        opportunities=opportunities,
        risks=risks,
        evidence_gaps=evidence_gaps,
    )

    payload = {
        "code": normalized_code,
        "generated_at": generated_at or _utc_now(),
        "report_type": REPORT_TYPE,
        "not_for_trading_advice": True,
        "data_quality_assessment": data_quality,
        "executive_summary": executive_summary,
        "macro_context": macro_context,
        "industry_context": industry_context,
        "company_fundamentals": company,
        "opportunity_analysis": opportunities,
        "risk_analysis": risks,
        "evidence_gaps": evidence_gaps,
        "rebuttal_conditions": rebuttal_conditions,
        "follow_up_variables": follow_up_variables,
        "source_artifact_refs": _build_source_artifact_refs(
            fundamental_payloads=fundamental_payloads,
            evidence_pack_payloads=evidence_pack_payloads,
            fact_candidates=fact_candidates,
            review_decisions=review_decisions,
            score_explainability=score_explainability,
            diff_report=diff_report,
        ),
    }
    _assert_report_payload(payload)
    return payload


def write_research_report_v1(payload: dict[str, Any], output_root: Path, timestamp: str) -> Path:
    """Write ``fundamental_research_report_v1.json`` under ``output_root``."""

    _assert_report_payload(payload)
    _assert_no_secret_like_payload(json.dumps(payload, ensure_ascii=False, sort_keys=True))

    code = _normalize_code(str(payload.get("code", "")))
    if not _TIMESTAMP_RE.fullmatch(str(timestamp)) or ".." in str(timestamp):
        raise ResearchReportArtifactBoundaryError("timestamp contains unsupported path characters")

    root = Path(output_root)
    root_resolved = root.resolve(strict=False)
    report_path = root / str(timestamp) / code / OUTPUT_FILENAME
    report_resolved = report_path.resolve(strict=False)
    try:
        report_resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ResearchReportArtifactBoundaryError("research report path escapes output root") from exc
    if report_resolved.name != OUTPUT_FILENAME:
        raise ResearchReportArtifactBoundaryError("writer may only write fundamental_research_report_v1.json")

    report_resolved.parent.mkdir(parents=True, exist_ok=True)
    report_resolved.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return report_resolved


def _build_data_quality_assessment(
    *,
    fact_candidates: dict[str, Any] | None,
    review_decisions: dict[str, Any] | None,
    score_explainability: dict[str, Any] | None,
    diff_report: dict[str, Any] | None,
) -> dict[str, Any]:
    auto_core = _auto_accepted_core_fields(fact_candidates)
    review_queue = _manual_review_queue(fact_candidates)
    decisions = _decision_list(review_decisions)
    score_summary = _dict_or_empty(_get(score_explainability, "score_summary"))
    confidence_summary = _dict_or_empty(_get(score_explainability, "confidence_summary"))
    diff_summary = _dict_or_empty(_get(diff_report, "summary"))

    auto_core_items = [
        {
            "field_path": str(item.get("field_path")),
            "value": item.get("value"),
            "report_period": item.get("report_period"),
            "as_of_date": item.get("as_of_date"),
            "source_provider": item.get("source_provider"),
            "canonical_unit": item.get("canonical_unit"),
            "evidence_label": "auto_accepted_candidate",
            "caveat": "Auto acceptance is candidate-level evidence only and is not reviewed ground truth.",
        }
        for item in auto_core
        if isinstance(item, dict) and item.get("field_path")
    ]

    review_items = [
        {
            "field_path": _simple_field_path(str(item.get("field_path") or "")),
            "issue_type": item.get("issue_type") or item.get("queue_item_type"),
            "priority": item.get("priority"),
            "candidate_count": item.get("candidate_count"),
            "reason": item.get("reason"),
            "evidence_label": _queue_label(item),
            "caveat": "Manual-review queue items limit conclusion strength until source, period, unit, mapping, or provider coverage is resolved.",
        }
        for item in review_queue
        if isinstance(item, dict)
    ]

    review_decision_items = [
        {
            "field_path": _simple_field_path(str(decision.get("field_path") or "")),
            "queue_item_type": decision.get("queue_item_type"),
            "decision_outcome": decision.get("decision_outcome"),
            "eligible_for_future_promotion": bool(decision.get("eligible_for_future_promotion")),
            "fixture_write_allowed": bool(decision.get("fixture_write_allowed")),
            "decision_reason": decision.get("decision_reason"),
            "follow_up_type": decision.get("follow_up_type"),
            "evidence_label": _decision_label(decision),
            "caveat": "Review decisions document workflow status only; future promotion eligibility is not verified fact.",
        }
        for decision in decisions
        if isinstance(decision, dict)
    ]

    valuation_status = _valuation_as_of_date_status(
        auto_core_items=auto_core_items,
        review_items=review_items,
        review_decisions=review_decision_items,
    )
    business_status = _business_composition_status(
        fact_candidates=fact_candidates,
        review_items=review_items,
        review_decisions=review_decision_items,
    )
    main_business_status = _main_business_status(
        review_items=review_items,
        review_decisions=review_decision_items,
    )
    score_status = _score_confidence_status(
        score_summary=score_summary,
        confidence_summary=confidence_summary,
        score_explainability=score_explainability,
    )
    diff_status = _diff_report_status(diff_summary=diff_summary)

    impact = [
        _judgement(
            title="financial_and_valuation_candidate_strength",
            analysis=(
                "Financial and valuation fields can support a research discussion at candidate level, "
                "but they do not permit a strong company conclusion without reviewed business exposure and cash-flow context."
            ),
            evidence_label="auto_accepted_candidate" if auto_core_items else "manual_review_required",
            supporting_fields=[item["field_path"] for item in auto_core_items],
            caveats=["Auto-accepted candidate status is not reviewed ground truth."],
        ),
        _judgement(
            title="business_exposure_limits",
            analysis=(
                "main_business and business_composition caveats prevent the report from treating grid-equipment "
                "or digital-grid exposure as fully reviewed company realization, and they limit conclusion strength."
            ),
            evidence_label="manual_review_required",
            supporting_fields=[
                "basic_info.main_business",
                "business_composition.period",
                "business_composition.classification_type",
                "business_composition.revenue_ratio",
            ],
            caveats=["Industry narrative is a hypothesis until company-level evidence is reviewed."],
        ),
        _judgement(
            title="provider_comparison_caveat",
            analysis=(
                "Score or confidence differences from provider comparison remain review-facing caveats and do not alter "
                "scores, provider precedence, or reported fact status."
            ),
            evidence_label="coverage_caveat",
            supporting_fields=["fundamental.fundamental_score", "confidence"],
            caveats=_score_caveat_texts(score_explainability),
        ),
    ]

    return {
        "auto_accepted_core_fields": auto_core_items,
        "manual_review_required_fields": review_items,
        "candidate_review_decisions": review_decision_items,
        "valuation_as_of_date_status": valuation_status,
        "business_composition_status": business_status,
        "main_business_status": main_business_status,
        "score_confidence_explainability_status": score_status,
        "diff_report_status": diff_status,
        "impact_on_research_conclusion": impact,
        "reporting_boundary": _judgement(
            title="research_report_boundary",
            analysis=(
                "The report uses local artifacts only, does not promote fixtures, does not merge providers, "
                "and does not change provider precedence."
            ),
            evidence_label="coverage_caveat",
            supporting_fields=[],
            caveats=["Runtime behavior is limited to in-memory aggregation unless the explicit writer is called."],
        ),
    }


def _build_company_fundamentals(
    *,
    code: str,
    fundamental_payloads: dict[str, Any],
    evidence_pack_payloads: dict[str, Any],
    candidates: list[dict[str, Any]],
    data_quality: dict[str, Any],
) -> dict[str, Any]:
    stock_view = _stock_view(fundamental_payloads, evidence_pack_payloads)
    financial_metrics = [
        _metric_item(
            field_path=f"financial_metrics.{field}",
            candidates=candidates,
            evidence_pack_payloads=evidence_pack_payloads,
            fallback_block="financial_metrics",
            fallback_field=field,
        )
        for field in FINANCIAL_FIELDS
    ]
    valuation_metrics = [
        _metric_item(
            field_path=f"valuation_metrics.{field}",
            candidates=candidates,
            evidence_pack_payloads=evidence_pack_payloads,
            fallback_block="valuation_metrics",
            fallback_field=field,
        )
        for field in VALUATION_FIELDS
    ]
    business_rows = _business_composition_preview(evidence_pack_payloads)
    trusted_fields = [
        _judgement(
            title=item["field_path"],
            analysis=(
                f"{item['field_path']} is usable as an auto-accepted candidate for V1 report discussion, "
                "not as reviewed ground truth."
            ),
            evidence_label="auto_accepted_candidate",
            supporting_fields=[item["field_path"]],
            caveats=[item.get("caveat")],
        )
        for item in data_quality.get("auto_accepted_core_fields", [])
        if isinstance(item, dict)
    ]
    review_fields = [
        _judgement(
            title=str(item.get("field_path") or "manual_review_required"),
            analysis=str(item.get("reason") or item.get("caveat") or "Field requires manual review before strong use."),
            evidence_label=str(item.get("evidence_label") or "manual_review_required"),
            supporting_fields=[str(item.get("field_path"))] if item.get("field_path") else [],
            caveats=[item.get("caveat")],
        )
        for item in data_quality.get("manual_review_required_fields", [])
        if isinstance(item, dict)
    ]

    return {
        "profile": _judgement(
            title="stable_growth_grid_equipment_profile",
            analysis=(
                f"{code} is treated as a stable_growth / grid-equipment research sample in the current local artifacts; "
                "the exact company exposure remains constrained by main_business and business-composition review gaps."
            ),
            evidence_label="manual_review_required",
            supporting_fields=["strategy_type", "industry", "basic_info.main_business", "business_composition"],
            caveats=[
                "stable_growth classification is an artifact-level research lens, not a trading recommendation.",
                "Grid-equipment exposure must be tied to reviewed company disclosures before being treated as realized.",
            ],
        ),
        "stock": stock_view,
        "financial_metrics": financial_metrics,
        "valuation_metrics": valuation_metrics,
        "business_composition": {
            "status": data_quality["business_composition_status"],
            "available_segments_preview": business_rows,
            "interpretation": _judgement(
                title="business_composition_is_caveated",
                analysis=(
                    "Available segment rows can orient research, but period, classification type, ratio denominator, "
                    "mapping, and provider coverage caveats keep them out of reviewed fact status."
                ),
                evidence_label="manual_review_required",
                supporting_fields=["business_composition.period", "business_composition.classification_type", "business_composition.revenue_ratio"],
                caveats=["Do not use the largest segment hint as canonical main_business."],
            ),
        },
        "trusted_fields": trusted_fields,
        "fields_needing_review": review_fields,
    }


def _build_macro_context() -> dict[str, Any]:
    paths = [
        _judgement(
            title="interest_rate_environment",
            analysis=(
                "Interest-rate changes affect discount rates, valuation sensitivity, financing costs, and the market's "
                "tolerance for long-duration grid infrastructure expectations."
            ),
            evidence_label="forward_tracking_variable",
            supporting_fields=["rates", "discount_rate", "financing_cost"],
        ),
        _judgement(
            title="credit_environment",
            analysis=(
                "Credit conditions can influence grid customer payment cadence, receivables quality, and capital-project "
                "execution pace."
            ),
            evidence_label="forward_tracking_variable",
            supporting_fields=["credit_conditions", "accounts_receivable", "operating_cashflow"],
        ),
        _judgement(
            title="fiscal_rhythm",
            analysis=(
                "Fiscal and public-infrastructure spending rhythm matters through project approval, delivery, and settlement timing."
            ),
            evidence_label="forward_tracking_variable",
            supporting_fields=["public_infrastructure_spending", "project_settlement"],
        ),
        _judgement(
            title="grid_investment_cycle",
            analysis=(
                "Power-grid investment is a demand-path variable for grid equipment, but V1 does not forecast capex or convert "
                "policy support into company revenue."
            ),
            evidence_label="forward_tracking_variable",
            supporting_fields=["grid_investment_amount", "state_grid_tenders", "china_southern_power_grid_tenders"],
        ),
        _judgement(
            title="new_power_system_policy_cadence",
            analysis=(
                "New power system, digital grid, UHV, and distribution-grid policy cadence should be tracked as mechanisms, "
                "not as proof of company realization."
            ),
            evidence_label="forward_tracking_variable",
            supporting_fields=["digital_grid_policy", "uhv_project_cadence", "distribution_grid_upgrade"],
        ),
    ]
    return {
        "overview": _judgement(
            title="macro_mechanism_only",
            analysis="Macro context is expressed as transmission paths and tracking variables only; V1 makes no macro forecast.",
            evidence_label="forward_tracking_variable",
            supporting_fields=["macro_tracking_variables"],
        ),
        "transmission_paths": paths,
        "follow_up_variables": [
            _tracking_variable("interest_rate_environment", "Track rate moves that change valuation sensitivity."),
            _tracking_variable("credit_environment", "Track financing and collection conditions that may affect receivables."),
            _tracking_variable("fiscal_rhythm", "Track infrastructure spending rhythm and project settlement cadence."),
            _tracking_variable("grid_investment_amount", "Track grid capex as an industry demand-path variable."),
            _tracking_variable("new_power_system_policy_cadence", "Track digital grid, UHV, and distribution-grid policy conversion."),
        ],
    }


def _build_industry_context(*, data_quality: dict[str, Any]) -> dict[str, Any]:
    contexts = [
        _judgement(
            title="grid_equipment_context",
            analysis=(
                "The relevant industry frame for 600406 is grid equipment and electric-power automation; this frame still "
                "needs company-level confirmation through reviewed main_business and business-composition evidence."
            ),
            evidence_label="manual_review_required",
            supporting_fields=["industry", "basic_info.main_business", "business_composition"],
            caveats=["Do not treat industry identity as reviewed company realization."],
        ),
        _judgement(
            title="state_grid_and_csg_tenders",
            analysis=(
                "State Grid and China Southern Power Grid tender rhythm is a demand-path monitor for orders and revenue conversion."
            ),
            evidence_label="forward_tracking_variable",
            supporting_fields=["state_grid_tenders", "china_southern_power_grid_tenders"],
        ),
        _judgement(
            title="uhv_distribution_grid_digital_grid",
            analysis=(
                "UHV, distribution-grid upgrades, and digital-grid programs can frame opportunity hypotheses only when linked "
                "to company orders, revenue, margins, cash flow, contract liabilities, or reviewed segment evidence."
            ),
            evidence_label="unsupported_assumption",
            supporting_fields=["uhv", "distribution_grid", "digital_grid"],
            caveats=["Industry prosperity is not company realization."],
        ),
        _judgement(
            title="power_automation_relay_dispatching_info_communication",
            analysis=(
                "Power automation, relay protection, dispatching systems, and power information communication are relevant "
                "exposure hypotheses, but official text and reviewed composition remain required."
            ),
            evidence_label="manual_review_required",
            supporting_fields=["basic_info.main_business", "business_composition.segment_name"],
            caveats=[data_quality["main_business_status"].get("caveat")],
        ),
        _judgement(
            title="delivery_settlement_receivables_cashflow",
            analysis=(
                "Project delivery and settlement cadence can create accounts-receivable and operating-cash-flow pressure; "
                "these variables must be tracked against revenue and contract liabilities."
            ),
            evidence_label="forward_tracking_variable",
            supporting_fields=["accounts_receivable", "operating_cashflow", "contract_liabilities"],
        ),
    ]
    return {
        "overview": _judgement(
            title="industry_to_company_conversion_boundary",
            analysis=(
                "Industry logic is useful for hypotheses, but V1 requires company-level evidence before writing conversion "
                "into orders, revenue, margin, or cash-flow realization."
            ),
            evidence_label="unsupported_assumption",
            supporting_fields=["orders", "revenue", "gross_margin", "operating_cashflow"],
        ),
        "industry_logic": contexts,
        "evidence_required_for_conversion": [
            _tracking_variable("company_tender_wins", "Track tenders and wins before asserting order conversion."),
            _tracking_variable("segment_revenue_evidence", "Track reviewed segment revenue and ratio evidence."),
            _tracking_variable("cash_collection_quality", "Track receivables and operating cash flow as delivery converts to cash."),
        ],
    }


def _build_opportunity_analysis(*, company: dict[str, Any], data_quality: dict[str, Any]) -> list[dict[str, Any]]:
    del company
    return [
        _judgement(
            title="grid_investment_cycle",
            analysis=(
                "Grid investment can support an opportunity path only if tender, order, revenue, margin, cash-flow, "
                "contract-liability, or segment evidence confirms company conversion."
            ),
            evidence_label="forward_tracking_variable",
            supporting_fields=["grid_investment_amount", "state_grid_tenders", "china_southern_power_grid_tenders"],
            caveats=["No company realization is inferred in V1."],
            follow_up_variables=["grid_investment_amount", "state_grid_tenders"],
        ),
        _judgement(
            title="digital_grid",
            analysis=(
                "Digital-grid demand is an opportunity hypothesis for a grid-equipment sample; current evidence does not "
                "prove company-level conversion without reviewed product-line, order, or segment data."
            ),
            evidence_label="unsupported_assumption",
            supporting_fields=["digital_grid_policy", "business_composition"],
            caveats=["Industry narrative remains an unsupported assumption until company evidence is reviewed."],
            follow_up_variables=["digital_grid_policy_and_tender_conversion"],
        ),
        _judgement(
            title="uhv_and_distribution_grid",
            analysis=(
                "UHV and distribution-grid construction are relevant demand-path variables, not automatic revenue evidence."
            ),
            evidence_label="forward_tracking_variable",
            supporting_fields=["uhv_project_cadence", "distribution_grid_project_cadence"],
            follow_up_variables=["uhv_distribution_grid_project_cadence"],
        ),
        _judgement(
            title="power_automation_and_relay_protection",
            analysis=(
                "Power automation, relay protection, dispatching, and information-communication exposure may be relevant, "
                "but official main_business and reviewed composition support are still required."
            ),
            evidence_label="manual_review_required",
            supporting_fields=["basic_info.main_business", "business_composition.classification_type"],
            caveats=[data_quality["main_business_status"].get("caveat")],
            follow_up_variables=["main_business_official_source", "business_composition_review"],
        ),
        _judgement(
            title="stable_operating_quality_candidate",
            analysis=(
                "Auto-accepted financial candidates provide inputs for testing stable operating quality, but do not by "
                "themselves prove durable quality or remove evidence caveats."
            ),
            evidence_label="auto_accepted_candidate",
            supporting_fields=[
                "financial_metrics.revenue",
                "financial_metrics.net_profit",
                "financial_metrics.gross_margin",
                "financial_metrics.roe",
                "financial_metrics.operating_cashflow",
            ],
            caveats=["Receivables, cash flow, contract liabilities, margin, ROE, and capex need ongoing review."],
            follow_up_variables=["operating_cashflow", "accounts_receivable_turnover", "contract_liabilities", "gross_margin"],
        ),
    ]


def _build_risk_analysis(*, company: dict[str, Any], data_quality: dict[str, Any]) -> list[dict[str, Any]]:
    del company
    return [
        _judgement(
            title="tender_cadence_risk",
            analysis="State Grid or China Southern Power Grid tender rhythm could weaken the demand path.",
            evidence_label="forward_tracking_variable",
            supporting_fields=["state_grid_tenders", "china_southern_power_grid_tenders"],
        ),
        _judgement(
            title="order_realization_risk",
            analysis="Industry demand may fail to convert into company orders, revenue, or cash collection.",
            evidence_label="unsupported_assumption",
            supporting_fields=["orders", "revenue", "operating_cashflow"],
            caveats=["No order realization is assumed in V1."],
        ),
        _judgement(
            title="receivables_and_cashflow_risk",
            analysis="Accounts receivable and operating cash flow can diverge from reported revenue during project delivery and settlement.",
            evidence_label="auto_accepted_candidate",
            supporting_fields=["financial_metrics.accounts_receivable", "financial_metrics.operating_cashflow"],
        ),
        _judgement(
            title="gross_margin_pressure",
            analysis="Gross margin compression would weaken the stable-growth quality reading.",
            evidence_label="forward_tracking_variable",
            supporting_fields=["financial_metrics.gross_margin"],
        ),
        _judgement(
            title="contract_liabilities_visibility_risk",
            analysis="Weakening contract liabilities could reduce backlog-style visibility and future revenue support.",
            evidence_label="forward_tracking_variable",
            supporting_fields=["financial_metrics.contract_liabilities"],
        ),
        _judgement(
            title="business_composition_scope_risk",
            analysis="Unclear business-composition period, classification type, and revenue-ratio denominator limit segment conclusions.",
            evidence_label="manual_review_required",
            supporting_fields=["business_composition.period", "business_composition.classification_type", "business_composition.revenue_ratio"],
            caveats=[data_quality["business_composition_status"].get("summary")],
        ),
        _judgement(
            title="valuation_date_risk",
            analysis="PE, PB, and market cap need same-date refresh; stale or mismatched dates weaken valuation interpretation.",
            evidence_label=data_quality["valuation_as_of_date_status"].get("evidence_label", "manual_review_required"),
            supporting_fields=["valuation_metrics.as_of_date", "valuation_metrics.pe_ttm", "valuation_metrics.pb", "valuation_metrics.market_cap"],
            caveats=[data_quality["valuation_as_of_date_status"].get("caveat")],
        ),
        _judgement(
            title="data_quality_risk",
            analysis="Candidate, review-decision, score-drift, and provider-coverage caveats constrain conclusion strength.",
            evidence_label="coverage_caveat",
            supporting_fields=["fact_candidates", "candidate_review_decisions", "score_confidence_explainability", "diff_report"],
        ),
    ]


def _build_evidence_gaps(
    *,
    data_quality: dict[str, Any],
    score_explainability: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    valuation = data_quality["valuation_as_of_date_status"]
    business = data_quality["business_composition_status"]
    main_business = data_quality["main_business_status"]
    gaps = [
        _gap_item(
            field_path="valuation_metrics.as_of_date",
            status=valuation.get("status"),
            analysis=valuation.get("analysis"),
            evidence_label=valuation.get("evidence_label", "manual_review_required"),
            caveat=valuation.get("caveat"),
        ),
        _gap_item(
            field_path="business_composition.period",
            status=business["period_status"].get("status"),
            analysis=business["period_status"].get("analysis"),
            evidence_label="manual_review_required",
            caveat=business["period_status"].get("caveat"),
        ),
        _gap_item(
            field_path="business_composition.classification_type",
            status=business["classification_type_status"].get("status"),
            analysis=business["classification_type_status"].get("analysis"),
            evidence_label="manual_review_required",
            caveat=business["classification_type_status"].get("caveat"),
        ),
        _gap_item(
            field_path="business_composition.revenue_ratio",
            status=business["revenue_ratio_status"].get("status"),
            analysis=business["revenue_ratio_status"].get("analysis"),
            evidence_label="manual_review_required",
            caveat=business["revenue_ratio_status"].get("caveat"),
        ),
        _gap_item(
            field_path="basic_info.main_business",
            status=main_business.get("status"),
            analysis=main_business.get("analysis"),
            evidence_label=main_business.get("evidence_label", "manual_review_required"),
            caveat=main_business.get("caveat"),
        ),
    ]
    if score_explainability:
        gaps.append(
            _gap_item(
                field_path="score_confidence_explainability.score_drift",
                status="review_facing_caveat",
                analysis=(
                    "Provider score drift or business-quality caveats remain explainability-only and do not recalculate scores "
                    "or change fact status."
                ),
                evidence_label="coverage_caveat",
                caveat="Score/confidence drift caveats must stay visible in the research report.",
            )
        )
    return gaps


def _build_rebuttal_conditions() -> list[dict[str, Any]]:
    return [
        _condition("revenue_growth_slowdown", "Revenue growth slows materially versus the current candidate trend.", ["financial_metrics.revenue"]),
        _condition("operating_cashflow_deterioration", "Operating cash flow deteriorates or remains weak relative to profit.", ["financial_metrics.operating_cashflow"]),
        _condition("receivables_grow_faster_than_revenue", "Accounts receivable grows faster than revenue or collection quality weakens.", ["financial_metrics.accounts_receivable", "financial_metrics.revenue"]),
        _condition("contract_liabilities_decline", "Contract liabilities decline or fail to support future order visibility.", ["financial_metrics.contract_liabilities"]),
        _condition("gross_margin_compression", "Gross margin compresses across reporting periods.", ["financial_metrics.gross_margin"]),
        _condition("grid_tender_rhythm_weakens", "State Grid or China Southern Power Grid tender rhythm weakens.", ["state_grid_tenders", "china_southern_power_grid_tenders"]),
        _condition("project_cadence_falls_short", "UHV, distribution-grid, or digital-grid project cadence falls short.", ["uhv_project_cadence", "distribution_grid_project_cadence", "digital_grid_policy_conversion"]),
        _condition("business_composition_does_not_support_exposure", "Reviewed business composition does not support assumed grid-equipment exposure.", ["business_composition"]),
        _condition("valuation_date_stale_or_mismatched", "Valuation metrics become stale or PE/PB/market_cap dates no longer match.", ["valuation_metrics.as_of_date"]),
    ]


def _build_follow_up_variables() -> list[dict[str, Any]]:
    return [
        _tracking_variable("grid_investment_amount", "Track the grid investment amount as an industry demand-path variable."),
        _tracking_variable("state_grid_and_csg_tenders", "Track State Grid and China Southern Power Grid tender data."),
        _tracking_variable("uhv_distribution_grid_project_cadence", "Track UHV and distribution-grid project rhythm."),
        _tracking_variable("digital_grid_policy_and_tender_conversion", "Track digital-grid policy progress and tender conversion."),
        _tracking_variable("accounts_receivable_turnover", "Track receivables turnover and collection quality."),
        _tracking_variable("operating_cashflow", "Track operating cash flow against profit and revenue."),
        _tracking_variable("contract_liabilities", "Track contract liabilities as an order-visibility proxy, not proof."),
        _tracking_variable("gross_margin", "Track gross margin for pricing, cost, and product-mix pressure."),
        _tracking_variable("business_composition", "Track period, classification type, segment revenue, and ratio denominator."),
        _tracking_variable("valuation_as_of_date", "Track valuation date freshness."),
        _tracking_variable("pe_pb_market_cap_same_date_refresh", "Refresh PE, PB, and market cap on the same date."),
    ]


def _build_executive_summary(
    *,
    code: str,
    company: dict[str, Any],
    data_quality: dict[str, Any],
    opportunities: list[dict[str, Any]],
    risks: list[dict[str, Any]],
    evidence_gaps: list[dict[str, Any]],
) -> dict[str, Any]:
    del company
    return {
        "one_sentence_fundamental_judgement": _judgement(
            title="evidence_constrained_fundamental_judgement",
            analysis=(
                f"{code} currently reads as a stable_growth / grid-equipment research case with usable financial and "
                "valuation candidate evidence, but business exposure, segment mix, and industry-to-company conversion "
                "remain review-constrained."
            ),
            evidence_label="manual_review_required",
            supporting_fields=["financial_metrics", "valuation_metrics", "basic_info.main_business", "business_composition"],
            caveats=["This is research context only and is not trading advice."],
        ),
        "evidence_strength": _judgement(
            title="mixed_evidence_strength",
            analysis=(
                "Evidence strength is moderate for candidate-level financial and valuation fields, weak for reviewed "
                "main-business and business-composition proof, and caveated by provider score drift."
            ),
            evidence_label="coverage_caveat",
            supporting_fields=["auto_accepted_core_fields", "manual_review_priority_queue", "score_confidence_explainability"],
        ),
        "primary_opportunity": opportunities[0],
        "primary_risk": risks[2],
        "largest_evidence_gap": evidence_gaps[4],
        "data_quality_state": _judgement(
            title="candidate_level_not_ground_truth",
            analysis=(
                "The report can discuss financial and valuation candidates, but main_business, composition period/type/ratio, "
                "and score-drift caveats limit conclusion strength."
            ),
            evidence_label="coverage_caveat",
            supporting_fields=[
                "valuation_metrics.as_of_date",
                "business_composition.period",
                "business_composition.classification_type",
                "business_composition.revenue_ratio",
                "basic_info.main_business",
            ],
            caveats=[
                data_quality["valuation_as_of_date_status"].get("caveat"),
                data_quality["business_composition_status"].get("summary"),
                data_quality["main_business_status"].get("caveat"),
            ],
        ),
    }


def _metric_item(
    *,
    field_path: str,
    candidates: list[dict[str, Any]],
    evidence_pack_payloads: dict[str, Any],
    fallback_block: str,
    fallback_field: str,
) -> dict[str, Any]:
    candidate = _best_candidate(candidates, field_path)
    if candidate:
        label = "auto_accepted_candidate" if candidate.get("review_status") == "auto_accepted" else "manual_review_required"
        return {
            "field_path": field_path,
            "value": candidate.get("value"),
            "display_value": _display_value(candidate.get("value"), candidate.get("canonical_unit")),
            "report_period": candidate.get("report_period"),
            "as_of_date": candidate.get("as_of_date"),
            "canonical_unit": candidate.get("canonical_unit"),
            "source_provider": candidate.get("source_provider"),
            "evidence_label": label,
            "analysis": _metric_analysis(field_path, label),
            "caveats": _compact_list([candidate.get("manual_review_note"), "Candidate-level evidence only; not reviewed ground truth."]),
        }
    fallback = _fallback_metric(evidence_pack_payloads, fallback_block, fallback_field)
    return {
        "field_path": field_path,
        "value": fallback.get("value"),
        "display_value": fallback.get("display_value"),
        "report_period": fallback.get("period"),
        "as_of_date": fallback.get("as_of_date"),
        "canonical_unit": fallback.get("unit"),
        "source_provider": fallback.get("provider"),
        "evidence_label": "manual_review_required" if fallback else "coverage_caveat",
        "analysis": _metric_analysis(field_path, "manual_review_required" if fallback else "coverage_caveat"),
        "caveats": ["Fallback evidence-pack value requires candidate or reviewed-source confirmation."],
    }


def _metric_analysis(field_path: str, label: str) -> str:
    if label == "auto_accepted_candidate":
        return f"{field_path} is available as an auto-accepted candidate and can inform, but not prove, the research view."
    if label == "manual_review_required":
        return f"{field_path} requires review before it can support a strong conclusion."
    return f"{field_path} has incomplete coverage in the provided artifacts."


def _valuation_as_of_date_status(
    *,
    auto_core_items: list[dict[str, Any]],
    review_items: list[dict[str, Any]],
    review_decisions: list[dict[str, Any]],
) -> dict[str, Any]:
    valuation_dates = {
        item.get("as_of_date")
        for item in auto_core_items
        if str(item.get("field_path")) in {"valuation_metrics.pe_ttm", "valuation_metrics.pb", "valuation_metrics.market_cap"}
        and item.get("as_of_date")
    }
    decision = _first_by_field(review_decisions, "valuation_metrics.as_of_date")
    queue_item = _first_by_field(review_items, "valuation_metrics.as_of_date")
    if len(valuation_dates) == 1:
        as_of_date = next(iter(valuation_dates))
        return {
            "field_path": "valuation_metrics.as_of_date",
            "status": "same_date_candidate_metadata_available",
            "as_of_date": as_of_date,
            "analysis": "PE, PB, and market cap expose same-date candidate metadata.",
            "evidence_label": "auto_accepted_candidate",
            "review_decision_outcome": decision.get("decision_outcome") if decision else None,
            "queue_issue_type": queue_item.get("issue_type") if queue_item else None,
            "caveat": "Same-date metadata is candidate-level support only; review decisions do not promote fixtures or verified facts.",
        }
    return {
        "field_path": "valuation_metrics.as_of_date",
        "status": "missing_or_mismatched",
        "as_of_date": None,
        "analysis": "Valuation as_of_date is missing, mixed, or not explicit enough for strong valuation interpretation.",
        "evidence_label": "manual_review_required",
        "review_decision_outcome": decision.get("decision_outcome") if decision else None,
        "queue_issue_type": queue_item.get("issue_type") if queue_item else None,
        "caveat": "PE, PB, and market cap should be refreshed on the same date.",
    }


def _business_composition_status(
    *,
    fact_candidates: dict[str, Any] | None,
    review_items: list[dict[str, Any]],
    review_decisions: list[dict[str, Any]],
) -> dict[str, Any]:
    summary = _dict_or_empty(_get(fact_candidates, "business_composition_summary"))
    period_item = _first_by_field(review_items, "business_composition.period")
    class_item = _first_by_field(review_items, "business_composition.classification_type")
    ratio_item = _first_by_field(review_items, "business_composition.revenue_ratio")
    period_decision = _first_by_field(review_decisions, "business_composition.period")
    class_decision = _first_by_field(review_decisions, "business_composition.classification_type")
    ratio_decision = _first_by_field(review_decisions, "business_composition.revenue_ratio")

    return {
        "summary": (
            "Business composition remains caveated by period alignment, classification type, revenue-ratio denominator, "
            "mapping, and provider coverage."
        ),
        "evidence_label": "manual_review_required",
        "candidate_count": summary.get("candidate_count"),
        "providers_present": summary.get("providers_present", []),
        "periods_observed": summary.get("periods_observed", []),
        "classification_type_coverage": summary.get("classification_type_coverage"),
        "revenue_ratio_coverage": summary.get("revenue_ratio_coverage"),
        "gross_margin_coverage": summary.get("gross_margin_coverage"),
        "mapping_missing_count": summary.get("mapping_missing_count"),
        "period_mismatch_count": summary.get("period_mismatch_count"),
        "provider_missing_count": summary.get("provider_missing_count"),
        "period_status": _composition_field_status(
            "business_composition.period",
            period_item,
            period_decision,
            "Composition rows must share period and group semantics before segment conclusions are strong.",
        ),
        "classification_type_status": _composition_field_status(
            "business_composition.classification_type",
            class_item,
            class_decision,
            "Classification type must be explicit before product, region, or industry rows are interpreted.",
        ),
        "revenue_ratio_status": _composition_field_status(
            "business_composition.revenue_ratio",
            ratio_item,
            ratio_decision,
            "Revenue-ratio denominator scope must be explicit and same-group before ratio interpretation.",
        ),
        "recommended_next_action": summary.get("recommended_next_action"),
    }


def _composition_field_status(
    field_path: str,
    queue_item: dict[str, Any] | None,
    decision: dict[str, Any] | None,
    analysis: str,
) -> dict[str, Any]:
    return {
        "field_path": field_path,
        "status": "manual_review_required",
        "analysis": analysis,
        "evidence_label": "manual_review_required",
        "queue_issue_type": queue_item.get("issue_type") if queue_item else None,
        "decision_outcome": decision.get("decision_outcome") if decision else None,
        "caveat": "Do not auto-accept mixed or provider-specific segment rows in V1.",
    }


def _main_business_status(
    *,
    review_items: list[dict[str, Any]],
    review_decisions: list[dict[str, Any]],
) -> dict[str, Any]:
    queue_item = _first_by_field(review_items, "basic_info.main_business")
    decision = _first_by_field(review_decisions, "basic_info.main_business")
    return {
        "field_path": "basic_info.main_business",
        "status": "official_source_gap",
        "analysis": "main_business needs official-source support before it can anchor company exposure.",
        "evidence_label": "manual_review_required" if queue_item or decision else "coverage_caveat",
        "queue_issue_type": queue_item.get("issue_type") if queue_item else None,
        "decision_outcome": decision.get("decision_outcome") if decision else None,
        "follow_up_type": decision.get("follow_up_type") if decision else None,
        "caveat": "Do not treat AkShare-only text or the largest segment hint as reviewed main_business.",
    }


def _score_confidence_status(
    *,
    score_summary: dict[str, Any],
    confidence_summary: dict[str, Any],
    score_explainability: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "score_summary": score_summary,
        "confidence_summary": confidence_summary,
        "provider_caveats": _labelled_caveats(_get(score_explainability, "provider_caveats")),
        "derived_hints": _labelled_caveats(_get(score_explainability, "derived_hints")),
        "narrative_hints": _labelled_caveats(_get(score_explainability, "narrative_hints")),
        "limitations": _get(score_explainability, "explainability_limitations") or [],
        "evidence_label": "coverage_caveat",
        "analysis": "Score and confidence explainability is read-only context and does not recalculate or promote facts.",
    }


def _diff_report_status(*, diff_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "summary": diff_summary,
        "blocker_count": diff_summary.get("blocker_count"),
        "review_required_count": diff_summary.get("review_required_count"),
        "category_counts": diff_summary.get("category_counts"),
        "evidence_label": "coverage_caveat",
        "analysis": "Provider diff caveats remain visible and do not trigger primary-provider changes or automatic merges.",
    }


def _labelled_caveats(value: Any) -> list[dict[str, Any]]:
    caveats = []
    for item in _as_list(value):
        if not isinstance(item, dict):
            continue
        caveats.append(
            {
                "code": item.get("code") or item.get("field") or item.get("scope"),
                "field": item.get("field"),
                "message": item.get("message") or item.get("note") or item.get("reason"),
                "derived": item.get("derived"),
                "not_for_scoring": item.get("not_for_scoring"),
                "evidence_label": "coverage_caveat",
            }
        )
    return caveats


def _stock_view(
    fundamental_payloads: dict[str, Any],
    evidence_pack_payloads: dict[str, Any],
) -> dict[str, Any]:
    payload = _first_payload(fundamental_payloads) or _first_payload(evidence_pack_payloads) or {}
    stock = _dict_or_empty(payload.get("stock"))
    return {
        "stock_code": payload.get("stock_code") or stock.get("code"),
        "stock_name": payload.get("stock_name") or stock.get("name"),
        "strategy_type": payload.get("strategy_type") or stock.get("strategy_type"),
        "status": payload.get("status") or stock.get("status"),
        "confidence": payload.get("confidence") or stock.get("confidence"),
        "fundamental_score": payload.get("fundamental_score") or stock.get("fundamental_score"),
        "evidence_label": "coverage_caveat",
        "caveat": "Stock profile fields come from local artifacts and are not fixture-promoted by the report builder.",
    }


def _business_composition_preview(evidence_pack_payloads: dict[str, Any], limit: int = 5) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for provider, payload in evidence_pack_payloads.items():
        for row in _as_list(_get(payload, "business_composition")):
            if not isinstance(row, dict):
                continue
            rows.append(
                {
                    "period": row.get("period"),
                    "classification_type": row.get("classification_type"),
                    "segment_name": row.get("segment_name"),
                    "revenue": row.get("revenue"),
                    "revenue_ratio": _value_or_raw(row.get("revenue_ratio")),
                    "gross_margin": _value_or_raw(row.get("gross_margin")),
                    "source_provider": str(provider),
                    "evidence_label": "manual_review_required",
                    "caveat": "Segment rows are a preview only; do not treat as reviewed composition or canonical main_business.",
                }
            )
            if len(rows) >= limit:
                return rows
    return rows


def _fallback_metric(
    evidence_pack_payloads: dict[str, Any],
    block: str,
    field: str,
) -> dict[str, Any]:
    for provider, payload in evidence_pack_payloads.items():
        block_payload = _dict_or_empty(_get(payload, block))
        if field not in block_payload:
            continue
        value = block_payload.get(field)
        return {
            "value": _value_or_raw(value),
            "display_value": value.get("display_value") if isinstance(value, dict) else None,
            "period": block_payload.get("period") if block == "financial_metrics" else None,
            "as_of_date": block_payload.get("period") if block == "valuation_metrics" else None,
            "unit": value.get("unit") if isinstance(value, dict) else None,
            "provider": str(provider),
        }
    return {}


def _build_source_artifact_refs(
    *,
    fundamental_payloads: dict[str, Any],
    evidence_pack_payloads: dict[str, Any],
    fact_candidates: dict[str, Any] | None,
    review_decisions: dict[str, Any] | None,
    score_explainability: dict[str, Any] | None,
    diff_report: dict[str, Any] | None,
) -> dict[str, Any]:
    explainability_refs = _dict_or_empty(_get(score_explainability, "providers"))
    fundamental_refs = []
    evidence_refs = []
    for provider in sorted(fundamental_payloads):
        ref = _provider_artifact_ref(explainability_refs, provider, "fundamental") or f"{provider}_fundamental.json"
        fundamental_refs.append(ref)
    for provider in sorted(evidence_pack_payloads):
        ref = _provider_artifact_ref(explainability_refs, provider, "evidence_pack") or f"{provider}_evidence_pack.json"
        evidence_refs.append(ref)
    return {
        "fundamental": _sanitize_refs(fundamental_refs),
        "evidence_pack": _sanitize_refs(evidence_refs),
        "fact_candidates": "fact_candidates.json" if fact_candidates else None,
        "candidate_review_decisions": "candidate_review_decisions.json" if review_decisions else None,
        "score_confidence_explainability": "score_confidence_explainability.json" if score_explainability else None,
        "provider_diff_report": "diff_report.json" if diff_report else None,
        "research_intelligence_p1": [],
    }


def _provider_artifact_ref(refs: dict[str, Any], provider: str, artifact_kind: str) -> str | None:
    provider_refs = _dict_or_empty(_get(refs, provider))
    artifacts = _dict_or_empty(provider_refs.get("artifact_refs"))
    value = artifacts.get(artifact_kind)
    return str(value) if value else None


def _sanitize_refs(refs: list[str]) -> list[str]:
    sanitized = []
    for ref in refs:
        name = Path(str(ref)).name
        if name and not _looks_like_forbidden_string(name):
            sanitized.append(name)
    return sanitized


def _candidate_list(fact_candidates: dict[str, Any] | None) -> list[dict[str, Any]]:
    return [candidate for candidate in _as_list(_get(fact_candidates, "candidates")) if isinstance(candidate, dict)]


def _auto_accepted_core_fields(fact_candidates: dict[str, Any] | None) -> list[dict[str, Any]]:
    return [item for item in _as_list(_get(fact_candidates, "auto_accepted_core_fields")) if isinstance(item, dict)]


def _manual_review_queue(fact_candidates: dict[str, Any] | None) -> list[dict[str, Any]]:
    return [item for item in _as_list(_get(fact_candidates, "manual_review_priority_queue")) if isinstance(item, dict)]


def _decision_list(review_decisions: dict[str, Any] | None) -> list[dict[str, Any]]:
    return [item for item in _as_list(_get(review_decisions, "decisions")) if isinstance(item, dict)]


def _best_candidate(candidates: list[dict[str, Any]], field_path: str) -> dict[str, Any] | None:
    matches = [candidate for candidate in candidates if _simple_field_path(str(candidate.get("field_path") or "")) == field_path]
    if not matches:
        return None
    auto = [candidate for candidate in matches if candidate.get("review_status") == "auto_accepted"]
    available = [candidate for candidate in matches if candidate.get("value") is not None]
    return (auto or available or matches)[0]


def _first_by_field(items: list[dict[str, Any]], field_path: str) -> dict[str, Any] | None:
    for item in items:
        if _simple_field_path(str(item.get("field_path") or "")) == field_path:
            return item
    return None


def _queue_label(item: dict[str, Any]) -> str:
    issue = str(item.get("issue_type") or item.get("queue_item_type") or "")
    if issue in {"block_provider_missing", "provider_missing", "akshare_only_review"}:
        return "coverage_caveat"
    return "manual_review_required"


def _decision_label(decision: dict[str, Any]) -> str:
    outcome = str(decision.get("decision_outcome") or "")
    if outcome in {"coverage_caveat", "defer_until_live_provider", "defer_until_sidecar"}:
        return "coverage_caveat"
    return "manual_review_required"


def _gap_item(
    *,
    field_path: str,
    status: Any,
    analysis: Any,
    evidence_label: str,
    caveat: Any,
) -> dict[str, Any]:
    return {
        "field_path": field_path,
        "status": status,
        "analysis": str(analysis or ""),
        "evidence_label": _safe_label(evidence_label),
        "caveat": caveat,
        "required_for_stronger_conclusion": True,
    }


def _condition(title: str, condition: str, supporting_fields: list[str]) -> dict[str, Any]:
    return {
        "title": title,
        "condition": condition,
        "evidence_label": "forward_tracking_variable",
        "supporting_fields": supporting_fields,
        "caveat": "This is a rebuttal condition, not a forecast.",
    }


def _tracking_variable(variable: str, why_it_matters: str) -> dict[str, Any]:
    return {
        "variable": variable,
        "why_it_matters": why_it_matters,
        "evidence_label": "forward_tracking_variable",
    }


def _judgement(
    *,
    title: str,
    analysis: str,
    evidence_label: str,
    supporting_fields: list[str] | None = None,
    caveats: list[Any] | None = None,
    follow_up_variables: list[str] | None = None,
) -> dict[str, Any]:
    item = {
        "title": title,
        "analysis": analysis,
        "evidence_label": _safe_label(evidence_label),
        "supporting_fields": supporting_fields or [],
        "caveats": _compact_list(caveats or []),
    }
    if follow_up_variables:
        item["follow_up_variables"] = follow_up_variables
    return item


def _score_caveat_texts(score_explainability: dict[str, Any] | None) -> list[str]:
    texts: list[str] = []
    for key in ("provider_caveats", "narrative_hints", "explainability_limitations"):
        for item in _as_list(_get(score_explainability, key)):
            if isinstance(item, dict):
                text = item.get("message") or item.get("note") or item.get("reason")
                if text:
                    texts.append(str(text))
            elif item:
                texts.append(str(item))
    return texts


def _display_value(value: Any, unit: Any) -> Any:
    if value is None:
        return None
    if _is_number(value):
        numeric = float(value)
        unit_text = str(unit or "")
        if unit_text == "RMB yuan":
            return f"{numeric:,.2f} RMB"
        if unit_text == "percentage_point":
            return f"{numeric:.2f}%"
        if unit_text == "multiple":
            return f"{numeric:.4g}x"
    return value


def _value_or_raw(value: Any) -> Any:
    if isinstance(value, dict):
        return value.get("raw_value", value.get("value", value.get("display_value")))
    return value


def _safe_label(label: str) -> str:
    if label not in ALLOWED_EVIDENCE_LABELS:
        return "coverage_caveat"
    return label


def _assert_report_payload(payload: dict[str, Any]) -> None:
    if payload.get("report_type") != REPORT_TYPE:
        raise ResearchReportBuildError("unsupported report_type")
    if payload.get("not_for_trading_advice") is not True:
        raise ResearchReportBuildError("report must be marked not_for_trading_advice")
    for key in (
        "code",
        "generated_at",
        "data_quality_assessment",
        "executive_summary",
        "macro_context",
        "industry_context",
        "company_fundamentals",
        "opportunity_analysis",
        "risk_analysis",
        "evidence_gaps",
        "rebuttal_conditions",
        "follow_up_variables",
        "source_artifact_refs",
    ):
        if key not in payload:
            raise ResearchReportBuildError(f"report is missing required section: {key}")
    _assert_no_forbidden_investment_advice_keys(payload)
    _assert_no_secret_like_payload(payload)
    _assert_evidence_labels(payload)


def _assert_evidence_labels(payload: Any) -> None:
    for path, item in _walk_dicts(payload, "$"):
        if "evidence_label" in item and item["evidence_label"] not in ALLOWED_EVIDENCE_LABELS:
            raise ResearchReportBuildError(f"invalid evidence_label at {path}")
        if any(key in item for key in ("analysis", "condition", "variable", "field_path")):
            if "evidence_label" not in item:
                raise ResearchReportBuildError(f"judgement item is missing evidence_label at {path}")
        if item.get("evidence_label") == "verified_fact":
            reviewed_source = item.get("reviewed_source") or item.get("reviewed_fixture")
            if not reviewed_source:
                raise ResearchReportBuildError("verified_fact requires an explicit reviewed source")


def _assert_no_forbidden_investment_advice_keys(payload: Any) -> None:
    for key in _walk_keys(payload):
        if str(key).lower() in FORBIDDEN_INVESTMENT_ADVICE_FIELDS:
            raise ResearchReportBuildError("report payload contains investment advice fields")


def _assert_dict(name: str, payload: Any) -> None:
    if not isinstance(payload, dict):
        raise ResearchReportBuildError(f"{name} must be a dict payload")


def _assert_no_secret_like_payload(payload: Any) -> None:
    finding = _first_secret_like_finding(payload, "$")
    if finding:
        raise ResearchReportSecretError(f"research report payload contains secret-like data at {finding}: <masked>")


def _first_secret_like_finding(value: Any, path: str) -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{_safe_path_key(str(key))}"
            if _SECRET_KEY_RE.search(str(key)) and child not in (None, "", "<masked>", "<redacted>"):
                return child_path
            key_finding = _first_secret_like_finding(str(key), f"{child_path}.__key__")
            if key_finding:
                return key_finding
            child_finding = _first_secret_like_finding(child, child_path)
            if child_finding:
                return child_finding
        return None
    if isinstance(value, list):
        for index, child in enumerate(value):
            child_finding = _first_secret_like_finding(child, f"{path}[{index}]")
            if child_finding:
                return child_finding
        return None
    if isinstance(value, str):
        if (
            _KEYED_SECRET_RE.search(value)
            or _BEARER_RE.search(value)
            or _MCP_RE.search(value)
            or _DOTENV_PATH_RE.search(value)
        ):
            return path
        if _LOCAL_SECRET_PATH_RE.search(value):
            return path
        if _TOKEN_LIKE_RE.search(value) and _SECRET_KEY_RE.search(value[:160]):
            return path
        if _TOKEN_LIKE_RE.fullmatch(value.strip()):
            return path
    return None


def _safe_path_key(key: str) -> str:
    if _SECRET_KEY_RE.search(key) or _TOKEN_LIKE_RE.search(key) or _DOTENV_PATH_RE.search(key):
        return "<masked_key>"
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,63}", key):
        return key
    return "<key>"


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _walk_dicts(value: Any, path: str):
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from _walk_dicts(child, f"{path}.{_safe_path_key(str(key))}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_dicts(child, f"{path}[{index}]")


def _normalize_code(code: str) -> str:
    code = str(code).strip()
    if not _STOCK_CODE_RE.fullmatch(code) or ".." in code:
        raise ResearchReportArtifactBoundaryError("code contains unsupported path characters")
    return code


def _simple_field_path(field_path: str) -> str:
    return _BUSINESS_INDEX_RE.sub("business_composition.", field_path)


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _get(payload: Any, key: str) -> Any:
    return payload.get(key) if isinstance(payload, dict) else None


def _first_payload(payloads: dict[str, Any]) -> dict[str, Any] | None:
    for value in payloads.values():
        if isinstance(value, dict):
            return value
    return None


def _compact_list(values: list[Any]) -> list[Any]:
    return [value for value in values if value not in (None, "", [], {})]


def _is_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return math.isfinite(float(value))
    if isinstance(value, str):
        try:
            return math.isfinite(float(value))
        except ValueError:
            return False
    return False


def _looks_like_forbidden_string(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return bool(_LOCAL_SECRET_PATH_RE.search(value) or _MCP_RE.search(value) or _DOTENV_PATH_RE.search(value))


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
