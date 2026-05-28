# -*- coding: utf-8 -*-

import copy
import inspect
import json
from pathlib import Path

import pytest

from src.fundamental_skill.research_report.orchestration import (
    CANDIDATE_REVIEW_DECISIONS_FILENAME,
    FACT_CANDIDATES_FILENAME,
    ReportRequestError,
    extract_chinese_summary_from_markdown,
    format_orchestration_response,
    locate_research_report_artifacts,
    normalize_report_request,
    run_single_stock_report_orchestration,
)
import src.fundamental_skill.research_report.orchestration as orchestration_module
from src.fundamental_skill.research_report.accepted_manifest import (
    build_accepted_manifest,
    compute_file_sha256,
    write_accepted_manifest,
)
from src.fundamental_skill.research_report.research_report_v1 import OUTPUT_FILENAME as JSON_OUTPUT_FILENAME
from src.fundamental_skill.research_report.research_report_v1_html import HTML_OUTPUT_FILENAME
from src.fundamental_skill.research_report.research_report_v1_presentation import (
    MARKDOWN_OUTPUT_FILENAME,
    render_research_report_v1_markdown,
)
from tests.test_auto_fact_candidate_generator import _provider_payload
from tests.test_research_report_v1_presentation import _fake_report


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _artifact_relative_path(timestamp: str, code: str, filename: str) -> str:
    return f"output/research_reports/{timestamp}/{code}/{filename}"


def _write_manifest_artifact_bundle(
    repo_root: Path,
    *,
    code: str = "600406",
    html_timestamp: str = "20260528T010000",
    markdown_timestamp: str | None = None,
    json_timestamp: str | None = None,
    freshness_status: str = "current",
    freshness_reason: str = "accepted baseline",
    supersedes: list[dict] | None = None,
) -> tuple[Path, dict]:
    markdown_timestamp = markdown_timestamp or html_timestamp
    json_timestamp = json_timestamp or html_timestamp
    html_rel = _artifact_relative_path(html_timestamp, code, HTML_OUTPUT_FILENAME)
    markdown_rel = _artifact_relative_path(markdown_timestamp, code, MARKDOWN_OUTPUT_FILENAME)
    json_rel = _artifact_relative_path(json_timestamp, code, JSON_OUTPUT_FILENAME)

    html_path = repo_root / Path(html_rel)
    markdown_path = repo_root / Path(markdown_rel)
    json_path = repo_root / Path(json_rel)
    _write_text(html_path, "<!doctype html><html><body>accepted manifest report</body></html>")
    _write_text(
        markdown_path,
        "# Accepted report\n\n## Local summary\nAccepted manifest baseline with no trading advice.\n",
    )
    _write_json(json_path, _report(code=code))

    entry = {
        "code": code,
        "company_name": "Manifest Sample",
        "report_type": "fundamental_research_report_v1",
        "presentation_profile": "stable_growth",
        "accepted_artifacts": {
            "html": html_rel,
            "markdown": markdown_rel,
            "json": json_rel,
        },
        "artifact_hashes": {
            "html_sha256": compute_file_sha256(html_path),
            "markdown_sha256": compute_file_sha256(markdown_path),
            "json_sha256": compute_file_sha256(json_path),
        },
        "acceptance": {
            "accepted_at": "2026-05-28T12:55:18+08:00",
            "accepted_stage": "cli_runtime_acceptance",
            "accepted_by": "human_or_codex_review",
            "acceptance_notes": [],
        },
        "freshness": {
            "freshness_status": freshness_status,
            "source_data_period": "2025Q4",
            "financial_report_period": "2025-12-31",
            "valuation_as_of_date": "2026-05-28",
            "report_generated_at": "2026-05-28T12:55:18+08:00",
            "accepted_at": "2026-05-28T12:55:18+08:00",
            "valid_until": "2026-06-30",
            "last_freshness_check_at": "2026-05-28T12:55:18+08:00",
            "freshness_reason": freshness_reason,
            "staleness_triggers": [],
            "manual_override": None,
        },
        "lineage": {
            "supersedes": supersedes or [],
            "superseded_by": None,
            "source_artifacts": [],
        },
        "safety": {
            "not_for_trading_advice": True,
            "no_token": True,
            "no_provider_call": True,
        },
    }
    output_root = repo_root / "output" / "research_reports"
    manifest = build_accepted_manifest(
        [entry],
        created_at="2026-05-28T12:55:18+08:00",
        updated_at="2026-05-28T12:55:18+08:00",
    )
    write_accepted_manifest(manifest, output_root / "accepted_manifest.json")
    return output_root, entry


