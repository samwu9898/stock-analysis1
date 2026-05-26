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
    normalize_ts_code,
)


def _assert_secret_not_rendered(secret: str, text: str) -> None:
    if secret in text:
        raise AssertionError("secret-like value was rendered")


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
                "grossprofit_margin": 30.0,
                "netprofit_margin": 12.0,
                "roe": 18.0,
                "rd_exp_ratio": 4.0,
            }
        ],
        "daily_basic": [
            {
                "period": "20260526",
                "pe_ttm": 20.0,
                "pb": 3.0,
                "ps": 2.5,
                "total_mv": 3000,
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


class _RecordingTransport:
    def __init__(self, **overrides):
        self.responses = _transport(**overrides)
        self.calls = []

    def call(self, endpoint, **params):
        self.calls.append({"endpoint": endpoint, "params": params})
        response = self.responses.get(endpoint, [])
        if isinstance(response, BaseException):
            raise response
        return response


def _provider(transport=None, *, token="FAKE_TOKEN_FOR_TESTING_ONLY__NOT_REAL__XYZ_1234567890"):
    client = TushareClient(transport=transport or _transport(), token=token)
    return TushareProvider(client=client, token=token)


def _field_traces(raw, block_name, field_name):
    return [
        trace
        for trace in raw["fetch_status"][block_name]["source_trace"]
        if trace.get("field_name") == field_name
    ]


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("600406", "600406.SH"),
        ("603259", "603259.SH"),
        ("002050", "002050.SZ"),
        ("002371", "002371.SZ"),
        ("000426", "000426.SZ"),
        ("002837", "002837.SZ"),
        ("900001", "900001.BJ"),
    ],
)
def test_normalize_ts_code_maps_supported_a_share_prefixes(code, expected):
    assert normalize_ts_code(code) == expected


@pytest.mark.parametrize("code", ["sz002050", "12345", "700000", "abc002050", " 002050"])
def test_normalize_ts_code_fails_closed_for_non_strict_or_unknown_codes(code):
    with pytest.raises(TushareProviderError) as exc_info:
        normalize_ts_code(code)

    message = str(exc_info.value).lower()
    assert "stock_code" in message
    assert "token" not in message
    assert "http" not in message


def test_tushare_provider_returns_canonical_raw_shape_and_capabilities():
    provider = _provider()
    raw = provider.fetch_to_raw_json("002050")
    capabilities = provider.capabilities()

    assert raw_has_canonical_shape(raw)
    assert raw["meta"]["code"] == "002050"
    assert raw["meta"]["ts_code"] == "002050.SZ"
    assert raw["meta"]["data_source"] == "tushare"
    assert raw["meta"]["connector_version"] == TUSHARE_PROVIDER_VERSION
    assert set(CANONICAL_RAW_BLOCKS) == set(raw["blocks"])
    assert "financial_metrics" not in raw["blocks"]
    assert "valuation_metrics" not in raw["blocks"]
    assert capabilities.provider_name == "tushare"
    assert capabilities.news is False
    assert capabilities.commodity_prices is False
    assert capabilities.realtime_market_data is False


def test_tushare_provider_fails_closed_for_invalid_code_before_transport_call():
    transport = _RecordingTransport()
    provider = TushareProvider(client=TushareClient(transport=transport), token_available=True)

    with pytest.raises(TushareProviderError):
        provider.fetch_to_raw_json("sz002050")

    assert transport.calls == []


