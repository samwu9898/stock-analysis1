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
from .ai_analyst.safety import check_text_safety


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"

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


def ai_report_summary_row(payload: dict[str, Any], source_path: str | Path | None = None) -> dict[str, Any]:
    return {
        "stock_code": payload.get("stock_code") or code_from_path(source_path, prefix="ai_report_"),
        "stock_name": payload.get("stock_name"),
        "fundamental_view": payload.get("fundamental_view"),
        "executive_summary": payload.get("executive_summary"),
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
    fields = ["dimension", "level", "reason"]
    return [pick_fields(row, fields) for row in rows if isinstance(row, dict)]


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
            "can_display_body": False,
        }
    schema = validate_ai_report(ai_report)
    json_safety = schema.get("safety", {})
    md_safety = check_text_safety(ai_report_markdown or "", allow_policy_context=False)
    blocked_terms = sorted(set(as_list(json_safety.get("blocked_terms")) + as_list(md_safety.get("blocked_terms"))))
    violations = as_list(json_safety.get("violations")) + as_list(md_safety.get("violations"))
    schema_valid = bool(schema.get("valid")) and not schema.get("schema_errors")
    safety_safe = bool(json_safety.get("safe", True)) and bool(md_safety.get("safe", True))
    return {
        "schema_valid": schema_valid,
        "schema_errors": schema.get("schema_errors", []),
        "safety_safe": safety_safe,
        "restricted_terms_count": len(blocked_terms),
        "blocked_terms": blocked_terms,
        "violations": violations,
        "can_display_body": schema_valid and safety_safe,
    }


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
