# -*- coding: utf-8 -*-
"""Deterministic evidence inventory and readiness skeleton primitives."""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any


DETERMINISTIC_EVIDENCE_INVENTORY_SCHEMA_VERSION = "deterministic_evidence_inventory.v1"
READINESS_SKELETON_SCHEMA_VERSION = "readiness_skeleton.v1"

OFFICIAL_BUSINESS_EVIDENCE_CATEGORY = "official_business_evidence_artifact_state"
CRITICAL_FINANCIAL_ARTIFACT_CATEGORY = "critical_financial_artifact_state"

REQUIRED_DETERMINISTIC_EVIDENCE_INVENTORY_FIELDS = (
    "schema_version",
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
    "caveats",
    "lineage_refs",
    "not_for_trading_advice",
)

REQUIRED_READINESS_SKELETON_FIELDS = (
    "schema_version",
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
    "readiness_level",
    "can_generate_accepted_report",
    "can_generate_experimental_report",
    "fail_closed_reason",
    "caveats",
    "lineage_refs",
    "not_for_trading_advice",
)

OFFICIAL_BUSINESS_ARTIFACT_TYPES = (
    "official_disclosure_facts_artifact",
    "official_disclosure_candidate_artifact",
)

OFFICIAL_BUSINESS_SOURCE_FAMILIES = ("official_disclosures",)

CRITICAL_FINANCIAL_ARTIFACT_TYPES = (
    "normalized_fundamentals_artifact",
    "provider_separated_fundamentals_artifact",
    "score_confidence_explainability_artifact",
    "report_artifact_state",
    "existing_local_report_artifact",
)

CRITICAL_FINANCIAL_SOURCE_FAMILIES = (
    "normalized_fundamentals",
    "provider_fundamentals",
    "score_confidence_explainability",
    "research_report_v1",
    "existing_local_reports",
)

BLOCKING_SOURCE_STATUSES = (
    "candidate_only",
    "review_required",
    "conflict_open",
    "invalidated",
    "missing",
    "unreadable",
    "ignored",
)

BLOCKING_REVIEW_STATUSES = (
    "review_required",
    "conflict_open",
    "rejected",
    "invalidated",
)

PROHIBITED_OUTPUT_KEYS = (
    "report_section",
    "recommendation",
    "target_price",
    "price_target",
    "trading_advice",
    "trading_signal",
    "technical_signal",
    "research_report_v1_section",
    "research_report_v1_integration_permission",
)

FORBIDDEN_TEXT_MARKERS = (
    "target_price",
    "price_target",
    "trading_signal",
    "technical_signal",
    "buy_advice",
    "sell_advice",
    "position_size",
    "position_sizing",
    "portfolio_weight",
    "portfolio_allocation",
    "report_section",
    "research_report_v1_section",
    "research_report_v1_section_payload",
    "hypothesis",
    "hypothesis_generator",
    "generate_hypothesis",
    "raw_real_manifest_dict",
    "raw_output_scan_result",
    "output_scan_result",
    "report_artifact_content",
    "parsed_report_section",
)


