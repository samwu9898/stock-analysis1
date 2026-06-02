# -*- coding: utf-8 -*-
"""Official cached artifact evidence locator thin slice.

This module consumes ``official_disclosure_artifact_cache.v1`` and emits
locator-only metadata from cached official PDF text layers. It does not write
files, call live services, inspect image layers, or produce fact records.
"""

from __future__ import annotations

import copy
import hashlib
import re
from collections.abc import Mapping, Sequence
from io import BytesIO
from pathlib import Path
from typing import Any

from .official_artifact_cache_acquisition import (
    ARTIFACT_CACHE_SCHEMA_VERSION,
    ARTIFACT_STATUS_CACHED,
    MAX_ARTIFACT_BYTES,
    PDF_MAGIC_BYTES,
    PROVIDER_NAME,
    OfficialArtifactCacheAcquisitionError,
    validate_official_disclosure_artifact_cache,
)


OFFICIAL_ARTIFACT_EVIDENCE_LOCATOR_SCHEMA_VERSION = "official_artifact_evidence_locator.v1"
OFFICIAL_ARTIFACT_EVIDENCE_LOCATOR_ITEM_SCHEMA_VERSION = "official_artifact_evidence_locator_item.v1"
OFFICIAL_ARTIFACT_TEXT_HIT_SCHEMA_VERSION = "official_artifact_text_hit.v1"
OFFICIAL_ARTIFACT_SECTION_LOCATOR_SCHEMA_VERSION = "official_artifact_section_locator.v1"

EXTRACTION_SCOPE_LOCATOR_TEXT_LAYER_ONLY = "locator_text_layer_only"

LOCATOR_CONFIDENCE_HIGH = "high"
LOCATOR_CONFIDENCE_MEDIUM = "medium"
LOCATOR_CONFIDENCE_LOW = "low"
LOCATOR_CONFIDENCE_BLOCKED = "blocked"
LOCATOR_CONFIDENCE_VALUES = {
    LOCATOR_CONFIDENCE_HIGH,
    LOCATOR_CONFIDENCE_MEDIUM,
    LOCATOR_CONFIDENCE_LOW,
    LOCATOR_CONFIDENCE_BLOCKED,
}

REASON_FORBIDDEN_MARKER_DETECTED = "forbidden_marker_detected"
REASON_INVALID_ARTIFACT_CACHE = "invalid_artifact_cache"
REASON_INVALID_LOCATOR_CONFIG = "invalid_locator_config"
REASON_ARTIFACT_STATUS_NOT_CACHED = "artifact_status_not_cached"
REASON_CACHE_PATH_MISSING = "cache_path_missing"
REASON_CACHE_PATH_FORBIDDEN = "cache_path_forbidden"
REASON_CACHE_PATH_NOT_FOUND = "cache_path_not_found"
REASON_CACHE_PATH_NOT_FILE = "cache_path_not_file"
REASON_CACHE_PATH_NOT_PDF = "cache_path_not_pdf"
REASON_CACHE_PATH_READ_FAILURE = "cache_path_read_failure"
REASON_SHA256_MISSING = "sha256_missing"
REASON_SHA256_MISMATCH = "sha256_mismatch"
REASON_FILE_SIZE_BYTES_MISSING = "file_size_bytes_missing"
REASON_FILE_SIZE_BYTES_MISMATCH = "file_size_bytes_mismatch"
REASON_FILE_SIZE_BYTES_NON_POSITIVE = "file_size_bytes_non_positive"
REASON_FILE_SIZE_BYTES_EXCEEDS_LIMIT = "file_size_bytes_exceeds_limit"
REASON_PDF_MAGIC_MISMATCH = "pdf_magic_mismatch"
REASON_PDF_TEXT_LAYER_DEPENDENCY_UNAVAILABLE = "pdf_text_layer_dependency_unavailable"
REASON_PDF_TEXT_LAYER_READ_FAILURE = "pdf_text_layer_read_failure"
REASON_PDF_TEXT_LAYER_UNAVAILABLE = "pdf_text_layer_unavailable"
REASON_LOCATOR_OUTPUT_FORBIDDEN_MARKER = "locator_output_forbidden_marker"
REASON_METRIC_LOCATOR_KEYWORD_FORBIDDEN = "metric_locator_keyword_forbidden"

DEFAULT_MAX_SNIPPET_CHARS = 200
DEFAULT_MAX_HITS_PER_TYPE = 5

DEFAULT_SAFE_KEYWORDS = (
    "目录",
    "重要提示",
    "公司简介",
    "管理层讨论与分析",
    "经营情况讨论与分析",
    "主营业务",
    "财务报表",
)

DEFAULT_SECTION_HEADINGS = (
    ("table_of_contents", "目录"),
    ("important_notice", "重要提示"),
    ("company_profile", "公司简介"),
    ("management_discussion", "管理层讨论与分析"),
    ("operation_discussion", "经营情况讨论与分析"),
    ("principal_business", "主营业务"),
    ("financial_statements", "财务报表"),
    ("consolidated_balance_sheet", "合并资产负债表"),
    ("consolidated_income_statement", "合并利润表"),
    ("consolidated_cashflow_statement", "合并现金流量表"),
)

DEFAULT_REPORT_TITLE_KEYWORDS = (
    "年度报告",
    "第一季度报告",
    "季度报告",
    "半年度报告",
    "Annual Report",
    "Quarterly Report",
    "Q1 Report",
    "Interim Report",
)

ANNOUNCEMENT_TYPE_TITLE_KEYWORDS = {
    "annual_report": ("年度报告", "Annual Report"),
    "quarterly_report": ("季度报告", "第一季度报告", "Quarterly Report", "Q1 Report"),
    "q1_report": ("第一季度报告", "Quarterly Report", "Q1 Report"),
    "semi_annual_report": ("半年度报告", "Interim Report", "Semi-Annual Report"),
    "half_year_report": ("半年度报告", "Interim Report", "Semi-Annual Report"),
}

