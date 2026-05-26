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
_MCP_URL_RE = re.compile(r"\bmcp(?:s)?://[^\s\"'<>]+|\bmcp\?[^\s\"']*token[^\s\"']*", flags=re.IGNORECASE)
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
_SAFE_PLACEHOLDER_LITERALS = {
    "<masked>",
    "<MASKED>",
    "<redacted>",
    "<REDACTED>",
    "<unset>",
    "<empty>",
    "<TUSHARE_TOKEN>",
    "<YOUR_TOKEN>",
    "<YOUR_TUSHARE_TOKEN>",
}
# These prefixes are intentionally fake-only. They are exempted only by the
# tracked tests policy, never by docs or the default runtime scanner.
_SAFE_FAKE_PREFIXES = ("FAKE_", "TEST_", "EXAMPLE_")
_DOC_PATTERN_NAMES = {
    "token_like_value",
    "token_like_near_secret_keyword",
    "keyed_secret",
    "bearer_secret",
    "url_query_secret",
    "url_query_token_like_value",
}
_SAFE_KEYED_TYPE_LITERALS = {
    "Any",
    "Path",
    "bool",
    "dict",
    "float",
    "int",
    "list",
    "str",
    "tuple",
}
_DOC_FILE_IDENTIFIER_RE = re.compile(
    r"^(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9][A-Za-z0-9._-]*\.(?:csv|json|md|py|rst|toml|txt|yaml|yml)$",
    flags=re.IGNORECASE,
)
_SAFE_CODE_VALUE_RE = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*(?:\[[^\]]+\]|\([^)]*\))*$"
)


@dataclass(frozen=True)
class TokenLeakScanPolicy:
    """Context-specific scanner exemptions without weakening runtime scans."""

    name: str
    allow_safe_placeholders: bool = True
    allow_prefixed_fake_tokens: bool = False
    allow_doc_pattern_names: bool = False
    allow_doc_file_identifiers: bool = False
    allow_code_identifier_values: bool = False


STRICT_TOKEN_LEAK_POLICY = TokenLeakScanPolicy(name="strict")
TRACKED_DOCS_TOKEN_LEAK_POLICY = TokenLeakScanPolicy(
    name="tracked_docs",
    allow_doc_pattern_names=True,
    allow_doc_file_identifiers=True,
)
TRACKED_TESTS_TOKEN_LEAK_POLICY = TokenLeakScanPolicy(
    name="tracked_tests",
    allow_prefixed_fake_tokens=True,
    allow_code_identifier_values=True,
)
SOURCE_CODE_TOKEN_LEAK_POLICY = TokenLeakScanPolicy(
    name="source_code",
    allow_code_identifier_values=True,
)


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


def scan_for_token_leaks(
    payload: Any,
    *,
    secret_refs: Iterable[str | None] | None = None,
    policy: TokenLeakScanPolicy = STRICT_TOKEN_LEAK_POLICY,
) -> TokenLeakScanResult:
    findings: list[TokenLeakFinding] = []
    refs = tuple(secret for secret in (secret_refs or ()) if secret)
    _scan(payload, path="$", findings=findings, secret_refs=refs, policy=policy)
    return TokenLeakScanResult(tuple(findings))


def assert_no_token_leaks(
    payload: Any,
    *,
    context: str = "payload",
    secret_refs: Iterable[str | None] | None = None,
    policy: TokenLeakScanPolicy = STRICT_TOKEN_LEAK_POLICY,
) -> None:
    result = scan_for_token_leaks(payload, secret_refs=secret_refs, policy=policy)
    if not result.ok:
        raise TokenLeakError(f"{context} contains secret-like data: {result}")


