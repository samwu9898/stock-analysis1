# -*- coding: utf-8 -*-

import builtins
import socket
import urllib.request

import pytest

import src.fundamental_skill.data_verification.official_source_discovery_adapter as adapter
from src.fundamental_skill.data_verification.official_disclosure_request import (
    normalize_official_disclosure_request,
)
from src.fundamental_skill.data_verification.official_source_discovery_adapter import (
    REASON_ALL_RECORDS_REJECTED,
    REASON_AMBIGUOUS_DUPLICATE_REVIEW_REQUIRED,
    REASON_FORBIDDEN_SOURCE_TYPE,
    REASON_MALFORMED_URL,
    REASON_MULTIPLE_CANDIDATES_REVIEW_REQUIRED,
    REASON_NO_CANDIDATES_FOUND,
    REASON_NON_ALLOWLIST_DOMAIN,
    REASON_REDIRECT_DOMAIN_NOT_ALLOWED,
    REASON_SOURCE_TYPE_NOT_ALLOWED_BY_REQUEST,
    REASON_SOURCE_DOMAIN_MISMATCH,
    REASON_STOCK_CODE_MISMATCH,
    discover_official_sources_from_metadata,
    validate_official_source_discovery_adapter_result,
)
from src.fundamental_skill.data_verification.validators import OfficialVerificationValidationError
from src.fundamental_skill.data_verification.security_identity import normalize_security_identity


def _request(**overrides):
    payload = {
        "security_identity": normalize_security_identity(
            {
                "stock_code": "600406",
                "company_name": "Guodian NARI",
                "not_for_trading_advice": True,
            }
        ),
        "query_period": "2024",
        "not_for_trading_advice": True,
    }
    payload.update(overrides)
    return normalize_official_disclosure_request(payload)


def _record(**overrides):
    record = {
        "source_url": "https://static.cninfo.com.cn/finalpage/2025-04-30/official.pdf",
        "source_title": "600406 2024 annual report",
        "disclosure_date": "2025-04-30",
        "stock_code": "600406",
        "company_name": "Guodian NARI",
        "exchange": "SSE",
        "period_key": "2024FY",
        "period_end_date": "2024-12-31",
        "announcement_type": "annual_report",
        "source_type": "cninfo_official_pdf",
        "source_domain": "static.cninfo.com.cn",
        "discovered_at_utc": "2026-06-01T00:00:00Z",
        "discovery_method": "cninfo_search_result",
        "not_for_trading_advice": True,
    }
    record.update(overrides)
    return record


def test_valid_cninfo_metadata_result_to_discovery_candidate():
    result = discover_official_sources_from_metadata(_request(), [_record()])

    assert result["schema_version"] == "official_source_discovery_adapter_result.v1"
    assert result["blocked_reasons"] == []
    assert result["rejected_records"] == []
    assert len(result["discovery_candidates"]) == 1
    candidate = result["discovery_candidates"][0]
    assert candidate["schema_version"] == "official_disclosure_discovery_candidate.v1"
    assert candidate["source_type"] == "cninfo_official_pdf"
    assert candidate["source_domain"] == "static.cninfo.com.cn"
    assert candidate["not_for_trading_advice"] is True


def test_valid_sse_metadata_result_to_discovery_candidate():
    result = discover_official_sources_from_metadata(
        _request(),
        [
            _record(
                source_type="sse_exchange_announcement",
                source_url="https://www.sse.com.cn/disclosure/listedinfo/announcement/c/official.pdf",
                source_domain="www.sse.com.cn",
                discovery_method="sse_announcement_list",
            )
        ],
    )

    candidate = result["discovery_candidates"][0]
    assert result["blocked_reasons"] == []
    assert candidate["source_type"] == "sse_exchange_announcement"
    assert candidate["source_domain"] == "www.sse.com.cn"


def test_valid_exchange_metadata_result_to_discovery_candidate():
    result = discover_official_sources_from_metadata(
        _request(),
        [
            _record(
                source_type="exchange_official_pdf",
                source_url="https://www.szse.cn/disclosure/official.pdf",
                source_domain="www.szse.cn",
                discovery_method="exchange_announcement_list",
            )
        ],
    )

    candidate = result["discovery_candidates"][0]
    assert result["blocked_reasons"] == []
    assert candidate["source_type"] == "exchange_official_pdf"
    assert candidate["source_domain"] == "www.szse.cn"


def test_non_allowlist_domain_rejected():
    result = discover_official_sources_from_metadata(
        _request(),
        [_record(source_url="https://evil.example/fake.pdf", source_domain="evil.example")],
    )

    assert result["discovery_candidates"] == []
    assert REASON_NON_ALLOWLIST_DOMAIN in result["rejected_records"][0]["reasons"]
    assert REASON_ALL_RECORDS_REJECTED in result["blocked_reasons"]


