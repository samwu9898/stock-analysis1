# -*- coding: utf-8 -*-

import json
from pathlib import Path

from dashboard.fundamental_dashboard import stock_selector_table_rows
from src.fundamental_skill import dashboard_helpers as helpers


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def sample_fundamental() -> dict:
    return {
        "stock_code": "000426",
        "stock_name": "sample",
        "strategy_type": "resource_swing",
        "status": "supportive",
        "confidence": "high",
        "fundamental_score": 76,
        "analyst_summary": "new neutral summary",
        "trader_summary": "legacy summary",
        "analysis_date": "2026-05-18",
        "risk_flags": [
            {
                "name": "risk A",
                "severity": "medium",
                "monitor_method": "watch data",
                "evidence": [{"source": "unit", "interpretation": "sample evidence"}],
            }
        ],
        "must_track_indicators": [
            {
                "name": "indicator A",
                "current_value": 1.2,
                "monitor_frequency": "weekly",
                "reason": "important",
            }
        ],
        "missing_fields": ["field.a"],
        "financial_quality": {"score": 60},
        "valuation_view": {"valuation_level": "reasonable", "score": 50},
        "invalidation_conditions": [
            {
                "condition": "condition",
                "evidence_needed": "evidence",
                "downstream_review_hint": "需要后续分析层复核",
                "action_hint_for_trader": "需要后续分析层复核",
            }
        ],
    }


def sample_raw() -> dict:
    return {
        "blocks": {
            "financial_indicator": [
                {
                    "revenue_yoy": 1,
                    "net_profit_yoy": 2,
                    "deducted_net_profit": 3,
                    "gross_margin": 4,
                    "net_margin": 5,
                    "roe": 6,
                    "operating_cashflow": 7,
                    "debt_to_asset": 8,
                    "inventory": 9,
                    "accounts_receivable": 10,
                }
            ],
            "valuation": [{"pe_ttm": 11, "pb": 12, "ps": 13, "market_cap": 14, "dividend_yield": None}],
            "business_composition": [
                {
                    "segment_name": "segment A",
                    "classification_type": "product",
                    "revenue": 100,
                    "revenue_ratio": 0.5,
                    "gross_margin": 0.2,
                    "cost": 80,
                    "profit": 20,
                    "period": "2025",
                }
            ],
            "commodity_prices": [
                {
                    "commodity_name": "copper",
                    "commodity_name_cn": "copper cn",
                    "symbol": "CU0",
                    "price": 70000,
                    "date": "2026-05-18",
                    "market": "domestic",
                    "source_function": "futures",
                    "source_priority": "primary",
                    "freshness_days": 0,
                    "is_stale": False,
                    "readiness_eligible": True,
                    "warnings": [],
                }
            ],
        },
        "fetch_status": {
            "basic_info": {
                "success": True,
                "error": None,
                "missing_fields": [],
                "warnings": [],
                "source_trace": [{"field_name": "stock_name"}],
            }
        },
        "errors": [],
    }


def sample_ai_report() -> dict:
    return {
        "ai_report_version": "fundamental_ai_report.v1",
        "stock_code": "000426",
        "stock_name": "sample",
        "fundamental_view": "supportive_for_further_evaluation",
        "executive_summary": "one sentence",
        "confidence_explanation": "confidence details",
        "confidence_breakdown": [
            {"dimension": "data_coverage", "level": "strong", "reason": "ok"},
            {"dimension": "financial_quality", "level": "medium", "reason": "some gaps"},
        ],
        "supporting_evidence": [
            {
                "evidence_name": "support A",
                "evidence_value": "value A",
                "why_it_matters": "important",
                "affects_dimension": "financial_quality",
                "source": "unit",
                "confidence_effect": "supportive",
            }
        ],
        "limiting_evidence": [
            {
                "evidence_name": "limit A",
                "evidence_value": "value B",
                "why_it_matters": "limits",
                "affects_dimension": "valuation",
                "source": "unit",
                "confidence_effect": "limits_confidence",
            }
        ],
        "unknown_or_missing_evidence": [
            {
                "evidence_name": "unknown A",
                "evidence_value": None,
                "why_it_matters": "missing",
                "affects_dimension": "growth_validation",
                "source": "missing_fields",
                "confidence_effect": "unknown",
            }
        ],
        "business_analysis": "business",
        "financial_quality_analysis": "financial",
        "valuation_analysis": "valuation",
        "industry_cycle_analysis": "industry",
        "risk_analysis": [{"risk_name": "risk A", "severity": "medium", "analysis": "risk"}],
        "must_track_analysis": [],
        "data_limitations": ["limit"],
        "invalidation_watch": [{"condition": "condition", "evidence_needed": "evidence"}],
        "final_summary": "final",
    }