FORBIDDEN_METRIC_LOCATOR_KEYWORDS = (
    "revenue",
    "operating revenue",
    "net profit",
    "net income",
    "profit attributable",
    "operating cash flow",
    "cash flow from operating activities",
    "EPS",
    "earnings per share",
    "营业收入",
    "主营业务收入",
    "净利润",
    "归母净利润",
    "归属于上市公司股东的净利润",
    "经营现金流",
    "经营活动产生的现金流量净额",
    "每股收益",
    "基本每股收益",
    "稀释每股收益",
)

FORBIDDEN_ENGLISH_MARKERS = (
    "token",
    ".env",
    "tushare_token",
    "official_verified",
    "official_metric_fact",
    "provider_official_conflict",
    "verified_metric",
    "official_value",
    "metric_value",
    "reconciliation_status",
    "Report V1",
    "formal report",
    "accepted manifest write",
    "output baseline write",
    "fixture write",
    "buy",
    "sell",
    "hold",
    "target price",
    "portfolio",
    "position",
    "technical signal",
    "trading advice",
    "investment advice",
    "OCR",
    "table extractor",
    "table extraction",
    "metric extraction",
    "revenue amount",
    "net profit amount",
    "operating cash flow amount",
    "EPS extraction",
)
FORBIDDEN_CJK_MARKERS = (
    "买入",
    "卖出",
    "持有",
    "目标价",
    "仓位",
    "组合",
    "技术信号",
    "投资建议",
    "正式研报",
    "输出基线",
    "写入fixture",
    "写入accepted manifest",
    "读取token",
    "读取.env",
    "读取tushare_token",
    "OCR",
    "表格抽取",
    "表格解析",
    "指标抽取",
    "营业收入数值",
    "归母净利润数值",
    "经营现金流数值",
    "每股收益抽取",
    "官方指标事实",
    "指标核验",
    "一致性核验",
)
WORD_MARKERS = {"token", "buy", "sell", "hold", "portfolio", "position"}
IDENTIFIER_SAFE_WORD_MARKERS = {"buy", "sell", "hold"}
ALLOWED_FLAG_MARKERS = {"not_official_verified", "not_for_trading_advice"}
CAMEL_SPLIT_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


class OfficialArtifactEvidenceLocatorError(ValueError):
    """Raised when evidence locating must fail closed."""


class OfficialArtifactEvidenceLocatorSafetyError(OfficialArtifactEvidenceLocatorError):
    """Raised when nested input contains a forbidden marker."""

    def __init__(self, marker: str) -> None:
        super().__init__("forbidden_marker")
        self.marker = marker


