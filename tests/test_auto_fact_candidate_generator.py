# -*- coding: utf-8 -*-

import copy
import inspect
import json
from pathlib import Path

import pytest

from src.fundamental_skill.ground_truth.auto_fact_candidate_generator import (
    FactCandidateArtifactBoundaryError,
    FactCandidateSecretError,
    build_fact_candidates_from_comparison_dir,
    write_fact_candidate_report,
)
import src.fundamental_skill.ground_truth.auto_fact_candidate_generator as generator_module


REQUIRED_CANDIDATE_KEYS = {
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
}
V11_SUMMARY_KEYS = {
    "field_group_summary",
    "auto_accepted_core_fields",
    "manual_review_priority_queue",
    "business_composition_summary",
    "provider_quality_summary",
    "candidate_report_limitations",
}

GROUND_TRUTH_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "ground_truth"
    / "fundamental_ground_truth_v1.json"
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _trace(field_name: str, endpoint: str, period: str | None, value):
    return {
        "field_name": field_name,
        "function_name": endpoint,
        "source_function": endpoint,
        "source_period": period,
        "value": value,
        "derived": False,
        "derivation_method": None,
    }


def _provider_payload(provider: str, *, revenue=100_000_000.0, valuation_date="2026-05-26") -> dict:
    financial_period = "2025-12-31"
    return {
        "schema_version": "test.fundamental_artifact.v1",
        "provider": provider,
        "blocks": {
            "basic_info": [
                {
                    "stock_code": "600406",
                    "stock_name": "NARI",
                    "industry": "Electrical Equipment",
                    "listing_date": "20031016",
                    "main_business": "Long narrative business description from provider output.",
                    "field_source_trace": {
                        "stock_code": _trace("stock_code", "stock_basic", None, "600406"),
                        "stock_name": _trace("stock_name", "stock_basic", None, "NARI"),
                        "industry": _trace("industry", "stock_basic", None, "Electrical Equipment"),
                        "listing_date": _trace("listing_date", "stock_basic", None, "20031016"),
                        "main_business": _trace(
                            "main_business",
                            "company_profile",
                            None,
                            "Long narrative business description from provider output.",
                        ),
                    },
                }
            ],
            "financial_metrics": [
                {
                    "period": financial_period,
                    "revenue": revenue,
                    "net_profit": 10_000_000.0,
                    "gross_margin": 30.0,
                    "roe": 12.0,
                    "operating_cashflow": 12_000_000.0,
                    "accounts_receivable": 2_000_000.0,
                    "inventory": 3_000_000.0,
                    "contract_liabilities": 4_000_000.0,
                    "capex": 5_000_000.0,
                    "field_source_trace": {
                        "period": _trace("period", "income", financial_period, financial_period),
                        "revenue": _trace("revenue", "income", financial_period, revenue),
                        "net_profit": _trace("net_profit", "income", financial_period, 10_000_000.0),
                        "gross_margin": _trace("gross_margin", "fina_indicator", financial_period, 30.0),
                        "roe": _trace("roe", "fina_indicator", financial_period, 12.0),
                        "operating_cashflow": _trace(
                            "operating_cashflow",
                            "cashflow",
                            financial_period,
                            12_000_000.0,
                        ),
                        "accounts_receivable": _trace(
                            "accounts_receivable",
                            "balancesheet",
                            financial_period,
                            2_000_000.0,
                        ),
                        "inventory": _trace("inventory", "balancesheet", financial_period, 3_000_000.0),
                        "contract_liabilities": _trace(
                            "contract_liabilities",
                            "balancesheet",
                            financial_period,
                            4_000_000.0,
                        ),
                        "capex": _trace("capex", "cashflow", financial_period, 5_000_000.0),
                    },
                }
            ],
            "valuation_metrics": [
                {
                    "as_of_date": valuation_date,
                    "pe_ttm": 20.0,
                    "pb": 3.0,
                    "market_cap": 1_000_000_000.0,
                    "field_source_trace": {
                        "pe_ttm": _trace("pe_ttm", "daily_basic", valuation_date, 20.0),
                        "pb": _trace("pb", "daily_basic", valuation_date, 3.0),
                        "market_cap": _trace("market_cap", "daily_basic", valuation_date, 1_000_000_000.0),
                    },
                }
            ],
            "business_composition": [
                {
                    "period": financial_period,
                    "classification_type": "by_product",
                    "segment_name": "Grid automation",
                    "revenue": 60_000_000.0,
                    "revenue_ratio": 60.0,
                    "gross_margin": 25.0,
                    "field_source_trace": {
                        "revenue": _trace("revenue", "fina_mainbz", financial_period, 60_000_000.0),
                        "revenue_ratio": _trace("revenue_ratio", "fina_mainbz", financial_period, 60.0),
                        "gross_margin": _trace("gross_margin", "fina_mainbz", financial_period, 25.0),
                    },
                }
            ],
        },
    }


