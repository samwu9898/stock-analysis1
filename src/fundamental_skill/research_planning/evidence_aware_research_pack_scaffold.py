# -*- coding: utf-8 -*-
"""Evidence-aware research pack scaffold builder.

This module assembles a validated ticker research context skeleton into a
structured, evidence-constrained scaffold. It does not read files, fetch data,
write artifacts, generate reports, or make analyst conclusions.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
import re
from typing import Any

from .ticker_research_context_skeleton import (
    EVIDENCE_STATUSES,
    TICKER_RESEARCH_CONTEXT_SCHEMA_VERSION,
    validate_ticker_research_context_skeleton,
)


EVIDENCE_AWARE_RESEARCH_PACK_SCAFFOLD_SCHEMA_VERSION = (
    "evidence_aware_research_pack_scaffold.v1"
)
EVIDENCE_AWARE_RESEARCH_PACK_SECTION_SCHEMA_VERSION = (
    "evidence_aware_research_pack_section.v1"
)
EVIDENCE_STATUS_LEGEND_SCHEMA_VERSION = "evidence_status_legend.v1"

SECTION_IDS = (
    "research_subject",
    "company_business_profile",
    "financial_context",
    "industry_context",
    "macro_transmission",
    "official_verification",
    "data_gaps",
    "research_questions",
)

_TOP_LEVEL_REQUIRED_FIELDS = (
    "schema_version",
    "ts_code",
    "stock_code",
    "company_name_hint",
    "source_context_schema_version",
    "sections",
    "evidence_status_legend",
    "global_limitations",
    "next_data_tasks",
    "blocked_reasons",
    "caveats",
    "not_for_trading_advice",
)

_SECTION_REQUIRED_FIELDS = (
    "schema_version",
    "section_id",
    "section_title",
    "source_component",
    "evidence_status",
    "items",
    "limitations",
    "next_data_tasks",
    "caveats",
    "not_for_trading_advice",
)

_DATA_TASK_REQUIRED_FIELDS = (
    "task_id",
    "gap_id",
    "required_data",
    "current_evidence_status",
    "priority",
    "not_for_trading_advice",
)

_LEGEND_ENTRY_REQUIRED_FIELDS = (
    "status",
    "meaning",
    "scaffold_rule",
    "not_for_trading_advice",
)

_RAW_PAYLOAD_TOP_LEVEL_KEYS = {
    "provider_candidate_financial_result",
    "provider_candidate_financial_snapshot",
    "provider_candidate_financial_trend_table",
    "provider_candidate_metric_verification_queue",
    "business_composition_evidence",
    "business_profile",
    "official_anchor_candidates",
    "official_metadata_candidates",
    "evidence_pack_summary",
    "industry_framework_hint",
    "business_segments",
    "main_products",
    "revenue_structure",
    "downstream_or_end_markets",
    "business_evidence_status",
    "strategy_type",
    "sub_type",
    "industry_tags",
}

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
    "status",
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
    "company benefits",
    "macro tailwind",
    "macro headwind",
    "industry boom",
    "investment thesis",
    "core investment logic",
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
    "\u516c\u53f8\u53d7\u76ca",
    "\u884c\u4e1a\u666f\u6c14",
    "\u6838\u5fc3\u6295\u8d44\u903b\u8f91\u6210\u7acb",
    "\u5b8f\u89c2\u5229\u597d",
    "\u5b8f\u89c2\u5229\u7a7a",
)

_WORD_MARKERS = {"token", "buy", "sell", "hold", "portfolio", "position"}
_IDENTIFIER_SAFE_WORD_MARKERS = {"buy", "sell", "hold"}


class EvidenceAwareResearchPackScaffoldError(ValueError):
    """Raised when an evidence-aware scaffold fails closed."""


def build_evidence_aware_research_pack_scaffold(
    context_skeleton: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a scaffold from a validated ticker research context skeleton."""

    context = _validated_context_copy(context_skeleton)
    sections = [
        _build_research_subject_section_from_context(context),
        _build_company_business_profile_section_from_context(context),
        _build_financial_context_section_from_context(context),
        _build_industry_context_section_from_context(context),
        _build_macro_transmission_section_from_context(context),
        _build_official_verification_section_from_context(context),
        _build_data_gap_section_from_context(context),
        _build_research_questions_section_from_context(context),
    ]
    data_gap_plan = context["data_gap_plan"]
    scaffold = {
        "schema_version": EVIDENCE_AWARE_RESEARCH_PACK_SCAFFOLD_SCHEMA_VERSION,
        "ts_code": context["ts_code"],
        "stock_code": context["stock_code"],
        "company_name_hint": context["company_name_hint"],
        "source_context_schema_version": context["schema_version"],
        "sections": sections,
        "evidence_status_legend": _build_evidence_status_legend_from_context(context),
        "global_limitations": [
            "Scaffold content is copied from the validated context skeleton.",
            "Provider candidate metrics remain candidate records until official checks are supplied.",
            "Sections organize evidence status and open tasks only.",
        ],
        "next_data_tasks": deepcopy(data_gap_plan["next_data_tasks"]),
        "blocked_reasons": list(data_gap_plan["blocked_reasons"]),
        "caveats": [
            "This scaffold does not fetch provider data or local artifacts.",
            "This scaffold does not produce analyst conclusions.",
        ],
        "not_for_trading_advice": True,
    }
    return validate_evidence_aware_research_pack_scaffold(scaffold)


