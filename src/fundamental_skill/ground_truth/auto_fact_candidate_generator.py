# -*- coding: utf-8 -*-
"""Offline provider-comparison artifact fact candidate generator.

This module intentionally stays below the provider/runtime layer. It reads
existing JSON artifacts only and emits auditable in-memory candidate reports.
"""

from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODE = "offline_artifact_candidate_generation"

PROVIDERS = ("tushare", "akshare")

FUNDAMENTAL_ARTIFACTS = {
    "tushare": "tushare_fundamental.json",
    "akshare": "akshare_fundamental.json",
}
RAW_ARTIFACTS = {
    "tushare": "tushare_raw.json",
    "akshare": "akshare_raw.json",
}
OPTIONAL_ARTIFACTS = ("diff_report.json", "score_confidence_explainability.json")

BASIC_FIELDS = ("stock_code", "stock_name", "industry", "listing_date", "main_business")
FINANCIAL_FIELDS = (
    "period",
    "revenue",
    "net_profit",
    "gross_margin",
    "roe",
    "operating_cashflow",
    "accounts_receivable",
    "inventory",
    "contract_liabilities",
    "capex",
)
VALUATION_FIELDS = ("as_of_date", "pe_ttm", "pb", "market_cap")
BUSINESS_COMPOSITION_FIELDS = (
    "period",
    "classification_type",
    "segment_name",
    "revenue",
    "revenue_ratio",
    "gross_margin",
)

BLOCK_ALIASES = {
    "basic_info": ("basic_info",),
    "financial_metrics": ("financial_metrics", "financial_indicator"),
    "valuation_metrics": ("valuation_metrics", "valuation"),
    "business_composition": ("business_composition",),
}

SOURCE_BLOCK_BY_CANONICAL = {
    "basic_info": "basic_info",
    "financial_metrics": "financial_indicator",
    "valuation_metrics": "valuation",
    "business_composition": "business_composition",
}

AMOUNT_FIELDS = {
    "financial_metrics.revenue",
    "financial_metrics.net_profit",
    "financial_metrics.operating_cashflow",
    "financial_metrics.accounts_receivable",
    "financial_metrics.inventory",
    "financial_metrics.contract_liabilities",
    "financial_metrics.capex",
    "valuation_metrics.market_cap",
}
RATIO_FIELDS = {
    "financial_metrics.gross_margin",
    "financial_metrics.roe",
}
VALUATION_MULTIPLE_FIELDS = {
    "valuation_metrics.pe_ttm",
    "valuation_metrics.pb",
}
TEXT_FIELDS = {
    "basic_info.stock_code",
    "basic_info.stock_name",
    "basic_info.industry",
    "basic_info.main_business",
    "business_composition.segment_name",
    "business_composition.classification_type",
}
DATE_FIELDS = {
    "basic_info.listing_date",
    "financial_metrics.period",
    "valuation_metrics.as_of_date",
    "business_composition.period",
}
BUSINESS_RATIO_FIELDS = {
    "business_composition.revenue_ratio",
    "business_composition.gross_margin",
}

REQUIRED_CANDIDATE_KEYS = (
    "field_path",
    "value",
    "source_provider",
    "source_artifact",
    "source_block",
    "source_endpoint",
    "source_trace",
    "report_period",
    "ann_date",
    "disclosure_date",
    "as_of_date",
    "data_unit",
    "canonical_unit",
    "derived",
    "derivation_method",
    "confidence",
    "review_status",
    "missing_category",
    "conflict_status",
    "manual_review_note",
)

FORBIDDEN_RECOMMENDATION_KEYS = {
    "buy",
    "sell",
    "target_price",
    "position",
    "stop_loss",
    "take_profit",
    "portfolio_weight",
}

_STOCK_CODE_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
_TIMESTAMP_RE = re.compile(r"^[A-Za-z0-9T_-]{1,64}$")
_DATE8_RE = re.compile(r"^\d{8}$")
_DATE10_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SECRET_KEY_RE = re.compile(
    r"\b(token|key|secret|auth|credential|api[_-]?key|access[_-]?key|tushare[_-]?token)\b",
    flags=re.IGNORECASE,
)
_KEYED_SECRET_RE = re.compile(
    r"\b(token|key|secret|auth|credential|api[_-]?key|access[_-]?key|tushare[_-]?token)\b\s*[:=]\s*[^\s,;&]+",
    flags=re.IGNORECASE,
)
_BEARER_RE = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]+", flags=re.IGNORECASE)
_MCP_RE = re.compile(r"\bmcp(?:s)?://[^\s\"'<>]+|\bmcp\?[^\s\"']*", flags=re.IGNORECASE)
_TOKEN_LIKE_RE = re.compile(
    r"\b(?=[A-Za-z0-9._~+/=-]{32,}\b)"
    r"(?=[A-Za-z0-9._~+/=-]*[a-z])"
    r"(?=[A-Za-z0-9._~+/=-]*[A-Z])"
    r"(?=[A-Za-z0-9._~+/=-]*\d)"
    r"[A-Za-z0-9._~+/=-]+\b"
)
_LOCAL_SECRET_PATH_RE = re.compile(r"\b[A-Za-z]:[\\/]+Users[\\/]+|/Users/[^/\s]+", flags=re.IGNORECASE)