def _comparison_dir(tmp_path: Path, *, akshare=True, tushare=True, ak_revenue=100_500_000.0) -> Path:
    code_dir = tmp_path / "600406"
    if tushare:
        _write_json(code_dir / "tushare_fundamental.json", _provider_payload("tushare"))
    if akshare:
        _write_json(code_dir / "akshare_fundamental.json", _provider_payload("akshare", revenue=ak_revenue))
    return code_dir


def _comparison_dir_with_many_business_rows(tmp_path: Path, row_count: int = 30) -> Path:
    code_dir = tmp_path / "600406"
    for provider in ("tushare", "akshare"):
        payload = _provider_payload(provider)
        template = payload["blocks"]["business_composition"][0]
        rows = []
        for index in range(row_count):
            row = copy.deepcopy(template)
            row["segment_name"] = f"Segment {index:02d}"
            row["revenue"] = 1_000_000.0 + index
            row["revenue_ratio"] = round(100 / row_count, 4)
            row["gross_margin"] = 20.0 + index / 10
            rows.append(row)
        payload["blocks"]["business_composition"] = rows
        _write_json(code_dir / f"{provider}_fundamental.json", payload)
    return code_dir


def _candidate(payload: dict, field_path: str, provider: str) -> dict:
    matches = [
        candidate
        for candidate in payload["candidates"]
        if candidate["field_path"] == field_path and candidate["source_provider"] == provider
    ]
    assert matches, f"missing candidate {provider}:{field_path}"
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


def test_builds_offline_payload_from_fake_fundamental_artifacts(tmp_path):
    code_dir = _comparison_dir(tmp_path)

    payload = build_fact_candidates_from_comparison_dir(code_dir)

    assert payload["code"] == "600406"
    assert payload["mode"] == "offline_artifact_candidate_generation"
    assert payload["source_artifacts"] == {
        "akshare_fundamental": "akshare_fundamental.json",
        "tushare_fundamental": "tushare_fundamental.json",
    }
    assert V11_SUMMARY_KEYS <= set(payload)
    assert payload["candidates"]
    assert {candidate["source_provider"] for candidate in payload["candidates"]} == {"tushare", "akshare"}


def test_candidates_have_required_schema_and_do_not_merge_providers(tmp_path):
    payload = build_fact_candidates_from_comparison_dir(_comparison_dir(tmp_path))

    assert all(REQUIRED_CANDIDATE_KEYS <= set(candidate) for candidate in payload["candidates"])
    assert all(set(candidate) == REQUIRED_CANDIDATE_KEYS for candidate in payload["candidates"])
    revenue_candidates = [
        candidate for candidate in payload["candidates"] if candidate["field_path"] == "financial_metrics.revenue"
    ]

    assert {candidate["source_provider"] for candidate in revenue_candidates} == {"tushare", "akshare"}
    assert len(revenue_candidates) == 2
    assert {candidate["value"] for candidate in revenue_candidates} == {100_000_000.0, 100_500_000.0}


