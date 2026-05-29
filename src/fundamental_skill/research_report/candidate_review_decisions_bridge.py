# -*- coding: utf-8 -*-
"""In-memory bridge-aware candidate review decisions builder and validator."""

from __future__ import annotations

import copy
import re
from datetime import datetime, timezone
from typing import Any


BRIDGE_REVIEW_DECISIONS_VERSION = "candidate_review_decisions_bridge.v1"

BRIDGE_REVIEW_SOURCE_TYPES = {
    "provider_candidates",
    "official_disclosure_candidates",
    "bridge_review_priority",
}

BRIDGE_REVIEW_DECISIONS = {
    "accepted_for_report_candidate",
    "manual_review_required",
    "blocked_by_caveat",
    "rejected",
    "needs_more_evidence",
    "conflict_requires_review",
}

FORBIDDEN_TRADING_RECOMMENDATION_KEYS = {
    "buy",
    "sell",
    "target_price",
    "position",
    "portfolio_weight",
}

FORBIDDEN_SIDE_EFFECT_KEYS = {
    "verified_fact",
    "auto_verified",
    "fixture_promotion",
    "promote_to_fixture",
    "fixture_write_allowed",
    "ground_truth_fixture_write",
    "accepted_manifest_update",
    "provider_primary",
    "primary_provider",
    "provider_primary_change",
    "provider_primary_switch",
    "switch_provider_primary",
    "research_report_v1_update",
}

REQUIRED_DECISION_KEYS = {
    "decision_id",
    "source_type",
    "candidate_id",
    "artifact_ref",
    "bridge_ref",
    "field_path",
    "period",
    "unit",
    "decision",
    "decision_reason",
    "review_status",
    "follow_up_class",
    "caveats",
    "not_for_trading_advice",
}

SUMMARY_COUNT_KEYS = {
    "total_decisions",
    "provider_decision_count",
    "official_decision_count",
    "bridge_priority_decision_count",
    "manual_review_required_count",
    "blocked_by_caveat_count",
    "accepted_for_report_candidate_count",
    "conflict_requires_review_count",
}

_A_SHARE_CODE_RE = re.compile(r"^\d{6}$")
_SECRET_KEY_RE = re.compile(
    r"(^|[^A-Za-z0-9])(?:api[_-]?)?(?:token|secret|credential|password|access[_-]?key|api[_-]?key)"
    r"([^A-Za-z0-9]|$)",
    flags=re.IGNORECASE,
)
_KEYED_SECRET_RE = re.compile(
    r"(^|[^A-Za-z0-9])(?:api[_-]?)?(?:token|secret|credential|password|access[_-]?key|api[_-]?key)"
    r"([^A-Za-z0-9]|$)\s*[:=]\s*[^\s,;&]+",
    flags=re.IGNORECASE,
)
_BEARER_RE = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]+", flags=re.IGNORECASE)
_REMOTE_CONTROL_RE = re.compile(
    r"\b" + "m" + "cp" + r"(?:s)?://[^\s\"'<>]+|\b" + "m" + "cp" + r"\?[^\s\"']*",
    flags=re.IGNORECASE,
)
_DOTENV_RE = re.compile(r"(^|[\\/:\s\"'`=])\.env(?:\.[A-Za-z0-9_-]+)*\b", flags=re.IGNORECASE)
_TOKEN_LIKE_RE = re.compile(
    r"\b(?=[A-Za-z0-9._~+=-]{32,}\b)"
    r"(?=[A-Za-z0-9._~+=-]*[a-z])"
    r"(?=[A-Za-z0-9._~+=-]*[A-Z])"
    r"(?=[A-Za-z0-9._~+=-]*\d)"
    r"[A-Za-z0-9._~+=-]+\b"
)
_LOCAL_SECRET_PATH_RE = re.compile(
    r"\b[A-Za-z]:[\\/]+Users[\\/]+[^\"'\s<>]*(?:[\\/]+(?:\.ssh|\.aws|\.azure|secrets?|credentials?)[\\/][^\"'\s<>]*)"
    r"|/(?:Users|home)/[^/\s]+/[^\"'\s<>]*(?:\.ssh|\.aws|\.azure|secrets?|credentials?)/[^\"'\s<>]*",
    flags=re.IGNORECASE,
)


class CandidateReviewDecisionsBridgeError(RuntimeError):
    """Base error for bridge-aware candidate review decision failures."""


class CandidateReviewDecisionsBridgeValidationError(CandidateReviewDecisionsBridgeError):
    """Raised when bridge-aware candidate review decisions are invalid."""


class CandidateReviewDecisionsBridgeSecretError(CandidateReviewDecisionsBridgeError):
    """Raised when secret-like material is detected."""


