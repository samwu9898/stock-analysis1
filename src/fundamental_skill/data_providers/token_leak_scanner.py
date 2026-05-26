# -*- coding: utf-8 -*-
"""Token and local-connection leak scanner for provider comparison artifacts."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .token_safety import MASKED_SECRET, sanitize_text


_KEYED_SECRET_RE = re.compile(
    r"(?P<key>\b(?:token|secret|api[_-]?key|access[_-]?key|tushare[_-]?token)\b)"
    r"(?P<sep>\s*[:=]\s*)"
    r"(?P<value>[^\s,;&]+)",
    flags=re.IGNORECASE,
)
_BEARER_RE = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]+", flags=re.IGNORECASE)
_MCP_URL_RE = re.compile(r"\bmcp(?:s)?://[^\s\"'<>]+|\bmcp\?[^\s\"'<>]*token[^\s\"'<>]*", flags=re.IGNORECASE)
_HIGH_ENTROPY_RE = re.compile(r"\b(?=[A-Za-z0-9._~+/=-]{32,}\b)(?=[A-Za-z0-9._~+/=-]*[A-Za-z])(?=[A-Za-z0-9._~+/=-]*\d)[A-Za-z0-9._~+/=-]+\b")


@dataclass(frozen=True)
class TokenLeakFinding:
    path: str
    kind: str
    sanitized_excerpt: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class TokenLeakScanResult:
    findings: tuple[TokenLeakFinding, ...]

    @property
    def ok(self) -> bool:
        return not self.findings

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "findings": [finding.to_dict() for finding in self.findings]}

    def __str__(self) -> str:
        if self.ok:
            return "TokenLeakScanResult(ok=True)"
        parts = [f"{finding.path}:{finding.kind}:{finding.sanitized_excerpt}" for finding in self.findings]
        return "TokenLeakScanResult(ok=False, findings=[" + "; ".join(parts) + "])"


class TokenLeakError(RuntimeError):
    """Raised when secret-like text appears in comparison artifacts."""


def scan_for_token_leaks(payload: Any) -> TokenLeakScanResult:
    findings: list[TokenLeakFinding] = []
    _scan(payload, path="$", findings=findings)
    return TokenLeakScanResult(tuple(findings))


def assert_no_token_leaks(payload: Any, *, context: str = "payload") -> None:
    result = scan_for_token_leaks(payload)
    if not result.ok:
        raise TokenLeakError(f"{context} contains secret-like data: {result}")


def _scan(value: Any, *, path: str, findings: list[TokenLeakFinding]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            item_path = f"{path}.{key}"
            if _looks_sensitive_key(str(key)) and item not in (None, "", MASKED_SECRET, "<unset>", "<empty>"):
                findings.append(TokenLeakFinding(item_path, "sensitive_key_value", MASKED_SECRET))
            _scan(item, path=item_path, findings=findings)
        return
    if isinstance(value, (list, tuple, set)):
        for index, item in enumerate(value):
            _scan(item, path=f"{path}[{index}]", findings=findings)
        return
    if isinstance(value, str):
        findings.extend(_find_in_text(value, path=path))


def _find_in_text(text: str, *, path: str) -> Iterable[TokenLeakFinding]:
    for regex, kind in (
        (_KEYED_SECRET_RE, "keyed_secret"),
        (_BEARER_RE, "bearer_secret"),
        (_MCP_URL_RE, "mcp_url_or_token"),
        (_HIGH_ENTROPY_RE, "token_like_value"),
    ):
        for match in regex.finditer(text):
            yield TokenLeakFinding(path, kind, _sanitized_excerpt(text, match.span()))


def _sanitized_excerpt(text: str, span: tuple[int, int]) -> str:
    start, end = span
    prefix = text[max(0, start - 20):start]
    suffix = text[end:min(len(text), end + 20)]
    raw_excerpt = f"{prefix}{MASKED_SECRET}{suffix}"
    return sanitize_text(raw_excerpt)


def _looks_sensitive_key(key: str) -> bool:
    return bool(re.search(r"\b(token|secret|api[_-]?key|access[_-]?key|tushare[_-]?token)\b", key, flags=re.IGNORECASE))
