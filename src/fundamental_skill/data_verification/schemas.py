# -*- coding: utf-8 -*-
"""Stable enums and schema constants for official verification."""

from __future__ import annotations

from enum import Enum


OFFICIAL_METRIC_FACT_VERSION = "official_metric_fact.v1"
PROVIDER_OFFICIAL_CONFLICT_VERSION = "provider_official_conflict.v1"
OFFICIAL_SOURCE_CANDIDATE_VERSION = "official_source_candidate.v1"
OFFICIAL_VERIFICATION_RUN_SUMMARY_VERSION = "official_verification_run_summary.v1"
BLOCKED_UNTIL_REVIEW_ITEM_VERSION = "blocked_until_review_item.v1"


class SourceType(str, Enum):
    CNINFO_OFFICIAL_PDF = "cninfo_official_pdf"
    SSE_EXCHANGE_ANNOUNCEMENT = "sse_exchange_official_announcement"
    LOCAL_OFFICIAL_CACHE = "local_official_cache"
    MIRROR_THIRD_PARTY_PAGE = "mirror_third_party_page"
    PROVIDER_ENDPOINT = "provider_endpoint"


class VerificationStatus(str, Enum):
    CANDIDATE = "candidate"
    VERIFIED = "verified"
    CONFLICT = "conflict"
    BLOCKED = "blocked"


class OfficialConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConflictType(str, Enum):
    EXACT_MATCH = "exact_match"
    ROUNDING_TOLERANCE = "rounding_tolerance"
    UNIT_MISMATCH = "unit_mismatch"
    PERIOD_MISMATCH = "period_mismatch"
    RAW_FIELD_MISMATCH = "raw_field_mismatch"
    ADJUSTED_BASIS_MISMATCH = "adjusted_before_after_mismatch"
    NUMERATOR_POLICY_CONFLICT = "numerator_policy_conflict"
    OFFICIAL_PROVIDER_CONFLICT = "official_provider_conflict"
    PROVIDER_PROVIDER_CONFLICT = "provider_provider_conflict"
    EXTRACTION_QUALITY_LOW = "extraction_quality_low"
    MISSING_DEPENDENCY = "missing_dependency"


