# -*- coding: utf-8 -*-

import pytest

from src.fundamental_skill.data_verification.live_network_discovery_client import (
    ERROR_NOT_FOR_TRADING_ADVICE_INVALID,
    ERROR_POLICY_REJECTED,
    REASON_POLICY_REJECTED,
    discover_live_network_metadata_with_injected_fake_client,
    validate_live_network_discovery_client_result,
)
from src.fundamental_skill.data_verification.official_disclosure_request import (
    normalize_official_disclosure_request,
)
from src.fundamental_skill.data_verification.security_identity import normalize_security_identity
from src.fundamental_skill.data_verification.validators import OfficialVerificationValidationError


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


def _fake_response(**overrides):
    request = _request()
    record = {
        "source_family": "cninfo",
        "source_domain": "static.cninfo.com.cn",
        "source_url": "https://static.cninfo.com.cn/metadata/2025-04-30/600406-2024.html",
        "source_title": "600406 2024 annual report",
        "disclosure_date": "2025-04-30",
        "stock_code": request["stock_code"],
        "exchange": request["exchange"],
        "company_name_hint": request["company_name"],
        "period_key": request["query_period"],
        "period_end_date": request["period_end_date"],
        "announcement_type": request["requested_announcement_type"],
        "source_type": "cninfo_official_pdf",
        "content_type": "text/html",
        "artifact_kind": "metadata",
        "is_downloaded": False,
        "discovery_status": "success",
        "freshness_status": "explicit_fake",
        "redirect_chain": [],
        "not_for_trading_advice": True,
    }
    record.update(overrides)
    return record


def _discover(record):
    return discover_live_network_metadata_with_injected_fake_client(_request(), [record])


def _policy_blocked(result):
    assert result["normalized_metadata_records"] == []
    assert result["errors"][0]["error_code"] == ERROR_POLICY_REJECTED
    assert REASON_POLICY_REJECTED in result["blocked_reasons"]


def test_not_for_trading_advice_missing_rejected():
    record = _fake_response()
    del record["not_for_trading_advice"]

    result = _discover(record)

    assert result["errors"][0]["error_code"] == ERROR_NOT_FOR_TRADING_ADVICE_INVALID


def test_not_for_trading_advice_false_rejected():
    result = _discover(_fake_response(not_for_trading_advice=False))

    assert result["errors"][0]["error_code"] == ERROR_NOT_FOR_TRADING_ADVICE_INVALID


def test_not_for_trading_advice_non_bool_rejected():
    result = _discover(_fake_response(not_for_trading_advice="true"))

    assert result["errors"][0]["error_code"] == ERROR_NOT_FOR_TRADING_ADVICE_INVALID


def test_nested_forbidden_markers_rejected():
    result = _discover(_fake_response(policy_decisions=[{"nested": ["target price"]}]))

    _policy_blocked(result)


@pytest.mark.parametrize("marker", ["token", ".env", "tushare_token"])
def test_token_env_and_tushare_token_markers_rejected(marker):
    result = _discover(_fake_response(source_title=f"unsafe {marker} marker"))

    _policy_blocked(result)


@pytest.mark.parametrize("marker", ["provider live", "provider lookup", "AkShare", "Tushare"])
def test_provider_akshare_and_tushare_markers_rejected(marker):
    result = _discover(_fake_response(policy_decisions=[marker]))

    _policy_blocked(result)


@pytest.mark.parametrize("marker", ["network", "HTTP client", "fetch", "download file"])
def test_network_http_fetch_and_download_markers_rejected(marker):
    result = _discover(_fake_response(policy_decisions=[marker]))

    _policy_blocked(result)


@pytest.mark.parametrize("marker", ["CNInfo live", "SSE live"])
def test_cninfo_and_sse_live_markers_rejected(marker):
    result = _discover(_fake_response(policy_decisions=[marker]))

    _policy_blocked(result)


@pytest.mark.parametrize("marker", ["PDF parser", "table extractor", "parse PDF", "parse_pdf"])
def test_pdf_parser_table_extractor_and_parse_pdf_markers_rejected(marker):
    result = _discover(_fake_response(policy_decisions=[marker]))

    _policy_blocked(result)


def test_metric_extraction_marker_rejected():
    result = _discover(_fake_response(policy_decisions=["metric extraction"]))

    _policy_blocked(result)


def test_official_metric_fact_marker_rejected():
    result = _discover(_fake_response(policy_decisions=["official_metric_fact"]))

    _policy_blocked(result)


def test_provider_official_conflict_marker_rejected():
    result = _discover(_fake_response(policy_decisions=["provider_official_conflict"]))

    _policy_blocked(result)


def test_report_v1_marker_rejected():
    result = _discover(_fake_response(policy_decisions=["Report V1"]))

    _policy_blocked(result)


@pytest.mark.parametrize(
    "marker",
    ["accepted manifest write", "output baseline write", "fixture write"],
)
def test_manifest_output_and_fixture_write_markers_rejected(marker):
    result = _discover(_fake_response(policy_decisions=[marker]))

    _policy_blocked(result)


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
    result = _discover(_fake_response(policy_decisions=[marker]))

    _policy_blocked(result)


