# -*- coding: utf-8 -*-

import json
from pathlib import Path

import pytest

from src.fundamental_skill.pipeline import FundamentalSkillPipeline
from src.fundamental_skill.validators import assert_valid_result, validate_no_trading_instruction


FIXTURES = Path(__file__).parent / "regression" / "fixtures"
EXPECTED = Path(__file__).parent / "regression" / "expected"
CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}
TRADE_TERMS = ["买入", "卖出", "加仓", "减仓", "清仓", "止损", "止盈", "目标价", "满仓", "梭哈"]


def case_id(path: Path) -> str:
    return path.stem


REGRESSION_FIXTURES = sorted(FIXTURES.glob("*.json"))


def fail_message(stock_code: str, field: str, actual, expected) -> str:
    return f"{stock_code} regression failed: {field}; actual={actual!r}; expected={expected!r}"


@pytest.mark.parametrize("fixture_path", REGRESSION_FIXTURES, ids=case_id)
def test_regression_snapshot(fixture_path: Path):
    expected_path = EXPECTED / fixture_path.name
    expected = json.loads(expected_path.read_text(encoding="utf-8"))

    result = FundamentalSkillPipeline().analyze_from_file(str(fixture_path))
    stock_code = expected["stock_code"]

    assert result.stock_code == stock_code, fail_message(stock_code, "stock_code", result.stock_code, stock_code)
    assert result.strategy_type == expected["expected_strategy_type"], fail_message(
        stock_code, "strategy_type", result.strategy_type, expected["expected_strategy_type"]
    )
    assert result.status in expected["allowed_status"], fail_message(
        stock_code, "status", result.status, expected["allowed_status"]
    )
    assert CONFIDENCE_RANK[result.confidence] <= CONFIDENCE_RANK[expected["max_confidence"]], fail_message(
        stock_code, "confidence", result.confidence, f"<= {expected['max_confidence']}"
    )
    if "max_score" in expected:
        assert result.fundamental_score <= expected["max_score"], fail_message(
            stock_code, "fundamental_score", result.fundamental_score, f"<= {expected['max_score']}"
        )

    risk_text = " ".join(risk.name for risk in result.risk_flags)
    for risk_keyword in expected.get("min_required_risk_flags", []):
        assert risk_keyword in risk_text, fail_message(stock_code, "risk_flags", risk_text, risk_keyword)

    track_text = " ".join(item.name for item in result.must_track_indicators)
    for keyword in expected.get("must_track_keywords", []):
        assert keyword in track_text, fail_message(stock_code, "must_track_indicators", track_text, keyword)

    key_driver_text = " ".join(result.key_drivers)
    for phrase in expected.get("forbidden_phrases", []):
        assert phrase not in result.trader_summary, fail_message(
            stock_code, "trader_summary forbidden phrase", result.trader_summary, phrase
        )
        assert phrase not in key_driver_text, fail_message(
            stock_code, "key_drivers forbidden phrase", key_driver_text, phrase
        )

    dumped = result.model_dump_json()
    assert validate_no_trading_instruction(dumped) == [], fail_message(
        stock_code, "trading terms", validate_no_trading_instruction(dumped), []
    )
    for term in TRADE_TERMS:
        assert term not in dumped, fail_message(stock_code, "final JSON trading term", dumped, term)
    assert_valid_result(result)
