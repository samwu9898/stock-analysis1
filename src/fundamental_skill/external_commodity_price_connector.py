# -*- coding: utf-8 -*-
"""External commodity price connector for resource-stock fundamental context.

This module fetches and normalizes commodity price observations for data
readiness. It does not analyze price trends, render HTML, call LLMs, call
accounts, or produce action instructions.
"""

from __future__ import annotations

import math
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXPOSURE_MAP = PROJECT_ROOT / "config" / "commodity_exposure_map.yaml"
STALE_AFTER_DAYS = 7

COMMODITY_MAP: dict[str, dict[str, Any]] = {
    "silver": {"cn": "\u767d\u94f6", "futures_symbol": "AG", "sge_function": "spot_silver_benchmark_sge"},
    "gold": {"cn": "\u9ec4\u91d1", "futures_symbol": "AU", "sge_function": "spot_golden_benchmark_sge"},
    "copper": {"cn": "\u94dc", "futures_symbol": "CU", "realtime_symbol": "\u6caa\u94dc", "continuous_symbol": "CU0"},
    "tin": {"cn": "\u9521", "futures_symbol": "SN", "realtime_symbol": "\u6caa\u9521", "continuous_symbol": "SN0"},
    "aluminum": {"cn": "\u94dd", "futures_symbol": "AL"},
    "cobalt": {"cn": "\u94b4", "futures_symbol": None, "status": "probe_only"},
    "molybdenum": {"cn": "\u94bc", "futures_symbol": None, "status": "probe_only"},
}


def _safe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        out = float(value)
        return out if math.isfinite(out) else None
    if isinstance(value, str):
        text = value.strip().replace(",", "").replace("%", "")
        if text in {"", "--", "None", "none", "null", "nan", "NaN"}:
            return None
        try:
            out = float(text)
        except ValueError:
            return None
        return out if math.isfinite(out) else None
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


