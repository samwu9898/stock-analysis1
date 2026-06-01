# -*- coding: utf-8 -*-
"""Ticker-agnostic research context skeleton builder.

This module is intentionally planning-only. It organizes explicitly supplied
provider candidates, verification queues, optional evidence summaries, and
industry hints into model-usable context. It does not fetch data, read local
artifacts, write outputs, generate reports, or make investment conclusions.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
import re
from typing import Any


TICKER_RESEARCH_CONTEXT_SCHEMA_VERSION = "ticker_research_context_skeleton.v1"
COMPANY_BUSINESS_PROFILE_SCHEMA_VERSION = "company_business_profile.v1"
FINANCIAL_CONTEXT_SCHEMA_VERSION = "provider_candidate_financial_context.v1"
INDUSTRY_CONTEXT_SCHEMA_VERSION = "industry_context.v1"
MACRO_TRANSMISSION_PATH_SCHEMA_VERSION = "macro_transmission_path.v1"
RESEARCH_QUESTION_SET_SCHEMA_VERSION = "research_question_set.v1"
DATA_GAP_PLAN_SCHEMA_VERSION = "research_context_data_gap_plan.v1"
EVIDENCE_STATUS_SUMMARY_SCHEMA_VERSION = "research_context_evidence_status_summary.v1"

PROVIDER_CANDIDATE_FINANCIAL_SNAPSHOT_SCHEMA_VERSION = "provider_candidate_financial_snapshot.v1"
PROVIDER_CANDIDATE_FINANCIAL_TREND_SCHEMA_VERSION = "provider_candidate_financial_trend_table.v1"
PROVIDER_CANDIDATE_QUEUE_SCHEMA_VERSION = "provider_candidate_metric_verification_queue.v1"

EVIDENCE_STATUSES = (
    "official_verified",
    "provider_candidate",
    "pending_official_verification",
    "framework_inference",
    "local_experiment",
    "data_gap",
    "blocked",
    "not_assessable",
)

QUESTION_PRIORITIES = ("high", "medium", "low")

TOP_LEVEL_REQUIRED_FIELDS = (
    "schema_version",
    "ts_code",
    "stock_code",
    "company_name_hint",
    "evidence_status_summary",
    "company_business_profile",
    "financial_context",
    "industry_context",
    "macro_transmission_path",
    "research_questions",
    "data_gap_plan",
    "caveats",
    "not_for_trading_advice",
)

_COMPANY_CONTEXT_REQUIRED_FIELDS = (
    "schema_version",
    "company_name_hint",
    "ts_code",
    "stock_code",
    "business_segments",
    "main_products",
    "revenue_structure",
    "downstream_or_end_markets",
    "business_model_questions",
    "evidence_status",
    "data_gaps",
    "caveats",
    "not_for_trading_advice",
)

_FINANCIAL_CONTEXT_REQUIRED_FIELDS = (
    "schema_version",
    "provider_trend_periods",
    "key_metric_candidates",
    "pending_official_verification_count",
    "missing_metric_count",
    "evidence_status",
    "data_gaps",
    "caveats",
    "not_for_trading_advice",
)

_INDUSTRY_CONTEXT_REQUIRED_FIELDS = (
    "schema_version",
    "strategy_type",
    "sub_type",
    "industry_tags",
    "possible_industry_frameworks",
    "industry_driver_questions",
    "industry_data_gaps",
    "evidence_status",
    "not_for_trading_advice",
)

_MACRO_PATH_REQUIRED_FIELDS = (
    "schema_version",
    "macro_variables_to_investigate",
    "industry_to_company_transmission_questions",
    "required_evidence_for_transmission",
    "data_gaps",
    "caveats",
    "not_for_trading_advice",
)

_RESEARCH_QUESTION_REQUIRED_FIELDS = (
    "question_id",
    "category",
    "question_text",
    "required_data",
    "current_evidence_status",
    "priority",
    "not_for_trading_advice",
)

_DATA_GAP_REQUIRED_FIELDS = (
    "gap_id",
    "category",
    "description",
    "required_data",
    "current_evidence_status",
    "priority",
    "not_for_trading_advice",
)

_ALLOWED_EXACT_KEYS = {
    "not_for_trading_advice",
    "not_official_verified",
}

_EVIDENCE_STATUS_FIELD_KEYS = {
    "evidence_status",
    "current_evidence_status",
    "required_next_status",
    "statuses_used",
    "official_evidence_statuses",
}

_FORBIDDEN_MARKERS = (
    "token",
    ".env",
    "tushare_token",
    "Report V1",
    "accepted manifest write",
    "write accepted manifest",
    "accepted_manifest_write",
    "output baseline write",
    "write output baseline",
    "output_baseline_write",
    "fixture write",
    "write fixture",
    "fixture_write",
    "buy",
    "sell",
    "hold",
    "target price",
    "price target",
    "portfolio",
    "position",
    "technical signal",
    "trading advice",
    "investment advice",
)

_FORBIDDEN_CJK_MARKERS = (
    "\u4e70\u5165",
    "\u5356\u51fa",
    "\u6301\u6709",
    "\u76ee\u6807\u4ef7",
    "\u4ed3\u4f4d",
    "\u7ec4\u5408",
    "\u6280\u672f\u4fe1\u53f7",
    "\u6295\u8d44\u5efa\u8bae",
    "\u6b63\u5f0f\u7814\u62a5",
    "\u8f93\u51fa\u57fa\u7ebf",
    "\u5199\u5165fixture",
    "\u5199\u5165accepted manifest",
    "\u8bfb\u53d6token",
    "\u8bfb\u53d6.env",
    "\u8bfb\u53d6tushare_token",
)

_WORD_MARKERS = {"token", "buy", "sell", "hold", "portfolio", "position"}
_IDENTIFIER_SAFE_WORD_MARKERS = {"buy", "sell", "hold"}

_METRIC_CONTAINER_KEYS = ("selected_metrics", "metrics", "key_metrics")
_TREND_ROW_META_KEYS = {
    "schema_version",
    "provider",
    "period_label",
    "period",
    "ann_date",
    "end_date",
    "source_tables_available",
    "selected_metrics",
    "metrics",
    "key_metrics",
    "missing_fields",
    "not_official_verified",
    "not_for_trading_advice",
}


class TickerResearchContextSkeletonError(ValueError):
    """Raised when a research context skeleton fails closed."""


def build_ticker_research_context_skeleton(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Build a ticker-agnostic context skeleton from explicit caller input."""

    source = _validated_payload_copy(payload)
    _assert_provider_candidate_inputs_not_official_verified(source)

    company_context = build_company_business_context_seed(source)
    financial_context = build_financial_context_from_provider_candidate(source)
    industry_context = build_industry_context_seed(source)
    macro_path = build_macro_transmission_prompt_seed(source)
    research_questions = _build_research_question_set_from_context(
        company_context=company_context,
        financial_context=financial_context,
        industry_context=industry_context,
        macro_path=macro_path,
    )
    data_gap_plan = _build_data_gap_plan(
        company_context=company_context,
        financial_context=financial_context,
        industry_context=industry_context,
        macro_path=macro_path,
    )

    context = {
        "schema_version": TICKER_RESEARCH_CONTEXT_SCHEMA_VERSION,
        "ts_code": _resolve_ts_code(source),
        "stock_code": _resolve_stock_code(source),
        "company_name_hint": source.get("company_name_hint"),
        "evidence_status_summary": _build_evidence_status_summary(source),
        "company_business_profile": company_context,
        "company_business_context": deepcopy(company_context),
        "financial_context": financial_context,
        "industry_context": industry_context,
        "macro_transmission_path": macro_path,
        "research_questions": research_questions,
        "data_gap_plan": data_gap_plan,
        "caveats": [
            "Context skeleton organizes input evidence status and model tasks only.",
            "Provider candidate inputs stay candidate-only until official checks are supplied.",
            "Company, industry, and macro judgments are left to downstream model analysis.",
        ],
        "not_for_trading_advice": True,
    }
    return validate_ticker_research_context_skeleton(context)


