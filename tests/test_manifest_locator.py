# -*- coding: utf-8 -*-

import builtins
import json
import os
from pathlib import Path

import pytest

from src.fundamental_skill.research_planning.manifest_locator import (
    ACCEPTED_STATUSES,
    ARTIFACT_FORMATS,
    ARTIFACT_KINDS,
    FRESHNESS_STATUSES,
    HASH_STATUSES,
    MANIFEST_ENTRY_ROW_SCHEMA_VERSION,
    MANIFEST_EXISTS_STATUSES,
    MANIFEST_LOCATOR_PAYLOAD_SCHEMA_VERSION,
    MANIFEST_SCHEMA_STATUSES,
    SOURCE_STATUSES,
    SYNTHETIC_MANIFEST_LOCATOR_INPUT_SCHEMA_VERSION,
    UNMATCHED_REASONS,
    build_manifest_entry_row,
    build_manifest_locator_payload,
    parse_synthetic_manifest_locator,
    validate_manifest_entry_row,
    validate_manifest_locator_payload,
)


def _valid_entry(**overrides):
    row = build_manifest_entry_row(
        stock_code="600406",
        company_name="NARI Technology",
        artifact_path="output/research_reports/20260529T000000Z/600406/fundamental_research_report_v1.json",
        artifact_kind="research_report_v1",
        artifact_format="json",
        accepted_status="accepted",
        freshness_status="current",
        hash_status="not_checked",
        source_status="available",
        caveats=["Manifest locator artifact state only."],
    )
    row.update(overrides)
    return row


def _valid_payload(**overrides):
    payload = build_manifest_locator_payload(
        stock_code="600406",
        company_name="NARI Technology",
        manifest_exists_status="not_checked",
        manifest_schema_status="not_checked",
        manifest_entry_count=0,
        matched_entries=[],
        report_artifact_refs=[],
        freshness_status="unknown",
        lineage_refs=[],
        caveats=["Read-only manifest locator state only."],
    )
    payload.update(overrides)
    return payload


def _synthetic_artifact(**overrides):
    artifact = {
        "artifact_path": "output/research_reports/synthetic/600406/fundamental_research_report_v1.json",
        "artifact_kind": "research_report_v1",
        "artifact_format": "json",
        "accepted_status": "accepted",
        "freshness_status": "current",
        "hash_status": "not_checked",
        "source_status": "available",
        "caveats": ["Synthetic manifest locator state only."],
        "not_for_trading_advice": True,
    }
    artifact.update(overrides)
    return artifact


def _synthetic_entry(**overrides):
    entry = {
        "stock_code": "600406",
        "company_name": "NARI Technology",
        "artifacts": [_synthetic_artifact()],
        "not_for_trading_advice": True,
    }
    entry.update(overrides)
    return entry


def _synthetic_manifest(**overrides):
    manifest = {
        "schema_version": SYNTHETIC_MANIFEST_LOCATOR_INPUT_SCHEMA_VERSION,
        "generated_at": "2026-05-30T00:00:00Z",
        "entries": [_synthetic_entry()],
        "not_for_trading_advice": True,
    }
    manifest.update(overrides)
    return manifest


def _write_synthetic_manifest(tmp_path, manifest):
    path = tmp_path / "synthetic_manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_enums_include_required_values():
    assert {"exists", "missing", "unreadable", "unknown", "not_checked"}.issubset(
        MANIFEST_EXISTS_STATUSES
    )
    assert {"valid", "invalid_json", "schema_mismatch", "unreadable", "not_checked"}.issubset(
        MANIFEST_SCHEMA_STATUSES
    )
    assert {"accepted", "missing", "stale", "superseded", "invalidated", "conflict_open"}.issubset(
        ACCEPTED_STATUSES
    )
    assert {"current", "unknown", "stale", "superseded", "invalidated", "not_applicable"}.issubset(
        FRESHNESS_STATUSES
    )
    assert {"match", "mismatch", "missing", "not_checked", "not_applicable"}.issubset(
        HASH_STATUSES
    )
    assert {"available", "missing", "review_required", "conflict_open", "ignored"}.issubset(
        SOURCE_STATUSES
    )
    assert {"accepted_manifest", "research_report_v1", "lineage_artifact", "unknown"}.issubset(
        ARTIFACT_KINDS
    )
    assert {"json", "markdown", "html", "manifest", "unknown"}.issubset(ARTIFACT_FORMATS)
    assert {"", "missing", "data_collection_required", "manifest_missing"}.issubset(
        UNMATCHED_REASONS
    )


