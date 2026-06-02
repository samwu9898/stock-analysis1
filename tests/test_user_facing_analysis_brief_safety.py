# -*- coding: utf-8 -*-

from __future__ import annotations

import copy
import json

import pytest

from src.fundamental_skill.research_planning.user_facing_analysis_brief import (
    UserFacingAnalysisBriefError,
    assert_no_user_facing_analysis_brief_forbidden_markers,
    build_user_facing_analysis_brief,
    validate_user_facing_analysis_brief,
)
from tests.test_user_facing_analysis_brief import _brief, _locator_result, _orchestration_result


@pytest.mark.parametrize("marker", ["token", "api_token"])
def test_token_marker_rejected(marker):
    with pytest.raises(UserFacingAnalysisBriefError, match="forbidden marker"):
        assert_no_user_facing_analysis_brief_forbidden_markers({"nested": [{"marker": marker}]})


def test_dotenv_marker_rejected():
    with pytest.raises(UserFacingAnalysisBriefError, match="forbidden marker"):
        assert_no_user_facing_analysis_brief_forbidden_markers({"marker": "read .env file"})


def test_tushare_token_marker_rejected():
    with pytest.raises(UserFacingAnalysisBriefError, match="forbidden marker"):
        assert_no_user_facing_analysis_brief_forbidden_markers({"marker": "tushare_token"})


@pytest.mark.parametrize("marker", ["official_metric_fact", "provider_official_conflict"])
def test_official_fact_and_conflict_markers_rejected(marker):
    with pytest.raises(UserFacingAnalysisBriefError, match="forbidden marker"):
        assert_no_user_facing_analysis_brief_forbidden_markers({"marker": marker})


@pytest.mark.parametrize("marker", ["Report V1", "formal report"])
def test_report_v1_and_formal_report_rejected(marker):
    with pytest.raises(UserFacingAnalysisBriefError, match="forbidden marker"):
        assert_no_user_facing_analysis_brief_forbidden_markers({"marker": marker})


@pytest.mark.parametrize(
    "marker",
    ["accepted manifest write", "output baseline write", "fixture write"],
)
def test_accepted_manifest_output_baseline_fixture_write_rejected(marker):
    with pytest.raises(UserFacingAnalysisBriefError, match="forbidden marker"):
        assert_no_user_facing_analysis_brief_forbidden_markers({"marker": marker})


@pytest.mark.parametrize(
    "marker",
    ["page_number", "snippet", "source_url", "sha256", "cache_path"],
)
def test_locator_trace_markers_rejected_in_user_visible_output(marker):
    brief = _brief()
    mutated = copy.deepcopy(brief)
    mutated["user_visible_sections"][0]["analysis_points"][0][marker] = "leak"

    with pytest.raises(UserFacingAnalysisBriefError, match="forbidden"):
        validate_user_facing_analysis_brief(mutated)


@pytest.mark.parametrize(
    "marker",
    ["OCR", "table extraction", "table extractor", "metric extraction"],
)
def test_ocr_table_and_metric_extraction_markers_rejected(marker):
    with pytest.raises(UserFacingAnalysisBriefError, match="forbidden marker"):
        assert_no_user_facing_analysis_brief_forbidden_markers({"marker": marker})


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
def test_trading_markers_rejected(marker):
    with pytest.raises(UserFacingAnalysisBriefError, match="forbidden marker"):
        assert_no_user_facing_analysis_brief_forbidden_markers({"marker": marker})


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
        "OCR",
        "\u8868\u683c\u62bd\u53d6",
        "\u8868\u683c\u89e3\u6790",
        "\u6307\u6807\u62bd\u53d6",
        "\u5b98\u65b9\u6307\u6807\u4e8b\u5b9e",
        "\u6307\u6807\u6838\u9a8c",
        "\u4e00\u81f4\u6027\u6838\u9a8c",
        "\u884c\u4e1a\u666f\u6c14",
        "\u5b8f\u89c2\u5229\u597d",
        "\u516c\u53f8\u53d7\u76ca",
        "\u6838\u5fc3\u6295\u8d44\u903b\u8f91\u6210\u7acb",
        "\u7b2c\u51e0\u9875",
        "\u9875\u7801",
        "\u539f\u6587\u7247\u6bb5",
        "\u6765\u6e90\u94fe\u63a5",
        "\u54c8\u5e0c",
        "\u7f13\u5b58\u8def\u5f84",
    ],
)
def test_chinese_forbidden_markers_rejected(marker):
    with pytest.raises(UserFacingAnalysisBriefError, match="forbidden marker"):
        assert_no_user_facing_analysis_brief_forbidden_markers({"marker": marker})


def test_controlled_policy_keys_and_boundary_phrase_are_allowed():
    assert_no_user_facing_analysis_brief_forbidden_markers(
        {
            "not_for_trading_advice": True,
            "not_official_verified": True,
            "official_verified_count": 0,
            "boundary": "\u5b98\u65b9\u6307\u6807\u6838\u9a8c\u5c1a\u672a\u5b8c\u6210",
        }
    )


def test_backend_locator_page_and_snippet_cannot_leak_into_markdown_preview():
    locator_result = _locator_result()
    brief = build_user_facing_analysis_brief(
        {
            "orchestration_result": _orchestration_result(),
            "locator_result": locator_result,
        }
    )
    preview = brief["markdown_preview"]

    assert "safe locator hint" not in preview
    assert "page_number" not in preview
    assert "snippet" not in preview
    assert "source_url" not in preview
    assert "sha256" not in preview
    assert "cache_path" not in preview


def test_backend_grounding_summary_rejects_raw_trace_key():
    brief = _brief()
    mutated = copy.deepcopy(brief)
    mutated["backend_grounding_summary"]["source_url"] = "https://example.com"

    with pytest.raises(UserFacingAnalysisBriefError, match="unsupported|forbidden"):
        validate_user_facing_analysis_brief(mutated)


def test_no_token_appears_in_result_or_captured_output(capsys):
    brief = _brief()
    captured = capsys.readouterr()
    serialized = json.dumps(brief, ensure_ascii=False).casefold()

    assert "token" not in captured.out.casefold()
    assert "token" not in captured.err.casefold()
    assert "token" not in serialized
