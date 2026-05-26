# -*- coding: utf-8 -*-
"""Read-only score / confidence explainability for provider comparison.

This module builds a diagnostic payload from already-produced comparison data.
It does not write files, call providers, read credentials, or recalculate final
scores.
"""

from __future__ import annotations

from typing import Any, Mapping


DRIFT_SUBCATEGORIES: tuple[str, ...] = (
    "missing_field",
    "unit_diff",
    "provider_coverage_caveat",
    "domain_evidence_missing",
    "scoring_penalty_due_to_provider_gap",
    "mapping_gap",
    "readiness_cap",
    "external_sidecar_missing",
)

DOMAIN_EVIDENCE_POLICY: dict[str, dict[str, Any]] = {
    "resource_swing": {
        "sidecar_policy": "commodity_prices are provider-independent evidence",
        "missing_policy": "mark external_sidecar_missing / provider_coverage_caveat",
    },
    "ai_datacenter_cooling": {
        "required_evidence_examples": [
            "liquid_cooling_revenue_share",
            "orders",
            "customer_validation",
            "batch_delivery",
        ],
        "missing_policy": "mark domain_evidence_missing",
    },
    "cxo": {
        "required_evidence_examples": [
            "backlog",
            "new_orders",
            "customer_region_exposure",
            "capacity_utilization",
        ],
        "missing_policy": "mark domain_evidence_missing when generic fundamentals cannot prove the domain claim",
    },
}


def build_score_confidence_explainability(
    *,
    code: str,
    akshare_raw: Mapping[str, Any],
    tushare_raw: Mapping[str, Any],
    akshare_fundamental: Mapping[str, Any],
    tushare_fundamental: Mapping[str, Any],
    akshare_evidence_pack: Mapping[str, Any],
    tushare_evidence_pack: Mapping[str, Any],
    diff_report: Mapping[str, Any] | None = None,
    artifact_refs: Mapping[str, Mapping[str, str]] | None = None,
) -> dict[str, Any]:
    """Build a diagnostic payload without mutating comparison inputs."""

    refs = _artifact_refs(artifact_refs)
    akshare_score = _score_from(akshare_fundamental, akshare_evidence_pack)
    tushare_score = _score_from(tushare_fundamental, tushare_evidence_pack)
    akshare_confidence = _confidence_from(akshare_fundamental, akshare_evidence_pack)
    tushare_confidence = _confidence_from(tushare_fundamental, tushare_evidence_pack)
    missing = _missing_field_summary(
        akshare_raw=akshare_raw,
        tushare_raw=tushare_raw,
        akshare_fundamental=akshare_fundamental,
        tushare_fundamental=tushare_fundamental,
        akshare_evidence_pack=akshare_evidence_pack,
        tushare_evidence_pack=tushare_evidence_pack,
    )
    provider_caveats = _provider_caveats(
        code=code,
        akshare_raw=akshare_raw,
        tushare_raw=tushare_raw,
        akshare_fundamental=akshare_fundamental,
        tushare_fundamental=tushare_fundamental,
        akshare_evidence_pack=akshare_evidence_pack,
        tushare_evidence_pack=tushare_evidence_pack,
        missing=missing,
    )
    drift_subcategory = _primary_drift_subcategory(
        code=code,
        missing=missing,
        provider_caveats=provider_caveats,
        diff_report=diff_report,
    )
    return {
        "code": _normalize_code(code),
        "providers": {
            "akshare": {"artifact_refs": refs["akshare"]},
            "tushare": {"artifact_refs": refs["tushare"]},
        },
        "automatic_acceptance": False,
        "explainability_only": True,
        "score_summary": {
            "akshare_score": akshare_score,
            "tushare_score": tushare_score,
            "score_delta": _numeric_delta(tushare_score, akshare_score),
            "score_drift_reason": _score_drift_reason(
                akshare_score=akshare_score,
                tushare_score=tushare_score,
                drift_subcategory=drift_subcategory,
                diff_report=diff_report,
            ),
        },
        "confidence_summary": {
            "akshare_confidence": akshare_confidence,
            "tushare_confidence": tushare_confidence,
            "confidence_delta": _confidence_delta(akshare_confidence, tushare_confidence),
            "confidence_drift_reason": _confidence_drift_reason(
                akshare_confidence=akshare_confidence,
                tushare_confidence=tushare_confidence,
                drift_subcategory=drift_subcategory,
                diff_report=diff_report,
            ),
        },
        "dimension_breakdown": _dimension_breakdown(
            akshare_fundamental=akshare_fundamental,
            tushare_fundamental=tushare_fundamental,
            missing=missing,
            provider_caveats=provider_caveats,
        ),
        "provider_caveats": provider_caveats,
        "derived_hints": _derived_hints(tushare_raw, tushare_evidence_pack),
        "domain_evidence_policy": DOMAIN_EVIDENCE_POLICY,
        "explainability_limitations": _explainability_limitations(
            akshare_fundamental=akshare_fundamental,
            tushare_fundamental=tushare_fundamental,
        ),
    }


