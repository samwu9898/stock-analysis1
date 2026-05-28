# -*- coding: utf-8 -*-
"""Accepted Research Report V1 artifact manifest helpers.

This module builds, validates, reads, and writes the accepted-artifact manifest
as a local JSON artifact. It does not locate reports, change CLI behavior, read
environment variables, contact data sources, or generate any runtime manifest
unless the explicit writer is called by the caller.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from .research_report_v1 import ResearchReportSecretError, _assert_no_secret_like_payload


MANIFEST_VERSION = "accepted_artifact_manifest.v1"
DEFAULT_MANIFEST_RELATIVE_PATH = "output/research_reports/accepted_manifest.json"
MANIFEST_SCOPE = "research_report_v1"
REPORT_TYPE = "fundamental_research_report_v1"

FRESHNESS_STATUSES = {
    "current",
    "unknown",
    "stale",
    "superseded",
    "invalidated",
}

REQUIRED_ARTIFACT_KINDS = ("html", "markdown", "json")
REQUIRED_HASH_KEYS = ("html_sha256", "markdown_sha256", "json_sha256")
ARTIFACT_ROOT = PurePosixPath("output/research_reports")
MANIFEST_FILENAME = "accepted_manifest.json"

FORBIDDEN_RECOMMENDATION_KEYS = {
    "buy",
    "sell",
    "target_price",
    "position",
    "portfolio_weight",
}

_CODE_RE = re.compile(r"^\d{6}$")
_SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")


class AcceptedManifestError(RuntimeError):
    """Base error for accepted artifact manifest operations."""


class ManifestValidationError(AcceptedManifestError):
    """Raised when a manifest payload fails schema or policy validation."""


class ManifestPathBoundaryError(AcceptedManifestError):
    """Raised when a manifest path escapes the allowed local boundary."""


class ManifestHashMismatchError(AcceptedManifestError):
    """Raised when an accepted artifact hash does not match the manifest."""


class ManifestEntryNotFoundError(AcceptedManifestError):
    """Raised when a stock code is not present in the manifest."""


def build_accepted_manifest(
    entries: list[dict[str, Any]],
    *,
    created_at: str | None = None,
    updated_at: str | None = None,
) -> dict[str, Any]:
    """Build and validate an in-memory accepted artifact manifest payload."""

    if not isinstance(entries, list):
        raise ManifestValidationError("manifest entries must be a list")
    now = _utc_now()
    payload = {
        "version": MANIFEST_VERSION,
        "created_at": created_at or now,
        "updated_at": updated_at or created_at or now,
        "manifest_scope": MANIFEST_SCOPE,
        "entries": copy.deepcopy(entries),
    }
    validate_accepted_manifest(payload)
    return payload


def validate_accepted_manifest(payload: dict[str, Any]) -> None:
    """Validate top-level manifest shape and every entry."""

    if not isinstance(payload, dict):
        raise ManifestValidationError("accepted manifest must be a dict payload")
    if payload.get("version") != MANIFEST_VERSION:
        raise ManifestValidationError("accepted manifest version is unsupported")
    if payload.get("manifest_scope") != MANIFEST_SCOPE:
        raise ManifestValidationError("accepted manifest scope must be research_report_v1")
    if not isinstance(payload.get("created_at"), str) or not payload.get("created_at"):
        raise ManifestValidationError("accepted manifest created_at must be a non-empty string")
    if not isinstance(payload.get("updated_at"), str) or not payload.get("updated_at"):
        raise ManifestValidationError("accepted manifest updated_at must be a non-empty string")
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ManifestValidationError("accepted manifest entries must be a list")

    _assert_no_forbidden_recommendation_keys(payload)

    seen_codes: set[str] = set()
    for entry in entries:
        validate_manifest_entry(entry)
        code = entry["code"]
        if code in seen_codes:
            raise ManifestValidationError(f"duplicate accepted manifest entry code: {code}")
        seen_codes.add(code)
    _assert_no_secret_like_payload_for_manifest(payload)


def validate_manifest_entry(entry: dict[str, Any]) -> None:
    """Validate a single manifest entry."""

    if not isinstance(entry, dict):
        raise ManifestValidationError("manifest entry must be a dict")
    _assert_no_forbidden_recommendation_keys(entry)

    code = entry.get("code")
    if not isinstance(code, str) or not _CODE_RE.fullmatch(code):
        raise ManifestValidationError("manifest entry code must be a 6 digit string")
    if not isinstance(entry.get("company_name"), str) or not entry.get("company_name"):
        raise ManifestValidationError("manifest entry company_name must be a non-empty string")
    if entry.get("report_type") != REPORT_TYPE:
        raise ManifestValidationError("manifest entry report_type is unsupported")
    if not isinstance(entry.get("presentation_profile"), str) or not entry.get("presentation_profile"):
        raise ManifestValidationError("manifest entry presentation_profile must be a non-empty string")

    artifacts = entry.get("accepted_artifacts")
    if not isinstance(artifacts, dict):
        raise ManifestValidationError("manifest entry accepted_artifacts must be a dict")
    for kind in REQUIRED_ARTIFACT_KINDS:
        value = artifacts.get(kind)
        if not isinstance(value, str) or not value:
            raise ManifestValidationError(f"manifest entry accepted_artifacts.{kind} is required")
        _validate_artifact_relative_path(value)

    hashes = entry.get("artifact_hashes")
    if not isinstance(hashes, dict):
        raise ManifestValidationError("manifest entry artifact_hashes must be a dict")
    for key in REQUIRED_HASH_KEYS:
        value = hashes.get(key)
        if not _is_sha256_hex(value):
            raise ManifestValidationError(f"manifest entry artifact_hashes.{key} must be a sha256 hex string")

    acceptance = entry.get("acceptance")
    if not isinstance(acceptance, dict):
        raise ManifestValidationError("manifest entry acceptance must be a dict")
    for key in ("accepted_at", "accepted_stage", "accepted_by", "acceptance_notes"):
        if key not in acceptance:
            raise ManifestValidationError(f"manifest entry acceptance.{key} is required")
    if not isinstance(acceptance.get("acceptance_notes"), list):
        raise ManifestValidationError("manifest entry acceptance.acceptance_notes must be a list")

    freshness = entry.get("freshness")
    if not isinstance(freshness, dict):
        raise ManifestValidationError("manifest entry freshness must be a dict")
    for key in (
        "freshness_status",
        "source_data_period",
        "financial_report_period",
        "valuation_as_of_date",
        "report_generated_at",
        "accepted_at",
        "valid_until",
        "last_freshness_check_at",
        "freshness_reason",
        "staleness_triggers",
        "manual_override",
    ):
        if key not in freshness:
            raise ManifestValidationError(f"manifest entry freshness.{key} is required")
    if freshness.get("freshness_status") not in FRESHNESS_STATUSES:
        raise ManifestValidationError("manifest entry freshness_status is unsupported")
    if not isinstance(freshness.get("staleness_triggers"), list):
        raise ManifestValidationError("manifest entry freshness.staleness_triggers must be a list")

    lineage = entry.get("lineage")
    if not isinstance(lineage, dict):
        raise ManifestValidationError("manifest entry lineage must be a dict")
    if not isinstance(lineage.get("supersedes"), list):
        raise ManifestValidationError("manifest entry lineage.supersedes must be a list")
    if not isinstance(lineage.get("source_artifacts"), list):
        raise ManifestValidationError("manifest entry lineage.source_artifacts must be a list")
    for item in lineage.get("supersedes", []):
        _validate_superseded_artifact_record(item)

    safety = entry.get("safety")
    if not isinstance(safety, dict):
        raise ManifestValidationError("manifest entry safety must be a dict")
    for key in ("not_for_trading_advice", "no_token", "no_provider_call"):
        if safety.get(key) is not True:
            raise ManifestValidationError(f"manifest entry safety.{key} must be true")
    _assert_no_secret_like_payload_for_manifest(entry)


def get_manifest_entry(payload: dict[str, Any], code: str) -> dict[str, Any]:
    """Return a manifest entry by code."""

    validate_accepted_manifest(payload)
    if not isinstance(code, str) or not _CODE_RE.fullmatch(code):
        raise ManifestEntryNotFoundError("manifest entry code not found")
    for entry in payload["entries"]:
        if entry["code"] == code:
            return entry
    raise ManifestEntryNotFoundError("manifest entry code not found")


def get_freshness_status(entry: dict[str, Any]) -> str:
    """Return the validated freshness status for an entry."""

    validate_manifest_entry(entry)
    return str(entry["freshness"]["freshness_status"])


def is_manifest_entry_usable_by_default(entry: dict[str, Any]) -> bool:
    """Return whether a manifest entry may be returned as the accepted baseline."""

    status = get_freshness_status(entry)
    return status in {"current", "unknown", "stale"}


def build_freshness_warning(entry: dict[str, Any]) -> str | None:
    """Build a user-visible freshness warning, if needed."""

    status = get_freshness_status(entry)
    if status == "current":
        return None
    reason = str(entry["freshness"].get("freshness_reason") or "").strip()
    suffix = f": {reason}" if reason else ""
    if status == "unknown":
        return f"freshness_status=unknown; accepted report freshness is not fully verified{suffix}"
    if status == "stale":
        return f"freshness_status=stale; accepted report may be outdated{suffix}"
    if status == "superseded":
        return f"freshness_status=superseded; artifact is not the accepted baseline{suffix}"
    if status == "invalidated":
        return f"freshness_status=invalidated; artifact must not be used as accepted report{suffix}"
    raise ManifestValidationError("manifest entry freshness_status is unsupported")


def compute_file_sha256(path: Path) -> str:
    """Compute SHA-256 for one local file."""

    file_path = Path(path)
    if not file_path.is_file():
        raise ManifestHashMismatchError("manifest artifact file is missing")
    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_manifest_entry_hashes(entry: dict[str, Any], *, repo_root: Path) -> None:
    """Verify all accepted artifact hashes for one entry against repo_root."""

    validate_manifest_entry(entry)
    root = Path(repo_root).resolve(strict=False)
    artifacts = entry["accepted_artifacts"]
    hashes = entry["artifact_hashes"]
    for kind, hash_key in (
        ("html", "html_sha256"),
        ("markdown", "markdown_sha256"),
        ("json", "json_sha256"),
    ):
        relative_path = artifacts[kind]
        artifact_path = _resolve_artifact_path_under_root(relative_path, root)
        expected = hashes[hash_key].lower()
        if not _SHA256_RE.fullmatch(expected):
            raise ManifestValidationError(f"manifest entry artifact_hashes.{hash_key} must be a sha256 hex string")
        actual = compute_file_sha256(artifact_path)
        if actual != expected:
            raise ManifestHashMismatchError(f"manifest artifact hash mismatch for {kind}: <masked>")


def read_accepted_manifest(path: Path) -> dict[str, Any]:
    """Read and validate an accepted manifest JSON file."""

    manifest_path = _resolve_manifest_file_path(path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_accepted_manifest(payload)
    return payload


def write_accepted_manifest(payload: dict[str, Any], path: Path) -> Path:
    """Validate, secret-scan, and write an accepted manifest JSON file."""

    validate_accepted_manifest(payload)
    _assert_no_secret_like_payload_for_manifest(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    manifest_path = _resolve_manifest_file_path(path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_artifact_relative_path(value: str) -> None:
    if _is_absolute_or_traversal(value):
        raise ManifestPathBoundaryError("accepted artifact path escapes output/research_reports")
    path = PurePosixPath(value)
    try:
        path.relative_to(ARTIFACT_ROOT)
    except ValueError as exc:
        raise ManifestPathBoundaryError("accepted artifact path must stay under output/research_reports") from exc
    if path == ARTIFACT_ROOT:
        raise ManifestPathBoundaryError("accepted artifact path must point to a file under output/research_reports")


def _validate_superseded_artifact_record(item: Any) -> None:
    if not isinstance(item, dict):
        raise ManifestValidationError("lineage.supersedes entries must be dict records")
    for key in ("artifact_type", "path", "sha256", "superseded_reason", "superseded_at", "replacement_path"):
        if key not in item:
            raise ManifestValidationError(f"lineage.supersedes entry {key} is required")
    if item.get("artifact_type") not in REQUIRED_ARTIFACT_KINDS:
        raise ManifestValidationError("lineage.supersedes artifact_type is unsupported")
    _validate_artifact_relative_path(str(item["path"]))
    _validate_artifact_relative_path(str(item["replacement_path"]))
    sha256 = item.get("sha256")
    if sha256 not in (None, "") and not _is_sha256_hex(sha256):
        raise ManifestValidationError("lineage.supersedes sha256 must be sha256 hex when present")


def _resolve_artifact_path_under_root(relative_path: str, root: Path) -> Path:
    _validate_artifact_relative_path(relative_path)
    candidate = root / PurePosixPath(relative_path)
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ManifestPathBoundaryError("manifest artifact path escapes repo root") from exc
    return resolved


def _resolve_manifest_file_path(path: Path) -> Path:
    raw_path = Path(path)
    if any(part == ".." for part in raw_path.parts):
        raise ManifestPathBoundaryError("accepted manifest path contains traversal")
    resolved = raw_path.resolve(strict=False)
    if resolved.name != MANIFEST_FILENAME:
        raise ManifestPathBoundaryError("accepted manifest writer may only target accepted_manifest.json")
    return resolved


def _is_absolute_or_traversal(value: str) -> bool:
    if not isinstance(value, str) or not value:
        return True
    if "\\" in value or ":" in value:
        return True
    path = PurePosixPath(value)
    if path.is_absolute():
        return True
    return any(part in ("", ".", "..") for part in path.parts)


def _is_sha256_hex(value: object) -> bool:
    return isinstance(value, str) and bool(_SHA256_RE.fullmatch(value))


def _assert_no_forbidden_recommendation_keys(payload: Any) -> None:
    for key in _walk_keys(payload):
        if str(key).lower() in FORBIDDEN_RECOMMENDATION_KEYS:
            raise ManifestValidationError("accepted manifest contains forbidden recommendation keys")


def _assert_no_secret_like_payload_for_manifest(payload: Any) -> None:
    try:
        _assert_no_secret_like_payload(_payload_for_secret_scan(payload, ()))
    except ResearchReportSecretError as exc:
        raise ManifestValidationError("accepted manifest contains secret-like data: <masked>") from exc


def _payload_for_secret_scan(value: Any, key_path: tuple[str, ...]) -> Any:
    if isinstance(value, dict):
        return {key: _payload_for_secret_scan(child, key_path + (str(key),)) for key, child in value.items()}
    if isinstance(value, list):
        return [_payload_for_secret_scan(child, key_path) for child in value]
    if isinstance(value, str):
        current_key = key_path[-1] if key_path else ""
        if current_key in {"sha256", "html_sha256", "markdown_sha256", "json_sha256"}:
            return "<manifest_artifact_reference>"
        if _is_manifest_artifact_path_field(key_path, value):
            return "<manifest_artifact_reference>"
    return value


def _is_manifest_artifact_path_field(key_path: tuple[str, ...], value: str) -> bool:
    if not key_path:
        return False
    current_key = key_path[-1]
    is_accepted_artifact = len(key_path) >= 2 and key_path[-2] == "accepted_artifacts" and current_key in REQUIRED_ARTIFACT_KINDS
    is_superseded_artifact = "supersedes" in key_path and current_key in {"path", "replacement_path"}
    if not (is_accepted_artifact or is_superseded_artifact):
        return False
    try:
        _validate_artifact_relative_path(value)
    except ManifestPathBoundaryError:
        return False
    return True


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)
