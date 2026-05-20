# -*- coding: utf-8 -*-
"""Validation helpers for fundamental_skill outputs."""

from __future__ import annotations

import json
from typing import Any

from .constants import PROHIBITED_TRADING_TERMS
from .schema import FundamentalAnalysisResult


def validate_no_trading_instruction(text: str) -> list[str]:
    """Return prohibited trading terms found in text."""
    if not text:
        return []
    return [term for term in PROHIBITED_TRADING_TERMS if term in text]


def _model_payload_keys(result: FundamentalAnalysisResult) -> set[str]:
    payload: dict[str, Any] = result.model_dump()
    return set(payload.keys())


def validate_result(result: FundamentalAnalysisResult) -> list[str]:
    """Validate final fundamental_skill output semantics."""
    errors: list[str] = []

    summary_terms = validate_no_trading_instruction(result.trader_summary)
    if summary_terms:
        errors.append(
            "trader_summary contains prohibited trading instruction terms: "
            + ", ".join(summary_terms)
        )

    for idx, condition in enumerate(result.invalidation_conditions):
        terms = validate_no_trading_instruction(condition.action_hint_for_trader)
        if terms:
            errors.append(
                f"invalidation_conditions[{idx}].action_hint_for_trader contains "
                f"prohibited terms: {', '.join(terms)}"
            )

    if result.confidence == "low":
        if not result.missing_fields and not result.confidence_reason.strip():
            errors.append(
                "confidence=low requires missing_fields or a non-empty confidence_reason"
            )

    if result.status == "insufficient_data" and result.fundamental_score > 50:
        errors.append("status=insufficient_data requires fundamental_score <= 50")

    if result.status == "negative":
        forbidden_fields = {"supports_new_position"}
        present_forbidden = sorted(_model_payload_keys(result) & forbidden_fields)
        if present_forbidden:
            errors.append(
                "FundamentalAnalysisResult must not contain trading-action fields: "
                + ", ".join(present_forbidden)
            )

    has_high_risk = any(risk.severity == "high" for risk in result.risk_flags)
    if has_high_risk:
        summary = result.trader_summary
        if "高风险" not in summary and "需要重新评估" not in summary:
            errors.append(
                "high severity risk_flags require trader_summary to mention "
                "高风险 or 需要重新评估"
            )

    dumped = json.dumps(result.model_dump(mode="json"), ensure_ascii=False, default=str)
    terms = validate_no_trading_instruction(dumped)
    if terms:
        errors.append(
            "result JSON contains prohibited trading instruction terms: "
            + ", ".join(sorted(set(terms)))
        )

    return errors


def assert_valid_result(result: FundamentalAnalysisResult) -> None:
    errors = validate_result(result)
    if errors:
        raise ValueError("; ".join(errors))