def test_valid_minimal_locator_payload():
    payload = build_manifest_locator_payload()

    assert payload["schema_version"] == MANIFEST_LOCATOR_PAYLOAD_SCHEMA_VERSION
    assert payload["manifest_path"] == "output/research_reports/accepted_manifest.json"
    assert payload["matched_entries"] == []
    assert payload["report_artifact_refs"] == []
    assert payload["not_for_trading_advice"] is True
    assert validate_manifest_locator_payload(payload) == payload


def test_valid_manifest_entry_row():
    row = _valid_entry()

    assert row["schema_version"] == MANIFEST_ENTRY_ROW_SCHEMA_VERSION
    assert row["not_for_trading_advice"] is True
    assert row["accepted_status"] == "accepted"
    assert row["freshness_status"] == "current"
    assert validate_manifest_entry_row(row) == row


@pytest.mark.parametrize("validator, payload", [
    (validate_manifest_entry_row, lambda: _valid_entry(stock_code="ABC")),
    (validate_manifest_locator_payload, lambda: _valid_payload(stock_code="ABC")),
])
def test_invalid_stock_code_is_rejected(validator, payload):
    with pytest.raises(ValueError, match="stock_code"):
        validator(payload())


@pytest.mark.parametrize("validator, payload", [
    (validate_manifest_entry_row, lambda: _valid_entry(not_for_trading_advice=False)),
    (validate_manifest_locator_payload, lambda: _valid_payload(not_for_trading_advice=False)),
])
def test_not_for_trading_advice_false_is_rejected(validator, payload):
    with pytest.raises(ValueError, match="not_for_trading_advice"):
        validator(payload())


@pytest.mark.parametrize("validator, payload, field", [
    (validate_manifest_entry_row, lambda: _valid_entry(artifact_kind="not_a_kind"), "artifact_kind"),
    (
        validate_manifest_locator_payload,
        lambda: _valid_payload(manifest_exists_status="not_a_status"),
        "manifest_exists_status",
    ),
])
def test_invalid_enum_is_rejected(validator, payload, field):
    with pytest.raises(ValueError, match=field):
        validator(payload())


def test_matched_entries_must_be_list():
    payload = _valid_payload(matched_entries={})

    with pytest.raises(ValueError, match="matched_entries"):
        validate_manifest_locator_payload(payload)


def test_report_artifact_refs_must_be_list():
    payload = _valid_payload(report_artifact_refs={})

    with pytest.raises(ValueError, match="report_artifact_refs"):
        validate_manifest_locator_payload(payload)


def test_report_artifact_refs_accept_safe_report_paths():
    ref = "output/research_reports/20260529T000000Z/600406/fundamental_research_report_v1.json"
    payload = _valid_payload(report_artifact_refs=[ref])

    assert validate_manifest_locator_payload(payload)["report_artifact_refs"] == [ref]


def test_report_artifact_refs_reject_unsafe_paths():
    payload = _valid_payload(report_artifact_refs=["config/token.txt"])

    with pytest.raises(ValueError, match="unsafe artifact_path"):
        validate_manifest_locator_payload(payload)


def test_report_artifact_refs_reject_forbidden_marker_without_path_leak():
    ref = "output/research_reports/20260529T000000Z/600406/target_price_report.json"
    payload = _valid_payload(report_artifact_refs=[ref])

    with pytest.raises(ValueError) as excinfo:
        validate_manifest_locator_payload(payload)

    assert "safety violation" in str(excinfo.value)
    assert ref not in str(excinfo.value)


@pytest.mark.parametrize("field", ["caveats", "lineage_refs"])
def test_locator_payload_list_fields_are_required(field):
    payload = _valid_payload(**{field: {}})

    with pytest.raises(ValueError, match=field):
        validate_manifest_locator_payload(payload)


