# -*- coding: utf-8 -*-

import pytest

from src.fundamental_skill.data_providers.token_leak_scanner import (
    TokenLeakError,
    assert_no_token_leaks,
    scan_for_token_leaks,
)


def test_scanner_accepts_safe_payload():
    result = scan_for_token_leaks({"source_trace": [{"provider": "tushare", "value": "<masked>"}]})

    assert result.ok
    assert result.findings == ()


def test_scanner_detects_keyed_token_and_masks_secret():
    fake_secret = "fake-token-for-tests-1234567890abcdef"

    result = scan_for_token_leaks({"error": f"token={fake_secret}"})

    assert not result.ok
    assert result.findings[0].kind == "keyed_secret"
    assert fake_secret not in str(result)
    assert "<masked>" in str(result)


def test_scanner_detects_bearer_and_sensitive_dict_key_without_leaking_value():
    fake_secret = "fakebearer1234567890abcdef1234567890"

    result = scan_for_token_leaks({"headers": f"Bearer {fake_secret}", "api_key": fake_secret})

    assert not result.ok
    assert {finding.kind for finding in result.findings} >= {"bearer_secret", "sensitive_key_value"}
    assert fake_secret not in str(result)


def test_scanner_detects_mcp_url_pattern_without_literal_secret_output():
    fake_secret = "mcp-secret-1234567890abcdef"
    text = "mcp" + "://local-tool/service?token=" + fake_secret

    result = scan_for_token_leaks(text)

    assert not result.ok
    assert any(finding.kind == "mcp_url_or_token" for finding in result.findings)
    assert fake_secret not in str(result)


def test_assert_no_token_leaks_raises_sanitized_error():
    fake_secret = "fake-token-for-tests-abcdef1234567890"

    with pytest.raises(TokenLeakError) as exc_info:
        assert_no_token_leaks({"message": f"api_key={fake_secret}"}, context="artifact")

    message = str(exc_info.value)
    assert "artifact contains secret-like data" in message
    assert fake_secret not in message
    assert "<masked>" in message
