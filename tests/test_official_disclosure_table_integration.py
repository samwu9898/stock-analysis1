# -*- coding: utf-8 -*-

import copy
import inspect

import pytest

from src.fundamental_skill.research_report.official_disclosure_parser import (
    OFFICIAL_DISCLOSURE_VERSION,
    PARSER_VERSION,
)
from src.fundamental_skill.research_report.official_disclosure_table_integration import (
    DEFAULT_TABLE_FACT_NAMESPACE,
    LOCAL_STRUCTURED_REVIEW_CAVEAT,
    TABLE_CONVERSION_WARNINGS_KEY,
    OfficialDisclosureTableIntegrationCollisionError,
    OfficialDisclosureTableIntegrationSecretError,
    OfficialDisclosureTableIntegrationValidationError,
    integrate_table_facts_into_official_disclosure_facts,
    validate_official_disclosure_table_integration_payload,
    validate_source_table_trace,
)
import src.fundamental_skill.research_report.official_disclosure_table_integration as integration_module


def _source_document(**overrides) -> dict:
    doc = {
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
        "caveats": [],
    }
    doc.update(overrides)
    return doc


def _existing_fact(**overrides) -> dict:
    fact = {
        "fact_id": "fact_existing_main_business",
        "field_path": "basic_info.main_business_official_text",
        "value": "grid automation and industrial control",
        "unit": None,
        "period": "2025H1",
        "source_document_id": "doc_600406_2025H1_real_local",
        "source_section": "main business",
        "source_page_or_anchor": "",
        "evidence_tier": "L1_official_disclosure",
        "extraction_confidence": "medium",
        "needs_human_review": True,
        "caveats": [],
    }
    fact.update(overrides)
    return fact


def _official_payload(**overrides) -> dict:
    payload = {
        "version": OFFICIAL_DISCLOSURE_VERSION,
        "code": "600406",
        "company_name": "Guodian NARI",
        "created_at": "2026-05-29T00:00:00+00:00",
        "parser_version": PARSER_VERSION,
        "source_documents": [_source_document()],
        "extracted_facts": [_existing_fact()],
        "extraction_warnings": ["kept existing warning"],
        "data_quality_caveats": ["kept existing caveat"],
        "not_for_trading_advice": True,
    }
    payload.update(overrides)
    return payload


def _source_table(**overrides) -> dict:
    table = {
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
        "reader_warnings": [
            {"reason": "delimiter_sniffed", "detail": ""},
            {"reason": "unit_not_detected", "detail": ""},
            {"reason": "period_not_detected", "detail": ""},
        ],
        "table_quality_hint": "structured_medium",
        "table_quality_final": "structured_medium",
        "source_hash": "",
        "caveats": [LOCAL_STRUCTURED_REVIEW_CAVEAT],
    }
    table.update(overrides)
    return table


def _table_fact(**overrides) -> dict:
    fact = {
        "fact_id": "table_fact_table_600406_2025h1_product_001_revenue",
        "field_path": "business_composition.product_segment.revenue",
        "value": "12224749159.44",
        "unit": "CNY",
        "period": "2025H1",
        "source_document_id": "doc_600406_2025H1_real_local",
        "source_section": "main business by product",
        "source_page_or_anchor": "",
        "source_table_id": "table_600406_2025h1_product",
        "source_row_index": 1,
        "source_column_name": "main business revenue",
        "source_column_map": {
            "segment_name": "product name",
            "revenue": "main business revenue",
            "denominator": "main business revenue total",
        },
        "classification_type": "product",
        "segment_name": "grid automation",
        "denominator": "main business revenue total",
        "evidence_tier": "L1_official_disclosure",
        "extraction_confidence": "medium",
        "needs_human_review": True,
        "table_quality": "structured_medium",
        "caveats": [
            LOCAL_STRUCTURED_REVIEW_CAVEAT,
            "delimiter_sniffed",
            "unit_not_detected",
            "period_not_detected",
            "structured_medium_requires_human_review",
        ],
    }
    fact.update(overrides)
    return fact


def _table_caveat(**overrides) -> dict:
    caveat = {
        "reason": "unit_not_detected",
        "table_quality": "structured_medium",
        "source_section": "main business by product",
        "can_extract_numeric_values": True,
        "requires_human_review": True,
        "caveat_only": False,
        "blocked_numeric_extraction": False,
    }
    caveat.update(overrides)
    return caveat


def _conversion_warning(reason: str = "denominator_missing", **overrides) -> dict:
    warning = {"reason": reason, "detail": ""}
    warning.update(overrides)
    return warning


def _integrate(**overrides) -> dict:
    kwargs = {
        "official_payload": _official_payload(),
        "table_facts": [_table_fact()],
        "table_caveats": [_table_caveat()],
        "conversion_warnings": [
            _conversion_warning("denominator_missing"),
            _conversion_warning("unit_not_detected"),
            _conversion_warning("period_not_detected"),
            _conversion_warning("delimiter_sniffed"),
        ],
        "source_tables": [_source_table()],
    }
    kwargs.update(overrides)
    return integrate_table_facts_into_official_disclosure_facts(
        kwargs["official_payload"],
        table_facts=kwargs["table_facts"],
        table_caveats=kwargs["table_caveats"],
        conversion_warnings=kwargs["conversion_warnings"],
        source_tables=kwargs["source_tables"],
    )