def test_manifest_entry_caveats_must_be_list():
    row = _valid_entry(caveats={})

    with pytest.raises(ValueError, match="caveats"):
        validate_manifest_entry_row(row)


def test_manifest_path_unsafe_is_rejected():
    payload = _valid_payload(manifest_path="config/.env.local")

    with pytest.raises(ValueError, match="unsafe artifact_path"):
        validate_manifest_locator_payload(payload)


def test_artifact_path_unsafe_is_rejected():
    row = _valid_entry(artifact_path="config/token.txt")

    with pytest.raises(ValueError, match="unsafe artifact_path"):
        validate_manifest_entry_row(row)


@pytest.mark.parametrize(
    "marker",
    [
        "verified_fact",
        "auto_verified",
        "accepted_manifest_update",
        "research_report_v1_update",
        "provider_primary_switch",
        "fixture_promotion",
        "target_price",
        "trading_signal",
    ],
)
def test_forbidden_markers_are_rejected(marker):
    row = _valid_entry(caveats=[marker])

    with pytest.raises(ValueError, match="safety violation"):
        validate_manifest_entry_row(row)


@pytest.mark.parametrize(
    "marker",
    [
        "verified_fact",
        "accepted_manifest_update",
        "research_report_v1_update",
        "provider_primary_switch",
        "fixture_promotion",
        "target_price",
    ],
)
def test_forbidden_markers_in_locator_payload_are_rejected(marker):
    payload = _valid_payload(caveats=[marker])

    with pytest.raises(ValueError, match="safety violation"):
        validate_manifest_locator_payload(payload)


def test_forbidden_marker_in_artifact_path_is_rejected_before_path_can_hide_it():
    path = "output/research_reports/20260529T000000Z/600406/target_price_report.json"
    row = _valid_entry(artifact_path=path)

    with pytest.raises(ValueError) as excinfo:
        validate_manifest_entry_row(row)

    assert "safety violation" in str(excinfo.value)
    assert path not in str(excinfo.value)


def test_accepted_current_is_not_verified_fact():
    row = _valid_entry(accepted_status="accepted", freshness_status="current")
    payload = build_manifest_locator_payload(
        stock_code="600406",
        matched_entries=[row],
        manifest_entry_count=1,
        freshness_status="current",
        caveats=["Accepted/current manifest state remains artifact lineage only."],
    )

    assert payload["matched_entries"][0]["accepted_status"] == "accepted"
    assert payload["matched_entries"][0]["freshness_status"] == "current"
    assert "verified_fact" not in repr(payload)
    assert "auto_verified" not in repr(payload)


def test_company_name_only_identity_remains_review_required():
    row = build_manifest_entry_row(
        company_name="Name Only",
        artifact_path="output/research_reports/20260529T000000Z/600406/fundamental_research_report_v1.json",
        artifact_kind="research_report_v1",
        artifact_format="json",
        accepted_status="review_required",
        source_status="review_required",
        caveats=["Name-only identity cannot confirm stock_code."],
    )

    assert row["stock_code"] == ""
    assert row["source_status"] == "review_required"


def test_unknown_ticker_does_not_fallback_to_accepted_samples():
    payload = build_manifest_locator_payload(
        stock_code="300475",
        manifest_exists_status="not_checked",
        manifest_schema_status="not_checked",
        unmatched_reason="data_collection_required",
        matched_entries=[],
        report_artifact_refs=[],
        caveats=["Unknown ticker requires data collection; no accepted-sample fallback."],
    )

    assert payload["stock_code"] == "300475"
    assert payload["matched_entries"] == []
    assert payload["unmatched_reason"] == "data_collection_required"
    rendered = repr(payload)
    assert "600406" not in rendered
    assert "002371" not in rendered
    assert "002050" not in rendered


def test_validators_do_not_use_file_io(monkeypatch):
    def fail_open(*args, **kwargs):
        raise AssertionError("manifest locator validators must not open files")

    monkeypatch.setattr(builtins, "open", fail_open)

    row = _valid_entry()
    payload = _valid_payload(matched_entries=[row], manifest_entry_count=1)

    assert validate_manifest_entry_row(row)["stock_code"] == "600406"
    assert validate_manifest_locator_payload(payload)["manifest_entry_count"] == 1


