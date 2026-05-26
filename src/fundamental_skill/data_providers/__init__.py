# -*- coding: utf-8 -*-
"""Provider abstraction package for data-source migration.

Phase 3 adds mocked TushareProvider MVP pieces while the production
RealDataConnector runner path remains unchanged.
"""

from .akshare_provider import AKSHARE_RAW_BLOCKS, AkShareProvider
from .base import DataProvider
from .comparison_artifacts import (
    BASE_ARTIFACT_NAMES,
    P1_ARTIFACT_NAMES,
    CodeComparisonArtifacts,
    ComparisonArtifactError,
    ComparisonArtifactPlan,
    plan_comparison_artifacts,
)
from .diff_classifier import DiffCategory, DiffItem, classify_field_diff
from .provider_router import ProviderRouter, ProviderRoutingError
from .real_token_smoke_gate import RealTokenSmokeGate, RealTokenSmokeGateError
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
from .token_leak_scanner import TokenLeakError, TokenLeakFinding, TokenLeakScanResult, scan_for_token_leaks
from .tushare_client import (
    TushareClient,
    TushareClientError,
    TushareMalformedResponseError,
    TusharePermissionError,
    TushareRateLimitError,
)
from .tushare_provider import TushareProvider, TushareProviderError
from .tushare_sdk_transport import TushareSdkTransport, TushareSdkTransportError

__all__ = [
    "CANONICAL_RAW_BLOCKS",
    "CANONICAL_RAW_TOP_LEVEL_KEYS",
    "AKSHARE_RAW_BLOCKS",
    "BASE_ARTIFACT_NAMES",
    "P1_ARTIFACT_NAMES",
    "AkShareProvider",
    "CodeComparisonArtifacts",
    "ComparisonArtifactError",
    "ComparisonArtifactPlan",
    "DataProvider",
    "DiffCategory",
    "DiffItem",
    "ProviderCapabilities",
    "ProviderMode",
    "ProviderRouter",
    "ProviderRoutingError",
    "ProviderSelection",
    "RealTokenSmokeGate",
    "RealTokenSmokeGateError",
    "TushareClient",
    "TushareClientError",
    "TushareMalformedResponseError",
    "TusharePermissionError",
    "TushareProvider",
    "TushareProviderError",
    "TushareRateLimitError",
    "TushareSdkTransport",
    "TushareSdkTransportError",
    "TokenLeakError",
    "TokenLeakFinding",
    "TokenLeakScanResult",
    "classify_field_diff",
    "mask_secret",
    "missing_canonical_raw_keys",
    "plan_comparison_artifacts",
    "parse_provider_mode",
    "scan_for_token_leaks",
    "sanitize_exception_message",
    "sanitize_text",
]
