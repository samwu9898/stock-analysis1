# -*- coding: utf-8 -*-
"""In-memory conversion from normalized CSV tables to table facts."""

from __future__ import annotations

import copy
import re
from typing import Any

from .business_composition_table import (
    BusinessCompositionTableQualityError,
    BusinessCompositionTableSecretError,
    BusinessCompositionTableValidationError,
    TABLE_QUALITY_VALUES,
    build_table_caveat,
    build_table_fact,
    get_table_quality_policy,
    validate_table_caveat,
    validate_table_fact,
)
from .local_structured_table_reader import (
    LocalStructuredTableSecretError,
    LocalStructuredTableValidationError,
    validate_normalized_table,
)


DEFAULT_LOCAL_CSV_TABLE_QUALITY = "structured_medium"
DEFAULT_LOCAL_CSV_CAVEAT = "local_structured_sample_requires_human_review"

CLASSIFICATION_TYPE_VALUES = {"industry", "product", "region", "other"}

MAPPING_FIELDS = {
    "segment_name",
    "revenue",
    "cost",
    "gross_margin",
    "revenue_yoy",
    "cost_yoy",
    "gross_margin_yoy_change",
}

CAVEAT_ONLY_TABLE_QUALITIES = {"unreliable_text_copy", "unusable"}

HEADER_ALLOWLIST = {
    "segment_name": {"产品名称", "分产品", "项目", "产品", "业务板块"},
    "revenue": {"主营业务收入", "营业收入", "收入"},
    "cost": {"主营业务成本", "营业成本", "成本"},
    "gross_margin": {"毛利率"},
    "revenue_yoy": {"主营业务收入比上年同期增减", "营业收入比上年同期增减", "收入同比"},
    "cost_yoy": {"主营业务成本比上年同期增减", "营业成本比上年同期增减", "成本同比"},
    "gross_margin_yoy_change": {"毛利率比上年同期增减", "毛利率同比变动"},
}

