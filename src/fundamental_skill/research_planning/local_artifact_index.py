# -*- coding: utf-8 -*-
"""Schema and pure path classifiers for local artifact inventory rows.

Phase 2A is intentionally side-effect free. The helpers in this module only
validate row shape and classify path strings. They do not read manifests,
inspect artifact contents, scan directories, compute file hashes, call
providers, or generate runtime artifacts.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import re
from typing import Any

from .safety import validate_payload_safety


LOCAL_ARTIFACT_INDEX_ROW_SCHEMA_VERSION = "local_artifact_index_row.v1"

ARTIFACT_TYPES = (
    "accepted_manifest",
    "report_artifact_state",
    "normalized_fundamentals_artifact",
    "provider_separated_fundamentals_artifact",
    "evidence_pack_artifact",
    "provider_candidate_artifact",
    "official_disclosure_facts_artifact",
    "official_disclosure_candidate_artifact",
    "candidate_source_bridge_artifact",
    "bridge_aware_review_decision_artifact",
    "provider_candidate_review_decision_artifact",
    "score_confidence_explainability_artifact",
    "existing_local_report_artifact",
    "ignored",
)

SOURCE_FAMILIES = (
    "accepted_manifest",
    "research_report_v1",
    "normalized_fundamentals",
    "provider_fundamentals",
    "evidence_packs",
    "provider_candidates",
    "official_disclosures",
    "source_index",
    "workflow_signal",
    "score_confidence_explainability",
    "existing_local_reports",
    "ignored",
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

REVIEW_STATUSES = (
    "unknown",
    "not_reviewed",
    "review_required",
    "reviewed",
    "accepted_for_report_candidate",
    "rejected",
    "conflict_open",
    "invalidated",
)

FRESHNESS_STATUSES = (
    "current",
    "unknown",
    "stale",
    "superseded",
    "invalidated",
    "not_applicable",
)

REQUIRED_ARTIFACT_ROW_FIELDS = (
    "artifact_id",
    "artifact_type",
    "artifact_path",
    "stock_code",
    "company_name",
    "source_family",
    "schema_version",
    "created_at",
    "modified_at",
    "data_period",
    "sha256",
    "file_size",
    "source_status",
    "review_status",
    "freshness_status",
    "caveats",
    "lineage_refs",
    "not_for_trading_advice",
)

_SIX_DIGIT_CODE_RE = re.compile(r"\d{6}")
_SHA256_RE = re.compile(r"[0-9a-f]{64}", re.IGNORECASE)
_WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[\\/]")
_URI_RE = re.compile(r"^[a-z][a-z0-9+.-]*://", re.IGNORECASE)
_SECRET_SEGMENT_RE = re.compile(
    r"(^|[._\-\s])("
    r"token|tokens|secret|secrets|credential|credentials|password|passwd|key|keys|"
    r"private[_\-\s]*key|secret[_\-\s]*key|api[_\-\s]*key|access[_\-\s]*token|"
    r"tushare[_\-\s]*token|bearer|id_rsa|id_dsa|id_ed25519"
    r")($|[._\-\s])",
    re.IGNORECASE,
)
_DOTENV_SEGMENT_RE = re.compile(r"^\.env($|[._-])", re.IGNORECASE)
_MCP_SEGMENT_RE = re.compile(r"(^|[._-])mcp($|[._-])", re.IGNORECASE)

_TRADING_ADVICE_ROW_MARKERS = (
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


def _normalise_artifact_path(path: str) -> str:
    if not isinstance(path, str):
        raise ValueError("artifact_path must be a string")
    normalized = path.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    normalized = re.sub(r"/+", "/", normalized)
    return normalized


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


def _validate_artifact_row_marker_safety(row: dict[str, Any]) -> None:
    for text in _iter_text_values(row):
        normalised = _normalise_marker(text)
        if any(_normalise_marker(marker) in normalised for marker in _TRADING_ADVICE_ROW_MARKERS):
            raise ValueError("artifact row safety violation: trading advice marker is not allowed")


def _path_segments(path: str) -> list[str]:
    return [segment for segment in _normalise_artifact_path(path).split("/") if segment]


def _is_absolute_or_uri_path(path: str) -> bool:
    normalized = path.strip()
    return (
        bool(_WINDOWS_ABSOLUTE_RE.match(normalized))
        or normalized.startswith("/")
        or normalized.startswith("\\\\")
        or bool(_URI_RE.match(normalized))
    )


def _path_safety_reason(path: str) -> str | None:
    normalized = _normalise_artifact_path(path)
    if not normalized:
        return "path is empty"
    if "\x00" in normalized:
        return "path contains a null byte"
    if _is_absolute_or_uri_path(path):
        return "absolute paths and URI paths are not allowed"
    segments = _path_segments(normalized)
    if any(segment == ".." for segment in segments):
        return "path traversal is not allowed"
    lowered = normalized.lower()
    if "tushare_token" in lowered or "access_token" in lowered or "api_key" in lowered:
        return "token or API credential path is not allowed"
    for index, segment in enumerate(segments):
        if _DOTENV_SEGMENT_RE.search(segment):
            return ".env paths are not allowed"
        if _SECRET_SEGMENT_RE.search(segment):
            return "token, secret, credential, or key paths are not allowed"
        if _MCP_SEGMENT_RE.search(segment) or (
            segment.lower() == "config" and index + 1 < len(segments) and "mcp" in segments[index + 1].lower()
        ):
            return "MCP config paths are not allowed"
    return None


def _looks_suspicious_mojibake_or_unrelated(path: str) -> bool:
    normalized = _normalise_artifact_path(path)
    if not normalized:
        return True
    if any(ord(char) < 32 for char in normalized):
        return True
    non_ascii = sum(1 for char in normalized if ord(char) > 127)
    if non_ascii and non_ascii / max(len(normalized), 1) > 0.20:
        return True
    if any(0x2500 <= ord(char) <= 0x259F for char in normalized):
        return True
    return False


def validate_artifact_path_safety(path: str) -> str:
    """Return a normalized safe path, or raise ValueError.

    This validator only reasons about the path string. It never opens the path
    or checks whether it exists.
    """

    reason = _path_safety_reason(path)
    if reason:
        raise ValueError(f"unsafe artifact_path: {reason}")
    return _normalise_artifact_path(path)


_PATH_CLASSIFIERS: tuple[tuple[re.Pattern[str], dict[str, str]], ...] = (
    (
        re.compile(r"^output/research_reports/accepted_manifest\.json$", re.IGNORECASE),
        {
            "artifact_type": "accepted_manifest",
            "source_family": "accepted_manifest",
            "source_status": "available",
            "review_status": "unknown",
            "freshness_status": "unknown",
            "caveat": "Accepted manifest path state only; not fact verification.",
        },
    ),
    (
        re.compile(
            r"^output/research_reports/[^/]+/(?P<stock_code>\d{6})/"
            r"fundamental_research_report_v1\.(json|md|html)$",
            re.IGNORECASE,
        ),
        {
            "artifact_type": "report_artifact_state",
            "source_family": "research_report_v1",
            "source_status": "available",
            "review_status": "unknown",
            "freshness_status": "unknown",
            "caveat": "Research Report V1 artifact path state only; not a new fact source.",
        },
    ),
    (
        re.compile(r"^output/fundamental_(?P<stock_code>\d{6})\.json$", re.IGNORECASE),
        {
            "artifact_type": "normalized_fundamentals_artifact",
            "source_family": "normalized_fundamentals",
            "source_status": "available",
            "review_status": "unknown",
            "freshness_status": "unknown",
            "caveat": "Normalized fundamentals artifact state only.",
        },
    ),
    (
        re.compile(
            r"^output/(provider_fundamentals|fundamentals_by_provider)/.+(?P<stock_code>\d{6}).*\.json$",
            re.IGNORECASE,
        ),
        {
            "artifact_type": "provider_separated_fundamentals_artifact",
            "source_family": "provider_fundamentals",
            "source_status": "available",
            "review_status": "unknown",
            "freshness_status": "unknown",
            "caveat": "Provider-separated fundamentals state only; providers are not merged.",
        },
    ),
    (
        re.compile(r"^output/evidence_pack_(?P<stock_code>\d{6})\.json$", re.IGNORECASE),
        {
            "artifact_type": "evidence_pack_artifact",
            "source_family": "evidence_packs",
            "source_status": "available",
            "review_status": "unknown",
            "freshness_status": "unknown",
            "caveat": "Evidence pack artifact state only.",
        },
    ),
    (
        re.compile(
            r"^output/ground_truth_candidates/[^/]+/(?P<stock_code>\d{6})/fact_candidates\.json$",
            re.IGNORECASE,
        ),
        {
            "artifact_type": "provider_candidate_artifact",
            "source_family": "provider_candidates",
            "source_status": "candidate_only",
            "review_status": "not_reviewed",
            "freshness_status": "unknown",
            "caveat": "Provider candidate artifact only; not a verified fact.",
        },
    ),
    (
        re.compile(
            r"^output/official_disclosures/[^/]+/(?P<stock_code>\d{6})/.*candidate.*\.json$",
            re.IGNORECASE,
        ),
        {
            "artifact_type": "official_disclosure_candidate_artifact",
            "source_family": "official_disclosures",
            "source_status": "candidate_only",
            "review_status": "review_required",
            "freshness_status": "unknown",
            "caveat": "Official disclosure candidate artifact only; not report-ready.",
        },
    ),
    (
        re.compile(
            r"^output/official_disclosures/[^/]+/(?P<stock_code>\d{6})/.*facts.*\.json$",
            re.IGNORECASE,
        ),
        {
            "artifact_type": "official_disclosure_facts_artifact",
            "source_family": "official_disclosures",
            "source_status": "available",
            "review_status": "unknown",
            "freshness_status": "unknown",
            "caveat": "Official disclosure facts artifact state only; no automatic fact promotion.",
        },
    ),
    (
        re.compile(
            r"^output/candidate_source_bridges/[^/]+/(?P<stock_code>\d{6})/.*\.json$",
            re.IGNORECASE,
        ),
        {
            "artifact_type": "candidate_source_bridge_artifact",
            "source_family": "source_index",
            "source_status": "available",
            "review_status": "unknown",
            "freshness_status": "not_applicable",
            "caveat": "Bridge artifact is a source index, not a merge.",
        },
    ),
    (
        re.compile(
            r"^output/candidate_review_decisions_bridge_reviews/[^/]+/(?P<stock_code>\d{6})/.*\.json$",
            re.IGNORECASE,
        ),
        {
            "artifact_type": "bridge_aware_review_decision_artifact",
            "source_family": "workflow_signal",
            "source_status": "review_required",
            "review_status": "review_required",
            "freshness_status": "not_applicable",
            "caveat": "Bridge-aware review decision is a workflow signal, not fixture promotion.",
        },
    ),
    (
        re.compile(
            r"^output/ground_truth_candidate_reviews/[^/]+/(?P<stock_code>\d{6})/"
            r"candidate_review_decisions\.json$",
            re.IGNORECASE,
        ),
        {
            "artifact_type": "provider_candidate_review_decision_artifact",
            "source_family": "workflow_signal",
            "source_status": "review_required",
            "review_status": "review_required",
            "freshness_status": "not_applicable",
            "caveat": "Review decision is a workflow signal, not fixture promotion.",
        },
    ),
    (
        re.compile(r"^output/provider_comparison/[^/]+/(?P<stock_code>\d{6})/.*\.json$", re.IGNORECASE),
        {
            "artifact_type": "score_confidence_explainability_artifact",
            "source_family": "score_confidence_explainability",
            "source_status": "available",
            "review_status": "unknown",
            "freshness_status": "unknown",
            "caveat": "Score/confidence explainability artifact state only.",
        },
    ),
    (
        re.compile(r"^output/ai_report_(?P<stock_code>\d{6})\.json$", re.IGNORECASE),
        {
            "artifact_type": "existing_local_report_artifact",
            "source_family": "existing_local_reports",
            "source_status": "available",
            "review_status": "unknown",
            "freshness_status": "unknown",
            "caveat": "Existing local report artifact state only.",
        },
    ),
)


def _matches_known_artifact_path(path: str) -> bool:
    normalized = _normalise_artifact_path(path)
    return any(pattern.match(normalized) for pattern, _metadata in _PATH_CLASSIFIERS)


def should_ignore_artifact_path(path: str) -> bool:
    """Return True when a path should not become a collected artifact row."""

    try:
        normalized = _normalise_artifact_path(path)
    except ValueError:
        return True
    if _path_safety_reason(path):
        return True
    if _looks_suspicious_mojibake_or_unrelated(normalized):
        return True
    return not _matches_known_artifact_path(normalized)


def _ignored_classification(path: str, caveat: str) -> dict[str, Any]:
    return {
        "artifact_type": "ignored",
        "artifact_path": _normalise_artifact_path(path) if isinstance(path, str) else "",
        "stock_code": "",
        "company_name": "",
        "source_family": "ignored",
        "source_status": "ignored",
        "review_status": "review_required",
        "freshness_status": "not_applicable",
        "caveats": [caveat],
        "not_for_trading_advice": True,
    }


def classify_artifact_path(path: str) -> dict[str, Any]:
    """Classify an artifact path string without touching the filesystem."""

    if not isinstance(path, str):
        return _ignored_classification("", "Path is not a string and was ignored.")

    normalized = _normalise_artifact_path(path)
    safety_reason = _path_safety_reason(path)
    if safety_reason:
        return _ignored_classification("<ignored_sensitive_path>", safety_reason)
    if _looks_suspicious_mojibake_or_unrelated(normalized):
        return _ignored_classification(normalized, "Suspicious or unrelated path was ignored.")

    for pattern, metadata in _PATH_CLASSIFIERS:
        match = pattern.match(normalized)
        if not match:
            continue
        stock_code = match.groupdict().get("stock_code", "")
        return {
            "artifact_type": metadata["artifact_type"],
            "artifact_path": normalized,
            "stock_code": stock_code,
            "company_name": "",
            "source_family": metadata["source_family"],
            "source_status": metadata["source_status"],
            "review_status": metadata["review_status"],
            "freshness_status": metadata["freshness_status"],
            "caveats": [metadata["caveat"]],
            "not_for_trading_advice": True,
        }

    return _ignored_classification(normalized, "Unknown path is not an allowed local artifact family.")


def _default_artifact_id(artifact_type: str, artifact_path: str, stock_code: str, data_period: str) -> str:
    raw = "|".join([artifact_type, artifact_path, stock_code, data_period])
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"local_artifact_{digest}"


def build_artifact_row(
    *,
    artifact_type: str,
    artifact_path: str,
    source_family: str,
    artifact_id: str | None = None,
    stock_code: str = "",
    company_name: str = "",
    schema_version: str = LOCAL_ARTIFACT_INDEX_ROW_SCHEMA_VERSION,
    created_at: str = "",
    modified_at: str = "",
    data_period: str = "",
    sha256: str = "",
    file_size: int = 0,
    source_status: str = "available",
    review_status: str = "unknown",
    freshness_status: str = "unknown",
    caveats: list[str] | None = None,
    lineage_refs: list[str] | None = None,
    not_for_trading_advice: bool = True,
) -> dict[str, Any]:
    """Build and validate a Local Artifact Index row."""

    normalized_path = validate_artifact_path_safety(artifact_path)
    row = {
        "artifact_id": artifact_id
        or _default_artifact_id(artifact_type, normalized_path, stock_code, data_period),
        "artifact_type": artifact_type,
        "artifact_path": normalized_path,
        "stock_code": stock_code,
        "company_name": company_name,
        "source_family": source_family,
        "schema_version": schema_version,
        "created_at": created_at,
        "modified_at": modified_at,
        "data_period": data_period,
        "sha256": sha256,
        "file_size": file_size,
        "source_status": source_status,
        "review_status": review_status,
        "freshness_status": freshness_status,
        "caveats": list(caveats or []),
        "lineage_refs": list(lineage_refs or []),
        "not_for_trading_advice": not_for_trading_advice,
    }
    return validate_artifact_row(row)


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


def validate_artifact_row(row: dict[str, Any]) -> dict[str, Any]:
    """Validate a Local Artifact Index row and return a defensive copy."""

    if not isinstance(row, dict):
        raise ValueError("artifact row must be a dict")
    missing = [field for field in REQUIRED_ARTIFACT_ROW_FIELDS if field not in row]
    if missing:
        raise ValueError(f"artifact row missing required fields: {missing}")

    validated = deepcopy(row)
    if validated["not_for_trading_advice"] is not True:
        raise ValueError("not_for_trading_advice must be true")

    artifact_id = _require_string(validated["artifact_id"], "artifact_id")
    if not artifact_id.strip():
        raise ValueError("artifact_id must be a non-empty string")

    validated["artifact_path"] = validate_artifact_path_safety(validated["artifact_path"])

    _validate_artifact_row_marker_safety(validated)

    safety_payload = deepcopy(validated)
    safety_payload["artifact_path"] = "<artifact_path>"
    if safety_payload.get("sha256"):
        safety_payload["sha256"] = "<sha256>"
    validate_payload_safety(safety_payload)

    _require_enum(validated["artifact_type"], ARTIFACT_TYPES, "artifact_type")
    _require_enum(validated["source_family"], SOURCE_FAMILIES, "source_family")
    _require_enum(validated["source_status"], SOURCE_STATUSES, "source_status")
    _require_enum(validated["review_status"], REVIEW_STATUSES, "review_status")
    _require_enum(validated["freshness_status"], FRESHNESS_STATUSES, "freshness_status")

    schema_version = _require_string(validated["schema_version"], "schema_version")
    if schema_version != LOCAL_ARTIFACT_INDEX_ROW_SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {LOCAL_ARTIFACT_INDEX_ROW_SCHEMA_VERSION}")

    stock_code = _require_string(validated["stock_code"], "stock_code")
    if stock_code and not re.fullmatch(r"\d{6}", stock_code):
        raise ValueError("stock_code must be empty or a six-digit ticker code")

    for field in ("company_name", "created_at", "modified_at", "data_period", "sha256"):
        _require_string(validated[field], field)

    if validated["sha256"] and not _SHA256_RE.fullmatch(validated["sha256"]):
        raise ValueError("sha256 must be empty or a 64-character hexadecimal digest")

    if not isinstance(validated["file_size"], int) or validated["file_size"] < 0:
        raise ValueError("file_size must be a non-negative integer")

    _require_list(validated["caveats"], "caveats")
    _require_list(validated["lineage_refs"], "lineage_refs")

    return validated
