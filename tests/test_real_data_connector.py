# -*- coding: utf-8 -*-

from datetime import date, datetime
from decimal import Decimal
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.fundamental_skill.pipeline import FundamentalSkillPipeline
from src.fundamental_skill.real_data_connector import RealDataConnector
from src.fundamental_skill.real_stock_runner import run_real_stock
from src.fundamental_skill.validators import validate_no_trading_instruction


TRADE_TERMS = ["买入", "卖出", "加仓", "减仓", "清仓", "止损", "止盈", "目标价", "满仓", "梭哈"]


class MockConnector(RealDataConnector):
    def __init__(self, cache_dir: Path, fail_valuation: bool = False) -> None:
        super().__init__(cache_dir=cache_dir)
        self.fail_valuation = fail_valuation

    def _fetch_basic_info(self, code: str):
        return [
            {
                "stock_code": code,
                "stock_name": "三花智控",
                "industry": "汽车零部件 / 热管理 / 工业自动化",
                "main_business": "制冷控制元器件、汽车热管理系统零部件、机器人执行器相关零部件布局",
                "listing_date": "2005-06-07",
            }
        ]

    def _fetch_financial_indicator(self, code: str):
        return [
            {
                "period": "2025-12-31",
                "revenue_yoy": 24.5,
                "net_profit_yoy": 31.2,
                "deducted_net_profit": 3600000000,
                "gross_margin": 28.5,
                "net_margin": 12.1,
                "roe": 18.2,
                "operating_cashflow": 4200000000,
                "debt_to_asset": 48.0,
                "inventory": 3600000000,
                "accounts_receivable": 5200000000,
            }
        ]

    def _fetch_valuation(self, code: str):
        if self.fail_valuation:
            raise RuntimeError("valuation endpoint unavailable")
        return [{"pe_ttm": 45.0, "pb": 5.2, "ps": 3.8, "market_cap": 120000000000}]

    def _fetch_business_composition(self, code: str):
        return [
            {
                "period": "2025-12-31",
                "segment_name": "汽车热管理系统零部件",
                "revenue": 13400000000,
                "revenue_ratio": 42.0,
                "gross_margin": 30.0,
            }
        ]

    def _fetch_news(self, code: str):
        return [
            {
                "title": "mock: 汽车热管理业务保持增长",
                "publish_time": "2026-01-15",
                "source": "mock",
                "url": None,
                "summary": "汽车热管理相关订单和收入仍需后续财报验证",
            }
        ]


def test_fetch_to_raw_json_shape_and_output_path(tmp_path):
    output_path = tmp_path / "raw_002050.json"
    raw = MockConnector(tmp_path / "cache").fetch_to_raw_json("002050", output_path=str(output_path))

    assert set(raw) >= {"meta", "blocks", "fetch_status", "errors"}
    assert raw["meta"]["code"] == "002050"
    assert raw["meta"]["connector_version"] == "real_data_connector.v2.3a"
    for block_name in ["basic_info", "financial_indicator", "valuation", "business_composition", "news"]:
        assert block_name in raw["blocks"]
        assert block_name in raw["fetch_status"]
    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8"))["meta"]["code"] == "002050"


def test_fetch_failure_is_recorded_without_crashing(tmp_path):
    raw = MockConnector(tmp_path / "cache", fail_valuation=True).fetch_to_raw_json("002050")

    assert raw["fetch_status"]["valuation"]["success"] is False
    assert "valuation endpoint unavailable" in raw["fetch_status"]["valuation"]["error"]
    assert any("valuation endpoint unavailable" in error for error in raw["errors"])
    assert raw["blocks"]["basic_info"]


def test_cache_is_used_within_24_hours(tmp_path):
    connector = MockConnector(tmp_path / "cache")
    first = connector.fetch_to_raw_json("002050")
    second = MockConnector(tmp_path / "cache", fail_valuation=True).fetch_to_raw_json("002050")

    assert first["meta"]["cache_hit"] is False
    assert second["meta"]["cache_hit"] is True
    assert second["fetch_status"]["valuation"]["success"] is True


