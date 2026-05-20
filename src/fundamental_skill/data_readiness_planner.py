# -*- coding: utf-8 -*-
"""Framework-aware data readiness planner."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from .classification_schema import FundamentalFramework, StockClassificationResult
from .data_adapter import FundamentalDataAdapter
from .external_commodity_price_connector import DEFAULT_EXPOSURE_MAP
from .framework_selector import FrameworkSelector
from .raw_schema import NormalizedFundamentalInput
from .readiness_schema import DataReadinessPlan, FieldReadiness, FieldRequirement
from .stock_classifier import StockClassifier


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REQUIREMENTS_CONFIG = PROJECT_ROOT / "config" / "data_requirements.yaml"

PENALTY = {"critical": 18, "high": 10, "medium": 5, "low": 2}
PARTIAL_PENALTY = {"critical": 9, "high": 5, "medium": 3, "low": 1}
IMPACT_MISSING = {"critical": "severe", "high": "moderate", "medium": "moderate", "low": "minor"}
IMPACT_PARTIAL = {"critical": "moderate", "high": "minor", "medium": "minor", "low": "minor"}
INVALID_VALUES = {None, "", "--", "N/A", "n/a", "NA", "na"}


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def _preview(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text[:120]


class DataReadinessPlanner:
    def __init__(self, config_path: str | Path | None = None) -> None:
        self.config_path = Path(config_path) if config_path else DEFAULT_REQUIREMENTS_CONFIG
        self.requirements = self._load_requirements()

    def plan(
        self,
        normalized: NormalizedFundamentalInput,
        classification: StockClassificationResult,
        framework: FundamentalFramework,
    ) -> DataReadinessPlan:
        requirements = [
            FieldRequirement(**item)
            for item in self.requirements.get(classification.strategy_type, self.requirements["unknown"]).get(
                "required_fields", []
            )
        ]

        readiness_items = [self._check_requirement(normalized, req) for req in requirements]
        critical_missing = []
        high_missing = []
        for item in readiness_items:
            if item.status not in {"missing", "partial"}:
                continue
            names = self._reported_missing_names(item, normalized)
            if item.importance == "critical":
                critical_missing.extend(names)
            if item.importance == "high":
                high_missing.extend(names)
        available = [item.field_name for item in readiness_items if item.status == "available"]
        partial = [item.field_name for item in readiness_items if item.status == "partial"]

        score = 100
        penalty_reasons: list[str] = []
        for item in readiness_items:
            if item.status == "missing":
                penalty = PENALTY[item.importance]
            elif item.status == "partial":
                penalty = PARTIAL_PENALTY[item.importance]
            else:
                penalty = 0
            if penalty:
                score -= penalty
                penalty_reasons.append(f"{item.display_name} {item.status}，扣减数据准备度 {penalty} 分。")
        if classification.strategy_type == "unknown":
            score -= 20
            penalty_reasons.append("strategy_type=unknown，额外降低数据准备度。")
        if classification.confidence == "low":
            score -= 10
            penalty_reasons.append("分类置信度为 low，额外降低数据准备度。")
        elif classification.confidence == "medium":
            score -= 5
            penalty_reasons.append("分类置信度为 medium，额外降低数据准备度。")
        if "unknown_raw_structure" in normalized.missing_fields:
            score -= 10
            penalty_reasons.append("raw data unknown structure，额外降低数据准备度。")
        if not normalized.financial_metrics:
            score -= 20
            penalty_reasons.append("financial_metrics 为空，额外降低数据准备度。")
        business_critical_missing = any(
            item.field_name == "business_composition.segments"
            and item.importance == "critical"
            and item.status in {"missing", "partial"}
            for item in readiness_items
        )
        if business_critical_missing:
            score -= 10
            penalty_reasons.append("critical 主营构成缺失，额外降低数据准备度。")
        if classification.strategy_type == "satellite_communication_infrastructure":
            foundation_available = (
                bool(normalized.financial_metrics)
                and normalized.business_composition is not None
                and bool(normalized.business_composition.segments)
                and bool(normalized.basic_info.industry or normalized.basic_info.main_business)
            )
            if foundation_available and score < 60:
                score = 60
                penalty_reasons.append(
                    "卫星通信基础设施 v1：basic_info、financials、business_composition 可用时不因行业专属运营指标缺失直接降为 insufficient。"
                )
        score = max(0, min(100, score))

        level = self._level_from_score(
            score=score,
            critical_missing_count=len(critical_missing),
            high_missing_count=len(high_missing),
            strategy_type=classification.strategy_type,
            classification_confidence=classification.confidence,
            financial_metrics_empty=not normalized.financial_metrics,
            readiness_items=readiness_items,
        )
        blockers = self._build_blockers(readiness_items)
        if not normalized.financial_metrics:
            blockers.insert(0, "财务数据不足：无法完整判断财务质量、利润趋势和风险暴露。")
            blockers = list(dict.fromkeys(blockers))
        recommended = [item.suggested_fix for item in readiness_items if item.status in {"missing", "partial"}]
        notes_for_analyzer = self._build_analyzer_notes(readiness_items, classification.strategy_type)
        notes_for_scorer = self._build_scorer_notes(readiness_items)

        return DataReadinessPlan(
            stock_code=normalized.stock_code,
            stock_name=normalized.stock_name,
            strategy_type=classification.strategy_type,
            classification_confidence=classification.confidence,
            framework_name=framework.display_name,
            generated_at=_now_iso(),
            readiness_score=score,
            readiness_level=level,
            field_readiness=readiness_items,
            critical_missing_fields=critical_missing,
            high_priority_missing_fields=high_missing,
            available_fields=available,
            partial_fields=partial,
            analysis_blockers=blockers,
            confidence_penalty_reasons=penalty_reasons,
            recommended_data_to_collect=list(dict.fromkeys(recommended)),
            notes_for_analyzer=notes_for_analyzer,
            notes_for_scorer=notes_for_scorer,
        )

    def _load_requirements(self) -> dict[str, Any]:
        with open(self.config_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        if "unknown" not in raw:
            raise ValueError("data requirements config must include unknown")
        return raw

    def _check_requirement(
        self, normalized: NormalizedFundamentalInput, requirement: FieldRequirement
    ) -> FieldReadiness:
        status, value, evidence_path, missing_reason = self._resolve_field(normalized, requirement.field_name)
        impact = "none" if status == "available" else (
            IMPACT_MISSING[requirement.importance] if status == "missing" else IMPACT_PARTIAL[requirement.importance]
        )
        return FieldReadiness(
            field_name=requirement.field_name,
            display_name=requirement.display_name,
            status=status,
            importance=requirement.importance,
            found_value_preview=_preview(value),
            missing_reason=missing_reason,
            impact_on_confidence=impact,
            suggested_fix=self._suggest_fix(requirement),
            evidence_path=evidence_path,
        )

    def _resolve_field(
        self, normalized: NormalizedFundamentalInput, field_name: str
    ) -> tuple[str, Any, str | None, str | None]:
        if field_name == "financial_metrics":
            return (
                "available" if normalized.financial_metrics else "missing",
                f"{len(normalized.financial_metrics)} periods" if normalized.financial_metrics else None,
                "financial_metrics",
                None if normalized.financial_metrics else "未找到财务指标列表",
            )
        if field_name.startswith("financial_metrics."):
            attr = field_name.split(".", 1)[1]
            if not normalized.financial_metrics:
                return "missing", None, "financial_metrics", "未找到财务指标列表"
            for idx, metric in enumerate(normalized.financial_metrics):
                value = getattr(metric, attr, None)
                if self._is_valid_value(value):
                    period = metric.period or f"index={idx}"
                    preview = f"{value} ({period})"
                    if idx == 0:
                        return "available", preview, f"financial_metrics[{idx}].{attr}", None
                    return "partial", preview, f"financial_metrics[{idx}].{attr}", f"最近一期缺少 {attr}，历史期存在"
            return "missing", None, f"financial_metrics[*].{attr}", f"任一期财务指标都缺少 {attr}"
        if field_name == "orders_or_contract_liabilities":
            for idx, metric in enumerate(normalized.financial_metrics):
                value = getattr(metric, "contract_liabilities", None)
                if self._is_valid_value(value):
                    period = metric.period or f"index={idx}"
                    return (
                        "partial",
                        f"{value} ({period})",
                        f"financial_metrics[{idx}].contract_liabilities",
                        "合同负债仅作为订单可见度 proxy，不等同于真实订单或 backlog",
                    )
            return (
                "missing",
                None,
                "financial_metrics[*].contract_liabilities",
                "缺少真实订单数据，也缺少合同负债 proxy",
            )
        if field_name.startswith("valuation_metrics."):
            attr = field_name.split(".", 1)[1]
            if normalized.valuation_metrics is None:
                return "missing", None, "valuation_metrics", "未找到估值指标"
            value = getattr(normalized.valuation_metrics, attr, None)
            if self._is_valid_value(value):
                return "available", value, f"valuation_metrics.{attr}", None
            return "missing", None, f"valuation_metrics.{attr}", f"估值指标中缺少 {attr}"
        if field_name == "business_composition.segments":
            if normalized.business_composition is None:
                return "missing", None, "business_composition", "未找到主营构成"
            segments = normalized.business_composition.segments
            if not segments:
                return "missing", None, "business_composition.segments", "主营构成 segments 为空"
            has_name = any(self._is_valid_value(seg.get("segment_name")) for seg in segments if isinstance(seg, dict))
            has_any_value = any(
                any(self._is_valid_value(seg.get(key)) for key in ("revenue", "revenue_ratio", "gross_margin"))
                for seg in segments
                if isinstance(seg, dict)
            )
            if has_name:
                return "available", f"{len(segments)} segments", "business_composition.segments", None
            if has_any_value:
                return "partial", f"{len(segments)} segments without segment_name", "business_composition.segments", "主营构成缺少有效业务名称"
            return "partial", None, "business_composition.segments", "主营构成缺少有效业务名称和收入字段"
        if field_name == "latest_news":
            if not normalized.latest_news:
                return "missing", None, "latest_news", "未找到新闻或公告"
            if any(item.title and item.title.strip() for item in normalized.latest_news):
                return "available", f"{len(normalized.latest_news)} items", "latest_news", None
            return "partial", None, "latest_news", "新闻对象存在但缺少标题"
        if field_name.startswith("basic_info."):
            attr = field_name.split(".", 1)[1]
            value = getattr(normalized.basic_info, attr, None)
            if value:
                return "available", value, f"basic_info.{attr}", None
            return "missing", None, f"basic_info.{attr}", f"基础信息缺少 {attr}"
        if field_name == "external.commodity_prices":
            return self._resolve_commodity_prices(normalized)
        if field_name.startswith("external."):
            return "missing", None, field_name, "当前标准化输入尚未包含外部变量数据"
        return "missing", None, field_name, "暂不支持该字段路径"

    def _resolve_commodity_prices(
        self, normalized: NormalizedFundamentalInput
    ) -> tuple[str, Any, str | None, str | None]:
        required = self._required_commodities(normalized.stock_code)
        rows = [
            row for row in normalized.raw_blocks.get("commodity_prices", [])
            if isinstance(row, dict)
        ]
        if not rows:
            return "missing", None, "raw_blocks.commodity_prices", "commodity_prices block is empty"

        details = self._commodity_missing_details(required, rows)
        eligible = set(details["eligible"])
        if not required:
            if eligible:
                return "available", f"{len(eligible)} commodities", "raw_blocks.commodity_prices", None
            return "partial", f"{len(rows)} rows", "raw_blocks.commodity_prices", "no eligible domestic primary commodity price"

        missing_fields = details["missing_fields"]
        if not missing_fields:
            return "available", ", ".join(sorted(eligible)), "raw_blocks.commodity_prices", None
        reason = "commodity coverage gaps: " + ", ".join(missing_fields)
        return "partial", ", ".join(sorted(eligible)) if eligible else f"{len(rows)} rows", "raw_blocks.commodity_prices", reason

    def _reported_missing_names(self, item: FieldReadiness, normalized: NormalizedFundamentalInput) -> list[str]:
        if item.field_name != "external.commodity_prices":
            return [item.field_name]
        required = self._required_commodities(normalized.stock_code)
        rows = [
            row for row in normalized.raw_blocks.get("commodity_prices", [])
            if isinstance(row, dict)
        ]
        if not rows:
            return [item.field_name]
        names = self._commodity_missing_details(required, rows)["missing_fields"]
        return list(dict.fromkeys(names or [item.field_name]))

    def _commodity_missing_details(self, required: list[str], rows: list[dict[str, Any]]) -> dict[str, list[str]]:
        by_name: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            name = row.get("commodity_name")
            if name:
                by_name.setdefault(str(name), []).append(row)

        eligible = []
        missing_fields = []
        for name in required:
            items = by_name.get(name, [])
            fresh_items = [
                row for row in items
                if row.get("readiness_eligible") is True
                and row.get("market") != "foreign_reference"
                and row.get("price") not in INVALID_VALUES
                and row.get("date") not in INVALID_VALUES
                and row.get("is_stale") is not True
            ]
            if fresh_items:
                eligible.append(name)
                continue
            if not items:
                missing_fields.append(f"external.commodity_prices.{name}")
                continue
            if all(row.get("market") == "foreign_reference" for row in items):
                missing_fields.append(f"external.commodity_prices.{name}.domestic_primary")
                continue
            if any(row.get("is_stale") is True or row.get("readiness_eligible") is False for row in items):
                missing_fields.append(f"external.commodity_prices.{name}.freshness")
                continue
            missing_fields.append(f"external.commodity_prices.{name}")
        return {"eligible": eligible, "missing_fields": missing_fields}

    def _required_commodities(self, stock_code: str) -> list[str]:
        if not DEFAULT_EXPOSURE_MAP.exists():
            return []
        with open(DEFAULT_EXPOSURE_MAP, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        digits = "".join(ch for ch in str(stock_code) if ch.isdigit())
        digits = digits.zfill(6)[-6:] if digits else str(stock_code)
        item = raw.get(digits) if isinstance(raw, dict) else None
        if not isinstance(item, dict):
            return []
        return [str(name) for name in item.get("commodities", [])]

    def _is_valid_value(self, value: Any) -> bool:
        if value in INVALID_VALUES:
            return False
        if isinstance(value, str) and value.strip() in INVALID_VALUES:
            return False
        return True

    def _suggest_fix(self, requirement: FieldRequirement) -> str:
        if requirement.field_name == "external.commodity_prices":
            return "补充银、锡、铜、金、铝、稀土等对应商品价格数据源"
        if requirement.category == "financial":
            return f"补充或修正财务字段：{requirement.display_name}"
        if requirement.category == "valuation":
            return f"补充估值字段：{requirement.display_name}"
        if requirement.category == "business_composition":
            return "补充主营业务构成数据"
        if requirement.category == "basic_info":
            return f"补充基础信息：{requirement.display_name}"
        if requirement.category == "news":
            return "补充最新公告或新闻数据"
        if requirement.category == "industry":
            return f"补充卫星通信行业专属字段：{requirement.display_name}"
        return f"补充字段：{requirement.display_name}"

    def _level_from_score(
        self,
        score: int,
        critical_missing_count: int,
        high_missing_count: int,
        strategy_type: str,
        classification_confidence: str,
        financial_metrics_empty: bool,
        readiness_items: list[FieldReadiness],
    ) -> str:
        if score >= 80 and critical_missing_count == 0:
            level = "sufficient"
        elif score >= 60:
            level = "usable_with_warnings"
        elif score >= 40:
            level = "weak"
        else:
            level = "insufficient"
        caps = []
        if critical_missing_count >= 1:
            caps.append("usable_with_warnings")
        if critical_missing_count >= 2:
            caps.append("weak")
        if critical_missing_count >= 3:
            caps.append("insufficient")
        if high_missing_count >= 2:
            caps.append("usable_with_warnings")
        if strategy_type == "unknown":
            caps.append("weak")
        if classification_confidence == "low":
            caps.append("weak")
        if financial_metrics_empty:
            caps.append("weak")
        missing = {item.field_name for item in readiness_items if item.status in {"missing", "partial"}}
        business_critical_missing = any(
            item.field_name == "business_composition.segments"
            and item.importance == "critical"
            and item.status in {"missing", "partial"}
            for item in readiness_items
        )
        has_critical_financial_missing = any(
            item.field_name.startswith("financial_metrics.")
            and item.importance == "critical"
            and item.status in {"missing", "partial"}
            for item in readiness_items
        )
        if business_critical_missing:
            caps.append("usable_with_warnings")
            if has_critical_financial_missing:
                caps.append("weak")
        if strategy_type == "right_trend_growth":
            if "financial_metrics.gross_margin" in missing:
                caps.append("usable_with_warnings")
            if "financial_metrics.revenue_yoy" in missing or "financial_metrics.net_profit_yoy" in missing:
                caps.append("weak")
        if strategy_type == "semiconductor_cycle":
            if "financial_metrics.inventory" in missing:
                caps.append("usable_with_warnings")
            if "financial_metrics.inventory" in missing and "financial_metrics.gross_margin" in missing:
                caps.append("weak")
        if strategy_type == "resource_swing":
            core_pair = {"financial_metrics.deducted_net_profit", "financial_metrics.operating_cashflow"}
            if core_pair & missing:
                caps.append("usable_with_warnings")
            if core_pair <= missing:
                caps.append("weak")
            if "business_composition.segments" in missing and core_pair <= missing:
                caps.append("insufficient")
        if strategy_type == "stable_growth":
            core_pair = {"financial_metrics.operating_cashflow", "financial_metrics.roe"}
            if core_pair & missing:
                caps.append("usable_with_warnings")
            if core_pair <= missing:
                caps.append("weak")
        if strategy_type == "satellite_communication_infrastructure":
            foundation = {
                "basic_info.industry",
                "basic_info.main_business",
                "business_composition.segments",
            }
            confidence_gating = {
                "satellite.capacity_utilization_or_lease_rate",
                "satellite.customer_structure_or_concentration",
                "satellite.design_or_remaining_life",
                "financial_metrics.depreciation_amortization",
            }
            if confidence_gating & missing:
                caps.append("usable_with_warnings")
            if confidence_gating <= missing and not (foundation & missing) and not financial_metrics_empty:
                caps.append("usable_with_warnings")
            if foundation & missing or financial_metrics_empty:
                caps.append("weak")
        for cap in caps:
            level = self._cap_level(level, cap)
        return level

    def _cap_level(self, level: str, cap: str) -> str:
        order = ["insufficient", "weak", "usable_with_warnings", "sufficient"]
        return order[min(order.index(level), order.index(cap))]

    def _build_blockers(self, items: list[FieldReadiness]) -> list[str]:
        blockers = []
        for item in items:
            if item.importance != "critical" or item.status not in {"missing", "partial"}:
                continue
            if "deducted_net_profit" in item.field_name:
                blockers.append("缺少扣非净利润，无法判断利润增长是否来自主业或一次性收益。")
            elif "operating_cashflow" in item.field_name:
                blockers.append("缺少经营现金流，无法判断利润质量和盈利兑现能力。")
            elif "business_composition" in item.field_name:
                blockers.append("缺少主营构成，无法判断公司核心业务暴露和收入来源。")
            elif "commodity_prices" in item.field_name:
                blockers.append("缺少商品价格：资源股周期判断不完整。")
            elif "gross_margin" in item.field_name:
                blockers.append("缺少毛利率，无法判断盈利能力变化和产品/周期弹性。")
            elif "inventory" in item.field_name:
                blockers.append("缺少存货数据，无法判断半导体或制造业周期压力。")
            elif "roe" in item.field_name:
                blockers.append("缺少 ROE，无法判断资本回报质量。")
            else:
                blockers.append(f"缺少{item.display_name}：会阻断相关基本面分析。")
        return list(dict.fromkeys(blockers))

    def _build_analyzer_notes(self, items: list[FieldReadiness], strategy_type: str) -> list[str]:
        notes = []
        missing_names = {item.field_name for item in items if item.status in {"missing", "partial"}}
        if "external.commodity_prices" in missing_names:
            notes.append("不要把未验证的商品涨价逻辑写成确定性结论。")
        if any("operating_cashflow" in name for name in missing_names):
            notes.append("缺少现金流数据时，不能下高置信度利润质量结论。")
        if "business_composition.segments" in missing_names:
            notes.append("缺少主营构成时，不能断言公司主要受益于某一业务或商品。")
        if any("gross_margin" in name for name in missing_names):
            notes.append("缺少毛利率时，不能高置信度判断盈利质量改善。")
        if strategy_type == "satellite_communication_infrastructure":
            notes.append("confidence 表示当前 fundamental_view 的证据置信度，不等于正向强度。")
            if "satellite.capacity_utilization_or_lease_rate" in missing_names:
                notes.append("缺容量利用率 / 出租率时，不得断言卫星资源利用充分。")
            if "satellite.customer_structure_or_concentration" in missing_names:
                notes.append("缺客户结构时，不得断言需求稳定或定价能力强。")
            if "satellite.design_or_remaining_life" in missing_names or "financial_metrics.depreciation_amortization" in missing_names:
                notes.append("缺卫星寿命、折旧摊销或折旧年限政策时，不得忽略资产老化和利润可比性风险。")
            if "satellite.launch_plan" in missing_names:
                notes.append("缺卫星发射计划时，不得断言新增容量确定释放。")
        if strategy_type == "unknown":
            notes.append("分类未知时，只能描述数据缺口，不能强行套用行业框架。")
        return notes

    def _build_scorer_notes(self, items: list[FieldReadiness]) -> list[str]:
        notes = []
        for item in items:
            if item.status not in {"missing", "partial"}:
                continue
            affected = item.field_name
            prefix = "需要降置信度" if item.importance in {"critical", "high"} else "可能需要降置信度"
            if item.field_name.startswith("financial_metrics"):
                notes.append(f"financial_quality {prefix}：{item.display_name}不可完整使用。")
            if item.field_name.startswith("external."):
                notes.append(f"industry_cycle {prefix}：{item.display_name}缺失。")
            for dimension in self._affected_dimensions_for_field(item.field_name):
                notes.append(f"{dimension} {prefix}：{item.display_name}缺失或不完整。")
            if "operating_cashflow" in item.field_name:
                notes.append("不允许给现金流质量高分。")
                notes.append("risk_flags 应加入“经营现金流数据缺失”。")
            if "gross_margin" in item.field_name:
                notes.append("financial_quality 和 industry_cycle 需要降置信度；不允许断言毛利率改善。")
            if "inventory" in item.field_name:
                notes.append("semiconductor_cycle 的周期判断需要降置信度；不允许断言库存周期健康。")
            if item.importance in {"critical", "high"}:
                notes.append(f"risk_flags 必须加入数据缺失风险：{affected}。")
        return list(dict.fromkeys(notes))

    def _affected_dimensions_for_field(self, field_name: str) -> list[str]:
        if "gross_margin" in field_name:
            return ["financial_quality", "industry_cycle"]
        if "operating_cashflow" in field_name or "deducted_net_profit" in field_name:
            return ["financial_quality", "risk_flags"]
        if "inventory" in field_name:
            return ["industry_cycle", "risk_flags"]
        if "commodity_prices" in field_name:
            return ["industry_cycle", "catalysts"]
        if "business_composition" in field_name:
            return ["business_summary", "key_drivers"]
        return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Build data readiness plan for fundamental_skill.")
    parser.add_argument("--input", required=True, help="Path to raw JSON fixture")
    parser.add_argument("--output", help="Optional output JSON path")
    args = parser.parse_args()

    normalized = FundamentalDataAdapter().from_file(args.input)
    classification = StockClassifier().classify(normalized)
    framework = FrameworkSelector().select(classification)
    plan = DataReadinessPlanner().plan(normalized, classification, framework)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(plan.model_dump_json(indent=2), encoding="utf-8")

    print(f"stock_code: {plan.stock_code}")
    print(f"stock_name: {plan.stock_name}")
    print(f"strategy_type: {plan.strategy_type}")
    print(f"classification_confidence: {plan.classification_confidence}")
    print(f"readiness_score: {plan.readiness_score}")
    print(f"readiness_level: {plan.readiness_level}")
    print(f"critical_missing_fields: {plan.critical_missing_fields}")
    print(f"high_priority_missing_fields: {plan.high_priority_missing_fields}")
    print(f"analysis_blockers: {plan.analysis_blockers}")
    print(f"recommended_data_to_collect: {plan.recommended_data_to_collect}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
