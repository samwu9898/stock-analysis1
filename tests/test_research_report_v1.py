# -*- coding: utf-8 -*-

import copy
import inspect
import json
from pathlib import Path

import pytest

from src.fundamental_skill.research_report.research_report_v1 import (
    ALLOWED_EVIDENCE_LABELS,
    REPORT_TYPE,
    ResearchReportArtifactBoundaryError,
    ResearchReportSecretError,
    build_research_report_v1,
    write_research_report_v1,
)
import src.fundamental_skill.research_report.research_report_v1 as report_module


GROUND_TRUTH_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "ground_truth"
    / "fundamental_ground_truth_v1.json"
)

TOP_LEVEL_SECTIONS = {
    "data_quality_assessment",
    "executive_summary",
    "macro_context",
    "industry_context",
    "company_fundamentals",
    "opportunity_analysis",
    "risk_analysis",
    "evidence_gaps",
    "rebuttal_conditions",
    "follow_up_variables",
    "source_artifact_refs",
}

FORBIDDEN_ADVICE_FIELDS = {
    "buy",
    "sell",
    "hold",
    "target_price",
    "position",
    "portfolio_weight",
    "technical_signal",
    "trading_recommendation",
    "investment_recommendation",
}


def _candidate(
    field_path: str,
    *,
    value=1.0,
    provider: str = "tushare",
    report_period: str | None = "2026-03-31",
    as_of_date: str | None = None,
    canonical_unit: str = "RMB yuan",
    review_status: str = "auto_accepted",
    missing_category=None,
):
    return {
        "field_path": field_path,
        "value": value,
        "source_provider": provider,
        "source_artifact": f"{provider}_raw.json",
        "source_block": field_path.split(".")[0],
        "source_endpoint": "fake_endpoint",
        "source_trace": {"artifact_file": f"{provider}_raw.json", "provider": provider},
        "report_period": report_period,
        "ann_date": None,
        "disclosure_date": None,
        "as_of_date": as_of_date,
        "data_unit": canonical_unit,
        "canonical_unit": canonical_unit,
        "derived": False,
        "derivation_method": None,
        "confidence": "high" if review_status == "auto_accepted" else "low",
        "review_status": review_status,
        "missing_category": missing_category,
        "conflict_status": "within_tolerance",
        "manual_review_note": "",
    }


def _auto_core(field_path: str, value, *, as_of_date=None, canonical_unit="RMB yuan"):
    return {
        "field_path": field_path,
        "value": value,
        "report_period": None if as_of_date else "2026-03-31",
        "as_of_date": as_of_date,
        "source_provider": "tushare",
        "canonical_unit": canonical_unit,
        "confidence": "high",
        "reason": "Core field passed V1 auto-acceptance checks.",
    }


def _queue(field_path: str, issue_type: str, priority: int = 2):
    return {
        "field_path": field_path,
        "issue_type": issue_type,
        "priority": priority,
        "candidate_count": 3,
        "reason": f"{field_path} requires review.",
        "representative_candidates": [],
    }


def _decision(field_path: str, queue_item_type: str, outcome: str, follow_up_type: str = "manual_review_later"):
    return {
        "decision_id": f"600406-{field_path}",
        "field_path": field_path,
        "queue_item_type": queue_item_type,
        "source_queue_priority": "B",
        "related_candidate_ids": [],
        "representative_candidates": [],
        "review_action": "review",
        "metadata_checked": ["source_provider", "source_trace"],
        "decision_outcome": outcome,
        "decision_reason": "Review decision is not fixture promotion.",
        "follow_up_type": follow_up_type,
        "follow_up_detail": "Keep review-facing only.",
        "eligible_for_future_promotion": outcome == "confirmed_for_future_promotion",
        "fixture_write_allowed": False,
        "reviewed_by": "unit_test",
        "reviewed_at": "2026-05-27T12:30:00+00:00",
        "confidence_after_review": "medium" if outcome == "confirmed_for_future_promotion" else "low",
        "not_for_trading_advice": True,
    }