def test_raw_json_can_be_consumed_by_pipeline():
    raw_path = Path(__file__).parent / "fixtures" / "real_connector_mock_002050.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8"))

    result = FundamentalSkillPipeline().analyze_from_dict(raw)

    assert result.stock_code == "002050"
    assert result.schema_version == "fundamental.v1"
    assert validate_no_trading_instruction(result.model_dump_json()) == []


def test_real_stock_runner_core_flow_with_mock_connector(tmp_path):
    output_path = tmp_path / "fundamental_002050.json"
    raw, result = run_real_stock(
        "002050",
        output=str(output_path),
        connector=MockConnector(tmp_path / "cache"),
    )

    assert raw["meta"]["code"] == "002050"
    assert result.stock_code == "002050"
    assert output_path.exists()
    assert (tmp_path / "raw_002050.json").exists()


def test_runner_result_has_no_trading_terms(tmp_path):
    _, result = run_real_stock(
        "002050",
        output=str(tmp_path / "fundamental_002050.json"),
        connector=MockConnector(tmp_path / "cache"),
    )
    dumped = result.model_dump_json()

    for term in TRADE_TERMS:
        assert term not in dumped
    assert validate_no_trading_instruction(dumped) == []


class FakeAkshare:
    __version__ = "1.mock"

    def __init__(
        self,
        financial_frame: pd.DataFrame | None = None,
        balance_frame: pd.DataFrame | None = None,
        profit_frame: pd.DataFrame | None = None,
        cashflow_frame: pd.DataFrame | None = None,
        valuation_frame: pd.DataFrame | None = None,
        business_frame: pd.DataFrame | None = None,
    ) -> None:
        self.financial_frame = financial_frame if financial_frame is not None else _financial_abstract_frame()
        self.balance_frame = balance_frame if balance_frame is not None else _sina_balance_sheet_frame()
        self.profit_frame = profit_frame if profit_frame is not None else _sina_profit_sheet_frame()
        self.cashflow_frame = cashflow_frame if cashflow_frame is not None else _sina_cashflow_sheet_frame()
        self.valuation_frame = valuation_frame if valuation_frame is not None else _valuation_frame()
        self.business_frame = business_frame if business_frame is not None else _business_composition_frame()

    def stock_profile_cninfo(self, symbol: str):
        return pd.DataFrame(
            [
                {
                    "A股代码": symbol,
                    "A股简称": "三花智控",
                    "公司名称": "浙江三花智能控制股份有限公司",
                    "所属行业": "汽车零部件",
                    "主营业务": "制冷控制元器件和汽车热管理系统零部件",
                    "经营范围": "备用经营范围",
                    "上市日期": "2005-06-07",
                }
            ]
        )

    def stock_financial_abstract(self, symbol: str):
        return self.financial_frame

    def stock_financial_report_sina(self, stock=None, symbol=None, indicator=None):
        statement = indicator or symbol
        if statement == "资产负债表":
            return self.balance_frame
        if statement == "利润表":
            return self.profit_frame
        if statement == "现金流量表":
            return self.cashflow_frame
        assert statement == "资产负债表"
        return self.balance_frame

    def stock_value_em(self, symbol: str):
        return self.valuation_frame

    def stock_zygc_em(self, symbol: str):
        return self.business_frame

    def stock_news_em(self, symbol: str):
        return pd.DataFrame(
            [
                {
                    "新闻标题": "公司发布公开业务动态",
                    "发布时间": "2026-05-17 10:00:00",
                    "文章来源": "东方财富",
                    "新闻链接": "https://example.com/news",
                    "新闻内容": "公开新闻内容摘要",
                }
            ]
        )

    def futures_spot_price(self, vars_list=None):
        rows = []
        for symbol in vars_list or []:
            rows.append(
                {
                    "symbol": symbol,
                    "date": date.today().isoformat(),
                    "spot_price": 100.0,
                    "near_contract": f"{symbol}2606",
                    "near_contract_price": 101.0,
                    "dominant_contract": f"{symbol}2607",
                    "dominant_contract_price": 102.0,
                }
            )
        return pd.DataFrame(rows)

    def futures_spot_price_daily(self, vars_list=None):
        return pd.DataFrame()


