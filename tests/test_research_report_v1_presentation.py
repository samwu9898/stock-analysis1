# -*- coding: utf-8 -*-

import copy
import inspect

import pytest

from src.fundamental_skill.research_report.research_report_v1 import (
    REPORT_TYPE,
    ResearchReportArtifactBoundaryError,
    ResearchReportSecretError,
)
from src.fundamental_skill.research_report.research_report_v1_presentation import (
    MARKDOWN_OUTPUT_FILENAME,
    render_research_report_v1_markdown,
    write_research_report_v1_markdown,
)
import src.fundamental_skill.research_report.research_report_v1_presentation as presentation_module


FORBIDDEN_TRADING_TERMS = (
    "买入",
    "卖出",
    "持有建议",
    "目标价",
    "仓位",
    "加仓",
    "减仓",
    "止损",
    "技术面交易信号",
    "确定性上涨",
    "必然兑现",
    "强烈推荐",
)


def _judgement(title: str, label: str = "forward_tracking_variable") -> dict:
    return {
        "title": title,
        "analysis": f"{title} analysis",
        "evidence_label": label,
        "supporting_fields": [],
        "caveats": [],
    }


def _metric(field_path: str, value, *, unit: str = "RMB yuan", label: str = "auto_accepted_candidate", as_of_date=None) -> dict:
    return {
        "field_path": field_path,
        "value": value,
        "display_value": None,
        "report_period": None if as_of_date else "2026-03-31",
        "as_of_date": as_of_date,
        "canonical_unit": unit,
        "source_provider": "tushare",
        "evidence_label": label,
        "analysis": "candidate-level metric",
        "caveats": ["Candidate-level evidence only."],
    }


def _review_field(field_path: str) -> dict:
    return {
        "field_path": field_path,
        "issue_type": "manual_review_required",
        "priority": 1,
        "candidate_count": 1,
        "reason": "requires review",
        "evidence_label": "manual_review_required",
        "caveat": "manual review limits conclusion strength",
    }


def _gap(field_path: str, label: str = "manual_review_required") -> dict:
    return {
        "field_path": field_path,
        "status": "manual_review_required",
        "analysis": "gap",
        "evidence_label": label,
        "caveat": "gap remains",
        "required_for_stronger_conclusion": True,
    }


def _condition(title: str) -> dict:
    return {
        "title": title,
        "condition": f"{title} condition",
        "evidence_label": "forward_tracking_variable",
        "supporting_fields": [],
        "caveat": "not a forecast",
    }


def _tracking(variable: str) -> dict:
    return {
        "variable": variable,
        "why_it_matters": f"{variable} matters",
        "evidence_label": "forward_tracking_variable",
    }


