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
    assert payload["candidates"]
    assert {candidate["source_provider"] for candidate in payload["candidates"]} == {"tushare", "akshare"}


def test_candidates_have_required_schema_and_do_not_merge_providers(tmp_path):
    payload = build_fact_candidates_from_comparison_dir(_comparison_dir(tmp_path))

    assert all(REQUIRED_CANDIDATE_KEYS <= set(candidate) for candidate in payload["candidates"])
    revenue_candidates = [
        candidate for candidate in payload["candidates"] if candidate["field_path"] == "financial_metrics.revenue"
    ]

    assert {candidate["source_provider"] for candidate in revenue_candidates} == {"tushare", "akshare"}
    assert len(revenue_candidates) == 2
    assert {candidate["value"] for candidate in revenue_candidates} == {100_000_000.0, 100_500_000.0}


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
