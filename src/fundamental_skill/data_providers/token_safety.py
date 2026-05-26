# -*- coding: utf-8 -*-
"""Helpers for masking provider secrets in diagnostics and errors."""

from __future__ import annotations

import re
from typing import Iterable


MASKED_SECRET = "<masked>"
UNSET_SECRET = "<unset>"
EMPTY_SECRET = "<empty>"

_KEYED_SECRET_RE = re.compile(
    r"(?P<key>\b(?:token|secret|api[_-]?key|access[_-]?key|tushare[_-]?token)\b)"
    r"(?P<sep>\s*[:=]\s*)"
    r"(?P<value>[^\s,;]+)",
    flags=re.IGNORECASE,
)
_BEARER_RE = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]+", flags=re.IGNORECASE)


def mask_secret(value: str | None) -> str:
    """Return a non-reversible display value for a secret-like string."""

    if value is None:
        return UNSET_SECRET
    if value == "":
        return EMPTY_SECRET
    return MASKED_SECRET


def sanitize_text(text: object, secrets: Iterable[str | None] | None = None) -> str:
    """Remove explicit and key-pattern secrets from diagnostic text."""

    sanitized = "" if text is None else str(text)
    for secret in secrets or ():
        if secret:
            sanitized = sanitized.replace(secret, MASKED_SECRET)
    sanitized = _KEYED_SECRET_RE.sub(lambda match: f"{match.group('key')}{match.group('sep')}{MASKED_SECRET}", sanitized)
    sanitized = _BEARER_RE.sub(f"Bearer {MASKED_SECRET}", sanitized)
    return sanitized


def sanitize_exception_message(exc: BaseException | object, secrets: Iterable[str | None] | None = None) -> str:
    """Return a sanitized exception message safe for logs and fetch status."""

    return sanitize_text(exc, secrets=secrets)

