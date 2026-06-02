# -*- coding: utf-8 -*-

from __future__ import annotations

import copy
import json

from src.fundamental_skill.research_planning.llm_analyst_renderer_handoff import (
    LLM_ANALYST_HANDOFF_CONTEXT_SCHEMA_VERSION,
    LLM_ANALYST_PROMPT_CONTRACT_SCHEMA_VERSION,
    LLM_ANALYST_RENDERER_OUTPUT_SCHEMA_VERSION,
    LLM_ANALYST_REQUIRED_OUTPUT_SECTIONS,
    assert_no_user_visible_engineering_labels,
    build_llm_analyst_prompt_contract,
    build_model_facing_analyst_context,
    fake_llm_analyst_renderer,
    render_professional_brief_with_fake_llm,
    validate_llm_analyst_renderer_output,
)
from src.fundamental_skill.research_planning.professional_compact_brief_quality import (
    PROFESSIONAL_ANALYST_COMPACT_BRIEF_SCHEMA_VERSION,
    build_professional_analyst_context,
    default_deterministic_analyst_renderer,
    render_professional_compact_brief_from_context,
)
from tests.test_controlled_real_tushare_professional_compact_brief_pilot import (
    _FakeFinancialClient,
    _build,
)


_BASE_RESULT = None


def _base_result():
    global _BASE_RESULT
    if _BASE_RESULT is None:
        _BASE_RESULT = _build()
    return _BASE_RESULT


def _bundle(client=None, **overrides):
    if client is None and not overrides:
        return copy.deepcopy(_base_result()["provider_candidate_bundle"])
    return _build(client or _FakeFinancialClient(), **overrides)[
        "provider_candidate_bundle"
    ]


def _internal_brief():
    return copy.deepcopy(_base_result()["internal_analysis_brief"])


def _professional_context(client=None, **overrides):
    return build_professional_analyst_context(
        _bundle(client, **overrides),
        internal_analysis_brief=_internal_brief(),
    )


def _serialized(value):
    return json.dumps(value, ensure_ascii=False)


def test_valid_professional_analyst_context_builds_model_facing_context():
    model_context = build_model_facing_analyst_context(_professional_context())

    assert model_context["schema_version"] == LLM_ANALYST_HANDOFF_CONTEXT_SCHEMA_VERSION
    assert model_context["stock_code"] == "600406"
    assert model_context["not_for_trading_advice"] is True


def test_model_facing_context_contains_expected_derived_signals():
    model_context = build_model_facing_analyst_context(_professional_context())
    signals = model_context["derived_signals"]

    for key in ("revenue", "profit", "cashflow", "receivables", "margin", "debt", "roe"):
        assert signals[key]["present"] in {True, False}
        assert signals[key]["direction_hint"]
        assert signals[key]["quality_hint"]
    assert signals["revenue"]["present"] is True
    assert signals["profit"]["present"] is True
    assert signals["cashflow"]["present"] is True


def test_model_facing_context_contains_data_source_and_boundary_fields():
    model_context = build_model_facing_analyst_context(_professional_context())

    assert model_context["data_source_note"] == "Tushare"
    assert model_context["model_data_boundary"]
    assert model_context["evidence_confidence_hint"]


def test_model_facing_context_excludes_raw_provider_and_pending_labels():
    model_context = build_model_facing_analyst_context(_professional_context())
    text = _serialized(model_context)

    for forbidden in (
        "provider_candidate",
        "pending_official_verification",
        "pending verification",
        "official_verified_count",
        "provider vs official",
    ):
        assert forbidden not in text


def test_model_facing_context_excludes_secret_trace_and_locator_markers():
    model_context = build_model_facing_analyst_context(_professional_context())
    text = _serialized(model_context).casefold()

    for forbidden in (
        "token",
        ".env",
        "tushare_token",
        "source_url",
        "page_number",
        "snippet",
        "sha256",
        "cache_path",
        "raw provider queue",
        "raw http",
    ):
        assert forbidden.casefold() not in text


def test_prompt_contract_contains_required_output_sections():
    model_context = build_model_facing_analyst_context(_professional_context())
    contract = build_llm_analyst_prompt_contract(model_context)

    assert contract["schema_version"] == LLM_ANALYST_PROMPT_CONTRACT_SCHEMA_VERSION
    for section in LLM_ANALYST_REQUIRED_OUTPUT_SECTIONS:
        assert section in contract["required_output_sections"]
        assert section in contract["output_contract"]


