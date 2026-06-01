# -*- coding: utf-8 -*-

import builtins
import socket
import urllib.request

from src.fundamental_skill.data_verification.official_disclosure_request import (
    ALLOWED_SOURCE_TYPES,
    REJECTION_ALLOWED_SOURCE_TYPES_EMPTY,
    REJECTION_ANNOUNCEMENT_TYPE_PERIOD_MISMATCH,
    REJECTION_AMBIGUOUS_QUERY_PERIOD,
    REJECTION_FORBIDDEN_DISCOVERY_SCOPE,
    REJECTION_FORBIDDEN_SOURCE_TYPE,
    REJECTION_MISSING_DISCOVERY_SCOPE,
    REJECTION_MISSING_QUERY_PERIOD,
    REJECTION_MISSING_REQUESTED_ANNOUNCEMENT_TYPE,
    REJECTION_MISSING_SECURITY_IDENTITY,
    REJECTION_NOT_FOR_TRADING_ADVICE_REQUIRED,
    REJECTION_Q4_QUERY_PERIOD_UNSUPPORTED,
    REJECTION_SECURITY_IDENTITY_CONFIDENCE_NOT_ALLOWED,
    REJECTION_SECURITY_IDENTITY_STATUS_NOT_VALID,
    REJECTION_SOURCE_PRIORITY_NOT_LIST,
    REJECTION_SOURCE_PRIORITY_NOT_ALLOWED,
    REJECTION_UNSUPPORTED_QUERY_PERIOD,
    REJECTION_UNSUPPORTED_REQUESTED_ANNOUNCEMENT_TYPE,
    build_official_disclosure_request_id,
    can_enter_discovery_candidate_generation,
    normalize_official_disclosure_request,
    validate_official_disclosure_request,
)
from src.fundamental_skill.data_verification.security_identity import (
    CONFIDENCE_LOW,
    STATUS_BLOCKED,
    STATUS_PARTIAL,
    normalize_security_identity,
)


def _identity_high():
    return normalize_security_identity("600406.SH")


def _identity_medium_with_caveat():
    return normalize_security_identity(
        {
            "stock_code": "600406",
            "company_name": "Guodian NARI",
            "not_for_trading_advice": True,
        }
    )


def _payload(**overrides):
    payload = {
        "security_identity": _identity_high(),
        "query_period": "2024",
        "not_for_trading_advice": True,
    }
    payload.update(overrides)
    return payload


def _request(**overrides):
    return normalize_official_disclosure_request(_payload(**overrides))


def test_valid_annual_report_request_from_high_confidence_identity():
    request = _request()

    assert request["schema_version"] == "official_disclosure_discovery_request.v1"
    assert request["request_id"].startswith("official_disclosure_request_")
    assert request["stock_code"] == "600406"
    assert request["exchange"] == "SSE"
    assert request["market"] == "CN_A"
    assert request["query_period"] == "2024FY"
    assert request["period_end_date"] == "2024-12-31"
    assert request["requested_announcement_type"] == "annual_report"
    assert request["allowed_source_types"] == list(ALLOWED_SOURCE_TYPES)
    assert request["source_priority"] == list(ALLOWED_SOURCE_TYPES)
    assert request["discovery_scope"] == "metadata_only"
    assert request["blocked_reasons"] == []
    assert request["rejection_reason"] is None
    assert request["not_for_trading_advice"] is True


def test_valid_annual_report_request_from_medium_confidence_identity_with_caveat():
    identity = _identity_medium_with_caveat()
    request = _request(security_identity=identity)

    assert request["rejection_reason"] is None
    assert request["company_name"] == "Guodian NARI"
    assert "company name supplied by user but not verified against stock code" in request[
        "caveats"
    ]
    assert "security identity derived from stock code and exchange only" in request[
        "caveats"
    ]


def test_valid_semiannual_report_request():
    request = _request(query_period="2024H1")

    assert request["query_period"] == "2024H1"
    assert request["period_end_date"] == "2024-06-30"
    assert request["requested_announcement_type"] == "semiannual_report"
    assert request["rejection_reason"] is None


def test_valid_quarterly_report_request():
    request = _request(query_period="2024Q3")

    assert request["query_period"] == "2024Q3"
    assert request["period_end_date"] == "2024-09-30"
    assert request["requested_announcement_type"] == "quarterly_report"
    assert request["rejection_reason"] is None


def test_q4_period_is_blocked_and_not_converted_to_annual_report():
    request = _request(query_period="2024Q4")

    assert request["rejection_reason"] == REJECTION_Q4_QUERY_PERIOD_UNSUPPORTED
    assert request["requested_announcement_type"] == ""


def test_missing_query_period_blocked():
    payload = _payload()
    del payload["query_period"]

    request = normalize_official_disclosure_request(payload)

    assert request["rejection_reason"] == REJECTION_MISSING_QUERY_PERIOD


def test_ambiguous_relative_query_period_blocked():
    request = _request(query_period="latest")

    assert request["rejection_reason"] == REJECTION_AMBIGUOUS_QUERY_PERIOD


def test_unsupported_query_period_blocked():
    request = _request(query_period="2024H2")

    assert request["rejection_reason"] == REJECTION_UNSUPPORTED_QUERY_PERIOD


def test_requested_announcement_type_must_match_query_period():
    request = _request(
        query_period="2024H1",
        requested_announcement_type="annual_report",
    )

    assert request["rejection_reason"] == REJECTION_ANNOUNCEMENT_TYPE_PERIOD_MISMATCH


def test_unsupported_announcement_type_blocked():
    request = _request(requested_announcement_type="correction")

    assert request["rejection_reason"] == REJECTION_UNSUPPORTED_REQUESTED_ANNOUNCEMENT_TYPE


