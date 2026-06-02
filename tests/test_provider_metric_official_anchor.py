# -*- coding: utf-8 -*-

from __future__ import annotations

import copy

import pytest

from src.fundamental_skill.data_verification.provider_metric_official_anchor import (
    ANCHOR_MAP_SCHEMA_VERSION,
    ANCHOR_STATUS_AMBIGUOUS,
    ANCHOR_STATUS_CONFLICT,
    ANCHOR_STATUS_MATCHED,
    ANCHOR_STATUS_MISSING,
    PENDING_OFFICIAL_VERIFICATION_STATUS,
    PROVIDER_NAME,
    ProviderMetricOfficialAnchorError,
    build_provider_metric_official_disclosure_anchor_map,
    validate_provider_metric_official_disclosure_anchor_map,
)


def _provider_queue(*items, **overrides):
    queue = {
        "schema_version": "provider_candidate_metric_verification_queue.v1",
        "provider": PROVIDER_NAME,
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
        "provider": PROVIDER_NAME,
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
        "official_verification_status": PENDING_OFFICIAL_VERIFICATION_STATUS,
        "not_official_verified": True,
        "not_for_trading_advice": True,
        "caveats": ["provider_candidate_requires_official_verification"],
    }
    item.update(overrides)
    return item


def _official_candidate(**overrides):
    candidate = {
        "source_title": "Guodian NARI 2025 Annual Report",
        "source_url": "https://static.cninfo.com.cn/finalpage/2026-04-30/121.pdf",
        "source_domain": "static.cninfo.com.cn",
        "disclosure_date": "2026-04-30",
        "stock_code": "600406",
        "company_name_hint": "Guodian NARI",
        "period_key": "2025FY",
        "period_end_date": "20251231",
        "announcement_type": "annual_report",
        "source_type": "cninfo_official_pdf",
        "not_for_trading_advice": True,
    }
    candidate.update(overrides)
    return candidate


def _first_anchor(anchor_map):
    assert len(anchor_map["anchor_items"]) == 1
    return anchor_map["anchor_items"][0]


def test_valid_queue_and_annual_report_metadata_candidate_match_anchor():
    anchor_map = build_provider_metric_official_disclosure_anchor_map(
        _provider_queue(),
        [_official_candidate()],
    )
    item = _first_anchor(anchor_map)

    assert anchor_map["schema_version"] == ANCHOR_MAP_SCHEMA_VERSION
    assert item["official_anchor_status"] == ANCHOR_STATUS_MATCHED
    assert item["official_verification_status"] == PENDING_OFFICIAL_VERIFICATION_STATUS
    assert item["official_disclosure_anchor"]["announcement_type"] == "annual_report"
    assert item["official_disclosure_anchor"]["anchor_evidence_status"] == "official_anchor_candidate"
    validate_provider_metric_official_disclosure_anchor_map(anchor_map)


def test_valid_queue_and_quarterly_report_metadata_candidate_match_anchor():
    queue = _provider_queue(
        _provider_item(period="20260331", period_label="2026Q1", metric_value=260),
        periods=["20260331"],
    )
    candidate = _official_candidate(
        source_title="Guodian NARI 2026 Q1 Report",
        source_url="https://www.sse.com.cn/disclosure/listedinfo/announcement/c/new/2026.pdf",
        source_domain="www.sse.com.cn",
        disclosure_date="2026-04-30",
        period_key="2026Q1",
        period_end_date="20260331",
        announcement_type="quarterly_report",
        source_type="sse_exchange_announcement",
    )

    item = _first_anchor(build_provider_metric_official_disclosure_anchor_map(queue, [candidate]))

    assert item["official_anchor_status"] == ANCHOR_STATUS_MATCHED
    assert item["official_disclosure_anchor"]["announcement_type"] == "quarterly_report"


def test_2025_fy_item_maps_to_annual_report():
    item = _provider_item(period="20250930", period_label="2025FY")
    candidate = _official_candidate(period_end_date="20250930", period_key="2025FY")

    anchor_item = _first_anchor(build_provider_metric_official_disclosure_anchor_map(_provider_queue(item), [candidate]))

    assert anchor_item["official_anchor_status"] == ANCHOR_STATUS_MATCHED
    assert anchor_item["official_disclosure_anchor"]["announcement_type"] == "annual_report"


