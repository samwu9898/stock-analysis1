# -*- coding: utf-8 -*-
"""Real A-share data connector for fundamental_skill.

This connector fetches public AkShare data and converts it into raw JSON blocks
that FundamentalDataAdapter already understands. It does not analyze, score,
render HTML, call LLMs, call trading accounts, or make trading decisions.
"""

from __future__ import annotations

import json
import math
import re
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

from .external_commodity_price_connector import ExternalCommodityPriceConnector


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE_DIR = PROJECT_ROOT / "cache" / "real_data"
CONNECTOR_VERSION = "real_data_connector.v2.3a"
BLOCK_NAMES = ("basic_info", "financial_indicator", "valuation", "business_composition", "news")


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def _safe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return None
        return float(value)
    if isinstance(value, str):
        text = value.strip().replace(",", "").replace("%", "")
        if text in {"", "--", "None", "none", "null", "nan", "NaN"}:
            return None
        multiplier = 1.0
        if text.endswith("亿"):
            multiplier = 100000000.0
            text = text[:-1]
        elif text.endswith("万"):
            multiplier = 10000.0
            text = text[:-1]
        try:
            return float(text) * multiplier
        except ValueError:
            return None
    return None


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if str(value) in {"NaT", "nan", "NaN", "inf", "-inf", "Infinity", "-Infinity"}:
        return None
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, Decimal):
        try:
            converted = float(value)
            return converted if math.isfinite(converted) else None
        except Exception:
            return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(_json_safe(key)): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]

    type_module = type(value).__module__
    if type_module.startswith("numpy"):
        try:
            if bool(getattr(value, "dtype", None)) and str(value.dtype).startswith("datetime64"):
                text = str(value)
                return None if text in {"NaT", "nan", "NaN"} else text
        except Exception:
            pass
        try:
            converted = value.item()
        except Exception:
            converted = None
        if converted is not None and converted is not value:
            return _json_safe(converted)
        try:
            converted_float = float(value)
            return converted_float if math.isfinite(converted_float) else None
        except Exception:
            return str(value)

    if type_module.startswith("pandas"):
        if str(value) in {"NaT", "nan", "NaN"}:
            return None
        if hasattr(value, "isoformat"):
            try:
                return value.isoformat()
            except Exception:
                pass
        try:
            if bool(value != value):
                return None
        except Exception:
            pass
        return str(value)

    try:
        if bool(value != value):
            return None
    except Exception:
        pass
    return str(value)


