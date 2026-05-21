# -*- coding: utf-8 -*-

from pathlib import Path

from src.fundamental_skill.data_adapter import FundamentalDataAdapter
from src.fundamental_skill.data_readiness_planner import DataReadinessPlanner
from src.fundamental_skill.classification_schema import StockClassificationResult
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


def build_ai_datacenter_plan(sub_type: str | None, warnings: list[str] | None = None):
    normalized = FundamentalDataAdapter().from_dict(
        {
            "meta": {
                "code": "999001",
                "stock_name": "AI Datacenter Subtype Fixture",
                "generated_at": "2026-05-21T00:00:00",
            },
            "blocks": {
                "basic_info": [
                    {
                        "stock_code": "999001",
                        "stock_name": "AI Datacenter Subtype Fixture",
                        "industry": "AI datacenter infrastructure",
                        "main_business": "IDC AIDC data center UPS power liquid cooling infrastructure",
                    }
                ],
                "financial_indicator": [
                    {
                        "period": "2025-12-31",
                        "revenue": 1000000000,
                        "net_profit": 100000000,
                        "gross_margin": 30,
                        "operating_cashflow": 80000000,
                        "accounts_receivable": 50000000,
                        "contract_liabilities": 30000000,
                        "capex": 120000000,
                        "inventory": 40000000,
                    }
                ],
                "valuation": [{"pe_ttm": 25, "pb": 3, "ps": 5}],
                "business_composition": [
                    {
                        "period": "2025-12-31",
                        "segment_name": "IDC AIDC data center operation revenue",
                        "revenue_ratio": 50,
                    },
                    {
                        "period": "2025-12-31",
                        "segment_name": "datacenter UPS power infrastructure revenue",
                        "revenue_ratio": 30,
                    },
                    {
                        "period": "2025-12-31",
                        "segment_name": "datacenter liquid cooling precision thermal revenue",
                        "revenue_ratio": 20,
                    },
                    {
                        "period": "2025-12-31",
                        "segment_name": "energy storage photovoltaic boundary revenue",
                        "revenue_ratio": 10,
                    },
                    {
                        "period": "2025-12-31",
                        "segment_name": "ordinary HVAC industrial air conditioning boundary revenue",
                        "revenue_ratio": 15,
                    },
                ],
            },
        }
    )
    classification = StockClassificationResult(
        stock_code="999001",
        stock_name="AI Datacenter Subtype Fixture",
        strategy_type="ai_datacenter_infrastructure",
        sub_type=sub_type,
        confidence="medium",
        confidence_score=60,
        warnings=warnings or [],
    )
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


def test_ai_datacenter_operator_readiness_excludes_power_and_cooling_fields():
    plan = build_ai_datacenter_plan("datacenter_operator")
    fields = {item.field_name for item in plan.field_readiness}
    missing = set(plan.critical_missing_fields + plan.high_priority_missing_fields)

    assert "ai_datacenter.customer_revenue_share" in fields
    assert "ai_datacenter.orders_or_backlog" in fields
    assert "financial_metrics.capex" in fields
    assert "ai_datacenter.cabinet_count" in fields
    assert "ai_datacenter.pue" in fields
    for field in {
        "ai_datacenter.power_ups_revenue_share",
        "ai_datacenter.power_ups_orders",
        "ai_datacenter.storage_pv_revenue_share",
        "ai_datacenter.cooling_revenue_share",
        "ai_datacenter.liquid_cooling_revenue_share",
        "ai_datacenter.liquid_cooling_customer_validation",
        "ai_datacenter.liquid_cooling_batch_orders",
        "ai_datacenter.ordinary_hvac_revenue_share",
    }:
        assert field not in fields
        assert field not in missing


