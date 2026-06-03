# -*- coding: utf-8 -*-

from __future__ import annotations

import copy
import json

import pytest

import src.fundamental_skill.research_planning.a_share_fundamental_skill_wrapper as wrapper
from src.fundamental_skill.research_planning.a_share_fundamental_skill_wrapper import (
    A_SHARE_FUNDAMENTAL_COMPACT_RESPONSE_SCHEMA_VERSION,
    A_SHARE_FUNDAMENTAL_SKILL_REQUEST_SCHEMA_VERSION,
    A_SHARE_FUNDAMENTAL_SKILL_RESPONSE_SCHEMA_VERSION,
    BLOCKED_REASON_VALIDATED_ANALYSIS_INPUT_REQUIRED,
    INPUT_MODE_ANALYSIS_BRIEF,
    INPUT_MODE_ORCHESTRATION_RESULT,
    INPUT_MODE_TICKER_ONLY_PROFESSIONAL_BRIEF,
    OUTPUT_MODE_COMPACT_BRIEF,
    OUTPUT_MODE_COMPACT_BRIEF_AND_REPORT_V1_COMPATIBILITY_PAYLOAD,
    OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF,
    OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF_AND_INTERNAL_PAYLOAD,
    PROFESSIONAL_BRIEF_SECTION_KEYS,
    SKILL_READINESS_BLOCKED,
    SKILL_READINESS_READY,
    TUSHARE_CLIENT_MODE_ENV_LIVE,
    TUSHARE_CLIENT_MODE_FAKE,
    TUSHARE_CLIENT_MODE_INJECTED,
    AShareFundamentalSkillWrapperError,
    build_a_share_fundamental_skill_response,
)
from tests.test_controlled_real_tushare_professional_compact_brief_pilot import (
    _FakeFinancialClient,
)
from tests.test_user_facing_analysis_brief import _brief, _orchestration_result


_SAMPLE_BRIEF = None
_SAMPLE_ORCHESTRATION_RESULT = None


def _sample_brief():
    global _SAMPLE_BRIEF
    if _SAMPLE_BRIEF is None:
        _SAMPLE_BRIEF = _brief()
    return copy.deepcopy(_SAMPLE_BRIEF)


def _sample_orchestration_result():
    global _SAMPLE_ORCHESTRATION_RESULT
    if _SAMPLE_ORCHESTRATION_RESULT is None:
        _SAMPLE_ORCHESTRATION_RESULT = _orchestration_result()
    return copy.deepcopy(_SAMPLE_ORCHESTRATION_RESULT)


def _request(**overrides):
    request = {
        "schema_version": A_SHARE_FUNDAMENTAL_SKILL_REQUEST_SCHEMA_VERSION,
        "stock_code": "600406",
        "ts_code": "600406.SH",
        "company_name_hint": "Guodian NARI",
        "input_mode": INPUT_MODE_ANALYSIS_BRIEF,
        "output_mode": OUTPUT_MODE_COMPACT_BRIEF,
        "user_facing_analysis_brief": _sample_brief(),
        "allow_network": False,
        "allow_file_writes": False,
        "not_for_trading_advice": True,
    }
    request.update(overrides)
    return request


def _ticker_request(**overrides):
    request = {
        "schema_version": A_SHARE_FUNDAMENTAL_SKILL_REQUEST_SCHEMA_VERSION,
        "stock_code": "600406",
        "ts_code": "600406.SH",
        "company_name_hint": "Guodian NARI",
        "periods": ["20251231"],
        "input_mode": INPUT_MODE_TICKER_ONLY_PROFESSIONAL_BRIEF,
        "output_mode": OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF,
        "tushare_client_mode": TUSHARE_CLIENT_MODE_INJECTED,
        "allow_network": False,
        "allow_file_writes": False,
        "not_for_trading_advice": True,
    }
    request.update(overrides)
    return request


def _ticker_build(client=None, **overrides):
    request = _ticker_request(**overrides)
    if client is None and request.get("tushare_client_mode") == TUSHARE_CLIENT_MODE_INJECTED:
        client = _FakeFinancialClient(ts_code=request.get("ts_code") or "600406.SH")
    return build_a_share_fundamental_skill_response(
        request,
        tushare_client=client,
    )


def test_valid_request_with_user_facing_analysis_brief_returns_ready_response():
    response = build_a_share_fundamental_skill_response(_request())

    assert response["schema_version"] == A_SHARE_FUNDAMENTAL_SKILL_RESPONSE_SCHEMA_VERSION
    assert response["readiness"]["status"] == SKILL_READINESS_READY
    assert response["readiness"]["input_mode"] == INPUT_MODE_ANALYSIS_BRIEF
    assert response["compact_response"]["stock_code"] == "600406"
    assert response["user_facing_analysis_brief"]["schema_version"] == (
        "user_facing_analysis_brief.v1"
    )
    assert response["not_for_trading_advice"] is True


