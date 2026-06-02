# -*- coding: utf-8 -*-

from __future__ import annotations

import copy
import hashlib

import pytest

from src.fundamental_skill.data_verification import official_artifact_evidence_locator as locator
from src.fundamental_skill.data_verification.official_artifact_evidence_locator import (
    LOCATOR_CONFIDENCE_BLOCKED,
    LOCATOR_CONFIDENCE_HIGH,
    LOCATOR_CONFIDENCE_LOW,
    LOCATOR_CONFIDENCE_MEDIUM,
    REASON_CACHE_PATH_FORBIDDEN,
    REASON_CACHE_PATH_MISSING,
    REASON_CACHE_PATH_NOT_PDF,
    REASON_FILE_SIZE_BYTES_EXCEEDS_LIMIT,
    REASON_FILE_SIZE_BYTES_MISSING,
    REASON_FILE_SIZE_BYTES_MISMATCH,
    REASON_FILE_SIZE_BYTES_NON_POSITIVE,
    REASON_PDF_MAGIC_MISMATCH,
    REASON_PDF_TEXT_LAYER_UNAVAILABLE,
    REASON_SHA256_MISMATCH,
    build_official_artifact_evidence_locator,
    validate_official_artifact_evidence_locator,
)


PDF_BYTES = b"%PDF-1.7\nfake official pdf bytes\n%%EOF"


def _write_pdf(tmp_path, name="report.pdf", body=PDF_BYTES):
    path = tmp_path / name
    path.write_bytes(body)
    return path


def _artifact_cache(*items, skipped_items=None, **overrides):
    payload = {
        "schema_version": "official_disclosure_artifact_cache.v1",
        "provider": "Tushare",
        "ts_code": "600406.SH",
        "stock_code": "600406",
        "company_name_hint": "Guodian NARI",
        "artifact_items": list(items),
        "skipped_items": list(skipped_items or []),
        "blocked_reasons": [],
        "caveats": [],
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }
    payload.update(overrides)
    return payload


def _artifact_item(cache_path, body=PDF_BYTES, **overrides):
    source_url = "https://static.cninfo.com.cn/finalpage/2026-04-30/report.pdf"
    item = {
        "schema_version": "official_disclosure_artifact_cache_item.v1",
        "artifact_id": "artifact_600406_2026q1",
        "source_title": "Guodian NARI 2026 Q1 Report",
        "source_url": source_url,
        "source_domain": "static.cninfo.com.cn",
        "final_url": source_url,
        "final_domain": "static.cninfo.com.cn",
        "disclosure_date": "2026-04-30",
        "stock_code": "600406",
        "company_name_hint": "Guodian NARI",
        "period_key": "2026Q1",
        "period_end_date": "20260331",
        "announcement_type": "quarterly_report",
        "source_type": "cninfo_official_pdf",
        "anchor_evidence_status": "official_anchor_candidate",
        "artifact_status": "cached",
        "download_status": "success",
        "cache_path": str(cache_path) if cache_path is not None else None,
        "file_size_bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "content_type": "application/pdf",
        "source_lineage": {
            "schema_version": "official_artifact_source_lineage.v1",
            "source_anchor_status": "matched",
            "source_anchor_url": source_url,
            "source_anchor_domain": "static.cninfo.com.cn",
            "source_anchor_title": "Guodian NARI 2026 Q1 Report",
            "source_disclosure_date": "2026-04-30",
            "anchor_map_schema_version": "provider_metric_official_disclosure_anchor_map.v1",
            "anchor_item_metric_keys": [],
            "not_official_verified": True,
            "not_for_trading_advice": True,
        },
        "not_official_verified": True,
        "not_for_trading_advice": True,
        "caveats": [],
    }
    item.update(overrides)
    return item


def _fake_pages():
    return [
        {
            "page_number": 1,
            "text": "Guodian NARI 600406 2026Q1 2026年第一季度报告 公司简介 管理层讨论与分析",
        },
        {
            "page_number": 2,
            "text": "财务报表 2026年3月31日 主营业务 经营情况讨论与分析",
        },
    ]


def test_valid_artifact_cache_with_fake_pdf_text_layer_builds_locator_result(tmp_path, monkeypatch):
    pdf_path = _write_pdf(tmp_path)
    monkeypatch.setattr(locator, "extract_pdf_text_layer_pages", lambda _pdf_bytes: _fake_pages())

    result = build_official_artifact_evidence_locator(_artifact_cache(_artifact_item(pdf_path)))
    item = result["locator_items"][0]

    assert result["schema_version"] == "official_artifact_evidence_locator.v1"
    assert result["provider"] == "Tushare"
    assert item["text_layer_available"] is True
    assert item["locator_confidence"] == LOCATOR_CONFIDENCE_HIGH
    assert item["report_title_hits"]
    assert item["company_name_hits"]
    assert item["stock_code_hits"]
    assert item["report_period_hits"]
    assert item["section_heading_hits"]
    assert item["keyword_hits"]
    assert item["section_heading_hits"][0]["page_number"] == 1
    assert item["not_official_verified"] is True
    assert item["not_for_trading_advice"] is True
    validate_official_artifact_evidence_locator(result)