class CandidateReviewDecisionsBridgePathError(CandidateReviewDecisionsBridgeValidationError):
    """Raised when an artifact reference escapes the allowed local boundary."""


def build_bridge_review_decision(
    *,
    decision_id: str,
    source_type: str,
    candidate_id: str,
    artifact_ref: str,
    bridge_ref: str = "",
    field_path: str = "",
    period: str = "",
    unit: str = "",
    decision: str,
    decision_reason: str,
    review_status: str = "",
    follow_up_class: str = "",
    caveats: list[str] | None = None,
) -> dict:
    """Build and validate one bridge-aware review decision row."""

    row = {
        "decision_id": decision_id,
        "source_type": source_type,
        "candidate_id": candidate_id,
        "artifact_ref": artifact_ref,
        "bridge_ref": bridge_ref,
        "field_path": field_path,
        "period": period,
        "unit": unit,
        "decision": decision,
        "decision_reason": decision_reason,
        "review_status": review_status,
        "follow_up_class": follow_up_class,
        "caveats": list(caveats or []),
        "not_for_trading_advice": True,
    }
    validate_bridge_review_decision(row)
    return row


def build_bridge_review_decisions_payload(
    *,
    code: str,
    company_name: str,
    decisions: list[dict],
    bridge_artifact_ref: str = "",
    created_at: str | None = None,
    summary: dict | None = None,
) -> dict:
    """Build and validate a bridge-aware review decisions payload in memory."""

    decision_rows = copy.deepcopy(decisions)
    payload = {
        "version": BRIDGE_REVIEW_DECISIONS_VERSION,
        "code": code,
        "company_name": company_name,
        "created_at": created_at if created_at is not None else _utc_now_text(),
        "bridge_artifact_ref": bridge_artifact_ref,
        "decisions": decision_rows,
        "summary": copy.deepcopy(summary) if summary is not None else _build_summary(decision_rows),
        "not_for_trading_advice": True,
    }
    validate_bridge_review_decisions_payload(payload)
    return payload


def build_official_candidate_review_decision(
    *,
    decision_id: str,
    candidate_id: str,
    artifact_ref: str,
    field_path: str = "",
    period: str = "",
    unit: str = "",
    evidence_tier: str = "L1_official_disclosure",
    extraction_confidence: str = "",
    has_trace: bool = True,
    denominator: str = "",
    source_lineage_mismatch: bool = False,
    caveat_only: bool = False,
    caveats: list[str] | None = None,
    decision: str | None = None,
    decision_reason: str = "",
    bridge_ref: str = "",
) -> dict:
    """Build an official-disclosure candidate review decision."""

    merged_caveats = list(caveats or [])
    selected_decision = decision or "manual_review_required"
    reason = decision_reason or "Official disclosure candidate requires human review before stronger use."

    if evidence_tier != "L1_official_disclosure" or not has_trace:
        selected_decision = "needs_more_evidence"
        reason = "Official candidate needs complete L1 source trace before review."
    if extraction_confidence == "structured_medium":
        selected_decision = "manual_review_required"
        reason = "structured_medium official extraction confidence still requires manual review."
        _append_unique(merged_caveats, "structured_medium_requires_manual_review")
    if not period or not unit or not denominator:
        selected_decision = "blocked_by_caveat"
        reason = "Missing period, unit, or denominator blocks accepted report-candidate use."
        _append_unique(merged_caveats, "missing_period_unit_or_denominator")
    if source_lineage_mismatch:
        selected_decision = "blocked_by_caveat"
        reason = "Source lineage mismatch blocks candidate use."
        _append_unique(merged_caveats, "source_lineage_mismatch")
    if caveat_only:
        selected_decision = "blocked_by_caveat"
        reason = "Caveat-only official evidence can only be recorded as caveat."
        _append_unique(merged_caveats, "caveat_only_official_evidence")
    if selected_decision == "accepted_for_report_candidate":
        _append_unique(merged_caveats, "accepted_for_report_candidate_not_verified")
        _append_unique(merged_caveats, "requires_later_report_v1_l1_evidence_design")

    return build_bridge_review_decision(
        decision_id=decision_id,
        source_type="official_disclosure_candidates",
        candidate_id=candidate_id,
        artifact_ref=artifact_ref,
        bridge_ref=bridge_ref,
        field_path=field_path,
        period=period,
        unit=unit,
        decision=selected_decision,
        decision_reason=reason,
        review_status=_review_status_for_decision(selected_decision),
        follow_up_class="official_evidence_review",
        caveats=merged_caveats,
    )


