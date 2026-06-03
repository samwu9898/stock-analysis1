# -*- coding: utf-8 -*-
"""Ticker-only professional compact brief quality evaluation harness.

The harness exercises the public wrapper ticker-only path with injected fake
Tushare clients, then evaluates only the user-facing professional compact brief.
It does not call live providers, LLM APIs, Report V1 builders, HTML renderers,
or write runtime artifacts.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable, Mapping
from copy import deepcopy
import json
import re
from typing import Any

from .a_share_fundamental_skill_wrapper import (
    A_SHARE_FUNDAMENTAL_SKILL_REQUEST_SCHEMA_VERSION,
    INPUT_MODE_TICKER_ONLY_PROFESSIONAL_BRIEF,
    OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF,
    PROFESSIONAL_BRIEF_SECTION_KEYS,
    SKILL_READINESS_READY,
    TUSHARE_CLIENT_MODE_INJECTED,
    build_a_share_fundamental_skill_response,
)


TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_EVALUATION_REQUEST_SCHEMA_VERSION = (
    "ticker_only_professional_brief_quality_evaluation_request.v1"
)
TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_EVALUATION_RESULT_SCHEMA_VERSION = (
    "ticker_only_professional_brief_quality_evaluation_result.v1"
)
TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_SAMPLE_SCHEMA_VERSION = (
    "ticker_only_professional_brief_quality_sample.v1"
)
TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_RUBRIC_SCHEMA_VERSION = (
    "ticker_only_professional_brief_quality_rubric.v1"
)
TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_SCORECARD_SCHEMA_VERSION = (
    "ticker_only_professional_brief_quality_scorecard.v1"
)
TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_ISSUE_SCHEMA_VERSION = (
    "ticker_only_professional_brief_quality_issue.v1"
)

QUALITY_STATUS_PASS = "pass"
QUALITY_STATUS_WARNING = "warning"
QUALITY_STATUS_FAIL = "fail"
QUALITY_STATUSES = (
    QUALITY_STATUS_PASS,
    QUALITY_STATUS_WARNING,
    QUALITY_STATUS_FAIL,
)

QUALITY_SAMPLE_IDS = (
    "baseline_600406_like",
    "non_600406_sample",
    "cashflow_supports_profit",
    "profit_stronger_than_cashflow",
    "high_receivables_pressure",
    "high_debt_pressure",
    "sparse_or_missing_metrics",
)

RUBRIC_DIMENSION_IDS = (
    "has_overall_fundamental_view",
    "has_business_logic_view",
    "has_financial_interpretation",
    "has_operating_quality_judgment",
    "has_cashflow_profit_match_judgment",
    "has_receivables_or_working_capital_view",
    "has_margin_or_profitability_view",
    "has_balance_sheet_or_debt_view",
    "has_industry_macro_transmission_view",
    "has_core_risk_view",
    "has_conclusion_boundary",
    "has_key_variables",
    "no_engineering_labels",
    "no_backend_trace",
    "no_user_responsibility_shift",
    "no_trading_advice",
    "source_note_is_tushare",
)

_SECTION_VIEW_KEYS = PROFESSIONAL_BRIEF_SECTION_KEYS[:6]
_SOURCE_NOTE = "数据来源：Tushare。"
_DEFAULT_PERIODS = ("20241231", "20251231")

_REQUEST_FIELDS = {
    "schema_version",
    "sample_ids",
    "include_professional_compact_brief_preview",
    "not_for_trading_advice",
}

_RESULT_FIELDS = {
    "schema_version",
    "overall_status",
    "sample_count",
    "pass_count",
    "warning_count",
    "fail_count",
    "sample_results",
    "aggregate_issues",
    "not_for_trading_advice",
}

_SAMPLE_RESULT_FIELDS = {
    "sample_id",
    "stock_code",
    "ts_code",
    "scenario",
    "overall_status",
    "readiness_status",
    "brief_section_keys",
    "source_note",
    "scorecard",
    "issues",
    "professional_compact_brief_preview",
}

_SCORECARD_FIELDS = {
    "schema_version",
    "sample_id",
    "overall_status",
    "dimensions",
    "pass_count",
    "warning_count",
    "fail_count",
    "issue_count",
    "issues",
    "not_for_trading_advice",
}

_DIMENSION_SCORE_FIELDS = {
    "dimension_id",
    "status",
    "severity",
    "message",
    "section_id",
}

_ISSUE_FIELDS = {
    "schema_version",
    "issue_id",
    "severity",
    "message",
    "section_id",
}

_AGGREGATE_ISSUE_FIELDS = {
    *_ISSUE_FIELDS,
    "sample_ids",
    "count",
}

_TABLE_FIELDS = {
    "income": (
        "revenue",
        "n_income_attr_p",
        "total_profit",
        "operate_profit",
        "basic_eps",
    ),
    "balancesheet": (
        "total_assets",
        "total_liab",
        "total_hldr_eqy_exc_min_int",
        "accounts_receiv",
        "inventories",
    ),
    "cashflow": (
        "n_cashflow_act",
        "c_cash_equ_end_period",
        "c_fr_sale_sg",
    ),
    "fina_indicator": (
        "grossprofit_margin",
        "netprofit_margin",
        "roe",
        "debt_to_assets",
        "ar_turn",
        "inv_turn",
    ),
}

_METRIC_TABLE = {
    metric: table_name
    for table_name, metrics in _TABLE_FIELDS.items()
    for metric in metrics
}

_SAMPLE_IDENTITY = {
    "baseline_600406_like": {
        "stock_code": "600406",
        "ts_code": "600406.SH",
        "company_name_hint": "Guodian NARI",
        "scenario": "baseline_600406_like",
    },
    "non_600406_sample": {
        "stock_code": "000001",
        "ts_code": "000001.SZ",
        "company_name_hint": "Ping An Bank",
        "scenario": "non_600406_sample",
    },
    "cashflow_supports_profit": {
        "stock_code": "600406",
        "ts_code": "600406.SH",
        "company_name_hint": "Guodian NARI",
        "scenario": "cashflow_supports_profit",
    },
    "profit_stronger_than_cashflow": {
        "stock_code": "600406",
        "ts_code": "600406.SH",
        "company_name_hint": "Guodian NARI",
        "scenario": "profit_stronger_than_cashflow",
    },
    "high_receivables_pressure": {
        "stock_code": "600406",
        "ts_code": "600406.SH",
        "company_name_hint": "Guodian NARI",
        "scenario": "high_receivables_pressure",
    },
    "high_debt_pressure": {
        "stock_code": "600406",
        "ts_code": "600406.SH",
        "company_name_hint": "Guodian NARI",
        "scenario": "high_debt_pressure",
    },
    "sparse_or_missing_metrics": {
        "stock_code": "600406",
        "ts_code": "600406.SH",
        "company_name_hint": "Guodian NARI",
        "scenario": "sparse_or_missing_metrics",
    },
}

_BASE_PREVIOUS_METRICS = {
    "revenue": 900.0,
    "n_income_attr_p": 95.0,
    "total_profit": 115.0,
    "operate_profit": 108.0,
    "basic_eps": 0.95,
    "total_assets": 2800.0,
    "total_liab": 840.0,
    "total_hldr_eqy_exc_min_int": 1960.0,
    "accounts_receiv": 110.0,
    "inventories": 75.0,
    "n_cashflow_act": 120.0,
    "c_cash_equ_end_period": 460.0,
    "c_fr_sale_sg": 890.0,
    "grossprofit_margin": 31.0,
    "netprofit_margin": 10.6,
    "roe": 14.0,
    "debt_to_assets": 30.0,
    "ar_turn": 4.2,
    "inv_turn": 7.6,
}

_BASE_LATEST_METRICS = {
    "revenue": 1000.0,
    "n_income_attr_p": 120.0,
    "total_profit": 150.0,
    "operate_profit": 140.0,
    "basic_eps": 1.23,
    "total_assets": 3000.0,
    "total_liab": 900.0,
    "total_hldr_eqy_exc_min_int": 2100.0,
    "accounts_receiv": 120.0,
    "inventories": 80.0,
    "n_cashflow_act": 180.0,
    "c_cash_equ_end_period": 500.0,
    "c_fr_sale_sg": 980.0,
    "grossprofit_margin": 32.5,
    "netprofit_margin": 12.0,
    "roe": 16.0,
    "debt_to_assets": 30.0,
    "ar_turn": 4.0,
    "inv_turn": 8.0,
}

_ALLOWED_EXACT_TEXTS = {
    "not_for_trading_advice",
    "no_trading_advice",
    *RUBRIC_DIMENSION_IDS,
    TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_EVALUATION_REQUEST_SCHEMA_VERSION,
    TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_EVALUATION_RESULT_SCHEMA_VERSION,
    TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_SAMPLE_SCHEMA_VERSION,
    TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_RUBRIC_SCHEMA_VERSION,
    TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_SCORECARD_SCHEMA_VERSION,
    TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_ISSUE_SCHEMA_VERSION,
}

_QUALITY_FORBIDDEN_MARKERS = (
    "token",
    ".env",
    "tushare_token",
    "api_key",
    "authorization",
    "backend trace",
    "backend_trace",
    "backend_grounding_summary",
    "raw_provider_bundle",
    "raw provider bundle",
    "raw_provider_rows",
    "raw provider rows",
    "raw rows",
    "raw_provider_queue",
    "raw provider queue",
    "raw_tushare_provider_result",
    "provider_candidate_bundle",
    "provider_candidate",
    "pending verification",
    "pending_official_verification",
    "candidate_items",
    "source_url",
    "page_number",
    "snippet",
    "sha256",
    "cache_path",
    "output/",
    "output\\",
    "output path",
    "fixture path",
    "fixtures/",
    "fixtures\\",
    "accepted manifest",
    "accepted_manifest",
    "official_metric_fact",
    "provider_official_conflict",
    "provider-official reconciliation",
    "provider vs official",
    "reconciliation",
    "Report V1 artifact",
    "report_v1_artifact",
    "HTML artifact",
    "html_artifact",
    "markdown artifact",
    "json runtime artifact",
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

_QUALITY_FORBIDDEN_CJK_MARKERS = (
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

_FRONTSTAGE_ENGINEERING_LABELS = (
    "provider_candidate",
    "provider candidate",
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
)

_RESPONSIBILITY_SHIFT_MARKERS = (
    "user should decide",
    "decide by yourself",
    "track by yourself",
    "用户自行",
    "自行判断",
    "自行跟踪",
    "需要用户",
    "建议用户",
    "请结合",
)

_TRADING_MARKERS = (
    "buy",
    "sell",
    "hold",
    "target price",
    "portfolio",
    "position",
    "technical signal",
    "trading advice",
    "investment advice",
    "买入",
    "卖出",
    "持有",
    "目标价",
    "仓位",
    "组合",
    "技术信号",
    "投资建议",
)

_BACKEND_TRACE_MARKERS = (
    "backend trace",
    "backend_trace",
    "backend_grounding_summary",
    "raw_provider",
    "raw provider",
    "candidate_items",
    "provider_candidate",
    "page_number",
    "snippet",
    "source_url",
    "sha256",
    "cache_path",
)

_SECRET_LIKE_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._-]{8,}\b", re.IGNORECASE),
)

_WORD_MARKERS = {"token", "buy", "sell", "hold", "portfolio", "position"}


class TickerOnlyProfessionalBriefQualityEvaluationError(ValueError):
    """Raised when the quality evaluation harness fails closed."""


TushareClientFactory = Callable[[Mapping[str, Any]], Any]


def build_ticker_only_professional_brief_quality_evaluation(
    request: Mapping[str, Any],
    *,
    tushare_client_factory: TushareClientFactory | None = None,
) -> dict[str, Any]:
    """Build an in-memory quality evaluation for ticker-only professional briefs."""

    validated_request = validate_quality_evaluation_request(request)
    rubric = build_default_quality_rubric()
    samples = build_quality_sample_requests(
        sample_ids=validated_request["sample_ids"],
    )
    sample_results = []
    for sample in samples:
        wrapper_request = deepcopy(sample["wrapper_request"])
        client = (
            tushare_client_factory(sample)
            if tushare_client_factory is not None
            else _ScenarioFakeTushareClient(
                sample_id=sample["sample_id"],
                ts_code=sample["ts_code"],
                periods=sample["periods"],
            )
        )
        wrapper_response = build_a_share_fundamental_skill_response(
            wrapper_request,
            tushare_client=client,
        )
        sample_results.append(
            _build_sample_result(
                sample,
                wrapper_response,
                rubric=rubric,
                include_preview=validated_request[
                    "include_professional_compact_brief_preview"
                ],
            )
        )

    status_counter = Counter(result["overall_status"] for result in sample_results)
    aggregate_issues = _aggregate_issues(sample_results)
    overall_status = _combine_statuses(result["overall_status"] for result in sample_results)
    result = {
        "schema_version": (
            TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_EVALUATION_RESULT_SCHEMA_VERSION
        ),
        "overall_status": overall_status,
        "sample_count": len(sample_results),
        "pass_count": status_counter[QUALITY_STATUS_PASS],
        "warning_count": status_counter[QUALITY_STATUS_WARNING],
        "fail_count": status_counter[QUALITY_STATUS_FAIL],
        "sample_results": sample_results,
        "aggregate_issues": aggregate_issues,
        "not_for_trading_advice": True,
    }
    return validate_quality_evaluation_result(result)


def build_quality_sample_requests(
    *,
    sample_ids: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    """Build deterministic in-memory wrapper requests for quality samples."""

    selected_sample_ids = _normalise_sample_ids(sample_ids)
    samples = []
    for sample_id in selected_sample_ids:
        identity = _SAMPLE_IDENTITY[sample_id]
        wrapper_request = {
            "schema_version": A_SHARE_FUNDAMENTAL_SKILL_REQUEST_SCHEMA_VERSION,
            "stock_code": identity["stock_code"],
            "ts_code": identity["ts_code"],
            "company_name_hint": identity["company_name_hint"],
            "periods": list(_DEFAULT_PERIODS),
            "input_mode": INPUT_MODE_TICKER_ONLY_PROFESSIONAL_BRIEF,
            "output_mode": OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF,
            "tushare_client_mode": TUSHARE_CLIENT_MODE_INJECTED,
            "allow_network": False,
            "allow_file_writes": False,
            "not_for_trading_advice": True,
        }
        samples.append(
            {
                "schema_version": (
                    TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_SAMPLE_SCHEMA_VERSION
                ),
                "sample_id": sample_id,
                "stock_code": identity["stock_code"],
                "ts_code": identity["ts_code"],
                "company_name_hint": identity["company_name_hint"],
                "scenario": identity["scenario"],
                "periods": list(_DEFAULT_PERIODS),
                "wrapper_request": wrapper_request,
                "not_for_trading_advice": True,
            }
        )
    return samples


def evaluate_professional_compact_brief(
    brief: Mapping[str, Any],
    *,
    sample_id: str,
    rubric: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate one user-facing professional compact brief against the rubric."""

    sample_id = _require_sample_id(sample_id)
    checked_brief = _require_mapping(brief, "professional_compact_brief")
    assert_no_quality_evaluation_forbidden_markers(checked_brief)
    assert_no_frontstage_engineering_labels(checked_brief)

    active_rubric = validate_quality_rubric(
        rubric if rubric is not None else build_default_quality_rubric()
    )
    dimension_scores = {}
    issues = []
    for dimension in active_rubric["dimensions"]:
        score = _evaluate_dimension(checked_brief, dimension)
        dimension_scores[score["dimension_id"]] = score
        if score["status"] != QUALITY_STATUS_PASS:
            issues.append(
                _build_issue(
                    issue_id=f"{score['dimension_id']}_{score['status']}",
                    severity=score["severity"],
                    message=score["message"],
                    section_id=score["section_id"],
                )
            )

    issues.extend(_sample_specific_quality_issues(sample_id, checked_brief))
    dimension_counter = Counter(
        score["status"] for score in dimension_scores.values()
    )
    overall_status = _combine_statuses(
        [
            *(score["status"] for score in dimension_scores.values()),
            *(issue["severity"] for issue in issues),
        ]
    )
    scorecard = {
        "schema_version": (
            TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_SCORECARD_SCHEMA_VERSION
        ),
        "sample_id": sample_id,
        "overall_status": overall_status,
        "dimensions": dimension_scores,
        "pass_count": dimension_counter[QUALITY_STATUS_PASS],
        "warning_count": dimension_counter[QUALITY_STATUS_WARNING],
        "fail_count": dimension_counter[QUALITY_STATUS_FAIL],
        "issue_count": len(issues),
        "issues": issues,
        "not_for_trading_advice": True,
    }
    return validate_quality_scorecard(scorecard)


