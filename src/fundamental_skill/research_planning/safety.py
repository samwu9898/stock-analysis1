# -*- coding: utf-8 -*-
"""Recursive safety scanner for autonomous research planning payloads."""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Any


_MASKED_KEY = "<masked_key>"

_SECRET_KEY_RE = re.compile(
    r"(^|[_\-\s.])(token|secret|credential|credentials|password|passwd|bearer)($|[_\-\s.])"
    r"|api[_\-\s]*key|access[_\-\s]*token|tushare[_\-\s]*token",
    re.IGNORECASE,
)

_BEARER_RE = re.compile(r"\bbearer\s+[A-Za-z0-9._~+/=-]{8,}", re.IGNORECASE)
_EXPLICIT_TOKEN_VALUE_RE = re.compile(
    r"\b(sk|ghp|gho|glpat)-?[A-Za-z0-9_]{16,}\b"
    r"|\bAKIA[0-9A-Z]{16}\b"
    r"|\bTUSHARE_TOKEN\b"
    r"|\bapi[_\-\s]*key\s*[:=]"
    r"|\baccess[_\-\s]*token\s*[:=]",
    re.IGNORECASE,
)
_HIGH_ENTROPY_CANDIDATE_RE = re.compile(r"[A-Za-z0-9_+/=-]{32,}")
_MCP_URL_RE = re.compile(
    r"\bmcp://[^\s]+|\b(?:https?|wss?)://[^\s]+/(?:mcp|mcp/|mcp\?|mcp#)[^\s]*",
    re.IGNORECASE,
)
_DOTENV_PATH_RE = re.compile(r"(^|[\s/\\])\.env($|[\s/\\.:_-])", re.IGNORECASE)
_LOCAL_SECRET_PATH_RE = re.compile(
    r"([A-Za-z]:[\\/]|[\\/])[^ \n\r\t]*(secret|secrets|credential|credentials|token|tokens|"
    r"\.aws[\\/]credentials|id_rsa|id_dsa|id_ed25519)[^ \n\r\t]*",
    re.IGNORECASE,
)
_SENSITIVE_VALUE_LABEL_RE = re.compile(
    r"\b(TUSHARE_TOKEN|api[_\-\s]*key|access[_\-\s]*token|bearer credential)\b",
    re.IGNORECASE,
)

_VERIFIED_FACT_MARKERS = (
    "verified_fact",
    "verified fact",
    "auto_verified",
    "auto verified",
)
_FIXTURE_PROMOTION_MARKERS = (
    "fixture_promotion",
    "fixture promotion",
    "promote_fixture",
    "promote fixture",
    "promote_to_fixture",
)
_ACCEPTED_MANIFEST_MARKERS = (
    "accepted_manifest_update",
    "accepted manifest update",
    "accepted_manifest_write",
    "accepted manifest write",
    "write_accepted_manifest",
    "update_accepted_manifest",
    "accepted_artifact_manifest_update",
)
_PROVIDER_PRIMARY_SWITCH_MARKERS = (
    "provider_primary_switch",
    "provider primary switch",
    "primary_provider_switch",
    "switch_provider_primary",
    "set_provider_primary",
)
_REPORT_V1_UPDATE_MARKERS = (
    "research_report_v1_update",
    "research report v1 update",
    "update_research_report_v1",
    "research_report_v1_write",
)

_TRADING_KEY_MARKERS = {
    "buy_advice",
    "sell_advice",
    "target_price",
    "price_target",
    "position_size",
    "position_sizing",
    "portfolio_weight",
    "portfolio_allocation",
    "technical_signal",
    "trading_signal",
    "trade_signal",
}
_ALLOWED_POLICY_KEYS = {"not_for_trading_advice"}

_TRADING_PHRASE_RES = (
    re.compile(r"\b(buy|sell)\s+(this\s+)?(stock|share|security)\b", re.IGNORECASE),
    re.compile(r"\b(recommend|recommendation|rating)\s+(buy|sell)\b", re.IGNORECASE),
    re.compile(r"\b(buy|sell)\s+(recommendation|rating|signal)\b", re.IGNORECASE),
    re.compile(r"\btarget\s+price\b", re.IGNORECASE),
    re.compile(r"\bprice\s+target\b", re.IGNORECASE),
    re.compile(
        r"\b(position\s+size|position\s+sizing|portfolio\s+weight|portfolio\s+allocation|"
        r"portfolio\s+position|account\s+position)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\btechnical\s+(signal|indicator|analysis)\b", re.IGNORECASE),
    re.compile(r"\btrading\s+signal\b", re.IGNORECASE),
)

_TRADING_CN_PHRASES = (
    "\u4e70\u5165",
    "\u5356\u51fa",
    "\u76ee\u6807\u4ef7",
    "\u4ed3\u4f4d",
    "\u7ec4\u5408\u6743\u91cd",
    "\u6280\u672f\u4fe1\u53f7",
    "\u4ea4\u6613\u4fe1\u53f7",
    "\u589e\u6301",
    "\u51cf\u6301",
)


@dataclass(frozen=True)
class SafetyFinding:
    """A sanitized safety finding."""

    path: str
    category: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {"path": self.path, "category": self.category, "reason": self.reason}


