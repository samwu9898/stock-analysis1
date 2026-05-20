# -*- coding: utf-8 -*-

from pathlib import Path

from src.fundamental_skill.data_adapter import FundamentalDataAdapter
from src.fundamental_skill.data_readiness_planner import DataReadinessPlanner
from src.fundamental_skill.framework_selector import FrameworkSelector
from src.fundamental_skill.readiness_schema import FieldRequirement
from src.fundamental_skill.stock_classifier import StockClassifier
from src.fundamental_skill.validators import validate_no_trading_instruction


FIXTURES = Path(__file__).parent / "fixtures"


def build_plan(name: str):
    normalized = FundamentalDataAdapter().from_file(str(FIXTURES / name))
    classification = StockClassifier().classify(normalized)
    framework = FrameworkSelector().select(classification)
    return DataReadinessPlanner().plan(normalized, classification, framework)


def test_advanced_manufacturing_requirements_can_be_read():
    planner = DataReadinessPlanner()

    requirements = planner.requirements["advanced_manufacturing_growth"]["required_fields"]
    fields = {item["field_name"] for item in requirements}

    assert "financial_metrics.gross_margin" in fields
    assert "financial_metrics.accounts_receivable" in fields
    assert "business_composition.segments" in fields


def test_resource_swing_complete_is_sufficient_or_usable():
    plan = build_plan("readiness_resource_swing_complete.json")

    assert plan.readiness_level in {"sufficient", "usable_with_warnings"}


def test_resource_swing_missing_cashflow_and_deducted_profit_are_critical():
    plan = build_plan("readiness_resource_swing_missing_cashflow.json")

    assert plan.readiness_score <= 60
    assert plan.readiness_level == "weak"
    assert "financial_metrics.operating_cashflow" in plan.critical_missing_fields
    assert "financial_metrics.deducted_net_profit" in plan.critical_missing_fields
    blockers = " ".join(plan.analysis_blockers)
    assert "扣非净利润" in blockers
    assert "经营现金流" in blockers


def test_growth_missing_margin_warns_scorer_about_financial_quality_or_margin():
    plan = build_plan("readiness_right_trend_growth_missing_margin.json")
    text = " ".join(plan.notes_for_scorer)

    assert plan.readiness_level != "sufficient"
    assert "financial_quality" in text or "毛利率" in text


def test_semiconductor_missing_inventory_creates_blocker_or_high_impact():
    plan = build_plan("readiness_semiconductor_missing_inventory.json")
    text = " ".join(plan.analysis_blockers + plan.confidence_penalty_reasons)

    assert plan.readiness_score <= 85
    assert plan.readiness_level != "sufficient"
    assert "存货" in text or "inventory" in text


def test_contract_liabilities_resolves_only_as_partial_proxy():
    normalized = FundamentalDataAdapter().from_dict(
        {
            "meta": {"code": "002371", "generated_at": "2026-05-19T00:00:00"},
            "blocks": {
                "basic_info": [{"stock_code": "002371", "stock_name": "北方华创", "industry": "半导体设备"}],
                "financial_indicator": [{"period": "20260331", "contract_liabilities": 4202521948.54}],
            },
        }
    )
    planner = DataReadinessPlanner()
    item = planner._check_requirement(
        normalized,
        FieldRequirement(
            field_name="orders_or_contract_liabilities",
            display_name="订单 / 合同负债",
            category="financial",
            importance="high",
            reason="订单可见度 proxy",
            expected_location=["financial_metrics.contract_liabilities"],
            affects_analysis=["business_quality"],
        ),
    )

    assert item.status == "partial"
    assert "proxy" in item.missing_reason
    assert item.evidence_path == "financial_metrics[0].contract_liabilities"


def test_stable_growth_missing_roe_and_cashflow_not_sufficient():
    plan = build_plan("readiness_stable_growth_missing_roe.json")

    assert plan.readiness_level in {"weak", "insufficient"}
    assert "financial_metrics.roe" in plan.critical_missing_fields
    assert "financial_metrics.operating_cashflow" in plan.critical_missing_fields


def test_unknown_sparse_highest_is_weak():
    plan = build_plan("readiness_unknown_sparse.json")

    assert plan.strategy_type == "unknown"
    assert plan.readiness_level in {"weak", "insufficient"}
    if plan.readiness_score < 40:
        assert plan.readiness_level == "insufficient"


def test_empty_financial_metrics_caps_level_and_adds_blocker():
    plan = build_plan("raw_missing_financials.json")
    text = " ".join(plan.analysis_blockers)

    assert plan.readiness_level in {"weak", "insufficient"}
    assert "财务数据不足" in text


def test_critical_business_composition_missing_caps_level_and_recommends_collection():
    plan = build_plan("raw_missing_financials.json")

    assert plan.readiness_level != "sufficient"
    assert any("主营业务构成" in item or "主营构成" in item for item in plan.recommended_data_to_collect)


def test_external_commodity_prices_missing_does_not_crash():
    plan = build_plan("readiness_resource_swing_complete.json")

    assert "external.commodity_prices" in plan.high_priority_missing_fields
    assert plan.readiness_level != "insufficient"


def test_readiness_score_between_0_and_100():
    plan = build_plan("readiness_resource_swing_missing_cashflow.json")

    assert 0 <= plan.readiness_score <= 100


def test_plan_does_not_contain_final_status_words():
    plan = build_plan("readiness_resource_swing_missing_cashflow.json")
    dumped = plan.model_dump_json()

    assert "supportive" not in dumped
    assert "neutral" not in dumped
    assert "negative" not in dumped


def test_plan_contains_no_trading_instruction_terms():
    plan = build_plan("readiness_resource_swing_missing_cashflow.json")

    assert validate_no_trading_instruction(plan.model_dump_json()) == []


def test_all_fixture_plans_contain_no_trading_instruction_terms():
    names = [
        "readiness_resource_swing_complete.json",
        "readiness_resource_swing_missing_cashflow.json",
        "readiness_right_trend_growth_missing_margin.json",
        "readiness_semiconductor_missing_inventory.json",
        "readiness_stable_growth_missing_roe.json",
        "readiness_unknown_sparse.json",
    ]
    for name in names:
        assert validate_no_trading_instruction(build_plan(name).model_dump_json()) == []
