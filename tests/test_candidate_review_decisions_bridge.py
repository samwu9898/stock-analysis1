# -*- coding: utf-8 -*-

import inspect

import pytest

import src.fundamental_skill.research_report.candidate_review_decisions_bridge as bridge_decisions_module
from src.fundamental_skill.research_report.candidate_review_decisions_bridge import (
    BRIDGE_REVIEW_DECISIONS,
    BRIDGE_REVIEW_DECISIONS_VERSION,
    BRIDGE_REVIEW_SOURCE_TYPES,
    CandidateReviewDecisionsBridgePathError,
    CandidateReviewDecisionsBridgeSecretError,
    CandidateReviewDecisionsBridgeValidationError,
    build_bridge_priority_review_decision,
    build_bridge_review_decision,
    build_bridge_review_decisions_payload,
    build_official_candidate_review_decision,
    build_provider_candidate_review_decision,
    validate_bridge_review_decision,
    validate_bridge_review_decisions_payload,
)


PROVIDER_ARTIFACT = "output/ground_truth_candidates/20260527T155056/600406/fact_candidates.json"
OFFICIAL_ARTIFACT = "output/official_disclosures/20260528T182057Z/600406/official_disclosure_candidates_review.json"
BRIDGE_ARTIFACT = "output/candidate_source_bridges/20260529T034024Z/600406/candidate_source_bridge_review.json"


def _provider_decision(**overrides) -> dict:
    params = {
        "decision_id": "600406-provider-001",
        "candidate_id": "provider-001",
        "artifact_ref": PROVIDER_ARTIFACT,
        "field_path": "financial_metrics.revenue",
        "period": "2025H1",
        "unit": "CNY",
        "denominator": "company_total",
    }
    params.update(overrides)
    return build_provider_candidate_review_decision(**params)


def _official_decision(**overrides) -> dict:
    params = {
        "decision_id": "600406-official-001",
        "candidate_id": "official-001",
        "artifact_ref": OFFICIAL_ARTIFACT,
        "field_path": "business_composition.revenue",
        "period": "2025H1",
        "unit": "CNY",
        "denominator": "company_total",
        "extraction_confidence": "structured_high",
        "has_trace": True,
        "decision": "accepted_for_report_candidate",
    }
    params.update(overrides)
    return build_official_candidate_review_decision(**params)


def _bridge_priority_decision(**overrides) -> dict:
    params = {
        "decision_id": "600406-bridge-001",
        "candidate_id": "priority-001",
        "artifact_ref": BRIDGE_ARTIFACT,
        "bridge_ref": BRIDGE_ARTIFACT,
        "field_path": "business_composition.revenue",
        "period": "2025H1",
        "unit": "CNY",
        "priority_class": "official_candidate",
        "reason": "official evidence review task",
    }
    params.update(overrides)
    return build_bridge_priority_review_decision(**params)


def test_constants_match_bridge_sources_design():
    assert BRIDGE_REVIEW_DECISIONS_VERSION == "candidate_review_decisions_bridge.v1"
    assert BRIDGE_REVIEW_SOURCE_TYPES == {
        "provider_candidates",
        "official_disclosure_candidates",
        "bridge_review_priority",
    }
    assert {
        "accepted_for_report_candidate",
        "manual_review_required",
        "blocked_by_caveat",
        "rejected",
        "needs_more_evidence",
        "conflict_requires_review",
    } <= BRIDGE_REVIEW_DECISIONS


def test_build_valid_official_review_decision():
    row = _official_decision()

    assert row["source_type"] == "official_disclosure_candidates"
    assert row["decision"] == "accepted_for_report_candidate"
    assert row["review_status"] == "reviewed_candidate_ready"
    assert "accepted_for_report_candidate_not_verified" in row["caveats"]
    assert row["not_for_trading_advice"] is True
    validate_bridge_review_decision(row)


def test_build_valid_provider_review_decision():
    row = _provider_decision()

    assert row["source_type"] == "provider_candidates"
    assert row["decision"] == "manual_review_required"
    assert row["review_status"] == "pending_human_review"
    assert row["not_for_trading_advice"] is True
    validate_bridge_review_decision(row)


