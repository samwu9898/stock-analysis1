# -*- coding: utf-8 -*-

import inspect
from pathlib import Path

import pytest

from src.fundamental_skill.research_report.business_composition_table import (
    BUSINESS_COMPOSITION_SECTION_DETECTED,
    BUSINESS_COMPOSITION_TABLE_FACT_VERSION,
    CLASSIFICATION_TYPE_VALUES,
    EVIDENCE_TIER_VALUES,
    EXTRACTION_CONFIDENCE_VALUES,
    TABLE_QUALITY_VALUES,
    TABLE_STRUCTURE_UNRELIABLE_DUE_TO_PDF_TEXT_COPY,
    BusinessCompositionTableQualityError,
    BusinessCompositionTableSecretError,
    BusinessCompositionTableValidationError,
    build_business_composition_table_facts,
    build_table_caveat,
    build_table_fact,
    build_unreliable_text_copy_caveat,
    get_table_quality_policy,
    is_numeric_extraction_allowed,
    validate_business_composition_table_facts,
    validate_table_fact,
)
import src.fundamental_skill.research_report.business_composition_table as table_module


def _fact(**overrides) -> dict:
    fact = {
        "fact_id": "fact_table_001_row_001",
        "field_path": "business_composition.product_segment.revenue",
        "value": 12224749159.44,
        "unit": "CNY",
        "period": "2025H1",
        "source_document_id": "doc_001",
        "source_section": "main business by product",
        "source_page_or_anchor": "",
        "source_table_id": "table_001",
        "source_row_index": 1,
        "source_column_name": "main business revenue",
        "source_column_map": {
            "segment_name": "product name",
            "revenue": "main business revenue",
            "denominator": "total row",
        },
        "classification_type": "product",
        "segment_name": "grid automation",
        "denominator": "main business revenue total",
        "evidence_tier": "L1_official_disclosure",
        "extraction_confidence": "high",
        "needs_human_review": False,
        "table_quality": "structured_high",
        "caveats": [],
    }
    fact.update(overrides)
    return fact


def test_constants_match_design_values():
    assert BUSINESS_COMPOSITION_TABLE_FACT_VERSION == "business_composition_table_facts.v1"
    assert TABLE_QUALITY_VALUES == {
        "structured_high",
        "structured_medium",
        "partially_structured",
        "unreliable_text_copy",
        "unusable",
    }
    assert CLASSIFICATION_TYPE_VALUES == {"industry", "product", "region", "other"}
    assert EVIDENCE_TIER_VALUES == {
        "L1_official_disclosure",
        "L2_multi_source_consistent",
        "L3_single_source_candidate",
        "L4_unsupported_or_missing",
    }
    assert EXTRACTION_CONFIDENCE_VALUES == {"high", "medium", "low"}


def test_table_quality_policies():
    high = get_table_quality_policy("structured_high")
    medium = get_table_quality_policy("structured_medium")
    partial = get_table_quality_policy("partially_structured")
    text_copy = get_table_quality_policy("unreliable_text_copy")
    unusable = get_table_quality_policy("unusable")

    assert high["can_extract_numeric_values"] is True
    assert high["requires_human_review"] is False
    assert high["l1_candidate_eligible"] is True
    assert high["candidate_generator_eligible"] is True
    assert high["caveat_only"] is False
    assert medium["requires_human_review"] is True
    assert medium["requires_caveat"] is True
    assert medium["l1_candidate_eligible"] is True
    assert medium["requires_accepted_policy"] is True
    assert partial["can_extract_numeric_values"] is True
    assert partial["limited_fields_only"] is True
    assert partial["candidate_generator_eligible"] is False
    assert text_copy["can_extract_numeric_values"] is False
    assert text_copy["caveat_only"] is True
    assert unusable["can_extract_numeric_values"] is False
    assert unusable["caveat_only"] is True


def test_invalid_table_quality_policy_rejected():
    with pytest.raises(BusinessCompositionTableQualityError):
        get_table_quality_policy("free_text")


