# -*- coding: utf-8 -*-

from __future__ import annotations

import copy
import json

from src.fundamental_skill.research_planning.analysis_brief_report_v1_adapter import (
    ANALYSIS_BRIEF_REPORT_V1_BACKEND_GROUNDING_SANITIZED_SCHEMA_VERSION,
    ANALYSIS_BRIEF_REPORT_V1_COMPATIBILITY_PAYLOAD_SCHEMA_VERSION,
    REPORT_V1_LABEL_COVERAGE_CAVEAT,
    REPORT_V1_LABEL_FORWARD_TRACKING_VARIABLE,
    REPORT_V1_LABEL_MANUAL_REVIEW_REQUIRED,
    REPORT_V1_LABEL_UNSUPPORTED_ASSUMPTION,
    REPORT_V1_LABEL_VERIFIED_FACT,
    build_analysis_brief_report_v1_compatibility_payload,
    translate_analysis_label_to_report_v1_label,
)
from src.fundamental_skill.research_planning.user_facing_analysis_brief import (
    LABEL_CANNOT_CONCLUDE,
    LABEL_DATA_GAP,
    LABEL_INFERENCE,
    LABEL_PENDING,
    LABEL_RELIABLE,
)
from tests.test_user_facing_analysis_brief import _brief, _locator_result


def _payload(locator_result=None):
    return build_analysis_brief_report_v1_compatibility_payload(_brief(locator_result))


def test_valid_user_facing_analysis_brief_builds_compatibility_payload():
    payload = _payload()

    assert (
        payload["schema_version"]
        == ANALYSIS_BRIEF_REPORT_V1_COMPATIBILITY_PAYLOAD_SCHEMA_VERSION
    )
    assert payload["source_brief_schema_version"] == "user_facing_analysis_brief.v1"
    assert payload["stock_code"] == "600406"
    assert payload["ts_code"] == "600406.SH"
    assert payload["company_name_hint"] == "Guodian NARI"
    assert payload["not_official_verified"] is True
    assert payload["not_for_trading_advice"] is True


def test_all_nine_user_visible_sections_are_mapped_to_context_blocks():
    payload = _payload()
    expected = {
        "subject_context": "subject_summary",
        "executive_boundary_context": "current_judgment_boundary",
        "business_context": "business_logic",
        "financial_context": "financial_interpretation",
        "industry_macro_context": "industry_macro_context",
        "risk_context": "risk_points",
        "evidence_gap_context": "data_gaps_that_matter",
        "follow_up_context": "tracking_indicators",
        "rebuttal_context": "cannot_conclude_yet",
    }

    for context_key, section_id in expected.items():
        assert payload[context_key]["source_section_id"] == section_id
        assert payload[context_key]["user_visible"] is True
        assert payload[context_key]["not_official_verified"] is True
        assert payload[context_key]["not_for_trading_advice"] is True


def test_field_mapping_targets_are_preserved_as_report_v1_candidates():
    payload = _payload()

    assert payload["subject_context"]["target_report_v1_section"] == [
        "executive_summary"
    ]
    assert payload["executive_boundary_context"]["target_report_v1_section"] == [
        "data_quality_assessment"
    ]
    assert payload["business_context"]["target_report_v1_section"] == [
        "company_fundamentals"
    ]
    assert payload["financial_context"]["target_report_v1_section"] == [
        "company_fundamentals",
        "data_quality_assessment",
    ]
    assert payload["industry_macro_context"]["target_report_v1_section"] == [
        "macro_context",
        "industry_context",
    ]
    assert payload["risk_context"]["target_report_v1_section"] == ["risk_analysis"]
    assert payload["evidence_gap_context"]["target_report_v1_section"] == [
        "evidence_gaps"
    ]
    assert payload["follow_up_context"]["target_report_v1_section"] == [
        "follow_up_variables"
    ]
    assert payload["rebuttal_context"]["target_report_v1_section"] == [
        "rebuttal_conditions",
        "evidence_gaps",
    ]


def test_tracking_indicators_map_to_follow_up_variables():
    payload = _payload()
    context = payload["follow_up_context"]

    assert context["source_section_id"] == "tracking_indicators"
    assert context["translated_evidence_label"] == REPORT_V1_LABEL_FORWARD_TRACKING_VARIABLE
    assert {
        point["translated_evidence_label"] for point in context["analysis_points"]
    } == {REPORT_V1_LABEL_FORWARD_TRACKING_VARIABLE}


def test_backend_grounding_summary_is_sanitized_only():
    payload = _payload(_locator_result())
    summary = payload["backend_grounding_summary_sanitized"]

    assert (
        summary["schema_version"]
        == ANALYSIS_BRIEF_REPORT_V1_BACKEND_GROUNDING_SANITIZED_SCHEMA_VERSION
    )
    assert summary["audit_trace_available"] is True
    assert summary["official_anchor_available"] is True
    assert summary["artifact_cached_available"] is True
    assert summary["locator_available"] is True
    assert summary["provider_candidate_present"] is True
    assert isinstance(summary["pending_verification_count"], int)
    assert isinstance(summary["official_verified_count"], int)
    assert isinstance(summary["data_gap_count"], int)
    assert set(summary) == {
        "schema_version",
        "audit_trace_available",
        "official_anchor_available",
        "artifact_cached_available",
        "locator_available",
        "provider_candidate_present",
        "pending_verification_count",
        "official_verified_count",
        "data_gap_count",
        "not_for_trading_advice",
    }


