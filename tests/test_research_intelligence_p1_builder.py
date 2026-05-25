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


def build_semiconductor_pack(
    code="002371",
    *,
    strategy_type="semiconductor_cycle",
    operating_cashflow=748055666.52,
    include_customer_qualification=False,
):
    indicators = [
        {"indicator_name": "inventory", "current_status": "available", "current_value": 28602898183.2},
        {"indicator_name": "order / contract liabilities", "current_status": "partial_proxy", "current_value": 4202521948.54},
        {"indicator_name": "localization revenue", "current_status": "missing", "current_value": None},
        {"indicator_name": "R&D expense ratio", "current_status": "available", "current_value": "13.59%"},
        {"indicator_name": "capex", "current_status": "available", "current_value": 468631710.94},
    ]
    if include_customer_qualification:
        indicators.append({"indicator_name": "customer qualification", "current_status": "available", "current_value": "pilot validation"})
    return {
        "stock": {"code": code, "name": "NAURA", "strategy_type": strategy_type, "status": "neutral", "confidence": "medium", "fundamental_score": 67},
        "basic_info": {
            "stock_code": code,
            "stock_name": "NAURA",
            "industry": "specialized equipment manufacturing",
            "main_business": "semiconductor equipment and integrated-circuit manufacturing equipment",
        },
        "financial_metrics": {
            "period": "20260331",
            "revenue": 10322863908.82,
            "revenue_yoy": {"raw_value": 25.79609, "display_value": "25.80%"},
            "gross_margin": {"raw_value": 40.772789, "display_value": "40.77%"},
            "net_profit": 1634739048.68,
            "operating_cashflow": operating_cashflow,
            "inventory": 28602898183.2,
            "accounts_receivable": 8780279745.35,
            "contract_liabilities": 4202521948.54,
            "r_and_d_expense": 1402436311.27,
            "r_and_d_expense_ratio": {"raw_value": 13.585728957171844, "display_value": "13.59%"},
            "capex": 468631710.94,
        },
        "business_composition": [
            {
                "period": "2025-12-31",
                "classification_type": "by product",
                "segment_name": "electronic process equipment",
                "revenue": 36731219888.81,
                "revenue_ratio": {"raw_value": 0.933375, "display_value": "93.34%"},
                "gross_margin": {"raw_value": 0.39177, "display_value": "39.18%"},
            },
            {
                "period": "2025-12-31",
                "classification_type": "by product",
                "segment_name": "electronic components",
                "revenue": 2579277891.07,
                "revenue_ratio": {"raw_value": 0.065542, "display_value": "6.55%"},
                "gross_margin": {"raw_value": 0.529509, "display_value": "52.95%"},
            },
        ],
        "enhanced_must_track_indicators": indicators,
        "risk_flags": [
            {"name": "semiconductor cycle volatility risk", "severity": "medium"},
            {"name": "localization realization risk", "severity": "medium"},
        ],
        "unknown_or_missing_evidence": [
            {"evidence_name": "new business revenue or order", "evidence_value": None},
            {"evidence_name": "large customer revenue share", "evidence_value": None},
        ],
        "source_trace_summary": [
            {"block_name": "business_composition", "trace_count": 1},
            {"block_name": "financial_indicator", "trace_count": 16},
            {"block_name": "news", "trace_count": 0},
        ],
    }


def build_semiconductor_outputs(code="002371", *, strategy_type="semiconductor_cycle", operating_cashflow=748055666.52):
    return ResearchIntelligenceP1Builder().build(
        build_semiconductor_pack(code, strategy_type=strategy_type, operating_cashflow=operating_cashflow)
    )


