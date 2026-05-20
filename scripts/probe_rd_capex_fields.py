# -*- coding: utf-8 -*-
"""Probe R&D and capex statement fields from AkShare candidates.

Probe-only helper for RealDataConnector v2.3 source expansion. It does not
modify RealDataConnector, run the deterministic pipeline, render reports, call
accounts, or add technical/trader behavior.
"""

from __future__ import annotations

import argparse
import inspect
import json
import math
import re
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any


DEFAULT_CODES = ("002050", "002371", "300308", "000426", "601899", "603993")

TARGET_FIELD_KEYWORDS: dict[str, tuple[str, ...]] = {
    "r_and_d_expense": ("研发费用", "研究开发费用", "研发支出", "研发投入", "研发费用合计"),
    "capex": (
        "购建固定资产、无形资产和其他长期资产支付的现金",
        "购建固定资产、无形资产和其他长期资产所支付的现金",
        "购建固定资产、无形资产和其他长期资产支付现金",
    ),
    "depreciation_amortization": (
        "固定资产折旧、油气资产折耗、生产性生物资产折旧",
        "无形资产摊销",
        "长期待摊费用摊销",
        "折旧与摊销",
    ),
}

DERIVED_FIELDS = ("r_and_d_expense_ratio", "capex_ratio")
ALL_TARGET_FIELDS = tuple(TARGET_FIELD_KEYWORDS) + DERIVED_FIELDS
REVENUE_KEYWORDS = ("营业总收入", "营业收入")

TARGET_FIELD_EXCLUDES: dict[str, tuple[str, ...]] = {
    "r_and_d_expense": ("增长率", "同比", "占比", "比例", "费用率"),
    "capex": ("固定资产余额", "在建工程", "同比", "比例"),
    "depreciation_amortization": ("同比", "比例"),
}

CANDIDATE_FUNCTIONS: tuple[dict[str, str], ...] = (
    {"statement_type": "profit_sheet", "function_name": "stock_profit_sheet_by_report_em"},
    {"statement_type": "profit_sheet", "function_name": "stock_profit_sheet_by_yearly_em"},
    {"statement_type": "profit_sheet", "function_name": "stock_profit_sheet_by_quarterly_em"},
    {"statement_type": "profit_sheet", "function_name": "stock_financial_report_sina"},
    {"statement_type": "profit_sheet", "function_name": "stock_financial_abstract"},
    {"statement_type": "cash_flow_sheet", "function_name": "stock_cash_flow_sheet_by_report_em"},
    {"statement_type": "cash_flow_sheet", "function_name": "stock_cash_flow_sheet_by_yearly_em"},
    {"statement_type": "cash_flow_sheet", "function_name": "stock_cash_flow_sheet_by_quarterly_em"},
    {"statement_type": "cash_flow_sheet", "function_name": "stock_financial_report_sina"},
    {"statement_type": "cash_flow_sheet", "function_name": "stock_financial_abstract"},
    {"statement_type": "financial_abstract", "function_name": "stock_financial_abstract"},
    {"statement_type": "financial_abstract", "function_name": "stock_financial_analysis_indicator"},
)

KEYWORD_SAMPLE_LIMIT = 5
PERIOD_KEYS = ("报告期", "报告日期", "报告日", "日期", "截止日期", "REPORT_DATE", "date")
VALUE_KEYS = ("本期金额", "金额", "value", "VALUE", "本期数", "本期发生额")


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(json_safe(key)): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item) for item in value]
    module_name = type(value).__module__
    if module_name.startswith("numpy"):
        try:
            converted = value.item()
            if converted is not value:
                return json_safe(converted)
        except Exception:
            pass
        try:
            numeric = float(value)
            return numeric if math.isfinite(numeric) else None
        except Exception:
            return str(value)
    if module_name.startswith("pandas"):
        if str(value) in {"NaT", "nan", "NaN"}:
            return None
        if hasattr(value, "isoformat"):
            try:
                return value.isoformat()
            except Exception:
                pass
        return str(value)
    if str(value) in {"nan", "NaN", "NaT"}:
        return None
    return str(value)


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            return None
        return float(value)
    if isinstance(value, str):
        text = value.strip().replace(",", "").replace("%", "")
        if text in {"", "--", "None", "none", "null", "nan", "NaN"}:
            return None
        multiplier = 1.0
        if text.endswith("亿元"):
            multiplier = 100000000.0
            text = text[:-2]
        elif text.endswith("万元"):
            multiplier = 10000.0
            text = text[:-2]
        elif text.endswith("亿"):
            multiplier = 100000000.0
            text = text[:-1]
        elif text.endswith("万"):
            multiplier = 10000.0
            text = text[:-1]
        try:
            return float(text) * multiplier
        except ValueError:
            return None
    return None


