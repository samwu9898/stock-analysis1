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


def build_satellite_pack(code="601698"):
    fundamental = sample_fundamental("satellite_communication_infrastructure")
    fundamental["stock_code"] = code
    fundamental["stock_name"] = "China Satcom"
    fundamental["sub_type"] = None
    fundamental["status"] = "neutral"
    fundamental["confidence"] = "low"
    fundamental["fundamental_score"] = 42
    raw = sample_raw()
    raw["meta"] = {"code": code, "stock_name": "China Satcom"}
    raw["blocks"]["basic_info"] = [
        {
            "stock_code": code,
            "stock_name": "China Satcom",
            "industry": "telecom, broadcast television and satellite transmission services",
            "main_business": "satellite space-segment operation and related application services",
        }
    ]
    raw["blocks"]["financial_indicator"][0].update(
        {
            "period": "2026-03-31",
            "revenue": 542414493.94,
            "gross_margin": 19.04,
            "net_margin": 7.76,
            "operating_cashflow": -37552257.46,
            "accounts_receivable": 973141701.49,
            "contract_liabilities": 773835146.63,
            "capex": 21414263.55,
        }
    )
    raw["blocks"]["business_composition"] = [
        {
            "period": "2025-12-31",
            "classification_type": "by industry",
            "segment_name": "broadcast television and satellite transmission services",
            "revenue": 2644781700.0,
            "revenue_ratio": 1.0,
            "gross_margin": 0.294502,
        },
        {"period": "2025-12-31", "classification_type": "by geography", "segment_name": "overseas", "revenue_ratio": 0.210178},
    ]
    raw["fetch_status"]["basic_info"] = {
        "success": True,
        "missing_fields": [],
        "warnings": [],
        "source_trace": [{"function_name": "stock_individual_info_em", "source_period": "2026-05-20"}],
    }
    raw["fetch_status"]["business_composition"] = {
        "success": True,
        "missing_fields": [],
        "warnings": [],
        "source_trace": [{"function_name": "stock_zygc_ym", "source_period": "2025-12-31"}],
    }
    return EvidencePackBuilder().build(fundamental, raw)


def build_satellite_outputs(code="601698"):
    return ResearchIntelligenceP1Builder().build(build_satellite_pack(code))


def build_low_altitude_pack(code="000099"):
    fundamental = sample_fundamental("low_altitude_economy_infrastructure")
    fundamental["stock_code"] = code
    fundamental["stock_name"] = "CITIC Offshore Helicopter"
    fundamental["sub_type"] = "aviation_operations_service"
    fundamental["status"] = "neutral"
    fundamental["confidence"] = "low"
    fundamental["fundamental_score"] = 63
    raw = sample_raw()
    raw["meta"] = {"code": code, "stock_name": "CITIC Offshore Helicopter"}
    raw["blocks"]["basic_info"] = [
        {
            "stock_code": code,
            "stock_name": "CITIC Offshore Helicopter",
            "industry": "general aviation operation services",
            "main_business": "general aviation operation and low-altitude flight services, including transport and emergency rescue services",
        }
    ]
    raw["blocks"]["financial_indicator"][0].update(
        {
            "period": "2026-03-31",
            "revenue": 502587618.96,
            "gross_margin": 21.236629,
            "net_margin": 17.794997,
            "operating_cashflow": 318600630.86,
            "accounts_receivable": 746917688.8,
            "contract_liabilities": 54125155.85,
            "capex": 68043974.05,
        }
    )
    raw["blocks"]["business_composition"] = [
        {
            "period": "2025-12-31",
            "classification_type": "by industry",
            "segment_name": "general aviation transportation",
            "revenue": 2215984977.85,
            "revenue_ratio": 0.991324,
            "gross_margin": 0.237805,
        },
        {
            "period": "2025-12-31",
            "classification_type": "by product",
            "segment_name": "general aviation transportation service",
            "revenue": 1646294001.73,
            "revenue_ratio": 0.736472,
            "gross_margin": 0.14868,
        },
    ]
    raw["fetch_status"]["basic_info"] = {
        "success": True,
        "missing_fields": [],
        "warnings": [],
        "source_trace": [{"function_name": "stock_individual_info_em", "source_period": "2026-05-20"}],
    }
    raw["fetch_status"]["business_composition"] = {
        "success": True,
        "missing_fields": [],
        "warnings": [],
        "source_trace": [{"function_name": "stock_zygc_ym", "source_period": "2025-12-31"}],
    }
    return EvidencePackBuilder().build(fundamental, raw)


