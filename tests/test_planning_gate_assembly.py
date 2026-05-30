# -*- coding: utf-8 -*-

from copy import deepcopy
import builtins
from pathlib import Path

import pytest

import src.fundamental_skill.research_planning.planning_gate_assembly as pga
from src.fundamental_skill.research_planning.bounded_hypothesis_generator import (
    build_bounded_hypothesis_payload,
)
from src.fundamental_skill.research_planning.evidence_readiness import (
    build_deterministic_evidence_inventory,
    build_readiness_skeleton,
)
from src.fundamental_skill.research_planning.local_artifact_index import (
    build_artifact_row,
    build_ticker_local_artifact_inventory,
)
from src.fundamental_skill.research_planning.planning_gate_assembly import (
    AUTONOMOUS_TICKER_RESEARCH_PLANNING_RESULT_SCHEMA_VERSION,
    READINESS_FLAGS_PLANNING_ONLY_CAVEAT,
    build_autonomous_ticker_research_planning_result,
    validate_autonomous_ticker_research_planning_result,
    validate_blocked_reason_item,
    validate_data_gap_plan_item,
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
    company_name: str = "NARI Technology",
    artifact_path: str | None = None,
) -> dict:
    return build_artifact_row(
        artifact_id=artifact_id,
        artifact_type=artifact_type,
        artifact_path=artifact_path or f"output/synthetic/20260531/{stock_code}/{artifact_id}.json",
        source_family=source_family,
        stock_code=stock_code,
        company_name=company_name,
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
        "artifact_path": "output/official_disclosures/20260531T000000Z/600406/business_facts.json",
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


def _inventory(rows: list[dict], *, identity_status: str | None = None, company_name: str = "NARI Technology") -> dict:
    inventory = build_ticker_local_artifact_inventory(
        stock_code="600406",
        company_name=company_name,
        artifact_rows=rows,
    )
    if identity_status is not None:
        inventory["identity_resolution_status"] = identity_status
    return inventory


def _evidence_ref(artifact_id: str = "official_business", *, stock_code: str = "600406") -> str:
    return f"deterministic_evidence_inventory.v1:evidence_inventory:{stock_code}:{artifact_id}"


def _state_ref(artifact_id: str = "official_business", state: str = "available", *, stock_code: str = "600406") -> str:
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
            "deterministic_evidence_inventory.v1:missing_data_artifacts:600406:critical_financial:missing"
        ],
        "required_follow_up_data": ["Collect critical financial artifact state."],
        "caveats": ["Blocked planning item only."],
        "not_for_trading_advice": True,
    }
    payload.update(overrides)
    return payload


def _phase_inputs(
    rows: list[dict] | None = None,
    *,
    identity_status: str | None = None,
    industry_hypotheses: list[dict] | None = None,
    blocked_hypotheses: list[dict] | None = None,
    required_follow_up_data: list[str] | None = None,
) -> tuple[dict, dict, dict, dict]:
    ticker_inventory = _inventory(rows or [_official_row(), _financial_row()], identity_status=identity_status)
    evidence_inventory = build_deterministic_evidence_inventory(
        ticker_local_artifact_inventory=ticker_inventory
    )
    skeleton = build_readiness_skeleton(deterministic_evidence_inventory=evidence_inventory)
    bounded_payload = build_bounded_hypothesis_payload(
        deterministic_evidence_inventory=evidence_inventory,
        readiness_skeleton=skeleton,
        industry_hypotheses=industry_hypotheses,
        blocked_hypotheses=blocked_hypotheses,
        required_follow_up_data=required_follow_up_data,
        caveats=["Phase 4 planning only; not fact verification."],
    )
    return ticker_inventory, evidence_inventory, skeleton, bounded_payload


def _build_result(**overrides) -> dict:
    ticker, evidence, skeleton, bounded = _phase_inputs(industry_hypotheses=[_hypothesis()])
    kwargs = {
        "ticker_local_artifact_inventory": ticker,
        "deterministic_evidence_inventory": evidence,
        "readiness_skeleton": skeleton,
        "bounded_hypothesis_payload": bounded,
        "stock_code": "600406",
        "company_name": "NARI Technology",
    }
    kwargs.update(overrides)
    return build_autonomous_ticker_research_planning_result(**kwargs)


