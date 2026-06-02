# -*- coding: utf-8 -*-
"""In-memory adapter from Analysis Brief to Report V1 compatibility context.

This module deliberately stops before Report V1 construction or presentation.
It accepts only an already validated user-facing analysis brief and emits a
standalone compatibility payload for future integration work.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from copy import deepcopy
import re
from typing import Any

from .user_facing_analysis_brief import (
    ANALYSIS_LABELS,
    LABEL_CANNOT_CONCLUDE,
    LABEL_DATA_GAP,
    LABEL_INFERENCE,
    LABEL_PENDING,
    LABEL_RELIABLE,
    USER_FACING_ANALYSIS_BRIEF_SCHEMA_VERSION,
    USER_FACING_ANALYSIS_BRIEF_SECTION_SCHEMA_VERSION,
    USER_VISIBLE_SECTION_IDS,
    validate_user_facing_analysis_brief,
)


ANALYSIS_BRIEF_REPORT_V1_COMPATIBILITY_PAYLOAD_SCHEMA_VERSION = (
    "analysis_brief_report_v1_compatibility_payload.v1"
)
ANALYSIS_BRIEF_REPORT_V1_CONTEXT_BLOCK_SCHEMA_VERSION = (
    "analysis_brief_report_v1_context_block.v1"
)
ANALYSIS_BRIEF_REPORT_V1_LABEL_TRANSLATION_SCHEMA_VERSION = (
    "analysis_brief_report_v1_label_translation.v1"
)
ANALYSIS_BRIEF_REPORT_V1_BACKEND_GROUNDING_SANITIZED_SCHEMA_VERSION = (
    "analysis_brief_report_v1_backend_grounding_sanitized.v1"
)

REPORT_V1_LABEL_VERIFIED_FACT = "verified_fact"
REPORT_V1_LABEL_AUTO_ACCEPTED_CANDIDATE = "auto_accepted_candidate"
REPORT_V1_LABEL_MANUAL_REVIEW_REQUIRED = "manual_review_required"
REPORT_V1_LABEL_UNSUPPORTED_ASSUMPTION = "unsupported_assumption"
REPORT_V1_LABEL_COVERAGE_CAVEAT = "coverage_caveat"
REPORT_V1_LABEL_FORWARD_TRACKING_VARIABLE = "forward_tracking_variable"

REPORT_V1_EVIDENCE_LABELS = (
    REPORT_V1_LABEL_VERIFIED_FACT,
    REPORT_V1_LABEL_AUTO_ACCEPTED_CANDIDATE,
    REPORT_V1_LABEL_MANUAL_REVIEW_REQUIRED,
    REPORT_V1_LABEL_UNSUPPORTED_ASSUMPTION,
    REPORT_V1_LABEL_COVERAGE_CAVEAT,
    REPORT_V1_LABEL_FORWARD_TRACKING_VARIABLE,
)

_ALLOWED_EMITTED_REPORT_V1_LABELS = tuple(
    label for label in REPORT_V1_EVIDENCE_LABELS if label != REPORT_V1_LABEL_VERIFIED_FACT
)

_BRIEF_TOP_LEVEL_KEYS = {
    "schema_version",
    "stock_code",
    "ts_code",
    "company_name_hint",
    "brief_type",
    "source_component_summary",
    "analysis_labels_legend",
    "user_visible_sections",
    "markdown_preview",
    "backend_grounding_summary",
    "caveats",
    "not_official_verified",
    "not_for_trading_advice",
}

_PAYLOAD_CONTEXT_KEYS = (
    "subject_context",
    "executive_boundary_context",
    "business_context",
    "financial_context",
    "industry_macro_context",
    "risk_context",
    "evidence_gap_context",
    "follow_up_context",
    "rebuttal_context",
)

_PAYLOAD_TOP_LEVEL_KEYS = {
    "schema_version",
    "stock_code",
    "ts_code",
    "company_name_hint",
    "source_brief_schema_version",
    "source_brief_preview_available",
    *_PAYLOAD_CONTEXT_KEYS,
    "label_translation_summary",
    "backend_grounding_summary_sanitized",
    "dropped_backend_fields_summary",
    "blocked_reasons",
    "caveats",
    "not_official_verified",
    "not_for_trading_advice",
}

_SECTION_MAPPING: dict[str, tuple[str, tuple[str, ...]]] = {
    "subject_summary": ("subject_context", ("executive_summary",)),
    "current_judgment_boundary": (
        "executive_boundary_context",
        ("data_quality_assessment",),
    ),
    "business_logic": ("business_context", ("company_fundamentals",)),
    "financial_interpretation": (
        "financial_context",
        ("company_fundamentals", "data_quality_assessment"),
    ),
    "industry_macro_context": (
        "industry_macro_context",
        ("macro_context", "industry_context"),
    ),
    "risk_points": ("risk_context", ("risk_analysis",)),
    "data_gaps_that_matter": ("evidence_gap_context", ("evidence_gaps",)),
    "tracking_indicators": ("follow_up_context", ("follow_up_variables",)),
    "cannot_conclude_yet": (
        "rebuttal_context",
        ("rebuttal_conditions", "evidence_gaps"),
    ),
}

_SANITIZED_BACKEND_KEYS = (
    "audit_trace_available",
    "official_anchor_available",
    "artifact_cached_available",
    "locator_available",
    "provider_candidate_present",
    "pending_verification_count",
    "official_verified_count",
    "data_gap_count",
)

_FORBIDDEN_BACKEND_TRACE_KEYS = {
    "anchor_map",
    "cache_path",
    "fixture_path",
    "fixture_paths",
    "full_anchor_map",
    "full_locator_hits",
    "full_official_metadata",
    "full_provider_queue",
    "locator_hits",
    "official_metadata",
    "output_artifact_path",
    "output_artifact_paths",
    "page_number",
    "provider_queue",
    "raw_pdf_text",
    "sha256",
    "snippet",
    "source_url",
}

_RAW_INPUT_KEYS = {
    "arbitrary_url",
    "cache_file_bytes",
    "cache_file_content",
    "download_url",
    "final_url",
    "http_response",
    "pdf_bytes",
    "pdf_url",
    "provider_queue",
    "raw_http_response",
    "raw_locator_result",
    "raw_orchestration_result",
    "raw_pdf_bytes",
    "raw_provider_queue",
    "source_url",
    "url",
}

_ALLOWED_EXACT_TEXTS = {
    "not_for_trading_advice",
    "not_official_verified",
    "official_verified_count",
    "\u5b98\u65b9\u6307\u6807\u6838\u9a8c\u5c1a\u672a\u5b8c\u6210",
}

_FORBIDDEN_MARKERS = (
    "token",
    ".env",
    "tushare_token",
    "official_metric_fact",
    "provider_official_conflict",
    "Report V1 artifact",
    "HTML artifact",
    "accepted manifest write",
    "output baseline write",
    "fixture write",
    "buy",
    "sell",
    "hold",
    "target price",
    "portfolio",
    "position",
    "technical signal",
    "trading advice",
    "investment advice",
    "OCR",
    "table extraction",
    "table extractor",
    "metric extraction",
    "provider-official reconciliation",
    "official value",
    "metric value",
    "page_number",
    "snippet",
    "source_url",
    "sha256",
    "cache_path",
    "output artifact path",
    "fixture path",
    REPORT_V1_LABEL_VERIFIED_FACT,
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
    "OCR",
    "\u8868\u683c\u62bd\u53d6",
    "\u8868\u683c\u89e3\u6790",
    "\u6307\u6807\u62bd\u53d6",
    "\u5b98\u65b9\u6307\u6807\u4e8b\u5b9e",
    "\u6307\u6807\u6838\u9a8c",
    "\u4e00\u81f4\u6027\u6838\u9a8c",
    "\u884c\u4e1a\u666f\u6c14",
    "\u5b8f\u89c2\u5229\u597d",
    "\u516c\u53f8\u53d7\u76ca",
    "\u6838\u5fc3\u6295\u8d44\u903b\u8f91\u6210\u7acb",
    "\u7b2c\u51e0\u9875",
    "\u9875\u7801",
    "\u539f\u6587\u7247\u6bb5",
    "\u6765\u6e90\u94fe\u63a5",
    "\u54c8\u5e0c",
    "\u7f13\u5b58\u8def\u5f84",
)

_WORD_MARKERS = {"token", "buy", "sell", "hold", "portfolio", "position"}

_TOKEN_LIKE_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._-]{8,}\b", re.IGNORECASE),
)


class AnalysisBriefReportV1AdapterError(ValueError):
    """Raised when the compatibility adapter fails closed."""


def build_analysis_brief_report_v1_compatibility_payload(
    brief: Mapping[str, Any],
) -> dict[str, Any]:
    """Build an in-memory compatibility payload from a user-facing brief."""

    source = _validate_brief_input_for_adapter(brief)
    sections_by_id = {section["section_id"]: section for section in source["user_visible_sections"]}

    payload: dict[str, Any] = {
        "schema_version": ANALYSIS_BRIEF_REPORT_V1_COMPATIBILITY_PAYLOAD_SCHEMA_VERSION,
        "stock_code": source["stock_code"],
        "ts_code": source["ts_code"],
        "company_name_hint": source["company_name_hint"],
        "source_brief_schema_version": source["schema_version"],
        "source_brief_preview_available": bool(source.get("markdown_preview")),
        "label_translation_summary": _build_label_translation_summary_from_validated(
            source
        ),
        "backend_grounding_summary_sanitized": (
            _build_backend_grounding_summary_sanitized_from_validated(source)
        ),
        "dropped_backend_fields_summary": {
            "raw_trace_details_included": False,
            "sanitized_backend_key_count": len(_SANITIZED_BACKEND_KEYS),
            "blocked_backend_trace_input_detected": False,
            "not_for_trading_advice": True,
        },
        "blocked_reasons": [],
        "caveats": [
            "Compatibility payload is in-memory only.",
            "Backend evidence details are summarized only.",
            "Stronger fact labels require future reviewed-source integration.",
        ],
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }
    for section_id in USER_VISIBLE_SECTION_IDS:
        context_key, target_sections = _SECTION_MAPPING[section_id]
        payload[context_key] = build_context_block_from_analysis_section(
            sections_by_id[section_id],
            target_report_v1_section=target_sections,
        )
    return validate_analysis_brief_report_v1_compatibility_payload(payload)


def validate_analysis_brief_report_v1_compatibility_payload(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate and return a defensive copy of a compatibility payload."""

    source = _require_mapping(payload, "payload")
    unsupported = sorted(set(source) - _PAYLOAD_TOP_LEVEL_KEYS)
    if unsupported:
        raise AnalysisBriefReportV1AdapterError(
            f"payload contains unsupported keys: {unsupported}"
        )
    _require_fields(source, tuple(sorted(_PAYLOAD_TOP_LEVEL_KEYS)), "payload")
    assert_no_analysis_brief_report_v1_adapter_forbidden_markers(source)
    result = deepcopy(dict(source))

    if result["schema_version"] != ANALYSIS_BRIEF_REPORT_V1_COMPATIBILITY_PAYLOAD_SCHEMA_VERSION:
        raise AnalysisBriefReportV1AdapterError("invalid payload schema_version")
    if result["source_brief_schema_version"] != USER_FACING_ANALYSIS_BRIEF_SCHEMA_VERSION:
        raise AnalysisBriefReportV1AdapterError("invalid source brief schema_version")
    _require_optional_string(result["stock_code"], "stock_code")
    _require_optional_string(result["ts_code"], "ts_code")
    _require_optional_string(result["company_name_hint"], "company_name_hint")
    _require_bool(result["source_brief_preview_available"], "source_brief_preview_available")
    _require_true(result["not_official_verified"], "not_official_verified")
    _require_true(result["not_for_trading_advice"], "not_for_trading_advice")
    for context_key in _PAYLOAD_CONTEXT_KEYS:
        result[context_key] = _validate_context_block(result[context_key], context_key)
    result["label_translation_summary"] = _validate_label_translation_summary(
        result["label_translation_summary"]
    )
    result["backend_grounding_summary_sanitized"] = (
        _validate_backend_grounding_summary_sanitized(
            result["backend_grounding_summary_sanitized"]
        )
    )
    result["dropped_backend_fields_summary"] = _validate_dropped_backend_fields_summary(
        result["dropped_backend_fields_summary"]
    )
    _require_string_list(result["blocked_reasons"], "blocked_reasons")
    _require_string_list(result["caveats"], "caveats")
    _assert_no_default_verified_fact_promotion(result)
    return result