BLOCKING_ROW_CAVEATS = {
    "blank_row",
    "comment_row",
    "duplicate_header_row",
    "duplicate_segment_name",
    "row_length_unstable",
    "segment_name_missing",
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


class CsvTableFactConverterError(RuntimeError):
    """Base error for CSV normalized table conversion."""


class CsvTableFactConverterValidationError(CsvTableFactConverterError):
    """Raised when converter input or output fails validation."""


class CsvTableFactConverterMappingError(CsvTableFactConverterError):
    """Raised when explicit or inferred column mapping is unsafe."""


class CsvTableFactConverterSecretError(CsvTableFactConverterError):
    """Raised when converter input contains secret-like data."""


def build_column_mapping(
    headers: list[str],
    *,
    explicit_mapping: dict | None = None,
) -> dict:
    """Build a conservative logical-column to source-header mapping."""

    if not isinstance(headers, list) or not all(isinstance(header, str) for header in headers):
        raise CsvTableFactConverterValidationError("headers must be a list of strings")
    _assert_no_forbidden_recommendation_keys(headers)
    _assert_no_secret_like_payload(headers)
    _assert_no_forbidden_recommendation_keys(explicit_mapping)
    _assert_no_secret_like_payload(explicit_mapping)

    mapping: dict[str, str] = {}
    used_headers: set[str] = set()
    if explicit_mapping is not None:
        if not isinstance(explicit_mapping, dict):
            raise CsvTableFactConverterMappingError("explicit_mapping must be a dict")
        for field, header in explicit_mapping.items():
            if field not in MAPPING_FIELDS:
                raise CsvTableFactConverterMappingError("explicit_mapping contains unsupported field")
            if not _non_empty_string(header):
                raise CsvTableFactConverterMappingError("explicit_mapping header must be a non-empty string")
            if header not in headers:
                raise CsvTableFactConverterMappingError("explicit_mapping header is not present in headers")
            if headers.count(header) > 1:
                raise CsvTableFactConverterMappingError("ambiguous_header")
            if header in used_headers:
                raise CsvTableFactConverterMappingError("explicit_mapping reuses a source header")
            mapping[field] = header
            used_headers.add(header)

    for field, allowlist in HEADER_ALLOWLIST.items():
        if field in mapping:
            continue
        normalized_allowlist = {_normalize_header(allowed) for allowed in allowlist}
        matches = [
            header
            for header in headers
            if _normalize_header(header) in normalized_allowlist
        ]
        unique_matches = sorted(set(matches), key=headers.index)
        if len(matches) > 1:
            raise CsvTableFactConverterMappingError("ambiguous_header")
        if len(unique_matches) == 1 and unique_matches[0] not in used_headers:
            mapping[field] = unique_matches[0]
            used_headers.add(unique_matches[0])

    return mapping


def iter_mapped_rows(normalized_table: dict, column_mapping: dict) -> list[dict]:
    """Return mapped rows without generating table facts."""

    _validate_normalized_table_for_converter(normalized_table)
    rows, _ = _iter_mapped_rows_with_caveats(normalized_table, column_mapping)
    return rows


def convert_normalized_table_to_table_facts(
    normalized_table: dict,
    *,
    period: str | None = None,
    unit: str | None = None,
    denominator: str | None = None,
    classification_type: str | None = None,
    explicit_mapping: dict | None = None,
    table_quality: str = DEFAULT_LOCAL_CSV_TABLE_QUALITY,
    needs_human_review: bool = True,
) -> dict:
    """Convert one normalized CSV table into in-memory facts or caveats."""

    _assert_no_forbidden_recommendation_keys(
        {
            "period": period,
            "unit": unit,
            "denominator": denominator,
            "classification_type": classification_type,
            "explicit_mapping": explicit_mapping,
            "table_quality": table_quality,
            "needs_human_review": needs_human_review,
        }
    )
    _assert_no_secret_like_payload(
        {
            "period": period,
            "unit": unit,
            "denominator": denominator,
            "classification_type": classification_type,
            "explicit_mapping": explicit_mapping,
            "table_quality": table_quality,
            "needs_human_review": needs_human_review,
        }
    )
    _validate_normalized_table_for_converter(normalized_table)
    if table_quality not in TABLE_QUALITY_VALUES:
        raise CsvTableFactConverterValidationError("table_quality is unsupported")
    if not isinstance(needs_human_review, bool):
        raise CsvTableFactConverterValidationError("needs_human_review must be a boolean")

    source_section = normalized_table.get("source_section", "")
    reader_reasons = _reader_warning_reasons(normalized_table)
    caveat_reasons = [DEFAULT_LOCAL_CSV_CAVEAT, *reader_reasons]
    conversion_warnings = list(caveat_reasons)

    if table_quality in CAVEAT_ONLY_TABLE_QUALITIES:
        reason = "unreliable_text_copy" if table_quality == "unreliable_text_copy" else "unusable_table"
        return _payload(
            normalized_table,
            table_facts=[],
            table_caveats=_build_table_caveats([reason, *caveat_reasons], table_quality, source_section),
            conversion_warnings=[reason, *conversion_warnings],
        )

    policy = _table_quality_policy(table_quality)
    if policy.get("requires_human_review") and needs_human_review is not True:
        raise CsvTableFactConverterValidationError("table_quality requires human review")

    try:
        column_mapping = build_column_mapping(normalized_table["headers"], explicit_mapping=explicit_mapping)
    except CsvTableFactConverterMappingError as exc:
        reason = "ambiguous_header" if "ambiguous_header" in str(exc) else "unsupported_column"
        return _payload(
            normalized_table,
            table_facts=[],
            table_caveats=_build_table_caveats([reason, *caveat_reasons], table_quality, source_section),
            conversion_warnings=[reason, *conversion_warnings],
        )

    mapped_rows, row_caveats = _iter_mapped_rows_with_caveats(normalized_table, column_mapping)
    caveat_reasons.extend(row_caveats)

    effective_period = _effective_value(period, normalized_table.get("detected_period"))
    effective_unit = _effective_value(unit, normalized_table.get("detected_unit"))
    effective_classification = _effective_classification(classification_type, normalized_table.get("classification_hint"))
    effective_denominator = _effective_value(denominator, None)

    blocking_reasons = _quality_gate_blocking_reasons(
        normalized_table=normalized_table,
        column_mapping=column_mapping,
        row_caveats=row_caveats,
        effective_period=effective_period,
        effective_unit=effective_unit,
        effective_classification=effective_classification,
        period_is_explicit=_non_empty_string(period),
        unit_is_explicit=_non_empty_string(unit),
    )
    if not effective_denominator:
        caveat_reasons.append("denominator_missing")
        conversion_warnings.append("denominator_missing")

    if blocking_reasons:
        return _payload(
            normalized_table,
            table_facts=[],
            table_caveats=_build_table_caveats([*blocking_reasons, *caveat_reasons], table_quality, source_section),
            conversion_warnings=[*blocking_reasons, *conversion_warnings, *row_caveats],
        )

    fact_caveats = _unique_reasons(caveat_reasons)
    source_column_map = copy.deepcopy(column_mapping)
    if effective_denominator:
        source_column_map["denominator"] = effective_denominator
    facts = []
    for row in mapped_rows:
        if row.get("skip_fact"):
            continue
        revenue_value = row["values"].get("revenue", "")
        if not _non_empty_string(revenue_value):
            continue
        fact = build_table_fact(
            fact_id=_fact_id(normalized_table["source_table_id"], row["source_row_index"], "revenue"),
            field_path="business_composition.product_segment.revenue",
            value=revenue_value,
            unit=effective_unit,
            period=effective_period,
            source_document_id=normalized_table["source_document_id"],
            source_section=normalized_table["source_section"],
            source_page_or_anchor=normalized_table.get("source_page_or_anchor", ""),
            source_table_id=normalized_table["source_table_id"],
            source_row_index=row["source_row_index"],
            source_column_name=column_mapping["revenue"],
            source_column_map=source_column_map,
            classification_type=effective_classification,
            segment_name=row["segment_name"],
            denominator=effective_denominator,
            evidence_tier="L1_official_disclosure",
            extraction_confidence="medium",
            needs_human_review=needs_human_review,
            table_quality=table_quality,
            caveats=fact_caveats,
        )
        validate_table_fact(fact)
        facts.append(fact)

    return _payload(
        normalized_table,
        table_facts=facts,
        table_caveats=_build_table_caveats(caveat_reasons, table_quality, source_section),
        conversion_warnings=conversion_warnings,
    )


def _validate_normalized_table_for_converter(normalized_table: dict) -> None:
    try:
        validate_normalized_table(normalized_table)
    except LocalStructuredTableSecretError as exc:
        raise CsvTableFactConverterSecretError("normalized table contains secret-like data: <masked>") from exc
    except LocalStructuredTableValidationError as exc:
        raise CsvTableFactConverterValidationError("normalized table is invalid") from exc


def _iter_mapped_rows_with_caveats(normalized_table: dict, column_mapping: dict) -> tuple[list[dict], list[str]]:
    if not isinstance(column_mapping, dict):
        raise CsvTableFactConverterMappingError("column_mapping must be a dict")
    if "segment_name" not in column_mapping:
        return [], ["segment_column_missing"]

    headers = normalized_table["headers"]
    rows = normalized_table["rows"]
    segment_index = _column_index(headers, column_mapping["segment_name"])
    mapped_rows = []
    caveats: list[str] = []
    seen_segments: set[str] = set()
    for row_index, row in enumerate(rows, start=1):
        row_caveats: list[str] = []
        if len(row) != len(headers):
            row_caveats.append("row_length_unstable")
        if not row or not any(cell.strip() for cell in row):
            row_caveats.append("blank_row")
        if len(row) == len(headers) and [_normalize_header(cell) for cell in row] == [_normalize_header(header) for header in headers]:
            row_caveats.append("duplicate_header_row")

        segment_name = row[segment_index] if segment_index < len(row) else ""
        if segment_name.strip().startswith(("#", "注:", "注：", "说明:", "说明：")):
            row_caveats.append("comment_row")
        if not segment_name.strip():
            row_caveats.append("segment_name_missing")
        if segment_name in seen_segments:
            row_caveats.append("duplicate_segment_name")
        if segment_name.strip():
            seen_segments.add(segment_name)

        skip_fact = bool(BLOCKING_ROW_CAVEATS.intersection(row_caveats))
        caveats.extend(row_caveats)
        if "segment_name_missing" in row_caveats:
            continue
        values = {
            field: row[_column_index(headers, header)] if _column_index(headers, header) < len(row) else ""
            for field, header in column_mapping.items()
        }
        mapped_rows.append(
            {
                "source_row_index": row_index,
                "segment_name": segment_name,
                "is_total_row": _is_total_row(segment_name),
                "cells": list(row),
                "values": values,
                "row_caveats": row_caveats,
                "skip_fact": skip_fact,
            }
        )

    return mapped_rows, _unique_reasons(caveats)


def _quality_gate_blocking_reasons(
    *,
    normalized_table: dict,
    column_mapping: dict,
    row_caveats: list[str],
    effective_period: str,
    effective_unit: str,
    effective_classification: str,
    period_is_explicit: bool,
    unit_is_explicit: bool,
) -> list[str]:
    reasons: list[str] = []
    headers = normalized_table["headers"]
    rows = normalized_table["rows"]
    reader_reasons = set(_reader_warning_reasons(normalized_table))
    if not headers or not any(header.strip() for header in headers):
        reasons.append("header_missing")
    if any(len(row) != len(headers) for row in rows) or "row_length_unstable" in reader_reasons:
        reasons.append("row_length_unstable")
    if not effective_classification:
        reasons.append("classification_not_detected")
    if "segment_name" not in column_mapping:
        reasons.append("segment_column_missing")
    if "revenue" not in column_mapping:
        reasons.append("revenue_column_missing")
    if not effective_unit or ("unit_not_detected" in reader_reasons and not unit_is_explicit):
        reasons.append("unit_not_detected")
    if not effective_period or ("period_not_detected" in reader_reasons and not period_is_explicit):
        reasons.append("period_not_detected")
    for reason in row_caveats:
        if reason in BLOCKING_ROW_CAVEATS:
            reasons.append(reason)
    return _unique_reasons(reasons)


def _build_table_caveats(reasons: list[str], table_quality: str, source_section: str) -> list[dict]:
    caveats = []
    for reason in _unique_reasons(reasons):
        if not _non_empty_string(reason):
            continue
        caveat = build_table_caveat(reason=reason, table_quality=table_quality, source_section=source_section)
        validate_table_caveat(caveat)
        caveats.append(caveat)
    return caveats


def _payload(
    normalized_table: dict,
    *,
    table_facts: list[dict],
    table_caveats: list[dict],
    conversion_warnings: list[str],
) -> dict:
    payload = {
        "source_document_id": normalized_table["source_document_id"],
        "source_table_id": normalized_table["source_table_id"],
        "table_facts": copy.deepcopy(table_facts),
        "table_caveats": copy.deepcopy(table_caveats),
        "conversion_warnings": [
            {"reason": reason, "detail": ""} for reason in _unique_reasons(conversion_warnings) if _non_empty_string(reason)
        ],
        "not_for_trading_advice": True,
    }
    _validate_converter_payload(payload)
    return payload


def _validate_converter_payload(payload: dict) -> None:
    _assert_no_forbidden_recommendation_keys(payload)
    _assert_no_secret_like_payload(payload)
    for fact in payload["table_facts"]:
        try:
            validate_table_fact(fact)
        except BusinessCompositionTableSecretError as exc:
            raise CsvTableFactConverterSecretError("table fact contains secret-like data: <masked>") from exc
        except BusinessCompositionTableValidationError as exc:
            raise CsvTableFactConverterValidationError("table fact is invalid") from exc
    for caveat in payload["table_caveats"]:
        try:
            validate_table_caveat(caveat)
        except BusinessCompositionTableSecretError as exc:
            raise CsvTableFactConverterSecretError("table caveat contains secret-like data: <masked>") from exc
        except BusinessCompositionTableValidationError as exc:
            raise CsvTableFactConverterValidationError("table caveat is invalid") from exc


def _table_quality_policy(table_quality: str) -> dict:
    try:
        return get_table_quality_policy(table_quality)
    except BusinessCompositionTableQualityError as exc:
        raise CsvTableFactConverterValidationError("table_quality is unsupported") from exc


def _reader_warning_reasons(normalized_table: dict) -> list[str]:
    reasons = []
    for warning in normalized_table.get("reader_warnings", []):
        if isinstance(warning, dict) and _non_empty_string(warning.get("reason")):
            reasons.append(warning["reason"])
    return _unique_reasons(reasons)


def _effective_value(explicit: str | None, detected: str | None) -> str:
    if isinstance(explicit, str) and explicit.strip():
        return explicit
    if isinstance(detected, str) and detected.strip():
        return detected
    return ""


def _effective_classification(explicit: str | None, hint: str | None) -> str:
    value = _effective_value(explicit, hint)
    return value if value in CLASSIFICATION_TYPE_VALUES else ""


def _column_index(headers: list[str], header: str) -> int:
    try:
        return headers.index(header)
    except ValueError as exc:
        raise CsvTableFactConverterMappingError("column_mapping references missing header") from exc


def _is_total_row(segment_name: str) -> bool:
    normalized = re.sub(r"\s+", "", segment_name).lower()
    return normalized in {"合计", "总计", "小计", "total"}


def _fact_id(source_table_id: str, source_row_index: int, field: str) -> str:
    base = re.sub(r"[^A-Za-z0-9_]+", "_", source_table_id).strip("_").lower()
    return f"{base}_row_{source_row_index:03d}_{field}"


def _normalize_header(value: str) -> str:
    return re.sub(r"\s+", "", value).strip().lower()


def _unique_reasons(reasons: list[str]) -> list[str]:
    unique = []
    for reason in reasons:
        if reason not in unique:
            unique.append(reason)
    return unique


def _assert_no_forbidden_recommendation_keys(payload: Any) -> None:
    for key in _walk_keys(payload):
        if str(key).lower() in {"buy", "sell", "target_price", "position", "portfolio_weight"}:
            raise CsvTableFactConverterValidationError("converter payload contains forbidden recommendation keys")


def _assert_no_secret_like_payload(payload: Any) -> None:
    finding = _first_secret_like_finding(payload, "$")
    if finding:
        raise CsvTableFactConverterSecretError(f"converter payload contains secret-like data at {finding}: <masked>")


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
