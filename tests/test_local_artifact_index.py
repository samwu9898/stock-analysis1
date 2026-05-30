# -*- coding: utf-8 -*-

import builtins
from copy import deepcopy
import glob
import os
from pathlib import Path

import pytest

from src.fundamental_skill.research_planning.local_artifact_index import (
    ARTIFACT_TYPES,
    FRESHNESS_STATUSES,
    IDENTITY_RESOLUTION_STATUSES,
    INVENTORY_GROUPS,
    LOCAL_ARTIFACT_INDEX_ROW_SCHEMA_VERSION,
    REVIEW_STATUSES,
    SOURCE_FAMILIES,
    SOURCE_STATUSES,
    TICKER_LOCAL_ARTIFACT_INVENTORY_SCHEMA_VERSION,
    build_artifact_row,
    build_ticker_local_artifact_inventory,
    classify_artifact_path,
    should_ignore_artifact_path,
    validate_artifact_path_safety,
    validate_artifact_row,
    validate_ticker_local_artifact_inventory,
)
from src.fundamental_skill.research_planning.manifest_locator import (
    build_manifest_entry_row,
    build_manifest_locator_payload,
)


def _valid_row(**overrides):
    row = build_artifact_row(
        artifact_type="provider_candidate_artifact",
        artifact_path="output/ground_truth_candidates/20260529T000000Z/600406/fact_candidates.json",
        source_family="provider_candidates",
        stock_code="600406",
        sha256="0123456789abcdef" * 4,
        file_size=123,
        source_status="candidate_only",
        review_status="not_reviewed",
        freshness_status="unknown",
        caveats=["Candidate artifact state only."],
        lineage_refs=["provider:tushare_local_artifact"],
    )
    row.update(overrides)
    return row


def test_enums_include_required_values():
    assert "provider_candidate_artifact" in ARTIFACT_TYPES
    assert "workflow_signal" in SOURCE_FAMILIES
    assert {
        "available",
        "missing",
        "partial",
        "candidate_only",
        "review_required",
        "conflict_open",
        "stale",
        "invalidated",
        "unreadable",
        "ignored",
    }.issubset(SOURCE_STATUSES)
    assert "review_required" in REVIEW_STATUSES
    assert {"current", "unknown", "stale", "superseded", "invalidated", "not_applicable"}.issubset(
        FRESHNESS_STATUSES
    )
    assert {"resolved", "not_found", "conflict_requires_review"}.issubset(IDENTITY_RESOLUTION_STATUSES)
    assert {"available", "missing", "ignored", "conflict"}.issubset(INVENTORY_GROUPS)


def test_valid_artifact_row():
    row = _valid_row()

    assert row["schema_version"] == LOCAL_ARTIFACT_INDEX_ROW_SCHEMA_VERSION
    assert row["not_for_trading_advice"] is True
    assert row["artifact_id"].startswith("local_artifact_")
    assert validate_artifact_row(row) == row


def test_invalid_not_for_trading_advice_false_is_rejected():
    row = _valid_row(not_for_trading_advice=False)

    with pytest.raises(ValueError, match="not_for_trading_advice"):
        validate_artifact_row(row)


def test_invalid_stock_code_is_rejected():
    row = _valid_row(stock_code="ABC")

    with pytest.raises(ValueError, match="stock_code"):
        validate_artifact_row(row)


def test_invalid_enum_is_rejected():
    row = _valid_row(artifact_type="not_a_supported_type")

    with pytest.raises(ValueError, match="artifact_type"):
        validate_artifact_row(row)


def test_provider_candidates_path_classification():
    result = classify_artifact_path(
        "output/ground_truth_candidates/20260529T000000Z/600406/fact_candidates.json"
    )

    assert result["artifact_type"] == "provider_candidate_artifact"
    assert result["source_family"] == "provider_candidates"
    assert result["source_status"] == "candidate_only"
    assert result["stock_code"] == "600406"
    assert result["artifact_type"] != "verified_fact"


