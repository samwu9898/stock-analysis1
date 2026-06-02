# -*- coding: utf-8 -*-

from __future__ import annotations

import copy
import json

import pytest

from src.fundamental_skill.research_planning.controlled_real_tushare_professional_compact_brief_pilot import (
    CONTROLLED_REAL_TUSHARE_PROFESSIONAL_COMPACT_BRIEF_REQUEST_SCHEMA_VERSION,
    CONTROLLED_REAL_TUSHARE_PROFESSIONAL_COMPACT_BRIEF_RESULT_SCHEMA_VERSION,
    CONTROLLED_REAL_TUSHARE_PROVIDER_CANDIDATE_BUNDLE_SCHEMA_VERSION,
    E2E_READINESS_READY,
    E2E_READINESS_SKIPPED,
    INTERNAL_EVIDENCE_STATUS_PROVIDER_CANDIDATE,
    INTERNAL_VERIFICATION_STATUS_PENDING_OFFICIAL_VERIFICATION,
    OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF,
    OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF_AND_INTERNAL_PAYLOAD,
    PROFESSIONAL_ANALYST_COMPACT_BRIEF_SCHEMA_VERSION,
    PROFESSIONAL_BRIEF_SECTION_KEYS,
    TUSHARE_CLIENT_MODE_ENV_LIVE,
    TUSHARE_CLIENT_MODE_FAKE,
    TUSHARE_CLIENT_MODE_INJECTED,
    ControlledRealTushareProfessionalCompactBriefPilotError,
    build_controlled_real_tushare_professional_compact_brief_result,
)


class _FakeFinancialClient:
    def __init__(self, *, ts_code="600406.SH", fail_with=None):
        self.ts_code = ts_code
        self.fail_with = fail_with
        self.calls = []

    def income(self, **params):
        return self._call(
            "income",
            params,
            {
                "revenue": 1000,
                "n_income_attr_p": 120,
                "total_profit": 150,
                "operate_profit": 140,
                "basic_eps": 1.23,
            },
        )

    def balancesheet(self, **params):
        return self._call(
            "balancesheet",
            params,
            {
                "total_assets": 3000,
                "total_liab": 900,
                "total_hldr_eqy_exc_min_int": 2100,
                "accounts_receiv": 330,
                "inventories": 80,
            },
        )

    def cashflow(self, **params):
        return self._call(
            "cashflow",
            params,
            {
                "n_cashflow_act": 180,
                "c_cash_equ_end_period": 500,
                "c_fr_sale_sg": 980,
            },
        )

    def fina_indicator(self, **params):
        return self._call(
            "fina_indicator",
            params,
            {
                "grossprofit_margin": 32.5,
                "netprofit_margin": 12.0,
                "roe": 16.0,
                "debt_to_assets": 30.0,
                "ar_turn": 4.0,
                "inv_turn": 8.0,
            },
        )

    def _call(self, endpoint, params, values):
        self.calls.append({"endpoint": endpoint, "params": dict(params)})
        if self.fail_with is not None:
            raise RuntimeError(self.fail_with)
        period = params["period"]
        row = {
            "ts_code": params["ts_code"],
            "period": period,
            "ann_date": "20260430",
            "end_date": period,
        }
        row.update(values)
        return [row]


def _request(**overrides):
    request = {
        "schema_version": CONTROLLED_REAL_TUSHARE_PROFESSIONAL_COMPACT_BRIEF_REQUEST_SCHEMA_VERSION,
        "stock_code": "600406",
        "ts_code": "600406.SH",
        "company_name_hint": "Guodian NARI",
        "periods": ["20251231"],
        "allow_network": False,
        "tushare_client_mode": TUSHARE_CLIENT_MODE_INJECTED,
        "output_mode": OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF,
        "not_for_trading_advice": True,
    }
    request.update(overrides)
    return request


def _build(client=None, **overrides):
    request = _request(**overrides)
    return build_controlled_real_tushare_professional_compact_brief_result(
        request,
        tushare_client=client or _FakeFinancialClient(ts_code=request["ts_code"]),
    )


