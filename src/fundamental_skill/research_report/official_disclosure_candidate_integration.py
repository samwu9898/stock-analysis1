# -*- coding: utf-8 -*-
"""In-memory official disclosure fact candidate adapter."""

from __future__ import annotations

import copy
import re
from typing import Any

from .official_disclosure_parser import (
    OfficialDisclosureSecretError,
    OfficialDisclosureValidationError,
    validate_official_disclosure_facts,
)


OFFICIAL_DISCLOSURE_SOURCE_TYPE = "official_disclosure"
OFFICIAL_DISCLOSURE_CANDIDATE_VERSION = "official_disclosure_fact_candidates.v1"
OFFICIAL_DISCLOSURE_EVIDENCE_TIER = "L1_official_disclosure"

REVIEW_STATUS_VALUES = {
    "auto_candidate",
    "manual_review_required",
    "blocked_by_caveat",
    "unsupported_or_missing",
}

CAVEAT_ONLY_TABLE_QUALITIES = {"unreliable_text_copy", "unusable"}
V1_TABLE_REVENUE_FIELD_SUFFIX = ".revenue"

FORBIDDEN_RECOMMENDATION_KEYS = {
    "buy",
    "sell",
    "target_price",
    "position",
    "portfolio_weight",
}

REQUIRED_CANDIDATE_ROW_KEYS = {
    "candidate_id",
    "field_path",
    "value",
    "unit",
    "period",
    "source_type",
    "evidence_tier",
    "source_document_id",
    "source_section",
    "source_page_or_anchor",
    "source_table_id",
    "source_row_index",
    "source_column_name",
    "source_column_map",
    "classification_type",
    "segment_name",
    "denominator",
    "table_quality",
    "extraction_confidence",
    "needs_human_review",
    "caveats",
    "review_status",
    "not_for_trading_advice",
}

_SECRET_KEY_RE = re.compile(
    r"(^|[^A-Za-z0-9])(token|key|secret|auth|credential|api[_-]?(?:key|token)|access[_-]?key)([^A-Za-z0-9]|$)",
    flags=re.IGNORECASE,
)
_KEYED_SECRET_RE = re.compile(
    r"(^|[^A-Za-z0-9])(token|key|secret|auth|credential|api[_-]?(?:key|token)|access[_-]?key)([^A-Za-z0-9]|$)\s*[:=]\s*[^\s,;&]+",
    flags=re.IGNORECASE,
)
_BEARER_RE = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]+", flags=re.IGNORECASE)
_REMOTE_CONTROL_RE = re.compile(
    r"\b" + "m" + "cp" + r"(?:s)?://[^\s\"'<>]+|\b" + "m" + "cp" + r"\?[^\s\"']*",
    flags=re.IGNORECASE,
)
_DOTFILE_CONFIG_RE = re.compile(
    r"(^|[\\/:\s\"'`=])\.env(?:\.[A-Za-z0-9_-]+)*\b",
    flags=re.IGNORECASE,
)
_TOKEN_LIKE_RE = re.compile(
    r"\b(?=[A-Za-z0-9._~+/=-]{32,}\b)"
    r"(?=[A-Za-z0-9._~+/=-]*[a-z])"
    r"(?=[A-Za-z0-9._~+/=-]*[A-Z])"
    r"(?=[A-Za-z0-9._~+/=-]*\d)"
    r"[A-Za-z0-9._~+/=-]+\b"
)
_LOCAL_SECRET_PATH_RE = re.compile(
    r"\b[A-Za-z]:[\\/]+Users[\\/]+[^\"'\s<>]*(?:[\\/]+(?:\.ssh|\.aws|\.azure|secrets?|credentials?)[\\/][^\"'\s<>]*)"
    r"|/(?:Users|home)/[^/\s]+/[^\"'\s<>]*(?:\.ssh|\.aws|\.azure|secrets?|credentials?)/[^\"'\s<>]*",
    flags=re.IGNORECASE,
)


class OfficialDisclosureCandidateIntegrationError(RuntimeError):
    """Base error for official disclosure candidate integration."""


class OfficialDisclosureCandidateValidationError(OfficialDisclosureCandidateIntegrationError):
    """Raised when an official disclosure candidate payload is invalid."""


class OfficialDisclosureCandidateConflictError(OfficialDisclosureCandidateValidationError):
    """Raised when official disclosure source lineage is inconsistent."""


class OfficialDisclosureCandidateSecretError(OfficialDisclosureCandidateIntegrationError):
    """Raised when candidate data contains secret-like material."""


