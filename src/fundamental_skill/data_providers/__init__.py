# -*- coding: utf-8 -*-
"""Provider abstraction package for data-source migration.

Phase 3 adds mocked TushareProvider MVP pieces while the production
RealDataConnector runner path remains unchanged.
"""

from .akshare_provider import AKSHARE_RAW_BLOCKS, AkShareProvider
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
from .tushare_client import (
    TushareClient,
    TushareClientError,
    TushareMalformedResponseError,
    TusharePermissionError,
    TushareRateLimitError,
)
from .tushare_provider import TushareProvider, TushareProviderError

__all__ = [
    "CANONICAL_RAW_BLOCKS",
    "CANONICAL_RAW_TOP_LEVEL_KEYS",
    "AKSHARE_RAW_BLOCKS",
    "AkShareProvider",
    "DataProvider",
    "ProviderCapabilities",
    "ProviderMode",
    "ProviderRouter",
    "ProviderRoutingError",
    "ProviderSelection",
    "TushareClient",
    "TushareClientError",
    "TushareMalformedResponseError",
    "TusharePermissionError",
    "TushareProvider",
    "TushareProviderError",
    "TushareRateLimitError",
    "mask_secret",
    "missing_canonical_raw_keys",
    "parse_provider_mode",
    "sanitize_exception_message",
    "sanitize_text",
]
