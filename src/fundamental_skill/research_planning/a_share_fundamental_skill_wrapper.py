# -*- coding: utf-8 -*-
"""Callable A-share fundamental skill wrapper thin slice.

This module is a small in-memory entry point around the existing Analysis Brief
chain. It accepts only explicit validated inputs, never fetches live data, never
writes artifacts, and never builds report or HTML outputs.
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
SUPPORTED_INPUT_MODES = (
    INPUT_MODE_ANALYSIS_BRIEF,
    INPUT_MODE_ORCHESTRATION_RESULT,
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
SUPPORTED_OUTPUT_MODES = (
    OUTPUT_MODE_COMPACT_BRIEF,
    OUTPUT_MODE_COMPACT_BRIEF_AND_REPORT_V1_COMPATIBILITY_PAYLOAD,
)
UNSUPPORTED_OUTPUT_MODES = (
    "report_v1_artifact",
    "html_artifact",
    "live_full_report",
    "trading_signal",
)

SKILL_READINESS_READY = "ready"
SKILL_READINESS_BLOCKED = "blocked"

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
    "input_mode",
    "output_mode",
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
    "input_mode",
    "output_mode",
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
    "required_inputs_present",
    "missing_required_inputs",
    "validation_errors",
    "has_compact_response",
    "has_user_facing_analysis_brief",
    "has_report_v1_compatibility_payload",
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
) -> dict[str, Any]:
    """Build the compact skill response from explicit validated inputs."""

    validated_request = validate_a_share_fundamental_skill_request(request)
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

    output_mode = source.get("output_mode", OUTPUT_MODE_COMPACT_BRIEF)
    if output_mode not in SUPPORTED_OUTPUT_MODES:
        raise AShareFundamentalSkillWrapperError(
            f"unsupported output_mode: {output_mode}"
        )

    allow_network = source.get("allow_network", False)
    if allow_network is True:
        raise AShareFundamentalSkillWrapperError(
            "allow_network=true is not allowed"
        )
    if not isinstance(allow_network, bool):
        raise AShareFundamentalSkillWrapperError("allow_network must be bool")

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
        "input_mode": input_mode,
        "output_mode": output_mode,
        "user_facing_analysis_brief": deepcopy(
            source.get("user_facing_analysis_brief")
        ),
        "orchestration_result": deepcopy(source.get("orchestration_result")),
        "locator_result": deepcopy(source.get("locator_result")),
        "allow_network": False,
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
        "input_mode": validated_request["input_mode"],
        "output_mode": validated_request["output_mode"],
        "allow_network": False,
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
    blocked_reasons: Iterable[Mapping[str, str]] | None = None,
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
    has_brief = brief is not None
    has_payload = compatibility_payload is not None
    has_compact_response = has_brief and not reason_list
    required_inputs_present = not missing_inputs
    status = (
        SKILL_READINESS_READY
        if (
            required_inputs_present
            and not validation_errors
            and has_compact_response
            and has_brief
            and (has_payload if requires_compatibility else True)
        )
        else SKILL_READINESS_BLOCKED
    )
    readiness = {
        "schema_version": A_SHARE_FUNDAMENTAL_SKILL_READINESS_SCHEMA_VERSION,
        "status": status,
        "input_mode": validated_request["input_mode"],
        "output_mode": validated_request["output_mode"],
        "required_inputs_present": required_inputs_present,
        "missing_required_inputs": missing_inputs,
        "validation_errors": validation_errors,
        "has_compact_response": has_compact_response,
        "has_user_facing_analysis_brief": has_brief,
        "has_report_v1_compatibility_payload": has_payload,
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
    _require_optional_string(result["stock_code"], "request_summary.stock_code")
    _require_optional_string(result["ts_code"], "request_summary.ts_code")
    _require_optional_string(
        result["company_name_hint"],
        "request_summary.company_name_hint",
    )
    _require_false(result["allow_network"], "request_summary.allow_network")
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
    if result["status"] not in {SKILL_READINESS_READY, SKILL_READINESS_BLOCKED}:
        raise AShareFundamentalSkillWrapperError("readiness.status invalid")
    if result["input_mode"] not in SUPPORTED_INPUT_MODES:
        raise AShareFundamentalSkillWrapperError("readiness.input_mode invalid")
    if result["output_mode"] not in SUPPORTED_OUTPUT_MODES:
        raise AShareFundamentalSkillWrapperError("readiness.output_mode invalid")
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
        if not result["required_inputs_present"]:
            raise AShareFundamentalSkillWrapperError(
                "ready readiness requires required inputs"
            )
        if result["missing_required_inputs"] or result["validation_errors"]:
            raise AShareFundamentalSkillWrapperError(
                "ready readiness cannot include missing inputs or errors"
            )
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
    if readiness["status"] == SKILL_READINESS_READY:
        if blocked_reasons:
            raise AShareFundamentalSkillWrapperError(
                "ready response cannot include blocked_reasons"
            )
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


def _assert_no_compact_backend_trace_leak(value: Mapping[str, Any]) -> None:
    serialized = json.dumps(value, ensure_ascii=False)
    normalized = serialized.casefold()
    for marker in _COMPACT_FORBIDDEN_OUTPUT_MARKERS:
        if marker.casefold() in normalized:
            raise AShareFundamentalSkillWrapperError(
                "compact_response contains backend trace marker"
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


__all__ = [
    "A_SHARE_FUNDAMENTAL_COMPACT_RESPONSE_SCHEMA_VERSION",
    "A_SHARE_FUNDAMENTAL_SKILL_READINESS_SCHEMA_VERSION",
    "A_SHARE_FUNDAMENTAL_SKILL_REQUEST_SCHEMA_VERSION",
    "A_SHARE_FUNDAMENTAL_SKILL_RESPONSE_SCHEMA_VERSION",
    "BLOCKED_MESSAGE_VALIDATED_ANALYSIS_INPUT_REQUIRED",
    "BLOCKED_REASON_VALIDATED_ANALYSIS_INPUT_REQUIRED",
    "INPUT_MODE_ANALYSIS_BRIEF",
    "INPUT_MODE_ORCHESTRATION_RESULT",
    "OUTPUT_MODE_COMPACT_BRIEF",
    "OUTPUT_MODE_COMPACT_BRIEF_AND_REPORT_V1_COMPATIBILITY_PAYLOAD",
    "SKILL_READINESS_BLOCKED",
    "SKILL_READINESS_READY",
    "SUPPORTED_INPUT_MODES",
    "SUPPORTED_OUTPUT_MODES",
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
