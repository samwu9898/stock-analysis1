# -*- coding: utf-8 -*-
"""In-memory assembly for table facts inside official disclosure facts."""

from __future__ import annotations

import copy
import re
from typing import Any

from .business_composition_table import (
    BusinessCompositionTableSecretError,
    BusinessCompositionTableValidationError,
    TABLE_QUALITY_VALUES,
    get_table_quality_policy,
    validate_table_caveat,
    validate_table_fact,
)
from .official_disclosure_parser import (
    OfficialDisclosureSecretError,
    OfficialDisclosureValidationError,
    validate_official_disclosure_facts,
)


DEFAULT_TABLE_FACT_NAMESPACE = "business_composition"
TABLE_CONVERSION_WARNINGS_KEY = "table_conversion_warnings"
LOCAL_STRUCTURED_REVIEW_CAVEAT = "local_structured_sample_requires_human_review"

FORBIDDEN_RECOMMENDATION_KEYS = {
    "buy",
    "sell",
    "target_price",
    "position",
    "portfolio_weight",
}

SOURCE_TABLE_REQUIRED_FIELDS = {
    "source_table_id",
    "source_document_id",
    "source_format",
    "source_file_path",
    "source_section",
    "table_title",
    "headers",
    "row_count",
    "column_count",
    "detected_unit",
    "detected_period",
    "classification_hint",
    "reader_warnings",
    "table_quality_hint",
    "table_quality_final",
    "caveats",
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


class OfficialDisclosureTableIntegrationError(RuntimeError):
    """Base error for table fact integration."""


class OfficialDisclosureTableIntegrationValidationError(OfficialDisclosureTableIntegrationError):
    """Raised when integration input or output fails validation."""


class OfficialDisclosureTableIntegrationCollisionError(OfficialDisclosureTableIntegrationValidationError):
    """Raised when ids collide or source table traces conflict."""


class OfficialDisclosureTableIntegrationSecretError(OfficialDisclosureTableIntegrationError):
    """Raised when integration data contains secret-like material."""


def integrate_table_facts_into_official_disclosure_facts(
    official_payload: dict,
    *,
    table_facts: list[dict],
    table_caveats: list[dict] | None = None,
    conversion_warnings: list[dict] | None = None,
    source_tables: list[dict] | None = None,
) -> dict:
    """Append table facts and table trace to a new in-memory payload."""

    _validate_base_official_payload(official_payload)
    _require_list("table_facts", table_facts)
    _require_optional_list("table_caveats", table_caveats)
    _require_optional_list("conversion_warnings", conversion_warnings)
    _require_optional_list("source_tables", source_tables)
    _assert_no_forbidden_recommendation_keys(
        {
            "table_facts": table_facts,
            "table_caveats": table_caveats or [],
            "conversion_warnings": conversion_warnings or [],
            "source_tables": source_tables or [],
        }
    )
    _assert_no_secret_like_payload(
        {
            "table_facts": table_facts,
            "table_caveats": table_caveats or [],
            "conversion_warnings": conversion_warnings or [],
            "source_tables": source_tables or [],
        }
    )

    payload = copy.deepcopy(official_payload)
    payload.setdefault("source_tables", [])
    payload.setdefault("table_caveats", [])
    payload.setdefault(TABLE_CONVERSION_WARNINGS_KEY, [])
    _require_list("source_tables", payload["source_tables"])
    _require_list("table_caveats", payload["table_caveats"])
    _require_list(TABLE_CONVERSION_WARNINGS_KEY, payload[TABLE_CONVERSION_WARNINGS_KEY])

    valid_document_ids = _source_document_ids(payload)
    existing_fact_ids = _existing_fact_ids(payload)
    source_table_index = _source_table_index(payload["source_tables"], valid_document_ids=valid_document_ids)

    incoming_source_tables = copy.deepcopy(source_tables or [])
    for source_table in incoming_source_tables:
        validate_source_table_trace(source_table, valid_document_ids=valid_document_ids)
        source_table_id = source_table["source_table_id"]
        if source_table_id in source_table_index:
            if _canonical_trace(source_table_index[source_table_id]) != _canonical_trace(source_table):
                raise OfficialDisclosureTableIntegrationCollisionError("source_table_id trace conflict")
            continue
        payload["source_tables"].append(source_table)
        source_table_index[source_table_id] = source_table

    incoming_facts = copy.deepcopy(table_facts)
    _validate_table_facts_for_integration(
        incoming_facts,
        valid_document_ids=valid_document_ids,
        existing_fact_ids=existing_fact_ids,
        source_table_ids=set(source_table_index),
    )

    default_source_table_id, default_source_document_id = _single_source_table_defaults(incoming_facts, incoming_source_tables)
    payload["table_caveats"].extend(
        _normalized_table_caveats(
            table_caveats or [],
            valid_document_ids=valid_document_ids,
            default_source_table_id=default_source_table_id,
            default_source_document_id=default_source_document_id,
        )
    )
    payload[TABLE_CONVERSION_WARNINGS_KEY].extend(
        _normalized_conversion_warnings(
            conversion_warnings or [],
            valid_document_ids=valid_document_ids,
            default_source_table_id=default_source_table_id,
            default_source_document_id=default_source_document_id,
        )
    )
    payload["extracted_facts"].extend(incoming_facts)

    validate_official_disclosure_table_integration_payload(payload)
    return payload


def validate_official_disclosure_table_integration_payload(payload: dict) -> None:
    """Validate an integrated official disclosure table payload."""

    _validate_base_official_payload(payload)
    _assert_no_forbidden_recommendation_keys(payload)
    _assert_no_secret_like_payload(payload)
    _assert_no_verified_marker(payload)

    if "source_tables" in payload:
        _require_list("source_tables", payload["source_tables"])
    if "table_caveats" in payload:
        _require_list("table_caveats", payload["table_caveats"])
    if TABLE_CONVERSION_WARNINGS_KEY in payload:
        _require_list(TABLE_CONVERSION_WARNINGS_KEY, payload[TABLE_CONVERSION_WARNINGS_KEY])

    valid_document_ids = _source_document_ids(payload)
    source_table_index = _source_table_index(payload.get("source_tables", []), valid_document_ids=valid_document_ids)
    for fact in payload.get("extracted_facts", []):
        if _is_table_fact(fact):
            _validate_one_table_fact_for_integration(
                fact,
                valid_document_ids=valid_document_ids,
                source_table_ids=set(source_table_index),
            )
    for caveat in payload.get("table_caveats", []):
        _validate_table_caveat_for_integration(caveat, valid_document_ids=valid_document_ids)
    for warning in payload.get(TABLE_CONVERSION_WARNINGS_KEY, []):
        _validate_warning_for_integration(warning, valid_document_ids=valid_document_ids)


def validate_source_table_trace(source_table: dict, *, valid_document_ids: set[str]) -> None:
    """Validate one source table trace record."""

    if not isinstance(source_table, dict):
        raise OfficialDisclosureTableIntegrationValidationError("source table trace must be a dict")
    _assert_no_forbidden_recommendation_keys(source_table)
    _assert_no_secret_like_payload(source_table)
    missing = SOURCE_TABLE_REQUIRED_FIELDS - set(source_table)
    if missing:
        raise OfficialDisclosureTableIntegrationValidationError("source table trace missing required fields")
    if not _non_empty_string(source_table["source_table_id"]):
        raise OfficialDisclosureTableIntegrationValidationError("source_table_id must be non-empty")
    if source_table["source_document_id"] not in valid_document_ids:
        raise OfficialDisclosureTableIntegrationValidationError("source table references unknown source_document_id")
    if not _non_empty_string(source_table["source_format"]):
        raise OfficialDisclosureTableIntegrationValidationError("source_format must be non-empty")
    for key in (
        "source_file_path",
        "source_section",
        "table_title",
        "detected_unit",
        "detected_period",
        "classification_hint",
        "table_quality_hint",
        "table_quality_final",
    ):
        if not isinstance(source_table[key], str):
            raise OfficialDisclosureTableIntegrationValidationError(f"{key} must be a string")
    if source_table["table_quality_hint"] and source_table["table_quality_hint"] not in TABLE_QUALITY_VALUES:
        raise OfficialDisclosureTableIntegrationValidationError("invalid_table_quality_hint")
    if source_table["table_quality_final"] and source_table["table_quality_final"] not in TABLE_QUALITY_VALUES:
        raise OfficialDisclosureTableIntegrationValidationError("invalid_table_quality_final")
    if "source_hash" in source_table and not isinstance(source_table["source_hash"], str):
        raise OfficialDisclosureTableIntegrationValidationError("source_hash must be a string")
    if not isinstance(source_table["headers"], list) or not all(isinstance(item, str) for item in source_table["headers"]):
        raise OfficialDisclosureTableIntegrationValidationError("headers must be a list of strings")
    for key in ("row_count", "column_count"):
        if not isinstance(source_table[key], int) or isinstance(source_table[key], bool) or source_table[key] < 0:
            raise OfficialDisclosureTableIntegrationValidationError(f"{key} must be a non-negative integer")
    if not isinstance(source_table["reader_warnings"], list):
        raise OfficialDisclosureTableIntegrationValidationError("reader_warnings must be a list")
    if not isinstance(source_table["caveats"], list):
        raise OfficialDisclosureTableIntegrationValidationError("caveats must be a list")
    if "rows" in source_table and not isinstance(source_table["rows"], list):
        raise OfficialDisclosureTableIntegrationValidationError("rows must be a list when present")


def _validate_base_official_payload(payload: dict) -> None:
    try:
        validate_official_disclosure_facts(payload)
    except OfficialDisclosureSecretError as exc:
        raise OfficialDisclosureTableIntegrationSecretError("official disclosure payload contains secret-like data: <masked>") from exc
    except OfficialDisclosureValidationError as exc:
        raise OfficialDisclosureTableIntegrationValidationError("official disclosure payload is invalid") from exc


def _validate_table_facts_for_integration(
    table_facts: list[dict],
    *,
    valid_document_ids: set[str],
    existing_fact_ids: set[str],
    source_table_ids: set[str],
) -> None:
    seen_new_fact_ids: set[str] = set()
    for fact in table_facts:
        _validate_one_table_fact_for_integration(
            fact,
            valid_document_ids=valid_document_ids,
            source_table_ids=source_table_ids,
        )
        fact_id = fact["fact_id"]
        if fact_id in existing_fact_ids or fact_id in seen_new_fact_ids:
            raise OfficialDisclosureTableIntegrationCollisionError("fact_id collision")
        seen_new_fact_ids.add(fact_id)


def _validate_one_table_fact_for_integration(
    fact: dict,
    *,
    valid_document_ids: set[str],
    source_table_ids: set[str],
) -> None:
    if not isinstance(fact, dict):
        raise OfficialDisclosureTableIntegrationValidationError("table fact must be a dict")
    _assert_no_forbidden_recommendation_keys(fact)
    _assert_no_secret_like_payload(fact)
    _assert_no_verified_marker(fact)
    try:
        validate_table_fact(fact)
    except BusinessCompositionTableSecretError as exc:
        raise OfficialDisclosureTableIntegrationSecretError("table fact contains secret-like data: <masked>") from exc
    except BusinessCompositionTableValidationError as exc:
        raise OfficialDisclosureTableIntegrationValidationError("table fact is invalid") from exc

    if fact["source_document_id"] not in valid_document_ids:
        raise OfficialDisclosureTableIntegrationValidationError("table fact references unknown source_document_id")
    if fact["source_table_id"] not in source_table_ids:
        raise OfficialDisclosureTableIntegrationValidationError("table fact references unknown source_table_id")
    if not fact["field_path"].startswith(f"{DEFAULT_TABLE_FACT_NAMESPACE}."):
        raise OfficialDisclosureTableIntegrationValidationError("table fact field_path is outside allowed namespace")
    if fact["evidence_tier"] != "L1_official_disclosure":
        raise OfficialDisclosureTableIntegrationValidationError("table fact evidence_tier must remain L1 candidate")
    if fact["needs_human_review"] is not True:
        raise OfficialDisclosureTableIntegrationValidationError("table fact must require human review")
    if LOCAL_STRUCTURED_REVIEW_CAVEAT not in fact["caveats"]:
        raise OfficialDisclosureTableIntegrationValidationError("table fact must retain local structured review caveat")
    policy = get_table_quality_policy(fact["table_quality"])
    if policy["caveat_only"]:
        raise OfficialDisclosureTableIntegrationValidationError("caveat-only table quality cannot append facts")


def _validate_table_caveat_for_integration(caveat: dict, *, valid_document_ids: set[str]) -> None:
    if not isinstance(caveat, dict):
        raise OfficialDisclosureTableIntegrationValidationError("table caveat must be a dict")
    _assert_no_forbidden_recommendation_keys(caveat)
    _assert_no_secret_like_payload(caveat)
    if {"reason", "table_quality", "source_section", "can_extract_numeric_values", "requires_human_review", "caveat_only", "blocked_numeric_extraction"} <= set(caveat):
        try:
            validate_table_caveat(caveat)
        except BusinessCompositionTableSecretError as exc:
            raise OfficialDisclosureTableIntegrationSecretError("table caveat contains secret-like data: <masked>") from exc
        except BusinessCompositionTableValidationError as exc:
            raise OfficialDisclosureTableIntegrationValidationError("table caveat is invalid") from exc
    elif not _non_empty_string(caveat.get("reason")):
        raise OfficialDisclosureTableIntegrationValidationError("table caveat reason must be non-empty")
    _validate_optional_trace_refs(caveat, valid_document_ids=valid_document_ids)


def _validate_warning_for_integration(warning: dict, *, valid_document_ids: set[str]) -> None:
    if not isinstance(warning, dict):
        raise OfficialDisclosureTableIntegrationValidationError("conversion warning must be a dict")
    _assert_no_forbidden_recommendation_keys(warning)
    _assert_no_secret_like_payload(warning)
    if not _non_empty_string(warning.get("reason")):
        raise OfficialDisclosureTableIntegrationValidationError("conversion warning reason must be non-empty")
    if "detail" in warning and not isinstance(warning["detail"], str):
        raise OfficialDisclosureTableIntegrationValidationError("conversion warning detail must be a string")
    _validate_optional_trace_refs(warning, valid_document_ids=valid_document_ids)


def _validate_optional_trace_refs(item: dict, *, valid_document_ids: set[str]) -> None:
    if "source_document_id" in item and item["source_document_id"] not in valid_document_ids:
        raise OfficialDisclosureTableIntegrationValidationError("trace item references unknown source_document_id")
    if "source_table_id" in item and not _non_empty_string(item["source_table_id"]):
        raise OfficialDisclosureTableIntegrationValidationError("trace item source_table_id must be non-empty")


def _source_document_ids(payload: dict) -> set[str]:
    return {doc["source_document_id"] for doc in payload["source_documents"]}


def _existing_fact_ids(payload: dict) -> set[str]:
    return {fact["fact_id"] for fact in payload["extracted_facts"]}


def _source_table_index(source_tables: list[dict], *, valid_document_ids: set[str]) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for source_table in source_tables:
        validate_source_table_trace(source_table, valid_document_ids=valid_document_ids)
        source_table_id = source_table["source_table_id"]
        if source_table_id in index and _canonical_trace(index[source_table_id]) != _canonical_trace(source_table):
            raise OfficialDisclosureTableIntegrationCollisionError("source_table_id trace conflict")
        if source_table_id in index:
            continue
        index[source_table_id] = source_table
    return index


def _normalized_table_caveats(
    caveats: list[dict],
    *,
    valid_document_ids: set[str],
    default_source_table_id: str | None,
    default_source_document_id: str | None,
) -> list[dict]:
    normalized = []
    for caveat in copy.deepcopy(caveats):
        _attach_default_trace(caveat, default_source_table_id, default_source_document_id)
        _validate_table_caveat_for_integration(caveat, valid_document_ids=valid_document_ids)
        normalized.append(caveat)
    return normalized


def _normalized_conversion_warnings(
    warnings: list[dict],
    *,
    valid_document_ids: set[str],
    default_source_table_id: str | None,
    default_source_document_id: str | None,
) -> list[dict]:
    normalized = []
    for warning in copy.deepcopy(warnings):
        if isinstance(warning, str):
            warning = {"reason": warning, "detail": ""}
        _attach_default_trace(warning, default_source_table_id, default_source_document_id)
        _validate_warning_for_integration(warning, valid_document_ids=valid_document_ids)
        normalized.append(warning)
    return normalized


def _attach_default_trace(item: dict, source_table_id: str | None, source_document_id: str | None) -> None:
    if not isinstance(item, dict):
        raise OfficialDisclosureTableIntegrationValidationError("trace item must be a dict")
    if source_table_id and "source_table_id" not in item:
        item["source_table_id"] = source_table_id
    if source_document_id and "source_document_id" not in item:
        item["source_document_id"] = source_document_id


def _single_source_table_defaults(
    table_facts: list[dict],
    source_tables: list[dict],
) -> tuple[str | None, str | None]:
    table_ids = {fact.get("source_table_id") for fact in table_facts if isinstance(fact, dict) and _non_empty_string(fact.get("source_table_id"))}
    doc_ids = {fact.get("source_document_id") for fact in table_facts if isinstance(fact, dict) and _non_empty_string(fact.get("source_document_id"))}
    if not table_ids and len(source_tables) == 1:
        table_ids.add(source_tables[0].get("source_table_id"))
    if not doc_ids and len(source_tables) == 1:
        doc_ids.add(source_tables[0].get("source_document_id"))
    table_id = next(iter(table_ids)) if len(table_ids) == 1 else None
    doc_id = next(iter(doc_ids)) if len(doc_ids) == 1 else None
    return table_id, doc_id


def _is_table_fact(fact: Any) -> bool:
    return isinstance(fact, dict) and "source_table_id" in fact


def _canonical_trace(value: dict) -> tuple:
    return _freeze(value)


def _freeze(value: Any):
    if isinstance(value, dict):
        return tuple(sorted((str(key), _freeze(child)) for key, child in value.items()))
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _assert_no_verified_marker(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered_key = str(key).lower()
            if lowered_key == "verified_fact":
                raise OfficialDisclosureTableIntegrationValidationError("verified fact marker is not allowed")
            if lowered_key == "review_status" and isinstance(child, str) and child.lower() == "verified":
                raise OfficialDisclosureTableIntegrationValidationError("verified fact marker is not allowed")
            _assert_no_verified_marker(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_verified_marker(child)


def _assert_no_forbidden_recommendation_keys(payload: Any) -> None:
    for key in _walk_keys(payload):
        if str(key).lower() in FORBIDDEN_RECOMMENDATION_KEYS:
            raise OfficialDisclosureTableIntegrationValidationError("payload contains forbidden recommendation keys")


def _assert_no_secret_like_payload(payload: Any) -> None:
    finding = _first_secret_like_finding(payload, "$")
    if finding:
        raise OfficialDisclosureTableIntegrationSecretError(f"payload contains secret-like data at {finding}: <masked>")


def _first_secret_like_finding(value: Any, path: str) -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{_safe_path_key(str(key))}"
            key_finding = _first_secret_like_finding(str(key), f"{child_path}.__key__")
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
        if (
            _SECRET_KEY_RE.search(value)
            or _KEYED_SECRET_RE.search(value)
            or _BEARER_RE.search(value)
            or _REMOTE_CONTROL_RE.search(value)
            or _DOTFILE_CONFIG_RE.search(value)
            or _LOCAL_SECRET_PATH_RE.search(value)
            or _TOKEN_LIKE_RE.fullmatch(value.strip())
        ):
            return path
        if _TOKEN_LIKE_RE.search(value) and _SECRET_KEY_RE.search(value[:160]):
            return path
    return None


def _safe_path_key(key: str) -> str:
    if _SECRET_KEY_RE.search(key) or _TOKEN_LIKE_RE.search(key) or _DOTFILE_CONFIG_RE.search(key):
        return "<masked_key>"
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,63}", key):
        return key
    return "<key>"


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _require_list(name: str, value: Any) -> None:
    if not isinstance(value, list):
        raise OfficialDisclosureTableIntegrationValidationError(f"{name} must be a list")


def _require_optional_list(name: str, value: Any) -> None:
    if value is not None and not isinstance(value, list):
        raise OfficialDisclosureTableIntegrationValidationError(f"{name} must be a list")


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