def test_valid_request_with_orchestration_result_builds_analysis_brief():
    request = _request(
        input_mode=INPUT_MODE_ORCHESTRATION_RESULT,
        user_facing_analysis_brief=None,
        orchestration_result=_sample_orchestration_result(),
    )

    response = build_a_share_fundamental_skill_response(request)

    assert response["readiness"]["status"] == SKILL_READINESS_READY
    assert response["readiness"]["input_mode"] == INPUT_MODE_ORCHESTRATION_RESULT
    assert response["user_facing_analysis_brief"]["schema_version"] == (
        "user_facing_analysis_brief.v1"
    )
    assert response["compact_response"]["section_summaries"]


def test_compact_response_schema_correct():
    compact = build_a_share_fundamental_skill_response(_request())["compact_response"]

    assert compact["schema_version"] == A_SHARE_FUNDAMENTAL_COMPACT_RESPONSE_SCHEMA_VERSION
    assert set(compact) == {
        "schema_version",
        "stock_code",
        "ts_code",
        "company_name_hint",
        "title",
        "summary_points",
        "section_summaries",
        "labels_used",
        "cannot_conclude_yet",
        "tracking_indicators",
        "markdown_preview",
        "not_for_trading_advice",
    }
    assert len(compact["section_summaries"]) == 9
    assert compact["not_for_trading_advice"] is True


def test_compact_response_includes_user_facing_section_summaries():
    compact = build_a_share_fundamental_skill_response(_request())["compact_response"]
    section_ids = [section["section_id"] for section in compact["section_summaries"]]

    assert section_ids == [
        "subject_summary",
        "current_judgment_boundary",
        "business_logic",
        "financial_interpretation",
        "industry_macro_context",
        "risk_points",
        "data_gaps_that_matter",
        "tracking_indicators",
        "cannot_conclude_yet",
    ]
    assert all(section["summary_points"] for section in compact["section_summaries"])


def test_compact_response_includes_labels_used_tracking_and_cannot_conclude():
    compact = build_a_share_fundamental_skill_response(_request())["compact_response"]

    assert compact["labels_used"]
    assert "\u5f85\u6838\u9a8c" in compact["labels_used"]
    assert compact["tracking_indicators"]
    assert compact["cannot_conclude_yet"]


def test_compact_response_does_not_include_backend_grounding_summary():
    compact = build_a_share_fundamental_skill_response(_request())["compact_response"]
    serialized = json.dumps(compact, ensure_ascii=False)

    assert "backend_grounding_summary" not in serialized


def test_compact_response_does_not_include_backend_trace_fields():
    compact = build_a_share_fundamental_skill_response(_request())["compact_response"]
    serialized = json.dumps(compact, ensure_ascii=False)

    for forbidden in ("page_number", "snippet", "source_url", "sha256", "cache_path"):
        assert forbidden not in serialized


def test_output_mode_with_compatibility_payload_returns_payload():
    response = build_a_share_fundamental_skill_response(
        _request(
            output_mode=OUTPUT_MODE_COMPACT_BRIEF_AND_REPORT_V1_COMPATIBILITY_PAYLOAD
        )
    )

    assert response["readiness"]["has_report_v1_compatibility_payload"] is True
    assert response["report_v1_compatibility_payload"]["schema_version"] == (
        "analysis_brief_report_v1_compatibility_payload.v1"
    )


def test_output_mode_compact_brief_does_not_return_compatibility_payload():
    response = build_a_share_fundamental_skill_response(_request())

    assert response["readiness"]["has_report_v1_compatibility_payload"] is False
    assert response["report_v1_compatibility_payload"] is None


def test_ticker_only_professional_brief_with_injected_fake_client_returns_ready():
    response = _ticker_build()

    assert response["readiness"]["status"] == SKILL_READINESS_READY
    assert response["readiness"]["input_mode"] == INPUT_MODE_TICKER_ONLY_PROFESSIONAL_BRIEF
    assert response["readiness"]["has_professional_compact_brief"] is True
    assert response["compact_response"] is None
    assert response["user_facing_analysis_brief"] is None
    assert response["professional_compact_brief"]["stock_code"] == "600406"


def test_ticker_only_professional_brief_returns_required_professional_sections():
    brief = _ticker_build()["professional_compact_brief"]

    for key in PROFESSIONAL_BRIEF_SECTION_KEYS:
        assert key in brief
    assert brief["overall_view"]["view"]
    assert brief["business_view"]["view"]
    assert brief["financial_view"]["view"]
    assert brief["operating_quality_view"]["view"]
    assert brief["industry_macro_view"]["view"]
    assert brief["risk_view"]["view"]
    assert brief["key_variables"]
    assert brief["conclusion_boundary"]
    assert brief["source_note"] == "数据来源：Tushare。"


