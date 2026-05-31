# -*- coding: utf-8 -*-

import pytest

from src.fundamental_skill.data_verification.official_disclosure_discovery_candidate import (
    normalize_official_disclosure_discovery_candidate,
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
        "raw_candidate_metadata": {},
        "normalized_candidate_metadata": {},
        "rejection_reason": "",
        "caveats": [],
        "not_for_trading_advice": True,
    }
    candidate.update(overrides)
    return candidate


def test_not_for_trading_advice_missing_rejected():
    candidate = _candidate()
    del candidate["not_for_trading_advice"]

    with pytest.raises(OfficialVerificationValidationError, match="not_for_trading_advice"):
        normalize_official_disclosure_discovery_candidate(candidate)


def test_not_for_trading_advice_false_rejected():
    with pytest.raises(OfficialVerificationValidationError, match="not_for_trading_advice"):
        normalize_official_disclosure_discovery_candidate(_candidate(not_for_trading_advice=False))


def test_not_for_trading_advice_non_bool_rejected():
    with pytest.raises(OfficialVerificationValidationError, match="not_for_trading_advice"):
        normalize_official_disclosure_discovery_candidate(_candidate(not_for_trading_advice="true"))


@pytest.mark.parametrize(
    "marker",
    [
        "token",
        ".env",
        "tushare_token.txt",
        "provider live",
        "AkShare live",
        "Tushare live",
        "network",
        "HTTP",
        "fetch",
        "download",
        "CNInfo live",
        "SSE live",
        "PDF parser",
        "table extractor",
        "parse PDF",
        "metric extraction",
        "official_metric_fact",
        "provider_official_conflict",
        "Report V1",
        "accepted manifest write",
        "output baseline write",
        "fixture write",
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
def test_english_forbidden_marker_values_rejected(marker):
    candidate = _candidate(caveats=[marker])

    with pytest.raises(OfficialVerificationValidationError, match="forbidden"):
        normalize_official_disclosure_discovery_candidate(candidate)


@pytest.mark.parametrize(
    "marker_key",
    [
        "token",
        "provider_live",
        "akshare_live",
        "tushare_live",
        "network",
        "http_request",
        "fetch",
        "download",
        "cninfo_live",
        "sse_live",
        "pdf_parser",
        "table_extractor",
        "parse_pdf",
        "metric_extraction",
        "official_metric_fact",
        "provider_official_conflict",
        "report_v1",
        "accepted_manifest_write",
        "output_baseline_write",
        "fixture_write",
        "target_price",
        "portfolio",
        "position",
        "technical_signal",
    ],
)
def test_forbidden_marker_keys_rejected(marker_key):
    candidate = _candidate(raw_candidate_metadata={marker_key: True})

    with pytest.raises(OfficialVerificationValidationError, match="forbidden"):
        normalize_official_disclosure_discovery_candidate(candidate)


@pytest.mark.parametrize(
    "marker",
    [
        "买入",
        "卖出",
        "持有",
        "目标价",
        "仓位",
        "组合",
        "技术信号",
        "投资建议",
        "下载",
        "网络",
        "联网",
        "解析PDF",
        "PDF解析",
        "表格抽取",
        "指标抽取",
        "正式研报",
        "输出基线",
        "写入fixture",
        "写入accepted manifest",
    ],
)
def test_chinese_forbidden_markers_rejected(marker):
    candidate = _candidate(caveats=[{"nested": [marker]}])

    with pytest.raises(OfficialVerificationValidationError, match="forbidden"):
        normalize_official_disclosure_discovery_candidate(candidate)


@pytest.mark.parametrize(
    "marker_key",
    [
        "买入",
        "卖出",
        "持有",
        "目标价",
        "仓位",
        "组合",
        "技术信号",
        "投资建议",
        "下载",
        "网络",
        "联网",
    ],
)
def test_raw_metadata_chinese_forbidden_marker_keys_rejected(marker_key):
    candidate = _candidate(raw_candidate_metadata={marker_key: True})

    with pytest.raises(OfficialVerificationValidationError, match="forbidden"):
        normalize_official_disclosure_discovery_candidate(candidate)


def test_raw_metadata_chinese_forbidden_marker_value_rejected():
    candidate = _candidate(raw_candidate_metadata={"note": "建议买入，目标价10元"})

    with pytest.raises(OfficialVerificationValidationError, match="forbidden"):
        normalize_official_disclosure_discovery_candidate(candidate)


def test_normalized_metadata_chinese_forbidden_marker_nested_rejected():
    candidate = _candidate(normalized_candidate_metadata={"outer": [{"目标价": "10元"}]})

    with pytest.raises(OfficialVerificationValidationError, match="forbidden"):
        normalize_official_disclosure_discovery_candidate(candidate)


def test_nested_forbidden_markers_rejected():
    candidate = _candidate(raw_candidate_metadata={"outer": [{"inner": ["target price"]}]})

    with pytest.raises(OfficialVerificationValidationError, match="forbidden"):
        normalize_official_disclosure_discovery_candidate(candidate)


@pytest.mark.parametrize(
    "marker",
    [
        "hidden_promotion",
        "file_authority",
        "provider_authority",
        "parsed_metrics",
        "report_ready_facts",
        "verified_fact_generation",
    ],
)
def test_hidden_promotion_and_authority_markers_rejected(marker):
    candidate = _candidate(normalized_candidate_metadata={marker: True})

    with pytest.raises(OfficialVerificationValidationError, match="forbidden"):
        normalize_official_disclosure_discovery_candidate(candidate)


def test_source_url_https_and_download_path_are_not_treated_as_network_action():
    candidate = _candidate(
        source_type="exchange_official_pdf",
        source_url="https://disc.static.szse.cn/download/disc/official.pdf",
        discovery_method="exchange_announcement_list",
    )

    normalized = normalize_official_disclosure_discovery_candidate(candidate)

    assert normalized["source_domain"] == "disc.static.szse.cn"
