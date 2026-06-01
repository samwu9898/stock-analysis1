# -*- coding: utf-8 -*-

from __future__ import annotations

import json

import pytest

from src.fundamental_skill.research_planning.evidence_aware_research_pack_scaffold import (
    assert_no_research_pack_scaffold_forbidden_markers,
    build_evidence_aware_research_pack_scaffold,
    validate_evidence_aware_research_pack_scaffold,
)
from src.fundamental_skill.research_planning.ticker_research_context_skeleton import (
    build_ticker_research_context_skeleton,
)

from tests.test_ticker_research_context_skeleton import _payload


def _scaffold():
    return build_evidence_aware_research_pack_scaffold(
        build_ticker_research_context_skeleton(_payload())
    )


def _section(scaffold, section_id):
    return next(section for section in scaffold["sections"] if section["section_id"] == section_id)


@pytest.mark.parametrize("marker", ["token", "api_token"])
def test_token_marker_rejected(marker):
    with pytest.raises(ValueError, match="forbidden marker"):
        assert_no_research_pack_scaffold_forbidden_markers({"nested": [{"marker": marker}]})


def test_dotenv_marker_rejected():
    with pytest.raises(ValueError, match="forbidden marker"):
        assert_no_research_pack_scaffold_forbidden_markers({"marker": "read .env file"})


def test_tushare_token_marker_rejected():
    with pytest.raises(ValueError, match="forbidden marker"):
        assert_no_research_pack_scaffold_forbidden_markers({"marker": "tushare_token"})


def test_report_v1_marker_rejected():
    with pytest.raises(ValueError, match="forbidden marker"):
        assert_no_research_pack_scaffold_forbidden_markers({"marker": "Report V1"})


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
        assert_no_research_pack_scaffold_forbidden_markers({"nested": [{"marker": marker}]})


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
        assert_no_research_pack_scaffold_forbidden_markers({"marker": marker})


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
    ],
)
def test_chinese_forbidden_markers_rejected(marker):
    with pytest.raises(ValueError, match="forbidden marker"):
        assert_no_research_pack_scaffold_forbidden_markers({"marker": marker})


def test_provider_candidate_cannot_become_official_verified():
    scaffold = _scaffold()
    financial = _section(scaffold, "financial_context")
    metric_item = next(item for item in financial["items"] if item["item_id"] == "key_metric_candidates")
    metric_item["key_metric_candidates"][0]["current_evidence_status"] = "official_verified"

    with pytest.raises(ValueError, match="official_verified"):
        validate_evidence_aware_research_pack_scaffold(scaffold)


def test_pending_verification_cannot_become_official_verified():
    scaffold = _scaffold()
    official = _section(scaffold, "official_verification")
    pending_item = next(
        item for item in official["items"] if item["item_id"] == "pending_official_verification_count"
    )
    pending_item["current_evidence_status"] = "official_verified"

    with pytest.raises(ValueError, match="official_verified"):
        validate_evidence_aware_research_pack_scaffold(scaffold)


def test_section_conclusion_like_forbidden_marker_rejected():
    scaffold = _scaffold()
    _section(scaffold, "macro_transmission")["limitations"].append(
        "company benefits from macro tailwind"
    )

    with pytest.raises(ValueError, match="forbidden marker"):
        validate_evidence_aware_research_pack_scaffold(scaffold)


def test_official_verified_text_is_rejected_outside_status_fields():
    with pytest.raises(ValueError, match="official_verified"):
        assert_no_research_pack_scaffold_forbidden_markers(
            {"plain_text": "official_verified should not be prose"}
        )


def test_legend_status_names_allow_official_verified():
    scaffold = _scaffold()
    statuses = [entry["status"] for entry in scaffold["evidence_status_legend"]["entries"]]

    assert "official_verified" in statuses
    validate_evidence_aware_research_pack_scaffold(scaffold)


def test_no_token_appears_in_result_or_captured_output(capsys):
    scaffold = _scaffold()
    captured = capsys.readouterr()
    serialized = json.dumps(scaffold, ensure_ascii=False).casefold()

    assert "token" not in captured.out.casefold()
    assert "token" not in captured.err.casefold()
    assert "token" not in serialized