def build_low_altitude_outputs(code="000099"):
    return ResearchIntelligenceP1Builder().build(build_low_altitude_pack(code))


def build_resource_pack(code="000426", *, strategy_type="resource_swing"):
    fundamental = sample_fundamental(strategy_type)
    fundamental["stock_code"] = code
    fundamental["stock_name"] = "Xingye Silver & Tin"
    fundamental["sub_type"] = None
    fundamental["status"] = "supportive"
    fundamental["confidence"] = "high"
    fundamental["fundamental_score"] = 76
    raw = sample_raw()
    raw["meta"] = {"code": code, "stock_name": "Xingye Silver & Tin"}
    raw["blocks"]["basic_info"] = [
        {
            "stock_code": code,
            "stock_name": "Xingye Silver & Tin",
            "industry": "non-ferrous metal mining and processing",
            "main_business": "silver, tin, lead-zinc ore mining and processing",
        }
    ]
    raw["blocks"]["financial_indicator"][0].update(
        {
            "period": "2026-03-31",
            "revenue": 1775000000.0,
            "revenue_yoy": 28.0,
            "gross_margin": 52.5,
            "net_margin": 24.0,
            "operating_cashflow": 620000000.0,
            "accounts_receivable": 360000000.0,
            "inventory": 420000000.0,
            "capex": 229152931.6,
        }
    )
    raw["blocks"]["business_composition"] = [
        {
            "period": "2025-12-31",
            "classification_type": "by product",
            "segment_name": "silver concentrate",
            "revenue": 950000000.0,
            "revenue_ratio": 0.50,
            "gross_margin": 0.61,
        },
        {
            "period": "2025-12-31",
            "classification_type": "by product",
            "segment_name": "tin concentrate",
            "revenue": 550000000.0,
            "revenue_ratio": 0.29,
            "gross_margin": 0.48,
        },
    ]
    raw["fetch_status"]["basic_info"] = {
        "success": True,
        "missing_fields": [],
        "warnings": [],
        "source_trace": [{"function_name": "stock_individual_info_em", "source_period": "2026-05-20"}],
    }
    raw["fetch_status"]["business_composition"] = {
        "success": True,
        "missing_fields": [],
        "warnings": [],
        "source_trace": [{"function_name": "stock_zygc_ym", "source_period": "2025-12-31"}],
    }
    return EvidencePackBuilder().build(fundamental, raw)


def build_resource_outputs(code="000426", *, strategy_type="resource_swing"):
    return ResearchIntelligenceP1Builder().build(build_resource_pack(code, strategy_type=strategy_type))


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


def test_satellite_driver_matrix_contains_required_four_groups():
    pack, questions = build_satellite_outputs()
    names = driver_names(pack)

    assert pack.strategy_type == "satellite_communication_infrastructure"
    assert {
        "satellite communication demand",
        "national satellite communication infrastructure policy",
        "bandwidth / transponder capacity demand",
        "enterprise / broadcast / emergency communication demand",
        "satellite resources",
        "transponder / bandwidth resources",
        "capacity utilization",
        "customer contract duration",
        "lease / service pricing",
        "customer concentration",
        "revenue stability",
        "gross margin stability",
        "capex",
        "depreciation",
        "operating cash flow",
        "receivables",
        "satellite remaining life / replacement capex",
        "satellite failure / launch / replacement risk",
        "remaining useful life risk",
        "capacity utilization risk",
        "customer renewal risk",
        "technology substitution risk",
        "policy / regulatory risk",
    }.issubset(names)
    assert questions.questions


