# -*- coding: utf-8 -*-

from __future__ import annotations

import copy

import pytest

from src.fundamental_skill.data_verification.provider_candidate_verification_queue import (
    OFFICIAL_VERIFICATION_STATUS,
    PROVIDER_NAME,
    QUEUE_SCHEMA_VERSION,
    ProviderCandidateVerificationQueueError,
    build_provider_candidate_metric_verification_queue,
    select_metric_keys_for_official_verification,
    validate_provider_candidate_metric_verification_queue,
)


def _provider_candidate_result(**overrides):
    result = {
        "schema_version": "provider_candidate_financial_snapshot.v1",
        "provider": PROVIDER_NAME,
        "ts_code": "600406.SH",
        "stock_code": "600406",
        "company_name_hint": "Guodian NARI",
        "periods": ["20251231", "20260331"],
        "trend_table": [
            {
                "schema_version": "provider_candidate_financial_trend_table.v1",
                "provider": PROVIDER_NAME,
                "period_label": "2025FY",
                "period": "20251231",
                "ann_date": "20260430",
                "end_date": "20251231",
                "source_tables_available": ["income", "balancesheet", "cashflow", "fina_indicator"],
                "selected_metrics": {
                    "revenue": 1000,
                    "n_income_attr_p": 120,
                    "total_profit": 150,
                    "operate_profit": 140,
                    "basic_eps": 1.23,
                    "n_cashflow_act": 180,
                    "c_fr_sale_sg": 980,
                    "c_cash_equ_end_period": 500,
                    "total_assets": 3000,
                    "total_liab": 900,
                    "accounts_receiv": 330,
                    "inventories": 80,
                    "total_hldr_eqy_exc_min_int": 2100,
                    "grossprofit_margin": 32.5,
                    "netprofit_margin": 12.0,
                    "roe": 16.0,
                    "debt_to_assets": 30.0,
                    "ar_turn": 4.0,
                    "inv_turn": None,
                },
                "not_official_verified": True,
                "not_for_trading_advice": True,
            },
            {
                "schema_version": "provider_candidate_financial_trend_table.v1",
                "provider": PROVIDER_NAME,
                "period_label": "2026Q1",
                "period": "20260331",
                "ann_date": "20260430",
                "end_date": "20260331",
                "source_tables_available": ["income", "balancesheet", "cashflow", "fina_indicator"],
                "selected_metrics": {
                    "revenue": 260,
                    "n_income_attr_p": 32,
                    "total_profit": 40,
                    "operate_profit": 38,
                    "basic_eps": 0.32,
                    "n_cashflow_act": 45,
                    "c_fr_sale_sg": 255,
                    "c_cash_equ_end_period": 520,
                    "total_assets": 3180,
                    "total_liab": 980,
                    "accounts_receiv": 350,
                    "inventories": 85,
                    "total_hldr_eqy_exc_min_int": 2200,
                    "grossprofit_margin": 33.0,
                    "netprofit_margin": 12.3,
                    "roe": 4.2,
                    "debt_to_assets": 30.8,
                    "ar_turn": 1.0,
                    "inv_turn": None,
                },
                "not_official_verified": True,
                "not_for_trading_advice": True,
            },
        ],
        "blocked_reasons": [],
        "caveats": ["multiple_provider_rows:cashflow:20260331"],
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }
    result.update(overrides)
    return result


def _item(queue, *, period, metric_key):
    matches = [
        item
        for item in queue["verification_items"]
        if item["period"] == period and item["metric_key"] == metric_key
    ]
    assert len(matches) == 1
    return matches[0]


def _valid_queue():
    return build_provider_candidate_metric_verification_queue(_provider_candidate_result())


def test_valid_tushare_provider_candidate_result_builds_verification_queue():
    queue = build_provider_candidate_metric_verification_queue(_provider_candidate_result())

    assert queue["schema_version"] == QUEUE_SCHEMA_VERSION
    assert queue["provider"] == PROVIDER_NAME
    assert queue["ts_code"] == "600406.SH"
    assert queue["stock_code"] == "600406"
    assert queue["periods"] == ["20251231", "20260331"]
    assert queue["not_official_verified"] is True
    assert queue["not_for_trading_advice"] is True
    assert len(queue["verification_items"]) == 38
    assert {item["period_label"] for item in queue["verification_items"]} == {"2025FY", "2026Q1"}
    assert "multiple_provider_rows:cashflow:20260331" in queue["caveats"]


def test_generated_valid_queue_passes_validator():
    queue = _valid_queue()

    validate_provider_candidate_metric_verification_queue(queue)


@pytest.mark.parametrize(
    "field, message",
    [
        ("ts_code", "ts_code"),
        ("stock_code", "stock_code"),
        ("period_label", "period_label"),
        ("end_date", "end_date"),
    ],
)
def test_validator_rejects_item_missing_required_identity_or_period_field(field, message):
    queue = _valid_queue()
    queue["verification_items"][0].pop(field)

    with pytest.raises(ProviderCandidateVerificationQueueError, match=message):
        validate_provider_candidate_metric_verification_queue(queue)


