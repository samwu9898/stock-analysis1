# -*- coding: utf-8 -*-

from __future__ import annotations

import copy
import json
import re

import pytest

from src.fundamental_skill.research_planning.investment_director_research_context_pack import (
    INVESTMENT_DIRECTOR_RESEARCH_CONTEXT_PACK_REQUEST_SCHEMA_VERSION,
    InvestmentDirectorResearchContextPackError,
    assert_no_investment_director_context_forbidden_markers,
    assert_no_raw_backend_or_secret_leak,
    build_investment_director_missing_coverage_map,
    build_investment_director_research_context_pack,
    validate_investment_director_research_context_pack,
)
from tests.test_investment_director_research_context_pack import (
    NEW_RULEBOOK_COVERAGE_IDS,
    _question,
    _request_002050,
    _request_600406,
)


def _contains_market_action_word(text, word):
    return re.search(rf"(?<![a-z0-9_]){re.escape(word)}(?![a-z0-9_])", text) is not None


def _assert_request_rejected(**overrides):
    request = _request_002050(**overrides)
    with pytest.raises(InvestmentDirectorResearchContextPackError):
        build_investment_director_research_context_pack(request)


@pytest.mark.parametrize("field", ["token", "api_key"])
def test_request_token_or_api_key_rejected(field):
    _assert_request_rejected(**{field: "unsafe"})


@pytest.mark.parametrize("marker", [".env", "key file", "credential file", "tushare_token.txt"])
def test_env_key_file_and_tushare_token_markers_rejected(marker):
    _assert_request_rejected(company_name_hint=marker)


@pytest.mark.parametrize("field", ["raw_provider_bundle", "raw_provider_rows", "candidate_items"])
def test_raw_provider_bundle_rows_and_candidate_items_rejected(field):
    _assert_request_rejected(**{field: []})


@pytest.mark.parametrize("field", ["source_url", "page_number", "snippet", "sha256", "cache_path"])
def test_source_locator_page_snippet_hash_cache_rejected(field):
    _assert_request_rejected(**{field: "unsafe"})


def test_raw_html_content_rejected():
    _assert_request_rejected(
        old_report_frontstage_snapshot={"core_conclusion": "<html><body>raw</body></html>"}
    )


@pytest.mark.parametrize("field", ["html_raw", "report_html_raw"])
def test_raw_html_fields_rejected(field):
    _assert_request_rejected(**{field: "<html></html>"})


@pytest.mark.parametrize("field", ["raw_prompt", "raw_llm_response"])
def test_raw_prompt_and_raw_llm_response_rejected(field):
    _assert_request_rejected(**{field: "raw"})


@pytest.mark.parametrize("field", ["output_path", "fixture_path", "accepted_manifest_path"])
def test_output_fixture_and_accepted_manifest_path_rejected(field):
    _assert_request_rejected(**{field: "unsafe"})


def test_pdf_bytes_rejected():
    _assert_request_rejected(pdf_bytes=b"%PDF")


def test_prompt_payload_cannot_contain_token_like_string():
    pack = build_investment_director_research_context_pack(_request_002050())
    unsafe = copy.deepcopy(pack)
    unsafe["llm_context_prompt_payload"]["analysis_requirements"].append(
        "sk-ThisLooksLikeASecretValue123456789"
    )

    with pytest.raises(InvestmentDirectorResearchContextPackError):
        validate_investment_director_research_context_pack(unsafe)


def test_pack_cannot_contain_backend_trace():
    pack = build_investment_director_research_context_pack(_request_002050())
    unsafe = copy.deepcopy(pack)
    unsafe["research_intelligence_context"]["manual_review_items"].append(
        {"note": "backend trace"}
    )

    with pytest.raises(InvestmentDirectorResearchContextPackError):
        validate_investment_director_research_context_pack(unsafe)


@pytest.mark.parametrize("marker", ["raw_provider_bundle", "raw_provider_rows", "candidate_items"])
def test_pack_cannot_contain_raw_provider_or_candidate_items(marker):
    with pytest.raises(InvestmentDirectorResearchContextPackError):
        assert_no_raw_backend_or_secret_leak({"note": marker})


@pytest.mark.parametrize("marker", ["source_url", "page_number", "snippet", "sha256", "cache_path"])
def test_pack_cannot_contain_locator_or_cache_markers(marker):
    with pytest.raises(InvestmentDirectorResearchContextPackError):
        assert_no_raw_backend_or_secret_leak({"note": marker})


@pytest.mark.parametrize(
    "marker",
    [
        "buy",
        "sell",
        "hold",
        "target price",
        "position",
        "technical signal",
        "买入",
        "卖出",
        "持有",
        "目标价",
        "仓位",
        "技术信号",
    ],
)
def test_pack_cannot_output_market_action_language(marker):
    with pytest.raises(InvestmentDirectorResearchContextPackError):
        assert_no_investment_director_context_forbidden_markers({"view": marker})


@pytest.mark.parametrize(
    "phrase",
    ["user should decide", "用户自行判断", "自行跟踪", "需要用户", "建议用户"],
)
def test_pack_cannot_shift_responsibility_to_user(phrase):
    with pytest.raises(InvestmentDirectorResearchContextPackError):
        assert_no_investment_director_context_forbidden_markers({"view": phrase})