def _report(code: str = "600406", strategy_type: str = "stable_growth") -> dict:
    return copy.deepcopy(_fake_report(code, strategy_type))


def _provider_comparison_dir(root: Path) -> Path:
    code_dir = root / "20260527T000000" / "600406"
    for provider in ("tushare", "akshare"):
        _write_json(code_dir / f"{provider}_fundamental.json", _provider_payload(provider))
        _write_json(
            code_dir / f"{provider}_evidence_pack.json",
            {
                "stock": {"code": "600406", "name": "NARI", "strategy_type": "stable_growth"},
                "financial_metrics": {"period": "2025-12-31", "revenue": 100_000_000.0},
                "valuation_metrics": {
                    "period": "2026-05-26",
                    "pe_ttm": 20.0,
                    "pb": 3.0,
                    "market_cap": 1_000_000_000.0,
                },
                "business_composition": [
                    {
                        "period": "2025-12-31",
                        "classification_type": "by_product",
                        "segment_name": "Grid automation",
                        "revenue": 60_000_000.0,
                        "revenue_ratio": 60.0,
                        "gross_margin": 25.0,
                    }
                ],
            },
        )
    _write_json(code_dir / "diff_report.json", {"code": "600406", "summary": {"review_required_count": 1}})
    _write_json(
        code_dir / "score_confidence_explainability.json",
        {
            "code": "600406",
            "providers": {
                "akshare": {"artifact_refs": {"fundamental": "akshare_fundamental.json", "evidence_pack": "akshare_evidence_pack.json"}},
                "tushare": {"artifact_refs": {"fundamental": "tushare_fundamental.json", "evidence_pack": "tushare_evidence_pack.json"}},
            },
            "score_summary": {"score_delta": 0},
            "confidence_summary": {"confidence_delta": "none"},
        },
    )
    return code_dir


def _assert_under(path: Path | None, root: Path) -> None:
    if path is None:
        return
    path.resolve(strict=False).relative_to(root.resolve(strict=False))


def _assert_no_positive_action_terms(response: str) -> None:
    forbidden = (
        "买入",
        "卖出",
        "持有建议",
        "加仓",
        "减仓",
        "止损",
        "确定性上涨",
        "必然兑现",
        "强烈推荐",
        "buy",
        "sell",
        "target price",
        "position sizing",
        "stop loss",
        "technical trading signal",
        "strong recommend",
    )
    for term in forbidden:
        assert term not in response.lower()

    for term in ("目标价", "仓位", "技术面交易信号"):
        matching_lines = [line for line in response.splitlines() if term in line]
        assert matching_lines == ["重要声明：本报告仅用于基本面研究，不构成买卖建议，不包含目标价、仓位或技术面交易信号。"]


def test_normalize_request_from_code_and_company_text():
    request = normalize_report_request("帮我生成 600406 国电南瑞的基本面投研报告")

    assert request["code"] == "600406"
    assert request["company_name"] == "国电南瑞"
    assert request["stock_pool"] is None
    assert request["report_type"] == "fundamental_research_report_v1"
    assert request["output_format"] == "html"


def test_normalize_request_from_known_company_name():
    request = normalize_report_request("分析一下北方华创的基本面")

    assert request["code"] == "002371"
    assert request["company_name"] == "北方华创"


def test_context_modifier_without_target_fails_closed():
    with pytest.raises(ReportRequestError, match="缺少目标标的"):
        normalize_report_request("只用本地 artifacts，不要调用实时接口")


def test_default_request_flags_are_safe():
    request = normalize_report_request(code="002050")

    assert request["data_mode"] == "offline_local_artifacts"
    assert request["provider_mode"] == "no_live_provider"
    assert request["provider_transport"] == "none"
    assert request["allow_network"] is False
    assert request["allow_token_read"] is False
    assert request["reasoning_level"] == "high"
    assert request["not_for_trading_advice"] is True
    assert request["strict_evidence_boundary"] is True


