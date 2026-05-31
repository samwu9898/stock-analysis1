# -*- coding: utf-8 -*-

import pytest

from src.fundamental_skill.data_verification.validators import (
    OfficialVerificationValidationError,
    validate_official_disclosure_locator_result,
    validate_official_source_registry_entry,
)


SHA = "d" * 64


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


def test_not_for_trading_advice_missing_rejected():
    entry = _entry()
    del entry["not_for_trading_advice"]

    with pytest.raises(OfficialVerificationValidationError, match="missing keys|not_for_trading_advice"):
        validate_official_source_registry_entry(entry)


def test_not_for_trading_advice_false_rejected():
    with pytest.raises(OfficialVerificationValidationError, match="not_for_trading_advice"):
        validate_official_source_registry_entry(_entry(not_for_trading_advice=False))


@pytest.mark.parametrize(
    "marker",
    [
        "read token",
        "read .env",
        "read tushare_token.txt",
        "provider live call",
        "network intent",
        "download pdf",
        "pdf parser",
        "parse pdf",
        "pdf table extractor",
        "report v1 trigger",
        "accepted manifest write",
        "output baseline write",
        "fixture write",
        "target price",
        "buy recommendation",
        "sell recommendation",
        "hold recommendation",
        "portfolio position",
        "technical signal",
    ],
)
def test_registry_rejects_forbidden_marker_values(marker):
    entry = _entry(caveats=[marker])

    with pytest.raises(OfficialVerificationValidationError, match="forbidden marker"):
        validate_official_source_registry_entry(entry)


@pytest.mark.parametrize(
    "key",
    [
        "token_read",
        "provider_live_call",
        "network_intent",
        "download_pdf",
        "pdf_parser",
        "parse_pdf",
        "pdf_table_extractor",
        "report_v1_trigger",
        "accepted_manifest_write",
        "output_baseline_write",
        "fixture_write",
        "target_price",
        "portfolio",
        "technical_signal",
    ],
)
def test_locator_rejects_forbidden_marker_keys(key):
    result = _result(**{key: True})

    with pytest.raises(OfficialVerificationValidationError, match="forbidden marker|metric/report/write"):
        validate_official_disclosure_locator_result(result)


def test_nested_marker_rejected():
    result = _result(caveats=[{"nested": ["target price"]}])

    with pytest.raises(OfficialVerificationValidationError, match="forbidden marker"):
        validate_official_disclosure_locator_result(result)


def test_nested_not_for_trading_false_rejected():
    result = _result(candidates=[_entry(caveats=[{"not_for_trading_advice": False}])])

    with pytest.raises(OfficialVerificationValidationError, match="not_for_trading_advice"):
        validate_official_disclosure_locator_result(result)
