# -*- coding: utf-8 -*-
"""Schema and validators for the autonomous ticker research planning gate.

The gate is intentionally planning-only. It validates payload shape, fail-closed
readiness flags, hypothesis provenance, and safety boundaries. It does not fetch
data, read manifests or artifacts, call models, or render reports.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import re
from typing import Any

from .safety import validate_payload_safety


SCHEMA_VERSION = "autonomous_ticker_research_planning_gate.v1"

IDENTITY_RESOLUTION_STATUSES = (
    "resolved",
    "ambiguous",
    "not_found",
    "conflict_requires_review",
    "blocked",
)

READINESS_LEVELS = (
    "accepted_report_ready",
    "experimental_report_ready",
    "data_collection_required",
    "classification_review_required",
    "evidence_conflict_review_required",
    "blocked",
)

HYPOTHESIS_TYPES = (
    "industry",
    "supply_chain_position",
    "industry_driver",
    "macro_factor",
    "business_model",
    "data_gap",
    "conflict",
)

CONFIDENCE_LEVELS = ("high", "medium", "low", "not_assessable")

ALLOWED_DOWNSTREAM_USES = (
    "planning_only",
    "data_collection_prioritization",
    "experimental_report_context_candidate",
    "blocked_until_review",
    "not_allowed_downstream",
)

REQUIRED_RESEARCH_PACK_OUTPUTS = (
    "Professional Research Report",
    "Evidence Panel",
    "Readiness Card",
    "Data Gap Plan",
    "Audit Manifest",
)

DEFAULT_RESEARCH_PACK_PLACEHOLDERS = {
    "professional_research_report": {
        "title": "Professional Research Report",
        "status": "placeholder_only",
    },
    "evidence_panel": {"title": "Evidence Panel", "status": "placeholder_only"},
    "readiness_card": {"title": "Readiness Card", "status": "placeholder_only"},
    "data_gap_plan": {"title": "Data Gap Plan", "status": "placeholder_only"},
    "audit_manifest": {"title": "Audit Manifest", "status": "placeholder_only"},
}

REQUIRED_PAYLOAD_FIELDS = (
    "schema_version",
    "generated_at",
    "stock_code",
    "company_name",
    "identity_resolution_status",
    "market",
    "exchange",
    "evidence_inventory",
    "business_description_evidence",
    "industry_hypotheses",
    "supply_chain_position_hypotheses",
    "macro_factor_hypotheses",
    "key_research_questions",
    "required_data_plan",
    "available_data_artifacts",
    "missing_data_artifacts",
    "evidence_confidence",
    "hypothesis_confidence",
    "report_readiness_level",
    "can_generate_accepted_report",
    "can_generate_experimental_report",
    "fail_closed_reason",
    "caveats",
    "research_pack_placeholders",
    "not_for_trading_advice",
)

_HYPOTHESIS_REQUIRED_FIELDS = (
    "hypothesis_id",
    "hypothesis_type",
    "hypothesis_text",
    "evidence_refs",
    "confidence",
    "caveats",
    "required_follow_up_data",
    "allowed_downstream_use",
)

_HYPOTHESIS_LIST_FIELDS = (
    "industry_hypotheses",
    "supply_chain_position_hypotheses",
    "macro_factor_hypotheses",
)

_PAYLOAD_LIST_FIELDS = (
    "evidence_inventory",
    "business_description_evidence",
    "industry_hypotheses",
    "supply_chain_position_hypotheses",
    "macro_factor_hypotheses",
    "key_research_questions",
    "required_data_plan",
    "available_data_artifacts",
    "missing_data_artifacts",
    "caveats",
)

_FORBIDDEN_DOWNSTREAM_USE_MARKERS = (
    "accepted_report_fact",
    "accepted_fact",
    "verified_fact",
    "auto_verified",
    "verified_report_fact",
    "report_fact_verified",
)


def _normalise_marker(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _normalise_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.strip().lower())


def _require_dict(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{path} must be a dict")
    return value


def _require_non_empty_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path} must be a non-empty string")
    return value


def _require_string(value: Any, path: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{path} must be a string")
    return value


def _require_bool(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{path} must be a boolean")
    return value


def _require_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{path} must be a list")
    return value


def _require_enum(value: Any, allowed: tuple[str, ...], path: str) -> str:
    text = _require_non_empty_string(value, path)
    if text not in allowed:
        raise ValueError(f"{path} must be one of {sorted(allowed)}")
    return text


def _validate_stock_code(value: Any) -> str:
    stock_code = _require_non_empty_string(value, "stock_code")
    if not re.fullmatch(r"\d{6}", stock_code):
        raise ValueError("stock_code must be a six-digit ticker code")
    return stock_code


def _validate_schema_version(value: Any) -> str:
    version = _require_non_empty_string(value, "schema_version")
    if version != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
    return version


def _validate_generated_at(value: Any) -> str:
    generated_at = _require_non_empty_string(value, "generated_at")
    candidate = generated_at[:-1] + "+00:00" if generated_at.endswith("Z") else generated_at
    try:
        datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError("generated_at must be ISO-8601 compatible") from exc
    return generated_at


def _validate_research_pack_placeholders(value: Any) -> None:
    placeholders = value
    found: set[str] = set()

    def collect(item: Any) -> None:
        if isinstance(item, str):
            found.add(_normalise_title(item))
            return
        if isinstance(item, dict):
            for field in ("title", "name", "output", "artifact"):
                candidate = item.get(field)
                if isinstance(candidate, str):
                    found.add(_normalise_title(candidate))

    if isinstance(placeholders, dict):
        for key, item in placeholders.items():
            found.add(_normalise_title(str(key)))
            collect(item)
    elif isinstance(placeholders, list):
        for item in placeholders:
            collect(item)
    else:
        raise ValueError("research_pack_placeholders must be a dict or list")

    missing = [
        title
        for title in REQUIRED_RESEARCH_PACK_OUTPUTS
        if _normalise_title(title) not in found
    ]
    if missing:
        raise ValueError(f"research_pack_placeholders missing required outputs: {missing}")


def _downstream_use_looks_verified(value: str) -> bool:
    marker = _normalise_marker(value)
    if marker in _FORBIDDEN_DOWNSTREAM_USE_MARKERS:
        return True
    return ("verified" in marker and "fact" in marker) or (
        "accepted" in marker and "fact" in marker
    )


def _allows_missing_evidence(hypothesis: dict[str, Any]) -> bool:
    return (
        hypothesis["hypothesis_type"] == "data_gap"
        or hypothesis["confidence"] == "not_assessable"
        or hypothesis["allowed_downstream_use"]
        in {"blocked_until_review", "not_allowed_downstream"}
    )


def build_hypothesis(
    *,
    hypothesis_id: str,
    hypothesis_type: str,
    hypothesis_text: str,
    evidence_refs: list[str] | None = None,
    confidence: str = "not_assessable",
    caveats: list[str] | None = None,
    required_follow_up_data: list[str] | None = None,
    allowed_downstream_use: str = "planning_only",
) -> dict[str, Any]:
    """Build and validate a planning-only hypothesis payload."""

    payload = {
        "hypothesis_id": hypothesis_id,
        "hypothesis_type": hypothesis_type,
        "hypothesis_text": hypothesis_text,
        "evidence_refs": list(evidence_refs or []),
        "confidence": confidence,
        "caveats": list(caveats or []),
        "required_follow_up_data": list(required_follow_up_data or []),
        "allowed_downstream_use": allowed_downstream_use,
    }
    return validate_hypothesis(payload)


def validate_hypothesis(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate one planning hypothesis and return it unchanged when valid."""

    hypothesis = _require_dict(payload, "hypothesis")
    missing = [field for field in _HYPOTHESIS_REQUIRED_FIELDS if field not in hypothesis]
    if missing:
        raise ValueError(f"hypothesis missing required fields: {missing}")

    _require_non_empty_string(hypothesis["hypothesis_id"], "hypothesis.hypothesis_id")
    _require_enum(hypothesis["hypothesis_type"], HYPOTHESIS_TYPES, "hypothesis.hypothesis_type")
    _require_non_empty_string(hypothesis["hypothesis_text"], "hypothesis.hypothesis_text")
    evidence_refs = _require_list(hypothesis["evidence_refs"], "hypothesis.evidence_refs")
    _require_enum(hypothesis["confidence"], CONFIDENCE_LEVELS, "hypothesis.confidence")
    _require_list(hypothesis["caveats"], "hypothesis.caveats")
    _require_list(
        hypothesis["required_follow_up_data"],
        "hypothesis.required_follow_up_data",
    )

    downstream_use = _require_non_empty_string(
        hypothesis["allowed_downstream_use"],
        "hypothesis.allowed_downstream_use",
    )
    if _downstream_use_looks_verified(downstream_use):
        raise ValueError("hypothesis.allowed_downstream_use must not claim accepted or verified fact status")
    if downstream_use not in ALLOWED_DOWNSTREAM_USES:
        raise ValueError(
            f"hypothesis.allowed_downstream_use must be one of {sorted(ALLOWED_DOWNSTREAM_USES)}"
        )
    if not evidence_refs and not _allows_missing_evidence(hypothesis):
        raise ValueError(
            "hypothesis.evidence_refs cannot be empty unless the hypothesis is a blocked data gap, "
            "not assessable, or blocked until review"
        )

    validate_payload_safety(hypothesis)
    return hypothesis