def test_2026_q1_item_maps_to_quarterly_report():
    item = _provider_item(period="20260331", period_label="2026Q1")
    candidate = _official_candidate(
        period_end_date="20260331",
        period_key="2026Q1",
        announcement_type="quarterly_report",
    )

    anchor_item = _first_anchor(build_provider_metric_official_disclosure_anchor_map(_provider_queue(item), [candidate]))

    assert anchor_item["official_anchor_status"] == ANCHOR_STATUS_MATCHED
    assert anchor_item["official_disclosure_anchor"]["announcement_type"] == "quarterly_report"


def test_missing_metadata_becomes_missing_anchor():
    candidate = _official_candidate()
    candidate.pop("source_title")

    anchor_map = build_provider_metric_official_disclosure_anchor_map(_provider_queue(), [candidate])
    item = _first_anchor(anchor_map)

    assert item["official_anchor_status"] == ANCHOR_STATUS_MISSING
    assert anchor_map["candidate_disclosure_summary"]["usable_candidates"] == 0
    assert anchor_map["candidate_disclosure_summary"]["rejected_candidates"][0]["reasons"] == ["missing_source_title"]


def test_empty_candidates_become_missing_anchor():
    item = _first_anchor(build_provider_metric_official_disclosure_anchor_map(_provider_queue(), []))

    assert item["official_anchor_status"] == ANCHOR_STATUS_MISSING
    assert item["official_disclosure_anchor"] is None


def test_non_list_candidates_are_blocked():
    anchor_map = build_provider_metric_official_disclosure_anchor_map(_provider_queue(), {"candidate": "not-list"})

    assert anchor_map["anchor_items"] == []
    assert "official_metadata_candidates_must_be_list" in anchor_map["blocked_reasons"]


def test_non_allowlist_domain_is_rejected():
    anchor_map = build_provider_metric_official_disclosure_anchor_map(
        _provider_queue(),
        [_official_candidate(source_url="https://example.com/report.pdf", source_domain="example.com")],
    )

    assert _first_anchor(anchor_map)["official_anchor_status"] == ANCHOR_STATUS_MISSING
    rejected = anchor_map["candidate_disclosure_summary"]["rejected_candidates"][0]
    assert "source_domain_not_allowlisted" in rejected["reasons"]
    assert "source_url_domain_not_allowlisted" in rejected["reasons"]


