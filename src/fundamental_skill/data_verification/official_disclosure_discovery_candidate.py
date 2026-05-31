# -*- coding: utf-8 -*-
"""Pure metadata contract helpers for official disclosure discovery candidates."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlparse

from .schemas import (
    OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_DISCOVERY_ONLY_SOURCE_TYPES,
    OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_LOCAL_CACHE_SOURCE_TYPES,
    OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_OFFICIAL_SOURCE_TYPES,
    OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_PROVIDER_SOURCE_TYPES,
    OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_REQUIRED_KEYS,
    OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_VERSION,
    AnnouncementType,
    OfficialDisclosureDiscoveryMethod,
    OfficialDisclosureDiscoveryRejectionReason,
    OfficialDisclosureSourceType,
    enum_values,
)
from .validators import OfficialVerificationValidationError, validate_safety_markers


_CODE_RE = re.compile(r"^\d{6}$")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_CAMEL_SPLIT_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_STANDALONE_HTTP_RE = re.compile(r"(?<![a-z])http(?![a-z])", flags=re.IGNORECASE)

_SOURCE_TYPE_ALIASES = {
    "sse_exchange_official_announcement": OfficialDisclosureSourceType.SSE_EXCHANGE_ANNOUNCEMENT.value,
}

_ALLOWED_DOMAINS_BY_SOURCE_TYPE = {
    OfficialDisclosureSourceType.CNINFO_OFFICIAL_PDF.value: ("cninfo.com.cn",),
    OfficialDisclosureSourceType.SSE_EXCHANGE_ANNOUNCEMENT.value: ("sse.com.cn",),
    OfficialDisclosureSourceType.EXCHANGE_OFFICIAL_PDF.value: ("cninfo.com.cn", "sse.com.cn", "szse.cn", "bse.cn"),
}

_DISCOVERY_FORBIDDEN_ENGLISH_MARKERS = (
    "token",
    ".env",
    "tushare_token.txt",
    "provider live",
    "AkShare live",
    "Tushare live",
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
    "买入",
    "卖出",
    "持有",
    "目标价",
    "仓位",
    "组合",
    "技术信号",
    "投资建议",
    "下载",
    "网络",
    "联网",
    "解析PDF",
    "PDF解析",
    "表格抽取",
    "指标抽取",
    "正式研报",
    "输出基线",
    "写入fixture",
    "写入accepted manifest",
)

_DISCOVERY_HIDDEN_PROMOTION_MARKERS = (
    "hidden promotion",
    "hidden_promotion",
    "file authority",
    "file_authority",
    "provider authority",
    "provider_authority",
    "parsed metrics",
    "parsed_metrics",
    "report-ready facts",
    "report_ready_facts",
    "verified fact generation",
    "verified_fact_generation",
)

_SHORT_WORD_MARKERS = {"buy", "sell", "hold", "http", "fetch", "network", "download"}


def normalize_official_disclosure_discovery_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize explicit discovery metadata without IO, network, download, parser, or writes."""

    _require_mapping(candidate, "official disclosure discovery candidate")
    normalized = {
        "schema_version": _clean_string(
            candidate.get("schema_version", OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_VERSION)
        ),
        "discovery_candidate_id": _clean_string(candidate.get("discovery_candidate_id", "")),
        "stock_code": _clean_string(candidate.get("stock_code", "")),
        "company_name": _clean_string(candidate.get("company_name", "")),
        "exchange": _clean_string(candidate.get("exchange", "")),
        "period_key": _clean_string(candidate.get("period_key", "")),
        "period_end_date": _clean_string(candidate.get("period_end_date", "")),
        "announcement_type": _canonical_enum_value(candidate.get("announcement_type")),
        "source_type": _canonical_source_type(candidate.get("source_type")),
        "source_url": _clean_string(candidate.get("source_url", "")),
        "source_title": _clean_string(candidate.get("source_title", "")),
        "disclosure_date": _clean_string(candidate.get("disclosure_date", "")),
        "discovered_at_utc": _clean_string(candidate.get("discovered_at_utc", "")),
        "discovery_method": _canonical_enum_value(candidate.get("discovery_method")),
        "source_domain": _clean_string(candidate.get("source_domain", "")),
        "raw_candidate_metadata": _normalize_metadata(candidate.get("raw_candidate_metadata", {})),
        "normalized_candidate_metadata": _normalize_metadata(candidate.get("normalized_candidate_metadata", {})),
        "rejection_reason": _clean_string(candidate.get("rejection_reason", "")),
        "caveats": _normalize_caveats(candidate.get("caveats", [])),
        "not_for_trading_advice": candidate.get("not_for_trading_advice"),
    }

    if normalized["source_url"] and not normalized["source_domain"]:
        normalized["source_domain"] = derive_source_domain_from_url(normalized["source_url"])
    if not normalized["discovery_candidate_id"]:
        normalized["discovery_candidate_id"] = build_discovery_candidate_id(normalized)

    rejection_reason = build_discovery_rejection_reason(normalized)
    if rejection_reason and not normalized["rejection_reason"]:
        normalized["rejection_reason"] = rejection_reason

    validate_official_disclosure_discovery_candidate(normalized)
    return normalized


