# -*- coding: utf-8 -*-

import pytest
from pydantic import ValidationError

from src.fundamental_skill.schema import (
    FinancialQuality,
    FundamentalAnalysisResult,
    IndustryCycle,
    InvalidationCondition,
    RiskFlag,
    ThesisCheck,
    ValuationView,
)
from src.fundamental_skill.validators import (
    assert_valid_result,
    validate_no_trading_instruction,
    validate_result,
)


def sample_result(**overrides):
    payload = {
        "stock_code": "000426",
        "stock_name": "兴业银锡",
        "analysis_date": "2026-05-15",
        "strategy_type": "resource_swing",
        "status": "supportive",
        "confidence": "medium",
        "confidence_reason": "mock 数据覆盖核心字段。",
        "fundamental_score": 70,
        "business_summary": "mock 基本面摘要。",
        "key_drivers": ["资源品价格"],
        "financial_quality": FinancialQuality(score=70, evidence=[]),
        "valuation_view": ValuationView(
            valuation_level="reasonable",
            score=60,
            evidence=[],
        ),
        "industry_cycle": IndustryCycle(
            cycle_position="upcycle",
            key_external_variables=["银价"],
            score=75,
            evidence=[],
        ),
        "risk_flags": [],
        "catalysts": [],
        "must_track_indicators": [],
        "invalidation_conditions": [
            InvalidationCondition(
                condition="核心假设失效",
                evidence_needed="关键数据恶化",
                action_hint_for_trader="需要交易员重新评估",
            )
        ],
        "thesis_check": ThesisCheck(
            user_thesis=None,
            thesis_support="none",
            supporting_evidence=[],
            opposing_evidence=[],
            missing_evidence=[],
        ),
        "suitable_strategy_type": "资源弹性基本面观察",
        "trader_summary": "基本面支持交给交易员进一步评估。",
        "data_sources": [],
        "data_timestamp": "2026-05-15T00:00:00",
        "missing_fields": [],
        "valid_until": None,
        "refresh_triggers": [],
        "raw_data_path": None,
    }
    payload.update(overrides)
    return FundamentalAnalysisResult(**payload)


def test_validate_no_trading_instruction_detects_terms():
    text = "这里不能写买入、卖出、目标价或满仓。"

    terms = validate_no_trading_instruction(text)

    assert "买入" in terms
    assert "卖出" in terms
    assert "目标价" in terms
    assert "满仓" in terms


def test_validate_result_blocks_trading_advice_in_trader_summary():
    result = sample_result(trader_summary="基本面很好，建议买入。")

    errors = validate_result(result)

    assert any("trader_summary" in error for error in errors)


def test_insufficient_data_score_over_50_is_invalid():
    result = sample_result(status="insufficient_data", fundamental_score=60)

    errors = validate_result(result)

    assert any("insufficient_data" in error for error in errors)


def test_low_confidence_without_reason_or_missing_fields_is_invalid():
    result = sample_result(confidence="low", confidence_reason="", missing_fields=[])

    errors = validate_result(result)

    assert any("confidence=low" in error for error in errors)


def test_invalid_action_hint_raises_or_is_caught():
    with pytest.raises(ValidationError):
        sample_result(
            invalidation_conditions=[
                {
                    "condition": "核心假设失效",
                    "evidence_needed": "关键数据恶化",
                    "action_hint_for_trader": "需要清仓或止损",
                }
            ]
        )


def test_validate_result_catches_action_hint_if_model_construct_bypasses_schema():
    invalid_condition = InvalidationCondition.model_construct(
        condition="核心假设失效",
        evidence_needed="关键数据恶化",
        action_hint_for_trader="需要清仓或止损",
    )
    result = sample_result(invalidation_conditions=[invalid_condition])

    errors = validate_result(result)

    assert any("action_hint_for_trader" in error for error in errors)


def test_high_risk_requires_warning_in_trader_summary():
    result = sample_result(
        risk_flags=[
            RiskFlag(
                name="商品价格回落风险",
                severity="high",
                evidence=[],
                monitor_method="跟踪商品价格",
            )
        ],
        trader_summary="基本面支持交给交易员进一步评估。",
    )

    errors = validate_result(result)

    assert any("high severity risk_flags" in error for error in errors)


def test_assert_valid_result_raises_on_errors():
    result = sample_result(trader_summary="建议卖出。")

    with pytest.raises(ValueError):
        assert_valid_result(result)