def test_ticker_only_professional_brief_does_not_return_provider_bundle_by_default():
    response = _ticker_build()
    serialized = json.dumps(response, ensure_ascii=False)

    assert "provider_candidate_bundle" not in response
    assert response["professional_internal_payload"] is None
    assert "candidate_items" not in serialized


def test_ticker_only_internal_payload_output_returns_sanitized_payload():
    response = _ticker_build(
        output_mode=OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF_AND_INTERNAL_PAYLOAD
    )

    assert response["readiness"]["status"] == SKILL_READINESS_READY
    assert response["readiness"]["has_professional_internal_payload"] is True
    assert response["professional_internal_payload"]["provider_candidate_count"] > 0
    assert "candidate_items" not in json.dumps(
        response["professional_internal_payload"],
        ensure_ascii=False,
    )


def test_ticker_only_professional_output_does_not_return_internal_payload():
    response = _ticker_build(output_mode=OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF)

    assert response["readiness"]["has_professional_internal_payload"] is False
    assert response["professional_internal_payload"] is None


def test_ticker_only_with_no_stock_code_or_ts_code_returns_blocked():
    response = _ticker_build(stock_code=None, ts_code=None)

    assert response["readiness"]["status"] == SKILL_READINESS_BLOCKED
    assert response["readiness"]["missing_required_inputs"] == ["stock_code_or_ts_code"]
    assert response["professional_compact_brief"] is None
    assert response["blocked_reasons"][0]["reason"] == "ticker_identity_required"


def test_ticker_only_with_missing_tushare_client_mode_returns_blocked():
    request = _ticker_request()
    request.pop("tushare_client_mode")

    response = build_a_share_fundamental_skill_response(request)

    assert response["readiness"]["status"] == SKILL_READINESS_BLOCKED
    assert response["readiness"]["missing_required_inputs"] == ["tushare_client_mode"]
    assert response["professional_compact_brief"] is None
    assert response["blocked_reasons"][0]["reason"] == "tushare_client_mode_required"


def test_ticker_only_injected_mode_without_client_returns_blocked():
    response = build_a_share_fundamental_skill_response(_ticker_request())

    assert response["readiness"]["status"] == SKILL_READINESS_BLOCKED
    assert response["professional_compact_brief"] is None
    assert response["blocked_reasons"][0]["reason"] == "injected_tushare_client_required"


def test_ticker_only_fake_mode_without_injected_client_returns_ready_without_network():
    response = build_a_share_fundamental_skill_response(
        _ticker_request(tushare_client_mode=TUSHARE_CLIENT_MODE_FAKE)
    )

    assert response["readiness"]["status"] == SKILL_READINESS_READY
    assert response["request_summary"]["allow_network"] is False
    assert response["professional_compact_brief"]["source_note"] == "数据来源：Tushare。"


def test_ticker_only_env_live_with_allow_network_false_returns_blocked():
    response = build_a_share_fundamental_skill_response(
        _ticker_request(
            tushare_client_mode=TUSHARE_CLIENT_MODE_ENV_LIVE,
            allow_network=False,
        )
    )

    assert response["readiness"]["status"] == SKILL_READINESS_BLOCKED
    assert response["professional_compact_brief"] is None
    assert response["blocked_reasons"][0]["reason"] == "network_not_allowed_for_env_live"


def test_ticker_only_request_returns_blocked_readiness_without_builder_call(monkeypatch):
    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("builder should not be called")

    monkeypatch.setattr(wrapper, "build_user_facing_analysis_brief", fail_if_called)
    request = _request(user_facing_analysis_brief=None)

    response = build_a_share_fundamental_skill_response(request)

    assert response["readiness"]["status"] == SKILL_READINESS_BLOCKED
    assert response["readiness"]["required_inputs_present"] is False
    assert response["blocked_reasons"][0]["reason"] == (
        BLOCKED_REASON_VALIDATED_ANALYSIS_INPUT_REQUIRED
    )
    assert response["compact_response"] is None


@pytest.mark.parametrize(
    ("key", "value"),
    [("allow_network", True), ("allow_file_writes", True)],
)
def test_disallowed_capability_flags_rejected(key, value):
    with pytest.raises(AShareFundamentalSkillWrapperError, match=key):
        build_a_share_fundamental_skill_response(_request(**{key: value}))


