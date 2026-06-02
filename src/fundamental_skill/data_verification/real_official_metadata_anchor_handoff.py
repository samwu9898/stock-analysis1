# -*- coding: utf-8 -*-
"""Real official metadata discovery handoff for disclosure anchors.

This module is the thin metadata-only bridge from an official disclosure
request to real official metadata records, the existing discovery adapter, and
the existing provider metric anchor map. It does not create official facts,
provider conflicts, reports, baselines, fixtures, manifests, or PDF-derived
content.
"""

from __future__ import annotations

import copy
import json
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from .official_disclosure_request import validate_official_disclosure_request
from .official_source_discovery_adapter import (
    discover_official_sources_from_metadata,
    validate_official_source_discovery_adapter_result,
)
from .provider_metric_official_anchor import (
    ProviderMetricOfficialAnchorError,
    build_provider_metric_official_disclosure_anchor_map,
    validate_provider_metric_official_disclosure_anchor_map,
)
from .validators import OfficialVerificationValidationError


HANDOFF_RESULT_SCHEMA_VERSION = "real_official_metadata_anchor_handoff_result.v1"
DISCOVERY_RESULT_SCHEMA_VERSION = "real_official_metadata_discovery_result.v1"
METADATA_RECORD_SCHEMA_VERSION = "real_official_metadata_record.v1"
OFFICIAL_METADATA_CANDIDATE_SCHEMA_VERSION = "official_disclosure_metadata_candidate.v1"

SOURCE_FAMILY_CNINFO = "cninfo"
SUPPORTED_SOURCE_FAMILIES = (SOURCE_FAMILY_CNINFO,)

CNINFO_METADATA_ENDPOINT = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
ALLOWED_CNINFO_METADATA_REQUEST_HOSTS = ("www.cninfo.com.cn",)
ALLOWED_CNINFO_METADATA_SOURCE_HOSTS = (
    "www.cninfo.com.cn",
    "static.cninfo.com.cn",
)
CNINFO_SOURCE_TYPE = "cninfo_official_pdf"
CNINFO_DISCOVERY_METHOD = "cninfo_search_result"
MAX_METADATA_RESPONSE_BYTES = 2_000_000

REASON_MISSING_REQUEST = "missing_request"
REASON_INVALID_REQUEST = "invalid_request"
REASON_REQUEST_BLOCKED = "request_blocked"
REASON_UNSUPPORTED_SOURCE_FAMILY = "unsupported_source_family"
REASON_ALLOW_NETWORK_FALSE = "allow_network_false"
REASON_OFFICIAL_HTTP_CLIENT_MISSING = "official_http_client_missing"
REASON_NON_ALLOWLIST_REQUEST_HOST = "non_allowlist_request_host"
REASON_TRANSPORT_ERROR = "official_metadata_transport_error"
REASON_TIMEOUT = "official_metadata_timeout"
REASON_MALFORMED_RESPONSE = "malformed_response"
REASON_EMPTY_RESPONSE = "empty_response"
REASON_MISSING_METADATA = "missing_metadata"
REASON_MISSING_REQUIRED_METADATA = "missing_required_metadata"
REASON_NON_ALLOWLIST_SOURCE_URL = "non_allowlist_source_url"
REASON_FORBIDDEN_SOURCE_DOMAIN = "forbidden_source_domain"
REASON_ANNOUNCEMENT_NOT_MATCHING_REQUEST = "announcement_not_matching_request"
REASON_UNSUPPORTED_CNINFO_PERIOD = "unsupported_cninfo_period"
REASON_FORBIDDEN_MARKER_DETECTED = "forbidden_marker_detected"
REASON_ADAPTER_HANDOFF_REJECTED = "adapter_handoff_rejected"
REASON_ANCHOR_MAP_HANDOFF_REJECTED = "anchor_map_handoff_rejected"
REASON_ANCHOR_MAP_NOT_FULLY_MATCHED = "anchor_map_not_fully_matched"

FORBIDDEN_SOURCE_DOMAIN_SUFFIXES = (
    "eastmoney.com",
    "eastmoney.com.cn",
    "sina.com.cn",
    "10jqka.com.cn",
    "hexun.com",
    "jrj.com.cn",
    "baidu.com",
    "google.com",
    "bing.com",
    "so.com",
    "sogou.com",
)

_CNINFO_CATEGORY_BY_PERIOD_SUFFIX = {
    "FY": "category_ndbg_szsh",
    "H1": "category_bndbg_szsh",
    "Q1": "category_yjdbg_szsh",
    "Q3": "category_sjdbg_szsh",
}
_CNINFO_COLUMN_BY_EXCHANGE = {
    "SSE": "sse",
    "SZSE": "szse",
    "BSE": "bj",
}
_CNINFO_STOCK_PREFIX_BY_EXCHANGE = {
    "SSE": "gssh",
    "SZSE": "gssz",
    "BSE": "gssb",
}

_FORBIDDEN_ENGLISH_MARKERS = (
    "token",
    ".env",
    "tushare_token",
    "official_verified",
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
    "download",
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
    "\u4e0b\u8f7d",
    "\u89e3\u6790PDF",
    "PDF\u89e3\u6790",
    "\u8868\u683c\u62bd\u53d6",
    "\u6307\u6807\u62bd\u53d6",
)
_WORD_MARKERS = {
    "token",
    "buy",
    "sell",
    "hold",
    "portfolio",
    "position",
    "download",
}
_IDENTIFIER_SAFE_WORD_MARKERS = {"buy", "sell", "hold"}
_CAMEL_SPLIT_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_DATE_RE = re.compile(r"(?P<date>20\d{2}[-/]\d{1,2}[-/]\d{1,2})")
_HTML_TAG_RE = re.compile(r"<[^>]+>")


