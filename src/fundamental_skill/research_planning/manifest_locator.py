# -*- coding: utf-8 -*-
"""Schema and pure validators for read-only manifest locator rows.

Phase 2B-1 is intentionally side-effect free. The helpers in this module only
validate dictionary shape and path strings. They do not read manifests, inspect
report artifacts, scan directories, compute file hashes, call providers, create
Local Artifact Index rows, or generate runtime artifacts.
"""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

from .local_artifact_index import validate_artifact_path_safety
from .safety import validate_payload_safety


MANIFEST_LOCATOR_PAYLOAD_SCHEMA_VERSION = "manifest_locator_payload.v1"
MANIFEST_ENTRY_ROW_SCHEMA_VERSION = "manifest_entry_row.v1"

MANIFEST_EXISTS_STATUSES = (
    "exists",
    "missing",
    "unreadable",
    "unknown",
    "not_checked",
)

MANIFEST_SCHEMA_STATUSES = (
    "valid",
    "invalid_json",
    "schema_mismatch",
    "unreadable",
    "not_checked",
    "review_required",
)

ACCEPTED_STATUSES = (
    "accepted",
    "missing",
    "stale",
    "superseded",
    "invalidated",
    "conflict_open",
    "review_required",
    "unknown",
)

FRESHNESS_STATUSES = (
    "current",
    "unknown",
    "stale",
    "superseded",
    "invalidated",
    "not_applicable",
)

HASH_STATUSES = (
    "match",
    "mismatch",
    "missing",
    "not_checked",
    "not_applicable",
    "review_required",
)

SOURCE_STATUSES = (
    "available",
    "missing",
    "partial",
    "candidate_only",
    "review_required",
    "conflict_open",
    "stale",
    "invalidated",
    "unreadable",
    "ignored",
)

ARTIFACT_KINDS = (
    "accepted_manifest",
    "research_report_v1",
    "superseded_report_artifact",
    "lineage_artifact",
    "unknown",
)

ARTIFACT_FORMATS = (
    "json",
    "markdown",
    "html",
    "manifest",
    "unknown",
)

UNMATCHED_REASONS = (
    "",
    "missing",
    "data_collection_required",
    "unrelated_ticker",
    "conflict_open",
    "schema_mismatch",
    "manifest_missing",
    "manifest_unreadable",
    "invalid_json",
    "duplicate_entries",
    "unsafe_path",
    "artifact_missing",
    "hash_mismatch",
    "review_required",
)

REQUIRED_MANIFEST_ENTRY_ROW_FIELDS = (
    "schema_version",
    "stock_code",
    "company_name",
    "artifact_path",
    "artifact_kind",
    "artifact_format",
    "accepted_status",
    "freshness_status",
    "hash_status",
    "source_status",
    "caveats",
    "not_for_trading_advice",
)

REQUIRED_MANIFEST_LOCATOR_PAYLOAD_FIELDS = (
    "schema_version",
    "manifest_path",
    "manifest_exists_status",
    "manifest_schema_status",
    "manifest_entry_count",
    "matched_entries",
    "unmatched_reason",
    "stock_code",
    "company_name",
    "report_artifact_refs",
    "freshness_status",
    "lineage_refs",
    "caveats",
    "not_for_trading_advice",
)

_SIX_DIGIT_CODE_RE = re.compile(r"\d{6}")

_FORBIDDEN_MARKERS = (
    "verified_fact",
    "verified fact",
    "auto_verified",
    "auto verified",
    "fixture_promotion",
    "fixture promotion",
    "promote_fixture",
    "promote fixture",
    "promote_to_fixture",
    "accepted_manifest_update",
    "accepted manifest update",
    "accepted_manifest_write",
    "accepted manifest write",
    "write_accepted_manifest",
    "update_accepted_manifest",
    "manifest_write",
    "manifest write",
    "manifest_update",
    "manifest update",
    "accepted_artifact_manifest_update",
    "provider_primary_switch",
    "provider primary switch",
    "primary_provider_switch",
    "switch_provider_primary",
    "set_provider_primary",
    "research_report_v1_update",
    "research report v1 update",
    "update_research_report_v1",
    "research_report_v1_write",
    "report_update",
    "buy_advice",
    "sell_advice",
    "target_price",
    "price_target",
    "position_size",
    "position_sizing",
    "portfolio_weight",
    "portfolio_allocation",
    "technical_signal",
    "trading_signal",
    "trade_signal",
)


