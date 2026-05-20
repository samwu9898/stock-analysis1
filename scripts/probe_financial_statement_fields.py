# -*- coding: utf-8 -*-
"""Probe financial statement fields from AkShare candidates.

This is a probe-only helper. It does not modify RealDataConnector, does not run
the deterministic pipeline, does not render dashboard output, and does not make
network access except through the explicitly probed AkShare functions.
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
    "inventory": ("存货", "存货合计"),
    "accounts_receivable": ("应收账款", "应收账款及应收票据", "应收票据及应收账款", "应收款项融资"),
    "contract_liabilities": ("合同负债", "预收款项", "预收账款"),
    "r_and_d_expense": ("研发费用", "研究开发费用"),
    "capex": (
        "购建固定资产、无形资产和其他长期资产支付的现金",
        "购建固定资产、无形资产和其他长期资产所支付的现金",
        "购建固定资产、无形资产和其他长期资产支付现金",
    ),
}

DERIVED_FIELDS = ("r_and_d_expense_ratio", "capex_ratio")
ALL_TARGET_FIELDS = tuple(TARGET_FIELD_KEYWORDS) + DERIVED_FIELDS
REVENUE_KEYWORDS = ("营业总收入", "营业收入")
TARGET_FIELD_EXCLUDES: dict[str, tuple[str, ...]] = {
    "inventory": ("周转率", "周转天数"),
    "accounts_receivable": ("周转率", "周转天数"),
}

CANDIDATE_FUNCTIONS: tuple[dict[str, str], ...] = (
    {"statement_type": "balance_sheet", "function_name": "stock_balance_sheet_by_report_em"},
    {"statement_type": "balance_sheet", "function_name": "stock_balance_sheet_by_yearly_em"},
    {"statement_type": "balance_sheet", "function_name": "stock_balance_sheet_by_quarterly_em"},
    {"statement_type": "balance_sheet", "function_name": "stock_financial_report_sina"},
    {"statement_type": "profit_sheet", "function_name": "stock_profit_sheet_by_report_em"},
    {"statement_type": "profit_sheet", "function_name": "stock_profit_sheet_by_yearly_em"},
    {"statement_type": "profit_sheet", "function_name": "stock_profit_sheet_by_quarterly_em"},
    {"statement_type": "profit_sheet", "function_name": "stock_financial_abstract"},
    {"statement_type": "cash_flow_sheet", "function_name": "stock_cash_flow_sheet_by_report_em"},
    {"statement_type": "cash_flow_sheet", "function_name": "stock_cash_flow_sheet_by_yearly_em"},
    {"statement_type": "cash_flow_sheet", "function_name": "stock_cash_flow_sheet_by_quarterly_em"},
    {"statement_type": "cash_flow_sheet", "function_name": "stock_financial_abstract"},
)

KEYWORD_SAMPLE_LIMIT = 5
PERIOD_KEYS = ("报告日", "报告期", "报告日期", "日期", "截止日期", "REPORT_DATE", "date")
VALUE_KEYS = ("本期金额", "金额", "value", "VALUE", "期末余额", "本期数")


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
        if text.endswith("亿"):
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


def contains_any(text: Any, keywords: tuple[str, ...]) -> bool:
    haystack = str(text)
    return any(keyword in haystack for keyword in keywords)


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


def latest_period_value(row: dict[str, Any], columns: list[str]) -> tuple[str | None, Any]:
    for period in period_columns(columns):
        value = row.get(period)
        if safe_float(value) is not None:
            return period, value
    source_period = None
    for key in PERIOD_KEYS:
        if row.get(key):
            source_period = str(row.get(key))
            break
    for key in VALUE_KEYS:
        if key in row and safe_float(row.get(key)) is not None:
            return source_period, row.get(key)
    numeric_items = [(key, value) for key, value in row.items() if safe_float(value) is not None and key not in PERIOD_KEYS]
    if numeric_items:
        key, value = numeric_items[-1]
        return source_period or str(key), value
    return source_period, None


def bind_period(row: dict[str, Any], fallback_period: str | None = None) -> tuple[str, str]:
    for key in PERIOD_KEYS:
        if row.get(key):
            return str(row[key]), "high"
    if fallback_period:
        return str(fallback_period), "medium"
    return "unknown", "low"


def normalize_match(match: dict[str, Any]) -> dict[str, Any]:
    source_column_or_row = match.get("source_column_or_row") or match.get("source_column") or match.get("source_row_name")
    period = match.get("source_period") or "unknown"
    value_confidence = match.get("value_confidence") or match.get("confidence") or "none"
    period_confidence = match.get("period_confidence") or ("low" if period == "unknown" else "medium")
    match["source_column_or_row"] = source_column_or_row
    match["source_period"] = period
    match["period_confidence"] = period_confidence
    match["value_confidence"] = value_confidence
    match["confidence"] = value_confidence
    return match


def find_rows_by_keywords(rows: list[dict[str, Any]], columns: list[str], keywords: tuple[str, ...]) -> list[dict[str, Any]]:
    names = row_name_columns(columns)
    matches = [row for row in rows if contains_any(row_text(row, names), keywords)]
    if not matches:
        matches = [row for row in rows if contains_any(json.dumps(json_safe(row), ensure_ascii=False), keywords)]
    return matches


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


def detect_field_candidates(rows: list[dict[str, Any]], columns: list[str]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for target, keywords in {**TARGET_FIELD_KEYWORDS, "revenue": REVENUE_KEYWORDS}.items():
        candidates = []
        column = first_matching_column(columns, keywords, target)
        if column:
            candidates.append(f"column:{column}")
        names = row_name_columns(columns)
        for row in find_rows_by_keywords(rows, columns, keywords)[:KEYWORD_SAMPLE_LIMIT]:
            text = row_text(row, names)
            if is_excluded_target_text(target, text):
                continue
            if text and text not in candidates:
                candidates.append(f"row:{text}")
        result[target] = candidates
    return result


def make_missing_match(target_field: str, function_name: str) -> dict[str, Any]:
    return normalize_match({
        "matched": False,
        "source_function": function_name,
        "source_column": None,
        "source_row_name": None,
        "source_column_or_row": None,
        "source_period": None,
        "value": None,
        "unit": None,
        "confidence": "none",
        "period_confidence": "none",
        "value_confidence": "none",
        "notes": "target field not found in this function result",
    })


def direct_match(
    target_field: str,
    function_name: str,
    rows: list[dict[str, Any]],
    columns: list[str],
) -> dict[str, Any]:
    keywords = TARGET_FIELD_KEYWORDS[target_field]
    column = first_matching_column(columns, keywords, target_field)
    if column:
        sorted_rows = sorted(rows, key=lambda row: str(next((row.get(key) for key in PERIOD_KEYS if row.get(key)), "")), reverse=True)
        for row in sorted_rows or rows:
            value = row.get(column)
            if safe_float(value) is not None:
                period, period_confidence = bind_period(row)
                return normalize_match({
                    "matched": True,
                    "source_function": function_name,
                    "source_column": column,
                    "source_row_name": None,
                    "source_column_or_row": column,
                    "source_period": period,
                    "value": json_safe(value),
                    "unit": "raw_statement_unit",
                    "confidence": "medium",
                    "period_confidence": period_confidence,
                    "value_confidence": "medium",
                    "notes": "matched by source column name",
                })
    names = row_name_columns(columns)
    for row in find_rows_by_keywords(rows, columns, keywords):
        if is_excluded_target_text(target_field, row_text(row, names)):
            continue
        source_period, value = latest_period_value(row, columns)
        if safe_float(value) is None:
            continue
        period_confidence = "low" if not source_period else ("medium" if source_period in columns else "high")
        return normalize_match({
            "matched": True,
            "source_function": function_name,
            "source_column": source_period if source_period in columns else None,
            "source_row_name": row_text(row, names),
            "source_column_or_row": source_period if source_period in columns else row_text(row, names),
            "source_period": source_period,
            "value": json_safe(value),
            "unit": "raw_statement_unit",
            "confidence": "high" if target_field in {"inventory", "contract_liabilities", "r_and_d_expense", "capex"} else "medium",
            "period_confidence": period_confidence,
            "value_confidence": "high" if target_field in {"inventory", "contract_liabilities", "r_and_d_expense", "capex"} else "medium",
            "notes": "matched by row name and latest numeric period",
        })
    return make_missing_match(target_field, function_name)


def derive_ratio_match(
    target_field: str,
    numerator_match: dict[str, Any],
    revenue_match: dict[str, Any] | None,
    function_name: str,
) -> dict[str, Any]:
    if not numerator_match.get("matched"):
        result = make_missing_match(target_field, function_name)
        result["notes"] = "numerator field is missing"
        return result
    if not revenue_match or not revenue_match.get("matched"):
        result = make_missing_match(target_field, function_name)
        result["notes"] = "营业总收入 is missing, ratio not derived"
        return result
    numerator = safe_float(numerator_match.get("value"))
    denominator = safe_float(revenue_match.get("value"))
    if numerator is None or denominator in (None, 0):
        result = make_missing_match(target_field, function_name)
        result["notes"] = "numerator or 营业总收入 is not numeric, ratio not derived"
        return result
    period = numerator_match.get("source_period") or revenue_match.get("source_period") or "unknown"
    period_confidence = (
        numerator_match.get("period_confidence")
        or revenue_match.get("period_confidence")
        or ("low" if period == "unknown" else "medium")
    )
    return normalize_match({
        "matched": True,
        "source_function": function_name,
        "source_column": numerator_match.get("source_column"),
        "source_row_name": numerator_match.get("source_row_name"),
        "source_column_or_row": numerator_match.get("source_column_or_row") or numerator_match.get("source_column") or numerator_match.get("source_row_name"),
        "source_period": period,
        "value": numerator / denominator * 100,
        "unit": "%",
        "confidence": "medium",
        "period_confidence": period_confidence,
        "value_confidence": "medium",
        "notes": "derived as numerator / 营业总收入 * 100",
    })


def detect_target_field_matches(function_name: str, rows: list[dict[str, Any]], columns: list[str]) -> dict[str, dict[str, Any]]:
    matches = {
        target: direct_match(target, function_name, rows, columns)
        for target in TARGET_FIELD_KEYWORDS
    }
    revenue = direct_revenue_match(function_name, rows, columns)
    matches["r_and_d_expense_ratio"] = derive_ratio_match(
        "r_and_d_expense_ratio",
        matches["r_and_d_expense"],
        revenue,
        function_name,
    )
    matches["capex_ratio"] = derive_ratio_match("capex_ratio", matches["capex"], revenue, function_name)
    return matches


def direct_revenue_match(function_name: str, rows: list[dict[str, Any]], columns: list[str]) -> dict[str, Any] | None:
    column = first_matching_column(columns, REVENUE_KEYWORDS)
    if column:
        for row in rows:
            value = row.get(column)
            if safe_float(value) is not None:
                period, period_confidence = bind_period(row)
                return normalize_match({
                    "matched": True,
                    "source_function": function_name,
                    "source_column": column,
                    "source_row_name": None,
                    "source_column_or_row": column,
                    "source_period": period,
                    "value": json_safe(value),
                    "unit": "raw_statement_unit",
                    "confidence": "medium",
                    "period_confidence": period_confidence,
                    "value_confidence": "medium",
                    "notes": "revenue denominator matched by column name",
                })
    names = row_name_columns(columns)
    for row in find_rows_by_keywords(rows, columns, REVENUE_KEYWORDS):
        source_period, value = latest_period_value(row, columns)
        if safe_float(value) is not None:
            period_confidence = "low" if not source_period else ("medium" if source_period in columns else "high")
            return normalize_match({
                "matched": True,
                "source_function": function_name,
                "source_column": source_period if source_period in columns else None,
                "source_row_name": row_text(row, names),
                "source_column_or_row": source_period if source_period in columns else row_text(row, names),
                "source_period": source_period,
                "value": json_safe(value),
                "unit": "raw_statement_unit",
                "confidence": "medium",
                "period_confidence": period_confidence,
                "value_confidence": "medium",
                "notes": "revenue denominator matched by row name",
            })
    return None


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
    shape = frame_shape(frame_or_records, row_list)
    limited_rows = [json_safe(row) for row in row_list[:limit_rows]]
    return {
        "statement_type": statement_type,
        "function_name": function_name,
        "success": True,
        "error": None,
        "shape": shape,
        "columns_full": columns,
        "dtypes": frame_dtypes(frame_or_records, columns),
        "head_rows": limited_rows,
        "detected_report_periods": detect_periods(columns, row_list),
        "detected_field_candidates": detect_field_candidates(row_list, columns),
        "target_field_matches": detect_target_field_matches(function_name, row_list, columns),
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
        "target_field_matches": {
            target: make_missing_match(target, function_name)
            for target in ALL_TARGET_FIELDS
        },
        "sample_rows_by_keywords": {},
    }


def call_variants(function_name: str, code: str) -> list[tuple[tuple[Any, ...], dict[str, Any]]]:
    if function_name == "stock_financial_report_sina":
        return [
            ((code,), {"indicator": "按年度"}),
            ((code,), {"indicator": "资产负债表"}),
            ((code,), {"indicator": "利润表"}),
            ((code,), {"indicator": "现金流量表"}),
            ((code,), {}),
            ((), {"stock": code}),
            ((), {"symbol": code}),
        ]
    if function_name == "stock_financial_abstract":
        return [((), {"symbol": code}), ((code,), {})]
    return [((), {"symbol": code}), ((code,), {})]


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
    for args, kwargs in call_variants(function_name, code):
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
        "schema_version": "financial_statement_probe.v1",
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
    parser.add_argument("--output-dir", default="data/financial_probe")
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
