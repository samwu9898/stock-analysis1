# -*- coding: utf-8 -*-

from copy import deepcopy

from src.fundamental_skill.ai_analyst.html_report_schema import (
    FundamentalHtmlReport,
    schema_example,
    validate_fundamental_html_report,
)


def sample_html_report():
    payload = schema_example()
    payload["report_meta"].update(
        {
            "stock_code": "002050",
            "stock_name": "三花智控",
            "generated_at": "2026-05-21T00:00:00+00:00",
            "strategy_type": "advanced_manufacturing_growth",
            "strategy_type_label": "高端制造成长",
            "sub_type": "",
            "sub_type_label": "不适用",
            "data_quality_status": "测试数据",
        }
    )
    payload["report_meta"]["status"] = "neutral"
    payload["report_meta"]["confidence"] = "low"
    payload["core_conclusion"].update(
        {
            "title": "核心结论",
            "summary": "这是 schema 测试用基本面摘要。",
            "evidence_confidence_explanation": "证据置信度用于说明数据可用性。",
        }
    )
    payload["company_profile"].update(
        {
            "main_business": "热管理零部件。",
            "ownership_or_company_nature": "制造业公司",
            "framework_identity": "高端制造成长",
            "core_business_anchor": "制冷空调零部件与汽车热管理。",
        }
    )
    return payload


def test_fundamental_html_report_accepts_complete_structure(tmp_path):
    report = sample_html_report()
    report["hero_tags"] = ["高端制造成长", "现金流需复核"]
    report["research_anchor"] = {
        "main_thesis": "制冷空调零部件基本盘与汽车热管理成长共同构成研究主线。",
        "key_conflict": "成长叙事存在，但新业务证据仍待验证。",
        "current_stage": "成长验证期",
        "what_is_proven": ["主营业务构成可见"],
        "what_is_unproven": ["新业务收入与订单待验证"],
    }
    report["quality_score_breakdown"]["industry_position"] = {
        "score": 6,
        "max_score": 10,
        "label": "行业位置",
        "explanation": "具备制造业主业锚点，但份额证据缺失。",
        "evidence_basis": ["业务构成"],
    }
    report["value_chain_map"] = {
        "upstream": "原材料和制造配套待验证",
        "company_role": "热管理零部件供应商",
        "downstream": "家电、汽车等需求端",
        "profit_source": "零部件制造和毛利率稳定性",
        "unproven_moats": ["客户结构待验证"],
        "key_bottlenecks": ["订单证据缺失"],
    }
    report["elasticity_formula"] = {
        "formula_title": "利润弹性",
        "formula_text": "利润弹性 = 收入增长 × 毛利率稳定性 × 费用率控制",
        "key_variables": ["收入", "毛利率", "费用率"],
        "interpretation": "只解释基本面传导。",
        "data_limitations": ["新业务收入缺失"],
    }
    report["tracking_plan_groups"] = [
        {
            "group_name": "财报跟踪",
            "items": [
                {
                    "indicator": "毛利率",
                    "frequency": "季度",
                    "why_it_matters": "验证利润质量",
                    "trigger_for_review": "连续波动时复核",
                }
            ],
        }
    ]

    model = FundamentalHtmlReport.model_validate(report)
    validation = validate_fundamental_html_report(report)

    assert model.report_version == "fundamental_html_report.v1"
    assert validation["valid"] is True
    assert validation["schema_errors"] == []
    assert model.research_anchor.key_conflict
    assert model.quality_score_breakdown.industry_position.score == 6


def test_v21_fields_are_backward_compatible_when_missing():
    report = sample_html_report()
    for key in (
        "hero_tags",
        "research_anchor",
        "quality_score_breakdown",
        "value_chain_map",
        "elasticity_formula",
        "tracking_plan_groups",
        "financial_ratio_caveats",
    ):
        report.pop(key, None)

    validation = validate_fundamental_html_report(report)

    assert validation["valid"] is True
    assert validation["report"]["hero_tags"] == []
    assert validation["report"]["research_anchor"]["main_thesis"] == ""


def test_forbidden_trading_fields_do_not_exist_in_valid_report():
    report = sample_html_report()
    keys = []

    def walk(value):
        if isinstance(value, dict):
            for key, child in value.items():
                keys.append(str(key))
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(report)

    for forbidden in ("target_price", "buy", "sell", "stop_loss", "position"):
        assert forbidden not in keys


def test_schema_rejects_forbidden_trading_field_names():
    report = sample_html_report()
    bad = deepcopy(report)
    bad["valuation_explanation"]["target_price"] = "not allowed"

    validation = validate_fundamental_html_report(bad)

    assert validation["valid"] is False
    assert validation["schema_errors"]
    assert validation["safety"]["forbidden_key_findings"]


def test_schema_rejects_forbidden_trading_text_in_body():
    report = sample_html_report()
    bad = deepcopy(report)
    bad["core_conclusion"]["summary"] = "这里出现目标价。"

    validation = validate_fundamental_html_report(bad)

    assert validation["valid"] is False
    assert validation["safety"]["forbidden_text_findings"]


def test_schema_rejects_expanded_forbidden_text_in_body():
    report = sample_html_report()

    for term in ("技术面分析", "买卖时机", "交易终端", "交易建议", "technical_skill", "trader_skill"):
        bad = deepcopy(report)
        bad["core_conclusion"]["summary"] = f"这里出现{term}。"

        validation = validate_fundamental_html_report(bad)

        assert validation["valid"] is False
        assert validation["safety"]["forbidden_text_findings"]


def test_schema_rejects_expanded_forbidden_field_names():
    report = sample_html_report()

    for field_name in ("technical_analysis", "trading_terminal", "technical_skill", "trader_skill"):
        bad = deepcopy(report)
        bad["company_profile"]["business_segments"] = [{field_name: "not allowed"}]

        validation = validate_fundamental_html_report(bad)

        assert validation["valid"] is False
        assert validation["safety"]["forbidden_key_findings"]


def test_schema_allows_safety_boundary_policy_terms():
    report = sample_html_report()
    report["safety_boundary"]["statement"] = (
        "本报告仅供基本面研究，不构成交易建议，不包含目标价，不包含买卖建议，不包含技术面判断，不连接交易账户。"
    )
    report["safety_boundary"]["forbidden_actions_excluded"] = ["交易建议", "目标价", "买卖建议", "技术面判断"]
    report["report_meta"]["safety_boundary"] = report["safety_boundary"]["statement"]

    validation = validate_fundamental_html_report(report)

    assert validation["valid"] is True