def build_advanced_manufacturing_pack(
    code="002050",
    *,
    strategy_type="advanced_manufacturing_growth",
    operating_cashflow=1105790187.12,
    include_robotics_layout_segment=False,
):
    business_composition = [
        {
            "period": "2025-12-31",
            "classification_type": "按行业分类",
            "segment_name": "通用设备制造业",
            "revenue": 31011744510.27,
            "revenue_ratio": {"raw_value": 1.0, "display_value": "100.00%"},
            "gross_margin": {"raw_value": 0.28777, "display_value": "28.78%"},
        },
        {
            "period": "2025-12-31",
            "classification_type": "按产品分类",
            "segment_name": "制冷空调电器零部件",
            "revenue": 18584743718.09,
            "revenue_ratio": {"raw_value": 0.599281, "display_value": "59.93%"},
            "gross_margin": {"raw_value": 0.287687, "display_value": "28.77%"},
        },
        {
            "period": "2025-12-31",
            "classification_type": "按产品分类",
            "segment_name": "汽车零部件",
            "revenue": 12427000792.18,
            "revenue_ratio": {"raw_value": 0.400719, "display_value": "40.07%"},
            "gross_margin": {"raw_value": 0.287894, "display_value": "28.79%"},
        },
        {
            "period": "2025-12-31",
            "classification_type": "按地区分类",
            "segment_name": "国外销售",
            "revenue": 13323488931.4,
            "revenue_ratio": {"raw_value": 0.429627, "display_value": "42.96%"},
            "gross_margin": {"raw_value": 0.311851, "display_value": "31.19%"},
        },
    ]
    if include_robotics_layout_segment:
        business_composition.append(
            {
                "period": "2025-12-31",
                "classification_type": "按产品分类",
                "segment_name": "机器人关键零部件布局",
            }
        )
    return {
        "stock": {"code": code, "name": "三花智控", "strategy_type": strategy_type, "status": "neutral", "confidence": "high", "fundamental_score": 68},
        "basic_info": {
            "stock_code": code,
            "stock_name": "三花智控",
            "industry": "通用设备制造业",
            "main_business": "制冷空调控制元器件、汽车热管理零部件，并积极布局机器人执行器相关零部件。",
        },
        "financial_metrics": {
            "period": "20260331",
            "revenue": 7773555419.29,
            "revenue_yoy": {"raw_value": 1.357397, "display_value": "1.36%"},
            "gross_margin": {"raw_value": 27.796688, "display_value": "27.80%"},
            "operating_cashflow": operating_cashflow,
            "accounts_receivable": 7010919404.89,
            "contract_liabilities": 80754056.98,
            "inventory": 5879322018.99,
            "capex": 521898492.14,
            "r_and_d_expense": 367461670.95,
            "r_and_d_expense_ratio": {"raw_value": 4.727073406309647, "display_value": "4.73%"},
        },
        "valuation_metrics": {"pe_ttm": 40.1, "pb": 6.2, "market_cap": 250000000000},
        "business_composition": business_composition,
        "enhanced_must_track_indicators": [
            {"indicator_name": "新业务收入或订单", "current_status": "missing", "current_value": None},
            {"indicator_name": "合同负债", "current_status": "partial_proxy", "current_value": 80754056.98},
            {"indicator_name": "大客户收入占比", "current_status": "missing", "current_value": None},
            {"indicator_name": "应收账款", "current_status": "available", "current_value": 7010919404.89},
            {"indicator_name": "存货", "current_status": "available", "current_value": 5879322018.99},
            {"indicator_name": "研发费用率", "current_status": "available", "current_value": "4.73%"},
        ],
        "latest_news": [
            {"title": "机器人主题新闻", "summary": "unverified context only"},
        ],
        "source_trace_summary": [
            {"block_name": "business_composition", "trace_count": 1},
            {"block_name": "financial_indicator", "trace_count": 16},
            {"block_name": "news", "trace_count": 3},
        ],
    }


def build_advanced_manufacturing_outputs(**kwargs):
    return ResearchIntelligenceP1Builder().build(build_advanced_manufacturing_pack(**kwargs))


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


