# -*- coding: utf-8 -*-

import json
from pathlib import Path

from src.fundamental_skill.data_adapter import FundamentalDataAdapter
from src.fundamental_skill.raw_schema import NormalizedFundamentalInput
from src.fundamental_skill.schema import FundamentalAnalysisResult
from src.fundamental_skill.validators import validate_no_trading_instruction


FIXTURES = Path(__file__).parent / "fixtures"


def test_from_file_reads_raw_with_meta_blocks():
    result = FundamentalDataAdapter().from_file(str(FIXTURES / "raw_with_meta_blocks.json"))

    assert isinstance(result, NormalizedFundamentalInput)
    assert result.stock_code == "000426"


def test_from_dict_reads_dict():
    raw = json.loads((FIXTURES / "raw_with_meta_blocks.json").read_text(encoding="utf-8"))

    result = FundamentalDataAdapter().from_dict(raw)

    assert result.stock_name == "兴业银锡"


def test_raw_with_meta_blocks_maps_core_fields():
    result = FundamentalDataAdapter().from_file(str(FIXTURES / "raw_with_meta_blocks.json"))

    assert result.stock_code == "000426"
    assert result.stock_name == "兴业银锡"
    assert result.basic_info.industry == "有色金属"
    assert len(result.financial_metrics) == 2
    assert result.financial_metrics[0].revenue == 4200000000


def test_adapter_maps_contract_liabilities_from_financial_block():
    raw = {
        "meta": {"code": "002371", "generated_at": "2026-05-19T00:00:00"},
        "blocks": {
            "basic_info": [{"stock_code": "002371", "stock_name": "北方华创"}],
            "financial_indicator": [
                {
                    "period": "20260331",
                    "inventory": 28602898183.2,
                    "accounts_receivable": 8780279745.35,
                    "contract_liabilities": 4202521948.54,
                }
            ],
        },
    }

    result = FundamentalDataAdapter().from_dict(raw)

    metric = result.financial_metrics[0]
    assert metric.inventory == 28602898183.2
    assert metric.accounts_receivable == 8780279745.35
    assert metric.contract_liabilities == 4202521948.54


def test_blocks_only_does_not_crash_and_records_missing_meta():
    result = FundamentalDataAdapter().from_file(str(FIXTURES / "raw_blocks_only.json"))

    assert result.stock_code == "000426"
    assert "missing_meta" in result.adapter_warnings
    assert "meta" in result.missing_fields


def test_unknown_structure_does_not_crash_and_records_unknown():
    result = FundamentalDataAdapter().from_file(str(FIXTURES / "raw_unknown_structure.json"))

    assert result.stock_code == "UNKNOWN"
    assert "unknown_raw_structure" in result.missing_fields
    assert any("unknown_raw_structure" in warning for warning in result.adapter_warnings)


def test_missing_financials_records_missing_field():
    result = FundamentalDataAdapter().from_file(str(FIXTURES / "raw_missing_financials.json"))

    assert "financial_metrics" in result.missing_fields


def test_block_status_records_each_block():
    result = FundamentalDataAdapter().from_file(str(FIXTURES / "raw_with_meta_blocks.json"))
    names = {status.block_name for status in result.block_status}

    assert {"basic_info", "financial_indicator", "valuation", "business_composition", "news"} <= names
    assert all(status.row_count is not None for status in result.block_status)


def test_data_sources_not_empty():
    result = FundamentalDataAdapter().from_file(str(FIXTURES / "raw_with_meta_blocks.json"))

    assert result.data_sources


def test_adapter_does_not_output_final_analysis_result():
    result = FundamentalDataAdapter().from_file(str(FIXTURES / "raw_with_meta_blocks.json"))

    assert not isinstance(result, FundamentalAnalysisResult)
    assert not hasattr(result, "status")
    assert not hasattr(result, "fundamental_score")


def test_adapter_output_fixture_contains_no_trading_instruction_terms():
    result = FundamentalDataAdapter().from_file(str(FIXTURES / "raw_with_meta_blocks.json"))
    dumped = result.model_dump_json()

    assert validate_no_trading_instruction(dumped) == []
