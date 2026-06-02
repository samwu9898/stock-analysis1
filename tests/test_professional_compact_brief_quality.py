# -*- coding: utf-8 -*-

from __future__ import annotations

import copy
import json

from src.fundamental_skill.research_planning.controlled_real_tushare_professional_compact_brief_pilot import (
    PROFESSIONAL_ANALYST_COMPACT_BRIEF_SCHEMA_VERSION,
    build_professional_analyst_compact_brief,
)
from src.fundamental_skill.research_planning.professional_compact_brief_quality import (
    PROFESSIONAL_ANALYST_CONTEXT_SCHEMA_VERSION,
    PROFESSIONAL_ANALYST_FINANCIAL_SIGNAL_SCHEMA_VERSION,
    PROFESSIONAL_ANALYST_QUALITY_SIGNAL_SCHEMA_VERSION,
    PROFESSIONAL_ANALYST_RENDERER_OUTPUT_SCHEMA_VERSION,
    assert_no_user_visible_engineering_labels,
    build_financial_signal_context,
    build_operating_quality_signal_context,
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


def _with_metric(bundle, key, value):
    copied = copy.deepcopy(bundle)
    latest_period = copied["periods"][-1]
    for item in copied["candidate_items"]:
        if item["period"] == latest_period and item["candidate_key"] == key:
            item["candidate_value"] = value
            item["value_status"] = "present" if value is not None else "missing"
    return copied


def _render_text(bundle):
    context = build_professional_analyst_context(
        bundle,
        internal_analysis_brief=_internal_brief(),
    )
    brief = render_professional_compact_brief_from_context(context)
    return json.dumps(brief, ensure_ascii=False)


def test_valid_provider_candidate_bundle_builds_professional_analyst_context():
    context = build_professional_analyst_context(
        _bundle(),
        internal_analysis_brief=_internal_brief(),
    )

    assert context["schema_version"] == PROFESSIONAL_ANALYST_CONTEXT_SCHEMA_VERSION
    assert context["stock_code"] == "600406"
    assert context["revenue_present"] is True
    assert context["profit_present"] is True


def test_context_contains_financial_signal_variables():
    context = build_professional_analyst_context(_bundle())
    signal = context["financial_signal"]

    assert signal["schema_version"] == PROFESSIONAL_ANALYST_FINANCIAL_SIGNAL_SCHEMA_VERSION
    assert context["revenue_direction_hint"]
    assert context["profit_direction_hint"]
    assert context["revenue_profit_consistency"]
    assert context["margin_present"] is True
    assert context["debt_ratio_present"] is True
    assert context["roe_present"] is True


def test_context_contains_operating_quality_variables():
    context = build_professional_analyst_context(_bundle())
    signal = context["operating_quality_signal"]

    assert signal["schema_version"] == PROFESSIONAL_ANALYST_QUALITY_SIGNAL_SCHEMA_VERSION
    assert context["operating_cashflow_present"] is True
    assert context["profit_cashflow_match"]
    assert context["receivables_present"] is True
    assert context["receivables_pressure_hint"]
    assert context["inventory_present"] is True
    assert context["turnover_or_working_capital_hint"]


def test_context_contains_key_variables_and_risk_flags():
    context = build_professional_analyst_context(
        _bundle(),
        internal_analysis_brief=_internal_brief(),
    )

    assert "经营现金流与利润匹配度" in context["key_variables"]
    assert "应收账款回款效率" in context["key_variables"]
    assert context["risk_flags"]


def test_deterministic_renderer_returns_professional_analyst_renderer_output():
    context = build_professional_analyst_context(_bundle())
    output = default_deterministic_analyst_renderer(context)

    assert output["schema_version"] == PROFESSIONAL_ANALYST_RENDERER_OUTPUT_SCHEMA_VERSION
    assert output["sections"]["overall_view"]
    assert output["key_variables"]


def test_renderer_output_has_clear_professional_judgments():
    text = _render_text(_bundle())

    assert "总体基本面判断" in text
    assert "经营质量" in text
    assert "现金流对利润形成支撑" in text
    assert "核心风险" in text
    assert "关键变量" not in text or "key_variables" in text


def test_renderer_output_varies_when_cashflow_supports_or_lags_profit():
    supported = _render_text(_with_metric(_bundle(), "n_cashflow_act", 180))
    lagging = _render_text(_with_metric(_bundle(), "n_cashflow_act", 50))

    assert supported != lagging
    assert "现金流对利润形成支撑" in supported
    assert "利润表现强于现金流，经营质量判断需要打折" in lagging


def test_cashflow_support_produces_positive_operating_quality_wording():
    text = _render_text(_with_metric(_bundle(), "n_cashflow_act", 180))

    assert "现金流对利润形成支撑" in text
    assert "偏稳" in text


def test_cashflow_lag_produces_discounted_operating_quality_wording():
    text = _render_text(_with_metric(_bundle(), "n_cashflow_act", 50))

    assert "经营质量判断需要打折" in text
    assert "需要打折" in text


def test_high_receivables_pressure_produces_receivables_risk_wording():
    bundle = _with_metric(_bundle(), "accounts_receiv", 450)
    text = _render_text(bundle)

    assert "应收扩张会削弱利润质量判断" in text


def test_margin_present_produces_profitability_quality_wording():
    text = _render_text(_bundle())

    assert "盈利能力具备较好观察起点" in text


def test_injected_analyst_renderer_is_accepted():
    context = build_professional_analyst_context(_bundle())

    def fake_renderer(renderer_context):
        return {
            "schema_version": PROFESSIONAL_ANALYST_RENDERER_OUTPUT_SCHEMA_VERSION,
            "sections": {
                key: "自定义分析师判断聚焦收入、利润、现金流、应收和资产结构之间的匹配关系。"
                for key in (
                    "overall_view",
                    "business_view",
                    "financial_view",
                    "operating_quality_view",
                    "industry_macro_view",
                    "risk_view",
                )
            },
            "key_variables": [
                "收入与利润同步性",
                "经营现金流与利润匹配度",
                "应收账款回款效率",
                "利润率结构",
                "资产负债结构",
            ],
            "conclusion_boundary": "结论边界聚焦基本面质量和经营韧性，不展开估值区间或操作动作。",
            "not_for_trading_advice": True,
        }

    brief = render_professional_compact_brief_from_context(
        context,
        analyst_renderer=fake_renderer,
    )

    assert brief["overall_view"]["view"].startswith("自定义分析师判断")


def test_injected_analyst_renderer_receives_sanitized_context_only():
    captured = {}
    context = build_professional_analyst_context(
        _bundle(),
        internal_analysis_brief=_internal_brief(),
    )

    def fake_renderer(renderer_context):
        captured["context"] = copy.deepcopy(renderer_context)
        return default_deterministic_analyst_renderer(renderer_context)

    render_professional_compact_brief_from_context(
        context,
        analyst_renderer=fake_renderer,
    )

    serialized = json.dumps(captured["context"], ensure_ascii=False)
    assert "revenue_present" in captured["context"]
    for forbidden in (
        "provider",
        "provider_candidate",
        "pending_official_verification",
        "official_verified_count",
        "not_official_verified",
        "source_table",
        "candidate_items",
        "backend_grounding_summary",
        "待核验",
        "数据缺口",
        "推理",
    ):
        assert forbidden not in serialized


def test_integration_builds_professional_compact_brief_from_existing_pilot_path():
    result = _build()

    assert result["professional_compact_brief"]["schema_version"] == (
        PROFESSIONAL_ANALYST_COMPACT_BRIEF_SCHEMA_VERSION
    )
    assert "现金流对利润形成支撑" in json.dumps(
        result["professional_compact_brief"],
        ensure_ascii=False,
    )


def test_no_engineering_labels_in_professional_output():
    brief = render_professional_compact_brief_from_context(
        build_professional_analyst_context(_bundle())
    )

    assert_no_user_visible_engineering_labels(brief)


def test_no_user_responsibility_shifting_phrases():
    text = _render_text(_bundle())

    for forbidden in ("用户自行", "自行判断", "自行跟踪", "需要用户", "建议用户", "请结合"):
        assert forbidden not in text


def test_no_trading_advice():
    text = _render_text(_bundle()).casefold()

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


def test_input_bundle_not_mutated():
    bundle = _bundle()
    before = copy.deepcopy(bundle)

    context = build_professional_analyst_context(
        bundle,
        internal_analysis_brief=_internal_brief(),
    )
    render_professional_compact_brief_from_context(context)

    assert bundle == before


def test_non_600406_sample_passes():
    bundle = _bundle(
        _FakeFinancialClient(ts_code="000001.SZ"),
        stock_code="000001",
        ts_code="000001.SZ",
        company_name_hint="Sample Company",
    )

    context = build_professional_analyst_context(bundle)
    brief = render_professional_compact_brief_from_context(context)

    assert brief["stock_code"] == "000001"
    assert brief["ts_code"] == "000001.SZ"


def test_signal_builders_are_available_independently():
    bundle = _bundle()

    financial = build_financial_signal_context(bundle)
    quality = build_operating_quality_signal_context(bundle)

    assert financial["revenue_present"] is True
    assert quality["operating_cashflow_present"] is True
