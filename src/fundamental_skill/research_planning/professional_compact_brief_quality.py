# -*- coding: utf-8 -*-
"""Professional analyst context and renderer boundary for compact briefs.

The module converts an internal Tushare candidate bundle into a sanitized
analyst context, then renders a professional user-facing compact brief without
calling an external model or writing artifacts.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from copy import deepcopy
import json
import re
from typing import Any


PROFESSIONAL_ANALYST_CONTEXT_SCHEMA_VERSION = "professional_analyst_context.v1"
PROFESSIONAL_ANALYST_FINANCIAL_SIGNAL_SCHEMA_VERSION = (
    "professional_analyst_financial_signal.v1"
)
PROFESSIONAL_ANALYST_QUALITY_SIGNAL_SCHEMA_VERSION = (
    "professional_analyst_quality_signal.v1"
)
PROFESSIONAL_ANALYST_INDUSTRY_MACRO_SIGNAL_SCHEMA_VERSION = (
    "professional_analyst_industry_macro_signal.v1"
)
PROFESSIONAL_ANALYST_RENDERER_OUTPUT_SCHEMA_VERSION = (
    "professional_analyst_renderer_output.v1"
)
PROFESSIONAL_ANALYST_COMPACT_BRIEF_SCHEMA_VERSION = (
    "professional_analyst_compact_brief.v1"
)
PROFESSIONAL_ANALYST_COMPACT_BRIEF_SECTION_SCHEMA_VERSION = (
    "professional_analyst_compact_brief_section.v1"
)

PROFESSIONAL_BRIEF_SECTION_KEYS = (
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

_RENDERED_SECTION_KEYS = (
    "overall_view",
    "business_view",
    "financial_view",
    "operating_quality_view",
    "industry_macro_view",
    "risk_view",
)

_CONTEXT_FIELDS = {
    "schema_version",
    "stock_code",
    "ts_code",
    "company_name_hint",
    "periods",
    "latest_period",
    "financial_signal",
    "operating_quality_signal",
    "industry_macro_signal",
    "revenue_present",
    "revenue_direction_hint",
    "profit_present",
    "profit_direction_hint",
    "revenue_profit_consistency",
    "operating_cashflow_present",
    "profit_cashflow_match",
    "receivables_present",
    "receivables_pressure_hint",
    "margin_present",
    "margin_quality_hint",
    "debt_ratio_present",
    "balance_sheet_pressure_hint",
    "roe_present",
    "capital_efficiency_hint",
    "inventory_present",
    "turnover_or_working_capital_hint",
    "key_variables",
    "risk_flags",
    "conclusion_boundary",
}

_FINANCIAL_SIGNAL_FIELDS = {
    "schema_version",
    "latest_period",
    "revenue_present",
    "revenue_value",
    "revenue_direction_hint",
    "profit_present",
    "profit_value",
    "profit_direction_hint",
    "revenue_profit_consistency",
    "margin_present",
    "grossprofit_margin_value",
    "netprofit_margin_value",
    "margin_quality_hint",
    "debt_ratio_present",
    "debt_to_assets_value",
    "balance_sheet_pressure_hint",
    "roe_present",
    "roe_value",
    "capital_efficiency_hint",
    "key_variables",
    "risk_flags",
}

_QUALITY_SIGNAL_FIELDS = {
    "schema_version",
    "latest_period",
    "operating_cashflow_present",
    "operating_cashflow_value",
    "profit_value",
    "profit_cashflow_match",
    "receivables_present",
    "accounts_receiv_value",
    "receivables_pressure_hint",
    "inventory_present",
    "inventories_value",
    "ar_turn_value",
    "inv_turn_value",
    "turnover_or_working_capital_hint",
    "quality_bias",
    "key_variables",
    "risk_flags",
}

_INDUSTRY_SIGNAL_FIELDS = {
    "schema_version",
    "business_variables",
    "industry_transmission_hint",
    "macro_boundary_hint",
    "key_variables",
    "risk_flags",
}

_RENDERER_OUTPUT_FIELDS = {
    "schema_version",
    "sections",
    "key_variables",
    "conclusion_boundary",
    "not_for_trading_advice",
}

_PROFESSIONAL_BRIEF_FIELDS = {
    "schema_version",
    "stock_code",
    "ts_code",
    "company_name_hint",
    "title",
    *PROFESSIONAL_BRIEF_SECTION_KEYS,
    "not_for_trading_advice",
}

_PROFESSIONAL_SECTION_FIELDS = {
    "schema_version",
    "section_id",
    "title",
    "view",
    "not_for_trading_advice",
}

_RAW_OR_FILE_KEYS = {
    "accepted_manifest",
    "accepted_manifest_path",
    "cache_path",
    "env",
    "env_file",
    "fixture_path",
    "fixtures_path",
    "output_path",
    "pdf_bytes",
    "raw_http_response",
    "raw_provider_queue",
    "raw_tushare_provider_result",
    "source_url",
    "tushare_token",
    "tushare_token_path",
}

_SECRET_KEYS = {
    "api_key",
    "api_token",
    "auth",
    "authorization",
    "credential",
    "credentials",
    "secret",
    "token",
}

_ALLOWED_EXACT_TEXTS = {
    "TUSHARE_TOKEN",
    "not_for_trading_advice",
}

_FORBIDDEN_MARKERS = (
    "token",
    ".env",
    "tushare_token",
    "backend trace",
    "backend_grounding_summary",
    "provider_candidate",
    "pending official verification",
    "pending_official_verification",
    "official verification",
    "provider_official_conflict",
    "official_metric_fact",
    "provider-official reconciliation",
    "provider vs official",
    "reconciliation",
    "Report V1 artifact",
    "HTML artifact",
    "accepted manifest write",
    "manifest write",
    "output baseline write",
    "output artifact path",
    "output write",
    "fixture write",
    "buy",
    "sell",
    "hold",
    "target price",
    "portfolio",
    "position",
    "technical signal",
    "trading advice",
    "investment advice",
    "page_number",
    "snippet",
    "source_url",
    "sha256",
    "cache_path",
)

_FORBIDDEN_CJK_MARKERS = (
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
    "投资建议",
    "正式研报",
    "写入fixture",
    "写入accepted manifest",
    "写入manifest",
    "读取token",
    "读取.env",
    "读取tushare_token",
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
    "provider",
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

_WORD_MARKERS = {"token", "buy", "sell", "hold", "portfolio", "position"}
_SECRET_LIKE_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._-]{8,}\b", re.IGNORECASE),
)

_BUSINESS_VARIABLE_CANDIDATES = (
    ("主营构成", "主营构成"),
    ("产品结构", "产品结构"),
    ("客户结构", "客户结构"),
    ("毛利率", "毛利率结构"),
    ("利润率", "利润率结构"),
    ("现金流", "现金流质量"),
    ("应收账款", "应收账款回款效率"),
    ("应收", "应收账款回款效率"),
    ("存货", "存货和周转效率"),
    ("订单", "订单变化"),
    ("招标", "招标节奏"),
    ("交付", "交付节奏"),
    ("回款", "回款节奏"),
)

_DEFAULT_BUSINESS_VARIABLES = (
    "主营构成",
    "订单交付",
    "回款节奏",
    "利润率结构",
    "现金流质量",
)


class ProfessionalCompactBriefQualityError(ValueError):
    """Raised when professional compact brief quality checks fail closed."""


AnalystRenderer = Callable[[Mapping[str, Any]], Mapping[str, Any]]


def build_professional_analyst_context(
    provider_candidate_bundle: Mapping[str, Any],
    *,
    internal_analysis_brief: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build sanitized analyst variables from provider metrics and internal brief."""

    bundle = _validated_bundle_input(provider_candidate_bundle)
    financial_signal = build_financial_signal_context(bundle)
    operating_quality_signal = build_operating_quality_signal_context(bundle)
    industry_macro_signal = build_industry_macro_signal_context(
        bundle,
        internal_analysis_brief=internal_analysis_brief,
    )
    key_variables = _dedupe_preserve_order(
        [
            *financial_signal["key_variables"],
            *operating_quality_signal["key_variables"],
            *industry_macro_signal["key_variables"],
        ]
    )
    risk_flags = _dedupe_preserve_order(
        [
            *financial_signal["risk_flags"],
            *operating_quality_signal["risk_flags"],
            *industry_macro_signal["risk_flags"],
        ]
    )
    if not risk_flags:
        risk_flags = ["收入、利润、现金流和周转变量需要保持匹配"]

    context = {
        "schema_version": PROFESSIONAL_ANALYST_CONTEXT_SCHEMA_VERSION,
        "stock_code": _optional_string(bundle.get("stock_code")),
        "ts_code": _optional_string(bundle.get("ts_code")),
        "company_name_hint": _optional_string(bundle.get("company_name_hint")),
        "periods": _periods_from_bundle(bundle),
        "latest_period": financial_signal["latest_period"]
        or operating_quality_signal["latest_period"],
        "financial_signal": financial_signal,
        "operating_quality_signal": operating_quality_signal,
        "industry_macro_signal": industry_macro_signal,
        "revenue_present": financial_signal["revenue_present"],
        "revenue_direction_hint": financial_signal["revenue_direction_hint"],
        "profit_present": financial_signal["profit_present"],
        "profit_direction_hint": financial_signal["profit_direction_hint"],
        "revenue_profit_consistency": financial_signal[
            "revenue_profit_consistency"
        ],
        "operating_cashflow_present": operating_quality_signal[
            "operating_cashflow_present"
        ],
        "profit_cashflow_match": operating_quality_signal["profit_cashflow_match"],
        "receivables_present": operating_quality_signal["receivables_present"],
        "receivables_pressure_hint": operating_quality_signal[
            "receivables_pressure_hint"
        ],
        "margin_present": financial_signal["margin_present"],
        "margin_quality_hint": financial_signal["margin_quality_hint"],
        "debt_ratio_present": financial_signal["debt_ratio_present"],
        "balance_sheet_pressure_hint": financial_signal[
            "balance_sheet_pressure_hint"
        ],
        "roe_present": financial_signal["roe_present"],
        "capital_efficiency_hint": financial_signal["capital_efficiency_hint"],
        "inventory_present": operating_quality_signal["inventory_present"],
        "turnover_or_working_capital_hint": operating_quality_signal[
            "turnover_or_working_capital_hint"
        ],
        "key_variables": key_variables,
        "risk_flags": risk_flags,
        "conclusion_boundary": (
            "当前更适合用经营韧性、现金流质量、回款效率和资产负债结构框架评估公司，"
            "不展开估值区间、价格方向或操作层面的动作。"
        ),
    }
    return validate_professional_analyst_context(context)


