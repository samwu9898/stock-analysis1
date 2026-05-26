# -*- coding: utf-8 -*-

from src.fundamental_skill.data_providers.diff_classifier import (
    DiffCategory,
    build_diff_report,
    classify_field_diff,
    make_diff_item,
)


def _assert_secret_not_rendered(secret: str, text: str) -> None:
    if secret in text:
        raise AssertionError("secret-like value was rendered")


def test_exact_match_category():
    item = classify_field_diff("raw.blocks.basic_info", [{"name": "A"}], [{"name": "A"}])

    assert item.category == DiffCategory.EXACT_MATCH.value
    assert item.severity == "info"
    assert item.review_required is False


def test_drift_categories_require_manual_review():
    for field_path, category in [
        ("fundamental.strategy_type", DiffCategory.STRATEGY_TYPE_DRIFT),
        ("fundamental.sub_type", DiffCategory.CLASSIFICATION_DRIFT),
        ("fundamental.confidence", DiffCategory.CONFIDENCE_DRIFT),
        ("fundamental.fundamental_score", DiffCategory.SCORE_DRIFT),
        ("research_questions_p1.questions", DiffCategory.P1_QUESTION_DRIFT),
    ]:
        item = classify_field_diff(field_path, "left", "right")
        assert item.category == category.value
        assert item.review_required is True
        assert item.severity == "blocker"


def test_missing_field_improvement_and_regression():
    improvement = classify_field_diff("evidence_pack.financial_metrics.roe", None, 10.5)
    regression = classify_field_diff("evidence_pack.financial_metrics.roe", 10.5, None)

    assert improvement.category == DiffCategory.MISSING_FIELD_IMPROVEMENT.value
    assert improvement.review_required is False
    assert regression.category == DiffCategory.MISSING_FIELD_REGRESSION.value
    assert regression.review_required is True


def test_permission_and_failed_akshare_categories():
    permission = classify_field_diff(
        "raw.blocks.business_composition",
        [{"segment_name": "core"}],
        [],
        tushare_status={"success": False, "error": "permission denied"},
    )
    failed_akshare = classify_field_diff(
        "raw.blocks.valuation",
        None,
        [{"pe_ttm": 20}],
        akshare_status={"success": False, "error": "failed"},
    )

    assert permission.category == DiffCategory.TUSHARE_PERMISSION_MISSING.value
    assert failed_akshare.category == DiffCategory.STALE_OR_FAILED_AKSHARE_FIELD.value


def test_token_risk_is_blocker_and_masks_values():
    fake_secret = "FAKE_TOKEN_FOR_TESTING_ONLY__NOT_REAL__XYZ_1234567890"
    item = classify_field_diff("raw.fetch_status.error", f"token={fake_secret}", "ok")

    assert item.category == DiffCategory.TOKEN_OR_SECRET_RISK.value
    assert item.severity == "blocker"
    assert item.review_required is True
    _assert_secret_not_rendered(fake_secret, str(item))


def test_make_diff_item_supports_all_required_categories():
    categories = [
        "exact_match",
        "expected_provider_difference",
        "harmless_format_difference",
        "unit_difference",
        "missing_field_improvement",
        "missing_field_regression",
        "stale_or_failed_akshare_field",
        "tushare_permission_missing",
        "canonical_mapping_issue",
        "strategy_type_drift",
        "classification_drift",
        "confidence_drift",
        "score_drift",
        "P1_question_drift",
        "safety_boundary_risk",
        "token_or_secret_risk",
    ]

    for category in categories:
        item = make_diff_item(category, "field", "a", "b")
        assert item.category == category
        assert set(item.to_dict()) == {
            "category",
            "field_path",
            "akshare_value",
            "tushare_value",
            "severity",
            "review_required",
            "note",
        }


def test_build_diff_report_disables_automatic_acceptance():
    raw = {"meta": {}, "blocks": {}, "fetch_status": {}, "errors": []}

    report = build_diff_report(code="600406", akshare_raw=raw, tushare_raw=raw)

    assert report["automatic_acceptance"] is False
    assert "summary" in report
