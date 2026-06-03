# -*- coding: utf-8 -*-

from __future__ import annotations

import copy
import json

import pytest

import src.fundamental_skill.research_planning.controlled_real_llm_manual_smoke as smoke_module
from src.fundamental_skill.research_planning.controlled_real_llm_manual_smoke import (
    CONTROLLED_REAL_LLM_MANUAL_SMOKE_REQUEST_SCHEMA_VERSION,
    CONTROLLED_REAL_LLM_MANUAL_SMOKE_RESULT_SCHEMA_VERSION,
    LLM_CLIENT_MODE_ENV_LIVE,
    LLM_CLIENT_MODE_FAKE,
    LLM_CLIENT_MODE_INJECTED,
    LLM_PROVIDER_DEEPSEEK,
    READINESS_BLOCKED,
    READINESS_READY,
    READINESS_SKIPPED,
    build_controlled_real_llm_manual_smoke_result,
    build_real_llm_prompt_from_model_facing_context,
    parse_real_llm_renderer_output,
    validate_real_llm_renderer_output,
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
        "llm_provider": LLM_PROVIDER_DEEPSEEK,
        "llm_client_mode": LLM_CLIENT_MODE_FAKE,
        "allow_network": False,
        "allow_file_writes": False,
        "not_for_trading_advice": True,
        "tushare_client_mode": TUSHARE_CLIENT_MODE_INJECTED,
        "allow_tushare_network": False,
        "include_professional_compact_brief_preview": True,
    }
    request.update(overrides)
    return request


def _valid_llm_output(**overrides):
    output = {
        "overall_view": (
            "Company quality analysis stays inside revenue profit cashflow "
            "and balance-sheet links, with no action language."
        ),
        "business_view": (
            "Business analysis focuses on delivery rhythm, customer payment "
            "cycle, margin transmission, and durable operating structure."
        ),
        "financial_view": (
            "Financial analysis compares revenue, profit, margin quality, "
            "capital efficiency, and balance-sheet pressure together."
        ),
        "operating_quality_view": (
            "Operating quality analysis links profit conversion, operating "
            "cashflow, receivables discipline, and working-capital efficiency."
        ),
        "industry_macro_view": (
            "Industry and macro variables matter only when they transmit into "
            "orders, delivery, cash collection, or margin structure."
        ),
        "risk_view": (
            "Core risk analysis watches mismatches among revenue, profit, "
            "cashflow, receivables, leverage, and external demand rhythm."
        ),
        "key_variables": [
            "revenue profit consistency",
            "profit cashflow conversion",
            "receivables collection quality",
            "margin structure",
            "balance sheet pressure",
        ],
        "conclusion_boundary": (
            "The conclusion stays inside fundamental quality and operating "
            "resilience analysis."
        ),
        "source_note": "Tushare source note for fundamental quality only.",
        "not_for_trading_advice": True,
    }
    output.update(overrides)
    return output


def _build(*, request=None, tushare_client=None, llm_client=None):
    active_request = request or _request()
    return build_controlled_real_llm_manual_smoke_result(
        active_request,
        tushare_client=tushare_client
        or _FakeFinancialClient(ts_code=active_request["ts_code"]),
        llm_client=llm_client,
    )


def _serialized(value):
    return json.dumps(value, ensure_ascii=False)


class _InjectedLLMClient:
    def __init__(self, response=None):
        self.response = response or json.dumps(_valid_llm_output(), ensure_ascii=False)
        self.calls = []

    def complete(self, *, prompt, model_context):
        self.calls.append(
            {
                "prompt": prompt,
                "model_context": copy.deepcopy(model_context),
            }
        )
        return self.response


class _RaisingLLMClient:
    def __init__(self, status_code):
        self.status_code = status_code

    def complete(self, *, prompt, model_context):
        del prompt, model_context
        raise _HTTPStatusError(self.status_code)


class _HTTPStatusError(RuntimeError):
    def __init__(self, status_code):
        super().__init__(f"safe status {status_code}")
        self.status_code = status_code


