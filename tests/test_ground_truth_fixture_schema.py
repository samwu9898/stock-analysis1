# -*- coding: utf-8 -*-

import json
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "ground_truth"
    / "fundamental_ground_truth_v1.json"
)

EXPECTED_CODES = {
    "600406",
    "002050",
    "002371",
    "603259",
    "000426",
    "002837",
    "002028",
    "601689",
    "300442",
    "601698",
    "601899",
    "300308",
}

REQUIRED_SAMPLE_KEYS = {
    "code",
    "name",
    "strategy_type_expected",
    "sample_role",
    "fields",
    "source_refs",
    "tolerance",
    "manual_review_notes",
    "audit_status",
}

REQUIRED_FIELD_GROUPS = {
    "basic_info",
    "financial_metrics",
    "valuation_metrics",
    "business_composition",
}

REQUIRED_BASIC_INFO_FIELDS = {
    "stock_code",
    "stock_name",
    "industry",
    "listing_date",
    "main_business",
}

REQUIRED_FINANCIAL_FIELDS = {
    "period",
    "revenue",
    "revenue_yoy",
    "net_profit",
    "net_profit_yoy",
    "deducted_net_profit",
    "gross_margin",
    "net_margin",
    "roe",
    "operating_cashflow",
    "debt_to_asset",
    "inventory",
    "accounts_receivable",
    "contract_liabilities",
    "r_and_d_expense",
    "r_and_d_expense_ratio",
    "capex",
}

REQUIRED_VALUATION_FIELDS = {
    "as_of_date",
    "pe_ttm",
    "pb",
    "ps",
    "market_cap",
    "dividend_yield",
}

REQUIRED_BUSINESS_COMPOSITION_FIELDS = {
    "period",
    "classification_type",
    "segment_name",
    "revenue",
    "revenue_ratio",
    "gross_margin",
    "cost",
    "profit",
    "profit_ratio",
}

REQUIRED_FIELD_OBJECT_KEYS = {
    "value",
    "source_ref",
    "data_unit",
    "canonical_unit",
    "confidence_of_ground_truth",
    "missing_category",
    "manual_review_note",
}

REQUIRED_TOLERANCE_KEYS = {
    "amount_relative_pct",
    "amount_absolute_floor_rmb",
    "ratio_pct_point",
    "business_revenue_ratio_pct_point",
    "valuation_policy",
    "text_policy",
}

FORBIDDEN_SENSITIVE_TEXT = (
    "TUSHARE_" + "TOKEN=",
    "api.tushare.pro/" + "mcp",
    "mcp" + "://",
    "mcp" + "?",
    "C:" + "\\Users\\",
    "C:" + "/Users/",
    "out" + "put/",
    "out" + "put\\",
    "provider_" + "comparison",
)

FORBIDDEN_RECOMMENDATION_KEYS = {
    "bu" + "y",
    "se" + "ll",
    "target_" + "price",
    "posi" + "tion",
    "stop_" + "loss",
    "take_" + "profit",
    "portfolio_" + "weight",
}

FORBIDDEN_RECOMMENDATION_TEXT = (
    "bu" + "y advice",
    "se" + "ll advice",
    "target " + "price",
    "posi" + "tion sizing",
    "买" + "入",
    "卖" + "出",
    "目标" + "价",
    "仓" + "位",
)


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _samples_by_code() -> dict:
    return {sample["code"]: sample for sample in _load_fixture()["samples"]}


def _walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _assert_field_object(field_object: dict) -> None:
    assert isinstance(field_object, dict)
    assert REQUIRED_FIELD_OBJECT_KEYS <= set(field_object)


def test_ground_truth_fixture_json_parses_and_has_expected_sample_pool():
    payload = _load_fixture()

    assert payload["version"] == "fundamental_ground_truth.v1"
    assert payload["created_at"]
    assert "scope" in payload
    assert payload["scope"]["not_for_trading_advice"] is True
    assert payload["scope"]["does_not_modify_scoring"] is True
    assert len(payload["samples"]) == 12
    assert {sample["code"] for sample in payload["samples"]} == EXPECTED_CODES


