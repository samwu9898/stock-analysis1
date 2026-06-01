"""No-IO security identity normalization for official disclosure entrypoints."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any


SCHEMA_VERSION = "security_identity.v1"

STATUS_VALID = "valid"
STATUS_PARTIAL = "partial"
STATUS_BLOCKED = "blocked"
IDENTITY_STATUSES = {STATUS_VALID, STATUS_PARTIAL, STATUS_BLOCKED}

CONFIDENCE_HIGH = "high"
CONFIDENCE_MEDIUM = "medium"
CONFIDENCE_LOW = "low"
CONFIDENCE_BLOCKED = "blocked"
IDENTITY_CONFIDENCES = {
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    CONFIDENCE_LOW,
    CONFIDENCE_BLOCKED,
}

MARKET_CN_A = "CN_A"

EXCHANGE_SSE = "SSE"
EXCHANGE_SZSE = "SZSE"
EXCHANGE_BSE = "BSE"
SUPPORTED_EXCHANGES = {EXCHANGE_SSE, EXCHANGE_SZSE, EXCHANGE_BSE}

REJECTION_MISSING_STOCK_CODE_AND_COMPANY_NAME = "missing_stock_code_and_company_name"
REJECTION_INVALID_STOCK_CODE = "invalid_stock_code"
REJECTION_UNSUPPORTED_MARKET = "unsupported_market"
REJECTION_UNKNOWN_EXCHANGE = "unknown_exchange"
REJECTION_UNSUPPORTED_EXCHANGE_SUFFIX = "unsupported_exchange_suffix"
REJECTION_CODE_PREFIX_EXCHANGE_MISMATCH = "code_prefix_exchange_mismatch"
REJECTION_COMPANY_NAME_ONLY_REQUIRES_APPROVED_STATIC_IDENTITY_MAP = (
    "company_name_only_requires_approved_static_identity_map"
)
REJECTION_STOCK_CODE_COMPANY_NAME_MISMATCH = "stock_code_company_name_mismatch"
REJECTION_COMPANY_ALIAS_CONFLICT = "company_alias_conflict"
REJECTION_IDENTITY_CONFIDENCE_TOO_LOW = "identity_confidence_too_low"
REJECTION_FORBIDDEN_MARKER_DETECTED = "forbidden_marker_detected"
REJECTION_NOT_FOR_TRADING_ADVICE_REQUIRED = "not_for_trading_advice_required"
REJECTION_LIVE_LOOKUP_FORBIDDEN = "live_lookup_forbidden"
REJECTION_PROVIDER_LOOKUP_FORBIDDEN = "provider_lookup_forbidden"
REJECTION_PDF_PARSER_FORBIDDEN = "pdf_parser_forbidden"
REJECTION_OUTPUT_FIXTURE_MANIFEST_WRITE_FORBIDDEN = (
    "output_fixture_manifest_write_forbidden"
)
REJECTION_TRADING_ADVICE_FORBIDDEN = "trading_advice_forbidden"
REJECTION_INVALID_SCHEMA_VERSION = "invalid_schema_version"
REJECTION_INVALID_IDENTITY_SHAPE = "invalid_identity_shape"

BLOCKING_REJECTION_REASONS = {
    REJECTION_MISSING_STOCK_CODE_AND_COMPANY_NAME,
    REJECTION_INVALID_STOCK_CODE,
    REJECTION_UNSUPPORTED_MARKET,
    REJECTION_UNKNOWN_EXCHANGE,
    REJECTION_UNSUPPORTED_EXCHANGE_SUFFIX,
    REJECTION_CODE_PREFIX_EXCHANGE_MISMATCH,
    REJECTION_COMPANY_NAME_ONLY_REQUIRES_APPROVED_STATIC_IDENTITY_MAP,
    REJECTION_STOCK_CODE_COMPANY_NAME_MISMATCH,
    REJECTION_COMPANY_ALIAS_CONFLICT,
    REJECTION_IDENTITY_CONFIDENCE_TOO_LOW,
    REJECTION_FORBIDDEN_MARKER_DETECTED,
    REJECTION_NOT_FOR_TRADING_ADVICE_REQUIRED,
    REJECTION_LIVE_LOOKUP_FORBIDDEN,
    REJECTION_PROVIDER_LOOKUP_FORBIDDEN,
    REJECTION_PDF_PARSER_FORBIDDEN,
    REJECTION_OUTPUT_FIXTURE_MANIFEST_WRITE_FORBIDDEN,
    REJECTION_TRADING_ADVICE_FORBIDDEN,
    REJECTION_INVALID_SCHEMA_VERSION,
    REJECTION_INVALID_IDENTITY_SHAPE,
}

DETERMINISTIC_PREFIX_CAVEATS = [
    "deterministic prefix inference is not live verification",
    "company identity is not verified",
    "symbol existence is not verified",
]

COMPANY_NAME_ONLY_CAVEATS = [
    "no IO",
    "no provider lookup",
    "no live exchange lookup",
    "company name cannot be verified",
]

UNVERIFIED_COMPANY_HINT_CAVEATS = [
    "company name supplied by user but not verified against stock code",
    "security identity derived from stock code and exchange only",
]

SUFFIX_TO_EXCHANGE = {
    "SH": EXCHANGE_SSE,
    "SS": EXCHANGE_SSE,
    "SSE": EXCHANGE_SSE,
    "SZ": EXCHANGE_SZSE,
    "SZSE": EXCHANGE_SZSE,
    "BJ": EXCHANGE_BSE,
    "BSE": EXCHANGE_BSE,
}

PREFIX_EXCHANGE_RULES = (
    (("600", "601", "603", "605", "688"), EXCHANGE_SSE),
    (("000", "001", "002", "003", "300", "301"), EXCHANGE_SZSE),
    (("8", "4"), EXCHANGE_BSE),
)

_STOCK_TOKEN_RE = re.compile(
    r"(?<!\d)(?P<code>\d{6})(?:\.(?P<suffix>[A-Za-z]+))?(?![A-Za-z0-9])"
)
_WHOLE_CODELIKE_RE = re.compile(r"^\s*\d+(?:\.[A-Za-z]+)?\s*$")

_SAFETY_MARKERS: tuple[tuple[str, str], ...] = (
    ("tushare_token", REJECTION_FORBIDDEN_MARKER_DETECTED),
    ("token", REJECTION_FORBIDDEN_MARKER_DETECTED),
    (".env", REJECTION_FORBIDDEN_MARKER_DETECTED),
    ("provider live", REJECTION_PROVIDER_LOOKUP_FORBIDDEN),
    ("akshare", REJECTION_PROVIDER_LOOKUP_FORBIDDEN),
    ("tushare", REJECTION_PROVIDER_LOOKUP_FORBIDDEN),
    ("cninfo live", REJECTION_LIVE_LOOKUP_FORBIDDEN),
    ("sse live", REJECTION_LIVE_LOOKUP_FORBIDDEN),
    ("network", REJECTION_LIVE_LOOKUP_FORBIDDEN),
    ("http", REJECTION_LIVE_LOOKUP_FORBIDDEN),
    ("fetch", REJECTION_LIVE_LOOKUP_FORBIDDEN),
    ("download", REJECTION_LIVE_LOOKUP_FORBIDDEN),
    ("pdf parser", REJECTION_PDF_PARSER_FORBIDDEN),
    ("table extractor", REJECTION_PDF_PARSER_FORBIDDEN),
    ("parse pdf", REJECTION_PDF_PARSER_FORBIDDEN),
    ("accepted manifest write", REJECTION_OUTPUT_FIXTURE_MANIFEST_WRITE_FORBIDDEN),
    ("output baseline write", REJECTION_OUTPUT_FIXTURE_MANIFEST_WRITE_FORBIDDEN),
    ("fixture write", REJECTION_OUTPUT_FIXTURE_MANIFEST_WRITE_FORBIDDEN),
    ("buy", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("sell", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("hold", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("target price", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("portfolio", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("position", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("technical signal", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("trading advice", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("investment advice", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("metric extraction", REJECTION_FORBIDDEN_MARKER_DETECTED),
    ("official_metric_fact", REJECTION_FORBIDDEN_MARKER_DETECTED),
    ("provider_official_conflict", REJECTION_FORBIDDEN_MARKER_DETECTED),
    ("report v1", REJECTION_FORBIDDEN_MARKER_DETECTED),
    ("买入", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("卖出", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("持有", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("目标价", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("仓位", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("组合", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("技术信号", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("投资建议", REJECTION_TRADING_ADVICE_FORBIDDEN),
    ("下载", REJECTION_LIVE_LOOKUP_FORBIDDEN),
    ("网络", REJECTION_LIVE_LOOKUP_FORBIDDEN),
    ("联网", REJECTION_LIVE_LOOKUP_FORBIDDEN),
    ("解析pdf", REJECTION_PDF_PARSER_FORBIDDEN),
    ("pdf解析", REJECTION_PDF_PARSER_FORBIDDEN),
    ("表格抽取", REJECTION_PDF_PARSER_FORBIDDEN),
    ("指标抽取", REJECTION_FORBIDDEN_MARKER_DETECTED),
    ("正式研报", REJECTION_FORBIDDEN_MARKER_DETECTED),
    ("输出基线", REJECTION_OUTPUT_FIXTURE_MANIFEST_WRITE_FORBIDDEN),
    ("写入fixture", REJECTION_OUTPUT_FIXTURE_MANIFEST_WRITE_FORBIDDEN),
    ("写入accepted manifest", REJECTION_OUTPUT_FIXTURE_MANIFEST_WRITE_FORBIDDEN),
)


class SecurityIdentitySafetyError(ValueError):
    """Raised when a payload contains a forbidden security identity marker."""

    def __init__(self, marker: str, rejection_reason: str) -> None:
        super().__init__(f"forbidden security identity marker: {marker}")
        self.marker = marker
        self.rejection_reason = rejection_reason


def assert_no_security_identity_forbidden_markers(value: Any) -> None:
    """Recursively reject forbidden marker values in explicit caller input."""

    if isinstance(value, str):
        normalized = value.casefold()
        for marker, rejection_reason in _SAFETY_MARKERS:
            if marker.casefold() in normalized:
                raise SecurityIdentitySafetyError(marker, rejection_reason)
        return

    if isinstance(value, Mapping):
        for nested_key, nested_value in value.items():
            assert_no_security_identity_forbidden_markers(nested_key)
            assert_no_security_identity_forbidden_markers(nested_value)
        return

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for nested_value in value:
            assert_no_security_identity_forbidden_markers(nested_value)


def infer_exchange_from_stock_code(stock_code: str | None) -> str | None:
    """Infer a CN A-share exchange from a normalized stock code prefix."""

    normalized_stock_code = normalize_stock_code(stock_code)
    if normalized_stock_code is None:
        return None

    for prefixes, exchange in PREFIX_EXCHANGE_RULES:
        if normalized_stock_code.startswith(prefixes):
            return exchange
    return None


def normalize_stock_code(raw: Any) -> str | None:
    """Normalize a stock code token to six digits, without looking it up."""

    if raw is None:
        return None

    raw_text = str(raw).strip()
    match = _STOCK_TOKEN_RE.search(raw_text)
    if match is None:
        return None
    return match.group("code")


def normalize_exchange_suffix(raw_suffix: Any) -> str | None:
    """Normalize a supported explicit exchange suffix or exchange name."""

    if raw_suffix is None:
        return None
    suffix = str(raw_suffix).strip().upper()
    if suffix.startswith("."):
        suffix = suffix[1:]
    return SUFFIX_TO_EXCHANGE.get(suffix) or (
        suffix if suffix in SUPPORTED_EXCHANGES else None
    )


def normalize_company_name(value: Any) -> str | None:
    """Normalize an explicitly supplied company name hint."""

    if value is None:
        return None
    normalized = re.sub(r"\s+", " ", str(value).strip())
    return normalized or None


def parse_stock_code_and_exchange(raw: Any) -> tuple[str | None, str | None, str | None]:
    """Parse one explicit stock token and optional exchange suffix from text."""

    if raw is None:
        return None, None, None

    matches = list(_STOCK_TOKEN_RE.finditer(str(raw)))
    if len(matches) > 1:
        return None, None, REJECTION_INVALID_STOCK_CODE
    if not matches:
        return None, None, None

    match = matches[0]
    suffix = match.group("suffix")
    if suffix:
        exchange = normalize_exchange_suffix(suffix)
        if exchange is None:
            return match.group("code"), None, REJECTION_UNSUPPORTED_EXCHANGE_SUFFIX
        return match.group("code"), exchange, None
    return match.group("code"), None, None


def normalize_security_identity(payload: Any) -> dict[str, Any]:
    """Build a fail-closed security_identity.v1 object from explicit input."""

    raw_user_input, stock_input, exchange_input, market_input, company_input, aliases, not_for = (
        _extract_payload_fields(payload)
    )

    if not_for is not True:
        return _blocked_identity(
            raw_user_input=raw_user_input,
            reason=REJECTION_NOT_FOR_TRADING_ADVICE_REQUIRED,
            stock_code=stock_input,
            company_name=company_input,
            company_aliases=aliases if isinstance(aliases, list) else [],
            not_for_trading_advice=not_for,
        )

    try:
        assert_no_security_identity_forbidden_markers(_payload_values_for_safety(payload))
    except SecurityIdentitySafetyError as exc:
        return _blocked_identity(
            raw_user_input=raw_user_input,
            reason=exc.rejection_reason,
            stock_code=stock_input,
            company_name=company_input,
            company_aliases=aliases if isinstance(aliases, list) else [],
            not_for_trading_advice=True,
        )

    if aliases is not None and not isinstance(aliases, list):
        return _blocked_identity(
            raw_user_input=raw_user_input,
            reason=REJECTION_COMPANY_ALIAS_CONFLICT,
            stock_code=stock_input,
            company_name=company_input,
            company_aliases=[],
            not_for_trading_advice=True,
        )

    company_aliases = aliases or []
    try:
        assert_no_security_identity_forbidden_markers(company_aliases)
    except SecurityIdentitySafetyError as exc:
        return _blocked_identity(
            raw_user_input=raw_user_input,
            reason=exc.rejection_reason,
            stock_code=stock_input,
            company_name=company_input,
            company_aliases=company_aliases,
            not_for_trading_advice=True,
        )

    stock_code, explicit_exchange, parse_rejection = _resolve_stock_code_and_exchange(
        raw_user_input, stock_input, exchange_input
    )
    company_name = normalize_company_name(company_input) or _extract_company_hint(
        raw_user_input
    )

    if parse_rejection is not None:
        return _blocked_identity(
            raw_user_input=raw_user_input,
            reason=parse_rejection,
            stock_code=stock_input,
            normalized_stock_code=stock_code,
            company_name=company_name,
            company_aliases=company_aliases,
            not_for_trading_advice=True,
        )

    if stock_code is None and _is_invalid_code_like_input(stock_input or raw_user_input):
        return _blocked_identity(
            raw_user_input=raw_user_input,
            reason=REJECTION_INVALID_STOCK_CODE,
            stock_code=stock_input,
            company_name=company_name,
            company_aliases=company_aliases,
            not_for_trading_advice=True,
        )

    if market_input is not None and str(market_input).strip().upper() != MARKET_CN_A:
        return _blocked_identity(
            raw_user_input=raw_user_input,
            reason=REJECTION_UNSUPPORTED_MARKET,
            stock_code=stock_input,
            normalized_stock_code=stock_code,
            company_name=company_name,
            company_aliases=company_aliases,
            not_for_trading_advice=True,
        )

    if stock_code is None and company_name is None:
        return _blocked_identity(
            raw_user_input=raw_user_input,
            reason=REJECTION_MISSING_STOCK_CODE_AND_COMPANY_NAME,
            stock_code=stock_input,
            company_name=company_input,
            company_aliases=company_aliases,
            not_for_trading_advice=True,
        )

    if stock_code is None and company_name is not None:
        return _blocked_identity(
            raw_user_input=raw_user_input,
            reason=REJECTION_COMPANY_NAME_ONLY_REQUIRES_APPROVED_STATIC_IDENTITY_MAP,
            company_name=company_name,
            normalized_company_name=company_name,
            company_aliases=company_aliases,
            caveats=COMPANY_NAME_ONLY_CAVEATS,
            not_for_trading_advice=True,
        )

    if stock_code is None:
        return _blocked_identity(
            raw_user_input=raw_user_input,
            reason=REJECTION_INVALID_STOCK_CODE,
            stock_code=stock_input,
            company_name=company_name,
            company_aliases=company_aliases,
            not_for_trading_advice=True,
        )

    inferred_exchange = infer_exchange_from_stock_code(stock_code)
    if inferred_exchange is None:
        return _blocked_identity(
            raw_user_input=raw_user_input,
            reason=REJECTION_UNKNOWN_EXCHANGE,
            stock_code=stock_input,
            normalized_stock_code=stock_code,
            company_name=company_name,
            company_aliases=company_aliases,
            not_for_trading_advice=True,
        )

    exchange = explicit_exchange or inferred_exchange
    if exchange not in SUPPORTED_EXCHANGES:
        return _blocked_identity(
            raw_user_input=raw_user_input,
            reason=REJECTION_UNKNOWN_EXCHANGE,
            stock_code=stock_input,
            normalized_stock_code=stock_code,
            company_name=company_name,
            company_aliases=company_aliases,
            not_for_trading_advice=True,
        )

    if exchange != inferred_exchange:
        return _blocked_identity(
            raw_user_input=raw_user_input,
            reason=REJECTION_CODE_PREFIX_EXCHANGE_MISMATCH,
            stock_code=stock_input,
            normalized_stock_code=stock_code,
            exchange=exchange,
            market=MARKET_CN_A,
            company_name=company_name,
            normalized_company_name=company_name,
            company_aliases=company_aliases,
            conflicts=[REJECTION_CODE_PREFIX_EXCHANGE_MISMATCH],
            not_for_trading_advice=True,
        )

    caveats: list[str] = []
    confidence = CONFIDENCE_HIGH if explicit_exchange else CONFIDENCE_MEDIUM

    if not explicit_exchange:
        caveats.extend(DETERMINISTIC_PREFIX_CAVEATS)

    if company_name is not None:
        confidence = CONFIDENCE_MEDIUM
        caveats.extend(UNVERIFIED_COMPANY_HINT_CAVEATS)

    return {
        "schema_version": SCHEMA_VERSION,
        "raw_user_input": raw_user_input,
        "stock_code": stock_input,
        "normalized_stock_code": stock_code,
        "exchange": exchange,
        "market": MARKET_CN_A,
        "company_name": company_name,
        "normalized_company_name": company_name,
        "company_aliases": company_aliases,
        "identity_confidence": confidence,
        "identity_status": STATUS_VALID,
        "identity_conflicts": [],
        "rejection_reason": None,
        "caveats": _dedupe_preserve_order(caveats),
        "not_for_trading_advice": True,
    }


def validate_security_identity(identity: Any) -> dict[str, Any]:
    """Validate an identity object, returning a fail-closed identity object."""

    if not isinstance(identity, Mapping):
        return _blocked_identity(
            raw_user_input="",
            reason=REJECTION_INVALID_IDENTITY_SHAPE,
            not_for_trading_advice=None,
        )

    raw_user_input = str(identity.get("raw_user_input") or "")
    stock_code = identity.get("stock_code")
    normalized_stock_code = identity.get("normalized_stock_code")
    exchange = identity.get("exchange")
    market = identity.get("market")
    company_name = identity.get("company_name")
    normalized_company_name = identity.get("normalized_company_name")
    company_aliases = identity.get("company_aliases")
    not_for = identity.get("not_for_trading_advice")

    if not_for is not True:
        return _blocked_identity(
            raw_user_input=raw_user_input,
            reason=REJECTION_NOT_FOR_TRADING_ADVICE_REQUIRED,
            stock_code=stock_code,
            normalized_stock_code=normalized_stock_code,
            exchange=exchange,
            market=market,
            company_name=company_name,
            normalized_company_name=normalized_company_name,
            company_aliases=company_aliases if isinstance(company_aliases, list) else [],
            not_for_trading_advice=not_for,
        )

    try:
        assert_no_security_identity_forbidden_markers(
            {
                "raw_user_input": raw_user_input,
                "stock_code": stock_code,
                "normalized_stock_code": normalized_stock_code,
                "exchange": exchange,
                "market": market,
                "company_name": company_name,
                "normalized_company_name": normalized_company_name,
                "company_aliases": company_aliases,
                "identity_conflicts": identity.get("identity_conflicts"),
            }
        )
    except SecurityIdentitySafetyError as exc:
        return _blocked_identity(
            raw_user_input=raw_user_input,
            reason=exc.rejection_reason,
            stock_code=stock_code,
            normalized_stock_code=normalized_stock_code,
            exchange=exchange,
            market=market,
            company_name=company_name,
            normalized_company_name=normalized_company_name,
            company_aliases=company_aliases if isinstance(company_aliases, list) else [],
            not_for_trading_advice=True,
        )

    if identity.get("schema_version") != SCHEMA_VERSION:
        return _blocked_identity(
            raw_user_input=raw_user_input,
            reason=REJECTION_INVALID_SCHEMA_VERSION,
            stock_code=stock_code,
            normalized_stock_code=normalized_stock_code,
            exchange=exchange,
            market=market,
            company_name=company_name,
            normalized_company_name=normalized_company_name,
            company_aliases=company_aliases if isinstance(company_aliases, list) else [],
            not_for_trading_advice=True,
        )

    if not isinstance(company_aliases, list):
        return _blocked_identity(
            raw_user_input=raw_user_input,
            reason=REJECTION_COMPANY_ALIAS_CONFLICT,
            stock_code=stock_code,
            normalized_stock_code=normalized_stock_code,
            exchange=exchange,
            market=market,
            company_name=company_name,
            normalized_company_name=normalized_company_name,
            company_aliases=[],
            not_for_trading_advice=True,
        )

    if not isinstance(identity.get("identity_conflicts"), list):
        return _blocked_identity(
            raw_user_input=raw_user_input,
            reason=REJECTION_INVALID_IDENTITY_SHAPE,
            stock_code=stock_code,
            normalized_stock_code=normalized_stock_code,
            exchange=exchange,
            market=market,
            company_name=company_name,
            normalized_company_name=normalized_company_name,
            company_aliases=company_aliases,
            not_for_trading_advice=True,
        )

    if not isinstance(identity.get("caveats"), list):
        return _blocked_identity(
            raw_user_input=raw_user_input,
            reason=REJECTION_INVALID_IDENTITY_SHAPE,
            stock_code=stock_code,
            normalized_stock_code=normalized_stock_code,
            exchange=exchange,
            market=market,
            company_name=company_name,
            normalized_company_name=normalized_company_name,
            company_aliases=company_aliases,
            not_for_trading_advice=True,
        )

    status = identity.get("identity_status")
    confidence = identity.get("identity_confidence")
    rejection_reason = identity.get("rejection_reason")

    if status not in IDENTITY_STATUSES or confidence not in IDENTITY_CONFIDENCES:
        return _blocked_identity(
            raw_user_input=raw_user_input,
            reason=REJECTION_INVALID_IDENTITY_SHAPE,
            stock_code=stock_code,
            normalized_stock_code=normalized_stock_code,
            exchange=exchange,
            market=market,
            company_name=company_name,
            normalized_company_name=normalized_company_name,
            company_aliases=company_aliases,
            not_for_trading_advice=True,
        )

    if status == STATUS_BLOCKED:
        if not rejection_reason:
            return _blocked_identity(
                raw_user_input=raw_user_input,
                reason=REJECTION_INVALID_IDENTITY_SHAPE,
                stock_code=stock_code,
                normalized_stock_code=normalized_stock_code,
                exchange=exchange,
                market=market,
                company_name=company_name,
                normalized_company_name=normalized_company_name,
                company_aliases=company_aliases,
                not_for_trading_advice=True,
            )
        return dict(identity)

    if status == STATUS_VALID:
        if rejection_reason in BLOCKING_REJECTION_REASONS:
            return _blocked_identity(
                raw_user_input=raw_user_input,
                reason=REJECTION_INVALID_IDENTITY_SHAPE,
                stock_code=stock_code,
                normalized_stock_code=normalized_stock_code,
                exchange=exchange,
                market=market,
                company_name=company_name,
                normalized_company_name=normalized_company_name,
                company_aliases=company_aliases,
                not_for_trading_advice=True,
            )
        if confidence not in {CONFIDENCE_HIGH, CONFIDENCE_MEDIUM}:
            return _blocked_identity(
                raw_user_input=raw_user_input,
                reason=REJECTION_IDENTITY_CONFIDENCE_TOO_LOW,
                stock_code=stock_code,
                normalized_stock_code=normalized_stock_code,
                exchange=exchange,
                market=market,
                company_name=company_name,
                normalized_company_name=normalized_company_name,
                company_aliases=company_aliases,
                not_for_trading_advice=True,
            )
        if not normalized_stock_code or exchange not in SUPPORTED_EXCHANGES:
            return _blocked_identity(
                raw_user_input=raw_user_input,
                reason=REJECTION_INVALID_IDENTITY_SHAPE,
                stock_code=stock_code,
                normalized_stock_code=normalized_stock_code,
                exchange=exchange,
                market=market,
                company_name=company_name,
                normalized_company_name=normalized_company_name,
                company_aliases=company_aliases,
                not_for_trading_advice=True,
            )
        if normalize_stock_code(normalized_stock_code) != str(
            normalized_stock_code
        ).strip():
            return _blocked_identity(
                raw_user_input=raw_user_input,
                reason=REJECTION_INVALID_STOCK_CODE,
                stock_code=stock_code,
                normalized_stock_code=normalized_stock_code,
                exchange=exchange,
                market=market,
                company_name=company_name,
                normalized_company_name=normalized_company_name,
                company_aliases=company_aliases,
                not_for_trading_advice=True,
            )
        if infer_exchange_from_stock_code(str(normalized_stock_code)) != exchange:
            return _blocked_identity(
                raw_user_input=raw_user_input,
                reason=REJECTION_CODE_PREFIX_EXCHANGE_MISMATCH,
                stock_code=stock_code,
                normalized_stock_code=normalized_stock_code,
                exchange=exchange,
                market=market,
                company_name=company_name,
                normalized_company_name=normalized_company_name,
                company_aliases=company_aliases,
                conflicts=[REJECTION_CODE_PREFIX_EXCHANGE_MISMATCH],
                not_for_trading_advice=True,
            )
        if market != MARKET_CN_A:
            return _blocked_identity(
                raw_user_input=raw_user_input,
                reason=REJECTION_UNSUPPORTED_MARKET,
                stock_code=stock_code,
                normalized_stock_code=normalized_stock_code,
                exchange=exchange,
                market=market,
                company_name=company_name,
                normalized_company_name=normalized_company_name,
                company_aliases=company_aliases,
                not_for_trading_advice=True,
            )

    if status == STATUS_PARTIAL:
        return _blocked_identity(
            raw_user_input=raw_user_input,
            reason=REJECTION_IDENTITY_CONFIDENCE_TOO_LOW,
            stock_code=stock_code,
            normalized_stock_code=normalized_stock_code,
            exchange=exchange,
            market=market,
            company_name=company_name,
            normalized_company_name=normalized_company_name,
            company_aliases=company_aliases,
            not_for_trading_advice=True,
        )

    return dict(identity)


def build_security_identity_rejection_reason(payload_or_identity: Any) -> str | None:
    """Return the current fail-closed rejection reason, if any."""

    if isinstance(payload_or_identity, Mapping) and payload_or_identity.get(
        "schema_version"
    ) == SCHEMA_VERSION:
        identity = validate_security_identity(payload_or_identity)
    else:
        identity = normalize_security_identity(payload_or_identity)
    return identity.get("rejection_reason")


def can_enter_disclosure_request(
    identity: Any, *, with_reason: bool = False
) -> bool | tuple[bool, str | None]:
    """Return whether an identity may enter a future disclosure request contract."""

    validated = validate_security_identity(identity)
    allowed = (
        validated.get("identity_status") == STATUS_VALID
        and validated.get("identity_confidence") in {CONFIDENCE_HIGH, CONFIDENCE_MEDIUM}
        and validated.get("rejection_reason") in {None, ""}
    )
    reason = None if allowed else validated.get("rejection_reason")
    if with_reason:
        return allowed, reason
    return allowed


def _extract_payload_fields(
    payload: Any,
) -> tuple[str, Any, Any, Any, Any, Any, Any]:
    if isinstance(payload, Mapping):
        raw_user_input = str(payload.get("raw_user_input") or "")
        stock_code = payload.get("stock_code")
        exchange = payload.get("exchange")
        market = payload.get("market")
        company_name = payload.get("company_name")
        company_aliases = payload.get("company_aliases")
        not_for_trading_advice = payload.get("not_for_trading_advice")

        if not raw_user_input:
            raw_parts = [
                str(value)
                for value in (stock_code, exchange, company_name)
                if value is not None
            ]
            raw_user_input = " ".join(raw_parts)

        return (
            raw_user_input,
            stock_code,
            exchange,
            market,
            company_name,
            company_aliases,
            not_for_trading_advice,
        )

    return str(payload or ""), None, None, None, None, None, True


def _payload_values_for_safety(payload: Any) -> Any:
    return payload


def _resolve_stock_code_and_exchange(
    raw_user_input: str, stock_input: Any, exchange_input: Any
) -> tuple[str | None, str | None, str | None]:
    source = stock_input if stock_input is not None else raw_user_input
    stock_code, suffix_exchange, parse_rejection = parse_stock_code_and_exchange(source)
    if parse_rejection is not None:
        return stock_code, suffix_exchange, parse_rejection

    explicit_exchange = normalize_exchange_suffix(exchange_input)
    if exchange_input is not None and explicit_exchange is None:
        return stock_code, None, REJECTION_UNSUPPORTED_EXCHANGE_SUFFIX

    if suffix_exchange is not None and explicit_exchange is not None:
        if suffix_exchange != explicit_exchange:
            return stock_code, explicit_exchange, REJECTION_CODE_PREFIX_EXCHANGE_MISMATCH
        return stock_code, suffix_exchange, None

    return stock_code, suffix_exchange or explicit_exchange, None


def _extract_company_hint(raw_user_input: str) -> str | None:
    if not raw_user_input:
        return None

    without_stock_code = _STOCK_TOKEN_RE.sub(" ", raw_user_input)
    cleaned = without_stock_code
    for token in (
        "请分析",
        "帮我分析",
        "请",
        "帮我",
        "分析",
        "一下",
        "年报",
        "年度报告",
        "半年报",
        "半年度报告",
        "季报",
        "季度报告",
        "一季报",
        "三季报",
    ):
        cleaned = cleaned.replace(token, " ")
    cleaned = re.sub(r"\b20\d{2}\b", " ", cleaned)
    cleaned = re.sub(r"[\s,，。:：;；/\\|]+", " ", cleaned).strip()
    return normalize_company_name(cleaned)


def _is_invalid_code_like_input(value: Any) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    if not text:
        return False
    if _STOCK_TOKEN_RE.search(text):
        return False
    return bool(_WHOLE_CODELIKE_RE.match(text))


def _blocked_identity(
    *,
    raw_user_input: str,
    reason: str,
    stock_code: Any = None,
    normalized_stock_code: Any = None,
    exchange: Any = None,
    market: Any = None,
    company_name: Any = None,
    normalized_company_name: Any = None,
    company_aliases: list[Any] | None = None,
    conflicts: list[str] | None = None,
    caveats: list[str] | None = None,
    not_for_trading_advice: Any = True,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "raw_user_input": raw_user_input,
        "stock_code": stock_code,
        "normalized_stock_code": normalized_stock_code,
        "exchange": exchange,
        "market": market,
        "company_name": company_name,
        "normalized_company_name": normalized_company_name,
        "company_aliases": company_aliases or [],
        "identity_confidence": CONFIDENCE_BLOCKED,
        "identity_status": STATUS_BLOCKED,
        "identity_conflicts": conflicts or [],
        "rejection_reason": reason,
        "caveats": caveats or [],
        "not_for_trading_advice": not_for_trading_advice,
    }


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped
