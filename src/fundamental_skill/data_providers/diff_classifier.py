# -*- coding: utf-8 -*-
"""Diff classification for provider-separated comparison reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Iterable, Mapping

from .token_leak_scanner import scan_for_token_leaks


class DiffCategory(str, Enum):
    EXACT_MATCH = "exact_match"
    EXPECTED_PROVIDER_DIFFERENCE = "expected_provider_difference"
    HARMLESS_FORMAT_DIFFERENCE = "harmless_format_difference"
    UNIT_DIFFERENCE = "unit_difference"
    MISSING_FIELD_IMPROVEMENT = "missing_field_improvement"
    MISSING_FIELD_REGRESSION = "missing_field_regression"
    STALE_OR_FAILED_AKSHARE_FIELD = "stale_or_failed_akshare_field"
    TUSHARE_PERMISSION_MISSING = "tushare_permission_missing"
    CANONICAL_MAPPING_ISSUE = "canonical_mapping_issue"
    STRATEGY_TYPE_DRIFT = "strategy_type_drift"
    CLASSIFICATION_DRIFT = "classification_drift"
    CONFIDENCE_DRIFT = "confidence_drift"
    SCORE_DRIFT = "score_drift"
    P1_QUESTION_DRIFT = "P1_question_drift"
    SAFETY_BOUNDARY_RISK = "safety_boundary_risk"
    TOKEN_OR_SECRET_RISK = "token_or_secret_risk"


class DriftSubcategory(str, Enum):
    MISSING_FIELD = "missing_field"
    UNIT_DIFF = "unit_diff"
    PROVIDER_COVERAGE_CAVEAT = "provider_coverage_caveat"
    DOMAIN_EVIDENCE_MISSING = "domain_evidence_missing"
    SCORING_PENALTY_DUE_TO_PROVIDER_GAP = "scoring_penalty_due_to_provider_gap"
    MAPPING_GAP = "mapping_gap"
    READINESS_CAP = "readiness_cap"
    EXTERNAL_SIDECAR_MISSING = "external_sidecar_missing"


DRIFT_SUBCATEGORY_VALUES: tuple[str, ...] = tuple(item.value for item in DriftSubcategory)


REVIEW_REQUIRED_CATEGORIES = {
    DiffCategory.STRATEGY_TYPE_DRIFT,
    DiffCategory.CLASSIFICATION_DRIFT,
    DiffCategory.CONFIDENCE_DRIFT,
    DiffCategory.SCORE_DRIFT,
    DiffCategory.P1_QUESTION_DRIFT,
    DiffCategory.SAFETY_BOUNDARY_RISK,
    DiffCategory.TOKEN_OR_SECRET_RISK,
}


@dataclass(frozen=True)
class DiffItem:
    category: str
    field_path: str
    akshare_value: Any
    tushare_value: Any
    severity: str
    review_required: bool
    note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def make_diff_item(
    category: DiffCategory | str,
    field_path: str,
    akshare_value: Any,
    tushare_value: Any,
    *,
    note: str = "",
    severity: str | None = None,
    review_required: bool | None = None,
) -> DiffItem:
    parsed = DiffCategory(category)
    return DiffItem(
        category=parsed.value,
        field_path=field_path,
        akshare_value=akshare_value,
        tushare_value=tushare_value,
        severity=severity or _severity_for(parsed),
        review_required=_review_required_for(parsed) if review_required is None else review_required,
        note=note or _default_note_for(parsed),
    )


def classify_field_diff(
    field_path: str,
    akshare_value: Any,
    tushare_value: Any,
    *,
    akshare_missing: bool | None = None,
    tushare_missing: bool | None = None,
    akshare_status: Mapping[str, Any] | None = None,
    tushare_status: Mapping[str, Any] | None = None,
) -> DiffItem:
    """Classify one provider field difference without accepting drift."""

    if _contains_secret_risk(akshare_value) or _contains_secret_risk(tushare_value):
        return make_diff_item(
            DiffCategory.TOKEN_OR_SECRET_RISK,
            field_path,
            "<masked>",
            "<masked>",
            note="Token-like or connection-secret text detected in compared values.",
        )

    if akshare_value == tushare_value:
        return make_diff_item(DiffCategory.EXACT_MATCH, field_path, akshare_value, tushare_value)

    ak_missing = _is_missing(akshare_value) if akshare_missing is None else akshare_missing
    ts_missing = _is_missing(tushare_value) if tushare_missing is None else tushare_missing
    lowered = field_path.lower()

    if "research_questions" in lowered or "research_questions_p1" in lowered:
        return make_diff_item(DiffCategory.P1_QUESTION_DRIFT, field_path, akshare_value, tushare_value)
    if lowered.endswith("strategy_type"):
        return make_diff_item(DiffCategory.STRATEGY_TYPE_DRIFT, field_path, akshare_value, tushare_value)
    if lowered.endswith("sub_type"):
        return make_diff_item(DiffCategory.CLASSIFICATION_DRIFT, field_path, akshare_value, tushare_value)
    if lowered.endswith("confidence") or ".confidence" in lowered:
        return make_diff_item(DiffCategory.CONFIDENCE_DRIFT, field_path, akshare_value, tushare_value)
    if lowered.endswith("score") or lowered.endswith("fundamental_score"):
        return make_diff_item(DiffCategory.SCORE_DRIFT, field_path, akshare_value, tushare_value)
    if _status_has_permission_error(tushare_status):
        return make_diff_item(DiffCategory.TUSHARE_PERMISSION_MISSING, field_path, akshare_value, tushare_value)
    if _status_failed(akshare_status) and not ts_missing:
        return make_diff_item(DiffCategory.STALE_OR_FAILED_AKSHARE_FIELD, field_path, akshare_value, tushare_value)
    if ak_missing and not ts_missing:
        return make_diff_item(DiffCategory.MISSING_FIELD_IMPROVEMENT, field_path, akshare_value, tushare_value)
    if not ak_missing and ts_missing:
        return make_diff_item(DiffCategory.MISSING_FIELD_REGRESSION, field_path, akshare_value, tushare_value)
    if _is_harmless_format_difference(akshare_value, tushare_value):
        return make_diff_item(DiffCategory.HARMLESS_FORMAT_DIFFERENCE, field_path, akshare_value, tushare_value)
    if _is_unit_difference(akshare_value, tushare_value):
        return make_diff_item(DiffCategory.UNIT_DIFFERENCE, field_path, akshare_value, tushare_value)

    return make_diff_item(DiffCategory.EXPECTED_PROVIDER_DIFFERENCE, field_path, akshare_value, tushare_value)


def canonical_mapping_issue(field_path: str, akshare_value: Any = None, tushare_value: Any = None, *, note: str = "") -> DiffItem:
    return make_diff_item(DiffCategory.CANONICAL_MAPPING_ISSUE, field_path, akshare_value, tushare_value, note=note)


def build_diff_report(
    *,
    code: str,
    akshare_raw: Mapping[str, Any],
    tushare_raw: Mapping[str, Any],
    akshare_fundamental: Mapping[str, Any] | None = None,
    tushare_fundamental: Mapping[str, Any] | None = None,
    akshare_evidence_pack: Mapping[str, Any] | None = None,
    tushare_evidence_pack: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a minimal comparison report over stable raw/fundamental/evidence fields."""

    items: list[DiffItem] = []
    for key in ("meta", "blocks", "fetch_status", "errors"):
        if key not in akshare_raw or key not in tushare_raw:
            items.append(canonical_mapping_issue(f"raw.{key}", akshare_raw.get(key), tushare_raw.get(key), note="Missing canonical raw top-level key."))

    raw_paths = (
        "blocks.basic_info",
        "blocks.business_composition",
        "blocks.financial_indicator",
        "blocks.valuation",
        "fetch_status",
    )
    for path in raw_paths:
        items.append(classify_field_diff(f"raw.{path}", _get_path(akshare_raw, path), _get_path(tushare_raw, path)))

    if akshare_fundamental is not None and tushare_fundamental is not None:
        for path in ("strategy_type", "sub_type", "status", "confidence", "fundamental_score", "missing_fields"):
            items.append(classify_field_diff(f"fundamental.{path}", _get_path(akshare_fundamental, path), _get_path(tushare_fundamental, path)))

    if akshare_evidence_pack is not None and tushare_evidence_pack is not None:
        for path in (
            "basic_info",
            "business_composition",
            "financial_metrics",
            "valuation_metrics",
            "missing_fields",
            "source_trace_summary",
            "stock.strategy_type",
            "stock.sub_type",
            "stock.status",
            "stock.confidence",
            "stock.fundamental_score",
        ):
            items.append(classify_field_diff(f"evidence_pack.{path}", _get_path(akshare_evidence_pack, path), _get_path(tushare_evidence_pack, path)))

    return {
        "code": code,
        "diff_items": [item.to_dict() for item in items],
        "summary": summarize_diff_items(items),
        "automatic_acceptance": False,
    }


