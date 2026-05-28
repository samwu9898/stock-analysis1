# -*- coding: utf-8 -*-

import copy
import hashlib
import inspect
import json
from pathlib import Path

import pytest

from src.fundamental_skill.research_report.official_disclosure_parser import (
    DEFAULT_OFFICIAL_DISCLOSURE_OUTPUT_DIR,
    OFFICIAL_DISCLOSURE_VERSION,
    PARSER_VERSION,
    OfficialDisclosureParserError,
    OfficialDisclosurePathBoundaryError,
    OfficialDisclosureSecretError,
    OfficialDisclosureValidationError,
    build_official_disclosure_facts,
    extract_main_business_candidate,
    extract_periodic_report_basics,
    read_local_official_text,
    read_official_disclosure_facts,
    validate_official_disclosure_facts,
    write_official_disclosure_facts,
)
import src.fundamental_skill.research_report.official_disclosure_parser as parser_module


def _source_document(**overrides) -> dict:
    doc = {
        "source_document_id": "doc_001",
        "document_type": "annual_report",
        "title": "国电南瑞2025年年度报告",
        "report_period": "2025A",
        "disclosure_date": "2026-04-30",
        "source_origin": "local_downloaded_official_disclosure",
        "source_uri_or_path": "local/600406_annual_report.txt",
        "sha256": "a" * 64,
        "text_extraction_method": "plain_text",
        "text_extraction_quality": "medium",
        "caveats": [],
    }
    doc.update(overrides)
    return doc


def _fact(**overrides) -> dict:
    fact = {
        "fact_id": "fact_001",
        "field_path": "basic_info.main_business_official_text",
        "value": "公司主要从事电网自动化及工业控制相关业务。",
        "unit": None,
        "period": "2025A",
        "source_document_id": "doc_001",
        "source_section": "主营业务",
        "source_page_or_anchor": "",
        "evidence_tier": "L1_official_disclosure",
        "extraction_confidence": "medium",
        "needs_human_review": True,
        "caveats": [],
    }
    fact.update(overrides)
    return fact


def _payload(**overrides) -> dict:
    payload = {
        "version": OFFICIAL_DISCLOSURE_VERSION,
        "code": "600406",
        "company_name": "国电南瑞",
        "created_at": "2026-05-28T00:00:00+00:00",
        "parser_version": PARSER_VERSION,
        "source_documents": [_source_document()],
        "extracted_facts": [_fact()],
        "extraction_warnings": [],
        "data_quality_caveats": [],
        "not_for_trading_advice": True,
    }
    payload.update(overrides)
    return payload


def test_build_valid_payload():
    payload = build_official_disclosure_facts(
        code="600406",
        company_name="国电南瑞",
        source_documents=[_source_document()],
        extracted_facts=[_fact()],
        created_at="2026-05-28T00:00:00+00:00",
    )

    assert payload["version"] == OFFICIAL_DISCLOSURE_VERSION
    assert payload["parser_version"] == PARSER_VERSION
    assert payload["not_for_trading_advice"] is True
    assert payload["source_documents"][0]["source_origin"] == "local_downloaded_official_disclosure"


def test_validate_valid_payload():
    validate_official_disclosure_facts(_payload())


def test_reject_invalid_version():
    payload = _payload(version="official_disclosure_facts.v0")

    with pytest.raises(OfficialDisclosureValidationError):
        validate_official_disclosure_facts(payload)


def test_reject_invalid_parser_version():
    payload = _payload(parser_version="minimal_official_disclosure_parser.v0")

    with pytest.raises(OfficialDisclosureValidationError):
        validate_official_disclosure_facts(payload)


def test_reject_invalid_code():
    payload = _payload(code="60040")

    with pytest.raises(OfficialDisclosureValidationError):
        validate_official_disclosure_facts(payload)


def test_reject_not_for_trading_advice_false():
    payload = _payload(not_for_trading_advice=False)

    with pytest.raises(OfficialDisclosureValidationError):
        validate_official_disclosure_facts(payload)


def test_reject_duplicate_source_document_id():
    payload = _payload(source_documents=[_source_document(), _source_document(title="duplicate")])

    with pytest.raises(OfficialDisclosureValidationError):
        validate_official_disclosure_facts(payload)


def test_reject_duplicate_fact_id():
    payload = _payload(extracted_facts=[_fact(), _fact(field_path="risk.regulatory_inquiry")])

    with pytest.raises(OfficialDisclosureValidationError):
        validate_official_disclosure_facts(payload)


def test_reject_invalid_document_type():
    payload = _payload(source_documents=[_source_document(document_type="broker_report")])

    with pytest.raises(OfficialDisclosureValidationError):
        validate_official_disclosure_facts(payload)


def test_reject_invalid_evidence_tier():
    payload = _payload(extracted_facts=[_fact(evidence_tier="L0_guess")])

    with pytest.raises(OfficialDisclosureValidationError):
        validate_official_disclosure_facts(payload)


def test_reject_invalid_extraction_confidence():
    payload = _payload(extracted_facts=[_fact(extraction_confidence="certain")])

    with pytest.raises(OfficialDisclosureValidationError):
        validate_official_disclosure_facts(payload)