def _fake_inputs():
    candidates = [
        _candidate("financial_metrics.revenue", value=9_564_242_921.53),
        _candidate("financial_metrics.net_profit", value=721_291_973.43),
        _candidate("financial_metrics.gross_margin", value=25.0953, canonical_unit="percentage_point"),
        _candidate("financial_metrics.roe", value=1.3591, canonical_unit="percentage_point"),
        _candidate("financial_metrics.operating_cashflow", value=-1_514_283_397.01),
        _candidate("financial_metrics.accounts_receivable", value=26_652_280_492.48),
        _candidate("financial_metrics.inventory", value=16_590_949_099.58),
        _candidate("financial_metrics.contract_liabilities", value=8_634_661_875.03),
        _candidate("financial_metrics.capex", value=451_693_205.88),
        _candidate("valuation_metrics.pe_ttm", value=24.597, report_period=None, as_of_date="2026-05-26", canonical_unit="multiple"),
        _candidate("valuation_metrics.pb", value=3.8257, report_period=None, as_of_date="2026-05-26", canonical_unit="multiple"),
        _candidate("valuation_metrics.market_cap", value=204_649_146_855.0, report_period=None, as_of_date="2026-05-26"),
        _candidate(
            "basic_info.main_business",
            value="AkShare-only text",
            report_period=None,
            canonical_unit="text",
            review_status="manual_review_required",
            missing_category="manual_review_required",
        ),
        _candidate(
            "business_composition[0].revenue_ratio",
            value=50.0,
            canonical_unit="percentage_point",
            review_status="manual_review_required",
            missing_category="manual_review_required",
        ),
    ]
    auto_core = [
        _auto_core("financial_metrics.revenue", 9_564_242_921.53),
        _auto_core("financial_metrics.net_profit", 721_291_973.43),
        _auto_core("financial_metrics.gross_margin", 25.0953, canonical_unit="percentage_point"),
        _auto_core("financial_metrics.roe", 1.3591, canonical_unit="percentage_point"),
        _auto_core("financial_metrics.operating_cashflow", -1_514_283_397.01),
        _auto_core("valuation_metrics.pe_ttm", 24.597, as_of_date="2026-05-26", canonical_unit="multiple"),
        _auto_core("valuation_metrics.pb", 3.8257, as_of_date="2026-05-26", canonical_unit="multiple"),
        _auto_core("valuation_metrics.market_cap", 204_649_146_855.0, as_of_date="2026-05-26"),
    ]
    fact_candidates = {
        "code": "600406",
        "auto_accepted_core_fields": auto_core,
        "manual_review_priority_queue": [
            _queue("valuation_metrics.as_of_date", "valuation_as_of_date_review_required", priority=1),
            _queue("business_composition.period", "business_composition_period_review_required"),
            _queue("business_composition.classification_type", "business_composition_field_review"),
            _queue("business_composition.revenue_ratio", "business_composition_field_review"),
            _queue("basic_info.main_business", "main_business_review"),
        ],
        "business_composition_summary": {
            "candidate_count": 20,
            "providers_present": ["akshare", "tushare"],
            "periods_observed": ["2025-12-31"],
            "classification_type_coverage": {"available_count": 1, "candidate_count": 10, "coverage_ratio": 0.1},
            "revenue_ratio_coverage": {"available_count": 1, "candidate_count": 10, "coverage_ratio": 0.1},
            "gross_margin_coverage": {"available_count": 8, "candidate_count": 10, "coverage_ratio": 0.8},
            "mapping_missing_count": 4,
            "period_mismatch_count": 2,
            "provider_missing_count": 3,
            "recommended_next_action": "Do not auto-accept mixed group rows.",
        },
        "candidates": candidates,
    }
    review_decisions = {
        "version": "candidate_review_decisions.v1",
        "code": "600406",
        "decisions": [
            _decision(
                "valuation_metrics.as_of_date",
                "valuation_as_of_date_review_required",
                "confirmed_for_future_promotion",
                follow_up_type="none",
            ),
            _decision("business_composition.period", "business_composition_period_review_required", "keep_manual_review_required"),
            _decision("business_composition.classification_type", "classification_type_missing", "requires_official_parser"),
            _decision("business_composition.revenue_ratio", "ratio_denominator_unclear", "keep_manual_review_required"),
            _decision("basic_info.main_business", "main_business_review_required", "requires_official_parser", "official_parser_needed"),
        ],
        "summary": {"fixture_write_allowed_count": 0, "eligible_for_future_promotion_count": 1},
    }
    score_explainability = {
        "code": "600406",
        "providers": {
            "akshare": {"artifact_refs": {"fundamental": "akshare_fundamental.json", "evidence_pack": "akshare_evidence_pack.json"}},
            "tushare": {"artifact_refs": {"fundamental": "tushare_fundamental.json", "evidence_pack": "tushare_evidence_pack.json"}},
        },
        "score_summary": {"akshare_score": 65, "tushare_score": 62, "score_delta": -3.0, "score_drift_reason": "mapping_gap"},
        "confidence_summary": {"akshare_confidence": "high", "tushare_confidence": "high", "confidence_delta": "no_confidence_drift"},
        "provider_caveats": [
            {
                "code": "mapping_gap",
                "field": "basic_info.main_business",
                "note": "Largest segment hint must not become canonical main_business.",
            }
        ],
        "derived_hints": [
            {
                "field": "business_composition.max_segment",
                "value": "Grid equipment manufacturing",
                "derived": True,
                "not_for_scoring": True,
                "reason": "Reviewer hint only.",
            }
        ],
        "narrative_hints": [
            {
                "code": "business_quality_main_business_gap",
                "message": "Business quality can still be lower when main_business and usable revenue_ratio evidence are missing.",
                "not_for_scoring": True,
            }
        ],
    }
    diff_report = {
        "code": "600406",
        "summary": {"category_counts": {"score_drift": 2}, "blocker_count": 2, "review_required_count": 2},
        "automatic_acceptance": False,
    }
    fundamental_payloads = {
        "akshare": {"stock_code": "600406", "stock_name": "NARI", "strategy_type": "stable_growth", "status": "neutral", "confidence": "high", "fundamental_score": 65},
        "tushare": {"stock_code": "600406", "stock_name": "NARI", "strategy_type": "stable_growth", "status": "neutral", "confidence": "high", "fundamental_score": 62},
    }
    evidence_pack_payloads = {
        "akshare": {
            "stock": {"code": "600406", "name": "NARI", "strategy_type": "stable_growth"},
            "financial_metrics": {"period": "20260331", "revenue": 9_564_242_921.53},
            "valuation_metrics": {"period": "2026-05-26", "pe_ttm": 24.597, "pb": 3.8257, "market_cap": 204_649_146_855.0},
            "business_composition": [
                {
                    "period": "2025-12-31",
                    "classification_type": "by_product",
                    "segment_name": "Grid automation",
                    "revenue": 33_422_155_368.42,
                    "revenue_ratio": {"raw_value": 50.46, "display_value": "50.46%"},
                    "gross_margin": {"raw_value": 30.12, "display_value": "30.12%"},
                }
            ],
        },
        "tushare": {"stock": {"code": "600406", "name": "NARI", "strategy_type": "stable_growth"}},
    }
    return {
        "code": "600406",
        "fundamental_payloads": fundamental_payloads,
        "evidence_pack_payloads": evidence_pack_payloads,
        "fact_candidates": fact_candidates,
        "review_decisions": review_decisions,
        "score_explainability": score_explainability,
        "diff_report": diff_report,
        "generated_at": "2026-05-27T12:00:00+00:00",
    }


