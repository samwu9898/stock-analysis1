# -*- coding: utf-8 -*-
"""No-IO official disclosure discovery request contract helpers."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

from .security_identity import (
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    MARKET_CN_A,
    SCHEMA_VERSION as SECURITY_IDENTITY_SCHEMA_VERSION,
    STATUS_VALID,
    validate_security_identity,
)


SCHEMA_VERSION = "official_disclosure_discovery_request.v1"

ANNOUNCEMENT_TYPE_ANNUAL_REPORT = "annual_report"
ANNOUNCEMENT_TYPE_SEMIANNUAL_REPORT = "semiannual_report"
ANNOUNCEMENT_TYPE_QUARTERLY_REPORT = "quarterly_report"
SUPPORTED_ANNOUNCEMENT_TYPES = {
    ANNOUNCEMENT_TYPE_ANNUAL_REPORT,
    ANNOUNCEMENT_TYPE_SEMIANNUAL_REPORT,
    ANNOUNCEMENT_TYPE_QUARTERLY_REPORT,
}

SOURCE_TYPE_CNINFO_OFFICIAL_PDF = "cninfo_official_pdf"
SOURCE_TYPE_SSE_EXCHANGE_ANNOUNCEMENT = "sse_exchange_announcement"
SOURCE_TYPE_EXCHANGE_OFFICIAL_PDF = "exchange_official_pdf"
ALLOWED_SOURCE_TYPES = (
    SOURCE_TYPE_CNINFO_OFFICIAL_PDF,
    SOURCE_TYPE_SSE_EXCHANGE_ANNOUNCEMENT,
    SOURCE_TYPE_EXCHANGE_OFFICIAL_PDF,
)

SOURCE_TYPE_PROVIDER_SOURCE_CANDIDATE = "provider_source_candidate"
SOURCE_TYPE_MIRROR_SOURCE_CANDIDATE = "mirror_source_candidate"
SOURCE_TYPE_UNKNOWN_SOURCE_CANDIDATE = "unknown_source_candidate"
SOURCE_TYPE_LOCAL_OFFICIAL_CACHE = "local_official_cache"
FORBIDDEN_SOURCE_TYPES = {
    SOURCE_TYPE_PROVIDER_SOURCE_CANDIDATE,
    SOURCE_TYPE_MIRROR_SOURCE_CANDIDATE,
    SOURCE_TYPE_UNKNOWN_SOURCE_CANDIDATE,
    SOURCE_TYPE_LOCAL_OFFICIAL_CACHE,
}

DISCOVERY_SCOPE_METADATA_ONLY = "metadata_only"
DISCOVERY_SCOPE_OFFICIAL_DISCLOSURE_CANDIDATE_ONLY = (
    "official_disclosure_candidate_only"
)
ALLOWED_DISCOVERY_SCOPES = {
    DISCOVERY_SCOPE_METADATA_ONLY,
    DISCOVERY_SCOPE_OFFICIAL_DISCLOSURE_CANDIDATE_ONLY,
}

DISCOVERY_SCOPE_DOWNLOAD = "download"
DISCOVERY_SCOPE_PARSE_PDF = "parse_pdf"
DISCOVERY_SCOPE_METRIC_EXTRACTION = "metric_extraction"
DISCOVERY_SCOPE_PROVIDER_LOOKUP = "provider_lookup"
DISCOVERY_SCOPE_REPORT_GENERATION = "report_generation"
DISCOVERY_SCOPE_OUTPUT_WRITE = "output_write"
FORBIDDEN_DISCOVERY_SCOPES = {
    DISCOVERY_SCOPE_DOWNLOAD,
    DISCOVERY_SCOPE_PARSE_PDF,
    DISCOVERY_SCOPE_METRIC_EXTRACTION,
    DISCOVERY_SCOPE_PROVIDER_LOOKUP,
    DISCOVERY_SCOPE_REPORT_GENERATION,
    DISCOVERY_SCOPE_OUTPUT_WRITE,
}

REJECTION_INVALID_REQUEST_SHAPE = "invalid_request_shape"
REJECTION_INVALID_SCHEMA_VERSION = "invalid_schema_version"
REJECTION_MISSING_SECURITY_IDENTITY = "missing_security_identity"
REJECTION_INVALID_SECURITY_IDENTITY_SCHEMA = "invalid_security_identity_schema"
REJECTION_INVALID_SECURITY_IDENTITY_SHAPE = "invalid_security_identity_shape"
REJECTION_SECURITY_IDENTITY_STATUS_NOT_VALID = "security_identity_status_not_valid"
REJECTION_SECURITY_IDENTITY_CONFIDENCE_NOT_ALLOWED = (
    "security_identity_confidence_not_allowed"
)
REJECTION_MISSING_STOCK_CODE = "missing_stock_code"
REJECTION_MISSING_EXCHANGE = "missing_exchange"
REJECTION_MISSING_MARKET = "missing_market"
REJECTION_TOP_LEVEL_IDENTITY_CONFLICT = "top_level_identity_conflict"
REJECTION_MISSING_QUERY_PERIOD = "missing_query_period"
REJECTION_AMBIGUOUS_QUERY_PERIOD = "ambiguous_query_period"
REJECTION_UNSUPPORTED_QUERY_PERIOD = "unsupported_query_period"
REJECTION_Q4_QUERY_PERIOD_UNSUPPORTED = "q4_query_period_unsupported"
REJECTION_MISSING_REQUESTED_ANNOUNCEMENT_TYPE = (
    "missing_requested_announcement_type"
)
REJECTION_UNSUPPORTED_REQUESTED_ANNOUNCEMENT_TYPE = (
    "unsupported_requested_announcement_type"
)
REJECTION_ANNOUNCEMENT_TYPE_PERIOD_MISMATCH = (
    "requested_announcement_type_query_period_mismatch"
)
REJECTION_ALLOWED_SOURCE_TYPES_NOT_LIST = "allowed_source_types_not_list"
REJECTION_ALLOWED_SOURCE_TYPES_EMPTY = "allowed_source_types_empty"
REJECTION_FORBIDDEN_SOURCE_TYPE = "forbidden_source_type"
REJECTION_UNSUPPORTED_SOURCE_TYPE = "unsupported_source_type"
REJECTION_SOURCE_PRIORITY_NOT_LIST = "source_priority_not_list"
REJECTION_SOURCE_PRIORITY_NOT_ALLOWED = "source_priority_not_allowed"
REJECTION_MISSING_DISCOVERY_SCOPE = "missing_discovery_scope"
REJECTION_FORBIDDEN_DISCOVERY_SCOPE = "forbidden_discovery_scope"
REJECTION_UNSUPPORTED_DISCOVERY_SCOPE = "unsupported_discovery_scope"
REJECTION_NOT_FOR_TRADING_ADVICE_REQUIRED = "not_for_trading_advice_required"
REJECTION_FORBIDDEN_MARKER_DETECTED = "forbidden_marker_detected"
REJECTION_LIVE_LOOKUP_FORBIDDEN = "live_lookup_forbidden"
REJECTION_PROVIDER_LOOKUP_FORBIDDEN = "provider_lookup_forbidden"
REJECTION_PDF_PARSER_FORBIDDEN = "pdf_parser_forbidden"
REJECTION_OUTPUT_FIXTURE_MANIFEST_WRITE_FORBIDDEN = (
    "output_fixture_manifest_write_forbidden"
)
REJECTION_TRADING_ADVICE_FORBIDDEN = "trading_advice_forbidden"
REJECTION_CAVEATS_NOT_LIST = "caveats_not_list"
REJECTION_BLOCKED_REASONS_NOT_LIST = "blocked_reasons_not_list"
REJECTION_MISSING_REQUEST_ID = "missing_request_id"
REJECTION_REQUEST_ID_MISMATCH = "request_id_mismatch"

_PERIOD_RE = re.compile(r"^(?P<year>20\d{2})(?P<suffix>A|FY|H1|Q[1-4])?$")
_CAMEL_SPLIT_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")

_RELATIVE_QUERY_PERIOD_MARKERS = (
    "latest",
    "recent",
    "最近",
    "最新",
    "上一期",
    "近年",
    "本期",
)

_SAFETY_MARKERS: tuple[tuple[str, str], ...] = (
    ("tushare_token", REJECTION_FORBIDDEN_MARKER_DETECTED),
    ("token", REJECTION_FORBIDDEN_MARKER_DETECTED),
    (".env", REJECTION_FORBIDDEN_MARKER_DETECTED),
    ("provider live", REJECTION_PROVIDER_LOOKUP_FORBIDDEN),
    ("provider lookup", REJECTION_PROVIDER_LOOKUP_FORBIDDEN),
    ("provider_lookup", REJECTION_PROVIDER_LOOKUP_FORBIDDEN),
    ("AkShare", REJECTION_PROVIDER_LOOKUP_FORBIDDEN),
    ("Tushare", REJECTION_PROVIDER_LOOKUP_FORBIDDEN),
    ("network", REJECTION_LIVE_LOOKUP_FORBIDDEN),
    ("HTTP", REJECTION_LIVE_LOOKUP_FORBIDDEN),
    ("fetch", REJECTION_LIVE_LOOKUP_FORBIDDEN),
    ("download", REJECTION_LIVE_LOOKUP_FORBIDDEN),
    ("live discovery", REJECTION_LIVE_LOOKUP_FORBIDDEN),
    ("CNInfo live", REJECTION_LIVE_LOOKUP_FORBIDDEN),
    ("SSE live", REJECTION_LIVE_LOOKUP_FORBIDDEN),
    ("PDF parser", REJECTION_PDF_PARSER_FORBIDDEN),
    ("table extractor", REJECTION_PDF_PARSER_FORBIDDEN),
    ("parse PDF", REJECTION_PDF_PARSER_FORBIDDEN),
    ("parse_pdf", REJECTION_PDF_PARSER_FORBIDDEN),
    ("metric extraction", REJECTION_FORBIDDEN_MARKER_DETECTED),
    ("metric_extraction", REJECTION_FORBIDDEN_MARKER_DETECTED),
    ("official_metric_fact", REJECTION_FORBIDDEN_MARKER_DETECTED),
    ("provider_official_conflict", REJECTION_FORBIDDEN_MARKER_DETECTED),
    ("Report V1", REJECTION_FORBIDDEN_MARKER_DETECTED),
    ("report_generation", REJECTION_FORBIDDEN_MARKER_DETECTED),
    ("accepted manifest write", REJECTION_OUTPUT_FIXTURE_MANIFEST_WRITE_FORBIDDEN),
    ("output baseline write", REJECTION_OUTPUT_FIXTURE_MANIFEST_WRITE_FORBIDDEN),
    ("fixture write", REJECTION_OUTPUT_FIXTURE_MANIFEST_WRITE_FORBIDDEN),
    ("output_write", REJECTION_OUTPUT_FIXTURE_MANIFEST_WRITE_FORBIDDEN),
    ("buy", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("sell", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("hold", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("target price", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("portfolio", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("position", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("technical signal", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("trading advice", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("investment advice", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("买入", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("卖出", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("持有", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("目标价", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("仓位", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("组合", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("技术信号", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("投资建议", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("下载", REJECTION_LIVE_LOOKUP_FORBIDDEN),
    ("网络", REJECTION_LIVE_LOOKUP_FORBIDDEN),
    ("联网", REJECTION_LIVE_LOOKUP_FORBIDDEN),
    ("解析PDF", REJECTION_PDF_PARSER_FORBIDDEN),
    ("PDF解析", REJECTION_PDF_PARSER_FORBIDDEN),
    ("表格抽取", REJECTION_PDF_PARSER_FORBIDDEN),
    ("指标抽取", REJECTION_FORBIDDEN_MARKER_DETECTED),
    ("正式研报", REJECTION_FORBIDDEN_MARKER_DETECTED),
    ("输出基线", REJECTION_OUTPUT_FIXTURE_MANIFEST_WRITE_FORBIDDEN),
    ("写入fixture", REJECTION_OUTPUT_FIXTURE_MANIFEST_WRITE_FORBIDDEN),
    ("写入accepted manifest", REJECTION_OUTPUT_FIXTURE_MANIFEST_WRITE_FORBIDDEN),
)

_SHORT_WORD_MARKERS = {
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


class OfficialDisclosureRequestSafetyError(ValueError):
    """Raised when explicit request input contains a forbidden marker."""

    def __init__(self, marker: str, rejection_reason: str) -> None:
        super().__init__(f"forbidden official disclosure request marker: {marker}")
        self.marker = marker
        self.rejection_reason = rejection_reason


def assert_no_official_disclosure_request_forbidden_markers(value: Any) -> None:
    """Recursively reject forbidden request markers in explicit caller input."""

    if isinstance(value, str):
        marker, reason = _string_forbidden_marker(value)
        if marker:
            raise OfficialDisclosureRequestSafetyError(marker, reason)
        return

    if isinstance(value, Mapping):
        for nested_key, nested_value in value.items():
            if str(nested_key) != "not_for_trading_advice":
                assert_no_official_disclosure_request_forbidden_markers(nested_key)
            assert_no_official_disclosure_request_forbidden_markers(nested_value)
        return

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for nested_value in value:
            assert_no_official_disclosure_request_forbidden_markers(nested_value)


def normalize_official_disclosure_request(payload: Any) -> dict[str, Any]:
    """Build a fail-closed request object from explicit metadata only."""

    if not isinstance(payload, Mapping):
        return _blocked_request(
            {},
            [REJECTION_INVALID_REQUEST_SHAPE],
            security_identity=None,
            not_for_trading_advice=None,
        )

    blocked_reasons: list[str] = []
    request_schema_version = _clean_string(payload.get("schema_version")) or SCHEMA_VERSION
    not_for_trading_advice = payload.get("not_for_trading_advice")
    if not_for_trading_advice is not True:
        blocked_reasons.append(REJECTION_NOT_FOR_TRADING_ADVICE_REQUIRED)

    security_identity, identity_reasons = _validate_security_identity_handoff(
        payload.get("security_identity")
    )
    blocked_reasons.extend(identity_reasons)

    safety_payload = payload if not identity_reasons else _without_security_identity(payload)
    try:
        assert_no_official_disclosure_request_forbidden_markers(safety_payload)
    except OfficialDisclosureRequestSafetyError as exc:
        blocked_reasons.append(exc.rejection_reason)

    if request_schema_version != SCHEMA_VERSION:
        blocked_reasons.append(REJECTION_INVALID_SCHEMA_VERSION)

    stock_code, exchange, market, company_name, identity_caveats, identity_conflict_reasons = (
        _metadata_from_identity_and_payload(security_identity, payload)
    )
    blocked_reasons.extend(identity_conflict_reasons)

    query_period, query_period_reasons = _normalize_query_period_with_reasons(
        payload.get("query_period")
    )
    blocked_reasons.extend(query_period_reasons)
    period_end_date = derive_period_end_date(query_period)

    requested_announcement_type, requested_type_reasons = (
        _normalize_requested_announcement_type_with_reasons(
            query_period,
            payload.get("requested_announcement_type"),
            explicit="requested_announcement_type" in payload,
        )
    )
    blocked_reasons.extend(requested_type_reasons)

    allowed_source_types, allowed_source_type_reasons = (
        _normalize_allowed_source_types_with_reasons(
            payload.get("allowed_source_types"),
            explicit="allowed_source_types" in payload,
        )
    )
    blocked_reasons.extend(allowed_source_type_reasons)

    source_priority, source_priority_reasons = _normalize_source_priority_with_reasons(
        payload.get("source_priority"),
        allowed_source_types,
        explicit="source_priority" in payload,
    )
    blocked_reasons.extend(source_priority_reasons)

    discovery_scope, discovery_scope_reasons = _normalize_discovery_scope_with_reasons(
        payload.get("discovery_scope"),
        explicit="discovery_scope" in payload,
    )
    blocked_reasons.extend(discovery_scope_reasons)

    if not stock_code:
        blocked_reasons.append(REJECTION_MISSING_STOCK_CODE)
    if not exchange:
        blocked_reasons.append(REJECTION_MISSING_EXCHANGE)
    if not market:
        blocked_reasons.append(REJECTION_MISSING_MARKET)

    caveats, caveat_reasons = _normalize_request_caveats(payload.get("caveats"))
    blocked_reasons.extend(caveat_reasons)
    caveats = _dedupe_preserve_order(identity_caveats + caveats)

    request = {
        "schema_version": request_schema_version,
        "request_id": "",
        "security_identity": security_identity,
        "stock_code": stock_code,
        "exchange": exchange,
        "market": market,
        "company_name": company_name,
        "query_period": query_period or _clean_string(payload.get("query_period")),
        "period_end_date": period_end_date or "",
        "requested_announcement_type": requested_announcement_type
        or _clean_string(payload.get("requested_announcement_type")),
        "allowed_source_types": allowed_source_types,
        "source_priority": source_priority,
        "discovery_scope": discovery_scope or _clean_string(payload.get("discovery_scope")),
        "blocked_reasons": [],
        "rejection_reason": None,
        "caveats": caveats,
        "not_for_trading_advice": not_for_trading_advice,
    }

    blocked_reasons = _dedupe_preserve_order(blocked_reasons)
    if not blocked_reasons:
        request["request_id"] = build_official_disclosure_request_id(request)
        explicit_request_id = _clean_string(payload.get("request_id"))
        if explicit_request_id and explicit_request_id != request["request_id"]:
            blocked_reasons.append(REJECTION_REQUEST_ID_MISMATCH)

    return _apply_blocking_reasons(request, blocked_reasons)


def validate_official_disclosure_request(request: Any) -> dict[str, Any]:
    """Validate an official disclosure request and return a fail-closed object."""

    if not isinstance(request, Mapping):
        return _blocked_request(
            {},
            [REJECTION_INVALID_REQUEST_SHAPE],
            security_identity=None,
            not_for_trading_advice=None,
        )

    normalized = dict(request)
    blocked_reasons: list[str] = []

    if normalized.get("schema_version") != SCHEMA_VERSION:
        blocked_reasons.append(REJECTION_INVALID_SCHEMA_VERSION)

    if normalized.get("not_for_trading_advice") is not True:
        blocked_reasons.append(REJECTION_NOT_FOR_TRADING_ADVICE_REQUIRED)

    security_identity, identity_reasons = _validate_security_identity_handoff(
        normalized.get("security_identity")
    )
    blocked_reasons.extend(identity_reasons)

    safety_payload = normalized if not identity_reasons else _without_security_identity(normalized)
    try:
        assert_no_official_disclosure_request_forbidden_markers(safety_payload)
    except OfficialDisclosureRequestSafetyError as exc:
        blocked_reasons.append(exc.rejection_reason)

    stock_code, exchange, market, company_name, identity_caveats, identity_conflict_reasons = (
        _metadata_from_identity_and_payload(security_identity, normalized)
    )
    blocked_reasons.extend(identity_conflict_reasons)
    if not stock_code:
        blocked_reasons.append(REJECTION_MISSING_STOCK_CODE)
    if not exchange:
        blocked_reasons.append(REJECTION_MISSING_EXCHANGE)
    if not market:
        blocked_reasons.append(REJECTION_MISSING_MARKET)

    query_period, query_period_reasons = _normalize_query_period_with_reasons(
        normalized.get("query_period")
    )
    blocked_reasons.extend(query_period_reasons)
    period_end_date = derive_period_end_date(query_period)
    if period_end_date and normalized.get("period_end_date") != period_end_date:
        blocked_reasons.append(REJECTION_UNSUPPORTED_QUERY_PERIOD)

    requested_announcement_type, requested_type_reasons = (
        _normalize_requested_announcement_type_with_reasons(
            query_period,
            normalized.get("requested_announcement_type"),
            explicit=True,
        )
    )
    blocked_reasons.extend(requested_type_reasons)

    allowed_source_types, allowed_source_type_reasons = (
        _normalize_allowed_source_types_with_reasons(
            normalized.get("allowed_source_types"),
            explicit=True,
        )
    )
    blocked_reasons.extend(allowed_source_type_reasons)

    source_priority, source_priority_reasons = _normalize_source_priority_with_reasons(
        normalized.get("source_priority"),
        allowed_source_types,
        explicit=True,
    )
    blocked_reasons.extend(source_priority_reasons)

    discovery_scope, discovery_scope_reasons = _normalize_discovery_scope_with_reasons(
        normalized.get("discovery_scope"),
        explicit=True,
    )
    blocked_reasons.extend(discovery_scope_reasons)

    caveats = normalized.get("caveats")
    if not isinstance(caveats, list):
        blocked_reasons.append(REJECTION_CAVEATS_NOT_LIST)
        caveats = []
    else:
        caveats = _dedupe_preserve_order(identity_caveats + list(caveats))

    if not isinstance(normalized.get("blocked_reasons"), list):
        blocked_reasons.append(REJECTION_BLOCKED_REASONS_NOT_LIST)
        existing_blocked_reasons: list[str] = []
    else:
        existing_blocked_reasons = list(normalized.get("blocked_reasons", []))

    normalized.update(
        {
            "security_identity": security_identity,
            "stock_code": stock_code,
            "exchange": exchange,
            "market": market,
            "company_name": company_name,
            "query_period": query_period or _clean_string(normalized.get("query_period")),
            "period_end_date": period_end_date or _clean_string(normalized.get("period_end_date")),
            "requested_announcement_type": requested_announcement_type
            or _clean_string(normalized.get("requested_announcement_type")),
            "allowed_source_types": allowed_source_types,
            "source_priority": source_priority,
            "discovery_scope": discovery_scope or _clean_string(normalized.get("discovery_scope")),
            "caveats": caveats,
        }
    )

    if not _clean_string(normalized.get("request_id")):
        blocked_reasons.append(REJECTION_MISSING_REQUEST_ID)
    elif not blocked_reasons:
        expected_request_id = build_official_disclosure_request_id(normalized)
        if normalized.get("request_id") != expected_request_id:
            blocked_reasons.append(REJECTION_REQUEST_ID_MISMATCH)

    if normalized.get("rejection_reason") not in {None, ""} and not existing_blocked_reasons:
        blocked_reasons.append(str(normalized["rejection_reason"]))

    blocked_reasons = _dedupe_preserve_order(existing_blocked_reasons + blocked_reasons)
    return _apply_blocking_reasons(normalized, blocked_reasons)


def normalize_query_period(value: Any) -> str | None:
    """Canonicalize supported explicit report periods without date or network lookup."""

    normalized, reasons = _normalize_query_period_with_reasons(value)
    if reasons:
        return None
    return normalized


def derive_period_end_date(query_period: Any) -> str | None:
    """Derive a period end date from a canonical or supported explicit period."""

    normalized = normalize_query_period(query_period)
    if normalized is None:
        return None

    year = normalized[:4]
    if normalized.endswith("FY"):
        return f"{year}-12-31"
    if normalized.endswith("H1"):
        return f"{year}-06-30"
    if normalized.endswith("Q1"):
        return f"{year}-03-31"
    if normalized.endswith("Q2"):
        return f"{year}-06-30"
    if normalized.endswith("Q3"):
        return f"{year}-09-30"
    return None


def normalize_requested_announcement_type(
    query_period: Any, requested_type: Any = None
) -> str | None:
    """Return the announcement type implied by period, rejecting mismatches."""

    normalized_period = normalize_query_period(query_period)
    normalized_type, reasons = _normalize_requested_announcement_type_with_reasons(
        normalized_period,
        requested_type,
        explicit=requested_type is not None,
    )
    if reasons:
        return None
    return normalized_type


def normalize_allowed_source_types(values: Any) -> list[str]:
    """Normalize allowed official source types, defaulting to all official types."""

    normalized, reasons = _normalize_allowed_source_types_with_reasons(
        values,
        explicit=values is not None,
    )
    if reasons:
        return []
    return normalized


def normalize_discovery_scope(value: Any) -> str | None:
    """Normalize an allowed no-IO discovery scope."""

    normalized, reasons = _normalize_discovery_scope_with_reasons(
        value,
        explicit=value is not None,
    )
    if reasons:
        return None
    return normalized


def build_official_disclosure_request_id(request: Mapping[str, Any]) -> str:
    """Build a deterministic request id from explicit metadata only."""

    identity = {
        "stock_code": _clean_string(request.get("stock_code")),
        "exchange": _clean_string(request.get("exchange")),
        "query_period": normalize_query_period(request.get("query_period"))
        or _clean_string(request.get("query_period")),
        "requested_announcement_type": _clean_string(
            request.get("requested_announcement_type")
        ),
        "allowed_source_types": _normalize_list_for_id(
            request.get("allowed_source_types")
        ),
        "source_priority": _normalize_list_for_id(request.get("source_priority")),
        "discovery_scope": _clean_string(request.get("discovery_scope")),
    }
    payload = json.dumps(identity, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]
    return f"official_disclosure_request_{digest}"


def build_request_rejection_reason(payload_or_request: Any) -> str | None:
    """Return the current fail-closed rejection reason, if any."""

    if isinstance(payload_or_request, Mapping) and payload_or_request.get(
        "schema_version"
    ) == SCHEMA_VERSION and "request_id" in payload_or_request:
        request = validate_official_disclosure_request(payload_or_request)
    else:
        request = normalize_official_disclosure_request(payload_or_request)
    return request.get("rejection_reason")


def can_enter_discovery_candidate_generation(
    request: Any, with_reason: bool = False
) -> bool | tuple[bool, str | None]:
    """Return whether a request may hand off to later candidate generation."""

    validated = validate_official_disclosure_request(request)
    allowed = (
        validated.get("schema_version") == SCHEMA_VERSION
        and validated.get("not_for_trading_advice") is True
        and validated.get("rejection_reason") in {None, ""}
        and validated.get("blocked_reasons") == []
        and validated.get("discovery_scope") in ALLOWED_DISCOVERY_SCOPES
    )
    reason = None if allowed else validated.get("rejection_reason")
    if with_reason:
        return allowed, reason
    return allowed


def _validate_security_identity_handoff(
    identity: Any,
) -> tuple[dict[str, Any] | None, list[str]]:
    if identity is None:
        return None, [REJECTION_MISSING_SECURITY_IDENTITY]
    if not isinstance(identity, Mapping):
        return None, [REJECTION_INVALID_SECURITY_IDENTITY_SHAPE]
    if identity.get("schema_version") != SECURITY_IDENTITY_SCHEMA_VERSION:
        return dict(identity), [REJECTION_INVALID_SECURITY_IDENTITY_SCHEMA]

    validated = validate_security_identity(identity)
    reasons: list[str] = []
    if validated.get("identity_status") != STATUS_VALID:
        reasons.append(REJECTION_SECURITY_IDENTITY_STATUS_NOT_VALID)
        if validated.get("rejection_reason"):
            reasons.append(str(validated["rejection_reason"]))
    if validated.get("identity_confidence") not in {CONFIDENCE_HIGH, CONFIDENCE_MEDIUM}:
        reasons.append(REJECTION_SECURITY_IDENTITY_CONFIDENCE_NOT_ALLOWED)
    return dict(validated), reasons


def _metadata_from_identity_and_payload(
    identity: Mapping[str, Any] | None, payload: Mapping[str, Any]
) -> tuple[str, str, str, str | None, list[str], list[str]]:
    if not identity:
        return "", "", "", None, [], []

    reasons: list[str] = []
    stock_code = _clean_string(identity.get("normalized_stock_code"))
    exchange = _clean_string(identity.get("exchange"))
    market = _clean_string(identity.get("market"))
    company_name = _clean_optional_string(
        identity.get("normalized_company_name") or identity.get("company_name")
    )
    caveats = (
        list(identity.get("caveats", [])) if isinstance(identity.get("caveats"), list) else []
    )

    for field, expected in (
        ("stock_code", stock_code),
        ("exchange", exchange),
        ("market", market),
    ):
        if field in payload and payload.get(field) is not None:
            if _clean_string(payload.get(field)) != expected:
                reasons.append(REJECTION_TOP_LEVEL_IDENTITY_CONFLICT)

    if "company_name" in payload and payload.get("company_name") is not None:
        payload_company_name = _clean_optional_string(payload.get("company_name"))
        if company_name and payload_company_name and payload_company_name != company_name:
            reasons.append(REJECTION_TOP_LEVEL_IDENTITY_CONFLICT)
        elif not company_name and payload_company_name:
            company_name = payload_company_name
            caveats.append("company name supplied in request but not verified against stock code")

    return stock_code, exchange, market, company_name, caveats, _dedupe_preserve_order(reasons)


def _normalize_query_period_with_reasons(value: Any) -> tuple[str | None, list[str]]:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None, [REJECTION_MISSING_QUERY_PERIOD]

    text = _clean_string(value).upper()
    if any(marker.casefold() in _clean_string(value).casefold() for marker in _RELATIVE_QUERY_PERIOD_MARKERS):
        return None, [REJECTION_AMBIGUOUS_QUERY_PERIOD]

    match = _PERIOD_RE.fullmatch(text)
    if not match:
        return None, [REJECTION_UNSUPPORTED_QUERY_PERIOD]

    year = match.group("year")
    suffix = match.group("suffix") or "FY"
    if suffix == "A":
        suffix = "FY"
    if suffix == "Q4":
        return None, [REJECTION_Q4_QUERY_PERIOD_UNSUPPORTED]
    if suffix not in {"FY", "H1", "Q1", "Q2", "Q3"}:
        return None, [REJECTION_UNSUPPORTED_QUERY_PERIOD]
    return f"{year}{suffix}", []


def _normalize_requested_announcement_type_with_reasons(
    query_period: str | None, requested_type: Any, *, explicit: bool
) -> tuple[str | None, list[str]]:
    implied_type = _announcement_type_for_period(query_period)
    if not implied_type:
        return None, []

    if not explicit:
        return implied_type, []
    if requested_type is None:
        return None, [REJECTION_MISSING_REQUESTED_ANNOUNCEMENT_TYPE]

    requested = _clean_string(requested_type)
    if not requested:
        return None, [REJECTION_MISSING_REQUESTED_ANNOUNCEMENT_TYPE]
    if requested not in SUPPORTED_ANNOUNCEMENT_TYPES:
        return requested, [REJECTION_UNSUPPORTED_REQUESTED_ANNOUNCEMENT_TYPE]
    if requested != implied_type:
        return requested, [REJECTION_ANNOUNCEMENT_TYPE_PERIOD_MISMATCH]
    return requested, []


def _announcement_type_for_period(query_period: str | None) -> str | None:
    if not query_period:
        return None
    if query_period.endswith("FY"):
        return ANNOUNCEMENT_TYPE_ANNUAL_REPORT
    if query_period.endswith("H1"):
        return ANNOUNCEMENT_TYPE_SEMIANNUAL_REPORT
    if query_period.endswith(("Q1", "Q2", "Q3")):
        return ANNOUNCEMENT_TYPE_QUARTERLY_REPORT
    return None


def _normalize_allowed_source_types_with_reasons(
    values: Any, *, explicit: bool
) -> tuple[list[str], list[str]]:
    if not explicit:
        return list(ALLOWED_SOURCE_TYPES), []
    if not isinstance(values, list):
        return [], [REJECTION_ALLOWED_SOURCE_TYPES_NOT_LIST]
    if not values:
        return [], [REJECTION_ALLOWED_SOURCE_TYPES_EMPTY]

    normalized = [_clean_string(value) for value in values]
    reasons = _source_type_reasons(normalized)
    return _dedupe_preserve_order(normalized), reasons


def _normalize_source_priority_with_reasons(
    values: Any, allowed_source_types: list[str], *, explicit: bool
) -> tuple[list[str], list[str]]:
    if not explicit:
        return list(allowed_source_types), []
    if not isinstance(values, list):
        return [], [REJECTION_SOURCE_PRIORITY_NOT_LIST]
    if not values:
        return list(allowed_source_types), []

    normalized = [_clean_string(value) for value in values]
    reasons = _source_type_reasons(normalized)
    for source_type in normalized:
        if source_type and source_type not in allowed_source_types:
            reasons.append(REJECTION_SOURCE_PRIORITY_NOT_ALLOWED)
    return _dedupe_preserve_order(normalized), _dedupe_preserve_order(reasons)


def _source_type_reasons(source_types: list[str]) -> list[str]:
    reasons: list[str] = []
    for source_type in source_types:
        if not source_type or source_type not in set(ALLOWED_SOURCE_TYPES) | FORBIDDEN_SOURCE_TYPES:
            reasons.append(REJECTION_UNSUPPORTED_SOURCE_TYPE)
        if source_type in FORBIDDEN_SOURCE_TYPES:
            reasons.append(REJECTION_FORBIDDEN_SOURCE_TYPE)
    return _dedupe_preserve_order(reasons)


def _normalize_discovery_scope_with_reasons(
    value: Any, *, explicit: bool
) -> tuple[str | None, list[str]]:
    if not explicit:
        return DISCOVERY_SCOPE_METADATA_ONLY, []
    if value is None:
        return None, [REJECTION_MISSING_DISCOVERY_SCOPE]

    normalized = _clean_string(value)
    if not normalized:
        return None, [REJECTION_MISSING_DISCOVERY_SCOPE]
    if normalized in FORBIDDEN_DISCOVERY_SCOPES:
        return normalized, [REJECTION_FORBIDDEN_DISCOVERY_SCOPE]
    if normalized not in ALLOWED_DISCOVERY_SCOPES:
        return normalized, [REJECTION_UNSUPPORTED_DISCOVERY_SCOPE]
    return normalized, []


def _normalize_request_caveats(value: Any) -> tuple[list[str], list[str]]:
    if value is None:
        return [], []
    if not isinstance(value, list):
        return [], [REJECTION_CAVEATS_NOT_LIST]
    return [str(item) for item in value], []


def _blocked_request(
    payload: Mapping[str, Any],
    reasons: list[str],
    *,
    security_identity: Mapping[str, Any] | None,
    not_for_trading_advice: Any,
) -> dict[str, Any]:
    request = {
        "schema_version": _clean_string(payload.get("schema_version")) or SCHEMA_VERSION,
        "request_id": "",
        "security_identity": dict(security_identity) if isinstance(security_identity, Mapping) else None,
        "stock_code": _clean_string(payload.get("stock_code")),
        "exchange": _clean_string(payload.get("exchange")),
        "market": _clean_string(payload.get("market")),
        "company_name": _clean_optional_string(payload.get("company_name")),
        "query_period": _clean_string(payload.get("query_period")),
        "period_end_date": _clean_string(payload.get("period_end_date")),
        "requested_announcement_type": _clean_string(payload.get("requested_announcement_type")),
        "allowed_source_types": [],
        "source_priority": [],
        "discovery_scope": _clean_string(payload.get("discovery_scope")),
        "blocked_reasons": [],
        "rejection_reason": None,
        "caveats": [],
        "not_for_trading_advice": not_for_trading_advice,
    }
    return _apply_blocking_reasons(request, reasons)


def _apply_blocking_reasons(
    request: Mapping[str, Any], blocked_reasons: list[str]
) -> dict[str, Any]:
    normalized = dict(request)
    blocked_reasons = _dedupe_preserve_order([reason for reason in blocked_reasons if reason])
    normalized["blocked_reasons"] = blocked_reasons
    normalized["rejection_reason"] = blocked_reasons[0] if blocked_reasons else None
    return normalized


def _without_security_identity(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key != "security_identity"}


def _normalize_list_for_id(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_clean_string(item) for item in value]


def _string_forbidden_marker(value: str) -> tuple[str, str | None]:
    for marker, reason in _SAFETY_MARKERS:
        if _contains_marker(value, marker):
            return marker, reason
    return "", None


def _contains_marker(value: str, marker: str) -> bool:
    if _contains_cjk(marker):
        return marker in value

    lowered = value.casefold()
    marker_lowered = marker.casefold()
    normalized_value = _normalize_marker_text(value)
    normalized_marker = _normalize_marker_text(marker)

    if marker_lowered == ".env":
        return ".env" in lowered
    if normalized_marker == "token":
        return bool(re.search(r"\btoken\b", lowered))
    if normalized_marker == "http":
        return "http" in lowered
    if normalized_marker in _SHORT_WORD_MARKERS:
        return normalized_marker in normalized_value.split("_") or bool(
            re.search(rf"\b{re.escape(normalized_marker)}\b", lowered)
        )
    return bool(normalized_marker and normalized_marker in normalized_value)


def _contains_cjk(value: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in value)


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


def _clean_optional_string(value: Any) -> str | None:
    cleaned = _clean_string(value)
    return cleaned or None


def _dedupe_preserve_order(values: list[Any]) -> list[Any]:
    seen: set[Any] = set()
    deduped: list[Any] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped
