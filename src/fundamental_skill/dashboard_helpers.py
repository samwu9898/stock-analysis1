# -*- coding: utf-8 -*-
"""Helpers for the local fundamental Streamlit dashboard.

The helpers only reshape existing JSON results for display. They do not run
analysis, alter pipeline rules, or create downstream action guidance.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .ai_analyst.report_schema import validate_ai_report
from .ai_analyst.safety import check_text_safety, detect_garbled_text, is_garbled_text


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"
CONFIDENCE_EXPLANATION = "置信度表示对当前基本面结论的证据置信度，不等于看好程度。"

STRATEGY_TYPE_LABELS = {
    "satellite_communication_infrastructure": "卫星通信基础设施",
    "low_altitude_economy_infrastructure": "低空经济基础设施 / 运营服务",
    "life_science_cxo_services": "CXO 医药外包服务",
    "advanced_manufacturing_growth": "高端制造成长",
    "semiconductor_cycle": "半导体周期",
    "resource_swing": "资源弹性",
    "resource_core": "资源核心",
    "right_trend_growth": "高景气成长",
    "stable_growth": "稳健成长",
    "theme_only": "题材型",
    "unknown": "未知 / 暂无法归类",
}

SUB_TYPE_LABELS = {
    "aviation_operations_service": "通航 / 低空飞行运营服务",
    "airspace_platform_system": "空域平台 / 调度系统",
    "integrated_cxo_platform": "综合 CXO 平台",
    "cdmo_manufacturing_services": "CDMO 生产制造服务",
    "clinical_cro_services": "临床 CRO 服务",
}

STATUS_LABELS = {
    "supportive": "基本面支持进一步研究",
    "neutral": "中性，需要更多证据",
    "negative": "基本面不支持",
    "insufficient_data": "数据不足，无法可靠判断",
}

AI_VIEW_LABELS = {
    "supportive_for_further_evaluation": "AI 观点：支持进一步研究",
    "neutral_requires_more_evidence": "AI 观点：中性，需要更多证据",
    "not_supportive": "AI 观点：不支持",
    "insufficient_data": "AI 观点：数据不足",
}

CONFIDENCE_LABELS = {
    "high": "高证据置信度",
    "medium": "中等证据置信度",
    "low": "低证据置信度",
}

CONFIDENCE_DIMENSION_LABELS = {
    "data_coverage": "数据覆盖",
    "financial_quality": "财务质量",
    "valuation_interpretability": "估值可解释性",
    "growth_validation": "成长 / 框架验证",
    "risk_identifiability": "风险可识别性",
}

STATUS_TO_AI_VIEW = {
    "supportive": "supportive_for_further_evaluation",
    "neutral": "neutral_requires_more_evidence",
    "negative": "not_supportive",
    "insufficient_data": "insufficient_data",
}

FORBIDDEN_TRADING_TERMS = (
    "买入",
    "卖出",
    "加仓",
    "减仓",
    "清仓",
    "止损",
    "止盈",
    "目标价",
    "满仓",
    "梭哈",
)

MOJIBAKE_FORBIDDEN_TRADING_TERMS = (
    "涔板叆",
    "鍗栧嚭",
    "鍔犱粨",
    "鍑忎粨",
    "娓呬粨",
    "姝㈡崯",
    "姝㈢泩",
    "鐩爣浠",
    "婊′粨",
    "姊搱",
)


def project_root() -> Path:
    return PROJECT_ROOT


def output_dir(path: str | Path | None = None) -> Path:
    return Path(path) if path is not None else DEFAULT_OUTPUT_DIR


def fundamental_path(stock_code: str, output_directory: str | Path | None = None) -> Path:
    return output_dir(output_directory) / f"fundamental_{normalize_stock_code(stock_code)}.json"


def raw_path(stock_code: str, output_directory: str | Path | None = None) -> Path:
    return output_dir(output_directory) / f"raw_{normalize_stock_code(stock_code)}.json"


def ai_report_path(stock_code: str, output_directory: str | Path | None = None) -> Path:
    return output_dir(output_directory) / f"ai_report_{normalize_stock_code(stock_code)}.json"


def ai_report_markdown_path(stock_code: str, output_directory: str | Path | None = None) -> Path:
    return output_dir(output_directory) / f"ai_report_{normalize_stock_code(stock_code)}.md"


def evidence_pack_path(stock_code: str, output_directory: str | Path | None = None) -> Path:
    return output_dir(output_directory) / f"evidence_pack_{normalize_stock_code(stock_code)}.json"


def ai_prompt_path(stock_code: str, output_directory: str | Path | None = None) -> Path:
    return output_dir(output_directory) / f"ai_prompt_{normalize_stock_code(stock_code)}.md"


def normalize_stock_code(stock_code: Any) -> str:
    digits = "".join(ch for ch in str(stock_code or "") if ch.isdigit())
    return digits[-6:] if len(digits) >= 6 else digits


def load_json_file(path: str | Path) -> dict[str, Any] | None:
    file_path = Path(path)
    if not file_path.exists():
        return None
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def load_text_file(path: str | Path) -> str | None:
    file_path = Path(path)
    if not file_path.exists():
        return None
    try:
        return file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def load_result_pair(
    stock_code: str,
    output_directory: str | Path | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    code = normalize_stock_code(stock_code)
    return load_json_file(fundamental_path(code, output_directory)), load_json_file(raw_path(code, output_directory))


def load_ai_bundle(
    stock_code: str,
    output_directory: str | Path | None = None,
) -> dict[str, Any]:
    code = normalize_stock_code(stock_code)
    return {
        "stock_code": code,
        "ai_report": load_json_file(ai_report_path(code, output_directory)),
        "ai_report_markdown": load_text_file(ai_report_markdown_path(code, output_directory)),
        "evidence_pack": load_json_file(evidence_pack_path(code, output_directory)),
        "ai_prompt": load_text_file(ai_prompt_path(code, output_directory)),
        "fundamental": load_json_file(fundamental_path(code, output_directory)),
        "raw": load_json_file(raw_path(code, output_directory)),
        "paths": {
            "ai_report": str(ai_report_path(code, output_directory)),
            "ai_report_markdown": str(ai_report_markdown_path(code, output_directory)),
            "evidence_pack": str(evidence_pack_path(code, output_directory)),
            "ai_prompt": str(ai_prompt_path(code, output_directory)),
            "fundamental": str(fundamental_path(code, output_directory)),
            "raw": str(raw_path(code, output_directory)),
        },
    }


def scan_fundamental_results(output_directory: str | Path | None = None) -> list[dict[str, Any]]:
    directory = output_dir(output_directory)
    if not directory.exists():
        return []

    rows = []
    for path in sorted(directory.glob("fundamental_*.json")):
        payload = load_json_file(path)
        if payload is None:
            continue
        rows.append(summary_row(payload, source_path=path))
    return rows


def scan_ai_reports(output_directory: str | Path | None = None) -> list[dict[str, Any]]:
    directory = output_dir(output_directory)
    if not directory.exists():
        return []
    rows = []
    for path in sorted(directory.glob("ai_report_*.json")):
        payload = load_json_file(path)
        if payload is None:
            continue
        rows.append(ai_report_summary_row(payload, source_path=path))
    return rows


def scan_available_stocks(output_directory: str | Path | None = None) -> list[dict[str, Any]]:
    by_code: dict[str, dict[str, Any]] = {}
    for row in scan_fundamental_results(output_directory):
        code = str(row.get("stock_code") or "")
        if not code:
            continue
        by_code.setdefault(code, {}).update(row)
        by_code[code]["has_fundamental"] = True
        by_code[code].setdefault("has_ai_report", False)
    for row in scan_ai_reports(output_directory):
        code = str(row.get("stock_code") or "")
        if not code:
            continue
        existing = by_code.setdefault(code, {"stock_code": code})
        existing.update({key: value for key, value in row.items() if value not in (None, "")})
        existing["has_ai_report"] = True
        existing.setdefault("has_fundamental", False)
    return sorted(by_code.values(), key=lambda item: (not item.get("has_ai_report"), str(item.get("stock_code"))))


def summary_row(payload: dict[str, Any], source_path: str | Path | None = None) -> dict[str, Any]:
    missing_fields = as_list(payload.get("missing_fields"))
    risk_flags = as_list(payload.get("risk_flags"))
    indicators = as_list(payload.get("must_track_indicators"))
    return {
        "stock_code": payload.get("stock_code") or code_from_path(source_path),
        "stock_name": payload.get("stock_name"),
        "strategy_type": payload.get("strategy_type"),
        "status": payload.get("status"),
        "confidence": payload.get("confidence"),
        "fundamental_score": payload.get("fundamental_score"),
        "analyst_summary": fundamental_analyst_summary(payload),
        "risk_flags_count": len(risk_flags),
        "must_track_indicators_count": len(indicators),
        "missing_fields_count": len(missing_fields),
        "generated_at_or_as_of": (
            payload.get("generated_at")
            or payload.get("as_of")
            or payload.get("analysis_date")
            or payload.get("data_timestamp")
        ),
        "path": str(source_path) if source_path else None,
    }


def strategy_type_label(strategy_type: Any) -> str:
    value = str(strategy_type or "")
    return STRATEGY_TYPE_LABELS.get(value, "未知 / 暂无法归类")


def sub_type_label(sub_type: Any) -> str:
    value = str(sub_type or "")
    if not value:
        return "不适用"
    return SUB_TYPE_LABELS.get(value, "未识别子类型")


def status_label(status: Any) -> str:
    value = str(status or "")
    return STATUS_LABELS.get(value, value or "-")


def ai_view_label(view: Any) -> str:
    value = str(view or "")
    return AI_VIEW_LABELS.get(value, value or "-")


def confidence_label(confidence: Any) -> str:
    value = str(confidence or "")
    return CONFIDENCE_LABELS.get(value, value or "-")


def format_strategy_type(strategy_type: Any) -> str:
    value = str(strategy_type or "")
    return f"{value}（{strategy_type_label(value)}）" if value else "未知 / 暂无法归类"


def format_sub_type(sub_type: Any) -> str:
    value = str(sub_type or "")
    return f"{value}（{sub_type_label(value)}）" if value else "不适用"


def evidence_stock(evidence_pack: dict[str, Any] | None) -> dict[str, Any]:
    stock = (evidence_pack or {}).get("stock")
    return stock if isinstance(stock, dict) else {}


def current_stock_snapshot(
    fundamental: dict[str, Any] | None,
    evidence_pack: dict[str, Any] | None,
    ai_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    stock = evidence_stock(evidence_pack)
    return {
        "stock_code": stock.get("code") or (fundamental or {}).get("stock_code") or (ai_report or {}).get("stock_code"),
        "stock_name": stock.get("name") or (fundamental or {}).get("stock_name") or (ai_report or {}).get("stock_name"),
        "strategy_type": stock.get("strategy_type") or (fundamental or {}).get("strategy_type"),
        "sub_type": stock.get("sub_type") or (fundamental or {}).get("sub_type"),
        "status": stock.get("status") or (fundamental or {}).get("status"),
        "confidence": stock.get("confidence") or (fundamental or {}).get("confidence"),
        "fundamental_score": stock.get("fundamental_score") or (fundamental or {}).get("fundamental_score"),
    }


def report_consistency_status(
    ai_report: dict[str, Any] | None,
    evidence_pack: dict[str, Any] | None,
    fundamental: dict[str, Any] | None,
    ai_report_markdown: str | None = None,
    paths: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if ai_report is None:
        return {"status": "missing", "label": "尚无 AI 报告", "warnings": ["尚无 AI 报告。"], "can_use_ai_body": False}

    current = current_stock_snapshot(fundamental, evidence_pack, ai_report)
    warnings: list[str] = []
    status = "ok"

    ai_code = normalize_stock_code(ai_report.get("stock_code"))
    current_code = normalize_stock_code(current.get("stock_code"))
    if ai_code and current_code and ai_code != current_code:
        status = "mismatch"
        warnings.append(f"股票代码不一致：AI report 为 {ai_code}，当前数据为 {current_code}。")

    expected_view = STATUS_TO_AI_VIEW.get(str(current.get("status") or ""))
    ai_view = ai_report.get("fundamental_view")
    if expected_view and ai_view and ai_view != expected_view:
        status = "mismatch"
        warnings.append(
            f"状态不一致：规则基本面状态为 {status_label(current.get('status'))}，AI 基本面观点为 {ai_view_label(ai_view)}。"
        )

    text = stringify_payload(ai_report) + "\n" + (ai_report_markdown or "")
    strategy = str(current.get("strategy_type") or "")
    sub_type = str(current.get("sub_type") or "")
    if strategy and strategy != "unknown":
        stale_strategy_markers = [
            "strategy_type is unknown",
            "strategy_type 为 unknown",
            "strategy_type: unknown",
            "current strategy_type is unknown",
            "No dedicated CXO",
        ]
        if any(marker in text for marker in stale_strategy_markers):
            status = "mismatch"
            warnings.append(
                f"分析框架不一致：当前数据为 {format_strategy_type(strategy)}，但 AI report 仍包含旧的 unknown/框架缺口描述。"
            )
    if sub_type and sub_type not in text and "unknown" in text:
        status = "mismatch"
        warnings.append(f"子类型不一致：当前数据为 {format_sub_type(sub_type)}，AI report 未体现该子类型并包含 unknown 描述。")

    path_map = paths or {}
    ai_path = Path(path_map.get("ai_report", "")) if path_map.get("ai_report") else None
    reference_paths = [
        Path(path_map[name])
        for name in ("fundamental", "evidence_pack")
        if path_map.get(name)
    ]
    try:
        if ai_path and ai_path.exists():
            ai_mtime = ai_path.stat().st_mtime
            newer_refs = [path.name for path in reference_paths if path.exists() and path.stat().st_mtime > ai_mtime + 1]
            if newer_refs and status == "ok":
                status = "stale"
            if newer_refs:
                warnings.append(f"AI report 文件早于当前数据文件：{', '.join(newer_refs)}。")
    except OSError:
        pass

    label_map = {
        "ok": "报告正常",
        "missing": "尚无 AI 报告",
        "stale": "报告过期",
        "mismatch": "报告不一致",
    }
    if status in {"stale", "mismatch"}:
        warnings.insert(0, "报告过期 / 报告与当前数据不一致，请重新生成 AI report。")
    return {"status": status, "label": label_map.get(status, status), "warnings": warnings, "can_use_ai_body": status == "ok"}


def neutralize_legacy_review_text(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    replacements = {
        "进入交易员 Agent 后续评估": "进入后续综合评估",
        "需要交易员重新评估": "需要后续分析层复核",
        "交给交易员进一步评估": "进入后续综合评估",
        "交易员进一步评估": "后续模块评估",
        "交易员 Agent": "后续分析层",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def fundamental_analyst_summary(fundamental: dict[str, Any] | None) -> str | None:
    value = (fundamental or {}).get("analyst_summary") or (fundamental or {}).get("trader_summary")
    return neutralize_legacy_review_text(value)


def invalidation_condition_rows(fundamental: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows = []
    for item in as_list((fundamental or {}).get("invalidation_conditions")):
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "condition": item.get("condition"),
                "evidence_needed": item.get("evidence_needed"),
                "downstream_review_hint": neutralize_legacy_review_text(
                    item.get("downstream_review_hint") or item.get("action_hint_for_trader")
                ),
            }
        )
    return rows


def ai_report_summary_row(payload: dict[str, Any], source_path: str | Path | None = None) -> dict[str, Any]:
    quality = detect_garbled_text(payload)
    return {
        "stock_code": payload.get("stock_code") or code_from_path(source_path, prefix="ai_report_"),
        "stock_name": payload.get("stock_name"),
        "fundamental_view": payload.get("fundamental_view"),
        "executive_summary": clean_ai_report_text(payload, "executive_summary"),
        "report_quality_status": quality["status"],
        "garbled_text_detected": quality["garbled_text_detected"],
        "confidence_breakdown_count": len(as_list(payload.get("confidence_breakdown"))),
        "supporting_evidence_count": len(as_list(payload.get("supporting_evidence"))),
        "limiting_evidence_count": len(as_list(payload.get("limiting_evidence"))),
        "unknown_evidence_count": len(as_list(payload.get("unknown_or_missing_evidence"))),
        "must_track_count": len(as_list(payload.get("must_track_analysis"))),
        "path": str(source_path) if source_path else None,
    }


def code_from_path(path: str | Path | None, prefix: str = "fundamental_") -> str | None:
    if path is None:
        return None
    stem = Path(path).stem
    return stem[len(prefix):] if stem.startswith(prefix) else None


def confidence_breakdown_rows(ai_report: dict[str, Any] | None, evidence_pack: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    rows = as_list((ai_report or {}).get("confidence_breakdown"))
    if not rows:
        rows = as_list((evidence_pack or {}).get("confidence_basis", {}).get("confidence_breakdown"))
    output = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        dimension = row.get("dimension")
        output.append(
            {
                "维度": CONFIDENCE_DIMENSION_LABELS.get(str(dimension), str(dimension or "-")),
                "状态": row.get("level"),
                "原因": row.get("reason"),
            }
        )
    return output


def evidence_rows(payload: dict[str, Any] | None, section: str) -> list[dict[str, Any]]:
    fields = [
        "evidence_name",
        "evidence_value",
        "why_it_matters",
        "affects_dimension",
        "source",
        "confidence_effect",
    ]
    return [pick_fields(row, fields) for row in as_list((payload or {}).get(section)) if isinstance(row, dict)]


def evidence_card_rows(payload: dict[str, Any] | None, section: str) -> list[dict[str, Any]]:
    rows = []
    for row in as_list((payload or {}).get(section)):
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "证据": row.get("evidence_name"),
                "当前值": display_value(row.get("evidence_value")),
                "为什么重要": row.get("why_it_matters"),
                "影响维度": CONFIDENCE_DIMENSION_LABELS.get(str(row.get("affects_dimension")), row.get("affects_dimension")),
                "来源": row.get("source"),
                "对置信度的影响": row.get("confidence_effect"),
            }
        )
    if not rows and section == "unknown_or_missing_evidence":
        missing_rows = as_list((payload or {}).get("missing_fields")) or as_list(
            (payload or {}).get("confidence_basis", {}).get("missing_fields")
        )
        for row in missing_rows:
            if isinstance(row, dict):
                rows.append(
                    {
                        "证据": row.get("field"),
                        "当前值": None,
                        "为什么重要": row.get("explanation"),
                        "影响维度": "数据覆盖",
                        "来源": "missing_fields",
                        "对置信度的影响": "unknown_or_limits_confidence",
                    }
                )
            else:
                rows.append(
                    {
                        "证据": row,
                        "当前值": None,
                        "为什么重要": "该字段缺失，相关基本面维度不足以判断。",
                        "影响维度": "数据覆盖",
                        "来源": "missing_fields",
                        "对置信度的影响": "unknown_or_limits_confidence",
                    }
                )
    return rows


def ai_must_track_rows(ai_report: dict[str, Any] | None, evidence_pack: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    source_rows = as_list((evidence_pack or {}).get("enhanced_must_track_indicators"))
    if not source_rows:
        source_rows = as_list((ai_report or {}).get("must_track_analysis"))
    rows = []
    for item in source_rows:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "indicator_name": item.get("indicator_name"),
                "priority": item.get("priority"),
                "current_value": display_value(item.get("current_value")),
                "current_status": item.get("current_status"),
                "why_it_matters": item.get("why_it_matters") or item.get("analysis"),
                "source": item.get("source"),
                "source_date": item.get("source_date"),
                "related_risk": item.get("related_risk"),
                "affects_dimension": item.get("affects_dimension"),
                "follow_up_question": item.get("follow_up_question"),
            }
        )
    return sorted(rows, key=lambda row: priority_rank(row.get("priority")))


def ai_must_track_rows_cn(
    ai_report: dict[str, Any] | None,
    evidence_pack: dict[str, Any] | None = None,
    include_low: bool = True,
) -> list[dict[str, Any]]:
    rows = []
    for row in ai_must_track_rows(ai_report, evidence_pack):
        if not include_low and row.get("priority") == "low":
            continue
        rows.append(
            {
                "指标": row.get("indicator_name"),
                "状态": row.get("current_status"),
                "优先级": row.get("priority"),
                "当前值": row.get("current_value"),
                "为什么重要": row.get("why_it_matters"),
                "下一步需要验证的证据": row.get("follow_up_question"),
            }
        )
    return rows


def high_priority_missing_evidence(evidence_pack: dict[str, Any] | None, ai_report: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    missing = []
    for row in ai_must_track_rows(ai_report, evidence_pack):
        priority = str(row.get("priority") or "")
        status = str(row.get("current_status") or "")
        if priority in {"high", "medium"} and ("missing" in status or row.get("current_value") in (None, "")):
            missing.append(row)
    return missing


def risk_gap_notice(fundamental: dict[str, Any] | None, evidence_pack: dict[str, Any] | None, ai_report: dict[str, Any] | None = None) -> str | None:
    risks = as_list((evidence_pack or {}).get("risk_flags")) or as_list((fundamental or {}).get("risk_flags"))
    gaps = high_priority_missing_evidence(evidence_pack, ai_report)
    if not gaps:
        missing_cards = evidence_card_rows(evidence_pack or ai_report, "unknown_or_missing_evidence")
        if len(missing_cards) >= 5:
            gaps = [{"indicator_name": row.get("证据"), "priority": "high", "current_status": "missing"} for row in missing_cards]
    if risks or not gaps:
        return None
    return "当前结构化风险项为 0，但仍存在高/中优先级证据缺口；这表示风险尚未被充分识别或量化，不表示没有风险。"


def risk_cards(fundamental: dict[str, Any] | None, evidence_pack: dict[str, Any] | None, ai_report: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    source = as_list((evidence_pack or {}).get("risk_flags")) or as_list((fundamental or {}).get("risk_flags")) or as_list((ai_report or {}).get("risk_analysis"))
    rows = []
    for item in source:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "风险": item.get("risk_name") or item.get("name"),
                "严重程度": item.get("severity"),
                "说明": item.get("reason") or item.get("analysis") or item.get("monitor_method"),
                "证据依据": summarize_evidence(item.get("evidence")),
            }
        )
    return sorted(rows, key=lambda row: {"high": 0, "medium": 1, "low": 2}.get(str(row.get("严重程度")), 3))


def conclusion_summary(
    fundamental: dict[str, Any] | None,
    ai_report: dict[str, Any] | None,
    consistency: dict[str, Any] | None = None,
) -> dict[str, Any]:
    analyst = fundamental_analyst_summary(fundamental)
    can_use_ai = bool((consistency or {}).get("can_use_ai_body", True))
    executive = clean_ai_report_text(ai_report, "executive_summary") if can_use_ai else None
    return {"primary": analyst or executive or "-", "ai_auxiliary": executive if analyst and executive else None}


def why_conclusion_bullets(
    fundamental: dict[str, Any] | None,
    evidence_pack: dict[str, Any] | None,
    ai_report: dict[str, Any] | None = None,
) -> list[str]:
    current = current_stock_snapshot(fundamental, evidence_pack, ai_report)
    bullets = [
        f"规则基本面状态为{status_label(current.get('status'))}，来自确定性 pipeline 的当前证据组合。",
        f"证据置信度为{confidence_label(current.get('confidence'))}；{CONFIDENCE_EXPLANATION}",
    ]
    supporting = evidence_card_rows(evidence_pack or ai_report, "supporting_evidence")
    limiting = evidence_card_rows(evidence_pack or ai_report, "limiting_evidence")
    missing = evidence_card_rows(evidence_pack or ai_report, "unknown_or_missing_evidence")
    if supporting:
        bullets.append("支持证据包括：" + "、".join(str(row.get("证据")) for row in supporting[:2] if row.get("证据")) + "。")
    if limiting:
        bullets.append("限制因素包括：" + "、".join(str(row.get("证据")) for row in limiting[:2] if row.get("证据")) + "。")
    gaps = [row.get("证据") for row in missing[:3] if row.get("证据")]
    if gaps:
        bullets.append("阻止高置信度的关键缺口包括：" + "、".join(str(item) for item in gaps) + "。")
    return [bullet for bullet in bullets if bullet and not bullet.endswith("：。")][:5]


def data_quality_view(
    fundamental: dict[str, Any] | None,
    evidence_pack: dict[str, Any] | None,
    raw: dict[str, Any] | None,
    consistency: dict[str, Any] | None = None,
) -> dict[str, Any]:
    missing = as_list((evidence_pack or {}).get("missing_fields")) or as_list((fundamental or {}).get("missing_fields"))
    fetch_rows = fetch_status_rows(raw)
    news_failures = [row for row in fetch_rows if row.get("block_name") == "news" and not row.get("success")]
    source_gaps = as_list((evidence_pack or {}).get("data_limitations"))
    return {
        "缺失字段数量": len(missing),
        "新闻源失败": "是" if news_failures else "否",
        "数据源缺口": len(source_gaps),
        "报告质量提示": (consistency or {}).get("label") or "未检查",
    }


def priority_rank(priority: Any) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(str(priority), 3)


def display_value(value: Any) -> Any:
    if isinstance(value, dict):
        if "display_value" in value:
            return value.get("display_value")
        if "raw_value" in value:
            return value.get("raw_value")
        return stringify_payload(value)
    if isinstance(value, list):
        parts = []
        for item in value[:6]:
            if isinstance(item, dict):
                name = item.get("commodity_name") or item.get("segment_name") or item.get("indicator_name")
                val = item.get("price") if item.get("price") is not None else display_value(item.get("revenue_ratio"))
                pieces = [str(piece) for piece in (name, val) if piece not in (None, "")]
                parts.append(": ".join(pieces) if pieces else stringify_payload(item))
            else:
                parts.append(str(item))
        return "; ".join(parts)
    return value


def ai_report_status(
    ai_report: dict[str, Any] | None,
    ai_report_markdown: str | None = None,
) -> dict[str, Any]:
    if ai_report is None:
        return {
            "schema_valid": False,
            "schema_errors": ["ai_report_missing"],
            "safety_safe": True,
            "restricted_terms_count": 0,
            "violations": [],
            "report_quality_status": "missing",
            "garbled_text_detected": False,
            "quality_warnings": [],
            "garbled_text_findings": [],
            "can_display_body": False,
        }
    schema = validate_ai_report(ai_report)
    json_safety = schema.get("safety", {})
    md_safety = check_text_safety(ai_report_markdown or "", allow_policy_context=False)
    quality = schema.get("quality") or detect_garbled_text(ai_report)
    blocked_terms = sorted(set(as_list(json_safety.get("blocked_terms")) + as_list(md_safety.get("blocked_terms"))))
    violations = as_list(json_safety.get("violations")) + as_list(md_safety.get("violations"))
    schema_valid = bool(schema.get("valid")) and not schema.get("schema_errors")
    safety_safe = bool(json_safety.get("safe", True)) and bool(md_safety.get("safe", True))
    garbled = bool(quality.get("garbled_text_detected"))
    return {
        "schema_valid": schema_valid,
        "schema_errors": schema.get("schema_errors", []),
        "safety_safe": safety_safe,
        "restricted_terms_count": len(blocked_terms),
        "blocked_terms": blocked_terms,
        "violations": violations,
        "report_quality_status": quality.get("status", "ok"),
        "garbled_text_detected": garbled,
        "quality_warnings": as_list(quality.get("warnings")),
        "garbled_text_findings": as_list(quality.get("findings")),
        "can_display_body": schema_valid and safety_safe and not garbled,
    }


def clean_ai_report_text(ai_report: dict[str, Any] | None, field: str, fallback: str | None = None) -> str | None:
    value = (ai_report or {}).get(field)
    if value in (None, "") or is_garbled_text(value):
        return fallback
    return str(value)


def evidence_pack_summary(evidence_pack: dict[str, Any] | None) -> dict[str, Any]:
    pack = evidence_pack or {}
    confidence = pack.get("confidence_basis") if isinstance(pack.get("confidence_basis"), dict) else {}
    return {
        "evidence_pack_version": pack.get("evidence_pack_version"),
        "stock_code": (pack.get("stock") or {}).get("code") if isinstance(pack.get("stock"), dict) else None,
        "stock_name": (pack.get("stock") or {}).get("name") if isinstance(pack.get("stock"), dict) else None,
        "strategy_type": (pack.get("stock") or {}).get("strategy_type") if isinstance(pack.get("stock"), dict) else None,
        "status": confidence.get("status"),
        "confidence": confidence.get("confidence"),
        "score": confidence.get("score"),
        "risk_flags_count": confidence.get("risk_flags_count"),
    }


def prompt_preview(stock_code: str, output_directory: str | Path | None = None, max_chars: int = 4000) -> str | None:
    prompt = load_text_file(ai_prompt_path(stock_code, output_directory))
    if prompt is None:
        return None
    return prompt[:max_chars]


def risk_flag_rows(payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows = []
    for item in as_list((payload or {}).get("risk_flags")):
        if not isinstance(item, dict):
            continue
        evidence = item.get("evidence")
        rows.append(
            {
                "risk_name": item.get("risk_name") or item.get("name"),
                "severity": item.get("severity"),
                "reason": item.get("reason") or item.get("monitor_method"),
                "evidence": summarize_evidence(evidence),
            }
        )
    return rows


def must_track_indicator_rows(payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows = []
    for item in as_list((payload or {}).get("must_track_indicators")):
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "indicator_name": item.get("indicator_name") or item.get("name"),
                "current_value": item.get("current_value"),
                "source": item.get("source"),
                "date": item.get("date") or item.get("period"),
                "reason": item.get("reason"),
                "frequency": item.get("frequency") or item.get("monitor_frequency"),
            }
        )
    return rows


def financial_quality_row(fundamental: dict[str, Any] | None, raw: dict[str, Any] | None) -> dict[str, Any]:
    metrics = first_dict((raw or {}).get("blocks", {}).get("financial_indicator"))
    quality = (fundamental or {}).get("financial_quality")
    if not isinstance(quality, dict):
        quality = {}
    fields = [
        "revenue_yoy",
        "net_profit_yoy",
        "deducted_net_profit",
        "gross_margin",
        "net_margin",
        "roe",
        "operating_cashflow",
        "debt_to_asset",
        "inventory",
        "accounts_receivable",
    ]
    row = {field: metrics.get(field) for field in fields}
    row["quality_score"] = quality.get("score")
    return row


def valuation_row(fundamental: dict[str, Any] | None, raw: dict[str, Any] | None) -> dict[str, Any]:
    valuation = first_dict((raw or {}).get("blocks", {}).get("valuation"))
    fields = ["pe_ttm", "pb", "ps", "market_cap", "dividend_yield"]
    row = {field: valuation.get(field) for field in fields}
    view = (fundamental or {}).get("valuation_view")
    if isinstance(view, dict):
        row["valuation_level"] = view.get("valuation_level")
        row["valuation_score"] = view.get("score")
    return row


def business_composition_rows(
    raw: dict[str, Any] | None,
    fundamental: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    rows = extract_block_rows(raw, "business_composition")
    if not rows:
        rows = extract_block_rows(fundamental, "business_composition")
    fields = [
        "segment_name",
        "classification_type",
        "revenue",
        "revenue_ratio",
        "gross_margin",
        "cost",
        "profit",
        "period",
    ]
    return [pick_fields(row, fields) for row in rows if isinstance(row, dict)]


def commodity_price_rows(raw: dict[str, Any] | None) -> list[dict[str, Any]]:
    fields = [
        "commodity_name",
        "commodity_name_cn",
        "symbol",
        "price",
        "date",
        "market",
        "source_function",
        "source_priority",
        "freshness_days",
        "is_stale",
        "readiness_eligible",
        "warnings",
    ]
    return [pick_fields(row, fields) for row in extract_block_rows(raw, "commodity_prices")]


def data_quality_summary(
    fundamental: dict[str, Any] | None,
    raw: dict[str, Any] | None,
) -> dict[str, Any]:
    detected = detect_forbidden_terms({"fundamental": fundamental, "raw": raw})
    return {
        "missing_fields": as_list((fundamental or {}).get("missing_fields")),
        "errors": as_list((raw or {}).get("errors")),
        "fetch_status": fetch_status_rows(raw),
        "source_trace": source_trace_rows(raw),
        "forbidden_terms_detected": bool(detected),
        "forbidden_terms_count": len(detected),
    }


def fetch_status_rows(raw: dict[str, Any] | None) -> list[dict[str, Any]]:
    status = (raw or {}).get("fetch_status")
    if not isinstance(status, dict):
        return []
    rows = []
    for block_name, item in sorted(status.items()):
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "block_name": block_name,
                "success": item.get("success"),
                "error": item.get("error"),
                "missing_fields_count": len(as_list(item.get("missing_fields"))),
                "warnings_count": len(as_list(item.get("warnings"))),
                "source_trace_count": len(as_list(item.get("source_trace"))),
                "fetched_at": item.get("fetched_at"),
            }
        )
    return rows


def source_trace_rows(raw: dict[str, Any] | None) -> list[dict[str, Any]]:
    status = (raw or {}).get("fetch_status")
    if not isinstance(status, dict):
        return []
    rows = []
    for block_name, item in sorted(status.items()):
        if not isinstance(item, dict):
            continue
        for trace in as_list(item.get("source_trace")):
            if isinstance(trace, dict):
                row = {"block_name": block_name}
                row.update(trace)
                rows.append(row)
    return rows


def detect_forbidden_terms(payload: Any) -> list[str]:
    text = stringify_payload(payload)
    terms = list(FORBIDDEN_TRADING_TERMS) + list(MOJIBAKE_FORBIDDEN_TRADING_TERMS)
    return sorted({term for term in terms if term and term in text})


def has_forbidden_terms(payload: Any) -> bool:
    return bool(detect_forbidden_terms(payload))


def stringify_payload(payload: Any) -> str:
    if payload is None:
        return ""
    if isinstance(payload, str):
        return payload
    try:
        return json.dumps(payload, ensure_ascii=False, default=str)
    except TypeError:
        return str(payload)


def extract_block_rows(payload: dict[str, Any] | None, block_name: str) -> list[dict[str, Any]]:
    blocks = (payload or {}).get("blocks")
    if isinstance(blocks, dict):
        return [row for row in as_list(blocks.get(block_name)) if isinstance(row, dict)]
    rows = (payload or {}).get(block_name)
    return [row for row in as_list(rows) if isinstance(row, dict)]


def first_dict(value: Any) -> dict[str, Any]:
    for item in as_list(value):
        if isinstance(item, dict):
            return item
    return {}


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def pick_fields(row: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    return {field: row.get(field) for field in fields}


def summarize_evidence(evidence: Any) -> str | None:
    items = [item for item in as_list(evidence) if isinstance(item, dict)]
    if not items:
        return None
    parts = []
    for item in items[:3]:
        source = item.get("source")
        metric = item.get("metric_name")
        value = item.get("value")
        period = item.get("period")
        interpretation = item.get("interpretation")
        pieces = [str(piece) for piece in (source, metric, value, period, interpretation) if piece not in (None, "")]
        if pieces:
            parts.append(" | ".join(pieces))
    return "\n".join(parts) if parts else None
