"""Controlled real LLM local manual smoke harness.

This module is intentionally narrow: it performs an in-memory manual smoke
through the existing ticker-only professional brief chain and a DeepSeek-shaped
LLM boundary.  It does not write files, read credential files, expose prompts,
or return raw model/provider payloads.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
import importlib
import json
import os
import re
from typing import Any

from .controlled_real_tushare_professional_compact_brief_pilot import (
    CONTROLLED_REAL_TUSHARE_PROFESSIONAL_COMPACT_BRIEF_REQUEST_SCHEMA_VERSION,
    OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF,
    TUSHARE_CLIENT_MODE_ENV_LIVE,
    TUSHARE_CLIENT_MODE_FAKE,
    TUSHARE_CLIENT_MODE_INJECTED,
    build_controlled_real_tushare_professional_compact_brief_result,
)
from .llm_analyst_renderer_handoff import (
    LLM_ANALYST_RENDERER_OUTPUT_SCHEMA_VERSION,
    build_model_facing_analyst_context,
    fake_llm_analyst_renderer,
    validate_model_facing_analyst_context,
    validate_llm_analyst_renderer_output,
)
from .professional_compact_brief_quality import (
    PROFESSIONAL_ANALYST_RENDERER_OUTPUT_SCHEMA_VERSION,
    build_professional_analyst_context,
    render_professional_compact_brief_from_context,
    validate_professional_analyst_renderer_output,
)
from .ticker_only_professional_brief_quality_evaluation import (
    QUALITY_SAMPLE_IDS,
    evaluate_professional_compact_brief,
)


CONTROLLED_REAL_LLM_MANUAL_SMOKE_REQUEST_SCHEMA_VERSION = (
    "controlled_real_llm_manual_smoke_request.v1"
)
CONTROLLED_REAL_LLM_MANUAL_SMOKE_RESULT_SCHEMA_VERSION = (
    "controlled_real_llm_manual_smoke_result.v1"
)
CONTROLLED_REAL_LLM_MANUAL_SMOKE_READINESS_SCHEMA_VERSION = (
    "controlled_real_llm_manual_smoke_readiness.v1"
)
CONTROLLED_REAL_LLM_MANUAL_SMOKE_SUMMARY_SCHEMA_VERSION = (
    "controlled_real_llm_manual_smoke_summary.v1"
)

LLM_PROVIDER_DEEPSEEK = "deepseek"
LLM_CLIENT_MODE_FAKE = "fake"
LLM_CLIENT_MODE_INJECTED = "injected"
LLM_CLIENT_MODE_ENV_LIVE = "env_live"
SUPPORTED_LLM_CLIENT_MODES = (
    LLM_CLIENT_MODE_FAKE,
    LLM_CLIENT_MODE_INJECTED,
    LLM_CLIENT_MODE_ENV_LIVE,
)
SUPPORTED_TUSHARE_CLIENT_MODES = (
    TUSHARE_CLIENT_MODE_FAKE,
    TUSHARE_CLIENT_MODE_INJECTED,
    TUSHARE_CLIENT_MODE_ENV_LIVE,
)

READINESS_READY = "ready"
READINESS_BLOCKED = "blocked"
READINESS_SKIPPED = "skipped"

DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-pro"
DEFAULT_QUALITY_SAMPLE_ID = "baseline_600406_like"
NON_600406_QUALITY_SAMPLE_ID = "non_600406_sample"

_REQUEST_FIELDS = {
    "schema_version",
    "stock_code",
    "ts_code",
    "company_name_hint",
    "periods",
    "llm_provider",
    "llm_client_mode",
    "allow_network",
    "allow_file_writes",
    "not_for_trading_advice",
    "tushare_client_mode",
    "allow_tushare_network",
    "include_professional_compact_brief_preview",
    "sample_id",
}

_RESULT_FIELDS = {
    "schema_version",
    "smoke_status",
    "readiness",
    "request_summary",
    "llm_provider",
    "model",
    "base_url",
    "professional_compact_brief_preview",
    "quality_check_summary",
    "blocked_reasons",
    "not_for_trading_advice",
}

_SUMMARY_FIELDS = {
    "schema_version",
    "stock_code",
    "ts_code",
    "company_name_hint",
    "periods",
    "sample_id",
    "llm_provider",
    "llm_client_mode",
    "allow_network",
    "allow_file_writes",
    "tushare_client_mode",
    "allow_tushare_network",
    "include_professional_compact_brief_preview",
    "not_for_trading_advice",
}

_READINESS_FIELDS = {
    "schema_version",
    "status",
    "provider_context_ready",
    "model_context_ready",
    "llm_call_ready",
    "renderer_output_ready",
    "professional_brief_ready",
    "quality_check_ready",
    "blocked_reasons",
    "allow_network",
    "llm_provider",
    "llm_client_mode",
    "not_for_trading_advice",
}

_LLM_RENDERED_SECTION_KEYS = (
    "overall_view",
    "business_view",
    "financial_view",
    "operating_quality_view",
    "industry_macro_view",
    "risk_view",
)

_STOCK_CODE_RE = re.compile(r"\d{6}")
_TS_CODE_RE = re.compile(r"\d{6}\.(SH|SZ|BJ)")

_RAW_OR_FILE_KEYS = {
    "api_key",
    "apikey",
    "api token",
    "api_token",
    "token",
    "secret",
    "credential",
    "authorization",
    "bearer",
    "raw_prompt",
    "raw_response",
    "raw_llm_response",
    "raw_provider_bundle",
    "raw_provider_rows",
    "provider_candidate_bundle",
    "candidate_items",
    "backend_trace",
    "source_url",
    "page_number",
    "snippet",
    "sha256",
    "cache_path",
    "output_path",
    "fixture_path",
    "accepted_manifest_path",
}

_ALLOWED_EXACT_TEXTS = {
    "Tushare",
    "deepseek",
    "env_live",
    "fake",
    "injected",
    "not_for_trading_advice",
    "https://api.deepseek.com",
    "deepseek-v4-pro",
    "deepseek_api_key_missing",
    "deepseek_sdk_unavailable",
    "deepseek_insufficient_balance",
    "deepseek_auth_failed",
    "deepseek_rate_limited",
    "deepseek_api_unavailable",
    "deepseek_network_error",
    "deepseek_api_error",
}

_SECRET_MARKERS = (
    "token",
    ".env",
    "key file",
    "tushare_token",
    "api_key",
    "api token",
    "secret",
    "credential",
    "authorization",
    "bearer",
)

_RAW_TRACE_MARKERS = (
    "backend trace",
    "backend_trace",
    "backend_grounding_summary",
    "raw prompt",
    "raw_prompt",
    "raw response",
    "raw_response",
    "raw llm response",
    "raw_llm_response",
    "raw provider bundle",
    "raw_provider_bundle",
    "raw provider row",
    "raw provider rows",
    "provider_candidate_bundle",
    "candidate_items",
    "source_url",
    "page_number",
    "snippet",
    "sha256",
    "cache_path",
    "output path",
    "output_path",
    "fixture path",
    "fixture_path",
    "accepted manifest",
    "accepted_manifest",
    "Report V1 artifact",
    "report_v1",
    "HTML artifact",
    "html artifact",
    "official_metric_fact",
    "provider_official_conflict",
    "provider vs official",
    "reconciliation",
)

_FRONTSTAGE_FORBIDDEN_MARKERS = (
    "provider_candidate",
    "provider candidate",
    "pending verification",
    "pending official verification",
    "official verification",
    "buy",
    "sell",
    "hold",
    "target price",
    "portfolio",
    "position",
    "technical signal",
    "trading advice",
    "\u4e70\u5165",
    "\u5356\u51fa",
    "\u6301\u6709",
    "\u76ee\u6807\u4ef7",
    "\u4ed3\u4f4d",
    "\u6280\u672f\u4fe1\u53f7",
    "\u4ea4\u6613\u5efa\u8bae",
    "\u7528\u6237\u81ea\u884c",
    "\u81ea\u884c\u5224\u65ad",
    "\u81ea\u884c\u8ddf\u8e2a",
    "\u9700\u8981\u7528\u6237",
    "\u5efa\u8bae\u7528\u6237",
    "\u5f85\u6838\u9a8c",
    "\u6570\u636e\u7f3a\u53e3",
    "\u63a8\u7406",
)

_WORD_MARKERS = {"buy", "sell", "hold", "portfolio", "position"}

_SECRET_LIKE_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]{12,}", re.IGNORECASE),
    re.compile(r"(api[_-]?key|token|secret)\s*[:=]\s*[A-Za-z0-9._~+/=-]{8,}", re.IGNORECASE),
)


class ControlledRealLLMManualSmokeError(ValueError):
    """Raised when the real LLM manual smoke boundary fails closed."""


class _StructuredSkip(Exception):
    def __init__(self, reasons: Iterable[str], *, model: str, base_url: str):
        super().__init__(",".join(str(reason) for reason in reasons))
        self.reasons = _dedupe_preserve_order(reasons)
        self.model = model
        self.base_url = base_url


class _OpenAICompatibleChatClient:
    def __init__(self, client: Any, *, model: str):
        self._client = client
        self._model = model

    def complete(self, *, prompt: str, model_context: Mapping[str, Any]) -> str:
        del model_context
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Return only valid JSON for a fundamental-analysis "
                        "renderer output. Do not include trading advice."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        return _extract_llm_text(response)


def build_controlled_real_llm_manual_smoke_result(
    request: Mapping[str, Any],
    *,
    tushare_client: Any | None = None,
    llm_client: Any | None = None,
) -> dict[str, Any]:
    """Run the minimal in-memory controlled real LLM manual smoke."""

    validated_request = validate_controlled_real_llm_manual_smoke_request(request)
    model, base_url = _deepseek_model_and_base_url()

    provider_result = build_controlled_real_tushare_professional_compact_brief_result(
        _controlled_tushare_request(validated_request),
        tushare_client=tushare_client,
    )
    provider_reasons = _safe_provider_reasons(provider_result.get("blocked_reasons", []))
    if provider_result["readiness"]["status"] != "ready":
        return validate_controlled_real_llm_manual_smoke_result(
            _build_result(
                validated_request,
                status=(
                    READINESS_SKIPPED
                    if provider_result["readiness"]["status"] == "skipped"
                    else READINESS_BLOCKED
                ),
                reasons=provider_reasons or ["provider_context_unavailable"],
                model=model,
                base_url=base_url,
                provider_context_ready=False,
            )
        )

    try:
        professional_context = build_professional_analyst_context(
            provider_result["provider_candidate_bundle"],
            internal_analysis_brief=provider_result["internal_analysis_brief"],
        )
        model_facing_context = build_model_facing_analyst_context(professional_context)
        _assert_no_raw_secret_artifact_markers(model_facing_context)
        prompt = build_real_llm_prompt_from_model_facing_context(model_facing_context)
        raw_text = _run_llm_call(
            validated_request,
            prompt=prompt,
            model_context=model_facing_context,
            llm_client=llm_client,
        )
        renderer_output = parse_real_llm_renderer_output(raw_text)
        renderer_output = validate_real_llm_renderer_output(renderer_output)
    except _StructuredSkip as exc:
        return validate_controlled_real_llm_manual_smoke_result(
            _build_result(
                validated_request,
                status=READINESS_SKIPPED,
                reasons=exc.reasons,
                model=exc.model,
                base_url=exc.base_url,
                provider_context_ready=True,
                model_context_ready=True,
            )
        )
    except json.JSONDecodeError:
        return validate_controlled_real_llm_manual_smoke_result(
            _build_result(
                validated_request,
                status=READINESS_BLOCKED,
                reasons=["real_llm_invalid_json"],
                model=model,
                base_url=base_url,
                provider_context_ready=True,
                model_context_ready=True,
                llm_call_ready=True,
            )
        )
    except ControlledRealLLMManualSmokeError as exc:
        return validate_controlled_real_llm_manual_smoke_result(
            _build_result(
                validated_request,
                status=READINESS_BLOCKED,
                reasons=_safe_exception_reasons(exc),
                model=model,
                base_url=base_url,
                provider_context_ready=True,
                model_context_ready=True,
                llm_call_ready=True,
            )
        )

    try:
        renderer_adapter_output = _professional_renderer_output_from_llm_output(
            renderer_output
        )
        professional_brief = render_professional_compact_brief_from_context(
            professional_context,
            analyst_renderer=lambda _context: renderer_adapter_output,
        )
        preview = (
            _professional_compact_brief_preview(professional_brief)
            if validated_request["include_professional_compact_brief_preview"]
            else None
        )
        quality_summary = _quality_check_summary(
            professional_brief,
            sample_id=validated_request["sample_id"],
        )
    except ControlledRealLLMManualSmokeError as exc:
        return validate_controlled_real_llm_manual_smoke_result(
            _build_result(
                validated_request,
                status=READINESS_BLOCKED,
                reasons=_safe_exception_reasons(exc),
                model=model,
                base_url=base_url,
                provider_context_ready=True,
                model_context_ready=True,
                llm_call_ready=True,
                renderer_output_ready=True,
            )
        )

    return validate_controlled_real_llm_manual_smoke_result(
        _build_result(
            validated_request,
            status=READINESS_READY,
            reasons=[],
            model=model,
            base_url=base_url,
            provider_context_ready=True,
            model_context_ready=True,
            llm_call_ready=True,
            renderer_output_ready=True,
            professional_brief_ready=True,
            quality_check_ready=True,
            professional_compact_brief_preview=preview,
            quality_check_summary=quality_summary,
        )
    )


def validate_controlled_real_llm_manual_smoke_request(
    request: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate and normalize the local manual smoke request."""

    source = _require_mapping(request, "request")
    _reject_bytes(source, "request")
    _reject_raw_or_secret_keys(source, "request")
    unsupported = sorted(set(source) - _REQUEST_FIELDS)
    if unsupported:
        raise ControlledRealLLMManualSmokeError(
            f"request contains unsupported keys: {unsupported}"
        )
    _assert_no_raw_secret_artifact_markers(source)

    if source.get("schema_version") != CONTROLLED_REAL_LLM_MANUAL_SMOKE_REQUEST_SCHEMA_VERSION:
        raise ControlledRealLLMManualSmokeError(
            "schema_version must be "
            f"{CONTROLLED_REAL_LLM_MANUAL_SMOKE_REQUEST_SCHEMA_VERSION}"
        )
    llm_provider = source.get("llm_provider", LLM_PROVIDER_DEEPSEEK)
    if llm_provider != LLM_PROVIDER_DEEPSEEK:
        raise ControlledRealLLMManualSmokeError("llm_provider must be deepseek")
    llm_client_mode = source.get("llm_client_mode", LLM_CLIENT_MODE_FAKE)
    if llm_client_mode not in SUPPORTED_LLM_CLIENT_MODES:
        raise ControlledRealLLMManualSmokeError("llm_client_mode unsupported")
    allow_network = _require_bool(source.get("allow_network", False), "allow_network")
    allow_file_writes = _require_bool(
        source.get("allow_file_writes", False),
        "allow_file_writes",
    )
    if allow_file_writes is not False:
        raise ControlledRealLLMManualSmokeError("allow_file_writes must be false")
    if source.get("not_for_trading_advice", True) is not True:
        raise ControlledRealLLMManualSmokeError("not_for_trading_advice must be true")
    if llm_client_mode == LLM_CLIENT_MODE_ENV_LIVE and not allow_network:
        raise ControlledRealLLMManualSmokeError(
            "allow_network must be true for env_live"
        )

    tushare_client_mode = source.get("tushare_client_mode", TUSHARE_CLIENT_MODE_FAKE)
    if tushare_client_mode not in SUPPORTED_TUSHARE_CLIENT_MODES:
        raise ControlledRealLLMManualSmokeError("tushare_client_mode unsupported")
    allow_tushare_network = _require_bool(
        source.get("allow_tushare_network", False),
        "allow_tushare_network",
    )
    include_preview = _require_bool(
        source.get("include_professional_compact_brief_preview", True),
        "include_professional_compact_brief_preview",
    )

    stock_code = _optional_string(source.get("stock_code"), "stock_code")
    ts_code = _optional_string(source.get("ts_code"), "ts_code")
    if stock_code is None and ts_code is None:
        raise ControlledRealLLMManualSmokeError("stock_code or ts_code is required")
    if stock_code is not None and not _STOCK_CODE_RE.fullmatch(stock_code):
        raise ControlledRealLLMManualSmokeError("stock_code must be six digits")
    if ts_code is not None and not _TS_CODE_RE.fullmatch(ts_code):
        raise ControlledRealLLMManualSmokeError(
            "ts_code must be six digits plus market suffix"
        )
    if ts_code is None:
        ts_code = _derive_ts_code(stock_code)
    if stock_code is None:
        stock_code = ts_code.split(".", 1)[0]
    if ts_code.split(".", 1)[0] != stock_code:
        raise ControlledRealLLMManualSmokeError("stock_code and ts_code mismatch")

    sample_id = source.get("sample_id")
    if sample_id is None:
        sample_id = (
            DEFAULT_QUALITY_SAMPLE_ID
            if stock_code == "600406"
            else NON_600406_QUALITY_SAMPLE_ID
        )
    if sample_id not in QUALITY_SAMPLE_IDS:
        raise ControlledRealLLMManualSmokeError("sample_id unsupported")

    result = {
        "schema_version": source["schema_version"],
        "stock_code": stock_code,
        "ts_code": ts_code,
        "company_name_hint": _optional_string(
            source.get("company_name_hint"),
            "company_name_hint",
        ),
        "periods": _periods(source.get("periods")),
        "llm_provider": llm_provider,
        "llm_client_mode": llm_client_mode,
        "allow_network": allow_network,
        "allow_file_writes": False,
        "not_for_trading_advice": True,
        "tushare_client_mode": tushare_client_mode,
        "allow_tushare_network": allow_tushare_network,
        "include_professional_compact_brief_preview": include_preview,
        "sample_id": sample_id,
    }
    _assert_no_raw_secret_artifact_markers(result)
    return result