def sample_evidence_pack() -> dict:
    return {
        "evidence_pack_version": "fundamental_evidence_pack.v1",
        "stock": {"code": "000426", "name": "sample", "strategy_type": "resource_swing"},
        "confidence_basis": {
            "status": "supportive",
            "confidence": "high",
            "score": 76,
            "risk_flags_count": 1,
            "confidence_breakdown": [
                {"dimension": "data_coverage", "level": "strong", "reason": "ok"}
            ],
        },
        "enhanced_must_track_indicators": [
            {
                "indicator_name": "medium item",
                "priority": "medium",
                "current_value": {"display_value": "1.00%"},
                "current_status": "available",
                "why_it_matters": "medium",
                "source": "unit",
                "source_date": "2026",
                "related_risk": None,
                "affects_dimension": "financial_quality",
                "follow_up_question": "watch",
            },
            {
                "indicator_name": "high item",
                "priority": "high",
                "current_value": None,
                "current_status": "missing",
                "why_it_matters": "high",
                "source": "unit",
                "source_date": None,
                "related_risk": "risk",
                "affects_dimension": "growth_validation",
                "follow_up_question": "fill data",
            },
        ],
        "source_trace_summary": [{"block_name": "basic_info", "trace_count": 1}],
        "missing_fields": [{"field": "field.a", "explanation": "missing"}],
        "data_limitations": ["limit"],
    }


def test_scan_fundamental_results_loads_output_files(tmp_path):
    write_json(tmp_path / "fundamental_000426.json", sample_fundamental())

    rows = helpers.scan_fundamental_results(tmp_path)

    assert len(rows) == 1
    assert rows[0]["stock_code"] == "000426"
    assert rows[0]["analyst_summary"] == "new neutral summary"
    assert rows[0]["risk_flags_count"] == 1


def test_dashboard_helpers_prefer_neutral_alias_and_fallback_to_legacy():
    payload = sample_fundamental()

    assert helpers.fundamental_analyst_summary(payload) == "new neutral summary"
    assert helpers.invalidation_condition_rows(payload)[0]["downstream_review_hint"] == "需要后续分析层复核"

    payload.pop("analyst_summary")
    payload["trader_summary"] = "基本面支持交给交易员进一步评估。"
    payload["invalidation_conditions"] = [
        {
            "condition": "condition",
            "evidence_needed": "evidence",
            "action_hint_for_trader": "需要交易员重新评估",
        }
    ]

    assert helpers.fundamental_analyst_summary(payload) == "基本面支持进入后续综合评估。"
    assert helpers.invalidation_condition_rows(payload)[0]["downstream_review_hint"] == "需要后续分析层复核"


def test_missing_file_does_not_crash(tmp_path):
    result, raw = helpers.load_result_pair("000426", tmp_path)

    assert result is None
    assert raw is None
    assert helpers.scan_fundamental_results(tmp_path) == []
    assert helpers.load_ai_bundle("000426", tmp_path)["ai_report"] is None


def test_risk_flags_to_rows():
    rows = helpers.risk_flag_rows(sample_fundamental())

    assert rows == [
        {
            "risk_name": "risk A",
            "severity": "medium",
            "reason": "watch data",
            "evidence": "unit | sample evidence",
        }
    ]