def test_allow_network_true_rejected_for_old_orchestration_result_mode():
    with pytest.raises(AShareFundamentalSkillWrapperError, match="allow_network"):
        build_a_share_fundamental_skill_response(
            _request(
                input_mode=INPUT_MODE_ORCHESTRATION_RESULT,
                user_facing_analysis_brief=None,
                orchestration_result=_sample_orchestration_result(),
                allow_network=True,
            )
        )


def test_unsupported_input_mode_rejected():
    with pytest.raises(AShareFundamentalSkillWrapperError, match="input_mode"):
        build_a_share_fundamental_skill_response(_request(input_mode="ticker_only_live"))


def test_unsupported_output_mode_rejected():
    with pytest.raises(AShareFundamentalSkillWrapperError, match="output_mode"):
        build_a_share_fundamental_skill_response(_request(output_mode="html_artifact"))


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("raw_tushare_provider_result", {"provider": "Tushare"}),
        ("raw_provider_queue", [{"metric": "x"}]),
        ("raw_http_response", {"body": "x"}),
        ("pdf_bytes", b"%PDF-1.7"),
        ("arbitrary_url", "https://example.com/report.pdf"),
        ("output_artifact_path", "output/report.json"),
    ],
)
def test_raw_inputs_rejected(key, value):
    request = _request()
    request[key] = value

    with pytest.raises(AShareFundamentalSkillWrapperError, match="raw|unsupported"):
        build_a_share_fundamental_skill_response(request)


def test_no_report_v1_builder_or_html_renderer_call_surface():
    response = build_a_share_fundamental_skill_response(_request())
    serialized = json.dumps(response, ensure_ascii=False)

    assert response["readiness"]["has_report_v1_artifact"] is False
    assert response["readiness"]["has_html_artifact"] is False
    assert "Report V1 artifact" not in serialized
    assert "HTML artifact" not in serialized


def test_no_output_fixture_or_manifest_write(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    response = build_a_share_fundamental_skill_response(_request())

    assert response["readiness"]["status"] == SKILL_READINESS_READY
    assert not (tmp_path / "output").exists()
    assert not (tmp_path / "fixtures").exists()
    assert not (tmp_path / "accepted_manifest.json").exists()


def test_ticker_only_no_output_fixture_or_manifest_write(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    response = _ticker_build()

    assert response["readiness"]["status"] == SKILL_READINESS_READY
    assert not (tmp_path / "output").exists()
    assert not (tmp_path / "fixtures").exists()
    assert not (tmp_path / "accepted_manifest.json").exists()


def test_input_request_not_mutated():
    request = _request(
        output_mode=OUTPUT_MODE_COMPACT_BRIEF_AND_REPORT_V1_COMPATIBILITY_PAYLOAD
    )
    before = copy.deepcopy(request)

    build_a_share_fundamental_skill_response(request)

    assert request == before


def test_ticker_only_input_request_not_mutated():
    request = _ticker_request(
        output_mode=OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF_AND_INTERNAL_PAYLOAD
    )
    before = copy.deepcopy(request)

    build_a_share_fundamental_skill_response(
        request,
        tushare_client=_FakeFinancialClient(),
    )

    assert request == before


def test_non_600406_brief_sample_passes():
    brief = _sample_brief()
    brief["stock_code"] = "000001"
    brief["ts_code"] = "000001.SZ"
    brief["company_name_hint"] = "Ping An Bank"

    response = build_a_share_fundamental_skill_response(
        _request(
            stock_code="000001",
            ts_code="000001.SZ",
            company_name_hint="Ping An Bank",
            user_facing_analysis_brief=brief,
        )
    )

    assert response["readiness"]["status"] == SKILL_READINESS_READY
    assert response["compact_response"]["stock_code"] == "000001"
    assert response["compact_response"]["ts_code"] == "000001.SZ"


def test_non_600406_ticker_only_sample_passes_with_injected_fake_client():
    response = _ticker_build(
        _FakeFinancialClient(ts_code="000001.SZ"),
        stock_code="000001",
        ts_code="000001.SZ",
        company_name_hint="Ping An Bank",
    )

    assert response["readiness"]["status"] == SKILL_READINESS_READY
    assert response["professional_compact_brief"]["stock_code"] == "000001"
    assert response["professional_compact_brief"]["ts_code"] == "000001.SZ"


def test_no_trading_advice_target_position_or_technical_signal():
    response = build_a_share_fundamental_skill_response(_request())
    serialized = json.dumps(response["compact_response"], ensure_ascii=False).casefold()

    for forbidden in (
        "target price",
        "portfolio",
        "position",
        "technical signal",
        "trading advice",
        "\u76ee\u6807\u4ef7",
        "\u4ed3\u4f4d",
        "\u6280\u672f\u4fe1\u53f7",
    ):
        assert forbidden.casefold() not in serialized