def test_fake_llm_client_returns_ready_smoke_result():
    result = _build()

    assert result["schema_version"] == CONTROLLED_REAL_LLM_MANUAL_SMOKE_RESULT_SCHEMA_VERSION
    assert result["smoke_status"] == READINESS_READY
    assert result["readiness"]["status"] == READINESS_READY
    assert result["llm_provider"] == LLM_PROVIDER_DEEPSEEK
    assert result["professional_compact_brief_preview"]
    assert result["quality_check_summary"]["overall_status"]
    assert result["not_for_trading_advice"] is True


def test_injected_llm_client_returns_ready_smoke_result():
    client = _InjectedLLMClient()
    result = _build(
        request=_request(llm_client_mode=LLM_CLIENT_MODE_INJECTED),
        llm_client=client,
    )

    assert result["readiness"]["status"] == READINESS_READY
    assert client.calls
    assert result["professional_compact_brief_preview"]["not_for_trading_advice"] is True


def test_env_live_missing_deepseek_api_key_returns_skipped(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    result = _build(
        request=_request(
            llm_client_mode=LLM_CLIENT_MODE_ENV_LIVE,
            allow_network=True,
        )
    )

    assert result["readiness"]["status"] == READINESS_SKIPPED
    assert result["blocked_reasons"] == ["deepseek_api_key_missing"]
    assert result["professional_compact_brief_preview"] is None


def test_env_live_missing_openai_sdk_returns_skipped(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "present-but-not-returned")

    def fake_import(name):
        if name == "openai":
            raise ModuleNotFoundError(name)
        return __import__(name)

    monkeypatch.setattr(smoke_module.importlib, "import_module", fake_import)

    result = _build(
        request=_request(
            llm_client_mode=LLM_CLIENT_MODE_ENV_LIVE,
            allow_network=True,
        )
    )

    assert result["readiness"]["status"] == READINESS_SKIPPED
    assert result["blocked_reasons"] == ["deepseek_sdk_unavailable"]


def test_env_live_insufficient_balance_402_returns_skipped(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "present-but-not-returned")
    monkeypatch.setattr(
        smoke_module,
        "build_deepseek_manual_smoke_client_from_env",
        lambda: _RaisingLLMClient(402),
    )

    result = _build(
        request=_request(
            llm_client_mode=LLM_CLIENT_MODE_ENV_LIVE,
            allow_network=True,
        )
    )

    assert result["readiness"]["status"] == READINESS_SKIPPED
    assert result["blocked_reasons"] == ["deepseek_insufficient_balance"]


def test_env_live_auth_error_returns_safe_skip_without_key(monkeypatch):
    secret = "S3cr3tValueThatShouldStayHidden123456789"
    monkeypatch.setenv("DEEPSEEK_API_KEY", secret)
    monkeypatch.setattr(
        smoke_module,
        "build_deepseek_manual_smoke_client_from_env",
        lambda: _RaisingLLMClient(401),
    )

    result = _build(
        request=_request(
            llm_client_mode=LLM_CLIENT_MODE_ENV_LIVE,
            allow_network=True,
        )
    )

    text = _serialized(result)
    assert result["readiness"]["status"] == READINESS_SKIPPED
    assert result["blocked_reasons"] == ["deepseek_auth_failed"]
    assert secret not in text


def test_invalid_json_output_blocked():
    result = _build(
        request=_request(llm_client_mode=LLM_CLIENT_MODE_INJECTED),
        llm_client=_InjectedLLMClient("{not json"),
    )

    assert result["readiness"]["status"] == READINESS_BLOCKED
    assert result["blocked_reasons"] == ["real_llm_invalid_json"]
    assert result["professional_compact_brief_preview"] is None


def test_renderer_output_missing_required_section_blocked():
    payload = _valid_llm_output()
    payload.pop("risk_view")

    result = _build(
        request=_request(llm_client_mode=LLM_CLIENT_MODE_INJECTED),
        llm_client=_InjectedLLMClient(json.dumps(payload)),
    )

    assert result["readiness"]["status"] == READINESS_BLOCKED
    assert result["blocked_reasons"] == ["real_llm_renderer_output_invalid"]


def test_trading_advice_output_blocked():
    payload = _valid_llm_output(overall_view="buy this company after checking metrics")

    result = _build(
        request=_request(llm_client_mode=LLM_CLIENT_MODE_INJECTED),
        llm_client=_InjectedLLMClient(json.dumps(payload)),
    )

    assert result["readiness"]["status"] == READINESS_BLOCKED
    assert result["blocked_reasons"] == ["real_llm_renderer_output_invalid"]
    assert "buy this company" not in _serialized(result)


def test_engineering_label_output_blocked():
    payload = _valid_llm_output(
        business_view="provider_candidate details should never reach frontstage"
    )

    result = _build(
        request=_request(llm_client_mode=LLM_CLIENT_MODE_INJECTED),
        llm_client=_InjectedLLMClient(json.dumps(payload)),
    )

    assert result["readiness"]["status"] == READINESS_BLOCKED
    assert result["blocked_reasons"] == ["real_llm_renderer_output_invalid"]
    assert "provider_candidate details" not in _serialized(result)


def test_prompt_builder_receives_sanitized_model_facing_context():
    client = _InjectedLLMClient()
    result = _build(
        request=_request(llm_client_mode=LLM_CLIENT_MODE_INJECTED),
        llm_client=client,
    )

    assert result["readiness"]["status"] == READINESS_READY
    prompt = client.calls[0]["prompt"]
    model_context = client.calls[0]["model_context"]
    assert "provider_candidate_bundle" not in prompt
    assert "candidate_items" not in prompt
    assert "source_url" not in prompt
    assert "token" not in json.dumps(model_context, ensure_ascii=False).casefold()
    assert model_context["not_for_trading_advice"] is True


def test_prompt_builder_outputs_json_only_contract_from_model_context():
    client = _InjectedLLMClient()
    _build(
        request=_request(llm_client_mode=LLM_CLIENT_MODE_INJECTED),
        llm_client=client,
    )

    prompt_payload = json.loads(client.calls[0]["prompt"])
    assert prompt_payload["output_rules"]["json_only"] is True
    assert prompt_payload["output_rules"]["no_raw_provider_payloads"] is True
    assert "overall_view" in prompt_payload["required_top_level_fields"]


def test_result_contains_no_raw_prompt_or_raw_response_by_default():
    result = _build(
        request=_request(llm_client_mode=LLM_CLIENT_MODE_INJECTED),
        llm_client=_InjectedLLMClient(),
    )
    text = _serialized(result).casefold()

    for forbidden in (
        "raw_prompt",
        "raw response",
        "raw_llm_response",
        "provider_candidate_bundle",
        "candidate_items",
        "backend trace",
    ):
        assert forbidden not in text


def test_result_contains_sanitized_professional_preview_and_quality_summary():
    result = _build()
    preview_text = _serialized(result["professional_compact_brief_preview"]).casefold()

    assert result["professional_compact_brief_preview"]["overall_view"]["view"]
    assert result["quality_check_summary"]["sample_id"] == "baseline_600406_like"
    assert "pending verification" not in preview_text
    assert "provider_candidate" not in preview_text


def test_no_output_fixtures_or_manifest_artifact_markers_in_result():
    result = _build()
    text = _serialized(result).casefold()

    for forbidden in ("output_path", "fixture_path", "accepted_manifest", "html artifact"):
        assert forbidden not in text


def test_input_request_not_mutated():
    request = _request(llm_client_mode=LLM_CLIENT_MODE_INJECTED)
    original = copy.deepcopy(request)

    _build(request=request, llm_client=_InjectedLLMClient())

    assert request == original


def test_non_600406_sample_passes_with_fake_client():
    request = _request(
        stock_code="300750",
        ts_code="300750.SZ",
        company_name_hint="CATL",
    )

    result = _build(
        request=request,
        tushare_client=_FakeFinancialClient(ts_code="300750.SZ"),
    )

    assert result["readiness"]["status"] == READINESS_READY
    assert result["request_summary"]["sample_id"] == "non_600406_sample"


def test_parse_top_level_real_llm_json_to_renderer_output():
    parsed = parse_real_llm_renderer_output(json.dumps(_valid_llm_output()))

    assert parsed["schema_version"].endswith("renderer_output.v1")
    assert parsed["sections"]["overall_view"]
    assert validate_real_llm_renderer_output(parsed) == parsed

