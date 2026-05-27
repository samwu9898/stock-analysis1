# -*- coding: utf-8 -*-

import copy
import inspect
import json
from pathlib import Path

import pytest

from src.fundamental_skill.ground_truth.auto_fact_candidate_generator import (
    FactCandidateArtifactBoundaryError,
    FactCandidateSecretError,
)
from src.fundamental_skill.ground_truth.candidate_review_decisions import (
    FOLLOW_UP_TYPES,
    OUTCOMES,
    REQUIRED_DECISION_KEYS,
    build_candidate_review_decisions,
    write_candidate_review_decisions,
)
import src.fundamental_skill.ground_truth.candidate_review_decisions as decisions_module


GROUND_TRUTH_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "ground_truth"
    / "fundamental_ground_truth_v1.json"
)

FORBIDDEN_ADVICE_FIELDS = {
    "buy",
    "sell",
    "target_price",
    "position",
    "stop_loss",
    "take_profit",
    "portfolio_weight",
    "portfolio_weight_pct",
    "portfolio_weight_percent",
    "trading_recommendation",
    "investment_recommendation",
}


def _candidate(
    field_path: str,
    *,
    provider: str = "tushare",
    value=1.0,
    report_period: str | None = None,
    as_of_date: str | None = None,
    canonical_unit: str = "RMB yuan",
    review_status: str = "manual_review_required",
    missing_category: str | None = "manual_review_required",
    conflict_status: str = "within_tolerance",
    source_endpoint: str = "test_endpoint",
):
    return {
        "field_path": field_path,
        "value": value,
        "source_provider": provider,
        "source_artifact": f"{provider}_fundamental.json",
        "source_block": field_path.split(".")[0],
        "source_endpoint": source_endpoint,
        "source_trace": {
            "artifact_file": f"{provider}_fundamental.json",
            "provider": provider,
            "field_name": field_path.split(".")[-1],
            "endpoint": source_endpoint,
            "json_pointer": f"/blocks/{field_path.replace('.', '/')}",
            "row_selector": {
                "report_period": report_period,
                "as_of_date": as_of_date,
                "classification_type": "by_product" if field_path.startswith("business_composition") else None,
                "segment_name": "Grid automation" if field_path.startswith("business_composition") else None,
            },
        },
        "report_period": report_period,
        "ann_date": None,
        "disclosure_date": None,
        "as_of_date": as_of_date,
        "data_unit": canonical_unit,
        "canonical_unit": canonical_unit,
        "derived": False,
        "derivation_method": None,
        "confidence": "high" if review_status == "auto_accepted" else "low",
        "review_status": review_status,
        "missing_category": missing_category,
        "conflict_status": conflict_status,
        "manual_review_note": "",
    }


def _representative(candidate: dict) -> dict:
    return {
        "field_path": candidate["field_path"],
        "source_provider": candidate["source_provider"],
        "value": candidate["value"],
        "report_period": candidate["report_period"],
        "as_of_date": candidate["as_of_date"],
        "canonical_unit": candidate["canonical_unit"],
        "confidence": candidate["confidence"],
        "review_status": candidate["review_status"],
        "missing_category": candidate["missing_category"],
        "conflict_status": candidate["conflict_status"],
        "source_endpoint": candidate["source_endpoint"],
    }


def _queue_item(priority: int, field_path: str, issue_type: str, candidates: list[dict]) -> dict:
    return {
        "priority": priority,
        "field_path": field_path,
        "issue_type": issue_type,
        "source_provider": "mixed",
        "candidate_count": len(candidates),
        "representative_candidates": [_representative(candidate) for candidate in candidates[:3]],
        "reason": "fake review queue reason",
        "suggested_next_action": "fake review queue next action",
    }