def test_semiconductor_driver_matrix_contains_required_factors():
    pack, questions = build_semiconductor_outputs()
    names = driver_names(pack)

    assert pack.strategy_type == "semiconductor_cycle"
    assert pack.stock_code == "002371"
    assert {
        "semiconductor capex cycle",
        "downstream demand cycle",
        "inventory cycle",
        "localization / domestic substitution",
        "export control / sanctions / overseas restriction",
        "equipment sub-chain classification",
        "semiconductor-related revenue contribution",
        "product / equipment / material segment exposure",
        "customer qualification / customer adoption",
        "order visibility",
        "backlog / contract liabilities as partial proxy only",
        "localization revenue evidence",
        "R&D intensity and product conversion",
        "revenue growth quality",
        "gross margin recovery or pressure",
        "inventory level and inventory turnover",
        "receivables and cash conversion",
        "operating cash flow",
        "capex discipline",
        "R&D expense and R&D ratio as input evidence only",
        "impairment / inventory write-down risk",
        "inventory overbuild",
        "downstream capex slowdown",
        "customer qualification failure",
        "localization narrative without revenue",
        "R&D overread commercialization risk",
        "export control / supply-chain restriction",
        "margin pressure from product mix or price competition",
        "capex without utilization or revenue bridge",
        "contract liabilities / operating cash flow signal consistency",
    }.issubset(names)
    assert questions.questions


def test_semiconductor_002371_equipment_first_version_and_other_subchains_boundary():
    pack, _ = build_semiconductor_outputs()
    rows = {item.driver_factor: item for item in pack.driver_matrix}

    equipment = rows["equipment sub-chain classification"]
    assert equipment.company_transmission_path != TRANSMISSION_PATH_FALLBACK
    assert "evidence_pack.business_composition" in equipment.company_transmission_path
    assert "evidence_pack.financial_metrics.revenue=" in equipment.company_transmission_path

    for name in ["materials sub-chain boundary", "fabless sub-chain boundary", "foundry sub-chain boundary", "OSAT sub-chain boundary"]:
        row = rows[name]
        assert row.data_availability_status == "not_assessable"
        assert row.confidence_cap == "not_assessable"
        assert row.data_availability_status != "not_applicable"
        assert "Do not apply equipment order logic" in row.interpretation_guard


def test_semiconductor_revenue_yoy_and_margin_do_not_create_cycle_or_demand_conclusion():
    pack, _ = build_semiconductor_outputs()
    rows = {item.driver_factor: item for item in pack.driver_matrix}
    text = json.dumps(pack.model_dump(), ensure_ascii=False).lower()

    assert rows["revenue growth quality"].company_transmission_path != TRANSMISSION_PATH_FALLBACK
    assert "not semiconductor cycle transmission" in rows["revenue growth quality"].interpretation_guard
    assert "cycle recovery" not in text
    assert "strong demand" not in text


def test_semiconductor_contract_liabilities_remain_partial_proxy_not_backlog():
    pack, _ = build_semiconductor_outputs()
    rows = {item.driver_factor: item for item in pack.driver_matrix}

    order_visibility = rows["order visibility"]
    contract_proxy = rows["backlog / contract liabilities as partial proxy only"]

    assert order_visibility.company_transmission_path == TRANSMISSION_PATH_FALLBACK
    assert order_visibility.data_availability_status == "missing"
    assert order_visibility.confidence_cap == "not_assessable"
    assert "not backlog" in order_visibility.interpretation_guard
    assert contract_proxy.company_transmission_path != TRANSMISSION_PATH_FALLBACK
    assert contract_proxy.data_availability_status == "partial"
    assert contract_proxy.confidence_cap == "low"
    assert "partial proxy only" in contract_proxy.interpretation_guard
    assert "not backlog or confirmed delivery" in contract_proxy.interpretation_guard


