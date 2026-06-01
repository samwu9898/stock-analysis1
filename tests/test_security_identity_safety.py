import pytest

from fundamental_skill.data_verification.security_identity import (
    REJECTION_FORBIDDEN_MARKER_DETECTED,
    REJECTION_LIVE_LOOKUP_FORBIDDEN,
    REJECTION_NOT_FOR_TRADING_ADVICE_REQUIRED,
    REJECTION_OUTPUT_FIXTURE_MANIFEST_WRITE_FORBIDDEN,
    REJECTION_PDF_PARSER_FORBIDDEN,
    REJECTION_PROVIDER_LOOKUP_FORBIDDEN,
    REJECTION_TRADING_ADVICE_FORBIDDEN,
    STATUS_BLOCKED,
    SecurityIdentitySafetyError,
    assert_no_security_identity_forbidden_markers,
    normalize_security_identity,
)


def _blocked_reason(payload):
    identity = normalize_security_identity(payload)
    assert identity["identity_status"] == STATUS_BLOCKED
    return identity["rejection_reason"]


def _payload_with_note(note):
    return {
        "stock_code": "600406",
        "note": note,
        "not_for_trading_advice": True,
    }


def test_not_for_trading_advice_missing_rejected():
    assert _blocked_reason({"stock_code": "600406"}) == (
        REJECTION_NOT_FOR_TRADING_ADVICE_REQUIRED
    )


def test_not_for_trading_advice_false_rejected():
    assert _blocked_reason(
        {"stock_code": "600406", "not_for_trading_advice": False}
    ) == REJECTION_NOT_FOR_TRADING_ADVICE_REQUIRED


def test_not_for_trading_advice_non_bool_rejected():
    assert _blocked_reason(
        {"stock_code": "600406", "not_for_trading_advice": "true"}
    ) == REJECTION_NOT_FOR_TRADING_ADVICE_REQUIRED


def test_nested_forbidden_markers_are_rejected():
    payload = {
        "stock_code": "600406",
        "metadata": {"nested": ["safe", {"intent": "download PDF"}]},
        "not_for_trading_advice": True,
    }

    assert _blocked_reason(payload) == REJECTION_LIVE_LOOKUP_FORBIDDEN


def test_nested_forbidden_marker_keys_are_rejected():
    payload = {
        "stock_code": "600406",
        "metadata": {"download": "requested"},
        "not_for_trading_advice": True,
    }

    assert _blocked_reason(payload) == REJECTION_LIVE_LOOKUP_FORBIDDEN


@pytest.mark.parametrize("marker", ["token", ".env", "tushare_token"])
def test_token_env_and_tushare_token_markers_rejected(marker):
    assert _blocked_reason(_payload_with_note(marker)) == (
        REJECTION_FORBIDDEN_MARKER_DETECTED
    )


@pytest.mark.parametrize("marker", ["provider live", "AkShare", "Tushare"])
def test_provider_markers_rejected(marker):
    assert _blocked_reason(_payload_with_note(marker)) == (
        REJECTION_PROVIDER_LOOKUP_FORBIDDEN
    )


@pytest.mark.parametrize("marker", ["network", "HTTP", "fetch", "download"])
def test_network_markers_rejected(marker):
    assert _blocked_reason(_payload_with_note(marker)) == REJECTION_LIVE_LOOKUP_FORBIDDEN


@pytest.mark.parametrize("marker", ["CNInfo live", "SSE live"])
def test_cninfo_and_sse_live_markers_rejected(marker):
    assert _blocked_reason(_payload_with_note(marker)) == REJECTION_LIVE_LOOKUP_FORBIDDEN


@pytest.mark.parametrize("marker", ["PDF parser", "table extractor", "parse PDF"])
def test_pdf_parser_markers_rejected(marker):
    assert _blocked_reason(_payload_with_note(marker)) == REJECTION_PDF_PARSER_FORBIDDEN