def _ratio_percent(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator * 100


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


def _records(frame_or_records: Any) -> list[dict[str, Any]]:
    if frame_or_records is None:
        return []
    if isinstance(frame_or_records, list):
        return [item for item in frame_or_records if isinstance(item, dict)]
    if isinstance(frame_or_records, dict):
        return [frame_or_records]
    if hasattr(frame_or_records, "to_dict"):
        try:
            return frame_or_records.to_dict(orient="records")
        except TypeError:
            data = frame_or_records.to_dict()
            return data if isinstance(data, list) else [data]
    return []


def _period_columns(columns: list[str]) -> list[str]:
    return sorted(
        [str(column) for column in columns if re.fullmatch(r"(?:19|20)\d{6}", str(column))],
        reverse=True,
    )


def _previous_year_same_period(period: str) -> str | None:
    if not re.fullmatch(r"(?:19|20)\d{6}", str(period)):
        return None
    return f"{int(period[:4]) - 1}{period[4:]}"


def _market_prefix(code: str) -> str:
    return "sh" if code.startswith(("60", "68", "9")) else "sz"


def _prefixed_symbol(code: str) -> str:
    return f"{_market_prefix(code)}{code}"


class RealDataConnector:
    def __init__(self, cache_dir: str | Path | None = None) -> None:
        self.cache_dir = Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR
        self._source_traces: dict[str, list[dict[str, Any]]] = {}
        self._warnings: dict[str, list[str]] = {}

    def fetch_to_raw_json(
        self,
        stock_code: str,
        output_path: str | None = None,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        code = self._normalize_code(stock_code)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = self.cache_dir / f"{code}.json"

        if not force_refresh:
            cached = self._read_fresh_cache(cache_path)
            if cached is not None:
                cached.setdefault("meta", {})["cache_hit"] = True
                cached["meta"]["cache_path"] = str(cache_path)
                self._write_output(cached, output_path)
                return cached

        raw = self._empty_raw(code)
        fetchers: dict[str, Callable[[str], Any]] = {
            "basic_info": self._fetch_basic_info,
            "financial_indicator": self._fetch_financial_indicator,
            "valuation": self._fetch_valuation,
            "business_composition": self._fetch_business_composition,
            "news": self._fetch_news,
        }

        for block_name, fetcher in fetchers.items():
            self._source_traces[block_name] = []
            self._warnings[block_name] = []
            try:
                block = fetcher(code)
                raw["blocks"][block_name] = block
                missing = self._missing_fields_for_block(block_name, block)
                raw["fetch_status"][block_name] = {
                    "success": True,
                    "error": None,
                    "missing_fields": missing,
                    "fetched_at": raw["meta"]["generated_at"],
                    "source_trace": self._source_traces.get(block_name, []),
                    "warnings": self._warnings.get(block_name, []),
                }
            except Exception as exc:  # pragma: no cover - exact AkShare failures vary
                message = f"{block_name}: {exc}"
                raw["errors"].append(message)
                raw["fetch_status"][block_name] = {
                    "success": False,
                    "error": str(exc),
                    "missing_fields": self._expected_fields(block_name),
                    "fetched_at": raw["meta"]["generated_at"],
                    "source_trace": self._source_traces.get(block_name, []),
                    "warnings": self._warnings.get(block_name, []),
                }

        self._attach_commodity_prices(raw, code, force_refresh=force_refresh)

        raw["meta"]["stock_name"] = self._infer_stock_name(raw)
        raw["meta"]["data_cutoff"] = self._infer_data_cutoff(raw)
        raw["meta"]["cache_created_at"] = raw["meta"]["generated_at"]
        raw["meta"]["cache_hit"] = False
        raw["meta"]["cache_path"] = str(cache_path)

        if self._should_fallback_to_cache(raw["errors"]) and cache_path.exists():
            cached = self._read_cache(cache_path)
            if cached is not None:
                cached.setdefault("errors", []).extend(raw["errors"])
                cached.setdefault("meta", {})["cache_hit"] = True
                cached["meta"]["cache_fallback_reason"] = "fresh_fetch_failed"
                cached["meta"]["cache_path"] = str(cache_path)
                self._write_output(cached, output_path)
                return cached

        self._write_json(cache_path, raw)
        self._write_output(raw, output_path)
        return raw

    def _should_fallback_to_cache(self, errors: list[str]) -> bool:
        return any(not str(error).startswith("news:") for error in errors)

    def _load_akshare(self):
        try:
            import akshare as ak  # type: ignore
        except Exception as exc:  # pragma: no cover - environment dependent
            raise RuntimeError("akshare is not available; install akshare or use cached/mock data") from exc
        return ak

    def _fetch_basic_info(self, code: str) -> list[dict[str, Any]]:
        ak = self._load_akshare()
        rows = _records(ak.stock_profile_cninfo(symbol=code))
        row = rows[0] if rows else {}
        source = "stock_profile_cninfo"

        if not row:
            fallback_rows = _records(ak.stock_individual_info_em(symbol=code))
            item_map = self._item_value_map(fallback_rows)
            source = "stock_individual_info_em"
        else:
            item_map = {}

        mapped = {
            "stock_code": _first_present(row, ("A股代码", "stock_code", "股票代码")) or code,
            "stock_name": _first_present(row, ("A股简称", "stock_name", "股票简称")) or _first_present(row, ("公司名称", "name")) or item_map.get("股票简称"),
            "industry": _first_present(row, ("所属行业", "industry")) or item_map.get("所属行业"),
            "main_business": _first_present(row, ("主营业务", "main_business")) or _first_present(row, ("经营范围",)) or item_map.get("主营业务"),
            "listing_date": _first_present(row, ("上市日期", "listing_date")) or item_map.get("上市日期"),
        }
        for field_name, value in mapped.items():
            self._add_trace("basic_info", field_name, source, field_name, None, value, False, None)
        return [mapped]

    def _fetch_financial_indicator(self, code: str) -> list[dict[str, Any]]:
        ak = self._load_akshare()
        payload = ak.stock_financial_abstract(symbol=code)
        metrics = self._parse_financial_abstract(payload)
        self._merge_sina_balance_sheet_fields(metrics, code, ak)
        self._merge_sina_rd_capex_fields(metrics, code, ak)
        return metrics

    def _call_sina_statement(self, code: str, ak: Any, statement_name: str) -> Any:
        try:
            return ak.stock_financial_report_sina(stock=_prefixed_symbol(code), symbol=statement_name)
        except TypeError:
            try:
                return ak.stock_financial_report_sina(stock=code, symbol=statement_name)
            except TypeError:
                return ak.stock_financial_report_sina(code, statement_name)

    def _parse_financial_abstract(self, payload: Any) -> list[dict[str, Any]]:
        rows = _records(payload)
        if not rows:
            self._warn("financial_indicator", "stock_financial_abstract returned no rows")
            return []

        columns = [str(col) for col in getattr(payload, "columns", rows[0].keys())]
        indicator_column = self._find_column(columns, ("指标",))
        if not indicator_column:
            self._warn("financial_indicator", "stock_financial_abstract missing 指标 column")
            return []

        periods = _period_columns(columns)
        if not periods:
            self._warn("financial_indicator", "stock_financial_abstract missing period columns")
            return []
        latest_period = periods[0]
        previous_period = _previous_year_same_period(latest_period)

        revenue, revenue_indicator = self._value_for(rows, indicator_column, ("营业总收入",), latest_period)
        revenue_cost, _ = self._value_for(rows, indicator_column, ("营业成本",), latest_period)
        parent_profit, parent_profit_indicator = self._value_for(rows, indicator_column, ("归母净利润", "归属母公司净利润"), latest_period)
        net_profit_row = self._find_indicator_row(rows, indicator_column, ("净利润",), exact=True)
        net_profit = _safe_float(net_profit_row.get(latest_period)) if net_profit_row else None
        net_profit_indicator = str(net_profit_row.get(indicator_column)) if net_profit_row else None

        metric: dict[str, Any] = {"period": latest_period}
        self._assign_direct(metric, "revenue", revenue, revenue_indicator, latest_period)
        self._assign_yoy(metric, "revenue_yoy", rows, indicator_column, latest_period, previous_period, ("营业总收入增长率",), ("营业总收入",))
        self._assign_yoy(
            metric,
            "net_profit_yoy",
            rows,
            indicator_column,
            latest_period,
            previous_period,
            ("归属母公司净利润增长率", "归母净利润增长率"),
            ("归母净利润", "归属母公司净利润", "净利润"),
        )
        self._assign_direct_from_hints(metric, "deducted_net_profit", rows, indicator_column, ("扣非净利润",), latest_period)
        self._assign_direct(metric, "net_profit", parent_profit if parent_profit is not None else net_profit, parent_profit_indicator or net_profit_indicator, latest_period)
        self._assign_margin(metric, "gross_margin", rows, indicator_column, latest_period, ("毛利率",), revenue - revenue_cost if revenue is not None and revenue_cost is not None else None, revenue, "margin_from_revenue_cost", "营业总收入/营业成本")
        self._assign_margin(metric, "net_margin", rows, indicator_column, latest_period, ("销售净利率", "净利率"), net_profit, revenue, "margin_from_revenue_profit", "净利润/营业总收入")
        self._assign_direct_from_hints(metric, "roe", rows, indicator_column, ("净资产收益率(ROE)", "净资产收益率_ROE", "ROE", "净资产收益率_平均", "摊薄净资产收益率"), latest_period)
        self._assign_direct_from_hints(metric, "operating_cashflow", rows, indicator_column, ("经营现金流量净额",), latest_period)
        self._assign_direct_from_hints(metric, "debt_to_asset", rows, indicator_column, ("资产负债率",), latest_period)
        self._warn_if_proxy_only(rows, indicator_column, "存货", "inventory")
        self._warn_if_proxy_only(rows, indicator_column, "应收账款", "accounts_receivable")
        return [metric]

    def _merge_sina_balance_sheet_fields(self, metrics: list[dict[str, Any]], code: str, ak: Any) -> None:
        if not metrics:
            metrics.append({})
        try:
            payload = ak.stock_financial_report_sina(stock=_prefixed_symbol(code), symbol="资产负债表")
        except TypeError:
            try:
                payload = ak.stock_financial_report_sina(stock=code, symbol="资产负债表")
            except TypeError:
                payload = ak.stock_financial_report_sina(code, "资产负债表")
        except Exception as exc:
            self._warn("financial_indicator", f"stock_financial_report_sina balance_sheet failed: {exc}")
            return

        values = self._parse_sina_balance_sheet_fields(payload)
        metric = metrics[0]
        for field_name, item in values.items():
            value = item.get("value")
            metric[field_name] = value
            if metric.get("period") in (None, "", "unknown") and item.get("source_period") != "unknown":
                metric["period"] = item.get("source_period")
            if value is None:
                continue
            self._add_trace(
                "financial_indicator",
                field_name,
                "stock_financial_report_sina",
                item.get("source_column_or_row"),
                item.get("source_period"),
                value,
                False,
                None,
                source_column=item.get("source_column_or_row"),
                source_column_or_row=item.get("source_column_or_row"),
                source_function="stock_financial_report_sina",
                statement_type="balance_sheet",
                period_confidence=item.get("period_confidence"),
                value_confidence=item.get("value_confidence"),
                scope_note=item.get("scope_note"),
            )

    def _merge_sina_rd_capex_fields(self, metrics: list[dict[str, Any]], code: str, ak: Any) -> None:
        if not metrics:
            metrics.append({})
        metric = metrics[0]

        profit_values: dict[str, dict[str, Any]] = {}
        try:
            profit_payload = self._call_sina_statement(code, ak, "利润表")
            profit_values = self._parse_sina_profit_sheet_fields(profit_payload)
        except Exception as exc:
            self._warn("financial_indicator", f"stock_financial_report_sina profit_sheet failed: {exc}")

        r_and_d = profit_values.get("r_and_d_expense")
        revenue = profit_values.get("revenue")
        if r_and_d:
            metric["r_and_d_expense"] = r_and_d.get("value")
            if metric.get("period") in (None, "", "unknown") and r_and_d.get("source_period") != "unknown":
                metric["period"] = r_and_d.get("source_period")
            if r_and_d.get("value") is not None:
                self._add_financial_statement_trace("r_and_d_expense", r_and_d, "profit_sheet", derived=False)

        if r_and_d and revenue:
            if r_and_d.get("source_period") == revenue.get("source_period") and r_and_d.get("source_period") != "unknown":
                ratio = _ratio_percent(_safe_float(r_and_d.get("value")), _safe_float(revenue.get("value")))
                if ratio is not None:
                    ratio_item = {
                        "value": ratio,
                        "source_column_or_row": r_and_d.get("source_column_or_row"),
                        "source_period": r_and_d.get("source_period"),
                        "period_confidence": r_and_d.get("period_confidence"),
                        "value_confidence": "medium",
                        "unit": "%",
                        "unit_confidence": "high",
                        "cumulative_or_single_quarter": "cumulative",
                        "scope_note": self._rd_capex_scope_note("r_and_d_expense_ratio"),
                    }
                    method = "r_and_d_expense / revenue * 100, same source_period only"
                    metric["r_and_d_expense_ratio"] = ratio
                    self._add_financial_statement_trace(
                        "r_and_d_expense_ratio",
                        ratio_item,
                        "profit_sheet",
                        derived=True,
                        derivation_method=method,
                    )
            else:
                self._warn(
                    "financial_indicator",
                    "r_and_d_expense_ratio not derived because r_and_d_expense and revenue source_period differ",
                )
        elif r_and_d:
            self._warn("financial_indicator", "r_and_d_expense_ratio not derived because revenue is missing from profit sheet")

        try:
            cashflow_payload = self._call_sina_statement(code, ak, "现金流量表")
            cashflow_values = self._parse_sina_cashflow_sheet_fields(cashflow_payload)
        except Exception as exc:
            self._warn("financial_indicator", f"stock_financial_report_sina cash_flow_sheet failed: {exc}")
            cashflow_values = {}

        capex = cashflow_values.get("capex")
        if capex:
            metric["capex"] = capex.get("value")
            if metric.get("period") in (None, "", "unknown") and capex.get("source_period") != "unknown":
                metric["period"] = capex.get("source_period")
            if capex.get("value") is not None:
                self._add_financial_statement_trace("capex", capex, "cash_flow_sheet", derived=False)

    def _add_financial_statement_trace(
        self,
        field_name: str,
        item: dict[str, Any],
        statement_type: str,
        derived: bool,
        derivation_method: str | None = None,
    ) -> None:
        self._add_trace(
            "financial_indicator",
            field_name,
            "stock_financial_report_sina",
            item.get("source_column_or_row"),
            item.get("source_period"),
            item.get("value"),
            derived,
            derivation_method,
            source_column=item.get("source_column_or_row"),
            source_column_or_row=item.get("source_column_or_row"),
            source_function="stock_financial_report_sina",
            statement_type=statement_type,
            period_confidence=item.get("period_confidence"),
            value_confidence=item.get("value_confidence"),
            unit=item.get("unit"),
            unit_confidence=item.get("unit_confidence"),
            cumulative_or_single_quarter=item.get("cumulative_or_single_quarter"),
            scope_note=item.get("scope_note"),
        )

    def _parse_sina_profit_sheet_fields(self, payload: Any) -> dict[str, dict[str, Any]]:
        rows = _records(payload)
        if not rows:
            self._warn("financial_indicator", "stock_financial_report_sina profit_sheet returned no rows")
            return {}
        columns = [str(col) for col in getattr(payload, "columns", rows[0].keys())]
        out: dict[str, dict[str, Any]] = {}
        rd = self._first_statement_amount(rows, columns, ("研发费用",))
        revenue = self._first_statement_amount(rows, columns, ("营业总收入", "营业收入"))
        if rd:
            rd["scope_note"] = self._rd_capex_scope_note("r_and_d_expense")
            out["r_and_d_expense"] = rd
        else:
            self._warn("financial_indicator", "r_and_d_expense: stock_financial_report_sina missing profit-sheet column")
        if revenue:
            out["revenue"] = revenue
        else:
            self._warn("financial_indicator", "r_and_d_expense_ratio: stock_financial_report_sina profit-sheet revenue missing")
        return out

    def _parse_sina_cashflow_sheet_fields(self, payload: Any) -> dict[str, dict[str, Any]]:
        rows = _records(payload)
        if not rows:
            self._warn("financial_indicator", "stock_financial_report_sina cash_flow_sheet returned no rows")
            return {}
        columns = [str(col) for col in getattr(payload, "columns", rows[0].keys())]
        capex = self._first_statement_amount(
            rows,
            columns,
            (
                "购建固定资产、无形资产和其他长期资产所支付的现金",
                "购建固定资产、无形资产和其他长期资产支付的现金",
                "购建固定资产、无形资产和其他长期资产支付现金",
            ),
        )
        if capex:
            capex["scope_note"] = self._rd_capex_scope_note("capex")
            return {"capex": capex}
        self._warn("financial_indicator", "capex: stock_financial_report_sina missing cash-flow long-term-asset cash-paid column")
        return {}

    def _first_statement_amount(
        self,
        rows: list[dict[str, Any]],
        columns: list[str],
        source_columns: tuple[str, ...],
    ) -> dict[str, Any] | None:
        source_column = next((column for column in source_columns if column in columns or column in rows[0]), None)
        if source_column is None:
            return None
        selected_row = None
        selected_value = None
        for row in rows:
            value = _safe_float(row.get(source_column))
            if value is not None:
                selected_row = row
                selected_value = value
                break
        if selected_row is None:
            return None
        source_period, period_confidence = self._statement_source_period(selected_row)
        return {
            "value": selected_value,
            "source_column_or_row": source_column,
            "source_period": source_period,
            "period_confidence": period_confidence,
            "value_confidence": "medium",
            "unit": "raw_statement_unit",
            "unit_confidence": "low",
            "cumulative_or_single_quarter": "cumulative",
        }

    def _statement_source_period(self, row: dict[str, Any]) -> tuple[str, str]:
        source_period = str(row.get("报告日") or row.get("报告日期") or row.get("报告期") or "")
        if re.fullmatch(r"(?:19|20)\d{6}", source_period):
            return source_period, "high"
        if re.fullmatch(r"(?:19|20)\d{2}-\d{2}-\d{2}", source_period):
            return source_period, "high"
        return "unknown", "low"

    def _rd_capex_scope_note(self, field_name: str) -> str:
        if field_name == "r_and_d_expense":
            return "研发费用为利润表费用金额字段，不等同于研发人员数量、研发项目数量或技术壁垒。"
        if field_name == "r_and_d_expense_ratio":
            return "研发费用率由研发费用除以同报告期营业收入派生，用于观察研发强度，不等同于技术壁垒已确认。"
        if field_name == "capex":
            return "capex 为购建固定资产、无形资产和其他长期资产支付现金，不等同于产能确定释放或未来增长确定性。"
        return ""

    def _parse_sina_balance_sheet_fields(self, payload: Any) -> dict[str, dict[str, Any]]:
        rows = _records(payload)
        if not rows:
            self._warn("financial_indicator", "stock_financial_report_sina balance_sheet returned no rows")
            return {}

        columns = [str(col) for col in getattr(payload, "columns", rows[0].keys())]
        field_columns = {
            "inventory": ("存货",),
            "accounts_receivable": ("应收账款",),
            "contract_liabilities": ("合同负债",),
        }
        out: dict[str, dict[str, Any]] = {}
        for field_name, candidates in field_columns.items():
            source_column = next((column for column in candidates if column in columns or column in rows[0]), None)
            if source_column is None:
                self._warn("financial_indicator", f"{field_name}: stock_financial_report_sina missing balance-sheet column")
                continue
            selected_row = None
            selected_value = None
            for row in rows:
                value = _safe_float(row.get(source_column))
                if value is not None:
                    selected_row = row
                    selected_value = value
                    break
            if selected_row is None:
                self._warn("financial_indicator", f"{field_name}: stock_financial_report_sina balance-sheet value missing or non-numeric")
                continue
            source_period = str(selected_row.get("报告日") or "")
            if re.fullmatch(r"(?:19|20)\d{6}", source_period):
                period_confidence = "high"
            else:
                source_period = "unknown"
                period_confidence = "low"
                self._warn("financial_indicator", f"{field_name}: stock_financial_report_sina 报告日 is missing or unrecognizable")
            out[field_name] = {
                "value": selected_value,
                "source_column_or_row": source_column,
                "source_period": source_period,
                "period_confidence": period_confidence,
                "value_confidence": "medium",
                "scope_note": self._balance_sheet_scope_note(field_name),
            }
        return out

    def _balance_sheet_scope_note(self, field_name: str) -> str:
        if field_name == "contract_liabilities":
            return "合同负债可作为订单可见度 proxy，但不等同于真实订单或 backlog。"
        if field_name == "inventory":
            return "Balance-sheet inventory amount only; turnover ratio or turnover days are not substitutes."
        if field_name == "accounts_receivable":
            return "Balance-sheet accounts receivable amount only; turnover ratio or turnover days are not substitutes."
        return "Balance-sheet amount field."

    def _fetch_valuation(self, code: str) -> list[dict[str, Any]]:
        ak = self._load_akshare()
        rows = _records(ak.stock_value_em(symbol=code))
        return self._parse_stock_value_em(rows)

    def _fetch_business_composition(self, code: str) -> list[dict[str, Any]]:
        ak = self._load_akshare()
        rows = _records(ak.stock_zygc_em(symbol=_prefixed_symbol(code)))
        return self._parse_stock_zygc_em(rows)

    def _parse_stock_value_em(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not rows:
            self._warn("valuation", "stock_value_em returned no rows")
            return []

        row, period = self._latest_row_by_date(rows, "数据日期", "valuation", "stock_value_em")
        field_map = {
            "pe_ttm": "PE(TTM)",
            "pb": "市净率",
            "ps": "市销率",
            "market_cap": "总市值",
        }
        mapped: dict[str, Any] = {"period": period, "dividend_yield": None}
        for field_name, source_column in field_map.items():
            value = _safe_float(row.get(source_column))
            mapped[field_name] = value
            if source_column not in row:
                self._warn("valuation", f"stock_value_em missing column {source_column} for {field_name}")
            elif value is None:
                self._warn("valuation", f"stock_value_em column {source_column} could not be converted for {field_name}")
            else:
                self._add_trace(
                    "valuation",
                    field_name,
                    "stock_value_em",
                    source_column,
                    period,
                    value,
                    False,
                    None,
                    source_column=source_column,
                )
        self._warn("valuation", "dividend_yield is not available from confirmed v2.1 valuation sources")
        return [mapped]

    def _parse_stock_zygc_em(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not rows:
            self._warn("business_composition", "stock_zygc_em returned no rows")
            return []

        _, latest_period = self._latest_row_by_date(rows, "报告日期", "business_composition", "stock_zygc_em")
        if not latest_period:
            self._warn("business_composition", "stock_zygc_em missing sortable 报告日期; using all rows")

        latest_rows = [
            row for row in rows
            if not latest_period or str(row.get("报告日期") or "") == str(latest_period)
        ]
        segments = []
        for row in latest_rows:
            segment_name = row.get("主营构成")
            if segment_name in (None, ""):
                continue
            segments.append(
                {
                    "period": row.get("报告日期"),
                    "segment_name": segment_name,
                    "classification_type": row.get("分类类型"),
                    "revenue": _safe_float(row.get("主营收入")),
                    "revenue_ratio": _safe_float(row.get("收入比例")),
                    "gross_margin": _safe_float(row.get("毛利率")),
                    "cost": _safe_float(row.get("主营成本")),
                    "cost_ratio": _safe_float(row.get("成本比例")),
                    "profit": _safe_float(row.get("主营利润")),
                    "profit_ratio": _safe_float(row.get("利润比例")),
                }
            )
        if not segments:
            self._warn("business_composition", "stock_zygc_em latest period has no valid 主营构成 rows")
            return []

        self._add_trace(
            "business_composition",
            "segments",
            "stock_zygc_em",
            "主营构成",
            str(latest_period) if latest_period else None,
            len(segments),
            False,
            None,
            source_column="主营构成",
            row_count=len(segments),
            columns=list(rows[0].keys()) if rows and isinstance(rows[0], dict) else [],
        )
        return segments

    def _fetch_news(self, code: str) -> list[dict[str, Any]]:
        ak = self._load_akshare()
        rows = _records(ak.stock_news_em(symbol=code))
        out = []
        for row in rows[:20]:
            out.append(
                {
                    "title": _first_present(row, ("新闻标题", "标题", "title")),
                    "publish_time": str(_first_present(row, ("发布时间", "日期", "publish_time")) or "") or None,
                    "source": _first_present(row, ("文章来源", "来源", "source")),
                    "url": _first_present(row, ("新闻链接", "链接", "url")),
                    "summary": _first_present(row, ("新闻内容", "摘要", "summary")),
                    "raw": row,
                }
            )
        return out

    def _attach_commodity_prices(self, raw: dict[str, Any], code: str, force_refresh: bool = False) -> None:
        connector = ExternalCommodityPriceConnector()
        if code not in connector.exposure_map:
            return
        try:
            connector.akshare_client = self._load_akshare()
            result = connector.fetch_for_stock(code, force_refresh=force_refresh)
            commodities = result.get("commodities", [])
            raw["blocks"]["commodity_prices"] = commodities
            if result.get("foreign_reference"):
                raw["blocks"]["commodity_price_foreign_reference"] = result.get("foreign_reference", [])

            missing_commodities = list(result.get("missing_commodities", []))
            stale_commodities = [
                item.get("commodity_name")
                for item in commodities
                if isinstance(item, dict) and item.get("is_stale")
            ]
            partial_commodities = list(result.get("partial_commodities", []))
            missing_fields = [f"external.commodity_prices.{name}" for name in missing_commodities]
            missing_fields.extend(
                f"external.commodity_prices.{name}.freshness"
                for name in stale_commodities
                if name
            )
            raw["fetch_status"]["commodity_prices"] = {
                "success": bool(result.get("success")),
                "error": None,
                "missing_fields": list(dict.fromkeys(missing_fields)),
                "fetched_at": raw["meta"]["generated_at"],
                "source_trace": result.get("source_trace", []),
                "warnings": result.get("warnings", []),
                "missing_commodities": missing_commodities,
                "stale_commodities": list(dict.fromkeys(stale_commodities)),
                "partial_commodities": partial_commodities,
            }
        except Exception as exc:  # pragma: no cover - exact AkShare failures vary
            raw["errors"].append(f"commodity_prices: {exc}")
            raw["blocks"]["commodity_prices"] = []
            raw["fetch_status"]["commodity_prices"] = {
                "success": False,
                "error": str(exc),
                "missing_fields": ["external.commodity_prices"],
                "fetched_at": raw["meta"]["generated_at"],
                "source_trace": [],
                "warnings": [],
            }

    def _find_column(self, columns: list[str], names: tuple[str, ...]) -> str | None:
        for name in names:
            if name in columns:
                return name
        return None

    def _find_indicator_row(
        self,
        rows: list[dict[str, Any]],
        indicator_column: str,
        hints: tuple[str, ...],
        exact: bool = False,
        exclude: tuple[str, ...] = (),
    ) -> dict[str, Any] | None:
        for row in rows:
            text = str(row.get(indicator_column, ""))
            if any(term in text for term in exclude):
                continue
            if exact and any(text == hint for hint in hints):
                return row
            if not exact and any(hint in text for hint in hints):
                return row
        return None

    def _value_for(self, rows: list[dict[str, Any]], indicator_column: str, hints: tuple[str, ...], period: str) -> tuple[float | None, str | None]:
        row = self._find_indicator_row(rows, indicator_column, hints)
        if not row:
            return None, None
        return _safe_float(row.get(period)), str(row.get(indicator_column))

    def _assign_direct(self, metric: dict[str, Any], field: str, value: float | None, indicator: str | None, period: str) -> None:
        metric[field] = value
        if value is not None:
            self._add_trace("financial_indicator", field, "stock_financial_abstract", indicator, period, value, False, None)

    def _assign_direct_from_hints(
        self,
        metric: dict[str, Any],
        field: str,
        rows: list[dict[str, Any]],
        indicator_column: str,
        hints: tuple[str, ...],
        period: str,
        exact: bool = False,
        exclude: tuple[str, ...] = (),
    ) -> None:
        row = self._find_indicator_row(rows, indicator_column, hints, exact=exact, exclude=exclude)
        value = _safe_float(row.get(period)) if row else None
        indicator = str(row.get(indicator_column)) if row else None
        self._assign_direct(metric, field, value, indicator, period)

    def _assign_yoy(
        self,
        metric: dict[str, Any],
        field: str,
        rows: list[dict[str, Any]],
        indicator_column: str,
        latest_period: str,
        previous_period: str | None,
        growth_hints: tuple[str, ...],
        base_hints: tuple[str, ...],
    ) -> None:
        growth_row = self._find_indicator_row(rows, indicator_column, growth_hints)
        if growth_row:
            value = _safe_float(growth_row.get(latest_period))
            metric[field] = value
            if value is not None:
                self._add_trace("financial_indicator", field, "stock_financial_abstract", str(growth_row.get(indicator_column)), latest_period, value, False, None)
            return

        base_row = self._find_indicator_row(rows, indicator_column, base_hints)
        current = _safe_float(base_row.get(latest_period)) if base_row else None
        previous = _safe_float(base_row.get(previous_period)) if base_row and previous_period else None
        value = _ratio_percent((current - previous) if current is not None and previous is not None else None, previous)
        metric[field] = value
        if value is not None:
            self._add_trace("financial_indicator", field, "stock_financial_abstract", str(base_row.get(indicator_column)), latest_period, value, True, "yoy_from_same_period")

    def _assign_margin(
        self,
        metric: dict[str, Any],
        field: str,
        rows: list[dict[str, Any]],
        indicator_column: str,
        period: str,
        direct_hints: tuple[str, ...],
        numerator: float | None,
        denominator: float | None,
        derivation_method: str,
        source_indicator: str,
    ) -> None:
        row = self._find_indicator_row(rows, indicator_column, direct_hints)
        value = _safe_float(row.get(period)) if row else None
        if value is not None:
            metric[field] = value
            self._add_trace("financial_indicator", field, "stock_financial_abstract", str(row.get(indicator_column)), period, value, False, None)
            return
        value = _ratio_percent(numerator, denominator)
        metric[field] = value
        if value is not None:
            self._add_trace("financial_indicator", field, "stock_financial_abstract", source_indicator, period, value, True, derivation_method)

    def _warn_if_proxy_only(self, rows: list[dict[str, Any]], indicator_column: str, keyword: str, field: str) -> None:
        exact = self._find_indicator_row(rows, indicator_column, (keyword,), exact=True)
        proxy = any(keyword in str(row.get(indicator_column, "")) and any(term in str(row.get(indicator_column, "")) for term in ("周转率", "周转天数")) for row in rows)
        if exact is None and proxy:
            self._warn("financial_indicator", f"{field}: turnover proxy indicators exist, but no amount field was mapped")

    def _latest_row_by_date(
        self,
        rows: list[dict[str, Any]],
        date_column: str,
        block_name: str,
        function_name: str,
    ) -> tuple[dict[str, Any], str | None]:
        dated_rows = []
        for index, row in enumerate(rows):
            value = row.get(date_column)
            if value in (None, ""):
                continue
            try:
                parsed = datetime.fromisoformat(str(value))
            except ValueError:
                continue
            dated_rows.append((parsed, index, row, str(value)))
        if dated_rows:
            _, _, row, period = max(dated_rows, key=lambda item: (item[0], item[1]))
            return row, period
        self._warn(block_name, f"{function_name} missing sortable {date_column}; using first available row")
        row = rows[0] if rows else {}
        value = row.get(date_column)
        return row, str(value) if value not in (None, "") else None

    def _add_trace(
        self,
        block_name: str,
        field_name: str,
        function_name: str,
        source_indicator: str | None,
        source_period: str | None,
        value: Any,
        derived: bool,
        derivation_method: str | None,
        source_column: str | None = None,
        row_count: int | None = None,
        columns: list[str] | None = None,
        source_column_or_row: str | None = None,
        source_function: str | None = None,
        statement_type: str | None = None,
        period_confidence: str | None = None,
        value_confidence: str | None = None,
        unit: str | None = None,
        unit_confidence: str | None = None,
        cumulative_or_single_quarter: str | None = None,
        scope_note: str | None = None,
    ) -> None:
        trace = {
            "field_name": field_name,
            "block_name": block_name,
            "function_name": function_name,
            "source_function": source_function or function_name,
            "source_indicator": source_indicator,
            "source_period": source_period,
            "value": value,
            "derived": derived,
            "derivation_method": derivation_method,
        }
        if source_column is not None:
            trace["source_column"] = source_column
        if source_column_or_row is not None:
            trace["source_column_or_row"] = source_column_or_row
        if row_count is not None:
            trace["row_count"] = row_count
        if columns is not None:
            trace["columns"] = columns
        if statement_type is not None:
            trace["statement_type"] = statement_type
        if period_confidence is not None:
            trace["period_confidence"] = period_confidence
        if value_confidence is not None:
            trace["value_confidence"] = value_confidence
        if unit is not None:
            trace["unit"] = unit
        if unit_confidence is not None:
            trace["unit_confidence"] = unit_confidence
        if cumulative_or_single_quarter is not None:
            trace["cumulative_or_single_quarter"] = cumulative_or_single_quarter
        if scope_note is not None:
            trace["scope_note"] = scope_note
        self._source_traces.setdefault(block_name, []).append(trace)

    def _warn(self, block_name: str, message: str) -> None:
        self._warnings.setdefault(block_name, []).append(message)

    def _empty_raw(self, code: str) -> dict[str, Any]:
        generated_at = _now_iso()
        return {
            "meta": {
                "code": code,
                "generated_at": generated_at,
                "data_source": "akshare",
                "connector_version": CONNECTOR_VERSION,
            },
            "blocks": {name: [] for name in BLOCK_NAMES},
            "fetch_status": {
                name: {"success": False, "error": "not_fetched", "missing_fields": self._expected_fields(name)}
                for name in BLOCK_NAMES
            },
            "errors": [],
        }

    def _item_value_map(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        out = {}
        for row in rows:
            item = _first_present(row, ("item", "项目", "指标", "name"))
            value = _first_present(row, ("value", "值", "内容", "val"))
            if item is not None:
                out[str(item)] = value
        return out

    def _normalize_code(self, stock_code: str) -> str:
        digits = "".join(ch for ch in str(stock_code) if ch.isdigit())
        if len(digits) < 6:
            raise ValueError("stock_code must contain a 6 digit A-share code")
        return digits[-6:]

    def _missing_fields_for_block(self, block_name: str, block: Any) -> list[str]:
        rows = _records(block)
        if not rows:
            if block_name == "business_composition":
                return ["business_composition.segments"]
            return self._expected_fields(block_name)
        keys = set().union(*(row.keys() for row in rows if isinstance(row, dict)))
        missing = []
        for field in self._expected_fields(block_name):
            if field not in keys or all(row.get(field) in (None, "") for row in rows if isinstance(row, dict)):
                missing.append(field)
        return missing

    def _expected_fields(self, block_name: str) -> list[str]:
        return {
            "basic_info": ["stock_code", "stock_name", "industry", "main_business", "listing_date"],
            "financial_indicator": [
                "revenue_yoy",
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
            "business_composition": ["segment_name", "revenue", "revenue_ratio", "gross_margin"],
            "news": ["title", "publish_time", "source", "url", "summary"],
        }.get(block_name, [])

    def _infer_stock_name(self, raw: dict[str, Any]) -> str | None:
        rows = _records(raw.get("blocks", {}).get("basic_info"))
        return rows[0].get("stock_name") if rows else None

    def _infer_data_cutoff(self, raw: dict[str, Any]) -> str | None:
        rows = _records(raw.get("blocks", {}).get("financial_indicator"))
        periods = sorted(str(row.get("period")) for row in rows if row.get("period"))
        return periods[-1] if periods else None

    def _read_fresh_cache(self, cache_path: Path) -> dict[str, Any] | None:
        cached = self._read_cache(cache_path)
        if cached is None:
            return None
        created_at = cached.get("meta", {}).get("cache_created_at") or cached.get("meta", {}).get("generated_at")
        if not created_at:
            return None
        try:
            created = datetime.fromisoformat(str(created_at))
        except ValueError:
            return None
        if datetime.now() - created <= timedelta(hours=24):
            return cached
        return None

    def _read_cache(self, cache_path: Path) -> dict[str, Any] | None:
        if not cache_path.exists():
            return None
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _write_output(self, raw: dict[str, Any], output_path: str | None) -> None:
        if output_path:
            self._write_json(Path(output_path), raw)

    def _write_json(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        safe_data = _json_safe(data)
        path.write_text(json.dumps(safe_data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