def _fake_candidate_report() -> dict:
    valuation_candidates = [
        _candidate(
            "valuation_metrics.pe_ttm",
            value=20.0,
            as_of_date="2026-05-26",
            canonical_unit="multiple",
            review_status="auto_accepted",
            missing_category=None,
        ),
        _candidate(
            "valuation_metrics.pb",
            value=3.0,
            as_of_date="2026-05-26",
            canonical_unit="multiple",
            review_status="auto_accepted",
            missing_category=None,
        ),
        _candidate(
            "valuation_metrics.market_cap",
            value=100_000_000.0,
            as_of_date="2026-05-26",
            canonical_unit="RMB yuan",
            review_status="auto_accepted",
            missing_category=None,
        ),
    ]
    business_period = _candidate(
        "business_composition[0].period",
        value="2025-12-31",
        report_period="2025-12-31",
        canonical_unit="report_period",
        review_status="manual_review_required",
    )
    classification = _candidate(
        "business_composition[0].classification_type",
        value=None,
        report_period="2025-12-31",
        canonical_unit="text",
        review_status="mapping_missing",
        missing_category="mapping_missing",
    )
    revenue_ratio = _candidate(
        "business_composition[0].revenue_ratio",
        value=60.0,
        report_period="2025-12-31",
        canonical_unit="percentage_point",
        review_status="manual_review_required",
    )
    gross_margin = _candidate(
        "business_composition[0].gross_margin",
        value=25.0,
        report_period="2025-12-31",
        canonical_unit="percentage_point",
        review_status="manual_review_required",
    )
    main_business = _candidate(
        "basic_info.main_business",
        value="Provider narrative text.",
        canonical_unit="text",
        review_status="manual_review_required",
    )
    mapping_missing = _candidate(
        "financial_metrics.capex",
        value=None,
        report_period="2025-12-31",
        canonical_unit="RMB yuan",
        review_status="mapping_missing",
        missing_category="mapping_missing",
    )
    provider_missing = _candidate(
        "financial_metrics.inventory",
        value=1_000_000.0,
        report_period="2025-12-31",
        canonical_unit="RMB yuan",
        review_status="manual_review_required",
        conflict_status="provider_missing",
    )
    not_available = _candidate(
        "financial_metrics.accounts_receivable",
        value=None,
        report_period="2025-12-31",
        canonical_unit="RMB yuan",
        review_status="not_available",
        missing_category="not_available",
    )
    candidates = [
        *valuation_candidates,
        business_period,
        classification,
        revenue_ratio,
        gross_margin,
        main_business,
        mapping_missing,
        provider_missing,
        not_available,
    ]
    return {
        "code": "600406",
        "generated_at": "2026-05-27T12:00:00+00:00",
        "mode": "offline_artifact_candidate_generation",
        "source_artifacts": {
            "tushare_fundamental": "tushare_fundamental.json",
            "akshare_fundamental": "akshare_fundamental.json",
        },
        "candidates": candidates,
        "manual_review_priority_queue": [
            _queue_item(1, "valuation_metrics.as_of_date", "valuation_as_of_date_review_required", valuation_candidates),
            _queue_item(2, "business_composition.period", "business_composition_period_review_required", [business_period]),
            _queue_item(2, "business_composition.classification_type", "business_composition_field_review", [classification]),
            _queue_item(2, "business_composition.revenue_ratio", "business_composition_field_review", [revenue_ratio]),
            _queue_item(2, "business_composition.gross_margin", "business_composition_field_review", [gross_margin]),
            _queue_item(2, "basic_info.main_business", "main_business_review", [main_business]),
            _queue_item(2, "financial_metrics.*", "block_mapping_missing", [mapping_missing]),
            _queue_item(2, "financial_metrics.*", "block_provider_missing", [provider_missing]),
            _queue_item(3, "financial_metrics.accounts_receivable", "not_available", [not_available]),
        ],
    }


def _decision(payload: dict, field_path: str, queue_item_type: str) -> dict:
    matches = [
        decision
        for decision in payload["decisions"]
        if decision["field_path"] == field_path and decision["queue_item_type"] == queue_item_type
    ]
    assert len(matches) == 1, f"expected one decision for {field_path}:{queue_item_type}, got {len(matches)}"
    return matches[0]


def _walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _assert_secret_not_rendered(secret: str, text: str) -> None:
    if secret in text:
        raise AssertionError("secret-like value was rendered")


def test_builds_candidate_review_decisions_artifact_from_fake_candidate_report():
    candidate_report = _fake_candidate_report()
    before = copy.deepcopy(candidate_report)

    payload = build_candidate_review_decisions(
        candidate_report,
        reviewed_by="unit_test_reviewer",
        reviewed_at="2026-05-27T12:30:00+00:00",
    )

    assert candidate_report == before
    assert payload["version"] == "candidate_review_decisions.v1"
    assert payload["code"] == "600406"
    assert payload["created_at"] == "2026-05-27T12:30:00+00:00"
    assert payload["source_candidate_report"] == "fact_candidates.json"
    assert payload["review_mode"] == "protocol_guided_review"
    assert payload["decisions"]
    assert payload["summary"]["total_decisions"] == len(payload["decisions"])


