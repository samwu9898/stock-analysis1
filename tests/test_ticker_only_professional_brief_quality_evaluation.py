# -*- coding: utf-8 -*-

from __future__ import annotations

import copy
import json
import socket

import pytest

import src.fundamental_skill.research_planning.ticker_only_professional_brief_quality_evaluation as evaluation_module
from src.fundamental_skill.research_planning.ticker_only_professional_brief_quality_evaluation import (
    QUALITY_SAMPLE_IDS,
    QUALITY_STATUS_PASS,
    QUALITY_STATUS_WARNING,
    RUBRIC_DIMENSION_IDS,
    TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_EVALUATION_REQUEST_SCHEMA_VERSION,
    build_default_quality_rubric,
    build_quality_sample_requests,
    build_ticker_only_professional_brief_quality_evaluation,
)


_BASE_RESULT = None


def _request(**overrides):
    request = {
        "schema_version": (
            TICKER_ONLY_PROFESSIONAL_BRIEF_QUALITY_EVALUATION_REQUEST_SCHEMA_VERSION
        ),
        "not_for_trading_advice": True,
    }
    request.update(overrides)
    return request


def _result():
    global _BASE_RESULT
    if _BASE_RESULT is None:
        _BASE_RESULT = build_ticker_only_professional_brief_quality_evaluation(
            _request()
        )
    return copy.deepcopy(_BASE_RESULT)


def _sample_result(sample_id):
    for sample in _result()["sample_results"]:
        if sample["sample_id"] == sample_id:
            return sample
    raise AssertionError(f"missing sample result: {sample_id}")


def _issue_ids(sample):
    return {issue["issue_id"] for issue in sample["issues"]}


def _section(section_id, title, view):
    return {
        "schema_version": "professional_analyst_compact_brief_section.v1",
        "section_id": section_id,
        "title": title,
        "view": view,
        "not_for_trading_advice": True,
    }


def _professional_brief(**overrides):
    brief = {
        "schema_version": "professional_analyst_compact_brief.v1",
        "stock_code": "600406",
        "ts_code": "600406.SH",
        "company_name_hint": "Guodian NARI",
        "title": "Guodian NARI professional compact brief",
        "overall_view": _section(
            "overall_view",
            "总体基本面判断",
            "公司基本面判断应同时观察收入、利润、现金流和资产结构之间的相互支撑。",
        ),
        "business_view": _section(
            "business_view",
            "公司业务逻辑判断",
            "业务判断围绕主营构成、订单交付、回款节奏和利润率结构展开。",
        ),
        "financial_view": _section(
            "financial_view",
            "财务表现判断",
            "财务解释关注收入利润同步性、盈利能力、毛利率和资产负债结构。",
        ),
        "operating_quality_view": _section(
            "operating_quality_view",
            "经营质量判断",
            "经营质量判断关注现金流和利润匹配、应收占用、回款效率和周转表现。",
        ),
        "industry_macro_view": _section(
            "industry_macro_view",
            "行业和宏观传导判断",
            "行业和宏观变量需要通过订单、交付、回款和利润率传导到基本面。",
        ),
        "risk_view": _section(
            "risk_view",
            "核心风险判断",
            "核心风险在收入、利润、现金流、应收和资产负债压力之间的背离。",
        ),
        "key_variables": [
            "收入与利润同步性",
            "经营现金流与利润匹配度",
            "应收账款回款效率",
            "利润率结构",
            "资产负债结构",
        ],
        "conclusion_boundary": "结论边界聚焦基本面质量和经营韧性，不展开估值区间或动作层面。",
        "source_note": "数据来源：Tushare。",
        "not_for_trading_advice": True,
    }
    brief.update(overrides)
    return brief


def test_valid_evaluation_request_returns_result():
    result = _result()

    assert result["schema_version"].endswith("_result.v1")
    assert result["sample_count"] == len(QUALITY_SAMPLE_IDS)
    assert result["overall_status"] == QUALITY_STATUS_WARNING
    assert result["not_for_trading_advice"] is True


def test_evaluation_uses_wrapper_ticker_only_professional_brief_path(monkeypatch):
    calls = []

    def fake_wrapper(request, *, tushare_client=None):
        calls.append((copy.deepcopy(request), tushare_client))
        return {
            "readiness": {"status": "ready"},
            "professional_compact_brief": _professional_brief(
                stock_code=request["stock_code"],
                ts_code=request["ts_code"],
                company_name_hint=request["company_name_hint"],
            ),
        }

    monkeypatch.setattr(
        evaluation_module,
        "build_a_share_fundamental_skill_response",
        fake_wrapper,
    )

    result = build_ticker_only_professional_brief_quality_evaluation(
        _request(sample_ids=["baseline_600406_like"])
    )

    assert result["sample_count"] == 1
    assert calls
    wrapper_request, injected_client = calls[0]
    assert wrapper_request["input_mode"] == "ticker_only_professional_brief"
    assert wrapper_request["output_mode"] == "professional_compact_brief"
    assert wrapper_request["tushare_client_mode"] == "injected"
    assert wrapper_request["allow_network"] is False
    assert wrapper_request["allow_file_writes"] is False
    assert injected_client is not None


