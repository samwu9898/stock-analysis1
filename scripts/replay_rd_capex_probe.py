# -*- coding: utf-8 -*-
"""Replay R&D and capex probes into markdown.

Offline-only: reads saved probe JSON and writes a mapping audit markdown file.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


TARGET_FIELDS = (
    "r_and_d_expense",
    "r_and_d_expense_ratio",
    "capex",
    "capex_ratio",
    "depreciation_amortization",
)

OPTIONAL_FIELDS = {"depreciation_amortization"}
DERIVED_FIELDS = {"r_and_d_expense_ratio", "capex_ratio"}


def load_probe(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def successful_functions(probe: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in probe.get("function_results", []) if item.get("success")]


def failed_functions(probe: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in probe.get("function_results", []) if not item.get("success")]


def _score(match: dict[str, Any]) -> tuple[int, int, int]:
    confidence_score = {"high": 3, "medium": 2, "low": 1, "none": 0}
    return (
        confidence_score.get(str(match.get("value_confidence")), 0),
        confidence_score.get(str(match.get("period_confidence")), 0),
        confidence_score.get(str(match.get("unit_confidence")), 0),
    )


def best_matches(probe: dict[str, Any]) -> dict[str, dict[str, Any]]:
    matches: dict[str, dict[str, Any]] = {}
    for field in TARGET_FIELDS:
        candidates = []
        for result in successful_functions(probe):
            match = (result.get("target_field_matches") or {}).get(field)
            if match and match.get("matched"):
                item = dict(match)
                item["source_column_or_row"] = item.get("source_column_or_row") or item.get("source_column") or item.get("source_row_name")
                candidates.append(item)
        if candidates:
            candidates.sort(key=_score, reverse=True)
            matches[field] = candidates[0]
        else:
            matches[field] = {
                "matched": False,
                "source_function": None,
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
                "notes": "not found in successful function results",
            }
    return matches


def connector_recommendation(field: str, match: dict[str, Any]) -> str:
    if field in OPTIONAL_FIELDS:
        return "not ready"
    if not match.get("matched"):
        return "not ready"
    if field in DERIVED_FIELDS:
        return "recommended with caution"
    if (
        match.get("value_confidence") == "high"
        and match.get("period_confidence") in {"high", "medium"}
        and match.get("unit_confidence") in {"high", "medium"}
    ):
        return "strongly recommended"
    return "recommended with caution"


def field_note(field: str) -> str:
    return {
        "r_and_d_expense": "Profit-statement expense amount only; not a headcount, project, narrative, or ratio field.",
        "r_and_d_expense_ratio": "Derived from R&D expense divided by revenue only when both use the same source_period.",
        "capex": "Cash-flow statement cash paid to purchase or construct fixed, intangible, and other long-term assets.",
        "capex_ratio": "Derived from capex divided by revenue only when both use the same source_period.",
        "depreciation_amortization": "Optional observation field; multiple rows can represent different components, so do not promote if unstable.",
    }[field]


def mapping_summary(probe: dict[str, Any]) -> dict[str, dict[str, Any]]:
    matches = best_matches(probe)
    return {
        field: {
            **match,
            "connector_v2_3": connector_recommendation(field, match),
            "field_note": field_note(field),
        }
        for field, match in matches.items()
    }


def ambiguity_summary(summary: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    return {
        "single_quarter_or_cumulative_uncertain": [
            field for field, item in summary.items()
            if item.get("matched") and item.get("cumulative_or_single_quarter") == "unknown"
        ],
        "unit_uncertain": [
            field for field, item in summary.items()
            if item.get("matched") and item.get("unit_confidence") == "low"
        ],
        "period_uncertain_or_mismatched": [
            field for field, item in summary.items()
            if item.get("matched") and item.get("period_confidence") in {"low", "none"}
        ],
        "field_name_ambiguous": [
            field for field, item in summary.items()
            if item.get("matched") and item.get("connector_v2_3") == "recommended with caution"
        ],
    }


def render_markdown(probe: dict[str, Any]) -> str:
    summary = mapping_summary(probe)
    ambiguity = ambiguity_summary(summary)
    lines: list[str] = []

    lines.append(f"# R&D / Capex Source Expansion Probe Replay: {probe.get('stock_code')}")
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
    lines.append("| target_field | found | source_function | field_or_row | source_period | value | unit | period_confidence | value_confidence | unit_confidence | cumulative_or_single_quarter | connector_v2_3 |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for field in TARGET_FIELDS:
        item = summary[field]
        field_or_row = item.get("source_column_or_row") or item.get("source_row_name") or item.get("source_column") or ""
        value = item.get("value") if item.get("value") is not None else ""
        lines.append(
            f"| {field} | {bool(item.get('matched'))} | {item.get('source_function') or ''} | "
            f"{field_or_row} | {item.get('source_period') or ''} | {value} | {item.get('unit') or ''} | "
            f"{item.get('period_confidence') or ''} | {item.get('value_confidence') or ''} | {item.get('unit_confidence') or ''} | "
            f"{item.get('cumulative_or_single_quarter') or ''} | {item.get('connector_v2_3')} |"
        )
    lines.append("")

    lines.append("## 4. Target Field Details")
    for field in TARGET_FIELDS:
        item = summary[field]
        lines.append(f"### {field}")
        lines.append(f"- Found: {bool(item.get('matched'))}")
        lines.append(f"- Source function: {item.get('source_function') or ''}")
        lines.append(f"- Field / row name: {item.get('source_column_or_row') or item.get('source_column') or item.get('source_row_name') or ''}")
        lines.append(f"- Source period: {item.get('source_period') or ''}")
        lines.append(f"- Current value: {item.get('value') if item.get('value') is not None else ''}")
        lines.append(f"- Unit: {item.get('unit') or ''}")
        lines.append(f"- Period confidence: {item.get('period_confidence') or ''}")
        lines.append(f"- Value confidence: {item.get('value_confidence') or ''}")
        lines.append(f"- Unit confidence: {item.get('unit_confidence') or ''}")
        lines.append(f"- Cumulative or single quarter: {item.get('cumulative_or_single_quarter') or ''}")
        lines.append(f"- Scope note: {item.get('field_note')}")
        lines.append(f"- Suitable for connector v2.3: {item.get('connector_v2_3')}")
        if item.get("derivation_method"):
            lines.append(f"- Derivation method: {item.get('derivation_method')}")
        lines.append("")

    lines.append("## 5. Derived Field Summary")
    for field in ("r_and_d_expense_ratio", "capex_ratio"):
        item = summary[field]
        lines.append(f"- {field}: {'derivable' if item.get('matched') else 'not derivable'}; {item.get('notes')}")
    lines.append("")

    lines.append("## 6. Ambiguity / Risk Summary")
    lines.append(f"- Single-quarter/cumulative uncertain: {', '.join(ambiguity['single_quarter_or_cumulative_uncertain']) if ambiguity['single_quarter_or_cumulative_uncertain'] else 'none'}")
    lines.append(f"- Unit uncertain: {', '.join(ambiguity['unit_uncertain']) if ambiguity['unit_uncertain'] else 'none'}")
    lines.append(f"- Report-period uncertain or mismatched: {', '.join(ambiguity['period_uncertain_or_mismatched']) if ambiguity['period_uncertain_or_mismatched'] else 'none'}")
    lines.append(f"- Field-name ambiguous: {', '.join(ambiguity['field_name_ambiguous']) if ambiguity['field_name_ambiguous'] else 'none'}")
    lines.append("")

    lines.append("## 7. v2.3 Recommendation")
    strong = [field for field, item in summary.items() if item["connector_v2_3"] == "strongly recommended"]
    cautious = [field for field, item in summary.items() if item["connector_v2_3"] == "recommended with caution"]
    not_ready = [field for field, item in summary.items() if item["connector_v2_3"] == "not ready"]
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