def test_build_valid_bridge_priority_review_decision():
    row = _bridge_priority_decision()

    assert row["source_type"] == "bridge_review_priority"
    assert row["follow_up_class"] == "official_evidence_review"
    assert row["decision"] == "manual_review_required"
    validate_bridge_review_decision(row)


def test_build_payload_with_provider_official_and_bridge_priority_decisions():
    decisions = [_provider_decision(), _official_decision(), _bridge_priority_decision()]

    payload = build_bridge_review_decisions_payload(
        code="600406",
        company_name="Guodian NARI",
        decisions=decisions,
        bridge_artifact_ref=BRIDGE_ARTIFACT,
        created_at="2026-05-29T00:00:00+00:00",
    )

    assert payload["version"] == BRIDGE_REVIEW_DECISIONS_VERSION
    assert payload["code"] == "600406"
    assert payload["bridge_artifact_ref"] == BRIDGE_ARTIFACT
    assert payload["summary"]["total_decisions"] == 3
    assert payload["summary"]["provider_decision_count"] == 1
    assert payload["summary"]["official_decision_count"] == 1
    assert payload["summary"]["bridge_priority_decision_count"] == 1
    assert payload["summary"]["manual_review_required_count"] == 2
    assert payload["summary"]["accepted_for_report_candidate_count"] == 1
    validate_bridge_review_decisions_payload(payload)


def test_payload_accepts_valid_summary_counts():
    decisions = [_provider_decision(), _official_decision()]
    payload = build_bridge_review_decisions_payload(
        code="600406",
        company_name="Guodian NARI",
        decisions=decisions,
        bridge_artifact_ref=BRIDGE_ARTIFACT,
        summary={
            "total_decisions": 2,
            "provider_decision_count": 1,
            "official_decision_count": 1,
            "bridge_priority_decision_count": 0,
            "manual_review_required_count": 1,
            "blocked_by_caveat_count": 0,
            "accepted_for_report_candidate_count": 1,
            "conflict_requires_review_count": 0,
        },
    )

    assert payload["summary"]["total_decisions"] == 2
    validate_bridge_review_decisions_payload(payload)


def test_validate_payload_success_with_empty_decisions():
    payload = build_bridge_review_decisions_payload(code="600406", company_name="Guodian NARI", decisions=[])

    assert payload["summary"]["total_decisions"] == 0
    validate_bridge_review_decisions_payload(payload)


def test_reject_invalid_source_type():
    with pytest.raises(CandidateReviewDecisionsBridgeValidationError):
        build_bridge_review_decision(
            decision_id="d1",
            source_type="official_disclosure",
            candidate_id="candidate-001",
            artifact_ref=OFFICIAL_ARTIFACT,
            decision="manual_review_required",
            decision_reason="bad source type",
        )


def test_reject_empty_candidate_id():
    with pytest.raises(CandidateReviewDecisionsBridgeValidationError):
        build_bridge_review_decision(
            decision_id="d1",
            source_type="official_disclosure_candidates",
            candidate_id="",
            artifact_ref=OFFICIAL_ARTIFACT,
            decision="manual_review_required",
            decision_reason="empty candidate id",
        )


def test_reject_invalid_decision_enum():
    with pytest.raises(CandidateReviewDecisionsBridgeValidationError):
        build_bridge_review_decision(
            decision_id="d1",
            source_type="official_disclosure_candidates",
            candidate_id="candidate-001",
            artifact_ref=OFFICIAL_ARTIFACT,
            decision="verified",
            decision_reason="bad decision",
        )


@pytest.mark.parametrize("artifact_ref", ["C:/tmp/fact.json", "C:\\tmp\\fact.json", "/tmp/fact.json", "~/fact.json"])
def test_reject_absolute_artifact_ref(artifact_ref):
    with pytest.raises(CandidateReviewDecisionsBridgePathError):
        build_bridge_review_decision(
            decision_id="d1",
            source_type="provider_candidates",
            candidate_id="candidate-001",
            artifact_ref=artifact_ref,
            decision="manual_review_required",
            decision_reason="bad path",
        )