class RealOfficialMetadataAnchorHandoffError(ValueError):
    """Raised when the metadata handoff must fail closed."""


class RealOfficialMetadataHandoffSafetyError(RealOfficialMetadataAnchorHandoffError):
    """Raised when explicit nested input contains a forbidden marker."""

    def __init__(self, marker: str) -> None:
        super().__init__("forbidden_marker")
        self.marker = marker


def build_real_official_metadata_anchor_handoff(
    request: Any,
    provider_queue: Any,
    *,
    official_http_client: Any = None,
    allow_network: bool = False,
) -> dict[str, Any]:
    """Build a metadata-only official-anchor handoff result."""

    try:
        assert_no_real_official_metadata_handoff_forbidden_markers(request)
        assert_no_real_official_metadata_handoff_forbidden_markers(provider_queue)
    except RealOfficialMetadataHandoffSafetyError:
        result = _build_handoff_result(
            request={},
            source_family=SOURCE_FAMILY_CNINFO,
            metadata_records=[],
            discovery_adapter_result={},
            anchor_map_result={},
            blocked_reasons=[REASON_FORBIDDEN_MARKER_DETECTED],
            caveats=[],
        )
        validate_real_official_metadata_anchor_handoff_result(result)
        return result

    validated_request, request_reasons = _validate_request_for_handoff(request)
    source_family = _source_family_from_request(request)
    if source_family not in SUPPORTED_SOURCE_FAMILIES:
        request_reasons.append(REASON_UNSUPPORTED_SOURCE_FAMILY)

    if request_reasons:
        result = _build_handoff_result(
            request=validated_request,
            source_family=source_family,
            metadata_records=[],
            discovery_adapter_result={},
            anchor_map_result={},
            blocked_reasons=request_reasons,
            caveats=[],
        )
        validate_real_official_metadata_anchor_handoff_result(result)
        return result

    discovery_result = fetch_real_official_metadata_records_for_request(
        validated_request,
        official_http_client=official_http_client,
        allow_network=allow_network,
    )
    records = discovery_result.get("metadata_records", [])

    adapter_result: dict[str, Any] = {}
    anchor_map_result: dict[str, Any] = {}
    handoff_blocked: list[str] = []
    handoff_caveats: list[str] = list(discovery_result.get("caveats", []))

    if not _network_policy_blocked(discovery_result):
        anchor_handoff = build_anchor_map_from_real_metadata(
            validated_request,
            provider_queue,
            records,
        )
        adapter_result = dict(anchor_handoff.get("discovery_adapter_result", {}))
        anchor_map_result = dict(anchor_handoff.get("anchor_map_result", {}))
        handoff_blocked.extend(anchor_handoff.get("blocked_reasons", []))
        handoff_caveats.extend(anchor_handoff.get("caveats", []))

    result = _build_handoff_result(
        request=validated_request,
        source_family=source_family,
        metadata_records=records,
        discovery_adapter_result=adapter_result,
        anchor_map_result=anchor_map_result,
        blocked_reasons=list(discovery_result.get("blocked_reasons", [])) + handoff_blocked,
        caveats=handoff_caveats,
    )
    validate_real_official_metadata_anchor_handoff_result(result)
    return result


def fetch_real_official_metadata_records_for_request(
    request: Any,
    *,
    official_http_client: Any = None,
    allow_network: bool = False,
) -> dict[str, Any]:
    """Fetch official metadata records for the supported source family."""

    source_family = _source_family_from_request(request)
    if source_family != SOURCE_FAMILY_CNINFO:
        return _build_discovery_result(
            request=request if isinstance(request, Mapping) else {},
            metadata_request={},
            metadata_records=[],
            rejected_records=[],
            blocked_reasons=[REASON_UNSUPPORTED_SOURCE_FAMILY],
            caveats=[],
        )
    return fetch_cninfo_metadata_for_request(
        request,
        official_http_client=official_http_client,
        allow_network=allow_network,
    )


def fetch_cninfo_metadata_for_request(
    request: Any,
    *,
    official_http_client: Any = None,
    allow_network: bool = False,
) -> dict[str, Any]:
    """Fetch CNInfo announcement-list metadata with a fixed allowlisted host."""

    validated_request, request_reasons = _validate_request_for_handoff(request)
    metadata_request = build_cninfo_metadata_request(validated_request)

    if request_reasons:
        return _build_discovery_result(
            request=validated_request,
            metadata_request=metadata_request,
            metadata_records=[],
            rejected_records=[],
            blocked_reasons=request_reasons,
            caveats=[],
        )

    request_host = _domain_from_url(metadata_request.get("url"))
    if request_host not in ALLOWED_CNINFO_METADATA_REQUEST_HOSTS:
        return _build_discovery_result(
            request=validated_request,
            metadata_request=metadata_request,
            metadata_records=[],
            rejected_records=[],
            blocked_reasons=[REASON_NON_ALLOWLIST_REQUEST_HOST],
            caveats=[],
        )

    if not metadata_request.get("form_data"):
        return _build_discovery_result(
            request=validated_request,
            metadata_request=metadata_request,
            metadata_records=[],
            rejected_records=[],
            blocked_reasons=[REASON_UNSUPPORTED_CNINFO_PERIOD],
            caveats=[],
        )

    if allow_network is not True:
        reasons = [REASON_ALLOW_NETWORK_FALSE]
        if official_http_client is None:
            reasons.append(REASON_OFFICIAL_HTTP_CLIENT_MISSING)
        return _build_discovery_result(
            request=validated_request,
            metadata_request=metadata_request,
            metadata_records=[],
            rejected_records=[],
            blocked_reasons=reasons,
            caveats=[],
        )

    client = official_http_client or _default_cninfo_http_client
    try:
        response = _invoke_official_http_client(client, metadata_request)
    except (TimeoutError, socket.timeout):
        return _build_discovery_result(
            request=validated_request,
            metadata_request=metadata_request,
            metadata_records=[],
            rejected_records=[],
            blocked_reasons=[REASON_TIMEOUT],
            caveats=[],
        )
    except Exception:
        return _build_discovery_result(
            request=validated_request,
            metadata_request=metadata_request,
            metadata_records=[],
            rejected_records=[],
            blocked_reasons=[REASON_TRANSPORT_ERROR],
            caveats=[],
        )

    return normalize_cninfo_metadata_response(response, validated_request)