def _professional_text(result):
    return json.dumps(result["professional_compact_brief"], ensure_ascii=False)


def test_valid_request_with_injected_fake_tushare_client_returns_ready_result():
    result = _build()

    assert result["schema_version"] == (
        CONTROLLED_REAL_TUSHARE_PROFESSIONAL_COMPACT_BRIEF_RESULT_SCHEMA_VERSION
    )
    assert result["readiness"]["status"] == E2E_READINESS_READY
    assert result["professional_compact_brief"]["schema_version"] == (
        PROFESSIONAL_ANALYST_COMPACT_BRIEF_SCHEMA_VERSION
    )
    assert result["not_for_trading_advice"] is True


def test_allow_network_false_uses_fake_or_injected_only():
    client = _FakeFinancialClient()
    result = _build(client)

    assert result["readiness"]["status"] == E2E_READINESS_READY
    assert result["request_summary"]["allow_network"] is False
    assert [call["endpoint"] for call in client.calls] == [
        "income",
        "balancesheet",
        "cashflow",
        "fina_indicator",
    ]


def test_fake_mode_without_injected_client_returns_ready_without_network():
    result = build_controlled_real_tushare_professional_compact_brief_result(
        _request(tushare_client_mode=TUSHARE_CLIENT_MODE_FAKE)
    )

    assert result["readiness"]["status"] == E2E_READINESS_READY
    assert result["provider_candidate_bundle"]["candidate_items"]


def test_allow_network_false_does_not_read_or_echo_env_token(monkeypatch):
    secret = "S3cr3tValueThatShouldStayHidden123456789"
    monkeypatch.setenv("TUSHARE_" + "TOKEN", secret)

    result = _build()

    assert result["readiness"]["status"] == E2E_READINESS_READY
    assert secret not in json.dumps(result, ensure_ascii=False)


def test_allow_network_true_without_tushare_token_structured_skip(monkeypatch):
    monkeypatch.delenv("TUSHARE_" + "TOKEN", raising=False)

    result = build_controlled_real_tushare_professional_compact_brief_result(
        _request(
            allow_network=True,
            tushare_client_mode=TUSHARE_CLIENT_MODE_ENV_LIVE,
        )
    )

    assert result["readiness"]["status"] == E2E_READINESS_SKIPPED
    assert result["blocked_reasons"] == ["environment_credential_missing"]
    assert result["professional_compact_brief"] is None


def test_token_cannot_be_passed_in_request():
    request = _request()
    request["token"] = "not-allowed"

    with pytest.raises(
        ControlledRealTushareProfessionalCompactBriefPilotError,
        match="secret",
    ):
        build_controlled_real_tushare_professional_compact_brief_result(request)


def test_token_like_string_rejected():
    with pytest.raises(
        ControlledRealTushareProfessionalCompactBriefPilotError,
        match="secret_like_string",
    ):
        build_controlled_real_tushare_professional_compact_brief_result(
            _request(company_name_hint="S3cr3tValueThatShouldStayHidden123456789"),
            tushare_client=_FakeFinancialClient(),
        )


def test_provider_candidate_bundle_schema_correct():
    bundle = _build()["provider_candidate_bundle"]

    assert bundle["schema_version"] == (
        CONTROLLED_REAL_TUSHARE_PROVIDER_CANDIDATE_BUNDLE_SCHEMA_VERSION
    )
    assert bundle["provider"] == "Tushare"
    assert bundle["internal_evidence_status"] == (
        INTERNAL_EVIDENCE_STATUS_PROVIDER_CANDIDATE
    )
    assert bundle["internal_verification_status"] == (
        INTERNAL_VERIFICATION_STATUS_PENDING_OFFICIAL_VERIFICATION
    )
    assert bundle["official_verified_count"] == 0


def test_candidate_items_internal_statuses_are_candidate_and_pending():
    items = _build()["provider_candidate_bundle"]["candidate_items"]

    assert items
    assert all(
        item["internal_evidence_status"] == INTERNAL_EVIDENCE_STATUS_PROVIDER_CANDIDATE
        for item in items
    )
    assert all(
        item["internal_verification_status"]
        == INTERNAL_VERIFICATION_STATUS_PENDING_OFFICIAL_VERIFICATION
        for item in items
    )