def build_official_disclosure_candidate_row(
    *,
    official_fact: dict,
    source_document: dict,
    source_table: dict | None = None,
    candidate_id: str | None = None,
) -> dict:
    """Build one official disclosure candidate row from an extracted fact."""

    if not isinstance(official_fact, dict):
        raise OfficialDisclosureCandidateValidationError("official fact must be a dict")
    if not isinstance(source_document, dict):
        raise OfficialDisclosureCandidateValidationError("source document must be a dict")
    if source_table is not None and not isinstance(source_table, dict):
        raise OfficialDisclosureCandidateValidationError("source table must be a dict")
    _assert_no_forbidden_recommendation_keys(official_fact)
    _assert_no_forbidden_recommendation_keys(source_document)
    _assert_no_secret_like_payload(official_fact)
    _assert_no_secret_like_payload(source_document)
    _assert_no_verified_marker(official_fact)
    if source_table is not None:
        _assert_no_forbidden_recommendation_keys(source_table)
        _assert_no_secret_like_payload(source_table)
        _assert_no_verified_marker(source_table)

    fact_document_id = _string_or_empty(official_fact.get("source_document_id"))
    document_id = _string_or_empty(source_document.get("source_document_id"))
    if not fact_document_id or fact_document_id != document_id:
        raise OfficialDisclosureCandidateConflictError("official fact source_document_id does not match source document")

    fact_table_id = _string_or_empty(official_fact.get("source_table_id"))
    if fact_table_id:
        if source_table is None:
            raise OfficialDisclosureCandidateConflictError("table fact is missing source table trace")
        table_id = _string_or_empty(source_table.get("source_table_id"))
        table_document_id = _string_or_empty(source_table.get("source_document_id"))
        if fact_table_id != table_id or table_document_id != document_id:
            raise OfficialDisclosureCandidateConflictError("table fact source lineage mismatch")

    needs_human_review = official_fact.get("needs_human_review")
    if not isinstance(needs_human_review, bool):
        raise OfficialDisclosureCandidateValidationError("needs_human_review must be a bool")

    row = {
        "candidate_id": _string_or_empty(candidate_id) or _build_candidate_id(official_fact),
        "field_path": _string_or_empty(official_fact.get("field_path")),
        "value": copy.deepcopy(official_fact.get("value")),
        "unit": _first_string(official_fact.get("unit"), (source_table or {}).get("detected_unit")),
        "period": _first_string(
            official_fact.get("period"),
            (source_table or {}).get("detected_period"),
            source_document.get("report_period"),
        ),
        "source_type": OFFICIAL_DISCLOSURE_SOURCE_TYPE,
        "evidence_tier": OFFICIAL_DISCLOSURE_EVIDENCE_TIER,
        "source_document_id": document_id,
        "source_section": _first_string(official_fact.get("source_section"), (source_table or {}).get("source_section")),
        "source_page_or_anchor": _string_or_empty(official_fact.get("source_page_or_anchor")),
        "source_table_id": fact_table_id,
        "source_row_index": copy.deepcopy(official_fact.get("source_row_index")) if fact_table_id else None,
        "source_column_name": _string_or_empty(official_fact.get("source_column_name")) if fact_table_id else "",
        "source_column_map": copy.deepcopy(official_fact.get("source_column_map") or {}) if fact_table_id else {},
        "classification_type": _string_or_empty(official_fact.get("classification_type")),
        "segment_name": _string_or_empty(official_fact.get("segment_name")),
        "denominator": _string_or_empty(official_fact.get("denominator")),
        "table_quality": _first_string(official_fact.get("table_quality"), (source_table or {}).get("table_quality_final")),
        "extraction_confidence": _string_or_empty(official_fact.get("extraction_confidence")),
        "needs_human_review": needs_human_review,
        "caveats": _unique_strings(
            list(official_fact.get("caveats") or [])
            + list(source_document.get("caveats") or [])
            + list((source_table or {}).get("caveats") or [])
        ),
        "review_status": "",
        "not_for_trading_advice": True,
    }
    row["review_status"] = determine_official_candidate_review_status(row)
    validate_official_disclosure_candidate_row(row)
    return row


def determine_official_candidate_review_status(candidate_row: dict) -> str:
    """Return the V1 review status for one official disclosure candidate row."""

    if not isinstance(candidate_row, dict):
        raise OfficialDisclosureCandidateValidationError("candidate row must be a dict")
    if _table_quality(candidate_row) in CAVEAT_ONLY_TABLE_QUALITIES:
        raise OfficialDisclosureCandidateValidationError("caveat-only table quality cannot emit fact candidates")
    if _is_missing_value(candidate_row.get("value")):
        return "unsupported_or_missing"
    if _is_table_numeric_candidate(candidate_row) and (
        not _string_or_empty(candidate_row.get("unit"))
        or not _string_or_empty(candidate_row.get("period"))
        or not _string_or_empty(candidate_row.get("denominator"))
    ):
        return "blocked_by_caveat"
    if _table_quality(candidate_row) == "structured_medium":
        return "manual_review_required"
    if _has_human_review_caveat(candidate_row):
        return "manual_review_required"
    if candidate_row.get("needs_human_review") is True:
        return "manual_review_required"
    return "auto_candidate"


def convert_official_disclosure_facts_to_candidate_rows(
    official_payload: dict,
) -> dict:
    """Convert an official disclosure facts payload to official candidate rows."""

    _validate_official_payload_for_conversion(official_payload)
    source_documents = _source_document_index(official_payload)
    source_tables = _source_table_index(official_payload)
    candidate_rows: list[dict] = []
    candidate_caveats = copy.deepcopy(official_payload.get("table_caveats") or [])
    candidate_caveats.extend(copy.deepcopy(official_payload.get("data_quality_caveats") or []))
    integration_warnings = copy.deepcopy(official_payload.get("table_conversion_warnings") or [])
    integration_warnings.extend(copy.deepcopy(official_payload.get("extraction_warnings") or []))

    for official_fact in official_payload.get("extracted_facts", []):
        if _fact_has_caveat_only_table_quality(official_fact):
            candidate_caveats.append(_fact_caveat("caveat_only_table_quality", official_fact))
            continue
        if _is_table_fact(official_fact) and not _is_supported_v1_table_fact(official_fact):
            candidate_caveats.append(_fact_caveat("deferred_table_fact_type", official_fact))
            continue

        source_document_id = _string_or_empty(official_fact.get("source_document_id"))
        source_document = source_documents.get(source_document_id)
        if source_document is None:
            raise OfficialDisclosureCandidateConflictError("official fact references unknown source_document_id")

        source_table = None
        if _is_table_fact(official_fact):
            source_table_id = _string_or_empty(official_fact.get("source_table_id"))
            if not source_table_id:
                raise OfficialDisclosureCandidateConflictError("table fact is missing source_table_id")
            source_table = source_tables.get(source_table_id)
            if source_table is None:
                raise OfficialDisclosureCandidateConflictError("table fact references unknown source_table_id")
            if _string_or_empty(source_table.get("source_document_id")) != source_document_id:
                raise OfficialDisclosureCandidateConflictError("table fact source lineage mismatch")

        candidate_rows.append(
            build_official_disclosure_candidate_row(
                official_fact=official_fact,
                source_document=source_document,
                source_table=source_table,
            )
        )

    payload = {
        "version": OFFICIAL_DISCLOSURE_CANDIDATE_VERSION,
        "code": official_payload.get("code", ""),
        "company_name": official_payload.get("company_name", ""),
        "source_type": OFFICIAL_DISCLOSURE_SOURCE_TYPE,
        "candidate_rows": candidate_rows,
        "candidate_caveats": candidate_caveats,
        "integration_warnings": integration_warnings,
        "not_for_trading_advice": True,
    }
    validate_official_disclosure_candidate_payload(payload)
    return payload


def validate_official_disclosure_candidate_row(row: dict) -> None:
    """Validate one official disclosure candidate row."""

    if not isinstance(row, dict):
        raise OfficialDisclosureCandidateValidationError("candidate row must be a dict")
    missing = REQUIRED_CANDIDATE_ROW_KEYS - set(row)
    if missing:
        raise OfficialDisclosureCandidateValidationError("candidate row missing required keys")
    _assert_no_forbidden_recommendation_keys(row)
    _assert_no_secret_like_payload(row)
    _assert_no_verified_marker(row)
    if row.get("not_for_trading_advice") is not True:
        raise OfficialDisclosureCandidateValidationError("not_for_trading_advice must be true")
    if row.get("source_type") != OFFICIAL_DISCLOSURE_SOURCE_TYPE:
        raise OfficialDisclosureCandidateValidationError("source_type must be official_disclosure")
    if row.get("evidence_tier") != OFFICIAL_DISCLOSURE_EVIDENCE_TIER:
        raise OfficialDisclosureCandidateValidationError("evidence_tier must be L1_official_disclosure")
    if not _non_empty_string(row.get("candidate_id")):
        raise OfficialDisclosureCandidateValidationError("candidate_id must be non-empty")
    if not _non_empty_string(row.get("field_path")):
        raise OfficialDisclosureCandidateValidationError("field_path must be non-empty")
    if not _non_empty_string(row.get("source_document_id")):
        raise OfficialDisclosureCandidateValidationError("source_document_id must be non-empty")
    if not isinstance(row.get("needs_human_review"), bool):
        raise OfficialDisclosureCandidateValidationError("needs_human_review must be a bool")
    if row.get("review_status") not in REVIEW_STATUS_VALUES:
        raise OfficialDisclosureCandidateValidationError("review_status is unsupported")
    if not isinstance(row.get("caveats"), list) or not all(isinstance(item, str) for item in row["caveats"]):
        raise OfficialDisclosureCandidateValidationError("caveats must be a list of strings")
    if row.get("source_table_id"):
        if not isinstance(row.get("source_row_index"), int) or isinstance(row.get("source_row_index"), bool):
            raise OfficialDisclosureCandidateValidationError("table candidate source_row_index must be an integer")
        if not _non_empty_string(row.get("source_column_name")):
            raise OfficialDisclosureCandidateValidationError("table candidate source_column_name must be non-empty")
        if not isinstance(row.get("source_column_map"), dict):
            raise OfficialDisclosureCandidateValidationError("table candidate source_column_map must be a dict")
    elif not (_string_or_empty(row.get("source_section")) or _string_or_empty(row.get("source_page_or_anchor"))):
        raise OfficialDisclosureCandidateValidationError("text candidate requires source section or anchor")


