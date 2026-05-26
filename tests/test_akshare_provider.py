# -*- coding: utf-8 -*-

import inspect

from src.fundamental_skill.data_providers.akshare_provider import AKSHARE_RAW_BLOCKS, AkShareProvider
from src.fundamental_skill.data_providers.schemas import CANONICAL_RAW_BLOCKS, raw_has_canonical_shape


def _assert_secret_not_rendered(secret: str, text: str) -> None:
    if secret in text:
        raise AssertionError("secret-like value was rendered")


class FakeRealDataConnector:
    def __init__(self, raw=None):
        self.raw = raw if raw is not None else _canonical_raw()
        self.calls = []

    def fetch_to_raw_json(self, stock_code, output_path=None, force_refresh=False):
        self.calls.append(
            {
                "stock_code": stock_code,
                "output_path": output_path,
                "force_refresh": force_refresh,
            }
        )
        return self.raw


def _canonical_raw():
    return {
        "meta": {
            "code": "002050",
            "generated_at": "2026-05-26T00:00:00",
            "data_source": "akshare",
            "connector_version": "real_data_connector.test",
        },
        "blocks": {
            "basic_info": [{"stock_code": "002050", "stock_name": "Test Stock"}],
            "financial_indicator": [{"period": "20251231", "revenue": 1.0}],
            "valuation": [{"period": "2026-05-26", "pe_ttm": 10.0}],
            "business_composition": [{"segment_name": "core", "revenue": 1.0}],
            "news": [{"title": "news"}],
            "commodity_prices": [{"commodity_name": "copper"}],
            "commodity_price_foreign_reference": [{"commodity_name": "copper"}],
        },
        "fetch_status": {
            "basic_info": {"success": True, "error": None, "missing_fields": []},
            "financial_indicator": {"success": True, "error": None, "missing_fields": []},
            "valuation": {"success": True, "error": None, "missing_fields": []},
            "business_composition": {"success": True, "error": None, "missing_fields": []},
            "news": {"success": False, "error": "upstream news failed", "missing_fields": ["title"]},
            "commodity_prices": {
                "success": True,
                "error": None,
                "missing_fields": ["external.commodity_prices.freshness"],
            },
        },
        "errors": ["news: upstream news failed"],
    }


def test_akshare_provider_wraps_real_data_connector_without_reshaping_raw():
    raw = _canonical_raw()
    connector = FakeRealDataConnector(raw=raw)
    provider = AkShareProvider(connector=connector)

    returned = provider.fetch_to_raw_json("sz002050", force_refresh=True)

    assert returned is raw
    assert raw_has_canonical_shape(returned)
    assert set(CANONICAL_RAW_BLOCKS) <= set(returned["blocks"])
    assert returned["blocks"]["commodity_prices"] == [{"commodity_name": "copper"}]
    assert returned["fetch_status"]["news"]["error"] == "upstream news failed"
    assert returned["errors"] == ["news: upstream news failed"]
    assert connector.calls == [
        {"stock_code": "sz002050", "output_path": None, "force_refresh": True}
    ]


def test_akshare_provider_lazily_builds_connector_and_passes_default_force_refresh():
    connectors = []

    def factory():
        connector = FakeRealDataConnector()
        connectors.append(connector)
        return connector

    provider = AkShareProvider(connector_factory=factory)

    returned = provider.fetch_to_raw_json("002050")

    assert returned is connectors[0].raw
    assert connectors[0].calls == [
        {"stock_code": "002050", "output_path": None, "force_refresh": False}
    ]


def test_akshare_capabilities_describe_current_adapter_without_realtime_claims():
    capabilities = AkShareProvider(connector=FakeRealDataConnector()).capabilities()

    assert capabilities.provider_name == "akshare"
    assert capabilities.raw_blocks == AKSHARE_RAW_BLOCKS
    assert capabilities.news is True
    assert capabilities.commodity_prices is True
    assert capabilities.low_frequency_market_data is False
    assert capabilities.realtime_market_data is False
    assert capabilities.supports_block("commodity_prices")
    assert not capabilities.supports_block("minute_realtime")


def test_akshare_provider_metadata_does_not_expose_sensitive_values():
    secret = "FAKE_TOKEN_FOR_TESTING_ONLY__NOT_REAL__XYZ_1234567890"
    provider = AkShareProvider(connector=FakeRealDataConnector())
    metadata_text = repr(provider.capabilities()) + repr(provider)

    _assert_secret_not_rendered(secret, metadata_text)
    assert "token" not in metadata_text.lower()
    assert "mcp" not in metadata_text.lower()


def test_akshare_provider_module_does_not_import_tushare_mcp_or_http_clients():
    source = inspect.getsource(inspect.getmodule(AkShareProvider))

    assert "import tushare" not in source
    assert "requests" not in source
    assert "httpx" not in source
    assert "urllib" not in source
    assert "mcp" not in source.lower()
