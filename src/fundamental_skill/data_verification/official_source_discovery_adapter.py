# -*- coding: utf-8 -*-
"""Metadata-only official source discovery from explicit injected records."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urlparse

from .official_disclosure_discovery_candidate import (
    normalize_official_disclosure_discovery_candidate,
    validate_official_disclosure_discovery_candidate,
)
from .official_disclosure_request import validate_official_disclosure_request
from .validators import OfficialVerificationValidationError


SCHEMA_VERSION = "official_source_discovery_adapter_result.v1"
DISCOVERY_CANDIDATE_SCHEMA_VERSION = "official_disclosure_discovery_candidate.v1"

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

ALLOWED_DOMAINS = (
    "cninfo.com.cn",
    "static.cninfo.com.cn",
    "sse.com.cn",
    "www.sse.com.cn",
    "szse.cn",
    "www.szse.cn",
    "bse.cn",
    "www.bse.cn",
)

METADATA_RECORD_FIELDS = (
    "source_url",
    "source_title",
    "disclosure_date",
    "stock_code",
    "company_name",
    "exchange",
    "period_key",
    "period_end_date",
    "announcement_type",
    "source_type",
    "source_domain",
    "discovered_at_utc",
    "discovery_method",
    "redirect_chain",
    "caveats",
    "not_for_trading_advice",
)

REQUIRED_METADATA_FIELDS = (
    "source_url",
    "source_title",
    "disclosure_date",
    "stock_code",
    "exchange",
    "period_key",
    "period_end_date",
    "announcement_type",
    "source_type",
    "discovered_at_utc",
    "discovery_method",
)

FORBIDDEN_METADATA_FIELDS = {
    "file_content",
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

REASON_MISSING_REQUEST = "missing_request"
REASON_INVALID_REQUEST = "invalid_request"
REASON_REQUEST_BLOCKED = "request_blocked"
REASON_METADATA_RECORDS_MISSING = "metadata_records_missing"
REASON_METADATA_RECORDS_NOT_LIST = "metadata_records_not_list"
REASON_NO_METADATA_RECORDS = "no_metadata_records"
REASON_METADATA_RECORD_NOT_MAPPING = "metadata_record_not_mapping"
REASON_MISSING_REQUIRED_METADATA = "missing_required_metadata"
REASON_NOT_FOR_TRADING_ADVICE_REQUIRED = "not_for_trading_advice_required"
REASON_FORBIDDEN_METADATA_FIELD = "forbidden_metadata_field"
REASON_FORBIDDEN_MARKER_DETECTED = "forbidden_marker_detected"
REASON_FORBIDDEN_SOURCE_TYPE = "forbidden_source_type"
REASON_UNSUPPORTED_SOURCE_TYPE = "unsupported_source_type"
REASON_SOURCE_TYPE_NOT_ALLOWED_BY_REQUEST = "source_type_not_allowed_by_request"
REASON_NON_ALLOWLIST_DOMAIN = "non_allowlist_domain"
REASON_MALFORMED_URL = "malformed_url"
REASON_SOURCE_DOMAIN_MISMATCH = "source_domain_mismatch"
REASON_REDIRECT_CHAIN_NOT_LIST = "redirect_chain_not_list"
REASON_REDIRECT_DOMAIN_NOT_ALLOWED = "redirect_domain_not_allowed"
REASON_STOCK_CODE_MISMATCH = "stock_code_mismatch"
REASON_EXCHANGE_MISMATCH = "exchange_mismatch"
REASON_PERIOD_KEY_MISMATCH = "period_key_mismatch"
REASON_PERIOD_END_DATE_MISMATCH = "period_end_date_mismatch"
REASON_ANNOUNCEMENT_TYPE_MISMATCH = "announcement_type_mismatch"
REASON_COMPANY_NAME_MISMATCH = "company_name_mismatch"
REASON_CANDIDATE_VALIDATOR_REJECTED = "candidate_validator_rejected"
REASON_AMBIGUOUS_DUPLICATE_REVIEW_REQUIRED = "ambiguous_duplicate_review_required"
REASON_MULTIPLE_CANDIDATES_REVIEW_REQUIRED = "multiple_candidates_review_required"
REASON_NO_CANDIDATES_FOUND = "no_candidates_found"
REASON_ALL_RECORDS_REJECTED = "all_records_rejected"

_DISCOVERY_FORBIDDEN_ENGLISH_MARKERS = (
    "token",
    ".env",
    "tushare_token",
    "provider live",
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
    "metric extraction",
    "official_metric_fact",
    "provider_official_conflict",
    "Report V1",
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
)

_DISCOVERY_FORBIDDEN_CJK_MARKERS = (
    "涔板叆",
    "鍗栧嚭",
    "鎸佹湁",
    "鐩爣浠?",
    "浠撲綅",
    "缁勫悎",
    "鎶€鏈俊鍙?",
    "鎶曡祫寤鸿",
    "涓嬭浇",
    "缃戠粶",
    "鑱旂綉",
    "瑙ｆ瀽PDF",
    "PDF瑙ｆ瀽",
    "琛ㄦ牸鎶藉彇",
    "鎸囨爣鎶藉彇",
    "姝ｅ紡鐮旀姤",
    "杈撳嚭鍩虹嚎",
    "鍐欏叆fixture",
    "鍐欏叆accepted manifest",
    "璇诲彇token",
    "璇诲彇.env",
    "璇诲彇tushare_token",
    "璋冪敤AkShare",
    "璋冪敤Tushare",
    "璋冪敤CNInfo live",
    "璋冪敤SSE live",
    "璋冪敤provider",
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
_CAMEL_SPLIT_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_STANDALONE_HTTP_RE = re.compile(r"(?<![a-z])http(?![a-z])", flags=re.IGNORECASE)
_HOST_RE = re.compile(r"^[a-z0-9.-]+$")


def discover_official_sources_from_metadata(
    request: Any, metadata_records: Any
) -> dict[str, Any]:
    """Return candidate metadata from explicit records only; no IO or live lookup."""

    validated_request, request_reasons = _validate_request_for_adapter(request)
    if request_reasons:
        return build_discovery_blocked_result(
            request=validated_request,
            input_metadata_records=_safe_metadata_records_snapshot(metadata_records),
            discovery_candidates=[],
            rejected_records=[],
            blocked_reasons=request_reasons,
            caveats=_request_caveats(validated_request),
        )

    if metadata_records is None:
        return build_discovery_blocked_result(
            request=validated_request,
            input_metadata_records=[],
            discovery_candidates=[],
            rejected_records=[],
            blocked_reasons=[REASON_METADATA_RECORDS_MISSING],
            caveats=_request_caveats(validated_request),
        )
    if not isinstance(metadata_records, list):
        return build_discovery_blocked_result(
            request=validated_request,
            input_metadata_records=[],
            discovery_candidates=[],
            rejected_records=[],
            blocked_reasons=[REASON_METADATA_RECORDS_NOT_LIST],
            caveats=_request_caveats(validated_request),
        )
    if not metadata_records:
        return build_discovery_blocked_result(
            request=validated_request,
            input_metadata_records=[],
            discovery_candidates=[],
            rejected_records=[],
            blocked_reasons=[REASON_NO_METADATA_RECORDS, REASON_NO_CANDIDATES_FOUND],
            caveats=_request_caveats(validated_request),
        )

    input_snapshots: list[dict[str, Any]] = []
    rejected_records: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []

    for index, record in enumerate(metadata_records):
        if not isinstance(record, Mapping):
            rejected_records.append(
                build_rejected_discovery_record(
                    record,
                    [REASON_METADATA_RECORD_NOT_MAPPING],
                    record_index=index,
                )
            )
            input_snapshots.append({"record_index": index, "record_omitted": True, "not_for_trading_advice": True})
            continue

        try:
            normalized_record = normalize_metadata_record(record)
        except OfficialVerificationValidationError:
            rejected_records.append(
                build_rejected_discovery_record(
                    record,
                    [REASON_FORBIDDEN_MARKER_DETECTED],
                    record_index=index,
                )
            )
            input_snapshots.append(_safe_record_snapshot(record, record_index=index))
            continue

        input_snapshots.append(_safe_record_snapshot(normalized_record, record_index=index))
        rejection_reasons = check_metadata_record_against_request(validated_request, normalized_record)
        if rejection_reasons:
            rejected_records.append(
                build_rejected_discovery_record(
                    normalized_record,
                    rejection_reasons,
                    record_index=index,
                )
            )
            continue

        try:
            candidates.append(build_discovery_candidate_from_metadata(validated_request, normalized_record))
        except OfficialVerificationValidationError as exc:
            rejected_records.append(
                build_rejected_discovery_record(
                    normalized_record,
                    [REASON_CANDIDATE_VALIDATOR_REJECTED, str(exc)],
                    record_index=index,
                )
            )

    candidates, dedupe_reasons, dedupe_caveats = dedupe_discovery_candidates(candidates)
    blocked_reasons = list(dedupe_reasons)
    caveats = _dedupe_preserve_order(_request_caveats(validated_request) + dedupe_caveats)

    if not candidates:
        blocked_reasons.append(REASON_NO_CANDIDATES_FOUND)
        if rejected_records:
            blocked_reasons.append(REASON_ALL_RECORDS_REJECTED)
    elif len(candidates) > 1:
        blocked_reasons.append(REASON_MULTIPLE_CANDIDATES_REVIEW_REQUIRED)
        caveats.append("multiple plausible official metadata candidates require review")

    result = {
        "schema_version": SCHEMA_VERSION,
        "request": dict(validated_request),
        "input_metadata_records": input_snapshots,
        "discovery_candidates": candidates,
        "rejected_records": rejected_records,
        "blocked_reasons": _dedupe_preserve_order(blocked_reasons),
        "caveats": _dedupe_preserve_order(caveats),
        "not_for_trading_advice": True,
    }
    validate_official_source_discovery_adapter_result(result)
    return result


def validate_official_source_discovery_adapter_result(result: Any) -> None:
    """Validate adapter result shape without registering, locating, reading, or writing."""

    if not isinstance(result, Mapping):
        raise OfficialVerificationValidationError("adapter result must be a mapping")
    required = (
        "schema_version",
        "request",
        "input_metadata_records",
        "discovery_candidates",
        "rejected_records",
        "blocked_reasons",
        "caveats",
        "not_for_trading_advice",
    )
    missing = [key for key in required if key not in result]
    if missing:
        raise OfficialVerificationValidationError(f"adapter result missing keys: {missing}")
    if result["schema_version"] != SCHEMA_VERSION:
        raise OfficialVerificationValidationError("adapter result schema_version is unsupported")
    if result.get("not_for_trading_advice") is not True:
        raise OfficialVerificationValidationError("not_for_trading_advice must be true")
    for field in ("input_metadata_records", "discovery_candidates", "rejected_records", "blocked_reasons", "caveats"):
        if not isinstance(result.get(field), list):
            raise OfficialVerificationValidationError(f"{field} must be a list")
    _assert_adapter_result_metadata_has_no_forbidden_markers(result)
    for candidate in result["discovery_candidates"]:
        validate_official_disclosure_discovery_candidate(candidate)
    for rejected in result["rejected_records"]:
        if not isinstance(rejected, Mapping):
            raise OfficialVerificationValidationError("rejected_records must contain mappings")
        if not isinstance(rejected.get("reasons"), list) or not rejected["reasons"]:
            raise OfficialVerificationValidationError("rejected record reasons must be non-empty")
    if result["blocked_reasons"]:
        return
    if not result["discovery_candidates"] or result["rejected_records"]:
        raise OfficialVerificationValidationError("blocked, rejected, or empty discovery result requires blocked_reasons")


def normalize_metadata_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize one explicit metadata record without touching external state."""

    if not isinstance(record, Mapping):
        raise OfficialVerificationValidationError("metadata record must be a mapping")
    _assert_no_forbidden_metadata_fields(record)
    assert_no_official_source_discovery_forbidden_markers(record)

    normalized: dict[str, Any] = {}
    for field in METADATA_RECORD_FIELDS:
        if field not in record:
            continue
        value = record[field]
        if field == "not_for_trading_advice":
            normalized[field] = value
        elif field == "redirect_chain":
            normalized[field] = list(value) if isinstance(value, list) else value
        elif field == "caveats":
            normalized[field] = list(value) if isinstance(value, list) else value
        else:
            normalized[field] = _clean_string(value)

    source_url = normalized.get("source_url", "")
    parsed_url = _parse_official_url(source_url)
    if parsed_url:
        normalized["source_url"] = parsed_url["url"]
        normalized.setdefault("source_domain", parsed_url["host"])
        if not normalized.get("source_domain"):
            normalized["source_domain"] = parsed_url["host"]
    if normalized.get("source_domain"):
        normalized["source_domain"] = _normalize_domain_host(normalized["source_domain"]) or _clean_string(
            normalized["source_domain"]
        ).lower()

    return normalized


