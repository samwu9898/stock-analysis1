# -*- coding: utf-8 -*-

import builtins
import socket

import pytest

from src.fundamental_skill.data_verification.official_disclosure_discovery_candidate import (
    build_discovery_candidate_id,
    build_discovery_rejection_reason,
    can_handoff_to_registry,
    derive_source_domain_from_url,
    is_discovery_only_source_type,
    is_official_discovery_source_type,
    is_provider_discovery_source_type,
    normalize_official_disclosure_discovery_candidate,
    validate_official_disclosure_discovery_candidate,
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


def test_valid_cninfo_discovery_candidate_normalization():
    normalized = normalize_official_disclosure_discovery_candidate(
        _candidate(stock_code=" 600406 ", company_name=" Guodian NARI ")
    )

    assert normalized["stock_code"] == "600406"
    assert normalized["company_name"] == "Guodian NARI"
    assert normalized["source_domain"] == "static.cninfo.com.cn"
    assert normalized["schema_version"] == "official_disclosure_discovery_candidate.v1"
    assert normalized["discovery_candidate_id"].startswith("discovery_candidate_")
    assert can_handoff_to_registry(normalized) is True
    assert can_handoff_to_registry(normalized, with_reason=True) == (True, "")


def test_valid_sse_exchange_discovery_candidate_normalization():
    normalized = normalize_official_disclosure_discovery_candidate(
        _candidate(
            source_type="sse_exchange_announcement",
            source_url="https://www.sse.com.cn/disclosure/listedinfo/announcement/c/official.pdf",
            discovery_method="sse_announcement_list",
            source_domain="",
        )
    )

    assert normalized["source_domain"] == "www.sse.com.cn"
    assert is_official_discovery_source_type(normalized["source_type"]) is True
    assert can_handoff_to_registry(normalized) is True


def test_sse_exchange_official_announcement_alias_normalizes_to_official_source_type():
    normalized = normalize_official_disclosure_discovery_candidate(
        _candidate(
            source_type="sse_exchange_official_announcement",
            source_url="https://www.sse.com.cn/disclosure/listedinfo/announcement/c/official.pdf",
            discovery_method="sse_announcement_list",
            source_domain="",
        )
    )

    assert normalized["source_type"] == "sse_exchange_announcement"
    assert can_handoff_to_registry(normalized) is True


def test_valid_exchange_official_pdf_discovery_candidate_normalization():
    normalized = normalize_official_disclosure_discovery_candidate(
        _candidate(
            source_type="exchange_official_pdf",
            source_url="https://disc.static.szse.cn/download/disc/official.pdf",
            discovery_method="exchange_announcement_list",
            source_domain="",
        )
    )

    assert normalized["source_domain"] == "disc.static.szse.cn"
    assert can_handoff_to_registry(normalized) is True


def test_mirror_candidate_remains_discovery_only_and_cannot_become_official():
    normalized = normalize_official_disclosure_discovery_candidate(
        _candidate(
            source_type="mirror_source_candidate",
            source_url="",
            source_title="",
            disclosure_date="",
            source_domain="",
        )
    )

    assert is_discovery_only_source_type(normalized["source_type"]) is True
    assert normalized["rejection_reason"] == "mirror_source_not_official"
    assert can_handoff_to_registry(normalized) is False
    assert can_handoff_to_registry(normalized, with_reason=True) == (False, "mirror_source_not_official")


def test_provider_candidate_rejected_from_official_lane():
    normalized = normalize_official_disclosure_discovery_candidate(
        _candidate(
            source_type="provider_source_candidate",
            source_url="",
            source_title="",
            disclosure_date="",
            source_domain="",
        )
    )

    assert is_provider_discovery_source_type(normalized["source_type"]) is True
    assert normalized["rejection_reason"] == "provider_source_not_official"
    assert can_handoff_to_registry(normalized) is False


def test_unknown_source_value_blocked():
    with pytest.raises(OfficialVerificationValidationError, match="source_type"):
        normalize_official_disclosure_discovery_candidate(_candidate(source_type="random_source"))


def test_unknown_source_candidate_blocked_from_handoff():
    normalized = normalize_official_disclosure_discovery_candidate(
        _candidate(
            source_type="unknown_source_candidate",
            source_url="",
            source_title="",
            disclosure_date="",
            source_domain="",
        )
    )

    assert normalized["rejection_reason"] == "unknown_source_type"
    assert can_handoff_to_registry(normalized) is False


@pytest.mark.parametrize(
    "field",
    [
        "stock_code",
        "company_name",
        "exchange",
        "period_key",
        "period_end_date",
        "announcement_type",
        "discovered_at_utc",
        "discovery_method",
    ],
)
def test_missing_core_metadata_blocked(field):
    with pytest.raises(OfficialVerificationValidationError, match=field):
        normalize_official_disclosure_discovery_candidate(_candidate(**{field: ""}))


@pytest.mark.parametrize("field", ["source_url", "source_title", "disclosure_date"])
def test_missing_official_source_metadata_blocked(field):
    with pytest.raises(OfficialVerificationValidationError, match=field):
        normalize_official_disclosure_discovery_candidate(_candidate(**{field: ""}))


def test_missing_source_domain_blocked_when_url_exists():
    normalized = normalize_official_disclosure_discovery_candidate(_candidate())
    del normalized["source_domain"]

    with pytest.raises(OfficialVerificationValidationError, match="source_domain"):
        validate_official_disclosure_discovery_candidate(normalized)


def test_rejection_reason_invalid_source_domain_for_untrusted_domain():
    reason = build_discovery_rejection_reason(
        _candidate(source_url="https://evil.com/fake.pdf", source_domain="evil.com")
    )

    assert reason == "invalid_source_domain"


@pytest.mark.parametrize("source_url", ["https://", "file:///tmp/fake.pdf"])
def test_rejection_reason_invalid_source_domain_for_url_without_official_host(source_url):
    reason = build_discovery_rejection_reason(_candidate(source_url=source_url, source_domain="cninfo.com.cn"))

    assert reason == "invalid_source_domain"


def test_untrusted_domain_still_fails_closed_during_normalization():
    with pytest.raises(OfficialVerificationValidationError, match="domain"):
        normalize_official_disclosure_discovery_candidate(
            _candidate(source_url="https://evil.com/fake.pdf", source_domain="evil.com")
        )


def test_file_url_cannot_pass_official_discovery_candidate():
    with pytest.raises(OfficialVerificationValidationError, match="hostname"):
        normalize_official_disclosure_discovery_candidate(
            _candidate(source_url="file:///tmp/fake.pdf", source_domain="cninfo.com.cn")
        )


def test_local_cache_intent_is_inert_and_cannot_handoff():
    normalized = normalize_official_disclosure_discovery_candidate(
        _candidate(
            source_type="local_official_cache",
            source_url="",
            source_title="",
            disclosure_date="",
            source_domain="",
            raw_candidate_metadata={"local_cache_path": "local/official/600406_2024.pdf"},
        )
    )

    assert normalized["rejection_reason"] == "local_cache_inert"
    assert can_handoff_to_registry(normalized) is False


def test_normalized_candidate_can_only_handoff_explicitly_to_registry_locator():
    normalized = normalize_official_disclosure_discovery_candidate(_candidate())

    assert "official_metric_fact" not in normalized
    assert "provider_official_conflict" not in normalized
    assert "accepted_manifest" not in normalized
    assert can_handoff_to_registry(normalized) is True


def test_no_io_no_network_no_file_read_behavior_is_introduced(monkeypatch):
    def fail_io(*args, **kwargs):
        raise AssertionError("unexpected IO")

    monkeypatch.setattr(builtins, "open", fail_io)
    monkeypatch.setattr(socket, "socket", fail_io)

    normalized = normalize_official_disclosure_discovery_candidate(_candidate())

    assert normalized["source_domain"] == "static.cninfo.com.cn"


def test_deterministic_candidate_id_derived_from_explicit_metadata_only():
    first = normalize_official_disclosure_discovery_candidate(_candidate())
    second = normalize_official_disclosure_discovery_candidate(_candidate(raw_candidate_metadata={"ignored": "metadata"}))

    assert first["discovery_candidate_id"] == second["discovery_candidate_id"]
    assert build_discovery_candidate_id(first) == first["discovery_candidate_id"]


def test_derive_source_domain_from_url_is_pure_string_parsing():
    assert derive_source_domain_from_url("https://static.cninfo.com.cn/finalpage/file.pdf") == "static.cninfo.com.cn"
    assert derive_source_domain_from_url("file:///tmp/file.pdf") == ""