def test_official_disclosure_candidates_path_classification():
    result = classify_artifact_path(
        "output/official_disclosures/20260529T000000Z/300475/official_disclosure_candidate_payload.json"
    )

    assert result["artifact_type"] == "official_disclosure_candidate_artifact"
    assert result["source_family"] == "official_disclosures"
    assert result["source_status"] == "candidate_only"
    assert result["review_status"] == "review_required"


def test_candidate_source_bridge_path_classification():
    result = classify_artifact_path(
        "output/candidate_source_bridges/20260529T000000Z/600406/candidate_source_bridge_review.json"
    )

    assert result["artifact_type"] == "candidate_source_bridge_artifact"
    assert result["source_family"] == "source_index"
    assert "merge" in result["caveats"][0]


def test_bridge_aware_review_decisions_path_classification():
    result = classify_artifact_path(
        "output/candidate_review_decisions_bridge_reviews/20260529T000000Z/600406/"
        "candidate_review_decisions_bridge_review.json"
    )

    assert result["artifact_type"] == "bridge_aware_review_decision_artifact"
    assert result["source_family"] == "workflow_signal"
    assert result["source_status"] == "review_required"


def test_accepted_manifest_path_classification_is_not_verified_fact():
    result = classify_artifact_path("output/research_reports/accepted_manifest.json")

    assert result["artifact_type"] == "accepted_manifest"
    assert result["source_family"] == "accepted_manifest"
    assert result["artifact_type"] != "verified_fact"
    assert "fact verification" in result["caveats"][0]


def test_research_report_artifact_path_classification_is_not_verified_fact():
    result = classify_artifact_path(
        "output/research_reports/20260529T000000Z/600406/fundamental_research_report_v1.json"
    )

    assert result["artifact_type"] == "report_artifact_state"
    assert result["source_family"] == "research_report_v1"
    assert result["artifact_type"] not in {"verified_fact", "accepted_report_fact"}
    assert "not a new fact source" in result["caveats"][0]


def test_unknown_path_is_ignored():
    result = classify_artifact_path("docs/random_note.md")

    assert result["artifact_type"] == "ignored"
    assert result["source_status"] == "ignored"
    assert should_ignore_artifact_path("docs/random_note.md") is True


@pytest.mark.parametrize(
    "path",
    [
        ".env",
        "config/.env.local",
        "config/token.txt",
        "secrets/credential.json",
        "keys/provider.key",
        "config/mcp/server.json",
        "output/TUSHARE_TOKEN.json",
        "output/api_key.txt",
        "output/access_token.txt",
        "https://example.com/output/fundamental_600406.json",
        "output/../.env",
    ],
)
def test_secret_env_token_credential_and_mcp_paths_are_rejected_or_ignored(path):
    result = classify_artifact_path(path)

    assert result["artifact_type"] == "ignored"
    assert result["source_status"] == "ignored"
    assert should_ignore_artifact_path(path) is True
    with pytest.raises(ValueError, match="unsafe artifact_path"):
        validate_artifact_path_safety(path)


@pytest.mark.parametrize(
    "path",
    [
        "C:/Users/Admin/.tushare_token",
        "C:/Users/Admin/.aws/credentials",
        "/home/user/.env",
    ],
)
def test_absolute_secret_path_is_rejected(path):
    result = classify_artifact_path(path)

    assert result["artifact_type"] == "ignored"
    assert result["artifact_path"] == "<ignored_sensitive_path>"
    with pytest.raises(ValueError, match="unsafe artifact_path"):
        validate_artifact_path_safety(path)


def test_mojibake_unrelated_path_is_ignored():
    mojibake_path = "HTML\u00e2\u0095\u00a9\u00e2\u0095\u0093.md"
    result = classify_artifact_path(mojibake_path)

    assert result["artifact_type"] == "ignored"
    assert result["source_status"] == "ignored"
    assert should_ignore_artifact_path(mojibake_path) is True


