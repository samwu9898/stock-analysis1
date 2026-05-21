# -*- coding: utf-8 -*-

from copy import deepcopy

from src.fundamental_skill.ai_analyst.html_report_schema import (
    FundamentalHtmlReport,
    validate_fundamental_html_report,
)
from src.fundamental_skill.ai_analyst.html_report_runner import run_skeleton


def sample_html_report():
    result = run_skeleton("002050")
    # Avoid depending on repository output in schema-focused assertions.
    import json
    from pathlib import Path

    path = Path(result["json_path"])
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["report_meta"]["status"] = "neutral"
    payload["report_meta"]["confidence"] = "low"
    return payload


def test_fundamental_html_report_accepts_complete_structure(tmp_path):
    report = sample_html_report()

    model = FundamentalHtmlReport.model_validate(report)
    validation = validate_fundamental_html_report(report)

    assert model.report_version == "fundamental_html_report.v1"
    assert validation["valid"] is True
    assert validation["schema_errors"] == []


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
