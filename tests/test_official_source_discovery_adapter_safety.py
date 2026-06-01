# -*- coding: utf-8 -*-

import pytest

from src.fundamental_skill.data_verification.official_disclosure_request import (
    normalize_official_disclosure_request,
)
from src.fundamental_skill.data_verification.official_source_discovery_adapter import (
    REASON_FORBIDDEN_MARKER_DETECTED,
    REASON_NOT_FOR_TRADING_ADVICE_REQUIRED,
    discover_official_sources_from_metadata,
)
from src.fundamental_skill.data_verification.security_identity import normalize_security_identity


def _request():
    return normalize_official_disclosure_request(
        {
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
    )


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


def _discover(record):
    return discover_official_sources_from_metadata(_request(), [record])


def test_not_for_trading_advice_missing_rejected():
    record = _record()
    del record["not_for_trading_advice"]

    result = _discover(record)

    assert REASON_NOT_FOR_TRADING_ADVICE_REQUIRED in result["rejected_records"][0]["reasons"]


def test_not_for_trading_advice_false_rejected():
    result = _discover(_record(not_for_trading_advice=False))

    assert REASON_NOT_FOR_TRADING_ADVICE_REQUIRED in result["rejected_records"][0]["reasons"]


def test_not_for_trading_advice_non_bool_rejected():
    result = _discover(_record(not_for_trading_advice="true"))

    assert REASON_NOT_FOR_TRADING_ADVICE_REQUIRED in result["rejected_records"][0]["reasons"]


def test_nested_forbidden_markers_rejected():
    result = _discover(_record(caveats=[{"nested": ["target price"]}]))

    assert result["discovery_candidates"] == []
    assert REASON_FORBIDDEN_MARKER_DETECTED in result["rejected_records"][0]["reasons"]


@pytest.mark.parametrize("marker", ["token", ".env", "tushare_token"])
def test_token_env_and_tushare_token_markers_rejected(marker):
    result = _discover(_record(source_title=f"unsafe {marker} marker"))

    assert REASON_FORBIDDEN_MARKER_DETECTED in result["rejected_records"][0]["reasons"]


@pytest.mark.parametrize("marker", ["provider live", "AkShare", "Tushare"])
def test_provider_akshare_and_tushare_markers_rejected(marker):
    result = _discover(_record(caveats=[marker]))

    assert REASON_FORBIDDEN_MARKER_DETECTED in result["rejected_records"][0]["reasons"]


@pytest.mark.parametrize("marker", ["network", "HTTP client", "fetch", "download file"])
def test_network_http_fetch_and_download_markers_rejected(marker):
    result = _discover(_record(caveats=[marker]))

    assert REASON_FORBIDDEN_MARKER_DETECTED in result["rejected_records"][0]["reasons"]


@pytest.mark.parametrize("marker", ["CNInfo live", "SSE live"])
def test_cninfo_and_sse_live_markers_rejected(marker):
    result = _discover(_record(caveats=[marker]))

    assert REASON_FORBIDDEN_MARKER_DETECTED in result["rejected_records"][0]["reasons"]


@pytest.mark.parametrize("marker", ["PDF parser", "table extractor", "parse PDF"])
def test_pdf_parser_table_extractor_and_parse_pdf_markers_rejected(marker):
    result = _discover(_record(caveats=[marker]))

    assert REASON_FORBIDDEN_MARKER_DETECTED in result["rejected_records"][0]["reasons"]


def test_metric_extraction_marker_rejected():
    result = _discover(_record(caveats=["metric extraction"]))

    assert REASON_FORBIDDEN_MARKER_DETECTED in result["rejected_records"][0]["reasons"]


def test_official_metric_fact_marker_rejected():
    result = _discover(_record(caveats=["official_metric_fact"]))

    assert REASON_FORBIDDEN_MARKER_DETECTED in result["rejected_records"][0]["reasons"]


def test_provider_official_conflict_marker_rejected():
    result = _discover(_record(caveats=["provider_official_conflict"]))

    assert REASON_FORBIDDEN_MARKER_DETECTED in result["rejected_records"][0]["reasons"]


def test_report_v1_marker_rejected():
    result = _discover(_record(caveats=["Report V1"]))

    assert REASON_FORBIDDEN_MARKER_DETECTED in result["rejected_records"][0]["reasons"]


@pytest.mark.parametrize(
    "marker",
    ["accepted manifest write", "output baseline write", "fixture write"],
)
def test_manifest_output_and_fixture_write_markers_rejected(marker):
    result = _discover(_record(caveats=[marker]))

    assert REASON_FORBIDDEN_MARKER_DETECTED in result["rejected_records"][0]["reasons"]


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
def test_trading_and_investment_advice_markers_rejected(marker):
    result = _discover(_record(caveats=[marker]))

    assert REASON_FORBIDDEN_MARKER_DETECTED in result["rejected_records"][0]["reasons"]


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
        "璇诲彇token",
        "璇诲彇.env",
        "璇诲彇tushare_token",
        "璋冪敤AkShare",
        "璋冪敤Tushare",
        "璋冪敤CNInfo live",
        "璋冪敤SSE live",
        "璋冪敤provider",
    ],
)
def test_chinese_forbidden_markers_rejected(marker):
    result = _discover(_record(caveats=[{"nested": [marker]}]))

    assert REASON_FORBIDDEN_MARKER_DETECTED in result["rejected_records"][0]["reasons"]


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "provider_live",
        "akshare_live",
        "tushare_live",
        "network_intent",
        "http_request",
        "fetch_intent",
        "pdf_parser",
        "table_extractor",
        "parse_pdf",
        "metric_extraction",
        "official_metric_fact",
        "provider_official_conflict",
        "report_v1",
        "accepted_manifest_path",
        "output_path",
        "fixture_path",
        "downloaded_file_sha256",
        "local_cache_path",
    ],
)
def test_live_discovery_provider_parser_output_and_local_file_intent_keys_rejected(forbidden_key):
    result = _discover(_record(**{forbidden_key: True}))

    assert REASON_FORBIDDEN_MARKER_DETECTED in result["rejected_records"][0]["reasons"]
    assert result["discovery_candidates"] == []