class FactCandidateGenerationError(RuntimeError):
    """Raised when candidate generation cannot continue."""


class FactCandidateArtifactBoundaryError(RuntimeError):
    """Raised when report output would escape its artifact boundary."""


class FactCandidateSecretError(RuntimeError):
    """Raised when a candidate payload contains secret-like data."""


def build_fact_candidates_from_comparison_dir(code_dir: Path) -> dict[str, Any]:
    """Build an in-memory fact-candidate report from one comparison code dir.

    The function reads only files already present under ``code_dir``. It never
    reads environment variables and never imports or calls provider runtimes.
    """

    code_dir = Path(code_dir)
    if not code_dir.exists() or not code_dir.is_dir():
        raise FactCandidateGenerationError(f"comparison code dir does not exist: {code_dir}")

    code = _normalize_code(code_dir.name)
    artifacts = _load_artifacts(code_dir)
    candidates: list[dict[str, Any]] = []

    for provider in PROVIDERS:
        provider_artifacts = artifacts["provider_payloads"][provider]
        candidates.extend(_extract_provider_candidates(code, provider, provider_artifacts))

    _apply_provider_conflicts(candidates)
    payload = {
        "code": code,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "mode": MODE,
        "source_artifacts": artifacts["source_artifacts"],
        "candidates": candidates,
        "summary": _build_summary(candidates, artifacts["unreadable_artifacts"]),
    }
    _assert_payload_has_required_candidate_keys(payload)
    _assert_no_forbidden_recommendation_keys(payload)
    _assert_no_secret_like_payload(payload)
    return payload


def write_fact_candidate_report(payload: dict[str, Any], output_root: Path, timestamp: str) -> Path:
    """Write ``fact_candidates.json`` inside a timestamp/code artifact boundary."""

    _assert_no_secret_like_payload(payload)
    _assert_no_forbidden_recommendation_keys(payload)

    code = _normalize_code(str(payload.get("code", "")))
    if not _TIMESTAMP_RE.fullmatch(str(timestamp)) or ".." in str(timestamp):
        raise FactCandidateArtifactBoundaryError("timestamp contains unsupported path characters")

    root = Path(output_root)
    root_resolved = root.resolve(strict=False)
    report_path = root / str(timestamp) / code / "fact_candidates.json"
    report_resolved = report_path.resolve(strict=False)
    try:
        report_resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise FactCandidateArtifactBoundaryError("candidate report path escapes output root") from exc
    if report_resolved.name != "fact_candidates.json":
        raise FactCandidateArtifactBoundaryError("candidate writer may only write fact_candidates.json")

    report_resolved.parent.mkdir(parents=True, exist_ok=True)
    report_resolved.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return report_resolved


def _load_artifacts(code_dir: Path) -> dict[str, Any]:
    source_artifacts: dict[str, str] = {}
    unreadable_artifacts: list[str] = []
    provider_payloads: dict[str, dict[str, Any]] = {}

    for provider in PROVIDERS:
        fundamental_name = FUNDAMENTAL_ARTIFACTS[provider]
        raw_name = RAW_ARTIFACTS[provider]
        fundamental = _load_json(code_dir / fundamental_name, unreadable_artifacts)
        raw = _load_json(code_dir / raw_name, unreadable_artifacts)

        if (code_dir / fundamental_name).exists():
            source_artifacts[f"{provider}_fundamental"] = fundamental_name
        if (code_dir / raw_name).exists():
            source_artifacts[f"{provider}_raw"] = raw_name

        value_payload, value_artifact = _choose_value_payload(
            fundamental=fundamental,
            raw=raw,
            fundamental_name=fundamental_name,
            raw_name=raw_name,
        )
        provider_payloads[provider] = {
            "fundamental": fundamental,
            "raw": raw,
            "value_payload": value_payload,
            "source_artifact": value_artifact,
        }

    for artifact_name in OPTIONAL_ARTIFACTS:
        path = code_dir / artifact_name
        if path.exists():
            source_artifacts[artifact_name.removesuffix(".json")] = artifact_name
            _load_json(path, unreadable_artifacts)

    return {
        "source_artifacts": source_artifacts,
        "provider_payloads": provider_payloads,
        "unreadable_artifacts": unreadable_artifacts,
    }


