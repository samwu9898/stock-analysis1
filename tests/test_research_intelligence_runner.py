# -*- coding: utf-8 -*-

import json

from src.fundamental_skill.ai_analyst.evidence_pack import EvidencePackBuilder
from src.fundamental_skill.ai_analyst.research_intelligence_runner import main, run_research_intelligence

from tests.ai_test_fixtures import sample_fundamental, sample_raw


def test_research_intelligence_runner_writes_json_and_markdown(tmp_path):
    pack = EvidencePackBuilder().build(sample_fundamental("ai_datacenter_infrastructure"), sample_raw())
    evidence_path = tmp_path / "evidence_pack_002837.json"
    evidence_path.write_text(json.dumps(pack, ensure_ascii=False), encoding="utf-8")

    result = run_research_intelligence("002837", evidence_pack_path=evidence_path, output_dir=tmp_path)

    assert (tmp_path / "research_intelligence_002837.json").exists()
    assert (tmp_path / "research_questions_002837.json").exists()
    assert (tmp_path / "research_questions_002837.md").exists()
    assert result["stock_code"] == "002837"
    assert not (tmp_path / "reports").exists()


def test_research_intelligence_runner_cli(tmp_path, monkeypatch, capsys):
    pack = EvidencePackBuilder().build(sample_fundamental("advanced_manufacturing_growth"), sample_raw())
    evidence_path = tmp_path / "evidence_pack_002050.json"
    evidence_path.write_text(json.dumps(pack, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        [
            "research_intelligence_runner",
            "--code",
            "002050",
            "--evidence-pack-path",
            str(evidence_path),
            "--output-dir",
            str(tmp_path),
        ],
    )

    code = main()
    captured = capsys.readouterr()

    assert code == 0
    assert "research_intelligence:" in captured.out
    assert "research_questions_md:" in captured.out