def build_cninfo_metadata_request(request: Mapping[str, Any]) -> dict[str, Any]:
    """Derive the fixed CNInfo metadata endpoint request from the disclosure request."""

    if not isinstance(request, Mapping):
        return {
            "method": "POST",
            "url": CNINFO_METADATA_ENDPOINT,
            "host": "www.cninfo.com.cn",
            "form_data": {},
            "not_official_verified": True,
            "not_for_trading_advice": True,
        }

    query_period = _clean_string(request.get("query_period"))
    suffix = _period_suffix(query_period)
    category = _CNINFO_CATEGORY_BY_PERIOD_SUFFIX.get(suffix)
    exchange = _clean_string(request.get("exchange"))
    stock_code = _clean_string(request.get("stock_code"))
    column = _CNINFO_COLUMN_BY_EXCHANGE.get(exchange, "")
    stock = _cninfo_stock_param(stock_code, exchange)
    form_data: dict[str, str] = {}
    if category and column and stock:
        form_data = {
            "stock": stock,
            "tabName": "fulltext",
            "pageSize": "30",
            "pageNum": "1",
            "column": column,
            "category": category,
            "seDate": _cninfo_search_date_range(request),
            "isHLtitle": "true",
        }

    return {
        "method": "POST",
        "url": CNINFO_METADATA_ENDPOINT,
        "host": "www.cninfo.com.cn",
        "form_data": form_data,
        "metadata_only": True,
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }


def normalize_cninfo_metadata_response(
    response: Any,
    request: Any,
) -> dict[str, Any]:
    """Normalize a CNInfo metadata response into official metadata records."""

    validated_request, request_reasons = _validate_request_for_handoff(request)
    metadata_request = build_cninfo_metadata_request(validated_request)
    if request_reasons:
        return _build_discovery_result(
            request=validated_request,
            metadata_request=metadata_request,
            metadata_records=[],
            rejected_records=[],
            blocked_reasons=request_reasons,
            caveats=[],
        )

    announcements = _extract_cninfo_announcements(response)
    if announcements is None:
        return _build_discovery_result(
            request=validated_request,
            metadata_request=metadata_request,
            metadata_records=[],
            rejected_records=[],
            blocked_reasons=[REASON_MALFORMED_RESPONSE],
            caveats=[],
        )
    if not announcements:
        return _build_discovery_result(
            request=validated_request,
            metadata_request=metadata_request,
            metadata_records=[],
            rejected_records=[],
            blocked_reasons=[REASON_EMPTY_RESPONSE, REASON_MISSING_METADATA],
            caveats=[],
        )

    records: list[dict[str, Any]] = []
    rejected_records: list[dict[str, Any]] = []
    for index, announcement in enumerate(announcements):
        record, reasons = _normalize_cninfo_announcement(
            announcement,
            validated_request,
            record_index=index,
        )
        if record and not reasons:
            records.append(record)
            continue
        if reasons:
            rejected_records.append(
                {
                    "record_index": index,
                    "reasons": _dedupe_preserve_order(reasons),
                    "not_official_verified": True,
                    "not_for_trading_advice": True,
                }
            )

    blocked_reasons: list[str] = []
    if not records:
        blocked_reasons.append(REASON_MISSING_METADATA)
        for rejected in rejected_records:
            blocked_reasons.extend(rejected.get("reasons", []))

    return _build_discovery_result(
        request=validated_request,
        metadata_request=metadata_request,
        metadata_records=records,
        rejected_records=rejected_records,
        blocked_reasons=blocked_reasons,
        caveats=[],
    )


def build_official_metadata_candidates_from_records(
    records: Any,
) -> list[dict[str, Any]]:
    """Build anchor-map metadata candidates from explicit metadata records."""

    assert_no_real_official_metadata_handoff_forbidden_markers(records)
    if not isinstance(records, list):
        return []

    candidates: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, Mapping):
            continue
        source_url = _clean_string(record.get("source_url"))
        source_domain = _normalize_domain(record.get("source_domain")) or _domain_from_url(source_url)
        candidates.append(
            {
                "schema_version": OFFICIAL_METADATA_CANDIDATE_SCHEMA_VERSION,
                "source_title": _clean_string(record.get("source_title")),
                "source_url": source_url,
                "source_domain": source_domain,
                "disclosure_date": _clean_string(record.get("disclosure_date")),
                "stock_code": _clean_string(record.get("stock_code")),
                "company_name_hint": _clean_string(
                    record.get("company_name_hint") or record.get("company_name")
                ),
                "period_key": _clean_string(record.get("period_key")),
                "period_end_date": _clean_string(record.get("period_end_date")),
                "announcement_type": _clean_string(record.get("announcement_type")),
                "source_type": _clean_string(record.get("source_type")),
                "not_official_verified": True,
                "not_for_trading_advice": True,
            }
        )
    return candidates