def test_semiconductor_rd_ratio_does_not_output_moat_or_technology_barrier():
    pack, questions = build_semiconductor_outputs()
    rows = {item.driver_factor: item for item in pack.driver_matrix}
    text = json.dumps({"pack": pack.model_dump(), "questions": questions.model_dump()}, ensure_ascii=False).lower()

    assert rows["R&D expense and R&D ratio as input evidence only"].confidence_cap == "low"
    assert "input evidence only" in rows["R&D expense and R&D ratio as input evidence only"].interpretation_guard
    assert "moat" not in text
    assert "护城河" not in text
    assert "技术壁垒" not in text


def test_semiconductor_export_control_without_company_impact_is_not_operating_fact():
    pack, _ = build_semiconductor_outputs()
    rows = {item.driver_factor: item for item in pack.driver_matrix}
    text = json.dumps(pack.model_dump(), ensure_ascii=False).lower()

    for name in ["export control / sanctions / overseas restriction", "export control / supply-chain restriction"]:
        row = rows[name]
        assert row.company_transmission_path == TRANSMISSION_PATH_FALLBACK
        assert row.confidence_cap == "not_assessable"
        assert "company-level" in row.not_assessable_reason or "Company-level" in row.not_assessable_reason
    assert "export controls benefit domestic leaders" not in text
    assert "supply disruption" not in text
    assert "revenue decline" not in text


def test_semiconductor_customer_qualification_absent_is_missing_not_assessable():
    pack, _ = build_semiconductor_outputs()
    rows = {item.driver_factor: item for item in pack.driver_matrix}

    for name in ["customer qualification / customer adoption", "customer qualification failure"]:
        row = rows[name]
        assert row.data_availability_status == "missing"
        assert row.confidence_cap == "not_assessable"
        assert row.company_transmission_path == TRANSMISSION_PATH_FALLBACK
        assert "Do not infer" in row.interpretation_guard


def test_semiconductor_inventory_and_capex_are_observations_not_demand_or_capacity():
    pack, _ = build_semiconductor_outputs()
    rows = {item.driver_factor: item for item in pack.driver_matrix}
    text = json.dumps(pack.model_dump(), ensure_ascii=False).lower()

    assert rows["inventory cycle"].company_transmission_path != TRANSMISSION_PATH_FALLBACK
    assert "working-capital observation only" in rows["inventory cycle"].interpretation_guard
    assert "strong demand" not in text
    assert "demand deterioration" not in text

    assert rows["capex discipline"].company_transmission_path != TRANSMISSION_PATH_FALLBACK
    assert "cash outflow / investment observation only" in rows["capex discipline"].interpretation_guard
    assert "capacity release" not in text


def test_semiconductor_contradictory_signals_are_partial_low_and_list_both_signals():
    pack, _ = build_semiconductor_outputs(operating_cashflow=-1000000.0)
    row = {item.driver_factor: item for item in pack.driver_matrix}[
        "contract liabilities / operating cash flow signal consistency"
    ]

    assert row.data_availability_status == "partial"
    assert row.confidence_cap == "low"
    assert any("financial_metrics.contract_liabilities=" in item for item in row.available_evidence)
    assert any("financial_metrics.operating_cashflow=" in item for item in row.available_evidence)
    assert "manual review" in row.interpretation_guard
    assert "manual review" in row.research_question


def test_semiconductor_company_transmission_path_minimum_standard_applies():
    builder = ResearchIntelligenceP1Builder()
    financial_only_pack = {
        "stock": {"code": "002371", "name": "Financial Only", "strategy_type": "semiconductor_cycle"},
        "financial_metrics": {"revenue": 100, "gross_margin": 20},
    }
    business_only_pack = {
        "stock": {"code": "002371", "name": "Business Only", "strategy_type": "semiconductor_cycle"},
        "business_composition": [{"segment_name": "electronic process equipment", "revenue_ratio": 0.93}],
    }

    financial_pack, _ = builder.build(financial_only_pack)
    financial_row = {item.driver_factor: item for item in financial_pack.driver_matrix}[
        "semiconductor-related revenue contribution"
    ]
    assert financial_row.company_transmission_path == TRANSMISSION_PATH_FALLBACK
    assert financial_row.confidence_cap == "not_assessable"

    business_pack, _ = builder.build(business_only_pack)
    business_row = {item.driver_factor: item for item in business_pack.driver_matrix}[
        "semiconductor-related revenue contribution"
    ]
    assert business_row.company_transmission_path != TRANSMISSION_PATH_FALLBACK
    assert business_row.confidence_cap == "low"
    assert "financial_metrics" not in business_row.company_transmission_path


