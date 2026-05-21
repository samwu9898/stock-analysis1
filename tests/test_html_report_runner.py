# -*- coding: utf-8 -*-

import json

from src.fundamental_skill.ai_analyst.html_report_runner import (
    main,
    run_prompt_only,
    run_render_existing,
    run_skeleton,
)
from tests.ai_test_fixtures import sample_fundamental, sample_raw


def test_html_runner_prompt_only_outputs_prompt_file(tmp_path):
    fundamental = sample_fundamental("advanced_manufacturing_growth")
    fundamental["stock_code"] = "002050"
    raw = sample_raw()
    raw["meta"]["code"] = "002050"
    (tmp_path / "fundamental_002050.json").write_text(json.dumps(fundamental, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "raw_002050.json").write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")

    result = run_prompt_only("002050", output_dir=tmp_path)

    prompt_path = tmp_path / "reports" / "fundamental_report_prompt_002050.md"
    assert result["prompt_path"] == str(prompt_path)
    assert prompt_path.exists()
    assert "fundamental_html_report.v1" in prompt_path.read_text(encoding="utf-8")


def test_html_runner_render_existing_generates_html(tmp_path):
    result = run_skeleton("002050", output_dir=tmp_path)
    render_result = run_render_existing("002050", output_dir=tmp_path)

    assert result["skeleton_warning"] is True
    assert (tmp_path / "reports" / "fundamental_report_002050.json").exists()
    assert (tmp_path / "reports" / "fundamental_report_002050.html").exists()
    assert render_result["html_path"].endswith("fundamental_report_002050.html")


def test_html_runner_missing_file_returns_clear_error(capsys, monkeypatch, tmp_path):
    monkeypatch.setattr(
        "sys.argv",
        ["html_report_runner", "--code", "002050", "--mode", "render_existing", "--output-dir", str(tmp_path)],
    )

    code = main()
    captured = capsys.readouterr()

    assert code == 1
    assert "Required input file not found" in captured.out


def test_html_runner_skeleton_has_warning(tmp_path):
    result = run_skeleton("002050", output_dir=tmp_path)
    payload = json.loads((tmp_path / "reports" / "fundamental_report_002050.json").read_text(encoding="utf-8"))
    html = (tmp_path / "reports" / "fundamental_report_002050.html").read_text(encoding="utf-8")

    assert result["skeleton_warning"] is True
    assert payload["report_meta"]["status"] == "skeleton"
    assert payload["report_meta"]["confidence"] == "skeleton"
    assert payload["report_meta"]["fundamental_score"] is None
    assert "Skeleton" in payload["core_conclusion"]["title"]
    assert "不是正式 AI 分析报告" in payload["core_conclusion"]["title"]
    assert "不是正式 AI 分析报告" in html
    assert "没有形成正式研究结论" in html


def test_html_runner_skeleton_does_not_inherit_formal_meta_from_evidence_pack(tmp_path):
    evidence_pack = {
        "stock": {
            "code": "002050",
            "name": "三花智控",
            "strategy_type": "advanced_manufacturing_growth",
            "status": "neutral",
            "confidence": "high",
            "fundamental_score": 68,
        }
    }
    (tmp_path / "evidence_pack_002050.json").write_text(json.dumps(evidence_pack, ensure_ascii=False), encoding="utf-8")

    run_skeleton("002050", output_dir=tmp_path)
    payload = json.loads((tmp_path / "reports" / "fundamental_report_002050.json").read_text(encoding="utf-8"))

    assert payload["report_meta"]["status"] == "skeleton"
    assert payload["report_meta"]["confidence"] == "skeleton"
    assert payload["report_meta"]["fundamental_score"] is None
