# -*- coding: utf-8 -*-
"""In-memory candidate source bridge artifact builder and validator."""

from __future__ import annotations

import copy
import re
from typing import Any


CANDIDATE_SOURCE_BRIDGE_VERSION = "candidate_source_bridge.v1"

CANDIDATE_SOURCE_TYPES = {
    "provider_candidates",
    "official_disclosure_candidates",
}

CROSS_SOURCE_CONFLICT_TYPES = {
    "value_mismatch",
    "unit_mismatch",
    "period_mismatch",
    "denominator_mismatch",
    "classification_mismatch",
    "source_lineage_mismatch",
}

CROSS_SOURCE_CONFLICT_SEVERITIES = {
    "manual_review_required",
    "blocked_by_caveat",
    "informational",
}

REVIEW_PRIORITIES = {
    "high",
    "medium",
    "low",
}

FORBIDDEN_RECOMMENDATION_KEYS = {
    "buy",
    "sell",
    "target_price",
    "position",
    "portfolio_weight",
}

FORBIDDEN_SIDE_EFFECT_KEYS = {
    "verified_fact",
    "auto_verified",
    "provider_primary",
    "primary_provider",
    "provider_primary_change",
    "provider_primary_switch",
    "switch_provider_primary",
    "research_report_v1_update",
}

REQUIRED_SOURCE_ENTRY_KEYS = {
    "source_type",
    "artifact_path",
    "candidate_count",
    "manual_review_count",
    "blocked_count",
    "source_summary",
    "not_for_trading_advice",
}

REQUIRED_CONFLICT_KEYS = {
    "conflict_id",
    "field_path",
    "period",
    "unit",
    "provider_candidate_ref",
    "official_candidate_ref",
    "conflict_type",
    "severity",
    "caveats",
}

