# -*- coding: utf-8 -*-
"""Replay financial statement field probes into a mapping audit markdown file.

This script is offline-only. It reads probe JSON, writes markdown when requested,
and does not call AkShare or mutate pipeline outputs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


TARGET_FIELDS = (
    "inventory",
    "accounts_receivable",
    "contract_liabilities",
    "r_and_d_expense",
    "r_and_d_expense_ratio",
    "capex",
    "capex_ratio",
)

FIELD_LABELS = {
    "inventory": "inventory",
    "accounts_receivable": "accounts_receivable",
    "contract_liabilities": "contract_liabilities",
    "r_and_d_expense": "r_and_d_expense",
    "r_and_d_expense_ratio": "r_and_d_expense_ratio",
    "capex": "capex",
    "capex_ratio": "capex_ratio",
}

CAUTION_FIELDS = {"r_and_d_expense_ratio", "capex_ratio", "contract_liabilities"}
PERIOD_KEYS = ("报告日", "报告期", "报告日期", "日期", "截止日期", "REPORT_DATE", "date")


def load_probe(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def successful_functions(probe: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in probe.get("function_results", []) if item.get("success")]


def failed_functions(probe: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in probe.get("function_results", []) if not item.get("success")]


def _same_value(left: Any, right: Any) -> bool:
    try:
        return abs(float(left) - float(right)) < 1e-6
    except Exception:
        return str(left) == str(right)


def _period_from_row(row: dict[str, Any]) -> tuple[str | None, str]:
    for key in PERIOD_KEYS:
        if row.get(key):
            return str(row[key]), "high"
    return None, "low"


def normalize_match_from_result(match: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    item = dict(match)
    item["source_column_or_row"] = item.get("source_column_or_row") or item.get("source_column") or item.get("source_row_name")
    item["value_confidence"] = item.get("value_confidence") or item.get("confidence") or "none"
    item["confidence"] = item["value_confidence"]

    if item.get("matched") and not item.get("source_period"):
        source_column = item.get("source_column")
        value = item.get("value")
        for row in result.get("head_rows") or []:
            if source_column and source_column in row and _same_value(row.get(source_column), value):
                period, period_confidence = _period_from_row(row)
                if period:
                    item["source_period"] = period
                    item["period_confidence"] = period_confidence
                    item["notes"] = f"{item.get('notes')}; period rebound from head_rows.{source_column}"
                    break

    if item.get("matched"):
        item["source_period"] = item.get("source_period") or "unknown"
        item["period_confidence"] = item.get("period_confidence") or ("low" if item["source_period"] == "unknown" else "medium")
    else:
        item["source_period"] = item.get("source_period") or "unknown"
        item["period_confidence"] = item.get("period_confidence") or "none"
    return item


def best_matches(probe: dict[str, Any]) -> dict[str, dict[str, Any]]:
    matches: dict[str, dict[str, Any]] = {}
    for field in TARGET_FIELDS:
        candidates = []
        for result in successful_functions(probe):
            match = (result.get("target_field_matches") or {}).get(field)
            if match and match.get("matched"):
                candidates.append(normalize_match_from_result(match, result))
        if not candidates:
            matches[field] = {
                "matched": False,
                "source_function": None,
                "source_column": None,
                "source_row_name": None,
                "source_column_or_row": None,
                "source_period": None,
                "value": None,
                "unit": None,
                "confidence": "none",
                "period_confidence": "none",
                "value_confidence": "none",
                "notes": "not found in successful function results",
            }
            continue
        candidates.sort(
            key=lambda item: (
                {"high": 3, "medium": 2, "low": 1}.get(str(item.get("value_confidence")), 0),
                {"high": 3, "medium": 2, "low": 1}.get(str(item.get("period_confidence")), 0),
            ),
            reverse=True,
        )
        matches[field] = candidates[0]
    return matches


def connector_recommendation(field: str, match: dict[str, Any]) -> str:
    if not match.get("matched"):
        return "not ready"
    if field in CAUTION_FIELDS:
        return "recommended with caution"
    if match.get("value_confidence") == "high" and match.get("period_confidence") in {"high", "medium"}:
        return "strongly recommended"
    return "recommended with caution"


def field_note(field: str) -> str:
    notes = {
        "inventory": "Balance-sheet amount field only; turnover ratio is not a substitute.",
        "accounts_receivable": "Balance-sheet amount field only; turnover ratio is not a substitute.",
        "contract_liabilities": "Useful as structured order-visibility proxy, but not the same as explicit order backlog.",
        "r_and_d_expense": "Profit-statement expense amount.",
        "r_and_d_expense_ratio": "Derived only when both R&D expense and revenue are available.",
        "capex": "Cash-flow statement cash paid for fixed assets, intangible assets, and other long-term assets.",
        "capex_ratio": "Derived only when both capex and revenue are available.",
    }
    return notes[field]


def mapping_summary(probe: dict[str, Any]) -> dict[str, Any]:
    matches = best_matches(probe)
    return {
        field: {
            **match,
            "connector_recommendation": connector_recommendation(field, match),
            "field_note": field_note(field),
        }
        for field, match in matches.items()
    }


def missing_or_ambiguous(summary: dict[str, Any]) -> dict[str, list[str]]:
    missing = [field for field, item in summary.items() if not item.get("matched")]
    ambiguous = [
        field
        for field, item in summary.items()
        if item.get("matched") and item.get("connector_recommendation") == "recommended with caution"
    ]
    not_recommended = [
        "customer_concentration",
        "new_business_orders",
        "domestic_substitution_revenue",
        "production_or_unit_cost",
        "cobalt_or_molybdenum_price",
    ]
    return {
        "missing_fields": missing,
        "ambiguous_fields": ambiguous,
        "not_recommended_fields": not_recommended,
    }


def render_markdown(probe: dict[str, Any]) -> str:
    summary = mapping_summary(probe)
    gaps = missing_or_ambiguous(summary)
    lines: list[str] = []
    lines.append(f"# Financial Statement Field Probe Replay: {probe.get('stock_code')}")
    lines.append("")
    lines.append(f"- Generated at: {probe.get('generated_at')}")
    lines.append(f"- AkShare version: {probe.get('akshare_version')}")
    lines.append(f"- Probe schema: {probe.get('schema_version')}")
    lines.append("")

    lines.append("## 1. Successful Functions")
    successes = successful_functions(probe)
    if successes:
        lines.append("| function | statement_type | shape | periods |")
        lines.append("| --- | --- | --- | --- |")
        for item in successes:
            periods = ", ".join(map(str, item.get("detected_report_periods") or []))
            lines.append(f"| {item.get('function_name')} | {item.get('statement_type')} | {item.get('shape')} | {periods} |")
    else:
        lines.append("No successful functions.")
    lines.append("")

    lines.append("## 2. Failed Functions")
    failures = failed_functions(probe)
    if failures:
        lines.append("| function | statement_type | error |")
        lines.append("| --- | --- | --- |")
        for item in failures:
            lines.append(f"| {item.get('function_name')} | {item.get('statement_type')} | {str(item.get('error') or '').replace('|', '/')} |")
    else:
        lines.append("No failed functions.")
    lines.append("")

    lines.append("## 3. Target Field Mapping Summary")
    lines.append("| target_field | found | source_function | source_column_or_row | source_period | period_confidence | value | value_confidence | connector_v2_2 |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for field in TARGET_FIELDS:
        item = summary[field]
        column_or_row = item.get("source_column_or_row") or item.get("source_row_name") or item.get("source_column") or ""
        lines.append(
            f"| {field} | {bool(item.get('matched'))} | {item.get('source_function') or ''} | "
            f"{column_or_row} | {item.get('source_period') or ''} | {item.get('period_confidence') or ''} | "
            f"{item.get('value') if item.get('value') is not None else ''} | {item.get('value_confidence') or item.get('confidence') or ''} | "
            f"{item.get('connector_recommendation')} |"
        )
    lines.append("")

    lines.append("## 4. Target Field Details")
    for field in TARGET_FIELDS:
        item = summary[field]
        lines.append(f"### {FIELD_LABELS[field]}")
        lines.append(f"- Found: {bool(item.get('matched'))}")
        lines.append(f"- Source function: {item.get('source_function') or ''}")
        lines.append(f"- Column / row: {item.get('source_column_or_row') or item.get('source_column') or item.get('source_row_name') or ''}")
        lines.append(f"- Source period: {item.get('source_period') or ''}")
        lines.append(f"- Period confidence: {item.get('period_confidence') or ''}")
        lines.append(f"- Current value: {item.get('value') if item.get('value') is not None else ''}")
        lines.append(f"- Value confidence: {item.get('value_confidence') or item.get('confidence') or ''}")
        lines.append(f"- Scope note: {item.get('field_note')}")
        lines.append(f"- Suitable for connector v2.2: {item.get('connector_recommendation')}")
        lines.append("")

    lines.append("## 5. Derived Field Summary")
    for field in ("r_and_d_expense_ratio", "capex_ratio"):
        item = summary[field]
        lines.append(f"- {field}: {'derivable' if item.get('matched') else 'not derivable'}; {item.get('notes')}")
    lines.append("")

    lines.append("## 6. Missing / Ambiguous Fields")
    lines.append(f"- Missing fields: {', '.join(gaps['missing_fields']) if gaps['missing_fields'] else 'none'}")
    lines.append(f"- Ambiguous fields: {', '.join(gaps['ambiguous_fields']) if gaps['ambiguous_fields'] else 'none'}")
    lines.append(f"- Not recommended now: {', '.join(gaps['not_recommended_fields'])}")
    lines.append("")

    lines.append("## 7. v2.2 Connector Recommendation")
    strong = [field for field, item in summary.items() if item["connector_recommendation"] == "strongly recommended"]
    cautious = [field for field, item in summary.items() if item["connector_recommendation"] == "recommended with caution"]
    not_ready = [field for field, item in summary.items() if item["connector_recommendation"] == "not ready"]
    lines.append(f"- strongly recommended: {', '.join(strong) if strong else 'none'}")
    lines.append(f"- recommended with caution: {', '.join(cautious) if cautious else 'none'}")
    lines.append(f"- not ready: {', '.join(not_ready) if not_ready else 'none'}")
    lines.append("")
    return "\n".join(lines)


def write_replay(input_path: str | Path, output_path: str | Path) -> str:
    probe = load_probe(input_path)
    markdown = render_markdown(probe)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(markdown, encoding="utf-8")
    return markdown


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    probe = load_probe(args.input)
    markdown = render_markdown(probe)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(markdown, encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(markdown)


if __name__ == "__main__":
    main()