def build_financial_signal_context(
    provider_candidate_bundle: Mapping[str, Any],
) -> dict[str, Any]:
    """Build financial-performance signal variables from candidate metrics."""

    bundle = _validated_bundle_input(provider_candidate_bundle)
    metrics = _latest_metric_map(bundle)
    latest_period = _latest_period_with_items(bundle)
    revenue = metrics.get("revenue")
    profit = _first_metric(metrics, "n_income_attr_p", "total_profit")
    gross_margin = metrics.get("grossprofit_margin")
    net_margin = metrics.get("netprofit_margin")
    debt_to_assets = metrics.get("debt_to_assets")
    roe = metrics.get("roe")

    revenue_present = _is_number(revenue)
    profit_present = _is_number(profit)
    margin_present = _is_number(gross_margin) or _is_number(net_margin)
    debt_ratio_present = _is_number(debt_to_assets)
    roe_present = _is_number(roe)

    revenue_direction_hint, revenue_direction_code = _direction_hint(
        _metric_series(bundle, "revenue"),
        "收入",
    )
    profit_direction_hint, profit_direction_code = _direction_hint(
        _metric_series(bundle, "n_income_attr_p")
        or _metric_series(bundle, "total_profit"),
        "利润",
    )

    signal = {
        "schema_version": PROFESSIONAL_ANALYST_FINANCIAL_SIGNAL_SCHEMA_VERSION,
        "latest_period": latest_period,
        "revenue_present": revenue_present,
        "revenue_value": revenue if revenue_present else None,
        "revenue_direction_hint": revenue_direction_hint,
        "profit_present": profit_present,
        "profit_value": profit if profit_present else None,
        "profit_direction_hint": profit_direction_hint,
        "revenue_profit_consistency": _revenue_profit_consistency(
            revenue_present=revenue_present,
            profit_present=profit_present,
            revenue_direction_code=revenue_direction_code,
            profit_direction_code=profit_direction_code,
        ),
        "margin_present": margin_present,
        "grossprofit_margin_value": gross_margin if _is_number(gross_margin) else None,
        "netprofit_margin_value": net_margin if _is_number(net_margin) else None,
        "margin_quality_hint": _margin_quality_hint(gross_margin, net_margin),
        "debt_ratio_present": debt_ratio_present,
        "debt_to_assets_value": debt_to_assets if debt_ratio_present else None,
        "balance_sheet_pressure_hint": _balance_sheet_pressure_hint(
            debt_to_assets
        ),
        "roe_present": roe_present,
        "roe_value": roe if roe_present else None,
        "capital_efficiency_hint": _capital_efficiency_hint(roe),
        "key_variables": _dedupe_preserve_order(
            [
                "收入与利润同步性",
                "利润率结构",
                "资产负债结构",
                "资本效率",
            ]
        ),
        "risk_flags": _financial_risk_flags(
            revenue_present=revenue_present,
            profit_present=profit_present,
            consistency=_revenue_profit_consistency(
                revenue_present=revenue_present,
                profit_present=profit_present,
                revenue_direction_code=revenue_direction_code,
                profit_direction_code=profit_direction_code,
            ),
            margin_hint=_margin_quality_hint(gross_margin, net_margin),
            balance_hint=_balance_sheet_pressure_hint(debt_to_assets),
        ),
    }
    return _validate_financial_signal(signal)