def validate_official_disclosure_discovery_candidate(candidate: Mapping[str, Any]) -> None:
    """Validate discovery candidate metadata and fail closed before registry/locator handoff."""

    _require_mapping(candidate, "official disclosure discovery candidate")
    _require_keys(candidate, OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_REQUIRED_KEYS)
    validate_safety_markers(candidate)
    _assert_no_discovery_forbidden_markers(candidate, path="$")

    if candidate["schema_version"] != OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_VERSION:
        raise OfficialVerificationValidationError("discovery candidate schema_version is unsupported")
    if not isinstance(candidate.get("not_for_trading_advice"), bool) or candidate["not_for_trading_advice"] is not True:
        raise OfficialVerificationValidationError("not_for_trading_advice must be true")

    _require_stock_code(candidate.get("stock_code"), "stock_code")
    for field in ("discovery_candidate_id", "company_name", "exchange", "period_key", "period_end_date", "announcement_type"):
        _require_non_empty_string(candidate.get(field), field)
    _require_iso_date(candidate.get("period_end_date"), "period_end_date")
    _require_non_empty_string(candidate.get("discovered_at_utc"), "discovered_at_utc")
    _require_enum_value(candidate.get("announcement_type"), enum_values(AnnouncementType), "announcement_type")
    _require_enum_value(candidate.get("discovery_method"), enum_values(OfficialDisclosureDiscoveryMethod), "discovery_method")

    source_type = _canonical_source_type(candidate.get("source_type"))
    if candidate.get("source_type") != source_type:
        raise OfficialVerificationValidationError("source_type must be canonical")
    _require_known_source_type(source_type)

    source_url = candidate.get("source_url", "")
    source_domain = candidate.get("source_domain", "")
    if source_url:
        _require_non_empty_string(source_domain, "source_domain")
        derived_domain = derive_source_domain_from_url(source_url)
        if not derived_domain:
            raise OfficialVerificationValidationError("source_url must include a hostname")
        if not _source_domain_matches_url(source_domain, derived_domain):
            raise OfficialVerificationValidationError("source_domain must match source_url hostname")

    _require_mapping(candidate.get("raw_candidate_metadata", {}), "raw_candidate_metadata")
    _require_mapping(candidate.get("normalized_candidate_metadata", {}), "normalized_candidate_metadata")
    _require_list(candidate.get("caveats", []), "caveats")

    if source_type in OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_OFFICIAL_SOURCE_TYPES:
        _require_official_source_metadata(candidate, source_type)
        if candidate.get("rejection_reason"):
            raise OfficialVerificationValidationError("official discovery candidate cannot include rejection_reason")
        return

    _require_non_empty_string(candidate.get("rejection_reason"), "rejection_reason")
    if source_type in OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_PROVIDER_SOURCE_TYPES:
        return
    if source_type in OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_DISCOVERY_ONLY_SOURCE_TYPES:
        return
    if source_type in OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_LOCAL_CACHE_SOURCE_TYPES:
        return
    raise OfficialVerificationValidationError("source_type cannot enter official discovery lane")


def is_official_discovery_source_type(source_type: str) -> bool:
    return _canonical_source_type(source_type) in OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_OFFICIAL_SOURCE_TYPES


