# -*- coding: utf-8 -*-
"""Request-driven synthetic official disclosure dry-run integration.

This module is intentionally standalone. It only accepts explicit in-memory
payloads and does not perform IO, network access, provider lookup, downloads,
PDF parsing, metric extraction, report generation, or artifact writes.
"""

from __future__ import annotations

import copy
import re
from collections.abc import Mapping, Sequence
from typing import Any

from .official_disclosure_discovery_candidate import (
    normalize_official_disclosure_discovery_candidate,
)
from .official_disclosure_request import (
    ALLOWED_DISCOVERY_SCOPES,
    FORBIDDEN_DISCOVERY_SCOPES,
    FORBIDDEN_SOURCE_TYPES,
    SCHEMA_VERSION as OFFICIAL_DISCLOSURE_DISCOVERY_REQUEST_VERSION,
    normalize_official_disclosure_request,
    validate_official_disclosure_request,
)
from .schemas import (
    OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_DISCOVERY_ONLY_SOURCE_TYPES,
    OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_LOCAL_CACHE_SOURCE_TYPES,
    OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_PROVIDER_SOURCE_TYPES,
)
from .synthetic_official_disclosure_pipeline_dry_run import (
    build_synthetic_official_disclosure_pipeline_dry_run_result,
    validate_synthetic_official_disclosure_pipeline_dry_run_result,
)
from .validators import OfficialVerificationValidationError


REQUEST_SYNTHETIC_DRY_RUN_RESULT_SCHEMA_VERSION = (
    "official_disclosure_request_synthetic_dry_run_result.v1"
)

REQUEST_SYNTHETIC_DRY_RUN_RESULT_REQUIRED_KEYS = (
    "schema_version",
    "request",
    "security_identity",
    "input_synthetic_candidates",
    "request_compatible_candidates",
    "request_rejected_candidates",
    "synthetic_dry_run_result",
    "merged_blocked_reasons",
    "merged_data_gap_plan",
    "request_caveats",
    "dry_run_caveats",
    "final_caveats",
    "not_for_trading_advice",
)

REJECTION_MISSING_REQUEST = "missing_request"
REJECTION_INVALID_REQUEST = "invalid_request"
REJECTION_REQUEST_BLOCKED = "request_blocked"
REJECTION_MISSING_CANDIDATES = "missing_candidates"
REJECTION_CANDIDATES_NOT_LIST = "candidates_not_list"
REJECTION_NO_SYNTHETIC_CANDIDATES = "no_synthetic_candidates"
REJECTION_ALL_CANDIDATES_INCOMPATIBLE = "all_synthetic_candidates_incompatible"
REJECTION_MIXED_CANDIDATE_COMPATIBILITY = "mixed_compatible_and_incompatible_candidates"
REJECTION_STOCK_CODE_MISMATCH = "stock_code_mismatch"
REJECTION_EXCHANGE_MISMATCH = "exchange_mismatch"
REJECTION_COMPANY_NAME_MISMATCH = "company_name_mismatch"
REJECTION_PERIOD_MISMATCH = "period_mismatch"
REJECTION_ANNOUNCEMENT_TYPE_MISMATCH = "announcement_type_mismatch"
REJECTION_SOURCE_TYPE_NOT_ALLOWED = "source_type_not_allowed"
REJECTION_FORBIDDEN_SOURCE_KIND = "forbidden_source_kind"
REJECTION_FORBIDDEN_SCOPE_INTENT = "forbidden_scope_intent"
REJECTION_FORBIDDEN_MARKER = "forbidden_marker"
REJECTION_CANDIDATE_MUST_BE_MAPPING = "candidate_must_be_mapping"
REJECTION_IDENTITY_CONFIDENCE_PROMOTION_FORBIDDEN = (
    "identity_confidence_promotion_forbidden"
)
REJECTION_COMPANY_MATCH_PROMOTION_FORBIDDEN = "company_match_promotion_forbidden"
REJECTION_DRY_RUN_FAILED = "synthetic_dry_run_failed"
REJECTION_RESULT_BLOCKED_REASONS_MISSING = "merged_blocked_reasons_missing"
REJECTION_RESULT_DATA_GAP_PLAN_MISSING = "merged_data_gap_plan_missing"

DATA_GAP_PROVIDE_VALID_REQUEST = "provide_valid_official_disclosure_request"
DATA_GAP_RESOLVE_REQUEST_BLOCKERS = "resolve_request_blocked_reasons"
DATA_GAP_PROVIDE_SYNTHETIC_CANDIDATES = "provide_explicit_synthetic_discovery_candidates"
DATA_GAP_PROVIDE_COMPATIBLE_CANDIDATE = (
    "provide_request_compatible_synthetic_discovery_candidate"
)
DATA_GAP_CORRECT_INCOMPATIBLE_CANDIDATES = (
    "remove_or_correct_request_incompatible_candidates"
)
DATA_GAP_REVIEW_DRY_RUN_BLOCKERS = "resolve_synthetic_dry_run_blocked_reasons"

