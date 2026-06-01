import builtins
import socket
import urllib.request

from fundamental_skill.data_verification.security_identity import (
    CONFIDENCE_BLOCKED,
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    EXCHANGE_BSE,
    EXCHANGE_SSE,
    EXCHANGE_SZSE,
    MARKET_CN_A,
    REJECTION_CODE_PREFIX_EXCHANGE_MISMATCH,
    REJECTION_COMPANY_ALIAS_CONFLICT,
    REJECTION_COMPANY_NAME_ONLY_REQUIRES_APPROVED_STATIC_IDENTITY_MAP,
    REJECTION_INVALID_IDENTITY_SHAPE,
    REJECTION_INVALID_STOCK_CODE,
    REJECTION_MISSING_STOCK_CODE_AND_COMPANY_NAME,
    REJECTION_UNSUPPORTED_EXCHANGE_SUFFIX,
    STATUS_BLOCKED,
    STATUS_VALID,
    can_enter_disclosure_request,
    normalize_security_identity,
    validate_security_identity,
)


def test_stock_code_only_uses_deterministic_sse_prefix_policy():
    identity = normalize_security_identity("600406")

    assert identity["identity_status"] == STATUS_VALID
    assert identity["normalized_stock_code"] == "600406"
    assert identity["exchange"] == EXCHANGE_SSE
    assert identity["market"] == MARKET_CN_A
    assert identity["identity_confidence"] == CONFIDENCE_MEDIUM
    assert "deterministic prefix inference is not live verification" in identity["caveats"]
    assert "company identity is not verified" in identity["caveats"]
    assert "symbol existence is not verified" in identity["caveats"]


def test_explicit_sse_suffix_is_high_confidence_without_company_hint():
    identity = normalize_security_identity("600406.SH")

    assert identity["identity_status"] == STATUS_VALID
    assert identity["normalized_stock_code"] == "600406"
    assert identity["exchange"] == EXCHANGE_SSE
    assert identity["market"] == MARKET_CN_A
    assert identity["identity_confidence"] == CONFIDENCE_HIGH


def test_explicit_ss_suffix_normalizes_to_sse():
    identity = normalize_security_identity("600406.SS")

    assert identity["identity_status"] == STATUS_VALID
    assert identity["normalized_stock_code"] == "600406"
    assert identity["exchange"] == EXCHANGE_SSE
    assert identity["market"] == MARKET_CN_A


def test_explicit_sz_suffix_normalizes_to_szse():
    identity = normalize_security_identity("000001.SZ")

    assert identity["identity_status"] == STATUS_VALID
    assert identity["normalized_stock_code"] == "000001"
    assert identity["exchange"] == EXCHANGE_SZSE
    assert identity["market"] == MARKET_CN_A


def test_bse_prefix_is_valid_with_deterministic_policy():
    identity = normalize_security_identity("830799")

    assert identity["identity_status"] == STATUS_VALID
    assert identity["normalized_stock_code"] == "830799"
    assert identity["exchange"] == EXCHANGE_BSE
    assert identity["market"] == MARKET_CN_A
    assert identity["identity_confidence"] == CONFIDENCE_MEDIUM


def test_code_prefix_exchange_mismatch_is_blocked():
    identity = normalize_security_identity("600406.SZ")

    assert identity["identity_status"] == STATUS_BLOCKED
    assert identity["rejection_reason"] == REJECTION_CODE_PREFIX_EXCHANGE_MISMATCH


def test_unsupported_exchange_suffix_is_blocked():
    identity = normalize_security_identity("600406.US")

    assert identity["identity_status"] == STATUS_BLOCKED
    assert identity["rejection_reason"] == REJECTION_UNSUPPORTED_EXCHANGE_SUFFIX


def test_invalid_stock_code_is_blocked():
    identity = normalize_security_identity(
        {"stock_code": "60040", "not_for_trading_advice": True}
    )

    assert identity["identity_status"] == STATUS_BLOCKED
    assert identity["rejection_reason"] == REJECTION_INVALID_STOCK_CODE


def test_missing_stock_code_and_company_name_is_blocked():
    identity = normalize_security_identity(
        {"raw_user_input": "", "not_for_trading_advice": True}
    )

    assert identity["identity_status"] == STATUS_BLOCKED
    assert identity["rejection_reason"] == REJECTION_MISSING_STOCK_CODE_AND_COMPANY_NAME


