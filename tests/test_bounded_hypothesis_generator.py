# -*- coding: utf-8 -*-

from copy import deepcopy
import builtins

import pytest

import src.fundamental_skill.research_planning.bounded_hypothesis_generator as bhg
from src.fundamental_skill.research_planning.bounded_hypothesis_generator import (
    BOUNDED_HYPOTHESIS_PAYLOAD_SCHEMA_VERSION,
    BOUNDED_HYPOTHESIS_REQUEST_SCHEMA_VERSION,
    build_bounded_hypothesis_payload,
    validate_blocked_hypothesis_item,
    validate_bounded_hypothesis_item,
    validate_bounded_hypothesis_payload,
    validate_bounded_hypothesis_request,
)
from src.fundamental_skill.research_planning.evidence_readiness import (
    build_deterministic_evidence_inventory,
    build_readiness_skeleton,
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
    freshness_status: str = "current",
    stock_code: str = "600406",
    artifact_path: str | None = None,
) -> dict:
    return build_artifact_row(
        artifact_id=artifact_id,
        artifact_type=artifact_type,
        artifact_path=artifact_path or f"output/synthetic/20260530/{stock_code}/{artifact_id}.json",
        source_family=source_family,
        stock_code=stock_code,
        company_name="NARI Technology",
        sha256="0" * 64,
        file_size=100,
        source_status=source_status,
        review_status=review_status,
        freshness_status=freshness_status,
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


def _inventory(rows: list[dict], *, identity_status: str | None = None) -> dict:
    inventory = build_ticker_local_artifact_inventory(
        stock_code="600406",
        company_name="NARI Technology",
        artifact_rows=rows,
    )
    if identity_status is not None:
        inventory["identity_resolution_status"] = identity_status
    return inventory


def _phase3(
    rows: list[dict] | None = None,
    *,
    identity_status: str | None = None,
) -> tuple[dict, dict]:
    evidence_inventory = build_deterministic_evidence_inventory(
        ticker_local_artifact_inventory=_inventory(
            rows or [_official_row(), _financial_row()],
            identity_status=identity_status,
        )
    )
    skeleton = build_readiness_skeleton(deterministic_evidence_inventory=evidence_inventory)
    return evidence_inventory, skeleton


def _evidence_ref(artifact_id: str = "official_business", *, stock_code: str = "600406") -> str:
    return f"deterministic_evidence_inventory.v1:evidence_inventory:{stock_code}:{artifact_id}"


def _state_ref(
    artifact_id: str = "official_business",
    state: str = "available",
    *,
    stock_code: str = "600406",
) -> str:
    return f"readiness_skeleton.v1:evidence_inventory:{stock_code}:{artifact_id}:{state}"


def _hypothesis(**overrides) -> dict:
    payload = {
        "hypothesis_id": "industry-001",
        "hypothesis_type": "industry",
        "hypothesis_text": "Company may have exposure to grid automation demand.",
        "evidence_refs": [_evidence_ref()],
        "evidence_state_refs": [_state_ref()],
        "confidence": "low",
        "caveats": ["Planning only; artifact state only."],
        "required_follow_up_data": ["Collect segment disclosure."],
        "allowed_downstream_use": "planning_only",
        "not_for_trading_advice": True,
    }
    payload.update(overrides)
    return payload


def _blocked_hypothesis(**overrides) -> dict:
    payload = {
        "hypothesis_id": "blocked-001",
        "hypothesis_type": "data_gap",
        "hypothesis_text": "Critical financial evidence is missing.",
        "block_reason": "missing_required_evidence",
        "evidence_state_refs": [
            "deterministic_evidence_inventory.v1:missing_data_artifacts:critical_financial"
        ],
        "required_follow_up_data": ["Collect critical financial artifact state."],
        "caveats": ["Blocked planning item only."],
        "not_for_trading_advice": True,
    }
    payload.update(overrides)
    return payload


def _request(evidence_inventory: dict, skeleton: dict, **overrides) -> dict:
    payload = {
        "schema_version": BOUNDED_HYPOTHESIS_REQUEST_SCHEMA_VERSION,
        "stock_code": "600406",
        "company_name": "NARI Technology",
        "deterministic_evidence_inventory": evidence_inventory,
        "readiness_skeleton": skeleton,
        "not_for_trading_advice": True,
    }
    payload.update(overrides)
    return payload


def test_valid_bounded_industry_hypothesis_payload():
    evidence_inventory, skeleton = _phase3()

    payload = build_bounded_hypothesis_payload(
        deterministic_evidence_inventory=evidence_inventory,
        readiness_skeleton=skeleton,
        industry_hypotheses=[_hypothesis()],
        key_research_questions=["Which business segment evidence should be collected next?"],
        required_follow_up_data=["Collect segment disclosure."],
        caveats=["Phase 4 planning only; not fact verification."],
    )

    assert payload["schema_version"] == BOUNDED_HYPOTHESIS_PAYLOAD_SCHEMA_VERSION
    assert payload["source_readiness_level"] == skeleton["readiness_level"]
    assert payload["not_for_trading_advice"] is True


def test_valid_supply_chain_business_model_and_macro_hypotheses():
    evidence_inventory, skeleton = _phase3()
    supply_chain = _hypothesis(
        hypothesis_id="supply-001",
        hypothesis_type="supply_chain_position",
        hypothesis_text="Company may need upstream input and downstream customer mapping.",
    )
    business_model = _hypothesis(
        hypothesis_id="business-001",
        hypothesis_type="business_model",
        hypothesis_text="Company business mechanics require official artifact follow-up.",
    )
    macro = _hypothesis(
        hypothesis_id="macro-001",
        hypothesis_type="macro_factor",
        hypothesis_text="Macro factor exposure requires artifact-state follow-up.",
        transmission_path_summary=(
            "macro factor -> industry/business mechanism -> company artifact-state linkage"
        ),
    )

    payload = build_bounded_hypothesis_payload(
        deterministic_evidence_inventory=evidence_inventory,
        readiness_skeleton=skeleton,
        supply_chain_position_hypotheses=[supply_chain],
        business_model_hypotheses=[business_model],
        macro_factor_hypotheses=[macro],
    )

    assert payload["supply_chain_position_hypotheses"][0]["hypothesis_type"] == "supply_chain_position"
    assert payload["business_model_hypotheses"][0]["hypothesis_type"] == "business_model"
    assert payload["macro_factor_hypotheses"][0]["transmission_path_summary"]


def test_hypothesis_without_evidence_refs_is_rejected():
    with pytest.raises(ValueError, match="evidence_refs"):
        validate_bounded_hypothesis_item(
            _hypothesis(evidence_refs=[]),
            stock_code="600406",
            source_readiness_level="accepted_report_ready",
            identity_resolution_status="resolved",
        )


def test_hypothesis_rejects_missing_artifact_id_in_evidence_refs():
    evidence_inventory, skeleton = _phase3()

    with pytest.raises(ValueError, match="artifact_id|evidence_refs"):
        validate_bounded_hypothesis_item(
            _hypothesis(evidence_refs=[_evidence_ref("missing_artifact")]),
            stock_code="600406",
            source_readiness_level=skeleton["readiness_level"],
            identity_resolution_status=skeleton["identity_resolution_status"],
            deterministic_evidence_inventory=evidence_inventory,
            readiness_skeleton=skeleton,
        )


def test_hypothesis_rejects_missing_artifact_id_in_evidence_state_refs():
    evidence_inventory, skeleton = _phase3()

    with pytest.raises(ValueError, match="artifact_id|evidence_state_refs"):
        validate_bounded_hypothesis_item(
            _hypothesis(evidence_state_refs=[_state_ref("missing_artifact")]),
            stock_code="600406",
            source_readiness_level=skeleton["readiness_level"],
            identity_resolution_status=skeleton["identity_resolution_status"],
            deterministic_evidence_inventory=evidence_inventory,
            readiness_skeleton=skeleton,
        )


def test_blocked_readiness_rejects_downstream_hypothesis():
    evidence_inventory, skeleton = _phase3(identity_status="blocked")

    with pytest.raises(ValueError, match="identity|blocked"):
        build_bounded_hypothesis_payload(
            deterministic_evidence_inventory=evidence_inventory,
            readiness_skeleton=skeleton,
            industry_hypotheses=[
                _hypothesis(allowed_downstream_use="experimental_report_context_candidate")
            ],
        )


def test_blocked_readiness_rejects_blocked_until_review():
    with pytest.raises(ValueError, match="blocked|not_allowed_downstream|downstream"):
        validate_bounded_hypothesis_item(
            _hypothesis(allowed_downstream_use="blocked_until_review"),
            stock_code="600406",
            source_readiness_level="blocked",
            identity_resolution_status="resolved",
        )


def test_conflict_readiness_blocks_downstream_hypothesis():
    conflict_row = _financial_row(
        artifact_id="critical_conflict",
        source_status="conflict_open",
        review_status="conflict_open",
    )
    evidence_inventory, skeleton = _phase3([_official_row(), _financial_row(), conflict_row])

    with pytest.raises(ValueError, match="evidence_conflict|conflict"):
        build_bounded_hypothesis_payload(
            deterministic_evidence_inventory=evidence_inventory,
            readiness_skeleton=skeleton,
            industry_hypotheses=[
                _hypothesis(allowed_downstream_use="experimental_report_context_candidate")
            ],
        )


def test_mixed_available_candidate_only_evidence_ceiling():
    candidate = _row(
        artifact_id="candidate_business",
        artifact_type="official_disclosure_candidate_artifact",
        source_family="official_disclosures",
        source_status="candidate_only",
        freshness_status="unknown",
    )
    evidence_inventory, skeleton = _phase3([_official_row(), _financial_row(), candidate])
    hypothesis = _hypothesis(
        evidence_refs=[_evidence_ref(), _evidence_ref("candidate_business")],
        evidence_state_refs=[_state_ref(), _state_ref("candidate_business", "candidate_only")],
        allowed_downstream_use="experimental_report_context_candidate",
    )

    with pytest.raises(ValueError, match="candidate_only|review_required"):
        build_bounded_hypothesis_payload(
            deterministic_evidence_inventory=evidence_inventory,
            readiness_skeleton=skeleton,
            industry_hypotheses=[hypothesis],
        )

    hypothesis["allowed_downstream_use"] = "planning_only"
    assert build_bounded_hypothesis_payload(
        deterministic_evidence_inventory=evidence_inventory,
        readiness_skeleton=skeleton,
        industry_hypotheses=[hypothesis],
    )["industry_hypotheses"][0]["allowed_downstream_use"] == "planning_only"


def test_mixed_available_review_required_evidence_ceiling():
    review = _row(
        artifact_id="review_business",
        artifact_type="official_disclosure_candidate_artifact",
        source_family="official_disclosures",
        source_status="review_required",
        review_status="review_required",
        freshness_status="unknown",
    )
    evidence_inventory, skeleton = _phase3([_official_row(), _financial_row(), review])
    hypothesis = _hypothesis(
        evidence_refs=[_evidence_ref(), _evidence_ref("review_business")],
        evidence_state_refs=[_state_ref(), _state_ref("review_business", "review_required")],
        allowed_downstream_use="data_collection_prioritization",
    )

    with pytest.raises(ValueError, match="candidate_only|review_required"):
        build_bounded_hypothesis_payload(
            deterministic_evidence_inventory=evidence_inventory,
            readiness_skeleton=skeleton,
            industry_hypotheses=[hypothesis],
        )


def test_conflict_evidence_ref_must_be_blocked():
    conflict_hypothesis = _hypothesis(
        evidence_state_refs=[_state_ref("critical_conflict", "conflict_open")],
        allowed_downstream_use="planning_only",
    )

    with pytest.raises(ValueError, match="conflict_open"):
        validate_bounded_hypothesis_item(
            conflict_hypothesis,
            stock_code="600406",
            source_readiness_level="accepted_report_ready",
            identity_resolution_status="resolved",
        )

    conflict_hypothesis["allowed_downstream_use"] = "blocked_until_review"
    assert validate_bounded_hypothesis_item(
        conflict_hypothesis,
        stock_code="600406",
        source_readiness_level="accepted_report_ready",
        identity_resolution_status="resolved",
    )["allowed_downstream_use"] == "blocked_until_review"


def test_blocked_hypothesis_with_blocking_state_refs_is_valid():
    validated = validate_blocked_hypothesis_item(_blocked_hypothesis(), stock_code="600406")

    assert validated["evidence_state_refs"]
    assert "evidence_refs" not in validated


def test_blocked_hypothesis_allows_blocking_state_refs_without_artifact_refs():
    validated = validate_blocked_hypothesis_item(
        _blocked_hypothesis(evidence_state_refs=["readiness_skeleton.v1:readiness_level:blocked"]),
        stock_code="600406",
    )

    assert validated["evidence_state_refs"] == ["readiness_skeleton.v1:readiness_level:blocked"]
    assert "evidence_refs" not in validated


def test_blocked_hypothesis_with_empty_evidence_state_refs_is_rejected():
    with pytest.raises(ValueError, match="evidence_state_refs"):
        validate_blocked_hypothesis_item(
            _blocked_hypothesis(evidence_state_refs=[]),
            stock_code="600406",
        )


def test_phase4_v1_rejects_context_input():
    evidence_inventory, skeleton = _phase3()
    request = _request(
        evidence_inventory,
        skeleton,
        bounded_reasoning_context={"purpose": "not accepted"},
    )

    with pytest.raises(ValueError, match="bounded_reasoning_context|context"):
        validate_bounded_hypothesis_request(request)


def test_phase3_inputs_are_revalidated(monkeypatch):
    evidence_inventory, skeleton = _phase3()
    calls = {"inventory": 0, "skeleton": 0}
    original_inventory_validator = bhg.validate_deterministic_evidence_inventory
    original_skeleton_validator = bhg.validate_readiness_skeleton

    def counting_inventory_validator(payload):
        calls["inventory"] += 1
        return original_inventory_validator(payload)

    def counting_skeleton_validator(payload):
        calls["skeleton"] += 1
        return original_skeleton_validator(payload)

    monkeypatch.setattr(bhg, "validate_deterministic_evidence_inventory", counting_inventory_validator)
    monkeypatch.setattr(bhg, "validate_readiness_skeleton", counting_skeleton_validator)

    build_bounded_hypothesis_payload(
        deterministic_evidence_inventory=evidence_inventory,
        readiness_skeleton=skeleton,
    )

    assert calls["inventory"] >= 1
    assert calls["skeleton"] >= 1


def test_hand_mutated_phase3_payload_is_rejected():
    evidence_inventory, skeleton = _phase3()
    mutated = deepcopy(evidence_inventory)
    mutated["company_name"] = "Different Company"

    with pytest.raises(ValueError, match="Phase 3 inputs are inconsistent|company_name"):
        build_bounded_hypothesis_payload(
            deterministic_evidence_inventory=mutated,
            readiness_skeleton=skeleton,
        )


def test_source_readiness_level_equals_readiness_skeleton_level():
    evidence_inventory, skeleton = _phase3()
    payload = build_bounded_hypothesis_payload(
        deterministic_evidence_inventory=evidence_inventory,
        readiness_skeleton=skeleton,
    )
    payload["source_readiness_level"] = "blocked"

    with pytest.raises(ValueError, match="source_readiness_level"):
        validate_bounded_hypothesis_payload(
            payload,
            deterministic_evidence_inventory=evidence_inventory,
            readiness_skeleton=skeleton,
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("key_research_questions", ["What is the target price?"]),
        ("required_follow_up_data", ["portfolio weight payload"]),
    ],
)
def test_research_questions_and_follow_up_data_forbidden_markers_rejected(field, value):
    evidence_inventory, skeleton = _phase3()
    kwargs = {field: value}

    with pytest.raises(ValueError, match="trading|forbidden|target|portfolio"):
        build_bounded_hypothesis_payload(
            deterministic_evidence_inventory=evidence_inventory,
            readiness_skeleton=skeleton,
            **kwargs,
        )


