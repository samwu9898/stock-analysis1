# -*- coding: utf-8 -*-

import pytest

from src.fundamental_skill.data_verification.official_disclosure_request import (
    normalize_official_disclosure_request,
)
from src.fundamental_skill.data_verification.request_synthetic_dry_run_integration import (
    RequestSyntheticDryRunIntegrationSafetyError,
    assert_no_request_dry_run_forbidden_markers,
    build_request_synthetic_dry_run_integration_result,
)
from src.fundamental_skill.data_verification.security_identity import (
    normalize_security_identity,
)


def _request_payload(**overrides):
    payload = {
        "security_identity": normalize_security_identity("600406.SH"),
        "company_name": "Guodian NARI",
        "query_period": "2024",
        "not_for_trading_advice": True,
    }
    payload.update(overrides)
    return payload


def _request(**overrides):
    return normalize_official_disclosure_request(_request_payload(**overrides))


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
        "raw_candidate_metadata": {},
        "normalized_candidate_metadata": {},
        "rejection_reason": "",
        "caveats": [],
        "not_for_trading_advice": True,
    }
    candidate.update(overrides)
    return candidate


def _build_with_request_payload(payload):
    return build_request_synthetic_dry_run_integration_result(
        request=payload,
        input_synthetic_candidates=[_candidate()],
    )


def _build_with_candidate_note(note):
    return build_request_synthetic_dry_run_integration_result(
        request=_request(),
        input_synthetic_candidates=[
            _candidate(caveats=[{"nested": ["safe", {"note": note}]}])
        ],
    )


def _assert_request_blocked_for_note(note):
    result = _build_with_request_payload(
        _request_payload(metadata={"nested": ["safe", {"note": note}]})
    )

    assert result["synthetic_dry_run_result"] is None
    assert "request:forbidden_marker" in result["merged_blocked_reasons"]
    assert note not in repr(result)


def _assert_candidate_rejected_for_note(note):
    result = _build_with_candidate_note(note)

    assert result["request_compatible_candidates"] == []
    assert result["synthetic_dry_run_result"] is None
    assert "forbidden_marker" in result["request_rejected_candidates"][0][
        "rejection_reasons"
    ]
    assert note not in repr(result)


def test_not_for_trading_advice_missing_false_and_non_bool_rejected():
    missing_payload = _request_payload()
    del missing_payload["not_for_trading_advice"]
    missing = _build_with_request_payload(missing_payload)
    false = _build_with_request_payload(
        _request_payload(not_for_trading_advice=False)
    )
    non_bool = _build_with_request_payload(
        _request_payload(not_for_trading_advice="true")
    )

    for result in (missing, false, non_bool):
        assert result["synthetic_dry_run_result"] is None
        assert any(
            "not_for_trading_advice_required" in reason
            for reason in result["merged_blocked_reasons"]
        )
        assert result["not_for_trading_advice"] is True
        assert result["request"]["not_for_trading_advice"] is True


def test_nested_forbidden_markers_rejected_in_request_and_candidate():
    _assert_request_blocked_for_note("target price")
    _assert_candidate_rejected_for_note("target price")


@pytest.mark.parametrize("marker", ["token", ".env", "tushare_token"])
def test_token_env_and_tushare_token_markers_rejected(marker):
    _assert_request_blocked_for_note(marker)
    _assert_candidate_rejected_for_note(marker)


@pytest.mark.parametrize("marker", ["provider live", "AkShare", "Tushare"])
def test_provider_akshare_and_tushare_markers_rejected(marker):
    _assert_request_blocked_for_note(marker)
    _assert_candidate_rejected_for_note(marker)


@pytest.mark.parametrize("marker", ["network", "HTTP", "fetch", "download"])
def test_network_http_fetch_and_download_markers_rejected(marker):
    _assert_request_blocked_for_note(marker)
    _assert_candidate_rejected_for_note(marker)


@pytest.mark.parametrize("marker", ["CNInfo live", "SSE live"])
def test_cninfo_and_sse_live_markers_rejected(marker):
    _assert_request_blocked_for_note(marker)
    _assert_candidate_rejected_for_note(marker)


@pytest.mark.parametrize("marker", ["PDF parser", "table extractor", "parse PDF"])
def test_pdf_parser_table_extractor_and_parse_pdf_markers_rejected(marker):
    _assert_request_blocked_for_note(marker)
    _assert_candidate_rejected_for_note(marker)


@pytest.mark.parametrize(
    "marker",
    [
        "metric extraction",
        "official_metric_fact",
        "provider_official_conflict",
        "Report V1",
    ],
)
def test_metric_fact_conflict_and_report_markers_rejected(marker):
    _assert_request_blocked_for_note(marker)
    _assert_candidate_rejected_for_note(marker)


@pytest.mark.parametrize(
    "marker",
    ["accepted manifest write", "output baseline write", "fixture write"],
)
def test_accepted_manifest_output_baseline_and_fixture_write_rejected(marker):
    _assert_request_blocked_for_note(marker)
    _assert_candidate_rejected_for_note(marker)


@pytest.mark.parametrize(
    "marker",
    [
        "buy",
        "sell",
        "hold",
        "target price",
        "portfolio",
        "position",
        "technical signal",
        "trading advice",
        "investment advice",
    ],
)
def test_trading_advice_markers_rejected(marker):
    _assert_request_blocked_for_note(marker)
    _assert_candidate_rejected_for_note(marker)


@pytest.mark.parametrize(
    "marker",
    [
        "涔板叆",
        "鍗栧嚭",
        "鎸佹湁",
        "鐩爣浠?",
        "浠撲綅",
        "缁勫悎",
        "鎶€鏈俊鍙?",
        "鎶曡祫寤鸿",
        "涓嬭浇",
        "缃戠粶",
        "鑱旂綉",
        "瑙ｆ瀽PDF",
        "PDF瑙ｆ瀽",
        "琛ㄦ牸鎶藉彇",
        "鎸囨爣鎶藉彇",
        "姝ｅ紡鐮旀姤",
        "杈撳嚭鍩虹嚎",
        "鍐欏叆fixture",
        "鍐欏叆accepted manifest",
    ],
)
def test_chinese_forbidden_markers_rejected(marker):
    _assert_request_blocked_for_note(marker)
    _assert_candidate_rejected_for_note(marker)


@pytest.mark.parametrize(
    "marker",
    [
        "live discovery",
        "provider lookup",
        "PDF parser",
        "output baseline write",
    ],
)
def test_no_live_discovery_provider_lookup_pdf_parser_or_output_write_intent(marker):
    _assert_request_blocked_for_note(marker)
    _assert_candidate_rejected_for_note(marker)


def test_assert_no_request_dry_run_forbidden_markers_raises():
    with pytest.raises(RequestSyntheticDryRunIntegrationSafetyError):
        assert_no_request_dry_run_forbidden_markers(
            {"outer": ["safe", {"inner": "target price"}], "not_for_trading_advice": True}
        )


def test_source_url_https_and_download_path_are_metadata_not_fetch_intent():
    result = build_request_synthetic_dry_run_integration_result(
        request=_request(allowed_source_types=["exchange_official_pdf"]),
        input_synthetic_candidates=[
            _candidate(
                source_type="exchange_official_pdf",
                source_url="https://disc.static.szse.cn/download/disc/official.pdf",
                discovery_method="exchange_announcement_list",
            )
        ],
    )

    assert result["merged_blocked_reasons"] == []
    assert result["synthetic_dry_run_result"]["locator_result"]["locator_status"] == (
        "found_single_official_candidate"
    )