def build_operating_quality_signal_context(
    provider_candidate_bundle: Mapping[str, Any],
) -> dict[str, Any]:
    """Build operating-quality variables from cashflow and working capital."""

    bundle = _validated_bundle_input(provider_candidate_bundle)
    metrics = _latest_metric_map(bundle)
    latest_period = _latest_period_with_items(bundle)
    revenue = metrics.get("revenue")
    profit = _first_metric(metrics, "n_income_attr_p", "total_profit")
    cashflow = metrics.get("n_cashflow_act")
    receivables = metrics.get("accounts_receiv")
    inventories = metrics.get("inventories")
    ar_turn = metrics.get("ar_turn")
    inv_turn = metrics.get("inv_turn")

    profit_cashflow_match = _profit_cashflow_match(profit, cashflow)
    receivables_pressure_hint = _receivables_pressure_hint(receivables, revenue)
    turnover_hint = _turnover_or_working_capital_hint(
        inventories=inventories,
        revenue=revenue,
        ar_turn=ar_turn,
        inv_turn=inv_turn,
    )
    risk_flags = _operating_risk_flags(
        profit_cashflow_match=profit_cashflow_match,
        receivables_pressure_hint=receivables_pressure_hint,
        turnover_hint=turnover_hint,
    )
    signal = {
        "schema_version": PROFESSIONAL_ANALYST_QUALITY_SIGNAL_SCHEMA_VERSION,
        "latest_period": latest_period,
        "operating_cashflow_present": _is_number(cashflow),
        "operating_cashflow_value": cashflow if _is_number(cashflow) else None,
        "profit_value": profit if _is_number(profit) else None,
        "profit_cashflow_match": profit_cashflow_match,
        "receivables_present": _is_number(receivables),
        "accounts_receiv_value": receivables if _is_number(receivables) else None,
        "receivables_pressure_hint": receivables_pressure_hint,
        "inventory_present": _is_number(inventories),
        "inventories_value": inventories if _is_number(inventories) else None,
        "ar_turn_value": ar_turn if _is_number(ar_turn) else None,
        "inv_turn_value": inv_turn if _is_number(inv_turn) else None,
        "turnover_or_working_capital_hint": turnover_hint,
        "quality_bias": _quality_bias(profit_cashflow_match, risk_flags),
        "key_variables": _dedupe_preserve_order(
            [
                "经营现金流与利润匹配度",
                "应收账款回款效率",
                "存货和周转效率",
                "现金转化能力",
            ]
        ),
        "risk_flags": risk_flags,
    }
    return _validate_quality_signal(signal)