def test_each_decision_has_required_schema_and_v1_fixture_boundary():
    payload = build_candidate_review_decisions(_fake_candidate_report(), reviewed_at="2026-05-27T12:30:00+00:00")

    assert all(REQUIRED_DECISION_KEYS <= set(decision) for decision in payload["decisions"])
    assert all(decision["fixture_write_allowed"] is False for decision in payload["decisions"])
    assert all(decision["not_for_trading_advice"] is True for decision in payload["decisions"])
    assert all(decision["decision_outcome"] in OUTCOMES for decision in payload["decisions"])
    assert all(decision["follow_up_type"] in FOLLOW_UP_TYPES for decision in payload["decisions"])
    assert all("representative_candidates" in decision for decision in payload["decisions"])


def test_valuation_as_of_date_decision_can_confirm_future_eligibility_without_fixture_write():
    payload = build_candidate_review_decisions(_fake_candidate_report(), reviewed_at="2026-05-27T12:30:00+00:00")

    decision = _decision(payload, "valuation_metrics.as_of_date", "valuation_as_of_date_review_required")

    assert decision["review_action"] == "check_same_valuation_date_metadata"
    assert {"as_of_date", "source_provider", "source_endpoint", "source_trace", "canonical_unit"} <= set(
        decision["metadata_checked"]
    )
    assert decision["decision_outcome"] == "confirmed_for_future_promotion"
    assert decision["eligible_for_future_promotion"] is True
    assert decision["fixture_write_allowed"] is False
    assert decision["follow_up_type"] == "none"


def test_business_composition_period_decision_keeps_rows_out_of_promotion():
    payload = build_candidate_review_decisions(_fake_candidate_report(), reviewed_at="2026-05-27T12:30:00+00:00")

    decision = _decision(
        payload,
        "business_composition.period",
        "business_composition_period_review_required",
    )

    assert decision["review_action"] == "check_selected_period_and_row_grouping"
    assert {"report_period", "source_period", "classification_type", "segment_name", "source_endpoint"} <= set(
        decision["metadata_checked"]
    )
    assert decision["decision_outcome"] in {"keep_manual_review_required", "requires_provider_mapping_patch"}
    assert decision["eligible_for_future_promotion"] is False
    assert "Keep composition rows out of promotion" in decision["follow_up_detail"]


def test_business_composition_field_decisions_cover_type_ratio_and_margin():
    payload = build_candidate_review_decisions(_fake_candidate_report(), reviewed_at="2026-05-27T12:30:00+00:00")

    classification = _decision(payload, "business_composition.classification_type", "classification_type_missing")
    revenue_ratio = _decision(payload, "business_composition.revenue_ratio", "ratio_denominator_unclear")
    gross_margin = _decision(payload, "business_composition.gross_margin", "ratio_denominator_unclear")

    assert classification["review_action"] == "check_composition_classification_type"
    assert classification["decision_outcome"] == "requires_provider_mapping_patch"
    assert classification["follow_up_type"] == "provider_mapping_patch"
    assert revenue_ratio["review_action"] == "check_ratio_denominator_scope"
    assert revenue_ratio["decision_outcome"] == "keep_manual_review_required"
    assert "denominator" in " ".join(revenue_ratio["metadata_checked"])
    assert gross_margin["review_action"] == "check_margin_source_or_derivation"
    assert gross_margin["decision_outcome"] == "keep_manual_review_required"
    assert {"derived", "profit", "revenue", "classification_type"} <= set(gross_margin["metadata_checked"])


def test_main_business_decision_requires_official_parser_and_no_max_segment_derivation():
    payload = build_candidate_review_decisions(_fake_candidate_report(), reviewed_at="2026-05-27T12:30:00+00:00")

    decision = _decision(payload, "basic_info.main_business", "main_business_review_required")

    assert decision["review_action"] == "check_official_business_text_source"
    assert decision["decision_outcome"] == "requires_official_parser"
    assert decision["follow_up_type"] == "official_parser_needed"
    assert "must not be derived from the largest segment" in decision["decision_reason"]
    assert decision["eligible_for_future_promotion"] is False


def test_block_level_mapping_provider_and_not_available_decisions():
    payload = build_candidate_review_decisions(_fake_candidate_report(), reviewed_at="2026-05-27T12:30:00+00:00")

    mapping_missing = _decision(payload, "financial_metrics.*", "mapping_missing")
    provider_missing = _decision(payload, "financial_metrics.*", "provider_missing")
    not_available = _decision(payload, "financial_metrics.accounts_receivable", "not_available")

    assert mapping_missing["decision_outcome"] == "requires_provider_mapping_patch"
    assert mapping_missing["follow_up_type"] == "provider_mapping_patch"
    assert provider_missing["decision_outcome"] == "coverage_caveat"
    assert provider_missing["follow_up_type"] == "coverage_caveat"
    assert not_available["decision_outcome"] == "defer_until_live_provider"
    assert not_available["follow_up_type"] == "live_provider_needed"