def _collect_keys_and_strings(payload) -> tuple[set[str], list[str]]:
    keys: set[str] = set()
    strings: list[str] = []

    def visit(value) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                keys.add(str(key))
                strings.append(str(key))
                visit(child)
            return
        if isinstance(value, list):
            for child in value:
                visit(child)
            return
        if isinstance(value, str):
            strings.append(value)

    visit(payload)
    return keys, strings


def test_valid_full_planning_result_uses_internal_schema_and_caveat():
    result = _build_result()

    assert result["schema_version"] == AUTONOMOUS_TICKER_RESEARCH_PLANNING_RESULT_SCHEMA_VERSION
    assert result["stock_code"] == "600406"
    assert result["company_name"] == "NARI Technology"
    assert result["identity_resolution_status"] == "resolved"
    assert result["readiness_level"] == "accepted_report_ready"
    assert result["can_generate_accepted_report"] is True
    assert result["can_generate_experimental_report"] is False
    assert READINESS_FLAGS_PLANNING_ONLY_CAVEAT in result["caveats"]
    assert result["not_for_trading_advice"] is True
    assert validate_autonomous_ticker_research_planning_result(result) == result


@pytest.mark.parametrize(
    "missing_name",
    [
        "ticker_local_artifact_inventory",
        "deterministic_evidence_inventory",
        "readiness_skeleton",
        "bounded_hypothesis_payload",
    ],
)
def test_missing_each_upstream_payload_fails_closed(missing_name):
    ticker, evidence, skeleton, bounded = _phase_inputs(industry_hypotheses=[_hypothesis()])
    kwargs = {
        "ticker_local_artifact_inventory": ticker,
        "deterministic_evidence_inventory": evidence,
        "readiness_skeleton": skeleton,
        "bounded_hypothesis_payload": bounded,
    }
    kwargs[missing_name] = None

    with pytest.raises(ValueError, match="missing required upstream payload"):
        build_autonomous_ticker_research_planning_result(**kwargs)


def test_invalid_hand_mutated_upstream_payload_is_rejected():
    ticker, evidence, skeleton, bounded = _phase_inputs(industry_hypotheses=[_hypothesis()])
    evidence["schema_version"] = "deterministic_evidence_inventory.v0"

    with pytest.raises(ValueError, match="schema_version"):
        build_autonomous_ticker_research_planning_result(
            ticker_local_artifact_inventory=ticker,
            deterministic_evidence_inventory=evidence,
            readiness_skeleton=skeleton,
            bounded_hypothesis_payload=bounded,
        )


def test_upstream_revalidation_calls_all_phase_validators(monkeypatch):
    ticker, evidence, skeleton, bounded = _phase_inputs(industry_hypotheses=[_hypothesis()])
    calls = {"ticker": 0, "evidence": 0, "skeleton": 0, "bounded": 0}

    original_ticker = pga.phase2c.validate_ticker_local_artifact_inventory
    original_evidence = pga.phase3.validate_deterministic_evidence_inventory
    original_skeleton = pga.phase3.validate_readiness_skeleton
    original_bounded = pga.phase4.validate_bounded_hypothesis_payload

    def ticker_wrapper(payload):
        calls["ticker"] += 1
        return original_ticker(payload)

    def evidence_wrapper(payload):
        calls["evidence"] += 1
        return original_evidence(payload)

    def skeleton_wrapper(payload):
        calls["skeleton"] += 1
        return original_skeleton(payload)

    def bounded_wrapper(payload, **kwargs):
        calls["bounded"] += 1
        return original_bounded(payload, **kwargs)

    monkeypatch.setattr(pga.phase2c, "validate_ticker_local_artifact_inventory", ticker_wrapper)
    monkeypatch.setattr(pga.phase3, "validate_deterministic_evidence_inventory", evidence_wrapper)
    monkeypatch.setattr(pga.phase3, "validate_readiness_skeleton", skeleton_wrapper)
    monkeypatch.setattr(pga.phase4, "validate_bounded_hypothesis_payload", bounded_wrapper)

    build_autonomous_ticker_research_planning_result(
        ticker_local_artifact_inventory=ticker,
        deterministic_evidence_inventory=evidence,
        readiness_skeleton=skeleton,
        bounded_hypothesis_payload=bounded,
    )

    assert calls == {"ticker": 1, "evidence": 1, "skeleton": 1, "bounded": 1}


