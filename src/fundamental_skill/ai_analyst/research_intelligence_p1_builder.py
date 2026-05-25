# -*- coding: utf-8 -*-
"""Build Research Intelligence P1.1 pilot driver-matrix artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .research_intelligence_p1_schema import (
    LESS_THAN_TWO_BUCKETS_REASON,
    TRANSMISSION_PATH_FALLBACK,
    DriverFactor,
    ResearchDriverMatrixPack,
    ResearchDriverQuestion,
    ResearchDriverQuestionSet,
    SourceBucketSummary,
)


AI_DATACENTER_STRATEGY_TYPE = "ai_datacenter_infrastructure"
AI_DATACENTER_SUB_TYPES = {"cooling_liquid_cooling_infrastructure", "datacenter_operator"}
CXO_STRATEGY_TYPE = "life_science_cxo_services"
CXO_SUB_TYPES = {"integrated_cxo_platform", "cdmo_manufacturing_services", "clinical_cro_services"}
SATELLITE_STRATEGY_TYPE = "satellite_communication_infrastructure"
LOW_ALTITUDE_STRATEGY_TYPE = "low_altitude_economy_infrastructure"
LOW_ALTITUDE_SUB_TYPES = {"aviation_operations_service"}
RESOURCE_SWING_STRATEGY_TYPE = "resource_swing"
RESOURCE_CORE_STRATEGY_TYPE = "resource_core"
SEMICONDUCTOR_CYCLE_STRATEGY_TYPE = "semiconductor_cycle"
SEMICONDUCTOR_PRIMARY_SAMPLE = "002371"
ADVANCED_MANUFACTURING_STRATEGY_TYPE = "advanced_manufacturing_growth"
ADVANCED_MANUFACTURING_PRIMARY_SAMPLE = "002050"
STABLE_GROWTH_STRATEGY_TYPE = "stable_growth"
STABLE_GROWTH_PRIMARY_SAMPLE = "600406"
STABLE_GROWTH_VALIDATION_SAMPLE = "002028"
STABLE_GROWTH_EXCLUDED_SAMPLE = "600276"
SUPPORTED_STRATEGY_TYPES = {
    AI_DATACENTER_STRATEGY_TYPE,
    CXO_STRATEGY_TYPE,
    SATELLITE_STRATEGY_TYPE,
    LOW_ALTITUDE_STRATEGY_TYPE,
    RESOURCE_SWING_STRATEGY_TYPE,
    SEMICONDUCTOR_CYCLE_STRATEGY_TYPE,
    ADVANCED_MANUFACTURING_STRATEGY_TYPE,
    STABLE_GROWTH_STRATEGY_TYPE,
}

GENERIC_MISSING_BRIDGE_REASON = "Current evidence pack lacks concrete company transmission nodes for this driver."
ADVANCED_MANUFACTURING_LAYOUT_TERMS = (
    "积极布局",
    "开展研发",
    "开始涉足",
    "战略合作",
    "机器人关键零部件布局",
    "执行器布局",
    "layout",
    "strategic layout",
    "strategic cooperation",
)
RESOURCE_PRODUCT_TERMS = (
    "silver",
    "tin",
    "lead",
    "zinc",
    "copper",
    "gold",
    "molybdenum",
    "tungsten",
    "lithium",
    "nickel",
    "cobalt",
    "iron",
    "ore",
    "mine",
    "mining",
    "concentrate",
    "smelter",
    "processing",
    "银",
    "锡",
    "铅",
    "锌",
    "铜",
    "金",
    "钼",
    "钨",
    "锂",
    "镍",
    "钴",
    "铁",
    "矿",
    "精矿",
    "采选",
    "冶炼",
)


@dataclass(frozen=True)
class DriverSpec:
    layer: str
    driver_factor: str
    driver_scope: str
    why_it_matters: str
    required_evidence: tuple[str, ...]
    checked_paths: tuple[str, ...]
    interpretation_guard: str
    question: str
    next_check: str
    concrete_path_allowed: bool = False


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _metric_value(value: Any) -> Any:
    if isinstance(value, dict) and "raw_value" in value:
        return value.get("raw_value")
    return value


def _display_value(value: Any) -> str:
    if isinstance(value, dict):
        if value.get("display_value") not in (None, ""):
            return str(value.get("display_value"))
        if value.get("raw_value") not in (None, ""):
            return str(value.get("raw_value"))
    return str(value)


def _is_present(value: Any) -> bool:
    value = _metric_value(value)
    return value not in (None, "", [])


def _safe_text(value: Any, max_length: int = 160) -> str:
    text = str(value).replace("\n", " ").strip()
    return text if len(text) <= max_length else f"{text[:max_length]}..."


class ResearchIntelligenceP1Builder:
    """Build independent P1.1 driver matrix artifacts from an evidence pack."""

    def build(
        self,
        evidence_pack: dict[str, Any],
        p0_pack: dict[str, Any] | None = None,
        *,
        source_evidence_pack_path: str = "",
        source_p0_pack_path: str | None = None,
    ) -> tuple[ResearchDriverMatrixPack, ResearchDriverQuestionSet]:
        generated_at = datetime.now().isoformat(timespec="seconds")
        stock = evidence_pack.get("stock") if isinstance(evidence_pack.get("stock"), dict) else {}
        stock_code = str(stock.get("code") or evidence_pack.get("stock_code") or "UNKNOWN")
        stock_name = stock.get("name") or evidence_pack.get("stock_name")
        strategy_type = str(stock.get("strategy_type") or evidence_pack.get("strategy_type") or "unknown")
        sub_type = stock.get("sub_type") or evidence_pack.get("sub_type")

        source_summary = self.source_bucket_summary(evidence_pack)
        if strategy_type == AI_DATACENTER_STRATEGY_TYPE and sub_type in AI_DATACENTER_SUB_TYPES:
            drivers = self._ai_datacenter_drivers(evidence_pack, str(sub_type))
            summary_scope = "P1.1 AI datacenter pilot"
        elif strategy_type == CXO_STRATEGY_TYPE and sub_type in CXO_SUB_TYPES:
            drivers = self._cxo_drivers(evidence_pack, str(sub_type))
            summary_scope = "P1.1 CXO expansion"
        elif strategy_type == SATELLITE_STRATEGY_TYPE:
            drivers = self._satellite_drivers(evidence_pack)
            summary_scope = "P1.1 satellite expansion"
        elif strategy_type == LOW_ALTITUDE_STRATEGY_TYPE and sub_type in LOW_ALTITUDE_SUB_TYPES:
            drivers = self._low_altitude_drivers(evidence_pack, str(sub_type))
            summary_scope = "P1.1 low altitude expansion"
        elif strategy_type == RESOURCE_SWING_STRATEGY_TYPE and stock_code == "000426":
            drivers = self._resource_swing_drivers(evidence_pack)
            summary_scope = "P1.1 resource swing expansion"
        elif strategy_type == RESOURCE_CORE_STRATEGY_TYPE:
            drivers = [self._resource_core_design_only_driver(sub_type)]
            summary_scope = "P1.1 resource core design-only boundary"
        elif strategy_type == SEMICONDUCTOR_CYCLE_STRATEGY_TYPE and stock_code == SEMICONDUCTOR_PRIMARY_SAMPLE:
            drivers = self._semiconductor_cycle_drivers(evidence_pack)
            summary_scope = "P1.1 semiconductor expansion"
        elif strategy_type == ADVANCED_MANUFACTURING_STRATEGY_TYPE and stock_code == ADVANCED_MANUFACTURING_PRIMARY_SAMPLE:
            drivers = self._advanced_manufacturing_drivers(evidence_pack)
            summary_scope = "P1.1 advanced manufacturing expansion"
        elif strategy_type == STABLE_GROWTH_STRATEGY_TYPE and stock_code == STABLE_GROWTH_PRIMARY_SAMPLE:
            drivers = self._stable_growth_drivers(evidence_pack)
            summary_scope = "P1.1 stable growth expansion"
        elif strategy_type == STABLE_GROWTH_STRATEGY_TYPE:
            drivers = [self._stable_growth_boundary_driver(stock_code, sub_type)]
            summary_scope = "P1.1 stable growth validation / boundary sample"
        else:
            drivers = [self._unsupported_driver(strategy_type, sub_type)]
            summary_scope = "P1.1 unsupported pilot boundary"

        questions = [self._question_from_driver(driver) for driver in drivers]
        pack = ResearchDriverMatrixPack.model_validate(
            {
                "stock_code": stock_code,
                "stock_name": stock_name,
                "generated_at": generated_at,
                "strategy_type": strategy_type,
                "sub_type": sub_type,
                "source_evidence_pack_path": source_evidence_pack_path,
                "source_p0_pack_path": source_p0_pack_path,
                "driver_matrix": drivers,
                "not_assessable_drivers": [],
                "driver_research_questions": questions,
                "source_bucket_summary": source_summary,
            }
        )
        qset = ResearchDriverQuestionSet.model_validate(
            {
                "stock_code": stock_code,
                "stock_name": stock_name,
                "generated_at": generated_at,
                "strategy_type": strategy_type,
                "sub_type": sub_type,
                "questions": questions,
                "p1_summary": f"{summary_scope} driver questions: {len(questions)}",
            }
        )
        return pack, qset

    def source_bucket_summary(self, evidence_pack: dict[str, Any]) -> SourceBucketSummary:
        buckets: set[str] = set()
        for row in _as_list(evidence_pack.get("source_trace_summary")):
            if not isinstance(row, dict):
                continue
            block_name = str(row.get("block_name") or "").lower()
            trace_count = row.get("trace_count")
            if trace_count in (0, "0"):
                continue
            bucket = self._bucket_for_block(block_name)
            if bucket:
                buckets.add(bucket)
        if not buckets and evidence_pack:
            buckets.add("structured_data")

        reason = (
            LESS_THAN_TWO_BUCKETS_REASON
            if len(buckets) < 2
            else "P1.1 pilot records source-bucket independence only; full consensus assessment is deferred."
        )
        return SourceBucketSummary(
            source_buckets=sorted(buckets),
            independent_source_count=len(buckets),
            consensus_assessment_status="not_assessable",
            not_assessable_reason=reason,
        )

    def _bucket_for_block(self, block_name: str) -> str | None:
        if block_name in {"financial_indicator", "financial_metrics", "cash_flow", "balance_sheet", "income_statement"}:
            return "financial_statement"
        if block_name in {"business_composition", "basic_info", "company_announcement"}:
            return "company_disclosure"
        if block_name in {"news", "news_media"}:
            return "news_media"
        if block_name in {"ir", "company_ir"}:
            return "company_ir"
        if block_name in {"industry_official", "official_statistics"}:
            return "industry_official"
        if block_name in {"exchange_regulator", "exchange_notice"}:
            return "exchange_regulator"
        if block_name:
            return "structured_data"
        return None

    def _unsupported_driver(self, strategy_type: str, sub_type: Any) -> DriverFactor:
        return DriverFactor(
            layer="risk",
            driver_factor="unsupported_pilot_strategy",
            driver_scope="pilot_boundary",
            why_it_matters="P1.1 implementation is intentionally limited to accepted pilot strategy types.",
            required_evidence=[
                (
                    "accepted P1.1 support scope: ai_datacenter_infrastructure, "
                    "life_science_cxo_services, satellite_communication_infrastructure, "
                    "low_altitude_economy_infrastructure, resource_swing, semiconductor_cycle, "
                    "advanced_manufacturing_growth, stable_growth"
                ),
                (
                    "first-version sample boundaries: Resource=000426 only, Semiconductor=002371 only, "
                    "Advanced Manufacturing=002050 only, Stable Growth=600406 only"
                ),
                (
                    "resource_core remains design-only / deferred; right_trend_growth, theme_only, and "
                    "unknown remain unsupported / not_assessable"
                ),
                "supported pilot sub_type such as aviation_operations_service for low altitude",
            ],
            available_evidence=[f"input.strategy_type={strategy_type}", f"input.sub_type={sub_type}"],
            missing_evidence=["P1.1 template for this strategy_type or sub_type"],
            company_transmission_path=TRANSMISSION_PATH_FALLBACK,
            data_availability_status="not_assessable",
            confidence_cap="not_assessable",
            not_assessable_reason=(
                "Current P1.1 accepted support scope is ai_datacenter_infrastructure, "
                "life_science_cxo_services, satellite_communication_infrastructure, "
                "low_altitude_economy_infrastructure, resource_swing, semiconductor_cycle, "
                "advanced_manufacturing_growth, and stable_growth. First-version sample boundaries remain: "
                "Resource first-version only supports 000426 (000426 only); Semiconductor first-version only "
                "supports 002371 (002371 only); Advanced Manufacturing first-version only supports 002050 "
                "(002050 only); Stable Growth first-version only supports 600406 (600406 only). resource_core "
                "remains design-only / deferred; right_trend_growth, theme_only, and unknown remain unsupported "
                "/ not_assessable."
            ),
            what_was_checked=["stock.strategy_type", "stock.sub_type"],
            source_refs=[],
            research_question=(
                "Which accepted P1.1 expansion, if any, can assess this company under the current first-version "
                "scope, and what concrete evidence would be required before support can be widened?"
            ),
            interpretation_guard="Do not expand unsupported strategy types by free-form inference.",
        )

    def _resource_core_design_only_driver(self, sub_type: Any) -> DriverFactor:
        return DriverFactor(
            layer="risk",
            driver_factor="unsupported_pilot_strategy",
            driver_scope="resource_core_design_only_boundary",
            why_it_matters="P1.1 Resource first implementation is limited to resource_swing and keeps resource_core design-only.",
            required_evidence=[
                "strategy_type=resource_swing for first implementation",
                "historical operating cash flow for any later resource_core implementation",
                "capex split: sustaining vs expansionary for any later resource_core implementation",
                "debt / liquidity evidence for any later resource_core implementation",
                "dividend history or payout ratio for any later resource_core implementation",
            ],
            available_evidence=[f"input.strategy_type={RESOURCE_CORE_STRATEGY_TYPE}", f"input.sub_type={sub_type}"],
            missing_evidence=[
                "accepted first-implementation scope for resource_core",
                "complete resource_core implementation-gate evidence bundle",
            ],
            company_transmission_path=TRANSMISSION_PATH_FALLBACK,
            data_availability_status="not_assessable",
            confidence_cap="not_assessable",
            not_assessable_reason=(
                "resource_core is design-only in P1.1 Resource first implementation; "
                "do not assess stability, defensive quality, or dividend capacity."
            ),
            what_was_checked=["stock.strategy_type", "stock.sub_type"],
            source_refs=[],
            research_question=(
                "resource_core remains outside first implementation; does a later sample evidence pack provide "
                "operating cash flow history, sustaining-vs-expansionary capex split, debt/liquidity fields, "
                "and dividend history or payout ratio?"
            ),
            interpretation_guard=(
                "Do not generate resource_core stability, defensive, low-cost, or dividend-capacity judgments in "
                "the resource_swing first implementation."
            ),
        )

    def _resource_swing_drivers(self, pack: dict[str, Any]) -> list[DriverFactor]:
        return [self._build_resource_driver(pack, spec) for spec in self._resource_swing_specs()]

    def _resource_swing_specs(self) -> list[DriverSpec]:
        return [
            DriverSpec(
                "commodity",
                "core commodity price exposure",
                "macro / commodity / FX",
                "Commodity exposure identifies which product prices matter, but commodity price is not company revenue.",
                ("main commodity products", "product revenue ratio", "realized selling price", "production / sales volume", "cost and margin bridge"),
                ("basic_info.main_business", "business_composition", "financial_metrics.revenue", "financial_metrics.gross_margin", "financial_metrics.operating_cashflow", "commodity_prices"),
                "Commodity exposure is not company revenue or price benefit. External prices need realized price, volume, cost, margin, and cash-flow bridge.",
                "Which commodities actually drive company revenue, margin, and cash flow, and what product-level evidence links external prices to realized company economics?",
                "Check product / segment exposure, realized selling price, production volume, sales volume, unit cost, gross margin, and operating cash flow.",
                True,
            ),
            DriverSpec(
                "commodity",
                "commodity price cycle",
                "macro / commodity / FX",
                "Commodity-cycle context can affect resource companies, but cycle context is not company performance.",
                ("commodity cycle phase", "commodity price history", "realized price", "sales volume", "product inventory", "cash-flow bridge"),
                ("commodity_prices", "business_composition", "financial_metrics.revenue", "financial_metrics.gross_margin", "financial_metrics.inventory", "financial_metrics.operating_cashflow"),
                "Do not write commodity-cycle movement as company performance without realized company price, volume, margin, and cash-flow evidence.",
                "Has the commodity cycle translated into company realized price, sales volume, gross margin, working capital, and operating cash flow?",
                "Check commodity price series, realized selling price, sales volume, product inventory, margin, working capital, and operating cash flow.",
            ),
            DriverSpec(
                "macro",
                "USD / RMB FX exposure",
                "macro / commodity / FX",
                "FX exposure can affect USD-priced commodities, foreign revenue, costs, debt, cash, and derivatives.",
                ("currency-denominated revenue", "currency-denominated cost", "foreign-currency debt", "FX gain / loss", "FX hedge detail"),
                ("business_composition.geography", "financial_metrics.revenue", "missing_fields", "unknown_or_missing_evidence"),
                "Do not infer FX exposure solely from commodity type or export possibility.",
                "What revenue, cost, debt, cash, or derivative items expose the company to USD / RMB movement, and how is that visible in profit or cash flow?",
                "Check geographic / currency exposure, FX gain or loss, foreign-currency debt, cash, and derivative disclosure.",
            ),
            DriverSpec(
                "financial",
                "interest-rate / financing-cost pressure",
                "macro / commodity / FX",
                "Financing cost can constrain capex, liquidity, and cycle resilience when debt and maturity evidence exist.",
                ("debt amount", "interest expense", "rate structure", "debt maturity", "liquidity", "operating cash flow", "capex"),
                ("financial_metrics.operating_cashflow", "financial_metrics.capex", "missing_fields", "unknown_or_missing_evidence"),
                "Do not infer financing pressure without debt, interest expense, maturity, or liquidity evidence.",
                "Does financing cost or refinancing pressure constrain sustaining capex, expansion capex, liquidity, or resource-cycle resilience?",
                "Check debt, interest expense, rate structure, maturity schedule, liquidity, operating cash flow, and capex.",
            ),
            DriverSpec(
                "commodity",
                "global demand / inventory cycle",
                "macro / commodity / FX",
                "Demand and inventory-cycle signals need product inventory, sales volume, and cash-conversion evidence.",
                ("global demand series", "exchange / downstream inventory", "product-level company inventory", "sales volume", "production / sales reconciliation"),
                ("financial_metrics.inventory", "financial_metrics.revenue", "financial_metrics.accounts_receivable", "financial_metrics.operating_cashflow", "commodity_prices"),
                "Inventory change alone, even combined with revenue growth, is not demand evidence.",
                "Are global demand and inventory-cycle signals visible in company sales volume, product inventory, receivables, and operating cash flow?",
                "Check external demand, exchange inventory, product inventory split, sales volume, production / sales reconciliation, receivables, and operating cash flow.",
            ),
            DriverSpec(
                "policy",
                "policy / supply constraint",
                "macro / commodity / FX",
                "Policy and supply constraints can affect mine permits, quotas, output, costs, and capex only with company-specific evidence.",
                ("mine permit / quota", "production restriction", "environmental policy event", "company mine or capacity impact", "financial impact"),
                ("basic_info.industry", "business_composition", "risk_flags", "missing_fields", "unknown_or_missing_evidence"),
                "Policy / supply constraint is not automatic pricing power, production impact, or company realization.",
                "Which policy or supply constraints affect the company's mines, smelters, permits, output, costs, or capex requirements?",
                "Check permits, quotas, production restrictions, company mine/capacity impact, cost effect, and capex requirement.",
            ),
            DriverSpec(
                "company",
                "commodity revenue exposure",
                "company / asset / operation",
                "Product revenue exposure is the first company-level resource transmission node.",
                ("revenue by commodity", "revenue ratio", "segment gross margin", "period", "product definition"),
                ("basic_info.main_business", "business_composition", "financial_metrics.revenue", "financial_metrics.gross_margin"),
                "Revenue exposure is not realized commodity price sensitivity by itself.",
                "What share of revenue and gross margin comes from each commodity, and what segment definitions support the exposure?",
                "Check commodity segment name, revenue, revenue ratio, period, gross margin, and total revenue.",
                True,
            ),
            DriverSpec(
                "company",
                "production volume",
                "company / asset / operation",
                "Production volume is required before assessing mine output or ramp-up.",
                ("mine / product output", "concentrate / metal content", "period", "production vs capacity", "production disruption"),
                ("basic_info.main_business", "business_composition", "missing_fields", "unknown_or_missing_evidence"),
                "Do not treat resource amount, revenue, reserves, capex, or capacity as production.",
                "What production volume by commodity and mine validates operating output, and how does it compare with capacity and sales volume?",
                "Check product output, mine output, metal content, production period, capacity comparison, and disruption disclosure.",
            ),
            DriverSpec(
                "company",
                "sales volume",
                "company / asset / operation",
                "Sales volume and realized price are required to reconcile commodity revenue.",
                ("product sales volume", "realized selling price", "revenue reconciliation", "inventory movement", "customer / region split"),
                ("business_composition", "financial_metrics.revenue", "financial_metrics.inventory", "missing_fields", "unknown_or_missing_evidence"),
                "Do not treat production volume as sales volume unless both are disclosed and reconciled.",
                "What sales volume and realized price reconcile reported commodity revenue, and what inventory movement explains production-sales gaps?",
                "Check sales volume, realized selling price, revenue reconciliation, inventory movement, and customer / region split.",
            ),
            DriverSpec(
                "company",
                "grade / resource quality",
                "company / asset / operation",
                "Ore grade and recovery determine resource quality and cost position only when disclosed.",
                ("ore grade", "recovery rate", "concentrate grade", "mine dilution", "by-product credit", "cost and margin bridge"),
                ("business_composition", "financial_metrics.gross_margin", "missing_fields", "unknown_or_missing_evidence"),
                "Absence of grade data is not proof of poor resource quality; missing data supports only missing / not_assessable.",
                "What ore grade and recovery evidence supports resource quality and cost position by mine or product?",
                "Check ore grade, recovery rate, concentrate grade, dilution, by-product credit, cost, and margin bridge.",
            ),
            DriverSpec(
                "company",
                "reserves / resources",
                "company / asset / operation",
                "Reserves and resources inform mine-life questions, but they are not production volume.",
                ("reserves and resources by mine", "reporting standard", "commodity content", "grade", "update date", "depletion and conversion"),
                ("basic_info.main_business", "business_composition", "missing_fields", "unknown_or_missing_evidence"),
                "Do not treat reserves or resources as production, sales, or near-term cash flow.",
                "What reserves / resources are disclosed by mine, and how do grade, depletion, and conversion affect mine life?",
                "Check reserves, resources, reporting standard, commodity content, grade, update date, depletion, and conversion.",
            ),
            DriverSpec(
                "company",
                "mine / smelter / processing capacity",
                "company / asset / operation",
                "Capacity must be evidenced by asset, permit, utilization, and production bridge before use in resource analysis.",
                ("mine capacity", "processing capacity", "smelting capacity", "utilization", "bottleneck", "expansion status", "product bridge"),
                ("basic_info.main_business", "business_composition", "financial_metrics.capex", "missing_fields", "unknown_or_missing_evidence"),
                "Capex and business descriptions cannot substitute for accepted capacity, utilization, or output evidence.",
                "What mine, smelter, or processing capacity is available and utilized, and where are bottlenecks?",
                "Check mine capacity, processing capacity, smelting capacity, utilization, bottleneck, expansion status, and product bridge.",
            ),
            DriverSpec(
                "company",
                "inventory",
                "company / asset / operation",
                "Inventory can signal working-capital pressure only after product split and production-sales reconciliation.",
                (
                    "inventory amount",
                    "inventory type",
                    "product inventory",
                    "raw material / concentrate / finished goods split",
                    "write-down",
                    "sales volume",
                    "production / sales reconciliation",
                ),
                ("basic_info.main_business", "business_composition", "financial_metrics.inventory", "financial_metrics.revenue", "financial_metrics.operating_cashflow"),
                "Inventory decline plus revenue growth is still two financial observations, not an operating demand signal.",
                "What inventory type is building or falling, and does it reflect production-sales timing, price movement, or demand / collection pressure?",
                "Check inventory amount, product split, age, write-down, sales volume, production / sales reconciliation, revenue, and cash flow.",
                True,
            ),
            DriverSpec(
                "company",
                "hedging / derivative exposure",
                "company / asset / operation",
                "Hedging can change price-risk transmission only when derivative details are disclosed.",
                ("hedge notional", "commodity", "maturity", "hedge accounting", "fair value", "realized / unrealized gain or loss", "risk policy"),
                ("risk_flags", "missing_fields", "unknown_or_missing_evidence"),
                "Missing hedging disclosure means hedging status is not assessable; do not write risk as hedged or unhedged.",
                "Does the company use commodity or FX hedges, and what mismatch, maturity, or fair-value risk remains?",
                "Check hedge notional, commodity, maturity, hedge accounting, fair value, realized or unrealized gain/loss, and risk policy.",
            ),
            DriverSpec(
                "company",
                "cost curve position",
                "company / asset / operation",
                "Cost-curve position needs unit cost and peer evidence, not only gross margin.",
                ("cash cost", "all-in sustaining cost", "unit mining / processing cost", "by-product credit", "grade", "peer comparison"),
                ("business_composition", "financial_metrics.gross_margin", "financial_metrics.operating_cashflow", "missing_fields", "unknown_or_missing_evidence"),
                "Do not infer low-cost position from gross margin alone.",
                "Where does the company sit on the cost curve, and what evidence links grade, recovery, unit cost, and margin resilience?",
                "Check cash cost, all-in sustaining cost, unit cost, by-product credit, grade, and peer cost curve.",
            ),
            DriverSpec(
                "financial",
                "revenue sensitivity to commodity price",
                "financial",
                "Revenue sensitivity requires realized selling price and sales volume, not revenue growth alone.",
                ("product revenue ratio", "realized selling price", "sales volume", "commodity price series", "pricing formula", "pricing lag"),
                ("basic_info.main_business", "business_composition", "financial_metrics.revenue", "financial_metrics.revenue_yoy", "financial_metrics.realized_selling_price", "financial_metrics.sales_volume", "commodity_prices"),
                "Do not infer commodity price transmission from segment revenue plus revenue YoY. Revenue growth cannot be attributed to commodity price unless realized selling price and sales volume are both cited.",
                "How sensitive is revenue to each commodity after considering product mix, realized price, sales volume, pricing formula, and pricing lag?",
                "Check realized selling price, sales volume, pricing formula, pricing lag, product revenue ratio, and commodity price series.",
                True,
            ),
            DriverSpec(
                "financial",
                "gross margin sensitivity",
                "financial",
                "Gross-margin sensitivity requires realized price, unit cost, and product margin bridge.",
                ("product gross margin", "realized price", "unit cost", "energy / labor / treatment charge", "by-product credit", "inventory cost method"),
                ("basic_info.main_business", "business_composition", "financial_metrics.gross_margin", "financial_metrics.revenue", "commodity_prices"),
                "Do not infer margin leverage from commodity exposure alone.",
                "Which price and cost variables explain gross margin movement by commodity or segment?",
                "Check product gross margin, realized price, unit cost, treatment / refining charges, by-product credit, and inventory cost method.",
                True,
            ),
            DriverSpec(
                "financial",
                "operating cash flow",
                "financial",
                "Operating cash flow tests whether commodity revenue converts into cash after working-capital effects.",
                ("operating cash flow", "revenue", "receivables", "payables", "inventory", "capex separation", "commodity cycle bridge"),
                ("basic_info.main_business", "business_composition", "financial_metrics.operating_cashflow", "financial_metrics.revenue", "financial_metrics.accounts_receivable", "financial_metrics.inventory", "financial_metrics.capex"),
                "Cash flow is validation evidence, not proof of resource-core steadiness or commodity demand by itself.",
                "Does operating cash flow validate commodity revenue quality after receivables, inventory, payables, and price-cycle effects?",
                "Check operating cash flow, revenue, receivables, payables, inventory, capex separation, and commodity-cycle bridge.",
                True,
            ),
            DriverSpec(
                "financial",
                "capex: sustaining vs expansionary",
                "financial",
                "Capex must be split and bridged to projects before any asset or output interpretation.",
                ("capex total", "sustaining capex", "expansion capex", "project / mine mapping", "construction progress", "acceptance", "output bridge"),
                ("basic_info.main_business", "business_composition", "financial_metrics.capex", "financial_metrics.revenue", "financial_metrics.operating_cashflow"),
                "Aggregate capex is only cash outflow / investment observation; it is not mine ramp-up, smelter utilization, output growth, or revenue conversion.",
                "What portion of capex maintains existing assets versus expands capacity, and what evidence links projects to accepted capacity and output?",
                "Check total capex, sustaining vs expansionary split, project / mine mapping, progress, acceptance, utilization, output, revenue, and cash flow.",
                True,
            ),
            DriverSpec(
                "financial",
                "debt / liquidity / refinancing pressure",
                "financial",
                "Debt and liquidity pressure require balance-sheet, interest, maturity, and cash-flow evidence.",
                ("debt amount", "cash", "interest expense", "maturity schedule", "refinancing plan", "covenants", "operating cash flow", "capex"),
                ("financial_metrics.operating_cashflow", "financial_metrics.capex", "missing_fields", "unknown_or_missing_evidence"),
                "Do not infer refinancing risk without debt schedule, interest expense, and liquidity evidence.",
                "Does debt maturity or financing cost pressure constrain mine operation, sustaining capex, expansion plans, or dividends?",
                "Check debt amount, cash, interest expense, maturity schedule, refinancing plan, covenants, operating cash flow, and capex.",
            ),
            DriverSpec(
                "financial",
                "depreciation / depletion",
                "financial",
                "Depreciation, depletion, asset life, and reserve conversion affect reported profit quality.",
                ("depreciation", "depletion", "amortization", "mine life", "asset base", "impairment", "production units method"),
                ("financial_metrics.gross_margin", "financial_metrics.operating_cashflow", "missing_fields", "unknown_or_missing_evidence"),
                "Do not compare profitability without checking depletion and asset-life policy.",
                "How do depreciation, depletion, asset life, and reserve conversion affect reported profit and cash-flow quality?",
                "Check depreciation, depletion, amortization, mine life, asset base, impairment, and production-units method.",
            ),
            DriverSpec(
                "financial",
                "working capital",
                "financial",
                "Working capital requires receivables, inventory, payables, product split, and operating-volume bridge.",
                ("receivables", "inventory", "payables", "prepayments", "customer / supplier terms", "sales volume", "production / sales reconciliation"),
                ("basic_info.main_business", "business_composition", "financial_metrics.accounts_receivable", "financial_metrics.inventory", "financial_metrics.revenue", "financial_metrics.operating_cashflow"),
                "Lower inventory and higher revenue are not an operating demand signal; two financial observations are not operating demand evidence.",
                "Are working-capital movements driven by price, volume, inventory timing, customer collection, or supplier terms?",
                "Check receivables, inventory, payables, prepayments, product inventory, sales volume, production / sales reconciliation, customer terms, and supplier terms.",
                True,
            ),
            DriverSpec(
                "risk",
                "commodity price volatility",
                "risk",
                "Commodity price volatility requires product exposure, realized price, sensitivity, and hedging status to assess risk transmission.",
                ("product exposure", "commodity price history", "realized price", "hedging status", "margin and cash-flow sensitivity"),
                ("basic_info.main_business", "business_composition", "financial_metrics.revenue", "financial_metrics.gross_margin", "financial_metrics.operating_cashflow", "commodity_prices", "risk_flags"),
                "Do not claim price risk is hedged or unhedged beyond disclosed hedging evidence.",
                "How does commodity price volatility flow through product revenue, margin, hedging gain/loss, and operating cash flow?",
                "Check product exposure, commodity price history, realized price, hedging status, margin sensitivity, and cash-flow sensitivity.",
                True,
            ),
            DriverSpec(
                "risk",
                "production disruption",
                "risk",
                "Production disruption needs event, output, permit, safety, or maintenance evidence.",
                ("mine accident", "maintenance shutdown", "permit suspension", "grade decline", "equipment issue", "affected output", "financial impact"),
                ("risk_flags", "missing_fields", "unknown_or_missing_evidence", "financial_metrics.revenue"),
                "Revenue changes alone cannot identify production disruption or prove absence of disruption.",
                "Have mine, smelter, processing, safety, or permit disruptions affected production, cost, revenue, or cash flow?",
                "Check mine accident, maintenance shutdown, permit suspension, grade decline, equipment issue, affected output, and financial impact.",
            ),
            DriverSpec(
                "risk",
                "resource reserve depletion",
                "risk",
                "Reserve depletion requires reserve base, production, depletion rate, and exploration replacement.",
                ("reserve base", "mine life", "annual production", "depletion rate", "exploration replacement", "impairment"),
                ("basic_info.main_business", "business_composition", "missing_fields", "unknown_or_missing_evidence"),
                "Do not treat resource quantity as production or mine-life proof without grade and depletion context.",
                "Is reserve depletion or inadequate replacement affecting mine life, capex need, and long-term production visibility?",
                "Check reserve base, mine life, annual production, depletion rate, exploration replacement, and impairment.",
            ),
            DriverSpec(
                "risk",
                "environmental / safety / regulatory risk",
                "risk",
                "Environmental, safety, and regulatory events can affect output, cost, permits, capex, and cash flow.",
                ("environmental penalties", "safety accidents", "tailings / water / land permits", "production restrictions", "compliance cost", "remediation capex"),
                ("risk_flags", "missing_fields", "unknown_or_missing_evidence", "basic_info.industry"),
                "Absence of event data is not proof of compliant or safe operations.",
                "What environmental, safety, or regulatory events could affect output, costs, permits, capex, or cash flow?",
                "Check environmental penalties, safety accidents, tailings/water/land permits, restrictions, compliance cost, and remediation capex.",
            ),
            DriverSpec(
                "risk",
                "FX risk",
                "risk",
                "FX risk needs currency-denominated exposure or FX gain/loss evidence.",
                ("foreign-currency revenue / cost / debt / cash", "FX gain/loss", "hedge notional", "sensitivity"),
                ("business_composition.geography", "missing_fields", "unknown_or_missing_evidence", "risk_flags"),
                "Do not infer FX risk magnitude without currency-denominated evidence.",
                "What foreign-currency exposures create earnings, cash-flow, or debt-service risk, and are they hedged?",
                "Check foreign-currency revenue, cost, debt, cash, FX gain/loss, hedge notional, and sensitivity.",
            ),
            DriverSpec(
                "risk",
                "hedging loss / mismatch risk",
                "risk",
                "Hedging mismatch can occur only if hedge and underlying physical exposure evidence are disclosed.",
                ("hedge notional", "commodity / FX item hedged", "maturity", "fair value", "realized and unrealized gain/loss", "physical exposure match"),
                ("risk_flags", "missing_fields", "unknown_or_missing_evidence"),
                "Missing hedging disclosure means mismatch risk is not assessable; do not describe price risk as hedged or unhedged.",
                "Do hedges match physical exposure in volume, timing, commodity, and currency, or could hedge losses / mismatch occur?",
                "Check hedge notional, hedged item, maturity, fair value, realized and unrealized gain/loss, and physical exposure match.",
            ),
            DriverSpec(
                "risk",
                "capex overrun",
                "risk",
                "Capex overrun requires project budget, actual spend, progress, schedule, and acceptance evidence.",
                ("project budget", "actual spend", "progress", "schedule", "funding", "acceptance", "revised budget", "output bridge"),
                ("financial_metrics.capex", "missing_fields", "unknown_or_missing_evidence", "risk_flags"),
                "Aggregate capex cannot show project overrun, completion, accepted capacity, utilization, output, or revenue bridge.",
                "Are mine, smelter, or processing projects running over budget or behind schedule, and how does that affect funding and output?",
                "Check project budget, actual spend, progress, schedule, funding, acceptance, revised budget, and output bridge.",
            ),
            DriverSpec(
                "risk",
                "debt-cycle risk",
                "risk",
                "Debt-cycle risk requires debt maturity, interest rate, liquidity, capex commitments, and commodity stress evidence.",
                ("debt maturity", "refinancing", "interest rates", "commodity downturn stress", "liquidity", "capex commitments", "covenant risk"),
                ("financial_metrics.operating_cashflow", "financial_metrics.capex", "missing_fields", "unknown_or_missing_evidence"),
                "Do not infer debt-cycle risk without debt schedule, liquidity, and interest expense evidence.",
                "Under commodity-cycle stress, do debt maturities, capex commitments, and liquidity create refinancing or covenant pressure?",
                "Check debt maturity, refinancing, interest rates, liquidity, capex commitments, covenants, and commodity-stress sensitivity.",
            ),
        ]

    def _build_resource_driver(self, pack: dict[str, Any], spec: DriverSpec) -> DriverFactor:
        available = self._available_evidence(pack, spec.checked_paths)
        missing = self._missing_evidence(pack, spec.required_evidence, spec.checked_paths)
        business_nodes = self._prioritize_resource_business_nodes(
            [item for item in available if self._is_resource_business_node(item)]
        )
        financial_nodes = [item for item in available if "evidence_pack.financial_metrics." in item]

        hard_fallback_reason = ""
        if spec.driver_factor == "revenue sensitivity to commodity price" and not self._has_realized_price_and_sales_volume(pack):
            hard_fallback_reason = (
                "Realized selling price and sales volume are both required; segment revenue and revenue YoY "
                "must not be combined into commodity price transmission."
            )
        elif spec.driver_factor in {
            "commodity price cycle",
            "USD / RMB FX exposure",
            "interest-rate / financing-cost pressure",
            "global demand / inventory cycle",
            "policy / supply constraint",
            "production volume",
            "sales volume",
            "grade / resource quality",
            "reserves / resources",
            "mine / smelter / processing capacity",
            "hedging / derivative exposure",
            "cost curve position",
            "debt / liquidity / refinancing pressure",
            "depreciation / depletion",
            "production disruption",
            "resource reserve depletion",
            "environmental / safety / regulatory risk",
            "FX risk",
            "hedging loss / mismatch risk",
            "capex overrun",
            "debt-cycle risk",
        }:
            hard_fallback_reason = "Current evidence pack lacks the required resource-specific operating or risk evidence."

        if spec.concrete_path_allowed and not hard_fallback_reason:
            if business_nodes and financial_nodes:
                path_nodes = [business_nodes[0], *financial_nodes[:2]]
                path = " -> ".join(path_nodes)
                status = "partial" if missing else "available"
                cap = "low" if missing else "medium"
                reason = ""
            elif business_nodes:
                path_nodes = [business_nodes[0]]
                path = business_nodes[0]
                status = "partial"
                cap = "low"
                reason = ""
            else:
                path_nodes = []
                path = TRANSMISSION_PATH_FALLBACK
                status = "not_assessable"
                cap = "not_assessable"
                reason = (
                    "Resource transmission requires a product / segment business node; financial metrics alone "
                    "cannot establish commodity or operating transmission."
                )
        else:
            path_nodes = []
            path = TRANSMISSION_PATH_FALLBACK
            status = "not_assessable"
            cap = "not_assessable"
            reason = hard_fallback_reason or GENERIC_MISSING_BRIDGE_REASON

        return DriverFactor(
            layer=spec.layer,  # type: ignore[arg-type]
            driver_factor=spec.driver_factor,
            driver_scope=spec.driver_scope,
            why_it_matters=spec.why_it_matters,
            required_evidence=list(spec.required_evidence),
            available_evidence=available,
            missing_evidence=missing,
            company_transmission_path=path,
            data_availability_status=status,  # type: ignore[arg-type]
            confidence_cap=cap,  # type: ignore[arg-type]
            not_assessable_reason=reason,
            what_was_checked=list(spec.checked_paths),
            source_refs=[item.split("=")[0] for item in path_nodes],
            research_question=spec.question,
            interpretation_guard=spec.interpretation_guard,
        )

    def _is_resource_business_node(self, node: str) -> bool:
        if "evidence_pack.business_composition" in node:
            return True
        if "evidence_pack.basic_info.main_business=" not in node:
            return False
        lowered = node.lower()
        return any(term.lower() in lowered for term in RESOURCE_PRODUCT_TERMS)

    def _prioritize_resource_business_nodes(self, nodes: list[str]) -> list[str]:
        return sorted(nodes, key=lambda item: 0 if "evidence_pack.business_composition" in item else 1)

    def _has_realized_price_and_sales_volume(self, pack: dict[str, Any]) -> bool:
        price_paths = (
            "financial_metrics.realized_selling_price",
            "resource_metrics.realized_selling_price",
            "operation_metrics.realized_selling_price",
            "realized_selling_price",
        )
        volume_paths = (
            "financial_metrics.sales_volume",
            "resource_metrics.sales_volume",
            "operation_metrics.sales_volume",
            "sales_volume",
        )
        return any(_is_present(self._value_at_path(pack, path)) for path in price_paths) and any(
            _is_present(self._value_at_path(pack, path)) for path in volume_paths
        )

    def _stable_growth_boundary_driver(self, stock_code: str, sub_type: Any) -> DriverFactor:
        boundary_scope = "stable_growth P1.1 first implementation supports primary sample 600406 only."
        reason = boundary_scope
        if stock_code == STABLE_GROWTH_VALIDATION_SAMPLE:
            reason = (
                "002028 is a validation sample for boundary behavior and is not in the first-version positive path; "
                f"{boundary_scope}"
            )
        elif stock_code == STABLE_GROWTH_EXCLUDED_SAMPLE:
            reason = (
                "600276 is excluded from the first implementation and must not be force-fit into stable_growth; "
                f"{boundary_scope}"
            )
        return DriverFactor(
            layer="risk",
            driver_factor="unsupported_pilot_strategy",
            driver_scope="stable_growth_first_version_boundary",
            why_it_matters="P1.1 Stable Growth first implementation is intentionally narrowed to one primary sample.",
            required_evidence=[
                "strategy_type=stable_growth",
                "stock.code=600406 for first implementation",
                "current evidence pack with field-level financial and segment evidence",
            ],
            available_evidence=[
                f"input.stock_code={stock_code}",
                f"input.strategy_type={STABLE_GROWTH_STRATEGY_TYPE}",
                f"input.sub_type={sub_type}",
            ],
            missing_evidence=["accepted first-version stable_growth positive path for this sample"],
            company_transmission_path=TRANSMISSION_PATH_FALLBACK,
            data_availability_status="not_assessable",
            confidence_cap="not_assessable",
            not_assessable_reason=reason,
            what_was_checked=["stock.code", "stock.strategy_type", "stock.sub_type"],
            source_refs=[],
            research_question=(
                "Which accepted P1.1 expansion, if any, can assess this stable_growth boundary sample under the "
                "current first-version scope, and what concrete evidence would be required before support can be widened?"
            ),
            interpretation_guard="Do not extend stable_growth beyond 600406 or force-fit validation / excluded samples.",
        )

    def _stable_growth_drivers(self, pack: dict[str, Any]) -> list[DriverFactor]:
        return [self._build_stable_growth_driver(pack, payload) for payload in self._stable_growth_payloads()]

    def _stable_growth_payloads(self) -> list[dict[str, Any]]:
        valuation_question = "当前 evidence pack 中哪些证据足以支撑或解释当前估值背景，哪些证据仍缺失？"
        return [
            {
                "layer": "business",
                "driver_factor": "recurring revenue or repeat-order quality",
                "driver_scope": "business / demand",
                "why_it_matters": "Repeatability must be proven by renewal, repeat-order, cohort, contract, revenue-recognition, and collection evidence.",
                "required_evidence": ["product / service revenue", "repeat-order or renewal rate", "customer cohort", "contract duration", "collection"],
                "checked_paths": ("business_composition", "financial_metrics.revenue", "financial_metrics.contract_liabilities", "financial_metrics.operating_cashflow", "financial_metrics.accounts_receivable"),
                "path_policy": "fallback",
                "status": "not_assessable",
                "missing_evidence": ["renewal / repeat-order rate", "customer cohort", "contract duration", "order-to-revenue bridge", "collection bridge"],
                "not_assessable_reason": "Current evidence has segment and financial observations but no repeat-order, renewal, cohort, or contract-duration evidence.",
                "interpretation_guard": "Do not treat revenue growth, historical size, or the stable_growth label as recurring revenue.",
                "research_question": "What renewal, repeat-order, customer cohort, contract-duration, revenue-recognition, and collection evidence supports recurring revenue?",
            },
            {
                "layer": "business",
                "driver_factor": "customer stability",
                "driver_scope": "business / demand",
                "why_it_matters": "Customer stability requires customer-level retention, tenure, concentration, renewal, and payment behavior evidence.",
                "required_evidence": ["top customer revenue share", "customer tenure", "renewal / retention", "customer payment behavior", "receivable by customer"],
                "checked_paths": ("financial_metrics.revenue", "financial_metrics.accounts_receivable", "financial_metrics.operating_cashflow", "business_composition"),
                "path_policy": "fallback",
                "status": "not_assessable",
                "missing_evidence": ["top customer list", "customer tenure", "retention / churn", "customer payment behavior", "customer-level receivables"],
                "not_assessable_reason": "Customer-specific evidence is absent; aggregate revenue and receivables are financial observations only.",
                "interpretation_guard": "Do not infer customer stability from industry position, broad segment labels, or aggregate revenue.",
                "research_question": "Which customers support revenue stability, and is retention visible in orders, revenue, receivables, and cash collection?",
            },
            {
                "layer": "business",
                "driver_factor": "product / service demand durability",
                "driver_scope": "business / demand",
                "why_it_matters": "Demand durability must come from company-level multi-period revenue, retention, repeat order, renewal pricing, collection, or cash conversion.",
                "required_evidence": ["multi-period product / service revenue", "customer retention", "repeat order", "pricing renewal", "collection or cash conversion"],
                "checked_paths": ("basic_info.industry", "basic_info.main_business", "business_composition", "financial_metrics.revenue", "financial_metrics.operating_cashflow"),
                "path_policy": "fallback",
                "status": "not_assessable",
                "missing_evidence": ["multi-period product demand", "customer retention", "repeat-order evidence", "pricing-renewal evidence", "cash-conversion evidence"],
                "not_assessable_reason": "Industry, infrastructure, ownership, or product-attribute wording cannot verify company-level demand durability.",
                "interpretation_guard": "Industry type, rigid demand, infrastructure, policy protection, and SOE / central-SOE attributes are not demand durability evidence.",
                "research_question": "What company-level multi-period revenue, retention, repeat-order, pricing-renewal, collection, or cash-conversion evidence proves demand durability?",
            },
            {
                "layer": "business",
                "driver_factor": "order visibility",
                "driver_scope": "business / demand",
                "why_it_matters": "Order visibility requires signed orders, delivery schedule, cancellation history, shipment, revenue recognition, and collection evidence.",
                "required_evidence": ["signed orders", "true order table", "delivery schedule", "cancellation history", "shipment / acceptance", "collection"],
                "checked_paths": ("financial_metrics.contract_liabilities", "financial_metrics.revenue", "financial_metrics.operating_cashflow"),
                "path_policy": "fallback",
                "status": "missing",
                "missing_evidence": ["signed orders", "true order table", "delivery schedule", "cancellation history", "shipment / acceptance", "revenue-recognition terms"],
                "not_assessable_reason": "Signed-order and delivery evidence is absent; contract liabilities alone cannot establish order visibility.",
                "interpretation_guard": "Contract liabilities are partial proxy only; they are not backlog, signed orders, delivery schedule, or future revenue.",
                "research_question": "Which signed orders, delivery schedules, cancellations, shipments, revenue-recognition terms, and collections support order visibility?",
            },
            {
                "layer": "business",
                "driver_factor": "contract liabilities as partial proxy only",
                "driver_scope": "business / demand",
                "why_it_matters": "Contract liabilities can be a limited financial proxy only when kept separate from signed orders and delivery evidence.",
                "required_evidence": ["contract liabilities", "linked customer / order / project", "prepayment terms", "revenue-recognition schedule"],
                "checked_paths": ("financial_metrics.contract_liabilities", "financial_metrics.revenue", "financial_metrics.operating_cashflow"),
                "path_policy": "contract_liability_proxy",
                "missing_evidence": ["customer / order mapping", "project mapping", "prepayment terms", "revenue-recognition schedule"],
                "interpretation_guard": "Contract liabilities are partial proxy only; they are not backlog, signed orders, delivery schedule, future revenue, or stability proof.",
                "research_question": "Which customer, order, project mapping, prepayment terms, and revenue-recognition schedule explain contract liabilities as a partial proxy?",
            },
            {
                "layer": "business",
                "driver_factor": "customer concentration",
                "driver_scope": "business / demand",
                "why_it_matters": "Concentration can support or weaken stability only with customer share, customer-level receivables, and trend evidence.",
                "required_evidence": ["top customer revenue share", "top-five customer share", "customer-level receivables", "concentration trend"],
                "checked_paths": ("business_composition", "financial_metrics.accounts_receivable", "risk_flags", "unknown_or_missing_evidence"),
                "path_policy": "fallback",
                "status": "not_assessable",
                "missing_evidence": ["top customer revenue share", "top-five customer share", "customer-level receivables", "concentration trend"],
                "not_assessable_reason": "Top-customer and customer-receivable fields are absent.",
                "interpretation_guard": "Do not infer diversification from broad business segments alone.",
                "research_question": "Does customer concentration support stability or create dependency and collection risk, and what customer-level evidence proves it?",
            },
            {
                "layer": "business",
                "driver_factor": "pricing power evidence",
                "driver_scope": "business / demand",
                "why_it_matters": "Pricing power needs price, cost, volume, renewal, and customer-acceptance evidence beyond margin observations.",
                "required_evidence": ["price changes", "price formula", "volume", "unit cost", "renewal pricing", "customer acceptance"],
                "checked_paths": ("business_composition", "financial_metrics.gross_margin", "financial_metrics.revenue"),
                "path_policy": "fallback",
                "status": "not_assessable",
                "missing_evidence": ["product price / volume", "unit cost", "pricing formula", "renewal-pricing terms", "customer acceptance"],
                "not_assessable_reason": "Current margin and segment fields are observations only; price / volume and renewal-pricing evidence is absent.",
                "interpretation_guard": "Do not infer pricing power from stable or high gross margin alone.",
                "research_question": "Is margin supported by pricing power, cost pass-through, product mix, or temporary cost movement, and what price / volume evidence separates them?",
            },
            {
                "layer": "business",
                "driver_factor": "business mix stability",
                "driver_scope": "business / demand",
                "why_it_matters": "Business mix needs multi-period segment and product/customer mix evidence before any stability conclusion.",
                "required_evidence": ["multi-period revenue mix", "segment margins", "product / customer mix", "new / old business split"],
                "checked_paths": ("business_composition", "financial_metrics.revenue", "financial_metrics.gross_margin"),
                "path_policy": "segment_financial_observation",
                "missing_evidence": ["multi-period segment mix", "customer mix trend", "product-line trend", "segment restatement history"],
                "interpretation_guard": "One-period segment composition is an observation only, not long-term mix stability.",
                "research_question": "Has business mix remained stable across periods, and which product / service lines drive revenue and margin quality?",
            },
            {
                "layer": "financial",
                "driver_factor": "revenue growth quality",
                "driver_scope": "financial quality",
                "why_it_matters": "Revenue quality needs multi-period revenue, cash conversion, receivables, inventory, customer, order, and segment bridge evidence.",
                "required_evidence": ["multi-period revenue", "revenue YoY", "segment revenue", "cash conversion", "receivables", "inventory", "customer / order bridge"],
                "checked_paths": ("business_composition", "financial_metrics.revenue", "financial_metrics.revenue_yoy", "financial_metrics.operating_cashflow", "financial_metrics.accounts_receivable", "financial_metrics.inventory"),
                "path_policy": "fallback",
                "status": "not_assessable",
                "missing_evidence": ["multi-period revenue trend", "cash-conversion trend", "receivable trend", "inventory trend", "customer / order bridge"],
                "not_assessable_reason": "Single-period revenue and operating cash-flow observations cannot establish multi-period stability.",
                "interpretation_guard": "Single-period revenue plus same-direction operating cash flow is only a financial observation, not multi-period stability evidence.",
                "research_question": "Is revenue growth supported by cash collection, receivables / inventory discipline, customer / order evidence, and stable business mix rather than one-period movement?",
            },
            {
                "layer": "financial",
                "driver_factor": "gross margin stability",
                "driver_scope": "financial quality",
                "why_it_matters": "Gross-margin stability requires multi-period margin and product price / cost / volume evidence.",
                "required_evidence": ["multi-period gross margin", "segment margin", "product mix", "price / cost / volume", "cost pass-through"],
                "checked_paths": ("business_composition", "financial_metrics.gross_margin", "financial_metrics.revenue"),
                "path_policy": "fallback",
                "status": "not_assessable",
                "missing_evidence": ["multi-period margin series", "product cost", "price / volume", "mix shift", "cost pass-through terms"],
                "not_assessable_reason": "Only current-period margin observations are available.",
                "interpretation_guard": "Do not infer product advantage or pricing power from one-period margin.",
                "research_question": "Is gross margin stable because of product mix, pricing, cost control, or temporary factors, and what multi-period evidence separates them?",
            },
            {
                "layer": "financial",
                "driver_factor": "net margin stability",
                "driver_scope": "financial quality",
                "why_it_matters": "Net-margin stability needs expense, tax, one-off item, and multi-period evidence.",
                "required_evidence": ["multi-period net margin", "expense ratio", "tax", "non-recurring items", "impairment", "interest expense"],
                "checked_paths": ("financial_metrics.net_margin", "financial_metrics.net_profit", "financial_metrics.deducted_net_profit", "financial_metrics.operating_cashflow"),
                "path_policy": "fallback",
                "status": "not_assessable",
                "missing_evidence": ["expense breakdown", "tax bridge", "impairment detail", "non-recurring item bridge", "multi-period trend"],
                "not_assessable_reason": "Net margin and profit fields are current-period observations without full expense and one-off bridge.",
                "interpretation_guard": "Do not treat one-period net margin as durable profitability.",
                "research_question": "Does net margin come from operating quality rather than expense timing, subsidy, disposal gain, impairment reversal, or tax effects?",
            },
            {
                "layer": "financial",
                "driver_factor": "operating cash flow conversion",
                "driver_scope": "financial quality",
                "why_it_matters": "Cash conversion requires multi-period conversion, receivables, inventory, payables, and customer payment terms.",
                "required_evidence": ["operating cash flow", "revenue", "net profit", "receivables", "inventory", "payables", "multi-period conversion"],
                "checked_paths": ("financial_metrics.operating_cashflow", "financial_metrics.revenue", "financial_metrics.net_profit", "financial_metrics.accounts_receivable", "financial_metrics.inventory"),
                "path_policy": "fallback",
                "status": "not_assessable",
                "missing_evidence": ["payables", "cash conversion cycle", "customer terms", "multi-period operating cash-flow conversion"],
                "not_assessable_reason": "Single-period operating cash flow is not long-term cash-flow stability.",
                "interpretation_guard": "Single-period operating cash-flow improvement or weakness is not long-term cash-flow stability.",
                "research_question": "Does operating cash flow validate revenue and profit quality after receivables, inventory, payables, and customer payment terms?",
            },
            {
                "layer": "financial",
                "driver_factor": "accounts receivable / collection quality",
                "driver_scope": "financial quality",
                "why_it_matters": "Collection quality needs aging, overdue, bad-debt, DSO, customer receivable, and payment-term evidence.",
                "required_evidence": ["receivables", "receivable aging", "overdue amount", "bad-debt provision", "DSO", "customer mix"],
                "checked_paths": ("financial_metrics.accounts_receivable", "financial_metrics.revenue", "financial_metrics.operating_cashflow"),
                "path_policy": "fallback",
                "status": "missing",
                "missing_evidence": ["receivable aging", "overdue receivables", "bad-debt provision", "DSO trend", "customer-specific receivables"],
                "not_assessable_reason": "Aggregate receivables are available, but aging, overdue, provision, DSO, and customer data are absent.",
                "interpretation_guard": "Receivable growth is not high-quality revenue and may signal collection risk.",
                "research_question": "What receivable aging, overdue, bad-debt provision, DSO, customer receivable, and payment-term evidence is needed to assess collection quality?",
            },
            {
                "layer": "financial",
                "driver_factor": "inventory / working-capital discipline",
                "driver_scope": "financial quality",
                "why_it_matters": "Inventory discipline requires product inventory split, aging, write-down, turnover, payables, and sales bridge.",
                "required_evidence": ["inventory", "revenue", "inventory breakdown", "aging", "write-down", "turnover", "product sales bridge"],
                "checked_paths": ("financial_metrics.inventory", "financial_metrics.revenue", "financial_metrics.operating_cashflow", "financial_metrics.accounts_receivable"),
                "path_policy": "financial_observation",
                "missing_evidence": ["inventory breakdown", "aging", "write-down", "turnover", "payables", "product sales bridge"],
                "interpretation_guard": "Inventory build or decline is not direct demand proof without sales and product bridge.",
                "research_question": "Does inventory reflect working-capital timing, demand mismatch, production timing, or cost movement, and what product sales bridge is missing?",
            },
            {
                "layer": "financial",
                "driver_factor": "free cash flow",
                "driver_scope": "financial quality",
                "why_it_matters": "Derived free cash flow is only an observation unless capex split, working capital, debt service, and multi-period support exist.",
                "required_evidence": ["operating cash flow", "capex", "maintenance vs expansion capex", "working capital", "debt service", "multi-period free cash flow"],
                "checked_paths": ("financial_metrics.operating_cashflow", "financial_metrics.capex", "financial_metrics.accounts_receivable", "financial_metrics.inventory", "financial_metrics.debt_to_asset"),
                "path_policy": "financial_observation",
                "missing_evidence": ["maintenance vs expansion capex split", "working-capital detail", "debt service", "multi-period free-cash-flow trend"],
                "interpretation_guard": "operating_cashflow - capex is a derived observation only; it is not shareholder-return capacity without capex, debt, and earnings-quality support.",
                "research_question": "Is derived free cash flow repeatable after maintenance capex, working-capital needs, and debt service, or only a one-period observation?",
            },
            {
                "layer": "financial",
                "driver_factor": "ROE / ROIC stability",
                "driver_scope": "financial quality",
                "why_it_matters": "Return quality requires multi-period ROE / ROIC, DuPont drivers, leverage, asset turnover, margin, and one-off adjustments.",
                "required_evidence": ["multi-period ROE", "ROIC", "DuPont drivers", "invested capital", "leverage", "one-off adjustments"],
                "checked_paths": ("financial_metrics.roe", "financial_metrics.net_margin", "financial_metrics.revenue", "financial_metrics.debt_to_asset", "financial_metrics.net_profit", "financial_metrics.deducted_net_profit"),
                "path_policy": "fallback",
                "status": "not_assessable",
                "missing_evidence": ["ROIC", "invested capital", "multi-period return series", "DuPont components", "one-off adjustments"],
                "not_assessable_reason": "Only single-period ROE and related financial fields are available.",
                "interpretation_guard": "Single-period high ROE is a current return observation only, not long-term competitiveness.",
                "research_question": "Are ROE and ROIC stable because of operating return quality rather than leverage, one-off profit, or accounting effects?",
            },
            {
                "layer": "financial",
                "driver_factor": "debt / liquidity / interest burden",
                "driver_scope": "financial quality",
                "why_it_matters": "Financing resilience requires debt, liquidity, interest expense, maturity, covenants, and cash-flow evidence.",
                "required_evidence": ["debt amount", "cash", "interest expense", "debt maturity", "interest coverage", "liquidity", "operating cash flow"],
                "checked_paths": ("financial_metrics.debt_to_asset", "financial_metrics.operating_cashflow", "financial_metrics.capex"),
                "path_policy": "financial_observation",
                "missing_evidence": ["cash / liquidity field", "interest expense", "debt maturity", "restricted cash", "covenants", "refinancing schedule"],
                "interpretation_guard": "Do not infer balance-sheet resilience without debt, liquidity, maturity, interest, and cash-flow evidence.",
                "research_question": "Can the balance sheet support operations, capex, and shareholder-return decisions through a downturn, and which liquidity / maturity evidence is missing?",
            },
            {
                "layer": "financial",
                "driver_factor": "capex discipline: maintenance vs expansion",
                "driver_scope": "financial quality",
                "why_it_matters": "Capex discipline requires maintenance vs expansion split, project mapping, utilization, and revenue / cash-flow bridge.",
                "required_evidence": ["capex total", "maintenance capex", "expansion capex", "project mapping", "utilization", "revenue / cash-flow bridge"],
                "checked_paths": ("financial_metrics.capex", "financial_metrics.revenue", "financial_metrics.operating_cashflow"),
                "path_policy": "fallback",
                "status": "missing",
                "missing_evidence": ["maintenance capex", "expansion capex", "project list", "acceptance", "utilization", "revenue bridge"],
                "not_assessable_reason": "Aggregate capex is available, but maintenance / expansion split and project bridge are absent.",
                "interpretation_guard": "Aggregate capex is cash outflow only; it is not capacity release, utilization, future revenue, or growth conversion.",
                "research_question": "Is capex maintaining existing earnings power, expanding capacity, or consuming cash without visible project, utilization, revenue, and cash-flow bridge?",
            },
            {
                "layer": "company",
                "driver_factor": "dividend capacity",
                "driver_scope": "shareholder-return / durability",
                "why_it_matters": "Dividend capacity needs dividend fields plus repeatable FCF, debt, capex, working-capital, and earnings-quality support.",
                "required_evidence": ["dividend amount", "operating cash flow", "free cash flow", "capex split", "debt / liquidity", "profit quality"],
                "checked_paths": ("financial_metrics.operating_cashflow", "financial_metrics.capex", "financial_metrics.debt_to_asset", "financial_metrics.net_profit", "financial_metrics.deducted_net_profit"),
                "path_policy": "dividend_missing",
                "missing_evidence": ["dividend amount / history", "payout ratio", "free-cash-flow coverage", "debt maturity", "capex plan", "capital-allocation policy"],
                "not_assessable_reason": "Dividend / payout fields are absent from financial_metrics, and support legs are incomplete.",
                "interpretation_guard": "Do not write dividend capacity as sustainable shareholder return without free cash flow, debt, capex, and earnings-quality support.",
                "research_question": "Are dividend amount or history fields present, and are they covered by repeatable free cash flow, debt capacity, capex needs, and earnings quality?",
            },
            {
                "layer": "company",
                "driver_factor": "payout sustainability",
                "driver_scope": "shareholder-return / durability",
                "why_it_matters": "Payout sustainability requires payout history, FCF coverage, debt maturity, capex commitments, and policy evidence.",
                "required_evidence": ["payout ratio", "earnings quality", "free cash flow", "capex needs", "debt maturity", "management policy"],
                "checked_paths": ("financial_metrics.net_profit", "financial_metrics.operating_cashflow", "financial_metrics.capex", "financial_metrics.debt_to_asset"),
                "path_policy": "dividend_missing",
                "missing_evidence": ["payout ratio history", "dividend policy", "repurchase history", "capex commitments", "debt maturity"],
                "not_assessable_reason": "Payout fields and multi-period coverage evidence are absent.",
                "interpretation_guard": "Payout ratio is not shareholder-return quality by itself.",
                "research_question": "What payout policy, payout history, FCF coverage, debt maturity, and capex commitment evidence is missing before sustainability can be assessed?",
            },
            {
                "layer": "company",
                "driver_factor": "earnings quality",
                "driver_scope": "shareholder-return / durability",
                "why_it_matters": "Earnings quality needs cash conversion, non-recurring item detail, impairment, subsidy, disposal gain, and multi-period bridge.",
                "required_evidence": ["net profit", "deducted net profit", "cash conversion", "non-recurring items", "impairment", "subsidy", "receivables"],
                "checked_paths": ("financial_metrics.net_profit", "financial_metrics.deducted_net_profit", "financial_metrics.operating_cashflow", "financial_metrics.accounts_receivable"),
                "path_policy": "financial_observation",
                "missing_evidence": ["non-recurring item detail", "impairment", "subsidy split", "asset-disposal gains", "multi-period bridge"],
                "interpretation_guard": "Profit growth is not earnings quality without cash-flow and one-off item checks.",
                "research_question": "Are earnings supported by operating profit and cash conversion rather than one-off gains or accounting items?",
            },
            {
                "layer": "company",
                "driver_factor": "balance-sheet resilience",
                "driver_scope": "shareholder-return / durability",
                "why_it_matters": "Resilience requires debt, cash, liquidity, maturity, obligations, capex commitments, and working-capital stress evidence.",
                "required_evidence": ["debt", "cash", "liquidity", "maturity", "capex commitments", "off-balance-sheet obligations"],
                "checked_paths": ("financial_metrics.debt_to_asset", "financial_metrics.operating_cashflow", "financial_metrics.accounts_receivable", "financial_metrics.inventory", "financial_metrics.capex"),
                "path_policy": "fallback",
                "status": "not_assessable",
                "missing_evidence": ["cash / liquidity detail", "debt maturity", "restricted cash", "covenants", "off-balance commitments"],
                "not_assessable_reason": "Debt-to-asset and working-capital fields are observations only; liquidity and maturity detail is incomplete.",
                "interpretation_guard": "Low apparent leverage is not resilience if maturity, liquidity, and obligations are missing.",
                "research_question": "Can the balance sheet absorb weaker demand, collection delays, or capex pressure, and what maturity / liquidity evidence is missing?",
            },
            {
                "layer": "company",
                "driver_factor": "cyclicality / downturn resilience",
                "driver_scope": "shareholder-return / durability",
                "why_it_matters": "Downturn resilience requires multi-period performance through weak periods plus customer, pricing, order, and working-capital evidence.",
                "required_evidence": ["downturn-period revenue", "downturn-period margin", "downturn-period cash flow", "customer retention", "stress-period collection"],
                "checked_paths": ("financial_metrics.revenue", "financial_metrics.gross_margin", "financial_metrics.operating_cashflow", "financial_metrics.accounts_receivable", "financial_metrics.capex"),
                "path_policy": "fallback",
                "status": "not_assessable",
                "missing_evidence": ["downturn-period series", "customer retention through downturn", "price / volume through downturn", "order cancellation", "stress-period collection"],
                "not_assessable_reason": "Current evidence pack lacks downturn-period and multi-period stability evidence.",
                "interpretation_guard": "The stable_growth label is not downturn resilience without multi-period evidence.",
                "research_question": "How did revenue, margin, cash flow, receivables, and capex behave during weak demand periods?",
            },
            {
                "layer": "company",
                "driver_factor": "one-off profit / non-recurring item risk",
                "driver_scope": "shareholder-return / durability",
                "why_it_matters": "Net profit vs deducted net profit is a minimum one-off proxy but does not replace detailed non-recurring item notes.",
                "required_evidence": ["net profit", "deducted net profit", "asset disposal", "subsidy", "fair-value gain", "impairment", "tax effects"],
                "checked_paths": ("financial_metrics.net_profit", "financial_metrics.deducted_net_profit", "financial_metrics.operating_cashflow"),
                "path_policy": "financial_observation",
                "missing_evidence": ["detailed non-recurring item note", "asset disposal", "subsidy", "impairment", "fair-value movements", "tax reconciliation"],
                "interpretation_guard": "Do not treat reported net profit as recurring earnings without non-recurring item checks.",
                "research_question": "How much of profit depends on non-recurring items, and does recurring operating profit support the observed earnings base?",
            },
            {
                "layer": "risk",
                "driver_factor": "revenue growth without cash-flow support",
                "driver_scope": "risk",
                "why_it_matters": "Revenue, OCF, receivables, and inventory must be read together as signals that may conflict.",
                "required_evidence": ["revenue growth", "operating cash flow", "receivables", "inventory", "payables", "customer payment terms", "multi-period trend"],
                "checked_paths": ("financial_metrics.revenue_yoy", "financial_metrics.operating_cashflow", "financial_metrics.accounts_receivable", "financial_metrics.inventory", "financial_metrics.revenue"),
                "path_policy": "financial_observation",
                "missing_evidence": ["payables", "customer terms", "cash conversion cycle", "multi-period trend", "customer / order bridge"],
                "force_cap": "low",
                "interpretation_guard": "Even if single-period revenue_yoy is positive and OCF moves in the same direction, do not combine them into a stability conclusion.",
                "research_question": "Do revenue growth, operating cash flow, receivables, inventory, customer terms, and order evidence show repeatable cash conversion or a working-capital conflict?",
            },
            {
                "layer": "risk",
                "driver_factor": "margin stability without product / pricing evidence",
                "driver_scope": "risk",
                "why_it_matters": "Margin stability is a risk question when product price, cost, volume, and renewal-pricing evidence are absent.",
                "required_evidence": ["gross margin", "net margin", "product price", "unit cost", "mix", "renewal pricing", "customer acceptance"],
                "checked_paths": ("business_composition", "financial_metrics.gross_margin", "financial_metrics.net_margin", "financial_metrics.revenue"),
                "path_policy": "segment_financial_observation",
                "missing_evidence": ["price / volume", "unit cost", "product mix detail", "pricing formula", "competitor pricing"],
                "interpretation_guard": "Margin stability does not prove pricing power or product advantage.",
                "research_question": "Does margin have product, pricing, cost, and mix support, or is it only an unexplained accounting observation?",
            },
            {
                "layer": "risk",
                "driver_factor": "receivables growth masking collection risk",
                "driver_scope": "risk",
                "why_it_matters": "Receivables can mask collection pressure when revenue or profit looks positive.",
                "required_evidence": ["receivables", "revenue", "operating cash flow", "aging", "overdue", "bad-debt provision", "customer concentration"],
                "checked_paths": ("financial_metrics.accounts_receivable", "financial_metrics.revenue", "financial_metrics.operating_cashflow"),
                "path_policy": "financial_observation",
                "missing_evidence": ["aging", "overdue", "bad-debt provision", "customer receivables", "DSO trend"],
                "force_cap": "low",
                "interpretation_guard": "Receivable growth is not revenue quality and may be a negative working-capital signal.",
                "research_question": "Do aggregate receivables and OCF raise a collection-risk question pending aging, overdue, provision, DSO, and customer-receivable evidence?",
            },
            {
                "layer": "risk",
                "driver_factor": "inventory build without sales bridge",
                "driver_scope": "risk",
                "why_it_matters": "Inventory risk needs product split, sales volume, production reconciliation, aging, write-down, and turnover evidence.",
                "required_evidence": ["inventory", "revenue", "sales volume", "product inventory split", "production / sales reconciliation", "write-downs"],
                "checked_paths": ("financial_metrics.inventory", "financial_metrics.revenue", "financial_metrics.operating_cashflow"),
                "path_policy": "financial_observation",
                "missing_evidence": ["product inventory", "sales volume", "production volume", "aging", "write-down", "turnover"],
                "force_cap": "low",
                "interpretation_guard": "Inventory build without sales bridge cannot be interpreted as future demand.",
                "research_question": "Is inventory tied to confirmed sales / delivery timing, or does missing product and sales bridge leave demand mismatch and write-down risk unresolved?",
            },
            {
                "layer": "risk",
                "driver_factor": "capex expansion without revenue / utilization bridge",
                "driver_scope": "risk",
                "why_it_matters": "Capex risk remains when project-level capex, acceptance, utilization, revenue contribution, and funding evidence are missing.",
                "required_evidence": ["capex", "project list", "maintenance vs expansion split", "acceptance", "utilization", "revenue contribution"],
                "checked_paths": ("financial_metrics.capex", "financial_metrics.revenue", "financial_metrics.operating_cashflow"),
                "path_policy": "financial_observation",
                "missing_evidence": ["project-level capex", "utilization", "acceptance", "revenue contribution", "funding source"],
                "force_cap": "low",
                "interpretation_guard": "Capex is cash outflow only; no capacity, utilization, or revenue conversion may be inferred.",
                "research_question": "Is expansion consuming cash before project mapping, acceptance, utilization, revenue contribution, and funding evidence are verified?",
            },
            {
                "layer": "risk",
                "driver_factor": "contract liabilities overread as backlog",
                "driver_scope": "risk",
                "why_it_matters": "This risk row prevents contract liabilities from being overread as signed orders or future revenue.",
                "required_evidence": ["contract liabilities", "true order table", "signed orders", "customer / order mapping", "revenue-recognition schedule"],
                "checked_paths": ("financial_metrics.contract_liabilities", "financial_metrics.revenue", "financial_metrics.operating_cashflow"),
                "path_policy": "contract_liability_proxy",
                "missing_evidence": ["true order table", "signed orders", "customer mapping", "delivery / cancellation evidence", "revenue-recognition schedule"],
                "force_cap": "low",
                "interpretation_guard": "Contract liabilities are partial proxy only and must not be written as backlog or confirmed future revenue.",
                "research_question": "What true order table, signed-order, customer mapping, delivery / cancellation, and revenue-recognition evidence prevents overreading contract liabilities?",
            },
            {
                "layer": "risk",
                "driver_factor": "dividend overread without free cash flow",
                "driver_scope": "risk",
                "why_it_matters": "Dividend or payout language is unsafe without dividend fields and support from FCF, debt, capex, liquidity, and earnings quality.",
                "required_evidence": ["dividend / payout", "operating cash flow", "capex", "free cash flow", "debt", "liquidity", "earnings quality"],
                "checked_paths": ("financial_metrics.operating_cashflow", "financial_metrics.capex", "financial_metrics.debt_to_asset", "financial_metrics.net_profit", "financial_metrics.deducted_net_profit"),
                "path_policy": "dividend_missing",
                "missing_evidence": ["dividend / payout history", "debt maturity", "capex split", "non-recurring items", "multi-period free-cash-flow trend"],
                "not_assessable_reason": "Dividend / payout fields are absent and support legs are incomplete.",
                "interpretation_guard": "Dividend or payout alone is not shareholder-return sustainability.",
                "research_question": "Could dividend or payout be overstated without dividend fields plus free cash flow, debt, capex, liquidity, and earnings-quality support?",
            },
            {
                "layer": "risk",
                "driver_factor": "stable label overread without multi-period evidence",
                "driver_scope": "risk",
                "why_it_matters": "The routing label must never become evidence of operating steadiness or stability.",
                "required_evidence": ["multi-period revenue", "multi-period margin", "multi-period cash flow", "ROE / ROIC trend", "customer evidence", "payout trend"],
                "checked_paths": ("stock.strategy_type", "financial_metrics.revenue", "financial_metrics.operating_cashflow", "business_composition"),
                "path_policy": "fallback",
                "status": "not_assessable",
                "missing_evidence": ["multi-period trend tables", "customer retention", "order visibility", "downturn performance"],
                "not_assessable_reason": "stable_growth is a routing label and current evidence lacks multi-period stability support.",
                "interpretation_guard": "stable_growth is a routing label, not evidence of stability.",
                "research_question": "What multi-period revenue, margin, cash-flow, ROE / ROIC, customer, order, and payout evidence is required before using stability as an analytical conclusion?",
            },
            {
                "layer": "financial",
                "driver_factor": "valuation explainability as evidence sufficiency only",
                "driver_scope": "valuation context",
                "why_it_matters": "Valuation metrics can frame evidence sufficiency only and cannot become valuation or transaction judgment.",
                "required_evidence": ["valuation metrics", "profit quality", "cash conversion", "segment evidence", "risk flags"],
                "checked_paths": ("valuation_metrics.pe_ttm", "valuation_metrics.pb", "valuation_metrics.ps", "valuation_metrics.market_cap", "financial_metrics.net_profit", "financial_metrics.operating_cashflow", "business_composition"),
                "path_policy": "valuation_context",
                "missing_evidence": ["forward earnings bridge", "multi-period cash conversion", "segment quality history", "risk-adjusted operating evidence"],
                "force_cap": "low",
                "interpretation_guard": "Valuation metrics are evidence-sufficiency context only and must not become valuation level, price, upside, or transaction framing.",
                "research_question": valuation_question,
            },
        ]

    def _build_stable_growth_driver(self, pack: dict[str, Any], payload: dict[str, Any]) -> DriverFactor:
        checked_paths = tuple(payload["checked_paths"])
        available = self._stable_growth_available_evidence(pack, checked_paths)
        missing = list(payload.get("missing_evidence") or self._missing_evidence(pack, tuple(payload["required_evidence"]), checked_paths))
        financial_nodes = [item for item in available if "evidence_pack.financial_metrics." in item]
        valuation_nodes = [item for item in available if "evidence_pack.valuation_metrics." in item]
        business_nodes = [item for item in available if "evidence_pack.business_composition" in item]
        contract_nodes = [item for item in financial_nodes if "financial_metrics.contract_liabilities=" in item]
        dividend_nodes = self._stable_growth_dividend_nodes(pack)

        path_policy = payload.get("path_policy", "fallback")
        path_nodes: list[str] = []
        status = payload.get("status")
        cap = payload.get("force_cap")
        reason = payload.get("not_assessable_reason", "")

        if path_policy == "segment_financial_observation":
            if business_nodes and financial_nodes:
                path_nodes = [business_nodes[0], *financial_nodes[:3]]
                status = status or "partial"
                cap = cap or "low"
                path = " -> ".join(path_nodes)
            elif financial_nodes:
                path_nodes = financial_nodes[:3]
                status = status or "partial"
                cap = cap or "low"
                path = " -> ".join(path_nodes)
                reason = reason or "Only aggregate financial fields are available; segment / customer / order bridge is missing."
            else:
                status = status or "not_assessable"
                cap = "not_assessable"
                path = TRANSMISSION_PATH_FALLBACK
                reason = reason or "No concrete segment or financial node is available."
        elif path_policy == "financial_observation":
            if financial_nodes:
                path_nodes = financial_nodes[:5]
                status = status or "partial"
                cap = cap or "low"
                path = " -> ".join(path_nodes)
            else:
                status = status or "not_assessable"
                cap = "not_assessable"
                path = TRANSMISSION_PATH_FALLBACK
                reason = reason or "Financial observation node is absent."
        elif path_policy == "contract_liability_proxy":
            if contract_nodes:
                path_nodes = [*contract_nodes[:1], *[node for node in financial_nodes if node not in contract_nodes][:2]]
                status = status or "partial"
                cap = cap or "low"
                path = " -> ".join(path_nodes)
            else:
                status = status or "missing"
                cap = "not_assessable"
                path = TRANSMISSION_PATH_FALLBACK
                reason = reason or "Contract liabilities field is absent."
        elif path_policy == "dividend_missing":
            if dividend_nodes:
                path_nodes = [*dividend_nodes[:1], *financial_nodes[:3]]
                status = status or "not_assessable"
                cap = cap or "not_assessable"
                path = TRANSMISSION_PATH_FALLBACK
                reason = reason or "Dividend / payout fields exist but free cash flow, debt, capex, and earnings-quality support is incomplete."
            else:
                status = status or "missing"
                cap = "not_assessable"
                path = TRANSMISSION_PATH_FALLBACK
                reason = reason or "Dividend / payout fields are absent from financial_metrics."
        elif path_policy == "valuation_context":
            path_nodes = [*valuation_nodes[:2], *financial_nodes[:2], *business_nodes[:1]]
            if path_nodes:
                status = status or "partial"
                cap = cap or "low"
                path = " -> ".join(path_nodes)
            else:
                status = status or "not_assessable"
                cap = "not_assessable"
                path = TRANSMISSION_PATH_FALLBACK
                reason = reason or "Valuation context fields are absent."
        else:
            status = status or "not_assessable"
            cap = "not_assessable"
            path = TRANSMISSION_PATH_FALLBACK
            reason = reason or GENERIC_MISSING_BRIDGE_REASON

        if path == TRANSMISSION_PATH_FALLBACK:
            cap = "not_assessable"
            path_nodes = []

        return DriverFactor(
            layer=payload["layer"],
            driver_factor=payload["driver_factor"],
            driver_scope=payload["driver_scope"],
            why_it_matters=payload["why_it_matters"],
            required_evidence=list(payload["required_evidence"]),
            available_evidence=available,
            missing_evidence=missing,
            company_transmission_path=path,
            data_availability_status=status,
            confidence_cap=cap,
            not_assessable_reason=reason,
            what_was_checked=list(checked_paths),
            source_refs=[item.split("=")[0] for item in path_nodes],
            research_question=payload["research_question"],
            interpretation_guard=payload["interpretation_guard"],
        )

    def _stable_growth_available_evidence(self, pack: dict[str, Any], checked_paths: tuple[str, ...]) -> list[str]:
        available: list[str] = []
        for path in checked_paths:
            if path == "business_composition":
                available.extend(self._stable_growth_business_segment_nodes(pack))
            elif path in {"basic_info.industry", "basic_info.main_business", "stock.strategy_type"}:
                value = self._value_at_path(pack, path)
                if _is_present(value):
                    available.append(f"evidence_pack.{path}={_safe_text(_display_value(value))}")
            elif path in {"missing_fields", "unknown_or_missing_evidence", "risk_flags", "data_limitations"}:
                continue
            else:
                value = self._value_at_path(pack, path)
                if _is_present(value):
                    available.append(f"evidence_pack.{path}={_safe_text(_display_value(value))}")
        return available

    def _stable_growth_business_segment_nodes(self, pack: dict[str, Any]) -> list[str]:
        nodes: list[str] = []
        for index, row in enumerate(_as_list(pack.get("business_composition"))):
            if not isinstance(row, dict):
                continue
            name = row.get("segment_name")
            if not name:
                continue
            bits = [f"segment_name:{name}"]
            revenue = row.get("revenue")
            ratio = row.get("revenue_ratio")
            margin = row.get("gross_margin")
            period = row.get("period")
            if _is_present(revenue):
                bits.append(f"revenue:{_display_value(revenue)}")
            if _is_present(ratio):
                bits.append(f"revenue_ratio:{_display_value(ratio)}")
            if _is_present(margin):
                bits.append(f"gross_margin:{_display_value(margin)}")
            if period:
                bits.append(f"period:{period}")
            nodes.append(f"evidence_pack.business_composition[{index}]={'; '.join(bits)}")
        return nodes[:12]

    def _stable_growth_dividend_nodes(self, pack: dict[str, Any]) -> list[str]:
        nodes: list[str] = []
        financial_metrics = pack.get("financial_metrics") if isinstance(pack.get("financial_metrics"), dict) else {}
        for key, value in financial_metrics.items():
            lowered = str(key).lower()
            if ("dividend" in lowered or "payout" in lowered) and _is_present(value):
                nodes.append(f"evidence_pack.financial_metrics.{key}={_safe_text(_display_value(value))}")
        return nodes

    def _advanced_manufacturing_drivers(self, pack: dict[str, Any]) -> list[DriverFactor]:
        return [self._build_advanced_manufacturing_driver(pack, payload) for payload in self._advanced_manufacturing_payloads()]

    def _advanced_manufacturing_payloads(self) -> list[dict[str, Any]]:
        return [
            {
                "layer": "industry",
                "driver_factor": "high-end manufacturing demand cycle",
                "driver_scope": "macro / industry / demand",
                "why_it_matters": "High-end manufacturing cycle context requires company segment, customer, order, shipment, margin, receivable, inventory, and cash-flow bridge before it can be assessed.",
                "required_evidence": ["end-market demand cycle", "company product exposure", "customer orders / shipments", "revenue / margin / receivable / cash-flow bridge"],
                "checked_paths": ("business_composition", "financial_metrics.revenue", "financial_metrics.gross_margin", "financial_metrics.operating_cashflow", "financial_metrics.accounts_receivable", "financial_metrics.inventory"),
                "path_policy": "fallback",
                "status": "not_assessable",
                "missing_evidence": ["industry demand series", "customer adoption", "product-level orders and shipments", "customer mix", "product-line price / volume"],
                "not_assessable_reason": "Demand-cycle context lacks customer, product, order, shipment, and cash-conversion bridge evidence.",
                "interpretation_guard": "High-end manufacturing demand is background only; do not infer company growth certainty from industry context.",
                "research_question": "Has high-end manufacturing demand translated into disclosed company product-line revenue, orders, shipments, receivables, inventory turnover, and operating cash flow?",
            },
            {
                "layer": "industry",
                "driver_factor": "automotive / EV / thermal-management demand",
                "driver_scope": "macro / industry / demand",
                "why_it_matters": "Automotive thermal-management exposure can be observed from its own segment node, but realized demand needs customer, program, delivery, revenue, margin, and collection evidence.",
                "required_evidence": ["EV / auto production demand", "automotive thermal-management segment", "customer program / order", "delivery / revenue / margin / collection bridge"],
                "checked_paths": ("business_composition", "financial_metrics.revenue", "financial_metrics.gross_margin", "financial_metrics.operating_cashflow", "financial_metrics.accounts_receivable"),
                "path_policy": "layer_exposure",
                "business_layer": "automotive",
                "missing_evidence": ["auto / EV demand by customer", "named customer orders", "program delivery schedule", "mass-production schedule", "collection data"],
                "interpretation_guard": "Automotive thermal-management segment exposure is not customer order visibility or realized EV demand by itself.",
                "research_question": "Which automotive thermal-management customers, products, programs, deliveries, revenue, margin, and collections support realized demand?",
            },
            {
                "layer": "industry",
                "driver_factor": "robotics / humanoid robotics theme exposure",
                "driver_scope": "macro / industry / demand",
                "why_it_matters": "Robotics theme exposure is high narrative-risk unless supported by independent robotics revenue, order, customer, mass-production, delivery, or collection evidence.",
                "required_evidence": ["robotics product description", "independent non-zero revenue split", "signed orders or customers", "mass-production delivery", "collection evidence"],
                "checked_paths": ("business_composition", "basic_info.main_business", "enhanced_must_track_indicators"),
                "path_policy": "robotics_strict",
                "missing_evidence": ["robotics revenue ratio", "robotics revenue amount", "robotics order amount", "robotics customer list", "mass-production delivery", "collection evidence"],
                "not_assessable_reason": "Robotics / actuator exposure lacks independent non-zero revenue, order, customer, mass-production, delivery, and collection evidence.",
                "interpretation_guard": "Robotics or humanoid robotics theme is not revenue realization; layout, narrative, and news are context only.",
                "research_question": "Is robotics exposure supported by disclosed non-zero revenue, orders, customers, mass-production deliveries, and cash collection, or only by narrative?",
            },
            {
                "layer": "industry",
                "driver_factor": "customer capex / product adoption cycle",
                "driver_scope": "macro / industry / demand",
                "why_it_matters": "Customer capex and product adoption plans matter only after they are mapped to company products, orders, shipments, revenue, receivables, and cash flow.",
                "required_evidence": ["customer capex or adoption plan", "company product mapping", "customer qualification / nomination / design-win", "accepted orders", "revenue and cash bridge"],
                "checked_paths": ("enhanced_must_track_indicators", "business_composition", "financial_metrics.revenue", "financial_metrics.operating_cashflow"),
                "path_policy": "fallback",
                "status": "not_assessable",
                "missing_evidence": ["customer capex by named customer", "product adoption schedule", "accepted orders", "shipment / acceptance", "revenue recognition"],
                "not_assessable_reason": "Customer capex or adoption evidence is not linked to company order, shipment, revenue, receivable, and cash-flow nodes.",
                "interpretation_guard": "Customer capex is not company revenue.",
                "research_question": "Which customer capex or adoption programs have converted into company orders, shipments, revenue, receivables, and cash flow?",
            },
            {
                "layer": "industry",
                "driver_factor": "localization / import substitution",
                "driver_scope": "macro / industry / demand",
                "why_it_matters": "Localization context requires localized product revenue, domestic customer adoption, accepted delivery, repeat order, and collection evidence.",
                "required_evidence": ["localized product revenue", "domestic customer adoption", "customer qualification", "batch order / accepted delivery", "collection evidence"],
                "checked_paths": ("business_composition", "enhanced_must_track_indicators", "financial_metrics.revenue"),
                "path_policy": "fallback",
                "status": "not_assessable",
                "missing_evidence": ["localization-specific revenue", "domestic customer list", "qualification result", "accepted order", "repeat delivery", "collection evidence"],
                "not_assessable_reason": "Localization / import-substitution evidence lacks revenue and customer adoption bridge.",
                "interpretation_guard": "Localization narrative is not realized revenue.",
                "research_question": "What revenue, customers, accepted orders, repeat deliveries, and collections prove localization conversion?",
            },
            {
                "layer": "industry",
                "driver_factor": "overseas customer / export exposure",
                "driver_scope": "macro / industry / demand",
                "why_it_matters": "Overseas exposure needs geography or export revenue, customer geography, FX, trade-risk, receivable, and cash-flow evidence.",
                "required_evidence": ["overseas revenue share", "customer geography", "export product mix", "FX exposure", "trade restriction impact", "receivable and cash bridge"],
                "checked_paths": ("business_composition.geography", "financial_metrics.revenue", "financial_metrics.accounts_receivable", "financial_metrics.operating_cashflow"),
                "path_policy": "geography_financial_observation",
                "missing_evidence": ["top customer geography", "FX gains / losses", "trade restriction mapping", "overseas receivable aging", "overseas collection cycle"],
                "interpretation_guard": "Overseas customer narrative is not exposure magnitude or realized risk without company-level evidence.",
                "research_question": "How much revenue and working capital is exposed to overseas customers, export markets, FX, and trade restrictions?",
            },
            {
                "layer": "company",
                "driver_factor": "core business revenue contribution",
                "driver_scope": "refrigeration / air-conditioning core business",
                "why_it_matters": "The refrigeration / air-conditioning layer is the traditional core exposure and must be kept separate from automotive and robotics evidence.",
                "required_evidence": ["core segment revenue", "core revenue ratio", "period", "gross margin", "total revenue bridge"],
                "checked_paths": ("business_composition", "financial_metrics.revenue", "financial_metrics.gross_margin"),
                "path_policy": "layer_exposure",
                "business_layer": "core",
                "missing_evidence": ["product-level core revenue", "volume", "price", "customer split"],
                "interpretation_guard": "Core-business exposure is not proof of cycle strength, pricing power, or robotics realization.",
                "research_question": "What share of revenue and gross margin comes from refrigeration / air-conditioning control components, and what product/customer detail is missing?",
            },
            {
                "layer": "company",
                "driver_factor": "automotive thermal-management business contribution",
                "driver_scope": "automotive thermal management",
                "why_it_matters": "The automotive layer needs its own segment and customer/program bridge and must not be merged with core refrigeration or robotics.",
                "required_evidence": ["automotive thermal-management segment revenue", "revenue ratio", "product definition", "gross margin", "customer / program bridge"],
                "checked_paths": ("business_composition", "financial_metrics.revenue", "financial_metrics.gross_margin", "financial_metrics.operating_cashflow"),
                "path_policy": "layer_exposure",
                "business_layer": "automotive",
                "missing_evidence": ["product-line revenue and gross margin", "customer programs", "mass-production schedule", "order visibility", "collection"],
                "interpretation_guard": "Automotive thermal-management exposure is not order visibility by itself.",
                "research_question": "What revenue, margin, customer, program, delivery, and collection evidence supports automotive thermal-management growth?",
            },
            {
                "layer": "company",
                "driver_factor": "new business / robotics / emerging business revenue split",
                "driver_scope": "robotics / actuator / emerging business",
                "why_it_matters": "New-business realization requires an independent non-zero robotics or emerging-business revenue node, not strategic-layout wording.",
                "required_evidence": ["robotics / emerging product revenue", "revenue ratio", "gross margin", "period", "total revenue bridge"],
                "checked_paths": ("business_composition", "basic_info.main_business", "enhanced_must_track_indicators"),
                "path_policy": "robotics_strict",
                "missing_evidence": ["robotics revenue split", "robotics gross margin", "order amount", "customer and production status"],
                "not_assessable_reason": "Robotics / emerging business lacks disclosed independent non-zero revenue split and orders.",
                "interpretation_guard": "Do not treat new-business narrative as revenue realization.",
                "research_question": "What disclosed non-zero revenue and gross margin, if any, comes from robotics or emerging businesses?",
            },
            {
                "layer": "company",
                "driver_factor": "product line revenue and gross margin",
                "driver_scope": "company / product line",
                "why_it_matters": "Product-line revenue and margin explain mix only when broad segment labels are not overread as product-level proof.",
                "required_evidence": ["product-line revenue", "revenue ratio", "gross margin", "period", "price / volume / cost bridge"],
                "checked_paths": ("business_composition", "financial_metrics.revenue", "financial_metrics.gross_margin"),
                "path_policy": "business_financial_observation",
                "missing_evidence": ["product-level revenue", "product-level gross margin", "price / volume / cost", "product mix history"],
                "interpretation_guard": "Broad segment labels are exposure nodes only; product mix or pricing conclusion requires product-level evidence.",
                "research_question": "Which product lines have disclosed revenue and gross margin, and what price, volume, cost, and mix details remain missing?",
            },
            {
                "layer": "company",
                "driver_factor": "customer order visibility",
                "driver_scope": "company / business",
                "why_it_matters": "Order visibility requires signed order, customer, delivery schedule, cancellation, shipment, revenue recognition, and collection evidence.",
                "required_evidence": ["signed orders", "customer identity", "delivery schedule", "shipment", "revenue recognition", "collection"],
                "checked_paths": ("enhanced_must_track_indicators", "financial_metrics.contract_liabilities", "financial_metrics.operating_cashflow"),
                "path_policy": "fallback",
                "status": "missing",
                "missing_evidence": ["signed orders", "customer / order table", "delivery schedule", "shipment", "revenue recognition", "collection"],
                "not_assessable_reason": "Signed-order and customer delivery evidence is absent; contract liabilities alone cannot establish order visibility.",
                "interpretation_guard": "Contract liabilities are partial proxy only; they are not backlog, customer order table, or confirmed delivery.",
                "research_question": "What signed-order, customer, delivery, shipment, revenue-recognition, and collection evidence supports order visibility?",
            },
            {
                "layer": "company",
                "driver_factor": "mass production / delivery evidence",
                "driver_scope": "company / business",
                "why_it_matters": "Mass production and delivery evidence must be separated from qualification or design-win status.",
                "required_evidence": ["SOP / mass-production start", "accepted shipment", "delivery volume", "revenue recognition", "collection"],
                "checked_paths": ("enhanced_must_track_indicators", "business_composition", "financial_metrics.revenue"),
                "path_policy": "fallback",
                "status": "missing",
                "missing_evidence": ["SOP / mass-production start", "accepted shipment", "delivery volume", "revenue recognition", "collection"],
                "not_assessable_reason": "Mass-production, accepted delivery, and collection evidence is absent.",
                "interpretation_guard": "Qualification, nomination, or design-win status is not batch revenue without shipment, accepted delivery, revenue recognition, and collection.",
                "research_question": "Is there SOP, accepted shipment, delivery volume, revenue recognition, and collection evidence distinct from qualification or design-win status?",
            },
            {
                "layer": "company",
                "driver_factor": "customer concentration / top customer exposure",
                "driver_scope": "company / business",
                "why_it_matters": "Customer concentration affects revenue visibility and collection risk only when customer share, receivable concentration, and payment terms are disclosed.",
                "required_evidence": ["top customer revenue share", "named customer order", "receivable concentration", "payment terms", "customer change"],
                "checked_paths": ("enhanced_must_track_indicators", "risk_flags", "financial_metrics.accounts_receivable"),
                "path_policy": "fallback",
                "status": "not_assessable",
                "missing_evidence": ["top-five customer revenue share", "named customer orders", "receivable concentration", "payment terms"],
                "not_assessable_reason": "Customer concentration fields are absent from the current evidence pack.",
                "interpretation_guard": "Named-customer or big-customer context is not concentration magnitude without disclosed share and collection evidence.",
                "research_question": "What top-customer revenue share, receivable concentration, payment terms, and customer-change evidence defines customer concentration risk?",
            },
            {
                "layer": "company",
                "driver_factor": "customer qualification / nomination / design-win status",
                "driver_scope": "company / business",
                "why_it_matters": "Customer entry status is useful only as stage evidence and must not be treated as batch revenue.",
                "required_evidence": ["qualification status", "nomination status", "design-win status", "conversion prerequisites", "shipment / collection bridge"],
                "checked_paths": ("enhanced_must_track_indicators", "unknown_or_missing_evidence"),
                "path_policy": "fallback",
                "status": "missing",
                "missing_evidence": ["qualification status", "nomination status", "design-win status", "shipment / accepted delivery", "revenue recognition", "collection"],
                "not_assessable_reason": "Qualification / nomination / design-win status fields are absent.",
                "interpretation_guard": "Qualification / nomination / design-win is not batch revenue unless shipment, accepted delivery, revenue recognition, and collection evidence exists.",
                "research_question": "What qualification, nomination, or design-win stage is disclosed, and what shipment, revenue-recognition, and collection prerequisites remain?",
            },
            {
                "layer": "financial",
                "driver_factor": "contract liabilities as partial proxy only",
                "driver_scope": "financial / order proxy",
                "why_it_matters": "Contract liabilities may observe prepayment-like visibility, but they do not identify backlog, customer, order, product line, or revenue schedule.",
                "required_evidence": ["contract liabilities", "prepayment terms", "linked customer / order / product line", "revenue-recognition schedule"],
                "checked_paths": ("financial_metrics.contract_liabilities", "financial_metrics.revenue", "financial_metrics.operating_cashflow"),
                "path_policy": "financial_observation",
                "missing_evidence": ["customer / order mapping", "product-line mapping", "revenue-recognition schedule", "cancellation terms"],
                "force_cap": "low",
                "interpretation_guard": "Contract liabilities are partial proxy only, not backlog or confirmed delivery.",
                "research_question": "What customer, order, product line, or revenue-recognition schedule explains contract liabilities without treating them as backlog?",
            },
            {
                "layer": "company",
                "driver_factor": "product mix upgrade",
                "driver_scope": "company / business",
                "why_it_matters": "Product mix upgrade requires product-level revenue, price, volume, cost, and gross-margin evidence beyond broad segment and aggregate margin.",
                "required_evidence": ["product mix history", "product-line revenue", "gross margin by product", "price / volume / cost", "customer adoption"],
                "checked_paths": ("business_composition", "financial_metrics.gross_margin", "financial_metrics.revenue"),
                "path_policy": "business_financial_observation",
                "missing_evidence": ["product mix history", "price / volume / cost", "customer adoption", "product-level margin bridge"],
                "interpretation_guard": "Gross margin movement cannot be attributed to product mix or pricing without product, price, cost, customer, and volume evidence.",
                "research_question": "What product-level evidence explains product mix upgrade, price, volume, cost, and gross-margin movement?",
            },
            {
                "layer": "financial",
                "driver_factor": "revenue growth quality",
                "driver_scope": "financial",
                "why_it_matters": "Revenue growth quality requires cash conversion, receivable aging, customer/order mapping, and segment bridge rather than revenue growth alone.",
                "required_evidence": ["revenue growth", "operating cash flow", "accounts receivable", "customer/order mapping", "collection bridge"],
                "checked_paths": ("business_composition", "financial_metrics.revenue", "financial_metrics.revenue_yoy", "financial_metrics.operating_cashflow", "financial_metrics.accounts_receivable"),
                "path_policy": "business_financial_observation",
                "missing_evidence": ["receivable aging", "customer payment terms", "customer/order mapping", "segment cash conversion"],
                "force_cap": "low",
                "interpretation_guard": "Receivable growth is not high-quality revenue; revenue growth needs collection and customer/order bridge.",
                "research_question": "Do revenue growth, operating cash flow, accounts receivable, and customer/order mapping support cash conversion, or do collection questions remain?",
            },
            {
                "layer": "financial",
                "driver_factor": "gross margin stability",
                "driver_scope": "financial",
                "why_it_matters": "Gross margin stability is an aggregate observation until product mix, price, cost, and customer evidence explains it.",
                "required_evidence": ["gross margin", "product mix", "price", "cost", "customer / volume bridge"],
                "checked_paths": ("business_composition", "financial_metrics.gross_margin", "financial_metrics.revenue"),
                "path_policy": "business_financial_observation",
                "missing_evidence": ["product mix", "price evidence", "cost detail", "customer / volume bridge"],
                "interpretation_guard": "Gross margin alone cannot identify product-mix upgrade, price competition, or technology advantage.",
                "research_question": "What product mix, pricing, cost, customer, and volume evidence explains gross-margin stability or pressure?",
            },
            {
                "layer": "financial",
                "driver_factor": "operating cash flow",
                "driver_scope": "financial",
                "why_it_matters": "Operating cash flow is a cash-conversion observation and needs receivable, inventory, order, and delivery bridge.",
                "required_evidence": ["operating cash flow", "revenue", "accounts receivable", "inventory", "delivery / collection bridge"],
                "checked_paths": ("financial_metrics.operating_cashflow", "financial_metrics.revenue", "financial_metrics.accounts_receivable", "financial_metrics.inventory"),
                "path_policy": "financial_observation",
                "missing_evidence": ["receivable aging", "inventory turnover", "delivery / collection bridge", "customer payment terms"],
                "force_cap": "low",
                "interpretation_guard": "Operating cash flow validates cash conversion only after collection and working-capital bridge are checked.",
                "research_question": "Does operating cash flow reconcile with revenue, receivables, inventory, delivery, and customer collection evidence?",
            },
            {
                "layer": "financial",
                "driver_factor": "accounts receivable / collection quality",
                "driver_scope": "financial",
                "why_it_matters": "Collection quality requires aging, overdue, payment terms, and customer concentration evidence; receivable amount alone is insufficient.",
                "required_evidence": ["accounts receivable", "receivable aging", "overdue receivables", "payment terms", "customer concentration"],
                "checked_paths": ("financial_metrics.accounts_receivable", "financial_metrics.revenue", "financial_metrics.operating_cashflow"),
                "path_policy": "financial_observation",
                "missing_evidence": ["receivable aging", "overdue receivables", "bad-debt provision", "customer-level payment terms", "customer concentration"],
                "force_cap": "low",
                "interpretation_guard": "Receivable growth must not be written as high-quality revenue; it is a collection-quality question.",
                "research_question": "What receivable aging, overdue, payment-term, bad-debt, and customer-concentration evidence explains collection quality?",
            },
            {
                "layer": "financial",
                "driver_factor": "inventory and production-sales bridge",
                "driver_scope": "financial",
                "why_it_matters": "Aggregate inventory is a working-capital observation and cannot be mapped to a single business layer or robotics demand.",
                "required_evidence": ["aggregate inventory", "product-level inventory split", "turnover", "production-sales reconciliation", "orders / shipments", "write-down detail"],
                "checked_paths": ("financial_metrics.inventory", "financial_metrics.revenue", "financial_metrics.operating_cashflow"),
                "path_policy": "financial_observation",
                "missing_evidence": ["product-level inventory split", "inventory turnover", "production-sales reconciliation", "orders", "shipments", "write-down evidence"],
                "force_cap": "low",
                "interpretation_guard": "Aggregate inventory must not be used to judge robotics or single-layer demand strength or weakness.",
                "research_question": "What product-level inventory split, turnover, production-sales bridge, orders, shipments, and write-down evidence explains inventory?",
            },
            {
                "layer": "financial",
                "driver_factor": "capex-to-revenue / capacity utilization bridge",
                "driver_scope": "financial",
                "why_it_matters": "Capex is cash outflow / investment observation unless mapped to project, acceptance, utilization, output, delivery, revenue, and cash flow.",
                "required_evidence": ["capex", "project mapping", "acceptance", "capacity utilization", "output / delivery", "revenue bridge", "cash-flow bridge"],
                "checked_paths": ("financial_metrics.capex", "financial_metrics.revenue", "financial_metrics.operating_cashflow"),
                "path_policy": "financial_observation",
                "missing_evidence": ["capex project mapping", "acceptance", "capacity utilization", "output / delivery", "revenue bridge"],
                "force_cap": "low",
                "interpretation_guard": "Capex is cash outflow / investment observation, not capacity release, mass production, utilization, or revenue conversion.",
                "research_question": "Which capex projects map to acceptance, utilization, output, delivery, revenue, and cash-flow evidence?",
            },
            {
                "layer": "financial",
                "driver_factor": "R&D expense as input evidence only",
                "driver_scope": "financial",
                "why_it_matters": "R&D expense and ratio are input evidence; product conversion, validation, reliability, orders, revenue, and margin are separate proof points.",
                "required_evidence": ["R&D expense", "R&D ratio", "product conversion", "customer validation", "order revenue", "margin contribution"],
                "checked_paths": ("financial_metrics.r_and_d_expense", "financial_metrics.r_and_d_expense_ratio", "financial_metrics.revenue"),
                "path_policy": "financial_observation",
                "missing_evidence": ["R&D project milestones", "product conversion", "customer validation", "order revenue", "margin contribution"],
                "force_cap": "low",
                "interpretation_guard": "R&D expense / ratio is input evidence only and is not proof of product competitiveness, reliability, customer stickiness, or commercialization.",
                "research_question": "Which R&D projects converted into validated products, customer adoption, orders, revenue, and margin contribution?",
            },
            {
                "layer": "financial",
                "driver_factor": "free cash flow / working-capital pressure",
                "driver_scope": "financial",
                "why_it_matters": "Free cash flow and working-capital pressure need operating cash flow, capex, receivables, inventory, and payables bridge.",
                "required_evidence": ["operating cash flow", "capex", "accounts receivable", "inventory", "working-capital bridge"],
                "checked_paths": ("financial_metrics.operating_cashflow", "financial_metrics.capex", "financial_metrics.accounts_receivable", "financial_metrics.inventory"),
                "path_policy": "financial_observation",
                "missing_evidence": ["free cash flow calculation", "working-capital bridge", "payables detail", "customer payment terms"],
                "force_cap": "low",
                "interpretation_guard": "Working-capital movement is not demand proof; it requires receivable, inventory, payable, order, and shipment bridge.",
                "research_question": "How do operating cash flow, capex, receivables, inventory, and payables explain free cash flow and working-capital pressure?",
            },
            {
                "layer": "financial",
                "driver_factor": "valuation explainability as evidence sufficiency only",
                "driver_scope": "financial / valuation context",
                "why_it_matters": "Valuation metrics can only frame evidence sufficiency questions and must not become a valuation judgment or trading output.",
                "required_evidence": ["valuation metrics", "profit growth", "gross margin stability", "cash-flow conversion", "new-business realization evidence"],
                "checked_paths": ("valuation_metrics", "financial_metrics.revenue", "financial_metrics.gross_margin", "financial_metrics.operating_cashflow", "business_composition"),
                "path_policy": "valuation_context",
                "missing_evidence": ["profit growth bridge", "gross-margin explanation", "cash-flow conversion", "automotive customer/program evidence", "robotics revenue/order evidence"],
                "force_cap": "low",
                "interpretation_guard": "Valuation metrics are evidence sufficiency context only; do not output valuation judgment, price support, target, or trade action.",
                "research_question": "当前 evidence pack 中哪些证据足以支撑或解释当前估值背景，哪些证据仍缺失？",
            },
            {
                "layer": "risk",
                "driver_factor": "new business narrative without revenue",
                "driver_scope": "risk",
                "why_it_matters": "New-business narrative is a risk when revenue split, order, customer, production, delivery, and collection evidence is missing.",
                "required_evidence": ["new business revenue", "orders", "customers", "production / delivery", "collection"],
                "checked_paths": ("business_composition", "basic_info.main_business", "enhanced_must_track_indicators"),
                "path_policy": "robotics_strict",
                "missing_evidence": ["independent new-business revenue", "orders", "customers", "production / delivery", "collection"],
                "not_assessable_reason": "New-business / robotics realization evidence is missing; narrative cannot be a valid node.",
                "interpretation_guard": "Strategic layout, cooperation, or R&D wording is context only, not operating fact.",
                "research_question": "Which independent revenue, order, customer, production, delivery, or collection evidence would turn new-business narrative into operating fact?",
            },
            {
                "layer": "risk",
                "driver_factor": "robotics theme without order / customer / mass-production evidence",
                "driver_scope": "risk",
                "why_it_matters": "Robotics theme must remain not assessable without direct operating evidence.",
                "required_evidence": ["robotics order", "robotics customer", "mass-production delivery", "accepted shipment", "collection"],
                "checked_paths": ("business_composition", "basic_info.main_business", "enhanced_must_track_indicators"),
                "path_policy": "robotics_strict",
                "missing_evidence": ["robotics order", "robotics customer", "mass-production delivery", "accepted shipment", "collection"],
                "not_assessable_reason": "Robotics order, customer, mass-production, shipment, and collection evidence is absent.",
                "interpretation_guard": "Robotics theme exposure is not company realization and must not use refrigeration or automotive financial data as proxy.",
                "research_question": "What direct robotics order, customer, mass-production, accepted shipment, and collection evidence exists beyond narrative context?",
            },
            {
                "layer": "risk",
                "driver_factor": "customer concentration risk",
                "driver_scope": "risk",
                "why_it_matters": "Customer concentration risk requires top-customer share, receivable concentration, payment terms, and customer-change evidence.",
                "required_evidence": ["top customer share", "receivable concentration", "payment terms", "customer changes", "order dependency"],
                "checked_paths": ("enhanced_must_track_indicators", "risk_flags", "financial_metrics.accounts_receivable"),
                "path_policy": "fallback",
                "status": "not_assessable",
                "missing_evidence": ["top customer share", "receivable concentration", "payment terms", "customer changes"],
                "not_assessable_reason": "Customer concentration fields are missing.",
                "interpretation_guard": "Customer concentration cannot be inferred from customer rumors or aggregate receivables.",
                "research_question": "What top-customer share, payment terms, receivable concentration, and customer-change evidence defines concentration risk?",
            },
            {
                "layer": "risk",
                "driver_factor": "receivables / collection deterioration",
                "driver_scope": "risk",
                "why_it_matters": "Deterioration risk is distinct from neutral collection-quality checking and needs aging, overdue, provisions, and customer evidence.",
                "required_evidence": ["receivable aging", "overdue receivables", "bad-debt provision", "customer payment terms", "operating cash flow"],
                "checked_paths": ("financial_metrics.accounts_receivable", "financial_metrics.operating_cashflow", "financial_metrics.revenue"),
                "path_policy": "financial_observation",
                "missing_evidence": ["receivable aging", "overdue receivables", "bad-debt provision", "customer payment terms"],
                "force_cap": "low",
                "interpretation_guard": "Receivables deterioration cannot be concluded from receivable amount alone; use it as a risk question.",
                "research_question": "Do receivable aging, overdue balances, provisions, customer payment terms, and operating cash flow indicate collection deterioration?",
            },
            {
                "layer": "risk",
                "driver_factor": "inventory build without demand bridge",
                "driver_scope": "risk",
                "why_it_matters": "Inventory risk needs product split, turnover, production-sales reconciliation, orders, shipments, and write-down evidence.",
                "required_evidence": ["product inventory split", "turnover", "production-sales reconciliation", "orders", "shipments", "write-down evidence"],
                "checked_paths": ("financial_metrics.inventory", "financial_metrics.revenue", "financial_metrics.operating_cashflow"),
                "path_policy": "financial_observation",
                "missing_evidence": ["product inventory split", "turnover", "production-sales reconciliation", "orders", "shipments", "write-down evidence"],
                "force_cap": "low",
                "interpretation_guard": "Inventory growth or decline must not be used to judge demand strength or weakness, especially for robotics.",
                "research_question": "What product-level inventory split, turnover, production-sales reconciliation, orders, shipments, and write-down evidence explains inventory risk?",
            },
            {
                "layer": "risk",
                "driver_factor": "capex without utilization / revenue bridge",
                "driver_scope": "risk",
                "why_it_matters": "Capex execution risk remains when project mapping, acceptance, utilization, output, delivery, revenue, and cash-flow bridge are missing.",
                "required_evidence": ["capex", "project mapping", "acceptance", "utilization", "output / delivery", "revenue bridge"],
                "checked_paths": ("financial_metrics.capex", "financial_metrics.revenue", "financial_metrics.operating_cashflow"),
                "path_policy": "financial_observation",
                "missing_evidence": ["project mapping", "acceptance", "utilization", "output / delivery", "revenue bridge"],
                "force_cap": "low",
                "interpretation_guard": "Capex is not capacity release, mass production, utilization, or revenue conversion.",
                "research_question": "Could capex remain unverified because project mapping, acceptance, utilization, output, delivery, revenue, and cash-flow evidence are missing?",
            },
            {
                "layer": "risk",
                "driver_factor": "gross margin pressure from product mix or price competition",
                "driver_scope": "risk",
                "why_it_matters": "Margin pressure needs product mix, pricing, cost, competition, customer, and volume evidence.",
                "required_evidence": ["gross margin", "product mix", "pricing", "cost", "competition", "customer / volume bridge"],
                "checked_paths": ("business_composition", "financial_metrics.gross_margin", "financial_metrics.revenue"),
                "path_policy": "business_financial_observation",
                "missing_evidence": ["product mix", "pricing", "cost detail", "competition evidence", "customer / volume bridge"],
                "interpretation_guard": "Do not attribute gross margin pressure to product mix or price competition without product, price, cost, customer, and volume evidence.",
                "research_question": "Is gross-margin pressure tied to product mix, price competition, cost, customer, or volume, and what evidence supports that link?",
            },
            {
                "layer": "risk",
                "driver_factor": "overseas customer / FX / trade risk",
                "driver_scope": "risk",
                "why_it_matters": "Overseas, FX, and trade risk need geography, customer, currency, trade event, receivable, and cash-flow mapping.",
                "required_evidence": ["overseas revenue share", "customer geography", "FX gains / losses", "trade event", "overseas receivable / cash bridge"],
                "checked_paths": ("business_composition.geography", "financial_metrics.accounts_receivable", "financial_metrics.operating_cashflow"),
                "path_policy": "geography_financial_observation",
                "missing_evidence": ["customer geography", "FX gains / losses", "trade restriction mapping", "overseas receivable aging"],
                "interpretation_guard": "Overseas exposure is not realized FX or trade impact without company-level mapping.",
                "research_question": "Which overseas customers, currencies, trade events, receivables, and cash flows define overseas / FX / trade risk?",
            },
            {
                "layer": "risk",
                "driver_factor": "product qualification or mass-production delay",
                "driver_scope": "risk",
                "why_it_matters": "Qualification or mass-production delay risk cannot be inferred without stage, timeline, customer, shipment, and revenue impact evidence.",
                "required_evidence": ["qualification stage", "mass-production timeline", "delay disclosure", "customer impact", "shipment / revenue impact"],
                "checked_paths": ("enhanced_must_track_indicators", "risk_flags", "unknown_or_missing_evidence"),
                "path_policy": "fallback",
                "status": "missing",
                "missing_evidence": ["qualification stage", "mass-production timeline", "delay disclosure", "customer impact", "shipment / revenue impact"],
                "not_assessable_reason": "Qualification, mass-production timeline, and delay evidence is absent.",
                "interpretation_guard": "Do not infer qualification success, delay, or batch revenue from missing data.",
                "research_question": "What qualification stage, mass-production timeline, delay disclosure, customer impact, shipment, and revenue evidence would reveal delay risk?",
            },
            {
                "layer": "risk",
                "driver_factor": "revenue growth / cash-flow / receivable signal consistency",
                "driver_scope": "risk / contradiction",
                "why_it_matters": "Revenue, operating cash flow, and accounts receivable must be listed together when cash-conversion signals could conflict.",
                "required_evidence": ["revenue growth", "operating cash flow", "accounts receivable", "customer/order mapping", "receivable aging"],
                "checked_paths": ("financial_metrics.revenue_yoy", "financial_metrics.operating_cashflow", "financial_metrics.accounts_receivable", "financial_metrics.revenue"),
                "path_policy": "financial_observation",
                "missing_evidence": ["customer/order mapping", "receivable aging", "payment terms", "segment cash conversion"],
                "force_cap": "low",
                "interpretation_guard": "If revenue growth, operating cash flow, or accounts receivable point in different directions, list all signals and require manual review.",
                "research_question": "Do revenue growth, operating cash flow, accounts receivable, customer/order mapping, and receivable aging point to consistent cash conversion, or require manual review?",
            },
        ]

    def _build_advanced_manufacturing_driver(self, pack: dict[str, Any], payload: dict[str, Any]) -> DriverFactor:
        checked_paths = tuple(payload["checked_paths"])
        available = self._advanced_available_evidence(pack, checked_paths)
        missing = list(payload.get("missing_evidence") or self._missing_evidence(pack, tuple(payload["required_evidence"]), checked_paths))
        financial_nodes = [item for item in available if "evidence_pack.financial_metrics." in item]
        valuation_nodes = [item for item in available if "evidence_pack.valuation_metrics" in item]
        business_nodes = [item for item in available if "evidence_pack.business_composition" in item]
        geography_nodes = [item for item in available if "evidence_pack.business_composition" in item and self._is_advanced_geography_node(item)]
        layer_nodes = self._advanced_layer_nodes(pack, str(payload.get("business_layer") or ""))
        robotics_nodes = self._advanced_robotics_valid_nodes(pack)

        path_policy = payload.get("path_policy", "fallback")
        path_nodes: list[str] = []
        status = payload.get("status")
        cap = payload.get("force_cap")
        reason = payload.get("not_assessable_reason", "")

        if path_policy == "layer_exposure":
            if layer_nodes:
                path_nodes = [layer_nodes[0], *financial_nodes[:3]]
                status = status or "partial"
                cap = cap or "low"
                path = " -> ".join(path_nodes)
            else:
                status = status or "not_assessable"
                cap = "not_assessable"
                path = TRANSMISSION_PATH_FALLBACK
                reason = reason or "The required business layer segment is absent or lacks numeric segment evidence."
        elif path_policy == "robotics_strict":
            if robotics_nodes:
                path_nodes = robotics_nodes[:1]
                status = status or "partial"
                cap = cap or "low"
                path = " -> ".join(path_nodes)
            else:
                status = status or "not_assessable"
                cap = "not_assessable"
                path = TRANSMISSION_PATH_FALLBACK
                reason = reason or "Robotics / actuator layer lacks independent non-zero revenue, order, customer, mass-production, delivery, or collection evidence."
        elif path_policy == "business_financial_observation":
            if business_nodes and financial_nodes:
                path_nodes = [business_nodes[0], *financial_nodes[:3]]
                status = status or "partial"
                cap = cap or "low"
                path = " -> ".join(path_nodes)
            elif business_nodes:
                path_nodes = [business_nodes[0]]
                status = status or "partial"
                cap = cap or "low"
                path = business_nodes[0]
            else:
                status = status or "not_assessable"
                cap = "not_assessable"
                path = TRANSMISSION_PATH_FALLBACK
                reason = reason or "Business segment node is required; financial metrics alone cannot establish business transmission."
        elif path_policy == "financial_observation":
            if financial_nodes:
                path_nodes = financial_nodes[:4]
                status = status or "partial"
                cap = cap or "low"
                path = " -> ".join(path_nodes)
            else:
                status = status or "not_assessable"
                cap = "not_assessable"
                path = TRANSMISSION_PATH_FALLBACK
                reason = reason or "Financial observation node is absent."
        elif path_policy == "geography_financial_observation":
            if geography_nodes:
                path_nodes = [geography_nodes[0], *financial_nodes[:2]]
                status = status or "partial"
                cap = cap or "low"
                path = " -> ".join(path_nodes)
            else:
                status = status or "not_assessable"
                cap = "not_assessable"
                path = TRANSMISSION_PATH_FALLBACK
                reason = reason or "Geographic / overseas segment node is absent."
        elif path_policy == "valuation_context":
            path_nodes = [*valuation_nodes[:1], *financial_nodes[:3], *business_nodes[:1]]
            if path_nodes:
                status = status or "partial"
                cap = cap or "low"
                path = " -> ".join(path_nodes)
            else:
                status = status or "not_assessable"
                cap = "not_assessable"
                path = TRANSMISSION_PATH_FALLBACK
                reason = reason or "Valuation context and operating evidence are absent."
        else:
            status = status or "not_assessable"
            cap = "not_assessable"
            path = TRANSMISSION_PATH_FALLBACK
            reason = reason or GENERIC_MISSING_BRIDGE_REASON

        if path == TRANSMISSION_PATH_FALLBACK:
            cap = "not_assessable"

        return DriverFactor(
            layer=payload["layer"],
            driver_factor=payload["driver_factor"],
            driver_scope=payload["driver_scope"],
            why_it_matters=payload["why_it_matters"],
            required_evidence=list(payload["required_evidence"]),
            available_evidence=available,
            missing_evidence=missing,
            company_transmission_path=path,
            data_availability_status=status,
            confidence_cap=cap,
            not_assessable_reason=reason,
            what_was_checked=list(checked_paths),
            source_refs=[item.split("=")[0] for item in path_nodes],
            research_question=payload["research_question"],
            interpretation_guard=payload["interpretation_guard"],
        )

    def _advanced_available_evidence(self, pack: dict[str, Any], checked_paths: tuple[str, ...]) -> list[str]:
        available: list[str] = []
        for path in checked_paths:
            if path in {"news", "latest_news"}:
                continue
            if path == "business_composition":
                available.extend(self._advanced_business_segment_nodes(pack))
            elif path == "business_composition.geography":
                available.extend(self._advanced_geography_nodes(pack))
            elif path == "enhanced_must_track_indicators":
                available.extend(self._indicator_nodes(pack))
            elif path in {"missing_fields", "unknown_or_missing_evidence", "risk_flags", "data_limitations"}:
                continue
            else:
                value = self._value_at_path(pack, path)
                if _is_present(value):
                    available.append(f"evidence_pack.{path}={_safe_text(_display_value(value))}")
        return available

    def _advanced_business_segment_nodes(self, pack: dict[str, Any]) -> list[str]:
        nodes: list[str] = []
        for index, row in enumerate(_as_list(pack.get("business_composition"))):
            if not isinstance(row, dict):
                continue
            name = row.get("segment_name")
            if not name:
                continue
            bits = [f"segment_name:{name}"]
            revenue = row.get("revenue")
            ratio = row.get("revenue_ratio")
            margin = row.get("gross_margin")
            period = row.get("period")
            if _is_present(revenue):
                bits.append(f"revenue:{_display_value(revenue)}")
            if _is_present(ratio):
                bits.append(f"revenue_ratio:{_display_value(ratio)}")
            if _is_present(margin):
                bits.append(f"gross_margin:{_display_value(margin)}")
            if period:
                bits.append(f"period:{period}")
            nodes.append(f"evidence_pack.business_composition[{index}]={'; '.join(bits)}")
        return nodes[:10]

    def _advanced_geography_nodes(self, pack: dict[str, Any]) -> list[str]:
        return [node for node in self._advanced_business_segment_nodes(pack) if self._is_advanced_geography_node(node)][:6]

    def _advanced_layer_nodes(self, pack: dict[str, Any], layer: str) -> list[str]:
        nodes: list[str] = []
        for node in self._advanced_business_segment_nodes(pack):
            lowered = node.lower()
            if layer == "core" and any(term in lowered for term in ("制冷", "空调", "refrigeration", "air-conditioning", "air conditioning")):
                nodes.append(node)
            elif layer == "automotive" and any(term in lowered for term in ("汽车", "automotive", "thermal-management", "thermal management")):
                nodes.append(node)
            elif layer == "robotics" and self._is_advanced_robotics_business_node(node):
                nodes.append(node)
        return nodes

    def _advanced_robotics_valid_nodes(self, pack: dict[str, Any]) -> list[str]:
        nodes: list[str] = []
        for node in self._advanced_layer_nodes(pack, "robotics"):
            if self._advanced_node_has_nonzero_revenue(node):
                nodes.append(node)
        nodes.extend(self._advanced_direct_robotics_nodes(pack))
        return nodes

    def _advanced_direct_robotics_nodes(self, pack: dict[str, Any]) -> list[str]:
        nodes: list[str] = []
        direct_terms = ("order", "customer", "mass production", "delivery", "collection", "订单", "客户", "量产", "交付", "回款")
        robotics_terms = ("robot", "robotics", "actuator", "机器人", "执行器")
        good_status = ("available", "partial", "confirmed", "disclosed")
        for index, row in enumerate(_as_list(pack.get("enhanced_must_track_indicators"))):
            if not isinstance(row, dict):
                continue
            name = str(row.get("indicator_name") or "")
            status = str(row.get("current_status") or "")
            value = row.get("current_value")
            haystack = f"{name} {status} {_display_value(value) if _is_present(value) else ''}".lower()
            if (
                _is_present(value)
                and any(term.lower() in haystack for term in robotics_terms)
                and any(term.lower() in haystack for term in direct_terms)
                and any(term in status.lower() for term in good_status)
            ):
                nodes.append(
                    f"evidence_pack.enhanced_must_track_indicators[{index}]="
                    f"{_safe_text(name)}; status:{_safe_text(status)}; value:{_safe_text(_display_value(value))}"
                )
        return nodes

    def _is_advanced_robotics_business_node(self, node: str) -> bool:
        lowered = node.lower()
        if any(term.lower() in lowered for term in ADVANCED_MANUFACTURING_LAYOUT_TERMS):
            return False
        return any(term in lowered for term in ("robot", "robotics", "actuator", "机器人", "执行器"))

    def _advanced_node_has_nonzero_revenue(self, node: str) -> bool:
        if "revenue:" not in node and "revenue_ratio:" not in node:
            return False
        lowered = node.lower()
        zero_markers = ("revenue:0", "revenue_ratio:0", "revenue_ratio:0.00%", "revenue_ratio:0%")
        return not any(marker in lowered for marker in zero_markers)

    def _is_advanced_geography_node(self, node: str) -> bool:
        lowered = node.lower()
        return any(
            term in lowered
            for term in (
                "overseas",
                "domestic",
                "geography",
                "region",
                "国外",
                "国内",
                "境外",
                "境内",
                "海外",
                "地区",
            )
        )

    def _semiconductor_cycle_drivers(self, pack: dict[str, Any]) -> list[DriverFactor]:
        rows: list[DriverFactor] = []
        for payload in self._semiconductor_driver_payloads():
            rows.append(self._build_semiconductor_driver(pack, payload))
        return rows

    def _semiconductor_driver_payloads(self) -> list[dict[str, Any]]:
        return [
            {
                "layer": "macro",
                "driver_factor": "semiconductor capex cycle",
                "driver_scope": "macro / industry / cycle",
                "why_it_matters": "Fab capex can affect equipment demand, but external capex is not company orders or revenue.",
                "required_evidence": [
                    "semiconductor wafer-fab capex by customer / node / category",
                    "equipment segment exposure",
                    "customer order / shipment / revenue bridge",
                    "margin and cash-flow bridge",
                ],
                "checked_paths": ("business_composition", "basic_info.main_business", "financial_metrics.revenue", "financial_metrics.gross_margin", "financial_metrics.operating_cashflow"),
                "path_policy": "business_financial_observation",
                "missing_evidence": ["fab capex cycle data", "customer capex by fab", "product-category order / shipment", "delivery and acceptance schedule"],
                "interpretation_guard": "External semiconductor capex is background only; do not convert it into company order, shipment, revenue, margin, or cash-flow facts without company bridge evidence.",
                "research_question": "Which fab capex categories map to the company's disclosed equipment segments, customers, orders, revenue, receivables, and cash conversion?",
            },
            {
                "layer": "industry",
                "driver_factor": "downstream demand cycle",
                "driver_scope": "macro / industry / cycle",
                "why_it_matters": "End demand can affect fabs and equipment orders, but downstream demand is not company demand without customer or shipment evidence.",
                "required_evidence": ["end-demand by application", "customer mix", "product shipments", "order / receivable / cash-flow bridge"],
                "checked_paths": ("business_composition", "financial_metrics.revenue", "financial_metrics.gross_margin", "financial_metrics.operating_cashflow"),
                "path_policy": "fallback",
                "status": "not_assessable",
                "missing_evidence": ["downstream demand series", "customer production utilization", "shipment volume", "order pull-in / pushout evidence"],
                "not_assessable_reason": "Customer, order, shipment, and product bridge evidence is absent; financial co-movement cannot prove semiconductor demand transmission.",
                "interpretation_guard": "Downstream demand is not company demand unless company customer, order, shipment, revenue, receivable, and cash-flow evidence is present.",
                "research_question": "Has downstream demand translated into company orders, shipments, revenue, receivables, and operating cash flow?",
            },
            {
                "layer": "industry",
                "driver_factor": "inventory cycle",
                "driver_scope": "macro / industry / cycle",
                "why_it_matters": "Aggregate inventory is a working-capital observation; demand-cycle interpretation needs product-level and operating evidence.",
                "required_evidence": ["aggregate inventory", "product-level inventory", "inventory turnover", "order / shipment evidence", "write-down detail"],
                "checked_paths": ("business_composition", "financial_metrics.inventory", "financial_metrics.revenue", "financial_metrics.gross_margin", "financial_metrics.operating_cashflow"),
                "path_policy": "business_financial_observation",
                "missing_evidence": ["product-level inventory split", "inventory aging", "inventory turnover", "order / shipment evidence", "inventory write-down detail"],
                "interpretation_guard": "Inventory movement is a working-capital observation only; do not infer demand strength or demand weakness from aggregate inventory movement.",
                "research_question": "Is inventory movement driven by demand, production ramp, long-cycle equipment delivery, safety stock, product mix, write-down, or customer timing?",
            },
            {
                "layer": "industry",
                "driver_factor": "localization / domestic substitution",
                "driver_scope": "macro / industry / cycle",
                "why_it_matters": "Localization context matters only after it is tied to disclosed revenue, customer adoption, accepted orders, and collection evidence.",
                "required_evidence": ["localized product revenue", "domestic customer adoption", "accepted orders", "collection evidence"],
                "checked_paths": ("business_composition", "enhanced_must_track_indicators", "financial_metrics.revenue"),
                "path_policy": "fallback",
                "status": "missing",
                "missing_evidence": ["localization revenue split", "domestic customer adoption", "accepted orders", "collection evidence"],
                "not_assessable_reason": "Localization revenue / domestic customer adoption evidence is missing in the current evidence pack.",
                "interpretation_guard": "Localization narrative is not realized revenue without company localization revenue, customer adoption, orders, and collection evidence.",
                "research_question": "What disclosed revenue, customers, orders, adoption, and collection evidence proves localization conversion?",
            },
            {
                "layer": "risk",
                "driver_factor": "export control / sanctions / overseas restriction",
                "driver_scope": "macro / policy / risk",
                "why_it_matters": "Restrictions are risk or constraint context unless company-level affected product, supplier, customer, cost, order, or revenue impact is disclosed.",
                "required_evidence": ["official restriction", "affected product / supplier / customer / geography", "company exposure", "order / cost / revenue impact"],
                "checked_paths": ("risk_flags", "missing_fields", "unknown_or_missing_evidence", "business_composition", "financial_metrics.revenue"),
                "path_policy": "fallback",
                "status": "not_assessable",
                "missing_evidence": ["company-level affected product", "supplier exposure", "customer exposure", "cost / order / revenue impact evidence"],
                "not_assessable_reason": "Current evidence lacks company-level restriction impact nodes.",
                "interpretation_guard": "Export-control context must remain risk / constraint context; do not state realized positive or negative company operating impact without company impact evidence.",
                "research_question": "Which products, suppliers, customers, or geographies are exposed to restrictions, and what realized impact is visible in orders, costs, revenue, or cash flow?",
            },
            {
                "layer": "supply_chain",
                "driver_factor": "equipment sub-chain classification",
                "driver_scope": "equipment / materials / foundry / fabless / OSAT",
                "why_it_matters": "Sub-chain classification decides which operating variables are relevant; equipment logic must not be applied to other sub-chains.",
                "required_evidence": ["explicit sub-chain classification", "segment revenue", "equipment product exposure", "financial bridge"],
                "checked_paths": ("business_composition", "basic_info.industry", "basic_info.main_business", "financial_metrics.revenue"),
                "path_policy": "business_financial_observation",
                "missing_evidence": ["equipment-type split such as etch / deposition / cleaning", "customer fab use case", "order / shipment bridge"],
                "interpretation_guard": "The first version treats 002371 as equipment only when disclosed business nodes support it; do not apply equipment order logic to materials, foundry, fabless, or OSAT.",
                "research_question": "Which disclosed segment proves equipment sub-chain exposure, and which equipment-type operating variables still need follow-up evidence?",
            },
            *[
                {
                    "layer": "supply_chain",
                    "driver_factor": f"{sub_chain} sub-chain boundary",
                    "driver_scope": "equipment / materials / foundry / fabless / OSAT",
                    "why_it_matters": f"{sub_chain} requires its own operating metrics and is not fully implemented in semiconductor P1.1 v1.",
                    "required_evidence": [f"explicit {sub_chain} business exposure", f"{sub_chain} segment revenue", f"{sub_chain} operating metrics"],
                    "checked_paths": ("business_composition", "basic_info.main_business"),
                    "path_policy": "fallback",
                    "status": "not_assessable",
                    "missing_evidence": [f"explicit {sub_chain} exposure", f"{sub_chain} segment revenue", f"{sub_chain} operating metrics"],
                    "not_assessable_reason": f"Current 002371 evidence does not provide a complete {sub_chain} implementation basis; absence is not treated as not_applicable.",
                    "interpretation_guard": f"Do not apply equipment order logic to {sub_chain}; use not_applicable only when explicit evidence shows irrelevance.",
                    "research_question": f"Does the company have explicit {sub_chain} exposure, and what segment revenue and operating metrics would be required before assessing it?",
                }
                for sub_chain in ("materials", "fabless", "foundry", "OSAT")
            ],
            {
                "layer": "company",
                "driver_factor": "semiconductor-related revenue contribution",
                "driver_scope": "company / business",
                "why_it_matters": "Segment revenue contribution is the first exposure node, but exposure is not cycle transmission.",
                "required_evidence": ["segment revenue", "revenue ratio", "segment definition", "period", "total revenue bridge"],
                "checked_paths": ("business_composition", "financial_metrics.revenue", "financial_metrics.gross_margin"),
                "path_policy": "business_financial_observation",
                "missing_evidence": ["more granular semiconductor-only revenue", "product-level revenue", "customer split"],
                "interpretation_guard": "Segment exposure can support exposure only; it does not prove demand, localization conversion, or semiconductor-cycle transmission.",
                "research_question": "What share of revenue is directly semiconductor-related, and what segment definition supports that exposure?",
            },
            {
                "layer": "company",
                "driver_factor": "product / equipment / material segment exposure",
                "driver_scope": "company / business",
                "why_it_matters": "Product and equipment segment labels decide what evidence can be used for transmission.",
                "required_evidence": ["product category", "equipment type or material type", "revenue ratio", "margin", "customer use case"],
                "checked_paths": ("business_composition", "basic_info.main_business", "financial_metrics.revenue", "financial_metrics.gross_margin"),
                "path_policy": "business_financial_observation",
                "missing_evidence": ["etch / deposition / cleaning / materials split", "process-node coverage", "customer application"],
                "interpretation_guard": "A broad electronic process equipment label does not imply exposure to every semiconductor equipment or material category.",
                "research_question": "Which product or equipment/material segment drives revenue and margin, and what customer fab use case does it address?",
            },
            {
                "layer": "company",
                "driver_factor": "customer qualification / customer adoption",
                "driver_scope": "company / business",
                "why_it_matters": "Qualification and adoption evidence is required before customer progress can be connected to batch economics.",
                "required_evidence": ["customer qualification status", "production-line adoption", "acceptance", "batch order", "repeat order", "revenue and collection"],
                "checked_paths": ("enhanced_must_track_indicators", "missing_fields", "unknown_or_missing_evidence"),
                "path_policy": "fallback",
                "status": "missing",
                "missing_evidence": ["customer qualification status", "customer adoption", "accepted order", "repeat order", "revenue and collection"],
                "not_assessable_reason": "Customer qualification / adoption evidence is expected but entirely absent.",
                "interpretation_guard": "Do not infer qualification success or qualification failure when qualification / adoption evidence is absent.",
                "research_question": "Which customers have qualified and adopted the product, and has adoption converted into accepted orders, revenue, and collection?",
            },
            {
                "layer": "company",
                "driver_factor": "order visibility",
                "driver_scope": "company / business",
                "why_it_matters": "Order visibility requires signed orders, true backlog, delivery schedule, cancellation, shipment, and revenue-recognition evidence.",
                "required_evidence": ["signed orders", "true backlog", "delivery schedule", "cancellation history", "shipment", "revenue recognition"],
                "checked_paths": ("financial_metrics.contract_liabilities", "financial_metrics.revenue", "financial_metrics.operating_cashflow", "enhanced_must_track_indicators"),
                "path_policy": "fallback",
                "status": "missing",
                "missing_evidence": ["true backlog", "new signed orders", "delivery schedule", "customer / order table", "cancellation history"],
                "not_assessable_reason": "True backlog and signed-order evidence is absent; contract liabilities alone cannot establish order visibility.",
                "interpretation_guard": "Contract liabilities are partial proxy only and are not backlog or confirmed delivery.",
                "research_question": "What order, backlog, delivery, cancellation, and shipment evidence supports revenue visibility?",
            },
            {
                "layer": "company",
                "driver_factor": "backlog / contract liabilities as partial proxy only",
                "driver_scope": "company / business",
                "why_it_matters": "Contract liabilities can be a partial prepayment proxy, but they are not true backlog or confirmed delivery.",
                "required_evidence": ["contract liabilities", "prepayment terms", "linked customer / order / project", "revenue-recognition terms"],
                "checked_paths": ("business_composition", "financial_metrics.contract_liabilities", "financial_metrics.revenue", "financial_metrics.operating_cashflow"),
                "path_policy": "business_financial_observation",
                "missing_evidence": ["contract note parser", "order disclosure", "customer / project mapping", "revenue-recognition schedule"],
                "force_cap": "low",
                "interpretation_guard": "Contract liabilities are partial proxy only, not backlog or confirmed delivery; order visibility must not exceed partial.",
                "research_question": "What customer, order, or project do contract liabilities correspond to, and what evidence prevents treating them as true backlog?",
            },
            {
                "layer": "company",
                "driver_factor": "localization revenue evidence",
                "driver_scope": "company / business",
                "why_it_matters": "Localization conversion requires company revenue, customer adoption, accepted orders, and collection evidence.",
                "required_evidence": ["localization-specific revenue", "domestic customer adoption", "product acceptance", "repeat orders", "collection"],
                "checked_paths": ("enhanced_must_track_indicators", "business_composition", "financial_metrics.revenue"),
                "path_policy": "fallback",
                "status": "missing",
                "missing_evidence": ["localization-specific revenue", "domestic customer adoption", "product acceptance", "repeat orders", "collection"],
                "not_assessable_reason": "Localization revenue / domestic customer adoption / accepted-order evidence is missing.",
                "interpretation_guard": "Company localization wording cannot substitute for disclosed localization revenue and customer evidence.",
                "research_question": "Which disclosed revenue and customer evidence proves that localization has converted into company economics?",
            },
            {
                "layer": "financial",
                "driver_factor": "R&D intensity and product conversion",
                "driver_scope": "company / business / financial",
                "why_it_matters": "R&D expense and ratio are input evidence; commercialization requires product conversion and customer adoption evidence.",
                "required_evidence": ["R&D expense", "R&D ratio", "product launch", "customer validation", "order revenue", "margin contribution"],
                "checked_paths": ("business_composition", "financial_metrics.r_and_d_expense", "financial_metrics.r_and_d_expense_ratio", "financial_metrics.revenue"),
                "path_policy": "business_financial_observation",
                "missing_evidence": ["R&D project list", "product milestone", "customer validation", "order revenue", "margin contribution"],
                "force_cap": "low",
                "interpretation_guard": "R&D expense and ratio are input evidence only; do not convert them into a technology-barrier conclusion without product conversion and customer adoption evidence.",
                "research_question": "Which R&D projects have converted into products, customer validation, order revenue, and margin contribution?",
            },
            {
                "layer": "financial",
                "driver_factor": "revenue growth quality",
                "driver_scope": "financial",
                "why_it_matters": "Revenue growth quality needs segment, order, receivable, and cash-flow validation rather than financial co-movement alone.",
                "required_evidence": ["revenue", "revenue_yoy", "segment revenue", "orders / shipments", "receivables", "operating cash flow"],
                "checked_paths": ("business_composition", "financial_metrics.revenue", "financial_metrics.revenue_yoy", "financial_metrics.accounts_receivable", "financial_metrics.operating_cashflow"),
                "path_policy": "business_financial_observation",
                "missing_evidence": ["independent order evidence", "shipment evidence", "customer adoption evidence", "receivable aging"],
                "interpretation_guard": "Positive revenue_yoy plus stable or improving gross margin is not semiconductor cycle transmission and is not demand-strength evidence without independent operating nodes.",
                "research_question": "Does revenue growth reconcile with segment revenue, orders, shipments, receivables, and operating cash flow rather than only financial co-movement?",
            },
            {
                "layer": "financial",
                "driver_factor": "gross margin recovery or pressure",
                "driver_scope": "financial",
                "why_it_matters": "Gross margin must be tied to product mix, pricing, cost, and order evidence before it can explain business transmission.",
                "required_evidence": ["gross margin", "product mix", "pricing", "cost", "order / shipment bridge"],
                "checked_paths": ("business_composition", "financial_metrics.gross_margin", "financial_metrics.revenue", "financial_metrics.operating_cashflow"),
                "path_policy": "business_financial_observation",
                "missing_evidence": ["product-mix bridge", "pricing evidence", "cost evidence", "order / shipment bridge"],
                "interpretation_guard": "Gross margin observation cannot be combined with revenue_yoy to claim cycle transmission; product mix, pricing, cost, and operating evidence are required.",
                "research_question": "Which product mix, pricing, cost, order, and shipment evidence explains gross margin movement?",
            },
            {
                "layer": "financial",
                "driver_factor": "inventory level and inventory turnover",
                "driver_scope": "financial",
                "why_it_matters": "Inventory and turnover diagnose working capital and write-down risk, not demand health by themselves.",
                "required_evidence": ["inventory", "inventory turnover", "product-level inventory", "orders", "revenue", "gross margin"],
                "checked_paths": ("business_composition", "financial_metrics.inventory", "financial_metrics.revenue", "financial_metrics.gross_margin"),
                "path_policy": "business_financial_observation",
                "missing_evidence": ["inventory turnover", "product-level inventory", "order evidence", "write-down detail"],
                "interpretation_guard": "Aggregate inventory is only a working-capital observation; do not infer demand health or deterioration without product-level and operating evidence.",
                "research_question": "What inventory turnover, product-level inventory, order, revenue, gross margin, and write-down evidence explains the inventory level?",
            },
            {
                "layer": "financial",
                "driver_factor": "receivables and cash conversion",
                "driver_scope": "financial",
                "why_it_matters": "Receivables and operating cash flow test whether revenue converts into cash.",
                "required_evidence": ["accounts receivable", "receivable aging", "operating cash flow", "collection terms", "customer concentration"],
                "checked_paths": ("business_composition", "financial_metrics.accounts_receivable", "financial_metrics.operating_cashflow", "financial_metrics.revenue"),
                "path_policy": "business_financial_observation",
                "missing_evidence": ["receivable aging", "payment terms", "customer-specific collection", "cash conversion cycle"],
                "interpretation_guard": "Revenue observation needs receivable and cash conversion checks; receivables alone do not prove order quality.",
                "research_question": "Do receivables, aging, collection terms, and operating cash flow support revenue cash conversion?",
            },
            {
                "layer": "financial",
                "driver_factor": "operating cash flow",
                "driver_scope": "financial",
                "why_it_matters": "Operating cash flow validates whether accounting profit and revenue are converting into cash.",
                "required_evidence": ["operating cash flow", "revenue", "net profit", "receivables", "inventory"],
                "checked_paths": ("business_composition", "financial_metrics.operating_cashflow", "financial_metrics.revenue", "financial_metrics.net_profit", "financial_metrics.accounts_receivable", "financial_metrics.inventory"),
                "path_policy": "business_financial_observation",
                "missing_evidence": ["cash conversion cycle", "receivable aging", "inventory turnover"],
                "interpretation_guard": "Operating cash flow is a financial validation node; it does not independently prove semiconductor demand or order visibility.",
                "research_question": "How do operating cash flow, revenue, net profit, receivables, and inventory reconcile for cash-conversion quality?",
            },
            {
                "layer": "financial",
                "driver_factor": "capex discipline",
                "driver_scope": "financial",
                "why_it_matters": "Aggregate capex observes investment cash outflow; project mapping is required before operating implications can be assessed.",
                "required_evidence": ["capex", "project mapping", "acceptance", "utilization", "shipment bridge", "revenue and cash-flow bridge"],
                "checked_paths": ("business_composition", "financial_metrics.capex", "financial_metrics.operating_cashflow", "financial_metrics.revenue"),
                "path_policy": "business_financial_observation",
                "missing_evidence": ["project mapping", "acceptance", "utilization", "shipment bridge", "revenue and cash-flow bridge"],
                "interpretation_guard": "Aggregate capex is cash outflow / investment observation only; do not infer utilization, shipment, or revenue bridge without project evidence.",
                "research_question": "Which projects or assets does capex correspond to, and is there acceptance, utilization, shipment, revenue, or cash-flow evidence?",
            },
            {
                "layer": "financial",
                "driver_factor": "R&D expense and R&D ratio as input evidence only",
                "driver_scope": "financial",
                "why_it_matters": "R&D expense and ratio can be tracked as inputs but require conversion evidence to support product economics.",
                "required_evidence": ["R&D expense", "R&D ratio", "product conversion", "customer adoption", "order revenue", "margin contribution"],
                "checked_paths": ("business_composition", "financial_metrics.r_and_d_expense", "financial_metrics.r_and_d_expense_ratio", "financial_metrics.revenue"),
                "path_policy": "business_financial_observation",
                "missing_evidence": ["product conversion", "customer adoption", "order revenue", "margin contribution"],
                "force_cap": "low",
                "interpretation_guard": "R&D expense and ratio are input evidence only; no technology-barrier conclusion is allowed without product conversion and customer adoption evidence.",
                "research_question": "Do R&D expense and R&D ratio connect to product conversion, customer adoption, order revenue, and margin contribution?",
            },
            {
                "layer": "financial",
                "driver_factor": "impairment / inventory write-down risk",
                "driver_scope": "financial / risk",
                "why_it_matters": "Inventory write-down and impairment detail is needed to assess obsolete inventory or project asset risk.",
                "required_evidence": ["inventory", "inventory aging", "write-down detail", "impairment detail", "product-level inventory"],
                "checked_paths": ("business_composition", "financial_metrics.inventory", "financial_metrics.gross_margin", "risk_flags"),
                "path_policy": "business_financial_observation",
                "missing_evidence": ["inventory aging", "inventory write-down detail", "impairment detail", "product-level inventory"],
                "interpretation_guard": "Aggregate inventory cannot identify obsolete product, impairment, or demand weakness without write-down and product-level evidence.",
                "research_question": "Are inventory aging, write-down, impairment, and product-level inventory details sufficient to assess inventory risk?",
            },
            {
                "layer": "risk",
                "driver_factor": "inventory overbuild",
                "driver_scope": "risk",
                "why_it_matters": "Inventory overbuild risk requires product-level inventory, turnover, order, margin, and write-down evidence.",
                "required_evidence": ["product-level inventory", "turnover", "orders", "gross margin", "write-down"],
                "checked_paths": ("business_composition", "financial_metrics.inventory", "financial_metrics.revenue", "financial_metrics.gross_margin"),
                "path_policy": "business_financial_observation",
                "missing_evidence": ["product-level inventory", "inventory turnover", "orders", "write-down detail"],
                "interpretation_guard": "Inventory increase is not direct demand weakness, and inventory decline plus revenue growth is not demand-strength proof.",
                "research_question": "Does product-level inventory, turnover, orders, gross margin, and write-down evidence indicate overbuild risk?",
            },
            {
                "layer": "risk",
                "driver_factor": "downstream capex slowdown",
                "driver_scope": "risk",
                "why_it_matters": "Customer capex slowdown risk needs customer capex, order, shipment, revenue, and cash-flow evidence.",
                "required_evidence": ["customer capex", "customer order / shipment", "revenue bridge", "cash-flow bridge"],
                "checked_paths": ("business_composition", "financial_metrics.revenue", "risk_flags"),
                "path_policy": "fallback",
                "status": "not_assessable",
                "missing_evidence": ["customer capex data", "customer order / shipment", "revenue bridge", "cash-flow bridge"],
                "not_assessable_reason": "Customer capex and company order / shipment bridge evidence is absent.",
                "interpretation_guard": "Do not infer company impact from downstream capex context without customer and company bridge evidence.",
                "research_question": "Would downstream capex slowdown appear in company order, shipment, revenue, receivable, and cash-flow evidence?",
            },
            {
                "layer": "risk",
                "driver_factor": "customer qualification failure",
                "driver_scope": "risk",
                "why_it_matters": "Qualification failure risk cannot be inferred without qualification/adoption evidence and failure indicators.",
                "required_evidence": ["qualification status", "adoption status", "failure / delay disclosure", "order impact", "revenue impact"],
                "checked_paths": ("enhanced_must_track_indicators", "risk_flags", "unknown_or_missing_evidence"),
                "path_policy": "fallback",
                "status": "missing",
                "missing_evidence": ["qualification status", "adoption status", "failure / delay disclosure", "order impact", "revenue impact"],
                "not_assessable_reason": "Customer qualification / adoption evidence is expected but absent; neither success nor failure can be inferred.",
                "interpretation_guard": "Do not infer customer qualification failure or success from missing data.",
                "research_question": "What qualification or adoption evidence would reveal customer delay, failure, accepted order, or revenue impact?",
            },
            {
                "layer": "risk",
                "driver_factor": "localization narrative without revenue",
                "driver_scope": "risk",
                "why_it_matters": "Localization narrative can remain unrealized if revenue, adoption, accepted orders, and collection evidence are missing.",
                "required_evidence": ["localization revenue", "domestic customer adoption", "accepted orders", "collection"],
                "checked_paths": ("enhanced_must_track_indicators", "risk_flags", "business_composition"),
                "path_policy": "fallback",
                "status": "missing",
                "missing_evidence": ["localization revenue", "domestic customer adoption", "accepted orders", "collection"],
                "not_assessable_reason": "Localization realization evidence is missing; risk row records narrative-not-realized risk only.",
                "interpretation_guard": "This risk row flags narrative-not-realized risk and must not duplicate a company localization revenue conclusion.",
                "research_question": "What evidence would show whether localization narrative remains unconverted into revenue, orders, adoption, and collection?",
            },
            {
                "layer": "risk",
                "driver_factor": "R&D overread commercialization risk",
                "driver_scope": "risk",
                "why_it_matters": "R&D input metrics can be overread if product conversion and customer adoption evidence is missing.",
                "required_evidence": ["R&D expense", "R&D ratio", "product conversion", "customer adoption", "order revenue"],
                "checked_paths": ("business_composition", "financial_metrics.r_and_d_expense", "financial_metrics.r_and_d_expense_ratio"),
                "path_policy": "business_financial_observation",
                "missing_evidence": ["product conversion", "customer adoption", "order revenue", "margin contribution"],
                "force_cap": "low",
                "interpretation_guard": "R&D input metrics should not be overread as commercialized product strength without conversion evidence.",
                "research_question": "Where could R&D input metrics be overread because product conversion, customer adoption, order revenue, or margin evidence is missing?",
            },
            {
                "layer": "risk",
                "driver_factor": "export control / supply-chain restriction",
                "driver_scope": "risk",
                "why_it_matters": "Supply-chain restriction risk requires company product, supplier, customer, cost, order, or revenue impact nodes.",
                "required_evidence": ["restricted supplier / component", "affected product", "affected customer", "cost impact", "order / revenue impact"],
                "checked_paths": ("risk_flags", "missing_fields", "unknown_or_missing_evidence", "business_composition"),
                "path_policy": "fallback",
                "status": "not_assessable",
                "missing_evidence": ["restricted supplier / component", "affected product", "affected customer", "cost / order / revenue impact"],
                "not_assessable_reason": "Company-level product, supplier, customer, cost, order, and revenue impact nodes are absent.",
                "interpretation_guard": "Treat restrictions as risk / constraint context only until company impact evidence is disclosed.",
                "research_question": "Which suppliers, components, products, customers, costs, orders, or revenue lines would evidence restriction exposure?",
            },
            {
                "layer": "risk",
                "driver_factor": "margin pressure from product mix or price competition",
                "driver_scope": "risk",
                "why_it_matters": "Margin pressure needs product mix, pricing, cost, and competition evidence beyond gross margin alone.",
                "required_evidence": ["gross margin", "product mix", "pricing", "cost", "competition evidence"],
                "checked_paths": ("business_composition", "financial_metrics.gross_margin", "financial_metrics.revenue"),
                "path_policy": "business_financial_observation",
                "missing_evidence": ["product-mix detail", "pricing evidence", "cost detail", "competition evidence"],
                "interpretation_guard": "Gross margin alone cannot identify product-mix or price-competition pressure.",
                "research_question": "Is margin pressure tied to product mix, pricing, costs, or competition, and what evidence supports that link?",
            },
            {
                "layer": "risk",
                "driver_factor": "capex without utilization or revenue bridge",
                "driver_scope": "risk",
                "why_it_matters": "Capex can create execution and cash-flow risk if project utilization and revenue bridge remain unverified.",
                "required_evidence": ["capex", "project mapping", "acceptance", "utilization", "revenue bridge", "cash-flow bridge"],
                "checked_paths": ("business_composition", "financial_metrics.capex", "financial_metrics.operating_cashflow", "financial_metrics.revenue"),
                "path_policy": "business_financial_observation",
                "missing_evidence": ["project mapping", "acceptance", "utilization", "revenue bridge"],
                "interpretation_guard": "Aggregate capex is not proof of utilization, shipment, or revenue bridge.",
                "research_question": "Could capex remain unverified because project mapping, acceptance, utilization, revenue, and cash-flow evidence are missing?",
            },
            {
                "layer": "risk",
                "driver_factor": "contract liabilities / operating cash flow signal consistency",
                "driver_scope": "risk / contradiction",
                "why_it_matters": "Concrete company signals must be listed together when they could point in different directions.",
                "required_evidence": ["contract liabilities", "operating cash flow", "revenue", "orders / backlog mapping"],
                "checked_paths": ("business_composition", "financial_metrics.contract_liabilities", "financial_metrics.operating_cashflow", "financial_metrics.revenue"),
                "path_policy": "business_financial_observation",
                "missing_evidence": ["order / backlog mapping", "prepayment terms", "customer / project mapping", "receivable aging"],
                "force_cap": "low",
                "interpretation_guard": "If contract liabilities and operating cash flow conflict, list both signals and require manual review; do not selectively cite one signal.",
                "research_question": "Do contract liabilities, operating cash flow, revenue, and customer/order mapping point to consistent visibility, or do conflicting signals require manual review?",
            },
        ]

    def _build_semiconductor_driver(self, pack: dict[str, Any], payload: dict[str, Any]) -> DriverFactor:
        checked_paths = tuple(payload["checked_paths"])
        available = self._available_evidence(pack, checked_paths)
        missing = list(payload.get("missing_evidence") or self._missing_evidence(pack, tuple(payload["required_evidence"]), checked_paths))
        business_nodes = self._prioritize_semiconductor_business_nodes(
            [item for item in available if self._is_semiconductor_business_node(item)]
        )
        financial_nodes = [item for item in available if "evidence_pack.financial_metrics." in item]

        path_policy = payload.get("path_policy", "fallback")
        path_nodes: list[str] = []
        status = payload.get("status")
        cap = payload.get("force_cap")
        reason = payload.get("not_assessable_reason", "")
        if path_policy == "business_financial_observation":
            if business_nodes and financial_nodes:
                path_nodes = [business_nodes[0], *financial_nodes[:3]]
                status = status or "partial"
                cap = cap or "low"
                path = " -> ".join(path_nodes)
            elif business_nodes:
                path_nodes = [business_nodes[0]]
                status = status or "partial"
                cap = cap or "low"
                path = business_nodes[0]
            else:
                status = "not_assessable"
                cap = "not_assessable"
                path = TRANSMISSION_PATH_FALLBACK
                reason = (
                    "Semiconductor transmission requires a business / segment starting node; "
                    "financial metrics alone cannot establish company transmission."
                )
        else:
            status = status or "not_assessable"
            cap = "not_assessable"
            path = TRANSMISSION_PATH_FALLBACK
            path_nodes = []
            reason = reason or GENERIC_MISSING_BRIDGE_REASON

        if path == TRANSMISSION_PATH_FALLBACK:
            cap = "not_assessable"
        elif not financial_nodes and cap != "low":
            cap = "low"

        return DriverFactor(
            layer=payload["layer"],
            driver_factor=payload["driver_factor"],
            driver_scope=payload["driver_scope"],
            why_it_matters=payload["why_it_matters"],
            required_evidence=list(payload["required_evidence"]),
            available_evidence=available,
            missing_evidence=missing,
            company_transmission_path=path,
            data_availability_status=status,
            confidence_cap=cap,
            not_assessable_reason=reason,
            what_was_checked=list(checked_paths),
            source_refs=[item.split("=")[0] for item in path_nodes],
            research_question=payload["research_question"],
            interpretation_guard=payload["interpretation_guard"],
        )

    def _is_semiconductor_business_node(self, node: str) -> bool:
        if "evidence_pack.business_composition" in node:
            lowered = node.lower()
            geography_terms = ("geography", "region", "by geography", "鎸夊湴", "鍦板尯")
            return not any(term in lowered for term in geography_terms)
        if "evidence_pack.basic_info." not in node:
            return False
        lowered = node.lower()
        terms = (
            "semiconductor",
            "electronic process",
            "equipment",
            "integrated circuit",
            "wafer",
            "鐢靛瓙宸ヨ壓",
            "瑁呭",
            "闆嗘垚鐢佃矾",
            "鍗婂浣",
        )
        return any(term in lowered for term in terms)

    def _prioritize_semiconductor_business_nodes(self, nodes: list[str]) -> list[str]:
        return sorted(nodes, key=lambda item: 0 if "evidence_pack.business_composition" in item else 1)

    def _ai_datacenter_drivers(self, pack: dict[str, Any], sub_type: str) -> list[DriverFactor]:
        specs = [*self._common_specs()]
        if sub_type == "cooling_liquid_cooling_infrastructure":
            specs.extend(self._cooling_specs())
        elif sub_type == "datacenter_operator":
            specs.extend(self._operator_specs())
        return [self._build_driver(pack, spec) for spec in specs]

    def _common_specs(self) -> list[DriverSpec]:
        return [
            DriverSpec(
                "macro",
                "AI capex cycle",
                "macro",
                "AI capex can affect infrastructure demand, but customer capex is not company revenue.",
                ("customer AI capex source", "company customer or order bridge", "segment revenue bridge"),
                ("business_composition", "financial_metrics.revenue", "financial_metrics.accounts_receivable"),
                "AI capex is background only until company contracts, revenue, delivery, and cash collection are evidenced.",
                "AI capex demand has not yet been tied to disclosed company orders, revenue, delivery, and cash collection; what evidence can bridge that gap?",
                "Check customer capex source, disclosed customer/order evidence, segment revenue, receivables, and operating cash flow.",
            ),
            DriverSpec(
                "policy",
                "power / PUE policy",
                "policy",
                "PUE policy can constrain datacenter economics and cooling demand, but policy is not business realization.",
                ("policy source", "company PUE metric", "project/customer revenue bridge"),
                ("missing_fields", "unknown_or_missing_evidence", "enhanced_must_track_indicators"),
                "Policy or efficiency language must not be treated as revenue without project and financial evidence.",
                "Which disclosed PUE metrics, project acceptance records, or customer contracts verify company-level exposure to PUE policy constraints?",
                "Check PUE fields, project disclosures, customer contracts, and revenue bridge.",
            ),
            DriverSpec(
                "financial",
                "electricity cost pressure",
                "financial",
                "Power cost can affect datacenter profitability and PUE economics.",
                ("electricity cost", "PUE metric", "gross margin", "operating cash flow"),
                ("financial_metrics.gross_margin", "financial_metrics.operating_cashflow", "missing_fields"),
                "Electricity cost pressure cannot be inferred from PUE or revenue alone.",
                "Does the evidence pack disclose electricity cost, PUE, gross-margin effect, and operating-cash-flow impact for datacenter operations?",
                "Check electricity cost disclosure, PUE, gross margin, and operating cash flow.",
                True,
            ),
            DriverSpec(
                "company",
                "data center related revenue",
                "company",
                "Datacenter revenue share is the first company-level bridge for the AI infrastructure thesis.",
                ("business composition segment", "datacenter-related revenue or ratio", "period"),
                ("business_composition", "enhanced_must_track_indicators", "financial_metrics.revenue"),
                "Segment revenue can support exposure, but not orders, utilization, or future growth by itself.",
                "What portion of revenue is disclosed as datacenter, AIDC, IDC, room cooling, cabinet cooling, or related infrastructure revenue?",
                "Check business composition segments and period-specific revenue ratios.",
                True,
            ),
            DriverSpec(
                "company",
                "customer contracts / order visibility",
                "company",
                "Orders and contracts are required before treating demand as company realization.",
                ("customer identity or type", "order amount or contract term", "delivery or acceptance stage", "revenue recognition path"),
                ("financial_metrics.contract_liabilities", "unknown_or_missing_evidence", "enhanced_must_track_indicators"),
                "Contract liabilities are partial proxy only and must not be treated as backlog or confirmed future revenue.",
                "Which disclosed customer contracts or orders identify customer type, amount, delivery stage, acceptance, and revenue recognition path?",
                "Check customer/order disclosures, contract liabilities only as partial proxy, delivery, acceptance, and revenue recognition.",
                True,
            ),
            DriverSpec(
                "financial",
                "capex-to-revenue bridge",
                "financial",
                "Capex must be bridged to projects, acceptance, utilization, revenue, and cash flow before any capacity interpretation.",
                ("capex", "project mapping", "acceptance or utilization", "revenue bridge", "cash-flow bridge"),
                ("financial_metrics.capex", "financial_metrics.revenue", "financial_metrics.operating_cashflow", "unknown_or_missing_evidence"),
                "Capex is long-term asset investment, not automatic capacity release.",
                "Which projects does capex correspond to, and are acceptance, utilization, revenue, and operating cash-flow bridges disclosed?",
                "Check capex, project mapping, acceptance or utilization, revenue, and operating cash flow.",
                True,
            ),
            DriverSpec(
                "financial",
                "operating cash flow",
                "financial",
                "Operating cash flow tests whether revenue conversion is supported by cash collection.",
                ("operating cash flow", "revenue", "receivables"),
                ("financial_metrics.operating_cashflow", "financial_metrics.revenue", "financial_metrics.accounts_receivable"),
                "Revenue growth without cash conversion remains a research question.",
                "Does operating cash flow support datacenter-related revenue conversion, or are delivery and collection cycles weakening cash quality?",
                "Check operating cash flow, revenue, and receivables.",
                True,
            ),
            DriverSpec(
                "financial",
                "receivables",
                "financial",
                "Receivables help test whether revenue growth is converting into collection.",
                ("accounts receivable", "revenue", "customer/payment-cycle evidence"),
                ("financial_metrics.accounts_receivable", "financial_metrics.revenue", "risk_flags"),
                "Receivables are a cash-quality check, not proof of customer demand.",
                "Are receivables expanding relative to revenue, and do customer payment cycles explain the collection risk?",
                "Check receivables, revenue, customer payment cycle, and collection risk flags.",
                True,
            ),
            DriverSpec(
                "financial",
                "contract liabilities as partial proxy only",
                "financial",
                "Contract liabilities may indicate prepayment visibility but cannot be read as backlog.",
                ("contract liabilities", "customer/order disclosure", "revenue recognition terms"),
                ("financial_metrics.contract_liabilities", "enhanced_must_track_indicators"),
                "Contract liabilities are partial proxy only, not backlog, confirmed orders, or future revenue.",
                "What business and customers do contract liabilities correspond to, and why should they remain only a partial visibility proxy?",
                "Check contract liabilities, customer/order evidence, and revenue recognition terms.",
                True,
            ),
            DriverSpec(
                "financial",
                "depreciation / electricity cost impact",
                "financial",
                "Datacenter capex can create depreciation and power-cost pressure before utilization matures.",
                ("depreciation", "electricity cost", "capex", "gross margin", "operating cash flow"),
                ("financial_metrics.capex", "financial_metrics.gross_margin", "financial_metrics.operating_cashflow", "missing_fields"),
                "Capex and gross margin do not reveal depreciation or electricity-cost impact without direct disclosure.",
                "Are depreciation and electricity-cost impacts disclosed for datacenter projects, and how do they affect margin and cash flow?",
                "Check depreciation, electricity cost, capex, gross margin, and operating cash flow.",
                True,
            ),
            DriverSpec(
                "risk",
                "customer concentration",
                "risk",
                "Concentrated AI/datacenter customers can create order-cut and collection risk.",
                ("customer concentration", "customer revenue share", "order/customer source"),
                ("missing_fields", "risk_flags", "unknown_or_missing_evidence"),
                "Customer capex or market demand cannot substitute for company customer concentration evidence.",
                "Does the company disclose AI/datacenter customer concentration, customer revenue share, or order-cut exposure?",
                "Check customer concentration, revenue share, customer/order source, and risk flags.",
            ),
            DriverSpec(
                "risk",
                "technology route risk",
                "risk",
                "Cooling or power architecture can shift across liquid cooling, air cooling, immersion, or other routes.",
                ("product route", "customer validation stage", "batch order evidence", "revenue split"),
                ("unknown_or_missing_evidence", "enhanced_must_track_indicators", "business_composition"),
                "POC, testing, or certification is not a batch order or realized revenue.",
                "Is the technology route validated by batch orders and revenue split, or only by testing, certification, or POC signals?",
                "Check route disclosure, validation stage, batch orders, and revenue split.",
            ),
            DriverSpec(
                "risk",
                "project delivery / acceptance risk",
                "risk",
                "Project delivery and acceptance determine whether infrastructure work can become recognized revenue.",
                ("project delivery stage", "acceptance evidence", "revenue recognition", "cash collection"),
                ("unknown_or_missing_evidence", "risk_flags", "financial_metrics.operating_cashflow"),
                "Project announcement or construction progress is not revenue without acceptance and recognition evidence.",
                "Which projects have delivery, acceptance, revenue recognition, and cash collection evidence?",
                "Check project delivery, acceptance, revenue recognition, and cash collection.",
            ),
            DriverSpec(
                "risk",
                "policy-to-revenue missing bridge",
                "risk",
                "Policy support remains background unless bridged to company contracts, utilization, revenue, and cash flow.",
                ("policy source", "company contract or project evidence", "revenue bridge", "cash-flow bridge"),
                ("missing_fields", "unknown_or_missing_evidence", "financial_metrics.revenue", "financial_metrics.operating_cashflow"),
                "Policy, news, and theme heat must not be treated as business realization.",
                "What evidence links policy or AI infrastructure demand to company contracts, utilization, revenue, and operating cash flow?",
                "Check policy source, company contract/project evidence, revenue bridge, and cash-flow bridge.",
            ),
        ]

    def _cooling_specs(self) -> list[DriverSpec]:
        return [
            DriverSpec(
                "industry",
                "liquid cooling penetration",
                "industry",
                "Liquid cooling penetration matters only if it converts into company orders, revenue, and delivery.",
                ("industry penetration source", "company liquid-cooling product/order evidence", "revenue split"),
                ("unknown_or_missing_evidence", "enhanced_must_track_indicators", "business_composition"),
                "Industry penetration cannot be treated as company demand without company-level evidence.",
                "Has liquid cooling penetration converted into company-level product orders, delivery, revenue split, and cash collection?",
                "Check industry source, liquid-cooling product/order evidence, revenue split, and cash collection.",
            ),
            DriverSpec(
                "company",
                "liquid cooling revenue",
                "company",
                "Separate liquid-cooling revenue is needed to distinguish liquid cooling from ordinary room or cabinet thermal control.",
                ("liquid-cooling revenue", "period", "gross margin or revenue ratio", "customer/order bridge"),
                ("business_composition", "enhanced_must_track_indicators", "unknown_or_missing_evidence"),
                "Room cooling or cabinet thermal-control revenue must not be relabeled as liquid-cooling revenue without disclosure.",
                "Is liquid-cooling revenue separately disclosed, and how is it bridged to customers, orders, delivery, and cash collection?",
                "Check liquid-cooling revenue, period, gross margin, revenue ratio, customer/order bridge, and ordinary thermal-control boundary.",
            ),
        ]

    def _operator_specs(self) -> list[DriverSpec]:
        return [
            DriverSpec(
                "industry",
                "cabinet / MW buildout",
                "industry",
                "Cabinet and MW scale are operating capacity indicators, not revenue by themselves.",
                ("cabinet count", "MW scale", "project status", "customer contract bridge"),
                ("missing_fields", "unknown_or_missing_evidence", "enhanced_must_track_indicators"),
                "Cabinet or MW buildout is not revenue until rack-up, contract, utilization, and recognition are evidenced.",
                "Are cabinet count, MW scale, project status, customer contracts, and revenue recognition disclosed?",
                "Check cabinet count, MW scale, project status, customer contracts, and revenue recognition.",
            ),
            DriverSpec(
                "industry",
                "customer deployment cycle",
                "industry",
                "Customer deployment pace determines whether datacenter capacity turns into utilization and revenue.",
                ("customer deployment timeline", "rack-up stage", "contract terms", "revenue recognition"),
                ("unknown_or_missing_evidence", "risk_flags", "financial_metrics.revenue"),
                "Customer deployment expectations cannot be treated as revenue without utilization and recognition evidence.",
                "What customer deployment, rack-up, and revenue-recognition milestones are disclosed?",
                "Check deployment timeline, rack-up stage, contract terms, and revenue recognition.",
            ),
            DriverSpec(
                "industry",
                "rack-up / utilization",
                "industry",
                "Utilization is needed to test whether datacenter assets are monetizing.",
                ("rack-up rate", "utilization", "revenue bridge", "cash-flow bridge"),
                ("missing_fields", "unknown_or_missing_evidence", "financial_metrics.revenue", "financial_metrics.operating_cashflow"),
                "Capacity, cabinets, or MW are not utilization and do not prove monetization.",
                "Are rack-up rate and utilization disclosed, and do they bridge to revenue and operating cash flow?",
                "Check rack-up rate, utilization, revenue, and operating cash flow.",
            ),
            DriverSpec(
                "company",
                "PUE / MW / cabinet metrics",
                "company",
                "PUE, MW, and cabinet metrics are core operating disclosures for datacenter operators.",
                ("PUE", "MW scale", "cabinet count", "utilization"),
                ("missing_fields", "unknown_or_missing_evidence", "enhanced_must_track_indicators"),
                "Do not fabricate PUE, MW, cabinet, or utilization metrics when they are absent.",
                "Which PUE, MW, cabinet, and utilization metrics are disclosed, and what period and project do they cover?",
                "Check PUE, MW scale, cabinet count, utilization, period, and project scope.",
            ),
        ]

    def _cxo_drivers(self, pack: dict[str, Any], sub_type: str) -> list[DriverFactor]:
        specs = [*self._cxo_common_specs()]
        if sub_type == "integrated_cxo_platform":
            specs.extend(self._cxo_integrated_specs())
        elif sub_type == "cdmo_manufacturing_services":
            specs.extend(self._cxo_cdmo_specs())
        elif sub_type == "clinical_cro_services":
            specs.extend(self._cxo_clinical_specs())
        return [self._build_driver(pack, spec) for spec in specs]

    def _cxo_common_specs(self) -> list[DriverSpec]:
        return [
            DriverSpec(
                "macro",
                "global biotech / pharma R&D outsourcing demand",
                "macro",
                "Global outsourcing demand is background until bridged to company customers, orders, revenue, and cash collection.",
                ("global biotech funding trend", "pharma R&D outsourcing trend", "company customer or order bridge", "service-line revenue bridge"),
                ("business_composition", "financial_metrics.revenue", "financial_metrics.accounts_receivable", "financial_metrics.operating_cashflow"),
                "Global pharma or biotech demand must not be treated as company demand without company-level evidence.",
                "Has global biotech / pharma R&D outsourcing demand translated into disclosed company customers, orders, service-line revenue, receivables, and cash conversion?",
                "Check global demand source, disclosed customers/orders, service-line revenue, receivables, and operating cash flow.",
            ),
            DriverSpec(
                "macro",
                "pharma R&D budget / biotech funding cycle",
                "macro",
                "Customer budget and biotech funding cycles can affect CXO demand but do not prove company realization.",
                ("pharma R&D budget trend", "biotech funding trend", "customer budget signal", "company order or project bridge"),
                ("business_composition", "financial_metrics.revenue", "financial_metrics.gross_margin"),
                "Customer budgets and funding cycles are context only until linked to company orders, projects, revenue, and collection.",
                "Which customer-budget or biotech-funding evidence is linked to company orders, projects, service-line revenue, and collection?",
                "Check customer budget sources, company orders/projects, revenue bridge, and collection bridge.",
            ),
            DriverSpec(
                "policy",
                "overseas regulatory / Biosecure Act risk",
                "policy",
                "Overseas regulation and Biosecure Act exposure are risk context, not company operating facts without impact evidence.",
                ("official regulatory or policy source", "affected company entity or service line", "customer/order impact", "revenue or cash-flow bridge"),
                ("missing_fields", "unknown_or_missing_evidence", "risk_flags", "business_composition.geography"),
                "Biosecure Act or overseas regulation must not be converted into company performance impact without company-specific evidence.",
                "What evidence shows whether Biosecure Act or overseas regulatory risk has affected company customers, orders, projects, revenue, margin, or collection?",
                "Check official risk source, affected entity, customer/order impact, and financial bridge.",
            ),
            DriverSpec(
                "company",
                "CXO revenue contribution",
                "company",
                "CXO service-line revenue is the first company-level bridge for the CXO framework.",
                ("CXO service revenue contribution", "business composition segment", "period", "gross margin or revenue ratio"),
                ("business_composition", "financial_metrics.revenue", "financial_metrics.gross_margin"),
                "Segment revenue supports exposure, but it does not prove order recovery, customer quality, or future growth.",
                "What CXO / CRO / CDMO service revenue contribution is disclosed by service line, period, revenue ratio, and margin?",
                "Check business composition segments, service-line revenue, period, revenue ratio, and gross margin.",
                True,
            ),
            DriverSpec(
                "company",
                "backlog / new signed orders",
                "company",
                "True backlog and new signed orders test order visibility beyond recognized revenue.",
                ("true backlog or on-hand orders", "new signed orders", "order period", "service line", "customer or project stage", "revenue recognition path"),
                ("missing_fields", "unknown_or_missing_evidence", "enhanced_must_track_indicators", "financial_metrics.contract_liabilities"),
                "Contract liabilities are only a partial proxy and must not substitute for true backlog or new signed orders.",
                "What true backlog and new signed order evidence exists by service line, customer type, project stage, and revenue recognition timing?",
                "Check backlog, new signed orders, service line, customer/project stage, and revenue recognition.",
            ),
            DriverSpec(
                "financial",
                "contract liabilities as partial proxy only",
                "financial",
                "Contract liabilities may show prepayments or visibility, but they are not backlog or confirmed future revenue.",
                ("contract liabilities", "linked customer/order/project disclosure", "prepayment terms", "revenue recognition terms"),
                ("financial_metrics.contract_liabilities", "financial_metrics.revenue", "financial_metrics.operating_cashflow", "enhanced_must_track_indicators"),
                "Contract liabilities are partial proxy only and must not be labeled backlog.",
                "What business, customer, or project do contract liabilities correspond to, and what evidence prevents treating them as true backlog?",
                "Check contract liabilities, linked order/project evidence, prepayment terms, and revenue recognition.",
                True,
            ),
            DriverSpec(
                "risk",
                "customer concentration",
                "risk",
                "Customer concentration can create order volatility, margin pressure, and collection risk.",
                ("top customer revenue share", "major customer changes", "active customer count", "customer geography", "one-off order marker"),
                ("missing_fields", "unknown_or_missing_evidence", "enhanced_must_track_indicators", "risk_flags"),
                "Revenue or segment mix cannot substitute for customer concentration evidence.",
                "Does customer concentration or major-customer change create order, margin, receivable, or one-off revenue risk?",
                "Check top customer share, active customer count, major customer changes, geography, and one-off order markers.",
            ),
            DriverSpec(
                "company",
                "overseas revenue / US customer exposure",
                "company",
                "Overseas and U.S. exposure determine regulatory, customer, FX, and demand-risk follow-up needs.",
                ("overseas revenue share", "U.S. or North America revenue share", "customer geography", "major customer region", "FX exposure"),
                ("business_composition.geography", "missing_fields", "unknown_or_missing_evidence"),
                "Overseas revenue is exposure only; it is not regulatory impact or customer-loss evidence by itself.",
                "How much revenue and customer demand is exposed to overseas and U.S. customers, and how is that linked to revenue, margin, receivables, or cash conversion?",
                "Check geographic revenue, U.S. or North America exposure, customer region, FX exposure, and financial bridge.",
                True,
            ),
            DriverSpec(
                "industry",
                "CDMO capacity utilization",
                "industry",
                "CDMO utilization distinguishes built capacity from absorbed capacity and realized production demand.",
                ("CDMO capacity", "capacity utilization", "commercial-stage project count", "capacity expansion status", "CDMO revenue", "gross margin", "capex bridge"),
                ("missing_fields", "unknown_or_missing_evidence", "enhanced_must_track_indicators", "financial_metrics.capex", "financial_metrics.gross_margin", "business_composition"),
                "Do not infer CDMO utilization from capex, revenue growth, or gross margin without actual utilization or project-stage evidence.",
                "Is CDMO capacity being absorbed by commercial projects and utilization, or does current evidence only show capex, revenue, and margin without utilization bridge?",
                "Check CDMO capacity, utilization, commercial-stage projects, capacity expansion, capex, revenue, margin, and cash bridge.",
            ),
            DriverSpec(
                "industry",
                "clinical project pipeline / project stage",
                "industry",
                "Clinical project count and stage are required before judging clinical CRO pipeline quality.",
                ("clinical project count", "project stage", "project progress or acceptance", "cancellation or delay", "clinical service revenue", "collection status"),
                ("missing_fields", "unknown_or_missing_evidence", "enhanced_must_track_indicators", "business_composition"),
                "Do not fabricate clinical project count or stage from clinical service revenue or company descriptions.",
                "What clinical project count, stage mix, progress, cancellation/delay, and collection evidence validates clinical CRO service demand?",
                "Check clinical project count, stage mix, progress, cancellation/delay, clinical revenue, and collection status.",
            ),
            DriverSpec(
                "risk",
                "one-off large order / project volatility",
                "risk",
                "Large customer or one-off project effects can distort normalized revenue, margin, and cash conversion.",
                ("major customer or product order concentration", "one-off order marker", "project completion or cancellation", "abnormal base-period explanation"),
                ("risk_flags", "missing_fields", "unknown_or_missing_evidence", "enhanced_must_track_indicators", "financial_metrics.revenue"),
                "Growth fields alone cannot prove normalized demand without customer/project evidence.",
                "Is current growth or margin affected by one-off large orders, customer concentration, or project volatility rather than normalized CXO demand?",
                "Check major customer/order concentration, one-off marker, project completion/cancellation, and base-period explanation.",
            ),
            DriverSpec(
                "financial",
                "receivables / collection cycle",
                "financial",
                "Receivables and collection cycle test whether recognized CXO revenue converts into cash.",
                ("accounts receivable", "revenue", "operating cash flow", "collection cycle or DSO", "payment terms"),
                ("financial_metrics.accounts_receivable", "financial_metrics.revenue", "financial_metrics.operating_cashflow", "missing_fields"),
                "Receivables are a cash-quality check, not proof of customer demand.",
                "Are receivables and collection cycle consistent with revenue recognition, or is cash conversion lagging recognized CXO revenue?",
                "Check accounts receivable, revenue, operating cash flow, DSO or payment terms, and customer payment evidence.",
                True,
            ),
            DriverSpec(
                "financial",
                "operating cash flow",
                "financial",
                "Operating cash flow tests whether revenue, project delivery, and collection are converting into cash.",
                ("operating cash flow", "revenue", "accounts receivable", "contract liabilities"),
                ("financial_metrics.operating_cashflow", "financial_metrics.revenue", "financial_metrics.accounts_receivable", "financial_metrics.contract_liabilities"),
                "Revenue growth without cash conversion remains a research question.",
                "Does operating cash flow support recognized CXO revenue, or do receivables and project cycles weaken cash conversion?",
                "Check operating cash flow, revenue, receivables, contract liabilities, and collection quality.",
                True,
            ),
            DriverSpec(
                "financial",
                "capex-to-revenue / utilization bridge",
                "financial",
                "Capex must be bridged to projects, acceptance, utilization, revenue, and cash flow before capacity interpretation.",
                ("capex", "project or capacity mapping", "acceptance or start-up", "utilization", "service-line revenue", "cash-flow bridge"),
                ("financial_metrics.capex", "financial_metrics.revenue", "financial_metrics.operating_cashflow", "business_composition", "unknown_or_missing_evidence"),
                "Capex is investment, not capacity release, utilization, order absorption, or revenue realization.",
                "Which projects or capacity does capex fund, and has the company disclosed acceptance, utilization, revenue, and operating cash-flow bridges?",
                "Check capex, project/capacity mapping, acceptance, utilization, service-line revenue, and operating cash flow.",
                True,
            ),
            DriverSpec(
                "financial",
                "margin and cash conversion",
                "financial",
                "Margin and cash conversion show whether CXO revenue quality is supported by service mix, pricing, and collection.",
                ("gross margin", "net margin", "operating cash flow", "receivables", "contract liabilities", "service-line mix"),
                ("financial_metrics.gross_margin", "financial_metrics.net_margin", "financial_metrics.operating_cashflow", "financial_metrics.accounts_receivable", "financial_metrics.contract_liabilities", "business_composition"),
                "Margin and cash metrics do not prove demand recovery without order, customer, or project evidence.",
                "Do margins and operating cash flow support the quality of CXO revenue, or do receivables, capex, or mix changes indicate weaker cash conversion?",
                "Check gross margin, net margin, operating cash flow, receivables, contract liabilities, and service-line mix.",
                True,
            ),
            DriverSpec(
                "risk",
                "customer loss / project cancellation",
                "risk",
                "Customer loss and project cancellation can affect order visibility, utilization, revenue recognition, and collection.",
                ("customer loss evidence", "project cancellation or delay", "affected service line", "revenue or collection impact"),
                ("risk_flags", "missing_fields", "unknown_or_missing_evidence", "enhanced_must_track_indicators"),
                "Do not infer customer loss or project cancellation without direct disclosure.",
                "What evidence shows customer loss, project cancellation, delay, affected service line, and revenue or collection impact?",
                "Check customer loss, project cancellation/delay, service line, revenue impact, and collection impact.",
            ),
            DriverSpec(
                "risk",
                "overseas regulatory / geopolitical risk",
                "risk",
                "Overseas regulatory and geopolitical risks require company-specific exposure and impact evidence.",
                ("overseas exposure", "U.S. customer exposure", "regulatory event", "company impact disclosure", "financial bridge"),
                ("business_composition.geography", "risk_flags", "missing_fields", "unknown_or_missing_evidence"),
                "Do not treat overseas regulation or geopolitical risk as company performance fact without impact evidence.",
                "Which overseas regulatory or geopolitical exposure has company-specific customer, order, project, revenue, margin, or collection impact evidence?",
                "Check overseas exposure, U.S. customer exposure, regulatory event, company impact disclosure, and financial bridge.",
            ),
            DriverSpec(
                "risk",
                "capacity absorption risk",
                "risk",
                "Capacity absorption risk tests whether invested labs or manufacturing assets are being used by projects and revenue.",
                ("capacity expansion", "utilization", "project stage", "service-line revenue", "cash-flow bridge"),
                ("financial_metrics.capex", "financial_metrics.gross_margin", "financial_metrics.operating_cashflow", "missing_fields", "unknown_or_missing_evidence"),
                "Do not infer capacity absorption from capex or margin without utilization and project-stage evidence.",
                "Does the evidence show capacity expansion being absorbed by utilization, projects, service-line revenue, and operating cash flow?",
                "Check capacity expansion, utilization, project stage, service-line revenue, and cash-flow bridge.",
            ),
            DriverSpec(
                "risk",
                "disclosure gap risk",
                "risk",
                "Disclosure gaps define which CXO driver claims cannot be assessed from the current evidence pack.",
                ("missing driver fields", "source trace", "data limitations", "must-track indicator status"),
                ("missing_fields", "data_limitations", "enhanced_must_track_indicators", "source_trace_summary"),
                "Disclosure gaps must remain research questions and must not be filled with generic industry assumptions.",
                "Which CXO driver fields are missing or only partially evidenced, and what source should verify each gap?",
                "Check missing fields, data limitations, must-track indicators, and source trace summary.",
            ),
        ]

    def _cxo_integrated_specs(self) -> list[DriverSpec]:
        return [
            DriverSpec(
                "company",
                "integrated platform business mix",
                "company",
                "Integrated CXO platforms need service-line mix rather than one homogeneous revenue reading.",
                ("drug discovery revenue", "preclinical service revenue", "CMC / CDMO revenue", "testing or biology revenue", "period"),
                ("business_composition", "enhanced_must_track_indicators"),
                "Total revenue growth does not prove that every integrated CXO segment is improving.",
                "How is integrated CXO platform revenue split across discovery, preclinical, testing, biology, CMC/CDMO, and other service lines?",
                "Check service-line revenue, revenue ratio, margin, and period.",
                True,
            ),
            DriverSpec(
                "company",
                "active customers / platform efficiency",
                "company",
                "Integrated platforms require customer breadth and personnel/platform efficiency evidence.",
                ("active customer count", "major customer changes", "employee or scientist count", "personnel efficiency"),
                ("missing_fields", "unknown_or_missing_evidence", "enhanced_must_track_indicators"),
                "Do not infer customer breadth or personnel efficiency from revenue alone.",
                "What active-customer, major-customer-change, employee, scientist, or personnel-efficiency evidence supports platform quality?",
                "Check active customers, major customer changes, employee/scientist count, and personnel efficiency.",
            ),
        ]

    def _cxo_cdmo_specs(self) -> list[DriverSpec]:
        return [
            DriverSpec(
                "industry",
                "commercial-stage CDMO projects",
                "industry",
                "Commercial-stage project count is needed to distinguish manufacturing visibility from early-stage demand.",
                ("commercial-stage project count", "project stage", "customer or product concentration", "revenue recognition path"),
                ("missing_fields", "unknown_or_missing_evidence", "enhanced_must_track_indicators", "business_composition"),
                "Do not infer commercial-stage project count from CDMO revenue, capex, or margin.",
                "Which commercial-stage CDMO projects, stages, customer/product concentration, and revenue-recognition paths are disclosed?",
                "Check commercial-stage project count, project stage, customer/product concentration, and revenue recognition.",
            ),
            DriverSpec(
                "risk",
                "GMP / FDA / NMPA compliance event",
                "risk",
                "Compliance events can affect manufacturing continuity, customer trust, and delivery.",
                ("GMP / FDA / NMPA compliance event", "affected facility or service line", "remediation status", "customer/order impact"),
                ("missing_fields", "unknown_or_missing_evidence", "risk_flags", "enhanced_must_track_indicators"),
                "Do not fabricate compliance events or company impact without source-traced disclosure.",
                "Are there GMP / FDA / NMPA compliance events, and what facility, service line, remediation status, or customer/order impact is disclosed?",
                "Check compliance events, affected facility/service line, remediation, and customer/order impact.",
            ),
        ]

    def _cxo_clinical_specs(self) -> list[DriverSpec]:
        return [
            DriverSpec(
                "company",
                "SMO / data-statistics revenue",
                "company",
                "Clinical CRO sub-type needs clinical service-line mix beyond total revenue.",
                ("clinical trial service revenue", "SMO revenue", "data-statistics revenue", "period", "project delivery bridge"),
                ("business_composition", "enhanced_must_track_indicators", "financial_metrics.revenue"),
                "Clinical service revenue does not prove project stage or delivery quality without project evidence.",
                "What clinical trial, SMO, or data-statistics revenue is disclosed, and how is it linked to project delivery and collection?",
                "Check clinical service-line revenue, period, project delivery, and collection.",
                True,
            ),
            DriverSpec(
                "risk",
                "clinical project delivery / collection",
                "risk",
                "Clinical project delivery and collection determine whether projects become high-quality revenue and cash.",
                ("project delivery progress", "acceptance or milestone", "project cancellation or delay", "receivables", "collection cycle"),
                ("missing_fields", "unknown_or_missing_evidence", "enhanced_must_track_indicators", "financial_metrics.accounts_receivable", "financial_metrics.operating_cashflow"),
                "Do not judge clinical project delivery or collection cycle without project and payment evidence.",
                "Which clinical projects have delivery progress, milestones, cancellation/delay status, receivables, and collection evidence?",
                "Check delivery progress, milestone/acceptance, cancellation/delay, receivables, and collection cycle.",
            ),
        ]

    def _satellite_drivers(self, pack: dict[str, Any]) -> list[DriverFactor]:
        return [self._build_driver(pack, spec) for spec in self._satellite_specs()]

    def _low_altitude_drivers(self, pack: dict[str, Any], sub_type: str) -> list[DriverFactor]:
        if sub_type != "aviation_operations_service":
            return [self._unsupported_driver(LOW_ALTITUDE_STRATEGY_TYPE, sub_type)]
        return [self._build_driver(pack, spec) for spec in self._low_altitude_aviation_specs()]

    def _low_altitude_aviation_specs(self) -> list[DriverSpec]:
        return [
            DriverSpec(
                "policy",
                "low-altitude policy pilot progress",
                "macro_policy_industry",
                "Policy pilots are context until linked to company routes, projects, contracts, revenue, and collection.",
                ("official policy pilot list", "pilot scope", "company-specific participation", "project / contract / revenue / collection bridge"),
                ("missing_fields", "unknown_or_missing_evidence", "risk_flags", "enhanced_must_track_indicators"),
                "Policy pilot progress is not company revenue, and must not be written as low-altitude policy improves so the company benefits.",
                "Which policy pilots are tied to company-specific routes, bases, projects, contracts, revenue recognition, or collection evidence?",
                "Check official policy pilot, company participation, project/contract evidence, revenue recognition, and collection.",
            ),
            DriverSpec(
                "policy",
                "airspace / route approval",
                "macro_policy_industry",
                "Airspace and route approval determine whether policy context becomes company-usable operating resources.",
                ("approved airspace", "route approval", "operating permission", "base or takeoff / landing site rights", "company operating volume bridge"),
                ("missing_fields", "unknown_or_missing_evidence", "enhanced_must_track_indicators", "basic_info.main_business"),
                "Airspace reform is not company-usable airspace without company-level approval, route, base, or operation-right evidence.",
                "What company-usable airspace, route, base, or takeoff / landing resources have been approved, and how do they connect to flight volume and revenue?",
                "Check airspace approval, route approval, operating permission, base resources, and operating-volume bridge.",
            ),
            DriverSpec(
                "policy",
                "local government low-altitude infrastructure spending",
                "macro_policy_industry",
                "Local government spending matters only when linked to company contracts, acceptance, revenue, and collection.",
                ("budget / tender / procurement project", "project owner", "winning bidder", "company contract amount", "delivery / acceptance", "revenue and collection bridge"),
                ("financial_metrics.revenue", "financial_metrics.accounts_receivable", "financial_metrics.operating_cashflow", "financial_metrics.contract_liabilities", "business_composition"),
                "Local-government spending plans are not company revenue without contract, acceptance, revenue, and collection evidence.",
                "Has local government low-altitude spending converted into disclosed company contracts, accepted projects, revenue, receivables, and cash collection?",
                "Check procurement project, company contract, acceptance, revenue, receivables, and cash collection.",
            ),
            DriverSpec(
                "policy",
                "aviation safety / regulatory requirements",
                "macro_policy_industry",
                "Safety and regulatory requirements can affect service continuity, compliance cost, and operating permissions.",
                ("operating licenses", "safety-management disclosures", "accident / incident history", "CAAC penalties", "compliance cost", "grounding / rectification events"),
                ("missing_fields", "risk_flags", "enhanced_must_track_indicators", "data_limitations"),
                "Safety and compliance are constraints; absence of event data is not proof of safe operations.",
                "What safety, license, penalty, rectification, or compliance-cost evidence affects service continuity, cost structure, or operating risk?",
                "Check licenses, safety events, penalties, rectification, and compliance cost.",
            ),
            DriverSpec(
                "industry",
                "low-altitude operation demand",
                "macro_policy_industry",
                "Low-altitude demand is useful only if bridged to company customers, routes, flight hours, sorties, revenue, and cash flow.",
                ("demand by emergency rescue / offshore oil / tourism / logistics / inspection", "company customer bridge", "route bridge", "flight-hour or sortie bridge", "revenue and cash-flow bridge"),
                ("business_composition", "financial_metrics.revenue", "financial_metrics.gross_margin", "financial_metrics.operating_cashflow", "financial_metrics.accounts_receivable"),
                "Industry demand is not company demand unless the company customer, route, operating-volume, revenue, and cash-flow bridge is evidenced.",
                "Which low-altitude demand categories have translated into company customers, routes, flight hours, sorties, revenue, receivables, and cash flow?",
                "Check customer demand category, company customers, routes, flight hours, sorties, revenue, receivables, and cash flow.",
            ),
            DriverSpec(
                "company",
                "low-altitude / general aviation / air-traffic-management revenue contribution",
                "company_operating",
                "Service-line revenue contribution is the first company-level bridge for low-altitude infrastructure or operation exposure.",
                ("segment revenue", "revenue ratio", "segment gross margin", "service-line description", "period", "sub-type routing"),
                ("basic_info.main_business", "business_composition", "financial_metrics.revenue", "financial_metrics.gross_margin"),
                "Business composition supports exposure only; it does not prove flight utilization, route quality, customer stability, or project acceptance.",
                "What share of revenue is directly tied to low-altitude, general aviation, or air-traffic-management services, and what period and segment definition support it?",
                "Check main business, business composition, revenue ratio, segment gross margin, period, and sub_type.",
                True,
            ),
            DriverSpec(
                "company",
                "flight hours",
                "company_operating",
                "Flight hours validate utilization and demand realization for aviation operation services.",
                ("disclosed flight hours by period", "service type", "aircraft / route / customer mapping", "revenue and cash-flow bridge"),
                ("missing_fields", "unknown_or_missing_evidence", "enhanced_must_track_indicators", "financial_metrics.revenue"),
                "Do not infer operating capability, utilization, demand stability, or revenue per flight hour when flight hours are missing.",
                "What disclosed flight hours validate utilization and demand realization, and how do they connect to revenue and cash conversion?",
                "Check flight hours, period, service type, aircraft/route/customer mapping, revenue, and cash-flow bridge.",
            ),
            DriverSpec(
                "company",
                "flight sorties",
                "company_operating",
                "Flight sorties validate actual service volume by mission and customer type.",
                ("disclosed flight sorties by period", "mission type", "customer / route mapping", "revenue and cash-flow bridge"),
                ("missing_fields", "unknown_or_missing_evidence", "enhanced_must_track_indicators", "financial_metrics.revenue"),
                "Do not write service volume as fact without flight-sortie evidence.",
                "What flight-sortie data validates actual service volume by mission type and customer, and how does it bridge to revenue?",
                "Check flight sorties, mission type, route/customer mapping, revenue, and cash-flow bridge.",
            ),
            DriverSpec(
                "company",
                "platform dispatch volume",
                "company_operating",
                "Dispatch volume is relevant only when the company operates a low-altitude platform and discloses usage.",
                ("dispatch volume", "platform users", "route / airspace / aircraft coverage", "recurring platform revenue", "project acceptance"),
                ("missing_fields", "unknown_or_missing_evidence", "enhanced_must_track_indicators", "business_composition"),
                "Do not infer platform usage from project labels, revenue, or aviation-operation subtype unless dispatch volume is disclosed.",
                "If a platform exists, what dispatch volume and monetization evidence supports platform utilization?",
                "Check dispatch volume, platform users, coverage, recurring platform revenue, and acceptance.",
            ),
            DriverSpec(
                "company",
                "route / base / airspace resources",
                "company_operating",
                "Routes, bases, takeoff / landing sites, and airspace permissions define operating-resource access.",
                ("route list", "base list", "takeoff / landing sites", "usable airspace", "operating permissions", "coverage", "utilization"),
                ("missing_fields", "unknown_or_missing_evidence", "enhanced_must_track_indicators", "basic_info.main_business"),
                "Do not convert operating-service description into route, base, or scarce airspace-resource control.",
                "What routes, bases, takeoff / landing sites, and airspace resources does the company control, and how are they used?",
                "Check routes, bases, takeoff/landing sites, usable airspace, operating permissions, coverage, and utilization.",
            ),
            DriverSpec(
                "company",
                "project contracts",
                "company_operating",
                "Signed project contracts are required before treating low-altitude project demand as company visibility.",
                ("signed contract", "customer", "amount", "period", "service scope", "revenue-recognition terms", "collection schedule"),
                ("financial_metrics.contract_liabilities", "business_composition", "financial_metrics.revenue", "missing_fields", "unknown_or_missing_evidence"),
                "Contract liabilities are partial proxy only; strategic cooperation or framework agreement is not signed contract revenue and not backlog.",
                "Which contracts support low-altitude or general aviation service revenue, and what amount, customer, scope, and timing are disclosed?",
                "Check signed contracts, customers, amount, period, service scope, revenue recognition, and collection schedule.",
            ),
            DriverSpec(
                "company",
                "project acceptance / delivery",
                "company_operating",
                "Acceptance and delivery milestones determine whether projects can become recognized revenue and collectable cash.",
                ("delivery milestone", "acceptance certificate", "accepted amount", "revenue recognition", "customer payment", "unresolved delivery risk"),
                ("financial_metrics.revenue", "financial_metrics.accounts_receivable", "financial_metrics.operating_cashflow", "missing_fields", "unknown_or_missing_evidence"),
                "Do not treat project announcement, winning bid, or contract signing as acceptance.",
                "Which projects have been delivered and accepted, and how is acceptance linked to revenue recognition and cash collection?",
                "Check delivery milestone, acceptance certificate, accepted amount, revenue recognition, customer payment, and delivery risk.",
            ),
            DriverSpec(
                "company",
                "customer type",
                "company_operating",
                "Customer type and concentration determine demand durability, collection risk, and policy dependence.",
                ("customer split by government / SOE / enterprise / emergency rescue / offshore oil / tourism / logistics / inspection", "revenue concentration", "receivable concentration", "payment terms"),
                ("financial_metrics.accounts_receivable", "financial_metrics.operating_cashflow", "business_composition", "missing_fields", "risk_flags"),
                "Government or SOE customer type does not imply payment certainty, and segment revenue cannot substitute for customer structure.",
                "What customer types drive revenue, receivables, and cash collection, and where is government or SOE payment-cycle risk concentrated?",
                "Check customer type, revenue concentration, receivable concentration, payment terms, receivables, and operating cash flow.",
            ),
            DriverSpec(
                "financial",
                "revenue stability",
                "financial",
                "Revenue stability requires contract duration, customer concentration, operating volume, renewals, and cash collection beyond revenue snapshots.",
                ("revenue by period", "segment revenue", "contract duration", "customer concentration", "flight hours / sorties", "renewal or recurring service evidence"),
                ("financial_metrics.revenue", "business_composition", "financial_metrics.operating_cashflow", "financial_metrics.accounts_receivable", "missing_fields"),
                "Historical revenue alone is not stability proof without contracts, customers, flight hours, sorties, renewal evidence, and collection.",
                "Is revenue stability supported by contracts, customers, flight hours or sorties, renewal evidence, and cash collection, or only by historical revenue fields?",
                "Check revenue, segment revenue, contract duration, customer concentration, flight hours/sorties, renewals, receivables, and cash flow.",
            ),
            DriverSpec(
                "financial",
                "gross margin stability",
                "financial",
                "Gross margin stability needs period comparison and service mix, aircraft utilization, pricing, maintenance, depreciation, and compliance-cost bridges.",
                ("gross margin by period", "segment gross margin", "service mix", "aircraft utilization", "fuel / maintenance / depreciation cost", "pricing terms"),
                ("financial_metrics.gross_margin", "business_composition", "missing_fields", "risk_flags"),
                "Do not infer pricing power, utilization, or stable service mix from gross margin alone.",
                "Is gross margin stability explained by service mix, aircraft utilization, pricing, maintenance, depreciation, and compliance cost?",
                "Check gross margin, segment gross margin, service mix, utilization, cost detail, pricing terms, and period comparison.",
            ),
            DriverSpec(
                "financial",
                "operating cash flow",
                "financial",
                "Operating cash flow tests whether service revenue converts into cash after receivables and contract-liability context.",
                ("operating cash flow", "revenue", "receivables", "contract liabilities", "customer payment terms", "project collection history"),
                ("financial_metrics.operating_cashflow", "financial_metrics.revenue", "financial_metrics.accounts_receivable", "financial_metrics.contract_liabilities"),
                "Cash flow is validation evidence, not proof of demand durability or customer payment certainty.",
                "Does operating cash flow support revenue quality after considering receivables, contract liabilities, customer type, and collection cycle?",
                "Check operating cash flow, revenue, receivables, contract liabilities, customer payment terms, and project collection history.",
                True,
            ),
            DriverSpec(
                "financial",
                "receivables",
                "financial",
                "Receivables test collection pressure after service revenue recognition.",
                ("accounts receivable", "revenue", "receivable aging", "bad-debt provision", "customer concentration", "government / SOE exposure", "operating cash flow"),
                ("financial_metrics.accounts_receivable", "financial_metrics.revenue", "financial_metrics.operating_cashflow", "missing_fields", "risk_flags"),
                "Recognized revenue and government customer labels do not guarantee collection.",
                "Are receivables consistent with recognized service revenue, or do aging, concentration, and payment terms indicate collection pressure?",
                "Check accounts receivable, revenue, receivable aging, bad-debt provision, customer concentration, customer type, and operating cash flow.",
                True,
            ),
            DriverSpec(
                "financial",
                "government / SOE collection cycle",
                "financial",
                "Government and SOE collection cycle requires customer type, acceptance, payment terms, receivable aging, and cash receipts.",
                ("customer type", "payment terms", "project acceptance", "receivable aging", "overdue receivables", "cash receipts by customer or project"),
                ("financial_metrics.accounts_receivable", "financial_metrics.operating_cashflow", "missing_fields", "risk_flags"),
                "Do not treat government or SOE customers as payment certainty; receivables alone cannot establish collection cycle.",
                "How long is the collection cycle for government or SOE customers, and is payment delayed after project acceptance or service delivery?",
                "Check customer type, payment terms, project acceptance, receivable aging, overdue receivables, and cash receipts by customer/project.",
            ),
            DriverSpec(
                "financial",
                "contract liabilities as partial proxy only",
                "financial",
                "Contract liabilities may show prepayments or visibility, but they are not backlog or confirmed future revenue.",
                ("contract liabilities", "prepayment terms", "linked customer / contract / project disclosure", "revenue recognition terms", "comparison with revenue and cash flow"),
                ("financial_metrics.contract_liabilities", "financial_metrics.revenue", "financial_metrics.operating_cashflow", "enhanced_must_track_indicators"),
                "Contract liabilities are partial proxy only and must not be labeled backlog.",
                "What customer, contract, or project do contract liabilities correspond to, and why should they not be treated as true backlog?",
                "Check contract liabilities, prepayment terms, linked customer/contract/project disclosure, revenue recognition, revenue, and cash flow.",
                True,
            ),
            DriverSpec(
                "financial",
                "capex-to-service-capacity bridge",
                "financial",
                "Capex must be bridged to aircraft, bases, routes, platforms, acceptance, utilization, revenue, and cash flow before capacity interpretation.",
                ("capex", "aircraft / base / platform / project mapping", "delivery / acceptance", "flight hours / sorties", "utilization", "revenue and cash-flow bridge"),
                ("financial_metrics.capex", "financial_metrics.revenue", "financial_metrics.operating_cashflow", "business_composition", "missing_fields"),
                "Capex is cash outflow or investment observation only; it is not service-capacity release, utilization, flight-hour growth, or revenue conversion.",
                "Which aircraft, bases, routes, platforms, or projects does capex fund, and has the company disclosed acceptance, utilization, revenue, and cash-flow bridges?",
                "Check capex, asset/project mapping, acceptance, flight hours/sorties, utilization, revenue, and operating cash flow.",
                True,
            ),
            DriverSpec(
                "financial",
                "safety / compliance cost",
                "financial",
                "Safety and compliance costs can affect service continuity, gross margin, and cash conversion.",
                ("safety-management cost", "maintenance cost", "training cost", "insurance cost", "regulatory penalty", "rectification cost", "impact on margin and cash flow"),
                ("financial_metrics.gross_margin", "financial_metrics.operating_cashflow", "missing_fields", "risk_flags", "data_limitations"),
                "Do not infer safety-cost burden or absence from aggregate gross margin or cash flow alone.",
                "What safety and compliance costs affect service continuity, gross margin, and cash conversion?",
                "Check safety-management cost, maintenance cost, training cost, insurance cost, regulatory penalty, rectification cost, margin, and cash flow.",
            ),
            DriverSpec(
                "risk",
                "airspace approval delay",
                "risk",
                "Airspace or route approval delays can affect flight volume, route launch, service continuity, and revenue timing.",
                ("approval applications", "route / airspace approval status", "delay events", "affected service or project", "revenue impact"),
                ("missing_fields", "unknown_or_missing_evidence", "risk_flags", "basic_info.main_business"),
                "Do not infer approved airspace or absence of delay from policy direction.",
                "Are any airspace or route approvals delayed, and which services, projects, flight volumes, or revenues are affected?",
                "Check approval applications, route/airspace status, delay events, affected service/project, and revenue impact.",
            ),
            DriverSpec(
                "risk",
                "project acceptance delay",
                "risk",
                "Project acceptance delays can affect revenue recognition, receivables, and cash collection.",
                ("project list", "expected acceptance date", "actual acceptance", "delay reason", "revenue recognition and payment impact"),
                ("financial_metrics.revenue", "financial_metrics.accounts_receivable", "financial_metrics.operating_cashflow", "missing_fields", "risk_flags"),
                "Project announcement is not acceptance, and delivery is not collection.",
                "Which projects are waiting for acceptance, and how would delays affect revenue recognition, receivables, and cash flow?",
                "Check project list, expected and actual acceptance, delay reason, revenue recognition, receivables, and payment impact.",
            ),
            DriverSpec(
                "risk",
                "safety incident / regulatory penalty",
                "risk",
                "Safety incidents and regulatory penalties can affect service continuity, cost, insurance, licenses, and customer confidence.",
                ("accident / incident", "CAAC penalty", "grounding / rectification", "insurance claim", "service interruption", "financial impact"),
                ("missing_fields", "risk_flags", "unknown_or_missing_evidence", "enhanced_must_track_indicators"),
                "Absence of event evidence is not evidence of safe operations.",
                "Have safety incidents, penalties, grounding, or rectification events affected operations, costs, or customer service continuity?",
                "Check accident/incident records, CAAC penalties, grounding, rectification, insurance, service interruption, and financial impact.",
            ),
            DriverSpec(
                "risk",
                "government payment delay",
                "risk",
                "Government payment delay requires customer type, acceptance, payment schedule, overdue receivables, aging, and cash-flow pressure.",
                ("customer type", "project acceptance", "payment schedule", "overdue receivables", "receivable aging", "operating cash-flow pressure"),
                ("financial_metrics.accounts_receivable", "financial_metrics.operating_cashflow", "missing_fields", "risk_flags"),
                "Government customer exposure is not collection certainty; receivables alone cannot prove payment delay or payment quality.",
                "Is there evidence of government payment delay after service delivery or project acceptance, and how does it affect operating cash flow?",
                "Check customer type, project acceptance, payment schedule, overdue receivables, aging, and operating cash flow.",
            ),
            DriverSpec(
                "risk",
                "utilization / flight-hour insufficiency",
                "risk",
                "Utilization and flight-hour sufficiency determine whether fleet and route capacity are actually used.",
                ("fleet scale", "aircraft type mix", "flight hours", "flight sorties", "route / base usage", "revenue per flight hour"),
                ("missing_fields", "unknown_or_missing_evidence", "enhanced_must_track_indicators", "financial_metrics.revenue"),
                "Revenue cannot substitute for utilization, flight hours, sorties, or revenue per flight hour.",
                "Does operating volume support fleet and service-capacity utilization, or is utilization not assessable from current evidence?",
                "Check fleet scale, aircraft type mix, flight hours, flight sorties, route/base usage, and revenue per flight hour.",
            ),
            DriverSpec(
                "risk",
                "policy pilot does not convert into company revenue",
                "risk",
                "Policy pilot conversion risk tests whether policy context has become contracts, accepted projects, revenue, and collection.",
                ("policy pilot", "company project role", "contract", "acceptance", "revenue recognition", "collection"),
                ("missing_fields", "unknown_or_missing_evidence", "financial_metrics.revenue", "financial_metrics.operating_cashflow", "risk_flags"),
                "Do not treat policy pilot as project income without company contract, acceptance, revenue, and collection bridge.",
                "Which policy pilots have failed or not yet proven conversion into company contracts, accepted projects, revenue, and cash collection?",
                "Check policy pilot, company project role, contract, acceptance, revenue recognition, and collection.",
            ),
            DriverSpec(
                "risk",
                "customer concentration",
                "risk",
                "Customer concentration can create renewal, pricing, receivable, and one-off revenue risk.",
                ("top customer share", "customer count", "customer type", "revenue concentration", "receivable concentration", "renewal / contract duration"),
                ("financial_metrics.accounts_receivable", "missing_fields", "risk_flags", "unknown_or_missing_evidence", "enhanced_must_track_indicators"),
                "Segment revenue or industry labels cannot substitute for customer concentration evidence.",
                "Does customer concentration create renewal, pricing, receivable, or one-off revenue risk?",
                "Check top customer share, customer count, customer type, revenue concentration, receivable concentration, renewal, and contract duration.",
            ),
            DriverSpec(
                "risk",
                "weather / operational disruption risk",
                "risk",
                "Weather and operational disruption can affect flight hours, sorties, service delivery, cost, and customer continuity.",
                ("weather disruptions", "route cancellation", "mission delay", "service interruption", "seasonal operating data", "revenue / cost impact"),
                ("missing_fields", "risk_flags", "unknown_or_missing_evidence", "data_limitations"),
                "Do not infer operational continuity from annual revenue alone.",
                "What weather or operational disruptions affect flight hours, sorties, service delivery, cost, or customer continuity?",
                "Check weather disruptions, route cancellation, mission delay, service interruption, seasonal data, and revenue/cost impact.",
            ),
        ]

    def _satellite_specs(self) -> list[DriverSpec]:
        return [
            DriverSpec(
                "macro",
                "satellite communication demand",
                "macro",
                "Satellite communication demand is background until bridged to company customers, contracts, utilization, revenue, and cash collection.",
                ("satellite communication demand series", "application demand", "company customer or contract bridge", "capacity utilization bridge", "revenue bridge"),
                ("business_composition", "financial_metrics.revenue", "financial_metrics.operating_cashflow", "financial_metrics.accounts_receivable"),
                "Satellite communication demand must not be treated as company revenue without company-level customer, contract, utilization, and cash-flow evidence.",
                "Has satellite communication demand translated into disclosed company customers, contracts, capacity utilization, revenue, receivables, and operating cash flow?",
                "Check demand source, company customer/contract bridge, utilization, revenue, receivables, and operating cash flow.",
            ),
            DriverSpec(
                "policy",
                "national satellite communication infrastructure policy",
                "policy",
                "National policy can shape infrastructure context, but policy support is not business realization.",
                ("official policy source", "affected infrastructure segment", "company license or project evidence", "company contract evidence", "revenue or cash-flow bridge"),
                ("missing_fields", "unknown_or_missing_evidence", "risk_flags", "enhanced_must_track_indicators"),
                "Policy support is not business realization without company-specific project, contract, revenue, or cash-flow evidence.",
                "Which national satellite communication infrastructure policies are linked to company-specific licenses, projects, contracts, revenue recognition, or cash collection?",
                "Check official policy source, company license/project evidence, contract evidence, revenue bridge, and cash-flow bridge.",
            ),
            DriverSpec(
                "industry",
                "bandwidth / transponder capacity demand",
                "industry",
                "Bandwidth and transponder demand matter only when company capacity, utilization, pricing, and revenue bridge are evidenced.",
                ("bandwidth demand source", "transponder demand source", "company transponder or bandwidth resources", "capacity utilization", "lease or service pricing"),
                ("business_composition", "financial_metrics.revenue", "financial_metrics.gross_margin", "missing_fields", "risk_flags"),
                "External bandwidth or transponder demand cannot prove company utilization, pricing, or revenue.",
                "Is external bandwidth / transponder demand visible in company capacity utilization, service pricing, contract renewals, revenue, margin, and cash flow?",
                "Check bandwidth/transponder demand, company capacity resources, utilization, pricing, revenue, margin, and cash flow.",
            ),
            DriverSpec(
                "industry",
                "enterprise / broadcast / emergency communication demand",
                "industry",
                "Customer-segment demand requires contract, renewal, pricing, receivable, and cash-flow evidence before it can support company realization.",
                ("enterprise demand", "broadcast demand", "emergency communication demand", "customer contract duration", "collection quality"),
                ("business_composition", "financial_metrics.revenue", "financial_metrics.operating_cashflow", "financial_metrics.accounts_receivable"),
                "Customer category labels do not prove demand stability, renewal quality, pricing, or collection.",
                "Which enterprise, broadcast, or emergency communication customers support revenue, and are contract duration, renewal, pricing, receivables, and cash collection evidenced?",
                "Check customer segment demand, contract duration, renewal, pricing, receivables, and cash collection.",
            ),
            DriverSpec(
                "company",
                "satellite resources",
                "company",
                "Satellite resources define the asset base, but resource ownership does not prove productive utilization or monetization.",
                ("in-orbit satellite list", "ownership or control", "orbital slot or frequency resources", "service scope", "capacity mapped to revenue"),
                ("basic_info.main_business", "basic_info.industry", "business_composition", "missing_fields", "risk_flags"),
                "Main-business text or satellite-resource language cannot prove sufficient resources, utilization, or revenue conversion.",
                "What satellite resources, orbital/frequency rights, and service scope does the company control, and how are they linked to service revenue and operating cash flow?",
                "Check in-orbit satellites, ownership/control, orbital/frequency resources, service scope, capacity map, revenue, and operating cash flow.",
            ),
            DriverSpec(
                "company",
                "transponder / bandwidth resources",
                "company",
                "Transponder and bandwidth resources are needed before assessing space-segment monetization capacity.",
                ("transponder count", "bandwidth capacity", "capacity by band", "available versus leased capacity", "service region"),
                ("business_composition", "financial_metrics.revenue", "missing_fields", "risk_flags"),
                "Do not infer transponder or bandwidth resources from revenue or business composition alone.",
                "What transponder and bandwidth resources are available, and which part is monetized by disclosed contracts or service revenue?",
                "Check transponder count, bandwidth capacity, capacity by band, available/leased split, service region, contracts, and service revenue.",
            ),
            DriverSpec(
                "company",
                "capacity utilization",
                "company",
                "Capacity utilization distinguishes available satellite capacity from revenue-generating capacity.",
                ("capacity utilization rate", "lease rate", "bandwidth sold versus available", "utilization by satellite or band", "revenue and margin bridge"),
                ("missing_fields", "unknown_or_missing_evidence", "risk_flags", "financial_metrics.revenue", "financial_metrics.gross_margin"),
                "Capacity resources, revenue, gross margin, or capex are not capacity utilization.",
                "Are satellite resources being used at disclosed utilization levels, and how does utilization connect to revenue, margin, receivables, and cash flow?",
                "Check utilization rate, lease rate, sold/available bandwidth, utilization by satellite or band, revenue, margin, receivables, and cash flow.",
            ),
            DriverSpec(
                "company",
                "customer contract duration",
                "company",
                "Contract duration and renewal terms are required before assessing revenue visibility.",
                ("contract start and end dates", "average contract duration", "renewal terms", "customer type", "revenue recognition schedule"),
                ("financial_metrics.contract_liabilities", "business_composition", "missing_fields", "risk_flags"),
                "Contract liabilities and segment revenue cannot establish contract duration or renewal visibility.",
                "What are the contract durations and renewal terms for satellite communication customers, and how do they support or weaken revenue visibility?",
                "Check customer contracts, duration, renewal terms, customer type, and revenue recognition schedule.",
            ),
            DriverSpec(
                "company",
                "lease / service pricing",
                "company",
                "Lease and service pricing are needed to distinguish pricing quality from accounting margin snapshots.",
                ("unit bandwidth price", "transponder lease price", "service pricing formula", "price changes", "customer mix", "gross margin bridge"),
                ("financial_metrics.gross_margin", "business_composition", "missing_fields", "risk_flags"),
                "Gross margin alone cannot prove lease price, service pricing, or pricing power.",
                "What evidence shows lease or service pricing by capacity type, and is pricing pressure visible in gross margin or customer mix?",
                "Check unit bandwidth price, transponder lease price, service pricing formula, price changes, customer mix, and gross margin bridge.",
            ),
            DriverSpec(
                "risk",
                "customer concentration",
                "risk",
                "Customer concentration can create renewal, pricing, receivable, and one-off revenue risk.",
                ("top customer revenue share", "customer count", "customer type", "contract concentration", "receivable concentration"),
                ("missing_fields", "risk_flags", "unknown_or_missing_evidence", "enhanced_must_track_indicators", "financial_metrics.accounts_receivable"),
                "Segment revenue or industry labels cannot substitute for customer concentration evidence.",
                "Does customer concentration create renewal, pricing, receivable, or one-off revenue risk?",
                "Check top customer share, customer count, customer type, contract concentration, receivable concentration, and collection quality.",
            ),
            DriverSpec(
                "financial",
                "revenue stability",
                "financial",
                "Revenue stability needs customer contract duration, renewal, customer concentration, utilization, and cash collection evidence.",
                ("revenue by period", "segment revenue", "customer contract duration", "renewal rate", "customer concentration", "utilization bridge"),
                ("financial_metrics.revenue", "business_composition", "financial_metrics.operating_cashflow", "financial_metrics.accounts_receivable", "missing_fields"),
                "Do not state revenue stability as fact when customer contracts, renewal, concentration, and utilization are missing.",
                "Is revenue stability supported by contract duration, renewal evidence, utilization, customer concentration, and cash collection, or only by historical revenue fields?",
                "Check revenue, segment revenue, contract duration, renewal rate, customer concentration, utilization, receivables, and cash flow.",
            ),
            DriverSpec(
                "financial",
                "gross margin stability",
                "financial",
                "Gross margin stability requires period comparison plus pricing, utilization, customer mix, and depreciation context.",
                ("gross margin by period", "segment gross margin", "pricing", "capacity utilization", "depreciation policy", "customer mix"),
                ("financial_metrics.gross_margin", "business_composition", "missing_fields", "risk_flags"),
                "Gross margin alone cannot prove pricing power or stable utilization.",
                "Is gross margin stability explained by pricing, utilization, customer mix, and depreciation, or is current evidence only a financial snapshot?",
                "Check gross margin by period, segment gross margin, pricing, utilization, depreciation policy, and customer mix.",
            ),
            DriverSpec(
                "financial",
                "capex",
                "financial",
                "Capex can indicate long-term asset investment, but it does not prove launch success, in-orbit operation, utilization, or revenue conversion.",
                ("capex", "project or satellite mapping", "procurement or launch progress", "acceptance or in-orbit status", "revenue and cash-flow bridge"),
                ("financial_metrics.capex", "financial_metrics.revenue", "financial_metrics.operating_cashflow", "missing_fields", "risk_flags"),
                "Capex is cash outflow only; it is not satellite deployment success, capacity release, utilization, or revenue.",
                "Which satellites, projects, or assets does capex fund, and has the company disclosed launch, in-orbit status, utilization, revenue, and cash-flow bridges?",
                "Check capex, project/satellite mapping, procurement, launch progress, in-orbit status, utilization, revenue, and cash flow.",
                True,
            ),
            DriverSpec(
                "financial",
                "depreciation",
                "financial",
                "Depreciation and useful-life policy are critical for asset-heavy satellite operators.",
                ("depreciation or amortization amount", "satellite asset depreciation policy", "satellite useful life", "impairment", "segment asset detail"),
                ("financial_metrics.depreciation_amortization", "missing_fields", "risk_flags", "financial_metrics.gross_margin"),
                "Profitability comparisons must not ignore missing depreciation, amortization, impairment, and satellite useful-life policy.",
                "How do depreciation policy and satellite useful life affect reported profit and margin quality?",
                "Check depreciation/amortization, satellite asset policy, useful life, impairment, segment asset detail, and gross margin.",
            ),
            DriverSpec(
                "financial",
                "operating cash flow",
                "financial",
                "Operating cash flow tests whether recognized satellite communication revenue converts into cash.",
                ("operating cash flow", "revenue", "receivables", "contract liabilities", "customer payment terms", "collection history"),
                ("financial_metrics.operating_cashflow", "financial_metrics.revenue", "financial_metrics.accounts_receivable", "financial_metrics.contract_liabilities"),
                "Cash-flow quality is a validation question and does not prove stable demand by itself.",
                "Does operating cash flow support revenue quality after considering receivables, contract liabilities, customer payment terms, and capex needs?",
                "Check operating cash flow, revenue, receivables, contract liabilities, payment terms, collection history, and capex needs.",
                True,
            ),
            DriverSpec(
                "financial",
                "receivables",
                "financial",
                "Receivables help test customer payment quality and collection risk.",
                ("accounts receivable", "revenue", "customer concentration", "aging", "bad-debt provision", "payment terms", "operating cash flow"),
                ("financial_metrics.accounts_receivable", "financial_metrics.revenue", "financial_metrics.operating_cashflow", "missing_fields", "risk_flags"),
                "Do not infer customer quality or collection stability without receivable aging, payment terms, and customer concentration.",
                "Are receivables consistent with the satellite communication revenue model, or do aging, concentration, and payment terms indicate collection risk?",
                "Check receivables, revenue, customer concentration, aging, bad-debt provision, payment terms, and operating cash flow.",
                True,
            ),
            DriverSpec(
                "financial",
                "satellite remaining life / replacement capex",
                "financial",
                "Remaining satellite life and replacement capex determine asset-aging and long-cycle cash-flow risk.",
                ("remaining useful life by satellite", "design life", "launch date", "replacement schedule", "sustaining capex", "depreciation and impairment"),
                ("financial_metrics.capex", "missing_fields", "risk_flags"),
                "Capex cannot substitute for satellite remaining life, launch date, replacement schedule, depreciation, or impairment evidence.",
                "What is the remaining useful life of operating satellites, and what replacement capex is required to maintain service capacity?",
                "Check remaining useful life, design life, launch date, replacement schedule, sustaining capex, depreciation, and impairment.",
            ),
            DriverSpec(
                "risk",
                "satellite failure / launch / replacement risk",
                "risk",
                "Launch, in-orbit anomaly, insurance, impairment, and replacement events can materially affect capacity and service continuity.",
                ("launch schedule", "launch success or failure", "in-orbit anomaly", "insurance claim", "impairment", "replacement plan", "service impact"),
                ("missing_fields", "risk_flags", "unknown_or_missing_evidence", "enhanced_must_track_indicators"),
                "Normal revenue or ordinary operation data cannot prove absence of satellite failure, launch, insurance, impairment, or replacement risk.",
                "Are there satellite launch, in-orbit failure, insurance, impairment, or replacement events that affect capacity, service continuity, capex, or cash flow?",
                "Check launch schedule, launch result, in-orbit anomaly, insurance claim, impairment, replacement plan, and service impact.",
            ),
            DriverSpec(
                "risk",
                "remaining useful life risk",
                "risk",
                "Remaining useful life risk determines replacement timing, service continuity, and depreciation interpretation.",
                ("launch date", "design life", "remaining life", "depreciation policy", "replacement timeline", "service dependency by satellite"),
                ("missing_fields", "risk_flags", "financial_metrics.capex"),
                "Do not infer remaining life from company age, capex, or satellite-resource descriptions.",
                "Which satellites are approaching end of life, and what evidence links remaining life to revenue continuity and replacement capex?",
                "Check launch date, design life, remaining life, depreciation policy, replacement timeline, and service dependency by satellite.",
            ),
            DriverSpec(
                "risk",
                "capacity utilization risk",
                "risk",
                "Utilization risk tests whether available satellite capacity is leased, sold, renewed, and converted into revenue.",
                ("available capacity", "leased capacity", "utilization rate", "customer cancellations", "price changes", "revenue and margin bridge"),
                ("missing_fields", "risk_flags", "financial_metrics.revenue", "financial_metrics.gross_margin"),
                "Capacity resources are not utilization or revenue, and revenue alone cannot assess unused-capacity risk.",
                "Does unused capacity, lower lease rate, or customer churn create revenue and margin risk?",
                "Check available capacity, leased capacity, utilization rate, customer cancellations, price changes, revenue, and margin bridge.",
            ),
            DriverSpec(
                "risk",
                "customer renewal risk",
                "risk",
                "Customer renewal risk requires contract expiry, renewal rate, customer concentration, and receivable-quality evidence.",
                ("contract duration", "expiry schedule", "renewal rate", "customer concentration", "customer type", "receivable quality"),
                ("financial_metrics.contract_liabilities", "financial_metrics.accounts_receivable", "missing_fields", "risk_flags"),
                "Revenue, contract liabilities, or customer category labels cannot prove customer renewal quality.",
                "What contract expiries or renewal dependencies could affect revenue visibility and cash collection?",
                "Check contract duration, expiry schedule, renewal rate, customer concentration, customer type, and receivable quality.",
            ),
            DriverSpec(
                "risk",
                "technology substitution risk",
                "risk",
                "Technology substitution can affect pricing, utilization, and customer renewal, but only company impact evidence supports assessment.",
                ("LEO / HTS / terrestrial fiber / 5G substitute", "affected service line", "pricing evidence", "utilization evidence", "company response"),
                ("risk_flags", "missing_fields", "unknown_or_missing_evidence", "business_composition"),
                "Technology narratives must not be treated as realized company impact without service-line, pricing, utilization, or customer evidence.",
                "Which services face substitution from LEO, high-throughput satellites, terrestrial networks, or other technologies, and is impact visible in pricing, utilization, revenue, or margin?",
                "Check substitute technology, affected service line, pricing, utilization, customer impact, and company response.",
            ),
            DriverSpec(
                "risk",
                "policy / regulatory risk",
                "risk",
                "Policy and regulation are constraints on license, frequency, orbital resources, service continuity, pricing, and capex.",
                ("license conditions", "frequency or orbital resource regulation", "national security constraints", "policy changes", "company compliance evidence", "service impact"),
                ("basic_info.industry", "risk_flags", "missing_fields", "unknown_or_missing_evidence"),
                "Policy and regulation are constraints, not automatic support or business realization.",
                "What policy, license, frequency, orbital-slot, or regulatory conditions could affect company service continuity, pricing, capex, or customer contracts?",
                "Check license conditions, frequency/orbital regulation, national-security constraints, policy changes, compliance evidence, and service impact.",
            ),
        ]

    def _build_driver(self, pack: dict[str, Any], spec: DriverSpec) -> DriverFactor:
        available = self._available_evidence(pack, spec.checked_paths)
        missing = self._missing_evidence(pack, spec.required_evidence, spec.checked_paths)
        has_concrete_path = bool(available) and spec.concrete_path_allowed

        if has_concrete_path:
            path = " -> ".join(available[:3])
            status = "partial" if missing else "available"
            cap = "low" if missing else "medium"
            reason = ""
        else:
            path = TRANSMISSION_PATH_FALLBACK
            status = "not_assessable"
            cap = "not_assessable"
            reason = GENERIC_MISSING_BRIDGE_REASON if missing else "Available evidence is insufficient for a company transmission path."

        return DriverFactor(
            layer=spec.layer,  # type: ignore[arg-type]
            driver_factor=spec.driver_factor,
            driver_scope=spec.driver_scope,
            why_it_matters=spec.why_it_matters,
            required_evidence=list(spec.required_evidence),
            available_evidence=available,
            missing_evidence=missing,
            company_transmission_path=path,
            data_availability_status=status,  # type: ignore[arg-type]
            confidence_cap=cap,  # type: ignore[arg-type]
            not_assessable_reason=reason,
            what_was_checked=list(spec.checked_paths),
            source_refs=[item.split("=")[0] for item in available],
            research_question=spec.question,
            interpretation_guard=spec.interpretation_guard,
        )

    def _available_evidence(self, pack: dict[str, Any], checked_paths: tuple[str, ...]) -> list[str]:
        available: list[str] = []
        for path in checked_paths:
            if path == "business_composition":
                available.extend(self._business_segment_nodes(pack))
            elif path == "business_composition.geography":
                available.extend(self._business_geography_nodes(pack))
            elif path == "enhanced_must_track_indicators":
                available.extend(self._indicator_nodes(pack))
            elif path == "source_trace_summary":
                available.extend(self._source_trace_nodes(pack))
            elif path in {"missing_fields", "unknown_or_missing_evidence", "risk_flags", "data_limitations"}:
                continue
            else:
                value = self._value_at_path(pack, path)
                if _is_present(value):
                    available.append(f"evidence_pack.{path}={_safe_text(_display_value(value))}")
        return available

    def _missing_evidence(
        self,
        pack: dict[str, Any],
        required_evidence: tuple[str, ...],
        checked_paths: tuple[str, ...],
    ) -> list[str]:
        missing_text = " ".join(
            self._missing_item_text(item)
            for item in (
                _as_list(pack.get("missing_fields"))
                + _as_list(pack.get("unknown_or_missing_evidence"))
                + _as_list(pack.get("data_limitations"))
            )
        ).lower()
        available_text = " ".join(self._available_evidence(pack, checked_paths)).lower()
        missing: list[str] = []
        for item in required_evidence:
            normalized = item.lower()
            if self._requirement_satisfied(normalized, available_text):
                continue
            if any(token in missing_text for token in self._requirement_tokens(normalized)):
                missing.append(item)
                continue
            if normalized in {
                "customer ai capex source",
                "policy source",
                "electricity cost",
                "pue metric",
                "company pue metric",
                "project/customer revenue bridge",
                "industry penetration source",
                "customer concentration",
                "customer revenue share",
                "project delivery stage",
                "acceptance evidence",
                "depreciation",
                "cabinet count",
                "mw scale",
                "rack-up rate",
                "utilization",
                "customer deployment timeline",
                "liquid-cooling revenue",
            }:
                missing.append(item)
            elif item not in missing:
                missing.append(item)
        return missing

    def _requirement_satisfied(self, requirement: str, available_text: str) -> bool:
        if requirement in {"revenue", "datacenter-related revenue or ratio"}:
            return "financial_metrics.revenue=" in available_text or "business_composition" in available_text
        if requirement in {"operating cash flow", "cash-flow bridge"}:
            return "financial_metrics.operating_cashflow=" in available_text
        if requirement == "accounts receivable":
            return "financial_metrics.accounts_receivable=" in available_text
        if requirement in {"receivables", "collection status"}:
            return "financial_metrics.accounts_receivable=" in available_text
        if requirement == "contract liabilities":
            return "financial_metrics.contract_liabilities=" in available_text
        if requirement == "capex":
            return "financial_metrics.capex=" in available_text
        if requirement in {"gross margin", "gross margin or revenue ratio"}:
            return "financial_metrics.gross_margin=" in available_text or "gross_margin" in available_text
        if requirement == "net margin":
            return "financial_metrics.net_margin=" in available_text
        if requirement in {"business composition segment", "period"}:
            return "business_composition" in available_text
        if requirement in {
            "main commodity products",
            "product exposure",
            "revenue by commodity",
            "product definition",
        }:
            return "business_composition" in available_text or "basic_info.main_business=" in available_text
        if requirement in {"product revenue ratio", "revenue ratio"}:
            return "revenue_ratio" in available_text
        if requirement == "segment gross margin":
            return "gross_margin" in available_text
        if requirement == "inventory":
            return "financial_metrics.inventory=" in available_text
        if requirement == "inventory amount":
            return "financial_metrics.inventory=" in available_text
        if requirement == "capex total":
            return "financial_metrics.capex=" in available_text
        if requirement == "commodity price series":
            return "commodity_prices=" in available_text
        if requirement == "revenue reconciliation":
            return "financial_metrics.revenue=" in available_text
        if requirement == "sales volume":
            return "sales_volume=" in available_text
        if requirement == "realized selling price":
            return "realized_selling_price=" in available_text
        if requirement in {
            "service-line revenue bridge",
            "service-line revenue",
            "cxo service revenue contribution",
            "service-line mix",
        }:
            return "business_composition" in available_text
        if requirement == "overseas revenue share":
            return any(
                token in available_text
                for token in ("overseas", "north america", "u.s.", "us customer", "境外", "海外", "北美", "美国")
            )
        if requirement == "datacenter-related revenue or ratio":
            return any(token in available_text for token in ("aidc", "idc", "机房", "机柜", "数据中心"))
        return False

    def _requirement_tokens(self, requirement: str) -> list[str]:
        return [token for token in requirement.replace("/", " ").replace("-", " ").split() if len(token) >= 3]

    def _missing_item_text(self, item: Any) -> str:
        if isinstance(item, dict):
            return str(item.get("field") or item.get("evidence_name") or item.get("why_it_matters") or item)
        return str(item)

    def _business_segment_nodes(self, pack: dict[str, Any]) -> list[str]:
        nodes: list[str] = []
        for index, row in enumerate(_as_list(pack.get("business_composition"))):
            if not isinstance(row, dict):
                continue
            name = row.get("segment_name")
            if not name:
                continue
            ratio = row.get("revenue_ratio")
            period = row.get("period")
            bits = [f"segment_name:{name}"]
            if _is_present(ratio):
                bits.append(f"revenue_ratio:{_display_value(ratio)}")
            if period:
                bits.append(f"period:{period}")
            nodes.append(f"evidence_pack.business_composition[{index}]={'; '.join(bits)}")
        return nodes[:8]

    def _business_geography_nodes(self, pack: dict[str, Any]) -> list[str]:
        nodes: list[str] = []
        keywords = (
            "overseas",
            "domestic",
            "north america",
            "u.s.",
            "united states",
            "us customer",
            "境外",
            "境内",
            "海外",
            "北美",
            "美国",
        )
        for index, row in enumerate(_as_list(pack.get("business_composition"))):
            if not isinstance(row, dict):
                continue
            name = str(row.get("segment_name") or "")
            classification = str(row.get("classification_type") or "")
            haystack = f"{name} {classification}".lower()
            if not any(keyword in haystack for keyword in keywords):
                continue
            ratio = row.get("revenue_ratio")
            period = row.get("period")
            bits = [f"segment_name:{name}"]
            if _is_present(ratio):
                bits.append(f"revenue_ratio:{_display_value(ratio)}")
            if period:
                bits.append(f"period:{period}")
            nodes.append(f"evidence_pack.business_composition[{index}]={'; '.join(bits)}")
        return nodes[:6]

    def _indicator_nodes(self, pack: dict[str, Any]) -> list[str]:
        nodes: list[str] = []
        for index, row in enumerate(_as_list(pack.get("enhanced_must_track_indicators"))):
            if not isinstance(row, dict):
                continue
            name = row.get("indicator_name")
            status = row.get("current_status")
            if not name or not status:
                continue
            nodes.append(f"evidence_pack.enhanced_must_track_indicators[{index}]={_safe_text(name)}; status:{_safe_text(status)}")
        return nodes[:8]

    def _source_trace_nodes(self, pack: dict[str, Any]) -> list[str]:
        nodes: list[str] = []
        for index, row in enumerate(_as_list(pack.get("source_trace_summary"))):
            if not isinstance(row, dict):
                continue
            block = row.get("block_name")
            trace_count = row.get("trace_count")
            if not block:
                continue
            nodes.append(
                f"evidence_pack.source_trace_summary[{index}]="
                f"block_name:{_safe_text(block)}; trace_count:{_safe_text(trace_count)}"
            )
        return nodes[:8]

    def _value_at_path(self, pack: dict[str, Any], path: str) -> Any:
        current: Any = pack
        for part in path.split("."):
            if not isinstance(current, dict):
                return None
            current = current.get(part)
        return current

    def _question_from_driver(self, driver: DriverFactor) -> ResearchDriverQuestion:
        status = driver.data_availability_status
        cap = driver.confidence_cap
        priority = "P1" if status in {"missing", "not_assessable"} else "P2"
        trigger = (
            f"not_assessable:{driver.driver_factor}"
            if status == "not_assessable"
            else f"missing_or_partial:{driver.driver_factor}"
        )
        next_check = "Check required evidence and source-traced fields listed in the driver matrix."
        if driver.missing_evidence:
            next_check = f"Check missing evidence: {', '.join(driver.missing_evidence[:5])}."
        return ResearchDriverQuestion(
            question=driver.research_question,
            layer=driver.layer,
            driver_factor=driver.driver_factor,
            priority=priority,  # type: ignore[arg-type]
            evidence_trigger=trigger,
            why_it_matters=driver.why_it_matters,
            next_check=next_check,
            data_availability_status=status,
            confidence_cap=cap,
        )


def build_research_intelligence_p1(
    evidence_pack: dict[str, Any],
    p0_pack: dict[str, Any] | None = None,
    *,
    source_evidence_pack_path: str = "",
    source_p0_pack_path: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    pack, questions = ResearchIntelligenceP1Builder().build(
        evidence_pack,
        p0_pack,
        source_evidence_pack_path=source_evidence_pack_path,
        source_p0_pack_path=source_p0_pack_path,
    )
    return pack.model_dump(), questions.model_dump()
