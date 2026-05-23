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
SUPPORTED_STRATEGY_TYPES = {
    AI_DATACENTER_STRATEGY_TYPE,
    CXO_STRATEGY_TYPE,
    SATELLITE_STRATEGY_TYPE,
    LOW_ALTITUDE_STRATEGY_TYPE,
}

GENERIC_MISSING_BRIDGE_REASON = "Current evidence pack lacks concrete company transmission nodes for this driver."


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
                    "strategy_type=ai_datacenter_infrastructure, life_science_cxo_services, "
                    "satellite_communication_infrastructure, or low_altitude_economy_infrastructure"
                ),
                "supported pilot sub_type such as aviation_operations_service for low altitude",
            ],
            available_evidence=[f"input.strategy_type={strategy_type}", f"input.sub_type={sub_type}"],
            missing_evidence=["P1.1 template for this strategy_type or sub_type"],
            company_transmission_path=TRANSMISSION_PATH_FALLBACK,
            data_availability_status="not_assessable",
            confidence_cap="not_assessable",
            not_assessable_reason=(
                "Current P1.1 implementation only supports ai_datacenter_infrastructure, "
                "life_science_cxo_services, satellite_communication_infrastructure, and "
                "low_altitude_economy_infrastructure / aviation_operations_service pilot templates."
            ),
            what_was_checked=["stock.strategy_type", "stock.sub_type"],
            source_refs=[],
            research_question=(
                "Current P1.1 pilot boundary does not support this strategy_type / sub_type; "
                "what expansion template would be required before assessment?"
            ),
            interpretation_guard="Do not expand unsupported strategy types by free-form inference.",
        )

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