def test_parse_valid_synthetic_manifest(tmp_path):
    manifest_path = _write_synthetic_manifest(tmp_path, _synthetic_manifest())

    payload = parse_synthetic_manifest_locator(
        manifest_path,
        stock_code="600406",
        company_name_hint="NARI Technology",
    )

    assert payload["schema_version"] == MANIFEST_LOCATOR_PAYLOAD_SCHEMA_VERSION
    assert payload["manifest_exists_status"] == "exists"
    assert payload["manifest_schema_status"] == "valid"
    assert payload["manifest_entry_count"] == 1
    assert payload["unmatched_reason"] == ""
    assert payload["stock_code"] == "600406"
    assert payload["company_name"] == "NARI Technology"
    assert payload["report_artifact_refs"] == [
        "output/research_reports/synthetic/600406/fundamental_research_report_v1.json"
    ]
    assert payload["matched_entries"][0]["schema_version"] == MANIFEST_ENTRY_ROW_SCHEMA_VERSION
    assert payload["matched_entries"][0]["accepted_status"] == "accepted"
    assert validate_manifest_locator_payload(payload) == payload


def test_parse_valid_synthetic_manifest_accepts_report_artifacts_alias(tmp_path):
    entry = _synthetic_entry(report_artifacts=[_synthetic_artifact()])
    del entry["artifacts"]
    manifest_path = _write_synthetic_manifest(tmp_path, _synthetic_manifest(entries=[entry]))

    payload = parse_synthetic_manifest_locator(manifest_path, stock_code="600406")

    assert payload["manifest_schema_status"] == "valid"
    assert len(payload["matched_entries"]) == 1


def test_parse_missing_synthetic_manifest_returns_missing_without_fallback(tmp_path):
    payload = parse_synthetic_manifest_locator(tmp_path / "missing_manifest.json", stock_code="300475")

    assert payload["manifest_exists_status"] == "missing"
    assert payload["manifest_schema_status"] == "not_checked"
    assert payload["unmatched_reason"] == "manifest_missing"
    assert payload["matched_entries"] == []


def test_parse_unreadable_synthetic_manifest_returns_unreadable(tmp_path, monkeypatch):
    manifest_path = _write_synthetic_manifest(tmp_path, _synthetic_manifest())

    def unreadable_open(*args, **kwargs):
        raise PermissionError("blocked synthetic manifest read")

    monkeypatch.setattr(builtins, "open", unreadable_open)

    payload = parse_synthetic_manifest_locator(manifest_path, stock_code="600406")

    assert payload["manifest_exists_status"] == "unreadable"
    assert payload["manifest_schema_status"] == "unreadable"
    assert payload["unmatched_reason"] == "manifest_unreadable"


def test_parse_invalid_json_synthetic_manifest(tmp_path):
    manifest_path = tmp_path / "synthetic_manifest.json"
    manifest_path.write_text("{not valid json", encoding="utf-8")

    payload = parse_synthetic_manifest_locator(manifest_path, stock_code="600406")

    assert payload["manifest_schema_status"] == "invalid_json"
    assert payload["unmatched_reason"] == "invalid_json"
    assert payload["matched_entries"] == []


def test_parse_invalid_synthetic_schema_version(tmp_path):
    manifest_path = _write_synthetic_manifest(
        tmp_path,
        _synthetic_manifest(schema_version="not_synthetic_manifest_locator_input.v1"),
    )

    payload = parse_synthetic_manifest_locator(manifest_path, stock_code="600406")

    assert payload["manifest_schema_status"] == "schema_mismatch"
    assert payload["unmatched_reason"] == "schema_mismatch"
    assert payload["matched_entries"] == []


def test_parse_synthetic_manifest_entries_missing(tmp_path):
    manifest = _synthetic_manifest()
    del manifest["entries"]
    manifest_path = _write_synthetic_manifest(tmp_path, manifest)

    payload = parse_synthetic_manifest_locator(manifest_path, stock_code="600406")

    assert payload["manifest_schema_status"] == "schema_mismatch"
    assert payload["unmatched_reason"] == "schema_mismatch"


