# -*- coding: utf-8 -*-

from __future__ import annotations

import json
from types import SimpleNamespace

from scripts import generate_fundamental_html_report as wrapper


def test_prepare_runs_required_prompt_only_stages_and_writes_next_task(tmp_path, monkeypatch):
    calls: list[tuple[str, str]] = []

    def fake_run_real_stock(code, output=None, force_refresh=False):
        calls.append(("real_stock", code))
        output_path = tmp_path / "fundamental_002837.json"
        raw_path = tmp_path / "raw_002837.json"
        output_path.write_text("{}", encoding="utf-8")
        raw_path.write_text("{}", encoding="utf-8")
        return {}, SimpleNamespace(stock_name="英维克")

    def fake_ai_prompt_only(code, output_dir=None):
        calls.append(("ai_prompt_only", code))
        evidence_path = tmp_path / "evidence_pack_002837.json"
        prompt_path = tmp_path / "ai_prompt_002837.md"
        evidence_path.write_text("{}", encoding="utf-8")
        prompt_path.write_text("ai prompt", encoding="utf-8")
        return {
            "stock_code": code,
            "evidence_pack_path": str(evidence_path),
            "prompt_path": str(prompt_path),
        }

    def fake_html_prompt_only(code, output_dir=None):
        calls.append(("html_prompt_only", code))
        prompt_path = tmp_path / "reports" / "fundamental_report_prompt_002837.md"
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text("fundamental_html_report.v1", encoding="utf-8")
        return {"stock_code": code, "prompt_path": str(prompt_path)}

    monkeypatch.setattr(wrapper, "run_real_stock", fake_run_real_stock)
    monkeypatch.setattr(wrapper.ai_analyst_runner, "run_prompt_only", fake_ai_prompt_only)
    monkeypatch.setattr(wrapper.html_report_runner, "run_prompt_only", fake_html_prompt_only)

    result = wrapper.run_prepare("002837", output_dir=tmp_path)
    task_path = tmp_path / "reports" / "fundamental_report_next_task_002837.md"

    assert calls == [
        ("real_stock", "002837"),
        ("ai_prompt_only", "002837"),
        ("html_prompt_only", "002837"),
    ]
    assert result["stock_code"] == "002837"
    assert result["stock_name"] == "英维克"
    assert result["next_task_path"] == str(task_path)
    assert task_path.exists()
    task_text = task_path.read_text(encoding="utf-8")
    assert "fundamental_html_report.v1" in task_text
    assert "不要 skeleton" in task_text
    assert "不得输出交易建议、目标价、仓位、技术面、K线" in task_text
    assert "output/reports" in task_text or "reports" in task_text


def test_build_next_task_instructions_mentions_render_and_safety_boundaries(tmp_path):
    instructions = wrapper.build_next_task_instructions(
        code="sz002837",
        ai_prompt_path=tmp_path / "ai_prompt_002837.md",
        html_prompt_path=tmp_path / "reports" / "fundamental_report_prompt_002837.md",
        formal_json_path=tmp_path / "reports" / "fundamental_report_002837.json",
        formal_html_path=tmp_path / "reports" / "fundamental_report_002837.html",
        output_dir=tmp_path,
    )

    assert "002837" in instructions
    assert "fundamental_html_report.v1" in instructions
    assert "--mode render_existing --visual-audit" in instructions
    assert "不得编造订单、客户、份额、排名、产能释放" in instructions
    assert "不得输出交易建议、目标价、仓位、技术面、K线" in instructions
    assert "不要 skeleton" in instructions


def test_render_existing_delegates_to_html_report_runner(tmp_path, monkeypatch):
    calls = []

    def fake_render_existing(code, output_dir=None):
        calls.append((code, output_dir))
        return {"stock_code": code, "html_path": str(tmp_path / "reports" / f"fundamental_report_{code}.html")}

    monkeypatch.setattr(wrapper.html_report_runner, "run_render_existing", fake_render_existing)

    result = wrapper.run_render_existing("002837", output_dir=tmp_path)

    assert result["stock_code"] == "002837"
    assert calls == [("002837", tmp_path)]