def build_anchor_map_from_real_metadata(
    request: Any,
    provider_queue: Any,
    records: Any,
) -> dict[str, Any]:
    """Hand real metadata through the existing adapter and anchor map."""

    try:
        assert_no_real_official_metadata_handoff_forbidden_markers(records)
    except RealOfficialMetadataHandoffSafetyError:
        return {
            "discovery_adapter_result": {},
            "official_metadata_candidates": [],
            "anchor_map_result": {},
            "blocked_reasons": [REASON_FORBIDDEN_MARKER_DETECTED],
            "caveats": [],
            "not_official_verified": True,
            "not_for_trading_advice": True,
        }

    if not isinstance(records, list):
        records = []

    blocked_reasons: list[str] = []
    caveats: list[str] = []
    try:
        adapter_result = discover_official_sources_from_metadata(
            request,
            _adapter_handoff_records(records),
        )
    except OfficialVerificationValidationError:
        adapter_result = {}
        blocked_reasons.append(REASON_ADAPTER_HANDOFF_REJECTED)

    adapter_candidates = _build_candidates_from_adapter_result(adapter_result)
    if isinstance(adapter_result, Mapping) and adapter_result.get("blocked_reasons"):
        blocked_reasons.append(REASON_ADAPTER_HANDOFF_REJECTED)
        blocked_reasons.extend(
            f"adapter:{reason}"
            for reason in adapter_result.get("blocked_reasons", [])
            if _clean_string(reason)
        )

    try:
        anchor_map_result = build_provider_metric_official_disclosure_anchor_map(
            provider_queue,
            adapter_candidates,
        )
    except ProviderMetricOfficialAnchorError:
        anchor_map_result = {}
        blocked_reasons.append(REASON_ANCHOR_MAP_HANDOFF_REJECTED)

    if isinstance(anchor_map_result, Mapping):
        anchor_blocked = anchor_map_result.get("blocked_reasons", [])
        if isinstance(anchor_blocked, list) and anchor_blocked:
            blocked_reasons.append(REASON_ANCHOR_MAP_HANDOFF_REJECTED)
            blocked_reasons.extend(
                f"anchor_map:{reason}"
                for reason in anchor_blocked
                if _clean_string(reason)
            )
        non_matched_statuses = [
            item.get("official_anchor_status")
            for item in anchor_map_result.get("anchor_items", [])
            if isinstance(item, Mapping)
            and item.get("official_anchor_status") != "matched"
        ]
        if non_matched_statuses:
            blocked_reasons.append(REASON_ANCHOR_MAP_NOT_FULLY_MATCHED)
            caveats.extend(f"anchor_status:{status}" for status in non_matched_statuses if status)
        caveats.extend(anchor_map_result.get("caveats", []))

    return {
        "discovery_adapter_result": dict(adapter_result),
        "official_metadata_candidates": adapter_candidates,
        "anchor_map_result": dict(anchor_map_result),
        "blocked_reasons": _dedupe_preserve_order(blocked_reasons),
        "caveats": _dedupe_preserve_order(caveats),
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }


def validate_real_official_metadata_anchor_handoff_result(result: Any) -> None:
    """Validate handoff result shape and safety constraints."""

    if not isinstance(result, Mapping):
        raise RealOfficialMetadataAnchorHandoffError("handoff_result_must_be_mapping")
    required = (
        "schema_version",
        "request",
        "source_family",
        "target_ts_code",
        "target_stock_code",
        "target_periods",
        "metadata_records",
        "discovery_adapter_result",
        "anchor_map_result",
        "live_smoke_summary",
        "blocked_reasons",
        "caveats",
        "not_official_verified",
        "not_for_trading_advice",
    )
    missing = [key for key in required if key not in result]
    if missing:
        raise RealOfficialMetadataAnchorHandoffError(f"handoff_result_missing:{missing}")
    if result.get("schema_version") != HANDOFF_RESULT_SCHEMA_VERSION:
        raise RealOfficialMetadataAnchorHandoffError("invalid_handoff_schema_version")
    if result.get("source_family") not in SUPPORTED_SOURCE_FAMILIES:
        raise RealOfficialMetadataAnchorHandoffError("invalid_source_family")
    if result.get("not_official_verified") is not True:
        raise RealOfficialMetadataAnchorHandoffError("not_official_verified_required")
    if result.get("not_for_trading_advice") is not True:
        raise RealOfficialMetadataAnchorHandoffError("not_for_trading_advice_required")
    for field in ("target_periods", "metadata_records", "blocked_reasons", "caveats"):
        if not isinstance(result.get(field), list):
            raise RealOfficialMetadataAnchorHandoffError(f"{field}_must_be_list")
    if not isinstance(result.get("request"), Mapping):
        raise RealOfficialMetadataAnchorHandoffError("request_must_be_mapping")
    if not isinstance(result.get("discovery_adapter_result"), Mapping):
        raise RealOfficialMetadataAnchorHandoffError("adapter_result_must_be_mapping")
    if not isinstance(result.get("anchor_map_result"), Mapping):
        raise RealOfficialMetadataAnchorHandoffError("anchor_map_result_must_be_mapping")
    if not isinstance(result.get("live_smoke_summary"), Mapping):
        raise RealOfficialMetadataAnchorHandoffError("live_smoke_summary_must_be_mapping")

    adapter_result = result.get("discovery_adapter_result")
    if adapter_result:
        validate_official_source_discovery_adapter_result(adapter_result)
    anchor_map_result = result.get("anchor_map_result")
    if anchor_map_result:
        validate_provider_metric_official_disclosure_anchor_map(anchor_map_result)
    assert_no_real_official_metadata_handoff_forbidden_markers(result)