def test_summary_counts_and_fixture_write_count_stay_conservative():
    payload = build_candidate_review_decisions(_fake_candidate_report(), reviewed_at="2026-05-27T12:30:00+00:00")
    summary = payload["summary"]

    assert summary["total_decisions"] == 9
    assert summary["confirmed_for_future_promotion_count"] == 1
    assert summary["keep_manual_review_required_count"] >= 3
    assert summary["requires_provider_mapping_patch_count"] >= 2
    assert summary["requires_official_parser_count"] == 1
    assert summary["coverage_caveat_count"] == 1
    assert summary["defer_until_live_provider_count"] == 1
    assert summary["defer_until_sidecar_count"] == 0
    assert summary["rejected_count"] == 0
    assert summary["fixture_write_allowed_count"] == 0
    assert summary["eligible_for_future_promotion_count"] == 1
    assert summary["next_recommended_stage"] == "review_decisions_artifact_acceptance"


def test_payload_contains_no_investment_advice_fields():
    payload = build_candidate_review_decisions(_fake_candidate_report(), reviewed_at="2026-05-27T12:30:00+00:00")
    keys = {str(key).lower() for key in _walk_keys(payload)}

    assert not (FORBIDDEN_ADVICE_FIELDS & keys)
    assert all("target_price" not in decision for decision in payload["decisions"])
    assert all("portfolio_weight" not in decision for decision in payload["decisions"])


def test_does_not_write_ground_truth_fixture(tmp_path):
    before = GROUND_TRUTH_FIXTURE.read_text(encoding="utf-8")

    payload = build_candidate_review_decisions(_fake_candidate_report(), reviewed_at="2026-05-27T12:30:00+00:00")
    write_candidate_review_decisions(payload, tmp_path / "ground_truth_candidate_reviews", "20260527T123000")

    assert GROUND_TRUTH_FIXTURE.read_text(encoding="utf-8") == before


def test_writer_writes_only_candidate_review_decisions_json_under_tmpdir(tmp_path):
    payload = build_candidate_review_decisions(_fake_candidate_report(), reviewed_at="2026-05-27T12:30:00+00:00")
    output_root = tmp_path / "ground_truth_candidate_reviews"

    path = write_candidate_review_decisions(payload, output_root, "20260527T123000")

    assert path == output_root / "20260527T123000" / "600406" / "candidate_review_decisions.json"
    assert json.loads(path.read_text(encoding="utf-8"))["version"] == "candidate_review_decisions.v1"
    assert [item for item in output_root.rglob("*") if item.is_file()] == [path]


def test_writer_rejects_path_traversal(tmp_path):
    payload = build_candidate_review_decisions(_fake_candidate_report(), reviewed_at="2026-05-27T12:30:00+00:00")

    with pytest.raises(FactCandidateArtifactBoundaryError):
        write_candidate_review_decisions(payload, tmp_path / "ground_truth_candidate_reviews", "..\\escape")

    bad_payload = copy.deepcopy(payload)
    bad_payload["code"] = "..\\escape"
    with pytest.raises(FactCandidateArtifactBoundaryError):
        write_candidate_review_decisions(bad_payload, tmp_path / "ground_truth_candidate_reviews", "20260527T123000")


def test_writer_secret_scan_blocks_bearer_and_mcp_url(tmp_path):
    payload = build_candidate_review_decisions(_fake_candidate_report(), reviewed_at="2026-05-27T12:30:00+00:00")
    bad_payload = copy.deepcopy(payload)
    bad_payload["decisions"][0]["follow_up_detail"] = "Bearer A9abcdefABCDEF1234567890abcdefABCDEF1234567890z"

    with pytest.raises(FactCandidateSecretError):
        write_candidate_review_decisions(bad_payload, tmp_path / "ground_truth_candidate_reviews", "20260527T123000")

    mcp_payload = copy.deepcopy(payload)
    mcp_payload["decisions"][0]["follow_up_detail"] = "mcp://local-secret-endpoint"
    with pytest.raises(FactCandidateSecretError):
        write_candidate_review_decisions(mcp_payload, tmp_path / "ground_truth_candidate_reviews", "20260527T123000")