def test_metric_extraction_marker_rejected():
    assert _blocked_reason(_payload_with_note("metric extraction")) == (
        REJECTION_FORBIDDEN_MARKER_DETECTED
    )


def test_official_metric_fact_marker_rejected():
    assert _blocked_reason(_payload_with_note("official_metric_fact")) == (
        REJECTION_FORBIDDEN_MARKER_DETECTED
    )


def test_provider_official_conflict_marker_rejected():
    assert _blocked_reason(_payload_with_note("provider_official_conflict")) == (
        REJECTION_FORBIDDEN_MARKER_DETECTED
    )


def test_report_v1_marker_rejected():
    assert _blocked_reason(_payload_with_note("Report V1")) == (
        REJECTION_FORBIDDEN_MARKER_DETECTED
    )


@pytest.mark.parametrize(
    "marker",
    ["accepted manifest write", "output baseline write", "fixture write"],
)
def test_accepted_manifest_output_baseline_and_fixture_write_markers_rejected(marker):
    assert _blocked_reason(_payload_with_note(marker)) == (
        REJECTION_OUTPUT_FIXTURE_MANIFEST_WRITE_FORBIDDEN
    )


@pytest.mark.parametrize(
    "marker",
    [
        "buy",
        "sell",
        "hold",
        "target price",
        "portfolio",
        "position",
        "technical signal",
    ],
)
def test_trading_signal_markers_rejected(marker):
    assert _blocked_reason(_payload_with_note(marker)) == (
        REJECTION_TRADING_ADVICE_FORBIDDEN
    )


@pytest.mark.parametrize(
    "marker",
    [
        "买入",
        "卖出",
        "持有",
        "目标价",
        "仓位",
        "组合",
        "技术信号",
        "投资建议",
    ],
)
def test_chinese_trading_advice_markers_rejected(marker):
    assert _blocked_reason(_payload_with_note(marker)) == (
        REJECTION_TRADING_ADVICE_FORBIDDEN
    )


@pytest.mark.parametrize("marker", ["下载", "网络", "联网"])
def test_chinese_network_markers_rejected(marker):
    assert _blocked_reason(_payload_with_note(marker)) == REJECTION_LIVE_LOOKUP_FORBIDDEN


@pytest.mark.parametrize("marker", ["解析PDF", "PDF解析", "表格抽取"])
def test_chinese_pdf_markers_rejected(marker):
    assert _blocked_reason(_payload_with_note(marker)) == REJECTION_PDF_PARSER_FORBIDDEN


@pytest.mark.parametrize("marker", ["指标抽取", "正式研报"])
def test_chinese_metric_and_report_markers_rejected(marker):
    assert _blocked_reason(_payload_with_note(marker)) == (
        REJECTION_FORBIDDEN_MARKER_DETECTED
    )


@pytest.mark.parametrize("marker", ["输出基线", "写入fixture", "写入accepted manifest"])
def test_chinese_output_write_markers_rejected(marker):
    assert _blocked_reason(_payload_with_note(marker)) == (
        REJECTION_OUTPUT_FIXTURE_MANIFEST_WRITE_FORBIDDEN
    )


@pytest.mark.parametrize(
    ("marker", "reason"),
    [
        ("CNInfo live lookup", REJECTION_LIVE_LOOKUP_FORBIDDEN),
        ("provider live lookup", REJECTION_PROVIDER_LOOKUP_FORBIDDEN),
        ("PDF parser", REJECTION_PDF_PARSER_FORBIDDEN),
        ("output baseline write", REJECTION_OUTPUT_FIXTURE_MANIFEST_WRITE_FORBIDDEN),
    ],
)
def test_live_provider_pdf_parser_and_output_write_intents_rejected(marker, reason):
    assert _blocked_reason(_payload_with_note(marker)) == reason


def test_assert_no_security_identity_forbidden_markers_raises_on_nested_value():
    with pytest.raises(SecurityIdentitySafetyError):
        assert_no_security_identity_forbidden_markers({"x": ["safe", "target price"]})
