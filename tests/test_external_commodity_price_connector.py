# -*- coding: utf-8 -*-

from __future__ import annotations

import json
from datetime import date

import pandas as pd

from src.fundamental_skill.classification_schema import FundamentalFramework, StockClassificationResult
from src.fundamental_skill.data_adapter import FundamentalDataAdapter
from src.fundamental_skill.data_readiness_planner import DataReadinessPlanner
from src.fundamental_skill.external_commodity_price_connector import ExternalCommodityPriceConnector


class FakeCommodityAkshare:
    def __init__(self, mode: str = "primary") -> None:
        self.mode = mode
        self.requested_vars: list[str] = []

    def futures_spot_price(self, vars_list=None):
        self.requested_vars.extend(vars_list or [])
        if self.mode in {"sge", "foreign_only"}:
            return pd.DataFrame()
        dt = "2026-05-01" if self.mode in {"daily_fallback", "all_stale", "realtime", "daily_v11", "main_v11"} else "2026-05-18"
        return pd.DataFrame(
            [
                {
                    "symbol": symbol,
                    "date": dt,
                    "spot_price": 100.0 + len(symbol),
                    "near_contract": f"{symbol}2606",
                    "near_contract_price": 101.0,
                    "dominant_contract": f"{symbol}2607",
                    "dominant_contract_price": 102.0,
                    "near_basis": 1.0,
                    "dominant_basis": 2.0,
                }
                for symbol in vars_list or ["CU"]
            ]
        )

    def futures_spot_price_daily(self, vars_list=None):
        if self.mode in {"realtime", "daily_v11", "main_v11"}:
            return pd.DataFrame(
                [{"symbol": symbol, "date": "2021-02-01", "spot_price": 300.0 + len(symbol)} for symbol in vars_list or ["CU"]]
            )
        if self.mode == "daily_fallback":
            return pd.DataFrame(
                [
                    {
                        "symbol": symbol,
                        "date": "2026-05-18",
                        "spot_price": 200.0 + len(symbol),
                        "near_contract": f"{symbol}2608",
                        "near_contract_price": 201.0,
                        "dominant_contract": f"{symbol}2609",
                        "dominant_contract_price": 202.0,
                    }
                    for symbol in vars_list or ["CU"]
                ]
            )
        if self.mode == "all_stale":
            return pd.DataFrame(
                [{"symbol": symbol, "date": "2026-05-02", "spot_price": 300.0 + len(symbol)} for symbol in vars_list or ["CU"]]
            )
        return pd.DataFrame()

    def futures_zh_realtime(self, symbol=None):
        if self.mode != "realtime":
            return pd.DataFrame()
        data = {
            "沪铜": {"symbol": "CU0", "name": "沪铜", "trade": 81000.0},
            "沪锡": {"symbol": "SN0", "name": "沪锡", "trade": 260000.0},
        }
        row = data.get(symbol)
        if not row:
            return pd.DataFrame()
        return pd.DataFrame(
            [
                {
                    **row,
                    "tradedate": "2026-05-18",
                    "ticktime": "14:59:00",
                    "settlement": row["trade"] - 10.0,
                    "presettlement": row["trade"] - 20.0,
                    "open": row["trade"] - 100.0,
                    "high": row["trade"] + 100.0,
                    "low": row["trade"] - 200.0,
                }
            ]
        )

    def futures_zh_daily_sina(self, symbol=None):
        if self.mode != "daily_v11":
            return pd.DataFrame()
        if symbol == "CU0":
            return pd.DataFrame([{"date": "2026-05-18", "open": 80000.0, "high": 82100.0, "low": 79900.0, "close": 82000.0, "volume": 1, "hold": 2}])
        if symbol == "SN0":
            return pd.DataFrame([{"date": "2026-05-18", "open": 250000.0, "high": 261000.0, "low": 249000.0, "close": 260000.0, "volume": 3, "hold": 4}])
        return pd.DataFrame()

    def futures_main_sina(self, symbol=None):
        if self.mode != "main_v11":
            return pd.DataFrame()
        if symbol == "SN0":
            return pd.DataFrame([{"日期": "2026-05-18", "开盘价": 250000.0, "最高价": 261000.0, "最低价": 249000.0, "收盘价": 260500.0, "成交量": 3, "持仓量": 4}])
        if symbol == "CU0":
            return pd.DataFrame([{"日期": "2026-05-18", "开盘价": 80000.0, "最高价": 82100.0, "最低价": 79900.0, "收盘价": 82050.0, "成交量": 1, "持仓量": 2}])
        return pd.DataFrame()

    def spot_silver_benchmark_sge(self):
        if self.mode not in {"sge", "all_stale"}:
            return pd.DataFrame()
        dt = "2026-05-01" if self.mode == "all_stale" else "2026-05-18"
        return pd.DataFrame([{"交易时间": dt, "晚盘价": 888.0, "早盘价": 880.0}])

    def spot_golden_benchmark_sge(self):
        if self.mode not in {"sge", "all_stale"}:
            return pd.DataFrame()
        dt = "2026-05-01" if self.mode == "all_stale" else "2026-05-18"
        return pd.DataFrame([{"交易时间": dt, "晚盘价": 777.0, "早盘价": 770.0}])

    def futures_foreign_commodity_realtime(self, vars_list=None):
        if self.mode == "foreign_only":
            return pd.DataFrame([{"symbol": "CAD", "price": 9000.0, "date": "2026-05-18"}])
        return pd.DataFrame()


