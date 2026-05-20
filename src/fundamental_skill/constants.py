# -*- coding: utf-8 -*-
"""Constants for the fundamental skill contract."""

STATUS_VALUES = ("supportive", "neutral", "negative", "insufficient_data")

CONFIDENCE_VALUES = ("high", "medium", "low")

STRATEGY_TYPES = (
    "resource_swing",
    "resource_core",
    "right_trend_growth",
    "semiconductor_cycle",
    "stable_growth",
    "advanced_manufacturing_growth",
    "satellite_communication_infrastructure",
    "low_altitude_economy_infrastructure",
    "life_science_cxo_services",
    "theme_only",
    "unknown",
)

RISK_SEVERITY_VALUES = ("low", "medium", "high")

SOURCE_TYPES = (
    "akshare",
    "user_input",
    "news",
    "financial_statement",
    "derived",
    "unknown",
)

CATALYST_TYPES = (
    "earnings",
    "policy",
    "industry_cycle",
    "commodity_price",
    "order",
    "valuation",
    "other",
)

VALUATION_LEVELS = ("low", "reasonable", "high", "unknown")

INDUSTRY_CYCLE_POSITIONS = ("upcycle", "neutral", "downcycle", "unknown")

THESIS_SUPPORT_VALUES = (
    "supported",
    "partially_supported",
    "unsupported",
    "unverified",
    "none",
)

PROHIBITED_TRADING_TERMS = (
    "买入",
    "卖出",
    "满仓",
    "梭哈",
    "清仓",
    "止损",
    "止盈",
    "加仓",
    "减仓",
    "目标价",
    "保证收益",
    "必涨",
    "必跌",
)

ALLOWED_TRADER_ACTION_HINTS = (
    "需要交易员重新评估",
    "需要暂停基本面支持判断",
    "需要更新基本面分析",
)