def test_module_has_no_network_token_provider_runtime_or_mcp_access():
    source = inspect.getsource(orchestration_module)

    assert "TUSHARE_TOKEN" not in source
    assert "os.environ" not in source
    assert "requests" not in source
    assert "socket" not in source
    assert "data_providers" not in source
    assert "tushare_provider" not in source
    assert "akshare_provider" not in source
    assert "provider_router" not in source
    assert "list_mcp" not in source
    assert "mcp__" not in source


def test_locator_reuses_existing_html(tmp_path):
    output_root = tmp_path / "research_reports"
    html_path = output_root / "20260528T010000" / "600406" / HTML_OUTPUT_FILENAME
    _write_text(html_path, "<!doctype html><html><body>local accepted report</body></html>")

    located = locate_research_report_artifacts("600406", output_root)

    assert located["html_path"] == html_path.resolve(strict=False)
    assert located["missing_artifacts"] == []


def test_manifest_current_happy_path_uses_manifest_not_timestamp_latest(tmp_path):
    output_root, _ = _write_manifest_artifact_bundle(tmp_path, html_timestamp="20260528T010000")
    latest_html = output_root / "20260528T020000" / "600406" / HTML_OUTPUT_FILENAME
    _write_text(latest_html, "<!doctype html><html><body>experimental latest</body></html>")

    located = locate_research_report_artifacts("600406", output_root)

    assert located["html_path"] == (tmp_path / "output" / "research_reports" / "20260528T010000" / "600406" / HTML_OUTPUT_FILENAME).resolve(strict=False)
    assert located["manifest_used"] is True
    assert located["manifest_status"] == "used"
    assert located["freshness_status"] == "current"
    assert located["freshness_warning"] is None
    assert "manifest_latest_conflict_warning" in located["manifest_warning"]


def test_manifest_mixed_timestamp_bundle_for_002371_is_valid_and_located(tmp_path):
    output_root, _ = _write_manifest_artifact_bundle(
        tmp_path,
        code="002371",
        html_timestamp="20260528T125518",
        markdown_timestamp="20260528T125518",
        json_timestamp="20260527T220148",
    )

    located = locate_research_report_artifacts("002371", output_root)

    assert located["manifest_used"] is True
    assert "20260528T125518" in str(located["html_path"])
    assert "20260528T125518" in str(located["markdown_path"])
    assert "20260527T220148" in str(located["json_path"])


def test_manifest_prevents_superseded_old_artifact_selection(tmp_path):
    old_markdown_rel = _artifact_relative_path("20260527T220148", "002371", MARKDOWN_OUTPUT_FILENAME)
    old_html_rel = _artifact_relative_path("20260528T090024", "002371", HTML_OUTPUT_FILENAME)
    _write_text(tmp_path / Path(old_markdown_rel), "# old markdown")
    _write_text(tmp_path / Path(old_html_rel), "<!doctype html><html><body>old html</body></html>")
    supersedes = [
        {
            "artifact_type": "markdown",
            "path": old_markdown_rel,
            "sha256": compute_file_sha256(tmp_path / Path(old_markdown_rel)),
            "superseded_reason": "professional_voice_regeneration",
            "superseded_at": "2026-05-28T12:55:18+08:00",
            "replacement_path": _artifact_relative_path("20260528T125518", "002371", MARKDOWN_OUTPUT_FILENAME),
        },
        {
            "artifact_type": "html",
            "path": old_html_rel,
            "sha256": compute_file_sha256(tmp_path / Path(old_html_rel)),
            "superseded_reason": "professional_voice_regeneration",
            "superseded_at": "2026-05-28T12:55:18+08:00",
            "replacement_path": _artifact_relative_path("20260528T125518", "002371", HTML_OUTPUT_FILENAME),
        },
    ]
    output_root, _ = _write_manifest_artifact_bundle(
        tmp_path,
        code="002371",
        html_timestamp="20260528T125518",
        markdown_timestamp="20260528T125518",
        json_timestamp="20260527T220148",
        supersedes=supersedes,
    )

    located = locate_research_report_artifacts("002371", output_root)

    assert located["manifest_used"] is True
    assert "20260528T125518" in str(located["html_path"])
    assert "20260528T090024" not in str(located["html_path"])
    assert "20260527T220148" in str(located["json_path"])


