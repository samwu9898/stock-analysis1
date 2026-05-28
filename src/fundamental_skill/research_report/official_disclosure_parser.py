# -*- coding: utf-8 -*-
"""Minimal local official disclosure text parser.

This module only handles caller-provided local text files and isolated JSON
payloads. It has no live data-source integration and no report-chain side
effects.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OFFICIAL_DISCLOSURE_VERSION = "official_disclosure_facts.v1"
PARSER_VERSION = "minimal_official_disclosure_parser.v1"
DEFAULT_OFFICIAL_DISCLOSURE_OUTPUT_DIR = "output/official_disclosures"

SOURCE_ORIGIN = "local_downloaded_official_disclosure"
OUTPUT_FILENAME = "official_disclosure_facts.json"

DOCUMENT_TYPES = {
    "annual_report",
    "semiannual_report",
    "quarterly_report",
    "earnings_preannouncement",
    "earnings_flash",
    "guidance_or_operating_update",
    "major_contract_or_order",
    "regulatory_inquiry",
    "regulatory_penalty",
    "shareholder_reduction",
    "share_pledge",
    "major_asset_restructuring",
    "related_party_transaction",
    "litigation_arbitration",
    "auditor_opinion_change",
    "other_official_disclosure",
}

EVIDENCE_TIERS = {
    "L1_official_disclosure",
    "L2_multi_source_consistent",
    "L3_single_source_candidate",
    "L4_unsupported_or_missing",
}

EXTRACTION_CONFIDENCE = {"high", "medium", "low"}
TEXT_EXTRACTION_METHODS = {"plain_text"}
TEXT_EXTRACTION_QUALITY = {"high", "medium", "low"}
SUPPORTED_TEXT_SUFFIXES = {".txt", ".md", ".html", ".htm"}
MAX_LOCAL_TEXT_BYTES = 2_000_000

FORBIDDEN_RECOMMENDATION_KEYS = {
    "buy",
    "sell",
    "target_price",
    "position",
    "portfolio_weight",
}

_CODE_RE = re.compile(r"^\d{6}$")
_SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")
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
    r"|/Users/[^/\s]+/[^\"'\s<>]*(?:\.ssh|\.aws|\.azure|secrets?|credentials?)/[^\"'\s<>]*",
    flags=re.IGNORECASE,
)
_SECTION_HEADING_RE = re.compile(r"^\s*(第[一二三四五六七八九十\d]+[章节]|[一二三四五六七八九十\d]+[、.．])")
_DATE_RE = re.compile(r"(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})日?")


class OfficialDisclosureParserError(RuntimeError):
    """Base error for official disclosure parser operations."""


class OfficialDisclosureValidationError(OfficialDisclosureParserError):
    """Raised when a parser payload fails schema or policy validation."""


class OfficialDisclosurePathBoundaryError(OfficialDisclosureParserError):
    """Raised when a requested local path escapes its allowed boundary."""


class OfficialDisclosureSecretError(OfficialDisclosureParserError):
    """Raised when payload or text contains secret-like data."""


def build_official_disclosure_facts(
    *,
    code: str,
    company_name: str,
    source_documents: list[dict],
    extracted_facts: list[dict],
    created_at: str | None = None,
    extraction_warnings: list[str] | None = None,
    data_quality_caveats: list[str] | None = None,
) -> dict:
    """Build and validate an in-memory official disclosure facts payload."""

    payload = {
        "version": OFFICIAL_DISCLOSURE_VERSION,
        "code": code,
        "company_name": company_name,
        "created_at": created_at or _utc_now(),
        "parser_version": PARSER_VERSION,
        "source_documents": copy.deepcopy(source_documents),
        "extracted_facts": copy.deepcopy(extracted_facts),
        "extraction_warnings": list(extraction_warnings or []),
        "data_quality_caveats": list(data_quality_caveats or []),
        "not_for_trading_advice": True,
    }
    validate_official_disclosure_facts(payload)
    return payload


def validate_official_disclosure_facts(payload: dict) -> None:
    """Validate the top-level official disclosure facts payload."""

    if not isinstance(payload, dict):
        raise OfficialDisclosureValidationError("official disclosure payload must be a dict")
    if payload.get("version") != OFFICIAL_DISCLOSURE_VERSION:
        raise OfficialDisclosureValidationError("official disclosure version is unsupported")
    if payload.get("parser_version") != PARSER_VERSION:
        raise OfficialDisclosureValidationError("official disclosure parser version is unsupported")
    if not isinstance(payload.get("code"), str) or not _CODE_RE.fullmatch(payload["code"]):
        raise OfficialDisclosureValidationError("code must be a 6 digit string")
    if not isinstance(payload.get("company_name"), str) or not payload["company_name"]:
        raise OfficialDisclosureValidationError("company_name must be a non-empty string")
    if not isinstance(payload.get("created_at"), str) or not payload["created_at"]:
        raise OfficialDisclosureValidationError("created_at must be a non-empty string")
    if payload.get("not_for_trading_advice") is not True:
        raise OfficialDisclosureValidationError("not_for_trading_advice must be true")
    if not isinstance(payload.get("source_documents"), list):
        raise OfficialDisclosureValidationError("source_documents must be a list")
    if not isinstance(payload.get("extracted_facts"), list):
        raise OfficialDisclosureValidationError("extracted_facts must be a list")
    if not isinstance(payload.get("extraction_warnings"), list):
        raise OfficialDisclosureValidationError("extraction_warnings must be a list")
    if not isinstance(payload.get("data_quality_caveats"), list):
        raise OfficialDisclosureValidationError("data_quality_caveats must be a list")

    _assert_no_forbidden_recommendation_keys(payload)
    _assert_no_secret_like_payload(payload)

    seen_document_ids: set[str] = set()
    for doc in payload["source_documents"]:
        validate_source_document(doc)
        document_id = doc["source_document_id"]
        if document_id in seen_document_ids:
            raise OfficialDisclosureValidationError(f"duplicate source_document_id: {document_id}")
        seen_document_ids.add(document_id)

    seen_fact_ids: set[str] = set()
    for fact in payload["extracted_facts"]:
        validate_extracted_fact(fact, valid_document_ids=seen_document_ids)
        fact_id = fact["fact_id"]
        if fact_id in seen_fact_ids:
            raise OfficialDisclosureValidationError(f"duplicate fact_id: {fact_id}")
        seen_fact_ids.add(fact_id)


def validate_source_document(doc: dict) -> None:
    """Validate one source document record."""

    if not isinstance(doc, dict):
        raise OfficialDisclosureValidationError("source document must be a dict")
    required = {
        "source_document_id",
        "document_type",
        "title",
        "report_period",
        "disclosure_date",
        "source_origin",
        "source_uri_or_path",
        "sha256",
        "text_extraction_method",
        "text_extraction_quality",
        "caveats",
    }
    missing = required - set(doc)
    if missing:
        raise OfficialDisclosureValidationError(f"source document missing keys: {sorted(missing)}")
    if not _non_empty_string(doc["source_document_id"]):
        raise OfficialDisclosureValidationError("source_document_id must be a non-empty string")
    if doc["document_type"] not in DOCUMENT_TYPES:
        raise OfficialDisclosureValidationError("document_type is unsupported")
    if not isinstance(doc["title"], str):
        raise OfficialDisclosureValidationError("title must be a string")
    if not isinstance(doc["report_period"], str):
        raise OfficialDisclosureValidationError("report_period must be a string")
    if not isinstance(doc["disclosure_date"], str):
        raise OfficialDisclosureValidationError("disclosure_date must be a string")
    if doc["source_origin"] != SOURCE_ORIGIN:
        raise OfficialDisclosureValidationError("source_origin is unsupported")
    if not isinstance(doc["source_uri_or_path"], str):
        raise OfficialDisclosureValidationError("source_uri_or_path must be a string")
    if not isinstance(doc["sha256"], str) or not _SHA256_RE.fullmatch(doc["sha256"]):
        raise OfficialDisclosureValidationError("sha256 must be a hex sha256 string")
    if doc["text_extraction_method"] not in TEXT_EXTRACTION_METHODS:
        raise OfficialDisclosureValidationError("text_extraction_method is unsupported")
    if doc["text_extraction_quality"] not in TEXT_EXTRACTION_QUALITY:
        raise OfficialDisclosureValidationError("text_extraction_quality is unsupported")
    if not isinstance(doc["caveats"], list) or not all(isinstance(item, str) for item in doc["caveats"]):
        raise OfficialDisclosureValidationError("caveats must be a list of strings")
    _assert_no_forbidden_recommendation_keys(doc)
    _assert_no_secret_like_payload(doc)


def validate_extracted_fact(fact: dict, *, valid_document_ids: set[str]) -> None:
    """Validate one extracted fact record."""

    if not isinstance(fact, dict):
        raise OfficialDisclosureValidationError("extracted fact must be a dict")
    required = {
        "fact_id",
        "field_path",
        "value",
        "unit",
        "period",
        "source_document_id",
        "source_section",
        "source_page_or_anchor",
        "evidence_tier",
        "extraction_confidence",
        "needs_human_review",
        "caveats",
    }
    missing = required - set(fact)
    if missing:
        raise OfficialDisclosureValidationError(f"extracted fact missing keys: {sorted(missing)}")
    if not _non_empty_string(fact["fact_id"]):
        raise OfficialDisclosureValidationError("fact_id must be a non-empty string")
    if not _non_empty_string(fact["field_path"]):
        raise OfficialDisclosureValidationError("field_path must be a non-empty string")
    if fact["unit"] is not None and not isinstance(fact["unit"], str):
        raise OfficialDisclosureValidationError("unit must be a string or null")
    if not isinstance(fact["period"], str):
        raise OfficialDisclosureValidationError("period must be a string")
    if fact["source_document_id"] not in valid_document_ids:
        raise OfficialDisclosureValidationError("extracted fact references an unknown source_document_id")
    if not isinstance(fact["source_section"], str):
        raise OfficialDisclosureValidationError("source_section must be a string")
    if not isinstance(fact["source_page_or_anchor"], str):
        raise OfficialDisclosureValidationError("source_page_or_anchor must be a string")
    if fact["evidence_tier"] not in EVIDENCE_TIERS:
        raise OfficialDisclosureValidationError("evidence_tier is unsupported")
    if fact["extraction_confidence"] not in EXTRACTION_CONFIDENCE:
        raise OfficialDisclosureValidationError("extraction_confidence is unsupported")
    if not isinstance(fact["needs_human_review"], bool):
        raise OfficialDisclosureValidationError("needs_human_review must be a boolean")
    if not isinstance(fact["caveats"], list) or not all(isinstance(item, str) for item in fact["caveats"]):
        raise OfficialDisclosureValidationError("caveats must be a list of strings")

    if fact["evidence_tier"] == "L1_official_disclosure":
        has_location = bool(fact["source_section"].strip() or fact["source_page_or_anchor"].strip())
        if not has_location:
            raise OfficialDisclosureValidationError("L1 official disclosure facts require source location")

    _assert_no_forbidden_recommendation_keys(fact)
    _assert_no_secret_like_payload(fact)


def read_local_official_text(path: Path, *, repo_root: Path | None = None) -> dict:
    """Read one explicit local plain-text disclosure file."""

    root = Path(repo_root) if repo_root is not None else Path.cwd()
    resolved_path, root_resolved = _resolve_under_root(Path(path), root)
    if not resolved_path.exists() or not resolved_path.is_file():
        raise OfficialDisclosurePathBoundaryError("local disclosure text path must point to a file")
    if resolved_path.suffix.lower() not in SUPPORTED_TEXT_SUFFIXES:
        raise OfficialDisclosureParserError("unsupported local disclosure text suffix")

    raw = resolved_path.read_bytes()
    size_bytes = len(raw)
    if size_bytes > MAX_LOCAL_TEXT_BYTES:
        raise OfficialDisclosureParserError("local disclosure text is too large")
    if b"\x00" in raw:
        raise OfficialDisclosureParserError("local disclosure text appears to be binary")

    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise OfficialDisclosureParserError("local disclosure text must be utf-8 text") from exc
    _assert_no_secret_like_payload(text)

    caveats = []
    if resolved_path.suffix.lower() in {".html", ".htm"}:
        caveats.append("HTML file was read as plain text; markup was not structurally parsed.")
    if not text.strip():
        caveats.append("Local disclosure text is empty after decoding.")

    relative_path = _relative_posix_path(resolved_path, root_resolved)
    return {
        "source_document_id": "",
        "document_type": "other_official_disclosure",
        "title": resolved_path.stem,
        "report_period": "",
        "disclosure_date": "",
        "source_origin": SOURCE_ORIGIN,
        "source_uri_or_path": relative_path,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "text_extraction_method": "plain_text",
        "text_extraction_quality": "medium",
        "caveats": caveats,
        "text": text,
        "size_bytes": size_bytes,
    }


def extract_main_business_candidate(text: str, *, source_document_id: str) -> dict | None:
    """Extract a conservative main-business candidate from local text."""

    if not isinstance(text, str) or not text.strip():
        return None
    if not _non_empty_string(source_document_id):
        raise OfficialDisclosureValidationError("source_document_id must be a non-empty string")

    lines = [line.strip() for line in text.splitlines()]
    section_patterns = (
        re.compile(r"(主营业务|主要业务|公司业务概要|主营业务分析|main\s+business)", flags=re.IGNORECASE),
        re.compile(r"(经营情况讨论与分析|管理层讨论与分析)"),
    )
    for index, line in enumerate(lines):
        matched_label = _matching_section_label(line, section_patterns)
        if not matched_label:
            continue
        snippet = _collect_section_snippet(lines, index, matched_label)
        if not snippet:
            continue
        caveats = ["Candidate extracted from a simple local text section hint; manual review is required."]
        if len(snippet) >= 500:
            caveats.append("Extracted text was truncated to 500 characters.")
        return {
            "fact_id": "fact_main_business_001",
            "field_path": "basic_info.main_business_official_text",
            "value": snippet[:500],
            "unit": None,
            "period": "",
            "source_document_id": source_document_id,
            "source_section": matched_label,
            "source_page_or_anchor": "",
            "evidence_tier": "L1_official_disclosure",
            "extraction_confidence": "medium",
            "needs_human_review": True,
            "caveats": caveats,
        }
    return None


def extract_periodic_report_basics(text: str, *, source_document_id: str) -> dict:
    """Extract conservative periodic-report metadata hints from local text."""

    if not isinstance(text, str):
        text = ""
    if not _non_empty_string(source_document_id):
        raise OfficialDisclosureValidationError("source_document_id must be a non-empty string")

    compact = " ".join(line.strip() for line in text.splitlines() if line.strip())
    document_type = _detect_document_type(compact)
    report_period = _detect_report_period(compact, document_type)
    disclosure_date = _detect_disclosure_date(compact)
    caveats = []
    if document_type == "other_official_disclosure":
        caveats.append("Periodic report type was not confidently detected.")
    if not report_period:
        caveats.append("Report period was not confidently detected.")
    if not disclosure_date:
        caveats.append("Disclosure date was not confidently detected.")

    confidence = "medium" if document_type != "other_official_disclosure" and report_period else "low"
    return {
        "source_document_id": source_document_id,
        "document_type": document_type,
        "report_period": report_period,
        "disclosure_date": disclosure_date,
        "extraction_confidence": confidence,
        "needs_human_review": True,
        "caveats": caveats,
    }


def write_official_disclosure_facts(payload: dict, path: Path) -> Path:
    """Validate and write official disclosure facts as pretty JSON."""

    validate_official_disclosure_facts(payload)
    _assert_no_secret_like_payload(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    target = _resolve_output_path(Path(path))
    if target.suffix.lower() != ".json":
        raise OfficialDisclosurePathBoundaryError("official disclosure writer only writes JSON files")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def read_official_disclosure_facts(path: Path) -> dict:
    """Read, validate, and return official disclosure facts JSON."""

    source = _resolve_output_path(Path(path))
    if source.suffix.lower() != ".json":
        raise OfficialDisclosurePathBoundaryError("official disclosure reader only reads JSON files")
    payload = json.loads(source.read_text(encoding="utf-8"))
    validate_official_disclosure_facts(payload)
    return payload


def _detect_document_type(text: str) -> str:
    if re.search(r"(半年度报告|中期报告|semi[-\s]?annual)", text, flags=re.IGNORECASE):
        return "semiannual_report"
    if re.search(r"(第一季度报告|半?年度?第三季度报告|第三季度报告|季度报告|quarterly)", text, flags=re.IGNORECASE):
        return "quarterly_report"
    if re.search(r"(年度报告|annual\s+report)", text, flags=re.IGNORECASE):
        return "annual_report"
    return "other_official_disclosure"


def _detect_report_period(text: str, document_type: str) -> str:
    match = re.search(r"(\d{4})\s*(?:年\s*)?年度报告", text)
    if match:
        return f"{match.group(1)}A"
    match = re.search(r"(\d{4})\s*年\s*(半年度报告|中期报告)", text)
    if match:
        return f"{match.group(1)}H1"
    match = re.search(r"(\d{4})\s*年\s*第?([一二三四1-4])季度报告", text)
    if match:
        quarter = {"一": "1", "二": "2", "三": "3", "四": "4"}.get(match.group(2), match.group(2))
        return f"{match.group(1)}Q{quarter}"
    match = re.search(r"报告期(?:间)?\s*[:：]\s*([0-9]{4}(?:[-年][0-9]{1,2}[-月][0-9]{1,2}日?)?|[0-9]{4}\s*年度)", text)
    if match:
        return _normalize_date_like(match.group(1))
    return ""


def _detect_disclosure_date(text: str) -> str:
    match = re.search(r"(披露日期|公告日期|发布日期)\s*[:：]\s*" + _DATE_RE.pattern, text)
    if match:
        return _format_date_parts(match.group(2), match.group(3), match.group(4))
    match = re.search(r"(\d{4})年年度报告.*?(" + _DATE_RE.pattern + r")", text)
    if match:
        return _format_date_parts(match.group(3), match.group(4), match.group(5))
    return ""


def _normalize_date_like(value: str) -> str:
    match = _DATE_RE.fullmatch(value.strip())
    if match:
        return _format_date_parts(match.group(1), match.group(2), match.group(3))
    return re.sub(r"\s+", "", value.strip())


def _format_date_parts(year: str, month: str, day: str) -> str:
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _matching_section_label(line: str, patterns: tuple[re.Pattern[str], ...]) -> str:
    for pattern in patterns:
        match = pattern.search(line)
        if match:
            return match.group(1)
    return ""


def _collect_section_snippet(lines: list[str], start_index: int, matched_label: str) -> str:
    collected: list[str] = []
    first_line = lines[start_index]
    after_label = re.split(re.escape(matched_label), first_line, maxsplit=1)[-1]
    after_label = after_label.lstrip(" ：:.-　")
    if after_label:
        collected.append(after_label)
    for line in lines[start_index + 1 :]:
        if not line:
            if collected:
                break
            continue
        if collected and _SECTION_HEADING_RE.match(line):
            break
        collected.append(line)
        if sum(len(item) for item in collected) >= 500:
            break
    return _squash_text(" ".join(collected))[:500]


def _squash_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _resolve_under_root(path: Path, root: Path) -> tuple[Path, Path]:
    if _contains_parent_reference(path) or _contains_parent_reference(root):
        raise OfficialDisclosurePathBoundaryError("path traversal is not allowed")
    root_resolved = root.resolve(strict=False)
    candidate = path if path.is_absolute() else root_resolved / path
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise OfficialDisclosurePathBoundaryError("local disclosure path escapes repo root") from exc
    if _path_string_is_forbidden(str(path)) or _path_string_is_forbidden(str(resolved)):
        raise OfficialDisclosureSecretError("local disclosure path contains secret-like data: <masked>")
    return resolved, root_resolved


def _resolve_output_path(path: Path) -> Path:
    if _contains_parent_reference(path):
        raise OfficialDisclosurePathBoundaryError("path traversal is not allowed")
    if _path_string_is_forbidden(str(path)):
        raise OfficialDisclosureSecretError("official disclosure path contains secret-like data: <masked>")
    return path.resolve(strict=False)


def _relative_posix_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _contains_parent_reference(path: Path) -> bool:
    return any(part == ".." for part in path.parts)


def _path_string_is_forbidden(value: str) -> bool:
    return bool(_DOTFILE_CONFIG_RE.search(value) or _LOCAL_SECRET_PATH_RE.search(value) or _REMOTE_CONTROL_RE.search(value))


def _assert_no_forbidden_recommendation_keys(payload: Any) -> None:
    for key in _walk_keys(payload):
        if str(key).lower() in FORBIDDEN_RECOMMENDATION_KEYS:
            raise OfficialDisclosureValidationError("official disclosure payload contains forbidden recommendation keys")


def _assert_no_secret_like_payload(payload: Any) -> None:
    finding = _first_secret_like_finding(payload, "$")
    if finding:
        raise OfficialDisclosureSecretError(f"official disclosure payload contains secret-like data at {finding}: <masked>")


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
