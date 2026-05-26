# -*- coding: utf-8 -*-

from src.fundamental_skill.data_providers.token_safety import (
    EMPTY_SECRET,
    MASKED_SECRET,
    UNSET_SECRET,
    mask_secret,
    sanitize_exception_message,
    sanitize_text,
)


def test_mask_secret_handles_empty_short_and_long_values():
    assert mask_secret(None) == UNSET_SECRET
    assert mask_secret("") == EMPTY_SECRET
    assert mask_secret("a") == MASKED_SECRET
    assert mask_secret("fake-token-for-tests-1234567890") == MASKED_SECRET


def test_sanitize_text_masks_explicit_secret_without_exposing_full_value():
    secret = "fake-token-for-tests-1234567890"
    text = f"provider failed with {secret}"

    sanitized = sanitize_text(text, secrets=[secret])

    assert secret not in sanitized
    assert MASKED_SECRET in sanitized


def test_sanitize_text_masks_keyed_token_patterns():
    secret = "fake-token-for-tests-abcdef"
    text = f"TUSHARE_TOKEN={secret} token: {secret} api_key={secret}"

    sanitized = sanitize_text(text)

    assert secret not in sanitized
    assert "TUSHARE_TOKEN=<masked>" in sanitized
    assert "token: <masked>" in sanitized
    assert "api_key=<masked>" in sanitized


def test_sanitize_text_masks_bearer_values():
    secret = "fakeBearerToken123456"
    text = f"Authorization: Bearer {secret}"

    sanitized = sanitize_text(text)

    assert secret not in sanitized
    assert "Bearer <masked>" in sanitized


def test_sanitize_exception_message_is_safe_for_router_errors():
    secret = "fake-token-for-tests-exception"
    exc = RuntimeError(f"request failed token={secret}")

    sanitized = sanitize_exception_message(exc)

    assert secret not in sanitized
    assert "token=<masked>" in sanitized