def build_planning_payload(
    *,
    stock_code: str,
    company_name: str,
    generated_at: str | None = None,
    identity_resolution_status: str = "blocked",
    market: str = "CN",
    exchange: str = "unknown",
    evidence_inventory: list[Any] | None = None,
    business_description_evidence: list[Any] | None = None,
    industry_hypotheses: list[dict[str, Any]] | None = None,
    supply_chain_position_hypotheses: list[dict[str, Any]] | None = None,
    macro_factor_hypotheses: list[dict[str, Any]] | None = None,
    key_research_questions: list[Any] | None = None,
    required_data_plan: list[Any] | None = None,
    available_data_artifacts: list[Any] | None = None,
    missing_data_artifacts: list[Any] | None = None,
    evidence_confidence: str = "not_assessable",
    hypothesis_confidence: str = "not_assessable",
    report_readiness_level: str = "blocked",
    can_generate_accepted_report: bool = False,
    can_generate_experimental_report: bool = False,
    fail_closed_reason: str = "",
    caveats: list[str] | None = None,
    research_pack_placeholders: dict[str, Any] | list[Any] | None = None,
    not_for_trading_advice: bool = True,
) -> dict[str, Any]:
    """Build and validate a planning-gate payload without side effects."""

    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at
        or datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "stock_code": stock_code,
        "company_name": company_name,
        "identity_resolution_status": identity_resolution_status,
        "market": market,
        "exchange": exchange,
        "evidence_inventory": list(evidence_inventory or []),
        "business_description_evidence": list(business_description_evidence or []),
        "industry_hypotheses": list(industry_hypotheses or []),
        "supply_chain_position_hypotheses": list(supply_chain_position_hypotheses or []),
        "macro_factor_hypotheses": list(macro_factor_hypotheses or []),
        "key_research_questions": list(key_research_questions or []),
        "required_data_plan": list(required_data_plan or []),
        "available_data_artifacts": list(available_data_artifacts or []),
        "missing_data_artifacts": list(missing_data_artifacts or []),
        "evidence_confidence": evidence_confidence,
        "hypothesis_confidence": hypothesis_confidence,
        "report_readiness_level": report_readiness_level,
        "can_generate_accepted_report": can_generate_accepted_report,
        "can_generate_experimental_report": can_generate_experimental_report,
        "fail_closed_reason": fail_closed_reason,
        "caveats": list(caveats or []),
        "research_pack_placeholders": deepcopy(
            research_pack_placeholders or DEFAULT_RESEARCH_PACK_PLACEHOLDERS
        ),
        "not_for_trading_advice": not_for_trading_advice,
    }
    return validate_planning_payload(payload)


