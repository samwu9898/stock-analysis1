# -*- coding: utf-8 -*-
"""Pure policy helpers for official disclosure source registry entries."""

from __future__ import annotations

import re
from typing import Any, Mapping

from .schemas import (
    OFFICIAL_DISCLOSURE_CACHE_SOURCE_TYPES,
    OFFICIAL_DISCLOSURE_DISCOVERY_ONLY_SOURCE_TYPES,
    OFFICIAL_DISCLOSURE_OFFICIAL_SOURCE_TYPES,
    OFFICIAL_DISCLOSURE_PROVIDER_SOURCE_TYPES,
    OFFICIAL_DISCLOSURE_SELECTABLE_SOURCE_STATUSES,
    OfficialDisclosureSourceStatus,
    OfficialDisclosureSourceType,
)
from .validators import OfficialVerificationValidationError, validate_official_source_registry_entry


_SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")


def is_official_source_type(source_type: str) -> bool:
    return source_type in OFFICIAL_DISCLOSURE_OFFICIAL_SOURCE_TYPES


def is_discovery_only_source_type(source_type: str) -> bool:
    return source_type in OFFICIAL_DISCLOSURE_DISCOVERY_ONLY_SOURCE_TYPES


def is_provider_source_type(source_type: str) -> bool:
    return source_type in OFFICIAL_DISCLOSURE_PROVIDER_SOURCE_TYPES


def validate_sha256(value: Any) -> None:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise OfficialVerificationValidationError("file_sha256 must be a sha256 hex digest")


def build_source_conflict_reason(*, source_url: str, previous_sha256: str, current_sha256: str) -> str:
    validate_sha256(previous_sha256)
    validate_sha256(current_sha256)
    if not source_url:
        raise OfficialVerificationValidationError("source_url is required for source_conflict reason")
    if previous_sha256 == current_sha256:
        raise OfficialVerificationValidationError("source_conflict requires different sha256 values")
    return (
        "source_conflict: same source_url has different file_sha256; "
        f"source_url={source_url}; previous_sha256={previous_sha256}; current_sha256={current_sha256}"
    )


def can_enter_official_candidate_lane(entry: Mapping[str, Any]) -> bool:
    validate_official_source_registry_entry(entry)
    return (
        entry.get("source_status") == OfficialDisclosureSourceStatus.OFFICIAL_CANDIDATE.value
        and entry.get("source_type") in OFFICIAL_DISCLOSURE_OFFICIAL_SOURCE_TYPES
    )


def can_enter_official_cache_lane(entry: Mapping[str, Any]) -> bool:
    validate_official_source_registry_entry(entry)
    return (
        entry.get("source_status") == OfficialDisclosureSourceStatus.OFFICIAL_CACHED.value
        and entry.get("source_type") in OFFICIAL_DISCLOSURE_CACHE_SOURCE_TYPES | OFFICIAL_DISCLOSURE_OFFICIAL_SOURCE_TYPES
    )


def classify_source_status(entry_or_candidate: Mapping[str, Any]) -> str:
    source_type = str(entry_or_candidate.get("source_type") or entry_or_candidate.get("candidate_source_type") or "")
    if source_type == OfficialDisclosureSourceType.MIRROR_SOURCE_CANDIDATE.value:
        return OfficialDisclosureSourceStatus.REJECTED_MIRROR.value
    if source_type == OfficialDisclosureSourceType.PROVIDER_SOURCE_CANDIDATE.value:
        return OfficialDisclosureSourceStatus.REJECTED_PROVIDER_ENDPOINT.value
    if source_type == OfficialDisclosureSourceType.UNKNOWN_SOURCE_CANDIDATE.value:
        return OfficialDisclosureSourceStatus.BLOCKED_UNTIL_REVIEW.value
    if source_type == OfficialDisclosureSourceType.LOCAL_OFFICIAL_CACHE.value:
        if not entry_or_candidate.get("source_url"):
            return OfficialDisclosureSourceStatus.BLOCKED_UNTIL_REVIEW.value
        if not entry_or_candidate.get("file_sha256"):
            return OfficialDisclosureSourceStatus.MISSING_SHA256.value
        return OfficialDisclosureSourceStatus.OFFICIAL_CACHED.value
    if _missing_required_metadata(entry_or_candidate):
        return OfficialDisclosureSourceStatus.MISSING_REQUIRED_METADATA.value
    if source_type in OFFICIAL_DISCLOSURE_OFFICIAL_SOURCE_TYPES:
        return OfficialDisclosureSourceStatus.OFFICIAL_CANDIDATE.value
    return OfficialDisclosureSourceStatus.BLOCKED_UNTIL_REVIEW.value


def is_selectable_official_entry(entry: Mapping[str, Any]) -> bool:
    return (
        entry.get("source_status") in OFFICIAL_DISCLOSURE_SELECTABLE_SOURCE_STATUSES
        and entry.get("source_type") in OFFICIAL_DISCLOSURE_OFFICIAL_SOURCE_TYPES | OFFICIAL_DISCLOSURE_CACHE_SOURCE_TYPES
    )


def _missing_required_metadata(entry: Mapping[str, Any]) -> bool:
    return any(
        not entry.get(key)
        for key in ("source_title", "disclosure_date", "period_key", "period_end_date", "announcement_type")
    )