def _artifact_refs(artifact_refs: Mapping[str, Mapping[str, str]] | None) -> dict[str, dict[str, str]]:
    if artifact_refs:
        return {
            "akshare": {
                "raw": _safe_ref(artifact_refs.get("akshare", {}).get("raw"), "akshare_raw.json"),
                "fundamental": _safe_ref(artifact_refs.get("akshare", {}).get("fundamental"), "akshare_fundamental.json"),
                "evidence_pack": _safe_ref(artifact_refs.get("akshare", {}).get("evidence_pack"), "akshare_evidence_pack.json"),
            },
            "tushare": {
                "raw": _safe_ref(artifact_refs.get("tushare", {}).get("raw"), "tushare_raw.json"),
                "fundamental": _safe_ref(artifact_refs.get("tushare", {}).get("fundamental"), "tushare_fundamental.json"),
                "evidence_pack": _safe_ref(artifact_refs.get("tushare", {}).get("evidence_pack"), "tushare_evidence_pack.json"),
            },
        }
    return {
        "akshare": {
            "raw": "akshare_raw.json",
            "fundamental": "akshare_fundamental.json",
            "evidence_pack": "akshare_evidence_pack.json",
        },
        "tushare": {
            "raw": "tushare_raw.json",
            "fundamental": "tushare_fundamental.json",
            "evidence_pack": "tushare_evidence_pack.json",
        },
    }


def _safe_ref(value: str | None, fallback: str) -> str:
    if not value:
        return fallback
    text = str(value).replace("\\", "/").strip()
    return text.rsplit("/", 1)[-1] or fallback


def _score_from(fundamental: Mapping[str, Any], evidence_pack: Mapping[str, Any]) -> Any:
    return _first_present(
        fundamental,
        ("fundamental_score", "score"),
        fallback=_get_path(evidence_pack, "stock.fundamental_score")
        if _get_path(evidence_pack, "stock.fundamental_score") is not None
        else _get_path(evidence_pack, "confidence_basis.score"),
    )


def _confidence_from(fundamental: Mapping[str, Any], evidence_pack: Mapping[str, Any]) -> Any:
    return _first_present(
        fundamental,
        ("confidence",),
        fallback=_get_path(evidence_pack, "stock.confidence")
        if _get_path(evidence_pack, "stock.confidence") is not None
        else _get_path(evidence_pack, "confidence_basis.confidence"),
    )


def _first_present(payload: Mapping[str, Any], keys: tuple[str, ...], *, fallback: Any = None) -> Any:
    for key in keys:
        if payload.get(key) is not None:
            return payload.get(key)
    return fallback


def _numeric_delta(left: Any, right: Any) -> Any:
    try:
        return float(left) - float(right)
    except (TypeError, ValueError):
        return None


def _confidence_delta(akshare_confidence: Any, tushare_confidence: Any) -> str | None:
    if akshare_confidence is None and tushare_confidence is None:
        return None
    if akshare_confidence == tushare_confidence:
        return "no_confidence_drift"
    return f"{akshare_confidence}_to_{tushare_confidence}"


def _score_drift_reason(
    *,
    akshare_score: Any,
    tushare_score: Any,
    drift_subcategory: str | None,
    diff_report: Mapping[str, Any] | None,
) -> str | None:
    if akshare_score == tushare_score and not _has_diff_category(diff_report, "score_drift"):
        return None
    return drift_subcategory or "scoring_explainability_gap"


def _confidence_drift_reason(
    *,
    akshare_confidence: Any,
    tushare_confidence: Any,
    drift_subcategory: str | None,
    diff_report: Mapping[str, Any] | None,
) -> str | None:
    if akshare_confidence == tushare_confidence and not _has_diff_category(diff_report, "confidence_drift"):
        return None
    return drift_subcategory or "scoring_explainability_gap"


