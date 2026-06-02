# -*- coding: utf-8 -*-

from __future__ import annotations

import copy
import json
import urllib.request

from src.fundamental_skill.data_verification.official_disclosure_request import (
    normalize_official_disclosure_request,
)
from src.fundamental_skill.data_verification.real_official_metadata_anchor_handoff import (
    MAX_METADATA_RESPONSE_BYTES,
    REASON_ADAPTER_HANDOFF_REJECTED,
    REASON_ALLOW_NETWORK_FALSE,
    REASON_ANCHOR_MAP_NOT_FULLY_MATCHED,
    REASON_EMPTY_RESPONSE,
    REASON_FORBIDDEN_SOURCE_DOMAIN,
    REASON_MALFORMED_RESPONSE,
    REASON_MISSING_METADATA,
    REASON_NON_ALLOWLIST_SOURCE_URL,
    REASON_TRANSPORT_ERROR,
    build_anchor_map_from_real_metadata,
    build_official_metadata_candidates_from_records,
    build_real_official_metadata_anchor_handoff,
    fetch_cninfo_metadata_for_request,
)
from src.fundamental_skill.data_verification.security_identity import (
    normalize_security_identity,
)


def _request(query_period="2025FY", **overrides):
    payload = {
        "security_identity": normalize_security_identity(
            {
                "stock_code": "600406",
                "company_name": "Guodian NARI",
                "not_for_trading_advice": True,
            }
        ),
        "query_period": query_period,
        "not_for_trading_advice": True,
    }
    payload.update(overrides)
    return normalize_official_disclosure_request(payload)


def _provider_queue(*items, **overrides):
    queue = {
        "schema_version": "provider_candidate_metric_verification_queue.v1",
        "provider": "Tushare",
        "ts_code": "600406.SH",
        "stock_code": "600406",
        "company_name_hint": "Guodian NARI",
        "periods": ["20251231"],
        "verification_items": list(items) if items else [_provider_item()],
        "blocked_reasons": [],
        "caveats": [],
        "not_official_verified": True,
        "not_for_trading_advice": True,
    }
    queue.update(overrides)
    return queue


def _provider_item(**overrides):
    item = {
        "schema_version": "provider_candidate_metric_verification_item.v1",
        "provider": "Tushare",
        "ts_code": "600406.SH",
        "stock_code": "600406",
        "company_name_hint": "Guodian NARI",
        "period": "20251231",
        "period_label": "2025FY",
        "metric_key": "revenue",
        "metric_value": 1000,
        "value_status": "present",
        "source_table": "income",
        "source_field": "revenue",
        "provider_native_unit": "provider_native_amount_unverified",
        "official_verification_status": "pending_official_verification",
        "not_official_verified": True,
        "not_for_trading_advice": True,
        "caveats": ["provider_candidate_requires_official_verification"],
    }
    item.update(overrides)
    return item


def _annual_announcement(**overrides):
    announcement = {
        "secCode": "600406",
        "secName": "Guodian NARI",
        "announcementTitle": "Guodian NARI 2025 Annual Report",
        "adjunctUrl": "finalpage/2026-04-30/annual.pdf",
        "announcementTime": "2026-04-30",
    }
    announcement.update(overrides)
    return announcement


def _quarterly_announcement(**overrides):
    announcement = {
        "secCode": "600406",
        "secName": "Guodian NARI",
        "announcementTitle": "Guodian NARI 2026 Q1 Report",
        "adjunctUrl": "finalpage/2026-04-29/q1.pdf",
        "announcementTime": "2026-04-29",
    }
    announcement.update(overrides)
    return announcement


def _fake_client(response):
    calls = []

    def client(metadata_request):
        calls.append(copy.deepcopy(metadata_request))
        return copy.deepcopy(response)

    client.calls = calls
    return client


