# -*- coding: utf-8 -*-

import pytest

from src.fundamental_skill.data_verification.official_disclosure_request import (
    REJECTION_FORBIDDEN_MARKER_DETECTED,
    REJECTION_LIVE_LOOKUP_FORBIDDEN,
    REJECTION_NOT_FOR_TRADING_ADVICE_REQUIRED,
    REJECTION_OUTPUT_FIXTURE_MANIFEST_WRITE_FORBIDDEN,
    REJECTION_PDF_PARSER_FORBIDDEN,
    REJECTION_PROVIDER_LOOKUP_FORBIDDEN,
    REJECTION_TRADING_ADVICE_FORBIDDEN,
    OfficialDisclosureRequestSafetyError,
    assert_no_official_disclosure_request_forbidden_markers,
    normalize_official_disclosure_request,
)
from src.fundamental_skill.data_verification.security_identity import normalize_security_identity


def _payload(**overrides):
    payload = {
        "security_identity": normalize_security_identity("600406.SH"),
        "query_period": "2024",
        "not_for_trading_advice": True,
    }
    payload.update(overrides)
    return payload


def _payload_with_note(note):
    return _payload(metadata={"nested": ["safe", {"note": note}]})


def _blocked_request(payload):
    request = normalize_official_disclosure_request(payload)
    assert request["rejection_reason"] is not None
    return request


def test_not_for_trading_advice_missing_rejected():
    payload = _payload()
    del payload["not_for_trading_advice"]

    request = _blocked_request(payload)

    assert request["rejection_reason"] == REJECTION_NOT_FOR_TRADING_ADVICE_REQUIRED


def test_not_for_trading_advice_false_rejected():
    request = _blocked_request(_payload(not_for_trading_advice=False))

    assert request["rejection_reason"] == REJECTION_NOT_FOR_TRADING_ADVICE_REQUIRED


def test_not_for_trading_advice_non_bool_rejected():
    request = _blocked_request(_payload(not_for_trading_advice="true"))

    assert request["rejection_reason"] == REJECTION_NOT_FOR_TRADING_ADVICE_REQUIRED


def test_nested_forbidden_markers_rejected():
    request = _blocked_request(_payload_with_note("download PDF"))

    assert request["rejection_reason"] == REJECTION_LIVE_LOOKUP_FORBIDDEN


@pytest.mark.parametrize("marker", ["token", ".env", "tushare_token"])
def test_token_env_and_tushare_token_markers_rejected(marker):
    request = _blocked_request(_payload_with_note(marker))

    assert request["rejection_reason"] == REJECTION_FORBIDDEN_MARKER_DETECTED


@pytest.mark.parametrize("marker", ["provider live", "AkShare", "Tushare"])
def test_provider_akshare_and_tushare_markers_rejected(marker):
    request = _blocked_request(_payload_with_note(marker))

    assert request["rejection_reason"] == REJECTION_PROVIDER_LOOKUP_FORBIDDEN


@pytest.mark.parametrize("marker", ["network", "HTTP", "fetch", "download"])
def test_network_http_fetch_and_download_markers_rejected(marker):
    request = _blocked_request(_payload_with_note(marker))

    assert request["rejection_reason"] == REJECTION_LIVE_LOOKUP_FORBIDDEN


@pytest.mark.parametrize("marker", ["CNInfo live", "SSE live"])
def test_cninfo_and_sse_live_markers_rejected(marker):
    request = _blocked_request(_payload_with_note(marker))

    assert request["rejection_reason"] == REJECTION_LIVE_LOOKUP_FORBIDDEN


@pytest.mark.parametrize("marker", ["PDF parser", "table extractor", "parse PDF"])
def test_pdf_parser_table_extractor_and_parse_pdf_markers_rejected(marker):
    request = _blocked_request(_payload_with_note(marker))

    assert request["rejection_reason"] == REJECTION_PDF_PARSER_FORBIDDEN


def test_metric_extraction_marker_rejected():
    request = _blocked_request(_payload_with_note("metric extraction"))

    assert request["rejection_reason"] == REJECTION_FORBIDDEN_MARKER_DETECTED


def test_official_metric_fact_marker_rejected():
    request = _blocked_request(_payload_with_note("official_metric_fact"))

    assert request["rejection_reason"] == REJECTION_FORBIDDEN_MARKER_DETECTED


def test_provider_official_conflict_marker_rejected():
    request = _blocked_request(_payload_with_note("provider_official_conflict"))

    assert request["rejection_reason"] == REJECTION_FORBIDDEN_MARKER_DETECTED


def test_report_v1_marker_rejected():
    request = _blocked_request(_payload_with_note("Report V1"))

    assert request["rejection_reason"] == REJECTION_FORBIDDEN_MARKER_DETECTED


@pytest.mark.parametrize(
    "marker",
    ["accepted manifest write", "output baseline write", "fixture write"],
)
def test_accepted_manifest_output_baseline_and_fixture_write_markers_rejected(marker):
    request = _blocked_request(_payload_with_note(marker))

    assert (
        request["rejection_reason"]
        == REJECTION_OUTPUT_FIXTURE_MANIFEST_WRITE_FORBIDDEN
    )


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
    ],
)
def test_trading_signal_markers_rejected(marker):
    request = _blocked_request(_payload_with_note(marker))

    assert request["rejection_reason"] == REJECTION_TRADING_ADVICE_FORBIDDEN


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
    request = _blocked_request(_payload_with_note(marker))

    assert request["rejection_reason"] is not None


@pytest.mark.parametrize(
    ("marker", "reason"),
    [
        ("live discovery", REJECTION_LIVE_LOOKUP_FORBIDDEN),
        ("provider lookup", REJECTION_PROVIDER_LOOKUP_FORBIDDEN),
        ("PDF parser", REJECTION_PDF_PARSER_FORBIDDEN),
        ("output_write", REJECTION_OUTPUT_FIXTURE_MANIFEST_WRITE_FORBIDDEN),
    ],
)
def test_no_live_discovery_provider_lookup_pdf_parser_or_output_write_intent(
    marker, reason
):
    request = _blocked_request(_payload_with_note(marker))

    assert request["rejection_reason"] == reason


def test_assert_no_official_disclosure_request_forbidden_markers_raises():
    with pytest.raises(OfficialDisclosureRequestSafetyError):
        assert_no_official_disclosure_request_forbidden_markers(
            {"outer": ["safe", {"inner": "target price"}]}
        )
