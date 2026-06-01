# -*- coding: utf-8 -*-

from __future__ import annotations

import copy

from src.fundamental_skill.data_providers.tushare_financial_provider import (
    DEFAULT_COMPANY_NAME_HINT,
    PROVIDER_NAME,
    SUPPORTED_PERIODS,
    build_tushare_financial_provider_candidate,
)


def _base_responses():
    return {
        ("income", "20251231"): [
            {
                "ts_code": "600406.SH",
                "period": "20251231",
                "ann_date": "20260430",
                "end_date": "20251231",
                "update_flag": "1",
                "report_type": "1",
                "revenue": 1000,
                "n_income_attr_p": 120,
                "total_profit": 150,
                "operate_profit": 140,
                "basic_eps": 1.23,
            }
        ],
        ("balancesheet", "20251231"): [
            {
                "ts_code": "600406.SH",
                "period": "20251231",
                "ann_date": "20260430",
                "end_date": "20251231",
                "total_assets": 3000,
                "total_liab": 900,
                "total_hldr_eqy_exc_min_int": 2100,
                "accounts_receiv": 330,
                "inventories": 80,
            }
        ],
        ("cashflow", "20251231"): [
            {
                "ts_code": "600406.SH",
                "period": "20251231",
                "ann_date": "20260430",
                "end_date": "20251231",
                "n_cashflow_act": 180,
                "c_cash_equ_end_period": 500,
                "c_fr_sale_sg": 980,
            }
        ],
        ("fina_indicator", "20251231"): [
            {
                "ts_code": "600406.SH",
                "period": "20251231",
                "ann_date": "20260430",
                "end_date": "20251231",
                "grossprofit_margin": 32.5,
                "netprofit_margin": 12.0,
                "roe": 16.0,
                "debt_to_assets": 30.0,
                "ar_turn": 4.0,
                "inv_turn": 8.0,
            }
        ],
        ("income", "20260331"): [
            {
                "ts_code": "600406.SH",
                "period": "20260331",
                "ann_date": "20260429",
                "end_date": "20260331",
                "revenue": 260,
                "n_income_attr_p": 32,
                "total_profit": 40,
                "operate_profit": 38,
                "basic_eps": 0.32,
            }
        ],
        ("balancesheet", "20260331"): [
            {
                "ts_code": "600406.SH",
                "period": "20260331",
                "ann_date": "20260429",
                "end_date": "20260331",
                "total_assets": 3180,
                "total_liab": 980,
                "total_hldr_eqy_exc_min_int": 2200,
                "accounts_receiv": 350,
                "inventories": 85,
            }
        ],
        ("cashflow", "20260331"): [
            {
                "ts_code": "600406.SH",
                "period": "20260331",
                "ann_date": "20260429",
                "end_date": "20260331",
                "n_cashflow_act": 45,
                "c_cash_equ_end_period": 520,
                "c_fr_sale_sg": 255,
            }
        ],
        ("fina_indicator", "20260331"): [
            {
                "ts_code": "600406.SH",
                "period": "20260331",
                "ann_date": "20260429",
                "end_date": "20260331",
                "grossprofit_margin": 33.0,
                "netprofit_margin": 12.3,
                "roe": 4.2,
                "debt_to_assets": 30.8,
                "ar_turn": 1.0,
                "inv_turn": 2.0,
            }
        ],
    }


class _FakeFinancialClient:
    def __init__(self, responses=None):
        self.responses = responses if responses is not None else _base_responses()
        self.calls = []

    def income(self, **params):
        return self._call("income", **params)

    def balancesheet(self, **params):
        return self._call("balancesheet", **params)

    def cashflow(self, **params):
        return self._call("cashflow", **params)

    def fina_indicator(self, **params):
        return self._call("fina_indicator", **params)

    def _call(self, endpoint, **params):
        self.calls.append({"endpoint": endpoint, "params": dict(params)})
        response = self.responses.get((endpoint, params["period"]), [])
        if isinstance(response, BaseException):
            raise response
        return copy.deepcopy(response)