def test_stock_code_mismatch_fails_closed():
    ticker, evidence, skeleton, bounded = _phase_inputs(industry_hypotheses=[_hypothesis()])
    ticker["stock_code"] = "600000"

    with pytest.raises(ValueError, match="stock_code"):
        build_autonomous_ticker_research_planning_result(
            ticker_local_artifact_inventory=ticker,
            deterministic_evidence_inventory=evidence,
            readiness_skeleton=skeleton,
            bounded_hypothesis_payload=bounded,
        )


def test_company_name_hint_mismatch_fails_closed():
    with pytest.raises(ValueError, match="company_name hint"):
        _build_result(company_name="Other Company")


@pytest.mark.parametrize("alias", ["NARI", "Nari Tech", "NARI Tech"])
def test_company_name_abbreviation_or_fuzzy_alias_is_rejected(alias):
    with pytest.raises(ValueError, match="company_name hint"):
        _build_result(company_name=alias)


def test_upstream_company_name_mismatch_fails_closed():
    ticker, evidence, skeleton, bounded = _phase_inputs(industry_hypotheses=[_hypothesis()])
    ticker["company_name"] = "NARI"

    with pytest.raises(ValueError, match="company_name mismatch|conflict"):
        build_autonomous_ticker_research_planning_result(
            ticker_local_artifact_inventory=ticker,
            deterministic_evidence_inventory=evidence,
            readiness_skeleton=skeleton,
            bounded_hypothesis_payload=bounded,
        )


def test_source_readiness_level_mismatch_is_rejected():
    ticker, evidence, skeleton, bounded = _phase_inputs(industry_hypotheses=[_hypothesis()])
    bounded["source_readiness_level"] = "blocked"

    with pytest.raises(ValueError, match="source_readiness_level"):
        build_autonomous_ticker_research_planning_result(
            ticker_local_artifact_inventory=ticker,
            deterministic_evidence_inventory=evidence,
            readiness_skeleton=skeleton,
            bounded_hypothesis_payload=bounded,
        )


def test_blocked_readiness_returns_fail_closed_planning_result():
    ticker, evidence, skeleton, bounded = _phase_inputs(
        identity_status="blocked",
        blocked_hypotheses=[_blocked_hypothesis(block_reason="blocked_readiness")],
    )

    result = build_autonomous_ticker_research_planning_result(
        ticker_local_artifact_inventory=ticker,
        deterministic_evidence_inventory=evidence,
        readiness_skeleton=skeleton,
        bounded_hypothesis_payload=bounded,
    )

    assert result["readiness_level"] == "blocked"
    assert result["can_generate_accepted_report"] is False
    assert result["can_generate_experimental_report"] is False
    assert any(reason["reason_type"] == "blocked_readiness" for reason in result["blocked_reasons"])


def test_evidence_conflict_readiness_returns_non_accepted_result():
    conflict_row = _financial_row(
        artifact_id="critical_conflict",
        source_status="conflict_open",
        review_status="conflict_open",
    )
    ticker, evidence, skeleton, bounded = _phase_inputs(
        rows=[_official_row(), conflict_row],
        blocked_hypotheses=[_blocked_hypothesis(block_reason="evidence_conflict")],
    )

    result = build_autonomous_ticker_research_planning_result(
        ticker_local_artifact_inventory=ticker,
        deterministic_evidence_inventory=evidence,
        readiness_skeleton=skeleton,
        bounded_hypothesis_payload=bounded,
    )

    assert result["readiness_level"] == "evidence_conflict_review_required"
    assert result["can_generate_accepted_report"] is False
    assert result["can_generate_experimental_report"] is False
    assert any(reason["reason_type"] == "evidence_conflict_readiness" for reason in result["blocked_reasons"])


def test_accepted_readiness_preserves_planning_indicator_flags():
    result = _build_result()

    assert result["readiness_level"] == "accepted_report_ready"
    assert result["can_generate_accepted_report"] is True
    assert result["can_generate_experimental_report"] is False
    assert "dashboard_payload" not in _collect_keys_and_strings(result)[0]
    assert "report_sections" not in _collect_keys_and_strings(result)[0]


