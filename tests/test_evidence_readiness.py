# -*- coding: utf-8 -*-

import builtins
from copy import deepcopy
import glob
import os
from pathlib import Path
import socket

import pytest

from src.fundamental_skill.research_planning.evidence_readiness import (
    CRITICAL_FINANCIAL_ARTIFACT_CATEGORY,
    DETERMINISTIC_EVIDENCE_INVENTORY_SCHEMA_VERSION,
    OFFICIAL_BUSINESS_EVIDENCE_CATEGORY,
    READINESS_SKELETON_SCHEMA_VERSION,
    build_deterministic_evidence_inventory,
    build_readiness_skeleton,
    validate_deterministic_evidence_inventory,
    validate_readiness_skeleton,
)
from src.fundamental_skill.research_planning.local_artifact_index import (
    build_artifact_row,
    build_ticker_local_artifact_inventory,
)


def _row(
    *,
    artifact_id: str,
    artifact_type: str,
    source_family: str,
    source_status: str = "available",
    review_status: str = "unknown",
    artifact_path: str | None = None,
) -> dict:
    return build_artifact_row(
        artifact_id=artifact_id,
        artifact_type=artifact_type,
        artifact_path=artifact_path or f"output/synthetic/20260530/600406/{artifact_id}.json",
        source_family=source_family,
        stock_code="600406",
        company_name="NARI Technology",
        sha256="0" * 64,
        file_size=100,
        source_status=source_status,
        review_status=review_status,
        freshness_status="unknown",
        caveats=["Artifact state only."],
        lineage_refs=[f"test:{artifact_id}"],
        not_for_trading_advice=True,
    )


def _official_row(**overrides) -> dict:
    params = {
        "artifact_id": "official_business",
        "artifact_type": "official_disclosure_facts_artifact",
        "source_family": "official_disclosures",
        "artifact_path": "output/official_disclosures/20260530T000000Z/600406/business_facts.json",
    }
    params.update(overrides)
    return _row(**params)


def _financial_row(**overrides) -> dict:
    params = {
        "artifact_id": "critical_financial",
        "artifact_type": "normalized_fundamentals_artifact",
        "source_family": "normalized_fundamentals",
        "artifact_path": "output/fundamental_600406.json",
    }
    params.update(overrides)
    return _row(**params)


def _ignored_row(**overrides) -> dict:
    params = {
        "artifact_id": "ignored_artifact",
        "artifact_type": "ignored",
        "source_family": "ignored",
        "source_status": "ignored",
        "review_status": "review_required",
        "artifact_path": "<ignored_path>",
    }
    params.update(overrides)
    return _row(**params)


def _inventory(rows: list[dict], *, identity_status: str | None = None, caveats: list[str] | None = None) -> dict:
    inventory = build_ticker_local_artifact_inventory(
        stock_code="600406",
        company_name="NARI Technology",
        artifact_rows=rows,
    )
    if identity_status is not None:
        inventory["identity_resolution_status"] = identity_status
    if caveats:
        inventory["caveats"] = list(inventory["caveats"]) + list(caveats)
    return inventory


def _accepted_inventory() -> dict:
    return _inventory([_official_row(), _financial_row()])


def _collect_keys(payload) -> set[str]:
    keys: set[str] = set()

    def visit(value) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                keys.add(str(key))
                visit(child)
            return
        if isinstance(value, list):
            for child in value:
                visit(child)

    visit(payload)
    return keys


def test_accepted_positive_path_builds_inventory_and_skeleton():
    skeleton = build_readiness_skeleton(ticker_local_artifact_inventory=_accepted_inventory())

    assert skeleton["schema_version"] == READINESS_SKELETON_SCHEMA_VERSION
    assert skeleton["readiness_level"] == "accepted_report_ready"
    assert skeleton["can_generate_accepted_report"] is True
    assert skeleton["can_generate_experimental_report"] is False
    assert skeleton["readiness_evidence_categories"][OFFICIAL_BUSINESS_EVIDENCE_CATEGORY]["formal_ready"] is True
    assert skeleton["readiness_evidence_categories"][CRITICAL_FINANCIAL_ARTIFACT_CATEGORY]["formal_ready"] is True
    assert validate_readiness_skeleton(skeleton) == skeleton


def test_experimental_positive_path_requires_evidence_no_conflict_and_resolved_identity():
    review_financial = _financial_row(
        artifact_id="critical_financial_review",
        source_status="review_required",
        review_status="review_required",
        artifact_path="output/fundamental_600406_review.json",
    )
    inventory = _inventory([_official_row(), _financial_row(), review_financial])

    skeleton = build_readiness_skeleton(ticker_local_artifact_inventory=inventory)

    assert skeleton["readiness_level"] == "experimental_report_ready"
    assert skeleton["can_generate_accepted_report"] is False
    assert skeleton["can_generate_experimental_report"] is True
    critical = skeleton["readiness_evidence_categories"][CRITICAL_FINANCIAL_ARTIFACT_CATEGORY]
    assert "critical_financial_review" in critical["blocked_artifact_ids"]