def _missing_field_summary(
    *,
    akshare_raw: Mapping[str, Any],
    tushare_raw: Mapping[str, Any],
    akshare_fundamental: Mapping[str, Any],
    tushare_fundamental: Mapping[str, Any],
    akshare_evidence_pack: Mapping[str, Any],
    tushare_evidence_pack: Mapping[str, Any],
) -> dict[str, list[str]]:
    akshare_missing = _collect_missing_fields(akshare_raw, akshare_fundamental, akshare_evidence_pack)
    tushare_missing = _collect_missing_fields(tushare_raw, tushare_fundamental, tushare_evidence_pack)
    return {
        "akshare": sorted(akshare_missing),
        "tushare": sorted(tushare_missing),
        "tushare_only": sorted(tushare_missing - akshare_missing),
        "akshare_only": sorted(akshare_missing - tushare_missing),
    }


def _collect_missing_fields(*payloads: Mapping[str, Any]) -> set[str]:
    missing: set[str] = set()
    for payload in payloads:
        missing.update(_string_list(payload.get("missing_fields")))
        missing.update(_missing_from_rows(payload.get("missing_fields")))
        missing.update(_missing_from_rows(_get_path(payload, "confidence_basis.missing_fields")))
        fetch_status = payload.get("fetch_status")
        if isinstance(fetch_status, Mapping):
            for status in fetch_status.values():
                if isinstance(status, Mapping):
                    missing.update(_string_list(status.get("missing_fields")))
        stock_missing = _get_path(payload, "stock.missing_fields")
        missing.update(_string_list(stock_missing))
        missing.update(_missing_from_rows(stock_missing))
    return {item for item in missing if item}


def _missing_from_rows(rows: Any) -> set[str]:
    values: set[str] = set()
    if not isinstance(rows, list):
        return values
    for row in rows:
        if isinstance(row, Mapping):
            field = row.get("field") or row.get("field_name") or row.get("name")
            if field:
                values.add(str(field))
    return values


def _string_list(value: Any) -> set[str]:
    if isinstance(value, str):
        return {value}
    if isinstance(value, list):
        return {str(item) for item in value if isinstance(item, (str, int, float))}
    return set()


def _provider_caveats(
    *,
    code: str,
    akshare_raw: Mapping[str, Any],
    tushare_raw: Mapping[str, Any],
    akshare_fundamental: Mapping[str, Any],
    tushare_fundamental: Mapping[str, Any],
    akshare_evidence_pack: Mapping[str, Any],
    tushare_evidence_pack: Mapping[str, Any],
    missing: Mapping[str, list[str]],
) -> list[dict[str, Any]]:
    caveats: list[dict[str, Any]] = []
    normalized_code = _normalize_code(code)
    if _commodity_sidecar_missing(normalized_code, akshare_raw, tushare_raw, akshare_evidence_pack, tushare_evidence_pack, missing):
        caveats.append(
            {
                "code": "provider_coverage_caveat",
                "provider": "tushare",
                "field": "commodity_prices",
                "category": "external_sidecar_missing",
                "note": "Commodity prices are provider-independent sidecar evidence and are not part of generic Tushare fundamentals.",
            }
        )
    if _ai_datacenter_domain_missing(normalized_code, akshare_fundamental, tushare_fundamental, akshare_evidence_pack, tushare_evidence_pack, missing):
        caveats.append(
            {
                "code": "domain_evidence_missing",
                "provider": "tushare",
                "field": "ai_datacenter.domain_evidence",
                "category": "domain_evidence_missing",
                "note": "Liquid-cooling revenue share, orders, customer validation, and batch delivery are domain evidence outside generic Tushare fundamentals.",
            }
        )
    if _main_business_missing(tushare_raw, tushare_evidence_pack, missing):
        caveats.append(
            {
                "code": "mapping_gap",
                "provider": "tushare",
                "field": "basic_info.main_business",
                "category": "mapping_gap",
                "note": "A largest business segment may be shown as a derived hint but must not become canonical basic_info.main_business.",
            }
        )
    return caveats


def _commodity_sidecar_missing(
    code: str,
    akshare_raw: Mapping[str, Any],
    tushare_raw: Mapping[str, Any],
    akshare_evidence_pack: Mapping[str, Any],
    tushare_evidence_pack: Mapping[str, Any],
    missing: Mapping[str, list[str]],
) -> bool:
    if code != "000426":
        return False
    ak_has = _has_block_rows(akshare_raw, "commodity_prices") or bool(akshare_evidence_pack.get("commodity_prices"))
    ts_has = _has_block_rows(tushare_raw, "commodity_prices") or bool(tushare_evidence_pack.get("commodity_prices"))
    ts_missing = any("commodity_prices" in field for field in missing.get("tushare", []))
    return ak_has and (not ts_has or ts_missing)