def test_field_group_summary_counts_candidates_by_block_provider_and_status(tmp_path):
    payload = build_fact_candidates_from_comparison_dir(_comparison_dir(tmp_path))
    summary = payload["field_group_summary"]

    assert summary["basic_info"] == {
        "candidate_count": 10,
        "tushare_candidate_count": 5,
        "akshare_candidate_count": 5,
        "auto_accepted_count": 0,
        "manual_review_required_count": 10,
        "source_conflict_count": 0,
        "period_mismatch_count": 0,
        "unit_unknown_count": 0,
        "provider_missing_count": 0,
        "mapping_missing_count": 0,
        "not_available_count": 0,
    }
    assert summary["financial_metrics"]["candidate_count"] == 20
    assert summary["financial_metrics"]["tushare_candidate_count"] == 10
    assert summary["financial_metrics"]["akshare_candidate_count"] == 10
    assert summary["financial_metrics"]["auto_accepted_count"] == 10
    assert summary["financial_metrics"]["manual_review_required_count"] == 10
    assert summary["valuation_metrics"]["candidate_count"] == 8
    assert summary["valuation_metrics"]["auto_accepted_count"] == 3
    assert summary["valuation_metrics"]["manual_review_required_count"] == 4
    assert summary["valuation_metrics"]["mapping_missing_count"] == 1
    assert summary["business_composition"]["candidate_count"] == 12
    assert summary["business_composition"]["manual_review_required_count"] == 12


def test_auto_accepted_core_fields_lists_only_core_auto_acceptance_items(tmp_path):
    payload = build_fact_candidates_from_comparison_dir(_comparison_dir(tmp_path))
    core_fields = payload["auto_accepted_core_fields"]

    assert [item["field_path"] for item in core_fields] == [
        "financial_metrics.revenue",
        "financial_metrics.net_profit",
        "financial_metrics.gross_margin",
        "financial_metrics.roe",
        "financial_metrics.operating_cashflow",
        "valuation_metrics.pe_ttm",
        "valuation_metrics.pb",
        "valuation_metrics.market_cap",
    ]
    assert {item["source_provider"] for item in core_fields} == {"tushare"}
    assert all(item["confidence"] == "high" for item in core_fields)
    assert all(item["canonical_unit"] for item in core_fields)
    assert not any(item["field_path"] == "financial_metrics.capex" for item in core_fields)
    assert not any(item["field_path"] == "valuation_metrics.as_of_date" for item in core_fields)
    assert all(item["report_period"] or item["as_of_date"] for item in core_fields)


def test_manual_review_priority_queue_aggregates_business_composition_and_respects_limit(tmp_path):
    payload = build_fact_candidates_from_comparison_dir(_comparison_dir_with_many_business_rows(tmp_path))
    queue = payload["manual_review_priority_queue"]

    assert len(queue) <= 20
    business_items = [item for item in queue if item["field_path"].startswith("business_composition")]
    assert business_items
    assert all("[" not in item["field_path"] for item in business_items)
    assert any(
        item["field_path"] == "business_composition.revenue_ratio"
        and item["candidate_count"] == 60
        and len(item["representative_candidates"]) <= 3
        for item in business_items
    )
    assert any(item["issue_type"] == "business_composition_field_review" for item in business_items)


def test_business_composition_summary_compresses_periods_coverage_and_next_action(tmp_path):
    payload = build_fact_candidates_from_comparison_dir(_comparison_dir(tmp_path))
    summary = payload["business_composition_summary"]

    assert summary["total_rows"] == 2
    assert summary["candidate_count"] == 12
    assert summary["providers_present"] == ["akshare", "tushare"]
    assert summary["periods_observed"] == ["2025-12-31"]
    assert summary["classification_type_coverage"]["available_count"] == 2
    assert summary["revenue_ratio_coverage"]["available_count"] == 2
    assert summary["gross_margin_coverage"]["available_count"] == 2
    assert summary["top_issue_categories"]
    next_action = summary["recommended_next_action"].lower()
    assert "fina_mainbz type=p/d/i" in next_action
    assert "do not auto-accept mixed group rows" in next_action
    assert "do not merge akshare and tushare composition rows" in next_action


def test_provider_quality_summary_counts_without_ground_truth_or_error_claims(tmp_path):
    payload = build_fact_candidates_from_comparison_dir(_comparison_dir(tmp_path))
    summary = payload["provider_quality_summary"]

    assert summary["tushare"]["auto_accepted_count"] == 13
    assert summary["akshare"]["auto_accepted_count"] == 0
    assert summary["tushare"]["manual_review_count"] == 12
    assert summary["akshare"]["manual_review_count"] == 25
    assert summary["tushare"]["mapping_missing_count"] == 1
    text = json.dumps(summary, ensure_ascii=False).lower()
    assert "ground truth" not in text
    assert "akshare is wrong" not in text
    assert "tushare is truth" not in text