def _load_json(path: Path, unreadable_artifacts: list[str]) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        unreadable_artifacts.append(path.name)
        return None
    if isinstance(payload, dict):
        return payload
    unreadable_artifacts.append(path.name)
    return None


def _choose_value_payload(
    *,
    fundamental: dict[str, Any] | None,
    raw: dict[str, Any] | None,
    fundamental_name: str,
    raw_name: str,
) -> tuple[dict[str, Any] | None, str | None]:
    if _has_extractable_blocks(fundamental):
        return fundamental, fundamental_name
    if _has_extractable_blocks(raw):
        return raw, raw_name
    if fundamental:
        return fundamental, fundamental_name
    if raw:
        return raw, raw_name
    return None, None


def _has_extractable_blocks(payload: dict[str, Any] | None) -> bool:
    if not isinstance(payload, dict):
        return False
    blocks = payload.get("blocks")
    if isinstance(blocks, dict) and any(name in blocks for aliases in BLOCK_ALIASES.values() for name in aliases):
        return True
    return any(name in payload for aliases in BLOCK_ALIASES.values() for name in aliases)


def _extract_provider_candidates(
    code: str,
    provider: str,
    provider_artifacts: dict[str, Any],
) -> list[dict[str, Any]]:
    value_payload = provider_artifacts["value_payload"]
    source_artifact = provider_artifacts["source_artifact"]
    if not isinstance(value_payload, dict) or not source_artifact:
        return []

    trace_payload = provider_artifacts.get("raw") or value_payload
    candidates: list[dict[str, Any]] = []
    candidates.extend(
        _extract_block_candidates(
            code=code,
            provider=provider,
            payload=value_payload,
            trace_payload=trace_payload,
            canonical_block="basic_info",
            fields=BASIC_FIELDS,
            source_artifact=source_artifact,
        )
    )
    candidates.extend(
        _extract_block_candidates(
            code=code,
            provider=provider,
            payload=value_payload,
            trace_payload=trace_payload,
            canonical_block="financial_metrics",
            fields=FINANCIAL_FIELDS,
            source_artifact=source_artifact,
        )
    )
    candidates.extend(
        _extract_block_candidates(
            code=code,
            provider=provider,
            payload=value_payload,
            trace_payload=trace_payload,
            canonical_block="valuation_metrics",
            fields=VALUATION_FIELDS,
            source_artifact=source_artifact,
        )
    )
    candidates.extend(
        _extract_block_candidates(
            code=code,
            provider=provider,
            payload=value_payload,
            trace_payload=trace_payload,
            canonical_block="business_composition",
            fields=BUSINESS_COMPOSITION_FIELDS,
            source_artifact=source_artifact,
        )
    )
    return candidates


def _extract_block_candidates(
    *,
    code: str,
    provider: str,
    payload: dict[str, Any],
    trace_payload: dict[str, Any],
    canonical_block: str,
    fields: tuple[str, ...],
    source_artifact: str,
) -> list[dict[str, Any]]:
    source_block = _source_block_for_payload(payload, canonical_block)
    rows = _block_rows(payload, canonical_block)
    if canonical_block == "basic_info" and not rows:
        rows = [_synthesize_basic_info_row(payload)]
    rows = [row for row in rows if row]
    if not rows:
        return []

    candidates: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows):
        for field in fields:
            if not _field_is_present(row, field, canonical_block):
                continue
            value = _field_value(row, field, canonical_block)
            field_path = _field_path(canonical_block, field, row_index, len(rows))
            trace = _trace_for_field(trace_payload, row, source_block, field, row_index)
            candidate = _build_candidate(
                code=code,
                provider=provider,
                source_artifact=source_artifact,
                source_block=canonical_block,
                raw_block=source_block,
                row=row,
                row_index=row_index,
                field=field,
                field_path=field_path,
                value=value,
                trace=trace,
            )
            candidates.append(candidate)
    return candidates


def _build_candidate(
    *,
    code: str,
    provider: str,
    source_artifact: str,
    source_block: str,
    raw_block: str,
    row: dict[str, Any],
    row_index: int,
    field: str,
    field_path: str,
    value: Any,
    trace: dict[str, Any] | None,
) -> dict[str, Any]:
    metadata = _field_metadata(row, field)
    report_period = _report_period_for(source_block, field, row, value, trace)
    as_of_date = _as_of_date_for(source_block, field, row, value, trace)
    value = _normalize_value(source_block, field, value)
    data_unit, canonical_unit = _units_for(source_block, field, value, metadata)
    source_endpoint = _source_endpoint(trace, metadata)
    source_trace = _source_trace(
        code=code,
        provider=provider,
        artifact_file=source_artifact,
        source_block=source_block,
        raw_block=raw_block,
        row=row,
        row_index=row_index,
        field=field,
        trace=trace,
        endpoint=source_endpoint,
        report_period=report_period,
        as_of_date=as_of_date,
    )
    derived = _bool_or_default(metadata.get("derived"), _bool_or_default(_trace_value(trace, "derived"), False))
    derivation_method = metadata.get("derivation_method") or _trace_value(trace, "derivation_method")

    candidate = {
        "field_path": field_path,
        "value": value,
        "source_provider": provider,
        "source_artifact": source_artifact,
        "source_block": source_block,
        "source_endpoint": source_endpoint,
        "source_trace": source_trace,
        "report_period": report_period,
        "ann_date": _first_present(metadata.get("ann_date"), _trace_value(trace, "ann_date")),
        "disclosure_date": _first_present(metadata.get("disclosure_date"), _trace_value(trace, "disclosure_date")),
        "as_of_date": as_of_date,
        "data_unit": data_unit,
        "canonical_unit": canonical_unit,
        "derived": derived,
        "derivation_method": derivation_method,
        "confidence": "medium",
        "review_status": "manual_review_required",
        "missing_category": "manual_review_required",
        "conflict_status": "not_compared",
        "manual_review_note": "",
    }
    _apply_initial_review(candidate)
    return candidate


def _apply_initial_review(candidate: dict[str, Any]) -> None:
    field_path = _normalized_simple_field_path(candidate["field_path"])
    value = candidate["value"]

    if value is None:
        candidate.update(
            confidence="unavailable",
            review_status="not_available",
            missing_category="not_available",
            manual_review_note="Provider did not supply a value for this candidate field.",
        )
        return

    if field_path == "basic_info.main_business":
        candidate.update(
            confidence="low",
            review_status="manual_review_required",
            missing_category="manual_review_required",
            manual_review_note="main_business is narrative text and is not auto-accepted in V1.",
        )
        return

    if field_path.startswith("basic_info.") or field_path in TEXT_FIELDS or _is_business_text_field(field_path):
        candidate.update(
            confidence="medium" if candidate["source_provider"] == "tushare" else "low",
            review_status="manual_review_required",
            missing_category="manual_review_required",
            manual_review_note="Text or identity fields require review in V1.",
        )
        return

    if field_path.startswith("business_composition."):
        if not _business_row_has_classification(candidate):
            candidate.update(
                confidence="low",
                review_status="mapping_missing",
                missing_category="mapping_missing",
                manual_review_note="business_composition classification_type is missing or unclear.",
            )
        else:
            candidate.update(
                confidence="medium" if candidate["source_provider"] == "tushare" else "low",
                review_status="manual_review_required",
                missing_category="manual_review_required",
                manual_review_note="business_composition rows require classification and denominator review in V1.",
            )
        return

    if not candidate["data_unit"] or not candidate["canonical_unit"]:
        candidate.update(
            confidence="low",
            review_status="unit_unknown",
            missing_category="unit_unknown",
            manual_review_note="Unit or canonical unit is not explicit enough for auto acceptance.",
        )
        return

    if _requires_report_period(field_path) and not candidate["report_period"]:
        candidate.update(
            confidence="low",
            review_status="period_mismatch",
            missing_category="period_mismatch",
            manual_review_note="Report period is missing for a period-sensitive field.",
        )
        return

    if _requires_as_of_date(field_path) and not candidate["as_of_date"]:
        candidate.update(
            confidence="low",
            review_status="period_mismatch",
            missing_category="period_mismatch",
            manual_review_note="As-of date is missing for a date-sensitive valuation field.",
        )
        return

    if candidate["source_provider"] != "tushare":
        candidate.update(
            confidence="medium",
            review_status="manual_review_required",
            missing_category="manual_review_required",
            manual_review_note="AkShare candidates are emitted for review but not auto-accepted in V1.",
        )
        return

    if not candidate["source_endpoint"]:
        candidate.update(
            confidence="low",
            review_status="mapping_missing",
            missing_category="mapping_missing",
            manual_review_note="Source endpoint/function metadata is missing.",
        )
        return

    candidate.update(
        confidence="high",
        review_status="auto_accepted",
        missing_category=None,
        manual_review_note="",
    )