def test_constants_match_design():
    assert DEFAULT_TABLE_FACT_NAMESPACE == "business_composition"


def test_integrate_valid_table_facts_into_official_payload():
    integrated = _integrate()

    validate_official_disclosure_table_integration_payload(integrated)
    assert integrated["not_for_trading_advice"] is True
    assert integrated["source_documents"] == [_source_document()]
    assert integrated["extraction_warnings"] == ["kept existing warning"]
    assert integrated["data_quality_caveats"] == ["kept existing caveat"]


def test_returns_deep_copy_and_does_not_mutate_inputs():
    official_payload = _official_payload()
    table_facts = [_table_fact()]
    table_caveats = [_table_caveat()]
    conversion_warnings = [_conversion_warning("denominator_missing")]
    source_tables = [_source_table()]
    originals = copy.deepcopy((official_payload, table_facts, table_caveats, conversion_warnings, source_tables))

    integrated = integrate_table_facts_into_official_disclosure_facts(
        official_payload,
        table_facts=table_facts,
        table_caveats=table_caveats,
        conversion_warnings=conversion_warnings,
        source_tables=source_tables,
    )
    integrated["extracted_facts"][1]["value"] = "changed"
    integrated["source_tables"][0]["headers"].append("changed")

    assert (official_payload, table_facts, table_caveats, conversion_warnings, source_tables) == originals


def test_appends_table_facts_and_preserves_existing_extracted_facts():
    integrated = _integrate()

    assert [fact["fact_id"] for fact in integrated["extracted_facts"]] == [
        "fact_existing_main_business",
        "table_fact_table_600406_2025h1_product_001_revenue",
    ]


def test_adds_source_tables_table_caveats_and_conversion_warnings():
    integrated = _integrate()

    assert integrated["source_tables"] == [_source_table()]
    assert integrated["table_caveats"][0]["reason"] == "unit_not_detected"
    assert integrated["table_caveats"][0]["source_table_id"] == "table_600406_2025h1_product"
    assert {warning["reason"] for warning in integrated[TABLE_CONVERSION_WARNINGS_KEY]} == {
        "denominator_missing",
        "unit_not_detected",
        "period_not_detected",
        "delimiter_sniffed",
    }


def test_rejects_missing_source_document():
    with pytest.raises(OfficialDisclosureTableIntegrationValidationError):
        _integrate(table_facts=[_table_fact(source_document_id="doc_missing")])


def test_rejects_fact_id_collision():
    with pytest.raises(OfficialDisclosureTableIntegrationCollisionError):
        _integrate(table_facts=[_table_fact(fact_id="fact_existing_main_business")])


def test_rejects_conflicting_source_table_id_trace():
    official_payload = _official_payload(source_tables=[_source_table()])

    with pytest.raises(OfficialDisclosureTableIntegrationCollisionError):
        _integrate(official_payload=official_payload, source_tables=[_source_table(row_count=7)])


def test_duplicate_identical_source_table_trace_is_idempotent():
    official_payload = _official_payload(source_tables=[_source_table()])
    integrated = _integrate(official_payload=official_payload, source_tables=[_source_table()])

    assert integrated["source_tables"] == [_source_table()]


@pytest.mark.parametrize("table_quality", ["unreliable_text_copy", "unusable"])
def test_rejects_table_fact_with_caveat_only_quality(table_quality):
    with pytest.raises(OfficialDisclosureTableIntegrationValidationError):
        _integrate(table_facts=[_table_fact(table_quality=table_quality)])


@pytest.mark.parametrize(
    "marker",
    [
        {"verified_fact": True},
        {"review_status": "verified"},
    ],
)
def test_rejects_verified_fact_marker(marker):
    fact = _table_fact()
    fact.update(marker)

    with pytest.raises(OfficialDisclosureTableIntegrationValidationError):
        _integrate(table_facts=[fact])


def test_rejects_field_path_outside_business_composition_namespace():
    with pytest.raises(OfficialDisclosureTableIntegrationValidationError):
        _integrate(table_facts=[_table_fact(field_path="basic_info.revenue")])


def test_rejects_table_fact_without_human_review_or_local_caveat():
    with pytest.raises(OfficialDisclosureTableIntegrationValidationError):
        _integrate(table_facts=[_table_fact(needs_human_review=False)])
    with pytest.raises(OfficialDisclosureTableIntegrationValidationError):
        _integrate(table_facts=[_table_fact(caveats=["delimiter_sniffed"])])


def test_only_table_caveats_can_be_appended_without_facts():
    integrated = _integrate(
        table_facts=[],
        table_caveats=[_table_caveat(reason="unusable_table", table_quality="unusable", can_extract_numeric_values=False, caveat_only=True, blocked_numeric_extraction=True)],
        conversion_warnings=[],
        source_tables=[_source_table(table_quality_final="unusable")],
    )

    assert integrated["extracted_facts"] == [_existing_fact()]
    assert integrated["table_caveats"][0]["reason"] == "unusable_table"