def _scan(
    value: Any,
    *,
    path: str,
    findings: list[TokenLeakFinding],
    secret_refs: tuple[str, ...],
    policy: TokenLeakScanPolicy,
) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            item_path = _path_for_key(path, key_text)
            findings.extend(_find_in_text(key_text, path=f"{item_path}.__key__", secret_refs=secret_refs, policy=policy))
            if _looks_sensitive_key(str(key)) and not _is_allowed_sensitive_value(item, policy):
                findings.append(TokenLeakFinding(item_path, "sensitive_key_value", MASKED_SECRET))
            _scan(item, path=item_path, findings=findings, secret_refs=secret_refs, policy=policy)
        return
    if isinstance(value, (list, tuple, set)):
        for index, item in enumerate(value):
            _scan(item, path=f"{path}[{index}]", findings=findings, secret_refs=secret_refs, policy=policy)
        return
    if isinstance(value, str):
        findings.extend(_find_in_text(value, path=path, secret_refs=secret_refs, policy=policy))


def _find_in_text(
    text: str,
    *,
    path: str,
    secret_refs: tuple[str, ...],
    policy: TokenLeakScanPolicy,
) -> Iterable[TokenLeakFinding]:
    for secret in secret_refs:
        if secret and secret in text:
            yield TokenLeakFinding(path, "exact_secret", MASKED_SECRET)
    for match in _KEYED_SECRET_RE.finditer(text):
        if _is_safe_keyed_non_secret(match.group("key"), match.group("sep"), match.group("value"), policy):
            continue
        if not _is_allowed_literal(match.group("value"), policy):
            yield TokenLeakFinding(path, "keyed_secret", _sanitized_excerpt(text, match.span()))
    for match in _BEARER_RE.finditer(text):
        credential = match.group(0).split(None, 1)[1]
        if not _is_allowed_literal(credential, policy):
            yield TokenLeakFinding(path, "bearer_secret", _sanitized_excerpt(text, match.span()))
    for match in _MCP_URL_RE.finditer(text):
        if not _is_allowed_mcp_placeholder(match.group(0), policy):
            yield TokenLeakFinding(path, "mcp_url_or_token", _sanitized_excerpt(text, match.span()))
    for match in _TOKEN_LIKE_STRICT_RE.finditer(text):
        candidate = match.group(0)
        if _is_allowed_token_like_candidate(candidate, text=text, span=match.span(), policy=policy):
            continue
        yield TokenLeakFinding(path, "token_like_value", _sanitized_excerpt(text, match.span()))
    for match in _TOKEN_LIKE_RE.finditer(text):
        candidate = match.group(0)
        if _is_allowed_token_like_candidate(candidate, text=text, span=match.span(), policy=policy):
            continue
        if _has_nearby_secret_keyword(text, match.span()):
            yield TokenLeakFinding(path, "token_like_near_secret_keyword", MASKED_SECRET)
    yield from _find_url_query_leaks(text, path=path, policy=policy)


def _sanitized_excerpt(text: str, span: tuple[int, int]) -> str:
    del text, span
    return MASKED_SECRET


def _looks_sensitive_key(key: str) -> bool:
    return bool(_KEYWORD_RE.search(key))


def _is_allowed_sensitive_value(value: Any, policy: TokenLeakScanPolicy) -> bool:
    if value in (None, ""):
        return True
    if isinstance(value, str):
        return _is_allowed_literal(value, policy)
    return False


def _is_safe_keyed_non_secret(key: str, separator: str, value: object, policy: TokenLeakScanPolicy) -> bool:
    key_name = key.lower().replace("_", "-")
    source_value = str(value).strip()
    if policy.allow_code_identifier_values and source_value.startswith(("{", "(")):
        return True
    raw_value = source_value.strip("`'\".,;:)]")
    if policy.allow_code_identifier_values and _is_safe_code_value(raw_value):
        return True
    if policy.allow_code_identifier_values and key_name == "key" and bool(_SAFE_CODE_VALUE_RE.fullmatch(raw_value)):
        return True
    if ":" not in separator:
        return False
    return _normalize_candidate(value) in _SAFE_KEYED_TYPE_LITERALS


