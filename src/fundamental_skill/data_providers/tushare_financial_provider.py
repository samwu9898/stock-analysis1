# -*- coding: utf-8 -*-
"""Tushare financial statement provider-candidate thin slice.

This module intentionally stays outside the official verification path. Tushare
rows are provider-candidate observations only and must not be accepted as
officially verified facts by this slice.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterable, Mapping
from typing import Any

from .tushare_client import TushareClient
from .tushare_sdk_transport import TushareSdkTransport, TushareSdkTransportError


PROVIDER_NAME = "Tushare"
SNAPSHOT_SCHEMA_VERSION = "provider_candidate_financial_snapshot.v1"
TREND_TABLE_SCHEMA_VERSION = "provider_candidate_financial_trend_table.v1"
DEFAULT_TS_CODE = "600406.SH"
DEFAULT_COMPANY_NAME_HINT = "国电南瑞"
SUPPORTED_PERIODS = ("20251231", "20260331")
PERIOD_LABELS = {"20251231": "2025FY", "20260331": "2026Q1"}
TARGET_TABLES = ("income", "balancesheet", "cashflow", "fina_indicator")

INCOME_SELECTED_FIELDS = (
    "revenue",
    "n_income_attr_p",
    "total_profit",
    "operate_profit",
    "basic_eps",
)
BALANCESHEET_SELECTED_FIELDS = (
    "total_assets",
    "total_liab",
    "total_hldr_eqy_exc_min_int",
    "accounts_receiv",
    "inventories",
)
CASHFLOW_SELECTED_FIELDS = (
    "n_cashflow_act",
    "c_cash_equ_end_period",
    "c_fr_sale_sg",
)
FINA_INDICATOR_SELECTED_FIELDS = (
    "grossprofit_margin",
    "netprofit_margin",
    "roe",
    "debt_to_assets",
    "ar_turn",
    "inv_turn",
)

TABLE_SELECTED_FIELDS = {
    "income": INCOME_SELECTED_FIELDS,
    "balancesheet": BALANCESHEET_SELECTED_FIELDS,
    "cashflow": CASHFLOW_SELECTED_FIELDS,
    "fina_indicator": FINA_INDICATOR_SELECTED_FIELDS,
}
ROW_BUCKET_BY_TABLE = {
    "income": "income_rows",
    "balancesheet": "balancesheet_rows",
    "cashflow": "cashflow_rows",
    "fina_indicator": "fina_indicator_rows",
}
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
)
_WORD_MARKERS = {"token", "buy", "sell", "hold", "portfolio", "position"}
_IDENTIFIER_SAFE_WORD_MARKERS = {"buy", "sell", "hold"}
_TS_CODE_RE = re.compile(r"^\d{6}\.(?:SH|SZ|BJ)$")
_UNSET = object()


class TushareFinancialProviderCandidateError(ValueError):
    """Raised when a provider-candidate result fails closed."""


def build_tushare_financial_provider_candidate(
    *,
    ts_code: str | None = DEFAULT_TS_CODE,
    periods: Any = _UNSET,
    company_name_hint: str | None = DEFAULT_COMPANY_NAME_HINT,
    api_client: Any | None = None,
    allow_network: bool = False,
) -> dict[str, Any]:
    """Build a provider-candidate snapshot and trend table.

    Network access is opt-in. Tests and normal callers should pass an injected
    fake ``api_client`` implementing the four target Tushare endpoint methods.
    """

    requested_periods = periods
    if requested_periods is _UNSET:
        requested_periods = list(SUPPORTED_PERIODS)

    input_blockers = _validate_request_inputs(ts_code=ts_code, periods=requested_periods)
    if input_blockers:
        return _blocked_result(
            ts_code=ts_code,
            periods=requested_periods if isinstance(requested_periods, list) else [],
            company_name_hint=company_name_hint,
            blocked_reasons=input_blockers,
        )

    assert ts_code is not None
    stock_code = ts_code.split(".", 1)[0]
    result = _empty_result(ts_code=ts_code, periods=requested_periods, company_name_hint=company_name_hint)
    result["stock_code"] = stock_code

    client, client_blocker = _resolve_api_client(api_client=api_client, allow_network=allow_network)
    if client_blocker is not None:
        result["blocked_reasons"].append(client_blocker)
        validate_provider_candidate_financial_result(result)
        return result

    assert client is not None
    fetched = fetch_tushare_financial_candidate(
        api_client=client,
        ts_code=ts_code,
        periods=requested_periods,
    )
    for table_name in TARGET_TABLES:
        result[ROW_BUCKET_BY_TABLE[table_name]] = fetched[ROW_BUCKET_BY_TABLE[table_name]]
    result["missing_tables"].extend(fetched["missing_tables"])
    result["blocked_reasons"].extend(fetched["blocked_reasons"])
    result["caveats"].extend(fetched["caveats"])
    result["trend_table"] = build_provider_candidate_trend_table(
        periods=requested_periods,
        income_rows=result["income_rows"],
        balancesheet_rows=result["balancesheet_rows"],
        cashflow_rows=result["cashflow_rows"],
        fina_indicator_rows=result["fina_indicator_rows"],
    )
    validate_provider_candidate_financial_result(result)
    return result


def fetch_tushare_financial_candidate(
    *,
    api_client: Any,
    ts_code: str,
    periods: list[str],
) -> dict[str, Any]:
    """Fetch and normalize target financial statement tables."""

    fetched = {
        "income_rows": [],
        "balancesheet_rows": [],
        "cashflow_rows": [],
        "fina_indicator_rows": [],
        "missing_tables": [],
        "blocked_reasons": [],
        "caveats": [],
    }
    for period in periods:
        for table_name in TARGET_TABLES:
            try:
                raw_response = getattr(api_client, table_name)(ts_code=ts_code, period=period)
                rows, rejected_reasons = _normalize_table_rows_with_rejections(
                    raw_response,
                    table_name=table_name,
                    ts_code=ts_code,
                    period=period,
                )
            except Exception:
                fetched["missing_tables"].append(_missing_table(table_name, period, "api_exception"))
                fetched["blocked_reasons"].append(f"api_exception:{table_name}:{period}")
                fetched["caveats"].append(f"{table_name} provider request failed for period {period}")
                continue

            for reason in rejected_reasons:
                _record_rejected_provider_row(fetched, table_name=table_name, period=period, reason=reason)

            if not rows:
                if not rejected_reasons:
                    fetched["missing_tables"].append(_missing_table(table_name, period, "empty_response"))
                    fetched["blocked_reasons"].append(f"empty_response:{table_name}:{period}")
                    fetched["caveats"].append(f"{table_name} returned no provider rows for period {period}")
                continue

            for duplicate_period in _periods_with_multiple_rows(rows):
                _record_multiple_provider_rows(fetched, table_name=table_name, period=duplicate_period)
            fetched[ROW_BUCKET_BY_TABLE[table_name]].extend(rows)

    return fetched


def normalize_tushare_income_rows(response: Any, *, ts_code: str, period: str) -> list[dict[str, Any]]:
    return _normalize_table_rows(response, table_name="income", ts_code=ts_code, period=period)


def normalize_tushare_balancesheet_rows(response: Any, *, ts_code: str, period: str) -> list[dict[str, Any]]:
    return _normalize_table_rows(response, table_name="balancesheet", ts_code=ts_code, period=period)


def normalize_tushare_cashflow_rows(response: Any, *, ts_code: str, period: str) -> list[dict[str, Any]]:
    return _normalize_table_rows(response, table_name="cashflow", ts_code=ts_code, period=period)


def normalize_tushare_fina_indicator_rows(response: Any, *, ts_code: str, period: str) -> list[dict[str, Any]]:
    return _normalize_table_rows(response, table_name="fina_indicator", ts_code=ts_code, period=period)


def build_provider_candidate_trend_table(
    *,
    periods: list[str],
    income_rows: list[dict[str, Any]],
    balancesheet_rows: list[dict[str, Any]],
    cashflow_rows: list[dict[str, Any]],
    fina_indicator_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows_by_table = {
        "income": _selected_row_by_period(income_rows),
        "balancesheet": _selected_row_by_period(balancesheet_rows),
        "cashflow": _selected_row_by_period(cashflow_rows),
        "fina_indicator": _selected_row_by_period(fina_indicator_rows),
    }
    trend_rows = []
    for period in periods:
        selected_metrics: dict[str, Any] = {}
        missing_fields: list[str] = []
        source_tables_available = []
        ann_date = None
        end_date = None

        for table_name in TARGET_TABLES:
            row = rows_by_table[table_name].get(period)
            if row is None:
                for field in TABLE_SELECTED_FIELDS[table_name]:
                    selected_metrics[field] = None
                    missing_fields.append(f"{table_name}.{field}")
                continue
            source_tables_available.append(table_name)
            ann_date = ann_date or row.get("ann_date")
            end_date = end_date or row.get("end_date")
            selected = row.get("selected_fields", {})
            for field in TABLE_SELECTED_FIELDS[table_name]:
                selected_metrics[field] = selected.get(field)
                if selected.get(field) is None:
                    missing_fields.append(f"{table_name}.{field}")

        trend_row = {
            "schema_version": TREND_TABLE_SCHEMA_VERSION,
            "provider": PROVIDER_NAME,
            "period_label": PERIOD_LABELS.get(period, period),
            "period": period,
            "ann_date": ann_date,
            "end_date": end_date,
            "source_tables_available": source_tables_available,
            "selected_metrics": selected_metrics,
            "missing_fields": missing_fields,
            "not_official_verified": True,
            "not_for_trading_advice": True,
        }
        trend_row.update(selected_metrics)
        trend_rows.append(trend_row)
    return trend_rows


def validate_provider_candidate_financial_result(result: Mapping[str, Any]) -> None:
    """Validate required provider-candidate markers and reject forbidden intent."""

    if result.get("schema_version") != SNAPSHOT_SCHEMA_VERSION:
        raise TushareFinancialProviderCandidateError("invalid_schema_version")
    if result.get("provider") != PROVIDER_NAME:
        raise TushareFinancialProviderCandidateError("invalid_provider")
    _require_true_bool(result, "not_official_verified", "$")
    _require_true_bool(result, "not_for_trading_advice", "$")

    for bucket in ("income_rows", "balancesheet_rows", "cashflow_rows", "fina_indicator_rows"):
        rows = result.get(bucket)
        if not isinstance(rows, list):
            raise TushareFinancialProviderCandidateError("invalid_row_bucket")
        for index, row in enumerate(rows):
            _validate_candidate_row(row, f"$.{bucket}[{index}]")

    trend_table = result.get("trend_table")
    if not isinstance(trend_table, list):
        raise TushareFinancialProviderCandidateError("invalid_trend_table")
    for index, row in enumerate(trend_table):
        if not isinstance(row, Mapping):
            raise TushareFinancialProviderCandidateError("invalid_trend_row")
        if row.get("schema_version") != TREND_TABLE_SCHEMA_VERSION:
            raise TushareFinancialProviderCandidateError("invalid_trend_schema_version")
        if row.get("provider") != PROVIDER_NAME:
            raise TushareFinancialProviderCandidateError("invalid_trend_provider")
        _require_true_bool(row, "not_official_verified", f"$.trend_table[{index}]")
        _require_true_bool(row, "not_for_trading_advice", f"$.trend_table[{index}]")

    assert_no_tushare_provider_forbidden_markers(result)


def assert_no_tushare_provider_forbidden_markers(payload: Any) -> None:
    """Reject forbidden markers anywhere in nested dict/list/string payloads."""

    finding = _find_forbidden_marker(payload)
    if finding is not None:
        raise TushareFinancialProviderCandidateError("forbidden_marker")


def _validate_request_inputs(*, ts_code: str | None, periods: Any) -> list[str]:
    blockers = []
    if not ts_code:
        blockers.append("missing_ts_code")
    elif not isinstance(ts_code, str) or not _TS_CODE_RE.fullmatch(ts_code):
        blockers.append("unsupported_ts_code_format")

    if periods is None or periods == []:
        blockers.append("missing_periods")
    elif not isinstance(periods, list):
        blockers.append("periods_must_be_list")
    else:
        unsupported = [period for period in periods if period not in SUPPORTED_PERIODS]
        if unsupported:
            blockers.append("unsupported_period")
    return blockers


def _resolve_api_client(*, api_client: Any | None, allow_network: bool) -> tuple[Any | None, str | None]:
    if api_client is not None:
        return api_client, None
    if not allow_network:
        return None, "api_client_required_when_network_disabled"

    credential = os.environ.get("TUSHARE_TOKEN")
    if not credential:
        return None, "environment_credential_missing"

    try:
        transport = TushareSdkTransport(token=credential)
        return TushareClient(transport=transport, token=credential), None
    except TushareSdkTransportError as exc:
        if exc.code == "sdk_unavailable":
            return None, "provider_sdk_unavailable"
        return None, "provider_sdk_initialization_failed"


def _empty_result(
    *,
    ts_code: str | None,
    periods: list[str],
    company_name_hint: str | None,
) -> dict[str, Any]:
    stock_code = ts_code.split(".", 1)[0] if isinstance(ts_code, str) and "." in ts_code else None
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "provider": PROVIDER_NAME,
        "ts_code": ts_code,
        "stock_code": stock_code,
        "company_name_hint": company_name_hint,
        "periods": periods,
        "income_rows": [],
        "balancesheet_rows": [],
        "cashflow_rows": [],
        "fina_indicator_rows": [],
        "trend_table": [],
        "missing_tables": [],
        "blocked_reasons": [],
        "caveats": [],
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }


def _blocked_result(
    *,
    ts_code: str | None,
    periods: list[str],
    company_name_hint: str | None,
    blocked_reasons: list[str],
) -> dict[str, Any]:
    result = _empty_result(ts_code=ts_code, periods=periods, company_name_hint=company_name_hint)
    result["blocked_reasons"] = blocked_reasons
    validate_provider_candidate_financial_result(result)
    return result


def _normalize_table_rows(response: Any, *, table_name: str, ts_code: str, period: str) -> list[dict[str, Any]]:
    normalized, _ = _normalize_table_rows_with_rejections(
        response,
        table_name=table_name,
        ts_code=ts_code,
        period=period,
    )
    return normalized


def _normalize_table_rows_with_rejections(
    response: Any,
    *,
    table_name: str,
    ts_code: str,
    period: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    normalized = []
    rejected_reasons = []
    for raw_row in _records(response):
        row = dict(raw_row)
        rejection_reason = _row_identity_rejection_reason(row, ts_code=ts_code, period=period)
        if rejection_reason is not None:
            rejected_reasons.append(rejection_reason)
            continue

        row_ts_code = _identity_value(_first_present(row, ("ts_code",)))
        row_period = _identity_value(_first_present(row, ("period", "end_date")))
        selected_fields = {
            field: _first_present(row, (field,))
            for field in TABLE_SELECTED_FIELDS[table_name]
        }
        normalized.append(
            {
                "provider": PROVIDER_NAME,
                "table_name": table_name,
                "ts_code": row_ts_code,
                "period": row_period,
                "ann_date": _first_present(row, ("ann_date",)),
                "end_date": _first_present(row, ("end_date", "period")),
                "original_fields": row,
                "selected_fields": selected_fields,
                "not_official_verified": True,
                "not_for_trading_advice": True,
            }
        )
    return normalized, rejected_reasons


def _row_identity_rejection_reason(row: Mapping[str, Any], *, ts_code: str, period: str) -> str | None:
    row_ts_code = _identity_value(_first_present(row, ("ts_code",)))
    if row_ts_code is None:
        return "row_missing_ts_code"
    if row_ts_code != ts_code:
        return "row_ts_code_mismatch"

    row_period = _identity_value(_first_present(row, ("period",)))
    row_end_date = _identity_value(_first_present(row, ("end_date",)))
    if row_period is None and row_end_date is None:
        return "row_missing_period"
    if row_period is not None and row_period != period:
        return "row_period_mismatch"
    if row_end_date is not None and row_end_date != period:
        return "row_period_mismatch"
    return None


def _records(response: Any) -> list[dict[str, Any]]:
    if response is None:
        return []
    if isinstance(response, Mapping):
        if "items" in response and "fields" in response:
            fields = response.get("fields")
            items = response.get("items")
            if not isinstance(fields, list) or not isinstance(items, list):
                raise ValueError("malformed_response")
            return [dict(zip(fields, item, strict=False)) for item in items if isinstance(item, (list, tuple))]
        return [dict(response)]
    if isinstance(response, list):
        if not response:
            return []
        if all(isinstance(item, Mapping) for item in response):
            return [dict(item) for item in response]
        raise ValueError("malformed_response")
    if hasattr(response, "to_dict"):
        try:
            rows = response.to_dict(orient="records")
        except TypeError:
            rows = response.to_dict()
        if isinstance(rows, list) and all(isinstance(item, Mapping) for item in rows):
            return [dict(item) for item in rows]
    raise ValueError("malformed_response")


def _periods_with_multiple_rows(rows: list[dict[str, Any]]) -> list[str]:
    counts: dict[str, int] = {}
    for row in rows:
        period = row.get("period")
        if isinstance(period, str):
            counts[period] = counts.get(period, 0) + 1
    return [period for period, count in counts.items() if count > 1]


def _selected_row_by_period(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_period: dict[str, dict[str, Any]] = {}
    for row in rows:
        period = row.get("period")
        if not isinstance(period, str):
            continue
        current = by_period.get(period)
        if current is None or _ann_date_rank(row) > _ann_date_rank(current):
            by_period[period] = row
    return by_period


def _ann_date_rank(row: Mapping[str, Any]) -> str:
    return _identity_value(row.get("ann_date")) or ""


def _identity_value(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value).strip() or None


def _first_present(row: Mapping[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    lower = {str(key).lower(): value for key, value in row.items()}
    for key in keys:
        value = lower.get(key.lower())
        if value not in (None, ""):
            return value
    return None


def _missing_table(table_name: str, period: str, reason: str) -> dict[str, str]:
    return {"provider": PROVIDER_NAME, "table_name": table_name, "period": period, "reason": reason}


def _record_rejected_provider_row(
    fetched: dict[str, Any],
    *,
    table_name: str,
    period: str,
    reason: str,
) -> None:
    fetched["missing_tables"].append(_missing_table(table_name, period, reason))
    fetched["blocked_reasons"].append(f"{reason}:{table_name}:{period}")
    fetched["caveats"].append(f"{table_name} rejected provider row for period {period}: {reason}")


def _record_multiple_provider_rows(fetched: dict[str, Any], *, table_name: str, period: str) -> None:
    reason = f"multiple_provider_rows:{table_name}:{period}"
    _append_once(fetched["blocked_reasons"], reason)
    _append_once(fetched["caveats"], reason)


def _append_once(values: list[Any], value: Any) -> None:
    if value not in values:
        values.append(value)


def _validate_candidate_row(row: Any, path: str) -> None:
    if not isinstance(row, Mapping):
        raise TushareFinancialProviderCandidateError("invalid_row")
    required = (
        "provider",
        "table_name",
        "ts_code",
        "period",
        "ann_date",
        "end_date",
        "original_fields",
        "selected_fields",
    )
    if any(key not in row for key in required):
        raise TushareFinancialProviderCandidateError("missing_row_field")
    if row.get("provider") != PROVIDER_NAME:
        raise TushareFinancialProviderCandidateError("invalid_row_provider")
    if row.get("table_name") not in TARGET_TABLES:
        raise TushareFinancialProviderCandidateError("invalid_row_table")
    _require_true_bool(row, "not_official_verified", path)
    _require_true_bool(row, "not_for_trading_advice", path)


def _require_true_bool(payload: Mapping[str, Any], key: str, path: str) -> None:
    if key not in payload:
        raise TushareFinancialProviderCandidateError(f"{path}:{key}_missing")
    if payload.get(key) is not True:
        raise TushareFinancialProviderCandidateError(f"{path}:{key}_must_be_true")


def _find_forbidden_marker(payload: Any) -> str | None:
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            key_text = str(key)
            if key_text not in ALLOWED_EXACT_KEYS and _text_has_forbidden_marker(key_text):
                return key_text
            finding = _find_forbidden_marker(value)
            if finding is not None:
                return finding
        return None
    if isinstance(payload, (list, tuple, set)):
        for item in payload:
            finding = _find_forbidden_marker(item)
            if finding is not None:
                return finding
        return None
    if isinstance(payload, str) and _text_has_forbidden_marker(payload):
        return payload
    return None


def _text_has_forbidden_marker(value: str) -> bool:
    normalized = _normalize_marker_text(value)
    separator_normalized = _normalize_marker_text(re.sub(r"[_-]+", " ", value))
    for marker in FORBIDDEN_MARKERS:
        marker_text = _normalize_marker_text(marker)
        if marker_text in _WORD_MARKERS:
            boundary_chars = "a-z0-9_" if marker_text in _IDENTIFIER_SAFE_WORD_MARKERS else "a-z0-9"
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