def test_reject_fact_referencing_unknown_document():
    payload = _payload(extracted_facts=[_fact(source_document_id="doc_missing")])

    with pytest.raises(OfficialDisclosureValidationError):
        validate_official_disclosure_facts(payload)


def test_missing_l1_source_location_is_rejected_even_with_human_review():
    payload = _payload(extracted_facts=[_fact(source_section="", source_page_or_anchor="", needs_human_review=True)])

    with pytest.raises(OfficialDisclosureValidationError):
        validate_official_disclosure_facts(payload)


@pytest.mark.parametrize("key", ["buy", "sell", "target_price", "position", "portfolio_weight"])
def test_reject_forbidden_recommendation_keys(key):
    payload = _payload()
    payload[key] = "forbidden"

    with pytest.raises(OfficialDisclosureValidationError):
        validate_official_disclosure_facts(payload)


def test_reject_token_like_key():
    payload = _payload()
    payload["api_token"] = ""

    with pytest.raises(OfficialDisclosureSecretError):
        validate_official_disclosure_facts(payload)


def test_reject_token_like_value():
    payload = _payload()
    payload["data_quality_caveats"] = ["Aa1234567890Bb1234567890Cc1234567890"]

    with pytest.raises(OfficialDisclosureSecretError):
        validate_official_disclosure_facts(payload)


@pytest.mark.parametrize(
    "value",
    [
        "Bearer abcdefghijklmnopqrstuvwxyz123456",
        "mcp://local/test",
        "config/.env",
        "C:\\Users\\Admin\\.ssh\\id_rsa",
    ],
)
def test_reject_bearer_mcp_dotenv_and_local_secret_path(value):
    payload = _payload(data_quality_caveats=[value])

    with pytest.raises(OfficialDisclosureSecretError):
        validate_official_disclosure_facts(payload)


def test_local_text_reader_reads_txt_and_md_from_tmpdir(tmp_path):
    txt = tmp_path / "annual.txt"
    md = tmp_path / "annual.md"
    txt.write_text("主营业务：公司主要从事电网自动化业务。", encoding="utf-8")
    md.write_text("# 年度报告\n主营业务：公司主要从事控制系统业务。", encoding="utf-8")

    txt_draft = read_local_official_text(txt, repo_root=tmp_path)
    md_draft = read_local_official_text(md, repo_root=tmp_path)

    assert txt_draft["text"].startswith("主营业务")
    assert md_draft["text"].startswith("# 年度报告")
    assert txt_draft["source_uri_or_path"] == "annual.txt"
    assert md_draft["source_uri_or_path"] == "annual.md"


def test_local_text_reader_reads_html_as_plain_text_from_tmpdir(tmp_path):
    html = tmp_path / "annual.html"
    html.write_text("<html><body>主营业务：公司主要从事电网自动化业务。</body></html>", encoding="utf-8")

    draft = read_local_official_text(html, repo_root=tmp_path)

    assert "主营业务" in draft["text"]
    assert draft["source_uri_or_path"] == "annual.html"
    assert draft["caveats"] == ["HTML file was read as plain text; markup was not structurally parsed."]


def test_local_text_reader_blocks_path_traversal(tmp_path):
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("text", encoding="utf-8")

    with pytest.raises(OfficialDisclosurePathBoundaryError):
        read_local_official_text(tmp_path / ".." / outside.name, repo_root=tmp_path)


def test_local_text_reader_blocks_clean_absolute_repo_root_escape(tmp_path):
    outside = tmp_path.parent / f"{tmp_path.name}_outside.txt"
    outside.write_text("text", encoding="utf-8")

    with pytest.raises(OfficialDisclosurePathBoundaryError):
        read_local_official_text(outside.resolve(strict=False), repo_root=tmp_path)


def test_local_text_reader_blocks_unsupported_suffix_and_binary_file(tmp_path):
    pdf = tmp_path / "annual.pdf"
    pdf.write_text("not parsed", encoding="utf-8")
    binary = tmp_path / "annual.txt"
    binary.write_bytes(b"abc\x00def")

    with pytest.raises(OfficialDisclosureParserError):
        read_local_official_text(pdf, repo_root=tmp_path)
    with pytest.raises(OfficialDisclosureParserError):
        read_local_official_text(binary, repo_root=tmp_path)


def test_local_text_reader_blocks_too_large_file(tmp_path):
    path = tmp_path / "too_large.txt"
    path.write_bytes(b"x" * (parser_module.MAX_LOCAL_TEXT_BYTES + 1))

    with pytest.raises(OfficialDisclosureParserError):
        read_local_official_text(path, repo_root=tmp_path)


def test_local_text_reader_blocks_secret_like_text(tmp_path):
    path = tmp_path / "annual.txt"
    path.write_text("Bearer abcdefghijklmnopqrstuvwxyz123456", encoding="utf-8")

    with pytest.raises(OfficialDisclosureSecretError):
        read_local_official_text(path, repo_root=tmp_path)