def _is_safe_code_value(value: str) -> bool:
    if _TOKEN_LIKE_RE.fullmatch(value):
        return False
    if value.startswith("{") and "}" in value and not _TOKEN_LIKE_RE.search(value):
        return True
    if any(char in value for char in "().[]") and re.fullmatch(r"[A-Za-z0-9_().\[\]]+", value):
        return True
    if _SAFE_CODE_VALUE_RE.fullmatch(value):
        return True
    return bool(re.fullmatch(r"\([A-Za-z_][A-Za-z0-9_]*", value))


def _is_allowed_literal(value: object, policy: TokenLeakScanPolicy) -> bool:
    literal = _normalize_candidate(value)
    if not literal:
        return True
    value_part = literal.split("=", 1)[1] if "=" in literal else literal
    if policy.allow_safe_placeholders and value_part in _SAFE_PLACEHOLDER_LITERALS:
        return True
    if policy.allow_prefixed_fake_tokens and value_part.upper().startswith(_SAFE_FAKE_PREFIXES):
        return True
    if policy.allow_doc_pattern_names and value_part in _DOC_PATTERN_NAMES:
        return True
    return False


def _is_allowed_token_like_candidate(
    candidate: str,
    *,
    text: str,
    span: tuple[int, int],
    policy: TokenLeakScanPolicy,
) -> bool:
    literal = _normalize_candidate(candidate)
    if _is_allowed_literal(literal, policy):
        return True
    del text, span
    if policy.allow_doc_file_identifiers and _DOC_FILE_IDENTIFIER_RE.fullmatch(literal):
        return True
    return False


def _is_allowed_mcp_placeholder(value: str, policy: TokenLeakScanPolicy) -> bool:
    text = _normalize_candidate(value)
    if "://" in text:
        return False
    if "?" not in text:
        return False
    query = text.split("?", 1)[1]
    pairs = parse_qsl(query, keep_blank_values=True)
    if not pairs and policy.allow_doc_pattern_names and _looks_sensitive_key(query):
        return True
    for key, item in pairs:
        if _looks_sensitive_key(key):
            if item:
                return _is_allowed_literal(item, policy)
            return policy.allow_doc_pattern_names
    return False


def _normalize_candidate(value: object) -> str:
    return str(value).strip().strip("`'\".,;:)]}")


def _has_nearby_secret_keyword(text: str, span: tuple[int, int]) -> bool:
    start, end = span
    window = text[max(0, start - 80):min(len(text), end + 80)]
    return bool(_KEYWORD_RE.search(window))


def _find_url_query_leaks(text: str, *, path: str, policy: TokenLeakScanPolicy) -> Iterable[TokenLeakFinding]:
    for token in re.findall(r"\b[a-z][a-z0-9+.-]*://[^\s\"'<>]+|\b[a-z][a-z0-9+.-]*\?[^\s\"'<>]+", text, flags=re.IGNORECASE):
        try:
            parsed = urlsplit(token)
        except ValueError:
            continue
        query = parsed.query
        if not query and "?" in token:
            query = token.split("?", 1)[1]
        for key, value in parse_qsl(query, keep_blank_values=True):
            if _is_allowed_literal(value, policy):
                continue
            if _looks_sensitive_key(key) and value:
                yield TokenLeakFinding(path, "url_query_secret", MASKED_SECRET)
            elif _TOKEN_LIKE_RE.search(value) and (_looks_sensitive_key(key) or _has_nearby_secret_keyword(token, (token.find(value), token.find(value) + len(value)))):
                yield TokenLeakFinding(path, "url_query_token_like_value", MASKED_SECRET)


def _path_for_key(parent: str, key: str) -> str:
    if _looks_sensitive_key(key) or _TOKEN_LIKE_RE.search(key):
        return f"{parent}.<masked_key>"
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,63}", key):
        return f"{parent}.{key}"
    return f"{parent}.<key>"