def _fake_report() -> dict:
    financial_metrics = [
        _metric("financial_metrics.revenue", 9_564_242_921.53),
        _metric("financial_metrics.net_profit", 721_291_973.43),
        _metric("financial_metrics.gross_margin", 25.0953, unit="percentage_point"),
        _metric("financial_metrics.roe", 1.3591, unit="percentage_point"),
        _metric("financial_metrics.operating_cashflow", -1_514_283_397.01),
        _metric("financial_metrics.accounts_receivable", 26_652_280_492.48),
        _metric("financial_metrics.inventory", 16_590_949_099.58),
        _metric("financial_metrics.contract_liabilities", 8_634_661_875.03),
        _metric("financial_metrics.capex", 451_693_205.88),
    ]
    valuation_metrics = [
        _metric("valuation_metrics.pe_ttm", 24.597, unit="multiple", as_of_date="2026-05-26"),
        _metric("valuation_metrics.pb", 3.8257, unit="multiple", as_of_date="2026-05-26"),
        _metric("valuation_metrics.market_cap", 204_649_146_855.0, as_of_date="2026-05-26"),
    ]
    business_status = {
        "summary": "business composition remains caveated",
        "evidence_label": "manual_review_required",
        "candidate_count": 20,
        "providers_present": ["akshare", "tushare"],
        "periods_observed": ["2025-12-31"],
        "classification_type_coverage": {"available_count": 1, "candidate_count": 10, "coverage_ratio": 0.1},
        "revenue_ratio_coverage": {"available_count": 1, "candidate_count": 10, "coverage_ratio": 0.1},
        "gross_margin_coverage": {"available_count": 8, "candidate_count": 10, "coverage_ratio": 0.8},
        "mapping_missing_count": 4,
        "period_mismatch_count": 2,
        "provider_missing_count": 3,
        "period_status": _gap("business_composition.period"),
        "classification_type_status": _gap("business_composition.classification_type"),
        "revenue_ratio_status": _gap("business_composition.revenue_ratio"),
        "recommended_next_action": "review later",
    }
    data_quality = {
        "auto_accepted_core_fields": [
            {
                "field_path": item["field_path"],
                "value": item["value"],
                "report_period": item["report_period"],
                "as_of_date": item["as_of_date"],
                "source_provider": item["source_provider"],
                "canonical_unit": item["canonical_unit"],
                "evidence_label": "auto_accepted_candidate",
                "caveat": "candidate only",
            }
            for item in financial_metrics[:5] + valuation_metrics
        ],
        "manual_review_required_fields": [
            _review_field("valuation_metrics.as_of_date"),
            _review_field("business_composition.period"),
            _review_field("business_composition.classification_type"),
            _review_field("business_composition.revenue_ratio"),
            _review_field("basic_info.main_business"),
        ],
        "candidate_review_decisions": [
            {
                "field_path": "valuation_metrics.as_of_date",
                "queue_item_type": "valuation_date_review",
                "decision_outcome": "confirmed_for_future_promotion",
                "eligible_for_future_promotion": True,
                "fixture_write_allowed": False,
                "decision_reason": "workflow only",
                "follow_up_type": "none",
                "evidence_label": "manual_review_required",
                "caveat": "workflow status only",
            }
        ],
        "valuation_as_of_date_status": {
            "field_path": "valuation_metrics.as_of_date",
            "status": "same_date_candidate_metadata_available",
            "as_of_date": "2026-05-26",
            "analysis": "same-date candidate metadata",
            "evidence_label": "auto_accepted_candidate",
            "caveat": "same-date candidate metadata only",
        },
        "business_composition_status": business_status,
        "main_business_status": {
            "field_path": "basic_info.main_business",
            "status": "official_source_gap",
            "analysis": "official source needed",
            "evidence_label": "manual_review_required",
            "caveat": "official source needed",
        },
        "score_confidence_explainability_status": {
            "score_summary": {"akshare_score": 65, "tushare_score": 62, "score_delta": -3.0},
            "confidence_summary": {"akshare_confidence": "high", "tushare_confidence": "high", "confidence_delta": "no_drift"},
            "provider_caveats": [],
            "derived_hints": [],
            "narrative_hints": [],
            "limitations": [],
            "analysis": "read-only explainability",
            "evidence_label": "coverage_caveat",
        },
        "diff_report_status": {
            "summary": {"blocker_count": 2},
            "blocker_count": 2,
            "review_required_count": 2,
            "category_counts": {"score_drift": 2},
            "analysis": "read-only diff",
            "evidence_label": "coverage_caveat",
        },
        "impact_on_research_conclusion": [_judgement("impact", "coverage_caveat")],
        "reporting_boundary": _judgement("boundary", "coverage_caveat"),
    }
    return {
        "code": "600406",
        "generated_at": "2026-05-27T12:00:00+00:00",
        "report_type": REPORT_TYPE,
        "not_for_trading_advice": True,
        "data_quality_assessment": data_quality,
        "executive_summary": {
            "one_sentence_fundamental_judgement": _judgement("judgement", "manual_review_required"),
            "evidence_strength": _judgement("strength", "coverage_caveat"),
            "primary_opportunity": _judgement("grid_investment_cycle", "forward_tracking_variable"),
            "primary_risk": _judgement("receivables_and_cashflow_risk", "auto_accepted_candidate"),
            "largest_evidence_gap": _gap("basic_info.main_business"),
            "data_quality_state": _judgement("quality", "coverage_caveat"),
        },
        "macro_context": {"overview": _judgement("macro"), "transmission_paths": [], "follow_up_variables": []},
        "industry_context": {"overview": _judgement("industry"), "industry_logic": [], "evidence_required_for_conversion": []},
        "company_fundamentals": {
            "profile": _judgement("stable_growth_grid_equipment_profile", "manual_review_required"),
            "stock": {
                "stock_code": "600406",
                "stock_name": "国电南瑞",
                "strategy_type": "stable_growth",
                "status": "neutral",
                "confidence": "high",
                "fundamental_score": 65,
                "evidence_label": "coverage_caveat",
                "caveat": "local artifact only",
            },
            "financial_metrics": financial_metrics,
            "valuation_metrics": valuation_metrics,
            "business_composition": {
                "status": business_status,
                "available_segments_preview": [
                    {
                        "period": "2025-12-31",
                        "classification_type": "by_product",
                        "segment_name": "Grid automation",
                        "revenue": 33_422_155_368.42,
                        "revenue_ratio": 50.46,
                        "gross_margin": 30.12,
                        "source_provider": "akshare",
                        "evidence_label": "manual_review_required",
                        "caveat": "preview only",
                    }
                ],
                "interpretation": _judgement("composition", "manual_review_required"),
            },
            "trusted_fields": [_judgement("financial_metrics.revenue", "auto_accepted_candidate")],
            "fields_needing_review": [_judgement("basic_info.main_business", "manual_review_required")],
        },
        "opportunity_analysis": [
            _judgement("grid_investment_cycle", "forward_tracking_variable"),
            _judgement("digital_grid", "unsupported_assumption"),
            _judgement("uhv_and_distribution_grid", "forward_tracking_variable"),
            _judgement("power_automation_and_relay_protection", "manual_review_required"),
            _judgement("stable_operating_quality_candidate", "auto_accepted_candidate"),
        ],
        "risk_analysis": [
            _judgement("tender_cadence_risk", "forward_tracking_variable"),
            _judgement("order_realization_risk", "unsupported_assumption"),
            _judgement("receivables_and_cashflow_risk", "auto_accepted_candidate"),
            _judgement("gross_margin_pressure", "forward_tracking_variable"),
            _judgement("contract_liabilities_visibility_risk", "forward_tracking_variable"),
            _judgement("business_composition_scope_risk", "manual_review_required"),
            _judgement("valuation_date_risk", "auto_accepted_candidate"),
            _judgement("data_quality_risk", "coverage_caveat"),
        ],
        "evidence_gaps": [
            _gap("valuation_metrics.as_of_date", "auto_accepted_candidate"),
            _gap("business_composition.period"),
            _gap("business_composition.classification_type"),
            _gap("business_composition.revenue_ratio"),
            _gap("basic_info.main_business"),
            _gap("score_confidence_explainability.score_drift", "coverage_caveat"),
        ],
        "rebuttal_conditions": [
            _condition("revenue_growth_slowdown"),
            _condition("operating_cashflow_deterioration"),
            _condition("receivables_grow_faster_than_revenue"),
            _condition("contract_liabilities_decline"),
            _condition("gross_margin_compression"),
            _condition("grid_tender_rhythm_weakens"),
            _condition("project_cadence_falls_short"),
            _condition("business_composition_does_not_support_exposure"),
            _condition("valuation_date_stale_or_mismatched"),
        ],
        "follow_up_variables": [
            _tracking("grid_investment_amount"),
            _tracking("state_grid_and_csg_tenders"),
            _tracking("uhv_distribution_grid_project_cadence"),
            _tracking("digital_grid_policy_and_tender_conversion"),
            _tracking("accounts_receivable_turnover"),
            _tracking("operating_cashflow"),
            _tracking("contract_liabilities"),
            _tracking("gross_margin"),
            _tracking("business_composition"),
            _tracking("valuation_as_of_date"),
            _tracking("pe_pb_market_cap_same_date_refresh"),
        ],
        "source_artifact_refs": {
            "fundamental": ["akshare_fundamental.json", "tushare_fundamental.json"],
            "evidence_pack": ["akshare_evidence_pack.json", "tushare_evidence_pack.json"],
            "fact_candidates": "fact_candidates.json",
            "candidate_review_decisions": "candidate_review_decisions.json",
            "score_confidence_explainability": "score_confidence_explainability.json",
            "provider_diff_report": "diff_report.json",
            "research_intelligence_p1": [],
        },
    }


