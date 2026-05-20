# -*- coding: utf-8 -*-
"""Assemble final fundamental_skill structured result.

This module produces FundamentalAnalysisResult, not trading advice.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

from .analysis_context_builder import AnalysisContextBuilder
from .analysis_context_schema import AnalysisContext
from .classification_schema import FundamentalFramework, StockClassificationResult
from .data_adapter import FundamentalDataAdapter
from .data_readiness_planner import DataReadinessPlanner
from .framework_selector import FrameworkSelector
from .raw_schema import FinancialMetricInput, NormalizedFundamentalInput
from .readiness_schema import DataReadinessPlan
from .schema import (
    Catalyst,
    Evidence,
    FinancialQuality,
    FundamentalAnalysisResult,
    IndustryCycle,
    InvalidationCondition,
    RiskFlag,
    ThesisCheck,
    TrackIndicator,
    ValuationView,
)
from .scoring_engine import FundamentalScoringEngine
from .scoring_schema import DimensionScore, FundamentalScoringResult
from .stock_classifier import StockClassifier
from .validators import assert_valid_result


CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}
CONFIDENCE_BY_RANK = {0: "low", 1: "medium", 2: "high"}


def _now_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _dim(scoring: FundamentalScoringResult, name: str) -> DimensionScore:
    return next(item for item in scoring.dimension_scores if item.dimension_name == name)


def _latest_metric(normalized: NormalizedFundamentalInput) -> FinancialMetricInput | None:
    return normalized.financial_metrics[0] if normalized.financial_metrics else None


def _ev(
    source: str,
    interpretation: str,
    metric_name: str | None = None,
    value: Any = None,
    period: str | None = None,
) -> Evidence:
    return Evidence(
        source=source,
        metric_name=metric_name,
        value=value,
        period=period,
        interpretation=interpretation,
    )


def _severity_max(a: str, b: str) -> str:
    rank = {"low": 0, "medium": 1, "high": 2}
    return a if rank[a] >= rank[b] else b


def _cap_confidence(confidence: str, cap: str) -> str:
    return CONFIDENCE_BY_RANK[min(CONFIDENCE_RANK[confidence], CONFIDENCE_RANK[cap])]


class FundamentalResultAssembler:
    def assemble(
        self,
        normalized: NormalizedFundamentalInput,
        classification: StockClassificationResult,
        framework: FundamentalFramework,
        readiness: DataReadinessPlan,
        context: AnalysisContext,
        scoring: FundamentalScoringResult,
        user_thesis: str | None = None,
    ) -> FundamentalAnalysisResult:
        status = self._decide_status(normalized, classification, readiness, context, scoring)
        confidence = self._decide_confidence(classification, readiness, context, scoring)
        cap_reasons = self._confidence_cap_reasons(classification, readiness, context)
        fundamental_score = self._fundamental_score(status, confidence, classification, scoring)

        analyst_summary = self._analyst_summary(
            status, confidence, classification, framework, readiness, context, cap_reasons
        )
        result = FundamentalAnalysisResult(
            stock_code=normalized.stock_code,
            stock_name=normalized.stock_name,
            analysis_date=_now_date(),
            strategy_type=classification.strategy_type,
            sub_type=getattr(classification, "sub_type", None),
            status=status,
            confidence=confidence,
            confidence_reason=self._confidence_reason(confidence, readiness, context, scoring, cap_reasons),
            fundamental_score=fundamental_score,
            business_summary=self._business_summary(normalized, classification, framework),
            key_drivers=self._key_drivers(normalized, classification, framework, context),
            financial_quality=self._financial_quality(normalized, readiness, scoring),
            valuation_view=self._valuation_view(normalized, classification, scoring),
            industry_cycle=self._industry_cycle(classification, readiness, scoring),
            risk_flags=self._risk_flags(readiness, context, scoring),
            catalysts=self._catalysts(classification, readiness),
            must_track_indicators=self._track_indicators(classification, framework, readiness),
            invalidation_conditions=self._invalidation_conditions(classification),
            thesis_check=self._thesis_check(user_thesis, normalized),
            suitable_strategy_type=framework.display_name,
            analyst_summary=analyst_summary,
            trader_summary=analyst_summary,
            data_sources=normalized.data_sources,
            data_timestamp=normalized.generated_at,
            missing_fields=sorted(
                set(
                    normalized.missing_fields
                    + readiness.critical_missing_fields
                    + readiness.high_priority_missing_fields
                )
            ),
            valid_until=None,
            refresh_triggers=list(
                dict.fromkeys(framework.must_track_indicators[:4] + readiness.recommended_data_to_collect[:4])
            ),
            raw_data_path=normalized.raw_data_path,
        )
        assert_valid_result(result)
        return result

    def _decide_status(
        self,
        normalized: NormalizedFundamentalInput,
        classification: StockClassificationResult,
        readiness: DataReadinessPlan,
        context: AnalysisContext,
        scoring: FundamentalScoringResult,
    ) -> str:
        calibrated_real_data_gap = self._real_data_calibration_exception(
            normalized, classification, readiness, scoring
        )
        if (
            readiness.readiness_level == "insufficient"
            or context.overall_context_quality == "insufficient"
            or (
                scoring.score_confidence == "low"
                and readiness.readiness_level in {"weak", "insufficient"}
                and scoring.weighted_total_score < 55
                and not calibrated_real_data_gap
            )
            or classification.strategy_type == "unknown"
            or "unknown_raw_structure" in normalized.missing_fields
        ):
            return "insufficient_data"

        risk_control = _dim(scoring, "risk_control").constrained_score
        financial_quality = _dim(scoring, "financial_quality").constrained_score
        data_quality = _dim(scoring, "data_quality").constrained_score
        high_risks = self._high_risk_count(readiness, context, scoring)
        blocked = {item.dimension_name for item in context.blocked_dimensions}
        restricted_or_blocked = {
            item.dimension_name for item in context.blocked_dimensions + context.restricted_dimensions
        }
        if (
            scoring.weighted_total_score < 45
            or risk_control < 40
            or (financial_quality < 40 and data_quality >= 60)
            or (high_risks >= 3 and readiness.readiness_level != "insufficient")
            or ("financial_quality" in blocked and "business_summary" in restricted_or_blocked)
        ) and not calibrated_real_data_gap and not self._semiconductor_data_gap_neutral_exception(
            normalized, classification, readiness
        ) and not self._satellite_data_gap_neutral_exception(
            normalized, classification, readiness
        ) and not self._low_altitude_data_gap_neutral_exception(
            normalized, classification, readiness
        ) and not self._life_science_cxo_data_gap_neutral_exception(
            normalized, classification, readiness
        ):
            return "negative"

        business_quality = _dim(scoring, "business_quality").constrained_score
        industry_cycle = _dim(scoring, "industry_cycle").constrained_score
        advanced_medium_risks = self._advanced_manufacturing_medium_risk_count(classification, context)
        advanced_supportive_exception = (
            classification.strategy_type == "advanced_manufacturing_growth"
            and advanced_medium_risks >= 3
            and readiness.readiness_level == "sufficient"
            and financial_quality >= 70
            and business_quality >= 70
        )
        growth_exception = (
            classification.strategy_type in {
                "right_trend_growth",
                "semiconductor_cycle",
                "advanced_manufacturing_growth",
            }
            and business_quality >= 70
            and industry_cycle >= 65
        )
        high_risk_exception = readiness.readiness_level == "sufficient" and scoring.score_confidence == "high"
        if (
            scoring.weighted_total_score >= 70
            and scoring.score_confidence in {"high", "medium"}
            and readiness.readiness_level in {"sufficient", "usable_with_warnings"}
            and context.max_overall_confidence in {"high", "medium"}
            and (high_risks < 2 or high_risk_exception)
            and (advanced_medium_risks < 3 or advanced_supportive_exception)
            and data_quality >= 60
            and (financial_quality >= 60 or growth_exception)
        ):
            return "supportive"
        return "neutral"

    def _real_data_calibration_exception(
        self,
        normalized: NormalizedFundamentalInput,
        classification: StockClassificationResult,
        readiness: DataReadinessPlan,
        scoring: FundamentalScoringResult,
    ) -> bool:
        if classification.strategy_type not in {"advanced_manufacturing_growth", "semiconductor_cycle"}:
            return False
        if classification.confidence not in {"high", "medium"}:
            return False
        if readiness.readiness_level != "weak":
            return False
        if scoring.weighted_total_score < 45:
            return False
        if not normalized.stock_name or normalized.stock_code == "UNKNOWN":
            return False
        if not (normalized.basic_info.industry or normalized.basic_info.main_business):
            return False
        if self._available_financial_metric_count(normalized, classification.strategy_type) < 5:
            return False

        allowed_missing = {
            "business_composition",
            "business_composition.segments",
            "valuation_metrics",
            "valuation_metrics.pe_ttm",
            "valuation_metrics.market_cap",
            "financial_metrics.accounts_receivable",
            "financial_metrics.inventory",
            "data_cutoff",
        }
        actual_missing = set(
            normalized.missing_fields
            + readiness.critical_missing_fields
            + readiness.high_priority_missing_fields
        )
        if classification.strategy_type == "advanced_manufacturing_growth":
            actual_missing.discard("financial_metrics.inventory")
        if classification.strategy_type == "semiconductor_cycle":
            actual_missing.discard("financial_metrics.accounts_receivable")
        return actual_missing <= allowed_missing

    def _available_financial_metric_count(self, normalized: NormalizedFundamentalInput, strategy_type: str) -> int:
        metric = _latest_metric(normalized)
        if not metric:
            return 0
        fields = [
            "revenue_yoy",
            "net_profit_yoy",
            "deducted_net_profit",
            "gross_margin",
            "net_margin",
            "roe",
            "operating_cashflow",
            "debt_to_asset",
        ]
        if strategy_type == "semiconductor_cycle":
            fields = ["revenue_yoy", "net_profit_yoy", "gross_margin", "roe", "operating_cashflow", "debt_to_asset"]
        return sum(1 for field in fields if getattr(metric, field, None) is not None)

    def _semiconductor_data_gap_neutral_exception(
        self,
        normalized: NormalizedFundamentalInput,
        classification: StockClassificationResult,
        readiness: DataReadinessPlan,
    ) -> bool:
        if classification.strategy_type != "semiconductor_cycle":
            return False
        if not normalized.stock_name or not (normalized.basic_info.industry or normalized.basic_info.main_business):
            return False
        if self._available_financial_metric_count(normalized, "semiconductor_cycle") < 5:
            return False
        allowed_missing = {
            "business_composition",
            "business_composition.segments",
            "valuation_metrics",
            "valuation_metrics.pe_ttm",
            "valuation_metrics.market_cap",
            "financial_metrics.inventory",
            "data_cutoff",
        }
        actual_missing = set(
            normalized.missing_fields
            + readiness.critical_missing_fields
            + readiness.high_priority_missing_fields
        )
        return actual_missing <= allowed_missing

    def _satellite_data_gap_neutral_exception(
        self,
        normalized: NormalizedFundamentalInput,
        classification: StockClassificationResult,
        readiness: DataReadinessPlan,
    ) -> bool:
        if classification.strategy_type != "satellite_communication_infrastructure":
            return False
        if not normalized.financial_metrics:
            return False
        if not normalized.business_composition or not normalized.business_composition.segments:
            return False
        if not (normalized.basic_info.industry or normalized.basic_info.main_business):
            return False
        core_available = {
            "basic_info.industry",
            "basic_info.main_business",
            "business_composition.segments",
            "financial_metrics.gross_margin",
            "financial_metrics.operating_cashflow",
            "financial_metrics.accounts_receivable",
            "financial_metrics.contract_liabilities",
            "financial_metrics.capex",
        }
        actual_missing = set(readiness.critical_missing_fields + readiness.high_priority_missing_fields)
        return not (core_available & actual_missing)

    def _low_altitude_data_gap_neutral_exception(
        self,
        normalized: NormalizedFundamentalInput,
        classification: StockClassificationResult,
        readiness: DataReadinessPlan,
    ) -> bool:
        if classification.strategy_type != "low_altitude_economy_infrastructure":
            return False
        if not normalized.financial_metrics:
            return False
        if not normalized.business_composition or not normalized.business_composition.segments:
            return False
        if not (normalized.basic_info.industry or normalized.basic_info.main_business):
            return False
        core_available = {
            "basic_info.industry",
            "basic_info.main_business",
            "business_composition.segments",
            "financial_metrics.gross_margin",
            "financial_metrics.operating_cashflow",
            "financial_metrics.accounts_receivable",
            "financial_metrics.contract_liabilities",
        }
        actual_missing = set(readiness.critical_missing_fields + readiness.high_priority_missing_fields)
        return not (core_available & actual_missing)

    def _life_science_cxo_data_gap_neutral_exception(
        self,
        normalized: NormalizedFundamentalInput,
        classification: StockClassificationResult,
        readiness: DataReadinessPlan,
    ) -> bool:
        if classification.strategy_type != "life_science_cxo_services":
            return False
        if not normalized.financial_metrics:
            return False
        if not normalized.business_composition or not normalized.business_composition.segments:
            return False
        if not (normalized.basic_info.industry or normalized.basic_info.main_business):
            return False
        core_available = {
            "basic_info.industry",
            "basic_info.main_business",
            "business_composition.segments",
            "life_science_cxo.cxo_revenue_share",
            "financial_metrics.revenue",
            "financial_metrics.gross_margin",
            "financial_metrics.operating_cashflow",
            "financial_metrics.accounts_receivable",
            "financial_metrics.contract_liabilities",
            "financial_metrics.capex",
        }
        actual_missing = set(readiness.critical_missing_fields + readiness.high_priority_missing_fields)
        return not (core_available & actual_missing)

    def _decide_confidence(
        self,
        classification: StockClassificationResult,
        readiness: DataReadinessPlan,
        context: AnalysisContext,
        scoring: FundamentalScoringResult,
    ) -> str:
        if (
            context.max_overall_confidence == "low"
            or scoring.score_confidence == "low"
            or readiness.readiness_level in {"insufficient", "weak"}
        ):
            confidence = "low"
        elif context.max_overall_confidence == "medium" or scoring.score_confidence == "medium":
            confidence = "medium"
        elif (
            context.max_overall_confidence == "high"
            and scoring.score_confidence == "high"
            and readiness.readiness_level == "sufficient"
        ):
            confidence = "high"
        else:
            confidence = "medium"

        if self._resource_price_missing(classification, readiness, context):
            confidence = _cap_confidence(confidence, "medium")
            if readiness.readiness_level != "sufficient":
                confidence = _cap_confidence(confidence, "low")
        if self._growth_margin_missing(classification, readiness, context):
            confidence = _cap_confidence(confidence, "medium")
        if self._semiconductor_inventory_missing(classification, readiness, context):
            confidence = _cap_confidence(confidence, "medium")
        if self._stable_growth_core_missing(classification, readiness, context):
            confidence = _cap_confidence(confidence, "medium")
            if readiness.readiness_level == "weak":
                confidence = _cap_confidence(confidence, "low")
        if self._low_altitude_core_gating_missing(classification, readiness, context):
            confidence = _cap_confidence(confidence, "medium")
            if context.max_overall_confidence == "low":
                confidence = _cap_confidence(confidence, "low")
        if self._life_science_cxo_core_gating_missing(classification, readiness, context):
            confidence = _cap_confidence(confidence, "medium")
            if context.max_overall_confidence == "low":
                confidence = _cap_confidence(confidence, "low")
        if self._advanced_manufacturing_medium_risk_count(classification, context) >= 2:
            confidence = _cap_confidence(confidence, "medium")
        if self._structural_medium_risk_count(classification, context) >= 2:
            confidence = _cap_confidence(confidence, "medium")
        if self._has_high_severity_data_missing(readiness, context):
            confidence = _cap_confidence(confidence, "medium")
        if any(
            item.field_name.startswith("valuation_metrics") and item.status in {"missing", "partial"}
            for item in readiness.field_readiness
        ):
            confidence = _cap_confidence(confidence, "medium")
        return confidence

    def _fundamental_score(self, status: str, confidence: str, classification, scoring) -> int:
        score = scoring.weighted_total_score
        if status == "insufficient_data":
            score = min(score, 50)
        if confidence == "low":
            score = min(score, 70)
        if classification.strategy_type == "unknown":
            score = min(score, 50)
        return score

    def _confidence_reason(self, confidence, readiness, context, scoring, cap_reasons: list[str]) -> str:
        parts = [
            f"置信度为 {confidence}",
            f"数据准备度为 {readiness.readiness_level}",
            f"上下文质量为 {context.overall_context_quality}",
            f"规则评分置信度为 {scoring.score_confidence}",
        ]
        if cap_reasons:
            parts.append("置信度封顶原因：" + "；".join(cap_reasons))
        return "，".join(parts) + "。"

    def _business_summary(self, normalized, classification, framework) -> str:
        if classification.strategy_type == "unknown":
            return "业务信息不足，暂时不能稳定识别公司基本面框架。"
        industry = normalized.basic_info.industry or "行业信息缺失"
        main_business = normalized.basic_info.main_business or "主营业务信息缺失"
        if not normalized.business_composition or not normalized.business_composition.segments:
            return (
                f"公司处于{industry}，主营描述为：{main_business}。由于主营构成缺失，"
                f"不能断言具体收入来源。适用框架：{framework.display_name}。"
            )
        segments = [
            str(seg.get("segment_name"))
            for seg in normalized.business_composition.segments[:3]
            if isinstance(seg, dict) and seg.get("segment_name")
        ]
        segment_text = "、".join(segments) if segments else "主营构成名称不完整"
        return (
            f"公司处于{industry}，主营描述为：{main_business}。已识别主营构成包括"
            f"{segment_text}，适用框架为{framework.display_name}。"
        )

    def _key_drivers(self, normalized, classification, framework, context) -> list[str]:
        prohibited_types = {claim.claim_type for claim in context.prohibited_claims}
        drivers = []
        metric = _latest_metric(normalized)
        if metric and metric.revenue_yoy is not None:
            drivers.append(f"营收增速数据可用于验证成长或周期兑现：{metric.revenue_yoy}。")
        if metric and metric.net_profit_yoy is not None:
            drivers.append(f"净利润增速数据可用于观察盈利弹性：{metric.net_profit_yoy}。")

        if classification.strategy_type in {"resource_swing", "resource_core"}:
            if "commodity_price_benefit_confirmed" in prohibited_types:
                drivers.append("相关商品价格是后续关键观察项，资源品价格需要进一步验证。")
            else:
                drivers.append("商品价格可能是重要跟踪变量，但仍需持续验证。")
        if classification.strategy_type == "right_trend_growth":
            if "margin_improvement_confirmed" in prohibited_types:
                drivers.append("毛利率数据需要进一步验证，盈利能力变化仍需跟踪。")
            else:
                drivers.append("营收、利润、毛利率、订单和客户资本开支是高景气兑现的核心跟踪项。")
        if classification.strategy_type == "semiconductor_cycle":
            if "inventory_cycle_healthy" in prohibited_types:
                drivers.append("库存周期仍需验证，存货数据是后续关键跟踪项。")
            else:
                drivers.append("订单、毛利率、存货周期、国产替代兑现和资本开支周期是半导体框架的核心变量。")
        if classification.strategy_type == "advanced_manufacturing_growth":
            if "advanced_manufacturing_revenue_confirmed" in prohibited_types:
                drivers.append("机器人和汽车热管理业务仍需订单和收入验证，不能仅按概念确认贡献。")
            elif "robot_business_confirmed" in prohibited_types:
                drivers.append("机器人相关业务是重要跟踪变量，但仍需订单和收入验证。")
            else:
                drivers.append("汽车热管理、机器人执行器和工业自动化业务是高端制造成长框架的核心跟踪项。")
        if classification.strategy_type == "satellite_communication_infrastructure":
            drivers.append("卫星资源、轨位/频段、转发器/带宽容量、容量利用率和客户合同结构是卫星通信基础设施框架的核心变量。")
            drivers.append("合同负债只能作为订单可见度 proxy，capex 只能作为长期资产购建现金支出观察。")

        drivers.extend([f"框架关注：{item}" for item in framework.required_focus[:3]])
        if classification.strategy_type == "low_altitude_economy_infrastructure":
            drivers.append("Low-altitude economy is a sector cluster; this framework covers only infrastructure and operation service.")
            drivers.append("Sub_type routing must separate aviation_operations_service from airspace_platform_system; missing operation, contract, customer, acceptance or safety data caps confidence.")
        if classification.strategy_type == "life_science_cxo_services":
            drivers.append("CXO/CRO/CDMO are pharmaceutical R&D/manufacturing outsourcing services, not self-owned innovative drug pipeline valuation.")
            drivers.append("Backlog, new orders, customer structure, overseas exposure, CDMO utilization and clinical project progress are confidence gates; contract liabilities are partial_proxy only.")
            if normalized.stock_code.endswith("300363") or normalized.stock_code == "300363":
                drivers.append("Porton is treated as a high-volatility CDMO sample; historical data may be affected by one-off orders.")
        max_drivers = 8 if classification.strategy_type == "life_science_cxo_services" else 6
        return list(dict.fromkeys(drivers))[:max_drivers]

    def _financial_quality(self, normalized, readiness, scoring) -> FinancialQuality:
        metric = _latest_metric(normalized)
        score = _dim(scoring, "financial_quality").constrained_score
        missing = set(readiness.critical_missing_fields + readiness.high_priority_missing_fields)
        evidence = [
            _ev(
                "scoring.financial_quality",
                f"财务质量维度受上下文约束后得分为 {score}。",
                "financial_quality_score",
                score,
            )
        ]
        if metric:
            evidence.append(_ev("financial_metrics", "使用最近一期财务指标生成财务质量摘要。", period=metric.period))
        return FinancialQuality(
            revenue_trend=self._trend(metric.revenue_yoy if metric else None, "营收"),
            profit_trend=self._trend(metric.net_profit_yoy if metric else None, "利润"),
            margin_trend=(
                "毛利率数据缺失，不能断言改善。"
                if "financial_metrics.gross_margin" in missing
                else self._level(metric.gross_margin if metric else None, "毛利率")
            ),
            cashflow_quality=(
                "经营现金流数据缺失，不能写为良好。"
                if "financial_metrics.operating_cashflow" in missing
                else self._cashflow_quality(metric.operating_cashflow if metric else None)
            ),
            debt_pressure=self._debt_pressure(metric.debt_to_asset if metric else None),
            one_off_profit_risk=(
                "扣非净利润缺失，需要关注一次性收益或非经常性损益影响。"
                if "financial_metrics.deducted_net_profit" in missing
                else "已纳入扣非净利润字段观察。"
            ),
            score=score,
            evidence=evidence,
        )

    def _valuation_view(self, normalized, classification, scoring) -> ValuationView:
        score = _dim(scoring, "valuation_reasonableness").constrained_score
        val = normalized.valuation_metrics
        if not val:
            level = "unknown"
            method = "估值数据缺失，无法形成稳定估值观察。"
        else:
            pe = val.pe_ttm
            if pe is None or pe <= 0:
                level = "unknown"
            elif pe > 70:
                level = "high"
            else:
                level = "reasonable"
            method = "按策略类型保守解释 PE/PB/市值；成长和半导体框架需考虑估值波动。"
        if classification.strategy_type == "satellite_communication_infrastructure":
            method = (
                "PE/PB/PS 对卫星通信基础设施只能作为 secondary valuation evidence；"
                "估值需要结合资产寿命、折旧、现金流稳定性、容量利用率、客户结构和更新 capex。"
            )
        return ValuationView(
            valuation_level=level,
            valuation_method=method,
            peer_comparison=None,
            historical_percentile=None,
            score=score,
            evidence=[
                _ev(
                    "scoring.valuation_reasonableness",
                    f"估值维度约束后得分为 {score}。",
                    "valuation_score",
                    score,
                )
            ],
        )

    def _industry_cycle(self, classification, readiness, scoring) -> IndustryCycle:
        score = _dim(scoring, "industry_cycle").constrained_score
        missing = set(readiness.critical_missing_fields + readiness.high_priority_missing_fields)
        if classification.strategy_type in {"resource_swing", "resource_core"} and "external.commodity_prices" in missing:
            position = "unknown"
            trend = "缺少商品价格数据，资源股周期判断受商品价格数据缺失限制。"
        elif classification.strategy_type == "semiconductor_cycle" and "financial_metrics.inventory" in missing:
            position = "unknown"
            trend = "缺少存货数据，库存与半导体周期状态仍需验证。"
        elif classification.strategy_type == "unknown":
            position = "unknown"
            trend = "分类和数据不足。"
        elif classification.strategy_type == "satellite_communication_infrastructure":
            position = "unknown" if readiness.readiness_level in {"weak", "insufficient"} else "neutral"
            trend = "行业专属运营数据缺失时，不足以判断商业航天业务兑现、容量利用率或客户需求稳定性。"
        elif classification.strategy_type == "life_science_cxo_services":
            position = "unknown" if readiness.readiness_level in {"weak", "insufficient"} else "neutral"
            trend = "Missing backlog/new orders/customer structure/overseas exposure/CDMO utilization/clinical project evidence is insufficient to judge industry prosperity or business realization."
        elif readiness.readiness_level in {"weak", "insufficient"}:
            position = "unknown"
            trend = "关键数据缺失，周期判断需要降低置信度。"
        else:
            position = "neutral"
            trend = "可做框架内观察，但不写成确定性周期结论。"
        return IndustryCycle(
            cycle_position=position,
            industry_trend=trend,
            key_external_variables=framework_vars(classification.strategy_type),
            score=score,
            evidence=[
                _ev(
                    "scoring.industry_cycle",
                    f"行业周期维度约束后得分为 {score}。",
                    "industry_cycle_score",
                    score,
                )
            ],
        )

    def _risk_flags(self, readiness, context, scoring) -> list[RiskFlag]:
        risks: dict[str, RiskFlag] = {}
        for risk in list(context.required_risks) + list(scoring.required_risks):
            risks[risk.risk_name] = RiskFlag(
                name=risk.risk_name,
                severity=risk.severity,
                evidence=[_ev("analysis_context.required_risks", risk.reason)],
                monitor_method="补充对应数据并在后续分析中复核。",
            )
        for blocker in readiness.analysis_blockers:
            name = blocker.split("，")[0].replace("。", "")
            existing = risks.get(name)
            severity = "high" if "缺少" in blocker else "medium"
            if existing:
                risks[name] = existing.model_copy(update={"severity": _severity_max(existing.severity, severity)})
            else:
                risks[name] = RiskFlag(
                    name=name,
                    severity=severity,
                    evidence=[_ev("readiness.analysis_blockers", blocker)],
                    monitor_method="补充数据后重新评估该风险。",
                )
        missing = set(readiness.critical_missing_fields + readiness.high_priority_missing_fields)
        if any(field.startswith("valuation_metrics") for field in missing):
            risks.setdefault(
                "估值数据缺失",
                RiskFlag(
                    name="估值数据缺失",
                    severity="medium",
                    evidence=[_ev("readiness.missing_fields", "估值数据缺失，不能判断估值是否合理。")],
                    monitor_method="补充 PE、PB、市值和估值分位等估值数据后再复核。",
                ),
            )
        return list(risks.values())

    def _catalysts(self, classification, readiness) -> list[Catalyst]:
        missing = set(readiness.critical_missing_fields + readiness.high_priority_missing_fields)
        catalysts = []
        if classification.strategy_type in {"resource_swing", "resource_core"}:
            catalysts.append(
                Catalyst(
                    name="商品价格与利润弹性验证",
                    catalyst_type="commodity_price",
                    evidence=[_ev("framework", "商品价格是资源框架的重要外部变量。")],
                    expected_timeframe=None,
                    uncertainty="high" if "external.commodity_prices" in missing else "medium",
                )
            )
        if classification.strategy_type in {
            "right_trend_growth",
            "semiconductor_cycle",
            "advanced_manufacturing_growth",
        }:
            catalysts.append(
                Catalyst(
                    name="收入增长与订单验证",
                    catalyst_type="order",
                    evidence=[_ev("framework", "订单和收入增长是该框架的核心观察项。")],
                    expected_timeframe=None,
                    uncertainty="high" if readiness.readiness_level in {"weak", "insufficient"} else "medium",
                )
            )
        if not catalysts:
            catalysts.append(
                Catalyst(
                    name="财务数据更新",
                    catalyst_type="earnings",
                    evidence=[_ev("readiness", "后续财务数据更新可改善分析质量。")],
                    expected_timeframe=None,
                    uncertainty="medium",
                )
            )
        if classification.strategy_type == "life_science_cxo_services":
            catalysts = [
                Catalyst(
                    name="CXO service demand and order-visibility validation",
                    catalyst_type="order",
                    evidence=[_ev("framework", "Requires real backlog/new orders, customer structure, overseas exposure, CDMO utilization or clinical project progress; CXO concept words are not evidence.")],
                    expected_timeframe=None,
                    uncertainty="high" if readiness.readiness_level in {"weak", "insufficient", "usable_with_warnings"} else "medium",
                )
            ]
        return catalysts[:3]

    def _track_indicators(self, classification, framework, readiness) -> list[TrackIndicator]:
        names = list(framework.must_track_indicators)
        if classification.strategy_type == "low_altitude_economy_infrastructure":
            names = [
                "low-altitude revenue share",
                "accounts receivable",
                "contract liabilities",
                "operating cashflow",
                "customer structure",
                "safety events / accidents / regulatory penalties",
            ]
            if getattr(classification, "sub_type", None) == "aviation_operations_service":
                names.extend(["fleet size", "operating hours", "flight sorties", "aircraft type mix"])
            else:
                names.extend(["contract amount", "project acceptance progress", "platform dispatch volume", "software service revenue share"])
        if classification.strategy_type == "life_science_cxo_services":
            names = [
                "CXO / CRO / CDMO related revenue share",
                "backlog / on-hand orders",
                "new signed orders",
                "contract liabilities partial_proxy",
                "customer concentration",
                "overseas revenue share",
                "North America / U.S. revenue share",
                "gross margin",
                "operating cashflow",
                "accounts receivable",
                "collection cycle",
                "capex",
                "FX impact",
                "overseas regulatory / geopolitical / Biosecure Act / sanction risk",
                "project cancellation or delay",
                "one-off large-order marker",
            ]
            subtype = getattr(classification, "sub_type", None)
            if subtype == "integrated_cxo_platform":
                names.extend(["business-segment revenue mix", "drug discovery revenue", "preclinical revenue", "CMC / CDMO revenue", "active customers", "employee/scientist count"])
            elif subtype == "cdmo_manufacturing_services":
                names.extend(["CDMO orders", "CDMO capacity utilization", "commercial project count", "capacity expansion progress", "GMP/FDA/NMPA compliance event", "major customer concentration"])
            elif subtype == "clinical_cro_services":
                names.extend(["clinical project count", "clinical trial service revenue", "SMO / data-statistics revenue", "project acceptance progress", "project collection cycle"])
        if classification.strategy_type == "resource_swing":
            names.extend(["对应商品价格", "扣非净利润", "经营现金流", "主营构成"])
        elif classification.strategy_type == "right_trend_growth":
            names.extend(["营收增速", "净利润增速", "毛利率", "订单或客户资本开支", "云厂商资本开支", "客户收入占比", "估值消化"])
        elif classification.strategy_type == "semiconductor_cycle":
            names.extend(["毛利率", "存货", "研发投入或订单", "经营现金流", "行业资本开支", "国产替代订单兑现", "估值波动"])
        elif classification.strategy_type == "stable_growth":
            names.extend(["经营现金流", "ROE", "应收账款", "订单", "新签订单", "项目交付", "回款"])
        elif classification.strategy_type == "advanced_manufacturing_growth":
            names.extend([
                "营收增速",
                "净利润增速",
                "毛利率",
                "经营现金流",
                "应收账款",
                "业务构成",
                "机器人相关业务收入或订单",
                "汽车热管理业务收入或订单",
            ])
        elif classification.strategy_type == "satellite_communication_infrastructure":
            names.extend([
                "卫星资源和轨位 / 频段资源",
                "转发器 / 带宽容量",
                "容量利用率 / 出租率",
                "单位带宽价格",
                "客户结构和合同期限",
                "卫星剩余寿命",
                "折旧摊销",
                "卫星发射计划",
                "卫星故障 / 保险事件",
                "合同负债",
                "capex",
            ])
        missing = set(readiness.critical_missing_fields + readiness.high_priority_missing_fields)
        if any(field.startswith("valuation_metrics") for field in missing):
            names.extend(["PE", "PB", "市值", "估值分位"])
        if classification.strategy_type == "low_altitude_economy_infrastructure":
            names.extend([
                "low-altitude revenue share",
                "customer structure",
                "accounts receivable",
                "contract liabilities",
                "operating cashflow",
                "low-altitude business gross margin",
                "safety events / accidents / regulatory penalties",
                "fleet size",
                "operating hours",
                "flight sorties",
                "contract amount",
                "project acceptance progress",
                "platform dispatch volume",
            ])
        if classification.strategy_type == "life_science_cxo_services":
            names.extend([
                "CXO / CRO / CDMO related revenue share",
                "backlog / on-hand orders",
                "new signed orders",
                "contract liabilities partial_proxy",
                "customer concentration",
                "overseas revenue share",
                "North America / U.S. revenue share",
                "CDMO capacity utilization",
                "clinical project count",
                "GMP/FDA/NMPA compliance event",
                "one-off large-order marker",
            ])
        names.extend(readiness.recommended_data_to_collect[:4])
        out = []
        max_items = 25 if classification.strategy_type == "life_science_cxo_services" else 12
        for name in list(dict.fromkeys(names))[:max_items]:
            out.append(
                TrackIndicator(
                    name=name,
                    current_value=None,
                    importance=(
                        "high"
                        if name in readiness.recommended_data_to_collect
                        or "经营现金流" in name
                        or "扣非" in name
                        else "medium"
                    ),
                    monitor_frequency="quarterly",
                    reason="用于更新基本面分析和置信度。",
                )
            )
        return out

    def _invalidation_conditions(self, classification) -> list[InvalidationCondition]:
        mapping = {
            "resource_swing": [
                ("商品价格趋势反转", "商品价格和库存数据"),
                ("扣非利润明显弱于归母利润", "扣非净利润与归母净利润对比"),
                ("经营现金流与利润背离", "经营现金流和利润表数据"),
                ("主营构成无法支持资源暴露逻辑", "主营构成明细"),
            ],
            "resource_core": [
                ("商品价格组合走弱", "铜、金等商品价格组合"),
                ("现金流恶化", "经营现金流数据"),
                ("资本开支失控", "资本开支和债务数据"),
                ("主营构成无法支持资源龙头逻辑", "主营构成明细"),
            ],
            "right_trend_growth": [
                ("营收或利润增速显著放缓", "收入和利润同比数据"),
                ("毛利率持续下滑", "毛利率连续变化"),
                ("订单或客户资本开支低于预期", "订单和客户资本开支数据"),
                ("估值无法被业绩消化", "估值与业绩增速对比"),
            ],
            "semiconductor_cycle": [
                ("存货大幅增加", "存货和周转数据"),
                ("毛利率下降", "毛利率数据"),
                ("国产替代或订单进展低于预期", "订单和业务进展数据"),
                ("下游资本开支下行", "行业资本开支数据"),
            ],
            "stable_growth": [
                ("经营现金流恶化", "经营现金流数据"),
                ("ROE 下滑", "ROE 数据"),
                ("应收账款压力上升", "应收账款数据"),
                ("订单增长低于预期", "订单数据"),
            ],
            "advanced_manufacturing_growth": [
                ("营收或利润增速明显放缓", "收入和利润同比数据"),
                ("毛利率持续下滑", "毛利率连续变化"),
                ("经营现金流与利润背离", "经营现金流和利润数据"),
                ("机器人或新业务收入和订单无法验证", "机器人相关业务收入或订单数据"),
                ("大客户需求低于预期", "客户订单或收入占比数据"),
                ("估值无法被业绩增长消化", "估值与业绩增速对比"),
            ],
            "life_science_cxo_services": [
                ("CXO/CRO/CDMO revenue share cannot be confirmed or drops below the routing threshold", "business composition and segment revenue disclosure"),
                ("Backlog, new signed orders, customer concentration or overseas exposure deteriorates or remains unavailable", "backlog, new-order, customer and regional disclosure"),
                ("CDMO utilization, commercial project count, capacity expansion or GMP/FDA/NMPA compliance deteriorates", "CDMO utilization, project, capex and compliance-event data"),
                ("Clinical project count, acceptance progress, cancellation/delay or collection cycle deteriorates", "clinical project, acceptance, cancellation/delay and receivables/collection data"),
                ("One-off large-order distortion or major customer concentration invalidates historical trend comparison", "single customer/product/order history and major-customer share"),
            ],
            "satellite_communication_infrastructure": [
                ("容量利用率或出租率恶化", "容量利用率 / 出租率数据"),
                ("客户结构或合同期限恶化", "客户集中度、客户类型和合同期限结构"),
                ("卫星寿命、折旧或发射计划出现重大不确定性", "卫星剩余寿命、折旧摊销、发射计划和资产减值披露"),
                ("经营现金流与利润背离", "经营现金流、利润和应收账款数据"),
                ("商业航天新业务无法兑现", "商业航天新业务收入、订单和现金流证据"),
            ],
        }
        pairs = mapping.get(classification.strategy_type, [("关键数据仍无法补全", "基础信息、财务指标和主营构成")])
        return [
            InvalidationCondition(
                condition=condition,
                evidence_needed=evidence,
                downstream_review_hint="需要后续分析层复核",
                action_hint_for_trader="需要后续分析层复核",
            )
            for condition, evidence in pairs[:4]
        ]

    def _thesis_check(self, user_thesis, normalized) -> ThesisCheck:
        if not user_thesis:
            return ThesisCheck(
                user_thesis=None,
                thesis_support="none",
                supporting_evidence=[],
                opposing_evidence=[],
                missing_evidence=[],
            )
        text = (normalized.basic_info.industry or "") + " " + (normalized.basic_info.main_business or "")
        support = "unverified"
        supporting = []
        for word in user_thesis.split():
            if word and word in text:
                support = "partially_supported"
                supporting.append(_ev("basic_info", f"用户假设中的关键词在基础信息中出现：{word}。"))
                break
        return ThesisCheck(
            user_thesis=user_thesis,
            thesis_support=support,
            supporting_evidence=supporting,
            opposing_evidence=[],
            missing_evidence=[] if supporting else ["缺少可直接验证用户假设的数据"],
        )

    def _analyst_summary(
        self,
        status,
        confidence,
        classification,
        framework,
        readiness,
        context,
        cap_reasons: list[str],
    ) -> str:
        status_meaning = {
            "supportive": "基本面支持进入后续综合评估",
            "neutral": "基本面没有明显否定，但支持力度不足",
            "negative": "基本面不支持继续评估，或风险明显高于逻辑",
            "insufficient_data": "数据不足，不能可靠判断",
        }[status]
        risks = "、".join([r.risk_name for r in context.required_risks[:3]]) or "暂无高优先级数据风险"
        limitations = list(cap_reasons)
        if status == "supportive" and confidence == "medium":
            limitations.append("基本面支持后续评估，但仍存在关键验证项")
        if self._resource_price_missing(classification, readiness, context):
            limitations.append("外部价格变量未验证")
        if classification.strategy_type == "advanced_manufacturing_growth":
            limitations.append("机器人相关业务仍需订单和收入验证")
            risk_names = {risk.risk_name for risk in context.required_risks}
            if "大客户依赖验证不足" in risk_names:
                limitations.append("大客户收入占比和订单持续性需要跟踪")
            if "估值预期消化风险" in risk_names:
                limitations.append("估值需要业绩增长消化")
        risk_names = {risk.risk_name for risk in context.required_risks}
        if classification.strategy_type == "right_trend_growth":
            if "AI资本开支依赖风险" in risk_names:
                limitations.append("AI资本开支和云厂商需求节奏需要跟踪")
            if "订单与客户验证不足" in risk_names:
                limitations.append("订单、客户收入占比和订单持续性需要验证")
            if "估值预期消化风险" in risk_names:
                limitations.append("估值需要收入和利润增长消化")
        elif classification.strategy_type == "semiconductor_cycle":
            if "半导体周期波动风险" in risk_names:
                limitations.append("半导体订单、库存和资本开支周期需要跟踪")
            if "国产替代兑现验证风险" in risk_names:
                limitations.append("国产替代需要订单、收入和客户验证")
            if "半导体估值波动风险" in risk_names:
                limitations.append("半导体估值对周期和兑现节奏敏感")
        elif classification.strategy_type == "stable_growth":
            if "订单节奏验证风险" in risk_names:
                limitations.append("订单和项目交付节奏需要验证")
            if "应收账款与现金流跟踪风险" in risk_names:
                limitations.append("应收账款、回款和经营现金流需要跟踪")
        limitation_text = "；".join(dict.fromkeys(limitations)) or "暂无额外置信度封顶因素"
        risk_prefix = (
            "存在高风险，"
            if readiness.critical_missing_fields or any(r.severity == "high" for r in context.required_risks)
            else ""
        )
        return (
            f"基本面状态为 {status}，含义是：{status_meaning}；置信度 {confidence}。"
            f"strategy_type 为 {classification.strategy_type}，公司属于{framework.display_name}。"
            f"主要限制因素：{limitation_text}。{risk_prefix}主要风险包括：{risks}。"
        )

    def _trader_summary(
        self,
        status,
        confidence,
        classification,
        framework,
        readiness,
        context,
        cap_reasons: list[str],
    ) -> str:
        """Deprecated compatibility wrapper; use _analyst_summary for new code."""
        return self._analyst_summary(
            status, confidence, classification, framework, readiness, context, cap_reasons
        )

    def _trend(self, value, label) -> str | None:
        if value is None:
            return f"{label}趋势数据缺失"
        if value > 20:
            return f"{label}同比增长较快"
        if value < 0:
            return f"{label}同比下降"
        return f"{label}同比变化温和"

    def _level(self, value, label) -> str | None:
        if value is None:
            return f"{label}数据缺失"
        return f"{label}为 {value}"

    def _cashflow_quality(self, value) -> str:
        if value is None:
            return "经营现金流数据缺失"
        if value > 0:
            return "经营现金流为正，但仍需结合利润和周转验证"
        return "经营现金流为负，需要关注盈利兑现能力"

    def _debt_pressure(self, value) -> str | None:
        if value is None:
            return "资产负债率数据缺失"
        if value < 60:
            return "资产负债率低于60"
        return "资产负债率不低，需要关注债务压力"

    def _confidence_cap_reasons(self, classification, readiness, context) -> list[str]:
        reasons = []
        if self._resource_price_missing(classification, readiness, context):
            reasons.append("资源股周期判断受商品价格数据缺失限制")
        if self._growth_margin_missing(classification, readiness, context):
            reasons.append("毛利率数据缺失，盈利能力判断需要降置信度")
        if self._semiconductor_inventory_missing(classification, readiness, context):
            reasons.append("存货数据缺失，半导体周期判断需要降置信度")
        if self._stable_growth_core_missing(classification, readiness, context):
            reasons.append("现金流或 ROE 数据缺失，稳健性判断需要降置信度")
        if self._satellite_core_gating_missing(classification, readiness, context):
            reasons.append("缺容量利用率、客户结构、卫星寿命或折旧摊销，卫星通信基础设施判断不得高置信度")
        if self._life_science_cxo_core_gating_missing(classification, readiness, context):
            reasons.append("Life-science CXO judgement cannot use high confidence while backlog/new orders/customer/overseas exposure/CDMO utilization/clinical project gates are missing.")
        if self._advanced_manufacturing_medium_risk_count(classification, context) >= 2:
            reasons.append("高端制造新业务、大客户或估值验证风险较多")
        if self._structural_medium_risk_count(classification, context) >= 2:
            if classification.strategy_type == "right_trend_growth":
                reasons.append("高景气成长股存在资本开支、订单客户或估值验证风险")
            elif classification.strategy_type == "semiconductor_cycle":
                reasons.append("半导体存在周期、国产替代兑现或估值波动风险")
            elif classification.strategy_type == "stable_growth":
                reasons.append("稳健成长股存在订单节奏或回款现金流跟踪风险")
        if self._has_high_severity_data_missing(readiness, context):
            reasons.append("存在高严重度数据缺失风险")
        return list(dict.fromkeys(reasons))

    def _resource_price_missing(self, classification, readiness, context) -> bool:
        if classification.strategy_type not in {"resource_swing", "resource_core"}:
            return False
        return (
            "external.commodity_prices" in readiness.high_priority_missing_fields
            or any(
                item.field_name == "external.commodity_prices" and item.status in {"missing", "partial"}
                for item in readiness.field_readiness
            )
            or any("商品价格数据缺失" in risk.risk_name for risk in context.required_risks)
        )

    def _growth_margin_missing(self, classification, readiness, context) -> bool:
        if classification.strategy_type != "right_trend_growth":
            return False
        return (
            "financial_metrics.gross_margin" in readiness.critical_missing_fields
            or "financial_metrics.gross_margin" in readiness.high_priority_missing_fields
            or any("毛利率数据缺失" in risk.risk_name for risk in context.required_risks)
            or any(claim.claim_type == "margin_improvement_confirmed" for claim in context.prohibited_claims)
        )

    def _semiconductor_inventory_missing(self, classification, readiness, context) -> bool:
        if classification.strategy_type != "semiconductor_cycle":
            return False
        return (
            "financial_metrics.inventory" in readiness.critical_missing_fields
            or "financial_metrics.inventory" in readiness.high_priority_missing_fields
            or any("存货数据缺失" in risk.risk_name for risk in context.required_risks)
            or any(claim.claim_type == "inventory_cycle_healthy" for claim in context.prohibited_claims)
        )

    def _stable_growth_core_missing(self, classification, readiness, context) -> bool:
        if classification.strategy_type != "stable_growth":
            return False
        missing = set(readiness.critical_missing_fields + readiness.high_priority_missing_fields)
        return (
            "financial_metrics.operating_cashflow" in missing
            or "financial_metrics.roe" in missing
            or any(risk.risk_name in {"经营现金流数据缺失", "ROE 数据缺失"} for risk in context.required_risks)
        )

    def _satellite_core_gating_missing(self, classification, readiness, context) -> bool:
        if classification.strategy_type != "satellite_communication_infrastructure":
            return False
        missing = {
            item.field_name
            for item in readiness.field_readiness
            if item.status in {"missing", "partial"}
        }
        core_gating = {
            "satellite.capacity_utilization_or_lease_rate",
            "satellite.customer_structure_or_concentration",
            "satellite.design_or_remaining_life",
            "financial_metrics.depreciation_amortization",
        }
        return bool(core_gating & missing)

    def _has_high_severity_data_missing(self, readiness, context) -> bool:
        return bool(readiness.critical_missing_fields) or any(
            risk.severity == "high" and "数据缺失" in risk.risk_name for risk in context.required_risks
        )

    def _low_altitude_core_gating_missing(self, classification, readiness, context) -> bool:
        if classification.strategy_type != "low_altitude_economy_infrastructure":
            return False
        missing = {
            item.field_name
            for item in readiness.field_readiness
            if item.status in {"missing", "partial"}
        }
        shared = {"low_altitude.revenue_share", "low_altitude.customer_structure", "low_altitude.safety_or_regulatory_event"}
        if getattr(classification, "sub_type", None) == "aviation_operations_service":
            subtype_fields = {"low_altitude.fleet_size", "low_altitude.operating_hours", "low_altitude.flight_sorties"}
        else:
            subtype_fields = {"low_altitude.contract_amount", "low_altitude.project_acceptance_progress", "low_altitude.platform_dispatch_volume"}
        return bool((shared | subtype_fields) & missing)

    def _life_science_cxo_core_gating_missing(self, classification, readiness, context) -> bool:
        if classification.strategy_type != "life_science_cxo_services":
            return False
        missing = {
            item.field_name
            for item in readiness.field_readiness
            if item.status in {"missing", "partial"}
        }
        shared = {
            "life_science_cxo.backlog",
            "life_science_cxo.new_signed_orders",
            "life_science_cxo.customer_concentration",
            "life_science_cxo.overseas_revenue_share",
            "life_science_cxo.north_america_or_us_revenue_share",
        }
        subtype = getattr(classification, "sub_type", None)
        subtype_fields: set[str] = set()
        if subtype == "cdmo_manufacturing_services":
            subtype_fields = {"life_science_cxo.cdmo_capacity_utilization"}
        elif subtype == "clinical_cro_services":
            subtype_fields = {"life_science_cxo.clinical_project_count"}
        return bool((shared | subtype_fields) & missing)

    def _high_risk_count(self, readiness, context, scoring) -> int:
        names = {risk.risk_name for risk in context.required_risks if risk.severity == "high"}
        names.update(risk.risk_name for risk in scoring.required_risks if risk.severity == "high")
        names.update(readiness.critical_missing_fields)
        return len(names)

    def _advanced_manufacturing_medium_risk_count(self, classification, context) -> int:
        if classification.strategy_type != "advanced_manufacturing_growth":
            return 0
        target = {"机器人业务兑现验证不足", "大客户依赖验证不足", "估值预期消化风险"}
        return sum(1 for risk in context.required_risks if risk.severity == "medium" and risk.risk_name in target)

    def _structural_medium_risk_count(self, classification, context) -> int:
        targets = {
            "right_trend_growth": {"AI资本开支依赖风险", "订单与客户验证不足", "估值预期消化风险"},
            "semiconductor_cycle": {"半导体周期波动风险", "国产替代兑现验证风险", "半导体估值波动风险"},
            "stable_growth": {"订单节奏验证风险", "应收账款与现金流跟踪风险"},
        }.get(classification.strategy_type, set())
        return sum(1 for risk in context.required_risks if risk.severity == "medium" and risk.risk_name in targets)


def framework_vars(strategy_type: str) -> list[str]:
    if strategy_type in {"resource_swing", "resource_core"}:
        return ["商品价格", "产量", "成本曲线"]
    if strategy_type == "right_trend_growth":
        return ["订单", "客户资本开支", "收入增速"]
    if strategy_type == "semiconductor_cycle":
        return ["订单", "存货", "研发投入"]
    if strategy_type == "stable_growth":
        return ["订单", "现金流", "ROE"]
    if strategy_type == "advanced_manufacturing_growth":
        return ["订单", "客户验证", "毛利率", "应收账款"]
    if strategy_type == "satellite_communication_infrastructure":
        return ["卫星资源", "转发器 / 带宽容量", "容量利用率 / 出租率", "客户结构", "资产寿命 / 折旧"]
    if strategy_type == "low_altitude_economy_infrastructure":
        return ["sub_type", "low-altitude revenue share", "operating volume", "contract acceptance", "customer structure", "safety/regulatory events"]
    if strategy_type == "life_science_cxo_services":
        return ["sub_type", "CXO revenue share", "backlog/new orders", "customer concentration", "overseas/U.S. exposure", "CDMO utilization", "clinical project count", "compliance/FX/geopolitics"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble final FundamentalAnalysisResult.")
    parser.add_argument("--input", required=True, help="Path to raw JSON fixture")
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    normalized = FundamentalDataAdapter().from_file(args.input)
    classification = StockClassifier().classify(normalized)
    framework = FrameworkSelector().select(classification)
    readiness = DataReadinessPlanner().plan(normalized, classification, framework)
    context = AnalysisContextBuilder().build(normalized, classification, framework, readiness)
    scoring = FundamentalScoringEngine().score(normalized, classification, framework, readiness, context)
    result = FundamentalResultAssembler().assemble(normalized, classification, framework, readiness, context, scoring)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")

    print(f"stock_code: {result.stock_code}")
    print(f"stock_name: {result.stock_name}")
    print(f"strategy_type: {result.strategy_type}")
    print(f"status: {result.status}")
    print(f"confidence: {result.confidence}")
    print(f"fundamental_score: {result.fundamental_score}")
    print(f"top risk flags: {[risk.name for risk in result.risk_flags[:3]]}")
    print(f"must track indicators count: {len(result.must_track_indicators)}")
    print(f"invalidation conditions count: {len(result.invalidation_conditions)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
