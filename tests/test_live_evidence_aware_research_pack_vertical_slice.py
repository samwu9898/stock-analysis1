# -*- coding: utf-8 -*-

from __future__ import annotations

import copy
import json

import pytest

from src.fundamental_skill.data_verification.provider_metric_official_anchor import (
    build_provider_metric_official_disclosure_anchor_map,
)
from src.fundamental_skill.research_planning.evidence_aware_research_pack_scaffold import (
    build_evidence_aware_research_pack_scaffold,
)
from src.fundamental_skill.research_planning.live_evidence_aware_research_pack_vertical_slice import (
    LIVE_EVIDENCE_AWARE_RESEARCH_PACK_VERTICAL_SLICE_SCHEMA_VERSION,
    SECTION_IDS,
    build_live_evidence_aware_research_pack_vertical_slice,
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


def _artifact_cache(anchor_map):
    anchor_item = anchor_map["anchor_items"][0]
    anchor = anchor_item["official_disclosure_anchor"]
    sha256 = "a" * 64
    cache_filename = f"600406_20251231_annual_report_{sha256}.pdf"
    return {
        "schema_version": "official_disclosure_artifact_cache.v1",
        "provider": "Tushare",
        "ts_code": "600406.SH",
        "stock_code": "600406",
        "company_name_hint": "Guodian NARI",
        "artifact_items": [
            {
                "schema_version": "official_disclosure_artifact_cache_item.v1",
                "artifact_id": "sample-artifact-1",
                "source_title": anchor["source_title"],
                "source_url": anchor["source_url"],
                "source_domain": anchor["source_domain"],
                "final_url": anchor["source_url"],
                "final_domain": anchor["source_domain"],
                "disclosure_date": anchor["disclosure_date"],
                "stock_code": "600406",
                "company_name_hint": "Guodian NARI",
                "period_key": anchor["period_key"],
                "period_end_date": anchor["period_end_date"],
                "announcement_type": anchor["announcement_type"],
                "source_type": anchor["source_type"],
                "anchor_evidence_status": anchor["anchor_evidence_status"],
                "artifact_status": "cached",
                "download_status": "success",
                "cache_path": f"C:\\sample-cache\\{cache_filename}",
                "file_size_bytes": 4096,
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


def _sample_components():
    provider_result = _provider_candidate_result(
        stock_code="600406",
        ts_code="600406.SH",
        company_name_hint="Guodian NARI",
    )
    queue = _verification_queue(
        stock_code="600406",
        ts_code="600406.SH",
        company_name_hint="Guodian NARI",
    )
    context = build_ticker_research_context_skeleton(
        _payload(
            stock_code="600406",
            ts_code="600406.SH",
            company_name_hint="Guodian NARI",
            provider_candidate_financial_result=provider_result,
            provider_candidate_metric_verification_queue=queue,
            industry_framework_hint={
                "framework_id": "stable_growth",
                "driver_questions": ["Which disclosed demand data should be tested?"],
                "macro_variables": ["grid investment cycle"],
            },
        )
    )
    scaffold = build_evidence_aware_research_pack_scaffold(context)
    anchor_map = build_provider_metric_official_disclosure_anchor_map(
        queue,
        [
            _official_candidate(
                source_title="Guodian NARI 2025 Annual Report",
                source_url="https://static.cninfo.com.cn/finalpage/2026-04-30/annual.pdf",
                source_domain="static.cninfo.com.cn",
                stock_code="600406",
                company_name_hint="Guodian NARI",
                period_key="2025FY",
                period_end_date="20251231",
                announcement_type="annual_report",
            )
        ],
    )
    return {
        "ticker_research_context_skeleton": context,
        "evidence_aware_research_pack_scaffold": scaffold,
        "provider_metric_official_anchor_map": anchor_map,
        "official_disclosure_artifact_cache": _artifact_cache(anchor_map),
    }


def _section(vertical_slice, section_id):
    return next(section for section in vertical_slice["sections"] if section["section_id"] == section_id)


def test_valid_components_build_vertical_slice():
    vertical_slice = build_live_evidence_aware_research_pack_vertical_slice(_sample_components())

    assert vertical_slice["schema_version"] == LIVE_EVIDENCE_AWARE_RESEARCH_PACK_VERTICAL_SLICE_SCHEMA_VERSION
    assert vertical_slice["stock_code"] == "600406"
    assert vertical_slice["ts_code"] == "600406.SH"
    assert vertical_slice["company_name_hint"] == "Guodian NARI"
    assert vertical_slice["not_official_verified"] is True
    assert vertical_slice["not_for_trading_advice"] is True


def test_sections_contain_all_fixed_section_ids():
    vertical_slice = build_live_evidence_aware_research_pack_vertical_slice(_sample_components())

    assert tuple(section["section_id"] for section in vertical_slice["sections"]) == SECTION_IDS


def test_evidence_status_rollup_contains_required_status_counts():
    rollup = build_live_evidence_aware_research_pack_vertical_slice(_sample_components())[
        "evidence_status_rollup"
    ]

    assert rollup["provider_candidate_present"] is True
    assert rollup["pending_official_verification_count"] >= 1
    assert rollup["official_anchor_matched_count"] >= 1
    assert rollup["official_artifact_cached_count"] == 1
    assert rollup["official_verified_count"] == 0
    assert rollup["data_gap_count"] >= 1


def test_financial_candidate_summary_retains_provider_and_pending_statuses():
    section = _section(
        build_live_evidence_aware_research_pack_vertical_slice(_sample_components()),
        "financial_candidate_summary",
    )
    serialized = json.dumps(section, ensure_ascii=False)

    assert "provider_candidate" in serialized
    assert "pending_official_verification" in serialized
    assert "official_verified" not in serialized.replace("not_official_verified", "")


def test_official_anchor_and_artifact_status_displays_metadata_without_cache_path():
    section = _section(
        build_live_evidence_aware_research_pack_vertical_slice(_sample_components()),
        "official_anchor_and_artifact_status",
    )
    serialized = json.dumps(section, ensure_ascii=False)

    assert "official_anchor_matched" in serialized
    assert "artifact_cached" in serialized
    assert "sha256_prefix" in serialized
    assert "file_size_bytes" in serialized
    assert "cache_filename" in serialized
    assert "C:\\sample-cache" not in serialized
    assert "cache_path" not in serialized
    assert "official_verified" not in serialized.replace("not_official_verified", "")


def test_company_business_profile_missing_evidence_displays_data_gap():
    section = _section(
        build_live_evidence_aware_research_pack_vertical_slice(_sample_components()),
        "company_business_profile",
    )

    assert section["evidence_status"] == "data_gap"
    assert any(item["current_evidence_status"] == "data_gap" for item in section["evidence_items"])


def test_industry_and_macro_context_displays_questions_without_conclusion():
    section = _section(
        build_live_evidence_aware_research_pack_vertical_slice(_sample_components()),
        "industry_and_macro_context",
    )
    serialized = json.dumps(section, ensure_ascii=False).casefold()

    assert "industry_driver_questions" in serialized
    assert "industry_to_company_transmission_questions" in serialized
    assert "conclusion" not in serialized
    assert "company benefits" not in serialized
    assert "tailwind" not in serialized


def test_data_gaps_and_next_tasks_displays_high_priority_gaps():
    section = _section(
        build_live_evidence_aware_research_pack_vertical_slice(_sample_components()),
        "data_gaps_and_next_tasks",
    )
    high_priority = next(
        point for point in section["user_visible_points"] if point["point_id"] == "high_priority_data_gaps"
    )

    assert high_priority["count"] >= 1
    assert high_priority["current_evidence_status"] == "data_gap"


def test_research_questions_preserve_categories():
    vertical_slice = build_live_evidence_aware_research_pack_vertical_slice(_sample_components())
    source_categories = {
        question["category"]
        for question in _sample_components()["ticker_research_context_skeleton"]["research_questions"]["questions"]
    }
    section_categories = {
        item["category"]
        for item in _section(vertical_slice, "research_questions")["evidence_items"]
    }

    assert source_categories == section_categories


def test_cannot_conclude_yet_section_exists():
    section = _section(
        build_live_evidence_aware_research_pack_vertical_slice(_sample_components()),
        "cannot_conclude_yet",
    )

    assert section["evidence_status"] == "blocked"
    assert {item["blocked_conclusion"] for item in section["evidence_items"]} >= {
        "official_metric_values",
        "provider_official_consistency",
        "production_research_pack",
        "directional_decision",
        "valuation_target",
        "sizing_instruction",
    }


def test_markdown_preview_contains_evidence_labels_data_gaps_and_cannot_conclude():
    preview = build_live_evidence_aware_research_pack_vertical_slice(_sample_components())[
        "user_readable_markdown_preview"
    ]

    assert "这不是正式研报 / 不是投资建议" in preview
    assert "[provider_candidate]" in preview
    assert "data_gaps_and_next_tasks" in preview
    assert "cannot_conclude_yet" in preview
    assert "买入" not in preview
    assert "卖出" not in preview
    assert "持有" not in preview


def test_raw_tushare_provider_result_rejected():
    components = _sample_components()
    components["raw_tushare_provider_result"] = {"provider": "Tushare"}

    with pytest.raises(ValueError, match="raw inputs"):
        build_live_evidence_aware_research_pack_vertical_slice(components)


def test_raw_provider_queue_rejected():
    components = _sample_components()
    components["raw_provider_queue"] = {"schema_version": "provider_candidate_metric_verification_queue.v1"}

    with pytest.raises(ValueError, match="raw inputs"):
        build_live_evidence_aware_research_pack_vertical_slice(components)


def test_raw_pdf_bytes_rejected():
    components = _sample_components()
    components["pdf_bytes"] = b"%PDF-1.7"

    with pytest.raises(ValueError, match="raw inputs|raw bytes"):
        build_live_evidence_aware_research_pack_vertical_slice(components)


def test_input_components_not_mutated():
    components = _sample_components()
    before = copy.deepcopy(components)

    build_live_evidence_aware_research_pack_vertical_slice(components)

    assert components == before


def test_no_output_fixture_or_manifest_write(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    vertical_slice = build_live_evidence_aware_research_pack_vertical_slice(_sample_components())

    assert vertical_slice["schema_version"] == LIVE_EVIDENCE_AWARE_RESEARCH_PACK_VERTICAL_SLICE_SCHEMA_VERSION
    assert not (tmp_path / "output").exists()
    assert not (tmp_path / "fixtures").exists()
    assert not (tmp_path / "accepted_manifest.json").exists()
