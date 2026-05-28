# -*- coding: utf-8 -*-
"""Offline single-stock orchestration for Research Report V1 artifacts.

This module is intentionally a local artifact coordinator. It normalizes a
user request, locates existing Research Report V1 artifacts, and only invokes
the accepted offline builders/renderers when downstream artifacts can be
deterministically reconstructed from local inputs.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import re
from pathlib import Path
from typing import Any

from src.fundamental_skill.ground_truth.auto_fact_candidate_generator import (
    build_fact_candidates_from_comparison_dir,
    write_fact_candidate_report,
)
from src.fundamental_skill.ground_truth.candidate_review_decisions import (
    build_candidate_review_decisions,
    write_candidate_review_decisions,
)

from .research_report_v1 import (
    OUTPUT_FILENAME as JSON_OUTPUT_FILENAME,
    REPORT_TYPE,
    _assert_no_secret_like_payload,
    build_research_report_v1,
    write_research_report_v1,
)
from .research_report_v1_html import (
    HTML_OUTPUT_FILENAME,
    _assert_html_has_no_external_resources,
    _assert_no_forbidden_trading_terms,
    _assert_no_local_path_like_payload,
    render_research_report_v1_html,
    write_research_report_v1_html,
)
from .research_report_v1_presentation import (
    MARKDOWN_OUTPUT_FILENAME,
    render_research_report_v1_markdown,
    write_research_report_v1_markdown,
)


class ReportRequestError(ValueError):
    """Raised when a user request cannot be safely normalized."""


class ReportArtifactError(RuntimeError):
    """Raised when local artifact orchestration cannot continue safely."""


KNOWN_COMPANY_TO_CODE = {
    "国电南瑞": "600406",
    "北方华创": "002371",
    "三花智控": "002050",
}
KNOWN_CODE_TO_COMPANY = {code: company for company, code in KNOWN_COMPANY_TO_CODE.items()}

FACT_CANDIDATES_FILENAME = "fact_candidates.json"
CANDIDATE_REVIEW_DECISIONS_FILENAME = "candidate_review_decisions.json"

_A_SHARE_CODE_RE = re.compile(r"(?<!\d)(?:SH|SZ|sh|sz)?([0-9]{6})(?!\d)")
_SAFE_TIMESTAMP_RE = re.compile(r"^[A-Za-z0-9T_-]{1,64}$")
_TIMESTAMP_DIR_RE = re.compile(r"^\d{8}T\d{6}$")

_OUTPUT_FORMATS = {"json", "markdown", "md", "html", "all"}
_SUPPORTED_DATA_MODE = "offline_local_artifacts"
_SAFE_DEFAULTS = {
    "report_type": REPORT_TYPE,
    "output_format": "html",
    "data_mode": _SUPPORTED_DATA_MODE,
    "provider_mode": "no_live_provider",
    "provider_transport": "none",
    "allow_network": False,
    "allow_token_read": False,
    "reasoning_level": "high",
    "not_for_trading_advice": True,
    "requested_sections": [],
    "language": "zh-CN",
    "strict_evidence_boundary": True,
}
_NON_CHINESE_SUMMARY_FALLBACK = "当前仅找到结构化摘要字段，建议打开 Markdown 报告查看中文摘要。"
_CHINESE_CHAR_RE = re.compile(r"[\u4e00-\u9fff]")

_PROVIDER_COMPARISON_INPUT_FILENAMES = (
    "tushare_fundamental.json",
    "akshare_fundamental.json",
    "tushare_evidence_pack.json",
    "akshare_evidence_pack.json",
    "diff_report.json",
    "score_confidence_explainability.json",
)
_FUNDAMENTAL_INPUTS = {
    "tushare": "tushare_fundamental.json",
    "akshare": "akshare_fundamental.json",
}
_EVIDENCE_PACK_INPUTS = {
    "tushare": "tushare_evidence_pack.json",
    "akshare": "akshare_evidence_pack.json",
}

_POSITIVE_TRADING_PATTERNS = tuple(
    re.compile(pattern, flags=re.IGNORECASE)
    for pattern in (
        r"买入",
        r"卖出",
        r"持有建议",
        r"加仓",
        r"减仓",
        r"清仓",
        r"止损",
        r"止盈",
        r"K线",
        r"\bbuy\b",
        r"\bsell\b",
        r"\bhold\s+recommendation\b",
        r"\bincrease\s+position\b",
        r"\breduce\s+position\b",
        r"\bstop\s+loss\b",
        r"\btake\s+profit\b",
        r"\btechnical\s+trading\s+signal\b",
    )
)


def normalize_report_request(
    user_text: str | None = None,
    *,
    code: str | None = None,
    company_name: str | None = None,
    output_format: str = "html",
    data_mode: str = _SUPPORTED_DATA_MODE,
) -> dict[str, Any]:
    """Normalize a natural-language single-stock report request.

    The function only uses explicit request text and a small local alias table.
    It does not infer unknown companies from external sources.
    """

    text = user_text or ""
    normalized_format = _normalize_output_format(output_format)
    if data_mode != _SUPPORTED_DATA_MODE:
        raise ReportRequestError("当前阶段仅支持 offline_local_artifacts 数据模式。")

    resolved_code = _normalize_optional_code(code) or _extract_code(text)
    resolved_company = company_name or _company_from_text(text)

    if resolved_company and not resolved_code:
        resolved_code = KNOWN_COMPANY_TO_CODE.get(resolved_company)
    if resolved_code and not resolved_company:
        resolved_company = KNOWN_CODE_TO_COMPANY.get(resolved_code)

    stock_pool = None
    if not any((resolved_code, resolved_company, stock_pool)):
        raise ReportRequestError("缺少目标标的：请补充股票代码、公司名或 stock_pool。")

    request = {
        "code": resolved_code,
        "company_name": resolved_company,
        "stock_pool": stock_pool,
        **_SAFE_DEFAULTS,
        "output_format": normalized_format,
        "data_mode": data_mode,
    }
    return request


def locate_research_report_artifacts(
    code: str,
    output_root: Path,
    provider_comparison_root: Path | None = None,
) -> dict[str, Any]:
    """Locate the latest local Research Report V1 artifacts for one code."""

    normalized_code = _normalize_required_code(code)
    root = Path(output_root)
    provider_dir = _find_latest_provider_comparison_dir(normalized_code, provider_comparison_root)
    provider_artifacts = _provider_comparison_artifacts(provider_dir)

    html_path = _latest_artifact(root, normalized_code, HTML_OUTPUT_FILENAME)
    markdown_path = _latest_artifact(root, normalized_code, MARKDOWN_OUTPUT_FILENAME)
    json_path = _latest_artifact(root, normalized_code, JSON_OUTPUT_FILENAME)
    fact_candidates_path = _latest_artifact(root, normalized_code, FACT_CANDIDATES_FILENAME) or _artifact_in_dir(
        provider_dir,
        FACT_CANDIDATES_FILENAME,
    )
    decisions_path = _latest_artifact(root, normalized_code, CANDIDATE_REVIEW_DECISIONS_FILENAME) or _artifact_in_dir(
        provider_dir,
        CANDIDATE_REVIEW_DECISIONS_FILENAME,
    )

    missing_artifacts: list[str] = []
    if not any((html_path, markdown_path, json_path)) and not _can_rebuild_from_provider_artifacts(provider_artifacts):
        missing_artifacts = _missing_local_artifact_checklist(normalized_code)

    return {
        "code": normalized_code,
        "html_path": html_path,
        "markdown_path": markdown_path,
        "json_path": json_path,
        "fact_candidates_path": fact_candidates_path,
        "candidate_review_decisions_path": decisions_path,
        "provider_comparison_dir": provider_dir,
        "provider_comparison_artifacts": provider_artifacts,
        "missing_artifacts": missing_artifacts,
    }


def run_single_stock_report_orchestration(
    request: dict[str, Any],
    *,
    output_root: Path,
    provider_comparison_root: Path | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Run the offline single-stock Research Report V1 orchestration path."""

    normalized_request = _validate_orchestration_request(request)
    code = str(normalized_request["code"])
    company_name = normalized_request.get("company_name") or KNOWN_CODE_TO_COMPANY.get(code)
    output_root = Path(output_root)
    timestamp_text = _safe_timestamp(timestamp)
    actions_taken: list[str] = ["validated_request"]

    located = locate_research_report_artifacts(code, output_root, provider_comparison_root)
    actions_taken.append("located_local_artifacts")

    if located["html_path"]:
        report = _load_optional_report(located["json_path"])
        _scan_existing_artifacts(
            located["html_path"],
            located["markdown_path"],
            located["json_path"],
            located["fact_candidates_path"],
            located["candidate_review_decisions_path"],
        )
        actions_taken.append("reused_existing_html")
        return _build_result(
            status="reused",
            code=code,
            company_name=company_name,
            html_path=located["html_path"],
            markdown_path=located["markdown_path"],
            json_path=located["json_path"],
            fact_candidates_path=located["fact_candidates_path"],
            candidate_review_decisions_path=located["candidate_review_decisions_path"],
            report=report,
            missing_artifacts=[],
            actions_taken=actions_taken,
        )

    if located["markdown_path"]:
        report = _load_optional_report(located["json_path"])
        markdown = _read_text_artifact(located["markdown_path"])
        html = render_research_report_v1_html(markdown, report)
        html_path = write_research_report_v1_html(html, output_root, timestamp_text, code)
        actions_taken.append("generated_html_from_markdown")
        return _build_result(
            status="generated",
            code=code,
            company_name=company_name,
            html_path=html_path,
            markdown_path=located["markdown_path"],
            json_path=located["json_path"],
            fact_candidates_path=located["fact_candidates_path"],
            candidate_review_decisions_path=located["candidate_review_decisions_path"],
            report=report,
            missing_artifacts=[],
            actions_taken=actions_taken,
        )

    if located["json_path"]:
        report = _load_json_artifact(located["json_path"])
        markdown_path = write_research_report_v1_markdown(report, output_root, timestamp_text)
        markdown = _read_text_artifact(markdown_path)
        html = render_research_report_v1_html(markdown, report)
        html_path = write_research_report_v1_html(html, output_root, timestamp_text, code)
        actions_taken.extend(["generated_markdown_from_json", "generated_html_from_markdown"])
        return _build_result(
            status="generated",
            code=code,
            company_name=company_name,
            html_path=html_path,
            markdown_path=markdown_path,
            json_path=located["json_path"],
            fact_candidates_path=located["fact_candidates_path"],
            candidate_review_decisions_path=located["candidate_review_decisions_path"],
            report=report,
            missing_artifacts=[],
            actions_taken=actions_taken,
        )

    if _can_rebuild_from_provider_artifacts(located["provider_comparison_artifacts"]):
        comparison_dir = located["provider_comparison_dir"]
        if comparison_dir is None:
            raise ReportArtifactError("provider comparison directory is unavailable")

        if located["fact_candidates_path"]:
            fact_candidates = _load_json_artifact(located["fact_candidates_path"])
            fact_candidates_path = located["fact_candidates_path"]
            actions_taken.append("reused_fact_candidates")
        else:
            fact_candidates = build_fact_candidates_from_comparison_dir(comparison_dir)
            fact_candidates_path = write_fact_candidate_report(fact_candidates, output_root, timestamp_text)
            actions_taken.append("generated_fact_candidates")

        if located["candidate_review_decisions_path"]:
            review_decisions = _load_json_artifact(located["candidate_review_decisions_path"])
            decisions_path = located["candidate_review_decisions_path"]
            actions_taken.append("reused_candidate_review_decisions")
        else:
            review_decisions = build_candidate_review_decisions(
                fact_candidates,
                reviewed_at=_generated_at_from_timestamp(timestamp_text),
            )
            decisions_path = write_candidate_review_decisions(review_decisions, output_root, timestamp_text)
            actions_taken.append("generated_candidate_review_decisions")

        provider_inputs = _load_provider_comparison_inputs(comparison_dir)
        report = build_research_report_v1(
            code=code,
            fundamental_payloads=provider_inputs["fundamental_payloads"],
            evidence_pack_payloads=provider_inputs["evidence_pack_payloads"],
            fact_candidates=fact_candidates,
            review_decisions=review_decisions,
            score_explainability=provider_inputs["score_explainability"],
            diff_report=provider_inputs["diff_report"],
            generated_at=_generated_at_from_timestamp(timestamp_text),
        )
        json_path = write_research_report_v1(report, output_root, timestamp_text)
        markdown_path = write_research_report_v1_markdown(report, output_root, timestamp_text)
        markdown = _read_text_artifact(markdown_path)
        html = render_research_report_v1_html(markdown, report)
        html_path = write_research_report_v1_html(html, output_root, timestamp_text, code)
        actions_taken.extend(
            [
                "generated_research_report_json",
                "generated_markdown_from_json",
                "generated_html_from_markdown",
            ]
        )
        return _build_result(
            status="generated",
            code=code,
            company_name=company_name,
            html_path=html_path,
            markdown_path=markdown_path,
            json_path=json_path,
            fact_candidates_path=fact_candidates_path,
            candidate_review_decisions_path=decisions_path,
            report=report,
            missing_artifacts=[],
            actions_taken=actions_taken,
        )

    actions_taken.append("failed_closed_missing_local_artifacts")
    return _build_result(
        status="failed_missing_artifacts",
        code=code,
        company_name=company_name,
        html_path=None,
        markdown_path=None,
        json_path=None,
        fact_candidates_path=located["fact_candidates_path"],
        candidate_review_decisions_path=located["candidate_review_decisions_path"],
        report=None,
        missing_artifacts=located["missing_artifacts"] or _missing_local_artifact_checklist(code),
        actions_taken=actions_taken,
    )