def _get_any(row: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    lower = {str(key).lower(): value for key, value in row.items()}
    for key in keys:
        value = lower.get(key.lower())
        if value not in (None, ""):
            return value
    return None


def _parse_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()[:19]
    for candidate in (text, text[:10]):
        try:
            return datetime.fromisoformat(candidate).date()
        except ValueError:
            pass
    for pattern in ("%Y%m%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(text, pattern).date()
        except ValueError:
            pass
    return None


class ExternalCommodityPriceConnector:
    def __init__(
        self,
        exposure_map_path: str | Path | None = None,
        akshare_client: Any | None = None,
        as_of_date: date | None = None,
    ) -> None:
        self.exposure_map_path = Path(exposure_map_path) if exposure_map_path else DEFAULT_EXPOSURE_MAP
        self.akshare_client = akshare_client
        self.as_of_date = as_of_date or date.today()
        self.exposure_map = self._load_exposure_map()

    def fetch_for_stock(self, stock_code: str, force_refresh: bool = False) -> dict[str, Any]:
        del force_refresh
        code = self._normalize_code(stock_code)
        exposure = self.exposure_map.get(code)
        if not exposure:
            return {
                "commodities": [],
                "missing_commodities": [],
                "stale_commodities": [],
                "partial_commodities": [],
                "warnings": [f"{code} has no configured commodity exposure"],
                "source_trace": [],
                "foreign_reference": [],
                "not_applicable": True,
                "success": False,
            }

        warnings: list[str] = []
        source_trace: list[dict[str, Any]] = []
        commodities: list[dict[str, Any]] = []
        missing: list[str] = []
        stale: list[str] = []
        required = [str(name) for name in exposure.get("commodities", [])]
        ak = self._load_akshare()

        for name in required:
            config = COMMODITY_MAP.get(name, {})
            symbol = config.get("futures_symbol")
            if not symbol:
                message = f"{name}: no_stable_primary_source"
                warnings.append(message)
                missing.append(name)
                source_trace.append(
                    {
                        "block_name": "commodity_prices",
                        "commodity_name": name,
                        "function_name": None,
                        "source_priority": "missing",
                        "success": False,
                        "stale": None,
                        "missing_reason": message,
                        "derived": False,
                    }
                )
                continue

            item = self._fetch_best_price(ak, name, str(symbol), config, source_trace)
            if item is None:
                missing.append(name)
                warnings.append(f"{name}: no_fresh_domestic_price_source")
                continue
            if item.get("is_stale"):
                stale.append(name)
                warnings.append(f"{name}: all_sources_stale")
            warnings.extend(item.get("warnings", []))
            commodities.append(item)

        fresh = [
            item.get("commodity_name")
            for item in commodities
            if isinstance(item, dict) and item.get("readiness_eligible") is True
        ]
        partial = [name for name in required if name not in fresh and name not in missing]
        return {
            "commodities": commodities,
            "missing_commodities": list(dict.fromkeys(missing)),
            "stale_commodities": list(dict.fromkeys(stale)),
            "partial_commodities": list(dict.fromkeys(partial)),
            "warnings": list(dict.fromkeys(warnings)),
            "source_trace": source_trace,
            "foreign_reference": self._fetch_foreign_reference(ak, source_trace),
            "not_applicable": False,
            "success": bool(required) and not missing and not stale and len(fresh) == len(required),
        }

    def _load_akshare(self) -> Any:
        if self.akshare_client is not None:
            return self.akshare_client
        try:
            import akshare as ak  # type: ignore
        except Exception as exc:  # pragma: no cover - environment dependent
            raise RuntimeError("akshare is not available; install akshare or use cached/mock data") from exc
        return ak

    def _load_exposure_map(self) -> dict[str, Any]:
        if not self.exposure_map_path.exists():
            return {}
        with open(self.exposure_map_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        return {self._normalize_code(key): value for key, value in raw.items() if isinstance(value, dict)}

    def _fetch_best_price(
        self,
        ak: Any,
        commodity_name: str,
        symbol: str,
        config: dict[str, Any],
        source_trace: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        stale_candidates: list[dict[str, Any]] = []

        primary = self._fetch_domestic_source(
            ak, commodity_name, symbol, config, "futures_spot_price", "primary", source_trace
        )
        if primary and primary.get("readiness_eligible"):
            return primary
        if primary:
            primary["warnings"] = list(dict.fromkeys(primary.get("warnings", []) + ["stale_primary_price"]))
            stale_candidates.append(primary)

        daily = self._fetch_domestic_source(
            ak,
            commodity_name,
            symbol,
            config,
            "futures_spot_price_daily",
            "domestic_daily_fallback",
            source_trace,
        )
        if daily and daily.get("readiness_eligible"):
            daily["warnings"] = list(dict.fromkeys(daily.get("warnings", []) + ["used_daily_fallback"]))
            return daily
        if daily:
            stale_candidates.append(daily)

        if commodity_name in {"copper", "tin"}:
            fresh_domestic = self._fetch_copper_tin_fresh_source(
                ak, commodity_name, symbol, config, source_trace
            )
            if fresh_domestic and fresh_domestic.get("readiness_eligible"):
                return fresh_domestic
            if fresh_domestic:
                stale_candidates.append(fresh_domestic)

        if commodity_name in {"silver", "gold"}:
            sge = self._fetch_sge_fallback(ak, commodity_name, symbol, config, source_trace)
            if sge and sge.get("readiness_eligible"):
                sge["warnings"] = list(dict.fromkeys(sge.get("warnings", []) + ["used_sge_fallback"]))
                return sge
            if sge:
                stale_candidates.append(sge)

        if stale_candidates:
            candidate = stale_candidates[0]
            candidate["source_priority"] = "stale_reference"
            candidate["readiness_eligible"] = False
            candidate["warnings"] = list(dict.fromkeys(candidate.get("warnings", []) + ["all_sources_stale"]))
            return candidate
        return None

    def _fetch_copper_tin_fresh_source(
        self,
        ak: Any,
        commodity_name: str,
        symbol: str,
        config: dict[str, Any],
        source_trace: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        realtime_symbol = str(config.get("realtime_symbol") or symbol)
        continuous_symbol = str(config.get("continuous_symbol") or symbol)
        attempts = (
            {
                "function_name": "futures_zh_realtime",
                "symbol": realtime_symbol,
                "priority": "domestic_realtime_primary",
                "market": "domestic_futures_realtime",
                "price_keys": ("trade", "last_price", "price", "\u6700\u65b0\u4ef7"),
                "date_keys": ("tradedate", "ticktime", "date", "\u65e5\u671f", "\u884c\u60c5\u65f6\u95f4", "time"),
                "warning": "used_domestic_realtime_primary",
            },
            {
                "function_name": "futures_zh_daily_sina",
                "symbol": continuous_symbol,
                "priority": "domestic_daily_fallback",
                "market": "domestic_futures_daily",
                "price_keys": ("close", "\u6536\u76d8\u4ef7", "settle", "price"),
                "date_keys": ("date", "\u65e5\u671f", "datetime", "time"),
                "warning": "used_zh_daily_fallback",
            },
            {
                "function_name": "futures_main_sina",
                "symbol": continuous_symbol,
                "priority": "domestic_main_fallback",
                "market": "domestic_futures_main",
                "price_keys": ("\u6536\u76d8\u4ef7", "close", "price"),
                "date_keys": ("date", "\u65e5\u671f", "datetime", "time"),
                "warning": "used_main_fallback",
            },
        )
        stale_candidates: list[dict[str, Any]] = []
        for attempt in attempts:
            item = self._fetch_market_quote_source(
                ak=ak,
                commodity_name=commodity_name,
                symbol=str(attempt["symbol"]),
                config=config,
                function_name=str(attempt["function_name"]),
                priority=str(attempt["priority"]),
                market=str(attempt["market"]),
                price_keys=attempt["price_keys"],
                date_keys=attempt["date_keys"],
                source_trace=source_trace,
            )
            if item and item.get("readiness_eligible"):
                item["warnings"] = list(dict.fromkeys(item.get("warnings", []) + [str(attempt["warning"])]))
                return item
            if item:
                stale_candidates.append(item)
        return stale_candidates[0] if stale_candidates else None

    def _fetch_market_quote_source(
        self,
        ak: Any,
        commodity_name: str,
        symbol: str,
        config: dict[str, Any],
        function_name: str,
        priority: str,
        market: str,
        price_keys: tuple[str, ...],
        date_keys: tuple[str, ...],
        source_trace: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        rows = self._call_akshare_rows(ak, function_name, symbol)
        row = self._select_symbol_row(rows, symbol)
        item = self._map_market_quote_row(
            row,
            commodity_name,
            symbol,
            config,
            function_name,
            priority,
            market,
            price_keys,
            date_keys,
        )
        if item is not None:
            trace = self._trace_from_item(item, row or {}, function_name, priority)
            item["source_trace"] = trace
            source_trace.append(trace)
            return item
        source_trace.append(
            {
                "block_name": "commodity_prices",
                "commodity_name": commodity_name,
                "function_name": function_name,
                "source_priority": priority,
                "success": False,
                "stale": None,
                "row_count": len(rows),
                "columns": list(rows[0].keys()) if rows and isinstance(rows[0], dict) else [],
                "warning": "no usable row",
                "derived": False,
            }
        )
        return None

    def _fetch_domestic_source(
        self,
        ak: Any,
        commodity_name: str,
        symbol: str,
        config: dict[str, Any],
        function_name: str,
        priority: str,
        source_trace: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        rows = self._call_akshare_rows(ak, function_name, symbol)
        row = self._select_symbol_row(rows, symbol)
        item = self._map_futures_row(row, commodity_name, symbol, config, function_name, priority)
        if item is not None:
            trace = self._trace_from_item(item, row or {}, function_name, priority)
            item["source_trace"] = trace
            source_trace.append(trace)
            return item
        source_trace.append(
            {
                "block_name": "commodity_prices",
                "commodity_name": commodity_name,
                "function_name": function_name,
                "source_priority": priority,
                "success": False,
                "stale": None,
                "row_count": len(rows),
                "columns": list(rows[0].keys()) if rows and isinstance(rows[0], dict) else [],
                "warning": "no usable row",
                "derived": False,
            }
        )
        return None

    def _fetch_sge_fallback(
        self,
        ak: Any,
        commodity_name: str,
        symbol: str,
        config: dict[str, Any],
        source_trace: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        function_name = config.get("sge_function")
        if not function_name or not hasattr(ak, function_name):
            return None
        try:
            rows = _records(getattr(ak, function_name)())
        except Exception as exc:
            source_trace.append(
                {
                    "block_name": "commodity_prices",
                    "commodity_name": commodity_name,
                    "function_name": function_name,
                    "source_priority": "sge_fallback",
                    "success": False,
                    "stale": None,
                    "error": str(exc),
                    "derived": False,
                }
            )
            return None
        row = self._latest_row(rows)
        if row is None:
            return None
        price = _safe_float(_get_any(row, ("\u665a\u76d8\u4ef7", "\u665a\u76d8\u57fa\u51c6\u4ef7", "pm_price", "price")))
        if price is None:
            price = _safe_float(_get_any(row, ("\u65e9\u76d8\u4ef7", "\u65e9\u76d8\u57fa\u51c6\u4ef7", "am_price")))
        dt = _parse_date(_get_any(row, ("\u4ea4\u6613\u65f6\u95f4", "date", "\u65e5\u671f", "time")))
        if price is None:
            return None
        item = self._base_item(commodity_name, symbol, config, price, dt, "SGE", function_name, "sge_fallback")
        trace = self._trace_from_item(item, row, function_name, "sge_fallback")
        item["source_trace"] = trace
        source_trace.append(trace)
        return item

    def _fetch_foreign_reference(self, ak: Any, source_trace: list[dict[str, Any]]) -> list[dict[str, Any]]:
        function_name = "futures_foreign_commodity_realtime"
        if not hasattr(ak, function_name):
            return []
        rows = self._call_akshare_rows(ak, function_name, "CAD")
        references = []
        for row in rows[:20]:
            symbol = str(_get_any(row, ("symbol", "\u4ee3\u7801", "\u54c1\u79cd", "name")) or "")
            price = _safe_float(_get_any(row, ("price", "\u6700\u65b0\u4ef7", "last_price", "\u73b0\u4ef7")))
            if not symbol or price is None:
                continue
            references.append(
                {
                    "symbol": symbol,
                    "price": price,
                    "date": str(_get_any(row, ("date", "\u65e5\u671f", "time", "\u65f6\u95f4")) or ""),
                    "market": "foreign_reference",
                    "source_function": function_name,
                    "source_priority": "foreign_reference",
                    "readiness_eligible": False,
                }
            )
        if references:
            source_trace.append(
                {
                    "block_name": "commodity_prices",
                    "function_name": function_name,
                    "source_priority": "foreign_reference",
                    "success": True,
                    "stale": None,
                    "row_count": len(references),
                    "derived": False,
                }
            )
        return references

    def _call_akshare_rows(self, ak: Any, function_name: str, symbol: str) -> list[dict[str, Any]]:
        if not hasattr(ak, function_name):
            return []
        fn: Callable[..., Any] = getattr(ak, function_name)
        attempts = (
            lambda: fn(vars_list=[symbol]),
            lambda: fn(symbol=symbol),
            lambda: fn(symbol),
            lambda: fn(),
        )
        for attempt in attempts:
            try:
                rows = _records(attempt())
            except TypeError:
                continue
            except Exception:
                continue
            if rows:
                return rows
        return []

    def _select_symbol_row(self, rows: list[dict[str, Any]], symbol: str) -> dict[str, Any] | None:
        if not rows:
            return None
        for row in rows:
            raw_symbol = str(_get_any(row, ("symbol", "var", "\u54c1\u79cd", "\u5546\u54c1", "\u4ee3\u7801", "\u5408\u7ea6")) or "").upper()
            if raw_symbol == symbol or symbol in raw_symbol:
                return row
        return self._latest_row(rows)

    def _latest_row(self, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not rows:
            return None
        dated = []
        for index, row in enumerate(rows):
            parsed = _parse_date(_get_any(row, ("date", "\u65e5\u671f", "\u4ea4\u6613\u65f6\u95f4", "\u6570\u636e\u65e5\u671f", "time")))
            if parsed:
                dated.append((parsed, index, row))
        if dated:
            return max(dated, key=lambda item: (item[0], item[1]))[2]
        return rows[0]

    def _map_futures_row(
        self,
        row: dict[str, Any] | None,
        commodity_name: str,
        symbol: str,
        config: dict[str, Any],
        function_name: str,
        priority: str,
    ) -> dict[str, Any] | None:
        if not row:
            return None
        price = _safe_float(_get_any(row, ("spot_price", "\u73b0\u8d27\u4ef7\u683c", "\u73b0\u8d27\u4ef7", "spot", "price")))
        dt = _parse_date(_get_any(row, ("date", "\u65e5\u671f", "\u6570\u636e\u65e5\u671f", "\u4ea4\u6613\u65f6\u95f4", "time")))
        if price is None:
            return None
        item = self._base_item(
            commodity_name,
            symbol,
            config,
            price,
            dt,
            "domestic_futures_spot",
            function_name,
            priority,
        )
        item.update(
            {
                "near_contract": _get_any(row, ("near_contract", "\u8fd1\u6708\u5408\u7ea6", "near_contract_symbol")),
                "near_contract_price": _safe_float(_get_any(row, ("near_contract_price", "\u8fd1\u6708\u5408\u7ea6\u4ef7\u683c"))),
                "dominant_contract": _get_any(row, ("dominant_contract", "\u4e3b\u529b\u5408\u7ea6", "dominant_contract_symbol")),
                "dominant_contract_price": _safe_float(_get_any(row, ("dominant_contract_price", "\u4e3b\u529b\u5408\u7ea6\u4ef7\u683c"))),
                "near_basis": _safe_float(_get_any(row, ("near_basis", "\u8fd1\u6708\u57fa\u5dee"))),
                "dominant_basis": _safe_float(_get_any(row, ("dominant_basis", "dom_basis", "\u4e3b\u529b\u57fa\u5dee"))),
            }
        )
        return item

    def _map_market_quote_row(
        self,
        row: dict[str, Any] | None,
        commodity_name: str,
        symbol: str,
        config: dict[str, Any],
        function_name: str,
        priority: str,
        market: str,
        price_keys: tuple[str, ...],
        date_keys: tuple[str, ...],
    ) -> dict[str, Any] | None:
        if not row:
            return None
        price = _safe_float(_get_any(row, price_keys))
        dt = _parse_date(_get_any(row, date_keys))
        if dt is None and _get_any(row, ("ticktime", "\u884c\u60c5\u65f6\u95f4", "time")) is not None:
            # Realtime rows can expose a time-only field after a separate trade date.
            tradedate = _parse_date(_get_any(row, ("tradedate", "trade_date", "\u4ea4\u6613\u65e5\u671f", "date", "\u65e5\u671f")))
            dt = tradedate
        if price is None:
            return None
        item = self._base_item(
            commodity_name,
            symbol,
            config,
            price,
            dt,
            market,
            function_name,
            priority,
        )
        item.update(
            {
                "settlement": _safe_float(_get_any(row, ("settlement", "\u7ed3\u7b97\u4ef7", "settle"))),
                "presettlement": _safe_float(_get_any(row, ("presettlement", "\u6628\u7ed3\u7b97", "pre_settlement"))),
                "open": _safe_float(_get_any(row, ("open", "\u5f00\u76d8\u4ef7"))),
                "high": _safe_float(_get_any(row, ("high", "\u6700\u9ad8\u4ef7"))),
                "low": _safe_float(_get_any(row, ("low", "\u6700\u4f4e\u4ef7"))),
                "close": _safe_float(_get_any(row, ("close", "\u6536\u76d8\u4ef7"))),
                "volume": _safe_float(_get_any(row, ("volume", "\u6210\u4ea4\u91cf"))),
                "hold": _safe_float(_get_any(row, ("hold", "\u6301\u4ed3\u91cf"))),
            }
        )
        return item

    def _base_item(
        self,
        commodity_name: str,
        symbol: str,
        config: dict[str, Any],
        price: float,
        dt: date | None,
        market: str,
        function_name: str,
        priority: str,
    ) -> dict[str, Any]:
        freshness_days = max(0, (self.as_of_date - dt).days) if dt else None
        is_stale = True if dt is None else freshness_days > STALE_AFTER_DAYS
        warnings = []
        if dt is None:
            warnings.append("unparseable_price_date")
        if is_stale:
            warnings.append(f"{commodity_name} price is stale: {freshness_days} days old")
        return {
            "commodity_name": commodity_name,
            "commodity_name_cn": config.get("cn"),
            "symbol": symbol,
            "price": price,
            "date": dt.isoformat() if dt else None,
            "market": market,
            "source_function": function_name,
            "source_priority": priority,
            "near_contract": None,
            "near_contract_price": None,
            "dominant_contract": None,
            "dominant_contract_price": None,
            "change": None,
            "unit": None,
            "currency": None,
            "freshness_days": freshness_days,
            "is_stale": is_stale,
            "readiness_eligible": market != "foreign_reference" and not is_stale,
            "warnings": warnings,
        }

    def _trace_from_item(
        self,
        item: dict[str, Any],
        row: dict[str, Any],
        function_name: str,
        priority: str,
    ) -> dict[str, Any]:
        return {
            "block_name": "commodity_prices",
            "commodity_name": item["commodity_name"],
            "function_name": function_name,
            "source_priority": priority,
            "source_period": item.get("date"),
            "source_column": self._source_column_for_priority(priority),
            "value": item.get("price"),
            "market": item.get("market"),
            "success": item.get("price") is not None,
            "stale": item.get("is_stale"),
            "date": item.get("date"),
            "columns": list(row.keys()),
            "derived": False,
        }

    def _source_column_for_priority(self, priority: str) -> str:
        return {
            "primary": "spot_price",
            "domestic_daily_fallback": "close",
            "domestic_realtime_primary": "trade",
            "domestic_main_fallback": "\u6536\u76d8\u4ef7",
            "sge_fallback": "\u665a\u76d8\u4ef7/\u65e9\u76d8\u4ef7",
        }.get(priority, "price")

    def _normalize_code(self, stock_code: Any) -> str:
        digits = "".join(ch for ch in str(stock_code) if ch.isdigit())
        if 0 < len(digits) < 6:
            return digits.zfill(6)
        if not digits:
            return str(stock_code)
        return digits[-6:]
