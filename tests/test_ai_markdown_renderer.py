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

    assert "# 601698 AI 基本面报告" in markdown
    assert "## 摘要" in markdown
    assert "当前识别为 satellite_communication_infrastructure" in markdown
    assert "????????" not in markdown
    assert "部分 AI 自由文本字段损坏，当前报告使用结构化 evidence fallback 生成。" in markdown
    assert "合同负债只能作为订单可见度 proxy，不等同真实 backlog" in markdown
    assert "PE/PB/PS 不能单独作为估值充分依据" in markdown


def test_renderer_writes_and_reads_utf8_markdown(tmp_path):
    output = tmp_path / "ai_report_601698.md"
    markdown = write_ai_report_markdown(sample_report(), output, evidence_pack=sample_evidence_pack())
    read_back = output.read_text(encoding="utf-8")

    assert read_back == markdown
    assert "容量利用率 / 出租率" in read_back
    assert "摘要" in read_back


def test_renderer_output_can_be_json_serialized_without_ascii_loss():
    markdown = render_ai_report_markdown(sample_report(), evidence_pack=sample_evidence_pack())
    payload = {"markdown": markdown}

    encoded = json.dumps(payload, ensure_ascii=False)

    assert "摘要" in encoded
