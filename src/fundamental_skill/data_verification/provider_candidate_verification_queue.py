# -*- coding: utf-8 -*-
"""Provider candidate metric verification queue bridge.

This module converts an explicit Tushare provider-candidate financial trend
table into metric candidates that still require official disclosure
verification. It is intentionally pure: no network, no provider calls, no file
reads, and no artifact writes.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any


PROVIDER_NAME = "Tushare"
INPUT_SNAPSHOT_SCHEMA_VERSION = "provider_candidate_financial_snapshot.v1"
INPUT_TREND_TABLE_SCHEMA_VERSION = "provider_candidate_financial_trend_table.v1"
QUEUE_SCHEMA_VERSION = "provider_candidate_metric_verification_queue.v1"
QUEUE_ITEM_SCHEMA_VERSION = "provider_candidate_metric_verification_item.v1"
OFFICIAL_VERIFICATION_STATUS = "pending_official_verification"

ALLOWED_EXACT_KEYS = {"not_official_verified", "not_for_trading_advice"}
FORBIDDEN_MARKERS = (
    "token",
    ".env",
    "tushare_token",
    "official_verified",
    "official_metric_fact",
    "provider_official_conflict",
    "Report V1",
    "accepted manifest write",
    "output baseline write",
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
)
FORBIDDEN_CJK_MARKERS = (
    "买入",
    "卖出",
    "持有",
    "目标价",
    "仓位",
    "组合",
    "技术信号",
    "投资建议",
    "正式研报",
    "输出基线",
    "写入fixture",
    "写入accepted manifest",
    "读取token",
    "读取.env",
    "读取tushare_token",
    "涔板叆",
    "鍗栧嚭",
    "鎸佹湁",
    "鐩爣浠?",
    "浠撲綅",
    "缁勫悎",
    "鎶€鏈俊鍙?",
    "鎶曡祫寤鸿",
    "姝ｅ紡鐮旀姤",
    "杈撳嚭鍩虹嚎",
    "鍐欏叆fixture",
    "鍐欏叆accepted manifest",
    "璇诲彇token",
    "璇诲彇.env",
    "璇诲彇tushare_token",
)
WORD_MARKERS = {"token", "buy", "sell", "hold", "portfolio", "position"}
IDENTIFIER_SAFE_WORD_MARKERS = {"buy", "sell", "hold"}

METRIC_SELECTIONS = (
    {"metric_key": "revenue", "source_table": "income", "source_field": "revenue", "required": True},
    {
        "metric_key": "n_income_attr_p",
        "source_table": "income",
        "source_field": "n_income_attr_p",
        "required": True,
    },
    {"metric_key": "total_profit", "source_table": "income", "source_field": "total_profit", "required": True},
    {
        "metric_key": "operate_profit",
        "source_table": "income",
        "source_field": "operate_profit",
        "required": True,
    },
    {"metric_key": "basic_eps", "source_table": "income", "source_field": "basic_eps", "required": False},
    {
        "metric_key": "n_cashflow_act",
        "source_table": "cashflow",
        "source_field": "n_cashflow_act",
        "required": True,
    },
    {"metric_key": "c_fr_sale_sg", "source_table": "cashflow", "source_field": "c_fr_sale_sg", "required": True},
    {
        "metric_key": "c_cash_equ_end_period",
        "source_table": "cashflow",
        "source_field": "c_cash_equ_end_period",
        "required": False,
    },
    {
        "metric_key": "total_assets",
        "source_table": "balancesheet",
        "source_field": "total_assets",
        "required": True,
    },
    {
        "metric_key": "total_liab",
        "source_table": "balancesheet",
        "source_field": "total_liab",
        "required": True,
    },
    {
        "metric_key": "accounts_receiv",
        "source_table": "balancesheet",
        "source_field": "accounts_receiv",
        "required": True,
    },
    {
        "metric_key": "inventories",
        "source_table": "balancesheet",
        "source_field": "inventories",
        "required": True,
    },
    {
        "metric_key": "total_hldr_eqy_exc_min_int",
        "source_table": "balancesheet",
        "source_field": "total_hldr_eqy_exc_min_int",
        "required": False,
    },
    {
        "metric_key": "grossprofit_margin",
        "source_table": "fina_indicator",
        "source_field": "grossprofit_margin",
        "required": True,
    },
    {
        "metric_key": "netprofit_margin",
        "source_table": "fina_indicator",
        "source_field": "netprofit_margin",
        "required": True,
    },
    {"metric_key": "roe", "source_table": "fina_indicator", "source_field": "roe", "required": True},
    {
        "metric_key": "debt_to_assets",
        "source_table": "fina_indicator",
        "source_field": "debt_to_assets",
        "required": True,
    },
    {"metric_key": "ar_turn", "source_table": "fina_indicator", "source_field": "ar_turn", "required": False},
    {"metric_key": "inv_turn", "source_table": "fina_indicator", "source_field": "inv_turn", "required": False},
)


class ProviderCandidateVerificationQueueError(ValueError):
    """Raised when a provider candidate verification queue fails closed."""


def build_provider_candidate_metric_verification_queue(provider_candidate_result: Any) -> dict[str, Any]:
    """Build a queue of provider metrics that need official verification."""

    assert_no_provider_candidate_queue_forbidden_markers(provider_candidate_result)
    blockers = _input_blockers(provider_candidate_result)
    if blockers:
        result = _empty_queue(provider_candidate_result if isinstance(provider_candidate_result, Mapping) else None)
        result["blocked_reasons"].extend(blockers)
        result["caveats"].append("provider_candidate_input_rejected")
        validate_provider_candidate_metric_verification_queue(result)
        return result

    assert isinstance(provider_candidate_result, Mapping)
    result = _empty_queue(provider_candidate_result)
    result["verification_items"] = build_verification_items_from_trend_table(provider_candidate_result)
    result["caveats"].extend(_safe_string_values(provider_candidate_result.get("caveats", [])))
    result["caveats"].append("provider_candidate_values_require_official_verification")
    validate_provider_candidate_metric_verification_queue(result)
    return result


def build_verification_items_from_trend_table(provider_candidate_result: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Build verification queue items from provider trend rows."""

    items: list[dict[str, Any]] = []
    for trend_row in provider_candidate_result.get("trend_table", []):
        if not isinstance(trend_row, Mapping):
            continue
        source_tables_available = set(_safe_string_values(trend_row.get("source_tables_available", [])))
        selected_metrics = trend_row.get("selected_metrics")
        metric_values = selected_metrics if isinstance(selected_metrics, Mapping) else trend_row

        for selection in METRIC_SELECTIONS:
            metric_key = str(selection["metric_key"])
            source_table = str(selection["source_table"])
            metric_value = metric_values.get(metric_key) if isinstance(metric_values, Mapping) else None
            source_table_available = source_table in source_tables_available
            value_status = "present" if metric_value is not None else "missing"
            caveats = ["provider_candidate_requires_official_verification"]
            if value_status == "missing":
                caveats.append(f"missing_provider_metric:{metric_key}")
            if not source_table_available:
                caveats.append(f"source_table_unavailable:{source_table}")
            if trend_row.get("ann_date") in (None, ""):
                caveats.append("missing_provider_ann_date")

            items.append(
                {
                    "schema_version": QUEUE_ITEM_SCHEMA_VERSION,
                    "provider": PROVIDER_NAME,
                    "ts_code": provider_candidate_result.get("ts_code"),
                    "stock_code": provider_candidate_result.get("stock_code"),
                    "company_name_hint": provider_candidate_result.get("company_name_hint"),
                    "period": trend_row.get("period"),
                    "period_label": trend_row.get("period_label"),
                    "ann_date": trend_row.get("ann_date"),
                    "end_date": trend_row.get("end_date"),
                    "metric_key": metric_key,
                    "metric_value": metric_value,
                    "source_table": source_table,
                    "source_field": str(selection["source_field"]),
                    "source_table_available": source_table_available,
                    "provider_native_unit": _provider_native_unit(metric_key),
                    "value_status": value_status,
                    "official_verification_status": OFFICIAL_VERIFICATION_STATUS,
                    "official_verification_required": True,
                    "not_official_verified": True,
                    "not_for_trading_advice": True,
                    "caveats": caveats,
                }
            )
    return items