def test_parse_synthetic_manifest_entries_not_list(tmp_path):
    manifest_path = _write_synthetic_manifest(tmp_path, _synthetic_manifest(entries={}))

    payload = parse_synthetic_manifest_locator(manifest_path, stock_code="600406")

    assert payload["manifest_schema_status"] == "schema_mismatch"
    assert payload["unmatched_reason"] == "schema_mismatch"


def test_parse_synthetic_manifest_unsafe_manifest_path_does_not_open(monkeypatch):
    def fail_open(*args, **kwargs):
        raise AssertionError("unsafe synthetic manifest path must not be opened")

    monkeypatch.setattr(builtins, "open", fail_open)

    payload = parse_synthetic_manifest_locator(
        "output/research_reports/accepted_manifest.json",
        stock_code="600406",
    )

    assert payload["manifest_exists_status"] == "not_checked"
    assert payload["unmatched_reason"] == "unsafe_path"
    assert payload["matched_entries"] == []


def test_parse_synthetic_manifest_unsafe_artifact_path(tmp_path):
    manifest_path = _write_synthetic_manifest(
        tmp_path,
        _synthetic_manifest(
            entries=[
                _synthetic_entry(
                    artifacts=[
                        _synthetic_artifact(artifact_path="config/token.txt"),
                    ]
                )
            ]
        ),
    )

    payload = parse_synthetic_manifest_locator(manifest_path, stock_code="600406")

    assert payload["manifest_schema_status"] == "review_required"
    assert payload["unmatched_reason"] == "unsafe_path"
    assert payload["matched_entries"] == []


def test_parse_synthetic_manifest_invalid_artifact_enum(tmp_path):
    manifest_path = _write_synthetic_manifest(
        tmp_path,
        _synthetic_manifest(
            entries=[
                _synthetic_entry(
                    artifacts=[
                        _synthetic_artifact(artifact_kind="not_a_kind"),
                    ]
                )
            ]
        ),
    )

    payload = parse_synthetic_manifest_locator(manifest_path, stock_code="600406")

    assert payload["manifest_schema_status"] == "schema_mismatch"
    assert payload["unmatched_reason"] == "schema_mismatch"
    assert payload["matched_entries"] == []


def test_parse_synthetic_manifest_artifact_caveats_must_be_list(tmp_path):
    manifest_path = _write_synthetic_manifest(
        tmp_path,
        _synthetic_manifest(
            entries=[
                _synthetic_entry(
                    artifacts=[
                        _synthetic_artifact(caveats={"not": "a-list"}),
                    ]
                )
            ]
        ),
    )

    payload = parse_synthetic_manifest_locator(manifest_path, stock_code="600406")

    assert payload["manifest_schema_status"] == "schema_mismatch"
    assert payload["unmatched_reason"] == "schema_mismatch"
    assert payload["matched_entries"] == []


def test_parse_unknown_ticker_does_not_fallback_to_accepted_samples(tmp_path):
    manifest_path = _write_synthetic_manifest(tmp_path, _synthetic_manifest())

    payload = parse_synthetic_manifest_locator(manifest_path, stock_code="300475")

    assert payload["manifest_schema_status"] == "valid"
    assert payload["unmatched_reason"] == "data_collection_required"
    assert payload["matched_entries"] == []
    rendered = repr(payload)
    assert "600406" not in rendered
    assert "002371" not in rendered
    assert "002050" not in rendered


def test_parse_synthetic_manifest_duplicate_entries(tmp_path):
    manifest_path = _write_synthetic_manifest(
        tmp_path,
        _synthetic_manifest(entries=[_synthetic_entry(), _synthetic_entry()]),
    )

    payload = parse_synthetic_manifest_locator(manifest_path, stock_code="600406")

    assert payload["manifest_schema_status"] == "review_required"
    assert payload["unmatched_reason"] == "duplicate_entries"
    assert payload["matched_entries"] == []


