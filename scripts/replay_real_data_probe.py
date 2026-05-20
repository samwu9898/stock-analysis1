# -*- coding: utf-8 -*-
"""Replay an offline AkShare probe and suggest connector mapping candidates.

This is an offline audit helper. It does not run the fundamental pipeline, does
not modify RealDataConnector, and does not produce trading advice.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


FIELD_HINTS: dict[str, dict[str, tuple[str, ...]]] = {
    "basic_info": {
        "stock_name": ("stock_name", "name", "简称", "名称", "绠", "鍚"),
        "industry": ("industry", "行业", "琛屼笟"),
        "main_business": ("main_business", "主营", "经营范围", "涓昏惀", "缁忚惀"),
        "listing_date": ("listing_date", "上市", "涓婂競"),
    },
    "financial_indicator": {
        "revenue_yoy": ("revenue_yoy", "收入同比", "澧為暱", "growth"),
        "net_profit_yoy": ("net_profit_yoy", "利润同比", "鍑€鍒╂鼎", "growth"),
        "gross_margin": ("gross_margin", "毛利率", "姣涘埄", "瘺"),
        "roe": ("roe", "ROE", "净资产收益", "鍑€璧勪骇"),
        "operating_cashflow": ("operating_cashflow", "经营现金", "缁忚惀鐜伴噾"),
        "debt_to_asset": ("debt_to_asset", "资产负债", "璧勪骇璐熷€"),
        "inventory": ("inventory", "存货", "瀛樿揣"),
        "accounts_receivable": ("accounts_receivable", "应收", "搴旀敹"),
    },
    "valuation": {
        "pe_ttm": ("pe_ttm", "PE", "市盈率", "TTM", "甯傜泩"),
        "pb": ("pb", "PB", "市净率", "甯傚噣"),
        "ps": ("ps", "PS", "市销率", "甯傞攢"),
        "market_cap": ("market_cap", "总市值", "市值", "鎬诲競鍊", "总值"),
        "dividend_yield": ("dividend_yield", "dividend", "股息率", "股息", "鑲℃伅"),
    },
    "business_composition": {
        "segment_name": ("segment_name", "主营构成", "业务名称", "项目名称", "分类", "产品", "行业", "涓昏惀鏋勬垚"),
        "revenue": ("revenue", "主营收入", "营业收入", "收入", "涓昏惀鏀跺叆", "钀ヤ笟鏀跺叆"),
        "revenue_ratio": ("revenue_ratio", "收入比例", "收入占比", "占比", "鏀跺叆姣斾緥", "鍗犳瘮"),
        "gross_margin": ("gross_margin", "毛利率", "姣涘埄"),
        "period": ("period", "报告期", "日期", "期间", "年度"),
    },
    "commodity_prices": {
        "commodity_name": ("commodity", "symbol", "name", "品种", "商品", "名称", "合约"),
        "price": ("price", "close", "settle", "价格", "现货价", "最新价", "收盘价", "结算价"),
        "change": ("change", "pct", "涨跌", "涨跌幅"),
        "unit": ("unit", "单位"),
        "date": ("date", "time", "日期", "时间"),
        "market": ("market", "exchange", "市场", "交易所"),
    },
    "news": {
        "title": ("title", "标题", "鏍囬"),
        "publish_time": ("publish_time", "日期", "时间", "鍙戝竷"),
        "source": ("source", "来源", "鏉ユ簮"),
        "url": ("url", "链接", "閾炬帴"),
        "summary": ("summary", "摘要", "内容", "鍐呭"),
    },
}


FINANCIAL_ABSTRACT_TARGETS: dict[str, tuple[str, ...]] = {
    "revenue_yoy": ("营业总收入", "钀ヤ笟鎬绘敹鍏"),
    "net_profit_yoy": ("归母净利润", "净利润", "褰掓瘝鍑€鍒╂鼎", "鍑€鍒╂鼎"),
    "deducted_net_profit": ("扣非净利润", "鎵ｉ潪鍑€鍒╂鼎"),
    "gross_margin": ("营业总收入", "营业成本", "毛利率", "钀ヤ笟鎬绘敹鍏", "钀ヤ笟鎴愭湰", "姣涘埄"),
    "net_margin": ("营业总收入", "净利润", "净利率", "钀ヤ笟鎬绘敹鍏", "鍑€鍒╂鼎", "鍑€鍒╃巼"),
    "roe": ("ROE", "净资产收益", "鍑€璧勪骇"),
    "operating_cashflow": ("经营现金", "缁忚惀鐜伴噾", "缁忚惀娲诲姩"),
    "debt_to_asset": ("资产负债率", "璧勪骇璐熷€"),
    "inventory": ("存货", "瀛樿揣"),
    "accounts_receivable": ("应收账款", "搴旀敹璐"),
}


COMMODITY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "silver": ("白银", "银", "AG", "Ag", "XAG", "silver"),
    "tin": ("锡", "SN", "Sn", "tin"),
    "copper": ("铜", "CU", "Cu", "CAD", "copper"),
    "gold": ("黄金", "金", "AU", "Au", "XAU", "gold"),
    "aluminum": ("铝", "AL", "Al", "AHD", "aluminum", "aluminium"),
    "molybdenum": ("钼", "MO", "molybdenum"),
    "cobalt": ("钴", "CO", "cobalt"),
    "rare_earth": ("稀土", "rare earth"),
}

COPPER_TIN = ("copper", "tin")


def load_probe(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def successful_functions(probe: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    return {
        category: [result for result in results if result.get("success")]
        for category, results in probe.get("categories", {}).items()
    }


def failed_functions(probe: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    return {
        category: [result for result in results if not result.get("success")]
        for category, results in probe.get("categories", {}).items()
    }


def _match_text(text: str, hints: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(str(hint).lower() in lowered for hint in hints)


def suggest_mappings(probe: dict[str, Any]) -> dict[str, Any]:
    suggestions: dict[str, Any] = {}
    for category, results in successful_functions(probe).items():
        category_suggestions = {}
        columns_by_function = {
            result["function_name"]: [str(col) for col in result.get("columns_full") or result.get("columns", [])]
            for result in results
        }
        all_columns = [(fn, col) for fn, cols in columns_by_function.items() for col in cols]
        for target_field, hints in FIELD_HINTS.get(category, {}).items():
            matches = [
                {"function_name": fn, "column": col}
                for fn, col in all_columns
                if _match_text(col, hints)
            ]
            category_suggestions[target_field] = matches[:8]
        suggestions[category] = {
            "successful_functions": [result["function_name"] for result in results],
            "field_candidates": category_suggestions,
        }
    return suggestions


def _field_candidate_summary(probe: dict[str, Any], category: str, target_fields: tuple[str, ...]) -> dict[str, Any]:
    suggestions = suggest_mappings(probe).get(category, {"successful_functions": [], "field_candidates": {}})
    field_candidates = suggestions.get("field_candidates", {})
    missing_fields = [field for field in target_fields if not field_candidates.get(field)]
    successful = successful_functions(probe).get(category, [])
    usable_successes = [
        {
            "function_name": item.get("function_name"),
            "notes": item.get("notes"),
            "shape": item.get("shape", []),
            "row_count": item.get("row_count"),
            "columns": item.get("columns_full") or item.get("columns", []),
            "head_rows": item.get("head_rows") or item.get("head", []),
            "call_kwargs": item.get("call_kwargs", {}),
            "empty_table": item.get("row_count") == 0 or item.get("shape") in ([0, 0], [0]),
        }
        for item in successful
    ]
    return {
        "successful_functions": suggestions.get("successful_functions", []),
        "usable_successes": usable_successes,
        "field_candidates": {field: field_candidates.get(field, []) for field in target_fields},
        "missing_fields": missing_fields,
    }


def valuation_candidate_summary(probe: dict[str, Any]) -> dict[str, Any]:
    return _field_candidate_summary(
        probe,
        "valuation",
        ("pe_ttm", "pb", "ps", "market_cap", "dividend_yield"),
    )


def business_composition_candidate_summary(probe: dict[str, Any]) -> dict[str, Any]:
    return _field_candidate_summary(
        probe,
        "business_composition",
        ("segment_name", "revenue", "revenue_ratio", "gross_margin", "period"),
    )


def _rows_as_text(rows: list[Any]) -> str:
    return " ".join(json.dumps(row, ensure_ascii=False) if isinstance(row, (dict, list)) else str(row) for row in rows)


def commodity_prices_summary(probe: dict[str, Any]) -> dict[str, Any]:
    successes = successful_functions(probe).get("commodity_prices", [])
    coverage: dict[str, list[str]] = {name: [] for name in COMMODITY_KEYWORDS}
    successful_details = []
    for item in successes:
        rows = item.get("head_rows") or item.get("head") or []
        columns = item.get("columns_full") or item.get("columns", [])
        haystack = " ".join([str(item.get("function_name")), str(item.get("notes")), " ".join(map(str, columns)), _rows_as_text(rows)])
        for commodity, keywords in COMMODITY_KEYWORDS.items():
            if _match_text(haystack, keywords):
                coverage[commodity].append(str(item.get("function_name")))
        successful_details.append(
            {
                "function_name": item.get("function_name"),
                "notes": item.get("notes"),
                "shape": item.get("shape", []),
                "row_count": item.get("row_count"),
                "columns": columns,
                "head_rows": rows,
                "call_kwargs": item.get("call_kwargs", {}),
                "empty_table": item.get("row_count") == 0 or item.get("shape") in ([0, 0], [0]),
            }
        )
    covered = {name: sorted(set(functions)) for name, functions in coverage.items() if functions}
    return {
        "successful_functions": [item.get("function_name") for item in successes],
        "successful_details": successful_details,
        "covered_commodities": covered,
        "missing_commodities": [name for name in COMMODITY_KEYWORDS if name not in covered],
        "strategy_types": ["resource_swing", "resource_core"] if covered else [],
        "connector_ready": False,
        "connector_ready_reason": "probe evidence only; RealDataConnector mapping requires a separate v2.1 design review",
    }


def _commodity_from_candidate(item: dict[str, Any]) -> str | None:
    commodity = item.get("commodity")
    if commodity in COPPER_TIN:
        return str(commodity)
    haystack = " ".join(
        [
            str(item.get("function_name")),
            str(item.get("notes")),
            str(item.get("symbol_used")),
            json.dumps(item.get("call_kwargs", {}), ensure_ascii=False),
            _rows_as_text(item.get("head_rows") or item.get("head") or []),
        ]
    )
    for name in COPPER_TIN:
        if _match_text(haystack, COMMODITY_KEYWORDS[name]):
            return name
    return None


def copper_tin_freshness_summary(probe: dict[str, Any]) -> dict[str, Any]:
    results = probe.get("categories", {}).get("commodity_prices", [])
    by_commodity: dict[str, list[dict[str, Any]]] = {name: [] for name in COPPER_TIN}
    for item in results:
        commodity = _commodity_from_candidate(item)
        if commodity not in by_commodity:
            continue
        detail = {
            "function_name": item.get("function_name"),
            "commodity": commodity,
            "symbol_used": item.get("symbol_used"),
            "symbol_formatter": item.get("symbol_formatter"),
            "success": bool(item.get("success")),
            "error": item.get("error"),
            "shape": item.get("shape", []),
            "row_count": item.get("row_count"),
            "detected_date_columns": item.get("detected_date_columns", []),
            "detected_price_columns": item.get("detected_price_columns", []),
            "latest_date_detected": item.get("latest_date_detected"),
            "freshness_days": item.get("freshness_days"),
            "is_fresh_candidate": bool(item.get("is_fresh_candidate")),
            "call_kwargs": item.get("call_kwargs", {}),
            "columns": item.get("columns_full") or item.get("columns", []),
            "source_notes": item.get("source_notes", []),
        }
        by_commodity[commodity].append(detail)

    best_candidates: dict[str, dict[str, Any] | None] = {}
    for commodity, items in by_commodity.items():
        fresh = [
            item
            for item in items
            if item.get("success") and item.get("is_fresh_candidate") and item.get("detected_price_columns")
        ]
        if fresh:
            best_candidates[commodity] = sorted(
                fresh,
                key=lambda item: (
                    item.get("freshness_days") if item.get("freshness_days") is not None else 999999,
                    str(item.get("function_name")),
                ),
            )[0]
        else:
            best_candidates[commodity] = None

    return {
        "commodities": by_commodity,
        "successful_functions": {
            commodity: sorted({str(item.get("function_name")) for item in items if item.get("success")})
            for commodity, items in by_commodity.items()
        },
        "fresh_candidates": {
            commodity: [
                item
                for item in items
                if item.get("success") and item.get("is_fresh_candidate") and item.get("detected_price_columns")
            ]
            for commodity, items in by_commodity.items()
        },
        "best_connector_v11_candidates": best_candidates,
        "no_fresh_domestic_source": [
            commodity for commodity, candidate in best_candidates.items() if candidate is None
        ],
        "missing_is_correct_if_no_fresh_source": True,
    }


def _matching_indicators(indicator_names: list[str], hints: tuple[str, ...]) -> list[str]:
    matches = []
    for name in indicator_names:
        if _match_text(str(name), hints):
            matches.append(str(name))
    return matches


def financial_abstract_summaries(probe: dict[str, Any]) -> list[dict[str, Any]]:
    summaries = []
    for result in successful_functions(probe).get("financial_indicator", []):
        if result.get("function_name") != "stock_financial_abstract":
            continue
        indicator_names = [str(item) for item in result.get("indicator_names_full", [])]
        target_mappings = {}
        missing_targets = []
        for target_field, hints in FINANCIAL_ABSTRACT_TARGETS.items():
            matches = _matching_indicators(indicator_names, hints)
            target_mappings[target_field] = {
                "status": "matched" if matches else "missing",
                "matched_indicators": matches,
                "hints": list(hints),
            }
            if not matches:
                missing_targets.append(target_field)
        summaries.append(
            {
                "function_name": result.get("function_name"),
                "shape": result.get("shape", []),
                "row_count": result.get("row_count"),
                "period_columns": result.get("period_columns", []),
                "indicator_names_full": indicator_names,
                "indicator_count": len(indicator_names),
                "sample_rows_by_keywords": result.get("sample_rows_by_keywords", {}),
                "target_mappings": target_mappings,
                "missing_targets": missing_targets,
            }
        )
    return summaries


def replay_probe(probe: dict[str, Any]) -> dict[str, Any]:
    success = successful_functions(probe)
    failed = failed_functions(probe)
    return {
        "stock_code": probe.get("stock_code"),
        "akshare_version": probe.get("akshare_version"),
        "generated_at": probe.get("generated_at"),
        "successful_blocks": {category: [item["function_name"] for item in items] for category, items in success.items()},
        "failed_blocks": {category: [item["function_name"] for item in items] for category, items in failed.items()},
        "function_not_found": {
            category: [item["function_name"] for item in items if item.get("error") == "function_not_found"]
            for category, items in failed.items()
        },
        "mapping_suggestions": suggest_mappings(probe),
        "financial_abstract": financial_abstract_summaries(probe),
        "valuation_candidates": valuation_candidate_summary(probe),
        "business_composition_candidates": business_composition_candidate_summary(probe),
        "commodity_prices": commodity_prices_summary(probe),
        "copper_tin_freshness": copper_tin_freshness_summary(probe),
    }


def _render_preview(items: list[Any], limit: int = 20) -> str:
    values = [str(item) for item in items]
    if not values:
        return "none"
    preview = ", ".join(values[:limit])
    omitted = len(values) - limit
    if omitted > 0:
        return f"{preview}, ... (+{omitted} more)"
    return preview


def _render_field_candidates(lines: list[str], detail: dict[str, Any]) -> None:
    for field, matches in detail.get("field_candidates", {}).items():
        rendered = ", ".join(f"{item['function_name']}.{item['column']}" for item in matches) or "none"
        lines.append(f"- {field}: {rendered}")


def format_summary(summary: dict[str, Any]) -> str:
    lines = [
        f"# Real Data Probe Replay {summary.get('stock_code')}",
        "",
        f"- akshare_version: `{summary.get('akshare_version')}`",
        f"- probe_generated_at: `{summary.get('generated_at')}`",
        "",
        "## Successful Functions",
    ]
    for category, names in summary["successful_blocks"].items():
        lines.append(f"- {category}: {', '.join(names) if names else 'none'}")
    lines.extend(["", "## Failed Functions"])
    for category, names in summary["failed_blocks"].items():
        lines.append(f"- {category}: {', '.join(names) if names else 'none'}")
    lines.extend(["", "## Mapping Suggestions"])
    for category, detail in summary["mapping_suggestions"].items():
        lines.append(f"### {category}")
        lines.append(f"- successful_functions: {', '.join(detail.get('successful_functions', [])) or 'none'}")
        _render_field_candidates(lines, detail)

    valuation = summary.get("valuation_candidates", {})
    if valuation:
        lines.extend(["", "## Valuation Candidate Summary"])
        lines.append(f"- successful_functions: {', '.join(valuation.get('successful_functions', [])) or 'none'}")
        _render_field_candidates(lines, valuation)
        lines.append(f"- missing_fields: {', '.join(valuation.get('missing_fields', [])) or 'none'}")
        for item in valuation.get("usable_successes", [])[:5]:
            lines.append(
                f"- sample {item.get('function_name')}: shape={item.get('shape')} empty={item.get('empty_table')} columns={_render_preview(item.get('columns', []), 10)}"
            )

    business = summary.get("business_composition_candidates", {})
    if business:
        lines.extend(["", "## Business Composition Candidate Summary"])
        lines.append(f"- successful_functions: {', '.join(business.get('successful_functions', [])) or 'none'}")
        _render_field_candidates(lines, business)
        lines.append(f"- missing_fields: {', '.join(business.get('missing_fields', [])) or 'none'}")
        for item in business.get("usable_successes", [])[:5]:
            lines.append(
                f"- sample {item.get('function_name')}: shape={item.get('shape')} empty={item.get('empty_table')} columns={_render_preview(item.get('columns', []), 10)}"
            )
            rows = item.get("head_rows", [])
            if rows:
                lines.append(f"  sample_rows: {_render_preview(rows, 2)}")

    commodity = summary.get("commodity_prices", {})
    if commodity:
        lines.extend(["", "## Commodity Prices Summary"])
        lines.append(f"- successful_functions: {', '.join(commodity.get('successful_functions', [])) or 'none'}")
        covered = commodity.get("covered_commodities", {})
        if covered:
            for name, functions in covered.items():
                lines.append(f"- {name}: {', '.join(functions)}")
        else:
            lines.append("- covered_commodities: none")
        lines.append(f"- missing_commodities: {', '.join(commodity.get('missing_commodities', [])) or 'none'}")
        lines.append(f"- strategy_types: {', '.join(commodity.get('strategy_types', [])) or 'none'}")
        lines.append(f"- connector_ready: {commodity.get('connector_ready')}")
        lines.append(f"- connector_ready_reason: {commodity.get('connector_ready_reason')}")
        for item in commodity.get("successful_details", [])[:5]:
            lines.append(
                f"- sample {item.get('function_name')}: shape={item.get('shape')} empty={item.get('empty_table')} columns={_render_preview(item.get('columns', []), 10)}"
            )

    freshness = summary.get("copper_tin_freshness", {})
    if freshness:
        lines.extend(["", "## Copper/Tin Freshness Candidate Summary"])
        for commodity in COPPER_TIN:
            items = freshness.get("commodities", {}).get(commodity, [])
            successful = freshness.get("successful_functions", {}).get(commodity, [])
            lines.append(f"### {commodity}")
            lines.append(f"- successful_functions: {', '.join(successful) if successful else 'none'}")
            if items:
                for item in items:
                    status = "fresh" if item.get("is_fresh_candidate") else "stale_or_unusable"
                    lines.append(
                        "- candidate "
                        f"{item.get('function_name')} symbol={item.get('symbol_used') or item.get('call_kwargs')} "
                        f"success={item.get('success')} status={status} "
                        f"latest_date={item.get('latest_date_detected')} freshness_days={item.get('freshness_days')} "
                        f"price_columns={_render_preview(item.get('detected_price_columns', []), 6)}"
                    )
            else:
                lines.append("- candidates: none")
            best = freshness.get("best_connector_v11_candidates", {}).get(commodity)
            if best:
                lines.append(
                    f"- best_connector_v1_1_candidate: {best.get('function_name')} symbol={best.get('symbol_used') or best.get('call_kwargs')} latest_date={best.get('latest_date_detected')}"
                )
            else:
                lines.append("- best_connector_v1_1_candidate: none")
        no_fresh = freshness.get("no_fresh_domestic_source", [])
        if no_fresh:
            lines.append(
                "- no_fresh_domestic_source: "
                + ", ".join(no_fresh)
                + "; keeping detailed freshness missing is correct."
            )

    if summary.get("financial_abstract"):
        lines.extend(["", "## Financial Abstract Wide Table"])
        for detail in summary["financial_abstract"]:
            lines.append(f"### {detail.get('function_name')}")
            lines.append(f"- shape: {detail.get('shape')}")
            lines.append(f"- row_count: {detail.get('row_count')}")
            lines.append(f"- period_columns: {_render_preview(detail.get('period_columns', []), 12)}")
            lines.append(f"- indicator_count: {detail.get('indicator_count')}")
            lines.append(f"- indicator_names_full: {_render_preview(detail.get('indicator_names_full', []), 30)}")
            lines.append("- target_field_mappings:")
            for target_field, mapping in detail.get("target_mappings", {}).items():
                matched = _render_preview(mapping.get("matched_indicators", []), 8)
                lines.append(f"  - {target_field}: {mapping.get('status')} ({matched})")
            missing = detail.get("missing_targets", [])
            lines.append(f"- missing_targets: {', '.join(missing) if missing else 'none'}")
            sample_rows = detail.get("sample_rows_by_keywords", {})
            if sample_rows:
                lines.append("- sample_rows_by_keywords:")
                for keyword, rows in sample_rows.items():
                    indicator_values = []
                    for row in rows:
                        if isinstance(row, dict):
                            indicator_values.append(row.get("指标") or row.get("鎸囨爣") or row.get("indicator") or row.get("项目") or row)
                    lines.append(f"  - {keyword}: {_render_preview(indicator_values, 5)}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay an offline AkShare probe JSON.")
    parser.add_argument("--input", required=True, help="Path to data/real_probe/probe_<code>.json")
    parser.add_argument("--output", help="Optional markdown output path")
    args = parser.parse_args()

    probe = load_probe(args.input)
    summary = replay_probe(probe)
    text = format_summary(summary)
    print(text)
    if args.output:
        output_path = Path(args.output)
    else:
        input_path = Path(args.input)
        output_path = input_path.with_name(input_path.name.replace("probe_", "replay_")).with_suffix(".md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
