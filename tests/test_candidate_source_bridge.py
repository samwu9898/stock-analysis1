# -*- coding: utf-8 -*-

import inspect

import pytest

import src.fundamental_skill.research_report.candidate_source_bridge as bridge_module
from src.fundamental_skill.research_report.candidate_source_bridge import (
    CANDIDATE_SOURCE_BRIDGE_VERSION,
    CANDIDATE_SOURCE_TYPES,
    CandidateSourceBridgeConflictError,
    CandidateSourceBridgePathError,
    CandidateSourceBridgeSecretError,
    CandidateSourceBridgeValidationError,
    build_candidate_source_bridge,
    build_candidate_source_entry,
    build_cross_source_conflict,
    build_review_priority,
    validate_candidate_source_bridge,
    validate_candidate_source_entry,
    validate_cross_source_conflict,
    validate_review_priority,
)


def _provider_source(**overrides) -> dict:
    entry = {
        "source_type": "provider_candidates",
        "artifact_path": "output/ground_truth_candidates/20260527T155056/600406/fact_candidates.json",
        "candidate_count": 12,
        "manual_review_count": 4,
        "blocked_count": 1,
        "source_summary": {"mode": "offline_artifact_candidate_generation"},
        "not_for_trading_advice": True,
    }
    entry.update(overrides)
    return entry


def _official_source(**overrides) -> dict:
    entry = {
        "source_type": "official_disclosure_candidates",
        "artifact_path": "output/official_disclosures/20260528T182057Z/600406/official_disclosure_candidates_review.json",
        "candidate_count": 7,
        "manual_review_count": 7,
        "blocked_count": 0,
        "source_summary": {
            "artifact_version": "official_disclosure_fact_candidates.v1",
            "evidence_tier": "L1_official_disclosure",
            "source_documents": 1,
            "source_tables": 1,
        },
        "not_for_trading_advice": True,
    }
    entry.update(overrides)
    return entry


def _conflict(**overrides) -> dict:
    entry = {
        "conflict_id": "600406-conflict-001",
        "field_path": "business_composition.product_segment.revenue",
        "period": "2025H1",
        "unit": "CNY",
        "provider_candidate_ref": {
            "source_type": "provider_candidates",
            "artifact_ref": "output/ground_truth_candidates/20260527T155056/600406/fact_candidates.json",
            "candidate_id": "provider-001",
        },
        "official_candidate_ref": {
            "source_type": "official_disclosure_candidates",
            "artifact_ref": "output/official_disclosures/20260528T182057Z/600406/official_disclosure_candidates_review.json",
            "candidate_id": "official-001",
        },
        "conflict_type": "value_mismatch",
        "severity": "manual_review_required",
        "caveats": ["review signal only"],
    }
    entry.update(overrides)
    return entry


def _review_priority(**overrides) -> dict:
    entry = {
        "priority_id": "600406-official-A1",
        "source_type": "official_disclosure_candidates",
        "candidate_ref": {
            "artifact_ref": "output/official_disclosures/20260528T182057Z/600406/official_disclosure_candidates_review.json",
            "candidate_id": "official-001",
        },
        "field_path": "business_composition.product_segment.revenue",
        "priority": "high",
        "reason": "official_provider_conflict",
        "caveats": ["structured_medium_requires_review"],
    }
    entry.update(overrides)
    return entry


def test_constants_match_bridge_design():
    assert CANDIDATE_SOURCE_BRIDGE_VERSION == "candidate_source_bridge.v1"
    assert CANDIDATE_SOURCE_TYPES == {"provider_candidates", "official_disclosure_candidates"}


def test_build_valid_bridge_with_provider_source_only():
    payload = build_candidate_source_bridge(
        code="600406",
        company_name="Guodian NARI",
        candidate_sources=[_provider_source()],
        created_at="2026-05-29T00:00:00Z",
    )

    assert payload["version"] == CANDIDATE_SOURCE_BRIDGE_VERSION
    assert payload["code"] == "600406"
    assert payload["candidate_sources"][0]["source_type"] == "provider_candidates"
    assert payload["not_for_trading_advice"] is True
    validate_candidate_source_bridge(payload)


def test_build_valid_bridge_with_official_source_only():
    payload = build_candidate_source_bridge(
        code="600406",
        company_name="Guodian NARI",
        candidate_sources=[_official_source()],
    )

    assert payload["candidate_sources"][0]["candidate_count"] == 7
    assert payload["candidate_sources"][0]["manual_review_count"] == 7
    validate_candidate_source_bridge(payload)


def test_build_valid_bridge_with_provider_and_official_sources():
    payload = build_candidate_source_bridge(
        code="600406",
        company_name="Guodian NARI",
        candidate_sources=[_provider_source(), _official_source()],
        cross_source_conflicts=[_conflict()],
        review_priorities=[_review_priority()],
    )

    assert len(payload["candidate_sources"]) == 2
    assert payload["cross_source_conflicts"][0]["conflict_type"] == "value_mismatch"
    assert payload["review_priorities"][0]["priority"] == "high"
    validate_candidate_source_bridge(payload)