def build_research_subject_section(context_skeleton: Mapping[str, Any]) -> dict[str, Any]:
    """Build the research subject section from the validated context skeleton."""

    return _build_research_subject_section_from_context(_validated_context_copy(context_skeleton))


def build_company_business_profile_section(
    context_skeleton: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the company business profile scaffold section."""

    return _build_company_business_profile_section_from_context(
        _validated_context_copy(context_skeleton)
    )


def build_financial_context_section(context_skeleton: Mapping[str, Any]) -> dict[str, Any]:
    """Build the financial context scaffold section."""

    return _build_financial_context_section_from_context(_validated_context_copy(context_skeleton))


def build_industry_context_section(context_skeleton: Mapping[str, Any]) -> dict[str, Any]:
    """Build the industry context scaffold section."""

    return _build_industry_context_section_from_context(_validated_context_copy(context_skeleton))


def build_macro_transmission_section(context_skeleton: Mapping[str, Any]) -> dict[str, Any]:
    """Build the macro transmission scaffold section."""

    return _build_macro_transmission_section_from_context(_validated_context_copy(context_skeleton))


def build_official_verification_section(
    context_skeleton: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the official verification scaffold section."""

    return _build_official_verification_section_from_context(
        _validated_context_copy(context_skeleton)
    )


def build_data_gap_section(context_skeleton: Mapping[str, Any]) -> dict[str, Any]:
    """Build the data gap scaffold section."""

    return _build_data_gap_section_from_context(_validated_context_copy(context_skeleton))


def build_research_questions_section(context_skeleton: Mapping[str, Any]) -> dict[str, Any]:
    """Build the research questions scaffold section."""

    return _build_research_questions_section_from_context(_validated_context_copy(context_skeleton))


def build_evidence_status_legend(context_skeleton: Mapping[str, Any]) -> dict[str, Any]:
    """Build the fixed evidence status legend after validating the input contract."""

    return _build_evidence_status_legend_from_context(_validated_context_copy(context_skeleton))


def validate_evidence_aware_research_pack_scaffold(
    scaffold: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate and return a defensive copy of an evidence-aware scaffold."""

    assert_no_research_pack_scaffold_forbidden_markers(scaffold)
    source = _require_mapping(scaffold, "evidence_aware_research_pack_scaffold")
    _require_fields(source, _TOP_LEVEL_REQUIRED_FIELDS, "evidence_aware_research_pack_scaffold")
    result = deepcopy(dict(source))

    _require_schema_version(
        result["schema_version"],
        EVIDENCE_AWARE_RESEARCH_PACK_SCAFFOLD_SCHEMA_VERSION,
        "schema_version",
    )
    _require_optional_string(result["ts_code"], "ts_code")
    _require_optional_string(result["stock_code"], "stock_code")
    _require_optional_string(result["company_name_hint"], "company_name_hint")
    _require_schema_version(
        result["source_context_schema_version"],
        TICKER_RESEARCH_CONTEXT_SCHEMA_VERSION,
        "source_context_schema_version",
    )
    _require_true(result["not_for_trading_advice"], "not_for_trading_advice")
    _require_string_list(result["global_limitations"], "global_limitations")
    _require_string_list(result["blocked_reasons"], "blocked_reasons")
    _require_string_list(result["caveats"], "caveats")

    next_data_tasks = _require_list(result["next_data_tasks"], "next_data_tasks")
    for index, task in enumerate(next_data_tasks):
        _validate_data_task(task, f"next_data_tasks[{index}]")

    sections = _require_list(result["sections"], "sections")
    result["sections"] = [
        _validate_section(section, f"sections[{index}]")
        for index, section in enumerate(sections)
    ]
    section_ids = [section["section_id"] for section in result["sections"]]
    if tuple(section_ids) != SECTION_IDS:
        raise EvidenceAwareResearchPackScaffoldError(
            f"sections must be ordered as {SECTION_IDS}"
        )

    result["evidence_status_legend"] = _validate_evidence_status_legend(
        result["evidence_status_legend"]
    )
    _validate_evidence_status_values(result)
    _assert_financial_section_not_official_verified(result)
    _assert_pending_items_not_official_verified(result)
    return result


def assert_no_research_pack_scaffold_forbidden_markers(value: Any) -> None:
    """Reject blocked markers in nested scaffold keys and values."""

    finding = _find_forbidden_marker(value)
    if finding:
        raise EvidenceAwareResearchPackScaffoldError(
            f"research pack scaffold safety violation: forbidden marker: {finding}"
        )


def _build_research_subject_section_from_context(context: Mapping[str, Any]) -> dict[str, Any]:
    summary = context["evidence_status_summary"]
    evidence_status = _non_empty_status_collection(summary["statuses_used"], "data_gap")
    items = [
        {
            "item_id": "subject_identity",
            "ts_code": context["ts_code"],
            "stock_code": context["stock_code"],
            "company_name_hint": context["company_name_hint"],
            "current_evidence_status": _first_status(evidence_status),
            "not_for_trading_advice": True,
        },
        {
            "item_id": "evidence_status_summary",
            "statuses_used": list(summary["statuses_used"]),
            "provider_candidate_financial_supplied": summary[
                "provider_candidate_financial_supplied"
            ],
            "verification_queue_supplied": summary["verification_queue_supplied"],
            "official_evidence_statuses": list(summary["official_evidence_statuses"]),
            "has_explicit_official_evidence": summary["has_explicit_official_evidence"],
            "not_for_trading_advice": True,
        },
    ]
    return _section(
        section_id="research_subject",
        section_title="Research subject",
        source_component="evidence_status_summary",
        evidence_status=evidence_status,
        items=items,
        limitations=[
            "Subject identifiers are copied from the validated context skeleton.",
            "Evidence status summary is descriptive and does not evaluate the company.",
        ],
        next_data_tasks=[],
        caveats=list(context["caveats"]),
    )


def _build_company_business_profile_section_from_context(
    context: Mapping[str, Any],
) -> dict[str, Any]:
    profile = context["company_business_profile"]
    evidence_status = profile["evidence_status"]
    items = [
        _profile_field_item(
            "business_segments",
            profile["business_segments"],
            evidence_status,
            profile["data_gaps"],
        ),
        _profile_field_item(
            "main_products",
            profile["main_products"],
            evidence_status,
            profile["data_gaps"],
        ),
        _profile_field_item(
            "revenue_structure",
            profile["revenue_structure"],
            evidence_status,
            profile["data_gaps"],
        ),
        _profile_field_item(
            "downstream_or_end_markets",
            profile["downstream_or_end_markets"],
            evidence_status,
            profile["data_gaps"],
        ),
        {
            "item_id": "company_business_data_gaps",
            "data_gaps": deepcopy(profile["data_gaps"]),
            "current_evidence_status": "data_gap"
            if profile["data_gaps"]
            else evidence_status,
            "not_for_trading_advice": True,
        },
    ]
    return _section(
        section_id="company_business_profile",
        section_title="Company business profile",
        source_component="company_business_profile",
        evidence_status=evidence_status,
        items=items,
        limitations=[
            "Empty business fields are shown as data gaps.",
            "Financial metrics are not used to infer business composition.",
        ],
        next_data_tasks=_tasks_from_gaps(profile["data_gaps"], "company_business"),
        caveats=list(profile["caveats"]),
    )


def _build_financial_context_section_from_context(context: Mapping[str, Any]) -> dict[str, Any]:
    financial = context["financial_context"]
    evidence_status = _non_empty_status_collection(financial["evidence_status"], "data_gap")
    metric_summaries = [
        {
            "period": item["period"],
            "period_label": item["period_label"],
            "metric_key": item["metric_key"],
            "metric_value": deepcopy(item["metric_value"]),
            "value_status": item["value_status"],
            "source_tables_available": list(item["source_tables_available"]),
            "current_evidence_status": item["current_evidence_status"],
            "required_next_status": item["required_next_status"],
            "not_for_trading_advice": True,
        }
        for item in financial["key_metric_candidates"]
    ]
    items = [
        {
            "item_id": "provider_trend_periods",
            "provider_trend_periods": list(financial["provider_trend_periods"]),
            "current_evidence_status": _first_status(evidence_status),
            "not_for_trading_advice": True,
        },
        {
            "item_id": "key_metric_candidates",
            "key_metric_candidates": metric_summaries,
            "current_evidence_status": "provider_candidate"
            if metric_summaries
            else "data_gap",
            "not_for_trading_advice": True,
        },
        {
            "item_id": "verification_and_missing_counts",
            "pending_official_verification_count": financial[
                "pending_official_verification_count"
            ],
            "missing_metric_count": financial["missing_metric_count"],
            "current_evidence_status": "pending_official_verification"
            if financial["pending_official_verification_count"]
            else _first_status(evidence_status),
            "not_for_trading_advice": True,
        },
        {
            "item_id": "financial_data_gaps",
            "data_gaps": deepcopy(financial["data_gaps"]),
            "current_evidence_status": "data_gap"
            if financial["data_gaps"]
            else _first_status(evidence_status),
            "not_for_trading_advice": True,
        },
    ]
    return _section(
        section_id="financial_context",
        section_title="Financial context",
        source_component="financial_context",
        evidence_status=evidence_status,
        items=items,
        limitations=[
            "Provider values remain candidate records.",
            "Official checks are outside this scaffold.",
        ],
        next_data_tasks=_tasks_from_gaps(financial["data_gaps"], "financial"),
        caveats=list(financial["caveats"]),
    )


def _build_industry_context_section_from_context(context: Mapping[str, Any]) -> dict[str, Any]:
    industry = context["industry_context"]
    evidence_status = industry["evidence_status"]
    items = [
        {
            "item_id": "industry_classification_inputs",
            "strategy_type": industry["strategy_type"],
            "sub_type": industry["sub_type"],
            "industry_tags": list(industry["industry_tags"]),
            "current_evidence_status": evidence_status,
            "not_for_trading_advice": True,
        },
        {
            "item_id": "possible_industry_frameworks",
            "possible_industry_frameworks": deepcopy(industry["possible_industry_frameworks"]),
            "current_evidence_status": evidence_status,
            "not_for_trading_advice": True,
        },
        {
            "item_id": "industry_driver_questions",
            "industry_driver_questions": list(industry["industry_driver_questions"]),
            "current_evidence_status": evidence_status,
            "not_for_trading_advice": True,
        },
        {
            "item_id": "industry_data_gaps",
            "industry_data_gaps": deepcopy(industry["industry_data_gaps"]),
            "current_evidence_status": "data_gap"
            if industry["industry_data_gaps"]
            else evidence_status,
            "not_for_trading_advice": True,
        },
    ]
    return _section(
        section_id="industry_context",
        section_title="Industry context",
        source_component="industry_context",
        evidence_status=evidence_status,
        items=items,
        limitations=[
            "Framework labels are input context, not industry facts.",
            "No default framework is introduced by this scaffold.",
        ],
        next_data_tasks=_tasks_from_gaps(industry["industry_data_gaps"], "industry"),
        caveats=[],
    )


def _build_macro_transmission_section_from_context(context: Mapping[str, Any]) -> dict[str, Any]:
    macro_path = context["macro_transmission_path"]
    evidence_status = _macro_transmission_status(context)
    items = [
        {
            "item_id": "macro_variables_to_investigate",
            "macro_variables_to_investigate": list(
                macro_path["macro_variables_to_investigate"]
            ),
            "current_evidence_status": evidence_status,
            "not_for_trading_advice": True,
        },
        {
            "item_id": "industry_to_company_transmission_questions",
            "industry_to_company_transmission_questions": list(
                macro_path["industry_to_company_transmission_questions"]
            ),
            "current_evidence_status": evidence_status,
            "not_for_trading_advice": True,
        },
        {
            "item_id": "required_evidence_for_transmission",
            "required_evidence_for_transmission": list(
                macro_path["required_evidence_for_transmission"]
            ),
            "current_evidence_status": evidence_status,
            "not_for_trading_advice": True,
        },
        {
            "item_id": "macro_transmission_data_gaps",
            "data_gaps": deepcopy(macro_path["data_gaps"]),
            "current_evidence_status": "data_gap"
            if macro_path["data_gaps"]
            else evidence_status,
            "not_for_trading_advice": True,
        },
    ]
    return _section(
        section_id="macro_transmission",
        section_title="Macro transmission",
        source_component="macro_transmission_path",
        evidence_status=evidence_status,
        items=items,
        limitations=[
            "Macro path contains questions and evidence needs only.",
            "No directional macro impact is stated.",
        ],
        next_data_tasks=_tasks_from_gaps(macro_path["data_gaps"], "macro"),
        caveats=list(macro_path["caveats"]),
    )


def _build_official_verification_section_from_context(
    context: Mapping[str, Any],
) -> dict[str, Any]:
    financial = context["financial_context"]
    summary = context["evidence_status_summary"]
    pending_count = financial["pending_official_verification_count"]
    explicit_statuses = list(summary["official_evidence_statuses"])
    status_values: list[str] = []
    if pending_count:
        status_values.append("pending_official_verification")
    status_values.extend(explicit_statuses)
    evidence_status = _non_empty_status_collection(status_values, "data_gap")
    pending_status = "pending_official_verification" if pending_count else "data_gap"
    items = [
        {
            "item_id": "pending_official_verification_count",
            "pending_official_verification_count": pending_count,
            "current_evidence_status": pending_status,
            "not_for_trading_advice": True,
        },
        {
            "item_id": "explicit_official_evidence_presence",
            "has_explicit_official_evidence": summary["has_explicit_official_evidence"],
            "official_evidence_statuses": explicit_statuses,
            "current_evidence_status": "official_verified"
            if summary["has_explicit_official_evidence"]
            else "data_gap",
            "not_for_trading_advice": True,
        },
    ]
    next_data_tasks = [
        {
            "task_id": "official_anchor_mapping",
            "description": "Map pending provider metrics to official disclosure anchors.",
            "required_data": ["official disclosure anchors for pending metrics"],
            "current_evidence_status": pending_status,
            "priority": "high" if pending_count else "medium",
            "not_for_trading_advice": True,
        },
        {
            "task_id": "official_evidence_extraction",
            "description": "Extract official disclosure evidence for queued metrics.",
            "required_data": ["official disclosure evidence for queued metrics"],
            "current_evidence_status": pending_status,
            "priority": "high" if pending_count else "medium",
            "not_for_trading_advice": True,
        },
    ]
    return _section(
        section_id="official_verification",
        section_title="Official verification",
        source_component="financial_context + evidence_status_summary",
        evidence_status=evidence_status,
        items=items,
        limitations=[
            "Queued items remain pending until explicit official evidence is supplied.",
            "This scaffold records verification needs only.",
        ],
        next_data_tasks=next_data_tasks,
        caveats=[
            "No derived official records are produced.",
            "No conflict review record is produced.",
        ],
    )


def _build_data_gap_section_from_context(context: Mapping[str, Any]) -> dict[str, Any]:
    plan = context["data_gap_plan"]
    evidence_status = "data_gap"
    items = [
        {
            "item_id": "data_gaps",
            "data_gaps": deepcopy(plan["data_gaps"]),
            "current_evidence_status": evidence_status,
            "not_for_trading_advice": True,
        },
        {
            "item_id": "next_data_tasks",
            "next_data_tasks": deepcopy(plan["next_data_tasks"]),
            "current_evidence_status": evidence_status,
            "not_for_trading_advice": True,
        },
        {
            "item_id": "blocked_reasons",
            "blocked_reasons": list(plan["blocked_reasons"]),
            "current_evidence_status": "blocked"
            if plan["blocked_reasons"]
            else evidence_status,
            "not_for_trading_advice": True,
        },
    ]
    return _section(
        section_id="data_gaps",
        section_title="Data gaps",
        source_component="data_gap_plan",
        evidence_status=evidence_status,
        items=items,
        limitations=[
            "High-priority gaps are copied from the context skeleton.",
            "Gap severity is not hidden or softened.",
        ],
        next_data_tasks=deepcopy(plan["next_data_tasks"]),
        caveats=[],
    )


def _build_research_questions_section_from_context(
    context: Mapping[str, Any],
) -> dict[str, Any]:
    question_set = context["research_questions"]
    questions = [
        {
            "question_id": question["question_id"],
            "category": question["category"],
            "question_text": question["question_text"],
            "required_data": list(question["required_data"]),
            "current_evidence_status": question["current_evidence_status"],
            "priority": question["priority"],
            "not_for_trading_advice": True,
        }
        for question in question_set["questions"]
    ]
    evidence_status = _non_empty_status_collection(
        _dedupe_preserve_order(question["current_evidence_status"] for question in questions),
        "data_gap",
    )
    return _section(
        section_id="research_questions",
        section_title="Research questions",
        source_component="research_questions",
        evidence_status=evidence_status,
        items=questions,
        limitations=[
            "Questions remain open research tasks.",
            "Question text is not rewritten into proof language.",
        ],
        next_data_tasks=[],
        caveats=[],
    )


def _build_evidence_status_legend_from_context(context: Mapping[str, Any]) -> dict[str, Any]:
    del context
    meanings = {
        "official_verified": "Explicit official source evidence exists in the validated context.",
        "provider_candidate": "A provider-supplied candidate record is present.",
        "pending_official_verification": "A candidate item still needs official source checking.",
        "framework_inference": "A framework or question was organized from supplied context.",
        "local_experiment": "A local experiment status was supplied by the context.",
        "data_gap": "Required evidence is missing or incomplete.",
        "blocked": "Progress is blocked by missing required evidence.",
        "not_assessable": "The component cannot yet be assessed from supplied context.",
    }
    rules = {
        "official_verified": "May appear only as an explicit context status or legend label.",
        "provider_candidate": "Must not be elevated by this scaffold.",
        "pending_official_verification": "Must remain pending until official evidence is supplied.",
        "framework_inference": "May frame questions but not facts.",
        "local_experiment": "May be copied only if supplied by the context.",
        "data_gap": "Must be shown when source components expose missing evidence.",
        "blocked": "Must be shown when the data gap plan exposes blockers.",
        "not_assessable": "Must be shown when a source component cannot be assessed.",
    }
    return {
        "schema_version": EVIDENCE_STATUS_LEGEND_SCHEMA_VERSION,
        "entries": [
            {
                "status": status,
                "meaning": meanings[status],
                "scaffold_rule": rules[status],
                "not_for_trading_advice": True,
            }
            for status in EVIDENCE_STATUSES
        ],
        "not_for_trading_advice": True,
    }


def _section(
    *,
    section_id: str,
    section_title: str,
    source_component: str,
    evidence_status: str | list[str],
    items: list[Mapping[str, Any]],
    limitations: list[str],
    next_data_tasks: list[Mapping[str, Any]],
    caveats: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": EVIDENCE_AWARE_RESEARCH_PACK_SECTION_SCHEMA_VERSION,
        "section_id": section_id,
        "section_title": section_title,
        "source_component": source_component,
        "evidence_status": deepcopy(evidence_status),
        "items": deepcopy(items),
        "limitations": list(limitations),
        "next_data_tasks": deepcopy(next_data_tasks),
        "caveats": list(caveats),
        "not_for_trading_advice": True,
    }


def _profile_field_item(
    item_id: str,
    value: list[Any],
    component_status: str,
    data_gaps: list[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "item_id": item_id,
        "value": deepcopy(value),
        "data_gap_displayed": not bool(value),
        "current_evidence_status": component_status
        if value
        else ("data_gap" if data_gaps else component_status),
        "not_for_trading_advice": True,
    }


def _tasks_from_gaps(
    gaps: Iterable[Mapping[str, Any]],
    prefix: str,
) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for index, gap in enumerate(gaps):
        tasks.append(
            {
                "task_id": f"{prefix}_task_{index + 1:03d}",
                "gap_id": str(gap["gap_id"]),
                "required_data": list(gap["required_data"]),
                "current_evidence_status": gap["current_evidence_status"],
                "priority": gap["priority"],
                "not_for_trading_advice": True,
            }
        )
    return tasks


def _macro_transmission_status(context: Mapping[str, Any]) -> str:
    macro_path = context["macro_transmission_path"]
    if macro_path["data_gaps"]:
        return str(macro_path["data_gaps"][0]["current_evidence_status"])
    for question in context["research_questions"]["questions"]:
        if question["category"] == "macro_transmission":
            return str(question["current_evidence_status"])
    return "framework_inference"


def _validated_context_copy(context_skeleton: Mapping[str, Any]) -> dict[str, Any]:
    source = _require_mapping(context_skeleton, "context_skeleton")
    _reject_raw_payload_keys(source)
    validated = validate_ticker_research_context_skeleton(source)
    _reject_raw_payload_keys(validated)
    if validated["schema_version"] != TICKER_RESEARCH_CONTEXT_SCHEMA_VERSION:
        raise EvidenceAwareResearchPackScaffoldError(
            "context_skeleton must be ticker_research_context_skeleton.v1"
        )
    return deepcopy(validated)


def _reject_raw_payload_keys(value: Mapping[str, Any]) -> None:
    raw_keys = sorted(key for key in _RAW_PAYLOAD_TOP_LEVEL_KEYS if key in value)
    if raw_keys:
        raise EvidenceAwareResearchPackScaffoldError(
            f"context_skeleton contains raw payload keys: {raw_keys}"
        )


def _validate_section(value: Any, path: str) -> dict[str, Any]:
    section = _require_mapping(value, path)
    _require_fields(section, _SECTION_REQUIRED_FIELDS, path)
    result = deepcopy(dict(section))
    _require_schema_version(
        result["schema_version"],
        EVIDENCE_AWARE_RESEARCH_PACK_SECTION_SCHEMA_VERSION,
        f"{path}.schema_version",
    )
    if result["section_id"] not in SECTION_IDS:
        raise EvidenceAwareResearchPackScaffoldError(f"{path}.section_id is invalid")
    _require_non_empty_string(result["section_title"], f"{path}.section_title")
    _require_non_empty_string(result["source_component"], f"{path}.source_component")
    _require_evidence_status_collection(result["evidence_status"], f"{path}.evidence_status")
    items = _require_list(result["items"], f"{path}.items")
    for index, item in enumerate(items):
        _require_mapping(item, f"{path}.items[{index}]")
    _require_string_list(result["limitations"], f"{path}.limitations")
    tasks = _require_list(result["next_data_tasks"], f"{path}.next_data_tasks")
    for index, task in enumerate(tasks):
        _require_mapping(task, f"{path}.next_data_tasks[{index}]")
    _require_string_list(result["caveats"], f"{path}.caveats")
    _require_true(result["not_for_trading_advice"], f"{path}.not_for_trading_advice")
    return result


def _validate_evidence_status_legend(value: Any) -> dict[str, Any]:
    legend = _require_mapping(value, "evidence_status_legend")
    _require_schema_version(
        legend.get("schema_version"),
        EVIDENCE_STATUS_LEGEND_SCHEMA_VERSION,
        "evidence_status_legend.schema_version",
    )
    entries = _require_list(legend.get("entries"), "evidence_status_legend.entries")
    result_entries = []
    for index, entry in enumerate(entries):
        path = f"evidence_status_legend.entries[{index}]"
        mapping = _require_mapping(entry, path)
        _require_fields(mapping, _LEGEND_ENTRY_REQUIRED_FIELDS, path)
        result_entry = deepcopy(dict(mapping))
        _require_evidence_status(result_entry["status"], f"{path}.status")
        _require_non_empty_string(result_entry["meaning"], f"{path}.meaning")
        _require_non_empty_string(result_entry["scaffold_rule"], f"{path}.scaffold_rule")
        _require_true(result_entry["not_for_trading_advice"], f"{path}.not_for_trading_advice")
        result_entries.append(result_entry)
    statuses = [entry["status"] for entry in result_entries]
    if tuple(statuses) != EVIDENCE_STATUSES:
        raise EvidenceAwareResearchPackScaffoldError(
            "evidence_status_legend must include all evidence statuses in order"
        )
    _require_true(legend.get("not_for_trading_advice"), "evidence_status_legend.not_for_trading_advice")
    return {
        "schema_version": EVIDENCE_STATUS_LEGEND_SCHEMA_VERSION,
        "entries": result_entries,
        "not_for_trading_advice": True,
    }


def _validate_data_task(value: Any, path: str) -> dict[str, Any]:
    task = _require_mapping(value, path)
    _require_fields(task, _DATA_TASK_REQUIRED_FIELDS, path)
    result = deepcopy(dict(task))
    _require_non_empty_string(result["task_id"], f"{path}.task_id")
    _require_non_empty_string(result["gap_id"], f"{path}.gap_id")
    _require_string_list(result["required_data"], f"{path}.required_data")
    _require_evidence_status(result["current_evidence_status"], f"{path}.current_evidence_status")
    if result["priority"] not in {"high", "medium", "low"}:
        raise EvidenceAwareResearchPackScaffoldError(
            f"{path}.priority must be high, medium, or low"
        )
    _require_true(result["not_for_trading_advice"], f"{path}.not_for_trading_advice")
    return result


def _validate_evidence_status_values(value: Any) -> None:
    def visit(child: Any, path: str) -> None:
        if isinstance(child, Mapping):
            for key, nested in child.items():
                key_text = str(key)
                next_path = f"{path}.{key_text}" if path else key_text
                if key_text in _EVIDENCE_STATUS_FIELD_KEYS:
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


def _assert_financial_section_not_official_verified(scaffold: Mapping[str, Any]) -> None:
    for section in scaffold["sections"]:
        if section["section_id"] == "financial_context" and _status_value_present(
            section, "official_verified"
        ):
            raise EvidenceAwareResearchPackScaffoldError(
                "financial context section cannot claim official_verified"
            )


def _assert_pending_items_not_official_verified(scaffold: Mapping[str, Any]) -> None:
    for section in scaffold["sections"]:
        for item in section["items"]:
            item_id = str(item.get("item_id", ""))
            if (
                "pending_official_verification" in item_id
                and item.get("current_evidence_status") == "official_verified"
            ):
                raise EvidenceAwareResearchPackScaffoldError(
                    "pending verification item cannot become official_verified"
                )


def _status_value_present(value: Any, target: str) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in _EVIDENCE_STATUS_FIELD_KEYS and _status_value_present(child, target):
                return True
            if key not in _EVIDENCE_STATUS_FIELD_KEYS and _status_value_present(child, target):
                return True
        return False
    if isinstance(value, list):
        return any(_status_value_present(item, target) for item in value)
    return value == target


def _non_empty_status_collection(value: Any, fallback: str) -> str | list[str]:
    statuses = _string_values(value)
    return _dedupe_preserve_order(statuses) if statuses else fallback


def _first_status(value: Any) -> str:
    statuses = _string_values(value)
    return statuses[0] if statuses else "data_gap"


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


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise EvidenceAwareResearchPackScaffoldError(f"{field} must be a mapping")
    return value


def _require_fields(value: Mapping[str, Any], fields: tuple[str, ...], path: str) -> None:
    missing = [field for field in fields if field not in value]
    if missing:
        raise EvidenceAwareResearchPackScaffoldError(f"{path} missing required fields: {missing}")


def _require_schema_version(value: Any, expected: str, path: str) -> None:
    if value != expected:
        raise EvidenceAwareResearchPackScaffoldError(f"{path} must be {expected}")


def _require_optional_string(value: Any, path: str) -> None:
    if value is not None and not isinstance(value, str):
        raise EvidenceAwareResearchPackScaffoldError(f"{path} must be a string or null")


def _require_non_empty_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceAwareResearchPackScaffoldError(f"{path} must be a non-empty string")
    return value


def _require_string_list(value: Any, path: str) -> list[str]:
    if not isinstance(value, list):
        raise EvidenceAwareResearchPackScaffoldError(f"{path} must be a list")
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise EvidenceAwareResearchPackScaffoldError(f"{path}[{index}] must be a string")
    return value


def _require_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise EvidenceAwareResearchPackScaffoldError(f"{path} must be a list")
    return value


def _require_true(value: Any, path: str) -> None:
    if value is not True:
        raise EvidenceAwareResearchPackScaffoldError(f"{path} must be true")


def _require_evidence_status(value: Any, path: str) -> str:
    if not isinstance(value, str) or value not in EVIDENCE_STATUSES:
        raise EvidenceAwareResearchPackScaffoldError(f"{path} must be one of {EVIDENCE_STATUSES}")
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
        raise EvidenceAwareResearchPackScaffoldError(
            f"{path} must be an evidence status or list"
        )
    if not value and not allow_empty:
        raise EvidenceAwareResearchPackScaffoldError(f"{path} cannot be empty")
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


def _contains_official_verified_text(value: str) -> bool:
    normalised = _normalise_marker(value)
    if normalised == "not_official_verified":
        return False
    return bool(re.search(r"(?<!not_)official_verified", normalised))


def _normalise_marker(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().casefold()).strip("_")


def _normalize_separator_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[_-]+", " ", value.strip().casefold())).strip()


__all__ = [
    "EVIDENCE_AWARE_RESEARCH_PACK_SCAFFOLD_SCHEMA_VERSION",
    "EVIDENCE_AWARE_RESEARCH_PACK_SECTION_SCHEMA_VERSION",
    "EVIDENCE_STATUS_LEGEND_SCHEMA_VERSION",
    "SECTION_IDS",
    "EvidenceAwareResearchPackScaffoldError",
    "assert_no_research_pack_scaffold_forbidden_markers",
    "build_company_business_profile_section",
    "build_data_gap_section",
    "build_evidence_aware_research_pack_scaffold",
    "build_evidence_status_legend",
    "build_financial_context_section",
    "build_industry_context_section",
    "build_macro_transmission_section",
    "build_official_verification_section",
    "build_research_questions_section",
    "build_research_subject_section",
    "validate_evidence_aware_research_pack_scaffold",
]