def build_default_quality_rubric() -> dict[str, Any]:
    """Build the default rubric used by the evaluation harness."""

    dimensions = [
        _rubric_dimension(
            "has_overall_fundamental_view",
            "overall_view",
            "Overall fundamental view is present.",
        ),
        _rubric_dimension(
            "has_business_logic_view",
            "business_view",
            "Business logic view is present.",
        ),
        _rubric_dimension(
            "has_financial_interpretation",
            "financial_view",
            "Financial interpretation is present.",
        ),
        _rubric_dimension(
            "has_operating_quality_judgment",
            "operating_quality_view",
            "Operating quality judgment is present.",
        ),
        _rubric_dimension(
            "has_cashflow_profit_match_judgment",
            "operating_quality_view",
            "Cashflow and profit match judgment is present.",
        ),
        _rubric_dimension(
            "has_receivables_or_working_capital_view",
            "operating_quality_view",
            "Receivables or working-capital view is present.",
        ),
        _rubric_dimension(
            "has_margin_or_profitability_view",
            "financial_view",
            "Margin or profitability view is present.",
        ),
        _rubric_dimension(
            "has_balance_sheet_or_debt_view",
            "financial_view",
            "Balance sheet or debt view is present.",
        ),
        _rubric_dimension(
            "has_industry_macro_transmission_view",
            "industry_macro_view",
            "Industry and macro transmission view is present.",
        ),
        _rubric_dimension(
            "has_core_risk_view",
            "risk_view",
            "Core risk view is present.",
        ),
        _rubric_dimension(
            "has_conclusion_boundary",
            "conclusion_boundary",
            "Conclusion boundary is present.",
        ),
        _rubric_dimension(
            "has_key_variables",
            "key_variables",
            "Key variables are present.",
        ),
        _rubric_dimension(
            "no_engineering_labels",
            None,
            "No frontstage engineering labels are present.",
        ),
        _rubric_dimension(
            "no_backend_trace",
            None,
            "No hidden execution markers are present.",
        ),
        _rubric_dimension(
            "no_user_responsibility_shift",
            None,
            "No responsibility-shifting wording is present.",
        ),
        _rubric_dimension(
            "no_trading_advice",
            None,
            "No prohibited market-action wording is present.",
        ),
        _rubric_dimension(
            "source_note_is_tushare",
            "source_note",
            "Source note is Tushare.",
        ),
    ]
    rubric = {
        "schema_version": (
            TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_RUBRIC_SCHEMA_VERSION
        ),
        "dimension_ids": list(RUBRIC_DIMENSION_IDS),
        "dimensions": dimensions,
        "not_for_trading_advice": True,
    }
    return validate_quality_rubric(rubric)


