# -*- coding: utf-8 -*-
"""Injected fake metadata client for live discovery readiness tests."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urlparse, urlunsplit

from .official_disclosure_request import validate_official_disclosure_request
from .official_source_discovery_adapter import discover_official_sources_from_metadata
from .validators import OfficialVerificationValidationError


SCHEMA_VERSION = "live_network_discovery_client_result.v1"
CLIENT_MODE_INJECTED_FAKE = "injected_fake"

SOURCE_FAMILY_CNINFO = "cninfo"
SOURCE_FAMILY_SSE = "sse"
SOURCE_FAMILY_SZSE = "szse"
SOURCE_FAMILY_BSE = "bse"
ALLOWED_SOURCE_FAMILIES = (
    SOURCE_FAMILY_CNINFO,
    SOURCE_FAMILY_SSE,
    SOURCE_FAMILY_SZSE,
    SOURCE_FAMILY_BSE,
)

SOURCE_TYPE_CNINFO_OFFICIAL_PDF = "cninfo_official_pdf"
SOURCE_TYPE_SSE_EXCHANGE_ANNOUNCEMENT = "sse_exchange_announcement"
SOURCE_TYPE_EXCHANGE_OFFICIAL_PDF = "exchange_official_pdf"

ALLOWED_HOSTS_BY_SOURCE_FAMILY = {
    SOURCE_FAMILY_CNINFO: ("www.cninfo.com.cn", "static.cninfo.com.cn"),
    SOURCE_FAMILY_SSE: ("www.sse.com.cn",),
    SOURCE_FAMILY_SZSE: ("www.szse.cn",),
    SOURCE_FAMILY_BSE: ("www.bse.cn",),
}

SOURCE_FAMILY_BY_SOURCE_TYPE = {
    SOURCE_TYPE_CNINFO_OFFICIAL_PDF: (SOURCE_FAMILY_CNINFO,),
    SOURCE_TYPE_SSE_EXCHANGE_ANNOUNCEMENT: (SOURCE_FAMILY_SSE,),
    SOURCE_TYPE_EXCHANGE_OFFICIAL_PDF: (
        SOURCE_FAMILY_CNINFO,
        SOURCE_FAMILY_SSE,
        SOURCE_FAMILY_SZSE,
        SOURCE_FAMILY_BSE,
    ),
}

DEFAULT_SOURCE_TYPE_BY_SOURCE_FAMILY = {
    SOURCE_FAMILY_CNINFO: SOURCE_TYPE_CNINFO_OFFICIAL_PDF,
    SOURCE_FAMILY_SSE: SOURCE_TYPE_SSE_EXCHANGE_ANNOUNCEMENT,
    SOURCE_FAMILY_SZSE: SOURCE_TYPE_EXCHANGE_OFFICIAL_PDF,
    SOURCE_FAMILY_BSE: SOURCE_TYPE_EXCHANGE_OFFICIAL_PDF,
}

DISCOVERY_METHOD_BY_SOURCE_FAMILY = {
    SOURCE_FAMILY_CNINFO: "cninfo_search_result",
    SOURCE_FAMILY_SSE: "sse_announcement_list",
    SOURCE_FAMILY_SZSE: "exchange_announcement_list",
    SOURCE_FAMILY_BSE: "exchange_announcement_list",
}

ALLOWED_CONTENT_TYPES = ("application/json", "text/html")
BLOCKED_CONTENT_TYPES = (
    "text/plain",
    "application/pdf",
    "application/octet-stream",
    "application/zip",
    "application/x-zip-compressed",
    "application/x-rar-compressed",
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
)
BLOCKED_BINARY_SUFFIXES = (
    ".pdf",
    ".zip",
    ".rar",
    ".7z",
    ".tar",
    ".gz",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".bin",
    ".exe",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
)
MAX_REDIRECT_CHAIN_LENGTH = 3
DEFAULT_DISCOVERED_AT_UTC = "1970-01-01T00:00:00Z"

ERROR_TRANSPORT_ERROR = "transport_error"
ERROR_TIMEOUT = "timeout"
ERROR_RATE_LIMITED = "rate_limited"
ERROR_RETRY_EXHAUSTED = "retry_exhausted"
ERROR_REDIRECT_REJECTED = "redirect_rejected"
ERROR_DOMAIN_REJECTED = "domain_rejected"
ERROR_CONTENT_TYPE_REJECTED = "content_type_rejected"
ERROR_MALFORMED_RESPONSE = "malformed_response"
ERROR_EMPTY_RESULT = "empty_result"
ERROR_POLICY_REJECTED = "policy_rejected"
ERROR_INVALID_REQUEST = "invalid_request"
ERROR_NOT_FOR_TRADING_ADVICE_INVALID = "not_for_trading_advice_invalid"

SUPPORTED_ERROR_CODES = {
    ERROR_TRANSPORT_ERROR,
    ERROR_TIMEOUT,
    ERROR_RATE_LIMITED,
    ERROR_RETRY_EXHAUSTED,
    ERROR_REDIRECT_REJECTED,
    ERROR_DOMAIN_REJECTED,
    ERROR_CONTENT_TYPE_REJECTED,
    ERROR_MALFORMED_RESPONSE,
    ERROR_EMPTY_RESULT,
    ERROR_POLICY_REJECTED,
    ERROR_INVALID_REQUEST,
    ERROR_NOT_FOR_TRADING_ADVICE_INVALID,
}

REASON_MISSING_REQUEST = "missing_request"
REASON_INVALID_REQUEST = "invalid_request"
REASON_REQUEST_BLOCKED = "request_blocked"
REASON_CLIENT_MODE_BLOCKED = "client_mode_blocked"
REASON_FAKE_RESPONSES_MISSING = "fake_responses_missing"
REASON_FAKE_RESPONSES_NOT_LIST = "fake_responses_not_list"
REASON_EMPTY_RESULT = "empty_result"
REASON_FAKE_RESPONSE_NOT_MAPPING = "fake_response_not_mapping"
REASON_UNSUPPORTED_SOURCE_FAMILY = "unsupported_source_family"
REASON_SOURCE_TYPE_MISMATCH = "source_type_mismatch"
REASON_DOMAIN_REJECTED = "domain_rejected"
REASON_REDIRECT_REJECTED = "redirect_rejected"
REASON_CONTENT_TYPE_REJECTED = "content_type_rejected"
REASON_MALFORMED_RESPONSE = "malformed_response"
REASON_POLICY_REJECTED = "policy_rejected"
REASON_NOT_FOR_TRADING_ADVICE_INVALID = "not_for_trading_advice_invalid"
REASON_ADAPTER_HANDOFF_REJECTED = "adapter_handoff_rejected"
REASON_NO_NORMALIZED_METADATA_RECORDS = "no_normalized_metadata_records"

FAKE_RESPONSE_FIELDS = (
    "source_family",
    "source_domain",
    "normalized_url",
    "source_url",
    "source_title",
    "disclosure_date",
    "stock_code",
    "exchange",
    "company_name_hint",
    "period_key",
    "period_end_date",
    "announcement_type",
    "source_type",
    "content_type",
    "artifact_kind",
    "is_downloaded",
    "discovery_status",
    "freshness_status",
    "policy_decisions",
    "error_code",
    "error_message",
    "redirect_chain",
    "not_for_trading_advice",
)

RESULT_LIST_FIELDS = (
    "input_fake_responses",
    "normalized_metadata_records",
    "blocked_reasons",
    "policy_decisions",
    "errors",
    "caveats",
)
FINAL_RESULT_SAFETY_SCAN_FIELDS = (
    "request",
    "typed_metadata_query",
    "input_fake_responses",
    "normalized_metadata_records",
    "discovery_adapter_result",
    "blocked_reasons",
    "policy_decisions",
    "errors",
    "caveats",
)

FORBIDDEN_RESULT_FIELDS = {
    "file_content",
    "pdf_bytes",
    "pdf_content",
    "pdf_text",
    "extracted_table",
    "extracted_tables",
    "table_extraction",
    "metrics",
    "metric",
    "local_cache_path",
    "downloaded_file_sha256",
    "file_sha256",
    "output_path",
    "fixture_path",
    "accepted_manifest_path",
    "accepted_manifest",
    "output_baseline",
    "fixture_payload",
    "registry_entry",
    "locator_result",
    "verified_fact",
    "official_metric_fact",
    "provider_official_conflict",
    "report_v1",
}

FORBIDDEN_INPUT_FIELDS = FORBIDDEN_RESULT_FIELDS | {
    "provider_endpoint",
    "provider_lookup",
    "provider_lookup_attempt",
    "akshare_call",
    "tushare_call",
    "download_url",
    "download_attempt",
    "parse_pdf",
    "parser_attempt",
    "pdf_parser",
    "table_extractor",
    "metric_extraction",
    "manifest_write",
    "fixture_write",
    "output_write",
    "token_read",
    "env_read",
}

FORBIDDEN_ENGLISH_MARKERS = (
    "token",
    ".env",
    "tushare_token",
    "provider live",
    "provider lookup",
    "provider_lookup",
    "AkShare",
    "Tushare",
    "network",
    "HTTP",
    "fetch",
    "download",
    "CNInfo live",
    "SSE live",
    "PDF parser",
    "table extractor",
    "parse PDF",
    "parse_pdf",
    "metric extraction",
    "metric_extraction",
    "official_metric_fact",
    "provider_official_conflict",
    "Report V1",
    "accepted manifest write",
    "accepted_manifest_write",
    "output baseline write",
    "output_baseline_write",
    "fixture write",
    "fixture_write",
    "buy",
    "sell",
    "hold",
    "target price",
    "portfolio",
    "position",
    "technical signal",
    "trading advice",
    "investment advice",
)

FORBIDDEN_CJK_MARKERS = (
    "\u4e70\u5165",
    "\u5356\u51fa",
    "\u6301\u6709",
    "\u76ee\u6807\u4ef7",
    "\u4ed3\u4f4d",
    "\u7ec4\u5408",
    "\u6280\u672f\u4fe1\u53f7",
    "\u6295\u8d44\u5efa\u8bae",
    "\u4e0b\u8f7d",
    "\u7f51\u7edc",
    "\u8054\u7f51",
    "\u89e3\u6790PDF",
    "PDF\u89e3\u6790",
    "\u8868\u683c\u62bd\u53d6",
    "\u6307\u6807\u62bd\u53d6",
    "\u6b63\u5f0f\u7814\u62a5",
    "\u8f93\u51fa\u57fa\u7ebf",
    "\u5199\u5165fixture",
    "\u5199\u5165accepted manifest",
    "\u8bfb\u53d6token",
    "\u8bfb\u53d6.env",
    "\u8bfb\u53d6tushare_token",
    "\u8c03\u7528AkShare",
    "\u8c03\u7528Tushare",
    "\u8c03\u7528CNInfo live",
    "\u8c03\u7528SSE live",
    "\u8c03\u7528provider",
)

SHORT_WORD_MARKERS = {
    "buy",
    "sell",
    "hold",
    "http",
    "fetch",
    "network",
    "download",
    "portfolio",
    "position",
    "token",
}

_CAMEL_SPLIT_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_HOST_RE = re.compile(r"^[a-z0-9.-]+$")


def discover_live_network_metadata_with_injected_fake_client(
    request: Any,
    fake_responses: Any,
    *,
    client_mode: str = CLIENT_MODE_INJECTED_FAKE,
) -> dict[str, Any]:
    """Normalize explicit fake metadata responses and hand valid records to the adapter."""

    policy_decisions = [
        _policy_decision("client_mode_policy", "injected_fake_only", "allow"),
        _policy_decision("io_policy", "explicit_payload_only", "allow"),
    ]
    request_snapshot, request_reasons = _validate_request_for_client(request)
    input_snapshot = _safe_fake_responses_snapshot(fake_responses)

    if client_mode != CLIENT_MODE_INJECTED_FAKE:
        return _build_result(
            request=request_snapshot,
            typed_metadata_query={},
            input_fake_responses=input_snapshot,
            normalized_metadata_records=[],
            discovery_adapter_result={},
            blocked_reasons=[REASON_CLIENT_MODE_BLOCKED],
            policy_decisions=policy_decisions
            + [_policy_decision("client_mode_policy", REASON_CLIENT_MODE_BLOCKED, "block")],
            errors=[
                _build_error(
                    ERROR_POLICY_REJECTED,
                    REASON_CLIENT_MODE_BLOCKED,
                    error_message="unsupported_client_mode",
                )
            ],
            caveats=[],
        )

    if request_reasons:
        reason = request_reasons[0]
        return _build_result(
            request=request_snapshot,
            typed_metadata_query={},
            input_fake_responses=input_snapshot,
            normalized_metadata_records=[],
            discovery_adapter_result={},
            blocked_reasons=request_reasons,
            policy_decisions=policy_decisions
            + [_policy_decision("request_policy", reason, "block")],
            errors=[_build_error(ERROR_INVALID_REQUEST, reason)],
            caveats=[],
        )

    typed_metadata_query = build_typed_metadata_query(request_snapshot)

    if fake_responses is None:
        return _build_result(
            request=request_snapshot,
            typed_metadata_query=typed_metadata_query,
            input_fake_responses=[],
            normalized_metadata_records=[],
            discovery_adapter_result=discover_official_sources_from_metadata(request_snapshot, []),
            blocked_reasons=[REASON_FAKE_RESPONSES_MISSING, REASON_EMPTY_RESULT],
            policy_decisions=policy_decisions
            + [_policy_decision("fake_response_policy", REASON_FAKE_RESPONSES_MISSING, "block")],
            errors=[_build_error(ERROR_EMPTY_RESULT, REASON_FAKE_RESPONSES_MISSING)],
            caveats=[],
        )

    if not isinstance(fake_responses, list):
        return _build_result(
            request=request_snapshot,
            typed_metadata_query=typed_metadata_query,
            input_fake_responses=[],
            normalized_metadata_records=[],
            discovery_adapter_result=discover_official_sources_from_metadata(request_snapshot, []),
            blocked_reasons=[REASON_FAKE_RESPONSES_NOT_LIST, REASON_MALFORMED_RESPONSE],
            policy_decisions=policy_decisions
            + [_policy_decision("fake_response_policy", REASON_FAKE_RESPONSES_NOT_LIST, "block")],
            errors=[_build_error(ERROR_MALFORMED_RESPONSE, REASON_FAKE_RESPONSES_NOT_LIST)],
            caveats=[],
        )

    if not fake_responses:
        return _build_result(
            request=request_snapshot,
            typed_metadata_query=typed_metadata_query,
            input_fake_responses=[],
            normalized_metadata_records=[],
            discovery_adapter_result=discover_official_sources_from_metadata(request_snapshot, []),
            blocked_reasons=[REASON_EMPTY_RESULT],
            policy_decisions=policy_decisions
            + [_policy_decision("fake_response_policy", REASON_EMPTY_RESULT, "block")],
            errors=[_build_error(ERROR_EMPTY_RESULT, REASON_EMPTY_RESULT)],
            caveats=[],
        )

    normalized_records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    blocked_reasons: list[str] = []

    for record_index, fake_response in enumerate(fake_responses):
        normalized_record, record_errors, record_decisions = _normalize_fake_response(
            request_snapshot,
            typed_metadata_query,
            fake_response,
            record_index=record_index,
        )
        policy_decisions.extend(record_decisions)
        if record_errors:
            errors.extend(record_errors)
            blocked_reasons.extend(error["reason"] for error in record_errors if error.get("reason"))
            continue
        if normalized_record:
            normalized_records.append(normalized_record)

    if normalized_records:
        discovery_adapter_result = _handoff_to_discovery_adapter(request_snapshot, normalized_records)
        policy_decisions.append(_policy_decision("adapter_handoff_policy", "qualified_metadata_records", "allow"))
        adapter_blocked = discovery_adapter_result.get("blocked_reasons", [])
        if isinstance(adapter_blocked, list) and adapter_blocked:
            blocked_reasons.append(REASON_ADAPTER_HANDOFF_REJECTED)
            blocked_reasons.extend(_clean_string(reason) for reason in adapter_blocked if _clean_string(reason))
    else:
        discovery_adapter_result = discover_official_sources_from_metadata(request_snapshot, [])
        if not blocked_reasons:
            blocked_reasons.append(REASON_NO_NORMALIZED_METADATA_RECORDS)

    if errors and not blocked_reasons:
        blocked_reasons.append(REASON_POLICY_REJECTED)

    return _build_result(
        request=request_snapshot,
        typed_metadata_query=typed_metadata_query,
        input_fake_responses=input_snapshot,
        normalized_metadata_records=normalized_records,
        discovery_adapter_result=discovery_adapter_result,
        blocked_reasons=blocked_reasons,
        policy_decisions=policy_decisions,
        errors=errors,
        caveats=[],
    )


def build_typed_metadata_query(request: Any) -> dict[str, Any]:
    """Derive a metadata-only query object from a valid disclosure request."""

    request_snapshot, request_reasons = _validate_request_for_client(request)
    if request_reasons:
        return {}

    allowed_source_types = list(request_snapshot.get("allowed_source_types", []))
    allowed_source_families = _allowed_source_families_for_types(allowed_source_types)
    allowed_domains = _allowed_domains_for_families(allowed_source_families)

    query = {
        "request_id": _clean_string(request_snapshot.get("request_id")),
        "stock_code": _clean_string(request_snapshot.get("stock_code")),
        "exchange": _clean_string(request_snapshot.get("exchange")),
        "query_period": _clean_string(request_snapshot.get("query_period")),
        "period_end_date": _clean_string(request_snapshot.get("period_end_date")),
        "requested_announcement_type": _clean_string(
            request_snapshot.get("requested_announcement_type")
        ),
        "allowed_source_types": allowed_source_types,
        "allowed_source_families": allowed_source_families,
        "allowed_domains": allowed_domains,
        "metadata_only": True,
        "not_for_trading_advice": True,
    }
    _assert_no_forbidden_result_fields(query, path="$.typed_metadata_query")
    return query


def validate_live_network_discovery_client_result(result: Any) -> None:
    """Validate the injected-fake client result without touching external state."""

    if not isinstance(result, Mapping):
        raise OfficialVerificationValidationError("live client result must be a mapping")
    required = (
        "schema_version",
        "request",
        "typed_metadata_query",
        "client_mode",
        "input_fake_responses",
        "normalized_metadata_records",
        "discovery_adapter_result",
        "blocked_reasons",
        "policy_decisions",
        "errors",
        "caveats",
        "not_for_trading_advice",
    )
    missing = [key for key in required if key not in result]
    if missing:
        raise OfficialVerificationValidationError(f"live client result missing keys: {missing}")
    if result["schema_version"] != SCHEMA_VERSION:
        raise OfficialVerificationValidationError("live client result schema_version is unsupported")
    if result["client_mode"] != CLIENT_MODE_INJECTED_FAKE:
        raise OfficialVerificationValidationError("client_mode must be injected_fake")
    if result.get("not_for_trading_advice") is not True:
        raise OfficialVerificationValidationError("not_for_trading_advice must be true")
    if not isinstance(result.get("request"), Mapping):
        raise OfficialVerificationValidationError("request must be a mapping")
    if not isinstance(result.get("typed_metadata_query"), Mapping):
        raise OfficialVerificationValidationError("typed_metadata_query must be a mapping")
    if not isinstance(result.get("discovery_adapter_result"), Mapping):
        raise OfficialVerificationValidationError("discovery_adapter_result must be a mapping")
    for field in RESULT_LIST_FIELDS:
        if not isinstance(result.get(field), list):
            raise OfficialVerificationValidationError(f"{field} must be a list")
    for error in result["errors"]:
        if not isinstance(error, Mapping):
            raise OfficialVerificationValidationError("errors must contain mappings")
        if error.get("error_code") not in SUPPORTED_ERROR_CODES:
            raise OfficialVerificationValidationError("unsupported live client error_code")
        if not error.get("reason"):
            raise OfficialVerificationValidationError("live client error requires reason")
    if (result["errors"] or not result["normalized_metadata_records"]) and not result["blocked_reasons"]:
        raise OfficialVerificationValidationError("blocked, error, or empty result requires blocked_reasons")

    _assert_no_forbidden_result_fields(result, path="$")
    _assert_final_result_envelope_has_no_forbidden_markers(result)


def _normalize_fake_response(
    request: Mapping[str, Any],
    typed_metadata_query: Mapping[str, Any],
    fake_response: Any,
    *,
    record_index: int,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[dict[str, Any]]]:
    decisions: list[dict[str, Any]] = []

    if not isinstance(fake_response, Mapping):
        return (
            None,
            [_build_error(ERROR_MALFORMED_RESPONSE, REASON_FAKE_RESPONSE_NOT_MAPPING, record_index=record_index)],
            [_policy_decision("fake_response_policy", REASON_FAKE_RESPONSE_NOT_MAPPING, "block", record_index)],
        )

    try:
        _assert_no_forbidden_input_fields(fake_response, path="$")
        _assert_no_forbidden_markers(fake_response, path="$")
    except OfficialVerificationValidationError:
        return (
            None,
            [_build_error(ERROR_POLICY_REJECTED, REASON_POLICY_REJECTED, record_index=record_index)],
            [_policy_decision("safety_marker_policy", REASON_POLICY_REJECTED, "block", record_index)],
        )

    if fake_response.get("not_for_trading_advice") is not True:
        return (
            None,
            [
                _build_error(
                    ERROR_NOT_FOR_TRADING_ADVICE_INVALID,
                    REASON_NOT_FOR_TRADING_ADVICE_INVALID,
                    record_index=record_index,
                )
            ],
            [_policy_decision("advice_flag_policy", REASON_NOT_FOR_TRADING_ADVICE_INVALID, "block", record_index)],
        )

    explicit_error = _explicit_error_from_fake_response(fake_response, record_index=record_index)
    if explicit_error is not None:
        return (
            None,
            [explicit_error],
            [_policy_decision("explicit_error_policy", explicit_error["reason"], "block", record_index)],
        )

    if fake_response.get("is_downloaded") is True:
        return (
            None,
            [_build_error(ERROR_POLICY_REJECTED, REASON_POLICY_REJECTED, record_index=record_index)],
            [_policy_decision("artifact_policy", REASON_POLICY_REJECTED, "block", record_index)],
        )

    source_family = _clean_string(fake_response.get("source_family")).lower()
    if source_family not in ALLOWED_SOURCE_FAMILIES:
        return (
            None,
            [_build_error(ERROR_POLICY_REJECTED, REASON_UNSUPPORTED_SOURCE_FAMILY, record_index=record_index)],
            [_policy_decision("source_family_policy", REASON_UNSUPPORTED_SOURCE_FAMILY, "block", record_index)],
        )

    source_type = _clean_string(fake_response.get("source_type")) or DEFAULT_SOURCE_TYPE_BY_SOURCE_FAMILY[source_family]
    if source_type != DEFAULT_SOURCE_TYPE_BY_SOURCE_FAMILY[source_family]:
        return (
            None,
            [_build_error(ERROR_POLICY_REJECTED, REASON_SOURCE_TYPE_MISMATCH, record_index=record_index)],
            [_policy_decision("source_type_policy", REASON_SOURCE_TYPE_MISMATCH, "block", record_index)],
        )

    required_error = _required_fake_metadata_error(fake_response)
    if required_error:
        return (
            None,
            [_build_error(ERROR_MALFORMED_RESPONSE, required_error, record_index=record_index)],
            [_policy_decision("metadata_shape_policy", required_error, "block", record_index)],
        )

    source_url = _clean_string(fake_response.get("source_url")) or _clean_string(fake_response.get("normalized_url"))
    parsed_source_url = _parse_url(source_url)
    if parsed_source_url is None:
        return (
            None,
            [_build_error(ERROR_DOMAIN_REJECTED, REASON_DOMAIN_REJECTED, record_index=record_index)],
            [_policy_decision("domain_allowlist_policy", REASON_DOMAIN_REJECTED, "block", record_index)],
        )

    host = parsed_source_url["host"]
    if host not in ALLOWED_HOSTS_BY_SOURCE_FAMILY[source_family]:
        return (
            None,
            [_build_error(ERROR_DOMAIN_REJECTED, REASON_DOMAIN_REJECTED, record_index=record_index)],
            [_policy_decision("domain_allowlist_policy", REASON_DOMAIN_REJECTED, "block", record_index)],
        )

    source_domain = _normalize_host_value(fake_response.get("source_domain")) or host
    if source_domain != host:
        return (
            None,
            [_build_error(ERROR_DOMAIN_REJECTED, REASON_DOMAIN_REJECTED, record_index=record_index)],
            [_policy_decision("domain_allowlist_policy", REASON_DOMAIN_REJECTED, "block", record_index)],
        )
    decisions.append(_policy_decision("domain_allowlist_policy", "exact_host_allowed", "allow", record_index))

    redirect_chain, redirect_error = _normalize_redirect_chain(
        fake_response.get("redirect_chain"),
        source_family=source_family,
    )
    if redirect_error:
        return (
            None,
            [_build_error(ERROR_REDIRECT_REJECTED, redirect_error, record_index=record_index)],
            [_policy_decision("redirect_policy", redirect_error, "block", record_index)],
        )
    decisions.append(_policy_decision("redirect_policy", "redirect_metadata_allowed", "allow", record_index))

    content_type = _normalize_content_type(fake_response.get("content_type"))
    content_type_error = _content_type_rejection_reason(content_type, parsed_source_url["path"])
    if content_type_error:
        return (
            None,
            [_build_error(ERROR_CONTENT_TYPE_REJECTED, content_type_error, record_index=record_index)],
            [_policy_decision("content_type_policy", content_type_error, "block", record_index)],
        )
    decisions.append(_policy_decision("content_type_policy", "metadata_content_type_allowed", "allow", record_index))

    mismatch_error = _request_mismatch_error(request, fake_response)
    if mismatch_error:
        return (
            None,
            [_build_error(ERROR_POLICY_REJECTED, mismatch_error, record_index=record_index)],
            [_policy_decision("typed_query_match_policy", mismatch_error, "block", record_index)],
        )

    if source_family not in typed_metadata_query.get("allowed_source_families", []):
        return (
            None,
            [_build_error(ERROR_POLICY_REJECTED, REASON_UNSUPPORTED_SOURCE_FAMILY, record_index=record_index)],
            [_policy_decision("typed_query_match_policy", REASON_UNSUPPORTED_SOURCE_FAMILY, "block", record_index)],
        )

    normalized_record = {
        "source_url": parsed_source_url["url"],
        "source_title": _clean_string(fake_response.get("source_title")),
        "disclosure_date": _clean_string(fake_response.get("disclosure_date")),
        "stock_code": _clean_string(request.get("stock_code")),
        "company_name": _clean_string(fake_response.get("company_name_hint"))
        or _clean_string(request.get("company_name")),
        "exchange": _clean_string(request.get("exchange")),
        "period_key": _clean_string(request.get("query_period")),
        "period_end_date": _clean_string(request.get("period_end_date")),
        "announcement_type": _clean_string(request.get("requested_announcement_type")),
        "source_type": source_type,
        "source_domain": host,
        "discovered_at_utc": _clean_string(fake_response.get("discovered_at_utc")) or DEFAULT_DISCOVERED_AT_UTC,
        "discovery_method": DISCOVERY_METHOD_BY_SOURCE_FAMILY[source_family],
        "redirect_chain": redirect_chain,
        "caveats": ["injected_fake_metadata_record", "metadata_only"],
        "not_for_trading_advice": True,
    }
    decisions.append(_policy_decision("metadata_normalization_policy", "metadata_record_normalized", "allow", record_index))
    return normalized_record, [], decisions


def _explicit_error_from_fake_response(fake_response: Mapping[str, Any], *, record_index: int) -> dict[str, Any] | None:
    error_code = _clean_string(fake_response.get("error_code"))
    if not error_code:
        return None
    if error_code not in SUPPORTED_ERROR_CODES:
        return _build_error(ERROR_MALFORMED_RESPONSE, REASON_MALFORMED_RESPONSE, record_index=record_index)
    reason = {
        ERROR_TRANSPORT_ERROR: ERROR_TRANSPORT_ERROR,
        ERROR_TIMEOUT: ERROR_TIMEOUT,
        ERROR_RATE_LIMITED: ERROR_RATE_LIMITED,
        ERROR_RETRY_EXHAUSTED: ERROR_RETRY_EXHAUSTED,
        ERROR_REDIRECT_REJECTED: REASON_REDIRECT_REJECTED,
        ERROR_DOMAIN_REJECTED: REASON_DOMAIN_REJECTED,
        ERROR_CONTENT_TYPE_REJECTED: REASON_CONTENT_TYPE_REJECTED,
        ERROR_MALFORMED_RESPONSE: REASON_MALFORMED_RESPONSE,
        ERROR_EMPTY_RESULT: REASON_EMPTY_RESULT,
        ERROR_POLICY_REJECTED: REASON_POLICY_REJECTED,
        ERROR_INVALID_REQUEST: REASON_INVALID_REQUEST,
        ERROR_NOT_FOR_TRADING_ADVICE_INVALID: REASON_NOT_FOR_TRADING_ADVICE_INVALID,
    }[error_code]
    return _build_error(
        error_code,
        reason,
        record_index=record_index,
        error_message=_safe_error_message(fake_response.get("error_message")),
    )


def _handoff_to_discovery_adapter(
    request: Mapping[str, Any], normalized_records: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    try:
        return discover_official_sources_from_metadata(request, _adapter_handoff_records(normalized_records))
    except OfficialVerificationValidationError as exc:
        return {
            "schema_version": "official_source_discovery_adapter_result.v1",
            "request": dict(request),
            "input_metadata_records": _adapter_handoff_records(normalized_records),
            "discovery_candidates": [],
            "rejected_records": [],
            "blocked_reasons": [REASON_ADAPTER_HANDOFF_REJECTED, _clean_string(exc)],
            "caveats": [],
            "not_for_trading_advice": True,
        }


def _adapter_handoff_records(normalized_records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for record in normalized_records:
        handoff_record = dict(record)
        handoff_record.pop("redirect_chain", None)
        records.append(handoff_record)
    return records


def _build_result(
    *,
    request: Mapping[str, Any],
    typed_metadata_query: Mapping[str, Any],
    input_fake_responses: Sequence[Mapping[str, Any]],
    normalized_metadata_records: Sequence[Mapping[str, Any]],
    discovery_adapter_result: Mapping[str, Any],
    blocked_reasons: Sequence[str],
    policy_decisions: Sequence[Mapping[str, Any]],
    errors: Sequence[Mapping[str, Any]],
    caveats: Sequence[str],
) -> dict[str, Any]:
    normalized_errors = [dict(error) for error in errors]
    normalized_blocked = _dedupe_preserve_order(
        [_clean_string(reason) for reason in blocked_reasons if _clean_string(reason)]
    )
    if (normalized_errors or not normalized_metadata_records) and not normalized_blocked:
        normalized_blocked = [REASON_NO_NORMALIZED_METADATA_RECORDS]

    result = {
        "schema_version": SCHEMA_VERSION,
        "request": dict(request),
        "typed_metadata_query": dict(typed_metadata_query),
        "client_mode": CLIENT_MODE_INJECTED_FAKE,
        "input_fake_responses": [dict(item) for item in input_fake_responses],
        "normalized_metadata_records": [dict(item) for item in normalized_metadata_records],
        "discovery_adapter_result": dict(discovery_adapter_result),
        "blocked_reasons": normalized_blocked,
        "policy_decisions": [dict(item) for item in policy_decisions],
        "errors": normalized_errors,
        "caveats": [_clean_string(caveat) for caveat in caveats if _clean_string(caveat)],
        "not_for_trading_advice": True,
    }
    validate_live_network_discovery_client_result(result)
    return result


def _validate_request_for_client(request: Any) -> tuple[dict[str, Any], list[str]]:
    if request is None:
        return {}, [REASON_MISSING_REQUEST]
    if not isinstance(request, Mapping):
        return {}, [REASON_INVALID_REQUEST]

    validated = validate_official_disclosure_request(request)
    reasons: list[str] = []
    if validated.get("schema_version") != "official_disclosure_discovery_request.v1":
        reasons.append(REASON_INVALID_REQUEST)
    if validated.get("rejection_reason") not in {None, ""} or validated.get("blocked_reasons"):
        reasons.append(REASON_REQUEST_BLOCKED)
        reasons.extend(
            f"request:{reason}"
            for reason in validated.get("blocked_reasons", [])
            if _clean_string(reason)
        )
    return dict(validated), _dedupe_preserve_order(reasons)


def _allowed_source_families_for_types(source_types: Sequence[Any]) -> list[str]:
    families: list[str] = []
    for source_type in source_types:
        families.extend(SOURCE_FAMILY_BY_SOURCE_TYPE.get(_clean_string(source_type), ()))
    return [family for family in ALLOWED_SOURCE_FAMILIES if family in families]


def _allowed_domains_for_families(source_families: Sequence[str]) -> list[str]:
    domains: list[str] = []
    for family in source_families:
        domains.extend(ALLOWED_HOSTS_BY_SOURCE_FAMILY.get(family, ()))
    return _dedupe_preserve_order(domains)


def _normalize_redirect_chain(value: Any, *, source_family: str) -> tuple[list[str], str | None]:
    if value is None:
        return [], None
    if not isinstance(value, list):
        return [], REASON_REDIRECT_REJECTED
    if len(value) > MAX_REDIRECT_CHAIN_LENGTH:
        return [], REASON_REDIRECT_REJECTED

    normalized: list[str] = []
    for redirect_url in value:
        parsed = _parse_url(redirect_url)
        if parsed is None:
            return [], REASON_REDIRECT_REJECTED
        if parsed["host"] not in ALLOWED_HOSTS_BY_SOURCE_FAMILY[source_family]:
            return [], REASON_REDIRECT_REJECTED
        if _has_blocked_binary_suffix(parsed["path"]):
            return [], REASON_REDIRECT_REJECTED
        normalized.append(parsed["url"])
    return normalized, None


def _content_type_rejection_reason(content_type: str, url_path: str) -> str | None:
    if not content_type:
        return REASON_CONTENT_TYPE_REJECTED
    if content_type not in ALLOWED_CONTENT_TYPES:
        return REASON_CONTENT_TYPE_REJECTED
    if _has_blocked_binary_suffix(url_path):
        return REASON_CONTENT_TYPE_REJECTED
    return None


def _required_fake_metadata_error(fake_response: Mapping[str, Any]) -> str | None:
    for field in ("source_url", "source_title", "disclosure_date"):
        if not _clean_string(fake_response.get(field)):
            return REASON_MALFORMED_RESPONSE
    return None


def _request_mismatch_error(request: Mapping[str, Any], fake_response: Mapping[str, Any]) -> str | None:
    checks = (
        ("stock_code", "stock_code"),
        ("exchange", "exchange"),
        ("period_key", "query_period"),
        ("period_end_date", "period_end_date"),
        ("announcement_type", "requested_announcement_type"),
    )
    for fake_field, request_field in checks:
        fake_value = _clean_string(fake_response.get(fake_field))
        if fake_value and fake_value != _clean_string(request.get(request_field)):
            return REASON_POLICY_REJECTED
    return None


def _parse_url(value: Any) -> dict[str, str] | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    try:
        parsed = urlparse(raw)
        if parsed.port is not None:
            return None
    except ValueError:
        return None
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return None
    if parsed.username or parsed.password or "@" in parsed.netloc:
        return None
    if "%" in parsed.netloc or "\\" in parsed.netloc:
        return None
    host = (parsed.hostname or "").strip().lower().rstrip(".")
    if not _host_is_safe(host):
        return None
    canonical_url = urlunsplit(
        (
            parsed.scheme.lower(),
            host,
            parsed.path,
            parsed.query,
            parsed.fragment,
        )
    )
    return {"url": canonical_url, "host": host, "path": parsed.path or ""}


def _host_is_safe(host: str) -> bool:
    if not host or host.startswith(".") or host.endswith(".") or ".." in host:
        return False
    if not _HOST_RE.fullmatch(host):
        return False
    labels = host.split(".")
    return all(label and not label.startswith("xn--") for label in labels)


def _normalize_host_value(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    if "://" in raw:
        parsed = _parse_url(raw)
        return parsed["host"] if parsed else None
    if any(separator in raw for separator in ("/", "\\", "?", "#", "@", "%", ":")):
        return None
    host = raw.lower().rstrip(".")
    return host if _host_is_safe(host) else None


def _normalize_content_type(value: Any) -> str:
    raw = _clean_string(value).lower()
    if not raw:
        return ""
    return raw.split(";", 1)[0].strip()


def _has_blocked_binary_suffix(path: str) -> bool:
    lowered = _clean_string(path).lower()
    return any(lowered.endswith(suffix) for suffix in BLOCKED_BINARY_SUFFIXES)


def _safe_fake_responses_snapshot(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [_safe_fake_response_snapshot(item, record_index=index) for index, item in enumerate(value)]


def _safe_fake_response_snapshot(record: Any, *, record_index: int) -> dict[str, Any]:
    snapshot: dict[str, Any] = {"record_index": record_index}
    if not isinstance(record, Mapping):
        snapshot["record_omitted"] = True
        snapshot["not_for_trading_advice"] = True
        return snapshot

    for field in FAKE_RESPONSE_FIELDS:
        if field not in record:
            continue
        value = record[field]
        if field in {"source_url", "normalized_url", "redirect_chain"}:
            snapshot[field] = _sanitize_url_value(value)
            continue
        if field == "error_code":
            snapshot[field] = _clean_string(value)
            continue
        if _value_has_forbidden_marker(value):
            snapshot[f"{field}_omitted"] = True
            continue
        snapshot[field] = _copy_jsonlike(value)
    if any(field not in FAKE_RESPONSE_FIELDS for field in record):
        snapshot["extra_fields_omitted"] = True
    return snapshot


def _sanitize_url_value(value: Any) -> Any:
    if isinstance(value, list):
        return [_sanitize_url_value(item) for item in value]
    if not isinstance(value, str):
        return value
    try:
        _assert_url_has_no_secret_marker(value, path="$")
    except OfficialVerificationValidationError:
        return "[omitted_unsafe_url]"
    return value


def _copy_jsonlike(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _copy_jsonlike(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_copy_jsonlike(item) for item in value]
    if isinstance(value, tuple):
        return [_copy_jsonlike(item) for item in value]
    return value


def _build_error(
    error_code: str,
    reason: str,
    *,
    record_index: int | None = None,
    error_message: str = "",
) -> dict[str, Any]:
    error = {
        "error_code": error_code,
        "reason": reason,
        "retryable": error_code in {ERROR_TRANSPORT_ERROR, ERROR_TIMEOUT, ERROR_RATE_LIMITED},
        "not_for_trading_advice": True,
    }
    if record_index is not None:
        error["record_index"] = record_index
    if error_message:
        error["error_message"] = error_message
    return error


def _policy_decision(policy: str, reason: str, decision: str, record_index: int | None = None) -> dict[str, Any]:
    item = {
        "policy": policy,
        "reason": reason,
        "decision": decision,
        "not_for_trading_advice": True,
    }
    if record_index is not None:
        item["record_index"] = record_index
    return item


def _safe_error_message(value: Any) -> str:
    message = _clean_string(value)
    if not message:
        return ""
    try:
        _assert_no_forbidden_markers(message, path="$.error_message")
    except OfficialVerificationValidationError:
        return "omitted_unsafe_message"
    return message


def _assert_no_forbidden_input_fields(value: Any, *, path: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized_key = _normalize_marker_text(key)
            compact_key = normalized_key.replace("_", "")
            for forbidden_field in FORBIDDEN_INPUT_FIELDS:
                normalized_forbidden = _normalize_marker_text(forbidden_field)
                if normalized_key == normalized_forbidden or compact_key == normalized_forbidden.replace("_", ""):
                    raise OfficialVerificationValidationError(f"forbidden live client input field at {path}.{key}")
            _assert_no_forbidden_input_fields(item, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_no_forbidden_input_fields(item, path=f"{path}[{index}]")


def _assert_no_forbidden_result_fields(value: Any, *, path: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized_key = _normalize_marker_text(key)
            compact_key = normalized_key.replace("_", "")
            for forbidden_field in FORBIDDEN_RESULT_FIELDS:
                normalized_forbidden = _normalize_marker_text(forbidden_field)
                if normalized_key == normalized_forbidden or compact_key == normalized_forbidden.replace("_", ""):
                    raise OfficialVerificationValidationError(f"forbidden live client result field at {path}.{key}")
            _assert_no_forbidden_result_fields(item, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_no_forbidden_result_fields(item, path=f"{path}[{index}]")


def _assert_final_result_envelope_has_no_forbidden_markers(result: Mapping[str, Any]) -> None:
    for field in FINAL_RESULT_SAFETY_SCAN_FIELDS:
        _assert_no_forbidden_markers(result.get(field), path=f"$.{field}")


def _assert_no_forbidden_markers(value: Any, *, path: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            normalized_key = _normalize_marker_text(key)
            if key_text != "not_for_trading_advice" and _key_has_forbidden_marker(normalized_key):
                raise OfficialVerificationValidationError(f"forbidden live client marker key at {path}.{key}")
            if key_text in {"source_url", "normalized_url"}:
                _assert_url_has_no_secret_marker(item, path=f"{path}.{key}")
            elif key_text == "redirect_chain":
                _assert_redirect_chain_has_no_secret_marker(item, path=f"{path}.{key}")
            elif key_text == "error_code":
                continue
            else:
                _assert_no_forbidden_markers(item, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_no_forbidden_markers(item, path=f"{path}[{index}]")
    elif isinstance(value, str):
        marker = _string_forbidden_marker(value)
        if marker:
            raise OfficialVerificationValidationError(f"forbidden live client marker value at {path}: {marker}")


def _assert_url_has_no_secret_marker(value: Any, *, path: str) -> None:
    if not isinstance(value, str):
        return
    lowered = value.casefold()
    if "tushare_token" in lowered or ".env" in lowered or re.search(r"\btoken\b", lowered):
        raise OfficialVerificationValidationError(f"forbidden live client URL marker at {path}")


def _assert_redirect_chain_has_no_secret_marker(value: Any, *, path: str) -> None:
    if isinstance(value, list):
        for index, item in enumerate(value):
            _assert_url_has_no_secret_marker(item, path=f"{path}[{index}]")
    else:
        _assert_no_forbidden_markers(value, path=path)


def _value_has_forbidden_marker(value: Any) -> bool:
    try:
        _assert_no_forbidden_markers(value, path="$")
    except OfficialVerificationValidationError:
        return True
    return False


def _key_has_forbidden_marker(normalized_key: str) -> bool:
    compact_key = normalized_key.replace("_", "")
    for marker in FORBIDDEN_ENGLISH_MARKERS:
        normalized_marker = _normalize_marker_text(marker)
        compact_marker = normalized_marker.replace("_", "")
        if normalized_marker == "env":
            if normalized_key == "env" or normalized_key.endswith("_env") or normalized_key.startswith("env_"):
                return True
            continue
        if normalized_marker == "token":
            if "token" in normalized_key.split("_") or normalized_key.endswith("_token") or normalized_key.startswith("token_"):
                return True
            continue
        if normalized_marker in SHORT_WORD_MARKERS:
            if normalized_marker in normalized_key.split("_"):
                return True
            continue
        if normalized_marker and (normalized_marker in normalized_key or compact_marker in compact_key):
            return True
    for marker in FORBIDDEN_CJK_MARKERS:
        if marker in normalized_key:
            return True
    return False


def _string_forbidden_marker(value: str) -> str:
    for marker in FORBIDDEN_CJK_MARKERS:
        if marker in value:
            return marker

    lowered = value.casefold()
    normalized = _normalize_marker_text(value)
    normalized_for_marker_scan = normalized.replace("not_for_trading_advice", "")
    if "tushare_token" in lowered:
        return "tushare_token"
    if ".env" in lowered:
        return ".env"
    if re.search(r"\btoken\b", lowered):
        return "token"
    for marker in FORBIDDEN_ENGLISH_MARKERS:
        marker_norm = _normalize_marker_text(marker)
        if marker_norm in {"token", "env"}:
            continue
        if marker_norm == "http":
            if "http" in normalized.split("_") or re.search(r"(?<![a-z])http(?![a-z])", value, flags=re.IGNORECASE):
                return marker
            continue
        if marker_norm in SHORT_WORD_MARKERS:
            if marker_norm in normalized.split("_") or re.search(rf"\b{re.escape(marker_norm)}\b", lowered):
                return marker
            continue
        if marker_norm and marker_norm in normalized_for_marker_scan:
            return marker
    return ""


def _normalize_marker_text(value: Any) -> str:
    raw = _clean_string(value)
    camel_split = _CAMEL_SPLIT_RE.sub("_", raw)
    lowered = camel_split.casefold()
    lowered = re.sub(r"[\s\-\.]+", "_", lowered)
    lowered = re.sub(r"_+", "_", lowered).strip("_")
    return lowered


def _clean_string(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _dedupe_preserve_order(values: Sequence[Any]) -> list[Any]:
    seen: set[Any] = set()
    deduped: list[Any] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped
