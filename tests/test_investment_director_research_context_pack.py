# -*- coding: utf-8 -*-

from __future__ import annotations

import builtins
import copy
import json
import re
import socket

from src.fundamental_skill.research_planning.investment_director_research_context_pack import (
    COVERAGE_STATUSES,
    INVESTMENT_DIRECTOR_RESEARCH_CONTEXT_PACK_REQUEST_SCHEMA_VERSION,
    INVESTMENT_DIRECTOR_RESEARCH_CONTEXT_PACK_SCHEMA_VERSION,
    build_investment_director_research_context_pack,
)


def _driver(
    driver_factor,
    *,
    layer="company",
    question,
    required,
    available=None,
    missing=None,
    status="missing",
    confidence="not_assessable",
    reason="当前结构化输入尚不足以判断。",
    checked=None,
    trigger=None,
    next_check=None,
):
    return {
        "layer": layer,
        "driver_factor": driver_factor,
        "driver_scope": "sample inline test",
        "why_it_matters": f"{driver_factor}决定模型能否把主题传导到公司经营证据。",
        "required_evidence": list(required),
        "available_evidence": list(available or []),
        "missing_evidence": list(missing or required),
        "company_transmission_path": "传导路径无法从当前证据包验证"
        if status in {"missing", "not_assessable"}
        else f"evidence_pack.{driver_factor}=structured_summary",
        "data_availability_status": status,
        "confidence_cap": confidence,
        "not_assessable_reason": reason,
        "what_was_checked": list(checked or [driver_factor, "inline structured summary"]),
        "research_question": question,
        "evidence_trigger": trigger or f"{driver_factor}:{status}",
        "next_check": next_check or "Collect and map: " + "; ".join(list(missing or required)[:3]),
        "interpretation_guard": "仅作为待验证研究问题，不改写为公司层面结论。",
    }


def _question(
    question,
    *,
    category,
    layer="company",
    required,
    available=None,
    missing=None,
    status="missing",
    confidence="not_assessable",
    reason="当前结构化输入尚不足以判断。",
    trigger=None,
    checked=None,
):
    return {
        "question": question,
        "category": category,
        "layer": layer,
        "priority": "P0",
        "evidence_trigger": trigger or f"{category}:{status}",
        "why_it_matters": "该问题决定后续模型是否能形成投资总监式深度分析。",
        "required_evidence": list(required),
        "available_evidence": list(available or []),
        "missing_evidence": list(missing or required),
        "data_availability_status": status,
        "confidence_cap": confidence,
        "not_assessable_reason": reason,
        "what_was_checked": list(checked or [category, "inline question payload"]),
        "suggested_next_action": "Collect and map: " + "; ".join(list(missing or required)[:3]),
    }


def _request_002050(**overrides):
    request = {
        "schema_version": INVESTMENT_DIRECTOR_RESEARCH_CONTEXT_PACK_REQUEST_SCHEMA_VERSION,
        "stock_code": "002050",
        "ts_code": "002050.SZ",
        "company_name_hint": "002050-like advanced manufacturing sample",
        "strategy_type": "advanced_manufacturing_growth",
        "sub_type": "automotive_thermal_and_new_business",
        "not_for_trading_advice": True,
        "include_prompt_payload": True,
        "include_missing_coverage_map": True,
        "old_report_frontstage_snapshot": {
            "core_conclusion": "制冷空调基本盘和汽车零部件是可验证支柱；机器人/新业务仍缺收入、订单、客户、量产证据。",
            "core_conflict": "核心矛盾是可验证基本盘 vs 新业务/高成长证据缺口。",
            "company_profile_summary": "公司样本包含制冷空调基本盘、汽车零部件支柱和机器人/新业务待验证线索。",
            "business_composition_summary": "业务构成：制冷空调基本盘；汽车零部件支柱；机器人/新业务证据待补。",
            "financial_quality_summary": "财务质量需要收入、利润、现金流、应收和存货联动检查。",
            "valuation_explainability_summary": "估值解释需要盈利、现金流和证据充分性边界。",
            "quality_score_summary": {
                "six_dimension_score": "结构化六维评分摘要，仅作旧前台研究线索。"
            },
            "risk_summary": "新业务证据不足、客户集中度不可评估、热管理细分证据不足。",
            "tracking_plan_summary": "跟踪订单、交付、回款、利润率、分部收入和客户证据。",
            "data_quality_summary": "仅结构化摘要输入；不包含原始页面或渲染产物。",
        },
        "research_intelligence_p0": {
            "schema_version": "research_intelligence.v1",
            "stock_code": "002050",
            "generated_at": "2026-06-03T00:00:00",
            "strategy_type": "advanced_manufacturing_growth",
            "sub_type": "automotive_thermal_and_new_business",
            "source_hierarchy": [
                {
                    "source_name": "old_frontstage_snapshot",
                    "evidence_type": "structured_summary",
                    "data_availability_status": "partial",
                    "what_was_checked": ["business_composition_summary", "risk_summary"],
                }
            ],
            "business_financial_cross_validation": [
                {
                    "item_id": "automotive_parts_pillar_partial",
                    "strategy_type": "advanced_manufacturing_growth",
                    "business_claim": "汽车零部件是可验证支柱，但热管理细分仍需客户/项目/交付/回款证据。",
                    "financial_checks": ["分部收入", "经营现金流", "应收回款"],
                    "required_evidence": ["客户项目", "交付节奏", "回款质量"],
                    "available_evidence": ["旧前台摘要识别汽车零部件支柱"],
                    "missing_evidence": ["热管理客户", "项目进度", "交付/回款细节"],
                    "validation_status": "partially_validated",
                    "data_availability_status": "partial",
                    "confidence_cap": "medium",
                    "what_was_checked": ["old_report_frontstage_snapshot.business_composition_summary"],
                }
            ],
            "rule_triggered_contradictions": [
                {
                    "rule_id": "new_business_proxy_overread",
                    "triggered": "true",
                    "severity": "high",
                    "contradiction_type": "missing_bridge",
                    "claim_or_risk": "机器人/新业务叙事缺少收入、订单、客户、量产证据。",
                    "evidence_for": ["旧前台摘要提到机器人/新业务证据待补"],
                    "missing_evidence": ["机器人收入", "机器人订单", "客户", "量产"],
                    "data_availability_status": "not_assessable",
                    "confidence_cap": "not_assessable",
                    "not_assessable_reason": "仅有主题框架，没有经营证据。",
                    "what_was_checked": ["old_report_frontstage_snapshot.risk_summary"],
                    "research_question_id": "rq_robotics_gap",
                }
            ],
            "manual_review_items": [
                _question(
                    "客户集中度是否能从结构化输入判断？",
                    category="customer_concentration",
                    required=["客户收入集中度", "主要客户变化", "回款质量"],
                    missing=["客户集中度数据", "主要客户变化", "回款质量"],
                    checked=["old_frontstage_snapshot", "P1 driver matrix"],
                    status="not_assessable",
                    confidence="not_assessable",
                    reason="未提供客户结构和集中度证据。",
                )
            ],
            "ir_question_candidates": [
                _question(
                    "汽车热管理客户/项目/交付/回款证据如何补齐？",
                    category="ir_automotive_thermal",
                    required=["客户清单", "项目节点", "交付", "回款"],
                    available=["汽车零部件支柱摘要"],
                    missing=["热管理客户", "项目节点", "交付和回款"],
                    status="partial",
                    confidence="low",
                )
            ],
        },
        "research_questions_p0": {
            "schema_version": "research_questions.v1",
            "stock_code": "002050",
            "generated_at": "2026-06-03T00:00:00",
            "questions": [
                _question(
                    "估值背景是否有盈利、现金流和证据充分性支撑？",
                    category="valuation_explainability",
                    layer="valuation",
                    required=["盈利证据", "现金流证据", "估值解释边界"],
                    missing=["估值解释所需证据充分性"],
                    checked=["valuation_explainability_summary"],
                )
            ],
        },
        "research_intelligence_p1": {
            "schema_version": "research_intelligence_p1.v1",
            "stock_code": "002050",
            "generated_at": "2026-06-03T00:00:00",
            "strategy_type": "advanced_manufacturing_growth",
            "sub_type": "automotive_thermal_and_new_business",
            "driver_matrix": [
                _driver(
                    "robotics_new_business_evidence_gap",
                    question="机器人/新业务是否已有收入、订单、客户、量产证据支撑高成长叙事？",
                    required=["机器人收入", "订单", "客户", "量产证据"],
                    missing=["机器人收入", "订单", "客户", "量产证据"],
                    status="not_assessable",
                    confidence="not_assessable",
                    reason="只有主题框架，没有经营兑现证据。",
                    checked=["P1 driver matrix", "old report risk summary"],
                ),
                _driver(
                    "automotive_thermal_management_partial",
                    question="汽车热管理细分是否能由客户、项目、交付、回款证据支撑？",
                    required=["热管理客户", "项目进度", "交付", "回款"],
                    available=["旧前台摘要识别汽车零部件支柱"],
                    missing=["热管理客户", "项目进度", "交付", "回款"],
                    status="partial",
                    confidence="low",
                    reason="有汽车零部件支柱摘要，但热管理细分证据不足。",
                ),
                _driver(
                    "capex_to_revenue_bridge",
                    question="capex 如何通过项目进度、交付和收入转化形成经营证据？",
                    required=["capex项目", "项目进度", "交付", "收入转化"],
                    missing=["项目映射", "交付证据", "收入转化证据"],
                ),
                _driver(
                    "r_and_d_conversion",
                    question="R&D 投入是否有产品、客户和收入转化证据？",
                    required=["研发项目", "产品节点", "客户采用", "收入转化"],
                    missing=["产品节点", "客户采用", "收入转化"],
                ),
                _driver(
                    "contract_liabilities_proxy_only",
                    question="合同负债是否有订单、履约、回款和独立 backlog 证据配套？",
                    required=["合同负债", "订单明细", "履约", "回款", "backlog披露"],
                    available=["合同负债可作为代理信号"],
                    missing=["订单明细", "履约", "回款", "backlog披露"],
                    status="partial",
                    confidence="low",
                ),
                _driver(
                    "peer_market_share_gap",
                    layer="industry",
                    question="同业/竞品和市场份额数据是否足以支持竞争力判断？",
                    required=["同业样本", "竞品指标", "市场份额分母"],
                    missing=["同业样本", "竞品指标", "市场份额分母"],
                ),
            ],
            "driver_research_questions": [
                _question(
                    "高端制造需求如何传导到订单、交付、回款和利润率？",
                    category="advanced_manufacturing_growth_transmission",
                    layer="industry",
                    required=["需求线索", "订单", "交付", "回款", "利润率"],
                    missing=["订单", "交付", "回款", "利润率"],
                    checked=["P1 driver matrix"],
                )
            ],
            "not_assessable_drivers": [
                _driver(
                    "customer_concentration_not_assessable",
                    question="客户集中度是否可评估？",
                    required=["客户收入结构", "客户集中度", "主要客户变化"],
                    missing=["客户收入结构", "客户集中度"],
                    status="not_assessable",
                    confidence="not_assessable",
                    reason="客户结构证据未提供。",
                )
            ],
            "source_bucket_summary": {
                "source_buckets": ["company_disclosure"],
                "independent_source_count": 1,
                "consensus_assessment_status": "not_assessable",
                "not_assessable_reason": "Less than two independent source buckets are available.",
            },
        },
        "research_questions_p1": {
            "schema_version": "research_questions_p1.v1",
            "stock_code": "002050",
            "generated_at": "2026-06-03T00:00:00",
            "strategy_type": "advanced_manufacturing_growth",
            "questions": [],
        },
        "ticker_research_context_skeleton": {
            "schema_version": "ticker_research_context_skeleton.v1",
            "research_questions": {
                "questions": [
                    _question(
                        "收入增长是否与现金流、应收和存货联动匹配？",
                        category="cashflow_receivable_inventory_linkage",
                        layer="financial",
                        required=["收入", "现金流", "应收", "存货"],
                        missing=["现金流/应收/存货联动表"],
                        status="partial",
                        confidence="low",
                    )
                ]
            },
        },
        "evidence_aware_research_pack": {
            "schema_version": "evidence_aware_research_pack_scaffold.v1",
            "sections": [
                {
                    "section_id": "research_questions",
                    "items": [
                        {
                            "item_id": "capex_mapping_gap",
                            "question": "capex-to-revenue bridge",
                            "required_evidence": ["项目进度", "收入转化"],
                            "current_evidence_status": "missing",
                        }
                    ],
                }
            ],
        },
    }
    request.update(overrides)
    return request


def _request_600406(**overrides):
    request = {
        "schema_version": INVESTMENT_DIRECTOR_RESEARCH_CONTEXT_PACK_REQUEST_SCHEMA_VERSION,
        "stock_code": "600406",
        "ts_code": "600406.SH",
        "company_name_hint": "600406-like stable growth sample",
        "strategy_type": "stable_growth",
        "sub_type": "cash_conversion_quality",
        "not_for_trading_advice": True,
        "include_prompt_payload": True,
        "include_missing_coverage_map": True,
        "old_report_frontstage_snapshot": {
            "core_conclusion": "stable growth 样本需要现金转化、应收回款、资本效率和分红持续性证据支撑。",
            "core_conflict": "核心矛盾是稳定增长框架 vs 现金转化、回款、资本效率和分红证据充分性。",
            "company_profile_summary": "公司身份仅为 regression-shaped 样本，不写具体行业结论。",
            "business_composition_summary": "业务结构需要结构化分部和客户留存证据。",
            "financial_quality_summary": "关注现金转化、应收回款、ROE/ROIC、capex纪律和分红覆盖。",
            "valuation_explainability_summary": "估值背景只能在盈利、现金流和资本效率证据内讨论。",
            "quality_score_summary": {"stable_growth_score_frame": "仅记录待验证维度。"},
            "risk_summary": "重复订单、客户留存和分红持续性证据不足。",
            "tracking_plan_summary": "跟踪现金转化、应收回款、复购/留存、ROE/ROIC、capex纪律、分红覆盖。",
            "data_quality_summary": "仅结构化摘要输入。",
        },
        "research_intelligence_p1": {
            "schema_version": "research_intelligence_p1.v1",
            "stock_code": "600406",
            "generated_at": "2026-06-03T00:00:00",
            "strategy_type": "stable_growth",
            "sub_type": "cash_conversion_quality",
            "driver_matrix": [
                _driver(
                    "cash_conversion_quality",
                    layer="financial",
                    question="利润是否转化为经营现金流？",
                    required=["经营现金流", "利润", "现金转化趋势"],
                    available=["旧前台摘要提示现金转化维度"],
                    missing=["利润到现金流桥接表"],
                    status="partial",
                    confidence="low",
                ),
                _driver(
                    "receivables_collection_quality",
                    layer="financial",
                    question="应收账款和回款质量是否支撑稳定增长框架？",
                    required=["应收趋势", "回款证据", "账龄或坏账边界"],
                    available=["旧前台摘要提示应收回款维度"],
                    missing=["应收趋势", "回款证据"],
                    status="partial",
                    confidence="low",
                ),
                _driver(
                    "repeat_order_customer_retention",
                    question="重复订单和客户留存证据是否可见？",
                    required=["重复订单", "客户留存", "客户结构"],
                    missing=["重复订单", "客户留存"],
                ),
                _driver(
                    "roe_roic_evidence_sufficiency",
                    layer="financial",
                    question="ROE/ROIC 是否有足够证据解释资本效率？",
                    required=["ROE趋势", "ROIC证据", "投入资本口径"],
                    available=["旧前台摘要提示资本效率维度"],
                    missing=["ROIC证据", "投入资本口径"],
                    status="partial",
                    confidence="low",
                ),
                _driver(
                    "capex_discipline",
                    layer="financial",
                    question="capex纪律是否有现金回收和项目进度证据？",
                    required=["capex计划", "项目进度", "现金回收边界"],
                    missing=["capex计划", "项目进度", "现金回收边界"],
                ),
                _driver(
                    "dividend_payout_sustainability",
                    layer="financial",
                    question="分红/派息持续性是否有现金覆盖和负债边界？",
                    required=["分红历史", "现金覆盖", "负债边界"],
                    missing=["分红历史", "现金覆盖"],
                ),
            ],
            "driver_research_questions": [],
            "not_assessable_drivers": [],
            "source_bucket_summary": {
                "source_buckets": ["company_disclosure"],
                "independent_source_count": 1,
                "consensus_assessment_status": "not_assessable",
                "not_assessable_reason": "Less than two independent source buckets are available.",
            },
        },
        "research_questions_p1": {
            "schema_version": "research_questions_p1.v1",
            "stock_code": "600406",
            "generated_at": "2026-06-03T00:00:00",
            "strategy_type": "stable_growth",
            "questions": [],
        },
    }
    request.update(overrides)
    return request