def format_orchestration_response(result: dict[str, Any]) -> str:
    """Format a short Chinese user-facing orchestration response."""

    status = str(result.get("status") or "unknown")
    status_text = {
        "generated": "已生成",
        "reused": "已找到并复用",
        "failed_missing_artifacts": "未生成：缺少本地 artifact",
    }.get(status, status)
    markdown_parts = _summary_parts_from_markdown_path(result.get("markdown_path"))

    lines = [
        f"报告状态：{status_text}",
        f"HTML: {_display_path(result.get('html_path'))}",
        f"Markdown: {_display_path(result.get('markdown_path'))}",
        f"JSON: {_display_path(result.get('json_path'))}",
        "",
        f"简短摘要：{_user_facing_summary(result, markdown_parts)}",
        f"最大机会：{_user_facing_detail(result, 'largest_opportunity', markdown_parts, '已定位结构化机会字段；建议打开 Markdown 报告查看中文机会说明。')}",
        f"最大风险：{_user_facing_detail(result, 'largest_risk', markdown_parts, '已定位结构化风险字段；建议打开 Markdown 报告查看中文风险说明。')}",
        f"最大证据缺口：{_user_facing_detail(result, 'largest_evidence_gap', markdown_parts, '已定位结构化证据缺口字段；建议打开 Markdown 报告查看中文证据说明。')}",
        f"数据质量状态：{_user_facing_detail(result, 'data_quality_status', markdown_parts, '已定位结构化数据质量字段；建议打开 Markdown 报告查看中文数据质量说明。')}",
    ]

    missing = [str(item) for item in result.get("missing_artifacts") or []]
    if missing:
        lines.extend(["", "缺少的本地 artifacts：", *[f"- {item}" for item in missing]])

    lines.extend(
        [
            "",
            "重要声明：本报告仅用于基本面研究，不构成买卖建议，不包含目标价、仓位或技术面交易信号。",
        ]
    )
    return "\n".join(lines)


