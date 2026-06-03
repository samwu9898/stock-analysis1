# -*- coding: utf-8 -*-
"""Investment-director research context pack reuse adapter.

This module is intentionally in-memory. It merges explicitly supplied
Research Intelligence P0/P1 shaped payloads, frontstage report snapshots,
ticker context skeletons, and evidence-aware pack components into a compact
model-facing research context. It does not read runtime artifacts, fetch live
data, call LLMs, render reports, or write files.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
import json
import re
from typing import Any


INVESTMENT_DIRECTOR_RESEARCH_CONTEXT_PACK_REQUEST_SCHEMA_VERSION = (
    "investment_director_research_context_pack_request.v1"
)
INVESTMENT_DIRECTOR_RESEARCH_CONTEXT_PACK_SCHEMA_VERSION = (
    "investment_director_research_context_pack.v1"
)
INVESTMENT_DIRECTOR_MISSING_COVERAGE_MAP_SCHEMA_VERSION = (
    "investment_director_missing_coverage_map.v1"
)
INVESTMENT_DIRECTOR_COVERAGE_ITEM_SCHEMA_VERSION = (
    "investment_director_coverage_item.v1"
)
INVESTMENT_DIRECTOR_COLLISION_QUESTION_SCHEMA_VERSION = (
    "investment_director_collision_question.v1"
)
INVESTMENT_DIRECTOR_COLLISION_QUESTION_SET_SCHEMA_VERSION = (
    "investment_director_collision_question_set.v1"
)
INVESTMENT_DIRECTOR_LLM_CONTEXT_PROMPT_PAYLOAD_SCHEMA_VERSION = (
    "investment_director_llm_context_prompt_payload.v1"
)
INVESTMENT_DIRECTOR_SOURCE_ASSET_SUMMARY_SCHEMA_VERSION = (
    "investment_director_source_asset_summary.v1"
)
INVESTMENT_DIRECTOR_SOURCE_TIER_AND_VIEWPOINT_CONTEXT_SCHEMA_VERSION = (
    "investment_director_source_tier_and_viewpoint_context.v1"
)
INVESTMENT_DIRECTOR_FRAMEWORK_ALIGNMENT_SCHEMA_VERSION = (
    "investment_director_framework_alignment.v1"
)
INVESTMENT_DIRECTOR_FRONTSTAGE_VISUALIZATION_REQUIREMENTS_SCHEMA_VERSION = (
    "investment_director_frontstage_visualization_requirements.v1"
)

COVERAGE_STATUSES = (
    "covered",
    "partial_but_not_llm_visible",
    "framework_exists_but_missing_data",
    "missing",
    "not_applicable",
)
DATA_AVAILABILITY_STATUSES = (
    "available",
    "partial",
    "missing",
    "stale",
    "not_applicable",
    "not_assessable",
)
CONFIDENCE_CAPS = ("high", "medium", "low", "not_assessable")
COLLISION_LAYERS = (
    "macro",
    "industry",
    "company",
    "financial",
    "risk",
    "valuation",
    "source",
)
COLLISION_TRIGGER_SOURCES = ("p0", "p1", "html_snapshot", "evidence_pack", "derived")
PRIORITIES = ("P0", "P1", "P2", "future")

FRONTSTAGE_CONTEXT_FIELDS = (
    "core_conclusion",
    "core_conflict",
    "company_profile_summary",
    "business_composition_summary",
    "financial_quality_summary",
    "valuation_explainability_summary",
    "quality_score_summary",
    "risk_summary",
    "tracking_plan_summary",
    "data_quality_summary",
)

REQUEST_FIELDS = {
    "schema_version",
    "stock_code",
    "ts_code",
    "company_name_hint",
    "not_for_trading_advice",
    "research_intelligence_p0",
    "research_questions_p0",
    "research_intelligence_p1",
    "research_questions_p1",
    "ticker_research_context_skeleton",
    "evidence_aware_research_pack",
    "old_report_frontstage_snapshot",
    "professional_compact_brief",
    "strategy_type",
    "sub_type",
    "include_prompt_payload",
    "include_missing_coverage_map",
    "not_applicable_coverage_categories",
}

FORBIDDEN_REQUEST_KEYS = {
    "accepted_manifest",
    "accepted_manifest_path",
    "api_key",
    "api_token",
    "authorization",
    "bearer",
    "cache_path",
    "candidate_items",
    "credential",
    "credentials",
    "env",
    "env_file",
    "fixture_path",
    "fixtures_path",
    "html_raw",
    "key_file",
    "output_path",
    "page_number",
    "pdf_bytes",
    "raw_llm_response",
    "raw_prompt",
    "raw_provider_bundle",
    "raw_provider_rows",
    "report_html_raw",
    "secret",
    "sha256",
    "snippet",
    "source_url",
    "token",
    "tushare_token",
    "tushare_token_path",
}

ALLOWED_EXACT_KEYS = {
    "not_for_trading_advice",
    "trading_advice_allowed",
    "html_report_mapping",
}

RAW_BACKEND_MARKERS = (
    ".env",
    "api key",
    "api_key",
    "accepted manifest path",
    "accepted_manifest_path",
    "backend trace",
    "backend_trace",
    "backend_grounding_summary",
    "bearer ",
    "cache path",
    "cache_path",
    "candidate_items",
    "chart artifact",
    "credential file",
    "fixture path",
    "fixture_path",
    "HTML artifact",
    "JSON artifact",
    "key file",
    "Markdown artifact",
    "output path",
    "output_path",
    "page_number",
    "pdf bytes",
    "pdf_bytes",
    "raw llm response",
    "raw prompt",
    "raw provider bundle",
    "raw provider row",
    "raw provider rows",
    "raw_llm_response",
    "raw_prompt",
    "raw_provider_bundle",
    "raw_provider_rows",
    "Report V1 artifact",
    "report artifact",
    "report_html_raw",
    "sha256",
    "snippet",
    "source_url",
    "tushare_token",
)

MARKET_ACTION_WORDS = {"buy", "sell", "hold", "portfolio", "position"}
MARKET_ACTION_PHRASES = (
    "target price",
    "price target",
    "technical signal",
)
MARKET_ACTION_CJK_MARKERS = (
    "买入",
    "卖出",
    "持有",
    "目标价",
    "仓位",
    "技术信号",
    "投资建议",
    "交易建议",
)
USER_RESPONSIBILITY_SHIFT_MARKERS = (
    "user should decide",
    "decide by yourself",
    "track by yourself",
    "用户自行判断",
    "用户自行",
    "自行判断",
    "自行跟踪",
    "需要用户",
    "建议用户",
)
POSITIVE_OVERREAD_MARKERS = (
    "capex increased, so capacity has been released",
    "capex directly means capacity release",
    "capex 直接等于产能释放",
    "产能释放确定",
    "contract liabilities mean backlog",
    "contract liabilities directly mean backlog",
    "合同负债代表 backlog",
    "合同负债等于 backlog",
    "合同负债直接等于",
    "r&d ratio is high, so the technology moat is strong",
    "r&d 率直接等于技术壁垒",
    "研发投入直接等于技术壁垒",
    "industry demand is strong, so the company benefits",
    "policy supports demand, company benefits",
    "行业景气直接等于公司受益",
    "政策支持直接等于公司受益",
    "公司受益",
    "公司属于 stable_growth，所以经营稳健",
    "公司属于stable_growth，所以经营稳健",
    "stable_growth therefore operating steadiness",
    "机器人收入已兑现",
    "robotics realized revenue",
)
VAGUE_GAP_MARKERS = (
    "needs more research",
    "more research needed",
    "需进一步研究",
    "需要更多研究",
    "需要更多资料",
    "后续继续关注",
)

HTML_CONTENT_RE = re.compile(
    r"<!doctype|<\s*(html|head|body|script|style|div|section|table|span|p)\b|</\s*[a-z][a-z0-9]*\s*>",
    re.IGNORECASE,
)
SECRET_LIKE_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._-]{8,}\b", re.IGNORECASE),
)


class InvestmentDirectorResearchContextPackError(ValueError):
    """Raised when the investment-director context pack fails closed."""


def build_investment_director_research_context_pack(
    request: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the in-memory investment-director research context pack."""

    source = _validated_request_copy(request)
    frontstage_context = build_old_report_frontstage_snapshot(
        source.get("old_report_frontstage_snapshot")
    )
    research_context = _build_research_intelligence_context(source)
    collision_question_set = {
        "schema_version": INVESTMENT_DIRECTOR_COLLISION_QUESTION_SET_SCHEMA_VERSION,
        "questions": build_collision_questions_from_research_intelligence(source),
        "not_for_trading_advice": True,
    }
    missing_coverage_map = (
        build_investment_director_missing_coverage_map(source)
        if source.get("include_missing_coverage_map", True)
        else None
    )
    pack = {
        "schema_version": INVESTMENT_DIRECTOR_RESEARCH_CONTEXT_PACK_SCHEMA_VERSION,
        "company_identity": {
            "stock_code": source["stock_code"],
            "ts_code": source["ts_code"],
            "company_name_hint": source.get("company_name_hint"),
            "strategy_type": source.get("strategy_type"),
            "sub_type": source.get("sub_type"),
            "framework_status": "reuse_adapter_from_supplied_research_assets",
        },
        "source_asset_summary": summarize_research_intelligence_asset_presence(source),
        "frontstage_report_context": frontstage_context,
        "research_intelligence_context": research_context,
        "collision_question_set": collision_question_set,
        "source_tier_and_viewpoint_context": (
            build_source_tier_and_viewpoint_context(source)
        ),
        "director_framework_alignment": build_director_framework_alignment(
            missing_coverage_map
        ),
        "frontstage_visualization_requirements": (
            build_frontstage_visualization_requirements(
                frontstage_context,
                missing_coverage_map,
            )
        ),
        "not_for_trading_advice": True,
    }
    if missing_coverage_map is not None:
        pack["missing_coverage_map"] = missing_coverage_map
    if source.get("include_prompt_payload", True):
        pack["llm_context_prompt_payload"] = (
            build_llm_context_prompt_payload_from_investment_director_pack(pack)
        )
    return validate_investment_director_research_context_pack(pack)