def _normalise_marker(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _identity_statuses() -> tuple[str, ...]:
    from .autonomous_ticker_research_schema import IDENTITY_RESOLUTION_STATUSES

    return IDENTITY_RESOLUTION_STATUSES


def _readiness_levels() -> tuple[str, ...]:
    from .autonomous_ticker_research_schema import READINESS_LEVELS

    return READINESS_LEVELS


def _validate_payload_safety(payload: Any) -> None:
    from .safety import validate_payload_safety

    validate_payload_safety(payload)


def _validate_ticker_inventory(inventory: dict[str, Any]) -> dict[str, Any]:
    from .local_artifact_index import validate_ticker_local_artifact_inventory

    return validate_ticker_local_artifact_inventory(inventory)


def _validate_artifact_row(row: dict[str, Any]) -> dict[str, Any]:
    from .local_artifact_index import validate_artifact_row

    return validate_artifact_row(row)


def _require_dict(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be a dict")
    return value


def _require_string(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    return value


def _require_stock_code(value: Any, field: str) -> str:
    stock_code = _require_string(value, field)
    if not re.fullmatch(r"\d{6}", stock_code):
        raise ValueError(f"{field} must be a six-digit stock code")
    return stock_code


def _require_bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be a bool")
    return value


def _require_enum(value: Any, allowed: tuple[str, ...], field: str) -> str:
    text = _require_string(value, field)
    if text not in allowed:
        raise ValueError(f"{field} must be one of {allowed}")
    return text


def _require_string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise ValueError(f"{field}[{index}] must be a string")
        result.append(item)
    return result


def _validate_artifact_row_list(value: Any, field: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(value):
        try:
            rows.append(_validate_artifact_row(row))
        except ValueError as exc:
            raise ValueError(f"{field}[{index}] is invalid: {exc}") from exc
    return rows


def _iter_keys_and_text(value: Any) -> list[str]:
    text: list[str] = []

    def visit(child: Any) -> None:
        if isinstance(child, dict):
            for key, nested in child.items():
                text.append(str(key))
                visit(nested)
            return
        if isinstance(child, list):
            for nested in child:
                visit(nested)
            return
        if isinstance(child, str):
            text.append(child)

    visit(value)
    return text


def _reject_forbidden_markers(payload: Any) -> None:
    forbidden = tuple(_normalise_marker(marker) for marker in FORBIDDEN_TEXT_MARKERS)
    for text in _iter_keys_and_text(payload):
        normalised = _normalise_marker(text)
        for marker in forbidden:
            if marker and marker in normalised:
                raise ValueError("readiness payload safety violation: forbidden downstream marker")


def _reject_prohibited_output_keys(payload: Any) -> None:
    prohibited = {_normalise_marker(key) for key in PROHIBITED_OUTPUT_KEYS}

    def visit(child: Any) -> None:
        if isinstance(child, dict):
            for key, nested in child.items():
                if _normalise_marker(str(key)) in prohibited:
                    raise ValueError("readiness payload contains prohibited report or trading key")
                visit(nested)
            return
        if isinstance(child, list):
            for nested in child:
                visit(nested)

    visit(payload)


def _mask_payload_for_safety(value: Any) -> Any:
    if isinstance(value, dict):
        masked: dict[str, Any] = {}
        for key, child in value.items():
            if key == "artifact_path":
                masked[key] = "<artifact_path>"
            elif key == "sha256" and child:
                masked[key] = "<sha256>"
            else:
                masked[key] = _mask_payload_for_safety(child)
        return masked
    if isinstance(value, list):
        return [_mask_payload_for_safety(child) for child in value]
    return value


def _is_conflict(row: dict[str, Any]) -> bool:
    return row["source_status"] == "conflict_open" or row["review_status"] == "conflict_open"


def _is_ignored(row: dict[str, Any]) -> bool:
    return row["source_status"] == "ignored" or row["artifact_type"] == "ignored"


def _is_missing(row: dict[str, Any]) -> bool:
    return row["source_status"] in {"missing", "unreadable"}


def _is_candidate_only(row: dict[str, Any]) -> bool:
    return row["source_status"] == "candidate_only"


def _is_review_required(row: dict[str, Any]) -> bool:
    return row["source_status"] == "review_required" or row["review_status"] == "review_required"


def _is_available_artifact_state(row: dict[str, Any]) -> bool:
    return (
        row["source_status"] == "available"
        and not _is_conflict(row)
        and not _is_ignored(row)
        and row["review_status"] not in BLOCKING_REVIEW_STATUSES
    )


def _is_official_business(row: dict[str, Any]) -> bool:
    return (
        row["artifact_type"] in OFFICIAL_BUSINESS_ARTIFACT_TYPES
        or row["source_family"] in OFFICIAL_BUSINESS_SOURCE_FAMILIES
    )


def _is_critical_financial(row: dict[str, Any]) -> bool:
    return (
        row["artifact_type"] in CRITICAL_FINANCIAL_ARTIFACT_TYPES
        or row["source_family"] in CRITICAL_FINANCIAL_SOURCE_FAMILIES
    )


def _row_counts_as_category_present(row: dict[str, Any]) -> bool:
    return (
        row["source_status"] not in {"missing", "unreadable", "ignored", "invalidated", "conflict_open"}
        and row["review_status"] != "conflict_open"
        and row["artifact_type"] != "ignored"
    )


def _row_counts_as_formal_ready(row: dict[str, Any]) -> bool:
    return _is_available_artifact_state(row)


def _category_summary(rows: list[dict[str, Any]], predicate: Any) -> dict[str, Any]:
    category_rows = [row for row in rows if predicate(row)]
    present_rows = [row for row in category_rows if _row_counts_as_category_present(row)]
    formal_rows = [row for row in category_rows if _row_counts_as_formal_ready(row)]
    blocked_rows = [
        row
        for row in category_rows
        if row["source_status"] in BLOCKING_SOURCE_STATUSES or row["review_status"] in BLOCKING_REVIEW_STATUSES
    ]
    return {
        "present": bool(present_rows),
        "formal_ready": bool(formal_rows),
        "artifact_ids": [row["artifact_id"] for row in present_rows],
        "formal_ready_artifact_ids": [row["artifact_id"] for row in formal_rows],
        "blocked_artifact_ids": [row["artifact_id"] for row in blocked_rows],
    }


def _build_readiness_categories(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        OFFICIAL_BUSINESS_EVIDENCE_CATEGORY: _category_summary(rows, _is_official_business),
        CRITICAL_FINANCIAL_ARTIFACT_CATEGORY: _category_summary(rows, _is_critical_financial),
    }


def _validate_category_summary(value: Any, field: str) -> dict[str, Any]:
    summary = _require_dict(value, field)
    result = {
        "present": _require_bool(summary.get("present"), f"{field}.present"),
        "formal_ready": _require_bool(summary.get("formal_ready"), f"{field}.formal_ready"),
        "artifact_ids": _require_string_list(summary.get("artifact_ids"), f"{field}.artifact_ids"),
        "formal_ready_artifact_ids": _require_string_list(
            summary.get("formal_ready_artifact_ids"),
            f"{field}.formal_ready_artifact_ids",
        ),
        "blocked_artifact_ids": _require_string_list(
            summary.get("blocked_artifact_ids"),
            f"{field}.blocked_artifact_ids",
        ),
    }
    extra = set(summary) - set(result)
    if extra:
        raise ValueError(f"{field} has unsupported fields: {sorted(extra)}")
    return result


def _validate_readiness_categories(value: Any) -> dict[str, dict[str, Any]]:
    categories = _require_dict(value, "readiness_evidence_categories")
    required = (OFFICIAL_BUSINESS_EVIDENCE_CATEGORY, CRITICAL_FINANCIAL_ARTIFACT_CATEGORY)
    missing = [field for field in required if field not in categories]
    if missing:
        raise ValueError(f"readiness_evidence_categories missing required fields: {missing}")
    extra = set(categories) - set(required)
    if extra:
        raise ValueError(f"readiness_evidence_categories has unsupported fields: {sorted(extra)}")
    return {
        OFFICIAL_BUSINESS_EVIDENCE_CATEGORY: _validate_category_summary(
            categories[OFFICIAL_BUSINESS_EVIDENCE_CATEGORY],
            OFFICIAL_BUSINESS_EVIDENCE_CATEGORY,
        ),
        CRITICAL_FINANCIAL_ARTIFACT_CATEGORY: _validate_category_summary(
            categories[CRITICAL_FINANCIAL_ARTIFACT_CATEGORY],
            CRITICAL_FINANCIAL_ARTIFACT_CATEGORY,
        ),
    }


def _group_rows(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    available: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    candidate_only: list[dict[str, Any]] = []
    review_required: list[dict[str, Any]] = []
    conflict: list[dict[str, Any]] = []
    ignored: list[dict[str, Any]] = []

    for row in rows:
        if _is_conflict(row):
            conflict.append(deepcopy(row))
        elif _is_ignored(row):
            ignored.append(deepcopy(row))
        elif _is_missing(row):
            missing.append(deepcopy(row))
        elif _is_candidate_only(row):
            candidate_only.append(deepcopy(row))
        elif _is_review_required(row):
            review_required.append(deepcopy(row))
        elif _is_available_artifact_state(row):
            available.append(deepcopy(row))

    return {
        "available_data_artifacts": available,
        "missing_data_artifacts": missing,
        "candidate_only_artifacts": candidate_only,
        "review_required_artifacts": review_required,
        "conflict_artifacts": conflict,
        "ignored_artifacts": ignored,
    }


def _has_safety_block(payload: dict[str, Any]) -> bool:
    if payload.get("identity_resolution_status") == "blocked":
        return True
    for text in _iter_keys_and_text(payload.get("caveats", [])):
        normalised = _normalise_marker(text)
        if "safety_violation" in normalised or "forbidden_marker" in normalised:
            return True
    return False


def _base_caveats(extra: list[str] | None = None) -> list[str]:
    caveats = [
        "Artifact-state readiness only; no artifact content was read.",
        "Available artifact state is not fact verification.",
        "Readiness flags are indicators only and do not trigger report generation.",
    ]
    if extra:
        caveats.extend(extra)
    return caveats


def build_deterministic_evidence_inventory(
    *,
    ticker_local_artifact_inventory: dict[str, Any],
    stock_code: str | None = None,
    company_name: str | None = None,
    not_for_trading_advice: bool = True,
) -> dict[str, Any]:
    """Build deterministic artifact-state evidence inventory from Phase 2C inventory."""

    if not_for_trading_advice is not True:
        raise ValueError("not_for_trading_advice must be true")

    inventory = _validate_ticker_inventory(ticker_local_artifact_inventory)
    if stock_code is not None and _require_stock_code(stock_code, "stock_code") != inventory["stock_code"]:
        raise ValueError("stock_code must match ticker_local_artifact_inventory stock_code")
    if company_name is not None:
        _require_string(company_name, "company_name")

    rows = [_validate_artifact_row(row) for row in inventory["artifact_rows"]]
    grouped = _group_rows(rows)
    categories = _build_readiness_categories(rows)

    evidence_inventory = {
        "schema_version": DETERMINISTIC_EVIDENCE_INVENTORY_SCHEMA_VERSION,
        "stock_code": inventory["stock_code"],
        "company_name": company_name if company_name is not None else inventory["company_name"],
        "identity_resolution_status": inventory["identity_resolution_status"],
        "evidence_inventory": rows,
        "available_data_artifacts": grouped["available_data_artifacts"],
        "missing_data_artifacts": grouped["missing_data_artifacts"],
        "candidate_only_artifacts": grouped["candidate_only_artifacts"],
        "review_required_artifacts": grouped["review_required_artifacts"],
        "conflict_artifacts": grouped["conflict_artifacts"],
        "ignored_artifacts": grouped["ignored_artifacts"],
        "readiness_evidence_categories": categories,
        "caveats": _base_caveats(list(inventory["caveats"])),
        "lineage_refs": list(inventory["lineage_refs"])
        + ["ticker_local_artifact_inventory.v1", "deterministic_evidence_inventory.v1"],
        "not_for_trading_advice": True,
    }
    return validate_deterministic_evidence_inventory(evidence_inventory)


def validate_deterministic_evidence_inventory(evidence_inventory: dict[str, Any]) -> dict[str, Any]:
    """Validate deterministic evidence inventory and return a defensive copy."""

    _require_dict(evidence_inventory, "deterministic_evidence_inventory")
    missing = [
        field for field in REQUIRED_DETERMINISTIC_EVIDENCE_INVENTORY_FIELDS if field not in evidence_inventory
    ]
    if missing:
        raise ValueError(f"deterministic evidence inventory missing required fields: {missing}")

    validated = deepcopy(evidence_inventory)
    extra = set(validated) - set(REQUIRED_DETERMINISTIC_EVIDENCE_INVENTORY_FIELDS)
    if extra:
        raise ValueError(f"deterministic evidence inventory has unsupported fields: {sorted(extra)}")

    schema_version = _require_string(validated["schema_version"], "schema_version")
    if schema_version != DETERMINISTIC_EVIDENCE_INVENTORY_SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {DETERMINISTIC_EVIDENCE_INVENTORY_SCHEMA_VERSION}")
    _require_stock_code(validated["stock_code"], "stock_code")
    _require_string(validated["company_name"], "company_name")
    _require_enum(validated["identity_resolution_status"], _identity_statuses(), "identity_resolution_status")
    if validated["not_for_trading_advice"] is not True:
        raise ValueError("not_for_trading_advice must be true")

    validated["evidence_inventory"] = _validate_artifact_row_list(
        validated["evidence_inventory"],
        "evidence_inventory",
    )
    for field in (
        "available_data_artifacts",
        "missing_data_artifacts",
        "candidate_only_artifacts",
        "review_required_artifacts",
        "conflict_artifacts",
        "ignored_artifacts",
    ):
        validated[field] = _validate_artifact_row_list(validated[field], field)
    validated["readiness_evidence_categories"] = _validate_readiness_categories(
        validated["readiness_evidence_categories"]
    )
    validated["caveats"] = _require_string_list(validated["caveats"], "caveats")
    validated["lineage_refs"] = _require_string_list(validated["lineage_refs"], "lineage_refs")

    _reject_prohibited_output_keys(validated)
    _reject_forbidden_markers(validated)
    _validate_payload_safety(_mask_payload_for_safety(validated))
    return validated


def _readiness_for_identity(identity_status: str) -> tuple[str, str]:
    if identity_status == "blocked":
        return "blocked", "identity is blocked"
    if identity_status == "conflict_requires_review":
        return "evidence_conflict_review_required", "identity conflict requires review"
    if identity_status == "ambiguous":
        return "classification_review_required", "identity is ambiguous"
    return "data_collection_required", "identity is not resolved"


def _readiness_decision(evidence_inventory: dict[str, Any]) -> tuple[str, bool, bool, str]:
    identity_status = evidence_inventory["identity_resolution_status"]
    conflict_artifacts = evidence_inventory["conflict_artifacts"]
    ignored_artifacts = evidence_inventory["ignored_artifacts"]
    available_artifacts = evidence_inventory["available_data_artifacts"]
    candidate_only_artifacts = evidence_inventory["candidate_only_artifacts"]
    review_required_artifacts = evidence_inventory["review_required_artifacts"]
    rows = evidence_inventory["evidence_inventory"]
    categories = evidence_inventory["readiness_evidence_categories"]
    official = categories[OFFICIAL_BUSINESS_EVIDENCE_CATEGORY]
    critical = categories[CRITICAL_FINANCIAL_ARTIFACT_CATEGORY]
    safety_block = _has_safety_block(evidence_inventory)
    only_ignored = bool(rows) and not available_artifacts and len(ignored_artifacts) == len(rows)
    critical_blocked = bool(critical["blocked_artifact_ids"])

    if safety_block:
        return "blocked", False, False, "safety or forbidden marker blocks readiness"
    if identity_status != "resolved":
        readiness, reason = _readiness_for_identity(identity_status)
        return readiness, False, False, reason
    if conflict_artifacts:
        return "evidence_conflict_review_required", False, False, "conflict artifacts require review"
    if only_ignored:
        return "data_collection_required", False, False, "only ignored artifacts are available"
    if not rows:
        return "data_collection_required", False, False, "no artifacts are available"
    if not official["present"]:
        return "data_collection_required", False, False, "official/business evidence artifact state is missing"
    if not critical["present"]:
        return "data_collection_required", False, False, "critical financial artifact state is missing"

    accepted_ready = official["formal_ready"] and critical["formal_ready"] and not critical_blocked
    experimental_ready = (
        bool(available_artifacts)
        and official["present"]
        and critical["present"]
        and not accepted_ready
        and not conflict_artifacts
    )

    if accepted_ready:
        return "accepted_report_ready", True, False, ""
    if experimental_ready:
        return "experimental_report_ready", False, True, ""
    if candidate_only_artifacts or review_required_artifacts:
        return "classification_review_required", False, False, "artifact classification or review is required"
    return "data_collection_required", False, False, "required formal readiness artifacts are unavailable"


def build_readiness_skeleton(
    *,
    ticker_local_artifact_inventory: dict[str, Any] | None = None,
    deterministic_evidence_inventory: dict[str, Any] | None = None,
    not_for_trading_advice: bool = True,
) -> dict[str, Any]:
    """Build a fail-closed readiness skeleton from validated artifact state."""

    if not_for_trading_advice is not True:
        raise ValueError("not_for_trading_advice must be true")
    if deterministic_evidence_inventory is None:
        if ticker_local_artifact_inventory is None:
            raise ValueError("ticker_local_artifact_inventory or deterministic_evidence_inventory is required")
        evidence_inventory = build_deterministic_evidence_inventory(
            ticker_local_artifact_inventory=ticker_local_artifact_inventory,
            not_for_trading_advice=True,
        )
    else:
        evidence_inventory = validate_deterministic_evidence_inventory(deterministic_evidence_inventory)

    readiness_level, accepted, experimental, fail_closed_reason = _readiness_decision(evidence_inventory)
    skeleton = {
        "schema_version": READINESS_SKELETON_SCHEMA_VERSION,
        "stock_code": evidence_inventory["stock_code"],
        "company_name": evidence_inventory["company_name"],
        "identity_resolution_status": evidence_inventory["identity_resolution_status"],
        "evidence_inventory": evidence_inventory["evidence_inventory"],
        "available_data_artifacts": evidence_inventory["available_data_artifacts"],
        "missing_data_artifacts": evidence_inventory["missing_data_artifacts"],
        "candidate_only_artifacts": evidence_inventory["candidate_only_artifacts"],
        "review_required_artifacts": evidence_inventory["review_required_artifacts"],
        "conflict_artifacts": evidence_inventory["conflict_artifacts"],
        "ignored_artifacts": evidence_inventory["ignored_artifacts"],
        "readiness_evidence_categories": evidence_inventory["readiness_evidence_categories"],
        "readiness_level": readiness_level,
        "can_generate_accepted_report": accepted,
        "can_generate_experimental_report": experimental,
        "fail_closed_reason": fail_closed_reason,
        "caveats": _base_caveats(evidence_inventory["caveats"]),
        "lineage_refs": list(evidence_inventory["lineage_refs"]) + ["readiness_skeleton.v1"],
        "not_for_trading_advice": True,
    }
    return validate_readiness_skeleton(skeleton)


def validate_readiness_skeleton(readiness_skeleton: dict[str, Any]) -> dict[str, Any]:
    """Validate a readiness skeleton and return a defensive copy."""

    _require_dict(readiness_skeleton, "readiness_skeleton")
    missing = [field for field in REQUIRED_READINESS_SKELETON_FIELDS if field not in readiness_skeleton]
    if missing:
        raise ValueError(f"readiness skeleton missing required fields: {missing}")

    validated = deepcopy(readiness_skeleton)
    extra = set(validated) - set(REQUIRED_READINESS_SKELETON_FIELDS)
    if extra:
        raise ValueError(f"readiness skeleton has unsupported fields: {sorted(extra)}")

    schema_version = _require_string(validated["schema_version"], "schema_version")
    if schema_version != READINESS_SKELETON_SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {READINESS_SKELETON_SCHEMA_VERSION}")
    _require_stock_code(validated["stock_code"], "stock_code")
    _require_string(validated["company_name"], "company_name")
    identity_status = _require_enum(
        validated["identity_resolution_status"],
        _identity_statuses(),
        "identity_resolution_status",
    )
    readiness_level = _require_enum(validated["readiness_level"], _readiness_levels(), "readiness_level")
    accepted = _require_bool(validated["can_generate_accepted_report"], "can_generate_accepted_report")
    experimental = _require_bool(
        validated["can_generate_experimental_report"],
        "can_generate_experimental_report",
    )
    if validated["not_for_trading_advice"] is not True:
        raise ValueError("not_for_trading_advice must be true")

    validated["evidence_inventory"] = _validate_artifact_row_list(
        validated["evidence_inventory"],
        "evidence_inventory",
    )
    for field in (
        "available_data_artifacts",
        "missing_data_artifacts",
        "candidate_only_artifacts",
        "review_required_artifacts",
        "conflict_artifacts",
        "ignored_artifacts",
    ):
        validated[field] = _validate_artifact_row_list(validated[field], field)
    validated["readiness_evidence_categories"] = _validate_readiness_categories(
        validated["readiness_evidence_categories"]
    )
    validated["fail_closed_reason"] = _require_string(
        validated["fail_closed_reason"],
        "fail_closed_reason",
    )
    validated["caveats"] = _require_string_list(validated["caveats"], "caveats")
    validated["lineage_refs"] = _require_string_list(validated["lineage_refs"], "lineage_refs")

    if identity_status != "resolved" and (accepted or experimental):
        raise ValueError("report-generation readiness flags require resolved identity")
    if validated["conflict_artifacts"] and (accepted or experimental):
        raise ValueError("conflict artifacts must fail closed for readiness flags")
    if readiness_level in {
        "blocked",
        "data_collection_required",
        "classification_review_required",
        "evidence_conflict_review_required",
    } and (accepted or experimental):
        raise ValueError(f"{readiness_level} must fail closed for readiness flags")
    if readiness_level == "experimental_report_ready" and (accepted or not experimental):
        raise ValueError("experimental_report_ready requires only experimental readiness flag")
    if readiness_level == "accepted_report_ready":
        if not accepted:
            raise ValueError("accepted_report_ready requires can_generate_accepted_report=true")
        if experimental:
            raise ValueError("accepted_report_ready requires can_generate_experimental_report=false")
    if accepted:
        official = validated["readiness_evidence_categories"][OFFICIAL_BUSINESS_EVIDENCE_CATEGORY]
        critical = validated["readiness_evidence_categories"][CRITICAL_FINANCIAL_ARTIFACT_CATEGORY]
        if not official["formal_ready"] or not critical["formal_ready"]:
            raise ValueError("accepted readiness requires formal official/business and financial artifact state")
        if critical["blocked_artifact_ids"]:
            raise ValueError("accepted readiness cannot have critical readiness blockers")
    if experimental:
        official = validated["readiness_evidence_categories"][OFFICIAL_BUSINESS_EVIDENCE_CATEGORY]
        critical = validated["readiness_evidence_categories"][CRITICAL_FINANCIAL_ARTIFACT_CATEGORY]
        if not official["present"] or not critical["present"]:
            raise ValueError("experimental readiness requires official/business and financial artifact state")
        if not validated["available_data_artifacts"]:
            raise ValueError("experimental readiness requires available non-ignored artifact state")

    _reject_prohibited_output_keys(validated)
    _reject_forbidden_markers(validated)
    _validate_payload_safety(_mask_payload_for_safety(validated))
    return validated


__all__ = [
    "CRITICAL_FINANCIAL_ARTIFACT_CATEGORY",
    "DETERMINISTIC_EVIDENCE_INVENTORY_SCHEMA_VERSION",
    "OFFICIAL_BUSINESS_EVIDENCE_CATEGORY",
    "READINESS_SKELETON_SCHEMA_VERSION",
    "REQUIRED_DETERMINISTIC_EVIDENCE_INVENTORY_FIELDS",
    "REQUIRED_READINESS_SKELETON_FIELDS",
    "build_deterministic_evidence_inventory",
    "build_readiness_skeleton",
    "validate_deterministic_evidence_inventory",
    "validate_readiness_skeleton",
]
