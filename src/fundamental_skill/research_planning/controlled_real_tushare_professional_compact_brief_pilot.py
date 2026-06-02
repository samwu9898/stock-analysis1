# -*- coding: utf-8 -*-
"""Controlled Tushare to professional compact brief pilot.

This thin slice keeps provider evidence status internal while producing a
professional, user-facing fundamental brief. It never writes artifacts, never
reads local credential files, and never promotes Tushare rows to official facts.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
import os
import json
import re
from typing import Any

from .a_share_fundamental_skill_wrapper import (
    A_SHARE_FUNDAMENTAL_SKILL_REQUEST_SCHEMA_VERSION,
    INPUT_MODE_ORCHESTRATION_RESULT,
    OUTPUT_MODE_COMPACT_BRIEF,
    build_a_share_fundamental_skill_response,
)
from .evidence_aware_research_pack_scaffold import (
    build_evidence_aware_research_pack_scaffold,
)
from .live_evidence_research_pack_orchestration_entry import (
    LIVE_EVIDENCE_RESEARCH_PACK_ORCHESTRATION_REQUEST_SCHEMA_VERSION,
    REQUESTED_OUTPUT_VERTICAL_SLICE_AND_MARKDOWN_PREVIEW,
    build_live_evidence_research_pack_orchestration_result,
)
from .ticker_research_context_skeleton import build_ticker_research_context_skeleton


CONTROLLED_REAL_TUSHARE_PROFESSIONAL_COMPACT_BRIEF_REQUEST_SCHEMA_VERSION = (
    "controlled_real_tushare_professional_compact_brief_request.v1"
)
CONTROLLED_REAL_TUSHARE_PROFESSIONAL_COMPACT_BRIEF_RESULT_SCHEMA_VERSION = (
    "controlled_real_tushare_professional_compact_brief_result.v1"
)
CONTROLLED_REAL_TUSHARE_PROVIDER_CANDIDATE_BUNDLE_SCHEMA_VERSION = (
    "controlled_real_tushare_provider_candidate_bundle.v1"
)
PROFESSIONAL_ANALYST_COMPACT_BRIEF_SCHEMA_VERSION = (
    "professional_analyst_compact_brief.v1"
)
PROFESSIONAL_ANALYST_COMPACT_BRIEF_SECTION_SCHEMA_VERSION = (
    "professional_analyst_compact_brief_section.v1"
)
CONTROLLED_REAL_TUSHARE_PROFESSIONAL_E2E_READINESS_SCHEMA_VERSION = (
    "controlled_real_tushare_professional_e2e_readiness.v1"
)
CONTROLLED_REAL_TUSHARE_PROVIDER_CANDIDATE_ITEM_SCHEMA_VERSION = (
    "controlled_real_tushare_provider_candidate_item.v1"
)
CONTROLLED_REAL_TUSHARE_PROFESSIONAL_INTERNAL_PAYLOAD_SCHEMA_VERSION = (
    "controlled_real_tushare_professional_internal_payload.v1"
)

PROVIDER_NAME = "Tushare"
SUPPORTED_PERIODS = ("20251231", "20260331")
PERIOD_LABELS = {"20251231": "2025FY", "20260331": "2026Q1"}
TARGET_TABLES = ("income", "balancesheet", "cashflow", "fina_indicator")

TUSHARE_CLIENT_MODE_FAKE = "fake"
TUSHARE_CLIENT_MODE_INJECTED = "injected"
TUSHARE_CLIENT_MODE_ENV_LIVE = "env_live"
SUPPORTED_TUSHARE_CLIENT_MODES = (
    TUSHARE_CLIENT_MODE_FAKE,
    TUSHARE_CLIENT_MODE_INJECTED,
    TUSHARE_CLIENT_MODE_ENV_LIVE,
)

OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF = "professional_compact_brief"
OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF_AND_INTERNAL_PAYLOAD = (
    "professional_compact_brief_and_internal_payload"
)
SUPPORTED_OUTPUT_MODES = (
    OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF,
    OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF_AND_INTERNAL_PAYLOAD,
)

E2E_READINESS_READY = "ready"
E2E_READINESS_BLOCKED = "blocked"
E2E_READINESS_SKIPPED = "skipped"

INTERNAL_EVIDENCE_STATUS_PROVIDER_CANDIDATE = "provider_candidate"
INTERNAL_VERIFICATION_STATUS_PENDING_OFFICIAL_VERIFICATION = (
    "pending_official_verification"
)

PROFESSIONAL_BRIEF_SECTION_KEYS = (
    "overall_view",
    "business_view",
    "financial_view",
    "operating_quality_view",
    "industry_macro_view",
    "risk_view",
    "key_variables",
    "conclusion_boundary",
    "source_note",
)

_REQUEST_FIELDS = {
    "schema_version",
    "stock_code",
    "ts_code",
    "company_name_hint",
    "periods",
    "allow_network",
    "tushare_client_mode",
    "output_mode",
    "not_for_trading_advice",
}

_RESULT_FIELDS = {
    "schema_version",
    "readiness",
    "request_summary",
    "provider_candidate_bundle",
    "internal_analysis_brief",
    "skill_wrapper_response",
    "professional_compact_brief",
    "internal_payload",
    "blocked_reasons",
    "caveats",
    "not_official_verified",
    "not_for_trading_advice",
}

_REQUEST_SUMMARY_FIELDS = {
    "schema_version",
    "stock_code",
    "ts_code",
    "company_name_hint",
    "periods",
    "allow_network",
    "tushare_client_mode",
    "output_mode",
    "not_for_trading_advice",
}

_READINESS_FIELDS = {
    "schema_version",
    "status",
    "provider_candidate_ready",
    "internal_chain_ready",
    "wrapper_ready",
    "professional_brief_ready",
    "provider_candidate_count",
    "official_verified_count",
    "blocked_reasons",
    "allow_network",
    "tushare_client_mode",
    "not_official_verified",
    "not_for_trading_advice",
}

_BUNDLE_FIELDS = {
    "schema_version",
    "provider",
    "stock_code",
    "ts_code",
    "company_name_hint",
    "periods",
    "candidate_items",
    "internal_evidence_status",
    "internal_verification_status",
    "official_verified_count",
    "blocked_reasons",
    "caveats",
    "not_official_verified",
    "not_for_trading_advice",
}

_CANDIDATE_ITEM_FIELDS = {
    "schema_version",
    "item_id",
    "provider",
    "stock_code",
    "ts_code",
    "company_name_hint",
    "period",
    "period_label",
    "ann_date",
    "end_date",
    "candidate_key",
    "candidate_value",
    "source_table",
    "source_table_available",
    "value_status",
    "internal_evidence_status",
    "internal_verification_status",
    "not_official_verified",
    "not_for_trading_advice",
}

_PROFESSIONAL_BRIEF_FIELDS = {
    "schema_version",
    "stock_code",
    "ts_code",
    "company_name_hint",
    "title",
    *PROFESSIONAL_BRIEF_SECTION_KEYS,
    "not_for_trading_advice",
}

_PROFESSIONAL_SECTION_FIELDS = {
    "schema_version",
    "section_id",
    "title",
    "view",
    "not_for_trading_advice",
}

_INTERNAL_PAYLOAD_FIELDS = {
    "schema_version",
    "provider_candidate_count",
    "internal_analysis_brief_schema_version",
    "wrapper_response_schema_version",
    "wrapper_readiness_status",
    "not_official_verified",
    "not_for_trading_advice",
}

_FATAL_PROVIDER_BLOCKERS = {
    "api_client_required_when_network_disabled",
    "environment_credential_missing",
    "env_live_disallows_injected_client",
    "injected_client_required",
    "network_not_allowed_for_env_live",
    "provider_sdk_initialization_failed",
    "provider_sdk_unavailable",
}

_METRIC_SOURCE_TABLE = {
    "revenue": "income",
    "n_income_attr_p": "income",
    "total_profit": "income",
    "operate_profit": "income",
    "basic_eps": "income",
    "total_assets": "balancesheet",
    "total_liab": "balancesheet",
    "total_hldr_eqy_exc_min_int": "balancesheet",
    "accounts_receiv": "balancesheet",
    "inventories": "balancesheet",
    "n_cashflow_act": "cashflow",
    "c_cash_equ_end_period": "cashflow",
    "c_fr_sale_sg": "cashflow",
    "grossprofit_margin": "fina_indicator",
    "netprofit_margin": "fina_indicator",
    "roe": "fina_indicator",
    "debt_to_assets": "fina_indicator",
    "ar_turn": "fina_indicator",
    "inv_turn": "fina_indicator",
}

_TABLE_SELECTED_FIELDS = {
    "income": (
        "revenue",
        "n_income_attr_p",
        "total_profit",
        "operate_profit",
        "basic_eps",
    ),
    "balancesheet": (
        "total_assets",
        "total_liab",
        "total_hldr_eqy_exc_min_int",
        "accounts_receiv",
        "inventories",
    ),
    "cashflow": (
        "n_cashflow_act",
        "c_cash_equ_end_period",
        "c_fr_sale_sg",
    ),
    "fina_indicator": (
        "grossprofit_margin",
        "netprofit_margin",
        "roe",
        "debt_to_assets",
        "ar_turn",
        "inv_turn",
    ),
}

_RAW_OR_FILE_KEYS = {
    "accepted_manifest",
    "accepted_manifest_path",
    "cache_path",
    "env",
    "env_file",
    "fixture_path",
    "fixtures_path",
    "output_path",
    "pdf_bytes",
    "raw_http_response",
    "raw_provider_queue",
    "raw_tushare_provider_result",
    "source_url",
    "tushare_token",
    "tushare_token_path",
}

_SECRET_KEYS = {
    "api_key",
    "api_token",
    "auth",
    "authorization",
    "credential",
    "credentials",
    "secret",
    "token",
}

_ALLOWED_EXACT_TEXTS = {
    "TUSHARE_TOKEN",
    "has_html_artifact",
    "has_report_v1_artifact",
    "has_trading_advice",
    "not_for_trading_advice",
    "not_official_verified",
    "official_verified_count",
}

_INTERNAL_ALLOWED_TEXTS = {
    INTERNAL_EVIDENCE_STATUS_PROVIDER_CANDIDATE,
    INTERNAL_VERIFICATION_STATUS_PENDING_OFFICIAL_VERIFICATION,
}

_FORBIDDEN_MARKERS = (
    "token",
    ".env",
    "tushare_token",
    "official_metric_fact",
    "provider_official_conflict",
    "Report V1 artifact",
    "HTML artifact",
    "accepted manifest write",
    "output baseline write",
    "fixture write",
    "buy",
    "sell",
    "hold",
    "target price",
    "portfolio",
    "position",
    "technical signal",
    "trading advice",
    "investment advice",
    "OCR",
    "table extraction",
    "table extractor",
    "metric extraction",
    "provider-official reconciliation",
    "official value",
    "metric value",
    "page_number",
    "snippet",
    "source_url",
    "sha256",
    "cache_path",
    "output artifact path",
    "fixture path",
    "verified_fact",
    "live CNInfo",
    "PDF parser",
)

_FORBIDDEN_CJK_MARKERS = (
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
)

_USER_VISIBLE_ENGINEERING_LABELS = (
    "provider_candidate",
    "pending_official_verification",
    "pending verification",
    "official verification",
    "official_verified_count",
    "data gap",
    "evidence locator",
    "anchor map",
    "artifact cached",
    "reconciliation",
    "provider vs official",
    "\u5f85\u6838\u9a8c",
    "\u6570\u636e\u7f3a\u53e3",
    "\u63a8\u7406",
    "\u5b98\u65b9\u6838\u9a8c",
    "\u5c1a\u672a\u5b8c\u6210\u5b98\u65b9\u6838\u9a8c",
    "provider",
    "\u5019\u9009\u6570\u636e",
    "\u8bc1\u636e\u72b6\u6001",
    "\u53e3\u5f84\u4e00\u81f4\u6027",
    "\u7528\u6237\u81ea\u884c",
    "\u81ea\u884c\u5224\u65ad",
    "\u81ea\u884c\u8ddf\u8e2a",
    "\u9700\u8981\u7528\u6237",
    "\u5efa\u8bae\u7528\u6237",
)

_WORD_MARKERS = {"token", "buy", "sell", "hold", "portfolio", "position"}
_IDENTIFIER_SAFE_WORD_MARKERS = {"buy", "sell", "hold"}
_TS_CODE_RE = re.compile(r"^\d{6}\.(?:SH|SZ|BJ)$")
_STOCK_CODE_RE = re.compile(r"^\d{6}$")
_SECRET_LIKE_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._-]{8,}\b", re.IGNORECASE),
)


class ControlledRealTushareProfessionalCompactBriefPilotError(ValueError):
    """Raised when the professional compact brief pilot fails closed."""


class _DefaultFakeTushareClient:
    def __init__(self, *, ts_code: str, periods: Iterable[str]) -> None:
        self._ts_code = ts_code
        self._periods = list(periods)

    def income(self, **params: Any) -> list[dict[str, Any]]:
        period = params["period"]
        return [
            self._row(
                period,
                revenue=1000 if period == self._periods[0] else 260,
                n_income_attr_p=120 if period == self._periods[0] else 32,
                total_profit=150 if period == self._periods[0] else 40,
                operate_profit=140 if period == self._periods[0] else 38,
                basic_eps=1.23 if period == self._periods[0] else 0.32,
            )
        ]

    def balancesheet(self, **params: Any) -> list[dict[str, Any]]:
        period = params["period"]
        return [
            self._row(
                period,
                total_assets=3000 if period == self._periods[0] else 3180,
                total_liab=900 if period == self._periods[0] else 980,
                total_hldr_eqy_exc_min_int=2100 if period == self._periods[0] else 2200,
                accounts_receiv=330 if period == self._periods[0] else 350,
                inventories=80 if period == self._periods[0] else 85,
            )
        ]

    def cashflow(self, **params: Any) -> list[dict[str, Any]]:
        period = params["period"]
        return [
            self._row(
                period,
                n_cashflow_act=180 if period == self._periods[0] else 45,
                c_cash_equ_end_period=500 if period == self._periods[0] else 520,
                c_fr_sale_sg=980 if period == self._periods[0] else 255,
            )
        ]

    def fina_indicator(self, **params: Any) -> list[dict[str, Any]]:
        period = params["period"]
        return [
            self._row(
                period,
                grossprofit_margin=32.5 if period == self._periods[0] else 33.0,
                netprofit_margin=12.0 if period == self._periods[0] else 12.3,
                roe=16.0 if period == self._periods[0] else 4.2,
                debt_to_assets=30.0 if period == self._periods[0] else 30.8,
                ar_turn=4.0 if period == self._periods[0] else 1.0,
                inv_turn=8.0 if period == self._periods[0] else 2.0,
            )
        ]

    def _row(self, period: str, **values: Any) -> dict[str, Any]:
        row = {
            "ts_code": self._ts_code,
            "period": period,
            "ann_date": "20260430" if period.endswith("1231") else "20260429",
            "end_date": period,
        }
        row.update(values)
        return row


def build_controlled_real_tushare_professional_compact_brief_result(
    request: Mapping[str, Any],
    *,
    tushare_client: Any | None = None,
) -> dict[str, Any]:
    """Build the controlled Tushare to professional compact brief result."""

    validated_request = validate_controlled_real_tushare_professional_compact_brief_request(
        request
    )
    provider_result, provider_blockers = _build_provider_candidate_result(
        validated_request,
        tushare_client=tushare_client,
    )
    if provider_blockers or provider_result is None:
        return validate_controlled_real_tushare_professional_compact_brief_result(
            _blocked_result(validated_request, provider_blockers)
        )

    provider_candidate_bundle = build_provider_candidate_bundle_from_tushare_response(
        provider_result
    )
    fatal_blockers = [
        reason
        for reason in provider_candidate_bundle["blocked_reasons"]
        if reason in _FATAL_PROVIDER_BLOCKERS
    ]
    if fatal_blockers or not provider_candidate_bundle["candidate_items"]:
        return validate_controlled_real_tushare_professional_compact_brief_result(
            _blocked_result(
                validated_request,
                fatal_blockers or ["provider_candidate_items_missing"],
            )
        )

    internal_inputs = build_internal_analysis_inputs_from_provider_candidate_bundle(
        provider_candidate_bundle
    )
    context = build_ticker_research_context_skeleton(internal_inputs)
    scaffold = build_evidence_aware_research_pack_scaffold(context)
    orchestration_result = build_live_evidence_research_pack_orchestration_result(
        {
            "schema_version": (
                LIVE_EVIDENCE_RESEARCH_PACK_ORCHESTRATION_REQUEST_SCHEMA_VERSION
            ),
            "stock_code": validated_request["stock_code"],
            "ts_code": validated_request["ts_code"],
            "company_name_hint": validated_request["company_name_hint"],
            "components": {
                "ticker_research_context_skeleton": context,
                "evidence_aware_research_pack_scaffold": scaffold,
            },
            "requested_output": REQUESTED_OUTPUT_VERTICAL_SLICE_AND_MARKDOWN_PREVIEW,
            "allow_network": False,
            "not_for_trading_advice": True,
        }
    )
    if orchestration_result["readiness"]["status"] != "ready":
        return validate_controlled_real_tushare_professional_compact_brief_result(
            _blocked_result(validated_request, orchestration_result["blocked_reasons"])
        )

    wrapper_response = build_a_share_fundamental_skill_response(
        {
            "schema_version": A_SHARE_FUNDAMENTAL_SKILL_REQUEST_SCHEMA_VERSION,
            "stock_code": validated_request["stock_code"],
            "ts_code": validated_request["ts_code"],
            "company_name_hint": validated_request["company_name_hint"],
            "input_mode": INPUT_MODE_ORCHESTRATION_RESULT,
            "output_mode": OUTPUT_MODE_COMPACT_BRIEF,
            "orchestration_result": orchestration_result,
            "allow_network": False,
            "allow_file_writes": False,
            "not_for_trading_advice": True,
        }
    )
    if wrapper_response["readiness"]["status"] != "ready":
        return validate_controlled_real_tushare_professional_compact_brief_result(
            _blocked_result(
                validated_request,
                [reason["reason"] for reason in wrapper_response["blocked_reasons"]],
            )
        )

    professional_brief = build_professional_analyst_compact_brief(
        provider_candidate_bundle,
        internal_analysis_brief=wrapper_response["user_facing_analysis_brief"],
    )
    internal_payload = None
    if (
        validated_request["output_mode"]
        == OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF_AND_INTERNAL_PAYLOAD
    ):
        internal_payload = _build_internal_payload(
            provider_candidate_bundle,
            wrapper_response,
        )

    result = {
        "schema_version": (
            CONTROLLED_REAL_TUSHARE_PROFESSIONAL_COMPACT_BRIEF_RESULT_SCHEMA_VERSION
        ),
        "readiness": build_e2e_readiness(
            validated_request,
            provider_candidate_bundle=provider_candidate_bundle,
            wrapper_response=wrapper_response,
            professional_compact_brief=professional_brief,
        ),
        "request_summary": build_request_summary(validated_request),
        "provider_candidate_bundle": provider_candidate_bundle,
        "internal_analysis_brief": wrapper_response["user_facing_analysis_brief"],
        "skill_wrapper_response": wrapper_response,
        "professional_compact_brief": professional_brief,
        "internal_payload": internal_payload,
        "blocked_reasons": [],
        "caveats": _result_caveats(),
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }
    return validate_controlled_real_tushare_professional_compact_brief_result(result)


def validate_controlled_real_tushare_professional_compact_brief_request(
    request: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate a professional compact brief request."""

    source = _require_mapping(request, "request")
    _reject_bytes(source, "request")
    _reject_raw_or_secret_keys(source, "request")
    unsupported = sorted(set(source) - _REQUEST_FIELDS)
    if unsupported:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            f"request contains unsupported keys: {unsupported}"
        )
    assert_no_controlled_real_tushare_professional_brief_forbidden_markers(source)

    if source.get("schema_version") != (
        CONTROLLED_REAL_TUSHARE_PROFESSIONAL_COMPACT_BRIEF_REQUEST_SCHEMA_VERSION
    ):
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "schema_version must be "
            f"{CONTROLLED_REAL_TUSHARE_PROFESSIONAL_COMPACT_BRIEF_REQUEST_SCHEMA_VERSION}"
        )

    allow_network = source.get("allow_network", False)
    if not isinstance(allow_network, bool):
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "allow_network must be bool"
        )
    client_mode = source.get("tushare_client_mode", TUSHARE_CLIENT_MODE_FAKE)
    if client_mode not in SUPPORTED_TUSHARE_CLIENT_MODES:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "tushare_client_mode unsupported"
        )
    output_mode = source.get("output_mode", OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF)
    if output_mode not in SUPPORTED_OUTPUT_MODES:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "output_mode unsupported"
        )
    if source.get("not_for_trading_advice", True) is not True:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "not_for_trading_advice must be true"
        )

    stock_code = _optional_string(source.get("stock_code"), "stock_code")
    ts_code = _optional_string(source.get("ts_code"), "ts_code")
    if stock_code is None and ts_code is None:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "stock_code or ts_code is required"
        )
    if stock_code is not None and not _STOCK_CODE_RE.fullmatch(stock_code):
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "stock_code must be six digits"
        )
    if ts_code is not None and not _TS_CODE_RE.fullmatch(ts_code):
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "ts_code must be six digits plus market suffix"
        )
    if ts_code is None:
        ts_code = _derive_ts_code(stock_code)
    if stock_code is None:
        stock_code = ts_code.split(".", 1)[0]
    if ts_code.split(".", 1)[0] != stock_code:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "stock_code and ts_code mismatch"
        )

    result = {
        "schema_version": source["schema_version"],
        "stock_code": stock_code,
        "ts_code": ts_code,
        "company_name_hint": _optional_string(
            source.get("company_name_hint"),
            "company_name_hint",
        ),
        "periods": _periods(source.get("periods")),
        "allow_network": allow_network,
        "tushare_client_mode": client_mode,
        "output_mode": output_mode,
        "not_for_trading_advice": True,
    }
    assert_no_controlled_real_tushare_professional_brief_forbidden_markers(result)
    return result


