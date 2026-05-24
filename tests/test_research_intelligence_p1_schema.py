# -*- coding: utf-8 -*-

import pytest

from src.fundamental_skill.ai_analyst.research_intelligence_p1_schema import (
    LESS_THAN_TWO_BUCKETS_REASON,
    TRANSMISSION_PATH_FALLBACK,
    DriverFactor,
    ResearchDriverMatrixPack,
    ResearchDriverQuestion,
    SourceBucketSummary,
)


def _driver(**overrides):
    payload = {
        "layer": "company",
        "driver_factor": "data center related revenue",
        "driver_scope": "company",
        "why_it_matters": "Datacenter revenue share is the first company evidence bridge.",
        "required_evidence": ["business composition segment", "datacenter-related revenue or ratio"],
        "available_evidence": ["evidence_pack.business_composition[0]=segment_name:IDC业务; revenue_ratio:55.76%"],
        "missing_evidence": ["customer/order bridge"],
        "company_transmission_path": "evidence_pack.business_composition[0]=segment_name:IDC业务; revenue_ratio:55.76%",
        "data_availability_status": "partial",
        "confidence_cap": "low",
        "not_assessable_reason": "",
        "what_was_checked": ["business_composition"],
        "source_refs": ["evidence_pack.business_composition[0]"],
        "research_question": "What datacenter revenue share is disclosed?",
        "interpretation_guard": "Segment revenue does not prove orders or utilization.",
    }
    payload.update(overrides)
    return payload


def _question(**overrides):
    payload = {
        "question": "What datacenter revenue share is disclosed?",
        "layer": "company",
        "driver_factor": "data center related revenue",
        "priority": "P1",
        "evidence_trigger": "missing_or_partial:data center related revenue",
        "why_it_matters": "Revenue share is required for company-level exposure.",
        "next_check": "Check business composition.",
        "data_availability_status": "partial",
        "confidence_cap": "low",
    }
    payload.update(overrides)
    return payload


def test_research_driver_matrix_pack_validates_full_structure():
    driver = DriverFactor.model_validate(_driver())
    question = ResearchDriverQuestion.model_validate(_question())

    pack = ResearchDriverMatrixPack.model_validate(
        {
            "stock_code": "300442",
            "stock_name": "润泽科技",
            "generated_at": "2026-05-22T00:00:00",
            "strategy_type": "ai_datacenter_infrastructure",
            "sub_type": "datacenter_operator",
            "source_evidence_pack_path": "output/evidence_pack_300442.json",
            "driver_matrix": [driver],
            "not_assessable_drivers": [],
            "driver_research_questions": [question],
            "source_bucket_summary": {
                "source_buckets": ["company_disclosure", "financial_statement"],
                "independent_source_count": 2,
                "consensus_assessment_status": "not_assessable",
            },
        }
    )

    assert pack.schema_version == "research_intelligence_p1.v1"
    assert pack.driver_matrix[0].driver_factor == "data center related revenue"
    assert pack.source_bucket_summary.independent_source_count == 2
    assert pack.safety_boundary.safe


def test_company_transmission_path_fallback_requires_not_assessable_confidence():
    driver = DriverFactor.model_validate(
        _driver(
            available_evidence=[],
            source_refs=[],
            company_transmission_path=TRANSMISSION_PATH_FALLBACK,
            data_availability_status="not_assessable",
            confidence_cap="not_assessable",
            not_assessable_reason="Current evidence pack lacks concrete company transmission nodes for this driver.",
        )
    )

    assert driver.company_transmission_path == TRANSMISSION_PATH_FALLBACK
    assert driver.confidence_cap == "not_assessable"


def test_company_transmission_path_fallback_rejects_non_not_assessable_confidence():
    with pytest.raises(ValueError, match="fallback company_transmission_path"):
        DriverFactor.model_validate(
            _driver(
                company_transmission_path=TRANSMISSION_PATH_FALLBACK,
                confidence_cap="low",
            )
        )


def test_company_transmission_path_rejects_vague_language():
    with pytest.raises(ValueError, match="vague transmission"):
        DriverFactor.model_validate(
            _driver(
                company_transmission_path="宏观向好，公司受益",
            )
        )


def test_company_transmission_path_rejects_satellite_vague_language():
    with pytest.raises(ValueError, match="vague transmission"):
        DriverFactor.model_validate(
            _driver(
                company_transmission_path="卫星通信需求向好，公司受益",
            )
        )


def test_company_transmission_path_rejects_resource_vague_language():
    with pytest.raises(ValueError, match="vague transmission"):
        DriverFactor.model_validate(
            _driver(
                company_transmission_path="商品价格上涨，公司受益",
            )
        )


def test_source_bucket_counting_deduplicates_same_bucket_and_marks_not_assessable():
    summary = SourceBucketSummary.model_validate(
        {
            "source_buckets": ["news_media", "news_media"],
            "independent_source_count": 2,
            "consensus_assessment_status": "not_assessable",
            "not_assessable_reason": LESS_THAN_TWO_BUCKETS_REASON,
        }
    )

    assert summary.source_buckets == ["news_media"]
    assert summary.independent_source_count == 1
    assert summary.consensus_assessment_status == "not_assessable"


def test_source_bucket_requires_not_assessable_when_less_than_two_buckets():
    with pytest.raises(ValueError, match="fewer than two independent source buckets"):
        SourceBucketSummary.model_validate(
            {
                "source_buckets": ["company_disclosure"],
                "independent_source_count": 1,
                "consensus_assessment_status": "consensus",
                "not_assessable_reason": LESS_THAN_TWO_BUCKETS_REASON,
            }
        )