def translate_analysis_label_to_report_v1_label(
    label: str,
    *,
    explicit_reviewed_source: bool = False,
) -> str:
    """Translate an Analysis Brief label without promoting candidates by default."""

    if not isinstance(explicit_reviewed_source, bool):
        raise AnalysisBriefReportV1AdapterError("explicit_reviewed_source must be bool")
    if label not in ANALYSIS_LABELS:
        raise AnalysisBriefReportV1AdapterError("unsupported analysis label")
    if label == LABEL_RELIABLE and explicit_reviewed_source:
        return REPORT_V1_LABEL_VERIFIED_FACT
    if label in (LABEL_RELIABLE, LABEL_PENDING):
        return REPORT_V1_LABEL_MANUAL_REVIEW_REQUIRED
    if label == LABEL_DATA_GAP:
        return REPORT_V1_LABEL_COVERAGE_CAVEAT
    if label == LABEL_INFERENCE:
        return REPORT_V1_LABEL_UNSUPPORTED_ASSUMPTION
    if label == LABEL_CANNOT_CONCLUDE:
        return REPORT_V1_LABEL_COVERAGE_CAVEAT
    raise AnalysisBriefReportV1AdapterError("unsupported analysis label")


def build_context_block_from_analysis_section(
    section: Mapping[str, Any],
    *,
    target_report_v1_section: str | Iterable[str],
) -> dict[str, Any]:
    """Build one compatibility context block from a user-visible section."""

    source = _validate_analysis_section_for_adapter(section)
    target_sections = _normalise_target_sections(target_report_v1_section)
    block = {
        "schema_version": ANALYSIS_BRIEF_REPORT_V1_CONTEXT_BLOCK_SCHEMA_VERSION,
        "source_section_id": source["section_id"],
        "target_report_v1_section": list(target_sections),
        "source_analysis_label": source["analysis_label"],
        "translated_evidence_label": _translate_label_for_target(
            source["analysis_label"],
            target_sections,
        ),
        "analysis_points": [
            _build_context_analysis_point(point, target_sections)
            for point in source["analysis_points"]
        ],
        "caveats": _context_block_caveats(source),
        "user_visible": True,
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }
    return _validate_context_block(block, "context_block")


