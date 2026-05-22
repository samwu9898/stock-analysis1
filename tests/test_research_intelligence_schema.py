# -*- coding: utf-8 -*-

import pytest

from src.fundamental_skill.ai_analyst.research_intelligence_schema import (
    ResearchIntelligencePack,
    ResearchQuestion,
    ResearchQuestionSet,
)


def _question(**overrides):
    payload = {
        "question_id": "q_test",
        "question": "补充收入拆分和现金流解释。",
        "category": "manual_review",
        "priority": "P0",
        "evidence_trigger": "revenue_growth_vs_cashflow_mismatch",
        "why_it_matters": "验证业务说法是否有财务证据。",
        "data_availability_status": "partial",
        "confidence_cap": "medium",
        "what_was_checked": ["financial_metrics.revenue_yoy"],
    }
    payload.update(overrides)
    return payload


def test_research_question_without_evidence_trigger_is_downgraded_from_p0():
    question = ResearchQuestion.model_validate(_question(evidence_trigger=""))

    assert question.priority == "P1"


def test_missing_item_requires_not_assessable_reason():
    with pytest.raises(ValueError, match="not_assessable_reason"):
        ResearchQuestion.model_validate(
            _question(
                data_availability_status="missing",
                confidence_cap="low",
                evidence_trigger="missing_required_field",
            )
        )


def test_schema_validates_full_research_artifacts():
    question = ResearchQuestion.model_validate(_question())
    pack = ResearchIntelligencePack.model_validate(
        {
            "stock_code": "002837",
            "stock_name": "英维克",
            "generated_at": "2026-05-22T00:00:00",
            "strategy_type": "ai_datacenter_infrastructure",
            "sub_type": "cooling_liquid_cooling_infrastructure",
            "source_hierarchy": [
                {
                    "source_tier": "S4",
                    "source_name": "financial_indicator",
                    "evidence_type": "fact",
                    "data_availability_status": "available",
                    "source_confidence": "medium",
                    "what_was_checked": ["source_trace_summary.financial_indicator"],
                }
            ],
            "evidence_classification": [],
            "strategy_driver_map": {},
            "business_financial_cross_validation": [],
            "rule_triggered_contradictions": [],
            "manual_review_items": [],
            "ir_question_candidates": [question],
        }
    )
    qset = ResearchQuestionSet.model_validate(
        {
            "stock_code": "002837",
            "stock_name": "英维克",
            "generated_at": "2026-05-22T00:00:00",
            "questions": [question],
        }
    )

    assert pack.schema_version == "research_intelligence.v1"
    assert qset.schema_version == "research_questions.v1"
    assert qset.questions[0].evidence_trigger