def test_writer_secret_scan_blocks_dotenv_paths_without_leaking_value(tmp_path):
    payload = build_candidate_review_decisions(_fake_candidate_report(), reviewed_at="2026-05-27T12:30:00+00:00")
    secret_paths = [
        ".env",
        ".env.local",
        ".env.production",
        "path/to/.env",
        "path/to/.env.local",
        "C:\\Users\\Example\\project\\.env",
        "/Users/example/project/.env",
        "/home/example/project/.env",
    ]

    for secret_path in secret_paths:
        bad_payload = copy.deepcopy(payload)
        bad_payload["decisions"][0]["follow_up_detail"] = f"load local configuration from {secret_path}"

        with pytest.raises(FactCandidateSecretError) as exc_info:
            write_candidate_review_decisions(
                bad_payload,
                tmp_path / "ground_truth_candidate_reviews",
                "20260527T123000",
            )

        message = str(exc_info.value)
        assert "<masked>" in message
        _assert_secret_not_rendered(secret_path, message)


def test_builder_secret_scan_blocks_dotenv_dict_keys_without_leaking_key():
    secret_keys = [".env", "path/to/.env.local"]

    for secret_key in secret_keys:
        candidate_report = _fake_candidate_report()
        candidate_report["manual_review_priority_queue"][0]["representative_candidates"][0][secret_key] = "value"

        with pytest.raises(FactCandidateSecretError) as exc_info:
            build_candidate_review_decisions(candidate_report, reviewed_at="2026-05-27T12:30:00+00:00")

        message = str(exc_info.value)
        assert "<masked>" in message
        assert "<masked_key>" in message
        _assert_secret_not_rendered(secret_key, message)


def test_writer_secret_scan_still_blocks_local_secret_path_without_leaking_value(tmp_path):
    secret_path = "C:\\Users\\Example\\secrets\\credential.txt"
    payload = build_candidate_review_decisions(_fake_candidate_report(), reviewed_at="2026-05-27T12:30:00+00:00")
    bad_payload = copy.deepcopy(payload)
    bad_payload["decisions"][0]["follow_up_detail"] = f"review note references {secret_path}"

    with pytest.raises(FactCandidateSecretError) as exc_info:
        write_candidate_review_decisions(bad_payload, tmp_path / "ground_truth_candidate_reviews", "20260527T123000")

    message = str(exc_info.value)
    assert "<masked>" in message
    _assert_secret_not_rendered(secret_path, message)


def test_writer_secret_scan_masks_token_like_dict_key_in_exception_location(tmp_path):
    secret = "A9abcdefABCDEF1234567890abcdefABCDEF1234567890z"
    payload = build_candidate_review_decisions(_fake_candidate_report(), reviewed_at="2026-05-27T12:30:00+00:00")
    bad_payload = copy.deepcopy(payload)
    bad_payload["decisions"][0]["representative_candidates"][0][secret] = "value"

    with pytest.raises(FactCandidateSecretError) as exc_info:
        write_candidate_review_decisions(bad_payload, tmp_path / "ground_truth_candidate_reviews", "20260527T123000")

    message = str(exc_info.value)
    assert "<masked>" in message
    assert "<masked_key>" in message
    _assert_secret_not_rendered(secret, message)


def test_builder_rejects_token_like_input_without_leaking_secret():
    secret = "A9abcdefABCDEF1234567890abcdefABCDEF1234567890z"
    candidate_report = _fake_candidate_report()
    candidate_report["manual_review_priority_queue"][0]["representative_candidates"][0][secret] = "value"

    with pytest.raises(FactCandidateSecretError) as exc_info:
        build_candidate_review_decisions(candidate_report, reviewed_at="2026-05-27T12:30:00+00:00")

    message = str(exc_info.value)
    assert "<masked>" in message
    assert "<masked_key>" in message
    _assert_secret_not_rendered(secret, message)


def test_module_does_not_import_provider_runtime_read_env_network_or_mcp():
    source = inspect.getsource(decisions_module)

    assert "data_providers" not in source
    assert "tushare_provider" not in source
    assert "akshare_provider" not in source
    assert "provider_router" not in source
    assert "import os" not in source
    assert "os.environ" not in source
    assert "getenv" not in source
    assert "requests" not in source
    assert "socket" not in source
    assert "urllib" not in source
    assert "list_mcp" not in source
    assert "mcp__" not in source
    assert "validator" not in source
