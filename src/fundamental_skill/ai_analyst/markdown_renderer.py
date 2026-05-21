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

from src.fundamental_skill import dashboard_helpers as dashboard
from .report_schema import validate_ai_report
from .safety import detect_garbled_text, is_garbled_text


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"
GARBLED_TEXT_WARNING = "AI 自由文本损坏：部分字段命中乱码检测，当前报告使用结构化 evidence fallback 生成。"


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
        "sub_type": evidence_stock.get("sub_type") or (fundamental or {}).get("sub_type"),
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
    consistency_status: dict[str, Any] | None = None,
) -> str:
    stock = _stock(report, evidence_pack, fundamental)
    quality = detect_garbled_text(report)
    schema_status = validate_ai_report(report)
    consistency = consistency_status or dashboard.report_consistency_status(report, evidence_pack, fundamental)
    summary = _safe_text(report.get("executive_summary"), _summary_fallback(stock, report, evidence_pack))
    final_summary = _safe_text(report.get("final_summary"), summary)
    conclusion = dashboard.conclusion_summary(fundamental, report, consistency)
    primary_summary = conclusion["primary"] if conclusion["primary"] != "-" else summary
    evidence_source = evidence_pack or report
    supporting = dashboard.evidence_card_rows(evidence_source, "supporting_evidence")
    limiting = dashboard.evidence_card_rows(evidence_source, "limiting_evidence")
    missing = dashboard.evidence_card_rows(evidence_source, "unknown_or_missing_evidence")

    lines = [
        f"# {stock['code']} {stock['name']} AI基本面分析报告",
        "",
        "## 一句话结论",
        "",
        primary_summary,
        "",
        f"> {dashboard.CONFIDENCE_EXPLANATION}",
        "",
        "## 公司身份与分析框架",
        "",
        f"- 股票代码：{stock['code'] or '-'}",
        f"- 公司名称：{stock['name'] or '-'}",
        f"- 分析框架：{dashboard.format_strategy_type(stock['strategy_type'])}",
        f"- 子类型：{dashboard.format_sub_type(stock.get('sub_type'))}",
        f"- 规则基本面状态：{dashboard.status_label(stock['status'])}",
        f"- AI基本面观点：{dashboard.ai_view_label(report.get('fundamental_view'))}",
        f"- 证据置信度：{dashboard.confidence_label(stock['confidence'])}",
        f"- 基本面评分：{_display_value(stock['score'])}",
        "",
        "## 结论速览",
        "",
    ]
    for item in dashboard.why_conclusion_bullets(fundamental, evidence_pack, report):
        lines.append(f"- {item}")

    lines.extend(["", "## 状态与置信度解释", ""])
    lines.append(f"- 当前状态：{dashboard.status_label(stock['status'])}")
    lines.append(f"- 当前置信度：{dashboard.confidence_label(stock['confidence'])}")
    lines.append(f"- {dashboard.CONFIDENCE_EXPLANATION}")

    if consistency.get("status") in {"stale", "mismatch"}:
        lines.extend(["", f"> 报告过期 / 不一致：{'；'.join(consistency.get('warnings') or [])}"])
    elif not consistency.get("can_use_ai_body", True):
        lines.extend(["", f"> 报告状态：{consistency.get('label') or '未通过'}"])
    if quality["garbled_text_detected"]:
        lines.extend(["", f"> {GARBLED_TEXT_WARNING}"])
    if schema_status.get("schema_errors"):
        lines.extend(["", "> schema / safety 不通过：结构校验未通过，AI 正文不能作为可信主报告。"])
    elif not schema_status.get("safety", {}).get("safe", True):
        lines.extend(["", "> schema / safety 不通过：安全校验未通过，AI 正文不能作为可信主报告。"])

    lines.extend(["", "## 证据地图", "", "### 支持证据", ""])
    for row in supporting[:8]:
        lines.append(f"- {row.get('证据') or '-'}：{row.get('为什么重要') or '-'}")
    if not supporting:
        lines.append("- 暂无结构化支持证据。")
    lines.extend(["", "### 限制因素", ""])
    for row in limiting[:8]:
        lines.append(f"- {row.get('证据') or '-'}：{row.get('为什么重要') or '-'}")
    if not limiting:
        lines.append("- 暂无结构化限制因素。")
    lines.extend(["", "### 缺失证据", ""])
    for row in missing[:10]:
        lines.append(f"- {row.get('证据') or '-'}：{row.get('为什么重要') or '-'}")
    if not missing:
        lines.append("- 暂无结构化缺失证据。")

    lines.extend(["", "## 行业框架检查", ""])
    lines.append(f"- strategy_type：{stock['strategy_type'] or '-'}")
    lines.append(f"- 中文解释：{dashboard.strategy_type_label(stock['strategy_type'])}")
    lines.append(f"- sub_type：{stock.get('sub_type') or '不适用'}")
    lines.append(f"- 中文解释：{dashboard.sub_type_label(stock.get('sub_type'))}")
    if stock["strategy_type"] == "satellite_communication_infrastructure":
        lines.append("- 合同负债只能作为订单可见度 proxy，不等同真实 backlog。")
        lines.append("- capex 只能作为长期资产购建现金支出，不等同新增容量确定释放。")
        lines.append("- PE/PB/PS 不能单独作为估值充分依据。")

    lines.extend(["", "## 必须跟踪指标", ""])
    rows = dashboard.ai_must_track_rows_cn(report, evidence_pack, include_low=False)
    if rows:
        lines.extend(
            [
                _table_row(["指标", "状态", "优先级", "当前值", "为什么重要", "下一步需要验证的证据"]),
                _table_row(["---", "---", "---", "---", "---", "---"]),
            ]
        )
        for row in rows:
            lines.append(
                _table_row(
                    [
                        row.get("指标"),
                        row.get("状态"),
                        row.get("优先级"),
                        row.get("当前值"),
                        row.get("为什么重要"),
                        row.get("下一步需要验证的证据"),
                    ]
                )
            )
    else:
        lines.append("- 暂无 high / medium 优先级必须跟踪指标。")

    lines.extend(["", "## 风险提示", ""])
    risks = dashboard.risk_cards(fundamental, evidence_pack, report)
    if risks:
        for row in risks[:10]:
            lines.append(f"- {row.get('风险') or '-'}｜严重程度：{row.get('严重程度') or '-'}｜说明：{row.get('说明') or '-'}")
    else:
        notice = dashboard.risk_gap_notice(fundamental, evidence_pack, report)
        lines.append(f"- {notice or '暂无结构化风险项；仍需结合证据缺口理解未识别风险。'}")

    lines.extend(["", "## 后续复核条件", ""])
    for item in _as_list(report.get("invalidation_watch")) or _as_list((evidence_pack or {}).get("invalidation_conditions")):
        if isinstance(item, dict):
            hint = item.get("downstream_review_hint") or item.get("action_hint_for_trader")
            lines.append(f"- {item.get('condition') or '-'}：需要验证 {item.get('evidence_needed') or '-'}；{dashboard.neutralize_legacy_review_text(hint) or '需要后续复核'}")

    lines.extend(["", "## 数据质量与来源限制", ""])
    limitations = _as_list(report.get("data_limitations")) or _as_list((evidence_pack or {}).get("data_limitations"))
    for item in limitations[:20]:
        lines.append(f"- {_display_value(item)}")
    if not limitations:
        lines.append("- 暂无额外数据限制。")

    lines.extend(["", "## 安全边界说明", ""])
    lines.append("本报告仅用于 A 股基本面研究展示与审计，不提供交易建议，不提供目标价，不提供仓位建议，不使用技术面图表，不连接交易账户。")
    lines.extend(["", "<!-- final_summary fallback -->", final_summary, ""])
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