def assert_no_real_official_metadata_handoff_forbidden_markers(value: Any) -> None:
    """Recursively reject forbidden markers in handoff inputs and outputs."""

    marker = _find_forbidden_marker(value)
    if marker is not None:
        raise RealOfficialMetadataHandoffSafetyError(marker)


def _validate_request_for_handoff(request: Any) -> tuple[dict[str, Any], list[str]]:
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


def _source_family_from_request(request: Any) -> str:
    if isinstance(request, Mapping) and _clean_string(request.get("source_family")):
        return _clean_string(request.get("source_family"))
    return SOURCE_FAMILY_CNINFO


def _network_policy_blocked(discovery_result: Mapping[str, Any]) -> bool:
    reasons = discovery_result.get("blocked_reasons", [])
    return isinstance(reasons, list) and REASON_ALLOW_NETWORK_FALSE in reasons


def _build_handoff_result(
    *,
    request: Mapping[str, Any],
    source_family: str,
    metadata_records: Sequence[Mapping[str, Any]],
    discovery_adapter_result: Mapping[str, Any],
    anchor_map_result: Mapping[str, Any],
    blocked_reasons: Sequence[str],
    caveats: Sequence[str],
) -> dict[str, Any]:
    normalized_request = dict(request) if isinstance(request, Mapping) else {}
    records = [dict(record) for record in metadata_records]
    blocked = _dedupe_preserve_order(
        [_clean_string(reason) for reason in blocked_reasons if _clean_string(reason)]
    )
    result = {
        "schema_version": HANDOFF_RESULT_SCHEMA_VERSION,
        "request": normalized_request,
        "source_family": source_family or SOURCE_FAMILY_CNINFO,
        "target_ts_code": _target_ts_code(normalized_request),
        "target_stock_code": _clean_string(normalized_request.get("stock_code")),
        "target_periods": _target_periods(normalized_request),
        "metadata_records": records,
        "discovery_adapter_result": dict(discovery_adapter_result),
        "anchor_map_result": dict(anchor_map_result),
        "live_smoke_summary": _build_live_smoke_summary(
            normalized_request,
            records,
            discovery_adapter_result,
            anchor_map_result,
            blocked,
            caveats,
        ),
        "blocked_reasons": blocked,
        "caveats": _dedupe_preserve_order(
            [_clean_string(caveat) for caveat in caveats if _clean_string(caveat)]
        ),
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }
    return result


def _build_discovery_result(
    *,
    request: Mapping[str, Any],
    metadata_request: Mapping[str, Any],
    metadata_records: Sequence[Mapping[str, Any]],
    rejected_records: Sequence[Mapping[str, Any]],
    blocked_reasons: Sequence[str],
    caveats: Sequence[str],
) -> dict[str, Any]:
    result = {
        "schema_version": DISCOVERY_RESULT_SCHEMA_VERSION,
        "request": dict(request) if isinstance(request, Mapping) else {},
        "source_family": SOURCE_FAMILY_CNINFO,
        "metadata_request": dict(metadata_request),
        "metadata_records": [dict(record) for record in metadata_records],
        "rejected_records": [dict(record) for record in rejected_records],
        "blocked_reasons": _dedupe_preserve_order(
            [_clean_string(reason) for reason in blocked_reasons if _clean_string(reason)]
        ),
        "caveats": _dedupe_preserve_order(
            [_clean_string(caveat) for caveat in caveats if _clean_string(caveat)]
        ),
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }
    assert_no_real_official_metadata_handoff_forbidden_markers(result)
    return result


def _build_live_smoke_summary(
    request: Mapping[str, Any],
    records: Sequence[Mapping[str, Any]],
    adapter_result: Mapping[str, Any],
    anchor_map_result: Mapping[str, Any],
    blocked_reasons: Sequence[str],
    caveats: Sequence[str],
) -> dict[str, Any]:
    first_record = records[0] if records else {}
    anchor_items = anchor_map_result.get("anchor_items", []) if isinstance(anchor_map_result, Mapping) else []
    anchor_statuses = [
        item.get("official_anchor_status")
        for item in anchor_items
        if isinstance(item, Mapping)
    ]
    return {
        "request_target": {
            "ts_code": _target_ts_code(request),
            "stock_code": _clean_string(request.get("stock_code")),
            "query_period": _clean_string(request.get("query_period")),
            "period_end_date": _clean_string(request.get("period_end_date")),
            "announcement_type": _clean_string(request.get("requested_announcement_type")),
        },
        "metadata_records_found": bool(records),
        "metadata_records_count": len(records),
        "source_title": _clean_string(first_record.get("source_title")),
        "disclosure_date": _clean_string(first_record.get("disclosure_date")),
        "source_domain": _clean_string(first_record.get("source_domain")),
        "announcement_type": _clean_string(first_record.get("announcement_type")),
        "adapter_status": _adapter_status(adapter_result),
        "anchor_map_status": _anchor_map_status(anchor_statuses),
        "blocked_reasons_count": len(blocked_reasons),
        "caveats_count": len(caveats),
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }


def _adapter_status(adapter_result: Mapping[str, Any]) -> str:
    if not adapter_result:
        return "not_run"
    if adapter_result.get("blocked_reasons"):
        return "blocked"
    if adapter_result.get("discovery_candidates"):
        return "candidate_found"
    return "missing_metadata"


def _anchor_map_status(anchor_statuses: Sequence[Any]) -> str:
    statuses = [_clean_string(status) for status in anchor_statuses if _clean_string(status)]
    if not statuses:
        return "not_run"
    if all(status == "matched" for status in statuses):
        return "matched"
    return ",".join(_dedupe_preserve_order(statuses))