def test_experimental_readiness_preserves_only_experimental_indicator():
    review_financial = _financial_row(
        artifact_id="critical_financial_review",
        source_status="review_required",
        review_status="review_required",
        artifact_path="output/fundamental_600406_review.json",
    )
    ticker, evidence, skeleton, bounded = _phase_inputs(
        rows=[_official_row(), _financial_row(), review_financial],
        industry_hypotheses=[_hypothesis()],
    )

    result = build_autonomous_ticker_research_planning_result(
        ticker_local_artifact_inventory=ticker,
        deterministic_evidence_inventory=evidence,
        readiness_skeleton=skeleton,
        bounded_hypothesis_payload=bounded,
    )

    assert result["readiness_level"] == "experimental_report_ready"
    assert result["can_generate_accepted_report"] is False
    assert result["can_generate_experimental_report"] is True


def test_blocked_hypothesis_block_reason_propagates_without_hypothesis_text():
    blocked = _blocked_hypothesis(
        hypothesis_text="Do not copy this upstream hypothesis text.",
        block_reason="missing_required_evidence",
    )
    ticker, evidence, skeleton, bounded = _phase_inputs(blocked_hypotheses=[blocked])

    result = build_autonomous_ticker_research_planning_result(
        ticker_local_artifact_inventory=ticker,
        deterministic_evidence_inventory=evidence,
        readiness_skeleton=skeleton,
        bounded_hypothesis_payload=bounded,
    )

    assert any(reason["blocking_state"] == "missing_required_evidence" for reason in result["blocked_reasons"])
    _, strings = _collect_keys_and_strings(result)
    assert "Do not copy this upstream hypothesis text." not in strings
    assert "hypothesis_text" not in _collect_keys_and_strings(result)[0]


def test_data_gap_plan_item_containing_target_price_or_trading_advice_is_rejected():
    item = {
        "gap_id": "data_gap_001",
        "gap_type": "missing_required_evidence",
        "description": "Need target price follow-up.",
        "source_phase": "phase3",
        "source_ref": "readiness_skeleton.v1",
        "priority": "high",
        "required_follow_up_data": ["Buy this stock after collection."],
        "caveats": [],
        "not_for_trading_advice": True,
    }

    with pytest.raises(ValueError, match="forbidden|trading"):
        validate_data_gap_plan_item(item)


def test_blocked_reason_item_containing_hypothesis_text_or_report_conclusion_is_rejected():
    item = {
        "reason_id": "blocked_reason_001",
        "reason_type": "blocked_readiness",
        "source_phase": "phase4",
        "source_ref": "bounded_hypothesis_payload.v1.blocked_hypotheses[0]",
        "blocking_state": "blocked",
        "description": "Do not include hypothesis_text or report conclusion.",
        "caveats": [],
        "not_for_trading_advice": True,
    }

    with pytest.raises(ValueError, match="forbidden"):
        validate_blocked_reason_item(item)


def test_final_output_forbidden_marker_scan_rejects_report_trading_template_keys():
    result = _build_result()
    with_report_key = deepcopy(result)
    with_report_key["report_sections"] = []

    with pytest.raises(ValueError, match="unsupported|prohibited"):
        validate_autonomous_ticker_research_planning_result(with_report_key)

    with_template_marker = deepcopy(result)
    with_template_marker["caveats"].append("template_payload is not allowed here.")
    with pytest.raises(ValueError, match="forbidden"):
        validate_autonomous_ticker_research_planning_result(with_template_marker)


def test_downstream_use_is_not_promoted_and_output_has_no_report_or_trading_content():
    result = _build_result()
    keys, strings = _collect_keys_and_strings(result)
    normalised = " ".join(strings).lower()

    assert "allowed_downstream_use" not in keys
    assert "report_sections" not in keys
    assert "investment_conclusion" not in keys
    assert "trading_advice" not in keys
    assert "target_price" not in normalised
    assert "trading advice" not in normalised
    assert "verified_fact" not in normalised


