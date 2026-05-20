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
    return _load_module("probe_rd_capex_fields")


def _replay_module():
    return _load_module("replay_rd_capex_probe")


def test_detects_r_and_d_expense():
    probe = _probe_module()
    rows = [{"指标": "研发费用", "20260331": 44.0}]
    matches = probe.detect_target_field_matches("mock_profit", "profit_sheet", rows, ["指标", "20260331"])
    assert matches["r_and_d_expense"]["matched"] is True
    assert matches["r_and_d_expense"]["value"] == 44.0
    assert matches["r_and_d_expense"]["source_period"] == "20260331"


def test_detects_capex():
    probe = _probe_module()
    rows = [{"指标": "购建固定资产、无形资产和其他长期资产支付的现金", "20260331": 55.0}]
    matches = probe.detect_target_field_matches("mock_cashflow", "cash_flow_sheet", rows, ["指标", "20260331"])
    assert matches["capex"]["matched"] is True
    assert matches["capex"]["value"] == 55.0
    assert matches["capex"]["source_period"] == "20260331"


def test_r_and_d_expense_ratio_derives_with_same_period_revenue():
    probe = _probe_module()
    rows = [
        {"指标": "研发费用", "20260331": 25.0},
        {"指标": "营业总收入", "20260331": 100.0},
    ]
    matches = probe.detect_target_field_matches("mock_profit", "profit_sheet", rows, ["指标", "20260331"])
    assert matches["r_and_d_expense_ratio"]["matched"] is True
    assert matches["r_and_d_expense_ratio"]["value"] == 25.0
    assert matches["r_and_d_expense_ratio"]["source_period"] == "20260331"


def test_capex_ratio_derives_with_same_period_revenue():
    probe = _probe_module()
    rows = [
        {"指标": "购建固定资产、无形资产和其他长期资产支付的现金", "20260331": 10.0},
        {"指标": "营业总收入", "20260331": 200.0},
    ]
    matches = probe.detect_target_field_matches("mock_cashflow", "cash_flow_sheet", rows, ["指标", "20260331"])
    assert matches["capex_ratio"]["matched"] is True
    assert matches["capex_ratio"]["value"] == 5.0
    assert matches["capex_ratio"]["source_period"] == "20260331"


def test_different_periods_do_not_derive_ratio():
    probe = _probe_module()
    rows = [
        {"指标": "研发费用", "20260331": 25.0, "20251231": None},
        {"指标": "营业总收入", "20260331": None, "20251231": 100.0},
    ]
    matches = probe.detect_target_field_matches("mock_profit", "profit_sheet", rows, ["指标", "20260331", "20251231"])
    assert matches["r_and_d_expense"]["source_period"] == "20260331"
    assert matches["r_and_d_expense_ratio"]["matched"] is False
    assert "period mismatch" in matches["r_and_d_expense_ratio"]["notes"]


def test_missing_revenue_does_not_derive_ratio():
    probe = _probe_module()
    rows = [{"指标": "研发费用", "20260331": 25.0}]
    matches = probe.detect_target_field_matches("mock_profit", "profit_sheet", rows, ["指标", "20260331"])
    assert matches["r_and_d_expense_ratio"]["matched"] is False
    assert "revenue is missing" in matches["r_and_d_expense_ratio"]["notes"]


def test_marks_cumulative_or_single_quarter():
    probe = _probe_module()
    rows = [{"指标": "研发费用", "20260331": 25.0}]
    report_matches = probe.detect_target_field_matches("stock_profit_sheet_by_report_em", "profit_sheet", rows, ["指标", "20260331"])
    quarter_matches = probe.detect_target_field_matches("stock_profit_sheet_by_quarterly_em", "profit_sheet", rows, ["指标", "20260331"])
    assert report_matches["r_and_d_expense"]["cumulative_or_single_quarter"] == "cumulative"
    assert quarter_matches["r_and_d_expense"]["cumulative_or_single_quarter"] == "single_quarter"


def test_uncertain_unit_marks_low_confidence():
    probe = _probe_module()
    rows = [{"指标": "研发费用", "20260331": 25.0}]
    matches = probe.detect_target_field_matches("mock_profit", "profit_sheet", rows, ["指标", "20260331"])
    assert matches["r_and_d_expense"]["unit"] == "raw_statement_unit"
    assert matches["r_and_d_expense"]["unit_confidence"] == "low"


class FakeAkshareMissing:
    __version__ = "mock"


def test_missing_function_does_not_crash():
    probe = _probe_module()
    result = probe.attempt_function(FakeAkshareMissing(), "profit_sheet", "stock_profit_sheet_by_report_em", "002050", 5)
    assert result["success"] is False
    assert result["error"] == "function_not_found"


class FakeAkshareEmpty:
    __version__ = "mock"

    def stock_profit_sheet_by_report_em(self, symbol=None):
        return pd.DataFrame()


def test_empty_dataframe_does_not_crash():
    probe = _probe_module()
    result = probe.attempt_function(FakeAkshareEmpty(), "profit_sheet", "stock_profit_sheet_by_report_em", "002050", 5)
    assert result["success"] is True
    assert result["shape"] == [0, 0]
    assert result["target_field_matches"]["r_and_d_expense"]["matched"] is False


def test_replay_outputs_v2_3_recommendation():
    probe_mod = _probe_module()
    replay = _replay_module()
    rows = [
        {"指标": "研发费用", "20260331": 25.0},
        {"指标": "营业总收入", "20260331": 100.0},
        {"指标": "购建固定资产、无形资产和其他长期资产支付的现金", "20260331": 10.0},
    ]
    result = probe_mod.summarize_result("profit_sheet", "mock_profit", pd.DataFrame(rows), 5)
    probe = {
        "schema_version": "rd_capex_probe.v1",
        "stock_code": "002050",
        "generated_at": "2026-05-20T10:00:00",
        "akshare_version": "mock",
        "functions_attempted": ["mock_profit"],
        "target_fields": list(probe_mod.ALL_TARGET_FIELDS),
        "function_results": [result],
    }
    markdown = replay.render_markdown(probe)
    assert "v2.3 Recommendation" in markdown
    assert "Target Field Mapping Summary" in markdown
    assert "Derived Field Summary" in markdown
    assert "r_and_d_expense_ratio" in markdown
