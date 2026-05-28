# -*- coding: utf-8 -*-

import inspect

import pytest

from src.fundamental_skill.research_report.csv_table_fact_converter import (
    DEFAULT_LOCAL_CSV_CAVEAT,
    DEFAULT_LOCAL_CSV_TABLE_QUALITY,
    CsvTableFactConverterMappingError,
    CsvTableFactConverterSecretError,
    CsvTableFactConverterValidationError,
    build_column_mapping,
    convert_normalized_table_to_table_facts,
    iter_mapped_rows,
)
import src.fundamental_skill.research_report.csv_table_fact_converter as converter_module


def _normalized_table(**overrides) -> dict:
    payload = {
        "version": "normalized_table.v1",
        "source_document_id": "doc_001",
        "source_table_id": "table_001",
        "source_file_path": "output/official_disclosures/local_structured_table_samples/600406_h1_product.csv",
        "source_format": "csv",
        "source_section": "主营业务分产品情况",
        "source_page_or_anchor": "",
        "table_title": "600406 2025H1 主营业务分产品情况",
        "headers": [
            "产品名称",
            "主营业务收入",
            "主营业务成本",
            "毛利率",
            "主营业务收入比上年同期增减",
            "主营业务成本比上年同期增减",
            "毛利率比上年同期增减",
        ],
        "rows": [
            ["电网智能", "12224749159.44", "8515559910.55", "30.34%", "28.37%", "34.00%", "减少2.93个百分点"],
            ["数能融合", "3900471200.41", "2987871514.67", "23.40%", "4.43%", "8.20%", "减少2.67个百分点"],
            ["能源低碳", "6541392925.48", "5129271270.93", "21.59%", "29.49%", "32.33%", "减少1.68个百分点"],
            ["工业互联", "1244708867.06", "995740014.98", "20.00%", "2.94%", "6.29%", "减少2.52个百分点"],
            ["集成及其他", "299843729.33", "194657180.84", "35.08%", "-58.60%", "-59.08%", "增加0.75个百分点"],
            ["合计", "24211165881.72", "17823099891.97", "26.38%", "19.60%", "23.73%", "减少2.46个百分点"],
        ],
        "row_count": 6,
        "column_count": 7,
        "detected_unit": "",
        "detected_period": "",
        "classification_hint": "product",
        "reader_warnings": [
            {"reason": "delimiter_sniffed", "detail": "CSV delimiter was inferred with csv.Sniffer: ','."},
            {"reason": "unit_not_detected", "detail": ""},
            {"reason": "period_not_detected", "detail": ""},
        ],
        "table_quality_hint": "structured_medium",
    }
    payload.update(overrides)
    return payload


def _convert(payload: dict | None = None, **overrides) -> dict:
    kwargs = {
        "period": "2025H1",
        "unit": "CNY",
        "denominator": "主营业务收入合计",
    }
    kwargs.update(overrides)
    return convert_normalized_table_to_table_facts(
        payload or _normalized_table(),
        **kwargs,
    )


def _caveat_reasons(payload: dict) -> set[str]:
    return {caveat["reason"] for caveat in payload["table_caveats"]}


def _warning_reasons(payload: dict) -> set[str]:
    return {warning["reason"] for warning in payload["conversion_warnings"]}


def _fact_for_segment(payload: dict, segment_name: str) -> dict:
    matches = [fact for fact in payload["table_facts"] if fact["segment_name"] == segment_name]
    assert matches, f"missing fact for {segment_name}"
    return matches[0]


def test_constants_match_design_defaults():
    assert DEFAULT_LOCAL_CSV_TABLE_QUALITY == "structured_medium"
    assert DEFAULT_LOCAL_CSV_CAVEAT == "local_structured_sample_requires_human_review"


def test_build_column_mapping_from_allowlist():
    mapping = build_column_mapping(_normalized_table()["headers"])

    assert mapping["segment_name"] == "产品名称"
    assert mapping["revenue"] == "主营业务收入"
    assert mapping["cost"] == "主营业务成本"
    assert mapping["gross_margin"] == "毛利率"
    assert mapping["revenue_yoy"] == "主营业务收入比上年同期增减"
    assert mapping["cost_yoy"] == "主营业务成本比上年同期增减"
    assert mapping["gross_margin_yoy_change"] == "毛利率比上年同期增减"


