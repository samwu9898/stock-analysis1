# -*- coding: utf-8 -*-
"""Build safe downstream analysis context from classification/framework/readiness."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from .analysis_context_schema import (
    AnalysisContext,
    AnalysisDimensionPermission,
    AnalyzerInstruction,
    ProhibitedClaim,
    RequiredRisk,
    ScoringConstraint,
)
from .classification_schema import FundamentalFramework, StockClassificationResult
from .data_adapter import FundamentalDataAdapter
from .data_readiness_planner import DataReadinessPlanner
from .framework_selector import FrameworkSelector
from .raw_schema import NormalizedFundamentalInput
from .readiness_schema import DataReadinessPlan, FieldReadiness
from .stock_classifier import StockClassifier


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RULES_CONFIG = PROJECT_ROOT / "config" / "analysis_context_rules.yaml"
STANDARD_DIMENSIONS = [
    "business_summary",
    "financial_quality",
    "valuation_view",
    "industry_cycle",
    "risk_flags",
    "catalysts",
    "thesis_check",
    "must_track_indicators",
]
SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2}
PERMISSION_RANK = {
    "allowed": 0,
    "allowed_with_low_confidence": 1,
    "restricted": 2,
    "blocked": 3,
}
CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


class AnalysisContextBuilder:
    def __init__(self, config_path: str | Path | None = None) -> None:
        self.config_path = Path(config_path) if config_path else DEFAULT_RULES_CONFIG
        self.rules = self._load_rules()

    def build(
        self,
        normalized: NormalizedFundamentalInput,
        classification: StockClassificationResult,
        framework: FundamentalFramework,
        readiness: DataReadinessPlan,
    ) -> AnalysisContext:
        quality, max_confidence = self._context_quality_and_cap(classification, readiness)
        missing_items = [
            item for item in readiness.field_readiness if item.status in {"missing", "partial"}
        ]

        required_risks: dict[str, RequiredRisk] = {}
        prohibited_claims: dict[str, ProhibitedClaim] = {}
        scoring_constraints: dict[str, ScoringConstraint] = {}
        analyzer_instructions: list[AnalyzerInstruction] = []
        dimension_impacts: dict[str, dict[str, Any]] = {}

        for item in missing_items:
            rule = self.rules.get("missing_field_rules", {}).get(item.field_name)
            if not rule:
                continue
            for dimension in rule.get("affected_dimensions", []):
                self._register_dimension_impact(dimension_impacts, dimension, item, readiness)
            self._merge_required_risk(required_risks, item, rule.get("required_risk"))
            self._merge_prohibited_claims(prohibited_claims, item, rule.get("prohibited_claims", []))
            self._merge_scoring_constraints(scoring_constraints, item, rule.get("scoring_constraints", {}))
            for raw_instruction in rule.get("analyzer_instructions", []) or []:
                analyzer_instructions.append(AnalyzerInstruction(**raw_instruction))

        self._apply_advanced_manufacturing_unverified_rules(
            normalized=normalized,
            classification=classification,
            required_risks=required_risks,
            prohibited_claims=prohibited_claims,
            scoring_constraints=scoring_constraints,
            analyzer_instructions=analyzer_instructions,
        )
        self._apply_growth_semiconductor_structural_rules(
            normalized=normalized,
            classification=classification,
            required_risks=required_risks,
            prohibited_claims=prohibited_claims,
            scoring_constraints=scoring_constraints,
            analyzer_instructions=analyzer_instructions,
        )

        self._apply_strategy_specific_rules(
            classification.strategy_type,
            {item.field_name for item in missing_items},
            analyzer_instructions,
        )

        allowed, restricted, blocked = self._build_dimension_permissions(
            dimension_impacts, readiness
        )
        warnings = self._build_warnings(classification, readiness)
        data_gaps = [
            f"{item.display_name}: {item.missing_reason or '字段缺失'}"
            for item in missing_items
        ]
        safe_summary = self._build_safe_summary(
            classification=classification,
            framework=framework,
            readiness=readiness,
            max_confidence=max_confidence,
        )

        return AnalysisContext(
            stock_code=normalized.stock_code,
            stock_name=normalized.stock_name,
            strategy_type=classification.strategy_type,
            classification_confidence=classification.confidence,
            readiness_score=readiness.readiness_score,
            readiness_level=readiness.readiness_level,
            framework_name=framework.display_name,
            generated_at=_now_iso(),
            overall_context_quality=quality,
            max_overall_confidence=max_confidence,
            allowed_dimensions=allowed,
            restricted_dimensions=restricted,
            blocked_dimensions=blocked,
            required_risks=list(required_risks.values()),
            prohibited_claims=list(prohibited_claims.values()),
            scoring_constraints=list(scoring_constraints.values()),
            analyzer_instructions=analyzer_instructions,
            data_gaps_summary=data_gaps,
            safe_summary_for_next_stage=safe_summary,
            context_warnings=warnings,
        )

    def _load_rules(self) -> dict[str, Any]:
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _context_quality_and_cap(
        self, classification: StockClassificationResult, readiness: DataReadinessPlan
    ) -> tuple[str, str]:
        general = self.rules.get("general", {})
        readiness_caps = general.get("readiness_level_caps", {})
        base = readiness_caps.get(readiness.readiness_level, readiness_caps["insufficient"])
        quality = base["overall_context_quality"]
        cap = base["max_overall_confidence"]

        class_cap = general.get("classification_confidence_caps", {}).get(
            classification.confidence, {"max_overall_confidence": "low"}
        )["max_overall_confidence"]
        cap = self._min_confidence(cap, class_cap)
        if classification.strategy_type == "unknown":
            unknown = general.get("unknown_strategy_cap", {})
            cap = self._min_confidence(cap, unknown.get("max_overall_confidence", "low"))
            quality = unknown.get("overall_context_quality", "insufficient")
        return quality, cap

    def _min_confidence(self, a: str, b: str) -> str:
        return a if CONFIDENCE_RANK[a] <= CONFIDENCE_RANK[b] else b

    def _register_dimension_impact(
        self,
        impacts: dict[str, dict[str, Any]],
        dimension: str,
        item: FieldReadiness,
        readiness: DataReadinessPlan,
    ) -> None:
        permission = "allowed_with_low_confidence"
        max_confidence = "medium"
        if item.importance == "high":
            permission = "restricted"
            max_confidence = "low"
        if item.importance == "critical":
            permission = "blocked" if readiness.readiness_level in {"weak", "insufficient"} else "restricted"
            max_confidence = "low"

        current = impacts.setdefault(
            dimension,
            {
                "permission": "allowed",
                "max_confidence": "high",
                "missing_fields": set(),
                "reasons": [],
            },
        )
        if PERMISSION_RANK[permission] > PERMISSION_RANK[current["permission"]]:
            current["permission"] = permission
        current["max_confidence"] = self._min_confidence(current["max_confidence"], max_confidence)
        current["missing_fields"].add(item.field_name)
        current["reasons"].append(f"{item.display_name}{item.status}，影响该维度。")

    def _merge_required_risk(
        self, risks: dict[str, RequiredRisk], item: FieldReadiness, raw: dict[str, Any] | None
    ) -> None:
        if not raw:
            return
        risk = RequiredRisk(
            risk_name=raw["risk_name"],
            severity=raw["severity"],
            reason=raw["reason"],
            evidence_source=item.field_name,
            must_include=True,
        )
        existing = risks.get(risk.risk_name)
        if existing is None or SEVERITY_RANK[risk.severity] > SEVERITY_RANK[existing.severity]:
            risks[risk.risk_name] = risk

    def _merge_prohibited_claims(
        self, claims: dict[str, ProhibitedClaim], item: FieldReadiness, raw_claims: list[dict[str, Any]]
    ) -> None:
        for raw in raw_claims or []:
            existing = claims.get(raw["claim_type"])
            if existing is None:
                claims[raw["claim_type"]] = ProhibitedClaim(
                    claim_type=raw["claim_type"],
                    prohibited_reason=raw["prohibited_reason"],
                    related_missing_fields=[item.field_name],
                    example_forbidden_phrases=raw.get("example_forbidden_phrases", []),
                )
                continue
            fields = sorted(set(existing.related_missing_fields + [item.field_name]))
            phrases = sorted(set(existing.example_forbidden_phrases + raw.get("example_forbidden_phrases", [])))
            claims[raw["claim_type"]] = existing.model_copy(
                update={
                    "related_missing_fields": fields,
                    "example_forbidden_phrases": phrases,
                }
            )

    def _merge_scoring_constraints(
        self,
        constraints: dict[str, ScoringConstraint],
        item: FieldReadiness,
        raw_constraints: dict[str, dict[str, Any]],
    ) -> None:
        for dimension, raw in (raw_constraints or {}).items():
            max_score = int(raw["max_score"])
            reason = f"{item.display_name}{item.status}，限制 {dimension} 分数上限。"
            existing = constraints.get(dimension)
            if existing is None:
                constraints[dimension] = ScoringConstraint(
                    scoring_dimension=dimension,
                    max_score=max_score,
                    reason=reason,
                    related_missing_fields=[item.field_name],
                )
                continue
            constraints[dimension] = existing.model_copy(
                update={
                    "max_score": min(existing.max_score, max_score),
                    "reason": existing.reason + " " + reason,
                    "related_missing_fields": sorted(
                        set(existing.related_missing_fields + [item.field_name])
                    ),
                }
            )

    def _apply_strategy_specific_rules(
        self,
        strategy_type: str,
        missing_fields: set[str],
        analyzer_instructions: list[AnalyzerInstruction],
    ) -> None:
        strategy_rules = self.rules.get("strategy_specific_rules", {}).get(strategy_type, {})
        must_include = set(strategy_rules.get("must_include_if_missing", []))
        if must_include & missing_fields:
            for instruction in strategy_rules.get("prohibited_if_missing_core", []) or []:
                analyzer_instructions.append(
                    AnalyzerInstruction(
                        instruction_type="must_not_do",
                        instruction=instruction,
                        reason="策略框架核心字段缺失。",
                    )
                )

    def _apply_advanced_manufacturing_unverified_rules(
        self,
        normalized: NormalizedFundamentalInput,
        classification: StockClassificationResult,
        required_risks: dict[str, RequiredRisk],
        prohibited_claims: dict[str, ProhibitedClaim],
        scoring_constraints: dict[str, ScoringConstraint],
        analyzer_instructions: list[AnalyzerInstruction],
    ) -> None:
        if classification.strategy_type != "advanced_manufacturing_growth":
            return
        text = self._collect_context_text(normalized)
        rules = self.rules.get("unverified_rules", {})

        robot_terms = ("机器人", "机器人执行器", "人形机器人", "执行器", "关节模组", "线性执行器")
        customer_terms = ("特斯拉", "大客户", "核心客户", "供应链", "新能源车客户")
        unverified_terms = ("布局", "预期", "待验证", "相关", "探索", "储备", "mock")
        new_business_terms = ("机器人", "新能源车", "高端制造", "新业务")

        has_robot = any(term in text for term in robot_terms)
        robot_verified = self._has_verified_robot_business(normalized)
        robot_unverified = has_robot and (not robot_verified or any(term in text for term in unverified_terms))
        if robot_unverified:
            self._apply_unverified_rule(
                "robot_business_validation",
                "robot_business_validation",
                rules,
                required_risks,
                prohibited_claims,
                scoring_constraints,
                analyzer_instructions,
            )

        has_customer_logic = any(term in text for term in customer_terms)
        customer_verified = (
            any(term in text for term in ("客户收入占比", "客户订单金额", "订单金额", "订单数据"))
            and not any(term in text for term in ("不提供", "缺少", "待验证", "需继续验证", "需要验证", "未充分验证"))
        )
        if has_customer_logic and not customer_verified:
            self._apply_unverified_rule(
                "customer_concentration_validation",
                "customer_concentration_validation",
                rules,
                required_risks,
                prohibited_claims,
                scoring_constraints,
                analyzer_instructions,
            )

        pe_ttm = normalized.valuation_metrics.pe_ttm if normalized.valuation_metrics else None
        valuation_missing_with_expectation = normalized.valuation_metrics is None and any(
            term in text for term in new_business_terms
        )
        if (pe_ttm is not None and pe_ttm > 40) or valuation_missing_with_expectation:
            self._apply_unverified_rule(
                "valuation_expectation_risk",
                "valuation_expectation_risk",
                rules,
                required_risks,
                prohibited_claims,
                scoring_constraints,
                analyzer_instructions,
            )

    def _apply_growth_semiconductor_structural_rules(
        self,
        normalized: NormalizedFundamentalInput,
        classification: StockClassificationResult,
        required_risks: dict[str, RequiredRisk],
        prohibited_claims: dict[str, ProhibitedClaim],
        scoring_constraints: dict[str, ScoringConstraint],
        analyzer_instructions: list[AnalyzerInstruction],
    ) -> None:
        strategy_type = classification.strategy_type
        if strategy_type not in {"right_trend_growth", "semiconductor_cycle", "stable_growth"}:
            return

        text = self._collect_context_text(normalized)
        rules = self.rules.get("unverified_rules", {})
        pe_ttm = normalized.valuation_metrics.pe_ttm if normalized.valuation_metrics else None

        if strategy_type == "right_trend_growth":
            ai_terms = (
                "AI",
                "算力",
                "光模块",
                "CPO",
                "PCB",
                "AI服务器",
                "服务器",
                "数据中心",
                "云厂商",
                "液冷",
                "高速互联",
            )
            customer_terms = ("大客户", "海外客户", "云厂商", "订单", "供应链", "客户", "资本开支")
            growth_terms = ai_terms + ("高景气", "成长", "产能", "需求")

            if any(term in text for term in ai_terms):
                self._apply_unverified_rule(
                    "ai_capex_dependency_risk",
                    "ai_capex_dependency_risk",
                    rules,
                    required_risks,
                    prohibited_claims,
                    scoring_constraints,
                    analyzer_instructions,
                )
            if any(term in text for term in customer_terms) and not self._has_customer_order_validation(text):
                self._apply_unverified_rule(
                    "growth_order_customer_validation_risk",
                    "growth_order_customer_validation_risk",
                    rules,
                    required_risks,
                    prohibited_claims,
                    scoring_constraints,
                    analyzer_instructions,
                )
            if (pe_ttm is not None and pe_ttm > 40) or (
                normalized.valuation_metrics is None and any(term in text for term in growth_terms)
            ):
                self._apply_unverified_rule(
                    "growth_valuation_expectation_risk",
                    "growth_valuation_expectation_risk",
                    rules,
                    required_risks,
                    prohibited_claims,
                    scoring_constraints,
                    analyzer_instructions,
                )
            return

        if strategy_type == "semiconductor_cycle":
            semiconductor_terms = (
                "国产替代",
                "半导体设备",
                "半导体",
                "芯片",
                "GPU",
                "CPU",
                "存储",
                "集成电路",
                "晶圆",
                "刻蚀",
                "薄膜",
                "封测",
                "光刻",
                "设备",
            )
            self._apply_unverified_rule(
                "semiconductor_cycle_volatility_risk",
                "semiconductor_cycle_volatility_risk",
                rules,
                required_risks,
                prohibited_claims,
                scoring_constraints,
                analyzer_instructions,
            )
            if any(term in text for term in semiconductor_terms):
                self._apply_unverified_rule(
                    "domestic_substitution_validation_risk",
                    "domestic_substitution_validation_risk",
                    rules,
                    required_risks,
                    prohibited_claims,
                    scoring_constraints,
                    analyzer_instructions,
                )
            if (pe_ttm is not None and pe_ttm > 50) or (
                normalized.valuation_metrics is None and any(term in text for term in semiconductor_terms)
            ):
                self._apply_unverified_rule(
                    "semiconductor_valuation_volatility_risk",
                    "semiconductor_valuation_volatility_risk",
                    rules,
                    required_risks,
                    prohibited_claims,
                    scoring_constraints,
                    analyzer_instructions,
                )
            return

        stable_order_terms = (
            "海外订单",
            "电网投资",
            "特高压",
            "政策投资",
            "新签订单",
            "项目交付",
            "订单",
            "交付",
        )
        stable_cash_terms = ("应收账款", "回款", "现金流", "经营现金流")
        if any(term in text for term in stable_order_terms):
            self._apply_unverified_rule(
                "stable_order_timing_risk",
                "stable_order_timing_risk",
                rules,
                required_risks,
                prohibited_claims,
                scoring_constraints,
                analyzer_instructions,
            )
        if any(term in text for term in stable_cash_terms) or self._stable_cashflow_data_risk(normalized):
            self._apply_unverified_rule(
                "stable_receivable_cashflow_tracking_risk",
                "stable_receivable_cashflow_tracking_risk",
                rules,
                required_risks,
                prohibited_claims,
                scoring_constraints,
                analyzer_instructions,
            )

    def _apply_unverified_rule(
        self,
        evidence_source: str,
        rule_name: str,
        rules: dict[str, Any],
        required_risks: dict[str, RequiredRisk],
        prohibited_claims: dict[str, ProhibitedClaim],
        scoring_constraints: dict[str, ScoringConstraint],
        analyzer_instructions: list[AnalyzerInstruction],
    ) -> None:
        rule = rules.get(rule_name)
        if not rule:
            return
        self._merge_required_risk_for_source(required_risks, evidence_source, rule.get("required_risk"))
        self._merge_prohibited_claims_for_source(
            prohibited_claims, evidence_source, rule.get("prohibited_claims", [])
        )
        self._merge_scoring_constraints_for_source(
            scoring_constraints, evidence_source, rule.get("scoring_constraints", {})
        )
        for raw_instruction in rule.get("analyzer_instructions", []) or []:
            analyzer_instructions.append(AnalyzerInstruction(**raw_instruction))

    def _merge_required_risk_for_source(
        self, risks: dict[str, RequiredRisk], evidence_source: str, raw: dict[str, Any] | None
    ) -> None:
        if not raw:
            return
        risk = RequiredRisk(
            risk_name=raw["risk_name"],
            severity=raw["severity"],
            reason=raw["reason"],
            evidence_source=evidence_source,
            must_include=True,
        )
        existing = risks.get(risk.risk_name)
        if existing is None or SEVERITY_RANK[risk.severity] > SEVERITY_RANK[existing.severity]:
            risks[risk.risk_name] = risk

    def _merge_prohibited_claims_for_source(
        self, claims: dict[str, ProhibitedClaim], evidence_source: str, raw_claims: list[dict[str, Any]]
    ) -> None:
        for raw in raw_claims or []:
            existing = claims.get(raw["claim_type"])
            if existing is None:
                claims[raw["claim_type"]] = ProhibitedClaim(
                    claim_type=raw["claim_type"],
                    prohibited_reason=raw["prohibited_reason"],
                    related_missing_fields=[evidence_source],
                    example_forbidden_phrases=raw.get("example_forbidden_phrases", []),
                )
                continue
            claims[raw["claim_type"]] = existing.model_copy(
                update={
                    "related_missing_fields": sorted(set(existing.related_missing_fields + [evidence_source])),
                    "example_forbidden_phrases": sorted(
                        set(existing.example_forbidden_phrases + raw.get("example_forbidden_phrases", []))
                    ),
                }
            )

    def _merge_scoring_constraints_for_source(
        self,
        constraints: dict[str, ScoringConstraint],
        evidence_source: str,
        raw_constraints: dict[str, dict[str, Any]],
    ) -> None:
        for dimension, raw in (raw_constraints or {}).items():
            max_score = int(raw["max_score"])
            reason = f"{evidence_source} 未充分验证，限制 {dimension} 分数上限。"
            existing = constraints.get(dimension)
            if existing is None:
                constraints[dimension] = ScoringConstraint(
                    scoring_dimension=dimension,
                    max_score=max_score,
                    reason=reason,
                    related_missing_fields=[evidence_source],
                )
                continue
            constraints[dimension] = existing.model_copy(
                update={
                    "max_score": min(existing.max_score, max_score),
                    "reason": existing.reason + " " + reason,
                    "related_missing_fields": sorted(set(existing.related_missing_fields + [evidence_source])),
                }
            )

    def _collect_context_text(self, normalized: NormalizedFundamentalInput) -> str:
        parts = [
            normalized.stock_name or "",
            normalized.basic_info.industry or "",
            normalized.basic_info.main_business or "",
            str(normalized.raw_blocks),
        ]
        if normalized.business_composition:
            parts.extend(str(segment) for segment in normalized.business_composition.segments)
        parts.extend(f"{item.title} {item.summary or ''}" for item in normalized.latest_news)
        return " ".join(parts)

    def _has_customer_order_validation(self, text: str) -> bool:
        validation_terms = (
            "客户收入占比",
            "客户收入比例",
            "客户订单金额",
            "订单金额",
            "订单数据",
            "在手订单",
            "订单持续性数据",
        )
        negative_terms = ("不提供", "缺少", "待验证", "需继续验证", "需要验证", "未充分验证", "无法验证")
        return any(term in text for term in validation_terms) and not any(term in text for term in negative_terms)

    def _stable_cashflow_data_risk(self, normalized: NormalizedFundamentalInput) -> bool:
        metric = normalized.financial_metrics[0] if normalized.financial_metrics else None
        if metric is None:
            return False
        return metric.accounts_receivable is None or metric.operating_cashflow is None or metric.operating_cashflow < 0

    def _has_verified_robot_business(self, normalized: NormalizedFundamentalInput) -> bool:
        if not normalized.business_composition:
            return False
        for segment in normalized.business_composition.segments:
            if not isinstance(segment, dict):
                continue
            name = str(segment.get("segment_name", ""))
            note = str(segment.get("note", ""))
            if "机器人" not in name and "执行器" not in name:
                continue
            has_numeric_validation = any(
                segment.get(key) not in (None, "", "--", "N/A")
                for key in ("revenue", "order", "orders", "revenue_ratio")
            )
            if has_numeric_validation and not any(term in note for term in ("布局", "预期", "待验证", "探索", "储备", "mock")):
                return True
        return False

    def _build_dimension_permissions(
        self,
        impacts: dict[str, dict[str, Any]],
        readiness: DataReadinessPlan,
    ) -> tuple[list[AnalysisDimensionPermission], list[AnalysisDimensionPermission], list[AnalysisDimensionPermission]]:
        allowed: list[AnalysisDimensionPermission] = []
        restricted: list[AnalysisDimensionPermission] = []
        blocked: list[AnalysisDimensionPermission] = []
        all_dimensions = sorted(set(STANDARD_DIMENSIONS) | set(impacts.keys()))
        for dimension in all_dimensions:
            impact = impacts.get(dimension)
            if impact is None:
                permission = AnalysisDimensionPermission(
                    dimension_name=dimension,
                    permission="allowed",
                    reason="未被当前数据缺口直接限制。",
                    related_missing_fields=[],
                    max_confidence="high" if readiness.readiness_level == "sufficient" else "medium",
                )
            else:
                permission = AnalysisDimensionPermission(
                    dimension_name=dimension,
                    permission=impact["permission"],
                    reason=" ".join(impact["reasons"]),
                    related_missing_fields=sorted(impact["missing_fields"]),
                    max_confidence=impact["max_confidence"],
                )
            if permission.permission == "blocked":
                blocked.append(permission)
            elif permission.permission == "restricted":
                restricted.append(permission)
            else:
                allowed.append(permission)
        return allowed, restricted, blocked

    def _build_warnings(
        self, classification: StockClassificationResult, readiness: DataReadinessPlan
    ) -> list[str]:
        warnings = []
        if readiness.readiness_level in {"weak", "insufficient"}:
            warnings.append(f"数据准备度为 {readiness.readiness_level}，后续分析必须降低确定性。")
        if classification.strategy_type == "unknown":
            warnings.append("股票类型未知，不能强行套用行业框架。")
        if readiness.critical_missing_fields:
            warnings.append("存在 critical 数据缺口，后续分析必须显式披露数据限制。")
        return warnings

    def _build_safe_summary(
        self,
        classification: StockClassificationResult,
        framework: FundamentalFramework,
        readiness: DataReadinessPlan,
        max_confidence: str,
    ) -> str:
        missing = "、".join(readiness.critical_missing_fields + readiness.high_priority_missing_fields)
        if not missing:
            missing = "无核心缺口"
        return (
            f"该标的被分类为{framework.display_name}，分类置信度 {classification.confidence}，"
            f"数据准备度 {readiness.readiness_level}。当前关键数据缺口：{missing}。"
            f"后续分析整体最高置信度为 {max_confidence}，必须遵守维度限制、禁用结论和评分上限。"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build safe analysis context for fundamental_skill.")
    parser.add_argument("--input", required=True, help="Path to raw JSON fixture")
    parser.add_argument("--output", help="Optional output JSON path")
    args = parser.parse_args()

    normalized = FundamentalDataAdapter().from_file(args.input)
    classification = StockClassifier().classify(normalized)
    framework = FrameworkSelector().select(classification)
    readiness = DataReadinessPlanner().plan(normalized, classification, framework)
    context = AnalysisContextBuilder().build(normalized, classification, framework, readiness)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(context.model_dump_json(indent=2), encoding="utf-8")

    print(f"stock_code: {context.stock_code}")
    print(f"stock_name: {context.stock_name}")
    print(f"strategy_type: {context.strategy_type}")
    print(f"readiness_level: {context.readiness_level}")
    print(f"overall_context_quality: {context.overall_context_quality}")
    print(f"max_overall_confidence: {context.max_overall_confidence}")
    print(f"required_risks: {[risk.risk_name for risk in context.required_risks]}")
    print(f"prohibited_claims count: {len(context.prohibited_claims)}")
    print(
        "scoring_constraints: "
        + str({item.scoring_dimension: item.max_score for item in context.scoring_constraints})
    )
    print(f"context_warnings: {context.context_warnings}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
