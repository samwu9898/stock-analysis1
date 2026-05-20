# -*- coding: utf-8 -*-
"""Deterministic rule-based fundamental scoring engine."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from .analysis_context_builder import AnalysisContextBuilder
from .analysis_context_schema import AnalysisContext
from .classification_schema import FundamentalFramework, StockClassificationResult
from .data_adapter import FundamentalDataAdapter
from .data_readiness_planner import DataReadinessPlanner
from .framework_selector import FrameworkSelector
from .raw_schema import FinancialMetricInput, NormalizedFundamentalInput
from .readiness_schema import DataReadinessPlan
from .scoring_schema import (
    DimensionScore,
    FundamentalScoringResult,
    RequiredRiskForScoring,
    ScoringEvidence,
)
from .stock_classifier import StockClassifier


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCORING_CONFIG = PROJECT_ROOT / "config" / "fundamental_scoring.yaml"
DIMENSIONS = [
    "business_quality",
    "financial_quality",
    "industry_cycle",
    "valuation_reasonableness",
    "catalyst_strength",
    "risk_control",
    "data_quality",
]


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def _clamp(value: float, low: int = 0, high: int = 100) -> int:
    return int(max(low, min(high, round(value))))


def _fmt(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)[:120]


class FundamentalScoringEngine:
    def __init__(self, config_path: str | Path | None = None) -> None:
        self.config_path = Path(config_path) if config_path else DEFAULT_SCORING_CONFIG
        self.config = self._load_config()

    def score(
        self,
        normalized: NormalizedFundamentalInput,
        classification: StockClassificationResult,
        framework: FundamentalFramework,
        readiness: DataReadinessPlan,
        context: AnalysisContext,
    ) -> FundamentalScoringResult:
        weights, warnings = self._weights_for_strategy(classification.strategy_type)
        scorers = {
            "business_quality": self._score_business_quality,
            "financial_quality": self._score_financial_quality,
            "industry_cycle": self._score_industry_cycle,
            "valuation_reasonableness": self._score_valuation_reasonableness,
            "catalyst_strength": self._score_catalyst_strength,
            "risk_control": self._score_risk_control,
            "data_quality": self._score_data_quality,
        }
        dimension_scores = []
        cannot_score = []
        for dimension in DIMENSIONS:
            raw_score, reason, positive, negative, penalties = scorers[dimension](
                normalized, classification, readiness, context
            )
            constrained, max_allowed, applied = self.apply_context_constraints(
                dimension, raw_score, context
            )
            if max_allowed is not None and max_allowed <= 40:
                cannot_score.append(dimension)
            dimension_scores.append(
                DimensionScore(
                    dimension_name=dimension,
                    raw_score=_clamp(raw_score),
                    constrained_score=constrained,
                    weight=weights[dimension],
                    max_allowed_score=max_allowed,
                    score_reason=reason,
                    positive_evidence=positive,
                    negative_evidence=negative,
                    applied_constraints=applied,
                    missing_data_penalties=penalties,
                )
            )

        weighted = sum(item.constrained_score * item.weight for item in dimension_scores)
        weighted = self._cap_weighted_total(_clamp(weighted), classification, readiness, context)
        score_confidence = self._score_confidence(readiness, context)
        required_risks = [
            RequiredRiskForScoring(
                risk_name=risk.risk_name,
                severity=risk.severity,
                reason=risk.reason,
                from_context=True,
            )
            for risk in context.required_risks
        ]

        risk_warnings = self._advanced_manufacturing_risk_warnings(classification, context)
        risk_warnings.extend(self._structural_risk_warnings(classification, context))

        return FundamentalScoringResult(
            stock_code=normalized.stock_code,
            stock_name=normalized.stock_name,
            strategy_type=classification.strategy_type,
            generated_at=_now_iso(),
            context_quality=context.overall_context_quality,
            max_overall_confidence=context.max_overall_confidence,
            readiness_score=readiness.readiness_score,
            readiness_level=readiness.readiness_level,
            dimension_scores=dimension_scores,
            weighted_total_score=weighted,
            score_confidence=score_confidence,
            required_risks=required_risks,
            scoring_warnings=list(dict.fromkeys(warnings + context.context_warnings + risk_warnings)),
            cannot_score_dimensions=sorted(set(cannot_score)),
            notes_for_final_analyzer=[
                "该评分为规则型中间材料，不是最终基本面结论。",
                "后续分析必须遵守 AnalysisContext 的禁用结论和评分上限。",
            ],
        )

    def _load_config(self) -> dict[str, Any]:
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _weights_for_strategy(self, strategy_type: str) -> tuple[dict[str, float], list[str]]:
        weights = dict(self.config["strategy_weights"].get(strategy_type) or self.config["strategy_weights"]["unknown"])
        warnings = []
        total = sum(float(v) for v in weights.values())
        if abs(total - 1.0) > 0.0001:
            weights = {k: float(v) / total for k, v in weights.items()}
            warnings.append("strategy weights normalized because sum was not 1.0")
        return {k: float(weights[k]) for k in DIMENSIONS}, warnings

    def _latest_metric(self, normalized: NormalizedFundamentalInput) -> FinancialMetricInput | None:
        return normalized.financial_metrics[0] if normalized.financial_metrics else None

    def _ev(self, field: str, value: Any, interpretation: str, period: str | None = None, confidence: str = "medium") -> ScoringEvidence:
        return ScoringEvidence(
            source_field=field,
            value_preview=_fmt(value),
            period=period,
            interpretation=interpretation,
            confidence=confidence,
        )

    def _score_data_quality(self, normalized, classification, readiness, context):
        score = 85 if readiness.readiness_score >= 85 else 75 if readiness.readiness_score >= 70 else 60 if readiness.readiness_score >= 55 else 45 if readiness.readiness_score >= 40 else 30
        if readiness.readiness_level == "insufficient":
            score = min(score, 40)
        if readiness.readiness_level == "weak":
            score = min(score, 55)
        if context.overall_context_quality == "insufficient":
            score = min(score, 40)
        return score, "数据质量分主要由 readiness_score 和 readiness_level 决定。", [], [], readiness.confidence_penalty_reasons

    def _score_financial_quality(self, normalized, classification, readiness, context):
        score = 50
        pos, neg, penalties = [], [], []
        metric = self._latest_metric(normalized)
        if not metric:
            return 35, "缺少财务指标，财务质量只能低置信度评估。", pos, neg, ["financial_metrics missing"]
        p = metric.period
        if metric.revenue_yoy is not None:
            if metric.revenue_yoy > 20:
                score += 8; pos.append(self._ev("financial_metrics.revenue_yoy", metric.revenue_yoy, "营收增速超过20%。", p))
            if metric.revenue_yoy > 50:
                score += 5; pos.append(self._ev("financial_metrics.revenue_yoy", metric.revenue_yoy, "营收增速超过50%。", p))
            if metric.revenue_yoy < 0:
                score -= 8; neg.append(self._ev("financial_metrics.revenue_yoy", metric.revenue_yoy, "营收增速为负。", p))
        if metric.net_profit_yoy is not None:
            if metric.net_profit_yoy > 20:
                score += 8; pos.append(self._ev("financial_metrics.net_profit_yoy", metric.net_profit_yoy, "净利润增速超过20%。", p))
            if metric.net_profit_yoy > 50:
                score += 5; pos.append(self._ev("financial_metrics.net_profit_yoy", metric.net_profit_yoy, "净利润增速超过50%。", p))
            if metric.net_profit_yoy < 0:
                score -= 10; neg.append(self._ev("financial_metrics.net_profit_yoy", metric.net_profit_yoy, "净利润增速为负。", p))
        if metric.gross_margin is not None:
            if metric.gross_margin > 20:
                score += 5; pos.append(self._ev("financial_metrics.gross_margin", metric.gross_margin, "毛利率超过20%。", p))
            if metric.gross_margin > 35:
                score += 5; pos.append(self._ev("financial_metrics.gross_margin", metric.gross_margin, "毛利率超过35%。", p))
            if metric.gross_margin < 10:
                score -= 8; neg.append(self._ev("financial_metrics.gross_margin", metric.gross_margin, "毛利率低于10%。", p))
        else:
            penalties.append("gross_margin missing")
        if metric.roe is not None:
            if metric.roe > 10:
                score += 5; pos.append(self._ev("financial_metrics.roe", metric.roe, "ROE超过10%。", p))
            if metric.roe > 15:
                score += 5; pos.append(self._ev("financial_metrics.roe", metric.roe, "ROE超过15%。", p))
            if metric.roe < 5:
                score -= 6; neg.append(self._ev("financial_metrics.roe", metric.roe, "ROE低于5%。", p))
        if metric.operating_cashflow is not None:
            if metric.operating_cashflow > 0:
                score += 6; pos.append(self._ev("financial_metrics.operating_cashflow", metric.operating_cashflow, "经营现金流为正。", p))
            elif metric.operating_cashflow < 0:
                score -= 10; neg.append(self._ev("financial_metrics.operating_cashflow", metric.operating_cashflow, "经营现金流为负。", p))
        else:
            score -= 3; penalties.append("operating_cashflow missing")
        if metric.deducted_net_profit is not None:
            if metric.net_profit and abs(metric.deducted_net_profit / metric.net_profit) >= 0.8:
                score += 5; pos.append(self._ev("financial_metrics.deducted_net_profit", metric.deducted_net_profit, "扣非净利润接近净利润。", p))
        else:
            score -= 3; penalties.append("deducted_net_profit missing")
        return _clamp(score, 20, 95), "财务质量按增长、盈利能力、ROE、现金流和扣非利润规则评分。", pos, neg, penalties

    def _score_business_quality(self, normalized, classification, readiness, context):
        score = 50
        pos, neg, penalties = [], [], []
        text = self._business_text(normalized)
        if normalized.business_composition and normalized.business_composition.segments:
            score += 10; pos.append(self._ev("business_composition.segments", len(normalized.business_composition.segments), "存在主营构成。"))
        else:
            score -= 12; penalties.append("business_composition missing")
        if normalized.basic_info.main_business:
            score += 8; pos.append(self._ev("basic_info.main_business", normalized.basic_info.main_business, "主营业务字段可用。"))
        else:
            score -= 8; penalties.append("main_business missing")
        if normalized.basic_info.industry:
            score += 5; pos.append(self._ev("basic_info.industry", normalized.basic_info.industry, "行业字段可用。"))
        if self._strategy_text_match(classification.strategy_type, text):
            score += 8; pos.append(self._ev("strategy_type", classification.strategy_type, "业务文本与分类框架匹配。"))
        if classification.strategy_type == "resource_core" and any(k in text for k in ("多矿种", "铜", "金")):
            score += 8
        if classification.strategy_type == "resource_swing" and any(k in text for k in ("银", "锡", "铜", "稀土")):
            score += 6
        if classification.strategy_type == "right_trend_growth" and any(k in text for k in ("AI", "光模块", "PCB", "服务器", "液冷")):
            score += 6
        if classification.strategy_type == "semiconductor_cycle" and any(k in text for k in ("设备", "芯片", "晶圆", "存储")):
            score += 6
        if classification.strategy_type == "stable_growth" and any(k in text for k in ("电网", "变压器", "电力设备")):
            score += 6
        if classification.strategy_type == "advanced_manufacturing_growth" and any(
            k in text
            for k in (
                "汽车热管理",
                "热管理",
                "机器人执行器",
                "机器人",
                "工业自动化",
                "精密制造",
                "汽车零部件",
                "高端制造",
            )
        ):
            score += 8
        if classification.strategy_type == "satellite_communication_infrastructure" and any(
            k in text
            for k in (
                "电信、广播电视和卫星传输服务",
                "卫星空间段运营",
                "卫星传输服务",
                "卫星通信服务",
                "广播电视和卫星传输服务",
                "转发器",
                "带宽资源",
                "轨位资源",
                "频段资源",
            )
        ):
            score += 8
        if classification.strategy_type == "low_altitude_economy_infrastructure":
            if getattr(classification, "sub_type", None):
                score += 6
                pos.append(self._ev("classification.sub_type", getattr(classification, "sub_type", None), "low-altitude sub_type routing is available."))
            low_altitude_missing = {
                item.field_name
                for item in readiness.field_readiness
                if item.field_name.startswith("low_altitude.") and item.status in {"missing", "partial"}
            }
            if low_altitude_missing:
                score -= 8
                penalties.append("low-altitude sub_type confidence-gating indicators missing")
        if classification.strategy_type == "life_science_cxo_services":
            if getattr(classification, "sub_type", None):
                score += 6
                pos.append(self._ev("classification.sub_type", getattr(classification, "sub_type", None), "life-science CXO sub_type routing is available."))
            cxo_missing = {
                item.field_name
                for item in readiness.field_readiness
                if item.field_name.startswith("life_science_cxo.") and item.status in {"missing", "partial"}
            }
            if cxo_missing:
                score -= 8
                penalties.append("life-science CXO confidence-gating indicators missing")
        if classification.strategy_type == "theme_only":
            score -= 10
        if classification.strategy_type == "unknown":
            score -= 15
        return _clamp(score, 20, 95), "业务质量按主营、行业、业务构成和分类匹配度评分。", pos, neg, penalties

    def _score_industry_cycle(self, normalized, classification, readiness, context):
        score = 50
        pos, neg, penalties = [], [], []
        metric = self._latest_metric(normalized)
        if classification.confidence == "high":
            score += 5
        elif classification.confidence == "low":
            score -= 8
        if readiness.readiness_level == "weak":
            score -= 8
        if readiness.readiness_level == "insufficient":
            score -= 15
        missing = set(readiness.critical_missing_fields + readiness.high_priority_missing_fields)
        if classification.strategy_type in {"resource_swing", "resource_core"}:
            if "external.commodity_prices" in missing:
                score -= 10; penalties.append("external.commodity_prices missing")
            if "business_composition.segments" in missing:
                score -= 10; penalties.append("business_composition.segments missing")
            if metric and metric.revenue_yoy and metric.revenue_yoy > 20:
                score += 5; pos.append(self._ev("financial_metrics.revenue_yoy", metric.revenue_yoy, "营收增速支持周期观察。", metric.period))
            if metric and metric.net_profit_yoy and metric.net_profit_yoy > 20:
                score += 5; pos.append(self._ev("financial_metrics.net_profit_yoy", metric.net_profit_yoy, "利润增速支持周期观察。", metric.period))
        if classification.strategy_type == "right_trend_growth":
            if metric and metric.revenue_yoy and metric.revenue_yoy > 30:
                score += 8; pos.append(self._ev("financial_metrics.revenue_yoy", metric.revenue_yoy, "收入高增支持景气观察。", metric.period))
            if metric and metric.net_profit_yoy and metric.net_profit_yoy > 30:
                score += 8; pos.append(self._ev("financial_metrics.net_profit_yoy", metric.net_profit_yoy, "利润高增支持景气观察。", metric.period))
            if "financial_metrics.gross_margin" in missing:
                score -= 8; penalties.append("gross_margin missing")
        if classification.strategy_type == "semiconductor_cycle":
            if "financial_metrics.inventory" in missing:
                score -= 10; penalties.append("inventory missing")
            if "financial_metrics.gross_margin" in missing:
                score -= 8; penalties.append("gross_margin missing")
            if metric and metric.revenue_yoy and metric.revenue_yoy > 20:
                score += 5
        if classification.strategy_type == "stable_growth":
            if metric and metric.operating_cashflow and metric.operating_cashflow > 0:
                score += 5
            if metric and metric.roe and metric.roe > 10:
                score += 5
            if "financial_metrics.accounts_receivable" in missing:
                score -= 5; penalties.append("accounts_receivable missing")
        if classification.strategy_type == "advanced_manufacturing_growth":
            if "business_composition.segments" in missing:
                score -= 10; penalties.append("business_composition.segments missing")
            if "financial_metrics.accounts_receivable" in missing:
                score -= 5; penalties.append("accounts_receivable missing")
            if metric and metric.revenue_yoy and metric.revenue_yoy > 20:
                score += 6; pos.append(self._ev("financial_metrics.revenue_yoy", metric.revenue_yoy, "收入增长支持高端制造成长观察。", metric.period))
            if metric and metric.net_profit_yoy and metric.net_profit_yoy > 20:
                score += 6; pos.append(self._ev("financial_metrics.net_profit_yoy", metric.net_profit_yoy, "利润增长支持高端制造成长观察。", metric.period))
            if metric and metric.gross_margin and metric.gross_margin > 25:
                score += 5; pos.append(self._ev("financial_metrics.gross_margin", metric.gross_margin, "毛利率可用于观察产品结构和盈利能力。", metric.period))
        if classification.strategy_type == "low_altitude_economy_infrastructure":
            subtype = getattr(classification, "sub_type", None)
            if subtype == "aviation_operations_service":
                gating = {"low_altitude.fleet_size", "low_altitude.operating_hours", "low_altitude.flight_sorties"} & missing
            else:
                gating = {"low_altitude.contract_amount", "low_altitude.project_acceptance_progress", "low_altitude.customer_structure", "low_altitude.platform_dispatch_volume"} & missing
            if gating:
                score -= 10
                penalties.append("low-altitude sub_type operating/contract indicators missing")
            if metric and metric.operating_cashflow and metric.operating_cashflow > 0:
                score += 4; pos.append(self._ev("financial_metrics.operating_cashflow", metric.operating_cashflow, "Operating cashflow is available as basic cash-conversion evidence.", metric.period))
            if metric and metric.gross_margin and metric.gross_margin > 15:
                score += 3; pos.append(self._ev("financial_metrics.gross_margin", metric.gross_margin, "Gross margin is basic operating-quality evidence, not low-altitude realization proof.", metric.period))
        if classification.strategy_type == "life_science_cxo_services":
            shared_missing = {
                "life_science_cxo.backlog",
                "life_science_cxo.new_signed_orders",
                "life_science_cxo.customer_concentration",
                "life_science_cxo.overseas_revenue_share",
                "life_science_cxo.north_america_or_us_revenue_share",
            } & missing
            subtype = getattr(classification, "sub_type", None)
            subtype_missing: set[str] = set()
            if subtype == "cdmo_manufacturing_services":
                subtype_missing = {"life_science_cxo.cdmo_capacity_utilization"} & missing
            elif subtype == "clinical_cro_services":
                subtype_missing = {"life_science_cxo.clinical_project_count"} & missing
            if shared_missing or subtype_missing:
                score -= 10
                penalties.append("life-science CXO order/customer/overseas/utilization/project gates missing")
            if metric and metric.operating_cashflow and metric.operating_cashflow > 0:
                score += 4; pos.append(self._ev("financial_metrics.operating_cashflow", metric.operating_cashflow, "Operating cashflow is base cash-conversion evidence, not order visibility.", metric.period))
            if metric and metric.gross_margin and metric.gross_margin > 15:
                score += 3; pos.append(self._ev("financial_metrics.gross_margin", metric.gross_margin, "Gross margin is base operating-quality evidence; v1 does not infer CDMO utilization from margin.", metric.period))
        if classification.strategy_type == "satellite_communication_infrastructure":
            satellite_missing = {
                "satellite.capacity_utilization_or_lease_rate",
                "satellite.customer_structure_or_concentration",
                "satellite.design_or_remaining_life",
                "financial_metrics.depreciation_amortization",
            } & missing
            if satellite_missing:
                score -= 10
                penalties.append("satellite confidence-gating indicators missing")
            if metric and metric.operating_cashflow and metric.operating_cashflow > 0:
                score += 5; pos.append(self._ev("financial_metrics.operating_cashflow", metric.operating_cashflow, "经营现金流可用于观察长周期运营现金转换。", metric.period))
            if metric and metric.gross_margin and metric.gross_margin > 20:
                score += 4; pos.append(self._ev("financial_metrics.gross_margin", metric.gross_margin, "毛利率可用于观察基础服务盈利能力，但不能替代容量利用率。", metric.period))
        return _clamp(score, 20, 95), "行业周期按分类置信度、准备度和策略关键变量评分。", pos, neg, penalties

    def _score_valuation_reasonableness(self, normalized, classification, readiness, context):
        score = 50
        pos, neg, penalties = [], [], []
        val = normalized.valuation_metrics
        if not val:
            return score, "估值数据缺失，保持中性基础分并记录告警。", pos, neg, ["valuation_metrics missing"]
        if val.pe_ttm is not None:
            pe = val.pe_ttm
            if pe <= 0:
                score -= 10; neg.append(self._ev("valuation_metrics.pe_ttm", pe, "PE TTM 非正常值。"))
            elif pe < 15:
                add = 8 if classification.strategy_type in {"stable_growth", "resource_core"} else 3
                score += add; pos.append(self._ev("valuation_metrics.pe_ttm", pe, "PE TTM 较低，但按策略类型保守加分。"))
            elif pe <= 35:
                score += 5; pos.append(self._ev("valuation_metrics.pe_ttm", pe, "PE TTM 位于中等区间。"))
            elif pe <= 70:
                if classification.strategy_type in {"right_trend_growth", "semiconductor_cycle", "advanced_manufacturing_growth"}:
                    score -= 3
                else:
                    score -= 5
            else:
                score -= 10; neg.append(self._ev("valuation_metrics.pe_ttm", pe, "PE TTM 高于70。"))
        if val.pb is not None and val.pb > 8:
            score -= 5
        if val.market_cap is None:
            score -= 2; penalties.append("market_cap missing")
        if val.dividend_yield is not None and val.dividend_yield > 2 and classification.strategy_type in {"resource_core", "stable_growth"}:
            score += 5; pos.append(self._ev("valuation_metrics.dividend_yield", val.dividend_yield, "股息率对该策略类型有帮助。"))
        if classification.strategy_type == "satellite_communication_infrastructure":
            score = min(score, 60)
            penalties.append("PE/PB/PS for satellite communication infrastructure are secondary valuation evidence only")
        if classification.strategy_type == "low_altitude_economy_infrastructure":
            score = min(score, 60)
            penalties.append("PE/PB/PS for low-altitude infrastructure are limited valuation context only")
        if classification.strategy_type == "life_science_cxo_services":
            score = min(score, 60)
            penalties.append("PE/PB/PS for life-science CXO services are limited valuation context only")
        return _clamp(score, 20, 95), "估值评分按策略类型保守解释 PE、PB、市值和股息率。", pos, neg, penalties

    def _score_catalyst_strength(self, normalized, classification, readiness, context):
        score = 50
        pos, neg, penalties = [], [], []
        text = self._business_text(normalized) + " " + " ".join([n.title + " " + (n.summary or "") for n in normalized.latest_news])
        if normalized.latest_news:
            score += 3; pos.append(self._ev("latest_news", len(normalized.latest_news), "存在新闻或公告材料。"))
        if classification.strategy_type == "right_trend_growth" and any(k in text for k in ("AI", "算力", "订单", "数据中心")):
            score += 5
        if classification.strategy_type == "resource_swing" and any(k in text for k in ("银", "锡", "铜", "金", "稀土")):
            score += 4
        if classification.strategy_type == "semiconductor_cycle" and any(k in text for k in ("国产替代", "半导体", "设备", "芯片")):
            score += 4
        if classification.strategy_type == "advanced_manufacturing_growth" and any(
            k in text for k in ("机器人", "汽车热管理", "订单", "客户", "工业自动化", "执行器")
        ):
            score += 5
        if classification.strategy_type == "satellite_communication_infrastructure" and any(
            k in text for k in ("商业航天", "卫星发射", "卫星通信", "卫星传输", "转发器", "带宽")
        ):
            score += 3
            penalties.append("satellite catalysts require operating-data validation and are capped conservatively")
        if classification.strategy_type == "low_altitude_economy_infrastructure":
            score = min(score, 58)
            penalties.append("low-altitude theme, policy pilot or cooperation does not raise catalyst strength without revenue/contract/customer/operation/acceptance evidence")
        if classification.strategy_type == "life_science_cxo_services":
            score = min(score, 55)
            penalties.append("CXO concept, contract liabilities, capex or R&D ratio do not raise catalyst strength without real orders/customer/overseas/utilization/project evidence")
        if normalized.latest_news and not normalized.financial_metrics:
            score = min(score, 65); penalties.append("news catalyst without financial validation capped at 65")
        return _clamp(score, 20, 95), "催化强度仅按新闻存在和业务关键词做保守规则评分。", pos, neg, penalties

    def _score_risk_control(self, normalized, classification, readiness, context):
        score = 70
        pos, neg, penalties = [], [], []
        for risk in context.required_risks:
            if risk.severity == "high":
                score -= 12
            elif risk.severity == "medium":
                score -= 7
            else:
                score -= 3
            neg.append(self._ev("context.required_risks", risk.risk_name, risk.reason, confidence="high"))
        if readiness.readiness_level == "weak":
            score -= 8
        if readiness.readiness_level == "insufficient":
            score -= 15
        if classification.strategy_type == "theme_only":
            score -= 10
        if classification.strategy_type == "unknown":
            score -= 15
        if not normalized.financial_metrics:
            score -= 15; penalties.append("financial_metrics missing")
        if not normalized.business_composition:
            score -= 8; penalties.append("business_composition missing")
        metric = self._latest_metric(normalized)
        if metric:
            if metric.operating_cashflow is not None and metric.operating_cashflow > 0:
                score += 5; pos.append(self._ev("financial_metrics.operating_cashflow", metric.operating_cashflow, "经营现金流为正。", metric.period))
            if metric.debt_to_asset is not None and metric.debt_to_asset < 60:
                score += 5
            if metric.roe is not None and metric.roe > 10:
                score += 3
            if classification.strategy_type == "advanced_manufacturing_growth" and metric.accounts_receivable is None:
                score -= 5; penalties.append("accounts_receivable missing")
            if classification.strategy_type == "satellite_communication_infrastructure":
                if metric.accounts_receivable is None:
                    score -= 5; penalties.append("accounts_receivable missing")
                if metric.contract_liabilities is not None:
                    pos.append(self._ev("financial_metrics.contract_liabilities", metric.contract_liabilities, "合同负债只能作为订单可见度 proxy，不等同真实 backlog。", metric.period))
                if metric.capex is not None:
                    pos.append(self._ev("financial_metrics.capex", metric.capex, "capex 只表示长期资产购建现金支出，不等同新增容量确定释放。", metric.period))
            if classification.strategy_type == "life_science_cxo_services":
                if metric.accounts_receivable is None:
                    score -= 5; penalties.append("accounts_receivable missing")
                if metric.contract_liabilities is not None:
                    pos.append(self._ev("financial_metrics.contract_liabilities", metric.contract_liabilities, "Contract liabilities are partial_proxy only and do not equal real backlog.", metric.period))
                if metric.capex is not None:
                    pos.append(self._ev("financial_metrics.capex", metric.capex, "Capex is capacity input observation only, not capacity absorption or future order realization.", metric.period))
                if metric.r_and_d_expense_ratio is not None:
                    pos.append(self._ev("financial_metrics.r_and_d_expense_ratio", metric.r_and_d_expense_ratio, "R&D ratio is R&D intensity only, not technology-moat confirmation.", metric.period))
        return _clamp(score, 20, 90), "风险可控度从70分开始，根据上下文风险、准备度和财务稳健性调整。", pos, neg, penalties

    def apply_context_constraints(self, dimension: str, raw_score: int, context: AnalysisContext) -> tuple[int, int | None, list[str]]:
        caps: list[tuple[int, str]] = []
        for item in context.scoring_constraints:
            if item.scoring_dimension == dimension:
                caps.append((item.max_score, f"context scoring constraint: {dimension} <= {item.max_score}"))
            elif item.scoring_dimension == "risk_penalty" and dimension == "risk_control":
                caps.append((item.max_score, f"context risk constraint mapped to risk_control <= {item.max_score}"))
        dim_permissions = {d.dimension_name: d for d in context.blocked_dimensions + context.restricted_dimensions + context.allowed_dimensions}
        perm = dim_permissions.get(self._permission_dimension_name(dimension))
        if perm:
            if perm.permission == "blocked":
                caps.append((40, f"dimension blocked: {perm.dimension_name} <= 40"))
            elif perm.permission == "restricted":
                caps.append((60, f"dimension restricted: {perm.dimension_name} <= 60"))
            elif perm.permission == "allowed_with_low_confidence":
                caps.append((75, f"dimension low confidence: {perm.dimension_name} <= 75"))
        if context.max_overall_confidence == "low":
            caps.append((75, "overall confidence low: dimension <= 75"))
        if context.readiness_level == "insufficient":
            caps.append((60, "readiness insufficient: dimension <= 60"))
        if not caps:
            return _clamp(raw_score), None, []
        max_allowed = min(cap for cap, _ in caps)
        return min(_clamp(raw_score), max_allowed), max_allowed, [reason for _, reason in caps]

    def _permission_dimension_name(self, score_dimension: str) -> str:
        return {
            "business_quality": "business_summary",
            "financial_quality": "financial_quality",
            "industry_cycle": "industry_cycle",
            "valuation_reasonableness": "valuation_view",
            "catalyst_strength": "catalysts",
            "risk_control": "risk_flags",
            "data_quality": "thesis_check",
        }.get(score_dimension, score_dimension)

    def _cap_weighted_total(self, score: int, classification, readiness, context) -> int:
        caps = []
        if context.max_overall_confidence == "low":
            caps.append(70)
        if readiness.readiness_level == "weak":
            caps.append(70)
        if readiness.readiness_level == "insufficient":
            caps.append(50)
        if classification.strategy_type == "unknown":
            caps.append(50)
        if classification.strategy_type == "low_altitude_economy_infrastructure" and context.max_overall_confidence == "low":
            caps.append(65)
        if classification.strategy_type == "life_science_cxo_services" and context.max_overall_confidence == "low":
            caps.append(65)
        if context.overall_context_quality == "insufficient":
            caps.append(50)
        return min([score] + caps) if caps else score

    def _score_confidence(self, readiness, context) -> str:
        if context.max_overall_confidence == "low":
            return "low"
        if readiness.readiness_level in {"weak", "insufficient"}:
            return "low"
        if readiness.readiness_level == "usable_with_warnings":
            return "medium"
        if readiness.readiness_level == "sufficient" and context.max_overall_confidence == "high":
            return "high"
        return "medium"

    def _advanced_manufacturing_risk_warnings(self, classification, context) -> list[str]:
        if classification.strategy_type != "advanced_manufacturing_growth":
            return []
        risk_names = {risk.risk_name for risk in context.required_risks}
        warnings = []
        if "机器人业务兑现验证不足" in risk_names:
            warnings.append("机器人业务仍需订单和收入验证")
        if "大客户依赖验证不足" in risk_names:
            warnings.append("大客户收入占比和订单持续性需要验证")
        if "估值预期消化风险" in risk_names:
            warnings.append("估值可能已经反映部分成长预期")
        return warnings

    def _structural_risk_warnings(self, classification, context) -> list[str]:
        risk_names = {risk.risk_name for risk in context.required_risks}
        warnings = []
        if classification.strategy_type == "right_trend_growth":
            if "AI资本开支依赖风险" in risk_names:
                warnings.append("AI资本开支、云厂商需求和订单持续性需要验证")
            if "订单与客户验证不足" in risk_names:
                warnings.append("客户收入占比和订单持续性验证不足")
            if "估值预期消化风险" in risk_names:
                warnings.append("估值需要后续收入和利润增长消化")
        elif classification.strategy_type == "semiconductor_cycle":
            if "半导体周期波动风险" in risk_names:
                warnings.append("半导体订单、库存和资本开支周期存在波动风险")
            if "国产替代兑现验证风险" in risk_names:
                warnings.append("国产替代逻辑需要订单、收入和客户验证")
            if "半导体估值波动风险" in risk_names:
                warnings.append("半导体估值对周期和兑现节奏敏感")
        elif classification.strategy_type == "stable_growth":
            if "订单节奏验证风险" in risk_names:
                warnings.append("订单和项目交付节奏需要持续验证")
            if "应收账款与现金流跟踪风险" in risk_names:
                warnings.append("应收账款、回款和经营现金流需要持续跟踪")
        elif classification.strategy_type == "life_science_cxo_services":
            if any("backlog" in name or "new signed orders" in name for name in risk_names):
                warnings.append("Life-science CXO order visibility needs real backlog/new-order evidence; contract liabilities are partial_proxy only.")
            if any("customer" in name for name in risk_names):
                warnings.append("Customer concentration and geography remain confidence gates for CXO demand stability.")
            if any("overseas" in name or "U.S." in name or "geopolitical" in name for name in risk_names):
                warnings.append("Overseas regulation, Biosecure Act, sanctions, geopolitics and FX risk remain explicit CXO guards.")
            if any("one-off" in name for name in risk_names):
                warnings.append("One-off large-order distortion risk prevents strong historical trend claims.")
        return warnings

    def _business_text(self, normalized: NormalizedFundamentalInput) -> str:
        parts = [normalized.basic_info.industry or "", normalized.basic_info.main_business or ""]
        if normalized.business_composition:
            parts.extend(str(seg) for seg in normalized.business_composition.segments)
        return " ".join(parts)

    def _strategy_text_match(self, strategy_type: str, text: str) -> bool:
        keywords = {
            "resource_swing": ("银", "锡", "铜", "稀土", "有色"),
            "resource_core": ("多矿种", "资源龙头", "铜", "金"),
            "right_trend_growth": ("AI", "光模块", "PCB", "服务器", "液冷"),
            "semiconductor_cycle": ("半导体", "设备", "芯片", "晶圆", "存储"),
            "stable_growth": ("电网", "变压器", "电力设备"),
            "advanced_manufacturing_growth": (
                "汽车热管理",
                "热管理",
                "机器人",
                "机器人执行器",
                "工业自动化",
                "精密制造",
                "汽车零部件",
                "高端制造",
            ),
            "satellite_communication_infrastructure": (
                "卫星空间段",
                "卫星通信",
                "卫星传输",
                "广播电视和卫星传输服务",
                "转发器",
                "带宽资源",
                "轨位资源",
                "频段资源",
            ),
            "low_altitude_economy_infrastructure": (
                "\u901a\u822a\u8fd0\u8425",
                "\u4f4e\u7a7a\u98de\u884c\u670d\u52a1",
                "\u901a\u822a\u8fd0\u8f93",
                "\u822a\u7a7a\u5e94\u6025\u6551\u63f4",
                "\u7a7a\u4e2d\u4ea4\u901a\u7ba1\u7406",
                "\u7a7a\u7ba1\u7cfb\u7edf",
                "\u4f4e\u7a7a\u8c03\u5ea6",
                "\u4f4e\u7a7a\u8fd0\u884c\u5e73\u53f0",
                "\u6307\u6325\u8c03\u5ea6\u5e73\u53f0",
            ),
            "life_science_cxo_services": (
                "CRO",
                "CDMO",
                "CXO",
                "CMC",
                "clinical CRO",
                "drug discovery",
                "preclinical",
                "pharmaceutical outsourcing",
                "\u4e34\u5e8a\u7814\u7a76",
                "\u4e34\u5e8a CRO",
                "\u836f\u7269\u53d1\u73b0",
                "\u533b\u836f\u5916\u5305",
                "\u5408\u540c\u7814\u7a76",
            ),
        }
        return any(k in text for k in keywords.get(strategy_type, ()))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run rule-based fundamental scoring engine.")
    parser.add_argument("--input", required=True, help="Path to raw JSON fixture")
    parser.add_argument("--output", help="Optional output JSON path")
    args = parser.parse_args()

    normalized = FundamentalDataAdapter().from_file(args.input)
    classification = StockClassifier().classify(normalized)
    framework = FrameworkSelector().select(classification)
    readiness = DataReadinessPlanner().plan(normalized, classification, framework)
    context = AnalysisContextBuilder().build(normalized, classification, framework, readiness)
    result = FundamentalScoringEngine().score(normalized, classification, framework, readiness, context)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")

    print(f"stock_code: {result.stock_code}")
    print(f"stock_name: {result.stock_name}")
    print(f"strategy_type: {result.strategy_type}")
    print(f"readiness_level: {result.readiness_level}")
    print(f"context_quality: {result.context_quality}")
    print(f"max_overall_confidence: {result.max_overall_confidence}")
    print(f"weighted_total_score: {result.weighted_total_score}")
    print(f"score_confidence: {result.score_confidence}")
    print("dimension scores summary:")
    for item in result.dimension_scores:
        print(f"  - {item.dimension_name}: raw={item.raw_score}, constrained={item.constrained_score}, weight={item.weight}")
    print(f"required risks count: {len(result.required_risks)}")
    print(f"scoring_warnings: {result.scoring_warnings}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
