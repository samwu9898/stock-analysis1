# -*- coding: utf-8 -*-

from __future__ import annotations

import json

import pytest

from src.fundamental_skill.research_planning.live_evidence_aware_research_pack_vertical_slice import (
    assert_no_live_research_pack_forbidden_markers,
    build_live_evidence_aware_research_pack_vertical_slice,
    validate_live_evidence_aware_research_pack_vertical_slice,
)
from tests.test_live_evidence_aware_research_pack_vertical_slice import _sample_components


def _vertical_slice():
    return build_live_evidence_aware_research_pack_vertical_slice(_sample_components())


def _section(vertical_slice, section_id):
    return next(section for section in vertical_slice["sections"] if section["section_id"] == section_id)


@pytest.mark.parametrize("marker", ["token", "api_token"])
def test_token_marker_rejected(marker):
    with pytest.raises(ValueError, match="forbidden marker"):
        assert_no_live_research_pack_forbidden_markers({"nested": [{"marker": marker}]})


def test_dotenv_marker_rejected():
    with pytest.raises(ValueError, match="forbidden marker"):
        assert_no_live_research_pack_forbidden_markers({"marker": "read .env file"})


def test_tushare_token_marker_rejected():
    with pytest.raises(ValueError, match="forbidden marker"):
        assert_no_live_research_pack_forbidden_markers({"marker": "tushare_token"})


@pytest.mark.parametrize("marker", ["official_metric_fact", "provider_official_conflict"])
def test_forbidden_official_fact_and_conflict_markers_rejected(marker):
    with pytest.raises(ValueError, match="forbidden marker"):
        assert_no_live_research_pack_forbidden_markers({"marker": marker})


@pytest.mark.parametrize("marker", ["Report V1", "formal report"])
def test_report_v1_and_formal_report_markers_rejected(marker):
    with pytest.raises(ValueError, match="forbidden marker"):
        assert_no_live_research_pack_forbidden_markers({"marker": marker})


@pytest.mark.parametrize(
    "marker",
    [
        "accepted manifest write",
        "output baseline write",
        "fixture write",
    ],
)
def test_accepted_manifest_output_baseline_fixture_write_markers_rejected(marker):
    with pytest.raises(ValueError, match="forbidden marker"):
        assert_no_live_research_pack_forbidden_markers({"nested": [{"marker": marker}]})


@pytest.mark.parametrize(
    "marker",
    [
        "parse PDF",
        "PDF parser",
        "table extractor",
        "metric extraction",
    ],
)
def test_pdf_parser_table_and_metric_extraction_markers_rejected(marker):
    with pytest.raises(ValueError, match="forbidden marker"):
        assert_no_live_research_pack_forbidden_markers({"marker": marker})


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
def test_trading_and_advice_markers_rejected(marker):
    with pytest.raises(ValueError, match="forbidden marker"):
        assert_no_live_research_pack_forbidden_markers({"marker": marker})


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
        "\u884c\u4e1a\u666f\u6c14",
        "\u5b8f\u89c2\u5229\u597d",
        "\u516c\u53f8\u53d7\u76ca",
        "\u6838\u5fc3\u6295\u8d44\u903b\u8f91\u6210\u7acb",
    ],
)
def test_chinese_forbidden_markers_rejected(marker):
    with pytest.raises(ValueError, match="forbidden marker"):
        assert_no_live_research_pack_forbidden_markers({"marker": marker})


def test_controlled_disclaimer_is_allowed():
    assert_no_live_research_pack_forbidden_markers("这不是正式研报 / 不是投资建议")


def test_artifact_cached_cannot_become_official_verified():
    vertical_slice = _vertical_slice()
    section = _section(vertical_slice, "official_anchor_and_artifact_status")
    artifact = next(
        item for item in section["evidence_items"] if item.get("item_id") == "artifact_cache_metadata"
    )
    artifact["artifact_cache_metadata"][0]["artifact_evidence_status"] = "official_verified"

    with pytest.raises(ValueError, match="official_verified"):
        validate_live_evidence_aware_research_pack_vertical_slice(vertical_slice)


def test_official_anchor_matched_cannot_become_official_verified():
    vertical_slice = _vertical_slice()
    section = _section(vertical_slice, "official_anchor_and_artifact_status")
    anchor = next(item for item in section["evidence_items"] if item.get("item_id") == "anchor_items")
    anchor["anchor_items"][0]["current_evidence_status"] = "official_verified"

    with pytest.raises(ValueError, match="official_verified"):
        validate_live_evidence_aware_research_pack_vertical_slice(vertical_slice)


def test_provider_candidate_cannot_become_official_verified():
    vertical_slice = _vertical_slice()
    section = _section(vertical_slice, "financial_candidate_summary")
    metrics = next(
        item for item in section["evidence_items"] if item.get("item_id") == "metric_candidate_statuses"
    )
    metrics["metric_candidates"][0]["current_evidence_status"] = "official_verified"

    with pytest.raises(ValueError, match="official_verified"):
        validate_live_evidence_aware_research_pack_vertical_slice(vertical_slice)


def test_no_token_appears_in_result_or_captured_output(capsys):
    vertical_slice = _vertical_slice()
    captured = capsys.readouterr()
    serialized = json.dumps(vertical_slice, ensure_ascii=False).casefold()

    assert "token" not in captured.out.casefold()
    assert "token" not in captured.err.casefold()
    assert "token" not in serialized
