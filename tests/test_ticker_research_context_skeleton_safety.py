# -*- coding: utf-8 -*-

from __future__ import annotations

import json

import pytest

from src.fundamental_skill.research_planning.ticker_research_context_skeleton import (
    TickerResearchContextSkeletonError,
    assert_no_research_context_forbidden_markers,
    build_ticker_research_context_skeleton,
)

from tests.test_ticker_research_context_skeleton import (
    _payload,
    _provider_candidate_result,
    _verification_queue,
)


@pytest.mark.parametrize("marker", ["token", "api_token"])
def test_token_marker_rejected(marker):
    with pytest.raises(TickerResearchContextSkeletonError, match="forbidden marker"):
        build_ticker_research_context_skeleton(_payload(caveats=[marker]))


def test_dotenv_marker_rejected():
    with pytest.raises(TickerResearchContextSkeletonError, match="forbidden marker"):
        build_ticker_research_context_skeleton(_payload(caveats=["read .env file"]))


def test_tushare_token_marker_rejected():
    with pytest.raises(TickerResearchContextSkeletonError, match="forbidden marker"):
        build_ticker_research_context_skeleton(_payload(caveats=["tushare_token"]))


def test_report_v1_marker_rejected():
    with pytest.raises(TickerResearchContextSkeletonError, match="forbidden marker"):
        build_ticker_research_context_skeleton(_payload(caveats=["Report V1 update"]))


@pytest.mark.parametrize(
    "marker",
    [
        "accepted manifest write",
        "output baseline write",
        "fixture write",
    ],
)
def test_accepted_manifest_output_baseline_fixture_write_markers_rejected(marker):
    with pytest.raises(TickerResearchContextSkeletonError, match="forbidden marker"):
        assert_no_research_context_forbidden_markers({"nested": [{"marker": marker}]})


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
    with pytest.raises(TickerResearchContextSkeletonError, match="forbidden marker"):
        build_ticker_research_context_skeleton(_payload(caveats=[marker]))


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
    with pytest.raises(TickerResearchContextSkeletonError, match="forbidden marker"):
        build_ticker_research_context_skeleton(_payload(caveats=[marker]))


def test_provider_candidate_cannot_become_official_verified():
    queue = _verification_queue()
    queue["verification_items"][0]["official_verification_status"] = "official_verified"

    with pytest.raises(TickerResearchContextSkeletonError, match="official_verified"):
        build_ticker_research_context_skeleton(
            _payload(provider_candidate_metric_verification_queue=queue)
        )


def test_provider_candidate_financial_result_cannot_claim_official_verified():
    result = _provider_candidate_result()
    result["trend_table"][0]["selected_metrics"]["revenue"] = "official_verified"

    with pytest.raises(TickerResearchContextSkeletonError, match="official_verified"):
        build_ticker_research_context_skeleton(
            _payload(provider_candidate_financial_result=result)
        )


def test_caveats_official_verified_text_is_rejected():
    with pytest.raises(TickerResearchContextSkeletonError, match="official_verified"):
        build_ticker_research_context_skeleton(_payload(caveats=["official_verified"]))


def test_business_segments_official_verified_text_is_rejected():
    with pytest.raises(TickerResearchContextSkeletonError, match="official_verified"):
        build_ticker_research_context_skeleton(_payload(business_segments=["official_verified"]))


def test_official_verified_status_name_is_allowed_for_explicit_official_evidence():
    context = build_ticker_research_context_skeleton(
        _payload(
            official_anchor_candidates=[
                {
                    "anchor_id": "annual_business_section",
                    "evidence_status": "official_verified",
                    "source_type": "official_disclosure",
                }
            ]
        )
    )

    assert context["evidence_status_summary"]["official_evidence_statuses"] == ["official_verified"]
    assert "official_verified" in context["evidence_status_summary"]["statuses_used"]
    assert context["evidence_status_summary"]["has_explicit_official_evidence"] is True


def test_no_token_appears_in_result_or_captured_output(capsys):
    context = build_ticker_research_context_skeleton(_payload())
    captured = capsys.readouterr()
    serialized = json.dumps(context, ensure_ascii=False).casefold()

    assert "token" not in captured.out.casefold()
    assert "token" not in captured.err.casefold()
    assert "token" not in serialized
