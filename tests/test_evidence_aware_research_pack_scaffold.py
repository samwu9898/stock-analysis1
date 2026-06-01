# -*- coding: utf-8 -*-

from __future__ import annotations

import copy
import json

import pytest

from src.fundamental_skill.research_planning.evidence_aware_research_pack_scaffold import (
    EVIDENCE_AWARE_RESEARCH_PACK_SCAFFOLD_SCHEMA_VERSION,
    SECTION_IDS,
    build_evidence_aware_research_pack_scaffold,
)
from src.fundamental_skill.research_planning.ticker_research_context_skeleton import (
    EVIDENCE_STATUSES,
    TICKER_RESEARCH_CONTEXT_SCHEMA_VERSION,
    build_ticker_research_context_skeleton,
)

from tests.test_ticker_research_context_skeleton import _payload


def _context(**payload_overrides):
    return build_ticker_research_context_skeleton(_payload(**payload_overrides))


def _section(scaffold, section_id):
    return next(section for section in scaffold["sections"] if section["section_id"] == section_id)


def _flatten_strings(value):
    result = []
    if isinstance(value, dict):
        for key, child in value.items():
            result.append(str(key))
            result.extend(_flatten_strings(child))
    elif isinstance(value, list):
        for child in value:
            result.extend(_flatten_strings(child))
    elif isinstance(value, str):
        result.append(value)
    return result


def test_valid_ticker_research_context_skeleton_builds_scaffold():
    context = _context()
    scaffold = build_evidence_aware_research_pack_scaffold(context)

    assert scaffold["schema_version"] == EVIDENCE_AWARE_RESEARCH_PACK_SCAFFOLD_SCHEMA_VERSION
    assert scaffold["source_context_schema_version"] == TICKER_RESEARCH_CONTEXT_SCHEMA_VERSION
    assert scaffold["stock_code"] == context["stock_code"]
    assert scaffold["not_for_trading_advice"] is True


def test_scaffold_sections_include_expected_fixed_ids():
    scaffold = build_evidence_aware_research_pack_scaffold(_context())

    assert tuple(section["section_id"] for section in scaffold["sections"]) == SECTION_IDS


def test_input_must_be_ticker_research_context_skeleton():
    with pytest.raises(ValueError, match="raw payload keys|schema_version"):
        build_evidence_aware_research_pack_scaffold(_payload())


def test_invalid_context_schema_version_is_blocked():
    context = _context()
    context["schema_version"] = "provider_candidate_financial_snapshot.v1"

    with pytest.raises(ValueError, match="schema_version"):
        build_evidence_aware_research_pack_scaffold(context)


def test_company_business_profile_data_gap_is_displayed():
    scaffold = build_evidence_aware_research_pack_scaffold(_context())
    section = _section(scaffold, "company_business_profile")

    assert section["evidence_status"] == "data_gap"
    assert any(
        item["item_id"] == "company_business_data_gaps" and item["data_gaps"]
        for item in section["items"]
    )


def test_financial_context_provider_candidate_and_pending_statuses_are_retained():
    scaffold = build_evidence_aware_research_pack_scaffold(_context())
    section = _section(scaffold, "financial_context")
    serialized = json.dumps(section, ensure_ascii=False)

    assert "provider_candidate" in section["evidence_status"]
    assert "pending_official_verification" in section["evidence_status"]
    assert "provider_candidate" in serialized
    assert "pending_official_verification" in serialized
    assert "official_verified" not in serialized


def test_industry_context_not_assessable_is_displayed():
    scaffold = build_evidence_aware_research_pack_scaffold(_context())
    section = _section(scaffold, "industry_context")

    assert section["evidence_status"] == "not_assessable"
    assert any(item["item_id"] == "industry_data_gaps" for item in section["items"])


def test_macro_transmission_displays_questions_without_conclusion():
    scaffold = build_evidence_aware_research_pack_scaffold(_context())
    section = _section(scaffold, "macro_transmission")
    serialized = json.dumps(section, ensure_ascii=False).casefold()

    question_item = next(
        item
        for item in section["items"]
        if item["item_id"] == "industry_to_company_transmission_questions"
    )
    assert question_item["industry_to_company_transmission_questions"]
    assert "tailwind" not in serialized
    assert "favorable" not in serialized
    assert "company benefits" not in serialized


def test_data_gap_section_displays_high_priority_gaps():
    context = _context()
    scaffold = build_evidence_aware_research_pack_scaffold(context)
    section = _section(scaffold, "data_gaps")
    high_priority_gap_ids = {
        gap["gap_id"] for gap in context["data_gap_plan"]["data_gaps"] if gap["priority"] == "high"
    }
    serialized = json.dumps(section, ensure_ascii=False)

    assert high_priority_gap_ids
    for gap_id in high_priority_gap_ids:
        assert gap_id in serialized


def test_research_questions_section_preserves_question_categories():
    context = _context()
    scaffold = build_evidence_aware_research_pack_scaffold(context)
    section = _section(scaffold, "research_questions")

    source_categories = {question["category"] for question in context["research_questions"]["questions"]}
    scaffold_categories = {item["category"] for item in section["items"]}
    assert source_categories == scaffold_categories


def test_evidence_status_legend_contains_all_statuses():
    scaffold = build_evidence_aware_research_pack_scaffold(_context())
    statuses = [entry["status"] for entry in scaffold["evidence_status_legend"]["entries"]]

    assert tuple(statuses) == EVIDENCE_STATUSES


def test_provider_candidate_is_not_upgraded_to_official_verified():
    scaffold = build_evidence_aware_research_pack_scaffold(_context())
    financial_strings = _flatten_strings(_section(scaffold, "financial_context"))

    assert "official_verified" not in financial_strings


def test_explicit_official_verified_status_is_preserved_in_summary_and_legend():
    context = _context(
        official_anchor_candidates=[
            {
                "anchor_id": "annual_business_section",
                "evidence_status": "official_verified",
                "source_type": "official_disclosure",
            }
        ]
    )
    scaffold = build_evidence_aware_research_pack_scaffold(context)
    subject = _section(scaffold, "research_subject")
    official_section = _section(scaffold, "official_verification")

    assert any(
        item.get("official_evidence_statuses") == ["official_verified"]
        for item in subject["items"]
    )
    assert any(
        item["item_id"] == "explicit_official_evidence_presence"
        and item["current_evidence_status"] == "official_verified"
        for item in official_section["items"]
    )
    assert "official_verified" in [
        entry["status"] for entry in scaffold["evidence_status_legend"]["entries"]
    ]


def test_raw_provider_payload_keys_are_rejected_even_with_context_schema_version():
    context = _context()
    context["provider_candidate_financial_result"] = {"provider": "Tushare"}

    with pytest.raises(ValueError, match="raw payload keys"):
        build_evidence_aware_research_pack_scaffold(context)


def test_no_output_fixture_or_manifest_write(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    scaffold = build_evidence_aware_research_pack_scaffold(_context())

    assert scaffold["schema_version"] == EVIDENCE_AWARE_RESEARCH_PACK_SCAFFOLD_SCHEMA_VERSION
    assert not (tmp_path / "output").exists()
    assert not (tmp_path / "fixtures").exists()
    assert not (tmp_path / "accepted_manifest.json").exists()


def test_input_context_is_not_mutated():
    context = _context()
    before = copy.deepcopy(context)

    build_evidence_aware_research_pack_scaffold(context)

    assert context == before
