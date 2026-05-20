# -*- coding: utf-8 -*-

from pathlib import Path

from src.fundamental_skill.analysis_context_builder import AnalysisContextBuilder
from src.fundamental_skill.data_adapter import FundamentalDataAdapter
from src.fundamental_skill.data_readiness_planner import DataReadinessPlanner
from src.fundamental_skill.framework_selector import FrameworkSelector
from src.fundamental_skill.result_assembler import FundamentalResultAssembler
from src.fundamental_skill.scoring_engine import FundamentalScoringEngine
from src.fundamental_skill.stock_classifier import StockClassifier
from src.fundamental_skill.validators import assert_valid_result, validate_no_trading_instruction


FIXTURES = Path(__file__).parent / "fixtures"
PROHIBITED_TERMS = ["买入", "卖出", "加仓", "减仓", "清仓", "止损", "止盈", "目标价", "满仓", "梭哈"]
ALLOWED_ACTION_HINTS = {"需要交易员重新评估", "需要暂停基本面支持判断", "需要更新基本面分析"}


def build_result(name: str):
    normalized = FundamentalDataAdapter().from_file(str(FIXTURES / name))
    classification = StockClassifier().classify(normalized)
    framework = FrameworkSelector().select(classification)
    readiness = DataReadinessPlanner().plan(normalized, classification, framework)
    context = AnalysisContextBuilder().build(normalized, classification, framework, readiness)
    scoring = FundamentalScoringEngine().score(normalized, classification, framework, readiness, context)
    result = FundamentalResultAssembler().assemble(
        normalized, classification, framework, readiness, context, scoring
    )
    return normalized, classification, framework, readiness, context, scoring, result


def dim(scoring, name):
    return next(item for item in scoring.dimension_scores if item.dimension_name == name)


def dumped(result) -> str:
    return result.model_dump_json()


def test_resource_swing_good_assembles_valid_result():
    *_, result = build_result("result_resource_swing_good.json")

    assert result.status in {"supportive", "neutral"}
    assert result.confidence in {"high", "medium"}
    assert 0 <= result.fundamental_score <= 100
    assert result.risk_flags
    assert result.must_track_indicators
    assert_valid_result(result)


def test_resource_swing_good_missing_commodity_price_caps_confidence():
    *_, result = build_result("result_resource_swing_good.json")

    assert result.status in {"supportive", "neutral"}
    assert result.confidence != "high"
    assert any("商品价格数据缺失" in risk.name for risk in result.risk_flags)
    assert any(term in result.trader_summary for term in ["商品价格", "价格数据", "周期判断受限"])


def test_resource_swing_weak_is_low_confidence_and_keeps_data_risks():
    *_, result = build_result("result_resource_swing_weak.json")

    assert result.status in {"neutral", "insufficient_data", "negative"}
    assert result.confidence == "low"
    assert result.fundamental_score <= 70
    risk_text = " ".join(risk.name for risk in result.risk_flags)
    assert any(term in risk_text for term in ["扣非净利润", "经营现金流", "商品价格"])
    assert validate_no_trading_instruction(result.trader_summary) == []


def test_growth_good_keeps_growth_drivers_and_conservative_valuation():
    *_, classification, _, _, _, _, result = build_result("result_right_trend_growth_good.json")

    assert classification.strategy_type == "right_trend_growth"
    driver_text = " ".join(result.key_drivers)
    assert any(term in driver_text for term in ["营收", "利润", "景气"])
    valuation_text = " ".join(
        value or ""
        for value in [
            result.valuation_view.valuation_level,
            result.valuation_view.valuation_method,
            result.valuation_view.peer_comparison,
            result.valuation_view.historical_percentile,
        ]
    )
    assert "低估" not in valuation_text
    assert "便宜" not in valuation_text
    assert_valid_result(result)


