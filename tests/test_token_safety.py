# -*- coding: utf-8 -*-

from src.fundamental_skill.data_providers.token_safety import (
    EMPTY_SECRET,
    MASKED_SECRET,
    UNSET_SECRET,
    mask_secret,
    sanitize_exception_message,
    sanitize_text,
)


def _assert_secret_not_rendered(secret: str, text: str) -> None:
    if secret in text:
        raise AssertionError("secret-like value was rendered")


def test_mask_secret_handles_empty_short_and_long_values():
    assert mask_secret(None) == UNSET_SECRET
    assert mask_secret("") == EMPTY_SECRET
    assert mask_secret("a") == MASKED_SECRET
    secret = "FAKE_TOKEN_FOR_TESTING_ONLY__NOT_REAL__XYZ_1234567890"
    if mask_secret(secret) != MASKED_SECRET:
        raise AssertionError("secret-like value was not masked")


def test_sanitize_text_masks_explicit_secret_without_exposing_full_value():
    secret = "FAKE_TOKEN_FOR_TESTING_ONLY__NOT_REAL__XYZ_1234567890"
    text = f"provider failed with {secret}"

    sanitized = sanitize_text(text, secrets=[secret])

    _assert_secret_not_rendered(secret, sanitized)
    assert MASKED_SECRET in sanitized


def test_sanitize_text_masks_keyed_token_patterns():
    secret = "FAKE_TOKEN_FOR_TESTING_ONLY__NOT_REAL__XYZ_1234567890"
    text = f"TUSHARE_TOKEN={secret} token: {secret} api_key={secret}"

    sanitized = sanitize_text(text)

    _assert_secret_not_rendered(secret, sanitized)
    assert "TUSHARE_TOKEN=<masked>" in sanitized
    assert "token: <masked>" in sanitized
    assert "api_key=<masked>" in sanitized


def test_sanitize_text_masks_bearer_values():
    secret = "fakeBearerToken123456"
    text = f"Authorization: Bearer {secret}"

    sanitized = sanitize_text(text)

    _assert_secret_not_rendered(secret, sanitized)
    assert "Bearer <masked>" in sanitized


def test_sanitize_exception_message_is_safe_for_router_errors():
    secret = "FAKE_TOKEN_FOR_TESTING_ONLY__NOT_REAL__XYZ_1234567890"
    exc = RuntimeError(f"request failed token={secret}")

    sanitized = sanitize_exception_message(exc)

    _assert_secret_not_rendered(secret, sanitized)
    assert "token=<masked>" in sanitized