def test_visual_audit_uses_formal_html_path_and_audit_output_dir(tmp_path, monkeypatch):
    captured = {}

    def fake_visual_main(argv):
        captured["argv"] = argv
        return 0

    import scripts.visual_audit_html_report as visual_audit_html_report

    monkeypatch.setattr(visual_audit_html_report, "main", fake_visual_main)

    exit_code = wrapper.run_visual_audit("002837", output_dir=tmp_path)

    assert exit_code == 0
    assert captured["argv"][0:2] == ["--html", str(tmp_path / "reports" / "fundamental_report_002837.html")]
    assert "--output-dir" in captured["argv"]
    assert str(tmp_path / "visual_audit" / "002837") in captured["argv"]
    assert "--notes" in captured["argv"]


def test_cli_prepare_prints_next_task_without_api_or_skeleton(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        wrapper,
        "run_prepare",
        lambda code, output_dir=None, force_refresh=False: {
            "stock_code": "002837",
            "stock_name": "英维克",
            "fundamental_path": str(tmp_path / "fundamental_002837.json"),
            "raw_path": str(tmp_path / "raw_002837.json"),
            "evidence_pack_path": str(tmp_path / "evidence_pack_002837.json"),
            "ai_prompt_path": str(tmp_path / "ai_prompt_002837.md"),
            "html_prompt_path": str(tmp_path / "reports" / "fundamental_report_prompt_002837.md"),
            "formal_json_path": str(tmp_path / "reports" / "fundamental_report_002837.json"),
            "formal_html_path": str(tmp_path / "reports" / "fundamental_report_002837.html"),
            "next_task_path": str(tmp_path / "reports" / "fundamental_report_next_task_002837.md"),
            "next_task": "只输出 JSON；不要 skeleton；不调用 OpenAI API；不得输出交易建议、目标价、仓位、技术面、K线。",
        },
    )

    code = wrapper.main(["--code", "002837", "--output-dir", str(tmp_path)])
    captured = capsys.readouterr()

    assert code == 0
    assert "next_task:" in captured.out
    assert "不要 skeleton" in captured.out
    assert "不调用 OpenAI API" in captured.out
    assert "不得输出交易建议、目标价、仓位、技术面、K线" in captured.out
    assert "skeleton output" not in captured.out


def test_gitignore_keeps_output_artifacts_out_of_git():
    gitignore = (wrapper.PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "output/" in gitignore


def test_wrapper_does_not_create_skeleton_files_in_prepare_result(tmp_path, monkeypatch):
    monkeypatch.setattr(
        wrapper,
        "run_real_stock",
        lambda code, output=None, force_refresh=False: ({}, SimpleNamespace(stock_name="英维克")),
    )
    monkeypatch.setattr(
        wrapper.ai_analyst_runner,
        "run_prompt_only",
        lambda code, output_dir=None: {
            "stock_code": code,
            "evidence_pack_path": str(tmp_path / f"evidence_pack_{code}.json"),
            "prompt_path": str(tmp_path / f"ai_prompt_{code}.md"),
        },
    )
    monkeypatch.setattr(
        wrapper.html_report_runner,
        "run_prompt_only",
        lambda code, output_dir=None: {
            "stock_code": code,
            "prompt_path": str(tmp_path / "reports" / f"fundamental_report_prompt_{code}.md"),
        },
    )

    result = wrapper.run_prepare("002837", output_dir=tmp_path)

    serialized = json.dumps(result, ensure_ascii=False)
    assert "skeleton/fundamental_report_002837_skeleton" not in serialized
    assert result["formal_json_path"].endswith("reports\\fundamental_report_002837.json") or result[
        "formal_json_path"
    ].endswith("reports/fundamental_report_002837.json")
