# -*- coding: utf-8 -*-

import builtins
import copy
import socket
import urllib.request

import pytest

from src.fundamental_skill.data_verification.synthetic_official_disclosure_pipeline_dry_run import (
    build_synthetic_official_disclosure_pipeline_dry_run_result,
    validate_synthetic_official_disclosure_pipeline_dry_run_result,
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


def _build(candidates, **overrides):
    payload = {
        "stock_code": "600406",
        "company_name": "Guodian NARI",
        "query_period": {"period_key": "2024FY", "period_end_date": "2024-12-31"},
        "requested_announcement_type": "annual_report",
        "input_discovery_candidates": candidates,
    }
    payload.update(overrides)
    return build_synthetic_official_disclosure_pipeline_dry_run_result(**payload)


def test_result_not_for_trading_advice_missing_rejected():
    result = _build([_candidate()])
    del result["not_for_trading_advice"]

    with pytest.raises(OfficialVerificationValidationError, match="not_for_trading_advice|missing keys"):
        validate_synthetic_official_disclosure_pipeline_dry_run_result(result)


def test_result_not_for_trading_advice_false_rejected():
    result = _build([_candidate()])
    result["not_for_trading_advice"] = False

    with pytest.raises(OfficialVerificationValidationError, match="not_for_trading_advice"):
        validate_synthetic_official_disclosure_pipeline_dry_run_result(result)


def test_result_not_for_trading_advice_non_bool_rejected():
    result = _build([_candidate()])
    result["not_for_trading_advice"] = "true"

    with pytest.raises(OfficialVerificationValidationError, match="not_for_trading_advice"):
        validate_synthetic_official_disclosure_pipeline_dry_run_result(result)


def test_candidate_not_for_trading_advice_missing_rejected_as_candidate_gap():
    candidate = _candidate()
    del candidate["not_for_trading_advice"]

    result = _build([candidate])

    assert result["rejected_discovery_candidates"][0]["rejection_reason"] == "not_for_trading_advice_required"
    assert result["locator_result"]["locator_status"] == "rejected_all_candidates"


def test_candidate_not_for_trading_advice_false_rejected_fail_closed():
    with pytest.raises(OfficialVerificationValidationError, match="not_for_trading_advice"):
        _build([_candidate(not_for_trading_advice=False)])


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
    with pytest.raises(OfficialVerificationValidationError, match="forbidden|not_for_trading_advice"):
        _build([_candidate(caveats=[{"nested": [marker]}])])


@pytest.mark.parametrize(
    "marker_key",
    [
        "token",
        "env",
        "tushare_token_txt",
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
    with pytest.raises(OfficialVerificationValidationError, match="forbidden"):
        _build([_candidate(raw_candidate_metadata={marker_key: True})])


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
    with pytest.raises(OfficialVerificationValidationError, match="forbidden"):
        _build([_candidate(caveats=[{"nested": [marker]}])])


def test_final_recursive_safety_scan_covers_nested_result():
    result = _build([_candidate()])
    unsafe = copy.deepcopy(result)
    unsafe["readiness_skeleton"]["required_explicit_inputs"].append({"nested": ["target price"]})

    with pytest.raises(OfficialVerificationValidationError, match="forbidden"):
        validate_synthetic_official_disclosure_pipeline_dry_run_result(unsafe)


@pytest.mark.parametrize(
    "marker",
    [
        "accepted manifest write",
        "output baseline write",
        "fixture write",
    ],
)
def test_output_fixture_manifest_write_intent_rejected(marker):
    with pytest.raises(OfficialVerificationValidationError, match="forbidden"):
        _build([_candidate(normalized_candidate_metadata={"intent": marker})])


def test_no_io_no_network_no_file_read(monkeypatch):
    def fail_io(*args, **kwargs):
        raise AssertionError("unexpected IO")

    monkeypatch.setattr(builtins, "open", fail_io)
    monkeypatch.setattr(socket, "socket", fail_io)
    monkeypatch.setattr(urllib.request, "urlopen", fail_io)

    result = _build([_candidate()])

    assert result["locator_result"]["locator_status"] == "found_single_official_candidate"


def test_no_url_fetch():
    result = _build([_candidate(source_url="https://static.cninfo.com.cn/finalpage/2025-04-30/official.pdf")])

    assert result["normalized_discovery_candidates"][0]["source_domain"] == "static.cninfo.com.cn"


def test_no_output_fixture_manifest_write_intent_in_valid_result():
    result = _build([_candidate()])

    text = repr(result)
    assert "accepted manifest write" not in text
    assert "output baseline write" not in text
    assert "fixture write" not in text
