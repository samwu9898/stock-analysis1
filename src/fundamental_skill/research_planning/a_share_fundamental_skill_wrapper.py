# -*- coding: utf-8 -*-
"""Callable A-share fundamental skill wrapper thin slice.

This module is a small callable entry point around the existing Analysis Brief
and controlled professional brief chains. Legacy analysis_brief and
orchestration_result modes remain in-memory and do not fetch live data.
ticker_only_professional_brief may call the controlled Tushare professional
brief pilot only through the narrow env_live + allow_network=true path. The
wrapper never writes artifacts, never reads local credential files, never builds
Report V1 or HTML outputs, and never provides trading advice.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
import json
import re
from typing import Any

from .analysis_brief_report_v1_adapter import (
    build_analysis_brief_report_v1_compatibility_payload,
    validate_analysis_brief_report_v1_compatibility_payload,
)
from .user_facing_analysis_brief import (
    ANALYSIS_LABELS,
    USER_VISIBLE_SECTION_IDS,
    build_user_facing_analysis_brief,
    validate_user_facing_analysis_brief,
)


A_SHARE_FUNDAMENTAL_SKILL_REQUEST_SCHEMA_VERSION = (
    "a_share_fundamental_skill_request.v1"
)
A_SHARE_FUNDAMENTAL_SKILL_RESPONSE_SCHEMA_VERSION = (
    "a_share_fundamental_skill_response.v1"
)
A_SHARE_FUNDAMENTAL_SKILL_READINESS_SCHEMA_VERSION = (
    "a_share_fundamental_skill_readiness.v1"
)
A_SHARE_FUNDAMENTAL_COMPACT_RESPONSE_SCHEMA_VERSION = (
    "a_share_fundamental_compact_response.v1"
)

INPUT_MODE_ANALYSIS_BRIEF = "analysis_brief"
INPUT_MODE_ORCHESTRATION_RESULT = "orchestration_result"
INPUT_MODE_TICKER_ONLY_PROFESSIONAL_BRIEF = "ticker_only_professional_brief"
SUPPORTED_INPUT_MODES = (
    INPUT_MODE_ANALYSIS_BRIEF,
    INPUT_MODE_ORCHESTRATION_RESULT,
    INPUT_MODE_TICKER_ONLY_PROFESSIONAL_BRIEF,
)
UNSUPPORTED_INPUT_MODES = (
    "ticker_only_live",
    "full_autonomous",
    "live_provider",
    "report_v1_generation",
    "html_generation",
)

OUTPUT_MODE_COMPACT_BRIEF = "compact_brief"
OUTPUT_MODE_COMPACT_BRIEF_AND_REPORT_V1_COMPATIBILITY_PAYLOAD = (
    "compact_brief_and_report_v1_compatibility_payload"
)
OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF = "professional_compact_brief"
OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF_AND_INTERNAL_PAYLOAD = (
    "professional_compact_brief_and_internal_payload"
)
SUPPORTED_OUTPUT_MODES = (
    OUTPUT_MODE_COMPACT_BRIEF,
    OUTPUT_MODE_COMPACT_BRIEF_AND_REPORT_V1_COMPATIBILITY_PAYLOAD,
    OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF,
    OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF_AND_INTERNAL_PAYLOAD,
)
UNSUPPORTED_OUTPUT_MODES = (
    "report_v1_artifact",
    "html_artifact",
    "live_full_report",
    "trading_signal",
)

SKILL_READINESS_READY = "ready"
SKILL_READINESS_BLOCKED = "blocked"
SKILL_READINESS_SKIPPED = "skipped"

TUSHARE_CLIENT_MODE_FAKE = "fake"
TUSHARE_CLIENT_MODE_INJECTED = "injected"
TUSHARE_CLIENT_MODE_ENV_LIVE = "env_live"
SUPPORTED_TUSHARE_CLIENT_MODES = (
    TUSHARE_CLIENT_MODE_FAKE,
    TUSHARE_CLIENT_MODE_INJECTED,
    TUSHARE_CLIENT_MODE_ENV_LIVE,
)

RENDERER_MODE_DETERMINISTIC = "deterministic"
RENDERER_MODE_FAKE_LLM = "fake_llm"
SUPPORTED_RENDERER_MODES = (
    RENDERER_MODE_DETERMINISTIC,
    RENDERER_MODE_FAKE_LLM,
)

PROFESSIONAL_ANALYST_COMPACT_BRIEF_SCHEMA_VERSION = (
    "professional_analyst_compact_brief.v1"
)
PROFESSIONAL_ANALYST_COMPACT_BRIEF_SECTION_SCHEMA_VERSION = (
    "professional_analyst_compact_brief_section.v1"
)
PROFESSIONAL_BRIEF_SECTION_KEYS = (
    "overall_view",
    "business_view",
    "financial_view",
    "operating_quality_view",
    "industry_macro_view",
    "risk_view",
    "key_variables",
    "conclusion_boundary",
    "source_note",
)

BLOCKED_REASON_VALIDATED_ANALYSIS_INPUT_REQUIRED = (
    "validated_analysis_input_required"
)
BLOCKED_MESSAGE_VALIDATED_ANALYSIS_INPUT_REQUIRED = (
    "current wrapper requires validated analysis inputs; "
    "live ticker orchestration is later stage"
)

_REQUEST_FIELDS = {
    "schema_version",
    "stock_code",
    "ts_code",
    "company_name_hint",
    "periods",
    "input_mode",
    "output_mode",
    "tushare_client_mode",
    "renderer_mode",
    "user_facing_analysis_brief",
    "orchestration_result",
    "locator_result",
    "allow_network",
    "allow_file_writes",
    "not_for_trading_advice",
}

_REQUEST_SUMMARY_FIELDS = {
    "schema_version",
    "stock_code",
    "ts_code",
    "company_name_hint",
    "periods",
    "input_mode",
    "output_mode",
    "tushare_client_mode",
    "renderer_mode",
    "allow_network",
    "allow_file_writes",
    "has_user_facing_analysis_brief",
    "has_orchestration_result",
    "has_locator_result",
    "not_for_trading_advice",
}

_RESPONSE_FIELDS = {
    "schema_version",
    "readiness",
    "request_summary",
    "compact_response",
    "user_facing_analysis_brief",
    "report_v1_compatibility_payload",
    "professional_compact_brief",
    "professional_internal_payload",
    "blocked_reasons",
    "caveats",
    "not_official_verified",
    "not_for_trading_advice",
}

_READINESS_FIELDS = {
    "schema_version",
    "status",
    "input_mode",
    "output_mode",
    "renderer_mode",
    "required_inputs_present",
    "missing_required_inputs",
    "validation_errors",
    "has_compact_response",
    "has_user_facing_analysis_brief",
    "has_report_v1_compatibility_payload",
    "has_professional_compact_brief",
    "has_professional_internal_payload",
    "has_report_v1_artifact",
    "has_html_artifact",
    "has_trading_advice",
    "not_for_trading_advice",
}

_COMPACT_RESPONSE_FIELDS = {
    "schema_version",
    "stock_code",
    "ts_code",
    "company_name_hint",
    "title",
    "summary_points",
    "section_summaries",
    "labels_used",
    "cannot_conclude_yet",
    "tracking_indicators",
    "markdown_preview",
    "not_for_trading_advice",
}

_COMPACT_SECTION_SUMMARY_FIELDS = {
    "section_id",
    "section_title",
    "analysis_label",
    "summary_points",
}

_PROFESSIONAL_BRIEF_FIELDS = {
    "schema_version",
    "stock_code",
    "ts_code",
    "company_name_hint",
    "title",
    *PROFESSIONAL_BRIEF_SECTION_KEYS,
    "not_for_trading_advice",
}

_PROFESSIONAL_SECTION_FIELDS = {
    "schema_version",
    "section_id",
    "title",
    "view",
    "not_for_trading_advice",
}

_PROFESSIONAL_INTERNAL_PAYLOAD_FIELDS = {
    "schema_version",
    "provider_candidate_count",
    "internal_analysis_brief_schema_version",
    "wrapper_response_schema_version",
    "wrapper_readiness_status",
    "renderer_mode",
    "not_official_verified",
    "not_for_trading_advice",
}

_RAW_INPUT_KEYS = {
    "arbitrary_url",
    "cache_file_bytes",
    "cache_file_content",
    "cache_path",
    "download_url",
    "final_url",
    "fixture_path",
    "html_artifact_path",
    "http_response",
    "output_artifact_path",
    "pdf_bytes",
    "pdf_url",
    "provider_queue",
    "raw_http_response",
    "raw_pdf_bytes",
    "raw_provider_queue",
    "raw_tushare_provider_result",
    "report_v1_artifact_path",
    "source_url",
    "tushare_provider_result",
    "url",
}

_COMPACT_FORBIDDEN_OUTPUT_MARKERS = (
    "backend_grounding_summary",
    "page_number",
    "snippet",
    "source_url",
    "sha256",
    "cache_path",
    "provider queue",
    "anchor map",
    "locator hits",
    "official metadata",
    "Report V1 artifact path",
    "HTML artifact path",
)

_PROFESSIONAL_FRONTSTAGE_FORBIDDEN_MARKERS = (
    "provider_candidate",
    "provider candidate",
    "pending_official_verification",
    "pending verification",
    "official verification",
    "official_verified_count",
    "data gap",
    "evidence locator",
    "anchor map",
    "artifact cached",
    "reconciliation",
    "provider vs official",
    "provider",
    "page_number",
    "snippet",
    "source_url",
    "sha256",
    "cache_path",
    "\u5f85\u6838\u9a8c",
    "\u6570\u636e\u7f3a\u53e3",
    "\u63a8\u7406",
    "\u5b98\u65b9\u6838\u9a8c",
    "\u5c1a\u672a\u5b8c\u6210\u5b98\u65b9\u6838\u9a8c",
    "\u5019\u9009\u6570\u636e",
    "\u8bc1\u636e\u72b6\u6001",
    "\u53e3\u5f84\u4e00\u81f4\u6027",
    "\u7528\u6237\u81ea\u884c",
    "\u81ea\u884c\u5224\u65ad",
    "\u81ea\u884c\u8ddf\u8e2a",
    "\u9700\u8981\u7528\u6237",
    "\u5efa\u8bae\u7528\u6237",
    "\u8bf7\u7ed3\u5408",
)

_ALLOWED_EXACT_TEXTS = {
    "has_html_artifact",
    "has_report_v1_artifact",
    "has_trading_advice",
    "not_for_trading_advice",
    "not_official_verified",
    "official_verified_count",
    "\u5b98\u65b9\u6307\u6807\u6838\u9a8c\u5c1a\u672a\u5b8c\u6210",
    "\u8fd9\u4e0d\u662f\u6b63\u5f0f\u7814\u62a5 / \u4e0d\u662f\u6295\u8d44\u5efa\u8bae",
    "\u8fd9\u4e0d\u662f\u6b63\u5f0f\u7814\u62a5/\u4e0d\u662f\u6295\u8d44\u5efa\u8bae",
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
    "verified_fact",
    "live Tushare",
    "live provider",
    "live CNInfo",
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
_TOKEN_LIKE_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._-]{8,}\b", re.IGNORECASE),
)


class AShareFundamentalSkillWrapperError(ValueError):
    """Raised when the callable wrapper fails closed."""


def build_a_share_fundamental_skill_response(
    request: Mapping[str, Any],
    *,
    tushare_client: Any | None = None,
) -> dict[str, Any]:
    """Build the compact skill response from explicit validated inputs."""

    validated_request = validate_a_share_fundamental_skill_request(request)
    if validated_request["input_mode"] == INPUT_MODE_TICKER_ONLY_PROFESSIONAL_BRIEF:
        return _build_ticker_only_professional_brief_response(
            validated_request,
            tushare_client=tushare_client,
        )

    missing_inputs = _missing_required_inputs(validated_request)
    if missing_inputs:
        blocked_reasons = [_validated_analysis_input_required_reason()]
        response = {
            "schema_version": A_SHARE_FUNDAMENTAL_SKILL_RESPONSE_SCHEMA_VERSION,
            "readiness": build_skill_readiness(
                validated_request,
                blocked_reasons=blocked_reasons,
            ),
            "request_summary": build_request_summary(validated_request),
            "compact_response": None,
            "user_facing_analysis_brief": None,
            "report_v1_compatibility_payload": None,
            "professional_compact_brief": None,
            "professional_internal_payload": None,
            "blocked_reasons": blocked_reasons,
            "caveats": _response_caveats(),
            "not_official_verified": True,
            "not_for_trading_advice": True,
        }
        return validate_a_share_fundamental_skill_response(response)

    brief = _build_or_validate_brief(validated_request)
    compact_response = build_compact_response_from_analysis_brief(brief)
    compatibility_payload = None
    if (
        validated_request["output_mode"]
        == OUTPUT_MODE_COMPACT_BRIEF_AND_REPORT_V1_COMPATIBILITY_PAYLOAD
    ):
        compatibility_payload = build_analysis_brief_report_v1_compatibility_payload(
            brief
        )

    response = {
        "schema_version": A_SHARE_FUNDAMENTAL_SKILL_RESPONSE_SCHEMA_VERSION,
        "readiness": build_skill_readiness(
            validated_request,
            brief=brief,
            compatibility_payload=compatibility_payload,
        ),
        "request_summary": build_request_summary(validated_request),
        "compact_response": compact_response,
        "user_facing_analysis_brief": brief,
        "report_v1_compatibility_payload": compatibility_payload,
        "professional_compact_brief": None,
        "professional_internal_payload": None,
        "blocked_reasons": [],
        "caveats": _response_caveats(),
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }
    return validate_a_share_fundamental_skill_response(response)


def validate_a_share_fundamental_skill_request(
    request: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the callable wrapper request and return a defensive copy."""

    source = _require_mapping(request, "request")
    _reject_raw_inputs(source, "request")
    unsupported = sorted(set(source) - _REQUEST_FIELDS)
    if unsupported:
        raise AShareFundamentalSkillWrapperError(
            f"request contains unsupported keys: {unsupported}"
        )
    if source.get("schema_version") != A_SHARE_FUNDAMENTAL_SKILL_REQUEST_SCHEMA_VERSION:
        raise AShareFundamentalSkillWrapperError(
            "schema_version must be "
            f"{A_SHARE_FUNDAMENTAL_SKILL_REQUEST_SCHEMA_VERSION}"
        )

    input_mode = source.get("input_mode", INPUT_MODE_ANALYSIS_BRIEF)
    if input_mode not in SUPPORTED_INPUT_MODES:
        raise AShareFundamentalSkillWrapperError(
            f"unsupported input_mode: {input_mode}"
        )

    output_mode = source.get(
        "output_mode",
        (
            OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF
            if input_mode == INPUT_MODE_TICKER_ONLY_PROFESSIONAL_BRIEF
            else OUTPUT_MODE_COMPACT_BRIEF
        ),
    )
    if output_mode not in SUPPORTED_OUTPUT_MODES:
        raise AShareFundamentalSkillWrapperError(
            f"unsupported output_mode: {output_mode}"
        )
    if input_mode == INPUT_MODE_TICKER_ONLY_PROFESSIONAL_BRIEF:
        if output_mode not in {
            OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF,
            OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF_AND_INTERNAL_PAYLOAD,
        }:
            raise AShareFundamentalSkillWrapperError(
                "ticker-only professional brief requires professional output_mode"
            )
    elif output_mode in {
        OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF,
        OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF_AND_INTERNAL_PAYLOAD,
    }:
        raise AShareFundamentalSkillWrapperError(
            "professional output_mode requires ticker-only professional brief input_mode"
        )

    tushare_client_mode = source.get("tushare_client_mode")
    if tushare_client_mode is not None:
        if tushare_client_mode not in SUPPORTED_TUSHARE_CLIENT_MODES:
            raise AShareFundamentalSkillWrapperError(
                f"unsupported tushare_client_mode: {tushare_client_mode}"
            )
        if input_mode != INPUT_MODE_TICKER_ONLY_PROFESSIONAL_BRIEF:
            raise AShareFundamentalSkillWrapperError(
                "tushare_client_mode requires ticker-only professional brief input_mode"
            )

    renderer_mode = source.get("renderer_mode")
    if (
        renderer_mode is not None
        and input_mode != INPUT_MODE_TICKER_ONLY_PROFESSIONAL_BRIEF
    ):
        raise AShareFundamentalSkillWrapperError(
            "renderer_mode requires ticker-only professional brief input_mode"
        )
    if renderer_mode is None:
        renderer_mode = (
            RENDERER_MODE_DETERMINISTIC
            if input_mode == INPUT_MODE_TICKER_ONLY_PROFESSIONAL_BRIEF
            else None
        )
    else:
        renderer_mode = _validate_renderer_mode(
            renderer_mode,
            "renderer_mode",
        )

    allow_network = source.get("allow_network", False)
    if not isinstance(allow_network, bool):
        raise AShareFundamentalSkillWrapperError("allow_network must be bool")
    if allow_network is True and not (
        input_mode == INPUT_MODE_TICKER_ONLY_PROFESSIONAL_BRIEF
        and tushare_client_mode == TUSHARE_CLIENT_MODE_ENV_LIVE
    ):
        raise AShareFundamentalSkillWrapperError(
            "allow_network=true is only allowed for ticker-only professional brief env_live mode"
        )

    allow_file_writes = source.get("allow_file_writes", False)
    if allow_file_writes is True:
        raise AShareFundamentalSkillWrapperError(
            "allow_file_writes=true is not allowed"
        )
    if not isinstance(allow_file_writes, bool):
        raise AShareFundamentalSkillWrapperError("allow_file_writes must be bool")

    not_for_trading_advice = source.get("not_for_trading_advice", True)
    if not_for_trading_advice is not True:
        raise AShareFundamentalSkillWrapperError(
            "not_for_trading_advice must be true"
        )
    _assert_no_request_forbidden_markers(source)

    result = {
        "schema_version": source["schema_version"],
        "stock_code": _optional_string(source.get("stock_code"), "stock_code"),
        "ts_code": _optional_string(source.get("ts_code"), "ts_code"),
        "company_name_hint": _optional_string(
            source.get("company_name_hint"),
            "company_name_hint",
        ),
        "periods": _optional_string_list(source.get("periods"), "periods"),
        "input_mode": input_mode,
        "output_mode": output_mode,
        "tushare_client_mode": tushare_client_mode,
        "renderer_mode": renderer_mode,
        "user_facing_analysis_brief": deepcopy(
            source.get("user_facing_analysis_brief")
        ),
        "orchestration_result": deepcopy(source.get("orchestration_result")),
        "locator_result": deepcopy(source.get("locator_result")),
        "allow_network": allow_network,
        "allow_file_writes": False,
        "not_for_trading_advice": True,
    }
    return result


