# -*- coding: utf-8 -*-
"""Pure helpers for official disclosure locator results."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .official_disclosure_source_registry import is_selectable_official_entry
from .schemas import (
    OFFICIAL_DISCLOSURE_LOCATOR_RESULT_VERSION,
    OfficialDisclosureLocatorStatus,
)
from .validators import OfficialVerificationValidationError, validate_official_disclosure_locator_result


def select_single_official_candidate(candidates: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    selectable = [candidate for candidate in candidates if is_selectable_official_entry(candidate)]
    if len(selectable) > 1:
        raise OfficialVerificationValidationError("multiple official candidates require review")
    if not selectable:
        return None
    return selectable[0]


def classify_locator_status(
    candidates: Sequence[Mapping[str, Any]],
    rejected_candidates: Sequence[Mapping[str, Any]],
    source_conflicts: Sequence[Mapping[str, Any] | str],
) -> str:
    selectable = [candidate for candidate in candidates if is_selectable_official_entry(candidate)]
    if source_conflicts or len(selectable) > 1:
        return OfficialDisclosureLocatorStatus.FOUND_MULTIPLE_CANDIDATES_REVIEW_REQUIRED.value
    if len(selectable) == 1:
        return OfficialDisclosureLocatorStatus.FOUND_SINGLE_OFFICIAL_CANDIDATE.value
    if candidates and rejected_candidates and len(candidates) == len(rejected_candidates):
        return OfficialDisclosureLocatorStatus.REJECTED_ALL_CANDIDATES.value
    if not candidates:
        return OfficialDisclosureLocatorStatus.NO_OFFICIAL_SOURCE_FOUND.value
    return OfficialDisclosureLocatorStatus.BLOCKED_UNTIL_REVIEW.value


def reject_non_official_candidates(candidates: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [candidate for candidate in candidates if not is_selectable_official_entry(candidate)]


def build_locator_blocked_result(
    *,
    stock_code: str,
    company_name: str,
    query_period: Mapping[str, Any],
    requested_announcement_type: str,
    blocked_reason: str,
    candidates: Sequence[Mapping[str, Any]] | None = None,
    rejected_candidates: Sequence[Mapping[str, Any]] | None = None,
    source_conflicts: Sequence[Mapping[str, Any] | str] | None = None,
    caveats: Sequence[str] | None = None,
) -> dict[str, Any]:
    result = {
        "schema_version": OFFICIAL_DISCLOSURE_LOCATOR_RESULT_VERSION,
        "stock_code": stock_code,
        "company_name": company_name,
        "query_period": dict(query_period),
        "requested_announcement_type": requested_announcement_type,
        "candidates": list(candidates or []),
        "selected_official_source_id": "",
        "rejected_candidates": list(rejected_candidates or []),
        "source_conflicts": list(source_conflicts or []),
        "locator_status": OfficialDisclosureLocatorStatus.BLOCKED_UNTIL_REVIEW.value,
        "blocked_reason": blocked_reason,
        "caveats": list(caveats or []),
        "not_for_trading_advice": True,
    }
    validate_official_disclosure_locator_result(result)
    return result


def build_locator_review_required_result(
    *,
    stock_code: str,
    company_name: str,
    query_period: Mapping[str, Any],
    requested_announcement_type: str,
    candidates: Sequence[Mapping[str, Any]],
    blocked_reason: str,
    source_conflicts: Sequence[Mapping[str, Any] | str] | None = None,
    caveats: Sequence[str] | None = None,
) -> dict[str, Any]:
    result = {
        "schema_version": OFFICIAL_DISCLOSURE_LOCATOR_RESULT_VERSION,
        "stock_code": stock_code,
        "company_name": company_name,
        "query_period": dict(query_period),
        "requested_announcement_type": requested_announcement_type,
        "candidates": list(candidates),
        "selected_official_source_id": "",
        "rejected_candidates": reject_non_official_candidates(candidates),
        "source_conflicts": list(source_conflicts or []),
        "locator_status": OfficialDisclosureLocatorStatus.FOUND_MULTIPLE_CANDIDATES_REVIEW_REQUIRED.value,
        "blocked_reason": blocked_reason,
        "caveats": list(caveats or []),
        "not_for_trading_advice": True,
    }
    validate_official_disclosure_locator_result(result)
    return result