class _UrlopenResponse:
    def __init__(self, *, final_url, payload=None, body=None, content_type="application/json"):
        self._final_url = final_url
        self.headers = {"Content-Type": content_type}
        if body is not None:
            self._body = body
        else:
            self._body = json.dumps(payload).encode("utf-8")

    def geturl(self):
        return self._final_url

    def read(self, _size=-1):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc, _tb):
        return False


def _first_anchor_item(result):
    return result["anchor_map_result"]["anchor_items"][0]


def test_allow_network_false_blocks_before_client_use():
    client = _fake_client({"announcements": [_annual_announcement()]})

    result = build_real_official_metadata_anchor_handoff(
        _request(),
        _provider_queue(),
        official_http_client=client,
        allow_network=False,
    )

    assert REASON_ALLOW_NETWORK_FALSE in result["blocked_reasons"]
    assert result["metadata_records"] == []
    assert result["discovery_adapter_result"] == {}
    assert client.calls == []


def test_fake_cninfo_annual_response_handoffs_to_adapter_and_anchor_map():
    client = _fake_client({"announcements": [_annual_announcement()]})

    result = build_real_official_metadata_anchor_handoff(
        _request("2025FY"),
        _provider_queue(),
        official_http_client=client,
        allow_network=True,
    )

    assert result["blocked_reasons"] == []
    assert result["metadata_records"][0]["announcement_type"] == "annual_report"
    assert result["metadata_records"][0]["period_key"] == "2025FY"
    assert result["metadata_records"][0]["source_domain"] == "static.cninfo.com.cn"
    assert result["discovery_adapter_result"]["discovery_candidates"]
    assert _first_anchor_item(result)["official_anchor_status"] == "matched"
    assert result["live_smoke_summary"]["adapter_status"] == "candidate_found"
    assert result["live_smoke_summary"]["anchor_map_status"] == "matched"
    assert client.calls[0]["host"] == "www.cninfo.com.cn"


def test_cninfo_annual_summary_notice_is_not_used_as_report_metadata():
    client = _fake_client(
        {
            "announcements": [
                _annual_announcement(
                    announcementTitle="Guodian NARI 2025 Annual Report Summary",
                    adjunctUrl="finalpage/2026-04-30/annual-summary.pdf",
                ),
                _annual_announcement(adjunctUrl="finalpage/2026-04-30/annual-full.pdf"),
            ]
        }
    )

    result = build_real_official_metadata_anchor_handoff(
        _request("2025FY"),
        _provider_queue(),
        official_http_client=client,
        allow_network=True,
    )

    assert len(result["metadata_records"]) == 1
    assert result["metadata_records"][0]["source_url"].endswith("annual-full.pdf")
    assert _first_anchor_item(result)["official_anchor_status"] == "matched"


def test_fake_cninfo_quarterly_response_handoffs_to_adapter_and_anchor_map():
    queue = _provider_queue(
        _provider_item(period="20260331", period_label="2026Q1", metric_value=260),
        periods=["20260331"],
    )
    client = _fake_client({"announcements": [_quarterly_announcement()]})

    result = build_real_official_metadata_anchor_handoff(
        _request("2026Q1"),
        queue,
        official_http_client=client,
        allow_network=True,
    )

    assert result["blocked_reasons"] == []
    assert result["metadata_records"][0]["announcement_type"] == "quarterly_report"
    assert result["metadata_records"][0]["period_key"] == "2026Q1"
    assert _first_anchor_item(result)["official_anchor_status"] == "matched"


def test_2025_fy_target_maps_to_annual_report():
    discovery = fetch_cninfo_metadata_for_request(
        _request("2025FY"),
        official_http_client=_fake_client({"announcements": [_annual_announcement()]}),
        allow_network=True,
    )

    assert discovery["metadata_request"]["form_data"]["category"] == "category_ndbg_szsh"
    assert discovery["metadata_records"][0]["announcement_type"] == "annual_report"