def test_partial_identity_rejected():
    identity = _identity_high()
    identity["identity_status"] = STATUS_PARTIAL
    identity["identity_confidence"] = CONFIDENCE_LOW

    request = _request(security_identity=identity)

    assert REJECTION_SECURITY_IDENTITY_STATUS_NOT_VALID in request["blocked_reasons"]
    assert REJECTION_SECURITY_IDENTITY_CONFIDENCE_NOT_ALLOWED in request[
        "blocked_reasons"
    ]


def test_blocked_identity_rejected():
    identity = normalize_security_identity("600406.SZ")

    request = _request(security_identity=identity)

    assert identity["identity_status"] == STATUS_BLOCKED
    assert REJECTION_SECURITY_IDENTITY_STATUS_NOT_VALID in request["blocked_reasons"]


def test_company_name_only_blocked_identity_rejected():
    identity = normalize_security_identity(
        {"company_name": "Guodian NARI", "not_for_trading_advice": True}
    )

    request = _request(security_identity=identity)

    assert identity["identity_status"] == STATUS_BLOCKED
    assert REJECTION_SECURITY_IDENTITY_STATUS_NOT_VALID in request["blocked_reasons"]


def test_missing_security_identity_blocked():
    payload = _payload()
    del payload["security_identity"]

    request = normalize_official_disclosure_request(payload)

    assert request["rejection_reason"] == REJECTION_MISSING_SECURITY_IDENTITY


def test_allowed_source_types_with_provider_mirror_unknown_or_cache_rejected():
    for source_type in (
        "provider_source_candidate",
        "mirror_source_candidate",
        "unknown_source_candidate",
        "local_official_cache",
    ):
        request = _request(allowed_source_types=[source_type])

        assert REJECTION_FORBIDDEN_SOURCE_TYPE in request["blocked_reasons"]


def test_allowed_source_types_empty_rejected():
    request = _request(allowed_source_types=[])

    assert request["rejection_reason"] == REJECTION_ALLOWED_SOURCE_TYPES_EMPTY


def test_forbidden_discovery_scope_rejected():
    for scope in ("download", "parse_pdf", "metric_extraction"):
        request = _request(discovery_scope=scope)

        assert REJECTION_FORBIDDEN_DISCOVERY_SCOPE in request["blocked_reasons"]


def test_source_priority_with_provider_rejected():
    request = _request(source_priority=["provider_source_candidate"])

    assert REJECTION_FORBIDDEN_SOURCE_TYPE in request["blocked_reasons"]
    assert REJECTION_SOURCE_PRIORITY_NOT_ALLOWED in request["blocked_reasons"]


def test_validate_request_rejects_missing_derived_required_fields():
    request = _request()

    missing_type = dict(request)
    del missing_type["requested_announcement_type"]
    assert validate_official_disclosure_request(missing_type)["rejection_reason"] == (
        REJECTION_MISSING_REQUESTED_ANNOUNCEMENT_TYPE
    )

    missing_priority = dict(request)
    del missing_priority["source_priority"]
    assert validate_official_disclosure_request(missing_priority)["rejection_reason"] == (
        REJECTION_SOURCE_PRIORITY_NOT_LIST
    )

    missing_scope = dict(request)
    del missing_scope["discovery_scope"]
    assert validate_official_disclosure_request(missing_scope)["rejection_reason"] == (
        REJECTION_MISSING_DISCOVERY_SCOPE
    )


def test_deterministic_request_id():
    first = _request()
    second = _request(caveats=["caller caveat"])

    assert first["request_id"] == second["request_id"]
    assert build_official_disclosure_request_id(first) == first["request_id"]


def test_request_preserves_security_identity_caveats():
    identity = normalize_security_identity("600406")
    request = _request(security_identity=identity)

    for caveat in identity["caveats"]:
        assert caveat in request["caveats"]


def test_request_does_not_claim_company_name_verified():
    request = _request(company_name="Guodian NARI")

    assert request["company_name"] == "Guodian NARI"
    assert "company_name_verified" not in request
    assert all("verified match" not in caveat for caveat in request["caveats"])


def test_can_enter_discovery_candidate_generation_true_only_for_valid_request():
    valid_request = _request()
    blocked_request = _request(query_period="2024Q4")
    invalid_not_for_trading_advice = _request(not_for_trading_advice=False)
    forbidden_source = _request(allowed_source_types=["provider_source_candidate"])
    forbidden_scope = _request(discovery_scope="download")
    forbidden_marker = _request(caveats=["target price"])

    assert can_enter_discovery_candidate_generation(valid_request) is True
    assert can_enter_discovery_candidate_generation(valid_request, with_reason=True) == (
        True,
        None,
    )
    assert can_enter_discovery_candidate_generation(blocked_request) is False
    assert can_enter_discovery_candidate_generation(invalid_not_for_trading_advice) is False
    assert (
        invalid_not_for_trading_advice["rejection_reason"]
        == REJECTION_NOT_FOR_TRADING_ADVICE_REQUIRED
    )
    assert can_enter_discovery_candidate_generation(forbidden_source) is False
    assert can_enter_discovery_candidate_generation(forbidden_scope) is False
    assert can_enter_discovery_candidate_generation(forbidden_marker) is False


def test_no_io_no_network_no_file_read_behavior_introduced(monkeypatch):
    def fail_io(*args, **kwargs):
        raise AssertionError("unexpected IO")

    monkeypatch.setattr(builtins, "open", fail_io)
    monkeypatch.setattr(socket, "create_connection", fail_io)
    monkeypatch.setattr(urllib.request, "urlopen", fail_io)

    request = _request()

    assert request["rejection_reason"] is None
