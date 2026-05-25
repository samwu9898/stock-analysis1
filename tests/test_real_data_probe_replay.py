# -*- coding: utf-8 -*-

import importlib.util
import json
import sys
from pathlib import Path


TRADE_TERMS = ["买入", "卖出", "加仓", "减仓", "清仓", "止损", "止盈", "目标价", "满仓", "梭哈"]


def _load_replay_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "replay_real_data_probe.py"
    spec = importlib.util.spec_from_file_location("replay_real_data_probe", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _load_probe_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "probe_akshare_real_data.py"
    spec = importlib.util.spec_from_file_location("probe_akshare_real_data", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _mock_probe():
    return {
        "schema_version": "akshare_probe.v1",
        "stock_code": "002050",
        "generated_at": "2026-05-17T10:00:00",
        "akshare_version": "1.mock",
        "limit_rows": 2,
        "categories": {
            "basic_info": [
                {
                    "category": "basic_info",
                    "function_name": "stock_individual_info_em",
                    "success": True,
                    "error": None,
                    "columns": ["stock_name", "industry", "main_business", "listing_date"],
                    "columns_full": ["stock_name", "industry", "main_business", "listing_date"],
                    "shape": [1, 4],
                    "row_count": 1,
                    "dtypes": {"stock_name": "object"},
                    "head": [{"stock_name": "三花智控", "industry": "auto parts"}],
                    "head_rows": [{"stock_name": "三花智控", "industry": "auto parts"}],
                },
                {
                    "category": "basic_info",
                    "function_name": "missing_basic_fn",
                    "success": False,
                    "error": "function_not_found",
                    "columns": [],
                    "columns_full": [],
                    "shape": [],
                    "row_count": None,
                    "dtypes": {},
                    "head": [],
                    "head_rows": [],
                },
            ],
            "financial_indicator": [
                {
                    "category": "financial_indicator",
                    "function_name": "stock_financial_analysis_indicator",
                    "success": True,
                    "error": None,
                    "columns": ["report_period", "revenue_yoy", "gross_margin", "ROE"],
                    "columns_full": ["report_period", "revenue_yoy", "gross_margin", "ROE"],
                    "shape": [4, 4],
                    "row_count": 4,
                    "dtypes": {"report_period": "object"},
                    "head": [{"report_period": "2025-12-31", "gross_margin": 28.5}],
                    "head_rows": [{"report_period": "2025-12-31", "gross_margin": 28.5}],
                },
                {
                    "category": "financial_indicator",
                    "function_name": "stock_financial_abstract",
                    "success": True,
                    "error": None,
                    "columns": ["选项", "指标", "20260331", "20251231", "20250331"],
                    "columns_full": ["选项", "指标", "20260331", "20251231", "20250331"],
                    "shape": [6, 5],
                    "row_count": 6,
                    "dtypes": {"选项": "object", "指标": "object", "20260331": "float64"},
                    "head": [{"选项": "利润表", "指标": "营业总收入", "20260331": 10.0}],
                    "head_rows": [{"选项": "利润表", "指标": "营业总收入", "20260331": 10.0}],
                    "indicator_names_full": ["营业总收入", "营业成本", "扣非净利润", "ROE", "经营现金流量净额", "存货"],
                    "option_names_full": ["利润表", "现金流量表", "资产负债表"],
                    "period_columns": ["20260331", "20251231", "20250331"],
                    "sample_rows_by_keywords": {
                        "营业总收入": [{"选项": "利润表", "指标": "营业总收入", "20260331": 10.0}],
                        "扣非净利润": [{"选项": "利润表", "指标": "扣非净利润", "20260331": 2.0}],
                        "ROE": [{"选项": "盈利能力", "指标": "ROE", "20260331": 12.0}],
                        "经营现金": [{"选项": "现金流量表", "指标": "经营现金流量净额", "20260331": 3.0}],
                    },
                },
            ],
            "valuation": [
                {
                    "category": "valuation",
                    "function_name": "stock_value_em",
                    "success": True,
                    "error": None,
                    "columns": ["日期", "PE(TTM)", "PB", "总市值"],
                    "columns_full": ["日期", "PE(TTM)", "PB", "总市值"],
                    "shape": [3, 4],
                    "row_count": 3,
                    "dtypes": {"PE(TTM)": "float64", "PB": "float64", "总市值": "float64"},
                    "head": [{"日期": "2026-05-15", "PE(TTM)": 35.0, "PB": 4.2, "总市值": 120000000000}],
                    "head_rows": [{"日期": "2026-05-15", "PE(TTM)": 35.0, "PB": 4.2, "总市值": 120000000000}],
                },
                {
                    "category": "valuation",
                    "function_name": "stock_zh_a_spot_em",
                    "success": False,
                    "error": "TimeoutError: timeout",
                    "columns": [],
                    "columns_full": [],
                    "shape": [],
                    "row_count": None,
                    "dtypes": {},
                    "head": [],
                    "head_rows": [],
                },
            ],
            "business_composition": [
                {
                    "category": "business_composition",
                    "function_name": "stock_zygc_em",
                    "success": True,
                    "error": None,
                    "columns": ["segment_name", "revenue", "revenue_ratio", "gross_margin", "period"],
                    "columns_full": ["segment_name", "revenue", "revenue_ratio", "gross_margin", "period"],
                    "shape": [3, 5],
                    "row_count": 3,
                    "dtypes": {"segment_name": "object"},
                    "head": [{"segment_name": "auto thermal", "revenue": 100.0, "revenue_ratio": 42.0, "period": "2025"}],
                    "head_rows": [{"segment_name": "auto thermal", "revenue": 100.0, "revenue_ratio": 42.0, "period": "2025"}],
                },
                {
                    "category": "business_composition",
                    "function_name": "stock_empty_business",
                    "success": True,
                    "error": None,
                    "columns": [],
                    "columns_full": [],
                    "shape": [0, 0],
                    "row_count": 0,
                    "dtypes": {},
                    "head": [],
                    "head_rows": [],
                },
            ],
            "commodity_prices": [
                {
                    "category": "commodity_prices",
                    "function_name": "spot_price_table_qh",
                    "success": True,
                    "error": None,
                    "columns": ["品种", "最新价", "单位", "日期"],
                    "columns_full": ["品种", "最新价", "单位", "日期"],
                    "shape": [2, 4],
                    "row_count": 2,
                    "dtypes": {"品种": "object", "最新价": "float64"},
                    "head": [
                        {"品种": "铜", "最新价": 80000, "单位": "元/吨", "日期": "2026-05-15"},
                        {"品种": "白银", "最新价": 8000, "单位": "元/千克", "日期": "2026-05-15"},
                    ],
                    "head_rows": [
                        {"品种": "铜", "最新价": 80000, "单位": "元/吨", "日期": "2026-05-15"},
                        {"品种": "白银", "最新价": 8000, "单位": "元/千克", "日期": "2026-05-15"},
                    ],
                },
                {
                    "category": "commodity_prices",
                    "function_name": "futures_zh_spot",
                    "commodity": "copper",
                    "symbol_used": "CU0",
                    "symbol_formatter": "symbol_kw",
                    "success": True,
                    "error": None,
                    "columns": ["datetime", "last_price", "symbol"],
                    "columns_full": ["datetime", "last_price", "symbol"],
                    "shape": [1, 3],
                    "row_count": 1,
                    "dtypes": {"datetime": "object", "last_price": "float64"},
                    "head": [{"datetime": "2026-05-17", "last_price": 82000.0, "symbol": "CU0"}],
                    "head_rows": [{"datetime": "2026-05-17", "last_price": 82000.0, "symbol": "CU0"}],
                    "detected_date_columns": ["datetime"],
                    "detected_price_columns": ["last_price"],
                    "latest_date_detected": "2026-05-17",
                    "freshness_days": 1,
                    "is_fresh_candidate": True,
                    "source_notes": [],
                },
                {
                    "category": "commodity_prices",
                    "function_name": "futures_main_sina",
                    "commodity": "tin",
                    "symbol_used": "SN0",
                    "symbol_formatter": "symbol_kw",
                    "success": True,
                    "error": None,
                    "columns": ["date", "close", "symbol"],
                    "columns_full": ["date", "close", "symbol"],
                    "shape": [1, 3],
                    "row_count": 1,
                    "dtypes": {"date": "object", "close": "float64"},
                    "head": [{"date": "2026-05-16", "close": 260000.0, "symbol": "SN0"}],
                    "head_rows": [{"date": "2026-05-16", "close": 260000.0, "symbol": "SN0"}],
                    "detected_date_columns": ["date"],
                    "detected_price_columns": ["close"],
                    "latest_date_detected": "2026-05-16",
                    "freshness_days": 2,
                    "is_fresh_candidate": True,
                    "source_notes": [],
                },
                {
                    "category": "commodity_prices",
                    "function_name": "futures_spot_price_daily",
                    "commodity": "tin",
                    "symbol_used": "SN",
                    "symbol_formatter": "symbol_kw",
                    "success": True,
                    "error": None,
                    "columns": ["date", "spot_price"],
                    "columns_full": ["date", "spot_price"],
                    "shape": [1, 2],
                    "row_count": 1,
                    "dtypes": {"date": "object", "spot_price": "float64"},
                    "head": [{"date": "2021-02-01", "spot_price": 169500.0}],
                    "head_rows": [{"date": "2021-02-01", "spot_price": 169500.0}],
                    "detected_date_columns": ["date"],
                    "detected_price_columns": ["spot_price"],
                    "latest_date_detected": "2021-02-01",
                    "freshness_days": 1932,
                    "is_fresh_candidate": False,
                    "source_notes": [],
                },
                {
                    "category": "commodity_prices",
                    "function_name": "futures_hist_daily_em",
                    "commodity": "copper",
                    "symbol_used": "CU",
                    "symbol_formatter": "symbol_kw",
                    "success": True,
                    "error": None,
                    "columns": ["last_price"],
                    "columns_full": ["last_price"],
                    "shape": [1, 1],
                    "row_count": 1,
                    "dtypes": {"last_price": "float64"},
                    "head": [{"last_price": 81000.0}],
                    "head_rows": [{"last_price": 81000.0}],
                    "detected_date_columns": [],
                    "detected_price_columns": ["last_price"],
                    "latest_date_detected": None,
                    "freshness_days": None,
                    "is_fresh_candidate": False,
                    "source_notes": [],
                },
                {
                    "category": "commodity_prices",
                    "function_name": "futures_hist_daily_sina",
                    "commodity": "tin",
                    "symbol_used": "SN",
                    "symbol_formatter": "symbol_kw",
                    "success": True,
                    "error": None,
                    "columns": ["date"],
                    "columns_full": ["date"],
                    "shape": [1, 1],
                    "row_count": 1,
                    "dtypes": {"date": "object"},
                    "head": [{"date": "2026-05-17"}],
                    "head_rows": [{"date": "2026-05-17"}],
                    "detected_date_columns": ["date"],
                    "detected_price_columns": [],
                    "latest_date_detected": "2026-05-17",
                    "freshness_days": 1,
                    "is_fresh_candidate": True,
                    "source_notes": [],
                },
                {
                    "category": "commodity_prices",
                    "function_name": "missing_commodity_fn",
                    "success": False,
                    "error": "function_not_found",
                    "columns": [],
                    "columns_full": [],
                    "shape": [],
                    "row_count": None,
                    "dtypes": {},
                    "head": [],
                    "head_rows": [],
                },
            ],
            "news": [
                {
                    "category": "news",
                    "function_name": "stock_news_em",
                    "success": True,
                    "error": None,
                    "columns": ["title", "publish_time", "source", "url"],
                    "columns_full": ["title", "publish_time", "source", "url"],
                    "shape": [5, 4],
                    "row_count": 5,
                    "dtypes": {"title": "object"},
                    "head": [{"title": "mock title"}],
                    "head_rows": [{"title": "mock title"}],
                }
            ],
        },
    }


def test_replay_reads_probe_json(tmp_path):
    module = _load_replay_module()
    path = tmp_path / "probe_002050.json"
    path.write_text(json.dumps(_mock_probe(), ensure_ascii=False), encoding="utf-8")

    probe = module.load_probe(path)

    assert probe["stock_code"] == "002050"


def test_replay_identifies_success_failed_and_function_not_found():
    module = _load_replay_module()
    summary = module.replay_probe(_mock_probe())

    assert "stock_individual_info_em" in summary["successful_blocks"]["basic_info"]
    assert "stock_zh_a_spot_em" in summary["failed_blocks"]["valuation"]
    assert "missing_basic_fn" in summary["function_not_found"]["basic_info"]
    assert "missing_commodity_fn" in summary["function_not_found"]["commodity_prices"]


def test_dataframe_like_payload_is_summarized_into_mapping_suggestions():
    module = _load_replay_module()
    summary = module.replay_probe(_mock_probe())
    basic_candidates = summary["mapping_suggestions"]["basic_info"]["field_candidates"]
    financial_candidates = summary["mapping_suggestions"]["financial_indicator"]["field_candidates"]

    assert basic_candidates["stock_name"][0]["column"] == "stock_name"
    assert financial_candidates["gross_margin"][0]["column"] == "gross_margin"


def test_replay_reads_financial_abstract_indicator_names():
    module = _load_replay_module()
    summary = module.replay_probe(_mock_probe())
    detail = summary["financial_abstract"][0]

    assert detail["indicator_names_full"] == ["营业总收入", "营业成本", "扣非净利润", "ROE", "经营现金流量净额", "存货"]
    assert detail["period_columns"] == ["20260331", "20251231", "20250331"]
    assert detail["target_mappings"]["deducted_net_profit"]["matched_indicators"] == ["扣非净利润"]
    assert detail["target_mappings"]["roe"]["matched_indicators"] == ["ROE"]
    assert detail["target_mappings"]["operating_cashflow"]["matched_indicators"] == ["经营现金流量净额"]


def test_replay_identifies_valuation_candidates():
    module = _load_replay_module()
    summary = module.replay_probe(_mock_probe())
    valuation = summary["valuation_candidates"]

    assert valuation["field_candidates"]["pe_ttm"][0]["column"] == "PE(TTM)"
    assert valuation["field_candidates"]["pb"][0]["column"] == "PB"
    assert valuation["field_candidates"]["market_cap"][0]["column"] == "总市值"
    assert "ps" in valuation["missing_fields"]


def test_replay_identifies_business_composition_candidates_and_empty_tables():
    module = _load_replay_module()
    summary = module.replay_probe(_mock_probe())
    business = summary["business_composition_candidates"]

    assert business["field_candidates"]["segment_name"][0]["column"] == "segment_name"
    assert business["field_candidates"]["revenue"][0]["column"] == "revenue"
    assert business["field_candidates"]["revenue_ratio"][0]["column"] == "revenue_ratio"
    assert any(item["function_name"] == "stock_empty_business" and item["empty_table"] for item in business["usable_successes"])


def test_replay_summarizes_commodity_prices_block():
    module = _load_replay_module()
    summary = module.replay_probe(_mock_probe())
    commodity = summary["commodity_prices"]

    assert "spot_price_table_qh" in commodity["successful_functions"]
    assert "copper" in commodity["covered_commodities"]
    assert "silver" in commodity["covered_commodities"]
    assert commodity["strategy_types"] == ["resource_swing", "resource_core"]
    assert commodity["connector_ready"] is False


def test_replay_identifies_fresh_copper_and_tin_candidates():
    module = _load_replay_module()
    summary = module.replay_probe(_mock_probe())
    freshness = summary["copper_tin_freshness"]

    assert "futures_zh_spot" in freshness["successful_functions"]["copper"]
    assert "futures_main_sina" in freshness["successful_functions"]["tin"]
    assert freshness["best_connector_v11_candidates"]["copper"]["function_name"] == "futures_zh_spot"
    assert freshness["best_connector_v11_candidates"]["tin"]["function_name"] == "futures_main_sina"
    assert freshness["best_connector_v11_candidates"]["copper"]["latest_date_detected"] == "2026-05-17"


def test_replay_marks_stale_and_missing_columns_without_crashing():
    module = _load_replay_module()
    summary = module.replay_probe(_mock_probe())
    tin_items = summary["copper_tin_freshness"]["commodities"]["tin"]
    copper_items = summary["copper_tin_freshness"]["commodities"]["copper"]

    stale_tin = next(item for item in tin_items if item["function_name"] == "futures_spot_price_daily")
    missing_date = next(item for item in copper_items if item["function_name"] == "futures_hist_daily_em")
    missing_price = next(item for item in tin_items if item["function_name"] == "futures_hist_daily_sina")

    assert stale_tin["is_fresh_candidate"] is False
    assert stale_tin["latest_date_detected"] == "2021-02-01"
    assert missing_date["detected_date_columns"] == []
    assert missing_date["is_fresh_candidate"] is False
    assert missing_price["detected_price_columns"] == []
    assert missing_price not in summary["copper_tin_freshness"]["fresh_candidates"]["tin"]


def test_probe_detects_freshness_metadata_for_payloads(monkeypatch):
    pandas = __import__("pandas")
    module = _load_probe_module()
    real_datetime = module.datetime

    class FixedDateTime(real_datetime):
        @classmethod
        def now(cls):
            return real_datetime(2026, 5, 20, 10, 0, 0)

    monkeypatch.setattr(module, "datetime", FixedDateTime)
    frame = pandas.DataFrame(
        [
            {"date": "2026-05-11", "close": 80000.0},
            {"date": "2026-05-18", "close": 81000.0},
        ]
    )

    summary = module.summarize_payload(frame, limit_rows=1)

    assert summary["detected_date_columns"] == ["date"]
    assert "close" in summary["detected_price_columns"]
    assert summary["latest_date_detected"] == "2026-05-18"
    assert summary["freshness_days"] == 2
    assert summary["is_fresh_candidate"] is True


def test_probe_records_function_not_found_with_freshness_fields():
    module = _load_probe_module()

    class FakeAk:
        pass

    result = module.run_candidate(
        FakeAk(),
        module.Candidate(
            "commodity_prices",
            "missing_probe_fn",
            module._args_none,
            module._kwargs_empty,
            "missing function",
            commodity="copper",
            symbol_used="CU",
            symbol_formatter="symbol_kw",
        ),
        "000426",
        1,
    )

    assert result["error"] == "function_not_found"
    assert result["commodity"] == "copper"
    assert result["symbol_used"] == "CU"
    assert result["detected_date_columns"] == []
    assert result["is_fresh_candidate"] is False


def test_probe_summarizes_indicator_dataframe_keyword_rows():
    pandas = __import__("pandas")
    module = _load_probe_module()
    frame = pandas.DataFrame(
        [
            {"选项": "利润表", "指标": "营业总收入", "20260331": 10.0, "20251231": 40.0},
            {"选项": "利润表", "指标": "扣非净利润", "20260331": 2.0, "20251231": 8.0},
            {"选项": "盈利能力", "指标": "ROE", "20260331": 12.0, "20251231": 11.0},
            {"选项": "现金流量表", "指标": "经营现金流量净额", "20260331": 3.0, "20251231": 9.0},
            {"选项": "资产负债表", "指标": "应收账款", "20260331": 4.0, "20251231": 5.0},
        ]
    )

    summary = module.summarize_payload(frame, limit_rows=2)

    assert summary["columns_full"] == ["选项", "指标", "20260331", "20251231"]
    assert summary["head_rows"] == summary["head"]
    assert summary["indicator_names_full"] == ["营业总收入", "扣非净利润", "ROE", "经营现金流量净额", "应收账款"]
    assert summary["option_names_full"] == ["利润表", "盈利能力", "现金流量表", "资产负债表"]
    assert summary["period_columns"] == ["20260331", "20251231"]
    assert summary["row_count"] == 5


def test_probe_summarizes_list_and_dict_payloads_with_full_fields():
    module = _load_probe_module()

    list_summary = module.summarize_payload([{"品种": "铜", "最新价": 80000}], limit_rows=1)
    dict_summary = module.summarize_payload({"PE": 20, "PB": 2}, limit_rows=1)

    assert list_summary["columns_full"] == ["品种", "最新价"]
    assert list_summary["head_rows"] == [{"品种": "铜", "最新价": 80000}]
    assert list_summary["row_count"] == 1
    assert dict_summary["columns_full"] == ["PE", "PB"]
    assert dict_summary["head_rows"] == [{"PE": 20, "PB": 2}]


def test_format_summary_has_no_trading_terms():
    module = _load_replay_module()
    text = module.format_summary(module.replay_probe(_mock_probe()))

    for term in TRADE_TERMS:
        assert term not in text


def test_replay_writes_optional_markdown(tmp_path):
    module = _load_replay_module()
    summary = module.replay_probe(_mock_probe())
    output = tmp_path / "replay_002050.md"
    output.write_text(module.format_summary(summary), encoding="utf-8")

    assert output.exists()
    assert "Mapping Suggestions" in output.read_text(encoding="utf-8")