def test_satellite_missing_capacity_operating_fields_are_not_assessable():
    pack, _ = build_satellite_outputs()
    rows = {item.driver_factor: item for item in pack.driver_matrix}

    for name in [
        "transponder / bandwidth resources",
        "capacity utilization",
        "customer contract duration",
        "lease / service pricing",
        "satellite remaining life / replacement capex",
        "satellite failure / launch / replacement risk",
    ]:
        row = rows[name]
        assert row.company_transmission_path == TRANSMISSION_PATH_FALLBACK
        assert row.confidence_cap == "not_assessable"
        assert row.data_availability_status == "not_assessable"
        assert row.missing_evidence


def test_satellite_capex_does_not_equal_satellite_deployment_success():
    pack, _ = build_satellite_outputs()
    row = {item.driver_factor: item for item in pack.driver_matrix}["capex"]

    assert row.company_transmission_path != TRANSMISSION_PATH_FALLBACK
    assert "evidence_pack.financial_metrics.capex=" in row.company_transmission_path
    assert "not satellite deployment success" in row.interpretation_guard
    assert any("launch" in item or "in-orbit" in item for item in row.missing_evidence)


def test_satellite_capacity_resource_not_utilization_or_revenue():
    pack, _ = build_satellite_outputs()
    rows = {item.driver_factor: item for item in pack.driver_matrix}

    assert rows["bandwidth / transponder capacity demand"].company_transmission_path == TRANSMISSION_PATH_FALLBACK
    assert "cannot prove company utilization" in rows["bandwidth / transponder capacity demand"].interpretation_guard
    assert rows["capacity utilization risk"].company_transmission_path == TRANSMISSION_PATH_FALLBACK
    assert "Capacity resources are not utilization or revenue" in rows["capacity utilization risk"].interpretation_guard


def test_satellite_policy_support_not_business_realization():
    pack, _ = build_satellite_outputs()
    rows = {item.driver_factor: item for item in pack.driver_matrix}

    for name in ["national satellite communication infrastructure policy", "policy / regulatory risk"]:
        row = rows[name]
        assert row.company_transmission_path == TRANSMISSION_PATH_FALLBACK
        assert row.confidence_cap == "not_assessable"
        assert "not business realization" in row.interpretation_guard or "not automatic support" in row.interpretation_guard


def test_satellite_company_transmission_path_enforcement_uses_exact_fallback_or_nodes():
    pack, _ = build_satellite_outputs()
    bad_phrases = [
        "卫星通信需求向好，公司受益",
        "政策支持，公司兑现",
        "容量资源丰富，公司收入稳定",
    ]

    for row in pack.driver_matrix:
        assert not any(phrase in row.company_transmission_path for phrase in bad_phrases)
        if row.company_transmission_path == TRANSMISSION_PATH_FALLBACK:
            assert row.confidence_cap == "not_assessable"
        else:
            assert "evidence_pack." in row.company_transmission_path
            assert "=" in row.company_transmission_path


def test_satellite_source_bucket_counting_uses_existing_bucket_rules():
    pack, _ = build_satellite_outputs()

    assert pack.source_bucket_summary.consensus_assessment_status == "not_assessable"
    assert pack.source_bucket_summary.independent_source_count >= 2
    assert "company_disclosure" in pack.source_bucket_summary.source_buckets
    assert "financial_statement" in pack.source_bucket_summary.source_buckets