def test_tushare_provider_passes_normalized_ts_code_to_all_sdk_endpoints_and_keeps_canonical_code():
    transport = _RecordingTransport(
        stock_basic=[
            {
                "ts_code": "002837.SZ",
                "name": "Mock Envicool",
                "industry": "mock datacenter thermal",
                "list_date": "2016-12-29",
            }
        ]
    )
    provider = TushareProvider(client=TushareClient(transport=transport), token_available=True)

    raw = provider.fetch_to_raw_json("002837")

    expected_endpoints = [
        "stock_basic",
        "income",
        "balancesheet",
        "cashflow",
        "fina_indicator",
        "daily_basic",
        "fina_mainbz",
    ]
    assert [call["endpoint"] for call in transport.calls] == expected_endpoints
    assert all(call["params"] == {"ts_code": "002837.SZ"} for call in transport.calls)
    assert raw["meta"]["code"] == "002837"
    assert raw["meta"]["ts_code"] == "002837.SZ"
    assert raw["blocks"]["basic_info"][0]["stock_code"] == "002837"

    statuses = raw["fetch_status"]
    assert all(statuses[block]["ts_code"] == "002837.SZ" for block in CANONICAL_RAW_BLOCKS)
    endpoint_traces = [
        trace
        for status in statuses.values()
        for trace in status["source_trace"]
        if trace["field_name"] == "__endpoint_call__"
    ]
    assert [trace["endpoint"] for trace in endpoint_traces] == expected_endpoints
    assert {trace["ts_code"] for trace in endpoint_traces} == {"002837.SZ"}
    assert all(trace["request_period"] == "omitted" for trace in endpoint_traces)
    assert all(trace["request_start_date"] == "omitted" for trace in endpoint_traces)
    assert all(trace["request_end_date"] == "omitted" for trace in endpoint_traces)
    assert all(trace["request_trade_date"] == "omitted" for trace in endpoint_traces)
    assert any(trace["selected_row_period"] == "20251231" for trace in endpoint_traces)


def test_tushare_provider_source_trace_records_normalized_ts_code_without_sensitive_metadata():
    secret = "FAKE_TOKEN_FOR_TESTING_ONLY__NOT_REAL__XYZ_1234567890"
    local_tool_url = "http://127.0.0.1:9999/local-tool"
    provider = _provider(token=secret)
    raw = provider.fetch_to_raw_json("002050")

    trace_text = repr(raw["fetch_status"])

    assert raw["fetch_status"]["valuation"]["endpoints"] == ["daily_basic"]
    assert raw["fetch_status"]["valuation"]["row_count"] == 1
    assert "002050.SZ" in trace_text
    _assert_secret_not_rendered(secret, trace_text)
    assert local_tool_url not in trace_text


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
        "market_cap": 30000000.0,
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


def test_tushare_provider_gross_margin_prefers_margin_percentage_over_gross_profit_amount():
    raw = _provider(
        _transport(
            fina_indicator=[
                {
                    "period": "20251231",
                    "gross_margin": 700.0,
                    "grossprofit_margin": 31.5,
                    "netprofit_margin": 12.0,
                }
            ]
        )
    ).fetch_to_raw_json("002050")

    metric = raw["blocks"]["financial_indicator"][0]
    trace = _field_traces(raw, "financial_indicator", "gross_margin")[0]

    assert metric["gross_margin"] == 31.5
    assert trace["source_field"] == "grossprofit_margin"
    assert trace["derived"] is False


def test_tushare_provider_gross_margin_derives_from_revenue_and_cost_with_trace():
    raw = _provider(
        _transport(
            income=[{"period": "20251231", "revenue": 1000, "oper_cost": 650, "net_profit": 120}],
            fina_indicator=[{"period": "20251231", "gross_margin": 650000000.0}],
        )
    ).fetch_to_raw_json("002050")

    metric = raw["blocks"]["financial_indicator"][0]
    trace = _field_traces(raw, "financial_indicator", "gross_margin")[0]

    assert metric["gross_margin"] == 35.0
    assert trace["derived"] is True
    assert trace["derivation_method"] == "(revenue - cost) / revenue * 100"
    assert trace["source_fields"] == ["income.revenue", "income.oper_cost"]


def test_tushare_provider_net_margin_derives_from_net_profit_and_revenue_with_trace():
    raw = _provider(
        _transport(
            income=[{"period": "20251231", "revenue": 1000, "net_profit": 125}],
            fina_indicator=[{"period": "20251231"}],
        )
    ).fetch_to_raw_json("002050")

    metric = raw["blocks"]["financial_indicator"][0]
    trace = _field_traces(raw, "financial_indicator", "net_margin")[0]

    assert metric["net_margin"] == 12.5
    assert trace["derived"] is True
    assert trace["derivation_method"] == "net_profit / revenue * 100"


def test_tushare_provider_debt_to_asset_derives_from_balance_totals_with_trace():
    raw = _provider(
        _transport(
            balancesheet=[
                {
                    "period": "20251231",
                    "total_liab": 400,
                    "total_assets": 1000,
                    "inventory": 210,
                }
            ]
        )
    ).fetch_to_raw_json("002050")

    metric = raw["blocks"]["financial_indicator"][0]
    trace = _field_traces(raw, "financial_indicator", "debt_to_asset")[0]

    assert metric["debt_to_asset"] == 40.0
    assert trace["derived"] is True
    assert trace["derivation_method"] == "total_liab / total_assets * 100"


