# -*- coding: utf-8 -*-

from __future__ import annotations

import pytest

from src.fundamental_skill.data_verification.official_artifact_cache_acquisition import (
    OfficialArtifactCacheSafetyError,
    REASON_FORBIDDEN_MARKER_DETECTED,
    assert_no_official_artifact_cache_forbidden_markers,
    build_official_artifact_cache_from_anchor_map,
)


def _anchor_map(marker=None, source_url=None):
    anchor_url = source_url or "https://static.cninfo.com.cn/finalpage/2026-04-30/report.pdf"
    payload = {
        "schema_version": "provider_metric_official_disclosure_anchor_map.v1",
        "provider": "Tushare",
        "ts_code": "600406.SH",
        "stock_code": "600406",
        "company_name_hint": "Guodian NARI",
        "anchor_items": [
            {
                "schema_version": "provider_metric_official_disclosure_anchor_item.v1",
                "provider": "Tushare",
                "ts_code": "600406.SH",
                "stock_code": "600406",
                "company_name_hint": "Guodian NARI",
                "period": "20260331",
                "period_label": "2026Q1",
                "metric_key": "revenue",
                "metric_value": 1000,
                "value_status": "present",
                "source_table": "income",
                "source_field": "revenue",
                "provider_native_unit": "provider_native_amount_unverified",
                "official_verification_status": "pending_official_verification",
                "official_anchor_status": "matched",
                "official_anchor_required": True,
                "official_disclosure_anchor": {
                    "source_title": "Guodian NARI 2026 Q1 Report",
                    "source_url": anchor_url,
                    "source_domain": "static.cninfo.com.cn",
                    "disclosure_date": "2026-04-30",
                    "stock_code": "600406",
                    "company_name_hint": "Guodian NARI",
                    "period_key": "2026Q1",
                    "period_end_date": "20260331",
                    "announcement_type": "quarterly_report",
                    "source_type": "cninfo_official_pdf",
                    "anchor_evidence_status": "official_anchor_candidate",
                    "not_for_trading_advice": True,
                },
                "not_official_verified": True,
                "not_for_trading_advice": True,
                "caveats": [],
            }
        ],
        "blocked_reasons": [],
        "caveats": [],
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }
    if marker is not None:
        payload["nested_safety_payload"] = [{"marker": marker}]
    return payload


@pytest.mark.parametrize("marker", ["token", ".env", "tushare_token"])
def test_secret_markers_are_rejected(marker):
    with pytest.raises(OfficialArtifactCacheSafetyError):
        assert_no_official_artifact_cache_forbidden_markers({"outer": [{"inner": marker}]})


@pytest.mark.parametrize(
    "marker",
    [
        "official_verified",
        "official_metric_fact",
        "provider_official_conflict",
        "Report V1",
    ],
)
def test_official_fact_conflict_and_report_markers_are_rejected(marker):
    with pytest.raises(OfficialArtifactCacheSafetyError):
        assert_no_official_artifact_cache_forbidden_markers({"nested": [marker]})


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
    with pytest.raises(OfficialArtifactCacheSafetyError):
        assert_no_official_artifact_cache_forbidden_markers({"nested": [marker]})


@pytest.mark.parametrize(
    "marker",
    [
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
def test_pdf_content_operation_markers_are_rejected(marker):
    with pytest.raises(OfficialArtifactCacheSafetyError):
        assert_no_official_artifact_cache_forbidden_markers({"nested": [{"marker": marker}]})


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
    with pytest.raises(OfficialArtifactCacheSafetyError):
        assert_no_official_artifact_cache_forbidden_markers({"outer": [{"inner": marker}]})


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
        "\u89e3\u6790PDF",
        "PDF\u89e3\u6790",
        "\u8868\u683c\u62bd\u53d6",
        "\u6307\u6807\u62bd\u53d6",
    ],
)
def test_chinese_forbidden_markers_are_rejected(marker):
    with pytest.raises(OfficialArtifactCacheSafetyError):
        assert_no_official_artifact_cache_forbidden_markers({"nested": ["safe", {"marker": marker}]})


def test_url_token_marker_is_rejected_without_echoing_secret(tmp_path, capsys):
    secret_url = "https://static.cninfo.com.cn/finalpage/report.pdf?token=VerySecretValue123"

    result = build_official_artifact_cache_from_anchor_map(
        _anchor_map(source_url=secret_url),
        cache_dir=tmp_path,
        official_http_client=lambda _request: {"body": b"%PDF-1.7\n", "content_type": "application/pdf"},
        allow_network=True,
    )
    captured = capsys.readouterr()

    assert result["blocked_reasons"] == [REASON_FORBIDDEN_MARKER_DETECTED]
    assert "VerySecretValue123" not in repr(result)
    assert "VerySecretValue123" not in captured.out
    assert "VerySecretValue123" not in captured.err
    assert captured.out == ""
    assert captured.err == ""


def test_allowed_flags_and_anchor_candidate_status_are_not_false_positives():
    payload = {
        "not_official_verified": True,
        "not_for_trading_advice": True,
        "official_verification_status": "pending_official_verification",
        "anchor_evidence_status": "official_anchor_candidate",
        "source_url": "https://static.cninfo.com.cn/finalpage/2026-04-30/report.pdf",
    }

    assert_no_official_artifact_cache_forbidden_markers(payload)


def test_source_url_download_word_is_allowed_for_this_stage():
    payload = {
        "source_url": "https://static.cninfo.com.cn/download/report.pdf",
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }

    assert_no_official_artifact_cache_forbidden_markers(payload)


def test_no_token_appears_in_result_or_captured_output(tmp_path, capsys):
    secret_value = "token SuperSecretShouldNotEcho987654321"

    result = build_official_artifact_cache_from_anchor_map(
        _anchor_map(marker=secret_value),
        cache_dir=tmp_path,
        official_http_client=lambda _request: {"body": b"%PDF-1.7\n", "content_type": "application/pdf"},
        allow_network=True,
    )
    captured = capsys.readouterr()

    assert result["blocked_reasons"] == [REASON_FORBIDDEN_MARKER_DETECTED]
    assert "SuperSecretShouldNotEcho987654321" not in repr(result)
    assert "SuperSecretShouldNotEcho987654321" not in captured.out
    assert "SuperSecretShouldNotEcho987654321" not in captured.err
    assert captured.out == ""
    assert captured.err == ""
