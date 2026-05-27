# -*- coding: utf-8 -*-

import copy
import inspect

import pytest

from src.fundamental_skill.research_report.research_report_v1 import (
    REPORT_TYPE,
    ResearchReportArtifactBoundaryError,
    ResearchReportBuildError,
    ResearchReportSecretError,
)
from src.fundamental_skill.research_report.research_report_v1_presentation import (
    MARKDOWN_OUTPUT_FILENAME,
    PRESENTATION_PROFILE_REGISTRY,
    render_research_report_v1_markdown,
    select_presentation_profile,
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
    "清仓",
    "止损",
    "止盈",
    "技术面交易信号",
    "K线",
)

GRID_TERMS = ("国网 / 南网", "特高压")
SEMICONDUCTOR_TERMS = ("半导体设备", "晶圆厂 capex", "晶圆厂资本开支", "国产替代")
THERMAL_TERMS = ("热管理", "机器人 / 新业务")


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
        "source_provider": "local_fixture",
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


def _fake_report(code: str = "600406", strategy_type: str = "stable_growth") -> dict:
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
        "providers_present": ["local"],
        "periods_observed": ["2025-12-31"],
        "classification_type_coverage": {"available_count": 1, "candidate_count": 10, "coverage_ratio": 0.1},
        "revenue_ratio_coverage": {"available_count": 1, "candidate_count": 10, "coverage_ratio": 0.1},
        "period_status": _gap("business_composition.period"),
        "classification_type_status": _gap("business_composition.classification_type"),
        "revenue_ratio_status": _gap("business_composition.revenue_ratio"),
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
            "analysis": "read-only explainability",
            "evidence_label": "coverage_caveat",
        },
        "impact_on_research_conclusion": [_judgement("impact", "coverage_caveat")],
        "reporting_boundary": _judgement("boundary", "coverage_caveat"),
    }
    stock_name = {"600406": "国电南瑞", "002371": "北方华创", "002050": "三花智控"}.get(code, "未知公司")
    return {
        "code": code,
        "generated_at": "2026-05-27T12:00:00+00:00",
        "report_type": REPORT_TYPE,
        "not_for_trading_advice": True,
        "strategy_type_expected": strategy_type,
        "data_quality_assessment": data_quality,
        "executive_summary": {
            "one_sentence_fundamental_judgement": _judgement("judgement", "manual_review_required"),
            "evidence_strength": _judgement("strength", "coverage_caveat"),
            "primary_opportunity": _judgement("primary_opportunity", "forward_tracking_variable"),
            "primary_risk": _judgement("primary_risk", "auto_accepted_candidate"),
            "largest_evidence_gap": _gap("basic_info.main_business"),
            "data_quality_state": _judgement("quality", "coverage_caveat"),
        },
        "macro_context": {"overview": _judgement("macro"), "transmission_paths": [], "follow_up_variables": []},
        "industry_context": {"overview": _judgement("industry"), "industry_logic": [], "evidence_required_for_conversion": []},
        "company_fundamentals": {
            "profile": _judgement("profile", "manual_review_required"),
            "stock": {
                "stock_code": code,
                "stock_name": stock_name,
                "strategy_type": strategy_type,
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
                "available_segments_preview": [],
                "interpretation": _judgement("composition", "manual_review_required"),
            },
            "trusted_fields": [_judgement("financial_metrics.revenue", "auto_accepted_candidate")],
            "fields_needing_review": [_judgement("basic_info.main_business", "manual_review_required")],
        },
        "opportunity_analysis": [
            _judgement("grid_investment_cycle", "forward_tracking_variable"),
            _judgement("digital_grid", "unsupported_assumption"),
            _judgement("domestic_fab_capex", "unsupported_assumption"),
            _judgement("localization_and_tool_adoption", "manual_review_required"),
            _judgement("nev_thermal_management", "forward_tracking_variable"),
            _judgement("new_business_optionality", "unsupported_assumption"),
        ],
        "risk_analysis": [
            _judgement("receivables_and_cashflow_risk", "auto_accepted_candidate"),
            _judgement("tender_cadence_risk", "forward_tracking_variable"),
            _judgement("semiconductor_cycle_downturn", "forward_tracking_variable"),
            _judgement("inventory_revenue_mismatch", "manual_review_required"),
            _judgement("auto_demand_volatility", "forward_tracking_variable"),
            _judgement("new_business_realization_shortfall", "unsupported_assumption"),
            _judgement("gross_margin_pressure", "forward_tracking_variable"),
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
            _condition("gross_margin_compression"),
        ],
        "follow_up_variables": [
            _tracking("legacy_grid_variable"),
            _tracking("legacy_semiconductor_variable"),
            _tracking("legacy_thermal_variable"),
        ],
        "source_artifact_refs": {
            "fundamental": ["local_fundamental.json"],
            "evidence_pack": ["local_evidence_pack.json"],
            "fact_candidates": "fact_candidates.json",
            "candidate_review_decisions": "candidate_review_decisions.json",
            "score_confidence_explainability": "score_confidence_explainability.json",
            "provider_diff_report": "diff_report.json",
            "research_intelligence_p1": [],
        },
    }