def _text(value):
    return json.dumps(value, ensure_ascii=False)


def _coverage_by_id(pack):
    return {
        item["requirement_id"]: item
        for item in pack["missing_coverage_map"]["items"]
    }


NEW_RULEBOOK_COVERAGE_IDS = (
    "authoritative_data_crosscheck",
    "news_and_special_events",
    "source_tier_classification",
    "rd_staff_and_project_mapping",
    "revenue_driver_decomposition",
    "cost_driver_decomposition",
    "balance_sheet_reclassification",
    "financing_cashflow_dependency",
    "selective_disclosure_risk",
    "conclusion_first_frontstage",
    "visualization_plan",
)


def _contains_market_action_word(text, word):
    return re.search(rf"(?<![a-z0-9_]){re.escape(word)}(?![a-z0-9_])", text) is not None


def test_valid_002050_like_request_returns_pack():
    pack = build_investment_director_research_context_pack(_request_002050())

    assert pack["schema_version"] == INVESTMENT_DIRECTOR_RESEARCH_CONTEXT_PACK_SCHEMA_VERSION
    assert pack["company_identity"]["stock_code"] == "002050"
    assert pack["not_for_trading_advice"] is True


def test_valid_600406_like_request_returns_pack():
    pack = build_investment_director_research_context_pack(_request_600406())

    assert pack["schema_version"] == INVESTMENT_DIRECTOR_RESEARCH_CONTEXT_PACK_SCHEMA_VERSION
    assert pack["company_identity"]["strategy_type"] == "stable_growth"