def test_missing_manifest_falls_back_with_warning(tmp_path):
    output_root = tmp_path / "research_reports"
    html_path = output_root / "20260528T010000" / "600406" / HTML_OUTPUT_FILENAME
    _write_text(html_path, "<!doctype html><html><body>local accepted report</body></html>")

    located = locate_research_report_artifacts("600406", output_root)

    assert located["html_path"] == html_path.resolve(strict=False)
    assert located["manifest_used"] is False
    assert located["manifest_status"] == "missing"
    assert "manifest_missing_warning" in located["manifest_warning"]


def test_manifest_entry_missing_falls_back_with_warning(tmp_path):
    output_root, _ = _write_manifest_artifact_bundle(tmp_path, code="002371")
    fallback_html = output_root / "20260528T020000" / "600406" / HTML_OUTPUT_FILENAME
    _write_text(fallback_html, "<!doctype html><html><body>fallback report</body></html>")

    located = locate_research_report_artifacts("600406", output_root)

    assert located["html_path"] == fallback_html.resolve(strict=False)
    assert located["manifest_used"] is False
    assert located["manifest_status"] == "entry_missing"
    assert "manifest_entry_missing_warning" in located["manifest_warning"]


@pytest.mark.parametrize("freshness_status", ["unknown", "stale"])
def test_manifest_unknown_and_stale_are_usable_with_warning(tmp_path, freshness_status):
    output_root, _ = _write_manifest_artifact_bundle(
        tmp_path,
        freshness_status=freshness_status,
        freshness_reason=f"{freshness_status} freshness for test",
    )

    result = run_single_stock_report_orchestration(
        normalize_report_request(code="600406"),
        output_root=output_root,
        timestamp="20260528T020000",
    )
    response = format_orchestration_response(result)

    assert result["status"] == "reused"
    assert result["manifest_used"] is True
    assert result["freshness_status"] == freshness_status
    assert result["freshness_warning"]
    assert freshness_status in result["freshness_warning"]
    assert freshness_status in response
    assert "Freshness 提示：" in response


@pytest.mark.parametrize("freshness_status", ["superseded", "invalidated"])
def test_manifest_superseded_or_invalidated_fail_closed(tmp_path, freshness_status):
    output_root, _ = _write_manifest_artifact_bundle(
        tmp_path,
        freshness_status=freshness_status,
        freshness_reason=f"{freshness_status} entry cannot be accepted baseline",
    )

    result = run_single_stock_report_orchestration(
        normalize_report_request(code="600406"),
        output_root=output_root,
        timestamp="20260528T020000",
    )

    assert result["status"] == "failed_invalid_manifest"
    assert result["manifest_used"] is False
    assert result["manifest_status"] == freshness_status
    assert result["freshness_status"] == freshness_status
    assert result["html_path"] is None


def test_manifest_missing_referenced_file_fails_closed(tmp_path):
    output_root, entry = _write_manifest_artifact_bundle(tmp_path)
    missing_path = tmp_path / Path(entry["accepted_artifacts"]["markdown"])
    missing_path.unlink()

    result = run_single_stock_report_orchestration(
        normalize_report_request(code="600406"),
        output_root=output_root,
        timestamp="20260528T020000",
    )

    assert result["status"] == "failed_invalid_manifest"
    assert result["manifest_status"] == "invalid"
    assert result["manifest_used"] is False
    assert "<masked>" not in result["manifest_warning"]


def test_manifest_hash_mismatch_fails_closed_without_secret_leak(tmp_path):
    output_root, entry = _write_manifest_artifact_bundle(tmp_path)
    html_path = tmp_path / Path(entry["accepted_artifacts"]["html"])
    _write_text(html_path, "<!doctype html><html><body>changed</body></html>")

    result = run_single_stock_report_orchestration(
        normalize_report_request(code="600406"),
        output_root=output_root,
        timestamp="20260528T020000",
    )

    assert result["status"] == "failed_invalid_manifest"
    assert result["manifest_status"] == "invalid"
    assert result["manifest_used"] is False
    assert "changed" not in result["manifest_warning"]