def test_profile_registry_contains_first_batch_and_fallback():
    assert set(PRESENTATION_PROFILE_REGISTRY) >= {
        "stable_growth_grid_equipment",
        "semiconductor_equipment_cycle",
        "advanced_manufacturing_thermal_management",
        "generic_fundamental_report",
    }
    assert "电网投资" in PRESENTATION_PROFILE_REGISTRY["stable_growth_grid_equipment"].keywords
    assert "半导体设备" in PRESENTATION_PROFILE_REGISTRY["semiconductor_equipment_cycle"].keywords
    assert "热管理" in PRESENTATION_PROFILE_REGISTRY["advanced_manufacturing_thermal_management"].keywords


@pytest.mark.parametrize(
    ("code", "strategy", "profile_id"),
    [
        ("600406", "stable_growth", "stable_growth_grid_equipment"),
        ("002371", "semiconductor_cycle", "semiconductor_equipment_cycle"),
        ("002050", "advanced_manufacturing_growth", "advanced_manufacturing_thermal_management"),
    ],
)
def test_select_presentation_profile_for_primary_samples(code, strategy, profile_id):
    selection = select_presentation_profile(_fake_report(code, strategy))

    assert selection["presentation_profile_id"] == profile_id
    assert selection["presentation_profile_selected_by"] == "strategy_type_expected"
    assert selection["fallback_reason"] is None
    assert selection["profile_selection_warning"] is None


def test_unknown_code_and_strategy_fallback_to_generic():
    report = _fake_report("999999", "unknown")

    selection = select_presentation_profile(report)
    markdown = render_research_report_v1_markdown(report)

    assert selection["presentation_profile_id"] == "generic_fundamental_report"
    assert selection["presentation_profile_selected_by"] == "fallback"
    assert selection["fallback_reason"]
    for term in GRID_TERMS + SEMICONDUCTOR_TERMS + THERMAL_TERMS:
        assert term not in markdown


def test_classifier_code_conflict_warns_and_falls_back():
    report = _fake_report("600406", "semiconductor_cycle")

    selection = select_presentation_profile(report)
    markdown = render_research_report_v1_markdown(report)

    assert selection["presentation_profile_id"] == "generic_fundamental_report"
    assert selection["profile_selection_warning"] == "classifier_code_profile_conflict"
    assert "profile_selection_warning: `classifier_code_profile_conflict`" in markdown


