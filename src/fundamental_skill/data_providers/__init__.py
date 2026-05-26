# -*- coding: utf-8 -*-
"""Provider abstraction skeleton for future data-source migration.

Phase 1 intentionally does not wire this package into the production
RealDataConnector flow.
"""

from .base import DataProvider
from .provider_router import ProviderRouter, ProviderRoutingError
from .schemas import (
    CANONICAL_RAW_BLOCKS,
    CANONICAL_RAW_TOP_LEVEL_KEYS,
    ProviderCapabilities,
    ProviderMode,
    ProviderSelection,
    missing_canonical_raw_keys,
    parse_provider_mode,
)
from .token_safety import mask_secret, sanitize_exception_message, sanitize_text

__all__ = [
    "CANONICAL_RAW_BLOCKS",
    "CANONICAL_RAW_TOP_LEVEL_KEYS",
    "DataProvider",
    "ProviderCapabilities",
    "ProviderMode",
    "ProviderRouter",
    "ProviderRoutingError",
    "ProviderSelection",
    "mask_secret",
    "missing_canonical_raw_keys",
    "parse_provider_mode",
    "sanitize_exception_message",
    "sanitize_text",
]

