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