def test_built_pack_contains_no_market_action_or_user_shift_phrases():
    pack = build_investment_director_research_context_pack(_request_002050())
    text = json.dumps(pack, ensure_ascii=False).casefold()

    for forbidden in ("buy", "sell", "hold", "position"):
        assert not _contains_market_action_word(text, forbidden)
    for forbidden in (
        "target price",
        "technical signal",
        "用户自行判断",
        "自行跟踪",
        "需要用户",
        "建议用户",
    ):
        assert forbidden not in text


def test_source_tier_context_cannot_claim_consensus_with_one_source_bucket():
    pack = build_investment_director_research_context_pack(_request_002050())
    unsafe = copy.deepcopy(pack)
    unsafe["source_tier_and_viewpoint_context"]["independent_source_count"] = 1
    unsafe["source_tier_and_viewpoint_context"]["consensus_status"] = "available"

    with pytest.raises(InvestmentDirectorResearchContextPackError):
        validate_investment_director_research_context_pack(unsafe)


def test_director_framework_alignment_cannot_claim_fully_covered_when_weak_links_exist():
    pack = build_investment_director_research_context_pack(_request_002050())
    unsafe = copy.deepcopy(pack)
    unsafe["director_framework_alignment"]["alignment_summary"] = (
        "fully covered investment director framework"
    )

    with pytest.raises(InvestmentDirectorResearchContextPackError):
        validate_investment_director_research_context_pack(unsafe)


@pytest.mark.parametrize(
    "marker",
    ["<html><body>raw</body></html>", "chart artifact", "Report V1 artifact", "HTML artifact"],
)
def test_frontstage_visualization_requirements_cannot_generate_raw_artifacts(marker):
    pack = build_investment_director_research_context_pack(_request_002050())
    unsafe = copy.deepcopy(pack)
    unsafe["frontstage_visualization_requirements"]["html_report_mapping_summary"] = marker

    with pytest.raises(InvestmentDirectorResearchContextPackError):
        validate_investment_director_research_context_pack(unsafe)


@pytest.mark.parametrize(
    "marker",
    ["needs more research", "more research needed", "需进一步研究", "需要更多资料", "后续继续关注"],
)
def test_added_coverage_categories_cannot_contain_vague_next_data_task(marker):
    pack = build_investment_director_research_context_pack(_request_002050())
    unsafe = copy.deepcopy(pack)
    for item in unsafe["missing_coverage_map"]["items"]:
        if item["requirement_id"] == "news_and_special_events":
            item["next_data_task"] = marker
            break

    with pytest.raises(InvestmentDirectorResearchContextPackError):
        validate_investment_director_research_context_pack(unsafe)


@pytest.mark.parametrize(
    "section_name, field_name",
    [
        ("source_tier_and_viewpoint_context", "viewpoint_boundary"),
        ("director_framework_alignment", "alignment_summary"),
        ("frontstage_visualization_requirements", "html_report_mapping_summary"),
    ],
)
@pytest.mark.parametrize(
    "marker",
    ["backend trace", "raw_provider_bundle", "source_url", "snippet", "sha256", "cache_path"],
)
def test_added_sections_cannot_contain_backend_trace_or_raw_markers(
    section_name,
    field_name,
    marker,
):
    pack = build_investment_director_research_context_pack(_request_002050())
    unsafe = copy.deepcopy(pack)
    unsafe[section_name][field_name] = marker

    with pytest.raises(InvestmentDirectorResearchContextPackError):
        validate_investment_director_research_context_pack(unsafe)


@pytest.mark.parametrize(
    "section_name, field_name",
    [
        ("source_tier_and_viewpoint_context", "viewpoint_boundary"),
        ("director_framework_alignment", "alignment_summary"),
        ("frontstage_visualization_requirements", "html_report_mapping_summary"),
    ],
)
@pytest.mark.parametrize(
    "marker",
    ["buy", "target price", "position", "technical signal", "目标价", "仓位"],
)
def test_added_sections_cannot_contain_trading_language(
    section_name,
    field_name,
    marker,
):
    pack = build_investment_director_research_context_pack(_request_002050())
    unsafe = copy.deepcopy(pack)
    unsafe[section_name][field_name] = marker

    with pytest.raises(InvestmentDirectorResearchContextPackError):
        validate_investment_director_research_context_pack(unsafe)


@pytest.mark.parametrize(
    "section_name, field_name",
    [
        ("source_tier_and_viewpoint_context", "viewpoint_boundary"),
        ("director_framework_alignment", "alignment_summary"),
        ("frontstage_visualization_requirements", "html_report_mapping_summary"),
    ],
)
def test_added_sections_cannot_shift_responsibility_to_user(section_name, field_name):
    pack = build_investment_director_research_context_pack(_request_002050())
    unsafe = copy.deepcopy(pack)
    unsafe[section_name][field_name] = "建议用户自行判断"

    with pytest.raises(InvestmentDirectorResearchContextPackError):
        validate_investment_director_research_context_pack(unsafe)


