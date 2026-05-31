# -*- coding: utf-8 -*-

import pytest

from src.fundamental_skill.data_verification.official_disclosure_source_registry import (
    build_source_conflict_reason,
    can_enter_official_cache_lane,
    can_enter_official_candidate_lane,
    classify_source_status,
    validate_sha256,
)
from src.fundamental_skill.data_verification.validators import (
    OfficialVerificationValidationError,
    validate_official_source_registry_entry,
)


SHA = "a" * 64
OTHER_SHA = "b" * 64


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


def test_cninfo_official_pdf_candidate_accepted_as_official_candidate():
    entry = _entry()

    validate_official_source_registry_entry(entry)

    assert can_enter_official_candidate_lane(entry) is True


def test_sse_exchange_announcement_accepted_as_official_candidate():
    entry = _entry(
        source_id="src_600406_2024fy_sse",
        source_type="sse_exchange_announcement",
        source_url="https://www.sse.com.cn/disclosure/listedinfo/announcement/c/official.pdf",
    )

    validate_official_source_registry_entry(entry)

    assert can_enter_official_candidate_lane(entry) is True


def test_exchange_official_pdf_accepted_as_official_candidate():
    entry = _entry(
        source_id="src_600406_2024fy_exchange_pdf",
        source_type="exchange_official_pdf",
        source_url="https://disc.static.szse.cn/download/disc/official.pdf",
    )

    validate_official_source_registry_entry(entry)

    assert can_enter_official_candidate_lane(entry) is True


def test_mirror_rejected_as_official():
    entry = _entry(
        source_type="mirror_source_candidate",
        source_url="https://finance.sina.com.cn/mirror/official.pdf",
        source_status="official_candidate",
    )

    with pytest.raises(OfficialVerificationValidationError, match="mirror|unknown"):
        validate_official_source_registry_entry(entry)


def test_provider_endpoint_rejected_as_official():
    entry = _entry(
        source_type="provider_source_candidate",
        source_url="https://provider.example.invalid/endpoint",
        source_status="official_candidate",
    )

    with pytest.raises(OfficialVerificationValidationError, match="provider"):
        validate_official_source_registry_entry(entry)


def test_unknown_source_blocked():
    entry = _entry(
        source_type="unknown_source_candidate",
        source_url="",
        source_title="",
        disclosure_date="",
        period_key="",
        period_end_date="",
        file_sha256="",
        source_status="blocked_until_review",
        rejection_reason="unknown source requires review",
        caveats=["unknown source candidate"],
    )

    validate_official_source_registry_entry(entry)

    assert classify_source_status(entry) == "blocked_until_review"


def test_local_cache_without_sha256_rejected():
    entry = _entry(
        source_type="local_official_cache",
        source_status="official_cached",
        source_url="https://static.cninfo.com.cn/finalpage/2025-04-30/official.pdf",
        local_cache_path="local/official/600406_2024.pdf",
        file_sha256="",
    )

    with pytest.raises(OfficialVerificationValidationError, match="file_sha256"):
        validate_official_source_registry_entry(entry)


def test_local_cache_cannot_enter_official_candidate_lane():
    entry = _entry(
        source_type="local_official_cache",
        source_status="official_candidate",
        source_url="https://static.cninfo.com.cn/finalpage/2025-04-30/official.pdf",
        local_cache_path="local/official/600406_2024.pdf",
    )

    with pytest.raises(OfficialVerificationValidationError, match="official_candidate"):
        validate_official_source_registry_entry(entry)


def test_local_cache_with_official_url_and_sha256_accepted():
    entry = _entry(
        source_type="local_official_cache",
        source_status="official_cached",
        local_cache_path="local/official/600406_2024.pdf",
        source_url="https://static.cninfo.com.cn/finalpage/2025-04-30/official.pdf",
    )

    validate_official_source_registry_entry(entry)

    assert can_enter_official_cache_lane(entry) is True


def test_local_experiments_cache_cannot_enter_production_official_cache():
    entry = _entry(
        source_type="local_official_cache",
        source_status="official_cached",
        local_cache_path=".local_experiments/600406/official.pdf",
        source_url="https://static.cninfo.com.cn/finalpage/2025-04-30/official.pdf",
    )

    with pytest.raises(OfficialVerificationValidationError, match="local_experiments"):
        validate_official_source_registry_entry(entry)


def test_local_file_without_official_url_blocked():
    entry = _entry(
        source_type="local_official_cache",
        source_status="blocked_until_review",
        source_url="",
        source_title="",
        disclosure_date="",
        period_key="",
        period_end_date="",
        file_sha256="",
        local_cache_path="local/official/600406_2024.pdf",
        rejection_reason="local file lacks original official source URL",
        caveats=["local cache metadata only"],
    )

    validate_official_source_registry_entry(entry)

    assert classify_source_status(entry) == "blocked_until_review"


@pytest.mark.parametrize("missing_key", ["source_title", "disclosure_date", "period_key", "period_end_date"])
def test_missing_disclosure_metadata_rejected(missing_key):
    entry = _entry(**{missing_key: ""})

    with pytest.raises(OfficialVerificationValidationError, match="missing metadata"):
        validate_official_source_registry_entry(entry)


def test_sha256_must_be_64_hex():
    with pytest.raises(OfficialVerificationValidationError, match="sha256"):
        validate_sha256("not-a-sha")


def test_sha256_mismatch_source_conflict_helper():
    reason = build_source_conflict_reason(
        source_url="https://static.cninfo.com.cn/finalpage/2025-04-30/official.pdf",
        previous_sha256=SHA,
        current_sha256=OTHER_SHA,
    )

    assert "source_conflict" in reason
    assert SHA in reason
    assert OTHER_SHA in reason


@pytest.mark.parametrize("required_key", ["registry_version", "source_version", "source_refresh_policy"])
def test_version_and_refresh_policy_required(required_key):
    entry = _entry(**{required_key: ""})

    with pytest.raises(OfficialVerificationValidationError, match=required_key):
        validate_official_source_registry_entry(entry)
