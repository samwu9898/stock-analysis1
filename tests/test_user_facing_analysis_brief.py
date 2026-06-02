# -*- coding: utf-8 -*-

from __future__ import annotations

import copy
import json

import pytest

from src.fundamental_skill.research_planning.user_facing_analysis_brief import (
    BACKEND_GROUNDING_SUMMARY_SCHEMA_VERSION,
    LABEL_CANNOT_CONCLUDE,
    LABEL_DATA_GAP,
    LABEL_INFERENCE,
    LABEL_PENDING,
    USER_FACING_ANALYSIS_BRIEF_SCHEMA_VERSION,
    USER_VISIBLE_SECTION_IDS,
    UserFacingAnalysisBriefError,
    build_user_facing_analysis_brief,
)
from src.fundamental_skill.research_planning.live_evidence_research_pack_orchestration_entry import (
    build_live_evidence_research_pack_orchestration_result,
)
from tests.test_live_evidence_research_pack_orchestration_entry import _request


def _orchestration_result():
    return build_live_evidence_research_pack_orchestration_result(_request())


def _locator_result():
    snippet = "safe locator hint for company profile"
    section_snippet = "safe section heading context"
    return {
        "schema_version": "official_artifact_evidence_locator.v1",
        "provider": "Tushare",
        "ts_code": "600406.SH",
        "stock_code": "600406",
        "company_name_hint": "Guodian NARI",
        "locator_items": [
            {
                "schema_version": "official_artifact_evidence_locator_item.v1",
                "artifact_id": "artifact_001",
                "source_title": "Guodian NARI Annual Report",
                "source_url": "https://static.cninfo.com.cn/finalpage/report.pdf",
                "source_domain": "static.cninfo.com.cn",
                "disclosure_date": "2026-04-30",
                "stock_code": "600406",
                "company_name_hint": "Guodian NARI",
                "period_key": "2025FY",
                "period_end_date": "20251231",
                "announcement_type": "annual_report",
                "source_artifact_sha256": "a" * 64,
                "source_file_size_bytes": 4096,
                "cache_filename": "safe_report.pdf",
                "text_layer_available": True,
                "report_title_hits": [
                    {
                        "schema_version": "official_artifact_text_hit.v1",
                        "hit_type": "report_title",
                        "keyword": "Annual Report",
                        "page_number": 1,
                        "snippet": snippet,
                        "snippet_char_count": len(snippet),
                        "confidence": "high",
                        "not_official_verified": True,
                        "not_for_trading_advice": True,
                    }
                ],
                "company_name_hits": [],
                "stock_code_hits": [],
                "report_period_hits": [],
                "section_heading_hits": [
                    {
                        "schema_version": "official_artifact_section_locator.v1",
                        "section_type": "company_profile",
                        "heading_text": "Company Profile",
                        "page_number": 2,
                        "snippet": section_snippet,
                        "confidence": "medium",
                        "not_official_verified": True,
                        "not_for_trading_advice": True,
                    }
                ],
                "keyword_hits": [],
                "locator_confidence": "high",
                "extraction_scope": "locator_text_layer_only",
                "not_official_verified": True,
                "not_for_trading_advice": True,
                "caveats": [],
            }
        ],
        "skipped_items": [],
        "blocked_reasons": [],
        "caveats": [],
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }


def _brief(locator_result=None):
    payload = {"orchestration_result": _orchestration_result()}
    if locator_result is not None:
        payload["locator_result"] = locator_result
    return build_user_facing_analysis_brief(payload)


def _section(brief, section_id):
    return next(
        section
        for section in brief["user_visible_sections"]
        if section["section_id"] == section_id
    )


def test_valid_orchestration_result_builds_user_facing_analysis_brief():
    brief = _brief()

    assert brief["schema_version"] == USER_FACING_ANALYSIS_BRIEF_SCHEMA_VERSION
    assert brief["brief_type"] == "user_facing_analysis_draft"
    assert brief["stock_code"] == "600406"
    assert brief["ts_code"] == "600406.SH"
    assert brief["company_name_hint"] == "Guodian NARI"
    assert brief["not_official_verified"] is True
    assert brief["not_for_trading_advice"] is True


def test_valid_orchestration_and_locator_build_without_exposing_locator_details():
    locator_result = _locator_result()
    brief = _brief(locator_result)
    serialized_user = json.dumps(
        {
            "sections": brief["user_visible_sections"],
            "preview": brief["markdown_preview"],
        },
        ensure_ascii=False,
    )

    assert brief["backend_grounding_summary"]["locator_available"] is True
    for forbidden in (
        "page_number",
        "snippet",
        "source_url",
        "sha256",
        "cache_path",
        "safe locator hint",
        "https://static.cninfo.com.cn",
        "a" * 64,
    ):
        assert forbidden not in serialized_user


