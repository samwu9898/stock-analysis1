# -*- coding: utf-8 -*-
"""Standalone orchestration entry for live evidence research-pack slices.

This module accepts already-validated component payloads, assembles the existing
live evidence-aware vertical slice, and wraps it in a public orchestration
result. It does not fetch live data, read files, write artifacts, parse PDFs, or
create analyst conclusions.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
import re
from typing import Any

from .live_evidence_aware_research_pack_vertical_slice import (
    LIVE_EVIDENCE_AWARE_RESEARCH_PACK_VERTICAL_SLICE_SCHEMA_VERSION,
    assert_no_live_research_pack_forbidden_markers,
    build_live_evidence_aware_research_pack_vertical_slice,
    validate_live_evidence_aware_research_pack_vertical_slice,
)


LIVE_EVIDENCE_RESEARCH_PACK_ORCHESTRATION_REQUEST_SCHEMA_VERSION = (
    "live_evidence_research_pack_orchestration_request.v1"
)
LIVE_EVIDENCE_RESEARCH_PACK_ORCHESTRATION_RESULT_SCHEMA_VERSION = (
    "live_evidence_research_pack_orchestration_result.v1"
)
LIVE_EVIDENCE_RESEARCH_PACK_ORCHESTRATION_READINESS_SCHEMA_VERSION = (
    "live_evidence_research_pack_orchestration_readiness.v1"
)

REQUESTED_OUTPUT_VERTICAL_SLICE_AND_MARKDOWN_PREVIEW = (
    "vertical_slice_and_markdown_preview"
)

ORCHESTRATION_READINESS_READY = "ready"
ORCHESTRATION_READINESS_BLOCKED = "blocked"

REQUIRED_COMPONENT_KEYS = ("evidence_aware_research_pack_scaffold",)
OPTIONAL_COMPONENT_KEYS = (
    "ticker_research_context_skeleton",
    "provider_metric_official_anchor_map",
    "real_official_metadata_anchor_handoff_result",
    "official_disclosure_artifact_cache",
)
ALLOWED_COMPONENT_KEYS = set(REQUIRED_COMPONENT_KEYS + OPTIONAL_COMPONENT_KEYS)

_REQUEST_FIELDS = {
    "schema_version",
    "stock_code",
    "ts_code",
    "company_name_hint",
    "components",
    "requested_output",
    "allow_network",
    "not_for_trading_advice",
}

_RAW_REQUEST_KEYS = {
    "arbitrary_url",
    "cache_file_content",
    "cache_file_bytes",
    "cache_path",
    "download_url",
    "final_url",
    "http_response",
    "pdf_bytes",
    "pdf_url",
    "raw_http_response",
    "raw_provider_queue",
    "raw_tushare_provider_result",
    "source_url",
    "url",
}

_RAW_COMPONENT_KEYS = {
    "arbitrary_url",
    "cache_file_content",
    "cache_file_bytes",
    "official_http_response",
    "pdf_bytes",
    "provider_candidate_financial_result",
    "provider_candidate_financial_snapshot",
    "provider_candidate_financial_trend_table",
    "provider_candidate_metric_verification_queue",
    "provider_candidate_verification_queue",
    "provider_queue",
    "raw_http_response",
    "raw_official_http_response",
    "raw_pdf_bytes",
    "raw_provider_queue",
    "raw_tushare_provider_result",
    "tushare_provider_result",
}

_RESULT_REQUIRED_FIELDS = (
    "schema_version",
    "request_summary",
    "readiness",
    "vertical_slice",
    "markdown_preview",
    "evidence_status_rollup",
    "source_component_summary",
    "blocked_reasons",
    "caveats",
    "not_official_verified",
    "not_for_trading_advice",
)

_READINESS_REQUIRED_FIELDS = (
    "schema_version",
    "status",
    "required_components_present",
    "optional_components_present",
    "missing_required_components",
    "validation_errors",
    "has_vertical_slice",
    "has_markdown_preview",
    "has_formal_research_report",
    "has_trading_advice",
    "not_for_trading_advice",
)

_SOURCE_COMPONENT_SUMMARY_REQUIRED_FIELDS = (
    "component_keys_present",
    "required_component_keys",
    "optional_component_keys_allowed",
    "optional_component_keys_present",
    "component_schema_versions",
    "not_official_verified",
    "not_for_trading_advice",
)

_ALLOWED_EXACT_KEYS = {
    "has_formal_research_report",
    "has_trading_advice",
    "not_for_trading_advice",
    "not_official_verified",
    "official_verified_count",
}

_EVIDENCE_STATUS_FIELD_KEYS = {
    "anchor_evidence_status",
    "artifact_evidence_status",
    "current_evidence_status",
    "evidence_status",
    "official_evidence_statuses",
    "official_verification_status",
    "required_next_status",
    "source_anchor_status",
    "status",
    "status_label",
    "statuses_used",
}

_EVIDENCE_STATUS_VALUES = {
    "artifact_cached",
    "blocked",
    "data_gap",
    "framework_inference",
    "local_experiment",
    "not_assessable",
    "official_anchor_matched",
    "official_verified",
    "pending_official_verification",
    "provider_candidate",
}

_CONTROLLED_ALLOWED_TEXTS = {
    "official_verified_count",
    "\u8fd9\u4e0d\u662f\u6b63\u5f0f\u7814\u62a5 / \u4e0d\u662f\u6295\u8d44\u5efa\u8bae",
    "\u8fd9\u4e0d\u662f\u6b63\u5f0f\u7814\u62a5/\u4e0d\u662f\u6295\u8d44\u5efa\u8bae",
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
    "live provider",
    "live Tushare",
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


class LiveEvidenceResearchPackOrchestrationEntryError(ValueError):
    """Raised when orchestration entry validation fails closed."""


def build_live_evidence_research_pack_orchestration_result(
    request: Mapping[str, Any],
) -> dict[str, Any]:
    """Build an orchestration result from explicit validated components."""

    validated_request = validate_live_evidence_research_pack_orchestration_request(
        request
    )
    readiness = build_orchestration_readiness(validated_request)
    if readiness["missing_required_components"] or readiness["validation_errors"]:
        return validate_live_evidence_research_pack_orchestration_result(
            _build_blocked_result(
                validated_request,
                readiness,
                _blocked_reasons_from_readiness(readiness),
            )
        )

    try:
        vertical_slice = build_live_evidence_aware_research_pack_vertical_slice(
            validated_request["components"]
        )
        vertical_slice = validate_live_evidence_aware_research_pack_vertical_slice(
            vertical_slice
        )
    except ValueError as exc:
        raise LiveEvidenceResearchPackOrchestrationEntryError(
            f"vertical_slice_build_failed: {_safe_error_message(exc)}"
        ) from exc

    identity_errors = _identity_consistency_errors(validated_request, vertical_slice)
    if identity_errors:
        blocked_readiness = build_orchestration_readiness(
            validated_request,
            validation_errors=identity_errors,
        )
        return validate_live_evidence_research_pack_orchestration_result(
            _build_blocked_result(validated_request, blocked_readiness, identity_errors)
        )

    ready_readiness = build_orchestration_readiness(
        validated_request,
        vertical_slice=vertical_slice,
    )
    result = {
        "schema_version": LIVE_EVIDENCE_RESEARCH_PACK_ORCHESTRATION_RESULT_SCHEMA_VERSION,
        "request_summary": build_request_summary(validated_request),
        "readiness": ready_readiness,
        "vertical_slice": vertical_slice,
        "markdown_preview": vertical_slice["user_readable_markdown_preview"],
        "evidence_status_rollup": vertical_slice["evidence_status_rollup"],
        "source_component_summary": build_source_component_summary(validated_request),
        "blocked_reasons": [],
        "caveats": _result_caveats(),
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }
    return validate_live_evidence_research_pack_orchestration_result(result)


def validate_live_evidence_research_pack_orchestration_request(
    request: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate and normalize the public orchestration request."""

    source = _require_mapping(request, "orchestration_request")
    _reject_raw_request_keys(source)
    unsupported = sorted(set(source) - _REQUEST_FIELDS)
    if unsupported:
        raise LiveEvidenceResearchPackOrchestrationEntryError(
            f"request contains unsupported keys: {unsupported}"
        )
    _reject_bytes(source, "orchestration_request")
    assert_no_live_evidence_orchestration_forbidden_markers(source)

    if source.get("schema_version") != (
        LIVE_EVIDENCE_RESEARCH_PACK_ORCHESTRATION_REQUEST_SCHEMA_VERSION
    ):
        raise LiveEvidenceResearchPackOrchestrationEntryError(
            "schema_version must be "
            f"{LIVE_EVIDENCE_RESEARCH_PACK_ORCHESTRATION_REQUEST_SCHEMA_VERSION}"
        )

    requested_output = source.get(
        "requested_output",
        REQUESTED_OUTPUT_VERTICAL_SLICE_AND_MARKDOWN_PREVIEW,
    )
    if requested_output != REQUESTED_OUTPUT_VERTICAL_SLICE_AND_MARKDOWN_PREVIEW:
        raise LiveEvidenceResearchPackOrchestrationEntryError(
            "requested_output must be "
            f"{REQUESTED_OUTPUT_VERTICAL_SLICE_AND_MARKDOWN_PREVIEW}"
        )

    allow_network = source.get("allow_network", False)
    if allow_network is True:
        raise LiveEvidenceResearchPackOrchestrationEntryError(
            "allow_network=true is not allowed"
        )
    if not isinstance(allow_network, bool):
        raise LiveEvidenceResearchPackOrchestrationEntryError(
            "allow_network must be a bool"
        )

    not_for_trading_advice = source.get("not_for_trading_advice", True)
    if not_for_trading_advice is not True:
        raise LiveEvidenceResearchPackOrchestrationEntryError(
            "not_for_trading_advice must be true"
        )

    components = source.get("components", {})
    if components is None:
        components = {}
    if not isinstance(components, Mapping):
        raise LiveEvidenceResearchPackOrchestrationEntryError(
            "components must be a mapping"
        )
    _reject_raw_component_keys(components)
    unsupported_components = sorted(set(components) - ALLOWED_COMPONENT_KEYS)
    if unsupported_components:
        raise LiveEvidenceResearchPackOrchestrationEntryError(
            f"components contains unsupported keys: {unsupported_components}"
        )

    result = {
        "schema_version": source["schema_version"],
        "stock_code": _optional_string(source.get("stock_code"), "stock_code"),
        "ts_code": _optional_string(source.get("ts_code"), "ts_code"),
        "company_name_hint": _optional_string(
            source.get("company_name_hint"),
            "company_name_hint",
        ),
        "components": deepcopy(dict(components)),
        "requested_output": requested_output,
        "allow_network": False,
        "not_for_trading_advice": True,
    }
    assert_no_live_evidence_orchestration_forbidden_markers(result)
    return result