def select_metric_keys_for_official_verification(provider_candidate_result: Any | None = None) -> list[str]:
    """Return the deterministic first-pass metric key selection."""

    del provider_candidate_result
    return [str(selection["metric_key"]) for selection in METRIC_SELECTIONS]


def validate_provider_candidate_metric_verification_queue(queue: Mapping[str, Any]) -> None:
    """Validate queue shape and provider-candidate safety markers."""

    if not isinstance(queue, Mapping):
        raise ProviderCandidateVerificationQueueError("invalid_queue")
    if queue.get("schema_version") != QUEUE_SCHEMA_VERSION:
        raise ProviderCandidateVerificationQueueError("invalid_queue_schema_version")
    if queue.get("provider") != PROVIDER_NAME:
        raise ProviderCandidateVerificationQueueError("invalid_queue_provider")
    _require_true_bool(queue, "not_official_verified", "$")
    _require_true_bool(queue, "not_for_trading_advice", "$")

    if not isinstance(queue.get("verification_items"), list):
        raise ProviderCandidateVerificationQueueError("invalid_verification_items")
    for index, item in enumerate(queue["verification_items"]):
        _validate_queue_item(item, f"$.verification_items[{index}]")

    if not isinstance(queue.get("blocked_reasons"), list):
        raise ProviderCandidateVerificationQueueError("invalid_blocked_reasons")
    if not isinstance(queue.get("caveats"), list):
        raise ProviderCandidateVerificationQueueError("invalid_caveats")
    assert_no_provider_candidate_queue_forbidden_markers(queue)