def test_sections_schema_and_markdown_preview_are_fixed_and_user_facing():
    brief = _brief()
    section_ids = tuple(section["section_id"] for section in brief["user_visible_sections"])

    assert section_ids == USER_VISIBLE_SECTION_IDS
    assert brief["markdown_preview"]
    assert "current_judgment_boundary" in brief["markdown_preview"]
    assert "data_gaps_that_matter" in brief["markdown_preview"]
    assert "tracking_indicators" in brief["markdown_preview"]
    assert "cannot_conclude_yet" in brief["markdown_preview"]
    assert LABEL_PENDING in brief["markdown_preview"]
    assert LABEL_DATA_GAP in brief["markdown_preview"]
    assert LABEL_INFERENCE in brief["markdown_preview"]
    assert LABEL_CANNOT_CONCLUDE in brief["markdown_preview"]


def test_backend_grounding_summary_is_not_default_visible_and_has_only_summary_keys():
    summary = _brief(_locator_result())["backend_grounding_summary"]

    assert summary["schema_version"] == BACKEND_GROUNDING_SUMMARY_SCHEMA_VERSION
    assert summary["default_visible"] is False
    assert summary["audit_trace_available"] is True
    assert summary["official_anchor_available"] is True
    assert summary["artifact_cached_available"] is True
    assert summary["provider_candidate_present"] is True
    assert isinstance(summary["pending_verification_count"], int)
    assert isinstance(summary["official_verified_count"], int)
    assert isinstance(summary["data_gap_count"], int)
    serialized = json.dumps(summary, ensure_ascii=False)
    for forbidden in ("page_number", "snippet", "source_url", "sha256", "cache_path"):
        assert forbidden not in serialized


def test_evidence_statuses_map_to_user_visible_labels_without_promotion():
    brief = _brief()

    assert _section(brief, "financial_interpretation")["analysis_label"] == LABEL_PENDING
    assert _section(brief, "business_logic")["analysis_label"] == LABEL_DATA_GAP
    assert _section(brief, "industry_macro_context")["analysis_label"] == LABEL_INFERENCE
    assert _section(brief, "cannot_conclude_yet")["analysis_label"] == LABEL_CANNOT_CONCLUDE
    assert brief["backend_grounding_summary"]["official_verified_count"] == 0
    assert all(
        point["label"] != "\u8f83\u53ef\u9760"
        for section in brief["user_visible_sections"]
        for point in section["analysis_points"]
    )


def test_artifact_and_locator_availability_do_not_upgrade_to_reliable_label():
    brief = _brief(_locator_result())
    labels = {
        point["label"]
        for section in brief["user_visible_sections"]
        for point in section["analysis_points"]
    }

    assert brief["backend_grounding_summary"]["locator_available"] is True
    assert "\u8f83\u53ef\u9760" not in labels


def test_missing_locator_result_still_builds_brief():
    brief = _brief()

    assert brief["backend_grounding_summary"]["locator_available"] is False
    assert brief["markdown_preview"]


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("raw_tushare_provider_result", {"provider": "Tushare"}),
        ("raw_provider_queue", [{"metric": "x"}]),
        ("pdf_bytes", b"%PDF-1.7"),
        ("arbitrary_url", "https://example.com/report.pdf"),
    ],
)
def test_raw_inputs_rejected(key, value):
    payload = {"orchestration_result": _orchestration_result()}
    payload["orchestration_result"] = copy.deepcopy(payload["orchestration_result"])
    payload["orchestration_result"][key] = value

    with pytest.raises(UserFacingAnalysisBriefError, match="raw|bytes"):
        build_user_facing_analysis_brief(payload)


def test_allow_network_true_rejected():
    with pytest.raises(UserFacingAnalysisBriefError, match="allow_network"):
        build_user_facing_analysis_brief(
            {"orchestration_result": _orchestration_result(), "allow_network": True}
        )


def test_input_payload_not_mutated():
    payload = {
        "orchestration_result": _orchestration_result(),
        "locator_result": _locator_result(),
    }
    before = copy.deepcopy(payload)

    build_user_facing_analysis_brief(payload)

    assert payload == before


def test_no_output_fixture_or_manifest_write(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    brief = build_user_facing_analysis_brief(
        {"orchestration_result": _orchestration_result()}
    )

    assert brief["markdown_preview"]
    assert not (tmp_path / "output").exists()
    assert not (tmp_path / "fixtures").exists()
    assert not (tmp_path / "accepted_manifest.json").exists()