@pytest.mark.parametrize(
    "marker",
    [
        "verified_fact",
        "auto_verified",
        "fixture_promotion",
        "accepted_manifest_update",
        "provider_primary_switch",
        "research_report_v1_update",
        "target_price",
    ],
)
def test_validator_rejects_forbidden_downstream_markers(marker):
    row = _valid_row(caveats=[marker])

    with pytest.raises(ValueError, match="safety violation"):
        validate_artifact_row(row)


@pytest.mark.parametrize("marker", ["target_price", "trading_signal"])
def test_validator_rejects_forbidden_markers_in_artifact_path_before_masking(marker):
    artifact_path = (
        f"output/official_disclosures/20260529T000000Z/600406/{marker}_candidate.json"
    )
    row = _valid_row(artifact_path=artifact_path)

    classification = classify_artifact_path(artifact_path)
    assert classification["artifact_type"] == "official_disclosure_candidate_artifact"
    assert classification["artifact_type"] != "verified_fact"
    assert validate_artifact_path_safety(artifact_path) == artifact_path

    with pytest.raises(ValueError) as excinfo:
        validate_artifact_row(row)

    message = str(excinfo.value)
    assert "safety violation" in message
    assert artifact_path not in message
    assert row["sha256"] not in message


def test_classifier_does_not_use_file_io(monkeypatch):
    def fail_open(*args, **kwargs):
        raise AssertionError("classifier must not open files")

    monkeypatch.setattr(builtins, "open", fail_open)

    result = classify_artifact_path(
        "output/official_disclosures/20260529T000000Z/600406/business_table_candidate.json"
    )

    assert result["artifact_type"] == "official_disclosure_candidate_artifact"


def _valid_manifest_entry(**overrides):
    params = {
        "stock_code": "600406",
        "company_name": "NARI Technology",
        "artifact_path": "output/research_reports/20260529T000000Z/600406/fundamental_research_report_v1.json",
        "artifact_kind": "research_report_v1",
        "artifact_format": "json",
        "accepted_status": "accepted",
        "freshness_status": "current",
        "hash_status": "not_checked",
        "source_status": "available",
        "caveats": ["Manifest locator state only."],
        "not_for_trading_advice": True,
    }
    params.update(overrides)
    return build_manifest_entry_row(**params)


def test_ticker_inventory_schema_constants_and_validation():
    inventory = build_ticker_local_artifact_inventory(
        stock_code="600406",
        company_name="NARI Technology",
        explicit_artifact_paths=[
            "output/ground_truth_candidates/20260529T000000Z/600406/fact_candidates.json"
        ],
    )

    assert inventory["schema_version"] == TICKER_LOCAL_ARTIFACT_INVENTORY_SCHEMA_VERSION
    assert inventory["identity_resolution_status"] == "resolved"
    assert inventory["not_for_trading_advice"] is True
    assert validate_ticker_local_artifact_inventory(inventory) == inventory


def test_ticker_inventory_from_valid_explicit_artifact_paths():
    inventory = build_ticker_local_artifact_inventory(
        stock_code="600406",
        company_name="NARI Technology",
        explicit_artifact_paths=[
            "output/ground_truth_candidates/20260529T000000Z/600406/fact_candidates.json",
            "docs/random_note.md",
        ],
    )

    assert len(inventory["available_data_artifacts"]) == 1
    assert inventory["available_data_artifacts"][0]["stock_code"] == "600406"
    assert inventory["available_data_artifacts"][0]["source_status"] == "candidate_only"
    assert len(inventory["ignored_artifacts"]) == 1
    assert inventory["ignored_artifacts"][0]["source_status"] == "ignored"
    assert "verified_fact" not in str(inventory)
    assert "evidence_fact" not in str(inventory)


