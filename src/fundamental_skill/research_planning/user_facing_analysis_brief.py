# -*- coding: utf-8 -*-
"""User-facing analysis brief draft thin slice.

This module turns an already-built orchestration result into a readable analysis
draft. It does not fetch live data, read files, parse PDFs, extract metrics, or
produce trading-oriented conclusions.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
import re
from typing import Any

from ..data_verification.official_artifact_evidence_locator import (
    OFFICIAL_ARTIFACT_EVIDENCE_LOCATOR_SCHEMA_VERSION,
    validate_official_artifact_evidence_locator,
)
from .live_evidence_research_pack_orchestration_entry import (
    LIVE_EVIDENCE_RESEARCH_PACK_ORCHESTRATION_RESULT_SCHEMA_VERSION,
    validate_live_evidence_research_pack_orchestration_result,
)


USER_FACING_ANALYSIS_BRIEF_SCHEMA_VERSION = "user_facing_analysis_brief.v1"
USER_FACING_ANALYSIS_BRIEF_SECTION_SCHEMA_VERSION = (
    "user_facing_analysis_brief_section.v1"
)
ANALYSIS_CONFIDENCE_LABEL_SCHEMA_VERSION = "analysis_confidence_label.v1"
BACKEND_GROUNDING_SUMMARY_SCHEMA_VERSION = "backend_grounding_summary.v1"

BRIEF_TYPE_USER_FACING_ANALYSIS_DRAFT = "user_facing_analysis_draft"

LABEL_RELIABLE = "\u8f83\u53ef\u9760"
LABEL_PENDING = "\u5f85\u6838\u9a8c"
LABEL_DATA_GAP = "\u6570\u636e\u7f3a\u53e3"
LABEL_INFERENCE = "\u63a8\u7406"
LABEL_CANNOT_CONCLUDE = "\u4e0d\u53ef\u5224\u65ad"

ANALYSIS_LABELS = (
    LABEL_RELIABLE,
    LABEL_PENDING,
    LABEL_DATA_GAP,
    LABEL_INFERENCE,
    LABEL_CANNOT_CONCLUDE,
)

USER_VISIBLE_SECTION_IDS = (
    "subject_summary",
    "current_judgment_boundary",
    "business_logic",
    "financial_interpretation",
    "industry_macro_context",
    "risk_points",
    "data_gaps_that_matter",
    "tracking_indicators",
    "cannot_conclude_yet",
)

_PAYLOAD_KEYS = {
    "orchestration_result",
    "locator_result",
    "analysis_mode",
    "allow_network",
    "not_for_trading_advice",
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
    "raw_pdf_bytes",
    "raw_provider_queue",
    "raw_tushare_provider_result",
    "source_url",
    "tushare_provider_result",
    "url",
}

_FORBIDDEN_USER_VISIBLE_KEYS = {
    "cache_path",
    "page_number",
    "sha256",
    "snippet",
    "source_url",
}

_BACKEND_GROUNDING_KEYS = {
    "schema_version",
    "default_visible",
    "audit_trace_available",
    "official_anchor_available",
    "artifact_cached_available",
    "locator_available",
    "provider_candidate_present",
    "pending_verification_count",
    "official_verified_count",
    "data_gap_count",
    "source_component_schema_versions",
    "grounding_notes",
    "not_for_trading_advice",
}

_ALLOWED_EXACT_TEXTS = {
    "not_for_trading_advice",
    "not_official_verified",
    "official_verified_count",
    "\u5b98\u65b9\u6307\u6807\u6838\u9a8c\u5c1a\u672a\u5b8c\u6210",
    "\u975e\u4ea4\u6613\u7528\u9014\u57fa\u672c\u9762\u5206\u6790\u8349\u7a3f",
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
_IDENTIFIER_SAFE_WORD_MARKERS = {"buy", "sell", "hold"}


class UserFacingAnalysisBriefError(ValueError):
    """Raised when the analysis brief fails closed."""


def build_user_facing_analysis_brief(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Build a user-facing analysis brief from explicit upstream results."""

    source = _validate_input_payload(payload)
    orchestration_result = validate_live_evidence_research_pack_orchestration_result(
        source["orchestration_result"]
    )
    locator_result = source.get("locator_result")
    if locator_result is not None:
        validate_official_artifact_evidence_locator(locator_result)
        locator_result = deepcopy(locator_result)

    sections = build_user_visible_sections(orchestration_result, locator_result)
    brief = {
        "schema_version": USER_FACING_ANALYSIS_BRIEF_SCHEMA_VERSION,
        "stock_code": _identity_value(orchestration_result, "stock_code"),
        "ts_code": _identity_value(orchestration_result, "ts_code"),
        "company_name_hint": _identity_value(orchestration_result, "company_name_hint"),
        "brief_type": BRIEF_TYPE_USER_FACING_ANALYSIS_DRAFT,
        "source_component_summary": _build_source_component_summary(
            orchestration_result,
            locator_result,
        ),
        "analysis_labels_legend": _analysis_labels_legend(),
        "user_visible_sections": sections,
        "markdown_preview": "",
        "backend_grounding_summary": build_backend_grounding_summary(
            orchestration_result,
            locator_result,
        ),
        "caveats": _brief_caveats(orchestration_result),
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }
    brief["markdown_preview"] = build_user_facing_analysis_markdown_preview(brief)
    return validate_user_facing_analysis_brief(brief)


