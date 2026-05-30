# -*- coding: utf-8 -*-
"""Phase 4 bounded hypothesis payload schema and deterministic validators.

This module is intentionally pure and side-effect free. It validates in-memory
Phase 3 readiness payloads, bounded hypothesis items, blocked hypothesis items,
and assembled Phase 4 payloads. It does not call models, read files, scan
directories, call providers, or render reports.
"""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

from .autonomous_ticker_research_schema import (
    ALLOWED_DOWNSTREAM_USES,
    CONFIDENCE_LEVELS,
    HYPOTHESIS_TYPES,
    IDENTITY_RESOLUTION_STATUSES,
    READINESS_LEVELS,
)
from .evidence_readiness import (
    validate_deterministic_evidence_inventory,
    validate_readiness_skeleton,
)
from .safety import validate_payload_safety


BOUNDED_HYPOTHESIS_REQUEST_SCHEMA_VERSION = "bounded_hypothesis_request.v1"
BOUNDED_HYPOTHESIS_PAYLOAD_SCHEMA_VERSION = "bounded_hypothesis_payload.v1"

HYPOTHESIS_LIST_FIELDS = (
    "industry_hypotheses",
    "supply_chain_position_hypotheses",
    "business_model_hypotheses",
    "macro_factor_hypotheses",
)

PAYLOAD_REQUIRED_FIELDS = (
    "schema_version",
    "stock_code",
    "company_name",
    "source_readiness_level",
    "industry_hypotheses",
    "supply_chain_position_hypotheses",
    "business_model_hypotheses",
    "macro_factor_hypotheses",
    "key_research_questions",
    "required_follow_up_data",
    "blocked_hypotheses",
    "caveats",
    "lineage_refs",
    "not_for_trading_advice",
)

REQUEST_ALLOWED_FIELDS = (
    "schema_version",
    "stock_code",
    "company_name",
    "deterministic_evidence_inventory",
    "readiness_skeleton",
    "not_for_trading_advice",
)

REQUEST_FORBIDDEN_CONTEXT_FIELDS = (
    "context",
    "reasoning_context",
    "bounded_reasoning_context",
    "bounded_model_reasoning_context",
)

HYPOTHESIS_REQUIRED_FIELDS = (
    "hypothesis_id",
    "hypothesis_type",
    "hypothesis_text",
    "evidence_refs",
    "evidence_state_refs",
    "confidence",
    "caveats",
    "required_follow_up_data",
    "allowed_downstream_use",
    "not_for_trading_advice",
)

HYPOTHESIS_OPTIONAL_FIELDS = (
    "transmission_path",
    "transmission_path_summary",
    "reasoning_summary",
)

BLOCKED_HYPOTHESIS_REQUIRED_FIELDS = (
    "hypothesis_id",
    "hypothesis_type",
    "hypothesis_text",
    "block_reason",
    "evidence_state_refs",
    "required_follow_up_data",
    "caveats",
    "not_for_trading_advice",
)

BLOCKED_HYPOTHESIS_OPTIONAL_FIELDS = (
    "evidence_refs",
    "confidence",
    "transmission_path",
    "transmission_path_summary",
)

BLOCK_REASONS = (
    "unresolved_identity",
    "blocked_readiness",
    "evidence_conflict",
    "missing_required_evidence",
    "candidate_only_evidence",
    "review_required_evidence",
    "forbidden_marker",
    "not_for_trading_advice_violation",
    "other",
)

_HYPOTHESIS_TYPE_BY_LIST_FIELD = {
    "industry_hypotheses": {"industry", "industry_driver"},
    "supply_chain_position_hypotheses": {"supply_chain_position"},
    "business_model_hypotheses": {"business_model"},
    "macro_factor_hypotheses": {"macro_factor"},
}

_READINESS_ALLOWED_DOWNSTREAM_USES = {
    "accepted_report_ready": set(ALLOWED_DOWNSTREAM_USES),
    "experimental_report_ready": set(ALLOWED_DOWNSTREAM_USES),
    "data_collection_required": {
        "planning_only",
        "data_collection_prioritization",
        "blocked_until_review",
        "not_allowed_downstream",
    },
    "classification_review_required": {
        "planning_only",
        "blocked_until_review",
        "not_allowed_downstream",
    },
    "evidence_conflict_review_required": {
        "blocked_until_review",
        "not_allowed_downstream",
    },
    "blocked": {
        "not_allowed_downstream",
    },
}

