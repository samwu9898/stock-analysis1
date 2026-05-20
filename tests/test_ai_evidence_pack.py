# -*- coding: utf-8 -*-

import pytest

from src.fundamental_skill.ai_analyst.evidence_pack import EvidencePackBuilder, explain_missing_field
from scripts.audit_must_have_indicator_coverage import build_row

from tests.ai_test_fixtures import sample_fundamental, sample_raw


def test_build_evidence_pack_from_dicts():
    pack = EvidencePackBuilder().build(sample_fundamental(), sample_raw())

    assert pack["evidence_pack_version"] == "fundamental_evidence_pack.v1"
    assert pack["stock"]["code"] == "000426"
    assert pack["financial_metrics"]["gross_margin"]["display_value"] == "40.00%"
    assert pack["confidence_basis"]["risk_flags_count"] == 1
    assert pack["source_trace_summary"][0]["trace_count"] >= 1


def test_missing_raw_file_has_clear_error(tmp_path):
    fundamental = tmp_path / "fundamental_000426.json"
    fundamental.write_text("{}", encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="Required input file not found"):
        EvidencePackBuilder().build_from_files(fundamental, tmp_path / "raw_000426.json")


def test_missing_fields_do_not_crash_and_get_chinese_explanation():
    raw = sample_raw()
    raw["blocks"].pop("valuation")

    pack = EvidencePackBuilder().build(sample_fundamental(), raw)

    assert pack["valuation_metrics"] == {}
    assert "应收账款" in explain_missing_field("financial_metrics.accounts_receivable")


def test_resource_swing_generates_commodity_indicator():
    pack = EvidencePackBuilder().build(sample_fundamental("resource_swing"), sample_raw())

    indicators = pack["enhanced_must_track_indicators"]
    commodity = [item for item in indicators if item["indicator_name"] == "核心商品价格"][0]
    assert commodity["current_status"] == "available"
    assert commodity["affects_dimension"] == "industry_cycle"
    assert commodity["priority"] in {"medium", "high", "low"}
    assert commodity["follow_up_question"]


def test_advanced_manufacturing_generates_receivable_new_business_major_customer():
    pack = EvidencePackBuilder().build(sample_fundamental("advanced_manufacturing_growth"), sample_raw())
    names = {item["indicator_name"]: item for item in pack["enhanced_must_track_indicators"]}

    assert names["新业务收入或订单"]["current_status"] == "missing"
    assert names["大客户收入占比"]["current_status"] == "missing"
    assert names["应收账款"]["source"] == "financial_indicator"
    assert names["应收账款"]["current_status"] == "available"
    assert names["存货"]["current_status"] == "available"
    assert names["合同负债"]["current_status"] == "partial_proxy"


def test_semiconductor_generates_inventory_order_rd_items():
    pack = EvidencePackBuilder().build(sample_fundamental("semiconductor_cycle"), sample_raw())
    names = {item["indicator_name"]: item for item in pack["enhanced_must_track_indicators"]}

    assert {"存货", "订单 / 合同负债", "研发费用率", "资本开支"}.issubset(names)
    assert names["订单 / 合同负债"]["current_status"] == "partial_proxy"
    assert names["订单 / 合同负债"]["scope_note"] == "合同负债可作为订单可见度 proxy，但不等同于真实订单或 backlog。"
    assert names["研发费用率"]["current_status"] == "available"
    assert names["资本开支"]["current_status"] == "available"


def test_ratio_fields_get_display_values_and_unit_assumptions():
    raw = sample_raw()
    raw["blocks"]["financial_indicator"][0]["gross_margin"] = 27.796688
    raw["blocks"]["business_composition"][0]["gross_margin"] = 0.28777
    raw["blocks"]["business_composition"][0]["revenue_ratio"] = 0.599281

    pack = EvidencePackBuilder().build(sample_fundamental(), raw)

    assert pack["financial_metrics"]["gross_margin"]["display_value"] == "27.80%"
    assert pack["business_composition"][0]["gross_margin"]["display_value"] == "28.78%"
    assert pack["business_composition"][0]["revenue_ratio"]["display_value"] == "59.93%"
    assert "unit_assumption" in pack["financial_metrics"]["revenue_yoy"]
    assert "unit_assumption" in pack["financial_metrics"]["net_profit_yoy"]


def test_v23a_evidence_pack_reads_rd_capex_fields_and_keeps_exclusions():
    pack = EvidencePackBuilder().build(sample_fundamental("advanced_manufacturing_growth"), sample_raw())
    financial = pack["financial_metrics"]
    names = {item["indicator_name"]: item for item in pack["enhanced_must_track_indicators"]}

    assert financial["r_and_d_expense"] == 17755979.09
    assert financial["r_and_d_expense_ratio"]["raw_value"] == 0.8336652584671204
    assert financial["r_and_d_expense_ratio"]["display_value"] == "0.83%"
    assert financial["r_and_d_expense_ratio"]["unit_confidence"] == "high"
    assert financial["capex"] == 229152931.6
    assert "capex_ratio" not in financial
    assert "depreciation_amortization" not in financial
    assert names["研发费用率"]["current_status"] == "available"
    assert names["新业务收入或订单"]["current_status"] == "missing"
    assert names["大客户收入占比"]["current_status"] == "missing"
    assert not any(item["evidence_name"] == "研发费用率" for item in pack["unknown_or_missing_evidence"])


def test_must_have_audit_counts_v23a_rd_capex_as_available():
    fundamental = sample_fundamental("semiconductor_cycle")
    pack = EvidencePackBuilder().build(fundamental, sample_raw())

    rd_row = build_row(pack, fundamental, "研发费用率")
    capex_row = build_row(pack, fundamental, "资本开支")

    assert rd_row["coverage_status"] == "available"
    assert capex_row["coverage_status"] == "available"


def test_confidence_breakdown_and_evidence_classification_are_populated():
    pack = EvidencePackBuilder().build(sample_fundamental(), sample_raw())

    breakdown = pack["confidence_basis"]["confidence_breakdown"]
    assert len(breakdown) >= 5
    assert {item["dimension"] for item in breakdown} >= {
        "data_coverage",
        "financial_quality",
        "valuation_interpretability",
        "growth_validation",
        "risk_identifiability",
    }
    assert pack["supporting_evidence"]
    assert pack["limiting_evidence"]
    assert pack["unknown_or_missing_evidence"]