def test_semiconductor_source_bucket_counting_uses_existing_bucket_rules():
    pack, _ = build_semiconductor_outputs()

    assert pack.source_bucket_summary.consensus_assessment_status == "not_assessable"
    assert pack.source_bucket_summary.source_buckets == ["company_disclosure", "financial_statement"]
    assert pack.source_bucket_summary.independent_source_count == 2


def test_semiconductor_non_primary_samples_remain_unsupported():
    for code in ["688012", "688981", "603501", "300604", "300308", "300476", "688008"]:
        pack, _ = build_semiconductor_outputs(code=code)

        assert len(pack.driver_matrix) == 1
        row = pack.driver_matrix[0]
        assert row.driver_factor == "unsupported_pilot_strategy"
        assert row.company_transmission_path == TRANSMISSION_PATH_FALLBACK
        assert row.confidence_cap == "not_assessable"
        assert "002371 only" in row.not_assessable_reason


def test_semiconductor_outputs_do_not_include_forbidden_safety_terms():
    pack, questions = build_semiconductor_outputs()
    text = json.dumps({"pack": pack.model_dump(), "questions": questions.model_dump()}, ensure_ascii=False)

    assert pack.safety_boundary.safe
    assert questions.safety_boundary.safe
    assert not any(term in text for term in FORBIDDEN_TERMS)
    assert "technical_skill" not in text
    assert "trader_skill" not in text


def test_advanced_manufacturing_driver_matrix_contains_required_factors():
    pack, questions = build_advanced_manufacturing_outputs()
    names = driver_names(pack)

    assert pack.strategy_type == "advanced_manufacturing_growth"
    assert pack.stock_code == "002050"
    assert {
        "high-end manufacturing demand cycle",
        "automotive / EV / thermal-management demand",
        "robotics / humanoid robotics theme exposure",
        "customer capex / product adoption cycle",
        "localization / import substitution",
        "overseas customer / export exposure",
        "core business revenue contribution",
        "automotive thermal-management business contribution",
        "new business / robotics / emerging business revenue split",
        "product line revenue and gross margin",
        "customer order visibility",
        "mass production / delivery evidence",
        "customer concentration / top customer exposure",
        "customer qualification / nomination / design-win status",
        "contract liabilities as partial proxy only",
        "product mix upgrade",
        "revenue growth quality",
        "gross margin stability",
        "operating cash flow",
        "accounts receivable / collection quality",
        "inventory and production-sales bridge",
        "capex-to-revenue / capacity utilization bridge",
        "R&D expense as input evidence only",
        "free cash flow / working-capital pressure",
        "valuation explainability as evidence sufficiency only",
        "new business narrative without revenue",
        "robotics theme without order / customer / mass-production evidence",
        "customer concentration risk",
        "receivables / collection deterioration",
        "inventory build without demand bridge",
        "capex without utilization / revenue bridge",
        "gross margin pressure from product mix or price competition",
        "overseas customer / FX / trade risk",
        "product qualification or mass-production delay",
    }.issubset(names)
    assert questions.questions