def records(frame_or_records: Any) -> list[dict[str, Any]]:
    if frame_or_records is None:
        return []
    if isinstance(frame_or_records, list):
        return [item for item in frame_or_records if isinstance(item, dict)]
    if isinstance(frame_or_records, dict):
        return [frame_or_records]
    if hasattr(frame_or_records, "to_dict"):
        try:
            return frame_or_records.to_dict(orient="records")
        except TypeError:
            data = frame_or_records.to_dict()
            return data if isinstance(data, list) else [data]
    return []


def frame_shape(frame_or_records: Any, rows: list[dict[str, Any]]) -> list[int]:
    shape = getattr(frame_or_records, "shape", None)
    if shape is not None:
        return [int(item) for item in shape]
    if rows:
        return [len(rows), len(rows[0])]
    return [0, 0]


def frame_columns(frame_or_records: Any, rows: list[dict[str, Any]]) -> list[str]:
    columns = getattr(frame_or_records, "columns", None)
    if columns is not None:
        return [str(item) for item in list(columns)]
    seen: list[str] = []
    for row in rows:
        for key in row:
            text = str(key)
            if text not in seen:
                seen.append(text)
    return seen


def frame_dtypes(frame_or_records: Any, columns: list[str]) -> dict[str, str]:
    dtypes = getattr(frame_or_records, "dtypes", None)
    if dtypes is None:
        return {}
    result: dict[str, str] = {}
    for column in columns:
        try:
            result[column] = str(dtypes[column])
        except Exception:
            pass
    return result


def period_columns(columns: list[str]) -> list[str]:
    return sorted(
        [column for column in columns if re.fullmatch(r"(?:19|20)\d{6}", str(column))],
        reverse=True,
    )


def detect_periods(columns: list[str], rows: list[dict[str, Any]]) -> list[str]:
    found = set(period_columns(columns))
    for row in rows:
        for key, value in row.items():
            for item in (key, value):
                text = str(item)
                if re.fullmatch(r"(?:19|20)\d{6}", text):
                    found.add(text)
                elif re.fullmatch(r"(?:19|20)\d{2}-\d{2}-\d{2}", text):
                    found.add(text)
    return sorted(found, reverse=True)


def row_name_columns(columns: list[str]) -> list[str]:
    priority = (
        "指标",
        "项目",
        "项目名称",
        "报表项目",
        "科目",
        "名称",
        "item",
        "ITEM_NAME",
        "REPORT_ITEM_NAME",
    )
    selected = [column for column in priority if column in columns]
    return selected or columns[:2]


def row_text(row: dict[str, Any], columns: list[str]) -> str:
    if not columns:
        return " ".join(str(value) for value in row.values())
    return " ".join(str(row.get(column, "")) for column in columns)


def contains_any(text: Any, keywords: tuple[str, ...]) -> bool:
    haystack = str(text)
    return any(keyword in haystack for keyword in keywords)


def is_excluded_target_text(target_field: str, text: Any) -> bool:
    excludes = TARGET_FIELD_EXCLUDES.get(target_field, ())
    return any(exclude in str(text) for exclude in excludes)


def first_matching_column(columns: list[str], keywords: tuple[str, ...], target_field: str | None = None) -> str | None:
    for keyword in keywords:
        for column in columns:
            if target_field and is_excluded_target_text(target_field, column):
                continue
            if keyword == str(column):
                return column
    for keyword in keywords:
        for column in columns:
            if target_field and is_excluded_target_text(target_field, column):
                continue
            if keyword in str(column):
                return column
    return None


def unit_from_text(*parts: Any) -> tuple[str | None, str]:
    text = " ".join(str(part) for part in parts if part is not None)
    if "亿元" in text:
        return "CNY_100m", "medium"
    if "万元" in text:
        return "CNY_10k", "medium"
    if re.search(r"[^万亿]元", text):
        return "CNY", "medium"
    if "%" in text or "比例" in text or "率" in text:
        return "%", "medium"
    return "raw_statement_unit", "low"