def test_satellite_outputs_do_not_include_forbidden_safety_terms():
    pack, questions = build_satellite_outputs()
    text = json.dumps({"pack": pack.model_dump(), "questions": questions.model_dump()}, ensure_ascii=False)
    forbidden_terms = FORBIDDEN_TERMS + ["买入", "卖出", "加仓", "减仓", "清仓", "止损", "止盈", "目标价", "仓位", "盈亏比", "K线", "技术面"]

    assert pack.safety_boundary.safe
    assert questions.safety_boundary.safe
    assert not any(term in text for term in forbidden_terms)


def test_low_altitude_driver_matrix_contains_required_four_groups():
    pack, questions = build_low_altitude_outputs()
    names = driver_names(pack)

    assert pack.strategy_type == "low_altitude_economy_infrastructure"
    assert pack.sub_type == "aviation_operations_service"
    assert {
        "low-altitude policy pilot progress",
        "airspace / route approval",
        "local government low-altitude infrastructure spending",
        "aviation safety / regulatory requirements",
        "low-altitude operation demand",
        "low-altitude / general aviation / air-traffic-management revenue contribution",
        "flight hours",
        "flight sorties",
        "platform dispatch volume",
        "route / base / airspace resources",
        "project contracts",
        "project acceptance / delivery",
        "customer type",
        "revenue stability",
        "gross margin stability",
        "operating cash flow",
        "receivables",
        "government / SOE collection cycle",
        "contract liabilities as partial proxy only",
        "capex-to-service-capacity bridge",
        "safety / compliance cost",
        "airspace approval delay",
        "project acceptance delay",
        "safety incident / regulatory penalty",
        "government payment delay",
        "utilization / flight-hour insufficiency",
        "policy pilot does not convert into company revenue",
        "customer concentration",
        "weather / operational disruption risk",
    }.issubset(names)
    assert questions.questions


def test_low_altitude_policy_airspace_and_local_spending_without_bridge_are_not_assessable():
    pack, _ = build_low_altitude_outputs()
    rows = {item.driver_factor: item for item in pack.driver_matrix}

    for name in [
        "low-altitude policy pilot progress",
        "airspace / route approval",
        "local government low-altitude infrastructure spending",
        "low-altitude operation demand",
    ]:
        row = rows[name]
        assert row.company_transmission_path == TRANSMISSION_PATH_FALLBACK
        assert row.confidence_cap == "not_assessable"
        assert row.data_availability_status == "not_assessable"
        assert row.missing_evidence


def test_low_altitude_missing_flight_hours_sorties_and_dispatch_are_not_assessable():
    pack, _ = build_low_altitude_outputs()
    rows = {item.driver_factor: item for item in pack.driver_matrix}

    for name in ["flight hours", "flight sorties", "platform dispatch volume", "utilization / flight-hour insufficiency"]:
        row = rows[name]
        assert row.company_transmission_path == TRANSMISSION_PATH_FALLBACK
        assert row.confidence_cap == "not_assessable"
        assert row.data_availability_status == "not_assessable"
        assert "Do not" in row.interpretation_guard or "Revenue cannot substitute" in row.interpretation_guard


def test_low_altitude_project_contract_and_acceptance_missing_are_not_assessable():
    pack, _ = build_low_altitude_outputs()
    rows = {item.driver_factor: item for item in pack.driver_matrix}

    for name in ["project contracts", "project acceptance / delivery", "project acceptance delay"]:
        row = rows[name]
        assert row.company_transmission_path == TRANSMISSION_PATH_FALLBACK
        assert row.confidence_cap == "not_assessable"
        assert row.data_availability_status == "not_assessable"
    assert "as acceptance" in rows["project acceptance / delivery"].interpretation_guard


def test_low_altitude_government_collection_cycle_missing_is_not_assessable():
    pack, _ = build_low_altitude_outputs()
    rows = {item.driver_factor: item for item in pack.driver_matrix}

    for name in ["government / SOE collection cycle", "government payment delay"]:
        row = rows[name]
        assert row.company_transmission_path == TRANSMISSION_PATH_FALLBACK
        assert row.confidence_cap == "not_assessable"
        assert "certainty" in row.interpretation_guard


