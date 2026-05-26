# -*- coding: utf-8 -*-
"""Deterministic fake provider for Phase 1 tests.

The fake provider never imports provider SDKs, reads credentials, calls MCP, or
touches the network.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .schemas import CANONICAL_RAW_BLOCKS, ProviderCapabilities


@dataclass
class FakeDataProvider:
    name: str = "fake"
    stock_name: str = "Fake Stock"
    fail_message: str | None = None
    calls: list[dict[str, Any]] = field(default_factory=list)

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider_name=self.name,
            raw_blocks=CANONICAL_RAW_BLOCKS,
            basic_info=True,
            financial_indicator=True,
            valuation=True,
            business_composition=True,
            news=True,
            commodity_prices=False,
            low_frequency_market_data=False,
            realtime_market_data=False,
            notes=("phase1_fake_provider",),
        )

    def fetch_to_raw_json(self, stock_code: str, *, force_refresh: bool = False) -> dict[str, Any]:
        self.calls.append({"stock_code": stock_code, "force_refresh": force_refresh})
        if self.fail_message:
            raise RuntimeError(self.fail_message)

        code = _normalize_code(stock_code)
        generated_at = "2026-05-26T00:00:00"
        blocks: dict[str, list[dict[str, Any]]] = {
            "basic_info": [
                {
                    "stock_code": code,
                    "stock_name": self.stock_name,
                    "industry": "phase1 test industry",
                    "main_business": "phase1 canonical raw provider test data",
                    "listing_date": "2020-01-01",
                }
            ],
            "financial_indicator": [
                {
                    "period": "20251231",
                    "revenue": 100000000.0,
                    "revenue_yoy": 12.5,
                    "net_profit": 10000000.0,
                    "net_profit_yoy": 9.5,
                    "deducted_net_profit": 9000000.0,
                    "gross_margin": 30.0,
                    "net_margin": 10.0,
                    "roe": 11.0,
                    "operating_cashflow": 12000000.0,
                    "debt_to_asset": 35.0,
                    "inventory": 8000000.0,
                    "accounts_receivable": 7000000.0,
                    "contract_liabilities": 2000000.0,
                    "r_and_d_expense": 3000000.0,
                    "r_and_d_expense_ratio": 3.0,
                    "capex": 4000000.0,
                }
            ],
            "valuation": [
                {
                    "period": "2026-05-26",
                    "pe_ttm": 20.0,
                    "pb": 2.0,
                    "ps": 3.0,
                    "market_cap": 2000000000.0,
                    "dividend_yield": 1.2,
                }
            ],
            "business_composition": [
                {
                    "period": "2025-12-31",
                    "classification_type": "phase1_test",
                    "segment_name": "core segment",
                    "revenue": 100000000.0,
                    "revenue_ratio": 1.0,
                    "gross_margin": 0.30,
                    "cost": 70000000.0,
                    "profit": 30000000.0,
                    "profit_ratio": 1.0,
                }
            ],
            "news": [
                {
                    "title": "phase1 fake provider news",
                    "publish_time": "2026-05-26 00:00:00",
                    "source": "phase1_fake",
                    "url": None,
                    "summary": "Deterministic fake provider row for router tests.",
                }
            ],
        }
        return {
            "meta": {
                "code": code,
                "stock_name": self.stock_name,
                "generated_at": generated_at,
                "data_source": self.name,
                "connector_version": "fake_data_provider.phase1",
                "cache_hit": False,
            },
            "blocks": blocks,
            "fetch_status": {
                block_name: {
                    "success": True,
                    "error": None,
                    "missing_fields": [],
                    "fetched_at": generated_at,
                    "source_name": self.name,
                    "source_trace": [
                        {
                            "field_name": "phase1_fake",
                            "block_name": block_name,
                            "function_name": "FakeDataProvider.fetch_to_raw_json",
                            "source_function": "FakeDataProvider.fetch_to_raw_json",
                            "source_period": None,
                            "value": len(rows),
                            "derived": False,
                            "derivation_method": None,
                        }
                    ],
                    "warnings": [],
                }
                for block_name, rows in blocks.items()
            },
            "errors": [],
        }


def _normalize_code(stock_code: str) -> str:
    digits = "".join(ch for ch in str(stock_code) if ch.isdigit())
    return digits[-6:] if len(digits) >= 6 else str(stock_code)