def test_tushare_provider_r_and_d_expense_ratio_derives_from_expense_and_revenue_with_trace():
    raw = _provider(
        _transport(
            income=[{"period": "20251231", "revenue": 1000, "net_profit": 120, "rd_exp": 45}],
            fina_indicator=[{"period": "20251231"}],
        )
    ).fetch_to_raw_json("002050")

    metric = raw["blocks"]["financial_indicator"][0]
    trace = _field_traces(raw, "financial_indicator", "r_and_d_expense_ratio")[0]

    assert metric["r_and_d_expense_ratio"] == 4.5
    assert trace["derived"] is True
    assert trace["derivation_method"] == "r_and_d_expense / revenue * 100"


def test_tushare_provider_market_cap_converts_total_mv_10k_rmb_to_rmb_without_converting_ratios():
    raw = _provider(
        _transport(
            daily_basic=[
                {
                    "period": "20260526",
                    "pe_ttm": 10.0,
                    "pb": 2.0,
                    "ps_ttm": 3.5,
                    "ps": 4.0,
                    "total_mv": 123.45,
                }
            ]
        )
    ).fetch_to_raw_json("002050")

    valuation = raw["blocks"]["valuation"][0]
    trace = _field_traces(raw, "valuation", "market_cap")[0]

    assert valuation["market_cap"] == 1234500.0
    assert valuation["pe_ttm"] == 10.0
    assert valuation["pb"] == 2.0
    assert valuation["ps"] == 3.5
    assert trace["source_field"] == "total_mv"
    assert trace["source_unit"] == "10k RMB"
    assert trace["canonical_unit"] == "RMB"
    assert trace["multiplier"] == 10000


def test_tushare_provider_business_composition_derives_group_ratios_and_gross_margin():
    raw = _provider(
        _transport(
            fina_mainbz=[
                {
                    "period": "20251231",
                    "type": "P",
                    "bz_item": "segment A",
                    "bz_sales": 300,
                    "bz_cost": 180,
                    "bz_profit": 120,
                },
                {
                    "period": "20251231",
                    "type": "P",
                    "bz_item": "segment B",
                    "bz_sales": 700,
                    "bz_cost": 560,
                    "bz_profit": 140,
                },
                {
                    "period": "20251231",
                    "type": "D",
                    "bz_item": "region C",
                    "bz_sales": 50,
                    "bz_cost": 40,
                    "bz_profit": 10,
                },
            ]
        )
    ).fetch_to_raw_json("002050")

    first, second, third = raw["blocks"]["business_composition"]
    revenue_ratio_trace = _field_traces(raw, "business_composition", "revenue_ratio")[0]
    profit_ratio_trace = _field_traces(raw, "business_composition", "profit_ratio")[0]
    gross_margin_trace = _field_traces(raw, "business_composition", "gross_margin")[0]

    assert first["classification_type"] == "product"
    assert second["classification_type"] == "product"
    assert third["classification_type"] == "region"
    assert first["revenue_ratio"] == 30.0
    assert second["revenue_ratio"] == 70.0
    assert first["profit_ratio"] == pytest.approx(46.1538461538)
    assert second["profit_ratio"] == pytest.approx(53.8461538462)
    assert first["gross_margin"] == 40.0
    assert second["gross_margin"] == 20.0
    assert revenue_ratio_trace["derived"] is True
    assert revenue_ratio_trace["denominator_scope"] == "period=20251231;classification_type=product;denominator=sum(revenue)"
    assert profit_ratio_trace["derived"] is True
    assert gross_margin_trace["derived"] is True
    assert gross_margin_trace["derivation_method"] == "profit / revenue * 100"


