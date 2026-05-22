# -*- coding: utf-8 -*-

from copy import deepcopy

from src.fundamental_skill.ai_analyst.evidence_pack import EvidencePackBuilder
from src.fundamental_skill.ai_analyst.research_intelligence_builder import ResearchIntelligenceBuilder

from tests.ai_test_fixtures import sample_fundamental, sample_raw


FORBIDDEN_TERMS = ["买入", "卖出", "加仓", "减仓", "清仓", "止损", "止盈", "目标价", "仓位", "盈亏比", "K线", "技术面"]


def build_pack(strategy_type="advanced_manufacturing_growth", raw=None):
    raw = raw or sample_raw()
    return EvidencePackBuilder().build(sample_fundamental(strategy_type), raw)


def build_outputs(strategy_type="advanced_manufacturing_growth", raw=None):
    return ResearchIntelligenceBuilder().build(build_pack(strategy_type, raw))


def test_builder_generates_research_intelligence_pack_from_evidence_pack():
    intelligence, questions = build_outputs("advanced_manufacturing_growth")

    assert intelligence.schema_version == "research_intelligence.v1"
    assert questions.schema_version == "research_questions.v1"
    assert intelligence.source_hierarchy
    assert intelligence.evidence_classification
    assert intelligence.strategy_driver_map["drivers"]
    assert intelligence.business_financial_cross_validation
    assert len(intelligence.rule_triggered_contradictions) >= 15
    assert all(q.evidence_trigger for q in questions.questions if q.priority == "P0")


def test_proxy_is_not_treated_as_fact():
    intelligence, _ = build_outputs("advanced_manufacturing_growth")

    proxy_rows = [
        item
        for item in intelligence.evidence_classification
        if item.evidence_name == "合同负债"
    ]
    assert proxy_rows
    assert proxy_rows[0].evidence_type == "proxy"
    assert "backlog" in proxy_rows[0].interpretation_boundary


def test_missing_evidence_generates_ir_or_manual_question():
    raw = sample_raw()
    raw["blocks"]["financial_indicator"][0].pop("operating_cashflow")
    intelligence, questions = build_outputs("stable_growth", raw)

    rule_ids = {item.rule_id: item for item in intelligence.rule_triggered_contradictions}
    assert rule_ids["stable_growth_without_receivables_cashflow_check"].triggered in {"true", "not_assessable"}
    assert any(q.evidence_trigger == "stable_growth_without_receivables_cashflow_check" for q in questions.questions)


def test_strategy_aware_questions_for_new_frameworks():
    strategies = {
        "ai_datacenter_infrastructure": "AI datacenter infrastructure revenue",
        "life_science_cxo_services": "CXO growth",
        "satellite_communication_infrastructure": "satellite infrastructure economics",
        "low_altitude_economy_infrastructure": "low-altitude exposure",
        "advanced_manufacturing_growth": "new manufacturing or robotics growth",
    }
    for strategy, expected_claim in strategies.items():
        intelligence, questions = build_outputs(strategy)
        claims = " ".join(item.business_claim for item in intelligence.business_financial_cross_validation)
        question_text = " ".join(q.question for q in questions.questions)

        assert expected_claim in claims
        assert "补充验证" in question_text or any(q.evidence_trigger for q in questions.questions)


def test_unknown_and_theme_only_are_conservative():
    for strategy in ["unknown", "theme_only"]:
        intelligence, questions = build_outputs(strategy)
        triggered = {item.rule_id for item in intelligence.rule_triggered_contradictions if item.triggered == "true"}

        assert "classification_low_confidence_requires_review" in triggered
        assert any("复核分类" in q.question or "先复核" in q.question for q in questions.questions)


def test_rule_missing_fields_do_not_fabricate_contradiction():
    raw = sample_raw()
    raw["blocks"]["financial_indicator"][0].pop("operating_cashflow")
    intelligence, _ = build_outputs("right_trend_growth", raw)
    rule = {
        item.rule_id: item
        for item in intelligence.rule_triggered_contradictions
    }["revenue_growth_vs_cashflow_mismatch"]

    assert rule.triggered == "not_assessable"
    assert rule.contradiction_type == "missing_data_blocker"
    assert rule.not_assessable_reason


def test_no_forbidden_trading_or_technical_terms_in_builder_outputs():
    intelligence, questions = build_outputs("ai_datacenter_infrastructure")
    text = f"{intelligence.model_dump()} {questions.model_dump()}"

    assert not any(term in text for term in FORBIDDEN_TERMS)


def test_cross_validation_covers_legacy_strategy_types():
    for strategy in [
        "right_trend_growth",
        "resource_core",
        "resource_swing",
        "semiconductor_cycle",
        "stable_growth",
        "theme_only",
        "unknown",
    ]:
        intelligence, _ = build_outputs(strategy)
        assert any(item.strategy_type == strategy for item in intelligence.business_financial_cross_validation)
