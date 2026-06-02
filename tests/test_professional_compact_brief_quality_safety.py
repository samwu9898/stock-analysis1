# -*- coding: utf-8 -*-

from __future__ import annotations

import json

import pytest

from src.fundamental_skill.research_planning.professional_compact_brief_quality import (
    PROFESSIONAL_ANALYST_RENDERER_OUTPUT_SCHEMA_VERSION,
    ProfessionalCompactBriefQualityError,
    assert_no_professional_brief_quality_forbidden_markers,
    assert_no_user_visible_engineering_labels,
    build_professional_analyst_context,
    render_professional_compact_brief_from_context,
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
    return _BASE_CONTEXT


def _assert_marker_rejected(marker):
    with pytest.raises(ProfessionalCompactBriefQualityError):
        assert_no_professional_brief_quality_forbidden_markers({"note": marker})


@pytest.mark.parametrize(
    "marker",
    [
        "token",
        ".env",
        "tushare_token",
    ],
)
def test_secret_or_token_markers_rejected(marker):
    _assert_marker_rejected(marker)


@pytest.mark.parametrize(
    "marker",
    [
        "backend trace",
        "backend_grounding_summary",
        "page_number",
        "snippet",
        "source_url",
        "sha256",
        "cache_path",
    ],
)
def test_backend_trace_markers_rejected(marker):
    _assert_marker_rejected(marker)


@pytest.mark.parametrize(
    "label",
    [
        "provider_candidate",
        "pending official verification",
        "pending_official_verification",
        "official verification",
        "待核验",
        "数据缺口",
        "推理",
    ],
)
def test_provider_or_pending_verification_labels_rejected(label):
    with pytest.raises(ProfessionalCompactBriefQualityError):
        assert_no_user_visible_engineering_labels({"view": label})


@pytest.mark.parametrize(
    "phrase",
    [
        "用户自行",
        "自行判断",
        "自行跟踪",
        "需要用户",
        "建议用户",
    ],
)
def test_user_responsibility_shifting_phrases_rejected(phrase):
    with pytest.raises(ProfessionalCompactBriefQualityError):
        assert_no_user_visible_engineering_labels({"view": phrase})


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
        "buy recommendation",
        "sell signal",
        "买入",
        "卖出",
        "持有",
        "目标价",
        "仓位",
        "技术信号",
        "投资建议",
    ],
)
def test_trading_advice_markers_rejected(marker):
    _assert_marker_rejected(marker)


@pytest.mark.parametrize("phrase", ["threshold", "shareholder", "withholding"])
def test_non_trading_words_are_not_rejected_by_word_boundaries(phrase):
    assert_no_professional_brief_quality_forbidden_markers({"note": phrase})


@pytest.mark.parametrize(
    "marker",
    [
        "official_metric_fact",
        "provider_official_conflict",
        "provider-official reconciliation",
        "provider vs official",
        "reconciliation",
    ],
)
def test_official_fact_or_reconciliation_markers_rejected(marker):
    _assert_marker_rejected(marker)


@pytest.mark.parametrize(
    "marker",
    [
        "Report V1 artifact",
        "HTML artifact",
        "output artifact path",
        "output write",
        "fixture write",
        "accepted manifest write",
        "manifest write",
    ],
)
def test_artifact_or_write_markers_rejected(marker):
    _assert_marker_rejected(marker)


def _unsafe_renderer_output(view):
    return {
        "schema_version": PROFESSIONAL_ANALYST_RENDERER_OUTPUT_SCHEMA_VERSION,
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
        "not_for_trading_advice": True,
    }


def test_fake_renderer_cannot_leak_backend_trace():
    def renderer(_context):
        return _unsafe_renderer_output(
            "backend trace page_number snippet source_url sha256 cache_path"
        )

    with pytest.raises(ProfessionalCompactBriefQualityError):
        render_professional_compact_brief_from_context(
            _context(),
            analyst_renderer=renderer,
        )


def test_fake_renderer_cannot_return_trading_advice():
    def renderer(_context):
        return _unsafe_renderer_output(
            "buy recommendation with target price and position signal"
        )

    with pytest.raises(ProfessionalCompactBriefQualityError):
        render_professional_compact_brief_from_context(
            _context(),
            analyst_renderer=renderer,
        )


def test_no_token_appears_in_result_or_captured_output(capsys):
    brief = render_professional_compact_brief_from_context(_context())
    captured = capsys.readouterr()
    serialized = json.dumps(brief, ensure_ascii=False).casefold()

    assert "token" not in serialized
    assert "token" not in captured.out.casefold()
    assert "token" not in captured.err.casefold()
