# -*- coding: utf-8 -*-

from __future__ import annotations

import json

import pytest

from src.fundamental_skill.research_planning.controlled_real_tushare_professional_compact_brief_pilot import (
    ControlledRealTushareProfessionalCompactBriefPilotError,
    assert_no_controlled_real_tushare_professional_brief_forbidden_markers,
    assert_no_user_visible_engineering_labels,
    build_controlled_real_tushare_professional_compact_brief_result,
)
from tests.test_controlled_real_tushare_professional_compact_brief_pilot import (
    _FakeFinancialClient,
    _build,
    _request,
)


def _assert_rejected(marker):
    with pytest.raises(ControlledRealTushareProfessionalCompactBriefPilotError):
        assert_no_controlled_real_tushare_professional_brief_forbidden_markers(
            {"note": marker}
        )


@pytest.mark.parametrize(
    "marker",
    [
        "token",
        ".env",
        "tushare_token",
        "official_metric_fact",
        "provider_official_conflict",
        "Report V1 artifact",
        "HTML artifact",
        "accepted manifest write",
        "output baseline write",
        "fixture write",
        "PDF parser",
        "OCR",
        "table extraction",
        "table extractor",
        "metric extraction",
        "provider-official reconciliation",
        "verified_fact",
        "page_number",
        "snippet",
        "source_url",
        "sha256",
        "cache_path",
    ],
)
def test_english_forbidden_markers_rejected(marker):
    _assert_rejected(marker)


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
        "买入",
        "卖出",
        "持有",
        "目标价",
        "仓位",
        "组合",
        "技术信号",
        "投资建议",
    ],
)
def test_trading_or_advice_markers_rejected(marker):
    _assert_rejected(marker)


@pytest.mark.parametrize(
    "phrase",
    [
        "buy recommendation",
        "sell signal",
        "hold position",
        "buy signal",
        "sell recommendation",
    ],
)
def test_english_trading_phrases_rejected(phrase):
    _assert_rejected(phrase)


@pytest.mark.parametrize("phrase", ["threshold", "shareholder", "withholding"])
def test_non_trading_words_are_not_rejected_by_word_boundaries(phrase):
    assert_no_controlled_real_tushare_professional_brief_forbidden_markers(
        {"note": phrase}
    )


@pytest.mark.parametrize(
    "marker",
    [
        "正式研报",
        "输出基线",
        "写入fixture",
        "写入accepted manifest",
        "读取token",
        "读取.env",
        "读取tushare_token",
        "表格抽取",
        "表格解析",
        "指标抽取",
        "官方指标事实",
        "指标核验",
        "一致性核验",
        "行业景气",
        "宏观利好",
        "公司受益",
        "核心投资逻辑成立",
        "第几页",
        "页码",
        "原文片段",
        "来源链接",
        "哈希",
        "缓存路径",
    ],
)
def test_chinese_forbidden_markers_rejected(marker):
    _assert_rejected(marker)


@pytest.mark.parametrize(
    "label",
    [
        "provider_candidate",
        "pending_official_verification",
        "pending verification",
        "official verification",
        "official_verified_count",
        "data gap",
        "evidence locator",
        "anchor map",
        "artifact cached",
        "reconciliation",
        "provider vs official",
        "待核验",
        "数据缺口",
        "推理",
        "官方核验",
        "尚未完成官方核验",
        "provider",
        "候选数据",
        "证据状态",
        "口径一致性",
        "用户自行",
        "自行判断",
        "自行跟踪",
        "需要用户",
        "建议用户",
    ],
)
def test_user_visible_engineering_labels_rejected(label):
    with pytest.raises(ControlledRealTushareProfessionalCompactBriefPilotError):
        assert_no_user_visible_engineering_labels({"professional_compact_brief": label})


def test_token_value_not_echoed_in_blocked_result_or_captured_output(capsys):
    secret = "S3cr3tValueThatShouldStayHidden123456789"
    result = build_controlled_real_tushare_professional_compact_brief_result(
        _request(),
        tushare_client=_FakeFinancialClient(fail_with="provider failed " + secret),
    )
    captured = capsys.readouterr()

    serialized = json.dumps(result, ensure_ascii=False)
    assert secret not in serialized
    assert secret not in captured.out
    assert secret not in captured.err
    assert result["professional_compact_brief"] is None


def test_backend_trace_cannot_leak_into_professional_compact_brief():
    brief = _build()["professional_compact_brief"]
    serialized = json.dumps(brief, ensure_ascii=False)

    for forbidden in ("backend_grounding_summary", "page_number", "snippet", "source_url", "sha256", "cache_path"):
        assert forbidden not in serialized


def test_no_token_appears_in_ready_result_or_captured_output(capsys):
    result = _build()
    captured = capsys.readouterr()
    serialized = json.dumps(result, ensure_ascii=False).casefold()

    assert "token" not in serialized
    assert "token" not in captured.out.casefold()
    assert "token" not in captured.err.casefold()


def test_output_fixture_manifest_path_keys_rejected():
    for key in ("output_path", "fixture_path", "accepted_manifest_path"):
        request = _request()
        request[key] = "blocked"
        with pytest.raises(ControlledRealTushareProfessionalCompactBriefPilotError):
            build_controlled_real_tushare_professional_compact_brief_result(
                request,
                tushare_client=_FakeFinancialClient(),
            )


def test_raw_file_or_backend_trace_request_fields_rejected():
    for key, value in (
        ("raw_tushare_provider_result", {"provider": "Tushare"}),
        ("raw_provider_queue", []),
        ("pdf_bytes", b"%PDF-1.7"),
        ("source_url", "https://example.invalid/report.pdf"),
    ):
        request = _request()
        request[key] = value
        with pytest.raises(ControlledRealTushareProfessionalCompactBriefPilotError):
            build_controlled_real_tushare_professional_compact_brief_result(
                request,
                tushare_client=_FakeFinancialClient(),
            )


def test_internal_candidate_statuses_are_not_promoted_to_official_fact():
    result = _build()
    bundle = result["provider_candidate_bundle"]
    serialized = json.dumps(bundle, ensure_ascii=False)

    assert bundle["official_verified_count"] == 0
    assert "official_metric_fact" not in serialized
    assert "provider_official_conflict" not in serialized
    assert "provider-official reconciliation" not in serialized
    allowed_removed = serialized.replace("not_official_verified", "").replace(
        "official_verified_count",
        "",
    )
    assert "official_verified" not in allowed_removed


def test_report_html_and_output_artifacts_are_not_generated():
    result = _build()
    serialized = json.dumps(result["professional_compact_brief"], ensure_ascii=False)

    assert result["skill_wrapper_response"]["readiness"]["has_report_v1_artifact"] is False
    assert result["skill_wrapper_response"]["readiness"]["has_html_artifact"] is False
    assert "Report V1 artifact" not in serialized
    assert "HTML artifact" not in serialized
    assert "output artifact path" not in serialized
