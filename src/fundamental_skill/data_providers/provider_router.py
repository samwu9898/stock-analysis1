# -*- coding: utf-8 -*-
"""Provider routing skeleton for Phase 1.

The router works only with injected providers in Phase 1. It does not import or
instantiate AkShare, Tushare, SDK clients, MCP tools, or network transports.
"""

from __future__ import annotations

from typing import Any, Mapping

from .base import DataProvider
from .schemas import ProviderMode, ProviderSelection, parse_provider_mode
from .token_safety import mask_secret, sanitize_exception_message, sanitize_text


class ProviderRoutingError(RuntimeError):
    """Non-secret provider routing failure."""

    def __init__(self, message: object, *, secrets: tuple[str | None, ...] = ()) -> None:
        super().__init__(sanitize_text(message, secrets=secrets))


def provider_mode_from_config(config: Mapping[str, Any] | None = None, default: ProviderMode | str = ProviderMode.AUTO) -> ProviderMode:
    """Read provider mode from a lightweight config mapping."""

    if not config:
        return parse_provider_mode(default)
    for key in ("provider", "provider_mode", "data_provider"):
        if key in config:
            return parse_provider_mode(config.get(key))
    return parse_provider_mode(default)


class ProviderRouter:
    """Select among injected providers without changing existing main flow."""

    def __init__(
        self,
        *,
        mode: ProviderMode | str | None = ProviderMode.AUTO,
        akshare_provider: DataProvider | None = None,
        tushare_provider: DataProvider | None = None,
        tushare_token: str | None = None,
        tushare_token_available: bool = False,
    ) -> None:
        self.mode = parse_provider_mode(mode)
        self.akshare_provider = akshare_provider
        self.tushare_provider = tushare_provider
        self._tushare_token_available = bool(tushare_token_available or tushare_token)
        self._token_display = mask_secret(tushare_token) if tushare_token is not None else mask_secret(None)

    @classmethod
    def from_config(
        cls,
        config: Mapping[str, Any] | None = None,
        *,
        akshare_provider: DataProvider | None = None,
        tushare_provider: DataProvider | None = None,
        tushare_token: str | None = None,
        tushare_token_available: bool = False,
    ) -> "ProviderRouter":
        return cls(
            mode=provider_mode_from_config(config),
            akshare_provider=akshare_provider,
            tushare_provider=tushare_provider,
            tushare_token=tushare_token,
            tushare_token_available=tushare_token_available,
        )

    def __repr__(self) -> str:
        providers = ", ".join(self.available_provider_names()) or "none"
        return (
            f"ProviderRouter(mode={self.mode.value!r}, providers={providers!r}, "
            f"tushare_token={self._token_display!r})"
        )

    def available_provider_names(self) -> tuple[str, ...]:
        names = []
        if self.akshare_provider is not None:
            names.append(self.akshare_provider.name)
        if self.tushare_provider is not None:
            names.append(self.tushare_provider.name)
        return tuple(names)

    def select(self) -> ProviderSelection:
        if self.mode == ProviderMode.AUTO:
            if self._can_use_tushare():
                return ProviderSelection(
                    mode=self.mode,
                    selected_provider=self.tushare_provider.name if self.tushare_provider else "tushare",
                    fallback_provider=self.akshare_provider.name if self.akshare_provider else "akshare",
                    reason="auto selected injected Tushare provider",
                )
            if self.akshare_provider is not None:
                return ProviderSelection(
                    mode=self.mode,
                    selected_provider=self.akshare_provider.name,
                    fallback_provider=None,
                    reason="auto selected injected AkShare fallback provider",
                )
            return ProviderSelection(
                mode=self.mode,
                selected_provider="akshare",
                reason="auto defaults to AkShare placeholder in Phase 1",
            )

        if self.mode == ProviderMode.AKSHARE:
            return ProviderSelection(
                mode=self.mode,
                selected_provider=self.akshare_provider.name if self.akshare_provider else "akshare",
                reason="akshare mode selected",
            )

        if self.mode == ProviderMode.TUSHARE:
            self._require_tushare_ready()
            return ProviderSelection(
                mode=self.mode,
                selected_provider=self.tushare_provider.name if self.tushare_provider else "tushare",
                reason="tushare mode selected injected Tushare provider",
            )

        if self.mode == ProviderMode.DUAL_COMPARE:
            return self.comparison_plan()

        raise ProviderRoutingError(f"unsupported provider mode: {self.mode}")

    def comparison_plan(self) -> ProviderSelection:
        providers = (
            self.akshare_provider.name if self.akshare_provider else "akshare",
            self.tushare_provider.name if self.tushare_provider else "tushare",
        )
        return ProviderSelection(
            mode=ProviderMode.DUAL_COMPARE,
            selected_provider=None,
            comparison_providers=providers,
            reason="dual_compare records comparison intent only; no automatic merge",
        )

    def fetch_to_raw_json(self, stock_code: str, *, force_refresh: bool = False) -> dict[str, Any]:
        if self.mode == ProviderMode.DUAL_COMPARE:
            raise ProviderRoutingError("dual_compare does not return a merged raw JSON payload")

        selection = self.select()
        provider = self._provider_for_selection(selection)
        if provider is None:
            raise ProviderRoutingError(
                f"provider {selection.selected_provider!r} is not injected in Phase 1"
            )
        try:
            return provider.fetch_to_raw_json(stock_code, force_refresh=force_refresh)
        except Exception as exc:
            raise ProviderRoutingError(
                sanitize_exception_message(exc),
            ) from exc

    def _provider_for_selection(self, selection: ProviderSelection) -> DataProvider | None:
        if self.akshare_provider is not None and selection.selected_provider == self.akshare_provider.name:
            return self.akshare_provider
        if self.tushare_provider is not None and selection.selected_provider == self.tushare_provider.name:
            return self.tushare_provider
        if selection.selected_provider == "akshare":
            return self.akshare_provider
        if selection.selected_provider == "tushare":
            return self.tushare_provider
        return None

    def _can_use_tushare(self) -> bool:
        return self.tushare_provider is not None and self._tushare_token_available

    def _require_tushare_ready(self) -> None:
        if not self._tushare_token_available:
            raise ProviderRoutingError("provider=tushare requires an available Tushare token")
        if self.tushare_provider is None:
            raise ProviderRoutingError("provider=tushare requires an injected Tushare provider in Phase 1")

