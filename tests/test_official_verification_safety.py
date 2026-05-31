# -*- coding: utf-8 -*-

import pytest

from src.fundamental_skill.data_verification.validators import (
    _FORBIDDEN_CJK_VALUE_MARKERS,
    _FORBIDDEN_EXACT_KEYS,
    OfficialVerificationValidationError,
    validate_official_metric_fact,
)


SHA = "d" * 64


def _fact(**overrides):
    fact = {
        "fact_id": "fact_600406_2024_revenue",
        "stock_code": "600406",
        "company_name": "Guodian NARI",
        "metric_id": "revenue",
        "metric_policy_id": "revenue.v1",
        "metric_type": "direct",
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
        "extraction_quality": "high",
        "verification_status": "verified",
        "official_confidence": "high",
        "conflict_refs": [],
        "caveats": [],
        "verifier": "unit-test",
        "reviewer": "",
        "not_for_trading_advice": True,
    }
    fact.update(overrides)
    return fact


@pytest.mark.parametrize(
    "marker",
    [
        "read tushare_token.txt",
        "read .env",
        "provider live call",
        "accepted manifest write",
        "output baseline write",
        "buy recommendation",
        "sell recommendation",
        "hold recommendation",
        "target price",
        "portfolio position",
        "technical signal",
        "trading signal",
        "buy signal",
        "sell signal",
        "hold signal",
        "network intent",
        "download pdf",
        "parse pdf",
        "report v1 trigger",
    ],
)
def test_forbidden_marker_values_rejected(marker):
    fact = _fact(caveats=[marker])

    with pytest.raises(OfficialVerificationValidationError, match="forbidden marker"):
        validate_official_metric_fact(fact)


@pytest.mark.parametrize(
    "marker",
    [
        "buy",
        "sell",
        "hold",
        "buying",
        "selling",
        "accumulate",
        "reduce",
        "overweight",
        "underweight",
        "target_price",
        "price_target",
        "portfolio",
        "portfolio_weight",
        "position",
        "position_size",
        "technical_signal",
        "trading_signal",
        "buy_signal",
        "sell_signal",
        "hold_signal",
        "买入",
        "卖出",
        "持有",
        "目标价",
        "仓位",
        "配置比例",
        "技术信号",
        "交易信号",
    ],
)
def test_bare_forbidden_marker_values_rejected(marker):
    fact = _fact(caveats=[marker])

    with pytest.raises(OfficialVerificationValidationError, match="forbidden marker"):
        validate_official_metric_fact(fact)


@pytest.mark.parametrize(
    "key",
    [
        "token_read",
        "provider_live_call",
        "accepted_manifest_write",
        "output_baseline_write",
        "target_price",
        "price_target",
        "position",
        "position_size",
        "portfolio",
        "portfolio_weight",
        "technical_signal",
        "trading_signal",
        "buy_signal",
        "sell_signal",
        "hold_signal",
        "buy_recommendation",
        "sell_recommendation",
        "hold_recommendation",
        "report_v1_trigger",
        "network_intent",
    ],
)
def test_forbidden_marker_keys_rejected(key):
    fact = _fact(**{key: True})

    with pytest.raises(OfficialVerificationValidationError, match="forbidden marker"):
        validate_official_metric_fact(fact)


def test_nested_forbidden_marker_value_rejected():
    fact = _fact(caveats=[{"nested": ["目标价"]}])

    with pytest.raises(OfficialVerificationValidationError, match="forbidden marker"):
        validate_official_metric_fact(fact)


def test_key_alias_with_spaces_rejected():
    fact = _fact(**{"technical signal": True})

    with pytest.raises(OfficialVerificationValidationError, match="forbidden marker"):
        validate_official_metric_fact(fact)


def test_forbidden_cjk_marker_inventory_is_utf8_clean():
    expected = {"买入", "卖出", "持有", "目标价", "仓位", "配置比例", "技术信号", "交易信号"}

    assert set(_FORBIDDEN_CJK_VALUE_MARKERS) == expected
    assert expected.issubset(_FORBIDDEN_EXACT_KEYS)
    assert all("�" not in marker for marker in _FORBIDDEN_CJK_VALUE_MARKERS)


@pytest.mark.parametrize(
    "payload",
    [
        {"目标价": "10元"},
        {"建议": "买入"},
        {"动作": "卖出"},
        {"观点": "持有"},
        {"仓位": "50%"},
        {"信号": "技术信号"},
        {"nested": [{"建议": "买入"}, {"动作": ["卖出", {"观点": "持有"}]}]},
    ],
)
def test_forbidden_cjk_marker_keys_and_values_rejected(payload):
    fact = _fact(caveats=[payload])

    with pytest.raises(OfficialVerificationValidationError, match="forbidden marker"):
        validate_official_metric_fact(fact)


@pytest.mark.parametrize(
    "key",
    [
        "targetPrice",
        "TargetPrice",
        "target-price",
        "priceTarget",
        "portfolioWeight",
        "positionSize",
        "technicalSignal",
        "tradingSignal",
        "buySignal",
        "sellSignal",
        "holdSignal",
    ],
)
def test_forbidden_marker_camel_pascal_and_kebab_keys_rejected(key):
    fact = _fact(**{key: True})

    with pytest.raises(OfficialVerificationValidationError, match="forbidden marker"):
        validate_official_metric_fact(fact)


@pytest.mark.parametrize(
    "marker",
    [
        "targetPrice",
        "TargetPrice",
        "target-price",
        "priceTarget",
        "portfolioWeight",
        "positionSize",
        "technicalSignal",
        "tradingSignal",
        "buySignal",
        "sellSignal",
        "holdSignal",
    ],
)
def test_forbidden_marker_camel_pascal_and_kebab_values_rejected(marker):
    fact = _fact(caveats=[{"nested": [marker]}])

    with pytest.raises(OfficialVerificationValidationError, match="forbidden marker"):
        validate_official_metric_fact(fact)


def test_nested_not_for_trading_advice_false_rejected():
    fact = _fact(caveats=[{"lineage_note": "manual anchor", "not_for_trading_advice": False}])

    with pytest.raises(OfficialVerificationValidationError, match="not_for_trading_advice"):
        validate_official_metric_fact(fact)


def test_harmless_nested_dict_without_not_for_trading_advice_passes():
    fact = _fact(caveats=[{"lineage_note": "manual anchor", "anchors": ["annual report table"]}])

    validate_official_metric_fact(fact)


@pytest.mark.parametrize("source_ref", ["akshare_income", "tushare_income", "mirror_page_1", "source_candidate_1"])
def test_verified_fact_with_non_official_source_ref_rejected(source_ref):
    fact = _fact(source_ref=source_ref)

    with pytest.raises(OfficialVerificationValidationError, match="source_ref"):
        validate_official_metric_fact(fact)


@pytest.mark.parametrize("source_type", ["provider_endpoint", "mirror_third_party_page"])
def test_verified_fact_with_non_official_source_type_rejected(source_type):
    fact = _fact(source_type=source_type)

    with pytest.raises(OfficialVerificationValidationError, match="source_type"):
        validate_official_metric_fact(fact)


def test_verified_fact_with_cninfo_official_source_type_accepted():
    fact = _fact(official_source_type="cninfo_official_pdf")

    validate_official_metric_fact(fact)


def test_verified_fact_missing_official_lineage_rejected():
    fact = _fact(source_ref="")

    with pytest.raises(OfficialVerificationValidationError, match="source_ref"):
        validate_official_metric_fact(fact)


def test_valid_fact_without_forbidden_intents_passes():
    validate_official_metric_fact(_fact())
