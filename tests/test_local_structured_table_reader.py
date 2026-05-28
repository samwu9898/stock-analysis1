# -*- coding: utf-8 -*-

import inspect
from pathlib import Path

import pytest

from src.fundamental_skill.research_report.local_structured_table_reader import (
    DEFAULT_MAX_CSV_BYTES,
    NORMALIZED_TABLE_VERSION,
    SUPPORTED_TABLE_FORMATS,
    LocalStructuredTableFormatError,
    LocalStructuredTablePathBoundaryError,
    LocalStructuredTableSecretError,
    LocalStructuredTableValidationError,
    build_reader_warning,
    detect_classification_hint,
    detect_table_period,
    detect_table_unit,
    read_local_csv_table,
    validate_normalized_table,
)
import src.fundamental_skill.research_report.local_structured_table_reader as reader_module


def _payload(**overrides) -> dict:
    payload = {
        "version": NORMALIZED_TABLE_VERSION,
        "source_document_id": "doc_001",
        "source_table_id": "table_001",
        "source_file_path": "sample.csv",
        "source_format": "csv",
        "source_section": "主营业务分产品情况",
        "source_page_or_anchor": "",
        "table_title": "",
        "headers": ["产品", "2025H1营业收入（万元）"],
        "rows": [["电网自动化", "123.45"]],
        "row_count": 1,
        "column_count": 2,
        "detected_unit": "万元",
        "detected_period": "2025H1",
        "classification_hint": "product",
        "reader_warnings": [],
        "table_quality_hint": "structured_medium",
    }
    payload.update(overrides)
    return payload


def _warning_reasons(payload: dict) -> set[str]:
    return {warning["reason"] for warning in payload["reader_warnings"]}


def test_constants_match_design_values():
    assert NORMALIZED_TABLE_VERSION == "normalized_table.v1"
    assert SUPPORTED_TABLE_FORMATS == {"csv"}
    assert DEFAULT_MAX_CSV_BYTES == 2_000_000


def test_read_valid_csv_from_tmpdir(tmp_path):
    path = tmp_path / "business.csv"
    path.write_text("产品,2025H1营业收入（万元）\n电网自动化,123.45\n", encoding="utf-8")

    payload = read_local_csv_table(
        path,
        repo_root=tmp_path,
        source_document_id="doc_001",
        source_table_id="table_001",
        source_section="主营业务分产品情况",
    )

    assert payload["version"] == NORMALIZED_TABLE_VERSION
    assert payload["source_file_path"] == "business.csv"
    assert payload["source_format"] == "csv"
    assert payload["headers"] == ["产品", "2025H1营业收入（万元）"]
    assert payload["rows"] == [["电网自动化", "123.45"]]
    assert payload["row_count"] == 1
    assert payload["column_count"] == 2
    assert payload["detected_unit"] == "万元"
    assert payload["detected_period"] == "2025H1"
    assert payload["classification_hint"] == "product"
    assert payload["table_quality_hint"] == "structured_medium"
    assert "delimiter_sniffed" in _warning_reasons(payload)


def test_utf8_sig_bom_handled(tmp_path):
    path = tmp_path / "bom.csv"
    path.write_bytes("产品,营业收入（万元）\n电网自动化,123\n".encode("utf-8-sig"))

    payload = read_local_csv_table(
        path,
        repo_root=tmp_path,
        source_document_id="doc_001",
        source_table_id="table_001",
    )

    assert payload["headers"][0] == "产品"
    assert not payload["headers"][0].startswith("\ufeff")


def test_custom_delimiter(tmp_path):
    path = tmp_path / "semicolon.csv"
    path.write_text("产品;营业收入（万元）\n电网自动化;123\n", encoding="utf-8")

    payload = read_local_csv_table(
        path,
        repo_root=tmp_path,
        source_document_id="doc_001",
        source_table_id="table_001",
        delimiter=";",
    )

    assert payload["headers"] == ["产品", "营业收入（万元）"]
    assert payload["rows"] == [["电网自动化", "123"]]
    assert "delimiter_sniffed" not in _warning_reasons(payload)