_BLOCKED_ONLY_DOWNSTREAM_USES = {"blocked_until_review", "not_allowed_downstream"}
_REVIEW_CEILING_DOWNSTREAM_USES = {
    "planning_only",
    "blocked_until_review",
    "not_allowed_downstream",
}

_PROHIBITED_DOWNSTREAM_USE_MARKERS = (
    "verified_fact",
    "accepted_report_fact",
    "accepted_fact",
    "report_fact",
    "trading_signal",
    "target_price",
    "buy_sell_decision",
    "portfolio_weight",
)

_PROHIBITED_PAYLOAD_KEYS = (
    "verified_fact",
    "verified_facts",
    "accepted_report_fact",
    "accepted_report_facts",
    "report_fact",
    "report_facts",
    "report_section",
    "report_sections",
    "research_report",
    "research_report_v1_section",
    "dashboard_payload",
    "template_payload",
    "provider_payload",
    "target_price",
    "price_target",
    "trading_signal",
    "buy_sell_decision",
    "portfolio_weight",
    "position_size",
)

_FORBIDDEN_TEXT_MARKERS = (
    "verified_fact",
    "accepted_report_fact",
    "report_fact",
    "research_report_v1_section",
    "report_section",
    "dashboard_payload",
    "template_payload",
    "target_price",
    "price_target",
    "portfolio_weight",
    "portfolio_allocation",
    "trading_signal",
    "technical_signal",
    "investment_recommendation",
    "investment_advice",
    "buy_recommendation",
    "sell_recommendation",
    "buy_signal",
    "sell_signal",
    "provider_primary_switch",
    "fixture_promotion",
    "manifest_update",
)

_TRADING_PHRASE_PATTERNS = (
    re.compile(r"\b(buy|sell)\b", re.IGNORECASE),
    re.compile(r"\btarget\s+price\b", re.IGNORECASE),
    re.compile(r"\bprice\s+target\b", re.IGNORECASE),
    re.compile(r"\btrading\s+signal\b", re.IGNORECASE),
    re.compile(r"\binvestment\s+recommendation\b", re.IGNORECASE),
    re.compile(r"\bportfolio\s+weight\b", re.IGNORECASE),
)

_TRADING_CN_PHRASES = (
    "\u4e70\u5165",
    "\u5356\u51fa",
    "\u76ee\u6807\u4ef7",
    "\u4ed3\u4f4d",
    "\u7ec4\u5408\u6743\u91cd",
    "\u4ea4\u6613\u4fe1\u53f7",
    "\u6295\u8d44\u5efa\u8bae",
)

_STATE_MARKERS = {
    "candidate_only": "candidate_only",
    "review_required": "review_required",
    "conflict_open": "conflict_open",
    "conflict_artifacts": "conflict_open",
    "evidence_conflict_review_required": "conflict_open",
    "blocked": "blocked",
    "missing": "missing",
    "unreadable": "missing",
}

_BLOCKING_STATE_MARKERS = (
    "blocked",
    "conflict",
    "non_empty",
    "missing",
    "candidate_only",
    "review_required",
    "critical_financial",
    "official_business",
    "evidence_conflict_review_required",
)


