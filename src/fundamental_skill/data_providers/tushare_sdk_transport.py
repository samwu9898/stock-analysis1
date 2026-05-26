# -*- coding: utf-8 -*-
"""Local-only Tushare SDK transport skeleton for real-token smoke gating.

The transport is intentionally tiny and injectable. Tests can pass a fake SDK
object or factory; the real SDK is imported lazily only when no SDK object is
injected by an explicit real-token smoke caller.
"""

from __future__ import annotations

import importlib
import re
from typing import Any, Callable

from .token_leak_scanner import TokenLeakError, assert_no_token_leaks, scan_for_token_leaks
from .token_safety import MASKED_SECRET, sanitize_text


class TushareSdkTransportError(RuntimeError):
    """Sanitized SDK transport failure."""

    def __init__(
        self,
        *,
        code: str,
        error_class: str = "transport_error",
        endpoint: str | None = None,
        gate_name: str = "real_token_smoke",
        provider_name: str = "tushare",
        timestamp: str | None = None,
        stock_code: str | None = None,
        message: object | None = None,
    ) -> None:
        self.code = code
        self.error_class = _safe_label(error_class)
        self.endpoint = _safe_label(endpoint) if endpoint else None
        self.gate_name = _safe_label(gate_name)
        self.provider_name = _safe_label(provider_name)
        self.timestamp = _safe_label(timestamp) if timestamp else None
        self.stock_code = _safe_label(stock_code) if stock_code else None
        self.safe_message = _safe_exception_message(
            code=self.code,
            error_class=self.error_class,
            endpoint=self.endpoint,
            gate_name=self.gate_name,
            provider_name=self.provider_name,
            timestamp=self.timestamp,
            stock_code=self.stock_code,
            message=message,
        )
        super().__init__(self.safe_message)

    @classmethod
    def from_exception(
        cls,
        exc: BaseException,
        *,
        code: str,
        endpoint: str | None = None,
        token: str | None = None,
        gate_name: str = "real_token_smoke",
        provider_name: str = "tushare",
        timestamp: str | None = None,
        stock_code: str | None = None,
    ) -> "TushareSdkTransportError":
        del token
        return cls(
            code=code,
            error_class=type(exc).__name__,
            endpoint=endpoint,
            gate_name=gate_name,
            provider_name=provider_name,
            timestamp=timestamp,
            stock_code=stock_code,
        )


class TushareSdkTransport:
    """Mockable facade over a Tushare SDK ``pro_api`` object."""

    provider_name = "tushare"
    gate_name = "real_token_smoke"

    def __init__(
        self,
        *,
        token: str | None,
        sdk: Any | None = None,
        sdk_factory: Callable[[], Any] | None = None,
        timestamp: str | None = None,
    ) -> None:
        if not token:
            raise TushareSdkTransportError(code="missing_token", error_class="MissingToken")
        self._timestamp = _safe_label(timestamp) if timestamp else None
        self._api = self._initialize_api(token=token, sdk=sdk, sdk_factory=sdk_factory)

    def __repr__(self) -> str:
        return "TushareSdkTransport(provider='tushare', token='<masked>')"

    def call(self, endpoint: str, **params: Any) -> Any:
        """Call one SDK endpoint and return the raw SDK response."""

        safe_endpoint = _validate_endpoint(endpoint)
        params_scan = scan_for_token_leaks(params)
        if not params_scan.ok:
            raise TushareSdkTransportError(
                code="secret_in_request_params",
                error_class="TokenLeakError",
                endpoint=safe_endpoint,
                timestamp=self._timestamp,
            )

        method = getattr(self._api, safe_endpoint, None)
        if not callable(method):
            raise TushareSdkTransportError(
                code="missing_endpoint",
                error_class="MissingEndpoint",
                endpoint=safe_endpoint,
                timestamp=self._timestamp,
            )

        try:
            response = method(**params)
            assert_no_token_leaks(response, context=f"tushare sdk {safe_endpoint} response")
            return response
        except TokenLeakError as exc:
            raise TushareSdkTransportError.from_exception(
                exc,
                code="token_leak_blocker",
                endpoint=safe_endpoint,
                timestamp=self._timestamp,
            ) from None
        except Exception as exc:
            raise TushareSdkTransportError.from_exception(
                exc,
                code="sdk_call_error",
                endpoint=safe_endpoint,
                timestamp=self._timestamp,
            ) from None

    def _initialize_api(self, *, token: str, sdk: Any | None, sdk_factory: Callable[[], Any] | None) -> Any:
        try:
            sdk_obj = sdk
            if sdk_obj is None and sdk_factory is not None:
                sdk_obj = sdk_factory()
            if sdk_obj is None:
                sdk_obj = importlib.import_module("tushare")
            if sdk_obj is None:
                raise RuntimeError("SDK unavailable")

            set_token = getattr(sdk_obj, "set_token", None)
            if callable(set_token):
                set_token(token)

            pro_api = getattr(sdk_obj, "pro_api", None)
            api = pro_api() if callable(pro_api) else sdk_obj
            if api is None:
                raise RuntimeError("SDK pro_api unavailable")
            return api
        except ModuleNotFoundError as exc:
            raise TushareSdkTransportError.from_exception(
                exc,
                code="sdk_unavailable",
                token=token,
                timestamp=self._timestamp,
            ) from None
        except Exception as exc:
            raise TushareSdkTransportError.from_exception(
                exc,
                code="sdk_initialization_error",
                token=token,
                timestamp=self._timestamp,
            ) from None


def _validate_endpoint(endpoint: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,63}", str(endpoint)):
        raise TushareSdkTransportError(code="invalid_endpoint", error_class="InvalidEndpoint")
    return str(endpoint)


def _safe_label(value: object) -> str:
    text = sanitize_text(value)
    if scan_for_token_leaks(text).ok and re.fullmatch(r"[A-Za-z0-9_.:-]+", text):
        return text
    return MASKED_SECRET


def _safe_exception_message(
    *,
    code: str,
    error_class: str,
    endpoint: str | None,
    gate_name: str,
    provider_name: str,
    timestamp: str | None,
    stock_code: str | None,
    message: object | None,
) -> str:
    del message
    parts = [
        f"gate={gate_name}",
        f"provider={provider_name}",
        f"code={_safe_label(code)}",
        f"error_class={error_class}",
    ]
    if endpoint:
        parts.append(f"endpoint={endpoint}")
    if timestamp:
        parts.append(f"timestamp={timestamp}")
    if stock_code:
        parts.append(f"stock_code={stock_code}")
    return "tushare_sdk_transport_error: " + " ".join(parts)
