# -*- coding: utf-8 -*-

import inspect

import pytest

from src.fundamental_skill.data_providers.schemas import CANONICAL_RAW_BLOCKS, raw_has_canonical_shape
from src.fundamental_skill.data_providers.tushare_client import (
    TushareClient,
    TusharePermissionError,
    TushareRateLimitError,
)
from src.fundamental_skill.data_providers.tushare_provider import (
    TUSHARE_PROVIDER_VERSION,
    TushareProvider,
    TushareProviderError,
)


def _transport(**overrides):
    base = {
        "stock_basic": [
            {
                "stock_code": "002050",
                "stock_name": "Mock Sanhua",
                "industry": "mock manufacturing",
                "listing_date": "2005-06-07",
            }
        ],
        "income": [
            {
                "period": "20251231",
                "revenue": 1000,
                "net_profit": 120,
                "deducted_net_profit": 110,
                "r_and_d_expense": 40,
            }
        ],
        "balancesheet": [
            {
                "period": "20251231",
                "debt_to_asset": 35.5,
                "inventory": 210,
                "accounts_receivable": 180,
                "contract_liabilities": 60,
            }
        ],
        "cashflow": [
            {
                "period": "20251231",
                "operating_cashflow": 160,
                "capex": 70,
            }
        ],
        "fina_indicator": [
            {
                "period": "20251231",
                "revenue_yoy": 12.5,
                "net_profit_yoy": 15.0,
                "gross_margin": 30.0,
                "net_margin": 12.0,
                "roe": 18.0,
                "r_and_d_expense_ratio": 4.0,
            }
        ],
        "daily_basic": [
            {
                "period": "20260526",
                "pe_ttm": 20.0,
                "pb": 3.0,
                "ps": 2.5,
                "market_cap": 3000,
                "dividend_yield": 1.2,
            }
        ],
        "fina_mainbz": [
            {
                "period": "20251231",
                "classification_type": "product",
                "segment_name": "thermal management",
                "revenue": 800,
                "revenue_ratio": 80,
                "gross_margin": 32,
                "cost": 544,
                "profit": 256,
                "profit_ratio": 85,
            }
        ],
    }
    base.update(overrides)
    return base


def _provider(transport=None, *, token="fake-token-for-tests-provider"):
    client = TushareClient(transport=transport or _transport(), token=token)
    return TushareProvider(client=client, token=token)


def test_tushare_provider_returns_canonical_raw_shape_and_capabilities():
    provider = _provider()
    raw = provider.fetch_to_raw_json("sz002050")
    capabilities = provider.capabilities()

    assert raw_has_canonical_shape(raw)
    assert raw["meta"]["code"] == "002050"
    assert raw["meta"]["data_source"] == "tushare"
    assert raw["meta"]["connector_version"] == TUSHARE_PROVIDER_VERSION
    assert set(CANONICAL_RAW_BLOCKS) == set(raw["blocks"])
    assert "financial_metrics" not in raw["blocks"]
    assert "valuation_metrics" not in raw["blocks"]
    assert capabilities.provider_name == "tushare"
    assert capabilities.news is False
    assert capabilities.commodity_prices is False
    assert capabilities.realtime_market_data is False


def test_tushare_provider_maps_basic_info_with_main_business_missing_until_verified():
    raw = _provider().fetch_to_raw_json("002050")

    basic = raw["blocks"]["basic_info"][0]

    assert basic["stock_code"] == "002050"
    assert basic["stock_name"] == "Mock Sanhua"
    assert basic["industry"] == "mock manufacturing"
    assert basic["listing_date"] == "2005-06-07"
    assert basic["main_business"] is None
    assert raw["fetch_status"]["basic_info"]["success"] is True
    assert "main_business" in raw["fetch_status"]["basic_info"]["missing_fields"]


def test_tushare_provider_maps_financial_indicator_from_mocked_statement_blocks():
    raw = _provider().fetch_to_raw_json("002050")

    metric = raw["blocks"]["financial_indicator"][0]

    assert metric["period"] == "20251231"
    assert metric["revenue"] == 1000.0
    assert metric["net_profit"] == 120.0
    assert metric["deducted_net_profit"] == 110.0
    assert metric["r_and_d_expense"] == 40.0
    assert metric["debt_to_asset"] == 35.5
    assert metric["inventory"] == 210.0
    assert metric["accounts_receivable"] == 180.0
    assert metric["contract_liabilities"] == 60.0
    assert metric["operating_cashflow"] == 160.0
    assert metric["capex"] == 70.0
    assert metric["revenue_yoy"] == 12.5
    assert metric["net_profit_yoy"] == 15.0
    assert metric["gross_margin"] == 30.0
    assert metric["net_margin"] == 12.0
    assert metric["roe"] == 18.0
    assert metric["r_and_d_expense_ratio"] == 4.0