def test_2026_q1_target_maps_to_quarterly_report():
    discovery = fetch_cninfo_metadata_for_request(
        _request("2026Q1"),
        official_http_client=_fake_client({"announcements": [_quarterly_announcement()]}),
        allow_network=True,
    )

    assert discovery["metadata_request"]["form_data"]["category"] == "category_yjdbg_szsh"
    assert discovery["metadata_records"][0]["announcement_type"] == "quarterly_report"


def test_malformed_response_blocks_structurally():
    result = build_real_official_metadata_anchor_handoff(
        _request(),
        _provider_queue(),
        official_http_client=_fake_client({"unexpected": []}),
        allow_network=True,
    )

    assert REASON_MALFORMED_RESPONSE in result["blocked_reasons"]
    assert result["metadata_records"] == []


def test_empty_response_blocks_and_reports_missing_metadata():
    result = build_real_official_metadata_anchor_handoff(
        _request(),
        _provider_queue(),
        official_http_client=_fake_client({"announcements": []}),
        allow_network=True,
    )

    assert REASON_EMPTY_RESPONSE in result["blocked_reasons"]
    assert REASON_MISSING_METADATA in result["blocked_reasons"]


def test_no_matching_announcement_returns_missing_metadata_and_missing_anchor():
    result = build_real_official_metadata_anchor_handoff(
        _request(),
        _provider_queue(),
        official_http_client=_fake_client(
            {"announcements": [_annual_announcement(announcementTitle="Guodian NARI 2024 Annual Report")]}
        ),
        allow_network=True,
    )

    assert REASON_MISSING_METADATA in result["blocked_reasons"]
    assert REASON_ANCHOR_MAP_NOT_FULLY_MATCHED in result["blocked_reasons"]
    assert _first_anchor_item(result)["official_anchor_status"] == "missing_anchor"


def test_non_allowlist_source_url_is_rejected():
    result = build_real_official_metadata_anchor_handoff(
        _request(),
        _provider_queue(),
        official_http_client=_fake_client(
            {
                "announcements": [
                    _annual_announcement(adjunctUrl="https://finance.sina.com.cn/report.pdf")
                ]
            }
        ),
        allow_network=True,
    )

    assert REASON_NON_ALLOWLIST_SOURCE_URL in result["blocked_reasons"]
    assert REASON_FORBIDDEN_SOURCE_DOMAIN in result["blocked_reasons"]
    assert result["metadata_records"] == []


def test_provider_mirror_or_search_source_is_rejected():
    result = build_real_official_metadata_anchor_handoff(
        _request(),
        _provider_queue(),
        official_http_client=_fake_client(
            {"announcements": [_annual_announcement(adjunctUrl="https://www.baidu.com/result.pdf")]}
        ),
        allow_network=True,
    )

    assert REASON_NON_ALLOWLIST_SOURCE_URL in result["blocked_reasons"]
    assert REASON_FORBIDDEN_SOURCE_DOMAIN in result["blocked_reasons"]
    assert result["metadata_records"] == []


