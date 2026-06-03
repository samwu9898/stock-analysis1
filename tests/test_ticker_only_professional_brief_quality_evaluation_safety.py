# -*- coding: utf-8 -*-

from __future__ import annotations

import json

import pytest

from src.fundamental_skill.research_planning.ticker_only_professional_brief_quality_evaluation import (
    TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_EVALUATION_REQUEST_SCHEMA_VERSION,
    TickerOnlyProfessionalBriefQualityEvaluationError,
    assert_no_frontstage_engineering_labels,
    assert_no_quality_evaluation_forbidden_markers,
    build_ticker_only_professional_brief_quality_evaluation,
)


def _request(**overrides):
    request = {
        "schema_version": (
            TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_EVALUATION_REQUEST_SCHEMA_VERSION
        ),
        "sample_ids": ["baseline_600406_like"],
        "not_for_trading_advice": True,
    }
    request.update(overrides)
    return request


@pytest.mark.parametrize(
    "value",
    [
        {"token": "secret"},
        "token",
        "sk-1234567890abcdef",
        "Bearer abcdefghijklmnop",
    ],
)
def test_token_marker_rejected(value):
    with pytest.raises(TickerOnlyProfessionalBriefQualityEvaluationError):
        assert_no_quality_evaluation_forbidden_markers(value)


@pytest.mark.parametrize("value", [".env", {"env_file": ".env"}])
def test_env_marker_rejected(value):
    with pytest.raises(TickerOnlyProfessionalBriefQualityEvaluationError):
        assert_no_quality_evaluation_forbidden_markers(value)


@pytest.mark.parametrize(
    "value",
    ["tushare_token", {"tushare_token_path": "tushare_token.txt"}],
)
def test_tushare_token_marker_rejected(value):
    with pytest.raises(TickerOnlyProfessionalBriefQualityEvaluationError):
        assert_no_quality_evaluation_forbidden_markers(value)


@pytest.mark.parametrize(
    "value",
    [
        {"raw_provider_rows": [{"metric": "revenue"}]},
        "raw provider rows",
        {"raw_provider_bundle": {"x": 1}},
    ],
)
def test_raw_provider_rows_rejected(value):
    with pytest.raises(TickerOnlyProfessionalBriefQualityEvaluationError):
        assert_no_quality_evaluation_forbidden_markers(value)


@pytest.mark.parametrize(
    "value",
    [{"raw_provider_queue": []}, "raw provider queue"],
)
def test_raw_provider_queue_rejected(value):
    with pytest.raises(TickerOnlyProfessionalBriefQualityEvaluationError):
        assert_no_quality_evaluation_forbidden_markers(value)


@pytest.mark.parametrize(
    "value",
    [{"candidate_items": []}, {"provider_candidate_bundle": {}}, "provider_candidate"],
)
def test_candidate_items_rejected_from_evaluation_result(value):
    with pytest.raises(TickerOnlyProfessionalBriefQualityEvaluationError):
        assert_no_quality_evaluation_forbidden_markers(value)


@pytest.mark.parametrize(
    "value",
    [
        {"source_url": "https://example.test"},
        {"page_number": 1},
        {"snippet": "source text"},
        {"sha256": "abc"},
        {"cache_path": "cache/file.pdf"},
    ],
)
def test_source_locator_trace_markers_rejected(value):
    with pytest.raises(TickerOnlyProfessionalBriefQualityEvaluationError):
        assert_no_quality_evaluation_forbidden_markers(value)


@pytest.mark.parametrize(
    "value",
    [
        "output/result.json",
        "fixtures/result.json",
        "accepted manifest path",
        {"accepted_manifest": "accepted_manifest.json"},
    ],
)
def test_output_fixture_and_manifest_paths_rejected(value):
    with pytest.raises(TickerOnlyProfessionalBriefQualityEvaluationError):
        assert_no_quality_evaluation_forbidden_markers(value)


@pytest.mark.parametrize(
    "value",
    [
        "provider_candidate",
        "pending verification",
        "pending_official_verification",
        "official verification",
        "provider vs official",
    ],
)
def test_provider_candidate_pending_verification_rejected_from_frontstage_preview(value):
    with pytest.raises(TickerOnlyProfessionalBriefQualityEvaluationError):
        assert_no_frontstage_engineering_labels(value)


@pytest.mark.parametrize("value", ["待核验", "数据缺口", "推理"])
def test_chinese_engineering_labels_rejected(value):
    with pytest.raises(TickerOnlyProfessionalBriefQualityEvaluationError):
        assert_no_frontstage_engineering_labels(value)


@pytest.mark.parametrize(
    "value",
    ["用户自行", "自行判断", "自行跟踪", "需要用户", "建议用户"],
)
def test_user_responsibility_shift_phrases_rejected(value):
    with pytest.raises(TickerOnlyProfessionalBriefQualityEvaluationError):
        assert_no_quality_evaluation_forbidden_markers(value)


@pytest.mark.parametrize(
    "value",
    [
        "buy",
        "sell",
        "hold",
        "target price",
        "portfolio",
        "position",
        "technical signal",
        "买入",
        "卖出",
        "持有",
        "目标价",
        "仓位",
        "技术信号",
    ],
)
def test_market_action_language_rejected(value):
    with pytest.raises(TickerOnlyProfessionalBriefQualityEvaluationError):
        assert_no_quality_evaluation_forbidden_markers(value)


@pytest.mark.parametrize(
    "value",
    [
        "official_metric_fact",
        "provider_official_conflict",
        "provider-official reconciliation",
        "reconciliation",
    ],
)
def test_official_metric_fact_conflict_and_reconciliation_rejected(value):
    with pytest.raises(TickerOnlyProfessionalBriefQualityEvaluationError):
        assert_no_quality_evaluation_forbidden_markers(value)


@pytest.mark.parametrize(
    "value",
    ["Report V1 artifact", "HTML artifact", "report_v1_artifact", "html_artifact"],
)
def test_report_v1_and_html_artifacts_rejected(value):
    with pytest.raises(TickerOnlyProfessionalBriefQualityEvaluationError):
        assert_no_quality_evaluation_forbidden_markers(value)


def test_no_token_appears_in_result_or_captured_output(monkeypatch, capsys):
    secret = "S3cr3tValueThatShouldStayHidden123456789"
    monkeypatch.setenv("TUSHARE_" + "TOKEN", secret)

    result = build_ticker_only_professional_brief_quality_evaluation(_request())
    captured = capsys.readouterr()
    serialized = json.dumps(result, ensure_ascii=False)

    assert secret not in serialized
    assert secret not in captured.out
    assert secret not in captured.err


def test_no_backend_trace_appears_in_professional_preview():
    result = build_ticker_only_professional_brief_quality_evaluation(_request())
    preview = result["sample_results"][0]["professional_compact_brief_preview"]
    serialized = json.dumps(preview, ensure_ascii=False)

    for forbidden in (
        "backend_trace",
        "backend_grounding_summary",
        "candidate_items",
        "source_url",
        "page_number",
        "snippet",
        "sha256",
        "cache_path",
    ):
        assert forbidden not in serialized