def _build(client=None, **overrides):
    return build_tushare_financial_provider_candidate(
        ts_code="600406.SH",
        periods=list(SUPPORTED_PERIODS),
        company_name_hint=DEFAULT_COMPANY_NAME_HINT,
        api_client=client or _FakeFinancialClient(),
        **overrides,
    )


def _missing_table_reason_recorded(result, *, table_name, period, reason):
    return {
        "provider": PROVIDER_NAME,
        "table_name": table_name,
        "period": period,
        "reason": reason,
    } in result["missing_tables"]


def test_fake_client_returns_all_target_tables_and_trend_rows_for_target_periods():
    client = _FakeFinancialClient()
    result = _build(client)

    assert result["schema_version"] == "provider_candidate_financial_snapshot.v1"
    assert result["provider"] == PROVIDER_NAME
    assert result["ts_code"] == "600406.SH"
    assert result["stock_code"] == "600406"
    assert result["company_name_hint"] == "国电南瑞"
    assert result["periods"] == ["20251231", "20260331"]
    assert result["not_official_verified"] is True
    assert result["not_for_trading_advice"] is True
    assert [row["period_label"] for row in result["trend_table"]] == ["2025FY", "2026Q1"]

    assert all(row["provider"] == PROVIDER_NAME for row in result["income_rows"])
    assert all(row["not_official_verified"] is True for row in result["income_rows"])
    assert all(row["not_for_trading_advice"] is True for row in result["income_rows"])
    assert all(row["provider"] == PROVIDER_NAME for row in result["balancesheet_rows"])
    assert all(row["provider"] == PROVIDER_NAME for row in result["cashflow_rows"])
    assert all(row["provider"] == PROVIDER_NAME for row in result["fina_indicator_rows"])
    assert result["income_rows"][0]["original_fields"]["update_flag"] == "1"
    assert result["income_rows"][0]["original_fields"]["report_type"] == "1"

    first_trend, second_trend = result["trend_table"]
    assert first_trend["revenue"] == 1000
    assert first_trend["n_income_attr_p"] == 120
    assert first_trend["total_assets"] == 3000
    assert first_trend["n_cashflow_act"] == 180
    assert first_trend["grossprofit_margin"] == 32.5
    assert second_trend["revenue"] == 260
    assert second_trend["roe"] == 4.2
    assert set(first_trend["source_tables_available"]) == {
        "income",
        "balancesheet",
        "cashflow",
        "fina_indicator",
    }
    assert [call["endpoint"] for call in client.calls] == [
        "income",
        "balancesheet",
        "cashflow",
        "fina_indicator",
        "income",
        "balancesheet",
        "cashflow",
        "fina_indicator",
    ]
    assert all(call["params"]["ts_code"] == "600406.SH" for call in client.calls)


def test_missing_table_and_missing_field_are_recorded_without_fabrication():
    responses = _base_responses()
    responses[("cashflow", "20260331")] = []
    responses[("income", "20260331")] = [
        {
            "ts_code": "600406.SH",
            "period": "20260331",
            "ann_date": "20260429",
            "end_date": "20260331",
            "revenue": 260,
            "n_income_attr_p": 32,
            "total_profit": 40,
            "operate_profit": 38,
        }
    ]
    result = _build(_FakeFinancialClient(responses))

    assert {
        "provider": PROVIDER_NAME,
        "table_name": "cashflow",
        "period": "20260331",
        "reason": "empty_response",
    } in result["missing_tables"]
    q1 = result["trend_table"][1]
    assert q1["basic_eps"] is None
    assert q1["n_cashflow_act"] is None
    assert "income.basic_eps" in q1["missing_fields"]
    assert "cashflow.n_cashflow_act" in q1["missing_fields"]
    assert "empty_response:cashflow:20260331" in result["blocked_reasons"]


def test_empty_api_result_is_blocked_and_caveated():
    client = _FakeFinancialClient(responses={})

    result = _build(client)

    assert len(result["missing_tables"]) == 8
    assert all(reason.startswith("empty_response:") for reason in result["blocked_reasons"])
    assert result["caveats"]
    assert result["trend_table"][0]["source_tables_available"] == []
    assert result["trend_table"][0]["revenue"] is None