def validate_official_disclosure_candidate_payload(payload: dict) -> None:
    """Validate an official disclosure candidate payload."""

    if not isinstance(payload, dict):
        raise OfficialDisclosureCandidateValidationError("candidate payload must be a dict")
    if payload.get("version") != OFFICIAL_DISCLOSURE_CANDIDATE_VERSION:
        raise OfficialDisclosureCandidateValidationError("candidate payload version is unsupported")
    if payload.get("source_type") != OFFICIAL_DISCLOSURE_SOURCE_TYPE:
        raise OfficialDisclosureCandidateValidationError("candidate payload source_type must be official_disclosure")
    if payload.get("not_for_trading_advice") is not True:
        raise OfficialDisclosureCandidateValidationError("not_for_trading_advice must be true")
    if not isinstance(payload.get("code"), str) or not payload["code"]:
        raise OfficialDisclosureCandidateValidationError("code must be a non-empty string")
    if not isinstance(payload.get("company_name"), str) or not payload["company_name"]:
        raise OfficialDisclosureCandidateValidationError("company_name must be a non-empty string")
    if not isinstance(payload.get("candidate_rows"), list):
        raise OfficialDisclosureCandidateValidationError("candidate_rows must be a list")
    if not isinstance(payload.get("candidate_caveats"), list):
        raise OfficialDisclosureCandidateValidationError("candidate_caveats must be a list")
    if not isinstance(payload.get("integration_warnings"), list):
        raise OfficialDisclosureCandidateValidationError("integration_warnings must be a list")
    _assert_no_forbidden_recommendation_keys(payload)
    _assert_no_secret_like_payload(payload)
    _assert_no_verified_marker(payload)
    seen_candidate_ids: set[str] = set()
    for row in payload["candidate_rows"]:
        validate_official_disclosure_candidate_row(row)
        candidate_id = row["candidate_id"]
        if candidate_id in seen_candidate_ids:
            raise OfficialDisclosureCandidateValidationError("duplicate candidate_id")
        seen_candidate_ids.add(candidate_id)


def _validate_official_payload_for_conversion(official_payload: dict) -> None:
    try:
        validate_official_disclosure_facts(official_payload)
    except OfficialDisclosureSecretError as exc:
        raise OfficialDisclosureCandidateSecretError("official disclosure payload contains secret-like data: <masked>") from exc
    except OfficialDisclosureValidationError as exc:
        raise OfficialDisclosureCandidateValidationError(str(exc)) from exc
    _assert_no_forbidden_recommendation_keys(official_payload)
    _assert_no_secret_like_payload(official_payload)
    _assert_no_verified_marker(official_payload)


def _source_document_index(official_payload: dict) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for source_document in official_payload.get("source_documents", []):
        source_document_id = _string_or_empty(source_document.get("source_document_id"))
        if not source_document_id:
            raise OfficialDisclosureCandidateValidationError("source document missing source_document_id")
        if source_document_id in index:
            raise OfficialDisclosureCandidateConflictError("duplicate source_document_id")
        index[source_document_id] = source_document
    return index