def test_pack_contains_required_top_level_contexts():
    pack = build_investment_director_research_context_pack(_request_002050())

    for key in (
        "company_identity",
        "frontstage_report_context",
        "research_intelligence_context",
        "collision_question_set",
        "source_tier_and_viewpoint_context",
        "director_framework_alignment",
        "frontstage_visualization_requirements",
        "missing_coverage_map",
        "llm_context_prompt_payload",
    ):
        assert key in pack


def test_source_tier_and_viewpoint_context_marks_viewpoints_not_assessable_with_one_bucket():
    pack = build_investment_director_research_context_pack(_request_002050())
    context = pack["source_tier_and_viewpoint_context"]

    assert context["schema_version"] == "investment_director_source_tier_and_viewpoint_context.v1"
    assert context["independent_source_count"] == 1
    assert context["available_source_buckets"]
    assert context["consensus_status"] == "not_assessable"
    assert context["divergent_view_status"] == "not_assessable"
    assert context["opposing_view_status"] == "not_assessable"
    assert context["missing_viewpoint_evidence"]


def test_director_framework_alignment_weak_links_derive_from_missing_or_partial_coverage():
    pack = build_investment_director_research_context_pack(_request_002050())
    coverage = _coverage_by_id(pack)
    weak_links = pack["director_framework_alignment"]["weak_links"]

    assert pack["director_framework_alignment"]["schema_version"] == "investment_director_framework_alignment.v1"
    assert weak_links
    for link in weak_links:
        assert link["requirement_id"] in coverage
        assert link["coverage_status"] == coverage[link["requirement_id"]]["coverage_status"]
        assert link["coverage_status"] not in {"covered", "not_applicable"}
        assert link["next_data_task"] == coverage[link["requirement_id"]]["next_data_task"]


