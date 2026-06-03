# -*- coding: utf-8 -*-

from __future__ import annotations

import copy
import json

import pytest

from src.fundamental_skill.research_planning.a_share_fundamental_skill_wrapper import (
    A_SHARE_FUNDAMENTAL_SKILL_REQUEST_SCHEMA_VERSION,
    INPUT_MODE_TICKER_ONLY_PROFESSIONAL_BRIEF,
    OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF,
    TUSHARE_CLIENT_MODE_ENV_LIVE,
    TUSHARE_CLIENT_MODE_INJECTED,
    INPUT_MODE_ORCHESTRATION_RESULT,
    AShareFundamentalSkillWrapperError,
    assert_no_a_share_fundamental_skill_wrapper_forbidden_markers,
    build_a_share_fundamental_skill_response,
)
from tests.test_controlled_real_tushare_professional_compact_brief_pilot import (
    _FakeFinancialClient,
)
from tests.test_user_facing_analysis_brief import (
    _brief,
    _locator_result,
    _orchestration_result,
)


_SAMPLE_BRIEF = None
_SAMPLE_ORCHESTRATION_RESULT = None
_SAMPLE_LOCATOR_RESULT = None


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


def _sample_locator_result():
    global _SAMPLE_LOCATOR_RESULT
    if _SAMPLE_LOCATOR_RESULT is None:
        _SAMPLE_LOCATOR_RESULT = _locator_result()
    return copy.deepcopy(_SAMPLE_LOCATOR_RESULT)


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


def _ticker_build(**overrides):
    request = _ticker_request(**overrides)
    return build_a_share_fundamental_skill_response(
        request,
        tushare_client=_FakeFinancialClient(ts_code=request["ts_code"]),
    )


@pytest.mark.parametrize("marker", ["token", "api_token", "Bearer abcdefghijk"])
def test_token_marker_rejected(marker):
    with pytest.raises(AShareFundamentalSkillWrapperError, match="forbidden|token"):
        assert_no_a_share_fundamental_skill_wrapper_forbidden_markers(
            {"nested": [{"marker": marker}]}
        )


def test_dotenv_marker_rejected():
    with pytest.raises(AShareFundamentalSkillWrapperError, match="forbidden"):
        assert_no_a_share_fundamental_skill_wrapper_forbidden_markers(
            {"marker": "read .env file"}
        )


def test_tushare_token_marker_rejected():
    with pytest.raises(AShareFundamentalSkillWrapperError, match="forbidden"):
        assert_no_a_share_fundamental_skill_wrapper_forbidden_markers(
            {"marker": "tushare_token"}
        )


def test_token_field_rejected_in_ticker_only_request():
    request = _ticker_request()
    request["token"] = "not-allowed"

    with pytest.raises(AShareFundamentalSkillWrapperError, match="unsupported|token"):
        build_a_share_fundamental_skill_response(
            request,
            tushare_client=_FakeFinancialClient(),
        )


def test_token_like_string_rejected_in_ticker_only_request():
    with pytest.raises(
        AShareFundamentalSkillWrapperError,
        match="token_like_string|forbidden",
    ):
        build_a_share_fundamental_skill_response(
            _ticker_request(company_name_hint="Bearer abcdefghijk"),
            tushare_client=_FakeFinancialClient(),
        )


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("tushare_token", "not-allowed"),
        ("env_file", ".env"),
        ("raw_provider_queue", [{"metric": "x"}]),
        ("raw_tushare_provider_result", {"rows": []}),
        ("pdf_bytes", b"%PDF-1.7"),
        ("output_artifact_path", "output/report.json"),
        ("fixture_path", "fixtures/sample.json"),
        ("accepted_manifest_path", "accepted_manifest.json"),
    ],
)
def test_raw_secret_file_and_manifest_inputs_rejected_in_ticker_only_request(key, value):
    request = _ticker_request()
    request[key] = value

    with pytest.raises(
        AShareFundamentalSkillWrapperError,
        match="raw|unsupported|forbidden",
    ):
        build_a_share_fundamental_skill_response(
            request,
            tushare_client=_FakeFinancialClient(),
        )


@pytest.mark.parametrize("marker", ["official_metric_fact", "provider_official_conflict"])
def test_official_fact_and_conflict_markers_rejected(marker):
    with pytest.raises(AShareFundamentalSkillWrapperError, match="forbidden"):
        assert_no_a_share_fundamental_skill_wrapper_forbidden_markers({"marker": marker})


@pytest.mark.parametrize("marker", ["Report V1 artifact", "HTML artifact"])
def test_report_v1_and_html_artifact_markers_rejected(marker):
    with pytest.raises(AShareFundamentalSkillWrapperError, match="forbidden"):
        assert_no_a_share_fundamental_skill_wrapper_forbidden_markers({"marker": marker})


