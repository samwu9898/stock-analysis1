# -*- coding: utf-8 -*-
"""Live evidence-aware research pack vertical slice assembler.

This module combines already-built, explicitly supplied component payloads into
a user-readable vertical slice. It does not fetch data, read files, parse PDF
content, write artifacts, or produce trading-oriented conclusions.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
import re
from typing import Any

from ..data_verification.official_artifact_cache_acquisition import (
    ARTIFACT_CACHE_SCHEMA_VERSION,
    validate_official_disclosure_artifact_cache,
)
from ..data_verification.provider_metric_official_anchor import (
    ANCHOR_MAP_SCHEMA_VERSION,
    validate_provider_metric_official_disclosure_anchor_map,
)
from ..data_verification.real_official_metadata_anchor_handoff import (
    HANDOFF_RESULT_SCHEMA_VERSION,
    validate_real_official_metadata_anchor_handoff_result,
)
from .evidence_aware_research_pack_scaffold import (
    EVIDENCE_AWARE_RESEARCH_PACK_SCAFFOLD_SCHEMA_VERSION,
    validate_evidence_aware_research_pack_scaffold,
)
from .ticker_research_context_skeleton import (
    TICKER_RESEARCH_CONTEXT_SCHEMA_VERSION,
    validate_ticker_research_context_skeleton,
)


LIVE_EVIDENCE_AWARE_RESEARCH_PACK_VERTICAL_SLICE_SCHEMA_VERSION = (
    "live_evidence_aware_research_pack_vertical_slice.v1"
)
LIVE_EVIDENCE_RESEARCH_PACK_SECTION_SCHEMA_VERSION = (
    "live_evidence_research_pack_section.v1"
)
LIVE_EVIDENCE_STATUS_ROLLUP_SCHEMA_VERSION = "live_evidence_status_rollup.v1"

VERTICAL_SLICE_EVIDENCE_STATUSES = (
    "official_verified",
    "provider_candidate",
    "pending_official_verification",
    "official_anchor_matched",
    "artifact_cached",
    "framework_inference",
    "local_experiment",
    "data_gap",
    "not_assessable",
    "blocked",
)

SECTION_IDS = (
    "subject",
    "evidence_status_summary",
    "financial_candidate_summary",
    "official_anchor_and_artifact_status",
    "company_business_profile",
    "industry_and_macro_context",
    "data_gaps_and_next_tasks",
    "research_questions",
    "cannot_conclude_yet",
)

ALLOWED_COMPONENT_KEYS = {
    "ticker_research_context_skeleton",
    "evidence_aware_research_pack_scaffold",
    "provider_metric_official_anchor_map",
    "real_official_metadata_anchor_handoff_result",
    "official_disclosure_artifact_cache",
}

_RAW_COMPONENT_KEYS = {
    "provider_candidate_financial_result",
    "provider_candidate_financial_snapshot",
    "provider_candidate_financial_trend_table",
    "provider_candidate_metric_verification_queue",
    "raw_provider_queue",
    "provider_queue",
    "raw_tushare_provider_result",
    "tushare_provider_result",
    "raw_official_http_response",
    "official_http_response",
    "pdf_bytes",
    "raw_pdf_bytes",
    "cache_file_content",
    "cache_file_bytes",
}

_TOP_LEVEL_REQUIRED_FIELDS = (
    "schema_version",
    "stock_code",
    "ts_code",
    "company_name_hint",
    "vertical_slice_subject",
    "source_components",
    "evidence_status_rollup",
    "sections",
    "user_readable_markdown_preview",
    "data_gaps",
    "next_data_tasks",
    "caveats",
    "not_official_verified",
    "not_for_trading_advice",
)

_SECTION_REQUIRED_FIELDS = (
    "schema_version",
    "section_id",
    "section_title",
    "source_components",
    "evidence_status",
    "evidence_items",
    "user_visible_points",
    "limitations",
    "next_data_tasks",
    "caveats",
    "not_official_verified",
    "not_for_trading_advice",
)

_ROLLUP_REQUIRED_FIELDS = (
    "schema_version",
    "provider_candidate_present",
    "pending_official_verification_count",
    "official_anchor_matched_count",
    "official_artifact_cached_count",
    "official_verified_count",
    "data_gap_count",
    "not_assessable_count",
    "blocked_count",
    "has_formal_research_report",
    "has_trading_advice",
    "not_for_trading_advice",
)

_EVIDENCE_STATUS_FIELD_KEYS = {
    "evidence_status",
    "current_evidence_status",
    "required_next_status",
    "statuses_used",
    "status",
    "status_label",
    "anchor_evidence_status",
    "artifact_evidence_status",
    "official_verification_status",
    "source_anchor_status",
}

_ALLOWED_EXACT_KEYS = {
    "not_for_trading_advice",
    "not_official_verified",
    "has_trading_advice",
    "has_formal_research_report",
    "official_verified_count",
}

_CONTROLLED_DISCLAIMER_TEXTS = {
    "这不是正式研报 / 不是投资建议",
    "official_verified_count",
}

_FORBIDDEN_MARKERS = (
    "token",
    ".env",
    "tushare_token",
    "official_metric_fact",
    "provider_official_conflict",
    "Report V1",
    "formal report",
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
    "parse PDF",
    "PDF parser",
    "table extractor",
    "metric extraction",
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
    "\u89e3\u6790PDF",
    "PDF\u89e3\u6790",
    "\u8868\u683c\u62bd\u53d6",
    "\u6307\u6807\u62bd\u53d6",
    "\u884c\u4e1a\u666f\u6c14",
    "\u5b8f\u89c2\u5229\u597d",
    "\u516c\u53f8\u53d7\u76ca",
    "\u6838\u5fc3\u6295\u8d44\u903b\u8f91\u6210\u7acb",
)

_WORD_MARKERS = {"token", "buy", "sell", "hold", "portfolio", "position"}
_IDENTIFIER_SAFE_WORD_MARKERS = {"buy", "sell", "hold"}


class LiveEvidenceAwareResearchPackVerticalSliceError(ValueError):
    """Raised when the vertical slice fails a shape or safety check."""


def build_live_evidence_aware_research_pack_vertical_slice(
    components: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a standalone vertical slice from explicit component payloads."""

    validated = _validated_components_copy(components)
    sections = [
        build_subject_section(validated),
        build_evidence_status_summary_section(validated),
        build_financial_candidate_section(validated),
        build_official_anchor_and_artifact_section(validated),
        build_company_business_profile_section(validated),
        build_industry_and_macro_context_section(validated),
        build_data_gap_section(validated),
        build_research_question_section(validated),
        build_cannot_conclude_yet_section(validated),
    ]
    source_components = _build_source_components(validated)
    rollup = build_evidence_status_rollup(validated)
    vertical_slice = {
        "schema_version": LIVE_EVIDENCE_AWARE_RESEARCH_PACK_VERTICAL_SLICE_SCHEMA_VERSION,
        "stock_code": _resolve_identity(validated, "stock_code"),
        "ts_code": _resolve_identity(validated, "ts_code"),
        "company_name_hint": _resolve_identity(validated, "company_name_hint"),
        "vertical_slice_subject": {
            "stock_code": _resolve_identity(validated, "stock_code"),
            "ts_code": _resolve_identity(validated, "ts_code"),
            "company_name_hint": _resolve_identity(validated, "company_name_hint"),
            "sample_only": True,
            "production_research_pack_generated": False,
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
        "source_components": source_components,
        "evidence_status_rollup": rollup,
        "sections": sections,
        "user_readable_markdown_preview": "",
        "data_gaps": _collect_top_level_data_gaps(validated),
        "next_data_tasks": _collect_next_data_tasks(validated),
        "caveats": _dedupe_preserve_order(
            [
                "Vertical slice assembled from explicit validated components only.",
                "Provider candidate and artifact-cache evidence remain non-verified states.",
            ]
            + _component_caveats(validated)
        ),
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }
    vertical_slice["user_readable_markdown_preview"] = build_vertical_slice_markdown_preview(
        vertical_slice
    )
    return validate_live_evidence_aware_research_pack_vertical_slice(vertical_slice)


def validate_live_evidence_aware_research_pack_vertical_slice(
    vertical_slice: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate and return a defensive copy of a live vertical slice."""

    assert_no_live_research_pack_forbidden_markers(vertical_slice)
    source = _require_mapping(vertical_slice, "vertical_slice")
    _require_fields(source, _TOP_LEVEL_REQUIRED_FIELDS, "vertical_slice")
    result = deepcopy(dict(source))
    _require_schema_version(
        result["schema_version"],
        LIVE_EVIDENCE_AWARE_RESEARCH_PACK_VERTICAL_SLICE_SCHEMA_VERSION,
        "schema_version",
    )
    _require_optional_string(result["stock_code"], "stock_code")
    _require_optional_string(result["ts_code"], "ts_code")
    _require_optional_string(result["company_name_hint"], "company_name_hint")
    _require_mapping(result["vertical_slice_subject"], "vertical_slice_subject")
    _require_true(result["not_official_verified"], "not_official_verified")
    _require_true(result["not_for_trading_advice"], "not_for_trading_advice")
    result["source_components"] = _validate_source_components(result["source_components"])
    result["evidence_status_rollup"] = _validate_evidence_status_rollup(
        result["evidence_status_rollup"]
    )
    sections = _require_list(result["sections"], "sections")
    result["sections"] = [
        _validate_section(section, f"sections[{index}]")
        for index, section in enumerate(sections)
    ]
    section_ids = [section["section_id"] for section in result["sections"]]
    if tuple(section_ids) != SECTION_IDS:
        raise LiveEvidenceAwareResearchPackVerticalSliceError(
            f"sections must be ordered as {SECTION_IDS}"
        )
    _require_non_empty_string(
        result["user_readable_markdown_preview"],
        "user_readable_markdown_preview",
    )
    _require_list(result["data_gaps"], "data_gaps")
    _require_list(result["next_data_tasks"], "next_data_tasks")
    _require_string_list(result["caveats"], "caveats")
    _validate_evidence_status_values(result)
    _assert_no_cache_path_disclosure(result)
    _assert_candidate_anchor_artifact_not_promoted(result)
    return result


def build_vertical_slice_markdown_preview(vertical_slice: Mapping[str, Any]) -> str:
    """Build controlled markdown from structured vertical-slice sections."""

    source = _require_mapping(vertical_slice, "vertical_slice")
    sections = _require_list(source.get("sections"), "sections")
    subject = _require_mapping(source.get("vertical_slice_subject"), "vertical_slice_subject")
    rollup = _require_mapping(source.get("evidence_status_rollup"), "evidence_status_rollup")
    lines = [
        "# Live Evidence-aware Research Pack Vertical Slice",
        "这不是正式研报 / 不是投资建议",
        "",
        "## Subject",
        f"- stock_code: {subject.get('stock_code')}",
        f"- ts_code: {subject.get('ts_code')}",
        f"- company_name_hint: {subject.get('company_name_hint')}",
        "",
        "## Evidence Status Rollup",
    ]
    for key in (
        "provider_candidate_present",
        "pending_official_verification_count",
        "official_anchor_matched_count",
        "official_artifact_cached_count",
        "official_verified_count",
        "data_gap_count",
        "not_assessable_count",
        "blocked_count",
    ):
        display_key = (
            "explicit_official_status_count"
            if key == "official_verified_count"
            else key
        )
        lines.append(f"- [{display_key}] {rollup.get(key)}")
    for section in sections:
        section_id = str(section.get("section_id"))
        lines.extend(["", f"## {section_id}"])
        statuses = _status_values(section.get("evidence_status"))
        label = ", ".join(statuses) if statuses else "not_assessable"
        lines.append(f"- evidence_status: [{label}]")
        for point in section.get("user_visible_points", [])[:8]:
            if not isinstance(point, Mapping):
                continue
            point_id = point.get("point_id") or point.get("item_id") or "point"
            status = point.get("current_evidence_status") or point.get("status_label")
            display = _preview_display_value(point)
            if status:
                lines.append(f"- [{status}] {point_id}: {display}")
            else:
                lines.append(f"- {point_id}: {display}")
    preview = "\n".join(lines).strip() + "\n"
    assert_no_live_research_pack_forbidden_markers(preview)
    return preview


def build_evidence_status_rollup(components: Mapping[str, Any]) -> dict[str, Any]:
    """Summarize supplied evidence states without promoting them."""

    validated = _validated_components_copy(components)
    financial = _financial_context(validated)
    anchor_map = _anchor_map(validated)
    artifact_cache = validated.get("official_disclosure_artifact_cache") or {}
    scaffold = validated["evidence_aware_research_pack_scaffold"]

    pending_count = _non_negative_int(
        financial.get("pending_official_verification_count"),
        default=0,
    )
    anchor_pending = sum(
        1
        for item in _list_from_mapping(anchor_map, "anchor_items")
        if item.get("official_verification_status") == "pending_official_verification"
    )
    matched_count = sum(
        1
        for item in _list_from_mapping(anchor_map, "anchor_items")
        if _anchor_item_matched(item)
    )
    cached_count = sum(
        1
        for item in _list_from_mapping(artifact_cache, "artifact_items")
        if _artifact_item_cached(item)
    )
    data_gap_count = _count_status_value(scaffold, "data_gap")
    not_assessable_count = _count_status_value(scaffold, "not_assessable")
    blocked_count = len(_collect_blocked_reasons(validated)) + _count_status_value(
        scaffold,
        "blocked",
    )
    rollup = {
        "schema_version": LIVE_EVIDENCE_STATUS_ROLLUP_SCHEMA_VERSION,
        "provider_candidate_present": _count_status_value(scaffold, "provider_candidate") > 0,
        "pending_official_verification_count": max(pending_count, anchor_pending),
        "official_anchor_matched_count": matched_count,
        "official_artifact_cached_count": cached_count,
        "official_verified_count": _explicit_official_verified_count(validated),
        "data_gap_count": data_gap_count,
        "not_assessable_count": not_assessable_count,
        "blocked_count": blocked_count,
        "has_formal_research_report": False,
        "has_trading_advice": False,
        "not_for_trading_advice": True,
    }
    return _validate_evidence_status_rollup(rollup)


def build_subject_section(components: Mapping[str, Any]) -> dict[str, Any]:
    """Build the subject section without company evaluation."""

    validated = _validated_components_copy(components)
    points = [
        {
            "point_id": "stock_code",
            "value": _resolve_identity(validated, "stock_code"),
            "current_evidence_status": "not_assessable",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
        {
            "point_id": "ts_code",
            "value": _resolve_identity(validated, "ts_code"),
            "current_evidence_status": "not_assessable",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
        {
            "point_id": "company_name_hint",
            "value": _resolve_identity(validated, "company_name_hint"),
            "current_evidence_status": "not_assessable",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
        {
            "point_id": "vertical_slice_positioning",
            "sample_only": True,
            "production_research_pack_generated": False,
            "current_evidence_status": "not_assessable",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
    ]
    return _section(
        section_id="subject",
        section_title="Subject",
        source_components=["evidence_aware_research_pack_scaffold"],
        evidence_status="not_assessable",
        evidence_items=points,
        user_visible_points=points,
        limitations=["Identity fields are copied from supplied components only."],
        next_data_tasks=[],
        caveats=[],
    )


def build_evidence_status_summary_section(components: Mapping[str, Any]) -> dict[str, Any]:
    """Build a status-only summary section."""

    validated = _validated_components_copy(components)
    rollup = build_evidence_status_rollup(validated)
    points = [
        {
            "point_id": "provider_candidate",
            "present": rollup["provider_candidate_present"],
            "current_evidence_status": "provider_candidate"
            if rollup["provider_candidate_present"]
            else "data_gap",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
        {
            "point_id": "pending_official_verification",
            "count": rollup["pending_official_verification_count"],
            "current_evidence_status": "pending_official_verification"
            if rollup["pending_official_verification_count"]
            else "not_assessable",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
        {
            "point_id": "official_anchor_matched",
            "count": rollup["official_anchor_matched_count"],
            "current_evidence_status": "official_anchor_matched"
            if rollup["official_anchor_matched_count"]
            else "data_gap",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
        {
            "point_id": "artifact_cached",
            "count": rollup["official_artifact_cached_count"],
            "current_evidence_status": "artifact_cached"
            if rollup["official_artifact_cached_count"]
            else "data_gap",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
        {
            "point_id": "data_gap",
            "count": rollup["data_gap_count"],
            "current_evidence_status": "data_gap"
            if rollup["data_gap_count"]
            else "not_assessable",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
        {
            "point_id": "not_assessable",
            "count": rollup["not_assessable_count"],
            "current_evidence_status": "not_assessable",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
    ]
    return _section(
        section_id="evidence_status_summary",
        section_title="Evidence status summary",
        source_components=list(validated.keys()),
        evidence_status=_dedupe_preserve_order(
            point["current_evidence_status"] for point in points
        ),
        evidence_items=points,
        user_visible_points=points,
        limitations=["This section reports evidence states only."],
        next_data_tasks=[],
        caveats=[],
    )


def build_financial_candidate_section(components: Mapping[str, Any]) -> dict[str, Any]:
    """Build a provider-candidate financial summary without quality judgment."""

    validated = _validated_components_copy(components)
    financial = _financial_context(validated)
    metric_candidates = [
        {
            "metric_key": item.get("metric_key"),
            "period": item.get("period"),
            "period_label": item.get("period_label"),
            "value_status": item.get("value_status"),
            "current_evidence_status": item.get("current_evidence_status", "provider_candidate"),
            "required_next_status": item.get(
                "required_next_status",
                "pending_official_verification",
            ),
            "not_official_verified": True,
            "not_for_trading_advice": True,
        }
        for item in _list_from_mapping(financial, "key_metric_candidates")
    ]
    points = [
        {
            "point_id": "provider_trend_periods",
            "provider_trend_periods": list(financial.get("provider_trend_periods", [])),
            "current_evidence_status": "provider_candidate"
            if financial.get("provider_trend_periods")
            else "data_gap",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
        {
            "point_id": "key_metric_candidate_count",
            "count": len(metric_candidates),
            "current_evidence_status": "provider_candidate"
            if metric_candidates
            else "data_gap",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
        {
            "point_id": "pending_official_verification_count",
            "count": _non_negative_int(
                financial.get("pending_official_verification_count"),
                default=0,
            ),
            "current_evidence_status": "pending_official_verification"
            if financial.get("pending_official_verification_count")
            else "not_assessable",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
        {
            "point_id": "missing_metric_count",
            "count": _non_negative_int(financial.get("missing_metric_count"), default=0),
            "current_evidence_status": "data_gap"
            if financial.get("missing_metric_count")
            else "not_assessable",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
    ]
    evidence_items = points + [
        {
            "item_id": "metric_candidate_statuses",
            "metric_candidates": metric_candidates,
            "current_evidence_status": "provider_candidate"
            if metric_candidates
            else "data_gap",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        }
    ]
    return _section(
        section_id="financial_candidate_summary",
        section_title="Financial candidate summary",
        source_components=_present_sources(
            validated,
            [
                "evidence_aware_research_pack_scaffold",
                "ticker_research_context_skeleton",
            ],
        ),
        evidence_status=_non_empty_status_collection(
            financial.get("evidence_status"),
            "data_gap",
        ),
        evidence_items=evidence_items,
        user_visible_points=points,
        limitations=[
            "Provider metrics are represented as candidate records.",
            "No financial direction or quality judgment is inferred here.",
        ],
        next_data_tasks=_tasks_from_gaps(_list_from_mapping(financial, "data_gaps")),
        caveats=_string_values(financial.get("caveats")),
    )


def build_official_anchor_and_artifact_section(
    components: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the official anchor and artifact-cache status section."""

    validated = _validated_components_copy(components)
    anchor_map = _anchor_map(validated)
    artifact_cache = validated.get("official_disclosure_artifact_cache") or {}
    anchor_items = [
        {
            "metric_key": item.get("metric_key"),
            "period": item.get("period"),
            "period_label": item.get("period_label"),
            "official_anchor_status": item.get("official_anchor_status"),
            "current_evidence_status": "official_anchor_matched"
            if _anchor_item_matched(item)
            else "data_gap",
            "source_title": _anchor_title(item),
            "source_domain": _anchor_domain(item),
            "not_official_verified": True,
            "not_for_trading_advice": True,
        }
        for item in _list_from_mapping(anchor_map, "anchor_items")
    ]
    artifact_items = [
        _artifact_metadata_item(item)
        for item in _list_from_mapping(artifact_cache, "artifact_items")
    ]
    points = [
        {
            "point_id": "official_anchor_matched_count",
            "count": sum(1 for item in anchor_items if item["current_evidence_status"] == "official_anchor_matched"),
            "current_evidence_status": "official_anchor_matched"
            if any(item["current_evidence_status"] == "official_anchor_matched" for item in anchor_items)
            else "data_gap",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
        {
            "point_id": "official_artifact_cached_count",
            "count": sum(1 for item in artifact_items if item["artifact_evidence_status"] == "artifact_cached"),
            "current_evidence_status": "artifact_cached"
            if any(item["artifact_evidence_status"] == "artifact_cached" for item in artifact_items)
            else "data_gap",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
    ]
    evidence_items = points + [
        {
            "item_id": "anchor_items",
            "anchor_items": anchor_items,
            "current_evidence_status": "official_anchor_matched"
            if any(item["current_evidence_status"] == "official_anchor_matched" for item in anchor_items)
            else "data_gap",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
        {
            "item_id": "artifact_cache_metadata",
            "artifact_cache_metadata": artifact_items,
            "current_evidence_status": "artifact_cached"
            if any(item["artifact_evidence_status"] == "artifact_cached" for item in artifact_items)
            else "data_gap",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
    ]
    return _section(
        section_id="official_anchor_and_artifact_status",
        section_title="Official anchor and artifact status",
        source_components=_present_sources(
            validated,
            [
                "provider_metric_official_anchor_map",
                "real_official_metadata_anchor_handoff_result",
                "official_disclosure_artifact_cache",
            ],
        ),
        evidence_status=_dedupe_preserve_order(
            point["current_evidence_status"] for point in points
        ),
        evidence_items=evidence_items,
        user_visible_points=points + artifact_items[:4],
        limitations=[
            "Anchor matched and artifact cached states are not official verification.",
            "Only artifact cache metadata is displayed.",
        ],
        next_data_tasks=[],
        caveats=_dedupe_preserve_order(
            _string_values(anchor_map.get("caveats"))
            + _string_values(artifact_cache.get("caveats"))
        ),
    )


def build_company_business_profile_section(components: Mapping[str, Any]) -> dict[str, Any]:
    """Build the company business profile section from scaffold/context evidence."""

    validated = _validated_components_copy(components)
    profile = _company_business_profile(validated)
    business_fields = {
        "business_segments": profile.get("business_segments", []),
        "main_products": profile.get("main_products", []),
        "revenue_structure": profile.get("revenue_structure", []),
        "downstream_or_end_markets": profile.get("downstream_or_end_markets", []),
    }
    has_business_evidence = any(bool(value) for value in business_fields.values())
    points = [
        {
            "point_id": field,
            "value_count": len(value) if isinstance(value, list) else 0,
            "values": deepcopy(value) if isinstance(value, list) else [],
            "current_evidence_status": profile.get("evidence_status", "data_gap")
            if value
            else "data_gap",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        }
        for field, value in business_fields.items()
    ]
    points.append(
        {
            "point_id": "business_evidence_presence",
            "present": has_business_evidence,
            "current_evidence_status": profile.get("evidence_status", "data_gap")
            if has_business_evidence
            else "data_gap",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        }
    )
    return _section(
        section_id="company_business_profile",
        section_title="Company business profile",
        source_components=_present_sources(
            validated,
            [
                "evidence_aware_research_pack_scaffold",
                "ticker_research_context_skeleton",
            ],
        ),
        evidence_status=profile.get("evidence_status", "data_gap")
        if has_business_evidence
        else "data_gap",
        evidence_items=points
        + [
            {
                "item_id": "business_data_gaps",
                "data_gaps": deepcopy(profile.get("data_gaps", [])),
                "current_evidence_status": "data_gap"
                if profile.get("data_gaps")
                else "not_assessable",
                "not_official_verified": True,
                "not_for_trading_advice": True,
            }
        ],
        user_visible_points=points,
        limitations=[
            "Business profile uses supplied business evidence only.",
            "No business segment is inferred from financial candidates.",
        ],
        next_data_tasks=_tasks_from_gaps(_list_from_mapping(profile, "data_gaps")),
        caveats=_string_values(profile.get("caveats")),
    )


def build_industry_and_macro_context_section(
    components: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the industry and macro context section as question-only framing."""

    validated = _validated_components_copy(components)
    industry = _industry_context(validated)
    macro = _macro_transmission(validated)
    points = [
        {
            "point_id": "possible_industry_frameworks",
            "possible_industry_frameworks": deepcopy(
                industry.get("possible_industry_frameworks", [])
            ),
            "current_evidence_status": industry.get("evidence_status", "not_assessable"),
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
        {
            "point_id": "industry_driver_questions",
            "industry_driver_questions": _string_values(
                industry.get("industry_driver_questions")
            ),
            "current_evidence_status": industry.get("evidence_status", "not_assessable"),
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
        {
            "point_id": "macro_variables_to_investigate",
            "macro_variables_to_investigate": _string_values(
                macro.get("macro_variables_to_investigate")
            ),
            "current_evidence_status": "framework_inference"
            if macro.get("macro_variables_to_investigate")
            else "not_assessable",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
        {
            "point_id": "industry_to_company_transmission_questions",
            "industry_to_company_transmission_questions": _string_values(
                macro.get("industry_to_company_transmission_questions")
            ),
            "current_evidence_status": "framework_inference"
            if macro.get("industry_to_company_transmission_questions")
            else "not_assessable",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
    ]
    data_gaps = _list_from_mapping(industry, "industry_data_gaps") + _list_from_mapping(
        macro,
        "data_gaps",
    )
    return _section(
        section_id="industry_and_macro_context",
        section_title="Industry and macro context",
        source_components=_present_sources(
            validated,
            [
                "evidence_aware_research_pack_scaffold",
                "ticker_research_context_skeleton",
            ],
        ),
        evidence_status=_dedupe_preserve_order(
            point["current_evidence_status"] for point in points
        ),
        evidence_items=points
        + [
            {
                "item_id": "industry_macro_data_gaps",
                "data_gaps": deepcopy(data_gaps),
                "current_evidence_status": "data_gap" if data_gaps else "not_assessable",
                "not_official_verified": True,
                "not_for_trading_advice": True,
            }
        ],
        user_visible_points=points,
        limitations=[
            "Framework hints and macro paths remain questions.",
            "No industry or macro direction is concluded.",
        ],
        next_data_tasks=_tasks_from_gaps(data_gaps),
        caveats=_string_values(macro.get("caveats")),
    )


def build_business_industry_macro_section(
    components: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Build the business and industry/macro sections requested by the slice."""

    return [
        build_company_business_profile_section(components),
        build_industry_and_macro_context_section(components),
    ]


def build_data_gap_section(components: Mapping[str, Any]) -> dict[str, Any]:
    """Build the data gaps and next tasks section."""

    validated = _validated_components_copy(components)
    gaps = _collect_top_level_data_gaps(validated)
    high_priority_gaps = [
        gap for gap in gaps if isinstance(gap, Mapping) and gap.get("priority") == "high"
    ]
    tasks = _collect_next_data_tasks(validated)
    points = [
        {
            "point_id": "high_priority_data_gaps",
            "data_gaps": deepcopy(high_priority_gaps),
            "count": len(high_priority_gaps),
            "current_evidence_status": "data_gap"
            if high_priority_gaps
            else "not_assessable",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
        {
            "point_id": "next_data_tasks",
            "next_data_tasks": deepcopy(tasks),
            "count": len(tasks),
            "current_evidence_status": "data_gap" if tasks else "not_assessable",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
    ]
    return _section(
        section_id="data_gaps_and_next_tasks",
        section_title="Data gaps and next tasks",
        source_components=_present_sources(
            validated,
            [
                "evidence_aware_research_pack_scaffold",
                "ticker_research_context_skeleton",
            ],
        ),
        evidence_status="data_gap" if gaps or tasks else "not_assessable",
        evidence_items=points,
        user_visible_points=points,
        limitations=["Open gaps are displayed rather than hidden."],
        next_data_tasks=tasks,
        caveats=[],
    )


def build_research_question_section(components: Mapping[str, Any]) -> dict[str, Any]:
    """Build the research questions section without rewriting questions."""

    validated = _validated_components_copy(components)
    questions = [
        {
            "question_id": question.get("question_id"),
            "category": question.get("category"),
            "question_text": question.get("question_text"),
            "required_data": _string_values(question.get("required_data")),
            "current_evidence_status": question.get(
                "current_evidence_status",
                "not_assessable",
            ),
            "priority": question.get("priority"),
            "not_official_verified": True,
            "not_for_trading_advice": True,
        }
        for question in _research_questions(validated)
    ]
    return _section(
        section_id="research_questions",
        section_title="Research questions",
        source_components=_present_sources(
            validated,
            [
                "evidence_aware_research_pack_scaffold",
                "ticker_research_context_skeleton",
            ],
        ),
        evidence_status=_non_empty_status_collection(
            [question["current_evidence_status"] for question in questions],
            "data_gap",
        ),
        evidence_items=questions,
        user_visible_points=questions,
        limitations=["Questions remain open tasks and are not rewritten as conclusions."],
        next_data_tasks=[],
        caveats=[],
    )


def build_cannot_conclude_yet_section(components: Mapping[str, Any]) -> dict[str, Any]:
    """Build the user-readable list of currently blocked conclusion types."""

    _validated_components_copy(components)
    points = [
        {
            "point_id": "official_metric_values_unconfirmed",
            "blocked_conclusion": "official_metric_values",
            "current_evidence_status": "blocked",
            "reason": "no_explicit_metric_verification_input",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
        {
            "point_id": "provider_official_consistency_unconfirmed",
            "blocked_conclusion": "provider_official_consistency",
            "current_evidence_status": "blocked",
            "reason": "reconciliation_not_performed",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
        {
            "point_id": "production_research_pack_unavailable",
            "blocked_conclusion": "production_research_pack",
            "current_evidence_status": "blocked",
            "reason": "vertical_slice_only",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
        {
            "point_id": "directional_decision_unavailable",
            "blocked_conclusion": "directional_decision",
            "current_evidence_status": "blocked",
            "reason": "outside_vertical_slice_scope",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
        {
            "point_id": "valuation_target_unavailable",
            "blocked_conclusion": "valuation_target",
            "current_evidence_status": "blocked",
            "reason": "outside_vertical_slice_scope",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
        {
            "point_id": "sizing_instruction_unavailable",
            "blocked_conclusion": "sizing_instruction",
            "current_evidence_status": "blocked",
            "reason": "outside_vertical_slice_scope",
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
    ]
    return _section(
        section_id="cannot_conclude_yet",
        section_title="Cannot conclude yet",
        source_components=list(ALLOWED_COMPONENT_KEYS),
        evidence_status="blocked",
        evidence_items=points,
        user_visible_points=points,
        limitations=["Current vertical slice value includes explicit non-conclusions."],
        next_data_tasks=[],
        caveats=[],
    )


def assert_no_live_research_pack_forbidden_markers(value: Any) -> None:
    """Reject blocked markers in nested vertical-slice keys and values."""

    finding = _find_forbidden_marker(value)
    if finding:
        raise LiveEvidenceAwareResearchPackVerticalSliceError(
            f"live research pack vertical slice safety violation: forbidden marker: {finding}"
        )


def _validated_components_copy(components: Mapping[str, Any]) -> dict[str, Any]:
    source = _require_mapping(components, "components")
    _reject_raw_component_keys(source)
    _reject_bytes(source, "components")
    unexpected = sorted(set(source) - ALLOWED_COMPONENT_KEYS)
    if unexpected:
        raise LiveEvidenceAwareResearchPackVerticalSliceError(
            f"components contains unsupported keys: {unexpected}"
        )
    if "evidence_aware_research_pack_scaffold" not in source:
        raise LiveEvidenceAwareResearchPackVerticalSliceError(
            "components.evidence_aware_research_pack_scaffold is required"
        )
    assert_no_live_research_pack_forbidden_markers(source)
    result: dict[str, Any] = {}
    if source.get("ticker_research_context_skeleton") is not None:
        result["ticker_research_context_skeleton"] = validate_ticker_research_context_skeleton(
            source["ticker_research_context_skeleton"]
        )
    result["evidence_aware_research_pack_scaffold"] = (
        validate_evidence_aware_research_pack_scaffold(
            source["evidence_aware_research_pack_scaffold"]
        )
    )
    if source.get("provider_metric_official_anchor_map") is not None:
        validate_provider_metric_official_disclosure_anchor_map(
            source["provider_metric_official_anchor_map"]
        )
        result["provider_metric_official_anchor_map"] = deepcopy(
            source["provider_metric_official_anchor_map"]
        )
    if source.get("real_official_metadata_anchor_handoff_result") is not None:
        validate_real_official_metadata_anchor_handoff_result(
            source["real_official_metadata_anchor_handoff_result"]
        )
        result["real_official_metadata_anchor_handoff_result"] = deepcopy(
            source["real_official_metadata_anchor_handoff_result"]
        )
    if source.get("official_disclosure_artifact_cache") is not None:
        validate_official_disclosure_artifact_cache(
            source["official_disclosure_artifact_cache"]
        )
        result["official_disclosure_artifact_cache"] = deepcopy(
            source["official_disclosure_artifact_cache"]
        )
    _assert_candidate_anchor_artifact_inputs_not_promoted(result)
    return result


def _build_source_components(components: Mapping[str, Any]) -> dict[str, Any]:
    context = components.get("ticker_research_context_skeleton") or {}
    scaffold = components.get("evidence_aware_research_pack_scaffold") or {}
    anchor_map = _anchor_map(components)
    handoff = components.get("real_official_metadata_anchor_handoff_result") or {}
    artifact_cache = components.get("official_disclosure_artifact_cache") or {}
    return {
        "ticker_research_context_skeleton_schema_version": context.get("schema_version"),
        "evidence_aware_research_pack_scaffold_schema_version": scaffold.get(
            "schema_version"
        ),
        "anchor_map_schema_version": anchor_map.get("schema_version"),
        "real_metadata_handoff_schema_version": handoff.get("schema_version"),
        "artifact_cache_schema_version": artifact_cache.get("schema_version"),
        "component_keys_present": sorted(components.keys()),
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }


def _validate_source_components(value: Any) -> dict[str, Any]:
    source = _require_mapping(value, "source_components")
    result = deepcopy(dict(source))
    if result.get("ticker_research_context_skeleton_schema_version") not in {
        None,
        TICKER_RESEARCH_CONTEXT_SCHEMA_VERSION,
    }:
        raise LiveEvidenceAwareResearchPackVerticalSliceError(
            "invalid ticker research context schema version"
        )
    _require_schema_version(
        result.get("evidence_aware_research_pack_scaffold_schema_version"),
        EVIDENCE_AWARE_RESEARCH_PACK_SCAFFOLD_SCHEMA_VERSION,
        "source_components.evidence_aware_research_pack_scaffold_schema_version",
    )
    if result.get("anchor_map_schema_version") not in {None, ANCHOR_MAP_SCHEMA_VERSION}:
        raise LiveEvidenceAwareResearchPackVerticalSliceError(
            "invalid anchor map schema version"
        )
    if result.get("real_metadata_handoff_schema_version") not in {
        None,
        HANDOFF_RESULT_SCHEMA_VERSION,
    }:
        raise LiveEvidenceAwareResearchPackVerticalSliceError(
            "invalid handoff schema version"
        )
    if result.get("artifact_cache_schema_version") not in {
        None,
        ARTIFACT_CACHE_SCHEMA_VERSION,
    }:
        raise LiveEvidenceAwareResearchPackVerticalSliceError(
            "invalid artifact cache schema version"
        )
    _require_list(result.get("component_keys_present"), "source_components.component_keys_present")
    _require_true(result.get("not_official_verified"), "source_components.not_official_verified")
    _require_true(result.get("not_for_trading_advice"), "source_components.not_for_trading_advice")
    return result


def _validate_evidence_status_rollup(value: Any) -> dict[str, Any]:
    rollup = _require_mapping(value, "evidence_status_rollup")
    _require_fields(rollup, _ROLLUP_REQUIRED_FIELDS, "evidence_status_rollup")
    result = deepcopy(dict(rollup))
    _require_schema_version(
        result["schema_version"],
        LIVE_EVIDENCE_STATUS_ROLLUP_SCHEMA_VERSION,
        "evidence_status_rollup.schema_version",
    )
    if not isinstance(result["provider_candidate_present"], bool):
        raise LiveEvidenceAwareResearchPackVerticalSliceError(
            "provider_candidate_present must be bool"
        )
    for key in (
        "pending_official_verification_count",
        "official_anchor_matched_count",
        "official_artifact_cached_count",
        "official_verified_count",
        "data_gap_count",
        "not_assessable_count",
        "blocked_count",
    ):
        _require_non_negative_int(result[key], f"evidence_status_rollup.{key}")
    if result["has_formal_research_report"] is not False:
        raise LiveEvidenceAwareResearchPackVerticalSliceError(
            "has_formal_research_report must be false"
        )
    if result["has_trading_advice"] is not False:
        raise LiveEvidenceAwareResearchPackVerticalSliceError(
            "has_trading_advice must be false"
        )
    _require_true(result["not_for_trading_advice"], "evidence_status_rollup.not_for_trading_advice")
    return result


def _validate_section(value: Any, path: str) -> dict[str, Any]:
    section = _require_mapping(value, path)
    _require_fields(section, _SECTION_REQUIRED_FIELDS, path)
    result = deepcopy(dict(section))
    _require_schema_version(
        result["schema_version"],
        LIVE_EVIDENCE_RESEARCH_PACK_SECTION_SCHEMA_VERSION,
        f"{path}.schema_version",
    )
    if result["section_id"] not in SECTION_IDS:
        raise LiveEvidenceAwareResearchPackVerticalSliceError(
            f"{path}.section_id is invalid"
        )
    _require_non_empty_string(result["section_title"], f"{path}.section_title")
    _require_string_list(result["source_components"], f"{path}.source_components")
    _require_evidence_status_collection(result["evidence_status"], f"{path}.evidence_status")
    _require_list(result["evidence_items"], f"{path}.evidence_items")
    _require_list(result["user_visible_points"], f"{path}.user_visible_points")
    _require_string_list(result["limitations"], f"{path}.limitations")
    _require_list(result["next_data_tasks"], f"{path}.next_data_tasks")
    _require_string_list(result["caveats"], f"{path}.caveats")
    _require_true(result["not_official_verified"], f"{path}.not_official_verified")
    _require_true(result["not_for_trading_advice"], f"{path}.not_for_trading_advice")
    return result


def _section(
    *,
    section_id: str,
    section_title: str,
    source_components: list[str],
    evidence_status: str | list[str],
    evidence_items: list[Mapping[str, Any]],
    user_visible_points: list[Mapping[str, Any]],
    limitations: list[str],
    next_data_tasks: list[Mapping[str, Any]],
    caveats: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": LIVE_EVIDENCE_RESEARCH_PACK_SECTION_SCHEMA_VERSION,
        "section_id": section_id,
        "section_title": section_title,
        "source_components": list(source_components),
        "evidence_status": deepcopy(evidence_status),
        "evidence_items": deepcopy(evidence_items),
        "user_visible_points": deepcopy(user_visible_points),
        "limitations": list(limitations),
        "next_data_tasks": deepcopy(next_data_tasks),
        "caveats": list(caveats),
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }


def _financial_context(components: Mapping[str, Any]) -> Mapping[str, Any]:
    context = components.get("ticker_research_context_skeleton")
    if isinstance(context, Mapping) and isinstance(context.get("financial_context"), Mapping):
        return context["financial_context"]
    scaffold = components["evidence_aware_research_pack_scaffold"]
    section = _scaffold_section(scaffold, "financial_context")
    result = {
        "provider_trend_periods": [],
        "key_metric_candidates": [],
        "pending_official_verification_count": 0,
        "missing_metric_count": 0,
        "evidence_status": section.get("evidence_status", "data_gap"),
        "data_gaps": [],
        "caveats": section.get("caveats", []),
    }
    for item in _list_from_mapping(section, "items"):
        item_id = item.get("item_id")
        if item_id == "provider_trend_periods":
            result["provider_trend_periods"] = item.get("provider_trend_periods", [])
        elif item_id == "key_metric_candidates":
            result["key_metric_candidates"] = item.get("key_metric_candidates", [])
        elif item_id == "verification_and_missing_counts":
            result["pending_official_verification_count"] = item.get(
                "pending_official_verification_count",
                0,
            )
            result["missing_metric_count"] = item.get("missing_metric_count", 0)
        elif item_id == "financial_data_gaps":
            result["data_gaps"] = item.get("data_gaps", [])
    return result


def _company_business_profile(components: Mapping[str, Any]) -> Mapping[str, Any]:
    context = components.get("ticker_research_context_skeleton")
    if isinstance(context, Mapping) and isinstance(
        context.get("company_business_profile"),
        Mapping,
    ):
        return context["company_business_profile"]
    section = _scaffold_section(
        components["evidence_aware_research_pack_scaffold"],
        "company_business_profile",
    )
    result = {
        "business_segments": [],
        "main_products": [],
        "revenue_structure": [],
        "downstream_or_end_markets": [],
        "evidence_status": section.get("evidence_status", "data_gap"),
        "data_gaps": [],
        "caveats": section.get("caveats", []),
    }
    for item in _list_from_mapping(section, "items"):
        item_id = item.get("item_id")
        if item_id in {
            "business_segments",
            "main_products",
            "revenue_structure",
            "downstream_or_end_markets",
        }:
            result[item_id] = item.get("value", [])
        elif item_id == "company_business_data_gaps":
            result["data_gaps"] = item.get("data_gaps", [])
    return result


def _industry_context(components: Mapping[str, Any]) -> Mapping[str, Any]:
    context = components.get("ticker_research_context_skeleton")
    if isinstance(context, Mapping) and isinstance(context.get("industry_context"), Mapping):
        return context["industry_context"]
    section = _scaffold_section(
        components["evidence_aware_research_pack_scaffold"],
        "industry_context",
    )
    result = {
        "possible_industry_frameworks": [],
        "industry_driver_questions": [],
        "industry_data_gaps": [],
        "evidence_status": section.get("evidence_status", "not_assessable"),
    }
    for item in _list_from_mapping(section, "items"):
        if item.get("item_id") == "possible_industry_frameworks":
            result["possible_industry_frameworks"] = item.get(
                "possible_industry_frameworks",
                [],
            )
        elif item.get("item_id") == "industry_driver_questions":
            result["industry_driver_questions"] = item.get("industry_driver_questions", [])
        elif item.get("item_id") == "industry_data_gaps":
            result["industry_data_gaps"] = item.get("industry_data_gaps", [])
    return result


def _macro_transmission(components: Mapping[str, Any]) -> Mapping[str, Any]:
    context = components.get("ticker_research_context_skeleton")
    if isinstance(context, Mapping) and isinstance(
        context.get("macro_transmission_path"),
        Mapping,
    ):
        return context["macro_transmission_path"]
    section = _scaffold_section(
        components["evidence_aware_research_pack_scaffold"],
        "macro_transmission",
    )
    result = {
        "macro_variables_to_investigate": [],
        "industry_to_company_transmission_questions": [],
        "data_gaps": [],
        "caveats": section.get("caveats", []),
    }
    for item in _list_from_mapping(section, "items"):
        if item.get("item_id") == "macro_variables_to_investigate":
            result["macro_variables_to_investigate"] = item.get(
                "macro_variables_to_investigate",
                [],
            )
        elif item.get("item_id") == "industry_to_company_transmission_questions":
            result["industry_to_company_transmission_questions"] = item.get(
                "industry_to_company_transmission_questions",
                [],
            )
        elif item.get("item_id") == "macro_transmission_data_gaps":
            result["data_gaps"] = item.get("data_gaps", [])
    return result


def _research_questions(components: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    context = components.get("ticker_research_context_skeleton")
    if isinstance(context, Mapping):
        question_set = context.get("research_questions")
        if isinstance(question_set, Mapping):
            return _list_from_mapping(question_set, "questions")
    section = _scaffold_section(
        components["evidence_aware_research_pack_scaffold"],
        "research_questions",
    )
    return _list_from_mapping(section, "items")


def _anchor_map(components: Mapping[str, Any]) -> Mapping[str, Any]:
    if isinstance(components.get("provider_metric_official_anchor_map"), Mapping):
        return components["provider_metric_official_anchor_map"]
    handoff = components.get("real_official_metadata_anchor_handoff_result")
    if isinstance(handoff, Mapping) and isinstance(handoff.get("anchor_map_result"), Mapping):
        return handoff["anchor_map_result"]
    return {}


def _scaffold_section(scaffold: Mapping[str, Any], section_id: str) -> Mapping[str, Any]:
    for section in _list_from_mapping(scaffold, "sections"):
        if section.get("section_id") == section_id:
            return section
    return {}


def _collect_top_level_data_gaps(components: Mapping[str, Any]) -> list[dict[str, Any]]:
    context = components.get("ticker_research_context_skeleton")
    if isinstance(context, Mapping):
        data_gap_plan = context.get("data_gap_plan")
        if isinstance(data_gap_plan, Mapping):
            return deepcopy(_list_from_mapping(data_gap_plan, "data_gaps"))
    scaffold = components["evidence_aware_research_pack_scaffold"]
    section = _scaffold_section(scaffold, "data_gaps")
    for item in _list_from_mapping(section, "items"):
        if item.get("item_id") == "high_priority_data_gaps":
            return deepcopy(_list_from_mapping(item, "data_gaps"))
    gaps: list[dict[str, Any]] = []
    for section in _list_from_mapping(scaffold, "sections"):
        for item in _list_from_mapping(section, "items"):
            for key in ("data_gaps", "industry_data_gaps"):
                for gap in _list_from_mapping(item, key):
                    gaps.append(deepcopy(dict(gap)))
    return _dedupe_dicts(gaps)


def _collect_next_data_tasks(components: Mapping[str, Any]) -> list[dict[str, Any]]:
    scaffold = components["evidence_aware_research_pack_scaffold"]
    tasks = deepcopy(_list_from_mapping(scaffold, "next_data_tasks"))
    for section in _list_from_mapping(scaffold, "sections"):
        tasks.extend(deepcopy(_list_from_mapping(section, "next_data_tasks")))
    return _dedupe_dicts(tasks)


def _collect_blocked_reasons(components: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    for component in components.values():
        if isinstance(component, Mapping):
            reasons.extend(_string_values(component.get("blocked_reasons")))
            handoff_anchor = component.get("anchor_map_result")
            if isinstance(handoff_anchor, Mapping):
                reasons.extend(_string_values(handoff_anchor.get("blocked_reasons")))
    return _dedupe_preserve_order(reasons)


def _component_caveats(components: Mapping[str, Any]) -> list[str]:
    caveats: list[str] = []
    for component in components.values():
        if isinstance(component, Mapping):
            caveats.extend(_string_values(component.get("caveats")))
    return _dedupe_preserve_order(caveats)


def _tasks_from_gaps(gaps: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    tasks = []
    for index, gap in enumerate(gaps):
        tasks.append(
            {
                "task_id": f"vertical_slice_gap_task_{index + 1:03d}",
                "gap_id": gap.get("gap_id"),
                "required_data": _string_values(gap.get("required_data")),
                "current_evidence_status": gap.get("current_evidence_status", "data_gap"),
                "priority": gap.get("priority", "medium"),
                "not_official_verified": True,
                "not_for_trading_advice": True,
            }
        )
    return tasks


def _artifact_metadata_item(item: Mapping[str, Any]) -> dict[str, Any]:
    sha256 = item.get("sha256")
    cache_filename = _cache_filename_from_path(item.get("cache_path"))
    artifact_status = item.get("artifact_status")
    return {
        "point_id": f"artifact_cache_metadata:{item.get('artifact_id')}",
        "source_title": item.get("source_title"),
        "source_domain": item.get("source_domain"),
        "final_domain": item.get("final_domain"),
        "file_size_bytes": item.get("file_size_bytes"),
        "sha256_prefix": sha256[:12] if isinstance(sha256, str) else None,
        "artifact_status": artifact_status,
        "cache_filename": cache_filename,
        "artifact_evidence_status": "artifact_cached"
        if _artifact_item_cached(item)
        else "blocked",
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }


def _cache_filename_from_path(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip().replace("\\", "/")
    return normalized.rsplit("/", 1)[-1] or None


def _anchor_item_matched(item: Mapping[str, Any]) -> bool:
    return item.get("official_anchor_status") in {"matched", "official_anchor_matched"}


def _artifact_item_cached(item: Mapping[str, Any]) -> bool:
    return item.get("artifact_status") in {"cached", "artifact_cached"}


def _anchor_title(item: Mapping[str, Any]) -> Any:
    anchor = item.get("official_disclosure_anchor")
    return anchor.get("source_title") if isinstance(anchor, Mapping) else None


def _anchor_domain(item: Mapping[str, Any]) -> Any:
    anchor = item.get("official_disclosure_anchor")
    return anchor.get("source_domain") if isinstance(anchor, Mapping) else None


def _resolve_identity(components: Mapping[str, Any], key: str) -> Any:
    for component_key in (
        "ticker_research_context_skeleton",
        "evidence_aware_research_pack_scaffold",
        "provider_metric_official_anchor_map",
        "official_disclosure_artifact_cache",
    ):
        component = components.get(component_key)
        if isinstance(component, Mapping) and component.get(key) not in (None, ""):
            return component.get(key)
    return None


def _explicit_official_verified_count(components: Mapping[str, Any]) -> int:
    context = components.get("ticker_research_context_skeleton")
    if isinstance(context, Mapping):
        summary = context.get("evidence_status_summary")
        if isinstance(summary, Mapping):
            return sum(
                1
                for status in _status_values(summary.get("official_evidence_statuses"))
                if status == "official_verified"
            )
    scaffold = components.get("evidence_aware_research_pack_scaffold")
    if isinstance(scaffold, Mapping):
        subject = _scaffold_section(scaffold, "research_subject")
        count = 0
        for item in _list_from_mapping(subject, "items"):
            count += sum(
                1
                for status in _status_values(item.get("official_evidence_statuses"))
                if status == "official_verified"
            )
        return count
    return 0


def _count_status_value(value: Any, target: str) -> int:
    count = 0

    def visit(child: Any, key_hint: str | None = None) -> None:
        nonlocal count
        if isinstance(child, Mapping):
            for key, nested in child.items():
                key_text = str(key)
                if key_text == "evidence_status_legend":
                    continue
                visit(nested, key_text)
            return
        if isinstance(child, list):
            for item in child:
                visit(item, key_hint)
            return
        if key_hint in _EVIDENCE_STATUS_FIELD_KEYS and child == target:
            count += 1

    visit(value)
    return count


def _validate_evidence_status_values(value: Any) -> None:
    def visit(child: Any, path: str) -> None:
        if isinstance(child, Mapping):
            for key, nested in child.items():
                key_text = str(key)
                next_path = f"{path}.{key_text}" if path else key_text
                if key_text in _EVIDENCE_STATUS_FIELD_KEYS:
                    _require_evidence_status_collection(nested, next_path)
                else:
                    visit(nested, next_path)
            return
        if isinstance(child, list):
            for index, item in enumerate(child):
                visit(item, f"{path}[{index}]")

    visit(value, "")


def _assert_candidate_anchor_artifact_inputs_not_promoted(components: Mapping[str, Any]) -> None:
    financial = _financial_context(components) if "evidence_aware_research_pack_scaffold" in components else {}
    for item in _list_from_mapping(financial, "key_metric_candidates"):
        if item.get("current_evidence_status") == "official_verified":
            raise LiveEvidenceAwareResearchPackVerticalSliceError(
                "provider_candidate cannot become official_verified"
            )
    for item in _list_from_mapping(_anchor_map(components), "anchor_items"):
        if item.get("official_anchor_status") == "official_verified":
            raise LiveEvidenceAwareResearchPackVerticalSliceError(
                "official_anchor_matched cannot become official_verified"
            )
        if item.get("official_verification_status") == "official_verified":
            raise LiveEvidenceAwareResearchPackVerticalSliceError(
                "pending provider item cannot become official_verified"
            )
    cache = components.get("official_disclosure_artifact_cache") or {}
    for item in _list_from_mapping(cache, "artifact_items"):
        if item.get("artifact_status") == "official_verified":
            raise LiveEvidenceAwareResearchPackVerticalSliceError(
                "artifact_cached cannot become official_verified"
            )


def _assert_candidate_anchor_artifact_not_promoted(vertical_slice: Mapping[str, Any]) -> None:
    for section in _list_from_mapping(vertical_slice, "sections"):
        section_id = section.get("section_id")
        if section_id in {
            "financial_candidate_summary",
            "official_anchor_and_artifact_status",
        } and _status_value_present(section, "official_verified"):
            raise LiveEvidenceAwareResearchPackVerticalSliceError(
                "candidate, anchor, or artifact section cannot claim official_verified"
            )


def _assert_no_cache_path_disclosure(value: Any) -> None:
    def visit(child: Any) -> None:
        if isinstance(child, Mapping):
            for key, nested in child.items():
                if key == "cache_path":
                    raise LiveEvidenceAwareResearchPackVerticalSliceError(
                        "vertical slice must not disclose cache_path"
                    )
                visit(nested)
            return
        if isinstance(child, list):
            for item in child:
                visit(item)

    visit(value)


def _reject_raw_component_keys(value: Mapping[str, Any]) -> None:
    raw_keys = sorted(key for key in _RAW_COMPONENT_KEYS if key in value)
    if raw_keys:
        raise LiveEvidenceAwareResearchPackVerticalSliceError(
            f"components contains raw inputs: {raw_keys}"
        )


def _reject_bytes(value: Any, path: str) -> None:
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise LiveEvidenceAwareResearchPackVerticalSliceError(
            f"{path} contains raw bytes"
        )
    if isinstance(value, Mapping):
        for key, child in value.items():
            _reject_bytes(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_bytes(child, f"{path}[{index}]")


def _present_sources(components: Mapping[str, Any], keys: list[str]) -> list[str]:
    return [key for key in keys if key in components]


def _preview_display_value(point: Mapping[str, Any]) -> str:
    for key in (
        "count",
        "present",
        "value",
        "provider_trend_periods",
        "source_title",
        "category",
        "blocked_conclusion",
    ):
        if key in point:
            return _compact_value(point[key])
    return "structured"


def _compact_value(value: Any) -> str:
    if isinstance(value, list):
        if not value:
            return "[]"
        return ", ".join(str(item) for item in value[:4])
    return str(value)


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
    statuses = _status_values(value)
    return _dedupe_preserve_order(statuses) if statuses else fallback


def _status_values(value: Any) -> list[str]:
    return [
        status
        for status in _string_values(value)
        if status in VERTICAL_SLICE_EVIDENCE_STATUSES
    ]


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


def _list_from_mapping(value: Any, key: str) -> list[Any]:
    if not isinstance(value, Mapping):
        return []
    items = value.get(key)
    return items if isinstance(items, list) else []


def _dedupe_dicts(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        deepcopy(item)
        for item in _dedupe_preserve_order(values)
        if isinstance(item, Mapping)
    ]


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


def _non_negative_int(value: Any, *, default: int = 0) -> int:
    if isinstance(value, int) and value >= 0:
        return value
    return default


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise LiveEvidenceAwareResearchPackVerticalSliceError(f"{field} must be a mapping")
    return value


def _require_fields(value: Mapping[str, Any], fields: tuple[str, ...], path: str) -> None:
    missing = [field for field in fields if field not in value]
    if missing:
        raise LiveEvidenceAwareResearchPackVerticalSliceError(
            f"{path} missing required fields: {missing}"
        )


def _require_schema_version(value: Any, expected: str, path: str) -> None:
    if value != expected:
        raise LiveEvidenceAwareResearchPackVerticalSliceError(
            f"{path} must be {expected}"
        )


def _require_optional_string(value: Any, path: str) -> None:
    if value is not None and not isinstance(value, str):
        raise LiveEvidenceAwareResearchPackVerticalSliceError(
            f"{path} must be a string or null"
        )


def _require_non_empty_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LiveEvidenceAwareResearchPackVerticalSliceError(
            f"{path} must be a non-empty string"
        )
    return value


def _require_string_list(value: Any, path: str) -> list[str]:
    if not isinstance(value, list):
        raise LiveEvidenceAwareResearchPackVerticalSliceError(f"{path} must be a list")
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise LiveEvidenceAwareResearchPackVerticalSliceError(
                f"{path}[{index}] must be a string"
            )
    return value


def _require_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise LiveEvidenceAwareResearchPackVerticalSliceError(f"{path} must be a list")
    return value


def _require_true(value: Any, path: str) -> None:
    if value is not True:
        raise LiveEvidenceAwareResearchPackVerticalSliceError(f"{path} must be true")


def _require_non_negative_int(value: Any, path: str) -> int:
    if not isinstance(value, int) or value < 0:
        raise LiveEvidenceAwareResearchPackVerticalSliceError(
            f"{path} must be a non-negative int"
        )
    return value


def _require_evidence_status(value: Any, path: str) -> str:
    if not isinstance(value, str) or value not in VERTICAL_SLICE_EVIDENCE_STATUSES:
        raise LiveEvidenceAwareResearchPackVerticalSliceError(
            f"{path} must be one of {VERTICAL_SLICE_EVIDENCE_STATUSES}"
        )
    return value


def _require_evidence_status_collection(value: Any, path: str) -> list[str] | str:
    if isinstance(value, str):
        return _require_evidence_status(value, path)
    if not isinstance(value, list):
        raise LiveEvidenceAwareResearchPackVerticalSliceError(
            f"{path} must be an evidence status or list"
        )
    if not value:
        raise LiveEvidenceAwareResearchPackVerticalSliceError(f"{path} cannot be empty")
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
    if value in _CONTROLLED_DISCLAIMER_TEXTS:
        return None
    searchable_value = value
    for disclaimer in _CONTROLLED_DISCLAIMER_TEXTS:
        searchable_value = searchable_value.replace(disclaimer, "")
    if allow_evidence_status and value in VERTICAL_SLICE_EVIDENCE_STATUSES:
        return None
    if value in VERTICAL_SLICE_EVIDENCE_STATUSES and value != "official_verified":
        return None
    if _contains_official_verified_text(searchable_value):
        return "official_verified"
    lowered = searchable_value.casefold()
    separator_normalized = _normalize_separator_text(searchable_value)
    normalized_marker = _normalise_marker(searchable_value)

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
    if any(marker in searchable_value for marker in _FORBIDDEN_CJK_MARKERS):
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
    "LIVE_EVIDENCE_AWARE_RESEARCH_PACK_VERTICAL_SLICE_SCHEMA_VERSION",
    "LIVE_EVIDENCE_RESEARCH_PACK_SECTION_SCHEMA_VERSION",
    "LIVE_EVIDENCE_STATUS_ROLLUP_SCHEMA_VERSION",
    "SECTION_IDS",
    "VERTICAL_SLICE_EVIDENCE_STATUSES",
    "LiveEvidenceAwareResearchPackVerticalSliceError",
    "assert_no_live_research_pack_forbidden_markers",
    "build_business_industry_macro_section",
    "build_cannot_conclude_yet_section",
    "build_company_business_profile_section",
    "build_data_gap_section",
    "build_evidence_status_rollup",
    "build_evidence_status_summary_section",
    "build_financial_candidate_section",
    "build_industry_and_macro_context_section",
    "build_live_evidence_aware_research_pack_vertical_slice",
    "build_official_anchor_and_artifact_section",
    "build_research_question_section",
    "build_subject_section",
    "build_vertical_slice_markdown_preview",
    "validate_live_evidence_aware_research_pack_vertical_slice",
]
