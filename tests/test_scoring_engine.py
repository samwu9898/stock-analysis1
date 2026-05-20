# -*- coding: utf-8 -*-

from pathlib import Path

from src.fundamental_skill.analysis_context_builder import AnalysisContextBuilder
from src.fundamental_skill.data_adapter import FundamentalDataAdapter
from src.fundamental_skill.data_readiness_planner import DataReadinessPlanner
from src.fundamental_skill.framework_selector import FrameworkSelector
from src.fundamental_skill.scoring_engine import FundamentalScoringEngine
from src.fundamental_skill.stock_classifier import StockClassifier
from src.fundamental_skill.validators import validate_no_trading_instruction


FIXTURES = Path(__file__).parent / "fixtures"


def build_all(name: str):
    normalized = FundamentalDataAdapter().from_file(str(FIXTURES / name))
    classification = StockClassifier().classify(normalized)
    framework = FrameworkSelector().select(classification)
    readiness = DataReadinessPlanner().plan(normalized, classification, framework)
    context = AnalysisContextBuilder().build(normalized, classification, framework, readiness)
    scoring = FundamentalScoringEngine().score(normalized, classification, framework, readiness, context)
    return normalized, classification, framework, readiness, context, scoring


def dim(scoring, name):
    return next(item for item in scoring.dimension_scores if item.dimension_name == name)


def string_values(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from string_values(v)
    elif isinstance(value, list):
        for v in value:
            yield from string_values(v)
    elif isinstance(value, str):
        yield value


def test_resource_swing_good_scores_with_financial_evidence():
    _, classification, _, _, _, scoring = build_all("scoring_resource_swing_good.json")

    assert classification.strategy_type == "resource_swing"
    assert 0 <= scoring.weighted_total_score <= 100
    assert scoring.score_confidence != "low"
    assert dim(scoring, "financial_quality").positive_evidence


def test_resource_swing_weak_is_capped_by_context():
    _, _, _, readiness, _, scoring = build_all("scoring_resource_swing_weak.json")

    assert readiness.readiness_level == "weak"
    assert scoring.score_confidence == "low"
    assert scoring.weighted_total_score <= 70
    assert dim(scoring, "financial_quality").constrained_score <= 60
    assert any(r.risk_name in {"扣非净利润数据缺失", "经营现金流数据缺失"} for r in scoring.required_risks)


def test_growth_good_has_growth_evidence_and_beats_weak_resource_sample():
    _, classification, _, _, _, scoring = build_all("scoring_right_trend_growth_good.json")
    *_, weak_scoring = build_all("scoring_resource_swing_weak.json")

    assert classification.strategy_type == "right_trend_growth"
    evidence_text = " ".join(e.interpretation for e in dim(scoring, "financial_quality").positive_evidence)
    assert "营收增速" in evidence_text or "净利润增速" in evidence_text
    assert scoring.weighted_total_score > weak_scoring.weighted_total_score


def test_growth_missing_margin_applies_financial_constraint():
    *_, scoring = build_all("scoring_right_trend_growth_missing_margin.json")

    financial = dim(scoring, "financial_quality")
    assert financial.constrained_score <= 70
    assert any("financial_quality" in item for item in financial.applied_constraints)
    assert scoring.score_confidence != "high"


def test_semiconductor_missing_inventory_caps_industry_cycle():
    *_, scoring = build_all("scoring_semiconductor_missing_inventory.json")

    industry = dim(scoring, "industry_cycle")
    joined = " ".join(scoring.scoring_warnings + industry.applied_constraints + industry.missing_data_penalties)
    assert industry.constrained_score <= 70
    assert "inventory" in joined or "存货" in joined
    assert scoring.score_confidence != "high"


def test_stable_growth_weak_low_confidence_and_capped_financial_quality():
    *_, scoring = build_all("scoring_stable_growth_weak.json")

    assert scoring.score_confidence == "low"
    assert dim(scoring, "financial_quality").constrained_score <= 75
    assert scoring.weighted_total_score <= 70


def test_unknown_insufficient_total_and_data_quality_are_capped():
    *_, scoring = build_all("scoring_unknown_insufficient.json")

    assert scoring.weighted_total_score <= 50
    assert scoring.score_confidence == "low"
    assert dim(scoring, "data_quality").constrained_score <= 40


def test_context_constraint_forces_dimension_cap():
    *_, context, scoring = build_all("scoring_resource_swing_weak.json")

    constrained, max_allowed, applied = FundamentalScoringEngine().apply_context_constraints(
        "financial_quality", 95, context
    )

    assert max_allowed is not None
    assert constrained <= max_allowed
    assert applied


def test_risk_control_uses_required_risks_and_no_risk_penalty_dimension():
    *_, weak_scoring = build_all("scoring_resource_swing_weak.json")
    *_, good_scoring = build_all("scoring_resource_swing_good.json")

    assert dim(weak_scoring, "risk_control").constrained_score < dim(good_scoring, "risk_control").constrained_score
    assert all(item.dimension_name != "risk_penalty" for item in weak_scoring.dimension_scores)


def test_scoring_output_values_contain_no_prohibited_terms():
    prohibited = [
        "买入",
        "卖出",
        "加仓",
        "减仓",
        "清仓",
        "止损",
        "止盈",
        "目标价",
        "满仓",
        "梭哈",
        "supportive",
        "neutral",
        "negative",
        "fundamental_score",
    ]
    names = [
        "scoring_resource_swing_good.json",
        "scoring_resource_swing_weak.json",
        "scoring_right_trend_growth_good.json",
        "scoring_right_trend_growth_missing_margin.json",
        "scoring_semiconductor_missing_inventory.json",
        "scoring_stable_growth_weak.json",
        "scoring_unknown_insufficient.json",
    ]
    for name in names:
        *_, scoring = build_all(name)
        assert validate_no_trading_instruction(" ".join(string_values(scoring.model_dump()))) == []
        text_values = " ".join(string_values(scoring.model_dump()))
        for term in prohibited:
            assert term not in text_values


def test_advanced_manufacturing_risk_guard_constraints_apply():
    *_, context, scoring = build_all("pipeline_sanhua_mock.json")

    catalyst = dim(scoring, "catalyst_strength")
    risk_control = dim(scoring, "risk_control")
    valuation = dim(scoring, "valuation_reasonableness")

    assert context.strategy_type == "advanced_manufacturing_growth"
    assert catalyst.constrained_score <= 70
    assert risk_control.constrained_score <= 75
    assert valuation.constrained_score <= 70
    assert "机器人业务仍需订单和收入验证" in scoring.scoring_warnings
    assert "大客户收入占比和订单持续性需要验证" in scoring.scoring_warnings
    assert "估值可能已经反映部分成长预期" in scoring.scoring_warnings
