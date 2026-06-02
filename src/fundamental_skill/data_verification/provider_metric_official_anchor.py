# -*- coding: utf-8 -*-
"""Official disclosure anchor mapping for provider metric candidates.

This module is a standalone, in-memory bridge from provider candidate metric
verification items to explicit official disclosure metadata anchors. It does
not discover sources, fetch provider data, fetch official data, read files, or
write artifacts.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urlparse


PROVIDER_NAME = "Tushare"
PROVIDER_QUEUE_SCHEMA_VERSION = "provider_candidate_metric_verification_queue.v1"
PROVIDER_QUEUE_ITEM_SCHEMA_VERSION = "provider_candidate_metric_verification_item.v1"
ANCHOR_MAP_SCHEMA_VERSION = "provider_metric_official_disclosure_anchor_map.v1"
ANCHOR_ITEM_SCHEMA_VERSION = "provider_metric_official_disclosure_anchor_item.v1"
OFFICIAL_METADATA_CANDIDATE_SCHEMA_VERSION = "official_disclosure_metadata_candidate.v1"

PENDING_OFFICIAL_VERIFICATION_STATUS = "pending_official_verification"
ANCHOR_EVIDENCE_STATUS = "official_anchor_candidate"

ANCHOR_STATUS_MATCHED = "matched"
ANCHOR_STATUS_MISSING = "missing_anchor"
ANCHOR_STATUS_AMBIGUOUS = "ambiguous_anchor"
ANCHOR_STATUS_CONFLICT = "conflict"
ALLOWED_ANCHOR_STATUSES = {
    ANCHOR_STATUS_MATCHED,
    ANCHOR_STATUS_MISSING,
    ANCHOR_STATUS_AMBIGUOUS,
    ANCHOR_STATUS_CONFLICT,
}

ANNUAL_REPORT = "annual_report"
QUARTERLY_REPORT = "quarterly_report"
SEMIANNUAL_REPORT = "semiannual_report"
ALLOWED_ANNOUNCEMENT_TYPES = {ANNUAL_REPORT, QUARTERLY_REPORT, SEMIANNUAL_REPORT}

ALLOWED_SOURCE_TYPES = {
    "cninfo_official_pdf",
    "sse_exchange_announcement",
    "exchange_official_pdf",
}
ALLOWED_OFFICIAL_DOMAINS = {
    "www.cninfo.com.cn",
    "static.cninfo.com.cn",
    "www.sse.com.cn",
    "www.szse.cn",
    "www.bse.cn",
}

ALLOWED_EXACT_KEYS = {"not_official_verified", "not_for_trading_advice"}
SOURCE_URL_KEY = "source_url"
FORBIDDEN_SECRET_URL_MARKERS = ("token", ".env", "tushare_token")
FORBIDDEN_MARKERS = (
    "token",
    ".env",
    "tushare_token",
    "official_verified",
    "official_metric_fact",
    "provider_official_conflict",
    "Report V1",
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
    "download",
    "parse PDF",
    "PDF parser",
    "table extractor",
    "metric extraction",
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
    "下载",
    "解析PDF",
    "PDF解析",
    "表格抽取",
    "指标抽取",
)
WORD_MARKERS = {"token", "buy", "sell", "hold", "portfolio", "position", "download"}
IDENTIFIER_SAFE_WORD_MARKERS = {"buy", "sell", "hold"}


class ProviderMetricOfficialAnchorError(ValueError):
    """Raised when provider metric anchor mapping must fail closed."""


def build_provider_metric_official_disclosure_anchor_map(
    provider_queue: Any,
    official_metadata_candidates: Any,
) -> dict[str, Any]:
    """Build provider metric to official disclosure anchor mappings."""

    assert_no_provider_metric_anchor_forbidden_markers(provider_queue)
    assert_no_provider_metric_anchor_forbidden_markers(official_metadata_candidates)

    result = _empty_anchor_map(provider_queue if isinstance(provider_queue, Mapping) else None)
    queue_blockers = _provider_queue_blockers(provider_queue)
    if official_metadata_candidates is None or not isinstance(official_metadata_candidates, list):
        queue_blockers.append("official_metadata_candidates_must_be_list")

    if queue_blockers:
        result["blocked_reasons"].extend(queue_blockers)
        result["caveats"].append("anchor_mapping_input_rejected")
        validate_provider_metric_official_disclosure_anchor_map(result)
        return result

    assert isinstance(provider_queue, Mapping)
    assert isinstance(official_metadata_candidates, list)
    normalized_candidates, rejected_candidates = _normalize_candidate_list(official_metadata_candidates)
    result["candidate_disclosure_summary"] = {
        "schema_version": "official_disclosure_metadata_candidate_summary.v1",
        "total_candidates": len(official_metadata_candidates),
        "usable_candidates": len(normalized_candidates),
        "rejected_candidates": rejected_candidates,
    }

    for item in provider_queue["verification_items"]:
        match = match_provider_metric_to_official_anchor(item, normalized_candidates)
        anchor_item = _build_anchor_item(item, match)
        result["anchor_items"].append(anchor_item)
        if anchor_item["official_anchor_status"] != ANCHOR_STATUS_MATCHED:
            result["unmatched_items"].append(_unmatched_item_summary(anchor_item))

    result["caveats"].extend(
        [
            "anchor_mapping_only",
            "provider_values_preserved",
            "metric_verification_pending",
        ]
    )
    validate_provider_metric_official_disclosure_anchor_map(result)
    return result


def validate_provider_metric_official_disclosure_anchor_map(anchor_map: Mapping[str, Any]) -> None:
    """Validate anchor map shape and safety constraints."""

    if not isinstance(anchor_map, Mapping):
        raise ProviderMetricOfficialAnchorError("invalid_anchor_map")
    if anchor_map.get("schema_version") != ANCHOR_MAP_SCHEMA_VERSION:
        raise ProviderMetricOfficialAnchorError("invalid_anchor_map_schema_version")
    if anchor_map.get("provider") != PROVIDER_NAME:
        raise ProviderMetricOfficialAnchorError("invalid_anchor_map_provider")
    _require_true_bool(anchor_map, "not_official_verified", "$")
    _require_true_bool(anchor_map, "not_for_trading_advice", "$")

    for key in (
        "periods",
        "anchor_items",
        "unmatched_items",
        "blocked_reasons",
        "caveats",
    ):
        if not isinstance(anchor_map.get(key), list):
            raise ProviderMetricOfficialAnchorError(f"invalid_{key}")
    if not isinstance(anchor_map.get("candidate_disclosure_summary"), Mapping):
        raise ProviderMetricOfficialAnchorError("invalid_candidate_disclosure_summary")

    for index, item in enumerate(anchor_map["anchor_items"]):
        _validate_anchor_item(item, f"$.anchor_items[{index}]")
    for index, item in enumerate(anchor_map["unmatched_items"]):
        if not isinstance(item, Mapping):
            raise ProviderMetricOfficialAnchorError(f"invalid_unmatched_item:{index}")

    assert_no_provider_metric_anchor_forbidden_markers(anchor_map)


def normalize_official_disclosure_metadata_candidate(candidate: Any) -> dict[str, Any]:
    """Normalize one explicit official disclosure metadata candidate."""

    assert_no_provider_metric_anchor_forbidden_markers(candidate)
    blockers = _candidate_blockers(candidate)
    if blockers:
        raise ProviderMetricOfficialAnchorError(",".join(blockers))
    assert isinstance(candidate, Mapping)
    return _normalized_candidate(candidate)


def match_provider_metric_to_official_anchor(
    item: Any,
    candidates: Any,
) -> dict[str, Any]:
    """Match one provider metric item to normalized official metadata candidates."""

    assert_no_provider_metric_anchor_forbidden_markers(item)
    assert_no_provider_metric_anchor_forbidden_markers(candidates)
    item_blockers = _provider_item_blockers(item)
    if item_blockers:
        raise ProviderMetricOfficialAnchorError(",".join(item_blockers))
    if not isinstance(candidates, list):
        raise ProviderMetricOfficialAnchorError("official_metadata_candidates_must_be_list")

    normalized_candidates = [
        candidate
        if isinstance(candidate, Mapping)
        and candidate.get("schema_version") == OFFICIAL_METADATA_CANDIDATE_SCHEMA_VERSION
        else normalize_official_disclosure_metadata_candidate(candidate)
        for candidate in candidates
    ]

    assert isinstance(item, Mapping)
    required_type = infer_required_announcement_type_from_period(
        item.get("period"),
        item.get("period_label"),
    )
    if required_type is None:
        return {
            "official_anchor_status": ANCHOR_STATUS_MISSING,
            "official_disclosure_anchor": None,
            "caveats": ["unsupported_period_for_anchor_mapping"],
        }

    stock_code = _normalize_stock_code(item.get("stock_code"))
    period = _normalize_period_end_date(item.get("period"))
    exact_matches = [
        candidate
        for candidate in normalized_candidates
        if candidate["stock_code"] == stock_code
        and candidate["period_end_date"] == period
        and candidate["announcement_type"] == required_type
    ]

    if not exact_matches:
        conflict_caveats = _candidate_conflict_caveats(
            normalized_candidates,
            stock_code=stock_code,
            period=period,
            required_type=required_type,
        )
        status = (
            ANCHOR_STATUS_CONFLICT
            if "candidate_announcement_type_conflict" in conflict_caveats
            else ANCHOR_STATUS_MISSING
        )
        caveats = ["no_matching_official_anchor_candidate"]
        caveats.extend(conflict_caveats)
        return {
            "official_anchor_status": status,
            "official_disclosure_anchor": None,
            "caveats": _dedupe_strings(caveats),
        }

    deduped_matches = _dedupe_candidates_by_url(exact_matches)
    if len(deduped_matches) == 1:
        return {
            "official_anchor_status": ANCHOR_STATUS_MATCHED,
            "official_disclosure_anchor": _official_disclosure_anchor(deduped_matches[0]),
            "caveats": ["official_anchor_candidate_only"],
        }

    return {
        "official_anchor_status": ANCHOR_STATUS_AMBIGUOUS,
        "official_disclosure_anchor": None,
        "caveats": ["ambiguous_official_anchor_candidates"],
    }


def infer_required_announcement_type_from_period(period: Any, period_label: Any) -> str | None:
    """Infer the required disclosure type from a provider period."""

    period_text = _normalize_period_end_date(period)
    label_text = str(period_label or "").strip().casefold()
    if period_text.endswith("1231") or "fy" in label_text:
        return ANNUAL_REPORT
    if period_text.endswith("0331") or "q1" in label_text:
        return QUARTERLY_REPORT
    if period_text.endswith("0630") or "h1" in label_text:
        return SEMIANNUAL_REPORT
    return None


def assert_no_provider_metric_anchor_forbidden_markers(value: Any) -> None:
    """Reject forbidden markers in nested dict/list/string payloads."""

    finding = _find_forbidden_marker(value)
    if finding is not None:
        raise ProviderMetricOfficialAnchorError("forbidden_marker")


def _empty_anchor_map(provider_queue: Mapping[str, Any] | None) -> dict[str, Any]:
    return {
        "schema_version": ANCHOR_MAP_SCHEMA_VERSION,
        "provider": PROVIDER_NAME,
        "ts_code": provider_queue.get("ts_code") if provider_queue else None,
        "stock_code": provider_queue.get("stock_code") if provider_queue else None,
        "company_name_hint": provider_queue.get("company_name_hint") if provider_queue else None,
        "periods": _queue_periods(provider_queue),
        "anchor_items": [],
        "unmatched_items": [],
        "candidate_disclosure_summary": {
            "schema_version": "official_disclosure_metadata_candidate_summary.v1",
            "total_candidates": 0,
            "usable_candidates": 0,
            "rejected_candidates": [],
        },
        "blocked_reasons": [],
        "caveats": [],
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }


def _queue_periods(provider_queue: Mapping[str, Any] | None) -> list[str]:
    if not provider_queue:
        return []
    periods = provider_queue.get("periods")
    if isinstance(periods, list):
        return [str(period) for period in periods if period not in (None, "")]
    items = provider_queue.get("verification_items")
    if not isinstance(items, list):
        return []
    seen: list[str] = []
    for item in items:
        if not isinstance(item, Mapping):
            continue
        period = item.get("period")
        if period not in (None, "") and str(period) not in seen:
            seen.append(str(period))
    return seen


def _provider_queue_blockers(provider_queue: Any) -> list[str]:
    if provider_queue is None:
        return ["missing_provider_queue"]
    if not isinstance(provider_queue, Mapping):
        return ["provider_queue_must_be_mapping"]

    blockers: list[str] = []
    if provider_queue.get("schema_version") != PROVIDER_QUEUE_SCHEMA_VERSION:
        blockers.append("invalid_provider_queue_schema_version")
    if provider_queue.get("provider") != PROVIDER_NAME:
        blockers.append("unsupported_provider")
    _append_flag_blocker(blockers, provider_queue, "not_official_verified")
    _append_flag_blocker(blockers, provider_queue, "not_for_trading_advice")

    verification_items = provider_queue.get("verification_items")
    if "verification_items" not in provider_queue:
        blockers.append("missing_verification_items")
    elif not isinstance(verification_items, list):
        blockers.append("verification_items_must_be_list")
    else:
        for index, item in enumerate(verification_items):
            blockers.extend(f"item:{index}:{blocker}" for blocker in _provider_item_blockers(item))
    return blockers


def _provider_item_blockers(item: Any) -> list[str]:
    if not isinstance(item, Mapping):
        return ["provider_item_must_be_mapping"]

    blockers: list[str] = []
    required = (
        "ts_code",
        "stock_code",
        "period",
        "period_label",
        "metric_key",
        "metric_value",
        "value_status",
        "source_table",
        "source_field",
        "provider_native_unit",
        "official_verification_status",
        "not_official_verified",
        "not_for_trading_advice",
    )
    for key in required:
        if key not in item:
            blockers.append(f"missing_{key}")
    if item.get("schema_version") not in (None, PROVIDER_QUEUE_ITEM_SCHEMA_VERSION):
        blockers.append("invalid_provider_item_schema_version")
    if item.get("provider") != PROVIDER_NAME:
        blockers.append("unsupported_provider_item")
    if item.get("period") in (None, ""):
        blockers.append("missing_period")
    if item.get("metric_key") in (None, ""):
        blockers.append("missing_metric_key")
    if item.get("official_verification_status") != PENDING_OFFICIAL_VERIFICATION_STATUS:
        blockers.append("invalid_official_verification_status")
    _append_flag_blocker(blockers, item, "not_official_verified")
    _append_flag_blocker(blockers, item, "not_for_trading_advice")
    return _dedupe_strings(blockers)


def _append_flag_blocker(blockers: list[str], payload: Mapping[str, Any], key: str) -> None:
    reason_key = "advice_safety_flag" if key == "not_for_trading_advice" else key
    if key not in payload:
        blockers.append(f"missing_{reason_key}")
    elif payload.get(key) is not True:
        blockers.append(f"{reason_key}_must_be_true_bool")


def _normalize_candidate_list(candidates: list[Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    normalized: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates):
        blockers = _candidate_blockers(candidate)
        if blockers:
            rejected.append({"index": index, "reasons": blockers})
            continue
        assert isinstance(candidate, Mapping)
        normalized.append(_normalized_candidate(candidate))
    return normalized, rejected


def _candidate_blockers(candidate: Any) -> list[str]:
    if not isinstance(candidate, Mapping):
        return ["candidate_must_be_mapping"]

    blockers: list[str] = []
    required = (
        "source_title",
        "source_url",
        "disclosure_date",
        "stock_code",
        "period_end_date",
        "announcement_type",
        "source_type",
    )
    for key in required:
        if candidate.get(key) in (None, ""):
            blockers.append(f"missing_{key}")

    _append_flag_blocker(blockers, candidate, "not_for_trading_advice")

    announcement_type = candidate.get("announcement_type")
    if announcement_type not in (None, "") and announcement_type not in ALLOWED_ANNOUNCEMENT_TYPES:
        blockers.append("unsupported_announcement_type")

    source_type = candidate.get("source_type")
    if source_type not in (None, "") and source_type not in ALLOWED_SOURCE_TYPES:
        blockers.append("unsupported_source_type")

    url_text = str(candidate.get("source_url") or "").strip()
    parsed_url = urlparse(url_text)
    if url_text and parsed_url.scheme not in {"http", "https"}:
        blockers.append("source_url_scheme_must_be_http_or_https")

    domain = _candidate_domain(candidate)
    url_domain = _domain_from_url(url_text)
    if url_text and parsed_url.scheme in {"http", "https"} and url_domain not in ALLOWED_OFFICIAL_DOMAINS:
        blockers.append("source_url_domain_not_allowlisted")
    if domain is None:
        blockers.append("missing_source_domain")
    elif domain not in ALLOWED_OFFICIAL_DOMAINS:
        blockers.append("source_domain_not_allowlisted")
    elif url_domain is not None and domain != url_domain:
        blockers.append("source_domain_url_mismatch")
    return _dedupe_strings(blockers)


def _normalized_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    period_end_date = _normalize_period_end_date(candidate.get("period_end_date"))
    source_url = str(candidate.get("source_url")).strip()
    source_domain = _candidate_domain(candidate)
    assert source_domain is not None
    caveats = ["official_anchor_candidate_only"]
    if source_url.casefold().split("?", 1)[0].endswith(".pdf"):
        caveats.append("pdf_url_preserved_metadata_only")
    return {
        "schema_version": OFFICIAL_METADATA_CANDIDATE_SCHEMA_VERSION,
        "source_title": str(candidate.get("source_title")).strip(),
        "source_url": source_url,
        "source_domain": source_domain,
        "disclosure_date": str(candidate.get("disclosure_date")).strip(),
        "stock_code": _normalize_stock_code(candidate.get("stock_code")),
        "company_name_hint": candidate.get("company_name_hint"),
        "period_key": str(candidate.get("period_key") or period_end_date),
        "period_end_date": period_end_date,
        "announcement_type": str(candidate.get("announcement_type")).strip(),
        "source_type": str(candidate.get("source_type")).strip(),
        "anchor_evidence_status": ANCHOR_EVIDENCE_STATUS,
        "not_for_trading_advice": True,
        "caveats": caveats,
    }


def _candidate_domain(candidate: Mapping[str, Any]) -> str | None:
    raw_domain = candidate.get("source_domain")
    if raw_domain not in (None, ""):
        domain_text = str(raw_domain).strip().casefold()
        parsed_domain = urlparse(domain_text if "://" in domain_text else f"https://{domain_text}")
        return (parsed_domain.netloc or parsed_domain.path).split("/", 1)[0]
    return _domain_from_url(candidate.get("source_url"))


def _domain_from_url(source_url: Any) -> str | None:
    if source_url in (None, ""):
        return None
    parsed = urlparse(str(source_url).strip())
    if parsed.scheme not in {"http", "https"}:
        return None
    return parsed.netloc.casefold()


def _candidate_conflict_caveats(
    candidates: list[Mapping[str, Any]],
    *,
    stock_code: str,
    period: str,
    required_type: str,
) -> list[str]:
    caveats: list[str] = []
    if any(candidate["stock_code"] != stock_code for candidate in candidates):
        caveats.append("stock_code_mismatch_candidate_rejected")
    same_stock = [candidate for candidate in candidates if candidate["stock_code"] == stock_code]
    if any(candidate["period_end_date"] != period for candidate in same_stock):
        caveats.append("period_mismatch_candidate_rejected")
    if any(
        candidate["period_end_date"] == period and candidate["announcement_type"] != required_type
        for candidate in same_stock
    ):
        caveats.append("candidate_announcement_type_conflict")
    return caveats


def _dedupe_candidates_by_url(candidates: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    seen_urls: set[str] = set()
    deduped: list[Mapping[str, Any]] = []
    for candidate in candidates:
        source_url = str(candidate["source_url"])
        if source_url in seen_urls:
            continue
        seen_urls.add(source_url)
        deduped.append(candidate)
    return deduped


def _build_anchor_item(item: Mapping[str, Any], match: Mapping[str, Any]) -> dict[str, Any]:
    caveats = _safe_list(item.get("caveats"))
    caveats.extend(_safe_list(match.get("caveats")))
    return {
        "schema_version": ANCHOR_ITEM_SCHEMA_VERSION,
        "provider": PROVIDER_NAME,
        "ts_code": item.get("ts_code"),
        "stock_code": item.get("stock_code"),
        "company_name_hint": item.get("company_name_hint"),
        "period": item.get("period"),
        "period_label": item.get("period_label"),
        "metric_key": item.get("metric_key"),
        "metric_value": item.get("metric_value"),
        "value_status": item.get("value_status"),
        "source_table": item.get("source_table"),
        "source_field": item.get("source_field"),
        "provider_native_unit": item.get("provider_native_unit"),
        "official_verification_status": PENDING_OFFICIAL_VERIFICATION_STATUS,
        "official_anchor_status": match.get("official_anchor_status"),
        "official_anchor_required": True,
        "official_disclosure_anchor": match.get("official_disclosure_anchor"),
        "not_official_verified": True,
        "not_for_trading_advice": True,
        "caveats": _dedupe_strings(caveats),
    }


def _unmatched_item_summary(anchor_item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "period": anchor_item.get("period"),
        "period_label": anchor_item.get("period_label"),
        "metric_key": anchor_item.get("metric_key"),
        "official_anchor_status": anchor_item.get("official_anchor_status"),
        "caveats": anchor_item.get("caveats", []),
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }


def _official_disclosure_anchor(candidate: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "source_title": candidate["source_title"],
        "source_url": candidate["source_url"],
        "source_domain": candidate["source_domain"],
        "disclosure_date": candidate["disclosure_date"],
        "stock_code": candidate["stock_code"],
        "company_name_hint": candidate.get("company_name_hint"),
        "period_key": candidate["period_key"],
        "period_end_date": candidate["period_end_date"],
        "announcement_type": candidate["announcement_type"],
        "source_type": candidate["source_type"],
        "anchor_evidence_status": ANCHOR_EVIDENCE_STATUS,
        "not_for_trading_advice": True,
    }


def _validate_anchor_item(item: Any, path: str) -> None:
    if not isinstance(item, Mapping):
        raise ProviderMetricOfficialAnchorError("invalid_anchor_item")
    required = (
        "schema_version",
        "provider",
        "ts_code",
        "stock_code",
        "company_name_hint",
        "period",
        "period_label",
        "metric_key",
        "metric_value",
        "value_status",
        "source_table",
        "source_field",
        "provider_native_unit",
        "official_verification_status",
        "official_anchor_status",
        "official_anchor_required",
        "official_disclosure_anchor",
        "not_official_verified",
        "not_for_trading_advice",
        "caveats",
    )
    for key in required:
        if key not in item:
            raise ProviderMetricOfficialAnchorError(f"{path}:{key}_missing")
    if item.get("schema_version") != ANCHOR_ITEM_SCHEMA_VERSION:
        raise ProviderMetricOfficialAnchorError("invalid_anchor_item_schema_version")
    if item.get("provider") != PROVIDER_NAME:
        raise ProviderMetricOfficialAnchorError("invalid_anchor_item_provider")
    for key in ("ts_code", "stock_code", "period", "period_label", "metric_key"):
        if item.get(key) in (None, ""):
            raise ProviderMetricOfficialAnchorError(f"missing_anchor_item_{key}")
    if item.get("official_verification_status") != PENDING_OFFICIAL_VERIFICATION_STATUS:
        raise ProviderMetricOfficialAnchorError("invalid_anchor_item_official_verification_status")
    if item.get("official_anchor_status") not in ALLOWED_ANCHOR_STATUSES:
        raise ProviderMetricOfficialAnchorError("invalid_official_anchor_status")
    if item.get("official_anchor_required") is not True:
        raise ProviderMetricOfficialAnchorError("official_anchor_required_must_be_true")
    if not isinstance(item.get("caveats"), list):
        raise ProviderMetricOfficialAnchorError("invalid_anchor_item_caveats")
    _require_true_bool(item, "not_official_verified", path)
    _require_true_bool(item, "not_for_trading_advice", path)

    anchor = item.get("official_disclosure_anchor")
    if item.get("official_anchor_status") == ANCHOR_STATUS_MATCHED:
        _validate_official_disclosure_anchor(anchor)
    elif anchor is not None:
        raise ProviderMetricOfficialAnchorError("unmatched_item_must_not_have_anchor")


def _validate_official_disclosure_anchor(anchor: Any) -> None:
    if not isinstance(anchor, Mapping):
        raise ProviderMetricOfficialAnchorError("invalid_official_disclosure_anchor")
    required = (
        "source_title",
        "source_url",
        "source_domain",
        "disclosure_date",
        "stock_code",
        "company_name_hint",
        "period_key",
        "period_end_date",
        "announcement_type",
        "source_type",
        "anchor_evidence_status",
        "not_for_trading_advice",
    )
    for key in required:
        if key not in anchor:
            raise ProviderMetricOfficialAnchorError(f"official_disclosure_anchor_{key}_missing")
    if anchor.get("source_domain") not in ALLOWED_OFFICIAL_DOMAINS:
        raise ProviderMetricOfficialAnchorError("official_disclosure_anchor_domain_not_allowlisted")
    if anchor.get("announcement_type") not in ALLOWED_ANNOUNCEMENT_TYPES:
        raise ProviderMetricOfficialAnchorError("invalid_official_disclosure_anchor_announcement_type")
    if anchor.get("source_type") not in ALLOWED_SOURCE_TYPES:
        raise ProviderMetricOfficialAnchorError("invalid_official_disclosure_anchor_source_type")
    if anchor.get("anchor_evidence_status") != ANCHOR_EVIDENCE_STATUS:
        raise ProviderMetricOfficialAnchorError("invalid_anchor_evidence_status")
    _require_true_bool(anchor, "not_for_trading_advice", "$.official_disclosure_anchor")


def _require_true_bool(payload: Mapping[str, Any], key: str, path: str) -> None:
    if key not in payload:
        raise ProviderMetricOfficialAnchorError(f"{path}:{key}_missing")
    if payload.get(key) is not True:
        raise ProviderMetricOfficialAnchorError(f"{path}:{key}_must_be_true")


def _safe_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(value) for value in values if value not in (None, "")]


def _dedupe_strings(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _normalize_stock_code(value: Any) -> str:
    text = str(value or "").strip()
    if "." in text:
        return text.split(".", 1)[0]
    return text


def _normalize_period_end_date(value: Any) -> str:
    text = str(value or "").strip()
    compact = re.sub(r"[-/]", "", text)
    return compact


def _find_forbidden_marker(value: Any, parent_key: str | None = None) -> str | None:
    if isinstance(value, Mapping):
        for key, nested_value in value.items():
            key_text = str(key)
            if key_text not in ALLOWED_EXACT_KEYS and _text_has_forbidden_marker(key_text):
                return key_text
            finding = _find_forbidden_marker(nested_value, parent_key=key_text)
            if finding is not None:
                return finding
        return None
    if isinstance(value, (list, tuple, set)):
        for item in value:
            finding = _find_forbidden_marker(item, parent_key=parent_key)
            if finding is not None:
                return finding
        return None
    if isinstance(value, str):
        if parent_key == SOURCE_URL_KEY:
            return value if _url_has_forbidden_secret_marker(value) else None
        if _text_has_forbidden_marker(value):
            return value
    return None


def _url_has_forbidden_secret_marker(value: str) -> bool:
    normalized = _normalize_marker_text(value)
    return any(_normalize_marker_text(marker) in normalized for marker in FORBIDDEN_SECRET_URL_MARKERS)


def _text_has_forbidden_marker(value: str) -> bool:
    normalized = _normalize_marker_text(value)
    separator_normalized = _normalize_marker_text(re.sub(r"[_-]+", " ", value))
    if normalized == "not_official_verified":
        return False

    for marker in FORBIDDEN_MARKERS:
        marker_text = _normalize_marker_text(marker)
        if marker_text in WORD_MARKERS:
            boundary_chars = "a-z0-9_" if marker_text in IDENTIFIER_SAFE_WORD_MARKERS else "a-z0-9"
            if re.search(rf"(?<![{boundary_chars}]){re.escape(marker_text)}(?![{boundary_chars}])", normalized):
                return True
            continue
        if marker_text == "official_verified":
            if _contains_official_verified_marker(normalized):
                return True
            continue
        if marker_text in normalized or marker_text in separator_normalized:
            return True
    return any(marker in value for marker in FORBIDDEN_CJK_MARKERS)


def _contains_official_verified_marker(value: str) -> bool:
    if value == "not_official_verified":
        return False
    return bool(re.search(r"(?<!not_)official_verified", value))


def _normalize_marker_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().casefold())
