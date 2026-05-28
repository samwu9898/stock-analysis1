# -*- coding: utf-8 -*-

import copy
import inspect

import pytest

from src.fundamental_skill.research_report.official_disclosure_parser import (
    OFFICIAL_DISCLOSURE_VERSION,
    PARSER_VERSION,
)
from src.fundamental_skill.research_report.official_disclosure_candidate_integration import (
    OFFICIAL_DISCLOSURE_CANDIDATE_VERSION,
    OFFICIAL_DISCLOSURE_SOURCE_TYPE,
    OfficialDisclosureCandidateConflictError,
    OfficialDisclosureCandidateSecretError,
    OfficialDisclosureCandidateValidationError,
    build_official_disclosure_candidate_row,
    convert_official_disclosure_facts_to_candidate_rows,
    determine_official_candidate_review_status,
    validate_official_disclosure_candidate_payload,
    validate_official_disclosure_candidate_row,
)
import src.fundamental_skill.research_report.official_disclosure_candidate_integration as adapter_module


def _source_document(**overrides) -> dict:
    source_document = {
        "source_document_id": "doc_600406_2025H1_real_local",
        "document_type": "semiannual_report",
        "title": "600406 2025H1 semiannual report",
        "report_period": "2025H1",
        "disclosure_date": "2025-08-30",
        "source_origin": "local_downloaded_official_disclosure",
        "source_uri_or_path": "local/600406_2025h1.txt",
        "sha256": "a" * 64,
        "text_extraction_method": "plain_text",
        "text_extraction_quality": "medium",
        "caveats": ["source_document_requires_review"],
    }
    source_document.update(overrides)
    return source_document


def _official_fact(**overrides) -> dict:
    fact = {
        "fact_id": "fact_main_business_001",
        "field_path": "basic_info.main_business_official_text",
        "value": "Grid automation and industrial control official text.",
        "unit": None,
        "period": "2025H1",
        "source_document_id": "doc_600406_2025H1_real_local",
        "source_section": "main business",
        "source_page_or_anchor": "p12",
        "evidence_tier": "L1_official_disclosure",
        "extraction_confidence": "medium",
        "needs_human_review": True,
        "caveats": ["fact_requires_review"],
    }
    fact.update(overrides)
    return fact


def _source_table(**overrides) -> dict:
    source_table = {
        "source_table_id": "table_600406_2025h1_product",
        "source_document_id": "doc_600406_2025H1_real_local",
        "source_format": "csv",
        "source_file_path": "",
        "source_section": "main business by product",
        "table_title": "600406 2025H1 main business by product",
        "headers": ["product name", "main business revenue"],
        "row_count": 6,
        "column_count": 7,
        "detected_unit": "",
        "detected_period": "",
        "classification_hint": "product",
        "reader_warnings": [{"reason": "delimiter_sniffed", "detail": ""}],
        "table_quality_hint": "structured_medium",
        "table_quality_final": "structured_medium",
        "source_hash": "",
        "caveats": ["local_structured_sample_requires_human_review"],
    }
    source_table.update(overrides)
    return source_table


def _table_fact(index: int = 1, **overrides) -> dict:
    fact = _official_fact(
        fact_id=f"table_fact_{index:03d}_revenue",
        field_path="business_composition.product_segment.revenue",
        value=1000.0 + index,
        unit="CNY",
        period="2025H1",
        source_section="main business by product",
        source_page_or_anchor="",
        source_table_id="table_600406_2025h1_product",
        source_row_index=index,
        source_column_name="main business revenue",
        source_column_map={
            "segment_name": "product name",
            "revenue": "main business revenue",
            "denominator": "main business revenue total",
        },
        classification_type="product",
        segment_name=f"segment_{index}",
        denominator="main business revenue total",
        table_quality="structured_medium",
        caveats=["local_structured_sample_requires_human_review"],
    )
    fact.update(overrides)
    return fact


