# -*- coding: utf-8 -*-

from __future__ import annotations

import copy
import json

import pytest

from src.fundamental_skill.research_planning.ticker_research_context_skeleton import (
    COMPANY_BUSINESS_PROFILE_SCHEMA_VERSION,
    DATA_GAP_PLAN_SCHEMA_VERSION,
    INDUSTRY_CONTEXT_SCHEMA_VERSION,
    MACRO_TRANSMISSION_PATH_SCHEMA_VERSION,
    TICKER_RESEARCH_CONTEXT_SCHEMA_VERSION,
    build_financial_context_from_provider_candidate,
    build_industry_context_seed,
    build_macro_transmission_prompt_seed,
    build_ticker_research_context_skeleton,
    validate_ticker_research_context_skeleton,
)


def _provider_candidate_result(
    *,
    stock_code="000001",
    ts_code="000001.SZ",
    company_name_hint="Sample Company",
):
    return {
        "schema_version": "provider_candidate_financial_snapshot.v1",
        "provider": "Tushare",
        "ts_code": ts_code,
        "stock_code": stock_code,
        "company_name_hint": company_name_hint,
        "periods": ["20251231"],
        "trend_table": [
            {
                "schema_version": "provider_candidate_financial_trend_table.v1",
                "provider": "Tushare",
                "period_label": "2025FY",
                "period": "20251231",
                "ann_date": "20260430",
                "end_date": "20251231",
                "source_tables_available": ["income", "balancesheet", "cashflow", "fina_indicator"],
                "selected_metrics": {
                    "revenue": 1000,
                    "n_income_attr_p": 120,
                    "total_profit": 150,
                    "n_cashflow_act": 180,
                    "total_assets": 3000,
                    "grossprofit_margin": 32.5,
                    "inv_turn": None,
                },
                "missing_fields": ["fina_indicator.inv_turn"],
                "not_official_verified": True,
                "not_for_trading_advice": True,
            }
        ],
        "blocked_reasons": [],
        "caveats": ["provider row requires official checks"],
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }


def _verification_queue(
    *,
    stock_code="000001",
    ts_code="000001.SZ",
    company_name_hint="Sample Company",
):
    return {
        "schema_version": "provider_candidate_metric_verification_queue.v1",
        "provider": "Tushare",
        "ts_code": ts_code,
        "stock_code": stock_code,
        "company_name_hint": company_name_hint,
        "periods": ["20251231"],
        "verification_items": [
            {
                "schema_version": "provider_candidate_metric_verification_item.v1",
                "provider": "Tushare",
                "ts_code": ts_code,
                "stock_code": stock_code,
                "company_name_hint": company_name_hint,
                "period": "20251231",
                "period_label": "2025FY",
                "ann_date": "20260430",
                "end_date": "20251231",
                "metric_key": "revenue",
                "metric_value": 1000,
                "source_table": "income",
                "source_field": "revenue",
                "source_table_available": True,
                "provider_native_unit": "provider_native_amount_unverified",
                "value_status": "present",
                "official_verification_status": "pending_official_verification",
                "official_verification_required": True,
                "not_official_verified": True,
                "not_for_trading_advice": True,
                "caveats": ["provider candidate requires official checks"],
            },
            {
                "schema_version": "provider_candidate_metric_verification_item.v1",
                "provider": "Tushare",
                "ts_code": ts_code,
                "stock_code": stock_code,
                "company_name_hint": company_name_hint,
                "period": "20251231",
                "period_label": "2025FY",
                "ann_date": "20260430",
                "end_date": "20251231",
                "metric_key": "inv_turn",
                "metric_value": None,
                "source_table": "fina_indicator",
                "source_field": "inv_turn",
                "source_table_available": True,
                "provider_native_unit": "provider_native_turnover_unverified",
                "value_status": "missing",
                "official_verification_status": "pending_official_verification",
                "official_verification_required": True,
                "not_official_verified": True,
                "not_for_trading_advice": True,
                "caveats": ["missing_provider_metric:inv_turn"],
            },
        ],
        "blocked_reasons": [],
        "caveats": ["provider candidate values require official checks"],
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }


def _payload(**overrides):
    payload = {
        "ts_code": "000001.SZ",
        "stock_code": "000001",
        "company_name_hint": "Sample Company",
        "provider_candidate_financial_result": _provider_candidate_result(),
        "provider_candidate_metric_verification_queue": _verification_queue(),
        "not_for_trading_advice": True,
    }
    payload.update(overrides)
    return payload


def _flatten_strings(value):
    result = []
    if isinstance(value, dict):
        for key, child in value.items():
            result.append(str(key))
            result.extend(_flatten_strings(child))
    elif isinstance(value, list):
        for child in value:
            result.extend(_flatten_strings(child))
    elif isinstance(value, str):
        result.append(value)
    return result


def test_generic_ticker_payload_builds_context():
    context = build_ticker_research_context_skeleton(_payload())

    assert context["schema_version"] == TICKER_RESEARCH_CONTEXT_SCHEMA_VERSION
    assert context["stock_code"] == "000001"
    assert "company_business_profile" in context
    assert context["company_business_profile"]["schema_version"] == COMPANY_BUSINESS_PROFILE_SCHEMA_VERSION
    assert context["industry_context"]["schema_version"] == INDUSTRY_CONTEXT_SCHEMA_VERSION
    assert context["macro_transmission_path"]["schema_version"] == MACRO_TRANSMISSION_PATH_SCHEMA_VERSION
    assert context["data_gap_plan"]["schema_version"] == DATA_GAP_PLAN_SCHEMA_VERSION
    assert context["not_for_trading_advice"] is True


def test_company_business_context_alias_matches_company_business_profile():
    context = build_ticker_research_context_skeleton(_payload())

    assert context["company_business_context"] == context["company_business_profile"]


def test_600406_sample_payload_builds_context_without_hardcoded_business_conclusion():
    payload = _payload(
        ts_code="600406.SH",
        stock_code="600406",
        company_name_hint="Guodian NARI",
        provider_candidate_financial_result=_provider_candidate_result(
            stock_code="600406",
            ts_code="600406.SH",
            company_name_hint="Guodian NARI",
        ),
        provider_candidate_metric_verification_queue=_verification_queue(
            stock_code="600406",
            ts_code="600406.SH",
            company_name_hint="Guodian NARI",
        ),
    )

    context = build_ticker_research_context_skeleton(payload)
    business_profile = context["company_business_profile"]
    serialized = json.dumps(context, ensure_ascii=False).lower()

    assert context["stock_code"] == "600406"
    assert business_profile["business_segments"] == []
    assert business_profile["main_products"] == []
    assert "grid automation" not in serialized
    assert "state grid" not in serialized


def test_provider_candidate_financial_result_produces_financial_context():
    financial_context = build_financial_context_from_provider_candidate(_payload())

    assert financial_context["schema_version"] == "provider_candidate_financial_context.v1"
    assert financial_context["provider_trend_periods"] == ["20251231"]
    assert financial_context["key_metric_candidates"]
    assert "provider_candidate" in financial_context["evidence_status"]


def test_provider_candidate_metric_verification_queue_produces_pending_count():
    financial_context = build_financial_context_from_provider_candidate(_payload())

    assert financial_context["pending_official_verification_count"] == 2
    assert "pending_official_verification" in financial_context["evidence_status"]


def test_missing_business_composition_records_business_data_gap():
    context = build_ticker_research_context_skeleton(_payload())
    business_profile = context["company_business_profile"]

    assert business_profile["evidence_status"] == "data_gap"
    assert any(gap["gap_id"] == "company_business_composition_missing" for gap in business_profile["data_gaps"])