def test_delimiter_fallback_warning(tmp_path):
    path = tmp_path / "single_column.csv"
    path.write_text("产品\n电网自动化\n", encoding="utf-8")

    payload = read_local_csv_table(
        path,
        repo_root=tmp_path,
        source_document_id="doc_001",
        source_table_id="table_001",
    )

    assert "delimiter_fallback" in _warning_reasons(payload)
    assert payload["headers"] == ["产品"]
    assert payload["rows"] == [["电网自动化"]]


def test_headers_and_rows_preserved_as_raw_strings(tmp_path):
    path = tmp_path / "preserve.csv"
    path.write_text(" 产品 ,营业收入（万元）,空列\n 电网自动化 ,00123.450,\n\n", encoding="utf-8")

    payload = read_local_csv_table(
        path,
        repo_root=tmp_path,
        source_document_id="doc_001",
        source_table_id="table_001",
    )

    assert payload["headers"] == [" 产品 ", "营业收入（万元）", "空列"]
    assert payload["rows"] == [[" 电网自动化 ", "00123.450", ""], []]
    assert payload["rows"][0][1] == "00123.450"
    assert "blank_row_present" in _warning_reasons(payload)
    assert "row_length_unstable" in _warning_reasons(payload)


def test_no_numeric_conversion(tmp_path):
    path = tmp_path / "numeric.csv"
    path.write_text("产品,营业收入（万元）\n电网自动化,123.45\n", encoding="utf-8")

    payload = read_local_csv_table(
        path,
        repo_root=tmp_path,
        source_document_id="doc_001",
        source_table_id="table_001",
    )

    assert payload["rows"][0][1] == "123.45"
    assert isinstance(payload["rows"][0][1], str)


def test_empty_header_warning(tmp_path):
    path = tmp_path / "empty_header.csv"
    path.write_text("产品,,营业收入（万元）\n电网自动化,,123\n", encoding="utf-8")

    payload = read_local_csv_table(
        path,
        repo_root=tmp_path,
        source_document_id="doc_001",
        source_table_id="table_001",
    )

    assert "empty_header" in _warning_reasons(payload)
    assert payload["headers"] == ["产品", "", "营业收入（万元）"]


def test_row_length_unstable_warning(tmp_path):
    path = tmp_path / "ragged.csv"
    path.write_text("产品,营业收入（万元）\n电网自动化,123\n工业控制\n", encoding="utf-8")

    payload = read_local_csv_table(
        path,
        repo_root=tmp_path,
        source_document_id="doc_001",
        source_table_id="table_001",
    )

    assert "row_length_unstable" in _warning_reasons(payload)
    assert payload["table_quality_hint"] == "partially_structured"


def test_detect_unit_from_header():
    assert detect_table_unit(["产品", "营业收入（万元）"], [["电网自动化", "123"]]) == "万元"


def test_detect_period_from_header_or_row_only_when_explicit():
    assert detect_table_period(["产品", "2025H1营业收入"], [["电网自动化", "123"]]) == "2025H1"
    assert detect_table_period(["产品", "营业收入"], [["报告期：2025年半年度", "123"]]) == "2025H1"
    assert detect_table_period(["产品", "营业收入"], [["电网自动化", "123"]]) == ""


def test_classification_hint_from_source_section():
    assert detect_classification_hint([], [], source_section="主营业务分产品情况") == "product"
    assert detect_classification_hint([], [], source_section="主营业务分行业情况") == "industry"
    assert detect_classification_hint([], [], source_section="主营业务分地区情况") == "region"


def test_validate_normalized_table_success():
    validate_normalized_table(_payload())


def test_build_reader_warning_schema():
    assert build_reader_warning("row_length_unstable", detail="row 2") == {
        "reason": "row_length_unstable",
        "detail": "row 2",
    }


def test_reject_invalid_version():
    with pytest.raises(LocalStructuredTableValidationError):
        validate_normalized_table(_payload(version="normalized_table.v0"))


def test_reject_missing_source_document_id():
    with pytest.raises(LocalStructuredTableValidationError):
        validate_normalized_table(_payload(source_document_id=""))


def test_reject_missing_source_table_id():
    with pytest.raises(LocalStructuredTableValidationError):
        validate_normalized_table(_payload(source_table_id=""))


def test_reject_invalid_source_format():
    with pytest.raises(LocalStructuredTableValidationError):
        validate_normalized_table(_payload(source_format="xlsx"))


def test_reject_row_count_mismatch():
    with pytest.raises(LocalStructuredTableValidationError):
        validate_normalized_table(_payload(row_count=2))