def test_render_markdown_keeps_common_skeleton_and_selection_metadata():
    markdown = render_research_report_v1_markdown(_fake_report())

    assert markdown.startswith("# 600406 国电南瑞 基本面研究报告 V1\n")
    for heading in (
        "## 重要声明",
        "## Presentation Profile",
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
    assert "presentation_profile_id: `stable_growth_grid_equipment`" in markdown
    assert "presentation_profile_selected_by: `strategy_type_expected`" in markdown


def test_600406_uses_grid_profile_without_semiconductor_or_robotics_terms():
    markdown = render_research_report_v1_markdown(_fake_report("600406", "stable_growth"))

    assert "电网投资" in markdown
    assert "国网 / 南网" in markdown
    assert "特高压 / 配网" in markdown
    assert "合同负债只能作为订单可见度线索，不等于 backlog" in markdown
    for term in SEMICONDUCTOR_TERMS + ("机器人 / 新业务",):
        assert term not in markdown


def test_002371_uses_semiconductor_profile_without_grid_terms():
    markdown = render_research_report_v1_markdown(_fake_report("002371", "semiconductor_cycle"))

    assert "presentation_profile_id: `semiconductor_equipment_cycle`" in markdown
    assert "半导体设备" in markdown
    assert "国内晶圆厂 capex" in markdown
    assert "国产替代和设备导入" in markdown
    assert "研发投入转化" in markdown
    assert "存货和收入错配" in markdown
    assert "不能把国产替代叙事直接写成收入兑现" in markdown
    assert "不能把研发投入直接写成技术壁垒" in markdown
    assert "不能把库存变化直接写成需求强弱" in markdown
    assert "不能把 capex 直接写成订单" in markdown
    for term in GRID_TERMS:
        assert term not in markdown


def test_002050_uses_thermal_management_profile_without_grid_or_semiconductor_terms():
    markdown = render_research_report_v1_markdown(_fake_report("002050", "advanced_manufacturing_growth"))

    assert "presentation_profile_id: `advanced_manufacturing_thermal_management`" in markdown
    assert "热管理" in markdown
    assert "制冷控制" in markdown
    assert "新能源车热管理" in markdown
    assert "机器人 / 新业务" in markdown
    assert "新业务收入占比" in markdown
    assert "不能把机器人概念直接写成已兑现收入" in markdown
    assert "不能把新业务叙事直接写成利润增长" in markdown
    assert "不能把客户传闻写成已确认事实" in markdown
    assert "不能把行业空间直接写成公司确定性" in markdown
    for term in GRID_TERMS + ("半导体设备",):
        assert term not in markdown


def test_profile_selection_can_use_code_whitelist_when_strategy_missing():
    report = _fake_report("002371", "")
    report.pop("strategy_type_expected")
    report["company_fundamentals"]["stock"]["strategy_type"] = None

    selection = select_presentation_profile(report)

    assert selection["presentation_profile_id"] == "semiconductor_equipment_cycle"
    assert selection["presentation_profile_selected_by"] == "code_whitelist"


def test_profile_selection_can_use_p1_strategy_after_code_and_classifier_miss():
    report = _fake_report("999999", "unknown")
    report["research_intelligence_p1"] = {"strategy_type": "advanced_manufacturing_growth"}

    selection = select_presentation_profile(report)

    assert selection["presentation_profile_id"] == "advanced_manufacturing_thermal_management"
    assert selection["presentation_profile_selected_by"] == "evidence_pack_or_p1_strategy"


def test_profile_does_not_change_evidence_label_or_promote_candidate():
    report = _fake_report("002371", "semiconductor_cycle")
    before = copy.deepcopy(report)
    markdown = render_research_report_v1_markdown(report)

    assert report == before
    assert "待验证假设" in markdown
    assert "需人工复核" in markdown
    assert "候选可用字段" in markdown
    assert "verified_fact" not in markdown
    assert "已核验事实" not in markdown
    assert "经复核事实" not in markdown


def test_markdown_preserves_data_quality_caveats_and_boundaries():
    markdown = render_research_report_v1_markdown(_fake_report("002371", "semiconductor_cycle"))

    assert "数据质量 caveat 必须保留" in markdown
    assert "合同负债只能作为订单可见度线索，不等于 backlog" in markdown
    assert "资本开支只能作为投入节奏线索，不等于订单、产能释放、收入或增长兑现" in markdown
    assert "不能把合同负债直接写成 backlog" in markdown
    assert "不能把研发投入直接写成技术壁垒" in markdown
    assert "不能把库存变化直接写成需求强弱" in markdown


def test_markdown_formats_metrics_and_has_no_forbidden_trading_terms():
    markdown = render_research_report_v1_markdown(_fake_report())

    assert "收入：95.64亿元" in markdown
    assert "经营现金流：-15.14亿元" in markdown
    assert "应收账款：266.52亿元" in markdown
    assert "PE：24.60倍" in markdown
    for term in FORBIDDEN_TRADING_TERMS:
        assert term not in markdown


def test_renderer_blocks_nonselected_profile_terms_if_template_leaks():
    report = _fake_report("002371", "semiconductor_cycle")
    original = PRESENTATION_PROFILE_REGISTRY["semiconductor_equipment_cycle"].follow_up_variables
    mutated = PRESENTATION_PROFILE_REGISTRY["semiconductor_equipment_cycle"]
    object.__setattr__(mutated, "follow_up_variables", original + ("国网 / 南网",))
    try:
        with pytest.raises(ResearchReportBuildError):
            render_research_report_v1_markdown(report)
    finally:
        object.__setattr__(mutated, "follow_up_variables", original)


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
