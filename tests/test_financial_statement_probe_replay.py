# -*- coding: utf-8 -*-

import importlib.util
import sys
from pathlib import Path

import pandas as pd


def _load_module(name: str):
    path = Path(__file__).resolve().parents[1] / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _probe_module():
    return _load_module("probe_financial_statement_fields")


def _replay_module():
    return _load_module("replay_financial_statement_probe")


def test_balance_sheet_detects_inventory():
    probe = _probe_module()
    rows = [{"指标": "存货", "20260331": 100.0}]
    matches = probe.detect_target_field_matches("mock_balance", rows, ["指标", "20260331"])
    assert matches["inventory"]["matched"] is True
    assert matches["inventory"]["value"] == 100.0
    assert matches["inventory"]["source_period"] == "20260331"


def test_balance_sheet_detects_accounts_receivable():
    probe = _probe_module()
    rows = [{"指标": "应收票据及应收账款", "20260331": 220.0}]
    matches = probe.detect_target_field_matches("mock_balance", rows, ["指标", "20260331"])
    assert matches["accounts_receivable"]["matched"] is True
    assert matches["accounts_receivable"]["value"] == 220.0
    assert matches["accounts_receivable"]["source_period"] == "20260331"


def test_balance_sheet_detects_contract_liabilities():
    probe = _probe_module()
    rows = [{"指标": "合同负债", "20260331": 330.0}]
    matches = probe.detect_target_field_matches("mock_balance", rows, ["指标", "20260331"])
    assert matches["contract_liabilities"]["matched"] is True
    assert matches["contract_liabilities"]["value"] == 330.0
    assert matches["contract_liabilities"]["source_period"] == "20260331"


def test_profit_sheet_detects_r_and_d_expense():
    probe = _probe_module()
    rows = [{"指标": "研发费用", "20260331": 44.0}]
    matches = probe.detect_target_field_matches("mock_profit", rows, ["指标", "20260331"])
    assert matches["r_and_d_expense"]["matched"] is True
    assert matches["r_and_d_expense"]["value"] == 44.0


def test_cash_flow_sheet_detects_capex():
    probe = _probe_module()
    rows = [{"指标": "购建固定资产、无形资产和其他长期资产支付的现金", "20260331": 55.0}]
    matches = probe.detect_target_field_matches("mock_cashflow", rows, ["指标", "20260331"])
    assert matches["capex"]["matched"] is True
    assert matches["capex"]["value"] == 55.0


def test_r_and_d_expense_ratio_derives_when_revenue_exists():
    probe = _probe_module()
    rows = [
        {"指标": "研发费用", "20260331": 25.0},
        {"指标": "营业总收入", "20260331": 100.0},
    ]
    matches = probe.detect_target_field_matches("mock_profit", rows, ["指标", "20260331"])
    assert matches["r_and_d_expense_ratio"]["matched"] is True
    assert matches["r_and_d_expense_ratio"]["value"] == 25.0


def test_capex_ratio_derives_when_revenue_exists():
    probe = _probe_module()
    rows = [
        {"指标": "购建固定资产、无形资产和其他长期资产支付的现金", "20260331": 10.0},
        {"指标": "营业总收入", "20260331": 200.0},
    ]
    matches = probe.detect_target_field_matches("mock_cashflow", rows, ["指标", "20260331"])
    assert matches["capex_ratio"]["matched"] is True
    assert matches["capex_ratio"]["value"] == 5.0


def test_ratio_not_derived_without_revenue():
    probe = _probe_module()
    rows = [{"指标": "研发费用", "20260331": 25.0}]
    matches = probe.detect_target_field_matches("mock_profit", rows, ["指标", "20260331"])
    assert matches["r_and_d_expense_ratio"]["matched"] is False
    assert "营业总收入" in matches["r_and_d_expense_ratio"]["notes"]


class FakeAkshareMissing:
    __version__ = "mock"


def test_missing_function_does_not_crash():
    probe = _probe_module()
    result = probe.attempt_function(FakeAkshareMissing(), "balance_sheet", "stock_balance_sheet_by_report_em", "002050", 5)
    assert result["success"] is False
    assert result["error"] == "function_not_found"


class FakeAkshareEmpty:
    __version__ = "mock"

    def stock_balance_sheet_by_report_em(self, symbol=None):
        return pd.DataFrame()


def test_empty_dataframe_does_not_crash():
    probe = _probe_module()
    result = probe.attempt_function(FakeAkshareEmpty(), "balance_sheet", "stock_balance_sheet_by_report_em", "002050", 5)
    assert result["success"] is True
    assert result["shape"] == [0, 0]
    assert result["target_field_matches"]["inventory"]["matched"] is False


def test_stock_financial_report_sina_wide_table_binds_report_date():
    probe = _probe_module()
    rows = [
        {
            "报告日": "20260331",
            "存货": 100.0,
            "应收账款": 220.0,
            "合同负债": 330.0,
        },
        {
            "报告日": "20251231",
            "存货": 90.0,
            "应收账款": 210.0,
            "合同负债": 310.0,
        },
    ]
    result = probe.summarize_result("balance_sheet", "stock_financial_report_sina", pd.DataFrame(rows), 5)
    assert "20260331" in result["detected_report_periods"]
    matches = result["target_field_matches"]
    assert matches["inventory"]["source_period"] == "20260331"
    assert matches["inventory"]["period_confidence"] == "high"
    assert matches["accounts_receivable"]["source_period"] == "20260331"
    assert matches["contract_liabilities"]["source_period"] == "20260331"
    assert matches["contract_liabilities"]["source_column_or_row"] == "合同负债"


def test_unknown_period_marks_low_confidence_without_crashing():
    probe = _probe_module()
    rows = [{"存货": 100.0}]
    matches = probe.detect_target_field_matches("mock_balance", rows, ["存货"])
    assert matches["inventory"]["matched"] is True
    assert matches["inventory"]["source_period"] == "unknown"
    assert matches["inventory"]["period_confidence"] == "low"


def test_replay_outputs_target_field_summary():
    probe_mod = _probe_module()
    replay = _replay_module()
    rows = [
        {"指标": "存货", "20260331": 100.0},
        {"指标": "营业总收入", "20260331": 1000.0},
    ]
    result = probe_mod.summarize_result("balance_sheet", "mock_balance", pd.DataFrame(rows), 5)
    probe = {
        "schema_version": "financial_statement_probe.v1",
        "stock_code": "002050",
        "generated_at": "2026-05-19T10:00:00",
        "akshare_version": "mock",
        "functions_attempted": ["mock_balance"],
        "target_fields": list(probe_mod.ALL_TARGET_FIELDS),
        "function_results": [result],
    }
    markdown = replay.render_markdown(probe)
    assert "Target Field Mapping Summary" in markdown
    assert "inventory" in markdown
    assert "Successful Functions" in markdown
    assert "source_period" in markdown
    assert "20260331" in markdown