def bind_period(row: dict[str, Any], fallback_period: str | None = None) -> tuple[str, str]:
    for key in PERIOD_KEYS:
        if row.get(key):
            text = str(row[key])
            confidence = "high" if re.fullmatch(r"(?:19|20)\d{6}", text) or re.fullmatch(r"(?:19|20)\d{2}-\d{2}-\d{2}", text) else "medium"
            return text, confidence
    if fallback_period:
        confidence = "high" if re.fullmatch(r"(?:19|20)\d{6}", str(fallback_period)) else "medium"
        return str(fallback_period), confidence
    return "unknown", "low"


def infer_cumulative_or_single_quarter(function_name: str, statement_type: str, period: str | None = None) -> str:
    if "quarterly" in function_name:
        return "single_quarter"
    if "yearly" in function_name or "by_report" in function_name:
        return "cumulative"
    if statement_type in {"profit_sheet", "cash_flow_sheet"} and period and re.fullmatch(r"(?:19|20)\d{6}", str(period)):
        return "cumulative"
    return "unknown"


def latest_period_value(row: dict[str, Any], columns: list[str]) -> tuple[str | None, Any, str | None]:
    for period in period_columns(columns):
        value = row.get(period)
        if safe_float(value) is not None:
            return period, value, period
    source_period = None
    for key in PERIOD_KEYS:
        if row.get(key):
            source_period = str(row.get(key))
            break
    for key in VALUE_KEYS:
        if key in row and safe_float(row.get(key)) is not None:
            return source_period, row.get(key), key
    numeric_items = [(key, value) for key, value in row.items() if safe_float(value) is not None and key not in PERIOD_KEYS]
    if numeric_items:
        key, value = numeric_items[-1]
        return source_period or str(key), value, str(key)
    return source_period, None, None


def find_rows_by_keywords(rows: list[dict[str, Any]], columns: list[str], keywords: tuple[str, ...]) -> list[dict[str, Any]]:
    names = row_name_columns(columns)
    matches = [row for row in rows if contains_any(row_text(row, names), keywords)]
    if not matches:
        matches = [row for row in rows if contains_any(json.dumps(json_safe(row), ensure_ascii=False), keywords)]
    return matches


def normalize_match(match: dict[str, Any]) -> dict[str, Any]:
    source_column_or_row = match.get("source_column_or_row") or match.get("source_column") or match.get("source_row_name")
    period = match.get("source_period") or "unknown"
    value_confidence = match.get("value_confidence") or "none"
    period_confidence = match.get("period_confidence") or ("low" if period == "unknown" else "medium")
    unit_confidence = match.get("unit_confidence") or ("low" if match.get("unit") == "raw_statement_unit" else "medium")
    match["source_column_or_row"] = source_column_or_row
    match["source_period"] = period
    match["period_confidence"] = period_confidence
    match["value_confidence"] = value_confidence
    match["unit_confidence"] = unit_confidence
    return match


def make_missing_match(target_field: str, function_name: str, notes: str | None = None) -> dict[str, Any]:
    return normalize_match({
        "matched": False,
        "source_function": function_name,
        "source_column": None,
        "source_row_name": None,
        "source_column_or_row": None,
        "source_period": "unknown",
        "value": None,
        "unit": None,
        "period_confidence": "none",
        "value_confidence": "none",
        "unit_confidence": "none",
        "cumulative_or_single_quarter": "unknown",
        "derivation_method": None,
        "notes": notes or "target field not found in this function result",
    })


