# -*- coding: utf-8 -*-

import builtins
import copy
import socket
import urllib.request

from src.fundamental_skill.data_verification.official_disclosure_request import (
    normalize_official_disclosure_request,
)
from src.fundamental_skill.data_verification.request_synthetic_dry_run_integration import (
    REQUEST_SYNTHETIC_DRY_RUN_RESULT_SCHEMA_VERSION,
    build_request_synthetic_dry_run_integration_result,
    can_enter_request_synthetic_dry_run,
    check_candidate_request_compatibility,
    filter_candidates_by_request,
    validate_request_synthetic_dry_run_integration_result,
)
from src.fundamental_skill.data_verification.security_identity import (
    normalize_security_identity,
)
from src.fundamental_skill.data_verification.validators import (
    OfficialVerificationValidationError,
)


def _request(**overrides):
    payload = {
        "security_identity": normalize_security_identity("600406.SH"),
        "company_name": "Guodian NARI",
        "query_period": "2024",
        "not_for_trading_advice": True,
    }
    payload.update(overrides)
    return normalize_official_disclosure_request(payload)


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


def _build(candidates, request=None, **overrides):
    payload = {
        "request": _request() if request is None else request,
        "input_synthetic_candidates": candidates,
    }
    payload.update(overrides)
    return build_request_synthetic_dry_run_integration_result(**payload)


def _contains_key(payload, key):
    if isinstance(payload, dict):
        if key in payload:
            return True
        return any(_contains_key(value, key) for value in payload.values())
    if isinstance(payload, list):
        return any(_contains_key(value, key) for value in payload)
    return False


def test_valid_request_with_compatible_single_cninfo_candidate():
    result = _build([_candidate()])

    assert result["schema_version"] == REQUEST_SYNTHETIC_DRY_RUN_RESULT_SCHEMA_VERSION
    assert result["not_for_trading_advice"] is True
    assert len(result["request_compatible_candidates"]) == 1
    assert result["request_compatible_candidates"][0]["source_domain"] == (
        "static.cninfo.com.cn"
    )
    assert result["request_rejected_candidates"] == []
    assert result["synthetic_dry_run_result"]["locator_result"]["locator_status"] == (
        "found_single_official_candidate"
    )
    assert result["merged_blocked_reasons"] == []
    assert result["merged_data_gap_plan"] == []
    assert can_enter_request_synthetic_dry_run(result) is True


def test_valid_request_with_compatible_sse_exchange_candidate():
    result = _build(
        [
            _candidate(
                source_type="sse_exchange_announcement",
                source_url="https://www.sse.com.cn/disclosure/listedinfo/announcement/c/official.pdf",
                discovery_method="sse_announcement_list",
            )
        ],
        request=_request(allowed_source_types=["sse_exchange_announcement"]),
    )

    assert result["request_compatible_candidates"][0]["source_type"] == (
        "sse_exchange_announcement"
    )
    assert result["synthetic_dry_run_result"]["registry_entry_candidates"][0][
        "source_type"
    ] == "sse_exchange_announcement"


def test_request_blocked_does_not_enter_dry_run():
    result = _build([_candidate()], request=_request(query_period="2024Q4"))

    assert result["synthetic_dry_run_result"] is None
    assert result["request_compatible_candidates"] == []
    assert result["request_rejected_candidates"] == []
    assert any(reason.startswith("request:") for reason in result["merged_blocked_reasons"])
    assert result["merged_data_gap_plan"]


def test_missing_and_invalid_request_blocked():
    missing = build_request_synthetic_dry_run_integration_result(
        input_synthetic_candidates=[_candidate()]
    )
    invalid = build_request_synthetic_dry_run_integration_result(
        request="not a request",
        input_synthetic_candidates=[_candidate()],
    )

    assert "request:missing_request" in missing["merged_blocked_reasons"]
    assert missing["synthetic_dry_run_result"] is None
    assert invalid["synthetic_dry_run_result"] is None
    assert any(reason.startswith("request:") for reason in invalid["merged_blocked_reasons"])


def test_missing_non_list_and_empty_candidates_blocked():
    request = _request()

    missing = build_request_synthetic_dry_run_integration_result(request=request)
    non_list = _build("not a list", request=request)
    empty = _build([], request=request)

    assert "request_candidate:missing_candidates" in missing["merged_blocked_reasons"]
    assert "request_candidate:candidates_not_list" in non_list["merged_blocked_reasons"]
    assert "request_candidate:no_synthetic_candidates" in empty["merged_blocked_reasons"]
    assert missing["merged_data_gap_plan"]
    assert non_list["merged_data_gap_plan"]
    assert empty["merged_data_gap_plan"]


def test_all_candidates_incompatible_blocked():
    result = _build([_candidate(stock_code="600000")])

    assert result["request_compatible_candidates"] == []
    assert result["request_rejected_candidates"][0]["rejection_reason"] == (
        "stock_code_mismatch"
    )
    assert "request_candidate:all_synthetic_candidates_incompatible" in result[
        "merged_blocked_reasons"
    ]


def test_mixed_compatible_and_incompatible_candidates_fail_closed():
    result = _build([_candidate(), _candidate(exchange="SZSE")])

    assert len(result["request_compatible_candidates"]) == 1
    assert len(result["request_rejected_candidates"]) == 1
    assert result["synthetic_dry_run_result"] is not None
    assert "request_candidate:mixed_compatible_and_incompatible_candidates" in result[
        "merged_blocked_reasons"
    ]
    assert can_enter_request_synthetic_dry_run(result, with_reason=True)[0] is False


