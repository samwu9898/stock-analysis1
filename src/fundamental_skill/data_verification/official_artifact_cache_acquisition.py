# -*- coding: utf-8 -*-
"""Official disclosure artifact cache acquisition.

This standalone module consumes a matched official disclosure anchor map and
stores the referenced official PDF bytes in an explicitly supplied cache
directory. It records byte-level lineage and integrity metadata only.
"""

from __future__ import annotations

import copy
import hashlib
import os
import re
import socket
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


PROVIDER_NAME = "Tushare"
ANCHOR_MAP_SCHEMA_VERSION = "provider_metric_official_disclosure_anchor_map.v1"
ANCHOR_ITEM_SCHEMA_VERSION = "provider_metric_official_disclosure_anchor_item.v1"
ARTIFACT_CACHE_SCHEMA_VERSION = "official_disclosure_artifact_cache.v1"
ARTIFACT_CACHE_ITEM_SCHEMA_VERSION = "official_disclosure_artifact_cache_item.v1"
DOWNLOAD_RESULT_SCHEMA_VERSION = "official_disclosure_artifact_download_result.v1"
SOURCE_LINEAGE_SCHEMA_VERSION = "official_artifact_source_lineage.v1"

PENDING_OFFICIAL_VERIFICATION_STATUS = "pending_official_verification"
ANCHOR_EVIDENCE_STATUS = "official_anchor_candidate"
ANCHOR_STATUS_MATCHED = "matched"

ARTIFACT_STATUS_CACHED = "cached"
ARTIFACT_STATUS_SKIPPED = "skipped"
ARTIFACT_STATUS_BLOCKED = "blocked"
DOWNLOAD_STATUS_SUCCESS = "success"
DOWNLOAD_STATUS_BLOCKED = "blocked"
DOWNLOAD_STATUS_FAILED = "failed"

MAX_ARTIFACT_BYTES = 80 * 1024 * 1024
PDF_MAGIC_BYTES = b"%PDF-"
DEFAULT_TIMEOUT_SECONDS = 20

ALLOWED_OFFICIAL_ARTIFACT_DOMAINS = {
    "www.cninfo.com.cn",
    "static.cninfo.com.cn",
    "www.sse.com.cn",
    "www.szse.cn",
    "www.bse.cn",
}
ALLOWED_PDF_CONTENT_TYPES = {"application/pdf"}
CONDITIONAL_PDF_CONTENT_TYPES = {
    "",
    "application/octet-stream",
    "binary/octet-stream",
}
ALLOWED_EXACT_KEYS = {
    "not_official_verified",
    "not_for_trading_advice",
    "source_url",
    "final_url",
    "cache_path",
    "cache_dir",
}
SOURCE_URL_KEYS = {"source_url", "final_url"}
FORBIDDEN_SECRET_URL_MARKERS = ("token", ".env", "tushare_token")
FORBIDDEN_ENGLISH_MARKERS = (
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
    "parse PDF",
    "PDF parser",
    "table extractor",
    "metric extraction",
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
)
WORD_MARKERS = {"token", "buy", "sell", "hold", "portfolio", "position"}
IDENTIFIER_SAFE_WORD_MARKERS = {"buy", "sell", "hold"}
CAMEL_SPLIT_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")

REASON_FORBIDDEN_MARKER_DETECTED = "forbidden_marker_detected"
REASON_MISSING_ANCHOR_MAP = "missing_anchor_map"
REASON_ANCHOR_MAP_MUST_BE_MAPPING = "anchor_map_must_be_mapping"
REASON_INVALID_ANCHOR_MAP_SCHEMA_VERSION = "invalid_anchor_map_schema_version"
REASON_UNSUPPORTED_PROVIDER = "unsupported_provider"
REASON_ANCHOR_ITEMS_MISSING = "anchor_items_missing"
REASON_ANCHOR_ITEMS_MUST_BE_LIST = "anchor_items_must_be_list"
REASON_NO_MATCHED_ANCHORS = "no_matched_anchors"
REASON_ALLOW_NETWORK_FALSE = "allow_network_false"
REASON_OFFICIAL_HTTP_CLIENT_MISSING = "official_http_client_missing"
REASON_CACHE_DIR_MISSING = "cache_dir_missing"
REASON_CACHE_DIR_FORBIDDEN = "cache_dir_forbidden"
REASON_CACHE_DIR_NOT_DIRECTORY = "cache_dir_not_directory"
REASON_CACHE_DIR_NOT_WRITABLE = "cache_dir_not_writable"
REASON_WRITE_FAILURE = "cache_write_failure"
REASON_MISSING_OFFICIAL_DISCLOSURE_ANCHOR = "matched_anchor_missing_official_disclosure_anchor"
REASON_INVALID_ANCHOR_EVIDENCE_STATUS = "invalid_anchor_evidence_status"
REASON_INVALID_OFFICIAL_VERIFICATION_STATUS = "invalid_official_verification_status"
REASON_SOURCE_URL_MISSING = "source_url_missing"
REASON_SOURCE_URL_NON_HTTP = "source_url_non_http"
REASON_SOURCE_DOMAIN_NOT_ALLOWLISTED = "source_domain_not_allowlisted"
REASON_SOURCE_DOMAIN_URL_MISMATCH = "source_domain_url_mismatch"
REASON_FINAL_DOMAIN_NOT_ALLOWLISTED = "final_domain_not_allowlisted"
REASON_CONTENT_TYPE_NOT_ALLOWED = "content_type_not_allowed"
REASON_PDF_MAGIC_MISMATCH = "pdf_magic_mismatch"
REASON_SIZE_EXCEEDS_LIMIT = "size_exceeds_limit"
REASON_TRANSPORT_ERROR = "official_artifact_transport_error"
REASON_TIMEOUT = "official_artifact_timeout"
REASON_MALFORMED_RESPONSE = "malformed_official_artifact_response"
REASON_HTTP_STATUS_NOT_SUCCESS = "http_status_not_success"


class OfficialArtifactCacheAcquisitionError(ValueError):
    """Raised when artifact cache acquisition must fail closed."""