def validate_user_facing_analysis_brief(brief: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and return a defensive copy of an analysis brief."""

    source = _require_mapping(brief, "brief")
    _require_fields(
        source,
        (
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
        ),
        "brief",
    )
    assert_no_user_facing_analysis_brief_forbidden_markers(source)
    result = deepcopy(dict(source))

    if result["schema_version"] != USER_FACING_ANALYSIS_BRIEF_SCHEMA_VERSION:
        raise UserFacingAnalysisBriefError("invalid brief schema_version")
    if result["brief_type"] != BRIEF_TYPE_USER_FACING_ANALYSIS_DRAFT:
        raise UserFacingAnalysisBriefError("invalid brief_type")
    _require_optional_string(result["stock_code"], "stock_code")
    _require_optional_string(result["ts_code"], "ts_code")
    _require_optional_string(result["company_name_hint"], "company_name_hint")
    _require_true(result["not_official_verified"], "not_official_verified")
    _require_true(result["not_for_trading_advice"], "not_for_trading_advice")

    result["analysis_labels_legend"] = _validate_analysis_labels_legend(
        result["analysis_labels_legend"]
    )
    result["user_visible_sections"] = _validate_user_visible_sections(
        result["user_visible_sections"],
        result["backend_grounding_summary"],
    )
    _validate_backend_grounding_summary(result["backend_grounding_summary"])
    _require_mapping(result["source_component_summary"], "source_component_summary")
    _require_string_list(result["caveats"], "caveats")

    preview = _require_non_empty_string(result["markdown_preview"], "markdown_preview")
    if "backend_grounding_summary" in preview:
        raise UserFacingAnalysisBriefError(
            "markdown_preview must not include backend_grounding_summary"
        )
    for section_id in (
        "current_judgment_boundary",
        "data_gaps_that_matter",
        "tracking_indicators",
        "cannot_conclude_yet",
    ):
        if section_id not in preview:
            raise UserFacingAnalysisBriefError(
                f"markdown_preview missing required section: {section_id}"
            )
    return result


def build_user_visible_sections(
    orchestration_result: Mapping[str, Any],
    locator_result: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Build all fixed user-visible sections."""

    return [
        build_subject_summary_section(orchestration_result),
        build_current_judgment_boundary_section(orchestration_result, locator_result),
        build_business_logic_section(orchestration_result),
        build_financial_interpretation_section(orchestration_result),
        build_industry_macro_context_section(orchestration_result),
        build_risk_points_section(orchestration_result),
        build_data_gaps_that_matter_section(orchestration_result),
        build_tracking_indicators_section(orchestration_result),
        build_cannot_conclude_yet_section(orchestration_result),
    ]


def build_subject_summary_section(
    orchestration_result: Mapping[str, Any],
) -> dict[str, Any]:
    """Build subject summary without company evaluation."""

    return _section(
        "subject_summary",
        "\u6807\u7684\u6458\u8981",
        LABEL_PENDING,
        ["not_assessable"],
        [
            _point(
                LABEL_PENDING,
                (
                    f"\u6807\u7684\uff1a{_identity_value(orchestration_result, 'stock_code') or '-'}"
                    f" / {_identity_value(orchestration_result, 'ts_code') or '-'}"
                    f" / {_identity_value(orchestration_result, 'company_name_hint') or '-'}"
                ),
            ),
            _point(
                LABEL_INFERENCE,
                "\u8fd9\u662f\u975e\u4ea4\u6613\u7528\u9014\u57fa\u672c\u9762\u5206\u6790\u8349\u7a3f\uff0c\u4ec5\u7ec4\u7ec7\u5f53\u524d\u5df2\u663e\u5f0f\u4f20\u5165\u7684\u540e\u53f0\u72b6\u6001\u3002",
            ),
            _point(
                LABEL_CANNOT_CONCLUDE,
                "\u672c\u8282\u4e0d\u5bf9\u516c\u53f8\u597d\u574f\u6216\u8d8b\u52bf\u505a\u7ed3\u8bba\u3002",
            ),
        ],
    )


def build_current_judgment_boundary_section(
    orchestration_result: Mapping[str, Any],
    locator_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Explain what can and cannot be judged now."""

    rollup = _rollup(orchestration_result)
    official_verified_count = _rollup_int(rollup, "official_verified_count")
    boundary_label = LABEL_RELIABLE if official_verified_count > 0 else LABEL_PENDING
    locator_available = _locator_available(locator_result)
    anchor_count = _rollup_int(rollup, "official_anchor_matched_count")
    artifact_count = _rollup_int(rollup, "official_artifact_cached_count")
    support_text = "\u5df2\u6709\u540e\u53f0\u516c\u544a\u951a\u70b9\u6216 artifact \u72b6\u6001"
    if locator_available:
        support_text += "\uff0c\u4e14\u540e\u53f0 locator \u53ef\u7528"
    support_text += "\uff1b\u8fd9\u4ecd\u53ea\u662f grounding \u652f\u6491\uff0c\u4e0d\u4f5c\u4e3a\u7528\u6237\u4e3b\u5185\u5bb9\u3002"
    if not anchor_count and not artifact_count and not locator_available:
        support_text = "\u5f53\u524d\u672a\u89c1\u53ef\u7528\u7684\u540e\u53f0\u516c\u544a\u951a\u70b9\u6216 artifact \u72b6\u6001\u3002"

    return _section(
        "current_judgment_boundary",
        "\u5f53\u524d\u5224\u65ad\u8fb9\u754c",
        boundary_label,
        _rollup_statuses(rollup, include_support=True),
        [
            _point(
                boundary_label,
                "\u5f53\u524d\u53ef\u5f62\u6210\u57fa\u672c\u9762\u5206\u6790\u8349\u7a3f\uff1b\u5b98\u65b9\u6307\u6807\u6838\u9a8c\u5c1a\u672a\u5b8c\u6210\u3002",
            ),
            _point(LABEL_PENDING, support_text),
            _point(
                LABEL_CANNOT_CONCLUDE,
                "\u73b0\u9636\u6bb5\u4e0d\u4ea7\u751f\u4ef7\u683c\u3001\u914d\u7f6e\u6216\u4ea4\u6613\u7528\u9014\u7ed3\u8bba\u3002",
            ),
        ],
    )


def build_business_logic_section(
    orchestration_result: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the business logic section from supplied business-profile status."""

    section = _vertical_section(orchestration_result, "company_business_profile")
    status_values = _status_values(section.get("evidence_status"))
    has_data_gap = "data_gap" in status_values
    points = [
        _point(
            LABEL_DATA_GAP if has_data_gap else _label_for_statuses(status_values),
            (
                "\u4e1a\u52a1\u6784\u6210\u3001\u4ea7\u54c1\u7ed3\u6784\u548c\u5ba2\u6237\u7ed3\u6784\u4ecd\u9700\u8865\u5145\uff1b"
                "\u5f53\u524d\u4e0d\u63a8\u65ad\u4e3b\u8425\u4e1a\u52a1\u6216\u7ade\u4e89\u5730\u4f4d\u3002"
            ),
        ),
        _point(
            LABEL_INFERENCE,
            "\u540e\u7eed\u9700\u7ed3\u5408\u4e3b\u8425\u6784\u6210\u3001\u4ea7\u54c1\u7ed3\u6784\u548c\u5ba2\u6237\u7ed3\u6784\u6765\u5224\u65ad\u4e1a\u52a1\u903b\u8f91\u3002",
        ),
    ]
    return _section(
        "business_logic",
        "\u516c\u53f8\u4e1a\u52a1\u903b\u8f91",
        LABEL_DATA_GAP if has_data_gap else _label_for_statuses(status_values),
        status_values or ["not_assessable"],
        points,
    )


def build_financial_interpretation_section(
    orchestration_result: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a financial interpretation starting point without numeric extraction."""

    section = _vertical_section(orchestration_result, "financial_candidate_summary")
    status_values = _status_values(section.get("evidence_status"))
    rollup = _rollup(orchestration_result)
    provider_present = bool(rollup.get("provider_candidate_present"))
    pending_count = _rollup_int(rollup, "pending_official_verification_count")
    text = "\u5df2\u6709 provider candidate \u8d22\u52a1\u4fe1\u606f\uff0c\u53ef\u4f5c\u4e3a\u8d8b\u52bf\u89c2\u5bdf\u8d77\u70b9\uff0c\u4f46\u4ecd\u5f85\u6838\u9a8c\u3002"
    if not provider_present:
        text = "\u6682\u672a\u770b\u5230 provider candidate \u8d22\u52a1\u4fe1\u606f\uff0c\u8d22\u52a1\u89e3\u8bfb\u5148\u8bb0\u4e3a\u6570\u636e\u7f3a\u53e3\u3002"
    return _section(
        "financial_interpretation",
        "\u8d22\u52a1\u89e3\u8bfb\u8d77\u70b9",
        LABEL_PENDING if provider_present else LABEL_DATA_GAP,
        status_values or ["data_gap"],
        [
            _point(LABEL_PENDING if provider_present else LABEL_DATA_GAP, text),
            _point(
                LABEL_PENDING,
                f"\u5f85\u6838\u9a8c\u9879\u6570\uff1a{pending_count}\uff1b\u672c\u5c42\u4e0d\u751f\u6210\u6307\u6807\u6570\u503c\u6216\u8d22\u52a1\u4f18\u52a3\u5224\u65ad\u3002",
            ),
        ],
    )


def build_industry_macro_context_section(
    orchestration_result: Mapping[str, Any],
) -> dict[str, Any]:
    """Build framework-only industry and macro context."""

    section = _vertical_section(orchestration_result, "industry_and_macro_context")
    status_values = _status_values(section.get("evidence_status"))
    points = [
        _point(
            LABEL_INFERENCE,
            "\u5f53\u524d\u4ec5\u4fdd\u7559\u884c\u4e1a\u4e0e\u5b8f\u89c2\u5206\u6790\u6846\u67b6\uff0c\u4e0d\u76f4\u63a5\u5199\u65b9\u5411\u6027\u6216\u786e\u5b9a\u4f20\u5bfc\u7ed3\u8bba\u3002",
        ),
        _point(
            LABEL_INFERENCE,
            "\u540e\u7eed\u5e94\u68c0\u67e5\u9700\u6c42\u6570\u636e\u3001\u8ba2\u5355\u53d8\u5316\u3001\u4ea7\u4e1a\u94fe\u4f20\u5bfc\u548c\u516c\u53f8\u53ef\u89c2\u6d4b\u4e1a\u52a1\u7684\u5173\u8054\u3002",
        ),
    ]
    return _section(
        "industry_macro_context",
        "\u884c\u4e1a\u4e0e\u5b8f\u89c2\u4f20\u5bfc\u6846\u67b6",
        LABEL_INFERENCE,
        status_values or ["framework_inference"],
        points,
    )


def build_risk_points_section(
    orchestration_result: Mapping[str, Any],
) -> dict[str, Any]:
    """Build analysis/data/checking risk prompts only."""

    rollup = _rollup(orchestration_result)
    data_gap_count = _rollup_int(rollup, "data_gap_count")
    pending_count = _rollup_int(rollup, "pending_official_verification_count")
    blocked_count = _rollup_int(rollup, "blocked_count")
    return _section(
        "risk_points",
        "\u98ce\u9669\u63d0\u793a\u8fb9\u754c",
        LABEL_DATA_GAP if data_gap_count else LABEL_PENDING,
        _rollup_statuses(rollup),
        [
            _point(
                LABEL_DATA_GAP,
                f"\u5206\u6790\u98ce\u9669\uff1a\u5c1a\u6709 {data_gap_count} \u4e2a\u6570\u636e\u7f3a\u53e3\u4f1a\u5f71\u54cd\u7b80\u62a5\u6df1\u5ea6\u3002",
            ),
            _point(
                LABEL_PENDING,
                f"\u6570\u636e\u98ce\u9669\uff1a\u5c1a\u6709 {pending_count} \u4e2a\u5019\u9009\u9879\u7b49\u5f85\u5b98\u65b9\u53e3\u5f84\u786e\u8ba4\u3002",
            ),
            _point(
                LABEL_CANNOT_CONCLUDE,
                f"\u6821\u5bf9\u98ce\u9669\uff1a\u5c1a\u6709 {blocked_count} \u4e2a\u6682\u4e0d\u80fd\u4e0b\u7ed3\u8bba\u7684\u8fb9\u754c\u3002",
            ),
        ],
    )


def build_data_gaps_that_matter_section(
    orchestration_result: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the user-relevant data gaps list."""

    rollup = _rollup(orchestration_result)
    data_gap_count = _rollup_int(rollup, "data_gap_count")
    gaps = [
        "\u4e1a\u52a1\u6784\u6210\u7f3a\u53e3\uff1a\u4e3b\u8425\u6784\u6210\u3001\u4ea7\u54c1\u7ed3\u6784\u3001\u5ba2\u6237\u7ed3\u6784\u5c1a\u672a\u8db3\u4ee5\u652f\u6491\u4e1a\u52a1\u5224\u65ad\u3002",
        "\u5b98\u65b9\u6570\u503c\u6821\u5bf9\u7f3a\u53e3\uff1a\u5019\u9009\u8d22\u52a1\u4fe1\u606f\u5c1a\u9700\u4e0e\u5b98\u65b9\u53e3\u5f84\u786e\u8ba4\u3002",
        "provider \u4e0e\u5b98\u65b9\u53e3\u5f84\u4e00\u81f4\u6027\u7f3a\u53e3\uff1a\u5c1a\u4e0d\u80fd\u76f4\u63a5\u7528\u5019\u9009\u72b6\u6001\u63a8\u51fa\u7ed3\u8bba\u3002",
        "\u884c\u4e1a\u4e0e\u5b8f\u89c2\u4f20\u5bfc\u7f3a\u53e3\uff1a\u9700\u8981\u660e\u786e\u884c\u4e1a\u53d8\u91cf\u5982\u4f55\u5f71\u54cd\u516c\u53f8\u53ef\u89c2\u6d4b\u4e1a\u52a1\u3002",
        "\u98ce\u9669\u5224\u65ad\u7f3a\u53e3\uff1a\u9700\u8865\u8db3\u73b0\u91d1\u6d41\u3001\u5e94\u6536\u8d26\u6b3e\u548c\u8ba2\u5355\u53d8\u5316\u7b49\u6570\u636e\u3002",
    ]
    return _section(
        "data_gaps_that_matter",
        "\u5173\u952e\u6570\u636e\u7f3a\u53e3",
        LABEL_DATA_GAP,
        ["data_gap"],
        [_point(LABEL_DATA_GAP, gap) for gap in gaps]
        + [
            _point(
                LABEL_DATA_GAP,
                f"\u540e\u53f0 rollup \u663e\u793a\u6570\u636e\u7f3a\u53e3\u8ba1\u6570\uff1a{data_gap_count}\uff1b\u524d\u53f0\u4ec5\u4fdd\u7559\u5bf9\u5206\u6790\u6709\u5b9e\u9645\u5f71\u54cd\u7684\u7c7b\u578b\u3002",
            )
        ],
    )


def build_tracking_indicators_section(
    orchestration_result: Mapping[str, Any],
) -> dict[str, Any]:
    """Build follow-up tracking names without trigger conditions."""

    _ = orchestration_result
    indicators = [
        "\u4e3b\u8425\u6784\u6210",
        "\u6bdb\u5229\u7387\u7ed3\u6784",
        "\u73b0\u91d1\u6d41 / \u5e94\u6536\u8d26\u6b3e",
        "\u884c\u4e1a\u8ba2\u5355 / \u62db\u6807",
        "\u5b98\u65b9\u62ab\u9732\u6821\u5bf9\u72b6\u6001",
    ]
    return _section(
        "tracking_indicators",
        "\u540e\u7eed\u8ddf\u8e2a\u6e05\u5355",
        LABEL_INFERENCE,
        ["framework_inference"],
        [
            _point(
                LABEL_INFERENCE,
                "\u8ddf\u8e2a\u6e05\u5355\u4ec5\u5217\u51fa\u540d\u79f0\uff0c\u4e0d\u7ed9\u4ef7\u683c\u3001\u914d\u7f6e\u6216\u4ea4\u6613\u89e6\u53d1\u6761\u4ef6\u3002",
            )
        ]
        + [_point(LABEL_INFERENCE, item) for item in indicators],
    )


def build_cannot_conclude_yet_section(
    orchestration_result: Mapping[str, Any],
) -> dict[str, Any]:
    """Build explicit non-conclusions as user value."""

    _ = orchestration_result
    cannot_conclude = [
        "\u4e0d\u80fd\u786e\u8ba4\u5b98\u65b9\u6307\u6807\u503c\u3002",
        "\u4e0d\u80fd\u786e\u8ba4 provider \u4e0e\u5b98\u65b9\u53e3\u5f84\u4e00\u81f4\u3002",
        "\u4e0d\u80fd\u751f\u6210\u6b63\u5f0f\u62a5\u544a\u3002",
        "\u4e0d\u80fd\u751f\u6210\u4ea4\u6613\u7528\u9014\u7ed3\u8bba\u3002",
        "\u4e0d\u80fd\u786e\u8ba4\u884c\u4e1a\u6216\u5b8f\u89c2\u56e0\u7d20\u5bf9\u516c\u53f8\u5f62\u6210\u786e\u5b9a\u6027\u4f20\u5bfc\u3002",
    ]
    return _section(
        "cannot_conclude_yet",
        "\u5f53\u524d\u4e0d\u80fd\u4e0b\u7684\u7ed3\u8bba",
        LABEL_CANNOT_CONCLUDE,
        ["blocked"],
        [_point(LABEL_CANNOT_CONCLUDE, item) for item in cannot_conclude],
    )


def build_backend_grounding_summary(
    orchestration_result: Mapping[str, Any],
    locator_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize backend availability without raw trace fields."""

    rollup = _rollup(orchestration_result)
    summary = {
        "schema_version": BACKEND_GROUNDING_SUMMARY_SCHEMA_VERSION,
        "default_visible": False,
        "audit_trace_available": bool(locator_result),
        "official_anchor_available": _rollup_int(rollup, "official_anchor_matched_count")
        > 0,
        "artifact_cached_available": _rollup_int(
            rollup,
            "official_artifact_cached_count",
        )
        > 0,
        "locator_available": _locator_available(locator_result),
        "provider_candidate_present": bool(rollup.get("provider_candidate_present")),
        "pending_verification_count": _rollup_int(
            rollup,
            "pending_official_verification_count",
        ),
        "official_verified_count": _rollup_int(rollup, "official_verified_count"),
        "data_gap_count": _rollup_int(rollup, "data_gap_count"),
        "source_component_schema_versions": _source_component_schema_versions(
            orchestration_result,
            locator_result,
        ),
        "grounding_notes": [
            "Backend availability only; raw locator details are withheld.",
            "Counts and status availability do not upgrade candidate states.",
        ],
        "not_for_trading_advice": True,
    }
    _validate_backend_grounding_summary(summary)
    return summary


def build_user_facing_analysis_markdown_preview(brief: Mapping[str, Any]) -> str:
    """Build markdown preview from user-visible sections only."""

    source = _require_mapping(brief, "brief")
    sections = _require_list(source.get("user_visible_sections"), "user_visible_sections")
    lines = [
        "# \u975e\u4ea4\u6613\u7528\u9014\u57fa\u672c\u9762\u5206\u6790\u8349\u7a3f",
        "",
        f"- stock_code: {source.get('stock_code')}",
        f"- ts_code: {source.get('ts_code')}",
        f"- company_name_hint: {source.get('company_name_hint')}",
        "",
        "## \u4f7f\u7528\u6807\u7b7e",
    ]
    labels_used = _labels_used(sections)
    for label in labels_used:
        lines.append(f"- {label}")

    for section in sections:
        section_id = section["section_id"]
        lines.extend(["", f"## {section_id} - {section['section_title']}"])
        for point in section["analysis_points"]:
            lines.append(f"- [{point['label']}] {point['text']}")

    preview = "\n".join(lines).strip() + "\n"
    assert_no_user_facing_analysis_brief_forbidden_markers(preview)
    return preview


def assert_no_user_facing_analysis_brief_forbidden_markers(value: Any) -> None:
    """Reject forbidden markers in nested user-facing brief values."""

    finding = _find_forbidden_marker(value)
    if finding:
        raise UserFacingAnalysisBriefError(
            f"user-facing analysis brief safety violation: forbidden marker: {finding}"
        )


def _validate_input_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    source = _require_mapping(payload, "payload")
    unsupported = sorted(set(source) - _PAYLOAD_KEYS)
    if unsupported:
        raise UserFacingAnalysisBriefError(
            f"payload contains unsupported keys: {unsupported}"
        )
    if "orchestration_result" not in source:
        raise UserFacingAnalysisBriefError("payload requires orchestration_result")
    allow_network = source.get("allow_network", False)
    if allow_network is True:
        raise UserFacingAnalysisBriefError("allow_network=true is not allowed")
    if not isinstance(allow_network, bool):
        raise UserFacingAnalysisBriefError("allow_network must be bool")
    if source.get("not_for_trading_advice", True) is not True:
        raise UserFacingAnalysisBriefError("not_for_trading_advice must be true")
    analysis_mode = source.get("analysis_mode", "draft")
    if analysis_mode not in {"draft", "compact"}:
        raise UserFacingAnalysisBriefError("analysis_mode must be draft or compact")
    _reject_raw_payload_inputs(source)
    copied = deepcopy(dict(source))
    copied["analysis_mode"] = analysis_mode
    copied["allow_network"] = False
    copied["not_for_trading_advice"] = True
    return copied


def _reject_raw_payload_inputs(value: Any, path: str = "payload") -> None:
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise UserFacingAnalysisBriefError(f"{path} contains raw bytes")
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text == "locator_result":
                _reject_bytes(child, f"{path}.{key_text}")
                continue
            if key_text in _RAW_INPUT_KEYS:
                raise UserFacingAnalysisBriefError(
                    f"{path} contains raw input key: {key_text}"
                )
            _reject_raw_payload_inputs(child, f"{path}.{key_text}")
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            _reject_raw_payload_inputs(child, f"{path}[{index}]")


def _reject_bytes(value: Any, path: str) -> None:
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise UserFacingAnalysisBriefError(f"{path} contains raw bytes")
    if isinstance(value, Mapping):
        for key, child in value.items():
            _reject_bytes(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_bytes(child, f"{path}[{index}]")


def _analysis_labels_legend() -> list[dict[str, Any]]:
    return [
        _legend(LABEL_RELIABLE, "\u4ec5\u5f53 official_verified_count > 0 \u65f6\u4f7f\u7528\u3002"),
        _legend(LABEL_PENDING, "\u5019\u9009\u3001\u951a\u70b9\u6216 artifact \u72b6\u6001\u5c1a\u9700\u786e\u8ba4\u3002"),
        _legend(LABEL_DATA_GAP, "\u7f3a\u5c11\u8db3\u4ee5\u652f\u6491\u5206\u6790\u7684\u6570\u636e\u3002"),
        _legend(LABEL_INFERENCE, "\u4ec5\u4fdd\u7559\u6846\u67b6\u3001\u95ee\u9898\u6216\u540e\u7eed\u5206\u6790\u65b9\u5411\u3002"),
        _legend(LABEL_CANNOT_CONCLUDE, "\u5f53\u524d\u4e0d\u80fd\u4e0b\u7684\u7ed3\u8bba\u8fb9\u754c\u3002"),
    ]


def _legend(label: str, meaning: str) -> dict[str, Any]:
    return {
        "schema_version": ANALYSIS_CONFIDENCE_LABEL_SCHEMA_VERSION,
        "label": label,
        "meaning": meaning,
    }


def _section(
    section_id: str,
    title: str,
    label: str,
    evidence_statuses: Iterable[str],
    points: list[dict[str, str]],
) -> dict[str, Any]:
    section = {
        "schema_version": USER_FACING_ANALYSIS_BRIEF_SECTION_SCHEMA_VERSION,
        "section_id": section_id,
        "section_title": title,
        "analysis_label": label,
        "evidence_statuses": _dedupe_preserve_order(
            status for status in evidence_statuses if isinstance(status, str) and status
        ),
        "analysis_points": points,
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }
    _validate_section(section, "section")
    return section


def _point(label: str, text: str) -> dict[str, str]:
    if label not in ANALYSIS_LABELS:
        raise UserFacingAnalysisBriefError("invalid analysis label")
    return {"label": label, "text": text}


def _build_source_component_summary(
    orchestration_result: Mapping[str, Any],
    locator_result: Mapping[str, Any] | None,
) -> dict[str, Any]:
    source_summary = orchestration_result.get("source_component_summary")
    component_keys = []
    if isinstance(source_summary, Mapping):
        component_keys = _string_values(source_summary.get("component_keys_present"))
    return {
        "orchestration_schema_version": orchestration_result.get("schema_version"),
        "vertical_slice_schema_version": (
            _vertical_slice(orchestration_result).get("schema_version")
        ),
        "locator_schema_version": locator_result.get("schema_version")
        if isinstance(locator_result, Mapping)
        else None,
        "component_keys_present": component_keys,
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }


def _brief_caveats(orchestration_result: Mapping[str, Any]) -> list[str]:
    caveats = [
        "Brief is assembled from explicit upstream result objects only.",
        "Backend evidence details stay out of user-visible sections by default.",
    ]
    caveats.extend(_string_values(orchestration_result.get("caveats")))
    return _dedupe_preserve_order(caveats)


def _source_component_schema_versions(
    orchestration_result: Mapping[str, Any],
    locator_result: Mapping[str, Any] | None,
) -> dict[str, Any]:
    versions = {
        "orchestration_result": orchestration_result.get("schema_version"),
        "vertical_slice": _vertical_slice(orchestration_result).get("schema_version"),
    }
    summary = orchestration_result.get("source_component_summary")
    if isinstance(summary, Mapping):
        component_versions = summary.get("component_schema_versions")
        if isinstance(component_versions, Mapping):
            versions["components"] = deepcopy(dict(component_versions))
    if isinstance(locator_result, Mapping):
        versions["locator_result"] = locator_result.get("schema_version")
    return versions


def _validate_analysis_labels_legend(value: Any) -> list[dict[str, Any]]:
    legends = _require_list(value, "analysis_labels_legend")
    labels = []
    result = []
    for index, item in enumerate(legends):
        legend = _require_mapping(item, f"analysis_labels_legend[{index}]")
        _require_fields(
            legend,
            ("schema_version", "label", "meaning"),
            f"analysis_labels_legend[{index}]",
        )
        if legend["schema_version"] != ANALYSIS_CONFIDENCE_LABEL_SCHEMA_VERSION:
            raise UserFacingAnalysisBriefError("invalid label schema_version")
        label = _require_non_empty_string(legend["label"], "label")
        if label not in ANALYSIS_LABELS:
            raise UserFacingAnalysisBriefError("unsupported analysis label")
        _require_non_empty_string(legend["meaning"], "meaning")
        labels.append(label)
        result.append(deepcopy(dict(legend)))
    if tuple(labels) != ANALYSIS_LABELS:
        raise UserFacingAnalysisBriefError("analysis_labels_legend has wrong order")
    return result


def _validate_user_visible_sections(
    value: Any,
    backend_grounding_summary: Any,
) -> list[dict[str, Any]]:
    sections = _require_list(value, "user_visible_sections")
    result = [_validate_section(section, f"user_visible_sections[{index}]") for index, section in enumerate(sections)]
    section_ids = [section["section_id"] for section in result]
    if tuple(section_ids) != USER_VISIBLE_SECTION_IDS:
        raise UserFacingAnalysisBriefError("user_visible_sections have wrong order")
    if isinstance(backend_grounding_summary, Mapping):
        official_verified_count = backend_grounding_summary.get(
            "official_verified_count",
            0,
        )
        if official_verified_count == 0:
            used = {
                point["label"]
                for section in result
                for point in section["analysis_points"]
            } | {section["analysis_label"] for section in result}
            if LABEL_RELIABLE in used:
                raise UserFacingAnalysisBriefError(
                    "reliable label requires official_verified_count > 0"
                )
    return result


def _validate_section(value: Any, path: str) -> dict[str, Any]:
    section = _require_mapping(value, path)
    _require_fields(
        section,
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
        path,
    )
    result = deepcopy(dict(section))
    if result["schema_version"] != USER_FACING_ANALYSIS_BRIEF_SECTION_SCHEMA_VERSION:
        raise UserFacingAnalysisBriefError(f"{path}.schema_version invalid")
    _require_non_empty_string(result["section_id"], f"{path}.section_id")
    _require_non_empty_string(result["section_title"], f"{path}.section_title")
    if result["analysis_label"] not in ANALYSIS_LABELS:
        raise UserFacingAnalysisBriefError(f"{path}.analysis_label invalid")
    _require_string_list(result["evidence_statuses"], f"{path}.evidence_statuses")
    points = _require_list(result["analysis_points"], f"{path}.analysis_points")
    if not points:
        raise UserFacingAnalysisBriefError(f"{path}.analysis_points cannot be empty")
    for index, point in enumerate(points):
        item = _require_mapping(point, f"{path}.analysis_points[{index}]")
        _require_fields(item, ("label", "text"), f"{path}.analysis_points[{index}]")
        if item["label"] not in ANALYSIS_LABELS:
            raise UserFacingAnalysisBriefError("point label invalid")
        _require_non_empty_string(item["text"], "point.text")
    _require_true(result["not_official_verified"], f"{path}.not_official_verified")
    _require_true(result["not_for_trading_advice"], f"{path}.not_for_trading_advice")
    _assert_no_forbidden_user_visible_keys(result)
    return result


def _validate_backend_grounding_summary(value: Any) -> dict[str, Any]:
    summary = _require_mapping(value, "backend_grounding_summary")
    unknown = sorted(set(summary) - _BACKEND_GROUNDING_KEYS)
    if unknown:
        raise UserFacingAnalysisBriefError(
            f"backend_grounding_summary contains unsupported keys: {unknown}"
        )
    _require_fields(
        summary,
        tuple(sorted(_BACKEND_GROUNDING_KEYS)),
        "backend_grounding_summary",
    )
    result = deepcopy(dict(summary))
    if result["schema_version"] != BACKEND_GROUNDING_SUMMARY_SCHEMA_VERSION:
        raise UserFacingAnalysisBriefError("invalid backend_grounding_summary version")
    _require_false(result["default_visible"], "backend_grounding_summary.default_visible")
    for key in (
        "audit_trace_available",
        "official_anchor_available",
        "artifact_cached_available",
        "locator_available",
        "provider_candidate_present",
    ):
        _require_bool(result[key], f"backend_grounding_summary.{key}")
    for key in (
        "pending_verification_count",
        "official_verified_count",
        "data_gap_count",
    ):
        _require_non_negative_int(result[key], f"backend_grounding_summary.{key}")
    _require_mapping(
        result["source_component_schema_versions"],
        "backend_grounding_summary.source_component_schema_versions",
    )
    _require_string_list(
        result["grounding_notes"],
        "backend_grounding_summary.grounding_notes",
    )
    _require_true(
        result["not_for_trading_advice"],
        "backend_grounding_summary.not_for_trading_advice",
    )
    _assert_no_forbidden_user_visible_keys(result)
    return result


def _assert_no_forbidden_user_visible_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in _FORBIDDEN_USER_VISIBLE_KEYS:
                raise UserFacingAnalysisBriefError(
                    f"user-visible output contains forbidden key: {key}"
                )
            _assert_no_forbidden_user_visible_keys(child)
        return
    if isinstance(value, list):
        for item in value:
            _assert_no_forbidden_user_visible_keys(item)


def _labels_used(sections: Iterable[Mapping[str, Any]]) -> list[str]:
    labels = []
    for section in sections:
        labels.append(section.get("analysis_label"))
        for point in section.get("analysis_points", []):
            if isinstance(point, Mapping):
                labels.append(point.get("label"))
    return [label for label in ANALYSIS_LABELS if label in labels]


def _rollup(orchestration_result: Mapping[str, Any]) -> Mapping[str, Any]:
    rollup = orchestration_result.get("evidence_status_rollup")
    if isinstance(rollup, Mapping):
        return rollup
    vertical_rollup = _vertical_slice(orchestration_result).get("evidence_status_rollup")
    return vertical_rollup if isinstance(vertical_rollup, Mapping) else {}


def _vertical_slice(orchestration_result: Mapping[str, Any]) -> Mapping[str, Any]:
    vertical_slice = orchestration_result.get("vertical_slice")
    return vertical_slice if isinstance(vertical_slice, Mapping) else {}


def _vertical_section(orchestration_result: Mapping[str, Any], section_id: str) -> Mapping[str, Any]:
    for section in _vertical_slice(orchestration_result).get("sections", []):
        if isinstance(section, Mapping) and section.get("section_id") == section_id:
            return section
    return {}


def _identity_value(orchestration_result: Mapping[str, Any], key: str) -> Any:
    if orchestration_result.get(key) not in (None, ""):
        return orchestration_result.get(key)
    vertical_slice = _vertical_slice(orchestration_result)
    return vertical_slice.get(key)


def _rollup_int(rollup: Mapping[str, Any], key: str) -> int:
    value = rollup.get(key)
    return value if isinstance(value, int) and value >= 0 else 0


def _rollup_statuses(
    rollup: Mapping[str, Any],
    *,
    include_support: bool = False,
) -> list[str]:
    statuses = []
    if rollup.get("provider_candidate_present"):
        statuses.append("provider_candidate")
    if _rollup_int(rollup, "pending_official_verification_count"):
        statuses.append("pending_official_verification")
    if include_support and _rollup_int(rollup, "official_anchor_matched_count"):
        statuses.append("official_anchor_matched")
    if include_support and _rollup_int(rollup, "official_artifact_cached_count"):
        statuses.append("artifact_cached")
    if _rollup_int(rollup, "data_gap_count"):
        statuses.append("data_gap")
    if _rollup_int(rollup, "blocked_count"):
        statuses.append("blocked")
    return statuses or ["not_assessable"]


def _status_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [str(item) for item in value if isinstance(item, str) and item]
    return []


def _label_for_statuses(statuses: Iterable[str]) -> str:
    status_set = set(statuses)
    if "blocked" in status_set or "not_assessable" in status_set:
        return LABEL_CANNOT_CONCLUDE
    if "data_gap" in status_set:
        return LABEL_DATA_GAP
    if "framework_inference" in status_set or "local_experiment" in status_set:
        return LABEL_INFERENCE
    if status_set & {
        "provider_candidate",
        "pending_official_verification",
        "official_anchor_matched",
        "artifact_cached",
    }:
        return LABEL_PENDING
    return LABEL_INFERENCE


def _locator_available(locator_result: Mapping[str, Any] | None) -> bool:
    if not isinstance(locator_result, Mapping):
        return False
    return bool(locator_result.get("locator_items") or locator_result.get("skipped_items"))


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
        raise UserFacingAnalysisBriefError(f"{field} must be a mapping")
    return value


def _require_fields(value: Mapping[str, Any], fields: tuple[str, ...], path: str) -> None:
    missing = [field for field in fields if field not in value]
    if missing:
        raise UserFacingAnalysisBriefError(f"{path} missing required fields: {missing}")


def _require_optional_string(value: Any, path: str) -> None:
    if value is not None and not isinstance(value, str):
        raise UserFacingAnalysisBriefError(f"{path} must be string or null")


def _require_non_empty_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise UserFacingAnalysisBriefError(f"{path} must be a non-empty string")
    return value


def _require_string_list(value: Any, path: str) -> list[str]:
    if not isinstance(value, list):
        raise UserFacingAnalysisBriefError(f"{path} must be a list")
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise UserFacingAnalysisBriefError(f"{path}[{index}] must be a string")
    return value


def _require_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise UserFacingAnalysisBriefError(f"{path} must be a list")
    return value


def _require_true(value: Any, path: str) -> None:
    if value is not True:
        raise UserFacingAnalysisBriefError(f"{path} must be true")


def _require_false(value: Any, path: str) -> None:
    if value is not False:
        raise UserFacingAnalysisBriefError(f"{path} must be false")


def _require_bool(value: Any, path: str) -> None:
    if not isinstance(value, bool):
        raise UserFacingAnalysisBriefError(f"{path} must be bool")


def _require_non_negative_int(value: Any, path: str) -> int:
    if not isinstance(value, int) or value < 0:
        raise UserFacingAnalysisBriefError(f"{path} must be a non-negative int")
    return value


__all__ = [
    "ANALYSIS_CONFIDENCE_LABEL_SCHEMA_VERSION",
    "ANALYSIS_LABELS",
    "BACKEND_GROUNDING_SUMMARY_SCHEMA_VERSION",
    "BRIEF_TYPE_USER_FACING_ANALYSIS_DRAFT",
    "USER_FACING_ANALYSIS_BRIEF_SCHEMA_VERSION",
    "USER_FACING_ANALYSIS_BRIEF_SECTION_SCHEMA_VERSION",
    "USER_VISIBLE_SECTION_IDS",
    "UserFacingAnalysisBriefError",
    "assert_no_user_facing_analysis_brief_forbidden_markers",
    "build_backend_grounding_summary",
    "build_business_logic_section",
    "build_cannot_conclude_yet_section",
    "build_current_judgment_boundary_section",
    "build_data_gaps_that_matter_section",
    "build_financial_interpretation_section",
    "build_industry_macro_context_section",
    "build_risk_points_section",
    "build_subject_summary_section",
    "build_tracking_indicators_section",
    "build_user_facing_analysis_brief",
    "build_user_facing_analysis_markdown_preview",
    "build_user_visible_sections",
    "validate_user_facing_analysis_brief",
]