def test_field_mismatches_are_machine_readable():
    request = _request()

    cninfo_only_request = _request(allowed_source_types=["cninfo_official_pdf"])
    cases = [
        (request, _candidate(stock_code="600000"), "stock_code_mismatch"),
        (request, _candidate(exchange="SZSE"), "exchange_mismatch"),
        (request, _candidate(period_key="2023FY"), "period_mismatch"),
        (request, _candidate(period_end_date="2023-12-31"), "period_mismatch"),
        (
            request,
            _candidate(announcement_type="semiannual_report"),
            "announcement_type_mismatch",
        ),
        (
            cninfo_only_request,
            _candidate(source_type="exchange_official_pdf"),
            "source_type_not_allowed",
        ),
    ]

    for case_request, candidate, reason in cases:
        assert reason in check_candidate_request_compatibility(case_request, candidate)


def test_forbidden_source_kinds_rejected_before_normalizer_or_dry_run():
    for source_type in (
        "provider_source_candidate",
        "mirror_source_candidate",
        "unknown_source_candidate",
        "local_official_cache",
    ):
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

        assert result["synthetic_dry_run_result"] is None
        assert "forbidden_source_kind" in result["request_rejected_candidates"][0][
            "rejection_reasons"
        ]


def test_forbidden_scope_intent_rejected():
    result = _build([_candidate(raw_candidate_metadata={"parse_pdf": True})])

    assert result["request_compatible_candidates"] == []
    assert "forbidden_scope_intent" in result["request_rejected_candidates"][0][
        "rejection_reasons"
    ]


def test_multiple_official_candidates_and_source_conflict_review_required():
    multiple = _build(
        [
            _candidate(),
            _candidate(
                source_type="sse_exchange_announcement",
                source_url="https://www.sse.com.cn/disclosure/listedinfo/announcement/c/official.pdf",
                discovery_method="sse_announcement_list",
            ),
        ]
    )
    conflict = _build(
        [
            _candidate(source_title="600406 2024 annual report"),
            _candidate(source_title="600406 corrected annual report"),
        ]
    )

    assert "dry_run:locator:multiple_official_candidates_review_required" in multiple[
        "merged_blocked_reasons"
    ]
    assert "select_one_official_source_candidate_by_review" in multiple[
        "merged_data_gap_plan"
    ]
    assert "dry_run:locator:source_conflict_review_required" in conflict[
        "merged_blocked_reasons"
    ]


def test_request_caveats_preserved_and_company_hint_not_verified():
    request = _request(caveats=["caller caveat"])
    result = _build([_candidate()], request=request)

    assert "caller caveat" in result["request_caveats"]
    assert "caller caveat" in result["final_caveats"]
    assert "company_name_verified" not in result["security_identity"]
    assert result["request"]["company_name"] == "Guodian NARI"
    assert "company name supplied in request but not verified against stock code" in result[
        "request_caveats"
    ]


def test_candidate_cannot_raise_identity_confidence_or_verified_company_match():
    confidence = _build(
        [
            _candidate(
                normalized_candidate_metadata={"identity_confidence": "high"},
            )
        ]
    )
    company_match = _build(
        [
            _candidate(
                normalized_candidate_metadata={"verified_company_match": True},
            )
        ]
    )

    assert "identity_confidence_promotion_forbidden" in confidence[
        "request_rejected_candidates"
    ][0]["rejection_reasons"]
    assert "company_match_promotion_forbidden" in company_match[
        "request_rejected_candidates"
    ][0]["rejection_reasons"]


def test_filter_candidates_by_request_returns_compatible_and_rejected():
    compatible, rejected = filter_candidates_by_request(
        _request(),
        [_candidate(), _candidate(stock_code="600000")],
    )

    assert len(compatible) == 1
    assert len(rejected) == 1
    assert rejected[0]["rejection_reason"] == "stock_code_mismatch"


def test_final_result_cannot_contain_metric_fact_conflict_or_report_intent():
    result = _build([_candidate()])

    for forbidden_key in (
        "official_metric_fact",
        "provider_official_conflict",
        "report_v1",
        "accepted_manifest_write",
    ):
        unsafe = copy.deepcopy(result)
        unsafe["synthetic_dry_run_result"][forbidden_key] = {
            "not_for_trading_advice": True
        }
        try:
            validate_request_synthetic_dry_run_integration_result(unsafe)
        except OfficialVerificationValidationError as exc:
            assert "forbidden" in str(exc)
        else:
            raise AssertionError(f"{forbidden_key} should be rejected")

    assert not _contains_key(result, "official_metric_fact")
    assert not _contains_key(result, "provider_official_conflict")


def test_validator_requires_merged_blocked_context_for_nested_dry_run_blockers():
    result = _build([_candidate(), _candidate(exchange="SZSE")])
    unsafe = copy.deepcopy(result)
    unsafe["merged_blocked_reasons"] = []
    unsafe["merged_data_gap_plan"] = []

    try:
        validate_request_synthetic_dry_run_integration_result(unsafe)
    except OfficialVerificationValidationError as exc:
        assert "merged_blocked_reasons_missing" in str(exc)
    else:
        raise AssertionError("merged blocked context should be required")


def test_no_io_no_network_no_url_fetch_or_file_read(monkeypatch):
    def fail_io(*args, **kwargs):
        raise AssertionError("unexpected IO")

    monkeypatch.setattr(builtins, "open", fail_io)
    monkeypatch.setattr(socket, "socket", fail_io)
    monkeypatch.setattr(urllib.request, "urlopen", fail_io)

    result = _build([_candidate()])

    assert result["synthetic_dry_run_result"]["locator_result"]["locator_status"] == (
        "found_single_official_candidate"
    )