REQUIRED_REVIEW_PRIORITY_KEYS = {
    "priority_id",
    "source_type",
    "candidate_ref",
    "field_path",
    "priority",
    "reason",
    "caveats",
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
_DOTENV_RE = re.compile(
    r"(^|[\\/:\s\"'`=])\.env(?:\.[A-Za-z0-9_-]+)*\b",
    flags=re.IGNORECASE,
)
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


class CandidateSourceBridgeError(RuntimeError):
    """Base error for candidate source bridge failures."""


class CandidateSourceBridgeValidationError(CandidateSourceBridgeError):
    """Raised when a candidate source bridge payload is invalid."""


class CandidateSourceBridgePathError(CandidateSourceBridgeValidationError):
    """Raised when an artifact path is outside the allowed local boundary."""


class CandidateSourceBridgeSecretError(CandidateSourceBridgeError):
    """Raised when secret-like material is detected."""


class CandidateSourceBridgeConflictError(CandidateSourceBridgeValidationError):
    """Raised when bridge conflict or review-signal metadata is invalid."""


def build_candidate_source_bridge(
    *,
    code: str,
    company_name: str,
    candidate_sources: list[dict],
    cross_source_conflicts: list[dict] | None = None,
    review_priorities: list[dict] | None = None,
    created_at: str | None = None,
) -> dict:
    """Build a candidate source bridge payload without reading or writing files."""

    payload = {
        "version": CANDIDATE_SOURCE_BRIDGE_VERSION,
        "code": code,
        "company_name": company_name,
        "created_at": created_at or "",
        "candidate_sources": copy.deepcopy(candidate_sources),
        "cross_source_conflicts": copy.deepcopy(cross_source_conflicts or []),
        "review_priorities": copy.deepcopy(review_priorities or []),
        "not_for_trading_advice": True,
    }
    validate_candidate_source_bridge(payload)
    return payload


def build_candidate_source_entry(
    *,
    source_type: str,
    artifact_path: str,
    candidate_count: int,
    manual_review_count: int,
    blocked_count: int,
    source_summary: Any = "",
    caveats: list[Any] | None = None,
    not_for_trading_advice: bool = True,
    **extra: Any,
) -> dict:
    """Build and validate one bridge source entry."""

    entry = {
        "source_type": source_type,
        "artifact_path": artifact_path,
        "candidate_count": candidate_count,
        "manual_review_count": manual_review_count,
        "blocked_count": blocked_count,
        "source_summary": copy.deepcopy(source_summary),
        "not_for_trading_advice": not_for_trading_advice,
    }
    if caveats is not None:
        entry["caveats"] = copy.deepcopy(caveats)
    entry.update(copy.deepcopy(extra))
    validate_candidate_source_entry(entry)
    return entry


def build_cross_source_conflict(
    *,
    conflict_id: str,
    field_path: str,
    provider_candidate_ref: Any,
    official_candidate_ref: Any,
    conflict_type: str,
    severity: str,
    period: str = "",
    unit: str = "",
    caveats: list[Any] | None = None,
) -> dict:
    """Build and validate one cross-source conflict review signal."""

    entry = {
        "conflict_id": conflict_id,
        "field_path": field_path,
        "period": period,
        "unit": unit,
        "provider_candidate_ref": copy.deepcopy(provider_candidate_ref),
        "official_candidate_ref": copy.deepcopy(official_candidate_ref),
        "conflict_type": conflict_type,
        "severity": severity,
        "caveats": copy.deepcopy(caveats or []),
    }
    validate_cross_source_conflict(entry)
    return entry


def build_review_priority(
    *,
    priority_id: str,
    source_type: str,
    candidate_ref: Any,
    field_path: str,
    priority: str,
    reason: str,
    caveats: list[Any] | None = None,
) -> dict:
    """Build and validate one review-priority signal."""

    entry = {
        "priority_id": priority_id,
        "source_type": source_type,
        "candidate_ref": copy.deepcopy(candidate_ref),
        "field_path": field_path,
        "priority": priority,
        "reason": reason,
        "caveats": copy.deepcopy(caveats or []),
    }
    validate_review_priority(entry)
    return entry


def validate_candidate_source_bridge(payload: dict) -> None:
    """Validate a candidate source bridge payload."""

    if not isinstance(payload, dict):
        raise CandidateSourceBridgeValidationError("candidate source bridge payload must be a dict")
    _assert_payload_safe(payload)
    if payload.get("version") != CANDIDATE_SOURCE_BRIDGE_VERSION:
        raise CandidateSourceBridgeValidationError("candidate source bridge version is unsupported")
    if not isinstance(payload.get("code"), str) or not _A_SHARE_CODE_RE.match(payload["code"]):
        raise CandidateSourceBridgeValidationError("code must be a 6 digit A-share code")
    if not _non_empty_string(payload.get("company_name")):
        raise CandidateSourceBridgeValidationError("company_name must be non-empty")
    if not isinstance(payload.get("created_at"), str):
        raise CandidateSourceBridgeValidationError("created_at must be a string")
    if payload.get("not_for_trading_advice") is not True:
        raise CandidateSourceBridgeValidationError("not_for_trading_advice must be true")

    candidate_sources = payload.get("candidate_sources")
    if not isinstance(candidate_sources, list) or not candidate_sources:
        raise CandidateSourceBridgeValidationError("candidate_sources must be a non-empty list")
    for entry in candidate_sources:
        validate_candidate_source_entry(entry)

    cross_source_conflicts = payload.get("cross_source_conflicts")
    if not isinstance(cross_source_conflicts, list):
        raise CandidateSourceBridgeValidationError("cross_source_conflicts must be a list")
    for entry in cross_source_conflicts:
        validate_cross_source_conflict(entry)

    review_priorities = payload.get("review_priorities")
    if not isinstance(review_priorities, list):
        raise CandidateSourceBridgeValidationError("review_priorities must be a list")
    for entry in review_priorities:
        validate_review_priority(entry)


def validate_candidate_source_entry(entry: dict) -> None:
    """Validate one candidate source entry."""

    if not isinstance(entry, dict):
        raise CandidateSourceBridgeValidationError("candidate source entry must be a dict")
    _assert_required_keys(entry, REQUIRED_SOURCE_ENTRY_KEYS, "candidate source entry")
    _assert_no_forbidden_recommendation_keys(entry)
    _assert_no_forbidden_side_effect_keys(entry)
    _assert_no_verified_marker(entry)
    if entry.get("source_type") not in CANDIDATE_SOURCE_TYPES:
        raise CandidateSourceBridgeValidationError("candidate source entry source_type is unsupported")
    _validate_output_artifact_path(entry.get("artifact_path"))
    _assert_no_secret_like_payload(entry)
    for key in ("candidate_count", "manual_review_count", "blocked_count"):
        if not _non_negative_int(entry.get(key)):
            raise CandidateSourceBridgeValidationError(f"{key} must be a non-negative integer")
    if entry["manual_review_count"] + entry["blocked_count"] > entry["candidate_count"] and not entry.get("caveats"):
        raise CandidateSourceBridgeValidationError("review and blocked counts exceed candidate_count without caveat")
    if entry.get("not_for_trading_advice") is not True:
        raise CandidateSourceBridgeValidationError("not_for_trading_advice must be true")
    _validate_caveats(entry.get("caveats", []), "candidate source entry caveats")


def validate_cross_source_conflict(entry: dict) -> None:
    """Validate one cross-source conflict entry."""

    if not isinstance(entry, dict):
        raise CandidateSourceBridgeConflictError("cross-source conflict must be a dict")
    _assert_required_keys(entry, REQUIRED_CONFLICT_KEYS, "cross-source conflict")
    _assert_payload_safe(entry)
    if not _non_empty_string(entry.get("conflict_id")):
        raise CandidateSourceBridgeConflictError("conflict_id must be non-empty")
    if not _non_empty_string(entry.get("field_path")):
        raise CandidateSourceBridgeConflictError("field_path must be non-empty")
    if not isinstance(entry.get("period"), str):
        raise CandidateSourceBridgeConflictError("period must be a string")
    if not isinstance(entry.get("unit"), str):
        raise CandidateSourceBridgeConflictError("unit must be a string")
    _validate_ref(entry.get("provider_candidate_ref"), "provider_candidate_ref")
    _validate_ref(entry.get("official_candidate_ref"), "official_candidate_ref")
    if entry.get("conflict_type") not in CROSS_SOURCE_CONFLICT_TYPES:
        raise CandidateSourceBridgeConflictError("conflict_type is unsupported")
    if entry.get("severity") not in CROSS_SOURCE_CONFLICT_SEVERITIES:
        raise CandidateSourceBridgeConflictError("severity is unsupported")
    _validate_caveats(entry.get("caveats"), "cross-source conflict caveats")
    if "not_for_trading_advice" in entry and entry.get("not_for_trading_advice") is not True:
        raise CandidateSourceBridgeConflictError("not_for_trading_advice must be true when present")


def validate_review_priority(entry: dict) -> None:
    """Validate one review-priority entry."""

    if not isinstance(entry, dict):
        raise CandidateSourceBridgeValidationError("review priority must be a dict")
    _assert_required_keys(entry, REQUIRED_REVIEW_PRIORITY_KEYS, "review priority")
    _assert_payload_safe(entry)
    if not _non_empty_string(entry.get("priority_id")):
        raise CandidateSourceBridgeValidationError("priority_id must be non-empty")
    if entry.get("source_type") not in CANDIDATE_SOURCE_TYPES:
        raise CandidateSourceBridgeValidationError("review priority source_type is unsupported")
    _validate_ref(entry.get("candidate_ref"), "candidate_ref")
    if not _non_empty_string(entry.get("field_path")):
        raise CandidateSourceBridgeValidationError("field_path must be non-empty")
    if entry.get("priority") not in REVIEW_PRIORITIES:
        raise CandidateSourceBridgeValidationError("priority is unsupported")
    if not _non_empty_string(entry.get("reason")):
        raise CandidateSourceBridgeValidationError("reason must be non-empty")
    _validate_caveats(entry.get("caveats"), "review priority caveats")
    if "not_for_trading_advice" in entry and entry.get("not_for_trading_advice") is not True:
        raise CandidateSourceBridgeValidationError("not_for_trading_advice must be true when present")


def _assert_required_keys(payload: dict, required_keys: set[str], label: str) -> None:
    missing = required_keys - set(payload)
    if missing:
        raise CandidateSourceBridgeValidationError(f"{label} missing required keys")


def _validate_output_artifact_path(value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        raise CandidateSourceBridgePathError("artifact_path must be a non-empty relative output path")
    path = value.strip()
    if "\\" in path or ":" in path:
        raise CandidateSourceBridgePathError("artifact_path must use a relative output path")
    if path.startswith(("/", "~")):
        raise CandidateSourceBridgePathError("artifact_path must be relative")
    if not path.startswith("output/"):
        raise CandidateSourceBridgePathError("artifact_path must stay under output")
    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise CandidateSourceBridgePathError("artifact_path contains invalid path segments")
    _assert_no_secret_like_string(path, "artifact_path")


def _validate_ref(value: Any, label: str) -> None:
    if isinstance(value, str):
        if not value.strip():
            raise CandidateSourceBridgeValidationError(f"{label} must be non-empty")
        _assert_no_secret_like_string(value, label)
        return
    if isinstance(value, dict):
        if not value:
            raise CandidateSourceBridgeValidationError(f"{label} must be non-empty")
        _assert_payload_safe(value)
        artifact_ref = value.get("artifact_ref")
        if isinstance(artifact_ref, str) and artifact_ref:
            _validate_output_artifact_path(artifact_ref)
        return
    raise CandidateSourceBridgeValidationError(f"{label} must be a string or dict")


def _validate_caveats(value: Any, label: str) -> None:
    if not isinstance(value, list):
        raise CandidateSourceBridgeValidationError(f"{label} must be a list")
    for item in value:
        if not isinstance(item, (str, dict)):
            raise CandidateSourceBridgeValidationError(f"{label} entries must be strings or dicts")
        _assert_payload_safe(item)


def _assert_payload_safe(payload: Any) -> None:
    _assert_no_forbidden_recommendation_keys(payload)
    _assert_no_forbidden_side_effect_keys(payload)
    _assert_no_verified_marker(payload)
    _assert_no_secret_like_payload(payload)


def _assert_no_forbidden_recommendation_keys(payload: Any) -> None:
    for key in _walk_keys(payload):
        if str(key).lower() in FORBIDDEN_RECOMMENDATION_KEYS:
            raise CandidateSourceBridgeValidationError("bridge payload contains forbidden trading recommendation keys")


def _assert_no_forbidden_side_effect_keys(payload: Any) -> None:
    for key in _walk_keys(payload):
        if str(key).lower() in FORBIDDEN_SIDE_EFFECT_KEYS:
            raise CandidateSourceBridgeValidationError("bridge payload contains forbidden side-effect keys")


def _assert_no_verified_marker(payload: Any) -> None:
    finding = _first_verified_marker(payload, "$")
    if finding:
        raise CandidateSourceBridgeValidationError("bridge payload contains verified marker")


def _first_verified_marker(value: Any, path: str) -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).lower()
            if lowered in {"verified_fact", "auto_verified"}:
                return f"{path}.{_safe_path_key(str(key))}"
            if lowered == "review_status" and isinstance(child, str) and child.lower() == "verified":
                return f"{path}.{_safe_path_key(str(key))}"
            child_finding = _first_verified_marker(child, f"{path}.{_safe_path_key(str(key))}")
            if child_finding:
                return child_finding
        return None
    if isinstance(value, list):
        for index, child in enumerate(value):
            child_finding = _first_verified_marker(child, f"{path}[{index}]")
            if child_finding:
                return child_finding
        return None
    if isinstance(value, str) and value.lower() == "verified_fact":
        return path
    return None


def _assert_no_secret_like_payload(payload: Any) -> None:
    finding = _first_secret_like_finding(payload, "$")
    if finding:
        raise CandidateSourceBridgeSecretError(f"bridge payload contains secret-like data at {finding}: <masked>")


def _first_secret_like_finding(value: Any, path: str) -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{_safe_path_key(str(key))}"
            key_finding = _secret_string_finding(str(key), f"{child_path}.__key__")
            if key_finding:
                return key_finding
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
        raise CandidateSourceBridgeSecretError(f"bridge payload contains secret-like data at {finding}: <masked>")


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


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _non_negative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _safe_path_key(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", value)[:64] or "<key>"
