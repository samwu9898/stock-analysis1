# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import re
import socket

from src.fundamental_skill.data_verification.provider_metric_official_anchor import (
    build_provider_metric_official_disclosure_anchor_map,
)
from src.fundamental_skill.research_planning.evidence_aware_research_pack_scaffold import (
    build_evidence_aware_research_pack_scaffold,
)
from src.fundamental_skill.research_planning.live_evidence_aware_research_pack_vertical_slice import (
    LIVE_EVIDENCE_AWARE_RESEARCH_PACK_VERTICAL_SLICE_SCHEMA_VERSION,
)
from src.fundamental_skill.research_planning.live_evidence_research_pack_orchestration_entry import (
    LIVE_EVIDENCE_RESEARCH_PACK_ORCHESTRATION_REQUEST_SCHEMA_VERSION,
    ORCHESTRATION_READINESS_BLOCKED,
    ORCHESTRATION_READINESS_READY,
    REQUESTED_OUTPUT_VERTICAL_SLICE_AND_MARKDOWN_PREVIEW,
    build_live_evidence_research_pack_orchestration_result,
)
from src.fundamental_skill.research_planning.ticker_research_context_skeleton import (
    build_ticker_research_context_skeleton,
)
from tests.test_provider_metric_official_anchor import _official_candidate
from tests.test_ticker_research_context_skeleton import (
    _payload,
    _provider_candidate_result,
    _verification_queue,
)


COMPLETE_SAMPLE = {
    "stock_code": "300750",
    "ts_code": "300750.SZ",
    "company_name_hint": "Generic Battery Equipment Co",
}
MISSING_ANCHOR_SAMPLE = {
    "stock_code": "002371",
    "ts_code": "002371.SZ",
    "company_name_hint": "Generic Semiconductor Equipment Co",
}


def _request(identity, components):
    return {
        "schema_version": (
            LIVE_EVIDENCE_RESEARCH_PACK_ORCHESTRATION_REQUEST_SCHEMA_VERSION
        ),
        "stock_code": identity["stock_code"],
        "ts_code": identity["ts_code"],
        "company_name_hint": identity["company_name_hint"],
        "components": components,
        "requested_output": REQUESTED_OUTPUT_VERTICAL_SLICE_AND_MARKDOWN_PREVIEW,
        "allow_network": False,
        "not_for_trading_advice": True,
    }


def _generic_context_and_queue(identity):
    provider_result = _provider_candidate_result(**identity)
    queue = _verification_queue(**identity)
    context = build_ticker_research_context_skeleton(
        _payload(
            **identity,
            provider_candidate_financial_result=provider_result,
            provider_candidate_metric_verification_queue=queue,
        )
    )
    return context, queue


def _generic_anchor_candidate(identity):
    return _official_candidate(
        source_title=f"{identity['company_name_hint']} 2025 Annual Report",
        source_url=(
            "https://static.cninfo.com.cn/finalpage/2026-04-30/"
            f"{identity['stock_code']}-synthetic-annual.pdf"
        ),
        source_domain="static.cninfo.com.cn",
        stock_code=identity["stock_code"],
        company_name_hint=identity["company_name_hint"],
        period_key="2025FY",
        period_end_date="20251231",
        announcement_type="annual_report",
        source_type="cninfo_official_pdf",
    )


