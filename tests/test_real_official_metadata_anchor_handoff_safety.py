# -*- coding: utf-8 -*-

from __future__ import annotations

import pytest

from src.fundamental_skill.data_verification.official_disclosure_request import (
    normalize_official_disclosure_request,
)
from src.fundamental_skill.data_verification.real_official_metadata_anchor_handoff import (
    REASON_FORBIDDEN_MARKER_DETECTED,
    RealOfficialMetadataHandoffSafetyError,
    assert_no_real_official_metadata_handoff_forbidden_markers,
    build_real_official_metadata_anchor_handoff,
)
from src.fundamental_skill.data_verification.security_identity import (
    normalize_security_identity,
)


def _request(**overrides):
    payload = {
        "security_identity": normalize_security_identity(
            {
                "stock_code": "600406",
                "company_name": "Guodian NARI",
                "not_for_trading_advice": True,
            }
        ),
        "query_period": "2025FY",
        "not_for_trading_advice": True,
    }
    payload.update(overrides)
    return normalize_official_disclosure_request(payload)


def _provider_queue(marker=None):
    queue = {
        "schema_version": "provider_candidate_metric_verification_queue.v1",
        "provider": "Tushare",
        "ts_code": "600406.SH",
        "stock_code": "600406",
        "company_name_hint": "Guodian NARI",
        "periods": ["20251231"],
        "verification_items": [
            {
                "schema_version": "provider_candidate_metric_verification_item.v1",
                "provider": "Tushare",
                "ts_code": "600406.SH",
                "stock_code": "600406",
                "company_name_hint": "Guodian NARI",
                "period": "20251231",
                "period_label": "2025FY",
                "metric_key": "revenue",
                "metric_value": 1000,
                "value_status": "present",
                "source_table": "income",
                "source_field": "revenue",
                "provider_native_unit": "provider_native_amount_unverified",
                "official_verification_status": "pending_official_verification",
                "not_official_verified": True,
                "not_for_trading_advice": True,
                "caveats": ["provider_candidate_requires_official_verification"],
            }
        ],
        "blocked_reasons": [],
        "caveats": [],
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }
    if marker is not None:
        queue["nested_safety_payload"] = [{"marker": marker}]
    return queue


def _fake_client(response):
    def client(_metadata_request):
        return response

    return client


@pytest.mark.parametrize("marker", ["token", ".env", "tushare_token"])
def test_secret_markers_are_rejected(marker):
    with pytest.raises(RealOfficialMetadataHandoffSafetyError):
        assert_no_real_official_metadata_handoff_forbidden_markers({"outer": [{"inner": marker}]})


@pytest.mark.parametrize(
    "marker",
    [
        "official_verified",
        "official_metric_fact",
        "provider_official_conflict",
        "Report V1",
    ],
)
def test_official_fact_and_report_markers_are_rejected(marker):
    result = build_real_official_metadata_anchor_handoff(
        _request(),
        _provider_queue(marker),
        official_http_client=_fake_client({"announcements": []}),
        allow_network=True,
    )

    assert result["blocked_reasons"] == [REASON_FORBIDDEN_MARKER_DETECTED]
    assert marker not in repr(result).replace("not_official_verified", "")


@pytest.mark.parametrize(
    "marker",
    [
        "accepted manifest write",
        "output baseline write",
        "fixture write",
        "accepted_manifest_write",
        "output_baseline_write",
        "fixture_write",
    ],
)
def test_artifact_write_intent_markers_are_rejected(marker):
    with pytest.raises(RealOfficialMetadataHandoffSafetyError):
        assert_no_real_official_metadata_handoff_forbidden_markers({"nested": [marker]})