class OfficialArtifactCacheSafetyError(OfficialArtifactCacheAcquisitionError):
    """Raised when nested input contains a forbidden marker."""

    def __init__(self, marker: str) -> None:
        super().__init__("forbidden_marker")
        self.marker = marker


class OfficialArtifactFinalHostBlocked(OfficialArtifactCacheAcquisitionError):
    """Raised before body read when a redirect leaves the official allowlist."""

    def __init__(self) -> None:
        super().__init__(REASON_FINAL_DOMAIN_NOT_ALLOWLISTED)


def build_official_artifact_cache_from_anchor_map(
    anchor_map: Any,
    *,
    cache_dir: str | Path | None,
    official_http_client: Any = None,
    allow_network: bool = False,
) -> dict[str, Any]:
    """Build official artifact cache metadata from matched disclosure anchors."""

    try:
        assert_no_official_artifact_cache_forbidden_markers(anchor_map)
        assert_no_official_artifact_cache_forbidden_markers(str(cache_dir) if cache_dir is not None else "")
    except OfficialArtifactCacheSafetyError:
        result = _empty_artifact_cache_result(None, cache_dir=None)
        result["blocked_reasons"].append(REASON_FORBIDDEN_MARKER_DETECTED)
        validate_official_disclosure_artifact_cache(result)
        return result

    result = _empty_artifact_cache_result(anchor_map if isinstance(anchor_map, Mapping) else None, cache_dir=cache_dir)
    anchor_map_blockers = _anchor_map_contract_blockers(anchor_map)
    cache_path, cache_blockers = _prepare_cache_dir(cache_dir)
    if cache_blockers:
        result["blocked_reasons"].extend(cache_blockers)
    if anchor_map_blockers:
        result["blocked_reasons"].extend(anchor_map_blockers)
        validate_official_disclosure_artifact_cache(result)
        return result
    if cache_path is None:
        validate_official_disclosure_artifact_cache(result)
        return result

    assert isinstance(anchor_map, Mapping)
    normalized_items = normalize_official_artifact_anchor_items(anchor_map)
    matched_items = [item for item in normalized_items if item.get("official_anchor_status") == ANCHOR_STATUS_MATCHED]
    for item in normalized_items:
        if item.get("official_anchor_status") != ANCHOR_STATUS_MATCHED:
            result["skipped_items"].append(_skipped_item_from_anchor_item(item))

    if not matched_items:
        result["blocked_reasons"].append(REASON_NO_MATCHED_ANCHORS)
        validate_official_disclosure_artifact_cache(result)
        return result

    seen_source_urls: dict[str, dict[str, Any]] = {}
    seen_sha256: dict[str, dict[str, Any]] = {}
    for item in matched_items:
        anchor = item.get("official_disclosure_anchor")
        source_url = _clean_string(anchor.get("source_url")) if isinstance(anchor, Mapping) else ""
        if source_url and source_url in seen_source_urls:
            reused = _reused_item_from_cached_item(item, seen_source_urls[source_url], cache_status="reused_source_url")
            result["artifact_items"].append(reused)
            continue

        downloaded = download_official_artifact_from_anchor(
            item,
            cache_dir=cache_path,
            official_http_client=official_http_client,
            allow_network=allow_network,
            anchor_map_schema_version=_clean_string(anchor_map.get("schema_version")),
        )
        if downloaded.get("artifact_status") == ARTIFACT_STATUS_CACHED and downloaded.get("sha256") in seen_sha256:
            reused = _reused_item_from_cached_item(item, seen_sha256[str(downloaded.get("sha256"))], cache_status="reused_sha256")
            _remove_new_duplicate_cache_file(downloaded, reused)
            downloaded = reused
        result["artifact_items"].append(downloaded)
        if downloaded.get("artifact_status") == ARTIFACT_STATUS_CACHED:
            if source_url:
                seen_source_urls[source_url] = downloaded
            sha256 = downloaded.get("sha256")
            if isinstance(sha256, str) and sha256:
                seen_sha256[sha256] = downloaded
        else:
            result["blocked_reasons"].extend(_safe_list(downloaded.get("caveats")))

    result["blocked_reasons"] = _dedupe_preserve_order(result["blocked_reasons"])
    validate_official_disclosure_artifact_cache(result)
    return result