def test_structured_high_allows_numeric_extraction():
    assert is_numeric_extraction_allowed("structured_high") is True


def test_structured_medium_allows_numeric_extraction_with_human_review():
    assert is_numeric_extraction_allowed("structured_medium") is True

    fact = _fact(
        fact_id="fact_structured_medium",
        table_quality="structured_medium",
        needs_human_review=True,
        extraction_confidence="medium",
        caveats=["Structured table needs accepted policy review before downstream use."],
    )
    validate_table_fact(fact)


def test_partially_structured_limited_policy():
    policy = get_table_quality_policy("partially_structured")

    assert is_numeric_extraction_allowed("partially_structured") is True
    assert policy["limited_fields_only"] is True
    assert policy["requires_human_review"] is True
    assert policy["l1_candidate_eligible"] is False
    assert policy["candidate_generator_eligible"] is False


def test_partially_structured_valid_fact_still_passes():
    fact = _fact(
        fact_id="fact_partially_structured",
        table_quality="partially_structured",
        needs_human_review=True,
        extraction_confidence="medium",
        caveats=["Only fields with explicit row and column alignment are retained."],
    )

    validate_table_fact(fact)


def test_unreliable_text_copy_disallows_numeric_extraction():
    assert is_numeric_extraction_allowed("unreliable_text_copy") is False


def test_unusable_disallows_numeric_extraction():
    assert is_numeric_extraction_allowed("unusable") is False


def test_build_valid_product_revenue_fact():
    fact = build_table_fact(**_fact())

    assert fact["field_path"] == "business_composition.product_segment.revenue"
    assert fact["classification_type"] == "product"
    assert fact["segment_name"] == "grid automation"
    assert fact["value"] == 12224749159.44


def test_validate_valid_fact():
    validate_table_fact(_fact())


def test_fact_includes_source_column_map():
    fact = build_table_fact(**_fact())

    assert fact["source_column_map"] == {
        "segment_name": "product name",
        "revenue": "main business revenue",
        "denominator": "total row",
    }


def test_reject_missing_source_table_id():
    fact = _fact(source_table_id="")

    with pytest.raises(BusinessCompositionTableValidationError):
        validate_table_fact(fact)


@pytest.mark.parametrize(
    "overrides",
    [
        {"source_row_index": -1},
        {"source_column_name": ""},
    ],
)
def test_reject_missing_row_column_location(overrides):
    fact = _fact(**overrides)

    with pytest.raises(BusinessCompositionTableValidationError):
        validate_table_fact(fact)


def test_reject_invalid_classification_type():
    fact = _fact(classification_type="strategy")

    with pytest.raises(BusinessCompositionTableValidationError):
        validate_table_fact(fact)


def test_reject_invalid_evidence_tier():
    fact = _fact(evidence_tier="L0_guess")

    with pytest.raises(BusinessCompositionTableValidationError):
        validate_table_fact(fact)


def test_reject_invalid_extraction_confidence():
    fact = _fact(extraction_confidence="certain")

    with pytest.raises(BusinessCompositionTableValidationError):
        validate_table_fact(fact)


def test_reject_invalid_table_quality():
    fact = _fact(table_quality="raw_text")

    with pytest.raises(BusinessCompositionTableValidationError):
        validate_table_fact(fact)


def test_reject_non_bool_needs_human_review():
    fact = _fact(needs_human_review="yes")

    with pytest.raises(BusinessCompositionTableValidationError):
        validate_table_fact(fact)


def test_reject_empty_source_column_map():
    fact = _fact(source_column_map={})

    with pytest.raises(BusinessCompositionTableValidationError):
        validate_table_fact(fact)


def test_reject_l1_without_unit():
    fact = _fact(unit=None)

    with pytest.raises(BusinessCompositionTableValidationError):
        validate_table_fact(fact)


def test_reject_l1_without_denominator_or_caveat():
    fact = _fact(denominator=None, caveats=[])

    with pytest.raises(BusinessCompositionTableValidationError):
        validate_table_fact(fact)


