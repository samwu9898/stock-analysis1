# -*- coding: utf-8 -*-
"""Pure validation helpers for official verification payloads."""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Iterable, Mapping

from .schemas import (
    BLOCKED_UNTIL_REVIEW_ITEM_REQUIRED_KEYS,
    BLOCKED_UNTIL_REVIEW_ITEM_VERSION,
    DERIVED_METRIC_DEPENDENCIES,
    DISCOVERY_ONLY_SOURCE_TYPES,
    OFFICIAL_METRIC_FACT_REQUIRED_KEYS,
    OFFICIAL_METRIC_FACT_VERSION,
    OFFICIAL_SOURCE_CANDIDATE_REQUIRED_KEYS,
    OFFICIAL_SOURCE_CANDIDATE_VERSION,
    OFFICIAL_SOURCE_REQUIRED_FIELDS,
    OFFICIAL_SOURCE_TYPES,
    OFFICIAL_VERIFICATION_RUN_SUMMARY_REQUIRED_KEYS,
    OFFICIAL_VERIFICATION_RUN_SUMMARY_VERSION,
    PROVIDER_OFFICIAL_CONFLICT_REQUIRED_KEYS,
    PROVIDER_OFFICIAL_CONFLICT_VERSION,
    PROVIDER_SOURCE_TYPES,
    AnnouncementType,
    ConflictType,
    ExtractionQuality,
    MetricType,
    NormalizedUnit,
    OfficialConfidence,
    PeriodType,
    ResolutionStatus,
    Severity,
    StatementScope,
    SourceType,
    VerificationStatus,
)


class OfficialVerificationValidationError(ValueError):
    """Raised when an official verification payload violates policy."""


_CODE_RE = re.compile(r"^\d{6}$")
_SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")

_FORBIDDEN_EXACT_KEYS = {
    "buy",
    "sell",
    "hold",
    "buying",
    "selling",
    "accumulate",
    "reduce",
    "overweight",
    "underweight",
    "target_price",
    "price_target",
    "position",
    "position_size",
    "portfolio",
    "portfolio_weight",
    "technical_signal",
    "trading_signal",
    "buy_signal",
    "sell_signal",
    "hold_signal",
    "buy_recommendation",
    "sell_recommendation",
    "hold_recommendation",
    "买入",
    "卖出",
    "持有",
    "目标价",
    "仓位",
    "配置比例",
    "技术信号",
    "交易信号",
    "report_v1_trigger",
    "accepted_manifest_write",
    "accepted_manifest_write_intent",
    "output_baseline_write",
    "output_baseline_write_intent",
    "token_read",
    "token_read_intent",
    "provider_live_call",
    "network_intent",
    "download_pdf",
    "parse_pdf",
}

_FORBIDDEN_KEY_ALIASES = {
    "target price": "target_price",
    "price target": "price_target",
    "portfolio weight": "portfolio_weight",
    "position size": "position_size",
    "technical signal": "technical_signal",
    "trading signal": "trading_signal",
    "buy signal": "buy_signal",
    "sell signal": "sell_signal",
    "hold signal": "hold_signal",
    "buy recommendation": "buy_recommendation",
    "sell recommendation": "sell_recommendation",
    "hold recommendation": "hold_recommendation",
}

_FORBIDDEN_VALUE_MARKERS = (
    "tushare_token.txt",
    ".env",
    "read token",
    "read_token",
    "api_key=",
    "authorization: bearer",
    "target price",
    "buy recommendation",
    "sell recommendation",
    "hold recommendation",
    "portfolio position",
    "technical signal",
    "trading signal",
    "buy signal",
    "sell signal",
    "hold signal",
    "report v1 trigger",
    "report_v1_trigger",
    "accepted manifest write",
    "accepted_manifest_write",
    "output baseline write",
    "output_baseline_write",
    "provider live call",
    "provider_live_call",
    "akshare live",
    "tushare live",
    "cninfo live",
    "sse live",
    "network intent",
    "network_intent",
    "download pdf",
    "download_pdf",
    "parse pdf",
    "parse_pdf",
)