def test_render_markdown_from_fake_report_contains_chinese_headings_and_structure():
    markdown = render_research_report_v1_markdown(_fake_report())

    assert markdown.startswith("# 600406 国电南瑞 基本面研究报告 V1\n")
    for heading in (
        "## 重要声明",
        "## 一句话结论",
        "## 投研速读",
        "## 研究员判断",
        "## 数据质量说明",
        "## 宏观与行业逻辑",
        "## 公司基本面",
        "## 机会分析",
        "## 风险分析",
        "## 证据缺口",
        "## 反证条件",
        "## 后续跟踪清单",
    ):
        assert heading in markdown
    assert markdown.index("## 投研速读") < markdown.index("## 数据质量说明")


def test_markdown_contains_pm_summary_disclaimer_and_600406_terms():
    markdown = render_research_report_v1_markdown(_fake_report())

    assert "不是买卖建议" in markdown
    assert "不提供价格目标" in markdown
    assert "不提供配置比例建议" in markdown
    for term in (
        "600406",
        "国电南瑞",
        "电网设备",
        "电网投资",
        "国网 / 南网",
        "特高压",
        "配网",
        "数字电网",
        "电力自动化",
        "继电保护",
        "调度系统",
        "电力信息通信",
        "应收账款",
        "经营现金流",
        "合同负债",
        "主营构成口径不清",
        "估值数据日期",
    ):
        assert term in markdown