def validate_controlled_real_llm_manual_smoke_result(
    result: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the sanitized smoke result contract."""

    source = _require_mapping(result, "result")
    unsupported = sorted(set(source) - _RESULT_FIELDS)
    if unsupported:
        raise ControlledRealLLMManualSmokeError(
            f"result contains unsupported keys: {unsupported}"
        )
    _require_fields(source, tuple(sorted(_RESULT_FIELDS)), "result")
    _assert_no_secret_like_anywhere(source)
    copied = deepcopy(dict(source))
    if copied["schema_version"] != CONTROLLED_REAL_LLM_MANUAL_SMOKE_RESULT_SCHEMA_VERSION:
        raise ControlledRealLLMManualSmokeError("result schema_version invalid")
    if copied["smoke_status"] not in {
        READINESS_READY,
        READINESS_BLOCKED,
        READINESS_SKIPPED,
    }:
        raise ControlledRealLLMManualSmokeError("smoke_status invalid")
    copied["readiness"] = _validate_readiness(copied["readiness"])
    if copied["smoke_status"] != copied["readiness"]["status"]:
        raise ControlledRealLLMManualSmokeError("smoke_status readiness mismatch")
    copied["request_summary"] = _validate_request_summary(copied["request_summary"])
    if copied["llm_provider"] != LLM_PROVIDER_DEEPSEEK:
        raise ControlledRealLLMManualSmokeError("llm_provider invalid")
    _require_non_empty_string(copied["model"], "result.model")
    _require_non_empty_string(copied["base_url"], "result.base_url")
    if copied["professional_compact_brief_preview"] is not None:
        _assert_no_raw_secret_artifact_markers(copied["professional_compact_brief_preview"])
        assert_no_real_llm_frontstage_leak(copied["professional_compact_brief_preview"])
    if copied["quality_check_summary"] is not None:
        copied["quality_check_summary"] = _validate_quality_summary(
            copied["quality_check_summary"]
        )
    _require_string_list(copied["blocked_reasons"], "result.blocked_reasons")
    if copied["blocked_reasons"] != copied["readiness"]["blocked_reasons"]:
        raise ControlledRealLLMManualSmokeError("blocked_reasons mismatch")
    _require_true(copied["not_for_trading_advice"], "result.not_for_trading_advice")
    _assert_no_raw_secret_artifact_markers(copied)
    return copied


def build_deepseek_manual_smoke_client_from_env() -> Any:
    """Build a DeepSeek OpenAI-compatible client from allowed env vars only."""

    model, base_url = _deepseek_model_and_base_url()
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise _StructuredSkip(
            ["deepseek_api_key_missing"],
            model=model,
            base_url=base_url,
        )
    try:
        openai_module = importlib.import_module("openai")
        openai_client_class = getattr(openai_module, "OpenAI")
    except Exception as exc:
        raise _StructuredSkip(
            ["deepseek_sdk_unavailable"],
            model=model,
            base_url=base_url,
        ) from exc
    client = openai_client_class(api_key=api_key, base_url=base_url)
    return _OpenAICompatibleChatClient(client, model=model)


def build_real_llm_prompt_from_model_facing_context(
    model_facing_context: Mapping[str, Any],
) -> str:
    """Build a JSON-only prompt from sanitized model-facing context."""

    context = validate_model_facing_analyst_context(model_facing_context)
    _assert_no_raw_secret_artifact_markers(context)
    prompt_payload = {
        "task": "Return one JSON object for llm_analyst_renderer_output.v1.",
        "context": context,
        "required_top_level_fields": [
            *_LLM_RENDERED_SECTION_KEYS,
            "key_variables",
            "conclusion_boundary",
            "source_note",
            "not_for_trading_advice",
        ],
        "forbidden_output_markers": [
            "buy",
            "sell",
            "hold",
            "target price",
            "portfolio",
            "position",
            "technical signal",
            "trading advice",
            "provider_candidate",
            "pending verification",
            "official verification",
            "Report V1 artifact",
            "HTML artifact",
        ],
        "output_rules": {
            "json_only": True,
            "not_for_trading_advice": True,
            "no_artifacts": True,
            "no_backend_trace": True,
            "no_raw_provider_payloads": True,
        },
    }
    _assert_no_raw_secret_artifact_markers(prompt_payload["context"])
    return json.dumps(prompt_payload, ensure_ascii=False, sort_keys=True)


def parse_real_llm_renderer_output(raw_text: Any) -> dict[str, Any]:
    """Parse model text and normalize it into the LLM renderer output contract."""

    if isinstance(raw_text, Mapping):
        parsed = deepcopy(dict(raw_text))
    elif isinstance(raw_text, str):
        parsed = json.loads(raw_text)
    else:
        raise ControlledRealLLMManualSmokeError("real_llm_output must be text or mapping")
    if not isinstance(parsed, Mapping):
        raise ControlledRealLLMManualSmokeError("real_llm_output must be a JSON object")

    if "sections" in parsed:
        output = deepcopy(dict(parsed))
        output.setdefault("schema_version", LLM_ANALYST_RENDERER_OUTPUT_SCHEMA_VERSION)
    else:
        output = {
            "schema_version": parsed.get(
                "schema_version",
                LLM_ANALYST_RENDERER_OUTPUT_SCHEMA_VERSION,
            ),
            "sections": {
                key: parsed.get(key)
                for key in _LLM_RENDERED_SECTION_KEYS
            },
            "key_variables": parsed.get("key_variables"),
            "conclusion_boundary": parsed.get("conclusion_boundary"),
            "source_note": parsed.get("source_note"),
            "not_for_trading_advice": parsed.get("not_for_trading_advice"),
        }
    return deepcopy(output)


def validate_real_llm_renderer_output(output: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a real LLM renderer output before it reaches frontstage brief."""

    try:
        result = validate_llm_analyst_renderer_output(output)
    except Exception as exc:
        raise ControlledRealLLMManualSmokeError(
            "real_llm_renderer_output_invalid"
        ) from exc
    _assert_no_raw_secret_artifact_markers(result)
    assert_no_real_llm_frontstage_leak(result)
    return result


def assert_no_real_llm_smoke_forbidden_markers(value: Any) -> None:
    """Reject secrets, raw backend/provider payloads, artifacts, and unsafe output."""

    _assert_no_raw_secret_artifact_markers(value)
    assert_no_real_llm_frontstage_leak(value)


def assert_no_real_llm_frontstage_leak(value: Any) -> None:
    """Reject frontstage engineering labels and trading-action language."""

    finding = _find_marker(
        value,
        markers=_FRONTSTAGE_FORBIDDEN_MARKERS,
        allowed_exact_texts=_ALLOWED_EXACT_TEXTS,
    )
    if finding:
        raise ControlledRealLLMManualSmokeError(
            f"real llm smoke frontstage safety violation: {finding}"
        )


def _run_llm_call(
    request: Mapping[str, Any],
    *,
    prompt: str,
    model_context: Mapping[str, Any],
    llm_client: Any | None,
) -> str:
    mode = request["llm_client_mode"]
    if mode == LLM_CLIENT_MODE_FAKE:
        if llm_client is not None:
            raise ControlledRealLLMManualSmokeError("fake_llm_disallows_client")
        return json.dumps(fake_llm_analyst_renderer(model_context), ensure_ascii=False)
    if mode == LLM_CLIENT_MODE_INJECTED:
        if llm_client is None:
            raise ControlledRealLLMManualSmokeError("injected_llm_client_required")
        return _call_llm_client(
            llm_client,
            prompt=prompt,
            model_context=model_context,
            model=_deepseek_model_and_base_url()[0],
        )
    if mode == LLM_CLIENT_MODE_ENV_LIVE:
        if llm_client is not None:
            raise ControlledRealLLMManualSmokeError("env_live_disallows_injected_client")
        if request["allow_network"] is not True:
            raise _StructuredSkip(
                ["deepseek_network_not_allowed"],
                model=_deepseek_model_and_base_url()[0],
                base_url=_deepseek_model_and_base_url()[1],
            )
        try:
            client = build_deepseek_manual_smoke_client_from_env()
            return _call_llm_client(
                client,
                prompt=prompt,
                model_context=model_context,
                model=_deepseek_model_and_base_url()[0],
            )
        except _StructuredSkip:
            raise
        except Exception as exc:
            model, base_url = _deepseek_model_and_base_url()
            raise _StructuredSkip(
                [_safe_deepseek_error_reason(exc)],
                model=model,
                base_url=base_url,
            ) from exc
    raise ControlledRealLLMManualSmokeError("llm_client_mode unsupported")


def _call_llm_client(
    llm_client: Any,
    *,
    prompt: str,
    model_context: Mapping[str, Any],
    model: str,
) -> str:
    try:
        if hasattr(llm_client, "complete"):
            response = llm_client.complete(
                prompt=prompt,
                model_context=deepcopy(dict(model_context)),
            )
        elif hasattr(llm_client, "create"):
            response = llm_client.create(prompt=prompt, model=model)
        elif callable(llm_client):
            try:
                response = llm_client(
                    prompt=prompt,
                    model_context=deepcopy(dict(model_context)),
                    model=model,
                )
            except TypeError:
                response = llm_client(prompt)
        else:
            raise ControlledRealLLMManualSmokeError("llm_client unsupported")
    except ControlledRealLLMManualSmokeError:
        raise
    except Exception as exc:
        raise exc
    return _extract_llm_text(response)


def _extract_llm_text(response: Any) -> str:
    if isinstance(response, str):
        return response
    if isinstance(response, Mapping):
        for key in ("content", "text", "raw_text", "output_text"):
            value = response.get(key)
            if isinstance(value, str):
                return value
        choices = response.get("choices")
        if isinstance(choices, list) and choices:
            return _extract_llm_text(choices[0])
        message = response.get("message")
        if isinstance(message, Mapping):
            return _extract_llm_text(message)
    choices = getattr(response, "choices", None)
    if isinstance(choices, list) and choices:
        first = choices[0]
        message = getattr(first, "message", None)
        if message is not None:
            content = getattr(message, "content", None)
            if isinstance(content, str):
                return content
    raise ControlledRealLLMManualSmokeError("llm_response_text_missing")


def _professional_renderer_output_from_llm_output(
    output: Mapping[str, Any],
) -> dict[str, Any]:
    checked = validate_real_llm_renderer_output(output)
    renderer_output = {
        "schema_version": PROFESSIONAL_ANALYST_RENDERER_OUTPUT_SCHEMA_VERSION,
        "sections": deepcopy(checked["sections"]),
        "key_variables": list(checked["key_variables"]),
        "conclusion_boundary": checked["conclusion_boundary"],
        "not_for_trading_advice": True,
    }
    try:
        renderer_output = validate_professional_analyst_renderer_output(renderer_output)
    except Exception as exc:
        raise ControlledRealLLMManualSmokeError(
            "professional_renderer_output_invalid"
        ) from exc
    assert_no_real_llm_frontstage_leak(renderer_output)
    return renderer_output


def _professional_compact_brief_preview(brief: Mapping[str, Any]) -> dict[str, Any]:
    preview = {
        "schema_version": brief.get("schema_version"),
        "stock_code": brief.get("stock_code"),
        "ts_code": brief.get("ts_code"),
        "company_name_hint": brief.get("company_name_hint"),
        "title": brief.get("title"),
        "not_for_trading_advice": True,
    }
    for key in _LLM_RENDERED_SECTION_KEYS:
        preview[key] = deepcopy(brief.get(key))
    preview["key_variables"] = deepcopy(brief.get("key_variables", []))
    preview["conclusion_boundary"] = brief.get("conclusion_boundary")
    preview["source_note"] = brief.get("source_note")
    _assert_no_raw_secret_artifact_markers(preview)
    assert_no_real_llm_frontstage_leak(preview)
    return preview


def _quality_check_summary(brief: Mapping[str, Any], *, sample_id: str) -> dict[str, Any]:
    try:
        scorecard = evaluate_professional_compact_brief(brief, sample_id=sample_id)
    except Exception as exc:
        raise ControlledRealLLMManualSmokeError("quality_check_failed") from exc
    summary = {
        "schema_version": scorecard["schema_version"],
        "sample_id": scorecard["sample_id"],
        "overall_status": scorecard["overall_status"],
        "pass_count": scorecard["pass_count"],
        "warning_count": scorecard["warning_count"],
        "fail_count": scorecard["fail_count"],
        "issue_count": scorecard["issue_count"],
        "issue_ids": [
            issue["issue_id"]
            for issue in scorecard.get("issues", [])
            if isinstance(issue, Mapping) and isinstance(issue.get("issue_id"), str)
        ],
        "not_for_trading_advice": True,
    }
    return _validate_quality_summary(summary)


def _controlled_tushare_request(request: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": (
            CONTROLLED_REAL_TUSHARE_PROFESSIONAL_COMPACT_BRIEF_REQUEST_SCHEMA_VERSION
        ),
        "stock_code": request["stock_code"],
        "ts_code": request["ts_code"],
        "company_name_hint": request["company_name_hint"],
        "periods": list(request["periods"]),
        "allow_network": request["allow_tushare_network"],
        "tushare_client_mode": request["tushare_client_mode"],
        "output_mode": OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF,
        "not_for_trading_advice": True,
    }


