# -*- coding: utf-8 -*-
"""Source registry policy helpers for official verification."""

from __future__ import annotations

from typing import Any, Mapping

from .schemas import (
    DISCOVERY_ONLY_SOURCE_TYPES,
    OFFICIAL_SOURCE_REQUIRED_FIELDS,
    OFFICIAL_SOURCE_TYPES,
    PROVIDER_SOURCE_TYPES,
)
from .validators import OfficialVerificationValidationError, validate_official_source_candidate


def is_official_source_type(source_type: str) -> bool:
    return source_type in OFFICIAL_SOURCE_TYPES


def is_discovery_only_source_type(source_type: str) -> bool:
    return source_type in DISCOVERY_ONLY_SOURCE_TYPES


def is_provider_source_type(source_type: str) -> bool:
    return source_type in PROVIDER_SOURCE_TYPES


def source_has_required_official_fields(candidate: Mapping[str, Any]) -> bool:
    return all(_has_value(candidate.get(key)) for key in OFFICIAL_SOURCE_REQUIRED_FIELDS)


def can_source_be_accepted_as_official(candidate: Mapping[str, Any]) -> bool:
    """Return whether a source candidate is eligible as official fact source."""

    validate_official_source_candidate(candidate)
    return (
        candidate.get("accepted_as_official") is True
        and is_official_source_type(str(candidate.get("candidate_source_type")))
        and source_has_required_official_fields(candidate)
    )


def assert_source_eligible_for_verified_use(candidate: Mapping[str, Any]) -> None:
    """Raise if a source cannot support verified official metrics."""

    if not can_source_be_accepted_as_official(candidate):
        raise OfficialVerificationValidationError("source is not eligible for verified official use")


def validate_source_refresh_policy(candidate: Mapping[str, Any]) -> None:
    """Validate source refresh policy and registry version requirements."""

    validate_official_source_candidate(candidate)
    if not _has_value(candidate.get("source_refresh_policy")):
        raise OfficialVerificationValidationError("source_refresh_policy is required")
    if not _has_value(candidate.get("registry_version")):
        raise OfficialVerificationValidationError("registry_version is required")


def _has_value(value: Any) -> bool:
    return value is not None and (not isinstance(value, str) or bool(value.strip()))
