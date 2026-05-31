# -*- coding: utf-8 -*-
"""Metric lineage and policy validation helpers."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .schemas import (
    DEFERRED_METRIC_IDS,
    DERIVED_METRIC_DEPENDENCIES,
    PROXY_METRIC_IDS,
    Q1_NOT_ANNUALIZED_PERIOD_TYPES,
    STOCK_FLOW_RATIO_METRICS,
    ExtractionQuality,
    OfficialConfidence,
    VerificationStatus,
)
from .validators import OfficialVerificationValidationError, validate_official_metric_fact


CONFIDENCE_ORDER = {
    OfficialConfidence.LOW.value: 1,
    OfficialConfidence.MEDIUM.value: 2,
    OfficialConfidence.HIGH.value: 3,
}


def required_dependencies_for(metric_id: str) -> tuple[str, ...]:
    return DERIVED_METRIC_DEPENDENCIES.get(metric_id, ())


def is_derived_metric(metric_id: str) -> bool:
    return metric_id in DERIVED_METRIC_DEPENDENCIES


def is_proxy_metric(metric_id: str) -> bool:
    return metric_id in PROXY_METRIC_IDS


def is_deferred_metric(metric_id: str) -> bool:
    return metric_id in DEFERRED_METRIC_IDS


def requires_stock_flow_caveat(metric_id: str) -> bool:
    return metric_id in STOCK_FLOW_RATIO_METRICS


def q1_is_not_annualized(period_type: str, annualization_policy: str | None = None) -> bool:
    if period_type not in Q1_NOT_ANNUALIZED_PERIOD_TYPES:
        return False
    return annualization_policy in (None, "", "not_annualized")


def validate_verified_metric_lineage(fact: Mapping[str, Any]) -> None:
    """Validate verified metric lineage, dependency refs, sha256, and quality."""

    validate_official_metric_fact(fact)
    if fact.get("verification_status") != VerificationStatus.VERIFIED.value:
        return
    if fact.get("extraction_quality") == ExtractionQuality.LOW.value:
        raise OfficialVerificationValidationError("low quality extraction must be blocked")
    if is_derived_metric(str(fact.get("metric_id"))) and not fact.get("dependency_refs"):
        raise OfficialVerificationValidationError("verified derived metric requires dependency_refs")


def validate_required_metric_dependencies(metric_id: str, dependency_refs: Iterable[str]) -> None:
    """Require derived metrics to carry dependency refs for their policy."""

    refs = tuple(ref for ref in dependency_refs if ref)
    required = required_dependencies_for(metric_id)
    if required and len(refs) < len(required):
        raise OfficialVerificationValidationError(f"{metric_id} requires dependency_refs for: {required}")


def validate_derived_metric_confidence(metric_confidence: str, dependency_confidences: Iterable[str]) -> None:
    """Ensure derived metric confidence is not higher than its weakest input."""

    dependency_values = list(dependency_confidences)
    if not dependency_values:
        raise OfficialVerificationValidationError("derived metric requires dependency confidences")
    if metric_confidence not in CONFIDENCE_ORDER:
        raise OfficialVerificationValidationError("metric confidence is unsupported")
    weakest = min(CONFIDENCE_ORDER.get(value, 0) for value in dependency_values)
    if weakest <= 0:
        raise OfficialVerificationValidationError("dependency confidence is unsupported")
    if CONFIDENCE_ORDER[metric_confidence] > weakest:
        raise OfficialVerificationValidationError("derived metric confidence cannot exceed weakest dependency")


def validate_metric_policy(metric_id: str, *, numerator_policy: str = "", denominator_policy: str = "", caveats: Iterable[str] = ()) -> None:
    """Validate minimal metric-specific policy declarations."""

    caveat_values = set(caveats)
    if metric_id == "gross_margin" and not (
        {"revenue_cost_anchor_caveat", "cost_composition_caveat"} & caveat_values
    ):
        raise OfficialVerificationValidationError("gross_margin requires revenue/cost anchor caveat")
    if metric_id == "net_margin" and (not numerator_policy or not denominator_policy):
        raise OfficialVerificationValidationError("net_margin requires numerator and denominator policy")
    if metric_id == "operating_cash_flow_to_net_profit" and not numerator_policy:
        raise OfficialVerificationValidationError("operating_cash_flow_to_net_profit requires net profit numerator policy")
    if metric_id == "accounts_receivable_turnover_days" and "prior_period_ar_anchor" not in caveat_values:
        raise OfficialVerificationValidationError("accounts_receivable_turnover_days requires prior-period AR anchor policy")
    if metric_id in PROXY_METRIC_IDS and "contract_liabilities_proxy_caveat" not in caveat_values:
        raise OfficialVerificationValidationError("contract liabilities proxy caveat is required")
    if metric_id in DEFERRED_METRIC_IDS:
        raise OfficialVerificationValidationError("segment/business composition is deferred from production v1")