def test_validate_candidate_source_entry_and_helper():
    entry = build_candidate_source_entry(
        source_type="official_disclosure_candidates",
        artifact_path="output/official_disclosures/20260528T182057Z/600406/official_disclosure_candidates_review.json",
        candidate_count=7,
        manual_review_count=7,
        blocked_count=0,
        source_summary="L1 official disclosure",
    )

    validate_candidate_source_entry(entry)
    assert entry["not_for_trading_advice"] is True


def test_reject_invalid_source_type():
    with pytest.raises(CandidateSourceBridgeValidationError):
        validate_candidate_source_entry(_official_source(source_type="official_disclosure"))


@pytest.mark.parametrize(
    "artifact_path",
    [
        "C:/Users/Admin/secret.json",
        "C:\\Users\\Admin\\secret.json",
        "/tmp/fact_candidates.json",
        "~/fact_candidates.json",
    ],
)
def test_reject_absolute_artifact_path(artifact_path):
    with pytest.raises(CandidateSourceBridgePathError):
        validate_candidate_source_entry(_provider_source(artifact_path=artifact_path))


@pytest.mark.parametrize(
    "artifact_path",
    [
        "../output/fact_candidates.json",
        "output/../secret.json",
        "output//secret.json",
        "output/./secret.json",
    ],
)
def test_reject_path_traversal(artifact_path):
    with pytest.raises(CandidateSourceBridgePathError):
        validate_candidate_source_entry(_provider_source(artifact_path=artifact_path))


def test_reject_path_outside_output():
    with pytest.raises(CandidateSourceBridgePathError):
        validate_candidate_source_entry(_provider_source(artifact_path="tmp/fact_candidates.json"))


@pytest.mark.parametrize(
    "count_field",
    ["candidate_count", "manual_review_count", "blocked_count"],
)
def test_reject_negative_counts(count_field):
    with pytest.raises(CandidateSourceBridgeValidationError):
        validate_candidate_source_entry(_provider_source(**{count_field: -1}))


def test_reject_count_inconsistency_without_caveat():
    with pytest.raises(CandidateSourceBridgeValidationError):
        validate_candidate_source_entry(
            _provider_source(candidate_count=2, manual_review_count=2, blocked_count=1)
        )


def test_allow_count_inconsistency_with_caveat():
    validate_candidate_source_entry(
        _provider_source(candidate_count=2, manual_review_count=2, blocked_count=1, caveats=["overlapping counts"])
    )


def test_reject_missing_not_for_trading_advice():
    entry = _official_source()
    entry.pop("not_for_trading_advice")
    with pytest.raises(CandidateSourceBridgeValidationError):
        validate_candidate_source_entry(entry)

    with pytest.raises(CandidateSourceBridgeValidationError):
        validate_candidate_source_entry(_official_source(not_for_trading_advice=False))


def test_validate_cross_source_conflict_and_helper():
    entry = build_cross_source_conflict(
        conflict_id="600406-conflict-001",
        field_path="business_composition.product_segment.revenue",
        period="2025H1",
        unit="CNY",
        provider_candidate_ref="provider-candidate-001",
        official_candidate_ref="official-candidate-001",
        conflict_type="value_mismatch",
        severity="manual_review_required",
        caveats=["review signal only"],
    )

    validate_cross_source_conflict(entry)
    assert entry["severity"] == "manual_review_required"


def test_reject_invalid_conflict_type():
    with pytest.raises(CandidateSourceBridgeConflictError):
        validate_cross_source_conflict(_conflict(conflict_type="provider_primary_switch"))


def test_reject_invalid_severity():
    with pytest.raises(CandidateSourceBridgeConflictError):
        validate_cross_source_conflict(_conflict(severity="verified"))


def test_conflict_is_review_signal_only():
    entry = _conflict()
    validate_cross_source_conflict(entry)

    assert "provider_primary" not in repr(entry)
    assert "verified_fact" not in repr(entry)
    assert "research_report_v1_update" not in entry


def test_validate_review_priority_and_helper():
    entry = build_review_priority(
        priority_id="600406-official-A1",
        source_type="official_disclosure_candidates",
        candidate_ref="official-candidate-001",
        field_path="business_composition.product_segment.revenue",
        priority="high",
        reason="official_l1_trace_available",
        caveats=["not fixture promotion"],
    )

    validate_review_priority(entry)
    assert entry["priority"] == "high"


def test_reject_invalid_priority():
    with pytest.raises(CandidateSourceBridgeValidationError):
        validate_review_priority(_review_priority(priority="urgent"))


def test_review_priority_boundaries_are_not_fact_promotion():
    entry = _review_priority(reason="structured_medium_requires_review")
    validate_review_priority(entry)

    assert "verified_fact" not in repr(entry)
    assert "fixture" not in entry
    assert entry["priority"] == "high"


