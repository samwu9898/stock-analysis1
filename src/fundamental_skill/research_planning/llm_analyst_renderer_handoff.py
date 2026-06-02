# -*- coding: utf-8 -*-
"""LLM analyst renderer handoff contract with a deterministic fake renderer.

The module defines the model-facing context and renderer output boundary used
before a real LLM is introduced.  It stays fully local and in-memory.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
import json
import re
from typing import Any

from .professional_compact_brief_quality import (
    PROFESSIONAL_ANALYST_RENDERER_OUTPUT_SCHEMA_VERSION,
    render_professional_compact_brief_from_context,
    validate_professional_analyst_context,
    validate_professional_analyst_renderer_output,
)


LLM_ANALYST_HANDOFF_CONTEXT_SCHEMA_VERSION = "llm_analyst_handoff_context.v1"
LLM_ANALYST_PROMPT_CONTRACT_SCHEMA_VERSION = "llm_analyst_prompt_contract.v1"
LLM_ANALYST_RENDERER_OUTPUT_SCHEMA_VERSION = "llm_analyst_renderer_output.v1"
FAKE_LLM_ANALYST_RENDERER_RESULT_SCHEMA_VERSION = (
    "fake_llm_analyst_renderer_result.v1"
)

LLM_ANALYST_REQUIRED_OUTPUT_SECTIONS = (
    "overall_view",
    "business_view",
    "financial_view",
    "operating_quality_view",
    "industry_macro_view",
    "risk_view",
    "key_variables",
    "conclusion_boundary",
    "source_note",
)

_LLM_RENDERED_SECTION_KEYS = (
    "overall_view",
    "business_view",
    "financial_view",
    "operating_quality_view",
    "industry_macro_view",
    "risk_view",
)

_MODEL_CONTEXT_FIELDS = {
    "schema_version",
    "stock_code",
    "ts_code",
    "company_name_hint",
    "periods",
    "latest_period",
    "derived_signals",
    "key_variables",
    "risk_flags",
    "conclusion_boundary",
    "data_source_note",
    "model_data_boundary",
    "evidence_confidence_hint",
    "not_for_trading_advice",
}

_DERIVED_SIGNAL_FIELDS = {
    "revenue",
    "profit",
    "cashflow",
    "receivables",
    "margin",
    "debt",
    "roe",
}

_SIGNAL_FIELDS = {
    "present",
    "latest_value",
    "direction_hint",
    "quality_hint",
}

_PROMPT_CONTRACT_FIELDS = {
    "schema_version",
    "context_schema_version",
    "output_schema_version",
    "required_output_sections",
    "output_contract",
    "forbidden_output_markers",
    "trading_advice_allowed",
    "artifact_generation_allowed",
    "external_api_allowed",
    "not_for_trading_advice",
}

_OUTPUT_CONTRACT_FIELDS = {
    "overall_view",
    "business_view",
    "financial_view",
    "operating_quality_view",
    "industry_macro_view",
    "risk_view",
    "key_variables",
    "conclusion_boundary",
    "source_note",
    "not_for_trading_advice",
}

_LLM_RENDERER_OUTPUT_FIELDS = {
    "schema_version",
    "sections",
    "key_variables",
    "conclusion_boundary",
    "source_note",
    "not_for_trading_advice",
}

_ALLOWED_EXACT_TEXTS = {
    "Tushare",
    "not_for_trading_advice",
}

_FORBIDDEN_WORD_MARKERS = {"buy", "sell", "hold", "portfolio", "position"}

_LLM_HANDOFF_FORBIDDEN_MARKERS = (
    "token",
    ".env",
    "tushare_token",
    "api_key",
    "api token",
    "secret",
    "credential",
    "authorization",
    "bearer",
    "backend trace",
    "backend_grounding_summary",
    "raw provider row",
    "raw provider rows",
    "raw provider queue",
    "raw_http",
    "raw HTTP",
    "full locator hit",
    "full locator hits",
    "page",
    "page_number",
    "snippet",
    "source_url",
    "sha256",
    "cache_path",
    "artifact path",
    "output path",
    "output_path",
    "fixture path",
    "fixture_path",
    "accepted manifest path",
    "accepted_manifest_path",
    "provider_candidate",
    "pending official verification",
    "pending_official_verification",
    "pending verification",
    "official verification",
    "official_verified_count",
    "provider_official_conflict",
    "official_metric_fact",
    "provider vs official",
    "reconciliation",
    "Report V1 artifact",
    "HTML artifact",
    "report_v1",
    "html artifact",
    "buy",
    "sell",
    "hold",
    "target price",
    "portfolio",
    "position",
    "technical signal",
    "trading advice",
    "investment advice",
)

_LLM_HANDOFF_FORBIDDEN_CJK_MARKERS = (
    "待核验",
    "数据缺口",
    "推理",
    "官方核验",
    "尚未完成官方核验",
    "候选数据",
    "证据状态",
    "口径一致性",
    "用户自行",
    "自行判断",
    "自行跟踪",
    "需要用户",
    "建议用户",
    "买入",
    "卖出",
    "持有",
    "目标价",
    "仓位",
    "组合",
    "技术信号",
    "交易建议",
    "投资建议",
    "正式研报",
    "官方指标事实",
    "指标核验",
    "一致性核验",
    "第几页",
    "页码",
    "原文片段",
    "来源链接",
    "哈希",
    "缓存路径",
)

_USER_VISIBLE_ENGINEERING_LABELS = (
    "provider_candidate",
    "pending_official_verification",
    "pending verification",
    "official verification",
    "official_verified_count",
    "data gap",
    "evidence locator",
    "anchor map",
    "artifact cached",
    "reconciliation",
    "provider vs official",
    "待核验",
    "数据缺口",
    "推理",
    "官方核验",
    "尚未完成官方核验",
    "候选数据",
    "证据状态",
    "口径一致性",
    "用户自行",
    "自行判断",
    "自行跟踪",
    "需要用户",
    "建议用户",
)

_SECRET_LIKE_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._-]{8,}\b", re.IGNORECASE),
)


class LLMAnalystRendererHandoffError(ValueError):
    """Raised when the LLM analyst handoff boundary fails closed."""


def build_model_facing_analyst_context(
    professional_analyst_context: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the sanitized context that may be handed to an analyst model."""

    ctx = validate_professional_analyst_context(professional_analyst_context)
    assert_no_llm_handoff_forbidden_markers(ctx)
    financial = ctx["financial_signal"]
    quality = ctx["operating_quality_signal"]
    result = {
        "schema_version": LLM_ANALYST_HANDOFF_CONTEXT_SCHEMA_VERSION,
        "stock_code": ctx["stock_code"],
        "ts_code": ctx["ts_code"],
        "company_name_hint": ctx["company_name_hint"],
        "periods": list(ctx["periods"]),
        "latest_period": ctx["latest_period"],
        "derived_signals": {
            "revenue": _signal(
                present=ctx["revenue_present"],
                latest_value=financial.get("revenue_value"),
                direction_hint=ctx["revenue_direction_hint"],
                quality_hint=ctx["revenue_profit_consistency"],
            ),
            "profit": _signal(
                present=ctx["profit_present"],
                latest_value=financial.get("profit_value"),
                direction_hint=ctx["profit_direction_hint"],
                quality_hint=ctx["revenue_profit_consistency"],
            ),
            "cashflow": _signal(
                present=ctx["operating_cashflow_present"],
                latest_value=quality.get("operating_cashflow_value"),
                direction_hint=ctx["profit_cashflow_match"],
                quality_hint=ctx["profit_cashflow_match"],
            ),
            "receivables": _signal(
                present=ctx["receivables_present"],
                latest_value=quality.get("accounts_receiv_value"),
                direction_hint=ctx["receivables_pressure_hint"],
                quality_hint=ctx["receivables_pressure_hint"],
            ),
            "margin": _signal(
                present=ctx["margin_present"],
                latest_value=financial.get("netprofit_margin_value"),
                direction_hint=ctx["margin_quality_hint"],
                quality_hint=ctx["margin_quality_hint"],
            ),
            "debt": _signal(
                present=ctx["debt_ratio_present"],
                latest_value=financial.get("debt_to_assets_value"),
                direction_hint=ctx["balance_sheet_pressure_hint"],
                quality_hint=ctx["balance_sheet_pressure_hint"],
            ),
            "roe": _signal(
                present=ctx["roe_present"],
                latest_value=financial.get("roe_value"),
                direction_hint=ctx["capital_efficiency_hint"],
                quality_hint=ctx["capital_efficiency_hint"],
            ),
        },
        "key_variables": list(ctx["key_variables"]),
        "risk_flags": list(ctx["risk_flags"]),
        "conclusion_boundary": ctx["conclusion_boundary"],
        "data_source_note": "Tushare",
        "model_data_boundary": (
            "financial data is sourced from Tushare and should be used for "
            "fundamental analysis with cautious confidence"
        ),
        "evidence_confidence_hint": (
            "use cautious confidence and keep conclusions inside the "
            "fundamental-analysis boundary"
        ),
        "not_for_trading_advice": True,
    }
    return validate_model_facing_analyst_context(result)