def _ai_datacenter_domain_missing(
    code: str,
    akshare_fundamental: Mapping[str, Any],
    tushare_fundamental: Mapping[str, Any],
    akshare_evidence_pack: Mapping[str, Any],
    tushare_evidence_pack: Mapping[str, Any],
    missing: Mapping[str, list[str]],
) -> bool:
    strategy = str(
        tushare_fundamental.get("strategy_type")
        or _get_path(tushare_evidence_pack, "stock.strategy_type")
        or akshare_fundamental.get("strategy_type")
        or _get_path(akshare_evidence_pack, "stock.strategy_type")
        or ""
    )
    if code != "002837" and strategy != "ai_datacenter_infrastructure":
        return False
    text = " ".join(missing.get("tushare", []) + missing.get("tushare_only", [])).lower()
    if "ai_datacenter" in text or "liquid_cooling" in text or "customer_validation" in text or "batch" in text:
        return True
    return code == "002837"


def _main_business_missing(
    tushare_raw: Mapping[str, Any],
    tushare_evidence_pack: Mapping[str, Any],
    missing: Mapping[str, list[str]],
) -> bool:
    if _get_path(tushare_evidence_pack, "basic_info.main_business"):
        return False
    basic = _first_row(tushare_raw, "basic_info")
    if basic.get("main_business"):
        return False
    return "basic_info.main_business" in set(missing.get("tushare", []))


def _primary_drift_subcategory(
    *,
    code: str,
    missing: Mapping[str, list[str]],
    provider_caveats: list[Mapping[str, Any]],
    diff_report: Mapping[str, Any] | None,
) -> str | None:
    categories = {str(item.get("category")) for item in provider_caveats}
    if "external_sidecar_missing" in categories:
        return "external_sidecar_missing"
    if "domain_evidence_missing" in categories:
        return "domain_evidence_missing"
    if "mapping_gap" in categories:
        return "mapping_gap"
    if missing.get("tushare_only"):
        return "scoring_penalty_due_to_provider_gap"
    if _has_diff_category(diff_report, "unit_difference"):
        return "unit_diff"
    if _has_diff_category(diff_report, "missing_field_regression"):
        return "missing_field"
    del code
    return None


