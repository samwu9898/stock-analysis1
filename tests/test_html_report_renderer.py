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