def build_provider_candidate_review_decision(
    *,
    decision_id: str,
    candidate_id: str,
    artifact_ref: str,
    field_path: str = "",
    period: str = "",
    unit: str = "",
    denominator: str = "",
    source_lineage_mismatch: bool = False,
    conflict_with_official: bool = False,
    caveats: list[str] | None = None,
    decision: str | None = None,
    decision_reason: str = "",
    bridge_ref: str = "",
) -> dict:
    """Build a provider candidate review decision."""

    merged_caveats = list(caveats or [])
    selected_decision = decision or "manual_review_required"
    reason = decision_reason or "Provider candidate remains review-only before promotion or report use."

    if not period or not unit or not denominator:
        selected_decision = "blocked_by_caveat"
        reason = "Missing period, unit, or denominator blocks accepted report-candidate use."
        _append_unique(merged_caveats, "missing_period_unit_or_denominator")
    if source_lineage_mismatch:
        selected_decision = "blocked_by_caveat"
        reason = "Source lineage mismatch blocks candidate use."
        _append_unique(merged_caveats, "source_lineage_mismatch")
    if conflict_with_official:
        selected_decision = "conflict_requires_review"
        reason = "Provider and official candidates conflict and require manual review."
        _append_unique(merged_caveats, "provider_official_conflict")

    return build_bridge_review_decision(
        decision_id=decision_id,
        source_type="provider_candidates",
        candidate_id=candidate_id,
        artifact_ref=artifact_ref,
        bridge_ref=bridge_ref,
        field_path=field_path,
        period=period,
        unit=unit,
        decision=selected_decision,
        decision_reason=reason,
        review_status=_review_status_for_decision(selected_decision),
        follow_up_class="provider_candidate_review",
        caveats=merged_caveats,
    )


def build_bridge_priority_review_decision(
    *,
    decision_id: str,
    candidate_id: str,
    artifact_ref: str,
    bridge_ref: str,
    field_path: str = "",
    period: str = "",
    unit: str = "",
    reason: str = "",
    priority_class: str = "",
    caveats: list[str] | None = None,
    conflict: bool = False,
    schema_mismatch: bool = False,
    decision: str | None = None,
) -> dict:
    """Build a bridge-priority review decision."""

    merged_caveats = list(caveats or [])
    selected_decision = decision or "manual_review_required"
    selected_reason = reason or "Bridge review priority is a review queue signal only."
    follow_up_class = "bridge_priority_review"

    if schema_mismatch:
        selected_decision = "needs_more_evidence"
        selected_reason = "Bridge schema mismatch blocks deep cross-source conflict matching."
        follow_up_class = "framework_schema_follow_up"
        _append_unique(merged_caveats, "cross_source_conflict_detection_not_performed_schema_mismatch")
    elif priority_class == "official_candidate":
        follow_up_class = "official_evidence_review"
    if conflict:
        selected_decision = "conflict_requires_review"
        selected_reason = "Bridge priority indicates provider / official conflict requiring manual review."
        follow_up_class = "cross_source_review"
        _append_unique(merged_caveats, "provider_official_conflict")

    return build_bridge_review_decision(
        decision_id=decision_id,
        source_type="bridge_review_priority",
        candidate_id=candidate_id,
        artifact_ref=artifact_ref,
        bridge_ref=bridge_ref,
        field_path=field_path,
        period=period,
        unit=unit,
        decision=selected_decision,
        decision_reason=selected_reason,
        review_status=_review_status_for_decision(selected_decision),
        follow_up_class=follow_up_class,
        caveats=merged_caveats,
    )