def _normalise_marker(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _display_path(path: str) -> str:
    return path or "<root>"


def _append_key_path(path: str, key: str, masked: bool) -> str:
    segment = _MASKED_KEY if masked else str(key)
    return f"{path}.{segment}" if path else segment


def _append_index_path(path: str, index: int) -> str:
    return f"{path}[{index}]" if path else f"[{index}]"


def _is_secret_like_key(key: str) -> bool:
    return (
        bool(_SECRET_KEY_RE.search(key))
        or bool(_BEARER_RE.search(key))
        or bool(_EXPLICIT_TOKEN_VALUE_RE.search(key))
        or _looks_high_entropy_secret(key)
    )


def _entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = {char: value.count(char) for char in set(value)}
    length = len(value)
    return -sum((count / length) * math.log2(count / length) for count in counts.values())


def _looks_high_entropy_secret(value: str) -> bool:
    for candidate in _HIGH_ENTROPY_CANDIDATE_RE.findall(value):
        has_alpha = any(char.isalpha() for char in candidate)
        has_digit = any(char.isdigit() for char in candidate)
        if has_alpha and has_digit and _entropy(candidate) >= 4.2:
            return True
    return False


def _has_any_marker(text: str, markers: tuple[str, ...]) -> bool:
    lowered = text.lower()
    normalised = _normalise_marker(text)
    return any(marker in lowered or _normalise_marker(marker) in normalised for marker in markers)


def _scan_text(text: str, path: str, *, is_key: bool) -> list[SafetyFinding]:
    findings: list[SafetyFinding] = []
    display_path = _display_path(path)
    normalised = _normalise_marker(text)

    if is_key and normalised in _ALLOWED_POLICY_KEYS:
        return findings

    if is_key and normalised in _TRADING_KEY_MARKERS:
        findings.append(
            SafetyFinding(display_path, "trading_advice_marker", "trading advice key is not allowed")
        )
    if not is_key:
        if _BEARER_RE.search(text):
            findings.append(
                SafetyFinding(display_path, "credential", "bearer credential value is not allowed")
            )
        if _EXPLICIT_TOKEN_VALUE_RE.search(text) or _SENSITIVE_VALUE_LABEL_RE.search(text):
            findings.append(
                SafetyFinding(display_path, "credential", "token or API credential value is not allowed")
            )
        if _looks_high_entropy_secret(text):
            findings.append(
                SafetyFinding(display_path, "credential", "high-entropy secret-like value is not allowed")
            )
        if _MCP_URL_RE.search(text):
            findings.append(SafetyFinding(display_path, "mcp_url", "MCP URL is not allowed"))
        if _DOTENV_PATH_RE.search(text):
            findings.append(SafetyFinding(display_path, "dotenv_path", ".env path is not allowed"))
        if _LOCAL_SECRET_PATH_RE.search(text):
            findings.append(
                SafetyFinding(display_path, "secret_path", "local secret or credential path is not allowed")
            )

    if _has_any_marker(text, _VERIFIED_FACT_MARKERS):
        findings.append(
            SafetyFinding(display_path, "verified_fact_marker", "verified fact marker is not allowed")
        )
    if _has_any_marker(text, _FIXTURE_PROMOTION_MARKERS):
        findings.append(
            SafetyFinding(display_path, "fixture_promotion_marker", "fixture promotion marker is not allowed")
        )
    if _has_any_marker(text, _ACCEPTED_MANIFEST_MARKERS):
        findings.append(
            SafetyFinding(
                display_path,
                "accepted_manifest_marker",
                "accepted manifest write or update marker is not allowed",
            )
        )
    if _has_any_marker(text, _PROVIDER_PRIMARY_SWITCH_MARKERS):
        findings.append(
            SafetyFinding(
                display_path,
                "provider_primary_switch_marker",
                "provider primary switch marker is not allowed",
            )
        )
    if _has_any_marker(text, _REPORT_V1_UPDATE_MARKERS):
        findings.append(
            SafetyFinding(
                display_path,
                "research_report_v1_marker",
                "Research Report V1 write or update marker is not allowed",
            )
        )

    if not (is_key and normalised in _ALLOWED_POLICY_KEYS):
        for pattern in _TRADING_PHRASE_RES:
            if pattern.search(text):
                findings.append(
                    SafetyFinding(
                        display_path,
                        "trading_advice_marker",
                        "trading advice phrase is not allowed",
                    )
                )
                break
        if any(phrase in text for phrase in _TRADING_CN_PHRASES):
            findings.append(
                SafetyFinding(display_path, "trading_advice_marker", "trading advice phrase is not allowed")
            )

    return findings


def scan_payload_for_safety(payload: Any) -> list[SafetyFinding]:
    """Recursively scan a payload without leaking secret-like keys or values."""

    findings: list[SafetyFinding] = []

    def visit(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                key_text = str(key)
                masked = _is_secret_like_key(key_text)
                child_path = _append_key_path(path, key_text, masked)
                if masked:
                    findings.append(
                        SafetyFinding(
                            _display_path(child_path),
                            "credential",
                            "secret-like dictionary key is not allowed",
                        )
                    )
                else:
                    findings.extend(_scan_text(key_text, child_path, is_key=True))
                visit(child, child_path)
            return
        if isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, _append_index_path(path, index))
            return
        if isinstance(value, str):
            findings.extend(_scan_text(value, path, is_key=False))

    visit(payload, "")
    return findings


def validate_payload_safety(payload: Any) -> None:
    """Raise ValueError when the recursive safety scanner finds blocked content."""

    findings = scan_payload_for_safety(payload)
    if findings:
        details = "; ".join(
            f"{finding.category} at {finding.path}: {finding.reason}" for finding in findings
        )
        raise ValueError(f"planning payload safety violation: {details}")
