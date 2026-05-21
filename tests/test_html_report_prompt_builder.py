# -*- coding: utf-8 -*-

from src.fundamental_skill.ai_analyst.evidence_pack import EvidencePackBuilder
from src.fundamental_skill.ai_analyst.html_report_prompt_builder import (
    HtmlReportPromptBuilder,
    derive_metrics_v1,
)
from tests.ai_test_fixtures import sample_fundamental, sample_raw


def test_html_report_prompt_contains_required_constraints():
    pack = EvidencePackBuilder().build(sample_fundamental("advanced_manufacturing_growth"), sample_raw())
    prompt = HtmlReportPromptBuilder().build(pack)

    assert "必须解释，不得只复述数据" in prompt
    assert "不输出交易建议 / 不输出目标价 / 不输出技术面" in prompt
    assert "FundamentalHtmlReport" not in prompt
    assert "fundamental_html_report.v1" in prompt
    assert "必须输出中文" in prompt
    assert "不得把合同负债冒充 backlog" in prompt
    assert "不得用 capex 冒充产能释放" in prompt
    assert "不输出交易建议 / 不输出目标价 / 不输出技术面" in prompt
    assert "mixed stock-flow ratio" in prompt
    assert "应收账款/收入" in prompt


def test_html_report_prompt_includes_schema_and_evidence_pack():
    pack = EvidencePackBuilder().build(sample_fundamental(), sample_raw())
    prompt = HtmlReportPromptBuilder().build(pack)

    assert '"report_meta"' in prompt
    assert '"core_conclusion"' in prompt
    assert '"financial_quality_diagnosis"' in prompt
    assert '"must_track_indicators"' in prompt
    assert '"research_anchor"' in prompt
    assert '"quality_score_breakdown"' in prompt
    assert '"value_chain_map"' in prompt
    assert '"elasticity_formula"' in prompt
    assert '"tracking_plan_groups"' in prompt
    assert '"Evidence Pack"' or "Evidence Pack" in prompt


def test_html_report_prompt_contains_v21_generation_requirements():
    pack = EvidencePackBuilder().build(sample_fundamental("advanced_manufacturing_growth"), sample_raw())
    prompt = HtmlReportPromptBuilder().build(pack)

    assert "`research_anchor`" in prompt
    assert "`quality_score_breakdown`" in prompt
    assert "`value_chain_map`" in prompt
    assert "`elasticity_formula`" in prompt
    assert "`tracking_plan_groups`" in prompt
    assert "`financial_ratio_caveats`" in prompt
    assert "六维质量评分" in prompt
    assert "分层跟踪计划" in prompt
    assert "不得输出股价、目标价、盈亏比" in prompt


def test_derived_metrics_are_missing_safe():
    metrics = derive_metrics_v1({"financial_metrics": {"operating_cashflow": 10, "capex": 3}})

    assert metrics["free_cashflow"]["status"] == "derived"
    assert metrics["free_cashflow"]["value"] == 7
    assert metrics["operating_cashflow_to_revenue"]["status"] == "missing"