def test_l1_allows_missing_denominator_when_caveat_is_present():
    fact = _fact(
        denominator=None,
        caveats=["Denominator is visible only in an adjacent total row and needs manual confirmation."],
    )

    validate_table_fact(fact)


@pytest.mark.parametrize("value", [123.45, "123.45", {"revenue": 123.45}])
def test_reject_numeric_value_for_unreliable_text_copy(value):
    fact = _fact(
        value=value,
        table_quality="unreliable_text_copy",
        needs_human_review=True,
        extraction_confidence="low",
        caveats=["Copied text does not preserve row or column structure."],
    )

    with pytest.raises(BusinessCompositionTableValidationError):
        validate_table_fact(fact)


@pytest.mark.parametrize("value", [BUSINESS_COMPOSITION_SECTION_DETECTED, None])
def test_unreliable_text_copy_table_fact_rejected_even_when_value_is_nonnumeric_or_none(value):
    fact = _fact(
        fact_id="fact_section_detected",
        field_path="business_composition.section_detected",
        value=value,
        unit="section",
        table_quality="unreliable_text_copy",
        needs_human_review=True,
        extraction_confidence="low",
        caveats=["Copied text does not preserve row or column structure."],
    )

    with pytest.raises(BusinessCompositionTableValidationError, match="caveat-only"):
        validate_table_fact(fact)


@pytest.mark.parametrize("value", ["business_composition_table_unusable", None])
def test_unusable_table_fact_rejected_even_when_value_is_nonnumeric_or_none(value):
    fact = _fact(
        fact_id="fact_unusable",
        field_path="business_composition.table_unusable",
        value=value,
        unit="section",
        table_quality="unusable",
        needs_human_review=True,
        extraction_confidence="low",
        caveats=["Table structure is unusable for fact extraction."],
    )

    with pytest.raises(BusinessCompositionTableValidationError, match="caveat-only"):
        validate_table_fact(fact)


@pytest.mark.parametrize("key", ["buy", "sell", "target_price", "position", "portfolio_weight"])
def test_reject_forbidden_recommendation_keys(key):
    fact = _fact()
    fact[key] = "forbidden"

    with pytest.raises(BusinessCompositionTableValidationError):
        validate_table_fact(fact)


def test_reject_token_like_key():
    fact = _fact()
    fact["api_token"] = ""

    with pytest.raises(BusinessCompositionTableSecretError) as exc_info:
        validate_table_fact(fact)

    assert "api_token" not in str(exc_info.value)
    assert "<masked>" in str(exc_info.value)


def test_reject_token_like_value():
    secret_like = "Aa1234567890Bb1234567890Cc1234567890"
    fact = _fact(caveats=[secret_like])

    with pytest.raises(BusinessCompositionTableSecretError) as exc_info:
        validate_table_fact(fact)

    assert secret_like not in str(exc_info.value)
    assert "<masked>" in str(exc_info.value)


@pytest.mark.parametrize(
    "value",
    [
        "Bearer abcdefghijklmnopqrstuvwxyz123456",
        "mcp://local/test",
        "config/.env",
        "C:\\Users\\Admin\\.ssh\\id_rsa",
    ],
)
def test_reject_bearer_remote_control_dotenv_and_local_secret_path(value):
    fact = _fact(caveats=[value])

    with pytest.raises(BusinessCompositionTableSecretError) as exc_info:
        validate_table_fact(fact)

    assert value not in str(exc_info.value)
    assert "<masked>" in str(exc_info.value)


def test_build_unreliable_text_copy_caveat():
    caveat = build_unreliable_text_copy_caveat(source_section="main business by product")

    assert caveat["reason"] == TABLE_STRUCTURE_UNRELIABLE_DUE_TO_PDF_TEXT_COPY
    assert caveat["detected_signal"] == BUSINESS_COMPOSITION_SECTION_DETECTED
    assert caveat["table_quality"] == "unreliable_text_copy"
    assert caveat["blocked_numeric_extraction"] is True
    assert caveat["can_extract_numeric_values"] is False


