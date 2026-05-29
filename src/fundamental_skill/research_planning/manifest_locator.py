# -*- coding: utf-8 -*-
"""Schema, validators, and adapters for read-only manifest locator rows.

Phase 2B-1 is intentionally side-effect free. The helpers in this module only
validate dictionary shape and path strings. They do not read manifests, inspect
report artifacts, scan directories, compute file hashes, call providers, create
facts, or generate runtime artifacts. The Phase 2B-3 adapter converts one
validated manifest entry into one Local Artifact Index row as artifact state
only; it still does not read manifests, artifact contents, or filesystem
metadata.
"""

from __future__ import annotations

from copy import deepcopy
import json
import os
import re
from typing import Any

from .local_artifact_index import build_artifact_row, validate_artifact_path_safety, validate_artifact_row
from .safety import validate_payload_safety


MANIFEST_LOCATOR_PAYLOAD_SCHEMA_VERSION = "manifest_locator_payload.v1"
MANIFEST_ENTRY_ROW_SCHEMA_VERSION = "manifest_entry_row.v1"
SYNTHETIC_MANIFEST_LOCATOR_INPUT_SCHEMA_VERSION = "synthetic_manifest_locator_input.v1"

_SYNTHETIC_MANIFEST_PAYLOAD_PATH = "output/research_reports/synthetic_manifest_locator_input.json"

_MANIFEST_ARTIFACT_KIND_TO_LOCAL_ARTIFACT = {
    "accepted_manifest": ("accepted_manifest", "accepted_manifest"),
    "research_report_v1": ("report_artifact_state", "research_report_v1"),
    "superseded_report_artifact": ("report_artifact_state", "research_report_v1"),
    "lineage_artifact": ("existing_local_report_artifact", "existing_local_reports"),
}

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
_WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[\\/]")
_URI_RE = re.compile(r"^[a-z][a-z0-9+.-]*://", re.IGNORECASE)
_SYNTHETIC_SECRET_SEGMENT_RE = re.compile(
    r"(^|[._\-\s])("
    r"token|tokens|secret|secrets|credential|credentials|password|passwd|key|keys|"
    r"private[_\-\s]*key|secret[_\-\s]*key|api[_\-\s]*key|access[_\-\s]*token|"
    r"tushare[_\-\s]*token|bearer|id_rsa|id_dsa|id_ed25519"
    r")($|[._\-\s])",
    re.IGNORECASE,
)
_SYNTHETIC_DOTENV_SEGMENT_RE = re.compile(r"^\.env($|[._-])", re.IGNORECASE)
_SYNTHETIC_MCP_SEGMENT_RE = re.compile(r"(^|[._-])mcp($|[._-])", re.IGNORECASE)

