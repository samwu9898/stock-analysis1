# -*- coding: utf-8 -*-

import json

from src.fundamental_skill.ai_analyst.evidence_pack import EvidencePackBuilder
from src.fundamental_skill.ai_analyst.research_intelligence_p1_runner import main, run_research_intelligence_p1

from tests.ai_test_fixtures import sample_fundamental, sample_raw


def _pack(sub_type="cooling_liquid_cooling_infrastructure"):
    fundamental = sample_fundamental("ai_datacenter_infrastructure")
    fundamental["stock_code"] = "002837"
    fundamental["stock_name"] = "英维克"
    fundamental["sub_type"] = sub_type
    return EvidencePackBuilder().build(fundamental, sample_raw())


def _cxo_pack(sub_type="integrated_cxo_platform"):
    fundamental = sample_fundamental("life_science_cxo_services")
    fundamental["stock_code"] = "603259"
    fundamental["stock_name"] = "CXO Sample"
    fundamental["sub_type"] = sub_type
    raw = sample_raw()
    raw["blocks"]["financial_indicator"][0].update(
        {
            "revenue": 40300000000,
            "gross_margin": 39.5,
            "operating_cashflow": 9200000000,
            "accounts_receivable": 7100000000,
            "contract_liabilities": 2300000000,
            "capex": 4200000000,
        }
    )
    raw["blocks"]["business_composition"] = [
        {"period": "2025-12-31", "segment_name": "integrated CXO services", "revenue_ratio": 0.86, "gross_margin": 0.43},
        {"period": "2025-12-31", "segment_name": "overseas", "revenue_ratio": 0.83},
    ]
    return EvidencePackBuilder().build(fundamental, raw)


