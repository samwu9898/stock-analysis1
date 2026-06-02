# -*- coding: utf-8 -*-

from __future__ import annotations

import copy
import hashlib

import pytest

from src.fundamental_skill.data_verification.official_artifact_cache_acquisition import (
    ANCHOR_MAP_SCHEMA_VERSION,
    ANCHOR_STATUS_MATCHED,
    ARTIFACT_CACHE_SCHEMA_VERSION,
    ARTIFACT_STATUS_BLOCKED,
    ARTIFACT_STATUS_CACHED,
    ARTIFACT_STATUS_SKIPPED,
    DOWNLOAD_STATUS_BLOCKED,
    DOWNLOAD_STATUS_SUCCESS,
    MAX_ARTIFACT_BYTES,
    PENDING_OFFICIAL_VERIFICATION_STATUS,
    PROVIDER_NAME,
    REASON_ALLOW_NETWORK_FALSE,
    REASON_CACHE_DIR_FORBIDDEN,
    REASON_CACHE_DIR_MISSING,
    REASON_CACHE_DIR_NOT_DIRECTORY,
    REASON_CONTENT_TYPE_NOT_ALLOWED,
    REASON_FINAL_DOMAIN_NOT_ALLOWLISTED,
    REASON_NO_MATCHED_ANCHORS,
    REASON_PDF_MAGIC_MISMATCH,
    REASON_SIZE_EXCEEDS_LIMIT,
    build_official_artifact_cache_from_anchor_map,
    validate_official_disclosure_artifact_cache,
)


PDF_BYTES = b"%PDF-1.7\nfake official bytes\n%%EOF"


class FakeOfficialHttpClient:
    def __init__(self, *responses):
        self._responses = list(responses)
        self.calls = []

    def __call__(self, request):
        self.calls.append(copy.deepcopy(request))
        if len(self._responses) == 1:
            return self._responses[0]
        return self._responses.pop(0)


class FakeUrlopenResponse:
    def __init__(self, *, final_url, body=PDF_BYTES, content_type="application/pdf", fail_on_read=False):
        self._final_url = final_url
        self._body = body
        self._fail_on_read = fail_on_read
        self.headers = {"Content-Type": content_type}
        self.status = 200
        self.read_called = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def geturl(self):
        return self._final_url

    def read(self, _size):
        self.read_called = True
        if self._fail_on_read:
            raise AssertionError("body must not be read for non-allowlist final host")
        return self._body


def _response(**overrides):
    response = {
        "status_code": 200,
        "final_url": "https://static.cninfo.com.cn/finalpage/2026-04-30/report.pdf",
        "content_type": "application/pdf",
        "body": PDF_BYTES,
    }
    response.update(overrides)
    return response


def _anchor_map(*items, **overrides):
    payload = {
        "schema_version": ANCHOR_MAP_SCHEMA_VERSION,
        "provider": PROVIDER_NAME,
        "ts_code": "600406.SH",
        "stock_code": "600406",
        "company_name_hint": "Guodian NARI",
        "anchor_items": list(items) if items else [_anchor_item()],
        "unmatched_items": [],
        "blocked_reasons": [],
        "caveats": [],
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }
    payload.update(overrides)
    return payload


def _anchor_item(**overrides):
    item = {
        "schema_version": "provider_metric_official_disclosure_anchor_item.v1",
        "provider": PROVIDER_NAME,
        "ts_code": "600406.SH",
        "stock_code": "600406",
        "company_name_hint": "Guodian NARI",
        "period": "20260331",
        "period_label": "2026Q1",
        "metric_key": "revenue",
        "metric_value": 1000,
        "value_status": "present",
        "source_table": "income",
        "source_field": "revenue",
        "provider_native_unit": "provider_native_amount_unverified",
        "official_verification_status": PENDING_OFFICIAL_VERIFICATION_STATUS,
        "official_anchor_status": ANCHOR_STATUS_MATCHED,
        "official_anchor_required": True,
        "official_disclosure_anchor": _official_anchor(),
        "not_official_verified": True,
        "not_for_trading_advice": True,
        "caveats": ["provider_candidate_requires_official_anchor"],
    }
    item.update(overrides)
    return item


