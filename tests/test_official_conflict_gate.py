# -*- coding: utf-8 -*-

import math

import pytest

from src.fundamental_skill.data_verification.conflict_gate import (
    build_conflict_record,
    build_missing_prior_ar_anchor_block,
    can_promote_to_verified,
    classify_provider_official_match,
    validate_promotion_gate,
)
from src.fundamental_skill.data_verification.schemas import (
    ConflictType,
    ExtractionQuality,
    MetricType,
    NormalizedUnit,
    ResolutionStatus,
    VerificationStatus,
)
from src.fundamental_skill.data_verification.validators import OfficialVerificationValidationError


SHA = "e" * 64


def _metric_fact(**overrides):
    fact = {
        "fact_id": "fact_600406_2024_revenue",
        "stock_code": "600406",
        "company_name": "Guodian NARI",
        "metric_id": "revenue",
        "metric_policy_id": "revenue.v1",
        "metric_type": MetricType.DIRECT.value,
        "period_key": "2024FY",
        "period_end_date": "2024-12-31",
        "period_type": "FY",
        "statement_scope": "consolidated",
        "announcement_title": "600406 2024 annual report",
        "announcement_type": "annual_report",
        "disclosure_date": "2025-04-30",
        "source_ref": "src_600406_2024fy",
        "file_sha256": SHA,
        "page_or_anchor": "p42",
        "table_title": "Consolidated income statement",
        "row_label": "Operating revenue",
        "column_label": "2024",
        "raw_value": 100.0,
        "raw_unit": "CNY",
        "normalized_value": 100.0,
        "normalized_unit": NormalizedUnit.CNY.value,
        "dependency_refs": [],
        "extraction_method": "manual_table_anchor",
        "extraction_quality": ExtractionQuality.HIGH.value,
        "verification_status": VerificationStatus.VERIFIED.value,
        "official_confidence": "high",
        "conflict_refs": [],
        "caveats": [],
        "verifier": "unit-test",
        "reviewer": "",
        "not_for_trading_advice": True,
    }
    fact.update(overrides)
    return fact


def test_exact_match_promotes():
    gate = classify_provider_official_match(
        provider_value=100,
        official_value=100,
        normalized_unit=NormalizedUnit.CNY.value,
    )

    assert gate["gate_result"] == "exact_match"
    assert can_promote_to_verified(gate_result=gate, conflicts=[], blocked_items=[]) is True


def test_rounding_tolerance_promotes():
    gate = classify_provider_official_match(
        provider_value=25.104,
        official_value=25.10,
        normalized_unit=NormalizedUnit.PERCENT_POINT.value,
    )

    assert gate["gate_result"] == "rounding_tolerance"
    validate_promotion_gate(gate_result=gate, conflicts=[], blocked_items=[])


def test_unit_mismatch_blocked():
    gate = classify_provider_official_match(
        provider_value=1,
        official_value=1,
        normalized_unit=NormalizedUnit.CNY.value,
        provider_normalized_unit="ratio",
        official_normalized_unit="CNY",
    )

    assert gate["gate_result"] == "unit_mismatch"
    assert can_promote_to_verified(gate_result=gate, conflicts=[], blocked_items=[]) is False


def test_period_mismatch_blocked():
    gate = classify_provider_official_match(
        provider_value=1,
        official_value=1,
        normalized_unit=NormalizedUnit.CNY.value,
        provider_period_key="2024FY",
        official_period_key="2025FY",
    )

    assert gate["gate_result"] == "period_mismatch"
    assert gate["lane"] == "blocked"


def test_raw_field_mismatch_blocked():
    gate = classify_provider_official_match(
        provider_value=1,
        official_value=1,
        normalized_unit=NormalizedUnit.CNY.value,
        provider_raw_field="provider.gross_margin",
        official_raw_field="official.net_margin",
    )

    assert gate["gate_result"] == "raw_field_mismatch"
    assert gate["lane"] == "blocked"


def test_adjusted_before_after_mismatch_conflict():
    gate = classify_provider_official_match(
        provider_value=1,
        official_value=1,
        normalized_unit=NormalizedUnit.CNY.value,
        adjusted_basis_match=False,
    )

    assert gate["gate_result"] == "adjusted_before_after_mismatch"
    assert gate["lane"] == "conflict"
    assert gate["conflict_type"] == ConflictType.ADJUSTED_BASIS_MISMATCH.value


def test_numerator_policy_conflict():
    gate = classify_provider_official_match(
        provider_value=1,
        official_value=1,
        normalized_unit=NormalizedUnit.RATIO.value,
        numerator_policy_match=False,
    )

    assert gate["gate_result"] == "numerator_policy_conflict"
    assert gate["lane"] == "conflict"


