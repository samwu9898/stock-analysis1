# -*- coding: utf-8 -*-

import json
from pathlib import Path

from src.fundamental_skill.pipeline import FundamentalSkillPipeline
from src.fundamental_skill.schema import FundamentalAnalysisResult
from src.fundamental_skill.validators import assert_valid_result, validate_no_trading_instruction


FIXTURES = Path(__file__).parent / "fixtures"
PROHIBITED_TERMS = ["买入", "卖出", "加仓", "减仓", "清仓", "止损", "止盈", "目标价", "满仓", "梭哈"]


def test_analyze_from_file_runs_complete_pipeline():
    pipeline = FundamentalSkillPipeline()

    result = pipeline.analyze_from_file(str(FIXTURES / "result_resource_swing_good.json"))

    assert isinstance(result, FundamentalAnalysisResult)
    assert result.stock_code == "000426"
    assert pipeline.last_trace
    assert pipeline.last_trace["final_status"] == result.status
    assert pipeline.last_trace["final_confidence"] == result.confidence
    assert_valid_result(result)


def test_analyze_from_dict_runs_complete_pipeline():
    payload = json.loads((FIXTURES / "result_right_trend_growth_good.json").read_text(encoding="utf-8"))
    pipeline = FundamentalSkillPipeline()

    result = pipeline.analyze_from_dict(payload)

    assert isinstance(result, FundamentalAnalysisResult)
    assert result.strategy_type == "right_trend_growth"
    assert pipeline.last_trace
    assert pipeline.last_trace["weighted_total_score"] >= 0
    assert_valid_result(result)


def test_output_path_writes_json(tmp_path):
    pipeline = FundamentalSkillPipeline()
    output_path = tmp_path / "fundamental.json"

    result = pipeline.analyze_from_file(str(FIXTURES / "result_resource_swing_good.json"), output_path=str(output_path))

    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert saved["stock_code"] == result.stock_code
    assert saved["schema_version"] == "fundamental.v1"


def test_pipeline_sanhua_mock_generates_valid_result():
    pipeline = FundamentalSkillPipeline()

    result = pipeline.analyze_from_file(str(FIXTURES / "pipeline_sanhua_mock.json"))

    assert isinstance(result, FundamentalAnalysisResult)
    assert result.stock_code == "002050"
    assert result.stock_name == "三花智控"
    assert result.strategy_type == "advanced_manufacturing_growth"
    assert pipeline.last_trace
    assert pipeline.last_trace["stock_code"] == "002050"
    assert_valid_result(result)


def test_pipeline_sanhua_tracks_advanced_manufacturing_indicators():
    pipeline = FundamentalSkillPipeline()

    result = pipeline.analyze_from_file(str(FIXTURES / "pipeline_sanhua_mock.json"))
    indicator_text = " ".join(item.name for item in result.must_track_indicators)

    assert "机器人相关业务收入或订单" in indicator_text
    assert "汽车热管理业务收入" in indicator_text or "汽车热管理业务收入或订单" in indicator_text
    assert "毛利率" in indicator_text
    assert "经营现金流" in indicator_text
    assert "应收账款" in indicator_text
    assert "仍需订单和收入验证" in result.trader_summary


def test_pipeline_sanhua_advanced_manufacturing_risk_guard():
    pipeline = FundamentalSkillPipeline()

    result = pipeline.analyze_from_file(str(FIXTURES / "pipeline_sanhua_mock.json"))
    risk_names = {risk.name for risk in result.risk_flags}

    assert "机器人业务兑现验证不足" in risk_names
    assert "大客户依赖验证不足" in risk_names
    assert "估值预期消化风险" in risk_names
    assert result.confidence != "high"
    assert "机器人" in result.trader_summary
    assert "订单" in result.trader_summary
    assert "收入验证" in result.trader_summary
    driver_text = " ".join(result.key_drivers)
    assert "机器人业务已经兑现" not in driver_text
    assert "机器人业务成为主要增长来源" not in driver_text
    assert "人形机器人收入确定放量" not in driver_text
    assert "特斯拉订单确定增长" not in driver_text


def test_pipeline_outputs_contain_no_trading_instruction_terms():
    pipeline = FundamentalSkillPipeline()
    names = [
        "result_resource_swing_good.json",
        "result_resource_swing_weak.json",
        "pipeline_sanhua_mock.json",
    ]

    for name in names:
        result = pipeline.analyze_from_file(str(FIXTURES / name))
        dumped = result.model_dump_json()
        assert validate_no_trading_instruction(dumped) == []
        for term in PROHIBITED_TERMS:
            assert term not in dumped


def test_pipeline_module_does_not_call_llm_or_akshare():
    source = Path("src/fundamental_skill/pipeline.py").read_text(encoding="utf-8").lower()

    assert "akshare" not in source
    assert "openai" not in source
    assert "llm" not in source
