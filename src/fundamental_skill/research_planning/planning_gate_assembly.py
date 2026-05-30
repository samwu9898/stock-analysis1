# -*- coding: utf-8 -*-
"""Phase 5 controlled planning gate assembly.

This module is intentionally pure and side-effect free. It assembles already
supplied, validated Phase 2C, Phase 3, and Phase 4 planning payloads into one
internal planning boundary state. It does not read files, scan directories,
call providers, parse artifacts, render dashboards, or generate reports.
"""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

from . import bounded_hypothesis_generator as phase4
from . import evidence_readiness as phase3
from . import local_artifact_index as phase2c
from .autonomous_ticker_research_schema import (
    IDENTITY_RESOLUTION_STATUSES,
    READINESS_LEVELS,
)
from .safety import validate_payload_safety


AUTONOMOUS_TICKER_RESEARCH_PLANNING_RESULT_SCHEMA_VERSION = (
    "autonomous_ticker_research_planning_result.v1"
)

READINESS_FLAGS_PLANNING_ONLY_CAVEAT = (
    "readiness flags are planning indicators only; they are not Report V1 "
    "generation permissions and do not authorize report content creation."
)

DATA_GAP_PLAN_ITEM_REQUIRED_FIELDS = (
    "gap_id",
    "gap_type",
    "description",
    "source_phase",
    "source_ref",
    "priority",
    "required_follow_up_data",
    "caveats",
    "not_for_trading_advice",
)

DATA_GAP_TYPES = (
    "missing_phase2c_inventory",
    "missing_phase3_readiness",
    "missing_phase4_hypothesis_payload",
    "missing_required_evidence",
    "candidate_only_evidence",
    "review_required_evidence",
    "evidence_conflict",
    "identity_conflict",
    "readiness_blocked",
    "hypothesis_blocked",
    "downstream_use_blocked",
    "forbidden_marker",
    "not_for_trading_advice_violation",
    "other",
)

DATA_GAP_SOURCE_PHASES = ("phase2c", "phase3", "phase4", "phase5_assembly")
DATA_GAP_PRIORITIES = ("high", "medium", "low")

BLOCKED_REASON_ITEM_REQUIRED_FIELDS = (
    "reason_id",
    "reason_type",
    "source_phase",
    "source_ref",
    "blocking_state",
    "description",
    "caveats",
    "not_for_trading_advice",
)

BLOCKED_REASON_TYPES = (
    "missing_upstream_payload",
    "stock_code_mismatch",
    "company_name_conflict",
    "invalid_readiness_flags",
    "source_readiness_mismatch",
    "forbidden_marker",
    "not_for_trading_advice_violation",
    "blocked_readiness",
    "evidence_conflict_readiness",
    "all_artifacts_ignored",
    "no_hypotheses_allowed_downstream",
    "payload_validation_failed",
    "other",
)

PLANNING_RESULT_REQUIRED_FIELDS = (
    "schema_version",
    "stock_code",
    "company_name",
    "identity_resolution_status",
    "artifact_inventory_summary",
    "deterministic_evidence_inventory_ref",
    "readiness_skeleton_ref",
    "bounded_hypothesis_payload_ref",
    "readiness_level",
    "can_generate_accepted_report",
    "can_generate_experimental_report",
    "data_gap_plan",
    "blocked_reasons",
    "caveats",
    "lineage_refs",
    "not_for_trading_advice",
)

ARTIFACT_INVENTORY_SUMMARY_FIELDS = (
    "total_artifacts",
    "available_artifacts",
    "missing_artifacts",
    "candidate_only_artifacts",
    "review_required_artifacts",
    "conflict_artifacts",
    "ignored_artifacts",
)

LINEAGE_REF_FIELDS = ("schema_version", "stock_code", "lineage_ref")

_PROHIBITED_OUTPUT_KEYS = (
    "report_sections",
    "report_section",
    "research_report",
    "professional_research_report",
    "investment_conclusion",
    "investment_recommendation",
    "recommendation",
    "trading_advice",
    "target_price",
    "price_target",
    "position_size",
    "portfolio_weight",
    "technical_signal",
    "trading_signal",
    "verified_facts",
    "verified_fact",
    "accepted_report_facts",
    "accepted_report_fact",
    "report_facts",
    "report_fact",
    "provider_payload",
    "raw_manifest",
    "output_scan",
    "artifact_content",
    "dashboard_payload",
    "template_payload",
    "hypothesis_text",
    "report_conclusion",
)

