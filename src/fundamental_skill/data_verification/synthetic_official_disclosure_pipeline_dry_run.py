# -*- coding: utf-8 -*-
"""Synthetic-only, in-memory dry-run assembler for official disclosure handoff."""

from __future__ import annotations

import copy
import re
from collections.abc import Mapping, Sequence
from typing import Any

from .official_disclosure_discovery_candidate import (
    build_discovery_rejection_reason,
    can_handoff_to_registry,
    normalize_official_disclosure_discovery_candidate,
)
from .official_disclosure_locator import reject_non_official_candidates
from .schemas import (
    OFFICIAL_DISCLOSURE_LOCATOR_RESULT_VERSION,
    OFFICIAL_SOURCE_REGISTRY_ENTRY_VERSION,
    AnnouncementType,
    OfficialDisclosureLocatorStatus,
    OfficialDisclosureSourceStatus,
    SourceRefreshPolicy,
    SourceVersion,
    enum_values,
)
from .validators import (
    OfficialVerificationValidationError,
    validate_official_disclosure_locator_result,
    validate_official_source_registry_entry,
    validate_safety_markers,
)


SYNTHETIC_OFFICIAL_DISCLOSURE_PIPELINE_DRY_RUN_RESULT_VERSION = (
    "synthetic_official_disclosure_pipeline_dry_run_result.v1"
)

SYNTHETIC_OFFICIAL_DISCLOSURE_PIPELINE_DRY_RUN_RESULT_REQUIRED_KEYS = (
    "schema_version",
    "stock_code",
    "company_name",
    "query_period",
    "requested_announcement_type",
    "input_discovery_candidates",
    "normalized_discovery_candidates",
    "rejected_discovery_candidates",
    "registry_entry_candidates",
    "locator_result",
    "readiness_skeleton",
    "blocked_reasons",
    "data_gap_plan",
    "caveats",
    "not_for_trading_advice",
)

_CODE_RE = re.compile(r"^\d{6}$")
_CAMEL_SPLIT_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")

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