def test_validator_allows_company_name_hint_key_with_none_value():
    result = _provider_candidate_result(company_name_hint=None)

    queue = build_provider_candidate_metric_verification_queue(result)

    assert all("company_name_hint" in item for item in queue["verification_items"])
    assert all(item["company_name_hint"] is None for item in queue["verification_items"])
    validate_provider_candidate_metric_verification_queue(queue)


def test_ann_date_none_is_allowed_and_recorded_as_caveat():
    result = _provider_candidate_result()
    result["trend_table"][0]["ann_date"] = None

    queue = build_provider_candidate_metric_verification_queue(result)

    item = _item(queue, period="20251231", metric_key="revenue")
    assert item["ann_date"] is None
    assert "missing_provider_ann_date" in item["caveats"]
    validate_provider_candidate_metric_verification_queue(queue)


def test_validator_rejects_value_status_present_with_metric_value_none():
    queue = _valid_queue()
    item = _item(queue, period="20251231", metric_key="revenue")
    item["metric_value"] = None
    item["value_status"] = "present"

    with pytest.raises(ProviderCandidateVerificationQueueError, match="present_item_missing_value"):
        validate_provider_candidate_metric_verification_queue(queue)


def test_validator_rejects_source_table_unavailable_with_present_value_status():
    queue = _valid_queue()
    item = _item(queue, period="20251231", metric_key="revenue")
    item["source_table_available"] = False
    item["value_status"] = "present"

    with pytest.raises(ProviderCandidateVerificationQueueError, match="unavailable_source_table"):
        validate_provider_candidate_metric_verification_queue(queue)


def test_validator_rejects_source_table_unavailable_with_metric_value():
    queue = _valid_queue()
    item = _item(queue, period="20251231", metric_key="revenue")
    item["source_table_available"] = False
    item["value_status"] = "missing"

    with pytest.raises(ProviderCandidateVerificationQueueError, match="unavailable_source_table_has_value"):
        validate_provider_candidate_metric_verification_queue(queue)


def test_verification_items_keep_provider_candidate_and_pending_markers():
    queue = build_provider_candidate_metric_verification_queue(_provider_candidate_result())

    assert all(item["provider"] == PROVIDER_NAME for item in queue["verification_items"])
    assert all(item["not_official_verified"] is True for item in queue["verification_items"])
    assert all(item["not_for_trading_advice"] is True for item in queue["verification_items"])
    assert all(
        item["official_verification_status"] == OFFICIAL_VERIFICATION_STATUS
        for item in queue["verification_items"]
    )
    assert all(item["official_verification_required"] is True for item in queue["verification_items"])


def test_key_metrics_enter_queue_with_source_metadata():
    queue = build_provider_candidate_metric_verification_queue(_provider_candidate_result())

    revenue = _item(queue, period="20251231", metric_key="revenue")
    assert revenue["metric_value"] == 1000
    assert revenue["source_table"] == "income"
    assert revenue["source_field"] == "revenue"
    assert revenue["value_status"] == "present"

    assert _item(queue, period="20251231", metric_key="n_income_attr_p")["metric_value"] == 120
    assert _item(queue, period="20260331", metric_key="n_cashflow_act")["source_table"] == "cashflow"
    assert _item(queue, period="20260331", metric_key="total_assets")["source_table"] == "balancesheet"
    assert _item(queue, period="20260331", metric_key="grossprofit_margin")["source_table"] == "fina_indicator"


def test_missing_metric_becomes_missing_item_without_fabrication():
    queue = build_provider_candidate_metric_verification_queue(_provider_candidate_result())

    missing = _item(queue, period="20251231", metric_key="inv_turn")

    assert missing["metric_value"] is None
    assert missing["value_status"] == "missing"
    assert "missing_provider_metric:inv_turn" in missing["caveats"]
    assert missing["official_verification_status"] == OFFICIAL_VERIFICATION_STATUS


def test_metric_selection_policy_is_deterministic():
    assert select_metric_keys_for_official_verification() == [
        "revenue",
        "n_income_attr_p",
        "total_profit",
        "operate_profit",
        "basic_eps",
        "n_cashflow_act",
        "c_fr_sale_sg",
        "c_cash_equ_end_period",
        "total_assets",
        "total_liab",
        "accounts_receiv",
        "inventories",
        "total_hldr_eqy_exc_min_int",
        "grossprofit_margin",
        "netprofit_margin",
        "roe",
        "debt_to_assets",
        "ar_turn",
        "inv_turn",
    ]


def test_input_provider_other_than_tushare_is_blocked():
    result = _provider_candidate_result(provider="OtherProvider")

    queue = build_provider_candidate_metric_verification_queue(result)

    assert queue["verification_items"] == []
    assert "unsupported_provider" in queue["blocked_reasons"]


def test_input_schema_version_error_is_blocked():
    result = _provider_candidate_result(schema_version="wrong_schema")

    queue = build_provider_candidate_metric_verification_queue(result)

    assert queue["verification_items"] == []
    assert "invalid_provider_candidate_schema_version" in queue["blocked_reasons"]


