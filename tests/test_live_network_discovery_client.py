# -*- coding: utf-8 -*-

import builtins
import socket
import urllib.request

import pytest

import src.fundamental_skill.data_verification.live_network_discovery_client as live_client
from src.fundamental_skill.data_verification.live_network_discovery_client import (
    CLIENT_MODE_INJECTED_FAKE,
    ERROR_CONTENT_TYPE_REJECTED,
    ERROR_DOMAIN_REJECTED,
    ERROR_EMPTY_RESULT,
    ERROR_MALFORMED_RESPONSE,
    ERROR_RATE_LIMITED,
    ERROR_REDIRECT_REJECTED,
    ERROR_RETRY_EXHAUSTED,
    ERROR_TIMEOUT,
    REASON_CONTENT_TYPE_REJECTED,
    REASON_DOMAIN_REJECTED,
    REASON_EMPTY_RESULT,
    REASON_FAKE_RESPONSES_MISSING,
    REASON_FAKE_RESPONSES_NOT_LIST,
    REASON_MALFORMED_RESPONSE,
    REASON_POLICY_REJECTED,
    REASON_REDIRECT_REJECTED,
    REASON_UNSUPPORTED_SOURCE_FAMILY,
    discover_live_network_metadata_with_injected_fake_client,
    validate_live_network_discovery_client_result,
)
from src.fundamental_skill.data_verification.official_disclosure_request import (
    normalize_official_disclosure_request,
)
from src.fundamental_skill.data_verification.security_identity import normalize_security_identity


def _request(stock_code="600406", company_name="Guodian NARI", **overrides):
    payload = {
        "security_identity": normalize_security_identity(
            {
                "stock_code": stock_code,
                "company_name": company_name,
                "not_for_trading_advice": True,
            }
        ),
        "query_period": "2024",
        "not_for_trading_advice": True,
    }
    payload.update(overrides)
    return normalize_official_disclosure_request(payload)


