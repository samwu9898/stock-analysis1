# -*- coding: utf-8 -*-

from __future__ import annotations

import copy

import pytest

from src.fundamental_skill.data_verification.provider_candidate_verification_queue import (
    OFFICIAL_VERIFICATION_STATUS,
    PROVIDER_NAME,
    ProviderCandidateVerificationQueueError,
    assert_no_provider_candidate_queue_forbidden_markers,
    build_provider_candidate_metric_verification_queue,
    validate_provider_candidate_metric_verification_queue,
)


def _minimal_provider_candidate_result(**overrides):
    result = {
        "schema_version": "provider_candidate_financial_snapshot.v1",
        "provider": PROVIDER_NAME,
        "ts_code": "600406.SH",
        "stock_code": "600406",
        "company_name_hint": "Guodian NARI",
        "periods": ["20251231"],
        "trend_table": [
            {
                "schema_version": "provider_candidate_financial_trend_table.v1",
                "provider": PROVIDER_NAME,
                "period_label": "2025FY",
                "period": "20251231",
                "ann_date": "20260430",
                "end_date": "20251231",
                "source_tables_available": ["income"],
                "selected_metrics": {
                    "revenue": 100,
                    "n_income_attr_p": 10,
                },
                "not_official_verified": True,
                "not_for_trading_advice": True,
            }
        ],
        "blocked_reasons": [],
        "caveats": [],
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }
    result.update(overrides)
    return result


def _valid_queue():
    return build_provider_candidate_metric_verification_queue(_minimal_provider_candidate_result())


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
    with pytest.raises(ProviderCandidateVerificationQueueError, match="forbidden_marker"):
        assert_no_provider_candidate_queue_forbidden_markers({"outer": [{"inner": marker}]})


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
        "涔板叆",
        "鍗栧嚭",
        "鎸佹湁",
        "鐩爣浠?",
        "浠撲綅",
        "缁勫悎",
        "鎶€鏈俊鍙?",
        "鎶曡祫寤鸿",
        "姝ｅ紡鐮旀姤",
        "杈撳嚭鍩虹嚎",
        "鍐欏叆fixture",
        "鍐欏叆accepted manifest",
        "璇诲彇token",
        "璇诲彇.env",
        "璇诲彇tushare_token",
    ],
)
def test_chinese_forbidden_markers_are_rejected(marker):
    with pytest.raises(ProviderCandidateVerificationQueueError, match="forbidden_marker"):
        assert_no_provider_candidate_queue_forbidden_markers({"nested": ["safe", {"marker": marker}]})


def test_allowed_provider_and_candidate_flags_are_not_false_positives():
    payload = {
        "provider": PROVIDER_NAME,
        "not_official_verified": True,
        "not_for_trading_advice": True,
        "official_verification_status": OFFICIAL_VERIFICATION_STATUS,
        "official_verification_required": True,
    }

    assert_no_provider_candidate_queue_forbidden_markers(payload)


def test_financial_statement_raw_field_names_are_not_trading_marker_false_positives():
    payload = {"selected_metrics": {"sell_exp": 1, "revenue": 100}}

    assert_no_provider_candidate_queue_forbidden_markers(payload)


def test_result_validator_rejects_official_verified_key():
    queue = _valid_queue()
    queue["official_verified"] = True

    with pytest.raises(ProviderCandidateVerificationQueueError, match="forbidden_marker"):
        validate_provider_candidate_metric_verification_queue(queue)


def test_result_validator_rejects_official_metric_fact_and_conflict_markers():
    queue = _valid_queue()
    queue["verification_items"][0]["caveats"].append("official_metric_fact")

    with pytest.raises(ProviderCandidateVerificationQueueError, match="forbidden_marker"):
        validate_provider_candidate_metric_verification_queue(queue)

    queue = _valid_queue()
    queue["caveats"].append("provider_official_conflict")

    with pytest.raises(ProviderCandidateVerificationQueueError, match="forbidden_marker"):
        validate_provider_candidate_metric_verification_queue(queue)


@pytest.mark.parametrize(
    "field, marker",
    [
        ("ts_code", "official_metric_fact"),
        ("period_label", "target price"),
        ("company_name_hint", "目标价"),
    ],
)
def test_result_validator_rejects_forbidden_markers_in_item_identity_fields(field, marker):
    queue = _valid_queue()
    queue["verification_items"][0][field] = marker

    with pytest.raises(ProviderCandidateVerificationQueueError, match="forbidden_marker"):
        validate_provider_candidate_metric_verification_queue(queue)


def test_result_validator_rejects_missing_or_false_not_official_verified():
    queue = _valid_queue()
    missing = copy.deepcopy(queue)
    missing.pop("not_official_verified")
    false_value = copy.deepcopy(queue)
    false_value["not_official_verified"] = False

    with pytest.raises(ProviderCandidateVerificationQueueError, match="not_official_verified"):
        validate_provider_candidate_metric_verification_queue(missing)
    with pytest.raises(ProviderCandidateVerificationQueueError, match="not_official_verified"):
        validate_provider_candidate_metric_verification_queue(false_value)


@pytest.mark.parametrize("bad_value", [False, "true", 1, None])
def test_result_validator_rejects_missing_false_or_non_bool_trading_advice_flag(bad_value):
    queue = _valid_queue()
    queue["not_for_trading_advice"] = bad_value

    with pytest.raises(ProviderCandidateVerificationQueueError, match="not_for_trading_advice"):
        validate_provider_candidate_metric_verification_queue(queue)


def test_result_validator_rejects_item_candidate_flags_when_missing_or_false():
    queue = _valid_queue()
    queue["verification_items"][0]["not_official_verified"] = False

    with pytest.raises(ProviderCandidateVerificationQueueError, match="not_official_verified"):
        validate_provider_candidate_metric_verification_queue(queue)

    queue = _valid_queue()
    queue["verification_items"][0].pop("not_for_trading_advice")

    with pytest.raises(ProviderCandidateVerificationQueueError, match="not_for_trading_advice"):
        validate_provider_candidate_metric_verification_queue(queue)


def test_result_validator_rejects_official_verification_status_override():
    queue = _valid_queue()
    queue["verification_items"][0]["official_verification_status"] = "verified"

    with pytest.raises(ProviderCandidateVerificationQueueError, match="official_verification_status"):
        validate_provider_candidate_metric_verification_queue(queue)


def test_no_secret_value_appears_in_blocked_result_or_captured_output(capsys):
    secret_value = "HiddenCredentialValue9876543210ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    result = _minimal_provider_candidate_result(debug_payload=secret_value)
    result.pop("trend_table")

    queue = build_provider_candidate_metric_verification_queue(result)
    captured = capsys.readouterr()

    assert "missing_trend_table" in queue["blocked_reasons"]
    assert secret_value not in repr(queue)
    assert secret_value not in captured.out
    assert secret_value not in captured.err
    assert captured.out == ""
    assert captured.err == ""
