# -*- coding: utf-8 -*-

import pytest

from src.fundamental_skill.research_planning.autonomous_ticker_research_schema import (
    build_planning_payload,
    validate_planning_payload,
)


def _valid_payload(**overrides):
    payload = build_planning_payload(
        stock_code="600406",
        company_name="NARI Technology",
        generated_at="2026-05-29T00:00:00+00:00",
        identity_resolution_status="resolved",
        market="CN",
        exchange="SSE",
        report_readiness_level="data_collection_required",
        fail_closed_reason="Planning only; data collection is required.",
    )
    payload.update(overrides)
    return payload


def test_trading_advice_phrase_is_rejected():
    payload = _valid_payload(caveats=["Do not buy this stock."])

    with pytest.raises(ValueError, match="trading advice"):
        validate_planning_payload(payload)


def test_token_like_value_is_rejected_and_masked():
    token_value = "sk-" + "AbCdEfGhIjKlMnOpQrStUvWxYz123456"
    payload = _valid_payload(caveats=[token_value])

    with pytest.raises(ValueError) as exc_info:
        validate_planning_payload(payload)

    message = str(exc_info.value)
    assert token_value not in message
    assert "credential" in message


@pytest.mark.parametrize(
    "secret_key",
    [
        "TUSHARE_TOKEN",
        "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8",
    ],
)
def test_token_like_dict_key_is_rejected_without_leaking_key(secret_key):
    payload = _valid_payload()
    payload[secret_key] = "placeholder"

    with pytest.raises(ValueError) as exc_info:
        validate_planning_payload(payload)

    message = str(exc_info.value)
    assert secret_key not in message
    assert "<masked_key>" in message


@pytest.mark.parametrize(
    "blocked_value, expected",
    [
        ("mcp://local-server/tools", "MCP URL"),
        ("C:/workspace/.env", ".env"),
        ("C:/Users/Admin/.aws/credentials", "credential path"),
    ],
)
def test_mcp_dotenv_and_local_secret_paths_are_rejected(blocked_value, expected):
    payload = _valid_payload(caveats=[blocked_value])

    with pytest.raises(ValueError, match=expected):
        validate_planning_payload(payload)


@pytest.mark.parametrize(
    "marker, expected",
    [
        ("accepted_manifest_update", "accepted manifest"),
        ("fixture_promotion", "fixture promotion"),
        ("provider_primary_switch", "provider primary switch"),
        ("research_report_v1_update", "Research Report V1"),
    ],
)
def test_forbidden_runtime_mutation_markers_are_rejected(marker, expected):
    payload = _valid_payload(caveats=[marker])

    with pytest.raises(ValueError, match=expected):
        validate_planning_payload(payload)