def test_macro_hypothesis_without_transmission_path_rejected_or_blocked():
    macro = _hypothesis(
        hypothesis_id="macro-001",
        hypothesis_type="macro_factor",
        hypothesis_text="Macro exposure requires follow-up.",
    )

    with pytest.raises(ValueError, match="transmission_path"):
        validate_bounded_hypothesis_item(
            macro,
            stock_code="600406",
            source_readiness_level="accepted_report_ready",
            identity_resolution_status="resolved",
        )

    macro["allowed_downstream_use"] = "blocked_until_review"
    assert validate_bounded_hypothesis_item(
        macro,
        stock_code="600406",
        source_readiness_level="accepted_report_ready",
        identity_resolution_status="resolved",
    )["allowed_downstream_use"] == "blocked_until_review"


def test_cross_ticker_evidence_refs_rejected():
    with pytest.raises(ValueError, match="another stock_code|002371"):
        validate_bounded_hypothesis_item(
            _hypothesis(evidence_refs=[_evidence_ref(stock_code="002371")]),
            stock_code="600406",
            source_readiness_level="accepted_report_ready",
            identity_resolution_status="resolved",
        )


@pytest.mark.parametrize("bad_key", ["report_section", "template_payload", "dashboard_payload"])
def test_experimental_context_candidate_cannot_produce_report_or_dashboard_payload(bad_key):
    hypothesis = _hypothesis(allowed_downstream_use="experimental_report_context_candidate")
    hypothesis[bad_key] = "not allowed"

    with pytest.raises(ValueError, match="unsupported|prohibited"):
        validate_bounded_hypothesis_item(
            hypothesis,
            stock_code="600406",
            source_readiness_level="accepted_report_ready",
            identity_resolution_status="resolved",
        )