@pytest.mark.parametrize("artifact_ref", ["../output/fact.json", "output/../fact.json", "output//fact.json"])
def test_reject_path_traversal_artifact_ref(artifact_ref):
    with pytest.raises(CandidateReviewDecisionsBridgePathError):
        build_bridge_review_decision(
            decision_id="d1",
            source_type="provider_candidates",
            candidate_id="candidate-001",
            artifact_ref=artifact_ref,
            decision="manual_review_required",
            decision_reason="bad path",
        )


@pytest.mark.parametrize("bridge_ref", ["C:/tmp/bridge.json", "C:\\tmp\\bridge.json", "/tmp/bridge.json", "~/bridge.json"])
def test_reject_absolute_bridge_ref(bridge_ref):
    with pytest.raises(CandidateReviewDecisionsBridgePathError):
        _bridge_priority_decision(bridge_ref=bridge_ref)


@pytest.mark.parametrize("bridge_ref", ["../output/bridge.json", "output/../bridge.json", "output//bridge.json"])
def test_reject_path_traversal_bridge_ref(bridge_ref):
    with pytest.raises(CandidateReviewDecisionsBridgePathError):
        _bridge_priority_decision(bridge_ref=bridge_ref)


def test_reject_missing_not_for_trading_advice():
    row = _provider_decision()
    row.pop("not_for_trading_advice")
    with pytest.raises(CandidateReviewDecisionsBridgeValidationError):
        validate_bridge_review_decision(row)

    payload = build_bridge_review_decisions_payload(code="600406", company_name="Guodian NARI", decisions=[])
    payload["not_for_trading_advice"] = False
    with pytest.raises(CandidateReviewDecisionsBridgeValidationError):
        validate_bridge_review_decisions_payload(payload)


@pytest.mark.parametrize("patch", [{"verified_fact": True}, {"auto_verified": True}, {"review_status": "verified"}])
def test_reject_verified_fact_auto_verified_and_verified_status(patch):
    row = _provider_decision()
    row.update(patch)
    with pytest.raises(CandidateReviewDecisionsBridgeValidationError):
        validate_bridge_review_decision(row)


@pytest.mark.parametrize(
    "patch",
    [
        {"fixture_promotion": True},
        {"promote_to_fixture": True},
        {"fixture_write_allowed": True},
        {"ground_truth_fixture_write": True},
    ],
)
def test_reject_fixture_promotion_marker(patch):
    row = _provider_decision()
    row.update(patch)
    with pytest.raises(CandidateReviewDecisionsBridgeValidationError):
        validate_bridge_review_decision(row)


@pytest.mark.parametrize(
    "patch",
    [{"provider_primary": "official"}, {"primary_provider": "official"}, {"provider_primary_switch": True}],
)
def test_reject_provider_primary_switch(patch):
    row = _provider_decision()
    row.update(patch)
    with pytest.raises(CandidateReviewDecisionsBridgeValidationError):
        validate_bridge_review_decision(row)


@pytest.mark.parametrize(
    "patch",
    [{"buy": True}, {"sell": True}, {"target_price": 42}, {"position": "increase"}, {"portfolio_weight": 0.2}],
)
def test_reject_trading_recommendation_keys(patch):
    row = _provider_decision()
    row.update(patch)
    with pytest.raises(CandidateReviewDecisionsBridgeValidationError):
        validate_bridge_review_decision(row)


@pytest.mark.parametrize(
    "patch",
    [
        {"api_token": "value"},
        {"decision_reason": "review token: abc"},
        {"decision_reason": "Abcdefghijklmnopqrstuvwxyz123456"},
    ],
)
def test_reject_token_like_key_or_value(patch):
    row = _provider_decision()
    row.update(patch)
    with pytest.raises(CandidateReviewDecisionsBridgeSecretError):
        validate_bridge_review_decision(row)


def test_reject_token_like_dict_key_without_leaking_key():
    secret_key = "A9abcdefABCDEF1234567890abcdefABCDEF1234567890z"
    row = _provider_decision()
    row[secret_key] = "value"

    with pytest.raises(CandidateReviewDecisionsBridgeSecretError) as exc:
        validate_bridge_review_decision(row)

    message = str(exc.value)
    assert "<masked>" in message
    assert "<masked_key>" in message
    assert secret_key not in message


