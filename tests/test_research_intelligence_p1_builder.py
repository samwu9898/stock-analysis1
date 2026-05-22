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


def build_cxo_pack(sub_type="integrated_cxo_platform", code="603259"):
    fundamental = sample_fundamental("life_science_cxo_services")
    fundamental["stock_code"] = code
    fundamental["stock_name"] = "CXO Sample"
    fundamental["sub_type"] = sub_type
    raw = sample_raw()
    raw["blocks"]["financial_indicator"][0].update(
        {
            "revenue": 40300000000,
            "gross_margin": 39.5,
            "net_margin": 22.0,
            "operating_cashflow": 9200000000,
            "accounts_receivable": 7100000000,
            "contract_liabilities": 2300000000,
            "capex": 4200000000,
        }
    )
    if sub_type == "cdmo_manufacturing_services":
        raw["blocks"]["business_composition"] = [
            {"period": "2025-12-31", "segment_name": "CDMO / CMC manufacturing outsourcing services", "revenue_ratio": 0.78, "gross_margin": 0.38},
            {"period": "2025-12-31", "segment_name": "overseas", "revenue_ratio": 0.72},
        ]
    elif sub_type == "clinical_cro_services":
        raw["blocks"]["business_composition"] = [
            {"period": "2025-12-31", "segment_name": "clinical CRO and SMO services", "revenue_ratio": 0.82, "gross_margin": 0.41},
            {"period": "2025-12-31", "segment_name": "overseas", "revenue_ratio": 0.36},
        ]
    else:
        raw["blocks"]["business_composition"] = [
            {"period": "2025-12-31", "segment_name": "drug discovery and chemistry CRO/CDMO services", "revenue_ratio": 0.80, "gross_margin": 0.52},
            {"period": "2025-12-31", "segment_name": "testing and biology services", "revenue_ratio": 0.14, "gross_margin": 0.32},
            {"period": "2025-12-31", "segment_name": "overseas", "revenue_ratio": 0.83},
        ]
    return EvidencePackBuilder().build(fundamental, raw)


def build_cxo_outputs(sub_type="integrated_cxo_platform", code="603259"):
    return ResearchIntelligenceP1Builder().build(build_cxo_pack(sub_type, code))


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
    assert "does not support this strategy_type" in questions.questions[0].question


def test_cxo_integrated_platform_driver_matrix_contains_required_factors():
    pack, questions = build_cxo_outputs("integrated_cxo_platform", "603259")
    names = driver_names(pack)

    assert "global biotech / pharma R&D outsourcing demand" in names
    assert "backlog / new signed orders" in names
    assert "contract liabilities as partial proxy only" in names
    assert "CXO revenue contribution" in names
    assert "overseas revenue / US customer exposure" in names
    assert "margin and cash conversion" in names
    assert "integrated platform business mix" in names
    assert questions.questions
    assert pack.strategy_type == "life_science_cxo_services"
    assert pack.sub_type == "integrated_cxo_platform"


def test_cxo_cdmo_driver_matrix_contains_required_factors():
    pack, _ = build_cxo_outputs("cdmo_manufacturing_services", "002821")
    names = driver_names(pack)

    assert "CDMO capacity utilization" in names
    assert "capex-to-revenue / utilization bridge" in names
    assert "commercial-stage CDMO projects" in names
    assert "GMP / FDA / NMPA compliance event" in names
    assert "one-off large order / project volatility" in names
    assert "capacity absorption risk" in names


def test_cxo_clinical_cro_driver_matrix_contains_required_factors():
    pack, _ = build_cxo_outputs("clinical_cro_services", "300347")
    names = driver_names(pack)

    assert "clinical project pipeline / project stage" in names
    assert "SMO / data-statistics revenue" in names
    assert "clinical project delivery / collection" in names
    assert "receivables / collection cycle" in names
    assert "customer loss / project cancellation" in names


