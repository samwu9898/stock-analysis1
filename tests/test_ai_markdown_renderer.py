# -*- coding: utf-8 -*-

import json

from src.fundamental_skill.ai_analyst.markdown_renderer import (
    render_ai_report_markdown,
    write_ai_report_markdown,
)


def sample_report():
    return {
        "ai_report_version": "fundamental_ai_report.v1",
        "stock_code": "601698",
        "stock_name": "中国卫通",
        "fundamental_view": "neutral_requires_more_evidence",
        "executive_summary": "????????????????????????????",
        "confidence_explanation": "confidence low",
        "confidence_breakdown": [
            {"dimension": "data_coverage", "level": "medium", "reason": "结构化数据可用，但行业指标缺失"}
        ],
        "supporting_evidence": [],
        "limiting_evidence": [],
        "unknown_or_missing_evidence": [],
        "business_analysis": "????????????????????????????",
        "financial_quality_analysis": "????????????????????????????",
        "valuation_analysis": "????????????????????????????",
        "industry_cycle_analysis": "????????????????????????????",
        "risk_analysis": [],
        "must_track_analysis": [],
        "data_limitations": ["容量利用率缺失，缺失数据不足以判断"],
        "invalidation_watch": [],
        "final_summary": "????????????????????????????",
    }


def sample_evidence_pack():
    return {
        "stock": {
            "code": "601698",
            "name": "中国卫通",
            "strategy_type": "satellite_communication_infrastructure",
            "status": "neutral",
            "confidence": "low",
            "fundamental_score": 42,
        },
        "confidence_basis": {
            "missing_fields": [
                {"field": "satellite.capacity_utilization_or_lease_rate"},
                {"field": "satellite.customer_structure_or_concentration"},
            ]
        },
        "enhanced_must_track_indicators": [
            {
                "indicator_name": "容量利用率 / 出租率",
                "current_status": "missing",
                "current_value": None,
                "priority": "low",
                "why_it_matters": "区分可用容量和实际变现容量",
                "follow_up_question": "后续需要补充可验证公开数据。",
            },
            {
                "indicator_name": "合同负债",
                "current_status": "partial_proxy",
                "current_value": 773835146.63,
                "priority": "low",
                "why_it_matters": "只能作为订单可见度 proxy，不等同真实 backlog",
                "follow_up_question": "后续观察合同负债变化。",
            },
        ],
    }


def test_renderer_replaces_question_mark_summary_with_chinese_fallback():
    markdown = render_ai_report_markdown(sample_report(), evidence_pack=sample_evidence_pack())

    assert "# 601698 中国卫通 AI基本面分析报告" in markdown
    assert "## 一句话结论" in markdown
    assert "## 公司身份与分析框架" in markdown
    assert "## 证据地图" in markdown
    assert "## 必须跟踪指标" in markdown
    assert "当前识别为 satellite_communication_infrastructure" in markdown
    assert "????????" not in markdown
    assert "AI 自由文本损坏" in markdown
    assert "合同负债只能作为订单可见度 proxy，不等同真实 backlog" in markdown
    assert "PE/PB/PS 不能单独作为估值充分依据" in markdown
    assert "置信度表示对当前基本面结论的证据置信度，不等于看好程度。" in markdown
    assert "trader_summary" not in markdown


def test_renderer_writes_and_reads_utf8_markdown(tmp_path):
    output = tmp_path / "ai_report_601698.md"
    markdown = write_ai_report_markdown(sample_report(), output, evidence_pack=sample_evidence_pack())
    read_back = output.read_text(encoding="utf-8")

    assert read_back == markdown
    assert "satellite.capacity_utilization_or_lease_rate" in read_back
    assert "一句话结论" in read_back


def test_renderer_output_can_be_json_serialized_without_ascii_loss():
    markdown = render_ai_report_markdown(sample_report(), evidence_pack=sample_evidence_pack())
    payload = {"markdown": markdown}

    encoded = json.dumps(payload, ensure_ascii=False)

    assert "一句话结论" in encoded


def test_renderer_shows_stale_mismatch_and_garbled_warnings():
    status = {
        "status": "mismatch",
        "label": "报告不一致",
        "warnings": ["报告过期 / 报告与当前数据不一致，请重新生成 AI report。"],
        "can_use_ai_body": False,
    }

    markdown = render_ai_report_markdown(
        sample_report(),
        evidence_pack=sample_evidence_pack(),
        consistency_status=status,
    )

    assert "报告过期 / 不一致" in markdown
    assert "请重新生成 AI report" in markdown
    assert "AI 自由文本损坏" in markdown
    assert "schema" not in markdown.lower()
