# -*- coding: utf-8 -*-
"""Stable output contract for the A-share fundamental analysis skill."""

from .schema import (
    Catalyst,
    DataSource,
    Evidence,
    FinancialQuality,
    FundamentalAnalysisResult,
    IndustryCycle,
    InvalidationCondition,
    RiskFlag,
    ThesisCheck,
    TrackIndicator,
    ValuationView,
)
from .classification_schema import (
    ClassificationEvidence,
    FundamentalFramework,
    StockClassificationResult,
)
from .readiness_schema import DataReadinessPlan, FieldReadiness, FieldRequirement
from .raw_schema import (
    BasicInfoInput,
    BusinessCompositionInput,
    FinancialMetricInput,
    NewsItemInput,
    NormalizedFundamentalInput,
    RawBlockStatus,
    ValuationMetricInput,
)
from .validators import (
    assert_valid_result,
    validate_no_trading_instruction,
    validate_result,
)

__all__ = [
    "Catalyst",
    "DataSource",
    "DataReadinessPlan",
    "Evidence",
    "FinancialQuality",
    "ClassificationEvidence",
    "FundamentalFramework",
    "FundamentalAnalysisResult",
    "IndustryCycle",
    "InvalidationCondition",
    "RiskFlag",
    "ThesisCheck",
    "TrackIndicator",
    "ValuationView",
    "assert_valid_result",
    "BasicInfoInput",
    "BusinessCompositionInput",
    "FinancialMetricInput",
    "FieldReadiness",
    "FieldRequirement",
    "NewsItemInput",
    "NormalizedFundamentalInput",
    "RawBlockStatus",
    "StockClassificationResult",
    "ValuationMetricInput",
    "validate_no_trading_instruction",
    "validate_result",
]