def test_only_cached_artifact_items_are_processed(tmp_path, monkeypatch):
    pdf_path = _write_pdf(tmp_path)
    calls = []

    def fake_extract(pdf_bytes):
        calls.append(pdf_bytes)
        return _fake_pages()

    blocked_item = _artifact_item(
        None,
        artifact_id="blocked_artifact",
        artifact_status="blocked",
        download_status="blocked",
        file_size_bytes=None,
        sha256=None,
        caveats=["source_blocked"],
    )
    monkeypatch.setattr(locator, "extract_pdf_text_layer_pages", fake_extract)

    result = build_official_artifact_evidence_locator(
        _artifact_cache(_artifact_item(pdf_path), blocked_item)
    )

    assert len(result["locator_items"]) == 1
    assert len(result["skipped_items"]) == 1
    assert result["skipped_items"][0]["artifact_id"] == "blocked_artifact"
    assert calls == [PDF_BYTES]


def test_cache_level_skipped_items_are_carried_to_locator_skipped_items(tmp_path):
    skipped = {
        "not_official_verified": True,
        "not_for_trading_advice": True,
        "artifact_status": "skipped",
        "caveats": ["anchor_status_not_matched"],
    }
    result = build_official_artifact_evidence_locator(
        _artifact_cache(skipped_items=[skipped])
    )

    assert result["locator_items"] == []
    assert result["skipped_items"][0]["locator_confidence"] == LOCATOR_CONFIDENCE_BLOCKED


def test_sha256_mismatch_blocks_before_text_extraction(tmp_path, monkeypatch):
    pdf_path = _write_pdf(tmp_path)

    def fail_extract(_pdf_bytes):
        raise AssertionError("extractor must not run after sha mismatch")

    monkeypatch.setattr(locator, "extract_pdf_text_layer_pages", fail_extract)

    result = build_official_artifact_evidence_locator(
        _artifact_cache(_artifact_item(pdf_path, sha256="0" * 64))
    )
    item = result["locator_items"][0]

    assert item["locator_confidence"] == LOCATOR_CONFIDENCE_BLOCKED
    assert REASON_SHA256_MISMATCH in item["caveats"]


def test_file_size_mismatch_blocks(tmp_path, monkeypatch):
    pdf_path = _write_pdf(tmp_path)

    def fail_read_bytes(_path):
        raise AssertionError("read_bytes must not run after stat size mismatch")

    monkeypatch.setattr(locator.Path, "read_bytes", fail_read_bytes)
    monkeypatch.setattr(locator, "extract_pdf_text_layer_pages", lambda _pdf_bytes: _fake_pages())

    result = build_official_artifact_evidence_locator(
        _artifact_cache(_artifact_item(pdf_path, file_size_bytes=len(PDF_BYTES) + 1))
    )

    assert REASON_FILE_SIZE_BYTES_MISMATCH in result["locator_items"][0]["caveats"]
    assert result["locator_items"][0]["locator_confidence"] == LOCATOR_CONFIDENCE_BLOCKED


def test_missing_file_size_bytes_blocks_before_read(tmp_path, monkeypatch):
    pdf_path = _write_pdf(tmp_path)

    def fail_read_bytes(_path):
        raise AssertionError("read_bytes must not run when file_size_bytes is missing")

    monkeypatch.setattr(locator.Path, "read_bytes", fail_read_bytes)

    result = build_official_artifact_evidence_locator(
        _artifact_cache(_artifact_item(pdf_path, file_size_bytes=None))
    )

    assert REASON_FILE_SIZE_BYTES_MISSING in result["locator_items"][0]["caveats"]
    assert result["locator_items"][0]["locator_confidence"] == LOCATOR_CONFIDENCE_BLOCKED


def test_zero_size_file_blocks_before_read(tmp_path, monkeypatch):
    pdf_path = _write_pdf(tmp_path, body=b"")

    def fail_read_bytes(_path):
        raise AssertionError("read_bytes must not run for zero-size files")

    monkeypatch.setattr(locator.Path, "read_bytes", fail_read_bytes)

    result = build_official_artifact_evidence_locator(
        _artifact_cache(_artifact_item(pdf_path, body=b""))
    )

    assert REASON_FILE_SIZE_BYTES_NON_POSITIVE in result["locator_items"][0]["caveats"]
    assert result["locator_items"][0]["locator_confidence"] == LOCATOR_CONFIDENCE_BLOCKED