_FORBIDDEN_VALUE_PATTERNS = tuple(
    re.compile(pattern, flags=re.IGNORECASE)
    for pattern in (
        r"\bbuy\b",
        r"\bsell\b",
        r"\bhold\b",
        r"\bbuying\b",
        r"\bselling\b",
        r"\baccumulate\b",
        r"\breduce\b",
        r"\boverweight\b",
        r"\bunderweight\b",
        r"\btarget[\s_-]?price\b",
        r"\bprice[\s_-]?target\b",
        r"\bportfolio(?:[\s_-]?weight)?\b",
        r"\bposition(?:[\s_-]?size)?\b",
        r"\btechnical[\s_-]?signal\b",
        r"\btrading[\s_-]?signal\b",
        r"\bbuy[\s_-]?signal\b",
        r"\bsell[\s_-]?signal\b",
        r"\bhold[\s_-]?signal\b",
        r"\bbuy[\s_-]?recommendation\b",
        r"\bsell[\s_-]?recommendation\b",
        r"\bhold[\s_-]?recommendation\b",
    )
)

_FORBIDDEN_CJK_VALUE_MARKERS = (
    "买入",
    "卖出",
    "持有",
    "目标价",
    "仓位",
    "配置比例",
    "技术信号",
    "交易信号",
)

_FORBIDDEN_VERIFIED_SOURCE_MARKERS = (
    "akshare",
    "tushare",
    "provider_endpoint",
    "provider_fact",
    "provider_source",
    "mirror",
    "third_party",
    "web_snippet",
    "source_candidate",
)

_VERIFIED_SOURCE_HINT_FIELDS = (
    "source_ref",
    "source_url_or_path",
    "source_name",
)

_VERIFIED_SOURCE_TYPE_FIELDS = (
    "source_type",
    "official_source_type",
    "candidate_source_type",
)


def validate_safety_markers(payload: Any) -> None:
    """Reject trading, token, network, Report V1, and write-intent markers."""

    _assert_no_forbidden_markers(payload, path="$")
    _assert_not_for_trading_advice_recursive(payload, path="$", require_top_level=isinstance(payload, Mapping))


def validate_official_source_candidate(candidate: Mapping[str, Any]) -> None:
    """Validate `official_source_candidate.v1` and source acceptance policy."""

    _require_mapping(candidate, "official source candidate")
    _validate_optional_schema_version(candidate, OFFICIAL_SOURCE_CANDIDATE_VERSION)
    _require_keys(candidate, OFFICIAL_SOURCE_CANDIDATE_REQUIRED_KEYS, "official source candidate")
    validate_safety_markers(candidate)

    _require_stock_code(candidate.get("stock_code"), "stock_code")
    _require_enum(candidate.get("candidate_source_type"), SourceType, "candidate_source_type")
    _require_enum(candidate.get("announcement_type"), AnnouncementType, "announcement_type")
    _require_bool(candidate.get("is_official_candidate"), "is_official_candidate")
    _require_bool(candidate.get("is_mirror"), "is_mirror")
    _require_bool(candidate.get("accepted_as_official"), "accepted_as_official")
    _require_non_empty_string(candidate.get("source_refresh_policy"), "source_refresh_policy")
    _require_non_empty_string(candidate.get("registry_version"), "registry_version")

    source_type = candidate["candidate_source_type"]
    accepted = candidate["accepted_as_official"] is True
    if candidate["is_mirror"] or source_type in DISCOVERY_ONLY_SOURCE_TYPES:
        if accepted:
            raise OfficialVerificationValidationError("mirror or third-party source cannot be accepted as official")
    if source_type in PROVIDER_SOURCE_TYPES and accepted:
        raise OfficialVerificationValidationError("provider endpoint cannot be accepted as official fact")
    if accepted:
        if source_type not in OFFICIAL_SOURCE_TYPES:
            raise OfficialVerificationValidationError("accepted official source must use an official source type")
        missing = [key for key in OFFICIAL_SOURCE_REQUIRED_FIELDS if _is_blank(candidate.get(key))]
        if missing:
            raise OfficialVerificationValidationError(f"accepted official source missing fields: {missing}")
        _require_sha256(candidate.get("file_sha256"), "file_sha256")
    elif not _is_blank(candidate.get("file_sha256")):
        _require_sha256(candidate.get("file_sha256"), "file_sha256")