def is_discovery_only_source_type(source_type: str) -> bool:
    return _canonical_source_type(source_type) in OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_DISCOVERY_ONLY_SOURCE_TYPES


def is_provider_discovery_source_type(source_type: str) -> bool:
    return _canonical_source_type(source_type) in OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_PROVIDER_SOURCE_TYPES


def derive_source_domain_from_url(url: str) -> str:
    """Return the URL hostname from an explicit string without touching the network."""

    if not isinstance(url, str) or not url.strip():
        return ""
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        return ""
    return (parsed.hostname or "").lower()


def build_discovery_candidate_id(candidate: Mapping[str, Any]) -> str:
    """Build a deterministic ID from explicit metadata only."""

    _require_mapping(candidate, "official disclosure discovery candidate")
    identity = {
        "stock_code": _clean_string(candidate.get("stock_code", "")),
        "company_name": _clean_string(candidate.get("company_name", "")),
        "exchange": _clean_string(candidate.get("exchange", "")),
        "period_key": _clean_string(candidate.get("period_key", "")),
        "period_end_date": _clean_string(candidate.get("period_end_date", "")),
        "announcement_type": _canonical_enum_value(candidate.get("announcement_type")),
        "source_type": _canonical_source_type(candidate.get("source_type")),
        "source_url": _clean_string(candidate.get("source_url", "")),
        "source_title": _clean_string(candidate.get("source_title", "")),
        "disclosure_date": _clean_string(candidate.get("disclosure_date", "")),
        "discovery_method": _canonical_enum_value(candidate.get("discovery_method")),
        "source_domain": _clean_string(candidate.get("source_domain", "")),
    }
    payload = json.dumps(identity, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]
    return f"discovery_candidate_{digest}"


def can_handoff_to_registry(candidate: Mapping[str, Any], *, with_reason: bool = False) -> bool | tuple[bool, str]:
    """Return whether a candidate can explicitly hand off to registry validation."""

    try:
        validate_official_disclosure_discovery_candidate(candidate)
    except OfficialVerificationValidationError as exc:
        return (False, str(exc)) if with_reason else False

    reason = build_discovery_rejection_reason(candidate)
    allowed = not reason and is_official_discovery_source_type(str(candidate.get("source_type", "")))
    if with_reason:
        return allowed, reason
    return allowed