class AkshareConnector(RealDataConnector):
    def __init__(
        self,
        cache_dir: Path,
        financial_frame: pd.DataFrame | None = None,
        balance_frame: pd.DataFrame | None = None,
        profit_frame: pd.DataFrame | None = None,
        cashflow_frame: pd.DataFrame | None = None,
        valuation_frame: pd.DataFrame | None = None,
        business_frame: pd.DataFrame | None = None,
    ) -> None:
        super().__init__(cache_dir=cache_dir)
        self.fake_ak = FakeAkshare(
            financial_frame=financial_frame,
            balance_frame=balance_frame,
            profit_frame=profit_frame,
            cashflow_frame=cashflow_frame,
            valuation_frame=valuation_frame,
            business_frame=business_frame,
        )

    def _load_akshare(self):
        return self.fake_ak


def _financial_abstract_frame(include_growth: bool = True, include_direct_margin: bool = True) -> pd.DataFrame:
    rows = [
        {"选项": "利润表", "指标": "营业总收入", "20260331": 130.0, "20250331": 100.0},
        {"选项": "利润表", "指标": "营业成本", "20260331": 91.0, "20250331": 75.0},
        {"选项": "利润表", "指标": "归母净利润", "20260331": 24.0, "20250331": 20.0},
        {"选项": "利润表", "指标": "净利润", "20260331": 22.0, "20250331": 18.0},
        {"选项": "利润表", "指标": "扣非净利润", "20260331": 21.0, "20250331": 17.0},
        {"选项": "现金流量表", "指标": "经营现金流量净额", "20260331": 30.0, "20250331": 25.0},
        {"选项": "盈利能力", "指标": "净资产收益率(ROE)", "20260331": 12.5, "20250331": 11.0},
        {"选项": "偿债能力", "指标": "资产负债率", "20260331": 45.0, "20250331": 44.0},
        {"选项": "运营能力", "指标": "存货周转率", "20260331": 4.2, "20250331": 4.0},
        {"选项": "运营能力", "指标": "应收账款周转率", "20260331": 5.1, "20250331": 4.8},
    ]
    if include_growth:
        rows.extend(
            [
                {"选项": "成长能力", "指标": "营业总收入增长率", "20260331": 31.0, "20250331": 25.0},
                {"选项": "成长能力", "指标": "归属母公司净利润增长率", "20260331": 22.0, "20250331": 20.0},
            ]
        )
    if include_direct_margin:
        rows.extend(
            [
                {"选项": "盈利能力", "指标": "毛利率", "20260331": 29.5, "20250331": 25.0},
                {"选项": "盈利能力", "指标": "销售净利率", "20260331": 16.5, "20250331": 15.0},
            ]
        )
    return pd.DataFrame(rows)


def _sina_balance_sheet_frame(report_date: str | None = "20260331") -> pd.DataFrame:
    row = {
        "报告日": report_date,
        "应收账款": 7010919404.89,
        "存货": 5879322018.99,
        "合同负债": 80754056.98,
        "存货周转率": 4.2,
        "存货周转天数": 86.0,
        "应收账款周转率": 5.1,
        "应收账款周转天数": 70.0,
    }
    return pd.DataFrame([row])


def _sina_profit_sheet_frame(report_date: str | None = "20260331", revenue_report_date: str | None = "20260331") -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "报告日": report_date,
                "研发费用": 367461670.95,
                "营业总收入": None,
            },
            {
                "报告日": revenue_report_date,
                "研发费用": None,
                "营业总收入": 7773000000.0,
            },
        ]
    )