def _official_anchor(**overrides):
    anchor = {
        "source_title": "Guodian NARI 2026 Q1 Report",
        "source_url": "https://static.cninfo.com.cn/finalpage/2026-04-30/report.pdf",
        "source_domain": "static.cninfo.com.cn",
        "disclosure_date": "2026-04-30",
        "stock_code": "600406",
        "company_name_hint": "Guodian NARI",
        "period_key": "2026Q1",
        "period_end_date": "20260331",
        "announcement_type": "quarterly_report",
        "source_type": "cninfo_official_pdf",
        "anchor_evidence_status": "official_anchor_candidate",
        "not_for_trading_advice": True,
    }
    anchor.update(overrides)
    return anchor


def _build(tmp_path, anchor_map=None, response=None, allow_network=True):
    client = FakeOfficialHttpClient(response or _response())
    result = build_official_artifact_cache_from_anchor_map(
        anchor_map or _anchor_map(),
        cache_dir=tmp_path,
        official_http_client=client,
        allow_network=allow_network,
    )
    return result, client


def test_allow_network_false_blocks_download(tmp_path):
    result, client = _build(tmp_path, allow_network=False)

    item = result["artifact_items"][0]
    assert client.calls == []
    assert item["artifact_status"] == ARTIFACT_STATUS_BLOCKED
    assert item["download_status"] == DOWNLOAD_STATUS_BLOCKED
    assert REASON_ALLOW_NETWORK_FALSE in item["caveats"]
    assert list(tmp_path.glob("*.pdf")) == []


def test_valid_matched_cninfo_anchor_downloads_fake_pdf_bytes_to_cache(tmp_path):
    result, _client = _build(tmp_path)
    item = result["artifact_items"][0]

    assert result["schema_version"] == ARTIFACT_CACHE_SCHEMA_VERSION
    assert item["artifact_status"] == ARTIFACT_STATUS_CACHED
    assert item["download_status"] == DOWNLOAD_STATUS_SUCCESS
    assert item["sha256"] == hashlib.sha256(PDF_BYTES).hexdigest()
    assert item["file_size_bytes"] == len(PDF_BYTES)
    assert item["cache_path"].endswith(".pdf")
    assert item["source_lineage"]["source_anchor_status"] == ANCHOR_STATUS_MATCHED
    assert item["source_lineage"]["anchor_item_metric_keys"] == ["revenue"]
    assert item["not_official_verified"] is True
    assert item["not_for_trading_advice"] is True
    validate_official_disclosure_artifact_cache(result)


def test_cache_path_exists_without_promoting_anchor_to_verified(tmp_path):
    result, _client = _build(tmp_path)
    item = result["artifact_items"][0]

    assert item["cache_path"]
    assert item["cache_status"] == "stored"
    assert item["anchor_evidence_status"] == "official_anchor_candidate"
    assert "official_verified" not in repr(result).replace("not_official_verified", "")


def test_unmatched_anchor_is_skipped(tmp_path):
    unmatched = _anchor_item(
        official_anchor_status="missing_anchor",
        official_disclosure_anchor=None,
        caveats=["no_matching_official_anchor_candidate"],
    )
    result, client = _build(tmp_path, anchor_map=_anchor_map(unmatched))

    assert client.calls == []
    assert result["artifact_items"] == []
    assert result["skipped_items"][0]["artifact_status"] == ARTIFACT_STATUS_SKIPPED
    assert REASON_NO_MATCHED_ANCHORS in result["blocked_reasons"]


def test_no_matched_anchors_blocks_result(tmp_path):
    result, _client = _build(
        tmp_path,
        anchor_map=_anchor_map(
            _anchor_item(official_anchor_status="ambiguous_anchor", official_disclosure_anchor=None)
        ),
    )

    assert result["artifact_items"] == []
    assert REASON_NO_MATCHED_ANCHORS in result["blocked_reasons"]


def test_static_cninfo_source_url_is_allowed(tmp_path):
    result, _client = _build(
        tmp_path,
        anchor_map=_anchor_map(
            _anchor_item(
                official_disclosure_anchor=_official_anchor(
                    source_url="https://static.cninfo.com.cn/finalpage/2026-04-30/static.pdf",
                    source_domain="static.cninfo.com.cn",
                )
            )
        ),
    )

    assert result["artifact_items"][0]["source_domain"] == "static.cninfo.com.cn"
    assert result["artifact_items"][0]["artifact_status"] == ARTIFACT_STATUS_CACHED


