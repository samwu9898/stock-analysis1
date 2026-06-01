# -*- coding: utf-8 -*-

import copy

import pytest

from src.fundamental_skill.data_verification.synthetic_official_disclosure_pipeline_dry_run import (
    SYNTHETIC_OFFICIAL_DISCLOSURE_PIPELINE_DRY_RUN_RESULT_VERSION,
    build_synthetic_official_disclosure_pipeline_dry_run_result,
    validate_synthetic_official_disclosure_pipeline_dry_run_result,
)
from src.fundamental_skill.data_verification.validators import OfficialVerificationValidationError


def _candidate(**overrides):
    candidate = {
        "schema_version": "official_disclosure_discovery_candidate.v1",
        "discovery_candidate_id": "",
        "stock_code": "600406",
        "company_name": "Guodian NARI",
        "exchange": "SSE",
        "period_key": "2024FY",
        "period_end_date": "2024-12-31",
        "announcement_type": "annual_report",
        "source_type": "cninfo_official_pdf",
        "source_url": "https://static.cninfo.com.cn/finalpage/2025-04-30/official.pdf",
        "source_title": "600406 2024 annual report",
        "disclosure_date": "2025-04-30",
        "discovered_at_utc": "2026-06-01T00:00:00Z",
        "discovery_method": "cninfo_search_result",
        "source_domain": "",
        "raw_candidate_metadata": {"query": "600406 annual report"},
        "normalized_candidate_metadata": {},
        "rejection_reason": "",
        "caveats": [],
        "not_for_trading_advice": True,
    }
    candidate.update(overrides)
    return candidate


def _build(candidates, **overrides):
    payload = {
        "stock_code": "600406",
        "company_name": "Guodian NARI",
        "query_period": {"period_key": "2024FY", "period_end_date": "2024-12-31"},
        "requested_announcement_type": "annual_report",
        "input_discovery_candidates": candidates,
    }
    payload.update(overrides)
    return build_synthetic_official_disclosure_pipeline_dry_run_result(**payload)


def _contains_key(payload, key):
    if isinstance(payload, dict):
        if key in payload:
            return True
        return any(_contains_key(value, key) for value in payload.values())
    if isinstance(payload, list):
        return any(_contains_key(value, key) for value in payload)
    return False


def test_valid_single_cninfo_synthetic_candidate_dry_run():
    result = _build([_candidate()])

    assert result["schema_version"] == SYNTHETIC_OFFICIAL_DISCLOSURE_PIPELINE_DRY_RUN_RESULT_VERSION
    assert result["not_for_trading_advice"] is True
    assert len(result["normalized_discovery_candidates"]) == 1
    assert result["rejected_discovery_candidates"] == []
    assert len(result["registry_entry_candidates"]) == 1
    assert result["registry_entry_candidates"][0]["file_sha256"] == ""
    assert result["locator_result"]["locator_status"] == "found_single_official_candidate"
    assert result["locator_result"]["selected_official_source_id"]
    assert result["readiness_skeleton"]["readiness_status"] == "ready_for_verification_gate_input"
    assert result["blocked_reasons"] == []
    assert result["data_gap_plan"] == []
    assert not _contains_key(result, "official_metric_fact")
    assert not _contains_key(result, "provider_official_conflict")


def test_valid_sse_exchange_synthetic_candidate_dry_run():
    result = _build(
        [
            _candidate(
                source_type="sse_exchange_announcement",
                source_url="https://www.sse.com.cn/disclosure/listedinfo/announcement/c/official.pdf",
                discovery_method="sse_announcement_list",
                source_domain="",
            )
        ]
    )

    assert result["normalized_discovery_candidates"][0]["source_domain"] == "www.sse.com.cn"
    assert result["registry_entry_candidates"][0]["source_type"] == "sse_exchange_announcement"
    assert result["locator_result"]["locator_status"] == "found_single_official_candidate"


def test_valid_exchange_pdf_synthetic_candidate_dry_run():
    result = _build(
        [
            _candidate(
                source_type="exchange_official_pdf",
                source_url="https://disc.static.szse.cn/download/disc/official.pdf",
                discovery_method="exchange_announcement_list",
                source_domain="",
            )
        ]
    )

    assert result["normalized_discovery_candidates"][0]["source_domain"] == "disc.static.szse.cn"
    assert result["locator_result"]["locator_status"] == "found_single_official_candidate"


@pytest.mark.parametrize(
    "source_type,reason",
    [
        ("mirror_source_candidate", "mirror_source_not_official"),
        ("provider_source_candidate", "provider_source_not_official"),
        ("unknown_source_candidate", "unknown_source_type"),
    ],
)
def test_mirror_provider_unknown_rejected(source_type, reason):
    result = _build(
        [
            _candidate(
                source_type=source_type,
                source_url="",
                source_title="",
                disclosure_date="",
                source_domain="",
            )
        ]
    )

    assert result["registry_entry_candidates"] == []
    assert result["locator_result"]["locator_status"] == "rejected_all_candidates"
    assert result["rejected_discovery_candidates"][0]["rejection_reason"] == reason
    assert "registry:no_handoff_eligible_official_candidate" in result["blocked_reasons"]


def test_local_cache_intent_inert_and_rejected():
    result = _build(
        [
            _candidate(
                source_type="local_official_cache",
                source_url="",
                source_title="",
                disclosure_date="",
                source_domain="",
                raw_candidate_metadata={"cache_ref": "local official metadata only"},
            )
        ]
    )

    assert result["rejected_discovery_candidates"][0]["rejection_reason"] == "local_cache_inert"
    assert result["locator_result"]["locator_status"] == "rejected_all_candidates"