def test_valid_normalized_table_converts_to_revenue_facts():
    payload = _convert()

    assert payload["source_document_id"] == "doc_001"
    assert payload["source_table_id"] == "table_001"
    assert payload["not_for_trading_advice"] is True
    assert len(payload["table_facts"]) == 6
    assert payload["table_caveats"]
    assert {"电网智能", "数能融合", "合计"} <= {fact["segment_name"] for fact in payload["table_facts"]}


def test_facts_use_structured_medium_human_review_and_default_caveat():
    payload = _convert()

    for fact in payload["table_facts"]:
        assert fact["table_quality"] == "structured_medium"
        assert fact["needs_human_review"] is True
        assert DEFAULT_LOCAL_CSV_CAVEAT in fact["caveats"]
        assert fact["evidence_tier"] == "L1_official_disclosure"


def test_facts_include_source_location_and_column_map():
    payload = _convert()
    fact = _fact_for_segment(payload, "电网智能")

    assert fact["source_table_id"] == "table_001"
    assert fact["source_row_index"] == 1
    assert fact["source_column_name"] == "主营业务收入"
    assert fact["source_column_map"]["segment_name"] == "产品名称"
    assert fact["source_column_map"]["revenue"] == "主营业务收入"
    assert fact["source_column_map"]["denominator"] == "主营业务收入合计"


def test_facts_preserve_official_segment_name_and_raw_revenue_value():
    payload = _convert()
    fact = _fact_for_segment(payload, "数能融合")

    assert fact["segment_name"] == "数能融合"
    assert fact["value"] == "3900471200.41"
    assert isinstance(fact["value"], str)


def test_facts_use_explicit_period_unit_and_denominator():
    payload = _convert()
    fact = _fact_for_segment(payload, "合计")

    assert fact["period"] == "2025H1"
    assert fact["unit"] == "CNY"
    assert fact["denominator"] == "主营业务收入合计"
    assert fact["classification_type"] == "product"


def test_no_period_fails_closed_with_caveat():
    payload = convert_normalized_table_to_table_facts(
        _normalized_table(),
        unit="CNY",
        denominator="主营业务收入合计",
    )

    assert payload["table_facts"] == []
    assert "period_not_detected" in _caveat_reasons(payload)


def test_no_unit_fails_closed_with_caveat():
    payload = convert_normalized_table_to_table_facts(
        _normalized_table(),
        period="2025H1",
        denominator="主营业务收入合计",
    )

    assert payload["table_facts"] == []
    assert "unit_not_detected" in _caveat_reasons(payload)


def test_no_classification_fails_closed_with_caveat():
    payload = _convert(_normalized_table(classification_hint=""), classification_type=None)

    assert payload["table_facts"] == []
    assert "classification_not_detected" in _caveat_reasons(payload)


def test_explicit_classification_allows_missing_hint():
    payload = _convert(_normalized_table(classification_hint=""), classification_type="product")

    assert payload["table_facts"]
    assert {fact["classification_type"] for fact in payload["table_facts"]} == {"product"}


def test_missing_segment_column_fails_closed():
    payload = _normalized_table(
        headers=["主营业务收入", "主营业务成本"],
        rows=[["12224749159.44", "8515559910.55"]],
        row_count=1,
        column_count=2,
    )
    result = _convert(payload)

    assert result["table_facts"] == []
    assert "segment_column_missing" in _caveat_reasons(result)


def test_missing_revenue_column_fails_closed():
    payload = _normalized_table(
        headers=["产品名称", "主营业务成本"],
        rows=[["电网智能", "8515559910.55"]],
        row_count=1,
        column_count=2,
    )
    result = _convert(payload)

    assert result["table_facts"] == []
    assert "revenue_column_missing" in _caveat_reasons(result)


def test_ambiguous_header_fails_closed_with_caveat():
    payload = _normalized_table(
        headers=["产品名称", "产品", "主营业务收入"],
        rows=[["电网智能", "电网智能", "12224749159.44"]],
        row_count=1,
        column_count=3,
    )
    result = _convert(payload)

    assert result["table_facts"] == []
    assert "ambiguous_header" in _caveat_reasons(result)


def test_multiple_revenue_like_headers_are_ambiguous():
    with pytest.raises(CsvTableFactConverterMappingError, match="ambiguous_header"):
        build_column_mapping(["产品名称", "主营业务收入", "营业收入"])


def test_multiple_segment_like_headers_are_ambiguous():
    with pytest.raises(CsvTableFactConverterMappingError, match="ambiguous_header"):
        build_column_mapping(["产品名称", "业务板块", "主营业务收入"])