def test_advanced_manufacturing_three_business_layers_are_isolated():
    pack, _ = build_advanced_manufacturing_outputs()
    rows = {item.driver_factor: item for item in pack.driver_matrix}

    core = rows["core business revenue contribution"]
    auto = rows["automotive thermal-management business contribution"]
    robotics = rows["new business / robotics / emerging business revenue split"]

    assert core.company_transmission_path != TRANSMISSION_PATH_FALLBACK
    assert "制冷空调电器零部件" in core.company_transmission_path
    assert "汽车零部件" not in core.company_transmission_path.split(" -> ")[0]

    assert auto.company_transmission_path != TRANSMISSION_PATH_FALLBACK
    assert "汽车零部件" in auto.company_transmission_path
    assert "制冷空调电器零部件" not in auto.company_transmission_path.split(" -> ")[0]

    assert robotics.company_transmission_path == TRANSMISSION_PATH_FALLBACK
    assert robotics.confidence_cap == "not_assessable"
    assert "制冷空调" not in robotics.company_transmission_path
    assert "汽车零部件" not in robotics.company_transmission_path


def test_advanced_manufacturing_robotics_without_independent_revenue_forces_fallback():
    pack, _ = build_advanced_manufacturing_outputs(include_robotics_layout_segment=True)
    rows = {item.driver_factor: item for item in pack.driver_matrix}

    for name in [
        "robotics / humanoid robotics theme exposure",
        "new business / robotics / emerging business revenue split",
        "new business narrative without revenue",
        "robotics theme without order / customer / mass-production evidence",
    ]:
        row = rows[name]
        assert row.company_transmission_path == TRANSMISSION_PATH_FALLBACK
        assert row.data_availability_status == "not_assessable"
        assert row.confidence_cap == "not_assessable"
        assert "机器人关键零部件布局" not in row.source_refs


def test_advanced_manufacturing_layout_and_news_are_not_valid_transmission_nodes():
    pack, _ = build_advanced_manufacturing_outputs(include_robotics_layout_segment=True)
    text = json.dumps(pack.model_dump(), ensure_ascii=False)

    for row in pack.driver_matrix:
        assert "latest_news" not in row.company_transmission_path
        assert "news" not in row.company_transmission_path.lower()
        if "robotics" in row.driver_factor or "new business" in row.driver_factor:
            assert row.company_transmission_path == TRANSMISSION_PATH_FALLBACK
    assert "unverified context only" not in text


def test_advanced_manufacturing_customer_capex_design_win_and_mass_production_guards():
    pack, _ = build_advanced_manufacturing_outputs()
    rows = {item.driver_factor: item for item in pack.driver_matrix}

    customer_capex = rows["customer capex / product adoption cycle"]
    design_win = rows["customer qualification / nomination / design-win status"]
    mass_production = rows["mass production / delivery evidence"]

    assert customer_capex.company_transmission_path == TRANSMISSION_PATH_FALLBACK
    assert "Customer capex is not company revenue" in customer_capex.interpretation_guard
    assert design_win.company_transmission_path == TRANSMISSION_PATH_FALLBACK
    assert "is not batch revenue" in design_win.interpretation_guard
    assert mass_production.company_transmission_path == TRANSMISSION_PATH_FALLBACK
    assert "distinct from qualification" in mass_production.research_question


def test_advanced_manufacturing_contract_liabilities_capex_rd_receivable_inventory_guards():
    pack, _ = build_advanced_manufacturing_outputs()
    rows = {item.driver_factor: item for item in pack.driver_matrix}
    text = json.dumps(pack.model_dump(), ensure_ascii=False).lower()

    contract_row = rows["contract liabilities as partial proxy only"]
    capex_row = rows["capex-to-revenue / capacity utilization bridge"]
    rd_row = rows["R&D expense as input evidence only"]
    receivable_row = rows["accounts receivable / collection quality"]
    inventory_row = rows["inventory and production-sales bridge"]

    assert contract_row.company_transmission_path != TRANSMISSION_PATH_FALLBACK
    assert "partial proxy only" in contract_row.interpretation_guard
    assert "not backlog" in contract_row.interpretation_guard
    assert "financial_metrics.contract_liabilities=" in contract_row.company_transmission_path

    assert "cash outflow / investment observation" in capex_row.interpretation_guard
    assert "not capacity release" in capex_row.interpretation_guard
    assert "input evidence only" in rd_row.interpretation_guard
    assert "moat" not in rd_row.interpretation_guard.lower()
    assert "not be written as high-quality revenue" in receivable_row.interpretation_guard
    assert "must not be used to judge robotics" in inventory_row.interpretation_guard
    assert "strong demand" not in text