def test_markdown_exists_but_html_missing_generates_html(tmp_path):
    output_root = tmp_path / "research_reports"
    markdown = render_research_report_v1_markdown(_report())
    markdown_path = output_root / "20260528T010000" / "600406" / MARKDOWN_OUTPUT_FILENAME
    _write_text(markdown_path, markdown)
    before = markdown_path.read_bytes()

    result = run_single_stock_report_orchestration(
        normalize_report_request(code="600406"),
        output_root=output_root,
        timestamp="20260528T020000",
    )

    assert result["status"] == "generated"
    assert result["html_path"].is_file()
    assert result["markdown_path"] == markdown_path.resolve(strict=False)
    assert "generated_html_from_markdown" in result["actions_taken"]
    assert markdown_path.read_bytes() == before


def test_json_exists_but_markdown_missing_generates_markdown_and_html(tmp_path):
    output_root = tmp_path / "research_reports"
    json_path = output_root / "20260528T010000" / "600406" / JSON_OUTPUT_FILENAME
    _write_json(json_path, _report())
    before = json_path.read_bytes()

    result = run_single_stock_report_orchestration(
        normalize_report_request(code="600406"),
        output_root=output_root,
        timestamp="20260528T020000",
    )

    assert result["status"] == "generated"
    assert result["json_path"] == json_path.resolve(strict=False)
    assert result["markdown_path"].is_file()
    assert result["html_path"].is_file()
    assert "generated_markdown_from_json" in result["actions_taken"]
    assert "generated_html_from_markdown" in result["actions_taken"]
    assert json_path.read_bytes() == before


def test_provider_comparison_exists_but_downstream_missing_invokes_offline_rebuild_chain(tmp_path):
    output_root = tmp_path / "research_reports"
    provider_root = tmp_path / "provider_comparison"
    _provider_comparison_dir(provider_root)

    result = run_single_stock_report_orchestration(
        normalize_report_request(code="600406"),
        output_root=output_root,
        provider_comparison_root=provider_root,
        timestamp="20260528T030000",
    )

    assert result["status"] == "generated"
    assert result["fact_candidates_path"].name == FACT_CANDIDATES_FILENAME
    assert result["candidate_review_decisions_path"].name == CANDIDATE_REVIEW_DECISIONS_FILENAME
    assert result["json_path"].name == JSON_OUTPUT_FILENAME
    assert result["markdown_path"].name == MARKDOWN_OUTPUT_FILENAME
    assert result["html_path"].name == HTML_OUTPUT_FILENAME
    assert all(result[path_key].is_file() for path_key in ("fact_candidates_path", "candidate_review_decisions_path", "json_path", "markdown_path", "html_path"))
    assert "generated_fact_candidates" in result["actions_taken"]
    assert "generated_candidate_review_decisions" in result["actions_taken"]
    assert "generated_research_report_json" in result["actions_taken"]


def test_provider_comparison_missing_returns_missing_artifact_checklist(tmp_path):
    result = run_single_stock_report_orchestration(
        normalize_report_request(code="600406"),
        output_root=tmp_path / "research_reports",
        provider_comparison_root=tmp_path / "provider_comparison",
        timestamp="20260528T040000",
    )

    assert result["status"] == "failed_missing_artifacts"
    assert result["html_path"] is None
    assert "local provider comparison artifact root for 600406" in result["missing_artifacts"]
    assert JSON_OUTPUT_FILENAME in result["missing_artifacts"]


def test_final_response_includes_paths_and_summary(tmp_path):
    output_root = tmp_path / "research_reports"
    json_path = output_root / "20260528T010000" / "600406" / JSON_OUTPUT_FILENAME
    _write_json(json_path, _report())
    result = run_single_stock_report_orchestration(
        normalize_report_request(code="600406"),
        output_root=output_root,
        timestamp="20260528T020000",
    )

    response = format_orchestration_response(result)

    assert "报告状态：" in response
    assert str(result["html_path"]) in response
    assert str(result["markdown_path"]) in response
    assert str(result["json_path"]) in response
    assert "简短摘要：" in response
    assert "最大机会：" in response
    assert "最大风险：" in response
    assert "最大证据缺口：" in response
    assert "数据质量状态：" in response


