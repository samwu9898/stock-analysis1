# -*- coding: utf-8 -*-
"""Adapter from existing raw JSON blocks to normalized fundamental input.

This module does not fetch data, call LLMs, score fundamentals, or make
trading decisions.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from .raw_schema import (
    BasicInfoInput,
    BusinessCompositionInput,
    FinancialMetricInput,
    NewsItemInput,
    NormalizedFundamentalInput,
    RawBlockStatus,
    ValuationMetricInput,
)
from .schema import DataSource


BLOCK_ALIASES = {
    "basic_info": ("basic_info", "company_info", "stock_info", "个股信息", "公司资料"),
    "financial": (
        "financial_abstract",
        "financial_indicator",
        "fin_abstract",
        "fin_indicator_ths",
        "finance",
        "财务摘要",
        "主要财务指标",
        "利润表",
        "资产负债表",
        "现金流量表",
        "income_statement",
        "balance_sheet",
        "cashflow",
    ),
    "valuation": ("valuation", "market_data", "quote", "spot", "估值", "市盈率", "市净率"),
    "business": ("business_composition", "main_business", "zygc", "主营构成", "业务构成"),
    "news": ("news", "latest_news", "notice", "公告", "新闻"),
}


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _first_row(value: Any) -> dict[str, Any]:
    rows = _as_list(value)
    return rows[0] if rows and isinstance(rows[0], dict) else {}


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "").replace("%", "")
        if cleaned in {"", "--", "None", "null", "nan"}:
            return None
        multiplier = 1.0
        if cleaned.endswith("亿"):
            multiplier = 100000000.0
            cleaned = cleaned[:-1]
        elif cleaned.endswith("万"):
            multiplier = 10000.0
            cleaned = cleaned[:-1]
        try:
            return float(cleaned) * multiplier
        except ValueError:
            return None
    return None


def _get_any(row: dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    lower_map = {str(k).lower(): v for k, v in row.items()}
    for key in keys:
        value = lower_map.get(key.lower())
        if value not in (None, ""):
            return value
    return None


def _find_block(blocks: dict[str, Any], aliases: Iterable[str]) -> tuple[str | None, Any]:
    for alias in aliases:
        if alias in blocks:
            return alias, blocks[alias]
    lowered = {str(k).lower(): k for k in blocks}
    for alias in aliases:
        actual = lowered.get(alias.lower())
        if actual is not None:
            return actual, blocks[actual]
    return None, None


def _item_value_rows_to_dict(rows: list[Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        item = _get_any(row, ("item", "指标", "项目", "name", "key"))
        value = _get_any(row, ("value", "值", "内容", "val"))
        if item is not None:
            out[str(item)] = value
    return out


def _latest_period_from_rows(rows: list[Any]) -> str | None:
    date_keys = (
        "period",
        "报告期",
        "报告日",
        "报告日期",
        "date",
        "日期",
        "发布时间",
        "publish_time",
        "变更日期",
    )
    periods = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        value = _get_any(row, date_keys)
        if value is not None:
            periods.append(str(value)[:19])
    return sorted(periods)[-1] if periods else None


def _infer_stock_code(raw_data: dict[str, Any], blocks: dict[str, Any], raw_data_path: str | None) -> str | None:
    meta = raw_data.get("meta") if isinstance(raw_data.get("meta"), dict) else {}
    code = _get_any(meta, ("code", "stock_code", "symbol"))
    if code:
        return str(code)[-6:] if re.search(r"\d{6}$", str(code)) else str(code)

    for block_name in ("spot", "basic_info", "stock_info", "company_info", "zygc"):
        row = _first_row(blocks.get(block_name))
        code = _get_any(row, ("股票代码", "证券代码", "代码", "stock_code", "code", "symbol"))
        if code:
            match = re.search(r"(\d{6})", str(code))
            return match.group(1) if match else str(code)

    if raw_data_path:
        match = re.search(r"(\d{6})", Path(raw_data_path).name)
        if match:
            return match.group(1)
    return None


def _infer_market(code: str | None, meta: dict[str, Any]) -> str | None:
    market = _get_any(meta, ("market", "exchange"))
    if market:
        return str(market)
    if not code:
        return None
    if code.startswith(("60", "68", "11", "12", "5")):
        return "sh"
    if code.startswith(("00", "30", "20", "15", "16", "18")):
        return "sz"
    if code.startswith(("4", "8", "92")):
        return "bj"
    return None


class FundamentalDataAdapter:
    def from_file(self, raw_data_path: str) -> NormalizedFundamentalInput:
        with open(raw_data_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        return self.from_dict(raw_data, raw_data_path=raw_data_path)

    def from_dict(
        self, raw_data: dict[str, Any], raw_data_path: str | None = None
    ) -> NormalizedFundamentalInput:
        warnings: list[str] = []
        missing_fields: list[str] = []

        if not isinstance(raw_data, dict):
            raw_data = {"__raw__": raw_data}
            warnings.append("unknown_raw_structure: raw_data is not a dict")
            missing_fields.append("unknown_raw_structure")

        meta = raw_data.get("meta") if isinstance(raw_data.get("meta"), dict) else {}
        has_blocks = isinstance(raw_data.get("blocks"), dict)
        if has_blocks:
            blocks = raw_data["blocks"]
        else:
            known_top = {"meta", "errors", "fetch_status", "blocks"}
            if any(key in raw_data for key in known_top):
                blocks = {}
            else:
                blocks = {"__raw__": raw_data}
                warnings.append("unknown_raw_structure: no recognized blocks wrapper")
                missing_fields.append("unknown_raw_structure")

        if not meta:
            warnings.append("missing_meta")
            missing_fields.extend(["meta", "generated_at"])

        stock_code = _infer_stock_code(raw_data, blocks, raw_data_path) or "UNKNOWN"
        if stock_code == "UNKNOWN":
            missing_fields.append("stock_code")

        generated_at = str(_get_any(meta, ("generated_at", "created_at", "timestamp")) or _now_iso())
        data_cutoff = _get_any(meta, ("data_cutoff", "cutoff", "as_of"))

        basic_info = self._extract_basic_info(blocks, stock_code, meta)
        financial_metrics = self._extract_financial_metrics(blocks)
        valuation_metrics = self._extract_valuation_metrics(blocks)
        business_composition = self._extract_business_composition(blocks)
        latest_news = self._extract_news(blocks)
        block_status = self._build_block_status(raw_data, blocks, generated_at)
        data_sources = self._build_data_sources(block_status)

        normalized = NormalizedFundamentalInput(
            stock_code=stock_code,
            stock_name=basic_info.stock_name,
            generated_at=generated_at,
            data_cutoff=str(data_cutoff) if data_cutoff is not None else None,
            basic_info=basic_info,
            financial_metrics=financial_metrics,
            valuation_metrics=valuation_metrics,
            business_composition=business_composition,
            latest_news=latest_news,
            raw_blocks=blocks,
            block_status=block_status,
            data_sources=data_sources,
            missing_fields=[],
            adapter_warnings=warnings,
            raw_data_path=raw_data_path,
        )

        missing_fields.extend(self._collect_missing_fields(normalized))
        normalized.missing_fields = sorted(set(missing_fields))
        return normalized

    def _extract_basic_info(
        self, blocks: dict[str, Any], stock_code: str, meta: dict[str, Any]
    ) -> BasicInfoInput:
        _, block = _find_block(blocks, BLOCK_ALIASES["basic_info"])
        rows = _as_list(block)
        row = _first_row(rows)
        item_map = _item_value_rows_to_dict(rows)
        merged = {**item_map, **row}

        spot = _first_row(blocks.get("spot"))
        stock_name = (
            _get_any(meta, ("stock_name", "name"))
            or _get_any(merged, ("stock_name", "name", "股票简称", "证券简称", "org_short_name_cn", "公司简称"))
            or _get_any(spot, ("名称", "股票简称", "证券简称", "name"))
        )
        industry = _get_any(merged, ("industry", "所属行业", "affiliate_industry", "classi_name", "行业"))
        main_business = _get_any(merged, ("main_business", "主营业务", "main_operation_business", "经营范围", "operating_scope"))
        listing_date = _get_any(merged, ("listing_date", "上市日期", "listed_date", "成立日期", "established_date"))

        return BasicInfoInput(
            stock_code=stock_code,
            stock_name=str(stock_name) if stock_name is not None else None,
            market=_infer_market(stock_code, meta),
            industry=str(industry) if industry is not None else None,
            main_business=str(main_business) if main_business is not None else None,
            listing_date=str(listing_date) if listing_date is not None else None,
        )

    def _extract_financial_metrics(self, blocks: dict[str, Any]) -> list[FinancialMetricInput]:
        metrics: list[FinancialMetricInput] = []
        _, block = _find_block(blocks, BLOCK_ALIASES["financial"])
        rows = _as_list(block)
        for row in rows[:12]:
            if not isinstance(row, dict):
                continue
            metric = FinancialMetricInput(
                period=str(_get_any(row, ("period", "报告期", "报告日", "报告日期")) or "") or None,
                revenue=_to_float(_get_any(row, ("revenue", "营业总收入", "营业收入", "主营业务收入"))),
                revenue_yoy=_to_float(_get_any(row, ("revenue_yoy", "营业总收入同比增长率", "营业收入同比增长率"))),
                net_profit=_to_float(_get_any(row, ("net_profit", "净利润", "归母净利润"))),
                net_profit_yoy=_to_float(_get_any(row, ("net_profit_yoy", "净利润同比增长率", "归母净利润同比增长率"))),
                deducted_net_profit=_to_float(_get_any(row, ("deducted_net_profit", "扣非净利润"))),
                gross_margin=_to_float(_get_any(row, ("gross_margin", "销售毛利率", "毛利率"))),
                net_margin=_to_float(_get_any(row, ("net_margin", "销售净利率", "净利率"))),
                roe=_to_float(_get_any(row, ("roe", "净资产收益率", "ROE", "加权净资产收益率"))),
                operating_cashflow=_to_float(_get_any(row, ("operating_cashflow", "经营活动产生的现金流量净额", "经营现金流量净额"))),
                debt_to_asset=_to_float(_get_any(row, ("debt_to_asset", "资产负债率"))),
                inventory=_to_float(_get_any(row, ("inventory", "存货"))),
                accounts_receivable=_to_float(_get_any(row, ("accounts_receivable", "应收账款"))),
                contract_liabilities=_to_float(_get_any(row, ("contract_liabilities", "合同负债"))),
            )
            if any(value is not None for key, value in metric.model_dump().items() if key != "period"):
                metrics.append(metric)
        return metrics

    def _extract_valuation_metrics(self, blocks: dict[str, Any]) -> ValuationMetricInput | None:
        _, block = _find_block(blocks, BLOCK_ALIASES["valuation"])
        row = _first_row(block)
        if not row:
            return None
        valuation = ValuationMetricInput(
            pe_ttm=_to_float(_get_any(row, ("pe_ttm", "市盈率TTM", "市盈率-动态", "市盈率"))),
            pb=_to_float(_get_any(row, ("pb", "市净率"))),
            ps=_to_float(_get_any(row, ("ps", "市销率"))),
            dividend_yield=_to_float(_get_any(row, ("dividend_yield", "股息率"))),
            market_cap=_to_float(_get_any(row, ("market_cap", "总市值", "流通市值"))),
        )
        return valuation if any(v is not None for v in valuation.model_dump().values()) else None

    def _extract_business_composition(self, blocks: dict[str, Any]) -> BusinessCompositionInput | None:
        _, block = _find_block(blocks, BLOCK_ALIASES["business"])
        rows = [row for row in _as_list(block) if isinstance(row, dict)]
        if not rows:
            return None
        latest_period = _latest_period_from_rows(rows)
        segments = []
        for row in rows[:50]:
            segments.append(
                {
                    "segment_name": _get_any(row, ("segment_name", "主营构成", "业务名称", "name")),
                    "revenue": _to_float(_get_any(row, ("revenue", "主营收入", "营业收入"))),
                    "cost": _to_float(_get_any(row, ("cost", "主营成本", "营业成本"))),
                    "gross_margin": _to_float(_get_any(row, ("gross_margin", "毛利率"))),
                    "revenue_ratio": _to_float(_get_any(row, ("revenue_ratio", "收入比例"))),
                    "raw": row,
                }
            )
        return BusinessCompositionInput(period=latest_period, segments=segments)

    def _extract_news(self, blocks: dict[str, Any]) -> list[NewsItemInput]:
        news_items: list[NewsItemInput] = []
        _, block = _find_block(blocks, BLOCK_ALIASES["news"])
        for row in _as_list(block)[:20]:
            if not isinstance(row, dict):
                continue
            title = _get_any(row, ("title", "新闻标题", "公告标题", "报告名称"))
            if not title:
                continue
            news_items.append(
                NewsItemInput(
                    title=str(title),
                    publish_time=str(_get_any(row, ("publish_time", "发布时间", "公告日期", "日期")) or "") or None,
                    source=str(_get_any(row, ("source", "文章来源", "机构")) or "") or None,
                    url=str(_get_any(row, ("url", "新闻链接", "公告链接", "链接")) or "") or None,
                    summary=str(_get_any(row, ("summary", "新闻内容", "摘要")) or "") or None,
                )
            )
        return news_items

    def _build_block_status(
        self, raw_data: dict[str, Any], blocks: dict[str, Any], generated_at: str
    ) -> list[RawBlockStatus]:
        fetch_status = raw_data.get("fetch_status") if isinstance(raw_data.get("fetch_status"), dict) else {}
        statuses: list[RawBlockStatus] = []
        for name, value in blocks.items():
            rows = _as_list(value)
            status_info = fetch_status.get(name) if isinstance(fetch_status.get(name), dict) else {}
            error = status_info.get("error_message") or status_info.get("error")
            row_count = len(value) if isinstance(value, list) else (1 if value is not None else 0)
            statuses.append(
                RawBlockStatus(
                    block_name=str(name),
                    source_name=status_info.get("source_name") or str(name),
                    success=bool(status_info.get("success", row_count > 0 and not error)),
                    row_count=row_count,
                    latest_period=status_info.get("latest_period") or _latest_period_from_rows(rows),
                    fetched_at=status_info.get("fetched_at") or generated_at,
                    error_message=str(error) if error else None,
                )
            )
        return statuses

    def _build_data_sources(self, block_status: list[RawBlockStatus]) -> list[DataSource]:
        if not block_status:
            return [DataSource(name="unknown_raw_data", source_type="unknown", success=False)]
        return [
            DataSource(
                name=status.source_name or status.block_name,
                source_type="akshare" if status.block_name != "__raw__" else "unknown",
                fetched_at=status.fetched_at,
                period=status.latest_period,
                success=status.success,
                error_message=status.error_message,
            )
            for status in block_status
        ]

    def _collect_missing_fields(self, normalized_input: NormalizedFundamentalInput) -> list[str]:
        missing = []
        basic = normalized_input.basic_info
        for field_name in ("stock_name", "market", "industry", "main_business", "listing_date"):
            if getattr(basic, field_name) in (None, ""):
                missing.append(f"basic_info.{field_name}")
        if not normalized_input.financial_metrics:
            missing.append("financial_metrics")
        if normalized_input.valuation_metrics is None:
            missing.append("valuation_metrics")
        if normalized_input.business_composition is None:
            missing.append("business_composition")
        if not normalized_input.latest_news:
            missing.append("latest_news")
        if not normalized_input.data_cutoff:
            missing.append("data_cutoff")
        return missing


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize raw stock-analysis JSON for fundamental_skill.")
    parser.add_argument("--input", required=True, help="Path to raw JSON file")
    parser.add_argument("--output", required=True, help="Path to normalized output JSON")
    args = parser.parse_args()

    adapter = FundamentalDataAdapter()
    normalized = adapter.from_file(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(normalized.model_dump_json(indent=2), encoding="utf-8")

    print(f"stock_code: {normalized.stock_code}")
    print(f"stock_name: {normalized.stock_name}")
    print(f"missing_fields: {normalized.missing_fields}")
    print(f"adapter_warnings: {normalized.adapter_warnings}")
    print("block_status summary:")
    for status in normalized.block_status:
        print(
            f"  - {status.block_name}: success={status.success}, "
            f"rows={status.row_count}, latest_period={status.latest_period}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
