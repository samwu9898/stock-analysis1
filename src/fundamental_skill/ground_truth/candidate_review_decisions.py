# -*- coding: utf-8 -*-
"""Offline candidate review decision artifact builder.

This module consumes an in-memory ``fact_candidates.json`` payload and returns
an auditable ``candidate_review_decisions.json`` payload. It does not read
environment variables, fetch data, call providers, mutate candidate reports, or
write ground-truth fixtures.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .auto_fact_candidate_generator import (
    FactCandidateArtifactBoundaryError,
    FactCandidateGenerationError,
    FactCandidateSecretError,
    _assert_no_forbidden_recommendation_keys,
    _assert_no_secret_like_payload,
    _normalize_code,
)


VERSION = "candidate_review_decisions.v1"
REVIEW_MODE = "protocol_guided_review"
SOURCE_CANDIDATE_REPORT = "fact_candidates.json"
OUTPUT_FILENAME = "candidate_review_decisions.json"
DEFAULT_REVIEWER = "system_review_protocol"
DEFAULT_NEXT_STAGE = "review_decisions_artifact_acceptance"

OUTCOMES = {
    "confirmed_for_future_promotion",
    "keep_manual_review_required",
    "requires_provider_mapping_patch",
    "requires_official_parser",
    "coverage_caveat",
    "reject_candidate",
    "defer_until_live_provider",
    "defer_until_sidecar",
}

FOLLOW_UP_TYPES = {
    "none",
    "provider_mapping_patch",
    "official_parser_needed",
    "live_provider_needed",
    "sidecar_needed",
    "coverage_caveat",
    "reject",
    "manual_review_later",
}

REQUIRED_DECISION_KEYS = {
    "decision_id",
    "field_path",
    "queue_item_type",
    "source_queue_priority",
    "related_candidate_ids",
    "representative_candidates",
    "review_action",
    "metadata_checked",
    "decision_outcome",
    "decision_reason",
    "follow_up_type",
    "follow_up_detail",
    "eligible_for_future_promotion",
    "fixture_write_allowed",
    "reviewed_by",
    "reviewed_at",
    "confidence_after_review",
    "not_for_trading_advice",
}

FORBIDDEN_INVESTMENT_ADVICE_FIELDS = {
    "buy",
    "sell",
    "target_price",
    "position",
    "stop_loss",
    "take_profit",
    "portfolio_weight",
    "portfolio_weight_pct",
    "portfolio_weight_percent",
    "trading_recommendation",
    "investment_recommendation",
}

VALUATION_SAME_DATE_FIELDS = {
    "valuation_metrics.pe_ttm",
    "valuation_metrics.pb",
    "valuation_metrics.market_cap",
}

_TIMESTAMP_RE = re.compile(r"^[A-Za-z0-9T_-]{1,64}$")


class CandidateReviewDecisionError(RuntimeError):
    """Raised when a review-decision artifact cannot be built."""


def build_candidate_review_decisions(
    candidate_report: dict[str, Any],
    *,
    reviewed_by: str = DEFAULT_REVIEWER,
    reviewed_at: str | None = None,
) -> dict[str, Any]:
    """Build a V1 review decisions artifact from a candidate report payload."""

    if not isinstance(candidate_report, dict):
        raise CandidateReviewDecisionError("candidate report must be a dict payload")
    _assert_no_secret_like_payload(candidate_report)
    _assert_no_forbidden_recommendation_keys(candidate_report)
    _assert_no_investment_advice_fields(candidate_report)

    code = _normalize_code(str(candidate_report.get("code", "")))
    timestamp = reviewed_at or _utc_now()
    queue = candidate_report.get("manual_review_priority_queue") or []
    if not isinstance(queue, list):
        raise CandidateReviewDecisionError("manual_review_priority_queue must be a list")

    decisions = [
        _build_decision(
            code=code,
            queue_item=queue_item,
            candidate_report=candidate_report,
            reviewed_by=reviewed_by,
            reviewed_at=timestamp,
            sequence=index + 1,
        )
        for index, queue_item in enumerate(queue)
        if isinstance(queue_item, dict)
    ]
    payload = {
        "version": VERSION,
        "code": code,
        "created_at": timestamp,
        "source_candidate_report": SOURCE_CANDIDATE_REPORT,
        "review_mode": REVIEW_MODE,
        "decisions": decisions,
        "summary": _build_summary(decisions),
    }
    _assert_decisions_payload(payload)
    _assert_no_secret_like_payload(payload)
    _assert_no_forbidden_recommendation_keys(payload)
    _assert_no_investment_advice_fields(payload)
    return payload


def write_candidate_review_decisions(payload: dict[str, Any], output_root: Path, timestamp: str) -> Path:
    """Write ``candidate_review_decisions.json`` inside a timestamp/code boundary."""

    _assert_decisions_payload(payload)
    _assert_no_secret_like_payload(payload)
    _assert_no_secret_like_payload(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    _assert_no_forbidden_recommendation_keys(payload)
    _assert_no_investment_advice_fields(payload)

    code = _normalize_code(str(payload.get("code", "")))
    if not _TIMESTAMP_RE.fullmatch(str(timestamp)) or ".." in str(timestamp):
        raise FactCandidateArtifactBoundaryError("timestamp contains unsupported path characters")

    root = Path(output_root)
    root_resolved = root.resolve(strict=False)
    artifact_path = root / str(timestamp) / code / OUTPUT_FILENAME
    artifact_resolved = artifact_path.resolve(strict=False)
    try:
        artifact_resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise FactCandidateArtifactBoundaryError("review decisions path escapes output root") from exc
    if artifact_resolved.name != OUTPUT_FILENAME:
        raise FactCandidateArtifactBoundaryError("review decisions writer may only write candidate_review_decisions.json")

    artifact_resolved.parent.mkdir(parents=True, exist_ok=True)
    artifact_resolved.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return artifact_resolved


def _build_decision(
    *,
    code: str,
    queue_item: dict[str, Any],
    candidate_report: dict[str, Any],
    reviewed_by: str,
    reviewed_at: str,
    sequence: int,
) -> dict[str, Any]:
    field_path = _simple_field_path(str(queue_item.get("field_path") or "unknown"))
    raw_issue_type = str(queue_item.get("issue_type") or queue_item.get("queue_item_type") or "manual_review_required")
    queue_item_type = _canonical_queue_item_type(raw_issue_type, field_path)
    source_queue_priority = _priority_label(queue_item.get("priority"))
    context = _decision_context(queue_item_type, field_path, raw_issue_type, candidate_report, queue_item)

    return {
        "decision_id": f"{code}-{source_queue_priority}{sequence}",
        "field_path": field_path,
        "queue_item_type": queue_item_type,
        "source_queue_priority": source_queue_priority,
        "related_candidate_ids": _related_candidate_ids(queue_item),
        "representative_candidates": _representative_candidates(queue_item),
        "review_action": context["review_action"],
        "metadata_checked": context["metadata_checked"],
        "decision_outcome": context["decision_outcome"],
        "decision_reason": context["decision_reason"],
        "follow_up_type": context["follow_up_type"],
        "follow_up_detail": context["follow_up_detail"],
        "eligible_for_future_promotion": context["eligible_for_future_promotion"],
        "fixture_write_allowed": False,
        "reviewed_by": reviewed_by,
        "reviewed_at": reviewed_at,
        "confidence_after_review": context["confidence_after_review"],
        "not_for_trading_advice": True,
    }


def _decision_context(
    queue_item_type: str,
    field_path: str,
    raw_issue_type: str,
    candidate_report: dict[str, Any],
    queue_item: dict[str, Any],
) -> dict[str, Any]:
    if queue_item_type == "valuation_as_of_date_review_required":
        if _valuation_metadata_complete(candidate_report):
            return _context(
                review_action="check_same_valuation_date_metadata",
                metadata_checked=["as_of_date", "source_provider", "source_endpoint", "source_trace", "canonical_unit"],
                decision_outcome="confirmed_for_future_promotion",
                decision_reason=(
                    "Valuation PE, PB, and market_cap candidates expose same-date metadata, but V1 still "
                    "allows only future promote-rule consideration."
                ),
                follow_up_type="none",
                follow_up_detail="Keep valuation candidates eligible for later promote rules; do not write fixtures in V1.",
                eligible_for_future_promotion=True,
                confidence_after_review="medium",
            )
        follow_up_type = "provider_mapping_patch" if _queue_has_mapping_gap(queue_item) else "manual_review_later"
        return _context(
            review_action="check_same_valuation_date_metadata",
            metadata_checked=["as_of_date", "source_provider", "source_endpoint", "source_trace", "canonical_unit"],
            decision_outcome="keep_manual_review_required",
            decision_reason="Same-date valuation metadata is required before later promote-rule consideration.",
            follow_up_type=follow_up_type,
            follow_up_detail="Review PE, PB, and market_cap only when same-date metadata is explicit.",
            eligible_for_future_promotion=False,
            confidence_after_review="low",
        )

    if queue_item_type == "business_composition_period_review_required":
        outcome = "requires_provider_mapping_patch" if _queue_has_mapping_gap(queue_item) else "keep_manual_review_required"
        follow_up_type = "provider_mapping_patch" if outcome == "requires_provider_mapping_patch" else "manual_review_later"
        return _context(
            review_action="check_selected_period_and_row_grouping",
            metadata_checked=[
                "report_period",
                "source_period",
                "classification_type",
                "segment_name",
                "source_endpoint",
            ],
            decision_outcome=outcome,
            decision_reason="Composition rows must share report period and classification group before any later promotion.",
            follow_up_type=follow_up_type,
            follow_up_detail="Keep composition rows out of promotion until period and group semantics are explicit.",
            eligible_for_future_promotion=False,
            confidence_after_review="low",
        )

    if queue_item_type == "classification_type_missing":
        outcome = "requires_provider_mapping_patch" if _queue_has_mapping_gap(queue_item) else "requires_official_parser"
        follow_up_type = "provider_mapping_patch" if outcome == "requires_provider_mapping_patch" else "official_parser_needed"
        return _context(
            review_action="check_composition_classification_type",
            metadata_checked=["classification_type", "source_endpoint", "segment_name", "row_selector", "report_period"],
            decision_outcome=outcome,
            decision_reason="Business composition rows need stable product, region, or industry grouping.",
            follow_up_type=follow_up_type,
            follow_up_detail="Expose provider type metadata or use an official parser before reviewing segment rows.",
            eligible_for_future_promotion=False,
            confidence_after_review="low",
        )

    if queue_item_type == "ratio_denominator_unclear" and field_path.endswith(".gross_margin"):
        return _context(
            review_action="check_margin_source_or_derivation",
            metadata_checked=[
                "derived",
                "derivation_method",
                "profit",
                "revenue",
                "report_period",
                "classification_type",
                "source_trace",
            ],
            decision_outcome="keep_manual_review_required",
            decision_reason="Gross margin must be direct or correctly derived within the same period and classification group.",
            follow_up_type="manual_review_later",
            follow_up_detail="Review direct-vs-derived margin metadata after composition period and type are resolved.",
            eligible_for_future_promotion=False,
            confidence_after_review="low",
        )

    if queue_item_type == "ratio_denominator_unclear":
        return _context(
            review_action="check_ratio_denominator_scope",
            metadata_checked=[
                "numerator_source",
                "denominator_source",
                "denominator_scope",
                "report_period",
                "classification_type",
                "source_trace",
            ],
            decision_outcome="keep_manual_review_required",
            decision_reason="Revenue ratio denominator scope must be explicit and same-group before review can complete.",
            follow_up_type="manual_review_later",
            follow_up_detail="Check numerator, denominator, period, and classification group before later promote rules.",
            eligible_for_future_promotion=False,
            confidence_after_review="low",
        )

    if queue_item_type == "main_business_review_required":
        return _context(
            review_action="check_official_business_text_source",
            metadata_checked=[
                "source_provider",
                "source_endpoint",
                "source_trace",
                "text_freshness",
                "official_source_reference",
            ],
            decision_outcome="requires_official_parser",
            decision_reason="main_business needs official text support and must not be derived from the largest segment.",
            follow_up_type="official_parser_needed",
            follow_up_detail="Use CNInfo, annual report, exchange disclosure, or official profile parser support later.",
            eligible_for_future_promotion=False,
            confidence_after_review="low",
        )

    if queue_item_type == "mapping_missing":
        return _context(
            review_action="check_provider_mapping_coverage",
            metadata_checked=["source_endpoint", "source_field", "json_pointer", "source_block", "source_trace"],
            decision_outcome="requires_provider_mapping_patch",
            decision_reason="The source appears relevant, but canonical mapping coverage is incomplete.",
            follow_up_type="provider_mapping_patch",
            follow_up_detail="Patch provider or canonical mapping before any later promote-rule consideration.",
            eligible_for_future_promotion=False,
            confidence_after_review="low",
        )

    if queue_item_type == "provider_missing":
        return _context(
            review_action="check_provider_coverage",
            metadata_checked=["source_provider", "source_endpoint", "fetch_status", "errors", "source_artifacts"],
            decision_outcome="coverage_caveat",
            decision_reason="One provider is missing coverage; this is a limitation, not a direct fixture input.",
            follow_up_type="coverage_caveat",
            follow_up_detail="Document provider coverage and keep provider precedence unchanged.",
            eligible_for_future_promotion=False,
            confidence_after_review="low",
        )

    if queue_item_type == "not_available":
        return _not_available_context(field_path)

    if queue_item_type == "source_conflict":
        return _context(
            review_action="check_source_conflict_after_normalization",
            metadata_checked=["source_provider", "value", "report_period", "as_of_date", "canonical_unit", "source_trace"],
            decision_outcome="keep_manual_review_required",
            decision_reason="Provider values conflict and need normalized source review before any later decision.",
            follow_up_type="manual_review_later",
            follow_up_detail="Review source rows, unit normalization, and period compatibility.",
            eligible_for_future_promotion=False,
            confidence_after_review="low",
        )

    if queue_item_type == "unit_unknown":
        return _context(
            review_action="check_unit_metadata",
            metadata_checked=["data_unit", "canonical_unit", "source_endpoint", "source_trace"],
            decision_outcome="requires_provider_mapping_patch",
            decision_reason="Unit metadata is unclear and must be mapped before later promotion can be considered.",
            follow_up_type="provider_mapping_patch",
            follow_up_detail="Expose source unit and canonical unit metadata.",
            eligible_for_future_promotion=False,
            confidence_after_review="low",
        )

    if queue_item_type == "period_mismatch":
        return _context(
            review_action="check_period_alignment",
            metadata_checked=["report_period", "as_of_date", "source_period", "row_selector", "source_endpoint"],
            decision_outcome="keep_manual_review_required",
            decision_reason="Comparable fields must share report period or valuation date.",
            follow_up_type="manual_review_later",
            follow_up_detail="Align period metadata before any later promote-rule consideration.",
            eligible_for_future_promotion=False,
            confidence_after_review="low",
        )

    if raw_issue_type == "akshare_only_review":
        return _context(
            review_action="check_provider_coverage",
            metadata_checked=["source_provider", "source_endpoint", "source_trace", "conflict_status"],
            decision_outcome="coverage_caveat",
            decision_reason="AkShare-only candidates are review material and not auto-accepted in V1.",
            follow_up_type="coverage_caveat",
            follow_up_detail="Keep as coverage evidence without provider merge or fixture write.",
            eligible_for_future_promotion=False,
            confidence_after_review="low",
        )

    return _context(
        review_action="check_manual_review_queue_item",
        metadata_checked=["source_provider", "source_endpoint", "source_trace", "review_status", "conflict_status"],
        decision_outcome="keep_manual_review_required",
        decision_reason="Queue item remains unresolved in V1 review decisions.",
        follow_up_type="manual_review_later",
        follow_up_detail="Keep this item queued for later manual or mapping review.",
        eligible_for_future_promotion=False,
        confidence_after_review="low",
    )


def _not_available_context(field_path: str) -> dict[str, Any]:
    if field_path.startswith("business_composition.") or field_path == "basic_info.main_business":
        return _context(
            review_action="check_unavailable_field_scope",
            metadata_checked=["value", "source_endpoint", "source_provider", "missing_category", "manual_review_note"],
            decision_outcome="coverage_caveat",
            decision_reason="The field is unavailable in this candidate report and should remain outside fixture promotion.",
            follow_up_type="coverage_caveat",
            follow_up_detail="Record as a coverage caveat unless official parser support is added later.",
            eligible_for_future_promotion=False,
            confidence_after_review="unavailable",
        )
    return _context(
        review_action="check_unavailable_field_scope",
        metadata_checked=["value", "source_endpoint", "source_provider", "missing_category", "manual_review_note"],
        decision_outcome="defer_until_live_provider",
        decision_reason="Offline artifacts are insufficient for this unavailable field.",
        follow_up_type="live_provider_needed",
        follow_up_detail="Revisit only through an accepted guarded live-provider path.",
        eligible_for_future_promotion=False,
        confidence_after_review="unavailable",
    )


def _context(
    *,
    review_action: str,
    metadata_checked: list[str],
    decision_outcome: str,
    decision_reason: str,
    follow_up_type: str,
    follow_up_detail: str,
    eligible_for_future_promotion: bool,
    confidence_after_review: str,
) -> dict[str, Any]:
    if decision_outcome not in OUTCOMES:
        raise CandidateReviewDecisionError(f"unsupported decision outcome: {decision_outcome}")
    if follow_up_type not in FOLLOW_UP_TYPES:
        raise CandidateReviewDecisionError(f"unsupported follow-up type: {follow_up_type}")
    return {
        "review_action": review_action,
        "metadata_checked": metadata_checked,
        "decision_outcome": decision_outcome,
        "decision_reason": decision_reason,
        "follow_up_type": follow_up_type,
        "follow_up_detail": follow_up_detail,
        "eligible_for_future_promotion": bool(eligible_for_future_promotion),
        "confidence_after_review": confidence_after_review,
    }


def _canonical_queue_item_type(issue_type: str, field_path: str) -> str:
    if issue_type == "main_business_review":
        return "main_business_review_required"
    if issue_type == "business_composition_field_review":
        if field_path.endswith(".classification_type"):
            return "classification_type_missing"
        if field_path.endswith(".revenue_ratio") or field_path.endswith(".gross_margin"):
            return "ratio_denominator_unclear"
    if issue_type == "block_mapping_missing":
        return "mapping_missing"
    if issue_type == "block_provider_missing":
        return "provider_missing"
    if issue_type == "period_mismatch_core_field":
        return "period_mismatch"
    if issue_type == "missing_as_of_date":
        return "valuation_as_of_date_review_required"
    return issue_type


def _valuation_metadata_complete(candidate_report: dict[str, Any]) -> bool:
    candidates = candidate_report.get("candidates") or []
    if not isinstance(candidates, list):
        return False
    by_provider: dict[str, dict[str, dict[str, Any]]] = {}
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        field_path = _simple_field_path(str(candidate.get("field_path") or ""))
        if field_path not in VALUATION_SAME_DATE_FIELDS:
            continue
        provider = str(candidate.get("source_provider") or "")
        if provider:
            by_provider.setdefault(provider, {})[field_path] = candidate

    for provider_items in by_provider.values():
        if set(provider_items) != VALUATION_SAME_DATE_FIELDS:
            continue
        dates = {str(item.get("as_of_date")) for item in provider_items.values() if item.get("as_of_date")}
        if len(dates) != 1:
            continue
        if all(_candidate_has_complete_valuation_metadata(item) for item in provider_items.values()):
            return True
    return False


def _candidate_has_complete_valuation_metadata(candidate: dict[str, Any]) -> bool:
    return bool(
        candidate.get("value") is not None
        and candidate.get("as_of_date")
        and candidate.get("source_provider")
        and candidate.get("source_endpoint")
        and isinstance(candidate.get("source_trace"), dict)
        and candidate.get("canonical_unit")
    )


def _build_summary(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    outcome_counts = {outcome: 0 for outcome in OUTCOMES}
    for decision in decisions:
        outcome_counts[str(decision.get("decision_outcome"))] = (
            outcome_counts.get(str(decision.get("decision_outcome")), 0) + 1
        )
    return {
        "total_decisions": len(decisions),
        "confirmed_for_future_promotion_count": outcome_counts["confirmed_for_future_promotion"],
        "keep_manual_review_required_count": outcome_counts["keep_manual_review_required"],
        "requires_provider_mapping_patch_count": outcome_counts["requires_provider_mapping_patch"],
        "requires_official_parser_count": outcome_counts["requires_official_parser"],
        "coverage_caveat_count": outcome_counts["coverage_caveat"],
        "rejected_count": outcome_counts["reject_candidate"],
        "defer_until_live_provider_count": outcome_counts["defer_until_live_provider"],
        "defer_until_sidecar_count": outcome_counts["defer_until_sidecar"],
        "fixture_write_allowed_count": sum(1 for decision in decisions if decision.get("fixture_write_allowed")),
        "eligible_for_future_promotion_count": sum(
            1 for decision in decisions if decision.get("eligible_for_future_promotion")
        ),
        "next_recommended_stage": DEFAULT_NEXT_STAGE,
    }


def _assert_decisions_payload(payload: dict[str, Any]) -> None:
    decisions = payload.get("decisions")
    if not isinstance(decisions, list):
        raise CandidateReviewDecisionError("decisions must be a list")
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        raise CandidateReviewDecisionError("summary must be a dict")
    if payload.get("version") != VERSION:
        raise CandidateReviewDecisionError("unsupported review decisions version")
    if payload.get("review_mode") != REVIEW_MODE:
        raise CandidateReviewDecisionError("unsupported review mode")

    for decision in decisions:
        missing = REQUIRED_DECISION_KEYS - set(decision)
        if missing:
            raise CandidateReviewDecisionError(f"decision is missing required keys: {sorted(missing)}")
        if decision.get("fixture_write_allowed") is not False:
            raise CandidateReviewDecisionError("V1 review decisions must not allow fixture writes")
        if decision.get("not_for_trading_advice") is not True:
            raise CandidateReviewDecisionError("V1 review decisions must be marked not_for_trading_advice")
        if decision.get("decision_outcome") not in OUTCOMES:
            raise CandidateReviewDecisionError("decision has unsupported outcome")
        if decision.get("follow_up_type") not in FOLLOW_UP_TYPES:
            raise CandidateReviewDecisionError("decision has unsupported follow-up type")

    if summary.get("total_decisions") != len(decisions):
        raise CandidateReviewDecisionError("summary total_decisions does not match decisions length")
    if summary.get("fixture_write_allowed_count") != 0:
        raise CandidateReviewDecisionError("summary must not allow fixture writes in V1")


def _assert_no_investment_advice_fields(payload: Any) -> None:
    for key in _walk_keys(payload):
        if key.lower() in FORBIDDEN_INVESTMENT_ADVICE_FIELDS:
            raise FactCandidateGenerationError("review decisions payload contains investment advice fields")


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _queue_has_mapping_gap(queue_item: dict[str, Any]) -> bool:
    if str(queue_item.get("issue_type") or "") == "block_mapping_missing":
        return True
    for candidate in _representative_candidates(queue_item):
        if candidate.get("review_status") == "mapping_missing":
            return True
        if candidate.get("missing_category") == "mapping_missing":
            return True
        if not candidate.get("source_endpoint") or not candidate.get("canonical_unit"):
            return True
    return False


def _related_candidate_ids(queue_item: dict[str, Any]) -> list[Any]:
    ids = queue_item.get("related_candidate_ids")
    if isinstance(ids, list):
        return list(ids)
    ids = []
    for candidate in _representative_candidates(queue_item):
        candidate_id = candidate.get("candidate_id")
        if candidate_id is not None:
            ids.append(candidate_id)
    return ids


def _representative_candidates(queue_item: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = queue_item.get("representative_candidates")
    if not isinstance(candidates, list):
        return []
    return [_sanitize_representative_candidate(candidate) for candidate in candidates if isinstance(candidate, dict)]


def _sanitize_representative_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    allowed_keys = (
        "candidate_id",
        "field_path",
        "source_provider",
        "value",
        "report_period",
        "as_of_date",
        "canonical_unit",
        "confidence",
        "review_status",
        "missing_category",
        "conflict_status",
        "source_endpoint",
    )
    return {key: candidate.get(key) for key in allowed_keys if key in candidate}


def _simple_field_path(field_path: str) -> str:
    return re.sub(r"business_composition\[\d+\]\.", "business_composition.", field_path)


def _priority_label(priority: Any) -> str:
    try:
        value = int(priority)
    except (TypeError, ValueError):
        return "C"
    if value <= 1:
        return "A"
    if value == 2:
        return "B"
    return "C"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
