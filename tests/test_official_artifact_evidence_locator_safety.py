# -*- coding: utf-8 -*-

from __future__ import annotations

import hashlib

import pytest

from src.fundamental_skill.data_verification.official_artifact_evidence_locator import (
    REASON_FORBIDDEN_MARKER_DETECTED,
    REASON_METRIC_LOCATOR_KEYWORD_FORBIDDEN,
    OfficialArtifactEvidenceLocatorSafetyError,
    assert_no_official_artifact_evidence_locator_forbidden_markers,
    build_official_artifact_evidence_locator,
)


PDF_BYTES = b"%PDF-1.7\nfake official pdf bytes\n%%EOF"


def _artifact_cache(marker=None):
    payload = {
        "schema_version": "official_disclosure_artifact_cache.v1",
        "provider": "Tushare",
        "ts_code": "600406.SH",
        "stock_code": "600406",
        "company_name_hint": "Guodian NARI",
        "artifact_items": [
            {
                "schema_version": "official_disclosure_artifact_cache_item.v1",
                "artifact_id": "artifact_600406_2026q1",
                "source_title": "Guodian NARI 2026 Q1 Report",
                "source_url": "https://static.cninfo.com.cn/finalpage/2026-04-30/report.pdf",
                "source_domain": "static.cninfo.com.cn",
                "final_url": "https://static.cninfo.com.cn/finalpage/2026-04-30/report.pdf",
                "final_domain": "static.cninfo.com.cn",
                "disclosure_date": "2026-04-30",
                "stock_code": "600406",
                "company_name_hint": "Guodian NARI",
                "period_key": "2026Q1",
                "period_end_date": "20260331",
                "announcement_type": "quarterly_report",
                "source_type": "cninfo_official_pdf",
                "anchor_evidence_status": "official_anchor_candidate",
                "artifact_status": "cached",
                "download_status": "success",
                "cache_path": "C:/safe/cache/report.pdf",
                "file_size_bytes": len(PDF_BYTES),
                "sha256": hashlib.sha256(PDF_BYTES).hexdigest(),
                "content_type": "application/pdf",
                "source_lineage": {
                    "schema_version": "official_artifact_source_lineage.v1",
                    "source_anchor_status": "matched",
                    "source_anchor_url": "https://static.cninfo.com.cn/finalpage/2026-04-30/report.pdf",
                    "source_anchor_domain": "static.cninfo.com.cn",
                    "source_anchor_title": "Guodian NARI 2026 Q1 Report",
                    "source_disclosure_date": "2026-04-30",
                    "anchor_map_schema_version": "provider_metric_official_disclosure_anchor_map.v1",
                    "anchor_item_metric_keys": [],
                    "not_official_verified": True,
                    "not_for_trading_advice": True,
                },
                "not_official_verified": True,
                "not_for_trading_advice": True,
                "caveats": [],
            }
        ],
        "skipped_items": [],
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
    with pytest.raises(OfficialArtifactEvidenceLocatorSafetyError):
        assert_no_official_artifact_evidence_locator_forbidden_markers({"outer": [{"inner": marker}]})


@pytest.mark.parametrize(
    "marker",
    [
        "official_verified",
        "official_metric_fact",
        "provider_official_conflict",
        "verified_metric",
        "official_value",
        "metric_value",
        "reconciliation_status",
    ],
)
def test_official_fact_conflict_and_value_markers_are_rejected(marker):
    with pytest.raises(OfficialArtifactEvidenceLocatorSafetyError):
        assert_no_official_artifact_evidence_locator_forbidden_markers({"nested": [marker]})


@pytest.mark.parametrize("marker", ["Report V1", "formal report"])
def test_report_markers_are_rejected(marker):
    with pytest.raises(OfficialArtifactEvidenceLocatorSafetyError):
        assert_no_official_artifact_evidence_locator_forbidden_markers({"nested": [marker]})


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
    with pytest.raises(OfficialArtifactEvidenceLocatorSafetyError):
        assert_no_official_artifact_evidence_locator_forbidden_markers({"nested": [marker]})


@pytest.mark.parametrize("marker", ["OCR", "table extraction", "table extractor", "metric extraction"])
def test_pdf_forbidden_operation_markers_are_rejected(marker):
    with pytest.raises(OfficialArtifactEvidenceLocatorSafetyError):
        assert_no_official_artifact_evidence_locator_forbidden_markers({"nested": [{"marker": marker}]})


@pytest.mark.parametrize(
    "marker",
    [
        "revenue amount",
        "net profit amount",
        "operating cash flow amount",
        "EPS extraction",
        "revenue_amount",
        "net_profit_amount",
        "operating_cash_flow_amount",
        "eps_extraction",
    ],
)
def test_metric_amount_intent_markers_are_rejected(marker):
    with pytest.raises(OfficialArtifactEvidenceLocatorSafetyError):
        assert_no_official_artifact_evidence_locator_forbidden_markers({"nested": [{"marker": marker}]})


@pytest.mark.parametrize(
    "keyword",
    ["revenue", "营业收入", "净利润", "经营现金流", "每股收益"],
)
def test_metric_locator_keywords_in_config_are_rejected(keyword):
    result = build_official_artifact_evidence_locator(
        _artifact_cache(),
        locator_config={"keywords": [keyword]},
    )

    assert result["blocked_reasons"] == [REASON_METRIC_LOCATOR_KEYWORD_FORBIDDEN]


def test_metric_locator_section_heading_is_rejected():
    result = build_official_artifact_evidence_locator(
        _artifact_cache(),
        locator_config={"section_headings": [("custom_metric", "net profit")]},
    )

    assert result["blocked_reasons"] == [REASON_METRIC_LOCATOR_KEYWORD_FORBIDDEN]


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
def test_trading_and_position_markers_are_rejected(marker):
    with pytest.raises(OfficialArtifactEvidenceLocatorSafetyError):
        assert_no_official_artifact_evidence_locator_forbidden_markers({"outer": [{"inner": marker}]})


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
        "OCR",
        "表格抽取",
        "表格解析",
        "指标抽取",
        "营业收入数值",
        "归母净利润数值",
        "经营现金流数值",
        "每股收益抽取",
        "官方指标事实",
        "指标核验",
        "一致性核验",
    ],
)
def test_chinese_forbidden_markers_are_rejected(marker):
    with pytest.raises(OfficialArtifactEvidenceLocatorSafetyError):
        assert_no_official_artifact_evidence_locator_forbidden_markers({"nested": ["safe", {"marker": marker}]})


