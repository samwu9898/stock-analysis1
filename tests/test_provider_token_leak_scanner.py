# -*- coding: utf-8 -*-

import uuid

import pytest

from src.fundamental_skill.data_providers.token_leak_scanner import (
    TRACKED_DOCS_TOKEN_LEAK_POLICY,
    TRACKED_TESTS_TOKEN_LEAK_POLICY,
    TokenLeakError,
    assert_no_token_leaks,
    scan_for_token_leaks,
)


SAFE_FAKE_TOKEN = "FAKE_TOKEN_FOR_TESTING_ONLY__NOT_REAL__XYZ_1234567890"
SAFE_TEST_TOKEN = "TEST_TOKEN_FOR_TESTING_ONLY__NOT_REAL__XYZ_1234567890"
SAFE_EXAMPLE_TOKEN = "EXAMPLE_TOKEN_FOR_TESTING_ONLY__NOT_REAL__XYZ_1234567890"


def _realistic_token_like():
    return "A9" + uuid.uuid4().hex + "z" + uuid.uuid4().hex


def _assert_secret_not_rendered(secret: str, text: str) -> None:
    if secret in text:
        raise AssertionError("secret-like value was rendered")


def test_scanner_accepts_safe_payload():
    result = scan_for_token_leaks({"source_trace": [{"provider": "tushare", "value": "<masked>"}]})

    assert result.ok
    assert result.findings == ()


def test_scanner_detects_keyed_token_and_masks_secret():
    fake_secret = _realistic_token_like()

    result = scan_for_token_leaks({"error": f"token={fake_secret}"})

    assert not result.ok
    assert result.findings[0].kind == "keyed_secret"
    _assert_secret_not_rendered(fake_secret, str(result))
    assert "<masked>" in str(result)


def test_scanner_detects_bearer_and_sensitive_dict_key_without_leaking_value():
    fake_secret = _realistic_token_like()

    result = scan_for_token_leaks({"headers": f"Bearer {fake_secret}", "api_key": fake_secret})

    assert not result.ok
    assert {finding.kind for finding in result.findings} >= {"bearer_secret", "sensitive_key_value"}
    _assert_secret_not_rendered(fake_secret, str(result))


def test_scanner_detects_mcp_url_pattern_without_literal_secret_output():
    fake_secret = _realistic_token_like()
    text = "mcp" + "://local-tool/service?token=" + fake_secret

    result = scan_for_token_leaks(text)

    assert not result.ok
    assert any(finding.kind == "mcp_url_or_token" for finding in result.findings)
    _assert_secret_not_rendered(fake_secret, str(result))


def test_assert_no_token_leaks_raises_sanitized_error():
    fake_secret = _realistic_token_like()

    with pytest.raises(TokenLeakError) as exc_info:
        assert_no_token_leaks({"message": f"api_key={fake_secret}"}, context="artifact")

    message = str(exc_info.value)
    assert "artifact contains secret-like data" in message
    _assert_secret_not_rendered(fake_secret, message)
    assert "<masked>" in message


def test_scanner_detects_exact_token_reference_without_printing_it():
    fake_secret = _realistic_token_like()

    result = scan_for_token_leaks({"message": f"value {fake_secret}"}, secret_refs=(fake_secret,))

    assert not result.ok
    assert any(finding.kind == "exact_secret" for finding in result.findings)
    _assert_secret_not_rendered(fake_secret, str(result))
    assert {finding.sanitized_excerpt for finding in result.findings} == {"<masked>"}
    assert all(set(finding.to_dict()) == {"location", "sanitized_excerpt"} for finding in result.findings)


def test_scanner_detects_realistic_token_like_string_near_case_insensitive_keyword():
    fake_secret = _realistic_token_like()

    result = scan_for_token_leaks(f"CREDENTIAL issued: {fake_secret}")

    assert not result.ok
    assert any(finding.kind in {"token_like_value", "token_like_near_secret_keyword"} for finding in result.findings)
    _assert_secret_not_rendered(fake_secret, str(result))


def test_scanner_scans_dict_keys_values_and_url_query_parameters():
    fake_secret = _realistic_token_like()
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
    _assert_secret_not_rendered(fake_secret, str(result))
    assert all(finding.sanitized_excerpt == "<masked>" for finding in result.findings)


def test_tracked_tests_policy_allows_obviously_invalid_fake_prefixes():
    for token_value in (SAFE_FAKE_TOKEN, SAFE_TEST_TOKEN, SAFE_EXAMPLE_TOKEN):
        result = scan_for_token_leaks(
            {"fixture": f"TUSHARE_TOKEN={token_value}"},
            policy=TRACKED_TESTS_TOKEN_LEAK_POLICY,
        )

        assert result.ok


def test_strict_policy_still_blocks_prefixed_fake_token_in_runtime_payload():
    for token_value in (SAFE_FAKE_TOKEN, SAFE_TEST_TOKEN, SAFE_EXAMPLE_TOKEN):
        result = scan_for_token_leaks({"runtime": f"token={token_value}"})

        assert not result.ok
        assert any(finding.kind == "keyed_secret" for finding in result.findings)


def test_tracked_docs_policy_allows_safe_placeholders_and_pattern_names():
    docs_text = "\n".join(
        [
            "token=<YOUR_TOKEN>",
            "TUSHARE_TOKEN=<TUSHARE_TOKEN>",
            "LOCAL_TOKEN=<YOUR_TUSHARE_TOKEN>",
            "Authorization: Bearer <REDACTED>",
            "sanitized output uses <masked>",
            "mcp?token=<TUSHARE_TOKEN>",
            "scanner finding kind token_like_value is documented by name",
        ]
    )

    result = scan_for_token_leaks(docs_text, policy=TRACKED_DOCS_TOKEN_LEAK_POLICY)

    assert result.ok


def test_tracked_docs_policy_blocks_keyed_prefixed_fake_token():
    fake_doc_token = "FAKE_TOKEN_FOR_DOCS_ONLY__NOT_REAL__XYZ_1234567890"

    result = scan_for_token_leaks(f"token={fake_doc_token}", policy=TRACKED_DOCS_TOKEN_LEAK_POLICY)

    assert not result.ok
    assert any(finding.kind == "keyed_secret" for finding in result.findings)
    _assert_secret_not_rendered(fake_doc_token, str(result))


def test_runtime_generated_realistic_token_like_string_still_blocks():
    fake_secret = _realistic_token_like()

    result = scan_for_token_leaks(f"token issued for smoke gate: {fake_secret}")

    assert not result.ok
    _assert_secret_not_rendered(fake_secret, str(result))