@pytest.mark.parametrize("sample_id", QUALITY_SAMPLE_IDS)
def test_sample_set_includes_required_scenarios(sample_id):
    samples = build_quality_sample_requests()

    assert sample_id in {sample["sample_id"] for sample in samples}


def test_all_generated_samples_have_professional_compact_brief_preview():
    for sample in _result()["sample_results"]:
        assert sample["professional_compact_brief_preview"]
        assert sample["brief_section_keys"]


def test_scorecard_contains_required_rubric_dimensions():
    scorecard = _sample_result("baseline_600406_like")["scorecard"]

    assert tuple(scorecard["dimensions"]) == RUBRIC_DIMENSION_IDS
    assert set(build_default_quality_rubric()["dimension_ids"]) == set(
        RUBRIC_DIMENSION_IDS
    )


def test_pass_warning_fail_counts_are_consistent():
    result = _result()

    assert (
        result["pass_count"] + result["warning_count"] + result["fail_count"]
        == result["sample_count"]
    )
    for sample in result["sample_results"]:
        scorecard = sample["scorecard"]
        assert (
            scorecard["pass_count"]
            + scorecard["warning_count"]
            + scorecard["fail_count"]
            == len(RUBRIC_DIMENSION_IDS)
        )
        assert scorecard["issue_count"] == len(scorecard["issues"])


def test_aggregate_issues_are_deterministic():
    result = _result()
    aggregate_issue_ids = [issue["issue_id"] for issue in result["aggregate_issues"]]

    assert aggregate_issue_ids == [
        "balance_sheet_debt_pressure",
        "cashflow_profit_quality_pressure",
        "receivables_working_capital_pressure",
        "sparse_metrics_professional_boundary",
    ]


def test_cashflow_supports_profit_sample_passes_cashflow_profit_judgment():
    sample = _sample_result("cashflow_supports_profit")

    assert sample["overall_status"] == QUALITY_STATUS_PASS
    assert sample["scorecard"]["dimensions"][
        "has_cashflow_profit_match_judgment"
    ]["status"] == QUALITY_STATUS_PASS


def test_profit_stronger_than_cashflow_sample_flags_quality_pressure():
    sample = _sample_result("profit_stronger_than_cashflow")

    assert sample["overall_status"] == QUALITY_STATUS_WARNING
    assert "cashflow_profit_quality_pressure" in _issue_ids(sample)


def test_high_receivables_pressure_sample_flags_working_capital_risk():
    sample = _sample_result("high_receivables_pressure")

    assert sample["overall_status"] == QUALITY_STATUS_WARNING
    assert "receivables_working_capital_pressure" in _issue_ids(sample)


def test_high_debt_pressure_sample_flags_balance_sheet_pressure():
    sample = _sample_result("high_debt_pressure")

    assert sample["overall_status"] == QUALITY_STATUS_WARNING
    assert "balance_sheet_debt_pressure" in _issue_ids(sample)


def test_sparse_or_missing_metrics_sample_warns_without_engineering_labels():
    sample = _sample_result("sparse_or_missing_metrics")
    serialized = json.dumps(sample, ensure_ascii=False)

    assert sample["overall_status"] == QUALITY_STATUS_WARNING
    assert "sparse_metrics_professional_boundary" in _issue_ids(sample)
    for forbidden in ("provider_candidate", "pending_official_verification", "待核验", "数据缺口", "推理"):
        assert forbidden not in serialized


def test_non_600406_sample_passes():
    sample = _sample_result("non_600406_sample")

    assert sample["overall_status"] == QUALITY_STATUS_PASS
    assert sample["stock_code"] == "000001"
    assert sample["ts_code"] == "000001.SZ"


def test_input_request_not_mutated():
    request = _request(sample_ids=["baseline_600406_like"])
    before = copy.deepcopy(request)

    build_ticker_only_professional_brief_quality_evaluation(request)

    assert request == before


def test_no_output_fixtures_or_manifest_write(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    result = build_ticker_only_professional_brief_quality_evaluation(
        _request(sample_ids=["baseline_600406_like"])
    )

    assert result["sample_count"] == 1
    assert not (tmp_path / "output").exists()
    assert not (tmp_path / "fixtures").exists()
    assert not (tmp_path / "accepted_manifest.json").exists()


def test_no_network_call(monkeypatch):
    def fail_network(*_args, **_kwargs):
        raise AssertionError("network should not be called")

    monkeypatch.setattr(socket, "create_connection", fail_network)

    result = build_ticker_only_professional_brief_quality_evaluation(
        _request(sample_ids=["baseline_600406_like"])
    )

    assert result["sample_count"] == 1


def test_result_does_not_include_raw_provider_bundle_or_candidate_items():
    serialized = json.dumps(_result(), ensure_ascii=False)

    for forbidden in (
        "raw_provider_bundle",
        "provider_candidate_bundle",
        "candidate_items",
        "raw_provider_queue",
    ):
        assert forbidden not in serialized