def test_pdf_url_is_preserved_as_metadata_but_no_artifact_paths_are_written(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    pdf_url = "https://static.cninfo.com.cn/finalpage/2026-04-30/annual.PDF"
    client = _fake_client({"announcements": [_annual_announcement(adjunctUrl=pdf_url)]})

    result = build_real_official_metadata_anchor_handoff(
        _request(),
        _provider_queue(),
        official_http_client=client,
        allow_network=True,
    )

    assert result["metadata_records"][0]["source_url"] == pdf_url
    assert "pdf_url_preserved_metadata_only" in result["metadata_records"][0]["caveats"]
    assert len(client.calls) == 1
    assert not (tmp_path / "output").exists()
    assert not (tmp_path / "fixtures").exists()
    assert not (tmp_path / "accepted_manifest.json").exists()


def test_adapter_rejected_metadata_is_propagated_as_blocked_caveat():
    result = build_real_official_metadata_anchor_handoff(
        _request(),
        _provider_queue(),
        official_http_client=_fake_client(
            {
                "announcements": [
                    _annual_announcement(
                        adjunctUrl="https://www.cninfo.com.cn/finalpage/2026-04-30/annual.pdf"
                    )
                ]
            }
        ),
        allow_network=True,
    )

    assert REASON_ADAPTER_HANDOFF_REJECTED in result["blocked_reasons"]
    assert "adapter:all_records_rejected" in result["blocked_reasons"]
    assert result["anchor_map_result"]["anchor_items"][0]["official_anchor_status"] == "missing_anchor"


def test_anchor_map_missing_ambiguous_and_conflict_statuses_are_propagated():
    missing_result = build_real_official_metadata_anchor_handoff(
        _request(),
        _provider_queue(_provider_item(period="20260331", period_label="2026Q1"), periods=["20260331"]),
        official_http_client=_fake_client({"announcements": [_annual_announcement()]}),
        allow_network=True,
    )
    ambiguous_result = build_real_official_metadata_anchor_handoff(
        _request(),
        _provider_queue(),
        official_http_client=_fake_client(
            {
                "announcements": [
                    _annual_announcement(adjunctUrl="finalpage/2026-04-30/annual-a.pdf"),
                    _annual_announcement(
                        announcementTitle="Guodian NARI 2025 Annual Report Alternate",
                        adjunctUrl="finalpage/2026-04-30/annual-b.pdf",
                    ),
                ]
            }
        ),
        allow_network=True,
    )
    conflict_result = build_real_official_metadata_anchor_handoff(
        _request("2026Q1"),
        _provider_queue(
            _provider_item(period="20260331", period_label="2026FY", metric_value=260),
            periods=["20260331"],
        ),
        official_http_client=_fake_client({"announcements": [_quarterly_announcement()]}),
        allow_network=True,
    )

    assert _first_anchor_item(missing_result)["official_anchor_status"] == "missing_anchor"
    assert _first_anchor_item(ambiguous_result)["official_anchor_status"] == "ambiguous_anchor"
    assert _first_anchor_item(conflict_result)["official_anchor_status"] == "conflict"
    assert REASON_ANCHOR_MAP_NOT_FULLY_MATCHED in missing_result["blocked_reasons"]
    assert REASON_ANCHOR_MAP_NOT_FULLY_MATCHED in ambiguous_result["blocked_reasons"]
    assert REASON_ANCHOR_MAP_NOT_FULLY_MATCHED in conflict_result["blocked_reasons"]


def test_public_candidate_builder_preserves_metadata_only_shape():
    discovery = fetch_cninfo_metadata_for_request(
        _request(),
        official_http_client=_fake_client({"announcements": [_annual_announcement()]}),
        allow_network=True,
    )

    candidates = build_official_metadata_candidates_from_records(discovery["metadata_records"])

    assert candidates[0]["schema_version"] == "official_disclosure_metadata_candidate.v1"
    assert candidates[0]["not_official_verified"] is True
    assert candidates[0]["not_for_trading_advice"] is True


def test_public_anchor_handoff_uses_adapter_and_anchor_map():
    discovery = fetch_cninfo_metadata_for_request(
        _request(),
        official_http_client=_fake_client({"announcements": [_annual_announcement()]}),
        allow_network=True,
    )

    result = build_anchor_map_from_real_metadata(_request(), _provider_queue(), discovery["metadata_records"])

    assert result["discovery_adapter_result"]["discovery_candidates"]
    assert result["anchor_map_result"]["anchor_items"][0]["official_anchor_status"] == "matched"


def test_input_request_provider_queue_and_response_are_not_mutated():
    request = _request()
    provider_queue = _provider_queue()
    response = {"announcements": [_annual_announcement()]}
    before_request = copy.deepcopy(request)
    before_provider_queue = copy.deepcopy(provider_queue)
    before_response = copy.deepcopy(response)

    build_real_official_metadata_anchor_handoff(
        request,
        provider_queue,
        official_http_client=_fake_client(response),
        allow_network=True,
    )

    assert request == before_request
    assert provider_queue == before_provider_queue
    assert response == before_response


def test_no_output_fixture_or_manifest_write(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    result = build_real_official_metadata_anchor_handoff(
        _request(),
        _provider_queue(),
        official_http_client=_fake_client({"announcements": [_annual_announcement()]}),
        allow_network=True,
    )

    assert result["live_smoke_summary"]["metadata_records_found"] is True
    assert not (tmp_path / "output").exists()
    assert not (tmp_path / "fixtures").exists()
    assert not (tmp_path / "accepted_manifest.json").exists()


def test_default_cninfo_client_rejects_non_allowlist_redirect_final_host_without_echoing_url(
    monkeypatch,
    tmp_path,
    capsys,
):
    monkeypatch.chdir(tmp_path)
    redirect_secret = "RedirectSecretShouldNotEcho123"
    calls = []

    def fake_urlopen(req, timeout):
        calls.append({"url": req.full_url, "timeout": timeout})
        return _UrlopenResponse(
            final_url=f"https://evil.example.com/redirected?secret={redirect_secret}",
            payload={"announcements": [_annual_announcement()]},
        )

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    result = build_real_official_metadata_anchor_handoff(
        _request(),
        _provider_queue(),
        allow_network=True,
    )
    captured = capsys.readouterr()

    assert REASON_TRANSPORT_ERROR in result["blocked_reasons"]
    assert result["metadata_records"] == []
    assert calls == [{"url": "https://www.cninfo.com.cn/new/hisAnnouncement/query", "timeout": 15}]
    assert "evil.example.com" not in repr(result)
    assert "redirected" not in repr(result)
    assert redirect_secret not in repr(result)
    assert redirect_secret not in captured.out
    assert redirect_secret not in captured.err
    assert captured.out == ""
    assert captured.err == ""
    assert not (tmp_path / "output").exists()
    assert not (tmp_path / "fixtures").exists()
    assert not (tmp_path / "accepted_manifest.json").exists()


def test_default_cninfo_client_accepts_allowlist_final_host_and_parses_metadata(monkeypatch):
    calls = []

    def fake_urlopen(req, timeout):
        calls.append({"url": req.full_url, "timeout": timeout})
        return _UrlopenResponse(
            final_url="https://www.cninfo.com.cn/new/hisAnnouncement/query",
            payload={"announcements": [_annual_announcement()]},
        )

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    discovery = fetch_cninfo_metadata_for_request(_request(), allow_network=True)

    assert discovery["blocked_reasons"] == []
    assert discovery["metadata_records"][0]["source_domain"] == "static.cninfo.com.cn"
    assert calls == [{"url": "https://www.cninfo.com.cn/new/hisAnnouncement/query", "timeout": 15}]


def test_default_cninfo_client_rejects_pdf_content_type_as_transport_error(monkeypatch):
    def fake_urlopen(_req, timeout):
        return _UrlopenResponse(
            final_url="https://www.cninfo.com.cn/new/hisAnnouncement/query",
            payload={"announcements": [_annual_announcement()]},
            content_type="application/pdf",
        )

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    discovery = fetch_cninfo_metadata_for_request(_request(), allow_network=True)

    assert REASON_TRANSPORT_ERROR in discovery["blocked_reasons"]
    assert discovery["metadata_records"] == []


def test_default_cninfo_client_rejects_oversized_response_as_transport_error(monkeypatch):
    def fake_urlopen(_req, timeout):
        return _UrlopenResponse(
            final_url="https://www.cninfo.com.cn/new/hisAnnouncement/query",
            body=b"{" + (b"a" * MAX_METADATA_RESPONSE_BYTES),
        )

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    discovery = fetch_cninfo_metadata_for_request(_request(), allow_network=True)

    assert REASON_TRANSPORT_ERROR in discovery["blocked_reasons"]
    assert discovery["metadata_records"] == []