def test_frontstage_visualization_requirements_include_display_bands():
    pack = build_investment_director_research_context_pack(_request_002050())
    requirements = pack["frontstage_visualization_requirements"]

    assert requirements["schema_version"] == "investment_director_frontstage_visualization_requirements.v1"
    assert "core_conclusion" in requirements["conclusion_first_sections"]
    assert requirements["chart_ready_sections"]
    assert requirements["table_ready_sections"]
    assert requirements["material_backstage_sections"]
    assert "missing_coverage_map" in requirements["material_backstage_sections"]


def test_002050_pack_includes_advanced_manufacturing_driver_questions():
    pack = build_investment_director_research_context_pack(_request_002050())
    text = _text(pack)

    assert "advanced_manufacturing_growth" in text
    assert "高端制造需求如何传导到订单、交付、回款和利润率" in text


def test_002050_pack_includes_robotics_new_business_not_assessable():
    pack = build_investment_director_research_context_pack(_request_002050())
    text = _text(pack)

    assert "robotics_new_business_evidence_gap" in text
    assert "not_assessable" in text
    assert "机器人收入" in text


def test_002050_pack_includes_automotive_thermal_partial_evidence():
    pack = build_investment_director_research_context_pack(_request_002050())
    text = _text(pack)

    assert "automotive_thermal_management_partial" in text
    assert "旧前台摘要识别汽车零部件支柱" in text
    assert "热管理客户" in text


def test_002050_pack_includes_customer_concentration_gap():
    pack = build_investment_director_research_context_pack(_request_002050())
    text = _text(pack)

    assert "customer_concentration" in text
    assert "客户集中度数据" in text
    assert "not_assessable" in text


def test_002050_pack_includes_capex_r_and_d_and_valuation_questions():
    pack = build_investment_director_research_context_pack(_request_002050())
    text = _text(pack)

    assert "capex_to_revenue_bridge" in text
    assert "r_and_d_conversion" in text
    assert "valuation_explainability" in text


def test_002050_core_conflict_reflects_basic_business_vs_growth_gap():
    pack = build_investment_director_research_context_pack(_request_002050())

    assert (
        pack["frontstage_report_context"]["core_conflict"]
        == "核心矛盾是可验证基本盘 vs 新业务/高成长证据缺口。"
    )
    assert "可验证基本盘 vs 新业务/高成长证据缺口" in pack["llm_context_prompt_payload"]["core_conflicts_to_analyze"][0]


def test_600406_pack_does_not_reuse_002050_robotics_template():
    pack = build_investment_director_research_context_pack(_request_600406())
    text = _text(pack).casefold()

    assert "robotics" not in text
    assert "机器人" not in text
    assert "advanced_manufacturing" not in text
    assert "电网" not in text
    assert "国电南瑞" not in text