def _default_cninfo_http_client(metadata_request: Mapping[str, Any]) -> Any:
    encoded = urllib.parse.urlencode(metadata_request.get("form_data", {})).encode("utf-8")
    req = urllib.request.Request(
        _clean_string(metadata_request.get("url")),
        data=encoded,
        method="POST",
        headers={
            "Accept": "application/json,text/plain,*/*",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": "Mozilla/5.0 metadata-only official disclosure client",
            "Origin": "https://www.cninfo.com.cn",
            "Referer": "https://www.cninfo.com.cn/new/commonUrl/pageOfSearch",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            _assert_cninfo_metadata_final_host_allowed(response)
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if content_type and content_type not in {"application/json", "text/html", "text/plain"}:
                raise ValueError("unsupported_metadata_content_type")
            body = response.read(MAX_METADATA_RESPONSE_BYTES + 1)
    except urllib.error.URLError as exc:
        if isinstance(getattr(exc, "reason", None), socket.timeout):
            raise TimeoutError("metadata_timeout") from exc
        raise
    if len(body) > MAX_METADATA_RESPONSE_BYTES:
        raise ValueError("metadata_response_too_large")
    text = body.decode("utf-8", errors="replace").strip()
    return json.loads(text)


def _assert_cninfo_metadata_final_host_allowed(response: Any) -> None:
    geturl = getattr(response, "geturl", None)
    final_url = _clean_string(geturl()) if callable(geturl) else ""
    final_host = (urllib.parse.urlparse(final_url).hostname or "").strip().lower().rstrip(".")
    if final_host not in ALLOWED_CNINFO_METADATA_REQUEST_HOSTS:
        raise ValueError("non_allowlist_redirect_final_host")


def _invoke_official_http_client(client: Any, metadata_request: Mapping[str, Any]) -> Any:
    request_snapshot = copy.deepcopy(dict(metadata_request))
    if callable(client):
        return client(request_snapshot)
    if hasattr(client, "request"):
        return client.request(
            request_snapshot.get("method"),
            request_snapshot.get("url"),
            data=copy.deepcopy(request_snapshot.get("form_data", {})),
            headers={},
            timeout=15,
        )
    if hasattr(client, "post"):
        return client.post(
            request_snapshot.get("url"),
            data=copy.deepcopy(request_snapshot.get("form_data", {})),
            headers={},
            timeout=15,
        )
    raise TypeError("official_http_client_must_be_callable")


def _extract_cninfo_announcements(response: Any) -> list[Any] | None:
    normalized_response = _coerce_response_payload(response)
    if isinstance(normalized_response, list):
        return normalized_response
    if not isinstance(normalized_response, Mapping):
        return None

    announcements = normalized_response.get("announcements")
    if isinstance(announcements, list):
        return announcements

    nested = normalized_response.get("data")
    if isinstance(nested, Mapping):
        nested_announcements = nested.get("announcements")
        if isinstance(nested_announcements, list):
            return nested_announcements

    classified = normalized_response.get("classifiedAnnouncements")
    if isinstance(classified, list):
        flattened: list[Any] = []
        for group in classified:
            if isinstance(group, Mapping) and isinstance(group.get("announcements"), list):
                flattened.extend(group["announcements"])
        return flattened
    return None


def _coerce_response_payload(response: Any) -> Any:
    if hasattr(response, "json") and callable(response.json):
        return response.json()
    if isinstance(response, Mapping) and "json" in response:
        value = response.get("json")
        return value() if callable(value) else value
    if isinstance(response, (bytes, bytearray)):
        return json.loads(bytes(response).decode("utf-8", errors="replace"))
    if isinstance(response, str):
        return json.loads(response)
    return response


def _normalize_cninfo_announcement(
    announcement: Any,
    request: Mapping[str, Any],
    *,
    record_index: int,
) -> tuple[dict[str, Any] | None, list[str]]:
    if not isinstance(announcement, Mapping):
        return None, [REASON_MALFORMED_RESPONSE]

    try:
        assert_no_real_official_metadata_handoff_forbidden_markers(
            _announcement_safety_payload(announcement)
        )
    except RealOfficialMetadataHandoffSafetyError:
        return None, [REASON_FORBIDDEN_MARKER_DETECTED]

    source_title = _clean_cninfo_title(
        announcement.get("announcementTitle")
        or announcement.get("source_title")
        or announcement.get("title")
    )
    source_url = _normalize_cninfo_source_url(
        announcement.get("adjunctUrl")
        or announcement.get("source_url")
        or announcement.get("announcementUrl")
        or announcement.get("url")
    )
    source_domain = _domain_from_url(source_url)
    disclosure_date = _normalize_disclosure_date(
        announcement.get("announcementTime")
        or announcement.get("disclosure_date")
        or announcement.get("announcementDate")
    )
    stock_code = _clean_string(
        announcement.get("secCode")
        or announcement.get("stock_code")
        or announcement.get("stockCode")
        or request.get("stock_code")
    )
    company_name_hint = _clean_string(
        announcement.get("secName")
        or announcement.get("company_name_hint")
        or announcement.get("company_name")
        or request.get("company_name")
    )

    reasons: list[str] = []
    if not source_title or not source_url or not disclosure_date:
        reasons.append(REASON_MISSING_REQUIRED_METADATA)
    if source_domain not in ALLOWED_CNINFO_METADATA_SOURCE_HOSTS:
        reasons.append(REASON_NON_ALLOWLIST_SOURCE_URL)
    if _is_forbidden_source_domain(source_domain):
        reasons.append(REASON_FORBIDDEN_SOURCE_DOMAIN)
    if stock_code and stock_code != _clean_string(request.get("stock_code")):
        reasons.append(REASON_ANNOUNCEMENT_NOT_MATCHING_REQUEST)
    if not _announcement_matches_request(announcement, source_title, request):
        reasons.append(REASON_ANNOUNCEMENT_NOT_MATCHING_REQUEST)
    if reasons:
        return None, _dedupe_preserve_order(reasons)

    record = {
        "schema_version": METADATA_RECORD_SCHEMA_VERSION,
        "source_title": source_title,
        "source_url": source_url,
        "source_domain": source_domain,
        "disclosure_date": disclosure_date,
        "stock_code": _clean_string(request.get("stock_code")),
        "company_name": company_name_hint,
        "company_name_hint": company_name_hint,
        "exchange": _clean_string(request.get("exchange")),
        "period_key": _clean_string(request.get("query_period")),
        "period_end_date": _clean_string(request.get("period_end_date")),
        "announcement_type": _clean_string(request.get("requested_announcement_type")),
        "source_type": CNINFO_SOURCE_TYPE,
        "discovered_at_utc": _utc_now_string(),
        "discovery_method": CNINFO_DISCOVERY_METHOD,
        "redirect_chain": [],
        "caveats": ["pdf_url_preserved_metadata_only"]
        if source_url.casefold().split("?", 1)[0].endswith(".pdf")
        else [],
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }
    assert_no_real_official_metadata_handoff_forbidden_markers(record)
    return record, []


def _announcement_safety_payload(announcement: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "announcementTitle": announcement.get("announcementTitle")
        or announcement.get("source_title")
        or announcement.get("title"),
        "source_url": announcement.get("adjunctUrl")
        or announcement.get("source_url")
        or announcement.get("announcementUrl")
        or announcement.get("url"),
        "secCode": announcement.get("secCode") or announcement.get("stock_code"),
        "secName": announcement.get("secName") or announcement.get("company_name_hint"),
    }


def _announcement_matches_request(
    announcement: Mapping[str, Any],
    source_title: str,
    request: Mapping[str, Any],
) -> bool:
    if _is_cninfo_summary_title(source_title):
        return False

    explicit_type = _clean_string(announcement.get("announcement_type"))
    request_type = _clean_string(request.get("requested_announcement_type"))
    if explicit_type and explicit_type != request_type:
        return False

    explicit_period = _clean_string(announcement.get("period_key"))
    if explicit_period and explicit_period != _clean_string(request.get("query_period")):
        return False

    title = source_title.casefold()
    year = _clean_string(request.get("query_period"))[:4]
    if year and year not in title:
        return False

    if explicit_type == request_type or explicit_period == _clean_string(request.get("query_period")):
        return True
    if request_type == "annual_report":
        return "annual report" in title or "\u5e74\u5ea6\u62a5\u544a" in source_title
    if request_type == "semiannual_report":
        return (
            "semiannual report" in title
            or "semi-annual report" in title
            or "\u534a\u5e74\u5ea6\u62a5\u544a" in source_title
        )
    if request_type == "quarterly_report":
        suffix = _period_suffix(_clean_string(request.get("query_period")))
        if suffix == "Q1":
            return (
                "q1" in title
                or "first quarter" in title
                or "\u7b2c\u4e00\u5b63\u5ea6" in source_title
                or "\u4e00\u5b63\u5ea6" in source_title
            )
        if suffix == "Q3":
            return (
                "q3" in title
                or "third quarter" in title
                or "\u7b2c\u4e09\u5b63\u5ea6" in source_title
                or "\u4e09\u5b63\u5ea6" in source_title
            )
    return False


def _is_cninfo_summary_title(source_title: str) -> bool:
    title = source_title.casefold()
    return (
        "abstract" in title
        or "summary" in title
        or "\u6458\u8981" in source_title
    )


def _adapter_handoff_records(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    handoff_records: list[dict[str, Any]] = []
    for record in records:
        item = {key: _copy_jsonlike(value) for key, value in record.items()}
        item.pop("schema_version", None)
        item.pop("company_name", None)
        item.pop("company_name_hint", None)
        item.pop("not_official_verified", None)
        handoff_records.append(item)
    return handoff_records


def _build_candidates_from_adapter_result(adapter_result: Mapping[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(adapter_result, Mapping):
        return []
    candidates: list[dict[str, Any]] = []
    for candidate in adapter_result.get("discovery_candidates", []):
        if not isinstance(candidate, Mapping):
            continue
        candidates.append(
            {
                "schema_version": OFFICIAL_METADATA_CANDIDATE_SCHEMA_VERSION,
                "source_title": _clean_string(candidate.get("source_title")),
                "source_url": _clean_string(candidate.get("source_url")),
                "source_domain": _clean_string(candidate.get("source_domain")),
                "disclosure_date": _clean_string(candidate.get("disclosure_date")),
                "stock_code": _clean_string(candidate.get("stock_code")),
                "company_name_hint": _clean_string(candidate.get("company_name")),
                "period_key": _clean_string(candidate.get("period_key")),
                "period_end_date": _clean_string(candidate.get("period_end_date")),
                "announcement_type": _clean_string(candidate.get("announcement_type")),
                "source_type": _clean_string(candidate.get("source_type")),
                "not_official_verified": True,
                "not_for_trading_advice": True,
            }
        )
    return candidates


def _normalize_cninfo_source_url(value: Any) -> str:
    text = _clean_string(value)
    if not text:
        return ""
    if text.startswith("//"):
        return f"https:{text}"
    if text.startswith("http://") or text.startswith("https://"):
        return text
    return "https://static.cninfo.com.cn/" + text.lstrip("/")


def _normalize_disclosure_date(value: Any) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, (int, float)):
        seconds = float(value) / 1000 if float(value) > 10_000_000_000 else float(value)
        return datetime.fromtimestamp(seconds, tz=timezone.utc).date().isoformat()
    text = _clean_string(value)
    if text.isdigit():
        return _normalize_disclosure_date(int(text))
    match = _DATE_RE.search(text)
    if not match:
        return ""
    year, month, day = re.split(r"[-/]", match.group("date"))
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _clean_cninfo_title(value: Any) -> str:
    text = _HTML_TAG_RE.sub("", _clean_string(value))
    return re.sub(r"\s+", " ", text).strip()


def _cninfo_stock_param(stock_code: str, exchange: str) -> str:
    if not stock_code or not exchange:
        return ""
    prefix = _CNINFO_STOCK_PREFIX_BY_EXCHANGE.get(exchange)
    if not prefix:
        return ""
    return f"{stock_code},{prefix}0{stock_code}"


def _cninfo_search_date_range(request: Mapping[str, Any]) -> str:
    query_period = _clean_string(request.get("query_period"))
    year = int(query_period[:4]) if query_period[:4].isdigit() else datetime.now().year
    suffix = _period_suffix(query_period)
    disclosure_year = year + 1 if suffix == "FY" else year
    return f"{disclosure_year}-01-01~{disclosure_year}-12-31"


def _period_suffix(query_period: str) -> str:
    for suffix in ("FY", "H1", "Q1", "Q2", "Q3"):
        if query_period.endswith(suffix):
            return suffix
    return ""


def _target_ts_code(request: Mapping[str, Any]) -> str:
    stock_code = _clean_string(request.get("stock_code"))
    exchange = _clean_string(request.get("exchange"))
    suffix = {"SSE": "SH", "SZSE": "SZ", "BSE": "BJ"}.get(exchange)
    if stock_code and suffix:
        return f"{stock_code}.{suffix}"
    return stock_code


def _target_periods(request: Mapping[str, Any]) -> list[dict[str, Any]]:
    if not request:
        return []
    return [
        {
            "query_period": _clean_string(request.get("query_period")),
            "period_end_date": _clean_string(request.get("period_end_date")),
            "announcement_type": _clean_string(request.get("requested_announcement_type")),
        }
    ]


def _domain_from_url(source_url: Any) -> str:
    if source_url in (None, ""):
        return ""
    parsed = urlparse(str(source_url).strip())
    if parsed.scheme not in {"http", "https"}:
        return ""
    return (parsed.hostname or "").strip().lower().rstrip(".")


def _normalize_domain(value: Any) -> str:
    text = _clean_string(value).lower().rstrip(".")
    if not text:
        return ""
    if "://" in text:
        return _domain_from_url(text)
    if any(separator in text for separator in ("/", "\\", "?", "#", "@", "%", ":")):
        return ""
    return text


def _is_forbidden_source_domain(domain: str) -> bool:
    if not domain:
        return False
    return any(domain == suffix or domain.endswith(f".{suffix}") for suffix in FORBIDDEN_SOURCE_DOMAIN_SUFFIXES)


def _utc_now_string() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _find_forbidden_marker(value: Any, parent_key: str | None = None) -> str | None:
    if isinstance(value, Mapping):
        for key, nested_value in value.items():
            key_text = str(key)
            if key_text not in {"not_official_verified", "not_for_trading_advice", "source_url"}:
                if _text_has_forbidden_marker(key_text):
                    return key_text
            finding = _find_forbidden_marker(nested_value, parent_key=key_text)
            if finding is not None:
                return finding
        return None
    if isinstance(value, (list, tuple, set)):
        for nested_value in value:
            finding = _find_forbidden_marker(nested_value, parent_key=parent_key)
            if finding is not None:
                return finding
        return None
    if isinstance(value, str):
        if parent_key == "source_url":
            return value if _url_has_forbidden_secret_marker(value) else None
        if _text_has_forbidden_marker(value):
            return value
    return None


def _url_has_forbidden_secret_marker(value: str) -> bool:
    lowered = value.casefold()
    return (
        "tushare_token" in lowered
        or ".env" in lowered
        or re.search(r"\btoken\b", lowered) is not None
    )


def _text_has_forbidden_marker(value: str) -> bool:
    normalized = _normalize_marker_text(value)
    separator_normalized = _normalize_marker_text(re.sub(r"[_-]+", " ", value))
    if normalized == "not_official_verified":
        return False

    for marker in _FORBIDDEN_ENGLISH_MARKERS:
        marker_text = _normalize_marker_text(marker)
        if marker_text in _WORD_MARKERS:
            boundary_chars = "a-z0-9_" if marker_text in _IDENTIFIER_SAFE_WORD_MARKERS else "a-z0-9"
            if re.search(rf"(?<![{boundary_chars}]){re.escape(marker_text)}(?![{boundary_chars}])", normalized):
                return True
            continue
        if marker_text == "official_verified":
            if _contains_official_verified_marker(normalized):
                return True
            continue
        if marker_text and (marker_text in normalized or marker_text in separator_normalized):
            return True
    return any(marker in value for marker in _FORBIDDEN_CJK_MARKERS)


def _contains_official_verified_marker(value: str) -> bool:
    if value == "not_official_verified":
        return False
    return re.search(r"(?<!not_)official_verified", value) is not None


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


def _copy_jsonlike(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _copy_jsonlike(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_copy_jsonlike(item) for item in value]
    if isinstance(value, tuple):
        return [_copy_jsonlike(item) for item in value]
    return value


def _dedupe_preserve_order(values: Sequence[Any]) -> list[Any]:
    seen: set[Any] = set()
    result: list[Any] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