def _normalise_marker(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _iter_text_values(value: Any) -> list[str]:
    if isinstance(value, dict):
        texts: list[str] = []
        for key, child in value.items():
            texts.append(str(key))
            texts.extend(_iter_text_values(child))
        return texts
    if isinstance(value, list):
        texts = []
        for child in value:
            texts.extend(_iter_text_values(child))
        return texts
    if isinstance(value, str):
        return [value]
    return []


def _validate_marker_safety(payload: dict[str, Any], payload_name: str) -> None:
    normalised_markers = tuple(_normalise_marker(marker) for marker in _FORBIDDEN_MARKERS)
    for text in _iter_text_values(payload):
        normalised = _normalise_marker(text)
        if any(marker and marker in normalised for marker in normalised_markers):
            raise ValueError(f"{payload_name} safety violation: forbidden downstream marker is not allowed")


def _mask_path_fields_for_payload_safety(value: Any) -> Any:
    if isinstance(value, dict):
        masked: dict[str, Any] = {}
        for key, child in value.items():
            if key in {"artifact_path", "manifest_path"}:
                masked[key] = f"<{key}>"
            elif key == "report_artifact_refs":
                masked[key] = _mask_report_artifact_refs_for_payload_safety(child)
            else:
                masked[key] = _mask_path_fields_for_payload_safety(child)
        return masked
    if isinstance(value, list):
        return [_mask_path_fields_for_payload_safety(child) for child in value]
    return value


def _mask_report_artifact_refs_for_payload_safety(value: Any) -> Any:
    if isinstance(value, list):
        return [_mask_report_artifact_refs_for_payload_safety(child) for child in value]
    if isinstance(value, str):
        return "<report_artifact_ref>"
    if isinstance(value, dict):
        masked: dict[str, Any] = {}
        for key, child in value.items():
            if key in {"artifact_path", "manifest_path", "path"}:
                masked[key] = f"<{key}>"
            else:
                masked[key] = _mask_report_artifact_refs_for_payload_safety(child)
        return masked
    return value


def _require_string(value: Any, path: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{path} must be a string")
    return value


def _require_enum(value: Any, allowed: tuple[str, ...], path: str) -> str:
    text = _require_string(value, path)
    if text not in allowed:
        raise ValueError(f"{path} must be one of {sorted(allowed)}")
    return text


def _require_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{path} must be a list")
    return value


def _validate_stock_code(value: Any, path: str) -> str:
    text = _require_string(value, path)
    if text and not _SIX_DIGIT_CODE_RE.fullmatch(text):
        raise ValueError(f"{path} must be empty or a six-digit ticker code")
    return text


def _validate_not_for_trading_advice(value: Any) -> None:
    if value is not True:
        raise ValueError("not_for_trading_advice must be true")


def _validate_report_artifact_refs(value: Any) -> list[Any]:
    refs = _require_list(value, "report_artifact_refs")
    normalised_refs: list[Any] = []
    for index, ref in enumerate(refs):
        if isinstance(ref, str):
            normalised_refs.append(validate_artifact_path_safety(ref))
            continue
        if isinstance(ref, dict):
            normalised_ref = deepcopy(ref)
            for key in ("artifact_path", "manifest_path", "path"):
                if key not in normalised_ref:
                    continue
                normalised_ref[key] = validate_artifact_path_safety(
                    _require_string(normalised_ref[key], f"report_artifact_refs[{index}].{key}")
                )
            normalised_refs.append(normalised_ref)
            continue
        raise ValueError(f"report_artifact_refs[{index}] must be a string or dict")
    return normalised_refs


def _validate_name_only_identity_state(row: dict[str, Any]) -> None:
    if not row["company_name"] or row["stock_code"]:
        return
    has_review_state = (
        row.get("source_status") == "review_required"
        or row.get("accepted_status") == "review_required"
        or bool(row.get("caveats"))
    )
    if not has_review_state:
        raise ValueError("company_name-only identity must remain review_required")


def _validate_common_safety(payload: dict[str, Any], payload_name: str) -> None:
    _validate_marker_safety(payload, payload_name)
    validate_payload_safety(_mask_path_fields_for_payload_safety(payload))


def build_manifest_entry_row(
    *,
    artifact_path: str,
    stock_code: str = "",
    company_name: str = "",
    artifact_kind: str = "unknown",
    artifact_format: str = "unknown",
    accepted_status: str = "review_required",
    freshness_status: str = "unknown",
    hash_status: str = "not_checked",
    source_status: str = "review_required",
    caveats: list[Any] | None = None,
    not_for_trading_advice: bool = True,
    schema_version: str = MANIFEST_ENTRY_ROW_SCHEMA_VERSION,
) -> dict[str, Any]:
    """Build and validate a manifest entry locator row without file IO."""

    row = {
        "schema_version": schema_version,
        "stock_code": stock_code,
        "company_name": company_name,
        "artifact_path": artifact_path,
        "artifact_kind": artifact_kind,
        "artifact_format": artifact_format,
        "accepted_status": accepted_status,
        "freshness_status": freshness_status,
        "hash_status": hash_status,
        "source_status": source_status,
        "caveats": list(caveats or []),
        "not_for_trading_advice": not_for_trading_advice,
    }
    return validate_manifest_entry_row(row)


def validate_manifest_entry_row(row: dict[str, Any]) -> dict[str, Any]:
    """Validate a manifest entry locator row and return a defensive copy."""

    if not isinstance(row, dict):
        raise ValueError("manifest entry row must be a dict")
    missing = [field for field in REQUIRED_MANIFEST_ENTRY_ROW_FIELDS if field not in row]
    if missing:
        raise ValueError(f"manifest entry row missing required fields: {missing}")

    validated = deepcopy(row)
    _validate_not_for_trading_advice(validated["not_for_trading_advice"])

    schema_version = _require_string(validated["schema_version"], "schema_version")
    if schema_version != MANIFEST_ENTRY_ROW_SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {MANIFEST_ENTRY_ROW_SCHEMA_VERSION}")

    _validate_stock_code(validated["stock_code"], "stock_code")
    _require_string(validated["company_name"], "company_name")
    validated["artifact_path"] = validate_artifact_path_safety(validated["artifact_path"])

    _require_enum(validated["artifact_kind"], ARTIFACT_KINDS, "artifact_kind")
    _require_enum(validated["artifact_format"], ARTIFACT_FORMATS, "artifact_format")
    _require_enum(validated["accepted_status"], ACCEPTED_STATUSES, "accepted_status")
    _require_enum(validated["freshness_status"], FRESHNESS_STATUSES, "freshness_status")
    _require_enum(validated["hash_status"], HASH_STATUSES, "hash_status")
    _require_enum(validated["source_status"], SOURCE_STATUSES, "source_status")
    _require_list(validated["caveats"], "caveats")

    _validate_name_only_identity_state(validated)
    _validate_common_safety(validated, "manifest entry row")

    return validated


def build_manifest_locator_payload(
    *,
    manifest_path: str = "output/research_reports/accepted_manifest.json",
    manifest_exists_status: str = "not_checked",
    manifest_schema_status: str = "not_checked",
    manifest_entry_count: int = 0,
    matched_entries: list[Any] | None = None,
    unmatched_reason: str = "",
    stock_code: str = "",
    company_name: str = "",
    report_artifact_refs: list[Any] | None = None,
    freshness_status: str = "unknown",
    lineage_refs: list[Any] | None = None,
    caveats: list[Any] | None = None,
    not_for_trading_advice: bool = True,
    schema_version: str = MANIFEST_LOCATOR_PAYLOAD_SCHEMA_VERSION,
) -> dict[str, Any]:
    """Build and validate a read-only manifest locator payload without file IO."""

    payload = {
        "schema_version": schema_version,
        "manifest_path": manifest_path,
        "manifest_exists_status": manifest_exists_status,
        "manifest_schema_status": manifest_schema_status,
        "manifest_entry_count": manifest_entry_count,
        "matched_entries": list(matched_entries or []),
        "unmatched_reason": unmatched_reason,
        "stock_code": stock_code,
        "company_name": company_name,
        "report_artifact_refs": list(report_artifact_refs or []),
        "freshness_status": freshness_status,
        "lineage_refs": list(lineage_refs or []),
        "caveats": list(caveats or []),
        "not_for_trading_advice": not_for_trading_advice,
    }
    return validate_manifest_locator_payload(payload)


def validate_manifest_locator_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate a manifest locator payload and return a defensive copy."""

    if not isinstance(payload, dict):
        raise ValueError("manifest locator payload must be a dict")
    missing = [field for field in REQUIRED_MANIFEST_LOCATOR_PAYLOAD_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"manifest locator payload missing required fields: {missing}")

    validated = deepcopy(payload)
    _validate_not_for_trading_advice(validated["not_for_trading_advice"])

    schema_version = _require_string(validated["schema_version"], "schema_version")
    if schema_version != MANIFEST_LOCATOR_PAYLOAD_SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {MANIFEST_LOCATOR_PAYLOAD_SCHEMA_VERSION}")

    validated["manifest_path"] = validate_artifact_path_safety(validated["manifest_path"])
    _require_enum(validated["manifest_exists_status"], MANIFEST_EXISTS_STATUSES, "manifest_exists_status")
    _require_enum(validated["manifest_schema_status"], MANIFEST_SCHEMA_STATUSES, "manifest_schema_status")

    if not isinstance(validated["manifest_entry_count"], int) or validated["manifest_entry_count"] < 0:
        raise ValueError("manifest_entry_count must be a non-negative integer")

    matched_entries = _require_list(validated["matched_entries"], "matched_entries")
    for index, entry in enumerate(matched_entries):
        if not isinstance(entry, dict):
            raise ValueError(f"matched_entries[{index}] must be a dict")
        matched_entries[index] = validate_manifest_entry_row(entry)

    _require_enum(validated["unmatched_reason"], UNMATCHED_REASONS, "unmatched_reason")
    _validate_stock_code(validated["stock_code"], "stock_code")
    _require_string(validated["company_name"], "company_name")
    validated["report_artifact_refs"] = _validate_report_artifact_refs(validated["report_artifact_refs"])
    _require_enum(validated["freshness_status"], FRESHNESS_STATUSES, "freshness_status")
    _require_list(validated["lineage_refs"], "lineage_refs")
    _require_list(validated["caveats"], "caveats")

    _validate_common_safety(validated, "manifest locator payload")

    return validated