def direct_match(
    target_field: str,
    function_name: str,
    statement_type: str,
    rows: list[dict[str, Any]],
    columns: list[str],
) -> dict[str, Any]:
    keywords = TARGET_FIELD_KEYWORDS[target_field]
    column = first_matching_column(columns, keywords, target_field)
    if column:
        sorted_rows = sorted(
            rows,
            key=lambda row: str(next((row.get(key) for key in PERIOD_KEYS if row.get(key)), "")),
            reverse=True,
        )
        for row in sorted_rows or rows:
            value = row.get(column)
            if safe_float(value) is not None:
                period, period_confidence = bind_period(row)
                unit, unit_confidence = unit_from_text(column, value)
                return normalize_match({
                    "matched": True,
                    "source_function": function_name,
                    "source_column": column,
                    "source_row_name": None,
                    "source_column_or_row": column,
                    "source_period": period,
                    "value": json_safe(value),
                    "unit": unit,
                    "period_confidence": period_confidence,
                    "value_confidence": "medium",
                    "unit_confidence": unit_confidence,
                    "cumulative_or_single_quarter": infer_cumulative_or_single_quarter(function_name, statement_type, period),
                    "derivation_method": None,
                    "notes": "matched by source column name",
                })
    names = row_name_columns(columns)
    for row in find_rows_by_keywords(rows, columns, keywords):
        text = row_text(row, names)
        if is_excluded_target_text(target_field, text):
            continue
        source_period, value, value_column = latest_period_value(row, columns)
        if safe_float(value) is None:
            continue
        period_confidence = "low" if not source_period else ("high" if re.fullmatch(r"(?:19|20)\d{6}", str(source_period)) else "medium")
        unit, unit_confidence = unit_from_text(text, value_column, value)
        return normalize_match({
            "matched": True,
            "source_function": function_name,
            "source_column": value_column,
            "source_row_name": text,
            "source_column_or_row": value_column if value_column in columns else text,
            "source_period": source_period,
            "value": json_safe(value),
            "unit": unit,
            "period_confidence": period_confidence,
            "value_confidence": "high",
            "unit_confidence": unit_confidence,
            "cumulative_or_single_quarter": infer_cumulative_or_single_quarter(function_name, statement_type, source_period),
            "derivation_method": None,
            "notes": "matched by row name and latest numeric period",
        })
    return make_missing_match(target_field, function_name)


def direct_revenue_match(function_name: str, statement_type: str, rows: list[dict[str, Any]], columns: list[str]) -> dict[str, Any] | None:
    column = first_matching_column(columns, REVENUE_KEYWORDS)
    if column:
        sorted_rows = sorted(
            rows,
            key=lambda row: str(next((row.get(key) for key in PERIOD_KEYS if row.get(key)), "")),
            reverse=True,
        )
        for row in sorted_rows or rows:
            value = row.get(column)
            if safe_float(value) is not None:
                period, period_confidence = bind_period(row)
                unit, unit_confidence = unit_from_text(column, value)
                return normalize_match({
                    "matched": True,
                    "source_function": function_name,
                    "source_column": column,
                    "source_row_name": None,
                    "source_column_or_row": column,
                    "source_period": period,
                    "value": json_safe(value),
                    "unit": unit,
                    "period_confidence": period_confidence,
                    "value_confidence": "medium",
                    "unit_confidence": unit_confidence,
                    "cumulative_or_single_quarter": infer_cumulative_or_single_quarter(function_name, statement_type, period),
                    "derivation_method": None,
                    "notes": "revenue denominator matched by column name",
                })
    names = row_name_columns(columns)
    for row in find_rows_by_keywords(rows, columns, REVENUE_KEYWORDS):
        source_period, value, value_column = latest_period_value(row, columns)
        if safe_float(value) is not None:
            unit, unit_confidence = unit_from_text(row_text(row, names), value_column, value)
            return normalize_match({
                "matched": True,
                "source_function": function_name,
                "source_column": value_column,
                "source_row_name": row_text(row, names),
                "source_column_or_row": value_column if value_column in columns else row_text(row, names),
                "source_period": source_period,
                "value": json_safe(value),
                "unit": unit,
                "period_confidence": "low" if not source_period else ("high" if re.fullmatch(r"(?:19|20)\d{6}", str(source_period)) else "medium"),
                "value_confidence": "medium",
                "unit_confidence": unit_confidence,
                "cumulative_or_single_quarter": infer_cumulative_or_single_quarter(function_name, statement_type, source_period),
                "derivation_method": None,
                "notes": "revenue denominator matched by row name",
            })
    return None


