# -*- coding: utf-8 -*-

import copy

import pytest

from src.fundamental_skill.data_verification.conflict_gate import (
    build_blocked_until_review_item,
    build_conflict_record,
)
from src.fundamental_skill.data_verification.schemas import (
    BLOCKED_UNTIL_REVIEW_ITEM_VERSION,
    OFFICIAL_VERIFICATION_RUN_SUMMARY_VERSION,
    PROVIDER_OFFICIAL_CONFLICT_VERSION,
    ConflictType,
    ExtractionQuality,
    MetricType,
    NormalizedUnit,
    ResolutionStatus,
    VerificationStatus,
)
from src.fundamental_skill.data_verification.validators import (
    OfficialVerificationValidationError,
    validate_blocked_until_review_item,
    validate_official_metric_fact,
    validate_official_source_candidate,
    validate_official_verification_run_summary,
    validate_provider_official_conflict,
)


SHA = "a" * 64


def _source_candidate(**overrides):
    candidate = {
        "source_candidate_id": "src_600406_2024fy_ar",
        "stock_code": "600406",
        "period": "2024FY",
        "announcement_type": "annual_report",
        "candidate_source_type": "cninfo_official_pdf",
        "candidate_url": "https://example.invalid/600406_2024.pdf",
        "candidate_title": "600406 2024 annual report",
        "disclosure_date": "2025-04-30",
        "source_discovery_method": "manual_registry_entry",
        "is_official_candidate": True,
        "is_mirror": False,
        "accepted_as_official": True,
        "rejection_reason": "",
        "file_sha256": SHA,
        "local_cache_path": "local/official/600406_2024.pdf",
        "source_refresh_policy": "explicit_registry_refresh_only",
        "registry_version": "official_registry.v1",
        "not_for_trading_advice": True,
    }
    candidate.update(overrides)
    return candidate


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
        "source_ref": "src_600406_2024fy_ar",
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


def _run_summary(**overrides):
    summary = {
        "schema_version": OFFICIAL_VERIFICATION_RUN_SUMMARY_VERSION,
        "run_id": "run_600406_2024",
        "run_started_at_utc": "2026-05-31T00:00:00+00:00",
        "run_finished_at_utc": "2026-05-31T00:00:01+00:00",
        "stock_code": "600406",
        "source_registry_version": "official_registry.v1",
        "metric_count": 5,
        "verified_count": 2,
        "candidate_count": 1,
        "conflict_count": 1,
        "blocked_count": 1,
        "extraction_quality_summary": {"high": 4, "medium": 1, "low": 0},
        "unresolved_conflict_refs": ["conflict_1"],
        "blocked_item_refs": ["blocked_1"],
        "not_for_trading_advice": True,
    }
    summary.update(overrides)
    return summary


def test_valid_official_source_candidate_schema():
    validate_official_source_candidate(_source_candidate())


def test_valid_official_metric_fact_schema():
    validate_official_metric_fact(_metric_fact())


def test_valid_provider_official_conflict_schema():
    conflict = build_conflict_record(
        conflict_id="conflict_1",
        stock_code="600406",
        metric_id="gross_margin",
        period_key="2024FY",
        provider_fact_ref="provider_fact_1",
        official_fact_ref="official_fact_1",
        provider_value=25.0,
        official_value=24.0,
        normalized_unit="percent_point",
        conflict_type=ConflictType.OFFICIAL_PROVIDER_CONFLICT.value,
        reviewer="unit-test",
        created_at_utc="2026-05-31T00:00:00+00:00",
    )

    assert conflict["schema_version"] == PROVIDER_OFFICIAL_CONFLICT_VERSION
    validate_provider_official_conflict(conflict)


def test_valid_official_verification_run_summary_schema():
    validate_official_verification_run_summary(_run_summary())


def test_valid_blocked_until_review_item_schema():
    item = build_blocked_until_review_item(
        blocked_item_id="blocked_1",
        stock_code="600406",
        metric_id="accounts_receivable_turnover_days",
        period_key="2024FY",
        blocked_reason="missing_prior_ar_anchor",
        missing_dependency="prior_period_accounts_receivable_anchor",
        next_action="locate prior official balance sheet",
        review_owner="unit-test",
        created_at_utc="2026-05-31T00:00:00+00:00",
    )

    assert item["schema_version"] == BLOCKED_UNTIL_REVIEW_ITEM_VERSION
    validate_blocked_until_review_item(item)


def test_missing_not_for_trading_advice_rejected():
    fact = _metric_fact()
    fact.pop("not_for_trading_advice")

    with pytest.raises(OfficialVerificationValidationError, match="missing keys"):
        validate_official_metric_fact(fact)


def test_not_for_trading_advice_false_rejected():
    fact = _metric_fact(not_for_trading_advice=False)

    with pytest.raises(OfficialVerificationValidationError, match="not_for_trading_advice"):
        validate_official_metric_fact(fact)


def test_nested_not_for_trading_advice_false_rejected():
    fact = _metric_fact(caveats=[{"note": "nested", "not_for_trading_advice": False}])

    with pytest.raises(OfficialVerificationValidationError, match="not_for_trading_advice"):
        validate_official_metric_fact(fact)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("raw_value", None),
        ("raw_unit", ""),
        ("raw_unit", "   "),
        ("normalized_value", None),
        ("normalized_unit", ""),
        ("normalized_unit", "   "),
    ],
)
def test_official_metric_fact_rejects_missing_raw_or_normalized_values(field, value):
    fact = _metric_fact(**{field: value})

    with pytest.raises(OfficialVerificationValidationError, match=field):
        validate_official_metric_fact(fact)


@pytest.mark.parametrize("field", ["row_label", "column_label", "verifier"])
def test_official_metric_fact_rejects_empty_critical_scalar_fields(field):
    fact = _metric_fact(**{field: ""})

    with pytest.raises(OfficialVerificationValidationError, match=field):
        validate_official_metric_fact(fact)


def test_verified_medium_extraction_quality_requires_reviewer():
    fact = _metric_fact(extraction_quality=ExtractionQuality.MEDIUM.value, official_confidence="medium", reviewer="")

    with pytest.raises(OfficialVerificationValidationError, match="reviewer"):
        validate_official_metric_fact(fact)


def test_verified_medium_extraction_quality_accepts_reviewer_present():
    fact = _metric_fact(
        extraction_quality=ExtractionQuality.MEDIUM.value,
        official_confidence="medium",
        reviewer="prototype_review_required",
    )

    validate_official_metric_fact(fact)


def test_unresolved_conflict_record_blocks_promotion_semantics():
    conflict = build_conflict_record(
        conflict_id="conflict_unresolved",
        stock_code="600406",
        metric_id="gross_margin",
        period_key="2024FY",
        provider_fact_ref="provider_fact_1",
        official_fact_ref="official_fact_1",
        provider_value=25.0,
        official_value=24.0,
        normalized_unit="percent_point",
        conflict_type=ConflictType.OFFICIAL_PROVIDER_CONFLICT.value,
        reviewer="unit-test",
        resolution_status=ResolutionStatus.UNRESOLVED.value,
        created_at_utc="2026-05-31T00:00:00+00:00",
    )

    copied = copy.deepcopy(conflict)
    validate_provider_official_conflict(copied)
    assert copied == conflict
