# -*- coding: utf-8 -*-
"""Render AI analyst JSON reports to UTF-8 Markdown.

This renderer is intentionally presentation-only. It does not run the
deterministic pipeline, change classification, score fundamentals, or add
trading guidance.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .safety import detect_garbled_text, is_garbled_text


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"
GARBLED_TEXT_WARNING = "部分 AI 自由文本字段损坏，当前报告使用结构化 evidence fallback 生成。"


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _display_value(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, dict):
        if value.get("display_value") not in (None, ""):
            return str(value.get("display_value"))
        if value.get("raw_value") not in (None, ""):
            return str(value.get("raw_value"))
        return json.dumps(value, ensure_ascii=False, default=str)
    if isinstance(value, list):
        return "; ".join(_display_value(item) for item in value[:6]) or "-"
    return str(value)


def _is_corrupt_text(value: Any) -> bool:
    if not isinstance(value, str):
        return True
    text = value.strip()
    if not text:
        return True
    return is_garbled_text(text)


def _safe_text(value: Any, fallback: str) -> str:
    return fallback if _is_corrupt_text(value) else str(value).strip()


def _stock(report: dict[str, Any], evidence_pack: dict[str, Any] | None, fundamental: dict[str, Any] | None) -> dict[str, Any]:
    evidence_stock = (evidence_pack or {}).get("stock") if isinstance((evidence_pack or {}).get("stock"), dict) else {}
    return {
        "code": report.get("stock_code") or evidence_stock.get("code") or (fundamental or {}).get("stock_code") or "",
        "name": report.get("stock_name") or evidence_stock.get("name") or (fundamental or {}).get("stock_name") or "",
        "strategy_type": evidence_stock.get("strategy_type") or (fundamental or {}).get("strategy_type") or "",
        "status": evidence_stock.get("status") or (fundamental or {}).get("status") or "",
        "confidence": evidence_stock.get("confidence") or (fundamental or {}).get("confidence") or "",
        "score": evidence_stock.get("fundamental_score") or (fundamental or {}).get("fundamental_score"),
    }


def _summary_fallback(stock: dict[str, Any], report: dict[str, Any], evidence_pack: dict[str, Any] | None) -> str:
    missing = _as_list((evidence_pack or {}).get("confidence_basis", {}).get("missing_fields"))
    missing_names = [str(item.get("field")) for item in missing if isinstance(item, dict) and item.get("field")]
    core_missing = [
        item
        for item in missing_names
        if item.startswith("satellite.") or item == "financial_metrics.depreciation_amortization"
    ]
    if stock["strategy_type"] == "satellite_communication_infrastructure":
        suffix = "、".join(core_missing[:4]) if core_missing else "行业专属运营指标"
        return (
            f"{stock['code']} 当前识别为 satellite_communication_infrastructure，"
            f"fundamental_view 为 {report.get('fundamental_view') or '-'}，confidence 为 {stock['confidence'] or '-'}。"
            f"由于{suffix}等关键数据缺失，报告只能形成保守的基本面摘要。"
        )
    return (
        f"{stock['code']} 当前 fundamental_view 为 {report.get('fundamental_view') or '-'}，"
        f"confidence 为 {stock['confidence'] or '-'}。"
    )


def _analysis_fallback(section: str, stock: dict[str, Any]) -> str:
    if section == "business_analysis":
        return "主营和业务构成以 evidence pack 中的结构化字段为准；缺失字段不作补推。"
    if section == "financial_quality_analysis":
        return "财务指标仅用于观察基础经营质量；缺失数据不足以判断未披露的经营维度。"
    if section == "valuation_analysis":
        if stock["strategy_type"] == "satellite_communication_infrastructure":
            return "PE/PB/PS 只能作为辅助估值背景，不能单独构成估值充分依据。"
        return "估值分析仅基于已披露 valuation_metrics，缺失数据不作补推。"
    if section == "industry_cycle_analysis":
        if stock["strategy_type"] == "satellite_communication_infrastructure":
            return "行业专属数据缺失时，不足以判断商业航天业务兑现、容量利用率或客户需求稳定性。"
        return "行业变量需要继续结合可验证数据观察。"
    return "当前只能形成保守摘要，缺失数据不作补推。"


def _table_row(cells: list[Any]) -> str:
    safe_cells = [str(cell).replace("\n", " ").replace("|", "/") for cell in cells]
    return "| " + " | ".join(safe_cells) + " |"


def _must_track_rows(report: dict[str, Any], evidence_pack: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows = _as_list((evidence_pack or {}).get("enhanced_must_track_indicators"))
    if not rows:
        rows = _as_list(report.get("must_track_analysis"))
    return [row for row in rows if isinstance(row, dict)]


def render_ai_report_markdown(
    report: dict[str, Any],
    evidence_pack: dict[str, Any] | None = None,
    fundamental: dict[str, Any] | None = None,
) -> str:
    stock = _stock(report, evidence_pack, fundamental)
    quality = detect_garbled_text(report)
    summary = _safe_text(report.get("executive_summary"), _summary_fallback(stock, report, evidence_pack))
    final_summary = _safe_text(report.get("final_summary"), summary)

    lines = [
        f"# {stock['code']} AI 基本面报告",
        "",
        "## 摘要",
        "",
        summary,
        "",
        "## 结论",
        "",
        f"- strategy_type: {stock['strategy_type'] or '-'}",
        f"- fundamental_view: {report.get('fundamental_view') or '-'}",
        f"- status: {stock['status'] or '-'}",
        f"- confidence: {stock['confidence'] or '-'}",
        f"- score: {_display_value(stock['score'])}",
    ]
    if quality["garbled_text_detected"]:
        lines.extend(["", f"> WARNING: {GARBLED_TEXT_WARNING}"])
    if stock["strategy_type"] == "satellite_communication_infrastructure":
        lines.extend(
            [
                "- 合同负债只能作为订单可见度 proxy，不等同真实 backlog。",
                "- capex 只能作为长期资产购建现金支出，不等同新增容量确定释放。",
                "- PE/PB/PS 不能单独作为估值充分依据。",
            ]
        )

    lines.extend(["", "## 置信度拆解", ""])
    confidence_rows = _as_list(report.get("confidence_breakdown")) or _as_list(
        (evidence_pack or {}).get("confidence_basis", {}).get("confidence_breakdown")
    )
    if confidence_rows:
        lines.extend(
            [
                _table_row(["维度", "等级", "原因"]),
                _table_row(["---", "---", "---"]),
            ]
        )
        for row in confidence_rows:
            if isinstance(row, dict):
                lines.append(_table_row([row.get("dimension"), row.get("level"), row.get("reason")]))
    else:
        lines.append("- 暂无置信度拆解。")

    lines.extend(["", "## Must-Track Indicators", ""])
    rows = _must_track_rows(report, evidence_pack)
    if rows:
        lines.extend(
            [
                _table_row(["指标", "当前状态", "当前值", "优先级", "为什么重要", "后续问题"]),
                _table_row(["---", "---", "---", "---", "---", "---"]),
            ]
        )
        for row in rows:
            lines.append(
                _table_row(
                    [
                        row.get("indicator_name"),
                        row.get("current_status"),
                        _display_value(row.get("current_value")),
                        row.get("priority"),
                        row.get("why_it_matters"),
                        row.get("follow_up_question"),
                    ]
                )
            )
    else:
        lines.append("- 暂无 must-track 指标。")

    lines.extend(["", "## 分析摘要", ""])
    for title, key in [
        ("业务分析", "business_analysis"),
        ("财务质量", "financial_quality_analysis"),
        ("估值分析", "valuation_analysis"),
        ("行业周期", "industry_cycle_analysis"),
    ]:
        lines.extend(["", f"### {title}", "", _safe_text(report.get(key), _analysis_fallback(key, stock))])

    lines.extend(["", "## 数据限制", ""])
    limitations = _as_list(report.get("data_limitations")) or _as_list((evidence_pack or {}).get("data_limitations"))
    for item in limitations[:20]:
        lines.append(f"- {_display_value(item)}")
    if not limitations:
        lines.append("- 暂无额外数据限制。")

    lines.extend(["", "## 最终摘要", "", final_summary, ""])
    return "\n".join(lines)


def write_ai_report_markdown(
    report: dict[str, Any],
    output_path: str | Path,
    evidence_pack: dict[str, Any] | None = None,
    fundamental: dict[str, Any] | None = None,
) -> str:
    markdown = render_ai_report_markdown(report, evidence_pack=evidence_pack, fundamental=fundamental)
    Path(output_path).write_text(markdown, encoding="utf-8")
    return markdown


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def normalize_stock_code(code: Any) -> str:
    digits = "".join(ch for ch in str(code or "") if ch.isdigit())
    if len(digits) < 6:
        raise ValueError("stock code must contain 6 digits")
    return digits[-6:]


def render_from_output(code: str, output_dir: str | Path | None = None) -> str:
    normalized = normalize_stock_code(code)
    directory = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    report_path = directory / f"ai_report_{normalized}.json"
    evidence_path = directory / f"evidence_pack_{normalized}.json"
    fundamental_path = directory / f"fundamental_{normalized}.json"
    markdown_path = directory / f"ai_report_{normalized}.md"
    report = _load_json(report_path)
    if report is None:
        raise FileNotFoundError(f"AI report JSON not found: {report_path}")
    return write_ai_report_markdown(
        report,
        markdown_path,
        evidence_pack=_load_json(evidence_path),
        fundamental=_load_json(fundamental_path),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Render AI report JSON to UTF-8 Markdown.")
    parser.add_argument("--code", required=True, help="6 digit A-share stock code")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory containing AI report JSON")
    args = parser.parse_args()
    try:
        render_from_output(args.code, args.output_dir)
    except Exception as exc:
        print(str(exc))
        return 1
    print(f"ai_report_markdown: {Path(args.output_dir) / f'ai_report_{normalize_stock_code(args.code)}.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