_DRY_RUN_FORBIDDEN_KEY_MARKERS = (
    "token",
    "env",
    "tushare_token_txt",
    "provider_live",
    "provider_adapter",
    "akshare_live",
    "tushare_live",
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
    "verified_fact",
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

_DRY_RUN_FORBIDDEN_VALUE_MARKERS = (
    "tushare_token.txt",
    ".env",
    "provider live",
    "provider adapter",
    "akshare live",
    "tushare live",
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
    "verified fact",
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

_DRY_RUN_FORBIDDEN_CJK_MARKERS = (
    "买入",
    "卖出",
    "持有",
    "目标价",
    "仓位",
    "组合",
    "技术信号",
    "投资建议",
    "下载",
    "网络",
    "联网",
    "解析PDF",
    "PDF解析",
    "表格抽取",
    "指标抽取",
    "正式研报",
    "输出基线",
    "写入fixture",
    "写入accepted manifest",
)

_SOURCE_URL_KEY_NAMES = {"source_url", "candidate_url"}


def build_synthetic_official_disclosure_pipeline_dry_run_result(
    *,
    stock_code: str,
    company_name: str,
    query_period: Mapping[str, Any],
    requested_announcement_type: str,
    input_discovery_candidates: list[Any],
    source_conflicts: Sequence[Mapping[str, Any] | str] | None = None,
    caveats: Sequence[str] | None = None,
    not_for_trading_advice: bool = True,
) -> dict[str, Any]:
    """Build a dry-run result from explicit synthetic payloads only."""

    _validate_run_inputs(
        stock_code=stock_code,
        company_name=company_name,
        query_period=query_period,
        requested_announcement_type=requested_announcement_type,
        input_discovery_candidates=input_discovery_candidates,
        not_for_trading_advice=not_for_trading_advice,
    )
    assert_no_dry_run_forbidden_markers(input_discovery_candidates)

    normalized_candidates, rejected_candidates = normalize_synthetic_discovery_candidates(input_discovery_candidates)
    registry_candidates, handoff_rejections = build_registry_entry_candidates_from_discovery(normalized_candidates)
    rejected_candidates.extend(handoff_rejections)

    detected_conflicts = _detect_source_conflicts(registry_candidates)
    all_source_conflicts = list(source_conflicts or []) + detected_conflicts
    locator_result = build_locator_result_from_registry_candidates(
        stock_code=stock_code,
        company_name=company_name,
        query_period=query_period,
        requested_announcement_type=requested_announcement_type,
        registry_entry_candidates=registry_candidates,
        rejected_discovery_candidates=rejected_candidates,
        input_candidate_count=len(input_discovery_candidates),
        source_conflicts=all_source_conflicts,
    )
    blocked_reasons = aggregate_blocked_reasons(
        stock_code=stock_code,
        company_name=company_name,
        query_period=query_period,
        requested_announcement_type=requested_announcement_type,
        input_candidate_count=len(input_discovery_candidates),
        rejected_discovery_candidates=rejected_candidates,
        registry_entry_candidates=registry_candidates,
        locator_result=locator_result,
    )
    data_gap_plan = build_data_gap_plan(
        blocked_reasons=blocked_reasons,
        locator_result=locator_result,
        registry_entry_candidates=registry_candidates,
        input_candidate_count=len(input_discovery_candidates),
    )
    readiness_skeleton = build_readiness_skeleton(
        stock_code=stock_code,
        company_name=company_name,
        query_period=query_period,
        requested_announcement_type=requested_announcement_type,
        locator_result=locator_result,
        blocked_reasons=blocked_reasons,
        data_gap_plan=data_gap_plan,
    )

    result = {
        "schema_version": SYNTHETIC_OFFICIAL_DISCLOSURE_PIPELINE_DRY_RUN_RESULT_VERSION,
        "stock_code": stock_code,
        "company_name": company_name,
        "query_period": dict(query_period),
        "requested_announcement_type": requested_announcement_type,
        "input_discovery_candidates": _clone(input_discovery_candidates),
        "normalized_discovery_candidates": normalized_candidates,
        "rejected_discovery_candidates": rejected_candidates,
        "registry_entry_candidates": registry_candidates,
        "locator_result": locator_result,
        "readiness_skeleton": readiness_skeleton,
        "blocked_reasons": blocked_reasons,
        "data_gap_plan": data_gap_plan,
        "caveats": list(caveats or ["synthetic_only", "in_memory_only", "readiness_skeleton_only"]),
        "not_for_trading_advice": True,
    }
    validate_synthetic_official_disclosure_pipeline_dry_run_result(result)
    return result


def validate_synthetic_official_disclosure_pipeline_dry_run_result(result: Mapping[str, Any]) -> None:
    """Validate the dry-run result schema and fail closed on unsafe markers."""

    _require_mapping(result, "synthetic official disclosure pipeline dry-run result")
    _require_keys(
        result,
        SYNTHETIC_OFFICIAL_DISCLOSURE_PIPELINE_DRY_RUN_RESULT_REQUIRED_KEYS,
        "synthetic official disclosure pipeline dry-run result",
    )
    assert_no_dry_run_forbidden_markers(result)
    validate_safety_markers(result)

    if result["schema_version"] != SYNTHETIC_OFFICIAL_DISCLOSURE_PIPELINE_DRY_RUN_RESULT_VERSION:
        raise OfficialVerificationValidationError("dry-run result schema_version is unsupported")
    if result.get("not_for_trading_advice") is not True or not isinstance(result.get("not_for_trading_advice"), bool):
        raise OfficialVerificationValidationError("not_for_trading_advice must be bool true")

    _require_stock_code(result.get("stock_code"), "stock_code")
    _require_non_empty_string(result.get("company_name"), "company_name")
    _require_query_period(result.get("query_period"))
    _require_announcement_type(result.get("requested_announcement_type"), "requested_announcement_type")
    for field in (
        "input_discovery_candidates",
        "normalized_discovery_candidates",
        "rejected_discovery_candidates",
        "registry_entry_candidates",
        "blocked_reasons",
        "data_gap_plan",
        "caveats",
    ):
        _require_list(result.get(field), field)

    for candidate in result["registry_entry_candidates"]:
        validate_official_source_registry_entry(candidate)
    validate_official_disclosure_locator_result(result["locator_result"])
    _validate_readiness_skeleton(result["readiness_skeleton"])

    locator_status = result["locator_result"].get("locator_status")
    readiness_skeleton = result["readiness_skeleton"]
    if readiness_skeleton.get("locator_status") != locator_status:
        raise OfficialVerificationValidationError("readiness_skeleton locator_status must match locator_result")
    if readiness_skeleton.get("selected_official_source_id") != result["locator_result"].get("selected_official_source_id"):
        raise OfficialVerificationValidationError("readiness_skeleton selected_official_source_id must match locator_result")
    if locator_status != OfficialDisclosureLocatorStatus.FOUND_SINGLE_OFFICIAL_CANDIDATE.value:
        if not result["blocked_reasons"]:
            raise OfficialVerificationValidationError("blocked or review-required dry-run requires blocked_reasons")
        if not result["data_gap_plan"]:
            raise OfficialVerificationValidationError("blocked or review-required dry-run requires data_gap_plan")
        if not readiness_skeleton.get("blocked_reasons"):
            raise OfficialVerificationValidationError("blocked or review-required dry-run requires readiness_skeleton blocked_reasons")
        if not readiness_skeleton.get("required_explicit_inputs"):
            raise OfficialVerificationValidationError(
                "blocked or review-required dry-run requires readiness_skeleton required_explicit_inputs"
            )


def normalize_synthetic_discovery_candidates(candidates: list[Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Normalize candidates and convert non-safety validation failures into rejected records."""

    _require_list(candidates, "input_discovery_candidates")
    normalized_candidates: list[dict[str, Any]] = []
    rejected_candidates: list[dict[str, Any]] = []

    for index, candidate in enumerate(candidates):
        try:
            assert_no_dry_run_forbidden_markers(candidate)
            if not isinstance(candidate, Mapping):
                raise OfficialVerificationValidationError("discovery candidate must be a mapping")
            normalized = normalize_official_disclosure_discovery_candidate(candidate)
        except OfficialVerificationValidationError as exc:
            rejected_candidates.append(_build_discovery_rejection_record(index, candidate, str(exc)))
            continue
        normalized_candidates.append(normalized)

    return normalized_candidates, rejected_candidates


def build_registry_entry_candidates_from_discovery(
    normalized_discovery_candidates: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build registry entry candidates from explicit normalized discovery metadata only."""

    registry_candidates: list[dict[str, Any]] = []
    rejected_candidates: list[dict[str, Any]] = []

    for index, candidate in enumerate(normalized_discovery_candidates):
        allowed, reason = can_handoff_to_registry(candidate, with_reason=True)
        if not allowed:
            rejected_candidates.append(
                _build_rejection_record_from_normalized_candidate(
                    index=index,
                    candidate=candidate,
                    rejection_reason=reason or str(candidate.get("rejection_reason") or "not_handoff_eligible"),
                    stage="discovery_to_registry_handoff",
                )
            )
            continue

        entry = {
            "schema_version": OFFICIAL_SOURCE_REGISTRY_ENTRY_VERSION,
            "source_id": _build_registry_source_id(candidate),
            "stock_code": str(candidate["stock_code"]),
            "company_name": str(candidate["company_name"]),
            "period_key": str(candidate["period_key"]),
            "period_end_date": str(candidate["period_end_date"]),
            "announcement_type": str(candidate["announcement_type"]),
            "source_type": str(candidate["source_type"]),
            "source_url": str(candidate["source_url"]),
            "source_title": str(candidate["source_title"]),
            "disclosure_date": str(candidate["disclosure_date"]),
            "local_cache_path": "",
            "file_sha256": "",
            "retrieved_at_utc": "",
            "source_status": OfficialDisclosureSourceStatus.OFFICIAL_CANDIDATE.value,
            "source_refresh_policy": SourceRefreshPolicy.MANUAL_REVIEW_ONLY.value,
            "registry_version": "synthetic_dry_run_registry.v1",
            "source_version": SourceVersion.ORIGINAL.value,
            "rejection_reason": "",
            "caveats": ["synthetic_registry_entry_candidate"],
            "not_for_trading_advice": True,
        }
        try:
            validate_official_source_registry_entry(entry)
        except OfficialVerificationValidationError as exc:
            rejected_candidates.append(
                _build_rejection_record_from_normalized_candidate(
                    index=index,
                    candidate=candidate,
                    rejection_reason=f"registry_entry_validation_failed: {exc}",
                    stage="registry_entry_candidate",
                )
            )
            continue
        registry_candidates.append(entry)

    return registry_candidates, rejected_candidates


def build_locator_result_from_registry_candidates(
    *,
    stock_code: str,
    company_name: str,
    query_period: Mapping[str, Any],
    requested_announcement_type: str,
    registry_entry_candidates: Sequence[Mapping[str, Any]],
    rejected_discovery_candidates: Sequence[Mapping[str, Any]],
    input_candidate_count: int,
    source_conflicts: Sequence[Mapping[str, Any] | str] | None = None,
) -> dict[str, Any]:
    """Build an official disclosure locator result without selecting silently."""

    candidates = [dict(candidate) for candidate in registry_entry_candidates]
    rejected_candidates = [dict(candidate) for candidate in rejected_discovery_candidates]
    conflicts = list(source_conflicts or [])
    selectable_candidates = [candidate for candidate in candidates if candidate.get("source_status") == "official_candidate"]

    if conflicts or len(selectable_candidates) > 1:
        locator_result = {
            "schema_version": OFFICIAL_DISCLOSURE_LOCATOR_RESULT_VERSION,
            "stock_code": stock_code,
            "company_name": company_name,
            "query_period": dict(query_period),
            "requested_announcement_type": requested_announcement_type,
            "candidates": candidates,
            "selected_official_source_id": "",
            "rejected_candidates": reject_non_official_candidates(candidates),
            "source_conflicts": conflicts,
            "locator_status": OfficialDisclosureLocatorStatus.FOUND_MULTIPLE_CANDIDATES_REVIEW_REQUIRED.value,
            "blocked_reason": "source selection requires review",
            "caveats": ["manual_review_required"],
            "not_for_trading_advice": True,
        }
    elif len(selectable_candidates) == 1:
        selected = selectable_candidates[0]
        locator_result = {
            "schema_version": OFFICIAL_DISCLOSURE_LOCATOR_RESULT_VERSION,
            "stock_code": stock_code,
            "company_name": company_name,
            "query_period": dict(query_period),
            "requested_announcement_type": requested_announcement_type,
            "candidates": candidates,
            "selected_official_source_id": selected["source_id"],
            "rejected_candidates": [],
            "source_conflicts": [],
            "locator_status": OfficialDisclosureLocatorStatus.FOUND_SINGLE_OFFICIAL_CANDIDATE.value,
            "blocked_reason": "",
            "caveats": ["synthetic_locator_result"],
            "not_for_trading_advice": True,
        }
    elif input_candidate_count and rejected_candidates:
        locator_result = {
            "schema_version": OFFICIAL_DISCLOSURE_LOCATOR_RESULT_VERSION,
            "stock_code": stock_code,
            "company_name": company_name,
            "query_period": dict(query_period),
            "requested_announcement_type": requested_announcement_type,
            "candidates": [],
            "selected_official_source_id": "",
            "rejected_candidates": rejected_candidates,
            "source_conflicts": [],
            "locator_status": OfficialDisclosureLocatorStatus.REJECTED_ALL_CANDIDATES.value,
            "blocked_reason": "all discovery candidates rejected",
            "caveats": ["no_registry_candidate"],
            "not_for_trading_advice": True,
        }
    else:
        locator_result = {
            "schema_version": OFFICIAL_DISCLOSURE_LOCATOR_RESULT_VERSION,
            "stock_code": stock_code,
            "company_name": company_name,
            "query_period": dict(query_period),
            "requested_announcement_type": requested_announcement_type,
            "candidates": [],
            "selected_official_source_id": "",
            "rejected_candidates": [],
            "source_conflicts": [],
            "locator_status": OfficialDisclosureLocatorStatus.NO_OFFICIAL_SOURCE_FOUND.value,
            "blocked_reason": "no discovery candidates supplied",
            "caveats": ["empty_synthetic_payload"],
            "not_for_trading_advice": True,
        }

    validate_official_disclosure_locator_result(locator_result)
    return locator_result


def build_readiness_skeleton(
    *,
    stock_code: str,
    company_name: str,
    query_period: Mapping[str, Any],
    requested_announcement_type: str,
    locator_result: Mapping[str, Any],
    blocked_reasons: Sequence[str],
    data_gap_plan: Sequence[str],
) -> dict[str, Any]:
    """Create a gate-input readiness skeleton without producing facts or reports."""

    locator_status = str(locator_result.get("locator_status", ""))
    selected_id = str(locator_result.get("selected_official_source_id", ""))
    if locator_status == OfficialDisclosureLocatorStatus.FOUND_SINGLE_OFFICIAL_CANDIDATE.value:
        readiness_status = "ready_for_verification_gate_input"
        required_explicit_inputs: list[str] = []
    elif locator_status == OfficialDisclosureLocatorStatus.FOUND_MULTIPLE_CANDIDATES_REVIEW_REQUIRED.value:
        readiness_status = "review_required"
        required_explicit_inputs = ["manual_selection_of_one_official_source_candidate"]
    else:
        readiness_status = "blocked_until_review"
        required_explicit_inputs = list(data_gap_plan)

    skeleton = {
        "schema_version": "verification_readiness_skeleton.v1",
        "stock_code": stock_code,
        "company_name": company_name,
        "query_period": dict(query_period),
        "requested_announcement_type": requested_announcement_type,
        "readiness_status": readiness_status,
        "locator_status": locator_status,
        "selected_official_source_id": selected_id,
        "required_explicit_inputs": required_explicit_inputs,
        "blocked_reasons": list(blocked_reasons),
        "caveats": ["skeleton_only"],
        "not_for_trading_advice": True,
    }
    _validate_readiness_skeleton(skeleton)
    return skeleton


def aggregate_blocked_reasons(
    *,
    stock_code: str,
    company_name: str,
    query_period: Mapping[str, Any],
    requested_announcement_type: str,
    input_candidate_count: int,
    rejected_discovery_candidates: Sequence[Mapping[str, Any]],
    registry_entry_candidates: Sequence[Mapping[str, Any]],
    locator_result: Mapping[str, Any],
) -> list[str]:
    """Collect pipeline-level reasons across discovery, registry, locator, and readiness layers."""

    reasons: list[str] = []
    if not stock_code:
        reasons.append("missing_stock_code")
    if not company_name:
        reasons.append("missing_company_name")
    if not query_period:
        reasons.append("missing_query_period")
    if not requested_announcement_type:
        reasons.append("missing_requested_announcement_type")
    if input_candidate_count == 0:
        reasons.append("no_input_discovery_candidates")
    for rejected in rejected_discovery_candidates:
        reason = str(rejected.get("rejection_reason") or "discovery_candidate_rejected")
        reasons.append(f"discovery:{reason}")
    if input_candidate_count and not registry_entry_candidates:
        reasons.append("registry:no_handoff_eligible_official_candidate")

    locator_status = str(locator_result.get("locator_status", ""))
    blocked_reason = str(locator_result.get("blocked_reason") or "")
    if locator_status == OfficialDisclosureLocatorStatus.FOUND_MULTIPLE_CANDIDATES_REVIEW_REQUIRED.value:
        if locator_result.get("source_conflicts"):
            reasons.append("locator:source_conflict_review_required")
        else:
            reasons.append("locator:multiple_official_candidates_review_required")
    elif locator_status != OfficialDisclosureLocatorStatus.FOUND_SINGLE_OFFICIAL_CANDIDATE.value:
        reasons.append(f"locator:{blocked_reason or locator_status}")

    return _dedupe_keep_order(reasons)


def build_data_gap_plan(
    *,
    blocked_reasons: Sequence[str],
    locator_result: Mapping[str, Any],
    registry_entry_candidates: Sequence[Mapping[str, Any]],
    input_candidate_count: int,
) -> list[str]:
    """Describe explicit follow-up data needs without triggering acquisition."""

    if not blocked_reasons:
        return []

    plan: list[str] = []
    if input_candidate_count == 0:
        plan.append("provide_synthetic_discovery_candidate_payload")
    if any("missing_stock_code" in reason for reason in blocked_reasons):
        plan.append("provide_stock_code")
    if any("missing_company_name" in reason for reason in blocked_reasons):
        plan.append("provide_company_name")
    if any("missing_query_period" in reason for reason in blocked_reasons):
        plan.append("provide_query_period")
    if any("missing_requested_announcement_type" in reason for reason in blocked_reasons):
        plan.append("provide_requested_announcement_type")
    if any("source_conflict" in reason for reason in blocked_reasons):
        plan.append("resolve_source_metadata_conflict_by_review")
    if any("multiple_official_candidates" in reason for reason in blocked_reasons):
        plan.append("select_one_official_source_candidate_by_review")
    if not registry_entry_candidates:
        plan.append("provide_one_complete_official_discovery_candidate")
    if locator_result.get("locator_status") != OfficialDisclosureLocatorStatus.FOUND_SINGLE_OFFICIAL_CANDIDATE.value:
        plan.append("rerun_with_explicit_synthetic_metadata_after_review")
    return _dedupe_keep_order(plan)


def assert_no_dry_run_forbidden_markers(payload: Any) -> None:
    """Recursively reject dry-run forbidden markers in nested dict/list/string payloads."""

    _assert_no_dry_run_forbidden_markers(payload, path="$", key_name="")


def _build_discovery_rejection_record(index: int, candidate: Any, error: str) -> dict[str, Any]:
    if isinstance(candidate, Mapping):
        reason = build_discovery_rejection_reason(candidate)
        if not reason:
            reason = _normalize_error_reason(error)
        return {
            "input_index": index,
            "discovery_candidate_id": str(candidate.get("discovery_candidate_id") or ""),
            "source_type": str(candidate.get("source_type") or ""),
            "rejection_stage": "discovery_normalization",
            "rejection_reason": reason,
            "error": error,
            "not_for_trading_advice": True,
        }
    return {
        "input_index": index,
        "discovery_candidate_id": "",
        "source_type": "",
        "rejection_stage": "discovery_normalization",
        "rejection_reason": "candidate_must_be_mapping",
        "error": error,
        "not_for_trading_advice": True,
    }


def _build_rejection_record_from_normalized_candidate(
    *,
    index: int,
    candidate: Mapping[str, Any],
    rejection_reason: str,
    stage: str,
) -> dict[str, Any]:
    return {
        "input_index": index,
        "discovery_candidate_id": str(candidate.get("discovery_candidate_id") or ""),
        "source_type": str(candidate.get("source_type") or ""),
        "source_url": str(candidate.get("source_url") or ""),
        "source_domain": str(candidate.get("source_domain") or ""),
        "rejection_stage": stage,
        "rejection_reason": rejection_reason,
        "not_for_trading_advice": True,
    }


def _build_registry_source_id(candidate: Mapping[str, Any]) -> str:
    discovery_candidate_id = str(candidate.get("discovery_candidate_id") or "").strip()
    suffix = re.sub(r"[^A-Za-z0-9_]+", "_", discovery_candidate_id).strip("_")
    if not suffix:
        suffix = "missing_discovery_candidate_id"
    return f"synthetic_registry_entry_from_{suffix}"


def _detect_source_conflicts(candidates: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    by_url: dict[str, list[Mapping[str, Any]]] = {}
    for candidate in candidates:
        source_url = str(candidate.get("source_url") or "")
        if source_url:
            by_url.setdefault(source_url, []).append(candidate)

    fields = ("stock_code", "company_name", "period_key", "period_end_date", "announcement_type", "source_type", "source_title", "disclosure_date")
    for source_url, entries in by_url.items():
        if len(entries) < 2:
            continue
        signatures = {tuple(str(entry.get(field) or "") for field in fields) for entry in entries}
        if len(signatures) > 1:
            conflicts.append(
                {
                    "source_url": source_url,
                    "conflict_reason": "source_metadata_conflict",
                    "source_ids": [str(entry.get("source_id") or "") for entry in entries],
                    "not_for_trading_advice": True,
                }
            )
    return conflicts


def _validate_run_inputs(
    *,
    stock_code: str,
    company_name: str,
    query_period: Mapping[str, Any],
    requested_announcement_type: str,
    input_discovery_candidates: list[Any],
    not_for_trading_advice: bool,
) -> None:
    if not isinstance(not_for_trading_advice, bool) or not_for_trading_advice is not True:
        raise OfficialVerificationValidationError("not_for_trading_advice must be bool true")
    _require_stock_code(stock_code, "stock_code")
    _require_non_empty_string(company_name, "company_name")
    _require_query_period(query_period)
    _require_announcement_type(requested_announcement_type, "requested_announcement_type")
    _require_list(input_discovery_candidates, "input_discovery_candidates")


def _validate_readiness_skeleton(skeleton: Any) -> None:
    _require_mapping(skeleton, "readiness_skeleton")
    required = (
        "schema_version",
        "stock_code",
        "company_name",
        "query_period",
        "requested_announcement_type",
        "readiness_status",
        "locator_status",
        "selected_official_source_id",
        "required_explicit_inputs",
        "blocked_reasons",
        "caveats",
        "not_for_trading_advice",
    )
    _require_keys(skeleton, required, "readiness_skeleton")
    assert_no_dry_run_forbidden_markers(skeleton)
    if skeleton.get("not_for_trading_advice") is not True:
        raise OfficialVerificationValidationError("readiness_skeleton not_for_trading_advice must be true")
    _require_stock_code(skeleton.get("stock_code"), "readiness_skeleton.stock_code")
    _require_non_empty_string(skeleton.get("company_name"), "readiness_skeleton.company_name")
    _require_query_period(skeleton.get("query_period"))
    _require_announcement_type(skeleton.get("requested_announcement_type"), "readiness_skeleton.requested_announcement_type")
    _require_non_empty_string(skeleton.get("readiness_status"), "readiness_skeleton.readiness_status")
    _require_list(skeleton.get("required_explicit_inputs"), "readiness_skeleton.required_explicit_inputs")
    _require_list(skeleton.get("blocked_reasons"), "readiness_skeleton.blocked_reasons")
    _require_list(skeleton.get("caveats"), "readiness_skeleton.caveats")


def _assert_no_dry_run_forbidden_markers(payload: Any, *, path: str, key_name: str) -> None:
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            normalized_key = _normalize_marker_text(key)
            if normalized_key == "not_for_trading_advice":
                if value is not True or not isinstance(value, bool):
                    raise OfficialVerificationValidationError(f"{path}.{key} must be bool true")
                continue
            if _key_has_forbidden_marker(normalized_key):
                raise OfficialVerificationValidationError(f"forbidden dry-run marker key at {path}.{key}")
            _assert_no_dry_run_forbidden_markers(value, path=f"{path}.{key}", key_name=normalized_key)
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            _assert_no_dry_run_forbidden_markers(value, path=f"{path}[{index}]", key_name=key_name)
    elif isinstance(payload, str):
        marker = _string_forbidden_marker(payload, key_name=key_name)
        if marker:
            raise OfficialVerificationValidationError(f"forbidden dry-run marker value at {path}: {marker}")


def _key_has_forbidden_marker(normalized_key: str) -> bool:
    if normalized_key in {"source_url", "source_domain", "not_for_trading_advice"}:
        return False
    compact_key = normalized_key.replace("_", "")
    for marker in _DRY_RUN_FORBIDDEN_KEY_MARKERS:
        normalized_marker = _normalize_marker_text(marker)
        compact_marker = normalized_marker.replace("_", "")
        if normalized_marker in {"buy", "sell", "hold", "http", "fetch", "download", "network"}:
            if normalized_marker in normalized_key.split("_"):
                return True
            continue
        if normalized_marker == "env":
            if normalized_key == "env" or normalized_key.endswith("_env") or normalized_key.startswith("env_"):
                return True
            continue
        if normalized_marker == "token":
            if "token" in normalized_key.split("_") or normalized_key.endswith("_token") or normalized_key.startswith("token_"):
                return True
            continue
        if normalized_marker and (normalized_marker in normalized_key or compact_marker in compact_key):
            return True
    return False


def _string_forbidden_marker(value: str, *, key_name: str) -> str:
    if key_name in _SOURCE_URL_KEY_NAMES:
        lowered_url = value.lower()
        if "tushare_token.txt" in lowered_url or ".env" in lowered_url or re.search(r"\btoken\b", lowered_url):
            return "secret marker in source_url"
        return ""

    for marker in _DRY_RUN_FORBIDDEN_CJK_MARKERS:
        if marker in value:
            return marker

    lowered = value.lower()
    normalized = _normalize_marker_text(value)
    normalized = normalized.replace("not_for_trading_advice_required", "")
    normalized = normalized.replace("not_for_trading_advice", "")
    if "tushare_token.txt" in lowered:
        return "tushare_token.txt"
    if ".env" in lowered:
        return ".env"
    if re.search(r"\btoken\b", lowered):
        return "token"
    for pattern in _SHORT_WORD_VALUE_PATTERNS:
        if pattern.search(value):
            return pattern.pattern
    for marker in _DRY_RUN_FORBIDDEN_VALUE_MARKERS:
        marker_norm = _normalize_marker_text(marker)
        if marker_norm and marker_norm in normalized:
            return marker
    return ""


def _normalize_error_reason(error: str) -> str:
    normalized = _normalize_marker_text(error)
    if "source_domain" in normalized:
        return "invalid_source_domain"
    if "not_for_trading_advice" in normalized:
        return "not_for_trading_advice_required"
    if "source_type" in normalized:
        return "unknown_source_type"
    if "missing" in normalized:
        return "missing_required_metadata"
    return "discovery_candidate_rejected"


def _require_mapping(value: Any, label: str) -> None:
    if not isinstance(value, Mapping):
        raise OfficialVerificationValidationError(f"{label} must be a mapping")


def _require_keys(payload: Mapping[str, Any], required: Sequence[str], label: str) -> None:
    missing = [key for key in required if key not in payload]
    if missing:
        raise OfficialVerificationValidationError(f"{label} missing keys: {missing}")


def _require_stock_code(value: Any, field: str) -> None:
    if not isinstance(value, str) or not _CODE_RE.fullmatch(value):
        raise OfficialVerificationValidationError(f"{field} must be a 6 digit string")


def _require_non_empty_string(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise OfficialVerificationValidationError(f"{field} must be a non-empty string")


def _require_query_period(value: Any) -> None:
    _require_mapping(value, "query_period")
    if _is_blank(value.get("period_key")) and _is_blank(value.get("period_end_date")):
        raise OfficialVerificationValidationError("query_period requires period_key or period_end_date")


def _require_announcement_type(value: Any, field: str) -> None:
    if value not in enum_values(AnnouncementType):
        raise OfficialVerificationValidationError(f"{field} must be one of: {sorted(enum_values(AnnouncementType))}")


def _require_list(value: Any, field: str) -> None:
    if not isinstance(value, list):
        raise OfficialVerificationValidationError(f"{field} must be a list")


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _dedupe_keep_order(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped


def _clone(value: Any) -> Any:
    return copy.deepcopy(value)


def _normalize_marker_text(value: Any) -> str:
    raw = "" if value is None else str(value).strip()
    camel_split = _CAMEL_SPLIT_RE.sub("_", raw)
    lowered = camel_split.lower()
    lowered = re.sub(r"[\s\-\.]+", "_", lowered)
    lowered = re.sub(r"_+", "_", lowered).strip("_")
    return lowered