def build_discovery_rejection_reason(candidate: Mapping[str, Any]) -> str:
    """Explain why a candidate cannot enter the registry/locator handoff lane."""

    if not isinstance(candidate, Mapping):
        return OfficialDisclosureDiscoveryRejectionReason.MISSING_REQUIRED_METADATA.value
    if candidate.get("schema_version") not in {None, OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_VERSION}:
        return OfficialDisclosureDiscoveryRejectionReason.UNSUPPORTED_SCHEMA_VERSION.value
    if candidate.get("not_for_trading_advice") is not True:
        return OfficialDisclosureDiscoveryRejectionReason.NOT_FOR_TRADING_ADVICE_REQUIRED.value
    try:
        _assert_no_discovery_forbidden_markers(candidate, path="$")
    except OfficialVerificationValidationError:
        return OfficialDisclosureDiscoveryRejectionReason.FORBIDDEN_MARKER.value

    source_type = _canonical_source_type(candidate.get("source_type"))
    if not source_type or source_type not in _all_discovery_source_types():
        return OfficialDisclosureDiscoveryRejectionReason.UNKNOWN_SOURCE_TYPE.value
    if source_type in OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_PROVIDER_SOURCE_TYPES:
        return OfficialDisclosureDiscoveryRejectionReason.PROVIDER_SOURCE_NOT_OFFICIAL.value
    if source_type == OfficialDisclosureSourceType.MIRROR_SOURCE_CANDIDATE.value:
        return OfficialDisclosureDiscoveryRejectionReason.MIRROR_SOURCE_NOT_OFFICIAL.value
    if source_type == OfficialDisclosureSourceType.UNKNOWN_SOURCE_CANDIDATE.value:
        return OfficialDisclosureDiscoveryRejectionReason.UNKNOWN_SOURCE_TYPE.value
    if source_type in OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_LOCAL_CACHE_SOURCE_TYPES:
        return OfficialDisclosureDiscoveryRejectionReason.LOCAL_CACHE_INERT.value

    missing = [
        field
        for field in (
            "stock_code",
            "company_name",
            "exchange",
            "period_key",
            "period_end_date",
            "announcement_type",
            "discovered_at_utc",
            "discovery_method",
        )
        if _is_blank(candidate.get(field))
    ]
    if missing:
        return OfficialDisclosureDiscoveryRejectionReason.MISSING_REQUIRED_METADATA.value
    if source_type in OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_OFFICIAL_SOURCE_TYPES:
        if _is_blank(candidate.get("source_url")):
            return OfficialDisclosureDiscoveryRejectionReason.MISSING_OFFICIAL_URL.value
        derived_domain = derive_source_domain_from_url(str(candidate.get("source_url", "")))
        if not derived_domain:
            return OfficialDisclosureDiscoveryRejectionReason.INVALID_SOURCE_DOMAIN.value
        if _is_blank(candidate.get("source_title")):
            return OfficialDisclosureDiscoveryRejectionReason.MISSING_SOURCE_TITLE.value
        if _is_blank(candidate.get("disclosure_date")):
            return OfficialDisclosureDiscoveryRejectionReason.MISSING_DISCLOSURE_DATE.value
        if _is_blank(candidate.get("source_domain")):
            return OfficialDisclosureDiscoveryRejectionReason.MISSING_SOURCE_DOMAIN.value
        if not derived_domain or not _source_domain_matches_url(str(candidate.get("source_domain", "")), derived_domain):
            return OfficialDisclosureDiscoveryRejectionReason.INVALID_SOURCE_DOMAIN.value
        allowed_domains = _ALLOWED_DOMAINS_BY_SOURCE_TYPE[source_type]
        if not _domain_allowed(derived_domain, allowed_domains):
            return OfficialDisclosureDiscoveryRejectionReason.INVALID_SOURCE_DOMAIN.value
    return OfficialDisclosureDiscoveryRejectionReason.NONE.value


def _require_official_source_metadata(candidate: Mapping[str, Any], source_type: str) -> None:
    for field in ("source_url", "source_title", "disclosure_date", "source_domain"):
        _require_non_empty_string(candidate.get(field), field)
    _require_iso_date(candidate.get("disclosure_date"), "disclosure_date")
    allowed_domains = _ALLOWED_DOMAINS_BY_SOURCE_TYPE[source_type]
    derived_domain = derive_source_domain_from_url(str(candidate.get("source_url", "")))
    if not _domain_allowed(derived_domain, allowed_domains):
        raise OfficialVerificationValidationError("source_url domain is not allowed for official discovery source type")


def _normalize_metadata(value: Any) -> Any:
    if value is None:
        return {}
    return _normalize_nested(value)