_FORBIDDEN_MARKERS = (
    "verified_fact",
    "verified fact",
    "auto_verified",
    "auto verified",
    "evidence_fact",
    "evidence fact",
    "accepted_evidence_fact",
    "accepted evidence fact",
    "report_fact",
    "report fact",
    "accepted_report_fact",
    "accepted report fact",
    "hypothesis",
    "hypothesis_generator",
    "hypothesis generator",
    "generate_hypothesis",
    "generate hypothesis",
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


def _coerce_synthetic_manifest_path(path: Any) -> str:
    try:
        text = os.fspath(path)
    except TypeError as exc:
        raise ValueError("synthetic manifest path must be an explicit filesystem path") from exc
    if not isinstance(text, str):
        raise ValueError("synthetic manifest path must be a text filesystem path")
    return text


def _normalise_synthetic_manifest_path(path: str) -> str:
    return path.strip().replace("\\", "/")


def _is_absolute_synthetic_manifest_path(path: str) -> bool:
    text = path.strip()
    return bool(_WINDOWS_ABSOLUTE_RE.match(text)) or text.startswith("/")


def _synthetic_manifest_path_safety_reason(path: str) -> str | None:
    normalized = _normalise_synthetic_manifest_path(path)
    if not normalized:
        return "path is empty"
    if "\x00" in normalized:
        return "path contains a null byte"
    if _URI_RE.match(normalized) or normalized.startswith("//"):
        return "URI and UNC paths are not allowed"
    if not _is_absolute_synthetic_manifest_path(path):
        return "synthetic manifest path must be an explicit tmp_path file"
    segments = [segment for segment in normalized.split("/") if segment]
    lowered_segments = [segment.lower() for segment in segments]
    if any(segment == ".." for segment in segments):
        return "path traversal is not allowed"
    if "output" in lowered_segments:
        return "real output paths are not allowed"
    if "fixtures" in lowered_segments or "fixture" in lowered_segments:
        return "fixture paths are not allowed"
    lowered = normalized.lower()
    if lowered.endswith("/research_reports/accepted_manifest.json") or lowered.endswith(
        "/output/research_reports/accepted_manifest.json"
    ):
        return "real accepted manifest path is not allowed"
    if "tushare_token" in lowered or "access_token" in lowered or "api_key" in lowered:
        return "token or API credential path is not allowed"
    for index, segment in enumerate(segments):
        if _SYNTHETIC_DOTENV_SEGMENT_RE.search(segment):
            return ".env paths are not allowed"
        if _SYNTHETIC_SECRET_SEGMENT_RE.search(segment):
            return "token, secret, credential, or key paths are not allowed"
        if _SYNTHETIC_MCP_SEGMENT_RE.search(segment) or (
            segment.lower() == "config" and index + 1 < len(segments) and "mcp" in segments[index + 1].lower()
        ):
            return "MCP config paths are not allowed"
    return None


def _build_synthetic_manifest_failure_payload(
    *,
    stock_code: str,
    company_name_hint: str,
    manifest_exists_status: str,
    manifest_schema_status: str,
    unmatched_reason: str,
    caveat: str,
    manifest_entry_count: int = 0,
) -> dict[str, Any]:
    return build_manifest_locator_payload(
        manifest_path=_SYNTHETIC_MANIFEST_PAYLOAD_PATH,
        manifest_exists_status=manifest_exists_status,
        manifest_schema_status=manifest_schema_status,
        manifest_entry_count=manifest_entry_count,
        matched_entries=[],
        unmatched_reason=unmatched_reason,
        stock_code=stock_code,
        company_name=company_name_hint,
        report_artifact_refs=[],
        freshness_status="unknown",
        lineage_refs=[],
        caveats=[caveat],
    )


def _schema_mismatch_payload(
    *,
    stock_code: str,
    company_name_hint: str,
    caveat: str,
    manifest_entry_count: int = 0,
) -> dict[str, Any]:
    return _build_synthetic_manifest_failure_payload(
        stock_code=stock_code,
        company_name_hint=company_name_hint,
        manifest_exists_status="exists",
        manifest_schema_status="schema_mismatch",
        unmatched_reason="schema_mismatch",
        manifest_entry_count=manifest_entry_count,
        caveat=caveat,
    )


def _review_required_payload(
    *,
    stock_code: str,
    company_name_hint: str,
    caveat: str,
    manifest_entry_count: int = 0,
) -> dict[str, Any]:
    return _build_synthetic_manifest_failure_payload(
        stock_code=stock_code,
        company_name_hint=company_name_hint,
        manifest_exists_status="exists",
        manifest_schema_status="review_required",
        unmatched_reason="review_required",
        manifest_entry_count=manifest_entry_count,
        caveat=caveat,
    )


def _require_synthetic_manifest_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("synthetic manifest must be a dict")
    return value


def _entry_artifacts(entry: dict[str, Any]) -> list[Any]:
    has_artifacts = "artifacts" in entry
    has_report_artifacts = "report_artifacts" in entry
    if has_artifacts and has_report_artifacts:
        raise ValueError("synthetic entry must not define both artifacts and report_artifacts")
    if not has_artifacts and not has_report_artifacts:
        raise ValueError("synthetic entry missing artifacts")
    artifacts = entry["artifacts"] if has_artifacts else entry["report_artifacts"]
    return _require_list(artifacts, "artifacts")


def _invalid_artifact_payload(
    *,
    exc: ValueError,
    stock_code: str,
    company_name_hint: str,
    manifest_entry_count: int,
) -> dict[str, Any]:
    message = str(exc)
    if "unsafe artifact_path" in message:
        return _build_synthetic_manifest_failure_payload(
            stock_code=stock_code,
            company_name_hint=company_name_hint,
            manifest_exists_status="exists",
            manifest_schema_status="review_required",
            unmatched_reason="unsafe_path",
            manifest_entry_count=manifest_entry_count,
            caveat="Synthetic artifact path was unsafe; no rows emitted.",
        )
    if "safety violation" in message or "planning payload safety violation" in message:
        return _review_required_payload(
            stock_code=stock_code,
            company_name_hint=company_name_hint,
            manifest_entry_count=manifest_entry_count,
            caveat="Synthetic manifest safety violation; no rows emitted.",
        )
    return _schema_mismatch_payload(
        stock_code=stock_code,
        company_name_hint=company_name_hint,
        manifest_entry_count=manifest_entry_count,
        caveat="Synthetic artifact schema was invalid; no rows emitted.",
    )


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


def _manifest_entry_artifact_target(entry: dict[str, Any]) -> tuple[str, str]:
    artifact_kind = entry["artifact_kind"]
    if artifact_kind not in _MANIFEST_ARTIFACT_KIND_TO_LOCAL_ARTIFACT:
        raise ValueError("artifact_kind cannot be adapted into a Local Artifact Index row")
    return _MANIFEST_ARTIFACT_KIND_TO_LOCAL_ARTIFACT[artifact_kind]


def _map_manifest_entry_source_status(entry: dict[str, Any]) -> str:
    accepted_status = entry["accepted_status"]
    source_status = entry["source_status"]

    if accepted_status == "conflict_open" or source_status == "conflict_open":
        return "conflict_open"
    if accepted_status == "invalidated" or source_status == "invalidated":
        return "invalidated"
    if accepted_status == "missing" or source_status == "missing":
        return "missing"
    if accepted_status in {"stale", "superseded"} or source_status == "stale":
        return "stale"
    if source_status in {"unreadable", "ignored", "partial", "candidate_only", "review_required"}:
        return source_status
    if accepted_status == "accepted" and source_status == "available":
        return "available"
    return "review_required"


def _map_manifest_entry_review_status(entry: dict[str, Any], source_status: str) -> str:
    if source_status == "conflict_open":
        return "conflict_open"
    if source_status == "invalidated":
        return "invalidated"
    if source_status == "available" and entry["accepted_status"] == "accepted":
        return "unknown"
    return "review_required"


def _manifest_entry_adapter_caveats(entry: dict[str, Any]) -> list[Any]:
    caveats = list(entry["caveats"])
    caveats.extend(
        [
            "Manifest locator state only; not verified as fact.",
            "Manifest artifact path state only; report artifact content was not read.",
            f"Manifest artifact_format={entry['artifact_format']} preserved as locator metadata only.",
            (
                f"Manifest accepted_status={entry['accepted_status']}, "
                f"source_status={entry['source_status']}, and hash_status={entry['hash_status']} "
                "preserved as artifact state only; no real file hash was computed."
            ),
        ]
    )
    return caveats


def _manifest_entry_adapter_lineage_refs(
    entry: dict[str, Any],
    lineage_refs: list[Any] | None,
) -> list[str]:
    refs: list[str] = []
    if lineage_refs is not None:
        for index, ref in enumerate(_require_list(lineage_refs, "lineage_refs")):
            refs.append(_require_string(ref, f"lineage_refs[{index}]"))
    refs.extend(
        [
            "manifest_locator:manifest_entry_row.v1",
            "manifest_locator:artifact_path_field",
            f"manifest_locator:artifact_kind={entry['artifact_kind']}",
            f"manifest_locator:artifact_format={entry['artifact_format']}",
            f"manifest_locator:accepted_status={entry['accepted_status']}",
            f"manifest_locator:freshness_status={entry['freshness_status']}",
            f"manifest_locator:hash_status={entry['hash_status']}",
            f"manifest_locator:source_status={entry['source_status']}",
        ]
    )
    return refs


def manifest_entry_to_artifact_row(
    manifest_entry: dict[str, Any],
    *,
    lineage_refs: list[Any] | None = None,
) -> dict[str, Any]:
    """Convert one manifest entry row into one Local Artifact Index row.

    The adapter accepts only ``manifest_entry_row.v1`` dictionaries and
    defensively re-validates the input before mapping it. It records manifest
    locator state as artifact inventory only. It does not read manifests, check
    artifact existence, read report artifacts, compute real file hashes, write
    files, emit evidence facts, generate hypotheses, or enter report
    integration.
    """

    entry = validate_manifest_entry_row(manifest_entry)
    if not entry["artifact_path"].strip():
        raise ValueError("artifact_path is required for manifest entry adapter")

    artifact_type, source_family = _manifest_entry_artifact_target(entry)
    source_status = _map_manifest_entry_source_status(entry)
    review_status = _map_manifest_entry_review_status(entry, source_status)
    row = build_artifact_row(
        artifact_type=artifact_type,
        artifact_path=entry["artifact_path"],
        source_family=source_family,
        stock_code=entry["stock_code"],
        company_name=entry["company_name"],
        source_status=source_status,
        review_status=review_status,
        freshness_status=entry["freshness_status"],
        caveats=_manifest_entry_adapter_caveats(entry),
        lineage_refs=_manifest_entry_adapter_lineage_refs(entry, lineage_refs),
        not_for_trading_advice=True,
    )
    return validate_artifact_row(row)


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


def parse_synthetic_manifest_locator(
    synthetic_manifest_path: Any,
    *,
    stock_code: str,
    company_name_hint: str = "",
) -> dict[str, Any]:
    """Parse one explicitly provided tmp_path synthetic manifest JSON.

    This parser is synthetic-only. It reads exactly the caller-provided
    manifest JSON file, maps matching artifact references into
    ``manifest_entry_row.v1`` rows, and returns a
    ``manifest_locator_payload.v1`` payload. It never scans directories, never
    falls back to retained accepted samples, never reads artifact paths, never
    checks artifact existence, never hashes artifacts, and never writes files.
    """

    requested_stock_code = _validate_stock_code(stock_code, "stock_code")
    requested_company_name = _require_string(company_name_hint, "company_name_hint")
    manifest_path = _coerce_synthetic_manifest_path(synthetic_manifest_path)

    path_safety_reason = _synthetic_manifest_path_safety_reason(manifest_path)
    if path_safety_reason:
        return _build_synthetic_manifest_failure_payload(
            stock_code=requested_stock_code,
            company_name_hint=requested_company_name,
            manifest_exists_status="not_checked",
            manifest_schema_status="review_required",
            unmatched_reason="unsafe_path",
            caveat="Synthetic manifest path was unsafe; no file was read.",
        )

    try:
        with open(manifest_path, "r", encoding="utf-8") as manifest_file:
            raw_manifest = json.load(manifest_file)
    except FileNotFoundError:
        return _build_synthetic_manifest_failure_payload(
            stock_code=requested_stock_code,
            company_name_hint=requested_company_name,
            manifest_exists_status="missing",
            manifest_schema_status="not_checked",
            unmatched_reason="manifest_missing",
            caveat="Synthetic manifest was missing; no fallback was attempted.",
        )
    except json.JSONDecodeError:
        return _build_synthetic_manifest_failure_payload(
            stock_code=requested_stock_code,
            company_name_hint=requested_company_name,
            manifest_exists_status="exists",
            manifest_schema_status="invalid_json",
            unmatched_reason="invalid_json",
            caveat="Synthetic manifest JSON was invalid; no rows emitted.",
        )
    except OSError:
        return _build_synthetic_manifest_failure_payload(
            stock_code=requested_stock_code,
            company_name_hint=requested_company_name,
            manifest_exists_status="unreadable",
            manifest_schema_status="unreadable",
            unmatched_reason="manifest_unreadable",
            caveat="Synthetic manifest was unreadable; no fallback was attempted.",
        )

    try:
        manifest = _require_synthetic_manifest_dict(raw_manifest)
        _validate_common_safety(manifest, "synthetic manifest")
    except ValueError:
        return _review_required_payload(
            stock_code=requested_stock_code,
            company_name_hint=requested_company_name,
            caveat="Synthetic manifest safety violation; no rows emitted.",
        )

    if manifest.get("schema_version") != SYNTHETIC_MANIFEST_LOCATOR_INPUT_SCHEMA_VERSION:
        return _schema_mismatch_payload(
            stock_code=requested_stock_code,
            company_name_hint=requested_company_name,
            caveat="Synthetic manifest schema_version was invalid; no rows emitted.",
        )
    if not isinstance(manifest.get("generated_at"), str):
        return _schema_mismatch_payload(
            stock_code=requested_stock_code,
            company_name_hint=requested_company_name,
            caveat="Synthetic manifest generated_at was invalid; no rows emitted.",
        )
    if manifest.get("not_for_trading_advice") is not True:
        return _schema_mismatch_payload(
            stock_code=requested_stock_code,
            company_name_hint=requested_company_name,
            caveat="Synthetic manifest policy flag was false; no rows emitted.",
        )
    if "entries" not in manifest:
        return _schema_mismatch_payload(
            stock_code=requested_stock_code,
            company_name_hint=requested_company_name,
            caveat="Synthetic manifest entries were missing; no rows emitted.",
        )
    if not isinstance(manifest["entries"], list):
        return _schema_mismatch_payload(
            stock_code=requested_stock_code,
            company_name_hint=requested_company_name,
            caveat="Synthetic manifest entries must be a list; no rows emitted.",
        )

    entries = manifest["entries"]
    manifest_entry_count = len(entries)
    parsed_entries: list[dict[str, Any]] = []
    try:
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                raise ValueError(f"entries[{index}] must be a dict")
            entry_stock_code = _validate_stock_code(entry.get("stock_code", ""), f"entries[{index}].stock_code")
            entry_company_name = _require_string(entry.get("company_name", ""), f"entries[{index}].company_name")
            if entry.get("not_for_trading_advice") is not True:
                raise ValueError(f"entries[{index}].not_for_trading_advice must be true")
            artifacts = _entry_artifacts(entry)
            parsed_entries.append(
                {
                    "stock_code": entry_stock_code,
                    "company_name": entry_company_name,
                    "artifacts": artifacts,
                }
            )
    except ValueError:
        return _schema_mismatch_payload(
            stock_code=requested_stock_code,
            company_name_hint=requested_company_name,
            manifest_entry_count=manifest_entry_count,
            caveat="Synthetic manifest entries were invalid; no rows emitted.",
        )

    exact_matches = [entry for entry in parsed_entries if entry["stock_code"] == requested_stock_code]
    if len(exact_matches) > 1:
        return _build_synthetic_manifest_failure_payload(
            stock_code=requested_stock_code,
            company_name_hint=requested_company_name,
            manifest_exists_status="exists",
            manifest_schema_status="review_required",
            unmatched_reason="duplicate_entries",
            manifest_entry_count=manifest_entry_count,
            caveat="Synthetic manifest had duplicate entries for the requested code; review required.",
        )

    if not exact_matches:
        name_conflicts = [
            entry
            for entry in parsed_entries
            if requested_company_name and entry["company_name"] == requested_company_name
        ]
        if name_conflicts:
            return _build_synthetic_manifest_failure_payload(
                stock_code=requested_stock_code,
                company_name_hint=requested_company_name,
                manifest_exists_status="exists",
                manifest_schema_status="review_required",
                unmatched_reason="conflict_open",
                manifest_entry_count=manifest_entry_count,
                caveat="Synthetic company-name hint matched a different code; review required.",
            )
        return _build_synthetic_manifest_failure_payload(
            stock_code=requested_stock_code,
            company_name_hint=requested_company_name,
            manifest_exists_status="exists",
            manifest_schema_status="valid",
            unmatched_reason="data_collection_required",
            manifest_entry_count=manifest_entry_count,
            caveat="Unknown ticker requires data collection; no accepted-sample fallback.",
        )

    matched_entry = exact_matches[0]
    matched_company_name = matched_entry["company_name"]
    if requested_company_name and matched_company_name and matched_company_name != requested_company_name:
        return _build_synthetic_manifest_failure_payload(
            stock_code=requested_stock_code,
            company_name_hint=requested_company_name,
            manifest_exists_status="exists",
            manifest_schema_status="review_required",
            unmatched_reason="conflict_open",
            manifest_entry_count=manifest_entry_count,
            caveat="Synthetic manifest code and company-name hint conflicted; review required.",
        )

    matched_rows: list[dict[str, Any]] = []
    for artifact in matched_entry["artifacts"]:
        if not isinstance(artifact, dict):
            return _schema_mismatch_payload(
                stock_code=requested_stock_code,
                company_name_hint=requested_company_name,
                manifest_entry_count=manifest_entry_count,
                caveat="Synthetic artifact entries were invalid; no rows emitted.",
            )
        try:
            if artifact.get("not_for_trading_advice") is not True:
                raise ValueError("artifact not_for_trading_advice must be true")
            if "caveats" not in artifact:
                raise ValueError("artifact caveats must be present")
            artifact_caveats = _require_list(artifact["caveats"], "artifact.caveats")
            row = build_manifest_entry_row(
                stock_code=matched_entry["stock_code"],
                company_name=matched_company_name,
                artifact_path=artifact.get("artifact_path", ""),
                artifact_kind=artifact.get("artifact_kind", ""),
                artifact_format=artifact.get("artifact_format", ""),
                accepted_status=artifact.get("accepted_status", ""),
                freshness_status=artifact.get("freshness_status", ""),
                hash_status=artifact.get("hash_status", ""),
                source_status=artifact.get("source_status", ""),
                caveats=artifact_caveats,
                not_for_trading_advice=artifact.get("not_for_trading_advice"),
            )
        except ValueError as exc:
            return _invalid_artifact_payload(
                exc=exc,
                stock_code=requested_stock_code,
                company_name_hint=requested_company_name,
                manifest_entry_count=manifest_entry_count,
            )
        matched_rows.append(row)

    if not matched_rows:
        return _build_synthetic_manifest_failure_payload(
            stock_code=requested_stock_code,
            company_name_hint=requested_company_name,
            manifest_exists_status="exists",
            manifest_schema_status="review_required",
            unmatched_reason="missing",
            manifest_entry_count=manifest_entry_count,
            caveat="Synthetic manifest matched the requested code but contained no artifact rows.",
        )

    report_artifact_refs = [row["artifact_path"] for row in matched_rows]
    freshness_status = matched_rows[0]["freshness_status"] if len({row["freshness_status"] for row in matched_rows}) == 1 else "unknown"
    return build_manifest_locator_payload(
        manifest_path=_SYNTHETIC_MANIFEST_PAYLOAD_PATH,
        manifest_exists_status="exists",
        manifest_schema_status="valid",
        manifest_entry_count=manifest_entry_count,
        matched_entries=matched_rows,
        unmatched_reason="",
        stock_code=requested_stock_code,
        company_name=matched_company_name or requested_company_name,
        report_artifact_refs=report_artifact_refs,
        freshness_status=freshness_status,
        lineage_refs=[],
        caveats=["Synthetic manifest locator state only; report artifacts were not read."],
    )