def test_oversized_stat_file_blocks_before_read(tmp_path, monkeypatch):
    pdf_path = _write_pdf(tmp_path)

    def fail_read_bytes(_path):
        raise AssertionError("read_bytes must not run for oversized files")

    monkeypatch.setattr(locator.Path, "read_bytes", fail_read_bytes)
    monkeypatch.setattr(locator, "MAX_ARTIFACT_BYTES", len(PDF_BYTES) - 1)

    result = build_official_artifact_evidence_locator(_artifact_cache(_artifact_item(pdf_path)))

    assert REASON_FILE_SIZE_BYTES_EXCEEDS_LIMIT in result["locator_items"][0]["caveats"]
    assert result["locator_items"][0]["locator_confidence"] == LOCATOR_CONFIDENCE_BLOCKED


def test_missing_cache_path_blocks(tmp_path):
    result = build_official_artifact_evidence_locator(
        _artifact_cache(_artifact_item(None))
    )

    assert REASON_CACHE_PATH_MISSING in result["locator_items"][0]["caveats"]
    assert result["locator_items"][0]["cache_filename"] == ""


@pytest.mark.parametrize("dirname", ["output", "fixtures", ".local_experiments", "accepted_manifest"])
def test_forbidden_cache_path_blocks_without_reading(tmp_path, dirname, monkeypatch):
    forbidden_path = tmp_path / dirname / "report.pdf"

    def fail_extract(_pdf_bytes):
        raise AssertionError("extractor must not run for forbidden cache paths")

    monkeypatch.setattr(locator, "extract_pdf_text_layer_pages", fail_extract)

    result = build_official_artifact_evidence_locator(
        _artifact_cache(_artifact_item(forbidden_path))
    )

    assert result["locator_items"][0]["locator_confidence"] == LOCATOR_CONFIDENCE_BLOCKED
    assert REASON_CACHE_PATH_FORBIDDEN in result["locator_items"][0]["caveats"]


def test_non_pdf_cache_path_blocks(tmp_path):
    non_pdf_path = tmp_path / "report.txt"

    result = build_official_artifact_evidence_locator(
        _artifact_cache(_artifact_item(non_pdf_path))
    )

    assert REASON_CACHE_PATH_NOT_PDF in result["locator_items"][0]["caveats"]


def test_pdf_magic_mismatch_blocks_before_extraction(tmp_path, monkeypatch):
    body = b"not a pdf"
    bad_path = _write_pdf(tmp_path, body=body)

    def fail_extract(_pdf_bytes):
        raise AssertionError("extractor must not run after magic mismatch")

    monkeypatch.setattr(locator, "extract_pdf_text_layer_pages", fail_extract)

    result = build_official_artifact_evidence_locator(
        _artifact_cache(_artifact_item(bad_path, body=body))
    )

    assert REASON_PDF_MAGIC_MISMATCH in result["locator_items"][0]["caveats"]
    assert result["locator_items"][0]["locator_confidence"] == LOCATOR_CONFIDENCE_BLOCKED


def test_text_layer_unavailable_blocks_with_text_layer_false(tmp_path, monkeypatch):
    pdf_path = _write_pdf(tmp_path)

    def no_text_layer(_pdf_bytes):
        raise locator.OfficialArtifactEvidenceLocatorError(REASON_PDF_TEXT_LAYER_UNAVAILABLE)

    monkeypatch.setattr(locator, "extract_pdf_text_layer_pages", no_text_layer)

    result = build_official_artifact_evidence_locator(_artifact_cache(_artifact_item(pdf_path)))
    item = result["locator_items"][0]

    assert item["text_layer_available"] is False
    assert item["locator_confidence"] == LOCATOR_CONFIDENCE_BLOCKED
    assert REASON_PDF_TEXT_LAYER_UNAVAILABLE in item["caveats"]


def test_section_heading_hits_include_required_headings(tmp_path, monkeypatch):
    pdf_path = _write_pdf(tmp_path)
    monkeypatch.setattr(locator, "extract_pdf_text_layer_pages", lambda _pdf_bytes: _fake_pages())

    result = build_official_artifact_evidence_locator(_artifact_cache(_artifact_item(pdf_path)))
    headings = {hit["heading_text"] for hit in result["locator_items"][0]["section_heading_hits"]}

    assert {"财务报表", "管理层讨论与分析", "公司简介"} <= headings


def test_configured_safe_keywords_create_keyword_hits(tmp_path, monkeypatch):
    pdf_path = _write_pdf(tmp_path)
    monkeypatch.setattr(
        locator,
        "extract_pdf_text_layer_pages",
        lambda _pdf_bytes: [{"page_number": 1, "text": "自定义安全章节 其他文字"}],
    )

    result = build_official_artifact_evidence_locator(
        _artifact_cache(_artifact_item(pdf_path)),
        locator_config={"keywords": ["自定义安全章节"], "section_headings": []},
    )

    assert result["locator_items"][0]["keyword_hits"][0]["keyword"] == "自定义安全章节"
    assert result["locator_items"][0]["locator_confidence"] == LOCATOR_CONFIDENCE_LOW