def test_candidate_report_limitations_document_non_actions(tmp_path):
    payload = build_fact_candidates_from_comparison_dir(_comparison_dir(tmp_path))
    limitations = "\n".join(payload["candidate_report_limitations"]).lower()

    assert "not reviewed ground truth" in limitations
    assert "no fixture promotion" in limitations
    assert "no validator run" in limitations
    assert "no primary switch" in limitations
    assert "no automatic merge" in limitations
    assert "business composition still needs classification, period, and ratio review" in limitations
    assert "domain evidence" in limitations


def test_does_not_write_ground_truth_fixture(tmp_path):
    before = GROUND_TRUTH_FIXTURE.read_text(encoding="utf-8")

    payload = build_fact_candidates_from_comparison_dir(_comparison_dir(tmp_path))
    write_fact_candidate_report(payload, tmp_path / "ground_truth_candidates", "20260527T120000")

    assert GROUND_TRUTH_FIXTURE.read_text(encoding="utf-8") == before


def test_main_business_is_never_auto_accepted(tmp_path):
    payload = build_fact_candidates_from_comparison_dir(_comparison_dir(tmp_path))

    candidate = _candidate(payload, "basic_info.main_business", "tushare")

    assert candidate["review_status"] == "manual_review_required"
    assert candidate["missing_category"] == "manual_review_required"
    assert "main_business" in candidate["manual_review_note"]


def test_tushare_financial_and_valuation_fields_auto_accept_when_metadata_is_sufficient(tmp_path):
    payload = build_fact_candidates_from_comparison_dir(_comparison_dir(tmp_path))

    revenue = _candidate(payload, "financial_metrics.revenue", "tushare")
    pe_ttm = _candidate(payload, "valuation_metrics.pe_ttm", "tushare")

    assert revenue["review_status"] == "auto_accepted"
    assert revenue["confidence"] == "high"
    assert revenue["report_period"] == "2025-12-31"
    assert revenue["data_unit"] == "RMB yuan"
    assert revenue["canonical_unit"] == "RMB yuan"
    assert pe_ttm["review_status"] == "auto_accepted"
    assert pe_ttm["as_of_date"] == "2026-05-26"


def test_akshare_only_candidate_is_not_auto_accepted(tmp_path):
    payload = build_fact_candidates_from_comparison_dir(_comparison_dir(tmp_path, tushare=False))

    candidate = _candidate(payload, "valuation_metrics.pb", "akshare")

    assert candidate["review_status"] == "manual_review_required"
    assert candidate["missing_category"] == "manual_review_required"
    assert candidate["conflict_status"] == "provider_missing"


def test_provider_conflict_above_tolerance_marks_both_candidates(tmp_path):
    payload = build_fact_candidates_from_comparison_dir(_comparison_dir(tmp_path, ak_revenue=130_000_000.0))

    tushare = _candidate(payload, "financial_metrics.revenue", "tushare")
    akshare = _candidate(payload, "financial_metrics.revenue", "akshare")

    assert tushare["review_status"] == "source_conflict"
    assert akshare["review_status"] == "source_conflict"
    assert tushare["conflict_status"] == "source_conflict"
    assert akshare["missing_category"] == "source_conflict"
    assert payload["summary"]["source_conflict_count"] >= 2


def test_unit_unknown_marks_manual_review_without_guessing(tmp_path):
    code_dir = tmp_path / "600406"
    payload = _provider_payload("tushare")
    financial = payload["blocks"]["financial_metrics"][0]
    financial["field_metadata"] = {"capex": {"data_unit": None, "canonical_unit": None}}
    _write_json(code_dir / "tushare_fundamental.json", payload)

    report = build_fact_candidates_from_comparison_dir(code_dir)
    candidate = _candidate(report, "financial_metrics.capex", "tushare")

    assert candidate["review_status"] == "unit_unknown"
    assert candidate["missing_category"] == "unit_unknown"
    assert candidate["confidence"] == "low"


