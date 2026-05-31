# -*- coding: utf-8 -*-
"""Facade helpers for the minimal official verification production slice."""

from __future__ import annotations

from typing import Any, Mapping

from .conflict_gate import can_promote_to_verified, classify_provider_official_match, validate_promotion_gate
from .validators import (
    validate_blocked_until_review_item,
    validate_official_metric_fact,
    validate_official_source_candidate,
    validate_official_verification_run_summary,
    validate_provider_official_conflict,
    validate_safety_markers,
)


def validate_official_verification_artifact(payload: Mapping[str, Any], *, artifact_type: str) -> None:
    """Validate one official verification artifact by explicit type."""

    validators = {
        "official_metric_fact.v1": validate_official_metric_fact,
        "official_source_candidate.v1": validate_official_source_candidate,
        "provider_official_conflict.v1": validate_provider_official_conflict,
        "blocked_until_review_item.v1": validate_blocked_until_review_item,
        "official_verification_run_summary.v1": validate_official_verification_run_summary,
    }
    try:
        validator = validators[artifact_type]
    except KeyError as exc:
        raise ValueError(f"unsupported official verification artifact type: {artifact_type}") from exc
    validator(payload)


__all__ = [
    "can_promote_to_verified",
    "classify_provider_official_match",
    "validate_blocked_until_review_item",
    "validate_official_metric_fact",
    "validate_official_source_candidate",
    "validate_official_verification_artifact",
    "validate_official_verification_run_summary",
    "validate_provider_official_conflict",
    "validate_promotion_gate",
    "validate_safety_markers",
]