def test_must_track_indicators_to_rows():
    rows = helpers.must_track_indicator_rows(sample_fundamental())

    assert rows[0]["indicator_name"] == "indicator A"
    assert rows[0]["current_value"] == 1.2
    assert rows[0]["frequency"] == "weekly"


def test_extract_business_composition_from_raw_json():
    rows = helpers.business_composition_rows(sample_raw())

    assert rows[0]["segment_name"] == "segment A"
    assert rows[0]["revenue"] == 100


def test_extract_commodity_prices_from_raw_json():
    rows = helpers.commodity_price_rows(sample_raw())

    assert rows[0]["commodity_name"] == "copper"
    assert rows[0]["readiness_eligible"] is True


def test_detect_forbidden_trading_terms():
    detected = helpers.detect_forbidden_terms({"text": "这里包含买入和目标价"})

    assert "买入" in detected
    assert "目标价" in detected


def test_empty_none_and_missing_fields_do_not_crash():
    assert helpers.risk_flag_rows(None) == []
    assert helpers.must_track_indicator_rows({}) == []
    assert helpers.business_composition_rows(None) == []
    assert helpers.commodity_price_rows(None) == []
    assert helpers.financial_quality_row({}, {})["revenue_yoy"] is None
    assert helpers.valuation_row({}, {})["pe_ttm"] is None
    assert helpers.data_quality_summary({}, {})["fetch_status"] == []
    assert helpers.confidence_breakdown_rows(None) == []
    assert helpers.evidence_rows(None, "supporting_evidence") == []
    assert helpers.ai_must_track_rows(None, None) == []


def test_load_ai_report_and_prompt_preview(tmp_path):
    write_json(tmp_path / "ai_report_000426.json", sample_ai_report())
    (tmp_path / "ai_prompt_000426.md").write_text("prompt body", encoding="utf-8")

    bundle = helpers.load_ai_bundle("000426", tmp_path)

    assert bundle["ai_report"]["stock_code"] == "000426"
    assert helpers.prompt_preview("000426", tmp_path) == "prompt body"


def test_confidence_breakdown_rows_from_ai_report():
    rows = helpers.confidence_breakdown_rows(sample_ai_report())

    assert rows[0]["维度"] == "数据覆盖"
    assert rows[0]["状态"] == "strong"


def test_evidence_classification_rows():
    report = sample_ai_report()

    assert helpers.evidence_rows(report, "supporting_evidence")[0]["evidence_name"] == "support A"
    assert helpers.evidence_rows(report, "limiting_evidence")[0]["evidence_name"] == "limit A"
    assert helpers.evidence_rows(report, "unknown_or_missing_evidence")[0]["evidence_name"] == "unknown A"


def test_ai_must_track_rows_sort_high_priority_first():
    rows = helpers.ai_must_track_rows(sample_ai_report(), sample_evidence_pack())

    assert rows[0]["indicator_name"] == "high item"
    assert rows[0]["priority"] == "high"
    assert rows[1]["current_value"] == "1.00%"


def test_v3_chinese_strategy_and_sub_type_labels():
    assert helpers.format_strategy_type("satellite_communication_infrastructure") == "satellite_communication_infrastructure（卫星通信基础设施）"
    assert helpers.format_strategy_type("low_altitude_economy_infrastructure") == "low_altitude_economy_infrastructure（低空经济基础设施 / 运营服务）"
    assert helpers.format_strategy_type("life_science_cxo_services") == "life_science_cxo_services（CXO 医药外包服务）"
    assert helpers.format_sub_type("aviation_operations_service") == "aviation_operations_service（通航 / 低空飞行运营服务）"
    assert helpers.format_sub_type("integrated_cxo_platform") == "integrated_cxo_platform（综合 CXO 平台）"
    assert helpers.format_sub_type(None) == "不适用"


