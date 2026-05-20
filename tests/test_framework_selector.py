# -*- coding: utf-8 -*-

from src.fundamental_skill.classification_schema import StockClassificationResult
from src.fundamental_skill.constants import STRATEGY_TYPES
from src.fundamental_skill.framework_selector import FrameworkSelector
from src.fundamental_skill.validators import validate_no_trading_instruction


def test_each_strategy_type_returns_framework():
    selector = FrameworkSelector()

    for strategy_type in STRATEGY_TYPES:
        framework = selector.get_framework(strategy_type)
        assert framework.strategy_type == strategy_type
        assert framework.display_name


def test_unknown_fallback_returns_unknown_framework():
    framework = FrameworkSelector().get_framework("not_exist")

    assert framework.strategy_type == "unknown"


def test_framework_fields_are_not_empty():
    framework = FrameworkSelector().get_framework("resource_swing")

    assert framework.required_focus
    assert framework.must_track_indicators
    assert framework.key_risks
    assert framework.common_mistakes


def test_advanced_manufacturing_framework_returns_expected_fields():
    framework = FrameworkSelector().get_framework("advanced_manufacturing_growth")

    assert framework.strategy_type == "advanced_manufacturing_growth"
    assert "高端制造" in framework.display_name
    assert any("机器人" in item for item in framework.must_track_indicators)


def test_select_uses_classification_strategy_type():
    classification = StockClassificationResult(
        stock_code="000426",
        stock_name="兴业银锡",
        strategy_type="resource_swing",
        confidence="high",
        confidence_score=80,
        reasons=[],
        evidence=[],
        alternative_types=[],
        missing_fields=[],
        warnings=[],
    )

    framework = FrameworkSelector().select(classification)

    assert framework.strategy_type == "resource_swing"


def test_framework_contains_no_trading_instruction_terms():
    selector = FrameworkSelector()

    for strategy_type in STRATEGY_TYPES:
        framework = selector.get_framework(strategy_type)
        assert validate_no_trading_instruction(framework.model_dump_json()) == []
