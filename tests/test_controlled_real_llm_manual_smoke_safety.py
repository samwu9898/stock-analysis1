# -*- coding: utf-8 -*-

from __future__ import annotations

import copy
import json

import pytest

import src.fundamental_skill.research_planning.controlled_real_llm_manual_smoke as smoke_module
from src.fundamental_skill.research_planning.controlled_real_llm_manual_smoke import (
    CONTROLLED_REAL_LLM_MANUAL_SMOKE_REQUEST_SCHEMA_VERSION,
    ControlledRealLLMManualSmokeError,
    assert_no_real_llm_frontstage_leak,
    assert_no_real_llm_smoke_forbidden_markers,
    build_controlled_real_llm_manual_smoke_result,
    validate_controlled_real_llm_manual_smoke_request,
    validate_controlled_real_llm_manual_smoke_result,
)
from src.fundamental_skill.research_planning.controlled_real_tushare_professional_compact_brief_pilot import (
    TUSHARE_CLIENT_MODE_INJECTED,
)
from tests.test_controlled_real_tushare_professional_compact_brief_pilot import (
    _FakeFinancialClient,
)


def _request(**overrides):
    request = {
        "schema_version": CONTROLLED_REAL_LLM_MANUAL_SMOKE_REQUEST_SCHEMA_VERSION,
        "stock_code": "600406",
        "ts_code": "600406.SH",
        "company_name_hint": "Guodian NARI",
        "periods": ["20251231"],
        "llm_provider": "deepseek",
        "llm_client_mode": "fake",
        "allow_network": False,
        "allow_file_writes": False,
        "not_for_trading_advice": True,
        "tushare_client_mode": TUSHARE_CLIENT_MODE_INJECTED,
        "allow_tushare_network": False,
        "include_professional_compact_brief_preview": True,
    }
    request.update(overrides)
    return request


def _ready_result():
    return build_controlled_real_llm_manual_smoke_result(
        _request(),
        tushare_client=_FakeFinancialClient(),
    )


def _assert_request_rejected(**overrides):
    with pytest.raises(ControlledRealLLMManualSmokeError):
        validate_controlled_real_llm_manual_smoke_request(_request(**overrides))


@pytest.mark.parametrize("field", ["token", "api_key"])
def test_request_token_or_api_key_field_rejected(field):
    _assert_request_rejected(**{field: "value"})


@pytest.mark.parametrize(
    "marker",
    [".env", "key file", "credential file"],
)
def test_request_env_or_key_file_markers_rejected(marker):
    _assert_request_rejected(company_name_hint=marker)


def test_request_tushare_token_marker_rejected():
    _assert_request_rejected(company_name_hint="tushare_token.txt")


@pytest.mark.parametrize(
    "field",
    ["raw_provider_bundle", "raw_provider_rows", "candidate_items"],
)
def test_raw_provider_bundle_rows_and_candidate_items_rejected(field):
    _assert_request_rejected(**{field: []})


@pytest.mark.parametrize(
    "field",
    ["source_url", "page_number", "snippet", "sha256", "cache_path"],
)
def test_source_locator_and_cache_markers_rejected(field):
    _assert_request_rejected(**{field: "unsafe"})


@pytest.mark.parametrize(
    "field",
    ["output_path", "fixture_path", "accepted_manifest_path"],
)
def test_output_fixture_and_manifest_path_rejected(field):
    _assert_request_rejected(**{field: "unsafe"})


def test_prompt_or_result_cannot_contain_backend_trace():
    with pytest.raises(ControlledRealLLMManualSmokeError):
        assert_no_real_llm_smoke_forbidden_markers({"note": "backend trace"})


def test_prompt_or_result_cannot_contain_token_like_string():
    with pytest.raises(ControlledRealLLMManualSmokeError):
        assert_no_real_llm_smoke_forbidden_markers(
            {"note": "sk-ThisLooksLikeASecretValue123456789"}
        )


@pytest.mark.parametrize(
    "marker",
    ["provider_candidate", "pending verification"],
)
def test_professional_preview_cannot_contain_provider_candidate_or_pending(marker):
    with pytest.raises(ControlledRealLLMManualSmokeError):
        assert_no_real_llm_frontstage_leak({"view": marker})


@pytest.mark.parametrize(
    "marker",
    [
        "\u5f85\u6838\u9a8c",
        "\u6570\u636e\u7f3a\u53e3",
        "\u63a8\u7406",
    ],
)
def test_professional_preview_cannot_contain_verification_gap_or_inference(marker):
    with pytest.raises(ControlledRealLLMManualSmokeError):
        assert_no_real_llm_frontstage_leak({"view": marker})


@pytest.mark.parametrize(
    "marker",
    [
        "\u7528\u6237\u81ea\u884c",
        "\u81ea\u884c\u5224\u65ad",
        "\u81ea\u884c\u8ddf\u8e2a",
        "\u9700\u8981\u7528\u6237",
        "\u5efa\u8bae\u7528\u6237",
    ],
)
def test_professional_preview_cannot_shift_responsibility_to_user(marker):
    with pytest.raises(ControlledRealLLMManualSmokeError):
        assert_no_real_llm_frontstage_leak({"view": marker})


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
        "\u4e70\u5165",
        "\u5356\u51fa",
        "\u6301\u6709",
        "\u76ee\u6807\u4ef7",
        "\u4ed3\u4f4d",
        "\u6280\u672f\u4fe1\u53f7",
    ],
)
def test_professional_preview_cannot_contain_trading_actions(marker):
    with pytest.raises(ControlledRealLLMManualSmokeError):
        assert_no_real_llm_frontstage_leak({"view": marker})


def test_result_cannot_include_raw_llm_response():
    result = _ready_result()
    unsafe = copy.deepcopy(result)
    unsafe["raw_llm_response"] = "raw"

    with pytest.raises(ControlledRealLLMManualSmokeError):
        validate_controlled_real_llm_manual_smoke_result(unsafe)


def test_result_cannot_include_backend_trace_marker():
    result = _ready_result()
    unsafe = copy.deepcopy(result)
    unsafe["quality_check_summary"]["issue_ids"].append("backend_trace")

    with pytest.raises(ControlledRealLLMManualSmokeError):
        validate_controlled_real_llm_manual_smoke_result(unsafe)


def test_no_key_appears_in_result_or_captured_output(monkeypatch, capsys):
    secret = "S3cr3tValueThatShouldStayHidden123456789"
    monkeypatch.setenv("DEEPSEEK_API_KEY", secret)

    def fake_import(name):
        if name == "openai":
            raise ModuleNotFoundError(name)
        return __import__(name)

    monkeypatch.setattr(smoke_module.importlib, "import_module", fake_import)
    result = build_controlled_real_llm_manual_smoke_result(
        _request(llm_client_mode="env_live", allow_network=True),
        tushare_client=_FakeFinancialClient(),
    )
    captured = capsys.readouterr()

    assert result["readiness"]["status"] == "skipped"
    assert secret not in json.dumps(result, ensure_ascii=False)
    assert secret not in captured.out
    assert secret not in captured.err


def test_ready_result_excludes_raw_prompt_provider_bundle_and_trace():
    result = _ready_result()
    text = json.dumps(result, ensure_ascii=False).casefold()

    for forbidden in (
        "raw_prompt",
        "raw_response",
        "provider_candidate_bundle",
        "candidate_items",
        "backend trace",
        "source_url",
        "cache_path",
    ):
        assert forbidden not in text