def derive_ratio_match(
    target_field: str,
    numerator_match: dict[str, Any],
    revenue_match: dict[str, Any] | None,
    function_name: str,
) -> dict[str, Any]:
    if not numerator_match.get("matched"):
        return make_missing_match(target_field, function_name, "numerator field is missing")
    if not revenue_match or not revenue_match.get("matched"):
        return make_missing_match(target_field, function_name, "revenue is missing, ratio not derived")
    numerator_period = numerator_match.get("source_period")
    revenue_period = revenue_match.get("source_period")
    if numerator_period != revenue_period or numerator_period in (None, "", "unknown"):
        return make_missing_match(
            target_field,
            function_name,
            f"source period mismatch, ratio not derived: numerator={numerator_period}, revenue={revenue_period}",
        )
    numerator = safe_float(numerator_match.get("value"))
    denominator = safe_float(revenue_match.get("value"))
    if numerator is None or denominator in (None, 0):
        return make_missing_match(target_field, function_name, "numerator or revenue is not numeric, ratio not derived")
    return normalize_match({
        "matched": True,
        "source_function": function_name,
        "source_column": numerator_match.get("source_column"),
        "source_row_name": numerator_match.get("source_row_name"),
        "source_column_or_row": numerator_match.get("source_column_or_row"),
        "source_period": numerator_period,
        "value": numerator / denominator * 100,
        "unit": "%",
        "period_confidence": numerator_match.get("period_confidence") or revenue_match.get("period_confidence") or "medium",
        "value_confidence": "medium",
        "unit_confidence": "high",
        "cumulative_or_single_quarter": numerator_match.get("cumulative_or_single_quarter") or "unknown",
        "derivation_method": f"{target_field.replace('_ratio', '')} / revenue * 100, same source_period only",
        "notes": "derived only because numerator and revenue share the same source_period",
    })


def detect_target_field_matches(function_name: str, statement_type: str, rows: list[dict[str, Any]], columns: list[str]) -> dict[str, dict[str, Any]]:
    matches = {
        target: direct_match(target, function_name, statement_type, rows, columns)
        for target in TARGET_FIELD_KEYWORDS
    }
    revenue = direct_revenue_match(function_name, statement_type, rows, columns)
    matches["r_and_d_expense_ratio"] = derive_ratio_match(
        "r_and_d_expense_ratio",
        matches["r_and_d_expense"],
        revenue,
        function_name,
    )
    matches["capex_ratio"] = derive_ratio_match("capex_ratio", matches["capex"], revenue, function_name)
    return matches


