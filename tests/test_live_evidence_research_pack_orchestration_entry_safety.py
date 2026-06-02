# -*- coding: utf-8 -*-

from __future__ import annotations

import json

import pytest

from src.fundamental_skill.research_planning.live_evidence_research_pack_orchestration_entry import (
    LiveEvidenceResearchPackOrchestrationEntryError,
    assert_no_live_evidence_orchestration_forbidden_markers,
    build_live_evidence_research_pack_orchestration_result,
)
from tests.test_live_evidence_aware_research_pack_vertical_slice import (
    _sample_components,
)
from tests.test_live_evidence_research_pack_orchestration_entry import _request


@pytest.mark.parametrize("marker", ["token", "api_token"])
def test_token_marker_rejected(marker):
    with pytest.raises(
        LiveEvidenceResearchPackOrchestrationEntryError,
        match="forbidden marker",
    ):
        assert_no_live_evidence_orchestration_forbidden_markers(
            {"nested": [{"marker": marker}]}
        )


def test_dotenv_marker_rejected():
    with pytest.raises(ValueError, match="forbidden marker"):
        assert_no_live_evidence_orchestration_forbidden_markers(
            {"marker": "read .env file"}
        )


def test_tushare_token_marker_rejected():
    with pytest.raises(ValueError, match="forbidden marker"):
        assert_no_live_evidence_orchestration_forbidden_markers(
            {"marker": "tushare_token"}
        )


@pytest.mark.parametrize("marker", ["official_metric_fact", "provider_official_conflict"])
def test_forbidden_official_fact_and_conflict_markers_rejected(marker):
    with pytest.raises(ValueError, match="forbidden marker"):
        assert_no_live_evidence_orchestration_forbidden_markers({"marker": marker})


@pytest.mark.parametrize("marker", ["Report V1", "formal report"])
def test_report_v1_and_formal_report_markers_rejected(marker):
    with pytest.raises(ValueError, match="forbidden marker"):
        assert_no_live_evidence_orchestration_forbidden_markers({"marker": marker})


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
        assert_no_live_evidence_orchestration_forbidden_markers(
            {"nested": [{"marker": marker}]}
        )


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
        assert_no_live_evidence_orchestration_forbidden_markers({"marker": marker})


@pytest.mark.parametrize("marker", ["live provider", "live Tushare", "live CNInfo"])
def test_live_provider_tushare_cninfo_markers_rejected(marker):
    with pytest.raises(ValueError, match="forbidden marker"):
        assert_no_live_evidence_orchestration_forbidden_markers({"marker": marker})


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
        assert_no_live_evidence_orchestration_forbidden_markers({"marker": marker})


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
        assert_no_live_evidence_orchestration_forbidden_markers({"marker": marker})


def test_provider_candidate_cannot_become_official_verified():
    components = _sample_components()
    financial = components["ticker_research_context_skeleton"]["financial_context"]
    financial["key_metric_candidates"][0]["current_evidence_status"] = (
        "official_verified"
    )

    with pytest.raises(ValueError, match="official_verified"):
        build_live_evidence_research_pack_orchestration_result(
            _request(components=components)
        )


def test_official_anchor_matched_cannot_become_official_verified():
    components = _sample_components()
    anchor_item = components["provider_metric_official_anchor_map"]["anchor_items"][0]
    anchor_item["official_anchor_status"] = "official_verified"

    with pytest.raises(ValueError, match="official_verified"):
        build_live_evidence_research_pack_orchestration_result(
            _request(components=components)
        )


def test_artifact_cached_cannot_become_official_verified():
    components = _sample_components()
    artifact = components["official_disclosure_artifact_cache"]["artifact_items"][0]
    artifact["artifact_status"] = "official_verified"

    with pytest.raises(ValueError, match="official_verified"):
        build_live_evidence_research_pack_orchestration_result(
            _request(components=components)
        )


def test_no_token_appears_in_result_or_captured_output(capsys):
    result = build_live_evidence_research_pack_orchestration_result(_request())
    captured = capsys.readouterr()
    serialized = json.dumps(result, ensure_ascii=False).casefold()

    assert "token" not in captured.out.casefold()
    assert "token" not in captured.err.casefold()
    assert "token" not in serialized