def test_600406_pack_includes_stable_growth_coverage_items():
    pack = build_investment_director_research_context_pack(_request_600406())
    coverage = _coverage_by_id(pack)

    for requirement_id in (
        "stable_cash_conversion",
        "stable_receivables_collection_quality",
        "stable_repeat_order_customer_retention",
        "stable_roe_roic_evidence_sufficiency",
        "stable_capex_discipline",
        "stable_dividend_payout_sustainability",
    ):
        assert requirement_id in coverage


def test_missing_coverage_map_includes_all_required_investment_director_categories():
    pack = build_investment_director_research_context_pack(_request_002050())
    coverage = _coverage_by_id(pack)

    for requirement_id in (
        "macro_context",
        "international_macro",
        "fx",
        "commodity",
        "policy",
        "industry_cycle",
        "industry_consensus",
        "divergent_views",
        "opposing_views",
        "competitor_peer_benchmark",
        "upstream_downstream_prices",
        "company_business_structure",
        "business_competitiveness",
        "market_share",
        "project_progress",
        "capex_mapping",
        "r_and_d_conversion",
        "financial_statement_quality",
        "cashflow_receivable_inventory_linkage",
        "debt_financing_structure",
        "disclosure_consistency",
        "prior_promise_vs_current_delivery",
        "governance_risk",
        "regulatory_violation_risk",
        "black_swan_risk",
        "manual_research_notes",
        "ir_questions",
        "frontstage_chart_ready_sections",
        "html_report_mapping",
        *NEW_RULEBOOK_COVERAGE_IDS,
    ):
        assert requirement_id in coverage


def test_covered_status_requires_framework_material_and_llm_visible_readiness():
    pack = build_investment_director_research_context_pack(_request_002050())

    for item in pack["missing_coverage_map"]["items"]:
        assert item["coverage_status"] in COVERAGE_STATUSES
        if item["coverage_status"] == "covered":
            assert item["covered_semantics"]["framework_exists"] is True
            assert item["covered_semantics"]["material_or_structured_input_exists"] is True
            assert item["covered_semantics"]["can_enter_llm_context"] is True
            assert item["currently_available_assets"]
            assert item["currently_llm_visible"] is True


def test_peer_and_market_share_framework_without_real_data_is_not_covered():
    pack = build_investment_director_research_context_pack(_request_002050())
    coverage = _coverage_by_id(pack)

    assert coverage["competitor_peer_benchmark"]["coverage_status"] == "framework_exists_but_missing_data"
    assert coverage["market_share"]["coverage_status"] == "framework_exists_but_missing_data"


def test_supplied_material_marked_not_llm_visible_is_partial_not_covered():
    request = _request_002050()
    request["research_intelligence_p1"]["driver_matrix"].append(
        _driver(
            "legacy_policy_transmission_note",
            layer="industry",
            question="政策变量是否已有公司订单/交付/回款传导证据？",
            required=["政策范围", "订单", "交付", "回款"],
            available=["旧 P1 已有政策传导研究笔记"],
            missing=["订单", "交付", "回款"],
            status="partial",
            confidence="low",
        )
    )
    request["research_intelligence_p1"]["driver_matrix"][-1]["currently_llm_visible"] = False

    pack = build_investment_director_research_context_pack(request)
    coverage = _coverage_by_id(pack)

    assert coverage["policy"]["coverage_status"] == "partial_but_not_llm_visible"


def test_every_missing_or_partial_item_has_required_evidence_and_next_data_task():
    pack = build_investment_director_research_context_pack(_request_002050())

    for item in pack["missing_coverage_map"]["items"]:
        if item["coverage_status"] != "covered":
            assert item["required_evidence"]
            assert item["next_data_task"]
            assert "needs more research" not in item["next_data_task"].casefold()