def _build_result(
    request: Mapping[str, Any],
    *,
    status: str,
    reasons: Iterable[str],
    model: str,
    base_url: str,
    provider_context_ready: bool = False,
    model_context_ready: bool = False,
    llm_call_ready: bool = False,
    renderer_output_ready: bool = False,
    professional_brief_ready: bool = False,
    quality_check_ready: bool = False,
    professional_compact_brief_preview: Mapping[str, Any] | None = None,
    quality_check_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    blocked_reasons = _dedupe_preserve_order(str(reason) for reason in reasons)
    readiness = {
        "schema_version": CONTROLLED_REAL_LLM_MANUAL_SMOKE_READINESS_SCHEMA_VERSION,
        "status": status,
        "provider_context_ready": provider_context_ready,
        "model_context_ready": model_context_ready,
        "llm_call_ready": llm_call_ready,
        "renderer_output_ready": renderer_output_ready,
        "professional_brief_ready": professional_brief_ready,
        "quality_check_ready": quality_check_ready,
        "blocked_reasons": blocked_reasons,
        "allow_network": request["allow_network"],
        "llm_provider": request["llm_provider"],
        "llm_client_mode": request["llm_client_mode"],
        "not_for_trading_advice": True,
    }
    result = {
        "schema_version": CONTROLLED_REAL_LLM_MANUAL_SMOKE_RESULT_SCHEMA_VERSION,
        "smoke_status": status,
        "readiness": readiness,
        "request_summary": _build_request_summary(request),
        "llm_provider": request["llm_provider"],
        "model": model,
        "base_url": base_url,
        "professional_compact_brief_preview": (
            deepcopy(dict(professional_compact_brief_preview))
            if professional_compact_brief_preview is not None
            else None
        ),
        "quality_check_summary": (
            deepcopy(dict(quality_check_summary))
            if quality_check_summary is not None
            else None
        ),
        "blocked_reasons": blocked_reasons,
        "not_for_trading_advice": True,
    }
    return result


def _build_request_summary(request: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": CONTROLLED_REAL_LLM_MANUAL_SMOKE_SUMMARY_SCHEMA_VERSION,
        "stock_code": request["stock_code"],
        "ts_code": request["ts_code"],
        "company_name_hint": request["company_name_hint"],
        "periods": list(request["periods"]),
        "sample_id": request["sample_id"],
        "llm_provider": request["llm_provider"],
        "llm_client_mode": request["llm_client_mode"],
        "allow_network": request["allow_network"],
        "allow_file_writes": False,
        "tushare_client_mode": request["tushare_client_mode"],
        "allow_tushare_network": request["allow_tushare_network"],
        "include_professional_compact_brief_preview": (
            request["include_professional_compact_brief_preview"]
        ),
        "not_for_trading_advice": True,
    }


def _validate_request_summary(value: Any) -> dict[str, Any]:
    summary = _require_mapping(value, "request_summary")
    unsupported = sorted(set(summary) - _SUMMARY_FIELDS)
    if unsupported:
        raise ControlledRealLLMManualSmokeError(
            f"request_summary contains unsupported keys: {unsupported}"
        )
    _require_fields(summary, tuple(sorted(_SUMMARY_FIELDS)), "request_summary")
    result = deepcopy(dict(summary))
    if result["schema_version"] != CONTROLLED_REAL_LLM_MANUAL_SMOKE_SUMMARY_SCHEMA_VERSION:
        raise ControlledRealLLMManualSmokeError("request_summary schema_version invalid")
    _optional_string(result["stock_code"], "request_summary.stock_code")
    _optional_string(result["ts_code"], "request_summary.ts_code")
    _optional_string(
        result["company_name_hint"],
        "request_summary.company_name_hint",
    )
    _require_string_list(result["periods"], "request_summary.periods")
    _require_non_empty_string(result["sample_id"], "request_summary.sample_id")
    if result["llm_provider"] != LLM_PROVIDER_DEEPSEEK:
        raise ControlledRealLLMManualSmokeError("request_summary llm_provider invalid")
    if result["llm_client_mode"] not in SUPPORTED_LLM_CLIENT_MODES:
        raise ControlledRealLLMManualSmokeError("request_summary llm_client_mode invalid")
    _require_bool(result["allow_network"], "request_summary.allow_network")
    if result["allow_file_writes"] is not False:
        raise ControlledRealLLMManualSmokeError("request_summary file writes invalid")
    if result["tushare_client_mode"] not in SUPPORTED_TUSHARE_CLIENT_MODES:
        raise ControlledRealLLMManualSmokeError(
            "request_summary tushare_client_mode invalid"
        )
    _require_bool(
        result["allow_tushare_network"],
        "request_summary.allow_tushare_network",
    )
    _require_bool(
        result["include_professional_compact_brief_preview"],
        "request_summary.include_professional_compact_brief_preview",
    )
    _require_true(
        result["not_for_trading_advice"],
        "request_summary.not_for_trading_advice",
    )
    return result


def _validate_readiness(value: Any) -> dict[str, Any]:
    readiness = _require_mapping(value, "readiness")
    unsupported = sorted(set(readiness) - _READINESS_FIELDS)
    if unsupported:
        raise ControlledRealLLMManualSmokeError(
            f"readiness contains unsupported keys: {unsupported}"
        )
    _require_fields(readiness, tuple(sorted(_READINESS_FIELDS)), "readiness")
    result = deepcopy(dict(readiness))
    if result["schema_version"] != CONTROLLED_REAL_LLM_MANUAL_SMOKE_READINESS_SCHEMA_VERSION:
        raise ControlledRealLLMManualSmokeError("readiness schema_version invalid")
    if result["status"] not in {READINESS_READY, READINESS_BLOCKED, READINESS_SKIPPED}:
        raise ControlledRealLLMManualSmokeError("readiness status invalid")
    for key in (
        "provider_context_ready",
        "model_context_ready",
        "llm_call_ready",
        "renderer_output_ready",
        "professional_brief_ready",
        "quality_check_ready",
        "allow_network",
    ):
        _require_bool(result[key], f"readiness.{key}")
    if result["llm_provider"] != LLM_PROVIDER_DEEPSEEK:
        raise ControlledRealLLMManualSmokeError("readiness llm_provider invalid")
    if result["llm_client_mode"] not in SUPPORTED_LLM_CLIENT_MODES:
        raise ControlledRealLLMManualSmokeError("readiness llm_client_mode invalid")
    _require_string_list(result["blocked_reasons"], "readiness.blocked_reasons")
    _require_true(result["not_for_trading_advice"], "readiness.not_for_trading_advice")
    if result["status"] == READINESS_READY and result["blocked_reasons"]:
        raise ControlledRealLLMManualSmokeError("ready result cannot have blockers")
    if result["status"] != READINESS_READY and not result["blocked_reasons"]:
        raise ControlledRealLLMManualSmokeError(
            "blocked or skipped result needs blockers"
        )
    return result


def _validate_quality_summary(value: Any) -> dict[str, Any]:
    summary = _require_mapping(value, "quality_check_summary")
    fields = {
        "schema_version",
        "sample_id",
        "overall_status",
        "pass_count",
        "warning_count",
        "fail_count",
        "issue_count",
        "issue_ids",
        "not_for_trading_advice",
    }
    unsupported = sorted(set(summary) - fields)
    if unsupported:
        raise ControlledRealLLMManualSmokeError(
            f"quality_check_summary contains unsupported keys: {unsupported}"
        )
    _require_fields(summary, tuple(sorted(fields)), "quality_check_summary")
    result = deepcopy(dict(summary))
    _require_non_empty_string(result["schema_version"], "quality.schema_version")
    _require_non_empty_string(result["sample_id"], "quality.sample_id")
    _require_non_empty_string(result["overall_status"], "quality.overall_status")
    for key in ("pass_count", "warning_count", "fail_count", "issue_count"):
        _require_non_negative_int(result[key], f"quality.{key}")
    _require_string_list(result["issue_ids"], "quality.issue_ids")
    _require_true(result["not_for_trading_advice"], "quality.not_for_trading_advice")
    _assert_no_raw_secret_artifact_markers(result)
    assert_no_real_llm_frontstage_leak(result)
    return result


def _deepseek_model_and_base_url() -> tuple[str, str]:
    model = os.environ.get("DEEPSEEK_MODEL") or DEFAULT_DEEPSEEK_MODEL
    base_url = os.environ.get("DEEPSEEK_BASE_URL") or DEFAULT_DEEPSEEK_BASE_URL
    return model, base_url


def _safe_deepseek_error_reason(exc: BaseException) -> str:
    status_code = getattr(exc, "status_code", None)
    if status_code is None:
        response = getattr(exc, "response", None)
        status_code = getattr(response, "status_code", None)
    if status_code is None:
        match = re.search(r"(?<!\d)(401|402|403|429|5\d\d)(?!\d)", str(exc))
        status_code = int(match.group(1)) if match else None
    if status_code == 402:
        return "deepseek_insufficient_balance"
    if status_code in {401, 403}:
        return "deepseek_auth_failed"
    if status_code == 429:
        return "deepseek_rate_limited"
    if isinstance(status_code, int) and status_code >= 500:
        return "deepseek_api_unavailable"
    text = str(type(exc).__name__).casefold()
    if any(marker in text for marker in ("timeout", "connection", "network")):
        return "deepseek_network_error"
    return "deepseek_api_error"


def _safe_provider_reasons(reasons: Iterable[Any]) -> list[str]:
    mapping = {
        "environment_credential_missing": "tushare_env_missing",
        "injected_client_required": "tushare_injected_client_required",
    }
    return _dedupe_preserve_order(mapping.get(str(reason), str(reason)) for reason in reasons)


def _safe_exception_reasons(exc: BaseException) -> list[str]:
    text = str(exc)
    allowed = {
        "fake_llm_disallows_client",
        "injected_llm_client_required",
        "env_live_disallows_injected_client",
        "real_llm_renderer_output_invalid",
        "professional_renderer_output_invalid",
        "quality_check_failed",
        "llm_response_text_missing",
    }
    for reason in allowed:
        if reason in text:
            return [reason]
    return ["real_llm_smoke_blocked"]


def _assert_no_raw_secret_artifact_markers(value: Any) -> None:
    finding = _find_marker(
        value,
        markers=(*_SECRET_MARKERS, *_RAW_TRACE_MARKERS),
        allowed_exact_texts=_ALLOWED_EXACT_TEXTS,
    )
    if finding:
        raise ControlledRealLLMManualSmokeError(
            f"real llm smoke safety violation: {finding}"
        )


def _reject_raw_or_secret_keys(value: Any, path: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized = _normalise_marker(key_text)
            if key_text in _RAW_OR_FILE_KEYS or normalized in _RAW_OR_FILE_KEYS:
                raise ControlledRealLLMManualSmokeError(
                    f"{path} contains unsupported file, raw, or secret key"
                )
            _reject_raw_or_secret_keys(child, f"{path}.{key_text}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_raw_or_secret_keys(child, f"{path}[{index}]")


def _reject_bytes(value: Any, path: str) -> None:
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise ControlledRealLLMManualSmokeError(f"{path} contains raw bytes")
    if isinstance(value, Mapping):
        for key, child in value.items():
            _reject_bytes(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_bytes(child, f"{path}[{index}]")


def _find_marker(
    value: Any,
    *,
    markers: Iterable[str],
    allowed_exact_texts: set[str],
) -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text not in allowed_exact_texts:
                key_finding = _text_marker(
                    key_text,
                    markers=markers,
                    allowed_exact_texts=allowed_exact_texts,
                )
                if key_finding:
                    return key_finding
            child_finding = _find_marker(
                child,
                markers=markers,
                allowed_exact_texts=allowed_exact_texts,
            )
            if child_finding:
                return child_finding
        return None
    if isinstance(value, (list, tuple, set)):
        for item in value:
            item_finding = _find_marker(
                item,
                markers=markers,
                allowed_exact_texts=allowed_exact_texts,
            )
            if item_finding:
                return item_finding
        return None
    if isinstance(value, str):
        return _text_marker(
            value,
            markers=markers,
            allowed_exact_texts=allowed_exact_texts,
        )
    return None


def _text_marker(
    value: str,
    *,
    markers: Iterable[str],
    allowed_exact_texts: set[str],
) -> str | None:
    if value in allowed_exact_texts:
        return None
    if _looks_like_secret_text(value):
        return "secret_like_string"
    searchable_value = value
    for allowed in allowed_exact_texts:
        searchable_value = searchable_value.replace(allowed, "")
    lowered = searchable_value.casefold()
    separator_normalized = _normalize_separator_text(searchable_value)
    normalized = _normalise_marker(searchable_value)
    for marker in markers:
        marker_lower = marker.casefold()
        marker_separator = _normalize_separator_text(marker)
        marker_normalized = _normalise_marker(marker)
        if marker_lower == ".env":
            if ".env" in lowered:
                return "forbidden_marker"
            continue
        if marker_normalized in _WORD_MARKERS:
            if re.search(
                rf"(?<![a-z0-9]){re.escape(marker_normalized)}(?![a-z0-9])",
                normalized,
            ):
                return "forbidden_marker"
            continue
        if (
            marker_lower in lowered
            or marker_separator in separator_normalized
            or (marker_normalized and marker_normalized in normalized)
            or marker in value
        ):
            return "forbidden_marker"
    return None


def _assert_no_secret_like_anywhere(value: Any) -> None:
    if isinstance(value, Mapping):
        for child in value.values():
            _assert_no_secret_like_anywhere(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_secret_like_anywhere(child)
    elif isinstance(value, str) and _looks_like_secret_text(value):
        raise ControlledRealLLMManualSmokeError("result contains secret-like string")


def _looks_like_secret_text(value: str) -> bool:
    if value in _ALLOWED_EXACT_TEXTS:
        return False
    for pattern in _SECRET_LIKE_PATTERNS:
        if pattern.search(value):
            return True
    compact = value.strip()
    if len(compact) < 32 or re.search(r"\s", compact):
        return False
    if not all(ord(char) < 128 for char in compact):
        return False
    has_upper = any(char.isupper() for char in compact)
    has_lower = any(char.islower() for char in compact)
    has_digit = any(char.isdigit() for char in compact)
    return has_upper and has_lower and has_digit


def _periods(value: Any) -> list[str]:
    if value is None:
        return ["20251231"]
    if not isinstance(value, list) or not value:
        raise ControlledRealLLMManualSmokeError("periods must be a non-empty list")
    result = []
    for item in value:
        if not isinstance(item, str) or not re.fullmatch(r"\d{8}", item):
            raise ControlledRealLLMManualSmokeError(
                "periods must contain YYYYMMDD strings"
            )
        result.append(item)
    return result


def _derive_ts_code(stock_code: str | None) -> str:
    assert stock_code is not None
    if stock_code.startswith(("6", "9")):
        suffix = "SH"
    elif stock_code.startswith(("0", "2", "3")):
        suffix = "SZ"
    else:
        suffix = "BJ"
    return f"{stock_code}.{suffix}"


def _optional_string(value: Any, path: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ControlledRealLLMManualSmokeError(f"{path} must be string or null")
    return value


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ControlledRealLLMManualSmokeError(f"{field} must be a mapping")
    return value


def _require_fields(value: Mapping[str, Any], fields: tuple[str, ...], path: str) -> None:
    missing = [field for field in fields if field not in value]
    if missing:
        raise ControlledRealLLMManualSmokeError(
            f"{path} missing required fields: {missing}"
        )


def _require_non_empty_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ControlledRealLLMManualSmokeError(f"{path} must be a non-empty string")
    return value


def _require_string_list(value: Any, path: str) -> list[str]:
    if not isinstance(value, list):
        raise ControlledRealLLMManualSmokeError(f"{path} must be a list")
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise ControlledRealLLMManualSmokeError(f"{path}[{index}] must be string")
    return value


def _require_bool(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise ControlledRealLLMManualSmokeError(f"{path} must be bool")
    return value


def _require_true(value: Any, path: str) -> None:
    if value is not True:
        raise ControlledRealLLMManualSmokeError(f"{path} must be true")


def _require_non_negative_int(value: Any, path: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ControlledRealLLMManualSmokeError(f"{path} must be a non-negative int")
    return value


def _normalise_marker(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().casefold()).strip("_")


def _normalize_separator_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[_-]+", " ", value.strip().casefold())).strip()


def _dedupe_preserve_order(values: Iterable[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value)
        if text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


__all__ = [
    "CONTROLLED_REAL_LLM_MANUAL_SMOKE_READINESS_SCHEMA_VERSION",
    "CONTROLLED_REAL_LLM_MANUAL_SMOKE_REQUEST_SCHEMA_VERSION",
    "CONTROLLED_REAL_LLM_MANUAL_SMOKE_RESULT_SCHEMA_VERSION",
    "CONTROLLED_REAL_LLM_MANUAL_SMOKE_SUMMARY_SCHEMA_VERSION",
    "DEFAULT_DEEPSEEK_BASE_URL",
    "DEFAULT_DEEPSEEK_MODEL",
    "LLM_CLIENT_MODE_ENV_LIVE",
    "LLM_CLIENT_MODE_FAKE",
    "LLM_CLIENT_MODE_INJECTED",
    "LLM_PROVIDER_DEEPSEEK",
    "READINESS_BLOCKED",
    "READINESS_READY",
    "READINESS_SKIPPED",
    "ControlledRealLLMManualSmokeError",
    "assert_no_real_llm_frontstage_leak",
    "assert_no_real_llm_smoke_forbidden_markers",
    "build_controlled_real_llm_manual_smoke_result",
    "build_deepseek_manual_smoke_client_from_env",
    "build_real_llm_prompt_from_model_facing_context",
    "parse_real_llm_renderer_output",
    "validate_controlled_real_llm_manual_smoke_request",
    "validate_controlled_real_llm_manual_smoke_result",
    "validate_real_llm_renderer_output",
]