def test_data_gap_plan_uses_required_follow_up_data_without_investment_advice():
    ticker, evidence, skeleton, bounded = _phase_inputs(
        industry_hypotheses=[_hypothesis()],
        required_follow_up_data=["Collect segment disclosure evidence."],
    )

    result = build_autonomous_ticker_research_planning_result(
        ticker_local_artifact_inventory=ticker,
        deterministic_evidence_inventory=evidence,
        readiness_skeleton=skeleton,
        bounded_hypothesis_payload=bounded,
    )

    assert any(
        "Collect segment disclosure evidence." in gap["required_follow_up_data"]
        for gap in result["data_gap_plan"]
    )
    assert all(gap["not_for_trading_advice"] is True for gap in result["data_gap_plan"])


def test_no_file_io_provider_network_or_parser_touch(monkeypatch):
    ticker, evidence, skeleton, bounded = _phase_inputs(industry_hypotheses=[_hypothesis()])

    def blocked_io(*args, **kwargs):
        raise AssertionError("Phase 5 must not perform IO")

    monkeypatch.setattr(builtins, "open", blocked_io)
    monkeypatch.setattr(Path, "open", blocked_io)

    result = build_autonomous_ticker_research_planning_result(
        ticker_local_artifact_inventory=ticker,
        deterministic_evidence_inventory=evidence,
        readiness_skeleton=skeleton,
        bounded_hypothesis_payload=bounded,
    )

    assert result["schema_version"] == AUTONOMOUS_TICKER_RESEARCH_PLANNING_RESULT_SCHEMA_VERSION


def test_no_input_mutation():
    ticker, evidence, skeleton, bounded = _phase_inputs(industry_hypotheses=[_hypothesis()])
    original = deepcopy((ticker, evidence, skeleton, bounded))

    build_autonomous_ticker_research_planning_result(
        ticker_local_artifact_inventory=ticker,
        deterministic_evidence_inventory=evidence,
        readiness_skeleton=skeleton,
        bounded_hypothesis_payload=bounded,
    )

    assert (ticker, evidence, skeleton, bounded) == original


def test_validators_return_defensive_copies():
    gap = {
        "gap_id": "data_gap_001",
        "gap_type": "missing_required_evidence",
        "description": "Missing artifact state requires data collection.",
        "source_phase": "phase3",
        "source_ref": "readiness_skeleton.v1",
        "priority": "high",
        "required_follow_up_data": ["Collect artifact state."],
        "caveats": [],
        "not_for_trading_advice": True,
    }

    validated_gap = validate_data_gap_plan_item(gap)
    validated_gap["required_follow_up_data"].append("Mutated copy only.")
    assert gap["required_follow_up_data"] == ["Collect artifact state."]

    result = _build_result()
    validated_result = validate_autonomous_ticker_research_planning_result(result)
    validated_result["caveats"].append("Mutated copy only.")
    assert "Mutated copy only." not in result["caveats"]


def test_invalid_schema_version_is_rejected():
    result = _build_result()
    result["schema_version"] = "autonomous_ticker_research_planning_result.v0"

    with pytest.raises(ValueError, match="schema_version"):
        validate_autonomous_ticker_research_planning_result(result)


def test_invalid_data_gap_plan_item_is_rejected():
    item = {
        "gap_id": "data_gap_001",
        "gap_type": "not_allowed",
        "description": "Missing artifact state requires data collection.",
        "source_phase": "phase3",
        "source_ref": "readiness_skeleton.v1",
        "priority": "high",
        "required_follow_up_data": ["Collect artifact state."],
        "caveats": [],
        "not_for_trading_advice": True,
    }

    with pytest.raises(ValueError, match="gap_type"):
        validate_data_gap_plan_item(item)


def test_invalid_blocked_reason_item_is_rejected():
    item = {
        "reason_id": "blocked_reason_001",
        "reason_type": "not_allowed",
        "source_phase": "phase3",
        "source_ref": "readiness_skeleton.v1",
        "blocking_state": "blocked",
        "description": "Upstream readiness state is blocked.",
        "caveats": [],
        "not_for_trading_advice": True,
    }

    with pytest.raises(ValueError, match="reason_type"):
        validate_blocked_reason_item(item)


def test_not_for_trading_advice_false_is_rejected():
    with pytest.raises(ValueError, match="not_for_trading_advice"):
        _build_result(not_for_trading_advice=False)

    result = _build_result()
    result["not_for_trading_advice"] = False
    with pytest.raises(ValueError, match="not_for_trading_advice"):
        validate_autonomous_ticker_research_planning_result(result)