def test_v3_report_consistency_detects_unknown_strategy_mismatch():
    fundamental = sample_fundamental()
    fundamental["strategy_type"] = "life_science_cxo_services"
    fundamental["sub_type"] = "integrated_cxo_platform"
    fundamental["status"] = "insufficient_data"
    evidence_pack = sample_evidence_pack()
    evidence_pack["stock"] = {
        "code": "000426",
        "name": "sample",
        "strategy_type": "life_science_cxo_services",
        "sub_type": "integrated_cxo_platform",
        "status": "insufficient_data",
        "confidence": "low",
        "fundamental_score": 50,
    }
    report = sample_ai_report()
    report["fundamental_view"] = "insufficient_data"
    report["valuation_analysis"] = "Because the current strategy_type is unknown, valuation cannot use a professional CXO framework."

    status = helpers.report_consistency_status(report, evidence_pack, fundamental)

    assert status["status"] == "mismatch"
    assert "报告过期 / 报告与当前数据不一致" in status["warnings"][0]
    assert status["can_use_ai_body"] is False


def test_v3_risk_gap_notice_when_no_risk_flags_but_missing_evidence_high():
    evidence_pack = sample_evidence_pack()
    evidence_pack["risk_flags"] = []
    notice = helpers.risk_gap_notice({"risk_flags": []}, evidence_pack, sample_ai_report())

    assert "不表示没有风险" in notice


def test_v3_must_track_rows_use_chinese_columns_and_priority_sort():
    rows = helpers.ai_must_track_rows_cn(sample_ai_report(), sample_evidence_pack(), include_low=False)

    assert list(rows[0].keys()) == ["指标", "状态", "优先级", "当前值", "为什么重要", "下一步需要验证的证据"]
    assert rows[0]["指标"] == "high item"
    assert rows[1]["指标"] == "medium item"


def test_ai_report_status_schema_and_safety():
    status = helpers.ai_report_status(sample_ai_report(), "clean markdown")

    assert status["schema_valid"] is True
    assert status["safety_safe"] is True
    assert status["restricted_terms_count"] == 0
    assert status["report_quality_status"] == "ok"
    assert status["garbled_text_detected"] is False
    assert status["can_display_body"] is True


def test_ai_report_status_detects_safety_violation():
    report = sample_ai_report()
    report["final_summary"] = "这里包含买入"

    status = helpers.ai_report_status(report, "")

    assert status["safety_safe"] is False
    assert status["restricted_terms_count"] == 1
    assert status["can_display_body"] is False


def test_ai_report_status_detects_garbled_text_warning():
    report = sample_ai_report()
    report["executive_summary"] = "????????????????????"

    status = helpers.ai_report_status(report, "clean markdown")

    assert status["schema_valid"] is True
    assert status["safety_safe"] is True
    assert status["report_quality_status"] == "garbled_text_detected"
    assert status["garbled_text_detected"] is True
    assert status["quality_warnings"]
    assert status["can_display_body"] is False
    assert helpers.clean_ai_report_text(report, "executive_summary", "fallback") == "fallback"


def test_scan_available_stocks_prefers_ai_report(tmp_path):
    write_json(tmp_path / "fundamental_000426.json", sample_fundamental())
    write_json(tmp_path / "ai_report_000426.json", sample_ai_report())

    rows = helpers.scan_available_stocks(tmp_path)

    assert rows[0]["stock_code"] == "000426"
    assert rows[0]["has_ai_report"] is True


def test_stock_selector_table_uses_chinese_column_names():
    rows = stock_selector_table_rows(
        [
            {
                "stock_code": "000426",
                "stock_name": "sample",
                "fundamental_view": "supportive_for_further_evaluation",
                "strategy_type": "resource_swing",
                "has_ai_report": True,
                "has_fundamental": True,
            }
        ]
    )

    assert list(rows[0].keys()) == [
        "股票代码",
        "公司名称",
        "AI基本面观点",
        "分析框架",
        "已有AI报告",
        "已有规则结果",
    ]
    assert "stock_code" not in rows[0]
    assert "stock_name" not in rows[0]
    assert rows[0]["股票代码"] == "000426"
