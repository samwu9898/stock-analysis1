# -*- coding: utf-8 -*-

from __future__ import annotations

import inspect
from io import StringIO
from pathlib import Path

import pytest

import src.fundamental_skill.research_report.generate_report as generate_report_cli


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