@pytest.mark.parametrize(
    "marker",
    ["accepted manifest write", "output baseline write", "fixture write"],
)
def test_accepted_manifest_output_baseline_fixture_write_rejected(marker):
    with pytest.raises(AShareFundamentalSkillWrapperError, match="forbidden"):
        assert_no_a_share_fundamental_skill_wrapper_forbidden_markers({"marker": marker})


@pytest.mark.parametrize(
    "marker",
    ["page_number", "snippet", "source_url", "sha256", "cache_path"],
)
def test_backend_trace_markers_rejected(marker):
    with pytest.raises(AShareFundamentalSkillWrapperError, match="forbidden"):
        assert_no_a_share_fundamental_skill_wrapper_forbidden_markers({marker: "leak"})


@pytest.mark.parametrize("marker", ["output artifact path", "fixture path"])
def test_output_artifact_path_and_fixture_path_rejected(marker):
    with pytest.raises(AShareFundamentalSkillWrapperError, match="forbidden"):
        assert_no_a_share_fundamental_skill_wrapper_forbidden_markers({"marker": marker})


@pytest.mark.parametrize(
    "marker",
    ["OCR", "table extraction", "table extractor", "metric extraction"],
)
def test_ocr_table_and_metric_extraction_markers_rejected(marker):
    with pytest.raises(AShareFundamentalSkillWrapperError, match="forbidden"):
        assert_no_a_share_fundamental_skill_wrapper_forbidden_markers({"marker": marker})


def test_provider_official_reconciliation_rejected():
    with pytest.raises(AShareFundamentalSkillWrapperError, match="forbidden"):
        assert_no_a_share_fundamental_skill_wrapper_forbidden_markers(
            {"marker": "provider-official reconciliation"}
        )


@pytest.mark.parametrize("marker", ["live Tushare", "live provider", "live CNInfo"])
def test_live_provider_markers_rejected(marker):
    with pytest.raises(AShareFundamentalSkillWrapperError, match="forbidden"):
        assert_no_a_share_fundamental_skill_wrapper_forbidden_markers({"marker": marker})


@pytest.mark.parametrize(
    "marker",
    [
        "buy",
        "sell",
        "hold",
        "target price",
        "portfolio",
        "position",
        "technical signal",
        "trading advice",
        "investment advice",
    ],
)
def test_trading_markers_rejected(marker):
    with pytest.raises(AShareFundamentalSkillWrapperError, match="forbidden"):
        assert_no_a_share_fundamental_skill_wrapper_forbidden_markers({"marker": marker})


@pytest.mark.parametrize(
    "marker",
    [
        "\u4e70\u5165",
        "\u5356\u51fa",
        "\u6301\u6709",
        "\u76ee\u6807\u4ef7",
        "\u4ed3\u4f4d",
        "\u7ec4\u5408",
        "\u6280\u672f\u4fe1\u53f7",
        "\u6295\u8d44\u5efa\u8bae",
        "\u6b63\u5f0f\u7814\u62a5",
        "\u8f93\u51fa\u57fa\u7ebf",
        "\u5199\u5165fixture",
        "\u5199\u5165accepted manifest",
        "\u8bfb\u53d6token",
        "\u8bfb\u53d6.env",
        "\u8bfb\u53d6tushare_token",
        "OCR",
        "\u8868\u683c\u62bd\u53d6",
        "\u8868\u683c\u89e3\u6790",
        "\u6307\u6807\u62bd\u53d6",
        "\u5b98\u65b9\u6307\u6807\u4e8b\u5b9e",
        "\u6307\u6807\u6838\u9a8c",
        "\u4e00\u81f4\u6027\u6838\u9a8c",
        "\u884c\u4e1a\u666f\u6c14",
        "\u5b8f\u89c2\u5229\u597d",
        "\u516c\u53f8\u53d7\u76ca",
        "\u6838\u5fc3\u6295\u8d44\u903b\u8f91\u6210\u7acb",
        "\u7b2c\u51e0\u9875",
        "\u9875\u7801",
        "\u539f\u6587\u7247\u6bb5",
        "\u6765\u6e90\u94fe\u63a5",
        "\u54c8\u5e0c",
        "\u7f13\u5b58\u8def\u5f84",
    ],
)
def test_chinese_forbidden_markers_rejected(marker):
    with pytest.raises(AShareFundamentalSkillWrapperError, match="forbidden"):
        assert_no_a_share_fundamental_skill_wrapper_forbidden_markers({"marker": marker})


