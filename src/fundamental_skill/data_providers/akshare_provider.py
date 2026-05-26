# -*- coding: utf-8 -*-
"""AkShare provider adapter backed by the existing RealDataConnector.

This adapter is intentionally thin: RealDataConnector remains the owner of the
current AkShare fetch, cache, commodity, and canonical raw JSON behavior.
"""

from __future__ import annotations

from typing import Any, Callable

from ..real_data_connector import RealDataConnector
from .schemas import CANONICAL_RAW_BLOCKS, ProviderCapabilities


AKSHARE_RAW_BLOCKS: tuple[str, ...] = (
    *CANONICAL_RAW_BLOCKS,
    "commodity_prices",
    "commodity_price_foreign_reference",
)


class AkShareProvider:
    """DataProvider implementation that preserves the current AkShare path."""

    name = "akshare"

    def __init__(
        self,
        connector: RealDataConnector | None = None,
        *,
        connector_factory: Callable[[], RealDataConnector] = RealDataConnector,
    ) -> None:
        self._connector = connector
        self._connector_factory = connector_factory

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider_name=self.name,
            raw_blocks=AKSHARE_RAW_BLOCKS,
            basic_info=True,
            financial_indicator=True,
            valuation=True,
            business_composition=True,
            news=True,
            commodity_prices=True,
            low_frequency_market_data=False,
            realtime_market_data=False,
            notes=("wraps_existing_real_data_connector",),
        )

    def fetch_to_raw_json(self, stock_code: str, *, force_refresh: bool = False) -> dict[str, Any]:
        return self._get_connector().fetch_to_raw_json(stock_code, force_refresh=force_refresh)

    def _get_connector(self) -> RealDataConnector:
        if self._connector is None:
            self._connector = self._connector_factory()
        return self._connector
