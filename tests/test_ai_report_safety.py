# -*- coding: utf-8 -*-

from src.fundamental_skill.ai_analyst.report_schema import validate_ai_report
from src.fundamental_skill.ai_analyst.safety import check_text_safety, detect_garbled_text


def valid_report():
    return {
        "ai_report_version": "fundamental_ai_report.v1",
        "stock_code": "002050",
        "stock_name": "三花智控",
        "fundamental_view": "neutral_requires_more_evidence",
        "executive_summary": "基本面需要更多证据验证。",
        "confidence_explanation": "置信度受缺失字段影响。",
        "confidence_breakdown": [{"dimension": "data_coverage", "level": "medium", "reason": "sample"}],
        "supporting_evidence": [{"evidence_name": "sample"}],
        "limiting_evidence": [{"evidence_name": "sample"}],
        "unknown_or_missing_evidence": [{"evidence_name": "sample"}],
        "business_analysis": "业务结构需要继续验证。",
        "financial_quality_analysis": "财务数据部分可用。",
        "valuation_analysis": "估值数据有限。",
        "industry_cycle_analysis": "行业变量需要继续观察。",
        "risk_analysis": [],
        "must_track_analysis": [],
        "data_limitations": [],
        "invalidation_watch": [],
        "final_summary": "当前仅能形成基本面研究摘要。",
    }


def test_report_schema_accepts_valid_view():
    result = validate_ai_report(valid_report())

    assert result["valid"] is True
    assert result["schema_errors"] == []
    assert result["report_quality_status"] == "ok"


def test_report_schema_rejects_invalid_view():
    report = valid_report()
    report["fundamental_view"] = "bullish"

    result = validate_ai_report(report)

    assert result["valid"] is False
    assert result["schema_errors"]


def test_safety_detects_forbidden_terms_in_report_body():
    result = check_text_safety("这里出现买入表达", allow_policy_context=False)

    assert result["safe"] is False
    assert "买入" in result["blocked_terms"]


def test_detects_garbled_question_mark_ai_report_text():
    report = valid_report()
    report["executive_summary"] = "????????????????????"

    quality = detect_garbled_text(report)
    validation = validate_ai_report(report)

    assert quality["garbled_text_detected"] is True
    assert quality["status"] == "garbled_text_detected"
    assert validation["schema_errors"] == []
    assert validation["report_quality_status"] == "garbled_text_detected"
    assert validation["warnings"]


def test_normal_chinese_report_is_not_garbled():
    quality = detect_garbled_text(valid_report())

    assert quality["garbled_text_detected"] is False
    assert quality["findings"] == []


def test_single_english_question_mark_is_not_garbled():
    report = valid_report()
    report["executive_summary"] = "What changed this quarter? Revenue evidence is still limited."

    quality = detect_garbled_text(report)

    assert quality["garbled_text_detected"] is False
