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
    format_orchestration_response,
    locate_research_report_artifacts,
    normalize_report_request,
    run_single_stock_report_orchestration,
)
import src.fundamental_skill.research_report.orchestration as orchestration_module
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