def test_conflict_plus_good_artifacts_sets_both_flags_false():
    conflict_row = _financial_row(
        artifact_id="critical_conflict",
        source_status="conflict_open",
        review_status="conflict_open",
        artifact_path="output/fundamental_600406_conflict.json",
    )
    inventory = _inventory([_official_row(), _financial_row(), conflict_row])

    skeleton = build_readiness_skeleton(ticker_local_artifact_inventory=inventory)

    assert skeleton["readiness_level"] == "evidence_conflict_review_required"
    assert skeleton["can_generate_accepted_report"] is False
    assert skeleton["can_generate_experimental_report"] is False


@pytest.mark.parametrize("identity_status", ["ambiguous", "not_found", "conflict_requires_review", "blocked"])
def test_identity_non_resolved_sets_both_flags_false(identity_status):
    skeleton = build_readiness_skeleton(
        ticker_local_artifact_inventory=_inventory(
            [_official_row(), _financial_row()],
            identity_status=identity_status,
        )
    )

    assert skeleton["can_generate_accepted_report"] is False
    assert skeleton["can_generate_experimental_report"] is False


def test_missing_official_business_evidence_sets_both_flags_false():
    skeleton = build_readiness_skeleton(ticker_local_artifact_inventory=_inventory([_financial_row()]))

    assert skeleton["readiness_level"] == "data_collection_required"
    assert skeleton["can_generate_accepted_report"] is False
    assert skeleton["can_generate_experimental_report"] is False


def test_missing_critical_financial_artifacts_sets_both_flags_false():
    skeleton = build_readiness_skeleton(ticker_local_artifact_inventory=_inventory([_official_row()]))

    assert skeleton["readiness_level"] == "data_collection_required"
    assert skeleton["can_generate_accepted_report"] is False
    assert skeleton["can_generate_experimental_report"] is False


def test_candidate_only_only_sets_both_flags_false():
    inventory = _inventory(
        [
            _official_row(
                artifact_id="official_candidate",
                artifact_type="official_disclosure_candidate_artifact",
                source_status="candidate_only",
                review_status="review_required",
                artifact_path="output/official_disclosures/20260530T000000Z/600406/business_candidate.json",
            )
        ]
    )

    skeleton = build_readiness_skeleton(ticker_local_artifact_inventory=inventory)

    assert skeleton["can_generate_accepted_report"] is False
    assert skeleton["can_generate_experimental_report"] is False


def test_review_required_only_sets_both_flags_false():
    inventory = _inventory(
        [
            _financial_row(
                source_status="review_required",
                review_status="review_required",
                artifact_path="output/fundamental_600406_review.json",
            )
        ]
    )

    skeleton = build_readiness_skeleton(ticker_local_artifact_inventory=inventory)

    assert skeleton["can_generate_accepted_report"] is False
    assert skeleton["can_generate_experimental_report"] is False


def test_only_ignored_with_safety_violation_is_blocked():
    inventory = _inventory(
        [_ignored_row()],
        identity_status="blocked",
        caveats=["Safety violation blocked readiness."],
    )

    skeleton = build_readiness_skeleton(ticker_local_artifact_inventory=inventory)

    assert skeleton["readiness_level"] == "blocked"
    assert skeleton["can_generate_accepted_report"] is False
    assert skeleton["can_generate_experimental_report"] is False


def test_only_ignored_without_safety_violation_requires_data_collection():
    skeleton = build_readiness_skeleton(ticker_local_artifact_inventory=_inventory([_ignored_row()]))

    assert skeleton["readiness_level"] == "data_collection_required"
    assert skeleton["can_generate_accepted_report"] is False
    assert skeleton["can_generate_experimental_report"] is False


def test_not_for_trading_advice_false_is_rejected():
    with pytest.raises(ValueError, match="not_for_trading_advice"):
        build_deterministic_evidence_inventory(
            ticker_local_artifact_inventory=_accepted_inventory(),
            not_for_trading_advice=False,
        )

    skeleton = build_readiness_skeleton(ticker_local_artifact_inventory=_accepted_inventory())
    skeleton["not_for_trading_advice"] = False
    with pytest.raises(ValueError, match="not_for_trading_advice"):
        validate_readiness_skeleton(skeleton)


def test_forbidden_markers_are_rejected():
    inventory = _accepted_inventory()
    inventory["caveats"].append("target_price should never appear")

    with pytest.raises(ValueError, match="safety violation|forbidden"):
        build_deterministic_evidence_inventory(ticker_local_artifact_inventory=inventory)


def test_output_contains_no_report_section_recommendation_or_trading_keys():
    skeleton = build_readiness_skeleton(ticker_local_artifact_inventory=_accepted_inventory())

    forbidden = {
        "report_section",
        "recommendation",
        "target_price",
        "price_target",
        "trading_advice",
        "trading_signal",
        "research_report_v1_section",
        "research_report_v1_integration_permission",
    }
    assert forbidden.isdisjoint(_collect_keys(skeleton))


