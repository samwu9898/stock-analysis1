# -*- coding: utf-8 -*-
"""Safety checks for AI analyst prompts and reports."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


FORBIDDEN_TERMS = (
    "买入",
    "卖出",
    "加仓",
    "减仓",
    "清仓",
    "止损",
    "止盈",
    "目标价",
    "满仓",
    "梭哈",
)

ALLOWED_CONTEXT_MARKERS = (
    "禁止词",
    "不得输出",
    "不得使用",
    "禁止输出",
    "明确禁止",
)


@dataclass(frozen=True)
class SafetyViolation:
    term: str
    context: str
    allowed_context: bool


AI_REPORT_FREE_TEXT_FIELDS = {
    "executive_summary",
    "confidence_explanation",
    "business_analysis",
    "financial_quality_analysis",
    "valuation_analysis",
    "industry_cycle_analysis",
    "final_summary",
    "analysis",
    "reason",
    "why_it_matters",
    "follow_up_question",
    "condition",
    "evidence_needed",
    "title",
    "heading",
}


def stringify_payload(payload: Any) -> str:
    if payload is None:
        return ""
    if isinstance(payload, str):
        return payload
    try:
        return json.dumps(payload, ensure_ascii=False, default=str)
    except TypeError:
        return str(payload)


def check_text_safety(payload: Any, allow_policy_context: bool = True) -> dict[str, Any]:
    """Detect restricted terms without mutating the source payload.

    The prompt is allowed to contain the terms in policy/prohibition sections.
    Final AI report body should normally have no detected terms.
    """

    text = stringify_payload(payload)
    violations: list[SafetyViolation] = []
    for term in FORBIDDEN_TERMS:
        start = 0
        while True:
            index = text.find(term, start)
            if index < 0:
                break
            context = text[max(0, index - 40): index + len(term) + 40]
            allowed = allow_policy_context and any(marker in context for marker in ALLOWED_CONTEXT_MARKERS)
            violations.append(SafetyViolation(term=term, context=context, allowed_context=allowed))
            start = index + len(term)

    blocked = [item for item in violations if not item.allowed_context]
    return {
        "safe": not blocked,
        "terms": sorted({item.term for item in violations}),
        "violations": [item.__dict__ for item in violations],
        "blocked_terms": sorted({item.term for item in blocked}),
        "blocked_count": len(blocked),
    }


def _garbled_text_reason(value: str) -> str | None:
    text = value.strip()
    if not text:
        return None

    compact = re.sub(r"\s+", "", text)
    question_count = text.count("?")
    cjk_count = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    alnum_count = sum(1 for ch in text if ch.isalnum())
    signal_length = cjk_count + alnum_count + question_count
    question_ratio = question_count / signal_length if signal_length else 0.0

    if re.search(r"\?{4,}", text):
        return "consecutive_question_marks"
    if re.fullmatch(r"(#+)?\?{3,}", compact):
        return "question_mark_title"
    if compact.startswith("##") and re.fullmatch(r"#+\?{2,}", compact):
        return "question_mark_title"
    if question_count >= 8 and question_ratio >= 0.20:
        return "high_question_mark_ratio"
    if cjk_count >= 8 and question_count >= 4 and question_ratio >= 0.08:
        return "abnormal_question_mark_ratio_in_chinese_text"
    return None


def is_garbled_text(value: Any) -> bool:
    """Return True when a displayed AI free-text value looks replacement-corrupt."""

    return isinstance(value, str) and _garbled_text_reason(value) is not None


def detect_garbled_text(report: Any) -> dict[str, Any]:
    """Detect replacement-question-mark corruption in AI report free-text values.

    The check intentionally scans values under known report free-text fields only.
    It does not inspect JSON schema field names or policy text.
    """

    findings: list[dict[str, Any]] = []

    def visit(value: Any, path: str, key: str | None = None) -> None:
        if isinstance(value, dict):
            for child_key, child_value in value.items():
                child_path = f"{path}.{child_key}" if path else str(child_key)
                visit(child_value, child_path, str(child_key))
            return
        if isinstance(value, list):
            for index, child_value in enumerate(value):
                visit(child_value, f"{path}[{index}]", key)
            return
        if key not in AI_REPORT_FREE_TEXT_FIELDS or not isinstance(value, str):
            return

        reason = _garbled_text_reason(value)
        if reason:
            findings.append(
                {
                    "path": path,
                    "reason": reason,
                    "question_count": value.count("?"),
                    "sample": value.strip()[:80],
                }
            )

    visit(report, "")
    status = "garbled_text_detected" if findings else "ok"
    return {
        "status": status,
        "garbled_text_detected": bool(findings),
        "warnings": (
            ["部分 AI 自由文本字段损坏，当前报告使用结构化 evidence fallback 生成。"]
            if findings
            else []
        ),
        "findings": findings,
    }
