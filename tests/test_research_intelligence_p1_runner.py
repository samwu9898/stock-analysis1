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
