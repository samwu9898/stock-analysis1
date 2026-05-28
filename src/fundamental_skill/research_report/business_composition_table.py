# -*- coding: utf-8 -*-
"""Business composition table fact schema and quality policy.

This module is intentionally in-memory only. It does not read source files,
write output, or connect to runtime data services.
"""

from __future__ import annotations

import copy
import re
from datetime import datetime, timezone
from typing import Any


BUSINESS_COMPOSITION_TABLE_FACT_VERSION = "business_composition_table_facts.v1"

TABLE_QUALITY_VALUES = {
    "structured_high",
    "structured_medium",
    "partially_structured",
    "unreliable_text_copy",
    "unusable",
}

CLASSIFICATION_TYPE_VALUES = {"industry", "product", "region", "other"}

EVIDENCE_TIER_VALUES = {
    "L1_official_disclosure",
    "L2_multi_source_consistent",
    "L3_single_source_candidate",
    "L4_unsupported_or_missing",
}

EXTRACTION_CONFIDENCE_VALUES = {"high", "medium", "low"}

FORBIDDEN_RECOMMENDATION_KEYS = {
    "buy",
    "sell",
    "target_price",
    "position",
    "portfolio_weight",
}

BUSINESS_COMPOSITION_SECTION_DETECTED = "business_composition_section_detected"
TABLE_STRUCTURE_UNRELIABLE_DUE_TO_PDF_TEXT_COPY = "table_structure_unreliable_due_to_pdf_text_copy"
BUSINESS_COMPOSITION_TABLE_UNUSABLE = "business_composition_table_unusable"

TABLE_FACT_REQUIRED_FIELDS = {
    "fact_id",
    "field_path",
    "value",
    "unit",
    "period",
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
    "evidence_tier",
    "extraction_confidence",
    "needs_human_review",
    "table_quality",
    "caveats",
}