def connector(mode: str = "primary") -> ExternalCommodityPriceConnector:
    return ExternalCommodityPriceConnector(
        akshare_client=FakeCommodityAkshare(mode=mode),
        as_of_date=date(2026, 5, 18),
    )


def test_000426_requests_silver_and_tin():
    ak = FakeCommodityAkshare()
    result = ExternalCommodityPriceConnector(akshare_client=ak, as_of_date=date(2026, 5, 18)).fetch_for_stock("000426")

    assert set(ak.requested_vars) >= {"AG", "SN"}
    assert {item["commodity_name"] for item in result["commodities"]} == {"silver", "tin"}


def test_601899_requests_copper_and_gold():
    ak = FakeCommodityAkshare()
    result = ExternalCommodityPriceConnector(akshare_client=ak, as_of_date=date(2026, 5, 18)).fetch_for_stock("601899")

    assert set(ak.requested_vars) >= {"CU", "AU"}
    assert {item["commodity_name"] for item in result["commodities"]} == {"copper", "gold"}


def test_603993_keeps_cobalt_and_molybdenum_missing():
    result = connector().fetch_for_stock("603993")

    assert {item["commodity_name"] for item in result["commodities"]} == {"copper"}
    assert set(result["missing_commodities"]) == {"cobalt", "molybdenum"}


def test_futures_spot_price_fresh_uses_primary():
    result = connector().fetch_for_stock("601899")
    copper = next(item for item in result["commodities"] if item["commodity_name"] == "copper")

    assert copper["price"] == 102.0
    assert copper["date"] == "2026-05-18"
    assert copper["near_contract"] == "CU2606"
    assert copper["dominant_contract"] == "CU2607"
    assert copper["source_priority"] == "primary"
    assert copper["readiness_eligible"] is True


def test_stale_primary_uses_daily_fallback_when_fresh():
    result = connector("daily_fallback").fetch_for_stock("601899")
    copper = next(item for item in result["commodities"] if item["commodity_name"] == "copper")

    assert copper["price"] == 202.0
    assert copper["source_priority"] == "domestic_daily_fallback"
    assert copper["readiness_eligible"] is True
    assert "used_daily_fallback" in copper["warnings"]


def test_silver_primary_stale_daily_failed_uses_sge_fallback():
    result = connector("sge").fetch_for_stock("000426")
    silver = next(item for item in result["commodities"] if item["commodity_name"] == "silver")

    assert silver["price"] == 888.0
    assert silver["market"] == "SGE"
    assert silver["source_priority"] == "sge_fallback"
    assert silver["readiness_eligible"] is True