def test_input_missing_is_blocked():
    queue = build_provider_candidate_metric_verification_queue(None)

    assert queue["verification_items"] == []
    assert queue["blocked_reasons"] == ["missing_provider_candidate_result"]


def test_trend_table_missing_or_non_list_is_blocked():
    missing = _provider_candidate_result()
    missing.pop("trend_table")
    non_list = _provider_candidate_result(trend_table="not a list")

    missing_queue = build_provider_candidate_metric_verification_queue(missing)
    non_list_queue = build_provider_candidate_metric_verification_queue(non_list)

    assert "missing_trend_table" in missing_queue["blocked_reasons"]
    assert "trend_table_must_be_list" in non_list_queue["blocked_reasons"]
    assert missing_queue["verification_items"] == []
    assert non_list_queue["verification_items"] == []


def test_trend_row_missing_period_or_provider_is_blocked():
    missing_period = _provider_candidate_result()
    missing_period["trend_table"][0].pop("period")
    missing_provider = _provider_candidate_result()
    missing_provider["trend_table"][0].pop("provider")

    period_queue = build_provider_candidate_metric_verification_queue(missing_period)
    provider_queue = build_provider_candidate_metric_verification_queue(missing_provider)

    assert "missing_trend_row_period:0" in period_queue["blocked_reasons"]
    assert "missing_trend_row_provider:0" in provider_queue["blocked_reasons"]
    assert period_queue["verification_items"] == []
    assert provider_queue["verification_items"] == []


def test_input_candidate_flags_fail_closed_when_missing_false_or_non_bool():
    missing = _provider_candidate_result()
    missing.pop("not_official_verified")
    false_value = _provider_candidate_result(not_official_verified=False)
    non_bool = _provider_candidate_result(not_for_trading_advice="true")

    assert "missing_not_official_verified" in build_provider_candidate_metric_verification_queue(missing)[
        "blocked_reasons"
    ]
    assert "not_official_verified_must_be_true_bool" in build_provider_candidate_metric_verification_queue(
        false_value
    )["blocked_reasons"]
    assert "advice_safety_flag_must_be_true_bool" in build_provider_candidate_metric_verification_queue(
        non_bool
    )["blocked_reasons"]


def test_trend_row_candidate_flags_fail_closed_when_missing_false_or_non_bool():
    missing = _provider_candidate_result()
    missing["trend_table"][0].pop("not_for_trading_advice")
    false_value = _provider_candidate_result()
    false_value["trend_table"][0]["not_official_verified"] = False
    non_bool = _provider_candidate_result()
    non_bool["trend_table"][0]["not_for_trading_advice"] = "true"

    assert "trend_row:0:missing_advice_safety_flag" in build_provider_candidate_metric_verification_queue(
        missing
    )["blocked_reasons"]
    assert "trend_row:0:not_official_verified_must_be_true_bool" in build_provider_candidate_metric_verification_queue(
        false_value
    )["blocked_reasons"]
    assert "trend_row:0:advice_safety_flag_must_be_true_bool" in build_provider_candidate_metric_verification_queue(
        non_bool
    )["blocked_reasons"]


def test_official_verified_marker_is_rejected_from_input():
    result = _provider_candidate_result()
    result["trend_table"][0]["official_verified"] = True

    with pytest.raises(ProviderCandidateVerificationQueueError, match="forbidden_marker"):
        build_provider_candidate_metric_verification_queue(result)


def test_official_metric_fact_and_provider_conflict_markers_are_rejected():
    official_metric_fact = _provider_candidate_result()
    official_metric_fact["trend_table"][0]["selected_metrics"]["revenue"] = "official_metric_fact"
    provider_conflict = _provider_candidate_result()
    provider_conflict["caveats"].append("provider_official_conflict")

    with pytest.raises(ProviderCandidateVerificationQueueError, match="forbidden_marker"):
        build_provider_candidate_metric_verification_queue(official_metric_fact)
    with pytest.raises(ProviderCandidateVerificationQueueError, match="forbidden_marker"):
        build_provider_candidate_metric_verification_queue(provider_conflict)


def test_metric_value_forbidden_marker_is_rejected():
    result = _provider_candidate_result()
    result["trend_table"][0]["selected_metrics"]["revenue"] = "target price"

    with pytest.raises(ProviderCandidateVerificationQueueError, match="forbidden_marker"):
        build_provider_candidate_metric_verification_queue(result)


def test_provider_queue_does_not_write_output_fixtures_or_manifest(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    queue = build_provider_candidate_metric_verification_queue(_provider_candidate_result())

    assert queue["provider"] == PROVIDER_NAME
    assert not (tmp_path / "output").exists()
    assert not (tmp_path / "fixtures").exists()
    assert not (tmp_path / "accepted_manifest.json").exists()


def test_valid_input_is_not_mutated():
    result = _provider_candidate_result()
    before = copy.deepcopy(result)

    build_provider_candidate_metric_verification_queue(result)

    assert result == before