def test_ticker_inventory_from_valid_manifest_locator_payload():
    entry = _valid_manifest_entry()
    payload = build_manifest_locator_payload(
        manifest_path="output/research_reports/accepted_manifest.json",
        manifest_exists_status="not_checked",
        manifest_schema_status="valid",
        manifest_entry_count=1,
        matched_entries=[entry],
        stock_code="600406",
        company_name="NARI Technology",
        report_artifact_refs=[entry["artifact_path"]],
        freshness_status="current",
        lineage_refs=["caller:synthetic_manifest_payload"],
        caveats=["Validated manifest locator payload only."],
    )

    inventory = build_ticker_local_artifact_inventory(
        stock_code="600406",
        company_name="NARI Technology",
        manifest_locator_payload=payload,
    )

    assert inventory["identity_resolution_status"] == "resolved"
    assert len(inventory["available_data_artifacts"]) == 1
    assert inventory["available_data_artifacts"][0]["source_family"] == "research_report_v1"
    assert "ticker_inventory:manifest_locator_payload.v1" in inventory["lineage_refs"]


def test_ticker_inventory_from_valid_manifest_entries_uses_local_import_adapter():
    entry = _valid_manifest_entry(
        artifact_path="output/research_reports/20260529T000000Z/600406/fundamental_research_report_v1.md",
        artifact_format="markdown",
    )

    inventory = build_ticker_local_artifact_inventory(
        stock_code="600406",
        company_name="NARI Technology",
        manifest_entries=[entry],
    )

    assert inventory["identity_resolution_status"] == "resolved"
    assert len(inventory["available_data_artifacts"]) == 1
    assert "ticker_inventory:manifest_entries" in inventory["lineage_refs"]


def test_ticker_inventory_from_valid_prebuilt_artifact_rows():
    row = _valid_row(company_name="NARI Technology")

    inventory = build_ticker_local_artifact_inventory(
        stock_code="600406",
        company_name="NARI Technology",
        artifact_rows=[row],
    )

    assert inventory["identity_resolution_status"] == "resolved"
    assert inventory["available_data_artifacts"][0]["artifact_id"] == row["artifact_id"]
    assert inventory["artifact_rows"][0] is not row


def test_ticker_inventory_duplicate_artifact_id_and_path_are_conflicts():
    path = "output/ground_truth_candidates/20260529T000000Z/600406/fact_candidates.json"
    row_a = _valid_row(artifact_id="duplicate_artifact", artifact_path=path)
    row_b = _valid_row(artifact_id="duplicate_artifact", artifact_path=path, company_name="NARI Technology")

    inventory = build_ticker_local_artifact_inventory(
        stock_code="600406",
        company_name="NARI Technology",
        artifact_rows=[row_a, row_b],
    )

    assert inventory["identity_resolution_status"] == "conflict_requires_review"
    assert len(inventory["conflict_artifacts"]) == 2
    caveats = " ".join(caveat for row in inventory["conflict_artifacts"] for caveat in row["caveats"])
    assert "Duplicate artifact_id" in caveats
    assert "Duplicate artifact_path" in caveats


def test_ticker_inventory_mismatched_ticker_is_conflict_not_fallback():
    row = _valid_row(
        stock_code="300475",
        artifact_path="output/official_disclosures/20260529T000000Z/300475/business_candidate.json",
        artifact_type="official_disclosure_candidate_artifact",
        source_family="official_disclosures",
        source_status="candidate_only",
        review_status="review_required",
    )

    inventory = build_ticker_local_artifact_inventory(stock_code="600406", artifact_rows=[row])

    assert inventory["identity_resolution_status"] == "conflict_requires_review"
    assert inventory["available_data_artifacts"] == []
    assert inventory["conflict_artifacts"][0]["stock_code"] == "300475"
    assert any("fallback" in caveat for caveat in inventory["conflict_artifacts"][0]["caveats"])


def test_ticker_inventory_company_conflict_requires_review():
    row = _valid_row(company_name="Different Company")

    inventory = build_ticker_local_artifact_inventory(
        stock_code="600406",
        company_name="NARI Technology",
        artifact_rows=[row],
    )

    assert inventory["identity_resolution_status"] == "conflict_requires_review"
    assert len(inventory["conflict_artifacts"]) == 1
    assert any("Company-name" in caveat for caveat in inventory["conflict_artifacts"][0]["caveats"])


