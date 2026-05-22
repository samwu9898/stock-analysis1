# -*- coding: utf-8 -*-
"""Build Research Intelligence P1.1 AI datacenter pilot artifacts."""

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


SUPPORTED_STRATEGY_TYPE = "ai_datacenter_infrastructure"
SUPPORTED_SUB_TYPES = {"cooling_liquid_cooling_infrastructure", "datacenter_operator"}

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
        if strategy_type != SUPPORTED_STRATEGY_TYPE or sub_type not in SUPPORTED_SUB_TYPES:
            drivers = [self._unsupported_driver(strategy_type, sub_type)]
        else:
            drivers = self._ai_datacenter_drivers(evidence_pack, str(sub_type))

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
                "p1_summary": f"P1.1 AI datacenter pilot driver questions: {len(questions)}",
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
            why_it_matters="P1.1 first implementation is intentionally limited to the AI datacenter pilot.",
            required_evidence=["strategy_type=ai_datacenter_infrastructure", "supported pilot sub_type"],
            available_evidence=[f"input.strategy_type={strategy_type}", f"input.sub_type={sub_type}"],
            missing_evidence=["P1.1 expansion template for this strategy_type or sub_type"],
            company_transmission_path=TRANSMISSION_PATH_FALLBACK,
            data_availability_status="not_assessable",
            confidence_cap="not_assessable",
            not_assessable_reason="Current P1.1 pilot only supports ai_datacenter_infrastructure with cooling_liquid_cooling_infrastructure or datacenter_operator.",
            what_was_checked=["stock.strategy_type", "stock.sub_type"],
            source_refs=[],
            research_question="当前 P1.1 pilot 仅支持 ai_datacenter_infrastructure，其他 strategy_type 需后续扩展。",
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
            elif path == "enhanced_must_track_indicators":
                available.extend(self._indicator_nodes(pack))
            elif path in {"missing_fields", "unknown_or_missing_evidence", "risk_flags"}:
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
        if requirement == "contract liabilities":
            return "financial_metrics.contract_liabilities=" in available_text
        if requirement == "capex":
            return "financial_metrics.capex=" in available_text
        if requirement in {"gross margin", "gross margin or revenue ratio"}:
            return "financial_metrics.gross_margin=" in available_text or "gross_margin" in available_text
        if requirement in {"business composition segment", "period"}:
            return "business_composition" in available_text
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