def test_every_new_missing_or_partial_coverage_item_has_concrete_next_data_task():
    pack = build_investment_director_research_context_pack(_request_002050())
    coverage = _coverage_by_id(pack)
    vague_markers = (
        "needs more research",
        "more research needed",
        "需进一步研究",
        "需要更多资料",
        "后续继续关注",
    )

    for requirement_id in NEW_RULEBOOK_COVERAGE_IDS:
        item = coverage[requirement_id]
        if item["coverage_status"] != "covered":
            assert item["required_evidence"]
            assert item["next_data_task"]
            for marker in vague_markers:
                assert marker not in item["next_data_task"].casefold()


def test_new_categories_are_not_covered_without_strict_covered_semantics():
    pack = build_investment_director_research_context_pack(_request_002050())
    coverage = _coverage_by_id(pack)

    for requirement_id in NEW_RULEBOOK_COVERAGE_IDS:
        item = coverage[requirement_id]
        if item["coverage_status"] == "covered":
            assert item["covered_semantics"]["framework_exists"] is True
            assert item["covered_semantics"]["material_or_structured_input_exists"] is True
            assert item["covered_semantics"]["can_enter_llm_context"] is True


def test_every_collision_question_has_evidence_trigger_and_what_was_checked():
    pack = build_investment_director_research_context_pack(_request_002050())

    for question in pack["collision_question_set"]["questions"]:
        assert question["evidence_trigger"]
        assert question["what_was_checked"]
        assert question["required_evidence"]
        assert question["data_availability_status"]


def test_prompt_payload_is_concise_and_does_not_dump_all_schema_fields():
    pack = build_investment_director_research_context_pack(_request_002050())
    payload = pack["llm_context_prompt_payload"]
    text = _text(payload)

    assert len(text) < 16000
    assert "covered_semantics" not in text
    assert "source_tier_summary" not in text
    assert "framework_chain" not in text
    assert "material_backstage_sections" not in text
    assert "schema_version" in payload


def test_prompt_payload_includes_metric_repetition_guard_and_collision_tasks():
    pack = build_investment_director_research_context_pack(_request_002050())
    payload = pack["llm_context_prompt_payload"]
    requirements = " ".join(payload["analysis_requirements"])
    categories = {item["category"] for item in payload["collision_questions"]}

    assert "Do not merely repeat metrics" in requirements
    assert "business-financial-risk" in requirements
    assert "revenue_growth_vs_cashflow" in categories
    assert "capex_vs_project_revenue_conversion" in categories


def test_prompt_payload_prohibits_trading_advice_without_action_terms():
    pack = build_investment_director_research_context_pack(_request_002050())
    payload = pack["llm_context_prompt_payload"]
    text = _text(payload).casefold()

    assert payload["output_boundaries"]["trading_advice_allowed"] is False
    for forbidden in ("buy", "sell", "hold", "position"):
        assert not _contains_market_action_word(text, forbidden)
    for forbidden in ("target price", "technical signal"):
        assert forbidden not in text


def test_no_output_fixtures_or_manifest_write(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    pack = build_investment_director_research_context_pack(_request_002050())

    assert pack["schema_version"] == INVESTMENT_DIRECTOR_RESEARCH_CONTEXT_PACK_SCHEMA_VERSION
    assert not (tmp_path / "output").exists()
    assert not (tmp_path / "fixtures").exists()
    assert not (tmp_path / "accepted_manifest.json").exists()


def test_input_request_is_not_mutated():
    request = _request_002050()
    before = copy.deepcopy(request)

    build_investment_director_research_context_pack(request)

    assert request == before


def test_no_network_call(monkeypatch):
    def blocked(*_args, **_kwargs):
        raise AssertionError("network must not be called")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "socket", blocked)

    pack = build_investment_director_research_context_pack(_request_002050())

    assert pack["company_identity"]["stock_code"] == "002050"


def test_no_live_llm_call(monkeypatch):
    real_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name in {"openai", "dashscope", "deepseek"}:
            raise AssertionError("LLM API must not be imported")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    pack = build_investment_director_research_context_pack(_request_002050())

    assert pack["company_identity"]["ts_code"] == "002050.SZ"