@pytest.mark.parametrize(
    "marker",
    [
        "download",
        "parse PDF",
        "PDF parser",
        "table extractor",
        "metric extraction",
        "parse_pdf",
        "pdf_parser",
        "table_extractor",
        "metric_extraction",
    ],
)
def test_pdf_and_metric_operation_markers_are_rejected(marker):
    with pytest.raises(RealOfficialMetadataHandoffSafetyError):
        assert_no_real_official_metadata_handoff_forbidden_markers({"nested": [{"marker": marker}]})


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
        "target_price",
        "technical_signal",
    ],
)
def test_trading_advice_markers_are_rejected(marker):
    with pytest.raises(RealOfficialMetadataHandoffSafetyError):
        assert_no_real_official_metadata_handoff_forbidden_markers({"outer": [{"inner": marker}]})


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
        "\u6b63\u5f0f\u7814\u62a5",
        "\u8f93\u51fa\u57fa\u7ebf",
        "\u5199\u5165fixture",
        "\u5199\u5165accepted manifest",
        "\u8bfb\u53d6token",
        "\u8bfb\u53d6.env",
        "\u8bfb\u53d6tushare_token",
        "\u4e0b\u8f7d",
        "\u89e3\u6790PDF",
        "PDF\u89e3\u6790",
        "\u8868\u683c\u62bd\u53d6",
        "\u6307\u6807\u62bd\u53d6",
    ],
)
def test_chinese_forbidden_markers_are_rejected(marker):
    with pytest.raises(RealOfficialMetadataHandoffSafetyError):
        assert_no_real_official_metadata_handoff_forbidden_markers({"nested": ["safe", {"marker": marker}]})


def test_url_token_marker_is_rejected_without_echoing_secret(capsys):
    secret_url = "https://static.cninfo.com.cn/finalpage/report.pdf?token=VerySecretValue123"
    result = build_real_official_metadata_anchor_handoff(
        _request(),
        _provider_queue(),
        official_http_client=_fake_client(
            {
                "announcements": [
                    {
                        "secCode": "600406",
                        "secName": "Guodian NARI",
                        "announcementTitle": "Guodian NARI 2025 Annual Report",
                        "adjunctUrl": secret_url,
                        "announcementTime": "2026-04-30",
                    }
                ]
            }
        ),
        allow_network=True,
    )
    captured = capsys.readouterr()

    assert REASON_FORBIDDEN_MARKER_DETECTED in result["blocked_reasons"]
    assert "VerySecretValue123" not in repr(result)
    assert "VerySecretValue123" not in captured.out
    assert "VerySecretValue123" not in captured.err
    assert captured.out == ""
    assert captured.err == ""


def test_allowed_flags_and_anchor_status_are_not_false_positives():
    payload = {
        "not_official_verified": True,
        "not_for_trading_advice": True,
        "official_verification_status": "pending_official_verification",
        "anchor_evidence_status": "official_anchor_candidate",
        "source_url": "https://static.cninfo.com.cn/finalpage/2026-04-30/report.pdf",
    }

    assert_no_real_official_metadata_handoff_forbidden_markers(payload)


def test_source_url_operation_word_is_not_a_false_positive():
    payload = {
        "source_url": "https://static.cninfo.com.cn/download/report.pdf",
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }

    assert_no_real_official_metadata_handoff_forbidden_markers(payload)


def test_no_token_appears_in_result_or_captured_output(capsys):
    request = _request()
    request["debug_payload"] = "token SuperSecretShouldNotEcho987654321"

    result = build_real_official_metadata_anchor_handoff(
        request,
        _provider_queue(),
        official_http_client=_fake_client({"announcements": []}),
        allow_network=True,
    )
    captured = capsys.readouterr()

    assert result["blocked_reasons"] == [REASON_FORBIDDEN_MARKER_DETECTED]
    assert "SuperSecretShouldNotEcho987654321" not in repr(result)
    assert "SuperSecretShouldNotEcho987654321" not in captured.out
    assert "SuperSecretShouldNotEcho987654321" not in captured.err
    assert captured.out == ""
    assert captured.err == ""
