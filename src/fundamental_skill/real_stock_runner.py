# -*- coding: utf-8 -*-
"""CLI runner for real public A-share data through FundamentalSkillPipeline."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from .pipeline import FundamentalSkillPipeline
from .real_data_connector import RealDataConnector
from .schema import FundamentalAnalysisResult


def run_real_stock(
    code: str,
    output: str | None = None,
    force_refresh: bool = False,
    connector: RealDataConnector | None = None,
) -> tuple[dict[str, Any], FundamentalAnalysisResult]:
    output_path = Path(output) if output else Path("output") / f"fundamental_{code}.json"
    raw_path = output_path.parent / f"raw_{code}.json"

    connector = connector or RealDataConnector()
    raw_json = connector.fetch_to_raw_json(code, output_path=str(raw_path), force_refresh=force_refresh)
    result = FundamentalSkillPipeline().analyze_from_dict(raw_json)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    return raw_json, result


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch real public A-share data and run fundamental_skill.")
    parser.add_argument("--code", required=True, help="6 digit A-share stock code")
    parser.add_argument("--output", required=False, help="Output FundamentalAnalysisResult JSON path")
    parser.add_argument("--force-refresh", action="store_true", help="Ignore cache and fetch fresh public data")
    args = parser.parse_args()

    raw_json, result = run_real_stock(args.code, output=args.output, force_refresh=args.force_refresh)
    errors = raw_json.get("errors", [])

    print(f"stock_code: {result.stock_code}")
    print(f"stock_name: {result.stock_name}")
    print(f"strategy_type: {result.strategy_type}")
    print(f"status: {result.status}")
    print(f"confidence: {result.confidence}")
    print(f"fundamental_score: {result.fundamental_score}")
    print(f"risk_flags count: {len(result.risk_flags)}")
    print(f"must_track_indicators count: {len(result.must_track_indicators)}")
    print(f"missing_fields: {result.missing_fields}")
    print(f"errors count: {len(errors)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