def test_gold_primary_stale_daily_failed_uses_sge_fallback():
    result = connector("sge").fetch_for_stock("601899")
    gold = next(item for item in result["commodities"] if item["commodity_name"] == "gold")

    assert gold["price"] == 777.0
    assert gold["source_priority"] == "sge_fallback"
    assert gold["readiness_eligible"] is True


def test_copper_futures_zh_realtime_fresh_uses_domestic_realtime_primary():
    result = connector("realtime").fetch_for_stock("601899")
    copper = next(item for item in result["commodities"] if item["commodity_name"] == "copper")

    assert copper["symbol"] == "沪铜"
    assert copper["price"] == 81000.0
    assert copper["settlement"] == 80990.0
    assert copper["presettlement"] == 80980.0
    assert copper["source_function"] == "futures_zh_realtime"
    assert copper["source_priority"] == "domestic_realtime_primary"
    assert copper["readiness_eligible"] is True


def test_tin_futures_zh_realtime_fresh_uses_domestic_realtime_primary():
    result = connector("realtime").fetch_for_stock("000426")
    tin = next(item for item in result["commodities"] if item["commodity_name"] == "tin")

    assert tin["symbol"] == "沪锡"
    assert tin["price"] == 260000.0
    assert tin["source_function"] == "futures_zh_realtime"
    assert tin["source_priority"] == "domestic_realtime_primary"
    assert tin["readiness_eligible"] is True


def test_copper_realtime_failed_uses_zh_daily_sina_fallback():
    result = connector("daily_v11").fetch_for_stock("601899")
    copper = next(item for item in result["commodities"] if item["commodity_name"] == "copper")

    assert copper["symbol"] == "CU0"
    assert copper["price"] == 82000.0
    assert copper["close"] == 82000.0
    assert copper["source_function"] == "futures_zh_daily_sina"
    assert copper["source_priority"] == "domestic_daily_fallback"
    assert copper["readiness_eligible"] is True


def test_tin_realtime_failed_uses_main_sina_fallback():
    result = connector("main_v11").fetch_for_stock("000426")
    tin = next(item for item in result["commodities"] if item["commodity_name"] == "tin")

    assert tin["symbol"] == "SN0"
    assert tin["price"] == 260500.0
    assert tin["close"] == 260500.0
    assert tin["source_function"] == "futures_main_sina"
    assert tin["source_priority"] == "domestic_main_fallback"
    assert tin["readiness_eligible"] is True


def test_all_sources_stale_returns_stale_reference():
    result = connector("all_stale").fetch_for_stock("601899")

    assert all(item["is_stale"] for item in result["commodities"])
    assert all(item["readiness_eligible"] is False for item in result["commodities"])
    assert all(item["source_priority"] == "stale_reference" for item in result["commodities"])
    assert result["success"] is False
    assert set(result["stale_commodities"]) == {"copper", "gold"}
    assert any("all_sources_stale" in item["warnings"] for item in result["commodities"])


def test_foreign_reference_does_not_satisfy_primary_readiness():
    result = connector("foreign_only").fetch_for_stock("603993")

    assert result["foreign_reference"]
    assert {item["commodity_name"] for item in result["commodities"]} == set()
    assert set(result["missing_commodities"]) == {"copper", "cobalt", "molybdenum"}


def test_unknown_stock_code_does_not_crash():
    result = connector().fetch_for_stock("002050")

    assert result["not_applicable"] is True
    assert result["commodities"] == []


def test_connector_output_is_json_safe():
    result = connector().fetch_for_stock("000426")

    loaded = json.loads(json.dumps(result, ensure_ascii=False))
    assert loaded["commodities"]