def download_official_artifact_from_anchor(
    anchor: Any,
    *,
    cache_dir: str | Path | None,
    official_http_client: Any = None,
    allow_network: bool = False,
    anchor_map_schema_version: str = ANCHOR_MAP_SCHEMA_VERSION,
) -> dict[str, Any]:
    """Download one official PDF artifact into an explicit cache directory."""

    try:
        assert_no_official_artifact_cache_forbidden_markers(anchor)
        assert_no_official_artifact_cache_forbidden_markers(str(cache_dir) if cache_dir is not None else "")
    except OfficialArtifactCacheSafetyError:
        return _blocked_artifact_item(
            {},
            {},
            [REASON_FORBIDDEN_MARKER_DETECTED],
            anchor_map_schema_version=anchor_map_schema_version,
        )

    anchor_item, official_anchor = _coerce_anchor_item(anchor)
    item_blockers = _matched_anchor_blockers(anchor_item, official_anchor)
    if item_blockers:
        return _blocked_artifact_item(
            anchor_item,
            official_anchor,
            item_blockers,
            anchor_map_schema_version=anchor_map_schema_version,
        )

    cache_path, cache_blockers = _prepare_cache_dir(cache_dir)
    if cache_blockers or cache_path is None:
        return _blocked_artifact_item(
            anchor_item,
            official_anchor,
            cache_blockers or [REASON_CACHE_DIR_MISSING],
            anchor_map_schema_version=anchor_map_schema_version,
        )

    if allow_network is not True:
        blockers = [REASON_ALLOW_NETWORK_FALSE]
        if official_http_client is None:
            blockers.append(REASON_OFFICIAL_HTTP_CLIENT_MISSING)
        return _blocked_artifact_item(
            anchor_item,
            official_anchor,
            blockers,
            anchor_map_schema_version=anchor_map_schema_version,
        )

    source_url = _clean_string(official_anchor.get("source_url"))
    client = official_http_client or _default_official_http_client
    try:
        response = _invoke_official_http_client(client, source_url)
        response_data, response_reasons = _coerce_official_http_response(response, source_url)
    except OfficialArtifactFinalHostBlocked:
        return _blocked_artifact_item(
            anchor_item,
            official_anchor,
            [REASON_FINAL_DOMAIN_NOT_ALLOWLISTED],
            anchor_map_schema_version=anchor_map_schema_version,
        )
    except (TimeoutError, socket.timeout):
        return _blocked_artifact_item(
            anchor_item,
            official_anchor,
            [REASON_TIMEOUT],
            anchor_map_schema_version=anchor_map_schema_version,
        )
    except Exception:
        return _blocked_artifact_item(
            anchor_item,
            official_anchor,
            [REASON_TRANSPORT_ERROR],
            anchor_map_schema_version=anchor_map_schema_version,
        )

    if response_reasons:
        return _blocked_artifact_item(
            anchor_item,
            official_anchor,
            response_reasons,
            anchor_map_schema_version=anchor_map_schema_version,
        )

    body = response_data["body"]
    final_url = response_data["final_url"]
    content_type = response_data["content_type"]
    final_domain = _domain_from_url(final_url)
    validation_reasons = _downloaded_artifact_blockers(
        body=body,
        source_url=source_url,
        final_url=final_url,
        final_domain=final_domain,
        content_type=content_type,
    )
    if validation_reasons:
        return _blocked_artifact_item(
            anchor_item,
            official_anchor,
            validation_reasons,
            final_url=final_url,
            final_domain=final_domain,
            content_type=content_type,
            anchor_map_schema_version=anchor_map_schema_version,
        )

    sha256 = hashlib.sha256(body).hexdigest()
    existing_path = _find_existing_cache_file_for_sha(cache_path, sha256)
    if existing_path is not None:
        item = _cached_artifact_item(
            anchor_item,
            official_anchor,
            final_url=final_url,
            final_domain=final_domain,
            content_type=content_type,
            cache_path=existing_path,
            file_size_bytes=len(body),
            sha256=sha256,
            cache_status="reused",
            anchor_map_schema_version=anchor_map_schema_version,
        )
        validate_official_disclosure_artifact_cache_item(item)
        return item

    final_cache_path = cache_path / _cache_filename(official_anchor, sha256)
    try:
        written_path = _atomic_write_cache_file(cache_path, final_cache_path, body)
    except Exception:
        return _blocked_artifact_item(
            anchor_item,
            official_anchor,
            [REASON_WRITE_FAILURE],
            final_url=final_url,
            final_domain=final_domain,
            content_type=content_type,
            anchor_map_schema_version=anchor_map_schema_version,
        )

    item = _cached_artifact_item(
        anchor_item,
        official_anchor,
        final_url=final_url,
        final_domain=final_domain,
        content_type=content_type,
        cache_path=written_path,
        file_size_bytes=len(body),
        sha256=sha256,
        cache_status="stored",
        anchor_map_schema_version=anchor_map_schema_version,
    )
    validate_official_disclosure_artifact_cache_item(item)
    return item


def validate_official_disclosure_artifact_cache(cache_result: Any) -> None:
    """Validate artifact cache result shape and safety constraints."""

    if not isinstance(cache_result, Mapping):
        raise OfficialArtifactCacheAcquisitionError("invalid_artifact_cache")
    if cache_result.get("schema_version") != ARTIFACT_CACHE_SCHEMA_VERSION:
        raise OfficialArtifactCacheAcquisitionError("invalid_artifact_cache_schema_version")
    _require_true_bool(cache_result, "not_official_verified", "$")
    _require_true_bool(cache_result, "not_for_trading_advice", "$")
    for key in ("artifact_items", "skipped_items", "blocked_reasons", "caveats"):
        if not isinstance(cache_result.get(key), list):
            raise OfficialArtifactCacheAcquisitionError(f"invalid_{key}")
    for index, item in enumerate(cache_result["artifact_items"]):
        validate_official_disclosure_artifact_cache_item(item, path=f"$.artifact_items[{index}]")
    for index, item in enumerate(cache_result["skipped_items"]):
        if not isinstance(item, Mapping):
            raise OfficialArtifactCacheAcquisitionError(f"invalid_skipped_item:{index}")
        _require_true_bool(item, "not_official_verified", f"$.skipped_items[{index}]")
        _require_true_bool(item, "not_for_trading_advice", f"$.skipped_items[{index}]")
    assert_no_official_artifact_cache_forbidden_markers(cache_result)


def validate_official_disclosure_artifact_cache_item(item: Any, *, path: str = "$") -> None:
    """Validate one artifact cache item."""

    if not isinstance(item, Mapping):
        raise OfficialArtifactCacheAcquisitionError("invalid_artifact_cache_item")
    required = (
        "schema_version",
        "artifact_id",
        "source_title",
        "source_url",
        "source_domain",
        "final_url",
        "final_domain",
        "disclosure_date",
        "stock_code",
        "company_name_hint",
        "period_key",
        "period_end_date",
        "announcement_type",
        "source_type",
        "anchor_evidence_status",
        "artifact_status",
        "download_status",
        "cache_path",
        "file_size_bytes",
        "sha256",
        "content_type",
        "source_lineage",
        "not_official_verified",
        "not_for_trading_advice",
        "caveats",
    )
    for key in required:
        if key not in item:
            raise OfficialArtifactCacheAcquisitionError(f"{path}:{key}_missing")
    if item.get("schema_version") != ARTIFACT_CACHE_ITEM_SCHEMA_VERSION:
        raise OfficialArtifactCacheAcquisitionError("invalid_artifact_cache_item_schema_version")
    if item.get("artifact_status") not in {
        ARTIFACT_STATUS_CACHED,
        ARTIFACT_STATUS_SKIPPED,
        ARTIFACT_STATUS_BLOCKED,
    }:
        raise OfficialArtifactCacheAcquisitionError("invalid_artifact_status")
    if item.get("download_status") not in {
        DOWNLOAD_STATUS_SUCCESS,
        DOWNLOAD_STATUS_BLOCKED,
        DOWNLOAD_STATUS_FAILED,
    }:
        raise OfficialArtifactCacheAcquisitionError("invalid_download_status")
    if item.get("anchor_evidence_status") not in (None, "", ANCHOR_EVIDENCE_STATUS):
        raise OfficialArtifactCacheAcquisitionError("invalid_item_anchor_evidence_status")
    if not isinstance(item.get("caveats"), list):
        raise OfficialArtifactCacheAcquisitionError("invalid_item_caveats")
    if not isinstance(item.get("source_lineage"), Mapping):
        raise OfficialArtifactCacheAcquisitionError("invalid_source_lineage")
    _require_true_bool(item, "not_official_verified", path)
    _require_true_bool(item, "not_for_trading_advice", path)
    _require_true_bool(item["source_lineage"], "not_official_verified", f"{path}.source_lineage")
    _require_true_bool(item["source_lineage"], "not_for_trading_advice", f"{path}.source_lineage")
    if item.get("artifact_status") == ARTIFACT_STATUS_CACHED:
        if item.get("download_status") != DOWNLOAD_STATUS_SUCCESS:
            raise OfficialArtifactCacheAcquisitionError("cached_item_requires_success_download_status")
        if not item.get("cache_path") or not item.get("sha256"):
            raise OfficialArtifactCacheAcquisitionError("cached_item_missing_cache_metadata")
        if not isinstance(item.get("file_size_bytes"), int) or item["file_size_bytes"] < 0:
            raise OfficialArtifactCacheAcquisitionError("invalid_file_size_bytes")
    assert_no_official_artifact_cache_forbidden_markers(item)


