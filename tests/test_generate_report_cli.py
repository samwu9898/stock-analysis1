# -*- coding: utf-8 -*-

from __future__ import annotations

import hashlib
import inspect
import json
import subprocess
from io import StringIO
from pathlib import Path

import pytest

import src.fundamental_skill.research_report.generate_report as generate_report_cli
from src.fundamental_skill.research_report.accepted_manifest import (
    build_accepted_manifest,
    compute_file_sha256,
    write_accepted_manifest,
)


_REPO_ROOT = Path(__file__).resolve().parents[1]
_REAL_MANIFEST_PATH = _REPO_ROOT / "output" / "research_reports" / "accepted_manifest.json"

_POSITIVE_TRADING_TERMS = (
    "买入",
    "卖出",
    "持有建议",
    "目标价",
    "仓位",
    "加仓",
    "减仓",
    "止损",
    "技术面交易信号",
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

_ENGLISH_JSON_SUMMARY_SENTINEL = "ENGLISH_JSON_SUMMARY_SHOULD_NOT_APPEAR"
_FULL_BODY_SENTINEL = "整份报告正文不应由 CLI 输出"


def _fake_result(status: str = "reused") -> dict:
    return {
        "status": status,
        "html_path": Path("output/research_reports/20260528T000000/600406/fundamental_research_report_v1.html"),
        "markdown_path": Path("output/research_reports/20260528T000000/600406/fundamental_research_report_v1.md"),
        "json_path": Path("output/research_reports/20260528T000000/600406/fundamental_research_report_v1.json"),
        "summary": "中文摘要：本报告仅复用本地已验收 artifact。",
        "largest_opportunity": "最大机会来自本地证据链支持的基本面变量。",
        "largest_risk": "最大风险来自本地证据仍需补充的经营变量。",
        "largest_evidence_gap": "最大证据缺口是本地 artifacts 中缺少更细证据。",
        "data_quality_status": "数据质量状态：本地 artifacts 可用，但保留 caveat。",
        "missing_artifacts": [],
        "manifest_path": Path("output/research_reports/accepted_manifest.json"),
        "manifest_status": "used",
        "manifest_used": True,
        "manifest_warning": None,
        "freshness_status": "current",
        "freshness_warning": None,
        "accepted_at": "2026-05-28T12:55:18+08:00",
        "valuation_as_of_date": "2026-05-28",
        "source_data_period": "2025Q4",
        "full_report_body": "这一大段正文不应由 CLI 直接输出。",
    }


def _formatted_response(result: dict) -> str:
    missing = "\n".join(f"- {item}" for item in result.get("missing_artifacts", []))
    checklist = f"\n缺少的本地 artifacts：\n{missing}" if missing else ""
    return "\n".join(
        [
            f"报告状态：{result['status']}",
            f"HTML: {result.get('html_path') or '未生成'}",
            f"Markdown: {result.get('markdown_path') or '未生成'}",
            f"JSON: {result.get('json_path') or '未生成'}",
            f"Manifest 状态：{result.get('manifest_status') or '未提供'}",
            f"Freshness 状态：{result.get('freshness_status') or '未提供'}",
            f"Freshness 提示：{result.get('freshness_warning') or result.get('manifest_warning') or '无'}",
            f"Accepted at：{result.get('accepted_at') or '未提供'}",
            f"Valuation as-of date：{result.get('valuation_as_of_date') or '未提供'}",
            f"Source data period：{result.get('source_data_period') or '未提供'}",
            "",
            f"简短摘要：{result['summary']}",
            f"最大机会：{result['largest_opportunity']}",
            f"最大风险：{result['largest_risk']}",
            f"最大证据缺口：{result['largest_evidence_gap']}",
            f"数据质量状态：{result['data_quality_status']}",
            checklist,
            "",
            "重要声明：本报告仅用于基本面研究，不构成买卖建议，不包含目标价、仓位或技术面交易信号。",
        ]
    )


def _install_fake_orchestration(monkeypatch: pytest.MonkeyPatch, *, result: dict | None = None) -> dict:
    calls: dict = {}

    def fake_normalize_report_request(*, code=None, company_name=None, output_format="html", data_mode="offline_local_artifacts"):
        calls["normalize"] = {
            "code": code,
            "company_name": company_name,
            "output_format": output_format,
            "data_mode": data_mode,
        }
        return {
            "code": code or "002371",
            "company_name": company_name,
            "output_format": output_format,
            "data_mode": data_mode,
            "provider_mode": "no_live_provider",
            "provider_transport": "none",
            "allow_network": False,
            "allow_token_read": False,
            "not_for_trading_advice": True,
            "strict_evidence_boundary": True,
        }

    def fake_run_single_stock_report_orchestration(
        request,
        *,
        output_root,
        provider_comparison_root=None,
        timestamp=None,
    ):
        calls["run"] = {
            "request": request,
            "output_root": output_root,
            "provider_comparison_root": provider_comparison_root,
            "timestamp": timestamp,
        }
        return result or _fake_result()

    def fake_format_orchestration_response(orchestration_result):
        calls["format"] = orchestration_result
        return _formatted_response(orchestration_result)

    monkeypatch.setattr(generate_report_cli, "normalize_report_request", fake_normalize_report_request)
    monkeypatch.setattr(
        generate_report_cli,
        "run_single_stock_report_orchestration",
        fake_run_single_stock_report_orchestration,
    )
    monkeypatch.setattr(generate_report_cli, "format_orchestration_response", fake_format_orchestration_response)
    return calls


def _run_cli(args: list[str], monkeypatch: pytest.MonkeyPatch, *, result: dict | None = None) -> tuple[int, str, dict]:
    calls = _install_fake_orchestration(monkeypatch, result=result)
    stdout = StringIO()
    exit_code = generate_report_cli.main(args, stdout=stdout)
    return exit_code, stdout.getvalue(), calls


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _fake_report_payload(code: str = "600406") -> dict:
    return {
        "code": code,
        "report_type": "fundamental_research_report_v1",
        "not_for_trading_advice": True,
        "executive_summary": {
            "one_sentence_fundamental_judgement": _ENGLISH_JSON_SUMMARY_SENTINEL,
            "primary_opportunity": {"analysis": "English opportunity sentinel should be hidden by markdown."},
            "primary_risk": {"analysis": "English risk sentinel should be hidden by markdown."},
            "largest_evidence_gap": {"analysis": "English evidence gap sentinel should be hidden by markdown."},
            "data_quality_state": {"analysis": "English data quality sentinel should be hidden by markdown."},
        },
        "data_quality_assessment": {
            "auto_accepted_core_fields": [],
            "manual_review_required_fields": [],
        },
    }


def _fake_markdown() -> str:
    return "\n".join(
        [
            "# Fake accepted report",
            "",
            "## 一句话结论",
            "这是一份仅用于 CLI 集成测试的中文摘要，覆盖 manifest locator 真实路径。",
            "机会来自本地验收 artifact 的一致性校验。",
            "风险来自 freshness 状态变化后的可见提示。",
            "证据缺口来自缺少进一步人工复核材料。",
            "",
            "## 投研速读",
            "- 数据质量：fake JSON 可读取，CLI 应优先展示 Markdown 中文摘要。",
            "",
            "## 正文",
            _FULL_BODY_SENTINEL,
        ]
    )


def _artifact_relative_path(timestamp: str, code: str, filename: str) -> str:
    return f"output/research_reports/{timestamp}/{code}/{filename}"


def _write_fake_cli_artifacts(
    tmp_path: Path,
    *,
    code: str = "600406",
    timestamp: str = "20260528T125518",
) -> dict[str, Path | str]:
    rels = {
        "html": _artifact_relative_path(timestamp, code, "fundamental_research_report_v1.html"),
        "markdown": _artifact_relative_path(timestamp, code, "fundamental_research_report_v1.md"),
        "json": _artifact_relative_path(timestamp, code, "fundamental_research_report_v1.json"),
    }
    paths = {kind: tmp_path / Path(relative) for kind, relative in rels.items()}
    _write_text(paths["html"], "<!doctype html><html><body>fake accepted html shell</body></html>")
    _write_text(paths["markdown"], _fake_markdown())
    _write_json(paths["json"], _fake_report_payload(code))
    return {
        "output_root": tmp_path / "output" / "research_reports",
        "html_path": paths["html"],
        "markdown_path": paths["markdown"],
        "json_path": paths["json"],
        "html_rel": rels["html"],
        "markdown_rel": rels["markdown"],
        "json_rel": rels["json"],
    }


def _manifest_entry(
    artifact_bundle: dict[str, Path | str],
    *,
    code: str = "600406",
    freshness_status: str = "current",
    freshness_reason: str = "direct CLI integration fake baseline",
    hash_mismatch: bool = False,
) -> dict:
    wrong_hash = "0" * 64
    return {
        "code": code,
        "company_name": "Manifest CLI Fake",
        "report_type": "fundamental_research_report_v1",
        "presentation_profile": "stable_growth",
        "accepted_artifacts": {
            "html": artifact_bundle["html_rel"],
            "markdown": artifact_bundle["markdown_rel"],
            "json": artifact_bundle["json_rel"],
        },
        "artifact_hashes": {
            "html_sha256": wrong_hash if hash_mismatch else compute_file_sha256(artifact_bundle["html_path"]),
            "markdown_sha256": compute_file_sha256(artifact_bundle["markdown_path"]),
            "json_sha256": compute_file_sha256(artifact_bundle["json_path"]),
        },
        "acceptance": {
            "accepted_at": "2026-05-28T12:55:18+08:00",
            "accepted_stage": "manifest_cli_integration_test",
            "accepted_by": "test",
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
            "supersedes": [],
            "superseded_by": None,
            "source_artifacts": [],
        },
        "safety": {
            "not_for_trading_advice": True,
            "no_token": True,
            "no_provider_call": True,
        },
    }


def _write_fake_manifest(
    tmp_path: Path,
    artifact_bundle: dict[str, Path | str],
    *,
    freshness_status: str = "current",
    hash_mismatch: bool = False,
) -> Path:
    manifest = build_accepted_manifest(
        [
            _manifest_entry(
                artifact_bundle,
                freshness_status=freshness_status,
                freshness_reason=f"{freshness_status} direct CLI integration fake baseline",
                hash_mismatch=hash_mismatch,
            )
        ],
        created_at="2026-05-28T12:55:18+08:00",
        updated_at="2026-05-28T12:55:18+08:00",
    )
    return write_accepted_manifest(manifest, tmp_path / "output" / "research_reports" / "accepted_manifest.json")


def _run_direct_cli(output_root: Path, *, code: str = "600406") -> tuple[int, str]:
    stdout = StringIO()
    exit_code = generate_report_cli.main(
        [
            "--code",
            code,
            "--format",
            "html",
            "--data-mode",
            "offline_local_artifacts",
            "--output-root",
            str(output_root),
        ],
        stdout=stdout,
    )
    return exit_code, stdout.getvalue()


def _stdout_without_disclaimer(stdout: str) -> str:
    return "\n".join(line for line in stdout.splitlines() if not line.startswith("重要声明："))


def _assert_no_positive_trading_advice_terms(stdout: str) -> None:
    scanned = _stdout_without_disclaimer(stdout).lower()
    for term in _POSITIVE_TRADING_TERMS:
        assert term.lower() not in scanned


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_real_manifest_state() -> dict[str, object]:
    if not _REAL_MANIFEST_PATH.exists():
        return {"exists": False}

    stat = _REAL_MANIFEST_PATH.stat()
    return {
        "exists": True,
        "sha256": _file_sha256(_REAL_MANIFEST_PATH),
        "mtime_ns": stat.st_mtime_ns,
        "size": stat.st_size,
    }


def assert_real_manifest_unchanged(snapshot: dict[str, object]) -> None:
    if not snapshot["exists"]:
        assert not _REAL_MANIFEST_PATH.exists()
    else:
        stat = _REAL_MANIFEST_PATH.stat()
        assert _file_sha256(_REAL_MANIFEST_PATH) == snapshot["sha256"]
        assert stat.st_mtime_ns == snapshot["mtime_ns"]
        assert stat.st_size == snapshot["size"]

    result = subprocess.run(
        ["git", "ls-files", "output"],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.splitlines() == []


def _assert_paths_are_tmp_only(stdout: str, tmp_path: Path) -> None:
    assert str(tmp_path) in stdout
    assert str(Path.cwd() / "output" / "research_reports") not in stdout


def test_code_html_invocation_calls_accepted_orchestration(monkeypatch):
    exit_code, stdout, calls = _run_cli(["--code", "600406", "--format", "html"], monkeypatch)

    assert exit_code == 0
    assert calls["normalize"] == {
        "code": "600406",
        "company_name": None,
        "output_format": "html",
        "data_mode": "offline_local_artifacts",
    }
    assert calls["run"]["request"]["provider_mode"] == "no_live_provider"
    assert calls["run"]["request"]["provider_transport"] == "none"
    assert calls["run"]["request"]["allow_network"] is False
    assert calls["run"]["request"]["allow_token_read"] is False
    assert calls["run"]["output_root"] == Path("output/research_reports")
    assert calls["run"]["provider_comparison_root"] is None
    assert calls["format"] is not None
    assert "HTML:" in stdout
    assert "Markdown:" in stdout
    assert "JSON:" in stdout
    assert "简短摘要：" in stdout


def test_company_name_invocation_calls_accepted_orchestration(monkeypatch):
    exit_code, stdout, calls = _run_cli(["--company-name", "北方华创", "--format", "html"], monkeypatch)

    assert exit_code == 0
    assert calls["normalize"]["code"] is None
    assert calls["normalize"]["company_name"] == "北方华创"
    assert "中文摘要" in stdout


def test_defaults_are_offline_no_provider_no_network_no_token(monkeypatch):
    exit_code, _, calls = _run_cli(["--code", "600406"], monkeypatch)

    assert exit_code == 0
    assert calls["normalize"]["output_format"] == "html"
    assert calls["normalize"]["data_mode"] == "offline_local_artifacts"
    request = calls["run"]["request"]
    assert request["provider_mode"] == "no_live_provider"
    assert request["provider_transport"] == "none"
    assert request["allow_network"] is False
    assert request["allow_token_read"] is False
    assert request["not_for_trading_advice"] is True
    assert request["strict_evidence_boundary"] is True


def test_local_provider_comparison_uses_only_local_provider_comparison_root(monkeypatch):
    exit_code, _, calls = _run_cli(
        [
            "--code",
            "600406",
            "--data-mode",
            "local_provider_comparison",
            "--provider-comparison-root",
            "output/provider_comparison",
        ],
        monkeypatch,
    )

    assert exit_code == 0
    assert calls["normalize"]["data_mode"] == "offline_local_artifacts"
    assert calls["run"]["provider_comparison_root"] == Path("output/provider_comparison")


def test_missing_code_and_company_name_fails_closed_without_calling_orchestration(monkeypatch):
    calls = _install_fake_orchestration(monkeypatch)
    stdout = StringIO()

    exit_code = generate_report_cli.main([], stdout=stdout)

    assert exit_code == 2
    assert "status: 失败_invalid_request" in stdout.getvalue()
    assert "缺少目标标的" in stdout.getvalue()
    assert "normalize" not in calls
    assert "run" not in calls


def test_missing_local_artifacts_returns_checklist_and_exit_code_3(monkeypatch):
    result = _fake_result(status="failed_missing_artifacts")
    result.update(
        {
            "html_path": None,
            "markdown_path": None,
            "json_path": None,
            "missing_artifacts": [
                "local provider comparison artifact root for 600406",
                "fundamental_research_report_v1.json",
            ],
        }
    )

    exit_code, stdout, _ = _run_cli(["--code", "600406"], monkeypatch, result=result)

    assert exit_code == 3
    assert "status: 未生成_missing_local_artifacts" in stdout
    assert "local provider comparison artifact root for 600406" in stdout
    assert "fundamental_research_report_v1.json" in stdout


@pytest.mark.parametrize(
    "args, expected_exit",
    [
        (["--code", "600406", "--data-mode", "future_live_provider"], 4),
        (["--code", "600406", "--allow-network"], 4),
        (["--code", "600406", "--provider-mode", "no_live_provider"], 4),
        (["--code", "600406", "--mcp"], 4),
        (["--code", "600406", "--format", "pdf"], 5),
        (["--code", "600406", "--data-mode", "unknown_mode"], 5),
    ],
)
def test_unsupported_live_provider_network_token_mcp_or_mode_fails_closed(monkeypatch, args, expected_exit):
    calls = _install_fake_orchestration(monkeypatch)
    stdout = StringIO()

    exit_code = generate_report_cli.main(args, stdout=stdout)

    assert exit_code == expected_exit
    assert "失败_" in stdout.getvalue()
    assert "run" not in calls


def test_stdout_contains_required_paths_summary_and_no_full_body(monkeypatch):
    exit_code, stdout, _ = _run_cli(["--code", "600406"], monkeypatch)

    assert exit_code == 0
    assert "fundamental_research_report_v1.html" in stdout
    assert "fundamental_research_report_v1.md" in stdout
    assert "fundamental_research_report_v1.json" in stdout
    assert "中文摘要" in stdout
    assert "最大机会" in stdout
    assert "最大风险" in stdout
    assert "最大证据缺口" in stdout
    assert "数据质量状态" in stdout
    assert "重要声明" in stdout
    assert "这一大段正文不应由 CLI 直接输出" not in stdout


def test_stdout_contains_manifest_and_freshness_fields(monkeypatch):
    result = _fake_result()
    result.update(
        {
            "freshness_status": "stale",
            "freshness_warning": "freshness_status=stale; accepted report may be outdated",
        }
    )

    exit_code, stdout, _ = _run_cli(["--code", "600406"], monkeypatch, result=result)

    assert exit_code == 0
    assert "Manifest" in stdout
    assert "Freshness" in stdout
    assert "stale" in stdout
    assert "accepted report may be outdated" in stdout
    assert "full_report_body" not in stdout


def test_direct_cli_current_manifest_happy_path_uses_tmp_manifest_artifacts(tmp_path):
    real_manifest_snapshot = snapshot_real_manifest_state()
    bundle = _write_fake_cli_artifacts(tmp_path)
    _write_fake_manifest(tmp_path, bundle, freshness_status="current")

    exit_code, stdout = _run_direct_cli(bundle["output_root"])

    assert exit_code == 0
    assert str(bundle["html_path"].resolve(strict=False)) in stdout
    assert str(bundle["markdown_path"].resolve(strict=False)) in stdout
    assert str(bundle["json_path"].resolve(strict=False)) in stdout
    assert "这是一份仅用于 CLI 集成测试的中文摘要" in stdout
    assert "Manifest 状态" in stdout
    assert "used" in stdout
    assert "Freshness 状态" in stdout
    assert "current" in stdout
    assert _ENGLISH_JSON_SUMMARY_SENTINEL not in stdout
    assert "English opportunity sentinel" not in stdout
    assert _FULL_BODY_SENTINEL not in stdout
    _assert_no_positive_trading_advice_terms(stdout)
    _assert_paths_are_tmp_only(stdout, tmp_path)
    assert_real_manifest_unchanged(real_manifest_snapshot)


def test_direct_cli_missing_manifest_falls_back_to_timestamp_artifacts(tmp_path):
    real_manifest_snapshot = snapshot_real_manifest_state()
    bundle = _write_fake_cli_artifacts(tmp_path, timestamp="20260528T131415")

    exit_code, stdout = _run_direct_cli(bundle["output_root"])

    assert exit_code == 0
    assert "manifest_missing_warning" in stdout
    assert str(bundle["html_path"].resolve(strict=False)) in stdout
    assert str(bundle["markdown_path"].resolve(strict=False)) in stdout
    assert str(bundle["json_path"].resolve(strict=False)) in stdout
    assert "Manifest 状态" in stdout
    assert "missing" in stdout
    assert "Freshness 状态" in stdout
    assert "unknown" in stdout
    _assert_no_positive_trading_advice_terms(stdout)
    _assert_paths_are_tmp_only(stdout, tmp_path)
    assert_real_manifest_unchanged(real_manifest_snapshot)


@pytest.mark.parametrize("freshness_status", ["stale", "unknown"])
def test_direct_cli_stale_or_unknown_manifest_is_visible_with_warning(tmp_path, freshness_status):
    real_manifest_snapshot = snapshot_real_manifest_state()
    bundle = _write_fake_cli_artifacts(tmp_path)
    _write_fake_manifest(tmp_path, bundle, freshness_status=freshness_status)

    exit_code, stdout = _run_direct_cli(bundle["output_root"])

    assert exit_code == 0
    assert f"freshness_status={freshness_status}" in stdout
    assert f"Freshness 状态：{freshness_status}" in stdout
    assert "Freshness 提示：" in stdout
    assert str(bundle["html_path"].resolve(strict=False)) in stdout
    _assert_no_positive_trading_advice_terms(stdout)
    _assert_paths_are_tmp_only(stdout, tmp_path)
    assert_real_manifest_unchanged(real_manifest_snapshot)


@pytest.mark.parametrize("freshness_status", ["superseded", "invalidated"])
def test_direct_cli_superseded_or_invalidated_manifest_fails_closed_without_timestamp_fallback(tmp_path, freshness_status):
    real_manifest_snapshot = snapshot_real_manifest_state()
    bundle = _write_fake_cli_artifacts(tmp_path)
    _write_fake_manifest(tmp_path, bundle, freshness_status=freshness_status)

    exit_code, stdout = _run_direct_cli(bundle["output_root"])

    assert exit_code != 0
    assert exit_code == generate_report_cli.SAFETY_BOUNDARY_EXIT_CODE
    assert "failed_invalid_manifest" in stdout
    assert freshness_status in stdout
    assert "fail closed" in stdout
    assert str(bundle["html_path"].resolve(strict=False)) not in stdout
    assert str(bundle["markdown_path"].resolve(strict=False)) not in stdout
    assert str(bundle["json_path"].resolve(strict=False)) not in stdout
    assert "fake accepted html shell" not in stdout
    _assert_no_positive_trading_advice_terms(stdout)
    assert_real_manifest_unchanged(real_manifest_snapshot)


def test_direct_cli_manifest_hash_mismatch_fails_closed_without_artifact_or_secret_leak(tmp_path):
    real_manifest_snapshot = snapshot_real_manifest_state()
    bundle = _write_fake_cli_artifacts(tmp_path)
    _write_fake_manifest(tmp_path, bundle, freshness_status="current", hash_mismatch=True)

    exit_code, stdout = _run_direct_cli(bundle["output_root"])

    assert exit_code != 0
    assert exit_code == generate_report_cli.SAFETY_BOUNDARY_EXIT_CODE
    assert "failed_invalid_manifest" in stdout
    assert "artifact verification failed" in stdout
    assert str(bundle["html_path"].resolve(strict=False)) not in stdout
    assert str(bundle["markdown_path"].resolve(strict=False)) not in stdout
    assert str(bundle["json_path"].resolve(strict=False)) not in stdout
    assert "fake accepted html shell" not in stdout
    assert _FULL_BODY_SENTINEL not in stdout
    assert _ENGLISH_JSON_SUMMARY_SENTINEL not in stdout
    assert "<masked>" not in stdout
    _assert_no_positive_trading_advice_terms(stdout)
    assert_real_manifest_unchanged(real_manifest_snapshot)


def test_stdout_has_no_positive_trading_advice_terms(monkeypatch):
    exit_code, stdout, _ = _run_cli(["--code", "600406"], monkeypatch)

    assert exit_code == 0
    for term in ("买入", "卖出", "加仓", "减仓", "清仓", "止损", "止盈", "K线", "buy", "sell"):
        assert term not in stdout.lower()


def test_cli_source_has_no_env_network_provider_mcp_or_legacy_runner_imports():
    source = inspect.getsource(generate_report_cli)
    blocked_fragments = (
        "os.environ",
        "getenv",
        "requests",
        "urllib",
        "subprocess",
        "import tushare",
        "import akshare",
        "import mcp",
        "real_stock_runner",
        "html_report_runner",
        "generate_fundamental_html_report",
        "ai_analyst.runner",
    )

    assert ("TUSHARE" + "_TOKEN") not in source
    for fragment in blocked_fragments:
        assert fragment not in source


def test_cli_uses_only_thin_orchestration_surface():
    source = inspect.getsource(generate_report_cli)

    assert "normalize_report_request" in source
    assert "run_single_stock_report_orchestration" in source
    assert "format_orchestration_response" in source
    assert "build_research_report_v1" not in source
    assert "render_research_report_v1_markdown" not in source
    assert "render_research_report_v1_html" not in source
    assert "build_fact_candidates" not in source
    assert "build_candidate_review_decisions" not in source