def test_low_altitude_capex_does_not_equal_service_capacity_release():
    pack, _ = build_low_altitude_outputs()
    row = {item.driver_factor: item for item in pack.driver_matrix}["capex-to-service-capacity bridge"]

    assert row.company_transmission_path != TRANSMISSION_PATH_FALLBACK
    assert "evidence_pack.financial_metrics.capex=" in row.company_transmission_path
    assert "not service-capacity release" in row.interpretation_guard
    assert any("flight hours" in item or "utilization" in item for item in row.missing_evidence)


def test_low_altitude_contract_liabilities_do_not_replace_backlog():
    pack, _ = build_low_altitude_outputs()
    rows = {item.driver_factor: item for item in pack.driver_matrix}
    project_contracts = rows["project contracts"]
    contract_proxy = rows["contract liabilities as partial proxy only"]

    assert project_contracts.company_transmission_path == TRANSMISSION_PATH_FALLBACK
    assert project_contracts.confidence_cap == "not_assessable"
    assert "not backlog" in project_contracts.interpretation_guard
    assert contract_proxy.company_transmission_path != TRANSMISSION_PATH_FALLBACK
    assert "evidence_pack.financial_metrics.contract_liabilities=" in contract_proxy.company_transmission_path
    assert "must not be labeled backlog" in contract_proxy.interpretation_guard


def test_low_altitude_company_transmission_path_enforcement_uses_exact_fallback_or_nodes():
    pack, _ = build_low_altitude_outputs()
    bad_phrases = [
        "低空经济政策向好，公司受益",
        "空域改革推进，公司飞行量提升",
        "地方政府加大低空投入，公司收入增长",
    ]

    for row in pack.driver_matrix:
        assert not any(phrase in row.company_transmission_path for phrase in bad_phrases)
        if row.company_transmission_path == TRANSMISSION_PATH_FALLBACK:
            assert row.confidence_cap == "not_assessable"
        else:
            assert "evidence_pack." in row.company_transmission_path
            assert "=" in row.company_transmission_path


def test_low_altitude_source_bucket_counting_uses_existing_bucket_rules():
    pack, _ = build_low_altitude_outputs()

    assert pack.source_bucket_summary.consensus_assessment_status == "not_assessable"
    assert pack.source_bucket_summary.independent_source_count >= 2
    assert "company_disclosure" in pack.source_bucket_summary.source_buckets
    assert "financial_statement" in pack.source_bucket_summary.source_buckets


def test_low_altitude_outputs_do_not_include_forbidden_safety_terms():
    pack, questions = build_low_altitude_outputs()
    text = json.dumps({"pack": pack.model_dump(), "questions": questions.model_dump()}, ensure_ascii=False)

    assert pack.safety_boundary.safe
    assert questions.safety_boundary.safe
    assert not any(term in text for term in FORBIDDEN_TERMS)


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


def test_resource_swing_driver_matrix_contains_required_four_groups():
    pack, questions = build_resource_outputs()
    names = driver_names(pack)

    assert pack.strategy_type == "resource_swing"
    assert {
        "core commodity price exposure",
        "commodity price cycle",
        "USD / RMB FX exposure",
        "interest-rate / financing-cost pressure",
        "global demand / inventory cycle",
        "policy / supply constraint",
        "commodity revenue exposure",
        "production volume",
        "sales volume",
        "grade / resource quality",
        "reserves / resources",
        "mine / smelter / processing capacity",
        "inventory",
        "hedging / derivative exposure",
        "cost curve position",
        "revenue sensitivity to commodity price",
        "gross margin sensitivity",
        "operating cash flow",
        "capex: sustaining vs expansionary",
        "debt / liquidity / refinancing pressure",
        "depreciation / depletion",
        "working capital",
        "commodity price volatility",
        "production disruption",
        "resource reserve depletion",
        "environmental / safety / regulatory risk",
        "FX risk",
        "hedging loss / mismatch risk",
        "capex overrun",
        "debt-cycle risk",
    }.issubset(names)
    assert "dividend capacity for resource_core" not in names
    assert questions.questions