def test_ai_datacenter_power_readiness_excludes_operator_and_cooling_fields():
    plan = build_ai_datacenter_plan("power_ups_infrastructure")
    fields = {item.field_name for item in plan.field_readiness}
    missing = set(plan.critical_missing_fields + plan.high_priority_missing_fields)

    assert "ai_datacenter.customer_revenue_share" in fields
    assert "ai_datacenter.orders_or_backlog" in fields
    assert "ai_datacenter.power_ups_revenue_share" in fields
    assert "ai_datacenter.storage_pv_revenue_share" in fields
    for field in {
        "ai_datacenter.cabinet_count",
        "ai_datacenter.mw_scale",
        "ai_datacenter.rack_up_or_utilization",
        "ai_datacenter.pue",
        "ai_datacenter.power_quota_energy_policy",
        "financial_metrics.depreciation_amortization",
        "ai_datacenter.cooling_revenue_share",
        "ai_datacenter.liquid_cooling_revenue_share",
        "ai_datacenter.liquid_cooling_customer_validation",
        "ai_datacenter.liquid_cooling_batch_orders",
        "ai_datacenter.ordinary_hvac_revenue_share",
    }:
        assert field not in fields
        assert field not in missing


def test_ai_datacenter_cooling_readiness_excludes_operator_and_power_fields():
    plan = build_ai_datacenter_plan("cooling_liquid_cooling_infrastructure")
    fields = {item.field_name for item in plan.field_readiness}
    missing = set(plan.critical_missing_fields + plan.high_priority_missing_fields)

    assert "ai_datacenter.customer_revenue_share" in fields
    assert "ai_datacenter.orders_or_backlog" in fields
    assert "ai_datacenter.cooling_revenue_share" in fields
    assert "ai_datacenter.liquid_cooling_revenue_share" in fields
    for field in {
        "ai_datacenter.cabinet_count",
        "ai_datacenter.mw_scale",
        "ai_datacenter.rack_up_or_utilization",
        "ai_datacenter.pue",
        "ai_datacenter.power_quota_energy_policy",
        "financial_metrics.depreciation_amortization",
        "ai_datacenter.power_ups_revenue_share",
        "ai_datacenter.power_ups_orders",
        "ai_datacenter.storage_pv_revenue_share",
    }:
        assert field not in fields
        assert field not in missing


def test_ai_datacenter_empty_subtype_is_conservative_and_does_not_crash():
    plan = build_ai_datacenter_plan(None)
    fields = {item.field_name for item in plan.field_readiness}

    assert plan.strategy_type == "ai_datacenter_infrastructure"
    assert "ai_datacenter.cabinet_count" in fields
    assert "ai_datacenter.power_ups_revenue_share" in fields
    assert "ai_datacenter.cooling_revenue_share" in fields


def test_ai_datacenter_power_storage_pv_boundary_missing_core_evidence_is_insufficient():
    plan = build_ai_datacenter_plan(
        "power_ups_infrastructure",
        ["ai_datacenter_power_storage_pv_boundary_confidence_capped"],
    )

    assert plan.readiness_level == "insufficient"
    assert plan.readiness_score <= 39
    assert "ai_datacenter.orders_or_backlog" in plan.high_priority_missing_fields
    assert any("boundary sample" in reason for reason in plan.confidence_penalty_reasons)


def test_ai_datacenter_cooling_hvac_boundary_missing_core_evidence_is_insufficient():
    plan = build_ai_datacenter_plan(
        "cooling_liquid_cooling_infrastructure",
        ["ai_datacenter_cooling_hvac_boundary_confidence_capped"],
    )

    assert plan.readiness_level == "insufficient"
    assert plan.readiness_score <= 39
    assert "ai_datacenter.liquid_cooling_customer_validation" in plan.high_priority_missing_fields
    assert any("boundary sample" in reason for reason in plan.confidence_penalty_reasons)


def test_ai_datacenter_non_boundary_fixture_keeps_readiness_floor():
    plan = build_ai_datacenter_plan("power_ups_infrastructure")

    assert plan.readiness_level == "usable_with_warnings"
    assert plan.readiness_score >= 60