def test_explicit_industry_framework_hint_drives_industry_context():
    payload = _payload(
        strategy_type="stable_growth",
        sub_type="input_power_grid_hint",
        industry_framework_hint={
            "framework_id": "stable_growth",
            "industry_tags": ["input_power_grid_hint"],
            "driver_questions": ["Which disclosed demand data should be tested?"],
            "macro_variables": ["grid investment cycle"],
        },
    )

    industry_context = build_industry_context_seed(payload)

    assert industry_context["strategy_type"] == "stable_growth"
    assert industry_context["sub_type"] == "input_power_grid_hint"
    assert industry_context["industry_tags"] == ["input_power_grid_hint"]
    assert industry_context["evidence_status"] == "framework_inference"
    assert industry_context["industry_data_gaps"] == []


def test_no_strategy_type_produces_industry_gap_and_not_assessable():
    industry_context = build_industry_context_seed(_payload())

    assert industry_context["evidence_status"] == "not_assessable"
    assert industry_context["possible_industry_frameworks"] == []
    assert any(gap["gap_id"] == "explicit_industry_context_missing" for gap in industry_context["industry_data_gaps"])


def test_macro_seed_produces_questions_not_conclusions():
    macro_path = build_macro_transmission_prompt_seed(
        _payload(industry_framework_hint={"framework_id": "generic_framework"})
    )
    serialized = json.dumps(macro_path).lower()

    assert macro_path["schema_version"] == MACRO_TRANSMISSION_PATH_SCHEMA_VERSION
    assert macro_path["industry_to_company_transmission_questions"]
    assert "favorable" not in serialized
    assert "tailwind" not in serialized
    assert "boom" not in serialized


def test_research_questions_cover_required_categories():
    context = build_ticker_research_context_skeleton(_payload())
    categories = {question["category"] for question in context["research_questions"]["questions"]}

    assert {
        "company_business_model",
        "financial_quality",
        "industry_context",
        "macro_transmission",
        "official_verification",
        "data_gap",
    }.issubset(categories)


def test_provider_candidate_not_upgraded_to_official_verified():
    context = build_ticker_research_context_skeleton(_payload())
    financial_strings = _flatten_strings(context["financial_context"])

    assert "official_verified" not in financial_strings
    assert all(item["current_evidence_status"] == "provider_candidate" for item in context["financial_context"]["key_metric_candidates"])


def test_explicit_official_verified_evidence_can_be_preserved_if_supplied():
    context = build_ticker_research_context_skeleton(
        _payload(
            official_anchor_candidates=[
                {
                    "anchor_id": "annual_business_section",
                    "evidence_status": "official_verified",
                    "source_type": "official_disclosure",
                }
            ]
        )
    )

    summary = context["evidence_status_summary"]
    assert summary["has_explicit_official_evidence"] is True
    assert "official_verified" in summary["official_evidence_statuses"]
    assert "official_verified" in summary["statuses_used"]


def test_research_question_text_containing_official_verified_is_rejected():
    context = build_ticker_research_context_skeleton(_payload())
    context["research_questions"]["questions"][0]["question_text"] = "official_verified should not be text"

    with pytest.raises(ValueError, match="official_verified"):
        validate_ticker_research_context_skeleton(context)


def test_data_gap_description_containing_official_verified_is_rejected():
    context = build_ticker_research_context_skeleton(_payload())
    context["data_gap_plan"]["data_gaps"][0]["description"] = "official_verified should not be text"

    with pytest.raises(ValueError, match="official_verified"):
        validate_ticker_research_context_skeleton(context)


def test_no_output_fixture_or_manifest_write(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    context = build_ticker_research_context_skeleton(_payload())

    assert context["schema_version"] == TICKER_RESEARCH_CONTEXT_SCHEMA_VERSION
    assert not (tmp_path / "output").exists()
    assert not (tmp_path / "fixtures").exists()
    assert not (tmp_path / "accepted_manifest.json").exists()


def test_input_payload_is_not_mutated():
    payload = _payload()
    before = copy.deepcopy(payload)

    build_ticker_research_context_skeleton(payload)

    assert payload == before