def test_internal_analysis_brief_and_wrapper_response_generated():
    result = _build()

    assert result["internal_analysis_brief"]["schema_version"] == (
        "user_facing_analysis_brief.v1"
    )
    assert result["skill_wrapper_response"]["readiness"]["status"] == "ready"
    assert result["skill_wrapper_response"]["compact_response"]


def test_professional_compact_brief_has_required_user_sections():
    brief = _build()["professional_compact_brief"]

    for key in PROFESSIONAL_BRIEF_SECTION_KEYS:
        assert key in brief
    for key in (
        "overall_view",
        "business_view",
        "financial_view",
        "operating_quality_view",
        "industry_macro_view",
        "risk_view",
    ):
        assert brief[key]["view"]
    assert brief["key_variables"]
    assert brief["conclusion_boundary"]
    assert brief["source_note"] == "数据来源：Tushare。"
    assert "公开披露信息" not in json.dumps(brief, ensure_ascii=False)


def test_professional_compact_brief_gives_analysis_view_not_empty_status():
    text = _professional_text(_build())

    assert "基本面判断" in text
    assert "收入" in text
    assert "利润" in text
    assert "现金流" in text
    assert "经营质量" in text
    assert len(text) > 600


def test_professional_compact_brief_excludes_engineering_labels():
    text = _professional_text(_build())

    for forbidden in (
        "待核验",
        "数据缺口",
        "推理",
        "provider_candidate",
        "provider candidate",
        "pending_official_verification",
        "official verification",
        "official_verified_count",
        "provider",
        "候选数据",
        "证据状态",
        "口径一致性",
    ):
        assert forbidden not in text


def test_professional_compact_brief_does_not_push_judgment_to_user():
    text = _professional_text(_build())

    for forbidden in ("用户自行", "自行判断", "自行跟踪", "需要用户", "建议用户", "请结合"):
        assert forbidden not in text


def test_output_mode_professional_compact_brief_and_internal_payload_returns_payload():
    result = _build(
        output_mode=OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF_AND_INTERNAL_PAYLOAD
    )

    assert result["internal_payload"]["schema_version"] == (
        "controlled_real_tushare_professional_internal_payload.v1"
    )
    assert result["internal_payload"]["provider_candidate_count"] > 0


def test_professional_compact_brief_has_no_backend_trace():
    text = _professional_text(_build())

    for forbidden in ("page_number", "snippet", "source_url", "sha256", "cache_path", "anchor map"):
        assert forbidden not in text


def test_professional_compact_brief_has_no_trading_advice():
    text = _professional_text(_build()).casefold()

    for forbidden in (
        "buy",
        "sell",
        "hold",
        "target price",
        "portfolio",
        "position",
        "technical signal",
        "trading advice",
        "买入",
        "卖出",
        "持有",
        "目标价",
        "仓位",
        "技术信号",
        "投资建议",
    ):
        assert forbidden.casefold() not in text


def test_input_request_not_mutated():
    request = _request(
        output_mode=OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF_AND_INTERNAL_PAYLOAD
    )
    before = copy.deepcopy(request)

    build_controlled_real_tushare_professional_compact_brief_result(
        request,
        tushare_client=_FakeFinancialClient(),
    )

    assert request == before


def test_non_600406_fake_sample_passes():
    result = _build(
        _FakeFinancialClient(ts_code="000001.SZ"),
        stock_code="000001",
        ts_code="000001.SZ",
        company_name_hint="Sample Company",
    )

    assert result["readiness"]["status"] == E2E_READINESS_READY
    assert result["professional_compact_brief"]["stock_code"] == "000001"
    assert result["professional_compact_brief"]["ts_code"] == "000001.SZ"


def test_no_output_fixtures_or_manifest_write(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    result = _build()

    assert result["readiness"]["status"] == E2E_READINESS_READY
    assert not (tmp_path / "output").exists()
    assert not (tmp_path / "fixtures").exists()
    assert not (tmp_path / "accepted_manifest.json").exists()