_TABLE_QUALITY_POLICIES = {
    "structured_high": {
        "can_extract_numeric_values": True,
        "requires_human_review": False,
        "l1_candidate_eligible": True,
        "candidate_generator_eligible": True,
        "caveat_only": False,
        "requires_caveat": False,
        "limited_fields_only": False,
        "requires_accepted_policy": False,
    },
    "structured_medium": {
        "can_extract_numeric_values": True,
        "requires_human_review": True,
        "l1_candidate_eligible": True,
        "candidate_generator_eligible": True,
        "caveat_only": False,
        "requires_caveat": True,
        "limited_fields_only": False,
        "requires_accepted_policy": True,
    },
    "partially_structured": {
        "can_extract_numeric_values": True,
        "requires_human_review": True,
        "l1_candidate_eligible": False,
        "candidate_generator_eligible": False,
        "caveat_only": False,
        "requires_caveat": True,
        "limited_fields_only": True,
        "requires_accepted_policy": True,
    },
    "unreliable_text_copy": {
        "can_extract_numeric_values": False,
        "requires_human_review": True,
        "l1_candidate_eligible": False,
        "candidate_generator_eligible": False,
        "caveat_only": True,
        "requires_caveat": True,
        "limited_fields_only": False,
        "requires_accepted_policy": False,
    },
    "unusable": {
        "can_extract_numeric_values": False,
        "requires_human_review": True,
        "l1_candidate_eligible": False,
        "candidate_generator_eligible": False,
        "caveat_only": True,
        "requires_caveat": True,
        "limited_fields_only": False,
        "requires_accepted_policy": False,
    },
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
_NUMERIC_STRING_RE = re.compile(
    r"^\s*[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?\s*$"
)


class BusinessCompositionTableError(RuntimeError):
    """Base error for business composition table schema operations."""


class BusinessCompositionTableValidationError(BusinessCompositionTableError):
    """Raised when a table fact or payload fails schema validation."""


class BusinessCompositionTableQualityError(BusinessCompositionTableError):
    """Raised when table quality policy input is unsupported."""


class BusinessCompositionTableSecretError(BusinessCompositionTableError):
    """Raised when payload data contains secret-like material."""


def get_table_quality_policy(table_quality: str) -> dict:
    """Return fail-closed policy flags for a table quality value."""

    if table_quality not in TABLE_QUALITY_VALUES:
        raise BusinessCompositionTableQualityError("table_quality is unsupported")
    return copy.deepcopy(_TABLE_QUALITY_POLICIES[table_quality])


def is_numeric_extraction_allowed(table_quality: str) -> bool:
    """Return whether structured numeric extraction is allowed by quality."""

    return bool(get_table_quality_policy(table_quality)["can_extract_numeric_values"])


def build_table_fact(
    *,
    fact_id: str,
    field_path: str,
    value,
    unit: str | None,
    period: str,
    source_document_id: str,
    source_section: str,
    source_table_id: str,
    source_row_index: int,
    source_column_name: str,
    source_column_map: dict,
    classification_type: str,
    segment_name: str,
    denominator: str | None,
    evidence_tier: str,
    extraction_confidence: str,
    needs_human_review: bool,
    table_quality: str,
    caveats: list[str] | None = None,
    source_page_or_anchor: str = "",
) -> dict:
    """Build and validate one business composition table fact."""

    fact = {
        "fact_id": fact_id,
        "field_path": field_path,
        "value": copy.deepcopy(value),
        "unit": unit,
        "period": period,
        "source_document_id": source_document_id,
        "source_section": source_section,
        "source_page_or_anchor": source_page_or_anchor,
        "source_table_id": source_table_id,
        "source_row_index": source_row_index,
        "source_column_name": source_column_name,
        "source_column_map": copy.deepcopy(source_column_map),
        "classification_type": classification_type,
        "segment_name": segment_name,
        "denominator": denominator,
        "evidence_tier": evidence_tier,
        "extraction_confidence": extraction_confidence,
        "needs_human_review": needs_human_review,
        "table_quality": table_quality,
        "caveats": list(caveats or []),
    }
    validate_table_fact(fact)
    return fact


def validate_table_fact(fact: dict) -> None:
    """Validate one business composition table fact."""

    if not isinstance(fact, dict):
        raise BusinessCompositionTableValidationError("table fact must be a dict")

    _assert_no_forbidden_recommendation_keys(fact)
    _assert_no_secret_like_payload(fact)

    missing = TABLE_FACT_REQUIRED_FIELDS - set(fact)
    if missing:
        raise BusinessCompositionTableValidationError(f"table fact missing keys: {sorted(missing)}")

    if not _non_empty_string(fact["fact_id"]):
        raise BusinessCompositionTableValidationError("fact_id must be a non-empty string")
    if not _non_empty_string(fact["field_path"]):
        raise BusinessCompositionTableValidationError("field_path must be a non-empty string")
    if fact["unit"] is not None and not isinstance(fact["unit"], str):
        raise BusinessCompositionTableValidationError("unit must be a string or null")
    if not _non_empty_string(fact["period"]):
        raise BusinessCompositionTableValidationError("period must be a non-empty string")
    if not _non_empty_string(fact["source_document_id"]):
        raise BusinessCompositionTableValidationError("source_document_id must be a non-empty string")
    if not isinstance(fact["source_section"], str):
        raise BusinessCompositionTableValidationError("source_section must be a string")
    if not isinstance(fact["source_page_or_anchor"], str):
        raise BusinessCompositionTableValidationError("source_page_or_anchor must be a string")
    if not _non_empty_string(fact["source_table_id"]):
        raise BusinessCompositionTableValidationError("source_table_id must be a non-empty string")
    if not isinstance(fact["source_row_index"], int) or isinstance(fact["source_row_index"], bool):
        raise BusinessCompositionTableValidationError("source_row_index must be a non-negative integer")
    if fact["source_row_index"] < 0:
        raise BusinessCompositionTableValidationError("source_row_index must be a non-negative integer")
    if not _non_empty_string(fact["source_column_name"]):
        raise BusinessCompositionTableValidationError("source_column_name must be a non-empty string")
    if not isinstance(fact["source_column_map"], dict) or not fact["source_column_map"]:
        raise BusinessCompositionTableValidationError("source_column_map must be a non-empty dict")
    if fact["classification_type"] not in CLASSIFICATION_TYPE_VALUES:
        raise BusinessCompositionTableValidationError("classification_type is unsupported")
    if not _non_empty_string(fact["segment_name"]):
        raise BusinessCompositionTableValidationError("segment_name must be a non-empty string")
    if fact["denominator"] is not None and not isinstance(fact["denominator"], str):
        raise BusinessCompositionTableValidationError("denominator must be a string or null")
    if fact["evidence_tier"] not in EVIDENCE_TIER_VALUES:
        raise BusinessCompositionTableValidationError("evidence_tier is unsupported")
    if fact["extraction_confidence"] not in EXTRACTION_CONFIDENCE_VALUES:
        raise BusinessCompositionTableValidationError("extraction_confidence is unsupported")
    if fact["table_quality"] not in TABLE_QUALITY_VALUES:
        raise BusinessCompositionTableValidationError("table_quality is unsupported")
    if not isinstance(fact["needs_human_review"], bool):
        raise BusinessCompositionTableValidationError("needs_human_review must be a boolean")
    if not isinstance(fact["caveats"], list) or not all(isinstance(item, str) for item in fact["caveats"]):
        raise BusinessCompositionTableValidationError("caveats must be a list of strings")

    policy = _TABLE_QUALITY_POLICIES[fact["table_quality"]]
    if policy["caveat_only"]:
        raise BusinessCompositionTableValidationError(
            "table_quality is caveat-only; use table_caveats instead of table_facts"
        )
    if policy["requires_human_review"] and fact["needs_human_review"] is not True:
        raise BusinessCompositionTableValidationError("table_quality requires human review")
    if policy["requires_caveat"] and _contains_structured_numeric(fact["value"]) and not fact["caveats"]:
        raise BusinessCompositionTableValidationError("table_quality requires caveats for numeric extraction")
    if policy["caveat_only"] and _contains_structured_numeric(fact["value"]):
        raise BusinessCompositionTableValidationError("table_quality does not allow structured numeric values")

    if fact["evidence_tier"] == "L1_official_disclosure":
        _validate_l1_table_fact_location(fact)


def build_table_caveat(
    *,
    reason: str,
    table_quality: str,
    source_section: str | None = None,
) -> dict:
    """Build one machine-readable caveat without numeric fact values."""

    if not _non_empty_string(reason):
        raise BusinessCompositionTableValidationError("caveat reason must be a non-empty string")
    policy = get_table_quality_policy(table_quality)
    caveat = {
        "reason": reason,
        "table_quality": table_quality,
        "source_section": source_section or "",
        "can_extract_numeric_values": policy["can_extract_numeric_values"],
        "requires_human_review": policy["requires_human_review"],
        "caveat_only": policy["caveat_only"],
        "blocked_numeric_extraction": not policy["can_extract_numeric_values"],
    }
    validate_table_caveat(caveat)
    return caveat


def build_unreliable_text_copy_caveat(source_section: str | None = None) -> dict:
    """Build the standard caveat for copied text with unreliable table layout."""

    caveat = build_table_caveat(
        reason=TABLE_STRUCTURE_UNRELIABLE_DUE_TO_PDF_TEXT_COPY,
        table_quality="unreliable_text_copy",
        source_section=source_section,
    )
    caveat["detected_signal"] = BUSINESS_COMPOSITION_SECTION_DETECTED
    validate_table_caveat(caveat)
    return caveat


def validate_table_caveat(caveat: dict) -> None:
    """Validate one machine-readable table caveat."""

    if not isinstance(caveat, dict):
        raise BusinessCompositionTableValidationError("table caveat must be a dict")
    _assert_no_forbidden_recommendation_keys(caveat)
    _assert_no_secret_like_payload(caveat)

    required = {
        "reason",
        "table_quality",
        "source_section",
        "can_extract_numeric_values",
        "requires_human_review",
        "caveat_only",
        "blocked_numeric_extraction",
    }
    missing = required - set(caveat)
    if missing:
        raise BusinessCompositionTableValidationError(f"table caveat missing keys: {sorted(missing)}")
    if not _non_empty_string(caveat["reason"]):
        raise BusinessCompositionTableValidationError("caveat reason must be a non-empty string")
    if caveat["table_quality"] not in TABLE_QUALITY_VALUES:
        raise BusinessCompositionTableValidationError("table_quality is unsupported")
    if not isinstance(caveat["source_section"], str):
        raise BusinessCompositionTableValidationError("source_section must be a string")
    for key in ("can_extract_numeric_values", "requires_human_review", "caveat_only", "blocked_numeric_extraction"):
        if not isinstance(caveat[key], bool):
            raise BusinessCompositionTableValidationError(f"{key} must be a boolean")
    if "value" in caveat:
        raise BusinessCompositionTableValidationError("table caveat must not include numeric fact value")


def build_business_composition_table_facts(
    *,
    code: str,
    company_name: str,
    source_document_id: str,
    table_facts: list[dict],
    table_caveats: list[dict] | None = None,
    created_at: str | None = None,
) -> dict:
    """Build and validate an in-memory table facts payload."""

    payload = {
        "version": BUSINESS_COMPOSITION_TABLE_FACT_VERSION,
        "code": code,
        "company_name": company_name,
        "created_at": created_at or _utc_now(),
        "source_document_id": source_document_id,
        "table_facts": copy.deepcopy(table_facts),
        "table_caveats": copy.deepcopy(table_caveats or []),
        "not_for_trading_advice": True,
    }
    validate_business_composition_table_facts(payload)
    return payload


def validate_business_composition_table_facts(payload: dict) -> None:
    """Validate an in-memory business composition table facts payload."""

    if not isinstance(payload, dict):
        raise BusinessCompositionTableValidationError("business composition table payload must be a dict")

    _assert_no_forbidden_recommendation_keys(payload)
    _assert_no_secret_like_payload(payload)

    required = {
        "version",
        "code",
        "company_name",
        "created_at",
        "source_document_id",
        "table_facts",
        "table_caveats",
        "not_for_trading_advice",
    }
    missing = required - set(payload)
    if missing:
        raise BusinessCompositionTableValidationError(f"business composition table payload missing keys: {sorted(missing)}")
    if payload["version"] != BUSINESS_COMPOSITION_TABLE_FACT_VERSION:
        raise BusinessCompositionTableValidationError("business composition table facts version is unsupported")
    if not _non_empty_string(payload["code"]):
        raise BusinessCompositionTableValidationError("code must be a non-empty string")
    if not _non_empty_string(payload["company_name"]):
        raise BusinessCompositionTableValidationError("company_name must be a non-empty string")
    if not _non_empty_string(payload["created_at"]):
        raise BusinessCompositionTableValidationError("created_at must be a non-empty string")
    if not _non_empty_string(payload["source_document_id"]):
        raise BusinessCompositionTableValidationError("source_document_id must be a non-empty string")
    if payload["not_for_trading_advice"] is not True:
        raise BusinessCompositionTableValidationError("not_for_trading_advice must be true")
    if not isinstance(payload["table_facts"], list):
        raise BusinessCompositionTableValidationError("table_facts must be a list")
    if not isinstance(payload["table_caveats"], list):
        raise BusinessCompositionTableValidationError("table_caveats must be a list")

    seen_fact_ids: set[str] = set()
    for fact in payload["table_facts"]:
        validate_table_fact(fact)
        if fact["source_document_id"] != payload["source_document_id"]:
            raise BusinessCompositionTableValidationError("table fact source_document_id must match payload source_document_id")
        if fact["fact_id"] in seen_fact_ids:
            raise BusinessCompositionTableValidationError(f"duplicate fact_id: {fact['fact_id']}")
        seen_fact_ids.add(fact["fact_id"])

    for caveat in payload["table_caveats"]:
        validate_table_caveat(caveat)


def _validate_l1_table_fact_location(fact: dict) -> None:
    if not _non_empty_string(fact["source_table_id"]):
        raise BusinessCompositionTableValidationError("L1 table facts require source_table_id")
    if fact["source_row_index"] < 0 or not _non_empty_string(fact["source_column_name"]):
        raise BusinessCompositionTableValidationError("L1 table facts require row and column location")
    if not _non_empty_string(fact["unit"]):
        raise BusinessCompositionTableValidationError("L1 table facts require unit")
    if not _non_empty_string(fact["period"]):
        raise BusinessCompositionTableValidationError("L1 table facts require period")
    if fact["classification_type"] not in CLASSIFICATION_TYPE_VALUES:
        raise BusinessCompositionTableValidationError("L1 table facts require classification_type")
    has_denominator = _non_empty_string(fact["denominator"])
    has_caveat = bool(fact["caveats"])
    if not has_denominator and not has_caveat:
        raise BusinessCompositionTableValidationError("L1 table facts require denominator or caveat")


def _contains_structured_numeric(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        return bool(_NUMERIC_STRING_RE.fullmatch(value))
    if isinstance(value, dict):
        return any(_contains_structured_numeric(child) for child in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_structured_numeric(child) for child in value)
    return False


def _assert_no_forbidden_recommendation_keys(payload: Any) -> None:
    for key in _walk_keys(payload):
        if str(key).lower() in FORBIDDEN_RECOMMENDATION_KEYS:
            raise BusinessCompositionTableValidationError("business composition table payload contains forbidden recommendation keys")


def _assert_no_secret_like_payload(payload: Any) -> None:
    finding = _first_secret_like_finding(payload, "$")
    if finding:
        raise BusinessCompositionTableSecretError(f"business composition table payload contains secret-like data at {finding}: <masked>")


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


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
