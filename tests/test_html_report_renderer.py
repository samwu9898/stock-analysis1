# -*- coding: utf-8 -*-

import json
import re

from src.fundamental_skill.ai_analyst.html_report_renderer import (
    render_fundamental_html_report,
    write_fundamental_html_report,
)
from src.fundamental_skill.ai_analyst.html_report_runner import run_skeleton


def sample_report():
    result = run_skeleton("002050")
    from pathlib import Path

    payload = json.loads(Path(result["json_path"]).read_text(encoding="utf-8"))
    payload["core_conclusion"].update(
        {
            "title": "核心结论",
            "summary": "公司当前只能形成保守的基本面研究摘要，主要原因是业务构成、客户和订单证据仍需补充。",
        }
    )
    payload["financial_quality_diagnosis"]["final_diagnosis"] = "经营现金流、应收和存货证据仍需结合正式数据复核。"
    payload["valuation_explanation"]["valuation_interpretation"] = "估值只能结合利润质量、现金流和同业可比性解释。"
    payload["risk_analysis"]["business_risks"] = ["新业务兑现仍缺少收入和客户证据。"]
    payload["hero_tags"] = ["高端制造成长", "汽车热管理", "现金流需复核"]
    payload["research_anchor"] = {
        "main_thesis": "制冷空调零部件基本盘与汽车热管理成长验证构成研究主线。",
        "key_conflict": "主业证据较清楚，但新业务和估值消化证据仍有缺口。",
        "current_stage": "成长验证期",
        "what_is_proven": ["制冷空调零部件与汽车零部件收入构成可见"],
        "what_is_unproven": ["机器人或新业务收入与订单待验证"],
    }
    payload["quality_score_breakdown"] = {
        "industry_position": {"score": 6, "max_score": 10, "label": "行业位置", "explanation": "制造业主业锚点清楚。", "evidence_basis": ["业务构成"]},
        "business_quality": {"score": 6, "max_score": 10, "label": "业务质量", "explanation": "毛利率线索可见。", "evidence_basis": ["毛利率"]},
        "growth_realization": {"score": 4, "max_score": 10, "label": "成长兑现", "explanation": "新业务证据不足。", "evidence_basis": ["missing evidence"]},
        "financial_quality": {"score": 6, "max_score": 10, "label": "财务质量", "explanation": "现金流需复核。", "evidence_basis": ["经营现金流"]},
        "valuation_explainability": {"score": 5, "max_score": 10, "label": "估值可解释性", "explanation": "依赖业绩兑现。", "evidence_basis": ["估值指标"]},
        "risk_identifiability": {"score": 5, "max_score": 10, "label": "风险可识别性", "explanation": "数据缺口清楚。", "evidence_basis": ["missing fields"]},
    }
    payload["value_chain_map"] = {
        "upstream": "原材料、阀件和制造配套待验证",
        "company_role": "热管理零部件制造商",
        "downstream": "家电与汽车热管理需求端",
        "profit_source": "规模制造、毛利率稳定性和产品结构",
        "unproven_moats": ["客户结构待验证"],
        "key_bottlenecks": ["新业务订单证据缺失"],
    }
    payload["elasticity_formula"] = {
        "formula_title": "利润弹性",
        "formula_text": "利润弹性 = 收入增长 × 毛利率稳定性 × 费用率控制",
        "key_variables": ["收入", "毛利率", "费用率", "经营现金流", "capex"],
        "interpretation": "用于观察基本面兑现路径。",
        "data_limitations": ["新业务收入缺失"],
    }
    payload["tracking_plan_groups"] = [
        {
            "group_name": "财报跟踪",
            "items": [{"indicator": "毛利率", "frequency": "季度", "why_it_matters": "验证利润质量", "trigger_for_review": "连续下滑时复核"}],
        },
        {"group_name": "公告/订单跟踪", "items": []},
        {"group_name": "行业/政策跟踪", "items": []},
        {"group_name": "风险复核", "items": []},
    ]
    return payload


def test_html_renderer_contains_required_chinese_sections():
    html = render_fundamental_html_report(sample_report())

    assert "核心结论" in html
    assert "财务质量诊断" in html
    assert "估值解释" in html
    assert "风险分析" in html
    assert "必须跟踪指标" in html
    assert "数据质量与未知项" in html
    assert "基本面情景分析" in html
    assert "主题" in html
    assert "研究主线 / 核心矛盾" in html
    assert "六维质量评分" in html
    assert "产业链图谱" in html
    assert "基本面弹性公式" in html
    assert "分层跟踪计划" in html
    assert "财务比例口径提示" in html
    assert "指标" in html
    assert "优先级" in html
    assert "当前状态" in html
    assert "为什么重要" in html
    assert "下一步证据" in html


def test_html_renderer_has_mobile_overflow_guards():
    html = render_fundamental_html_report(sample_report())

    assert "body { margin:0; overflow-x:hidden;" in html
    assert ".hero h1 {" in html
    assert "overflow-wrap:anywhere;" in html
    assert "word-break:break-word;" in html
    assert "nav { display:flex; gap:12px; overflow-x:auto; flex:1; min-width:0; max-width:100%;" in html
    assert ".table-wrap { overflow:auto; max-width:100%;" in html
    assert "@media (max-width:900px)" in html
    assert "table { min-width:640px; }" in html
    assert ".compact-table table { min-width:520px; }" in html


def test_html_renderer_excludes_trading_and_technical_terms():
    html = render_fundamental_html_report(sample_report())
    html_without_footer = re.sub(r"<footer>.*?</footer>", "", html, flags=re.S)

    for forbidden in (
        "K线",
        "目标价",
        "买入",
        "卖出",
        "仓位",
        "止损",
        "止盈",
        "盈亏比",
        "买卖时机",
        "交易终端",
        "技术面模块",
        "technical_skill",
        "trader_skill",
    ):
        assert forbidden not in html_without_footer

    assert "<h2>技术面" not in html
    assert "<h2>目标价" not in html
    assert "<h2>买卖" not in html


def test_html_renderer_allows_safety_boundary_policy_terms():
    report = sample_report()
    report["safety_boundary"]["statement"] = (
        "本报告仅供基本面研究，不构成交易建议，不包含目标价，不包含买卖建议，不包含技术面判断，不连接交易账户。"
    )
    report["safety_boundary"]["forbidden_actions_excluded"] = ["交易建议", "目标价", "买卖建议", "技术面判断"]
    report["report_meta"]["safety_boundary"] = report["safety_boundary"]["statement"]

    html = render_fundamental_html_report(report)

    assert "不构成交易建议" in html
    assert "不包含目标价" in html
    assert "不包含技术面判断" in html
    assert "<h2>技术面" not in html
    assert "<h2>目标价" not in html
    assert "<h2>买卖" not in html


def test_html_renderer_writes_to_output_reports(tmp_path):
    report = sample_report()
    output = tmp_path / "output" / "reports" / "fundamental_report_002050.html"

    html = write_fundamental_html_report(report, output)

    assert output.exists()
    assert output.read_text(encoding="utf-8") == html
    assert "三花" not in html or "基本面分析报告" in html