def _fake_response(request=None, **overrides):
    request = request or _request()
    record = {
        "source_family": "cninfo",
        "source_domain": "static.cninfo.com.cn",
        "source_url": "https://static.cninfo.com.cn/metadata/2025-04-30/600406-2024.html",
        "source_title": f"{request['stock_code']} 2024 annual report",
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


def _discover(fake_response, request=None, **kwargs):
    request = request or _request()
    return discover_live_network_metadata_with_injected_fake_client(
        request,
        [fake_response],
        **kwargs,
    )


def _error_codes(result):
    return [error["error_code"] for error in result["errors"]]


def test_injected_fake_client_success_path_hands_off_to_adapter():
    request = _request()
    result = _discover(_fake_response(request), request)

    assert result["schema_version"] == "live_network_discovery_client_result.v1"
    assert result["client_mode"] == CLIENT_MODE_INJECTED_FAKE
    assert result["blocked_reasons"] == []
    assert result["errors"] == []
    assert result["not_for_trading_advice"] is True
    assert result["typed_metadata_query"]["metadata_only"] is True
    assert result["typed_metadata_query"]["stock_code"] == "600406"
    assert "static.cninfo.com.cn" in result["typed_metadata_query"]["allowed_domains"]
    assert len(result["normalized_metadata_records"]) == 1
    assert result["discovery_adapter_result"]["blocked_reasons"] == []
    assert result["discovery_adapter_result"]["discovery_candidates"][0]["source_domain"] == "static.cninfo.com.cn"
    validate_live_network_discovery_client_result(result)


@pytest.mark.parametrize(
    ("family", "domain", "url", "source_type", "stock_code", "company_name", "expected_method"),
    [
        (
            "cninfo",
            "static.cninfo.com.cn",
            "https://static.cninfo.com.cn/metadata/600406-2024.html",
            "cninfo_official_pdf",
            "600406",
            "Guodian NARI",
            "cninfo_search_result",
        ),
        (
            "sse",
            "www.sse.com.cn",
            "https://www.sse.com.cn/disclosure/listedinfo/announcement/c/600406-2024.html",
            "sse_exchange_announcement",
            "600406",
            "Guodian NARI",
            "sse_announcement_list",
        ),
        (
            "szse",
            "www.szse.cn",
            "https://www.szse.cn/disclosure/listed/bulletinDetail/000001-2024.html",
            "exchange_official_pdf",
            "000001",
            "Ping An Bank",
            "exchange_announcement_list",
        ),
        (
            "bse",
            "www.bse.cn",
            "https://www.bse.cn/disclosure/2025/2024-annual.html",
            "exchange_official_pdf",
            "830799",
            "BSE Example",
            "exchange_announcement_list",
        ),
    ],
)
def test_source_family_fake_metadata_response_normalized(
    family, domain, url, source_type, stock_code, company_name, expected_method
):
    request = _request(stock_code=stock_code, company_name=company_name)
    result = _discover(
        _fake_response(
            request,
            source_family=family,
            source_domain=domain,
            source_url=url,
            source_type=source_type,
            source_title=f"{stock_code} 2024 annual report",
        ),
        request,
    )

    assert result["blocked_reasons"] == []
    record = result["normalized_metadata_records"][0]
    assert record["source_domain"] == domain
    assert record["source_type"] == source_type
    assert record["discovery_method"] == expected_method
    assert result["discovery_adapter_result"]["discovery_candidates"][0]["source_domain"] == domain


def test_non_allowlist_domain_rejected():
    result = _discover(
        _fake_response(source_domain="evil.example", source_url="https://evil.example/metadata.html")
    )

    assert result["normalized_metadata_records"] == []
    assert ERROR_DOMAIN_REJECTED in _error_codes(result)
    assert REASON_DOMAIN_REJECTED in result["blocked_reasons"]


@pytest.mark.parametrize(
    ("domain", "url"),
    [
        ("cninfo.com.cn", "https://cninfo.com.cn/metadata.html"),
        ("sse.com.cn", "https://sse.com.cn/metadata.html"),
        ("szse.cn", "https://szse.cn/metadata.html"),
        ("bse.cn", "https://bse.cn/metadata.html"),
    ],
)
def test_apex_host_rejected_unless_explicitly_allowed(domain, url):
    result = _discover(_fake_response(source_domain=domain, source_url=url))

    assert ERROR_DOMAIN_REJECTED in _error_codes(result)
    assert result["discovery_adapter_result"]["discovery_candidates"] == []


def test_path_or_query_allowlist_spoof_rejected():
    result = _discover(
        _fake_response(
            source_domain="evil.example",
            source_url="https://evil.example/path/static.cninfo.com.cn/page?next=www.sse.com.cn",
        )
    )

    assert ERROR_DOMAIN_REJECTED in _error_codes(result)


def test_userinfo_url_rejected():
    result = _discover(_fake_response(source_url="https://user@static.cninfo.com.cn/metadata.html"))

    assert ERROR_DOMAIN_REJECTED in _error_codes(result)


@pytest.mark.parametrize("url", ["https://", "file:///tmp/local.html", "https://static.cninfo.com.cn:8443/metadata.html"])
def test_malformed_url_rejected(url):
    result = _discover(_fake_response(source_url=url))

    assert ERROR_DOMAIN_REJECTED in _error_codes(result)


def test_mixed_case_host_and_trailing_dot_normalized():
    result = _discover(
        _fake_response(
            source_domain="STATIC.CNINFO.COM.CN.",
            source_url="HTTPS://STATIC.CNINFO.COM.CN./metadata.html",
        )
    )

    assert result["blocked_reasons"] == []
    assert result["normalized_metadata_records"][0]["source_url"] == "https://static.cninfo.com.cn/metadata.html"
    assert result["normalized_metadata_records"][0]["source_domain"] == "static.cninfo.com.cn"


def test_redirect_chain_valid_path():
    result = _discover(
        _fake_response(
            source_family="cninfo",
            redirect_chain=[
                "https://www.cninfo.com.cn/new/disclosure",
                "https://static.cninfo.com.cn/metadata/600406-2024.html",
            ],
        )
    )

    assert result["blocked_reasons"] == []
    assert len(result["normalized_metadata_records"][0]["redirect_chain"]) == 2


def test_redirect_chain_non_list_rejected():
    result = _discover(_fake_response(redirect_chain="https://static.cninfo.com.cn/metadata.html"))

    assert ERROR_REDIRECT_REJECTED in _error_codes(result)
    assert REASON_REDIRECT_REJECTED in result["blocked_reasons"]


def test_redirect_chain_too_long_rejected():
    result = _discover(
        _fake_response(
            redirect_chain=[
                "https://static.cninfo.com.cn/a.html",
                "https://static.cninfo.com.cn/b.html",
                "https://static.cninfo.com.cn/c.html",
                "https://static.cninfo.com.cn/d.html",
            ]
        )
    )

    assert ERROR_REDIRECT_REJECTED in _error_codes(result)


def test_cross_domain_redirect_rejected():
    result = _discover(
        _fake_response(
            redirect_chain=[
                "https://static.cninfo.com.cn/a.html",
                "https://www.sse.com.cn/disclosure/a.html",
            ]
        )
    )

    assert ERROR_REDIRECT_REJECTED in _error_codes(result)


def test_redirect_to_binary_endpoint_rejected():
    result = _discover(_fake_response(redirect_chain=["https://static.cninfo.com.cn/finalpage/official.pdf"]))

    assert ERROR_REDIRECT_REJECTED in _error_codes(result)


@pytest.mark.parametrize(
    ("error_code", "expected"),
    [
        (ERROR_TIMEOUT, ERROR_TIMEOUT),
        (ERROR_RETRY_EXHAUSTED, ERROR_RETRY_EXHAUSTED),
        (ERROR_RATE_LIMITED, ERROR_RATE_LIMITED),
        (ERROR_MALFORMED_RESPONSE, ERROR_MALFORMED_RESPONSE),
        (ERROR_EMPTY_RESULT, ERROR_EMPTY_RESULT),
    ],
)
def test_explicit_fake_error_response_modeled_as_blocked(error_code, expected):
    result = _discover(_fake_response(error_code=error_code, error_message="temporary"))

    assert result["normalized_metadata_records"] == []
    assert expected in _error_codes(result)
    assert result["blocked_reasons"]
    assert result["discovery_adapter_result"]["discovery_candidates"] == []


@pytest.mark.parametrize(
    "content_type",
    ["application/pdf", "application/octet-stream", "image/png", "application/zip", "text/plain", ""],
)
def test_blocked_or_unknown_content_type_rejected_without_artifact_access(content_type):
    result = _discover(_fake_response(content_type=content_type))

    assert ERROR_CONTENT_TYPE_REJECTED in _error_codes(result)
    assert REASON_CONTENT_TYPE_REJECTED in result["blocked_reasons"]


def test_content_type_mismatch_with_binary_suffix_rejected():
    result = _discover(_fake_response(source_url="https://static.cninfo.com.cn/finalpage/official.pdf"))

    assert ERROR_CONTENT_TYPE_REJECTED in _error_codes(result)


@pytest.mark.parametrize("field", ["source_title", "disclosure_date", "source_url"])
def test_missing_required_fake_metadata_rejected(field):
    result = _discover(_fake_response(**{field: ""}))

    assert ERROR_MALFORMED_RESPONSE in _error_codes(result)
    assert REASON_MALFORMED_RESPONSE in result["blocked_reasons"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("stock_code", "600000"),
        ("exchange", "SZSE"),
        ("period_key", "2024H1"),
        ("period_end_date", "2024-06-30"),
        ("announcement_type", "semiannual_report"),
    ],
)
def test_request_mismatch_rejected(field, value):
    result = _discover(_fake_response(**{field: value}))

    assert REASON_POLICY_REJECTED in result["blocked_reasons"]
    assert result["normalized_metadata_records"] == []


