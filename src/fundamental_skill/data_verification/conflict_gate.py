# -*- coding: utf-8 -*-
"""Pure conflict classification and promotion gate helpers."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from .schemas import (
    BLOCKED_UNTIL_REVIEW_ITEM_VERSION,
    PROVIDER_OFFICIAL_CONFLICT_VERSION,
    ConflictType,
    ExtractionQuality,
    NormalizedUnit,
    PROMOTABLE_GATE_RESULTS,
    PromotionGateResult,
    ResolutionStatus,
    Severity,
)
from .validators import (
    OfficialVerificationValidationError,
    validate_blocked_until_review_item,
    validate_official_metric_fact,
    validate_provider_official_conflict,
)


def classify_provider_official_match(
    *,
    provider_value: Any,
    official_value: Any,
    normalized_unit: str,
    provider_period_key: str | None = None,
    official_period_key: str | None = None,
    provider_normalized_unit: str | None = None,
    official_normalized_unit: str | None = None,
    provider_raw_field: str | None = None,
    official_raw_field: str | None = None,
    adjusted_basis_match: bool = True,
    numerator_policy_match: bool = True,
    provider_provider_conflict: bool = False,
    extraction_quality: str = ExtractionQuality.HIGH.value,
) -> dict[str, Any]:
    """Classify a provider-vs-official comparison without IO."""

    if extraction_quality == ExtractionQuality.LOW.value:
        return _gate(PromotionGateResult.EXTRACTION_QUALITY_LOW.value, lane="blocked", blocked_reason="extraction_quality_low")
    if provider_provider_conflict:
        return _gate(PromotionGateResult.PROVIDER_PROVIDER_CONFLICT.value, lane="candidate", conflict_type=ConflictType.PROVIDER_PROVIDER_CONFLICT.value)
    if provider_normalized_unit and official_normalized_unit and provider_normalized_unit != official_normalized_unit:
        return _gate(PromotionGateResult.UNIT_MISMATCH.value, lane="blocked", blocked_reason="unit_mismatch")
    if provider_period_key and official_period_key and provider_period_key != official_period_key:
        return _gate(PromotionGateResult.PERIOD_MISMATCH.value, lane="blocked", blocked_reason="period_mismatch")
    if provider_raw_field and official_raw_field and provider_raw_field != official_raw_field:
        return _gate(PromotionGateResult.RAW_FIELD_MISMATCH.value, lane="blocked", blocked_reason="raw_field_mismatch")
    if not adjusted_basis_match:
        return _gate(PromotionGateResult.ADJUSTED_BASIS_MISMATCH.value, lane="conflict", conflict_type=ConflictType.ADJUSTED_BASIS_MISMATCH.value)
    if not numerator_policy_match:
        return _gate(PromotionGateResult.NUMERATOR_POLICY_CONFLICT.value, lane="conflict", conflict_type=ConflictType.NUMERATOR_POLICY_CONFLICT.value)
    if _has_non_finite_number(provider_value) or _has_non_finite_number(official_value):
        return _gate(PromotionGateResult.OFFICIAL_PROVIDER_CONFLICT.value, lane="conflict", conflict_type=ConflictType.OFFICIAL_PROVIDER_CONFLICT.value)
    if provider_value == official_value:
        return _gate(PromotionGateResult.EXACT_MATCH.value, lane="verified", tolerance_basis="exact")
    if _within_rounding_tolerance(provider_value, official_value, normalized_unit):
        return _gate(PromotionGateResult.ROUNDING_TOLERANCE.value, lane="verified", tolerance_basis=f"{normalized_unit}_rounding")
    return _gate(PromotionGateResult.OFFICIAL_PROVIDER_CONFLICT.value, lane="conflict", conflict_type=ConflictType.OFFICIAL_PROVIDER_CONFLICT.value)


def can_promote_to_verified(
    metric_fact: Mapping[str, Any] | None = None,
    *,
    gate_result: str | Mapping[str, Any] | None = None,
    conflicts: Sequence[Mapping[str, Any]] | None = None,
    blocked_items: Sequence[Mapping[str, Any]] | None = None,
) -> bool:
    """Return whether a candidate may enter the verified lane."""

    result_value = _gate_result_value(gate_result)
    if result_value not in PROMOTABLE_GATE_RESULTS:
        return False
    if conflicts is None or blocked_items is None:
        return False
    if metric_fact is not None:
        try:
            validate_official_metric_fact(metric_fact)
        except OfficialVerificationValidationError:
            return False
        if metric_fact.get("extraction_quality") == ExtractionQuality.LOW.value:
            return False
        conflict_refs = set(metric_fact.get("conflict_refs") or ())
        resolved_refs = {
            str(conflict.get("conflict_id"))
            for conflict in conflicts
            if conflict.get("resolution_status") == ResolutionStatus.RESOLVED.value
        }
        if conflict_refs and not conflict_refs.issubset(resolved_refs):
            return False
    for conflict in conflicts:
        if conflict.get("resolution_status") != ResolutionStatus.RESOLVED.value:
            return False
    if blocked_items:
        return False
    return True


def validate_promotion_gate(
    metric_fact: Mapping[str, Any] | None = None,
    *,
    gate_result: str | Mapping[str, Any] | None = None,
    conflicts: Sequence[Mapping[str, Any]] | None = None,
    blocked_items: Sequence[Mapping[str, Any]] | None = None,
) -> None:
    """Raise unless a candidate can be promoted."""

    if not can_promote_to_verified(metric_fact, gate_result=gate_result, conflicts=conflicts, blocked_items=blocked_items):
        raise OfficialVerificationValidationError("candidate cannot be promoted to verified")


def build_conflict_record(
    *,
    conflict_id: str,
    stock_code: str,
    metric_id: str,
    period_key: str,
    provider_fact_ref: str,
    official_fact_ref: str,
    provider_value: Any,
    official_value: Any,
    normalized_unit: str,
    conflict_type: str,
    reviewer: str,
    severity: str = Severity.BLOCKER.value,
    resolution_status: str = ResolutionStatus.UNRESOLVED.value,
    review_note: str = "",
    preferred_value_candidate: Any = None,
    preferred_value_basis: str = "",
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    """Build and validate a provider-official conflict record."""

    record = {
        "schema_version": PROVIDER_OFFICIAL_CONFLICT_VERSION,
        "conflict_id": conflict_id,
        "stock_code": stock_code,
        "metric_id": metric_id,
        "period_key": period_key,
        "provider_fact_ref": provider_fact_ref,
        "official_fact_ref": official_fact_ref,
        "provider_value": provider_value,
        "official_value": official_value,
        "normalized_unit": normalized_unit,
        "conflict_type": conflict_type,
        "severity": severity,
        "resolution_status": resolution_status,
        "review_note": review_note,
        "preferred_value_candidate": preferred_value_candidate,
        "preferred_value_basis": preferred_value_basis,
        "created_at_utc": created_at_utc or _utc_now(),
        "reviewer": reviewer,
        "not_for_trading_advice": True,
    }
    validate_provider_official_conflict(record)
    return record


def build_blocked_until_review_item(
    *,
    blocked_item_id: str,
    stock_code: str,
    metric_id: str,
    period_key: str,
    blocked_reason: str,
    next_action: str,
    review_owner: str,
    missing_dependency: str = "",
    source_gap: str = "",
    extraction_quality: str = "",
    created_at_utc: str | None = None,
    resolved_at_utc: str = "",
    resolution_ref: str = "",
) -> dict[str, Any]:
    """Build and validate a blocked-until-review item."""

    item = {
        "schema_version": BLOCKED_UNTIL_REVIEW_ITEM_VERSION,
        "blocked_item_id": blocked_item_id,
        "stock_code": stock_code,
        "metric_id": metric_id,
        "period_key": period_key,
        "blocked_reason": blocked_reason,
        "missing_dependency": missing_dependency,
        "source_gap": source_gap,
        "extraction_quality": extraction_quality,
        "next_action": next_action,
        "review_owner": review_owner,
        "created_at_utc": created_at_utc or _utc_now(),
        "resolved_at_utc": resolved_at_utc,
        "resolution_ref": resolution_ref,
        "not_for_trading_advice": True,
    }
    validate_blocked_until_review_item(item)
    return item


def build_missing_prior_ar_anchor_block(metric_id: str, *, stock_code: str, period_key: str, review_owner: str) -> dict[str, Any]:
    """Build the canonical block item for missing prior-period AR anchor."""

    return build_blocked_until_review_item(
        blocked_item_id=f"blocked_{stock_code}_{period_key}_{metric_id}_prior_ar",
        stock_code=stock_code,
        metric_id=metric_id,
        period_key=period_key,
        blocked_reason="missing_prior_ar_anchor",
        missing_dependency="prior_period_accounts_receivable_anchor",
        source_gap="prior-period balance-sheet official anchor is missing",
        next_action="locate prior-period official balance sheet and verify AR anchor",
        review_owner=review_owner,
    )


def _gate(
    gate_result: str,
    *,
    lane: str,
    blocked_reason: str = "",
    conflict_type: str = "",
    tolerance_basis: str = "",
) -> dict[str, Any]:
    return {
        "gate_result": gate_result,
        "lane": lane,
        "can_promote": gate_result in PROMOTABLE_GATE_RESULTS,
        "blocked_reason": blocked_reason,
        "conflict_type": conflict_type,
        "tolerance_basis": tolerance_basis,
        "not_for_trading_advice": True,
    }


def _gate_result_value(gate_result: str | Mapping[str, Any] | None) -> str | None:
    if gate_result is None:
        return None
    if isinstance(gate_result, Mapping):
        return str(gate_result.get("gate_result") or "")
    return str(gate_result)


def _within_rounding_tolerance(provider_value: Any, official_value: Any, normalized_unit: str) -> bool:
    try:
        provider_number = float(provider_value)
        official_number = float(official_value)
    except (TypeError, ValueError):
        return False
    if not math.isfinite(provider_number) or not math.isfinite(official_number):
        return False
    diff = abs(provider_number - official_number)
    if normalized_unit == NormalizedUnit.CNY.value:
        base = max(abs(official_number), 1.0)
        return diff <= 1 or diff / base <= 0.0001
    if normalized_unit == NormalizedUnit.PERCENT_POINT.value:
        return diff <= 0.01
    if normalized_unit == NormalizedUnit.RATIO.value:
        return diff <= 0.0001
    if normalized_unit == NormalizedUnit.DAYS.value:
        return diff <= 0.1
    return False


def _has_non_finite_number(value: Any) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return not math.isfinite(number)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