def test_source_table_trace_validates():
    validate_source_table_trace(_source_table(), valid_document_ids={"doc_600406_2025H1_real_local"})


@pytest.mark.parametrize(
    "overrides",
    [
        {"table_quality_hint": "structured_medium", "table_quality_final": "structured_medium"},
        {"table_quality_hint": "structured_high", "table_quality_final": "structured_high"},
        {"table_quality_hint": "unreliable_text_copy", "table_quality_final": "unreliable_text_copy"},
    ],
)
def test_source_table_trace_accepts_known_table_quality_values(overrides):
    validate_source_table_trace(_source_table(**overrides), valid_document_ids={"doc_600406_2025H1_real_local"})


@pytest.mark.parametrize(
    ("field", "marker"),
    [
        ("table_quality_hint", "invalid_table_quality_hint"),
        ("table_quality_final", "invalid_table_quality_final"),
    ],
)
def test_source_table_trace_rejects_invalid_table_quality_values(field, marker):
    with pytest.raises(OfficialDisclosureTableIntegrationValidationError) as exc:
        validate_source_table_trace(
            _source_table(**{field: "nonsense_quality"}),
            valid_document_ids={"doc_600406_2025H1_real_local"},
        )
    assert marker in str(exc.value)


@pytest.mark.parametrize(
    "overrides",
    [
        {"source_table_id": ""},
        {"source_document_id": "doc_missing"},
        {"source_format": ""},
        {"headers": "not-a-list"},
        {"row_count": -1},
        {"column_count": True},
    ],
)
def test_rejects_invalid_source_table_trace(overrides):
    with pytest.raises(OfficialDisclosureTableIntegrationValidationError):
        validate_source_table_trace(_source_table(**overrides), valid_document_ids={"doc_600406_2025H1_real_local"})


def test_reader_and_converter_warnings_propagate():
    integrated = _integrate()

    assert {warning["reason"] for warning in integrated["source_tables"][0]["reader_warnings"]} == {
        "delimiter_sniffed",
        "unit_not_detected",
        "period_not_detected",
    }
    assert {warning["reason"] for warning in integrated[TABLE_CONVERSION_WARNINGS_KEY]} >= {
        "denominator_missing",
        "unit_not_detected",
        "period_not_detected",
        "delimiter_sniffed",
    }


def test_denominator_unit_period_and_delimiter_caveats_propagate_to_fact():
    fact = _integrate()["extracted_facts"][1]

    assert "delimiter_sniffed" in fact["caveats"]
    assert "unit_not_detected" in fact["caveats"]
    assert "period_not_detected" in fact["caveats"]
    assert LOCAL_STRUCTURED_REVIEW_CAVEAT in fact["caveats"]


@pytest.mark.parametrize("key", ["buy", "sell", "target_price", "position", "portfolio_weight"])
def test_forbidden_recommendation_keys_rejected(key):
    fact = _table_fact()
    fact[key] = "forbidden"

    with pytest.raises(OfficialDisclosureTableIntegrationValidationError):
        _integrate(table_facts=[fact])


def test_token_like_key_and_value_rejected_with_masked_error():
    fact = _table_fact()
    fact["api_token"] = ""

    with pytest.raises(OfficialDisclosureTableIntegrationSecretError) as key_error:
        _integrate(table_facts=[fact])
    assert "<masked>" in str(key_error.value)

    warning = _conversion_warning("unit_not_detected", detail="Aa1234567890Bb1234567890Cc1234567890")
    with pytest.raises(OfficialDisclosureTableIntegrationSecretError) as value_error:
        _integrate(conversion_warnings=[warning])
    assert "<masked>" in str(value_error.value)
    assert "Aa1234567890" not in str(value_error.value)


@pytest.mark.parametrize(
    "value",
    [
        "Bearer abcdefghijklmnopqrstuvwxyz123456",
        "mcp://local/test",
        "config/.env",
        "C:\\Users\\Admin\\.ssh\\id_rsa",
    ],
)
def test_bearer_remote_control_dotenv_and_local_secret_path_rejected(value):
    with pytest.raises(OfficialDisclosureTableIntegrationSecretError):
        _integrate(source_tables=[_source_table(source_file_path=value)])


def test_static_boundary_has_no_disallowed_imports_or_calls():
    source = inspect.getsource(integration_module)
    lowered = source.lower()

    disallowed_terms = [
        "cninfo",
        "tushare",
        "akshare",
        "provider",
        "requests",
        "urllib",
        "os.environ",
        "getenv",
        "subprocess",
        "ocr",
        "pdf",
        "docx",
        "bs4",
        "beautifulsoup",
        "pandas",
        "openpyxl",
        "old_runner",
    ]
    for term in disallowed_terms:
        assert term not in lowered
    assert "import official_disclosure_parser" not in source
    assert "import business_composition_table" not in source


def test_static_boundary_has_no_real_output_writes():
    source = inspect.getsource(integration_module)

    assert ".write_text(" not in source
    assert ".write_bytes(" not in source
    assert "open(" not in source
    assert "mkdir(" not in source