def validate_controlled_real_tushare_professional_compact_brief_result(
    result: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the professional compact brief pilot result."""

    source = _require_mapping(result, "result")
    unsupported = sorted(set(source) - _RESULT_FIELDS)
    if unsupported:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            f"result contains unsupported keys: {unsupported}"
        )
    _require_fields(source, tuple(sorted(_RESULT_FIELDS)), "result")
    _assert_no_secret_like_anywhere(source)
    copied = deepcopy(dict(source))

    if copied["schema_version"] != (
        CONTROLLED_REAL_TUSHARE_PROFESSIONAL_COMPACT_BRIEF_RESULT_SCHEMA_VERSION
    ):
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "invalid result schema_version"
        )
    copied["readiness"] = _validate_readiness(copied["readiness"])
    copied["request_summary"] = _validate_request_summary(copied["request_summary"])
    if copied["provider_candidate_bundle"] is not None:
        copied["provider_candidate_bundle"] = _validate_provider_candidate_bundle(
            copied["provider_candidate_bundle"]
        )
    if copied["professional_compact_brief"] is not None:
        copied["professional_compact_brief"] = _validate_professional_brief(
            copied["professional_compact_brief"]
        )
    if copied["internal_payload"] is not None:
        copied["internal_payload"] = _validate_internal_payload(
            copied["internal_payload"]
        )
    _require_string_list(copied["blocked_reasons"], "blocked_reasons")
    _require_string_list(copied["caveats"], "caveats")
    _require_true(copied["not_official_verified"], "not_official_verified")
    _require_true(copied["not_for_trading_advice"], "not_for_trading_advice")
    _assert_result_consistency(copied)
    return copied


def build_provider_candidate_bundle_from_tushare_response(
    provider_candidate_result: Mapping[str, Any],
) -> dict[str, Any]:
    """Convert Tushare provider output into an internal candidate bundle."""

    _validate_provider_candidate_result(provider_candidate_result)
    source = deepcopy(dict(provider_candidate_result))
    bundle = {
        "schema_version": CONTROLLED_REAL_TUSHARE_PROVIDER_CANDIDATE_BUNDLE_SCHEMA_VERSION,
        "provider": PROVIDER_NAME,
        "stock_code": source.get("stock_code"),
        "ts_code": source.get("ts_code"),
        "company_name_hint": source.get("company_name_hint"),
        "periods": _string_values(source.get("periods")),
        "candidate_items": _candidate_items_from_provider_result(source),
        "internal_evidence_status": INTERNAL_EVIDENCE_STATUS_PROVIDER_CANDIDATE,
        "internal_verification_status": (
            INTERNAL_VERIFICATION_STATUS_PENDING_OFFICIAL_VERIFICATION
        ),
        "official_verified_count": 0,
        "blocked_reasons": _string_values(source.get("blocked_reasons")),
        "caveats": _string_values(source.get("caveats")),
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }
    return _validate_provider_candidate_bundle(bundle)


def build_internal_analysis_inputs_from_provider_candidate_bundle(
    provider_candidate_bundle: Mapping[str, Any],
) -> dict[str, Any]:
    """Build shaped inputs for the existing internal analysis chain."""

    bundle = _validate_provider_candidate_bundle(provider_candidate_bundle)
    return {
        "ts_code": bundle["ts_code"],
        "stock_code": bundle["stock_code"],
        "company_name_hint": bundle["company_name_hint"],
        "provider_candidate_financial_result": _provider_snapshot_from_bundle(bundle),
        "provider_candidate_metric_verification_queue": _verification_queue_from_bundle(
            bundle
        ),
        "not_for_trading_advice": True,
    }


def build_professional_analyst_compact_brief(
    provider_candidate_bundle: Mapping[str, Any],
    *,
    internal_analysis_brief: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the user-facing professional analyst compact brief."""

    del internal_analysis_brief
    bundle = _validate_provider_candidate_bundle(provider_candidate_bundle)
    metrics = _latest_metric_map(bundle)
    company = bundle["company_name_hint"] or bundle["stock_code"] or "该公司"
    revenue = metrics.get("revenue")
    profit = metrics.get("n_income_attr_p")
    cashflow = metrics.get("n_cashflow_act")
    receivables = metrics.get("accounts_receiv")
    margin = metrics.get("grossprofit_margin")

    overall = (
        f"从当前财务观察看，{company}的基本面判断应围绕收入、利润和现金流的匹配度展开；"
        "收入与利润若能同步改善，同时现金流保持跟进，经营韧性会更强。"
    )
    business = (
        "业务逻辑判断的重点不在单一财务科目，而在主营构成、订单交付、客户回款与利润表现是否能相互印证。"
        "如果经营活动能够稳定转化为收入和现金流，公司质量判断会更扎实。"
    )
    financial = _financial_view(revenue=revenue, profit=profit, margin=margin)
    operating = _operating_quality_view(
        profit=profit,
        cashflow=cashflow,
        receivables=receivables,
    )
    industry = (
        "行业和宏观变量对公司基本面的传导，需要落到订单、招标、交付、回款和盈利能力这些经营变量上；"
        "外部环境改善不能直接等同为公司质量改善。"
    )
    risk = (
        "核心风险在于收入增长、利润率、现金流和应收变化之间出现背离；"
        "若利润表现强于现金流或回款压力上升，经营质量判断需要打折。"
    )
    key_variables = [
        "收入与利润的同步性",
        "经营现金流与利润的匹配度",
        "应收账款和存货变化",
        "主营构成、订单交付和回款节奏",
        "利润率和资产负债结构的稳定性",
    ]
    boundary = (
        "本简报聚焦基本面质量、经营韧性和风险边界，不讨论估值区间或操作层面的动作。"
    )
    brief = {
        "schema_version": PROFESSIONAL_ANALYST_COMPACT_BRIEF_SCHEMA_VERSION,
        "stock_code": bundle["stock_code"],
        "ts_code": bundle["ts_code"],
        "company_name_hint": bundle["company_name_hint"],
        "title": f"{company}基本面专业简报",
        "overall_view": build_professional_section(
            "overall_view",
            "总体基本面判断",
            overall,
        ),
        "business_view": build_professional_section(
            "business_view",
            "公司业务逻辑判断",
            business,
        ),
        "financial_view": build_professional_section(
            "financial_view",
            "财务表现判断",
            financial,
        ),
        "operating_quality_view": build_professional_section(
            "operating_quality_view",
            "经营质量判断",
            operating,
        ),
        "industry_macro_view": build_professional_section(
            "industry_macro_view",
            "行业和宏观传导判断",
            industry,
        ),
        "risk_view": build_professional_section(
            "risk_view",
            "核心风险判断",
            risk,
        ),
        "key_variables": key_variables,
        "conclusion_boundary": boundary,
        "source_note": "数据来源：Tushare。",
        "not_for_trading_advice": True,
    }
    return _validate_professional_brief(brief)


def build_professional_section(
    section_id: str,
    title: str,
    view: str,
) -> dict[str, Any]:
    """Build one professional brief section."""

    section = {
        "schema_version": PROFESSIONAL_ANALYST_COMPACT_BRIEF_SECTION_SCHEMA_VERSION,
        "section_id": section_id,
        "title": title,
        "view": view,
        "not_for_trading_advice": True,
    }
    return _validate_professional_section(section, f"professional.{section_id}")


def build_request_summary(request: Mapping[str, Any]) -> dict[str, Any]:
    """Build a safe request summary."""

    validated = validate_controlled_real_tushare_professional_compact_brief_request(
        request
    )
    summary = {
        "schema_version": validated["schema_version"],
        "stock_code": validated["stock_code"],
        "ts_code": validated["ts_code"],
        "company_name_hint": validated["company_name_hint"],
        "periods": list(validated["periods"]),
        "allow_network": validated["allow_network"],
        "tushare_client_mode": validated["tushare_client_mode"],
        "output_mode": validated["output_mode"],
        "not_for_trading_advice": True,
    }
    return _validate_request_summary(summary)


def build_e2e_readiness(
    request: Mapping[str, Any],
    *,
    provider_candidate_bundle: Mapping[str, Any] | None = None,
    wrapper_response: Mapping[str, Any] | None = None,
    professional_compact_brief: Mapping[str, Any] | None = None,
    blocked_reasons: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Build readiness without fetching or writing."""

    validated = validate_controlled_real_tushare_professional_compact_brief_request(
        request
    )
    reasons = _dedupe_preserve_order(str(reason) for reason in blocked_reasons or [])
    bundle = (
        _validate_provider_candidate_bundle(provider_candidate_bundle)
        if provider_candidate_bundle is not None
        else None
    )
    candidate_count = len(bundle["candidate_items"]) if bundle else 0
    wrapper_ready = bool(
        isinstance(wrapper_response, Mapping)
        and isinstance(wrapper_response.get("readiness"), Mapping)
        and wrapper_response["readiness"].get("status") == "ready"
    )
    professional_ready = professional_compact_brief is not None
    status = E2E_READINESS_READY
    if reasons:
        status = (
            E2E_READINESS_SKIPPED
            if "environment_credential_missing" in reasons
            else E2E_READINESS_BLOCKED
        )
    elif not (candidate_count and wrapper_ready and professional_ready):
        status = E2E_READINESS_BLOCKED

    readiness = {
        "schema_version": CONTROLLED_REAL_TUSHARE_PROFESSIONAL_E2E_READINESS_SCHEMA_VERSION,
        "status": status,
        "provider_candidate_ready": bool(candidate_count),
        "internal_chain_ready": wrapper_ready,
        "wrapper_ready": wrapper_ready,
        "professional_brief_ready": professional_ready,
        "provider_candidate_count": candidate_count,
        "official_verified_count": 0,
        "blocked_reasons": reasons,
        "allow_network": validated["allow_network"],
        "tushare_client_mode": validated["tushare_client_mode"],
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }
    return _validate_readiness(readiness)


def assert_no_controlled_real_tushare_professional_brief_forbidden_markers(
    value: Any,
) -> None:
    """Reject hard forbidden markers and secret-like values."""

    finding = _find_forbidden_marker(value)
    if finding:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            f"controlled Tushare professional brief safety violation: {finding}"
        )


def assert_no_user_visible_engineering_labels(value: Any) -> None:
    """Reject engineering labels in user-visible professional brief content."""

    serialized = json.dumps(value, ensure_ascii=False)
    lowered = serialized.casefold()
    separator = _normalize_separator_text(serialized)
    normalized = _normalise_marker(serialized)
    for marker in _USER_VISIBLE_ENGINEERING_LABELS:
        marker_lower = marker.casefold()
        marker_normalized = _normalise_marker(marker)
        if (
            marker_lower in lowered
            or _normalize_separator_text(marker) in separator
            or (marker_normalized and marker_normalized in normalized)
            or marker in serialized
        ):
            raise ControlledRealTushareProfessionalCompactBriefPilotError(
                "professional brief contains user-visible engineering label"
            )


def _build_provider_candidate_result(
    request: Mapping[str, Any],
    *,
    tushare_client: Any | None,
) -> tuple[dict[str, Any] | None, list[str]]:
    mode = request["tushare_client_mode"]
    if mode == TUSHARE_CLIENT_MODE_INJECTED and tushare_client is None:
        return None, ["injected_client_required"]
    if mode == TUSHARE_CLIENT_MODE_ENV_LIVE and not request["allow_network"]:
        return None, ["network_not_allowed_for_env_live"]
    if mode == TUSHARE_CLIENT_MODE_ENV_LIVE and tushare_client is not None:
        return None, ["env_live_disallows_injected_client"]

    api_client = tushare_client
    if mode == TUSHARE_CLIENT_MODE_FAKE and api_client is None:
        api_client = _DefaultFakeTushareClient(
            ts_code=request["ts_code"],
            periods=request["periods"],
        )
    elif mode == TUSHARE_CLIENT_MODE_ENV_LIVE:
        if not os.environ.get("TUSHARE_TOKEN"):
            return None, ["environment_credential_missing"]
        return _build_env_live_provider_candidate(request)

    return _build_local_provider_candidate(
        ts_code=request["ts_code"],
        periods=request["periods"],
        company_name_hint=request["company_name_hint"],
        api_client=api_client,
    ), []


def _build_env_live_provider_candidate(
    request: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        from ..data_providers.tushare_financial_provider import (
            build_tushare_financial_provider_candidate,
        )
    except Exception:
        return None, ["provider_sdk_unavailable"]

    try:
        result = build_tushare_financial_provider_candidate(
            ts_code=request["ts_code"],
            periods=list(request["periods"]),
            company_name_hint=request["company_name_hint"],
            api_client=None,
            allow_network=True,
        )
    except Exception:
        return None, ["provider_sdk_initialization_failed"]
    return result, []


def _build_local_provider_candidate(
    *,
    ts_code: str,
    periods: list[str],
    company_name_hint: str | None,
    api_client: Any,
) -> dict[str, Any]:
    blocked_reasons: list[str] = []
    caveats: list[str] = []
    rows_by_table: dict[str, dict[str, Mapping[str, Any]]] = {
        table_name: {} for table_name in TARGET_TABLES
    }
    any_success = False

    for period in periods:
        for table_name in TARGET_TABLES:
            try:
                raw_response = getattr(api_client, table_name)(
                    ts_code=ts_code,
                    period=period,
                )
                rows = _records(raw_response)
            except Exception:
                blocked_reasons.append(f"api_exception:{table_name}:{period}")
                caveats.append(f"{table_name} provider request failed for period {period}")
                continue
            row = _first_matching_row(rows, ts_code=ts_code, period=period)
            if row is None:
                blocked_reasons.append(f"empty_response:{table_name}:{period}")
                caveats.append(f"{table_name} returned no provider row for period {period}")
                continue
            rows_by_table[table_name][period] = row
            any_success = True

    trend_table = []
    if any_success:
        trend_table = [
            _trend_row_from_tables(
                period=period,
                rows_by_table=rows_by_table,
            )
            for period in periods
        ]

    result = {
        "schema_version": "provider_candidate_financial_snapshot.v1",
        "provider": PROVIDER_NAME,
        "ts_code": ts_code,
        "stock_code": ts_code.split(".", 1)[0],
        "company_name_hint": company_name_hint,
        "periods": list(periods),
        "trend_table": trend_table,
        "blocked_reasons": _dedupe_preserve_order(blocked_reasons),
        "caveats": _dedupe_preserve_order(caveats),
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }
    _validate_provider_candidate_result(result)
    return result


def _trend_row_from_tables(
    *,
    period: str,
    rows_by_table: Mapping[str, Mapping[str, Mapping[str, Any]]],
) -> dict[str, Any]:
    selected_metrics: dict[str, Any] = {}
    source_tables_available = []
    ann_date = None
    end_date = period
    missing_fields = []
    for table_name in TARGET_TABLES:
        row = rows_by_table.get(table_name, {}).get(period)
        if row is None:
            for field in _TABLE_SELECTED_FIELDS[table_name]:
                selected_metrics[field] = None
                missing_fields.append(f"{table_name}.{field}")
            continue
        source_tables_available.append(table_name)
        ann_date = ann_date or row.get("ann_date")
        end_date = row.get("end_date") or row.get("period") or end_date
        for field in _TABLE_SELECTED_FIELDS[table_name]:
            selected_metrics[field] = row.get(field)
            if row.get(field) is None:
                missing_fields.append(f"{table_name}.{field}")
    return {
        "schema_version": "provider_candidate_financial_trend_table.v1",
        "provider": PROVIDER_NAME,
        "period_label": PERIOD_LABELS.get(period, period),
        "period": period,
        "ann_date": ann_date,
        "end_date": end_date,
        "source_tables_available": source_tables_available,
        "selected_metrics": selected_metrics,
        "missing_fields": missing_fields,
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }


def _first_matching_row(
    rows: list[Mapping[str, Any]],
    *,
    ts_code: str,
    period: str,
) -> Mapping[str, Any] | None:
    for row in rows:
        row_ts_code = str(row.get("ts_code", "")).strip()
        row_period = str(row.get("period") or row.get("end_date") or "").strip()
        if row_ts_code == ts_code and row_period == period:
            return row
    return None


def _records(response: Any) -> list[Mapping[str, Any]]:
    if response is None:
        return []
    if isinstance(response, Mapping):
        if "fields" in response and "items" in response:
            fields = response.get("fields")
            items = response.get("items")
            if isinstance(fields, list) and isinstance(items, list):
                return [
                    dict(zip(fields, item, strict=False))
                    for item in items
                    if isinstance(item, (list, tuple))
                ]
        return [response]
    if isinstance(response, list):
        return [item for item in response if isinstance(item, Mapping)]
    if hasattr(response, "to_dict"):
        try:
            rows = response.to_dict(orient="records")
        except TypeError:
            rows = response.to_dict()
        if isinstance(rows, list):
            return [item for item in rows if isinstance(item, Mapping)]
    return []


def _validate_provider_candidate_result(value: Any) -> dict[str, Any]:
    result = _require_mapping(value, "provider_candidate_result")
    if result.get("schema_version") != "provider_candidate_financial_snapshot.v1":
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "invalid provider candidate schema_version"
        )
    if result.get("provider") != PROVIDER_NAME:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "invalid provider candidate provider"
        )
    _require_true(result.get("not_official_verified"), "provider_candidate.not_official_verified")
    _require_true(result.get("not_for_trading_advice"), "provider_candidate.not_for_trading_advice")
    _assert_no_secret_like_anywhere(result)
    return deepcopy(dict(result))


def _blocked_result(
    request: Mapping[str, Any],
    blocked_reasons: Iterable[str],
) -> dict[str, Any]:
    reason_list = _dedupe_preserve_order(str(reason) for reason in blocked_reasons)
    return {
        "schema_version": (
            CONTROLLED_REAL_TUSHARE_PROFESSIONAL_COMPACT_BRIEF_RESULT_SCHEMA_VERSION
        ),
        "readiness": build_e2e_readiness(request, blocked_reasons=reason_list),
        "request_summary": build_request_summary(request),
        "provider_candidate_bundle": None,
        "internal_analysis_brief": None,
        "skill_wrapper_response": None,
        "professional_compact_brief": None,
        "internal_payload": None,
        "blocked_reasons": reason_list,
        "caveats": _result_caveats(),
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }


def _build_internal_payload(
    provider_candidate_bundle: Mapping[str, Any],
    wrapper_response: Mapping[str, Any],
) -> dict[str, Any]:
    payload = {
        "schema_version": CONTROLLED_REAL_TUSHARE_PROFESSIONAL_INTERNAL_PAYLOAD_SCHEMA_VERSION,
        "provider_candidate_count": len(provider_candidate_bundle["candidate_items"]),
        "internal_analysis_brief_schema_version": wrapper_response[
            "user_facing_analysis_brief"
        ]["schema_version"],
        "wrapper_response_schema_version": wrapper_response["schema_version"],
        "wrapper_readiness_status": wrapper_response["readiness"]["status"],
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }
    return _validate_internal_payload(payload)


def _candidate_items_from_provider_result(
    provider_result: Mapping[str, Any],
) -> list[dict[str, Any]]:
    trend_table = provider_result.get("trend_table")
    if not isinstance(trend_table, list):
        return []
    result = []
    for row in trend_table:
        if not isinstance(row, Mapping):
            continue
        selected = row.get("selected_metrics")
        if not isinstance(selected, Mapping):
            continue
        source_tables = _string_values(row.get("source_tables_available"))
        for candidate_key, candidate_value in selected.items():
            source_table = _METRIC_SOURCE_TABLE.get(str(candidate_key), "provider")
            item = {
                "schema_version": CONTROLLED_REAL_TUSHARE_PROVIDER_CANDIDATE_ITEM_SCHEMA_VERSION,
                "item_id": f"{row.get('period')}:{candidate_key}",
                "provider": PROVIDER_NAME,
                "stock_code": provider_result.get("stock_code"),
                "ts_code": provider_result.get("ts_code"),
                "company_name_hint": provider_result.get("company_name_hint"),
                "period": row.get("period"),
                "period_label": row.get("period_label"),
                "ann_date": row.get("ann_date"),
                "end_date": row.get("end_date"),
                "candidate_key": str(candidate_key),
                "candidate_value": deepcopy(candidate_value),
                "source_table": source_table,
                "source_table_available": source_table in source_tables,
                "value_status": "missing"
                if candidate_value is None
                else "present",
                "internal_evidence_status": INTERNAL_EVIDENCE_STATUS_PROVIDER_CANDIDATE,
                "internal_verification_status": (
                    INTERNAL_VERIFICATION_STATUS_PENDING_OFFICIAL_VERIFICATION
                ),
                "not_official_verified": True,
                "not_for_trading_advice": True,
            }
            result.append(_validate_candidate_item(item, "candidate_item"))
    return result


def _provider_snapshot_from_bundle(bundle: Mapping[str, Any]) -> dict[str, Any]:
    rows = []
    for period in bundle["periods"]:
        period_items = [
            item for item in bundle["candidate_items"] if item["period"] == period
        ]
        if not period_items:
            continue
        rows.append(
            {
                "schema_version": "provider_candidate_financial_trend_table.v1",
                "provider": PROVIDER_NAME,
                "period_label": period_items[0]["period_label"],
                "period": period,
                "ann_date": period_items[0]["ann_date"],
                "end_date": period_items[0]["end_date"],
                "source_tables_available": _dedupe_preserve_order(
                    item["source_table"]
                    for item in period_items
                    if item["source_table_available"]
                ),
                "selected_metrics": {
                    item["candidate_key"]: item["candidate_value"]
                    for item in period_items
                },
                "missing_fields": [
                    f"{item['source_table']}.{item['candidate_key']}"
                    for item in period_items
                    if item["value_status"] == "missing"
                ],
                "not_official_verified": True,
                "not_for_trading_advice": True,
            }
        )
    return {
        "schema_version": "provider_candidate_financial_snapshot.v1",
        "provider": PROVIDER_NAME,
        "ts_code": bundle["ts_code"],
        "stock_code": bundle["stock_code"],
        "company_name_hint": bundle["company_name_hint"],
        "periods": list(bundle["periods"]),
        "trend_table": rows,
        "blocked_reasons": list(bundle["blocked_reasons"]),
        "caveats": list(bundle["caveats"]),
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }


def _verification_queue_from_bundle(bundle: Mapping[str, Any]) -> dict[str, Any]:
    items = []
    for item in bundle["candidate_items"]:
        items.append(
            {
                "schema_version": "provider_candidate_metric_verification_item.v1",
                "provider": PROVIDER_NAME,
                "ts_code": bundle["ts_code"],
                "stock_code": bundle["stock_code"],
                "company_name_hint": bundle["company_name_hint"],
                "period": item["period"],
                "period_label": item["period_label"],
                "ann_date": item["ann_date"],
                "end_date": item["end_date"],
                "metric_key": item["candidate_key"],
                "metric_value": item["candidate_value"],
                "source_table": item["source_table"],
                "source_field": item["candidate_key"],
                "source_table_available": item["source_table_available"],
                "provider_native_unit": "provider_native_unit_unverified",
                "value_status": item["value_status"],
                "official_verification_status": (
                    INTERNAL_VERIFICATION_STATUS_PENDING_OFFICIAL_VERIFICATION
                ),
                "official_verification_required": True,
                "not_official_verified": True,
                "not_for_trading_advice": True,
                "caveats": ["provider candidate requires official checks"],
            }
        )
    return {
        "schema_version": "provider_candidate_metric_verification_queue.v1",
        "provider": PROVIDER_NAME,
        "ts_code": bundle["ts_code"],
        "stock_code": bundle["stock_code"],
        "company_name_hint": bundle["company_name_hint"],
        "periods": list(bundle["periods"]),
        "verification_items": items,
        "blocked_reasons": [],
        "caveats": ["provider candidate values require official checks"],
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }


def _latest_metric_map(bundle: Mapping[str, Any]) -> dict[str, Any]:
    by_period = {
        period: [
            item for item in bundle["candidate_items"] if item["period"] == period
        ]
        for period in bundle["periods"]
    }
    latest_period = next(
        (period for period in reversed(bundle["periods"]) if by_period.get(period)),
        None,
    )
    if latest_period is None:
        return {}
    return {
        item["candidate_key"]: item["candidate_value"]
        for item in by_period[latest_period]
    }


def _financial_view(*, revenue: Any, profit: Any, margin: Any) -> str:
    if _is_number(revenue) and _is_number(profit):
        base = (
            "收入和利润已经形成可观察基础，财务判断重点在于利润增长是否由主营收入支撑。"
        )
    else:
        base = "财务判断应先看收入、利润和盈利能力之间的方向是否一致。"
    if _is_number(margin):
        base += " 毛利率表现可作为盈利质量的重要观察点。"
    return base


def _operating_quality_view(*, profit: Any, cashflow: Any, receivables: Any) -> str:
    if _is_number(profit) and _is_number(cashflow):
        if cashflow >= profit:
            return (
                "经营现金流对利润有一定支撑，说明利润质量具备较好的观察起点；"
                "后续重点看这种匹配关系能否持续。"
            )
        return (
            "利润表现强于经营现金流时，经营质量判断需要更谨慎；"
            "回款节奏和现金转化能力是判断质量的关键。"
        )
    if _is_number(receivables):
        return "经营质量判断应重点看应收变化、回款节奏和利润转化效率。"
    return "经营质量判断应围绕现金流、回款和资产周转展开。"


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_provider_candidate_bundle(value: Any) -> dict[str, Any]:
    bundle = _require_mapping(value, "provider_candidate_bundle")
    unsupported = sorted(set(bundle) - _BUNDLE_FIELDS)
    if unsupported:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            f"provider_candidate_bundle contains unsupported keys: {unsupported}"
        )
    _require_fields(bundle, tuple(sorted(_BUNDLE_FIELDS)), "provider_candidate_bundle")
    result = deepcopy(dict(bundle))
    if result["schema_version"] != (
        CONTROLLED_REAL_TUSHARE_PROVIDER_CANDIDATE_BUNDLE_SCHEMA_VERSION
    ):
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "invalid provider_candidate_bundle schema_version"
        )
    if result["provider"] != PROVIDER_NAME:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "provider_candidate_bundle provider invalid"
        )
    _require_optional_string(result["stock_code"], "provider_candidate_bundle.stock_code")
    _require_optional_string(result["ts_code"], "provider_candidate_bundle.ts_code")
    _require_optional_string(
        result["company_name_hint"],
        "provider_candidate_bundle.company_name_hint",
    )
    _require_string_list(result["periods"], "provider_candidate_bundle.periods")
    result["candidate_items"] = [
        _validate_candidate_item(item, f"provider_candidate_bundle.candidate_items[{index}]")
        for index, item in enumerate(
            _require_list(
                result["candidate_items"],
                "provider_candidate_bundle.candidate_items",
            )
        )
    ]
    if result["internal_evidence_status"] != INTERNAL_EVIDENCE_STATUS_PROVIDER_CANDIDATE:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "provider_candidate_bundle internal_evidence_status invalid"
        )
    if (
        result["internal_verification_status"]
        != INTERNAL_VERIFICATION_STATUS_PENDING_OFFICIAL_VERIFICATION
    ):
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "provider_candidate_bundle internal_verification_status invalid"
        )
    if result["official_verified_count"] != 0:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "official_verified_count must be zero"
        )
    _require_string_list(
        result["blocked_reasons"],
        "provider_candidate_bundle.blocked_reasons",
    )
    _require_string_list(result["caveats"], "provider_candidate_bundle.caveats")
    _require_true(
        result["not_official_verified"],
        "provider_candidate_bundle.not_official_verified",
    )
    _require_true(
        result["not_for_trading_advice"],
        "provider_candidate_bundle.not_for_trading_advice",
    )
    _assert_no_secret_like_anywhere(result)
    return result


def _validate_candidate_item(value: Any, path: str) -> dict[str, Any]:
    item = _require_mapping(value, path)
    unsupported = sorted(set(item) - _CANDIDATE_ITEM_FIELDS)
    if unsupported:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            f"{path} contains unsupported keys: {unsupported}"
        )
    _require_fields(item, tuple(sorted(_CANDIDATE_ITEM_FIELDS)), path)
    result = deepcopy(dict(item))
    if result["schema_version"] != (
        CONTROLLED_REAL_TUSHARE_PROVIDER_CANDIDATE_ITEM_SCHEMA_VERSION
    ):
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            f"{path}.schema_version invalid"
        )
    for key in (
        "item_id",
        "provider",
        "period",
        "candidate_key",
        "source_table",
        "value_status",
        "internal_evidence_status",
        "internal_verification_status",
    ):
        _require_non_empty_string(result[key], f"{path}.{key}")
    for key in (
        "stock_code",
        "ts_code",
        "company_name_hint",
        "period_label",
        "ann_date",
        "end_date",
    ):
        _require_optional_string(result[key], f"{path}.{key}")
    if result["provider"] != PROVIDER_NAME:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            f"{path}.provider invalid"
        )
    if result["value_status"] not in {"present", "missing"}:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            f"{path}.value_status invalid"
        )
    if result["internal_evidence_status"] != INTERNAL_EVIDENCE_STATUS_PROVIDER_CANDIDATE:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            f"{path}.internal_evidence_status invalid"
        )
    if (
        result["internal_verification_status"]
        != INTERNAL_VERIFICATION_STATUS_PENDING_OFFICIAL_VERIFICATION
    ):
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            f"{path}.internal_verification_status invalid"
        )
    _require_bool(result["source_table_available"], f"{path}.source_table_available")
    _require_true(result["not_official_verified"], f"{path}.not_official_verified")
    _require_true(result["not_for_trading_advice"], f"{path}.not_for_trading_advice")
    _assert_no_secret_like_anywhere(result)
    return result


def _validate_professional_brief(value: Any) -> dict[str, Any]:
    brief = _require_mapping(value, "professional_compact_brief")
    unsupported = sorted(set(brief) - _PROFESSIONAL_BRIEF_FIELDS)
    if unsupported:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            f"professional_compact_brief contains unsupported keys: {unsupported}"
        )
    _require_fields(
        brief,
        tuple(sorted(_PROFESSIONAL_BRIEF_FIELDS)),
        "professional_compact_brief",
    )
    result = deepcopy(dict(brief))
    if result["schema_version"] != PROFESSIONAL_ANALYST_COMPACT_BRIEF_SCHEMA_VERSION:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "professional_compact_brief schema_version invalid"
        )
    _require_optional_string(result["stock_code"], "professional.stock_code")
    _require_optional_string(result["ts_code"], "professional.ts_code")
    _require_optional_string(
        result["company_name_hint"],
        "professional.company_name_hint",
    )
    _require_non_empty_string(result["title"], "professional.title")
    for key in (
        "overall_view",
        "business_view",
        "financial_view",
        "operating_quality_view",
        "industry_macro_view",
        "risk_view",
    ):
        result[key] = _validate_professional_section(result[key], key)
    _require_string_list(result["key_variables"], "professional.key_variables")
    if len(result["key_variables"]) < 3:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "key_variables must contain professional variables"
        )
    _require_non_empty_string(
        result["conclusion_boundary"],
        "professional.conclusion_boundary",
    )
    _require_non_empty_string(result["source_note"], "professional.source_note")
    _require_true(result["not_for_trading_advice"], "professional.not_for_trading_advice")
    assert_no_controlled_real_tushare_professional_brief_forbidden_markers(result)
    assert_no_user_visible_engineering_labels(result)
    return result


def _validate_professional_section(value: Any, path: str) -> dict[str, Any]:
    section = _require_mapping(value, path)
    unsupported = sorted(set(section) - _PROFESSIONAL_SECTION_FIELDS)
    if unsupported:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            f"{path} contains unsupported keys: {unsupported}"
        )
    _require_fields(section, tuple(sorted(_PROFESSIONAL_SECTION_FIELDS)), path)
    result = deepcopy(dict(section))
    if result["schema_version"] != PROFESSIONAL_ANALYST_COMPACT_BRIEF_SECTION_SCHEMA_VERSION:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            f"{path}.schema_version invalid"
        )
    _require_non_empty_string(result["section_id"], f"{path}.section_id")
    _require_non_empty_string(result["title"], f"{path}.title")
    view = _require_non_empty_string(result["view"], f"{path}.view")
    if len(view) < 24:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            f"{path}.view is too thin"
        )
    _require_true(result["not_for_trading_advice"], f"{path}.not_for_trading_advice")
    assert_no_controlled_real_tushare_professional_brief_forbidden_markers(result)
    assert_no_user_visible_engineering_labels(result)
    return result


def _validate_internal_payload(value: Any) -> dict[str, Any]:
    payload = _require_mapping(value, "internal_payload")
    unsupported = sorted(set(payload) - _INTERNAL_PAYLOAD_FIELDS)
    if unsupported:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            f"internal_payload contains unsupported keys: {unsupported}"
        )
    _require_fields(payload, tuple(sorted(_INTERNAL_PAYLOAD_FIELDS)), "internal_payload")
    result = deepcopy(dict(payload))
    if result["schema_version"] != (
        CONTROLLED_REAL_TUSHARE_PROFESSIONAL_INTERNAL_PAYLOAD_SCHEMA_VERSION
    ):
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "internal_payload schema_version invalid"
        )
    _require_non_negative_int(
        result["provider_candidate_count"],
        "internal_payload.provider_candidate_count",
    )
    for key in (
        "internal_analysis_brief_schema_version",
        "wrapper_response_schema_version",
        "wrapper_readiness_status",
    ):
        _require_non_empty_string(result[key], f"internal_payload.{key}")
    _require_true(result["not_official_verified"], "internal_payload.not_official_verified")
    _require_true(result["not_for_trading_advice"], "internal_payload.not_for_trading_advice")
    _assert_no_secret_like_anywhere(result)
    return result


def _validate_request_summary(value: Any) -> dict[str, Any]:
    summary = _require_mapping(value, "request_summary")
    unsupported = sorted(set(summary) - _REQUEST_SUMMARY_FIELDS)
    if unsupported:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            f"request_summary contains unsupported keys: {unsupported}"
        )
    _require_fields(summary, tuple(sorted(_REQUEST_SUMMARY_FIELDS)), "request_summary")
    result = deepcopy(dict(summary))
    if result["schema_version"] != (
        CONTROLLED_REAL_TUSHARE_PROFESSIONAL_COMPACT_BRIEF_REQUEST_SCHEMA_VERSION
    ):
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "request_summary schema_version invalid"
        )
    _require_optional_string(result["stock_code"], "request_summary.stock_code")
    _require_optional_string(result["ts_code"], "request_summary.ts_code")
    _require_optional_string(
        result["company_name_hint"],
        "request_summary.company_name_hint",
    )
    _require_string_list(result["periods"], "request_summary.periods")
    _require_bool(result["allow_network"], "request_summary.allow_network")
    if result["tushare_client_mode"] not in SUPPORTED_TUSHARE_CLIENT_MODES:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "request_summary tushare_client_mode invalid"
        )
    if result["output_mode"] not in SUPPORTED_OUTPUT_MODES:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "request_summary output_mode invalid"
        )
    _require_true(result["not_for_trading_advice"], "request_summary.not_for_trading_advice")
    assert_no_controlled_real_tushare_professional_brief_forbidden_markers(result)
    return result


def _validate_readiness(value: Any) -> dict[str, Any]:
    readiness = _require_mapping(value, "readiness")
    unsupported = sorted(set(readiness) - _READINESS_FIELDS)
    if unsupported:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            f"readiness contains unsupported keys: {unsupported}"
        )
    _require_fields(readiness, tuple(sorted(_READINESS_FIELDS)), "readiness")
    result = deepcopy(dict(readiness))
    if result["schema_version"] != (
        CONTROLLED_REAL_TUSHARE_PROFESSIONAL_E2E_READINESS_SCHEMA_VERSION
    ):
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "readiness schema_version invalid"
        )
    if result["status"] not in {
        E2E_READINESS_READY,
        E2E_READINESS_BLOCKED,
        E2E_READINESS_SKIPPED,
    }:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "readiness status invalid"
        )
    for key in (
        "provider_candidate_ready",
        "internal_chain_ready",
        "wrapper_ready",
        "professional_brief_ready",
        "allow_network",
    ):
        _require_bool(result[key], f"readiness.{key}")
    _require_non_negative_int(
        result["provider_candidate_count"],
        "readiness.provider_candidate_count",
    )
    if result["official_verified_count"] != 0:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "readiness official_verified_count must be zero"
        )
    _require_string_list(result["blocked_reasons"], "readiness.blocked_reasons")
    if result["tushare_client_mode"] not in SUPPORTED_TUSHARE_CLIENT_MODES:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "readiness tushare_client_mode invalid"
        )
    _require_true(result["not_official_verified"], "readiness.not_official_verified")
    _require_true(result["not_for_trading_advice"], "readiness.not_for_trading_advice")
    _assert_no_secret_like_anywhere(result)
    return result


def _assert_result_consistency(result: Mapping[str, Any]) -> None:
    if result["readiness"]["status"] == E2E_READINESS_READY:
        required = (
            "provider_candidate_bundle",
            "internal_analysis_brief",
            "skill_wrapper_response",
            "professional_compact_brief",
        )
        for key in required:
            if result[key] is None:
                raise ControlledRealTushareProfessionalCompactBriefPilotError(
                    f"ready result requires {key}"
                )
        if result["blocked_reasons"]:
            raise ControlledRealTushareProfessionalCompactBriefPilotError(
                "ready result cannot include blocked_reasons"
            )
    else:
        if not result["blocked_reasons"]:
            raise ControlledRealTushareProfessionalCompactBriefPilotError(
                "blocked or skipped result requires blocked_reasons"
            )
        for key in (
            "provider_candidate_bundle",
            "internal_analysis_brief",
            "skill_wrapper_response",
            "professional_compact_brief",
            "internal_payload",
        ):
            if result[key] is not None:
                raise ControlledRealTushareProfessionalCompactBriefPilotError(
                    f"blocked or skipped result must not include {key}"
                )


def _result_caveats() -> list[str]:
    return [
        "Controlled pilot keeps provider evidence status internal.",
        "Professional compact brief is the user-facing view.",
        "No external artifact is written by this pilot.",
    ]


def _periods(value: Any) -> list[str]:
    if value is None:
        return [SUPPORTED_PERIODS[0]]
    if not isinstance(value, list) or not value:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "periods must be a non-empty list"
        )
    result = []
    for item in value:
        if not isinstance(item, str) or not re.fullmatch(r"\d{8}", item):
            raise ControlledRealTushareProfessionalCompactBriefPilotError(
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


def _reject_raw_or_secret_keys(value: Any, path: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized = _normalise_marker(key_text)
            if key_text in _RAW_OR_FILE_KEYS or normalized in _RAW_OR_FILE_KEYS:
                raise ControlledRealTushareProfessionalCompactBriefPilotError(
                    f"{path} contains unsupported file or raw key"
                )
            if normalized in _SECRET_KEYS:
                raise ControlledRealTushareProfessionalCompactBriefPilotError(
                    f"{path} contains unsupported secret key"
                )
            _reject_raw_or_secret_keys(child, f"{path}.{key_text}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_raw_or_secret_keys(child, f"{path}[{index}]")


def _reject_bytes(value: Any, path: str) -> None:
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            f"{path} contains raw bytes"
        )
    if isinstance(value, Mapping):
        for key, child in value.items():
            _reject_bytes(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_bytes(child, f"{path}[{index}]")


def _find_forbidden_marker(value: Any, *, allow_internal_status: bool = False) -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text not in _ALLOWED_EXACT_TEXTS:
                key_finding = _text_forbidden_marker(
                    key_text,
                    allow_internal_status=False,
                )
                if key_finding:
                    return key_finding
            child_finding = _find_forbidden_marker(
                child,
                allow_internal_status=key_text
                in {"internal_evidence_status", "internal_verification_status"},
            )
            if child_finding:
                return child_finding
        return None
    if isinstance(value, (list, tuple, set)):
        for item in value:
            item_finding = _find_forbidden_marker(
                item,
                allow_internal_status=allow_internal_status,
            )
            if item_finding:
                return item_finding
        return None
    if isinstance(value, str):
        return _text_forbidden_marker(
            value,
            allow_internal_status=allow_internal_status,
        )
    return None


def _text_forbidden_marker(value: str, *, allow_internal_status: bool) -> str | None:
    if value in _ALLOWED_EXACT_TEXTS:
        return None
    if allow_internal_status and value in _INTERNAL_ALLOWED_TEXTS:
        return None
    if _looks_like_secret_text(value):
        return "secret_like_string"

    searchable_value = value
    for allowed in _ALLOWED_EXACT_TEXTS:
        searchable_value = searchable_value.replace(allowed, "")
    lowered = searchable_value.casefold()
    separator_normalized = _normalize_separator_text(searchable_value)
    normalized_marker = _normalise_marker(searchable_value)

    for marker in _FORBIDDEN_MARKERS:
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
                normalized_marker,
            ):
                return "forbidden_marker"
            continue
        if (
            marker_lower in lowered
            or marker_separator in separator_normalized
            or marker_normalized in normalized_marker
        ):
            return "forbidden_marker"
    if any(marker in searchable_value for marker in _FORBIDDEN_CJK_MARKERS):
        return "forbidden_marker"
    return None


def _assert_no_secret_like_anywhere(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text not in _ALLOWED_EXACT_TEXTS and _looks_like_secret_text(key_text):
                raise ControlledRealTushareProfessionalCompactBriefPilotError(
                    "secret_like_string"
                )
            _assert_no_secret_like_anywhere(child)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            _assert_no_secret_like_anywhere(item)
    elif isinstance(value, str) and _looks_like_secret_text(value):
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            "secret_like_string"
        )


def _looks_like_secret_text(value: str) -> bool:
    for pattern in _SECRET_LIKE_PATTERNS:
        if pattern.search(value):
            return True
    compact = value.strip()
    if len(compact) < 32 or re.search(r"\s", compact):
        return False
    if compact in _ALLOWED_EXACT_TEXTS:
        return False
    has_upper = any(char.isupper() for char in compact)
    has_lower = any(char.islower() for char in compact)
    has_digit = any(char.isdigit() for char in compact)
    return has_upper and has_lower and has_digit


def _normalise_marker(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().casefold()).strip("_")


def _normalize_separator_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[_-]+", " ", value.strip().casefold())).strip()


def _optional_string(value: Any, path: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            f"{path} must be string or null"
        )
    stripped = value.strip()
    return stripped or None


def _string_values(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, (list, tuple, set)):
        return [
            str(item).strip()
            for item in value
            if item not in (None, "") and str(item).strip()
        ]
    return [str(value).strip()] if str(value).strip() else []


def _dedupe_preserve_order(values: Iterable[Any]) -> list[Any]:
    result: list[Any] = []
    seen: set[str] = set()
    for value in values:
        marker = repr(value)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(value)
    return result


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            f"{field} must be a mapping"
        )
    return value


def _require_fields(value: Mapping[str, Any], fields: tuple[str, ...], path: str) -> None:
    missing = [field for field in fields if field not in value]
    if missing:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            f"{path} missing required fields: {missing}"
        )


def _require_optional_string(value: Any, path: str) -> None:
    if value is not None and not isinstance(value, str):
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            f"{path} must be string or null"
        )


def _require_non_empty_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            f"{path} must be a non-empty string"
        )
    return value


def _require_string_list(value: Any, path: str) -> list[str]:
    if not isinstance(value, list):
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            f"{path} must be a list"
        )
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise ControlledRealTushareProfessionalCompactBriefPilotError(
                f"{path}[{index}] must be string"
            )
    return value


def _require_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            f"{path} must be a list"
        )
    return value


def _require_bool(value: Any, path: str) -> None:
    if not isinstance(value, bool):
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            f"{path} must be bool"
        )


def _require_true(value: Any, path: str) -> None:
    if value is not True:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            f"{path} must be true"
        )


def _require_non_negative_int(value: Any, path: str) -> int:
    if not isinstance(value, int) or value < 0:
        raise ControlledRealTushareProfessionalCompactBriefPilotError(
            f"{path} must be a non-negative int"
        )
    return value


__all__ = [
    "CONTROLLED_REAL_TUSHARE_PROFESSIONAL_COMPACT_BRIEF_REQUEST_SCHEMA_VERSION",
    "CONTROLLED_REAL_TUSHARE_PROFESSIONAL_COMPACT_BRIEF_RESULT_SCHEMA_VERSION",
    "CONTROLLED_REAL_TUSHARE_PROVIDER_CANDIDATE_BUNDLE_SCHEMA_VERSION",
    "PROFESSIONAL_ANALYST_COMPACT_BRIEF_SCHEMA_VERSION",
    "PROFESSIONAL_ANALYST_COMPACT_BRIEF_SECTION_SCHEMA_VERSION",
    "CONTROLLED_REAL_TUSHARE_PROFESSIONAL_E2E_READINESS_SCHEMA_VERSION",
    "CONTROLLED_REAL_TUSHARE_PROVIDER_CANDIDATE_ITEM_SCHEMA_VERSION",
    "E2E_READINESS_BLOCKED",
    "E2E_READINESS_READY",
    "E2E_READINESS_SKIPPED",
    "INTERNAL_EVIDENCE_STATUS_PROVIDER_CANDIDATE",
    "INTERNAL_VERIFICATION_STATUS_PENDING_OFFICIAL_VERIFICATION",
    "OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF",
    "OUTPUT_MODE_PROFESSIONAL_COMPACT_BRIEF_AND_INTERNAL_PAYLOAD",
    "PROFESSIONAL_BRIEF_SECTION_KEYS",
    "SUPPORTED_OUTPUT_MODES",
    "SUPPORTED_TUSHARE_CLIENT_MODES",
    "TUSHARE_CLIENT_MODE_ENV_LIVE",
    "TUSHARE_CLIENT_MODE_FAKE",
    "TUSHARE_CLIENT_MODE_INJECTED",
    "ControlledRealTushareProfessionalCompactBriefPilotError",
    "assert_no_controlled_real_tushare_professional_brief_forbidden_markers",
    "assert_no_user_visible_engineering_labels",
    "build_controlled_real_tushare_professional_compact_brief_result",
    "build_e2e_readiness",
    "build_internal_analysis_inputs_from_provider_candidate_bundle",
    "build_professional_analyst_compact_brief",
    "build_professional_section",
    "build_provider_candidate_bundle_from_tushare_response",
    "build_request_summary",
    "validate_controlled_real_tushare_professional_compact_brief_request",
    "validate_controlled_real_tushare_professional_compact_brief_result",
]