def test_advanced_manufacturing_valuation_explainability_fixed_wording_and_forbidden_phrases():
    pack, questions = build_advanced_manufacturing_outputs()
    row = {item.driver_factor: item for item in pack.driver_matrix}["valuation explainability as evidence sufficiency only"]
    text = json.dumps({"pack": pack.model_dump(), "questions": questions.model_dump()}, ensure_ascii=False)

    assert row.research_question == "当前 evidence pack 中哪些证据足以支撑或解释当前估值背景，哪些证据仍缺失？"
    assert "evidence sufficiency context only" in row.interpretation_guard
    forbidden = FORBIDDEN_TERMS + ["估值合理", "估值偏高", "估值偏低", "上涨空间", "下跌空间", "目标价", "买入", "卖出", "持有"]
    assert not any(term in text for term in forbidden)


def test_advanced_manufacturing_contradictory_signals_are_partial_low_and_listed():
    pack, _ = build_advanced_manufacturing_outputs(operating_cashflow=-1000000.0)
    row = {item.driver_factor: item for item in pack.driver_matrix}[
        "revenue growth / cash-flow / receivable signal consistency"
    ]

    assert row.data_availability_status == "partial"
    assert row.confidence_cap == "low"
    assert any("financial_metrics.revenue_yoy=" in item for item in row.available_evidence)
    assert any("financial_metrics.operating_cashflow=" in item for item in row.available_evidence)
    assert any("financial_metrics.accounts_receivable=" in item for item in row.available_evidence)
    assert "manual review" in row.interpretation_guard


def test_advanced_manufacturing_source_bucket_counting_and_boundaries():
    pack, _ = build_advanced_manufacturing_outputs()

    assert pack.source_bucket_summary.consensus_assessment_status == "not_assessable"
    assert pack.source_bucket_summary.source_buckets == ["company_disclosure", "financial_statement", "news_media"]
    assert pack.source_bucket_summary.independent_source_count == 3

    unsupported, _ = build_advanced_manufacturing_outputs(code="601689")
    assert len(unsupported.driver_matrix) == 1
    assert unsupported.driver_matrix[0].driver_factor == "unsupported_pilot_strategy"
    assert unsupported.driver_matrix[0].confidence_cap == "not_assessable"
    assert "002050 only" in unsupported.driver_matrix[0].not_assessable_reason

    non_pilot, _ = build_advanced_manufacturing_outputs(strategy_type="right_trend_growth")
    assert len(non_pilot.driver_matrix) == 1
    assert non_pilot.driver_matrix[0].driver_factor == "unsupported_pilot_strategy"


def test_advanced_manufacturing_generated_questions_avoid_obvious_robotics_duplication_and_safety_terms():
    pack, questions = build_advanced_manufacturing_outputs()
    text = json.dumps({"pack": pack.model_dump(), "questions": questions.model_dump()}, ensure_ascii=False)
    robotics_questions = [
        item.question
        for item in questions.questions
        if "robotics" in item.driver_factor or "new business" in item.driver_factor
    ]

    assert len(robotics_questions) == len(set(robotics_questions))
    assert any("non-zero revenue" in question for question in robotics_questions)
    assert any("direct robotics order" in question for question in robotics_questions)
    assert pack.safety_boundary.safe
    assert questions.safety_boundary.safe
    assert not any(term in text for term in FORBIDDEN_TERMS)
    assert "technical_skill" not in text
    assert "trader_skill" not in text