def test_builders_do_not_use_file_io_provider_or_network(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("evidence readiness must not perform IO, provider calls, or network access")

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
    monkeypatch.setattr(socket, "create_connection", fail)
    monkeypatch.setattr(socket, "socket", fail)

    skeleton = build_readiness_skeleton(ticker_local_artifact_inventory=_accepted_inventory())

    assert skeleton["readiness_level"] == "accepted_report_ready"


def test_builders_do_not_mutate_inputs():
    inventory = _accepted_inventory()
    snapshot = deepcopy(inventory)

    evidence_inventory = build_deterministic_evidence_inventory(ticker_local_artifact_inventory=inventory)
    skeleton = build_readiness_skeleton(deterministic_evidence_inventory=evidence_inventory)

    assert inventory == snapshot
    assert skeleton["stock_code"] == "600406"


def test_validators_return_defensive_copies():
    evidence_inventory = build_deterministic_evidence_inventory(
        ticker_local_artifact_inventory=_accepted_inventory()
    )
    validated = validate_deterministic_evidence_inventory(evidence_inventory)
    validated["caveats"].append("caller mutation")

    assert "caller mutation" not in evidence_inventory["caveats"]

    skeleton = build_readiness_skeleton(deterministic_evidence_inventory=evidence_inventory)
    validated_skeleton = validate_readiness_skeleton(skeleton)
    validated_skeleton["lineage_refs"].append("caller mutation")

    assert "caller mutation" not in skeleton["lineage_refs"]


def test_invalid_schema_version_is_rejected():
    evidence_inventory = build_deterministic_evidence_inventory(
        ticker_local_artifact_inventory=_accepted_inventory()
    )
    evidence_inventory["schema_version"] = "bad.v1"

    with pytest.raises(ValueError, match=DETERMINISTIC_EVIDENCE_INVENTORY_SCHEMA_VERSION):
        validate_deterministic_evidence_inventory(evidence_inventory)


def test_invalid_readiness_flags_are_rejected():
    skeleton = build_readiness_skeleton(ticker_local_artifact_inventory=_accepted_inventory())
    skeleton["readiness_level"] = "data_collection_required"

    with pytest.raises(ValueError, match="data_collection_required"):
        validate_readiness_skeleton(skeleton)


def test_validator_rejects_accepted_ready_with_experimental_flag_true():
    skeleton = build_readiness_skeleton(ticker_local_artifact_inventory=_accepted_inventory())
    assert skeleton["readiness_level"] == "accepted_report_ready"
    assert skeleton["can_generate_experimental_report"] is False

    skeleton["can_generate_experimental_report"] = True

    with pytest.raises(ValueError, match="can_generate_experimental_report|experimental"):
        validate_readiness_skeleton(skeleton)


def test_validator_rejects_accepted_ready_with_critical_blocker():
    review_financial = _financial_row(
        artifact_id="critical_financial_review",
        source_status="review_required",
        review_status="review_required",
        artifact_path="output/fundamental_600406_review.json",
    )
    skeleton = build_readiness_skeleton(
        ticker_local_artifact_inventory=_inventory([_official_row(), _financial_row(), review_financial])
    )
    skeleton["readiness_level"] = "accepted_report_ready"
    skeleton["can_generate_accepted_report"] = True
    skeleton["can_generate_experimental_report"] = False

    with pytest.raises(ValueError, match="critical readiness blockers"):
        validate_readiness_skeleton(skeleton)


def test_validator_rejects_experimental_ready_without_available_artifacts():
    official_candidate = _official_row(
        artifact_id="official_candidate",
        artifact_type="official_disclosure_candidate_artifact",
        source_status="candidate_only",
        review_status="review_required",
        artifact_path="output/official_disclosures/20260530T000000Z/600406/business_candidate.json",
    )
    financial_candidate = _financial_row(
        artifact_id="financial_candidate",
        source_status="candidate_only",
        review_status="not_reviewed",
        artifact_path="output/provider_fundamentals/synthetic_600406_candidate.json",
    )
    skeleton = build_readiness_skeleton(
        ticker_local_artifact_inventory=_inventory([official_candidate, financial_candidate])
    )
    skeleton["readiness_level"] = "experimental_report_ready"
    skeleton["can_generate_experimental_report"] = True

    with pytest.raises(ValueError, match="available non-ignored"):
        validate_readiness_skeleton(skeleton)


def test_readiness_flags_do_not_imply_report_generation():
    skeleton = build_readiness_skeleton(ticker_local_artifact_inventory=_accepted_inventory())

    assert skeleton["can_generate_accepted_report"] is True
    assert all("indicator" in caveat or "artifact" in caveat.lower() for caveat in skeleton["caveats"])
    assert "report_generation_permission" not in _collect_keys(skeleton)
