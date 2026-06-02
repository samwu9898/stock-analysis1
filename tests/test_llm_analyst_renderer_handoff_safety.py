# -*- coding: utf-8 -*-

from __future__ import annotations

import copy
import json

import pytest

from src.fundamental_skill.research_planning.llm_analyst_renderer_handoff import (
    LLM_ANALYST_RENDERER_OUTPUT_SCHEMA_VERSION,
    LLMAnalystRendererHandoffError,
    assert_no_llm_handoff_forbidden_markers,
    assert_no_user_visible_engineering_labels,
    build_model_facing_analyst_context,
    fake_llm_analyst_renderer,
    render_professional_brief_with_fake_llm,
    validate_llm_analyst_renderer_output,
)
from src.fundamental_skill.research_planning.professional_compact_brief_quality import (
    build_professional_analyst_context,
)
from tests.test_controlled_real_tushare_professional_compact_brief_pilot import _build


_BASE_CONTEXT = None


def _context():
    global _BASE_CONTEXT
    if _BASE_CONTEXT is None:
        result = _build()
        _BASE_CONTEXT = build_professional_analyst_context(
            result["provider_candidate_bundle"],
            internal_analysis_brief=result["internal_analysis_brief"],
        )
    return copy.deepcopy(_BASE_CONTEXT)


def _model_context():
    return build_model_facing_analyst_context(_context())


def _assert_marker_rejected(marker):
    with pytest.raises(LLMAnalystRendererHandoffError):
        assert_no_llm_handoff_forbidden_markers({"note": marker})


def _unsafe_llm_output(view):
    return {
        "schema_version": LLM_ANALYST_RENDERER_OUTPUT_SCHEMA_VERSION,
        "sections": {
            key: view
            for key in (
                "overall_view",
                "business_view",
                "financial_view",
                "operating_quality_view",
                "industry_macro_view",
                "risk_view",
            )
        },
        "key_variables": [
            "收入与利润同步性",
            "经营现金流与利润匹配度",
            "应收账款回款效率",
            "利润率结构",
            "资产负债结构",
        ],
        "conclusion_boundary": "结论边界聚焦基本面质量和经营韧性，不展开估值区间或操作动作。",
        "source_note": "数据来源：Tushare。",
        "not_for_trading_advice": True,
    }


@pytest.mark.parametrize("marker", ["token", "sk-Abcdefgh12345678"])
def test_token_marker_rejected(marker):
    _assert_marker_rejected(marker)


def test_env_marker_rejected():
    _assert_marker_rejected(".env")


def test_tushare_token_marker_rejected():
    _assert_marker_rejected("tushare_token")


def test_raw_provider_queue_rejected():
    _assert_marker_rejected("raw provider queue")


def test_raw_http_rejected():
    _assert_marker_rejected("raw HTTP response")


@pytest.mark.parametrize(
    "marker",
    ["source_url", "page_number", "snippet", "sha256", "cache_path"],
)
def test_locator_markers_rejected(marker):
    _assert_marker_rejected(marker)


@pytest.mark.parametrize(
    "marker",
    ["output path", "fixture path", "accepted manifest path"],
)
def test_artifact_path_markers_rejected(marker):
    _assert_marker_rejected(marker)


@pytest.mark.parametrize(
    "label",
    [
        "provider_candidate",
        "pending_official_verification",
        "pending verification",
    ],
)
def test_provider_candidate_or_pending_labels_rejected_from_user_output(label):
    with pytest.raises(LLMAnalystRendererHandoffError):
        assert_no_user_visible_engineering_labels({"view": label})


@pytest.mark.parametrize("label", ["待核验", "数据缺口", "推理"])
def test_engineering_cjk_labels_rejected_from_renderer_output(label):
    with pytest.raises(LLMAnalystRendererHandoffError):
        validate_llm_analyst_renderer_output(_unsafe_llm_output(label))


@pytest.mark.parametrize(
    "phrase",
    ["用户自行", "自行判断", "自行跟踪", "需要用户", "建议用户"],
)
def test_user_responsibility_shifting_phrases_rejected(phrase):
    with pytest.raises(LLMAnalystRendererHandoffError):
        validate_llm_analyst_renderer_output(_unsafe_llm_output(phrase))


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
        "买入",
        "卖出",
        "持有",
        "目标价",
        "仓位",
        "技术信号",
    ],
)
def test_trading_advice_markers_rejected(marker):
    _assert_marker_rejected(marker)


@pytest.mark.parametrize(
    "marker",
    [
        "official_metric_fact",
        "provider_official_conflict",
        "provider vs official",
        "reconciliation",
    ],
)
def test_official_fact_or_reconciliation_markers_rejected(marker):
    _assert_marker_rejected(marker)


@pytest.mark.parametrize("marker", ["Report V1 artifact", "HTML artifact"])
def test_report_v1_or_html_artifact_markers_rejected(marker):
    _assert_marker_rejected(marker)


def test_fake_renderer_cannot_leak_backend_trace():
    unsafe_context = _model_context()
    unsafe_context["risk_flags"].append(
        "backend trace page_number snippet source_url sha256 cache_path"
    )

    with pytest.raises(LLMAnalystRendererHandoffError):
        fake_llm_analyst_renderer(unsafe_context)


def test_fake_renderer_cannot_return_trading_advice():
    with pytest.raises(LLMAnalystRendererHandoffError):
        validate_llm_analyst_renderer_output(
            _unsafe_llm_output("buy recommendation with target price and position signal")
        )


def test_no_token_appears_in_result_or_captured_output(capsys):
    brief = render_professional_brief_with_fake_llm(_context())
    captured = capsys.readouterr()
    serialized = json.dumps(brief, ensure_ascii=False).casefold()

    assert "token" not in serialized
    assert "token" not in captured.out.casefold()
    assert "token" not in captured.err.casefold()