def test_official_provider_conflict_unresolved_cannot_promote():
    conflict = build_conflict_record(
        conflict_id="conflict_1",
        stock_code="600406",
        metric_id="gross_margin",
        period_key="2024FY",
        provider_fact_ref="provider_fact",
        official_fact_ref="official_fact",
        provider_value=25.0,
        official_value=24.0,
        normalized_unit="percent_point",
        conflict_type=ConflictType.OFFICIAL_PROVIDER_CONFLICT.value,
        reviewer="unit-test",
        created_at_utc="2026-05-31T00:00:00+00:00",
    )

    assert can_promote_to_verified(gate_result="exact_match", conflicts=[conflict], blocked_items=[]) is False
    with pytest.raises(OfficialVerificationValidationError, match="cannot"):
        validate_promotion_gate(gate_result="exact_match", conflicts=[conflict], blocked_items=[])


def test_provider_provider_conflict_cannot_promote():
    gate = classify_provider_official_match(
        provider_value=1,
        official_value=1,
        normalized_unit=NormalizedUnit.CNY.value,
        provider_provider_conflict=True,
    )

    assert gate["gate_result"] == "provider_provider_conflict"
    assert can_promote_to_verified(gate_result=gate, conflicts=[], blocked_items=[]) is False


def test_missing_prior_ar_anchor_blocked():
    item = build_missing_prior_ar_anchor_block(
        "accounts_receivable_turnover_days",
        stock_code="600406",
        period_key="2024FY",
        review_owner="unit-test",
    )

    assert item["blocked_reason"] == "missing_prior_ar_anchor"
    assert can_promote_to_verified(gate_result="exact_match", conflicts=[], blocked_items=[item]) is False


def test_gate_result_none_cannot_promote():
    assert can_promote_to_verified(gate_result=None, conflicts=[], blocked_items=[]) is False


def test_conflicts_none_cannot_promote():
    assert can_promote_to_verified(gate_result="exact_match", conflicts=None, blocked_items=[]) is False


def test_blocked_items_none_cannot_promote():
    assert can_promote_to_verified(gate_result="exact_match", conflicts=[], blocked_items=None) is False


def test_conflict_refs_without_resolved_conflict_records_cannot_promote():
    fact = _metric_fact(verification_status=VerificationStatus.CANDIDATE.value, conflict_refs=["conflict_1"])

    assert can_promote_to_verified(
        metric_fact=fact,
        gate_result="exact_match",
        conflicts=[],
        blocked_items=[],
    ) is False


def test_conflict_refs_with_resolved_conflict_records_can_promote():
    fact = _metric_fact(verification_status=VerificationStatus.CANDIDATE.value, conflict_refs=["conflict_1"])
    conflict = build_conflict_record(
        conflict_id="conflict_1",
        stock_code="600406",
        metric_id="revenue",
        period_key="2024FY",
        provider_fact_ref="provider_fact",
        official_fact_ref="official_fact",
        provider_value=100.0,
        official_value=100.0,
        normalized_unit="CNY",
        conflict_type=ConflictType.EXACT_MATCH.value,
        reviewer="unit-test",
        resolution_status=ResolutionStatus.RESOLVED.value,
        created_at_utc="2026-05-31T00:00:00+00:00",
    )

    assert can_promote_to_verified(
        metric_fact=fact,
        gate_result="exact_match",
        conflicts=[conflict],
        blocked_items=[],
    ) is True


def test_nan_value_cannot_promote():
    gate = classify_provider_official_match(
        provider_value=math.nan,
        official_value=math.nan,
        normalized_unit=NormalizedUnit.CNY.value,
    )

    assert gate["can_promote"] is False
    assert can_promote_to_verified(gate_result=gate, conflicts=[], blocked_items=[]) is False


def test_infinite_value_cannot_promote():
    gate = classify_provider_official_match(
        provider_value=100,
        official_value=math.inf,
        normalized_unit=NormalizedUnit.CNY.value,
    )

    assert gate["can_promote"] is False
    assert can_promote_to_verified(gate_result=gate, conflicts=[], blocked_items=[]) is False


def test_nonnumeric_value_does_not_crash_or_promote():
    gate = classify_provider_official_match(
        provider_value="not-a-number",
        official_value=100,
        normalized_unit=NormalizedUnit.CNY.value,
    )

    assert gate["gate_result"] == "official_provider_conflict"
    assert can_promote_to_verified(gate_result=gate, conflicts=[], blocked_items=[]) is False