def build_official_artifact_evidence_locator(
    artifact_cache: Any,
    *,
    locator_config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build locator-only metadata from cached official PDF artifacts."""

    cache_snapshot = _copy_jsonlike(artifact_cache)
    result = _empty_locator_result(cache_snapshot if isinstance(cache_snapshot, Mapping) else None)
    try:
        config = _normalize_locator_config(locator_config)
        assert_no_official_artifact_evidence_locator_forbidden_markers(cache_snapshot)
    except OfficialArtifactEvidenceLocatorSafetyError:
        result["blocked_reasons"].append(REASON_FORBIDDEN_MARKER_DETECTED)
        validate_official_artifact_evidence_locator(result)
        return result
    except OfficialArtifactEvidenceLocatorError as exc:
        result["blocked_reasons"].append(_clean_string(exc) or REASON_INVALID_LOCATOR_CONFIG)
        validate_official_artifact_evidence_locator(result)
        return result

    try:
        validate_official_disclosure_artifact_cache(cache_snapshot)
    except OfficialArtifactCacheAcquisitionError as exc:
        if not _can_fail_closed_per_item(cache_snapshot, exc):
            result["blocked_reasons"].append(REASON_INVALID_ARTIFACT_CACHE)
            validate_official_artifact_evidence_locator(result)
            return result
        result["blocked_reasons"].append(REASON_INVALID_ARTIFACT_CACHE)

    assert isinstance(cache_snapshot, Mapping)
    result["blocked_reasons"].extend(_safe_list(cache_snapshot.get("blocked_reasons")))
    result["caveats"] = _dedupe_preserve_order(result["caveats"] + _safe_list(cache_snapshot.get("caveats")))

    for item in _safe_mapping_list(cache_snapshot.get("artifact_items")):
        if item.get("artifact_status") != ARTIFACT_STATUS_CACHED:
            skipped = _skipped_locator_item_from_artifact_item(item, [REASON_ARTIFACT_STATUS_NOT_CACHED])
            result["skipped_items"].append(skipped)
            result["blocked_reasons"].extend(_safe_list(skipped.get("caveats")))
            continue
        locator_item = locate_evidence_in_cached_artifact(item, locator_config=config)
        result["locator_items"].append(locator_item)
        if locator_item.get("locator_confidence") == LOCATOR_CONFIDENCE_BLOCKED:
            result["blocked_reasons"].extend(_safe_list(locator_item.get("caveats")))

    for skipped_item in _safe_mapping_list(cache_snapshot.get("skipped_items")):
        skipped = _skipped_locator_item_from_artifact_item(skipped_item, [REASON_ARTIFACT_STATUS_NOT_CACHED])
        result["skipped_items"].append(skipped)
        result["blocked_reasons"].extend(_safe_list(skipped.get("caveats")))

    result["blocked_reasons"] = _dedupe_preserve_order(result["blocked_reasons"])
    result["caveats"] = _dedupe_preserve_order(result["caveats"])
    validate_official_artifact_evidence_locator(result)
    return result


def validate_official_artifact_evidence_locator(locator_result: Any) -> None:
    """Validate locator result shape and safety markers."""

    if not isinstance(locator_result, Mapping):
        raise OfficialArtifactEvidenceLocatorError("invalid_locator_result")
    if locator_result.get("schema_version") != OFFICIAL_ARTIFACT_EVIDENCE_LOCATOR_SCHEMA_VERSION:
        raise OfficialArtifactEvidenceLocatorError("invalid_locator_schema_version")
    _require_true_bool(locator_result, "not_official_verified", "$")
    _require_true_bool(locator_result, "not_for_trading_advice", "$")
    for key in ("locator_items", "skipped_items", "blocked_reasons", "caveats"):
        if not isinstance(locator_result.get(key), list):
            raise OfficialArtifactEvidenceLocatorError(f"invalid_{key}")
    for index, item in enumerate(locator_result["locator_items"]):
        validate_official_artifact_evidence_locator_item(item, path=f"$.locator_items[{index}]")
    for index, item in enumerate(locator_result["skipped_items"]):
        validate_official_artifact_evidence_locator_item(item, path=f"$.skipped_items[{index}]")
    _assert_no_disallowed_output_keys(locator_result)
    assert_no_official_artifact_evidence_locator_forbidden_markers(locator_result)


def validate_official_artifact_evidence_locator_item(item: Any, *, path: str = "$") -> None:
    """Validate a single locator item or skipped locator item."""

    if not isinstance(item, Mapping):
        raise OfficialArtifactEvidenceLocatorError(f"{path}:invalid_locator_item")
    required = (
        "schema_version",
        "artifact_id",
        "source_title",
        "source_url",
        "source_domain",
        "disclosure_date",
        "stock_code",
        "company_name_hint",
        "period_key",
        "period_end_date",
        "announcement_type",
        "source_artifact_sha256",
        "source_file_size_bytes",
        "cache_filename",
        "text_layer_available",
        "report_title_hits",
        "company_name_hits",
        "stock_code_hits",
        "report_period_hits",
        "section_heading_hits",
        "keyword_hits",
        "locator_confidence",
        "extraction_scope",
        "not_official_verified",
        "not_for_trading_advice",
        "caveats",
    )
    for key in required:
        if key not in item:
            raise OfficialArtifactEvidenceLocatorError(f"{path}:{key}_missing")
    if item.get("schema_version") != OFFICIAL_ARTIFACT_EVIDENCE_LOCATOR_ITEM_SCHEMA_VERSION:
        raise OfficialArtifactEvidenceLocatorError(f"{path}:invalid_locator_item_schema_version")
    if not isinstance(item.get("text_layer_available"), bool):
        raise OfficialArtifactEvidenceLocatorError(f"{path}:invalid_text_layer_available")
    if item.get("locator_confidence") not in LOCATOR_CONFIDENCE_VALUES:
        raise OfficialArtifactEvidenceLocatorError(f"{path}:invalid_locator_confidence")
    if item.get("extraction_scope") != EXTRACTION_SCOPE_LOCATOR_TEXT_LAYER_ONLY:
        raise OfficialArtifactEvidenceLocatorError(f"{path}:invalid_extraction_scope")
    for key in (
        "report_title_hits",
        "company_name_hits",
        "stock_code_hits",
        "report_period_hits",
        "keyword_hits",
        "caveats",
    ):
        if not isinstance(item.get(key), list):
            raise OfficialArtifactEvidenceLocatorError(f"{path}:invalid_{key}")
    if not isinstance(item.get("section_heading_hits"), list):
        raise OfficialArtifactEvidenceLocatorError(f"{path}:invalid_section_heading_hits")
    for hit_key in ("report_title_hits", "company_name_hits", "stock_code_hits", "report_period_hits", "keyword_hits"):
        for index, hit in enumerate(item[hit_key]):
            _validate_text_hit(hit, path=f"{path}.{hit_key}[{index}]")
    for index, section_hit in enumerate(item["section_heading_hits"]):
        _validate_section_hit(section_hit, path=f"{path}.section_heading_hits[{index}]")
    _require_true_bool(item, "not_official_verified", path)
    _require_true_bool(item, "not_for_trading_advice", path)
    _assert_no_disallowed_output_keys(item)
    assert_no_official_artifact_evidence_locator_forbidden_markers(item)


def locate_evidence_in_cached_artifact(
    artifact_item: Any,
    *,
    locator_config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Locate identity, period, section, and safe keyword hits in one cached PDF."""

    try:
        config = _normalize_locator_config(locator_config)
        assert_no_official_artifact_evidence_locator_forbidden_markers(artifact_item)
    except OfficialArtifactEvidenceLocatorSafetyError:
        return _blocked_locator_item(artifact_item if isinstance(artifact_item, Mapping) else {}, [REASON_FORBIDDEN_MARKER_DETECTED])
    except OfficialArtifactEvidenceLocatorError as exc:
        return _blocked_locator_item(artifact_item if isinstance(artifact_item, Mapping) else {}, [_clean_string(exc)])

    if not isinstance(artifact_item, Mapping):
        return _blocked_locator_item({}, [REASON_INVALID_ARTIFACT_CACHE])

    cache_path, path_blockers = _validated_cache_path(artifact_item)
    if path_blockers or cache_path is None:
        return _blocked_locator_item(artifact_item, path_blockers or [REASON_CACHE_PATH_MISSING], cache_path=cache_path)

    stat_blockers = _cached_pdf_stat_blockers(cache_path, artifact_item)
    if stat_blockers:
        return _blocked_locator_item(artifact_item, stat_blockers, cache_path=cache_path)

    try:
        pdf_bytes = cache_path.read_bytes()
    except Exception:
        return _blocked_locator_item(artifact_item, [REASON_CACHE_PATH_READ_FAILURE], cache_path=cache_path)

    byte_blockers = _cached_pdf_byte_blockers(pdf_bytes, artifact_item)
    if byte_blockers:
        return _blocked_locator_item(artifact_item, byte_blockers, cache_path=cache_path)

    try:
        pages = extract_pdf_text_layer_pages(pdf_bytes)
    except OfficialArtifactEvidenceLocatorError as exc:
        reason = _clean_string(exc) or REASON_PDF_TEXT_LAYER_READ_FAILURE
        return _blocked_locator_item(artifact_item, [reason], cache_path=cache_path)

    normalized_pages = _normalize_pages(pages)
    if not any(page["text"].strip() for page in normalized_pages):
        return _blocked_locator_item(artifact_item, [REASON_PDF_TEXT_LAYER_UNAVAILABLE], cache_path=cache_path)

    identity_hits = locate_report_identity_hits(normalized_pages, artifact_item, config)
    section_heading_hits = locate_section_heading_hits(normalized_pages, config)
    keyword_hits = locate_keyword_hits(normalized_pages, config)
    locator_item = _locator_item_base(artifact_item, cache_path=cache_path)
    locator_item.update(
        {
            "text_layer_available": True,
            "report_title_hits": identity_hits["report_title_hits"],
            "company_name_hits": identity_hits["company_name_hits"],
            "stock_code_hits": identity_hits["stock_code_hits"],
            "report_period_hits": identity_hits["report_period_hits"],
            "section_heading_hits": section_heading_hits,
            "keyword_hits": keyword_hits,
            "locator_confidence": _locator_confidence(
                identity_hits=identity_hits,
                section_heading_hits=section_heading_hits,
                keyword_hits=keyword_hits,
            ),
            "caveats": _dedupe_preserve_order(
                _safe_list(locator_item.get("caveats"))
                + ["locator_metadata_only", "pdf_text_layer_only", "not_a_fact_record"]
            ),
        }
    )
    try:
        validate_official_artifact_evidence_locator_item(locator_item)
    except OfficialArtifactEvidenceLocatorSafetyError:
        return _blocked_locator_item(artifact_item, [REASON_LOCATOR_OUTPUT_FORBIDDEN_MARKER], cache_path=cache_path)
    return locator_item


def extract_pdf_text_layer_pages(pdf_bytes: bytes) -> list[dict[str, Any]]:
    """Extract minimal page text from a PDF text layer using an installed library."""

    try:
        from pypdf import PdfReader
    except Exception as exc:  # pragma: no cover - environment dependent
        raise OfficialArtifactEvidenceLocatorError(REASON_PDF_TEXT_LAYER_DEPENDENCY_UNAVAILABLE) from exc

    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        pages: list[dict[str, Any]] = []
        for index, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            pages.append({"page_number": index, "text": text})
    except Exception as exc:
        raise OfficialArtifactEvidenceLocatorError(REASON_PDF_TEXT_LAYER_READ_FAILURE) from exc

    if not any(page["text"].strip() for page in pages):
        raise OfficialArtifactEvidenceLocatorError(REASON_PDF_TEXT_LAYER_UNAVAILABLE)
    return pages


def locate_report_identity_hits(
    pages: Sequence[Any],
    artifact_item: Mapping[str, Any],
    locator_config: Mapping[str, Any] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Locate report title, company, stock code, and period text hits."""

    config = _normalize_locator_config(locator_config)
    normalized_pages = _normalize_pages(pages)
    return {
        "report_title_hits": _find_text_hits(
            normalized_pages,
            _report_title_keywords(artifact_item),
            hit_type="report_title",
            config=config,
            confidence=LOCATOR_CONFIDENCE_HIGH,
        ),
        "company_name_hits": _find_text_hits(
            normalized_pages,
            _company_keywords(artifact_item),
            hit_type="company_name",
            config=config,
            confidence=LOCATOR_CONFIDENCE_HIGH,
        ),
        "stock_code_hits": _find_text_hits(
            normalized_pages,
            _stock_code_keywords(artifact_item),
            hit_type="stock_code",
            config=config,
            confidence=LOCATOR_CONFIDENCE_HIGH,
        ),
        "report_period_hits": _find_text_hits(
            normalized_pages,
            _period_keywords(artifact_item),
            hit_type="report_period",
            config=config,
            confidence=LOCATOR_CONFIDENCE_MEDIUM,
        ),
    }


def locate_section_heading_hits(
    pages: Sequence[Any],
    locator_config: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Locate configured section headings without reading structured tables."""

    config = _normalize_locator_config(locator_config)
    normalized_pages = _normalize_pages(pages)
    hits: list[dict[str, Any]] = []
    max_hits = int(config["max_hits_per_type"])
    for section_type, heading in config["section_headings"]:
        for page in normalized_pages:
            match_index = _casefold_index(page["text"], heading)
            if match_index < 0:
                continue
            snippet = _snippet_around(
                page["text"],
                match_index,
                len(heading),
                max_chars=int(config["max_snippet_chars"]),
            )
            hits.append(
                {
                    "schema_version": OFFICIAL_ARTIFACT_SECTION_LOCATOR_SCHEMA_VERSION,
                    "section_type": section_type,
                    "heading_text": heading,
                    "page_number": page["page_number"],
                    "snippet": snippet,
                    "confidence": LOCATOR_CONFIDENCE_MEDIUM,
                    "not_official_verified": True,
                    "not_for_trading_advice": True,
                }
            )
            break
        if len(hits) >= max_hits:
            break
    return hits


def locate_keyword_hits(
    pages: Sequence[Any],
    locator_config: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Locate configured safe keywords from the PDF text layer."""

    config = _normalize_locator_config(locator_config)
    return _find_text_hits(
        _normalize_pages(pages),
        config["keywords"],
        hit_type="keyword",
        config=config,
        confidence=LOCATOR_CONFIDENCE_LOW,
    )


def assert_no_official_artifact_evidence_locator_forbidden_markers(value: Any) -> None:
    """Reject forbidden marker text anywhere in nested data."""

    marker = _find_forbidden_marker(value)
    if marker is not None:
        raise OfficialArtifactEvidenceLocatorSafetyError(_redacted_marker(marker))


def _empty_locator_result(artifact_cache: Mapping[str, Any] | None) -> dict[str, Any]:
    cache = artifact_cache if isinstance(artifact_cache, Mapping) else {}
    return {
        "schema_version": OFFICIAL_ARTIFACT_EVIDENCE_LOCATOR_SCHEMA_VERSION,
        "provider": _clean_string(cache.get("provider")) or PROVIDER_NAME,
        "stock_code": _clean_string(cache.get("stock_code")),
        "ts_code": _clean_string(cache.get("ts_code")),
        "company_name_hint": _clean_string(cache.get("company_name_hint")),
        "locator_items": [],
        "skipped_items": [],
        "blocked_reasons": [],
        "caveats": ["locator_metadata_only", "pdf_text_layer_only"],
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }


def _locator_item_base(
    artifact_item: Mapping[str, Any],
    *,
    cache_path: Path | None = None,
) -> dict[str, Any]:
    raw_cache_path = _clean_string(artifact_item.get("cache_path"))
    cache_filename = cache_path.name if cache_path is not None else (Path(raw_cache_path).name if raw_cache_path else "")
    return {
        "schema_version": OFFICIAL_ARTIFACT_EVIDENCE_LOCATOR_ITEM_SCHEMA_VERSION,
        "artifact_id": _clean_string(artifact_item.get("artifact_id")),
        "source_title": _clean_string(artifact_item.get("source_title")),
        "source_url": _clean_string(artifact_item.get("source_url")),
        "source_domain": _clean_string(artifact_item.get("source_domain")),
        "disclosure_date": _clean_string(artifact_item.get("disclosure_date")),
        "stock_code": _clean_string(artifact_item.get("stock_code")),
        "company_name_hint": _clean_string(artifact_item.get("company_name_hint")),
        "period_key": _clean_string(artifact_item.get("period_key")),
        "period_end_date": _clean_string(artifact_item.get("period_end_date")),
        "announcement_type": _clean_string(artifact_item.get("announcement_type")),
        "source_artifact_sha256": _clean_string(artifact_item.get("sha256")),
        "source_file_size_bytes": artifact_item.get("file_size_bytes"),
        "cache_filename": cache_filename,
        "text_layer_available": False,
        "report_title_hits": [],
        "company_name_hits": [],
        "stock_code_hits": [],
        "report_period_hits": [],
        "section_heading_hits": [],
        "keyword_hits": [],
        "locator_confidence": LOCATOR_CONFIDENCE_BLOCKED,
        "extraction_scope": EXTRACTION_SCOPE_LOCATOR_TEXT_LAYER_ONLY,
        "not_official_verified": True,
        "not_for_trading_advice": True,
        "caveats": _safe_list(artifact_item.get("caveats")),
    }


def _blocked_locator_item(
    artifact_item: Mapping[str, Any],
    reasons: Sequence[str],
    *,
    cache_path: Path | None = None,
) -> dict[str, Any]:
    item = _locator_item_base(artifact_item, cache_path=cache_path)
    item["caveats"] = _dedupe_preserve_order(_safe_list(item.get("caveats")) + _safe_list(list(reasons)))
    item["text_layer_available"] = False
    item["locator_confidence"] = LOCATOR_CONFIDENCE_BLOCKED
    validate_official_artifact_evidence_locator_item(item)
    return item


def _skipped_locator_item_from_artifact_item(
    artifact_item: Mapping[str, Any],
    reasons: Sequence[str],
) -> dict[str, Any]:
    item = _blocked_locator_item(artifact_item, reasons)
    item["caveats"] = _dedupe_preserve_order(
        _safe_list(item.get("caveats")) + [f"source_artifact_status:{_clean_string(artifact_item.get('artifact_status'))}"]
    )
    validate_official_artifact_evidence_locator_item(item)
    return item


def _validated_cache_path(artifact_item: Mapping[str, Any]) -> tuple[Path | None, list[str]]:
    raw_cache_path = _clean_string(artifact_item.get("cache_path"))
    if not raw_cache_path:
        return None, [REASON_CACHE_PATH_MISSING]
    try:
        cache_path = Path(raw_cache_path)
    except TypeError:
        return None, [REASON_CACHE_PATH_MISSING]
    if _is_forbidden_cache_path(cache_path):
        return None, [REASON_CACHE_PATH_FORBIDDEN]
    if cache_path.suffix.casefold() != ".pdf":
        return cache_path, [REASON_CACHE_PATH_NOT_PDF]
    try:
        resolved = cache_path.expanduser().resolve(strict=False)
    except Exception:
        return cache_path, [REASON_CACHE_PATH_FORBIDDEN]
    if not resolved.exists():
        return resolved, [REASON_CACHE_PATH_NOT_FOUND]
    if not resolved.is_file():
        return resolved, [REASON_CACHE_PATH_NOT_FILE]
    return resolved, []


def _can_fail_closed_per_item(cache_snapshot: Any, validation_error: OfficialArtifactCacheAcquisitionError) -> bool:
    if not isinstance(cache_snapshot, Mapping):
        return False
    if cache_snapshot.get("schema_version") != ARTIFACT_CACHE_SCHEMA_VERSION:
        return False
    if cache_snapshot.get("not_official_verified") is not True:
        return False
    if cache_snapshot.get("not_for_trading_advice") is not True:
        return False
    if not isinstance(cache_snapshot.get("artifact_items"), list):
        return False
    error_text = str(validation_error)
    return "cached_item_missing_cache_metadata" in error_text or "invalid_file_size_bytes" in error_text


def _cached_pdf_stat_blockers(cache_path: Path, artifact_item: Mapping[str, Any]) -> list[str]:
    expected_size = artifact_item.get("file_size_bytes")
    if not isinstance(expected_size, int):
        return [REASON_FILE_SIZE_BYTES_MISSING]
    if expected_size <= 0:
        return [REASON_FILE_SIZE_BYTES_NON_POSITIVE]
    try:
        actual_size = cache_path.stat().st_size
    except Exception:
        return [REASON_CACHE_PATH_READ_FAILURE]
    if actual_size <= 0:
        return [REASON_FILE_SIZE_BYTES_NON_POSITIVE]
    if actual_size > MAX_ARTIFACT_BYTES:
        return [REASON_FILE_SIZE_BYTES_EXCEEDS_LIMIT]
    if actual_size != expected_size:
        return [REASON_FILE_SIZE_BYTES_MISMATCH]
    return []


def _assert_no_metric_locator_keyword(value: str) -> None:
    if _has_metric_locator_keyword(value):
        raise OfficialArtifactEvidenceLocatorError(REASON_METRIC_LOCATOR_KEYWORD_FORBIDDEN)


def _has_metric_locator_keyword(value: str) -> bool:
    text = _clean_string(value)
    if not text:
        return False
    normalized = _normalize_marker_text(text)
    for marker in FORBIDDEN_METRIC_LOCATOR_KEYWORDS:
        marker_text = _clean_string(marker)
        if not marker_text:
            continue
        if _has_cjk(marker_text):
            if marker_text in text:
                return True
            continue
        marker_normalized = _normalize_marker_text(marker_text)
        if re.search(rf"(?<![a-z0-9]){re.escape(marker_normalized)}(?![a-z0-9])", normalized):
            return True
    return False


def _has_cjk(value: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in value)


def _is_forbidden_cache_path(path: Path) -> bool:
    try:
        resolved = path.expanduser().resolve(strict=False)
    except Exception:
        return True
    parts = [part.casefold() for part in resolved.parts]
    forbidden_exact = {"output", "fixtures", ".local_experiments"}
    if any(part in forbidden_exact for part in parts):
        return True
    normalized_parts = [re.sub(r"[\s\-]+", "_", part) for part in parts]
    if any(
        part == "accepted_manifest" or ("accepted" in part and "manifest" in part) or (part.endswith(".json") and "manifest" in part)
        for part in normalized_parts
    ):
        return True
    try:
        repo_root = Path(__file__).resolve().parents[3]
    except IndexError:
        return False
    return resolved == repo_root or resolved.parent == repo_root


def _cached_pdf_byte_blockers(pdf_bytes: bytes, artifact_item: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    expected_sha256 = _clean_string(artifact_item.get("sha256"))
    expected_size = artifact_item.get("file_size_bytes")
    if not expected_sha256:
        blockers.append(REASON_SHA256_MISSING)
    elif hashlib.sha256(pdf_bytes).hexdigest() != expected_sha256:
        blockers.append(REASON_SHA256_MISMATCH)
    if not isinstance(expected_size, int):
        blockers.append(REASON_FILE_SIZE_BYTES_MISSING)
    elif len(pdf_bytes) != expected_size:
        blockers.append(REASON_FILE_SIZE_BYTES_MISMATCH)
    if not pdf_bytes.startswith(PDF_MAGIC_BYTES):
        blockers.append(REASON_PDF_MAGIC_MISMATCH)
    return _dedupe_preserve_order(blockers)


def _normalize_locator_config(locator_config: Mapping[str, Any] | None) -> dict[str, Any]:
    if locator_config is None:
        raw: Mapping[str, Any] = {}
    elif isinstance(locator_config, Mapping):
        raw = locator_config
    else:
        raise OfficialArtifactEvidenceLocatorError(REASON_INVALID_LOCATOR_CONFIG)
    assert_no_official_artifact_evidence_locator_forbidden_markers(raw)
    max_snippet_chars = _coerce_positive_int(raw.get("max_snippet_chars"), DEFAULT_MAX_SNIPPET_CHARS)
    max_snippet_chars = min(max_snippet_chars, DEFAULT_MAX_SNIPPET_CHARS)
    max_hits_per_type = _coerce_positive_int(raw.get("max_hits_per_type"), DEFAULT_MAX_HITS_PER_TYPE)
    raw_keywords = raw.get("keywords", DEFAULT_SAFE_KEYWORDS)
    keywords = _normalize_keyword_sequence(raw_keywords)
    section_headings = _normalize_section_headings(raw.get("section_headings", DEFAULT_SECTION_HEADINGS))
    return {
        "max_snippet_chars": max_snippet_chars,
        "max_hits_per_type": max_hits_per_type,
        "keywords": keywords,
        "section_headings": section_headings,
    }


def _normalize_keyword_sequence(values: Any) -> list[str]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise OfficialArtifactEvidenceLocatorError(REASON_INVALID_LOCATOR_CONFIG)
    keywords = [_clean_string(value) for value in values if _clean_string(value)]
    for keyword in keywords:
        assert_no_official_artifact_evidence_locator_forbidden_markers(keyword)
        _assert_no_metric_locator_keyword(keyword)
    return _dedupe_preserve_order(keywords)


def _normalize_section_headings(values: Any) -> list[tuple[str, str]]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise OfficialArtifactEvidenceLocatorError(REASON_INVALID_LOCATOR_CONFIG)
    headings: list[tuple[str, str]] = []
    for value in values:
        if isinstance(value, Mapping):
            section_type = _clean_string(value.get("section_type"))
            heading_text = _clean_string(value.get("heading_text"))
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and len(value) >= 2:
            section_type = _clean_string(value[0])
            heading_text = _clean_string(value[1])
        else:
            section_type = _safe_identifier(_clean_string(value))
            heading_text = _clean_string(value)
        if not section_type or not heading_text:
            continue
        assert_no_official_artifact_evidence_locator_forbidden_markers(section_type)
        assert_no_official_artifact_evidence_locator_forbidden_markers(heading_text)
        _assert_no_metric_locator_keyword(section_type)
        _assert_no_metric_locator_keyword(heading_text)
        headings.append((section_type, heading_text))
    return _dedupe_preserve_order(headings)


def _report_title_keywords(artifact_item: Mapping[str, Any]) -> list[str]:
    keywords: list[str] = []
    source_title = _clean_string(artifact_item.get("source_title"))
    if source_title and len(source_title) <= DEFAULT_MAX_SNIPPET_CHARS:
        keywords.append(source_title)
    announcement_type = _clean_string(artifact_item.get("announcement_type"))
    keywords.extend(ANNOUNCEMENT_TYPE_TITLE_KEYWORDS.get(announcement_type, ()))
    keywords.extend(DEFAULT_REPORT_TITLE_KEYWORDS)
    return _dedupe_preserve_order([keyword for keyword in keywords if keyword])


def _company_keywords(artifact_item: Mapping[str, Any]) -> list[str]:
    company_name = _clean_string(artifact_item.get("company_name_hint"))
    return [company_name] if company_name else []


def _stock_code_keywords(artifact_item: Mapping[str, Any]) -> list[str]:
    keywords = [_clean_string(artifact_item.get("stock_code"))]
    source_lineage = artifact_item.get("source_lineage")
    if isinstance(source_lineage, Mapping):
        keywords.append(_clean_string(source_lineage.get("ts_code")))
    return _dedupe_preserve_order([keyword for keyword in keywords if keyword])


def _period_keywords(artifact_item: Mapping[str, Any]) -> list[str]:
    keywords: list[str] = []
    period_key = _clean_string(artifact_item.get("period_key"))
    period_end_date = _clean_string(artifact_item.get("period_end_date"))
    if period_key:
        keywords.extend(_period_key_variants(period_key))
    if period_end_date:
        keywords.extend(_date_variants(period_end_date))
    return _dedupe_preserve_order([keyword for keyword in keywords if keyword])


def _period_key_variants(period_key: str) -> list[str]:
    variants = [period_key]
    match = re.fullmatch(r"(\d{4})Q([1-4])", period_key, flags=re.IGNORECASE)
    if match:
        year, quarter = match.groups()
        variants.extend([f"{year} Q{quarter}", f"{year}Q{quarter}", f"{year}年第{quarter}季度"])
        if quarter == "1":
            variants.extend([f"{year}年第一季度", "第一季度"])
    match = re.fullmatch(r"(\d{4})FY", period_key, flags=re.IGNORECASE)
    if match:
        year = match.group(1)
        variants.extend([year, f"{year}年度"])
    return variants


def _date_variants(period_end_date: str) -> list[str]:
    variants = [period_end_date]
    compact = re.fullmatch(r"(\d{4})(\d{2})(\d{2})", period_end_date)
    dashed = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", period_end_date)
    match = compact or dashed
    if match:
        year, month, day = match.groups()
        variants.extend(
            [
                f"{year}-{month}-{day}",
                f"{year}{month}{day}",
                f"{year}年{int(month)}月{int(day)}日",
                f"{year}年{month}月{day}日",
            ]
        )
    return variants


def _find_text_hits(
    pages: Sequence[Mapping[str, Any]],
    keywords: Sequence[str],
    *,
    hit_type: str,
    config: Mapping[str, Any],
    confidence: str,
) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    max_hits = int(config["max_hits_per_type"])
    max_chars = int(config["max_snippet_chars"])
    for keyword in keywords:
        clean_keyword = _clean_string(keyword)
        if not clean_keyword:
            continue
        for page in pages:
            match_index = _casefold_index(page["text"], clean_keyword)
            if match_index < 0:
                continue
            snippet = _snippet_around(page["text"], match_index, len(clean_keyword), max_chars=max_chars)
            hit = {
                "schema_version": OFFICIAL_ARTIFACT_TEXT_HIT_SCHEMA_VERSION,
                "hit_type": hit_type,
                "keyword": clean_keyword,
                "page_number": page["page_number"],
                "snippet": snippet,
                "snippet_char_count": len(snippet),
                "confidence": confidence,
                "not_official_verified": True,
                "not_for_trading_advice": True,
            }
            hits.append(hit)
            break
        if len(hits) >= max_hits:
            break
    return hits


def _locator_confidence(
    *,
    identity_hits: Mapping[str, list[dict[str, Any]]],
    section_heading_hits: Sequence[Mapping[str, Any]],
    keyword_hits: Sequence[Mapping[str, Any]],
) -> str:
    identity_group_count = sum(
        1
        for key in ("report_title_hits", "company_name_hits", "stock_code_hits", "report_period_hits")
        if identity_hits.get(key)
    )
    has_report = bool(identity_hits.get("report_title_hits"))
    has_entity = bool(identity_hits.get("company_name_hits") or identity_hits.get("stock_code_hits"))
    has_period_or_section = bool(identity_hits.get("report_period_hits") or section_heading_hits)
    if has_report and has_entity and has_period_or_section:
        return LOCATOR_CONFIDENCE_HIGH
    if identity_group_count >= 2 or (section_heading_hits and identity_group_count >= 1):
        return LOCATOR_CONFIDENCE_MEDIUM
    if identity_group_count or section_heading_hits or keyword_hits:
        return LOCATOR_CONFIDENCE_LOW
    return LOCATOR_CONFIDENCE_BLOCKED


def _normalize_pages(pages: Sequence[Any]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, page in enumerate(pages, start=1):
        if isinstance(page, Mapping):
            page_number = page.get("page_number", index)
            text = _clean_string(page.get("text"))
        else:
            page_number = index
            text = _clean_string(page)
        try:
            page_number_int = int(page_number)
        except (TypeError, ValueError):
            page_number_int = index
        if page_number_int < 1:
            page_number_int = index
        normalized.append({"page_number": page_number_int, "text": text})
    return normalized


def _casefold_index(text: str, keyword: str) -> int:
    return text.casefold().find(keyword.casefold())


def _snippet_around(text: str, index: int, keyword_length: int, *, max_chars: int) -> str:
    if max_chars <= 0:
        max_chars = DEFAULT_MAX_SNIPPET_CHARS
    if len(text) <= max_chars:
        return text
    center = index + max(keyword_length, 1) // 2
    start = max(0, center - max_chars // 2)
    end = min(len(text), start + max_chars)
    start = max(0, end - max_chars)
    return text[start:end].strip()


def _validate_text_hit(hit: Any, *, path: str) -> None:
    if not isinstance(hit, Mapping):
        raise OfficialArtifactEvidenceLocatorError(f"{path}:invalid_text_hit")
    required = (
        "schema_version",
        "hit_type",
        "keyword",
        "page_number",
        "snippet",
        "snippet_char_count",
        "confidence",
        "not_official_verified",
        "not_for_trading_advice",
    )
    for key in required:
        if key not in hit:
            raise OfficialArtifactEvidenceLocatorError(f"{path}:{key}_missing")
    if hit.get("schema_version") != OFFICIAL_ARTIFACT_TEXT_HIT_SCHEMA_VERSION:
        raise OfficialArtifactEvidenceLocatorError(f"{path}:invalid_text_hit_schema_version")
    _validate_page_number(hit.get("page_number"), path=path)
    if hit.get("confidence") not in LOCATOR_CONFIDENCE_VALUES - {LOCATOR_CONFIDENCE_BLOCKED}:
        raise OfficialArtifactEvidenceLocatorError(f"{path}:invalid_hit_confidence")
    snippet = _clean_string(hit.get("snippet"))
    if len(snippet) > DEFAULT_MAX_SNIPPET_CHARS:
        raise OfficialArtifactEvidenceLocatorError(f"{path}:snippet_too_long")
    if hit.get("snippet_char_count") != len(snippet):
        raise OfficialArtifactEvidenceLocatorError(f"{path}:invalid_snippet_char_count")
    _require_true_bool(hit, "not_official_verified", path)
    _require_true_bool(hit, "not_for_trading_advice", path)
    assert_no_official_artifact_evidence_locator_forbidden_markers(hit)


def _validate_section_hit(hit: Any, *, path: str) -> None:
    if not isinstance(hit, Mapping):
        raise OfficialArtifactEvidenceLocatorError(f"{path}:invalid_section_hit")
    required = (
        "schema_version",
        "section_type",
        "heading_text",
        "page_number",
        "snippet",
        "confidence",
        "not_official_verified",
        "not_for_trading_advice",
    )
    for key in required:
        if key not in hit:
            raise OfficialArtifactEvidenceLocatorError(f"{path}:{key}_missing")
    if hit.get("schema_version") != OFFICIAL_ARTIFACT_SECTION_LOCATOR_SCHEMA_VERSION:
        raise OfficialArtifactEvidenceLocatorError(f"{path}:invalid_section_hit_schema_version")
    _validate_page_number(hit.get("page_number"), path=path)
    if hit.get("confidence") not in LOCATOR_CONFIDENCE_VALUES - {LOCATOR_CONFIDENCE_BLOCKED}:
        raise OfficialArtifactEvidenceLocatorError(f"{path}:invalid_section_confidence")
    if len(_clean_string(hit.get("snippet"))) > DEFAULT_MAX_SNIPPET_CHARS:
        raise OfficialArtifactEvidenceLocatorError(f"{path}:snippet_too_long")
    _require_true_bool(hit, "not_official_verified", path)
    _require_true_bool(hit, "not_for_trading_advice", path)
    assert_no_official_artifact_evidence_locator_forbidden_markers(hit)


def _validate_page_number(value: Any, *, path: str) -> None:
    if not isinstance(value, int) or value < 1:
        raise OfficialArtifactEvidenceLocatorError(f"{path}:invalid_page_number")


def _assert_no_disallowed_output_keys(value: Any) -> None:
    disallowed = {"cache_path", "full_text", "page_text", "raw_pdf_text", "pdf_bytes"}
    if isinstance(value, Mapping):
        for key, nested_value in value.items():
            if str(key) in disallowed:
                raise OfficialArtifactEvidenceLocatorError("locator_result_contains_disallowed_payload")
            _assert_no_disallowed_output_keys(nested_value)
    elif isinstance(value, list):
        for item in value:
            _assert_no_disallowed_output_keys(item)


def _find_forbidden_marker(value: Any) -> str | None:
    if isinstance(value, Mapping):
        for key, nested_value in value.items():
            key_text = str(key)
            if _text_has_forbidden_marker(key_text):
                return key_text
            finding = _find_forbidden_marker(nested_value)
            if finding is not None:
                return finding
        return None
    if isinstance(value, (list, tuple, set)):
        for item in value:
            finding = _find_forbidden_marker(item)
            if finding is not None:
                return finding
        return None
    if isinstance(value, Path):
        return _find_forbidden_marker(str(value))
    if isinstance(value, str):
        if _text_has_forbidden_marker(value):
            return value
    return None


def _text_has_forbidden_marker(value: str) -> bool:
    normalized = _normalize_marker_text(value)
    separator_normalized = _normalize_marker_text(re.sub(r"[_-]+", " ", value))
    if normalized in ALLOWED_FLAG_MARKERS:
        return False
    lowered = value.casefold()
    for marker in FORBIDDEN_ENGLISH_MARKERS:
        marker_text = _normalize_marker_text(marker)
        if marker == ".env":
            if ".env" in lowered or normalized == "env":
                return True
            continue
        if marker_text in WORD_MARKERS:
            boundary_chars = "a-z0-9_" if marker_text in IDENTIFIER_SAFE_WORD_MARKERS else "a-z0-9"
            if re.search(rf"(?<![{boundary_chars}]){re.escape(marker_text)}(?![{boundary_chars}])", normalized):
                return True
            continue
        if marker_text == "official_verified":
            if _contains_official_verified_marker(normalized):
                return True
            continue
        if marker_text == "trading_advice" and normalized == "not_for_trading_advice":
            continue
        if marker_text and (marker_text in normalized or marker_text in separator_normalized):
            return True
    return any(marker in value for marker in FORBIDDEN_CJK_MARKERS)


def _contains_official_verified_marker(value: str) -> bool:
    if value == "not_official_verified":
        return False
    return re.search(r"(?<!not_)official_verified", value) is not None


def _normalize_marker_text(value: Any) -> str:
    raw = _clean_string(value)
    camel_split = CAMEL_SPLIT_RE.sub("_", raw)
    lowered = camel_split.casefold()
    lowered = re.sub(r"[\s\-\.]+", "_", lowered)
    lowered = re.sub(r"_+", "_", lowered).strip("_")
    return lowered


def _redacted_marker(marker: str) -> str:
    if _text_has_secret_marker(marker):
        return "redacted_forbidden_marker"
    return marker


def _text_has_secret_marker(value: str) -> bool:
    lowered = value.casefold()
    return "tushare_token" in lowered or ".env" in lowered or re.search(r"\btoken\b", lowered) is not None


def _safe_mapping_list(values: Any) -> list[Mapping[str, Any]]:
    if not isinstance(values, list):
        return []
    return [value for value in values if isinstance(value, Mapping)]


def _safe_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [_clean_string(value) for value in values if _clean_string(value)]


def _clean_string(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _coerce_positive_int(value: Any, default: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return number if number > 0 else default


def _require_true_bool(payload: Mapping[str, Any], key: str, path: str) -> None:
    if key not in payload:
        raise OfficialArtifactEvidenceLocatorError(f"{path}:{key}_missing")
    if payload.get(key) is not True:
        raise OfficialArtifactEvidenceLocatorError(f"{path}:{key}_must_be_true")


def _safe_identifier(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_").casefold()
    return text or "section"


def _copy_jsonlike(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _copy_jsonlike(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_copy_jsonlike(item) for item in value]
    if isinstance(value, tuple):
        return [_copy_jsonlike(item) for item in value]
    return copy.deepcopy(value)


def _dedupe_preserve_order(values: Sequence[Any]) -> list[Any]:
    seen: set[Any] = set()
    result: list[Any] = []
    for value in values:
        marker = repr(value)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(value)
    return result