def normalize_official_artifact_anchor_items(anchor_map: Any) -> list[dict[str, Any]]:
    """Normalize anchor-map items for artifact acquisition without mutation."""

    assert_no_official_artifact_cache_forbidden_markers(anchor_map)
    if not isinstance(anchor_map, Mapping):
        return []
    anchor_items = anchor_map.get("anchor_items")
    if not isinstance(anchor_items, list):
        return []
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(anchor_items):
        if not isinstance(item, Mapping):
            normalized.append(
                {
                    "schema_version": ANCHOR_ITEM_SCHEMA_VERSION,
                    "provider": PROVIDER_NAME,
                    "official_anchor_status": "invalid_anchor_item",
                    "official_disclosure_anchor": None,
                    "metric_key": None,
                    "item_index": index,
                    "not_official_verified": True,
                    "not_for_trading_advice": True,
                    "caveats": ["invalid_anchor_item"],
                }
            )
            continue
        copied = {str(key): _copy_jsonlike(value) for key, value in item.items()}
        copied.setdefault("item_index", index)
        copied.setdefault("not_official_verified", True)
        copied.setdefault("not_for_trading_advice", True)
        copied.setdefault("caveats", [])
        normalized.append(copied)
    return normalized


def build_artifact_id(anchor: Any) -> str:
    """Build a stable artifact id from explicit official anchor metadata."""

    _, official_anchor = _coerce_anchor_item(anchor)
    material = "|".join(
        [
            _clean_string(official_anchor.get("source_url")),
            _clean_string(official_anchor.get("stock_code")),
            _clean_string(official_anchor.get("period_end_date")),
            _clean_string(official_anchor.get("announcement_type")),
        ]
    )
    return "official-artifact-" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]


def assert_no_official_artifact_cache_forbidden_markers(value: Any) -> None:
    """Reject forbidden markers in nested dict/list/string payloads."""

    finding = _find_forbidden_marker(value)
    if finding is not None:
        raise OfficialArtifactCacheSafetyError(finding)


def _empty_artifact_cache_result(anchor_map: Mapping[str, Any] | None, *, cache_dir: Any) -> dict[str, Any]:
    return {
        "schema_version": ARTIFACT_CACHE_SCHEMA_VERSION,
        "provider": anchor_map.get("provider") if anchor_map else None,
        "ts_code": anchor_map.get("ts_code") if anchor_map else None,
        "stock_code": anchor_map.get("stock_code") if anchor_map else None,
        "company_name_hint": anchor_map.get("company_name_hint") if anchor_map else None,
        "artifact_items": [],
        "skipped_items": [],
        "blocked_reasons": [],
        "caveats": [
            "artifact_cache_only",
            "byte_integrity_metadata_only",
            "source_lineage_preserved",
        ],
        "cache_dir": str(cache_dir) if cache_dir is not None else None,
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }


def _anchor_map_contract_blockers(anchor_map: Any) -> list[str]:
    if anchor_map is None:
        return [REASON_MISSING_ANCHOR_MAP]
    if not isinstance(anchor_map, Mapping):
        return [REASON_ANCHOR_MAP_MUST_BE_MAPPING]

    blockers: list[str] = []
    if anchor_map.get("schema_version") != ANCHOR_MAP_SCHEMA_VERSION:
        blockers.append(REASON_INVALID_ANCHOR_MAP_SCHEMA_VERSION)
    if anchor_map.get("provider") != PROVIDER_NAME:
        blockers.append(REASON_UNSUPPORTED_PROVIDER)
    _append_true_flag_blocker(blockers, anchor_map, "not_official_verified")
    _append_true_flag_blocker(blockers, anchor_map, "not_for_trading_advice")
    if "anchor_items" not in anchor_map:
        blockers.append(REASON_ANCHOR_ITEMS_MISSING)
    elif not isinstance(anchor_map.get("anchor_items"), list):
        blockers.append(REASON_ANCHOR_ITEMS_MUST_BE_LIST)
    return _dedupe_preserve_order(blockers)