def _satellite_pack():
    fundamental = sample_fundamental("satellite_communication_infrastructure")
    fundamental["stock_code"] = "601698"
    fundamental["stock_name"] = "China Satcom"
    fundamental["sub_type"] = None
    raw = sample_raw()
    raw["meta"] = {"code": "601698", "stock_name": "China Satcom"}
    raw["blocks"]["basic_info"] = [
        {
            "stock_code": "601698",
            "stock_name": "China Satcom",
            "industry": "telecom, broadcast television and satellite transmission services",
            "main_business": "satellite space-segment operation and related application services",
        }
    ]
    raw["blocks"]["financial_indicator"][0].update(
        {
            "revenue": 542414493.94,
            "gross_margin": 19.04,
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
            "revenue_ratio": 1.0,
            "gross_margin": 0.294502,
        }
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


def _low_altitude_pack():
    fundamental = sample_fundamental("low_altitude_economy_infrastructure")
    fundamental["stock_code"] = "000099"
    fundamental["stock_name"] = "CITIC Offshore Helicopter"
    fundamental["sub_type"] = "aviation_operations_service"
    raw = sample_raw()
    raw["meta"] = {"code": "000099", "stock_name": "CITIC Offshore Helicopter"}
    raw["blocks"]["basic_info"] = [
        {
            "stock_code": "000099",
            "stock_name": "CITIC Offshore Helicopter",
            "industry": "general aviation operation services",
            "main_business": "general aviation operation and low-altitude flight services",
        }
    ]
    raw["blocks"]["financial_indicator"][0].update(
        {
            "revenue": 502587618.96,
            "gross_margin": 21.236629,
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
            "revenue_ratio": 0.991324,
            "gross_margin": 0.237805,
        }
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


def _resource_pack():
    fundamental = sample_fundamental("resource_swing")
    fundamental["stock_code"] = "000426"
    fundamental["stock_name"] = "Xingye Silver & Tin"
    fundamental["sub_type"] = None
    raw = sample_raw()
    raw["meta"] = {"code": "000426", "stock_name": "Xingye Silver & Tin"}
    raw["blocks"]["basic_info"] = [
        {
            "stock_code": "000426",
            "stock_name": "Xingye Silver & Tin",
            "industry": "non-ferrous metal mining and processing",
            "main_business": "silver, tin, lead-zinc ore mining and processing",
        }
    ]
    raw["blocks"]["financial_indicator"][0].update(
        {
            "revenue": 1775000000.0,
            "revenue_yoy": 28.0,
            "gross_margin": 52.5,
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
            "revenue_ratio": 0.50,
            "gross_margin": 0.61,
        }
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


def _semiconductor_pack():
    return {
        "stock": {"code": "002371", "name": "NAURA", "strategy_type": "semiconductor_cycle"},
        "basic_info": {
            "stock_code": "002371",
            "stock_name": "NAURA",
            "industry": "specialized equipment manufacturing",
            "main_business": "semiconductor equipment and integrated-circuit manufacturing equipment",
        },
        "financial_metrics": {
            "period": "20260331",
            "revenue": 10322863908.82,
            "revenue_yoy": {"raw_value": 25.79609, "display_value": "25.80%"},
            "gross_margin": {"raw_value": 40.772789, "display_value": "40.77%"},
            "operating_cashflow": 748055666.52,
            "accounts_receivable": 8780279745.35,
            "inventory": 28602898183.2,
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
            }
        ],
        "enhanced_must_track_indicators": [
            {"indicator_name": "localization revenue", "current_status": "missing", "current_value": None},
            {"indicator_name": "order / contract liabilities", "current_status": "partial_proxy", "current_value": 4202521948.54},
        ],
        "source_trace_summary": [
            {"block_name": "business_composition", "trace_count": 1},
            {"block_name": "financial_indicator", "trace_count": 16},
        ],
    }


def _advanced_manufacturing_pack():
    return {
        "stock": {"code": "002050", "name": "三花智控", "strategy_type": "advanced_manufacturing_growth"},
        "basic_info": {
            "stock_code": "002050",
            "stock_name": "三花智控",
            "industry": "通用设备制造业",
            "main_business": "制冷空调控制元器件、汽车热管理零部件，并积极布局机器人执行器相关零部件。",
        },
        "financial_metrics": {
            "period": "20260331",
            "revenue": 7773555419.29,
            "revenue_yoy": {"raw_value": 1.357397, "display_value": "1.36%"},
            "gross_margin": {"raw_value": 27.796688, "display_value": "27.80%"},
            "operating_cashflow": 1105790187.12,
            "accounts_receivable": 7010919404.89,
            "contract_liabilities": 80754056.98,
            "inventory": 5879322018.99,
            "capex": 521898492.14,
            "r_and_d_expense": 367461670.95,
            "r_and_d_expense_ratio": {"raw_value": 4.727073406309647, "display_value": "4.73%"},
        },
        "valuation_metrics": {"pe_ttm": 40.1, "pb": 6.2},
        "business_composition": [
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
        ],
        "enhanced_must_track_indicators": [
            {"indicator_name": "新业务收入或订单", "current_status": "missing", "current_value": None},
            {"indicator_name": "合同负债", "current_status": "partial_proxy", "current_value": 80754056.98},
        ],
        "source_trace_summary": [
            {"block_name": "business_composition", "trace_count": 1},
            {"block_name": "financial_indicator", "trace_count": 16},
        ],
    }


def test_research_intelligence_p1_runner_writes_independent_json_and_markdown(tmp_path):
    evidence_path = tmp_path / "evidence_pack_002837.json"
    evidence_path.write_text(json.dumps(_pack(), ensure_ascii=False), encoding="utf-8")

    result = run_research_intelligence_p1("002837", evidence_pack_path=evidence_path, output_dir=tmp_path)

    assert (tmp_path / "research_intelligence_p1_002837.json").exists()
    assert (tmp_path / "research_questions_p1_002837.json").exists()
    assert (tmp_path / "research_questions_p1_002837.md").exists()
    assert result["stock_code"] == "002837"
    assert not (tmp_path / "reports").exists()


def test_research_intelligence_p1_runner_cli(tmp_path, monkeypatch, capsys):
    evidence_path = tmp_path / "evidence_pack_300442.json"
    evidence_path.write_text(json.dumps(_pack("datacenter_operator"), ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        [
            "research_intelligence_p1_runner",
            "--code",
            "300442",
            "--evidence-pack-path",
            str(evidence_path),
            "--output-dir",
            str(tmp_path),
        ],
    )

    code = main()
    captured = capsys.readouterr()

    assert code == 0
    assert "research_intelligence_p1:" in captured.out
    assert "research_questions_p1_md:" in captured.out
    assert not (tmp_path / "reports").exists()


def test_research_intelligence_p1_runner_writes_cxo_expansion_artifacts(tmp_path):
    evidence_path = tmp_path / "evidence_pack_603259.json"
    evidence_path.write_text(json.dumps(_cxo_pack(), ensure_ascii=False), encoding="utf-8")

    result = run_research_intelligence_p1("603259", evidence_pack_path=evidence_path, output_dir=tmp_path)
    matrix = result["research_intelligence_p1"]["driver_matrix"]

    assert (tmp_path / "research_intelligence_p1_603259.json").exists()
    assert (tmp_path / "research_questions_p1_603259.json").exists()
    assert (tmp_path / "research_questions_p1_603259.md").exists()
    assert result["research_intelligence_p1"]["strategy_type"] == "life_science_cxo_services"
    assert any(item["driver_factor"] == "CXO revenue contribution" for item in matrix)
    assert not (tmp_path / "reports").exists()


def test_research_intelligence_p1_runner_writes_satellite_expansion_artifacts(tmp_path):
    evidence_path = tmp_path / "evidence_pack_601698.json"
    evidence_path.write_text(json.dumps(_satellite_pack(), ensure_ascii=False), encoding="utf-8")

    result = run_research_intelligence_p1("601698", evidence_pack_path=evidence_path, output_dir=tmp_path)
    matrix = result["research_intelligence_p1"]["driver_matrix"]

    assert (tmp_path / "research_intelligence_p1_601698.json").exists()
    assert (tmp_path / "research_questions_p1_601698.json").exists()
    assert (tmp_path / "research_questions_p1_601698.md").exists()
    assert result["research_intelligence_p1"]["strategy_type"] == "satellite_communication_infrastructure"
    assert any(item["driver_factor"] == "capacity utilization" for item in matrix)
    assert any(item["driver_factor"] == "satellite remaining life / replacement capex" for item in matrix)
    assert not (tmp_path / "reports").exists()


def test_research_intelligence_p1_runner_writes_low_altitude_expansion_artifacts(tmp_path):
    evidence_path = tmp_path / "evidence_pack_000099.json"
    evidence_path.write_text(json.dumps(_low_altitude_pack(), ensure_ascii=False), encoding="utf-8")

    result = run_research_intelligence_p1("000099", evidence_pack_path=evidence_path, output_dir=tmp_path)
    matrix = result["research_intelligence_p1"]["driver_matrix"]

    assert (tmp_path / "research_intelligence_p1_000099.json").exists()
    assert (tmp_path / "research_questions_p1_000099.json").exists()
    assert (tmp_path / "research_questions_p1_000099.md").exists()
    assert result["research_intelligence_p1"]["strategy_type"] == "low_altitude_economy_infrastructure"
    assert result["research_intelligence_p1"]["sub_type"] == "aviation_operations_service"
    assert any(item["driver_factor"] == "flight hours" for item in matrix)
    assert any(item["driver_factor"] == "capex-to-service-capacity bridge" for item in matrix)
    assert not (tmp_path / "reports").exists()


def test_research_intelligence_p1_runner_writes_resource_swing_expansion_artifacts(tmp_path):
    evidence_path = tmp_path / "evidence_pack_000426.json"
    evidence_path.write_text(json.dumps(_resource_pack(), ensure_ascii=False), encoding="utf-8")

    result = run_research_intelligence_p1("000426", evidence_pack_path=evidence_path, output_dir=tmp_path)
    matrix = result["research_intelligence_p1"]["driver_matrix"]

    assert (tmp_path / "research_intelligence_p1_000426.json").exists()
    assert (tmp_path / "research_questions_p1_000426.json").exists()
    assert (tmp_path / "research_questions_p1_000426.md").exists()
    assert result["research_intelligence_p1"]["strategy_type"] == "resource_swing"
    assert any(item["driver_factor"] == "core commodity price exposure" for item in matrix)
    assert any(item["driver_factor"] == "revenue sensitivity to commodity price" for item in matrix)
    assert not any(item["driver_factor"] == "dividend capacity for resource_core" for item in matrix)
    assert not (tmp_path / "reports").exists()


def test_research_intelligence_p1_runner_writes_semiconductor_expansion_artifacts(tmp_path):
    evidence_path = tmp_path / "evidence_pack_002371.json"
    evidence_path.write_text(json.dumps(_semiconductor_pack(), ensure_ascii=False), encoding="utf-8")

    result = run_research_intelligence_p1("002371", evidence_pack_path=evidence_path, output_dir=tmp_path)
    matrix = result["research_intelligence_p1"]["driver_matrix"]

    assert (tmp_path / "research_intelligence_p1_002371.json").exists()
    assert (tmp_path / "research_questions_p1_002371.json").exists()
    assert (tmp_path / "research_questions_p1_002371.md").exists()
    assert result["research_intelligence_p1"]["strategy_type"] == "semiconductor_cycle"
    assert any(item["driver_factor"] == "semiconductor capex cycle" for item in matrix)
    assert any(item["driver_factor"] == "equipment sub-chain classification" for item in matrix)
    assert not (tmp_path / "reports").exists()


def test_research_intelligence_p1_runner_writes_advanced_manufacturing_expansion_artifacts(tmp_path):
    evidence_path = tmp_path / "evidence_pack_002050.json"
    evidence_path.write_text(json.dumps(_advanced_manufacturing_pack(), ensure_ascii=False), encoding="utf-8")

    result = run_research_intelligence_p1("002050", evidence_pack_path=evidence_path, output_dir=tmp_path)
    matrix = result["research_intelligence_p1"]["driver_matrix"]

    assert (tmp_path / "research_intelligence_p1_002050.json").exists()
    assert (tmp_path / "research_questions_p1_002050.json").exists()
    assert (tmp_path / "research_questions_p1_002050.md").exists()
    assert result["research_intelligence_p1"]["strategy_type"] == "advanced_manufacturing_growth"
    assert any(item["driver_factor"] == "core business revenue contribution" for item in matrix)
    assert any(item["driver_factor"] == "valuation explainability as evidence sufficiency only" for item in matrix)
    assert not (tmp_path / "reports").exists()


def test_research_intelligence_p1_runner_writes_stable_growth_expansion_artifacts(tmp_path):
    evidence_pack = {
        "stock": {"code": "600406", "name": "NARI Technology", "strategy_type": "stable_growth", "status": "neutral", "confidence": "high"},
        "basic_info": {
            "stock_code": "600406",
            "stock_name": "NARI Technology",
            "industry": "power grid equipment and software",
            "main_business": "power automation and grid intelligence",
        },
        "financial_metrics": {
            "period": "20260331",
            "revenue": 12300000000.0,
            "revenue_yoy": {"raw_value": 8.5, "display_value": "8.50%"},
            "gross_margin": {"raw_value": 25.7, "display_value": "25.70%"},
            "net_margin": {"raw_value": 12.1, "display_value": "12.10%"},
            "net_profit": 721291973.43,
            "deducted_net_profit": 641986345.23,
            "operating_cashflow": 2100000000.0,
            "accounts_receivable": 26652280492.48,
            "inventory": 16590949099.58,
            "contract_liabilities": 8634661875.03,
            "capex": 451693205.88,
            "roe": {"raw_value": 1.36, "display_value": "1.36%"},
            "debt_to_asset": {"raw_value": 40.194985, "display_value": "40.19%"},
        },
        "valuation_metrics": {"pe_ttm": 24.0, "pb": 3.1, "ps": 2.7, "market_cap": 210000000000},
        "business_composition": [
            {
                "period": "2025-12-31",
                "classification_type": "by product",
                "segment_name": "grid intelligence",
                "revenue": 33422155368.42,
                "revenue_ratio": {"raw_value": 0.504646, "display_value": "50.46%"},
                "gross_margin": {"raw_value": 0.301197, "display_value": "30.12%"},
            }
        ],
        "source_trace_summary": [
            {"block_name": "business_composition", "trace_count": 1},
            {"block_name": "financial_indicator", "trace_count": 16},
            {"block_name": "valuation", "trace_count": 4},
        ],
    }
    evidence_path = tmp_path / "evidence_pack_600406.json"
    evidence_path.write_text(json.dumps(evidence_pack, ensure_ascii=False), encoding="utf-8")

    result = run_research_intelligence_p1("600406", evidence_pack_path=evidence_path, output_dir=tmp_path)
    matrix = result["research_intelligence_p1"]["driver_matrix"]

    assert (tmp_path / "research_intelligence_p1_600406.json").exists()
    assert (tmp_path / "research_questions_p1_600406.json").exists()
    assert (tmp_path / "research_questions_p1_600406.md").exists()
    assert result["research_intelligence_p1"]["strategy_type"] == "stable_growth"
    assert any(item["driver_factor"] == "recurring revenue or repeat-order quality" for item in matrix)
    assert any(item["driver_factor"] == "valuation explainability as evidence sufficiency only" for item in matrix)
    assert not (tmp_path / "reports").exists()