def test_resource_core_remains_design_only_unsupported():
    pack, questions = build_resource_outputs(strategy_type="resource_core")

    assert len(pack.driver_matrix) == 1
    row = pack.driver_matrix[0]
    assert row.driver_factor == "unsupported_pilot_strategy"
    assert row.company_transmission_path == TRANSMISSION_PATH_FALLBACK
    assert row.confidence_cap == "not_assessable"
    assert "design-only" in row.not_assessable_reason
    assert "stability" not in questions.questions[0].question.lower()


def test_resource_swing_non_primary_sample_is_unsupported():
    pack, _ = build_resource_outputs(code="603993")

    assert len(pack.driver_matrix) == 1
    row = pack.driver_matrix[0]
    assert row.driver_factor == "unsupported_pilot_strategy"
    assert row.company_transmission_path == TRANSMISSION_PATH_FALLBACK
    assert row.confidence_cap == "not_assessable"
    assert "000426 only" in row.not_assessable_reason


def test_resource_commodity_price_exposure_is_not_company_revenue():
    pack, _ = build_resource_outputs()
    row = {item.driver_factor: item for item in pack.driver_matrix}["core commodity price exposure"]

    assert row.company_transmission_path != TRANSMISSION_PATH_FALLBACK
    assert "evidence_pack.business_composition" in row.company_transmission_path
    assert "evidence_pack.financial_metrics.revenue=" in row.company_transmission_path
    assert "not company revenue" in row.interpretation_guard
    assert "realized selling price" in row.missing_evidence


def test_resource_revenue_sensitivity_requires_realized_price_and_sales_volume():
    pack, _ = build_resource_outputs()
    row = {item.driver_factor: item for item in pack.driver_matrix}["revenue sensitivity to commodity price"]

    assert row.company_transmission_path == TRANSMISSION_PATH_FALLBACK
    assert row.confidence_cap == "not_assessable"
    assert row.data_availability_status == "not_assessable"
    assert "Realized selling price and sales volume are both required" in row.not_assessable_reason
    assert "realized price" in row.research_question
    assert "sales volume" in row.research_question
    assert "pricing formula" in row.research_question
    assert "pricing lag" in row.research_question


def test_resource_segment_revenue_and_revenue_yoy_do_not_infer_price_transmission():
    pack, _ = build_resource_outputs()
    row = {item.driver_factor: item for item in pack.driver_matrix}["revenue sensitivity to commodity price"]

    assert any("financial_metrics.revenue_yoy=" in item for item in row.available_evidence)
    assert any("business_composition" in item for item in row.available_evidence)
    assert row.company_transmission_path == TRANSMISSION_PATH_FALLBACK
    assert "segment revenue plus revenue YoY" in row.interpretation_guard


def test_resource_inventory_decline_and_revenue_growth_do_not_infer_demand():
    pack, _ = build_resource_outputs()
    rows = {item.driver_factor: item for item in pack.driver_matrix}

    for name in ["inventory", "working capital"]:
        row = rows[name]
        assert "not an operating demand signal" in row.interpretation_guard
        assert "sales volume" in row.missing_evidence
        assert "production / sales reconciliation" in row.missing_evidence


def test_resource_missing_grade_data_does_not_infer_quality_good_or_bad():
    pack, _ = build_resource_outputs()
    row = {item.driver_factor: item for item in pack.driver_matrix}["grade / resource quality"]

    assert row.company_transmission_path == TRANSMISSION_PATH_FALLBACK
    assert row.confidence_cap == "not_assessable"
    assert "Absence of grade data is not proof of poor resource quality" in row.interpretation_guard
    assert "poor resource quality" not in row.research_question