def test_source_document_sha256_computed_correctly(tmp_path):
    path = tmp_path / "annual.txt"
    raw = "年度报告\n主营业务：公司主要从事电网自动化业务。".encode("utf-8")
    path.write_bytes(raw)

    draft = read_local_official_text(path, repo_root=tmp_path)

    assert draft["sha256"] == hashlib.sha256(raw).hexdigest()
    assert draft["size_bytes"] == len(raw)
    assert draft["text_extraction_method"] == "plain_text"


def test_main_business_extractor_returns_candidate_for_clear_local_text():
    text = "第三节 管理层讨论与分析\n主营业务：公司主要从事电网自动化、工业控制和信息通信相关产品及服务。"

    candidate = extract_main_business_candidate(text, source_document_id="doc_001")

    assert candidate is not None
    assert candidate["field_path"] == "basic_info.main_business_official_text"
    assert "电网自动化" in candidate["value"]
    assert len(candidate["value"]) <= 500
    assert candidate["evidence_tier"] == "L1_official_disclosure"
    assert candidate["needs_human_review"] is True


def test_main_business_extractor_returns_none_for_missing_section():
    assert extract_main_business_candidate("这里没有明确业务章节。", source_document_id="doc_001") is None


def test_periodic_report_basics_extractor_conservative_behavior():
    clear = extract_periodic_report_basics(
        "国电南瑞2025年年度报告 披露日期：2026年04月30日",
        source_document_id="doc_001",
    )
    weak = extract_periodic_report_basics("普通公告正文", source_document_id="doc_001")

    assert clear["document_type"] == "annual_report"
    assert clear["report_period"] == "2025A"
    assert clear["disclosure_date"] == "2026-04-30"
    assert clear["needs_human_review"] is True
    assert weak["document_type"] == "other_official_disclosure"
    assert weak["extraction_confidence"] == "low"
    assert weak["caveats"]


def test_periodic_report_basics_does_not_use_disclosure_date_year_as_period():
    result = extract_periodic_report_basics(
        "年度报告 披露日期：2026年04月30日",
        source_document_id="doc_001",
    )

    assert result["document_type"] == "annual_report"
    assert result["report_period"] == ""
    assert result["disclosure_date"] == "2026-04-30"
    assert result["extraction_confidence"] == "low"
    assert "Report period was not confidently detected." in result["caveats"]


@pytest.mark.parametrize("text", ["2025年年度报告", "2025年度报告", "2025年年度报告摘要"])
def test_periodic_report_basics_extracts_explicit_annual_report_period(text):
    result = extract_periodic_report_basics(text, source_document_id="doc_001")

    assert result["document_type"] == "annual_report"
    assert result["report_period"] == "2025A"


def test_writer_writes_only_tmpdir(tmp_path):
    payload = _payload()
    target = tmp_path / "official_disclosure_facts.json"

    written = write_official_disclosure_facts(payload, target)

    assert written == target.resolve(strict=False)
    assert written.exists()
    assert json.loads(written.read_text(encoding="utf-8")) == payload
    assert not (Path(DEFAULT_OFFICIAL_DISCLOSURE_OUTPUT_DIR) / "official_disclosure_facts.json").exists()


def test_writer_blocks_path_traversal(tmp_path):
    with pytest.raises(OfficialDisclosurePathBoundaryError):
        write_official_disclosure_facts(_payload(), tmp_path / ".." / "escape.json")


def test_writer_secret_scan_blocks_secrets(tmp_path):
    payload = _payload(data_quality_caveats=["Bearer abcdefghijklmnopqrstuvwxyz123456"])

    with pytest.raises(OfficialDisclosureSecretError):
        write_official_disclosure_facts(payload, tmp_path / "official_disclosure_facts.json")


def test_reader_roundtrip(tmp_path):
    payload = _payload()
    target = write_official_disclosure_facts(payload, tmp_path / "official_disclosure_facts.json")

    assert read_official_disclosure_facts(target) == payload


def test_no_runtime_boundary_imports_or_calls():
    source = inspect.getsource(parser_module)
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
        "OCR",
        "old runner",
        "TUSHARE_TOKEN",
        "pytesseract",
        "easyocr",
        "pdfplumber",
        "PyPDF",
        "pypdf",
        "pdfminer",
    ]

    for marker in forbidden:
        assert marker not in source


def test_no_real_output_writes_for_test_suite():
    default_root = Path(DEFAULT_OFFICIAL_DISCLOSURE_OUTPUT_DIR)

    assert not (default_root / "official_disclosure_facts.json").exists()


def test_builder_does_not_mutate_inputs():
    docs = [_source_document()]
    facts = [_fact()]

    payload = build_official_disclosure_facts(code="600406", company_name="国电南瑞", source_documents=docs, extracted_facts=facts)
    docs[0]["title"] = "mutated"
    facts[0]["value"] = "mutated"

    assert payload["source_documents"][0]["title"] != "mutated"
    assert payload["extracted_facts"][0]["value"] != "mutated"


def test_reader_rejects_invalid_json_payload(tmp_path):
    payload = copy.deepcopy(_payload())
    payload["version"] = "bad"
    path = tmp_path / "official_disclosure_facts.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(OfficialDisclosureValidationError):
        read_official_disclosure_facts(path)