def test_reused_html_with_markdown_prefers_chinese_one_sentence_over_english_json(tmp_path):
    output_root = tmp_path / "research_reports"
    code_dir = output_root / "20260528T010000" / "600406"
    html_path = code_dir / HTML_OUTPUT_FILENAME
    markdown_path = code_dir / MARKDOWN_OUTPUT_FILENAME
    json_path = code_dir / JSON_OUTPUT_FILENAME
    markdown = """# 600406 国电南瑞 基本面研究报告 V1

## 一句话结论
国电南瑞应优先作为电网设备和数字电网链路的本地研究样本跟踪。
最大机会来自电网投资、调度系统和继电保护需求的公司层面验证。
最大风险在于订单兑现、项目结算和回款节奏。
最大证据缺口是主营构成口径和官方主营业务来源。

## 研究员判断
这一段不应进入聊天摘要。
"""
    _write_text(html_path, "<!doctype html><html><body>local accepted report</body></html>")
    _write_text(markdown_path, markdown)
    _write_json(json_path, _report())
    before_markdown = markdown_path.read_bytes()
    before_json = json_path.read_bytes()

    result = run_single_stock_report_orchestration(
        normalize_report_request(code="600406"),
        output_root=output_root,
        timestamp="20260528T020000",
    )
    response = format_orchestration_response(result)

    assert result["status"] == "reused"
    assert result["summary"].startswith("国电南瑞应优先作为电网设备")
    assert "600406 currently reads as" not in result["summary"]
    assert "600406 currently reads as" not in response
    assert "Grid investment can support" not in response
    assert "Accounts receivable" not in response
    assert "main_business needs" not in response
    assert "国电南瑞应优先作为电网设备" in response
    assert "最大机会：最大机会来自电网投资" in response
    assert "最大风险：最大风险在于订单兑现" in response
    assert "最大证据缺口：最大证据缺口是主营构成口径" in response
    assert "这一段不应进入聊天摘要" not in response
    assert markdown_path.read_bytes() == before_markdown
    assert json_path.read_bytes() == before_json


def test_markdown_one_sentence_extraction_stops_before_next_heading():
    markdown = """# 样本

## 一句话结论
第一行中文结论。
第二行中文补充。

## 投研速读
- 不应跨 heading 出现。
"""

    summary = extract_chinese_summary_from_markdown(markdown)

    assert summary == "第一行中文结论。 第二行中文补充。"
    assert "不应跨 heading 出现" not in summary


def test_markdown_quick_read_fallback_extracts_first_two_bullets():
    markdown = """# 样本

## 投研速读
- 第一条中文速读。
- 第二条中文速读。
- 第三条不应进入摘要。

## 研究员判断
不应进入摘要。
"""

    summary = extract_chinese_summary_from_markdown(markdown)

    assert summary == "第一条中文速读。 第二条中文速读。"
    assert "第三条" not in summary
    assert "研究员判断" not in summary


def test_markdown_missing_does_not_present_english_json_summary_as_chinese(tmp_path):
    output_root = tmp_path / "research_reports"
    code_dir = output_root / "20260528T010000" / "600406"
    html_path = code_dir / HTML_OUTPUT_FILENAME
    json_path = code_dir / JSON_OUTPUT_FILENAME
    _write_text(html_path, "<!doctype html><html><body>local accepted report</body></html>")
    _write_json(json_path, _report())

    result = run_single_stock_report_orchestration(
        normalize_report_request(code="600406"),
        output_root=output_root,
        timestamp="20260528T020000",
    )
    response = format_orchestration_response(result)

    assert result["status"] == "reused"
    assert result["markdown_path"] is None
    assert result["summary"] == "当前仅找到结构化摘要字段，建议打开 Markdown 报告查看中文摘要。"
    assert "600406 currently reads as" not in response
    assert "Grid investment can support" not in response
    assert "当前仅找到结构化摘要字段，建议打开 Markdown 报告查看中文摘要。" in response
    assert "建议打开 Markdown 报告查看中文机会说明" in response


