# -*- coding: utf-8 -*-
"""Production skeleton for official metric verification.

This package is intentionally pure and in-memory. It does not download,
parse, fetch provider data, write report artifacts, or touch token files.
"""

from .conflict_gate import (
    build_blocked_until_review_item,
    build_conflict_record,
    can_promote_to_verified,
    classify_provider_official_match,
    validate_promotion_gate,
)
from .schemas import (
    BLOCKED_UNTIL_REVIEW_ITEM_VERSION,
    OFFICIAL_METRIC_FACT_VERSION,
    OFFICIAL_SOURCE_CANDIDATE_VERSION,
    OFFICIAL_VERIFICATION_RUN_SUMMARY_VERSION,
    PROVIDER_OFFICIAL_CONFLICT_VERSION,
    ConflictType,
    ExtractionQuality,
    MetricType,
    NormalizedUnit,
    OfficialConfidence,
    PeriodType,
    PromotionGateResult,
    SourceType,
    VerificationStatus,
)
from .validators import (
    OfficialVerificationValidationError,
    validate_blocked_until_review_item,
    validate_official_metric_fact,
    validate_official_source_candidate,
    validate_official_verification_run_summary,
    validate_provider_official_conflict,
    validate_safety_markers,
)

__all__ = [
    "BLOCKED_UNTIL_REVIEW_ITEM_VERSION",
    "OFFICIAL_METRIC_FACT_VERSION",
    "OFFICIAL_SOURCE_CANDIDATE_VERSION",
    "OFFICIAL_VERIFICATION_RUN_SUMMARY_VERSION",
    "PROVIDER_OFFICIAL_CONFLICT_VERSION",
    "ConflictType",
    "ExtractionQuality",
    "MetricType",
    "NormalizedUnit",
    "OfficialConfidence",
    "OfficialVerificationValidationError",
    "PeriodType",
    "PromotionGateResult",
    "SourceType",
    "VerificationStatus",
    "build_blocked_until_review_item",
    "build_conflict_record",
    "can_promote_to_verified",
    "classify_provider_official_match",
    "validate_blocked_until_review_item",
    "validate_official_metric_fact",
    "validate_official_source_candidate",
    "validate_official_verification_run_summary",
    "validate_provider_official_conflict",
    "validate_promotion_gate",
    "validate_safety_markers",
]
