# -*- coding: utf-8 -*-
"""Base protocol for data providers.

This module defines only the Phase 1 interface. It does not import AkShare,
Tushare, SDK clients, MCP tools, or network transports.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from .schemas import ProviderCapabilities


@runtime_checkable
class DataProvider(Protocol):
    """A provider that returns the existing canonical raw JSON structure."""

    name: str

    def fetch_to_raw_json(self, stock_code: str, *, force_refresh: bool = False) -> dict[str, Any]:
        """Return canonical raw stock data for downstream existing pipeline use."""

    def capabilities(self) -> ProviderCapabilities:
        """Return provider capability metadata for routing and diagnostics."""