def validate_quality_evaluation_request(
    request: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate an evaluation request and return a defensive copy."""

    source = _require_mapping(request, "request")
    _reject_bytes(source, "request")
    unsupported = sorted(set(source) - _REQUEST_FIELDS)
    if unsupported:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"request contains unsupported keys: {unsupported}"
        )
    if source.get("schema_version") != (
        TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_EVALUATION_REQUEST_SCHEMA_VERSION
    ):
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            "invalid quality evaluation request schema_version"
        )
    not_for_trading_advice = source.get("not_for_trading_advice", True)
    if not_for_trading_advice is not True:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            "request.not_for_trading_advice must be true"
        )
    include_preview = source.get("include_professional_compact_brief_preview", True)
    if not isinstance(include_preview, bool):
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            "include_professional_compact_brief_preview must be bool"
        )
    result = {
        "schema_version": source["schema_version"],
        "sample_ids": _normalise_sample_ids(source.get("sample_ids")),
        "include_professional_compact_brief_preview": include_preview,
        "not_for_trading_advice": True,
    }
    assert_no_quality_evaluation_forbidden_markers(result)
    return result


def validate_quality_evaluation_result(
    result: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate a quality evaluation result and return a defensive copy."""

    source = _require_mapping(result, "result")
    _reject_bytes(source, "result")
    unsupported = sorted(set(source) - _RESULT_FIELDS)
    if unsupported:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"result contains unsupported keys: {unsupported}"
        )
    _require_fields(source, _RESULT_FIELDS, "result")
    copied = deepcopy(dict(source))
    if copied["schema_version"] != (
        TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_EVALUATION_RESULT_SCHEMA_VERSION
    ):
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            "invalid quality evaluation result schema_version"
        )
    if copied["overall_status"] not in QUALITY_STATUSES:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            "result.overall_status invalid"
        )
    _require_true(copied["not_for_trading_advice"], "result.not_for_trading_advice")
    sample_results = _require_list(copied["sample_results"], "result.sample_results")
    copied["sample_results"] = [
        _validate_sample_result(item, f"result.sample_results[{index}]")
        for index, item in enumerate(sample_results)
    ]
    copied["aggregate_issues"] = [
        _validate_aggregate_issue(item, f"result.aggregate_issues[{index}]")
        for index, item in enumerate(
            _require_list(copied["aggregate_issues"], "result.aggregate_issues")
        )
    ]
    sample_count = _require_non_negative_int(
        copied["sample_count"],
        "result.sample_count",
    )
    if sample_count != len(copied["sample_results"]):
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            "result.sample_count mismatch"
        )
    status_counter = Counter(item["overall_status"] for item in copied["sample_results"])
    for key, status in (
        ("pass_count", QUALITY_STATUS_PASS),
        ("warning_count", QUALITY_STATUS_WARNING),
        ("fail_count", QUALITY_STATUS_FAIL),
    ):
        if _require_non_negative_int(copied[key], f"result.{key}") != status_counter[status]:
            raise TickerOnlyProfessionalBriefQualityEvaluationError(
                f"result.{key} mismatch"
            )
    expected_status = _combine_statuses(
        item["overall_status"] for item in copied["sample_results"]
    )
    if copied["overall_status"] != expected_status:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            "result.overall_status mismatch"
        )
    assert_no_quality_evaluation_forbidden_markers(copied)
    return copied