_FORBIDDEN_TEXT_MARKERS = (
    "hypothesis_text",
    "investment_conclusion",
    "investment_recommendation",
    "investment_advice",
    "trading_advice",
    "target_price",
    "price_target",
    "portfolio_weight",
    "portfolio_allocation",
    "position_size",
    "technical_signal",
    "trading_signal",
    "buy_recommendation",
    "sell_recommendation",
    "buy_signal",
    "sell_signal",
    "buy_sell",
    "report_section",
    "report_conclusion",
    "dashboard_payload",
    "template_payload",
    "provider_payload",
    "accepted_manifest",
    "output_scan",
    "verified_fact",
    "accepted_report_fact",
    "report_fact",
)

_TRADING_PHRASE_PATTERNS = (
    re.compile(r"\b(buy|sell)\s+(this\s+)?(stock|share|security)\b", re.IGNORECASE),
    re.compile(r"\b(recommend|recommendation|rating)\s+(buy|sell)\b", re.IGNORECASE),
    re.compile(r"\b(buy|sell)\s+(recommendation|rating|signal)\b", re.IGNORECASE),
    re.compile(r"\btarget\s+price\b", re.IGNORECASE),
    re.compile(r"\bprice\s+target\b", re.IGNORECASE),
    re.compile(r"\bportfolio\s+(weight|allocation|position)\b", re.IGNORECASE),
    re.compile(r"\btechnical\s+(signal|indicator|analysis)\b", re.IGNORECASE),
    re.compile(r"\btrading\s+signal\b", re.IGNORECASE),
)

_TRADING_CN_PHRASES = (
    "\u4e70\u5165",
    "\u5356\u51fa",
    "\u76ee\u6807\u4ef7",
    "\u4ed3\u4f4d",
    "\u7ec4\u5408\u6743\u91cd",
    "\u6280\u672f\u4fe1\u53f7",
    "\u4ea4\u6613\u4fe1\u53f7",
    "\u6295\u8d44\u5efa\u8bae",
)