def assert_no_provider_candidate_queue_forbidden_markers(value: Any) -> None:
    """Reject forbidden markers in nested dict/list/string payloads."""

    finding = _find_forbidden_marker(value)
    if finding is not None:
        raise ProviderCandidateVerificationQueueError("forbidden_marker")


def _empty_queue(provider_candidate_result: Mapping[str, Any] | None) -> dict[str, Any]:
    periods: list[str] = []
    if provider_candidate_result is not None:
        raw_periods = provider_candidate_result.get("periods")
        if isinstance(raw_periods, list):
            periods = [str(period) for period in raw_periods]
        elif isinstance(provider_candidate_result.get("trend_table"), list):
            periods = [
                str(row.get("period"))
                for row in provider_candidate_result["trend_table"]
                if isinstance(row, Mapping) and row.get("period") not in (None, "")
            ]
    return {
        "schema_version": QUEUE_SCHEMA_VERSION,
        "provider": PROVIDER_NAME,
        "ts_code": provider_candidate_result.get("ts_code") if provider_candidate_result else None,
        "stock_code": provider_candidate_result.get("stock_code") if provider_candidate_result else None,
        "company_name_hint": provider_candidate_result.get("company_name_hint") if provider_candidate_result else None,
        "periods": periods,
        "verification_items": [],
        "blocked_reasons": [],
        "caveats": [],
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }


def _input_blockers(provider_candidate_result: Any) -> list[str]:
    if provider_candidate_result is None:
        return ["missing_provider_candidate_result"]
    if not isinstance(provider_candidate_result, Mapping):
        return ["provider_candidate_result_must_be_mapping"]

    blockers: list[str] = []
    if provider_candidate_result.get("schema_version") != INPUT_SNAPSHOT_SCHEMA_VERSION:
        blockers.append("invalid_provider_candidate_schema_version")
    if provider_candidate_result.get("provider") != PROVIDER_NAME:
        blockers.append("unsupported_provider")
    _append_flag_blocker(blockers, provider_candidate_result, "not_official_verified")
    _append_flag_blocker(blockers, provider_candidate_result, "not_for_trading_advice")

    trend_table = provider_candidate_result.get("trend_table")
    if "trend_table" not in provider_candidate_result:
        blockers.append("missing_trend_table")
    elif not isinstance(trend_table, list):
        blockers.append("trend_table_must_be_list")
    else:
        for index, trend_row in enumerate(trend_table):
            if not isinstance(trend_row, Mapping):
                blockers.append(f"invalid_trend_row:{index}")
                continue
            if trend_row.get("schema_version") not in (None, INPUT_TREND_TABLE_SCHEMA_VERSION):
                blockers.append(f"invalid_trend_row_schema_version:{index}")
            if "provider" not in trend_row:
                blockers.append(f"missing_trend_row_provider:{index}")
            elif trend_row.get("provider") != PROVIDER_NAME:
                blockers.append(f"unsupported_trend_row_provider:{index}")
            if trend_row.get("period") in (None, ""):
                blockers.append(f"missing_trend_row_period:{index}")
            _append_flag_blocker(blockers, trend_row, "not_official_verified", prefix=f"trend_row:{index}:")
            _append_flag_blocker(blockers, trend_row, "not_for_trading_advice", prefix=f"trend_row:{index}:")
    return blockers


def _append_flag_blocker(
    blockers: list[str],
    payload: Mapping[str, Any],
    key: str,
    *,
    prefix: str = "",
) -> None:
    reason_key = "advice_safety_flag" if key == "not_for_trading_advice" else key
    if key not in payload:
        blockers.append(f"{prefix}missing_{reason_key}")
    elif payload.get(key) is not True:
        blockers.append(f"{prefix}{reason_key}_must_be_true_bool")


def _validate_queue_item(item: Any, path: str) -> None:
    if not isinstance(item, Mapping):
        raise ProviderCandidateVerificationQueueError("invalid_verification_item")
    required = (
        "schema_version",
        "provider",
        "ts_code",
        "stock_code",
        "company_name_hint",
        "period",
        "period_label",
        "ann_date",
        "end_date",
        "metric_key",
        "metric_value",
        "source_table",
        "source_field",
        "source_table_available",
        "provider_native_unit",
        "value_status",
        "official_verification_status",
        "official_verification_required",
        "not_official_verified",
        "not_for_trading_advice",
        "caveats",
    )
    for key in required:
        if key not in item:
            raise ProviderCandidateVerificationQueueError(f"{path}:{key}_missing")
    if item.get("schema_version") != QUEUE_ITEM_SCHEMA_VERSION:
        raise ProviderCandidateVerificationQueueError("invalid_item_schema_version")
    if item.get("provider") != PROVIDER_NAME:
        raise ProviderCandidateVerificationQueueError("invalid_item_provider")
    if item.get("ts_code") in (None, ""):
        raise ProviderCandidateVerificationQueueError("missing_item_ts_code")
    if item.get("stock_code") in (None, ""):
        raise ProviderCandidateVerificationQueueError("missing_item_stock_code")
    if item.get("period") in (None, ""):
        raise ProviderCandidateVerificationQueueError("missing_item_period")
    if item.get("period_label") in (None, ""):
        raise ProviderCandidateVerificationQueueError("missing_item_period_label")
    if item.get("end_date") in (None, ""):
        raise ProviderCandidateVerificationQueueError("missing_item_end_date")
    if item.get("official_verification_status") != OFFICIAL_VERIFICATION_STATUS:
        raise ProviderCandidateVerificationQueueError("invalid_official_verification_status")
    if item.get("official_verification_required") is not True:
        raise ProviderCandidateVerificationQueueError("official_verification_required_must_be_true")
    if item.get("value_status") not in {"present", "missing"}:
        raise ProviderCandidateVerificationQueueError("invalid_value_status")
    if not isinstance(item.get("source_table_available"), bool):
        raise ProviderCandidateVerificationQueueError("invalid_source_table_available")
    if item.get("source_table_available") is False and item.get("metric_value") is not None:
        raise ProviderCandidateVerificationQueueError("unavailable_source_table_has_value")
    if item.get("source_table_available") is False and item.get("value_status") == "present":
        raise ProviderCandidateVerificationQueueError("unavailable_source_table_has_present_value")
    if item.get("value_status") == "missing" and item.get("metric_value") is not None:
        raise ProviderCandidateVerificationQueueError("missing_item_has_value")
    if item.get("value_status") == "present" and item.get("metric_value") is None:
        raise ProviderCandidateVerificationQueueError("present_item_missing_value")
    if not isinstance(item.get("caveats"), list):
        raise ProviderCandidateVerificationQueueError("invalid_item_caveats")
    _require_true_bool(item, "not_official_verified", path)
    _require_true_bool(item, "not_for_trading_advice", path)


