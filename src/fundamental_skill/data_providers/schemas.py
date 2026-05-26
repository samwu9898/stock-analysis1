# -*- coding: utf-8 -*-
"""Lightweight provider-facing schemas.

These models intentionally stay independent from evidence_pack and final
fundamental output schemas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


CANONICAL_RAW_TOP_LEVEL_KEYS: tuple[str, ...] = ("meta", "blocks", "fetch_status", "errors")
CANONICAL_RAW_BLOCKS: tuple[str, ...] = (
    "basic_info",
    "financial_indicator",
    "valuation",
    "business_composition",
    "news",
)


class ProviderMode(str, Enum):
    """Supported provider routing modes."""

    AUTO = "auto"
    AKSHARE = "akshare"
    TUSHARE = "tushare"
    DUAL_COMPARE = "dual_compare"


def parse_provider_mode(value: ProviderMode | str | None) -> ProviderMode:
    """Normalize user/config provider mode values."""

    if value is None or value == "":
        return ProviderMode.AUTO
    if isinstance(value, ProviderMode):
        return value
    normalized = str(value).strip().lower().replace("-", "_")
    aliases = {
        "default": ProviderMode.AUTO,
        "auto": ProviderMode.AUTO,
        "ak": ProviderMode.AKSHARE,
        "akshare": ProviderMode.AKSHARE,
        "ts": ProviderMode.TUSHARE,
        "tushare": ProviderMode.TUSHARE,
        "dual": ProviderMode.DUAL_COMPARE,
        "dual_compare": ProviderMode.DUAL_COMPARE,
        "compare": ProviderMode.DUAL_COMPARE,
        "comparison": ProviderMode.DUAL_COMPARE,
        "tushare_vs_akshare": ProviderMode.DUAL_COMPARE,
    }
    try:
        return aliases[normalized]
    except KeyError as exc:
        allowed = ", ".join(mode.value for mode in ProviderMode)
        raise ValueError(f"unsupported provider mode: {value!r}; expected one of: {allowed}") from exc


@dataclass(frozen=True)
class ProviderCapabilities:
    """Provider capability metadata used by the router and tests."""

    provider_name: str
    raw_blocks: tuple[str, ...] = CANONICAL_RAW_BLOCKS
    basic_info: bool = True
    financial_indicator: bool = True
    valuation: bool = True
    business_composition: bool = True
    news: bool = False
    commodity_prices: bool = False
    low_frequency_market_data: bool = False
    realtime_market_data: bool = False
    notes: tuple[str, ...] = field(default_factory=tuple)

    def supports_block(self, block_name: str) -> bool:
        return block_name in self.raw_blocks


@dataclass(frozen=True)
class ProviderSelection:
    """A non-secret routing decision."""

    mode: ProviderMode
    selected_provider: str | None = None
    fallback_provider: str | None = None
    comparison_providers: tuple[str, ...] = field(default_factory=tuple)
    reason: str = ""

    @property
    def is_comparison(self) -> bool:
        return self.mode == ProviderMode.DUAL_COMPARE


def missing_canonical_raw_keys(raw: Mapping[str, Any]) -> list[str]:
    """Return missing top-level canonical keys for a raw provider payload."""

    return [key for key in CANONICAL_RAW_TOP_LEVEL_KEYS if key not in raw]


def raw_has_canonical_shape(raw: Mapping[str, Any]) -> bool:
    """Check only the stable top-level raw contract."""

    return not missing_canonical_raw_keys(raw) and isinstance(raw.get("blocks"), Mapping)