def _sina_cashflow_sheet_frame(report_date: str | None = "20260331") -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "报告日": report_date,
                "购建固定资产、无形资产和其他长期资产所支付的现金": 521898492.14,
            }
        ]
    )


def _valuation_frame(include_pe: bool = True) -> pd.DataFrame:
    rows = [
        {
            "数据日期": "2026-05-15",
            "PE(TTM)": 35.0,
            "市净率": 4.2,
            "市销率": 3.1,
            "总市值": 120000000000,
            "流通市值": 90000000000,
        },
        {
            "数据日期": "2026-05-17",
            "PE(TTM)": 38.0,
            "市净率": 4.5,
            "市销率": 3.4,
            "总市值": 130000000000,
            "流通市值": 98000000000,
        },
    ]
    if not include_pe:
        for row in rows:
            row.pop("PE(TTM)", None)
    return pd.DataFrame(rows)


def _business_composition_frame(empty: bool = False) -> pd.DataFrame:
    columns = ["股票代码", "报告日期", "分类类型", "主营构成", "主营收入", "收入比例", "主营成本", "成本比例", "主营利润", "利润比例", "毛利率"]
    if empty:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "股票代码": "002050",
                "报告日期": "2024-12-31",
                "分类类型": "按产品分类",
                "主营构成": "旧业务",
                "主营收入": 1.0,
                "收入比例": 0.01,
                "主营成本": 0.7,
                "成本比例": 0.01,
                "主营利润": 0.3,
                "利润比例": 0.01,
                "毛利率": 0.3,
            },
            {
                "股票代码": "002050",
                "报告日期": "2025-12-31",
                "分类类型": "按产品分类",
                "主营构成": "制冷空调电器零部件",
                "主营收入": 18584743718.09,
                "收入比例": 0.599281,
                "主营成本": 13238149193.04,
                "成本比例": 0.59935,
                "主营利润": 5346594525.05,
                "利润比例": 0.599109,
                "毛利率": 0.287687,
            },
            {
                "股票代码": "002050",
                "报告日期": "2025-12-31",
                "分类类型": "按行业分类",
                "主营构成": "通用设备制造业",
                "主营收入": 31011744510.27,
                "收入比例": 1.0,
                "主营成本": 22087497052.41,
                "成本比例": 1.0,
                "主营利润": 8924247457.86,
                "利润比例": 1.0,
                "毛利率": 0.28777,
            },
            {
                "股票代码": "002050",
                "报告日期": "2025-12-31",
                "分类类型": "按产品分类",
                "主营构成": "",
                "主营收入": 100.0,
                "收入比例": 0.1,
                "主营成本": 80.0,
                "成本比例": 0.1,
                "主营利润": 20.0,
                "利润比例": 0.1,
                "毛利率": 0.2,
            },
        ]
    )