def _resource_raw(stock_code: str, commodity_prices: list[dict]) -> dict:
    return {
        "meta": {"code": stock_code, "generated_at": "2026-05-18T12:00:00", "data_cutoff": "20260331"},
        "blocks": {
            "basic_info": [
                {
                    "stock_code": stock_code,
                    "stock_name": "resource",
                    "industry": "resource",
                    "main_business": "resource mining",
                    "listing_date": "2000-01-01",
                }
            ],
            "financial_indicator": [
                {
                    "period": "20260331",
                    "revenue_yoy": 20.0,
                    "net_profit_yoy": 30.0,
                    "deducted_net_profit": 1.0,
                    "gross_margin": 40.0,
                    "operating_cashflow": 1.0,
                    "debt_to_asset": 30.0,
                    "roe": 12.0,
                }
            ],
            "business_composition": [{"segment_name": "resource", "revenue": 1.0, "revenue_ratio": 1.0}],
            "valuation": [{"pe_ttm": 12.0, "pb": 1.2, "ps": 1.0, "market_cap": 100.0}],
            "news": [{"title": "resource update"}],
            "commodity_prices": commodity_prices,
        },
        "fetch_status": {},
        "errors": [],
    }


def _classification(stock_code: str, strategy_type: str) -> StockClassificationResult:
    return StockClassificationResult(
        stock_code=stock_code,
        stock_name="resource",
        strategy_type=strategy_type,
        confidence="high",
        confidence_score=80,
    )


def _framework(strategy_type: str) -> FundamentalFramework:
    return FundamentalFramework(
        strategy_type=strategy_type,
        display_name=strategy_type,
        description=strategy_type,
        required_focus=[],
        must_track_indicators=[],
        key_risks=[],
        preferred_metrics=[],
        invalidation_focus=[],
        common_mistakes=[],
        confidence_penalty_missing_fields=[],
    )


def _plan(stock_code: str, strategy_type: str, commodity_prices: list[dict]):
    raw = _resource_raw(stock_code, commodity_prices)
    normalized = FundamentalDataAdapter().from_dict(raw)
    return DataReadinessPlanner().plan(normalized, _classification(stock_code, strategy_type), _framework(strategy_type))


def test_readiness_full_coverage_removes_external_missing_for_000426():
    plan = _plan(
        "000426",
        "resource_swing",
        [
            {"commodity_name": "silver", "price": 1.0, "date": "2026-05-18", "readiness_eligible": True},
            {"commodity_name": "tin", "price": 2.0, "date": "2026-05-18", "readiness_eligible": True},
        ],
    )

    assert all(not item.startswith("external.commodity_prices") for item in plan.high_priority_missing_fields)


def test_readiness_full_coverage_removes_external_missing_for_601899():
    plan = _plan(
        "601899",
        "resource_core",
        [
            {"commodity_name": "copper", "price": 1.0, "date": "2026-05-18", "readiness_eligible": True},
            {"commodity_name": "gold", "price": 2.0, "date": "2026-05-18", "readiness_eligible": True},
        ],
    )

    assert all(not item.startswith("external.commodity_prices") for item in plan.high_priority_missing_fields)


def test_readiness_stale_price_keeps_specific_freshness_gap():
    plan = _plan(
        "601899",
        "resource_core",
        [
            {
                "commodity_name": "copper",
                "price": 1.0,
                "date": "2026-05-01",
                "is_stale": True,
                "readiness_eligible": False,
            },
            {"commodity_name": "gold", "price": 2.0, "date": "2026-05-18", "readiness_eligible": True},
        ],
    )

    assert "external.commodity_prices" not in plan.high_priority_missing_fields
    assert "external.commodity_prices.copper.freshness" in plan.high_priority_missing_fields


def test_readiness_partial_coverage_reports_specific_missing_for_603993():
    plan = _plan(
        "603993",
        "resource_core",
        [{"commodity_name": "copper", "price": 1.0, "date": "2026-05-18", "readiness_eligible": True}],
    )

    assert "external.commodity_prices.cobalt" in plan.high_priority_missing_fields
    assert "external.commodity_prices.molybdenum" in plan.high_priority_missing_fields


def test_readiness_foreign_reference_only_requires_domestic_primary():
    plan = _plan(
        "601899",
        "resource_core",
        [
            {
                "commodity_name": "copper",
                "price": 1.0,
                "date": "2026-05-18",
                "market": "foreign_reference",
                "readiness_eligible": False,
            },
            {"commodity_name": "gold", "price": 2.0, "date": "2026-05-18", "readiness_eligible": True},
        ],
    )

    assert "external.commodity_prices.copper.domestic_primary" in plan.high_priority_missing_fields