def test_source_url_pdf_is_preserved_as_metadata_without_side_effect(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    pdf_url = "https://static.cninfo.com.cn/finalpage/2026-04-30/121.PDF"

    anchor_map = build_provider_metric_official_disclosure_anchor_map(
        _provider_queue(),
        [_official_candidate(source_url=pdf_url)],
    )

    anchor = _first_anchor(anchor_map)["official_disclosure_anchor"]
    assert anchor["source_url"] == pdf_url
    assert not (tmp_path / "output").exists()
    assert not (tmp_path / "fixtures").exists()


def test_stock_code_mismatch_is_not_matched():
    item = _first_anchor(
        build_provider_metric_official_disclosure_anchor_map(
            _provider_queue(),
            [_official_candidate(stock_code="000001")],
        )
    )

    assert item["official_anchor_status"] == ANCHOR_STATUS_MISSING
    assert "stock_code_mismatch_candidate_rejected" in item["caveats"]


def test_period_mismatch_is_not_matched():
    item = _first_anchor(
        build_provider_metric_official_disclosure_anchor_map(
            _provider_queue(),
            [_official_candidate(period_end_date="20260331", announcement_type="quarterly_report")],
        )
    )

    assert item["official_anchor_status"] == ANCHOR_STATUS_MISSING
    assert "period_mismatch_candidate_rejected" in item["caveats"]


def test_announcement_type_mismatch_is_conflict_not_matched():
    item = _first_anchor(
        build_provider_metric_official_disclosure_anchor_map(
            _provider_queue(),
            [_official_candidate(announcement_type="quarterly_report")],
        )
    )

    assert item["official_anchor_status"] == ANCHOR_STATUS_CONFLICT
    assert item["official_disclosure_anchor"] is None
    assert "candidate_announcement_type_conflict" in item["caveats"]


def test_multiple_identical_candidates_are_deduped_and_matched():
    candidate = _official_candidate()
    anchor_map = build_provider_metric_official_disclosure_anchor_map(
        _provider_queue(),
        [copy.deepcopy(candidate), copy.deepcopy(candidate)],
    )

    assert _first_anchor(anchor_map)["official_anchor_status"] == ANCHOR_STATUS_MATCHED


def test_multiple_different_candidates_are_ambiguous():
    second = _official_candidate(
        source_title="Guodian NARI 2025 Annual Report Alternate",
        source_url="https://www.cninfo.com.cn/new/disclosure/detail/alternate.pdf",
        source_domain="www.cninfo.com.cn",
    )

    item = _first_anchor(
        build_provider_metric_official_disclosure_anchor_map(_provider_queue(), [_official_candidate(), second])
    )

    assert item["official_anchor_status"] == ANCHOR_STATUS_AMBIGUOUS
    assert item["official_disclosure_anchor"] is None


def test_provider_item_remains_pending_and_not_officially_verified():
    item = _first_anchor(build_provider_metric_official_disclosure_anchor_map(_provider_queue(), [_official_candidate()]))

    assert item["official_verification_status"] == PENDING_OFFICIAL_VERIFICATION_STATUS
    assert item["not_official_verified"] is True
    assert "official_verification_required" not in item


def test_matched_anchor_does_not_create_forbidden_verified_field():
    anchor_map = build_provider_metric_official_disclosure_anchor_map(_provider_queue(), [_official_candidate()])
    serialized = repr(anchor_map)

    assert "official_verified" not in serialized.replace("not_official_verified", "")


def test_provider_metric_value_remains_provider_candidate_value():
    item = _first_anchor(build_provider_metric_official_disclosure_anchor_map(_provider_queue(), [_official_candidate()]))

    assert item["metric_value"] == 1000
    assert item["source_table"] == "income"
    assert item["source_field"] == "revenue"


def test_no_output_fixture_or_manifest_write(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    anchor_map = build_provider_metric_official_disclosure_anchor_map(_provider_queue(), [_official_candidate()])

    assert anchor_map["provider"] == PROVIDER_NAME
    assert not (tmp_path / "output").exists()
    assert not (tmp_path / "fixtures").exists()
    assert not (tmp_path / "accepted_manifest.json").exists()


def test_input_queue_and_candidates_are_not_mutated():
    queue = _provider_queue()
    candidates = [_official_candidate()]
    before_queue = copy.deepcopy(queue)
    before_candidates = copy.deepcopy(candidates)

    build_provider_metric_official_disclosure_anchor_map(queue, candidates)

    assert queue == before_queue
    assert candidates == before_candidates


@pytest.mark.parametrize(
    "field, value, reason",
    [
        ("schema_version", "wrong", "invalid_provider_queue_schema_version"),
        ("provider", "Other", "unsupported_provider"),
        ("verification_items", "not-list", "verification_items_must_be_list"),
    ],
)
def test_provider_queue_shape_errors_block_mapping(field, value, reason):
    queue = _provider_queue()
    queue[field] = value

    anchor_map = build_provider_metric_official_disclosure_anchor_map(queue, [_official_candidate()])

    assert anchor_map["anchor_items"] == []
    assert reason in anchor_map["blocked_reasons"]


@pytest.mark.parametrize(
    "mutate, reason",
    [
        (lambda item: item.pop("period"), "item:0:missing_period"),
        (lambda item: item.pop("metric_key"), "item:0:missing_metric_key"),
        (
            lambda item: item.update({"official_verification_status": "verified"}),
            "item:0:invalid_official_verification_status",
        ),
        (lambda item: item.update({"not_official_verified": False}), "item:0:not_official_verified_must_be_true_bool"),
        (lambda item: item.update({"not_for_trading_advice": False}), "item:0:advice_safety_flag_must_be_true_bool"),
    ],
)
def test_provider_item_shape_errors_block_mapping(mutate, reason):
    item = _provider_item()
    mutate(item)

    anchor_map = build_provider_metric_official_disclosure_anchor_map(_provider_queue(item), [_official_candidate()])

    assert anchor_map["anchor_items"] == []
    assert reason in anchor_map["blocked_reasons"]


def test_missing_provider_queue_is_blocked():
    anchor_map = build_provider_metric_official_disclosure_anchor_map(None, [_official_candidate()])

    assert anchor_map["anchor_items"] == []
    assert "missing_provider_queue" in anchor_map["blocked_reasons"]


def test_missing_verification_items_are_blocked():
    queue = _provider_queue()
    queue.pop("verification_items")

    anchor_map = build_provider_metric_official_disclosure_anchor_map(queue, [_official_candidate()])

    assert anchor_map["anchor_items"] == []
    assert "missing_verification_items" in anchor_map["blocked_reasons"]