def test_api_exception_is_blocked_without_leaking_exception_message():
    secret_like = "S3cr3tValueThatShouldStayHidden123456789"
    responses = _base_responses()
    responses[("income", "20251231")] = RuntimeError("provider failed " + secret_like)
    result = _build(_FakeFinancialClient(responses))

    assert "api_exception:income:20251231" in result["blocked_reasons"]
    assert secret_like not in repr(result)
    assert result["income_rows"][0]["period"] == "20260331"


def test_mismatched_income_ts_code_is_rejected_and_recorded():
    responses = _base_responses()
    responses[("income", "20251231")] = [
        {
            "ts_code": "000001.SZ",
            "period": "20251231",
            "ann_date": "20260430",
            "end_date": "20251231",
            "revenue": 999,
            "n_income_attr_p": 99,
            "total_profit": 99,
            "operate_profit": 99,
            "basic_eps": 9.99,
        }
    ]

    result = _build(_FakeFinancialClient(responses))

    assert all(row["ts_code"] == "600406.SH" for row in result["income_rows"])
    assert all(row["period"] != "20251231" for row in result["income_rows"])
    assert "row_ts_code_mismatch:income:20251231" in result["blocked_reasons"]
    assert _missing_table_reason_recorded(
        result,
        table_name="income",
        period="20251231",
        reason="row_ts_code_mismatch",
    )
    first_trend = result["trend_table"][0]
    assert first_trend["revenue"] is None
    assert "income" not in first_trend["source_tables_available"]


def test_mismatched_income_period_is_rejected_without_polluting_trend_row():
    responses = _base_responses()
    responses[("income", "20251231")] = [
        {
            "ts_code": "600406.SH",
            "period": "20241231",
            "ann_date": "20260430",
            "end_date": "20241231",
            "revenue": 999,
            "n_income_attr_p": 99,
            "total_profit": 99,
            "operate_profit": 99,
            "basic_eps": 9.99,
        }
    ]

    result = _build(_FakeFinancialClient(responses))

    assert all(row["period"] != "20241231" for row in result["income_rows"])
    assert "row_period_mismatch:income:20251231" in result["blocked_reasons"]
    assert _missing_table_reason_recorded(
        result,
        table_name="income",
        period="20251231",
        reason="row_period_mismatch",
    )
    first_trend = result["trend_table"][0]
    assert first_trend["revenue"] is None
    assert 999 not in first_trend["selected_metrics"].values()
    assert "income" not in first_trend["source_tables_available"]


def test_rows_missing_identity_fields_are_rejected_and_recorded():
    responses = _base_responses()
    responses[("income", "20251231")] = [
        {
            "period": "20251231",
            "ann_date": "20260430",
            "end_date": "20251231",
            "revenue": 101,
        },
        {
            "ts_code": "600406.SH",
            "ann_date": "20260430",
            "revenue": 202,
        },
    ]

    result = _build(_FakeFinancialClient(responses))

    assert "row_missing_ts_code:income:20251231" in result["blocked_reasons"]
    assert "row_missing_period:income:20251231" in result["blocked_reasons"]
    assert _missing_table_reason_recorded(
        result,
        table_name="income",
        period="20251231",
        reason="row_missing_ts_code",
    )
    assert _missing_table_reason_recorded(
        result,
        table_name="income",
        period="20251231",
        reason="row_missing_period",
    )
    assert result["trend_table"][0]["revenue"] is None


def test_mismatch_reason_does_not_leak_rejected_row_values():
    secret_like = "SensitiveMismatchValue9876543210ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    responses = _base_responses()
    responses[("income", "20251231")] = [
        {
            "ts_code": "000001.SZ",
            "period": "20251231",
            "ann_date": "20260430",
            "end_date": "20251231",
            "revenue": secret_like,
        }
    ]

    result = _build(_FakeFinancialClient(responses))

    recorded_reasons = repr(result["blocked_reasons"] + result["missing_tables"] + result["caveats"])
    assert "row_ts_code_mismatch:income:20251231" in result["blocked_reasons"]
    assert secret_like not in repr(result)
    assert secret_like not in recorded_reasons