@pytest.mark.parametrize(
    "marker",
    [
        "\u4e70\u5165",
        "\u5356\u51fa",
        "\u6301\u6709",
        "\u76ee\u6807\u4ef7",
        "\u4ed3\u4f4d",
        "\u7ec4\u5408",
        "\u6280\u672f\u4fe1\u53f7",
        "\u6295\u8d44\u5efa\u8bae",
        "\u4e0b\u8f7d",
        "\u7f51\u7edc",
        "\u8054\u7f51",
        "\u89e3\u6790PDF",
        "PDF\u89e3\u6790",
        "\u8868\u683c\u62bd\u53d6",
        "\u6307\u6807\u62bd\u53d6",
        "\u6b63\u5f0f\u7814\u62a5",
        "\u8f93\u51fa\u57fa\u7ebf",
        "\u5199\u5165fixture",
        "\u5199\u5165accepted manifest",
        "\u8bfb\u53d6token",
        "\u8bfb\u53d6.env",
        "\u8bfb\u53d6tushare_token",
        "\u8c03\u7528AkShare",
        "\u8c03\u7528Tushare",
        "\u8c03\u7528CNInfo live",
        "\u8c03\u7528SSE live",
        "\u8c03\u7528provider",
    ],
)
def test_chinese_forbidden_markers_rejected(marker):
    result = _discover(_fake_response(policy_decisions=[{"nested": [marker]}]))

    _policy_blocked(result)


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "provider_endpoint",
        "provider_lookup",
        "akshare_call",
        "tushare_call",
        "network_intent",
        "http_request",
        "fetch_intent",
        "download_url",
        "download_attempt",
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
        "token_read",
        "env_read",
    ],
)
def test_forbidden_intent_keys_rejected(forbidden_key):
    result = _discover(_fake_response(**{forbidden_key: True}))

    _policy_blocked(result)


@pytest.mark.parametrize(
    "field_update",
    [
        {"is_downloaded": True},
        {"artifact_kind": "download"},
        {"artifact_kind": "PDF parser"},
        {"policy_decisions": ["provider lookup attempt"]},
        {"policy_decisions": ["output baseline write attempt"]},
    ],
)
def test_no_live_call_parser_or_output_write_intent(field_update):
    result = _discover(_fake_response(**field_update))

    _policy_blocked(result)


def test_result_validator_rejects_forbidden_marker_in_input_snapshot():
    result = _discover(_fake_response())
    result["input_fake_responses"][0]["source_title"] = "target price"

    with pytest.raises(OfficialVerificationValidationError, match="forbidden"):
        validate_live_network_discovery_client_result(result)


def test_result_validator_rejects_forbidden_marker_in_policy_decisions_value():
    result = _discover(_fake_response())
    result["policy_decisions"][0]["note"] = "target price"

    with pytest.raises(OfficialVerificationValidationError, match="forbidden"):
        validate_live_network_discovery_client_result(result)


def test_result_validator_rejects_forbidden_marker_in_blocked_reasons_value():
    result = _discover(_fake_response())
    result["blocked_reasons"].append("target price")

    with pytest.raises(OfficialVerificationValidationError, match="forbidden"):
        validate_live_network_discovery_client_result(result)


def test_result_validator_rejects_forbidden_marker_in_discovery_adapter_result_nested_value():
    result = _discover(_fake_response())
    result["discovery_adapter_result"]["caveats"].append("target price")

    with pytest.raises(OfficialVerificationValidationError, match="forbidden"):
        validate_live_network_discovery_client_result(result)


def test_result_validator_rejects_forbidden_marker_in_typed_metadata_query_non_url_field():
    result = _discover(_fake_response())
    result["typed_metadata_query"]["note"] = "target price"

    with pytest.raises(OfficialVerificationValidationError, match="forbidden"):
        validate_live_network_discovery_client_result(result)


def test_result_validator_allows_normal_official_url_fields_with_https():
    result = _discover(
        _fake_response(
            normalized_url="https://static.cninfo.com.cn/metadata/normalized.html",
            redirect_chain=["https://static.cninfo.com.cn/metadata/redirect.html"],
        )
    )
    result["input_fake_responses"][0]["normalized_url"] = "https://static.cninfo.com.cn/metadata/normalized.html"

    validate_live_network_discovery_client_result(result)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_url", "https://static.cninfo.com.cn/metadata/token.html"),
        ("normalized_url", "https://static.cninfo.com.cn/metadata/.env"),
        ("redirect_chain", ["https://static.cninfo.com.cn/metadata/tushare_token.html"]),
    ],
)
def test_result_validator_rejects_secret_markers_in_url_fields(field, value):
    result = _discover(_fake_response())
    result["input_fake_responses"][0][field] = value

    with pytest.raises(OfficialVerificationValidationError, match="URL marker"):
        validate_live_network_discovery_client_result(result)


def test_result_validator_rejects_nested_chinese_marker_in_result_envelope():
    result = _discover(_fake_response())
    result["policy_decisions"][0]["note"] = "\u76ee\u6807\u4ef7"

    with pytest.raises(OfficialVerificationValidationError, match="forbidden"):
        validate_live_network_discovery_client_result(result)


@pytest.mark.parametrize(
    "marker",
    ["official_metric_fact", "provider_official_conflict", "Report V1"],
)
def test_result_validator_rejects_fact_conflict_and_report_markers_in_final_result(marker):
    result = _discover(_fake_response())
    result["policy_decisions"][0]["note"] = marker

    with pytest.raises(OfficialVerificationValidationError, match="forbidden"):
        validate_live_network_discovery_client_result(result)


def test_result_validator_rejects_forbidden_result_field():
    result = _discover(_fake_response())
    result["pdf_text"] = "unsafe"

    with pytest.raises(OfficialVerificationValidationError, match="forbidden"):
        validate_live_network_discovery_client_result(result)