def _normalize_nested(value: Any) -> Any:
    if isinstance(value, str):
        return _clean_string(value)
    if isinstance(value, Mapping):
        return {str(key).strip(): _normalize_nested(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_nested(item) for item in value]
    if isinstance(value, tuple):
        return [_normalize_nested(item) for item in value]
    return value


def _normalize_caveats(value: Any) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        return value
    return [_normalize_nested(item) for item in value]


def _canonical_source_type(value: Any) -> str:
    normalized = _canonical_enum_value(value)
    return _SOURCE_TYPE_ALIASES.get(normalized, normalized)


def _canonical_enum_value(value: Any) -> str:
    return _normalize_marker_text(value)


def _clean_string(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _all_discovery_source_types() -> set[str]:
    return (
        set(OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_OFFICIAL_SOURCE_TYPES)
        | set(OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_DISCOVERY_ONLY_SOURCE_TYPES)
        | set(OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_PROVIDER_SOURCE_TYPES)
        | set(OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_LOCAL_CACHE_SOURCE_TYPES)
    )


def _require_mapping(value: Any, label: str) -> None:
    if not isinstance(value, Mapping):
        raise OfficialVerificationValidationError(f"{label} must be a mapping")


def _require_keys(payload: Mapping[str, Any], required: tuple[str, ...]) -> None:
    missing = [key for key in required if key not in payload]
    if missing:
        raise OfficialVerificationValidationError(f"official disclosure discovery candidate missing keys: {missing}")


def _require_stock_code(value: Any, field: str) -> None:
    if not isinstance(value, str) or not _CODE_RE.fullmatch(value):
        raise OfficialVerificationValidationError(f"{field} must be a 6 digit string")


def _require_known_source_type(value: str) -> None:
    if value not in _all_discovery_source_types():
        raise OfficialVerificationValidationError("source_type must be a known discovery candidate source type")


def _require_enum_value(value: Any, allowed: tuple[str, ...], field: str) -> None:
    if value not in allowed:
        raise OfficialVerificationValidationError(f"{field} must be one of: {sorted(allowed)}")


def _require_non_empty_string(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise OfficialVerificationValidationError(f"{field} must be a non-empty string")


def _require_iso_date(value: Any, field: str) -> None:
    if not isinstance(value, str) or not _ISO_DATE_RE.fullmatch(value):
        raise OfficialVerificationValidationError(f"{field} must be an ISO date string")


def _require_list(value: Any, field: str) -> None:
    if not isinstance(value, list):
        raise OfficialVerificationValidationError(f"{field} must be a list")


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _source_domain_matches_url(source_domain: str, derived_domain: str) -> bool:
    domain = source_domain.strip().lower()
    host = derived_domain.strip().lower()
    return bool(domain and host and (domain == host or host.endswith(f".{domain}") or domain.endswith(f".{host}")))


def _domain_allowed(domain: str, allowed_domains: tuple[str, ...]) -> bool:
    return any(domain == allowed or domain.endswith(f".{allowed}") for allowed in allowed_domains)


def _assert_no_discovery_forbidden_markers(payload: Any, *, path: str) -> None:
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            normalized_key = _normalize_marker_text(key)
            if _key_has_forbidden_marker(normalized_key):
                raise OfficialVerificationValidationError(f"forbidden discovery marker key at {path}.{key}")
            if str(key) == "source_url":
                _assert_source_url_has_no_secret_marker(value, path=f"{path}.{key}")
            else:
                _assert_no_discovery_forbidden_markers(value, path=f"{path}.{key}")
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            _assert_no_discovery_forbidden_markers(value, path=f"{path}[{index}]")
    elif isinstance(payload, str):
        marker = _string_forbidden_marker(payload)
        if marker:
            raise OfficialVerificationValidationError(f"forbidden discovery marker value at {path}: {marker}")


def _assert_source_url_has_no_secret_marker(value: Any, *, path: str) -> None:
    if not isinstance(value, str):
        return
    lowered = value.lower()
    if "tushare_token.txt" in lowered or ".env" in lowered or re.search(r"\btoken\b", lowered):
        raise OfficialVerificationValidationError(f"forbidden discovery marker value at {path}")


def _key_has_forbidden_marker(normalized_key: str) -> bool:
    if normalized_key == "not_for_trading_advice":
        return False
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
    lowered = value.lower()
    normalized = _normalize_marker_text(value)
    if "tushare_token.txt" in lowered:
        return "tushare_token.txt"
    if ".env" in lowered:
        return ".env"
    if re.search(r"\btoken\b", lowered):
        return "token"
    if _STANDALONE_HTTP_RE.search(value):
        return "HTTP"
    for marker in _DISCOVERY_FORBIDDEN_ENGLISH_MARKERS + _DISCOVERY_HIDDEN_PROMOTION_MARKERS:
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


def _all_marker_phrases() -> tuple[str, ...]:
    return (
        _DISCOVERY_FORBIDDEN_ENGLISH_MARKERS
        + _DISCOVERY_FORBIDDEN_CJK_MARKERS
        + _DISCOVERY_HIDDEN_PROMOTION_MARKERS
    )


def _normalize_marker_text(value: Any) -> str:
    raw = _clean_string(value)
    camel_split = _CAMEL_SPLIT_RE.sub("_", raw)
    lowered = camel_split.lower()
    lowered = re.sub(r"[\s\-\.]+", "_", lowered)
    lowered = re.sub(r"_+", "_", lowered).strip("_")
    return lowered