def test_verified_fact_rejected():
    with pytest.raises(AShareFundamentalSkillWrapperError, match="forbidden"):
        assert_no_a_share_fundamental_skill_wrapper_forbidden_markers(
            {"marker": "verified_fact"}
        )


def test_controlled_policy_keys_are_allowed():
    assert_no_a_share_fundamental_skill_wrapper_forbidden_markers(
        {
            "not_for_trading_advice": True,
            "not_official_verified": True,
            "official_verified_count": 0,
            "has_report_v1_artifact": False,
            "has_html_artifact": False,
            "has_trading_advice": False,
            "boundary": "\u5b98\u65b9\u6307\u6807\u6838\u9a8c\u5c1a\u672a\u5b8c\u6210",
        }
    )


def test_backend_trace_cannot_leak_into_compact_response():
    request = {
        "schema_version": A_SHARE_FUNDAMENTAL_SKILL_REQUEST_SCHEMA_VERSION,
        "stock_code": "600406",
        "ts_code": "600406.SH",
        "company_name_hint": "Guodian NARI",
        "input_mode": INPUT_MODE_ORCHESTRATION_RESULT,
        "orchestration_result": _sample_orchestration_result(),
        "locator_result": _sample_locator_result(),
        "allow_network": False,
        "allow_file_writes": False,
        "not_for_trading_advice": True,
    }

    response = build_a_share_fundamental_skill_response(request)
    serialized = json.dumps(response["compact_response"], ensure_ascii=False)

    for forbidden in (
        "page_number",
        "snippet",
        "source_url",
        "sha256",
        "cache_path",
        "safe locator hint",
        "https://static.cninfo.com.cn",
        "a" * 64,
    ):
        assert forbidden not in serialized


def test_professional_compact_brief_does_not_expose_engineering_labels():
    text = json.dumps(
        _ticker_build()["professional_compact_brief"],
        ensure_ascii=False,
    )

    for forbidden in (
        "provider_candidate",
        "pending_official_verification",
        "official verification",
        "official_verified_count",
        "provider",
        "候选数据",
        "证据状态",
        "待核验",
        "数据缺口",
        "推理",
        "官方核验",
    ):
        assert forbidden not in text


def test_professional_compact_brief_does_not_expose_backend_trace():
    text = json.dumps(
        _ticker_build()["professional_compact_brief"],
        ensure_ascii=False,
    )

    for forbidden in (
        "page_number",
        "snippet",
        "source_url",
        "sha256",
        "cache_path",
        "backend trace",
        "anchor map",
        "candidate_items",
    ):
        assert forbidden not in text


def test_professional_compact_brief_does_not_shift_judgment_to_user():
    text = json.dumps(
        _ticker_build()["professional_compact_brief"],
        ensure_ascii=False,
    )

    for forbidden in ("用户自行", "自行判断", "自行跟踪", "需要用户", "建议用户", "请结合"):
        assert forbidden not in text


def test_professional_compact_brief_has_no_trading_signal_or_action():
    text = json.dumps(
        _ticker_build()["professional_compact_brief"],
        ensure_ascii=False,
    ).casefold()

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


def test_no_token_appears_in_result_or_captured_output(capsys):
    request = {
        "schema_version": A_SHARE_FUNDAMENTAL_SKILL_REQUEST_SCHEMA_VERSION,
        "stock_code": "600406",
        "ts_code": "600406.SH",
        "company_name_hint": "Guodian NARI",
        "user_facing_analysis_brief": _sample_brief(),
        "allow_network": False,
        "allow_file_writes": False,
        "not_for_trading_advice": True,
    }

    response = build_a_share_fundamental_skill_response(request)
    captured = capsys.readouterr()
    serialized = json.dumps(response, ensure_ascii=False).casefold()

    assert "token" not in captured.out.casefold()
    assert "token" not in captured.err.casefold()
    assert "token" not in serialized


def test_env_live_blocked_result_does_not_print_or_return_token(monkeypatch, capsys):
    secret = "S3cr3tValueThatShouldStayHidden123456789"
    monkeypatch.setenv("TUSHARE_" + "TOKEN", secret)

    response = build_a_share_fundamental_skill_response(
        _ticker_request(
            tushare_client_mode=TUSHARE_CLIENT_MODE_ENV_LIVE,
            allow_network=False,
        )
    )
    captured = capsys.readouterr()
    serialized = json.dumps(response, ensure_ascii=False)

    assert response["readiness"]["status"] in {"blocked", "skipped"}
    assert secret not in captured.out
    assert secret not in captured.err
    assert secret not in serialized
    assert "token" not in captured.out.casefold()
    assert "token" not in captured.err.casefold()