def test_valuation_as_of_date_mismatch_marks_period_mismatch(tmp_path):
    code_dir = tmp_path / "600406"
    _write_json(code_dir / "tushare_fundamental.json", _provider_payload("tushare", valuation_date="2026-05-26"))
    _write_json(code_dir / "akshare_fundamental.json", _provider_payload("akshare", valuation_date="2026-05-27"))

    payload = build_fact_candidates_from_comparison_dir(code_dir)
    tushare = _candidate(payload, "valuation_metrics.market_cap", "tushare")
    akshare = _candidate(payload, "valuation_metrics.market_cap", "akshare")

    assert tushare["review_status"] == "period_mismatch"
    assert akshare["review_status"] == "period_mismatch"
    assert tushare["conflict_status"] == "period_mismatch"
    assert payload["summary"]["period_mismatch_count"] >= 2


def test_writer_writes_only_fact_candidates_json_under_tmpdir(tmp_path):
    payload = build_fact_candidates_from_comparison_dir(_comparison_dir(tmp_path / "input"))
    output_root = tmp_path / "ground_truth_candidates"

    path = write_fact_candidate_report(payload, output_root, "20260527T120000")

    assert path == output_root / "20260527T120000" / "600406" / "fact_candidates.json"
    assert json.loads(path.read_text(encoding="utf-8"))["mode"] == "offline_artifact_candidate_generation"
    assert [item for item in output_root.rglob("*") if item.is_file()] == [path]


def test_writer_rejects_path_traversal(tmp_path):
    payload = build_fact_candidates_from_comparison_dir(_comparison_dir(tmp_path / "input"))

    with pytest.raises(FactCandidateArtifactBoundaryError):
        write_fact_candidate_report(payload, tmp_path / "ground_truth_candidates", "..\\escape")

    bad_payload = copy.deepcopy(payload)
    bad_payload["code"] = "..\\escape"
    with pytest.raises(FactCandidateArtifactBoundaryError):
        write_fact_candidate_report(bad_payload, tmp_path / "ground_truth_candidates", "20260527T120000")


def test_writer_token_scanner_blocks_token_like_payload(tmp_path):
    payload = build_fact_candidates_from_comparison_dir(_comparison_dir(tmp_path / "input"))
    bad_payload = copy.deepcopy(payload)
    bad_payload["candidates"][0]["source_trace"]["note"] = (
        "token=A9abcdefABCDEF1234567890abcdefABCDEF1234567890z"
    )

    with pytest.raises(FactCandidateSecretError):
        write_fact_candidate_report(bad_payload, tmp_path / "ground_truth_candidates", "20260527T120000")


def test_writer_token_scanner_masks_token_like_dict_key_in_exception_location(tmp_path):
    secret = "A9abcdefABCDEF1234567890abcdefABCDEF1234567890z"
    payload = build_fact_candidates_from_comparison_dir(_comparison_dir(tmp_path / "input"))
    bad_payload = copy.deepcopy(payload)
    bad_payload["candidates"][0]["source_trace"]["nested"] = {secret: "value"}

    with pytest.raises(FactCandidateSecretError) as exc_info:
        write_fact_candidate_report(bad_payload, tmp_path / "ground_truth_candidates", "20260527T120000")

    message = str(exc_info.value)
    assert "<masked>" in message
    assert "<masked_key>" in message
    _assert_secret_not_rendered(secret, message)


def test_module_does_not_import_provider_runtime_read_env_or_network():
    source = inspect.getsource(generator_module)

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


def test_payload_contains_no_mcp_urls_secret_paths_or_investment_advice_fields(tmp_path):
    payload = build_fact_candidates_from_comparison_dir(_comparison_dir(tmp_path))
    text = json.dumps(payload, ensure_ascii=False).lower()

    assert "mcp://" not in text
    assert "c:\\users\\" not in text
    assert "c:/users/" not in text
    forbidden_keys = {"buy", "sell", "target_price", "position", "stop_loss", "take_profit", "portfolio_weight"}
    assert not (forbidden_keys & {str(key).lower() for key in _walk_keys(payload)})