@pytest.mark.parametrize("source_url", ["https://", "file:///tmp/fake.pdf"])
def test_malformed_url_rejected(source_url):
    result = discover_official_sources_from_metadata(
        _request(),
        [_record(source_url=source_url, source_domain="static.cninfo.com.cn")],
    )

    assert REASON_MALFORMED_URL in result["rejected_records"][0]["reasons"]


def test_url_allowlist_string_in_path_or_query_does_not_spoof_host():
    result = discover_official_sources_from_metadata(
        _request(),
        [
            _record(
                source_url="https://evil.example/path/static.cninfo.com.cn/file.pdf?next=www.sse.com.cn",
                source_domain="evil.example",
            )
        ],
    )

    assert result["discovery_candidates"] == []
    assert REASON_NON_ALLOWLIST_DOMAIN in result["rejected_records"][0]["reasons"]


def test_userinfo_url_rejected():
    result = discover_official_sources_from_metadata(
        _request(),
        [_record(source_url="https://user@static.cninfo.com.cn/finalpage/official.pdf")],
    )

    assert REASON_MALFORMED_URL in result["rejected_records"][0]["reasons"]


def test_redirect_chain_to_non_allowlist_domain_rejected():
    result = discover_official_sources_from_metadata(
        _request(),
        [
            _record(
                redirect_chain=[
                    "https://static.cninfo.com.cn/finalpage/official.pdf",
                    "https://evil.example/final.pdf",
                ]
            )
        ],
    )

    assert REASON_REDIRECT_DOMAIN_NOT_ALLOWED in result["rejected_records"][0]["reasons"]


@pytest.mark.parametrize(
    "source_type",
    [
        "provider_source_candidate",
        "mirror_source_candidate",
        "unknown_source_candidate",
        "local_official_cache",
    ],
)
def test_provider_mirror_unknown_and_local_cache_source_rejected(source_type):
    result = discover_official_sources_from_metadata(_request(), [_record(source_type=source_type)])

    assert result["discovery_candidates"] == []
    assert REASON_FORBIDDEN_SOURCE_TYPE in result["rejected_records"][0]["reasons"]


def test_request_mismatch_rejected():
    result = discover_official_sources_from_metadata(_request(), [_record(stock_code="600000")])

    assert REASON_STOCK_CODE_MISMATCH in result["rejected_records"][0]["reasons"]


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("exchange", "SZSE", "exchange_mismatch"),
        ("period_key", "2024H1", "period_key_mismatch"),
        ("period_end_date", "2024-06-30", "period_end_date_mismatch"),
        ("announcement_type", "semiannual_report", "announcement_type_mismatch"),
    ],
)
def test_request_match_fields_rejected(field, value, reason):
    result = discover_official_sources_from_metadata(_request(), [_record(**{field: value})])

    assert reason in result["rejected_records"][0]["reasons"]


def test_source_type_outside_request_allowed_source_types_rejected():
    request = _request(allowed_source_types=["sse_exchange_announcement"])
    result = discover_official_sources_from_metadata(request, [_record()])

    assert REASON_SOURCE_TYPE_NOT_ALLOWED_BY_REQUEST in result["rejected_records"][0]["reasons"]


@pytest.mark.parametrize(
    "field",
    ["source_title", "disclosure_date", "source_url", "discovered_at_utc"],
)
def test_missing_required_metadata_blocked(field):
    result = discover_official_sources_from_metadata(_request(), [_record(**{field: ""})])

    assert result["discovery_candidates"] == []
    assert REASON_NO_CANDIDATES_FOUND in result["blocked_reasons"]
    assert result["rejected_records"][0]["reasons"]


def test_url_host_and_source_domain_mismatch_rejected():
    result = discover_official_sources_from_metadata(
        _request(),
        [_record(source_domain="cninfo.com.cn")],
    )

    assert REASON_SOURCE_DOMAIN_MISMATCH in result["rejected_records"][0]["reasons"]


def test_duplicate_exact_candidates_deduped():
    result = discover_official_sources_from_metadata(_request(), [_record(), _record()])

    assert len(result["discovery_candidates"]) == 1
    assert result["blocked_reasons"] == []
    assert "duplicate exact metadata candidate deduped" in result["caveats"]


def test_same_url_different_metadata_review_required():
    result = discover_official_sources_from_metadata(
        _request(),
        [_record(), _record(source_title="600406 2024 annual report corrected title")],
    )

    assert len(result["discovery_candidates"]) == 2
    assert REASON_AMBIGUOUS_DUPLICATE_REVIEW_REQUIRED in result["blocked_reasons"]
    assert REASON_MULTIPLE_CANDIDATES_REVIEW_REQUIRED in result["blocked_reasons"]


def test_no_metadata_records_blocked():
    result = discover_official_sources_from_metadata(_request(), [])

    assert result["discovery_candidates"] == []
    assert "no_metadata_records" in result["blocked_reasons"]
    assert REASON_NO_CANDIDATES_FOUND in result["blocked_reasons"]