def test_added_sections_cannot_convert_missing_or_not_assessable_to_positive_conclusion():
    pack = build_investment_director_research_context_pack(_request_002050())
    unsafe = copy.deepcopy(pack)
    unsafe["director_framework_alignment"]["alignment_summary"] = (
        "missing weak links mean 公司受益"
    )

    with pytest.raises(InvestmentDirectorResearchContextPackError):
        validate_investment_director_research_context_pack(unsafe)


def test_added_coverage_categories_exist_without_vague_tasks_in_built_pack():
    pack = build_investment_director_research_context_pack(_request_002050())
    coverage = {
        item["requirement_id"]: item
        for item in pack["missing_coverage_map"]["items"]
    }
    vague_markers = (
        "needs more research",
        "more research needed",
        "需进一步研究",
        "需要更多资料",
        "后续继续关注",
    )

    for requirement_id in NEW_RULEBOOK_COVERAGE_IDS:
        assert requirement_id in coverage
        for marker in vague_markers:
            assert marker not in coverage[requirement_id]["next_data_task"].casefold()


def test_missing_or_not_assessable_cannot_be_converted_into_positive_conclusions():
    pack = build_investment_director_research_context_pack(_request_002050())
    text = json.dumps(pack, ensure_ascii=False)

    assert "not_assessable" in text
    assert "缺口已解决" not in text
    assert "已经验证为正向结论" not in text
    assert "结论成立" not in text


def test_002050_robotics_theme_cannot_be_written_as_realized_revenue():
    pack = build_investment_director_research_context_pack(_request_002050())
    text = json.dumps(pack, ensure_ascii=False)

    assert "机器人" in text
    assert "机器人收入已兑现" not in text
    assert "robotics realized revenue" not in text.casefold()
    assert "收入已兑现" not in text


def test_600406_stable_growth_label_cannot_be_written_as_operating_steadiness_evidence():
    pack = build_investment_director_research_context_pack(_request_600406())
    text = json.dumps(pack, ensure_ascii=False)

    assert "stable_growth" in text
    assert "公司属于 stable_growth，所以经营稳健" not in text
    assert "公司属于stable_growth，所以经营稳健" not in text
    assert "stable_growth therefore operating steadiness" not in text.casefold()


@pytest.mark.parametrize(
    "phrase",
    [
        "capex increased, so capacity has been released",
        "capex 直接等于产能释放",
        "产能释放确定",
        "contract liabilities mean backlog",
        "合同负债代表 backlog",
        "R&D ratio is high, so the technology moat is strong",
        "R&D 率直接等于技术壁垒",
        "industry demand is strong, so the company benefits",
        "公司受益",
    ],
)
def test_positive_proxy_overread_phrases_rejected(phrase):
    with pytest.raises(InvestmentDirectorResearchContextPackError):
        assert_no_investment_director_context_forbidden_markers({"view": phrase})


def test_built_pack_does_not_contain_positive_proxy_overread_phrases():
    pack = build_investment_director_research_context_pack(_request_002050())
    text = json.dumps(pack, ensure_ascii=False).casefold()

    for forbidden in (
        "capacity has been released",
        "产能释放",
        "合同负债代表",
        "r&d ratio is high",
        "r&d 率直接等于",
        "公司受益",
    ):
        assert forbidden not in text


def test_coverage_item_with_only_framework_but_no_material_cannot_be_covered():
    request = {
        "schema_version": INVESTMENT_DIRECTOR_RESEARCH_CONTEXT_PACK_REQUEST_SCHEMA_VERSION,
        "stock_code": "999999",
        "ts_code": "999999.SZ",
        "company_name_hint": "framework-only sample",
        "strategy_type": "advanced_manufacturing_growth",
        "not_for_trading_advice": True,
        "research_questions_p1": {
            "schema_version": "research_questions_p1.v1",
            "stock_code": "999999",
            "generated_at": "2026-06-03T00:00:00",
            "questions": [
                _question(
                    "同业和市场份额数据是否存在？",
                    category="market_share_peer_framework",
                    layer="industry",
                    required=["同业样本", "市场份额分母"],
                    missing=["同业样本", "市场份额分母"],
                    status="missing",
                    confidence="not_assessable",
                    checked=["inline framework only"],
                )
            ],
        },
    }

    coverage_map = build_investment_director_missing_coverage_map(request)
    by_id = {item["requirement_id"]: item for item in coverage_map["items"]}

    assert by_id["market_share"]["coverage_status"] == "framework_exists_but_missing_data"
    assert by_id["competitor_peer_benchmark"]["coverage_status"] == "framework_exists_but_missing_data"
    assert by_id["market_share"]["covered_semantics"]["material_or_structured_input_exists"] is False


def test_no_token_appears_in_result_or_captured_output(capsys):
    pack = build_investment_director_research_context_pack(_request_002050())
    captured = capsys.readouterr()
    serialized = json.dumps(pack, ensure_ascii=False).casefold()

    assert "token" not in serialized
    assert "token" not in captured.out.casefold()
    assert "token" not in captured.err.casefold()
