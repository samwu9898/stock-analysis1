# -*- coding: utf-8 -*-

from pathlib import Path

from src.fundamental_skill.analysis_context_builder import AnalysisContextBuilder
from src.fundamental_skill.analysis_context_schema import PROHIBITED_CONTEXT_TERMS
from src.fundamental_skill.data_adapter import FundamentalDataAdapter
from src.fundamental_skill.data_readiness_planner import DataReadinessPlanner
from src.fundamental_skill.framework_selector import FrameworkSelector
from src.fundamental_skill.stock_classifier import StockClassifier
from src.fundamental_skill.validators import validate_no_trading_instruction


FIXTURES = Path(__file__).parent / "fixtures"


def build_context(name: str):
    normalized = FundamentalDataAdapter().from_file(str(FIXTURES / name))
    classification = StockClassifier().classify(normalized)
    framework = FrameworkSelector().select(classification)
    readiness = DataReadinessPlanner().plan(normalized, classification, framework)
    return AnalysisContextBuilder().build(normalized, classification, framework, readiness)


def constraint_map(context):
    return {item.scoring_dimension: item.max_score for item in context.scoring_constraints}


def claim_types(context):
    return {item.claim_type for item in context.prohibited_claims}


def risk_names(context):
    return {item.risk_name for item in context.required_risks}


def dimensions_by_permission(context):
    out = {}
    for item in context.allowed_dimensions + context.restricted_dimensions + context.blocked_dimensions:
        out[item.dimension_name] = item.permission
    return out


def test_resource_swing_weak_context_limits_confidence_and_claims():
    context = build_context("context_resource_swing_weak.json")

    assert context.max_overall_confidence == "low"
    assert {"扣非净利润数据缺失", "经营现金流数据缺失", "商品价格数据缺失"} <= risk_names(context)
    assert {
        "sustainable_profit_growth",
        "cashflow_quality_strong",
        "commodity_price_benefit_confirmed",
    } <= claim_types(context)
    assert dimensions_by_permission(context)["financial_quality"] in {"restricted", "blocked"}
    assert constraint_map(context)["financial_quality"] <= 60


def test_growth_warning_margin_limits_context():
    context = build_context("context_right_trend_growth_warning.json")

    assert context.max_overall_confidence in {"low", "medium"}
    assert "margin_improvement_confirmed" in claim_types(context)
    assert constraint_map(context)["financial_quality"] <= 70


def test_semiconductor_inventory_missing_limits_cycle():
    context = build_context("context_semiconductor_warning.json")
    permissions = dimensions_by_permission(context)

    assert "inventory_cycle_healthy" in claim_types(context)
    assert permissions["industry_cycle"] in {"allowed_with_low_confidence", "restricted", "blocked"}
    assert constraint_map(context)["industry_cycle"] <= 70


def test_stable_growth_weak_limits_financial_quality():
    context = build_context("context_stable_growth_weak.json")
    permissions = dimensions_by_permission(context)

    assert context.max_overall_confidence == "low"
    assert {"ROE 数据缺失", "经营现金流数据缺失"} <= risk_names(context)
    assert not (
        permissions["financial_quality"] == "allowed"
        and any(item.dimension_name == "financial_quality" and item.max_confidence == "high" for item in context.allowed_dimensions)
    )


def test_unknown_insufficient_context_has_warnings_and_restrictions():
    context = build_context("context_unknown_insufficient.json")

    assert context.overall_context_quality == "insufficient"
    assert context.max_overall_confidence == "low"
    assert context.context_warnings
    assert context.blocked_dimensions or context.restricted_dimensions


def test_scoring_constraints_merge_take_lowest_score():
    context = build_context("context_resource_swing_weak.json")

    assert constraint_map(context)["financial_quality"] == 60


def test_prohibited_claims_are_deduplicated():
    context = build_context("context_resource_swing_weak.json")
    types = [item.claim_type for item in context.prohibited_claims]

    assert len(types) == len(set(types))


def test_required_risks_are_deduplicated():
    context = build_context("context_resource_swing_weak.json")
    names = [item.risk_name for item in context.required_risks]

    assert len(names) == len(set(names))


def test_safe_summary_contains_no_trading_instruction_terms():
    context = build_context("context_resource_swing_weak.json")

    assert validate_no_trading_instruction(context.safe_summary_for_next_stage) == []


def test_all_context_outputs_exclude_prohibited_terms():
    names = [
        "context_resource_swing_weak.json",
        "context_right_trend_growth_warning.json",
        "context_semiconductor_warning.json",
        "context_stable_growth_weak.json",
        "context_unknown_insufficient.json",
    ]
    for name in names:
        dumped = build_context(name).model_dump_json()
        assert validate_no_trading_instruction(dumped) == []
        for term in PROHIBITED_CONTEXT_TERMS:
            assert term not in dumped


def test_advanced_manufacturing_unverified_risks_and_constraints():
    context = build_context("pipeline_sanhua_mock.json")
    constraints = constraint_map(context)
    risks = risk_names(context)

    assert context.strategy_type == "advanced_manufacturing_growth"
    assert "机器人业务兑现验证不足" in risks
    assert "大客户依赖验证不足" in risks
    assert "估值预期消化风险" in risks
    assert constraints["catalyst_strength"] <= 70
    assert constraints["risk_control"] <= 75
    assert constraints["valuation_reasonableness"] <= 70
    assert "robot_business_confirmed" in claim_types(context)
    assert "customer_demand_confirmed" in claim_types(context)
