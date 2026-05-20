# -*- coding: utf-8 -*-

import pytest
from pydantic import ValidationError

from src.fundamental_skill.schema import (
    DataSource,
    Evidence,
    FinancialQuality,
    FundamentalAnalysisResult,
    IndustryCycle,
    InvalidationCondition,
    ThesisCheck,
    ValuationView,
)


def sample_result(**overrides):
    evidence = Evidence(
        source="mock",
        metric_name="revenue",
        value="mock",
        period="2025",
        interpretation="收入趋势用于 mock 测试。",
    )
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
        "key_drivers": ["资源品价格", "产量释放"],
        "financial_quality": FinancialQuality(score=70, evidence=[evidence]),
        "valuation_view": ValuationView(
            valuation_level="reasonable",
            score=60,
            evidence=[evidence],
        ),
        "industry_cycle": IndustryCycle(
            cycle_position="upcycle",
            key_external_variables=["银价", "锡价"],
            score=75,
            evidence=[evidence],
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
        "data_sources": [
            DataSource(
                name="mock_sample",
                source_type="derived",
                fetched_at="2026-05-15T00:00:00",
                period="mock",
            )
        ],
        "data_timestamp": "2026-05-15T00:00:00",
        "missing_fields": [],
        "valid_until": None,
        "refresh_triggers": ["季度报告发布"],
        "raw_data_path": None,
    }
    payload.update(overrides)
    return FundamentalAnalysisResult(**payload)


def test_fundamental_analysis_result_can_be_constructed():
    result = sample_result()

    assert result.schema_version == "fundamental.v1"
    assert result.model_dump_json()


def test_fundamental_score_over_100_raises():
    with pytest.raises(ValidationError):
        sample_result(fundamental_score=101)


def test_invalid_status_raises():
    with pytest.raises(ValidationError):
        sample_result(status="positive")


def test_invalid_confidence_raises():
    with pytest.raises(ValidationError):
        sample_result(confidence="certain")


def test_invalid_strategy_type_raises():
    with pytest.raises(ValidationError):
        sample_result(strategy_type="auto_trade")