def test_reject_column_count_mismatch():
    with pytest.raises(LocalStructuredTableValidationError):
        validate_normalized_table(_payload(column_count=3))


def test_reject_non_string_cell():
    with pytest.raises(LocalStructuredTableValidationError):
        validate_normalized_table(_payload(rows=[["电网自动化", 123]]))


def test_reject_unsupported_suffix(tmp_path):
    path = tmp_path / "table.txt"
    path.write_text("产品,营业收入\n电网自动化,123\n", encoding="utf-8")

    with pytest.raises(LocalStructuredTableFormatError):
        read_local_csv_table(path, repo_root=tmp_path, source_document_id="doc_001", source_table_id="table_001")


def test_reject_path_traversal(tmp_path):
    outside = tmp_path.parent / "outside.csv"
    outside.write_text("产品,营业收入\n电网自动化,123\n", encoding="utf-8")

    with pytest.raises(LocalStructuredTablePathBoundaryError):
        read_local_csv_table(
            tmp_path / ".." / outside.name,
            repo_root=tmp_path,
            source_document_id="doc_001",
            source_table_id="table_001",
        )


def test_reject_repo_root_escape(tmp_path):
    outside = tmp_path.parent / f"{tmp_path.name}_outside.csv"
    outside.write_text("产品,营业收入\n电网自动化,123\n", encoding="utf-8")

    with pytest.raises(LocalStructuredTablePathBoundaryError):
        read_local_csv_table(
            outside.resolve(strict=False),
            repo_root=tmp_path,
            source_document_id="doc_001",
            source_table_id="table_001",
        )


def test_reject_too_large_csv(tmp_path):
    path = tmp_path / "too_large.csv"
    path.write_bytes(b"x" * (DEFAULT_MAX_CSV_BYTES + 1))

    with pytest.raises(LocalStructuredTableFormatError):
        read_local_csv_table(path, repo_root=tmp_path, source_document_id="doc_001", source_table_id="table_001")


def test_reject_binary_file(tmp_path):
    path = tmp_path / "binary.csv"
    path.write_bytes(b"abc\x00def")

    with pytest.raises(LocalStructuredTableFormatError):
        read_local_csv_table(path, repo_root=tmp_path, source_document_id="doc_001", source_table_id="table_001")


def test_reject_token_like_key_and_value_without_leaking_secret():
    secret_like = "Aa1234567890Bb1234567890Cc1234567890"

    with pytest.raises(LocalStructuredTableSecretError) as key_exc:
        validate_normalized_table(_payload(api_token=""))
    with pytest.raises(LocalStructuredTableSecretError) as value_exc:
        validate_normalized_table(_payload(reader_warnings=[{"reason": "secret", "detail": secret_like}]))

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
    with pytest.raises(LocalStructuredTableSecretError) as exc_info:
        validate_normalized_table(_payload(reader_warnings=[{"reason": "blocked", "detail": value}]))

    assert value not in str(exc_info.value)
    assert "<masked>" in str(exc_info.value)


def test_reject_secret_like_csv_text(tmp_path):
    path = tmp_path / "secret.csv"
    path.write_text("产品,备注\n电网自动化,Bearer abcdefghijklmnopqrstuvwxyz123456\n", encoding="utf-8")

    with pytest.raises(LocalStructuredTableSecretError):
        read_local_csv_table(path, repo_root=tmp_path, source_document_id="doc_001", source_table_id="table_001")


def test_no_provider_env_network_or_mcp_imports():
    source = inspect.getsource(reader_module)
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


def test_no_ocr_document_markup_workbook_or_table_extraction_imports():
    source = inspect.getsource(reader_module)
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


def test_no_real_output_writes(tmp_path):
    source = inspect.getsource(reader_module)
    public_names = {name for name in dir(reader_module) if not name.startswith("_")}
    path = tmp_path / "input.csv"
    path.write_text("产品,营业收入（万元）\n电网自动化,123\n", encoding="utf-8")
    before = {child.name for child in tmp_path.iterdir()}

    read_local_csv_table(path, repo_root=tmp_path, source_document_id="doc_001", source_table_id="table_001")

    assert not any(name.startswith("write_") for name in public_names)
    assert ".write_text" not in source
    assert ".write_bytes" not in source
    assert {child.name for child in tmp_path.iterdir()} == before
