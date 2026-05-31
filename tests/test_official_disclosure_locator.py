# -*- coding: utf-8 -*-

import pytest

from src.fundamental_skill.data_verification.official_disclosure_locator import (
    classify_locator_status,
    reject_non_official_candidates,
    select_single_official_candidate,
)
from src.fundamental_skill.data_verification.validators import (
    OfficialVerificationValidationError,
    validate_official_disclosure_locator_result,
)


SHA = "c" * 64


def _entry(**overrides):
    entry = {
        "schema_version": "official_source_registry_entry.v1",
        "source_id": "src_600406_2024fy_cninfo",
        "stock_code": "600406",
        "company_name": "Guodian NARI",
        "period_key": "2024FY",
        "period_end_date": "2024-12-31",
        "announcement_type": "annual_report",
        "source_type": "cninfo_official_pdf",
        "source_url": "https://static.cninfo.com.cn/finalpage/2025-04-30/official.pdf",
        "source_title": "600406 2024 annual report",
        "disclosure_date": "2025-04-30",
        "local_cache_path": "",
        "file_sha256": SHA,
        "retrieved_at_utc": "2026-05-31T00:00:00Z",
        "source_status": "official_candidate",
        "source_refresh_policy": "manual_review_only",
        "registry_version": "registry.v1",
        "source_version": "original",
        "rejection_reason": "",
        "caveats": [],
        "not_for_trading_advice": True,
    }
    entry.update(overrides)
    return entry


def _result(**overrides):
    result = {
        "schema_version": "official_disclosure_locator_result.v1",
        "stock_code": "600406",
        "company_name": "Guodian NARI",
        "query_period": {"period_key": "2024FY", "period_end_date": "2024-12-31"},
        "requested_announcement_type": "annual_report",
        "candidates": [_entry()],
        "selected_official_source_id": "src_600406_2024fy_cninfo",
        "rejected_candidates": [],
        "source_conflicts": [],
        "locator_status": "found_single_official_candidate",
        "blocked_reason": "",
        "caveats": [],
        "not_for_trading_advice": True,
    }
    result.update(overrides)
    return result


def test_single_official_candidate_selected():
    candidates = [_entry()]

    validate_official_disclosure_locator_result(_result(candidates=candidates))

    assert select_single_official_candidate(candidates)["source_id"] == "src_600406_2024fy_cninfo"
    assert classify_locator_status(candidates, [], []) == "found_single_official_candidate"


def test_multiple_official_candidates_review_required_and_no_silent_selection():
    candidates = [
        _entry(),
        _entry(
            source_id="src_600406_2024fy_sse",
            source_type="sse_exchange_announcement",
            source_url="https://www.sse.com.cn/disclosure/listedinfo/announcement/c/official.pdf",
        ),
    ]
    result = _result(
        candidates=candidates,
        selected_official_source_id="",
        locator_status="found_multiple_candidates_review_required",
        blocked_reason="multiple official candidates require review",
        caveats=["manual review required"],
    )

    validate_official_disclosure_locator_result(result)

    with pytest.raises(OfficialVerificationValidationError, match="multiple"):
        select_single_official_candidate(candidates)
    assert classify_locator_status(candidates, [], []) == "found_multiple_candidates_review_required"


def test_multiple_official_candidates_cannot_select_silently():
    result = _result(
        candidates=[
            _entry(),
            _entry(
                source_id="src_600406_2024fy_sse",
                source_type="sse_exchange_announcement",
                source_url="https://www.sse.com.cn/disclosure/listedinfo/announcement/c/official.pdf",
            ),
        ],
        selected_official_source_id="src_600406_2024fy_cninfo",
        locator_status="found_multiple_candidates_review_required",
        blocked_reason="multiple official candidates require review",
    )

    with pytest.raises(OfficialVerificationValidationError, match="cannot be selected silently"):
        validate_official_disclosure_locator_result(result)