def test_growth_missing_margin_limits_confidence_and_flags_margin_risk():
    *_, result = build_result("result_right_trend_growth_missing_margin.json")

    assert result.confidence != "high"
    assert "毛利率改善" not in (result.financial_quality.margin_trend or "")
    assert "毛利率改善明显" not in " ".join(result.key_drivers)
    assert "盈利能力持续提升" not in " ".join(result.key_drivers)
    risk_text = " ".join(risk.name for risk in result.risk_flags)
    assert "毛利率" in risk_text or "盈利能力验证不足" in risk_text


def test_semiconductor_missing_inventory_does_not_confirm_inventory_cycle():
    *_, result = build_result("result_semiconductor_missing_inventory.json")

    assert "库存周期健康" not in (result.industry_cycle.industry_trend or "")
    assert "半导体周期反转" not in (result.industry_cycle.industry_trend or "")
    assert "库存周期健康" not in " ".join(result.key_drivers)
    risk_text = " ".join(risk.name for risk in result.risk_flags)
    assert "存货数据缺失" in risk_text
    assert result.confidence != "high"


def test_stable_growth_weak_keeps_low_confidence_and_cashflow_risks():
    *_, result = build_result("result_stable_growth_weak.json")

    assert result.confidence == "low"
    assert "现金流稳健" not in (result.financial_quality.cashflow_quality or "")
    risk_text = " ".join(risk.name for risk in result.risk_flags)
    assert "ROE" in risk_text or "经营现金流" in risk_text


def test_unknown_sparse_becomes_insufficient_data():
    *_, result = build_result("result_unknown_insufficient.json")

    assert result.status == "insufficient_data"
    assert result.confidence == "low"
    assert result.fundamental_score <= 50
    assert "数据不足" in result.trader_summary


def test_status_priority_and_weak_low_confidence_do_not_become_supportive():
    *_, unknown_result = build_result("result_unknown_insufficient.json")
    *_, weak_result = build_result("result_resource_swing_weak.json")

    assert unknown_result.status == "insufficient_data"
    assert weak_result.confidence == "low"
    assert weak_result.status != "supportive"


def test_resource_core_missing_commodity_price_caps_confidence_and_cycle():
    *_, result = build_result("result_resource_core_missing_commodity.json")

    assert result.strategy_type == "resource_core"
    assert result.confidence != "high"
    assert result.industry_cycle.cycle_position != "upcycle"
    assert any("商品价格数据缺失" in risk.name for risk in result.risk_flags)


def test_supportive_medium_confidence_mentions_key_validation_items():
    *_, result = build_result("result_resource_swing_good.json")

    if result.status == "supportive" and result.confidence == "medium":
        assert "关键验证项" in result.trader_summary or "数据限制" in result.trader_summary


def test_high_severity_data_missing_caps_confidence_below_high():
    *_, result = build_result("result_resource_swing_weak.json")

    assert any(risk.severity == "high" and "数据缺失" in risk.name for risk in result.risk_flags)
    assert result.confidence != "high"


def test_invalidation_action_hints_are_allowed_and_safe():
    *_, result = build_result("result_resource_swing_good.json")

    for condition in result.invalidation_conditions:
        assert condition.action_hint_for_trader in ALLOWED_ACTION_HINTS
        assert validate_no_trading_instruction(condition.action_hint_for_trader) == []


def test_all_result_outputs_exclude_trading_instruction_terms():
    names = [
        "result_resource_swing_good.json",
        "result_resource_swing_weak.json",
        "result_right_trend_growth_good.json",
        "result_right_trend_growth_missing_margin.json",
        "result_semiconductor_missing_inventory.json",
        "result_stable_growth_weak.json",
        "result_unknown_insufficient.json",
    ]
    for name in names:
        *_, result = build_result(name)
        assert validate_no_trading_instruction(dumped(result)) == []
        for term in PROHIBITED_TERMS:
            assert term not in dumped(result)
        assert_valid_result(result)