def test_handoff_to_official_source_discovery_adapter(monkeypatch):
    calls = {"count": 0}
    original = live_client.discover_official_sources_from_metadata

    def counting_adapter(request, records):
        calls["count"] += 1
        return original(request, records)

    monkeypatch.setattr(live_client, "discover_official_sources_from_metadata", counting_adapter)

    result = _discover(_fake_response())

    assert result["blocked_reasons"] == []
    assert calls["count"] == 1
    assert result["discovery_adapter_result"]["discovery_candidates"]


def test_no_direct_registry_locator_or_fact_generation():
    result = _discover(_fake_response())

    for forbidden_key in (
        "registry_entry",
        "locator_result",
        "verified_fact",
        "official_metric_fact",
        "provider_official_conflict",
        "accepted_manifest",
        "output_baseline",
        "fixture_payload",
    ):
        assert forbidden_key not in result
        assert forbidden_key not in result["discovery_adapter_result"]
        assert forbidden_key not in result["discovery_adapter_result"]["discovery_candidates"][0]


def test_real_network_mode_disabled_by_design():
    result = _discover(_fake_response(), client_mode="real_network")

    assert result["client_mode"] == CLIENT_MODE_INJECTED_FAKE
    assert result["normalized_metadata_records"] == []
    assert result["errors"][0]["error_code"] == "policy_rejected"
    assert "client_mode_blocked" in result["blocked_reasons"]


def test_fake_responses_missing_non_list_and_empty_blocked():
    request = _request()

    missing = discover_live_network_metadata_with_injected_fake_client(request, None)
    non_list = discover_live_network_metadata_with_injected_fake_client(request, {"records": []})
    empty = discover_live_network_metadata_with_injected_fake_client(request, [])

    assert REASON_FAKE_RESPONSES_MISSING in missing["blocked_reasons"]
    assert REASON_FAKE_RESPONSES_NOT_LIST in non_list["blocked_reasons"]
    assert REASON_EMPTY_RESULT in empty["blocked_reasons"]


def test_unsupported_source_family_rejected():
    result = _discover(_fake_response(source_family="unknown"))

    assert REASON_UNSUPPORTED_SOURCE_FAMILY in result["blocked_reasons"]
    assert result["normalized_metadata_records"] == []


def test_no_io_no_url_fetch_no_file_read(monkeypatch):
    def fail_io(*args, **kwargs):
        raise AssertionError("unexpected external access")

    monkeypatch.setattr(builtins, "open", fail_io)
    monkeypatch.setattr(socket, "socket", fail_io)
    monkeypatch.setattr(urllib.request, "urlopen", fail_io)

    result = _discover(_fake_response())

    assert result["blocked_reasons"] == []
    assert result["discovery_adapter_result"]["discovery_candidates"][0]["source_domain"] == "static.cninfo.com.cn"