def test_v2_maps_profile_news_and_financial_abstract(tmp_path):
    raw = AkshareConnector(tmp_path / "cache").fetch_to_raw_json("002050", force_refresh=True)

    basic = raw["blocks"]["basic_info"][0]
    news = raw["blocks"]["news"][0]
    metric = raw["blocks"]["financial_indicator"][0]

    assert basic["stock_code"] == "002050"
    assert basic["stock_name"] == "三花智控"
    assert basic["industry"] == "汽车零部件"
    assert basic["main_business"] == "制冷控制元器件和汽车热管理系统零部件"
    assert basic["listing_date"] == "2005-06-07"
    assert news["title"] == "公司发布公开业务动态"
    assert news["publish_time"] == "2026-05-17 10:00:00"
    assert news["source"] == "东方财富"
    assert news["url"] == "https://example.com/news"
    assert news["summary"] == "公开新闻内容摘要"
    assert metric["period"] == "20260331"
    assert metric["revenue_yoy"] == 31.0
    assert metric["net_profit_yoy"] == 22.0
    assert metric["deducted_net_profit"] == 21.0
    assert metric["gross_margin"] == 29.5
    assert metric["net_margin"] == 16.5
    assert metric["roe"] == 12.5
    assert metric["operating_cashflow"] == 30.0
    assert metric["debt_to_asset"] == 45.0
    assert metric["inventory"] == 5879322018.99
    assert metric["accounts_receivable"] == 7010919404.89
    assert metric["contract_liabilities"] == 80754056.98
    assert "inventory" not in raw["fetch_status"]["financial_indicator"]["missing_fields"]
    assert "accounts_receivable" not in raw["fetch_status"]["financial_indicator"]["missing_fields"]
    assert "contract_liabilities" not in raw["fetch_status"]["financial_indicator"]["missing_fields"]
    assert any("inventory" in warning for warning in raw["fetch_status"]["financial_indicator"]["warnings"])
    assert any("accounts_receivable" in warning for warning in raw["fetch_status"]["financial_indicator"]["warnings"])


def test_v22a_maps_sina_balance_sheet_fields_and_source_trace(tmp_path):
    raw = AkshareConnector(tmp_path / "cache").fetch_to_raw_json("002050", force_refresh=True)
    metric = raw["blocks"]["financial_indicator"][0]
    traces = raw["fetch_status"]["financial_indicator"]["source_trace"]

    assert metric["inventory"] == 5879322018.99
    assert metric["accounts_receivable"] == 7010919404.89
    assert metric["contract_liabilities"] == 80754056.98

    for field_name, source_column in {
        "inventory": "存货",
        "accounts_receivable": "应收账款",
        "contract_liabilities": "合同负债",
    }.items():
        trace = next(item for item in traces if item["field_name"] == field_name)
        assert trace["source_function"] == "stock_financial_report_sina"
        assert trace["source_column_or_row"] == source_column
        assert trace["source_period"] == "20260331"
        assert trace["period_confidence"] == "high"
        assert trace["value_confidence"] == "medium"
        assert trace["statement_type"] == "balance_sheet"

    contract_trace = next(item for item in traces if item["field_name"] == "contract_liabilities")
    assert contract_trace["scope_note"] == "合同负债可作为订单可见度 proxy，但不等同于真实订单或 backlog。"


def test_v22a_unrecognizable_sina_report_period_does_not_crash(tmp_path):
    raw = AkshareConnector(
        tmp_path / "cache",
        balance_frame=_sina_balance_sheet_frame(report_date=None),
    ).fetch_to_raw_json("002050", force_refresh=True)
    metric = raw["blocks"]["financial_indicator"][0]
    traces = raw["fetch_status"]["financial_indicator"]["source_trace"]

    assert metric["inventory"] == 5879322018.99
    inventory_trace = next(item for item in traces if item["field_name"] == "inventory")
    assert inventory_trace["source_period"] == "unknown"
    assert inventory_trace["period_confidence"] == "low"