def test_tushare_provider_maps_valuation_and_business_composition():
    raw = _provider().fetch_to_raw_json("002050")

    valuation = raw["blocks"]["valuation"][0]
    segment = raw["blocks"]["business_composition"][0]

    assert valuation == {
        "period": "20260526",
        "pe_ttm": 20.0,
        "pb": 3.0,
        "ps": 2.5,
        "market_cap": 3000.0,
        "dividend_yield": 1.2,
    }
    assert segment["period"] == "20251231"
    assert segment["classification_type"] == "product"
    assert segment["segment_name"] == "thermal management"
    assert segment["revenue"] == 800.0
    assert segment["revenue_ratio"] == 80.0
    assert segment["gross_margin"] == 32.0
    assert segment["cost"] == 544.0
    assert segment["profit"] == 256.0
    assert segment["profit_ratio"] == 85.0


def test_tushare_provider_marks_news_missing_and_fallback_without_replacement_claim():
    raw = _provider().fetch_to_raw_json("002050")

    assert raw["blocks"]["news"] == []
    assert raw["fetch_status"]["news"]["success"] is False
    assert raw["fetch_status"]["news"]["error"] == "news_missing_fallback"
    assert raw["fetch_status"]["news"]["missing_fields"] == ["title", "publish_time", "source", "url", "summary"]
    assert any("does not replace news" in warning for warning in raw["fetch_status"]["news"]["warnings"])


def test_tushare_provider_records_field_missing_without_turning_it_into_fact():
    raw = _provider(_transport(daily_basic=[{"period": "20260526", "pe_ttm": 20.0}])).fetch_to_raw_json("002050")

    valuation = raw["blocks"]["valuation"][0]

    assert valuation["pe_ttm"] == 20.0
    assert valuation["pb"] is None
    assert "pb" in raw["fetch_status"]["valuation"]["missing_fields"]
    assert "market_cap" in raw["fetch_status"]["valuation"]["missing_fields"]
    assert raw["fetch_status"]["valuation"]["success"] is True


def test_tushare_provider_records_permission_denied_with_sanitized_error():
    secret = "fake-token-for-tests-permission"
    raw = _provider(
        _transport(stock_basic=TusharePermissionError(f"token={secret} permission denied")),
        token=secret,
    ).fetch_to_raw_json("002050")

    status = raw["fetch_status"]["basic_info"]

    assert raw["blocks"]["basic_info"] == []
    assert status["success"] is False
    assert "permission_denied" in status["error"]
    assert secret not in status["error"]
    assert secret not in repr(raw)


def test_tushare_provider_records_empty_business_composition():
    raw = _provider(_transport(fina_mainbz=[])).fetch_to_raw_json("002050")

    assert raw["blocks"]["business_composition"] == []
    assert raw["fetch_status"]["business_composition"]["success"] is False
    assert raw["fetch_status"]["business_composition"]["error"] == "empty_response"
    assert raw["fetch_status"]["business_composition"]["missing_fields"] == ["business_composition.segments"]


def test_tushare_provider_records_malformed_response():
    raw = _provider(_transport(daily_basic="not a tabular mocked response")).fetch_to_raw_json("002050")

    status = raw["fetch_status"]["valuation"]

    assert raw["blocks"]["valuation"] == []
    assert status["success"] is False
    assert "malformed_response" in status["error"]
    assert "pe_ttm" in status["missing_fields"]


def test_tushare_provider_records_rate_limit_with_sanitized_error():
    secret = "fake-token-for-tests-rate-limit"
    raw = _provider(
        _transport(daily_basic=TushareRateLimitError(f"{'TUSHARE_' + 'TOKEN'}={secret} rate limit")),
        token=secret,
    ).fetch_to_raw_json("002050")

    status = raw["fetch_status"]["valuation"]

    assert status["success"] is False
    assert "rate_limit" in status["error"]
    assert secret not in status["error"]
    assert secret not in repr(raw)


def test_tushare_provider_no_token_fails_closed_before_fetch():
    provider = TushareProvider(client=TushareClient(transport=_transport()))

    with pytest.raises(TushareProviderError) as exc_info:
        provider.fetch_to_raw_json("002050")

    assert "requires an available Tushare token" in str(exc_info.value)


def test_tushare_provider_masks_token_in_repr_and_provider_errors():
    secret = "fake-token-for-tests-provider-repr"
    provider = TushareProvider(token=secret)

    with pytest.raises(TushareProviderError) as exc_info:
        provider.fetch_to_raw_json("002050")

    assert secret not in repr(provider)
    assert "<masked>" in repr(provider)
    assert secret not in str(exc_info.value)


def test_tushare_provider_source_traces_are_non_secret_and_field_based():
    raw = _provider().fetch_to_raw_json("002050")
    traces = raw["fetch_status"]["financial_indicator"]["source_trace"]

    assert traces
    assert {trace["block_name"] for trace in traces} == {"financial_indicator"}
    assert "revenue" in {trace["field_name"] for trace in traces}
    assert all("token" not in repr(trace).lower() for trace in traces)


def test_tushare_provider_module_has_no_real_provider_or_external_io_imports():
    import src.fundamental_skill.data_providers.tushare_provider as module

    source = inspect.getsource(module)

    forbidden = (
        "import " + "tushare",
        "req" + "uests",
        "ht" + "tpx",
        "url" + "lib",
        "api." + "tushare" + ".pro",
        "m" + "cp",
    )
    for marker in forbidden:
        assert marker not in source.lower()
