# -*- coding: utf-8 -*-

import pytest

from src.fundamental_skill.data_providers.tushare_sdk_transport import (
    TushareSdkTransport,
    TushareSdkTransportError,
)


def _fake_secret():
    return "Zz9Yy8Xx7Ww6Vv5" + "Uu4Tt3Ss2Rr1Qq0" + "Pp9Oo8Ii7Uu6Yy5"


def _assert_secret_not_rendered(secret: str, text: str) -> None:
    if secret in text:
        raise AssertionError("secret-like value was rendered")


def _assert_secret_forwarded(actual: str | None, expected: str) -> None:
    if actual != expected:
        raise AssertionError("secret-like value was not forwarded")


class _FakePro:
    def __init__(self, response=None, exc=None):
        self.response = response if response is not None else [{"ts_code": "600406.SH", "name": "Safe"}]
        self.exc = exc
        self.calls = []

    def stock_basic(self, **params):
        self.calls.append(("stock_basic", params))
        if self.exc is not None:
            raise self.exc
        return self.response


class _FakeSdk:
    def __init__(self, pro):
        self.pro = pro
        self.token_seen = None

    def set_token(self, token):
        self.token_seen = token

    def pro_api(self):
        return self.pro


def test_sdk_transport_requires_token_before_sdk_initialization():
    with pytest.raises(TushareSdkTransportError) as exc_info:
        TushareSdkTransport(token=None, sdk_factory=lambda: (_ for _ in ()).throw(AssertionError("not called")))

    assert exc_info.value.code == "missing_token"
    assert "token=<masked>" not in str(exc_info.value)


def test_sdk_transport_uses_injected_sdk_and_masks_repr():
    fake_secret = _fake_secret()
    pro = _FakePro()
    sdk = _FakeSdk(pro)

    transport = TushareSdkTransport(token=fake_secret, sdk=sdk, timestamp="20260526T120000")
    rows = transport.call("stock_basic", ts_code="600406.SH")

    assert rows == [{"ts_code": "600406.SH", "name": "Safe"}]
    assert pro.calls == [("stock_basic", {"ts_code": "600406.SH"})]
    _assert_secret_forwarded(sdk.token_seen, fake_secret)
    _assert_secret_not_rendered(fake_secret, repr(transport))
    assert "_token" not in vars(transport)


def test_sdk_transport_sanitizes_sdk_exception_at_source_boundary():
    fake_secret = _fake_secret()
    pro = _FakePro(exc=RuntimeError("API body token=" + fake_secret + " Authorization: Bearer " + fake_secret))
    transport = TushareSdkTransport(token=fake_secret, sdk=_FakeSdk(pro))

    with pytest.raises(TushareSdkTransportError) as exc_info:
        transport.call("stock_basic", ts_code="600406.SH")

    message = str(exc_info.value)
    assert exc_info.value.code == "sdk_call_error"
    assert "RuntimeError" in message
    _assert_secret_not_rendered(fake_secret, message)
    assert "Bearer" not in message
    assert "API body" not in message


def test_sdk_transport_blocks_token_like_response_before_provider_storage():
    fake_secret = _fake_secret()
    pro = _FakePro(response={"provider_message": "credential=" + fake_secret})
    transport = TushareSdkTransport(token=fake_secret, sdk=_FakeSdk(pro))

    with pytest.raises(TushareSdkTransportError) as exc_info:
        transport.call("stock_basic", ts_code="600406.SH")

    assert exc_info.value.code == "token_leak_blocker"
    _assert_secret_not_rendered(fake_secret, str(exc_info.value))


def test_sdk_transport_rejects_secret_like_request_params():
    fake_secret = _fake_secret()
    transport = TushareSdkTransport(token=fake_secret, sdk=_FakeSdk(_FakePro()))

    with pytest.raises(TushareSdkTransportError) as exc_info:
        transport.call("stock_basic", api_key=fake_secret)

    assert exc_info.value.code == "secret_in_request_params"
    _assert_secret_not_rendered(fake_secret, str(exc_info.value))
