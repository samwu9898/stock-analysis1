# -*- coding: utf-8 -*-

import pytest

from src.fundamental_skill.data_verification.metric_lineage import (
    q1_is_not_annualized,
    required_dependencies_for,
    requires_stock_flow_caveat,
    validate_derived_metric_confidence,
    validate_metric_policy,
    validate_required_metric_dependencies,
    validate_verified_metric_lineage,
)
from src.fundamental_skill.data_verification.schemas import ExtractionQuality, MetricType, VerificationStatus
from src.fundamental_skill.data_verification.validators import OfficialVerificationValidationError


SHA = "c" * 64


def _fact(**overrides):
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
        "normalized_unit": "CNY",
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


def test_verified_direct_metric_requires_full_lineage():
    fact = _fact(table_title="")

    with pytest.raises(OfficialVerificationValidationError, match="table_title"):
        validate_verified_metric_lineage(fact)


def test_verified_derived_metric_requires_dependency_refs():
    fact = _fact(
        metric_id="gross_margin",
        metric_policy_id="gross_margin.v1",
        metric_type=MetricType.DERIVED.value,
        dependency_refs=[],
    )

    with pytest.raises(OfficialVerificationValidationError, match="dependency_refs"):
        validate_verified_metric_lineage(fact)


def test_missing_required_dependency_refs_rejected():
    with pytest.raises(OfficialVerificationValidationError, match="gross_margin"):
        validate_required_metric_dependencies("gross_margin", ["fact_revenue"])


def test_extraction_quality_low_blocked():
    fact = _fact(extraction_quality=ExtractionQuality.LOW.value)

    with pytest.raises(OfficialVerificationValidationError, match="low|verified"):
        validate_verified_metric_lineage(fact)


def test_all_official_files_require_sha256():
    fact = _fact(file_sha256="")

    with pytest.raises(OfficialVerificationValidationError, match="file_sha256"):
        validate_verified_metric_lineage(fact)


def test_metric_policy_constants_cover_required_derived_metrics():
    assert required_dependencies_for("gross_margin") == ("revenue", "operating_cost")
    assert "revenue" in required_dependencies_for("net_margin")
    assert "prior" not in required_dependencies_for("accounts_receivable_turnover_days")
    assert requires_stock_flow_caveat("contract_liabilities_to_revenue") is True
    assert q1_is_not_annualized("Q1") is True


def test_derived_metric_confidence_cannot_exceed_weakest_dependency():
    with pytest.raises(OfficialVerificationValidationError, match="confidence"):
        validate_derived_metric_confidence("high", ["high", "medium"])

    validate_derived_metric_confidence("medium", ["high", "medium"])


def test_gross_margin_without_anchor_caveat_rejected():
    with pytest.raises(OfficialVerificationValidationError, match="gross_margin"):
        validate_metric_policy("gross_margin", caveats=[])


def test_gross_margin_with_revenue_cost_anchor_caveat_accepted():
    validate_metric_policy("gross_margin", caveats=["revenue_cost_anchor_caveat"])


def test_gross_margin_with_cost_composition_caveat_accepted():
    validate_metric_policy("gross_margin", caveats=["cost_composition_caveat"])
