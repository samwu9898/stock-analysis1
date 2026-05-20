# -*- coding: utf-8 -*-
"""Normalized raw input schema for fundamental_skill.

These models represent adapter output, not final fundamental analysis.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .schema import DataSource


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RawBlockStatus(StrictBaseModel):
    block_name: str
    source_name: str | None = None
    success: bool
    row_count: int | None = None
    latest_period: str | None = None
    fetched_at: str | None = None
    error_message: str | None = None


class BasicInfoInput(StrictBaseModel):
    stock_code: str
    stock_name: str | None = None
    market: str | None = None
    industry: str | None = None
    main_business: str | None = None
    listing_date: str | None = None


class FinancialMetricInput(StrictBaseModel):
    period: str | None = None
    revenue: float | None = None
    revenue_yoy: float | None = None
    net_profit: float | None = None
    net_profit_yoy: float | None = None
    deducted_net_profit: float | None = None
    gross_margin: float | None = None
    net_margin: float | None = None
    roe: float | None = None
    operating_cashflow: float | None = None
    debt_to_asset: float | None = None
    inventory: float | None = None
    accounts_receivable: float | None = None
    contract_liabilities: float | None = None


class ValuationMetricInput(StrictBaseModel):
    pe_ttm: float | None = None
    pb: float | None = None
    ps: float | None = None
    dividend_yield: float | None = None
    market_cap: float | None = None


class BusinessCompositionInput(StrictBaseModel):
    period: str | None = None
    segments: list[dict[str, Any]] = Field(default_factory=list)


class NewsItemInput(StrictBaseModel):
    title: str
    publish_time: str | None = None
    source: str | None = None
    url: str | None = None
    summary: str | None = None


class NormalizedFundamentalInput(StrictBaseModel):
    schema_version: str = "fundamental_input.v1"
    stock_code: str
    stock_name: str | None = None
    generated_at: str
    data_cutoff: str | None = None
    basic_info: BasicInfoInput
    financial_metrics: list[FinancialMetricInput] = Field(default_factory=list)
    valuation_metrics: ValuationMetricInput | None = None
    business_composition: BusinessCompositionInput | None = None
    latest_news: list[NewsItemInput] = Field(default_factory=list)
    raw_blocks: dict[str, Any] = Field(default_factory=dict)
    block_status: list[RawBlockStatus] = Field(default_factory=list)
    data_sources: list[DataSource] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    adapter_warnings: list[str] = Field(default_factory=list)
    raw_data_path: str | None = None

    @field_validator("schema_version")
    @classmethod
    def schema_version_must_match(cls, value: str) -> str:
        if value != "fundamental_input.v1":
            raise ValueError("schema_version must be fundamental_input.v1")
        return value