def validate_bridge_review_decision(row: dict) -> None:
    """Validate one bridge-aware review decision row."""

    if not isinstance(row, dict):
        raise CandidateReviewDecisionsBridgeValidationError("review decision row must be a dict")
    _assert_payload_safe(row)
    missing = REQUIRED_DECISION_KEYS - set(row)
    if missing:
        raise CandidateReviewDecisionsBridgeValidationError("review decision row missing required keys")
    if not _non_empty_string(row.get("decision_id")):
        raise CandidateReviewDecisionsBridgeValidationError("decision_id must be non-empty")
    if row.get("source_type") not in BRIDGE_REVIEW_SOURCE_TYPES:
        raise CandidateReviewDecisionsBridgeValidationError("source_type is unsupported")
    if not _non_empty_string(row.get("candidate_id")):
        raise CandidateReviewDecisionsBridgeValidationError("candidate_id must be non-empty")
    _validate_output_ref(row.get("artifact_ref"), "artifact_ref")
    bridge_ref = row.get("bridge_ref")
    if bridge_ref:
        _validate_output_ref(bridge_ref, "bridge_ref")
    if not _string_or_empty(row.get("field_path")):
        raise CandidateReviewDecisionsBridgeValidationError("field_path must be a string")
    if not _string_or_empty(row.get("period")):
        raise CandidateReviewDecisionsBridgeValidationError("period must be a string")
    if not _string_or_empty(row.get("unit")):
        raise CandidateReviewDecisionsBridgeValidationError("unit must be a string")
    if row.get("decision") not in BRIDGE_REVIEW_DECISIONS:
        raise CandidateReviewDecisionsBridgeValidationError("decision is unsupported")
    if not _non_empty_string(row.get("decision_reason")):
        raise CandidateReviewDecisionsBridgeValidationError("decision_reason must be non-empty")
    if not _string_or_empty(row.get("review_status")):
        raise CandidateReviewDecisionsBridgeValidationError("review_status must be a string")
    if not _string_or_empty(row.get("follow_up_class")):
        raise CandidateReviewDecisionsBridgeValidationError("follow_up_class must be a string")
    _validate_caveats(row.get("caveats"))
    if row.get("not_for_trading_advice") is not True:
        raise CandidateReviewDecisionsBridgeValidationError("not_for_trading_advice must be true")


def validate_bridge_review_decisions_payload(payload: dict) -> None:
    """Validate a bridge-aware review decisions payload."""

    if not isinstance(payload, dict):
        raise CandidateReviewDecisionsBridgeValidationError("review decisions payload must be a dict")
    _assert_payload_safe(payload)
    if payload.get("version") != BRIDGE_REVIEW_DECISIONS_VERSION:
        raise CandidateReviewDecisionsBridgeValidationError("review decisions bridge version is unsupported")
    if not isinstance(payload.get("code"), str) or not _A_SHARE_CODE_RE.match(payload["code"]):
        raise CandidateReviewDecisionsBridgeValidationError("code must be a 6 digit A-share code")
    if not _non_empty_string(payload.get("company_name")):
        raise CandidateReviewDecisionsBridgeValidationError("company_name must be non-empty")
    if not _string_or_empty(payload.get("created_at")):
        raise CandidateReviewDecisionsBridgeValidationError("created_at must be a string")
    bridge_artifact_ref = payload.get("bridge_artifact_ref")
    if bridge_artifact_ref:
        _validate_output_ref(bridge_artifact_ref, "bridge_artifact_ref")
    decisions = payload.get("decisions")
    if not isinstance(decisions, list):
        raise CandidateReviewDecisionsBridgeValidationError("decisions must be a list")
    for row in decisions:
        validate_bridge_review_decision(row)
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        raise CandidateReviewDecisionsBridgeValidationError("summary must be a dict")
    _validate_summary(summary, decisions)
    if payload.get("not_for_trading_advice") is not True:
        raise CandidateReviewDecisionsBridgeValidationError("not_for_trading_advice must be true")


def _build_summary(decisions: list[dict]) -> dict:
    return {
        "total_decisions": len(decisions),
        "provider_decision_count": _count_by_source(decisions, "provider_candidates"),
        "official_decision_count": _count_by_source(decisions, "official_disclosure_candidates"),
        "bridge_priority_decision_count": _count_by_source(decisions, "bridge_review_priority"),
        "manual_review_required_count": _count_by_decision(decisions, "manual_review_required"),
        "blocked_by_caveat_count": _count_by_decision(decisions, "blocked_by_caveat"),
        "accepted_for_report_candidate_count": _count_by_decision(decisions, "accepted_for_report_candidate"),
        "conflict_requires_review_count": _count_by_decision(decisions, "conflict_requires_review"),
    }


def _validate_summary(summary: dict, decisions: list[dict]) -> None:
    for key in SUMMARY_COUNT_KEYS & set(summary):
        value = summary[key]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise CandidateReviewDecisionsBridgeValidationError("summary counts must be non-negative integers")
    if "total_decisions" in summary and summary["total_decisions"] != len(decisions):
        raise CandidateReviewDecisionsBridgeValidationError("summary total_decisions does not match decisions length")


def _count_by_source(decisions: list[dict], source_type: str) -> int:
    return sum(1 for row in decisions if row.get("source_type") == source_type)


def _count_by_decision(decisions: list[dict], decision: str) -> int:
    return sum(1 for row in decisions if row.get("decision") == decision)


