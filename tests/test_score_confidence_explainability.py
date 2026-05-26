# -*- coding: utf-8 -*-

import ast

from src.fundamental_skill.data_providers.score_confidence_explainability import (
    build_score_confidence_explainability,
)
from src.fundamental_skill.data_providers.token_leak_scanner import assert_no_token_leaks


def _raw(code="600406", *, provider="akshare", main_business="core business", commodities=None, business=None, missing=None):
    blocks = {
        "basic_info": [
            {
                "stock_code": code,
                "stock_name": "Sample",
                "main_business": main_business,
            }
        ],
        "financial_indicator": [{"revenue": 100.0}],
        "valuation": [{"market_cap": 1000.0}],
        "business_composition": business or [],
        "news": [],
    }
    if commodities is not None:
        blocks["commodity_prices"] = commodities
    return {
        "meta": {"code": code, "data_source": provider},
        "blocks": blocks,
        "fetch_status": {
            "basic_info": {"success": True, "missing_fields": ["basic_info.main_business"] if main_business is None else []},
            "business_composition": {"success": True, "missing_fields": missing or []},
            "commodity_prices": {"success": commodities is not None, "missing_fields": [] if commodities else ["external.commodity_prices"]},
        },
        "errors": [],
    }


def _fundamental(code="600406", *, strategy_type="stable_growth", score=70, confidence="medium", missing=None, dimensions=None):
    payload = {
        "stock_code": code,
        "stock_name": "Sample",
        "strategy_type": strategy_type,
        "sub_type": None,
        "status": "watch",
        "confidence": confidence,
        "fundamental_score": score,
        "missing_fields": missing or [],
    }
    if dimensions is not None:
        payload["dimension_scores"] = dimensions
    return payload


def _pack(code="600406", *, strategy_type="stable_growth", score=70, confidence="medium", missing=None, commodities=None, business=None, main_business="core business"):
    missing_rows = [{"field": field, "explanation": "missing"} for field in (missing or [])]
    return {
        "stock": {
            "code": code,
            "strategy_type": strategy_type,
            "confidence": confidence,
            "fundamental_score": score,
        },
        "basic_info": {"main_business": main_business},
        "business_composition": business or [],
        "commodity_prices": commodities or [],
        "confidence_basis": {
            "confidence": confidence,
            "score": score,
            "missing_fields": missing_rows,
        },
        "missing_fields": missing_rows,
    }


def test_explainability_module_has_no_forbidden_import_boundaries():
    source = open(
        "src/fundamental_skill/data_providers/score_confidence_explainability.py",
        encoding="utf-8",
    ).read()
    tree = ast.parse(source)
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")

    forbidden = [
        "scoring_engine",
        "data_readiness_planner",
        "readiness_schema",
        "stock_classifier",
        "research_intelligence_p1_builder",
        "research_intelligence_p1_schema",
        "html_report",
        "dashboard",
    ]
    for module_name in imported:
        assert not any(term in module_name for term in forbidden)


def test_schema_flags_and_score_confidence_summary_are_diagnostic_only():
    payload = build_score_confidence_explainability(
        code="600406",
        akshare_raw=_raw(),
        tushare_raw=_raw(provider="tushare"),
        akshare_fundamental=_fundamental(score=80, confidence="high"),
        tushare_fundamental=_fundamental(score=70, confidence="medium"),
        akshare_evidence_pack=_pack(score=80, confidence="high"),
        tushare_evidence_pack=_pack(score=70, confidence="medium"),
        diff_report={"diff_items": [{"category": "score_drift"}, {"category": "confidence_drift"}]},
    )

    assert payload["automatic_acceptance"] is False
    assert payload["explainability_only"] is True
    assert payload["score_summary"]["akshare_score"] == 80
    assert payload["score_summary"]["tushare_score"] == 70
    assert payload["score_summary"]["score_delta"] == -10.0
    assert payload["confidence_summary"]["confidence_delta"] == "high_to_medium"
    assert payload["providers"]["akshare"]["artifact_refs"]["raw"] == "akshare_raw.json"
    assert_no_token_leaks(payload, context="score_confidence_explainability")


def test_dimension_breakdown_uses_existing_dimension_scores_only():
    payload = build_score_confidence_explainability(
        code="600406",
        akshare_raw=_raw(),
        tushare_raw=_raw(provider="tushare"),
        akshare_fundamental=_fundamental(
            dimensions={
                "financial_quality": {
                    "raw_score": 80,
                    "constrained_score": 75,
                    "weight": 0.3,
                    "key_input_fields": ["financial_metrics.roe"],
                }
            }
        ),
        tushare_fundamental=_fundamental(
            score=65,
            missing=["financial_metrics.roe"],
            dimensions={
                "financial_quality": {
                    "raw_score": 60,
                    "constrained_score": 60,
                    "weight": 0.3,
                    "key_input_fields": ["financial_metrics.roe"],
                    "caps_or_constraints": ["readiness_cap"],
                }
            },
        ),
        akshare_evidence_pack=_pack(),
        tushare_evidence_pack=_pack(score=65, missing=["financial_metrics.roe"]),
    )

    row = payload["dimension_breakdown"][0]
    assert row["dimension"] == "financial_quality"
    assert row["akshare_raw_score"] == 80
    assert row["tushare_raw_score"] == 60
    assert row["delta"] == -15.0
    assert row["missing_fields"] == ["financial_metrics.roe"]


