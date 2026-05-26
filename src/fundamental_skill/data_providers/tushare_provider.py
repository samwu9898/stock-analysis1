# -*- coding: utf-8 -*-
"""Mocked-only Tushare provider MVP for Phase 3.

The provider maps injected Tushare-like mocked responses into the existing
canonical raw JSON structure. It does not import real provider SDKs, read
credentials, read local tool config, or perform external I/O.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Callable

from .schemas import CANONICAL_RAW_BLOCKS, ProviderCapabilities
from .token_safety import mask_secret, sanitize_exception_message, sanitize_text
from .tushare_client import (
    TushareClient,
    TushareClientError,
    TushareMalformedResponseError,
)


TUSHARE_PROVIDER_VERSION = "tushare_provider.phase3_mocked_mvp"
SH_TS_CODE_PREFIXES = ("600", "601", "603", "605", "688", "689")
SZ_TS_CODE_PREFIXES = ("000", "001", "002", "003", "300", "301")


class TushareProviderError(RuntimeError):
    """Sanitized provider failure."""

    def __init__(self, message: object, *, secrets: tuple[str | None, ...] = ()) -> None:
        super().__init__(sanitize_text(message, secrets=secrets))


class TushareProvider:
    """DataProvider implementation backed by an injected mocked client."""

    name = "tushare"

    def __init__(
        self,
        client: TushareClient | None = None,
        *,
        client_factory: Callable[[], TushareClient] | None = None,
        token: str | None = None,
        token_available: bool = False,
        require_token: bool = True,
    ) -> None:
        self._client = client
        self._client_factory = client_factory
        self._token = token
        self._token_available = bool(token_available or token)
        self._require_token = require_token
        self._token_display = mask_secret(token) if token is not None else mask_secret(None)

    def __repr__(self) -> str:
        return (
            f"TushareProvider(name={self.name!r}, client_injected={self._client is not None}, "
            f"token={self._token_display!r})"
        )

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider_name=self.name,
            raw_blocks=CANONICAL_RAW_BLOCKS,
            basic_info=True,
            financial_indicator=True,
            valuation=True,
            business_composition=True,
            news=False,
            commodity_prices=False,
            low_frequency_market_data=True,
            realtime_market_data=False,
            notes=("phase3_mocked_only", "news_missing_fallback", "commodity_prices_not_replaced"),
        )

    def fetch_to_raw_json(self, stock_code: str, *, force_refresh: bool = False) -> dict[str, Any]:
        del force_refresh
        self._require_token_ready()

        code = _normalize_code(stock_code)
        ts_code = normalize_ts_code(code)
        raw = self._empty_raw(code, ts_code)
        client = self._get_client()

        block_builders: dict[
            str,
            Callable[[TushareClient, str, str], tuple[list[dict[str, Any]], list[dict[str, Any]]]],
        ] = {
            "basic_info": self._fetch_basic_info,
            "financial_indicator": self._fetch_financial_indicator,
            "valuation": self._fetch_valuation,
            "business_composition": self._fetch_business_composition,
        }
        for block_name, builder in block_builders.items():
            try:
                rows, source_trace = builder(client, code, ts_code)
                raw["blocks"][block_name] = rows
                missing = self._missing_fields_for_block(block_name, rows)
                raw["fetch_status"][block_name] = self._status(
                    block_name,
                    success=bool(rows),
                    error=None if rows else "empty_response",
                    missing_fields=missing,
                    fetched_at=raw["meta"]["generated_at"],
                    source_trace=source_trace,
                    warnings=[] if rows else [f"{block_name} returned no mocked rows"],
                    ts_code=ts_code,
                    row_count=len(rows),
                    endpoints=_endpoints_from_trace(source_trace),
                )
                if not rows:
                    raw["errors"].append(f"{block_name}: empty_response")
            except TushareClientError as exc:
                error_text = self._error_text(exc)
                raw["blocks"][block_name] = []
                raw["fetch_status"][block_name] = self._status(
                    block_name,
                    success=False,
                    error=error_text,
                    missing_fields=self._expected_fields(block_name),
                    fetched_at=raw["meta"]["generated_at"],
                    source_trace=[self._source_trace_for_error(block_name, ts_code, exc)],
                    warnings=[],
                    ts_code=ts_code,
                    row_count=0,
                    endpoints=[_endpoint_for_error(block_name, exc)],
                )
                raw["errors"].append(f"{block_name}: {error_text}")

        raw["blocks"]["news"] = []
        raw["fetch_status"]["news"] = self._status(
            "news",
            success=False,
            error="news_missing_fallback",
            missing_fields=self._expected_fields("news"),
            fetched_at=raw["meta"]["generated_at"],
            source_trace=[],
            warnings=["TushareProvider Phase 3 MVP does not replace news; use future news provider fallback"],
            ts_code=ts_code,
            row_count=0,
            endpoints=[],
        )
        raw["errors"].append("news: news_missing_fallback")

        raw["meta"]["stock_name"] = _first_value(raw["blocks"]["basic_info"], "stock_name")
        raw["meta"]["data_cutoff"] = _first_value(raw["blocks"]["financial_indicator"], "period")
        return raw

    def _require_token_ready(self) -> None:
        if self._require_token and not self._token_available:
            raise TushareProviderError("provider=tushare requires an available Tushare token", secrets=(self._token,))

    def _get_client(self) -> TushareClient:
        if self._client is not None:
            return self._client
        if self._client_factory is not None:
            self._client = self._client_factory()
            return self._client
        raise TushareProviderError("TushareProvider Phase 3 requires an injected mocked TushareClient", secrets=(self._token,))

    def _fetch_basic_info(self, client: TushareClient, code: str, ts_code: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        rows = _records(client.stock_basic(ts_code=ts_code), endpoint="stock_basic")
        row = rows[0] if rows else {}
        source_trace = [self._source_trace_for_endpoint("basic_info", "stock_basic", ts_code, rows)]
        if not row:
            return [], source_trace
        mapped = [
            {
                "stock_code": _canonical_code_from_row(row, fallback=code),
                "stock_name": _first_present(row, ("stock_name", "name")),
                "industry": _first_present(row, ("industry", "classi_name")),
                "main_business": _first_present(row, ("main_business", "business_scope", "operating_scope")),
                "listing_date": _first_present(row, ("listing_date", "list_date")),
            }
        ]
        source_trace.extend(self._source_trace_for_rows("basic_info", mapped))
        return mapped, source_trace

    def _fetch_financial_indicator(
        self, client: TushareClient, code: str, ts_code: str
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        del code
        income_rows = _records(client.income(ts_code=ts_code), endpoint="income")
        balance_rows = _records(client.balancesheet(ts_code=ts_code), endpoint="balancesheet")
        cashflow_rows = _records(client.cashflow(ts_code=ts_code), endpoint="cashflow")
        indicator_rows = _records(client.fina_indicator(ts_code=ts_code), endpoint="fina_indicator")
        source_trace = [
            self._source_trace_for_endpoint("financial_indicator", "income", ts_code, income_rows),
            self._source_trace_for_endpoint("financial_indicator", "balancesheet", ts_code, balance_rows),
            self._source_trace_for_endpoint("financial_indicator", "cashflow", ts_code, cashflow_rows),
            self._source_trace_for_endpoint("financial_indicator", "fina_indicator", ts_code, indicator_rows),
        ]
        income = income_rows[0] if income_rows else {}
        balance = balance_rows[0] if balance_rows else {}
        cashflow = cashflow_rows[0] if cashflow_rows else {}
        indicator = indicator_rows[0] if indicator_rows else {}
        if not any((income, balance, cashflow, indicator)):
            return [], source_trace

        metric: dict[str, Any] = {
            "period": _first_present(income, ("period", "end_date", "ann_date"))
            or _first_present(indicator, ("period", "end_date", "ann_date"))
            or _first_present(balance, ("period", "end_date", "ann_date"))
            or _first_present(cashflow, ("period", "end_date", "ann_date")),
        }
        field_trace: dict[str, dict[str, Any]] = {}

        def map_from_sources(
            field_name: str,
            sources: tuple[tuple[dict[str, Any], str, tuple[str, ...]], ...],
        ) -> float | None:
            for source_row, source_function, keys in sources:
                value, source_field = _float_from_row(source_row, keys)
                if value is not None:
                    metric[field_name] = value
                    field_trace[field_name] = _field_trace(
                        source_function=source_function,
                        source_field=source_field,
                    )
                    return value
            metric[field_name] = None
            return None

        def map_percentage_from_sources(
            field_name: str,
            sources: tuple[tuple[dict[str, Any], str, tuple[str, ...], tuple[str, ...]], ...],
        ) -> float | None:
            for source_row, source_function, trusted_keys, fallback_keys in sources:
                value, source_field = _percentage_from_row(source_row, trusted_keys, fallback_keys=fallback_keys)
                if value is not None:
                    metric[field_name] = value
                    field_trace[field_name] = _field_trace(
                        source_function=source_function,
                        source_field=source_field,
                        canonical_unit="%",
                    )
                    return value
            metric[field_name] = None
            return None

        map_from_sources("revenue", ((income, "income", ("revenue", "total_revenue")),))
        map_from_sources("net_profit", ((income, "income", ("net_profit", "n_income_attr_p", "n_income")),))
        map_from_sources(
            "deducted_net_profit",
            (
                (indicator, "fina_indicator", ("deducted_net_profit", "profit_dedt", "dt_net_profit")),
                (income, "income", ("deducted_net_profit", "profit_dedt", "dt_net_profit")),
            ),
        )
        map_from_sources("r_and_d_expense", ((income, "income", ("r_and_d_expense", "rd_exp")),))
        map_from_sources("inventory", ((balance, "balancesheet", ("inventory", "inventories")),))
        map_from_sources(
            "accounts_receivable",
            (
                (
                    balance,
                    "balancesheet",
                    (
                        "accounts_receivable",
                        "accounts_receiv",
                        "accounts_recv",
                        "acct_receiv",
                        "acct_rcv",
                        "notes_receiv",
                    ),
                ),
            ),
        )
        map_from_sources(
            "contract_liabilities",
            ((balance, "balancesheet", ("contract_liabilities", "contract_liab", "contract_liabilities_current")),),
        )
        map_from_sources("operating_cashflow", ((cashflow, "cashflow", ("operating_cashflow", "n_cashflow_act")),))
        map_from_sources(
            "capex",
            (
                (
                    cashflow,
                    "cashflow",
                    (
                        "capex",
                        "c_pay_acq_const_fiolta",
                        "cash_pay_acq_const_fiolta",
                        "purchase_fixed_assets",
                    ),
                ),
            ),
        )
        map_from_sources("revenue_yoy", ((indicator, "fina_indicator", ("revenue_yoy", "or_yoy")),))
        map_from_sources("net_profit_yoy", ((indicator, "fina_indicator", ("net_profit_yoy", "netprofit_yoy")),))
        map_percentage_from_sources(
            "gross_margin",
            (
                (
                    indicator,
                    "fina_indicator",
                    ("grossprofit_margin", "gross_profit_margin", "gross_profit_rate", "sales_grossprofit_margin"),
                    ("gross_margin",),
                ),
            ),
        )
        map_percentage_from_sources(
            "net_margin",
            (
                (
                    indicator,
                    "fina_indicator",
                    ("netprofit_margin", "net_profit_margin", "net_profit_rate", "sales_netprofit_margin"),
                    ("net_margin",),
                ),
            ),
        )
        map_from_sources("roe", ((indicator, "fina_indicator", ("roe", "roe_weighted", "roe_waa")),))
        map_from_sources(
            "debt_to_asset",
            (
                (indicator, "fina_indicator", ("debt_to_asset", "debt_to_assets", "assets_liab_ratio")),
                (balance, "balancesheet", ("debt_to_asset", "debt_to_assets", "assets_liab_ratio")),
            ),
        )
        map_from_sources(
            "r_and_d_expense_ratio",
            (
                (
                    indicator,
                    "fina_indicator",
                    ("r_and_d_expense_ratio", "rd_exp_ratio", "rd_exp_to_revenue", "rd_exp_to_revenue_pct"),
                ),
            ),
        )

        revenue = metric.get("revenue")
        if metric.get("gross_margin") is None:
            cost, cost_field = _float_from_row(
                income,
                ("cost", "oper_cost", "operating_cost", "total_oper_cost", "total_cogs", "biz_cost"),
            )
            derived = _ratio_percentage(None if revenue is None or cost is None else revenue - cost, revenue)
            if derived is not None:
                metric["gross_margin"] = derived
                field_trace["gross_margin"] = _field_trace(
                    source_function="income",
                    derived=True,
                    derivation_method="(revenue - cost) / revenue * 100",
                    source_fields=_source_field_refs(
                        ("income", field_trace.get("revenue", {}).get("source_field")),
                        ("income", cost_field),
                    ),
                    canonical_unit="%",
                )
        if metric.get("net_margin") is None:
            derived = _ratio_percentage(metric.get("net_profit"), revenue)
            if derived is not None:
                metric["net_margin"] = derived
                field_trace["net_margin"] = _field_trace(
                    source_function="income",
                    derived=True,
                    derivation_method="net_profit / revenue * 100",
                    source_fields=_source_field_refs(
                        ("income", field_trace.get("net_profit", {}).get("source_field")),
                        ("income", field_trace.get("revenue", {}).get("source_field")),
                    ),
                    canonical_unit="%",
                )
        if metric.get("debt_to_asset") is None:
            total_liab, total_liab_field = _float_from_row(balance, ("total_liab", "total_liability", "total_liabilities"))
            total_assets, total_assets_field = _float_from_row(balance, ("total_assets", "total_asset"))
            derived = _ratio_percentage(total_liab, total_assets)
            if derived is not None:
                metric["debt_to_asset"] = derived
                field_trace["debt_to_asset"] = _field_trace(
                    source_function="balancesheet",
                    derived=True,
                    derivation_method="total_liab / total_assets * 100",
                    source_fields=_source_field_refs(
                        ("balancesheet", total_liab_field),
                        ("balancesheet", total_assets_field),
                    ),
                    canonical_unit="%",
                )
        if metric.get("r_and_d_expense_ratio") is None:
            derived = _ratio_percentage(metric.get("r_and_d_expense"), revenue)
            if derived is not None:
                metric["r_and_d_expense_ratio"] = derived
                field_trace["r_and_d_expense_ratio"] = _field_trace(
                    source_function="income",
                    derived=True,
                    derivation_method="r_and_d_expense / revenue * 100",
                    source_fields=_source_field_refs(
                        ("income", field_trace.get("r_and_d_expense", {}).get("source_field")),
                        ("income", field_trace.get("revenue", {}).get("source_field")),
                    ),
                    canonical_unit="%",
                )

        source_trace.extend(self._source_trace_for_rows("financial_indicator", [metric], [field_trace]))
        return [metric], source_trace

    def _fetch_valuation(self, client: TushareClient, code: str, ts_code: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        del code
        rows = _records(client.daily_basic(ts_code=ts_code), endpoint="daily_basic")
        row = rows[0] if rows else {}
        source_trace = [self._source_trace_for_endpoint("valuation", "daily_basic", ts_code, rows)]
        if not row:
            return [], source_trace
        mapped_row: dict[str, Any] = {"period": _first_present(row, ("period", "trade_date"))}
        field_trace: dict[str, dict[str, Any]] = {}
        for field_name, keys in {
            "pe_ttm": ("pe_ttm",),
            "pb": ("pb",),
            "ps": ("ps_ttm", "ps"),
            "dividend_yield": ("dividend_yield", "dv_ttm"),
        }.items():
            value, source_field = _float_from_row(row, keys)
            mapped_row[field_name] = value
            if value is not None:
                field_trace[field_name] = _field_trace(
                    source_function="daily_basic",
                    source_field=source_field,
                    canonical_unit="ratio",
                )

        market_cap, source_field = _float_from_row(row, ("market_cap",))
        if market_cap is not None:
            mapped_row["market_cap"] = market_cap
            field_trace["market_cap"] = _field_trace(
                source_function="daily_basic",
                source_field=source_field,
                canonical_unit="RMB",
            )
        else:
            market_cap_10k, source_field = _float_from_row(row, ("total_mv", "circ_mv"))
            mapped_row["market_cap"] = market_cap_10k * 10000 if market_cap_10k is not None else None
            if market_cap_10k is not None:
                field_trace["market_cap"] = _field_trace(
                    source_function="daily_basic",
                    source_field=source_field,
                    source_unit="10k RMB",
                    canonical_unit="RMB",
                    multiplier=10000,
                )

        mapped = [mapped_row]
        source_trace.extend(self._source_trace_for_rows("valuation", mapped, [field_trace]))
        return mapped, source_trace

    def _fetch_business_composition(
        self, client: TushareClient, code: str, ts_code: str
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        del code
        rows = _records(client.fina_mainbz(ts_code=ts_code), endpoint="fina_mainbz")
        source_trace = [self._source_trace_for_endpoint("business_composition", "fina_mainbz", ts_code, rows)]
        segments = []
        trace_metadata: list[dict[str, dict[str, Any]]] = []
        for row in rows:
            segment: dict[str, Any] = {"period": _first_present(row, ("period", "end_date"))}
            field_trace: dict[str, dict[str, Any]] = {}
            classification_value, classification_field = _first_present_with_key(
                row, ("classification_type", "bz_type", "type", "class_type", "category_type")
            )
            segment["classification_type"] = _normalize_classification_type(classification_value)
            if segment["classification_type"] is not None:
                field_trace["classification_type"] = _field_trace(
                    source_function="fina_mainbz",
                    source_field=classification_field,
                )

            name_value, name_field = _first_present_with_key(row, ("segment_name", "bz_item", "name"))
            segment["segment_name"] = name_value
            if name_value is not None:
                field_trace["segment_name"] = _field_trace(source_function="fina_mainbz", source_field=name_field)

            for field_name, keys in {
                "revenue": ("revenue", "bz_sales", "sales"),
                "cost": ("cost", "bz_cost"),
                "profit": ("profit", "bz_profit", "gross_profit"),
                "revenue_ratio": ("revenue_ratio", "bz_sales_ratio", "sales_ratio"),
                "profit_ratio": ("profit_ratio", "bz_profit_ratio"),
            }.items():
                value, source_field = _float_from_row(row, keys)
                segment[field_name] = value
                if value is not None:
                    field_trace[field_name] = _field_trace(source_function="fina_mainbz", source_field=source_field)

            gross_margin, gross_margin_field = _percentage_from_row(
                row,
                ("bz_grossprofit_margin", "grossprofit_margin", "gross_profit_margin"),
                fallback_keys=("gross_margin",),
            )
            segment["gross_margin"] = gross_margin
            if gross_margin is not None:
                field_trace["gross_margin"] = _field_trace(
                    source_function="fina_mainbz",
                    source_field=gross_margin_field,
                    canonical_unit="%",
                )
            segments.append(segment)
            trace_metadata.append(field_trace)

        _derive_business_composition_fields(segments, trace_metadata)
        source_trace.extend(self._source_trace_for_rows("business_composition", segments, trace_metadata))
        return segments, source_trace

    def _status(
        self,
        block_name: str,
        *,
        success: bool,
        error: str | None,
        missing_fields: list[str],
        fetched_at: str,
        source_trace: list[dict[str, Any]],
        warnings: list[str],
        ts_code: str | None = None,
        row_count: int | None = None,
        endpoints: list[str] | None = None,
    ) -> dict[str, Any]:
        return {
            "success": success,
            "error": sanitize_text(error, secrets=(self._token,)) if error else None,
            "missing_fields": missing_fields,
            "missing_reasons": {
                field: _missing_reason(success=success, error=error) for field in missing_fields
            },
            "fetched_at": fetched_at,
            "source_name": self.name,
            "endpoints": endpoints or [],
            "ts_code": ts_code,
            "row_count": row_count,
            "source_trace": source_trace,
            "warnings": [sanitize_text(warning, secrets=(self._token,)) for warning in warnings],
        }

    def _source_trace_for_endpoint(
        self,
        block_name: str,
        endpoint: str,
        ts_code: str,
        rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        selected_row = rows[0] if rows else {}
        selected_period = _first_present(selected_row, ("period", "end_date", "trade_date"))
        selected_ann_date = _first_present(selected_row, ("ann_date",))
        selected_trade_date = _first_present(selected_row, ("trade_date",))
        return {
            "field_name": "__endpoint_call__",
            "block_name": block_name,
            "function_name": endpoint,
            "source_function": endpoint,
            "endpoint": endpoint,
            "ts_code": ts_code,
            "row_count": len(rows),
            "request_period": "omitted",
            "request_start_date": "omitted",
            "request_end_date": "omitted",
            "request_trade_date": "omitted",
            "selected_row_period": selected_period or "missing",
            "selected_row_ann_date": selected_ann_date or "missing",
            "selected_row_trade_date": selected_trade_date or "missing",
            "source_period": selected_period,
            "value": len(rows),
            "derived": False,
            "derivation_method": None,
        }

    def _source_trace_for_error(self, block_name: str, ts_code: str, exc: TushareClientError) -> dict[str, Any]:
        endpoint = _endpoint_for_error(block_name, exc)
        return {
            "field_name": "__endpoint_call__",
            "block_name": block_name,
            "function_name": endpoint,
            "source_function": endpoint,
            "endpoint": endpoint,
            "ts_code": ts_code,
            "row_count": 0,
            "request_period": "omitted",
            "request_start_date": "omitted",
            "request_end_date": "omitted",
            "request_trade_date": "omitted",
            "selected_row_period": "missing",
            "selected_row_ann_date": "missing",
            "selected_row_trade_date": "missing",
            "source_period": None,
            "value": None,
            "derived": False,
            "derivation_method": None,
        }

    def _source_trace_for_rows(
        self,
        block_name: str,
        rows: list[dict[str, Any]],
        field_trace_metadata: list[dict[str, dict[str, Any]]] | None = None,
    ) -> list[dict[str, Any]]:
        traces = []
        default_endpoint = {
            "basic_info": "stock_basic",
            "valuation": "daily_basic",
            "business_composition": "fina_mainbz",
        }.get(block_name, "financial_statements_and_indicators")
        field_trace_metadata = field_trace_metadata or [{} for _ in rows]
        for row_index, row in enumerate(rows):
            metadata_by_field = field_trace_metadata[row_index] if row_index < len(field_trace_metadata) else {}
            for field_name, value in row.items():
                if value in (None, ""):
                    continue
                metadata = metadata_by_field.get(field_name, {})
                endpoint = metadata.get("source_function") or default_endpoint
                trace = {
                    "field_name": field_name,
                    "block_name": block_name,
                    "function_name": endpoint,
                    "source_function": endpoint,
                    "source_period": row.get("period") or row.get("listing_date"),
                    "value": sanitize_text(value, secrets=(self._token,)) if isinstance(value, str) else value,
                    "derived": bool(metadata.get("derived", False)),
                    "derivation_method": metadata.get("derivation_method"),
                }
                for key in (
                    "source_field",
                    "source_fields",
                    "source_unit",
                    "canonical_unit",
                    "multiplier",
                    "denominator_scope",
                ):
                    if metadata.get(key) is not None:
                        trace[key] = metadata[key]
                traces.append(
                    trace
                )
        return traces

    def _missing_fields_for_block(self, block_name: str, rows: list[dict[str, Any]]) -> list[str]:
        if not rows:
            if block_name == "business_composition":
                return ["business_composition.segments"]
            return self._expected_fields(block_name)
        missing = []
        for field in self._expected_fields(block_name):
            if all(row.get(field) in (None, "") for row in rows):
                missing.append(field)
        return missing

    def _expected_fields(self, block_name: str) -> list[str]:
        return {
            "basic_info": ["stock_code", "stock_name", "industry", "main_business", "listing_date"],
            "financial_indicator": [
                "period",
                "revenue",
                "revenue_yoy",
                "net_profit",
                "net_profit_yoy",
                "deducted_net_profit",
                "gross_margin",
                "net_margin",
                "roe",
                "operating_cashflow",
                "debt_to_asset",
                "inventory",
                "accounts_receivable",
                "contract_liabilities",
                "r_and_d_expense",
                "r_and_d_expense_ratio",
                "capex",
            ],
            "valuation": ["pe_ttm", "pb", "ps", "market_cap", "dividend_yield"],
            "business_composition": [
                "period",
                "classification_type",
                "segment_name",
                "revenue",
                "revenue_ratio",
                "gross_margin",
                "cost",
                "profit",
                "profit_ratio",
            ],
            "news": ["title", "publish_time", "source", "url", "summary"],
        }.get(block_name, [])

    def _error_text(self, exc: TushareClientError) -> str:
        message = sanitize_exception_message(exc, secrets=(self._token,))
        return f"{exc.code}: {message}" if exc.code not in message else message

    def _empty_raw(self, code: str, ts_code: str) -> dict[str, Any]:
        generated_at = _now_iso()
        return {
            "meta": {
                "code": code,
                "ts_code": ts_code,
                "generated_at": generated_at,
                "data_source": self.name,
                "connector_version": TUSHARE_PROVIDER_VERSION,
                "cache_hit": False,
            },
            "blocks": {name: [] for name in CANONICAL_RAW_BLOCKS},
            "fetch_status": {
                name: {
                    "success": False,
                    "error": "not_fetched",
                    "missing_fields": self._expected_fields(name),
                    "source_name": self.name,
                    "source_trace": [],
                    "warnings": [],
                }
                for name in CANONICAL_RAW_BLOCKS
            },
            "errors": [],
        }


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def normalize_ts_code(code: str) -> str:
    """Return the strict Tushare ``ts_code`` for a supported 6 digit A-share code."""

    text = str(code)
    if len(text) != 6 or not text.isdigit():
        raise TushareProviderError("stock_code must be a strict 6 digit A-share code")
    if text.startswith(SH_TS_CODE_PREFIXES):
        return f"{text}.SH"
    if text.startswith(SZ_TS_CODE_PREFIXES):
        return f"{text}.SZ"
    if text.startswith("9"):
        return f"{text}.BJ"
    raise TushareProviderError("stock_code has unsupported A-share exchange prefix")


def _normalize_code(stock_code: str) -> str:
    ts_code = normalize_ts_code(stock_code)
    return ts_code.split(".", 1)[0]


def _canonical_code_from_row(row: dict[str, Any], *, fallback: str) -> str:
    value = _first_present(row, ("stock_code", "symbol", "code", "ts_code"))
    if value is None:
        return fallback
    text = str(value).strip()
    if len(text) >= 6 and text[:6].isdigit():
        return text[:6]
    return fallback


def _safe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return None
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "").replace("%", "")
        if cleaned in {"", "--", "None", "none", "null", "nan", "NaN"}:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _first_present_with_key(row: dict[str, Any], keys: tuple[str, ...]) -> tuple[Any, str | None]:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key], key
    lower = {str(key).lower(): (str(key), value) for key, value in row.items()}
    for key in keys:
        found = lower.get(key.lower())
        if found is None:
            continue
        actual_key, value = found
        if value not in (None, ""):
            return value, actual_key
    return None, None


def _float_from_row(row: dict[str, Any], keys: tuple[str, ...]) -> tuple[float | None, str | None]:
    value, source_field = _first_present_with_key(row, keys)
    float_value = _safe_float(value)
    if float_value is None or not math.isfinite(float_value):
        return None, None
    return float_value, source_field


def _looks_like_percentage(value: float | None) -> bool:
    return value is not None and math.isfinite(value) and -100.0 <= value <= 100.0


def _percentage_from_row(
    row: dict[str, Any],
    trusted_keys: tuple[str, ...],
    *,
    fallback_keys: tuple[str, ...] = (),
) -> tuple[float | None, str | None]:
    for key in trusted_keys:
        value, source_field = _float_from_row(row, (key,))
        if value is not None:
            return value, source_field
    for key in fallback_keys:
        value, source_field = _float_from_row(row, (key,))
        if _looks_like_percentage(value):
            return value, source_field
    return None, None


def _ratio_percentage(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    if not math.isfinite(numerator) or not math.isfinite(denominator):
        return None
    value = numerator / denominator * 100
    return value if math.isfinite(value) else None


def _field_trace(
    *,
    source_function: str,
    source_field: str | None = None,
    source_fields: list[str] | None = None,
    source_unit: str | None = None,
    canonical_unit: str | None = None,
    multiplier: float | int | None = None,
    derived: bool = False,
    derivation_method: str | None = None,
    denominator_scope: str | None = None,
) -> dict[str, Any]:
    return {
        "source_function": source_function,
        "source_field": source_field,
        "source_fields": source_fields,
        "source_unit": source_unit,
        "canonical_unit": canonical_unit,
        "multiplier": multiplier,
        "derived": derived,
        "derivation_method": derivation_method,
        "denominator_scope": denominator_scope,
    }


def _source_field_refs(*refs: tuple[str, Any]) -> list[str]:
    out = []
    for source_function, source_field in refs:
        if source_field:
            out.append(f"{source_function}.{source_field}")
    return out


def _normalize_classification_type(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    normalized = text.lower()
    mapping = {
        "p": "product",
        "product": "product",
        "products": "product",
        "by_product": "product",
        "d": "region",
        "area": "region",
        "region": "region",
        "district": "region",
        "geography": "region",
        "i": "industry",
        "industry": "industry",
        "industries": "industry",
    }
    return mapping.get(normalized, text)


def _missing_reason(*, success: bool, error: str | None) -> str:
    if not success:
        return error or "not_fetched"
    return "not_available_or_not_reliably_derivable"


def _derive_business_composition_fields(
    segments: list[dict[str, Any]],
    trace_metadata: list[dict[str, dict[str, Any]]],
) -> None:
    grouped_indexes: dict[tuple[str, str], list[int]] = {}
    for index, segment in enumerate(segments):
        period = segment.get("period")
        classification_type = segment.get("classification_type")
        if period in (None, "") or classification_type in (None, ""):
            continue
        grouped_indexes.setdefault((str(period), str(classification_type)), []).append(index)

    for index, segment in enumerate(segments):
        if segment.get("gross_margin") is not None:
            continue
        gross_margin = _ratio_percentage(segment.get("profit"), segment.get("revenue"))
        if gross_margin is None:
            continue
        segment["gross_margin"] = gross_margin
        trace_metadata[index]["gross_margin"] = _field_trace(
            source_function="fina_mainbz",
            derived=True,
            derivation_method="profit / revenue * 100",
            source_fields=_source_field_refs(
                ("fina_mainbz", trace_metadata[index].get("profit", {}).get("source_field")),
                ("fina_mainbz", trace_metadata[index].get("revenue", {}).get("source_field")),
            ),
            canonical_unit="%",
            denominator_scope="segment revenue",
        )

    for (period, classification_type), indexes in grouped_indexes.items():
        total_revenue = sum(
            segment["revenue"]
            for segment in (segments[index] for index in indexes)
            if isinstance(segment.get("revenue"), (int, float)) and math.isfinite(segment["revenue"])
        )
        total_profit = sum(
            segment["profit"]
            for segment in (segments[index] for index in indexes)
            if isinstance(segment.get("profit"), (int, float)) and math.isfinite(segment["profit"])
        )
        revenue_scope = f"period={period};classification_type={classification_type};denominator=sum(revenue)"
        profit_scope = f"period={period};classification_type={classification_type};denominator=sum(profit)"
        for index in indexes:
            segment = segments[index]
            if segment.get("revenue_ratio") is None and total_revenue > 0:
                revenue_ratio = _ratio_percentage(segment.get("revenue"), total_revenue)
                if revenue_ratio is not None:
                    segment["revenue_ratio"] = revenue_ratio
                    trace_metadata[index]["revenue_ratio"] = _field_trace(
                        source_function="fina_mainbz",
                        derived=True,
                        derivation_method="segment_revenue / group_total_revenue * 100",
                        source_fields=_source_field_refs(
                            ("fina_mainbz", trace_metadata[index].get("revenue", {}).get("source_field")),
                        ),
                        canonical_unit="%",
                        denominator_scope=revenue_scope,
                    )
            if segment.get("profit_ratio") is None and total_profit != 0:
                profit_ratio = _ratio_percentage(segment.get("profit"), total_profit)
                if profit_ratio is not None:
                    segment["profit_ratio"] = profit_ratio
                    trace_metadata[index]["profit_ratio"] = _field_trace(
                        source_function="fina_mainbz",
                        derived=True,
                        derivation_method="segment_profit / group_total_profit * 100",
                        source_fields=_source_field_refs(
                            ("fina_mainbz", trace_metadata[index].get("profit", {}).get("source_field")),
                        ),
                        canonical_unit="%",
                        denominator_scope=profit_scope,
                    )


def _records(response: Any, *, endpoint: str) -> list[dict[str, Any]]:
    if response is None:
        return []
    if isinstance(response, dict):
        if "items" in response and "fields" in response:
            fields = response.get("fields")
            items = response.get("items")
            if not isinstance(fields, list) or not isinstance(items, list):
                raise TushareMalformedResponseError(f"{endpoint}: malformed response", endpoint=endpoint)
            return [dict(zip(fields, item, strict=False)) for item in items if isinstance(item, (list, tuple))]
        return [response]
    if isinstance(response, list):
        if all(isinstance(item, dict) for item in response):
            return response
        if not response:
            return []
        raise TushareMalformedResponseError(f"{endpoint}: malformed response", endpoint=endpoint)
    if hasattr(response, "to_dict"):
        try:
            rows = response.to_dict(orient="records")
        except TypeError:
            rows = response.to_dict()
        if isinstance(rows, list) and all(isinstance(item, dict) for item in rows):
            return rows
    raise TushareMalformedResponseError(f"{endpoint}: malformed response", endpoint=endpoint)


def _first_record(response: Any, *, endpoint: str) -> dict[str, Any]:
    rows = _records(response, endpoint=endpoint)
    return rows[0] if rows else {}


def _first_present(row: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    lower = {str(key).lower(): value for key, value in row.items()}
    for key in keys:
        value = lower.get(key.lower())
        if value not in (None, ""):
            return value
    return None


def _first_value(rows: list[dict[str, Any]], key: str) -> Any:
    for row in rows:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return None


def _endpoints_from_trace(source_trace: list[dict[str, Any]]) -> list[str]:
    endpoints = []
    for trace in source_trace:
        endpoint = trace.get("endpoint")
        if isinstance(endpoint, str) and endpoint and endpoint not in endpoints:
            endpoints.append(endpoint)
    return endpoints


def _endpoint_for_error(block_name: str, exc: TushareClientError) -> str:
    if exc.endpoint:
        return exc.endpoint
    return {
        "basic_info": "stock_basic",
        "financial_indicator": "financial_statements_and_indicators",
        "valuation": "daily_basic",
        "business_composition": "fina_mainbz",
    }.get(block_name, block_name)