FINAL_CAVEATS = (
    "request_driven_synthetic_dry_run_only",
    "explicit_payload_only",
    "in_memory_only",
    "readiness_only",
)

_MISSING = object()
_CAMEL_SPLIT_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_TOKEN_RE = re.compile(r"\btoken\b", flags=re.IGNORECASE)

_SOURCE_URL_KEY_NAMES = {"source_url", "candidate_url"}
_CANDIDATE_SOURCE_TYPE_ALIASES = {
    "sse_exchange_official_announcement": "sse_exchange_announcement",
}
_FORBIDDEN_CANDIDATE_SOURCE_TYPES = (
    set(FORBIDDEN_SOURCE_TYPES)
    | set(OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_PROVIDER_SOURCE_TYPES)
    | set(OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_DISCOVERY_ONLY_SOURCE_TYPES)
    | set(OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_LOCAL_CACHE_SOURCE_TYPES)
)

_FORBIDDEN_KEY_MARKERS = (
    "token",
    "env",
    "tushare_token",
    "tushare_token_txt",
    "provider_live",
    "provider_lookup",
    "provider_adapter",
    "akshare",
    "tushare",
    "network",
    "http",
    "fetch",
    "download",
    "cninfo_live",
    "sse_live",
    "pdf_parser",
    "pdf_table_extractor",
    "table_extractor",
    "parse_pdf",
    "metric_extraction",
    "official_metric_fact",
    "provider_official_conflict",
    "report_v1",
    "accepted_manifest",
    "accepted_manifest_write",
    "output_baseline",
    "output_baseline_write",
    "fixture_write",
    "buy",
    "sell",
    "hold",
    "target_price",
    "portfolio",
    "position",
    "technical_signal",
    "trading_advice",
    "investment_advice",
)

_FORBIDDEN_VALUE_MARKERS = (
    "tushare_token",
    "tushare_token.txt",
    ".env",
    "provider live",
    "provider lookup",
    "provider adapter",
    "akshare",
    "tushare",
    "live discovery",
    "network",
    "http",
    "fetch",
    "download",
    "cninfo live",
    "sse live",
    "pdf parser",
    "table extractor",
    "pdf table extractor",
    "parse pdf",
    "parse_pdf",
    "metric extraction",
    "official_metric_fact",
    "provider_official_conflict",
    "report v1",
    "accepted manifest write",
    "accepted_manifest_write",
    "accepted manifest",
    "accepted_manifest",
    "output baseline write",
    "output_baseline_write",
    "output baseline",
    "output_baseline",
    "fixture write",
    "fixture_write",
    "target price",
    "price target",
    "technical signal",
    "trading advice",
    "investment advice",
)

_FORBIDDEN_CJK_MARKERS = (
    "涔板叆",
    "鍗栧嚭",
    "鎸佹湁",
    "鐩爣浠?",
    "浠撲綅",
    "缁勫悎",
    "鎶€鏈俊鍙?",
    "鎶曡祫寤鸿",
    "涓嬭浇",
    "缃戠粶",
    "鑱旂綉",
    "瑙ｆ瀽PDF",
    "PDF瑙ｆ瀽",
    "琛ㄦ牸鎶藉彇",
    "鎸囨爣鎶藉彇",
    "姝ｅ紡鐮旀姤",
    "杈撳嚭鍩虹嚎",
    "鍐欏叆fixture",
    "鍐欏叆accepted manifest",
    "璇诲彇token",
    "璇诲彇.env",
    "璇诲彇tushare_token",
    "璋冪敤AkShare",
    "璋冪敤Tushare",
    "璋冪敤CNInfo live",
    "璋冪敤SSE live",
    "璋冪敤provider",
)

_SHORT_WORD_VALUE_PATTERNS = tuple(
    re.compile(pattern, flags=re.IGNORECASE)
    for pattern in (
        r"\bbuy\b",
        r"\bsell\b",
        r"\bhold\b",
        r"\bhttp\b",
        r"\bfetch\b",
        r"\bdownload\b",
        r"\bnetwork\b",
        r"\bportfolio\b",
        r"\bposition\b",
    )
)


class RequestSyntheticDryRunIntegrationSafetyError(
    OfficialVerificationValidationError
):
    """Raised when request-driven dry-run payloads contain forbidden markers."""

    def __init__(self, marker: str, path: str) -> None:
        super().__init__(f"forbidden request synthetic dry-run marker at {path}: {marker}")
        self.marker = marker
        self.path = path


def build_request_synthetic_dry_run_integration_result(
    request: Any = _MISSING,
    input_synthetic_candidates: Any = _MISSING,
    *,
    source_conflicts: Sequence[Mapping[str, Any] | str] | None = None,
    caveats: Sequence[str] | None = None,
    not_for_trading_advice: bool = True,
) -> dict[str, Any]:
    """Build a request-driven dry-run result from explicit in-memory payloads."""

    request_safety_reason = None
    if request is _MISSING or request is None:
        normalized_request = _empty_blocked_request(REJECTION_MISSING_REQUEST)
    else:
        try:
            assert_no_request_dry_run_forbidden_markers(
                _with_not_for_trading_advice_normalized_for_marker_scan(request)
            )
        except RequestSyntheticDryRunIntegrationSafetyError:
            request_safety_reason = REJECTION_FORBIDDEN_MARKER
        normalized_request = _normalize_or_validate_request(request)

    request_blocked_reasons = list(normalized_request.get("blocked_reasons", []))
    if request_safety_reason:
        request_blocked_reasons = [request_safety_reason]
        normalized_request = _sanitize_for_result(normalized_request)

    if not isinstance(not_for_trading_advice, bool) or not_for_trading_advice is not True:
        request_blocked_reasons = merge_blocked_reasons(
            request_blocked_reasons,
            ["not_for_trading_advice_required"],
        )

    if _request_is_blocked(normalized_request, request_blocked_reasons):
        reasons = _prefix_reasons("request", request_blocked_reasons or [REJECTION_REQUEST_BLOCKED])
        result = _assemble_result(
            request=normalized_request,
            input_synthetic_candidates=[],
            request_compatible_candidates=[],
            request_rejected_candidates=[],
            synthetic_dry_run_result=None,
            merged_blocked_reasons=reasons,
            merged_data_gap_plan=[DATA_GAP_RESOLVE_REQUEST_BLOCKERS],
            request_caveats=_safe_list(normalized_request.get("caveats")),
            dry_run_caveats=[],
            extra_caveats=caveats,
        )
        validate_request_synthetic_dry_run_integration_result(result)
        return result

    if input_synthetic_candidates is _MISSING or input_synthetic_candidates is None:
        result = _assemble_result(
            request=normalized_request,
            input_synthetic_candidates=[],
            request_compatible_candidates=[],
            request_rejected_candidates=[],
            synthetic_dry_run_result=None,
            merged_blocked_reasons=[f"request_candidate:{REJECTION_MISSING_CANDIDATES}"],
            merged_data_gap_plan=[DATA_GAP_PROVIDE_SYNTHETIC_CANDIDATES],
            request_caveats=_safe_list(normalized_request.get("caveats")),
            dry_run_caveats=[],
            extra_caveats=caveats,
        )
        validate_request_synthetic_dry_run_integration_result(result)
        return result

    if not isinstance(input_synthetic_candidates, list):
        result = _assemble_result(
            request=normalized_request,
            input_synthetic_candidates=[],
            request_compatible_candidates=[],
            request_rejected_candidates=[],
            synthetic_dry_run_result=None,
            merged_blocked_reasons=[f"request_candidate:{REJECTION_CANDIDATES_NOT_LIST}"],
            merged_data_gap_plan=[DATA_GAP_PROVIDE_SYNTHETIC_CANDIDATES],
            request_caveats=_safe_list(normalized_request.get("caveats")),
            dry_run_caveats=[],
            extra_caveats=caveats,
        )
        validate_request_synthetic_dry_run_integration_result(result)
        return result

    if not input_synthetic_candidates:
        result = _assemble_result(
            request=normalized_request,
            input_synthetic_candidates=[],
            request_compatible_candidates=[],
            request_rejected_candidates=[],
            synthetic_dry_run_result=None,
            merged_blocked_reasons=[f"request_candidate:{REJECTION_NO_SYNTHETIC_CANDIDATES}"],
            merged_data_gap_plan=[DATA_GAP_PROVIDE_SYNTHETIC_CANDIDATES],
            request_caveats=_safe_list(normalized_request.get("caveats")),
            dry_run_caveats=[],
            extra_caveats=caveats,
        )
        validate_request_synthetic_dry_run_integration_result(result)
        return result

    compatible_candidates, rejected_candidates = filter_candidates_by_request(
        normalized_request,
        input_synthetic_candidates,
    )

    if not compatible_candidates:
        result = _assemble_result(
            request=normalized_request,
            input_synthetic_candidates=input_synthetic_candidates,
            request_compatible_candidates=[],
            request_rejected_candidates=rejected_candidates,
            synthetic_dry_run_result=None,
            merged_blocked_reasons=[
                f"request_candidate:{REJECTION_ALL_CANDIDATES_INCOMPATIBLE}"
            ],
            merged_data_gap_plan=[DATA_GAP_PROVIDE_COMPATIBLE_CANDIDATE],
            request_caveats=_safe_list(normalized_request.get("caveats")),
            dry_run_caveats=[],
            extra_caveats=caveats,
        )
        validate_request_synthetic_dry_run_integration_result(result)
        return result

    dry_run_result: dict[str, Any] | None = None
    dry_run_error_reasons: list[str] = []
    try:
        dry_run_result = build_synthetic_official_disclosure_pipeline_dry_run_result(
            stock_code=str(normalized_request.get("stock_code") or ""),
            company_name=_company_name_for_dry_run(normalized_request, compatible_candidates),
            query_period={
                "period_key": str(normalized_request.get("query_period") or ""),
                "period_end_date": str(normalized_request.get("period_end_date") or ""),
            },
            requested_announcement_type=str(
                normalized_request.get("requested_announcement_type") or ""
            ),
            input_discovery_candidates=compatible_candidates,
            source_conflicts=source_conflicts,
            caveats=merge_caveats(
                _safe_list(normalized_request.get("caveats")),
                _candidate_caveats(compatible_candidates),
                ["request_driven_integration"],
            ),
            not_for_trading_advice=True,
        )
    except OfficialVerificationValidationError:
        dry_run_error_reasons.append(REJECTION_DRY_RUN_FAILED)

    dry_run_blocked_reasons = (
        _safe_list(dry_run_result.get("blocked_reasons")) if dry_run_result else []
    )
    dry_run_data_gap_plan = (
        _safe_list(dry_run_result.get("data_gap_plan")) if dry_run_result else []
    )
    dry_run_caveats = _safe_list(dry_run_result.get("caveats")) if dry_run_result else []

    integration_blocked_reasons: list[str] = []
    integration_data_gap_plan: list[str] = []
    if rejected_candidates:
        integration_blocked_reasons.append(
            f"request_candidate:{REJECTION_MIXED_CANDIDATE_COMPATIBILITY}"
        )
        integration_data_gap_plan.append(DATA_GAP_CORRECT_INCOMPATIBLE_CANDIDATES)
    if dry_run_error_reasons:
        integration_blocked_reasons.extend(_prefix_reasons("dry_run", dry_run_error_reasons))
        integration_data_gap_plan.append(DATA_GAP_REVIEW_DRY_RUN_BLOCKERS)

    merged_blocked_reasons = merge_blocked_reasons(
        integration_blocked_reasons,
        _prefix_reasons("dry_run", dry_run_blocked_reasons),
    )
    merged_data_gap_plan = merge_data_gap_plan(
        integration_data_gap_plan,
        dry_run_data_gap_plan,
    )

    result = _assemble_result(
        request=normalized_request,
        input_synthetic_candidates=input_synthetic_candidates,
        request_compatible_candidates=compatible_candidates,
        request_rejected_candidates=rejected_candidates,
        synthetic_dry_run_result=dry_run_result,
        merged_blocked_reasons=merged_blocked_reasons,
        merged_data_gap_plan=merged_data_gap_plan,
        request_caveats=_safe_list(normalized_request.get("caveats")),
        dry_run_caveats=dry_run_caveats,
        extra_caveats=caveats,
    )
    validate_request_synthetic_dry_run_integration_result(result)
    return result


def validate_request_synthetic_dry_run_integration_result(
    result: Mapping[str, Any],
) -> None:
    """Validate the request-driven integration envelope and safety boundary."""

    _require_mapping(result, "request synthetic dry-run integration result")
    _require_keys(result, REQUEST_SYNTHETIC_DRY_RUN_RESULT_REQUIRED_KEYS)
    assert_no_request_dry_run_forbidden_markers(result)

    if result["schema_version"] != REQUEST_SYNTHETIC_DRY_RUN_RESULT_SCHEMA_VERSION:
        raise OfficialVerificationValidationError(
            "request synthetic dry-run result schema_version is unsupported"
        )
    if result.get("not_for_trading_advice") is not True or not isinstance(
        result.get("not_for_trading_advice"), bool
    ):
        raise OfficialVerificationValidationError("not_for_trading_advice must be bool true")

    for field in (
        "input_synthetic_candidates",
        "request_compatible_candidates",
        "request_rejected_candidates",
        "merged_blocked_reasons",
        "merged_data_gap_plan",
        "request_caveats",
        "dry_run_caveats",
        "final_caveats",
    ):
        if not isinstance(result.get(field), list):
            raise OfficialVerificationValidationError(f"{field} must be a list")

    if result["merged_blocked_reasons"] and not result["merged_data_gap_plan"]:
        raise OfficialVerificationValidationError(REJECTION_RESULT_DATA_GAP_PLAN_MISSING)

    request = result.get("request")
    if isinstance(request, Mapping) and request.get("blocked_reasons"):
        _require_merged_blocked_context(result)
    if (
        result.get("input_synthetic_candidates")
        and result.get("request_rejected_candidates")
        and not result.get("request_compatible_candidates")
    ):
        _require_merged_blocked_context(result)
    if result.get("request_rejected_candidates") and result.get(
        "request_compatible_candidates"
    ):
        _require_merged_blocked_context(result)

    synthetic_dry_run_result = result.get("synthetic_dry_run_result")
    if synthetic_dry_run_result is not None:
        _require_mapping(synthetic_dry_run_result, "synthetic_dry_run_result")
        validate_synthetic_official_disclosure_pipeline_dry_run_result(
            synthetic_dry_run_result
        )
        if synthetic_dry_run_result.get("blocked_reasons"):
            _require_merged_blocked_context(result)