def summarize_diff_items(items: Iterable[DiffItem]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    blocker_count = 0
    review_count = 0
    for item in items:
        counts[item.category] = counts.get(item.category, 0) + 1
        if item.severity == "blocker":
            blocker_count += 1
        if item.review_required:
            review_count += 1
    return {
        "category_counts": counts,
        "blocker_count": blocker_count,
        "review_required_count": review_count,
    }


def render_diff_report_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        f"# Provider Diff Report {report.get('code')}",
        "",
        "Automatic acceptance: false",
        "",
        "| category | field_path | severity | review_required | note |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in report.get("diff_items", []):
        if not isinstance(item, Mapping):
            continue
        lines.append(
            "| {category} | `{field_path}` | {severity} | {review_required} | {note} |".format(
                category=item.get("category", ""),
                field_path=item.get("field_path", ""),
                severity=item.get("severity", ""),
                review_required=item.get("review_required", ""),
                note=str(item.get("note", "")).replace("|", "/"),
            )
        )
    lines.append("")
    return "\n".join(lines)


def _get_path(payload: Mapping[str, Any], path: str) -> Any:
    current: Any = payload
    for part in path.split("."):
        if not isinstance(current, Mapping):
            return None
        current = current.get(part)
    return current


def _contains_secret_risk(value: Any) -> bool:
    return bool(scan_for_token_leaks(value).findings)


def _is_missing(value: Any) -> bool:
    return value in (None, "", [], {})


def _status_failed(status: Mapping[str, Any] | None) -> bool:
    return bool(status and (status.get("success") is False or status.get("error")))


def _status_has_permission_error(status: Mapping[str, Any] | None) -> bool:
    text = str(status or {}).lower()
    return "permission" in text or "denied" in text


def _is_harmless_format_difference(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return False
    return str(left).strip() == str(right).strip()


def _is_unit_difference(left: Any, right: Any) -> bool:
    try:
        left_num = float(str(left).strip().replace("%", ""))
        right_num = float(str(right).strip().replace("%", ""))
    except (TypeError, ValueError):
        return False
    if left_num == right_num:
        return False
    return abs(left_num * 100 - right_num) < 1e-9 or abs(right_num * 100 - left_num) < 1e-9


def _severity_for(category: DiffCategory) -> str:
    if category == DiffCategory.TOKEN_OR_SECRET_RISK:
        return "blocker"
    if category in REVIEW_REQUIRED_CATEGORIES:
        return "blocker"
    if category in {DiffCategory.EXACT_MATCH, DiffCategory.HARMLESS_FORMAT_DIFFERENCE, DiffCategory.EXPECTED_PROVIDER_DIFFERENCE}:
        return "info"
    return "review"


def _review_required_for(category: DiffCategory) -> bool:
    return category in REVIEW_REQUIRED_CATEGORIES or category in {
        DiffCategory.UNIT_DIFFERENCE,
        DiffCategory.MISSING_FIELD_REGRESSION,
        DiffCategory.TUSHARE_PERMISSION_MISSING,
        DiffCategory.CANONICAL_MAPPING_ISSUE,
    }


def _default_note_for(category: DiffCategory) -> str:
    return {
        DiffCategory.EXACT_MATCH: "Provider values match exactly.",
        DiffCategory.EXPECTED_PROVIDER_DIFFERENCE: "Provider values differ; review source trace before interpretation.",
        DiffCategory.HARMLESS_FORMAT_DIFFERENCE: "Values differ only by harmless formatting.",
        DiffCategory.UNIT_DIFFERENCE: "Values appear to use different units or scales.",
        DiffCategory.MISSING_FIELD_IMPROVEMENT: "Tushare fills a field missing from AkShare.",
        DiffCategory.MISSING_FIELD_REGRESSION: "Tushare is missing a field present in AkShare.",
        DiffCategory.STALE_OR_FAILED_AKSHARE_FIELD: "AkShare failed or appears stale while Tushare has data.",
        DiffCategory.TUSHARE_PERMISSION_MISSING: "Tushare field appears unavailable because of permission or endpoint access.",
        DiffCategory.CANONICAL_MAPPING_ISSUE: "Provider output violates or weakens the canonical mapping contract.",
        DiffCategory.STRATEGY_TYPE_DRIFT: "Strategy type drift requires manual review and must not be automatically accepted.",
        DiffCategory.CLASSIFICATION_DRIFT: "Classification drift requires manual review.",
        DiffCategory.CONFIDENCE_DRIFT: "Confidence drift requires manual review.",
        DiffCategory.SCORE_DRIFT: "Score drift requires manual review.",
        DiffCategory.P1_QUESTION_DRIFT: "P1.1 question drift requires manual review.",
        DiffCategory.SAFETY_BOUNDARY_RISK: "Safety boundary risk requires manual review.",
        DiffCategory.TOKEN_OR_SECRET_RISK: "Secret-like data must not enter comparison artifacts.",
    }[category]
