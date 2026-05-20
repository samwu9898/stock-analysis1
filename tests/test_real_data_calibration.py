# -*- coding: utf-8 -*-

from src.fundamental_skill.data_adapter import FundamentalDataAdapter
from src.fundamental_skill.pipeline import FundamentalSkillPipeline
from src.fundamental_skill.stock_classifier import StockClassifier
from src.fundamental_skill.validators import validate_no_trading_instruction


def _raw(
    code: str,
    name: str,
    industry: str,
    main_business: str,
    financial: dict,
    news: list[dict] | None = None,
    valuation: list[dict] | None = None,
    business: list[dict] | None = None,
):
    return {
        "meta": {"code": code, "stock_name": name, "generated_at": "2026-05-17T00:00:00", "data_cutoff": "20260331"},
        "blocks": {
            "basic_info": [
                {
                    "stock_code": code,
                    "stock_name": name,
                    "industry": industry,
                    "main_business": main_business,
                    "listing_date": "2000-01-01",
                }
            ],
            "financial_indicator": [{"period": "20260331", **financial}],
            "valuation": valuation or [],
            "business_composition": business or [],
            "news": news or [],
        },
        "fetch_status": {},
        "errors": [],
    }


def _advanced_financial(accounts_receivable=None):
    return {
        "revenue_yoy": 1.3,
        "net_profit_yoy": 2.7,
        "deducted_net_profit": 985000000,
        "gross_margin": 27.8,
        "net_margin": 12.2,
        "roe": 2.9,
        "operating_cashflow": 1100000000,
        "debt_to_asset": 33.3,
        "accounts_receivable": accounts_receivable,
    }


def test_advanced_real_data_gaps_are_neutral_not_insufficient():
    raw = _raw(
        "002050",
        "三花智控",
        "通用设备制造业",
        "汽车热管理和制冷控制业务",
        _advanced_financial(),
        news=[
            {
                "title": "机器人执行器和特斯拉供应链相关公开信息",
                "summary": "机器人业务和大客户供应链仍需订单和收入验证",
            }
        ],
    )

    result = FundamentalSkillPipeline().analyze_from_dict(raw)
    risk_text = result.model_dump_json()

    assert result.strategy_type == "advanced_manufacturing_growth"
    assert result.status == "neutral"
    assert result.confidence != "high"
    assert "主营构成" in risk_text or "业务构成" in risk_text
    assert "估值" in risk_text
    assert "机器人" in risk_text or "大客户" in risk_text
    assert validate_no_trading_instruction(risk_text) == []


def test_semiconductor_real_data_gaps_are_neutral_not_negative():
    raw = _raw(
        "002371",
        "北方华创",
        "半导体设备",
        "半导体设备、刻蚀、薄膜和国产替代相关业务",
        {
            "revenue_yoy": 28.0,
            "net_profit_yoy": 35.0,
            "deducted_net_profit": 1800000000,
            "gross_margin": 44.0,
            "net_margin": 18.0,
            "roe": 18.0,
            "operating_cashflow": 2500000000,
            "debt_to_asset": 38.0,
            "inventory": None,
        },
        news=[{"title": "半导体设备国产替代订单验证", "summary": "国产替代和周期波动仍需验证"}],
    )

    result = FundamentalSkillPipeline().analyze_from_dict(raw)
    risk_text = result.model_dump_json()

    assert result.strategy_type == "semiconductor_cycle"
    assert result.status == "neutral"
    assert result.confidence != "high"
    assert "存货" in risk_text
    assert "半导体" in risk_text or "国产替代" in risk_text
    assert "估值" in risk_text
    assert validate_no_trading_instruction(risk_text) == []


def test_zijin_mining_prefers_resource_core():
    raw = _raw(
        "601899",
        "紫金矿业",
        "有色金属矿业",
        "全球矿业、多矿种、铜、金资源龙头和大型矿企",
        {
            "revenue_yoy": 12.0,
            "net_profit_yoy": 18.0,
            "deducted_net_profit": 10000000000,
            "gross_margin": 20.0,
            "operating_cashflow": 12000000000,
            "debt_to_asset": 45.0,
        },
        business=[{"segment_name": "铜金矿产", "revenue": 10000000000, "revenue_ratio": 80.0}],
    )
    normalized = FundamentalDataAdapter().from_dict(raw)

    result = StockClassifier().classify(normalized)

    assert result.strategy_type == "resource_core"


def test_xingye_yinxi_still_resource_swing():
    raw = _raw(
        "000426",
        "兴业银锡",
        "有色金属",
        "银、锡等资源品采选和冶炼业务",
        {
            "revenue_yoy": 18.0,
            "net_profit_yoy": 25.0,
            "deducted_net_profit": 800000000,
            "gross_margin": 40.0,
            "operating_cashflow": 900000000,
        },
    )
    normalized = FundamentalDataAdapter().from_dict(raw)

    result = StockClassifier().classify(normalized)

    assert result.strategy_type == "resource_swing"


def test_valuation_missing_alone_does_not_force_insufficient():
    raw = _raw(
        "002050",
        "三花智控",
        "通用设备制造业",
        "汽车热管理和制冷控制业务",
        _advanced_financial(accounts_receivable=1500000000),
        business=[{"segment_name": "汽车热管理", "revenue": 10000000000, "revenue_ratio": 45.0}],
    )

    result = FundamentalSkillPipeline().analyze_from_dict(raw)

    assert result.status != "insufficient_data"
    assert result.confidence != "high"


def test_business_composition_missing_alone_does_not_force_insufficient():
    raw = _raw(
        "002050",
        "三花智控",
        "通用设备制造业",
        "汽车热管理和制冷控制业务",
        _advanced_financial(accounts_receivable=1500000000),
        valuation=[{"pe_ttm": 40.0, "pb": 5.0, "market_cap": 100000000000}],
    )

    result = FundamentalSkillPipeline().analyze_from_dict(raw)

    assert result.status != "insufficient_data"
    assert result.confidence != "high"