def validate_investment_director_research_context_pack(
    pack: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate and return a defensive copy of a context pack."""

    assert_no_investment_director_context_forbidden_markers(pack)
    source = _require_mapping(pack, "investment_director_research_context_pack")
    required = (
        "schema_version",
        "company_identity",
        "source_asset_summary",
        "frontstage_report_context",
        "research_intelligence_context",
        "collision_question_set",
        "source_tier_and_viewpoint_context",
        "director_framework_alignment",
        "frontstage_visualization_requirements",
        "not_for_trading_advice",
    )
    _require_fields(source, required, "investment_director_research_context_pack")
    result = deepcopy(dict(source))
    _require_schema_version(
        result["schema_version"],
        INVESTMENT_DIRECTOR_RESEARCH_CONTEXT_PACK_SCHEMA_VERSION,
        "schema_version",
    )
    _validate_company_identity(result["company_identity"])
    _validate_source_asset_summary(result["source_asset_summary"])
    _validate_frontstage_report_context(result["frontstage_report_context"])
    _validate_research_intelligence_context(result["research_intelligence_context"])
    result["collision_question_set"] = _validate_collision_question_set(
        result["collision_question_set"]
    )
    result["source_tier_and_viewpoint_context"] = (
        _validate_source_tier_and_viewpoint_context(
            result["source_tier_and_viewpoint_context"]
        )
    )
    result["director_framework_alignment"] = _validate_director_framework_alignment(
        result["director_framework_alignment"]
    )
    result["frontstage_visualization_requirements"] = (
        _validate_frontstage_visualization_requirements(
            result["frontstage_visualization_requirements"]
        )
    )
    if "missing_coverage_map" in result:
        result["missing_coverage_map"] = validate_investment_director_missing_coverage_map(
            result["missing_coverage_map"]
        )
    if "llm_context_prompt_payload" in result:
        result["llm_context_prompt_payload"] = (
            _validate_llm_context_prompt_payload(result["llm_context_prompt_payload"])
        )
    _require_true(result["not_for_trading_advice"], "not_for_trading_advice")
    assert_no_investment_director_context_forbidden_markers(result)
    return result


def build_investment_director_missing_coverage_map(
    inputs: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the investment-director coverage map from supplied assets."""

    source = _validated_inputs_copy_for_component(inputs)
    entries = _collect_asset_entries(source)
    not_applicable = set(_string_values(source.get("not_applicable_coverage_categories")))
    requirements = list(_BASE_COVERAGE_REQUIREMENTS)
    requirements.extend(_strategy_specific_requirements(source))
    items = [
        _coverage_item_from_requirement(requirement, entries, not_applicable)
        for requirement in requirements
    ]
    result = {
        "schema_version": INVESTMENT_DIRECTOR_MISSING_COVERAGE_MAP_SCHEMA_VERSION,
        "items": items,
        "status_counts": _coverage_status_counts(items),
        "covered_definition": (
            "covered requires framework_exists, material_or_structured_input_exists, "
            "and can_enter_llm_context all true"
        ),
        "not_for_trading_advice": True,
    }
    return validate_investment_director_missing_coverage_map(result)


def validate_investment_director_missing_coverage_map(
    coverage_map: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate and return a defensive copy of a missing coverage map."""

    assert_no_investment_director_context_forbidden_markers(coverage_map)
    source = _require_mapping(coverage_map, "investment_director_missing_coverage_map")
    required = (
        "schema_version",
        "items",
        "status_counts",
        "covered_definition",
        "not_for_trading_advice",
    )
    _require_fields(source, required, "investment_director_missing_coverage_map")
    result = deepcopy(dict(source))
    _require_schema_version(
        result["schema_version"],
        INVESTMENT_DIRECTOR_MISSING_COVERAGE_MAP_SCHEMA_VERSION,
        "missing_coverage_map.schema_version",
    )
    items = _require_list(result["items"], "missing_coverage_map.items")
    result["items"] = [
        _validate_coverage_item(item, f"missing_coverage_map.items[{index}]")
        for index, item in enumerate(items)
    ]
    ids = {item["requirement_id"] for item in result["items"]}
    missing_base = [
        item["requirement_id"]
        for item in _BASE_COVERAGE_REQUIREMENTS
        if item["requirement_id"] not in ids
    ]
    if missing_base:
        raise InvestmentDirectorResearchContextPackError(
            f"missing coverage requirements: {missing_base}"
        )
    if result["status_counts"] != _coverage_status_counts(result["items"]):
        raise InvestmentDirectorResearchContextPackError("status_counts mismatch")
    _require_non_empty_string(
        result["covered_definition"], "missing_coverage_map.covered_definition"
    )
    _require_true(
        result["not_for_trading_advice"],
        "missing_coverage_map.not_for_trading_advice",
    )
    return result


def build_source_tier_and_viewpoint_context(
    inputs: Mapping[str, Any],
) -> dict[str, Any]:
    """Summarize supplied source tiers and viewpoint availability only."""

    source = _validated_inputs_copy_for_component(inputs)
    p0 = _mapping_or_empty(source.get("research_intelligence_p0"))
    p1 = _mapping_or_empty(source.get("research_intelligence_p1"))
    source_hierarchy = _iter_component_items(p0.get("source_hierarchy"))
    bucket_summary = _mapping_or_empty(p1.get("source_bucket_summary"))
    source_buckets = _dedupe_preserve_order(
        _string_values(bucket_summary.get("source_buckets"))
        + [
            str(item.get("source_tier") or item.get("source_name"))
            for item in source_hierarchy
            if item.get("source_tier") or item.get("source_name")
        ]
    )
    independent_count = _non_negative_int_or_default(
        bucket_summary.get("independent_source_count"),
        len(set(source_buckets)),
    )
    if independent_count < 2:
        consensus_status = "not_assessable"
        divergent_status = "not_assessable"
        opposing_status = "not_assessable"
        missing_viewpoint = [
            "at least two independent source buckets",
            "structured consensus/divergence summary",
            "structured opposing-view evidence",
        ]
        boundary = (
            "Only source-tier availability is summarized; fewer than two independent "
            "source buckets means consensus, divergence, and opposing views remain not assessable."
        )
    else:
        consensus_status = _normalize_viewpoint_status(
            bucket_summary.get("consensus_assessment_status")
        )
        text = _searchable_text([p0, p1]).casefold()
        divergent_status = "partial" if "diverg" in text or "分歧" in text else "missing"
        opposing_status = "partial" if "opposing" in text or "反证" in text or "相反" in text else "missing"
        missing_viewpoint = []
        if divergent_status == "missing":
            missing_viewpoint.append("structured divergent-view evidence")
        if opposing_status == "missing":
            missing_viewpoint.append("structured opposing-view evidence")
        boundary = (
            "This section records viewpoint availability boundaries only and does not "
            "generate market-view prose."
        )
    context = {
        "schema_version": INVESTMENT_DIRECTOR_SOURCE_TIER_AND_VIEWPOINT_CONTEXT_SCHEMA_VERSION,
        "source_tier_summary": [
            {
                "source_name": item.get("source_name") or item.get("source_tier") or "supplied_source",
                "source_tier": item.get("source_tier"),
                "evidence_type": item.get("evidence_type") or "structured_context",
                "data_availability_status": _normalize_data_status(
                    item.get("data_availability_status")
                ),
                "what_was_checked": _string_values(item.get("what_was_checked")),
            }
            for item in source_hierarchy
        ],
        "available_source_buckets": source_buckets,
        "independent_source_count": independent_count,
        "consensus_status": consensus_status,
        "divergent_view_status": divergent_status,
        "opposing_view_status": opposing_status,
        "viewpoint_boundary": boundary,
        "missing_viewpoint_evidence": missing_viewpoint,
        "not_for_trading_advice": True,
    }
    return _validate_source_tier_and_viewpoint_context(context)


def build_director_framework_alignment(
    coverage_map: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Build an alignment summary from the Missing Coverage Map."""

    items = _coverage_items_from_map(coverage_map)
    by_id = {item["requirement_id"]: item for item in items}
    framework_chain = {
        "macro_policy_industry": _chain_statuses(
            by_id,
            (
                "macro_context",
                "international_macro",
                "fx",
                "commodity",
                "policy",
                "industry_cycle",
                "industry_consensus",
                "divergent_views",
                "opposing_views",
                "news_and_special_events",
                "source_tier_classification",
            ),
        ),
        "company_business_project_competitor_customer": _chain_statuses(
            by_id,
            (
                "company_business_structure",
                "business_competitiveness",
                "market_share",
                "competitor_peer_benchmark",
                "project_progress",
                "revenue_driver_decomposition",
            ),
        ),
        "financial_cashflow_capex_rd_debt": _chain_statuses(
            by_id,
            (
                "financial_statement_quality",
                "cashflow_receivable_inventory_linkage",
                "capex_mapping",
                "r_and_d_conversion",
                "rd_staff_and_project_mapping",
                "cost_driver_decomposition",
                "balance_sheet_reclassification",
                "debt_financing_structure",
                "financing_cashflow_dependency",
            ),
        ),
        "disclosure_delivery_risk_research_notes": _chain_statuses(
            by_id,
            (
                "disclosure_consistency",
                "prior_promise_vs_current_delivery",
                "selective_disclosure_risk",
                "governance_risk",
                "regulatory_violation_risk",
                "black_swan_risk",
                "manual_research_notes",
                "ir_questions",
                "authoritative_data_crosscheck",
            ),
        ),
        "collision_and_judgment": _chain_statuses(
            by_id,
            (
                "opposing_views",
                "disclosure_consistency",
                "cashflow_receivable_inventory_linkage",
                "authoritative_data_crosscheck",
            ),
        ),
        "frontstage_display": _chain_statuses(
            by_id,
            (
                "frontstage_chart_ready_sections",
                "html_report_mapping",
                "conclusion_first_frontstage",
                "visualization_plan",
            ),
        ),
    }
    weak_links = [
        {
            "requirement_id": item["requirement_id"],
            "coverage_status": item["coverage_status"],
            "next_data_task": item["next_data_task"],
            "blocks_llm_depth": item["blocks_llm_depth"],
            "not_for_trading_advice": True,
        }
        for item in items
        if item["coverage_status"] not in {"covered", "not_applicable"}
    ]
    alignment_summary = (
        f"Coverage map exposes {len(weak_links)} weak link(s); alignment remains bounded by missing or partial evidence."
        if weak_links
        else "Coverage map currently exposes no weak links; keep supplied evidence visible in the model context."
    )
    alignment = {
        "schema_version": INVESTMENT_DIRECTOR_FRAMEWORK_ALIGNMENT_SCHEMA_VERSION,
        "framework_chain": framework_chain,
        "alignment_summary": alignment_summary,
        "weak_links": weak_links[:20],
        "next_alignment_tasks": [
            item["next_data_task"] for item in weak_links[:10]
        ],
        "not_for_trading_advice": True,
    }
    return _validate_director_framework_alignment(alignment)


def build_frontstage_visualization_requirements(
    frontstage_context: Mapping[str, Any],
    coverage_map: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Build an in-memory display requirement summary for future frontstage use."""

    frontstage = _require_mapping(frontstage_context, "frontstage_context")
    by_id = {
        item["requirement_id"]: item
        for item in _coverage_items_from_map(coverage_map)
    }
    display_items = [
        by_id[item]
        for item in (
            "conclusion_first_frontstage",
            "visualization_plan",
            "frontstage_chart_ready_sections",
            "html_report_mapping",
        )
        if item in by_id and by_id[item]["coverage_status"] != "covered"
    ]
    requirements = {
        "schema_version": INVESTMENT_DIRECTOR_FRONTSTAGE_VISUALIZATION_REQUIREMENTS_SCHEMA_VERSION,
        "conclusion_first_sections": _non_empty_frontstage_section_names(
            frontstage,
            ("core_conclusion", "core_conflict", "risk_summary"),
        ),
        "chart_ready_sections": _non_empty_frontstage_section_names(
            frontstage,
            (
                "quality_score_summary",
                "financial_quality_summary",
                "business_composition_summary",
                "tracking_plan_summary",
            ),
        ),
        "table_ready_sections": [
            "missing_coverage_map.status_counts",
            "collision_question_set.questions",
            "source_tier_and_viewpoint_context.source_tier_summary",
        ],
        "material_backstage_sections": [
            "source_asset_summary",
            "research_intelligence_context",
            "missing_coverage_map",
            "collision_question_set",
        ],
        "missing_visualization_inputs": [
            {
                "requirement_id": item["requirement_id"],
                "coverage_status": item["coverage_status"],
                "required_evidence": list(item["required_evidence"]),
                "next_data_task": item["next_data_task"],
            }
            for item in display_items
        ],
        "html_report_mapping_summary": (
            "Future frontstage integration should place conclusion/core conflict first, "
            "show chart/table-ready summaries next, and keep detailed materials backstage."
        ),
        "not_for_trading_advice": True,
    }
    return _validate_frontstage_visualization_requirements(requirements)


def build_collision_questions_from_research_intelligence(
    inputs: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Build evidence-status-aware collision questions from P0/P1 inputs."""

    source = _validated_inputs_copy_for_component(inputs)
    normalized_questions = _normalized_research_questions(source)
    checked_assets = _checked_asset_names(source)
    result = []
    for blueprint in _COLLISION_BLUEPRINTS:
        matches = _matching_question_items(blueprint["keywords"], normalized_questions)
        result.append(
            _collision_question_from_blueprint(
                blueprint=blueprint,
                matches=matches,
                checked_assets=checked_assets,
            )
        )
    return [_validate_collision_question(item, f"collision_questions[{index}]") for index, item in enumerate(result)]


def build_llm_context_prompt_payload_from_investment_director_pack(
    pack: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a concise prompt payload draft without calling an LLM."""

    source = _require_mapping(pack, "investment_director_pack")
    frontstage = _require_mapping(
        source.get("frontstage_report_context"), "frontstage_report_context"
    )
    collision_questions = _require_mapping(
        source.get("collision_question_set"), "collision_question_set"
    ).get("questions", [])
    coverage_items = _require_mapping(
        source.get("missing_coverage_map", {"items": []}), "missing_coverage_map"
    ).get("items", [])
    core_conflicts = _dedupe_preserve_order(
        _string_values(frontstage.get("core_conflict"))
        + [
            question["question"]
            for question in collision_questions
            if isinstance(question, Mapping)
            and question.get("data_availability_status")
            in {"missing", "partial", "not_assessable"}
        ][:6]
    )
    prompt_payload = {
        "schema_version": INVESTMENT_DIRECTOR_LLM_CONTEXT_PROMPT_PAYLOAD_SCHEMA_VERSION,
        "role": "A股专业基本面研究员",
        "task": "形成投资总监式基本面分析",
        "analysis_requirements": [
            "Do not merely repeat metrics; explain business-financial-risk collisions.",
            "Treat missing and not_assessable items as boundaries, not conclusions.",
            "External themes must be connected to company orders, delivery, collection, revenue, margins, or cash conversion before a company-level claim.",
            "Use the collision questions as required checks, not as optional appendices.",
        ],
        "available_materials_summary": _compact_materials_summary(
            source.get("source_asset_summary", {})
        ),
        "core_conflicts_to_analyze": core_conflicts[:8],
        "collision_questions": [
            _compact_collision_question(question)
            for question in list(collision_questions)[:12]
        ],
        "missing_coverage_boundaries": [
            _compact_coverage_boundary(item)
            for item in coverage_items
            if isinstance(item, Mapping)
            and item.get("coverage_status") != "covered"
        ][:14],
        "required_output_sections": [
            "核心结论",
            "核心矛盾",
            "公司靠什么赚钱",
            "业务竞争力判断",
            "财务质量与经营真相",
            "行业/宏观/上下游传导",
            "信息对撞结果",
            "关键支持证据",
            "关键反证/风险",
            "需要继续验证的问题",
            "结论边界",
        ],
        "output_boundaries": {
            "trading_advice_allowed": False,
            "external_api_allowed": False,
            "artifact_generation_allowed": False,
            "disallowed_output_types": [
                "market_action_call",
                "price_objective",
                "sizing_instruction",
                "chart_timing_signal",
                "responsibility_shift_to_reader",
            ],
        },
        "not_for_trading_advice": True,
    }
    return _validate_llm_context_prompt_payload(prompt_payload)


def assert_no_investment_director_context_forbidden_markers(value: Any) -> None:
    """Reject raw backends, secrets, action language, and positive overreads."""

    assert_no_raw_backend_or_secret_leak(value)
    finding = _find_market_or_responsibility_marker(value)
    if finding:
        raise InvestmentDirectorResearchContextPackError(
            f"investment director context safety violation: {finding}"
        )
    overread = _find_positive_overread(value)
    if overread:
        raise InvestmentDirectorResearchContextPackError(
            f"investment director context overread violation: {overread}"
        )


def assert_no_raw_backend_or_secret_leak(value: Any) -> None:
    """Reject secrets, raw provider payloads, backend traces, locators, and HTML."""

    _reject_bytes(value, "value")
    _reject_forbidden_keys(value, "value")
    finding = _find_raw_or_secret_marker(value)
    if finding:
        raise InvestmentDirectorResearchContextPackError(
            f"raw backend or secret leak: {finding}"
        )


def build_old_report_frontstage_snapshot(
    old_report_frontstage_snapshot: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Normalize a structured old frontstage report snapshot."""

    snapshot = old_report_frontstage_snapshot or {}
    mapping = _require_mapping(snapshot, "old_report_frontstage_snapshot")
    _reject_forbidden_keys(mapping, "old_report_frontstage_snapshot")
    assert_no_raw_backend_or_secret_leak(mapping)
    return {
        "schema_version": "investment_director_frontstage_report_context.v1",
        **{
            key: deepcopy(mapping.get(key, "" if key != "quality_score_summary" else {}))
            for key in FRONTSTAGE_CONTEXT_FIELDS
        },
        "not_for_trading_advice": True,
    }


def normalize_research_question_item(
    item: Mapping[str, Any],
    *,
    trigger_source: str = "derived",
) -> dict[str, Any]:
    """Normalize a P0/P1 shaped research question without upgrading evidence."""

    source = _require_mapping(item, "research_question_item")
    question_text = _first_present(
        source,
        ("question", "question_text", "research_question", "driver_factor", "claim_or_risk"),
    )
    if not question_text:
        question_text = "Supplied research item requires evidence-status review."
    layer = _first_present(source, ("layer", "driver_layer"))
    normalized = {
        "question": str(question_text),
        "category": str(_first_present(source, ("category", "driver_factor", "rule_id")) or "derived"),
        "layer": _normalize_layer(layer),
        "trigger_source": _normalize_trigger_source(trigger_source),
        "evidence_trigger": str(_first_present(source, ("evidence_trigger", "trigger_rule_id", "rule_id")) or ""),
        "why_it_matters": str(_first_present(source, ("why_it_matters", "claim_or_risk")) or ""),
        "required_evidence": _string_values(source.get("required_evidence") or source.get("required_data")),
        "available_evidence": _string_values(source.get("available_evidence") or source.get("evidence_for")),
        "missing_evidence": _string_values(
            source.get("missing_evidence")
            or source.get("evidence_gap")
            or source.get("evidence_against")
        ),
        "data_availability_status": _normalize_data_status(
            _first_present(source, ("data_availability_status", "current_evidence_status", "validation_status"))
        ),
        "confidence_cap": _normalize_confidence_cap(source.get("confidence_cap")),
        "not_assessable_reason": str(source.get("not_assessable_reason") or ""),
        "what_was_checked": _string_values(source.get("what_was_checked")),
        "suggested_next_action": str(_first_present(source, ("suggested_next_action", "next_check")) or ""),
    }
    if not normalized["evidence_trigger"]:
        normalized["evidence_trigger"] = _evidence_trigger_from_normalized(normalized)
    if not normalized["what_was_checked"]:
        normalized["what_was_checked"] = _checked_fields_from_item(source)
    if not normalized["why_it_matters"]:
        normalized["why_it_matters"] = "It determines whether the supplied research frame can support a deeper fundamental conclusion."
    if not normalized["required_evidence"]:
        normalized["required_evidence"] = ["structured evidence that resolves the stated research question"]
    if normalized["data_availability_status"] in {"missing", "not_assessable"} and not normalized["not_assessable_reason"]:
        normalized["not_assessable_reason"] = "Supplied structured inputs do not yet contain enough evidence to answer this item."
    if not normalized["suggested_next_action"]:
        normalized["suggested_next_action"] = _next_action_from_evidence(
            normalized["required_evidence"],
            normalized["missing_evidence"],
        )
    return normalized


def summarize_research_intelligence_asset_presence(
    request: Mapping[str, Any],
) -> dict[str, Any]:
    """Summarize which reusable source assets were explicitly supplied."""

    source = _require_mapping(request, "request")
    components = []
    for key in (
        "research_intelligence_p0",
        "research_questions_p0",
        "research_intelligence_p1",
        "research_questions_p1",
        "ticker_research_context_skeleton",
        "evidence_aware_research_pack",
        "old_report_frontstage_snapshot",
        "professional_compact_brief",
    ):
        value = source.get(key)
        components.append(
            {
                "asset_id": key,
                "present": _has_material_value(value),
                "visible_in_adapter_pack": _has_material_value(value),
                "key_fields_present": _present_field_names(value),
                "not_for_trading_advice": True,
            }
        )
    return {
        "schema_version": INVESTMENT_DIRECTOR_SOURCE_ASSET_SUMMARY_SCHEMA_VERSION,
        "components": components,
        "summary": _source_asset_presence_sentence(components),
        "not_for_trading_advice": True,
    }


def _validated_request_copy(request: Mapping[str, Any]) -> dict[str, Any]:
    source = _require_mapping(request, "request")
    _reject_bytes(source, "request")
    _reject_forbidden_keys(source, "request")
    assert_no_raw_backend_or_secret_leak(source)
    unsupported = sorted(set(source) - REQUEST_FIELDS)
    if unsupported:
        raise InvestmentDirectorResearchContextPackError(
            f"request contains unsupported fields: {unsupported}"
        )
    _require_fields(
        source,
        ("schema_version", "stock_code", "ts_code", "not_for_trading_advice"),
        "request",
    )
    _require_schema_version(
        source["schema_version"],
        INVESTMENT_DIRECTOR_RESEARCH_CONTEXT_PACK_REQUEST_SCHEMA_VERSION,
        "request.schema_version",
    )
    _require_non_empty_string(source["stock_code"], "request.stock_code")
    _require_non_empty_string(source["ts_code"], "request.ts_code")
    if "company_name_hint" in source:
        _require_optional_string(source["company_name_hint"], "request.company_name_hint")
    _require_true(source["not_for_trading_advice"], "request.not_for_trading_advice")
    for flag in ("include_prompt_payload", "include_missing_coverage_map"):
        if flag in source and not isinstance(source[flag], bool):
            raise InvestmentDirectorResearchContextPackError(f"request.{flag} must be bool")
    for key in (
        "research_intelligence_p0",
        "research_questions_p0",
        "research_intelligence_p1",
        "research_questions_p1",
        "ticker_research_context_skeleton",
        "evidence_aware_research_pack",
        "old_report_frontstage_snapshot",
        "professional_compact_brief",
    ):
        if key in source and source[key] is not None:
            _require_mapping(source[key], f"request.{key}")
    return deepcopy(dict(source))


def _validated_inputs_copy_for_component(inputs: Mapping[str, Any]) -> dict[str, Any]:
    source = _require_mapping(inputs, "inputs")
    _reject_bytes(source, "inputs")
    _reject_forbidden_keys(source, "inputs")
    assert_no_raw_backend_or_secret_leak(source)
    return deepcopy(dict(source))


def _build_research_intelligence_context(source: Mapping[str, Any]) -> dict[str, Any]:
    p0 = _mapping_or_empty(source.get("research_intelligence_p0"))
    p1 = _mapping_or_empty(source.get("research_intelligence_p1"))
    question_items = _normalized_research_questions(source)
    result = {
        "schema_version": "investment_director_research_intelligence_context.v1",
        "source_hierarchy_summary": _source_hierarchy_summary(p0, p1),
        "business_financial_cross_validation": _combined_list_field(
            p0,
            "business_financial_cross_validation",
        ),
        "rule_triggered_contradictions": _combined_list_field(
            p0,
            "rule_triggered_contradictions",
        ),
        "driver_questions": [
            deepcopy(item)
            for item in question_items
            if item["trigger_source"] == "p1" or _driver_like(item)
        ],
        "manual_review_items": _manual_review_items(source, question_items),
        "ir_question_candidates": _ir_question_candidates(source, question_items),
        "not_assessable_items": _not_assessable_items(source, question_items),
        "missing_evidence_items": _missing_evidence_items(source, question_items),
        "proxy_guardrails": _proxy_guardrails_from_items(question_items),
        "company_transmission_path_items": _company_transmission_path_items(p1),
        "source_bucket_independence_summary": deepcopy(
            p1.get("source_bucket_summary", {})
        ),
        "not_for_trading_advice": True,
    }
    return result


def _validate_company_identity(value: Any) -> None:
    identity = _require_mapping(value, "company_identity")
    _require_fields(
        identity,
        (
            "stock_code",
            "ts_code",
            "company_name_hint",
            "strategy_type",
            "sub_type",
            "framework_status",
        ),
        "company_identity",
    )
    _require_non_empty_string(identity["stock_code"], "company_identity.stock_code")
    _require_non_empty_string(identity["ts_code"], "company_identity.ts_code")
    _require_optional_string(
        identity["company_name_hint"], "company_identity.company_name_hint"
    )
    _require_optional_string(identity["strategy_type"], "company_identity.strategy_type")
    _require_optional_string(identity["sub_type"], "company_identity.sub_type")
    _require_non_empty_string(
        identity["framework_status"], "company_identity.framework_status"
    )


def _validate_source_asset_summary(value: Any) -> None:
    summary = _require_mapping(value, "source_asset_summary")
    _require_schema_version(
        summary.get("schema_version"),
        INVESTMENT_DIRECTOR_SOURCE_ASSET_SUMMARY_SCHEMA_VERSION,
        "source_asset_summary.schema_version",
    )
    components = _require_list(summary.get("components"), "source_asset_summary.components")
    for index, item in enumerate(components):
        component = _require_mapping(item, f"source_asset_summary.components[{index}]")
        _require_fields(
            component,
            (
                "asset_id",
                "present",
                "visible_in_adapter_pack",
                "key_fields_present",
                "not_for_trading_advice",
            ),
            f"source_asset_summary.components[{index}]",
        )
        _require_non_empty_string(
            component["asset_id"], f"source_asset_summary.components[{index}].asset_id"
        )
        _require_bool(
            component["present"], f"source_asset_summary.components[{index}].present"
        )
        _require_bool(
            component["visible_in_adapter_pack"],
            f"source_asset_summary.components[{index}].visible_in_adapter_pack",
        )
        _require_string_list(
            component["key_fields_present"],
            f"source_asset_summary.components[{index}].key_fields_present",
        )
        _require_true(
            component["not_for_trading_advice"],
            f"source_asset_summary.components[{index}].not_for_trading_advice",
        )
    _require_non_empty_string(summary.get("summary"), "source_asset_summary.summary")
    _require_true(
        summary.get("not_for_trading_advice"),
        "source_asset_summary.not_for_trading_advice",
    )


def _validate_frontstage_report_context(value: Any) -> None:
    context = _require_mapping(value, "frontstage_report_context")
    _require_schema_version(
        context.get("schema_version"),
        "investment_director_frontstage_report_context.v1",
        "frontstage_report_context.schema_version",
    )
    _require_fields(
        context,
        ("schema_version", *FRONTSTAGE_CONTEXT_FIELDS, "not_for_trading_advice"),
        "frontstage_report_context",
    )
    _require_true(
        context["not_for_trading_advice"],
        "frontstage_report_context.not_for_trading_advice",
    )


def _validate_research_intelligence_context(value: Any) -> None:
    context = _require_mapping(value, "research_intelligence_context")
    required = (
        "schema_version",
        "source_hierarchy_summary",
        "business_financial_cross_validation",
        "rule_triggered_contradictions",
        "driver_questions",
        "manual_review_items",
        "ir_question_candidates",
        "not_assessable_items",
        "missing_evidence_items",
        "proxy_guardrails",
        "company_transmission_path_items",
        "source_bucket_independence_summary",
        "not_for_trading_advice",
    )
    _require_fields(context, required, "research_intelligence_context")
    for key in required:
        if key in {"schema_version", "source_bucket_independence_summary", "not_for_trading_advice"}:
            continue
        _require_list(context[key], f"research_intelligence_context.{key}")
    _require_true(
        context["not_for_trading_advice"],
        "research_intelligence_context.not_for_trading_advice",
    )


def _validate_source_tier_and_viewpoint_context(value: Any) -> dict[str, Any]:
    context = _require_mapping(value, "source_tier_and_viewpoint_context")
    required = (
        "schema_version",
        "source_tier_summary",
        "available_source_buckets",
        "independent_source_count",
        "consensus_status",
        "divergent_view_status",
        "opposing_view_status",
        "viewpoint_boundary",
        "missing_viewpoint_evidence",
        "not_for_trading_advice",
    )
    _require_fields(context, required, "source_tier_and_viewpoint_context")
    result = deepcopy(dict(context))
    _require_schema_version(
        result["schema_version"],
        INVESTMENT_DIRECTOR_SOURCE_TIER_AND_VIEWPOINT_CONTEXT_SCHEMA_VERSION,
        "source_tier_and_viewpoint_context.schema_version",
    )
    source_tiers = _require_list(
        result["source_tier_summary"],
        "source_tier_and_viewpoint_context.source_tier_summary",
    )
    for index, item in enumerate(source_tiers):
        mapping = _require_mapping(
            item,
            f"source_tier_and_viewpoint_context.source_tier_summary[{index}]",
        )
        _require_fields(
            mapping,
            (
                "source_name",
                "source_tier",
                "evidence_type",
                "data_availability_status",
                "what_was_checked",
            ),
            f"source_tier_and_viewpoint_context.source_tier_summary[{index}]",
        )
        _require_non_empty_string(
            mapping["source_name"],
            f"source_tier_and_viewpoint_context.source_tier_summary[{index}].source_name",
        )
        _require_optional_string(
            mapping["source_tier"],
            f"source_tier_and_viewpoint_context.source_tier_summary[{index}].source_tier",
        )
        _require_non_empty_string(
            mapping["evidence_type"],
            f"source_tier_and_viewpoint_context.source_tier_summary[{index}].evidence_type",
        )
        if mapping["data_availability_status"] not in DATA_AVAILABILITY_STATUSES:
            raise InvestmentDirectorResearchContextPackError(
                "source_tier_and_viewpoint_context source status invalid"
            )
        _require_string_list(
            mapping["what_was_checked"],
            f"source_tier_and_viewpoint_context.source_tier_summary[{index}].what_was_checked",
        )
    _require_string_list(
        result["available_source_buckets"],
        "source_tier_and_viewpoint_context.available_source_buckets",
    )
    independent_count = _require_non_negative_int(
        result["independent_source_count"],
        "source_tier_and_viewpoint_context.independent_source_count",
    )
    for key in (
        "consensus_status",
        "divergent_view_status",
        "opposing_view_status",
    ):
        if result[key] not in DATA_AVAILABILITY_STATUSES:
            raise InvestmentDirectorResearchContextPackError(
                f"source_tier_and_viewpoint_context.{key} invalid"
            )
    if independent_count < 2:
        for key in (
            "consensus_status",
            "divergent_view_status",
            "opposing_view_status",
        ):
            if result[key] != "not_assessable":
                raise InvestmentDirectorResearchContextPackError(
                    "fewer than two independent source buckets cannot claim viewpoint assessment"
                )
    _require_non_empty_string(
        result["viewpoint_boundary"],
        "source_tier_and_viewpoint_context.viewpoint_boundary",
    )
    _require_string_list(
        result["missing_viewpoint_evidence"],
        "source_tier_and_viewpoint_context.missing_viewpoint_evidence",
    )
    _require_true(
        result["not_for_trading_advice"],
        "source_tier_and_viewpoint_context.not_for_trading_advice",
    )
    return result


def _validate_director_framework_alignment(value: Any) -> dict[str, Any]:
    alignment = _require_mapping(value, "director_framework_alignment")
    required = (
        "schema_version",
        "framework_chain",
        "alignment_summary",
        "weak_links",
        "next_alignment_tasks",
        "not_for_trading_advice",
    )
    _require_fields(alignment, required, "director_framework_alignment")
    result = deepcopy(dict(alignment))
    _require_schema_version(
        result["schema_version"],
        INVESTMENT_DIRECTOR_FRAMEWORK_ALIGNMENT_SCHEMA_VERSION,
        "director_framework_alignment.schema_version",
    )
    chain = _require_mapping(
        result["framework_chain"],
        "director_framework_alignment.framework_chain",
    )
    required_chain = (
        "macro_policy_industry",
        "company_business_project_competitor_customer",
        "financial_cashflow_capex_rd_debt",
        "disclosure_delivery_risk_research_notes",
        "collision_and_judgment",
        "frontstage_display",
    )
    _require_fields(chain, required_chain, "director_framework_alignment.framework_chain")
    for key in required_chain:
        rows = _require_list(chain[key], f"director_framework_alignment.framework_chain.{key}")
        for index, row in enumerate(rows):
            mapping = _require_mapping(
                row,
                f"director_framework_alignment.framework_chain.{key}[{index}]",
            )
            _require_fields(
                mapping,
                ("requirement_id", "coverage_status", "blocks_llm_depth"),
                f"director_framework_alignment.framework_chain.{key}[{index}]",
            )
            _require_non_empty_string(
                mapping["requirement_id"],
                f"director_framework_alignment.framework_chain.{key}[{index}].requirement_id",
            )
            if mapping["coverage_status"] not in COVERAGE_STATUSES:
                raise InvestmentDirectorResearchContextPackError(
                    "director framework chain coverage status invalid"
                )
            _require_bool(
                mapping["blocks_llm_depth"],
                f"director_framework_alignment.framework_chain.{key}[{index}].blocks_llm_depth",
            )
    _require_non_empty_string(
        result["alignment_summary"],
        "director_framework_alignment.alignment_summary",
    )
    weak_links = _require_list(
        result["weak_links"],
        "director_framework_alignment.weak_links",
    )
    for index, item in enumerate(weak_links):
        mapping = _require_mapping(
            item,
            f"director_framework_alignment.weak_links[{index}]",
        )
        _require_fields(
            mapping,
            (
                "requirement_id",
                "coverage_status",
                "next_data_task",
                "blocks_llm_depth",
                "not_for_trading_advice",
            ),
            f"director_framework_alignment.weak_links[{index}]",
        )
        if mapping["coverage_status"] in {"covered", "not_applicable"}:
            raise InvestmentDirectorResearchContextPackError(
                "director framework weak_links must come from missing or partial coverage"
            )
        _require_non_empty_string(
            mapping["next_data_task"],
            f"director_framework_alignment.weak_links[{index}].next_data_task",
        )
        _require_true(
            mapping["not_for_trading_advice"],
            f"director_framework_alignment.weak_links[{index}].not_for_trading_advice",
        )
    if weak_links and _contains_full_coverage_claim(result["alignment_summary"]):
        raise InvestmentDirectorResearchContextPackError(
            "director framework alignment cannot claim full coverage while weak links exist"
        )
    _require_string_list(
        result["next_alignment_tasks"],
        "director_framework_alignment.next_alignment_tasks",
    )
    _require_true(
        result["not_for_trading_advice"],
        "director_framework_alignment.not_for_trading_advice",
    )
    return result


def _validate_frontstage_visualization_requirements(value: Any) -> dict[str, Any]:
    requirements = _require_mapping(value, "frontstage_visualization_requirements")
    required = (
        "schema_version",
        "conclusion_first_sections",
        "chart_ready_sections",
        "table_ready_sections",
        "material_backstage_sections",
        "missing_visualization_inputs",
        "html_report_mapping_summary",
        "not_for_trading_advice",
    )
    _require_fields(requirements, required, "frontstage_visualization_requirements")
    result = deepcopy(dict(requirements))
    _require_schema_version(
        result["schema_version"],
        INVESTMENT_DIRECTOR_FRONTSTAGE_VISUALIZATION_REQUIREMENTS_SCHEMA_VERSION,
        "frontstage_visualization_requirements.schema_version",
    )
    for key in (
        "conclusion_first_sections",
        "chart_ready_sections",
        "table_ready_sections",
        "material_backstage_sections",
    ):
        _require_string_list(
            result[key],
            f"frontstage_visualization_requirements.{key}",
        )
    missing_inputs = _require_list(
        result["missing_visualization_inputs"],
        "frontstage_visualization_requirements.missing_visualization_inputs",
    )
    for index, item in enumerate(missing_inputs):
        mapping = _require_mapping(
            item,
            f"frontstage_visualization_requirements.missing_visualization_inputs[{index}]",
        )
        _require_fields(
            mapping,
            (
                "requirement_id",
                "coverage_status",
                "required_evidence",
                "next_data_task",
            ),
            f"frontstage_visualization_requirements.missing_visualization_inputs[{index}]",
        )
        _require_non_empty_string(
            mapping["requirement_id"],
            f"frontstage_visualization_requirements.missing_visualization_inputs[{index}].requirement_id",
        )
        if mapping["coverage_status"] not in COVERAGE_STATUSES:
            raise InvestmentDirectorResearchContextPackError(
                "frontstage visualization coverage status invalid"
            )
        _require_string_list(
            mapping["required_evidence"],
            f"frontstage_visualization_requirements.missing_visualization_inputs[{index}].required_evidence",
        )
        _require_non_empty_string(
            mapping["next_data_task"],
            f"frontstage_visualization_requirements.missing_visualization_inputs[{index}].next_data_task",
        )
    _require_non_empty_string(
        result["html_report_mapping_summary"],
        "frontstage_visualization_requirements.html_report_mapping_summary",
    )
    _require_true(
        result["not_for_trading_advice"],
        "frontstage_visualization_requirements.not_for_trading_advice",
    )
    return result


def _validate_collision_question_set(value: Any) -> dict[str, Any]:
    question_set = _require_mapping(value, "collision_question_set")
    _require_fields(
        question_set,
        ("schema_version", "questions", "not_for_trading_advice"),
        "collision_question_set",
    )
    _require_schema_version(
        question_set["schema_version"],
        INVESTMENT_DIRECTOR_COLLISION_QUESTION_SET_SCHEMA_VERSION,
        "collision_question_set.schema_version",
    )
    questions = _require_list(question_set["questions"], "collision_question_set.questions")
    result_questions = [
        _validate_collision_question(item, f"collision_question_set.questions[{index}]")
        for index, item in enumerate(questions)
    ]
    _require_true(
        question_set["not_for_trading_advice"],
        "collision_question_set.not_for_trading_advice",
    )
    return {
        "schema_version": INVESTMENT_DIRECTOR_COLLISION_QUESTION_SET_SCHEMA_VERSION,
        "questions": result_questions,
        "not_for_trading_advice": True,
    }


def _validate_collision_question(value: Any, path: str) -> dict[str, Any]:
    question = _require_mapping(value, path)
    required = (
        "schema_version",
        "question",
        "category",
        "layer",
        "trigger_source",
        "evidence_trigger",
        "why_it_matters",
        "required_evidence",
        "available_evidence",
        "missing_evidence",
        "data_availability_status",
        "confidence_cap",
        "not_assessable_reason",
        "what_was_checked",
        "suggested_next_action",
        "not_for_trading_advice",
    )
    _require_fields(question, required, path)
    result = deepcopy(dict(question))
    _require_schema_version(
        result["schema_version"],
        INVESTMENT_DIRECTOR_COLLISION_QUESTION_SCHEMA_VERSION,
        f"{path}.schema_version",
    )
    for key in ("question", "category", "evidence_trigger", "why_it_matters", "suggested_next_action"):
        _require_non_empty_string(result[key], f"{path}.{key}")
    if result["layer"] not in COLLISION_LAYERS:
        raise InvestmentDirectorResearchContextPackError(f"{path}.layer invalid")
    if result["trigger_source"] not in COLLISION_TRIGGER_SOURCES:
        raise InvestmentDirectorResearchContextPackError(f"{path}.trigger_source invalid")
    for key in ("required_evidence", "available_evidence", "missing_evidence", "what_was_checked"):
        _require_string_list(result[key], f"{path}.{key}")
    if not result["what_was_checked"]:
        raise InvestmentDirectorResearchContextPackError(f"{path}.what_was_checked cannot be empty")
    if result["data_availability_status"] not in DATA_AVAILABILITY_STATUSES:
        raise InvestmentDirectorResearchContextPackError(
            f"{path}.data_availability_status invalid"
        )
    if result["confidence_cap"] not in CONFIDENCE_CAPS:
        raise InvestmentDirectorResearchContextPackError(f"{path}.confidence_cap invalid")
    if result["data_availability_status"] in {"missing", "not_assessable"}:
        _require_non_empty_string(
            result["not_assessable_reason"], f"{path}.not_assessable_reason"
        )
    _require_true(result["not_for_trading_advice"], f"{path}.not_for_trading_advice")
    _assert_not_vague_gap_text(result, path)
    return result


def _validate_coverage_item(value: Any, path: str) -> dict[str, Any]:
    item = _require_mapping(value, path)
    required = (
        "schema_version",
        "requirement_id",
        "requirement_name",
        "coverage_status",
        "currently_available_assets",
        "currently_llm_visible",
        "gap_description",
        "required_evidence",
        "next_data_task",
        "priority",
        "blocks_llm_depth",
        "covered_semantics",
        "not_for_trading_advice",
    )
    _require_fields(item, required, path)
    result = deepcopy(dict(item))
    _require_schema_version(
        result["schema_version"],
        INVESTMENT_DIRECTOR_COVERAGE_ITEM_SCHEMA_VERSION,
        f"{path}.schema_version",
    )
    _require_non_empty_string(result["requirement_id"], f"{path}.requirement_id")
    _require_non_empty_string(result["requirement_name"], f"{path}.requirement_name")
    if result["coverage_status"] not in COVERAGE_STATUSES:
        raise InvestmentDirectorResearchContextPackError(
            f"{path}.coverage_status invalid"
        )
    _require_string_list(result["currently_available_assets"], f"{path}.currently_available_assets")
    _require_bool(result["currently_llm_visible"], f"{path}.currently_llm_visible")
    _require_non_empty_string(result["gap_description"], f"{path}.gap_description")
    _require_string_list(result["required_evidence"], f"{path}.required_evidence")
    _require_non_empty_string(result["next_data_task"], f"{path}.next_data_task")
    if result["priority"] not in PRIORITIES:
        raise InvestmentDirectorResearchContextPackError(f"{path}.priority invalid")
    _require_bool(result["blocks_llm_depth"], f"{path}.blocks_llm_depth")
    semantics = _require_mapping(result["covered_semantics"], f"{path}.covered_semantics")
    _require_fields(
        semantics,
        (
            "framework_exists",
            "material_or_structured_input_exists",
            "can_enter_llm_context",
        ),
        f"{path}.covered_semantics",
    )
    for key in (
        "framework_exists",
        "material_or_structured_input_exists",
        "can_enter_llm_context",
    ):
        _require_bool(semantics[key], f"{path}.covered_semantics.{key}")
    if result["coverage_status"] == "covered" and not all(semantics.values()):
        raise InvestmentDirectorResearchContextPackError(
            f"{path}.covered requires framework, material, and LLM visibility"
        )
    if result["coverage_status"] != "covered":
        if not result["required_evidence"] or not result["next_data_task"].strip():
            raise InvestmentDirectorResearchContextPackError(
                f"{path} missing/partial item requires evidence and next task"
            )
    _require_true(result["not_for_trading_advice"], f"{path}.not_for_trading_advice")
    _assert_not_vague_gap_text(result, path)
    return result


def _validate_llm_context_prompt_payload(value: Any) -> dict[str, Any]:
    payload = _require_mapping(value, "llm_context_prompt_payload")
    required = (
        "schema_version",
        "role",
        "task",
        "analysis_requirements",
        "available_materials_summary",
        "core_conflicts_to_analyze",
        "collision_questions",
        "missing_coverage_boundaries",
        "required_output_sections",
        "output_boundaries",
        "not_for_trading_advice",
    )
    _require_fields(payload, required, "llm_context_prompt_payload")
    result = deepcopy(dict(payload))
    _require_schema_version(
        result["schema_version"],
        INVESTMENT_DIRECTOR_LLM_CONTEXT_PROMPT_PAYLOAD_SCHEMA_VERSION,
        "llm_context_prompt_payload.schema_version",
    )
    if result["role"] != "A股专业基本面研究员":
        raise InvestmentDirectorResearchContextPackError("prompt role invalid")
    if result["task"] != "形成投资总监式基本面分析":
        raise InvestmentDirectorResearchContextPackError("prompt task invalid")
    _require_string_list(
        result["analysis_requirements"],
        "llm_context_prompt_payload.analysis_requirements",
    )
    if not any("Do not merely repeat metrics" in item for item in result["analysis_requirements"]):
        raise InvestmentDirectorResearchContextPackError(
            "prompt must include metric repetition guard"
        )
    for key in (
        "available_materials_summary",
        "core_conflicts_to_analyze",
        "collision_questions",
        "missing_coverage_boundaries",
        "required_output_sections",
    ):
        _require_list(result[key], f"llm_context_prompt_payload.{key}")
    if len(result["required_output_sections"]) < 11:
        raise InvestmentDirectorResearchContextPackError(
            "prompt required_output_sections too narrow"
        )
    boundaries = _require_mapping(
        result["output_boundaries"], "llm_context_prompt_payload.output_boundaries"
    )
    if boundaries.get("trading_advice_allowed") is not False:
        raise InvestmentDirectorResearchContextPackError(
            "prompt must disallow market action advice"
        )
    if len(json.dumps(result, ensure_ascii=False)) > 18000:
        raise InvestmentDirectorResearchContextPackError("prompt payload is too large")
    _require_true(
        result["not_for_trading_advice"],
        "llm_context_prompt_payload.not_for_trading_advice",
    )
    assert_no_investment_director_context_forbidden_markers(result)
    return result


def _collect_asset_entries(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []

    def add_entry(
        *,
        asset_id: str,
        source_asset: str,
        trigger_source: str,
        value: Any,
        has_material: bool | None = None,
        llm_visible: bool | None = None,
    ) -> None:
        if not _has_material_value(value):
            return
        mapping = value if isinstance(value, Mapping) else {}
        visible = _bool_from_mapping(
            mapping,
            ("currently_llm_visible", "llm_visible", "model_visible"),
            default=True,
        )
        if llm_visible is not None:
            visible = llm_visible
        material = _item_has_material(value) if has_material is None else has_material
        entries.append(
            {
                "asset_id": asset_id,
                "source_asset": source_asset,
                "trigger_source": trigger_source,
                "text": _searchable_text(value),
                "has_material": material,
                "llm_visible": visible,
            }
        )

    snapshot = _mapping_or_empty(source.get("old_report_frontstage_snapshot"))
    for key in FRONTSTAGE_CONTEXT_FIELDS:
        add_entry(
            asset_id=f"old_report_frontstage_snapshot.{key}",
            source_asset="old_report_frontstage_snapshot",
            trigger_source="html_snapshot",
            value={key: snapshot.get(key)},
            has_material=_has_material_value(snapshot.get(key)),
            llm_visible=True,
        )

    p0 = _mapping_or_empty(source.get("research_intelligence_p0"))
    for key in (
        "source_hierarchy",
        "evidence_classification",
        "strategy_driver_map",
        "business_financial_cross_validation",
        "rule_triggered_contradictions",
        "manual_review_items",
        "ir_question_candidates",
    ):
        for index, item in enumerate(_iter_component_items(p0.get(key))):
            add_entry(
                asset_id=f"research_intelligence_p0.{key}[{index}]",
                source_asset="research_intelligence_p0",
                trigger_source="p0",
                value=item,
                has_material=_item_has_material(item, question_counts_as_material=key in {"manual_review_items", "ir_question_candidates"}),
            )

    p1 = _mapping_or_empty(source.get("research_intelligence_p1"))
    for key in (
        "driver_matrix",
        "not_assessable_drivers",
        "driver_research_questions",
        "source_bucket_summary",
    ):
        for index, item in enumerate(_iter_component_items(p1.get(key))):
            add_entry(
                asset_id=f"research_intelligence_p1.{key}[{index}]",
                source_asset="research_intelligence_p1",
                trigger_source="p1",
                value=item,
                has_material=_item_has_material(item),
            )

    for request_key, trigger_source in (
        ("research_questions_p0", "p0"),
        ("research_questions_p1", "p1"),
        ("ticker_research_context_skeleton", "derived"),
        ("evidence_aware_research_pack", "evidence_pack"),
        ("professional_compact_brief", "derived"),
    ):
        payload = _mapping_or_empty(source.get(request_key))
        for index, item in enumerate(_iter_component_items(payload)):
            add_entry(
                asset_id=f"{request_key}[{index}]",
                source_asset=request_key,
                trigger_source=trigger_source,
                value=item,
                has_material=_item_has_material(item),
            )
    return entries


def _coverage_item_from_requirement(
    requirement: Mapping[str, Any],
    entries: list[dict[str, Any]],
    not_applicable: set[str],
) -> dict[str, Any]:
    requirement_id = str(requirement["requirement_id"])
    related = [
        entry
        for entry in entries
        if _entry_matches_requirement(entry, requirement)
    ]
    framework_exists = bool(related)
    material_entries = [entry for entry in related if entry["has_material"]]
    material_exists = bool(material_entries)
    llm_visible = bool(material_entries and any(entry["llm_visible"] for entry in material_entries))
    if requirement_id in not_applicable:
        status = "not_applicable"
    elif framework_exists and material_exists and llm_visible:
        status = "covered"
    elif framework_exists and material_exists:
        status = "partial_but_not_llm_visible"
    elif framework_exists:
        status = "framework_exists_but_missing_data"
    else:
        status = "missing"
    return {
        "schema_version": INVESTMENT_DIRECTOR_COVERAGE_ITEM_SCHEMA_VERSION,
        "requirement_id": requirement_id,
        "requirement_name": str(requirement["requirement_name"]),
        "coverage_status": status,
        "currently_available_assets": [
            entry["asset_id"] for entry in related[:8]
        ],
        "currently_llm_visible": llm_visible,
        "gap_description": _coverage_gap_description(
            requirement=requirement,
            status=status,
            related_count=len(related),
        ),
        "required_evidence": list(requirement["required_evidence"]),
        "next_data_task": _coverage_next_data_task(requirement, status),
        "priority": str(requirement["priority"]),
        "blocks_llm_depth": bool(requirement.get("blocks_llm_depth", True))
        and status != "covered"
        and status != "not_applicable",
        "covered_semantics": {
            "framework_exists": framework_exists,
            "material_or_structured_input_exists": material_exists,
            "can_enter_llm_context": llm_visible,
        },
        "not_for_trading_advice": True,
    }


def _coverage_gap_description(
    *,
    requirement: Mapping[str, Any],
    status: str,
    related_count: int,
) -> str:
    name = str(requirement["requirement_name"])
    if status == "covered":
        return f"{name} has a supplied framework, structured material, and adapter-visible context."
    if status == "partial_but_not_llm_visible":
        return f"{name} has structured material, but the supplied asset was marked as not currently model-visible."
    if status == "framework_exists_but_missing_data":
        return f"{name} has {related_count} supplied framework or question item(s), but lacks concrete structured evidence."
    if status == "not_applicable":
        return f"{name} is marked not applicable by the explicit request."
    return f"{name} has no supplied framework or structured evidence in the request."


def _coverage_next_data_task(requirement: Mapping[str, Any], status: str) -> str:
    if status == "covered":
        return "Keep this item visible in the next model context and refresh only when source inputs change."
    explicit_task = requirement.get("next_data_task")
    if isinstance(explicit_task, str) and explicit_task.strip():
        return explicit_task.strip()
    if status == "partial_but_not_llm_visible":
        return f"Move the supplied {requirement['requirement_id']} evidence summary into the next model-visible context."
    if status == "framework_exists_but_missing_data":
        return f"Collect the concrete evidence listed for {requirement['requirement_id']} before drawing a company-level conclusion."
    if status == "not_applicable":
        return "No follow-up required unless the strategy scope changes."
    return f"Add an explicit framework and the concrete evidence listed for {requirement['requirement_id']}."


def _entry_matches_requirement(
    entry: Mapping[str, Any],
    requirement: Mapping[str, Any],
) -> bool:
    text = " ".join(
        [
            str(entry.get("asset_id", "")),
            str(entry.get("source_asset", "")),
            str(entry["text"]),
        ]
    ).casefold()
    normalized = _normalise_marker(text)
    for keyword in requirement["keywords"]:
        keyword_text = str(keyword).casefold()
        if keyword_text in text:
            return True
        keyword_normalized = _normalise_marker(str(keyword))
        if keyword_normalized and keyword_normalized in normalized:
            return True
    return False


def _coverage_status_counts(items: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    counts = {status: 0 for status in COVERAGE_STATUSES}
    for item in items:
        status = item.get("coverage_status")
        if status in counts:
            counts[str(status)] += 1
    return counts


def _coverage_items_from_map(coverage_map: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(coverage_map, Mapping):
        return []
    items = coverage_map.get("items", [])
    if not isinstance(items, list):
        return []
    return [deepcopy(dict(item)) for item in items if isinstance(item, Mapping)]


def _chain_statuses(
    by_id: Mapping[str, Mapping[str, Any]],
    requirement_ids: Iterable[str],
) -> list[dict[str, Any]]:
    rows = []
    for requirement_id in requirement_ids:
        item = by_id.get(requirement_id)
        if item is None:
            rows.append(
                {
                    "requirement_id": requirement_id,
                    "coverage_status": "missing",
                    "blocks_llm_depth": True,
                }
            )
            continue
        rows.append(
            {
                "requirement_id": requirement_id,
                "coverage_status": item["coverage_status"],
                "blocks_llm_depth": item["blocks_llm_depth"],
            }
        )
    return rows


def _normalize_viewpoint_status(value: Any) -> str:
    text = str(value or "").strip()
    mapping = {
        "consensus": "available",
        "divergence": "partial",
        "contradiction": "partial",
        "not_assessable": "not_assessable",
    }
    text = mapping.get(text, text)
    return text if text in DATA_AVAILABILITY_STATUSES else "not_assessable"


def _non_negative_int_or_default(value: Any, default: int) -> int:
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return max(default, 0)


def _contains_full_coverage_claim(value: str) -> bool:
    lowered = value.casefold()
    return any(
        marker in lowered or marker in value
        for marker in (
            "fully covered",
            "complete coverage",
            "完整覆盖",
            "已完整覆盖",
            "全部覆盖",
        )
    )


def _non_empty_frontstage_section_names(
    frontstage: Mapping[str, Any],
    fields: Iterable[str],
) -> list[str]:
    return [field for field in fields if _has_material_value(frontstage.get(field))]


def _normalized_research_questions(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    p0 = _mapping_or_empty(source.get("research_intelligence_p0"))
    p1 = _mapping_or_empty(source.get("research_intelligence_p1"))
    for key in ("manual_review_items", "ir_question_candidates", "rule_triggered_contradictions"):
        for item in _iter_component_items(p0.get(key)):
            result.append(normalize_research_question_item(item, trigger_source="p0"))
    for item in _iter_component_items(_mapping_or_empty(source.get("research_questions_p0")).get("questions")):
        result.append(normalize_research_question_item(item, trigger_source="p0"))
    for key in ("driver_research_questions", "driver_matrix", "not_assessable_drivers"):
        for item in _iter_component_items(p1.get(key)):
            result.append(normalize_research_question_item(item, trigger_source="p1"))
    for item in _iter_component_items(_mapping_or_empty(source.get("research_questions_p1")).get("questions")):
        result.append(normalize_research_question_item(item, trigger_source="p1"))
    for item in _questions_from_ticker_context(source.get("ticker_research_context_skeleton")):
        result.append(normalize_research_question_item(item, trigger_source="derived"))
    for item in _questions_from_evidence_pack(source.get("evidence_aware_research_pack")):
        result.append(normalize_research_question_item(item, trigger_source="evidence_pack"))
    return _dedupe_question_items(result)


def _matching_question_items(
    keywords: Iterable[str],
    items: Iterable[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    return [
        item
        for item in items
        if _keywords_match_text(keywords, _searchable_text(item))
    ]


def _collision_question_from_blueprint(
    *,
    blueprint: Mapping[str, Any],
    matches: list[Mapping[str, Any]],
    checked_assets: list[str],
) -> dict[str, Any]:
    primary = matches[0] if matches else {}
    required_evidence = _dedupe_preserve_order(
        _string_values(primary.get("required_evidence"))
        or list(blueprint["required_evidence"])
    )
    available_evidence = _dedupe_preserve_order(
        _string_values(primary.get("available_evidence"))
    )
    missing_evidence = _dedupe_preserve_order(
        _string_values(primary.get("missing_evidence")) or required_evidence
    )
    status = _normalize_data_status(primary.get("data_availability_status"))
    if not matches:
        status = "missing"
    elif available_evidence and missing_evidence and status == "available":
        status = "partial"
    confidence_cap = _normalize_confidence_cap(primary.get("confidence_cap"))
    if status in {"missing", "not_assessable"} and confidence_cap == "high":
        confidence_cap = "not_assessable"
    question_text = str(primary.get("question") or blueprint["question"])
    not_assessable_reason = str(primary.get("not_assessable_reason") or "")
    if status in {"missing", "not_assessable"} and not not_assessable_reason:
        not_assessable_reason = str(blueprint["not_assessable_reason"])
    evidence_trigger = str(primary.get("evidence_trigger") or "")
    if not evidence_trigger:
        evidence_trigger = (
            f"derived:{blueprint['category']} checked against supplied P0/P1/frontstage/evidence-pack assets"
        )
    what_was_checked = _dedupe_preserve_order(
        _string_values(primary.get("what_was_checked")) or checked_assets
    )
    if matches:
        what_was_checked.extend(
            f"matched:{str(item.get('category') or item.get('question'))[:80]}"
            for item in matches[:3]
        )
    what_was_checked = _dedupe_preserve_order(what_was_checked)
    return {
        "schema_version": INVESTMENT_DIRECTOR_COLLISION_QUESTION_SCHEMA_VERSION,
        "question": question_text,
        "category": str(blueprint["category"]),
        "layer": _normalize_layer(primary.get("layer") or blueprint["layer"]),
        "trigger_source": _normalize_trigger_source(primary.get("trigger_source") or "derived"),
        "evidence_trigger": evidence_trigger,
        "why_it_matters": str(primary.get("why_it_matters") or blueprint["why_it_matters"]),
        "required_evidence": required_evidence,
        "available_evidence": available_evidence,
        "missing_evidence": missing_evidence,
        "data_availability_status": status,
        "confidence_cap": confidence_cap,
        "not_assessable_reason": not_assessable_reason,
        "what_was_checked": what_was_checked,
        "suggested_next_action": str(
            primary.get("suggested_next_action")
            or _next_action_from_evidence(required_evidence, missing_evidence)
        ),
        "not_for_trading_advice": True,
    }


def _compact_materials_summary(source_asset_summary: Any) -> list[dict[str, Any]]:
    summary = _mapping_or_empty(source_asset_summary)
    components = _iter_component_items(summary.get("components"))
    return [
        {
            "asset_id": item.get("asset_id"),
            "present": item.get("present"),
            "visible_in_adapter_pack": item.get("visible_in_adapter_pack"),
            "key_fields_present": list(item.get("key_fields_present", []))[:8],
        }
        for item in components
        if item.get("present")
    ]


def _compact_collision_question(question: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "question": question.get("question"),
        "category": question.get("category"),
        "evidence_trigger": question.get("evidence_trigger"),
        "data_availability_status": question.get("data_availability_status"),
        "confidence_cap": question.get("confidence_cap"),
        "missing_evidence": list(question.get("missing_evidence", []))[:4],
        "what_was_checked": list(question.get("what_was_checked", []))[:4],
    }


def _compact_coverage_boundary(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": item.get("requirement_id"),
        "coverage_status": item.get("coverage_status"),
        "gap_description": item.get("gap_description"),
        "required_evidence": list(item.get("required_evidence", []))[:4],
        "next_data_task": item.get("next_data_task"),
        "blocks_llm_depth": item.get("blocks_llm_depth"),
    }


def _source_hierarchy_summary(p0: Mapping[str, Any], p1: Mapping[str, Any]) -> list[dict[str, Any]]:
    source_hierarchy = _iter_component_items(p0.get("source_hierarchy"))
    bucket_summary = _mapping_or_empty(p1.get("source_bucket_summary"))
    result = [
        {
            "source_name": item.get("source_name") or item.get("source_tier") or "supplied_source",
            "evidence_type": item.get("evidence_type") or item.get("source_confidence") or "structured_context",
            "data_availability_status": _normalize_data_status(item.get("data_availability_status")),
            "what_was_checked": _string_values(item.get("what_was_checked")),
        }
        for item in source_hierarchy
    ]
    if bucket_summary:
        result.append(
            {
                "source_name": "source_bucket_summary",
                "evidence_type": "independence_summary",
                "data_availability_status": "partial"
                if bucket_summary.get("source_buckets")
                else "not_assessable",
                "what_was_checked": _string_values(bucket_summary.get("source_buckets"))
                or ["source_bucket_summary"],
            }
        )
    return result


def _combined_list_field(mapping: Mapping[str, Any], key: str) -> list[Any]:
    return deepcopy(list(_iter_component_items(mapping.get(key))))


def _manual_review_items(
    source: Mapping[str, Any],
    question_items: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    del source
    return [
        deepcopy(item)
        for item in question_items
        if item["trigger_source"] == "p0" and item["category"] not in {"ir", "ir_questions"}
    ]


def _ir_question_candidates(
    source: Mapping[str, Any],
    question_items: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    p0 = _mapping_or_empty(source.get("research_intelligence_p0"))
    result = [normalize_research_question_item(item, trigger_source="p0") for item in _iter_component_items(p0.get("ir_question_candidates"))]
    result.extend(
        deepcopy(item)
        for item in question_items
        if "ir" in _searchable_text(item).casefold()
    )
    return _dedupe_question_items(result)


def _not_assessable_items(
    source: Mapping[str, Any],
    question_items: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    p1 = _mapping_or_empty(source.get("research_intelligence_p1"))
    result = [
        normalize_research_question_item(item, trigger_source="p1")
        for item in _iter_component_items(p1.get("not_assessable_drivers"))
    ]
    result.extend(
        deepcopy(item)
        for item in question_items
        if item["data_availability_status"] == "not_assessable"
        or item["confidence_cap"] == "not_assessable"
    )
    return _dedupe_question_items(result)


def _missing_evidence_items(
    source: Mapping[str, Any],
    question_items: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    del source
    result = []
    for item in question_items:
        if item["missing_evidence"] or item["data_availability_status"] in {"missing", "partial", "not_assessable"}:
            result.append(
                {
                    "question": item["question"],
                    "category": item["category"],
                    "missing_evidence": list(item["missing_evidence"]),
                    "data_availability_status": item["data_availability_status"],
                    "confidence_cap": item["confidence_cap"],
                    "not_assessable_reason": item["not_assessable_reason"],
                    "not_for_trading_advice": True,
                }
            )
    return result


def _proxy_guardrails_from_items(items: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    guardrails = [
        {
            "guardrail_id": "capex_requires_project_revenue_bridge",
            "guardrail": "capex is an input; require project progress, delivery, revenue conversion, and margin evidence.",
            "related_keywords": ["capex", "capital expenditure", "项目进度", "收入转化"],
        },
        {
            "guardrail_id": "r_and_d_requires_product_customer_conversion",
            "guardrail": "R&D is an input; require product, customer, and revenue conversion evidence.",
            "related_keywords": ["R&D", "研发", "产品转化"],
        },
        {
            "guardrail_id": "contract_liability_proxy_requires_order_fulfillment",
            "guardrail": "contract liabilities are a proxy only; require order, fulfillment, collection, and independently disclosed backlog evidence.",
            "related_keywords": ["contract liabilities", "合同负债", "backlog"],
        },
        {
            "guardrail_id": "external_theme_requires_company_transmission",
            "guardrail": "external themes require company order, delivery, collection, revenue, and margin transmission evidence.",
            "related_keywords": ["industry", "policy", "theme", "行业", "政策", "主题"],
        },
    ]
    text = _searchable_text(list(items))
    return [
        {**guardrail, "triggered_by_supplied_items": _keywords_match_text(guardrail["related_keywords"], text), "not_for_trading_advice": True}
        for guardrail in guardrails
    ]


def _company_transmission_path_items(p1: Mapping[str, Any]) -> list[dict[str, Any]]:
    result = []
    for item in _iter_component_items(p1.get("driver_matrix")):
        path = item.get("company_transmission_path")
        if path:
            result.append(
                {
                    "driver_factor": item.get("driver_factor"),
                    "layer": _normalize_layer(item.get("layer")),
                    "company_transmission_path": path,
                    "data_availability_status": _normalize_data_status(item.get("data_availability_status")),
                    "confidence_cap": _normalize_confidence_cap(item.get("confidence_cap")),
                    "not_for_trading_advice": True,
                }
            )
    return result


def _driver_like(item: Mapping[str, Any]) -> bool:
    text = _searchable_text(item).casefold()
    return any(marker in text for marker in ("driver", "驱动", "capex", "r&d", "研发", "订单"))


def _questions_from_ticker_context(value: Any) -> list[Mapping[str, Any]]:
    context = _mapping_or_empty(value)
    questions = []
    research_questions = _mapping_or_empty(context.get("research_questions"))
    questions.extend(_iter_component_items(research_questions.get("questions")))
    data_gap_plan = _mapping_or_empty(context.get("data_gap_plan"))
    for gap in _iter_component_items(data_gap_plan.get("data_gaps")):
        questions.append(
            {
                "question": gap.get("description"),
                "category": gap.get("category"),
                "required_evidence": gap.get("required_data"),
                "data_availability_status": gap.get("current_evidence_status"),
                "what_was_checked": [gap.get("gap_id")] if gap.get("gap_id") else [],
            }
        )
    return questions


def _questions_from_evidence_pack(value: Any) -> list[Mapping[str, Any]]:
    pack = _mapping_or_empty(value)
    result = []
    for section in _iter_component_items(pack.get("sections")):
        for item in _iter_component_items(section.get("items")):
            if "question" in _searchable_text(item).casefold() or item.get("data_gaps"):
                result.append(
                    {
                        "question": item.get("question") or item.get("question_text") or item.get("item_id"),
                        "category": section.get("section_id"),
                        "required_evidence": item.get("required_data") or item.get("required_evidence"),
                        "data_availability_status": item.get("current_evidence_status") or section.get("evidence_status"),
                        "what_was_checked": [section.get("section_id"), item.get("item_id")],
                    }
                )
    return result


def _iter_component_items(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        if "questions" in value and isinstance(value["questions"], list):
            return [item for item in value["questions"] if isinstance(item, Mapping)]
        if "items" in value and isinstance(value["items"], list):
            return [item for item in value["items"] if isinstance(item, Mapping)]
        return [value]
    if isinstance(value, list):
        result = []
        for item in value:
            if isinstance(item, Mapping):
                result.append(item)
            elif isinstance(item, list):
                result.extend(_iter_component_items(item))
        return result
    return []


def _dedupe_question_items(items: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result = []
    seen = set()
    for item in items:
        key = (
            str(item.get("question")),
            str(item.get("category")),
            str(item.get("trigger_source")),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(deepcopy(dict(item)))
    return result


def _item_has_material(value: Any, *, question_counts_as_material: bool = False) -> bool:
    if isinstance(value, Mapping):
        status = _normalize_data_status(
            _first_present(value, ("data_availability_status", "current_evidence_status", "validation_status"))
        )
        if status == "available":
            return True
        if _string_values(value.get("available_evidence")) or _string_values(value.get("evidence_for")):
            return True
        if question_counts_as_material and _has_material_value(_first_present(value, ("question", "question_text", "research_question"))):
            return True
        if any(
            _has_material_value(value.get(key))
            for key in (
                "business_composition_summary",
                "financial_quality_summary",
                "core_conclusion",
                "core_conflict",
                "value",
            )
        ):
            return True
        return False
    return _has_material_value(value)


def _has_material_value(value: Any) -> bool:
    if value in (None, "", [], {}):
        return False
    if isinstance(value, Mapping):
        return any(_has_material_value(child) for child in value.values())
    if isinstance(value, list):
        return any(_has_material_value(item) for item in value)
    return True


def _bool_from_mapping(
    mapping: Mapping[str, Any],
    keys: tuple[str, ...],
    *,
    default: bool,
) -> bool:
    for key in keys:
        if key in mapping and isinstance(mapping[key], bool):
            return bool(mapping[key])
    return default


def _present_field_names(value: Any) -> list[str]:
    if not isinstance(value, Mapping):
        return []
    return [str(key) for key, child in value.items() if _has_material_value(child)][:12]


def _source_asset_presence_sentence(components: Iterable[Mapping[str, Any]]) -> str:
    present = [item["asset_id"] for item in components if item["present"]]
    if not present:
        return "No reusable research assets were supplied."
    return "Supplied reusable assets: " + ", ".join(present)


def _checked_asset_names(source: Mapping[str, Any]) -> list[str]:
    assets = [
        key
        for key in (
            "research_intelligence_p0",
            "research_questions_p0",
            "research_intelligence_p1",
            "research_questions_p1",
            "ticker_research_context_skeleton",
            "evidence_aware_research_pack",
            "old_report_frontstage_snapshot",
            "professional_compact_brief",
        )
        if _has_material_value(source.get(key))
    ]
    return assets or ["explicit request payload"]


def _checked_fields_from_item(item: Mapping[str, Any]) -> list[str]:
    fields = [
        key
        for key in (
            "required_evidence",
            "available_evidence",
            "missing_evidence",
            "data_availability_status",
            "confidence_cap",
            "company_transmission_path",
            "evidence_trigger",
        )
        if _has_material_value(item.get(key))
    ]
    return fields or ["supplied structured research question"]


def _evidence_trigger_from_normalized(item: Mapping[str, Any]) -> str:
    status = item["data_availability_status"]
    category = item["category"]
    if status in {"missing", "not_assessable"}:
        return f"missing_or_not_assessable:{category}"
    if item["missing_evidence"]:
        return f"partial_evidence_gap:{category}"
    return f"supplied_structured_item:{category}"


def _next_action_from_evidence(
    required_evidence: Iterable[str],
    missing_evidence: Iterable[str],
) -> str:
    missing = _string_values(list(missing_evidence)) or _string_values(list(required_evidence))
    if missing:
        return "Collect and map: " + "; ".join(missing[:4])
    return "Keep the available evidence mapped into the next model context."


def _keywords_match_text(keywords: Iterable[str], text: str) -> bool:
    lowered = text.casefold()
    normalized = _normalise_marker(text)
    for keyword in keywords:
        keyword_text = str(keyword).casefold()
        keyword_normalized = _normalise_marker(str(keyword))
        if keyword_text and keyword_text in lowered:
            return True
        if keyword_normalized and keyword_normalized in normalized:
            return True
    return False


def _searchable_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _mapping_or_empty(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _first_present(mapping: Mapping[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value not in (None, "", [], {}):
            return value
    return None


def _normalize_layer(value: Any) -> str:
    text = str(value or "").strip()
    mapping = {
        "policy": "macro",
        "supply_chain": "industry",
        "commodity": "industry",
        "business": "company",
    }
    text = mapping.get(text, text)
    return text if text in COLLISION_LAYERS else "company"


def _normalize_trigger_source(value: Any) -> str:
    text = str(value or "").strip()
    return text if text in COLLISION_TRIGGER_SOURCES else "derived"


def _normalize_data_status(value: Any) -> str:
    text = str(value or "").strip()
    mapping = {
        "validated": "available",
        "partially_validated": "partial",
        "weak": "partial",
        "contradicted": "partial",
        "data_gap": "missing",
        "framework_inference": "partial",
        "provider_candidate": "partial",
        "pending_official_verification": "partial",
    }
    text = mapping.get(text, text)
    return text if text in DATA_AVAILABILITY_STATUSES else "not_assessable"


def _normalize_confidence_cap(value: Any) -> str:
    text = str(value or "").strip()
    return text if text in CONFIDENCE_CAPS else "low"


def _string_values(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, Mapping):
        return [str(item).strip() for item in value.values() if str(item).strip()]
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
        raise InvestmentDirectorResearchContextPackError(f"{field} must be a mapping")
    return value


def _require_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise InvestmentDirectorResearchContextPackError(f"{path} must be a list")
    return value


def _require_fields(value: Mapping[str, Any], fields: tuple[str, ...], path: str) -> None:
    missing = [field for field in fields if field not in value]
    if missing:
        raise InvestmentDirectorResearchContextPackError(
            f"{path} missing required fields: {missing}"
        )


def _require_schema_version(value: Any, expected: str, path: str) -> None:
    if value != expected:
        raise InvestmentDirectorResearchContextPackError(f"{path} must be {expected}")


def _require_non_empty_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvestmentDirectorResearchContextPackError(
            f"{path} must be a non-empty string"
        )
    return value


def _require_optional_string(value: Any, path: str) -> None:
    if value is not None and not isinstance(value, str):
        raise InvestmentDirectorResearchContextPackError(f"{path} must be string or null")


def _require_string_list(value: Any, path: str) -> list[str]:
    if not isinstance(value, list):
        raise InvestmentDirectorResearchContextPackError(f"{path} must be a list")
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise InvestmentDirectorResearchContextPackError(f"{path}[{index}] must be string")
    return value


def _require_bool(value: Any, path: str) -> None:
    if not isinstance(value, bool):
        raise InvestmentDirectorResearchContextPackError(f"{path} must be bool")


def _require_non_negative_int(value: Any, path: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise InvestmentDirectorResearchContextPackError(f"{path} must be a non-negative int")
    return value


def _require_true(value: Any, path: str) -> None:
    if value is not True:
        raise InvestmentDirectorResearchContextPackError(f"{path} must be true")


def _reject_bytes(value: Any, path: str) -> None:
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise InvestmentDirectorResearchContextPackError(f"{path} contains raw bytes")
    if isinstance(value, Mapping):
        for key, child in value.items():
            _reject_bytes(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_bytes(child, f"{path}[{index}]")


def _reject_forbidden_keys(value: Any, path: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized = _normalise_marker(key_text)
            if key_text not in ALLOWED_EXACT_KEYS and (
                key_text in FORBIDDEN_REQUEST_KEYS
                or normalized in {_normalise_marker(item) for item in FORBIDDEN_REQUEST_KEYS}
            ):
                raise InvestmentDirectorResearchContextPackError(
                    f"{path} contains forbidden key: {key_text}"
                )
            _reject_forbidden_keys(child, f"{path}.{key_text}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_forbidden_keys(child, f"{path}[{index}]")


def _find_raw_or_secret_marker(value: Any) -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text not in ALLOWED_EXACT_KEYS:
                key_finding = _raw_text_finding(key_text)
                if key_finding:
                    return key_finding
            child_finding = _find_raw_or_secret_marker(child)
            if child_finding:
                return child_finding
        return None
    if isinstance(value, (list, tuple, set)):
        for child in value:
            child_finding = _find_raw_or_secret_marker(child)
            if child_finding:
                return child_finding
        return None
    if isinstance(value, str):
        return _raw_text_finding(value)
    return None


def _raw_text_finding(value: str) -> str | None:
    if _looks_like_secret_text(value):
        return "secret_like_string"
    if HTML_CONTENT_RE.search(value):
        return "raw_html"
    lowered = value.casefold()
    separator = _normalize_separator_text(value)
    normalized = _normalise_marker(value)
    for marker in RAW_BACKEND_MARKERS:
        marker_lower = marker.casefold()
        if marker_lower == ".env" and ".env" in lowered:
            return marker
        if marker_lower in lowered or _normalize_separator_text(marker) in separator:
            return marker
        marker_normalized = _normalise_marker(marker)
        if marker_normalized and marker_normalized in normalized:
            return marker
    if re.search(r"(?<![a-z0-9_])token(?![a-z0-9_])", normalized):
        return "token"
    return None


def _find_market_or_responsibility_marker(value: Any) -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text not in ALLOWED_EXACT_KEYS:
                finding = _market_or_responsibility_text_finding(key_text)
                if finding:
                    return finding
            child_finding = _find_market_or_responsibility_marker(child)
            if child_finding:
                return child_finding
        return None
    if isinstance(value, (list, tuple, set)):
        for child in value:
            child_finding = _find_market_or_responsibility_marker(child)
            if child_finding:
                return child_finding
        return None
    if isinstance(value, str):
        return _market_or_responsibility_text_finding(value)
    return None


def _market_or_responsibility_text_finding(value: str) -> str | None:
    lowered = value.casefold()
    normalized = _normalise_marker(value)
    for word in MARKET_ACTION_WORDS:
        if re.search(rf"(?<![a-z0-9_]){re.escape(word)}(?![a-z0-9_])", normalized):
            return word
    for phrase in MARKET_ACTION_PHRASES:
        if phrase in lowered or _normalize_separator_text(phrase) in _normalize_separator_text(value):
            return phrase
    for marker in MARKET_ACTION_CJK_MARKERS:
        if marker in value:
            return marker
    for marker in USER_RESPONSIBILITY_SHIFT_MARKERS:
        if marker.casefold() in lowered or marker in value:
            return marker
    return None


def _find_positive_overread(value: Any) -> str | None:
    if isinstance(value, Mapping):
        for child in value.values():
            finding = _find_positive_overread(child)
            if finding:
                return finding
        return None
    if isinstance(value, (list, tuple, set)):
        for child in value:
            finding = _find_positive_overread(child)
            if finding:
                return finding
        return None
    if not isinstance(value, str):
        return None
    lowered = value.casefold()
    for marker in POSITIVE_OVERREAD_MARKERS:
        if marker.casefold() in lowered:
            return marker
    return None


def _assert_not_vague_gap_text(value: Any, path: str) -> None:
    serialized = _searchable_text(value).casefold()
    for marker in VAGUE_GAP_MARKERS:
        if marker.casefold() in serialized:
            raise InvestmentDirectorResearchContextPackError(
                f"{path} contains vague gap marker"
            )


def _looks_like_secret_text(value: str) -> bool:
    for pattern in SECRET_LIKE_PATTERNS:
        if pattern.search(value):
            return True
    compact = value.strip()
    if len(compact) < 32 or re.search(r"\s", compact):
        return False
    has_upper = any(char.isupper() for char in compact)
    has_lower = any(char.islower() for char in compact)
    has_digit = any(char.isdigit() for char in compact)
    return has_upper and has_lower and has_digit


def _normalise_marker(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().casefold()).strip("_")


def _normalize_separator_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[_-]+", " ", value.strip().casefold())).strip()


_BASE_COVERAGE_REQUIREMENTS = (
    {
        "requirement_id": "macro_context",
        "requirement_name": "宏观背景与公司传导",
        "keywords": ("macro", "宏观", "transmission", "传导"),
        "required_evidence": ["macro variable", "industry-to-company transmission evidence"],
        "priority": "P1",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "international_macro",
        "requirement_name": "国际宏观与外部变量",
        "keywords": ("international", "overseas", "export", "国际", "海外", "出口"),
        "required_evidence": ["international demand or constraint variable", "company exposure bridge"],
        "priority": "P2",
        "blocks_llm_depth": False,
    },
    {
        "requirement_id": "fx",
        "requirement_name": "汇率暴露",
        "keywords": ("fx", "foreign exchange", "currency", "汇率", "外汇"),
        "required_evidence": ["currency exposure", "revenue/cost currency mix"],
        "priority": "P2",
        "blocks_llm_depth": False,
    },
    {
        "requirement_id": "commodity",
        "requirement_name": "商品价格与成本传导",
        "keywords": ("commodity", "raw material", "price", "商品", "原材料", "成本"),
        "required_evidence": ["input cost series", "gross margin bridge"],
        "priority": "P1",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "policy",
        "requirement_name": "政策变量与公司层面证据",
        "keywords": ("policy", "regulation", "政策", "监管"),
        "required_evidence": ["policy scope", "company order/delivery/collection bridge"],
        "priority": "P1",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "industry_cycle",
        "requirement_name": "行业周期位置",
        "keywords": ("industry cycle", "cycle", "行业周期", "景气", "周期"),
        "required_evidence": ["industry cycle indicator", "company revenue/margin bridge"],
        "priority": "P1",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "industry_consensus",
        "requirement_name": "行业共识",
        "keywords": ("consensus", "source_bucket", "共识", "一致"),
        "required_evidence": ["independent source bucket count", "consensus assessment"],
        "priority": "P2",
        "blocks_llm_depth": False,
    },
    {
        "requirement_id": "divergent_views",
        "requirement_name": "分歧观点",
        "keywords": ("divergence", "divergent", "分歧"),
        "required_evidence": ["divergent source summary", "reason for divergence"],
        "priority": "P2",
        "blocks_llm_depth": False,
    },
    {
        "requirement_id": "opposing_views",
        "requirement_name": "相反观点",
        "keywords": ("opposing", "contradiction", "反证", "相反", "矛盾"),
        "required_evidence": ["opposing view evidence", "contradiction trigger"],
        "priority": "P1",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "competitor_peer_benchmark",
        "requirement_name": "同业/竞品对比",
        "keywords": ("peer", "competitor", "benchmark", "同业", "竞品", "可比"),
        "required_evidence": ["peer set", "comparable metric table"],
        "priority": "P1",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "upstream_downstream_prices",
        "requirement_name": "上下游价格与订单传导",
        "keywords": ("upstream", "downstream", "price", "customer", "supplier", "上下游", "客户", "供应商"),
        "required_evidence": ["upstream/downstream price signal", "company order or margin bridge"],
        "priority": "P1",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "company_business_structure",
        "requirement_name": "公司业务结构",
        "keywords": ("business composition", "business structure", "segment", "业务构成", "业务结构", "分部"),
        "required_evidence": ["business segment summary", "revenue mix summary"],
        "priority": "P0",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "business_competitiveness",
        "requirement_name": "业务竞争力",
        "keywords": ("competitiveness", "competitive", "竞争力", "壁垒", "客户定点"),
        "required_evidence": ["customer/program/product evidence", "margin or retention evidence"],
        "priority": "P0",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "market_share",
        "requirement_name": "市场份额",
        "keywords": ("market share", "share", "份额", "市占率"),
        "required_evidence": ["market size", "company share estimate", "peer denominator"],
        "priority": "P1",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "project_progress",
        "requirement_name": "项目进度",
        "keywords": ("project progress", "program", "delivery", "项目进度", "项目", "交付"),
        "required_evidence": ["project/program milestone", "delivery evidence"],
        "priority": "P0",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "capex_mapping",
        "requirement_name": "capex 与项目/收入映射",
        "keywords": ("capex", "capital expenditure", "收入转化", "资本开支"),
        "required_evidence": ["capex item", "project milestone", "revenue conversion bridge"],
        "priority": "P0",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "r_and_d_conversion",
        "requirement_name": "R&D 投入与产品/收入转化",
        "keywords": ("r&d", "research development", "研发", "产品转化", "技术"),
        "required_evidence": ["R&D program", "product/customer/revenue conversion evidence"],
        "priority": "P0",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "financial_statement_quality",
        "requirement_name": "财务报表质量",
        "keywords": ("financial quality", "financial statement", "profit", "margin", "ROE", "ROIC", "财务质量", "利润", "利润率", "资本效率"),
        "required_evidence": ["profitability trend", "cash conversion", "capital efficiency evidence"],
        "priority": "P0",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "cashflow_receivable_inventory_linkage",
        "requirement_name": "现金流/应收/存货联动",
        "keywords": ("cashflow", "cash conversion", "receivable", "inventory", "collection", "现金流", "应收", "存货", "回款"),
        "required_evidence": ["operating cashflow", "receivable trend", "inventory or working-capital trend"],
        "priority": "P0",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "debt_financing_structure",
        "requirement_name": "负债与融资结构",
        "keywords": ("debt", "financing", "contract liabilities", "dividend", "payout", "负债", "融资", "合同负债", "分红"),
        "required_evidence": ["debt structure", "financing maturity", "payout sustainability evidence"],
        "priority": "P1",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "disclosure_consistency",
        "requirement_name": "披露一致性",
        "keywords": ("disclosure consistency", "consistency", "披露一致", "口径一致"),
        "required_evidence": ["disclosure statement", "financial cross-check"],
        "priority": "P0",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "prior_promise_vs_current_delivery",
        "requirement_name": "前期承诺与当前交付",
        "keywords": ("promise", "delivery", "承诺", "兑现", "交付"),
        "required_evidence": ["prior statement", "current delivery or revenue evidence"],
        "priority": "P1",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "governance_risk",
        "requirement_name": "治理风险",
        "keywords": ("governance", "治理"),
        "required_evidence": ["governance issue summary", "related risk evidence"],
        "priority": "P2",
        "blocks_llm_depth": False,
    },
    {
        "requirement_id": "regulatory_violation_risk",
        "requirement_name": "监管/违规风险",
        "keywords": ("regulatory", "violation", "监管", "违规"),
        "required_evidence": ["regulatory event", "violation status"],
        "priority": "P1",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "black_swan_risk",
        "requirement_name": "黑天鹅风险",
        "keywords": ("black swan", "tail risk", "黑天鹅", "极端风险"),
        "required_evidence": ["tail-risk scenario", "exposure boundary"],
        "priority": "P2",
        "blocks_llm_depth": False,
    },
    {
        "requirement_id": "manual_research_notes",
        "requirement_name": "人工研究笔记/待核事项",
        "keywords": ("manual_review", "manual", "review", "人工", "跟踪计划", "核验"),
        "required_evidence": ["manual review item", "checked field and evidence trigger"],
        "priority": "P0",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "ir_questions",
        "requirement_name": "IR 问题",
        "keywords": ("ir", "investor relations", "IR", "董秘", "调研问题"),
        "required_evidence": ["IR question candidate", "required answer type"],
        "priority": "P1",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "frontstage_chart_ready_sections",
        "requirement_name": "前台图表就绪研究段落",
        "keywords": ("chart", "quality_score", "tracking_plan", "六维评分", "图表", "评分"),
        "required_evidence": ["structured chart-ready summary", "data quality boundary"],
        "priority": "P2",
        "blocks_llm_depth": False,
    },
    {
        "requirement_id": "html_report_mapping",
        "requirement_name": "HTML/report section mapping summary",
        "keywords": ("frontstage", "report section", "html_report_mapping", "报告映射", "section"),
        "required_evidence": ["structured section mapping summary", "frontstage summary boundary"],
        "priority": "future",
        "blocks_llm_depth": False,
    },
    {
        "requirement_id": "authoritative_data_crosscheck",
        "requirement_name": "权威数据源与公司披露交叉核对",
        "keywords": ("authoritative", "official", "crosscheck", "权威", "公司披露", "交叉核对"),
        "required_evidence": ["authoritative data source field", "company disclosure field", "field-by-field comparison boundary"],
        "next_data_task": "补充权威数据源与公司披露字段对照。",
        "priority": "P0",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "news_and_special_events",
        "requirement_name": "新闻/特殊事件结构化输入",
        "keywords": ("news", "special event", "event", "新闻", "特殊事件", "突发"),
        "required_evidence": ["structured event summary", "event-to-company impact boundary", "evidence timestamp"],
        "next_data_task": "补充新闻/特殊事件结构化输入。",
        "priority": "P1",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "source_tier_classification",
        "requirement_name": "source tier 分类与可见性",
        "keywords": ("source_tier", "source hierarchy", "source_bucket", "source tier", "来源层级", "source_name"),
        "required_evidence": ["source tier classification", "source bucket count", "model-visible source summary"],
        "next_data_task": "补充 source tier、source bucket 与 LLM 可见性分类。",
        "priority": "P0",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "rd_staff_and_project_mapping",
        "requirement_name": "研发人员/研发项目/产品客户收入映射",
        "keywords": ("R&D staff", "研发人员", "研发项目", "rd_staff", "研发人数"),
        "required_evidence": ["R&D staff structure", "R&D project list", "product/customer/revenue conversion mapping"],
        "next_data_task": "补充研发人员、研发项目与产品/客户/收入转化映射。",
        "priority": "P0",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "revenue_driver_decomposition",
        "requirement_name": "收入增长驱动拆解",
        "keywords": ("revenue driver", "revenue decomposition", "收入增长驱动", "销量", "价格", "并表", "口径变化"),
        "required_evidence": ["volume driver", "price driver", "consolidation scope change", "cycle/policy/accounting boundary"],
        "next_data_task": "补充收入增长驱动拆解：销量、价格、并表、周期、政策、口径变化。",
        "priority": "P0",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "cost_driver_decomposition",
        "requirement_name": "成本变化驱动拆解",
        "keywords": ("cost driver", "cost decomposition", "成本变化", "原材料", "规模效应", "产品结构"),
        "required_evidence": ["raw material cost bridge", "scale-effect evidence", "product-mix and accounting-boundary evidence"],
        "next_data_task": "补充成本变化拆解：原材料、规模效应、产品结构、质量牺牲、会计口径。",
        "priority": "P0",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "balance_sheet_reclassification",
        "requirement_name": "资产负债表重分类与异常科目迁移",
        "keywords": ("balance sheet reclassification", "reclassification", "异常科目", "科目迁移", "重分类"),
        "required_evidence": ["balance-sheet account movement", "reclassification explanation", "abnormal-account migration check"],
        "next_data_task": "补充资产负债表分类变化和异常科目迁移。",
        "priority": "P1",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "financing_cashflow_dependency",
        "requirement_name": "融资现金流依赖与债务结构",
        "keywords": ("financing cashflow", "short debt", "long debt", "convertible bond", "融资现金流", "短债", "长债", "可转债", "利率"),
        "required_evidence": ["financing cashflow trend", "short/long debt structure", "interest-rate and bond structure"],
        "next_data_task": "补充融资现金流、短债长债、利率、发债、可转债结构。",
        "priority": "P1",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "selective_disclosure_risk",
        "requirement_name": "选择性披露风险",
        "keywords": ("selective disclosure", "selective_disclosure", "选择性披露", "披露风险"),
        "required_evidence": ["selective disclosure trigger", "missing counter-evidence", "disclosure consistency rule"],
        "next_data_task": "补充选择性披露风险识别规则。",
        "priority": "P1",
        "blocks_llm_depth": True,
    },
    {
        "requirement_id": "conclusion_first_frontstage",
        "requirement_name": "结论前置展示映射",
        "keywords": ("core_conclusion", "core_conflict", "conclusion first", "结论前置", "核心结论", "核心矛盾"),
        "required_evidence": ["core conclusion summary", "core conflict summary", "frontstage display ordering"],
        "next_data_task": "补充结论前置展示映射。",
        "priority": "P1",
        "blocks_llm_depth": False,
    },
    {
        "requirement_id": "visualization_plan",
        "requirement_name": "图表化展示所需字段",
        "keywords": ("visualization", "chart_ready", "table_ready", "quality_score", "图表化", "图表", "六维评分"),
        "required_evidence": ["chart-ready section list", "table-ready field list", "missing visualization input list"],
        "next_data_task": "补充图表化展示所需字段。",
        "priority": "P2",
        "blocks_llm_depth": False,
    },
)


def _strategy_specific_requirements(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    strategy_text = _searchable_text(
        [source.get("strategy_type"), source.get("sub_type")]
    ).casefold()
    if "stable_growth" not in strategy_text:
        return []
    return [
        {
            "requirement_id": "stable_cash_conversion",
            "requirement_name": "stable growth: cash conversion",
            "keywords": ("cash conversion", "cashflow", "现金转化", "现金流"),
            "required_evidence": ["cash conversion trend", "profit-to-cash bridge"],
            "priority": "P0",
            "blocks_llm_depth": True,
        },
        {
            "requirement_id": "stable_receivables_collection_quality",
            "requirement_name": "stable growth: receivables / collection quality",
            "keywords": ("receivables", "collection", "应收", "回款"),
            "required_evidence": ["receivables trend", "collection quality evidence"],
            "priority": "P0",
            "blocks_llm_depth": True,
        },
        {
            "requirement_id": "stable_repeat_order_customer_retention",
            "requirement_name": "stable growth: repeat order / customer retention",
            "keywords": ("repeat order", "retention", "customer retention", "复购", "客户留存"),
            "required_evidence": ["repeat order evidence", "customer retention evidence"],
            "priority": "P1",
            "blocks_llm_depth": True,
        },
        {
            "requirement_id": "stable_roe_roic_evidence_sufficiency",
            "requirement_name": "stable growth: ROE/ROIC evidence sufficiency",
            "keywords": ("ROE", "ROIC", "capital efficiency", "资本效率"),
            "required_evidence": ["ROE trend", "ROIC or invested-capital evidence"],
            "priority": "P1",
            "blocks_llm_depth": True,
        },
        {
            "requirement_id": "stable_capex_discipline",
            "requirement_name": "stable growth: capex discipline",
            "keywords": ("capex discipline", "capex", "capital expenditure", "资本开支纪律"),
            "required_evidence": ["capex plan", "cash return and project-progress bridge"],
            "priority": "P1",
            "blocks_llm_depth": True,
        },
        {
            "requirement_id": "stable_dividend_payout_sustainability",
            "requirement_name": "stable growth: dividend / payout sustainability",
            "keywords": ("dividend", "payout", "分红", "派息"),
            "required_evidence": ["dividend history", "cash coverage and debt boundary"],
            "priority": "P1",
            "blocks_llm_depth": True,
        },
    ]


_COLLISION_BLUEPRINTS = (
    {
        "category": "company_claim_vs_financial_data",
        "layer": "company",
        "keywords": ("company claim", "business claim", "披露", "说法", "业务说法"),
        "question": "Which company claims need to be checked against financial-statement evidence before forming a conclusion?",
        "why_it_matters": "It prevents company narratives from becoming unsupported fundamental conclusions.",
        "required_evidence": ["company claim", "financial statement check", "matching period"],
        "not_assessable_reason": "No matched company-claim and financial-statement evidence was supplied.",
    },
    {
        "category": "revenue_growth_vs_cashflow",
        "layer": "financial",
        "keywords": ("revenue", "cashflow", "cash conversion", "收入", "现金流", "现金转化"),
        "question": "Does revenue growth convert into operating cashflow and collection quality?",
        "why_it_matters": "Revenue without cash conversion can overstate operating quality.",
        "required_evidence": ["revenue trend", "operating cashflow trend", "collection evidence"],
        "not_assessable_reason": "Revenue and cashflow bridge evidence was not supplied together.",
    },
    {
        "category": "profit_growth_vs_operating_cashflow",
        "layer": "financial",
        "keywords": ("profit", "operating cashflow", "利润", "经营现金流"),
        "question": "Does profit growth match operating cashflow rather than only accounting profit?",
        "why_it_matters": "Profit-cash mismatch changes the quality boundary of the analysis.",
        "required_evidence": ["profit trend", "operating cashflow", "working-capital bridge"],
        "not_assessable_reason": "Profit and operating-cashflow bridge evidence was not supplied together.",
    },
    {
        "category": "revenue_growth_vs_receivable_inventory",
        "layer": "financial",
        "keywords": ("receivable", "inventory", "收入", "应收", "存货"),
        "question": "Is revenue growth supported without excessive receivable or inventory pressure?",
        "why_it_matters": "Working-capital pressure can cap confidence in growth quality.",
        "required_evidence": ["revenue trend", "receivable trend", "inventory trend"],
        "not_assessable_reason": "Receivable or inventory linkage evidence was not supplied.",
    },
    {
        "category": "capex_vs_project_revenue_conversion",
        "layer": "company",
        "keywords": ("capex", "capital expenditure", "project", "项目", "资本开支", "收入转化"),
        "question": "Which project milestones and revenue-conversion evidence connect capex to company results?",
        "why_it_matters": "Capex alone is only an input and cannot support output-side conclusions.",
        "required_evidence": ["capex item", "project progress", "delivery/revenue conversion evidence"],
        "not_assessable_reason": "Capex-to-project-to-revenue bridge evidence was not supplied.",
    },
    {
        "category": "r_and_d_input_vs_product_conversion",
        "layer": "company",
        "keywords": ("r&d", "研发", "research", "development", "产品转化", "技术"),
        "question": "Which product, customer, and revenue evidence converts R&D input into business results?",
        "why_it_matters": "R&D input needs conversion evidence before it can support business competitiveness.",
        "required_evidence": ["R&D program", "product milestone", "customer/revenue conversion evidence"],
        "not_assessable_reason": "R&D conversion evidence was not supplied.",
    },
    {
        "category": "contract_liabilities_vs_backlog",
        "layer": "financial",
        "keywords": ("contract liabilities", "合同负债", "backlog", "order", "订单"),
        "question": "Do contract liabilities have independent order, fulfillment, collection, and backlog evidence?",
        "why_it_matters": "Contract-liability proxies need independent checks before order visibility can be assessed.",
        "required_evidence": ["contract liabilities", "order detail", "fulfillment and collection evidence"],
        "not_assessable_reason": "Independent order or fulfillment evidence was not supplied.",
    },
    {
        "category": "industry_policy_theme_vs_company_orders_delivery_collection_revenue",
        "layer": "industry",
        "keywords": ("industry", "policy", "theme", "order", "delivery", "collection", "revenue", "行业", "政策", "主题", "订单", "交付", "回款"),
        "question": "Has the industry/policy/theme driver reached company orders, delivery, collection, revenue, or margins?",
        "why_it_matters": "External drivers only matter after a company-level transmission bridge is visible.",
        "required_evidence": ["external driver", "company order/delivery/collection/revenue bridge"],
        "not_assessable_reason": "Company-level transmission evidence was not supplied.",
    },
    {
        "category": "new_business_narrative_vs_segment_revenue_orders_customers",
        "layer": "company",
        "keywords": ("new business", "robotics", "机器人", "新业务", "分部收入", "客户", "量产"),
        "question": "Which segment revenue, order, customer, and mass-production evidence supports the new-business narrative?",
        "why_it_matters": "New-business narratives must remain bounded until operating evidence is supplied.",
        "required_evidence": ["segment revenue", "orders", "customers", "mass-production evidence"],
        "not_assessable_reason": "New-business operating evidence was not supplied.",
    },
    {
        "category": "valuation_context_vs_profit_cashflow_evidence_sufficiency",
        "layer": "valuation",
        "keywords": ("valuation", "evidence sufficiency", "估值", "证据充分性", "盈利", "现金流"),
        "question": "Is the valuation background explainable by profit, cashflow, and evidence sufficiency boundaries?",
        "why_it_matters": "Valuation context is shallow without profit, cashflow, and evidence-boundary checks.",
        "required_evidence": ["profit evidence", "cashflow evidence", "valuation explanation boundary"],
        "not_assessable_reason": "Valuation evidence sufficiency was not supplied.",
    },
    {
        "category": "competitor_peer_gap",
        "layer": "industry",
        "keywords": ("peer", "competitor", "market share", "同业", "竞品", "市场份额", "市占率"),
        "question": "Which peer, competitor, and market-share data are missing before relative competitiveness can be assessed?",
        "why_it_matters": "Competitiveness cannot be ranked without a peer denominator or comparable evidence.",
        "required_evidence": ["peer set", "market-share denominator", "comparable operating metrics"],
        "not_assessable_reason": "Peer or market-share data was not supplied.",
    },
    {
        "category": "multi_source_consensus_divergence_opposing_view_gap",
        "layer": "source",
        "keywords": ("source_bucket", "consensus", "divergence", "opposing", "source", "多源", "分歧", "相反", "共识"),
        "question": "Which multi-source consensus, divergence, or opposing-view checks are still absent?",
        "why_it_matters": "Single-source framing caps confidence in conclusions and hides contrary evidence.",
        "required_evidence": ["independent source buckets", "consensus/divergence summary", "opposing-view evidence"],
        "not_assessable_reason": "Multi-source independence evidence was not sufficient.",
    },
)


__all__ = [
    "CONFIDENCE_CAPS",
    "COVERAGE_STATUSES",
    "DATA_AVAILABILITY_STATUSES",
    "INVESTMENT_DIRECTOR_COLLISION_QUESTION_SCHEMA_VERSION",
    "INVESTMENT_DIRECTOR_COLLISION_QUESTION_SET_SCHEMA_VERSION",
    "INVESTMENT_DIRECTOR_COVERAGE_ITEM_SCHEMA_VERSION",
    "INVESTMENT_DIRECTOR_LLM_CONTEXT_PROMPT_PAYLOAD_SCHEMA_VERSION",
    "INVESTMENT_DIRECTOR_MISSING_COVERAGE_MAP_SCHEMA_VERSION",
    "INVESTMENT_DIRECTOR_RESEARCH_CONTEXT_PACK_REQUEST_SCHEMA_VERSION",
    "INVESTMENT_DIRECTOR_RESEARCH_CONTEXT_PACK_SCHEMA_VERSION",
    "INVESTMENT_DIRECTOR_SOURCE_ASSET_SUMMARY_SCHEMA_VERSION",
    "InvestmentDirectorResearchContextPackError",
    "assert_no_investment_director_context_forbidden_markers",
    "assert_no_raw_backend_or_secret_leak",
    "build_collision_questions_from_research_intelligence",
    "build_investment_director_missing_coverage_map",
    "build_investment_director_research_context_pack",
    "build_llm_context_prompt_payload_from_investment_director_pack",
    "build_old_report_frontstage_snapshot",
    "normalize_research_question_item",
    "summarize_research_intelligence_asset_presence",
    "validate_investment_director_missing_coverage_map",
    "validate_investment_director_research_context_pack",
]