def build_company_business_context_seed(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Build the company business profile component from explicit evidence only."""

    source = _validated_payload_copy(payload)
    business = _extract_business_evidence(source)
    has_business_evidence = any(
        business[field]
        for field in (
            "business_segments",
            "main_products",
            "revenue_structure",
            "downstream_or_end_markets",
        )
    )
    evidence_status = _dominant_evidence_status(business["evidence_statuses"])
    if not has_business_evidence:
        evidence_status = "data_gap"

    data_gaps: list[dict[str, Any]] = []
    if not business["business_segments"] and not business["revenue_structure"]:
        data_gaps.append(
            _gap(
                gap_id="company_business_composition_missing",
                category="company_business",
                description="Explicit business segment and revenue mix evidence was not supplied.",
                required_data=[
                    "business segment disclosure",
                    "revenue mix disclosure",
                ],
                current_evidence_status="data_gap",
                priority="high",
            )
        )
    if not business["main_products"]:
        data_gaps.append(
            _gap(
                gap_id="company_main_products_missing",
                category="company_business",
                description="Explicit product or service evidence was not supplied.",
                required_data=["product or service disclosure"],
                current_evidence_status="data_gap",
                priority="medium",
            )
        )
    if not business["downstream_or_end_markets"]:
        data_gaps.append(
            _gap(
                gap_id="company_end_markets_missing",
                category="company_business",
                description="Explicit end-market evidence was not supplied.",
                required_data=["customer or end-market disclosure"],
                current_evidence_status="data_gap",
                priority="medium",
            )
        )

    profile = {
        "schema_version": COMPANY_BUSINESS_PROFILE_SCHEMA_VERSION,
        "company_name_hint": source.get("company_name_hint"),
        "ts_code": _resolve_ts_code(source),
        "stock_code": _resolve_stock_code(source),
        "business_segments": business["business_segments"],
        "main_products": business["main_products"],
        "revenue_structure": business["revenue_structure"],
        "downstream_or_end_markets": business["downstream_or_end_markets"],
        "business_model_questions": [
            "What explicit disclosures define business segments and revenue mix?",
            "Which products or services are material enough to map into financial metrics?",
            "Which customer or end-market evidence is needed before model judgment?",
        ],
        "evidence_status": evidence_status,
        "data_gaps": data_gaps,
        "caveats": [
            "Business profile uses only explicit business evidence supplied in the payload.",
            "Financial trends alone are not used to infer business segments.",
        ],
        "not_for_trading_advice": True,
    }
    return _validate_company_business_context(profile)


def build_financial_context_from_provider_candidate(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Build financial context from provider-candidate data and verification queues."""

    source = _validated_payload_copy(payload)
    _assert_provider_candidate_inputs_not_official_verified(source)

    provider_result = _provider_candidate_financial_result(source)
    queue = _provider_candidate_verification_queue(source)
    trend_rows = _trend_rows_from_provider_result(provider_result, source)
    periods = _periods_from_provider_inputs(provider_result, queue, trend_rows)
    key_metric_candidates = _metric_candidates_from_trend_rows(trend_rows)
    pending_count, queue_missing_count = _verification_queue_counts(queue)
    provider_missing_count = sum(
        1 for item in key_metric_candidates if item["value_status"] == "missing"
    )
    missing_metric_count = max(provider_missing_count, queue_missing_count)

    evidence_status: list[str] = []
    if key_metric_candidates:
        evidence_status.append("provider_candidate")
    if pending_count:
        evidence_status.append("pending_official_verification")
    if not evidence_status:
        evidence_status.append("data_gap")

    data_gaps: list[dict[str, Any]] = []
    if provider_result is None and not trend_rows:
        data_gaps.append(
            _gap(
                gap_id="provider_candidate_financial_result_missing",
                category="financial",
                description="Provider candidate financial trend evidence was not supplied.",
                required_data=["provider candidate financial trend table"],
                current_evidence_status="data_gap",
                priority="high",
            )
        )
    if queue is None:
        data_gaps.append(
            _gap(
                gap_id="provider_candidate_verification_queue_missing",
                category="financial",
                description="Pending metric verification queue was not supplied.",
                required_data=["provider candidate metric verification queue"],
                current_evidence_status="data_gap",
                priority="high",
            )
        )
    if missing_metric_count:
        data_gaps.append(
            _gap(
                gap_id="provider_candidate_metrics_missing",
                category="financial",
                description="Some provider candidate metrics are missing and need follow-up evidence.",
                required_data=["missing metric values or official disclosure checks"],
                current_evidence_status="data_gap",
                priority="medium",
            )
        )

    caveats = [
        "Provider financial metrics are candidate observations only.",
        "Queued metrics remain pending official verification.",
    ]
    caveats.extend(_string_list_from_mapping(provider_result, "blocked_reasons"))
    caveats.extend(_string_list_from_mapping(provider_result, "caveats"))
    caveats.extend(_string_list_from_mapping(queue, "blocked_reasons"))
    caveats.extend(_string_list_from_mapping(queue, "caveats"))

    financial_context = {
        "schema_version": FINANCIAL_CONTEXT_SCHEMA_VERSION,
        "provider_trend_periods": periods,
        "key_metric_candidates": key_metric_candidates,
        "pending_official_verification_count": pending_count,
        "missing_metric_count": missing_metric_count,
        "evidence_status": _dedupe_preserve_order(evidence_status),
        "data_gaps": data_gaps,
        "caveats": _dedupe_preserve_order(caveats),
        "not_for_trading_advice": True,
    }
    return _validate_financial_context(financial_context)


def build_industry_context_seed(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Build industry context from explicit strategy/sub-type/framework hints."""

    source = _validated_payload_copy(payload)
    hint = source.get("industry_framework_hint")
    hint_items = _industry_hint_items(hint)

    strategy_type = source.get("strategy_type")
    sub_type = source.get("sub_type")
    industry_tags = _dedupe_preserve_order(
        _string_values(source.get("industry_tags"))
        + _collect_hint_strings(hint_items, ("industry_tags", "tags"))
    )
    possible_frameworks = _possible_industry_frameworks(
        strategy_type=strategy_type,
        sub_type=sub_type,
        hint_items=hint_items,
    )
    driver_questions = _dedupe_preserve_order(
        _collect_hint_strings(
            hint_items,
            (
                "industry_driver_questions",
                "driver_questions",
                "questions",
            ),
        )
    )

    has_explicit_industry_context = bool(
        strategy_type or sub_type or industry_tags or possible_frameworks or driver_questions
    )
    if has_explicit_industry_context and not driver_questions:
        driver_questions = [
            "Which supplied industry drivers should be tested against company disclosures?",
            "Which data series are needed to connect industry drivers to company financial metrics?",
        ]
    if not has_explicit_industry_context:
        driver_questions = [
            "Which explicit industry context should be supplied before model analysis?",
        ]

    evidence_status = _dominant_evidence_status(
        _collect_hint_strings(hint_items, ("evidence_status", "current_evidence_status"))
    )
    if evidence_status == "not_assessable" and has_explicit_industry_context:
        evidence_status = "framework_inference"

    industry_data_gaps: list[dict[str, Any]] = []
    if not has_explicit_industry_context:
        industry_data_gaps.append(
            _gap(
                gap_id="explicit_industry_context_missing",
                category="industry",
                description="Explicit industry framework or tag evidence was not supplied.",
                required_data=["strategy type, sub-type, or industry framework hint"],
                current_evidence_status="data_gap",
                priority="high",
            )
        )
        evidence_status = "not_assessable"

    industry_context = {
        "schema_version": INDUSTRY_CONTEXT_SCHEMA_VERSION,
        "strategy_type": strategy_type,
        "sub_type": sub_type,
        "industry_tags": industry_tags,
        "possible_industry_frameworks": possible_frameworks,
        "industry_driver_questions": driver_questions,
        "industry_data_gaps": industry_data_gaps,
        "evidence_status": evidence_status,
        "not_for_trading_advice": True,
    }
    return _validate_industry_context(industry_context)


def build_macro_transmission_prompt_seed(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Build macro transmission questions and evidence needs without conclusions."""

    source = _validated_payload_copy(payload)
    industry_context = build_industry_context_seed(source)
    hint_items = _industry_hint_items(source.get("industry_framework_hint"))
    macro_variables = _dedupe_preserve_order(
        _collect_hint_strings(
            hint_items,
            (
                "macro_variables_to_investigate",
                "macro_variables",
                "macro_factors",
            ),
        )
    )

    has_industry_context = industry_context["evidence_status"] != "not_assessable"
    data_gaps: list[dict[str, Any]] = []
    if has_industry_context and not macro_variables:
        macro_variables = ["macro variables linked to the supplied industry context"]
    if not has_industry_context:
        data_gaps.append(
            _gap(
                gap_id="macro_transmission_industry_context_missing",
                category="macro",
                description="Macro transmission cannot be framed without explicit industry context.",
                required_data=["explicit industry framework or industry tags"],
                current_evidence_status="data_gap",
                priority="high",
            )
        )

    transmission_questions = [
        "Which macro variables should be tested through the supplied industry context?",
        "What evidence links industry drivers to company revenue, margins, or cash flow metrics?",
    ]
    if not has_industry_context:
        transmission_questions = [
            "Which industry context is needed before macro transmission can be assessed?",
        ]

    macro_path = {
        "schema_version": MACRO_TRANSMISSION_PATH_SCHEMA_VERSION,
        "macro_variables_to_investigate": macro_variables,
        "industry_to_company_transmission_questions": transmission_questions,
        "required_evidence_for_transmission": [
            "industry data series tied to the supplied framework",
            "company segment or product evidence",
            "provider candidate financial metrics pending official verification",
        ],
        "data_gaps": data_gaps,
        "caveats": [
            "Macro transmission path is question-only and does not state direction or impact.",
            "Industry-to-company linkage requires explicit evidence before model judgment.",
        ],
        "not_for_trading_advice": True,
    }
    return _validate_macro_transmission_path(macro_path)


def build_research_question_set(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Build a research question set with required data and evidence status."""

    source = _validated_payload_copy(payload)
    return _build_research_question_set_from_context(
        company_context=build_company_business_context_seed(source),
        financial_context=build_financial_context_from_provider_candidate(source),
        industry_context=build_industry_context_seed(source),
        macro_path=build_macro_transmission_prompt_seed(source),
    )


def validate_ticker_research_context_skeleton(context: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and return a defensive copy of a context skeleton."""

    assert_no_research_context_forbidden_markers(context)
    validated = _require_mapping(context, "ticker_research_context_skeleton")
    missing = [field for field in TOP_LEVEL_REQUIRED_FIELDS if field not in validated]
    if missing:
        raise TickerResearchContextSkeletonError(f"context missing required fields: {missing}")

    result = deepcopy(dict(validated))
    _require_schema_version(
        result["schema_version"],
        TICKER_RESEARCH_CONTEXT_SCHEMA_VERSION,
        "schema_version",
    )
    _require_optional_string(result["ts_code"], "ts_code")
    _require_optional_string(result["stock_code"], "stock_code")
    _require_optional_string(result["company_name_hint"], "company_name_hint")
    _require_true(result["not_for_trading_advice"], "not_for_trading_advice")

    result["company_business_profile"] = _validate_company_business_context(
        result["company_business_profile"]
    )
    if "company_business_context" in result:
        result["company_business_context"] = _validate_company_business_context(
            result["company_business_context"]
        )
        if result["company_business_context"] != result["company_business_profile"]:
            raise TickerResearchContextSkeletonError(
                "company_business_context alias must match company_business_profile"
            )
    else:
        result["company_business_context"] = deepcopy(result["company_business_profile"])
    result["financial_context"] = _validate_financial_context(result["financial_context"])
    result["industry_context"] = _validate_industry_context(result["industry_context"])
    result["macro_transmission_path"] = _validate_macro_transmission_path(
        result["macro_transmission_path"]
    )
    result["research_questions"] = _validate_research_question_set(result["research_questions"])
    result["data_gap_plan"] = _validate_data_gap_plan(result["data_gap_plan"])
    _validate_evidence_status_summary(result["evidence_status_summary"])
    _require_string_list(result["caveats"], "caveats")
    _validate_evidence_status_values(result)
    _assert_financial_context_not_official_verified(result["financial_context"])
    return result


def assert_no_research_context_forbidden_markers(value: Any) -> None:
    """Reject blocked markers in nested keys and values without leaking payload text."""

    finding = _find_forbidden_marker(value)
    if finding:
        raise TickerResearchContextSkeletonError(
            f"research context safety violation: forbidden marker: {finding}"
        )


def _build_research_question_set_from_context(
    *,
    company_context: Mapping[str, Any],
    financial_context: Mapping[str, Any],
    industry_context: Mapping[str, Any],
    macro_path: Mapping[str, Any],
) -> dict[str, Any]:
    financial_status = _first_status(financial_context["evidence_status"])
    industry_status = str(industry_context["evidence_status"])
    questions = [
        _question(
            question_id="rq_company_business_model_001",
            category="company_business_model",
            question_text="What explicit disclosures define business segments, products, and revenue mix?",
            required_data=["business segment disclosure", "revenue mix disclosure"],
            current_evidence_status=str(company_context["evidence_status"]),
            priority="high" if company_context["data_gaps"] else "medium",
        ),
        _question(
            question_id="rq_financial_quality_001",
            category="financial_quality",
            question_text="Which provider candidate metrics require official disclosure checks before model analysis?",
            required_data=["provider metric queue", "official disclosure metric checks"],
            current_evidence_status=financial_status,
            priority="high" if financial_context["pending_official_verification_count"] else "medium",
        ),
        _question(
            question_id="rq_industry_context_001",
            category="industry_context",
            question_text="Which industry framework is supported by explicit input evidence?",
            required_data=["strategy type, sub-type, or industry framework hint"],
            current_evidence_status=industry_status,
            priority="high" if industry_context["industry_data_gaps"] else "medium",
        ),
        _question(
            question_id="rq_macro_transmission_001",
            category="macro_transmission",
            question_text="Which macro variables should be tested through the supplied industry context?",
            required_data=["macro variables", "industry data series", "company segment evidence"],
            current_evidence_status="data_gap" if macro_path["data_gaps"] else "framework_inference",
            priority="medium",
        ),
        _question(
            question_id="rq_official_verification_001",
            category="official_verification",
            question_text="Which pending provider metrics should be checked against official disclosures first?",
            required_data=["pending verification queue", "official disclosure metric sources"],
            current_evidence_status=(
                "pending_official_verification"
                if financial_context["pending_official_verification_count"]
                else "data_gap"
            ),
            priority="high",
        ),
        _question(
            question_id="rq_data_gap_001",
            category="data_gap",
            question_text="Which missing evidence blocks a fuller research context?",
            required_data=["company, financial, industry, and macro gap list"],
            current_evidence_status="data_gap",
            priority="high",
        ),
    ]
    question_set = {
        "schema_version": RESEARCH_QUESTION_SET_SCHEMA_VERSION,
        "questions": questions,
        "not_for_trading_advice": True,
    }
    return _validate_research_question_set(question_set)


def _build_data_gap_plan(
    *,
    company_context: Mapping[str, Any],
    financial_context: Mapping[str, Any],
    industry_context: Mapping[str, Any],
    macro_path: Mapping[str, Any],
) -> dict[str, Any]:
    gaps: list[dict[str, Any]] = []
    gaps.extend(deepcopy(company_context["data_gaps"]))
    gaps.extend(deepcopy(financial_context["data_gaps"]))
    gaps.extend(deepcopy(industry_context["industry_data_gaps"]))
    gaps.extend(deepcopy(macro_path["data_gaps"]))

    plan = {
        "schema_version": DATA_GAP_PLAN_SCHEMA_VERSION,
        "data_gaps": gaps,
        "blocked_reasons": [
            gap["gap_id"]
            for gap in gaps
            if gap["priority"] == "high" and gap["current_evidence_status"] == "data_gap"
        ],
        "next_data_tasks": [
            {
                "task_id": f"task_{index + 1:03d}",
                "gap_id": gap["gap_id"],
                "required_data": list(gap["required_data"]),
                "current_evidence_status": gap["current_evidence_status"],
                "priority": gap["priority"],
                "not_for_trading_advice": True,
            }
            for index, gap in enumerate(gaps)
        ],
        "not_for_trading_advice": True,
    }
    return _validate_data_gap_plan(plan)


def _build_evidence_status_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    provider_result = _provider_candidate_financial_result(payload)
    queue = _provider_candidate_verification_queue(payload)
    official_statuses = _explicit_official_evidence_statuses(payload)
    statuses = []
    if provider_result is not None:
        statuses.append("provider_candidate")
    if queue is not None:
        statuses.append("pending_official_verification")
    statuses.extend(official_statuses)
    if not statuses:
        statuses.append("data_gap")

    summary = {
        "schema_version": EVIDENCE_STATUS_SUMMARY_SCHEMA_VERSION,
        "statuses_used": _dedupe_preserve_order(statuses),
        "provider_candidate_financial_supplied": provider_result is not None,
        "verification_queue_supplied": queue is not None,
        "official_evidence_statuses": official_statuses,
        "has_explicit_official_evidence": "official_verified" in official_statuses,
        "not_for_trading_advice": True,
    }
    _validate_evidence_status_summary(summary)
    return summary


def _extract_business_evidence(payload: Mapping[str, Any]) -> dict[str, Any]:
    records: list[Mapping[str, Any]] = []
    for key in (
        "business_composition_evidence",
        "business_profile",
        "company_business_profile",
        "evidence_pack_summary",
    ):
        records.extend(_mapping_items(payload.get(key)))
    records.extend(_mapping_items(payload.get("official_anchor_candidates")))

    business = {
        "business_segments": _normalise_explicit_items(payload.get("business_segments")),
        "main_products": _normalise_explicit_items(payload.get("main_products")),
        "revenue_structure": _normalise_explicit_items(payload.get("revenue_structure")),
        "downstream_or_end_markets": _normalise_explicit_items(
            payload.get("downstream_or_end_markets")
        ),
        "evidence_statuses": _string_values(payload.get("business_evidence_status")),
    }
    for record in records:
        business["business_segments"].extend(
            _normalise_explicit_items(
                _first_present(record, ("business_segments", "segments"))
            )
        )
        business["main_products"].extend(
            _normalise_explicit_items(_first_present(record, ("main_products", "products")))
        )
        business["revenue_structure"].extend(
            _normalise_explicit_items(
                _first_present(record, ("revenue_structure", "revenue_mix"))
            )
        )
        business["downstream_or_end_markets"].extend(
            _normalise_explicit_items(
                _first_present(record, ("downstream_or_end_markets", "end_markets"))
            )
        )
        business["evidence_statuses"].extend(_evidence_statuses_from_mapping(record))

    for key in (
        "business_segments",
        "main_products",
        "revenue_structure",
        "downstream_or_end_markets",
        "evidence_statuses",
    ):
        business[key] = _dedupe_preserve_order(business[key])
    return business


def _provider_candidate_financial_result(payload: Mapping[str, Any]) -> Mapping[str, Any] | None:
    value = _first_present(
        payload,
        (
            "provider_candidate_financial_result",
            "provider_candidate_financial_snapshot",
        ),
    )
    return value if isinstance(value, Mapping) else None


def _provider_candidate_verification_queue(payload: Mapping[str, Any]) -> Mapping[str, Any] | None:
    value = payload.get("provider_candidate_metric_verification_queue")
    return value if isinstance(value, Mapping) else None


def _trend_rows_from_provider_result(
    provider_result: Mapping[str, Any] | None,
    payload: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    explicit_trend_table = payload.get("provider_candidate_financial_trend_table")
    if isinstance(explicit_trend_table, list):
        return [row for row in explicit_trend_table if isinstance(row, Mapping)]
    if provider_result is None:
        return []
    trend_table = provider_result.get("trend_table")
    if not isinstance(trend_table, list):
        return []
    return [row for row in trend_table if isinstance(row, Mapping)]


def _periods_from_provider_inputs(
    provider_result: Mapping[str, Any] | None,
    queue: Mapping[str, Any] | None,
    trend_rows: list[Mapping[str, Any]],
) -> list[str]:
    periods: list[str] = []
    if provider_result is not None:
        periods.extend(_string_values(provider_result.get("periods")))
    periods.extend(_safe_string(row.get("period")) for row in trend_rows)
    if queue is not None:
        periods.extend(_string_values(queue.get("periods")))
        verification_items = queue.get("verification_items")
        if isinstance(verification_items, list):
            periods.extend(
                _safe_string(item.get("period"))
                for item in verification_items
                if isinstance(item, Mapping)
            )
    return _dedupe_preserve_order(period for period in periods if period)


def _metric_candidates_from_trend_rows(trend_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for row in trend_rows:
        metrics = _metrics_from_trend_row(row)
        for metric_key, metric_value in metrics.items():
            candidates.append(
                {
                    "period": row.get("period"),
                    "period_label": row.get("period_label"),
                    "ann_date": row.get("ann_date"),
                    "end_date": row.get("end_date"),
                    "metric_key": str(metric_key),
                    "metric_value": deepcopy(metric_value),
                    "source_tables_available": _string_values(row.get("source_tables_available")),
                    "value_status": "missing" if metric_value is None else "present",
                    "current_evidence_status": "provider_candidate",
                    "required_next_status": "pending_official_verification",
                    "not_for_trading_advice": True,
                }
            )
    return candidates


def _metrics_from_trend_row(row: Mapping[str, Any]) -> dict[str, Any]:
    for key in _METRIC_CONTAINER_KEYS:
        value = row.get(key)
        if isinstance(value, Mapping):
            return {str(metric_key): deepcopy(metric_value) for metric_key, metric_value in value.items()}
    metrics: dict[str, Any] = {}
    for key, value in row.items():
        if key not in _TREND_ROW_META_KEYS:
            metrics[str(key)] = deepcopy(value)
    return metrics


def _verification_queue_counts(queue: Mapping[str, Any] | None) -> tuple[int, int]:
    if queue is None:
        return 0, 0
    verification_items = queue.get("verification_items")
    if not isinstance(verification_items, list):
        return 0, 0
    pending_count = 0
    missing_count = 0
    for item in verification_items:
        if not isinstance(item, Mapping):
            continue
        status = item.get("official_verification_status")
        if status == "pending_official_verification":
            pending_count += 1
        elif status not in (None, ""):
            raise TickerResearchContextSkeletonError(
                "provider candidate verification status must remain pending_official_verification"
            )
        if item.get("value_status") == "missing":
            missing_count += 1
    return pending_count, missing_count


def _possible_industry_frameworks(
    *,
    strategy_type: Any,
    sub_type: Any,
    hint_items: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    frameworks: list[dict[str, Any]] = []
    for framework_id in _string_values(strategy_type):
        frameworks.append(
            {
                "framework_id": framework_id,
                "sub_type": _safe_string(sub_type),
                "source": "input_strategy_type",
                "current_evidence_status": "framework_inference",
                "not_for_trading_advice": True,
            }
        )
    for item in hint_items:
        raw_frameworks = _first_present(
            item,
            (
                "possible_industry_frameworks",
                "frameworks",
                "framework_ids",
                "framework_id",
            ),
        )
        for framework_id in _string_values(raw_frameworks):
            frameworks.append(
                {
                    "framework_id": framework_id,
                    "sub_type": _safe_string(_first_present(item, ("sub_type",))),
                    "source": "input_industry_framework_hint",
                    "current_evidence_status": _dominant_evidence_status(
                        _evidence_statuses_from_mapping(item)
                    )
                    if _evidence_statuses_from_mapping(item)
                    else "framework_inference",
                    "not_for_trading_advice": True,
                }
            )
        if not raw_frameworks and isinstance(item.get("name"), str):
            frameworks.append(
                {
                    "framework_id": item["name"],
                    "sub_type": _safe_string(_first_present(item, ("sub_type",))),
                    "source": "input_industry_framework_hint",
                    "current_evidence_status": "framework_inference",
                    "not_for_trading_advice": True,
                }
            )
    return _dedupe_frameworks(frameworks)


def _industry_hint_items(hint: Any) -> list[Mapping[str, Any]]:
    if isinstance(hint, Mapping):
        return [hint]
    if isinstance(hint, list):
        return [item for item in hint if isinstance(item, Mapping)]
    if isinstance(hint, str) and hint.strip():
        return [{"framework_id": hint.strip()}]
    return []


def _collect_hint_strings(items: Iterable[Mapping[str, Any]], keys: Iterable[str]) -> list[str]:
    values: list[str] = []
    for item in items:
        values.extend(_string_values(_first_present(item, tuple(keys))))
    return values


def _explicit_official_evidence_statuses(payload: Mapping[str, Any]) -> list[str]:
    statuses: list[str] = []
    for key in ("official_anchor_candidates", "official_metadata_candidates", "evidence_pack_summary"):
        for item in _mapping_items(payload.get(key)):
            statuses.extend(
                status
                for status in _evidence_statuses_from_mapping(item)
                if status == "official_verified"
            )
            if item.get("official_verified") is True:
                statuses.append("official_verified")
    return _dedupe_preserve_order(statuses)


def _validated_payload_copy(payload: Mapping[str, Any]) -> dict[str, Any]:
    source = _require_mapping(payload, "payload")
    assert_no_research_context_forbidden_markers(source)
    if source.get("not_for_trading_advice", True) is not True:
        raise TickerResearchContextSkeletonError("not_for_trading_advice must be true")
    return deepcopy(dict(source))


def _assert_provider_candidate_inputs_not_official_verified(payload: Mapping[str, Any]) -> None:
    for key in (
        "provider_candidate_financial_result",
        "provider_candidate_financial_snapshot",
        "provider_candidate_financial_trend_table",
        "provider_candidate_metric_verification_queue",
    ):
        if key in payload and _contains_official_verified_marker(payload[key]):
            raise TickerResearchContextSkeletonError(
                "provider candidate input cannot claim official_verified"
            )


def _assert_financial_context_not_official_verified(financial_context: Mapping[str, Any]) -> None:
    if _contains_official_verified_marker(financial_context):
        raise TickerResearchContextSkeletonError(
            "financial context cannot claim official_verified for provider candidates"
        )


def _contains_official_verified_marker(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if _normalise_marker(key_text) != "not_official_verified":
                if _contains_official_verified_text(key_text):
                    return True
            if _contains_official_verified_marker(child):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_official_verified_marker(item) for item in value)
    if isinstance(value, str):
        return _contains_official_verified_text(value)
    return False


def _contains_official_verified_text(value: str) -> bool:
    normalised = _normalise_marker(value)
    if normalised == "not_official_verified":
        return False
    return bool(re.search(r"(?<!not_)official_verified", normalised))


def _validate_company_business_context(value: Any) -> dict[str, Any]:
    context = _require_mapping(value, "company_business_context")
    _require_fields(context, _COMPANY_CONTEXT_REQUIRED_FIELDS, "company_business_context")
    result = deepcopy(dict(context))
    _require_schema_version(
        result["schema_version"],
        COMPANY_BUSINESS_PROFILE_SCHEMA_VERSION,
        "company_business_context.schema_version",
    )
    _require_optional_string(result["company_name_hint"], "company_name_hint")
    _require_optional_string(result["ts_code"], "ts_code")
    _require_optional_string(result["stock_code"], "stock_code")
    for key in (
        "business_segments",
        "main_products",
        "revenue_structure",
        "downstream_or_end_markets",
    ):
        _require_list(result[key], key)
    _require_string_list(result["business_model_questions"], "business_model_questions")
    _require_evidence_status(result["evidence_status"], "company_business_context.evidence_status")
    result["data_gaps"] = [_validate_gap(gap, f"company_business_context.data_gaps[{index}]") for index, gap in enumerate(result["data_gaps"])]
    _require_string_list(result["caveats"], "company_business_context.caveats")
    _require_true(result["not_for_trading_advice"], "company_business_context.not_for_trading_advice")
    return result


def _validate_financial_context(value: Any) -> dict[str, Any]:
    context = _require_mapping(value, "financial_context")
    _require_fields(context, _FINANCIAL_CONTEXT_REQUIRED_FIELDS, "financial_context")
    result = deepcopy(dict(context))
    _require_schema_version(
        result["schema_version"],
        FINANCIAL_CONTEXT_SCHEMA_VERSION,
        "financial_context.schema_version",
    )
    _require_string_list(result["provider_trend_periods"], "financial_context.provider_trend_periods")
    _require_list(result["key_metric_candidates"], "financial_context.key_metric_candidates")
    for index, item in enumerate(result["key_metric_candidates"]):
        _validate_metric_candidate(item, f"financial_context.key_metric_candidates[{index}]")
    _require_non_negative_int(
        result["pending_official_verification_count"],
        "financial_context.pending_official_verification_count",
    )
    _require_non_negative_int(result["missing_metric_count"], "financial_context.missing_metric_count")
    _require_evidence_status_collection(result["evidence_status"], "financial_context.evidence_status")
    result["data_gaps"] = [_validate_gap(gap, f"financial_context.data_gaps[{index}]") for index, gap in enumerate(result["data_gaps"])]
    _require_string_list(result["caveats"], "financial_context.caveats")
    _require_true(result["not_for_trading_advice"], "financial_context.not_for_trading_advice")
    _assert_financial_context_not_official_verified(result)
    return result


def _validate_industry_context(value: Any) -> dict[str, Any]:
    context = _require_mapping(value, "industry_context")
    _require_fields(context, _INDUSTRY_CONTEXT_REQUIRED_FIELDS, "industry_context")
    result = deepcopy(dict(context))
    _require_schema_version(
        result["schema_version"],
        INDUSTRY_CONTEXT_SCHEMA_VERSION,
        "industry_context.schema_version",
    )
    _require_optional_string(result["strategy_type"], "industry_context.strategy_type")
    _require_optional_string(result["sub_type"], "industry_context.sub_type")
    _require_string_list(result["industry_tags"], "industry_context.industry_tags")
    _require_list(result["possible_industry_frameworks"], "industry_context.possible_industry_frameworks")
    for index, framework in enumerate(result["possible_industry_frameworks"]):
        _validate_framework(framework, f"industry_context.possible_industry_frameworks[{index}]")
    _require_string_list(result["industry_driver_questions"], "industry_context.industry_driver_questions")
    result["industry_data_gaps"] = [
        _validate_gap(gap, f"industry_context.industry_data_gaps[{index}]")
        for index, gap in enumerate(result["industry_data_gaps"])
    ]
    _require_evidence_status(result["evidence_status"], "industry_context.evidence_status")
    _require_true(result["not_for_trading_advice"], "industry_context.not_for_trading_advice")
    return result


def _validate_macro_transmission_path(value: Any) -> dict[str, Any]:
    context = _require_mapping(value, "macro_transmission_path")
    _require_fields(context, _MACRO_PATH_REQUIRED_FIELDS, "macro_transmission_path")
    result = deepcopy(dict(context))
    _require_schema_version(
        result["schema_version"],
        MACRO_TRANSMISSION_PATH_SCHEMA_VERSION,
        "macro_transmission_path.schema_version",
    )
    _require_string_list(
        result["macro_variables_to_investigate"],
        "macro_transmission_path.macro_variables_to_investigate",
    )
    _require_string_list(
        result["industry_to_company_transmission_questions"],
        "macro_transmission_path.industry_to_company_transmission_questions",
    )
    _require_string_list(
        result["required_evidence_for_transmission"],
        "macro_transmission_path.required_evidence_for_transmission",
    )
    result["data_gaps"] = [
        _validate_gap(gap, f"macro_transmission_path.data_gaps[{index}]")
        for index, gap in enumerate(result["data_gaps"])
    ]
    _require_string_list(result["caveats"], "macro_transmission_path.caveats")
    _require_true(result["not_for_trading_advice"], "macro_transmission_path.not_for_trading_advice")
    return result


def _validate_research_question_set(value: Any) -> dict[str, Any]:
    question_set = _require_mapping(value, "research_questions")
    _require_schema_version(
        question_set.get("schema_version"),
        RESEARCH_QUESTION_SET_SCHEMA_VERSION,
        "research_questions.schema_version",
    )
    questions = _require_list(question_set.get("questions"), "research_questions.questions")
    result_questions = [
        _validate_question(question, f"research_questions.questions[{index}]")
        for index, question in enumerate(questions)
    ]
    _require_true(question_set.get("not_for_trading_advice"), "research_questions.not_for_trading_advice")
    return {
        "schema_version": RESEARCH_QUESTION_SET_SCHEMA_VERSION,
        "questions": result_questions,
        "not_for_trading_advice": True,
    }


def _validate_data_gap_plan(value: Any) -> dict[str, Any]:
    plan = _require_mapping(value, "data_gap_plan")
    _require_schema_version(
        plan.get("schema_version"),
        DATA_GAP_PLAN_SCHEMA_VERSION,
        "data_gap_plan.schema_version",
    )
    gaps = _require_list(plan.get("data_gaps"), "data_gap_plan.data_gaps")
    next_tasks = _require_list(plan.get("next_data_tasks"), "data_gap_plan.next_data_tasks")
    blocked_reasons = _require_string_list(plan.get("blocked_reasons"), "data_gap_plan.blocked_reasons")
    result_gaps = [
        _validate_gap(gap, f"data_gap_plan.data_gaps[{index}]")
        for index, gap in enumerate(gaps)
    ]
    for index, task in enumerate(next_tasks):
        _validate_data_task(task, f"data_gap_plan.next_data_tasks[{index}]")
    _require_true(plan.get("not_for_trading_advice"), "data_gap_plan.not_for_trading_advice")
    return {
        "schema_version": DATA_GAP_PLAN_SCHEMA_VERSION,
        "data_gaps": result_gaps,
        "blocked_reasons": blocked_reasons,
        "next_data_tasks": deepcopy(next_tasks),
        "not_for_trading_advice": True,
    }


def _validate_evidence_status_summary(value: Any) -> dict[str, Any]:
    summary = _require_mapping(value, "evidence_status_summary")
    _require_schema_version(
        summary.get("schema_version"),
        EVIDENCE_STATUS_SUMMARY_SCHEMA_VERSION,
        "evidence_status_summary.schema_version",
    )
    _require_evidence_status_collection(summary.get("statuses_used"), "evidence_status_summary.statuses_used")
    _require_bool(
        summary.get("provider_candidate_financial_supplied"),
        "evidence_status_summary.provider_candidate_financial_supplied",
    )
    _require_bool(
        summary.get("verification_queue_supplied"),
        "evidence_status_summary.verification_queue_supplied",
    )
    _require_evidence_status_collection(
        summary.get("official_evidence_statuses"),
        "evidence_status_summary.official_evidence_statuses",
        allow_empty=True,
    )
    _require_bool(
        summary.get("has_explicit_official_evidence"),
        "evidence_status_summary.has_explicit_official_evidence",
    )
    _require_true(summary.get("not_for_trading_advice"), "evidence_status_summary.not_for_trading_advice")
    return deepcopy(dict(summary))


def _validate_metric_candidate(value: Any, path: str) -> dict[str, Any]:
    item = _require_mapping(value, path)
    required = (
        "period",
        "period_label",
        "ann_date",
        "end_date",
        "metric_key",
        "metric_value",
        "source_tables_available",
        "value_status",
        "current_evidence_status",
        "required_next_status",
        "not_for_trading_advice",
    )
    _require_fields(item, required, path)
    result = deepcopy(dict(item))
    _require_optional_string(result["period"], f"{path}.period")
    _require_optional_string(result["period_label"], f"{path}.period_label")
    _require_optional_string(result["ann_date"], f"{path}.ann_date")
    _require_optional_string(result["end_date"], f"{path}.end_date")
    _require_non_empty_string(result["metric_key"], f"{path}.metric_key")
    _require_string_list(result["source_tables_available"], f"{path}.source_tables_available")
    if result["value_status"] not in {"present", "missing"}:
        raise TickerResearchContextSkeletonError(f"{path}.value_status must be present or missing")
    _require_evidence_status(result["current_evidence_status"], f"{path}.current_evidence_status")
    _require_evidence_status(result["required_next_status"], f"{path}.required_next_status")
    if result["current_evidence_status"] == "official_verified":
        raise TickerResearchContextSkeletonError(f"{path}.current_evidence_status cannot be official_verified")
    _require_true(result["not_for_trading_advice"], f"{path}.not_for_trading_advice")
    return result


def _validate_framework(value: Any, path: str) -> dict[str, Any]:
    framework = _require_mapping(value, path)
    required = (
        "framework_id",
        "sub_type",
        "source",
        "current_evidence_status",
        "not_for_trading_advice",
    )
    _require_fields(framework, required, path)
    result = deepcopy(dict(framework))
    _require_non_empty_string(result["framework_id"], f"{path}.framework_id")
    _require_optional_string(result["sub_type"], f"{path}.sub_type")
    _require_non_empty_string(result["source"], f"{path}.source")
    _require_evidence_status(result["current_evidence_status"], f"{path}.current_evidence_status")
    _require_true(result["not_for_trading_advice"], f"{path}.not_for_trading_advice")
    return result


def _validate_question(value: Any, path: str) -> dict[str, Any]:
    question = _require_mapping(value, path)
    _require_fields(question, _RESEARCH_QUESTION_REQUIRED_FIELDS, path)
    result = deepcopy(dict(question))
    _require_non_empty_string(result["question_id"], f"{path}.question_id")
    _require_non_empty_string(result["category"], f"{path}.category")
    _require_non_empty_string(result["question_text"], f"{path}.question_text")
    _require_string_list(result["required_data"], f"{path}.required_data")
    _require_evidence_status(result["current_evidence_status"], f"{path}.current_evidence_status")
    if result["priority"] not in QUESTION_PRIORITIES:
        raise TickerResearchContextSkeletonError(f"{path}.priority must be one of {QUESTION_PRIORITIES}")
    _require_true(result["not_for_trading_advice"], f"{path}.not_for_trading_advice")
    return result


def _validate_gap(value: Any, path: str) -> dict[str, Any]:
    gap = _require_mapping(value, path)
    _require_fields(gap, _DATA_GAP_REQUIRED_FIELDS, path)
    result = deepcopy(dict(gap))
    _require_non_empty_string(result["gap_id"], f"{path}.gap_id")
    _require_non_empty_string(result["category"], f"{path}.category")
    _require_non_empty_string(result["description"], f"{path}.description")
    _require_string_list(result["required_data"], f"{path}.required_data")
    _require_evidence_status(result["current_evidence_status"], f"{path}.current_evidence_status")
    if result["priority"] not in QUESTION_PRIORITIES:
        raise TickerResearchContextSkeletonError(f"{path}.priority must be one of {QUESTION_PRIORITIES}")
    _require_true(result["not_for_trading_advice"], f"{path}.not_for_trading_advice")
    return result


def _validate_data_task(value: Any, path: str) -> dict[str, Any]:
    task = _require_mapping(value, path)
    required = (
        "task_id",
        "gap_id",
        "required_data",
        "current_evidence_status",
        "priority",
        "not_for_trading_advice",
    )
    _require_fields(task, required, path)
    _require_non_empty_string(task["task_id"], f"{path}.task_id")
    _require_non_empty_string(task["gap_id"], f"{path}.gap_id")
    _require_string_list(task["required_data"], f"{path}.required_data")
    _require_evidence_status(task["current_evidence_status"], f"{path}.current_evidence_status")
    if task["priority"] not in QUESTION_PRIORITIES:
        raise TickerResearchContextSkeletonError(f"{path}.priority must be one of {QUESTION_PRIORITIES}")
    _require_true(task["not_for_trading_advice"], f"{path}.not_for_trading_advice")
    return deepcopy(dict(task))


def _validate_evidence_status_values(value: Any) -> None:
    def visit(child: Any, path: str) -> None:
        if isinstance(child, Mapping):
            for key, nested in child.items():
                key_text = str(key)
                next_path = f"{path}.{key_text}" if path else key_text
                if key_text in {
                    "evidence_status",
                    "current_evidence_status",
                    "required_next_status",
                    "statuses_used",
                    "official_evidence_statuses",
                }:
                    _require_evidence_status_collection(
                        nested,
                        next_path,
                        allow_empty=key_text == "official_evidence_statuses",
                    )
                else:
                    visit(nested, next_path)
            return
        if isinstance(child, list):
            for index, item in enumerate(child):
                visit(item, f"{path}[{index}]")

    visit(value, "")


def _question(
    *,
    question_id: str,
    category: str,
    question_text: str,
    required_data: list[str],
    current_evidence_status: str,
    priority: str,
) -> dict[str, Any]:
    return {
        "question_id": question_id,
        "category": category,
        "question_text": question_text,
        "required_data": list(required_data),
        "current_evidence_status": current_evidence_status,
        "priority": priority,
        "not_for_trading_advice": True,
    }


def _gap(
    *,
    gap_id: str,
    category: str,
    description: str,
    required_data: list[str],
    current_evidence_status: str,
    priority: str,
) -> dict[str, Any]:
    return {
        "gap_id": gap_id,
        "category": category,
        "description": description,
        "required_data": list(required_data),
        "current_evidence_status": current_evidence_status,
        "priority": priority,
        "not_for_trading_advice": True,
    }


def _resolve_ts_code(payload: Mapping[str, Any]) -> str | None:
    for source in (
        payload,
        _provider_candidate_financial_result(payload) or {},
        _provider_candidate_verification_queue(payload) or {},
    ):
        value = source.get("ts_code") if isinstance(source, Mapping) else None
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _resolve_stock_code(payload: Mapping[str, Any]) -> str | None:
    for source in (
        payload,
        _provider_candidate_financial_result(payload) or {},
        _provider_candidate_verification_queue(payload) or {},
    ):
        value = source.get("stock_code") if isinstance(source, Mapping) else None
        if isinstance(value, str) and value.strip():
            return value.strip()
    ts_code = _resolve_ts_code(payload)
    if isinstance(ts_code, str) and re.fullmatch(r"\d{6}\.[A-Z]{2}", ts_code):
        return ts_code.split(".", 1)[0]
    return None


def _dominant_evidence_status(statuses: Iterable[Any]) -> str:
    rank = {
        "official_verified": 0,
        "provider_candidate": 1,
        "pending_official_verification": 2,
        "framework_inference": 3,
        "local_experiment": 4,
        "blocked": 5,
        "data_gap": 6,
        "not_assessable": 7,
    }
    valid = [status for status in _string_values(list(statuses)) if status in EVIDENCE_STATUSES]
    if not valid:
        return "not_assessable"
    return sorted(valid, key=lambda status: rank[status])[0]


def _evidence_statuses_from_mapping(value: Mapping[str, Any]) -> list[str]:
    statuses: list[str] = []
    for key in ("evidence_status", "current_evidence_status", "status"):
        statuses.extend(
            status
            for status in _string_values(value.get(key))
            if status in EVIDENCE_STATUSES
        )
    if value.get("official_verified") is True:
        statuses.append("official_verified")
    return _dedupe_preserve_order(statuses)


def _mapping_items(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, Mapping)]
    return []


def _normalise_explicit_items(value: Any) -> list[Any]:
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return deepcopy(value)
    if isinstance(value, tuple):
        return [deepcopy(item) for item in value]
    return [deepcopy(value)]


def _string_values(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, (list, tuple, set)):
        return [
            str(item).strip()
            for item in value
            if item not in (None, "") and str(item).strip()
        ]
    return [str(value).strip()] if str(value).strip() else []


def _string_list_from_mapping(value: Mapping[str, Any] | None, key: str) -> list[str]:
    if not isinstance(value, Mapping):
        return []
    return _string_values(value.get(key))


def _safe_string(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value).strip() or None


def _first_present(mapping: Mapping[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in mapping and mapping[key] not in (None, ""):
            return mapping[key]
    return None


def _first_status(value: Any) -> str:
    statuses = _string_values(value)
    return statuses[0] if statuses else "not_assessable"


def _dedupe_preserve_order(values: Iterable[Any]) -> list[Any]:
    result: list[Any] = []
    seen: set[str] = set()
    for value in values:
        marker = repr(value)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(value)
    return result


def _dedupe_frameworks(frameworks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str | None, str]] = set()
    for framework in frameworks:
        key = (
            framework["framework_id"],
            framework["sub_type"],
            framework["source"],
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(framework)
    return result


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TickerResearchContextSkeletonError(f"{field} must be a mapping")
    return value


def _require_fields(value: Mapping[str, Any], fields: tuple[str, ...], path: str) -> None:
    missing = [field for field in fields if field not in value]
    if missing:
        raise TickerResearchContextSkeletonError(f"{path} missing required fields: {missing}")


def _require_schema_version(value: Any, expected: str, path: str) -> None:
    if value != expected:
        raise TickerResearchContextSkeletonError(f"{path} must be {expected}")


def _require_optional_string(value: Any, path: str) -> None:
    if value is not None and not isinstance(value, str):
        raise TickerResearchContextSkeletonError(f"{path} must be a string or null")


def _require_non_empty_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TickerResearchContextSkeletonError(f"{path} must be a non-empty string")
    return value


def _require_string_list(value: Any, path: str) -> list[str]:
    if not isinstance(value, list):
        raise TickerResearchContextSkeletonError(f"{path} must be a list")
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise TickerResearchContextSkeletonError(f"{path}[{index}] must be a string")
    return value


def _require_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise TickerResearchContextSkeletonError(f"{path} must be a list")
    return value


def _require_bool(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise TickerResearchContextSkeletonError(f"{path} must be a bool")
    return value


def _require_true(value: Any, path: str) -> None:
    if value is not True:
        raise TickerResearchContextSkeletonError(f"{path} must be true")


def _require_non_negative_int(value: Any, path: str) -> int:
    if not isinstance(value, int) or value < 0:
        raise TickerResearchContextSkeletonError(f"{path} must be a non-negative int")
    return value


def _require_evidence_status(value: Any, path: str) -> str:
    if not isinstance(value, str) or value not in EVIDENCE_STATUSES:
        raise TickerResearchContextSkeletonError(f"{path} must be one of {EVIDENCE_STATUSES}")
    return value


def _require_evidence_status_collection(
    value: Any,
    path: str,
    *,
    allow_empty: bool = False,
) -> list[str] | str:
    if isinstance(value, str):
        return _require_evidence_status(value, path)
    if not isinstance(value, list):
        raise TickerResearchContextSkeletonError(f"{path} must be an evidence status or list")
    if not value and not allow_empty:
        raise TickerResearchContextSkeletonError(f"{path} cannot be empty")
    for index, item in enumerate(value):
        _require_evidence_status(item, f"{path}[{index}]")
    return value


def _find_forbidden_marker(value: Any, *, allow_evidence_status: bool = False) -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text not in _ALLOWED_EXACT_KEYS:
                key_finding = _text_forbidden_marker(key_text, allow_evidence_status=False)
                if key_finding:
                    return key_finding
            child_finding = _find_forbidden_marker(
                child,
                allow_evidence_status=key_text in _EVIDENCE_STATUS_FIELD_KEYS,
            )
            if child_finding:
                return child_finding
        return None
    if isinstance(value, (list, tuple, set)):
        for item in value:
            item_finding = _find_forbidden_marker(
                item,
                allow_evidence_status=allow_evidence_status,
            )
            if item_finding:
                return item_finding
        return None
    if isinstance(value, str):
        return _text_forbidden_marker(value, allow_evidence_status=allow_evidence_status)
    return None


def _text_forbidden_marker(value: str, *, allow_evidence_status: bool) -> str | None:
    if allow_evidence_status and value in EVIDENCE_STATUSES:
        return None
    if value in EVIDENCE_STATUSES and value != "official_verified":
        return None
    if _contains_official_verified_text(value):
        return "official_verified"
    lowered = value.casefold()
    separator_normalized = _normalize_separator_text(value)
    normalized_marker = _normalise_marker(value)

    for marker in _FORBIDDEN_MARKERS:
        marker_lower = marker.casefold()
        marker_separator = _normalize_separator_text(marker)
        marker_normalized = _normalise_marker(marker)
        if marker_lower == ".env":
            if ".env" in lowered:
                return "forbidden_marker"
            continue
        if marker_normalized in _WORD_MARKERS:
            boundary_chars = (
                "a-z0-9_"
                if marker_normalized in _IDENTIFIER_SAFE_WORD_MARKERS
                else "a-z0-9"
            )
            if re.search(
                rf"(?<![{boundary_chars}]){re.escape(marker_normalized)}(?![{boundary_chars}])",
                normalized_marker,
            ):
                return "forbidden_marker"
            continue
        if (
            marker_lower in lowered
            or marker_separator in separator_normalized
            or marker_normalized in normalized_marker
        ):
            return "forbidden_marker"
    if any(marker in value for marker in _FORBIDDEN_CJK_MARKERS):
        return "forbidden_marker"
    return None


def _normalise_marker(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().casefold()).strip("_")


def _normalize_separator_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[_-]+", " ", value.strip().casefold())).strip()


__all__ = [
    "COMPANY_BUSINESS_PROFILE_SCHEMA_VERSION",
    "DATA_GAP_PLAN_SCHEMA_VERSION",
    "EVIDENCE_STATUSES",
    "INDUSTRY_CONTEXT_SCHEMA_VERSION",
    "MACRO_TRANSMISSION_PATH_SCHEMA_VERSION",
    "RESEARCH_QUESTION_SET_SCHEMA_VERSION",
    "TICKER_RESEARCH_CONTEXT_SCHEMA_VERSION",
    "TickerResearchContextSkeletonError",
    "assert_no_research_context_forbidden_markers",
    "build_company_business_context_seed",
    "build_financial_context_from_provider_candidate",
    "build_industry_context_seed",
    "build_macro_transmission_prompt_seed",
    "build_research_question_set",
    "build_ticker_research_context_skeleton",
    "validate_ticker_research_context_skeleton",
]