def _build_report():
    return build_research_report_v1(**_fake_inputs())


def _walk_dicts(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_dicts(child)


def _walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _assert_secret_not_rendered(secret: str, text: str) -> None:
    if secret in text:
        raise AssertionError("secret-like value was rendered")


def test_build_report_from_fake_artifacts_has_top_level_schema_and_sections():
    report = _build_report()

    assert report["code"] == "600406"
    assert report["generated_at"] == "2026-05-27T12:00:00+00:00"
    assert report["report_type"] == REPORT_TYPE
    assert report["not_for_trading_advice"] is True
    assert TOP_LEVEL_SECTIONS <= set(report)
    assert report["source_artifact_refs"]["fundamental"] == ["akshare_fundamental.json", "tushare_fundamental.json"]
    assert report["source_artifact_refs"]["evidence_pack"] == ["akshare_evidence_pack.json", "tushare_evidence_pack.json"]


def test_every_key_judgement_has_allowed_evidence_label_and_no_verified_fact_without_fixture():
    report = _build_report()

    for item in _walk_dicts(report):
        if any(key in item for key in ("analysis", "condition", "variable", "field_path")):
            assert item.get("evidence_label") in ALLOWED_EVIDENCE_LABELS
        assert item.get("evidence_label") != "verified_fact"


def test_candidates_are_auto_accepted_candidates_not_verified_facts():
    report = _build_report()
    fields = report["data_quality_assessment"]["auto_accepted_core_fields"]
    revenue = next(item for item in fields if item["field_path"] == "financial_metrics.revenue")
    valuation = report["data_quality_assessment"]["valuation_as_of_date_status"]

    assert revenue["evidence_label"] == "auto_accepted_candidate"
    assert valuation["evidence_label"] == "auto_accepted_candidate"
    assert "verified_fact" not in json.dumps(report, ensure_ascii=False)


def test_review_decisions_are_not_treated_as_fixture_promotion():
    report = _build_report()
    decisions = report["data_quality_assessment"]["candidate_review_decisions"]
    valuation = next(item for item in decisions if item["field_path"] == "valuation_metrics.as_of_date")

    assert valuation["decision_outcome"] == "confirmed_for_future_promotion"
    assert valuation["evidence_label"] == "manual_review_required"
    assert valuation["fixture_write_allowed"] is False
    assert "not verified fact" in valuation["caveat"]


def test_data_quality_caveats_appear_and_limit_conclusion_strength():
    report = _build_report()
    quality = report["data_quality_assessment"]

    assert quality["main_business_status"]["status"] == "official_source_gap"
    assert "AkShare-only text" in quality["main_business_status"]["caveat"]
    assert quality["business_composition_status"]["period_status"]["evidence_label"] == "manual_review_required"
    assert quality["business_composition_status"]["classification_type_status"]["evidence_label"] == "manual_review_required"
    assert quality["business_composition_status"]["revenue_ratio_status"]["evidence_label"] == "manual_review_required"
    assert quality["score_confidence_explainability_status"]["score_summary"]["score_delta"] == -3.0
    assert quality["diff_report_status"]["blocker_count"] == 2
    assert any("limit conclusion strength" in item["analysis"] for item in quality["impact_on_research_conclusion"])


def test_600406_stable_growth_grid_equipment_behavior_is_specific_and_caveated():
    report = _build_report()
    text = json.dumps(report, ensure_ascii=False).lower()

    assert "stable_growth" in text
    assert "grid-equipment" in text
    assert "state grid" in text
    assert "china southern power grid" in text
    assert "uhv" in text
    assert "distribution-grid" in text
    assert "digital-grid" in text
    assert "power automation" in text
    assert "relay protection" in text
    assert "dispatching" in text
    assert "information communication" in text
    assert "industry prosperity is not company realization" in text
    assert "largest segment hint must not become canonical main_business" in text


def test_company_fundamentals_cover_required_fields_and_trust_boundary():
    report = _build_report()
    company = report["company_fundamentals"]
    financial_fields = {item["field_path"] for item in company["financial_metrics"]}
    valuation_fields = {item["field_path"] for item in company["valuation_metrics"]}

    for field in (
        "revenue",
        "net_profit",
        "gross_margin",
        "roe",
        "operating_cashflow",
        "accounts_receivable",
        "inventory",
        "contract_liabilities",
        "capex",
    ):
        assert f"financial_metrics.{field}" in financial_fields
    for field in ("pe_ttm", "pb", "market_cap"):
        assert f"valuation_metrics.{field}" in valuation_fields
    assert company["business_composition"]["available_segments_preview"][0]["evidence_label"] == "manual_review_required"
    assert any(item["title"] == "financial_metrics.revenue" for item in company["trusted_fields"])
    assert any(item["title"] == "basic_info.main_business" for item in company["fields_needing_review"])


def test_opportunity_risk_gap_bear_case_and_follow_up_sections_are_structured():
    report = _build_report()

    assert {item["title"] for item in report["opportunity_analysis"]} >= {
        "grid_investment_cycle",
        "digital_grid",
        "uhv_and_distribution_grid",
        "power_automation_and_relay_protection",
        "stable_operating_quality_candidate",
    }
    assert {item["title"] for item in report["risk_analysis"]} >= {
        "tender_cadence_risk",
        "order_realization_risk",
        "receivables_and_cashflow_risk",
        "gross_margin_pressure",
        "contract_liabilities_visibility_risk",
        "business_composition_scope_risk",
        "valuation_date_risk",
        "data_quality_risk",
    }
    assert {item["field_path"] for item in report["evidence_gaps"]} >= {
        "valuation_metrics.as_of_date",
        "business_composition.period",
        "business_composition.classification_type",
        "business_composition.revenue_ratio",
        "basic_info.main_business",
        "score_confidence_explainability.score_drift",
    }
    assert {item["title"] for item in report["rebuttal_conditions"]} >= {
        "revenue_growth_slowdown",
        "operating_cashflow_deterioration",
        "receivables_grow_faster_than_revenue",
        "contract_liabilities_decline",
        "gross_margin_compression",
        "grid_tender_rhythm_weakens",
        "business_composition_does_not_support_exposure",
        "valuation_date_stale_or_mismatched",
    }
    assert {item["variable"] for item in report["follow_up_variables"]} >= {
        "grid_investment_amount",
        "state_grid_and_csg_tenders",
        "uhv_distribution_grid_project_cadence",
        "digital_grid_policy_and_tender_conversion",
        "accounts_receivable_turnover",
        "operating_cashflow",
        "contract_liabilities",
        "gross_margin",
        "business_composition",
        "valuation_as_of_date",
        "pe_pb_market_cap_same_date_refresh",
    }


def test_report_has_no_investment_advice_or_technical_signal_fields():
    report = _build_report()
    keys = {key.lower() for key in _walk_keys(report)}

    assert not (FORBIDDEN_ADVICE_FIELDS & keys)
    assert report["not_for_trading_advice"] is True


def test_p1_proxy_and_industry_narrative_are_not_written_as_operating_facts():
    report = _build_report()
    text = json.dumps(report, ensure_ascii=False).lower()

    assert "p1 proxy proves" not in text
    assert "proxy operating fact" not in text
    assert "automatic revenue evidence" in text
    digital_grid = next(item for item in report["opportunity_analysis"] if item["title"] == "digital_grid")
    assert digital_grid["evidence_label"] == "unsupported_assumption"


def test_writer_writes_only_report_json_under_tmpdir_and_not_fixture(tmp_path):
    before = GROUND_TRUTH_FIXTURE.read_text(encoding="utf-8")
    report = _build_report()
    output_root = tmp_path / "research_reports"

    path = write_research_report_v1(report, output_root, "20260527T120000")

    assert path == output_root / "20260527T120000" / "600406" / "fundamental_research_report_v1.json"
    assert json.loads(path.read_text(encoding="utf-8"))["report_type"] == REPORT_TYPE
    assert [item for item in output_root.rglob("*") if item.is_file()] == [path]
    assert GROUND_TRUTH_FIXTURE.read_text(encoding="utf-8") == before


def test_writer_rejects_path_traversal(tmp_path):
    report = _build_report()

    with pytest.raises(ResearchReportArtifactBoundaryError):
        write_research_report_v1(report, tmp_path / "research_reports", "..\\escape")

    bad_report = copy.deepcopy(report)
    bad_report["code"] = "..\\escape"
    with pytest.raises(ResearchReportArtifactBoundaryError):
        write_research_report_v1(bad_report, tmp_path / "research_reports", "20260527T120000")


def test_writer_secret_scan_blocks_bearer_mcp_and_dotenv_without_leaking_value(tmp_path):
    report = _build_report()
    secret = "Bearer A9abcdefABCDEF1234567890abcdefABCDEF1234567890z"
    bad_report = copy.deepcopy(report)
    bad_report["risk_analysis"][0]["analysis"] = secret

    with pytest.raises(ResearchReportSecretError) as exc_info:
        write_research_report_v1(bad_report, tmp_path / "research_reports", "20260527T120000")
    _assert_secret_not_rendered(secret, str(exc_info.value))

    mcp_report = copy.deepcopy(report)
    mcp_report["risk_analysis"][0]["analysis"] = "mcp://local-secret-endpoint"
    with pytest.raises(ResearchReportSecretError):
        write_research_report_v1(mcp_report, tmp_path / "research_reports", "20260527T120000")

    dotenv_report = copy.deepcopy(report)
    dotenv_report["risk_analysis"][0]["analysis"] = "load path/to/.env.local"
    with pytest.raises(ResearchReportSecretError):
        write_research_report_v1(dotenv_report, tmp_path / "research_reports", "20260527T120000")


def test_builder_rejects_secret_like_input_without_rendering_secret():
    inputs = _fake_inputs()
    secret = "A9abcdefABCDEF1234567890abcdefABCDEF1234567890z"
    inputs["score_explainability"]["provider_caveats"][0][secret] = "value"

    with pytest.raises(ResearchReportSecretError) as exc_info:
        build_research_report_v1(**inputs)

    message = str(exc_info.value)
    assert "<masked>" in message
    assert "<masked_key>" in message
    _assert_secret_not_rendered(secret, message)


def test_module_does_not_import_provider_runtime_read_env_network_or_mcp():
    source = inspect.getsource(report_module)

    assert "data_providers" not in source
    assert "tushare_provider" not in source
    assert "akshare_provider" not in source
    assert "provider_router" not in source
    assert "import os" not in source
    assert "os.environ" not in source
    assert "getenv" not in source
    assert "requests" not in source
    assert "socket" not in source
    assert "urllib" not in source
    assert "list_mcp" not in source
    assert "mcp__" not in source
    assert "scoring_engine" not in source
    assert "readiness" not in source
    assert "validator" not in source