def test_ticker_inventory_unsafe_artifact_path_is_ignored():
    inventory = build_ticker_local_artifact_inventory(
        stock_code="600406",
        explicit_artifact_paths=["config/token.txt"],
    )

    assert inventory["identity_resolution_status"] == "not_found"
    assert inventory["available_data_artifacts"] == []
    assert len(inventory["ignored_artifacts"]) == 1
    assert inventory["ignored_artifacts"][0]["artifact_path"] == "<ignored_sensitive_path>"


def test_ticker_inventory_rejects_invalid_manifest_payload():
    with pytest.raises(ValueError, match="manifest locator payload"):
        build_ticker_local_artifact_inventory(
            stock_code="600406",
            manifest_locator_payload={"schema_version": "raw_real_manifest_dict"},
        )


def test_ticker_inventory_rejects_invalid_manifest_entry():
    with pytest.raises(ValueError, match="manifest entry row"):
        build_ticker_local_artifact_inventory(
            stock_code="600406",
            manifest_entries=[{"schema_version": "bad"}],
        )


def test_ticker_inventory_rejects_invalid_artifact_row():
    with pytest.raises(ValueError, match="artifact row"):
        build_ticker_local_artifact_inventory(
            stock_code="600406",
            artifact_rows=[{"schema_version": LOCAL_ARTIFACT_INDEX_ROW_SCHEMA_VERSION}],
        )


def test_ticker_inventory_rejects_raw_output_scan_result_fields():
    row = _valid_row()
    row["path_exists"] = True

    with pytest.raises(ValueError, match="unsupported artifact row fields"):
        build_ticker_local_artifact_inventory(stock_code="600406", artifact_rows=[row])


def test_ticker_inventory_rejects_report_artifact_content_fields():
    row = _valid_row()
    row["sections"] = [{"heading": "business overview", "text": "caller supplied parsed report content"}]

    with pytest.raises(ValueError, match="unsupported artifact row fields"):
        build_ticker_local_artifact_inventory(stock_code="600406", artifact_rows=[row])


def test_ticker_inventory_all_artifacts_ignored_and_no_artifacts_available():
    ignored_inventory = build_ticker_local_artifact_inventory(
        stock_code="600406",
        explicit_artifact_paths=["docs/random_note.md"],
    )
    empty_inventory = build_ticker_local_artifact_inventory(stock_code="600406")

    assert ignored_inventory["identity_resolution_status"] == "not_found"
    assert len(ignored_inventory["ignored_artifacts"]) == 1
    assert ignored_inventory["available_data_artifacts"] == []
    assert empty_inventory["identity_resolution_status"] == "not_found"
    assert empty_inventory["artifact_rows"] == []
    assert any("No available artifacts" in caveat for caveat in empty_inventory["caveats"])


def test_ticker_inventory_unknown_ticker_no_accepted_sample_fallback():
    payload = build_manifest_locator_payload(
        manifest_path="output/research_reports/accepted_manifest.json",
        manifest_exists_status="exists",
        manifest_schema_status="valid",
        manifest_entry_count=0,
        matched_entries=[],
        unmatched_reason="data_collection_required",
        stock_code="999999",
        company_name="Unknown",
        report_artifact_refs=[],
        freshness_status="unknown",
        caveats=["Unknown ticker requires explicit collection."],
    )

    inventory = build_ticker_local_artifact_inventory(
        stock_code="999999",
        company_name="Unknown",
        manifest_locator_payload=payload,
    )

    assert inventory["identity_resolution_status"] == "not_found"
    assert inventory["artifact_rows"] == []
    assert "600406" not in str(inventory)
    assert "002371" not in str(inventory)
    assert "002050" not in str(inventory)


