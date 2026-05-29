# -*- coding: utf-8 -*-

import builtins

import pytest

from src.fundamental_skill.research_planning.local_artifact_index import (
    ARTIFACT_TYPES,
    FRESHNESS_STATUSES,
    LOCAL_ARTIFACT_INDEX_ROW_SCHEMA_VERSION,
    REVIEW_STATUSES,
    SOURCE_FAMILIES,
    SOURCE_STATUSES,
    build_artifact_row,
    classify_artifact_path,
    should_ignore_artifact_path,
    validate_artifact_path_safety,
    validate_artifact_row,
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
