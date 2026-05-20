# -*- coding: utf-8 -*-

import json

from src.fundamental_skill.ai_analyst.runner import main, run_prompt_only

from tests.ai_test_fixtures import sample_fundamental, sample_raw


def test_runner_prompt_only_without_api_key(tmp_path):
    (tmp_path / "fundamental_002050.json").write_text(
        json.dumps(sample_fundamental("advanced_manufacturing_growth"), ensure_ascii=False),
        encoding="utf-8",
    )
    raw = sample_raw()
    raw["meta"]["code"] = "002050"
    (tmp_path / "raw_002050.json").write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")

    result = run_prompt_only("002050", output_dir=tmp_path)

    assert (tmp_path / "evidence_pack_002050.json").exists()
    assert (tmp_path / "ai_prompt_002050.md").exists()
    assert result["stock_code"] == "002050"


def test_runner_api_mode_is_not_implemented(capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["runner", "--code", "002050", "--mode", "api"])

    code = main()
    captured = capsys.readouterr()

    assert code == 0
    assert "API mode not implemented in v1; use prompt_only" in captured.out