def _artifact_cache(identity, anchor_map):
    anchor_item = anchor_map["anchor_items"][0]
    anchor = anchor_item["official_disclosure_anchor"]
    sha256 = "b" * 64
    cache_filename = (
        f"{identity['stock_code']}_20251231_synthetic_annual_{sha256}.pdf"
    )
    return {
        "schema_version": "official_disclosure_artifact_cache.v1",
        "provider": "Tushare",
        "ts_code": identity["ts_code"],
        "stock_code": identity["stock_code"],
        "company_name_hint": identity["company_name_hint"],
        "artifact_items": [
            {
                "schema_version": "official_disclosure_artifact_cache_item.v1",
                "artifact_id": f"{identity['stock_code']}-synthetic-artifact-1",
                "source_title": anchor["source_title"],
                "source_url": anchor["source_url"],
                "source_domain": anchor["source_domain"],
                "final_url": anchor["source_url"],
                "final_domain": anchor["source_domain"],
                "disclosure_date": anchor["disclosure_date"],
                "stock_code": identity["stock_code"],
                "company_name_hint": identity["company_name_hint"],
                "period_key": anchor["period_key"],
                "period_end_date": anchor["period_end_date"],
                "announcement_type": anchor["announcement_type"],
                "source_type": anchor["source_type"],
                "anchor_evidence_status": anchor["anchor_evidence_status"],
                "artifact_status": "cached",
                "download_status": "success",
                "cache_path": f"C:\\synthetic-cache\\{cache_filename}",
                "file_size_bytes": 8192,
                "sha256": sha256,
                "content_type": "application/pdf",
                "source_lineage": {
                    "schema_version": "official_artifact_source_lineage.v1",
                    "source_anchor_status": anchor_item["official_anchor_status"],
                    "source_anchor_url": anchor["source_url"],
                    "source_anchor_domain": anchor["source_domain"],
                    "source_anchor_title": anchor["source_title"],
                    "source_disclosure_date": anchor["disclosure_date"],
                    "anchor_map_schema_version": anchor_map["schema_version"],
                    "anchor_item_metric_keys": [anchor_item["metric_key"]],
                    "not_official_verified": True,
                    "not_for_trading_advice": True,
                },
                "not_official_verified": True,
                "not_for_trading_advice": True,
                "caveats": ["sha256_byte_integrity_only"],
            }
        ],
        "skipped_items": [],
        "blocked_reasons": [],
        "caveats": [],
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }


def _complete_components():
    context, queue = _generic_context_and_queue(COMPLETE_SAMPLE)
    scaffold = build_evidence_aware_research_pack_scaffold(context)
    anchor_map = build_provider_metric_official_disclosure_anchor_map(
        queue,
        [_generic_anchor_candidate(COMPLETE_SAMPLE)],
    )
    return {
        "ticker_research_context_skeleton": context,
        "evidence_aware_research_pack_scaffold": scaffold,
        "provider_metric_official_anchor_map": anchor_map,
        "official_disclosure_artifact_cache": _artifact_cache(
            COMPLETE_SAMPLE,
            anchor_map,
        ),
    }


def _missing_anchor_artifact_components():
    context, queue = _generic_context_and_queue(MISSING_ANCHOR_SAMPLE)
    scaffold = build_evidence_aware_research_pack_scaffold(context)
    anchor_map = build_provider_metric_official_disclosure_anchor_map(queue, [])
    return {
        "ticker_research_context_skeleton": context,
        "evidence_aware_research_pack_scaffold": scaffold,
        "provider_metric_official_anchor_map": anchor_map,
    }


def _result(identity, components):
    return build_live_evidence_research_pack_orchestration_result(
        _request(identity, components)
    )


def _section(vertical_slice, section_id):
    return next(
        section
        for section in vertical_slice["sections"]
        if section["section_id"] == section_id
    )


def _assert_no_identity_leak(value):
    serialized = json.dumps(value, ensure_ascii=False)
    assert "600406" not in serialized
    assert "\u56fd\u7535\u5357\u745e" not in serialized
    assert "Guodian NARI" not in serialized


def _assert_no_forbidden_preview_markers(preview):
    lowered = preview.casefold()
    assert "target price" not in lowered
    assert "technical signal" not in lowered
    for marker in ("buy", "sell", "hold", "position"):
        assert re.search(rf"(?<![a-z]){marker}(?![a-z])", lowered) is None
    for marker in (
        "\u4e70\u5165",
        "\u5356\u51fa",
        "\u6301\u6709",
        "\u76ee\u6807\u4ef7",
        "\u4ed3\u4f4d",
        "\u6280\u672f\u4fe1\u53f7",
    ):
        assert marker not in preview


def test_non_600406_complete_shaped_components_ready_result():
    result = _result(COMPLETE_SAMPLE, _complete_components())
    vertical_slice = result["vertical_slice"]
    rollup = result["evidence_status_rollup"]

    assert result["readiness"]["status"] == ORCHESTRATION_READINESS_READY
    assert vertical_slice["schema_version"] == (
        LIVE_EVIDENCE_AWARE_RESEARCH_PACK_VERTICAL_SLICE_SCHEMA_VERSION
    )
    assert vertical_slice["stock_code"] == COMPLETE_SAMPLE["stock_code"]
    assert vertical_slice["ts_code"] == COMPLETE_SAMPLE["ts_code"]
    assert result["markdown_preview"]
    assert rollup["provider_candidate_present"] is True
    assert rollup["pending_official_verification_count"] >= 1
    assert rollup["official_anchor_matched_count"] >= 1
    assert rollup["official_artifact_cached_count"] >= 1
    assert rollup["official_verified_count"] == 0