def test_ticker_inventory_rejects_not_for_trading_advice_false():
    with pytest.raises(ValueError, match="not_for_trading_advice"):
        build_ticker_local_artifact_inventory(stock_code="600406", not_for_trading_advice=False)


def test_ticker_inventory_rejects_forbidden_markers():
    row = _valid_row(caveats=["hypothesis"])

    with pytest.raises(ValueError, match="safety violation"):
        build_ticker_local_artifact_inventory(stock_code="600406", artifact_rows=[row])


def test_ticker_inventory_does_not_scan_read_or_write(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("ticker inventory builder must not perform filesystem IO or scans")

    monkeypatch.setattr(glob, "glob", fail)
    monkeypatch.setattr(Path, "glob", fail)
    monkeypatch.setattr(Path, "rglob", fail)
    monkeypatch.setattr(os, "walk", fail)
    monkeypatch.setattr(Path, "exists", fail)
    monkeypatch.setattr(Path, "stat", fail)
    monkeypatch.setattr(Path, "read_text", fail)
    monkeypatch.setattr(Path, "read_bytes", fail)
    monkeypatch.setattr(Path, "write_text", fail)
    monkeypatch.setattr(Path, "write_bytes", fail)
    monkeypatch.setattr(builtins, "open", fail)

    inventory = build_ticker_local_artifact_inventory(
        stock_code="600406",
        explicit_artifact_paths=[
            "output/official_disclosures/20260529T000000Z/600406/business_table_candidate.json"
        ],
    )

    assert len(inventory["available_data_artifacts"]) == 1


def test_ticker_inventory_does_not_mutate_inputs_or_share_outputs():
    entry = _valid_manifest_entry()
    payload = build_manifest_locator_payload(
        manifest_path="output/research_reports/accepted_manifest.json",
        manifest_exists_status="not_checked",
        manifest_schema_status="valid",
        manifest_entry_count=1,
        matched_entries=[entry],
        stock_code="600406",
        company_name="NARI Technology",
        report_artifact_refs=[entry["artifact_path"]],
        freshness_status="current",
        lineage_refs=["caller:manifest"],
        caveats=["Validated manifest locator payload only."],
    )
    row = _valid_row(company_name="NARI Technology")
    paths = ["output/ground_truth_candidates/20260529T000000Z/600406/fact_candidates.json"]

    payload_snapshot = deepcopy(payload)
    entry_snapshot = deepcopy(entry)
    row_snapshot = deepcopy(row)
    paths_snapshot = deepcopy(paths)

    inventory = build_ticker_local_artifact_inventory(
        stock_code="600406",
        company_name="NARI Technology",
        explicit_artifact_paths=paths,
        manifest_locator_payload=payload,
        manifest_entries=[entry],
        artifact_rows=[row],
    )

    assert payload == payload_snapshot
    assert entry == entry_snapshot
    assert row == row_snapshot
    assert paths == paths_snapshot

    inventory["artifact_rows"][0]["caveats"].append("caller mutation")
    second_inventory = build_ticker_local_artifact_inventory(
        stock_code="600406",
        company_name="NARI Technology",
        explicit_artifact_paths=paths,
        manifest_locator_payload=payload,
        manifest_entries=[entry],
        artifact_rows=[row],
    )

    assert "caller mutation" not in second_inventory["artifact_rows"][0]["caveats"]


def test_ticker_inventory_output_remains_artifact_state_not_fact_or_report_payload():
    inventory = build_ticker_local_artifact_inventory(
        stock_code="600406",
        explicit_artifact_paths=[
            "output/research_reports/20260529T000000Z/600406/fundamental_research_report_v1.html"
        ],
    )
    serialized = str(inventory).lower()

    assert inventory["available_data_artifacts"][0]["artifact_type"] == "report_artifact_state"
    assert "verified_fact" not in serialized
    assert "evidence_fact" not in serialized
    assert "report_fact" not in serialized
    assert "hypothesis" not in serialized
    assert "research_report_v1_section" not in serialized