@pytest.mark.parametrize(
    "payload_patch",
    [
        {"provider_primary": "official_disclosure_candidates"},
        {"primary_provider": "official_disclosure_candidates"},
        {"provider_primary_switch": True},
    ],
)
def test_no_provider_primary_change_field(payload_patch):
    payload = build_candidate_source_bridge(
        code="600406",
        company_name="Guodian NARI",
        candidate_sources=[_official_source()],
    )
    payload.update(payload_patch)

    with pytest.raises(CandidateSourceBridgeValidationError):
        validate_candidate_source_bridge(payload)


@pytest.mark.parametrize(
    "payload_patch",
    [
        {"verified_fact": True},
        {"auto_verified": True},
        {"review_status": "verified"},
        {"source_summary": "verified_fact"},
    ],
)
def test_no_verified_fact(payload_patch):
    with pytest.raises(CandidateSourceBridgeValidationError):
        validate_candidate_source_entry(_official_source(**payload_patch))


@pytest.mark.parametrize(
    "payload_patch",
    [
        {"buy": True},
        {"sell": True},
        {"target_price": 100},
        {"position": "increase"},
        {"portfolio_weight": 0.1},
    ],
)
def test_no_trading_recommendation_keys(payload_patch):
    with pytest.raises(CandidateSourceBridgeValidationError):
        validate_candidate_source_entry(_official_source(**payload_patch))


@pytest.mark.parametrize(
    "payload_patch",
    [
        {"api_token": "value"},
        {"source_summary": "Abcdefghijklmnopqrstuvwxyz123456"},
    ],
)
def test_reject_token_like_key_or_value(payload_patch):
    with pytest.raises(CandidateSourceBridgeSecretError):
        validate_candidate_source_entry(_official_source(**payload_patch))


@pytest.mark.parametrize(
    "bad_value",
    [
        "Bearer abc.def.ghi",
        "mcp://local-control",
        "config/.env.local",
        "C:\\Users\\Admin\\.ssh\\id_rsa",
    ],
)
def test_reject_bearer_remote_control_dotenv_and_local_secret_path(bad_value):
    with pytest.raises(CandidateSourceBridgeSecretError) as exc:
        validate_candidate_source_entry(_official_source(source_summary=bad_value))

    assert bad_value not in str(exc.value)


def test_secret_error_message_masks_value():
    secret_value = "Bearer abc.def.ghi"
    with pytest.raises(CandidateSourceBridgeSecretError) as exc:
        validate_candidate_source_entry(_official_source(source_summary=secret_value))

    assert "<masked>" in str(exc.value)
    assert secret_value not in str(exc.value)


def test_reject_bridge_missing_top_level_not_for_trading_advice():
    payload = {
        "version": CANDIDATE_SOURCE_BRIDGE_VERSION,
        "code": "600406",
        "company_name": "Guodian NARI",
        "created_at": "",
        "candidate_sources": [_official_source()],
        "cross_source_conflicts": [],
        "review_priorities": [],
    }

    with pytest.raises(CandidateSourceBridgeValidationError):
        validate_candidate_source_bridge(payload)


def test_reject_invalid_top_level_version_code_and_company():
    valid = build_candidate_source_bridge(
        code="600406",
        company_name="Guodian NARI",
        candidate_sources=[_official_source()],
    )
    with pytest.raises(CandidateSourceBridgeValidationError):
        validate_candidate_source_bridge({**valid, "version": "v0"})
    with pytest.raises(CandidateSourceBridgeValidationError):
        validate_candidate_source_bridge({**valid, "code": "60040"})
    with pytest.raises(CandidateSourceBridgeValidationError):
        validate_candidate_source_bridge({**valid, "company_name": ""})


def test_reject_empty_candidate_sources():
    with pytest.raises(CandidateSourceBridgeValidationError):
        build_candidate_source_bridge(code="600406", company_name="Guodian NARI", candidate_sources=[])


def test_builders_return_deep_copies_and_do_not_mutate_inputs():
    source = _official_source()
    priority = _review_priority()
    payload = build_candidate_source_bridge(
        code="600406",
        company_name="Guodian NARI",
        candidate_sources=[source],
        review_priorities=[priority],
    )

    payload["candidate_sources"][0]["source_summary"]["source_documents"] = 99
    payload["review_priorities"][0]["caveats"].append("changed")

    assert source["source_summary"]["source_documents"] == 1
    assert priority["caveats"] == ["structured_medium_requires_review"]


def test_no_real_output_writes_or_merge_function():
    assert not hasattr(bridge_module, "write_candidate_source_bridge")
    assert not hasattr(bridge_module, "merge_official_candidates_into_fact_candidates")


def test_no_provider_env_network_mcp_reader_or_runner_imports():
    source = inspect.getsource(bridge_module)
    forbidden_fragments = [
        "import requests",
        "from requests",
        "import urllib",
        "from urllib",
        "os.environ",
        "getenv",
        "subprocess",
        "cninfo",
        "tushare",
        "akshare",
        "ProviderRouter",
        "pytesseract",
        "easyocr",
        "pdfplumber",
        "pypdf",
        "import docx",
        "from docx",
        "BeautifulSoup",
        "bs4",
        "pandas",
        "openpyxl",
        "old_runner",
        "open(",
        "write_text",
        "mkdir",
    ]

    for fragment in forbidden_fragments:
        assert fragment not in source