def test_parse_synthetic_manifest_code_name_conflict(tmp_path):
    manifest_path = _write_synthetic_manifest(tmp_path, _synthetic_manifest())

    payload = parse_synthetic_manifest_locator(
        manifest_path,
        stock_code="600406",
        company_name_hint="Different Company",
    )

    assert payload["manifest_schema_status"] == "review_required"
    assert payload["unmatched_reason"] == "conflict_open"
    assert payload["matched_entries"] == []


def test_parse_synthetic_manifest_name_hint_different_code_conflict(tmp_path):
    manifest_path = _write_synthetic_manifest(tmp_path, _synthetic_manifest())

    payload = parse_synthetic_manifest_locator(
        manifest_path,
        stock_code="300475",
        company_name_hint="NARI Technology",
    )

    assert payload["manifest_schema_status"] == "review_required"
    assert payload["unmatched_reason"] == "conflict_open"
    assert payload["matched_entries"] == []
    assert "600406" not in repr(payload)


def test_parse_synthetic_manifest_not_for_trading_advice_false_rejects(tmp_path):
    manifest_path = _write_synthetic_manifest(
        tmp_path,
        _synthetic_manifest(not_for_trading_advice=False),
    )

    payload = parse_synthetic_manifest_locator(manifest_path, stock_code="600406")

    assert payload["manifest_schema_status"] == "schema_mismatch"
    assert payload["unmatched_reason"] == "schema_mismatch"
    assert payload["matched_entries"] == []


def test_parse_synthetic_manifest_artifact_policy_false_rejects(tmp_path):
    manifest_path = _write_synthetic_manifest(
        tmp_path,
        _synthetic_manifest(
            entries=[
                _synthetic_entry(
                    artifacts=[
                        _synthetic_artifact(not_for_trading_advice=False),
                    ]
                )
            ]
        ),
    )

    payload = parse_synthetic_manifest_locator(manifest_path, stock_code="600406")

    assert payload["manifest_schema_status"] == "schema_mismatch"
    assert payload["unmatched_reason"] == "schema_mismatch"
    assert payload["matched_entries"] == []


def test_parse_synthetic_manifest_marker_violation_rejects(tmp_path):
    manifest_path = _write_synthetic_manifest(
        tmp_path,
        _synthetic_manifest(
            entries=[
                _synthetic_entry(
                    artifacts=[
                        _synthetic_artifact(caveats=["verified_fact"]),
                    ]
                )
            ]
        ),
    )

    payload = parse_synthetic_manifest_locator(manifest_path, stock_code="600406")

    assert payload["manifest_schema_status"] == "review_required"
    assert payload["unmatched_reason"] == "review_required"
    assert payload["matched_entries"] == []


def test_parse_synthetic_manifest_no_directory_scan_report_read_or_file_write(tmp_path, monkeypatch):
    artifact_path = "output/research_reports/synthetic/600406/fundamental_research_report_v1.json"
    manifest_path = _write_synthetic_manifest(
        tmp_path,
        _synthetic_manifest(entries=[_synthetic_entry(artifacts=[_synthetic_artifact(artifact_path=artifact_path)])]),
    )
    original_open = builtins.open

    def guarded_open(file, mode="r", *args, **kwargs):
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            raise AssertionError("synthetic parser must not write files")
        if str(file) != str(manifest_path):
            raise AssertionError(f"synthetic parser must not open artifact paths: {file}")
        return original_open(file, mode, *args, **kwargs)

    def fail_directory_scan(*args, **kwargs):
        raise AssertionError("synthetic parser must not scan directories")

    monkeypatch.setattr(builtins, "open", guarded_open)
    monkeypatch.setattr(os, "listdir", fail_directory_scan)
    monkeypatch.setattr(Path, "iterdir", fail_directory_scan)
    monkeypatch.setattr(Path, "glob", fail_directory_scan)
    monkeypatch.setattr(Path, "rglob", fail_directory_scan)

    payload = parse_synthetic_manifest_locator(manifest_path, stock_code="600406")

    assert payload["manifest_schema_status"] == "valid"
    assert payload["matched_entries"][0]["artifact_path"] == artifact_path
