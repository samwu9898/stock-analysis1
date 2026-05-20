# -*- coding: utf-8 -*-


def sample_fundamental(strategy_type="resource_swing"):
    return {
        "stock_code": "000426",
        "stock_name": "兴业银锡",
        "strategy_type": strategy_type,
        "status": "supportive",
        "confidence": "high",
        "fundamental_score": 76,
        "analyst_summary": "基本面支持进入后续综合评估。",
        "trader_summary": "基本面支持进入后续综合评估。",
        "missing_fields": ["financial_metrics.accounts_receivable"],
        "risk_flags": [
            {"name": "数据缺口风险", "severity": "medium", "monitor_method": "继续验证缺失字段", "evidence": []}
        ],
        "must_track_indicators": [],
        "invalidation_conditions": [
            {
                "condition": "商品价格证据失效",
                "evidence_needed": "补充价格数据",
                "downstream_review_hint": "需要后续分析层复核",
                "action_hint_for_trader": "需要后续分析层复核",
            }
        ],
    }


def sample_raw():
    return {
        "meta": {"code": "000426", "stock_name": "兴业银锡"},
        "blocks": {
            "basic_info": [{"stock_code": "000426", "stock_name": "兴业银锡", "main_business": "银、锡矿产采选"}],
            "financial_indicator": [
                {
                    "period": "2026-03-31",
                    "revenue_yoy": 20.0,
                    "net_profit_yoy": 35.0,
                    "gross_margin": 40.0,
                    "operating_cashflow": 900000000,
                    "inventory": 500000000,
                    "accounts_receivable": 600000000,
                    "contract_liabilities": 70000000,
                    "r_and_d_expense": 17755979.09,
                    "r_and_d_expense_ratio": 0.8336652584671204,
                    "capex": 229152931.6,
                }
            ],
            "valuation": [{"period": "2026-05-18", "pe_ttm": 22.0, "pb": 2.2, "market_cap": 15000000000}],
            "business_composition": [{"period": "2025-12-31", "segment_name": "银精矿", "revenue_ratio": 50.0}],
            "commodity_prices": [
                {
                    "commodity_name": "silver",
                    "price": 8000,
                    "date": "2026-05-18",
                    "readiness_eligible": True,
                }
            ],
        },
        "fetch_status": {
            "financial_indicator": {
                "success": True,
                "missing_fields": ["accounts_receivable"],
                "warnings": [],
                "source_trace": [
                    {
                        "function_name": "stock_financial_abstract",
                        "field_name": "gross_margin",
                        "source_period": "20260331",
                    }
                ],
            },
            "commodity_prices": {
                "success": True,
                "missing_fields": [],
                "warnings": [],
                "source_trace": [
                    {"function_name": "futures_zh_realtime", "source_period": "2026-05-18"}
                ],
            },
        },
        "errors": [],
    }