def test_final_response_does_not_copy_whole_markdown_report(tmp_path):
    output_root = tmp_path / "research_reports"
    code_dir = output_root / "20260528T010000" / "600406"
    markdown_path = code_dir / MARKDOWN_OUTPUT_FILENAME
    json_path = code_dir / JSON_OUTPUT_FILENAME
    html_path = code_dir / HTML_OUTPUT_FILENAME
    markdown = """# 600406 国电南瑞 基本面研究报告 V1

## 一句话结论
第一行中文摘要。
第二行中文摘要。
第三行中文摘要。
第四行中文摘要。
第五行不应进入聊天响应。

## 深度正文
这是一段很长的正文，不应被复制到最终聊天响应。
"""
    _write_text(html_path, "<!doctype html><html><body>local accepted report</body></html>")
    _write_text(markdown_path, markdown)
    _write_json(json_path, _report())

    result = run_single_stock_report_orchestration(
        normalize_report_request(code="600406"),
        output_root=output_root,
        timestamp="20260528T020000",
    )
    response = format_orchestration_response(result)

    assert "第一行中文摘要" in response
    assert "第四行中文摘要" in response
    assert "第五行不应进入聊天响应" not in response
    assert "这是一段很长的正文" not in response
    assert len(result["summary"]) < 500


def test_final_response_allows_only_negative_disclaimer_for_trading_terms(tmp_path):
    output_root = tmp_path / "research_reports"
    code_dir = output_root / "20260528T010000" / "600406"
    _write_text(code_dir / HTML_OUTPUT_FILENAME, "<!doctype html><html><body>local accepted report</body></html>")
    _write_text(
        code_dir / MARKDOWN_OUTPUT_FILENAME,
        "# 600406 国电南瑞 基本面研究报告 V1\n\n## 一句话结论\n国电南瑞适合作为电网设备基本面研究样本继续跟踪。\n",
    )
    _write_json(code_dir / JSON_OUTPUT_FILENAME, _report())

    result = run_single_stock_report_orchestration(
        normalize_report_request(code="600406"),
        output_root=output_root,
        timestamp="20260528T020000",
    )
    response = format_orchestration_response(result)

    _assert_no_positive_action_terms(response)


def test_final_response_includes_not_for_trading_advice_statement():
    response = format_orchestration_response(
        {
            "status": "failed_missing_artifacts",
            "summary": "缺少本地 artifact。",
            "largest_opportunity": "未提供",
            "largest_risk": "未提供",
            "largest_evidence_gap": "未提供",
            "data_quality_status": "缺少结构化字段",
            "missing_artifacts": [],
        }
    )

    assert "仅用于基本面研究" in response
    assert "不构成买卖建议" in response
    assert "不包含目标价、仓位或技术面交易信号" in response


def test_final_response_has_no_positive_trading_advice_terms(tmp_path):
    output_root = tmp_path / "research_reports"
    json_path = output_root / "20260528T010000" / "600406" / JSON_OUTPUT_FILENAME
    _write_json(json_path, _report())
    result = run_single_stock_report_orchestration(
        normalize_report_request(code="600406"),
        output_root=output_root,
        timestamp="20260528T020000",
    )
    response = format_orchestration_response(result)

    for term in ("买入", "卖出", "加仓", "减仓", "清仓", "止损", "止盈", "K线"):
        assert term not in response


def test_legacy_runner_paths_are_not_used():
    source = inspect.getsource(orchestration_module)

    for legacy in (
        "src/data_fetcher.py",
        "src/html_renderer.py",
        "real_stock_runner",
        "ai_analyst/runner.py",
        "html_report_runner",
        "generate_fundamental_html_report",
    ):
        assert legacy not in source


def test_existing_input_artifacts_are_not_mutated(tmp_path):
    output_root = tmp_path / "research_reports"
    json_path = output_root / "20260528T010000" / "600406" / JSON_OUTPUT_FILENAME
    _write_json(json_path, _report())
    before = json_path.read_bytes()

    run_single_stock_report_orchestration(
        normalize_report_request(code="600406"),
        output_root=output_root,
        timestamp="20260528T020000",
    )

    assert json_path.read_bytes() == before


def test_writer_artifacts_stay_under_tmpdir(tmp_path):
    output_root = tmp_path / "research_reports"
    provider_root = tmp_path / "provider_comparison"
    _provider_comparison_dir(provider_root)

    result = run_single_stock_report_orchestration(
        normalize_report_request(code="600406"),
        output_root=output_root,
        provider_comparison_root=provider_root,
        timestamp="20260528T030000",
    )

    for key in ("html_path", "markdown_path", "json_path", "fact_candidates_path", "candidate_review_decisions_path"):
        _assert_under(result[key], tmp_path)