def test_found_single_status_rejects_multiple_selectable_candidates():
    result = _result(
        candidates=[
            _entry(),
            _entry(
                source_id="src_600406_2024fy_sse",
                source_type="sse_exchange_announcement",
                source_url="https://www.sse.com.cn/disclosure/listedinfo/announcement/c/official.pdf",
            ),
        ],
        selected_official_source_id="src_600406_2024fy_cninfo",
        locator_status="found_single_official_candidate",
    )

    with pytest.raises(OfficialVerificationValidationError, match="exactly one"):
        validate_official_disclosure_locator_result(result)


def test_selected_candidate_must_be_complete_registry_entry():
    result = _result(
        candidates=[
            {
                "source_id": "src_600406_2024fy_minimal",
                "source_type": "cninfo_official_pdf",
                "source_status": "official_candidate",
                "not_for_trading_advice": True,
            }
        ],
        selected_official_source_id="src_600406_2024fy_minimal",
    )

    with pytest.raises(OfficialVerificationValidationError, match="complete registry entry"):
        validate_official_disclosure_locator_result(result)


def test_no_official_source_found():
    result = _result(
        candidates=[],
        selected_official_source_id="",
        locator_status="no_official_source_found",
        blocked_reason="no official source found",
    )

    validate_official_disclosure_locator_result(result)

    assert classify_locator_status([], [], []) == "no_official_source_found"


def test_rejected_all_candidates():
    rejected = _entry(
        source_type="mirror_source_candidate",
        source_url="https://finance.sina.com.cn/mirror/official.pdf",
        source_status="rejected_mirror",
        rejection_reason="mirror source cannot be official",
        caveats=["discovery only"],
    )
    result = _result(
        candidates=[rejected],
        selected_official_source_id="",
        rejected_candidates=[rejected],
        locator_status="rejected_all_candidates",
        blocked_reason="all candidates rejected",
    )

    validate_official_disclosure_locator_result(result)

    assert classify_locator_status([rejected], [rejected], []) == "rejected_all_candidates"
    assert reject_non_official_candidates([rejected]) == [rejected]


@pytest.mark.parametrize(
    "source_type,source_status,rejection_reason",
    [
        ("mirror_source_candidate", "rejected_mirror", "mirror source cannot be official"),
        ("provider_source_candidate", "rejected_provider_endpoint", "provider endpoint cannot be official"),
        ("unknown_source_candidate", "blocked_until_review", "unknown source requires review"),
    ],
)
def test_mirror_provider_unknown_candidates_cannot_be_selected(source_type, source_status, rejection_reason):
    candidate = _entry(
        source_type=source_type,
        source_url="https://example.invalid/source",
        source_status=source_status,
        rejection_reason=rejection_reason,
        caveats=["not selectable"],
    )
    result = _result(candidates=[candidate], selected_official_source_id=candidate["source_id"])

    with pytest.raises(OfficialVerificationValidationError, match="cannot reference"):
        validate_official_disclosure_locator_result(result)


def test_selected_official_source_id_required_for_single_candidate_status():
    result = _result(selected_official_source_id="")

    with pytest.raises(OfficialVerificationValidationError, match="selected_official_source_id"):
        validate_official_disclosure_locator_result(result)


def test_blocked_or_rejected_status_requires_blocked_reason_or_caveat():
    result = _result(
        candidates=[],
        selected_official_source_id="",
        locator_status="blocked_until_review",
        blocked_reason="",
        caveats=[],
    )

    with pytest.raises(OfficialVerificationValidationError, match="blocked_reason|caveat"):
        validate_official_disclosure_locator_result(result)


def test_locator_result_cannot_include_metric_extraction_fields():
    result = _result(metric_id="revenue")

    with pytest.raises(OfficialVerificationValidationError, match="metric|report|write"):
        validate_official_disclosure_locator_result(result)


@pytest.mark.parametrize(
    "forbidden_marker",
    ["report v1 trigger", "accepted manifest write", "output baseline write", "provider live call", "read token"],
)
def test_locator_result_cannot_include_forbidden_intent_markers(forbidden_marker):
    result = _result(caveats=[forbidden_marker])

    with pytest.raises(OfficialVerificationValidationError, match="forbidden marker"):
        validate_official_disclosure_locator_result(result)