def test_explicit_mapping_resolves_legal_ambiguous_headers():
    normalized = _normalized_table(
        headers=["产品名称", "主营业务收入", "营业收入"],
        rows=[["电网智能", "12224749159.44", "12224749159.44"]],
        row_count=1,
        column_count=3,
    )

    payload = _convert(
        normalized,
        explicit_mapping={"segment_name": "产品名称", "revenue": "营业收入"},
    )

    assert len(payload["table_facts"]) == 1
    assert payload["table_facts"][0]["source_column_name"] == "营业收入"
    assert payload["table_facts"][0]["source_column_map"]["revenue"] == "营业收入"


def test_row_length_unstable_fails_closed_with_caveat():
    payload = _normalized_table(
        rows=[
            ["电网智能", "12224749159.44"],
            ["合计", "24211165881.72", "17823099891.97", "26.38%", "19.60%", "23.73%", "减少2.46个百分点"],
        ],
        row_count=2,
        reader_warnings=[{"reason": "row_length_unstable", "detail": ""}],
        table_quality_hint="partially_structured",
    )
    result = _convert(payload)

    assert result["table_facts"] == []
    assert "row_length_unstable" in _caveat_reasons(result)


def test_delimiter_sniffed_warning_is_propagated():
    payload = _convert()

    assert "delimiter_sniffed" in _caveat_reasons(payload)
    assert "delimiter_sniffed" in _warning_reasons(payload)
    assert all("delimiter_sniffed" in fact["caveats"] for fact in payload["table_facts"])


def test_explicit_mapping_works():
    normalized = _normalized_table(
        headers=["分类", "收入金额"],
        rows=[["电网智能", "12224749159.44"], ["合计", "24211165881.72"]],
        row_count=2,
        column_count=2,
        classification_hint="",
    )

    payload = convert_normalized_table_to_table_facts(
        normalized,
        period="2025H1",
        unit="CNY",
        denominator="主营业务收入合计",
        classification_type="product",
        explicit_mapping={"segment_name": "分类", "revenue": "收入金额"},
    )

    assert len(payload["table_facts"]) == 2
    assert _fact_for_segment(payload, "电网智能")["source_column_map"]["revenue"] == "收入金额"


def test_invalid_mapping_rejected():
    with pytest.raises(CsvTableFactConverterMappingError):
        build_column_mapping(["产品名称", "主营业务收入"], explicit_mapping={"revenue": "missing"})


def test_duplicate_explicit_mapping_header_rejected_as_ambiguous():
    with pytest.raises(CsvTableFactConverterMappingError, match="ambiguous_header"):
        build_column_mapping(
            ["产品名称", "主营业务收入", "主营业务收入"],
            explicit_mapping={"segment_name": "产品名称", "revenue": "主营业务收入"},
        )


def test_unit_not_detected_warning_blocks_without_explicit_unit():
    payload = convert_normalized_table_to_table_facts(
        _normalized_table(
            detected_unit="CNY",
            reader_warnings=[{"reason": "unit_not_detected", "detail": ""}],
        ),
        period="2025H1",
        denominator="主营业务收入合计",
    )

    assert payload["table_facts"] == []
    assert "unit_not_detected" in _caveat_reasons(payload)
    assert "unit_not_detected" in _warning_reasons(payload)


def test_period_not_detected_warning_blocks_without_explicit_period():
    payload = convert_normalized_table_to_table_facts(
        _normalized_table(
            detected_period="2025H1",
            reader_warnings=[{"reason": "period_not_detected", "detail": ""}],
        ),
        unit="CNY",
        denominator="主营业务收入合计",
    )

    assert payload["table_facts"] == []
    assert "period_not_detected" in _caveat_reasons(payload)
    assert "period_not_detected" in _warning_reasons(payload)


def test_explicit_period_and_unit_override_reader_warnings_but_preserve_caveats():
    payload = _convert(
        _normalized_table(
            detected_unit="CNY",
            detected_period="2025H1",
            reader_warnings=[
                {"reason": "unit_not_detected", "detail": ""},
                {"reason": "period_not_detected", "detail": ""},
            ],
        )
    )

    assert payload["table_facts"]
    assert {"unit_not_detected", "period_not_detected"} <= _caveat_reasons(payload)
    assert {"unit_not_detected", "period_not_detected"} <= _warning_reasons(payload)
    for fact in payload["table_facts"]:
        assert "unit_not_detected" in fact["caveats"]
        assert "period_not_detected" in fact["caveats"]


