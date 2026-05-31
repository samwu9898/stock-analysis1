# -*- coding: utf-8 -*-

import pytest

from src.fundamental_skill.data_verification.source_registry import (
    assert_source_eligible_for_verified_use,
    can_source_be_accepted_as_official,
    validate_source_refresh_policy,
)
from src.fundamental_skill.data_verification.validators import (
    OfficialVerificationValidationError,
    validate_official_source_candidate,
)


SHA = "b" * 64


def _candidate(**overrides):
    candidate = {
        "source_candidate_id": "src_600406_2024fy",
        "stock_code": "600406",
        "period": "2024FY",
        "announcement_type": "annual_report",
        "candidate_source_type": "cninfo_official_pdf",
        "candidate_url": "https://example.invalid/official.pdf",
        "candidate_title": "600406 2024 annual report",
        "disclosure_date": "2025-04-30",
        "source_discovery_method": "manual_registry_entry",
        "is_official_candidate": True,
        "is_mirror": False,
        "accepted_as_official": True,
        "rejection_reason": "",
        "file_sha256": SHA,
        "local_cache_path": "local/official/600406_2024.pdf",
        "source_refresh_policy": "explicit_registry_refresh_only",
        "registry_version": "official_registry.v1",
        "not_for_trading_advice": True,
    }
    candidate.update(overrides)
    return candidate


def test_mirror_source_cannot_be_accepted_as_official():
    candidate = _candidate(
        candidate_source_type="mirror_third_party_page",
        is_mirror=True,
        accepted_as_official=True,
    )

    with pytest.raises(OfficialVerificationValidationError, match="mirror"):
        validate_official_source_candidate(candidate)


def test_official_source_missing_file_sha256_rejected_for_verified_use():
    candidate = _candidate(file_sha256="")

    with pytest.raises(OfficialVerificationValidationError, match="missing fields|sha256"):
        assert_source_eligible_for_verified_use(candidate)


def test_source_refresh_policy_required():
    candidate = _candidate(source_refresh_policy="")

    with pytest.raises(OfficialVerificationValidationError, match="source_refresh_policy"):
        validate_source_refresh_policy(candidate)


def test_registry_version_required():
    candidate = _candidate(registry_version="")

    with pytest.raises(OfficialVerificationValidationError, match="registry_version"):
        validate_source_refresh_policy(candidate)


def test_provider_endpoint_cannot_be_official_fact():
    candidate = _candidate(
        candidate_source_type="provider_endpoint",
        accepted_as_official=True,
        is_official_candidate=False,
    )

    with pytest.raises(OfficialVerificationValidationError, match="provider endpoint"):
        validate_official_source_candidate(candidate)


def test_valid_official_source_can_be_accepted():
    assert can_source_be_accepted_as_official(_candidate()) is True