def test_resource_capex_aggregate_only_does_not_infer_capacity_or_output():
    pack, _ = build_resource_outputs()
    row = {item.driver_factor: item for item in pack.driver_matrix}["capex: sustaining vs expansionary"]
    text = json.dumps(row.model_dump(), ensure_ascii=False)

    assert row.company_transmission_path != TRANSMISSION_PATH_FALLBACK
    assert "evidence_pack.financial_metrics.capex=" in row.company_transmission_path
    assert "cash outflow / investment observation" in row.interpretation_guard
    assert not any(term in text for term in ["产能释放", "投产", "释放", "产量增长"])


def test_resource_hedging_disclosure_missing_keeps_status_not_assessable():
    pack, _ = build_resource_outputs()
    rows = {item.driver_factor: item for item in pack.driver_matrix}

    for name in ["hedging / derivative exposure", "hedging loss / mismatch risk"]:
        row = rows[name]
        assert row.company_transmission_path == TRANSMISSION_PATH_FALLBACK
        assert row.confidence_cap == "not_assessable"
        assert "not assessable" in row.interpretation_guard
        assert "hedged" in row.interpretation_guard
        assert "unhedged" in row.interpretation_guard


def test_resource_missing_data_does_not_become_not_applicable():
    pack, _ = build_resource_outputs()

    assert all(row.data_availability_status != "not_applicable" for row in pack.driver_matrix)
    assert {row.data_availability_status for row in pack.driver_matrix}.issubset({"partial", "available", "not_assessable"})


def test_resource_company_transmission_path_minimum_standard_applies():
    builder = ResearchIntelligenceP1Builder()
    financial_only_pack = {
        "stock": {"code": "000426", "name": "No Business Node", "strategy_type": "resource_swing"},
        "financial_metrics": {"revenue": 100, "gross_margin": 20},
    }
    business_only_pack = {
        "stock": {"code": "000426", "name": "Business Node Only", "strategy_type": "resource_swing"},
        "basic_info": {"main_business": "silver and tin mining"},
        "business_composition": [{"segment_name": "silver concentrate", "revenue_ratio": 0.5}],
    }

    financial_pack, _ = builder.build(financial_only_pack)
    financial_row = {item.driver_factor: item for item in financial_pack.driver_matrix}["commodity revenue exposure"]
    assert financial_row.company_transmission_path == TRANSMISSION_PATH_FALLBACK
    assert financial_row.confidence_cap == "not_assessable"

    business_pack, _ = builder.build(business_only_pack)
    business_row = {item.driver_factor: item for item in business_pack.driver_matrix}["commodity revenue exposure"]
    assert business_row.company_transmission_path != TRANSMISSION_PATH_FALLBACK
    assert business_row.confidence_cap == "low"
    assert "financial_metrics" not in business_row.company_transmission_path


def test_resource_source_bucket_counting_uses_existing_bucket_rules():
    builder = ResearchIntelligenceP1Builder()
    pack, _ = builder.build(
        {
            "stock": {"code": "000426", "name": "Resource", "strategy_type": "resource_swing"},
            "source_trace_summary": [
                {"block_name": "news", "trace_count": 3},
                {"block_name": "news", "trace_count": 2},
            ],
        }
    )

    assert pack.source_bucket_summary.source_buckets == ["news_media"]
    assert pack.source_bucket_summary.independent_source_count == 1
    assert pack.source_bucket_summary.consensus_assessment_status == "not_assessable"
    assert pack.source_bucket_summary.not_assessable_reason == LESS_THAN_TWO_BUCKETS_REASON


def test_resource_outputs_do_not_include_forbidden_safety_terms():
    pack, questions = build_resource_outputs()
    text = json.dumps({"pack": pack.model_dump(), "questions": questions.model_dump()}, ensure_ascii=False)

    assert pack.safety_boundary.safe
    assert questions.safety_boundary.safe
    assert not any(term in text for term in FORBIDDEN_TERMS)