def check_metadata_record_against_request(request: Mapping[str, Any], record: Mapping[str, Any]) -> list[str]:
    """Return fail-closed reasons for records that cannot become candidates."""

    reasons: list[str] = []

    if record.get("not_for_trading_advice") is not True:
        reasons.append(REASON_NOT_FOR_TRADING_ADVICE_REQUIRED)

    for field in REQUIRED_METADATA_FIELDS:
        if _is_blank(record.get(field)):
            reasons.append(REASON_MISSING_REQUIRED_METADATA)
            break

    source_type = _clean_string(record.get("source_type"))
    if source_type in FORBIDDEN_SOURCE_TYPES:
        reasons.append(REASON_FORBIDDEN_SOURCE_TYPE)
    elif source_type not in ALLOWED_SOURCE_TYPES:
        reasons.append(REASON_UNSUPPORTED_SOURCE_TYPE)
    elif source_type not in request.get("allowed_source_types", []):
        reasons.append(REASON_SOURCE_TYPE_NOT_ALLOWED_BY_REQUEST)

    parsed_url = _parse_official_url(record.get("source_url"))
    if not parsed_url:
        reasons.append(REASON_MALFORMED_URL)
    else:
        source_domain = _normalize_domain_host(record.get("source_domain")) or ""
        if source_domain and source_domain != parsed_url["host"]:
            reasons.append(REASON_SOURCE_DOMAIN_MISMATCH)
        if parsed_url["host"] not in ALLOWED_DOMAINS:
            reasons.append(REASON_NON_ALLOWLIST_DOMAIN)

    source_domain = _normalize_domain_host(record.get("source_domain")) or ""
    if source_domain and source_domain not in ALLOWED_DOMAINS:
        reasons.append(REASON_NON_ALLOWLIST_DOMAIN)

    reasons.extend(_redirect_chain_reasons(record.get("redirect_chain")))
    reasons.extend(_request_match_reasons(request, record))
    return _dedupe_preserve_order(reasons)