def test_tushare_provider_business_classification_missing_keeps_group_ratios_missing_but_derives_segment_margin():
    raw = _provider(
        _transport(
            fina_mainbz=[
                {
                    "period": "20251231",
                    "bz_item": "untyped segment",
                    "bz_sales": 300,
                    "bz_cost": 180,
                    "bz_profit": 120,
                },
                {
                    "period": "20251231",
                    "bz_item": "another untyped segment",
                    "bz_sales": 700,
                    "bz_cost": 560,
                    "bz_profit": 140,
                },
            ]
        )
    ).fetch_to_raw_json("002050")

    first = raw["blocks"]["business_composition"][0]

    assert first["classification_type"] is None
    assert first["revenue_ratio"] is None
    assert first["profit_ratio"] is None
    assert first["gross_margin"] == 40.0
    assert "classification_type" in raw["fetch_status"]["business_composition"]["missing_fields"]
    assert "revenue_ratio" in raw["fetch_status"]["business_composition"]["missing_fields"]
    assert "profit_ratio" in raw["fetch_status"]["business_composition"]["missing_fields"]


def test_tushare_provider_source_trace_contains_derived_and_conversion_metadata_without_sensitive_urls():
    secret = "FAKE_TOKEN_FOR_TESTING_ONLY__NOT_REAL__XYZ_1234567890"
    raw = _provider(
        _transport(
            income=[{"period": "20251231", "revenue": 1000, "oper_cost": 650, "net_profit": 120}],
            fina_indicator=[{"period": "20251231"}],
            daily_basic=[{"period": "20260526", "total_mv": 10, "pe_ttm": 1, "pb": 2, "ps": 3}],
        ),
        token=secret,
    ).fetch_to_raw_json("002050")

    trace_text = repr(raw["fetch_status"])

    assert _field_traces(raw, "financial_indicator", "gross_margin")[0]["derived"] is True
    assert _field_traces(raw, "valuation", "market_cap")[0]["source_unit"] == "10k RMB"
    _assert_secret_not_rendered(secret, trace_text)
    assert "mcp" not in trace_text.lower()
    assert "http://127.0.0.1" not in trace_text


def test_tushare_provider_does_not_generate_provider_comparison_output_or_require_real_token(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    transport = _RecordingTransport()
    provider = TushareProvider(client=TushareClient(transport=transport), token_available=True)

    raw = provider.fetch_to_raw_json("002050")

    assert raw["meta"]["data_source"] == "tushare"
    assert transport.calls
    assert not (tmp_path / "output" / "provider_comparison").exists()


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
    secret = "FAKE_TOKEN_FOR_TESTING_ONLY__NOT_REAL__XYZ_1234567890"
    raw = _provider(
        _transport(stock_basic=TusharePermissionError(f"token={secret} permission denied")),
        token=secret,
    ).fetch_to_raw_json("002050")

    status = raw["fetch_status"]["basic_info"]

    assert raw["blocks"]["basic_info"] == []
    assert status["success"] is False
    assert "permission_denied" in status["error"]
    _assert_secret_not_rendered(secret, status["error"])
    _assert_secret_not_rendered(secret, repr(raw))


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
    secret = "FAKE_TOKEN_FOR_TESTING_ONLY__NOT_REAL__XYZ_1234567890"
    raw = _provider(
        _transport(daily_basic=TushareRateLimitError(f"{'TUSHARE_' + 'TOKEN'}={secret} rate limit")),
        token=secret,
    ).fetch_to_raw_json("002050")

    status = raw["fetch_status"]["valuation"]

    assert status["success"] is False
    assert "rate_limit" in status["error"]
    _assert_secret_not_rendered(secret, status["error"])
    _assert_secret_not_rendered(secret, repr(raw))


def test_tushare_provider_no_token_fails_closed_before_fetch():
    provider = TushareProvider(client=TushareClient(transport=_transport()))

    with pytest.raises(TushareProviderError) as exc_info:
        provider.fetch_to_raw_json("002050")

    assert "requires an available Tushare token" in str(exc_info.value)


def test_tushare_provider_masks_token_in_repr_and_provider_errors():
    secret = "FAKE_TOKEN_FOR_TESTING_ONLY__NOT_REAL__XYZ_1234567890"
    provider = TushareProvider(token=secret)

    with pytest.raises(TushareProviderError) as exc_info:
        provider.fetch_to_raw_json("002050")

    _assert_secret_not_rendered(secret, repr(provider))
    assert "<masked>" in repr(provider)
    _assert_secret_not_rendered(secret, str(exc_info.value))


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
        "tushare" + "_token",
        "en" + "viron",
        "get" + "env",
        "provider" + "_comparison",
    )
    for marker in forbidden:
        assert marker not in source.lower()