class ExtractionQuality(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PeriodType(str, Enum):
    FY = "FY"
    H1 = "H1"
    Q1 = "Q1"
    Q3 = "Q3"
    ANNUAL = "annual"
    SEMIANNUAL = "semiannual"
    QUARTERLY = "quarterly"


class NormalizedUnit(str, Enum):
    CNY = "CNY"
    PERCENT_POINT = "percent_point"
    RATIO = "ratio"
    DAYS = "days"
    COUNT = "count"
    TEXT = "text"


class MetricType(str, Enum):
    DIRECT = "direct"
    DERIVED = "derived"
    PROXY = "proxy"
    DEFERRED = "deferred"


class StatementScope(str, Enum):
    CONSOLIDATED = "consolidated"
    PARENT_COMPANY = "parent_company"
    UNKNOWN = "unknown"


class AnnouncementType(str, Enum):
    ANNUAL_REPORT = "annual_report"
    SEMIANNUAL_REPORT = "semiannual_report"
    QUARTERLY_REPORT = "quarterly_report"
    OFFICIAL_ANNOUNCEMENT = "official_announcement"
    OTHER_OFFICIAL_DISCLOSURE = "other_official_disclosure"


class SourceStatus(str, Enum):
    CANDIDATE = "candidate"
    VERIFIED = "verified"
    REJECTED = "rejected"
    CONFLICT = "conflict"
    BLOCKED = "blocked"


class ResolutionStatus(str, Enum):
    UNRESOLVED = "unresolved"
    RESOLVED = "resolved"
    RETAINED_FOR_REVIEW = "retained_for_review"
    BLOCKED = "blocked"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    BLOCKER = "blocker"


class PromotionGateResult(str, Enum):
    EXACT_MATCH = "exact_match"
    ROUNDING_TOLERANCE = "rounding_tolerance"
    UNIT_MISMATCH = "unit_mismatch"
    PERIOD_MISMATCH = "period_mismatch"
    RAW_FIELD_MISMATCH = "raw_field_mismatch"
    ADJUSTED_BASIS_MISMATCH = "adjusted_before_after_mismatch"
    NUMERATOR_POLICY_CONFLICT = "numerator_policy_conflict"
    OFFICIAL_PROVIDER_CONFLICT = "official_provider_conflict"
    PROVIDER_PROVIDER_CONFLICT = "provider_provider_conflict"
    EXTRACTION_QUALITY_LOW = "extraction_quality_low"
    MISSING_DEPENDENCY = "missing_dependency"


PROMOTABLE_GATE_RESULTS = {
    PromotionGateResult.EXACT_MATCH.value,
    PromotionGateResult.ROUNDING_TOLERANCE.value,
}

OFFICIAL_SOURCE_TYPES = {
    SourceType.CNINFO_OFFICIAL_PDF.value,
    SourceType.SSE_EXCHANGE_ANNOUNCEMENT.value,
    SourceType.LOCAL_OFFICIAL_CACHE.value,
}

DISCOVERY_ONLY_SOURCE_TYPES = {
    SourceType.MIRROR_THIRD_PARTY_PAGE.value,
}

PROVIDER_SOURCE_TYPES = {
    SourceType.PROVIDER_ENDPOINT.value,
}

OFFICIAL_SOURCE_REQUIRED_FIELDS = (
    "candidate_title",
    "disclosure_date",
    "period",
    "announcement_type",
    "file_sha256",
)

OFFICIAL_SOURCE_CANDIDATE_REQUIRED_KEYS = (
    "source_candidate_id",
    "stock_code",
    "period",
    "announcement_type",
    "candidate_source_type",
    "candidate_url",
    "candidate_title",
    "disclosure_date",
    "source_discovery_method",
    "is_official_candidate",
    "is_mirror",
    "accepted_as_official",
    "rejection_reason",
    "file_sha256",
    "local_cache_path",
    "source_refresh_policy",
    "registry_version",
    "not_for_trading_advice",
)

OFFICIAL_METRIC_FACT_REQUIRED_KEYS = (
    "fact_id",
    "stock_code",
    "company_name",
    "metric_id",
    "metric_policy_id",
    "period_key",
    "period_end_date",
    "period_type",
    "statement_scope",
    "announcement_title",
    "announcement_type",
    "disclosure_date",
    "source_ref",
    "file_sha256",
    "page_or_anchor",
    "table_title",
    "row_label",
    "column_label",
    "raw_value",
    "raw_unit",
    "normalized_value",
    "normalized_unit",
    "dependency_refs",
    "extraction_method",
    "extraction_quality",
    "verification_status",
    "official_confidence",
    "conflict_refs",
    "caveats",
    "verifier",
    "reviewer",
    "not_for_trading_advice",
)

PROVIDER_OFFICIAL_CONFLICT_REQUIRED_KEYS = (
    "conflict_id",
    "stock_code",
    "metric_id",
    "period_key",
    "provider_fact_ref",
    "official_fact_ref",
    "provider_value",
    "official_value",
    "normalized_unit",
    "conflict_type",
    "severity",
    "resolution_status",
    "review_note",
    "preferred_value_candidate",
    "preferred_value_basis",
    "created_at_utc",
    "reviewer",
    "not_for_trading_advice",
)

BLOCKED_UNTIL_REVIEW_ITEM_REQUIRED_KEYS = (
    "blocked_item_id",
    "stock_code",
    "metric_id",
    "period_key",
    "blocked_reason",
    "missing_dependency",
    "source_gap",
    "extraction_quality",
    "next_action",
    "review_owner",
    "created_at_utc",
    "resolved_at_utc",
    "resolution_ref",
    "not_for_trading_advice",
)

OFFICIAL_VERIFICATION_RUN_SUMMARY_REQUIRED_KEYS = (
    "run_id",
    "run_started_at_utc",
    "run_finished_at_utc",
    "stock_code",
    "schema_version",
    "source_registry_version",
    "metric_count",
    "verified_count",
    "candidate_count",
    "conflict_count",
    "blocked_count",
    "extraction_quality_summary",
    "unresolved_conflict_refs",
    "blocked_item_refs",
    "not_for_trading_advice",
)

DERIVED_METRIC_DEPENDENCIES = {
    "gross_margin": ("revenue", "operating_cost"),
    "net_margin": ("net_profit", "revenue"),
    "operating_cash_flow_to_net_profit": ("operating_cash_flow", "net_profit"),
    "accounts_receivable_turnover_days": ("accounts_receivable_begin", "accounts_receivable_end", "revenue", "flow_days"),
    "r_and_d_expense_ratio": ("r_and_d_expense", "revenue"),
    "contract_liabilities_to_revenue": ("contract_liabilities", "revenue"),
}

PROXY_METRIC_IDS = {
    "contract_liabilities",
    "contract_liabilities_to_revenue",
}

DEFERRED_METRIC_IDS = {
    "segment_business_composition",
    "business_composition",
    "segment_composition",
}

STOCK_FLOW_RATIO_METRICS = {
    "accounts_receivable_to_revenue",
    "contract_liabilities_to_revenue",
    "inventory_to_revenue",
}

Q1_NOT_ANNUALIZED_PERIOD_TYPES = {
    PeriodType.Q1.value,
    PeriodType.QUARTERLY.value,
}


def enum_values(enum_cls: type[Enum]) -> tuple[str, ...]:
    """Return stable string values for a string enum."""

    return tuple(item.value for item in enum_cls)