def _source_table_index(official_payload: dict) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for source_table in official_payload.get("source_tables", []) or []:
        if not isinstance(source_table, dict):
            raise OfficialDisclosureCandidateValidationError("source table must be a dict")
        source_table_id = _string_or_empty(source_table.get("source_table_id"))
        source_document_id = _string_or_empty(source_table.get("source_document_id"))
        if not source_table_id or not source_document_id:
            raise OfficialDisclosureCandidateValidationError("source table trace is missing lineage")
        if source_table_id in index:
            raise OfficialDisclosureCandidateConflictError("duplicate source_table_id")
        index[source_table_id] = source_table
    return index


def _is_table_fact(fact: dict) -> bool:
    return any(
        key in fact
        for key in (
            "source_table_id",
            "source_row_index",
            "source_column_name",
            "source_column_map",
            "classification_type",
            "segment_name",
            "denominator",
            "table_quality",
        )
    )


def _is_supported_v1_table_fact(fact: dict) -> bool:
    field_path = _string_or_empty(fact.get("field_path")).lower()
    return field_path.endswith(V1_TABLE_REVENUE_FIELD_SUFFIX) or field_path == "business_composition.revenue"


def _fact_has_caveat_only_table_quality(fact: dict) -> bool:
    return _string_or_empty(fact.get("table_quality")).lower() in CAVEAT_ONLY_TABLE_QUALITIES


def _is_table_numeric_candidate(row: dict) -> bool:
    if not _string_or_empty(row.get("source_table_id")):
        return False
    field_path = _string_or_empty(row.get("field_path")).lower()
    return field_path.endswith(".revenue") or any(
        token in field_path
        for token in (
            "cost",
            "gross_margin",
            "yoy",
            "year_on_year",
            "revenue_ratio",
        )
    )


def _table_quality(row: dict) -> str:
    return _string_or_empty(row.get("table_quality")).lower()


def _has_human_review_caveat(row: dict) -> bool:
    caveats = row.get("caveats") or []
    return any(isinstance(caveat, str) and "human_review" in caveat.lower() for caveat in caveats)


def _is_missing_value(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _fact_caveat(reason: str, fact: dict) -> dict[str, str]:
    return {
        "reason": reason,
        "fact_id": _string_or_empty(fact.get("fact_id")),
        "field_path": _string_or_empty(fact.get("field_path")),
        "source_document_id": _string_or_empty(fact.get("source_document_id")),
        "source_table_id": _string_or_empty(fact.get("source_table_id")),
    }


def _build_candidate_id(official_fact: dict) -> str:
    parts = [
        OFFICIAL_DISCLOSURE_SOURCE_TYPE,
        _string_or_empty(official_fact.get("source_document_id")),
        _string_or_empty(official_fact.get("fact_id")) or _string_or_empty(official_fact.get("field_path")),
        _string_or_empty(official_fact.get("period")),
        _string_or_empty(official_fact.get("source_table_id")),
        _string_or_empty(official_fact.get("source_row_index")),
        _string_or_empty(official_fact.get("source_column_name")),
    ]
    return ":".join(_candidate_id_part(part) for part in parts if part)


def _candidate_id_part(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value).strip())
    return normalized.strip("_") or "empty"


def _first_string(*values: Any) -> str:
    for value in values:
        text = _string_or_empty(value)
        if text:
            return text
    return ""


def _string_or_empty(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return ""


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _unique_strings(values: list[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        if value in seen:
            continue
        result.append(value)
        seen.add(value)
    return result


def _assert_no_forbidden_recommendation_keys(payload: Any) -> None:
    for key in _walk_keys(payload):
        if str(key).lower() in FORBIDDEN_RECOMMENDATION_KEYS:
            raise OfficialDisclosureCandidateValidationError(
                "official disclosure candidate payload contains forbidden recommendation keys"
            )


def _assert_no_verified_marker(payload: Any) -> None:
    finding = _first_verified_marker(payload, "$")
    if finding:
        raise OfficialDisclosureCandidateValidationError("official disclosure candidate payload contains verified marker")


def _first_verified_marker(value: Any, path: str) -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).lower()
            if lowered == "verified_fact":
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


def _assert_no_secret_like_payload(payload: Any) -> None:
    finding = _first_secret_like_finding(payload, "$")
    if finding:
        raise OfficialDisclosureCandidateSecretError(
            f"official disclosure candidate payload contains secret-like data at {finding}: <masked>"
        )


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


def _secret_string_finding(value: str, path: str) -> str | None:
    if (
        _SECRET_KEY_RE.search(value)
        or _KEYED_SECRET_RE.search(value)
        or _BEARER_RE.search(value)
        or _REMOTE_CONTROL_RE.search(value)
        or _DOTFILE_CONFIG_RE.search(value)
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


def _safe_path_key(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", value)[:64] or "<key>"