def test_missing_denominator_is_in_conversion_warnings_for_caveated_revenue_facts():
    payload = _convert(denominator=None)

    assert payload["table_facts"]
    assert "denominator_missing" in _caveat_reasons(payload)
    assert "denominator_missing" in _warning_reasons(payload)
    assert all("denominator_missing" in fact["caveats"] for fact in payload["table_facts"])


def test_explicit_denominator_omits_denominator_missing_warning():
    payload = _convert()

    assert payload["table_facts"]
    assert "denominator_missing" not in _caveat_reasons(payload)
    assert "denominator_missing" not in _warning_reasons(payload)
    assert all("denominator_missing" not in fact["caveats"] for fact in payload["table_facts"])


def test_caveat_only_table_quality_outputs_caveats_only():
    payload = _convert(table_quality="unusable")

    assert payload["table_facts"] == []
    assert "unusable_table" in _caveat_reasons(payload)
    assert {caveat["table_quality"] for caveat in payload["table_caveats"]} == {"unusable"}


def test_iter_mapped_rows_preserves_source_rows_and_total_row():
    rows = iter_mapped_rows(_normalized_table(), build_column_mapping(_normalized_table()["headers"]))

    assert rows[0]["segment_name"] == "电网智能"
    assert rows[0]["source_row_index"] == 1
    assert rows[0]["cells"][1] == "12224749159.44"
    assert rows[-1]["segment_name"] == "合计"
    assert rows[-1]["is_total_row"] is True


def test_missing_segment_value_is_skipped_and_caveated():
    payload = _normalized_table(rows=[["", "12224749159.44", "", "", "", "", ""]], row_count=1)
    result = _convert(payload)

    assert result["table_facts"] == []
    assert "segment_name_missing" in _caveat_reasons(result)


def test_forbidden_recommendation_keys_rejected():
    payload = _normalized_table()
    payload["buy"] = "forbidden"

    with pytest.raises(CsvTableFactConverterValidationError):
        _convert(payload)


def test_token_like_key_and_value_rejected_without_leaking_secret():
    secret_like = "Aa1234567890Bb1234567890Cc1234567890"

    with pytest.raises(CsvTableFactConverterSecretError) as key_exc:
        _convert(explicit_mapping={"api_token": ""})
    with pytest.raises(CsvTableFactConverterSecretError) as value_exc:
        _convert(_normalized_table(reader_warnings=[{"reason": "blocked", "detail": secret_like}]))

    assert "api_token" not in str(key_exc.value)
    assert secret_like not in str(value_exc.value)
    assert "<masked>" in str(key_exc.value)
    assert "<masked>" in str(value_exc.value)


@pytest.mark.parametrize(
    "value",
    [
        "Bearer abcdefghijklmnopqrstuvwxyz123456",
        "mcp://local/test",
        "config/.env",
        "C:\\Users\\Admin\\.ssh\\id_rsa",
    ],
)
def test_reject_bearer_remote_control_dotenv_and_local_secret_path(value):
    with pytest.raises(CsvTableFactConverterSecretError) as exc_info:
        _convert(denominator=value)

    assert value not in str(exc_info.value)
    assert "<masked>" in str(exc_info.value)


def test_no_provider_env_network_or_mcp_imports():
    source = inspect.getsource(converter_module)
    forbidden = [
        "CNInfo",
        "Tushare",
        "AkShare",
        "provider",
        "MCP",
        "requests",
        "urllib",
        "os.environ",
        "getenv",
        "subprocess",
        "TUSHARE_TOKEN",
    ]

    for marker in forbidden:
        assert marker not in source


def test_no_ocr_pdf_docx_html_excel_reader_imports():
    source = inspect.getsource(converter_module)
    forbidden = [
        "OCR",
        "pytesseract",
        "easyocr",
        "pdfplumber",
        "camelot",
        "tabula",
        "PyPDF",
        "pypdf",
        "pdfminer",
        "docx",
        "bs4",
        "BeautifulSoup",
        "pandas",
        "openpyxl",
        "old runner",
    ]

    for marker in forbidden:
        assert marker not in source


def test_no_real_output_writes():
    source = inspect.getsource(converter_module)
    public_names = {name for name in dir(converter_module) if not name.startswith("_")}

    assert not any(name.startswith("write_") for name in public_names)
    assert ".write_text" not in source
    assert ".write_bytes" not in source
