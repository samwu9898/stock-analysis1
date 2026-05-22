# -*- coding: utf-8 -*-

from copy import deepcopy

from src.fundamental_skill.ai_analyst.evidence_pack import EvidencePackBuilder
from src.fundamental_skill.ai_analyst.research_intelligence_builder import ResearchIntelligenceBuilder
from src.fundamental_skill.ai_analyst.research_intelligence_schema import ContradictionItem

from tests.ai_test_fixtures import sample_fundamental, sample_raw


FORBIDDEN_TERMS = ["买入", "卖出", "加仓", "减仓", "清仓", "止损", "止盈", "目标价", "仓位", "盈亏比", "K线", "技术面"]


def build_pack(strategy_type="advanced_manufacturing_growth", raw=None, sub_type=None, missing_fields=None):
    raw = raw or sample_raw()
    fundamental = sample_fundamental(strategy_type)
    if sub_type:
        fundamental["sub_type"] = sub_type
    if missing_fields is not None:
        fundamental["missing_fields"] = missing_fields
    return EvidencePackBuilder().build(fundamental, raw)


def build_outputs(strategy_type="advanced_manufacturing_growth", raw=None, sub_type=None, missing_fields=None):
    return ResearchIntelligenceBuilder().build(build_pack(strategy_type, raw, sub_type, missing_fields))


def question_text(questions):
    return " ".join(q.question for q in questions.questions)


def rule_item(rule_id):
    return ContradictionItem(
        rule_id=rule_id,
        triggered="true",
        severity="medium",
        contradiction_type="missing_bridge",
        claim_or_risk=rule_id,
        missing_evidence=["customer/order/capacity bridge"],
        data_availability_status="partial",
        confidence_cap="low",
        what_was_checked=["mock.rule"],
    )


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


def test_unknown_and_theme_only_do_not_create_p0_explosion_from_missing_fields():
    raw = sample_raw()
    raw["blocks"]["financial_indicator"] = [{}]
    raw["blocks"]["valuation"] = [{}]
    raw["blocks"]["business_composition"] = []

    for strategy in ["unknown", "theme_only"]:
        _, questions = build_outputs(strategy, raw)
        p0_questions = [q for q in questions.questions if q.priority == "P0"]

        assert 1 <= len(p0_questions) <= 3
        assert all(q.evidence_trigger for q in p0_questions)
        assert any(q.question_id == "q_classification_basic_review" for q in p0_questions)
        assert any(q.question_id == "q_grouped_missing_data_for_classification" for q in p0_questions)
        assert not any(
            q.priority == "P0" and q.trigger_rule_id == "contract_liabilities_overread_as_backlog"
            for q in questions.questions
        )


def test_ai_datacenter_cooling_questions_are_researcher_specific():
    _, questions = build_outputs(
        "ai_datacenter_infrastructure",
        sub_type="cooling_liquid_cooling_infrastructure",
    )
    text = question_text(questions)

    assert "POC" in text
    assert "批量订单" in text
    assert "液冷收入是否单独披露" in text
    assert "普通温控" in text
    assert "补充客户、订单或交付的官方披露证据" not in text
    assert "补充容量、利用率、验收、投产或收入转换证据" not in text
    assert all(q.evidence_trigger for q in questions.questions if q.priority == "P0")


def test_ai_datacenter_operator_questions_are_researcher_specific():
    _, questions = build_outputs(
        "ai_datacenter_infrastructure",
        sub_type="datacenter_operator",
    )
    text = question_text(questions)

    assert "机柜数" in text
    assert "MW" in text
    assert "PUE" in text
    assert "新增 capex" in text
    assert "客户合同" in text
    assert "折旧" in text
    assert "补充客户、订单或交付的官方披露证据" not in text
    assert "补充政策或主题相关业务是否已有合同、收入或客户证据" not in text


def test_ai_datacenter_rule_fallbacks_do_not_use_generic_templates():
    builder = ResearchIntelligenceBuilder()

    cooling_customer = builder._strategy_rule_question_text(
        rule_item("customer_order_claim_without_customer_evidence"),
        "ai_datacenter_infrastructure",
        "cooling_liquid_cooling_infrastructure",
    )
    cooling_capacity = builder._strategy_rule_question_text(
        rule_item("capacity_claim_without_utilization"),
        "ai_datacenter_infrastructure",
        "cooling_liquid_cooling_infrastructure",
    )
    operator_customer = builder._strategy_rule_question_text(
        rule_item("customer_order_claim_without_customer_evidence"),
        "ai_datacenter_infrastructure",
        "datacenter_operator",
    )
    operator_policy = builder._strategy_rule_question_text(
        rule_item("policy_theme_without_contract_revenue"),
        "ai_datacenter_infrastructure",
        "datacenter_operator",
    )

    assert cooling_customer == "液冷或数据中心温控客户是否已有官方披露？订单是否包含客户类型、金额、交付节点、验收口径和收入确认安排？"
    assert cooling_capacity == "液冷或机房温控相关产能、项目投产、客户验收和收入转换是否披露？现有 capex 是否已转化为液冷/数据中心温控收入？"
    assert operator_customer == "客户合同是否披露客户类型、合同期限、机柜/MW规模、上架节奏和收入确认口径？"
    assert operator_policy == "AIDC/智算中心政策或行业需求是否已转化为可披露客户合同、上架率、PUE、收入或经营现金流，而不是仅停留在主题或建设预期？"

    generic_templates = [
        "补充客户、订单或交付的官方披露证据。",
        "补充容量、利用率、验收、投产或收入转换证据。",
        "补充政策或主题相关业务是否已有合同、收入或客户证据。",
    ]
    assert not any(item in {cooling_customer, cooling_capacity, operator_customer, operator_policy} for item in generic_templates)