def validate_model_facing_analyst_context(
    context: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the sanitized model-facing handoff context."""

    source = _require_mapping(context, "model_facing_analyst_context")
    unsupported = sorted(set(source) - _MODEL_CONTEXT_FIELDS)
    if unsupported:
        raise LLMAnalystRendererHandoffError(
            f"model_facing_analyst_context contains unsupported keys: {unsupported}"
        )
    _require_fields(
        source,
        tuple(sorted(_MODEL_CONTEXT_FIELDS)),
        "model_facing_analyst_context",
    )
    result = deepcopy(dict(source))
    if result["schema_version"] != LLM_ANALYST_HANDOFF_CONTEXT_SCHEMA_VERSION:
        raise LLMAnalystRendererHandoffError(
            "model_facing_analyst_context schema_version invalid"
        )
    _require_optional_string(result["stock_code"], "model_context.stock_code")
    _require_optional_string(result["ts_code"], "model_context.ts_code")
    _require_optional_string(
        result["company_name_hint"],
        "model_context.company_name_hint",
    )
    _require_string_list(result["periods"], "model_context.periods")
    _require_optional_string(result["latest_period"], "model_context.latest_period")
    result["derived_signals"] = _validate_derived_signals(
        result["derived_signals"]
    )
    _require_string_list(result["key_variables"], "model_context.key_variables")
    if len(result["key_variables"]) < 5:
        raise LLMAnalystRendererHandoffError(
            "model_context.key_variables must contain professional variables"
        )
    _require_string_list(result["risk_flags"], "model_context.risk_flags")
    _require_non_empty_string(
        result["conclusion_boundary"],
        "model_context.conclusion_boundary",
    )
    if result["data_source_note"] != "Tushare":
        raise LLMAnalystRendererHandoffError(
            "model_context.data_source_note must be Tushare"
        )
    _require_non_empty_string(
        result["model_data_boundary"],
        "model_context.model_data_boundary",
    )
    _require_non_empty_string(
        result["evidence_confidence_hint"],
        "model_context.evidence_confidence_hint",
    )
    _require_true(
        result["not_for_trading_advice"],
        "model_context.not_for_trading_advice",
    )
    assert_no_llm_handoff_forbidden_markers(result)
    assert_no_user_visible_engineering_labels(result)
    return result


def build_llm_analyst_prompt_contract(
    model_facing_context: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the explicit prompt/output contract for an analyst model."""

    validate_model_facing_analyst_context(model_facing_context)
    contract = {
        "schema_version": LLM_ANALYST_PROMPT_CONTRACT_SCHEMA_VERSION,
        "context_schema_version": LLM_ANALYST_HANDOFF_CONTEXT_SCHEMA_VERSION,
        "output_schema_version": LLM_ANALYST_RENDERER_OUTPUT_SCHEMA_VERSION,
        "required_output_sections": list(LLM_ANALYST_REQUIRED_OUTPUT_SECTIONS),
        "output_contract": {
            "overall_view": "overall fundamental judgment",
            "business_view": "business logic judgment",
            "financial_view": "financial performance judgment",
            "operating_quality_view": "operating quality judgment",
            "industry_macro_view": "industry and macro transmission judgment",
            "risk_view": "core risk judgment",
            "key_variables": "professional fundamental variables",
            "conclusion_boundary": "analysis boundary without action language",
            "source_note": "Tushare source note",
            "not_for_trading_advice": True,
        },
        "forbidden_output_markers": [
            "buy",
            "sell",
            "hold",
            "target price",
            "portfolio",
            "position",
            "technical signal",
            "trading advice",
            "用户自行判断",
            "用户自行跟踪",
            "需要用户结合",
            "建议用户",
            "待核验",
            "数据缺口",
            "推理",
            "provider candidate",
            "pending verification",
            "official verification",
            "page/snippet/source_url/sha256/cache_path",
            "Report V1 artifact",
            "HTML artifact",
        ],
        "trading_advice_allowed": False,
        "artifact_generation_allowed": False,
        "external_api_allowed": False,
        "not_for_trading_advice": True,
    }
    return validate_llm_analyst_prompt_contract(contract)


def validate_llm_analyst_prompt_contract(
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the prompt contract while allowing its forbidden marker list."""

    source = _require_mapping(contract, "llm_analyst_prompt_contract")
    unsupported = sorted(set(source) - _PROMPT_CONTRACT_FIELDS)
    if unsupported:
        raise LLMAnalystRendererHandoffError(
            f"llm_analyst_prompt_contract contains unsupported keys: {unsupported}"
        )
    _require_fields(source, tuple(sorted(_PROMPT_CONTRACT_FIELDS)), "prompt_contract")
    result = deepcopy(dict(source))
    if result["schema_version"] != LLM_ANALYST_PROMPT_CONTRACT_SCHEMA_VERSION:
        raise LLMAnalystRendererHandoffError("prompt_contract schema_version invalid")
    if result["context_schema_version"] != LLM_ANALYST_HANDOFF_CONTEXT_SCHEMA_VERSION:
        raise LLMAnalystRendererHandoffError(
            "prompt_contract context_schema_version invalid"
        )
    if result["output_schema_version"] != LLM_ANALYST_RENDERER_OUTPUT_SCHEMA_VERSION:
        raise LLMAnalystRendererHandoffError(
            "prompt_contract output_schema_version invalid"
        )
    sections = _require_string_list(
        result["required_output_sections"],
        "prompt_contract.required_output_sections",
    )
    missing_sections = [
        section for section in LLM_ANALYST_REQUIRED_OUTPUT_SECTIONS if section not in sections
    ]
    if missing_sections:
        raise LLMAnalystRendererHandoffError(
            f"prompt_contract missing required output sections: {missing_sections}"
        )
    output_contract = _require_mapping(
        result["output_contract"],
        "prompt_contract.output_contract",
    )
    unsupported_contract_fields = sorted(set(output_contract) - _OUTPUT_CONTRACT_FIELDS)
    if unsupported_contract_fields:
        raise LLMAnalystRendererHandoffError(
            "prompt_contract.output_contract contains unsupported keys: "
            f"{unsupported_contract_fields}"
        )
    _require_fields(
        output_contract,
        tuple(sorted(_OUTPUT_CONTRACT_FIELDS)),
        "prompt_contract.output_contract",
    )
    for key, value in output_contract.items():
        if key == "not_for_trading_advice":
            _require_true(value, "prompt_contract.output_contract.not_for_trading_advice")
        elif key == "key_variables":
            _require_non_empty_string(value, f"prompt_contract.output_contract.{key}")
        else:
            _require_non_empty_string(value, f"prompt_contract.output_contract.{key}")
    _require_string_list(
        result["forbidden_output_markers"],
        "prompt_contract.forbidden_output_markers",
    )
    for flag in (
        "trading_advice_allowed",
        "artifact_generation_allowed",
        "external_api_allowed",
    ):
        if result[flag] is not False:
            raise LLMAnalystRendererHandoffError(f"prompt_contract.{flag} must be false")
    _require_true(
        result["not_for_trading_advice"],
        "prompt_contract.not_for_trading_advice",
    )
    return result


def fake_llm_analyst_renderer(
    model_facing_context: Mapping[str, Any],
) -> dict[str, Any]:
    """Return deterministic professional analysis in the LLM output contract."""

    ctx = validate_model_facing_analyst_context(model_facing_context)
    company = ctx["company_name_hint"] or ctx["stock_code"] or "该公司"
    signals = ctx["derived_signals"]
    revenue = signals["revenue"]
    profit = signals["profit"]
    cashflow = signals["cashflow"]
    receivables = signals["receivables"]
    margin = signals["margin"]
    debt = signals["debt"]
    roe = signals["roe"]
    key_variables = _dedupe_preserve_order(ctx["key_variables"])[:8]
    risk_sentence = _risk_sentence(ctx["risk_flags"])
    sections = {
        "overall_view": (
            f"{company}的基本面分析重心应放在收入、利润、现金流和资产结构的相互印证上。"
            f"{revenue['quality_hint']}，{cashflow['quality_hint']}，"
            f"{debt['quality_hint']}。这些变量共同决定当前质量判断更偏经营韧性分析，"
            "而不是单点财务指标的线性外推。"
        ),
        "business_view": (
            f"{company}的业务判断需要沿着主营结构、订单交付、回款效率和利润率传导展开。"
            "若收入质量能够通过回款和现金转化体现，业务逻辑的可解释性会更强；"
            "若订单或回款节奏弱化，利润表现的持续性会被压低。"
        ),
        "financial_view": (
            f"财务表现的主线是收入方向、利润方向和盈利能力是否形成同向支撑。"
            f"{revenue['direction_hint']}，{profit['direction_hint']}，"
            f"{margin['quality_hint']}，{roe['quality_hint']}。"
            "因此财务质量需要同时看增长质量、利润率结构和资本效率。"
        ),
        "operating_quality_view": (
            f"经营质量主要取决于利润向现金的转化，以及应收和营运资本占用。"
            f"{cashflow['quality_hint']}；{receivables['quality_hint']}。"
            "现金流越能覆盖利润，基本面判断越扎实；营运资本占用上升时，质量判断需要收紧。"
        ),
        "industry_macro_view": (
            "行业与宏观变量需要落到订单、交付、回款和利润率四个经营环节。"
            "外部环境只有传导为收入确认节奏、毛利结构或现金回收能力变化，"
            "才会实质改变公司基本面判断。"
        ),
        "risk_view": (
            "核心风险来自收入、利润、现金流、应收和资产负债结构之间的不匹配。"
            f"{risk_sentence}"
            "若利润强于现金流、应收占用加重或杠杆压力上升，经营韧性的判断应更谨慎。"
        ),
    }
    output = {
        "schema_version": LLM_ANALYST_RENDERER_OUTPUT_SCHEMA_VERSION,
        "sections": sections,
        "key_variables": key_variables,
        "conclusion_boundary": ctx["conclusion_boundary"],
        "source_note": "数据来源：Tushare。分析仅限基本面质量、经营韧性和风险边界。",
        "not_for_trading_advice": True,
    }
    return validate_llm_analyst_renderer_output(output)


def validate_llm_analyst_renderer_output(
    output: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate fake or future LLM renderer output before public conversion."""

    source = _require_mapping(output, "llm_analyst_renderer_output")
    unsupported = sorted(set(source) - _LLM_RENDERER_OUTPUT_FIELDS)
    if unsupported:
        raise LLMAnalystRendererHandoffError(
            f"llm_analyst_renderer_output contains unsupported keys: {unsupported}"
        )
    _require_fields(
        source,
        tuple(sorted(_LLM_RENDERER_OUTPUT_FIELDS)),
        "llm_analyst_renderer_output",
    )
    result = deepcopy(dict(source))
    if result["schema_version"] != LLM_ANALYST_RENDERER_OUTPUT_SCHEMA_VERSION:
        raise LLMAnalystRendererHandoffError(
            "llm_analyst_renderer_output schema_version invalid"
        )
    sections = _require_mapping(
        result["sections"],
        "llm_analyst_renderer_output.sections",
    )
    unsupported_sections = sorted(set(sections) - set(_LLM_RENDERED_SECTION_KEYS))
    if unsupported_sections:
        raise LLMAnalystRendererHandoffError(
            "llm_analyst_renderer_output.sections contains unsupported keys: "
            f"{unsupported_sections}"
        )
    _require_fields(
        sections,
        _LLM_RENDERED_SECTION_KEYS,
        "llm_analyst_renderer_output.sections",
    )
    result["sections"] = {}
    for key in _LLM_RENDERED_SECTION_KEYS:
        view = _require_non_empty_string(
            sections[key],
            f"llm_analyst_renderer_output.sections.{key}",
        )
        if len(view) < 24:
            raise LLMAnalystRendererHandoffError(
                f"llm_analyst_renderer_output.sections.{key} is too thin"
            )
        result["sections"][key] = view
    _require_string_list(
        result["key_variables"],
        "llm_analyst_renderer_output.key_variables",
    )
    if len(result["key_variables"]) < 5:
        raise LLMAnalystRendererHandoffError(
            "llm_analyst_renderer_output.key_variables must contain professional variables"
        )
    _require_non_empty_string(
        result["conclusion_boundary"],
        "llm_analyst_renderer_output.conclusion_boundary",
    )
    _require_non_empty_string(
        result["source_note"],
        "llm_analyst_renderer_output.source_note",
    )
    _require_true(
        result["not_for_trading_advice"],
        "llm_analyst_renderer_output.not_for_trading_advice",
    )
    assert_no_llm_handoff_forbidden_markers(result)
    assert_no_user_visible_engineering_labels(result)
    return result


def fake_llm_professional_analyst_renderer(
    context: Mapping[str, Any],
) -> dict[str, Any]:
    """Adapter that lets the existing compact brief renderer call fake LLM."""

    model_context = build_model_facing_analyst_context(context)
    llm_output = fake_llm_analyst_renderer(model_context)
    return validate_professional_analyst_renderer_output(
        _professional_renderer_output_from_llm_output(llm_output)
    )


def render_professional_brief_with_fake_llm(
    context: Mapping[str, Any],
) -> dict[str, Any]:
    """Render the professional compact brief through the fake LLM handoff."""

    validate_professional_analyst_context(context)
    return render_professional_compact_brief_from_context(
        context,
        analyst_renderer=fake_llm_professional_analyst_renderer,
    )


def assert_no_llm_handoff_forbidden_markers(value: Any) -> None:
    """Reject secrets, backend traces, raw locators, artifacts, and advice."""

    finding = _find_forbidden_marker(value)
    if finding:
        raise LLMAnalystRendererHandoffError(
            f"llm analyst renderer handoff safety violation: {finding}"
        )


def assert_no_user_visible_engineering_labels(value: Any) -> None:
    """Reject engineering labels and responsibility-shifting user text."""

    serialized = json.dumps(value, ensure_ascii=False)
    lowered = serialized.casefold()
    separator = _normalize_separator_text(serialized)
    normalized = _normalise_marker(serialized)
    for marker in _USER_VISIBLE_ENGINEERING_LABELS:
        marker_lower = marker.casefold()
        marker_normalized = _normalise_marker(marker)
        if (
            marker_lower in lowered
            or _normalize_separator_text(marker) in separator
            or (marker_normalized and marker_normalized in normalized)
            or marker in serialized
        ):
            raise LLMAnalystRendererHandoffError(
                "llm analyst renderer output contains user-visible engineering label"
            )


def _professional_renderer_output_from_llm_output(
    output: Mapping[str, Any],
) -> dict[str, Any]:
    validated = validate_llm_analyst_renderer_output(output)
    return {
        "schema_version": PROFESSIONAL_ANALYST_RENDERER_OUTPUT_SCHEMA_VERSION,
        "sections": deepcopy(validated["sections"]),
        "key_variables": list(validated["key_variables"]),
        "conclusion_boundary": validated["conclusion_boundary"],
        "not_for_trading_advice": True,
    }


def _signal(
    *,
    present: bool,
    latest_value: Any,
    direction_hint: str,
    quality_hint: str,
) -> dict[str, Any]:
    return {
        "present": present,
        "latest_value": latest_value if _is_number(latest_value) else None,
        "direction_hint": direction_hint,
        "quality_hint": quality_hint,
    }


def _validate_derived_signals(value: Any) -> dict[str, Any]:
    signals = _require_mapping(value, "model_context.derived_signals")
    unsupported = sorted(set(signals) - _DERIVED_SIGNAL_FIELDS)
    if unsupported:
        raise LLMAnalystRendererHandoffError(
            f"model_context.derived_signals contains unsupported keys: {unsupported}"
        )
    _require_fields(
        signals,
        tuple(sorted(_DERIVED_SIGNAL_FIELDS)),
        "model_context.derived_signals",
    )
    result: dict[str, Any] = {}
    for signal_name in _DERIVED_SIGNAL_FIELDS:
        signal = _require_mapping(
            signals[signal_name],
            f"model_context.derived_signals.{signal_name}",
        )
        unsupported_signal_fields = sorted(set(signal) - _SIGNAL_FIELDS)
        if unsupported_signal_fields:
            raise LLMAnalystRendererHandoffError(
                f"model_context.derived_signals.{signal_name} contains unsupported "
                f"keys: {unsupported_signal_fields}"
            )
        _require_fields(
            signal,
            tuple(sorted(_SIGNAL_FIELDS)),
            f"model_context.derived_signals.{signal_name}",
        )
        copied = deepcopy(dict(signal))
        _require_bool(copied["present"], f"model_context.{signal_name}.present")
        if copied["latest_value"] is not None and not _is_number(copied["latest_value"]):
            raise LLMAnalystRendererHandoffError(
                f"model_context.{signal_name}.latest_value must be numeric or null"
            )
        _require_non_empty_string(
            copied["direction_hint"],
            f"model_context.{signal_name}.direction_hint",
        )
        _require_non_empty_string(
            copied["quality_hint"],
            f"model_context.{signal_name}.quality_hint",
        )
        result[signal_name] = copied
    return result


def _find_forbidden_marker(value: Any) -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text not in _ALLOWED_EXACT_TEXTS:
                key_finding = _text_forbidden_marker(key_text)
                if key_finding:
                    return key_finding
            child_finding = _find_forbidden_marker(child)
            if child_finding:
                return child_finding
        return None
    if isinstance(value, (list, tuple, set)):
        for item in value:
            item_finding = _find_forbidden_marker(item)
            if item_finding:
                return item_finding
        return None
    if isinstance(value, str):
        return _text_forbidden_marker(value)
    return None


def _text_forbidden_marker(value: str) -> str | None:
    if value in _ALLOWED_EXACT_TEXTS:
        return None
    if _looks_like_secret_text(value):
        return "secret_like_string"
    lowered = value.casefold()
    separator_normalized = _normalize_separator_text(value)
    normalized = _normalise_marker(value)
    for marker in _LLM_HANDOFF_FORBIDDEN_MARKERS:
        marker_lower = marker.casefold()
        marker_separator = _normalize_separator_text(marker)
        marker_normalized = _normalise_marker(marker)
        if marker_lower == ".env":
            if ".env" in lowered:
                return "forbidden_marker"
            continue
        if marker_normalized in _FORBIDDEN_WORD_MARKERS:
            if re.search(
                rf"(?<![a-z0-9]){re.escape(marker_normalized)}(?![a-z0-9])",
                normalized,
            ):
                return "forbidden_marker"
            continue
        if (
            marker_lower in lowered
            or marker_separator in separator_normalized
            or marker_normalized in normalized
        ):
            return "forbidden_marker"
    if any(marker in value for marker in _LLM_HANDOFF_FORBIDDEN_CJK_MARKERS):
        return "forbidden_marker"
    return None


def _risk_sentence(risk_flags: list[str]) -> str:
    clean_flags = [
        flag for flag in risk_flags if isinstance(flag, str) and flag.strip()
    ][:4]
    if not clean_flags:
        return "当前重点观察收入、利润、现金流和营运资本之间的匹配。"
    return "；".join(clean_flags) + "。"


def _dedupe_preserve_order(values: Iterable[Any]) -> list[Any]:
    result: list[Any] = []
    seen: set[str] = set()
    for value in values:
        marker = repr(value)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(value)
    return result


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise LLMAnalystRendererHandoffError(f"{field} must be a mapping")
    return value


def _require_fields(value: Mapping[str, Any], fields: tuple[str, ...], path: str) -> None:
    missing = [field for field in fields if field not in value]
    if missing:
        raise LLMAnalystRendererHandoffError(
            f"{path} missing required fields: {missing}"
        )


def _require_optional_string(value: Any, path: str) -> None:
    if value is not None and not isinstance(value, str):
        raise LLMAnalystRendererHandoffError(f"{path} must be string or null")


def _require_non_empty_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LLMAnalystRendererHandoffError(f"{path} must be a non-empty string")
    return value


def _require_string_list(value: Any, path: str) -> list[str]:
    if not isinstance(value, list):
        raise LLMAnalystRendererHandoffError(f"{path} must be a list")
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise LLMAnalystRendererHandoffError(f"{path}[{index}] must be string")
    return value


def _require_bool(value: Any, path: str) -> None:
    if not isinstance(value, bool):
        raise LLMAnalystRendererHandoffError(f"{path} must be bool")


def _require_true(value: Any, path: str) -> None:
    if value is not True:
        raise LLMAnalystRendererHandoffError(f"{path} must be true")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _normalise_marker(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().casefold()).strip("_")


def _normalize_separator_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[_-]+", " ", value.strip().casefold())).strip()


def _looks_like_secret_text(value: str) -> bool:
    for pattern in _SECRET_LIKE_PATTERNS:
        if pattern.search(value):
            return True
    compact = value.strip()
    if len(compact) < 32 or re.search(r"\s", compact):
        return False
    if compact in _ALLOWED_EXACT_TEXTS:
        return False
    has_upper = any(char.isupper() for char in compact)
    has_lower = any(char.islower() for char in compact)
    has_digit = any(char.isdigit() for char in compact)
    return has_upper and has_lower and has_digit


__all__ = [
    "FAKE_LLM_ANALYST_RENDERER_RESULT_SCHEMA_VERSION",
    "LLM_ANALYST_HANDOFF_CONTEXT_SCHEMA_VERSION",
    "LLM_ANALYST_PROMPT_CONTRACT_SCHEMA_VERSION",
    "LLM_ANALYST_RENDERER_OUTPUT_SCHEMA_VERSION",
    "LLM_ANALYST_REQUIRED_OUTPUT_SECTIONS",
    "LLMAnalystRendererHandoffError",
    "assert_no_llm_handoff_forbidden_markers",
    "assert_no_user_visible_engineering_labels",
    "build_llm_analyst_prompt_contract",
    "build_model_facing_analyst_context",
    "fake_llm_analyst_renderer",
    "fake_llm_professional_analyst_renderer",
    "render_professional_brief_with_fake_llm",
    "validate_llm_analyst_prompt_contract",
    "validate_llm_analyst_renderer_output",
    "validate_model_facing_analyst_context",
]