def test_missing_dimension_scores_emit_limitation_without_fake_breakdown():
    payload = build_score_confidence_explainability(
        code="600406",
        akshare_raw=_raw(),
        tushare_raw=_raw(provider="tushare"),
        akshare_fundamental=_fundamental(),
        tushare_fundamental=_fundamental(score=65),
        akshare_evidence_pack=_pack(),
        tushare_evidence_pack=_pack(score=65),
    )

    assert payload["dimension_breakdown"] == []
    assert any("dimension_level_scores_unavailable" in item for item in payload["explainability_limitations"])


def test_000426_external_sidecar_missing_is_marked_without_merging():
    commodity_rows = [{"commodity_name": "silver", "price": 1.0, "readiness_eligible": True}]
    payload = build_score_confidence_explainability(
        code="000426",
        akshare_raw=_raw(code="000426", commodities=commodity_rows),
        tushare_raw=_raw(code="000426", provider="tushare", commodities=None),
        akshare_fundamental=_fundamental(code="000426", strategy_type="resource_swing", score=75, confidence="medium"),
        tushare_fundamental=_fundamental(
            code="000426",
            strategy_type="resource_swing",
            score=65,
            confidence="low",
            missing=["external.commodity_prices"],
        ),
        akshare_evidence_pack=_pack(code="000426", strategy_type="resource_swing", score=75, confidence="medium", commodities=commodity_rows),
        tushare_evidence_pack=_pack(
            code="000426",
            strategy_type="resource_swing",
            score=65,
            confidence="low",
            missing=["external.commodity_prices"],
            commodities=[],
        ),
    )

    assert payload["score_summary"]["score_drift_reason"] == "external_sidecar_missing"
    assert payload["confidence_summary"]["confidence_drift_reason"] == "external_sidecar_missing"
    assert any(item["category"] == "external_sidecar_missing" for item in payload["provider_caveats"])


def test_002837_ai_datacenter_domain_evidence_missing_is_marked():
    missing = [
        "ai_datacenter.liquid_cooling_revenue_share",
        "ai_datacenter.liquid_cooling_customer_validation",
        "ai_datacenter.liquid_cooling_batch_orders",
    ]
    payload = build_score_confidence_explainability(
        code="002837",
        akshare_raw=_raw(code="002837"),
        tushare_raw=_raw(code="002837", provider="tushare", missing=missing),
        akshare_fundamental=_fundamental(code="002837", strategy_type="ai_datacenter_infrastructure", score=72, confidence="medium"),
        tushare_fundamental=_fundamental(
            code="002837",
            strategy_type="ai_datacenter_infrastructure",
            score=60,
            confidence="low",
            missing=missing,
        ),
        akshare_evidence_pack=_pack(code="002837", strategy_type="ai_datacenter_infrastructure", score=72, confidence="medium"),
        tushare_evidence_pack=_pack(
            code="002837",
            strategy_type="ai_datacenter_infrastructure",
            score=60,
            confidence="low",
            missing=missing,
        ),
    )

    assert payload["score_summary"]["score_drift_reason"] == "domain_evidence_missing"
    assert payload["confidence_summary"]["confidence_drift_reason"] == "domain_evidence_missing"
    assert any(item["category"] == "domain_evidence_missing" for item in payload["provider_caveats"])
    assert "ai_datacenter_cooling" in payload["domain_evidence_policy"]


def test_main_business_gap_uses_derived_hint_not_canonical_writeback():
    business_rows = [
        {"segment_name": "small segment", "revenue": 10.0},
        {"segment_name": "largest segment", "revenue": 100.0},
    ]
    payload = build_score_confidence_explainability(
        code="002050",
        akshare_raw=_raw(code="002050"),
        tushare_raw=_raw(code="002050", provider="tushare", main_business=None, business=business_rows),
        akshare_fundamental=_fundamental(code="002050", strategy_type="advanced_manufacturing_growth", score=75, confidence="medium"),
        tushare_fundamental=_fundamental(
            code="002050",
            strategy_type="advanced_manufacturing_growth",
            score=70,
            confidence="medium",
            missing=["basic_info.main_business"],
        ),
        akshare_evidence_pack=_pack(code="002050", strategy_type="advanced_manufacturing_growth"),
        tushare_evidence_pack=_pack(
            code="002050",
            strategy_type="advanced_manufacturing_growth",
            score=70,
            missing=["basic_info.main_business"],
            business=business_rows,
            main_business=None,
        ),
    )

    hint = payload["derived_hints"][0]
    assert hint["field"] == "business_composition.max_segment"
    assert hint["value"] == "largest segment"
    assert hint["derived"] is True
    assert hint["not_for_scoring"] is True
    assert any(item["field"] == "basic_info.main_business" for item in payload["provider_caveats"])