def test_same_table_same_period_selects_latest_ann_date_for_trend_table():
    responses = _base_responses()
    responses[("income", "20251231")] = [
        {
            "ts_code": "600406.SH",
            "period": "20251231",
            "ann_date": "20260429",
            "end_date": "20251231",
            "revenue": 111,
            "n_income_attr_p": 11,
            "total_profit": 12,
            "operate_profit": 13,
            "basic_eps": 0.11,
        },
        {
            "ts_code": "600406.SH",
            "period": "20251231",
            "ann_date": "20260430",
            "end_date": "20251231",
            "revenue": 222,
            "n_income_attr_p": 22,
            "total_profit": 23,
            "operate_profit": 24,
            "basic_eps": 0.22,
        },
    ]

    result = _build(_FakeFinancialClient(responses))

    assert result["trend_table"][0]["revenue"] == 222
    assert result["trend_table"][0]["not_official_verified"] is True
    assert "multiple_provider_rows:income:20251231" in (
        result["blocked_reasons"] + result["caveats"]
    )


def test_same_table_same_period_missing_ann_date_is_still_deterministic():
    responses = _base_responses()
    responses[("income", "20251231")] = [
        {
            "ts_code": "600406.SH",
            "period": "20251231",
            "end_date": "20251231",
            "revenue": 111,
            "n_income_attr_p": 11,
            "total_profit": 12,
            "operate_profit": 13,
            "basic_eps": 0.11,
        },
        {
            "ts_code": "600406.SH",
            "period": "20251231",
            "end_date": "20251231",
            "revenue": 222,
            "n_income_attr_p": 22,
            "total_profit": 23,
            "operate_profit": 24,
            "basic_eps": 0.22,
        },
    ]

    result = _build(_FakeFinancialClient(responses))

    assert result["trend_table"][0]["revenue"] == 111
    assert result["income_rows"][0]["ann_date"] is None
    assert "multiple_provider_rows:income:20251231" in (
        result["blocked_reasons"] + result["caveats"]
    )


def test_missing_api_client_with_network_disabled_fails_closed():
    result = build_tushare_financial_provider_candidate(
        ts_code="600406.SH",
        periods=["20251231"],
        allow_network=False,
    )

    assert result["blocked_reasons"] == ["api_client_required_when_network_disabled"]
    assert result["income_rows"] == []
    assert result["trend_table"] == []


def test_network_enabled_without_environment_credential_fails_closed(monkeypatch):
    monkeypatch.delenv("TUSHARE_" + "TOKEN", raising=False)

    result = build_tushare_financial_provider_candidate(
        ts_code="600406.SH",
        periods=["20251231"],
        allow_network=True,
    )

    assert result["blocked_reasons"] == ["environment_credential_missing"]
    assert result["income_rows"] == []


def test_invalid_inputs_fail_closed_before_client_calls():
    client = _FakeFinancialClient()

    assert build_tushare_financial_provider_candidate(ts_code=None, periods=["20251231"], api_client=client)[
        "blocked_reasons"
    ] == ["missing_ts_code"]
    assert build_tushare_financial_provider_candidate(ts_code="600406", periods=["20251231"], api_client=client)[
        "blocked_reasons"
    ] == ["unsupported_ts_code_format"]
    assert build_tushare_financial_provider_candidate(ts_code="600406.SH", periods=None, api_client=client)[
        "blocked_reasons"
    ] == ["missing_periods"]
    assert build_tushare_financial_provider_candidate(ts_code="600406.SH", periods=("20251231",), api_client=client)[
        "blocked_reasons"
    ] == ["periods_must_be_list"]
    assert build_tushare_financial_provider_candidate(ts_code="600406.SH", periods=["20241231"], api_client=client)[
        "blocked_reasons"
    ] == ["unsupported_period"]
    assert client.calls == []


def test_deterministic_behavior_with_same_fake_input():
    result_a = _build(_FakeFinancialClient())
    result_b = _build(_FakeFinancialClient())

    assert result_a == result_b


def test_provider_candidate_does_not_write_output_fixtures_or_manifest(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    result = _build(_FakeFinancialClient())

    assert result["provider"] == PROVIDER_NAME
    assert not (tmp_path / "output").exists()
    assert not (tmp_path / "fixtures").exists()
    assert not (tmp_path / "accepted_manifest.json").exists()
