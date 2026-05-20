# -*- coding: utf-8 -*-
"""Generate mock regression fixtures and key-field expected snapshots."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "regression" / "fixtures"
EXPECTED = ROOT / "tests" / "regression" / "expected"
TRADE_FORBIDDEN = ["买入", "卖出", "加仓", "减仓", "清仓", "止损", "止盈", "目标价", "满仓", "梭哈"]


def raw(code, name, industry, main_business, fin=None, val=None, segments=None, news=None):
    return {
        "meta": {
            "code": code,
            "stock_name": name,
            "market": "mock",
            "generated_at": "2026-05-15T10:00:00",
            "data_cutoff": "2025-12-31",
        },
        "blocks": {
            "basic_info": [
                {
                    "stock_code": code,
                    "stock_name": name,
                    "industry": industry,
                    "main_business": main_business,
                }
            ],
            "financial_indicator": fin or [],
            "valuation": val or [],
            "business_composition": segments or [],
            "news": news or [],
        },
    }


def fin(**kwargs):
    payload = {
        "period": "2025-12-31",
        "revenue_yoy": 25,
        "net_profit_yoy": 30,
        "gross_margin": 28,
        "roe": 15,
        "operating_cashflow": 1000000000,
        "debt_to_asset": 45,
        "accounts_receivable": 800000000,
        "deducted_net_profit": 900000000,
        "net_profit": 1000000000,
        "inventory": 500000000,
    }
    payload.update(kwargs)
    return [payload]


def val(pe, pb, cap, dividend=None):
    payload = {"pe_ttm": pe, "pb": pb, "market_cap": cap}
    if dividend is not None:
        payload["dividend_yield"] = dividend
    return [payload]


def seg(*names):
    return [
        {"period": "2025-12-31", "segment_name": name, "revenue_ratio": max(5, 55 - index * 15)}
        for index, name in enumerate(names)
    ]


def news(*items):
    return [
        {"title": title, "summary": summary, "source": "mock", "publish_time": "2026-01-01", "url": None}
        for title, summary in items
    ]


def build_samples():
    return {
        "000426_xingye_yinxi": raw(
            "000426",
            "兴业银锡",
            "有色金属 / 银 / 锡",
            "银、锡等有色金属矿产采选和冶炼，利润对商品价格较敏感",
            fin(revenue_yoy=28, net_profit_yoy=55, gross_margin=41, roe=16, operating_cashflow=900000000),
            val(22, 2.2, 15000000000),
            seg("银精矿", "锡精矿"),
            news(("mock：资源品业务保持增长", "银价和锡价仍需外部价格数据验证")),
        ),
        "603993_luoyang_moly": raw(
            "603993",
            "洛阳钼业",
            "铜 / 钴 / 钼 / 有色资源",
            "铜、钴、钼等多资源品矿业公司，包含海外项目和周期波动风险",
            fin(revenue_yoy=22, net_profit_yoy=35, gross_margin=26, roe=13, operating_cashflow=8000000000),
            val(24, 2.8, 180000000000),
            seg("铜钴业务", "钼钨业务"),
            news(("mock：海外矿山项目推进", "商品价格和海外项目风险需要跟踪")),
        ),
        "601899_zijin_mining": raw(
            "601899",
            "紫金矿业",
            "铜 / 金 / 多矿种 / 全球矿业",
            "多矿种铜金资源龙头，大型矿企，现金流和分红能力较强，存在海外项目和资本开支变量",
            fin(revenue_yoy=18, net_profit_yoy=25, gross_margin=22, roe=18, operating_cashflow=42000000000, debt_to_asset=52),
            val(18, 3, 300000000000, 2.5),
            seg("铜矿", "金矿", "其他矿产"),
            news(("mock：全球矿业项目保持推进", "商品价格组合、资本开支和海外项目仍需跟踪")),
        ),
        "300308_zhongji_innolight": raw(
            "300308",
            "中际旭创",
            "光模块 / AI 算力 / 数据中心",
            "高速光模块、AI算力、数据中心互联产品，受客户资本开支和订单影响",
            fin(revenue_yoy=60, net_profit_yoy=75, gross_margin=35, roe=22, operating_cashflow=3000000000),
            val(55, 7, 180000000000),
            seg("高速光模块", "数据中心互联"),
            news(("mock：AI算力订单保持景气", "客户资本开支、订单持续性和估值消化需要验证")),
        ),
        "300476_shenghong_tech": raw(
            "300476",
            "胜宏科技",
            "PCB / AI服务器 / 高速互联",
            "PCB和AI服务器高速互联相关产品，受AI服务器需求、产能和毛利率影响",
            fin(revenue_yoy=42, net_profit_yoy=58, gross_margin=27, roe=17, operating_cashflow=1600000000),
            val(48, 5.8, 90000000000),
            seg("PCB", "AI服务器高速互联板"),
            news(("mock：AI服务器PCB需求提升", "毛利率、产能释放和估值预期仍需验证")),
        ),
        "002371_naura": raw(
            "002371",
            "北方华创",
            "半导体设备 / 国产替代",
            "半导体设备、刻蚀、薄膜等国产替代方向，受订单、研发投入和资本开支周期影响",
            fin(revenue_yoy=32, net_profit_yoy=45, gross_margin=39, roe=14, operating_cashflow=2200000000, inventory=5000000000),
            val(68, 8, 220000000000),
            seg("半导体设备", "电子工艺装备"),
            news(("mock：国产替代订单持续推进", "估值波动、研发商业化和下游资本开支需要跟踪")),
        ),
        "688008_montage": raw(
            "688008",
            "澜起科技",
            "半导体 / 服务器内存接口 / AI服务器链",
            "半导体服务器内存接口芯片和AI服务器链相关产品，受服务器周期和客户需求影响",
            fin(revenue_yoy=36, net_profit_yoy=50, gross_margin=57, roe=13, operating_cashflow=1800000000, inventory=1200000000),
            val(60, 7, 130000000000),
            seg("内存接口芯片", "AI服务器相关芯片"),
            news(("mock：服务器内存接口需求恢复", "服务器周期、客户需求和估值波动需要跟踪")),
        ),
        "002050_sanhua": raw(
            "002050",
            "三花智控",
            "汽车热管理 / 制冷控制 / 高端制造",
            "制冷控制元器件、汽车热管理系统零部件、机器人执行器相关零部件布局，机器人业务仍为mock待验证描述",
            fin(revenue_yoy=24.5, net_profit_yoy=31.2, gross_margin=28.5, roe=18.2, operating_cashflow=4200000000, accounts_receivable=5200000000),
            val(45, 5.2, 120000000000),
            [
                {"period": "2025-12-31", "segment_name": "制冷空调电器零部件", "revenue_ratio": 45},
                {"period": "2025-12-31", "segment_name": "汽车热管理系统零部件", "revenue_ratio": 42},
                {"period": "2025-12-31", "segment_name": "机器人执行器相关零部件布局", "note": "mock 待验证布局，不提供明确收入占比或订单金额"},
            ],
            news(
                ("mock：汽车热管理业务保持增长", "汽车热管理相关订单和收入仍需财报验证"),
                ("mock：机器人执行器零部件布局受到关注", "机器人执行器相关零部件处于mock待验证阶段"),
                ("mock：特斯拉供应链和大客户需求需继续验证", "供应链描述为mock，不作为确定事实"),
            ),
        ),
        "601689_tuopu": raw(
            "601689",
            "拓普集团",
            "汽车零部件 / 机器人执行器 / 特斯拉供应链",
            "汽车零部件、智能底盘、机器人执行器相关零部件和新能源车供应链业务",
            fin(revenue_yoy=26, net_profit_yoy=28, gross_margin=24, roe=14, operating_cashflow=2500000000, accounts_receivable=4300000000),
            val(42, 5, 110000000000),
            [
                {"period": "2025-12-31", "segment_name": "汽车零部件", "revenue_ratio": 70},
                {"period": "2025-12-31", "segment_name": "机器人执行器相关零部件", "note": "mock 待验证"},
            ],
            news(("mock：机器人执行器业务仍需订单验证", "特斯拉供应链和大客户持续性需要验证")),
        ),
        "002028_siyuan": raw(
            "002028",
            "思源电气",
            "电力设备 / 输配电 / 变压器 / 海外订单",
            "输配电设备、变压器、电力自动化和海外订单相关业务，订单和现金流质量重要",
            fin(revenue_yoy=20, net_profit_yoy=24, gross_margin=31, roe=17, operating_cashflow=1800000000, accounts_receivable=2400000000, debt_to_asset=38),
            val(24, 3.2, 70000000000),
            seg("输配电设备", "变压器", "海外订单"),
            news(("mock：海外订单保持增长", "订单、现金流、毛利率和应收账款需要持续跟踪")),
        ),
        "600406_nari": raw(
            "600406",
            "国电南瑞",
            "电网自动化 / 智能电网 / 电力设备",
            "电网自动化、智能电网和电力设备龙头，受电网投资节奏和现金流影响",
            fin(revenue_yoy=14, net_profit_yoy=16, gross_margin=29, roe=16, operating_cashflow=5200000000, accounts_receivable=6500000000, debt_to_asset=35),
            val(28, 4.1, 160000000000),
            seg("电网自动化", "智能电网", "电力设备"),
            news(("mock：电网投资节奏平稳", "现金流和估值稳定性需要跟踪")),
        ),
        "999999_theme_a": raw(
            "999999",
            "题材样本A",
            "跨界概念 / 热门题材",
            "主营与热门概念关联不清，财务支撑弱，主要依赖题材新闻和互动平台传闻",
            [],
            val(95, 9, 6000000000),
            seg("传统业务"),
            news(("mock：互动平台提及人形机器人概念", "概念和主营相关性待验证"), ("mock：跨界转型传闻升温", "缺少订单和业绩验证")),
        ),
        "999998_insufficient_b": raw("999998", "数据不足样本B", None, None, [], [], [], []),
    }


def build_expected():
    return {
        "000426_xingye_yinxi": {"stock_code": "000426", "expected_strategy_type": "resource_swing", "allowed_status": ["supportive", "neutral", "insufficient_data"], "max_confidence": "medium", "min_required_risk_flags": ["商品价格数据缺失"], "must_track_keywords": ["商品价格", "扣非净利润", "经营现金流", "主营构成"], "forbidden_phrases": TRADE_FORBIDDEN},
        "603993_luoyang_moly": {"stock_code": "603993", "expected_strategy_type": "resource_swing", "allowed_status": ["supportive", "neutral", "insufficient_data"], "max_confidence": "medium", "min_required_risk_flags": ["商品价格数据缺失"], "must_track_keywords": ["商品价格", "经营现金流", "主营构成"], "forbidden_phrases": TRADE_FORBIDDEN},
        "601899_zijin_mining": {"stock_code": "601899", "expected_strategy_type": "resource_core", "allowed_status": ["supportive", "neutral"], "max_confidence": "medium", "min_required_risk_flags": ["商品价格数据缺失"], "must_track_keywords": ["铜价", "金价", "经营现金流", "资产负债率"], "forbidden_phrases": TRADE_FORBIDDEN},
        "300308_zhongji_innolight": {"stock_code": "300308", "expected_strategy_type": "right_trend_growth", "allowed_status": ["supportive", "neutral"], "max_confidence": "high", "min_required_risk_flags": [], "must_track_keywords": ["营收增速", "净利润增速", "毛利率", "客户", "订单"], "forbidden_phrases": TRADE_FORBIDDEN},
        "300476_shenghong_tech": {"stock_code": "300476", "expected_strategy_type": "right_trend_growth", "allowed_status": ["supportive", "neutral"], "max_confidence": "high", "min_required_risk_flags": [], "must_track_keywords": ["营收增速", "净利润增速", "毛利率", "订单"], "forbidden_phrases": TRADE_FORBIDDEN},
        "002371_naura": {"stock_code": "002371", "expected_strategy_type": "semiconductor_cycle", "allowed_status": ["supportive", "neutral"], "max_confidence": "high", "min_required_risk_flags": [], "must_track_keywords": ["订单", "毛利率", "存货", "研发", "经营现金流"], "forbidden_phrases": TRADE_FORBIDDEN},
        "688008_montage": {"stock_code": "688008", "expected_strategy_type": "semiconductor_cycle", "allowed_status": ["supportive", "neutral"], "max_confidence": "high", "min_required_risk_flags": [], "must_track_keywords": ["订单", "毛利率", "存货", "研发"], "forbidden_phrases": TRADE_FORBIDDEN},
        "002050_sanhua": {"stock_code": "002050", "expected_strategy_type": "advanced_manufacturing_growth", "allowed_status": ["supportive", "neutral"], "max_confidence": "medium", "min_required_risk_flags": ["机器人业务兑现验证不足", "大客户依赖验证不足"], "must_track_keywords": ["机器人", "汽车热管理", "毛利率", "经营现金流", "应收账款"], "forbidden_phrases": ["机器人业务已经兑现", "人形机器人收入确定放量", "特斯拉订单确定增长"] + TRADE_FORBIDDEN},
        "601689_tuopu": {"stock_code": "601689", "expected_strategy_type": "advanced_manufacturing_growth", "allowed_status": ["supportive", "neutral"], "max_confidence": "medium", "min_required_risk_flags": ["机器人业务兑现验证不足", "大客户依赖验证不足"], "must_track_keywords": ["机器人", "毛利率", "经营现金流", "应收账款"], "forbidden_phrases": ["机器人业务已经兑现", "特斯拉订单确定增长"] + TRADE_FORBIDDEN},
        "002028_siyuan": {"stock_code": "002028", "expected_strategy_type": "stable_growth", "allowed_status": ["supportive", "neutral"], "max_confidence": "high", "min_required_risk_flags": [], "must_track_keywords": ["经营现金流", "ROE", "毛利率", "应收账款", "订单"], "forbidden_phrases": TRADE_FORBIDDEN},
        "600406_nari": {"stock_code": "600406", "expected_strategy_type": "stable_growth", "allowed_status": ["supportive", "neutral"], "max_confidence": "high", "min_required_risk_flags": [], "must_track_keywords": ["经营现金流", "ROE", "毛利率", "应收账款", "订单"], "forbidden_phrases": TRADE_FORBIDDEN},
        "999999_theme_a": {"stock_code": "999999", "expected_strategy_type": "theme_only", "allowed_status": ["neutral", "negative", "insufficient_data"], "max_confidence": "medium", "min_required_risk_flags": [], "must_track_keywords": ["经营现金流", "毛利率", "主营"], "forbidden_phrases": TRADE_FORBIDDEN},
        "999998_insufficient_b": {"stock_code": "999998", "expected_strategy_type": "unknown", "allowed_status": ["insufficient_data"], "max_confidence": "low", "max_score": 50, "min_required_risk_flags": [], "must_track_keywords": ["行业", "主营", "财务"], "forbidden_phrases": TRADE_FORBIDDEN},
    }


def main() -> int:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    EXPECTED.mkdir(parents=True, exist_ok=True)
    samples = build_samples()
    expected = build_expected()
    for name, payload in samples.items():
        (FIXTURES / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    for name, payload in expected.items():
        (EXPECTED / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(samples)} regression fixtures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