def test_allowlisted_final_host_is_accepted(tmp_path):
    result, _client = _build(
        tmp_path,
        response=_response(final_url="https://www.sse.com.cn/disclosure/report.pdf"),
    )

    assert result["artifact_items"][0]["final_domain"] == "www.sse.com.cn"
    assert result["artifact_items"][0]["artifact_status"] == ARTIFACT_STATUS_CACHED


def test_non_allowlisted_final_host_is_rejected(tmp_path):
    result, _client = _build(
        tmp_path,
        response=_response(final_url="https://example.com/report.pdf"),
    )

    item = result["artifact_items"][0]
    assert item["artifact_status"] == ARTIFACT_STATUS_BLOCKED
    assert REASON_FINAL_DOMAIN_NOT_ALLOWLISTED in item["caveats"]


def test_default_client_redirect_final_host_non_allowlist_blocks_before_reading_body(
    tmp_path,
    monkeypatch,
    capsys,
):
    fake_response = FakeUrlopenResponse(
        final_url="https://evil.example.com/report.pdf?secret=ShouldNotEcho",
        fail_on_read=True,
    )

    def fake_urlopen(_request, timeout):
        assert timeout
        return fake_response

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "src.fundamental_skill.data_verification.official_artifact_cache_acquisition.urllib.request.urlopen",
        fake_urlopen,
    )

    result = build_official_artifact_cache_from_anchor_map(
        _anchor_map(),
        cache_dir=tmp_path / "cache",
        allow_network=True,
    )
    captured = capsys.readouterr()
    item = result["artifact_items"][0]

    assert item["artifact_status"] == ARTIFACT_STATUS_BLOCKED
    assert REASON_FINAL_DOMAIN_NOT_ALLOWLISTED in item["caveats"]
    assert fake_response.read_called is False
    assert "evil.example.com" not in repr(result)
    assert "ShouldNotEcho" not in repr(result)
    assert captured.out == ""
    assert captured.err == ""
    assert not (tmp_path / "output").exists()
    assert not (tmp_path / "fixtures").exists()
    assert not (tmp_path / "accepted_manifest.json").exists()


def test_default_client_allowlist_final_host_succeeds(tmp_path, monkeypatch):
    fake_response = FakeUrlopenResponse(
        final_url="https://static.cninfo.com.cn/finalpage/2026-04-30/report.pdf",
        body=PDF_BYTES,
        content_type="application/pdf",
    )

    def fake_urlopen(_request, timeout):
        assert timeout
        return fake_response

    monkeypatch.setattr(
        "src.fundamental_skill.data_verification.official_artifact_cache_acquisition.urllib.request.urlopen",
        fake_urlopen,
    )

    result = build_official_artifact_cache_from_anchor_map(
        _anchor_map(),
        cache_dir=tmp_path,
        allow_network=True,
    )
    item = result["artifact_items"][0]

    assert fake_response.read_called is True
    assert item["artifact_status"] == ARTIFACT_STATUS_CACHED
    assert item["sha256"] == hashlib.sha256(PDF_BYTES).hexdigest()
    assert item["file_size_bytes"] == len(PDF_BYTES)


@pytest.mark.parametrize(
    "content_type",
    [
        "application/pdf",
        "application/pdf; charset=binary",
    ],
)
def test_application_pdf_content_type_is_accepted(tmp_path, content_type):
    result, _client = _build(tmp_path, response=_response(content_type=content_type))

    assert result["artifact_items"][0]["artifact_status"] == ARTIFACT_STATUS_CACHED


@pytest.mark.parametrize("content_type", ["application/octet-stream", "binary/octet-stream", ""])
def test_octet_or_empty_content_type_with_pdf_url_and_magic_is_accepted(tmp_path, content_type):
    result, _client = _build(tmp_path, response=_response(content_type=content_type))

    assert result["artifact_items"][0]["artifact_status"] == ARTIFACT_STATUS_CACHED


@pytest.mark.parametrize("content_type", ["text/html", "application/json", "application/zip", "image/png"])
def test_non_pdf_content_type_is_rejected(tmp_path, content_type):
    result, _client = _build(tmp_path, response=_response(content_type=content_type))

    item = result["artifact_items"][0]
    assert item["artifact_status"] == ARTIFACT_STATUS_BLOCKED
    assert REASON_CONTENT_TYPE_NOT_ALLOWED in item["caveats"]


