# -*- coding: utf-8 -*-

from pathlib import Path
from typing import get_args

import yaml

from src.fundamental_skill import classification_schema, schema
from src.fundamental_skill.constants import STRATEGY_TYPES


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATHS = (
    PROJECT_ROOT / "config" / "strategy_classification.yaml",
    PROJECT_ROOT / "config" / "industry_frameworks.yaml",
    PROJECT_ROOT / "config" / "data_requirements.yaml",
)

EXPECTED_STRATEGY_TYPES = (
    "resource_swing",
    "resource_core",
    "right_trend_growth",
    "semiconductor_cycle",
    "stable_growth",
    "advanced_manufacturing_growth",
    "satellite_communication_infrastructure",
    "low_altitude_economy_infrastructure",
    "life_science_cxo_services",
    "theme_only",
    "unknown",
)


def _config_strategy_types(path: Path) -> tuple[str, ...]:
    with path.open("r", encoding="utf-8") as f:
        return tuple((yaml.safe_load(f) or {}).keys())


def test_strategy_type_constants_match_schema_and_configs():
    expected = set(EXPECTED_STRATEGY_TYPES)

    assert STRATEGY_TYPES == EXPECTED_STRATEGY_TYPES
    assert set(get_args(schema.StrategyType)) == expected
    assert set(get_args(classification_schema.StrategyType)) == expected

    for path in CONFIG_PATHS:
        assert set(_config_strategy_types(path)) == expected


def test_infrastructure_strategy_types_are_present_without_dropping_existing_types():
    assert "satellite_communication_infrastructure" in STRATEGY_TYPES
    assert "low_altitude_economy_infrastructure" in STRATEGY_TYPES
    assert "life_science_cxo_services" in STRATEGY_TYPES

    for strategy_type in (
        "resource_swing",
        "resource_core",
        "right_trend_growth",
        "semiconductor_cycle",
        "stable_growth",
        "advanced_manufacturing_growth",
        "theme_only",
        "unknown",
    ):
        assert strategy_type in STRATEGY_TYPES