def test_markdown_translates_fields_and_formats_values_in_chinese_units():
    markdown = render_research_report_v1_markdown(_fake_report())

    assert "收入：95.64亿元" in markdown
    assert "经营现金流：-15.14亿元" in markdown
    assert "应收账款：266.52亿元" in markdown
    assert "合同负债：86.35亿元" in markdown
    assert "PE：24.60倍" in markdown
    assert "毛利率：25.10%" in markdown


def test_main_body_does_not_expose_raw_json_field_names():
    markdown = render_research_report_v1_markdown(_fake_report())
    main_body = markdown.split("## 数据质量说明", 1)[0]

    for raw_name in (
        "operating_cashflow",
        "accounts_receivable",
        "contract_liabilities",
        "business_composition",
        "valuation_metrics.as_of_date",
        "financial_metrics.revenue",
    ):
        assert raw_name not in main_body


def test_markdown_has_no_forbidden_trading_advice_terms_and_no_verified_fact_label():
    markdown = render_research_report_v1_markdown(_fake_report())

    for term in FORBIDDEN_TRADING_TERMS:
        assert term not in markdown
    assert "verified_fact" not in markdown
    assert "已核验事实" not in markdown
    assert "候选可信字段" in markdown


def test_markdown_includes_data_quality_caveats_gaps_bear_cases_and_checklist():
    markdown = render_research_report_v1_markdown(_fake_report())

    assert "需人工复核" in markdown
    assert "官方来源缺口" in markdown
    assert "主营构成分类口径" in markdown
    assert "评分与置信度差异" in markdown
    assert "- 如果收入增速明显放缓，则会削弱当前判断。" in markdown
    assert "- [ ] 跟踪电网投资金额及项目节奏" in markdown


def test_writer_only_writes_markdown_under_tmpdir(tmp_path):
    report = _fake_report()
    output_root = tmp_path / "research_reports"

    path = write_research_report_v1_markdown(report, output_root, "20260527T120000")

    assert path == output_root / "20260527T120000" / "600406" / MARKDOWN_OUTPUT_FILENAME
    assert path.suffix == ".md"
    assert path.read_text(encoding="utf-8").startswith("# 600406 国电南瑞 基本面研究报告 V1")
    assert [item for item in output_root.rglob("*") if item.is_file()] == [path]


def test_writer_path_traversal_blocked(tmp_path):
    report = _fake_report()

    with pytest.raises(ResearchReportArtifactBoundaryError):
        write_research_report_v1_markdown(report, tmp_path / "research_reports", "..\\escape")

    bad_report = copy.deepcopy(report)
    bad_report["code"] = "..\\escape"
    with pytest.raises(ResearchReportArtifactBoundaryError):
        write_research_report_v1_markdown(bad_report, tmp_path / "research_reports", "20260527T120000")


def test_writer_secret_scan_catches_token_mcp_and_dotenv_path(tmp_path):
    report = _fake_report()
    secret = "token=A9abcdefABCDEF1234567890abcdefABCDEF1234567890z"
    bad_report = copy.deepcopy(report)
    bad_report["risk_analysis"][0]["analysis"] = secret

    with pytest.raises(ResearchReportSecretError) as exc_info:
        write_research_report_v1_markdown(bad_report, tmp_path / "research_reports", "20260527T120000")
    assert "A9abcdefABCDEF1234567890abcdefABCDEF1234567890z" not in str(exc_info.value)

    mcp_report = copy.deepcopy(report)
    mcp_report["risk_analysis"][0]["analysis"] = "mcp://local-secret-endpoint"
    with pytest.raises(ResearchReportSecretError):
        write_research_report_v1_markdown(mcp_report, tmp_path / "research_reports", "20260527T120000")

    dotenv_report = copy.deepcopy(report)
    dotenv_report["risk_analysis"][0]["analysis"] = "load path/to/.env.local"
    with pytest.raises(ResearchReportSecretError):
        write_research_report_v1_markdown(dotenv_report, tmp_path / "research_reports", "20260527T120000")


def test_presentation_module_has_no_provider_env_network_or_mcp_runtime_imports():
    source = inspect.getsource(presentation_module)

    assert "data_providers" not in source
    assert "tushare_provider" not in source
    assert "akshare_provider" not in source
    assert "provider_router" not in source
    assert "import os" not in source
    assert "os.environ" not in source
    assert "getenv" not in source
    assert "requests" not in source
    assert "socket" not in source
    assert "urllib" not in source
    assert "list_mcp" not in source
    assert "mcp__" not in source
    assert "scoring_engine" not in source
    assert "readiness" not in source
    assert "validator" not in source


def test_render_does_not_mutate_input_report():
    report = _fake_report()
    before = copy.deepcopy(report)

    render_research_report_v1_markdown(report)

    assert report == before