def _dimension_breakdown(
    *,
    akshare_fundamental: Mapping[str, Any],
    tushare_fundamental: Mapping[str, Any],
    missing: Mapping[str, list[str]],
    provider_caveats: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    ak_dimensions = _extract_dimension_scores(akshare_fundamental)
    ts_dimensions = _extract_dimension_scores(tushare_fundamental)
    dimension_names = sorted(set(ak_dimensions) | set(ts_dimensions))
    rows: list[dict[str, Any]] = []
    for dimension in dimension_names:
        ak_item = ak_dimensions.get(dimension, {})
        ts_item = ts_dimensions.get(dimension, {})
        ak_constrained = _score_value(ak_item, ("constrained_score", "score", "final_score"))
        ts_constrained = _score_value(ts_item, ("constrained_score", "score", "final_score"))
        rows.append(
            {
                "dimension": dimension,
                "akshare_raw_score": _score_value(ak_item, ("raw_score", "unconstrained_score")),
                "tushare_raw_score": _score_value(ts_item, ("raw_score", "unconstrained_score")),
                "akshare_constrained_score": ak_constrained,
                "tushare_constrained_score": ts_constrained,
                "weight": _score_value(ts_item, ("weight",)) if _score_value(ts_item, ("weight",)) is not None else _score_value(ak_item, ("weight",)),
                "delta": _numeric_delta(ts_constrained, ak_constrained),
                "key_input_fields": sorted(set(_string_list(ak_item.get("key_input_fields")) | _string_list(ts_item.get("key_input_fields")))),
                "missing_fields": missing.get("tushare_only", []),
                "readiness_penalties": sorted(set(_string_list(ak_item.get("readiness_penalties")) | _string_list(ts_item.get("readiness_penalties")))),
                "caps_or_constraints": sorted(set(_string_list(ak_item.get("caps_or_constraints")) | _string_list(ts_item.get("caps_or_constraints")))),
                "provider_caveats": sorted({str(item.get("category")) for item in provider_caveats if item.get("category")}),
                "drift_subcategory": _dimension_drift_subcategory(missing, provider_caveats),
            }
        )
    return rows


def _extract_dimension_scores(fundamental: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    for key in ("dimension_breakdown", "score_breakdown", "dimension_scores", "scoring_dimensions"):
        value = fundamental.get(key)
        extracted = _normalize_dimension_score_payload(value)
        if extracted:
            return extracted
    scoring = fundamental.get("scoring")
    if isinstance(scoring, Mapping):
        for key in ("dimension_breakdown", "score_breakdown", "dimension_scores", "scoring_dimensions"):
            extracted = _normalize_dimension_score_payload(scoring.get(key))
            if extracted:
                return extracted
    return {}


def _normalize_dimension_score_payload(value: Any) -> dict[str, Mapping[str, Any]]:
    if isinstance(value, Mapping):
        result: dict[str, Mapping[str, Any]] = {}
        for key, item in value.items():
            if isinstance(item, Mapping):
                result[str(key)] = item
            else:
                result[str(key)] = {"score": item}
        return result
    if isinstance(value, list):
        result = {}
        for item in value:
            if not isinstance(item, Mapping):
                continue
            dimension = item.get("dimension") or item.get("name") or item.get("scoring_dimension")
            if dimension:
                result[str(dimension)] = item
        return result
    return {}


def _score_value(payload: Mapping[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if payload.get(key) is not None:
            return payload.get(key)
    return None


def _dimension_drift_subcategory(missing: Mapping[str, list[str]], provider_caveats: list[Mapping[str, Any]]) -> str | None:
    categories = {str(item.get("category")) for item in provider_caveats}
    if "external_sidecar_missing" in categories:
        return "external_sidecar_missing"
    if "domain_evidence_missing" in categories:
        return "domain_evidence_missing"
    if missing.get("tushare_only"):
        return "scoring_penalty_due_to_provider_gap"
    return None


def _derived_hints(tushare_raw: Mapping[str, Any], tushare_evidence_pack: Mapping[str, Any]) -> list[dict[str, Any]]:
    segment = _largest_business_segment(tushare_evidence_pack.get("business_composition"))
    source = "tushare.evidence_pack.business_composition:selected_period"
    if segment is None:
        segment = _largest_business_segment(_get_path(tushare_raw, "blocks.business_composition"))
        source = "tushare.raw.business_composition:selected_period"
    if segment is None:
        return []
    return [
        {
            "field": "business_composition.max_segment",
            "value": segment,
            "source": source,
            "derived": True,
            "not_for_scoring": True,
            "reason": "Largest segment may help reviewers understand composition, but it must not become canonical basic_info.main_business.",
        }
    ]


def _largest_business_segment(rows: Any) -> str | None:
    if not isinstance(rows, list):
        return None
    candidates: list[tuple[float, str]] = []
    fallback: str | None = None
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        name = row.get("segment_name") or row.get("business_name") or row.get("name")
        if not name:
            continue
        fallback = fallback or str(name)
        metric = _first_number(row, ("revenue_ratio", "ratio", "revenue", "income"))
        if metric is not None:
            candidates.append((metric, str(name)))
    if candidates:
        return sorted(candidates, key=lambda item: item[0], reverse=True)[0][1]
    return fallback


def _first_number(payload: Mapping[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        try:
            value = payload.get(key)
            if value is None:
                continue
            return float(str(value).strip().replace("%", ""))
        except (TypeError, ValueError):
            continue
    return None


def _explainability_limitations(
    *,
    akshare_fundamental: Mapping[str, Any],
    tushare_fundamental: Mapping[str, Any],
) -> list[str]:
    if _extract_dimension_scores(akshare_fundamental) or _extract_dimension_scores(tushare_fundamental):
        return []
    return [
        "dimension_level_scores_unavailable: existing comparison artifacts do not expose dimension-level raw/constrained scores; explainability did not import scoring or recalculate scores."
    ]


def _has_diff_category(diff_report: Mapping[str, Any] | None, category: str) -> bool:
    if not diff_report:
        return False
    for item in diff_report.get("diff_items", []):
        if isinstance(item, Mapping) and item.get("category") == category:
            return True
    return False


def _has_block_rows(raw: Mapping[str, Any], block_name: str) -> bool:
    rows = _get_path(raw, f"blocks.{block_name}")
    return isinstance(rows, list) and bool(rows)


def _first_row(raw: Mapping[str, Any], block_name: str) -> Mapping[str, Any]:
    rows = _get_path(raw, f"blocks.{block_name}")
    if isinstance(rows, list) and rows and isinstance(rows[0], Mapping):
        return rows[0]
    return {}


def _get_path(payload: Mapping[str, Any], path: str) -> Any:
    current: Any = payload
    for part in path.split("."):
        if not isinstance(current, Mapping):
            return None
        current = current.get(part)
    return current


def _normalize_code(code: str) -> str:
    digits = "".join(ch for ch in str(code) if ch.isdigit())
    return digits[-6:] if len(digits) >= 6 else str(code)