def test_output_contains_no_report_ready_or_trading_advice_text():
    evidence_inventory, skeleton = _phase3()

    with pytest.raises(ValueError, match="target|trading|recommendation"):
        build_bounded_hypothesis_payload(
            deterministic_evidence_inventory=evidence_inventory,
            readiness_skeleton=skeleton,
            caveats=["This is an investment recommendation with a target price."],
        )


def test_no_file_io_or_input_mutation_and_defensive_copies(monkeypatch):
    evidence_inventory, skeleton = _phase3()
    hypothesis = _hypothesis()
    evidence_before = deepcopy(evidence_inventory)
    skeleton_before = deepcopy(skeleton)
    hypothesis_before = deepcopy(hypothesis)

    def fail_open(*args, **kwargs):  # pragma: no cover - should never run
        raise AssertionError("file IO is not allowed")

    monkeypatch.setattr(builtins, "open", fail_open)
    payload = build_bounded_hypothesis_payload(
        deterministic_evidence_inventory=evidence_inventory,
        readiness_skeleton=skeleton,
        industry_hypotheses=[hypothesis],
    )

    assert evidence_inventory == evidence_before
    assert skeleton == skeleton_before
    assert hypothesis == hypothesis_before

    payload["industry_hypotheses"][0]["caveats"].append("changed")
    assert hypothesis == hypothesis_before

    validated = validate_bounded_hypothesis_item(
        hypothesis,
        stock_code="600406",
        source_readiness_level=skeleton["readiness_level"],
        identity_resolution_status=skeleton["identity_resolution_status"],
    )
    validated["caveats"].append("changed")
    assert hypothesis == hypothesis_before


def test_invalid_request_schema_version_rejected():
    evidence_inventory, skeleton = _phase3()
    request = _request(evidence_inventory, skeleton, schema_version="wrong.v1")

    with pytest.raises(ValueError, match="schema_version"):
        validate_bounded_hypothesis_request(request)


@pytest.mark.parametrize(
    "bad_use",
    ["accepted_report_fact", "verified_fact", "report_fact", "target_price"],
)
def test_invalid_downstream_use_and_report_fact_markers_rejected(bad_use):
    with pytest.raises(ValueError, match="verified|report|target|downstream"):
        validate_bounded_hypothesis_item(
            _hypothesis(allowed_downstream_use=bad_use),
            stock_code="600406",
            source_readiness_level="accepted_report_ready",
            identity_resolution_status="resolved",
        )


@pytest.mark.parametrize("marker", ["verified_fact", "accepted_report_fact", "report_fact"])
def test_verified_and_report_fact_text_markers_rejected(marker):
    with pytest.raises(ValueError, match="forbidden"):
        validate_bounded_hypothesis_item(
            _hypothesis(required_follow_up_data=[marker]),
            stock_code="600406",
            source_readiness_level="accepted_report_ready",
            identity_resolution_status="resolved",
        )