def test_each_sample_has_required_top_level_keys_and_draft_status():
    for sample in _load_fixture()["samples"]:
        assert REQUIRED_SAMPLE_KEYS <= set(sample)
        assert sample["audit_status"] == "draft_manual_review_required"
        assert sample["manual_review_notes"]
        assert sample["source_refs"] == {}
        assert REQUIRED_TOLERANCE_KEYS <= set(sample["tolerance"])


def test_each_sample_has_required_field_groups_and_field_objects():
    for sample in _load_fixture()["samples"]:
        fields = sample["fields"]

        assert REQUIRED_FIELD_GROUPS <= set(fields)
        assert REQUIRED_BASIC_INFO_FIELDS <= set(fields["basic_info"])
        assert REQUIRED_FINANCIAL_FIELDS <= set(fields["financial_metrics"])
        assert REQUIRED_VALUATION_FIELDS <= set(fields["valuation_metrics"])
        assert isinstance(fields["business_composition"], list)

        for field_name in REQUIRED_BASIC_INFO_FIELDS:
            _assert_field_object(fields["basic_info"][field_name])
        for field_name in REQUIRED_FINANCIAL_FIELDS:
            _assert_field_object(fields["financial_metrics"][field_name])
        for field_name in REQUIRED_VALUATION_FIELDS:
            _assert_field_object(fields["valuation_metrics"][field_name])
        for row in fields["business_composition"]:
            assert REQUIRED_BUSINESS_COMPOSITION_FIELDS <= set(row)
            for field_name in REQUIRED_BUSINESS_COMPOSITION_FIELDS:
                _assert_field_object(row[field_name])


def test_financial_and_business_values_remain_unfilled_in_skeleton():
    for sample in _load_fixture()["samples"]:
        fields = sample["fields"]

        assert fields["basic_info"]["stock_code"]["value"] == sample["code"]
        assert fields["basic_info"]["stock_name"]["value"] == sample["name"]
        for field_name in ("industry", "listing_date", "main_business"):
            assert fields["basic_info"][field_name]["value"] is None

        for field_object in fields["financial_metrics"].values():
            assert field_object["value"] is None
        for field_object in fields["valuation_metrics"].values():
            assert field_object["value"] is None
        for row in fields["business_composition"]:
            for field_object in row.values():
                assert field_object["value"] is None


def test_fixture_contains_no_tokens_mcp_urls_secret_paths_or_output_paths():
    text = FIXTURE_PATH.read_text(encoding="utf-8")
    lowered = text.lower()

    for forbidden in FORBIDDEN_SENSITIVE_TEXT:
        assert forbidden.lower() not in lowered


def test_fixture_contains_no_recommendation_fields_or_advice_text():
    payload = _load_fixture()
    text = json.dumps(payload, ensure_ascii=False).lower()

    for key in _walk_keys(payload):
        assert key.lower() not in FORBIDDEN_RECOMMENDATION_KEYS
    for forbidden_text in FORBIDDEN_RECOMMENDATION_TEXT:
        assert forbidden_text.lower() not in text


def test_boundary_and_excluded_samples_are_not_current_p1_1_positive_support():
    samples = _samples_by_code()

    for code in ("002028", "601689"):
        sample = samples[code]
        assert sample["sample_role"] == "boundary_validation"
        assert sample["p1_1_support_status"] == "validation_only_not_first_version_positive_support"

    assert samples["601899"]["sample_role"] == "caveat_excluded_for_p1_1_v1"
    assert samples["601899"]["p1_1_support_status"] == "excluded_resource_core_design_only"
    assert samples["300308"]["sample_role"] == "boundary_excluded_from_current_p1_1_slices"
    assert samples["300308"]["p1_1_support_status"] == "excluded_from_current_p1_1_slices"
