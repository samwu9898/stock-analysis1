# -*- coding: utf-8 -*-

import inspect

import pytest

from src.fundamental_skill.data_providers.tushare_client import (
    TushareClient,
    TushareClientError,
    TusharePermissionError,
    TushareRateLimitError,
)


def _assert_secret_not_rendered(secret: str, text: str) -> None:
    if secret in text:
        raise AssertionError("secret-like value was rendered")


def test_tushare_client_uses_injected_mapping_transport_only():
    client = TushareClient(
        transport={
            "stock_basic": [{"ts_code": "002050.SZ", "name": "Mock Stock"}],
        }
    )

    rows = client.stock_basic(ts_code="002050")

    assert rows == [{"ts_code": "002050.SZ", "name": "Mock Stock"}]
    assert "transport_injected=True" in repr(client)


def test_tushare_client_uses_injected_callable_transport():
    calls = []

    def transport(endpoint, **params):
        calls.append({"endpoint": endpoint, "params": params})
        return [{"endpoint": endpoint, **params}]

    client = TushareClient(transport=transport)

    assert client.daily_basic(ts_code="002050") == [{"endpoint": "daily_basic", "ts_code": "002050"}]
    assert calls == [{"endpoint": "daily_basic", "params": {"ts_code": "002050"}}]


def test_tushare_client_without_transport_fails_closed():
    client = TushareClient()

    with pytest.raises(TushareClientError) as exc_info:
        client.income(ts_code="002050")

    assert exc_info.value.code == "no_transport"
    assert "mock transport is required" in str(exc_info.value)


def test_tushare_client_sanitizes_transport_errors_and_repr():
    fake_token = "FAKE_TOKEN_FOR_TESTING_ONLY__NOT_REAL__XYZ_1234567890"

    def transport(endpoint, **params):
        raise RuntimeError(f"{endpoint} failed token={fake_token}")

    client = TushareClient(transport=transport, token=fake_token)

    with pytest.raises(TushareClientError) as exc_info:
        client.cashflow(ts_code="002050")

    message = str(exc_info.value)
    _assert_secret_not_rendered(fake_token, message)
    assert "token=<masked>" in message
    _assert_secret_not_rendered(fake_token, repr(client))
    assert "<masked>" in repr(client)


def test_tushare_client_preserves_sanitized_permission_and_rate_limit_codes():
    secret = "FAKE_TOKEN_FOR_TESTING_ONLY__NOT_REAL__XYZ_1234567890"
    client = TushareClient(
        transport={
            "income": TusharePermissionError(f"token={secret} permission denied"),
            "daily_basic": TushareRateLimitError(f"token={secret} rate limit"),
        },
        token=secret,
    )

    with pytest.raises(TusharePermissionError) as permission_info:
        client.income(ts_code="002050")
    with pytest.raises(TushareRateLimitError) as rate_info:
        client.daily_basic(ts_code="002050")

    assert permission_info.value.code == "permission_denied"
    assert rate_info.value.code == "rate_limit"
    _assert_secret_not_rendered(secret, str(permission_info.value))
    _assert_secret_not_rendered(secret, str(rate_info.value))


def test_tushare_client_module_has_no_real_provider_or_external_io_imports():
    import src.fundamental_skill.data_providers.tushare_client as module

    source = inspect.getsource(module)

    forbidden = (
        "import " + "tushare",
        "req" + "uests",
        "ht" + "tpx",
        "url" + "lib",
        "api." + "tushare" + ".pro",
        "m" + "cp",
    )
    for marker in forbidden:
        assert marker not in source.lower()
