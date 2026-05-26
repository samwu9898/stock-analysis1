# -*- coding: utf-8 -*-

import inspect

import pytest

from src.fundamental_skill.data_providers.fake_provider import FakeDataProvider
from src.fundamental_skill.data_providers.schemas import (
    CANONICAL_RAW_BLOCKS,
    CANONICAL_RAW_TOP_LEVEL_KEYS,
    ProviderCapabilities,
    ProviderMode,
    missing_canonical_raw_keys,
    parse_provider_mode,
    raw_has_canonical_shape,
)
from src.fundamental_skill.real_stock_runner import run_real_stock


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, ProviderMode.AUTO),
        ("", ProviderMode.AUTO),
        ("auto", ProviderMode.AUTO),
        ("default", ProviderMode.AUTO),
        ("akshare", ProviderMode.AKSHARE),
        ("ak", ProviderMode.AKSHARE),
        ("tushare", ProviderMode.TUSHARE),
        ("ts", ProviderMode.TUSHARE),
        ("dual_compare", ProviderMode.DUAL_COMPARE),
        ("dual-compare", ProviderMode.DUAL_COMPARE),
        ("tushare_vs_akshare", ProviderMode.DUAL_COMPARE),
    ],
)
def test_parse_provider_mode(value, expected):
    assert parse_provider_mode(value) == expected


def test_parse_provider_mode_rejects_unknown_mode():
    with pytest.raises(ValueError, match="unsupported provider mode"):
        parse_provider_mode("live_realtime")


def test_provider_capabilities_supports_canonical_blocks():
    capabilities = ProviderCapabilities(provider_name="fake", news=True)

    for block_name in CANONICAL_RAW_BLOCKS:
        assert capabilities.supports_block(block_name)
    assert not capabilities.supports_block("minute_realtime")
    assert capabilities.realtime_market_data is False


def test_fake_provider_returns_canonical_raw_shape():
    raw = FakeDataProvider(name="fake_akshare").fetch_to_raw_json("sz002050", force_refresh=True)

    assert set(CANONICAL_RAW_TOP_LEVEL_KEYS) <= set(raw)
    assert missing_canonical_raw_keys(raw) == []
    assert raw_has_canonical_shape(raw)
    assert raw["meta"]["code"] == "002050"
    assert raw["meta"]["data_source"] == "fake_akshare"
    assert set(CANONICAL_RAW_BLOCKS) <= set(raw["blocks"])
    assert set(CANONICAL_RAW_BLOCKS) <= set(raw["fetch_status"])
    assert raw["errors"] == []
    for block_name in CANONICAL_RAW_BLOCKS:
        assert raw["fetch_status"][block_name]["success"] is True
        assert raw["fetch_status"][block_name]["source_name"] == "fake_akshare"


def test_missing_canonical_raw_keys_reports_only_top_level_contract():
    raw = {"meta": {}, "blocks": {}, "errors": []}

    assert missing_canonical_raw_keys(raw) == ["fetch_status"]
    assert raw_has_canonical_shape(raw) is False


def test_phase1_does_not_change_real_stock_runner_default_signature():
    signature = inspect.signature(run_real_stock)

    assert "connector" in signature.parameters
    assert "provider" not in signature.parameters
    assert "provider_mode" not in signature.parameters