def _official_payload(*, facts=None, source_tables=None, **overrides) -> dict:
    payload = {
        "version": OFFICIAL_DISCLOSURE_VERSION,
        "code": "600406",
        "company_name": "Guodian NARI",
        "created_at": "2026-05-29T00:00:00+00:00",
        "parser_version": PARSER_VERSION,
        "source_documents": [_source_document()],
        "extracted_facts": list(facts if facts is not None else [_official_fact()]),
        "source_tables": list(source_tables or []),
        "table_caveats": [{"reason": "unit_not_detected", "source_table_id": "table_600406_2025h1_product"}],
        "table_conversion_warnings": [{"reason": "denominator_missing", "source_table_id": "table_600406_2025h1_product"}],
        "extraction_warnings": ["text extraction warning"],
        "data_quality_caveats": ["data quality caveat"],
        "not_for_trading_advice": True,
    }
    payload.update(overrides)
    return payload


def test_constants_match_design():
    assert OFFICIAL_DISCLOSURE_SOURCE_TYPE == "official_disclosure"
    assert OFFICIAL_DISCLOSURE_CANDIDATE_VERSION == "official_disclosure_fact_candidates.v1"


def test_convert_valid_official_payload_with_main_business_fact():
    payload = convert_official_disclosure_facts_to_candidate_rows(_official_payload())

    validate_official_disclosure_candidate_payload(payload)
    assert payload["version"] == OFFICIAL_DISCLOSURE_CANDIDATE_VERSION
    assert payload["source_type"] == "official_disclosure"
    assert payload["not_for_trading_advice"] is True
    assert len(payload["candidate_rows"]) == 1
    row = payload["candidate_rows"][0]
    assert row["field_path"] == "basic_info.main_business_official_text"
    assert row["source_type"] == "official_disclosure"
    assert row["evidence_tier"] == "L1_official_disclosure"
    assert row["source_document_id"] == "doc_600406_2025H1_real_local"
    assert row["source_section"] == "main business"
    assert row["source_page_or_anchor"] == "p12"
    assert row["extraction_confidence"] == "medium"
    assert row["review_status"] == "manual_review_required"


def test_convert_valid_payload_with_periodic_text_facts():
    facts = [
        _official_fact(fact_id="fact_report_title", field_path="official_disclosure.periodic_report_title", value="2025 semiannual report"),
        _official_fact(fact_id="fact_disclosure_date", field_path="official_disclosure.disclosure_date", value="2025-08-30"),
        _official_fact(fact_id="fact_report_period", field_path="official_disclosure.report_period", value="2025H1"),
        _official_fact(fact_id="fact_risk_trigger", field_path="official_disclosure.risk_trigger_text", value="risk trigger text"),
        _official_fact(
            fact_id="fact_guidance_placeholder",
            field_path="official_disclosure.management_guidance_placeholder",
            value="guidance placeholder",
        ),
    ]
    payload = convert_official_disclosure_facts_to_candidate_rows(_official_payload(facts=facts))

    assert {row["field_path"] for row in payload["candidate_rows"]} == {
        "official_disclosure.periodic_report_title",
        "official_disclosure.disclosure_date",
        "official_disclosure.report_period",
        "official_disclosure.risk_trigger_text",
        "official_disclosure.management_guidance_placeholder",
    }
    assert all(row["source_section"] == "main business" for row in payload["candidate_rows"])


def test_convert_valid_payload_with_six_table_revenue_facts():
    facts = [_table_fact(index) for index in range(1, 7)]
    payload = convert_official_disclosure_facts_to_candidate_rows(
        _official_payload(facts=facts, source_tables=[_source_table()])
    )

    assert len(payload["candidate_rows"]) == 6
    assert {row["source_type"] for row in payload["candidate_rows"]} == {"official_disclosure"}
    assert {row["evidence_tier"] for row in payload["candidate_rows"]} == {"L1_official_disclosure"}
    assert {row["review_status"] for row in payload["candidate_rows"]} == {"manual_review_required"}


def test_table_candidate_rows_preserve_source_table_row_column_and_column_map():
    row = convert_official_disclosure_facts_to_candidate_rows(
        _official_payload(facts=[_table_fact()], source_tables=[_source_table()])
    )["candidate_rows"][0]

    assert row["source_table_id"] == "table_600406_2025h1_product"
    assert row["source_row_index"] == 1
    assert row["source_column_name"] == "main business revenue"
    assert row["source_column_map"] == {
        "segment_name": "product name",
        "revenue": "main business revenue",
        "denominator": "main business revenue total",
    }