def build_industry_macro_signal_context(
    provider_candidate_bundle: Mapping[str, Any],
    *,
    internal_analysis_brief: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build industry and macro transmission variables without leaking labels."""

    _validated_bundle_input(provider_candidate_bundle)
    business_variables = _business_variables_from_internal_brief(
        internal_analysis_brief
    )
    signal = {
        "schema_version": PROFESSIONAL_ANALYST_INDUSTRY_MACRO_SIGNAL_SCHEMA_VERSION,
        "business_variables": business_variables,
        "industry_transmission_hint": (
            "行业与宏观变量不能停留在主题层面，必须体现到订单、交付、回款和利润率。"
        ),
        "macro_boundary_hint": (
            "外部环境变化只有进入主营构成、订单节奏、交付能力和回款效率，"
            "才会改变基本面质量判断。"
        ),
        "key_variables": _dedupe_preserve_order(
            [
                *business_variables,
                "行业订单与招标节奏",
                "交付和回款传导",
            ]
        ),
        "risk_flags": ["行业传导若停留在主题层面，不能支撑公司质量改善判断"],
    }
    return _validate_industry_signal(signal)


def render_professional_compact_brief_from_context(
    context: Mapping[str, Any],
    *,
    analyst_renderer: AnalystRenderer | str | None = None,
) -> dict[str, Any]:
    """Render a professional compact brief from sanitized analyst context."""

    validated_context = validate_professional_analyst_context(context)
    renderer = _resolve_analyst_renderer(analyst_renderer)
    renderer_context = _sanitized_context_for_renderer(validated_context)
    renderer_output = validate_professional_analyst_renderer_output(
        renderer(deepcopy(renderer_context))
    )
    company = (
        validated_context["company_name_hint"]
        or validated_context["stock_code"]
        or "该公司"
    )
    sections = renderer_output["sections"]
    brief = {
        "schema_version": PROFESSIONAL_ANALYST_COMPACT_BRIEF_SCHEMA_VERSION,
        "stock_code": validated_context["stock_code"],
        "ts_code": validated_context["ts_code"],
        "company_name_hint": validated_context["company_name_hint"],
        "title": f"{company}基本面专业简报",
        "overall_view": _build_professional_section(
            "overall_view",
            "总体基本面判断",
            sections["overall_view"],
        ),
        "business_view": _build_professional_section(
            "business_view",
            "公司业务逻辑判断",
            sections["business_view"],
        ),
        "financial_view": _build_professional_section(
            "financial_view",
            "财务表现判断",
            sections["financial_view"],
        ),
        "operating_quality_view": _build_professional_section(
            "operating_quality_view",
            "经营质量判断",
            sections["operating_quality_view"],
        ),
        "industry_macro_view": _build_professional_section(
            "industry_macro_view",
            "行业和宏观传导判断",
            sections["industry_macro_view"],
        ),
        "risk_view": _build_professional_section(
            "risk_view",
            "核心风险判断",
            sections["risk_view"],
        ),
        "key_variables": list(renderer_output["key_variables"]),
        "conclusion_boundary": renderer_output["conclusion_boundary"],
        "source_note": "数据来源：Tushare。",
        "not_for_trading_advice": True,
    }
    return _validate_professional_brief(brief)


def render_professional_compact_brief_with_llm_handoff(
    context: Mapping[str, Any],
    *,
    renderer: str = "fake",
) -> dict[str, Any]:
    """Render a professional compact brief through the fake LLM handoff."""

    if renderer not in {"fake", "fake_llm"}:
        raise ProfessionalCompactBriefQualityError(
            "llm handoff renderer must be fake"
        )
    return render_professional_compact_brief_from_context(
        context,
        analyst_renderer="fake_llm",
    )


def default_deterministic_analyst_renderer(
    context: Mapping[str, Any],
) -> dict[str, Any]:
    """Render deterministic professional judgments without external APIs."""

    ctx = validate_professional_analyst_context(context)
    company = ctx["company_name_hint"] or ctx["stock_code"] or "该公司"
    financial = ctx["financial_signal"]
    quality = ctx["operating_quality_signal"]
    industry = ctx["industry_macro_signal"]
    risk_sentence = _risk_sentence(ctx["risk_flags"])
    business_variables = "、".join(industry["business_variables"][:5])

    sections = {
        "overall_view": (
            f"{company}当前基本面判断应放在经营韧性和现金流质量框架下展开。"
            f"{financial['revenue_profit_consistency']}，{quality['profit_cashflow_match']}；"
            f"{financial['balance_sheet_pressure_hint']}。整体看，判断重心不是单一增长项，"
            "而是收入、利润、现金流和资产结构能否形成相互支撑。"
        ),
        "business_view": (
            "公司业务逻辑需要落到主营构成、订单交付、客户回款和利润率的闭环。"
            f"当前可纳入分析的经营变量包括{business_variables}，这些变量决定收入质量能否"
            "转化为持续利润和现金回收。"
        ),
        "financial_view": (
            f"财务表现的主线是收入、利润和盈利能力三者是否同向。"
            f"{financial['revenue_direction_hint']}，{financial['profit_direction_hint']}；"
            f"{financial['margin_quality_hint']}，{financial['capital_efficiency_hint']}。"
            "若收入与利润同步性保持，财务质量判断会更扎实；若二者背离，利润质量需要打折。"
        ),
        "operating_quality_view": (
            f"{quality['profit_cashflow_match']}；{quality['receivables_pressure_hint']}；"
            f"{quality['turnover_or_working_capital_hint']}。"
            f"因此经营质量当前呈现{quality['quality_bias']}，核心是利润能否稳定转化为现金。"
        ),
        "industry_macro_view": (
            f"{industry['industry_transmission_hint']}"
            f"{industry['macro_boundary_hint']}"
            "行业变量只有传导到订单、交付、回款和利润率，才会改变公司基本面判断。"
        ),
        "risk_view": (
            "核心风险在于收入、利润、现金流、应收和存货之间出现背离。"
            f"{risk_sentence}"
            "当利润表现强于现金流，或应收与存货占用上升时，经营质量判断必须收紧。"
        ),
    }
    output = {
        "schema_version": PROFESSIONAL_ANALYST_RENDERER_OUTPUT_SCHEMA_VERSION,
        "sections": sections,
        "key_variables": list(ctx["key_variables"]),
        "conclusion_boundary": ctx["conclusion_boundary"],
        "not_for_trading_advice": True,
    }
    return validate_professional_analyst_renderer_output(output)


def _resolve_analyst_renderer(
    analyst_renderer: AnalystRenderer | str | None,
) -> AnalystRenderer:
    if analyst_renderer is None:
        return default_deterministic_analyst_renderer
    if analyst_renderer == "fake_llm":
        from .llm_analyst_renderer_handoff import (
            fake_llm_professional_analyst_renderer,
        )

        return fake_llm_professional_analyst_renderer
    if isinstance(analyst_renderer, str):
        raise ProfessionalCompactBriefQualityError(
            f"unsupported analyst_renderer: {analyst_renderer}"
        )
    if not callable(analyst_renderer):
        raise ProfessionalCompactBriefQualityError(
            "analyst_renderer must be callable, fake_llm, or null"
        )
    return analyst_renderer


def validate_professional_analyst_context(
    context: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate a sanitized professional analyst context."""

    source = _require_mapping(context, "professional_analyst_context")
    unsupported = sorted(set(source) - _CONTEXT_FIELDS)
    if unsupported:
        raise ProfessionalCompactBriefQualityError(
            f"professional_analyst_context contains unsupported keys: {unsupported}"
        )
    _require_fields(source, tuple(sorted(_CONTEXT_FIELDS)), "professional_analyst_context")
    result = deepcopy(dict(source))
    if result["schema_version"] != PROFESSIONAL_ANALYST_CONTEXT_SCHEMA_VERSION:
        raise ProfessionalCompactBriefQualityError(
            "professional_analyst_context schema_version invalid"
        )
    _require_optional_string(result["stock_code"], "context.stock_code")
    _require_optional_string(result["ts_code"], "context.ts_code")
    _require_optional_string(result["company_name_hint"], "context.company_name_hint")
    _require_string_list(result["periods"], "context.periods")
    _require_optional_string(result["latest_period"], "context.latest_period")
    result["financial_signal"] = _validate_financial_signal(
        result["financial_signal"]
    )
    result["operating_quality_signal"] = _validate_quality_signal(
        result["operating_quality_signal"]
    )
    result["industry_macro_signal"] = _validate_industry_signal(
        result["industry_macro_signal"]
    )
    for key in (
        "revenue_present",
        "profit_present",
        "operating_cashflow_present",
        "receivables_present",
        "margin_present",
        "debt_ratio_present",
        "roe_present",
        "inventory_present",
    ):
        _require_bool(result[key], f"context.{key}")
    for key in (
        "revenue_direction_hint",
        "profit_direction_hint",
        "revenue_profit_consistency",
        "profit_cashflow_match",
        "receivables_pressure_hint",
        "margin_quality_hint",
        "balance_sheet_pressure_hint",
        "capital_efficiency_hint",
        "turnover_or_working_capital_hint",
        "conclusion_boundary",
    ):
        _require_non_empty_string(result[key], f"context.{key}")
    _require_string_list(result["key_variables"], "context.key_variables")
    _require_string_list(result["risk_flags"], "context.risk_flags")
    if len(result["key_variables"]) < 5:
        raise ProfessionalCompactBriefQualityError(
            "context.key_variables must contain professional variables"
        )
    _assert_no_secret_like_anywhere(result)
    assert_no_user_visible_engineering_labels(result)
    return result


def validate_professional_analyst_renderer_output(
    output: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate renderer output before converting it into the public brief."""

    source = _require_mapping(output, "professional_analyst_renderer_output")
    unsupported = sorted(set(source) - _RENDERER_OUTPUT_FIELDS)
    if unsupported:
        raise ProfessionalCompactBriefQualityError(
            f"professional_analyst_renderer_output contains unsupported keys: {unsupported}"
        )
    _require_fields(source, tuple(sorted(_RENDERER_OUTPUT_FIELDS)), "renderer_output")
    result = deepcopy(dict(source))
    if result["schema_version"] != PROFESSIONAL_ANALYST_RENDERER_OUTPUT_SCHEMA_VERSION:
        raise ProfessionalCompactBriefQualityError("renderer output schema_version invalid")
    sections = _require_mapping(result["sections"], "renderer_output.sections")
    unsupported_sections = sorted(set(sections) - set(_RENDERED_SECTION_KEYS))
    if unsupported_sections:
        raise ProfessionalCompactBriefQualityError(
            f"renderer_output.sections contains unsupported keys: {unsupported_sections}"
        )
    _require_fields(sections, _RENDERED_SECTION_KEYS, "renderer_output.sections")
    result["sections"] = {}
    for key in _RENDERED_SECTION_KEYS:
        view = _require_non_empty_string(sections[key], f"renderer_output.{key}")
        if len(view) < 24:
            raise ProfessionalCompactBriefQualityError(
                f"renderer_output.{key} is too thin"
            )
        result["sections"][key] = view
    _require_string_list(result["key_variables"], "renderer_output.key_variables")
    if len(result["key_variables"]) < 5:
        raise ProfessionalCompactBriefQualityError(
            "renderer_output.key_variables must contain professional variables"
        )
    _require_non_empty_string(
        result["conclusion_boundary"],
        "renderer_output.conclusion_boundary",
    )
    _require_true(
        result["not_for_trading_advice"],
        "renderer_output.not_for_trading_advice",
    )
    assert_no_professional_brief_quality_forbidden_markers(result)
    assert_no_user_visible_engineering_labels(result)
    return result


def assert_no_professional_brief_quality_forbidden_markers(value: Any) -> None:
    """Reject secrets, backend traces, engineering labels, and advice markers."""

    finding = _find_forbidden_marker(value)
    if finding:
        raise ProfessionalCompactBriefQualityError(
            f"professional compact brief quality safety violation: {finding}"
        )


def assert_no_user_visible_engineering_labels(value: Any) -> None:
    """Reject backend or responsibility-shifting labels in user-visible text."""

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
            raise ProfessionalCompactBriefQualityError(
                "professional brief contains user-visible engineering label"
            )


def _validated_bundle_input(value: Mapping[str, Any]) -> dict[str, Any]:
    source = _require_mapping(value, "provider_candidate_bundle")
    _reject_bytes(source, "provider_candidate_bundle")
    _reject_raw_or_secret_keys(source, "provider_candidate_bundle")
    _assert_no_secret_like_anywhere(source)
    copied = deepcopy(dict(source))
    items = copied.get("candidate_items")
    if not isinstance(items, list) or not items:
        raise ProfessionalCompactBriefQualityError(
            "provider_candidate_bundle.candidate_items must be a non-empty list"
        )
    return copied


def _validate_financial_signal(value: Any) -> dict[str, Any]:
    signal = _require_mapping(value, "financial_signal")
    unsupported = sorted(set(signal) - _FINANCIAL_SIGNAL_FIELDS)
    if unsupported:
        raise ProfessionalCompactBriefQualityError(
            f"financial_signal contains unsupported keys: {unsupported}"
        )
    _require_fields(signal, tuple(sorted(_FINANCIAL_SIGNAL_FIELDS)), "financial_signal")
    result = deepcopy(dict(signal))
    if result["schema_version"] != PROFESSIONAL_ANALYST_FINANCIAL_SIGNAL_SCHEMA_VERSION:
        raise ProfessionalCompactBriefQualityError("financial_signal schema_version invalid")
    _require_optional_string(result["latest_period"], "financial_signal.latest_period")
    for key in (
        "revenue_present",
        "profit_present",
        "margin_present",
        "debt_ratio_present",
        "roe_present",
    ):
        _require_bool(result[key], f"financial_signal.{key}")
    for key in (
        "revenue_direction_hint",
        "profit_direction_hint",
        "revenue_profit_consistency",
        "margin_quality_hint",
        "balance_sheet_pressure_hint",
        "capital_efficiency_hint",
    ):
        _require_non_empty_string(result[key], f"financial_signal.{key}")
    _require_string_list(result["key_variables"], "financial_signal.key_variables")
    _require_string_list(result["risk_flags"], "financial_signal.risk_flags")
    return result


def _validate_quality_signal(value: Any) -> dict[str, Any]:
    signal = _require_mapping(value, "operating_quality_signal")
    unsupported = sorted(set(signal) - _QUALITY_SIGNAL_FIELDS)
    if unsupported:
        raise ProfessionalCompactBriefQualityError(
            f"operating_quality_signal contains unsupported keys: {unsupported}"
        )
    _require_fields(
        signal,
        tuple(sorted(_QUALITY_SIGNAL_FIELDS)),
        "operating_quality_signal",
    )
    result = deepcopy(dict(signal))
    if result["schema_version"] != PROFESSIONAL_ANALYST_QUALITY_SIGNAL_SCHEMA_VERSION:
        raise ProfessionalCompactBriefQualityError(
            "operating_quality_signal schema_version invalid"
        )
    _require_optional_string(
        result["latest_period"],
        "operating_quality_signal.latest_period",
    )
    for key in (
        "operating_cashflow_present",
        "receivables_present",
        "inventory_present",
    ):
        _require_bool(result[key], f"operating_quality_signal.{key}")
    for key in (
        "profit_cashflow_match",
        "receivables_pressure_hint",
        "turnover_or_working_capital_hint",
        "quality_bias",
    ):
        _require_non_empty_string(result[key], f"operating_quality_signal.{key}")
    _require_string_list(result["key_variables"], "operating_quality_signal.key_variables")
    _require_string_list(result["risk_flags"], "operating_quality_signal.risk_flags")
    return result


def _validate_industry_signal(value: Any) -> dict[str, Any]:
    signal = _require_mapping(value, "industry_macro_signal")
    unsupported = sorted(set(signal) - _INDUSTRY_SIGNAL_FIELDS)
    if unsupported:
        raise ProfessionalCompactBriefQualityError(
            f"industry_macro_signal contains unsupported keys: {unsupported}"
        )
    _require_fields(
        signal,
        tuple(sorted(_INDUSTRY_SIGNAL_FIELDS)),
        "industry_macro_signal",
    )
    result = deepcopy(dict(signal))
    if (
        result["schema_version"]
        != PROFESSIONAL_ANALYST_INDUSTRY_MACRO_SIGNAL_SCHEMA_VERSION
    ):
        raise ProfessionalCompactBriefQualityError(
            "industry_macro_signal schema_version invalid"
        )
    _require_string_list(result["business_variables"], "industry.business_variables")
    _require_non_empty_string(
        result["industry_transmission_hint"],
        "industry.industry_transmission_hint",
    )
    _require_non_empty_string(
        result["macro_boundary_hint"],
        "industry.macro_boundary_hint",
    )
    _require_string_list(result["key_variables"], "industry.key_variables")
    _require_string_list(result["risk_flags"], "industry.risk_flags")
    return result


def _validate_professional_brief(value: Any) -> dict[str, Any]:
    brief = _require_mapping(value, "professional_compact_brief")
    unsupported = sorted(set(brief) - _PROFESSIONAL_BRIEF_FIELDS)
    if unsupported:
        raise ProfessionalCompactBriefQualityError(
            f"professional_compact_brief contains unsupported keys: {unsupported}"
        )
    _require_fields(
        brief,
        tuple(sorted(_PROFESSIONAL_BRIEF_FIELDS)),
        "professional_compact_brief",
    )
    result = deepcopy(dict(brief))
    if result["schema_version"] != PROFESSIONAL_ANALYST_COMPACT_BRIEF_SCHEMA_VERSION:
        raise ProfessionalCompactBriefQualityError(
            "professional_compact_brief schema_version invalid"
        )
    _require_optional_string(result["stock_code"], "professional.stock_code")
    _require_optional_string(result["ts_code"], "professional.ts_code")
    _require_optional_string(
        result["company_name_hint"],
        "professional.company_name_hint",
    )
    _require_non_empty_string(result["title"], "professional.title")
    for key in _RENDERED_SECTION_KEYS:
        result[key] = _validate_professional_section(result[key], key)
    _require_string_list(result["key_variables"], "professional.key_variables")
    if len(result["key_variables"]) < 5:
        raise ProfessionalCompactBriefQualityError(
            "key_variables must contain professional variables"
        )
    _require_non_empty_string(
        result["conclusion_boundary"],
        "professional.conclusion_boundary",
    )
    _require_non_empty_string(result["source_note"], "professional.source_note")
    _require_true(result["not_for_trading_advice"], "professional.not_for_trading_advice")
    assert_no_professional_brief_quality_forbidden_markers(result)
    assert_no_user_visible_engineering_labels(result)
    return result


def _build_professional_section(
    section_id: str,
    title: str,
    view: str,
) -> dict[str, Any]:
    section = {
        "schema_version": PROFESSIONAL_ANALYST_COMPACT_BRIEF_SECTION_SCHEMA_VERSION,
        "section_id": section_id,
        "title": title,
        "view": view,
        "not_for_trading_advice": True,
    }
    return _validate_professional_section(section, f"professional.{section_id}")


def _validate_professional_section(value: Any, path: str) -> dict[str, Any]:
    section = _require_mapping(value, path)
    unsupported = sorted(set(section) - _PROFESSIONAL_SECTION_FIELDS)
    if unsupported:
        raise ProfessionalCompactBriefQualityError(
            f"{path} contains unsupported keys: {unsupported}"
        )
    _require_fields(section, tuple(sorted(_PROFESSIONAL_SECTION_FIELDS)), path)
    result = deepcopy(dict(section))
    if result["schema_version"] != (
        PROFESSIONAL_ANALYST_COMPACT_BRIEF_SECTION_SCHEMA_VERSION
    ):
        raise ProfessionalCompactBriefQualityError(f"{path}.schema_version invalid")
    _require_non_empty_string(result["section_id"], f"{path}.section_id")
    _require_non_empty_string(result["title"], f"{path}.title")
    view = _require_non_empty_string(result["view"], f"{path}.view")
    if len(view) < 24:
        raise ProfessionalCompactBriefQualityError(f"{path}.view is too thin")
    _require_true(result["not_for_trading_advice"], f"{path}.not_for_trading_advice")
    assert_no_professional_brief_quality_forbidden_markers(result)
    assert_no_user_visible_engineering_labels(result)
    return result


def _periods_from_bundle(bundle: Mapping[str, Any]) -> list[str]:
    periods = _string_values(bundle.get("periods"))
    if periods:
        return periods
    return _dedupe_preserve_order(
        str(item.get("period"))
        for item in bundle.get("candidate_items", [])
        if isinstance(item, Mapping) and item.get("period")
    )


def _latest_period_with_items(bundle: Mapping[str, Any]) -> str | None:
    periods = _periods_from_bundle(bundle)
    items = [item for item in bundle.get("candidate_items", []) if isinstance(item, Mapping)]
    for period in reversed(periods):
        if any(item.get("period") == period for item in items):
            return period
    return periods[-1] if periods else None


def _latest_metric_map(bundle: Mapping[str, Any]) -> dict[str, Any]:
    latest_period = _latest_period_with_items(bundle)
    if latest_period is None:
        return {}
    return {
        str(item.get("candidate_key")): item.get("candidate_value")
        for item in bundle.get("candidate_items", [])
        if isinstance(item, Mapping) and item.get("period") == latest_period
    }


def _metric_series(bundle: Mapping[str, Any], metric_key: str) -> list[Any]:
    by_period: dict[str, Any] = {}
    for item in bundle.get("candidate_items", []):
        if not isinstance(item, Mapping):
            continue
        if item.get("candidate_key") == metric_key:
            by_period[str(item.get("period"))] = item.get("candidate_value")
    return [by_period.get(period) for period in _periods_from_bundle(bundle)]


def _first_metric(metrics: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = metrics.get(key)
        if value is not None:
            return value
    return None


def _direction_hint(series: list[Any], label: str) -> tuple[str, str]:
    numeric_values = [value for value in series if _is_number(value)]
    if not numeric_values:
        return f"{label}尚未形成可观察数值", "absent"
    latest = numeric_values[-1]
    if len(numeric_values) == 1:
        return f"{label}已有单期观察值", "single"
    previous = numeric_values[-2]
    if previous == 0:
        if latest > 0:
            return f"{label}较前期改善", "up"
        if latest < 0:
            return f"{label}较前期转弱", "down"
        return f"{label}较前期基本平稳", "flat"
    change_ratio = (latest - previous) / abs(previous)
    if change_ratio > 0.03:
        return f"{label}较前期改善", "up"
    if change_ratio < -0.03:
        return f"{label}较前期回落", "down"
    return f"{label}较前期基本平稳", "flat"


def _revenue_profit_consistency(
    *,
    revenue_present: bool,
    profit_present: bool,
    revenue_direction_code: str,
    profit_direction_code: str,
) -> str:
    if not revenue_present or not profit_present:
        return "收入与利润同步性还不足以展开强判断"
    positive_or_flat = {"up", "flat", "single"}
    if (
        revenue_direction_code in positive_or_flat
        and profit_direction_code in positive_or_flat
    ):
        return "收入与利润具备同步观察基础"
    if revenue_direction_code == profit_direction_code:
        return "收入与利润方向一致，但质量仍取决于现金转化"
    return "收入与利润方向出现背离"


def _margin_quality_hint(gross_margin: Any, net_margin: Any) -> str:
    gross = gross_margin if _is_number(gross_margin) else None
    net = net_margin if _is_number(net_margin) else None
    if gross is None and net is None:
        return "盈利能力尚未形成可观察利润率变量"
    if (gross is not None and gross >= 30) or (net is not None and net >= 10):
        return "盈利能力具备较好观察起点"
    if (gross is not None and gross < 15) or (net is not None and net < 5):
        return "利润率偏薄会压低盈利质量判断"
    return "利润率处于可观察区间，盈利质量需要结合现金转化判断"


def _balance_sheet_pressure_hint(debt_to_assets: Any) -> str:
    if not _is_number(debt_to_assets):
        return "资产负债结构尚未形成明确压力变量"
    if debt_to_assets <= 40:
        return "资产负债结构压力较低"
    if debt_to_assets >= 65:
        return "资产负债结构压力偏高"
    return "资产负债结构处于中性区间"


def _capital_efficiency_hint(roe: Any) -> str:
    if not _is_number(roe):
        return "资本效率尚未形成稳定观察变量"
    if roe >= 15:
        return "资本效率表现较强"
    if roe <= 5:
        return "资本效率仍需要经营周期继续验证"
    return "资本效率处于可观察区间"


def _profit_cashflow_match(profit: Any, cashflow: Any) -> str:
    if _is_number(profit) and _is_number(cashflow):
        if cashflow >= profit:
            return "现金流对利润形成支撑"
        if cashflow >= 0:
            return "利润表现强于现金流，经营质量判断需要打折"
        return "现金流弱于利润并形成经营质量压力"
    if _is_number(cashflow):
        return "现金流已有观察基础，但利润匹配度需要结合利润变量判断"
    return "现金流与利润匹配度尚未形成明确判断"


def _receivables_pressure_hint(receivables: Any, revenue: Any) -> str:
    if not _is_number(receivables):
        return "应收账款尚未形成明确压力变量"
    if _is_number(revenue) and revenue:
        ratio = receivables / abs(revenue)
        if ratio >= 0.30:
            return "应收扩张会削弱利润质量判断"
        if ratio >= 0.15:
            return "应收占用需要纳入利润质量判断"
        return "应收压力相对可控"
    return "应收变化需要放入回款效率框架判断"


def _turnover_or_working_capital_hint(
    *,
    inventories: Any,
    revenue: Any,
    ar_turn: Any,
    inv_turn: Any,
) -> str:
    pressure_parts: list[str] = []
    if _is_number(inventories) and _is_number(revenue) and revenue:
        inventory_ratio = inventories / abs(revenue)
        if inventory_ratio >= 0.30:
            pressure_parts.append("存货占用压力偏高")
        elif inventory_ratio <= 0.12:
            pressure_parts.append("存货占用压力可控")
        else:
            pressure_parts.append("存货占用处于可观察区间")
    elif _is_number(inventories):
        pressure_parts.append("存货变化需要结合收入节奏判断")
    if _is_number(ar_turn):
        if ar_turn >= 3:
            pressure_parts.append("应收周转效率具备支撑")
        elif ar_turn < 1:
            pressure_parts.append("应收周转效率偏弱")
    if _is_number(inv_turn):
        if inv_turn >= 5:
            pressure_parts.append("存货周转效率具备支撑")
        elif inv_turn < 1:
            pressure_parts.append("存货周转效率偏弱")
    if pressure_parts:
        return "，".join(_dedupe_preserve_order(pressure_parts))
    return "周转和营运资本变量尚未形成明确判断"


def _financial_risk_flags(
    *,
    revenue_present: bool,
    profit_present: bool,
    consistency: str,
    margin_hint: str,
    balance_hint: str,
) -> list[str]:
    flags: list[str] = []
    if not revenue_present or not profit_present:
        flags.append("收入或利润变量不足会削弱财务表现判断")
    if "背离" in consistency:
        flags.append("收入与利润背离会削弱基本面质量判断")
    if "偏薄" in margin_hint:
        flags.append("利润率偏薄会削弱盈利质量判断")
    if "偏高" in balance_hint:
        flags.append("资产负债结构压力偏高会压缩经营弹性")
    return flags


def _operating_risk_flags(
    *,
    profit_cashflow_match: str,
    receivables_pressure_hint: str,
    turnover_hint: str,
) -> list[str]:
    flags: list[str] = []
    if "打折" in profit_cashflow_match or "压力" in profit_cashflow_match:
        flags.append(profit_cashflow_match)
    if "削弱" in receivables_pressure_hint or "纳入" in receivables_pressure_hint:
        flags.append(receivables_pressure_hint)
    if "偏高" in turnover_hint or "偏弱" in turnover_hint:
        flags.append(turnover_hint)
    return flags


def _quality_bias(profit_cashflow_match: str, risk_flags: list[str]) -> str:
    if "形成支撑" in profit_cashflow_match and not risk_flags:
        return "偏稳"
    if "形成支撑" in profit_cashflow_match:
        return "偏稳但需关注营运资本占用"
    if "打折" in profit_cashflow_match:
        return "需要打折"
    return "偏谨慎"


def _business_variables_from_internal_brief(
    internal_analysis_brief: Mapping[str, Any] | None,
) -> list[str]:
    if internal_analysis_brief is None:
        return list(_DEFAULT_BUSINESS_VARIABLES)
    _reject_bytes(internal_analysis_brief, "internal_analysis_brief")
    _reject_raw_or_secret_keys(internal_analysis_brief, "internal_analysis_brief")
    _assert_no_secret_like_anywhere(internal_analysis_brief)
    serialized = json.dumps(internal_analysis_brief, ensure_ascii=False)
    variables: list[str] = []
    for needle, variable in _BUSINESS_VARIABLE_CANDIDATES:
        if needle in serialized and _safe_business_variable(variable):
            variables.append(variable)
    if not variables:
        variables = list(_DEFAULT_BUSINESS_VARIABLES)
    return _dedupe_preserve_order(variables)[:8]


def _safe_business_variable(value: str) -> bool:
    try:
        assert_no_professional_brief_quality_forbidden_markers(value)
        assert_no_user_visible_engineering_labels(value)
    except ProfessionalCompactBriefQualityError:
        return False
    return True


def _risk_sentence(risk_flags: list[str]) -> str:
    clean_flags = [
        flag
        for flag in risk_flags
        if isinstance(flag, str) and flag.strip()
    ][:4]
    if not clean_flags:
        return "当前主要观察收入、利润、现金流和周转效率之间的匹配。"
    return "；".join(clean_flags) + "。"


def _sanitized_context_for_renderer(context: Mapping[str, Any]) -> dict[str, Any]:
    allowed = {
        key: deepcopy(context[key])
        for key in _CONTEXT_FIELDS
        if key in context
    }
    assert_no_user_visible_engineering_labels(allowed)
    _assert_no_secret_like_anywhere(allowed)
    return allowed


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

    searchable_value = value
    for allowed in _ALLOWED_EXACT_TEXTS:
        searchable_value = searchable_value.replace(allowed, "")
    lowered = searchable_value.casefold()
    separator_normalized = _normalize_separator_text(searchable_value)
    normalized_marker = _normalise_marker(searchable_value)

    for marker in _FORBIDDEN_MARKERS:
        marker_lower = marker.casefold()
        marker_separator = _normalize_separator_text(marker)
        marker_normalized = _normalise_marker(marker)
        if marker_lower == ".env":
            if ".env" in lowered:
                return "forbidden_marker"
            continue
        if marker_normalized in _WORD_MARKERS:
            if re.search(
                rf"(?<![a-z0-9]){re.escape(marker_normalized)}(?![a-z0-9])",
                normalized_marker,
            ):
                return "forbidden_marker"
            continue
        if (
            marker_lower in lowered
            or marker_separator in separator_normalized
            or marker_normalized in normalized_marker
        ):
            return "forbidden_marker"
    if any(marker in searchable_value for marker in _FORBIDDEN_CJK_MARKERS):
        return "forbidden_marker"
    return None


def _reject_raw_or_secret_keys(value: Any, path: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized = _normalise_marker(key_text)
            if key_text in _RAW_OR_FILE_KEYS or normalized in _RAW_OR_FILE_KEYS:
                raise ProfessionalCompactBriefQualityError(
                    f"{path} contains unsupported file or raw key"
                )
            if normalized in _SECRET_KEYS:
                raise ProfessionalCompactBriefQualityError(
                    f"{path} contains unsupported secret key"
                )
            _reject_raw_or_secret_keys(child, f"{path}.{key_text}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_raw_or_secret_keys(child, f"{path}[{index}]")


def _reject_bytes(value: Any, path: str) -> None:
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise ProfessionalCompactBriefQualityError(f"{path} contains raw bytes")
    if isinstance(value, Mapping):
        for key, child in value.items():
            _reject_bytes(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_bytes(child, f"{path}[{index}]")


def _assert_no_secret_like_anywhere(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text not in _ALLOWED_EXACT_TEXTS and _looks_like_secret_text(key_text):
                raise ProfessionalCompactBriefQualityError("secret_like_string")
            _assert_no_secret_like_anywhere(child)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            _assert_no_secret_like_anywhere(item)
    elif isinstance(value, str) and _looks_like_secret_text(value):
        raise ProfessionalCompactBriefQualityError("secret_like_string")


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


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _normalise_marker(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().casefold()).strip("_")


def _normalize_separator_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[_-]+", " ", value.strip().casefold())).strip()


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return str(value)
    stripped = value.strip()
    return stripped or None


def _string_values(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, (list, tuple, set)):
        return [
            str(item).strip()
            for item in value
            if item not in (None, "") and str(item).strip()
        ]
    return [str(value).strip()] if str(value).strip() else []


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
        raise ProfessionalCompactBriefQualityError(f"{field} must be a mapping")
    return value


def _require_fields(value: Mapping[str, Any], fields: tuple[str, ...], path: str) -> None:
    missing = [field for field in fields if field not in value]
    if missing:
        raise ProfessionalCompactBriefQualityError(
            f"{path} missing required fields: {missing}"
        )


def _require_optional_string(value: Any, path: str) -> None:
    if value is not None and not isinstance(value, str):
        raise ProfessionalCompactBriefQualityError(f"{path} must be string or null")


def _require_non_empty_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProfessionalCompactBriefQualityError(
            f"{path} must be a non-empty string"
        )
    return value


def _require_string_list(value: Any, path: str) -> list[str]:
    if not isinstance(value, list):
        raise ProfessionalCompactBriefQualityError(f"{path} must be a list")
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise ProfessionalCompactBriefQualityError(
                f"{path}[{index}] must be string"
            )
    return value


def _require_bool(value: Any, path: str) -> None:
    if not isinstance(value, bool):
        raise ProfessionalCompactBriefQualityError(f"{path} must be bool")


def _require_true(value: Any, path: str) -> None:
    if value is not True:
        raise ProfessionalCompactBriefQualityError(f"{path} must be true")


__all__ = [
    "PROFESSIONAL_ANALYST_CONTEXT_SCHEMA_VERSION",
    "PROFESSIONAL_ANALYST_FINANCIAL_SIGNAL_SCHEMA_VERSION",
    "PROFESSIONAL_ANALYST_QUALITY_SIGNAL_SCHEMA_VERSION",
    "PROFESSIONAL_ANALYST_RENDERER_OUTPUT_SCHEMA_VERSION",
    "PROFESSIONAL_ANALYST_COMPACT_BRIEF_SCHEMA_VERSION",
    "PROFESSIONAL_ANALYST_COMPACT_BRIEF_SECTION_SCHEMA_VERSION",
    "ProfessionalCompactBriefQualityError",
    "assert_no_professional_brief_quality_forbidden_markers",
    "assert_no_user_visible_engineering_labels",
    "build_financial_signal_context",
    "build_industry_macro_signal_context",
    "build_operating_quality_signal_context",
    "build_professional_analyst_context",
    "default_deterministic_analyst_renderer",
    "render_professional_compact_brief_with_llm_handoff",
    "render_professional_compact_brief_from_context",
    "validate_professional_analyst_context",
    "validate_professional_analyst_renderer_output",
]
