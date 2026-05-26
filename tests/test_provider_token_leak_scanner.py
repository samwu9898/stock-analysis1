# -*- coding: utf-8 -*-

import pytest

from src.fundamental_skill.data_providers.token_leak_scanner import (
    TokenLeakError,
    assert_no_token_leaks,
    scan_for_token_leaks,
)


def _fake_secret():
    return "Aa1Bb2Cc3Dd4Ee5" + "Ff6Gg7Hh8Ii9Jj0" + "Kk1Ll2Mm3Nn4Oo5"


def test_scanner_accepts_safe_payload():
    result = scan_for_token_leaks({"source_trace": [{"provider": "tushare", "value": "<masked>"}]})

    assert result.ok
    assert result.findings == ()


def test_scanner_detects_keyed_token_and_masks_secret():
    fake_secret = _fake_secret()

    result = scan_for_token_leaks({"error": f"token={fake_secret}"})

    assert not result.ok
    assert result.findings[0].kind == "keyed_secret"
    assert fake_secret not in str(result)
    assert "<masked>" in str(result)


def test_scanner_detects_bearer_and_sensitive_dict_key_without_leaking_value():
    fake_secret = _fake_secret()

    result = scan_for_token_leaks({"headers": f"Bearer {fake_secret}", "api_key": fake_secret})

    assert not result.ok
    assert {finding.kind for finding in result.findings} >= {"bearer_secret", "sensitive_key_value"}
    assert fake_secret not in str(result)


def test_scanner_detects_mcp_url_pattern_without_literal_secret_output():
    fake_secret = _fake_secret()
    text = "mcp" + "://local-tool/service?token=" + fake_secret

    result = scan_for_token_leaks(text)

    assert not result.ok
    assert any(finding.kind == "mcp_url_or_token" for finding in result.findings)
    assert fake_secret not in str(result)


def test_assert_no_token_leaks_raises_sanitized_error():
    fake_secret = _fake_secret()

    with pytest.raises(TokenLeakError) as exc_info:
        assert_no_token_leaks({"message": f"api_key={fake_secret}"}, context="artifact")

    message = str(exc_info.value)
    assert "artifact contains secret-like data" in message
    assert fake_secret not in message
    assert "<masked>" in message


def test_scanner_detects_exact_token_reference_without_printing_it():
    fake_secret = _fake_secret()

    result = scan_for_token_leaks({"message": f"value {fake_secret}"}, secret_refs=(fake_secret,))

    assert not result.ok
    assert any(finding.kind == "exact_secret" for finding in result.findings)
    assert fake_secret not in str(result)
    assert {finding.sanitized_excerpt for finding in result.findings} == {"<masked>"}
    assert all(set(finding.to_dict()) == {"location", "sanitized_excerpt"} for finding in result.findings)


def test_scanner_detects_realistic_token_like_string_near_case_insensitive_keyword():
    fake_secret = _fake_secret()

    result = scan_for_token_leaks(f"CREDENTIAL issued: {fake_secret}")

    assert not result.ok
    assert any(finding.kind in {"token_like_value", "token_like_near_secret_keyword"} for finding in result.findings)
    assert fake_secret not in str(result)


def test_scanner_scans_dict_keys_values_and_url_query_parameters():
    fake_secret = _fake_secret()
    payload = {
        "metadata": {
            "Auth" + fake_secret: "safe",
            "nested": {"credential": fake_secret},
            "url": "https://example.invalid/api?api_key=" + fake_secret,
        }
    }

    result = scan_for_token_leaks(payload)

    assert not result.ok
    kinds = {finding.kind for finding in result.findings}
    assert {"sensitive_key_value", "url_query_secret"} <= kinds
    assert any(kind in kinds for kind in {"token_like_value", "token_like_near_secret_keyword"})
    assert fake_secret not in str(result)
    assert all(finding.sanitized_excerpt == "<masked>" for finding in result.findings)
