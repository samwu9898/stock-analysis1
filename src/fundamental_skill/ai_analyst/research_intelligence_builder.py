# -*- coding: utf-8 -*-
"""Build Research Intelligence P0 artifacts from an existing evidence pack."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .research_intelligence_schema import (
    ConfidenceCap,
    ContradictionItem,
    CrossValidationItem,
    EvidenceClassificationItem,
    ResearchIntelligencePack,
    ResearchQuestion,
    ResearchQuestionSet,
    SafetyBoundary,
    SourceHierarchyItem,
    StrategyDriverItem,
    forbidden_research_text_findings,
)


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


def _is_present(value: Any) -> bool:
    if isinstance(value, dict) and "raw_value" in value:
        return value.get("raw_value") not in (None, "", [])
    return value not in (None, "", [])


def _to_float(value: Any) -> float | None:
    value = _metric_value(value)
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _text_contains_any(text: str, tokens: list[str]) -> bool:
    lowered = text.lower()
    return any(token.lower() in lowered for token in tokens)


def _missing_fields(pack: dict[str, Any]) -> set[str]:
    rows = []
    rows.extend(_as_list(pack.get("missing_fields")))
    rows.extend(_as_list(pack.get("confidence_basis", {}).get("missing_fields")))
    out: set[str] = set()
    for item in rows:
        if isinstance(item, dict) and item.get("field"):
            out.add(str(item.get("field")))
        elif item:
            out.add(str(item))
    return out


def _missing_explanations(pack: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in _as_list(pack.get("missing_fields")) + _as_list(pack.get("confidence_basis", {}).get("missing_fields")):
        if isinstance(item, dict) and item.get("field"):
            out[str(item["field"])] = str(item.get("explanation") or "")
    return out


def _indicator_by_name(pack: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("indicator_name")): item
        for item in _as_list(pack.get("enhanced_must_track_indicators"))
        if isinstance(item, dict) and item.get("indicator_name")
    }


def _pack_text(pack: dict[str, Any]) -> str:
    parts: list[str] = []
    stock = pack.get("stock", {})
    basis = pack.get("confidence_basis", {})
    if isinstance(stock, dict):
        parts.extend(str(value) for value in stock.values() if value is not None)
    if isinstance(basis, dict):
        parts.append(str(basis.get("analyst_summary") or ""))
    for row in _as_list(pack.get("risk_flags")):
        if isinstance(row, dict):
            parts.append(str(row.get("name") or ""))
            parts.append(str(row.get("monitor_method") or ""))
    for row in _as_list(pack.get("unknown_or_missing_evidence")):
        if isinstance(row, dict):
            parts.append(str(row.get("evidence_name") or ""))
            parts.append(str(row.get("why_it_matters") or ""))
    return " ".join(parts)


class ResearchIntelligenceBuilder:
    """Build independent P0 research-intelligence artifacts from evidence_pack."""

    def build(self, evidence_pack: dict[str, Any]) -> tuple[ResearchIntelligencePack, ResearchQuestionSet]:
        generated_at = datetime.now().isoformat(timespec="seconds")
        stock = evidence_pack.get("stock") if isinstance(evidence_pack.get("stock"), dict) else {}
        stock_code = str(stock.get("code") or evidence_pack.get("stock_code") or "UNKNOWN")
        stock_name = stock.get("name")
        strategy_type = str(stock.get("strategy_type") or "unknown")
        sub_type = stock.get("sub_type")
        data_cutoff = self._data_cutoff(evidence_pack)

        source_hierarchy = self._source_hierarchy(evidence_pack)
        evidence_classification = self._evidence_classification(evidence_pack)
        strategy_driver_map = {"drivers": self._strategy_driver_map(evidence_pack, strategy_type)}
        cross_validation = self._cross_validation(evidence_pack, strategy_type, sub_type)
        contradictions = self._contradictions(evidence_pack, strategy_type)
        questions = self._questions(evidence_pack, strategy_type, sub_type, contradictions, cross_validation)
        manual_items = [item for item in questions if item.suggested_recipient != "IR"]
        ir_items = [item for item in questions if item.suggested_recipient == "IR"]

        pack_payload = {
            "schema_version": "research_intelligence.v1",
            "stock_code": stock_code,
            "stock_name": stock_name,
            "generated_at": generated_at,
            "data_cutoff": data_cutoff,
            "strategy_type": strategy_type,
            "sub_type": sub_type,
            "source_hierarchy": source_hierarchy,
            "evidence_classification": evidence_classification,
            "strategy_driver_map": strategy_driver_map,
            "business_financial_cross_validation": cross_validation,
            "rule_triggered_contradictions": contradictions,
            "manual_review_items": manual_items,
            "ir_question_candidates": ir_items,
            "safety_boundary": self._safety_boundary([]),
        }
        pack_model = ResearchIntelligencePack.model_validate(pack_payload)
        safety = self._safety_boundary(forbidden_research_text_findings(pack_model.model_dump()))
        pack_model.safety_boundary = safety

        qset_payload = {
            "schema_version": "research_questions.v1",
            "stock_code": stock_code,
            "stock_name": stock_name,
            "generated_at": generated_at,
            "questions": questions,
            "p0_summary": self._priority_summary(questions, "P0"),
            "p1_summary": self._priority_summary(questions, "P1"),
            "p2_summary": self._priority_summary(questions, "P2"),
            "do_not_conclude_until_resolved": [q.question for q in questions if q.priority == "P0"][:8],
        }
        qset_model = ResearchQuestionSet.model_validate(qset_payload)
        return pack_model, qset_model

    def _data_cutoff(self, pack: dict[str, Any]) -> str | None:
        periods = [
            str(row.get("latest_period"))
            for row in _as_list(pack.get("source_trace_summary"))
            if isinstance(row, dict) and row.get("latest_period")
        ]
        return max(periods) if periods else None

    def _source_hierarchy(self, pack: dict[str, Any]) -> list[SourceHierarchyItem]:
        rows: list[SourceHierarchyItem] = []
        coverage = pack.get("confidence_basis", {}).get("data_coverage", {})
        for item in _as_list(pack.get("source_trace_summary")):
            if not isinstance(item, dict):
                continue
            block = str(item.get("block_name") or "unknown")
            cov = coverage.get(block, {}) if isinstance(coverage, dict) else {}
            success = bool(cov.get("success")) if cov else item.get("trace_count", 0) > 0
            fields = [str(field) for field in _as_list(item.get("fields"))]
            rows.append(SourceHierarchyItem(
                source_tier="S4" if block != "news" else "S5",
                source_name=block,
                source_period=item.get("latest_period"),
                source_timestamp=cov.get("fetched_at") if isinstance(cov, dict) else None,
                evidence_type="fact" if success else "missing",
                data_availability_status="available" if success else "missing",
                source_confidence="medium" if success else "low",
                unit_confidence=None,
                what_was_checked=[f"source_trace_summary.{block}", *fields[:6]] or [f"source_trace_summary.{block}"],
                not_assessable_reason="" if success else str(cov.get("error") or "source trace is unavailable"),
            ))
        if not rows:
            rows.append(SourceHierarchyItem(
                source_tier="S0",
                source_name="evidence_pack",
                evidence_type="missing",
                data_availability_status="missing",
                source_confidence="low",
                what_was_checked=["source_trace_summary"],
                not_assessable_reason="evidence pack has no source_trace_summary",
            ))
        return rows

    def _evidence_classification(self, pack: dict[str, Any]) -> list[EvidenceClassificationItem]:
        rows: list[EvidenceClassificationItem] = []
        specs = [
            ("supporting_evidence", "fact", "medium", "available"),
            ("limiting_evidence", "inference", "medium", "partial"),
            ("unknown_or_missing_evidence", "missing", "low", "missing"),
        ]
        for key, evidence_type, cap, status in specs:
            for item in _as_list(pack.get(key)):
                if not isinstance(item, dict):
                    continue
                name = str(item.get("evidence_name") or item.get("indicator_name") or key)
                rows.append(EvidenceClassificationItem(
                    evidence_name=name,
                    evidence_value=item.get("evidence_value"),
                    evidence_type=evidence_type,
                    source=str(item.get("source") or key),
                    source_refs=[str(item.get("source") or key)],
                    interpretation_boundary=self._boundary_for_evidence(name, item),
                    data_availability_status=status,  # type: ignore[arg-type]
                    confidence_cap=cap,  # type: ignore[arg-type]
                    not_assessable_reason=str(item.get("why_it_matters") or "missing evidence") if status == "missing" else "",
                    what_was_checked=[key, name],
                ))
        for item in _as_list(pack.get("enhanced_must_track_indicators")):
            if not isinstance(item, dict):
                continue
            status = str(item.get("current_status") or "")
            if "proxy" not in status:
                continue
            name = str(item.get("indicator_name") or "proxy evidence")
            rows.append(EvidenceClassificationItem(
                evidence_name=name,
                evidence_value=item.get("current_value"),
                evidence_type="proxy",
                source=str(item.get("source") or "enhanced_must_track_indicators"),
                source_refs=["enhanced_must_track_indicators"],
                interpretation_boundary=str(item.get("scope_note") or "proxy evidence cannot be treated as direct fact"),
                data_availability_status="partial",
                confidence_cap="medium",
                what_was_checked=["enhanced_must_track_indicators", name],
            ))
        return rows

    def _boundary_for_evidence(self, name: str, item: dict[str, Any]) -> str:
        text = f"{name} {item.get('why_it_matters', '')} {item.get('confidence_effect', '')}"
        if "合同负债" in text or "contract" in text.lower():
            return "Contract liabilities are visibility proxy only, not backlog or confirmed future revenue."
        if "研发" in text or "R&D" in text:
            return "R&D intensity is input evidence only, not proof of moat."
        if "capex" in text.lower():
            return "Capex is long-term asset cash outflow, not confirmed capacity release."
        return "Use as source-traced evidence only; do not infer missing facts."

    def _strategy_driver_map(self, pack: dict[str, Any], strategy_type: str) -> list[StrategyDriverItem]:
        missing = _missing_fields(pack)
        financial = pack.get("financial_metrics", {})
        business = _as_list(pack.get("business_composition"))
        base_specs = [
            ("demand / revenue validation", ["financial_metrics.revenue_yoy", "business_composition.segments"], ["revenue_yoy", "business_composition"], ["business claim vs revenue evidence"]),
            ("margin / pricing validation", ["financial_metrics.gross_margin"], ["gross_margin"], ["margin claim vs gross margin"]),
            ("cash conversion", ["financial_metrics.operating_cashflow"], ["operating_cashflow"], ["profit/revenue vs cash flow"]),
            ("working capital", ["financial_metrics.accounts_receivable", "financial_metrics.inventory"], ["accounts_receivable", "inventory"], ["revenue vs receivables/inventory"]),
            ("capex / asset intensity", ["financial_metrics.capex"], ["capex"], ["capex vs revenue bridge"]),
            ("customer / order visibility", ["financial_metrics.contract_liabilities", "customer/order evidence"], ["contract_liabilities"], ["orders cannot be inferred from proxy"]),
            ("valuation explainability", ["valuation_metrics.pe_ttm", "financial_metrics.net_profit", "financial_metrics.operating_cashflow"], ["pe_ttm", "net_profit", "operating_cashflow"], ["valuation vs earnings/cash support"]),
        ]
        framework_specs = {
            "ai_datacenter_infrastructure": ("datacenter / cooling realization", ["ai_datacenter.revenue_share", "ai_datacenter.orders_or_backlog", "ai_datacenter.liquid_cooling_revenue_share"], ["business_composition"], ["datacenter revenue vs orders/customers/delivery"]),
            "life_science_cxo_services": ("CXO order and capacity realization", ["cxo_revenue_share", "cxo_backlog", "cxo_customer_concentration"], ["business_composition"], ["CXO revenue vs orders/capacity/cash"]),
            "low_altitude_economy_infrastructure": ("low-altitude operating realization", ["low_altitude_revenue_share", "operating_hours", "project_acceptance"], ["business_composition"], ["low-altitude revenue vs operating evidence"]),
            "satellite_communication_infrastructure": ("satellite asset monetization", ["satellite.capacity_utilization_or_lease_rate", "satellite.transponder_or_bandwidth_capacity"], ["business_composition", "capex"], ["capacity/utilization vs revenue/cash"]),
            "advanced_manufacturing_growth": ("new manufacturing business realization", ["new_business_revenue", "customer_orders"], ["business_composition"], ["new business claim vs segment revenue"]),
            "right_trend_growth": ("high-growth order conversion", ["orders", "customer_validation"], ["revenue_yoy", "contract_liabilities"], ["growth claim vs cash and receivables"]),
            "resource_core": ("resource exposure validation", ["external.commodity_prices", "business_composition.segments"], ["commodity_prices", "business_composition"], ["commodity exposure vs business mix"]),
            "resource_swing": ("resource price sensitivity", ["external.commodity_prices", "business_composition.segments"], ["commodity_prices", "business_composition"], ["commodity price vs margin/cash sensitivity"]),
            "semiconductor_cycle": ("cycle and inventory validation", ["inventory", "orders", "r_and_d_expense_ratio"], ["inventory", "r_and_d_expense_ratio"], ["inventory/R&D vs demand and adoption"]),
            "stable_growth": ("stable growth cash validation", ["operating_cashflow", "accounts_receivable", "roe"], ["operating_cashflow", "accounts_receivable", "roe"], ["stable claim vs cash/receivables/ROE"]),
            "theme_only": ("theme-to-revenue validation", ["business_composition.segments", "orders", "customer evidence"], ["business_composition"], ["theme claim vs official revenue"]),
            "unknown": ("classification evidence validation", ["basic_info.main_business", "business_composition.segments", "financial_metrics"], ["basic_info", "business_composition", "financial_metrics"], ["classification cannot be forced"]),
        }
        base_specs.append(framework_specs.get(strategy_type, framework_specs["unknown"]))
        rows: list[StrategyDriverItem] = []
        for name, required, aliases, checks in base_specs:
            available = [alias for alias in aliases if self._has_alias(financial, business, pack, alias)]
            missing_evidence = [field for field in required if self._required_missing(field, missing, financial, business, pack)]
            status = "available" if not missing_evidence else ("partial" if available else "missing")
            rows.append(StrategyDriverItem(
                driver_name=name,
                why_it_matters=f"{name} is required for P0 evidence-gated research questions.",
                required_evidence=required,
                available_evidence=available,
                missing_evidence=missing_evidence,
                cross_validation_checks=checks,
                data_availability_status=status,  # type: ignore[arg-type]
                confidence_cap="medium" if missing_evidence else "high",
                not_assessable_reason=f"Missing required evidence: {', '.join(missing_evidence)}" if status == "missing" else "",
                what_was_checked=[*required, *aliases],
            ))
        return rows

    def _has_alias(self, financial: dict[str, Any], business: list[Any], pack: dict[str, Any], alias: str) -> bool:
        if alias == "business_composition":
            return bool(business)
        if alias == "commodity_prices":
            return bool(_as_list(pack.get("commodity_prices")))
        if alias == "basic_info":
            return bool(pack.get("basic_info"))
        if alias == "financial_metrics":
            return bool(financial)
        return _is_present(financial.get(alias)) or _is_present(pack.get("valuation_metrics", {}).get(alias))

    def _required_missing(self, field: str, missing: set[str], financial: dict[str, Any], business: list[Any], pack: dict[str, Any]) -> bool:
        if field in missing:
            return True
        leaf = field.split(".")[-1]
        if field == "basic_info.main_business":
            return not _is_present(pack.get("basic_info", {}).get("main_business"))
        if field.startswith("financial_metrics."):
            return not _is_present(financial.get(leaf))
        if field.startswith("valuation_metrics."):
            return not _is_present(pack.get("valuation_metrics", {}).get(leaf))
        if field == "business_composition.segments":
            return not bool(business)
        if field.startswith(("ai_datacenter.", "satellite.", "external.")):
            return field in missing
        if _is_present(financial.get(field)):
            return False
        indicator = _indicator_by_name(pack).get(field)
        if indicator:
            status = str(indicator.get("current_status") or "")
            return "missing" in status or "future_data_needed" in status
        # Industry-specific operating fields are not available unless the
        # evidence pack explicitly exposes them. Treat them as missing rather
        # than assuming the field was checked.
        return True

    def _cross_validation(self, pack: dict[str, Any], strategy_type: str, sub_type: str | None = None) -> list[CrossValidationItem]:
        financial = pack.get("financial_metrics", {})
        business = _as_list(pack.get("business_composition"))
        text = _pack_text(pack)
        specs = self._cross_validation_specs(strategy_type, sub_type)
        rows: list[CrossValidationItem] = []
        for index, spec in enumerate(specs, 1):
            required = spec["required"]
            available = [field for field in required if not self._required_missing(field, _missing_fields(pack), financial, business, pack)]
            missing = [field for field in required if field not in available]
            validation_status = "partially_validated" if available and missing else ("validated" if not missing else "missing")
            if spec.get("claim_tokens") and not _text_contains_any(text, spec["claim_tokens"]):
                validation_status = "not_assessable" if missing else "weak"
            status = "available" if validation_status == "validated" else ("partial" if available else "missing")
            rows.append(CrossValidationItem(
                item_id=f"cv_{index:02d}",
                strategy_type=strategy_type,
                business_claim=spec["claim"],
                financial_checks=spec["checks"],
                required_evidence=required,
                available_evidence=available,
                missing_evidence=missing,
                validation_status=validation_status,  # type: ignore[arg-type]
                triggered_question_ids=[],
                data_availability_status=status,  # type: ignore[arg-type]
                confidence_cap="medium" if missing else "high",
                not_assessable_reason=f"Missing required evidence: {', '.join(missing)}" if status == "missing" else "",
                what_was_checked=required + spec["checks"],
            ))
        return rows

    def _cross_validation_specs(self, strategy_type: str, sub_type: str | None = None) -> list[dict[str, Any]]:
        common = [
            {
                "claim": "reported growth should convert into cash and working-capital quality",
                "required": ["financial_metrics.revenue_yoy", "financial_metrics.operating_cashflow", "financial_metrics.accounts_receivable"],
                "checks": ["revenue_yoy vs operating_cashflow", "revenue_yoy vs accounts_receivable"],
            }
        ]
        by_type = {
            "ai_datacenter_infrastructure": [
                {"claim": "AI datacenter infrastructure revenue should be separated from generic thermal or power exposure", "required": ["ai_datacenter.revenue_share", "ai_datacenter.orders_or_backlog", "financial_metrics.contract_liabilities"], "checks": ["datacenter revenue vs orders/proxy"]},
                {"claim": "liquid-cooling or data-center capacity claims need customer, delivery, and revenue bridge", "required": ["ai_datacenter.liquid_cooling_revenue_share", "ai_datacenter.liquid_cooling_batch_orders", "ai_datacenter.delivery_cycle", "financial_metrics.capex"], "checks": ["capex vs delivery/revenue bridge"]},
            ],
            "life_science_cxo_services": [
                {"claim": "CXO growth should be supported by CXO revenue, orders, customers, and cash conversion", "required": ["cxo_revenue_share", "cxo_backlog", "financial_metrics.operating_cashflow", "financial_metrics.accounts_receivable"], "checks": ["CXO revenue vs backlog/cash"]},
                {"claim": "CDMO or CRO capacity expansion should link capex to utilization or revenue", "required": ["financial_metrics.capex", "cxo_cdmo_capacity_utilization", "business_composition.segments"], "checks": ["capex vs utilization/revenue"]},
            ],
            "low_altitude_economy_infrastructure": [
                {"claim": "low-altitude exposure should be validated by revenue, projects, and operating volume", "required": ["low_altitude_revenue_share", "operating_hours", "project_acceptance", "financial_metrics.accounts_receivable"], "checks": ["theme vs revenue/operation/cash"]},
            ],
            "satellite_communication_infrastructure": [
                {"claim": "satellite infrastructure economics require asset capacity, utilization, contracts, and cash flow", "required": ["satellite.transponder_or_bandwidth_capacity", "satellite.capacity_utilization_or_lease_rate", "financial_metrics.operating_cashflow", "financial_metrics.capex"], "checks": ["capacity/utilization vs revenue/cash"]},
            ],
            "advanced_manufacturing_growth": [
                {"claim": "new manufacturing or robotics growth should show segment revenue or customer/order evidence", "required": ["new_business_revenue", "customer_orders", "business_composition.segments"], "checks": ["new business vs segment revenue"]},
                {"claim": "product-mix improvement should be visible in segment margin and group margin", "required": ["financial_metrics.gross_margin", "business_composition.segments"], "checks": ["segment margin vs group margin"]},
            ],
            "right_trend_growth": [
                {"claim": "high-growth narrative should be supported by revenue growth, customer/order evidence, and cash conversion", "required": ["financial_metrics.revenue_yoy", "customer_orders", "financial_metrics.operating_cashflow", "financial_metrics.accounts_receivable"], "checks": ["growth vs orders/cash"]},
            ],
            "resource_core": [
                {"claim": "resource thesis should be supported by commodity exposure, prices, and cash resilience", "required": ["business_composition.segments", "external.commodity_prices", "financial_metrics.operating_cashflow", "financial_metrics.debt_to_asset"], "checks": ["commodity exposure vs cash/debt"]},
            ],
            "resource_swing": [
                {"claim": "resource swing thesis should link commodity prices, business mix, margins, and cash flow", "required": ["business_composition.segments", "external.commodity_prices", "financial_metrics.gross_margin", "financial_metrics.operating_cashflow"], "checks": ["commodity price vs margin/cash"]},
            ],
            "semiconductor_cycle": [
                {"claim": "semiconductor cycle claims require inventory, orders, customer adoption, and R&D interpretation", "required": ["financial_metrics.inventory", "customer_orders", "financial_metrics.r_and_d_expense_ratio", "financial_metrics.gross_margin"], "checks": ["inventory vs demand", "R&D as input only"]},
            ],
            "stable_growth": [
                {"claim": "stable-growth profile should be supported by ROE, cash flow, receivables, and leverage", "required": ["financial_metrics.roe", "financial_metrics.operating_cashflow", "financial_metrics.accounts_receivable", "financial_metrics.debt_to_asset"], "checks": ["ROE vs cash/leverage"]},
            ],
            "theme_only": [
                {"claim": "theme exposure should not be treated as fundamental realization without revenue, orders, or customers", "required": ["business_composition.segments", "customer_orders", "financial_metrics.operating_cashflow"], "checks": ["theme vs revenue/orders/cash"]},
            ],
            "unknown": [
                {"claim": "unknown classification needs basic business and financial anchors before research conclusions", "required": ["basic_info.main_business", "business_composition.segments", "financial_metrics.revenue_yoy"], "checks": ["classification evidence completeness"]},
            ],
        }
        specs = common + by_type.get(strategy_type, by_type["unknown"])
        if strategy_type == "ai_datacenter_infrastructure" and sub_type == "cooling_liquid_cooling_infrastructure":
            specs.extend([
                {
                    "claim": "liquid-cooling realization should distinguish validation stage, batch orders, revenue recognition, and ordinary HVAC boundary",
                    "required": [
                        "ai_datacenter_cooling_revenue_share",
                        "ai_datacenter_liquid_cooling_revenue_share",
                        "ai_datacenter_liquid_cooling_customer_validation",
                        "ai_datacenter_liquid_cooling_batch_orders",
                        "ai_datacenter_liquid_cooling_revenue_recognition",
                        "ai_datacenter_ordinary_hvac_revenue_share",
                    ],
                    "checks": ["liquid-cooling POC/certification vs batch orders", "datacenter cooling vs ordinary HVAC"],
                },
            ])
        elif strategy_type == "ai_datacenter_infrastructure" and sub_type == "datacenter_operator":
            specs.extend([
                {
                    "claim": "datacenter operator growth should bridge operating resources, rack-up, contracts, capex conversion, depreciation, and power cost",
                    "required": [
                        "ai_datacenter_cabinet_count",
                        "ai_datacenter_mw_scale",
                        "ai_datacenter_rack_up_utilization",
                        "ai_datacenter_pue",
                        "ai_datacenter_customer_contract_term",
                        "ai_datacenter_customer_concentration",
                        "ai_datacenter_revenue_per_cabinet",
                        "financial_metrics.capex",
                        "depreciation_amortization",
                        "ai_datacenter_power_cost_revenue",
                    ],
                    "checks": ["cabinet/MW/rack-up/PUE vs revenue", "capex vs contracts/revenue/cash"],
                },
            ])
        return specs

    def _contradictions(self, pack: dict[str, Any], strategy_type: str) -> list[ContradictionItem]:
        rules = [
            "revenue_growth_vs_cashflow_mismatch",
            "profit_growth_without_cashflow",
            "capex_without_revenue_bridge",
            "new_business_without_segment_revenue",
            "contract_liabilities_overread_as_backlog",
            "r_and_d_ratio_overread_as_moat",
            "inventory_build_vs_demand_claim",
            "receivables_growth_vs_revenue_growth",
            "high_valuation_without_earnings_cashflow_support",
            "policy_theme_without_contract_revenue",
            "commodity_exposure_without_business_mix",
            "customer_order_claim_without_customer_evidence",
            "capacity_claim_without_utilization",
            "stable_growth_without_receivables_cashflow_check",
            "classification_low_confidence_requires_review",
        ]
        return [self._evaluate_rule(rule, pack, strategy_type) for rule in rules]

    def _evaluate_rule(self, rule_id: str, pack: dict[str, Any], strategy_type: str) -> ContradictionItem:
        financial = pack.get("financial_metrics", {})
        valuation = pack.get("valuation_metrics", {})
        missing = _missing_fields(pack)
        text = _pack_text(pack)
        status = "false"
        ctype = "not_triggered"
        severity = "medium"
        claim = rule_id.replace("_", " ")
        evidence_for: list[str] = []
        evidence_against: list[str] = []
        missing_evidence: list[str] = []
        checked: list[str] = []

        def miss(fields: list[str]) -> bool:
            missing_evidence.extend([field for field in fields if self._field_missing(field, pack)])
            return bool(missing_evidence)

        if rule_id == "revenue_growth_vs_cashflow_mismatch":
            checked = ["financial_metrics.revenue_yoy", "financial_metrics.operating_cashflow"]
            rev = _to_float(financial.get("revenue_yoy"))
            ocf = _to_float(financial.get("operating_cashflow"))
            if rev is None or ocf is None:
                status, ctype = "not_assessable", "missing_data_blocker"
                miss(checked)
            elif rev > 0 and ocf <= 0:
                status, ctype, severity = "true", "actual_contradiction", "high"
                evidence_for = [f"revenue_yoy={rev}"]
                evidence_against = [f"operating_cashflow={ocf}"]
        elif rule_id == "profit_growth_without_cashflow":
            checked = ["financial_metrics.net_profit_yoy", "financial_metrics.operating_cashflow"]
            profit = _to_float(financial.get("net_profit_yoy"))
            ocf = _to_float(financial.get("operating_cashflow"))
            if profit is None or ocf is None:
                status, ctype = "not_assessable", "missing_data_blocker"
                miss(checked)
            elif profit > 0 and ocf <= 0:
                status, ctype, severity = "true", "actual_contradiction", "high"
                evidence_for = [f"net_profit_yoy={profit}"]
                evidence_against = [f"operating_cashflow={ocf}"]
        elif rule_id == "capex_without_revenue_bridge":
            checked = ["financial_metrics.capex", "business_composition.segments", "capacity/utilization/revenue bridge"]
            capex = _to_float(financial.get("capex"))
            has_bridge = not any(token in missing for token in ["ai_datacenter.delivery_cycle", "ai_datacenter.liquid_cooling_revenue_share"]) and bool(pack.get("business_composition"))
            if capex is None:
                status, ctype = "not_assessable", "missing_data_blocker"
                miss(["financial_metrics.capex"])
            elif capex > 0 and not has_bridge:
                status, ctype = "true", "missing_bridge"
                evidence_for = [f"capex={capex}"]
                missing_evidence = ["capacity/utilization/revenue bridge"]
        elif rule_id == "new_business_without_segment_revenue":
            checked = ["new business claim text", "business_composition.segments"]
            has_claim = _text_contains_any(text, ["new business", "新业务", "robot", "机器人", "liquid-cooling", "液冷", "AI datacenter"])
            has_segment = bool(pack.get("business_composition"))
            if has_claim and not has_segment:
                status, ctype, severity = "true", "missing_bridge", "high"
                missing_evidence = ["business_composition.segments"]
            elif has_claim and any(field in missing for field in ["ai_datacenter.liquid_cooling_revenue_share", "new_business_revenue"]):
                status, ctype = "true", "missing_bridge"
                missing_evidence = [field for field in missing if "revenue_share" in field or "new_business" in field]
        elif rule_id == "contract_liabilities_overread_as_backlog":
            checked = ["financial_metrics.contract_liabilities", "missing order/backlog fields"]
            cl = _to_float(financial.get("contract_liabilities"))
            order_missing = any("orders_or_backlog" in field or "backlog" in field for field in missing)
            if cl is None:
                status, ctype = "not_assessable", "missing_data_blocker"
                miss(["financial_metrics.contract_liabilities"])
            elif order_missing or _text_contains_any(text, ["backlog", "订单"]):
                status, ctype, severity = "true", "proxy_overread", "high"
                evidence_for = [f"contract_liabilities={cl}"]
                missing_evidence = [field for field in missing if "backlog" in field or "orders" in field]
        elif rule_id == "r_and_d_ratio_overread_as_moat":
            checked = ["financial_metrics.r_and_d_expense_ratio", "technology moat/adoption evidence"]
            rd = _to_float(financial.get("r_and_d_expense_ratio"))
            has_moat_claim = _text_contains_any(text, ["moat", "壁垒", "technology", "技术"])
            if rd is None:
                status, ctype = "not_assessable", "missing_data_blocker"
                miss(["financial_metrics.r_and_d_expense_ratio"])
            elif has_moat_claim:
                status, ctype = "true", "proxy_overread"
                evidence_for = [f"r_and_d_expense_ratio={rd}"]
                missing_evidence = ["product adoption or customer validation evidence"]
        elif rule_id == "inventory_build_vs_demand_claim":
            checked = ["financial_metrics.inventory", "demand/growth claim"]
            inv = _to_float(financial.get("inventory"))
            if inv is None:
                status, ctype = "not_assessable", "missing_data_blocker"
                miss(["financial_metrics.inventory"])
            elif _text_contains_any(text, ["demand", "growth", "景气", "需求", "订单"]):
                status, ctype = "true", "missing_bridge"
                evidence_for = [f"inventory={inv}"]
                missing_evidence = ["inventory turnover or demand bridge"]
        elif rule_id == "receivables_growth_vs_revenue_growth":
            checked = ["financial_metrics.accounts_receivable", "financial_metrics.revenue_yoy"]
            ar = _to_float(financial.get("accounts_receivable"))
            rev = _to_float(financial.get("revenue_yoy"))
            if ar is None or rev is None:
                status, ctype = "not_assessable", "missing_data_blocker"
                miss(checked)
            elif ar > 0 and rev <= 5:
                status, ctype = "true", "missing_bridge"
                evidence_for = [f"accounts_receivable={ar}", f"revenue_yoy={rev}"]
                missing_evidence = ["receivables turnover or collection-cycle evidence"]
        elif rule_id == "high_valuation_without_earnings_cashflow_support":
            checked = ["valuation_metrics.pe_ttm", "financial_metrics.net_profit_yoy", "financial_metrics.operating_cashflow"]
            pe = _to_float(valuation.get("pe_ttm"))
            profit = _to_float(financial.get("net_profit_yoy"))
            ocf = _to_float(financial.get("operating_cashflow"))
            if pe is None:
                status, ctype = "not_assessable", "missing_data_blocker"
                miss(["valuation_metrics.pe_ttm"])
            elif pe >= 50 and ((profit is not None and profit <= 5) or (ocf is not None and ocf <= 0)):
                status, ctype, severity = "true", "actual_contradiction", "high"
                evidence_for = [f"pe_ttm={pe}"]
                evidence_against = [f"net_profit_yoy={profit}", f"operating_cashflow={ocf}"]
        elif rule_id == "policy_theme_without_contract_revenue":
            checked = ["theme/policy text", "business_composition.segments", "customer/order evidence"]
            if strategy_type in {"theme_only", "unknown"} or _text_contains_any(text, ["theme", "policy", "政策", "主题"]):
                if not pack.get("business_composition") or any("orders" in field or "customer" in field for field in missing):
                    status, ctype = "true", "missing_bridge"
                    missing_evidence = ["contract/revenue/customer evidence"]
        elif rule_id == "commodity_exposure_without_business_mix":
            checked = ["commodity_prices", "business_composition.segments"]
            if strategy_type in {"resource_core", "resource_swing"}:
                if not pack.get("business_composition") or not pack.get("commodity_prices"):
                    status, ctype = "true", "missing_bridge"
                    missing_evidence = ["commodity prices or business composition"]
        elif rule_id == "customer_order_claim_without_customer_evidence":
            checked = ["customer/order claim", "customer/order missing fields"]
            if _text_contains_any(text, ["customer", "order", "客户", "订单"]):
                if any("customer" in field or "orders" in field or "backlog" in field for field in missing):
                    status, ctype = "true", "missing_bridge"
                    missing_evidence = [field for field in missing if "customer" in field or "orders" in field or "backlog" in field]
        elif rule_id == "capacity_claim_without_utilization":
            checked = ["capacity/capex claim", "utilization/acceptance/revenue evidence"]
            if _text_contains_any(text, ["capacity", "capex", "产能", "投产", "capex"]):
                if any(token in " ".join(missing).lower() for token in ["utilization", "delivery", "capacity", "acceptance"]):
                    status, ctype = "true", "missing_bridge"
                    missing_evidence = ["utilization, acceptance, delivery, or revenue conversion evidence"]
        elif rule_id == "stable_growth_without_receivables_cashflow_check":
            checked = ["strategy_type", "financial_metrics.accounts_receivable", "financial_metrics.operating_cashflow"]
            if strategy_type == "stable_growth":
                if self._field_missing("financial_metrics.accounts_receivable", pack) or self._field_missing("financial_metrics.operating_cashflow", pack):
                    status, ctype = "true", "missing_data_blocker"
                    miss(["financial_metrics.accounts_receivable", "financial_metrics.operating_cashflow"])
        elif rule_id == "classification_low_confidence_requires_review":
            checked = ["stock.strategy_type", "stock.confidence"]
            confidence = str(pack.get("stock", {}).get("confidence") or pack.get("confidence_basis", {}).get("confidence") or "")
            if strategy_type in {"theme_only", "unknown"} or confidence == "low":
                status, ctype, severity = "true", "low_confidence_classification_blocker", "high"
                missing_evidence = ["classification and basic business evidence"]

        if status == "not_assessable" and not missing_evidence:
            missing_evidence = ["required evidence unavailable"]
        availability = "not_assessable" if status == "not_assessable" else ("partial" if status == "true" else "available")
        cap: ConfidenceCap = "low" if status in {"true", "not_assessable"} else "high"
        return ContradictionItem(
            rule_id=rule_id,
            triggered=status,  # type: ignore[arg-type]
            severity=severity,  # type: ignore[arg-type]
            contradiction_type=ctype,  # type: ignore[arg-type]
            claim_or_risk=claim,
            evidence_for=evidence_for,
            evidence_against=evidence_against,
            missing_evidence=list(dict.fromkeys(missing_evidence)),
            research_question_id=f"q_{rule_id}" if status in {"true", "not_assessable"} else None,
            data_availability_status=availability,  # type: ignore[arg-type]
            confidence_cap=cap,
            not_assessable_reason=f"Cannot assess because missing: {', '.join(dict.fromkeys(missing_evidence))}" if availability == "not_assessable" else "",
            what_was_checked=checked or [rule_id],
        )

    def _field_missing(self, field: str, pack: dict[str, Any]) -> bool:
        return self._required_missing(field, _missing_fields(pack), pack.get("financial_metrics", {}), _as_list(pack.get("business_composition")), pack)

    def _cross_validation_question_text(
        self,
        cv: CrossValidationItem,
        strategy_type: str,
        sub_type: str | None,
    ) -> str:
        missing = set(cv.missing_evidence)
        claim = cv.business_claim

        def has_any(tokens: list[str]) -> bool:
            return any(token in missing or any(token in field for field in missing) for token in tokens)

        if strategy_type == "ai_datacenter_infrastructure" and sub_type == "cooling_liquid_cooling_infrastructure":
            if has_any(["liquid_cooling", "ordinary_hvac", "cooling_revenue"]):
                return (
                    "液冷客户验证目前是 POC、测试、认证，还是已经形成批量订单？"
                    "液冷订单是否披露金额、客户、交付节点和验收口径？"
                    "液冷收入是否单独披露，收入确认口径是什么；机房温控收入中有多少来自数据中心需求，多少可能是普通温控或工业温控？"
                )
            if not has_any(["ai_datacenter"]):
                return "数据中心温控收入增长是否有经营现金流、回款和应收账款质量支撑，哪些财务字段仍缺失？"
            return "数据中心温控收入、客户收入占比和订单交付证据分别披露到什么层级，能否与普通温控或工业温控明确分开？"
        if strategy_type == "ai_datacenter_infrastructure" and sub_type == "datacenter_operator":
            if not has_any(["ai_datacenter", "cabinet", "mw", "rack_up", "pue", "contract", "power_cost", "depreciation"]):
                return "数据中心运营收入增长是否有经营现金流、回款和应收账款质量支撑，哪些财务字段仍缺失？"
            return (
                "机柜数、MW、上架率和 PUE 是否披露？"
                "新增 capex 对应哪些数据中心项目，是否已经转化为上架率、收入或客户合同？"
                "客户合同期限、客户集中度、单机柜收入是否披露，折旧和电力成本如何影响利润和经营现金流？"
            )
        if strategy_type == "advanced_manufacturing_growth":
            if has_any(["new_business", "customer_orders", "major_customer", "business_composition"]):
                return (
                    "机器人或其他新业务是否有单独收入、订单、客户或量产证据？"
                    "新业务毛利率是否可拆分，大客户收入占比是否披露？"
                    "当前估值消化依赖哪些利润增长、毛利率和经营现金流证据，应收账款与经营现金流是否支持收入增长质量？"
                )
            return "当前估值消化依赖哪些利润增长、毛利率和经营现金流证据，是否能和新业务兑现节奏对应起来？"
        if strategy_type == "life_science_cxo_services":
            if not has_any(["cxo", "backlog", "customer", "capacity", "regulatory", "overseas"]):
                return "CXO 收入增长是否有经营现金流、回款和应收账款质量支撑，哪些财务字段仍缺失？"
            return (
                "backlog 和新签订单是否有官方披露？"
                "合同负债是否仅为 partial proxy、不能替代 backlog？"
                "美国或海外客户收入占比是否披露，生物安全法案、海外监管和客户流失风险是否需要单独复核？"
                "CDMO 产能利用率、临床项目数量或客户集中度是否披露，产能扩张是否已经形成收入、利用率或毛利率改善？"
            )
        if strategy_type == "low_altitude_economy_infrastructure":
            return (
                "低空、通航或空管收入占比是否披露？"
                "飞行小时、飞行架次或平台调度量是否披露？"
                "项目合同是否有验收和收入确认，主业是否真是低空基础设施或运营服务，而不是制造或题材？"
            )
        if strategy_type == "satellite_communication_infrastructure":
            return (
                "卫星容量、转发器或带宽资源是否披露？"
                "容量利用率、客户合同期限和单价是否披露？"
                "卫星寿命、折旧和 capex 是否影响现金流稳定性，客户集中度是否可判断？"
            )
        if strategy_type in {"resource_core", "resource_swing"}:
            return (
                "核心商品暴露和收入占比是否清楚？"
                "产量、成本曲线、库存、价格传导和套期保值是否披露？"
                "经营现金流和债务结构是否能承受周期波动？"
            )
        if strategy_type == "semiconductor_cycle":
            return (
                "存货变化是否支持周期复苏叙事？"
                "国产替代收入是否可拆分，客户导入是否已有收入证据？"
                "R&D 强度是否只是投入，而不是技术壁垒证明？"
            )
        if strategy_type == "stable_growth":
            return (
                "稳健增长是否有经营现金流和回款支撑？"
                "应收账款是否过快扩张，ROE 变化来自业务质量还是杠杆？"
                "订单或合同负债是否支撑稳定性，且是否避免把合同负债当作 backlog？"
            )
        if strategy_type in {"theme_only", "unknown"}:
            return (
                "当前主题是否有主营收入、订单和客户证据？"
                "为什么无法稳定分类，哪些主题说法不得进入正式结论？"
            )
        return f"补充验证：{claim}"

    def _questions(
        self,
        pack: dict[str, Any],
        strategy_type: str,
        sub_type: str | None,
        contradictions: list[ContradictionItem],
        cross_validation: list[CrossValidationItem],
    ) -> list[ResearchQuestion]:
        questions: list[ResearchQuestion] = []
        for item in contradictions:
            if item.triggered not in {"true", "not_assessable"}:
                continue
            questions.append(self._question_from_rule(item, strategy_type, sub_type))
        if strategy_type in {"theme_only", "unknown"}:
            questions.append(ResearchQuestion(
                question_id="q_classification_basic_review",
                question="先复核主营业务、业务构成和核心财务字段，避免在证据不足时强行套用行业框架。",
                category="classification",
                priority="P0",
                evidence_trigger="classification_low_confidence_requires_review",
                trigger_rule_id="classification_low_confidence_requires_review",
                why_it_matters="theme_only / unknown 需要先确认分类和基础字段，后续结论才可评估。",
                evidence_gap="classification or basic business evidence is insufficient",
                suggested_recipient="manual_review",
                expected_answer_type="document",
                source_refs=["stock.strategy_type", "basic_info", "business_composition", "financial_metrics"],
                data_availability_status="partial",
                confidence_cap="low",
                what_was_checked=["stock.strategy_type", "basic_info", "business_composition", "financial_metrics"],
            ))
        for cv in cross_validation:
            if cv.validation_status in {"missing", "not_assessable", "partially_validated"} and cv.missing_evidence:
                questions.append(ResearchQuestion(
                    question_id=f"q_{cv.item_id}",
                    question=self._cross_validation_question_text(cv, strategy_type, sub_type),
                    category="cross_validation",
                    priority="P1",
                    evidence_trigger=f"missing_required_evidence:{','.join(cv.missing_evidence[:3])}",
                    why_it_matters="该交叉验证项缺少关键证据，当前只能保守处理。",
                    evidence_gap=", ".join(cv.missing_evidence),
                    suggested_recipient="manual_review",
                    expected_answer_type="document",
                    source_refs=cv.required_evidence,
                    related_cross_validation_item_id=cv.item_id,
                    data_availability_status="missing",
                    confidence_cap="low",
                    not_assessable_reason=f"Missing required evidence: {', '.join(cv.missing_evidence)}",
                    what_was_checked=cv.what_was_checked,
                ))
        dedup: dict[str, ResearchQuestion] = {}
        seen_text: set[str] = set()
        for question in questions:
            if question.question in seen_text:
                continue
            seen_text.add(question.question)
            dedup.setdefault(question.question_id, question)
        return list(dedup.values())

    def _question_from_rule(self, item: ContradictionItem, strategy_type: str, sub_type: str | None = None) -> ResearchQuestion:
        strategy_specific = self._strategy_rule_question_text(item, strategy_type, sub_type)
        question_text = strategy_specific or {
            "revenue_growth_vs_cashflow_mismatch": "解释收入增长与经营现金流不匹配的原因，并补充回款、项目交付或季节性说明。",
            "profit_growth_without_cashflow": "解释利润增长为何未转化为经营现金流，并补充现金转换证据。",
            "capex_without_revenue_bridge": "说明 capex 对应项目状态，以及是否已有收入、利用率、验收或交付验证。",
            "new_business_without_segment_revenue": "拆分新业务或当前研究主线相关业务的收入、毛利率和订单 / 客户证据。",
            "contract_liabilities_overread_as_backlog": "说明合同负债对应的业务和客户类型，并确认其只作为收入可见度 proxy。",
            "r_and_d_ratio_overread_as_moat": "补充产品采用、客户验证或认证证据，避免把研发强度直接视为壁垒。",
            "inventory_build_vs_demand_claim": "解释存货与需求叙事之间的关系，并补充周转、备货或减值风险说明。",
            "receivables_growth_vs_revenue_growth": "解释应收账款与收入增长之间的关系，并补充回款周期或坏账风险说明。",
            "high_valuation_without_earnings_cashflow_support": "说明估值解释需要哪些利润增长和现金流证据支撑。",
            "policy_theme_without_contract_revenue": "补充政策或主题相关业务是否已有合同、收入或客户证据。",
            "commodity_exposure_without_business_mix": "补充核心商品暴露、业务收入占比、产量或成本数据。",
            "customer_order_claim_without_customer_evidence": "补充客户、订单或交付的官方披露证据。",
            "capacity_claim_without_utilization": "补充容量、利用率、验收、投产或收入转换证据。",
            "stable_growth_without_receivables_cashflow_check": "补充经营现金流和应收账款验证，判断稳健增长的现金质量。",
            "classification_low_confidence_requires_review": "先复核分类、主营业务、业务构成和核心财务字段。",
        }.get(item.rule_id, f"复核规则 {item.rule_id} 触发的证据缺口。")
        recipient = "IR" if item.triggered == "true" and item.contradiction_type != "low_confidence_classification_blocker" else "manual_review"
        return ResearchQuestion(
            question_id=f"q_{item.rule_id}",
            question=question_text,
            category="rule_triggered_review",
            priority="P0" if item.severity == "high" or strategy_type in {"theme_only", "unknown"} else "P1",
            evidence_trigger=item.rule_id,
            trigger_rule_id=item.rule_id,
            why_it_matters=f"Rule {item.rule_id} indicates {item.contradiction_type}; this affects P0 assessability.",
            evidence_gap=", ".join(item.missing_evidence),
            suggested_recipient=recipient,
            expected_answer_type="explanation",
            source_refs=item.what_was_checked,
            data_availability_status=item.data_availability_status,
            confidence_cap=item.confidence_cap,
            not_assessable_reason=item.not_assessable_reason,
            what_was_checked=item.what_was_checked,
        )

    def _strategy_rule_question_text(self, item: ContradictionItem, strategy_type: str, sub_type: str | None) -> str | None:
        if item.rule_id == "contract_liabilities_overread_as_backlog":
            if strategy_type == "life_science_cxo_services":
                return "backlog 和新签订单是否由公司官方披露？合同负债对应哪些业务和客户，是否仅作为 partial proxy、不能替代 backlog？"
            if strategy_type == "ai_datacenter_infrastructure":
                return "订单或 backlog 是否披露金额、客户、交付节点和验收口径？合同负债对应哪些项目，是否仅作为 partial proxy、不能替代真实订单或 backlog？"
            return "合同负债对应哪些业务和客户，是否仅作为 partial proxy、不能替代 backlog 或已确认未来收入？"
        if item.rule_id == "capex_without_revenue_bridge":
            if strategy_type == "ai_datacenter_infrastructure" and sub_type == "datacenter_operator":
                return "新增 capex 对应哪些数据中心项目，是否已经转化为上架率、收入或客户合同；折旧和电力成本如何影响利润和经营现金流？"
            if strategy_type == "life_science_cxo_services":
                return "产能扩张对应哪些 CDMO/CRO 项目，是否已经形成收入、利用率或毛利率改善；capex 是否仍只是产能投入观察？"
            if strategy_type == "satellite_communication_infrastructure":
                return "卫星寿命、折旧和 capex 对现金流稳定性的影响如何披露，新增资产是否已有容量利用率、合同期限和单价证据？"
            return "capex 对应哪些项目，是否已有收入、利用率、验收或交付证据；避免把 capex 直接当作产能释放。"
        if item.rule_id == "new_business_without_segment_revenue":
            if strategy_type == "advanced_manufacturing_growth":
                return "机器人或其他新业务是否有单独收入、订单、客户或量产证据；新业务毛利率和大客户收入占比是否可拆分？"
            if strategy_type == "ai_datacenter_infrastructure" and sub_type == "cooling_liquid_cooling_infrastructure":
                return "液冷客户验证目前是 POC、测试、认证，还是批量订单；液冷收入是否单独披露，收入确认口径是什么？"
        if item.rule_id == "revenue_growth_vs_cashflow_mismatch":
            if strategy_type == "ai_datacenter_infrastructure" and sub_type == "cooling_liquid_cooling_infrastructure":
                return "数据中心温控或液冷收入增长为何没有同步转化为利润和经营现金流，回款、验收或交付周期是否拖累现金质量？"
            return "收入增长为何没有同步转化为经营现金流，回款、验收、交付或季节性因素分别是什么？"
        if item.rule_id == "profit_growth_without_cashflow":
            return "利润增长为何没有同步转化为经营现金流，利润来源、回款节奏和营运资本变化是否披露？"
        if item.rule_id == "high_valuation_without_earnings_cashflow_support":
            if strategy_type == "advanced_manufacturing_growth":
                return "当前估值消化依赖哪些利润增长、毛利率和经营现金流证据，机器人或新业务兑现节奏是否足以解释估值压力？"
            return "估值解释依赖哪些利润增长、毛利率和经营现金流证据，哪些证据仍缺失？"
        if item.rule_id == "r_and_d_ratio_overread_as_moat":
            if strategy_type == "semiconductor_cycle":
                return "R&D 强度是否只是投入而不是技术壁垒证明，客户导入、国产替代收入和产品采用证据是否披露？"
            return "R&D 强度是否只是投入证据，产品采用、客户验证或认证证据是否能独立支撑技术壁垒判断？"
        if item.rule_id == "inventory_build_vs_demand_claim" and strategy_type == "semiconductor_cycle":
            return "存货变化是否支持周期复苏叙事，客户导入和收入确认是否能解释备货、周转或减值风险？"
        if item.rule_id == "commodity_exposure_without_business_mix":
            return "核心商品暴露和收入占比是否清楚，产量、成本曲线、库存、价格传导、套期保值和现金流韧性是否披露？"
        if item.rule_id == "policy_theme_without_contract_revenue":
            if strategy_type in {"theme_only", "unknown"}:
                return "当前主题是否有主营收入、订单和客户证据；为什么无法稳定分类，哪些主题说法不得进入正式结论？"
            if strategy_type == "ai_datacenter_infrastructure" and sub_type == "datacenter_operator":
                return "AIDC/智算中心政策或行业需求是否已转化为可披露客户合同、上架率、PUE、收入或经营现金流，而不是仅停留在主题或建设预期？"
            if strategy_type == "low_altitude_economy_infrastructure":
                return "低空、通航或空管收入占比是否披露，项目合同是否有验收和收入确认；主业是否真是低空基础设施或运营服务？"
        if item.rule_id == "stable_growth_without_receivables_cashflow_check":
            return "稳健增长是否有经营现金流和回款支撑，应收账款是否过快扩张，ROE 变化来自业务质量还是杠杆？"
        if item.rule_id == "classification_low_confidence_requires_review":
            return "为什么无法稳定分类；主营收入、订单、客户和核心财务证据分别缺什么，哪些主题说法不得进入正式结论？"
        if item.rule_id == "customer_order_claim_without_customer_evidence":
            if strategy_type == "ai_datacenter_infrastructure" and sub_type == "cooling_liquid_cooling_infrastructure":
                return "液冷或数据中心温控客户是否已有官方披露？订单是否包含客户类型、金额、交付节点、验收口径和收入确认安排？"
            if strategy_type == "ai_datacenter_infrastructure" and sub_type == "datacenter_operator":
                return "客户合同是否披露客户类型、合同期限、机柜/MW规模、上架节奏和收入确认口径？"
            if strategy_type == "advanced_manufacturing_growth":
                return "机器人或新业务客户、订单和量产证据是否为官方披露，大客户收入占比是否可判断？"
            if strategy_type == "life_science_cxo_services":
                return "海外或美国客户收入占比、客户集中度和客户流失风险是否披露，相关订单是否有官方依据？"
        if item.rule_id == "capacity_claim_without_utilization":
            if strategy_type == "ai_datacenter_infrastructure" and sub_type == "cooling_liquid_cooling_infrastructure":
                return "液冷或机房温控相关产能、项目投产、客户验收和收入转换是否披露？现有 capex 是否已转化为液冷/数据中心温控收入？"
            if strategy_type == "life_science_cxo_services":
                return "CDMO 产能利用率、临床项目数量或客户集中度是否披露，产能扩张是否已经形成收入、利用率或毛利率改善？"
            if strategy_type == "ai_datacenter_infrastructure" and sub_type == "datacenter_operator":
                return "机柜数、MW、上架率和 PUE 是否披露，新增资源是否已经转化为收入或客户合同？"
        return None

    def _safety_boundary(self, findings: list[dict[str, str]]) -> SafetyBoundary:
        return SafetyBoundary(
            safe=not findings,
            blocked_terms=sorted({item["term"] for item in findings}),
            blocked_count=len(findings),
        )

    def _priority_summary(self, questions: list[ResearchQuestion], priority: str) -> str:
        count = sum(1 for item in questions if item.priority == priority)
        return f"{priority} questions: {count}"


def build_research_intelligence(evidence_pack: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    pack, questions = ResearchIntelligenceBuilder().build(evidence_pack)
    return pack.model_dump(), questions.model_dump()