def test_table_candidate_rows_preserve_classification_segment_denominator_and_quality():
    row = convert_official_disclosure_facts_to_candidate_rows(
        _official_payload(facts=[_table_fact()], source_tables=[_source_table()])
    )["candidate_rows"][0]

    assert row["classification_type"] == "product"
    assert row["segment_name"] == "segment_1"
    assert row["denominator"] == "main business revenue total"
    assert row["table_quality"] == "structured_medium"
    assert "local_structured_sample_requires_human_review" in row["caveats"]


def test_returns_deep_copy_and_does_not_mutate_inputs():
    official_payload = _official_payload(facts=[_table_fact()], source_tables=[_source_table()])
    original = copy.deepcopy(official_payload)

    candidate_payload = convert_official_disclosure_facts_to_candidate_rows(official_payload)
    candidate_payload["candidate_rows"][0]["source_column_map"]["revenue"] = "changed"
    candidate_payload["candidate_caveats"][0]["reason"] = "changed"

    assert official_payload == original


def test_needs_human_review_true_maps_to_manual_review_required():
    row = build_official_disclosure_candidate_row(
        official_fact=_official_fact(needs_human_review=True),
        source_document=_source_document(),
    )

    assert row["needs_human_review"] is True
    assert row["review_status"] == "manual_review_required"


def test_missing_unit_period_or_denominator_blocks_table_numeric_fact():
    fact = _table_fact(unit=None, period="", denominator="", caveats=["denominator_missing"])
    row = build_official_disclosure_candidate_row(
        official_fact=fact,
        source_document=_source_document(report_period=""),
        source_table=_source_table(detected_unit="", detected_period=""),
    )

    assert row["review_status"] == "blocked_by_caveat"


def test_structured_medium_remains_manual_review_required():
    row = build_official_disclosure_candidate_row(
        official_fact=_table_fact(table_quality="structured_medium", needs_human_review=False),
        source_document=_source_document(),
        source_table=_source_table(table_quality_final="structured_medium"),
    )

    assert determine_official_candidate_review_status(row) == "manual_review_required"
    assert row["review_status"] == "manual_review_required"


def test_structured_high_can_be_auto_candidate_but_never_verified():
    row = build_official_disclosure_candidate_row(
        official_fact=_table_fact(table_quality="structured_high", needs_human_review=False, caveats=[]),
        source_document=_source_document(caveats=[]),
        source_table=_source_table(table_quality_final="structured_high", caveats=[]),
    )

    assert row["review_status"] == "auto_candidate"
    assert "verified_fact" not in row


def test_unsupported_or_missing_value_maps_to_unsupported_or_missing():
    row = build_official_disclosure_candidate_row(
        official_fact=_official_fact(value=None, needs_human_review=False),
        source_document=_source_document(),
    )

    assert row["review_status"] == "unsupported_or_missing"


@pytest.mark.parametrize("table_quality", ["unreliable_text_copy", "unusable"])
def test_caveat_only_table_quality_not_converted_to_fact_candidates(table_quality):
    payload = convert_official_disclosure_facts_to_candidate_rows(
        _official_payload(
            facts=[_table_fact(table_quality=table_quality)],
            source_tables=[_source_table(table_quality_final=table_quality)],
        )
    )

    assert payload["candidate_rows"] == []
    assert any(
        isinstance(caveat, dict) and caveat["reason"] == "caveat_only_table_quality"
        for caveat in payload["candidate_caveats"]
    )


@pytest.mark.parametrize(
    "field_path",
    [
        "business_composition.product_segment.cost",
        "business_composition.product_segment.gross_margin",
        "business_composition.product_segment.yoy",
    ],
)
def test_deferred_table_fact_types_not_converted_by_v1(field_path):
    payload = convert_official_disclosure_facts_to_candidate_rows(
        _official_payload(facts=[_table_fact(field_path=field_path)], source_tables=[_source_table()])
    )

    assert payload["candidate_rows"] == []
    assert any(
        isinstance(caveat, dict) and caveat["reason"] == "deferred_table_fact_type"
        for caveat in payload["candidate_caveats"]
    )