def test_v23a_maps_rd_expense_capex_and_rd_ratio_source_trace(tmp_path):
    raw = AkshareConnector(tmp_path / "cache").fetch_to_raw_json("002050", force_refresh=True)
    metric = raw["blocks"]["financial_indicator"][0]
    traces = raw["fetch_status"]["financial_indicator"]["source_trace"]

    assert metric["r_and_d_expense"] == 367461670.95
    assert metric["r_and_d_expense_ratio"] == 367461670.95 / 7773000000.0 * 100
    assert metric["capex"] == 521898492.14
    assert "capex_ratio" not in metric
    assert "depreciation_amortization" not in metric

    rd_trace = next(item for item in traces if item["field_name"] == "r_and_d_expense")
    ratio_trace = next(item for item in traces if item["field_name"] == "r_and_d_expense_ratio")
    capex_trace = next(item for item in traces if item["field_name"] == "capex")

    assert rd_trace["source_function"] == "stock_financial_report_sina"
    assert rd_trace["source_column_or_row"] == "研发费用"
    assert rd_trace["source_period"] == "20260331"
    assert rd_trace["period_confidence"] == "high"
    assert rd_trace["value_confidence"] == "medium"
    assert rd_trace["unit"] == "raw_statement_unit"
    assert rd_trace["unit_confidence"] == "low"
    assert rd_trace["cumulative_or_single_quarter"] == "cumulative"
    assert rd_trace["statement_type"] == "profit_sheet"
    assert rd_trace["derived"] is False

    assert ratio_trace["unit"] == "%"
    assert ratio_trace["unit_confidence"] == "high"
    assert ratio_trace["derived"] is True
    assert ratio_trace["derivation_method"] == "r_and_d_expense / revenue * 100, same source_period only"
    assert ratio_trace["cumulative_or_single_quarter"] == "cumulative"

    assert capex_trace["source_column_or_row"] == "购建固定资产、无形资产和其他长期资产所支付的现金"
    assert capex_trace["statement_type"] == "cash_flow_sheet"
    assert capex_trace["unit_confidence"] == "low"
    assert capex_trace["cumulative_or_single_quarter"] == "cumulative"


def test_v23a_different_period_does_not_derive_rd_ratio(tmp_path):
    raw = AkshareConnector(
        tmp_path / "cache",
        profit_frame=_sina_profit_sheet_frame(report_date="20260331", revenue_report_date="20251231"),
    ).fetch_to_raw_json("002050", force_refresh=True)
    metric = raw["blocks"]["financial_indicator"][0]

    assert metric["r_and_d_expense"] == 367461670.95
    assert "r_and_d_expense_ratio" not in metric
    assert any("r_and_d_expense_ratio not derived" in warning for warning in raw["fetch_status"]["financial_indicator"]["warnings"])


def test_v23a_scope_notes_do_not_contain_trading_terms(tmp_path):
    raw = AkshareConnector(tmp_path / "cache").fetch_to_raw_json("002050", force_refresh=True)
    traces = raw["fetch_status"]["financial_indicator"]["source_trace"]
    scoped = [
        trace["scope_note"]
        for trace in traces
        if trace.get("field_name") in {"r_and_d_expense", "r_and_d_expense_ratio", "capex"}
    ]

    assert scoped
    for note in scoped:
        for term in TRADE_TERMS:
            assert term not in note


def test_v22a_does_not_use_turnover_columns_as_amount_fields(tmp_path):
    balance = pd.DataFrame(
        [
            {
                "报告日": "20260331",
                "存货周转率": 9.9,
                "存货周转天数": 37.0,
                "应收账款周转率": 8.8,
                "应收账款周转天数": 41.0,
            }
        ]
    )
    raw = AkshareConnector(tmp_path / "cache", balance_frame=balance).fetch_to_raw_json("002050", force_refresh=True)
    metric = raw["blocks"]["financial_indicator"][0]

    assert metric.get("inventory") is None
    assert metric.get("accounts_receivable") is None
    assert metric.get("contract_liabilities") is None
    assert "inventory" in raw["fetch_status"]["financial_indicator"]["missing_fields"]
    assert "accounts_receivable" in raw["fetch_status"]["financial_indicator"]["missing_fields"]
    assert "contract_liabilities" in raw["fetch_status"]["financial_indicator"]["missing_fields"]