def validate_not_for_trading_advice(payload: dict[str, Any]) -> None:
    """Require the explicit non-trading-advice guardrail."""

    _require_dict(payload, "planning_payload")
    if "not_for_trading_advice" not in payload:
        raise ValueError("not_for_trading_advice is required and must be true")
    if payload["not_for_trading_advice"] is not True:
        raise ValueError("not_for_trading_advice must be true")


def validate_readiness_consistency(payload: dict[str, Any]) -> None:
    """Validate fail-closed readiness flags."""

    planning_payload = _require_dict(payload, "planning_payload")
    validate_not_for_trading_advice(planning_payload)

    identity_status = _require_enum(
        planning_payload.get("identity_resolution_status"),
        IDENTITY_RESOLUTION_STATUSES,
        "identity_resolution_status",
    )
    readiness = _require_enum(
        planning_payload.get("report_readiness_level"),
        READINESS_LEVELS,
        "report_readiness_level",
    )
    accepted = _require_bool(
        planning_payload.get("can_generate_accepted_report"),
        "can_generate_accepted_report",
    )
    experimental = _require_bool(
        planning_payload.get("can_generate_experimental_report"),
        "can_generate_experimental_report",
    )

    if identity_status != "resolved" and accepted:
        raise ValueError("can_generate_accepted_report must be false unless identity is resolved")
    if readiness == "blocked" and (accepted or experimental):
        raise ValueError("blocked readiness must fail closed for accepted and experimental reports")
    if readiness == "data_collection_required" and accepted:
        raise ValueError("data_collection_required cannot generate an accepted report")
    if readiness in {
        "classification_review_required",
        "evidence_conflict_review_required",
    } and accepted:
        raise ValueError(f"{readiness} cannot generate an accepted report")
    if experimental and readiness not in {
        "experimental_report_ready",
        "accepted_report_ready",
    }:
        raise ValueError(
            "can_generate_experimental_report requires experimental_report_ready or accepted_report_ready"
        )
    if accepted and readiness != "accepted_report_ready":
        raise ValueError("can_generate_accepted_report requires accepted_report_ready")
    if readiness == "experimental_report_ready" and accepted:
        raise ValueError("experimental_report_ready cannot generate an accepted report")