def test_company_name_only_is_blocked_without_static_identity_map():
    identity = normalize_security_identity("国电南瑞")

    assert identity["identity_status"] == STATUS_BLOCKED
    assert identity["identity_confidence"] == CONFIDENCE_BLOCKED
    assert (
        identity["rejection_reason"]
        == REJECTION_COMPANY_NAME_ONLY_REQUIRES_APPROVED_STATIC_IDENTITY_MAP
    )
    assert identity["normalized_company_name"] == "国电南瑞"
    assert "no IO" in identity["caveats"]
    assert "no provider lookup" in identity["caveats"]
    assert "no live exchange lookup" in identity["caveats"]
    assert "company name cannot be verified" in identity["caveats"]


def test_stock_code_with_company_name_retains_unverified_hint():
    identity = normalize_security_identity("请分析 600406 国电南瑞")

    assert identity["identity_status"] == STATUS_VALID
    assert identity["normalized_stock_code"] == "600406"
    assert identity["exchange"] == EXCHANGE_SSE
    assert identity["market"] == MARKET_CN_A
    assert identity["normalized_company_name"] == "国电南瑞"
    assert identity["identity_confidence"] == CONFIDENCE_MEDIUM
    assert identity["identity_conflicts"] == []
    assert (
        "company name supplied by user but not verified against stock code"
        in identity["caveats"]
    )
    assert "security identity derived from stock code and exchange only" in identity[
        "caveats"
    ]


def test_company_aliases_must_be_list():
    identity = normalize_security_identity(
        {
            "stock_code": "600406",
            "company_aliases": "国电南瑞",
            "not_for_trading_advice": True,
        }
    )

    assert identity["identity_status"] == STATUS_BLOCKED
    assert identity["rejection_reason"] == REJECTION_COMPANY_ALIAS_CONFLICT


def test_identity_conflicts_must_be_list():
    identity = normalize_security_identity("600406")
    identity["identity_conflicts"] = "not-a-list"

    validated = validate_security_identity(identity)

    assert validated["identity_status"] == STATUS_BLOCKED
    assert validated["rejection_reason"] == REJECTION_INVALID_IDENTITY_SHAPE


def test_caveats_must_be_list():
    identity = normalize_security_identity("600406")
    identity["caveats"] = "not-a-list"

    validated = validate_security_identity(identity)

    assert validated["identity_status"] == STATUS_BLOCKED
    assert validated["rejection_reason"] == REJECTION_INVALID_IDENTITY_SHAPE


def test_valid_identity_rejects_normalized_code_exchange_mismatch():
    identity = normalize_security_identity("600406.SH")
    identity["exchange"] = EXCHANGE_SZSE

    validated = validate_security_identity(identity)

    assert validated["identity_status"] == STATUS_BLOCKED
    assert validated["rejection_reason"] == REJECTION_CODE_PREFIX_EXCHANGE_MISMATCH


def test_valid_identity_rejects_invalid_normalized_stock_code():
    identity = normalize_security_identity("600406.SH")
    identity["normalized_stock_code"] = "60040"

    validated = validate_security_identity(identity)

    assert validated["identity_status"] == STATUS_BLOCKED
    assert validated["rejection_reason"] == REJECTION_INVALID_STOCK_CODE


def test_blocked_identity_must_have_rejection_reason():
    identity = normalize_security_identity("600406.SZ")
    identity["rejection_reason"] = None

    validated = validate_security_identity(identity)

    assert validated["identity_status"] == STATUS_BLOCKED
    assert validated["rejection_reason"] == REJECTION_INVALID_IDENTITY_SHAPE


def test_valid_identity_can_enter_disclosure_request():
    identity = normalize_security_identity("600406")

    assert can_enter_disclosure_request(identity) is True


def test_blocked_identity_cannot_enter_disclosure_request():
    identity = normalize_security_identity("国电南瑞")

    assert can_enter_disclosure_request(identity) is False


def test_normalization_does_not_use_file_or_network_io(monkeypatch):
    def fail_open(*args, **kwargs):
        raise AssertionError("file IO is forbidden")

    def fail_socket(*args, **kwargs):
        raise AssertionError("network IO is forbidden")

    monkeypatch.setattr(builtins, "open", fail_open)
    monkeypatch.setattr(socket, "create_connection", fail_socket)
    monkeypatch.setattr(urllib.request, "urlopen", fail_socket)

    identity = normalize_security_identity("600406")

    assert identity["identity_status"] == STATUS_VALID