def _apply_provider_conflicts(candidates: list[dict[str, Any]]) -> None:
    by_field: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates:
        by_field.setdefault(candidate["field_path"], []).append(candidate)

    for group in by_field.values():
        tushare_items = [item for item in group if item["source_provider"] == "tushare" and item["value"] is not None]
        akshare_items = [item for item in group if item["source_provider"] == "akshare" and item["value"] is not None]
        if not tushare_items or not akshare_items:
            for item in group:
                if item["conflict_status"] == "not_compared":
                    item["conflict_status"] = "provider_missing"
            continue

        for tushare_item in tushare_items:
            for akshare_item in akshare_items:
                status = _compare_candidates(tushare_item, akshare_item)
                _mark_conflict_result(tushare_item, status)
                _mark_conflict_result(akshare_item, status)


def _compare_candidates(left: dict[str, Any], right: dict[str, Any]) -> str:
    field_path = _normalized_simple_field_path(left["field_path"])
    if left["report_period"] and right["report_period"] and left["report_period"] != right["report_period"]:
        return "period_mismatch"
    if field_path.startswith("valuation_metrics.") and left["as_of_date"] and right["as_of_date"]:
        if left["as_of_date"] != right["as_of_date"]:
            return "period_mismatch"
    if field_path.startswith("business_composition."):
        left_selector = left["source_trace"].get("row_selector", {})
        right_selector = right["source_trace"].get("row_selector", {})
        if left_selector.get("classification_type") != right_selector.get("classification_type"):
            return "period_mismatch"
        if left_selector.get("segment_name") != right_selector.get("segment_name"):
            return "period_mismatch"

    left_value = _canonical_numeric_value(left)
    right_value = _canonical_numeric_value(right)
    if left_value is None or right_value is None:
        return "text_manual_review"

    if _is_ratio_field(field_path):
        return "within_tolerance" if abs(left_value - right_value) <= 0.5 else "source_conflict"

    denominator = max(abs(left_value), abs(right_value), 1.0)
    relative_error = abs(left_value - right_value) / denominator
    return "within_tolerance" if relative_error <= 0.01 else "source_conflict"


def _mark_conflict_result(candidate: dict[str, Any], status: str) -> None:
    if status == "within_tolerance":
        if candidate["conflict_status"] in {"not_compared", "provider_missing"}:
            candidate["conflict_status"] = "within_tolerance"
        return
    if status == "text_manual_review":
        if candidate["conflict_status"] in {"not_compared", "provider_missing"}:
            candidate["conflict_status"] = "text_manual_review"
        return

    candidate["conflict_status"] = status
    if status == "source_conflict":
        candidate.update(
            confidence="low",
            review_status="source_conflict",
            missing_category="source_conflict",
            manual_review_note="Provider values differ beyond V1 tolerance and require review.",
        )
    elif status == "period_mismatch":
        candidate.update(
            confidence="low",
            review_status="period_mismatch",
            missing_category="period_mismatch",
            manual_review_note="Provider periods or valuation as-of dates are not comparable.",
        )


def _build_summary(candidates: list[dict[str, Any]], unreadable_artifacts: list[str]) -> dict[str, Any]:
    def count_status(status: str) -> int:
        return sum(1 for candidate in candidates if candidate["review_status"] == status)

    return {
        "candidate_count": len(candidates),
        "auto_accepted_count": count_status("auto_accepted"),
        "manual_review_required_count": count_status("manual_review_required"),
        "source_conflict_count": count_status("source_conflict"),
        "unit_unknown_count": count_status("unit_unknown"),
        "period_mismatch_count": count_status("period_mismatch"),
        "mapping_missing_count": count_status("mapping_missing"),
        "not_available_count": count_status("not_available"),
        "provider_missing_count": sum(1 for candidate in candidates if candidate["conflict_status"] == "provider_missing"),
        "unreadable_artifacts": sorted(set(unreadable_artifacts)),
    }


def _block_rows(payload: dict[str, Any], canonical_block: str) -> list[dict[str, Any]]:
    for alias in BLOCK_ALIASES[canonical_block]:
        value = _nested_blocks(payload).get(alias)
        rows = _as_rows(value)
        if rows:
            return rows
    for alias in BLOCK_ALIASES[canonical_block]:
        rows = _as_rows(payload.get(alias))
        if rows:
            return rows
    return []


def _source_block_for_payload(payload: dict[str, Any], canonical_block: str) -> str:
    blocks = _nested_blocks(payload)
    for alias in BLOCK_ALIASES[canonical_block]:
        if alias in blocks:
            return alias
    for alias in BLOCK_ALIASES[canonical_block]:
        if alias in payload:
            return alias
    return SOURCE_BLOCK_BY_CANONICAL[canonical_block]


def _nested_blocks(payload: dict[str, Any]) -> dict[str, Any]:
    blocks = payload.get("blocks")
    return blocks if isinstance(blocks, dict) else {}


def _as_rows(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [row for row in value if isinstance(row, dict)]
    return []


def _synthesize_basic_info_row(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        field: payload.get(field)
        for field in BASIC_FIELDS
        if field in payload and payload.get(field) is not None
    }


def _field_is_present(row: dict[str, Any], field: str, canonical_block: str) -> bool:
    if field in row:
        return True
    if canonical_block == "valuation_metrics" and field == "as_of_date":
        return "period" in row
    return False


def _field_value(row: dict[str, Any], field: str, canonical_block: str) -> Any:
    if canonical_block == "valuation_metrics" and field == "as_of_date":
        return row.get("as_of_date", row.get("period"))
    return row.get(field)


def _field_path(canonical_block: str, field: str, row_index: int, row_count: int) -> str:
    if canonical_block == "business_composition":
        return f"business_composition[{row_index}].{field}"
    del row_index, row_count
    return f"{canonical_block}.{field}"


def _field_metadata(row: dict[str, Any], field: str) -> dict[str, Any]:
    for key in ("field_metadata", "metadata", "_field_metadata"):
        metadata = row.get(key)
        if isinstance(metadata, dict) and isinstance(metadata.get(field), dict):
            return dict(metadata[field])
    return {}


def _trace_for_field(
    trace_payload: dict[str, Any],
    row: dict[str, Any],
    source_block: str,
    field: str,
    row_index: int,
) -> dict[str, Any] | None:
    row_trace = _trace_from_row(row, field)
    if row_trace:
        return row_trace

    trace_rows: list[dict[str, Any]] = []
    fetch_status = trace_payload.get("fetch_status")
    if isinstance(fetch_status, dict):
        for alias in _block_lookup_aliases(source_block):
            status = fetch_status.get(alias)
            if isinstance(status, dict):
                trace_rows.extend(_as_rows(status.get("source_trace")))
    trace_rows.extend(_as_rows(trace_payload.get("source_trace")))

    exact_matches = [
        trace
        for trace in trace_rows
        if str(trace.get("field_name", "")).lower() == field.lower()
        or str(trace.get("field", "")).lower() == field.lower()
    ]
    for trace in exact_matches:
        if "value" not in trace or _loosely_equal(trace.get("value"), row.get(field)):
            return trace
    if exact_matches:
        return exact_matches[min(row_index, len(exact_matches) - 1)]

    for trace in trace_rows:
        if field == "period" and trace.get("source_period"):
            return trace
        if source_block == "business_composition" and trace.get("field_name") == "segments":
            return trace
    return None


def _trace_from_row(row: dict[str, Any], field: str) -> dict[str, Any] | None:
    trace = row.get("source_trace")
    if isinstance(trace, dict):
        return trace
    for item in _as_rows(trace):
        if item.get("field_name") == field or item.get("field") == field:
            return item
    field_traces = row.get("field_source_trace")
    if isinstance(field_traces, dict) and isinstance(field_traces.get(field), dict):
        return field_traces[field]
    return None


def _block_lookup_aliases(source_block: str) -> tuple[str, ...]:
    aliases = [source_block]
    for values in BLOCK_ALIASES.values():
        if source_block in values:
            aliases.extend(alias for alias in values if alias not in aliases)
    return tuple(aliases)


def _source_endpoint(trace: dict[str, Any] | None, metadata: dict[str, Any]) -> str | None:
    for value in (
        metadata.get("source_endpoint"),
        metadata.get("endpoint"),
        _trace_value(trace, "function_name"),
        _trace_value(trace, "source_function"),
        _trace_value(trace, "endpoint"),
        _trace_value(trace, "source_endpoint"),
    ):
        if value:
            return str(value)
    return None


def _source_trace(
    *,
    code: str,
    provider: str,
    artifact_file: str,
    source_block: str,
    raw_block: str,
    row: dict[str, Any],
    row_index: int,
    field: str,
    trace: dict[str, Any] | None,
    endpoint: str | None,
    report_period: str | None,
    as_of_date: str | None,
) -> dict[str, Any]:
    row_selector = {
        key: value
        for key, value in {
            "report_period": report_period,
            "as_of_date": as_of_date,
            "segment_name": row.get("segment_name") if source_block == "business_composition" else None,
            "classification_type": row.get("classification_type") if source_block == "business_composition" else None,
        }.items()
        if value is not None
    }
    source_trace: dict[str, Any] = {
        "artifact_file": artifact_file,
        "code": code,
        "provider": provider,
        "block": source_block,
        "raw_block": raw_block,
        "field_name": field,
        "json_pointer": f"/blocks/{raw_block}/{row_index}/{field}",
        "row_selector": row_selector,
    }
    if endpoint:
        source_trace["endpoint"] = endpoint
    for key in (
        "source_field",
        "source_indicator",
        "source_column",
        "source_column_or_row",
        "statement_type",
        "period_confidence",
        "value_confidence",
        "unit_confidence",
        "denominator_scope",
    ):
        value = _trace_value(trace, key)
        if value is not None:
            source_trace[key] = value
    source_period = _trace_value(trace, "source_period")
    if source_period is not None:
        source_trace["source_period"] = _normalize_date(source_period)
    return _sanitize_trace(source_trace)


def _sanitize_trace(trace: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in trace.items():
        if key in {"cache_path", "raw_data_path", "local_path", "path"}:
            continue
        if isinstance(value, dict):
            sanitized[key] = _sanitize_trace(value)
        elif isinstance(value, list):
            sanitized[key] = [
                _sanitize_trace(item) if isinstance(item, dict) else item
                for item in value
                if not _looks_like_forbidden_string(item)
            ]
        elif not _looks_like_forbidden_string(value):
            sanitized[key] = value
    return sanitized


def _looks_like_forbidden_string(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return bool(_LOCAL_SECRET_PATH_RE.search(value) or _MCP_RE.search(value))


def _report_period_for(
    source_block: str,
    field: str,
    row: dict[str, Any],
    value: Any,
    trace: dict[str, Any] | None,
) -> str | None:
    if source_block == "financial_metrics":
        return _normalize_date(value if field == "period" else _first_present(row.get("period"), _trace_value(trace, "source_period")))
    if source_block == "business_composition":
        return _normalize_date(value if field == "period" else _first_present(row.get("period"), _trace_value(trace, "source_period")))
    return None


def _as_of_date_for(
    source_block: str,
    field: str,
    row: dict[str, Any],
    value: Any,
    trace: dict[str, Any] | None,
) -> str | None:
    if source_block == "valuation_metrics":
        return _normalize_date(value if field == "as_of_date" else _first_present(row.get("as_of_date"), row.get("period"), _trace_value(trace, "source_period")))
    return None


def _normalize_value(source_block: str, field: str, value: Any) -> Any:
    if value is None:
        return None
    if source_block == "basic_info" and field == "listing_date":
        return _normalize_date(value)
    if source_block in {"financial_metrics", "business_composition"} and field == "period":
        return _normalize_date(value)
    if source_block == "valuation_metrics" and field == "as_of_date":
        return _normalize_date(value)
    return value


def _normalize_date(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if _DATE10_RE.fullmatch(text):
        return text
    if _DATE8_RE.fullmatch(text):
        return f"{text[0:4]}-{text[4:6]}-{text[6:8]}"
    return text or None


def _units_for(source_block: str, field: str, value: Any, metadata: dict[str, Any]) -> tuple[str | None, str | None]:
    if "data_unit" in metadata or "canonical_unit" in metadata:
        return metadata.get("data_unit"), metadata.get("canonical_unit")

    simple_path = f"{source_block}.{field}"
    if simple_path in AMOUNT_FIELDS or (source_block == "business_composition" and field == "revenue"):
        return "RMB yuan", "RMB yuan"
    if simple_path in RATIO_FIELDS or (source_block == "business_composition" and field in {"revenue_ratio", "gross_margin"}):
        data_unit = "ratio_fraction" if _is_number(value) and abs(float(value)) <= 1 else "percentage_point"
        return data_unit, "percentage_point"
    if simple_path in VALUATION_MULTIPLE_FIELDS:
        return "multiple", "multiple"
    if simple_path in DATE_FIELDS:
        return "date" if field != "period" else "report_period", "date" if field != "period" else "report_period"
    if simple_path in TEXT_FIELDS or _is_business_text_field(simple_path):
        return "text", "text"
    return None, None


def _canonical_numeric_value(candidate: dict[str, Any]) -> float | None:
    value = candidate.get("value")
    if not _is_number(value):
        return None
    numeric = float(value)
    unit = str(candidate.get("data_unit") or "").lower()
    canonical = str(candidate.get("canonical_unit") or "").lower()
    if canonical == "percentage_point":
        if unit in {"ratio_fraction", "fraction", "decimal_ratio"}:
            return numeric * 100
        return numeric
    if canonical == "rmb yuan":
        multiplier = _amount_unit_multiplier(unit)
        if multiplier is None:
            return None
        return numeric * multiplier
    return numeric


def _amount_unit_multiplier(unit: str) -> float | None:
    normalized = unit.replace("-", " ").replace("_", " ").strip()
    if normalized in {"rmb yuan", "yuan", "cny", "rmb", ""}:
        return 1.0
    if normalized in {"rmb thousand", "thousand rmb", "thousand yuan"}:
        return 1000.0
    if normalized in {"rmb ten thousand", "ten thousand rmb", "10k rmb", "wan yuan"}:
        return 10000.0
    if normalized in {"rmb hundred million", "hundred million rmb", "100m rmb", "yi yuan"}:
        return 100000000.0
    return None


def _trace_value(trace: dict[str, Any] | None, key: str) -> Any:
    if isinstance(trace, dict):
        return trace.get(key)
    return None


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _bool_or_default(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.lower() in {"true", "yes", "1"}:
            return True
        if value.lower() in {"false", "no", "0"}:
            return False
    return default


def _normalized_simple_field_path(field_path: str) -> str:
    return re.sub(r"business_composition\[\d+\]\.", "business_composition.", field_path)


def _is_business_text_field(field_path: str) -> bool:
    return field_path in {"business_composition.segment_name", "business_composition.classification_type"}


def _business_row_has_classification(candidate: dict[str, Any]) -> bool:
    selector = candidate.get("source_trace", {}).get("row_selector", {})
    return bool(selector.get("classification_type"))


def _requires_report_period(field_path: str) -> bool:
    return field_path.startswith("financial_metrics.") or field_path.startswith("business_composition")


def _requires_as_of_date(field_path: str) -> bool:
    return field_path in {
        "valuation_metrics.pe_ttm",
        "valuation_metrics.pb",
        "valuation_metrics.market_cap",
        "valuation_metrics.as_of_date",
    }


def _is_ratio_field(field_path: str) -> bool:
    return field_path in RATIO_FIELDS or field_path in BUSINESS_RATIO_FIELDS


def _is_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return math.isfinite(float(value))
    if isinstance(value, str):
        try:
            return math.isfinite(float(value))
        except ValueError:
            return False
    return False


def _loosely_equal(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return False
    if _is_number(left) and _is_number(right):
        return abs(float(left) - float(right)) <= max(abs(float(left)), abs(float(right)), 1.0) * 0.000001
    return str(left) == str(right)


def _assert_payload_has_required_candidate_keys(payload: dict[str, Any]) -> None:
    for candidate in payload.get("candidates", []):
        missing = set(REQUIRED_CANDIDATE_KEYS) - set(candidate)
        if missing:
            raise FactCandidateGenerationError(f"candidate is missing required keys: {sorted(missing)}")


def _assert_no_forbidden_recommendation_keys(payload: Any) -> None:
    for key in _walk_keys(payload):
        if key.lower() in FORBIDDEN_RECOMMENDATION_KEYS:
            raise FactCandidateGenerationError("candidate payload contains investment recommendation fields")


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _assert_no_secret_like_payload(payload: Any) -> None:
    finding = _first_secret_like_finding(payload, "$")
    if finding:
        raise FactCandidateSecretError(f"candidate payload contains secret-like data at {finding}: <masked>")


def _first_secret_like_finding(value: Any, path: str) -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{_safe_path_key(str(key))}"
            if _SECRET_KEY_RE.search(str(key)) and child not in (None, "", "<masked>", "<redacted>"):
                return child_path
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
        if _KEYED_SECRET_RE.search(value) or _BEARER_RE.search(value) or _MCP_RE.search(value):
            return path
        if _LOCAL_SECRET_PATH_RE.search(value):
            return path
        if _TOKEN_LIKE_RE.search(value) and _SECRET_KEY_RE.search(_nearby_text(value)):
            return path
        if _TOKEN_LIKE_RE.fullmatch(value.strip()):
            return path
    return None


def _nearby_text(text: str) -> str:
    return text[:160]


def _safe_path_key(key: str) -> str:
    if _SECRET_KEY_RE.search(key) or _TOKEN_LIKE_RE.search(key):
        return "<masked_key>"
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,63}", key):
        return key
    return "<key>"


def _normalize_code(code: str) -> str:
    code = str(code).strip()
    if not _STOCK_CODE_RE.fullmatch(code) or ".." in code:
        raise FactCandidateArtifactBoundaryError("code contains unsupported path characters")
    return code
