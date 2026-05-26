# -*- coding: utf-8 -*-

import pytest

from src.fundamental_skill.data_providers.fake_provider import FakeDataProvider
from src.fundamental_skill.data_providers.provider_router import (
    ProviderRouter,
    ProviderRoutingError,
    provider_mode_from_config,
)
from src.fundamental_skill.data_providers.schemas import ProviderMode
from src.fundamental_skill.data_providers.tushare_client import TushareClient
from src.fundamental_skill.data_providers.tushare_provider import TushareProvider


def test_provider_mode_from_config_reads_supported_keys():
    assert provider_mode_from_config({"provider": "akshare"}) == ProviderMode.AKSHARE
    assert provider_mode_from_config({"provider_mode": "tushare"}) == ProviderMode.TUSHARE
    assert provider_mode_from_config({"data_provider": "dual"}) == ProviderMode.DUAL_COMPARE
    assert provider_mode_from_config({}) == ProviderMode.AUTO


def test_auto_falls_back_to_injected_akshare_provider_without_tushare():
    akshare = FakeDataProvider(name="akshare")
    router = ProviderRouter(mode="auto", akshare_provider=akshare)

    selection = router.select()
    raw = router.fetch_to_raw_json("002050", force_refresh=True)

    assert selection.selected_provider == "akshare"
    assert selection.fallback_provider is None
    assert raw["meta"]["data_source"] == "akshare"
    assert akshare.calls == [{"stock_code": "002050", "force_refresh": True}]


def test_auto_can_lazily_create_akshare_provider_when_tushare_is_unavailable():
    created = []

    def factory():
        provider = FakeDataProvider(name="akshare")
        created.append(provider)
        return provider

    router = ProviderRouter(mode="auto", akshare_provider_factory=factory)

    selection = router.select()
    raw = router.fetch_to_raw_json("002050", force_refresh=True)

    assert selection.selected_provider == "akshare"
    assert raw["meta"]["data_source"] == "akshare"
    assert created[0].calls == [{"stock_code": "002050", "force_refresh": True}]


def test_akshare_mode_can_lazily_create_registered_akshare_provider():
    created = []

    def factory():
        provider = FakeDataProvider(name="akshare")
        created.append(provider)
        return provider

    router = ProviderRouter(mode="akshare", akshare_provider_factory=factory)

    raw = router.fetch_to_raw_json("002050")

    assert raw["meta"]["data_source"] == "akshare"
    assert created[0].calls == [{"stock_code": "002050", "force_refresh": False}]


def test_auto_prefers_injected_tushare_when_token_available():
    akshare = FakeDataProvider(name="akshare")
    tushare = FakeDataProvider(name="tushare")
    router = ProviderRouter(
        mode="auto",
        akshare_provider=akshare,
        tushare_provider=tushare,
        tushare_token_available=True,
    )

    selection = router.select()
    raw = router.fetch_to_raw_json("002050")

    assert selection.selected_provider == "tushare"
    assert selection.fallback_provider == "akshare"
    assert raw["meta"]["data_source"] == "tushare"
    assert tushare.calls == [{"stock_code": "002050", "force_refresh": False}]
    assert akshare.calls == []


def test_tushare_mode_without_token_fails_closed():
    router = ProviderRouter(mode="tushare", tushare_provider=FakeDataProvider(name="tushare"))

    with pytest.raises(ProviderRoutingError) as exc_info:
        router.select()

    assert "requires an available Tushare token" in str(exc_info.value)


def test_tushare_mode_without_provider_fails_closed_and_masks_token():
    fake_token = "fake-token-for-tests-1234567890"
    router = ProviderRouter(mode="tushare", tushare_token=fake_token)

    with pytest.raises(ProviderRoutingError) as exc_info:
        router.select()

    message = str(exc_info.value)
    assert "requires an injected Tushare provider" in message
    assert fake_token not in message
    assert fake_token not in repr(router)
    assert "<masked>" in repr(router)


def test_tushare_mode_with_injected_provider_and_token_fetches_fake_raw():
    tushare = FakeDataProvider(name="tushare")
    router = ProviderRouter(mode="tushare", tushare_provider=tushare, tushare_token_available=True)

    raw = router.fetch_to_raw_json("002050")

    assert raw["meta"]["data_source"] == "tushare"
    assert tushare.calls == [{"stock_code": "002050", "force_refresh": False}]


def test_tushare_mode_with_injected_phase3_provider_and_fake_token_available_fetches_mocked_raw():
    provider = TushareProvider(
        client=TushareClient(
            transport={
                "stock_basic": [{"stock_code": "002050", "stock_name": "Mock Stock"}],
                "income": [],
                "balancesheet": [],
                "cashflow": [],
                "fina_indicator": [],
                "daily_basic": [],
                "fina_mainbz": [],
            }
        ),
        token_available=True,
    )
    router = ProviderRouter(mode="tushare", tushare_provider=provider, tushare_token_available=True)

    raw = router.fetch_to_raw_json("002050")

    assert raw["meta"]["data_source"] == "tushare"
    assert raw["blocks"]["basic_info"][0]["stock_name"] == "Mock Stock"
    assert raw["fetch_status"]["news"]["error"] == "news_missing_fallback"


def test_dual_compare_returns_intent_and_does_not_auto_merge():
    akshare = FakeDataProvider(name="akshare")
    tushare = FakeDataProvider(name="tushare")
    router = ProviderRouter(
        mode="dual_compare",
        akshare_provider=akshare,
        tushare_provider=tushare,
        tushare_token_available=True,
    )

    selection = router.select()

    assert selection.is_comparison
    assert selection.selected_provider is None
    assert selection.comparison_providers == ("akshare", "tushare")
    assert "no automatic merge" in selection.reason
    with pytest.raises(ProviderRoutingError, match="does not return a merged raw JSON"):
        router.fetch_to_raw_json("002050")
    assert akshare.calls == []
    assert tushare.calls == []


def test_provider_failure_error_is_sanitized():
    fake_token = "fake-token-for-tests-abcdef"
    failing = FakeDataProvider(
        name="tushare",
        fail_message=f"token={fake_token} failed",
    )
    router = ProviderRouter(
        mode="tushare",
        tushare_provider=failing,
        tushare_token=fake_token,
    )

    with pytest.raises(ProviderRoutingError) as exc_info:
        router.fetch_to_raw_json("002050")

    message = str(exc_info.value)
    assert fake_token not in message
    assert "token=<masked>" in message