def test_all_candidates_rejected_blocks_result():
    result = _build(
        [
            _candidate(source_type="mirror_source_candidate", source_url="", source_title="", disclosure_date="", source_domain=""),
            _candidate(source_type="provider_source_candidate", source_url="", source_title="", disclosure_date="", source_domain=""),
        ]
    )

    assert result["normalized_discovery_candidates"]
    assert result["registry_entry_candidates"] == []
    assert len(result["rejected_discovery_candidates"]) == 2
    assert result["locator_result"]["locator_status"] == "rejected_all_candidates"
    assert result["data_gap_plan"]


def test_no_candidates_blocks_result():
    result = _build([])

    assert result["input_discovery_candidates"] == []
    assert result["locator_result"]["locator_status"] == "no_official_source_found"
    assert "no_input_discovery_candidates" in result["blocked_reasons"]
    assert "provide_synthetic_discovery_candidate_payload" in result["data_gap_plan"]


def test_multiple_official_candidates_review_required():
    result = _build(
        [
            _candidate(),
            _candidate(
                source_type="sse_exchange_announcement",
                source_url="https://www.sse.com.cn/disclosure/listedinfo/announcement/c/official.pdf",
                discovery_method="sse_announcement_list",
                source_domain="",
            ),
        ]
    )

    assert result["locator_result"]["locator_status"] == "found_multiple_candidates_review_required"
    assert result["locator_result"]["selected_official_source_id"] == ""
    assert "locator:multiple_official_candidates_review_required" in result["blocked_reasons"]
    assert "select_one_official_source_candidate_by_review" in result["data_gap_plan"]
    assert result["readiness_skeleton"]["readiness_status"] == "review_required"


def test_source_conflict_blocks_or_requires_review():
    source_url = "https://static.cninfo.com.cn/finalpage/2025-04-30/official.pdf"
    result = _build(
        [
            _candidate(source_url=source_url, source_title="600406 2024 annual report"),
            _candidate(source_url=source_url, source_title="600406 corrected annual report"),
        ]
    )

    assert result["locator_result"]["locator_status"] == "found_multiple_candidates_review_required"
    assert result["locator_result"]["source_conflicts"]
    assert "locator:source_conflict_review_required" in result["blocked_reasons"]


def test_missing_candidate_metadata_blocks():
    result = _build([_candidate(company_name="")])

    assert result["normalized_discovery_candidates"] == []
    assert result["rejected_discovery_candidates"][0]["rejection_reason"] == "missing_required_metadata"
    assert result["locator_result"]["locator_status"] == "rejected_all_candidates"


def test_missing_source_url_blocks():
    result = _build([_candidate(source_url="", source_domain="")])

    assert result["rejected_discovery_candidates"][0]["rejection_reason"] == "missing_official_url"
    assert result["locator_result"]["locator_status"] == "rejected_all_candidates"


def test_source_domain_mismatch_blocks():
    result = _build([_candidate(source_domain="evil.example")])

    assert result["rejected_discovery_candidates"][0]["rejection_reason"] == "invalid_source_domain"
    assert result["locator_result"]["locator_status"] == "rejected_all_candidates"


def test_missing_run_metadata_fails_closed():
    with pytest.raises(OfficialVerificationValidationError, match="company_name"):
        _build([_candidate()], company_name="")


def test_deterministic_result_behavior_from_explicit_payload():
    first = _build([_candidate()])
    second = _build([_candidate()])

    assert first == second


def test_registry_candidates_come_only_from_explicit_normalized_metadata():
    result = _build(
        [
            _candidate(
                source_title="600406 explicit annual report",
                raw_candidate_metadata={"source_title": "untrusted metadata title"},
                normalized_candidate_metadata={"source_title": "untrusted normalized title"},
            )
        ]
    )

    registry_entry = result["registry_entry_candidates"][0]
    assert registry_entry["source_title"] == "600406 explicit annual report"
    assert registry_entry["source_id"].startswith("synthetic_registry_entry_from_discovery_candidate_")
    assert registry_entry["local_cache_path"] == ""
    assert registry_entry["file_sha256"] == ""


def test_readiness_skeleton_insufficient_rejected_for_blocked_or_review_result():
    result = _build(
        [
            _candidate(),
            _candidate(
                source_type="sse_exchange_announcement",
                source_url="https://www.sse.com.cn/disclosure/listedinfo/announcement/c/official.pdf",
                discovery_method="sse_announcement_list",
                source_domain="",
            ),
        ]
    )
    result["readiness_skeleton"]["required_explicit_inputs"] = []

    with pytest.raises(OfficialVerificationValidationError, match="readiness_skeleton|required_explicit_inputs"):
        validate_synthetic_official_disclosure_pipeline_dry_run_result(result)


@pytest.mark.parametrize("forbidden_key", ["verified_fact", "official_metric_fact", "provider_official_conflict"])
def test_dry_run_result_cannot_generate_forbidden_fact_or_conflict_payloads(forbidden_key):
    result = _build([_candidate()])
    unsafe = copy.deepcopy(result)
    unsafe["readiness_skeleton"][forbidden_key] = {"not_for_trading_advice": True}

    with pytest.raises(OfficialVerificationValidationError, match="forbidden|metric|conflict"):
        validate_synthetic_official_disclosure_pipeline_dry_run_result(unsafe)