def detect_field_candidates(rows: list[dict[str, Any]], columns: list[str]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for target, keywords in {**TARGET_FIELD_KEYWORDS, "revenue": REVENUE_KEYWORDS}.items():
        candidates = []
        column = first_matching_column(columns, keywords, target if target in TARGET_FIELD_KEYWORDS else None)
        if column:
            candidates.append(f"column:{column}")
        names = row_name_columns(columns)
        for row in find_rows_by_keywords(rows, columns, keywords)[:KEYWORD_SAMPLE_LIMIT]:
            text = row_text(row, names)
            if target in TARGET_FIELD_KEYWORDS and is_excluded_target_text(target, text):
                continue
            if text and f"row:{text}" not in candidates:
                candidates.append(f"row:{text}")
        result[target] = candidates
    return result


def sample_rows_by_keywords(rows: list[dict[str, Any]], columns: list[str]) -> dict[str, list[dict[str, Any]]]:
    samples: dict[str, list[dict[str, Any]]] = {}
    for label, keywords in {**TARGET_FIELD_KEYWORDS, "revenue": REVENUE_KEYWORDS}.items():
        samples[label] = [json_safe(row) for row in find_rows_by_keywords(rows, columns, keywords)[:KEYWORD_SAMPLE_LIMIT]]
    return samples


def summarize_result(
    statement_type: str,
    function_name: str,
    frame_or_records: Any,
    limit_rows: int,
) -> dict[str, Any]:
    row_list = records(frame_or_records)
    columns = frame_columns(frame_or_records, row_list)
    return {
        "statement_type": statement_type,
        "function_name": function_name,
        "success": True,
        "error": None,
        "shape": frame_shape(frame_or_records, row_list),
        "columns_full": columns,
        "dtypes": frame_dtypes(frame_or_records, columns),
        "head_rows": [json_safe(row) for row in row_list[:limit_rows]],
        "detected_report_periods": detect_periods(columns, row_list),
        "detected_field_candidates": detect_field_candidates(row_list, columns),
        "target_field_matches": detect_target_field_matches(function_name, statement_type, row_list, columns),
        "sample_rows_by_keywords": sample_rows_by_keywords(row_list, columns),
    }


def summarize_failure(statement_type: str, function_name: str, error: str) -> dict[str, Any]:
    return {
        "statement_type": statement_type,
        "function_name": function_name,
        "success": False,
        "error": error,
        "shape": [0, 0],
        "columns_full": [],
        "dtypes": {},
        "head_rows": [],
        "detected_report_periods": [],
        "detected_field_candidates": {},
        "target_field_matches": {target: make_missing_match(target, function_name) for target in ALL_TARGET_FIELDS},
        "sample_rows_by_keywords": {},
    }


def market_prefix(code: str) -> str:
    return "sh" if code.startswith(("60", "68", "9")) else "sz"


def prefixed_symbol(code: str) -> str:
    return f"{market_prefix(code)}{code}"


def call_variants(function_name: str, statement_type: str, code: str) -> list[tuple[tuple[Any, ...], dict[str, Any]]]:
    prefixed = prefixed_symbol(code)
    if function_name == "stock_financial_report_sina":
        statement_name = "利润表" if statement_type == "profit_sheet" else "现金流量表"
        return [
            ((), {"stock": prefixed, "symbol": statement_name}),
            ((), {"stock": code, "symbol": statement_name}),
            ((prefixed,), {"symbol": statement_name}),
            ((code,), {"symbol": statement_name}),
            ((code,), {"indicator": statement_name}),
            ((), {"symbol": code}),
            ((), {"stock": prefixed}),
        ]
    if function_name == "stock_financial_abstract":
        return [((), {"symbol": code}), ((code,), {}), ((), {"stock": prefixed})]
    if function_name == "stock_financial_analysis_indicator":
        return [((), {"symbol": code}), ((code,), {}), ((), {"stock": prefixed})]
    return [((), {"symbol": code}), ((code,), {}), ((), {"stock": prefixed}), ((), {"stock": code})]


def function_accepts_call(func: Any, args: tuple[Any, ...], kwargs: dict[str, Any]) -> bool:
    try:
        inspect.signature(func).bind_partial(*args, **kwargs)
        return True
    except Exception:
        return True


def attempt_function(ak: Any, statement_type: str, function_name: str, code: str, limit_rows: int) -> dict[str, Any]:
    if not hasattr(ak, function_name):
        return summarize_failure(statement_type, function_name, "function_not_found")
    func = getattr(ak, function_name)
    errors: list[str] = []
    for args, kwargs in call_variants(function_name, statement_type, code):
        try:
            if not function_accepts_call(func, args, kwargs):
                continue
            payload = func(*args, **kwargs)
            result = summarize_result(statement_type, function_name, payload, limit_rows)
            result["call_args"] = list(args)
            result["call_kwargs"] = kwargs
            return result
        except Exception as exc:  # pragma: no cover - AkShare failures vary by version/network
            errors.append(f"args={args} kwargs={kwargs}: {type(exc).__name__}: {exc}")
    return summarize_failure(statement_type, function_name, " | ".join(errors) if errors else "no_call_variant_succeeded")


def probe_code(code: str, ak: Any, limit_rows: int) -> dict[str, Any]:
    version = getattr(ak, "__version__", "unknown")
    function_results = [
        attempt_function(ak, item["statement_type"], item["function_name"], code, limit_rows)
        for item in CANDIDATE_FUNCTIONS
    ]
    return {
        "schema_version": "rd_capex_probe.v1",
        "stock_code": code,
        "generated_at": now_iso(),
        "akshare_version": version,
        "functions_attempted": [item["function_name"] for item in CANDIDATE_FUNCTIONS],
        "target_fields": list(ALL_TARGET_FIELDS),
        "function_results": function_results,
    }


def load_akshare() -> Any:
    import akshare as ak  # type: ignore

    return ak


def write_probe(probe: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"probe_{probe['stock_code']}.json"
    path.write_text(json.dumps(json_safe(probe), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codes", nargs="*", default=list(DEFAULT_CODES))
    parser.add_argument("--output-dir", default="data/rd_capex_probe")
    parser.add_argument("--limit-rows", type=int, default=5)
    args = parser.parse_args()

    ak = load_akshare()
    output_dir = Path(args.output_dir)
    for code in args.codes:
        probe = probe_code(code, ak, args.limit_rows)
        path = write_probe(probe, output_dir)
        successes = sum(1 for item in probe["function_results"] if item.get("success"))
        print(f"{code}: wrote {path} successful_functions={successes}")


if __name__ == "__main__":
    main()