def build_discovery_candidate_from_metadata(
    request: Mapping[str, Any], record: Mapping[str, Any]
) -> dict[str, Any]:
    """Build and validate an official disclosure discovery candidate."""

    reasons = check_metadata_record_against_request(request, record)
    if reasons:
        raise OfficialVerificationValidationError(f"metadata record rejected: {reasons}")

    candidate = {
        "schema_version": DISCOVERY_CANDIDATE_SCHEMA_VERSION,
        "discovery_candidate_id": "",
        "stock_code": _clean_string(record.get("stock_code")),
        "company_name": _clean_string(record.get("company_name")) or _clean_string(request.get("company_name")),
        "exchange": _clean_string(record.get("exchange")),
        "period_key": _clean_string(record.get("period_key")),
        "period_end_date": _clean_string(record.get("period_end_date")),
        "announcement_type": _clean_string(record.get("announcement_type")),
        "source_type": _clean_string(record.get("source_type")),
        "source_url": _clean_string(record.get("source_url")),
        "source_title": _clean_string(record.get("source_title")),
        "disclosure_date": _clean_string(record.get("disclosure_date")),
        "discovered_at_utc": _clean_string(record.get("discovered_at_utc")),
        "discovery_method": _clean_string(record.get("discovery_method")),
        "source_domain": _clean_string(record.get("source_domain")),
        "raw_candidate_metadata": _raw_candidate_metadata(record),
        "normalized_candidate_metadata": {
            "adapter_schema_version": SCHEMA_VERSION,
            "request_id": _clean_string(request.get("request_id")),
            "metadata_only": True,
            "company_hint_verified": False,
        },
        "rejection_reason": "",
        "caveats": _dedupe_preserve_order(
            _request_caveats(request) + _record_caveats(record) + ["metadata-only candidate; company hint is not verified"]
        ),
        "not_for_trading_advice": True,
    }
    return normalize_official_disclosure_discovery_candidate(candidate)