def test_v2_financial_fallbacks_and_source_trace(tmp_path):
    frame = _financial_abstract_frame(include_growth=False, include_direct_margin=False)
    raw = AkshareConnector(tmp_path / "cache", financial_frame=frame).fetch_to_raw_json("002050", force_refresh=True)
    metric = raw["blocks"]["financial_indicator"][0]
    traces = raw["fetch_status"]["financial_indicator"]["source_trace"]

    assert metric["revenue_yoy"] == 30.0
    assert metric["net_profit_yoy"] == 20.0
    assert metric["gross_margin"] == 30.0
    assert metric["net_margin"] == 22.0 / 130.0 * 100
    assert any(trace["field_name"] == "revenue_yoy" and trace["derived"] is True and trace["derivation_method"] == "yoy_from_same_period" for trace in traces)
    assert any(trace["field_name"] == "gross_margin" and trace["derived"] is True and trace["derivation_method"] == "margin_from_revenue_cost" for trace in traces)


def test_v21_maps_stock_value_em_valuation_and_source_trace(tmp_path):
    raw = AkshareConnector(tmp_path / "cache").fetch_to_raw_json("002050", force_refresh=True)
    valuation = raw["blocks"]["valuation"][0]
    traces = raw["fetch_status"]["valuation"]["source_trace"]

    assert valuation["period"] == "2026-05-17"
    assert valuation["pe_ttm"] == 38.0
    assert valuation["pb"] == 4.5
    assert valuation["ps"] == 3.4
    assert valuation["market_cap"] == 130000000000.0
    assert valuation["dividend_yield"] is None
    assert "dividend_yield" in raw["fetch_status"]["valuation"]["missing_fields"]
    assert any(
        trace["field_name"] == "pe_ttm"
        and trace["function_name"] == "stock_value_em"
        and trace["source_column"] == "PE(TTM)"
        and trace["source_period"] == "2026-05-17"
        and trace["derived"] is False
        for trace in traces
    )


def test_v21_valuation_missing_pe_does_not_crash(tmp_path):
    raw = AkshareConnector(
        tmp_path / "cache",
        valuation_frame=_valuation_frame(include_pe=False),
    ).fetch_to_raw_json("002050", force_refresh=True)
    valuation = raw["blocks"]["valuation"][0]

    assert valuation["pe_ttm"] is None
    assert valuation["pb"] == 4.5
    assert valuation["ps"] == 3.4
    assert "pe_ttm" in raw["fetch_status"]["valuation"]["missing_fields"]
    assert any("PE(TTM)" in warning for warning in raw["fetch_status"]["valuation"]["warnings"])


def test_v21_maps_stock_zygc_em_business_composition_latest_period(tmp_path):
    raw = AkshareConnector(tmp_path / "cache").fetch_to_raw_json("002050", force_refresh=True)
    segments = raw["blocks"]["business_composition"]
    traces = raw["fetch_status"]["business_composition"]["source_trace"]

    assert len(segments) == 2
    assert {segment["period"] for segment in segments} == {"2025-12-31"}
    assert all(segment["segment_name"] for segment in segments)
    product = next(segment for segment in segments if segment["classification_type"] == "按产品分类")
    assert product["segment_name"] == "制冷空调电器零部件"
    assert product["revenue"] == 18584743718.09
    assert product["revenue_ratio"] == 0.599281
    assert product["gross_margin"] == 0.287687
    assert product["cost"] == 13238149193.04
    assert product["cost_ratio"] == 0.59935
    assert product["profit"] == 5346594525.05
    assert product["profit_ratio"] == 0.599109
    assert any(
        trace["field_name"] == "segments"
        and trace["function_name"] == "stock_zygc_em"
        and trace["source_period"] == "2025-12-31"
        and trace["row_count"] == 2
        and "主营构成" in trace["columns"]
        for trace in traces
    )


def test_v21_empty_business_composition_is_missing_not_crash(tmp_path):
    raw = AkshareConnector(
        tmp_path / "cache",
        business_frame=_business_composition_frame(empty=True),
    ).fetch_to_raw_json("002050", force_refresh=True)

    assert raw["blocks"]["business_composition"] == []
    assert "business_composition.segments" in raw["fetch_status"]["business_composition"]["missing_fields"]
    assert any("stock_zygc_em returned no rows" in warning for warning in raw["fetch_status"]["business_composition"]["warnings"])