def test_non_600406_complete_sample_has_anchor_and_artifact_status_without_cache_path():
    result = _result(COMPLETE_SAMPLE, _complete_components())
    section = _section(
        result["vertical_slice"],
        "official_anchor_and_artifact_status",
    )
    serialized = json.dumps(section, ensure_ascii=False)

    assert "official_anchor_matched" in serialized
    assert "artifact_cached" in serialized
    assert "cache_filename" in serialized
    assert "sha256_prefix" in serialized
    assert "file_size_bytes" in serialized
    assert "C:\\synthetic-cache" not in serialized
    assert "cache_path" not in serialized


def test_non_600406_complete_sample_does_not_leak_600406_or_guodian_terms():
    result = _result(COMPLETE_SAMPLE, _complete_components())
    preview = result["markdown_preview"]

    _assert_no_identity_leak(result)
    _assert_no_forbidden_preview_markers(preview)
    assert "stable_growth" not in json.dumps(result, ensure_ascii=False)


def test_non_600406_missing_anchor_artifact_sample_still_ready_with_gaps():
    result = _result(
        MISSING_ANCHOR_SAMPLE,
        _missing_anchor_artifact_components(),
    )
    vertical_slice = result["vertical_slice"]
    preview = result["markdown_preview"]

    assert result["readiness"]["status"] == ORCHESTRATION_READINESS_READY
    assert vertical_slice["stock_code"] == MISSING_ANCHOR_SAMPLE["stock_code"]
    assert vertical_slice["ts_code"] == MISSING_ANCHOR_SAMPLE["ts_code"]
    assert _section(vertical_slice, "cannot_conclude_yet")["evidence_status"] == (
        ORCHESTRATION_READINESS_BLOCKED
    )
    assert _section(vertical_slice, "data_gaps_and_next_tasks")
    assert "data_gaps_and_next_tasks" in preview
    assert "cannot_conclude_yet" in preview
    assert "data_gap" in preview


def test_non_600406_missing_anchor_artifact_rollup_zero_anchor_zero_artifact():
    result = _result(
        MISSING_ANCHOR_SAMPLE,
        _missing_anchor_artifact_components(),
    )
    rollup = result["evidence_status_rollup"]

    assert rollup["provider_candidate_present"] is True
    assert rollup["pending_official_verification_count"] >= 1
    assert rollup["official_anchor_matched_count"] == 0
    assert rollup["official_artifact_cached_count"] == 0
    assert rollup["official_verified_count"] == 0


def test_generic_samples_keep_official_verified_count_zero():
    complete_result = _result(COMPLETE_SAMPLE, _complete_components())
    missing_result = _result(
        MISSING_ANCHOR_SAMPLE,
        _missing_anchor_artifact_components(),
    )

    assert complete_result["evidence_status_rollup"]["official_verified_count"] == 0
    assert missing_result["evidence_status_rollup"]["official_verified_count"] == 0


def test_generic_samples_reject_identity_mismatch():
    request = _request(COMPLETE_SAMPLE, _complete_components())
    request["stock_code"] = "300751"

    result = build_live_evidence_research_pack_orchestration_result(request)

    assert result["readiness"]["status"] == ORCHESTRATION_READINESS_BLOCKED
    assert "stock_code_mismatch" in result["blocked_reasons"]
    assert result["vertical_slice"] is None
    assert result["markdown_preview"] == ""


def test_generic_samples_do_not_write_output_fixtures_manifest(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    result = _result(COMPLETE_SAMPLE, _complete_components())

    assert result["readiness"]["status"] == ORCHESTRATION_READINESS_READY
    assert not (tmp_path / "output").exists()
    assert not (tmp_path / "fixtures").exists()
    assert not (tmp_path / "accepted_manifest.json").exists()


def test_generic_samples_do_not_call_network(monkeypatch):
    def fail_socket(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "create_connection", fail_socket)

    complete_result = _result(COMPLETE_SAMPLE, _complete_components())
    missing_result = _result(
        MISSING_ANCHOR_SAMPLE,
        _missing_anchor_artifact_components(),
    )

    assert complete_result["readiness"]["status"] == ORCHESTRATION_READINESS_READY
    assert missing_result["readiness"]["status"] == ORCHESTRATION_READINESS_READY