def _require_true_bool(payload: Mapping[str, Any], key: str, path: str) -> None:
    if key not in payload:
        raise ProviderCandidateVerificationQueueError(f"{path}:{key}_missing")
    if payload.get(key) is not True:
        raise ProviderCandidateVerificationQueueError(f"{path}:{key}_must_be_true")


def _safe_string_values(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(value) for value in values if value not in (None, "")]


def _provider_native_unit(metric_key: str) -> str:
    if metric_key in {"grossprofit_margin", "netprofit_margin", "roe", "debt_to_assets"}:
        return "provider_native_ratio_unverified"
    if metric_key in {"ar_turn", "inv_turn"}:
        return "provider_native_turnover_unverified"
    if metric_key == "basic_eps":
        return "provider_native_per_share_unverified"
    return "provider_native_amount_unverified"


def _find_forbidden_marker(value: Any) -> str | None:
    if isinstance(value, Mapping):
        for key, nested_value in value.items():
            key_text = str(key)
            if key_text not in ALLOWED_EXACT_KEYS and _text_has_forbidden_marker(key_text):
                return key_text
            finding = _find_forbidden_marker(nested_value)
            if finding is not None:
                return finding
        return None
    if isinstance(value, (list, tuple, set)):
        for item in value:
            finding = _find_forbidden_marker(item)
            if finding is not None:
                return finding
        return None
    if isinstance(value, str) and _text_has_forbidden_marker(value):
        return value
    return None


def _text_has_forbidden_marker(value: str) -> bool:
    normalized = _normalize_marker_text(value)
    separator_normalized = _normalize_marker_text(re.sub(r"[_-]+", " ", value))
    if normalized == "not_official_verified":
        return False

    for marker in FORBIDDEN_MARKERS:
        marker_text = _normalize_marker_text(marker)
        if marker_text in WORD_MARKERS:
            boundary_chars = "a-z0-9_" if marker_text in IDENTIFIER_SAFE_WORD_MARKERS else "a-z0-9"
            if re.search(rf"(?<![{boundary_chars}]){re.escape(marker_text)}(?![{boundary_chars}])", normalized):
                return True
            continue
        if marker_text == "official_verified":
            if _contains_official_verified_marker(normalized):
                return True
            continue
        if marker_text in normalized or marker_text in separator_normalized:
            return True
    return any(marker in value for marker in FORBIDDEN_CJK_MARKERS)


def _contains_official_verified_marker(value: str) -> bool:
    if value == "not_official_verified":
        return False
    return bool(re.search(r"(?<!not_)official_verified", value))


def _normalize_marker_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().casefold())