def test_advanced_manufacturing_questions_are_researcher_specific():
    _, questions = build_outputs("advanced_manufacturing_growth")
    text = question_text(questions)

    assert "机器人" in text
    assert "新业务是否有单独收入" in text
    assert "订单" in text
    assert "大客户收入占比" in text
    assert "估值消化" in text
    assert "经营现金流" in text


def test_life_science_cxo_questions_keep_backlog_proxy_guard():
    _, questions = build_outputs(
        "life_science_cxo_services",
        sub_type="integrated_cxo_platform",
    )
    text = question_text(questions)

    assert "backlog" in text
    assert "新签订单" in text
    assert "partial proxy" in text
    assert "不能替代 backlog" in text
    assert "美国" in text
    assert "生物安全法案" in text
    assert "产能利用率" in text


def test_resource_questions_include_commodity_volume_cost_and_cash_resilience():
    for strategy in ["resource_core", "resource_swing"]:
        _, questions = build_outputs(strategy)
        text = question_text(questions)

        assert "核心商品暴露" in text
        assert "商品价格" in text
        assert "产量" in text
        assert "销量" in text
        assert "品位" in text
        assert "资源量/储量" in text
        assert "现金成本" in text
        assert "完全成本" in text
        assert "套期保值" in text
        assert "汇率敞口" in text
        assert "维持性/扩张性 capex" in text
        assert "债务结构" in text
        assert "补充业务构成" not in text


def test_low_altitude_questions_are_operating_and_acceptance_specific():
    _, questions = build_outputs("low_altitude_economy_infrastructure")
    text = question_text(questions)

    assert "低空、通航或空管收入占比" in text
    assert "飞行小时" in text
    assert "飞行架次" in text
    assert "平台调度量" in text
    assert "验收节点" in text
    assert "收入确认口径" in text
    assert "政府/国企客户回款周期" in text
    assert "低空基础设施或运营服务" in text
    assert "补充客户、订单或交付" not in text


def test_satellite_questions_are_capacity_contract_and_life_specific():
    _, questions = build_outputs("satellite_communication_infrastructure")
    text = question_text(questions)

    assert "卫星容量" in text
    assert "转发器" in text
    assert "带宽资源" in text
    assert "容量利用率" in text
    assert "客户合同期限" in text
    assert "卫星剩余寿命" in text
    assert "合同续约风险" in text
    assert "补充客户、订单或交付" not in text


def test_contract_liabilities_proxy_questions_are_strategy_contextualized():
    builder = ResearchIntelligenceBuilder()
    item = rule_item("contract_liabilities_overread_as_backlog")
    ai_datacenter_text = builder._strategy_rule_question_text(item, "ai_datacenter_infrastructure", None)

    assert "客户项目可见度" in builder._strategy_rule_question_text(item, "life_science_cxo_services", None)
    assert "客户合同" in ai_datacenter_text
    assert "订单金额" in ai_datacenter_text
    assert "交付节点" in ai_datacenter_text
    assert "收入确认口径" in ai_datacenter_text
    assert "partial proxy" in ai_datacenter_text
    assert "不能替代真实订单" in ai_datacenter_text
    assert "已确认未来收入" in ai_datacenter_text
    assert "运营服务回款" in builder._strategy_rule_question_text(item, "low_altitude_economy_infrastructure", None)
    assert "容量租赁" in builder._strategy_rule_question_text(item, "satellite_communication_infrastructure", None)
    assert "价格敞口" in builder._strategy_rule_question_text(item, "resource_swing", None)
    assert "先降级处理" in builder._strategy_rule_question_text(item, "unknown", None)


def test_stable_growth_mock_evidence_triggers_stability_specific_questions():
    raw = sample_raw()
    raw["blocks"]["financial_indicator"][0].pop("operating_cashflow")

    _, questions = build_outputs("stable_growth", raw)
    text = question_text(questions)

    assert "稳健增长" in text
    assert "经营现金流" in text
    assert "回款" in text
    assert "应收账款" in text
    assert "ROE" in text
    assert "杠杆" in text
    assert "合同负债或订单" in text
    assert "债务结构" in text


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