def test_table_caveats_and_conversion_warnings_propagate():
    payload = convert_official_disclosure_facts_to_candidate_rows(
        _official_payload(facts=[_table_fact()], source_tables=[_source_table()])
    )

    assert {"reason": "unit_not_detected", "source_table_id": "table_600406_2025h1_product"} in payload["candidate_caveats"]
    assert {"reason": "denominator_missing", "source_table_id": "table_600406_2025h1_product"} in payload["integration_warnings"]
    assert "text extraction warning" in payload["integration_warnings"]
    assert "data quality caveat" in payload["candidate_caveats"]


def test_source_lineage_mismatch_fails_closed():
    with pytest.raises(OfficialDisclosureCandidateConflictError):
        convert_official_disclosure_facts_to_candidate_rows(
            _official_payload(
                facts=[_table_fact(source_table_id="missing_table")],
                source_tables=[_source_table()],
            )
        )
    with pytest.raises(OfficialDisclosureCandidateConflictError):
        convert_official_disclosure_facts_to_candidate_rows(
            _official_payload(
                facts=[_table_fact()],
                source_tables=[_source_table(source_document_id="doc_other")],
            )
        )


def test_no_verified_fact_marker_allowed():
    payload = convert_official_disclosure_facts_to_candidate_rows(_official_payload())

    assert "verified_fact" not in repr(payload)
    with pytest.raises(OfficialDisclosureCandidateValidationError):
        convert_official_disclosure_facts_to_candidate_rows(
            _official_payload(facts=[_official_fact(verified_fact=True)])
        )
    with pytest.raises(OfficialDisclosureCandidateValidationError):
        validate_official_disclosure_candidate_row(
            {
                **payload["candidate_rows"][0],
                "review_status": "verified",
            }
        )


def test_forbidden_recommendation_keys_rejected():
    with pytest.raises(OfficialDisclosureCandidateValidationError):
        convert_official_disclosure_facts_to_candidate_rows(
            _official_payload(facts=[_official_fact(buy=True)])
        )


@pytest.mark.parametrize(
    "payload_override",
    [
        {"api_token": "value"},
        {"value": "Abcdefghijklmnopqrstuvwxyz123456"},
    ],
)
def test_token_like_key_or_value_rejected(payload_override):
    with pytest.raises(OfficialDisclosureCandidateSecretError):
        convert_official_disclosure_facts_to_candidate_rows(
            _official_payload(facts=[_official_fact(**payload_override)])
        )


@pytest.mark.parametrize(
    "bad_value",
    [
        "Bearer abc.def.ghi",
        "mcp://local-control",
        "config/.env.local",
        "C:\\Users\\Admin\\.ssh\\id_rsa",
    ],
)
def test_bearer_remote_control_dotenv_and_local_secret_path_rejected(bad_value):
    with pytest.raises(OfficialDisclosureCandidateSecretError) as exc:
        convert_official_disclosure_facts_to_candidate_rows(
            _official_payload(facts=[_official_fact(caveats=[bad_value])])
        )

    assert bad_value not in str(exc.value)


def test_candidate_payload_validation_rejects_bad_source_type_and_advice_flag():
    payload = convert_official_disclosure_facts_to_candidate_rows(_official_payload())
    with pytest.raises(OfficialDisclosureCandidateValidationError):
        validate_official_disclosure_candidate_payload({**payload, "source_type": "tushare"})
    with pytest.raises(OfficialDisclosureCandidateValidationError):
        validate_official_disclosure_candidate_payload({**payload, "not_for_trading_advice": False})


def test_existing_fact_candidates_schema_is_provider_centric_so_merge_is_not_implemented():
    assert not hasattr(adapter_module, "merge_official_candidates_into_fact_candidates")


def test_static_boundary_has_no_provider_env_network_reader_or_runner_imports():
    source = inspect.getsource(adapter_module)
    forbidden_fragments = [
        "CNInfo",
        "Tushare",
        "AkShare",
        "requests",
        "urllib",
        "os.environ",
        "getenv",
        "subprocess",
        "pytesseract",
        "easyocr",
        "pdfplumber",
        "pypdf",
        "docx",
        "BeautifulSoup",
        "bs4",
        "pandas",
        "openpyxl",
        "old_runner",
        "write_text",
        "open(",
        "mkdir",
    ]

    for fragment in forbidden_fragments:
        assert fragment not in source
