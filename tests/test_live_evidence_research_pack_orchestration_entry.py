# -*- coding: utf-8 -*-

from __future__ import annotations

import copy
import json
import socket

import pytest

from src.fundamental_skill.research_planning.evidence_aware_research_pack_scaffold import (
    build_evidence_aware_research_pack_scaffold,
)
from src.fundamental_skill.research_planning.live_evidence_aware_research_pack_vertical_slice import (
    LIVE_EVIDENCE_AWARE_RESEARCH_PACK_VERTICAL_SLICE_SCHEMA_VERSION,
)
from src.fundamental_skill.research_planning.live_evidence_research_pack_orchestration_entry import (
    LIVE_EVIDENCE_RESEARCH_PACK_ORCHESTRATION_REQUEST_SCHEMA_VERSION,
    LIVE_EVIDENCE_RESEARCH_PACK_ORCHESTRATION_RESULT_SCHEMA_VERSION,
    ORCHESTRATION_READINESS_BLOCKED,
    ORCHESTRATION_READINESS_READY,
    REQUESTED_OUTPUT_VERTICAL_SLICE_AND_MARKDOWN_PREVIEW,
    LiveEvidenceResearchPackOrchestrationEntryError,
    build_live_evidence_research_pack_orchestration_result,
)
from src.fundamental_skill.research_planning.ticker_research_context_skeleton import (
    build_ticker_research_context_skeleton,
)
from tests.test_live_evidence_aware_research_pack_vertical_slice import (
    _sample_components,
)
from tests.test_ticker_research_context_skeleton import _payload


def _request(**overrides):
    request = {
        "schema_version": (
            LIVE_EVIDENCE_RESEARCH_PACK_ORCHESTRATION_REQUEST_SCHEMA_VERSION
        ),
        "stock_code": "600406",
        "ts_code": "600406.SH",
        "company_name_hint": "Guodian NARI",
        "components": _sample_components(),
        "requested_output": REQUESTED_OUTPUT_VERTICAL_SLICE_AND_MARKDOWN_PREVIEW,
        "allow_network": False,
        "not_for_trading_advice": True,
    }
    request.update(overrides)
    return request


def _generic_components():
    context = build_ticker_research_context_skeleton(_payload())
    scaffold = build_evidence_aware_research_pack_scaffold(context)
    return {"evidence_aware_research_pack_scaffold": scaffold}


def test_valid_request_with_sample_validated_components_returns_ready_result():
    result = build_live_evidence_research_pack_orchestration_result(_request())

    assert result["schema_version"] == (
        LIVE_EVIDENCE_RESEARCH_PACK_ORCHESTRATION_RESULT_SCHEMA_VERSION
    )
    assert result["readiness"]["status"] == ORCHESTRATION_READINESS_READY
    assert result["vertical_slice"]["schema_version"] == (
        LIVE_EVIDENCE_AWARE_RESEARCH_PACK_VERTICAL_SLICE_SCHEMA_VERSION
    )
    assert result["markdown_preview"]
    assert result["evidence_status_rollup"]
    assert result["markdown_preview"] == (
        result["vertical_slice"]["user_readable_markdown_preview"]
    )
    assert result["evidence_status_rollup"] == (
        result["vertical_slice"]["evidence_status_rollup"]
    )


def test_request_summary_contains_stock_code_and_ts_code():
    result = build_live_evidence_research_pack_orchestration_result(_request())
    summary = result["request_summary"]

    assert summary["stock_code"] == "600406"
    assert summary["ts_code"] == "600406.SH"
    assert summary["requested_output"] == (
        REQUESTED_OUTPUT_VERTICAL_SLICE_AND_MARKDOWN_PREVIEW
    )


def test_missing_components_returns_blocked_readiness():
    request = _request()
    request.pop("components")

    result = build_live_evidence_research_pack_orchestration_result(request)

    assert result["readiness"]["status"] == ORCHESTRATION_READINESS_BLOCKED
    assert result["readiness"]["missing_required_components"] == [
        "evidence_aware_research_pack_scaffold"
    ]
    assert result["vertical_slice"] is None
    assert result["markdown_preview"] == ""
    assert result["evidence_status_rollup"] is None


def test_missing_evidence_aware_research_pack_scaffold_returns_blocked_readiness():
    components = _sample_components()
    components.pop("evidence_aware_research_pack_scaffold")

    result = build_live_evidence_research_pack_orchestration_result(
        _request(components=components)
    )

    assert result["readiness"]["status"] == ORCHESTRATION_READINESS_BLOCKED
    assert "evidence_aware_research_pack_scaffold" in (
        result["readiness"]["missing_required_components"]
    )
    assert result["vertical_slice"] is None