def extract_chinese_summary_from_markdown(markdown_text: str) -> str:
    """Extract a short Chinese user-facing summary from accepted V1 Markdown."""

    return _extract_chinese_summary_parts_from_markdown(markdown_text).get("summary", "")


def _validate_orchestration_request(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ReportRequestError("request must be a dict")

    merged = {**_SAFE_DEFAULTS, **request}
    code = _normalize_optional_code(merged.get("code"))
    company_name = merged.get("company_name")
    if not company_name and code:
        company_name = KNOWN_CODE_TO_COMPANY.get(code)
    if company_name and not code:
        code = KNOWN_COMPANY_TO_CODE.get(str(company_name))

    stock_pool = merged.get("stock_pool")
    if not any((code, company_name, stock_pool)):
        raise ReportRequestError("缺少目标标的：请补充股票代码、公司名或 stock_pool。")
    if not code:
        raise ReportRequestError("当前 V1 单票 offline orchestration 需要可本地解析的 6 位股票代码。")
    if stock_pool:
        raise ReportRequestError("当前阶段仅实现 V1 单票 orchestration，stock_pool 批量模式尚未启用。")

    _assert_safe_request_flags(merged)
    merged["code"] = code
    merged["company_name"] = company_name
    merged["stock_pool"] = None
    merged["output_format"] = _normalize_output_format(str(merged.get("output_format") or "html"))
    return merged


def _assert_safe_request_flags(request: dict[str, Any]) -> None:
    expected = {
        "report_type": REPORT_TYPE,
        "data_mode": _SUPPORTED_DATA_MODE,
        "provider_mode": "no_live_provider",
        "provider_transport": "none",
        "allow_network": False,
        "allow_token_read": False,
        "not_for_trading_advice": True,
        "strict_evidence_boundary": True,
    }
    for key, expected_value in expected.items():
        if request.get(key) != expected_value:
            raise ReportRequestError(f"unsafe request flag: {key}")


def _build_result(
    *,
    status: str,
    code: str,
    company_name: str | None,
    html_path: Path | None,
    markdown_path: Path | None,
    json_path: Path | None,
    fact_candidates_path: Path | None,
    candidate_review_decisions_path: Path | None,
    report: dict[str, Any] | None,
    missing_artifacts: list[str],
    actions_taken: list[str],
) -> dict[str, Any]:
    summary_fields = _summary_fields(report, status=status)
    markdown_parts = _summary_parts_from_markdown_path(markdown_path)
    if markdown_parts.get("summary"):
        summary_fields["summary"] = markdown_parts["summary"]
    elif not _contains_chinese(summary_fields["summary"]):
        summary_fields["artifact_summary_raw"] = summary_fields["summary"]
        summary_fields["summary"] = _NON_CHINESE_SUMMARY_FALLBACK
    for key in ("summary", "largest_opportunity", "largest_risk", "largest_evidence_gap", "data_quality_status"):
        _assert_no_positive_trading_output(summary_fields[key])
    return {
        "status": status,
        "code": code,
        "company_name": company_name,
        "html_path": html_path,
        "markdown_path": markdown_path,
        "json_path": json_path,
        "fact_candidates_path": fact_candidates_path,
        "candidate_review_decisions_path": candidate_review_decisions_path,
        **summary_fields,
        "not_for_trading_advice": True,
        "missing_artifacts": missing_artifacts,
        "actions_taken": actions_taken,
    }


def _user_facing_summary(result: dict[str, Any], markdown_parts: dict[str, str] | None = None) -> str:
    markdown_summary = (markdown_parts or {}).get("summary")
    if markdown_summary:
        return markdown_summary

    summary = _display_text(result.get("summary"))
    if _contains_chinese(summary):
        return summary
    return _NON_CHINESE_SUMMARY_FALLBACK


def _user_facing_detail(
    result: dict[str, Any],
    key: str,
    markdown_parts: dict[str, str] | None,
    fallback: str,
) -> str:
    markdown_detail = (markdown_parts or {}).get(key)
    if markdown_detail:
        return markdown_detail
    value = _display_text(result.get(key))
    if _contains_chinese(value):
        return value
    return fallback


def _summary_parts_from_markdown_path(markdown_path: Any) -> dict[str, str]:
    if not markdown_path:
        return {}
    path = Path(markdown_path)
    if not path.is_file():
        return {}
    try:
        markdown = _read_text_artifact(path)
    except ReportArtifactError:
        return {}
    return _extract_chinese_summary_parts_from_markdown(markdown)


def _extract_chinese_summary_parts_from_markdown(markdown_text: str) -> dict[str, str]:
    if not isinstance(markdown_text, str) or not markdown_text.strip():
        return {}

    parts: dict[str, str] = {}
    conclusion_lines = _clean_markdown_lines(_extract_markdown_section_lines(markdown_text, "一句话结论"), max_lines=4)
    conclusion = " ".join(conclusion_lines)
    if _contains_chinese(conclusion):
        parts["summary"] = _short_text(conclusion, limit=480)
        for line in conclusion_lines:
            if "机会" in line and "largest_opportunity" not in parts:
                parts["largest_opportunity"] = _short_text(line, limit=260)
            if "风险" in line and "largest_risk" not in parts:
                parts["largest_risk"] = _short_text(line, limit=260)
            if "证据缺口" in line and "largest_evidence_gap" not in parts:
                parts["largest_evidence_gap"] = _short_text(line, limit=260)

    quick_read_lines = _clean_markdown_lines(
        _extract_markdown_section_lines(markdown_text, "投研速读"),
        max_lines=8,
        bullets_only=True,
    )
    for line in quick_read_lines:
        if ("数据可信度" in line or "数据质量" in line) and "data_quality_status" not in parts:
            parts["data_quality_status"] = _short_text(line, limit=260)

    if "summary" not in parts:
        quick_summary = " ".join(quick_read_lines[:2])
        if _contains_chinese(quick_summary):
            parts["summary"] = _short_text(quick_summary, limit=480)

    return parts


def _extract_markdown_section_lines(markdown_text: str, heading: str) -> list[str]:
    section: list[str] = []
    in_section = False
    expected_heading = f"## {heading}"

    for line in markdown_text.splitlines():
        stripped = line.strip()
        if in_section and stripped.startswith("## "):
            break
        if not in_section and stripped == expected_heading:
            in_section = True
            continue
        if in_section:
            section.append(line)

    return section


def _compact_markdown_lines(lines: list[str], *, max_lines: int, bullets_only: bool = False) -> str:
    return " ".join(_clean_markdown_lines(lines, max_lines=max_lines, bullets_only=bullets_only))


def _clean_markdown_lines(lines: list[str], *, max_lines: int, bullets_only: bool = False) -> list[str]:
    selected: list[str] = []
    for line in lines:
        cleaned = _clean_markdown_summary_line(line)
        if not cleaned:
            continue
        if bullets_only and not _is_markdown_bullet(line):
            continue
        selected.append(cleaned)
        if len(selected) >= max_lines:
            break
    return selected


def _clean_markdown_summary_line(line: str) -> str:
    cleaned = line.strip()
    cleaned = re.sub(r"^[-*+]\s+", "", cleaned)
    cleaned = re.sub(r"^\d+[.)、]\s+", "", cleaned)
    cleaned = cleaned.replace("**", "").replace("`", "")
    return " ".join(cleaned.split())


def _is_markdown_bullet(line: str) -> bool:
    return bool(re.match(r"^\s*(?:[-*+]|\d+[.)、])\s+", line))


def _contains_chinese(text: Any) -> bool:
    return bool(_CHINESE_CHAR_RE.search(str(text or "")))


def _summary_fields(report: dict[str, Any] | None, *, status: str) -> dict[str, str]:
    if not report:
        if status == "failed_missing_artifacts":
            text = "缺少本地 Research Report V1 链路 artifact，已 fail closed，未生成报告。"
        else:
            text = "已定位本地展示 artifact；未找到可用于结构化摘要的 Research Report V1 JSON。"
        return {
            "summary": text,
            "largest_opportunity": "未从本地 JSON 中提取到结构化机会字段。",
            "largest_risk": "未从本地 JSON 中提取到结构化风险字段。",
            "largest_evidence_gap": "未从本地 JSON 中提取到结构化证据缺口字段。",
            "data_quality_status": "缺少结构化 JSON 数据质量字段。",
        }

    executive = _dict_or_empty(report.get("executive_summary"))
    return {
        "summary": _short_text(
            _text_from_item(executive.get("one_sentence_fundamental_judgement"))
            or _text_from_item(executive.get("evidence_strength"))
            or "已基于本地 Research Report V1 JSON 提取摘要。"
        ),
        "largest_opportunity": _short_text(_text_from_item(executive.get("primary_opportunity")) or "本地 JSON 未提供 primary_opportunity。"),
        "largest_risk": _short_text(_text_from_item(executive.get("primary_risk")) or "本地 JSON 未提供 primary_risk。"),
        "largest_evidence_gap": _short_text(_text_from_item(executive.get("largest_evidence_gap")) or "本地 JSON 未提供 largest_evidence_gap。"),
        "data_quality_status": _short_text(_text_from_item(executive.get("data_quality_state")) or _data_quality_fallback(report)),
    }


def _data_quality_fallback(report: dict[str, Any]) -> str:
    quality = _dict_or_empty(report.get("data_quality_assessment"))
    auto_count = len(_as_list(quality.get("auto_accepted_core_fields")))
    review_count = len(_as_list(quality.get("manual_review_required_fields")))
    return f"候选可用字段 {auto_count} 项；仍需人工复核字段 {review_count} 项。"


def _latest_artifact(root: Path, code: str, filename: str) -> Path | None:
    if not root.exists():
        return None
    paths: dict[str, Path] = {}
    direct = root / code / filename
    if direct.is_file():
        paths[str(direct.resolve(strict=False))] = direct
    for path in root.rglob(filename):
        if path.is_file() and path.parent.name == code:
            paths[str(path.resolve(strict=False))] = path
    if not paths:
        return None
    return sorted(paths.values(), key=_artifact_sort_key)[-1].resolve(strict=False)


def _artifact_sort_key(path: Path) -> tuple[str, int, str]:
    parent_name = path.parent.parent.name if path.parent.name else ""
    timestamp = parent_name if _TIMESTAMP_DIR_RE.fullmatch(parent_name) else ""
    try:
        mtime = path.stat().st_mtime_ns
    except OSError:
        mtime = 0
    return (timestamp, mtime, str(path))


def _find_latest_provider_comparison_dir(code: str, provider_comparison_root: Path | None) -> Path | None:
    if provider_comparison_root is None:
        return None
    root = Path(provider_comparison_root)
    if not root.exists():
        return None

    candidates: dict[str, Path] = {}
    if root.name == code and root.is_dir():
        candidates[str(root.resolve(strict=False))] = root
    direct = root / code
    if direct.is_dir():
        candidates[str(direct.resolve(strict=False))] = direct
    for path in root.rglob(code):
        if path.is_dir() and path.name == code:
            candidates[str(path.resolve(strict=False))] = path

    usable = [path for path in candidates.values() if _provider_comparison_artifacts(path)]
    if not usable:
        return None
    return sorted(usable, key=_provider_dir_sort_key)[-1].resolve(strict=False)


def _provider_dir_sort_key(path: Path) -> tuple[str, int, str]:
    try:
        mtime = path.stat().st_mtime_ns
    except OSError:
        mtime = 0
    timestamp = path.parent.name if _TIMESTAMP_DIR_RE.fullmatch(path.parent.name) else ""
    return (timestamp, mtime, str(path))


def _provider_comparison_artifacts(provider_dir: Path | None) -> dict[str, Path]:
    if provider_dir is None:
        return {}
    artifacts = {}
    for filename in _PROVIDER_COMPARISON_INPUT_FILENAMES:
        path = provider_dir / filename
        if path.is_file():
            artifacts[filename] = path.resolve(strict=False)
    return artifacts


def _artifact_in_dir(directory: Path | None, filename: str) -> Path | None:
    if directory is None:
        return None
    path = directory / filename
    if path.is_file():
        return path.resolve(strict=False)
    return None


def _can_rebuild_from_provider_artifacts(artifacts: dict[str, Path]) -> bool:
    return any(filename in artifacts for filename in _FUNDAMENTAL_INPUTS.values())


def _load_provider_comparison_inputs(comparison_dir: Path) -> dict[str, Any]:
    fundamental_payloads = _load_named_json_payloads(comparison_dir, _FUNDAMENTAL_INPUTS)
    if not fundamental_payloads:
        raise ReportArtifactError("missing provider-separated fundamental artifacts")
    evidence_pack_payloads = _load_named_json_payloads(comparison_dir, _EVIDENCE_PACK_INPUTS)
    return {
        "fundamental_payloads": fundamental_payloads,
        "evidence_pack_payloads": evidence_pack_payloads,
        "diff_report": _load_optional_json(comparison_dir / "diff_report.json"),
        "score_explainability": _load_optional_json(comparison_dir / "score_confidence_explainability.json"),
    }


def _load_named_json_payloads(comparison_dir: Path, filenames: dict[str, str]) -> dict[str, Any]:
    payloads: dict[str, Any] = {}
    for key, filename in filenames.items():
        path = comparison_dir / filename
        if path.is_file():
            payloads[key] = _load_json_artifact(path)
    return payloads


def _load_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return _load_json_artifact(path)


def _load_optional_report(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    return _load_json_artifact(path)


def _load_json_artifact(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReportArtifactError(f"cannot read JSON artifact: {path}") from exc
    if not isinstance(payload, dict):
        raise ReportArtifactError(f"JSON artifact must contain an object: {path}")
    _assert_no_secret_like_payload(payload)
    return payload


def _read_text_artifact(path: Path) -> str:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise ReportArtifactError(f"cannot read text artifact: {path}") from exc
    _assert_no_secret_like_payload(text)
    return text


def _scan_existing_artifacts(*paths: Path | None) -> None:
    for path in paths:
        if path is None:
            continue
        if path.suffix == ".json":
            _load_json_artifact(path)
            continue
        text = _read_text_artifact(path)
        if path.suffix == ".html":
            _assert_no_local_path_like_payload(text)
            _assert_no_forbidden_trading_terms(text)
            _assert_html_has_no_external_resources(text)


def _missing_local_artifact_checklist(code: str) -> list[str]:
    return [
        f"local provider comparison artifact root for {code}",
        "provider-separated fundamental artifacts",
        "provider-separated evidence packs",
        FACT_CANDIDATES_FILENAME,
        CANDIDATE_REVIEW_DECISIONS_FILENAME,
        JSON_OUTPUT_FILENAME,
        MARKDOWN_OUTPUT_FILENAME,
        HTML_OUTPUT_FILENAME,
    ]


def _normalize_output_format(output_format: str) -> str:
    normalized = str(output_format or "html").lower()
    if normalized not in _OUTPUT_FORMATS:
        raise ReportRequestError("output_format must be json, markdown, html, or all")
    return "markdown" if normalized == "md" else normalized


def _extract_code(text: str) -> str | None:
    match = _A_SHARE_CODE_RE.search(text)
    return match.group(1) if match else None


def _company_from_text(text: str) -> str | None:
    for company in KNOWN_COMPANY_TO_CODE:
        if company in text:
            return company
    return None


def _normalize_optional_code(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    match = _A_SHARE_CODE_RE.search(text)
    if not match:
        raise ReportRequestError("股票代码必须是 6 位 A 股代码。")
    return match.group(1)


def _normalize_required_code(value: Any) -> str:
    code = _normalize_optional_code(value)
    if not code:
        raise ReportRequestError("缺少 6 位股票代码。")
    return code


def _safe_timestamp(timestamp: str | None) -> str:
    timestamp_text = timestamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    if not _SAFE_TIMESTAMP_RE.fullmatch(timestamp_text) or ".." in timestamp_text:
        raise ReportArtifactError("timestamp contains unsupported path characters")
    return timestamp_text


def _generated_at_from_timestamp(timestamp: str) -> str:
    match = re.fullmatch(r"(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})", timestamp)
    if not match:
        return timestamp
    year, month, day, hour, minute, second = match.groups()
    return f"{year}-{month}-{day}T{hour}:{minute}:{second}+00:00"


def _text_from_item(value: Any) -> str | None:
    if isinstance(value, dict):
        for key in ("analysis", "summary", "caveat", "status", "title", "field_path"):
            item = value.get(key)
            if item:
                return str(item)
    if isinstance(value, list):
        for item in value:
            text = _text_from_item(item)
            if text:
                return text
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _short_text(text: str, limit: int = 260) -> str:
    compact = " ".join(str(text).split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def _assert_no_positive_trading_output(text: str) -> None:
    for pattern in _POSITIVE_TRADING_PATTERNS:
        if pattern.search(text):
            raise ReportArtifactError("summary contains prohibited investment-action language")


def _display_path(value: Any) -> str:
    return str(value) if value else "未生成"


def _display_text(value: Any) -> str:
    return str(value) if value else "未提供"


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []
