# -*- coding: utf-8 -*-

from pathlib import Path

from src.fundamental_skill.data_adapter import FundamentalDataAdapter
from src.fundamental_skill.stock_classifier import StockClassifier
from src.fundamental_skill.validators import validate_no_trading_instruction


FIXTURES = Path(__file__).parent / "fixtures"


def classify_fixture(name: str):
    normalized = FundamentalDataAdapter().from_file(str(FIXTURES / name))
    return StockClassifier().classify(normalized)


def test_resource_swing_fixture_classifies():
    result = classify_fixture("classifier_resource_swing.json")
    assert result.strategy_type == "resource_swing"


def test_resource_core_fixture_classifies():
    result = classify_fixture("classifier_resource_core.json")
    assert result.strategy_type == "resource_core"


def test_semiconductor_cycle_fixture_classifies():
    result = classify_fixture("classifier_semiconductor_cycle.json")
    assert result.strategy_type == "semiconductor_cycle"


def test_right_trend_growth_fixture_classifies():
    result = classify_fixture("classifier_right_trend_growth.json")
    assert result.strategy_type == "right_trend_growth"


def test_sanhua_mock_classifies_as_advanced_manufacturing_growth():
    result = classify_fixture("pipeline_sanhua_mock.json")

    assert result.strategy_type == "advanced_manufacturing_growth"


def test_tuopu_mock_classifies_as_advanced_manufacturing_growth():
    result = classify_fixture("classifier_advanced_manufacturing_tuopu.json")

    assert result.strategy_type == "advanced_manufacturing_growth"


def test_stable_growth_fixture_classifies():
    result = classify_fixture("classifier_stable_growth.json")
    assert result.strategy_type == "stable_growth"


def test_theme_only_fixture_classifies_theme_or_unknown():
    result = classify_fixture("classifier_theme_only.json")
    assert result.strategy_type in {"theme_only", "unknown"}


def test_unknown_fixture_classifies_unknown():
    result = classify_fixture("classifier_unknown.json")
    assert result.strategy_type == "unknown"
    assert result.confidence == "low"


def test_satellite_communication_infrastructure_fixture_classifies():
    result = classify_fixture("classifier_satellite_601698.json")

    assert result.strategy_type == "satellite_communication_infrastructure"


def test_satellite_negative_boundary_fixtures_do_not_classify_as_satellite():
    for fixture in [
        "classifier_satellite_negative_600118.json",
        "classifier_satellite_negative_002465.json",
        "classifier_satellite_negative_688066.json",
        "classifier_satellite_negative_002895.json",
    ]:
        result = classify_fixture(fixture)
        assert result.strategy_type != "satellite_communication_infrastructure"


def test_satellite_news_only_theme_does_not_classify_as_satellite():
    result = classify_fixture("classifier_satellite_news_only_theme.json")

    assert result.strategy_type in {"theme_only", "unknown"}


def test_low_altitude_aviation_operations_service_classifies():
    result = classify_fixture("classifier_low_altitude_000099.json")

    assert result.strategy_type == "low_altitude_economy_infrastructure"
    assert result.sub_type == "aviation_operations_service"
    assert result.confidence != "high"


def test_low_altitude_airspace_platform_system_classifies():
    result = classify_fixture("classifier_low_altitude_688631.json")

    assert result.strategy_type == "low_altitude_economy_infrastructure"
    assert result.sub_type == "airspace_platform_system"
    assert result.confidence != "high"


def test_low_altitude_boundary_negative_does_not_route_to_old_frameworks():
    result = classify_fixture("classifier_low_altitude_negative_688070.json")

    assert result.strategy_type != "low_altitude_economy_infrastructure"
    assert result.strategy_type not in {"semiconductor_cycle", "resource_swing"}


def test_low_altitude_theme_only_guard():
    result = classify_fixture("classifier_low_altitude_theme_only.json")

    assert result.strategy_type in {"theme_only", "unknown"}


def test_life_science_cxo_positive_subtypes_classify():
    expected = {
        "classifier_life_science_cxo_603259.json": "integrated_cxo_platform",
        "classifier_life_science_cxo_300759.json": "integrated_cxo_platform",
        "classifier_life_science_cxo_002821.json": "cdmo_manufacturing_services",
        "classifier_life_science_cxo_300363.json": "cdmo_manufacturing_services",
        "classifier_life_science_cxo_300347.json": "clinical_cro_services",
    }
    for fixture, sub_type in expected.items():
        result = classify_fixture(fixture)
        assert result.strategy_type == "life_science_cxo_services"
        assert result.sub_type == sub_type
        assert result.confidence != "high"


def test_life_science_cxo_porton_high_volatility_caution():
    result = classify_fixture("classifier_life_science_cxo_300363.json")

    assert result.strategy_type == "life_science_cxo_services"
    assert "high_volatility_cdmo_sample_one_off_order_caution" in result.warnings


def test_life_science_cxo_negative_boundaries_do_not_classify():
    for fixture in [
        "classifier_life_science_cxo_negative_600276.json",
        "classifier_life_science_cxo_negative_600521.json",
        "classifier_life_science_cxo_negative_000739.json",
        "classifier_life_science_cxo_negative_300760.json",
        "classifier_life_science_cxo_negative_300012.json",
        "classifier_life_science_cxo_negative_600196.json",
    ]:
        result = classify_fixture(fixture)
        assert result.strategy_type != "life_science_cxo_services"


def test_news_only_match_cannot_be_high_confidence():
    normalized = FundamentalDataAdapter().from_file(str(FIXTURES / "classifier_theme_only.json"))
    normalized.basic_info.industry = None
    normalized.basic_info.main_business = None
    normalized.raw_blocks = {}

    result = StockClassifier().classify(normalized)

    assert result.confidence != "high"


def test_resource_core_tiebreaker_prefers_zijin():
    result = classify_fixture("classifier_resource_core.json")

    assert result.strategy_type == "resource_core"
    assert "resource_swing" in result.alternative_types


def test_semiconductor_tiebreaker_prefers_semiconductor_keywords():
    normalized = FundamentalDataAdapter().from_file(str(FIXTURES / "classifier_semiconductor_cycle.json"))
    normalized.latest_news.append(
        normalized.latest_news[0].model_copy(
            update={"title": "AI算力服务器数据中心需求扩散", "summary": "同时出现AI成长关键词"}
        )
    )

    result = StockClassifier().classify(normalized)

    assert result.strategy_type == "semiconductor_cycle"
    assert "right_trend_growth" in result.alternative_types


def test_missing_fields_are_passed_through():
    normalized = FundamentalDataAdapter().from_file(str(FIXTURES / "raw_missing_financials.json"))
    result = StockClassifier().classify(normalized)

    assert "financial_metrics" in result.missing_fields


def test_classifier_output_has_no_trading_instruction_terms():
    result = classify_fixture("classifier_resource_swing.json")

    assert validate_no_trading_instruction(result.model_dump_json()) == []