def test_backend_only_fields_are_not_leaked_to_payload():
    payload = _payload(_locator_result())
    serialized = json.dumps(payload, ensure_ascii=False)

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
        assert forbidden not in serialized


def test_label_translation_rules_do_not_promote_by_default():
    assert (
        translate_analysis_label_to_report_v1_label(LABEL_RELIABLE)
        == REPORT_V1_LABEL_MANUAL_REVIEW_REQUIRED
    )
    assert (
        translate_analysis_label_to_report_v1_label(LABEL_RELIABLE, explicit_reviewed_source=True)
        == REPORT_V1_LABEL_VERIFIED_FACT
    )
    assert (
        translate_analysis_label_to_report_v1_label(LABEL_PENDING)
        == REPORT_V1_LABEL_MANUAL_REVIEW_REQUIRED
    )
    assert (
        translate_analysis_label_to_report_v1_label(LABEL_DATA_GAP)
        == REPORT_V1_LABEL_COVERAGE_CAVEAT
    )
    assert (
        translate_analysis_label_to_report_v1_label(LABEL_INFERENCE)
        == REPORT_V1_LABEL_UNSUPPORTED_ASSUMPTION
    )
    assert (
        translate_analysis_label_to_report_v1_label(LABEL_CANNOT_CONCLUDE)
        == REPORT_V1_LABEL_COVERAGE_CAVEAT
    )


def test_no_verified_fact_emitted_by_default():
    payload = _payload(_locator_result())
    serialized = json.dumps(payload, ensure_ascii=False)

    assert REPORT_V1_LABEL_VERIFIED_FACT not in serialized
    assert payload["label_translation_summary"]["official_fact_promotion_blocked"] is True
    assert all(
        block["translated_evidence_label"] != REPORT_V1_LABEL_VERIFIED_FACT
        for block in (payload[key] for key in (
            "subject_context",
            "executive_boundary_context",
            "business_context",
            "financial_context",
            "industry_macro_context",
            "risk_context",
            "evidence_gap_context",
            "follow_up_context",
            "rebuttal_context",
        ))
    )


def test_locator_and_artifact_status_do_not_upgrade_to_verified_fact():
    payload = _payload(_locator_result())

    assert payload["backend_grounding_summary_sanitized"]["locator_available"] is True
    assert payload["backend_grounding_summary_sanitized"]["artifact_cached_available"] is True
    assert REPORT_V1_LABEL_VERIFIED_FACT not in json.dumps(payload, ensure_ascii=False)


def test_no_report_html_output_fixture_or_manifest_write(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    payload = build_analysis_brief_report_v1_compatibility_payload(_brief())

    assert payload["schema_version"] == ANALYSIS_BRIEF_REPORT_V1_COMPATIBILITY_PAYLOAD_SCHEMA_VERSION
    assert not (tmp_path / "output").exists()
    assert not (tmp_path / "fixtures").exists()
    assert not (tmp_path / "accepted_manifest.json").exists()
    assert not (tmp_path / "report.md").exists()
    assert not (tmp_path / "report.html").exists()


def test_input_brief_not_mutated():
    brief = _brief(_locator_result())
    before = copy.deepcopy(brief)

    build_analysis_brief_report_v1_compatibility_payload(brief)

    assert brief == before


def test_non_600406_brief_sample_passes():
    brief = _brief()
    brief["stock_code"] = "000001"
    brief["ts_code"] = "000001.SZ"
    brief["company_name_hint"] = "Ping An Bank"

    payload = build_analysis_brief_report_v1_compatibility_payload(brief)

    assert payload["stock_code"] == "000001"
    assert payload["ts_code"] == "000001.SZ"
    assert payload["company_name_hint"] == "Ping An Bank"


def test_missing_locator_still_passes():
    payload = _payload()

    assert payload["backend_grounding_summary_sanitized"]["locator_available"] is False
    assert payload["subject_context"]["analysis_points"]


def test_markdown_preview_is_not_parsed_as_source_of_truth():
    brief = _brief()
    brief["user_visible_sections"][0]["analysis_points"][0]["text"] = "section-source-text"
    brief["markdown_preview"] = "\n".join(
        [
            "preview-only-text",
            "current_judgment_boundary",
            "data_gaps_that_matter",
            "tracking_indicators",
            "cannot_conclude_yet",
        ]
    )

    payload = build_analysis_brief_report_v1_compatibility_payload(brief)
    serialized = json.dumps(payload, ensure_ascii=False)

    assert payload["source_brief_preview_available"] is True
    assert "section-source-text" in serialized
    assert "preview-only-text" not in serialized