def validate_a_share_fundamental_skill_response(
    response: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate and return a defensive copy of a wrapper response."""

    source = _require_mapping(response, "response")
    unsupported = sorted(set(source) - _RESPONSE_FIELDS)
    if unsupported:
        raise AShareFundamentalSkillWrapperError(
            f"response contains unsupported keys: {unsupported}"
        )
    _reject_raw_inputs(source, "response")
    assert_no_a_share_fundamental_skill_wrapper_forbidden_markers(source)
    _require_fields(source, tuple(sorted(_RESPONSE_FIELDS)), "response")

    result = deepcopy(dict(source))
    if result["schema_version"] != A_SHARE_FUNDAMENTAL_SKILL_RESPONSE_SCHEMA_VERSION:
        raise AShareFundamentalSkillWrapperError("invalid response schema_version")
    result["readiness"] = _validate_readiness(result["readiness"])
    result["request_summary"] = _validate_request_summary(result["request_summary"])
    result["blocked_reasons"] = _validate_blocked_reasons(
        result["blocked_reasons"]
    )
    _require_string_list(result["caveats"], "caveats")
    _require_true(result["not_official_verified"], "not_official_verified")
    _require_true(result["not_for_trading_advice"], "not_for_trading_advice")

    compact_response = result["compact_response"]
    if compact_response is not None:
        result["compact_response"] = _validate_compact_response(compact_response)

    brief = result["user_facing_analysis_brief"]
    if brief is not None:
        result["user_facing_analysis_brief"] = validate_user_facing_analysis_brief(
            brief
        )

    compatibility_payload = result["report_v1_compatibility_payload"]
    if compatibility_payload is not None:
        result["report_v1_compatibility_payload"] = (
            validate_analysis_brief_report_v1_compatibility_payload(
                compatibility_payload
            )
        )

    professional_brief = result["professional_compact_brief"]
    if professional_brief is not None:
        result["professional_compact_brief"] = _validate_professional_compact_brief(
            professional_brief
        )

    internal_payload = result["professional_internal_payload"]
    if internal_payload is not None:
        result["professional_internal_payload"] = _validate_professional_internal_payload(
            internal_payload
        )

    _assert_response_consistency(result)
    assert_no_a_share_fundamental_skill_wrapper_forbidden_markers(result)
    return result


def build_compact_response_from_analysis_brief(
    brief: Mapping[str, Any],
) -> dict[str, Any]:
    """Build compact user-facing output from brief sections and preview only."""

    source = validate_user_facing_analysis_brief(brief)
    sections = source["user_visible_sections"]
    section_summaries = [
        {
            "section_id": section["section_id"],
            "section_title": section["section_title"],
            "analysis_label": section["analysis_label"],
            "summary_points": [
                point["text"] for point in section["analysis_points"]
            ],
        }
        for section in sections
    ]
    compact = {
        "schema_version": A_SHARE_FUNDAMENTAL_COMPACT_RESPONSE_SCHEMA_VERSION,
        "stock_code": source["stock_code"],
        "ts_code": source["ts_code"],
        "company_name_hint": source["company_name_hint"],
        "title": _compact_title(source),
        "summary_points": _first_points(sections),
        "section_summaries": section_summaries,
        "labels_used": _labels_used(sections),
        "cannot_conclude_yet": _section_point_texts(
            sections,
            "cannot_conclude_yet",
        ),
        "tracking_indicators": _section_point_texts(
            sections,
            "tracking_indicators",
        ),
        "markdown_preview": source["markdown_preview"],
        "not_for_trading_advice": True,
    }
    return _validate_compact_response(compact)


def build_request_summary(request: Mapping[str, Any]) -> dict[str, Any]:
    """Build a safe request summary without exposing backend details."""

    validated_request = validate_a_share_fundamental_skill_request(request)
    summary = {
        "schema_version": validated_request["schema_version"],
        "stock_code": validated_request["stock_code"],
        "ts_code": validated_request["ts_code"],
        "company_name_hint": validated_request["company_name_hint"],
        "periods": deepcopy(validated_request["periods"]),
        "input_mode": validated_request["input_mode"],
        "output_mode": validated_request["output_mode"],
        "tushare_client_mode": validated_request["tushare_client_mode"],
        "renderer_mode": validated_request["renderer_mode"],
        "allow_network": validated_request["allow_network"],
        "allow_file_writes": False,
        "has_user_facing_analysis_brief": (
            validated_request.get("user_facing_analysis_brief") is not None
        ),
        "has_orchestration_result": (
            validated_request.get("orchestration_result") is not None
        ),
        "has_locator_result": validated_request.get("locator_result") is not None,
        "not_for_trading_advice": True,
    }
    return _validate_request_summary(summary)


def build_skill_readiness(
    request: Mapping[str, Any],
    *,
    brief: Mapping[str, Any] | None = None,
    compatibility_payload: Mapping[str, Any] | None = None,
    professional_compact_brief: Mapping[str, Any] | None = None,
    professional_internal_payload: Mapping[str, Any] | None = None,
    blocked_reasons: Iterable[Mapping[str, str]] | None = None,
    status_override: str | None = None,
) -> dict[str, Any]:
    """Build readiness without fetching data or constructing artifacts."""

    validated_request = validate_a_share_fundamental_skill_request(request)
    missing_inputs = _missing_required_inputs(validated_request)
    reason_list = _validate_blocked_reasons(list(blocked_reasons or []))
    validation_errors = [reason["reason"] for reason in reason_list]
    requires_compatibility = (
        validated_request["output_mode"]
        == OUTPUT_MODE_COMPACT_BRIEF_AND_REPORT_V1_COMPATIBILITY_PAYLOAD
    )
    requires_professional_internal_payload = (
        validated_request["output_mode"]
        == OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF_AND_INTERNAL_PAYLOAD
    )
    is_ticker_only_professional = (
        validated_request["input_mode"] == INPUT_MODE_TICKER_ONLY_PROFESSIONAL_BRIEF
    )
    has_brief = brief is not None
    has_payload = compatibility_payload is not None
    has_professional_brief = professional_compact_brief is not None
    has_professional_internal_payload = professional_internal_payload is not None
    has_compact_response = (
        has_brief and not reason_list and not is_ticker_only_professional
    )
    required_inputs_present = not missing_inputs
    ready = (
        required_inputs_present
        and not validation_errors
        and (
            (
                has_professional_brief
                and (
                    has_professional_internal_payload
                    if requires_professional_internal_payload
                    else True
                )
            )
            if is_ticker_only_professional
            else (
                has_compact_response
                and has_brief
                and (has_payload if requires_compatibility else True)
            )
        )
    )
    if ready:
        status = SKILL_READINESS_READY
    elif status_override == SKILL_READINESS_SKIPPED:
        status = SKILL_READINESS_SKIPPED
    else:
        status = SKILL_READINESS_BLOCKED
    readiness = {
        "schema_version": A_SHARE_FUNDAMENTAL_SKILL_READINESS_SCHEMA_VERSION,
        "status": status,
        "input_mode": validated_request["input_mode"],
        "output_mode": validated_request["output_mode"],
        "renderer_mode": validated_request["renderer_mode"],
        "required_inputs_present": required_inputs_present,
        "missing_required_inputs": missing_inputs,
        "validation_errors": validation_errors,
        "has_compact_response": has_compact_response,
        "has_user_facing_analysis_brief": has_brief,
        "has_report_v1_compatibility_payload": has_payload,
        "has_professional_compact_brief": has_professional_brief,
        "has_professional_internal_payload": has_professional_internal_payload,
        "has_report_v1_artifact": False,
        "has_html_artifact": False,
        "has_trading_advice": False,
        "not_for_trading_advice": True,
    }
    return _validate_readiness(readiness)


def assert_no_a_share_fundamental_skill_wrapper_forbidden_markers(
    value: Any,
) -> None:
    """Reject wrapper-forbidden markers in nested keys, lists, and strings."""

    finding = _find_forbidden_marker(value)
    if finding:
        raise AShareFundamentalSkillWrapperError(
            "A-share fundamental skill wrapper safety violation: "
            f"forbidden marker: {finding}"
        )


def _assert_no_request_forbidden_markers(value: Any) -> None:
    finding = _find_forbidden_marker(value, skip_backend_inputs=True)
    if finding:
        raise AShareFundamentalSkillWrapperError(
            "A-share fundamental skill wrapper request safety violation: "
            f"forbidden marker: {finding}"
        )


def _build_ticker_only_professional_brief_response(
    request: Mapping[str, Any],
    *,
    tushare_client: Any | None,
) -> dict[str, Any]:
    missing_inputs = _missing_required_inputs(request)
    if missing_inputs:
        return _blocked_ticker_only_professional_brief_response(
            request,
            _missing_ticker_only_blocked_reasons(missing_inputs),
        )
    if (
        request["tushare_client_mode"] == TUSHARE_CLIENT_MODE_INJECTED
        and tushare_client is None
    ):
        return _blocked_ticker_only_professional_brief_response(
            request,
            [
                {
                    "reason": "injected_tushare_client_required",
                    "message": (
                        "ticker-only professional brief injected mode requires "
                        "an injected Tushare client"
                    ),
                }
            ],
        )

    from .controlled_real_tushare_professional_compact_brief_pilot import (
        CONTROLLED_REAL_TUSHARE_PROFESSIONAL_COMPACT_BRIEF_REQUEST_SCHEMA_VERSION,
        E2E_READINESS_SKIPPED,
        build_controlled_real_tushare_professional_compact_brief_result,
    )

    pilot_result = build_controlled_real_tushare_professional_compact_brief_result(
        {
            "schema_version": (
                CONTROLLED_REAL_TUSHARE_PROFESSIONAL_COMPACT_BRIEF_REQUEST_SCHEMA_VERSION
            ),
            "stock_code": request["stock_code"],
            "ts_code": request["ts_code"],
            "company_name_hint": request["company_name_hint"],
            "periods": deepcopy(request["periods"]),
            "allow_network": request["allow_network"],
            "tushare_client_mode": request["tushare_client_mode"],
            "renderer_mode": request["renderer_mode"],
            "output_mode": request["output_mode"],
            "not_for_trading_advice": True,
        },
        tushare_client=tushare_client,
    )

    professional_brief = pilot_result["professional_compact_brief"]
    internal_payload = pilot_result["internal_payload"]
    blocked_reasons = _professional_blocked_reasons(pilot_result)
    status_override = (
        SKILL_READINESS_SKIPPED
        if pilot_result["readiness"]["status"] == E2E_READINESS_SKIPPED
        else None
    )
    response = {
        "schema_version": A_SHARE_FUNDAMENTAL_SKILL_RESPONSE_SCHEMA_VERSION,
        "readiness": build_skill_readiness(
            request,
            professional_compact_brief=professional_brief,
            professional_internal_payload=internal_payload,
            blocked_reasons=blocked_reasons,
            status_override=status_override,
        ),
        "request_summary": build_request_summary(request),
        "compact_response": None,
        "user_facing_analysis_brief": None,
        "report_v1_compatibility_payload": None,
        "professional_compact_brief": professional_brief,
        "professional_internal_payload": internal_payload,
        "blocked_reasons": blocked_reasons,
        "caveats": _professional_response_caveats(),
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }
    return validate_a_share_fundamental_skill_response(response)


def _blocked_ticker_only_professional_brief_response(
    request: Mapping[str, Any],
    blocked_reasons: Iterable[Mapping[str, str]],
) -> dict[str, Any]:
    reason_list = _validate_blocked_reasons(list(blocked_reasons))
    response = {
        "schema_version": A_SHARE_FUNDAMENTAL_SKILL_RESPONSE_SCHEMA_VERSION,
        "readiness": build_skill_readiness(
            request,
            blocked_reasons=reason_list,
        ),
        "request_summary": build_request_summary(request),
        "compact_response": None,
        "user_facing_analysis_brief": None,
        "report_v1_compatibility_payload": None,
        "professional_compact_brief": None,
        "professional_internal_payload": None,
        "blocked_reasons": reason_list,
        "caveats": _professional_response_caveats(),
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }
    return validate_a_share_fundamental_skill_response(response)


def _missing_ticker_only_blocked_reasons(
    missing_inputs: Iterable[str],
) -> list[dict[str, str]]:
    reasons = []
    for missing_input in missing_inputs:
        if missing_input == "stock_code_or_ts_code":
            reasons.append(
                {
                    "reason": "ticker_identity_required",
                    "message": (
                        "ticker-only professional brief requires stock_code or ts_code"
                    ),
                }
            )
        elif missing_input == "tushare_client_mode":
            reasons.append(
                {
                    "reason": "tushare_client_mode_required",
                    "message": (
                        "ticker-only professional brief requires explicit "
                        "tushare_client_mode"
                    ),
                }
            )
        else:
            reasons.append(
                {
                    "reason": f"{missing_input}_required",
                    "message": f"ticker-only professional brief requires {missing_input}",
                }
            )
    return reasons


def _professional_blocked_reasons(
    pilot_result: Mapping[str, Any],
) -> list[dict[str, str]]:
    return [
        {
            "reason": str(reason),
            "message": f"ticker-only professional brief blocked: {reason}",
        }
        for reason in pilot_result["blocked_reasons"]
    ]


def _build_or_validate_brief(request: Mapping[str, Any]) -> dict[str, Any]:
    if request["input_mode"] == INPUT_MODE_ANALYSIS_BRIEF:
        return validate_user_facing_analysis_brief(
            request["user_facing_analysis_brief"]
        )
    payload: dict[str, Any] = {
        "orchestration_result": request["orchestration_result"],
        "allow_network": False,
        "not_for_trading_advice": True,
    }
    if request.get("locator_result") is not None:
        payload["locator_result"] = request["locator_result"]
    return build_user_facing_analysis_brief(payload)


def _missing_required_inputs(request: Mapping[str, Any]) -> list[str]:
    if request["input_mode"] == INPUT_MODE_ANALYSIS_BRIEF:
        if request.get("user_facing_analysis_brief") is None:
            return ["user_facing_analysis_brief"]
        return []
    if request["input_mode"] == INPUT_MODE_TICKER_ONLY_PROFESSIONAL_BRIEF:
        missing = []
        if request.get("stock_code") is None and request.get("ts_code") is None:
            missing.append("stock_code_or_ts_code")
        if request.get("tushare_client_mode") is None:
            missing.append("tushare_client_mode")
        return missing
    if request.get("orchestration_result") is None:
        return ["orchestration_result"]
    return []


def _validated_analysis_input_required_reason() -> dict[str, str]:
    return {
        "reason": BLOCKED_REASON_VALIDATED_ANALYSIS_INPUT_REQUIRED,
        "message": BLOCKED_MESSAGE_VALIDATED_ANALYSIS_INPUT_REQUIRED,
    }


def _response_caveats() -> list[str]:
    return [
        "Wrapper accepts explicit validated analysis inputs only.",
        "No external data call or artifact write is performed.",
        "Compact response is derived from user-visible brief sections only.",
    ]


def _professional_response_caveats() -> list[str]:
    return [
        "Wrapper accepts ticker-only professional brief requests only in this mode.",
        "No report, HTML, fixture, or output artifact is written.",
        "Professional compact brief is the user-facing view.",
    ]


def _compact_title(brief: Mapping[str, Any]) -> str:
    identity = " / ".join(
        str(value)
        for value in (
            brief.get("stock_code"),
            brief.get("ts_code"),
            brief.get("company_name_hint"),
        )
        if value not in (None, "")
    )
    return f"A-share fundamental brief: {identity or 'unknown subject'}"


def _first_points(sections: Iterable[Mapping[str, Any]]) -> list[str]:
    points = []
    for section in sections:
        analysis_points = section.get("analysis_points")
        if not isinstance(analysis_points, list) or not analysis_points:
            continue
        first = analysis_points[0]
        if isinstance(first, Mapping) and isinstance(first.get("text"), str):
            points.append(first["text"])
    return points


def _section_point_texts(
    sections: Iterable[Mapping[str, Any]],
    section_id: str,
) -> list[str]:
    for section in sections:
        if section.get("section_id") != section_id:
            continue
        return [
            point["text"]
            for point in section.get("analysis_points", [])
            if isinstance(point, Mapping) and isinstance(point.get("text"), str)
        ]
    return []


def _labels_used(sections: Iterable[Mapping[str, Any]]) -> list[str]:
    labels = []
    for section in sections:
        labels.append(section.get("analysis_label"))
        for point in section.get("analysis_points", []):
            if isinstance(point, Mapping):
                labels.append(point.get("label"))
    return [label for label in ANALYSIS_LABELS if label in labels]


def _validate_request_summary(value: Any) -> dict[str, Any]:
    summary = _require_mapping(value, "request_summary")
    unsupported = sorted(set(summary) - _REQUEST_SUMMARY_FIELDS)
    if unsupported:
        raise AShareFundamentalSkillWrapperError(
            f"request_summary contains unsupported keys: {unsupported}"
        )
    _require_fields(summary, tuple(sorted(_REQUEST_SUMMARY_FIELDS)), "request_summary")
    result = deepcopy(dict(summary))
    if result["schema_version"] != A_SHARE_FUNDAMENTAL_SKILL_REQUEST_SCHEMA_VERSION:
        raise AShareFundamentalSkillWrapperError(
            "request_summary schema_version invalid"
        )
    if result["input_mode"] not in SUPPORTED_INPUT_MODES:
        raise AShareFundamentalSkillWrapperError("request_summary input_mode invalid")
    if result["output_mode"] not in SUPPORTED_OUTPUT_MODES:
        raise AShareFundamentalSkillWrapperError("request_summary output_mode invalid")
    _validate_optional_renderer_mode_for_input(
        result["renderer_mode"],
        result["input_mode"],
        "request_summary.renderer_mode",
    )
    _require_optional_string_list(result["periods"], "request_summary.periods")
    if result["tushare_client_mode"] is not None and (
        result["tushare_client_mode"] not in SUPPORTED_TUSHARE_CLIENT_MODES
    ):
        raise AShareFundamentalSkillWrapperError(
            "request_summary tushare_client_mode invalid"
        )
    _require_optional_string(result["stock_code"], "request_summary.stock_code")
    _require_optional_string(result["ts_code"], "request_summary.ts_code")
    _require_optional_string(
        result["company_name_hint"],
        "request_summary.company_name_hint",
    )
    _require_bool(result["allow_network"], "request_summary.allow_network")
    if result["allow_network"] is True and not (
        result["input_mode"] == INPUT_MODE_TICKER_ONLY_PROFESSIONAL_BRIEF
        and result["tushare_client_mode"] == TUSHARE_CLIENT_MODE_ENV_LIVE
    ):
        raise AShareFundamentalSkillWrapperError(
            "request_summary allow_network true outside env_live professional path"
        )
    _require_false(
        result["allow_file_writes"],
        "request_summary.allow_file_writes",
    )
    for key in (
        "has_user_facing_analysis_brief",
        "has_orchestration_result",
        "has_locator_result",
    ):
        _require_bool(result[key], f"request_summary.{key}")
    _require_true(
        result["not_for_trading_advice"],
        "request_summary.not_for_trading_advice",
    )
    return result


def _validate_readiness(value: Any) -> dict[str, Any]:
    readiness = _require_mapping(value, "readiness")
    unsupported = sorted(set(readiness) - _READINESS_FIELDS)
    if unsupported:
        raise AShareFundamentalSkillWrapperError(
            f"readiness contains unsupported keys: {unsupported}"
        )
    _require_fields(readiness, tuple(sorted(_READINESS_FIELDS)), "readiness")
    result = deepcopy(dict(readiness))
    if result["schema_version"] != A_SHARE_FUNDAMENTAL_SKILL_READINESS_SCHEMA_VERSION:
        raise AShareFundamentalSkillWrapperError("invalid readiness schema_version")
    if result["status"] not in {
        SKILL_READINESS_READY,
        SKILL_READINESS_BLOCKED,
        SKILL_READINESS_SKIPPED,
    }:
        raise AShareFundamentalSkillWrapperError("readiness.status invalid")
    if result["input_mode"] not in SUPPORTED_INPUT_MODES:
        raise AShareFundamentalSkillWrapperError("readiness.input_mode invalid")
    if result["output_mode"] not in SUPPORTED_OUTPUT_MODES:
        raise AShareFundamentalSkillWrapperError("readiness.output_mode invalid")
    _validate_optional_renderer_mode_for_input(
        result["renderer_mode"],
        result["input_mode"],
        "readiness.renderer_mode",
    )
    _require_bool(
        result["required_inputs_present"],
        "readiness.required_inputs_present",
    )
    _require_string_list(
        result["missing_required_inputs"],
        "readiness.missing_required_inputs",
    )
    _require_string_list(result["validation_errors"], "readiness.validation_errors")
    for key in (
        "has_compact_response",
        "has_user_facing_analysis_brief",
        "has_report_v1_compatibility_payload",
        "has_professional_compact_brief",
        "has_professional_internal_payload",
        "has_report_v1_artifact",
        "has_html_artifact",
        "has_trading_advice",
    ):
        _require_bool(result[key], f"readiness.{key}")
    _require_false(result["has_report_v1_artifact"], "has_report_v1_artifact")
    _require_false(result["has_html_artifact"], "has_html_artifact")
    _require_false(result["has_trading_advice"], "has_trading_advice")
    _require_true(result["not_for_trading_advice"], "not_for_trading_advice")
    if result["status"] == SKILL_READINESS_READY:
        is_ticker_only_professional = (
            result["input_mode"] == INPUT_MODE_TICKER_ONLY_PROFESSIONAL_BRIEF
        )
        if not result["required_inputs_present"]:
            raise AShareFundamentalSkillWrapperError(
                "ready readiness requires required inputs"
            )
        if result["missing_required_inputs"] or result["validation_errors"]:
            raise AShareFundamentalSkillWrapperError(
                "ready readiness cannot include missing inputs or errors"
            )
        if is_ticker_only_professional:
            if not result["has_professional_compact_brief"]:
                raise AShareFundamentalSkillWrapperError(
                    "ready professional readiness requires professional brief"
                )
            if result["has_compact_response"] or result["has_user_facing_analysis_brief"]:
                raise AShareFundamentalSkillWrapperError(
                    "ready professional readiness must not expose compact response"
                )
            if (
                result["output_mode"]
                == OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF_AND_INTERNAL_PAYLOAD
                and not result["has_professional_internal_payload"]
            ):
                raise AShareFundamentalSkillWrapperError(
                    "professional internal payload output mode requires payload"
                )
            return result
        if not result["has_compact_response"]:
            raise AShareFundamentalSkillWrapperError(
                "ready readiness requires compact response"
            )
        if not result["has_user_facing_analysis_brief"]:
            raise AShareFundamentalSkillWrapperError(
                "ready readiness requires analysis brief"
            )
    return result


def _validate_compact_response(value: Any) -> dict[str, Any]:
    compact = _require_mapping(value, "compact_response")
    unsupported = sorted(set(compact) - _COMPACT_RESPONSE_FIELDS)
    if unsupported:
        raise AShareFundamentalSkillWrapperError(
            f"compact_response contains unsupported keys: {unsupported}"
        )
    _require_fields(compact, tuple(sorted(_COMPACT_RESPONSE_FIELDS)), "compact_response")
    result = deepcopy(dict(compact))
    if result["schema_version"] != A_SHARE_FUNDAMENTAL_COMPACT_RESPONSE_SCHEMA_VERSION:
        raise AShareFundamentalSkillWrapperError(
            "invalid compact_response schema_version"
        )
    _require_optional_string(result["stock_code"], "compact_response.stock_code")
    _require_optional_string(result["ts_code"], "compact_response.ts_code")
    _require_optional_string(
        result["company_name_hint"],
        "compact_response.company_name_hint",
    )
    _require_non_empty_string(result["title"], "compact_response.title")
    _require_string_list(result["summary_points"], "compact_response.summary_points")
    sections = _require_list(
        result["section_summaries"],
        "compact_response.section_summaries",
    )
    if not sections:
        raise AShareFundamentalSkillWrapperError(
            "compact_response.section_summaries cannot be empty"
        )
    section_ids = []
    for index, section in enumerate(sections):
        section_ids.append(
            _validate_compact_section_summary(
                section,
                f"compact_response.section_summaries[{index}]",
            )["section_id"]
        )
    if tuple(section_ids) != USER_VISIBLE_SECTION_IDS:
        raise AShareFundamentalSkillWrapperError(
            "compact_response section order invalid"
        )
    for label in _require_string_list(result["labels_used"], "labels_used"):
        if label not in ANALYSIS_LABELS:
            raise AShareFundamentalSkillWrapperError("labels_used contains invalid label")
    _require_string_list(
        result["cannot_conclude_yet"],
        "compact_response.cannot_conclude_yet",
    )
    _require_string_list(
        result["tracking_indicators"],
        "compact_response.tracking_indicators",
    )
    _require_non_empty_string(
        result["markdown_preview"],
        "compact_response.markdown_preview",
    )
    _require_true(
        result["not_for_trading_advice"],
        "compact_response.not_for_trading_advice",
    )
    _assert_no_compact_backend_trace_leak(result)
    assert_no_a_share_fundamental_skill_wrapper_forbidden_markers(result)
    return result


def _validate_compact_section_summary(value: Any, path: str) -> dict[str, Any]:
    section = _require_mapping(value, path)
    unsupported = sorted(set(section) - _COMPACT_SECTION_SUMMARY_FIELDS)
    if unsupported:
        raise AShareFundamentalSkillWrapperError(
            f"{path} contains unsupported keys: {unsupported}"
        )
    _require_fields(section, tuple(sorted(_COMPACT_SECTION_SUMMARY_FIELDS)), path)
    result = deepcopy(dict(section))
    if result["section_id"] not in USER_VISIBLE_SECTION_IDS:
        raise AShareFundamentalSkillWrapperError(f"{path}.section_id invalid")
    _require_non_empty_string(result["section_title"], f"{path}.section_title")
    if result["analysis_label"] not in ANALYSIS_LABELS:
        raise AShareFundamentalSkillWrapperError(f"{path}.analysis_label invalid")
    _require_string_list(result["summary_points"], f"{path}.summary_points")
    if not result["summary_points"]:
        raise AShareFundamentalSkillWrapperError(
            f"{path}.summary_points cannot be empty"
        )
    assert_no_a_share_fundamental_skill_wrapper_forbidden_markers(result)
    return result


def _validate_professional_compact_brief(value: Any) -> dict[str, Any]:
    brief = _require_mapping(value, "professional_compact_brief")
    unsupported = sorted(set(brief) - _PROFESSIONAL_BRIEF_FIELDS)
    if unsupported:
        raise AShareFundamentalSkillWrapperError(
            f"professional_compact_brief contains unsupported keys: {unsupported}"
        )
    _require_fields(
        brief,
        tuple(sorted(_PROFESSIONAL_BRIEF_FIELDS)),
        "professional_compact_brief",
    )
    result = deepcopy(dict(brief))
    if result["schema_version"] != PROFESSIONAL_ANALYST_COMPACT_BRIEF_SCHEMA_VERSION:
        raise AShareFundamentalSkillWrapperError(
            "professional_compact_brief schema_version invalid"
        )
    _require_optional_string(
        result["stock_code"],
        "professional_compact_brief.stock_code",
    )
    _require_optional_string(result["ts_code"], "professional_compact_brief.ts_code")
    _require_optional_string(
        result["company_name_hint"],
        "professional_compact_brief.company_name_hint",
    )
    _require_non_empty_string(result["title"], "professional_compact_brief.title")
    for key in PROFESSIONAL_BRIEF_SECTION_KEYS[:6]:
        result[key] = _validate_professional_section(
            result[key],
            f"professional_compact_brief.{key}",
        )
    _require_string_list(
        result["key_variables"],
        "professional_compact_brief.key_variables",
    )
    if not result["key_variables"]:
        raise AShareFundamentalSkillWrapperError(
            "professional_compact_brief.key_variables cannot be empty"
        )
    _require_non_empty_string(
        result["conclusion_boundary"],
        "professional_compact_brief.conclusion_boundary",
    )
    if result["source_note"] != "\u6570\u636e\u6765\u6e90\uff1aTushare\u3002":
        raise AShareFundamentalSkillWrapperError(
            "professional_compact_brief.source_note must be Tushare"
        )
    _require_true(
        result["not_for_trading_advice"],
        "professional_compact_brief.not_for_trading_advice",
    )
    _assert_no_professional_frontstage_leak(result)
    assert_no_a_share_fundamental_skill_wrapper_forbidden_markers(result)
    return result


def _validate_professional_section(value: Any, path: str) -> dict[str, Any]:
    section = _require_mapping(value, path)
    unsupported = sorted(set(section) - _PROFESSIONAL_SECTION_FIELDS)
    if unsupported:
        raise AShareFundamentalSkillWrapperError(
            f"{path} contains unsupported keys: {unsupported}"
        )
    _require_fields(section, tuple(sorted(_PROFESSIONAL_SECTION_FIELDS)), path)
    result = deepcopy(dict(section))
    if result["schema_version"] != (
        PROFESSIONAL_ANALYST_COMPACT_BRIEF_SECTION_SCHEMA_VERSION
    ):
        raise AShareFundamentalSkillWrapperError(f"{path}.schema_version invalid")
    _require_non_empty_string(result["section_id"], f"{path}.section_id")
    _require_non_empty_string(result["title"], f"{path}.title")
    view = _require_non_empty_string(result["view"], f"{path}.view")
    if len(view) < 24:
        raise AShareFundamentalSkillWrapperError(f"{path}.view is too thin")
    _require_true(result["not_for_trading_advice"], f"{path}.not_for_trading_advice")
    _assert_no_professional_frontstage_leak(result)
    assert_no_a_share_fundamental_skill_wrapper_forbidden_markers(result)
    return result


def _validate_professional_internal_payload(value: Any) -> dict[str, Any]:
    payload = _require_mapping(value, "professional_internal_payload")
    unsupported = sorted(set(payload) - _PROFESSIONAL_INTERNAL_PAYLOAD_FIELDS)
    if unsupported:
        raise AShareFundamentalSkillWrapperError(
            f"professional_internal_payload contains unsupported keys: {unsupported}"
        )
    _require_fields(
        payload,
        tuple(sorted(_PROFESSIONAL_INTERNAL_PAYLOAD_FIELDS)),
        "professional_internal_payload",
    )
    result = deepcopy(dict(payload))
    if result["schema_version"] != (
        "controlled_real_tushare_professional_internal_payload.v1"
    ):
        raise AShareFundamentalSkillWrapperError(
            "professional_internal_payload schema_version invalid"
        )
    _require_non_negative_int(
        result["provider_candidate_count"],
        "professional_internal_payload.provider_candidate_count",
    )
    for key in (
        "internal_analysis_brief_schema_version",
        "wrapper_response_schema_version",
        "wrapper_readiness_status",
    ):
        _require_non_empty_string(result[key], f"professional_internal_payload.{key}")
    _validate_renderer_mode(
        result["renderer_mode"],
        "professional_internal_payload.renderer_mode",
    )
    _require_true(
        result["not_official_verified"],
        "professional_internal_payload.not_official_verified",
    )
    _require_true(
        result["not_for_trading_advice"],
        "professional_internal_payload.not_for_trading_advice",
    )
    return result


def _validate_blocked_reasons(value: Any) -> list[dict[str, str]]:
    reasons = _require_list(value, "blocked_reasons")
    result = []
    for index, reason in enumerate(reasons):
        item = _require_mapping(reason, f"blocked_reasons[{index}]")
        _require_fields(item, ("reason", "message"), f"blocked_reasons[{index}]")
        result.append(
            {
                "reason": _require_non_empty_string(
                    item["reason"],
                    f"blocked_reasons[{index}].reason",
                ),
                "message": _require_non_empty_string(
                    item["message"],
                    f"blocked_reasons[{index}].message",
                ),
            }
        )
    return result


def _assert_response_consistency(response: Mapping[str, Any]) -> None:
    readiness = response["readiness"]
    compact_response = response["compact_response"]
    brief = response["user_facing_analysis_brief"]
    compatibility_payload = response["report_v1_compatibility_payload"]
    professional_brief = response["professional_compact_brief"]
    professional_internal_payload = response["professional_internal_payload"]
    blocked_reasons = response["blocked_reasons"]
    if readiness["has_compact_response"] != (compact_response is not None):
        raise AShareFundamentalSkillWrapperError(
            "readiness compact_response flag mismatch"
        )
    if readiness["has_user_facing_analysis_brief"] != (brief is not None):
        raise AShareFundamentalSkillWrapperError("readiness brief flag mismatch")
    if readiness["has_report_v1_compatibility_payload"] != (
        compatibility_payload is not None
    ):
        raise AShareFundamentalSkillWrapperError("readiness payload flag mismatch")
    if readiness["has_professional_compact_brief"] != (professional_brief is not None):
        raise AShareFundamentalSkillWrapperError(
            "readiness professional brief flag mismatch"
        )
    if readiness["has_professional_internal_payload"] != (
        professional_internal_payload is not None
    ):
        raise AShareFundamentalSkillWrapperError(
            "readiness professional internal payload flag mismatch"
        )
    if readiness["status"] == SKILL_READINESS_READY:
        if blocked_reasons:
            raise AShareFundamentalSkillWrapperError(
                "ready response cannot include blocked_reasons"
            )
        if readiness["input_mode"] == INPUT_MODE_TICKER_ONLY_PROFESSIONAL_BRIEF:
            if professional_brief is None:
                raise AShareFundamentalSkillWrapperError(
                    "ready professional response requires professional brief"
                )
            if compact_response is not None or brief is not None:
                raise AShareFundamentalSkillWrapperError(
                    "ready professional response must not include legacy compact fields"
                )
            if compatibility_payload is not None:
                raise AShareFundamentalSkillWrapperError(
                    "ready professional response must not include report payload"
                )
            if (
                readiness["output_mode"]
                == OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF_AND_INTERNAL_PAYLOAD
                and professional_internal_payload is None
            ):
                raise AShareFundamentalSkillWrapperError(
                    "professional internal payload output mode requires payload"
                )
            return
        if compact_response is None or brief is None:
            raise AShareFundamentalSkillWrapperError(
                "ready response requires compact response and brief"
            )
        if (
            readiness["output_mode"]
            == OUTPUT_MODE_COMPACT_BRIEF_AND_REPORT_V1_COMPATIBILITY_PAYLOAD
            and compatibility_payload is None
        ):
            raise AShareFundamentalSkillWrapperError(
                "compatibility output mode requires compatibility payload"
            )
    else:
        if not blocked_reasons and not readiness["missing_required_inputs"]:
            raise AShareFundamentalSkillWrapperError(
                "blocked response requires blocked reason or missing input"
            )
        if professional_brief is not None or professional_internal_payload is not None:
            raise AShareFundamentalSkillWrapperError(
                "blocked response must not include professional outputs"
            )


def _assert_no_compact_backend_trace_leak(value: Mapping[str, Any]) -> None:
    serialized = json.dumps(value, ensure_ascii=False)
    normalized = serialized.casefold()
    for marker in _COMPACT_FORBIDDEN_OUTPUT_MARKERS:
        if marker.casefold() in normalized:
            raise AShareFundamentalSkillWrapperError(
                "compact_response contains backend trace marker"
            )


def _assert_no_professional_frontstage_leak(value: Mapping[str, Any]) -> None:
    serialized = json.dumps(value, ensure_ascii=False)
    normalized = serialized.casefold()
    separator_normalized = _normalize_separator_text(serialized)
    marker_normalized_text = _normalise_marker(serialized)
    for marker in _PROFESSIONAL_FRONTSTAGE_FORBIDDEN_MARKERS:
        marker_lower = marker.casefold()
        marker_separator = _normalize_separator_text(marker)
        marker_normalized = _normalise_marker(marker)
        if (
            marker_lower in normalized
            or marker_separator in separator_normalized
            or (marker_normalized and marker_normalized in marker_normalized_text)
        ):
            raise AShareFundamentalSkillWrapperError(
                "professional_compact_brief contains frontstage forbidden marker"
            )
    finding = _find_forbidden_marker(value)
    if finding:
        raise AShareFundamentalSkillWrapperError(
            "professional_compact_brief contains wrapper-forbidden marker"
        )


def _reject_raw_inputs(value: Any, path: str) -> None:
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise AShareFundamentalSkillWrapperError(f"{path} contains raw bytes")
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text == "locator_result":
                _reject_bytes(child, child_path)
                continue
            if _normalise_marker(key_text) in _RAW_INPUT_KEYS or key_text in _RAW_INPUT_KEYS:
                raise AShareFundamentalSkillWrapperError(
                    f"{path} contains unsupported raw input key: {key_text}"
                )
            _reject_raw_inputs(child, child_path)
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            _reject_raw_inputs(child, f"{path}[{index}]")


def _reject_bytes(value: Any, path: str) -> None:
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise AShareFundamentalSkillWrapperError(f"{path} contains raw bytes")
    if isinstance(value, Mapping):
        for key, child in value.items():
            _reject_bytes(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_bytes(child, f"{path}[{index}]")


def _find_forbidden_marker(value: Any, *, skip_backend_inputs: bool = False) -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if skip_backend_inputs and key_text in {
                "locator_result",
                "orchestration_result",
            }:
                continue
            if key_text not in _ALLOWED_EXACT_TEXTS:
                key_finding = _text_forbidden_marker(key_text)
                if key_finding:
                    return key_finding
            child_finding = _find_forbidden_marker(
                child,
                skip_backend_inputs=skip_backend_inputs,
            )
            if child_finding:
                return child_finding
        return None
    if isinstance(value, (list, tuple, set)):
        for item in value:
            item_finding = _find_forbidden_marker(
                item,
                skip_backend_inputs=skip_backend_inputs,
            )
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


def _optional_string(value: Any, path: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise AShareFundamentalSkillWrapperError(f"{path} must be string or null")
    return value


def _optional_string_list(value: Any, path: str) -> list[str] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise AShareFundamentalSkillWrapperError(f"{path} must be a list or null")
    result = []
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise AShareFundamentalSkillWrapperError(
                f"{path}[{index}] must be string"
            )
        result.append(item)
    return result


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AShareFundamentalSkillWrapperError(f"{field} must be a mapping")
    return value


def _require_fields(value: Mapping[str, Any], fields: tuple[str, ...], path: str) -> None:
    missing = [field for field in fields if field not in value]
    if missing:
        raise AShareFundamentalSkillWrapperError(
            f"{path} missing required fields: {missing}"
        )


def _require_optional_string(value: Any, path: str) -> None:
    if value is not None and not isinstance(value, str):
        raise AShareFundamentalSkillWrapperError(f"{path} must be string or null")


def _require_optional_string_list(value: Any, path: str) -> None:
    if value is None:
        return
    _require_string_list(value, path)


def _validate_renderer_mode(value: Any, path: str) -> str:
    if not isinstance(value, str):
        raise AShareFundamentalSkillWrapperError(f"{path} must be string")
    if value not in SUPPORTED_RENDERER_MODES:
        raise AShareFundamentalSkillWrapperError(
            f"unsupported renderer_mode: {value}"
        )
    return value


def _validate_optional_renderer_mode_for_input(
    value: Any,
    input_mode: str,
    path: str,
) -> None:
    if input_mode == INPUT_MODE_TICKER_ONLY_PROFESSIONAL_BRIEF:
        _validate_renderer_mode(value, path)
        return
    if value is not None:
        raise AShareFundamentalSkillWrapperError(
            f"{path} requires ticker-only professional brief input_mode"
        )


def _require_non_empty_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AShareFundamentalSkillWrapperError(
            f"{path} must be a non-empty string"
        )
    return value


def _require_string_list(value: Any, path: str) -> list[str]:
    if not isinstance(value, list):
        raise AShareFundamentalSkillWrapperError(f"{path} must be a list")
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise AShareFundamentalSkillWrapperError(
                f"{path}[{index}] must be string"
            )
    return value


def _require_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise AShareFundamentalSkillWrapperError(f"{path} must be a list")
    return value


def _require_true(value: Any, path: str) -> None:
    if value is not True:
        raise AShareFundamentalSkillWrapperError(f"{path} must be true")


def _require_false(value: Any, path: str) -> None:
    if value is not False:
        raise AShareFundamentalSkillWrapperError(f"{path} must be false")


def _require_bool(value: Any, path: str) -> None:
    if not isinstance(value, bool):
        raise AShareFundamentalSkillWrapperError(f"{path} must be bool")


def _require_non_negative_int(value: Any, path: str) -> int:
    if not isinstance(value, int) or value < 0:
        raise AShareFundamentalSkillWrapperError(
            f"{path} must be a non-negative int"
        )
    return value


__all__ = [
    "A_SHARE_FUNDAMENTAL_COMPACT_RESPONSE_SCHEMA_VERSION",
    "A_SHARE_FUNDAMENTAL_SKILL_READINESS_SCHEMA_VERSION",
    "A_SHARE_FUNDAMENTAL_SKILL_REQUEST_SCHEMA_VERSION",
    "A_SHARE_FUNDAMENTAL_SKILL_RESPONSE_SCHEMA_VERSION",
    "BLOCKED_MESSAGE_VALIDATED_ANALYSIS_INPUT_REQUIRED",
    "BLOCKED_REASON_VALIDATED_ANALYSIS_INPUT_REQUIRED",
    "INPUT_MODE_ANALYSIS_BRIEF",
    "INPUT_MODE_ORCHESTRATION_RESULT",
    "INPUT_MODE_TICKER_ONLY_PROFESSIONAL_BRIEF",
    "OUTPUT_MODE_COMPACT_BRIEF",
    "OUTPUT_MODE_COMPACT_BRIEF_AND_REPORT_V1_COMPATIBILITY_PAYLOAD",
    "OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF",
    "OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF_AND_INTERNAL_PAYLOAD",
    "PROFESSIONAL_ANALYST_COMPACT_BRIEF_SCHEMA_VERSION",
    "PROFESSIONAL_BRIEF_SECTION_KEYS",
    "RENDERER_MODE_DETERMINISTIC",
    "RENDERER_MODE_FAKE_LLM",
    "SKILL_READINESS_BLOCKED",
    "SKILL_READINESS_READY",
    "SKILL_READINESS_SKIPPED",
    "SUPPORTED_INPUT_MODES",
    "SUPPORTED_OUTPUT_MODES",
    "SUPPORTED_RENDERER_MODES",
    "SUPPORTED_TUSHARE_CLIENT_MODES",
    "TUSHARE_CLIENT_MODE_ENV_LIVE",
    "TUSHARE_CLIENT_MODE_FAKE",
    "TUSHARE_CLIENT_MODE_INJECTED",
    "UNSUPPORTED_INPUT_MODES",
    "UNSUPPORTED_OUTPUT_MODES",
    "AShareFundamentalSkillWrapperError",
    "assert_no_a_share_fundamental_skill_wrapper_forbidden_markers",
    "build_a_share_fundamental_skill_response",
    "build_compact_response_from_analysis_brief",
    "build_request_summary",
    "build_skill_readiness",
    "validate_a_share_fundamental_skill_request",
    "validate_a_share_fundamental_skill_response",
]