def build_rejected_discovery_record(
    record: Any, reasons: Sequence[str], *, record_index: int | None = None
) -> dict[str, Any]:
    """Build a sanitized rejected-record outcome."""

    rejected = {
        "record": _safe_record_snapshot(record, record_index=record_index),
        "reasons": _dedupe_preserve_order([_clean_string(reason) for reason in reasons if _clean_string(reason)]),
        "not_for_trading_advice": True,
    }
    if not rejected["reasons"]:
        rejected["reasons"] = [REASON_INVALID_REQUEST]
    return rejected


def dedupe_discovery_candidates(
    candidates: Sequence[Mapping[str, Any]]
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    """Dedupe exact candidate identities and flag same-URL conflicts for review."""

    deduped: list[dict[str, Any]] = []
    seen_identities: set[tuple[Any, ...]] = set()
    seen_by_url: dict[str, tuple[Any, ...]] = {}
    blocked_reasons: list[str] = []
    caveats: list[str] = []

    for candidate in candidates:
        normalized = dict(candidate)
        identity = _candidate_identity(normalized)
        source_url = _clean_string(normalized.get("source_url"))
        if identity in seen_identities:
            caveats.append("duplicate exact metadata candidate deduped")
            continue
        if source_url in seen_by_url and seen_by_url[source_url] != identity:
            blocked_reasons.append(REASON_AMBIGUOUS_DUPLICATE_REVIEW_REQUIRED)
            caveats.append("same official URL has conflicting metadata and requires review")
        seen_identities.add(identity)
        seen_by_url[source_url] = identity
        deduped.append(normalized)

    return deduped, _dedupe_preserve_order(blocked_reasons), _dedupe_preserve_order(caveats)


def build_discovery_blocked_result(
    *,
    request: Mapping[str, Any] | None,
    input_metadata_records: Sequence[Any],
    discovery_candidates: Sequence[Mapping[str, Any]],
    rejected_records: Sequence[Mapping[str, Any]],
    blocked_reasons: Sequence[str],
    caveats: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Build a fail-closed adapter result."""

    result = {
        "schema_version": SCHEMA_VERSION,
        "request": dict(request) if isinstance(request, Mapping) else {},
        "input_metadata_records": list(input_metadata_records),
        "discovery_candidates": [dict(candidate) for candidate in discovery_candidates],
        "rejected_records": [dict(record) for record in rejected_records],
        "blocked_reasons": _dedupe_preserve_order([_clean_string(reason) for reason in blocked_reasons if _clean_string(reason)]),
        "caveats": _dedupe_preserve_order([_clean_string(caveat) for caveat in (caveats or []) if _clean_string(caveat)]),
        "not_for_trading_advice": True,
    }
    if not result["blocked_reasons"]:
        result["blocked_reasons"] = [REASON_NO_CANDIDATES_FOUND]
    validate_official_source_discovery_adapter_result(result)
    return result


def assert_no_official_source_discovery_forbidden_markers(value: Any) -> None:
    """Recursively reject forbidden live, IO, parser, metric, and advice markers."""

    _assert_no_markers(value, path="$")


def _validate_request_for_adapter(request: Any) -> tuple[dict[str, Any], list[str]]:
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
        reasons.extend([f"request:{reason}" for reason in validated.get("blocked_reasons", []) if reason])
    return dict(validated), _dedupe_preserve_order(reasons)


def _request_match_reasons(request: Mapping[str, Any], record: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    if _clean_string(record.get("stock_code")) != _clean_string(request.get("stock_code")):
        reasons.append(REASON_STOCK_CODE_MISMATCH)
    if _clean_string(record.get("exchange")) != _clean_string(request.get("exchange")):
        reasons.append(REASON_EXCHANGE_MISMATCH)
    if _clean_string(record.get("period_key")) != _clean_string(request.get("query_period")):
        reasons.append(REASON_PERIOD_KEY_MISMATCH)
    if _clean_string(record.get("period_end_date")) != _clean_string(request.get("period_end_date")):
        reasons.append(REASON_PERIOD_END_DATE_MISMATCH)
    if _clean_string(record.get("announcement_type")) != _clean_string(request.get("requested_announcement_type")):
        reasons.append(REASON_ANNOUNCEMENT_TYPE_MISMATCH)

    request_company = _clean_string(request.get("company_name"))
    record_company = _clean_string(record.get("company_name"))
    if request_company and record_company and request_company != record_company:
        reasons.append(REASON_COMPANY_NAME_MISMATCH)
    return reasons


def _redirect_chain_reasons(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        return [REASON_REDIRECT_CHAIN_NOT_LIST]
    reasons: list[str] = []
    for redirect_url in value:
        if not isinstance(redirect_url, str):
            reasons.append(REASON_MALFORMED_URL)
            continue
        _assert_url_has_no_secret_marker(redirect_url, path="$.redirect_chain")
        parsed = _parse_official_url(redirect_url)
        if not parsed:
            reasons.append(REASON_MALFORMED_URL)
        elif parsed["host"] not in ALLOWED_DOMAINS:
            reasons.append(REASON_REDIRECT_DOMAIN_NOT_ALLOWED)
    return _dedupe_preserve_order(reasons)


def _parse_official_url(value: Any) -> dict[str, str] | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    try:
        parsed = urlparse(raw)
        _ = parsed.port
    except ValueError:
        return None
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    if parsed.username or parsed.password or "@" in parsed.netloc:
        return None
    if "%" in parsed.netloc or "\\" in parsed.netloc:
        return None
    host = (parsed.hostname or "").strip().lower().rstrip(".")
    if not host or "%" in host or not _HOST_RE.fullmatch(host):
        return None
    return {"url": raw, "host": host}


def _normalize_domain_host(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    if "://" in raw:
        parsed = _parse_official_url(raw)
        return parsed["host"] if parsed else None
    if any(separator in raw for separator in ("/", "\\", "?", "#", "@", "%", ":")):
        return None
    host = raw.lower().rstrip(".")
    if not host or not _HOST_RE.fullmatch(host):
        return None
    return host


def _raw_candidate_metadata(record: Mapping[str, Any]) -> dict[str, Any]:
    metadata = {field: record[field] for field in METADATA_RECORD_FIELDS if field in record}
    metadata["adapter_schema_version"] = SCHEMA_VERSION
    return metadata


def _safe_metadata_records_snapshot(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [_safe_record_snapshot(record, record_index=index) for index, record in enumerate(value)]


def _safe_record_snapshot(record: Any, *, record_index: int | None = None) -> dict[str, Any]:
    snapshot: dict[str, Any] = {}
    if record_index is not None:
        snapshot["record_index"] = record_index
    if not isinstance(record, Mapping):
        snapshot["record_omitted"] = True
        snapshot["not_for_trading_advice"] = True
        return snapshot

    for field in METADATA_RECORD_FIELDS:
        if field not in record:
            continue
        value = record[field]
        if field in {"source_url", "redirect_chain"}:
            snapshot[field] = _sanitize_url_value(value)
            continue
        if _value_has_forbidden_marker(value):
            snapshot[f"{field}_omitted"] = True
            continue
        snapshot[field] = _copy_jsonlike(value)
    return snapshot


def _sanitize_url_value(value: Any) -> Any:
    if isinstance(value, list):
        return [_sanitize_url_value(item) for item in value]
    if not isinstance(value, str):
        return value
    try:
        _assert_url_has_no_secret_marker(value, path="$")
    except OfficialVerificationValidationError:
        return "[omitted:unsafe_url]"
    return value


def _copy_jsonlike(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _copy_jsonlike(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_copy_jsonlike(item) for item in value]
    if isinstance(value, tuple):
        return [_copy_jsonlike(item) for item in value]
    return value


def _assert_no_forbidden_metadata_fields(record: Mapping[str, Any]) -> None:
    for key, value in record.items():
        normalized_key = _normalize_marker_text(key)
        if normalized_key in FORBIDDEN_METADATA_FIELDS:
            raise OfficialVerificationValidationError(f"forbidden metadata field: {key}")
        if isinstance(value, Mapping):
            _assert_no_forbidden_metadata_fields(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, Mapping):
                    _assert_no_forbidden_metadata_fields(item)


def _assert_no_markers(value: Any, *, path: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized_key = _normalize_marker_text(key)
            if str(key) != "not_for_trading_advice" and _key_has_forbidden_marker(normalized_key):
                raise OfficialVerificationValidationError(f"forbidden source discovery marker key at {path}.{key}")
            if str(key) == "source_url":
                _assert_url_has_no_secret_marker(item, path=f"{path}.{key}")
            elif str(key) == "redirect_chain":
                _assert_redirect_chain_has_no_secret_marker(item, path=f"{path}.{key}")
            else:
                _assert_no_markers(item, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_no_markers(item, path=f"{path}[{index}]")
    elif isinstance(value, str):
        marker = _string_forbidden_marker(value)
        if marker:
            raise OfficialVerificationValidationError(f"forbidden source discovery marker value at {path}: {marker}")


def _assert_url_has_no_secret_marker(value: Any, *, path: str) -> None:
    if not isinstance(value, str):
        return
    lowered = value.casefold()
    if "tushare_token" in lowered or ".env" in lowered or re.search(r"\btoken\b", lowered):
        raise OfficialVerificationValidationError(f"forbidden source discovery marker value at {path}")


def _assert_redirect_chain_has_no_secret_marker(value: Any, *, path: str) -> None:
    if isinstance(value, list):
        for index, item in enumerate(value):
            _assert_url_has_no_secret_marker(item, path=f"{path}[{index}]")
    else:
        _assert_no_markers(value, path=path)


def _assert_adapter_result_metadata_has_no_forbidden_markers(result: Mapping[str, Any]) -> None:
    for field in ("input_metadata_records", "caveats"):
        _assert_no_markers(result.get(field, []), path=f"$.{field}")
    for index, rejected in enumerate(result.get("rejected_records", [])):
        if isinstance(rejected, Mapping):
            _assert_no_markers(rejected.get("record", {}), path=f"$.rejected_records[{index}].record")


def _value_has_forbidden_marker(value: Any) -> bool:
    try:
        _assert_no_markers(value, path="$")
    except OfficialVerificationValidationError:
        return True
    return False


def _key_has_forbidden_marker(normalized_key: str) -> bool:
    compact_key = normalized_key.replace("_", "")
    for marker in _all_marker_phrases():
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
        if normalized_marker in _SHORT_WORD_MARKERS:
            if normalized_marker in normalized_key.split("_"):
                return True
            continue
        if normalized_marker and (normalized_marker in normalized_key or compact_marker in compact_key):
            return True
    return False


def _string_forbidden_marker(value: str) -> str:
    for marker in _DISCOVERY_FORBIDDEN_CJK_MARKERS:
        if marker in value:
            return marker
    lowered = value.casefold()
    normalized = _normalize_marker_text(value)
    if "tushare_token" in lowered:
        return "tushare_token"
    if ".env" in lowered:
        return ".env"
    if re.search(r"\btoken\b", lowered):
        return "token"
    if _STANDALONE_HTTP_RE.search(value):
        return "HTTP"
    for marker in _DISCOVERY_FORBIDDEN_ENGLISH_MARKERS:
        marker_norm = _normalize_marker_text(marker)
        if marker_norm in {"token", "env", "http"}:
            continue
        if marker_norm in _SHORT_WORD_MARKERS:
            if re.search(rf"\b{re.escape(marker_norm)}\b", lowered):
                return marker
            continue
        if marker_norm and marker_norm in normalized:
            return marker
    return ""


def _candidate_identity(candidate: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        candidate.get("stock_code"),
        candidate.get("exchange"),
        candidate.get("period_key"),
        candidate.get("period_end_date"),
        candidate.get("announcement_type"),
        candidate.get("source_type"),
        candidate.get("source_url"),
        candidate.get("source_title"),
        candidate.get("disclosure_date"),
        candidate.get("source_domain"),
    )


def _request_caveats(request: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(request, Mapping) or not isinstance(request.get("caveats"), list):
        return []
    return [_clean_string(caveat) for caveat in request["caveats"] if _clean_string(caveat)]


def _record_caveats(record: Mapping[str, Any]) -> list[str]:
    caveats = record.get("caveats")
    if not isinstance(caveats, list):
        return []
    return [_clean_string(caveat) for caveat in caveats if _clean_string(caveat)]


def _clean_string(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _dedupe_preserve_order(values: Sequence[Any]) -> list[Any]:
    seen: set[Any] = set()
    deduped: list[Any] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped


def _normalize_marker_text(value: Any) -> str:
    raw = _clean_string(value)
    camel_split = _CAMEL_SPLIT_RE.sub("_", raw)
    lowered = camel_split.casefold()
    lowered = re.sub(r"[\s\-\.]+", "_", lowered)
    lowered = re.sub(r"_+", "_", lowered).strip("_")
    return lowered


def _all_marker_phrases() -> tuple[str, ...]:
    return _DISCOVERY_FORBIDDEN_ENGLISH_MARKERS + _DISCOVERY_FORBIDDEN_CJK_MARKERS
