# -*- coding: utf-8 -*-
"""Run sample regression fixtures through FundamentalSkillPipeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.fundamental_skill.pipeline import FundamentalSkillPipeline
from src.fundamental_skill.validators import assert_valid_result, validate_no_trading_instruction


FIXTURES = ROOT / "tests" / "regression" / "fixtures"
EXPECTED = ROOT / "tests" / "regression" / "expected"
CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}


def validate_result_against_expected(result, expected: dict) -> list[str]:
    errors = []
    if result.stock_code != expected["stock_code"]:
        errors.append(f"stock_code actual={result.stock_code} expected={expected['stock_code']}")
    if result.strategy_type != expected["expected_strategy_type"]:
        errors.append(
            f"strategy_type actual={result.strategy_type} expected={expected['expected_strategy_type']}"
        )
    if result.status not in expected["allowed_status"]:
        errors.append(f"status actual={result.status} expected one of {expected['allowed_status']}")
    if CONFIDENCE_RANK[result.confidence] > CONFIDENCE_RANK[expected["max_confidence"]]:
        errors.append(f"confidence actual={result.confidence} expected <= {expected['max_confidence']}")
    if "max_score" in expected and result.fundamental_score > expected["max_score"]:
        errors.append(f"fundamental_score actual={result.fundamental_score} expected <= {expected['max_score']}")

    risk_text = " ".join(risk.name for risk in result.risk_flags)
    for keyword in expected.get("min_required_risk_flags", []):
        if keyword not in risk_text:
            errors.append(f"missing risk flag keyword: {keyword}")

    track_text = " ".join(item.name for item in result.must_track_indicators)
    for keyword in expected.get("must_track_keywords", []):
        if keyword not in track_text:
            errors.append(f"missing track keyword: {keyword}")

    key_driver_text = " ".join(result.key_drivers)
    for phrase in expected.get("forbidden_phrases", []):
        if phrase in result.trader_summary:
            errors.append(f"forbidden phrase in trader_summary: {phrase}")
        if phrase in key_driver_text:
            errors.append(f"forbidden phrase in key_drivers: {phrase}")

    terms = validate_no_trading_instruction(result.model_dump_json())
    if terms:
        errors.append(f"trading terms found: {sorted(set(terms))}")
    try:
        assert_valid_result(result)
    except ValueError as exc:
        errors.append(f"assert_valid_result failed: {exc}")
    return errors


def main() -> int:
    pipeline = FundamentalSkillPipeline()
    total = 0
    failed = 0

    for fixture_path in sorted(FIXTURES.glob("*.json")):
        total += 1
        expected = json.loads((EXPECTED / fixture_path.name).read_text(encoding="utf-8"))
        try:
            result = pipeline.analyze_from_file(str(fixture_path))
            errors = validate_result_against_expected(result, expected)
        except Exception as exc:  # pragma: no cover - CLI diagnostic path
            result = None
            errors = [f"pipeline failed: {exc}"]

        if result is not None:
            print(
                f"{result.stock_code} {result.stock_name} "
                f"{result.strategy_type} {result.status} {result.confidence} "
                f"score={result.fundamental_score} risks={len(result.risk_flags)}"
            )
        else:
            print(f"{fixture_path.name} FAILED")

        if errors:
            failed += 1
            for error in errors:
                print(f"  FAIL: {error}")

    passed = total - failed
    print(f"summary: passed={passed} failed={failed} total={total}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