def validate_official_metric_fact(fact: Mapping[str, Any]) -> None:
    """Validate `official_metric_fact.v1` and verification lane policy."""

    _require_mapping(fact, "official metric fact")
    _validate_optional_schema_version(fact, OFFICIAL_METRIC_FACT_VERSION)
    _require_keys(fact, OFFICIAL_METRIC_FACT_REQUIRED_KEYS, "official metric fact")
    validate_safety_markers(fact)

    _require_stock_code(fact.get("stock_code"), "stock_code")
    _require_present_value(fact.get("raw_value"), "raw_value")
    _require_non_empty_string(fact.get("raw_unit"), "raw_unit")
    _require_present_value(fact.get("normalized_value"), "normalized_value")
    _require_non_empty_string(fact.get("normalized_unit"), "normalized_unit")
    _require_non_empty_string(fact.get("row_label"), "row_label")
    _require_non_empty_string(fact.get("column_label"), "column_label")
    _require_non_empty_string(fact.get("verifier"), "verifier")
    _require_enum(fact.get("period_type"), PeriodType, "period_type")
    _require_enum(fact.get("statement_scope"), StatementScope, "statement_scope")
    _require_enum(fact.get("announcement_type"), AnnouncementType, "announcement_type")
    _require_enum(fact.get("normalized_unit"), NormalizedUnit, "normalized_unit")
    _require_enum(fact.get("extraction_quality"), ExtractionQuality, "extraction_quality")
    _require_enum(fact.get("verification_status"), VerificationStatus, "verification_status")
    _require_enum(fact.get("official_confidence"), OfficialConfidence, "official_confidence")
    if "metric_type" in fact:
        _require_enum(fact.get("metric_type"), MetricType, "metric_type")
    _require_list(fact.get("dependency_refs"), "dependency_refs")
    _require_list(fact.get("conflict_refs"), "conflict_refs")
    _require_list(fact.get("caveats"), "caveats")
    if _is_blank(fact.get("file_sha256")):
        raise OfficialVerificationValidationError("official metric fact requires file_sha256")
    _require_sha256(fact.get("file_sha256"), "file_sha256")

    if _is_derived_metric(fact):
        if not fact["dependency_refs"]:
            raise OfficialVerificationValidationError("derived metric requires dependency_refs")

    if fact["verification_status"] == VerificationStatus.VERIFIED.value:
        _validate_verified_metric_fact(fact)


def validate_provider_official_conflict(conflict: Mapping[str, Any]) -> None:
    """Validate `provider_official_conflict.v1`."""

    _require_mapping(conflict, "provider official conflict")
    _validate_optional_schema_version(conflict, PROVIDER_OFFICIAL_CONFLICT_VERSION)
    _require_keys(conflict, PROVIDER_OFFICIAL_CONFLICT_REQUIRED_KEYS, "provider official conflict")
    validate_safety_markers(conflict)

    _require_stock_code(conflict.get("stock_code"), "stock_code")
    _require_enum(conflict.get("normalized_unit"), NormalizedUnit, "normalized_unit")
    _require_enum(conflict.get("conflict_type"), ConflictType, "conflict_type")
    _require_enum(conflict.get("severity"), Severity, "severity")
    _require_enum(conflict.get("resolution_status"), ResolutionStatus, "resolution_status")
    if conflict["conflict_type"] in {
        ConflictType.ADJUSTED_BASIS_MISMATCH.value,
        ConflictType.NUMERATOR_POLICY_CONFLICT.value,
        ConflictType.OFFICIAL_PROVIDER_CONFLICT.value,
        ConflictType.PROVIDER_PROVIDER_CONFLICT.value,
    } and conflict["severity"] == Severity.INFO.value:
        raise OfficialVerificationValidationError("conflict severity cannot be info for blocking conflict types")