def build_backend_grounding_summary_sanitized(
    brief: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the allowed backend availability summary only."""

    source = _validate_brief_input_for_adapter(brief)
    return _build_backend_grounding_summary_sanitized_from_validated(source)


def build_label_translation_summary(brief: Mapping[str, Any]) -> dict[str, Any]:
    """Summarize emitted label translations across the brief."""

    source = _validate_brief_input_for_adapter(brief)
    return _build_label_translation_summary_from_validated(source)


def assert_no_analysis_brief_report_v1_adapter_forbidden_markers(value: Any) -> None:
    """Reject adapter-forbidden markers in nested mappings, lists, and strings."""

    finding = _find_forbidden_marker(value)
    if finding:
        raise AnalysisBriefReportV1AdapterError(
            f"analysis brief Report V1 adapter safety violation: forbidden marker: {finding}"
        )


def _validate_brief_input_for_adapter(brief: Mapping[str, Any]) -> dict[str, Any]:
    source = validate_user_facing_analysis_brief(brief)
    unsupported = sorted(set(source) - _BRIEF_TOP_LEVEL_KEYS)
    if unsupported:
        raise AnalysisBriefReportV1AdapterError(
            f"brief contains unsupported keys for adapter: {unsupported}"
        )
    if source["schema_version"] != USER_FACING_ANALYSIS_BRIEF_SCHEMA_VERSION:
        raise AnalysisBriefReportV1AdapterError("brief must be user_facing_analysis_brief.v1")
    _reject_raw_inputs(source)
    _assert_no_forbidden_backend_trace_keys(
        {
            "user_visible_sections": source["user_visible_sections"],
            "backend_grounding_summary": source["backend_grounding_summary"],
        }
    )
    assert_no_analysis_brief_report_v1_adapter_forbidden_markers(source)
    return deepcopy(source)


def _build_backend_grounding_summary_sanitized_from_validated(
    brief: Mapping[str, Any],
) -> dict[str, Any]:
    source_summary = _require_mapping(
        brief["backend_grounding_summary"],
        "backend_grounding_summary",
    )
    summary: dict[str, Any] = {
        "schema_version": (
            ANALYSIS_BRIEF_REPORT_V1_BACKEND_GROUNDING_SANITIZED_SCHEMA_VERSION
        ),
        "not_for_trading_advice": True,
    }
    for key in _SANITIZED_BACKEND_KEYS:
        summary[key] = source_summary.get(key, 0 if key.endswith("_count") else False)
    return _validate_backend_grounding_summary_sanitized(summary)


def _build_label_translation_summary_from_validated(
    brief: Mapping[str, Any],
) -> dict[str, Any]:
    translation_counter: Counter[str] = Counter()
    source_labels: list[str] = []
    translation_items: list[dict[str, Any]] = []
    for section in brief["user_visible_sections"]:
        _, target_sections = _SECTION_MAPPING[section["section_id"]]
        source_label = section["analysis_label"]
        translated_label = _translate_label_for_target(source_label, target_sections)
        source_labels.append(source_label)
        translation_counter[translated_label] += 1
        translation_items.append(
            {
                "schema_version": (
                    ANALYSIS_BRIEF_REPORT_V1_LABEL_TRANSLATION_SCHEMA_VERSION
                ),
                "source_section_id": section["section_id"],
                "source_analysis_label": source_label,
                "translated_evidence_label": translated_label,
                "explicit_reviewed_source": False,
                "not_for_trading_advice": True,
            }
        )
    summary = {
        "schema_version": ANALYSIS_BRIEF_REPORT_V1_LABEL_TRANSLATION_SCHEMA_VERSION,
        "default_explicit_reviewed_source": False,
        "source_labels_seen": _dedupe_preserve_order(source_labels),
        "target_labels_emitted": sorted(translation_counter),
        "translation_counts": dict(sorted(translation_counter.items())),
        "translations": translation_items,
        "official_fact_promotion_blocked": True,
        "tracking_inference_as_follow_up_variable": any(
            item["translated_evidence_label"]
            == REPORT_V1_LABEL_FORWARD_TRACKING_VARIABLE
            for item in translation_items
        ),
        "not_for_trading_advice": True,
    }
    return _validate_label_translation_summary(summary)


def _build_context_analysis_point(
    point: Mapping[str, Any],
    target_sections: tuple[str, ...],
) -> dict[str, Any]:
    source = _require_mapping(point, "analysis_point")
    _require_fields(source, ("label", "text"), "analysis_point")
    label = source["label"]
    if label not in ANALYSIS_LABELS:
        raise AnalysisBriefReportV1AdapterError("analysis point label invalid")
    text = _require_non_empty_string(source["text"], "analysis_point.text")
    result = {
        "source_label": label,
        "translated_evidence_label": _translate_label_for_target(label, target_sections),
        "text": text,
    }
    assert_no_analysis_brief_report_v1_adapter_forbidden_markers(result)
    return result


def _translate_label_for_target(label: str, target_sections: tuple[str, ...]) -> str:
    if "follow_up_variables" in target_sections and label == LABEL_INFERENCE:
        return REPORT_V1_LABEL_FORWARD_TRACKING_VARIABLE
    return translate_analysis_label_to_report_v1_label(label)


def _context_block_caveats(section: Mapping[str, Any]) -> list[str]:
    evidence_statuses = _string_values(section.get("evidence_statuses"))
    caveats = [
        "Context block carries analysis wording only.",
        "Backend trace details are not included.",
    ]
    if evidence_statuses:
        caveats.append("Evidence status names are source-side labels only.")
    return caveats


def _validate_analysis_section_for_adapter(section: Mapping[str, Any]) -> dict[str, Any]:
    source = _require_mapping(section, "section")
    _require_fields(
        source,
        (
            "schema_version",
            "section_id",
            "section_title",
            "analysis_label",
            "evidence_statuses",
            "analysis_points",
            "not_official_verified",
            "not_for_trading_advice",
        ),
        "section",
    )
    result = deepcopy(dict(source))
    if result["schema_version"] != USER_FACING_ANALYSIS_BRIEF_SECTION_SCHEMA_VERSION:
        raise AnalysisBriefReportV1AdapterError("invalid section schema_version")
    if result["section_id"] not in USER_VISIBLE_SECTION_IDS:
        raise AnalysisBriefReportV1AdapterError("unsupported section_id")
    if result["analysis_label"] not in ANALYSIS_LABELS:
        raise AnalysisBriefReportV1AdapterError("invalid section analysis_label")
    _require_string_list(result["evidence_statuses"], "section.evidence_statuses")
    points = _require_list(result["analysis_points"], "section.analysis_points")
    if not points:
        raise AnalysisBriefReportV1AdapterError("section.analysis_points cannot be empty")
    _require_true(result["not_official_verified"], "section.not_official_verified")
    _require_true(result["not_for_trading_advice"], "section.not_for_trading_advice")
    _assert_no_forbidden_backend_trace_keys(result)
    assert_no_analysis_brief_report_v1_adapter_forbidden_markers(result)
    return result


def _validate_context_block(value: Any, path: str) -> dict[str, Any]:
    block = _require_mapping(value, path)
    required = (
        "schema_version",
        "source_section_id",
        "target_report_v1_section",
        "source_analysis_label",
        "translated_evidence_label",
        "analysis_points",
        "caveats",
        "user_visible",
        "not_official_verified",
        "not_for_trading_advice",
    )
    _require_fields(block, required, path)
    result = deepcopy(dict(block))
    if result["schema_version"] != ANALYSIS_BRIEF_REPORT_V1_CONTEXT_BLOCK_SCHEMA_VERSION:
        raise AnalysisBriefReportV1AdapterError(f"{path}.schema_version invalid")
    if result["source_section_id"] not in USER_VISIBLE_SECTION_IDS:
        raise AnalysisBriefReportV1AdapterError(f"{path}.source_section_id invalid")
    if result["source_analysis_label"] not in ANALYSIS_LABELS:
        raise AnalysisBriefReportV1AdapterError(f"{path}.source_analysis_label invalid")
    _normalise_target_sections(result["target_report_v1_section"])
    if result["translated_evidence_label"] not in _ALLOWED_EMITTED_REPORT_V1_LABELS:
        raise AnalysisBriefReportV1AdapterError(
            f"{path}.translated_evidence_label invalid"
        )
    points = _require_list(result["analysis_points"], f"{path}.analysis_points")
    if not points:
        raise AnalysisBriefReportV1AdapterError(f"{path}.analysis_points cannot be empty")
    for index, point in enumerate(points):
        _validate_context_analysis_point(point, f"{path}.analysis_points[{index}]")
    _require_string_list(result["caveats"], f"{path}.caveats")
    _require_true(result["user_visible"], f"{path}.user_visible")
    _require_true(result["not_official_verified"], f"{path}.not_official_verified")
    _require_true(result["not_for_trading_advice"], f"{path}.not_for_trading_advice")
    _assert_no_forbidden_backend_trace_keys(result)
    assert_no_analysis_brief_report_v1_adapter_forbidden_markers(result)
    return result


def _validate_context_analysis_point(value: Any, path: str) -> dict[str, Any]:
    point = _require_mapping(value, path)
    _require_fields(point, ("source_label", "translated_evidence_label", "text"), path)
    result = deepcopy(dict(point))
    if result["source_label"] not in ANALYSIS_LABELS:
        raise AnalysisBriefReportV1AdapterError(f"{path}.source_label invalid")
    if result["translated_evidence_label"] not in _ALLOWED_EMITTED_REPORT_V1_LABELS:
        raise AnalysisBriefReportV1AdapterError(
            f"{path}.translated_evidence_label invalid"
        )
    _require_non_empty_string(result["text"], f"{path}.text")
    assert_no_analysis_brief_report_v1_adapter_forbidden_markers(result)
    return result


def _validate_label_translation_summary(value: Any) -> dict[str, Any]:
    summary = _require_mapping(value, "label_translation_summary")
    required = (
        "schema_version",
        "default_explicit_reviewed_source",
        "source_labels_seen",
        "target_labels_emitted",
        "translation_counts",
        "translations",
        "official_fact_promotion_blocked",
        "tracking_inference_as_follow_up_variable",
        "not_for_trading_advice",
    )
    _require_fields(summary, required, "label_translation_summary")
    result = deepcopy(dict(summary))
    if result["schema_version"] != ANALYSIS_BRIEF_REPORT_V1_LABEL_TRANSLATION_SCHEMA_VERSION:
        raise AnalysisBriefReportV1AdapterError(
            "label_translation_summary schema_version invalid"
        )
    _require_false(
        result["default_explicit_reviewed_source"],
        "default_explicit_reviewed_source",
    )
    _require_true(
        result["official_fact_promotion_blocked"],
        "official_fact_promotion_blocked",
    )
    _require_bool(
        result["tracking_inference_as_follow_up_variable"],
        "tracking_inference_as_follow_up_variable",
    )
    _require_true(result["not_for_trading_advice"], "label_translation_summary.not_for_trading_advice")
    for label in _require_string_list(result["source_labels_seen"], "source_labels_seen"):
        if label not in ANALYSIS_LABELS:
            raise AnalysisBriefReportV1AdapterError("source_labels_seen invalid")
    for label in _require_string_list(result["target_labels_emitted"], "target_labels_emitted"):
        if label not in _ALLOWED_EMITTED_REPORT_V1_LABELS:
            raise AnalysisBriefReportV1AdapterError("target_labels_emitted invalid")
    counts = _require_mapping(result["translation_counts"], "translation_counts")
    for label, count in counts.items():
        if label not in _ALLOWED_EMITTED_REPORT_V1_LABELS:
            raise AnalysisBriefReportV1AdapterError("translation_counts label invalid")
        _require_non_negative_int(count, f"translation_counts.{label}")
    translations = _require_list(result["translations"], "translations")
    if not translations:
        raise AnalysisBriefReportV1AdapterError("translations cannot be empty")
    for index, item in enumerate(translations):
        translation = _require_mapping(item, f"translations[{index}]")
        _require_fields(
            translation,
            (
                "schema_version",
                "source_section_id",
                "source_analysis_label",
                "translated_evidence_label",
                "explicit_reviewed_source",
                "not_for_trading_advice",
            ),
            f"translations[{index}]",
        )
        if (
            translation["schema_version"]
            != ANALYSIS_BRIEF_REPORT_V1_LABEL_TRANSLATION_SCHEMA_VERSION
        ):
            raise AnalysisBriefReportV1AdapterError("translation schema_version invalid")
        if translation["source_section_id"] not in USER_VISIBLE_SECTION_IDS:
            raise AnalysisBriefReportV1AdapterError("translation section invalid")
        if translation["source_analysis_label"] not in ANALYSIS_LABELS:
            raise AnalysisBriefReportV1AdapterError("translation source label invalid")
        if translation["translated_evidence_label"] not in _ALLOWED_EMITTED_REPORT_V1_LABELS:
            raise AnalysisBriefReportV1AdapterError("translation target label invalid")
        _require_false(
            translation["explicit_reviewed_source"],
            "translation.explicit_reviewed_source",
        )
        _require_true(
            translation["not_for_trading_advice"],
            "translation.not_for_trading_advice",
        )
    assert_no_analysis_brief_report_v1_adapter_forbidden_markers(result)
    return result


def _validate_backend_grounding_summary_sanitized(value: Any) -> dict[str, Any]:
    summary = _require_mapping(value, "backend_grounding_summary_sanitized")
    required = (
        "schema_version",
        *_SANITIZED_BACKEND_KEYS,
        "not_for_trading_advice",
    )
    _require_fields(summary, required, "backend_grounding_summary_sanitized")
    result = deepcopy(dict(summary))
    if (
        result["schema_version"]
        != ANALYSIS_BRIEF_REPORT_V1_BACKEND_GROUNDING_SANITIZED_SCHEMA_VERSION
    ):
        raise AnalysisBriefReportV1AdapterError(
            "backend_grounding_summary_sanitized schema_version invalid"
        )
    for key in _SANITIZED_BACKEND_KEYS:
        if key.endswith("_count"):
            _require_non_negative_int(result[key], key)
        else:
            _require_bool(result[key], key)
    _require_true(result["not_for_trading_advice"], "not_for_trading_advice")
    _assert_no_forbidden_backend_trace_keys(result)
    assert_no_analysis_brief_report_v1_adapter_forbidden_markers(result)
    return result


def _validate_dropped_backend_fields_summary(value: Any) -> dict[str, Any]:
    summary = _require_mapping(value, "dropped_backend_fields_summary")
    required = (
        "raw_trace_details_included",
        "sanitized_backend_key_count",
        "blocked_backend_trace_input_detected",
        "not_for_trading_advice",
    )
    _require_fields(summary, required, "dropped_backend_fields_summary")
    result = deepcopy(dict(summary))
    _require_false(result["raw_trace_details_included"], "raw_trace_details_included")
    _require_non_negative_int(
        result["sanitized_backend_key_count"],
        "sanitized_backend_key_count",
    )
    _require_false(
        result["blocked_backend_trace_input_detected"],
        "blocked_backend_trace_input_detected",
    )
    _require_true(result["not_for_trading_advice"], "not_for_trading_advice")
    assert_no_analysis_brief_report_v1_adapter_forbidden_markers(result)
    return result


def _assert_no_default_verified_fact_promotion(value: Any) -> None:
    if isinstance(value, Mapping):
        if value.get("translated_evidence_label") == REPORT_V1_LABEL_VERIFIED_FACT:
            raise AnalysisBriefReportV1AdapterError(
                "verified fact label requires explicit reviewed source"
            )
        for child in value.values():
            _assert_no_default_verified_fact_promotion(child)
        return
    if isinstance(value, list):
        for child in value:
            _assert_no_default_verified_fact_promotion(child)


def _reject_raw_inputs(value: Any, path: str = "brief") -> None:
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise AnalysisBriefReportV1AdapterError(f"{path} contains raw bytes")
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text in _RAW_INPUT_KEYS:
                raise AnalysisBriefReportV1AdapterError(
                    f"{path} contains unsupported raw input key: {key_text}"
                )
            _reject_raw_inputs(child, f"{path}.{key_text}")
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            _reject_raw_inputs(child, f"{path}[{index}]")


def _assert_no_forbidden_backend_trace_keys(value: Any, path: str = "value") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if _normalise_marker(key_text) in _FORBIDDEN_BACKEND_TRACE_KEYS:
                raise AnalysisBriefReportV1AdapterError(
                    f"{path} contains forbidden backend trace key: {key_text}"
                )
            _assert_no_forbidden_backend_trace_keys(child, f"{path}.{key_text}")
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            _assert_no_forbidden_backend_trace_keys(child, f"{path}[{index}]")


def _find_forbidden_marker(value: Any) -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text not in _ALLOWED_EXACT_TEXTS:
                key_finding = _text_forbidden_marker(key_text)
                if key_finding:
                    return key_finding
            child_finding = _find_forbidden_marker(child)
            if child_finding:
                return child_finding
        return None
    if isinstance(value, (list, tuple, set)):
        for item in value:
            item_finding = _find_forbidden_marker(item)
            if item_finding:
                return item_finding
        return None
    if isinstance(value, str):
        return _text_forbidden_marker(value)
    return None


def _text_forbidden_marker(value: str) -> str | None:
    if value in _ALLOWED_EXACT_TEXTS:
        return None
    searchable_value = value
    for allowed_text in _ALLOWED_EXACT_TEXTS:
        searchable_value = searchable_value.replace(allowed_text, "")
    for pattern in _TOKEN_LIKE_PATTERNS:
        if pattern.search(searchable_value):
            return "token_like_string"

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
            if re.search(
                rf"(?<![a-z0-9]){re.escape(marker_normalized)}(?![a-z0-9])",
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


def _normalise_target_sections(value: str | Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, str):
        values = (value,)
    elif isinstance(value, Iterable):
        values = tuple(value)
    else:
        raise AnalysisBriefReportV1AdapterError("target_report_v1_section invalid")
    result = tuple(item for item in values if isinstance(item, str) and item.strip())
    if not result:
        raise AnalysisBriefReportV1AdapterError("target_report_v1_section cannot be empty")
    return result


def _normalise_marker(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().casefold()).strip("_")


def _normalize_separator_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[_-]+", " ", value.strip().casefold())).strip()


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
        raise AnalysisBriefReportV1AdapterError(f"{field} must be a mapping")
    return value


def _require_fields(value: Mapping[str, Any], fields: tuple[str, ...], path: str) -> None:
    missing = [field for field in fields if field not in value]
    if missing:
        raise AnalysisBriefReportV1AdapterError(
            f"{path} missing required fields: {missing}"
        )


def _require_optional_string(value: Any, path: str) -> None:
    if value is not None and not isinstance(value, str):
        raise AnalysisBriefReportV1AdapterError(f"{path} must be string or null")


def _require_non_empty_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AnalysisBriefReportV1AdapterError(f"{path} must be a non-empty string")
    return value


def _require_string_list(value: Any, path: str) -> list[str]:
    if not isinstance(value, list):
        raise AnalysisBriefReportV1AdapterError(f"{path} must be a list")
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise AnalysisBriefReportV1AdapterError(f"{path}[{index}] must be string")
    return value


def _require_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise AnalysisBriefReportV1AdapterError(f"{path} must be a list")
    return value


def _require_true(value: Any, path: str) -> None:
    if value is not True:
        raise AnalysisBriefReportV1AdapterError(f"{path} must be true")


def _require_false(value: Any, path: str) -> None:
    if value is not False:
        raise AnalysisBriefReportV1AdapterError(f"{path} must be false")


def _require_bool(value: Any, path: str) -> None:
    if not isinstance(value, bool):
        raise AnalysisBriefReportV1AdapterError(f"{path} must be bool")


def _require_non_negative_int(value: Any, path: str) -> int:
    if not isinstance(value, int) or value < 0:
        raise AnalysisBriefReportV1AdapterError(f"{path} must be a non-negative int")
    return value


__all__ = [
    "ANALYSIS_BRIEF_REPORT_V1_BACKEND_GROUNDING_SANITIZED_SCHEMA_VERSION",
    "ANALYSIS_BRIEF_REPORT_V1_COMPATIBILITY_PAYLOAD_SCHEMA_VERSION",
    "ANALYSIS_BRIEF_REPORT_V1_CONTEXT_BLOCK_SCHEMA_VERSION",
    "ANALYSIS_BRIEF_REPORT_V1_LABEL_TRANSLATION_SCHEMA_VERSION",
    "REPORT_V1_EVIDENCE_LABELS",
    "REPORT_V1_LABEL_AUTO_ACCEPTED_CANDIDATE",
    "REPORT_V1_LABEL_COVERAGE_CAVEAT",
    "REPORT_V1_LABEL_FORWARD_TRACKING_VARIABLE",
    "REPORT_V1_LABEL_MANUAL_REVIEW_REQUIRED",
    "REPORT_V1_LABEL_UNSUPPORTED_ASSUMPTION",
    "REPORT_V1_LABEL_VERIFIED_FACT",
    "AnalysisBriefReportV1AdapterError",
    "assert_no_analysis_brief_report_v1_adapter_forbidden_markers",
    "build_analysis_brief_report_v1_compatibility_payload",
    "build_backend_grounding_summary_sanitized",
    "build_context_block_from_analysis_section",
    "build_label_translation_summary",
    "translate_analysis_label_to_report_v1_label",
    "validate_analysis_brief_report_v1_compatibility_payload",
]