def validate_quality_scorecard(scorecard: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a sample scorecard and return a defensive copy."""

    source = _require_mapping(scorecard, "scorecard")
    unsupported = sorted(set(source) - _SCORECARD_FIELDS)
    if unsupported:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"scorecard contains unsupported keys: {unsupported}"
        )
    _require_fields(source, _SCORECARD_FIELDS, "scorecard")
    copied = deepcopy(dict(source))
    if copied["schema_version"] != (
        TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_SCORECARD_SCHEMA_VERSION
    ):
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            "invalid scorecard schema_version"
        )
    _require_sample_id(copied["sample_id"])
    if copied["overall_status"] not in QUALITY_STATUSES:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            "scorecard.overall_status invalid"
        )
    dimensions = _require_mapping(copied["dimensions"], "scorecard.dimensions")
    copied["dimensions"] = {
        dimension_id: _validate_dimension_score(
            score,
            f"scorecard.dimensions.{dimension_id}",
        )
        for dimension_id, score in dimensions.items()
    }
    if tuple(copied["dimensions"]) != RUBRIC_DIMENSION_IDS:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            "scorecard dimensions do not match rubric"
        )
    copied["issues"] = [
        _validate_issue(issue, f"scorecard.issues[{index}]")
        for index, issue in enumerate(_require_list(copied["issues"], "scorecard.issues"))
    ]
    dimension_counter = Counter(
        score["status"] for score in copied["dimensions"].values()
    )
    for key, status in (
        ("pass_count", QUALITY_STATUS_PASS),
        ("warning_count", QUALITY_STATUS_WARNING),
        ("fail_count", QUALITY_STATUS_FAIL),
    ):
        if _require_non_negative_int(copied[key], f"scorecard.{key}") != dimension_counter[status]:
            raise TickerOnlyProfessionalBriefQualityEvaluationError(
                f"scorecard.{key} mismatch"
            )
    if _require_non_negative_int(copied["issue_count"], "scorecard.issue_count") != len(
        copied["issues"]
    ):
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            "scorecard.issue_count mismatch"
        )
    expected_status = _combine_statuses(
        [
            *(score["status"] for score in copied["dimensions"].values()),
            *(issue["severity"] for issue in copied["issues"]),
        ]
    )
    if copied["overall_status"] != expected_status:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            "scorecard.overall_status mismatch"
        )
    _require_true(copied["not_for_trading_advice"], "scorecard.not_for_trading_advice")
    assert_no_quality_evaluation_forbidden_markers(copied)
    return copied


def assert_no_quality_evaluation_forbidden_markers(value: Any) -> None:
    """Reject secrets, raw backend traces, artifacts, and market-action language."""

    _reject_bytes(value, "value")
    finding = _find_forbidden_marker(value)
    if finding:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"quality evaluation safety violation: {finding}"
        )


def assert_no_frontstage_engineering_labels(value: Any) -> None:
    """Reject engineering labels in user-facing professional brief content."""

    _reject_bytes(value, "frontstage_value")
    serialized = json.dumps(value, ensure_ascii=False)
    lowered = serialized.casefold()
    separator = _normalize_separator_text(serialized)
    normalized = _normalise_marker(serialized)
    for marker in _FRONTSTAGE_ENGINEERING_LABELS:
        marker_lower = marker.casefold()
        marker_normalized = _normalise_marker(marker)
        if (
            marker_lower in lowered
            or _normalize_separator_text(marker) in separator
            or (marker_normalized and marker_normalized in normalized)
            or marker in serialized
        ):
            raise TickerOnlyProfessionalBriefQualityEvaluationError(
                "frontstage value contains engineering label"
            )


def validate_quality_rubric(rubric: Mapping[str, Any]) -> dict[str, Any]:
    source = _require_mapping(rubric, "rubric")
    expected_fields = {
        "schema_version",
        "dimension_ids",
        "dimensions",
        "not_for_trading_advice",
    }
    unsupported = sorted(set(source) - expected_fields)
    if unsupported:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"rubric contains unsupported keys: {unsupported}"
        )
    _require_fields(source, expected_fields, "rubric")
    copied = deepcopy(dict(source))
    if copied["schema_version"] != (
        TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_RUBRIC_SCHEMA_VERSION
    ):
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            "invalid rubric schema_version"
        )
    if tuple(_require_string_list(copied["dimension_ids"], "rubric.dimension_ids")) != (
        RUBRIC_DIMENSION_IDS
    ):
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            "rubric.dimension_ids invalid"
        )
    dimensions = _require_list(copied["dimensions"], "rubric.dimensions")
    copied["dimensions"] = [
        _validate_rubric_dimension(dimension, f"rubric.dimensions[{index}]")
        for index, dimension in enumerate(dimensions)
    ]
    if tuple(dimension["dimension_id"] for dimension in copied["dimensions"]) != (
        RUBRIC_DIMENSION_IDS
    ):
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            "rubric dimension order invalid"
        )
    _require_true(copied["not_for_trading_advice"], "rubric.not_for_trading_advice")
    return copied


def _build_sample_result(
    sample: Mapping[str, Any],
    wrapper_response: Mapping[str, Any],
    *,
    rubric: Mapping[str, Any],
    include_preview: bool,
) -> dict[str, Any]:
    readiness = _require_mapping(wrapper_response.get("readiness"), "wrapper.readiness")
    readiness_status = readiness.get("status")
    brief = wrapper_response.get("professional_compact_brief")
    if readiness_status != SKILL_READINESS_READY or brief is None:
        issue = _build_issue(
            issue_id="wrapper_not_ready",
            severity=QUALITY_STATUS_FAIL,
            message="Wrapper did not return a ready professional brief.",
            section_id=None,
        )
        scorecard = _blocked_scorecard(sample["sample_id"], issue)
        sample_result = {
            "sample_id": sample["sample_id"],
            "stock_code": sample["stock_code"],
            "ts_code": sample["ts_code"],
            "scenario": sample["scenario"],
            "overall_status": QUALITY_STATUS_FAIL,
            "readiness_status": str(readiness_status),
            "brief_section_keys": [],
            "source_note": None,
            "scorecard": scorecard,
            "issues": [issue],
            "professional_compact_brief_preview": None,
        }
        return _validate_sample_result(sample_result, "sample_result")

    scorecard = evaluate_professional_compact_brief(
        brief,
        sample_id=sample["sample_id"],
        rubric=rubric,
    )
    issues = deepcopy(scorecard["issues"])
    preview = (
        _professional_compact_brief_preview(brief)
        if include_preview
        else None
    )
    sample_result = {
        "sample_id": sample["sample_id"],
        "stock_code": sample["stock_code"],
        "ts_code": sample["ts_code"],
        "scenario": sample["scenario"],
        "overall_status": scorecard["overall_status"],
        "readiness_status": str(readiness_status),
        "brief_section_keys": _brief_section_keys(brief),
        "source_note": brief.get("source_note"),
        "scorecard": scorecard,
        "issues": issues,
        "professional_compact_brief_preview": preview,
    }
    return _validate_sample_result(sample_result, "sample_result")


def _blocked_scorecard(sample_id: str, issue: Mapping[str, Any]) -> dict[str, Any]:
    dimensions = {
        dimension_id: {
            "dimension_id": dimension_id,
            "status": QUALITY_STATUS_FAIL,
            "severity": QUALITY_STATUS_FAIL,
            "message": "Wrapper readiness prevented evaluation.",
            "section_id": None,
        }
        for dimension_id in RUBRIC_DIMENSION_IDS
    }
    scorecard = {
        "schema_version": (
            TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_SCORECARD_SCHEMA_VERSION
        ),
        "sample_id": sample_id,
        "overall_status": QUALITY_STATUS_FAIL,
        "dimensions": dimensions,
        "pass_count": 0,
        "warning_count": 0,
        "fail_count": len(dimensions),
        "issue_count": 1,
        "issues": [deepcopy(dict(issue))],
        "not_for_trading_advice": True,
    }
    return validate_quality_scorecard(scorecard)


def _evaluate_dimension(
    brief: Mapping[str, Any],
    dimension: Mapping[str, Any],
) -> dict[str, Any]:
    dimension_id = str(dimension["dimension_id"])
    section_id = dimension.get("section_id")
    passed = _dimension_passed(brief, dimension_id)
    status = QUALITY_STATUS_PASS if passed else _failed_dimension_status(brief)
    if status == QUALITY_STATUS_PASS:
        message = str(dimension["pass_message"])
    elif status == QUALITY_STATUS_WARNING:
        message = "Rubric dimension is thin under sparse metrics."
    else:
        message = "Rubric dimension did not meet the rubric."
    score = {
        "dimension_id": dimension_id,
        "status": status,
        "severity": status,
        "message": message,
        "section_id": section_id,
    }
    return _validate_dimension_score(score, f"dimension.{dimension_id}")


def _dimension_passed(brief: Mapping[str, Any], dimension_id: str) -> bool:
    full_text = _serialized_text(brief)
    if dimension_id == "has_overall_fundamental_view":
        return _has_text(_section_text(brief, "overall_view"), ("基本面", "收入", "利润", "现金流"))
    if dimension_id == "has_business_logic_view":
        return _has_text(_section_text(brief, "business_view"), ("主营", "订单", "交付", "回款", "业务"))
    if dimension_id == "has_financial_interpretation":
        return _has_text(_section_text(brief, "financial_view"), ("收入", "利润", "盈利", "资产负债"))
    if dimension_id == "has_operating_quality_judgment":
        return _has_text(_section_text(brief, "operating_quality_view"), ("经营质量", "现金流", "回款", "应收"))
    if dimension_id == "has_cashflow_profit_match_judgment":
        return _has_text(full_text, ("现金流",)) and _has_text(full_text, ("利润",))
    if dimension_id == "has_receivables_or_working_capital_view":
        return _has_text(full_text, ("应收", "存货", "周转", "营运资本"))
    if dimension_id == "has_margin_or_profitability_view":
        return _has_text(full_text, ("毛利率", "利润率", "盈利", "净利率"))
    if dimension_id == "has_balance_sheet_or_debt_view":
        return _has_text(full_text, ("资产负债", "负债", "资产结构"))
    if dimension_id == "has_industry_macro_transmission_view":
        return _has_text(
            _section_text(brief, "industry_macro_view"),
            ("行业", "宏观", "订单", "交付", "回款", "传导"),
        )
    if dimension_id == "has_core_risk_view":
        return _has_text(_section_text(brief, "risk_view"), ("风险", "压力", "削弱", "背离", "打折"))
    if dimension_id == "has_conclusion_boundary":
        return isinstance(brief.get("conclusion_boundary"), str) and len(
            brief["conclusion_boundary"].strip()
        ) >= 20
    if dimension_id == "has_key_variables":
        return isinstance(brief.get("key_variables"), list) and bool(
            brief["key_variables"]
        )
    if dimension_id == "no_engineering_labels":
        assert_no_frontstage_engineering_labels(brief)
        return True
    if dimension_id == "no_backend_trace":
        return not _contains_any(full_text, _BACKEND_TRACE_MARKERS)
    if dimension_id == "no_user_responsibility_shift":
        return not _contains_any(_strip_allowed_exact_texts(full_text), _RESPONSIBILITY_SHIFT_MARKERS)
    if dimension_id == "no_trading_advice":
        return not _contains_any(_strip_allowed_exact_texts(full_text), _TRADING_MARKERS)
    if dimension_id == "source_note_is_tushare":
        return brief.get("source_note") == _SOURCE_NOTE
    raise TickerOnlyProfessionalBriefQualityEvaluationError(
        f"unsupported rubric dimension: {dimension_id}"
    )


def _sample_specific_quality_issues(
    sample_id: str,
    brief: Mapping[str, Any],
) -> list[dict[str, Any]]:
    text = _serialized_text(brief)
    if sample_id == "cashflow_supports_profit":
        if _has_text(text, ("现金流对利润形成支撑", "现金流对利润的支撑")):
            return []
        return [
            _build_issue(
                issue_id="cashflow_support_judgment_missing",
                severity=QUALITY_STATUS_FAIL,
                message="Cashflow support judgment was not visible.",
                section_id="operating_quality_view",
            )
        ]
    if sample_id == "profit_stronger_than_cashflow":
        if _has_text(text, ("利润表现强于现金流", "经营质量判断需要打折", "现金流弱于利润")):
            return [
                _build_issue(
                    issue_id="cashflow_profit_quality_pressure",
                    severity=QUALITY_STATUS_WARNING,
                    message="Cashflow is weaker than profit in the visible judgment.",
                    section_id="operating_quality_view",
                )
            ]
        return [
            _build_issue(
                issue_id="cashflow_profit_pressure_missing",
                severity=QUALITY_STATUS_FAIL,
                message="Cashflow and profit pressure was not visible.",
                section_id="operating_quality_view",
            )
        ]
    if sample_id == "high_receivables_pressure":
        if _has_text(text, ("应收扩张", "应收占用", "回款效率")):
            return [
                _build_issue(
                    issue_id="receivables_working_capital_pressure",
                    severity=QUALITY_STATUS_WARNING,
                    message="Receivables pressure is visible in the judgment.",
                    section_id="operating_quality_view",
                )
            ]
        return [
            _build_issue(
                issue_id="receivables_pressure_missing",
                severity=QUALITY_STATUS_FAIL,
                message="Receivables pressure was not visible.",
                section_id="operating_quality_view",
            )
        ]
    if sample_id == "high_debt_pressure":
        if _has_text(text, ("资产负债结构压力偏高", "负债结构压力", "资产负债")):
            return [
                _build_issue(
                    issue_id="balance_sheet_debt_pressure",
                    severity=QUALITY_STATUS_WARNING,
                    message="Balance sheet pressure is visible in the judgment.",
                    section_id="financial_view",
                )
            ]
        return [
            _build_issue(
                issue_id="debt_pressure_missing",
                severity=QUALITY_STATUS_FAIL,
                message="Balance sheet pressure was not visible.",
                section_id="financial_view",
            )
        ]
    if sample_id == "sparse_or_missing_metrics":
        return [
            _build_issue(
                issue_id="sparse_metrics_professional_boundary",
                severity=QUALITY_STATUS_WARNING,
                message="Sparse metrics still produced a professional boundary.",
                section_id="conclusion_boundary",
            )
        ]
    return []


def _professional_compact_brief_preview(brief: Mapping[str, Any]) -> dict[str, Any]:
    preview = {
        "schema_version": brief.get("schema_version"),
        "stock_code": brief.get("stock_code"),
        "ts_code": brief.get("ts_code"),
        "company_name_hint": brief.get("company_name_hint"),
        "title": brief.get("title"),
        "not_for_trading_advice": True,
    }
    for key in _SECTION_VIEW_KEYS:
        if key in brief:
            preview[key] = deepcopy(brief[key])
    preview["key_variables"] = deepcopy(brief.get("key_variables", []))
    preview["conclusion_boundary"] = brief.get("conclusion_boundary")
    preview["source_note"] = brief.get("source_note")
    assert_no_quality_evaluation_forbidden_markers(preview)
    assert_no_frontstage_engineering_labels(preview)
    return preview


def _aggregate_issues(
    sample_results: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str | None], dict[str, Any]] = {}
    for result in sample_results:
        sample_id = str(result["sample_id"])
        for issue in result["issues"]:
            key = (
                issue["issue_id"],
                issue["severity"],
                issue["message"],
                issue.get("section_id"),
            )
            if key not in grouped:
                grouped[key] = {
                    "schema_version": (
                        TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_ISSUE_SCHEMA_VERSION
                    ),
                    "issue_id": issue["issue_id"],
                    "severity": issue["severity"],
                    "message": issue["message"],
                    "section_id": issue.get("section_id"),
                    "sample_ids": [],
                    "count": 0,
                }
            grouped[key]["sample_ids"].append(sample_id)
            grouped[key]["count"] += 1
    result = []
    for issue in grouped.values():
        issue["sample_ids"] = sorted(issue["sample_ids"])
        result.append(_validate_aggregate_issue(issue, "aggregate_issue"))
    return sorted(
        result,
        key=lambda issue: (
            issue["severity"],
            issue["issue_id"],
            ",".join(issue["sample_ids"]),
        ),
    )


def _scenario_metrics(sample_id: str, periods: Iterable[str]) -> dict[str, dict[str, Any]]:
    _require_sample_id(sample_id)
    period_list = list(periods)
    if not period_list:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            "sample periods cannot be empty"
        )
    previous = deepcopy(_BASE_PREVIOUS_METRICS)
    latest = deepcopy(_BASE_LATEST_METRICS)
    if sample_id == "non_600406_sample":
        latest.update(
            {
                "revenue": 1200.0,
                "n_income_attr_p": 135.0,
                "total_profit": 160.0,
                "accounts_receiv": 130.0,
                "n_cashflow_act": 170.0,
                "grossprofit_margin": 28.0,
                "netprofit_margin": 11.0,
                "roe": 13.0,
                "debt_to_assets": 38.0,
            }
        )
    elif sample_id == "cashflow_supports_profit":
        latest.update({"n_income_attr_p": 110.0, "total_profit": 128.0, "n_cashflow_act": 240.0})
    elif sample_id == "profit_stronger_than_cashflow":
        latest.update({"n_income_attr_p": 170.0, "total_profit": 190.0, "n_cashflow_act": 45.0})
    elif sample_id == "high_receivables_pressure":
        latest.update({"accounts_receiv": 420.0, "ar_turn": 0.8})
    elif sample_id == "high_debt_pressure":
        latest.update(
            {
                "total_assets": 3600.0,
                "total_liab": 2520.0,
                "total_hldr_eqy_exc_min_int": 1080.0,
                "debt_to_assets": 70.0,
            }
        )
    elif sample_id == "sparse_or_missing_metrics":
        latest = {key: None for key in latest}
        previous = {key: None for key in previous}
        latest.update({"total_assets": 3000.0, "total_liab": None})
        previous.update({"total_assets": 2800.0, "total_liab": None})

    by_period = {}
    for index, period in enumerate(period_list):
        by_period[period] = deepcopy(latest if index == len(period_list) - 1 else previous)
    return by_period


class _ScenarioFakeTushareClient:
    def __init__(self, *, sample_id: str, ts_code: str, periods: Iterable[str]) -> None:
        self.sample_id = _require_sample_id(sample_id)
        self.ts_code = ts_code
        self.periods = list(periods)
        self.calls: list[dict[str, Any]] = []
        self._metrics_by_period = _scenario_metrics(sample_id, self.periods)

    def income(self, **params: Any) -> list[dict[str, Any]]:
        return self._call("income", params)

    def balancesheet(self, **params: Any) -> list[dict[str, Any]]:
        return self._call("balancesheet", params)

    def cashflow(self, **params: Any) -> list[dict[str, Any]]:
        return self._call("cashflow", params)

    def fina_indicator(self, **params: Any) -> list[dict[str, Any]]:
        return self._call("fina_indicator", params)

    def _call(self, table_name: str, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        self.calls.append({"endpoint": table_name, "params": dict(params)})
        period = str(params["period"])
        row = {
            "ts_code": params["ts_code"],
            "period": period,
            "ann_date": "20260430" if period.endswith("1231") else "20260429",
            "end_date": period,
        }
        metrics = self._metrics_by_period.get(period, {})
        for field in _TABLE_FIELDS[table_name]:
            row[field] = metrics.get(field)
        return [row]


def _rubric_dimension(
    dimension_id: str,
    section_id: str | None,
    pass_message: str,
) -> dict[str, Any]:
    return {
        "dimension_id": dimension_id,
        "section_id": section_id,
        "pass_message": pass_message,
        "required": True,
    }


def _validate_rubric_dimension(value: Any, path: str) -> dict[str, Any]:
    dimension = _require_mapping(value, path)
    expected = {"dimension_id", "section_id", "pass_message", "required"}
    unsupported = sorted(set(dimension) - expected)
    if unsupported:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"{path} contains unsupported keys: {unsupported}"
        )
    _require_fields(dimension, expected, path)
    result = deepcopy(dict(dimension))
    if result["dimension_id"] not in RUBRIC_DIMENSION_IDS:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"{path}.dimension_id invalid"
        )
    if result["section_id"] is not None and not isinstance(result["section_id"], str):
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"{path}.section_id must be string or null"
        )
    _require_non_empty_string(result["pass_message"], f"{path}.pass_message")
    _require_true(result["required"], f"{path}.required")
    return result


def _validate_sample_result(value: Any, path: str) -> dict[str, Any]:
    sample = _require_mapping(value, path)
    unsupported = sorted(set(sample) - _SAMPLE_RESULT_FIELDS)
    if unsupported:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"{path} contains unsupported keys: {unsupported}"
        )
    _require_fields(sample, _SAMPLE_RESULT_FIELDS, path)
    result = deepcopy(dict(sample))
    _require_sample_id(result["sample_id"])
    for key in ("stock_code", "ts_code", "scenario", "readiness_status"):
        _require_non_empty_string(result[key], f"{path}.{key}")
    if result["overall_status"] not in QUALITY_STATUSES:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"{path}.overall_status invalid"
        )
    _require_optional_string(result["source_note"], f"{path}.source_note")
    _require_string_list(result["brief_section_keys"], f"{path}.brief_section_keys")
    result["scorecard"] = validate_quality_scorecard(result["scorecard"])
    result["issues"] = [
        _validate_issue(issue, f"{path}.issues[{index}]")
        for index, issue in enumerate(_require_list(result["issues"], f"{path}.issues"))
    ]
    if result["issues"] != result["scorecard"]["issues"]:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"{path}.issues mismatch"
        )
    if result["professional_compact_brief_preview"] is not None:
        preview = _require_mapping(
            result["professional_compact_brief_preview"],
            f"{path}.professional_compact_brief_preview",
        )
        assert_no_quality_evaluation_forbidden_markers(preview)
        assert_no_frontstage_engineering_labels(preview)
        result["professional_compact_brief_preview"] = deepcopy(dict(preview))
    expected_status = result["scorecard"]["overall_status"]
    if result["overall_status"] != expected_status:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"{path}.overall_status mismatch"
        )
    assert_no_quality_evaluation_forbidden_markers(result)
    return result


def _validate_dimension_score(value: Any, path: str) -> dict[str, Any]:
    score = _require_mapping(value, path)
    unsupported = sorted(set(score) - _DIMENSION_SCORE_FIELDS)
    if unsupported:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"{path} contains unsupported keys: {unsupported}"
        )
    _require_fields(score, _DIMENSION_SCORE_FIELDS, path)
    result = deepcopy(dict(score))
    if result["dimension_id"] not in RUBRIC_DIMENSION_IDS:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"{path}.dimension_id invalid"
        )
    if result["status"] not in QUALITY_STATUSES:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"{path}.status invalid"
        )
    if result["severity"] != result["status"]:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"{path}.severity mismatch"
        )
    _require_non_empty_string(result["message"], f"{path}.message")
    _require_optional_string(result["section_id"], f"{path}.section_id")
    return result


def _build_issue(
    *,
    issue_id: str,
    severity: str,
    message: str,
    section_id: str | None,
) -> dict[str, Any]:
    issue = {
        "schema_version": (
            TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_ISSUE_SCHEMA_VERSION
        ),
        "issue_id": issue_id,
        "severity": severity,
        "message": message,
        "section_id": section_id,
    }
    return _validate_issue(issue, "issue")


def _validate_issue(value: Any, path: str) -> dict[str, Any]:
    issue = _require_mapping(value, path)
    unsupported = sorted(set(issue) - _ISSUE_FIELDS)
    if unsupported:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"{path} contains unsupported keys: {unsupported}"
        )
    _require_fields(issue, _ISSUE_FIELDS, path)
    result = deepcopy(dict(issue))
    if result["schema_version"] != (
        TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_ISSUE_SCHEMA_VERSION
    ):
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"{path}.schema_version invalid"
        )
    _require_non_empty_string(result["issue_id"], f"{path}.issue_id")
    if result["severity"] not in QUALITY_STATUSES:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"{path}.severity invalid"
        )
    _require_non_empty_string(result["message"], f"{path}.message")
    _require_optional_string(result["section_id"], f"{path}.section_id")
    assert_no_quality_evaluation_forbidden_markers(result)
    return result


def _validate_aggregate_issue(value: Any, path: str) -> dict[str, Any]:
    issue = _require_mapping(value, path)
    unsupported = sorted(set(issue) - _AGGREGATE_ISSUE_FIELDS)
    if unsupported:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"{path} contains unsupported keys: {unsupported}"
        )
    _require_fields(issue, _AGGREGATE_ISSUE_FIELDS, path)
    result = deepcopy(dict(issue))
    base_issue = {
        key: result[key]
        for key in _ISSUE_FIELDS
    }
    _validate_issue(base_issue, path)
    result["sample_ids"] = _normalise_sample_ids(result["sample_ids"])
    if _require_non_negative_int(result["count"], f"{path}.count") != len(
        result["sample_ids"]
    ):
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"{path}.count mismatch"
        )
    assert_no_quality_evaluation_forbidden_markers(result)
    return result


def _normalise_sample_ids(sample_ids: Iterable[str] | None) -> list[str]:
    if sample_ids is None:
        return list(QUALITY_SAMPLE_IDS)
    if isinstance(sample_ids, str):
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            "sample_ids must be a list, not string"
        )
    result = []
    for sample_id in sample_ids:
        result.append(_require_sample_id(sample_id))
    if not result:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            "sample_ids cannot be empty"
        )
    return result


def _require_sample_id(value: Any) -> str:
    if not isinstance(value, str) or value not in QUALITY_SAMPLE_IDS:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"unsupported sample_id: {value}"
        )
    return value


def _failed_dimension_status(brief: Mapping[str, Any]) -> str:
    return QUALITY_STATUS_WARNING if _has_sparse_metric_language(brief) else QUALITY_STATUS_FAIL


def _has_sparse_metric_language(brief: Mapping[str, Any]) -> bool:
    return _contains_any(
        _serialized_text(brief),
        (
            "尚未形成",
            "不够",
            "不足",
            "缺少",
            "missing",
            "absent",
        ),
    )


def _brief_section_keys(brief: Mapping[str, Any]) -> list[str]:
    return [key for key in PROFESSIONAL_BRIEF_SECTION_KEYS if key in brief]


def _section_text(brief: Mapping[str, Any], section_id: str) -> str:
    section = brief.get(section_id)
    if isinstance(section, Mapping):
        return " ".join(
            str(section.get(key, ""))
            for key in ("section_id", "title", "view")
            if section.get(key) is not None
        )
    if section is None:
        return ""
    return str(section)


def _serialized_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _has_text(value: str, markers: Iterable[str]) -> bool:
    return _contains_any(value, markers)


def _contains_any(value: str, markers: Iterable[str]) -> bool:
    lowered = value.casefold()
    separator = _normalize_separator_text(value)
    normalized = _normalise_marker(value)
    for marker in markers:
        marker_text = str(marker)
        marker_lower = marker_text.casefold()
        marker_normalized = _normalise_marker(marker_text)
        if marker_normalized in _WORD_MARKERS:
            if re.search(
                rf"(?<![a-z0-9_]){re.escape(marker_normalized)}(?![a-z0-9_])",
                normalized,
            ):
                return True
            continue
        if (
            marker_lower in lowered
            or _normalize_separator_text(marker_text) in separator
            or (marker_normalized and marker_normalized in normalized)
            or marker_text in value
        ):
            return True
    return False


def _strip_allowed_exact_texts(value: str) -> str:
    result = value
    for allowed_text in _ALLOWED_EXACT_TEXTS:
        result = result.replace(allowed_text, "")
    return result


def _combine_statuses(statuses: Iterable[str]) -> str:
    status_list = list(statuses)
    if any(status == QUALITY_STATUS_FAIL for status in status_list):
        return QUALITY_STATUS_FAIL
    if any(status == QUALITY_STATUS_WARNING for status in status_list):
        return QUALITY_STATUS_WARNING
    return QUALITY_STATUS_PASS


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
    searchable_value = value
    for allowed_text in _ALLOWED_EXACT_TEXTS:
        searchable_value = searchable_value.replace(allowed_text, "")
    for pattern in _SECRET_LIKE_PATTERNS:
        if pattern.search(searchable_value):
            return "secret_like_string"

    lowered = searchable_value.casefold()
    separator = _normalize_separator_text(searchable_value)
    normalized = _normalise_marker(searchable_value)
    for marker in _QUALITY_FORBIDDEN_MARKERS:
        marker_lower = marker.casefold()
        marker_separator = _normalize_separator_text(marker)
        marker_normalized = _normalise_marker(marker)
        if marker_lower == ".env":
            if ".env" in lowered:
                return "forbidden_marker"
            continue
        if marker_normalized in _WORD_MARKERS:
            if re.search(
                rf"(?<![a-z0-9_]){re.escape(marker_normalized)}(?![a-z0-9_])",
                normalized,
            ):
                return "forbidden_marker"
            continue
        if (
            marker_lower in lowered
            or marker_separator in separator
            or (marker_normalized and marker_normalized in normalized)
        ):
            return "forbidden_marker"
    if any(marker in searchable_value for marker in _QUALITY_FORBIDDEN_CJK_MARKERS):
        return "forbidden_marker"
    return None


def _reject_bytes(value: Any, path: str) -> None:
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"{path} contains raw bytes"
        )
    if isinstance(value, Mapping):
        for key, child in value.items():
            _reject_bytes(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_bytes(child, f"{path}[{index}]")


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"{field} must be a mapping"
        )
    return value


def _require_fields(value: Mapping[str, Any], fields: Iterable[str], path: str) -> None:
    missing = [field for field in fields if field not in value]
    if missing:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"{path} missing required fields: {missing}"
        )


def _require_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"{path} must be a list"
        )
    return value


def _require_string_list(value: Any, path: str) -> list[str]:
    result = _require_list(value, path)
    for index, item in enumerate(result):
        if not isinstance(item, str):
            raise TickerOnlyProfessionalBriefQualityEvaluationError(
                f"{path}[{index}] must be string"
            )
    return result


def _require_non_empty_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"{path} must be a non-empty string"
        )
    return value


def _require_optional_string(value: Any, path: str) -> None:
    if value is not None and not isinstance(value, str):
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"{path} must be string or null"
        )


def _require_true(value: Any, path: str) -> None:
    if value is not True:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"{path} must be true"
        )


def _require_non_negative_int(value: Any, path: str) -> int:
    if not isinstance(value, int) or value < 0:
        raise TickerOnlyProfessionalBriefQualityEvaluationError(
            f"{path} must be a non-negative int"
        )
    return value


def _normalise_marker(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().casefold()).strip("_")


def _normalize_separator_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[_-]+", " ", value.strip().casefold())).strip()


__all__ = [
    "QUALITY_SAMPLE_IDS",
    "QUALITY_STATUS_FAIL",
    "QUALITY_STATUS_PASS",
    "QUALITY_STATUS_WARNING",
    "RUBRIC_DIMENSION_IDS",
    "TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_EVALUATION_REQUEST_SCHEMA_VERSION",
    "TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_EVALUATION_RESULT_SCHEMA_VERSION",
    "TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_ISSUE_SCHEMA_VERSION",
    "TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_RUBRIC_SCHEMA_VERSION",
    "TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_SAMPLE_SCHEMA_VERSION",
    "TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_SCORECARD_SCHEMA_VERSION",
    "TickerOnlyProfessionalBriefQualityEvaluationError",
    "assert_no_frontstage_engineering_labels",
    "assert_no_quality_evaluation_forbidden_markers",
    "build_default_quality_rubric",
    "build_quality_sample_requests",
    "build_ticker_only_professional_brief_quality_evaluation",
    "evaluate_professional_compact_brief",
    "validate_quality_evaluation_request",
    "validate_quality_evaluation_result",
    "validate_quality_scorecard",
]
