# -*- coding: utf-8 -*-

from __future__ import annotations

import pytest

from src.fundamental_skill.data_verification.provider_metric_official_anchor import (
    ProviderMetricOfficialAnchorError,
    assert_no_provider_metric_anchor_forbidden_markers,
    build_provider_metric_official_disclosure_anchor_map,
)


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


def _official_candidate(**overrides):
    candidate = {
        "source_title": "Guodian NARI 2025 Annual Report",
        "source_url": "https://static.cninfo.com.cn/finalpage/2026-04-30/121.pdf",
        "source_domain": "static.cninfo.com.cn",
        "disclosure_date": "2026-04-30",
        "stock_code": "600406",
        "company_name_hint": "Guodian NARI",
        "period_key": "2025FY",
        "period_end_date": "20251231",
        "announcement_type": "annual_report",
        "source_type": "cninfo_official_pdf",
        "not_for_trading_advice": True,
    }
    candidate.update(overrides)
    return candidate


@pytest.mark.parametrize("marker", ["token", ".env", "tushare_token"])
def test_secret_markers_are_rejected(marker):
    with pytest.raises(ProviderMetricOfficialAnchorError, match="forbidden_marker"):
        assert_no_provider_metric_anchor_forbidden_markers({"outer": [{"inner": marker}]})


@pytest.mark.parametrize(
    "marker",
    [
        "official_verified",
        "official_metric_fact",
        "provider_official_conflict",
        "Report V1",
    ],
)
def test_official_verification_forbidden_markers_are_rejected(marker):
    with pytest.raises(ProviderMetricOfficialAnchorError, match="forbidden_marker"):
        build_provider_metric_official_disclosure_anchor_map(_provider_queue(marker), [_official_candidate()])


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
    with pytest.raises(ProviderMetricOfficialAnchorError, match="forbidden_marker"):
        assert_no_provider_metric_anchor_forbidden_markers({"nested": [marker]})


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
def test_extraction_and_pdf_operation_markers_are_rejected(marker):
    with pytest.raises(ProviderMetricOfficialAnchorError, match="forbidden_marker"):
        assert_no_provider_metric_anchor_forbidden_markers({"nested": [{"marker": marker}]})


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
    with pytest.raises(ProviderMetricOfficialAnchorError, match="forbidden_marker"):
        assert_no_provider_metric_anchor_forbidden_markers({"outer": [{"inner": marker}]})


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
        "正式研报",
        "输出基线",
        "写入fixture",
        "写入accepted manifest",
        "读取token",
        "读取.env",
        "读取tushare_token",
        "下载",
        "解析PDF",
        "PDF解析",
        "表格抽取",
        "指标抽取",
    ],
)
def test_chinese_forbidden_markers_are_rejected(marker):
    with pytest.raises(ProviderMetricOfficialAnchorError, match="forbidden_marker"):
        assert_no_provider_metric_anchor_forbidden_markers({"nested": ["safe", {"marker": marker}]})


def test_url_secret_marker_is_rejected():
    candidate = _official_candidate(source_url="https://static.cninfo.com.cn/finalpage/report.pdf?token=abc")

    with pytest.raises(ProviderMetricOfficialAnchorError, match="forbidden_marker"):
        build_provider_metric_official_disclosure_anchor_map(_provider_queue(), [candidate])


def test_allowed_flags_and_anchor_candidate_status_are_not_false_positives():
    payload = {
        "not_official_verified": True,
        "not_for_trading_advice": True,
        "official_verification_status": "pending_official_verification",
        "anchor_evidence_status": "official_anchor_candidate",
        "source_url": "https://static.cninfo.com.cn/finalpage/2026-04-30/report.pdf",
    }

    assert_no_provider_metric_anchor_forbidden_markers(payload)


def test_source_url_operation_word_is_not_a_false_positive_when_official_url_is_explicit():
    payload = {
        "source_url": "https://static.cninfo.com.cn/download/report.pdf",
        "not_for_trading_advice": True,
    }

    assert_no_provider_metric_anchor_forbidden_markers(payload)


def test_no_secret_value_appears_in_result_or_captured_output(capsys):
    secret_value = "HiddenCredentialValue9876543210ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    queue = _provider_queue()
    queue["debug_payload"] = secret_value
    queue.pop("verification_items")

    anchor_map = build_provider_metric_official_disclosure_anchor_map(queue, [_official_candidate()])
    captured = capsys.readouterr()

    assert "missing_verification_items" in anchor_map["blocked_reasons"]
    assert secret_value not in repr(anchor_map)
    assert secret_value not in captured.out
    assert secret_value not in captured.err
    assert captured.out == ""
    assert captured.err == ""