def test_missing_metadata_records_blocked():
    result = discover_official_sources_from_metadata(_request(), None)

    assert result["discovery_candidates"] == []
    assert "metadata_records_missing" in result["blocked_reasons"]


def test_non_list_metadata_records_blocked():
    result = discover_official_sources_from_metadata(_request(), {"records": [_record()]})

    assert result["discovery_candidates"] == []
    assert "metadata_records_not_list" in result["blocked_reasons"]


def test_all_records_rejected_blocked():
    result = discover_official_sources_from_metadata(
        _request(),
        [_record(source_url="https://evil.example/fake.pdf", source_domain="evil.example")],
    )

    assert result["discovery_candidates"] == []
    assert REASON_ALL_RECORDS_REJECTED in result["blocked_reasons"]


def test_multiple_plausible_candidates_review_required():
    result = discover_official_sources_from_metadata(
        _request(),
        [
            _record(source_url="https://static.cninfo.com.cn/finalpage/2025-04-30/official-a.pdf"),
            _record(source_url="https://cninfo.com.cn/finalpage/2025-04-30/official-b.pdf", source_domain="cninfo.com.cn"),
        ],
    )

    assert len(result["discovery_candidates"]) == 2
    assert REASON_MULTIPLE_CANDIDATES_REVIEW_REQUIRED in result["blocked_reasons"]


def test_request_caveats_preserved_and_identity_confidence_not_raised():
    request = _request()
    result = discover_official_sources_from_metadata(request, [_record()])

    assert result["request"]["security_identity"]["identity_confidence"] == request["security_identity"]["identity_confidence"]
    assert set(request["caveats"]).issubset(set(result["caveats"]))
    assert "identity_confidence" not in result["discovery_candidates"][0]


def test_company_hint_not_verified():
    result = discover_official_sources_from_metadata(_request(), [_record()])
    candidate = result["discovery_candidates"][0]

    assert candidate["normalized_candidate_metadata"]["company_hint_verified"] is False
    assert "metadata-only candidate; company hint is not verified" in candidate["caveats"]


def test_discovery_candidate_validator_is_used(monkeypatch):
    calls = {"count": 0}
    original = adapter.validate_official_disclosure_discovery_candidate

    def counting_validator(candidate):
        calls["count"] += 1
        return original(candidate)

    monkeypatch.setattr(adapter, "validate_official_disclosure_discovery_candidate", counting_validator)

    result = discover_official_sources_from_metadata(_request(), [_record()])

    assert result["discovery_candidates"]
    assert calls["count"] >= 1


def test_no_registry_locator_verified_fact_or_metric_generated():
    result = discover_official_sources_from_metadata(_request(), [_record()])
    candidate = result["discovery_candidates"][0]

    for forbidden_key in (
        "registry_entry",
        "locator_result",
        "verified_fact",
        "official_metric_fact",
        "provider_official_conflict",
        "accepted_manifest",
        "output_baseline",
    ):
        assert forbidden_key not in result
        assert forbidden_key not in candidate


def test_result_validator_rejects_forbidden_marker_in_metadata_snapshot():
    result = {
        "schema_version": "official_source_discovery_adapter_result.v1",
        "request": {},
        "input_metadata_records": [{"source_title": "target price"}],
        "discovery_candidates": [],
        "rejected_records": [],
        "blocked_reasons": ["review_required"],
        "caveats": [],
        "not_for_trading_advice": True,
    }

    with pytest.raises(OfficialVerificationValidationError, match="forbidden"):
        validate_official_source_discovery_adapter_result(result)


def test_result_validator_rejects_forbidden_marker_in_rejected_record_snapshot():
    result = {
        "schema_version": "official_source_discovery_adapter_result.v1",
        "request": {},
        "input_metadata_records": [],
        "discovery_candidates": [],
        "rejected_records": [
            {
                "record": {"source_title": "provider live"},
                "reasons": ["forbidden_marker_detected"],
                "not_for_trading_advice": True,
            }
        ],
        "blocked_reasons": ["all_records_rejected"],
        "caveats": [],
        "not_for_trading_advice": True,
    }

    with pytest.raises(OfficialVerificationValidationError, match="forbidden"):
        validate_official_source_discovery_adapter_result(result)


def test_no_io_no_network_no_url_fetch_or_file_read(monkeypatch):
    def fail_io(*args, **kwargs):
        raise AssertionError("unexpected IO")

    monkeypatch.setattr(builtins, "open", fail_io)
    monkeypatch.setattr(socket, "socket", fail_io)
    monkeypatch.setattr(urllib.request, "urlopen", fail_io)

    result = discover_official_sources_from_metadata(_request(), [_record()])

    assert result["blocked_reasons"] == []
    assert result["discovery_candidates"][0]["source_domain"] == "static.cninfo.com.cn"