@pytest.mark.parametrize(
    "bad_value",
    [
        "Bearer abc.def.ghi",
        "mcp://local-control",
        "config/.env.local",
        "C:\\Users\\Admin\\.ssh\\id_rsa",
    ],
)
def test_reject_bearer_mcp_dotenv_and_local_secret_path_without_leaking_value(bad_value):
    row = _provider_decision()
    row["decision_reason"] = bad_value

    with pytest.raises(CandidateReviewDecisionsBridgeSecretError) as exc:
        validate_bridge_review_decision(row)

    assert "<masked>" in str(exc.value)
    assert bad_value not in str(exc.value)


def test_accepted_for_report_candidate_is_not_verified_fact():
    row = _official_decision()

    assert row["decision"] == "accepted_for_report_candidate"
    assert row["review_status"] != "verified"
    assert "verified_fact" not in row
    assert "auto_verified" not in row
    assert "accepted_for_report_candidate_not_verified" in row["caveats"]


def test_manual_review_required_remains_review_only():
    row = _provider_decision()

    assert row["decision"] == "manual_review_required"
    assert row["not_for_trading_advice"] is True
    assert "fixture_write_allowed" not in row
    assert "verified_fact" not in row


def test_blocked_by_caveat_for_missing_period_unit_denominator():
    row = _official_decision(period="", unit="CNY", denominator="")

    assert row["decision"] == "blocked_by_caveat"
    assert "missing_period_unit_or_denominator" in row["caveats"]


def test_blocked_by_caveat_for_source_lineage_mismatch():
    row = _provider_decision(source_lineage_mismatch=True)

    assert row["decision"] == "blocked_by_caveat"
    assert "source_lineage_mismatch" in row["caveats"]


def test_caveat_only_evidence_does_not_generate_accepted_report_candidate():
    row = _official_decision(caveat_only=True)

    assert row["decision"] == "blocked_by_caveat"
    assert "caveat_only_official_evidence" in row["caveats"]


def test_structured_medium_stays_manual_review_when_complete():
    row = _official_decision(extraction_confidence="structured_medium")

    assert row["decision"] == "manual_review_required"
    assert "structured_medium_requires_manual_review" in row["caveats"]


def test_conflict_requires_review_works():
    row = _provider_decision(conflict_with_official=True)

    assert row["decision"] == "conflict_requires_review"
    assert row["review_status"] == "reviewed_conflict_open"
    assert "provider_official_conflict" in row["caveats"]


def test_bridge_schema_mismatch_priority_becomes_needs_more_evidence():
    row = _bridge_priority_decision(schema_mismatch=True)

    assert row["decision"] == "needs_more_evidence"
    assert row["follow_up_class"] == "framework_schema_follow_up"
    assert "cross_source_conflict_detection_not_performed_schema_mismatch" in row["caveats"]


def test_no_real_output_writes_or_old_main_path_mutation_api():
    assert not hasattr(bridge_decisions_module, "write_bridge_review_decisions_payload")
    assert not hasattr(bridge_decisions_module, "write_candidate_review_decisions")
    assert not hasattr(bridge_decisions_module, "build_candidate_review_decisions")


def test_no_provider_env_network_mcp_reader_or_heavy_parser_imports():
    source = inspect.getsource(bridge_decisions_module)
    forbidden_fragments = [
        "cninfo",
        "tushare",
        "akshare",
        "data_providers",
        "provider_router",
        "import requests",
        "from requests",
        "import urllib",
        "from urllib",
        "os.environ",
        "getenv",
        "subprocess",
        "pytesseract",
        "easyocr",
        "pdfplumber",
        "pypdf",
        "import docx",
        "from docx",
        "BeautifulSoup",
        "bs4",
        "pandas",
        "openpyxl",
        "old_runner",
        "open(",
        "write_text",
        "mkdir",
    ]

    for fragment in forbidden_fragments:
        assert fragment not in source