def validate_blocked_until_review_item(item: Mapping[str, Any]) -> None:
    """Validate `blocked_until_review_item.v1`."""

    _require_mapping(item, "blocked until review item")
    _validate_optional_schema_version(item, BLOCKED_UNTIL_REVIEW_ITEM_VERSION)
    _require_keys(item, BLOCKED_UNTIL_REVIEW_ITEM_REQUIRED_KEYS, "blocked until review item")
    validate_safety_markers(item)

    _require_stock_code(item.get("stock_code"), "stock_code")
    _require_non_empty_string(item.get("blocked_reason"), "blocked_reason")
    _require_non_empty_string(item.get("next_action"), "next_action")
    _require_non_empty_string(item.get("review_owner"), "review_owner")
    if not _is_blank(item.get("extraction_quality")):
        _require_enum(item.get("extraction_quality"), ExtractionQuality, "extraction_quality")


def validate_official_verification_run_summary(summary: Mapping[str, Any]) -> None:
    """Validate `official_verification_run_summary.v1`."""

    _require_mapping(summary, "official verification run summary")
    _validate_optional_schema_version(summary, OFFICIAL_VERIFICATION_RUN_SUMMARY_VERSION)
    _require_keys(summary, OFFICIAL_VERIFICATION_RUN_SUMMARY_REQUIRED_KEYS, "official verification run summary")
    validate_safety_markers(summary)

    if summary["schema_version"] != OFFICIAL_VERIFICATION_RUN_SUMMARY_VERSION:
        raise OfficialVerificationValidationError("official verification run summary schema_version is unsupported")
    _require_stock_code(summary.get("stock_code"), "stock_code")
    _require_non_empty_string(summary.get("source_registry_version"), "source_registry_version")
    for key in ("metric_count", "verified_count", "candidate_count", "conflict_count", "blocked_count"):
        _require_non_negative_int(summary.get(key), key)
    if not isinstance(summary.get("extraction_quality_summary"), Mapping):
        raise OfficialVerificationValidationError("extraction_quality_summary must be a mapping")
    _require_list(summary.get("unresolved_conflict_refs"), "unresolved_conflict_refs")
    _require_list(summary.get("blocked_item_refs"), "blocked_item_refs")


def _validate_verified_metric_fact(fact: Mapping[str, Any]) -> None:
    if fact["extraction_quality"] == ExtractionQuality.LOW.value:
        raise OfficialVerificationValidationError("extraction_quality=low cannot be verified")
    if fact["extraction_quality"] == ExtractionQuality.MEDIUM.value:
        _require_non_empty_string(fact.get("reviewer"), "reviewer")
    if fact["conflict_refs"]:
        raise OfficialVerificationValidationError("verified metric cannot retain unresolved conflict_refs")
    for key in (
        "source_ref",
        "page_or_anchor",
        "table_title",
        "row_label",
        "column_label",
        "announcement_title",
        "disclosure_date",
        "verifier",
    ):
        _require_non_empty_string(fact.get(key), key)
    _validate_verified_source_lineage(fact)


def _validate_verified_source_lineage(fact: Mapping[str, Any]) -> None:
    for field in _VERIFIED_SOURCE_TYPE_FIELDS:
        if field not in fact or _is_blank(fact.get(field)):
            continue
        source_type = fact[field]
        if source_type not in OFFICIAL_SOURCE_TYPES:
            raise OfficialVerificationValidationError(f"{field} must be an official source type for verified fact")

    for field in _VERIFIED_SOURCE_HINT_FIELDS:
        value = fact.get(field)
        if _is_blank(value):
            continue
        normalized_value = _normalize_marker_key(value)
        for marker in _FORBIDDEN_VERIFIED_SOURCE_MARKERS:
            if marker in normalized_value:
                raise OfficialVerificationValidationError(f"{field} cannot reference provider, mirror, or source candidate lineage")


def _is_derived_metric(fact: Mapping[str, Any]) -> bool:
    if fact.get("metric_type") == MetricType.DERIVED.value:
        return True
    return str(fact.get("metric_id") or "") in DERIVED_METRIC_DEPENDENCIES


def _validate_optional_schema_version(payload: Mapping[str, Any], expected: str) -> None:
    version = payload.get("schema_version", payload.get("version"))
    if version is not None and version != expected:
        raise OfficialVerificationValidationError(f"unsupported schema version: {version!r}")