def test_allowed_section_headings_remain_allowed(tmp_path, monkeypatch):
    pdf_path = _write_pdf(tmp_path)
    monkeypatch.setattr(
        locator,
        "extract_pdf_text_layer_pages",
        lambda _pdf_bytes: [{"page_number": 1, "text": "财务报表 合并利润表 合并现金流量表"}],
    )

    result = build_official_artifact_evidence_locator(
        _artifact_cache(_artifact_item(pdf_path)),
        locator_config={
            "keywords": ["财务报表"],
            "section_headings": [
                ("financial_statements", "财务报表"),
                ("consolidated_income_statement", "合并利润表"),
                ("consolidated_cashflow_statement", "合并现金流量表"),
            ],
        },
    )
    headings = {hit["heading_text"] for hit in result["locator_items"][0]["section_heading_hits"]}

    assert result["blocked_reasons"] == []
    assert {"财务报表", "合并利润表", "合并现金流量表"} <= headings


def test_snippets_are_bounded_and_full_page_text_is_not_returned(tmp_path, monkeypatch):
    pdf_path = _write_pdf(tmp_path)
    long_text = "x" * 500 + "Guodian NARI" + "y" * 500
    monkeypatch.setattr(
        locator,
        "extract_pdf_text_layer_pages",
        lambda _pdf_bytes: [{"page_number": 1, "text": long_text}],
    )

    result = build_official_artifact_evidence_locator(_artifact_cache(_artifact_item(pdf_path)))
    hit = result["locator_items"][0]["company_name_hits"][0]

    assert hit["snippet_char_count"] <= 200
    assert long_text not in repr(result)


def test_page_numbers_are_one_based(tmp_path, monkeypatch):
    pdf_path = _write_pdf(tmp_path)
    monkeypatch.setattr(
        locator,
        "extract_pdf_text_layer_pages",
        lambda _pdf_bytes: [{"page_number": 0, "text": "Guodian NARI"}],
    )

    result = build_official_artifact_evidence_locator(_artifact_cache(_artifact_item(pdf_path)))

    assert result["locator_items"][0]["company_name_hits"][0]["page_number"] == 1


def test_locator_confidence_medium_for_partial_identity_hits(tmp_path, monkeypatch):
    pdf_path = _write_pdf(tmp_path)
    monkeypatch.setattr(
        locator,
        "extract_pdf_text_layer_pages",
        lambda _pdf_bytes: [{"page_number": 1, "text": "Guodian NARI 600406"}],
    )

    result = build_official_artifact_evidence_locator(_artifact_cache(_artifact_item(pdf_path)))

    assert result["locator_items"][0]["locator_confidence"] == LOCATOR_CONFIDENCE_MEDIUM


def test_result_uses_cache_filename_without_full_cache_path(tmp_path, monkeypatch):
    pdf_path = _write_pdf(tmp_path, name="safe_report.pdf")
    monkeypatch.setattr(locator, "extract_pdf_text_layer_pages", lambda _pdf_bytes: _fake_pages())

    result = build_official_artifact_evidence_locator(_artifact_cache(_artifact_item(pdf_path)))

    assert result["locator_items"][0]["cache_filename"] == "safe_report.pdf"
    assert str(pdf_path) not in repr(result)


def test_input_artifact_cache_is_not_mutated(tmp_path, monkeypatch):
    pdf_path = _write_pdf(tmp_path)
    artifact_cache = _artifact_cache(_artifact_item(pdf_path))
    before = copy.deepcopy(artifact_cache)
    monkeypatch.setattr(locator, "extract_pdf_text_layer_pages", lambda _pdf_bytes: _fake_pages())

    build_official_artifact_evidence_locator(artifact_cache)

    assert artifact_cache == before


def test_no_output_fixture_or_manifest_write(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    cache_dir = tmp_path / "safe_cache"
    cache_dir.mkdir()
    pdf_path = _write_pdf(cache_dir)
    monkeypatch.setattr(locator, "extract_pdf_text_layer_pages", lambda _pdf_bytes: _fake_pages())

    result = build_official_artifact_evidence_locator(_artifact_cache(_artifact_item(pdf_path)))

    assert result["locator_items"][0]["locator_confidence"] == LOCATOR_CONFIDENCE_HIGH
    assert not (tmp_path / "output").exists()
    assert not (tmp_path / "fixtures").exists()
    assert not (tmp_path / "accepted_manifest.json").exists()
