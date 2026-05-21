# -*- coding: utf-8 -*-

import json
import pytest

from src.fundamental_skill.ai_analyst.html_report_runner import (
    main,
    run_prompt_only,
    run_render_existing,
    run_skeleton,
)
from tests.ai_test_fixtures import sample_fundamental, sample_raw


def _skeleton_json_path(tmp_path, code="002050"):
    return tmp_path / "reports" / "skeleton" / f"fundamental_report_{code}_skeleton.json"


def _skeleton_html_path(tmp_path, code="002050"):
    return tmp_path / "reports" / "skeleton" / f"fundamental_report_{code}_skeleton.html"


def _formal_json_path(tmp_path, code="002050"):
    return tmp_path / "reports" / f"fundamental_report_{code}.json"


def _formal_html_path(tmp_path, code="002050"):
    return tmp_path / "reports" / f"fundamental_report_{code}.html"


def _formal_payload_from_skeleton(tmp_path):
    run_skeleton("002050", output_dir=tmp_path)
    payload = json.loads(_skeleton_json_path(tmp_path).read_text(encoding="utf-8"))
    payload["report_meta"]["status"] = "neutral"
    payload["report_meta"]["confidence"] = "high"
    payload["report_meta"]["fundamental_score"] = 68
    payload["report_meta"]["data_quality_status"] = "正式报告测试样例"
    payload["hero_tags"] = ["高端制造成长", "汽车热管理", "现金流需复核"]
    payload["core_conclusion"].update(
        {
            "title": "核心结论",
            "summary": "本样例用于验证正式 report JSON 可以渲染到正式 HTML 路径。",
        }
    )
    return payload


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
    assert not (tmp_path / "evidence_pack_002050.json").exists()
    assert not _formal_json_path(tmp_path).exists()
    assert not _formal_html_path(tmp_path).exists()


def test_html_runner_render_existing_generates_html(tmp_path):
    payload = _formal_payload_from_skeleton(tmp_path)
    payload["hero_tags"] = ["高端制造成长", "现金流需复核"]
    payload["research_anchor"] = {
        "main_thesis": "制冷空调零部件基本盘与汽车热管理成长验证。",
        "key_conflict": "成长证据与新业务缺口并存。",
        "current_stage": "验证期",
        "what_is_proven": ["主业构成可见"],
        "what_is_unproven": ["新业务订单待验证"],
    }
    payload["value_chain_map"] = {
        "upstream": "待验证",
        "company_role": "热管理零部件制造商",
        "downstream": "待验证",
        "profit_source": "毛利率与收入规模",
        "unproven_moats": ["客户结构待验证"],
        "key_bottlenecks": ["订单证据缺失"],
    }
    payload["elasticity_formula"] = {
        "formula_title": "利润弹性",
        "formula_text": "利润弹性 = 收入增长 × 毛利率稳定性 × 费用率控制",
        "key_variables": ["收入", "毛利率", "费用率"],
        "interpretation": "只用于基本面传导解释。",
        "data_limitations": ["新业务收入缺失"],
    }
    payload["tracking_plan_groups"] = [
        {"group_name": "财报跟踪", "items": [{"indicator": "毛利率", "frequency": "季度", "why_it_matters": "验证利润质量", "trigger_for_review": "波动时复核"}]},
        {"group_name": "公告/订单跟踪", "items": []},
        {"group_name": "行业/政策跟踪", "items": []},
        {"group_name": "风险复核", "items": []},
    ]
    json_path = _formal_json_path(tmp_path)
    json_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    render_result = run_render_existing("002050", output_dir=tmp_path)

    assert json_path.exists()
    assert _formal_html_path(tmp_path).exists()
    assert render_result["html_path"].endswith("fundamental_report_002050.html")
    assert "研究主线 / 核心矛盾" in _formal_html_path(tmp_path).read_text(encoding="utf-8")


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
    payload = json.loads(_skeleton_json_path(tmp_path).read_text(encoding="utf-8"))
    html = _skeleton_html_path(tmp_path).read_text(encoding="utf-8")

    assert result["skeleton_warning"] is True
    assert result["json_path"] == str(_skeleton_json_path(tmp_path))
    assert result["html_path"] == str(_skeleton_html_path(tmp_path))
    assert payload["report_meta"]["status"] == "skeleton"
    assert payload["report_meta"]["confidence"] == "skeleton"
    assert payload["report_meta"]["fundamental_score"] is None
    assert "Skeleton" in payload["core_conclusion"]["title"]
    assert "不是正式 AI 分析报告" in payload["core_conclusion"]["title"]
    assert "不是正式 AI 分析报告" in html
    assert "没有形成正式研究结论" in html
    assert not _formal_json_path(tmp_path).exists()
    assert not _formal_html_path(tmp_path).exists()


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
    payload = json.loads(_skeleton_json_path(tmp_path).read_text(encoding="utf-8"))

    assert payload["report_meta"]["status"] == "skeleton"
    assert payload["report_meta"]["confidence"] == "skeleton"
    assert payload["report_meta"]["fundamental_score"] is None


def test_html_runner_skeleton_mode_does_not_overwrite_formal_report_path(tmp_path):
    formal_json = _formal_json_path(tmp_path)
    formal_html = _formal_html_path(tmp_path)
    formal_json.parent.mkdir(parents=True, exist_ok=True)
    formal_json.write_text('{"formal": true}', encoding="utf-8")
    formal_html.write_text("<html>formal</html>", encoding="utf-8")

    run_skeleton("002050", output_dir=tmp_path)

    assert formal_json.read_text(encoding="utf-8") == '{"formal": true}'
    assert formal_html.read_text(encoding="utf-8") == "<html>formal</html>"
    assert _skeleton_json_path(tmp_path).exists()
    assert _skeleton_html_path(tmp_path).exists()


def test_html_runner_render_existing_rejects_skeleton_json_for_formal_html(tmp_path):
    run_skeleton("002050", output_dir=tmp_path)
    skeleton_payload = _skeleton_json_path(tmp_path).read_text(encoding="utf-8")
    _formal_json_path(tmp_path).write_text(skeleton_payload, encoding="utf-8")

    with pytest.raises(ValueError, match="skeleton report cannot be rendered as formal report"):
        run_render_existing("002050", output_dir=tmp_path)

    assert not _formal_html_path(tmp_path).exists()