def _normalise_marker(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


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
    prohibited = {_normalise_marker(key) for key in _PROHIBITED_OUTPUT_KEYS}
    for path, text, is_key in _iter_keys_and_strings(payload):
        if is_key and _normalise_marker(text) in prohibited:
            raise ValueError(f"{path} is a prohibited report, dashboard, provider, hypothesis, or trading key")


def _reject_forbidden_markers(payload: Any) -> None:
    markers = tuple(_normalise_marker(marker) for marker in _FORBIDDEN_TEXT_MARKERS)
    for path, text, is_key in _iter_keys_and_strings(payload):
        normalised = _normalise_marker(text)
        if is_key and normalised == "not_for_trading_advice":
            continue
        for marker in markers:
            if marker and marker in normalised:
                raise ValueError(f"{path} contains forbidden planning marker: {marker}")
        if not is_key:
            if any(pattern.search(text) for pattern in _TRADING_PHRASE_PATTERNS):
                raise ValueError(f"{path} contains trading advice or recommendation language")
            if any(phrase in text for phrase in _TRADING_CN_PHRASES):
                raise ValueError(f"{path} contains trading advice or recommendation language")


def _validate_payload_boundary_safety(payload: Any) -> None:
    _reject_prohibited_keys(payload)
    _reject_forbidden_markers(payload)
    validate_payload_safety(payload)


def _enforce_not_for_trading_advice_true(payload: Any) -> None:
    def visit(child: Any, path: str) -> None:
        if isinstance(child, dict):
            if "not_for_trading_advice" in child and child["not_for_trading_advice"] is not True:
                raise ValueError(f"{path or '<root>'}.not_for_trading_advice must be true")
            for key, nested in child.items():
                child_path = f"{path}.{key}" if path else str(key)
                visit(nested, child_path)
            return
        if isinstance(child, list):
            for index, nested in enumerate(child):
                visit(nested, f"{path}[{index}]")

    visit(payload, "")


def _require_dict(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be a dict")
    return value


def _require_string(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    return value


def _require_non_empty_string(value: Any, field: str) -> str:
    text = _require_string(value, field)
    if not text.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return text


def _require_stock_code(value: Any, field: str) -> str:
    stock_code = _require_non_empty_string(value, field)
    if not re.fullmatch(r"\d{6}", stock_code):
        raise ValueError(f"{field} must be a six-digit stock code")
    return stock_code


def _require_bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be a bool")
    return value


def _require_true(value: Any, field: str) -> None:
    if value is not True:
        raise ValueError(f"{field} must be true")


def _require_enum(value: Any, allowed: tuple[str, ...], field: str) -> str:
    text = _require_non_empty_string(value, field)
    if text not in allowed:
        raise ValueError(f"{field} must be one of {sorted(allowed)}")
    return text


def _require_string_list(value: Any, field: str, *, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    if not allow_empty and not value:
        raise ValueError(f"{field} must not be empty")
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field}[{index}] must be a non-empty string")
        result.append(item)
    return result


def _validate_schema_keys(payload: dict[str, Any], required: tuple[str, ...], field: str) -> None:
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f"{field} missing required fields: {missing}")
    extra = set(payload) - set(required)
    if extra:
        raise ValueError(f"{field} has unsupported fields: {sorted(extra)}")


def _dedupe_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def validate_data_gap_plan_item(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate one Phase 5 data-gap plan item and return a defensive copy."""

    item = deepcopy(_require_dict(payload, "data_gap_plan item"))
    _validate_schema_keys(item, DATA_GAP_PLAN_ITEM_REQUIRED_FIELDS, "data_gap_plan item")

    _require_non_empty_string(item["gap_id"], "data_gap_plan.gap_id")
    _require_enum(item["gap_type"], DATA_GAP_TYPES, "data_gap_plan.gap_type")
    _require_non_empty_string(item["description"], "data_gap_plan.description")
    _require_enum(item["source_phase"], DATA_GAP_SOURCE_PHASES, "data_gap_plan.source_phase")
    _require_non_empty_string(item["source_ref"], "data_gap_plan.source_ref")
    _require_enum(item["priority"], DATA_GAP_PRIORITIES, "data_gap_plan.priority")
    item["required_follow_up_data"] = _require_string_list(
        item["required_follow_up_data"],
        "data_gap_plan.required_follow_up_data",
        allow_empty=False,
    )
    item["caveats"] = _require_string_list(item["caveats"], "data_gap_plan.caveats")
    _require_true(item["not_for_trading_advice"], "data_gap_plan.not_for_trading_advice")

    _validate_payload_boundary_safety(item)
    return item


def validate_blocked_reason_item(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate one Phase 5 blocked-reason item and return a defensive copy."""

    item = deepcopy(_require_dict(payload, "blocked_reasons item"))
    _validate_schema_keys(item, BLOCKED_REASON_ITEM_REQUIRED_FIELDS, "blocked_reasons item")

    _require_non_empty_string(item["reason_id"], "blocked_reasons.reason_id")
    _require_enum(item["reason_type"], BLOCKED_REASON_TYPES, "blocked_reasons.reason_type")
    _require_enum(item["source_phase"], DATA_GAP_SOURCE_PHASES, "blocked_reasons.source_phase")
    _require_non_empty_string(item["source_ref"], "blocked_reasons.source_ref")
    _require_non_empty_string(item["blocking_state"], "blocked_reasons.blocking_state")
    _require_non_empty_string(item["description"], "blocked_reasons.description")
    item["caveats"] = _require_string_list(item["caveats"], "blocked_reasons.caveats")
    _require_true(item["not_for_trading_advice"], "blocked_reasons.not_for_trading_advice")

    _validate_payload_boundary_safety(item)
    return item


def _validate_required_upstream(name: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    if payload is None:
        raise ValueError(f"missing required upstream payload: {name}")
    return _require_dict(payload, name)


def _validate_upstream_payloads(
    *,
    ticker_local_artifact_inventory: dict[str, Any] | None,
    deterministic_evidence_inventory: dict[str, Any] | None,
    readiness_skeleton: dict[str, Any] | None,
    bounded_hypothesis_payload: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    ticker_inventory = phase2c.validate_ticker_local_artifact_inventory(
        _validate_required_upstream(
            phase2c.TICKER_LOCAL_ARTIFACT_INVENTORY_SCHEMA_VERSION,
            ticker_local_artifact_inventory,
        )
    )
    evidence_inventory = phase3.validate_deterministic_evidence_inventory(
        _validate_required_upstream(
            phase3.DETERMINISTIC_EVIDENCE_INVENTORY_SCHEMA_VERSION,
            deterministic_evidence_inventory,
        )
    )
    skeleton = phase3.validate_readiness_skeleton(
        _validate_required_upstream(phase3.READINESS_SKELETON_SCHEMA_VERSION, readiness_skeleton)
    )
    bounded_payload = phase4.validate_bounded_hypothesis_payload(
        _validate_required_upstream(
            phase4.BOUNDED_HYPOTHESIS_PAYLOAD_SCHEMA_VERSION,
            bounded_hypothesis_payload,
        ),
        deterministic_evidence_inventory=evidence_inventory,
        readiness_skeleton=skeleton,
    )
    return ticker_inventory, evidence_inventory, skeleton, bounded_payload


def _validate_stock_code_consistency(
    *,
    stock_code: str | None,
    ticker_inventory: dict[str, Any],
    evidence_inventory: dict[str, Any],
    skeleton: dict[str, Any],
    bounded_payload: dict[str, Any],
) -> str:
    upstream_codes = {
        ticker_inventory["stock_code"],
        evidence_inventory["stock_code"],
        skeleton["stock_code"],
        bounded_payload["stock_code"],
    }
    if len(upstream_codes) != 1:
        raise ValueError("stock_code mismatch across upstream payloads")
    resolved = next(iter(upstream_codes))
    if stock_code is not None and _require_stock_code(stock_code, "stock_code") != resolved:
        raise ValueError("stock_code hint must exactly match all upstream payloads")
    return resolved


def _validate_company_name_consistency(
    *,
    company_name: str | None,
    ticker_inventory: dict[str, Any],
    evidence_inventory: dict[str, Any],
    skeleton: dict[str, Any],
    bounded_payload: dict[str, Any],
) -> str:
    upstream_names = [
        ticker_inventory["company_name"],
        evidence_inventory["company_name"],
        skeleton["company_name"],
        bounded_payload["company_name"],
    ]
    for index, name in enumerate(upstream_names):
        _require_string(name, f"upstream company_name[{index}]")
    if len(set(upstream_names)) != 1:
        raise ValueError("company_name mismatch across upstream payloads")
    resolved = upstream_names[0]
    if company_name is not None and company_name != "":
        _require_string(company_name, "company_name")
        if company_name != resolved:
            raise ValueError("company_name hint must exactly match every upstream company_name")
    return resolved


def _validate_identity_consistency(
    ticker_inventory: dict[str, Any],
    evidence_inventory: dict[str, Any],
    skeleton: dict[str, Any],
) -> str:
    statuses = {
        ticker_inventory["identity_resolution_status"],
        evidence_inventory["identity_resolution_status"],
        skeleton["identity_resolution_status"],
    }
    if len(statuses) != 1:
        raise ValueError("identity_resolution_status mismatch across upstream payloads")
    return next(iter(statuses))


def _artifact_inventory_summary(evidence_inventory: dict[str, Any]) -> dict[str, int]:
    summary = {
        "total_artifacts": len(evidence_inventory["evidence_inventory"]),
        "available_artifacts": len(evidence_inventory["available_data_artifacts"]),
        "missing_artifacts": len(evidence_inventory["missing_data_artifacts"]),
        "candidate_only_artifacts": len(evidence_inventory["candidate_only_artifacts"]),
        "review_required_artifacts": len(evidence_inventory["review_required_artifacts"]),
        "conflict_artifacts": len(evidence_inventory["conflict_artifacts"]),
        "ignored_artifacts": len(evidence_inventory["ignored_artifacts"]),
    }
    return summary


def _lineage_ref(schema_version: str, stock_code: str) -> dict[str, str]:
    return {
        "schema_version": schema_version,
        "stock_code": stock_code,
        "lineage_ref": schema_version,
    }


def _new_gap(
    gaps: list[dict[str, Any]],
    *,
    gap_type: str,
    description: str,
    source_phase: str,
    source_ref: str,
    priority: str,
    required_follow_up_data: list[str],
    caveats: list[str] | None = None,
) -> None:
    item = {
        "gap_id": f"data_gap_{len(gaps) + 1:03d}",
        "gap_type": gap_type,
        "description": description,
        "source_phase": source_phase,
        "source_ref": source_ref,
        "priority": priority,
        "required_follow_up_data": list(required_follow_up_data),
        "caveats": list(caveats or []),
        "not_for_trading_advice": True,
    }
    gaps.append(validate_data_gap_plan_item(item))


def _new_blocked_reason(
    reasons: list[dict[str, Any]],
    *,
    reason_type: str,
    source_phase: str,
    source_ref: str,
    blocking_state: str,
    description: str,
    caveats: list[str] | None = None,
) -> None:
    item = {
        "reason_id": f"blocked_reason_{len(reasons) + 1:03d}",
        "reason_type": reason_type,
        "source_phase": source_phase,
        "source_ref": source_ref,
        "blocking_state": blocking_state,
        "description": description,
        "caveats": list(caveats or []),
        "not_for_trading_advice": True,
    }
    reasons.append(validate_blocked_reason_item(item))


def _build_data_gap_plan(
    evidence_inventory: dict[str, Any],
    skeleton: dict[str, Any],
    bounded_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []

    for index, row in enumerate(evidence_inventory["missing_data_artifacts"]):
        _new_gap(
            gaps,
            gap_type="missing_required_evidence",
            description="Missing artifact state requires data collection.",
            source_phase="phase3",
            source_ref=f"deterministic_evidence_inventory.v1.missing_data_artifacts[{index}]",
            priority="high",
            required_follow_up_data=[f"Collect or validate missing artifact state for {row['artifact_id']}."],
            caveats=row["caveats"],
        )
    for index, row in enumerate(evidence_inventory["candidate_only_artifacts"]):
        _new_gap(
            gaps,
            gap_type="candidate_only_evidence",
            description="Candidate-only artifact state requires follow-up validation.",
            source_phase="phase3",
            source_ref=f"deterministic_evidence_inventory.v1.candidate_only_artifacts[{index}]",
            priority="medium",
            required_follow_up_data=[f"Validate candidate-only artifact state for {row['artifact_id']}."],
            caveats=row["caveats"],
        )
    for index, row in enumerate(evidence_inventory["review_required_artifacts"]):
        _new_gap(
            gaps,
            gap_type="review_required_evidence",
            description="Artifact state requires review before downstream planning use.",
            source_phase="phase3",
            source_ref=f"deterministic_evidence_inventory.v1.review_required_artifacts[{index}]",
            priority="medium",
            required_follow_up_data=[f"Review artifact state for {row['artifact_id']}."],
            caveats=row["caveats"],
        )
    for index, row in enumerate(evidence_inventory["conflict_artifacts"]):
        _new_gap(
            gaps,
            gap_type="evidence_conflict",
            description="Conflicting artifact state requires resolution before accepted planning use.",
            source_phase="phase3",
            source_ref=f"deterministic_evidence_inventory.v1.conflict_artifacts[{index}]",
            priority="high",
            required_follow_up_data=[f"Resolve conflicting artifact state for {row['artifact_id']}."],
            caveats=row["caveats"],
        )

    if skeleton["fail_closed_reason"]:
        _new_gap(
            gaps,
            gap_type="readiness_blocked",
            description="Readiness state requires upstream follow-up before planning can advance.",
            source_phase="phase3",
            source_ref="readiness_skeleton.v1.fail_closed_reason",
            priority="high",
            required_follow_up_data=[skeleton["fail_closed_reason"]],
            caveats=[],
        )

    for index, follow_up in enumerate(bounded_payload["required_follow_up_data"]):
        _new_gap(
            gaps,
            gap_type="missing_required_evidence",
            description="Phase 4 requested follow-up data collection.",
            source_phase="phase4",
            source_ref=f"bounded_hypothesis_payload.v1.required_follow_up_data[{index}]",
            priority="medium",
            required_follow_up_data=[follow_up],
            caveats=[],
        )

    for item_index, blocked in enumerate(bounded_payload["blocked_hypotheses"]):
        for follow_index, follow_up in enumerate(blocked["required_follow_up_data"]):
            _new_gap(
                gaps,
                gap_type="hypothesis_blocked",
                description="Blocked upstream planning item requires follow-up data collection.",
                source_phase="phase4",
                source_ref=(
                    "bounded_hypothesis_payload.v1."
                    f"blocked_hypotheses[{item_index}].required_follow_up_data[{follow_index}]"
                ),
                priority="high",
                required_follow_up_data=[follow_up],
                caveats=blocked["caveats"],
            )

    return gaps


def _blocked_reason_type_from_block_reason(block_reason: str) -> str:
    mapping = {
        "unresolved_identity": "blocked_readiness",
        "blocked_readiness": "blocked_readiness",
        "evidence_conflict": "evidence_conflict_readiness",
        "missing_required_evidence": "blocked_readiness",
        "candidate_only_evidence": "blocked_readiness",
        "review_required_evidence": "blocked_readiness",
        "forbidden_marker": "forbidden_marker",
        "not_for_trading_advice_violation": "not_for_trading_advice_violation",
        "other": "other",
    }
    return mapping.get(block_reason, "other")


def _build_blocked_reasons(
    evidence_inventory: dict[str, Any],
    skeleton: dict[str, Any],
    bounded_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    reasons: list[dict[str, Any]] = []

    identity_status = skeleton["identity_resolution_status"]
    if identity_status != "resolved":
        reason_type = "company_name_conflict" if identity_status == "conflict_requires_review" else "blocked_readiness"
        _new_blocked_reason(
            reasons,
            reason_type=reason_type,
            source_phase="phase3",
            source_ref="readiness_skeleton.v1.identity_resolution_status",
            blocking_state=identity_status,
            description="Upstream identity state is not resolved.",
            caveats=[],
        )

    readiness_level = skeleton["readiness_level"]
    if readiness_level in {"blocked", "data_collection_required", "classification_review_required"}:
        _new_blocked_reason(
            reasons,
            reason_type="blocked_readiness",
            source_phase="phase3",
            source_ref="readiness_skeleton.v1.readiness_level",
            blocking_state=readiness_level,
            description="Upstream readiness state is not accepted planning ready.",
            caveats=[skeleton["fail_closed_reason"]] if skeleton["fail_closed_reason"] else [],
        )
    if readiness_level == "evidence_conflict_review_required":
        _new_blocked_reason(
            reasons,
            reason_type="evidence_conflict_readiness",
            source_phase="phase3",
            source_ref="readiness_skeleton.v1.readiness_level",
            blocking_state=readiness_level,
            description="Upstream readiness requires evidence conflict review.",
            caveats=[skeleton["fail_closed_reason"]] if skeleton["fail_closed_reason"] else [],
        )

    rows = evidence_inventory["evidence_inventory"]
    ignored = evidence_inventory["ignored_artifacts"]
    if rows and len(ignored) == len(rows):
        _new_blocked_reason(
            reasons,
            reason_type="all_artifacts_ignored",
            source_phase="phase3",
            source_ref="deterministic_evidence_inventory.v1.ignored_artifacts",
            blocking_state="all_artifacts_ignored",
            description="All upstream artifact states are ignored.",
            caveats=[],
        )

    for index, blocked in enumerate(bounded_payload["blocked_hypotheses"]):
        block_reason = blocked["block_reason"]
        _new_blocked_reason(
            reasons,
            reason_type=_blocked_reason_type_from_block_reason(block_reason),
            source_phase="phase4",
            source_ref=f"bounded_hypothesis_payload.v1.blocked_hypotheses[{index}].block_reason",
            blocking_state=block_reason,
            description=f"Upstream blocked planning item block_reason: {block_reason}.",
            caveats=blocked["caveats"],
        )

    return reasons


def _constrained_readiness_flags(
    skeleton: dict[str, Any],
    identity_status: str,
    evidence_inventory: dict[str, Any],
) -> tuple[bool, bool]:
    accepted = bool(skeleton["can_generate_accepted_report"])
    experimental = bool(skeleton["can_generate_experimental_report"])
    readiness_level = skeleton["readiness_level"]

    hard_conflict = (
        identity_status != "resolved"
        or bool(evidence_inventory["conflict_artifacts"])
        or readiness_level in {
            "blocked",
            "data_collection_required",
            "classification_review_required",
            "evidence_conflict_review_required",
        }
    )
    if hard_conflict:
        return False, False
    if readiness_level != "accepted_report_ready":
        accepted = False
    if readiness_level != "experimental_report_ready":
        experimental = False
    return accepted, experimental


def build_autonomous_ticker_research_planning_result(
    *,
    ticker_local_artifact_inventory: dict[str, Any] | None = None,
    deterministic_evidence_inventory: dict[str, Any] | None = None,
    readiness_skeleton: dict[str, Any] | None = None,
    bounded_hypothesis_payload: dict[str, Any] | None = None,
    stock_code: str | None = None,
    company_name: str | None = None,
    not_for_trading_advice: bool = True,
) -> dict[str, Any]:
    """Build the Phase 5 internal planning boundary state."""

    _require_true(not_for_trading_advice, "not_for_trading_advice")
    ticker_inventory, evidence_inventory, skeleton, bounded_payload = _validate_upstream_payloads(
        ticker_local_artifact_inventory=ticker_local_artifact_inventory,
        deterministic_evidence_inventory=deterministic_evidence_inventory,
        readiness_skeleton=readiness_skeleton,
        bounded_hypothesis_payload=bounded_hypothesis_payload,
    )

    resolved_stock_code = _validate_stock_code_consistency(
        stock_code=stock_code,
        ticker_inventory=ticker_inventory,
        evidence_inventory=evidence_inventory,
        skeleton=skeleton,
        bounded_payload=bounded_payload,
    )
    resolved_company_name = _validate_company_name_consistency(
        company_name=company_name,
        ticker_inventory=ticker_inventory,
        evidence_inventory=evidence_inventory,
        skeleton=skeleton,
        bounded_payload=bounded_payload,
    )
    identity_status = _validate_identity_consistency(ticker_inventory, evidence_inventory, skeleton)

    accepted, experimental = _constrained_readiness_flags(skeleton, identity_status, evidence_inventory)
    caveats = _dedupe_strings(
        list(evidence_inventory["caveats"])
        + list(skeleton["caveats"])
        + list(bounded_payload["caveats"])
        + [READINESS_FLAGS_PLANNING_ONLY_CAVEAT]
    )
    lineage_refs = _dedupe_strings(
        list(ticker_inventory["lineage_refs"])
        + list(evidence_inventory["lineage_refs"])
        + list(skeleton["lineage_refs"])
        + list(bounded_payload["lineage_refs"])
        + [AUTONOMOUS_TICKER_RESEARCH_PLANNING_RESULT_SCHEMA_VERSION]
    )

    result = {
        "schema_version": AUTONOMOUS_TICKER_RESEARCH_PLANNING_RESULT_SCHEMA_VERSION,
        "stock_code": resolved_stock_code,
        "company_name": resolved_company_name,
        "identity_resolution_status": identity_status,
        "artifact_inventory_summary": _artifact_inventory_summary(evidence_inventory),
        "deterministic_evidence_inventory_ref": _lineage_ref(
            phase3.DETERMINISTIC_EVIDENCE_INVENTORY_SCHEMA_VERSION,
            resolved_stock_code,
        ),
        "readiness_skeleton_ref": _lineage_ref(phase3.READINESS_SKELETON_SCHEMA_VERSION, resolved_stock_code),
        "bounded_hypothesis_payload_ref": _lineage_ref(
            phase4.BOUNDED_HYPOTHESIS_PAYLOAD_SCHEMA_VERSION,
            resolved_stock_code,
        ),
        "readiness_level": skeleton["readiness_level"],
        "can_generate_accepted_report": accepted,
        "can_generate_experimental_report": experimental,
        "data_gap_plan": _build_data_gap_plan(evidence_inventory, skeleton, bounded_payload),
        "blocked_reasons": _build_blocked_reasons(evidence_inventory, skeleton, bounded_payload),
        "caveats": caveats,
        "lineage_refs": lineage_refs,
        "not_for_trading_advice": True,
    }
    return validate_autonomous_ticker_research_planning_result(result)


def _validate_artifact_inventory_summary(value: Any) -> dict[str, int]:
    summary = deepcopy(_require_dict(value, "artifact_inventory_summary"))
    _validate_schema_keys(summary, ARTIFACT_INVENTORY_SUMMARY_FIELDS, "artifact_inventory_summary")
    for field in ARTIFACT_INVENTORY_SUMMARY_FIELDS:
        if not isinstance(summary[field], int) or summary[field] < 0:
            raise ValueError(f"artifact_inventory_summary.{field} must be a non-negative int")
    return summary


def _validate_lineage_ref(value: Any, field: str, expected_schema_version: str, stock_code: str) -> dict[str, str]:
    ref = deepcopy(_require_dict(value, field))
    _validate_schema_keys(ref, LINEAGE_REF_FIELDS, field)
    if ref["schema_version"] != expected_schema_version:
        raise ValueError(f"{field}.schema_version must be {expected_schema_version}")
    if ref["stock_code"] != stock_code:
        raise ValueError(f"{field}.stock_code must match result stock_code")
    if ref["lineage_ref"] != expected_schema_version:
        raise ValueError(f"{field}.lineage_ref must be {expected_schema_version}")
    return ref


def _validate_item_list(
    value: Any,
    field: str,
    validator: Any,
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    items: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        try:
            items.append(validator(item))
        except ValueError as exc:
            raise ValueError(f"{field}[{index}] invalid: {exc}") from exc
    return items


def validate_autonomous_ticker_research_planning_result(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate a Phase 5 planning result and return a defensive copy."""

    result = deepcopy(_require_dict(payload, "autonomous_ticker_research_planning_result"))
    _validate_schema_keys(result, PLANNING_RESULT_REQUIRED_FIELDS, "autonomous_ticker_research_planning_result")

    if result["schema_version"] != AUTONOMOUS_TICKER_RESEARCH_PLANNING_RESULT_SCHEMA_VERSION:
        raise ValueError(
            "schema_version must be "
            f"{AUTONOMOUS_TICKER_RESEARCH_PLANNING_RESULT_SCHEMA_VERSION}"
        )
    stock_code = _require_stock_code(result["stock_code"], "stock_code")
    _require_string(result["company_name"], "company_name")
    _require_enum(
        result["identity_resolution_status"],
        IDENTITY_RESOLUTION_STATUSES,
        "identity_resolution_status",
    )
    result["artifact_inventory_summary"] = _validate_artifact_inventory_summary(
        result["artifact_inventory_summary"]
    )
    result["deterministic_evidence_inventory_ref"] = _validate_lineage_ref(
        result["deterministic_evidence_inventory_ref"],
        "deterministic_evidence_inventory_ref",
        phase3.DETERMINISTIC_EVIDENCE_INVENTORY_SCHEMA_VERSION,
        stock_code,
    )
    result["readiness_skeleton_ref"] = _validate_lineage_ref(
        result["readiness_skeleton_ref"],
        "readiness_skeleton_ref",
        phase3.READINESS_SKELETON_SCHEMA_VERSION,
        stock_code,
    )
    result["bounded_hypothesis_payload_ref"] = _validate_lineage_ref(
        result["bounded_hypothesis_payload_ref"],
        "bounded_hypothesis_payload_ref",
        phase4.BOUNDED_HYPOTHESIS_PAYLOAD_SCHEMA_VERSION,
        stock_code,
    )
    readiness_level = _require_enum(result["readiness_level"], READINESS_LEVELS, "readiness_level")
    accepted = _require_bool(result["can_generate_accepted_report"], "can_generate_accepted_report")
    experimental = _require_bool(
        result["can_generate_experimental_report"],
        "can_generate_experimental_report",
    )
    if accepted and readiness_level != "accepted_report_ready":
        raise ValueError("can_generate_accepted_report requires accepted_report_ready readiness")
    if experimental and readiness_level != "experimental_report_ready":
        raise ValueError("can_generate_experimental_report requires experimental_report_ready readiness")
    if readiness_level in {
        "blocked",
        "data_collection_required",
        "classification_review_required",
        "evidence_conflict_review_required",
    } and (accepted or experimental):
        raise ValueError(f"{readiness_level} must fail closed for readiness flags")

    result["data_gap_plan"] = _validate_item_list(
        result["data_gap_plan"],
        "data_gap_plan",
        validate_data_gap_plan_item,
    )
    result["blocked_reasons"] = _validate_item_list(
        result["blocked_reasons"],
        "blocked_reasons",
        validate_blocked_reason_item,
    )
    result["caveats"] = _require_string_list(result["caveats"], "caveats")
    if READINESS_FLAGS_PLANNING_ONLY_CAVEAT not in result["caveats"]:
        raise ValueError("caveats must include readiness flags planning-only caveat")
    result["lineage_refs"] = _require_string_list(result["lineage_refs"], "lineage_refs", allow_empty=False)
    _require_true(result["not_for_trading_advice"], "not_for_trading_advice")

    _enforce_not_for_trading_advice_true(result)
    _validate_payload_boundary_safety(result)
    return result


__all__ = [
    "AUTONOMOUS_TICKER_RESEARCH_PLANNING_RESULT_SCHEMA_VERSION",
    "BLOCKED_REASON_ITEM_REQUIRED_FIELDS",
    "BLOCKED_REASON_TYPES",
    "DATA_GAP_PLAN_ITEM_REQUIRED_FIELDS",
    "DATA_GAP_PRIORITIES",
    "DATA_GAP_SOURCE_PHASES",
    "DATA_GAP_TYPES",
    "PLANNING_RESULT_REQUIRED_FIELDS",
    "READINESS_FLAGS_PLANNING_ONLY_CAVEAT",
    "build_autonomous_ticker_research_planning_result",
    "validate_autonomous_ticker_research_planning_result",
    "validate_blocked_reason_item",
    "validate_data_gap_plan_item",
]