def _normalise_marker(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _require_dict(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be a dict")
    return value


def _require_non_empty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _require_string(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    return value


def _require_bool_true(value: Any, field: str) -> None:
    if value is not True:
        raise ValueError(f"{field} must be true")


def _require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    return value


def _require_string_list(value: Any, field: str, *, allow_empty: bool = True) -> list[str]:
    items = _require_list(value, field)
    if not allow_empty and not items:
        raise ValueError(f"{field} must not be empty")
    result: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field}[{index}] must be a non-empty string")
        result.append(item)
    return result


def _require_enum(value: Any, allowed: tuple[str, ...], field: str) -> str:
    text = _require_non_empty_string(value, field)
    if text not in allowed:
        raise ValueError(f"{field} must be one of {sorted(allowed)}")
    return text


def _require_stock_code(value: Any, field: str) -> str:
    stock_code = _require_non_empty_string(value, field)
    if not re.fullmatch(r"\d{6}", stock_code):
        raise ValueError(f"{field} must be a six-digit stock code")
    return stock_code


def _iter_keys_and_strings(value: Any) -> list[tuple[str, str, bool]]:
    collected: list[tuple[str, str, bool]] = []

    def visit(child: Any, path: str) -> None:
        if isinstance(child, dict):
            for key, nested in child.items():
                key_text = str(key)
                child_path = f"{path}.{key_text}" if path else key_text
                collected.append((child_path, key_text, True))
                visit(nested, child_path)
            return
        if isinstance(child, list):
            for index, nested in enumerate(child):
                visit(nested, f"{path}[{index}]")
            return
        if isinstance(child, str):
            collected.append((path, child, False))

    visit(value, "")
    return collected


def _reject_prohibited_keys(payload: Any) -> None:
    prohibited = {_normalise_marker(key) for key in _PROHIBITED_PAYLOAD_KEYS}
    for path, text, is_key in _iter_keys_and_strings(payload):
        if is_key and _normalise_marker(text) in prohibited:
            raise ValueError(f"{path} is a prohibited report, dashboard, provider, or trading key")


def _reject_forbidden_markers(payload: Any) -> None:
    markers = tuple(_normalise_marker(marker) for marker in _FORBIDDEN_TEXT_MARKERS)
    for path, text, is_key in _iter_keys_and_strings(payload):
        normalised = _normalise_marker(text)
        if is_key and normalised == "not_for_trading_advice":
            continue
        for marker in markers:
            if marker and marker in normalised:
                raise ValueError(f"{path} contains forbidden Phase 4 marker: {marker}")
        if not is_key:
            if any(pattern.search(text) for pattern in _TRADING_PHRASE_PATTERNS):
                raise ValueError(f"{path} contains trading advice or recommendation language")
            if any(phrase in text for phrase in _TRADING_CN_PHRASES):
                raise ValueError(f"{path} contains trading advice or recommendation language")


def _validate_payload_safety(payload: Any) -> None:
    _reject_prohibited_keys(payload)
    _reject_forbidden_markers(payload)
    validate_payload_safety(payload)


def _downstream_use_looks_forbidden(value: str) -> bool:
    normalised = _normalise_marker(value)
    return any(marker in normalised for marker in _PROHIBITED_DOWNSTREAM_USE_MARKERS)


def _validate_downstream_use(value: Any, field: str) -> str:
    downstream_use = _require_non_empty_string(value, field)
    if _downstream_use_looks_forbidden(downstream_use):
        raise ValueError(f"{field} must not claim verified, report, trading, target, or portfolio use")
    if downstream_use not in ALLOWED_DOWNSTREAM_USES:
        raise ValueError(f"{field} must be one of {sorted(ALLOWED_DOWNSTREAM_USES)}")
    return downstream_use


def _reject_cross_ticker_refs(refs: list[str], stock_code: str, field: str) -> None:
    for index, ref in enumerate(refs):
        for candidate in re.findall(r"(?<!\d)(\d{6})(?!\d)", ref):
            if candidate != stock_code:
                raise ValueError(f"{field}[{index}] references another stock_code: {candidate}")


def _rows_by_artifact_id(*payloads: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for payload in payloads:
        if not payload:
            continue
        for field in (
            "evidence_inventory",
            "available_data_artifacts",
            "missing_data_artifacts",
            "candidate_only_artifacts",
            "review_required_artifacts",
            "conflict_artifacts",
            "ignored_artifacts",
        ):
            for row in payload.get(field, []):
                if isinstance(row, dict) and isinstance(row.get("artifact_id"), str):
                    rows[row["artifact_id"]] = row
    return rows


def _artifact_id_from_artifact_ref(ref: str) -> str | None:
    parts = ref.split(":")
    if len(parts) < 3:
        return None
    if parts[0] not in {"deterministic_evidence_inventory.v1", "readiness_skeleton.v1"}:
        return None
    if parts[1] != "evidence_inventory":
        return None
    if len(parts) >= 4 and re.fullmatch(r"\d{6}", parts[2]):
        return parts[3]
    return parts[2]


def _validate_artifact_refs_exist(
    refs: list[str],
    rows: dict[str, dict[str, Any]],
    field: str,
) -> None:
    for index, ref in enumerate(refs):
        artifact_id = _artifact_id_from_artifact_ref(ref)
        if artifact_id is not None and artifact_id not in rows:
            raise ValueError(f"{field}[{index}] references unknown artifact_id: {artifact_id}")


def _row_states(row: dict[str, Any]) -> set[str]:
    states: set[str] = set()
    for field in ("source_status", "review_status", "freshness_status"):
        value = row.get(field)
        if isinstance(value, str):
            normalised = _normalise_marker(value)
            if normalised in _STATE_MARKERS:
                states.add(_STATE_MARKERS[normalised])
            elif normalised in {"available", "accepted", "current", "reviewed"}:
                states.add(normalised)
    return states


def _states_from_ref_text(ref: str) -> set[str]:
    normalised = _normalise_marker(ref)
    states: set[str] = set()
    for marker, state in _STATE_MARKERS.items():
        if marker in normalised:
            states.add(state)
    return states


def _referenced_evidence_states(refs: list[str], rows: dict[str, dict[str, Any]]) -> set[str]:
    states: set[str] = set()
    for ref in refs:
        states.update(_states_from_ref_text(ref))
        for artifact_id, row in rows.items():
            if artifact_id and artifact_id in ref:
                states.update(_row_states(row))
    return states


def _validate_phase3_pair(
    deterministic_evidence_inventory: dict[str, Any],
    readiness_skeleton: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    evidence_inventory = validate_deterministic_evidence_inventory(deterministic_evidence_inventory)
    skeleton = validate_readiness_skeleton(readiness_skeleton)

    linked_fields = (
        "stock_code",
        "company_name",
        "identity_resolution_status",
        "evidence_inventory",
        "available_data_artifacts",
        "missing_data_artifacts",
        "candidate_only_artifacts",
        "review_required_artifacts",
        "conflict_artifacts",
        "ignored_artifacts",
        "readiness_evidence_categories",
    )
    for field in linked_fields:
        if evidence_inventory[field] != skeleton[field]:
            raise ValueError(f"Phase 3 inputs are inconsistent for {field}")
    return evidence_inventory, skeleton


def _resolve_stock_code(stock_code: str | None, evidence_inventory: dict[str, Any], skeleton: dict[str, Any]) -> str:
    phase3_stock_code = evidence_inventory["stock_code"]
    if skeleton["stock_code"] != phase3_stock_code:
        raise ValueError("Phase 3 stock_code values must match")
    if stock_code is not None and stock_code != phase3_stock_code:
        raise ValueError("stock_code hint must match validated Phase 3 payloads")
    return phase3_stock_code


def _resolve_company_name(company_name: str | None, evidence_inventory: dict[str, Any], skeleton: dict[str, Any]) -> str:
    phase3_company_name = evidence_inventory["company_name"]
    if skeleton["company_name"] != phase3_company_name:
        raise ValueError("Phase 3 company_name values must match")
    if company_name is not None and company_name != phase3_company_name:
        raise ValueError("company_name hint must not conflict with validated Phase 3 payloads")
    return phase3_company_name


def _validate_schema_keys(
    payload: dict[str, Any],
    required: tuple[str, ...],
    optional: tuple[str, ...],
    field: str,
) -> None:
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f"{field} missing required fields: {missing}")
    extra = set(payload) - set(required) - set(optional)
    if extra:
        raise ValueError(f"{field} has unsupported fields: {sorted(extra)}")


def _validate_readiness_ceiling(
    *,
    downstream_use: str,
    readiness_level: str | None,
    identity_resolution_status: str | None,
    states: set[str],
) -> None:
    if identity_resolution_status is not None and identity_resolution_status != "resolved":
        if downstream_use not in _BLOCKED_ONLY_DOWNSTREAM_USES:
            raise ValueError(
                f"identity status {identity_resolution_status} must fail closed for downstream use"
            )

    if readiness_level is not None:
        allowed_by_readiness = _READINESS_ALLOWED_DOWNSTREAM_USES[readiness_level]
        if downstream_use not in allowed_by_readiness:
            raise ValueError(f"{readiness_level} does not allow {downstream_use}")

    if "conflict_open" in states:
        if downstream_use not in _BLOCKED_ONLY_DOWNSTREAM_USES:
            raise ValueError("conflict_open evidence requires blocked downstream use")
    if "blocked" in states:
        if downstream_use not in _BLOCKED_ONLY_DOWNSTREAM_USES:
            raise ValueError("blocked evidence state requires blocked downstream use")
    if {"candidate_only", "review_required"} & states:
        if downstream_use not in _REVIEW_CEILING_DOWNSTREAM_USES:
            raise ValueError("candidate_only or review_required evidence limits downstream use")


def _validate_transmission_path(hypothesis: dict[str, Any]) -> None:
    if hypothesis["hypothesis_type"] != "macro_factor":
        return

    downstream_use = hypothesis["allowed_downstream_use"]
    path_value = hypothesis.get("transmission_path") or hypothesis.get("transmission_path_summary")
    if path_value is None:
        if downstream_use in _BLOCKED_ONLY_DOWNSTREAM_USES:
            return
        raise ValueError("macro_factor hypothesis requires transmission_path or transmission_path_summary")

    if isinstance(path_value, list):
        path_text = " -> ".join(_require_string_list(path_value, "hypothesis.transmission_path"))
    else:
        path_text = _require_non_empty_string(path_value, "hypothesis.transmission_path")

    normalised = _normalise_marker(path_text)
    if path_text.count("->") < 2 or (
        "industry" not in normalised and "business" not in normalised
    ) or "artifact" not in normalised:
        raise ValueError(
            "macro_factor transmission path must link macro factor -> "
            "industry/business mechanism -> company artifact-state linkage"
        )


def _validate_optional_hypothesis_fields(hypothesis: dict[str, Any]) -> None:
    for field in HYPOTHESIS_OPTIONAL_FIELDS:
        if field not in hypothesis:
            continue
        value = hypothesis[field]
        if isinstance(value, list):
            _require_string_list(value, f"hypothesis.{field}", allow_empty=False)
        else:
            _require_non_empty_string(value, f"hypothesis.{field}")


def validate_bounded_hypothesis_item(
    payload: dict[str, Any],
    *,
    stock_code: str | None = None,
    source_readiness_level: str | None = None,
    identity_resolution_status: str | None = None,
    deterministic_evidence_inventory: dict[str, Any] | None = None,
    readiness_skeleton: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate one bounded hypothesis item and return a defensive copy."""

    hypothesis = deepcopy(_require_dict(payload, "hypothesis"))
    _validate_schema_keys(
        hypothesis,
        HYPOTHESIS_REQUIRED_FIELDS,
        HYPOTHESIS_OPTIONAL_FIELDS,
        "hypothesis",
    )

    _require_non_empty_string(hypothesis["hypothesis_id"], "hypothesis.hypothesis_id")
    _require_enum(hypothesis["hypothesis_type"], HYPOTHESIS_TYPES, "hypothesis.hypothesis_type")
    _require_non_empty_string(hypothesis["hypothesis_text"], "hypothesis.hypothesis_text")
    evidence_refs = _require_string_list(
        hypothesis["evidence_refs"],
        "hypothesis.evidence_refs",
        allow_empty=False,
    )
    evidence_state_refs = _require_string_list(
        hypothesis["evidence_state_refs"],
        "hypothesis.evidence_state_refs",
        allow_empty=False,
    )
    _require_enum(hypothesis["confidence"], CONFIDENCE_LEVELS, "hypothesis.confidence")
    hypothesis["caveats"] = _require_string_list(hypothesis["caveats"], "hypothesis.caveats")
    hypothesis["required_follow_up_data"] = _require_string_list(
        hypothesis["required_follow_up_data"],
        "hypothesis.required_follow_up_data",
    )
    downstream_use = _validate_downstream_use(
        hypothesis["allowed_downstream_use"],
        "hypothesis.allowed_downstream_use",
    )
    _require_bool_true(hypothesis["not_for_trading_advice"], "hypothesis.not_for_trading_advice")
    _validate_optional_hypothesis_fields(hypothesis)

    if stock_code is not None:
        _require_stock_code(stock_code, "stock_code")
        _reject_cross_ticker_refs(evidence_refs, stock_code, "hypothesis.evidence_refs")
        _reject_cross_ticker_refs(evidence_state_refs, stock_code, "hypothesis.evidence_state_refs")

    if readiness_skeleton is not None:
        readiness = validate_readiness_skeleton(readiness_skeleton)
        source_readiness_level = readiness["readiness_level"]
        identity_resolution_status = readiness["identity_resolution_status"]
    if deterministic_evidence_inventory is not None:
        evidence_inventory = validate_deterministic_evidence_inventory(deterministic_evidence_inventory)
    else:
        evidence_inventory = None

    if source_readiness_level is not None:
        _require_enum(source_readiness_level, READINESS_LEVELS, "source_readiness_level")
    if identity_resolution_status is not None:
        _require_enum(
            identity_resolution_status,
            IDENTITY_RESOLUTION_STATUSES,
            "identity_resolution_status",
        )

    rows = _rows_by_artifact_id(evidence_inventory, readiness_skeleton)
    if evidence_inventory is not None:
        inventory_rows = _rows_by_artifact_id(evidence_inventory)
        _validate_artifact_refs_exist(evidence_refs, inventory_rows, "hypothesis.evidence_refs")
        _validate_artifact_refs_exist(
            evidence_state_refs,
            inventory_rows,
            "hypothesis.evidence_state_refs",
        )
    states = _referenced_evidence_states(evidence_refs + evidence_state_refs, rows)
    _validate_readiness_ceiling(
        downstream_use=downstream_use,
        readiness_level=source_readiness_level,
        identity_resolution_status=identity_resolution_status,
        states=states,
    )
    _validate_transmission_path(hypothesis)
    _validate_payload_safety(hypothesis)
    return hypothesis


def validate_blocked_hypothesis_item(
    payload: dict[str, Any],
    *,
    stock_code: str | None = None,
) -> dict[str, Any]:
    """Validate one blocked hypothesis item and return a defensive copy."""

    hypothesis = deepcopy(_require_dict(payload, "blocked_hypothesis"))
    _validate_schema_keys(
        hypothesis,
        BLOCKED_HYPOTHESIS_REQUIRED_FIELDS,
        BLOCKED_HYPOTHESIS_OPTIONAL_FIELDS,
        "blocked_hypothesis",
    )

    _require_non_empty_string(hypothesis["hypothesis_id"], "blocked_hypothesis.hypothesis_id")
    _require_enum(hypothesis["hypothesis_type"], HYPOTHESIS_TYPES, "blocked_hypothesis.hypothesis_type")
    _require_non_empty_string(hypothesis["hypothesis_text"], "blocked_hypothesis.hypothesis_text")
    _require_enum(hypothesis["block_reason"], BLOCK_REASONS, "blocked_hypothesis.block_reason")
    evidence_state_refs = _require_string_list(
        hypothesis["evidence_state_refs"],
        "blocked_hypothesis.evidence_state_refs",
        allow_empty=False,
    )
    hypothesis["required_follow_up_data"] = _require_string_list(
        hypothesis["required_follow_up_data"],
        "blocked_hypothesis.required_follow_up_data",
    )
    hypothesis["caveats"] = _require_string_list(hypothesis["caveats"], "blocked_hypothesis.caveats")
    _require_bool_true(
        hypothesis["not_for_trading_advice"],
        "blocked_hypothesis.not_for_trading_advice",
    )

    if "evidence_refs" in hypothesis:
        hypothesis["evidence_refs"] = _require_string_list(
            hypothesis["evidence_refs"],
            "blocked_hypothesis.evidence_refs",
        )
    if "confidence" in hypothesis:
        _require_enum(hypothesis["confidence"], CONFIDENCE_LEVELS, "blocked_hypothesis.confidence")
    for field in ("transmission_path", "transmission_path_summary"):
        if field in hypothesis:
            _require_non_empty_string(hypothesis[field], f"blocked_hypothesis.{field}")

    if stock_code is not None:
        _require_stock_code(stock_code, "stock_code")
        _reject_cross_ticker_refs(evidence_state_refs, stock_code, "blocked_hypothesis.evidence_state_refs")
        if "evidence_refs" in hypothesis:
            _reject_cross_ticker_refs(hypothesis["evidence_refs"], stock_code, "blocked_hypothesis.evidence_refs")

    if not any(
        any(marker in _normalise_marker(ref) for marker in _BLOCKING_STATE_MARKERS)
        for ref in evidence_state_refs
    ):
        raise ValueError("blocked_hypothesis.evidence_state_refs must reference a blocking state")

    _validate_payload_safety(hypothesis)
    return hypothesis


def validate_bounded_hypothesis_request(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate a Phase 4 v1 request and return a defensive copy."""

    request = deepcopy(_require_dict(payload, "bounded_hypothesis_request"))
    for field in REQUEST_FORBIDDEN_CONTEXT_FIELDS:
        if field in request:
            raise ValueError(f"Phase 4 v1 does not accept {field}")

    missing = [
        field
        for field in (
            "schema_version",
            "deterministic_evidence_inventory",
            "readiness_skeleton",
            "not_for_trading_advice",
        )
        if field not in request
    ]
    if missing:
        raise ValueError(f"bounded_hypothesis_request missing required fields: {missing}")
    extra = set(request) - set(REQUEST_ALLOWED_FIELDS)
    if extra:
        raise ValueError(f"bounded_hypothesis_request has unsupported fields: {sorted(extra)}")

    schema_version = _require_non_empty_string(request["schema_version"], "schema_version")
    if schema_version != BOUNDED_HYPOTHESIS_REQUEST_SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {BOUNDED_HYPOTHESIS_REQUEST_SCHEMA_VERSION}")
    _require_bool_true(request["not_for_trading_advice"], "not_for_trading_advice")

    evidence_inventory, skeleton = _validate_phase3_pair(
        request["deterministic_evidence_inventory"],
        request["readiness_skeleton"],
    )
    if "stock_code" in request:
        _resolve_stock_code(request["stock_code"], evidence_inventory, skeleton)
    if "company_name" in request:
        _resolve_company_name(request["company_name"], evidence_inventory, skeleton)

    request["deterministic_evidence_inventory"] = evidence_inventory
    request["readiness_skeleton"] = skeleton
    _validate_payload_safety(request)
    return request


def build_bounded_hypothesis_payload(
    *,
    request: dict[str, Any] | None = None,
    deterministic_evidence_inventory: dict[str, Any] | None = None,
    readiness_skeleton: dict[str, Any] | None = None,
    stock_code: str | None = None,
    company_name: str | None = None,
    industry_hypotheses: list[dict[str, Any]] | None = None,
    supply_chain_position_hypotheses: list[dict[str, Any]] | None = None,
    business_model_hypotheses: list[dict[str, Any]] | None = None,
    macro_factor_hypotheses: list[dict[str, Any]] | None = None,
    key_research_questions: list[str] | None = None,
    required_follow_up_data: list[str] | None = None,
    blocked_hypotheses: list[dict[str, Any]] | None = None,
    caveats: list[str] | None = None,
    lineage_refs: list[str] | None = None,
    not_for_trading_advice: bool = True,
) -> dict[str, Any]:
    """Assemble a deterministic Phase 4 payload from already supplied items."""

    _require_bool_true(not_for_trading_advice, "not_for_trading_advice")
    if request is not None:
        validated_request = validate_bounded_hypothesis_request(request)
        deterministic_evidence_inventory = validated_request["deterministic_evidence_inventory"]
        readiness_skeleton = validated_request["readiness_skeleton"]
        stock_code = validated_request.get("stock_code", stock_code)
        company_name = validated_request.get("company_name", company_name)

    if deterministic_evidence_inventory is None or readiness_skeleton is None:
        raise ValueError("deterministic_evidence_inventory and readiness_skeleton are required")

    evidence_inventory, skeleton = _validate_phase3_pair(
        deterministic_evidence_inventory,
        readiness_skeleton,
    )
    resolved_stock_code = _resolve_stock_code(stock_code, evidence_inventory, skeleton)
    resolved_company_name = _resolve_company_name(company_name, evidence_inventory, skeleton)

    payload = {
        "schema_version": BOUNDED_HYPOTHESIS_PAYLOAD_SCHEMA_VERSION,
        "stock_code": resolved_stock_code,
        "company_name": resolved_company_name,
        "source_readiness_level": skeleton["readiness_level"],
        "industry_hypotheses": list(industry_hypotheses or []),
        "supply_chain_position_hypotheses": list(supply_chain_position_hypotheses or []),
        "business_model_hypotheses": list(business_model_hypotheses or []),
        "macro_factor_hypotheses": list(macro_factor_hypotheses or []),
        "key_research_questions": list(key_research_questions or []),
        "required_follow_up_data": list(required_follow_up_data or []),
        "blocked_hypotheses": list(blocked_hypotheses or []),
        "caveats": list(caveats or []),
        "lineage_refs": list(lineage_refs or skeleton["lineage_refs"]) + [
            BOUNDED_HYPOTHESIS_PAYLOAD_SCHEMA_VERSION
        ],
        "not_for_trading_advice": True,
    }
    return validate_bounded_hypothesis_payload(
        payload,
        deterministic_evidence_inventory=evidence_inventory,
        readiness_skeleton=skeleton,
    )


def validate_bounded_hypothesis_payload(
    payload: dict[str, Any],
    *,
    deterministic_evidence_inventory: dict[str, Any] | None = None,
    readiness_skeleton: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate a Phase 4 bounded hypothesis payload and return a copy."""

    bounded_payload = deepcopy(_require_dict(payload, "bounded_hypothesis_payload"))
    _validate_schema_keys(bounded_payload, PAYLOAD_REQUIRED_FIELDS, (), "bounded_hypothesis_payload")

    schema_version = _require_non_empty_string(bounded_payload["schema_version"], "schema_version")
    if schema_version != BOUNDED_HYPOTHESIS_PAYLOAD_SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {BOUNDED_HYPOTHESIS_PAYLOAD_SCHEMA_VERSION}")
    stock_code = _require_stock_code(bounded_payload["stock_code"], "stock_code")
    _require_non_empty_string(bounded_payload["company_name"], "company_name")
    source_readiness_level = _require_enum(
        bounded_payload["source_readiness_level"],
        READINESS_LEVELS,
        "source_readiness_level",
    )
    _require_bool_true(bounded_payload["not_for_trading_advice"], "not_for_trading_advice")

    evidence_inventory = None
    skeleton = None
    identity_resolution_status = None
    if deterministic_evidence_inventory is not None and readiness_skeleton is not None:
        evidence_inventory, skeleton = _validate_phase3_pair(
            deterministic_evidence_inventory,
            readiness_skeleton,
        )
        if bounded_payload["source_readiness_level"] != skeleton["readiness_level"]:
            raise ValueError("source_readiness_level must equal readiness_skeleton.v1.readiness_level")
        if bounded_payload["stock_code"] != skeleton["stock_code"]:
            raise ValueError("payload stock_code must match readiness_skeleton stock_code")
        identity_resolution_status = skeleton["identity_resolution_status"]
    elif readiness_skeleton is not None:
        skeleton = validate_readiness_skeleton(readiness_skeleton)
        if bounded_payload["source_readiness_level"] != skeleton["readiness_level"]:
            raise ValueError("source_readiness_level must equal readiness_skeleton.v1.readiness_level")
        identity_resolution_status = skeleton["identity_resolution_status"]
    elif deterministic_evidence_inventory is not None:
        evidence_inventory = validate_deterministic_evidence_inventory(deterministic_evidence_inventory)

    for field in HYPOTHESIS_LIST_FIELDS:
        bounded_payload[field] = _require_list(bounded_payload[field], field)
        allowed_types = _HYPOTHESIS_TYPE_BY_LIST_FIELD[field]
        validated_items = []
        for index, item in enumerate(bounded_payload[field]):
            try:
                validated = validate_bounded_hypothesis_item(
                    item,
                    stock_code=stock_code,
                    source_readiness_level=source_readiness_level,
                    identity_resolution_status=identity_resolution_status,
                    deterministic_evidence_inventory=evidence_inventory,
                    readiness_skeleton=skeleton,
                )
            except ValueError as exc:
                raise ValueError(f"{field}[{index}] invalid: {exc}") from exc
            if validated["hypothesis_type"] not in allowed_types:
                raise ValueError(f"{field}[{index}] has incompatible hypothesis_type")
            validated_items.append(validated)
        bounded_payload[field] = validated_items

    bounded_payload["key_research_questions"] = _require_string_list(
        bounded_payload["key_research_questions"],
        "key_research_questions",
    )
    bounded_payload["required_follow_up_data"] = _require_string_list(
        bounded_payload["required_follow_up_data"],
        "required_follow_up_data",
    )
    bounded_payload["caveats"] = _require_string_list(bounded_payload["caveats"], "caveats")
    bounded_payload["lineage_refs"] = _require_string_list(
        bounded_payload["lineage_refs"],
        "lineage_refs",
        allow_empty=False,
    )

    bounded_payload["blocked_hypotheses"] = _require_list(
        bounded_payload["blocked_hypotheses"],
        "blocked_hypotheses",
    )
    blocked_items = []
    for index, item in enumerate(bounded_payload["blocked_hypotheses"]):
        try:
            blocked_items.append(validate_blocked_hypothesis_item(item, stock_code=stock_code))
        except ValueError as exc:
            raise ValueError(f"blocked_hypotheses[{index}] invalid: {exc}") from exc
    bounded_payload["blocked_hypotheses"] = blocked_items

    _validate_payload_safety(bounded_payload)
    return bounded_payload


__all__ = [
    "ALLOWED_DOWNSTREAM_USES",
    "BLOCK_REASONS",
    "BOUNDED_HYPOTHESIS_PAYLOAD_SCHEMA_VERSION",
    "BOUNDED_HYPOTHESIS_REQUEST_SCHEMA_VERSION",
    "CONFIDENCE_LEVELS",
    "HYPOTHESIS_TYPES",
    "build_bounded_hypothesis_payload",
    "validate_blocked_hypothesis_item",
    "validate_bounded_hypothesis_item",
    "validate_bounded_hypothesis_payload",
    "validate_bounded_hypothesis_request",
]