def test_caveat_can_express_business_composition_section_detected():
    caveat = build_table_caveat(
        reason=BUSINESS_COMPOSITION_SECTION_DETECTED,
        table_quality="unreliable_text_copy",
        source_section="main business by product",
    )

    assert caveat["reason"] == BUSINESS_COMPOSITION_SECTION_DETECTED
    assert caveat["blocked_numeric_extraction"] is True


def test_table_caveat_can_express_unreliable_pdf_text_copy():
    caveat = build_table_caveat(
        reason=TABLE_STRUCTURE_UNRELIABLE_DUE_TO_PDF_TEXT_COPY,
        table_quality="unreliable_text_copy",
        source_section="main business by product",
    )

    assert caveat["reason"] == TABLE_STRUCTURE_UNRELIABLE_DUE_TO_PDF_TEXT_COPY
    assert caveat["blocked_numeric_extraction"] is True


def test_caveat_does_not_include_numeric_value():
    caveat = build_unreliable_text_copy_caveat(source_section="main business by product")

    assert "value" not in caveat
    assert not any(isinstance(value, (int, float)) and not isinstance(value, bool) for value in caveat.values())


def test_caveat_helper_does_not_include_business_composition_numeric_fact_fields():
    caveat = build_unreliable_text_copy_caveat(source_section="main business by product")
    numeric_fact_fields = {
        "revenue",
        "cost",
        "gross_margin",
        "revenue_ratio",
        "revenue_yoy",
        "cost_yoy",
        "gross_margin_yoy_change",
        "segment_name",
        "value",
    }

    assert numeric_fact_fields.isdisjoint(caveat)


def test_build_and_validate_top_level_payload():
    fact = _fact()
    caveat = build_table_caveat(
        reason="structured_medium_requires_manual_total_check",
        table_quality="structured_medium",
        source_section="main business by product",
    )

    payload = build_business_composition_table_facts(
        code="600406",
        company_name="NARI Technology",
        source_document_id="doc_001",
        table_facts=[fact],
        table_caveats=[caveat],
        created_at="2026-05-28T00:00:00+00:00",
    )

    assert payload["version"] == BUSINESS_COMPOSITION_TABLE_FACT_VERSION
    assert payload["not_for_trading_advice"] is True
    validate_business_composition_table_facts(payload)


def test_top_level_payload_rejects_mismatched_source_document_id():
    payload = {
        "version": BUSINESS_COMPOSITION_TABLE_FACT_VERSION,
        "code": "600406",
        "company_name": "NARI Technology",
        "created_at": "2026-05-28T00:00:00+00:00",
        "source_document_id": "doc_002",
        "table_facts": [_fact()],
        "table_caveats": [],
        "not_for_trading_advice": True,
    }

    with pytest.raises(BusinessCompositionTableValidationError):
        validate_business_composition_table_facts(payload)


def test_no_runtime_boundary_imports_or_calls():
    source = inspect.getsource(table_module)
    forbidden = [
        "CNInfo",
        "Tushare",
        "AkShare",
        "provider",
        "MCP",
        "requests",
        "urllib",
        "os.environ",
        "getenv",
        "subprocess",
        "OCR",
        "pytesseract",
        "easyocr",
        "pdfplumber",
        "camelot",
        "tabula",
        "PyPDF",
        "pypdf",
        "pdfminer",
        "docx",
        "bs4",
        "BeautifulSoup",
        "pandas",
        "openpyxl",
        "old runner",
        "TUSHARE_TOKEN",
    ]

    for marker in forbidden:
        assert marker not in source


def test_no_reader_or_writer_entrypoints():
    public_names = {name for name in dir(table_module) if not name.startswith("_")}

    assert not any(name.startswith("read_") for name in public_names)
    assert not any(name.startswith("write_") for name in public_names)


def test_no_real_output_writes():
    output_roots = [
        Path("output/official_disclosures/business_composition_table_facts.json"),
        Path("output/business_composition_table_facts.json"),
    ]

    for path in output_roots:
        assert not path.exists()