def validate_live_evidence_research_pack_orchestration_result(
    result: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate and return a defensive copy of an orchestration result."""

    source = _require_mapping(result, "orchestration_result")
    _require_fields(source, _RESULT_REQUIRED_FIELDS, "orchestration_result")
    assert_no_live_evidence_orchestration_forbidden_markers(source)
    copied = deepcopy(dict(source))

    if copied["schema_version"] != (
        LIVE_EVIDENCE_RESEARCH_PACK_ORCHESTRATION_RESULT_SCHEMA_VERSION
    ):
        raise LiveEvidenceResearchPackOrchestrationEntryError(
            "orchestration result schema_version is invalid"
        )
    _require_mapping(copied["request_summary"], "request_summary")
    copied["readiness"] = _validate_readiness(copied["readiness"])
    copied["source_component_summary"] = _validate_source_component_summary(
        copied["source_component_summary"]
    )
    _require_string_list(copied["blocked_reasons"], "blocked_reasons")
    _require_string_list(copied["caveats"], "caveats")
    _require_true(copied["not_official_verified"], "not_official_verified")
    _require_true(copied["not_for_trading_advice"], "not_for_trading_advice")

    if copied["readiness"]["status"] == ORCHESTRATION_READINESS_READY:
        copied["vertical_slice"] = validate_live_evidence_aware_research_pack_vertical_slice(
            copied["vertical_slice"]
        )
        preview = _require_non_empty_string(
            copied["markdown_preview"],
            "markdown_preview",
        )
        if preview != copied["vertical_slice"]["user_readable_markdown_preview"]:
            raise LiveEvidenceResearchPackOrchestrationEntryError(
                "markdown_preview must match vertical_slice.user_readable_markdown_preview"
            )
        rollup = _require_mapping(
            copied["evidence_status_rollup"],
            "evidence_status_rollup",
        )
        if rollup != copied["vertical_slice"]["evidence_status_rollup"]:
            raise LiveEvidenceResearchPackOrchestrationEntryError(
                "evidence_status_rollup must match vertical_slice.evidence_status_rollup"
            )
    else:
        if copied["vertical_slice"] is not None:
            raise LiveEvidenceResearchPackOrchestrationEntryError(
                "blocked result must not include vertical_slice"
            )
        if copied["markdown_preview"] != "":
            raise LiveEvidenceResearchPackOrchestrationEntryError(
                "blocked result must not include markdown_preview"
            )
        if copied["evidence_status_rollup"] is not None:
            raise LiveEvidenceResearchPackOrchestrationEntryError(
                "blocked result must not include evidence_status_rollup"
            )

    return copied


def build_orchestration_readiness(
    request: Mapping[str, Any],
    *,
    vertical_slice: Mapping[str, Any] | None = None,
    validation_errors: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Build readiness without constructing or fetching any upstream component."""

    validated_request = validate_live_evidence_research_pack_orchestration_request(
        request
    )
    components = validated_request["components"]
    present_keys = set(components)
    missing_required = [
        key for key in REQUIRED_COMPONENT_KEYS if key not in present_keys
    ]
    validation_error_list = _dedupe_preserve_order(validation_errors or [])
    has_vertical_slice = vertical_slice is not None
    has_markdown_preview = bool(
        isinstance(vertical_slice, Mapping)
        and isinstance(vertical_slice.get("user_readable_markdown_preview"), str)
        and vertical_slice.get("user_readable_markdown_preview", "").strip()
    )
    status = (
        ORCHESTRATION_READINESS_READY
        if not missing_required
        and not validation_error_list
        and has_vertical_slice
        and has_markdown_preview
        else ORCHESTRATION_READINESS_BLOCKED
    )
    readiness = {
        "schema_version": (
            LIVE_EVIDENCE_RESEARCH_PACK_ORCHESTRATION_READINESS_SCHEMA_VERSION
        ),
        "status": status,
        "required_components_present": [
            key for key in REQUIRED_COMPONENT_KEYS if key in present_keys
        ],
        "optional_components_present": [
            key for key in OPTIONAL_COMPONENT_KEYS if key in present_keys
        ],
        "missing_required_components": missing_required,
        "validation_errors": validation_error_list,
        "has_vertical_slice": has_vertical_slice,
        "has_markdown_preview": has_markdown_preview,
        "has_formal_research_report": False,
        "has_trading_advice": False,
        "not_for_trading_advice": True,
    }
    return _validate_readiness(readiness)


def build_request_summary(request: Mapping[str, Any]) -> dict[str, Any]:
    """Build a safe summary of the orchestration request."""

    validated_request = validate_live_evidence_research_pack_orchestration_request(
        request
    )
    components = validated_request["components"]
    return {
        "schema_version": validated_request["schema_version"],
        "stock_code": validated_request["stock_code"],
        "ts_code": validated_request["ts_code"],
        "company_name_hint": validated_request["company_name_hint"],
        "requested_output": validated_request["requested_output"],
        "allow_network": False,
        "component_keys_present": sorted(components.keys()),
        "not_for_trading_advice": True,
    }


def build_source_component_summary(request: Mapping[str, Any]) -> dict[str, Any]:
    """Summarize supplied components by key and schema version only."""

    validated_request = validate_live_evidence_research_pack_orchestration_request(
        request
    )
    components = validated_request["components"]
    summary = {
        "component_keys_present": sorted(components.keys()),
        "required_component_keys": list(REQUIRED_COMPONENT_KEYS),
        "optional_component_keys_allowed": list(OPTIONAL_COMPONENT_KEYS),
        "optional_component_keys_present": [
            key for key in OPTIONAL_COMPONENT_KEYS if key in components
        ],
        "component_schema_versions": {
            key: value.get("schema_version")
            for key, value in components.items()
            if isinstance(value, Mapping)
        },
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }
    return _validate_source_component_summary(summary)


def assert_no_live_evidence_orchestration_forbidden_markers(value: Any) -> None:
    """Reject blocked markers in nested orchestration keys and values."""

    finding = _find_forbidden_marker(value)
    if finding:
        raise LiveEvidenceResearchPackOrchestrationEntryError(
            f"live evidence orchestration safety violation: forbidden marker: {finding}"
        )
    try:
        assert_no_live_research_pack_forbidden_markers(value)
    except ValueError as exc:
        raise LiveEvidenceResearchPackOrchestrationEntryError(
            _safe_error_message(exc)
        ) from exc


def _build_blocked_result(
    request: Mapping[str, Any],
    readiness: Mapping[str, Any],
    blocked_reasons: Iterable[str],
) -> dict[str, Any]:
    return {
        "schema_version": LIVE_EVIDENCE_RESEARCH_PACK_ORCHESTRATION_RESULT_SCHEMA_VERSION,
        "request_summary": build_request_summary(request),
        "readiness": readiness,
        "vertical_slice": None,
        "markdown_preview": "",
        "evidence_status_rollup": None,
        "source_component_summary": build_source_component_summary(request),
        "blocked_reasons": _dedupe_preserve_order(blocked_reasons),
        "caveats": _result_caveats(),
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }


def _blocked_reasons_from_readiness(readiness: Mapping[str, Any]) -> list[str]:
    reasons = [
        f"missing_required_component:{component}"
        for component in readiness.get("missing_required_components", [])
    ]
    reasons.extend(str(error) for error in readiness.get("validation_errors", []))
    return _dedupe_preserve_order(reasons)


def _identity_consistency_errors(
    request: Mapping[str, Any],
    vertical_slice: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    for key in ("stock_code", "ts_code"):
        request_value = _normalized_identity(request.get(key))
        slice_value = _normalized_identity(vertical_slice.get(key))
        if request_value and slice_value and request_value != slice_value:
            errors.append(f"{key}_mismatch")

    request_name = _normalized_identity(request.get("company_name_hint"))
    slice_name = _normalized_identity(vertical_slice.get("company_name_hint"))
    if request_name and slice_name and request_name.casefold() != slice_name.casefold():
        errors.append("company_name_hint_mismatch")
    return errors


def _validate_readiness(value: Any) -> dict[str, Any]:
    readiness = _require_mapping(value, "readiness")
    _require_fields(readiness, _READINESS_REQUIRED_FIELDS, "readiness")
    result = deepcopy(dict(readiness))
    if result["schema_version"] != (
        LIVE_EVIDENCE_RESEARCH_PACK_ORCHESTRATION_READINESS_SCHEMA_VERSION
    ):
        raise LiveEvidenceResearchPackOrchestrationEntryError(
            "readiness schema_version is invalid"
        )
    if result["status"] not in {
        ORCHESTRATION_READINESS_READY,
        ORCHESTRATION_READINESS_BLOCKED,
    }:
        raise LiveEvidenceResearchPackOrchestrationEntryError(
            "readiness.status is invalid"
        )
    _require_string_list(
        result["required_components_present"],
        "readiness.required_components_present",
    )
    _require_string_list(
        result["optional_components_present"],
        "readiness.optional_components_present",
    )
    _require_string_list(
        result["missing_required_components"],
        "readiness.missing_required_components",
    )
    _require_string_list(result["validation_errors"], "readiness.validation_errors")
    _require_bool(result["has_vertical_slice"], "readiness.has_vertical_slice")
    _require_bool(result["has_markdown_preview"], "readiness.has_markdown_preview")
    _require_false(
        result["has_formal_research_report"],
        "readiness.has_formal_research_report",
    )
    _require_false(result["has_trading_advice"], "readiness.has_trading_advice")
    _require_true(result["not_for_trading_advice"], "readiness.not_for_trading_advice")
    if result["status"] == ORCHESTRATION_READINESS_READY:
        if result["missing_required_components"] or result["validation_errors"]:
            raise LiveEvidenceResearchPackOrchestrationEntryError(
                "ready readiness cannot include missing components or validation errors"
            )
        if not result["has_vertical_slice"] or not result["has_markdown_preview"]:
            raise LiveEvidenceResearchPackOrchestrationEntryError(
                "ready readiness requires vertical slice and markdown preview"
            )
    return result


def _validate_source_component_summary(value: Any) -> dict[str, Any]:
    summary = _require_mapping(value, "source_component_summary")
    _require_fields(
        summary,
        _SOURCE_COMPONENT_SUMMARY_REQUIRED_FIELDS,
        "source_component_summary",
    )
    result = deepcopy(dict(summary))
    _require_string_list(
        result["component_keys_present"],
        "source_component_summary.component_keys_present",
    )
    _require_string_list(
        result["required_component_keys"],
        "source_component_summary.required_component_keys",
    )
    _require_string_list(
        result["optional_component_keys_allowed"],
        "source_component_summary.optional_component_keys_allowed",
    )
    _require_string_list(
        result["optional_component_keys_present"],
        "source_component_summary.optional_component_keys_present",
    )
    _require_mapping(
        result["component_schema_versions"],
        "source_component_summary.component_schema_versions",
    )
    _require_true(
        result["not_official_verified"],
        "source_component_summary.not_official_verified",
    )
    _require_true(
        result["not_for_trading_advice"],
        "source_component_summary.not_for_trading_advice",
    )
    return result


def _result_caveats() -> list[str]:
    return [
        "Orchestration uses explicit validated components only.",
        "The returned preview is copied from the vertical slice.",
        "No external data call or artifact write is performed.",
    ]


def _reject_raw_request_keys(value: Mapping[str, Any]) -> None:
    raw_keys = sorted(key for key in _RAW_REQUEST_KEYS if key in value)
    if raw_keys:
        raise LiveEvidenceResearchPackOrchestrationEntryError(
            f"request contains raw inputs: {raw_keys}"
        )


def _reject_raw_component_keys(value: Mapping[str, Any]) -> None:
    raw_keys = sorted(key for key in _RAW_COMPONENT_KEYS if key in value)
    if raw_keys:
        raise LiveEvidenceResearchPackOrchestrationEntryError(
            f"components contains raw inputs: {raw_keys}"
        )


def _reject_bytes(value: Any, path: str) -> None:
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise LiveEvidenceResearchPackOrchestrationEntryError(
            f"{path} contains raw bytes"
        )
    if isinstance(value, Mapping):
        for key, child in value.items():
            _reject_bytes(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_bytes(child, f"{path}[{index}]")


def _find_forbidden_marker(value: Any, *, allow_evidence_status: bool = False) -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text not in _ALLOWED_EXACT_KEYS:
                key_finding = _text_forbidden_marker(
                    key_text,
                    allow_evidence_status=False,
                )
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
        return _text_forbidden_marker(
            value,
            allow_evidence_status=allow_evidence_status,
        )
    return None


def _text_forbidden_marker(value: str, *, allow_evidence_status: bool) -> str | None:
    if value in _CONTROLLED_ALLOWED_TEXTS:
        return None
    searchable_value = value
    for allowed_text in _CONTROLLED_ALLOWED_TEXTS:
        searchable_value = searchable_value.replace(allowed_text, "")
    if allow_evidence_status and value in _EVIDENCE_STATUS_VALUES:
        return None
    if value in _EVIDENCE_STATUS_VALUES and value != "official_verified":
        return None

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


def _normalized_identity(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def _optional_string(value: Any, path: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise LiveEvidenceResearchPackOrchestrationEntryError(
            f"{path} must be a string or null"
        )
    return value


def _safe_error_message(error: Exception) -> str:
    message = str(error)
    return message if len(message) <= 240 else message[:237] + "..."


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
        raise LiveEvidenceResearchPackOrchestrationEntryError(
            f"{field} must be a mapping"
        )
    return value


def _require_fields(value: Mapping[str, Any], fields: tuple[str, ...], path: str) -> None:
    missing = [field for field in fields if field not in value]
    if missing:
        raise LiveEvidenceResearchPackOrchestrationEntryError(
            f"{path} missing required fields: {missing}"
        )


def _require_non_empty_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LiveEvidenceResearchPackOrchestrationEntryError(
            f"{path} must be a non-empty string"
        )
    return value


def _require_string_list(value: Any, path: str) -> list[str]:
    if not isinstance(value, list):
        raise LiveEvidenceResearchPackOrchestrationEntryError(
            f"{path} must be a list"
        )
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise LiveEvidenceResearchPackOrchestrationEntryError(
                f"{path}[{index}] must be a string"
            )
    return value


def _require_true(value: Any, path: str) -> None:
    if value is not True:
        raise LiveEvidenceResearchPackOrchestrationEntryError(f"{path} must be true")


def _require_false(value: Any, path: str) -> None:
    if value is not False:
        raise LiveEvidenceResearchPackOrchestrationEntryError(f"{path} must be false")


def _require_bool(value: Any, path: str) -> None:
    if not isinstance(value, bool):
        raise LiveEvidenceResearchPackOrchestrationEntryError(f"{path} must be bool")


__all__ = [
    "LIVE_EVIDENCE_RESEARCH_PACK_ORCHESTRATION_READINESS_SCHEMA_VERSION",
    "LIVE_EVIDENCE_RESEARCH_PACK_ORCHESTRATION_REQUEST_SCHEMA_VERSION",
    "LIVE_EVIDENCE_RESEARCH_PACK_ORCHESTRATION_RESULT_SCHEMA_VERSION",
    "OPTIONAL_COMPONENT_KEYS",
    "ORCHESTRATION_READINESS_BLOCKED",
    "ORCHESTRATION_READINESS_READY",
    "REQUESTED_OUTPUT_VERTICAL_SLICE_AND_MARKDOWN_PREVIEW",
    "REQUIRED_COMPONENT_KEYS",
    "LiveEvidenceResearchPackOrchestrationEntryError",
    "assert_no_live_evidence_orchestration_forbidden_markers",
    "build_live_evidence_research_pack_orchestration_result",
    "build_orchestration_readiness",
    "build_request_summary",
    "build_source_component_summary",
    "validate_live_evidence_research_pack_orchestration_request",
    "validate_live_evidence_research_pack_orchestration_result",
]