def test_prompt_contract_contains_no_trading_advice_allowance():
    model_context = build_model_facing_analyst_context(_professional_context())
    contract = build_llm_analyst_prompt_contract(model_context)

    assert contract["trading_advice_allowed"] is False
    assert contract["artifact_generation_allowed"] is False
    assert contract["external_api_allowed"] is False
    assert contract["not_for_trading_advice"] is True
    assert "buy" in contract["forbidden_output_markers"]
    assert "target price" in contract["forbidden_output_markers"]


def test_fake_llm_analyst_renderer_returns_valid_llm_output():
    model_context = build_model_facing_analyst_context(_professional_context())
    output = fake_llm_analyst_renderer(model_context)

    assert output["schema_version"] == LLM_ANALYST_RENDERER_OUTPUT_SCHEMA_VERSION
    assert validate_llm_analyst_renderer_output(output) == output
    assert output["not_for_trading_advice"] is True


def test_fake_renderer_output_gives_professional_judgments():
    model_context = build_model_facing_analyst_context(_professional_context())
    output = fake_llm_analyst_renderer(model_context)
    text = _serialized(output)

    assert "基本面分析重心" in text
    assert "业务判断" in text
    assert "财务表现" in text
    assert "经营质量" in text
    assert "行业与宏观" in text
    assert "核心风险" in text


def test_fake_renderer_output_hides_engineering_labels():
    model_context = build_model_facing_analyst_context(_professional_context())
    output = fake_llm_analyst_renderer(model_context)

    assert_no_user_visible_engineering_labels(output)
    text = _serialized(output)
    for forbidden in (
        "provider_candidate",
        "pending_official_verification",
        "待核验",
        "数据缺口",
        "推理",
        "source_url",
        "sha256",
        "cache_path",
    ):
        assert forbidden not in text


def test_fake_renderer_output_does_not_shift_responsibility_to_user():
    model_context = build_model_facing_analyst_context(_professional_context())
    text = _serialized(fake_llm_analyst_renderer(model_context))

    for forbidden in ("用户自行", "自行判断", "自行跟踪", "需要用户", "建议用户"):
        assert forbidden not in text


def test_fake_renderer_output_contains_no_trading_advice():
    model_context = build_model_facing_analyst_context(_professional_context())
    text = _serialized(fake_llm_analyst_renderer(model_context)).casefold()

    for forbidden in (
        "buy",
        "sell",
        "hold",
        "target price",
        "portfolio",
        "position",
        "technical signal",
        "trading advice",
        "买入",
        "卖出",
        "持有",
        "目标价",
        "仓位",
        "技术信号",
        "投资建议",
    ):
        assert forbidden.casefold() not in text


def test_fake_renderer_output_can_be_converted_to_professional_compact_brief():
    brief = render_professional_brief_with_fake_llm(_professional_context())

    assert brief["schema_version"] == PROFESSIONAL_ANALYST_COMPACT_BRIEF_SCHEMA_VERSION
    assert brief["overall_view"]["view"]
    assert "Tushare" in brief["source_note"]


def test_integration_through_professional_compact_brief_quality_works():
    brief = render_professional_compact_brief_from_context(
        _professional_context(),
        analyst_renderer="fake_llm",
    )

    assert brief["schema_version"] == PROFESSIONAL_ANALYST_COMPACT_BRIEF_SCHEMA_VERSION
    assert "基本面分析重心" in brief["overall_view"]["view"]


def test_deterministic_renderer_path_still_works():
    context = _professional_context()
    brief = render_professional_compact_brief_from_context(context)
    output = default_deterministic_analyst_renderer(context)

    assert brief["schema_version"] == PROFESSIONAL_ANALYST_COMPACT_BRIEF_SCHEMA_VERSION
    assert "经营韧性" in output["sections"]["overall_view"]


def test_input_context_not_mutated():
    context = _professional_context()
    before = copy.deepcopy(context)

    model_context = build_model_facing_analyst_context(context)
    fake_llm_analyst_renderer(model_context)
    render_professional_brief_with_fake_llm(context)

    assert context == before


def test_non_600406_sample_passes():
    context = _professional_context(
        _FakeFinancialClient(ts_code="000001.SZ"),
        stock_code="000001",
        ts_code="000001.SZ",
        company_name_hint="Sample Company",
    )
    model_context = build_model_facing_analyst_context(context)
    brief = render_professional_brief_with_fake_llm(context)

    assert model_context["stock_code"] == "000001"
    assert model_context["ts_code"] == "000001.SZ"
    assert brief["stock_code"] == "000001"
