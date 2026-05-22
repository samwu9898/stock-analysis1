# -*- coding: utf-8 -*-

import json

from src.fundamental_skill.ai_analyst.evidence_pack import EvidencePackBuilder
from src.fundamental_skill.ai_analyst.research_intelligence_p1_builder import ResearchIntelligenceP1Builder
from src.fundamental_skill.ai_analyst.research_intelligence_p1_schema import (
    LESS_THAN_TWO_BUCKETS_REASON,
    TRANSMISSION_PATH_FALLBACK,
)

from tests.ai_test_fixtures import sample_fundamental, sample_raw


FORBIDDEN_TERMS = ["买入", "卖出", "加仓", "减仓", "清仓", "止损", "止盈", "目标价", "仓位", "盈亏比", "K线", "技术面"]


def build_pack(sub_type="cooling_liquid_cooling_infrastructure", strategy_type="ai_datacenter_infrastructure"):
    fundamental = sample_fundamental(strategy_type)
    fundamental["stock_code"] = "002837"
    fundamental["stock_name"] = "英维克"
    fundamental["sub_type"] = sub_type
    return EvidencePackBuilder().build(fundamental, sample_raw())


def build_outputs(sub_type="cooling_liquid_cooling_infrastructure", strategy_type="ai_datacenter_infrastructure"):
    return ResearchIntelligenceP1Builder().build(build_pack(sub_type, strategy_type))


def driver_names(pack):
    return {item.driver_factor for item in pack.driver_matrix}


def test_ai_datacenter_cooling_driver_matrix_contains_required_factors():
    pack, questions = build_outputs("cooling_liquid_cooling_infrastructure")
    names = driver_names(pack)

    assert "liquid cooling penetration" in names
    assert "liquid cooling revenue" in names
    assert "customer contracts / order visibility" in names
    assert "capex-to-revenue bridge" in names
    assert questions.questions
    assert all(item.evidence_trigger for item in questions.questions)


def test_ai_datacenter_operator_driver_matrix_contains_required_factors():
    pack, _ = build_outputs("datacenter_operator")
    names = driver_names(pack)

    assert "cabinet / MW buildout" in names
    assert "rack-up / utilization" in names
    assert "PUE / MW / cabinet metrics" in names
    assert "customer deployment cycle" in names
    assert "electricity cost pressure" in names


def test_missing_operating_metrics_are_not_assessable_or_missing():
    pack, _ = build_outputs("datacenter_operator")
    rows = {item.driver_factor: item for item in pack.driver_matrix}

    for name in ["cabinet / MW buildout", "rack-up / utilization", "PUE / MW / cabinet metrics"]:
        row = rows[name]
        assert row.company_transmission_path == TRANSMISSION_PATH_FALLBACK
        assert row.confidence_cap == "not_assessable"
        assert row.data_availability_status == "not_assessable"
        assert row.missing_evidence


def test_builder_uses_exact_transmission_fallback_and_no_vague_paths():
    pack, _ = build_outputs("cooling_liquid_cooling_infrastructure")
    bad_phrases = ["宏观向好，公司受益", "行业空间大，公司有望受益", "政策支持，公司有望兑现"]

    for row in pack.driver_matrix:
        assert not any(phrase in row.company_transmission_path for phrase in bad_phrases)
        if row.company_transmission_path == TRANSMISSION_PATH_FALLBACK:
            assert row.confidence_cap == "not_assessable"
        else:
            assert "evidence_pack." in row.company_transmission_path
            assert "=" in row.company_transmission_path


def test_financial_metrics_do_not_create_macro_or_industry_transmission_path():
    pack, _ = build_outputs("cooling_liquid_cooling_infrastructure")

    for row in pack.driver_matrix:
        if row.layer in {"macro", "policy", "industry"}:
            assert row.company_transmission_path == TRANSMISSION_PATH_FALLBACK
            assert row.confidence_cap == "not_assessable"


def test_source_bucket_counting_uses_bucket_independence_not_file_count():
    builder = ResearchIntelligenceP1Builder()
    summary = builder.source_bucket_summary(
        {
            "source_trace_summary": [
                {"block_name": "news", "trace_count": 5},
                {"block_name": "news", "trace_count": 2},
            ]
        }
    )

    assert summary.source_buckets == ["news_media"]
    assert summary.independent_source_count == 1
    assert summary.consensus_assessment_status == "not_assessable"
    assert summary.not_assessable_reason == LESS_THAN_TWO_BUCKETS_REASON


def test_source_bucket_summary_counts_different_buckets_once_each():
    builder = ResearchIntelligenceP1Builder()
    summary = builder.source_bucket_summary(
        {
            "source_trace_summary": [
                {"block_name": "business_composition", "trace_count": 3},
                {"block_name": "financial_indicator", "trace_count": 10},
                {"block_name": "valuation", "trace_count": 2},
                {"block_name": "valuation", "trace_count": 1},
            ]
        }
    )

    assert summary.independent_source_count == 3
    assert summary.source_buckets == ["company_disclosure", "financial_statement", "structured_data"]


def test_unsupported_strategy_type_outputs_unsupported_pilot_strategy():
    pack, questions = build_outputs(
        sub_type="robotics_core_parts",
        strategy_type="advanced_manufacturing_growth",
    )

    assert len(pack.driver_matrix) == 1
    row = pack.driver_matrix[0]
    assert row.driver_factor == "unsupported_pilot_strategy"
    assert row.data_availability_status == "not_assessable"
    assert row.confidence_cap == "not_assessable"
    assert "仅支持 ai_datacenter_infrastructure" in questions.questions[0].question


def test_p1_outputs_do_not_include_forbidden_safety_terms():
    pack, questions = build_outputs("datacenter_operator")
    text = json.dumps({"pack": pack.model_dump(), "questions": questions.model_dump()}, ensure_ascii=False)

    assert pack.safety_boundary.safe
    assert questions.safety_boundary.safe
    assert not any(term in text for term in FORBIDDEN_TERMS)