def _require_mapping(value: Any, label: str) -> None:
    if not isinstance(value, Mapping):
        raise OfficialVerificationValidationError(f"{label} must be a mapping")


def _require_keys(payload: Mapping[str, Any], required: Iterable[str], label: str) -> None:
    missing = [key for key in required if key not in payload]
    if missing:
        raise OfficialVerificationValidationError(f"{label} missing keys: {missing}")


def _require_stock_code(value: Any, field: str) -> None:
    if not isinstance(value, str) or not _CODE_RE.fullmatch(value):
        raise OfficialVerificationValidationError(f"{field} must be a 6 digit string")


def _require_enum(value: Any, enum_cls: type[Enum], field: str) -> None:
    allowed = {item.value for item in enum_cls}
    if value not in allowed:
        raise OfficialVerificationValidationError(f"{field} must be one of: {sorted(allowed)}")


def _require_bool(value: Any, field: str) -> None:
    if not isinstance(value, bool):
        raise OfficialVerificationValidationError(f"{field} must be a bool")


def _require_list(value: Any, field: str) -> None:
    if not isinstance(value, list):
        raise OfficialVerificationValidationError(f"{field} must be a list")


def _require_non_empty_string(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise OfficialVerificationValidationError(f"{field} must be a non-empty string")


def _require_present_value(value: Any, field: str) -> None:
    if value is None:
        raise OfficialVerificationValidationError(f"{field} must not be None")


def _require_non_negative_int(value: Any, field: str) -> None:
    if not isinstance(value, int) or value < 0:
        raise OfficialVerificationValidationError(f"{field} must be a non-negative integer")


def _require_sha256(value: Any, field: str) -> None:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise OfficialVerificationValidationError(f"{field} must be a sha256 hex digest")


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _assert_not_for_trading_advice_recursive(payload: Any, *, path: str, require_top_level: bool) -> None:
    if isinstance(payload, Mapping):
        if require_top_level and payload.get("not_for_trading_advice") is not True:
            raise OfficialVerificationValidationError("not_for_trading_advice must be true")
        if "not_for_trading_advice" in payload and payload["not_for_trading_advice"] is not True:
            raise OfficialVerificationValidationError(f"{path}.not_for_trading_advice must be true")
        for key, value in payload.items():
            _assert_not_for_trading_advice_recursive(value, path=f"{path}.{key}", require_top_level=False)
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            _assert_not_for_trading_advice_recursive(value, path=f"{path}[{index}]", require_top_level=False)


def _assert_no_forbidden_markers(payload: Any, *, path: str) -> None:
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            normalized_key = _normalize_marker_key(key)
            if normalized_key in _FORBIDDEN_EXACT_KEYS:
                raise OfficialVerificationValidationError(f"forbidden marker key at {path}.{key}")
            _assert_no_forbidden_markers(value, path=f"{path}.{key}")
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            _assert_no_forbidden_markers(value, path=f"{path}[{index}]")
    elif isinstance(payload, str):
        lowered = payload.lower()
        for marker in _FORBIDDEN_VALUE_MARKERS:
            if marker in lowered:
                raise OfficialVerificationValidationError(f"forbidden marker value at {path}: {marker}")
        for marker in _FORBIDDEN_CJK_VALUE_MARKERS:
            if marker in payload:
                raise OfficialVerificationValidationError(f"forbidden marker value at {path}: {marker}")
        for pattern in _FORBIDDEN_VALUE_PATTERNS:
            if pattern.search(payload):
                raise OfficialVerificationValidationError(f"forbidden marker value at {path}: {pattern.pattern}")


def _normalize_marker_key(key: Any) -> str:
    raw = str(key).strip()
    camel_split = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", raw)
    lowered = camel_split.lower()
    lowered = re.sub(r"[\s\-\.]+", "_", lowered)
    lowered = re.sub(r"_+", "_", lowered).strip("_")
    if lowered in _FORBIDDEN_KEY_ALIASES:
        return _FORBIDDEN_KEY_ALIASES[lowered]
    return lowered
