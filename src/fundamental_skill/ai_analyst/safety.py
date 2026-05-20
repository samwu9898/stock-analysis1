# -*- coding: utf-8 -*-
"""Safety checks for AI analyst prompts and reports."""

from __future__ import annotations

import json
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