def _validate_output_ref(value: Any, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise CandidateReviewDecisionsBridgePathError(f"{label} must be a non-empty relative output path")
    path = value.strip()
    if "\\" in path or ":" in path:
        raise CandidateReviewDecisionsBridgePathError(f"{label} must use a relative output path")
    if path.startswith(("/", "~")):
        raise CandidateReviewDecisionsBridgePathError(f"{label} must be relative")
    if not path.startswith("output/"):
        raise CandidateReviewDecisionsBridgePathError(f"{label} must stay under output")
    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise CandidateReviewDecisionsBridgePathError(f"{label} contains invalid path segments")
    _assert_no_secret_like_string(path, label)


def _validate_caveats(value: Any) -> None:
    if not isinstance(value, list):
        raise CandidateReviewDecisionsBridgeValidationError("caveats must be a list")
    for item in value:
        if not isinstance(item, str):
            raise CandidateReviewDecisionsBridgeValidationError("caveats entries must be strings")
        _assert_no_secret_like_string(item, "caveats")


def _assert_payload_safe(payload: Any) -> None:
    _assert_no_forbidden_keys(payload)
    _assert_no_verified_marker(payload)
    _assert_no_secret_like_payload(payload)


def _assert_no_forbidden_keys(payload: Any) -> None:
    for key in _walk_keys(payload):
        lowered = str(key).lower()
        if lowered in FORBIDDEN_TRADING_RECOMMENDATION_KEYS:
            raise CandidateReviewDecisionsBridgeValidationError(
                "review decisions bridge payload contains forbidden trading recommendation keys"
            )
        if lowered in FORBIDDEN_SIDE_EFFECT_KEYS:
            raise CandidateReviewDecisionsBridgeValidationError(
                "review decisions bridge payload contains forbidden side-effect keys"
            )


def _assert_no_verified_marker(payload: Any) -> None:
    if _first_verified_marker(payload):
        raise CandidateReviewDecisionsBridgeValidationError("review decisions bridge payload contains verified marker")


def _first_verified_marker(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).lower()
            if lowered in {"verified_fact", "auto_verified"}:
                return True
            if lowered == "review_status" and isinstance(child, str) and child.lower() == "verified":
                return True
            if _first_verified_marker(child):
                return True
        return False
    if isinstance(value, list):
        return any(_first_verified_marker(child) for child in value)
    return isinstance(value, str) and value.lower() in {"verified_fact", "auto_verified"}


def _assert_no_secret_like_payload(payload: Any) -> None:
    finding = _first_secret_like_finding(payload, "$")
    if finding:
        raise CandidateReviewDecisionsBridgeSecretError(
            f"review decisions bridge payload contains secret-like data at {finding}: <masked>"
        )


def _first_secret_like_finding(value: Any, path: str) -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            safe_key = _safe_path_key(str(key))
            key_finding = _secret_string_finding(str(key), f"{path}.<masked_key>.__key__")
            if key_finding:
                return key_finding
            child_path = f"{path}.{safe_key}"
            child_finding = _first_secret_like_finding(child, child_path)
            if child_finding:
                return child_finding
        return None
    if isinstance(value, list):
        for index, child in enumerate(value):
            child_finding = _first_secret_like_finding(child, f"{path}[{index}]")
            if child_finding:
                return child_finding
        return None
    if isinstance(value, str):
        return _secret_string_finding(value, path)
    return None


def _assert_no_secret_like_string(value: str, label: str) -> None:
    finding = _secret_string_finding(value, label)
    if finding:
        raise CandidateReviewDecisionsBridgeSecretError(
            f"review decisions bridge payload contains secret-like data at {finding}: <masked>"
        )


def _secret_string_finding(value: str, path: str) -> str | None:
    if (
        _SECRET_KEY_RE.search(value)
        or _KEYED_SECRET_RE.search(value)
        or _BEARER_RE.search(value)
        or _REMOTE_CONTROL_RE.search(value)
        or _DOTENV_RE.search(value)
        or _TOKEN_LIKE_RE.search(value)
        or _LOCAL_SECRET_PATH_RE.search(value)
    ):
        return path
    return None


def _walk_keys(value: Any) -> list[str]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            keys.append(str(key))
            keys.extend(_walk_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.extend(_walk_keys(child))
    return keys


def _review_status_for_decision(decision: str) -> str:
    if decision == "accepted_for_report_candidate":
        return "reviewed_candidate_ready"
    if decision == "blocked_by_caveat":
        return "reviewed_caveated"
    if decision == "rejected":
        return "reviewed_rejected"
    if decision == "conflict_requires_review":
        return "reviewed_conflict_open"
    if decision == "needs_more_evidence":
        return "deferred"
    return "pending_human_review"


def _append_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_or_empty(value: Any) -> bool:
    return isinstance(value, str)


def _safe_path_key(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", value)[:64] or "<key>"


def _utc_now_text() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
