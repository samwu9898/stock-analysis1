# -*- coding: utf-8 -*-
"""Mockable Tushare client abstraction for Phase 3.

This module intentionally does not import the real Tushare SDK, read
credentials, read local tool config, or perform external I/O. It only provides
a small endpoint abstraction that tests can drive with injected transports.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .token_safety import mask_secret, sanitize_exception_message, sanitize_text


class TushareClientError(RuntimeError):
    """Sanitized client-side endpoint failure."""

    def __init__(
        self,
        message: object,
        *,
        code: str = "api_error",
        endpoint: str | None = None,
        secrets: tuple[str | None, ...] = (),
    ) -> None:
        self.code = code
        self.endpoint = endpoint
        super().__init__(sanitize_text(message, secrets=secrets))


class TusharePermissionError(TushareClientError):
    """Endpoint is unavailable under the current mocked permission set."""

    def __init__(self, message: object = "permission denied", *, endpoint: str | None = None, secrets: tuple[str | None, ...] = ()) -> None:
        super().__init__(message, code="permission_denied", endpoint=endpoint, secrets=secrets)


class TushareRateLimitError(TushareClientError):
    """Endpoint was rate limited by the mocked transport."""

    def __init__(self, message: object = "rate limit", *, endpoint: str | None = None, secrets: tuple[str | None, ...] = ()) -> None:
        super().__init__(message, code="rate_limit", endpoint=endpoint, secrets=secrets)


class TushareMalformedResponseError(TushareClientError):
    """Endpoint returned a shape that the provider cannot map."""

    def __init__(self, message: object = "malformed response", *, endpoint: str | None = None, secrets: tuple[str | None, ...] = ()) -> None:
        super().__init__(message, code="malformed_response", endpoint=endpoint, secrets=secrets)


Transport = Mapping[str, Any] | Callable[..., Any] | Any


class TushareClient:
    """Endpoint facade backed only by injected mocked transports."""

    def __init__(self, transport: Transport | None = None, *, token: str | None = None) -> None:
        self._transport = transport
        self._token = token
        self._token_display = mask_secret(token) if token is not None else mask_secret(None)

    def __repr__(self) -> str:
        return f"TushareClient(transport_injected={self._transport is not None}, token={self._token_display!r})"

    def request(self, endpoint: str, **params: Any) -> Any:
        """Return the mocked response for an endpoint or raise a sanitized error."""

        if self._transport is None:
            raise TushareClientError(
                "mock transport is required for Phase 3 TushareClient",
                code="no_transport",
                endpoint=endpoint,
                secrets=(self._token,),
            )
        try:
            return self._call_transport(endpoint, params)
        except TushareClientError as exc:
            message = sanitize_exception_message(exc, secrets=(self._token,))
            if type(exc) is TushareClientError:
                raise TushareClientError(
                    message,
                    code=exc.code,
                    endpoint=exc.endpoint or endpoint,
                    secrets=(self._token,),
                ) from exc
            raise type(exc)(message, endpoint=exc.endpoint or endpoint, secrets=(self._token,)) from exc
        except Exception as exc:
            raise TushareClientError(
                sanitize_exception_message(exc, secrets=(self._token,)),
                code="api_error",
                endpoint=endpoint,
                secrets=(self._token,),
            ) from exc

    def stock_basic(self, **params: Any) -> Any:
        return self.request("stock_basic", **params)

    def income(self, **params: Any) -> Any:
        return self.request("income", **params)

    def balancesheet(self, **params: Any) -> Any:
        return self.request("balancesheet", **params)

    def cashflow(self, **params: Any) -> Any:
        return self.request("cashflow", **params)

    def fina_indicator(self, **params: Any) -> Any:
        return self.request("fina_indicator", **params)

    def daily_basic(self, **params: Any) -> Any:
        return self.request("daily_basic", **params)

    def fina_mainbz(self, **params: Any) -> Any:
        return self.request("fina_mainbz", **params)

    def _call_transport(self, endpoint: str, params: dict[str, Any]) -> Any:
        if isinstance(self._transport, Mapping):
            response = self._transport.get(endpoint, [])
            if isinstance(response, BaseException):
                raise response
            return response
        call = getattr(self._transport, "call", None)
        if callable(call):
            return call(endpoint, **params)
        if callable(self._transport):
            return self._transport(endpoint, **params)
        raise TushareClientError("mock transport must be a mapping, callable, or object with call()", code="malformed_transport", endpoint=endpoint)