def validate_planning_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate a complete autonomous ticker research planning gate payload."""

    planning_payload = _require_dict(payload, "planning_payload")
    missing = [field for field in REQUIRED_PAYLOAD_FIELDS if field not in planning_payload]
    if missing:
        raise ValueError(f"planning_payload missing required fields: {missing}")

    _validate_schema_version(planning_payload["schema_version"])
    _validate_generated_at(planning_payload["generated_at"])
    _validate_stock_code(planning_payload["stock_code"])
    _require_non_empty_string(planning_payload["company_name"], "company_name")
    _require_enum(
        planning_payload["identity_resolution_status"],
        IDENTITY_RESOLUTION_STATUSES,
        "identity_resolution_status",
    )
    _require_non_empty_string(planning_payload["market"], "market")
    _require_non_empty_string(planning_payload["exchange"], "exchange")

    for field in _PAYLOAD_LIST_FIELDS:
        _require_list(planning_payload[field], field)

    _require_enum(
        planning_payload["evidence_confidence"],
        CONFIDENCE_LEVELS,
        "evidence_confidence",
    )
    _require_enum(
        planning_payload["hypothesis_confidence"],
        CONFIDENCE_LEVELS,
        "hypothesis_confidence",
    )
    _require_enum(
        planning_payload["report_readiness_level"],
        READINESS_LEVELS,
        "report_readiness_level",
    )
    _require_bool(
        planning_payload["can_generate_accepted_report"],
        "can_generate_accepted_report",
    )
    _require_bool(
        planning_payload["can_generate_experimental_report"],
        "can_generate_experimental_report",
    )
    _require_string(planning_payload["fail_closed_reason"], "fail_closed_reason")
    _validate_research_pack_placeholders(planning_payload["research_pack_placeholders"])

    for field in _HYPOTHESIS_LIST_FIELDS:
        for index, hypothesis in enumerate(planning_payload[field]):
            try:
                validate_hypothesis(hypothesis)
            except ValueError as exc:
                raise ValueError(f"{field}[{index}] invalid: {exc}") from exc

    validate_not_for_trading_advice(planning_payload)
    validate_readiness_consistency(planning_payload)
    validate_payload_safety(planning_payload)
    return planning_payload