def test_write_json_cleans_non_json_safe_values(tmp_path):
    connector = RealDataConnector(cache_dir=tmp_path / "cache")
    output_path = tmp_path / "raw_safe.json"
    raw = {
        "date": date(2026, 5, 18),
        "datetime": datetime(2026, 5, 18, 10, 30, 5),
        "timestamp": pd.Timestamp("2026-05-18 11:00:00"),
        "np_int": np.int64(7),
        "np_float": np.float64(3.5),
        "np_bool": np.bool_(True),
        "nan": float("nan"),
        "np_nan": np.float64(np.nan),
        "np_inf": np.float64(np.inf),
        "nat": pd.NaT,
        "decimal": Decimal("12.34"),
        "nested": {
            date(2026, 5, 19): [
                np.int32(2),
                {"stamp": pd.Timestamp("2026-05-19"), "bad": np.float64(-np.inf)},
                {np.int64(1), np.int64(2)},
            ]
        },
    }

    connector._write_json(output_path, raw)
    loaded = json.loads(output_path.read_text(encoding="utf-8"))

    assert loaded["date"] == "2026-05-18"
    assert loaded["datetime"] == "2026-05-18T10:30:05"
    assert loaded["timestamp"].startswith("2026-05-18T11:00:00")
    assert loaded["np_int"] == 7
    assert loaded["np_float"] == 3.5
    assert loaded["np_bool"] is True
    assert loaded["nan"] is None
    assert loaded["np_nan"] is None
    assert loaded["np_inf"] is None
    assert loaded["nat"] is None
    assert loaded["decimal"] == 12.34
    assert loaded["nested"]["2026-05-19"][0] == 2
    assert loaded["nested"]["2026-05-19"][1]["stamp"].startswith("2026-05-19T00:00:00")
    assert loaded["nested"]["2026-05-19"][1]["bad"] is None


def test_v2_raw_output_can_be_consumed_by_pipeline(tmp_path):
    raw = AkshareConnector(tmp_path / "cache").fetch_to_raw_json("002050", force_refresh=True)

    result = FundamentalSkillPipeline().analyze_from_dict(raw)

    assert result.stock_code == "002050"
    assert result.schema_version == "fundamental.v1"
    assert validate_no_trading_instruction(result.model_dump_json()) == []
    for term in ["买入", "卖出", "加仓", "减仓", "清仓", "止损", "止盈", "目标价", "满仓", "梭哈"]:
        assert term not in json.dumps(raw, ensure_ascii=False)
        assert term not in result.model_dump_json()


def test_resource_stock_raw_json_contains_commodity_prices(tmp_path):
    raw = AkshareConnector(tmp_path / "cache").fetch_to_raw_json("000426", force_refresh=True)

    assert "commodity_prices" in raw["blocks"]
    assert {item["commodity_name"] for item in raw["blocks"]["commodity_prices"]} == {"silver", "tin"}
    assert raw["fetch_status"]["commodity_prices"]["missing_fields"] == []
    json.loads(json.dumps(raw, ensure_ascii=False, default=str))


def test_non_resource_stock_raw_json_omits_commodity_prices(tmp_path):
    raw = AkshareConnector(tmp_path / "cache").fetch_to_raw_json("002050", force_refresh=True)

    assert "commodity_prices" not in raw["blocks"]
    assert "commodity_prices" not in raw["fetch_status"]


def test_resource_raw_with_commodity_prices_can_be_consumed_by_pipeline(tmp_path):
    raw = AkshareConnector(tmp_path / "cache").fetch_to_raw_json("000426", force_refresh=True)

    result = FundamentalSkillPipeline().analyze_from_dict(raw)

    assert result.stock_code == "000426"
    assert result.schema_version == "fundamental.v1"
    assert validate_no_trading_instruction(result.model_dump_json()) == []