def test_request_allow_network_true_rejected():
    with pytest.raises(
        LiveEvidenceResearchPackOrchestrationEntryError,
        match="allow_network",
    ):
        build_live_evidence_research_pack_orchestration_result(
            _request(allow_network=True)
        )


def test_raw_tushare_provider_result_rejected():
    components = _sample_components()
    components["raw_tushare_provider_result"] = {"provider": "Tushare"}

    with pytest.raises(ValueError, match="raw inputs"):
        build_live_evidence_research_pack_orchestration_result(
            _request(components=components)
        )


def test_raw_provider_queue_rejected():
    components = _sample_components()
    components["raw_provider_queue"] = {
        "schema_version": "provider_candidate_metric_verification_queue.v1"
    }

    with pytest.raises(ValueError, match="raw inputs"):
        build_live_evidence_research_pack_orchestration_result(
            _request(components=components)
        )


def test_raw_http_response_rejected():
    components = _sample_components()
    components["raw_official_http_response"] = {"status_code": 200}

    with pytest.raises(ValueError, match="raw inputs"):
        build_live_evidence_research_pack_orchestration_result(
            _request(components=components)
        )


def test_raw_pdf_bytes_rejected():
    components = _sample_components()
    components["pdf_bytes"] = b"%PDF-1.7"

    with pytest.raises(ValueError, match="raw inputs|raw bytes"):
        build_live_evidence_research_pack_orchestration_result(
            _request(components=components)
        )


def test_cache_file_content_rejected():
    components = _sample_components()
    components["cache_file_content"] = "%PDF-1.7"

    with pytest.raises(ValueError, match="raw inputs"):
        build_live_evidence_research_pack_orchestration_result(
            _request(components=components)
        )


def test_arbitrary_url_rejected():
    request = _request()
    request["source_url"] = "https://example.com/report.pdf"

    with pytest.raises(ValueError, match="raw inputs|unsupported"):
        build_live_evidence_research_pack_orchestration_result(request)


def test_identity_stock_code_mismatch_blocked():
    result = build_live_evidence_research_pack_orchestration_result(
        _request(stock_code="000001")
    )

    assert result["readiness"]["status"] == ORCHESTRATION_READINESS_BLOCKED
    assert "stock_code_mismatch" in result["blocked_reasons"]
    assert result["vertical_slice"] is None


def test_identity_ts_code_mismatch_blocked():
    result = build_live_evidence_research_pack_orchestration_result(
        _request(ts_code="000001.SZ")
    )

    assert result["readiness"]["status"] == ORCHESTRATION_READINESS_BLOCKED
    assert "ts_code_mismatch" in result["blocked_reasons"]
    assert result["vertical_slice"] is None


def test_valid_600406_sample_works_but_no_hardcoded_requirement():
    sample_result = build_live_evidence_research_pack_orchestration_result(_request())
    generic_result = build_live_evidence_research_pack_orchestration_result(
        _request(
            stock_code="000001",
            ts_code="000001.SZ",
            company_name_hint="Sample Company",
            components=_generic_components(),
        )
    )

    assert sample_result["readiness"]["status"] == ORCHESTRATION_READINESS_READY
    assert generic_result["readiness"]["status"] == ORCHESTRATION_READINESS_READY
    assert generic_result["vertical_slice"]["stock_code"] == "000001"
    assert generic_result["vertical_slice"]["ts_code"] == "000001.SZ"


def test_input_request_and_components_not_mutated():
    request = _request()
    before = copy.deepcopy(request)

    build_live_evidence_research_pack_orchestration_result(request)

    assert request == before


def test_no_output_fixture_or_manifest_write(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    result = build_live_evidence_research_pack_orchestration_result(_request())

    assert result["readiness"]["status"] == ORCHESTRATION_READINESS_READY
    assert not (tmp_path / "output").exists()
    assert not (tmp_path / "fixtures").exists()
    assert not (tmp_path / "accepted_manifest.json").exists()


def test_no_live_network_provider_call(monkeypatch):
    def fail_socket(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "create_connection", fail_socket)

    result = build_live_evidence_research_pack_orchestration_result(_request())

    assert result["readiness"]["status"] == ORCHESTRATION_READINESS_READY


def test_result_has_no_formal_report_or_advice_flags():
    result = build_live_evidence_research_pack_orchestration_result(_request())
    serialized = json.dumps(result, ensure_ascii=False)

    assert result["readiness"]["has_formal_research_report"] is False
    assert result["readiness"]["has_trading_advice"] is False
    assert result["not_for_trading_advice"] is True
    assert "official_metric_fact" not in serialized
    assert "provider_official_conflict" not in serialized
