# -*- coding: utf-8 -*-

from __future__ import annotations

import copy

import pytest

from src.fundamental_skill.data_providers.tushare_financial_provider import (
    PROVIDER_NAME,
    TushareFinancialProviderCandidateError,
    assert_no_tushare_provider_forbidden_markers,
    build_tushare_financial_provider_candidate,
    validate_provider_candidate_financial_result,
)


class _MiniClient:
    def __init__(self, *, income_exception=None):
        self.income_exception = income_exception

    def income(self, **params):
        if self.income_exception is not None:
            raise self.income_exception
        return [
            {
                "ts_code": params["ts_code"],
                "period": params["period"],
                "ann_date": "20260430",
                "end_date": params["period"],
                "revenue": 100,
                "n_income_attr_p": 10,
                "total_profit": 12,
                "operate_profit": 11,
            }
        ]

    def balancesheet(self, **params):
        return [
            {
                "ts_code": params["ts_code"],
                "period": params["period"],
                "ann_date": "20260430",
                "end_date": params["period"],
                "total_assets": 300,
                "total_liab": 90,
            }
        ]

    def cashflow(self, **params):
        return [
            {
                "ts_code": params["ts_code"],
                "period": params["period"],
                "ann_date": "20260430",
                "end_date": params["period"],
                "n_cashflow_act": 20,
            }
        ]

    def fina_indicator(self, **params):
        return [
            {
                "ts_code": params["ts_code"],
                "period": params["period"],
                "ann_date": "20260430",
                "end_date": params["period"],
                "grossprofit_margin": 30,
                "netprofit_margin": 10,
                "roe": 15,
                "debt_to_assets": 30,
            }
        ]


def _valid_result():
    return build_tushare_financial_provider_candidate(
        ts_code="600406.SH",
        periods=["20251231"],
        api_client=_MiniClient(),
    )


@pytest.mark.parametrize(
    "marker",
    [
        "token",
        ".env",
        "tushare_token",
        "official_verified",
        "official_metric_fact",
        "provider_official_conflict",
        "Report V1",
        "accepted manifest write",
        "output baseline write",
        "fixture write",
        "buy",
        "sell",
        "hold",
        "target price",
        "portfolio",
        "position",
        "technical signal",
        "trading advice",
        "investment advice",
        "accepted_manifest_write",
        "output_baseline_write",
        "fixture_write",
        "target_price",
        "technical_signal",
    ],
)
def test_english_forbidden_markers_are_rejected(marker):
    with pytest.raises(TushareFinancialProviderCandidateError, match="forbidden_marker"):
        assert_no_tushare_provider_forbidden_markers({"outer": [{"inner": marker}]})


@pytest.mark.parametrize(
    "marker",
    [
        "买入",
        "卖出",
        "持有",
        "目标价",
        "仓位",
        "组合",
        "技术信号",
        "投资建议",
        "正式研报",
        "输出基线",
        "写入fixture",
        "写入accepted manifest",
        "读取token",
        "读取.env",
        "读取tushare_token",
    ],
)
def test_chinese_forbidden_markers_are_rejected(marker):
    with pytest.raises(TushareFinancialProviderCandidateError, match="forbidden_marker"):
        assert_no_tushare_provider_forbidden_markers({"nested": ["safe", {"marker": marker}]})


def test_provider_name_and_required_candidate_flags_are_not_false_positives():
    payload = {
        "provider": PROVIDER_NAME,
        "not_official_verified": True,
        "not_for_trading_advice": True,
        "nested": [{"provider": PROVIDER_NAME, "not_official_verified": True}],
    }

    assert_no_tushare_provider_forbidden_markers(payload)


def test_financial_statement_raw_field_names_are_not_trading_marker_false_positives():
    class _RawStatementFieldClient(_MiniClient):
        def income(self, **params):
            rows = super().income(**params)
            rows[0]["sell_exp"] = 5
            return rows

    result = build_tushare_financial_provider_candidate(
        ts_code="600406.SH",
        periods=["20251231"],
        api_client=_RawStatementFieldClient(),
    )

    assert result["income_rows"][0]["original_fields"]["sell_exp"] == 5
    assert result["not_official_verified"] is True


def test_result_validator_rejects_official_verified_key():
    result = _valid_result()
    result["official_verified"] = True

    with pytest.raises(TushareFinancialProviderCandidateError, match="forbidden_marker"):
        validate_provider_candidate_financial_result(result)


def test_result_validator_rejects_official_metric_fact_and_conflict_markers():
    result = _valid_result()
    result["caveats"].append({"lineage": ["official_metric_fact", "provider_official_conflict"]})

    with pytest.raises(TushareFinancialProviderCandidateError, match="forbidden_marker"):
        validate_provider_candidate_financial_result(result)


def test_result_validator_rejects_missing_or_false_not_official_verified():
    result = _valid_result()
    missing = copy.deepcopy(result)
    missing.pop("not_official_verified")
    false_value = copy.deepcopy(result)
    false_value["not_official_verified"] = False

    with pytest.raises(TushareFinancialProviderCandidateError, match="not_official_verified"):
        validate_provider_candidate_financial_result(missing)
    with pytest.raises(TushareFinancialProviderCandidateError, match="not_official_verified"):
        validate_provider_candidate_financial_result(false_value)


@pytest.mark.parametrize("bad_value", [False, "true", 1, None])
def test_result_validator_rejects_missing_false_or_non_bool_trading_advice_flag(bad_value):
    result = _valid_result()
    result["not_for_trading_advice"] = bad_value

    with pytest.raises(TushareFinancialProviderCandidateError, match="not_for_trading_advice"):
        validate_provider_candidate_financial_result(result)


def test_result_validator_rejects_row_candidate_flags_when_missing_or_false():
    result = _valid_result()
    result["income_rows"][0]["not_official_verified"] = False

    with pytest.raises(TushareFinancialProviderCandidateError, match="not_official_verified"):
        validate_provider_candidate_financial_result(result)

    result = _valid_result()
    result["trend_table"][0].pop("not_for_trading_advice")

    with pytest.raises(TushareFinancialProviderCandidateError, match="not_for_trading_advice"):
        validate_provider_candidate_financial_result(result)


def test_no_secret_value_appears_in_result_or_captured_output(capsys):
    secret_value = "HiddenCredentialValue9876543210ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    result = build_tushare_financial_provider_candidate(
        ts_code="600406.SH",
        periods=["20251231"],
        api_client=_MiniClient(income_exception=RuntimeError("credential=" + secret_value)),
    )
    captured = capsys.readouterr()

    assert secret_value not in repr(result)
    assert secret_value not in captured.out
    assert secret_value not in captured.err
    assert captured.out == ""
    assert captured.err == ""


def test_mismatch_rejection_reason_is_redacted_and_silent(capsys):
    secret_value = "HiddenMismatchValue9876543210ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    class _MismatchIncomeClient(_MiniClient):
        def income(self, **params):
            return [
                {
                    "ts_code": "000001.SZ",
                    "period": params["period"],
                    "ann_date": "20260430",
                    "end_date": params["period"],
                    "revenue": secret_value,
                }
            ]

    result = build_tushare_financial_provider_candidate(
        ts_code="600406.SH",
        periods=["20251231"],
        api_client=_MismatchIncomeClient(),
    )
    captured = capsys.readouterr()

    assert "row_ts_code_mismatch:income:20251231" in result["blocked_reasons"]
    assert secret_value not in repr(result)
    assert secret_value not in captured.out
    assert secret_value not in captured.err
    assert captured.out == ""
    assert captured.err == ""
