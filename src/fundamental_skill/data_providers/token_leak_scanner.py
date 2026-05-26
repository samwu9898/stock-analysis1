# -*- coding: utf-8 -*-
"""Token and local-connection leak scanner for provider comparison artifacts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlsplit

from .token_safety import MASKED_SECRET


_SECRET_KEYWORDS = r"token|key|secret|auth|credential|api[_-]?key|access[_-]?key|tushare[_-]?token"
_KEYED_SECRET_RE = re.compile(
    rf"(?P<key>\b(?:{_SECRET_KEYWORDS})\b)"
    r"(?P<sep>\s*[:=]\s*)"
    r"(?P<value>[^\s,;&]+)",
    flags=re.IGNORECASE,
)
_BEARER_RE = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]+", flags=re.IGNORECASE)
_MCP_URL_RE = re.compile(r"\bmcp(?:s)?://[^\s\"'<>]+|\bmcp\?[^\s\"'<>]*token[^\s\"'<>]*", flags=re.IGNORECASE)
_TOKEN_LIKE_RE = re.compile(
    r"\b(?=[A-Za-z0-9._~+/=-]{32,}\b)"
    r"(?=[A-Za-z0-9._~+/=-]*[A-Za-z])"
    r"(?=[A-Za-z0-9._~+/=-]*\d)"
    r"[A-Za-z0-9._~+/=-]+\b"
)
_TOKEN_LIKE_STRICT_RE = re.compile(
    r"\b(?=[A-Za-z0-9._~+/=-]{32,}\b)"
    r"(?=[A-Za-z0-9._~+/=-]*[a-z])"
    r"(?=[A-Za-z0-9._~+/=-]*[A-Z])"
    r"(?=[A-Za-z0-9._~+/=-]*\d)"
    r"[A-Za-z0-9._~+/=-]+\b"
)
_KEYWORD_RE = re.compile(rf"\b(?:{_SECRET_KEYWORDS})\b", flags=re.IGNORECASE)


@dataclass(frozen=True)
class TokenLeakFinding:
    path: str
    kind: str
    sanitized_excerpt: str

    def to_dict(self) -> dict[str, str]:
        return {"location": self.path, "sanitized_excerpt": self.sanitized_excerpt}


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
        parts = [f"{finding.path}:{finding.sanitized_excerpt}" for finding in self.findings]
        return "TokenLeakScanResult(ok=False, findings=[" + "; ".join(parts) + "])"


class TokenLeakError(RuntimeError):
    """Raised when secret-like text appears in comparison artifacts."""


def scan_for_token_leaks(payload: Any, *, secret_refs: Iterable[str | None] | None = None) -> TokenLeakScanResult:
    findings: list[TokenLeakFinding] = []
    refs = tuple(secret for secret in (secret_refs or ()) if secret)
    _scan(payload, path="$", findings=findings, secret_refs=refs)
    return TokenLeakScanResult(tuple(findings))


def assert_no_token_leaks(payload: Any, *, context: str = "payload", secret_refs: Iterable[str | None] | None = None) -> None:
    result = scan_for_token_leaks(payload, secret_refs=secret_refs)
    if not result.ok:
        raise TokenLeakError(f"{context} contains secret-like data: {result}")


def _scan(value: Any, *, path: str, findings: list[TokenLeakFinding], secret_refs: tuple[str, ...]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            item_path = _path_for_key(path, key_text)
            findings.extend(_find_in_text(key_text, path=f"{item_path}.__key__", secret_refs=secret_refs))
            if _looks_sensitive_key(str(key)) and item not in (None, "", MASKED_SECRET, "<unset>", "<empty>"):
                findings.append(TokenLeakFinding(item_path, "sensitive_key_value", MASKED_SECRET))
            _scan(item, path=item_path, findings=findings, secret_refs=secret_refs)
        return
    if isinstance(value, (list, tuple, set)):
        for index, item in enumerate(value):
            _scan(item, path=f"{path}[{index}]", findings=findings, secret_refs=secret_refs)
        return
    if isinstance(value, str):
        findings.extend(_find_in_text(value, path=path, secret_refs=secret_refs))


def _find_in_text(text: str, *, path: str, secret_refs: tuple[str, ...]) -> Iterable[TokenLeakFinding]:
    for secret in secret_refs:
        if secret and secret in text:
            yield TokenLeakFinding(path, "exact_secret", MASKED_SECRET)
    for regex, kind in (
        (_KEYED_SECRET_RE, "keyed_secret"),
        (_BEARER_RE, "bearer_secret"),
        (_MCP_URL_RE, "mcp_url_or_token"),
        (_TOKEN_LIKE_STRICT_RE, "token_like_value"),
    ):
        for match in regex.finditer(text):
            yield TokenLeakFinding(path, kind, _sanitized_excerpt(text, match.span()))
    for match in _TOKEN_LIKE_RE.finditer(text):
        if _has_nearby_secret_keyword(text, match.span()):
            yield TokenLeakFinding(path, "token_like_near_secret_keyword", MASKED_SECRET)
    yield from _find_url_query_leaks(text, path=path)


def _sanitized_excerpt(text: str, span: tuple[int, int]) -> str:
    del text, span
    return MASKED_SECRET


def _looks_sensitive_key(key: str) -> bool:
    return bool(_KEYWORD_RE.search(key))


def _has_nearby_secret_keyword(text: str, span: tuple[int, int]) -> bool:
    start, end = span
    window = text[max(0, start - 80):min(len(text), end + 80)]
    return bool(_KEYWORD_RE.search(window))


def _find_url_query_leaks(text: str, *, path: str) -> Iterable[TokenLeakFinding]:
    for token in re.findall(r"\b[a-z][a-z0-9+.-]*://[^\s\"'<>]+|\b[a-z][a-z0-9+.-]*\?[^\s\"'<>]+", text, flags=re.IGNORECASE):
        try:
            parsed = urlsplit(token)
        except ValueError:
            continue
        query = parsed.query
        if not query and "?" in token:
            query = token.split("?", 1)[1]
        for key, value in parse_qsl(query, keep_blank_values=True):
            if _looks_sensitive_key(key) and value not in ("", MASKED_SECRET, "<unset>", "<empty>"):
                yield TokenLeakFinding(path, "url_query_secret", MASKED_SECRET)
            elif _TOKEN_LIKE_RE.search(value) and (_looks_sensitive_key(key) or _has_nearby_secret_keyword(token, (token.find(value), token.find(value) + len(value)))):
                yield TokenLeakFinding(path, "url_query_token_like_value", MASKED_SECRET)


def _path_for_key(parent: str, key: str) -> str:
    if _looks_sensitive_key(key) or _TOKEN_LIKE_RE.search(key):
        return f"{parent}.<masked_key>"
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,63}", key):
        return f"{parent}.{key}"
    return f"{parent}.<key>"
