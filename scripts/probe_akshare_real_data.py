# -*- coding: utf-8 -*-
"""Probe AkShare real A-share data structures and save offline samples.

This script does not run the fundamental pipeline and does not produce trading
advice. It only records public data interface shapes for later connector work.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def _market_prefix(code: str) -> str:
    return "sh" if code.startswith(("60", "68", "9")) else "sz"


def _eastmoney_secid(code: str) -> str:
    market_id = "1" if code.startswith(("60", "68", "9")) else "0"
    return f"{market_id}.{code}"


def _plain(code: str) -> str:
    return code


def _prefixed(code: str) -> str:
    return f"{_market_prefix(code)}{code}"


def _exchange_prefixed(code: str) -> str:
    return f"{_market_prefix(code).upper()}{code}"


STOCK_NAME_BY_CODE = {
    "002050": "三花智控",
    "000426": "兴业银锡",
    "300308": "中际旭创",
    "002371": "北方华创",
    "601899": "紫金矿业",
}


@dataclass(frozen=True)
class Candidate:
    category: str
    function_name: str
    args_builder: Callable[[str], tuple[Any, ...]]
    kwargs_builder: Callable[[str], dict[str, Any]]
    notes: str
    commodity: str | None = None
    symbol_used: str | None = None
    symbol_formatter: str | None = None


def _args_plain(code: str) -> tuple[Any, ...]:
    return (_plain(code),)


def _args_prefixed(code: str) -> tuple[Any, ...]:
    return (_prefixed(code),)


def _args_exchange_prefixed(code: str) -> tuple[Any, ...]:
    return (_exchange_prefixed(code),)


def _args_stock_name(code: str) -> tuple[Any, ...]:
    return (STOCK_NAME_BY_CODE.get(code, code),)


def _args_none(_: str) -> tuple[Any, ...]:
    return ()


def _kwargs_empty(_: str) -> dict[str, Any]:
    return {}


def _kwargs_symbol(code: str) -> dict[str, Any]:
    return {"symbol": _plain(code)}


def _kwargs_prefixed_symbol(code: str) -> dict[str, Any]:
    return {"symbol": _prefixed(code)}


def _kwargs_exchange_prefixed_symbol(code: str) -> dict[str, Any]:
    return {"symbol": _exchange_prefixed(code)}


def _kwargs_secid_symbol(code: str) -> dict[str, Any]:
    return {"symbol": _eastmoney_secid(code)}


def _kwargs_stock_name_symbol(code: str) -> dict[str, Any]:
    return {"symbol": STOCK_NAME_BY_CODE.get(code, code)}


def _kwargs_indicator_year(_: str) -> dict[str, Any]:
    return {"indicator": "按年度"}


def _kwargs_baidu_total_value(code: str) -> dict[str, Any]:
    return {"symbol": _plain(code), "indicator": "总市值", "period": "近一年"}


def _kwargs_baidu_pe(code: str) -> dict[str, Any]:
    return {"symbol": _plain(code), "indicator": "市盈率", "period": "近一年"}


def _kwargs_baidu_pb(code: str) -> dict[str, Any]:
    return {"symbol": _plain(code), "indicator": "市净率", "period": "近一年"}


def _kwargs_qh_symbol(symbol: str) -> Callable[[str], dict[str, Any]]:
    def _builder(_: str) -> dict[str, Any]:
        return {"symbol": symbol}

    return _builder


def _kwargs_futures_vars(vars_list: list[str]) -> Callable[[str], dict[str, Any]]:
    def _builder(_: str) -> dict[str, Any]:
        return {"vars_list": vars_list}

    return _builder


def _kwargs_foreign_symbols(symbols: list[str]) -> Callable[[str], dict[str, Any]]:
    def _builder(_: str) -> dict[str, Any]:
        return {"symbol": symbols}

    return _builder


def _kwargs_static_symbol(symbol: str) -> Callable[[str], dict[str, Any]]:
    def _builder(_: str) -> dict[str, Any]:
        return {"symbol": symbol}

    return _builder


def _kwargs_static_contract(symbol: str) -> Callable[[str], dict[str, Any]]:
    def _builder(_: str) -> dict[str, Any]:
        return {"contract": symbol}

    return _builder


def _kwargs_static_variety(symbol: str) -> Callable[[str], dict[str, Any]]:
    def _builder(_: str) -> dict[str, Any]:
        return {"symbol": symbol}

    return _builder


def _args_static_symbol(symbol: str) -> Callable[[str], tuple[Any, ...]]:
    def _builder(_: str) -> tuple[Any, ...]:
        return (symbol,)

    return _builder


def _commodity_symbol_candidates() -> list[Candidate]:
    specs = {
        "copper": ["CU", "cu", "\u6caa\u94dc", "\u94dc", "CU0", "cu0", "SHFE_CU"],
        "tin": ["SN", "sn", "\u6caa\u9521", "\u9521", "SN0", "sn0", "SHFE_SN"],
    }
    functions = [
        ("futures_zh_spot", _args_none, _kwargs_static_symbol, "symbol_kw"),
        ("futures_zh_daily_sina", _args_none, _kwargs_static_symbol, "symbol_kw"),
        ("futures_main_sina", _args_none, _kwargs_static_symbol, "symbol_kw"),
        ("futures_hist_em", _args_none, _kwargs_static_symbol, "symbol_kw"),
        ("futures_hist_daily_em", _args_none, _kwargs_static_symbol, "symbol_kw"),
        ("futures_hist_daily_sina", _args_none, _kwargs_static_symbol, "symbol_kw"),
        ("futures_shfe_daily", _args_none, _kwargs_static_symbol, "symbol_kw"),
        ("get_shfe_daily", _args_none, _kwargs_static_symbol, "symbol_kw"),
        ("futures_spot_price_previous", _args_none, _kwargs_static_variety, "symbol_kw"),
        ("futures_spot_stock", _args_none, _kwargs_static_symbol, "symbol_kw"),
        ("futures_spot_sys", _args_none, _kwargs_static_symbol, "symbol_kw"),
        ("futures_zh_realtime", _args_none, _kwargs_static_symbol, "symbol_kw"),
    ]
    candidates: list[Candidate] = []
    for commodity, symbols in specs.items():
        for symbol in symbols:
            for function_name, args_builder, kwargs_factory, formatter in functions:
                candidates.append(
                    Candidate(
                        "commodity_prices",
                        function_name,
                        args_builder,
                        kwargs_factory(symbol),
                        f"Fresh domestic {commodity} probe using {function_name} with symbol={symbol}.",
                        commodity=commodity,
                        symbol_used=symbol,
                        symbol_formatter=formatter,
                    )
                )
        for symbol in symbols:
            candidates.append(
                Candidate(
                    "commodity_prices",
                    "get_shfe_daily",
                    _args_static_symbol(symbol),
                    _kwargs_empty,
                    f"Fresh domestic {commodity} probe using get_shfe_daily positional symbol={symbol}.",
                    commodity=commodity,
                    symbol_used=symbol,
                    symbol_formatter="positional_symbol",
                )
            )
            candidates.append(
                Candidate(
                    "commodity_prices",
                    "futures_contract_detail",
                    _args_none,
                    _kwargs_static_contract(symbol),
                    f"Fresh domestic {commodity} contract-detail probe using contract={symbol}.",
                    commodity=commodity,
                    symbol_used=symbol,
                    symbol_formatter="contract_kw",
                )
            )
    return candidates


CANDIDATE_FUNCTIONS: dict[str, list[Candidate]] = {
    "basic_info": [
        Candidate("basic_info", "stock_individual_info_em", _args_none, _kwargs_symbol, "Eastmoney single-stock info."),
        Candidate("basic_info", "stock_profile_cninfo", _args_none, _kwargs_symbol, "CNInfo company profile."),
        Candidate("basic_info", "stock_individual_basic_info_xq", _args_none, _kwargs_prefixed_symbol, "Xueqiu basic info, prefixed symbol."),
    ],
    "financial_indicator": [
        Candidate("financial_indicator", "stock_financial_analysis_indicator", _args_none, _kwargs_symbol, "Sina financial indicators."),
        Candidate("financial_indicator", "stock_financial_abstract", _args_none, _kwargs_symbol, "Financial abstract if available."),
        Candidate("financial_indicator", "stock_financial_report_sina", _args_plain, _kwargs_indicator_year, "Sina financial report by annual indicator."),
    ],
    "valuation": [
        Candidate("valuation", "stock_zh_a_spot_em", _args_none, _kwargs_empty, "Eastmoney A-share spot table."),
        Candidate("valuation", "stock_sh_a_spot_em", _args_none, _kwargs_empty, "Eastmoney Shanghai A-share spot table."),
        Candidate("valuation", "stock_sz_a_spot_em", _args_none, _kwargs_empty, "Eastmoney Shenzhen A-share spot table."),
        Candidate("valuation", "stock_kc_a_spot_em", _args_none, _kwargs_empty, "Eastmoney STAR board spot table."),
        Candidate("valuation", "stock_cy_a_spot_em", _args_none, _kwargs_empty, "Eastmoney ChiNext spot table."),
        Candidate("valuation", "stock_individual_spot_xq", _args_none, _kwargs_prefixed_symbol, "Xueqiu individual spot."),
        Candidate("valuation", "stock_bid_ask_em", _args_none, _kwargs_secid_symbol, "Eastmoney bid/ask by secid."),
        Candidate("valuation", "stock_a_ttm_lyr", _args_none, _kwargs_empty, "Legulegu A-share PE table."),
        Candidate("valuation", "stock_a_all_pb", _args_none, _kwargs_empty, "Legulegu A-share PB table."),
        Candidate("valuation", "stock_a_gxl_lg", _args_none, _kwargs_empty, "Legulegu dividend yield table."),
        Candidate("valuation", "stock_value_em", _args_none, _kwargs_symbol, "Eastmoney single-stock value analysis."),
        Candidate("valuation", "stock_zh_valuation_baidu", _args_none, _kwargs_baidu_total_value, "Baidu valuation total market value."),
        Candidate("valuation", "stock_zh_valuation_baidu", _args_none, _kwargs_baidu_pe, "Baidu valuation PE."),
        Candidate("valuation", "stock_zh_valuation_baidu", _args_none, _kwargs_baidu_pb, "Baidu valuation PB."),
        Candidate("valuation", "stock_zh_valuation_comparison_em", _args_none, _kwargs_exchange_prefixed_symbol, "Eastmoney valuation comparison."),
    ],
    "business_composition": [
        Candidate("business_composition", "stock_zygc_em", _args_none, _kwargs_symbol, "Eastmoney main business composition."),
        Candidate("business_composition", "stock_zygc_em", _args_none, _kwargs_prefixed_symbol, "Eastmoney main business composition, lowercase prefixed symbol."),
        Candidate("business_composition", "stock_zygc_em", _args_none, _kwargs_exchange_prefixed_symbol, "Eastmoney main business composition, exchange-prefixed symbol."),
        Candidate("business_composition", "stock_zygc_em", _args_none, _kwargs_stock_name_symbol, "Eastmoney main business composition, stock name symbol."),
        Candidate("business_composition", "stock_zygc_ym", _args_none, _kwargs_symbol, "YiMai main business composition if available."),
        Candidate("business_composition", "stock_zygc_ym", _args_none, _kwargs_prefixed_symbol, "YiMai main business composition, lowercase prefixed symbol."),
        Candidate("business_composition", "stock_zygc_ym", _args_none, _kwargs_stock_name_symbol, "YiMai main business composition, stock name symbol."),
        Candidate("business_composition", "stock_main_business_cninfo", _args_none, _kwargs_symbol, "CNInfo main business composition."),
        Candidate("business_composition", "stock_main_business_cninfo", _args_none, _kwargs_prefixed_symbol, "CNInfo main business composition, lowercase prefixed symbol."),
        Candidate("business_composition", "stock_main_business_cninfo", _args_none, _kwargs_stock_name_symbol, "CNInfo main business composition, stock name symbol."),
    ],
    "commodity_prices": [
        Candidate("commodity_prices", "spot_price_table_qh", _args_none, _kwargs_empty, "Qihuo commodity spot price table."),
        Candidate("commodity_prices", "spot_price_qh", _args_none, _kwargs_qh_symbol("铜"), "Qihuo spot price for copper."),
        Candidate("commodity_prices", "spot_price_qh", _args_none, _kwargs_qh_symbol("铝"), "Qihuo spot price for aluminum."),
        Candidate("commodity_prices", "spot_price_qh", _args_none, _kwargs_qh_symbol("锡"), "Qihuo spot price for tin."),
        Candidate("commodity_prices", "spot_price_qh", _args_none, _kwargs_qh_symbol("黄金"), "Qihuo spot price for gold."),
        Candidate("commodity_prices", "spot_price_qh", _args_none, _kwargs_qh_symbol("白银"), "Qihuo spot price for silver."),
        Candidate("commodity_prices", "spot_price_qh", _args_none, _kwargs_qh_symbol("钼"), "Qihuo spot price for molybdenum."),
        Candidate("commodity_prices", "spot_price_qh", _args_none, _kwargs_qh_symbol("钴"), "Qihuo spot price for cobalt."),
        Candidate("commodity_prices", "spot_price_qh", _args_none, _kwargs_qh_symbol("稀土"), "Qihuo spot price for rare earth."),
        Candidate("commodity_prices", "spot_silver_benchmark_sge", _args_none, _kwargs_empty, "Shanghai Gold Exchange silver benchmark."),
        Candidate("commodity_prices", "spot_golden_benchmark_sge", _args_none, _kwargs_empty, "Shanghai Gold Exchange gold benchmark."),
        Candidate("commodity_prices", "spot_quotations_sge", _args_none, _kwargs_qh_symbol("Au99.99"), "Shanghai Gold Exchange gold quotation."),
        Candidate("commodity_prices", "spot_quotations_sge", _args_none, _kwargs_qh_symbol("Ag99.99"), "Shanghai Gold Exchange silver quotation."),
        Candidate("commodity_prices", "futures_spot_price", _args_none, _kwargs_futures_vars(["CU", "AL", "SN", "AU", "AG"]), "Domestic futures spot price for core metals."),
        Candidate("commodity_prices", "futures_spot_price_daily", _args_none, _kwargs_futures_vars(["CU", "AL", "SN", "AU", "AG"]), "Domestic futures spot price daily for core metals."),
        Candidate("commodity_prices", "futures_zh_realtime", _args_none, _kwargs_qh_symbol("铜"), "Domestic futures realtime copper probe."),
        Candidate("commodity_prices", "futures_zh_realtime", _args_none, _kwargs_qh_symbol("铝"), "Domestic futures realtime aluminum probe."),
        Candidate("commodity_prices", "futures_foreign_commodity_realtime", _args_none, _kwargs_foreign_symbols(["CAD", "AHD", "SND", "XAU", "XAG"]), "Foreign commodity realtime metals probe."),
        *_commodity_symbol_candidates(),
    ],
    "news": [
        Candidate("news", "stock_news_em", _args_none, _kwargs_symbol, "Eastmoney stock news."),
        Candidate("news", "stock_notice_report", _args_none, _kwargs_symbol, "Stock notices if available."),
        Candidate("news", "stock_zh_a_alerts_cls", _args_none, _kwargs_empty, "CLS A-share alerts table."),
    ],
}


def normalize_code(code: str) -> str:
    digits = "".join(ch for ch in str(code) if ch.isdigit())
    if len(digits) < 6:
        raise ValueError(f"Invalid stock code: {code!r}")
    return digits[-6:]


def serialize_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): serialize_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialize_value(item) for item in value]
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    return str(value)


DATE_COLUMN_HINTS = (
    "date",
    "datetime",
    "time",
    "\u65e5\u671f",
    "\u4ea4\u6613\u65e5\u671f",
    "\u884c\u60c5\u65f6\u95f4",
    "\u65f6\u95f4",
)

PRICE_COLUMN_HINTS = (
    "\u6700\u65b0\u4ef7",
    "\u6536\u76d8\u4ef7",
    "\u7ed3\u7b97\u4ef7",
    "\u73b0\u8d27\u4ef7\u683c",
    "\u73b0\u8d27\u4ef7",
    "spot_price",
    "price",
    "close",
    "settle",
    "last_price",
)


def _column_matches(column: str, hints: tuple[str, ...]) -> bool:
    lowered = str(column).lower()
    return any(str(hint).lower() in lowered for hint in hints)


def _parse_probe_date(value: Any) -> date | None:
    if value is None:
        return None
    if hasattr(value, "date") and not isinstance(value, date):
        try:
            return value.date()
        except Exception:
            pass
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    patterns = ("%Y-%m-%d", "%Y%m%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S")
    for pattern in patterns:
        try:
            return datetime.strptime(text[:19], pattern).date()
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(text.replace("/", "-"))
        return parsed.date()
    except Exception:
        return None


def _is_number_like(value: Any) -> bool:
    try:
        number = float(str(value).replace(",", ""))
    except Exception:
        return False
    return math.isfinite(number)


def _detect_table_metadata(rows: list[dict[str, Any]], columns: list[str]) -> dict[str, Any]:
    detected_date_columns = [column for column in columns if _column_matches(column, DATE_COLUMN_HINTS)]
    detected_price_columns = [
        column
        for column in columns
        if _column_matches(column, PRICE_COLUMN_HINTS)
        or any(_is_number_like(row.get(column)) for row in rows[:20] if isinstance(row, dict))
    ]
    latest_date: date | None = None
    for row in rows:
        if not isinstance(row, dict):
            continue
        for column in detected_date_columns:
            parsed = _parse_probe_date(row.get(column))
            if parsed and (latest_date is None or parsed > latest_date):
                latest_date = parsed
    today = datetime.now().date()
    freshness_days = (today - latest_date).days if latest_date else None
    return {
        "detected_date_columns": detected_date_columns,
        "detected_price_columns": detected_price_columns,
        "latest_date_detected": latest_date.isoformat() if latest_date else None,
        "freshness_days": freshness_days,
        "is_fresh_candidate": freshness_days is not None and 0 <= freshness_days <= 7,
        "source_notes": [],
    }


FINANCIAL_ABSTRACT_KEYWORDS = (
    "营业总收入",
    "营业成本",
    "归母净利润",
    "净利润",
    "扣非净利润",
    "毛利率",
    "净利率",
    "ROE",
    "净资产收益率",
    "经营现金流",
    "经营活动现金流",
    "资产负债率",
    "存货",
    "应收账款",
)

FINANCIAL_ABSTRACT_KEYWORDS = FINANCIAL_ABSTRACT_KEYWORDS + (
    "营业总收入",
    "营业成本",
    "归母净利润",
    "净利润",
    "扣非净利润",
    "毛利率",
    "净利率",
    "净资产收益率",
    "经营现金",
    "经营活动现金",
    "资产负债率",
    "存货",
    "应收账款",
)


def _period_columns(columns: list[str]) -> list[str]:
    return [column for column in columns if re.fullmatch(r"(?:19|20)\d{6}", column)]


def _first_existing_column(columns: list[str], candidates: tuple[str, ...]) -> str | None:
    column_set = set(columns)
    for candidate in candidates:
        if candidate in column_set:
            return candidate
    return None


def _unique_non_empty(values: Any) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _compact_row(row: dict[str, Any], period_columns: list[str]) -> dict[str, Any]:
    base_columns = [column for column in row.keys() if column not in period_columns]
    selected_periods = period_columns[:8]
    selected = base_columns + [column for column in selected_periods if column in row]
    return {column: row.get(column) for column in selected}


def _keyword_rows(frame: Any, indicator_column: str | None, option_column: str | None, period_cols: list[str]) -> dict[str, list[dict[str, Any]]]:
    if indicator_column is None:
        return {}
    rows = serialize_value(frame.to_dict(orient="records"))
    out: dict[str, list[dict[str, Any]]] = {}
    for keyword in FINANCIAL_ABSTRACT_KEYWORDS:
        matches = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            haystack_parts = [str(row.get(indicator_column, ""))]
            if option_column:
                haystack_parts.append(str(row.get(option_column, "")))
            haystack = " ".join(haystack_parts).lower()
            if keyword.lower() in haystack:
                matches.append(_compact_row(row, period_cols))
        if matches:
            out[keyword] = matches
    return out


def summarize_payload(payload: Any, limit_rows: int) -> dict[str, Any]:
    if hasattr(payload, "head") and hasattr(payload, "to_dict"):
        head = payload.head(limit_rows)
        columns = [str(col) for col in getattr(payload, "columns", [])]
        records_full = serialize_value(payload.to_dict(orient="records"))
        indicator_column = _first_existing_column(columns, ("指标",))
        option_column = _first_existing_column(columns, ("选项",))
        period_cols = _period_columns(columns)
        summary = {
            "payload_type": f"{type(payload).__module__}.{type(payload).__name__}",
            "columns": columns,
            "columns_full": columns,
            "shape": list(getattr(payload, "shape", [])),
            "row_count": int(getattr(payload, "shape", [0])[0]) if getattr(payload, "shape", []) else 0,
            "dtypes": {str(k): str(v) for k, v in getattr(payload, "dtypes", {}).items()},
            "head": serialize_value(head.to_dict(orient="records")),
            "head_rows": serialize_value(head.to_dict(orient="records")),
            "period_columns": period_cols,
            **_detect_table_metadata(records_full if isinstance(records_full, list) else [], columns),
        }
        if indicator_column is not None:
            summary["indicator_names_full"] = _unique_non_empty(payload[indicator_column].tolist())
        if option_column is not None:
            summary["option_names_full"] = _unique_non_empty(payload[option_column].tolist())
        keyword_rows = _keyword_rows(payload, indicator_column, option_column, period_cols)
        if keyword_rows:
            summary["sample_rows_by_keywords"] = keyword_rows
        return summary
    if isinstance(payload, list):
        columns = sorted({str(k) for row in payload[:limit_rows] if isinstance(row, dict) for k in row.keys()})
        head_rows = serialize_value(payload[:limit_rows])
        rows_full = serialize_value(payload)
        return {
            "payload_type": "list",
            "columns": columns,
            "columns_full": columns,
            "shape": [len(payload)],
            "row_count": len(payload),
            "dtypes": {},
            "head": head_rows,
            "head_rows": head_rows,
            **_detect_table_metadata(rows_full if isinstance(rows_full, list) else [], columns),
        }
    if isinstance(payload, dict):
        columns = [str(k) for k in payload.keys()]
        head_rows = [serialize_value(payload)]
        return {
            "payload_type": "dict",
            "columns": columns,
            "columns_full": columns,
            "shape": [1],
            "row_count": 1,
            "dtypes": {},
            "head": head_rows,
            "head_rows": head_rows,
            **_detect_table_metadata(head_rows, columns),
        }
    return {
        "payload_type": f"{type(payload).__module__}.{type(payload).__name__}",
        "columns": [],
        "columns_full": [],
        "shape": [],
        "row_count": None,
        "dtypes": {},
        "head": [serialize_value(payload)],
        "head_rows": [serialize_value(payload)],
        **_detect_table_metadata([], []),
    }


def run_candidate(ak: Any, candidate: Candidate, code: str, limit_rows: int) -> dict[str, Any]:
    base = {
        "category": candidate.category,
        "function_name": candidate.function_name,
        "commodity": candidate.commodity,
        "symbol_used": candidate.symbol_used,
        "symbol_formatter": candidate.symbol_formatter,
        "notes": candidate.notes,
        "success": False,
        "error": None,
    }
    if not hasattr(ak, candidate.function_name):
        return {
            **base,
            "error": "function_not_found",
            "call_args": serialize_value(candidate.args_builder(code)),
            "call_kwargs": serialize_value(candidate.kwargs_builder(code)),
            "columns": [],
            "columns_full": [],
            "shape": [],
            "row_count": None,
            "dtypes": {},
            "head": [],
            "head_rows": [],
            **_detect_table_metadata([], []),
        }
    try:
        fn = getattr(ak, candidate.function_name)
        args = candidate.args_builder(code)
        kwargs = candidate.kwargs_builder(code)
        payload = fn(*args, **kwargs)
        return {
            **base,
            "success": True,
            "error": None,
            "call_args": serialize_value(args),
            "call_kwargs": serialize_value(kwargs),
            **summarize_payload(payload, limit_rows),
        }
    except Exception as exc:
        return {
            **base,
            "error": f"{type(exc).__name__}: {exc}",
            "call_args": serialize_value(candidate.args_builder(code)),
            "call_kwargs": serialize_value(candidate.kwargs_builder(code)),
            "payload_type": None,
            "columns": [],
            "columns_full": [],
            "shape": [],
            "row_count": None,
            "dtypes": {},
            "head": [],
            "head_rows": [],
            **_detect_table_metadata([], []),
        }


def probe_code(ak: Any, code: str, limit_rows: int) -> dict[str, Any]:
    normalized = normalize_code(code)
    categories = {}
    for category, candidates in CANDIDATE_FUNCTIONS.items():
        categories[category] = [run_candidate(ak, candidate, normalized, limit_rows) for candidate in candidates]
    return {
        "schema_version": "akshare_probe.v1",
        "stock_code": normalized,
        "generated_at": _now_iso(),
        "akshare_version": getattr(ak, "__version__", "unknown"),
        "limit_rows": limit_rows,
        "categories": categories,
    }


def write_markdown_summary(probe: dict[str, Any], output_path: Path) -> None:
    lines = [
        f"# AkShare Probe {probe['stock_code']}",
        "",
        f"- generated_at: `{probe['generated_at']}`",
        f"- akshare_version: `{probe['akshare_version']}`",
        f"- limit_rows: `{probe['limit_rows']}`",
        "",
        "| category | function | success | shape | columns | error |",
        "|---|---|---:|---|---|---|",
    ]
    for category, results in probe["categories"].items():
        for result in results:
            columns = ", ".join(result.get("columns", [])[:12])
            shape = result.get("shape", [])
            error = str(result.get("error") or "").replace("|", "\\|")
            lines.append(
                f"| {category} | `{result['function_name']}` | {result['success']} | {shape} | {columns} | {error} |"
            )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe AkShare real data structures for offline connector work.")
    parser.add_argument("--codes", nargs="+", required=True, help="A-share 6 digit stock codes")
    parser.add_argument("--output-dir", default="data/real_probe", help="Directory for probe JSON/Markdown")
    parser.add_argument("--limit-rows", type=int, default=5, help="Rows to keep from each returned table")
    args = parser.parse_args()

    try:
        import akshare as ak  # type: ignore
    except Exception as exc:
        print(f"akshare import failed: {type(exc).__name__}: {exc}")
        print("Install locally with: py -m pip install akshare")
        return 1

    print(f"akshare version: {getattr(ak, '__version__', 'unknown')}")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for code in args.codes:
        probe = probe_code(ak, code, max(args.limit_rows, 0))
        json_path = output_dir / f"probe_{probe['stock_code']}.json"
        md_path = output_dir / f"probe_{probe['stock_code']}.md"
        json_path.write_text(json.dumps(probe, ensure_ascii=False, indent=2), encoding="utf-8")
        write_markdown_summary(probe, md_path)
        success_count = sum(
            1 for results in probe["categories"].values() for result in results if result.get("success")
        )
        print(f"{probe['stock_code']}: wrote {json_path} and {md_path}; success_count={success_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