def test_pdf_magic_mismatch_is_rejected(tmp_path):
    result, _client = _build(tmp_path, response=_response(body=b"<html>not a pdf</html>"))

    item = result["artifact_items"][0]
    assert item["artifact_status"] == ARTIFACT_STATUS_BLOCKED
    assert REASON_PDF_MAGIC_MISMATCH in item["caveats"]


def test_size_limit_exceeded_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "src.fundamental_skill.data_verification.official_artifact_cache_acquisition.MAX_ARTIFACT_BYTES",
        len(PDF_BYTES) - 1,
    )

    result, _client = _build(tmp_path)

    item = result["artifact_items"][0]
    assert item["artifact_status"] == ARTIFACT_STATUS_BLOCKED
    assert REASON_SIZE_EXCEEDS_LIMIT in item["caveats"]


def test_cache_dir_missing_is_rejected():
    result = build_official_artifact_cache_from_anchor_map(
        _anchor_map(),
        cache_dir=None,
        official_http_client=FakeOfficialHttpClient(_response()),
        allow_network=True,
    )

    assert result["artifact_items"] == []
    assert REASON_CACHE_DIR_MISSING in result["blocked_reasons"]


@pytest.mark.parametrize("dirname", ["output", "fixtures", ".local_experiments", "accepted_manifest"])
def test_forbidden_cache_dir_is_rejected(tmp_path, dirname):
    result = build_official_artifact_cache_from_anchor_map(
        _anchor_map(),
        cache_dir=tmp_path / dirname,
        official_http_client=FakeOfficialHttpClient(_response()),
        allow_network=True,
    )

    assert result["artifact_items"] == []
    assert REASON_CACHE_DIR_FORBIDDEN in result["blocked_reasons"]


def test_cache_dir_file_not_directory_is_rejected(tmp_path):
    cache_file = tmp_path / "cache-file"
    cache_file.write_text("not a directory", encoding="utf-8")

    result = build_official_artifact_cache_from_anchor_map(
        _anchor_map(),
        cache_dir=cache_file,
        official_http_client=FakeOfficialHttpClient(_response()),
        allow_network=True,
    )

    assert REASON_CACHE_DIR_NOT_DIRECTORY in result["blocked_reasons"]


def test_duplicate_same_source_url_is_reused_without_second_download(tmp_path):
    first = _anchor_item(metric_key="revenue")
    second = _anchor_item(metric_key="net_profit")
    result, client = _build(tmp_path, anchor_map=_anchor_map(first, second))

    assert len(client.calls) == 1
    assert len(result["artifact_items"]) == 2
    assert result["artifact_items"][1]["cache_status"] == "reused_source_url"
    assert result["artifact_items"][0]["cache_path"] == result["artifact_items"][1]["cache_path"]


def test_duplicate_same_sha256_is_reused(tmp_path):
    first = _anchor_item(metric_key="revenue")
    second = _anchor_item(
        metric_key="net_profit",
        official_disclosure_anchor=_official_anchor(
            source_url="https://static.cninfo.com.cn/finalpage/2026-04-30/alternate.pdf"
        ),
    )
    result, client = _build(
        tmp_path,
        anchor_map=_anchor_map(first, second),
        response=_response(),
    )

    assert len(client.calls) == 2
    assert result["artifact_items"][1]["cache_status"] == "reused_sha256"
    assert result["artifact_items"][0]["sha256"] == result["artifact_items"][1]["sha256"]


def test_input_anchor_map_is_not_mutated(tmp_path):
    anchor_map = _anchor_map()
    before = copy.deepcopy(anchor_map)

    _build(tmp_path, anchor_map=anchor_map)

    assert anchor_map == before


def test_no_output_fixture_or_manifest_write(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    cache_dir = tmp_path / "cache"

    result, _client = _build(cache_dir)

    assert result["artifact_items"][0]["artifact_status"] == ARTIFACT_STATUS_CACHED
    assert not (tmp_path / "output").exists()
    assert not (tmp_path / "fixtures").exists()
    assert not (tmp_path / "accepted_manifest.json").exists()