def test_allowed_not_official_verified_flag_is_not_false_positive():
    payload = {
        "not_official_verified": True,
        "not_for_trading_advice": True,
        "source_url": "https://static.cninfo.com.cn/finalpage/2026-04-30/report.pdf",
        "extraction_scope": "locator_text_layer_only",
    }

    assert_no_official_artifact_evidence_locator_forbidden_markers(payload)


def test_build_fail_closed_for_forbidden_marker_without_echoing_secret(capsys):
    secret_value = "token SuperSecretShouldNotEcho987654321"

    result = build_official_artifact_evidence_locator(_artifact_cache(marker=secret_value))
    captured = capsys.readouterr()

    assert result["blocked_reasons"] == [REASON_FORBIDDEN_MARKER_DETECTED]
    assert "SuperSecretShouldNotEcho987654321" not in repr(result)
    assert "SuperSecretShouldNotEcho987654321" not in captured.out
    assert "SuperSecretShouldNotEcho987654321" not in captured.err
    assert captured.out == ""
    assert captured.err == ""


def test_no_token_appears_in_result_or_captured_output(capsys):
    result = build_official_artifact_evidence_locator(_artifact_cache(marker="tushare_token=Hidden123"))
    captured = capsys.readouterr()

    assert result["blocked_reasons"] == [REASON_FORBIDDEN_MARKER_DETECTED]
    assert "Hidden123" not in repr(result)
    assert "Hidden123" not in captured.out
    assert "Hidden123" not in captured.err
    assert captured.out == ""
    assert captured.err == ""