def filter_candidates_by_request(
    request: Mapping[str, Any],
    candidates: list[Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split explicit candidates into request-compatible and rejected records."""

    compatible: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates):
        reasons = check_candidate_request_compatibility(request, candidate)
        if reasons:
            rejected.append(
                build_request_rejected_candidate(
                    candidate,
                    reasons,
                    input_index=index,
                )
            )
            continue
        compatible.append(normalize_official_disclosure_discovery_candidate(candidate))
    return compatible, rejected


def check_candidate_request_compatibility(
    request: Mapping[str, Any],
    candidate: Any,
) -> list[str]:
    """Return machine-readable request-candidate mismatch reasons."""

    if not isinstance(candidate, Mapping):
        return [REJECTION_CANDIDATE_MUST_BE_MAPPING]

    reasons: list[str] = []
    candidate_stock_code = _clean_string(candidate.get("stock_code"))
    candidate_exchange = _clean_string(candidate.get("exchange"))
    candidate_period_key = _clean_string(
        candidate.get("period_key", candidate.get("query_period"))
    )
    candidate_period_end_date = _clean_string(candidate.get("period_end_date"))
    candidate_announcement_type = _normalize_marker_text(
        candidate.get("announcement_type")
    )
    candidate_source_type = _canonical_candidate_source_type(candidate.get("source_type"))

    if candidate_stock_code != _clean_string(request.get("stock_code")):
        reasons.append(REJECTION_STOCK_CODE_MISMATCH)
    if candidate_exchange != _clean_string(request.get("exchange")):
        reasons.append(REJECTION_EXCHANGE_MISMATCH)

    request_company_name = _clean_string(request.get("company_name"))
    candidate_company_name = _clean_string(candidate.get("company_name"))
    if request_company_name and candidate_company_name and candidate_company_name != request_company_name:
        reasons.append(REJECTION_COMPANY_NAME_MISMATCH)

    if (
        candidate_period_key != _clean_string(request.get("query_period"))
        or candidate_period_end_date != _clean_string(request.get("period_end_date"))
    ):
        reasons.append(REJECTION_PERIOD_MISMATCH)

    if candidate_announcement_type != _clean_string(
        request.get("requested_announcement_type")
    ):
        reasons.append(REJECTION_ANNOUNCEMENT_TYPE_MISMATCH)

    allowed_source_types = request.get("allowed_source_types")
    if not isinstance(allowed_source_types, list) or candidate_source_type not in allowed_source_types:
        reasons.append(REJECTION_SOURCE_TYPE_NOT_ALLOWED)
    if candidate_source_type in _FORBIDDEN_CANDIDATE_SOURCE_TYPES:
        reasons.append(REJECTION_FORBIDDEN_SOURCE_KIND)

    if _candidate_has_forbidden_scope_intent(candidate):
        reasons.append(REJECTION_FORBIDDEN_SCOPE_INTENT)
    if _candidate_has_identity_promotion(candidate):
        reasons.append(REJECTION_IDENTITY_CONFIDENCE_PROMOTION_FORBIDDEN)
    if _candidate_has_company_match_promotion(candidate):
        reasons.append(REJECTION_COMPANY_MATCH_PROMOTION_FORBIDDEN)

    try:
        assert_no_request_dry_run_forbidden_markers(candidate)
    except RequestSyntheticDryRunIntegrationSafetyError:
        reasons.append(REJECTION_FORBIDDEN_MARKER)

    if not reasons:
        try:
            normalize_official_disclosure_discovery_candidate(candidate)
        except OfficialVerificationValidationError:
            reasons.append("candidate_normalization_failed")

    return _dedupe_keep_order(reasons)


def build_request_rejected_candidate(
    candidate: Any,
    reasons: Sequence[str],
    *,
    input_index: int | None = None,
) -> dict[str, Any]:
    """Build a sanitized request-candidate rejection record."""

    reason_list = _dedupe_keep_order([str(reason) for reason in reasons if reason])
    if not reason_list:
        reason_list = ["request_candidate_rejected"]

    record = {
        "input_index": -1 if input_index is None else input_index,
        "discovery_candidate_id": _candidate_field(candidate, "discovery_candidate_id"),
        "stock_code": _candidate_field(candidate, "stock_code"),
        "exchange": _candidate_field(candidate, "exchange"),
        "period_key": _candidate_field(candidate, "period_key"),
        "period_end_date": _candidate_field(candidate, "period_end_date"),
        "announcement_type": _candidate_field(candidate, "announcement_type"),
        "source_type": _candidate_field(candidate, "source_type"),
        "rejection_stage": "request_candidate_compatibility",
        "rejection_reason": reason_list[0],
        "rejection_reasons": reason_list,
        "candidate": _sanitize_for_result(candidate),
        "not_for_trading_advice": True,
    }
    assert_no_request_dry_run_forbidden_markers(record)
    return record


def merge_blocked_reasons(*reason_groups: Any) -> list[str]:
    """Merge nested blocked reason groups while preserving first-seen order."""

    return _dedupe_keep_order(_flatten_strings(reason_groups))


def merge_data_gap_plan(*plan_groups: Any) -> list[str]:
    """Merge nested data-gap plan groups while preserving first-seen order."""

    return _dedupe_keep_order(_flatten_strings(plan_groups))


def merge_caveats(*caveat_groups: Any) -> list[str]:
    """Merge caveats without allowing candidates to erase request caveats."""

    return _dedupe_keep_order(_flatten_strings(caveat_groups))


def assert_no_request_dry_run_forbidden_markers(value: Any) -> None:
    """Recursively reject forbidden request-driven dry-run markers."""

    _assert_no_forbidden_markers(value, path="$", key_name="")


def can_enter_request_synthetic_dry_run(
    result: Mapping[str, Any],
    with_reason: bool = False,
) -> bool | tuple[bool, str | None]:
    """Return whether a request-driven dry-run result is unblocked."""

    try:
        validate_request_synthetic_dry_run_integration_result(result)
    except OfficialVerificationValidationError as exc:
        return (False, str(exc)) if with_reason else False

    blocked_reasons = result.get("merged_blocked_reasons", [])
    allowed = (
        result.get("schema_version") == REQUEST_SYNTHETIC_DRY_RUN_RESULT_SCHEMA_VERSION
        and result.get("not_for_trading_advice") is True
        and isinstance(blocked_reasons, list)
        and not blocked_reasons
        and result.get("synthetic_dry_run_result") is not None
    )
    reason = None if allowed else _first_string(blocked_reasons) or "blocked"
    if with_reason:
        return allowed, reason
    return allowed


def _normalize_or_validate_request(request: Any) -> dict[str, Any]:
    if isinstance(request, Mapping) and request.get(
        "schema_version"
    ) == OFFICIAL_DISCLOSURE_DISCOVERY_REQUEST_VERSION and "request_id" in request:
        return validate_official_disclosure_request(request)
    return normalize_official_disclosure_request(request)


def _empty_blocked_request(reason: str) -> dict[str, Any]:
    request = normalize_official_disclosure_request(None)
    request["blocked_reasons"] = merge_blocked_reasons(
        request.get("blocked_reasons", []),
        [reason],
    )
    request["rejection_reason"] = request["blocked_reasons"][0]
    return request


def _request_is_blocked(request: Mapping[str, Any], reasons: Sequence[str]) -> bool:
    return bool(reasons) or request.get("not_for_trading_advice") is not True


def _assemble_result(
    *,
    request: Mapping[str, Any],
    input_synthetic_candidates: Any,
    request_compatible_candidates: Sequence[Mapping[str, Any]],
    request_rejected_candidates: Sequence[Mapping[str, Any]],
    synthetic_dry_run_result: Mapping[str, Any] | None,
    merged_blocked_reasons: Sequence[str],
    merged_data_gap_plan: Sequence[str],
    request_caveats: Sequence[str],
    dry_run_caveats: Sequence[str],
    extra_caveats: Sequence[str] | None,
) -> dict[str, Any]:
    merged_blocked = merge_blocked_reasons(merged_blocked_reasons)
    merged_data_gaps = merge_data_gap_plan(merged_data_gap_plan)
    if merged_blocked and not merged_data_gaps:
        merged_data_gaps = [DATA_GAP_REVIEW_DRY_RUN_BLOCKERS]

    result = {
        "schema_version": REQUEST_SYNTHETIC_DRY_RUN_RESULT_SCHEMA_VERSION,
        "request": _sanitize_for_result(request),
        "security_identity": _sanitize_for_result(request.get("security_identity")),
        "input_synthetic_candidates": _sanitize_input_candidate_list(
            input_synthetic_candidates
        ),
        "request_compatible_candidates": _sanitize_for_result(
            list(request_compatible_candidates)
        ),
        "request_rejected_candidates": _sanitize_for_result(
            list(request_rejected_candidates)
        ),
        "synthetic_dry_run_result": _sanitize_for_result(synthetic_dry_run_result),
        "merged_blocked_reasons": merged_blocked,
        "merged_data_gap_plan": merged_data_gaps,
        "request_caveats": _sanitize_for_result(list(request_caveats)),
        "dry_run_caveats": _sanitize_for_result(list(dry_run_caveats)),
        "final_caveats": merge_caveats(
            request_caveats,
            dry_run_caveats,
            extra_caveats,
            FINAL_CAVEATS,
        ),
        "not_for_trading_advice": True,
    }
    return result


def _sanitize_input_candidate_list(value: Any) -> list[Any]:
    if not isinstance(value, list):
        return []
    return _sanitize_for_result(value)


def _with_not_for_trading_advice_normalized_for_marker_scan(value: Any) -> Any:
    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key, nested in value.items():
            if _normalize_marker_text(key) == "not_for_trading_advice":
                normalized[str(key)] = True
            else:
                normalized[str(key)] = _with_not_for_trading_advice_normalized_for_marker_scan(
                    nested
                )
        return normalized
    if isinstance(value, list):
        return [
            _with_not_for_trading_advice_normalized_for_marker_scan(item)
            for item in value
        ]
    if isinstance(value, tuple):
        return [
            _with_not_for_trading_advice_normalized_for_marker_scan(item)
            for item in value
        ]
    return value


def _company_name_for_dry_run(
    request: Mapping[str, Any],
    compatible_candidates: Sequence[Mapping[str, Any]],
) -> str:
    request_company_name = _clean_string(request.get("company_name"))
    if request_company_name:
        return request_company_name
    for candidate in compatible_candidates:
        candidate_company_name = _clean_string(candidate.get("company_name"))
        if candidate_company_name:
            return candidate_company_name
    return "explicit synthetic company name unavailable"


def _candidate_caveats(candidates: Sequence[Mapping[str, Any]]) -> list[str]:
    caveats: list[str] = []
    for candidate in candidates:
        candidate_caveats = candidate.get("caveats")
        if isinstance(candidate_caveats, list):
            caveats.extend(str(caveat) for caveat in candidate_caveats)
    return _dedupe_keep_order(caveats)


def _candidate_has_forbidden_scope_intent(candidate: Mapping[str, Any]) -> bool:
    discovery_scope = _normalize_marker_text(candidate.get("discovery_scope"))
    if discovery_scope in set(FORBIDDEN_DISCOVERY_SCOPES) - set(ALLOWED_DISCOVERY_SCOPES):
        return True

    scan_payload = {
        "discovery_scope": candidate.get("discovery_scope"),
        "raw_candidate_metadata": candidate.get("raw_candidate_metadata"),
        "normalized_candidate_metadata": candidate.get("normalized_candidate_metadata"),
        "metadata": candidate.get("metadata"),
        "intent": candidate.get("intent"),
    }
    try:
        assert_no_request_dry_run_forbidden_markers(scan_payload)
    except RequestSyntheticDryRunIntegrationSafetyError:
        return True
    return False


def _candidate_has_identity_promotion(candidate: Mapping[str, Any]) -> bool:
    return _contains_normalized_marker(
        candidate,
        {
            "identity_confidence",
            "identity_confidence_high",
            "raise_identity_confidence",
            "promote_identity_confidence",
            "verified_identity",
        },
    )


def _candidate_has_company_match_promotion(candidate: Mapping[str, Any]) -> bool:
    return _contains_normalized_marker(
        candidate,
        {
            "verified_company_match",
            "company_name_verified",
            "verified_company_name",
            "company_match_verified",
        },
    )


def _contains_normalized_marker(value: Any, markers: set[str]) -> bool:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized_key = _normalize_marker_text(key)
            if normalized_key in markers:
                return True
            if _contains_normalized_marker(nested, markers):
                return True
        return False
    if isinstance(value, list):
        return any(_contains_normalized_marker(item, markers) for item in value)
    if isinstance(value, str):
        normalized_value = _normalize_marker_text(value)
        return any(marker in normalized_value for marker in markers)
    return False


def _prefix_reasons(prefix: str, reasons: Sequence[str]) -> list[str]:
    prefixed: list[str] = []
    for reason in reasons:
        reason_text = str(reason)
        if not reason_text:
            continue
        prefixed.append(
            reason_text if reason_text.startswith(f"{prefix}:") else f"{prefix}:{reason_text}"
        )
    return _dedupe_keep_order(prefixed)


def _candidate_field(candidate: Any, field: str) -> str:
    if not isinstance(candidate, Mapping):
        return ""
    return _clean_string(candidate.get(field))


def _canonical_candidate_source_type(value: Any) -> str:
    normalized = _normalize_marker_text(value)
    return _CANDIDATE_SOURCE_TYPE_ALIASES.get(normalized, normalized)


def _safe_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _clone(value: Any) -> Any:
    return copy.deepcopy(value)


def _sanitize_for_result(value: Any, *, key_name: str = "") -> Any:
    if isinstance(value, Mapping):
        sanitized: dict[str, Any] = {}
        blocked_index = 0
        for key, nested in value.items():
            normalized_key = _normalize_marker_text(key)
            if normalized_key != "not_for_trading_advice" and _key_forbidden_marker(normalized_key):
                sanitized_key = f"blocked_marker_{blocked_index}"
                blocked_index += 1
            else:
                sanitized_key = str(key)
            if normalized_key == "not_for_trading_advice":
                sanitized[sanitized_key] = True
                continue
            sanitized[sanitized_key] = _sanitize_for_result(
                nested,
                key_name=normalized_key,
            )
        return sanitized
    if isinstance(value, list):
        return [_sanitize_for_result(item, key_name=key_name) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_for_result(item, key_name=key_name) for item in value]
    if isinstance(value, str) and _string_forbidden_marker(value, key_name=key_name):
        return "[blocked_marker]"
    return copy.deepcopy(value)


def _assert_no_forbidden_markers(value: Any, *, path: str, key_name: str) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized_key = _normalize_marker_text(key)
            if normalized_key == "not_for_trading_advice":
                if nested is not True or not isinstance(nested, bool):
                    raise RequestSyntheticDryRunIntegrationSafetyError(
                        "not_for_trading_advice",
                        f"{path}.{key}",
                    )
                continue
            marker = _key_forbidden_marker(normalized_key)
            if marker:
                raise RequestSyntheticDryRunIntegrationSafetyError(marker, f"{path}.{key}")
            _assert_no_forbidden_markers(
                nested,
                path=f"{path}.{key}",
                key_name=normalized_key,
            )
        return
    if isinstance(value, list):
        for index, nested in enumerate(value):
            _assert_no_forbidden_markers(
                nested,
                path=f"{path}[{index}]",
                key_name=key_name,
            )
        return
    if isinstance(value, str):
        marker = _string_forbidden_marker(value, key_name=key_name)
        if marker:
            raise RequestSyntheticDryRunIntegrationSafetyError(marker, path)


def _key_forbidden_marker(normalized_key: str) -> str:
    if normalized_key in {"source_url", "source_domain", "not_for_trading_advice"}:
        return ""
    if normalized_key.startswith("not_for_trading_advice"):
        return ""

    compact_key = normalized_key.replace("_", "")
    for marker in _FORBIDDEN_KEY_MARKERS:
        normalized_marker = _normalize_marker_text(marker)
        compact_marker = normalized_marker.replace("_", "")
        if normalized_marker == "env":
            if normalized_key == "env" or normalized_key.endswith("_env") or normalized_key.startswith("env_"):
                return marker
            continue
        if normalized_marker == "token":
            if "token" in normalized_key.split("_") or normalized_key.endswith("_token") or normalized_key.startswith("token_"):
                return marker
            continue
        if normalized_marker in {"buy", "sell", "hold", "http", "fetch", "download", "network"}:
            if normalized_marker in normalized_key.split("_"):
                return marker
            continue
        if normalized_marker and (normalized_marker in normalized_key or compact_marker in compact_key):
            return marker
    return ""


def _string_forbidden_marker(value: str, *, key_name: str) -> str:
    lowered = value.casefold()
    if key_name in _SOURCE_URL_KEY_NAMES:
        if "tushare_token" in lowered or ".env" in lowered or _TOKEN_RE.search(value):
            return "secret marker in source_url"
        return ""

    for marker in _FORBIDDEN_CJK_MARKERS:
        if marker in value:
            return marker

    normalized = _normalize_marker_text(value)
    normalized = normalized.replace("not_for_trading_advice_required", "")
    normalized = normalized.replace("not_for_trading_advice", "")
    if normalized.endswith("_forbidden"):
        return ""
    if "tushare_token" in lowered:
        return "tushare_token"
    if ".env" in lowered:
        return ".env"
    if _TOKEN_RE.search(value):
        return "token"
    for pattern in _SHORT_WORD_VALUE_PATTERNS:
        if pattern.search(value):
            return pattern.pattern
    for marker in _FORBIDDEN_VALUE_MARKERS:
        marker_norm = _normalize_marker_text(marker)
        if marker_norm in {"token", "env", "http"}:
            continue
        compact_marker = marker_norm.replace("_", "")
        compact_value = normalized.replace("_", "")
        if marker_norm and (marker_norm in normalized or compact_marker in compact_value):
            return marker
    return ""


def _flatten_strings(groups: Any) -> list[str]:
    flattened: list[str] = []
    for group in groups:
        if group is None:
            continue
        if isinstance(group, str):
            if group:
                flattened.append(group)
            continue
        if isinstance(group, Mapping):
            flattened.extend(_flatten_strings(group.values()))
            continue
        if isinstance(group, Sequence) and not isinstance(group, (str, bytes, bytearray)):
            flattened.extend(_flatten_strings(group))
            continue
        if group:
            flattened.append(str(group))
    return flattened


def _dedupe_keep_order(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped


def _require_mapping(value: Any, label: str) -> None:
    if not isinstance(value, Mapping):
        raise OfficialVerificationValidationError(f"{label} must be a mapping")


def _require_keys(payload: Mapping[str, Any], required: Sequence[str]) -> None:
    missing = [key for key in required if key not in payload]
    if missing:
        raise OfficialVerificationValidationError(
            f"request synthetic dry-run result missing keys: {missing}"
        )


def _require_merged_blocked_context(result: Mapping[str, Any]) -> None:
    if not result.get("merged_blocked_reasons"):
        raise OfficialVerificationValidationError(REJECTION_RESULT_BLOCKED_REASONS_MISSING)
    if not result.get("merged_data_gap_plan"):
        raise OfficialVerificationValidationError(REJECTION_RESULT_DATA_GAP_PLAN_MISSING)


def _first_string(values: Any) -> str | None:
    for value in _flatten_strings(values):
        if value:
            return value
    return None


def _clean_string(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_marker_text(value: Any) -> str:
    raw = _clean_string(value)
    camel_split = _CAMEL_SPLIT_RE.sub("_", raw)
    lowered = camel_split.casefold()
    lowered = re.sub(r"[\s\-\.]+", "_", lowered)
    lowered = re.sub(r"_+", "_", lowered).strip("_")
    return lowered