def test_cxo_contract_liabilities_do_not_replace_backlog():
    pack, _ = build_cxo_outputs("integrated_cxo_platform")
    rows = {item.driver_factor: item for item in pack.driver_matrix}

    backlog = rows["backlog / new signed orders"]
    contract_proxy = rows["contract liabilities as partial proxy only"]

    assert backlog.company_transmission_path == TRANSMISSION_PATH_FALLBACK
    assert backlog.confidence_cap == "not_assessable"
    assert "contract liabilities" in backlog.interpretation_guard.lower()
    assert contract_proxy.company_transmission_path != TRANSMISSION_PATH_FALLBACK
    assert "evidence_pack.financial_metrics.contract_liabilities=" in contract_proxy.company_transmission_path
    assert "must not be labeled backlog" in contract_proxy.interpretation_guard


def test_cxo_biosecure_without_company_impact_is_not_assessable():
    pack, _ = build_cxo_outputs("integrated_cxo_platform")
    row = {item.driver_factor: item for item in pack.driver_matrix}["overseas regulatory / Biosecure Act risk"]

    assert row.company_transmission_path == TRANSMISSION_PATH_FALLBACK
    assert row.confidence_cap == "not_assessable"
    assert row.data_availability_status == "not_assessable"
    assert "company-specific evidence" in row.interpretation_guard


def test_cxo_cdmo_utilization_missing_is_not_assessable():
    pack, _ = build_cxo_outputs("cdmo_manufacturing_services", "002821")
    row = {item.driver_factor: item for item in pack.driver_matrix}["CDMO capacity utilization"]

    assert row.company_transmission_path == TRANSMISSION_PATH_FALLBACK
    assert row.confidence_cap == "not_assessable"
    assert "Do not infer CDMO utilization from capex" in row.interpretation_guard


def test_cxo_clinical_project_stage_missing_is_not_assessable():
    pack, _ = build_cxo_outputs("clinical_cro_services", "300347")
    row = {item.driver_factor: item for item in pack.driver_matrix}["clinical project pipeline / project stage"]

    assert row.company_transmission_path == TRANSMISSION_PATH_FALLBACK
    assert row.confidence_cap == "not_assessable"
    assert "Do not fabricate clinical project count" in row.interpretation_guard


def test_cxo_company_transmission_path_enforcement_uses_exact_fallback_or_nodes():
    pack, _ = build_cxo_outputs("integrated_cxo_platform")
    bad_phrases = [
        "全球研发外包需求向好，公司受益",
        "海外监管风险存在，公司承压",
        "CXO 行业景气回升，公司有望增长",
    ]

    for row in pack.driver_matrix:
        assert not any(phrase in row.company_transmission_path for phrase in bad_phrases)
        if row.company_transmission_path == TRANSMISSION_PATH_FALLBACK:
            assert row.confidence_cap == "not_assessable"
        else:
            assert "evidence_pack." in row.company_transmission_path
            assert "=" in row.company_transmission_path


def test_cxo_source_bucket_counting_uses_existing_bucket_rules():
    pack, _ = build_cxo_outputs("integrated_cxo_platform")

    assert pack.source_bucket_summary.consensus_assessment_status == "not_assessable"
    assert pack.source_bucket_summary.independent_source_count >= 1
    assert "financial_statement" in pack.source_bucket_summary.source_buckets


def test_cxo_outputs_do_not_include_forbidden_safety_terms():
    pack, questions = build_cxo_outputs("cdmo_manufacturing_services", "300363")
    text = json.dumps({"pack": pack.model_dump(), "questions": questions.model_dump()}, ensure_ascii=False)

    assert pack.safety_boundary.safe
    assert questions.safety_boundary.safe
    assert not any(term in text for term in FORBIDDEN_TERMS)


def test_p1_outputs_do_not_include_forbidden_safety_terms():
    pack, questions = build_outputs("datacenter_operator")
    text = json.dumps({"pack": pack.model_dump(), "questions": questions.model_dump()}, ensure_ascii=False)

    assert pack.safety_boundary.safe
    assert questions.safety_boundary.safe
    assert not any(term in text for term in FORBIDDEN_TERMS)
