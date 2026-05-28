# -*- coding: utf-8 -*-
"""CSV-only local structured table reader."""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path
from typing import Any


NORMALIZED_TABLE_VERSION = "normalized_table.v1"
SUPPORTED_TABLE_FORMATS = {"csv"}
DEFAULT_MAX_CSV_BYTES = 2_000_000

TABLE_QUALITY_VALUES = {
    "structured_high",
    "structured_medium",
    "partially_structured",
    "unreliable_text_copy",
    "unusable",
}

CLASSIFICATION_HINT_VALUES = {"industry", "product", "region", "other", "unknown"}

FORBIDDEN_RECOMMENDATION_KEYS = {
    "buy",
    "sell",
    "target_price",
    "position",
    "portfolio_weight",
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

_UNIT_RE = re.compile(
    r"(?:单位|金额单位|币种)\s*[:：]\s*([A-Za-z%％\u4e00-\u9fff]{1,12})"
    r"|[（(]\s*(元|千元|万元|百万元|亿元|人民币元|人民币万元|CNY|RMB|%|％)\s*[）)]",
    flags=re.IGNORECASE,
)
_EXPLICIT_PERIOD_RE = re.compile(r"(?<![A-Za-z0-9])(20\d{2})(A|H1|H2|Q[1-4])(?![A-Za-z0-9])", flags=re.IGNORECASE)
_CHINESE_PERIOD_RE = re.compile(
    r"(20\d{2})\s*年?\s*(年度|年报|半年度|中期|上半年|下半年|第一季度|第二季度|第三季度|第四季度|一季度|二季度|三季度|四季度|1季度|2季度|3季度|4季度)"
)


class LocalStructuredTableReaderError(RuntimeError):
    """Base error for local structured table reader operations."""


class LocalStructuredTableValidationError(LocalStructuredTableReaderError):
    """Raised when normalized table payload validation fails."""


class LocalStructuredTablePathBoundaryError(LocalStructuredTableReaderError):
    """Raised when a requested local path escapes its allowed boundary."""


class LocalStructuredTableSecretError(LocalStructuredTableReaderError):
    """Raised when a path, payload, or text contains secret-like data."""


class LocalStructuredTableFormatError(LocalStructuredTableReaderError):
    """Raised when a local structured table file cannot be safely read."""


def read_local_csv_table(
    path: Path,
    *,
    repo_root: Path | None = None,
    source_document_id: str,
    source_table_id: str,
    source_section: str = "",
    source_page_or_anchor: str = "",
    table_title: str = "",
    encoding: str | None = None,
    delimiter: str | None = None,
) -> dict:
    """Read one explicit local CSV file into a normalized table payload."""

    _assert_non_empty_string(source_document_id, "source_document_id")
    _assert_non_empty_string(source_table_id, "source_table_id")
    root = Path(repo_root) if repo_root is not None else Path.cwd()
    resolved_path, root_resolved = _resolve_under_root(Path(path), root)
    if not resolved_path.exists() or not resolved_path.is_file():
        raise LocalStructuredTablePathBoundaryError("local csv path must point to a file")
    if resolved_path.suffix.lower() != ".csv":
        raise LocalStructuredTableFormatError("unsupported local structured table suffix")

    size_bytes = resolved_path.stat().st_size
    if size_bytes > DEFAULT_MAX_CSV_BYTES:
        raise LocalStructuredTableFormatError("local csv file is too large")

    raw = resolved_path.read_bytes()
    if b"\x00" in raw:
        raise LocalStructuredTableFormatError("local csv file appears to be binary")

    text = _decode_csv_bytes(raw, encoding=encoding)
    _assert_no_secret_like_payload(text)

    reader_warnings: list[dict] = []
    selected_delimiter = _select_delimiter(text, delimiter=delimiter, warnings=reader_warnings)
    parsed_rows = list(csv.reader(io.StringIO(text, newline=""), delimiter=selected_delimiter))

    if parsed_rows:
        headers = [_strip_bom_from_first_header(cell, index) for index, cell in enumerate(parsed_rows[0])]
        rows = [list(row) for row in parsed_rows[1:]]
    else:
        headers = []
        rows = []

    _append_shape_warnings(headers, rows, reader_warnings)

    detected_unit = detect_table_unit(headers, rows)
    detected_period = detect_table_period(headers, rows)
    classification_hint = detect_classification_hint(headers, rows, source_section=source_section)
    if not detected_unit:
        reader_warnings.append(build_reader_warning("unit_not_detected"))
    if not detected_period:
        reader_warnings.append(build_reader_warning("period_not_detected"))
    if not classification_hint:
        reader_warnings.append(build_reader_warning("classification_not_detected"))

    payload = {
        "version": NORMALIZED_TABLE_VERSION,
        "source_document_id": source_document_id,
        "source_table_id": source_table_id,
        "source_file_path": _relative_posix_path(resolved_path, root_resolved),
        "source_format": "csv",
        "source_section": source_section,
        "source_page_or_anchor": source_page_or_anchor,
        "table_title": table_title,
        "headers": headers,
        "rows": rows,
        "row_count": len(rows),
        "column_count": len(headers),
        "detected_unit": detected_unit,
        "detected_period": detected_period,
        "classification_hint": classification_hint,
        "reader_warnings": reader_warnings,
        "table_quality_hint": _assign_table_quality_hint(headers, rows),
    }
    validate_normalized_table(payload)
    return payload


def detect_table_unit(headers: list[str], rows: list[list[str]]) -> str:
    """Return one explicit unit hint, or an empty string when ambiguous."""

    candidates = _unit_candidates(_flatten_cells(headers, rows, row_limit=5))
    return candidates[0] if len(candidates) == 1 else ""


def detect_table_period(headers: list[str], rows: list[list[str]]) -> str:
    """Return one explicit period hint, or an empty string when ambiguous."""

    candidates = _period_candidates(_flatten_cells(headers, rows, row_limit=5))
    return candidates[0] if len(candidates) == 1 else ""


def detect_classification_hint(headers: list[str], rows: list[list[str]], source_section: str = "") -> str:
    """Return a conservative segment-classification hint."""

    source_hint = _classification_hint_from_text(source_section)
    if source_hint:
        return source_hint

    hints: set[str] = set()
    for cell in _flatten_cells(headers, rows, row_limit=5):
        hint = _classification_hint_from_text(cell)
        if hint:
            hints.add(hint)
    return next(iter(hints)) if len(hints) == 1 else ""


def build_reader_warning(reason: str, *, detail: str | None = None) -> dict:
    """Build one machine-readable reader warning."""

    if not isinstance(reason, str) or not reason.strip():
        raise LocalStructuredTableValidationError("reader warning reason must be a non-empty string")
    warning = {"reason": reason, "detail": detail or ""}
    _assert_no_secret_like_payload(warning)
    return warning


def validate_normalized_table(payload: dict) -> None:
    """Validate one normalized table payload."""

    if not isinstance(payload, dict):
        raise LocalStructuredTableValidationError("normalized table payload must be a dict")
    _assert_no_forbidden_recommendation_keys(payload)
    _assert_no_secret_like_payload(payload)

    required = {
        "version",
        "source_document_id",
        "source_table_id",
        "source_file_path",
        "source_format",
        "source_section",
        "source_page_or_anchor",
        "table_title",
        "headers",
        "rows",
        "row_count",
        "column_count",
        "detected_unit",
        "detected_period",
        "classification_hint",
        "reader_warnings",
        "table_quality_hint",
    }
    missing = required - set(payload)
    if missing:
        raise LocalStructuredTableValidationError(f"normalized table payload missing keys: {sorted(missing)}")
    if payload["version"] != NORMALIZED_TABLE_VERSION:
        raise LocalStructuredTableValidationError("normalized table version is unsupported")
    if not _non_empty_string(payload["source_document_id"]):
        raise LocalStructuredTableValidationError("source_document_id must be a non-empty string")
    if not _non_empty_string(payload["source_table_id"]):
        raise LocalStructuredTableValidationError("source_table_id must be a non-empty string")
    if payload["source_format"] != "csv":
        raise LocalStructuredTableValidationError("source_format is unsupported")

    for key in (
        "source_file_path",
        "source_section",
        "source_page_or_anchor",
        "table_title",
        "detected_unit",
        "detected_period",
        "classification_hint",
        "table_quality_hint",
    ):
        if not isinstance(payload[key], str):
            raise LocalStructuredTableValidationError(f"{key} must be a string")

    if payload["classification_hint"] and payload["classification_hint"] not in CLASSIFICATION_HINT_VALUES:
        raise LocalStructuredTableValidationError("classification_hint is unsupported")
    if payload["table_quality_hint"] and payload["table_quality_hint"] not in TABLE_QUALITY_VALUES:
        raise LocalStructuredTableValidationError("table_quality_hint is unsupported")

    headers = payload["headers"]
    rows = payload["rows"]
    if not isinstance(headers, list):
        raise LocalStructuredTableValidationError("headers must be a list")
    if not all(isinstance(header, str) for header in headers):
        raise LocalStructuredTableValidationError("headers must contain only strings")
    if not isinstance(rows, list):
        raise LocalStructuredTableValidationError("rows must be a list")
    if not isinstance(payload["row_count"], int) or isinstance(payload["row_count"], bool):
        raise LocalStructuredTableValidationError("row_count must be an integer")
    if not isinstance(payload["column_count"], int) or isinstance(payload["column_count"], bool):
        raise LocalStructuredTableValidationError("column_count must be an integer")
    if payload["row_count"] != len(rows):
        raise LocalStructuredTableValidationError("row_count must match rows length")
    if payload["column_count"] != len(headers):
        raise LocalStructuredTableValidationError("column_count must match headers length")
    for row in rows:
        if not isinstance(row, list):
            raise LocalStructuredTableValidationError("each row must be a list")
        if not all(isinstance(cell, str) for cell in row):
            raise LocalStructuredTableValidationError("each row cell must be a string")

    warnings = payload["reader_warnings"]
    if not isinstance(warnings, list):
        raise LocalStructuredTableValidationError("reader_warnings must be a list")
    for warning in warnings:
        if not isinstance(warning, dict):
            raise LocalStructuredTableValidationError("reader_warnings must contain dicts")
        if not _non_empty_string(warning.get("reason")):
            raise LocalStructuredTableValidationError("reader warning reason must be a non-empty string")
        if "detail" in warning and not isinstance(warning["detail"], str):
            raise LocalStructuredTableValidationError("reader warning detail must be a string")


def _decode_csv_bytes(raw: bytes, *, encoding: str | None) -> str:
    if encoding is not None:
        normalized = encoding.lower().replace("_", "-")
        if normalized not in {"utf-8", "utf-8-sig"}:
            raise LocalStructuredTableFormatError("local csv encoding is unsupported")
        try:
            return raw.decode(normalized)
        except UnicodeDecodeError as exc:
            raise LocalStructuredTableFormatError("local csv file must be utf-8 text") from exc

    last_error: UnicodeDecodeError | None = None
    for candidate in ("utf-8-sig", "utf-8"):
        try:
            return raw.decode(candidate)
        except UnicodeDecodeError as exc:
            last_error = exc
    raise LocalStructuredTableFormatError("local csv file must be utf-8 text") from last_error


def _select_delimiter(text: str, *, delimiter: str | None, warnings: list[dict]) -> str:
    if delimiter is not None:
        if not isinstance(delimiter, str) or len(delimiter) != 1:
            raise LocalStructuredTableFormatError("csv delimiter must be a single character")
        return delimiter

    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        warnings.append(
            build_reader_warning(
                "delimiter_sniffed",
                detail=f"CSV delimiter was inferred with csv.Sniffer: {dialect.delimiter!r}.",
            )
        )
        return dialect.delimiter
    except csv.Error:
        warnings.append(
            build_reader_warning(
                "delimiter_fallback",
                detail="CSV delimiter was not confidently detected; comma fallback was used.",
            )
        )
        return ","


def _append_shape_warnings(headers: list[str], rows: list[list[str]], warnings: list[dict]) -> None:
    if not headers or not any(header.strip() for header in headers):
        warnings.append(build_reader_warning("header_missing"))
    if any(not header.strip() for header in headers):
        warnings.append(build_reader_warning("empty_header"))
    duplicate_headers = [header for header in headers if header and headers.count(header) > 1]
    if duplicate_headers:
        warnings.append(build_reader_warning("duplicate_header"))
    if any(not row or not any(cell.strip() for cell in row) for row in rows):
        warnings.append(build_reader_warning("blank_row_present"))
    if any(len(row) != len(headers) for row in rows):
        warnings.append(build_reader_warning("row_length_unstable"))


def _assign_table_quality_hint(headers: list[str], rows: list[list[str]]) -> str:
    if not headers or not any(header.strip() for header in headers):
        return "unusable"
    if any(len(row) != len(headers) for row in rows):
        return "partially_structured"
    if _has_segment_like_column(headers) and _has_revenue_like_column(headers):
        return "structured_medium"
    return ""


def _has_segment_like_column(headers: list[str]) -> bool:
    return any(
        re.search(r"(项目|类别|分类|产品|行业|地区|区域|segment|product|industry|region)", header, flags=re.IGNORECASE)
        for header in headers
    )


def _has_revenue_like_column(headers: list[str]) -> bool:
    return any(re.search(r"(收入|营收|营业额|revenue|sales)", header, flags=re.IGNORECASE) for header in headers)


def _strip_bom_from_first_header(value: str, index: int) -> str:
    return value.lstrip("\ufeff") if index == 0 else value


def _flatten_cells(headers: list[str], rows: list[list[str]], *, row_limit: int) -> list[str]:
    cells = list(headers)
    for row in rows[:row_limit]:
        cells.extend(row)
    return [cell for cell in cells if isinstance(cell, str) and cell.strip()]


def _unit_candidates(cells: list[str]) -> list[str]:
    candidates: list[str] = []
    for cell in cells:
        for match in _UNIT_RE.finditer(cell):
            unit = match.group(1) or match.group(2)
            if unit:
                normalized = unit.strip()
                if normalized and normalized not in candidates:
                    candidates.append(normalized)
    return candidates


def _period_candidates(cells: list[str]) -> list[str]:
    candidates: list[str] = []
    for cell in cells:
        for match in _EXPLICIT_PERIOD_RE.finditer(cell):
            period = f"{match.group(1)}{match.group(2).upper()}"
            if period not in candidates:
                candidates.append(period)
        for match in _CHINESE_PERIOD_RE.finditer(cell):
            period = _normalize_chinese_period(match.group(1), match.group(2))
            if period and period not in candidates:
                candidates.append(period)
    return candidates


def _normalize_chinese_period(year: str, label: str) -> str:
    if label in {"年度", "年报"}:
        return f"{year}A"
    if label in {"半年度", "中期", "上半年"}:
        return f"{year}H1"
    if label == "下半年":
        return f"{year}H2"
    quarter_map = {
        "第一季度": "Q1",
        "一季度": "Q1",
        "1季度": "Q1",
        "第二季度": "Q2",
        "二季度": "Q2",
        "2季度": "Q2",
        "第三季度": "Q3",
        "三季度": "Q3",
        "3季度": "Q3",
        "第四季度": "Q4",
        "四季度": "Q4",
        "4季度": "Q4",
    }
    suffix = quarter_map.get(label)
    return f"{year}{suffix}" if suffix else ""


def _classification_hint_from_text(value: str) -> str:
    if re.search(r"分产品|产品|product", value, flags=re.IGNORECASE):
        return "product"
    if re.search(r"分行业|行业|industry", value, flags=re.IGNORECASE):
        return "industry"
    if re.search(r"分地区|地区|区域|region", value, flags=re.IGNORECASE):
        return "region"
    if re.search(r"其他|other", value, flags=re.IGNORECASE):
        return "other"
    return ""


def _resolve_under_root(path: Path, root: Path) -> tuple[Path, Path]:
    if _contains_parent_reference(path) or _contains_parent_reference(root):
        raise LocalStructuredTablePathBoundaryError("path traversal is not allowed")
    root_resolved = root.resolve(strict=False)
    candidate = path if path.is_absolute() else root_resolved / path
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise LocalStructuredTablePathBoundaryError("local csv path escapes repo root") from exc
    if _path_string_is_forbidden(str(path)) or _path_string_is_forbidden(str(resolved)):
        raise LocalStructuredTableSecretError("local csv path contains secret-like data: <masked>")
    return resolved, root_resolved


def _relative_posix_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _contains_parent_reference(path: Path) -> bool:
    return any(part == ".." for part in path.parts)


def _path_string_is_forbidden(value: str) -> bool:
    return bool(_DOTFILE_CONFIG_RE.search(value) or _LOCAL_SECRET_PATH_RE.search(value) or _REMOTE_CONTROL_RE.search(value))


def _assert_non_empty_string(value: Any, field_name: str) -> None:
    if not _non_empty_string(value):
        raise LocalStructuredTableValidationError(f"{field_name} must be a non-empty string")


def _assert_no_forbidden_recommendation_keys(payload: Any) -> None:
    for key in _walk_keys(payload):
        if str(key).lower() in FORBIDDEN_RECOMMENDATION_KEYS:
            raise LocalStructuredTableValidationError("normalized table payload contains forbidden recommendation keys")


def _assert_no_secret_like_payload(payload: Any) -> None:
    finding = _first_secret_like_finding(payload, "$")
    if finding:
        raise LocalStructuredTableSecretError(f"normalized table payload contains secret-like data at {finding}: <masked>")


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