def _matched_anchor_blockers(anchor_item: Mapping[str, Any], official_anchor: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not official_anchor:
        blockers.append(REASON_MISSING_OFFICIAL_DISCLOSURE_ANCHOR)
        return blockers

    if anchor_item.get("official_anchor_status") not in (None, "", ANCHOR_STATUS_MATCHED):
        blockers.append(f"anchor_status_not_matched:{_clean_string(anchor_item.get('official_anchor_status'))}")
    if anchor_item.get("official_verification_status") not in (None, PENDING_OFFICIAL_VERIFICATION_STATUS):
        blockers.append(REASON_INVALID_OFFICIAL_VERIFICATION_STATUS)
    if anchor_item.get("not_official_verified") is not True:
        blockers.append("anchor_item_not_official_verified_must_be_true")
    if anchor_item.get("not_for_trading_advice") is not True:
        blockers.append("anchor_item_advice_safety_flag_must_be_true")
    if official_anchor.get("anchor_evidence_status") != ANCHOR_EVIDENCE_STATUS:
        blockers.append(REASON_INVALID_ANCHOR_EVIDENCE_STATUS)
    if official_anchor.get("not_for_trading_advice") is not True:
        blockers.append("anchor_advice_safety_flag_must_be_true")

    source_url = _clean_string(official_anchor.get("source_url"))
    parsed = urlparse(source_url)
    source_domain = _normalize_domain(official_anchor.get("source_domain")) or _domain_from_url(source_url)
    url_domain = _domain_from_url(source_url)
    if not source_url:
        blockers.append(REASON_SOURCE_URL_MISSING)
    elif parsed.scheme not in {"http", "https"}:
        blockers.append(REASON_SOURCE_URL_NON_HTTP)
    if source_url and _url_has_forbidden_secret_marker(source_url):
        blockers.append(REASON_FORBIDDEN_MARKER_DETECTED)
    if source_url and parsed.scheme in {"http", "https"} and url_domain not in ALLOWED_OFFICIAL_ARTIFACT_DOMAINS:
        blockers.append(REASON_SOURCE_DOMAIN_NOT_ALLOWLISTED)
    if source_domain and source_domain not in ALLOWED_OFFICIAL_ARTIFACT_DOMAINS:
        blockers.append(REASON_SOURCE_DOMAIN_NOT_ALLOWLISTED)
    if source_domain and url_domain and source_domain != url_domain:
        blockers.append(REASON_SOURCE_DOMAIN_URL_MISMATCH)
    return _dedupe_preserve_order(blockers)


def _prepare_cache_dir(cache_dir: str | Path | None) -> tuple[Path | None, list[str]]:
    if cache_dir in (None, ""):
        return None, [REASON_CACHE_DIR_MISSING]
    try:
        cache_path = Path(cache_dir)
    except TypeError:
        return None, [REASON_CACHE_DIR_MISSING]

    if _is_forbidden_cache_dir(cache_path):
        return None, [REASON_CACHE_DIR_FORBIDDEN]
    try:
        resolved = cache_path.expanduser().resolve(strict=False)
    except Exception:
        return None, [REASON_CACHE_DIR_FORBIDDEN]
    if _is_repo_root(resolved):
        return None, [REASON_CACHE_DIR_FORBIDDEN]
    if resolved.exists() and not resolved.is_dir():
        return None, [REASON_CACHE_DIR_NOT_DIRECTORY]
    try:
        resolved.mkdir(parents=True, exist_ok=True)
        probe_path = resolved / ".official_artifact_cache_write_probe.tmp"
        with probe_path.open("wb") as handle:
            handle.write(b"")
        probe_path.unlink(missing_ok=True)
    except Exception:
        return None, [REASON_CACHE_DIR_NOT_WRITABLE]
    return resolved, []


def _is_forbidden_cache_dir(path: Path) -> bool:
    parts = [part.casefold() for part in path.parts]
    forbidden_exact = {"output", "fixtures", ".local_experiments"}
    if any(part in forbidden_exact for part in parts):
        return True
    normalized_parts = [re.sub(r"[\s\-]+", "_", part) for part in parts]
    return any(
        part == "accepted_manifest"
        or ("accepted" in part and "manifest" in part)
        or part.endswith(".json") and "manifest" in part
        for part in normalized_parts
    )


def _is_repo_root(path: Path) -> bool:
    try:
        repo_root = Path(__file__).resolve().parents[3]
    except IndexError:
        return False
    return path == repo_root


def _invoke_official_http_client(client: Any, source_url: str) -> Any:
    request = {
        "method": "GET",
        "url": source_url,
        "headers": {
            "Accept": "application/pdf,application/octet-stream,binary/octet-stream",
            "User-Agent": "official artifact cache acquisition client",
        },
        "timeout": DEFAULT_TIMEOUT_SECONDS,
        "max_bytes": MAX_ARTIFACT_BYTES + 1,
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }
    request_snapshot = copy.deepcopy(request)
    if callable(client):
        return client(request_snapshot)
    if hasattr(client, "request"):
        return client.request(
            "GET",
            source_url,
            headers=copy.deepcopy(request["headers"]),
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
    if hasattr(client, "get"):
        return client.get(
            source_url,
            headers=copy.deepcopy(request["headers"]),
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
    raise TypeError("official_http_client_must_be_callable")


def _default_official_http_client(request: Mapping[str, Any]) -> dict[str, Any]:
    req = urllib.request.Request(
        _clean_string(request.get("url")),
        method="GET",
        headers=dict(request.get("headers", {})),
    )
    try:
        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
            final_url = response.geturl()
            final_host = _domain_from_url(final_url)
            if final_host not in ALLOWED_OFFICIAL_ARTIFACT_DOMAINS:
                raise OfficialArtifactFinalHostBlocked()
            content_type = response.headers.get("Content-Type", "")
            body = response.read(MAX_ARTIFACT_BYTES + 1)
            return {
                "status_code": response.status,
                "final_url": final_url,
                "content_type": content_type,
                "body": body,
            }
    except urllib.error.URLError as exc:
        if isinstance(getattr(exc, "reason", None), socket.timeout):
            raise TimeoutError("official_artifact_timeout") from exc
        raise


def _coerce_official_http_response(response: Any, source_url: str) -> tuple[dict[str, Any], list[str]]:
    if isinstance(response, (bytes, bytearray)):
        body = bytes(response)
        if len(body) > MAX_ARTIFACT_BYTES:
            return _empty_response_data(source_url, body), [REASON_SIZE_EXCEEDS_LIMIT]
        return _response_data(body=body, content_type="", final_url=source_url), []

    if isinstance(response, Mapping):
        status_code = response.get("status_code", response.get("status"))
        if status_code is not None and not _is_success_status(status_code):
            return _empty_response_data(source_url, b""), [REASON_HTTP_STATUS_NOT_SUCCESS]
        body = response.get("body", response.get("content", response.get("data")))
        if body is None and callable(response.get("read")):
            body = response["read"](MAX_ARTIFACT_BYTES + 1)
        headers = response.get("headers", {})
        content_type = response.get("content_type") or _header_value(headers, "Content-Type")
        final_url = response.get("final_url") or response.get("url") or source_url
        return _response_from_body(body, content_type, final_url, source_url)

    status_code = getattr(response, "status_code", None) or getattr(response, "status", None)
    if status_code is not None and not _is_success_status(status_code):
        return _empty_response_data(source_url, b""), [REASON_HTTP_STATUS_NOT_SUCCESS]
    headers = getattr(response, "headers", {})
    content_type = _header_value(headers, "Content-Type")
    final_url = _response_final_url(response) or source_url
    body = getattr(response, "content", None)
    if body is None and hasattr(response, "read") and callable(response.read):
        body = response.read(MAX_ARTIFACT_BYTES + 1)
    return _response_from_body(body, content_type, final_url, source_url)


def _response_from_body(
    body: Any,
    content_type: Any,
    final_url: Any,
    source_url: str,
) -> tuple[dict[str, Any], list[str]]:
    if isinstance(body, str):
        body_bytes = body.encode("utf-8")
    elif isinstance(body, (bytes, bytearray)):
        body_bytes = bytes(body)
    else:
        return _empty_response_data(source_url, b""), [REASON_MALFORMED_RESPONSE]
    if len(body_bytes) > MAX_ARTIFACT_BYTES:
        return _empty_response_data(source_url, body_bytes), [REASON_SIZE_EXCEEDS_LIMIT]
    return _response_data(
        body=body_bytes,
        content_type=_normalize_content_type(content_type),
        final_url=_clean_string(final_url) or source_url,
    ), []


def _downloaded_artifact_blockers(
    *,
    body: bytes,
    source_url: str,
    final_url: str,
    final_domain: str,
    content_type: str,
) -> list[str]:
    blockers: list[str] = []
    if _url_has_forbidden_secret_marker(final_url):
        blockers.append(REASON_FORBIDDEN_MARKER_DETECTED)
    if final_domain not in ALLOWED_OFFICIAL_ARTIFACT_DOMAINS:
        blockers.append(REASON_FINAL_DOMAIN_NOT_ALLOWLISTED)
    if len(body) > MAX_ARTIFACT_BYTES:
        blockers.append(REASON_SIZE_EXCEEDS_LIMIT)
    if not body.startswith(PDF_MAGIC_BYTES):
        blockers.append(REASON_PDF_MAGIC_MISMATCH)
    if not _content_type_allowed(content_type, source_url=source_url, final_url=final_url, body=body):
        blockers.append(REASON_CONTENT_TYPE_NOT_ALLOWED)
    return _dedupe_preserve_order(blockers)


def _content_type_allowed(content_type: str, *, source_url: str, final_url: str, body: bytes) -> bool:
    normalized = _normalize_content_type(content_type)
    if normalized in ALLOWED_PDF_CONTENT_TYPES:
        return body.startswith(PDF_MAGIC_BYTES)
    if normalized in CONDITIONAL_PDF_CONTENT_TYPES:
        return _url_path_ends_pdf(final_url) or _url_path_ends_pdf(source_url)
    if normalized.startswith("image/"):
        return False
    return False


def _cached_artifact_item(
    anchor_item: Mapping[str, Any],
    official_anchor: Mapping[str, Any],
    *,
    final_url: str,
    final_domain: str,
    content_type: str,
    cache_path: Path,
    file_size_bytes: int,
    sha256: str,
    cache_status: str,
    anchor_map_schema_version: str,
) -> dict[str, Any]:
    sanitized_final_url = _sanitize_url_for_output(final_url)
    item = _artifact_item_base(
        anchor_item,
        official_anchor,
        final_url=sanitized_final_url,
        final_domain=final_domain,
        content_type=_normalize_content_type(content_type),
        source_lineage=_source_lineage(anchor_item, official_anchor, anchor_map_schema_version),
    )
    item.update(
        {
            "artifact_status": ARTIFACT_STATUS_CACHED,
            "download_status": DOWNLOAD_STATUS_SUCCESS,
            "cache_path": str(cache_path),
            "file_size_bytes": file_size_bytes,
            "sha256": sha256,
            "cache_status": cache_status,
            "caveats": _dedupe_preserve_order(
                item["caveats"]
                + [
                    "official_pdf_bytes_cached",
                    "sha256_byte_integrity_only",
                    "not_an_official_fact_result",
                ]
            ),
        }
    )
    return item


def _blocked_artifact_item(
    anchor_item: Mapping[str, Any],
    official_anchor: Mapping[str, Any],
    reasons: Sequence[str],
    *,
    final_url: str | None = None,
    final_domain: str | None = None,
    content_type: str | None = None,
    anchor_map_schema_version: str,
) -> dict[str, Any]:
    safe_reasons = _dedupe_preserve_order([_clean_string(reason) for reason in reasons if _clean_string(reason)])
    item = _artifact_item_base(
        anchor_item,
        official_anchor,
        final_url=_sanitize_url_for_output(final_url) if final_url else None,
        final_domain=final_domain,
        content_type=_normalize_content_type(content_type),
        source_lineage=_source_lineage(anchor_item, official_anchor, anchor_map_schema_version),
    )
    item.update(
        {
            "artifact_status": ARTIFACT_STATUS_BLOCKED,
            "download_status": DOWNLOAD_STATUS_BLOCKED,
            "cache_path": None,
            "file_size_bytes": None,
            "sha256": None,
            "cache_status": None,
            "caveats": _dedupe_preserve_order(item["caveats"] + safe_reasons),
        }
    )
    validate_official_disclosure_artifact_cache_item(item)
    return item


def _artifact_item_base(
    anchor_item: Mapping[str, Any],
    official_anchor: Mapping[str, Any],
    *,
    final_url: str | None,
    final_domain: str | None,
    content_type: str | None,
    source_lineage: Mapping[str, Any],
) -> dict[str, Any]:
    source_url = _clean_string(official_anchor.get("source_url"))
    source_domain = _normalize_domain(official_anchor.get("source_domain")) or _domain_from_url(source_url)
    return {
        "schema_version": ARTIFACT_CACHE_ITEM_SCHEMA_VERSION,
        "artifact_id": build_artifact_id(official_anchor),
        "source_title": _clean_string(official_anchor.get("source_title")),
        "source_url": source_url,
        "source_domain": source_domain or None,
        "final_url": final_url,
        "final_domain": final_domain,
        "disclosure_date": _clean_string(official_anchor.get("disclosure_date")),
        "stock_code": _clean_string(official_anchor.get("stock_code") or anchor_item.get("stock_code")),
        "company_name_hint": _clean_string(
            official_anchor.get("company_name_hint") or anchor_item.get("company_name_hint")
        ),
        "period_key": _clean_string(official_anchor.get("period_key") or anchor_item.get("period_label")),
        "period_end_date": _clean_string(official_anchor.get("period_end_date") or anchor_item.get("period")),
        "announcement_type": _clean_string(official_anchor.get("announcement_type")),
        "source_type": _clean_string(official_anchor.get("source_type")),
        "anchor_evidence_status": _clean_string(official_anchor.get("anchor_evidence_status")),
        "content_type": _normalize_content_type(content_type),
        "source_lineage": dict(source_lineage),
        "not_official_verified": True,
        "not_for_trading_advice": True,
        "caveats": _dedupe_preserve_order(_safe_list(anchor_item.get("caveats"))),
    }


def _source_lineage(
    anchor_item: Mapping[str, Any],
    official_anchor: Mapping[str, Any],
    anchor_map_schema_version: str,
) -> dict[str, Any]:
    metric_keys: list[str] = []
    raw_metric_keys = anchor_item.get("metric_keys")
    if isinstance(raw_metric_keys, list):
        metric_keys.extend(_clean_string(key) for key in raw_metric_keys if _clean_string(key))
    metric_key = _clean_string(anchor_item.get("metric_key"))
    if metric_key and metric_key not in metric_keys:
        metric_keys.append(metric_key)
    source_url = _clean_string(official_anchor.get("source_url"))
    return {
        "schema_version": SOURCE_LINEAGE_SCHEMA_VERSION,
        "source_anchor_status": _clean_string(anchor_item.get("official_anchor_status")) or ANCHOR_STATUS_MATCHED,
        "source_anchor_url": source_url,
        "source_anchor_domain": _normalize_domain(official_anchor.get("source_domain")) or _domain_from_url(source_url),
        "source_anchor_title": _clean_string(official_anchor.get("source_title")),
        "source_disclosure_date": _clean_string(official_anchor.get("disclosure_date")),
        "anchor_map_schema_version": anchor_map_schema_version or ANCHOR_MAP_SCHEMA_VERSION,
        "anchor_item_metric_keys": metric_keys,
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }


def _skipped_item_from_anchor_item(anchor_item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": ARTIFACT_CACHE_ITEM_SCHEMA_VERSION,
        "artifact_id": None,
        "source_title": None,
        "source_url": None,
        "source_domain": None,
        "official_anchor_status": _clean_string(anchor_item.get("official_anchor_status")),
        "artifact_status": ARTIFACT_STATUS_SKIPPED,
        "download_status": DOWNLOAD_STATUS_BLOCKED,
        "period_key": _clean_string(anchor_item.get("period_label")),
        "period_end_date": _clean_string(anchor_item.get("period")),
        "metric_key": _clean_string(anchor_item.get("metric_key")),
        "caveats": _dedupe_preserve_order(
            _safe_list(anchor_item.get("caveats"))
            + [f"anchor_status_not_matched:{_clean_string(anchor_item.get('official_anchor_status'))}"]
        ),
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }


def _reused_item_from_cached_item(
    anchor_item: Mapping[str, Any],
    cached_item: Mapping[str, Any],
    *,
    cache_status: str,
) -> dict[str, Any]:
    _, official_anchor = _coerce_anchor_item(anchor_item)
    item = dict(cached_item)
    item["artifact_id"] = build_artifact_id(official_anchor)
    item["source_title"] = _clean_string(official_anchor.get("source_title"))
    item["source_url"] = _clean_string(official_anchor.get("source_url"))
    item["source_domain"] = _normalize_domain(official_anchor.get("source_domain")) or _domain_from_url(
        official_anchor.get("source_url")
    )
    item["disclosure_date"] = _clean_string(official_anchor.get("disclosure_date"))
    item["stock_code"] = _clean_string(official_anchor.get("stock_code") or anchor_item.get("stock_code"))
    item["company_name_hint"] = _clean_string(
        official_anchor.get("company_name_hint") or anchor_item.get("company_name_hint")
    )
    item["period_key"] = _clean_string(official_anchor.get("period_key") or anchor_item.get("period_label"))
    item["period_end_date"] = _clean_string(official_anchor.get("period_end_date") or anchor_item.get("period"))
    item["announcement_type"] = _clean_string(official_anchor.get("announcement_type"))
    item["source_type"] = _clean_string(official_anchor.get("source_type"))
    item["anchor_evidence_status"] = _clean_string(official_anchor.get("anchor_evidence_status"))
    item["source_lineage"] = _source_lineage(
        anchor_item,
        official_anchor,
        str(cached_item.get("source_lineage", {}).get("anchor_map_schema_version") or ANCHOR_MAP_SCHEMA_VERSION),
    )
    item["cache_status"] = cache_status
    item["caveats"] = _dedupe_preserve_order(_safe_list(item.get("caveats")) + [cache_status])
    validate_official_disclosure_artifact_cache_item(item)
    return item


def _remove_new_duplicate_cache_file(downloaded: Mapping[str, Any], reused: Mapping[str, Any]) -> None:
    new_path = _clean_string(downloaded.get("cache_path"))
    reused_path = _clean_string(reused.get("cache_path"))
    if not new_path or not reused_path or new_path == reused_path:
        return
    try:
        Path(new_path).unlink(missing_ok=True)
    except Exception:
        pass


def _find_existing_cache_file_for_sha(cache_dir: Path, sha256: str) -> Path | None:
    pattern = f"*_{sha256}.pdf"
    matches = sorted(path for path in cache_dir.glob(pattern) if path.is_file())
    return matches[0] if matches else None


def _cache_filename(official_anchor: Mapping[str, Any], sha256: str) -> str:
    stock_code = _filename_part(official_anchor.get("stock_code"), fallback="stock")
    period_end_date = _filename_part(official_anchor.get("period_end_date"), fallback="period")
    announcement_type = _filename_part(official_anchor.get("announcement_type"), fallback="announcement")
    return f"{stock_code}_{period_end_date}_{announcement_type}_{sha256}.pdf"


def _filename_part(value: Any, *, fallback: str) -> str:
    text = _clean_string(value)
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip("._-")
    return text or fallback


def _atomic_write_cache_file(cache_dir: Path, final_cache_path: Path, body: bytes) -> Path:
    temp_path: Path | None = None
    fd, raw_temp_path = tempfile.mkstemp(
        prefix=".official_artifact_",
        suffix=".tmp",
        dir=str(cache_dir),
    )
    temp_path = Path(raw_temp_path)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(body)
        if final_cache_path.exists():
            temp_path.unlink(missing_ok=True)
            return final_cache_path
        os.replace(temp_path, final_cache_path)
        return final_cache_path
    except Exception:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise


def _coerce_anchor_item(anchor: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(anchor, Mapping):
        return {}, {}
    if isinstance(anchor.get("official_disclosure_anchor"), Mapping):
        anchor_item = {str(key): _copy_jsonlike(value) for key, value in anchor.items()}
        official_anchor = {
            str(key): _copy_jsonlike(value)
            for key, value in anchor["official_disclosure_anchor"].items()
        }
        return anchor_item, official_anchor
    official_anchor = {str(key): _copy_jsonlike(value) for key, value in anchor.items()}
    anchor_item = {
        "official_anchor_status": ANCHOR_STATUS_MATCHED,
        "official_disclosure_anchor": official_anchor,
        "not_official_verified": True,
        "not_for_trading_advice": True,
        "caveats": [],
    }
    return anchor_item, official_anchor


def _append_true_flag_blocker(blockers: list[str], payload: Mapping[str, Any], key: str) -> None:
    reason_key = "advice_safety_flag" if key == "not_for_trading_advice" else key
    if key not in payload:
        blockers.append(f"missing_{reason_key}")
    elif payload.get(key) is not True:
        blockers.append(f"{reason_key}_must_be_true")


def _require_true_bool(payload: Mapping[str, Any], key: str, path: str) -> None:
    if key not in payload:
        raise OfficialArtifactCacheAcquisitionError(f"{path}:{key}_missing")
    if payload.get(key) is not True:
        raise OfficialArtifactCacheAcquisitionError(f"{path}:{key}_must_be_true")


def _response_data(*, body: bytes, content_type: str, final_url: str) -> dict[str, Any]:
    return {
        "schema_version": DOWNLOAD_RESULT_SCHEMA_VERSION,
        "body": body,
        "content_type": _normalize_content_type(content_type),
        "final_url": _clean_string(final_url),
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }


def _empty_response_data(source_url: str, body: bytes) -> dict[str, Any]:
    return _response_data(body=body, content_type="", final_url=source_url)


def _is_success_status(status_code: Any) -> bool:
    try:
        code = int(status_code)
    except (TypeError, ValueError):
        return False
    return 200 <= code < 300


def _header_value(headers: Any, key: str) -> str:
    if not isinstance(headers, Mapping):
        return ""
    for header_key, value in headers.items():
        if str(header_key).casefold() == key.casefold():
            return _clean_string(value)
    return ""


def _response_final_url(response: Any) -> str:
    raw_url = getattr(response, "url", None)
    if raw_url:
        return _clean_string(raw_url)
    geturl = getattr(response, "geturl", None)
    if callable(geturl):
        return _clean_string(geturl())
    return ""


def _normalize_content_type(value: Any) -> str:
    text = _clean_string(value).casefold()
    return text.split(";", 1)[0].strip()


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


def _url_path_ends_pdf(value: str) -> bool:
    return urlparse(value).path.casefold().endswith(".pdf")


def _sanitize_url_for_output(value: Any) -> str | None:
    text = _clean_string(value)
    if not text:
        return None
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"}:
        return None
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def _find_forbidden_marker(value: Any, parent_key: str | None = None) -> str | None:
    if isinstance(value, Mapping):
        for key, nested_value in value.items():
            key_text = str(key)
            if key_text not in ALLOWED_EXACT_KEYS and _text_has_forbidden_marker(key_text):
                return key_text
            finding = _find_forbidden_marker(nested_value, parent_key=key_text)
            if finding is not None:
                return finding
        return None
    if isinstance(value, (list, tuple, set)):
        for item in value:
            finding = _find_forbidden_marker(item, parent_key=parent_key)
            if finding is not None:
                return finding
        return None
    if isinstance(value, Path):
        return _find_forbidden_marker(str(value), parent_key=parent_key)
    if isinstance(value, str):
        if parent_key in SOURCE_URL_KEYS:
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

    for marker in FORBIDDEN_ENGLISH_MARKERS:
        marker_text = _normalize_marker_text(marker)
        if marker_text in WORD_MARKERS:
            boundary_chars = "a-z0-9_" if marker_text in IDENTIFIER_SAFE_WORD_MARKERS else "a-z0-9"
            if re.search(rf"(?<![{boundary_chars}]){re.escape(marker_text)}(?![{boundary_chars}])", normalized):
                return True
            continue
        if marker_text == "official_verified":
            if _contains_official_verified_marker(normalized):
                return True
            continue
        if marker_text and (marker_text in normalized or marker_text in separator_normalized):
            return True
    return any(marker in value for marker in FORBIDDEN_CJK_MARKERS)


def _contains_official_verified_marker(value: str) -> bool:
    if value == "not_official_verified":
        return False
    return re.search(r"(?<!not_)official_verified", value) is not None


def _normalize_marker_text(value: Any) -> str:
    raw = _clean_string(value)
    camel_split = CAMEL_SPLIT_RE.sub("_", raw)
    lowered = camel_split.casefold()
    lowered = re.sub(r"[\s\-\.]+", "_", lowered)
    lowered = re.sub(r"_+", "_", lowered).strip("_")
    return lowered


def _clean_string(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [_clean_string(value) for value in values if _clean_string(value)]


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
