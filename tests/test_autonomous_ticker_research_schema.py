# -*- coding: utf-8 -*-

import pytest

from src.fundamental_skill.research_planning.autonomous_ticker_research_schema import (
    REQUIRED_RESEARCH_PACK_OUTPUTS,
    SCHEMA_VERSION,
    build_hypothesis,
    build_planning_payload,
    validate_hypothesis,
    validate_planning_payload,
)


def _valid_hypothesis(**overrides):
    payload = {
        "hypothesis_id": "h_industry_001",
        "hypothesis_type": "industry",
        "hypothesis_text": "Company may be exposed to grid automation demand.",
        "evidence_refs": ["business_description_evidence[0]"],
        "confidence": "medium",
        "caveats": ["Planning hypothesis only."],
        "required_follow_up_data": ["Segment revenue evidence"],
        "allowed_downstream_use": "planning_only",
    }
    payload.update(overrides)
    return payload


def _valid_payload(**overrides):
    payload = build_planning_payload(
        stock_code="600406",
        company_name="NARI Technology",
        generated_at="2026-05-29T00:00:00+00:00",
        identity_resolution_status="resolved",
        market="CN",
        exchange="SSE",
        evidence_inventory=["company profile summary"],
        business_description_evidence=["grid automation business description"],
        industry_hypotheses=[_valid_hypothesis()],
        key_research_questions=["Which segments drive revenue?"],
        required_data_plan=["Collect segment revenue disclosure"],
        missing_data_artifacts=["segment revenue table"],
        evidence_confidence="low",
        hypothesis_confidence="medium",
        report_readiness_level="data_collection_required",
        fail_closed_reason="Accepted report requires more evidence.",
        caveats=["No model or provider has been called."],
    )
    payload.update(overrides)
    return payload


def _placeholder_titles(placeholders):
    titles = set()
    for key, value in placeholders.items():
        titles.add(str(key).replace("_", " ").title())
        if isinstance(value, dict) and "title" in value:
            titles.add(value["title"])
    return titles


def test_valid_minimal_planning_payload():
    payload = build_planning_payload(
        stock_code="600406",
        company_name="NARI Technology",
        generated_at="2026-05-29T00:00:00+00:00",
        identity_resolution_status="resolved",
        market="CN",
        exchange="SSE",
        report_readiness_level="data_collection_required",
        fail_closed_reason="Planning only; data collection is required.",
    )

    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["not_for_trading_advice"] is True
    assert payload["can_generate_accepted_report"] is False


def test_valid_hypothesis():
    hypothesis = build_hypothesis(
        hypothesis_id="h_industry_001",
        hypothesis_type="industry",
        hypothesis_text="Company may be exposed to grid automation demand.",
        evidence_refs=["business_description_evidence[0]"],
        confidence="medium",
        caveats=["Planning hypothesis only."],
        required_follow_up_data=["Segment revenue evidence"],
        allowed_downstream_use="planning_only",
    )

    assert hypothesis["hypothesis_id"] == "h_industry_001"


def test_invalid_schema_version_is_rejected():
    payload = _valid_payload(schema_version="wrong.v1")

    with pytest.raises(ValueError, match="schema_version"):
        validate_planning_payload(payload)


def test_invalid_stock_code_is_rejected():
    payload = _valid_payload(stock_code="ABC")

    with pytest.raises(ValueError, match="stock_code"):
        validate_planning_payload(payload)


def test_missing_not_for_trading_advice_is_rejected():
    payload = _valid_payload()
    payload.pop("not_for_trading_advice")

    with pytest.raises(ValueError, match="not_for_trading_advice"):
        validate_planning_payload(payload)


def test_false_not_for_trading_advice_is_rejected():
    payload = _valid_payload(not_for_trading_advice=False)

    with pytest.raises(ValueError, match="not_for_trading_advice"):
        validate_planning_payload(payload)


def test_hypothesis_without_evidence_refs_is_rejected():
    hypothesis = _valid_hypothesis(evidence_refs=[])

    with pytest.raises(ValueError, match="evidence_refs"):
        validate_hypothesis(hypothesis)


def test_blocked_data_gap_hypothesis_may_have_empty_evidence_refs():
    hypothesis = _valid_hypothesis(
        hypothesis_type="data_gap",
        hypothesis_text="Segment revenue evidence is missing.",
        evidence_refs=[],
        confidence="not_assessable",
        allowed_downstream_use="blocked_until_review",
    )

    assert validate_hypothesis(hypothesis)["evidence_refs"] == []


def test_hypothesis_verified_downstream_use_is_rejected():
    hypothesis = _valid_hypothesis(allowed_downstream_use="accepted_report_fact")

    with pytest.raises(ValueError, match="verified fact|accepted"):
        validate_hypothesis(hypothesis)


def test_accepted_readiness_inconsistent_is_rejected():
    payload = _valid_payload(can_generate_accepted_report=True)

    with pytest.raises(ValueError, match="accepted"):
        validate_planning_payload(payload)


def test_blocked_readiness_inconsistent_is_rejected():
    payload = _valid_payload(
        report_readiness_level="blocked",
        can_generate_experimental_report=True,
        fail_closed_reason="Blocked must fail closed.",
    )

    with pytest.raises(ValueError, match="blocked"):
        validate_planning_payload(payload)


def test_data_collection_required_rejects_experimental_report():
    payload = _valid_payload(can_generate_experimental_report=True)

    with pytest.raises(ValueError, match="experimental|can_generate_experimental_report"):
        validate_planning_payload(payload)


def test_classification_review_required_rejects_experimental_report():
    payload = _valid_payload(
        report_readiness_level="classification_review_required",
        can_generate_experimental_report=True,
        fail_closed_reason="Classification review must fail closed.",
    )

    with pytest.raises(ValueError, match="experimental|can_generate_experimental_report"):
        validate_planning_payload(payload)


def test_evidence_conflict_review_required_rejects_experimental_report():
    payload = _valid_payload(
        report_readiness_level="evidence_conflict_review_required",
        can_generate_experimental_report=True,
        fail_closed_reason="Evidence conflict review must fail closed.",
    )

    with pytest.raises(ValueError, match="experimental|can_generate_experimental_report"):
        validate_planning_payload(payload)


def test_experimental_readiness_does_not_allow_accepted_report():
    payload = _valid_payload(
        report_readiness_level="experimental_report_ready",
        can_generate_accepted_report=True,
        can_generate_experimental_report=True,
    )

    with pytest.raises(ValueError, match="accepted"):
        validate_planning_payload(payload)


def test_research_pack_placeholders_keep_required_outputs():
    payload = _valid_payload()

    titles = _placeholder_titles(payload["research_pack_placeholders"])

    for title in REQUIRED_RESEARCH_PACK_OUTPUTS:
        assert title in titles
