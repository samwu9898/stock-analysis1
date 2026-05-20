# -*- coding: utf-8 -*-
"""Build compact evidence packs for AI fundamental analysis."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .safety import check_text_safety


EVIDENCE_PACK_VERSION = "fundamental_evidence_pack.v1"
RATIO_FIELDS = {
    "gross_margin",
    "net_margin",
    "roe",
    "debt_to_asset",
    "revenue_ratio",
    "cost_ratio",
    "profit_ratio",
    "revenue_yoy",
    "net_profit_yoy",
    "r_and_d_expense_ratio",
}
YOY_FIELDS = {"revenue_yoy", "net_profit_yoy"}


FIELD_EXPLANATIONS = {
    "financial_metrics.accounts_receivable": "应收账款数据缺失，收入质量和回款压力不足以判断",
    "financial_metrics.inventory": "存货数据缺失，库存周期和存货压力不足以判断",
    "financial_metrics.contract_liabilities": "合同负债数据缺失，订单可见度 proxy 不足以观察；合同负债不等同于真实订单或 backlog",
    "accounts_receivable": "应收账款数据缺失，收入质量和回款压力不足以判断",
    "inventory": "存货数据缺失，库存周期和存货压力不足以判断",
    "contract_liabilities": "合同负债数据缺失，订单可见度 proxy 不足以观察；合同负债不等同于真实订单或 backlog",
    "external.commodity_prices": "外部商品价格数据缺失，资源品外部变量不足以判断",
    "external.commodity_prices.copper": "铜价数据缺失，资源品价格变量不足以判断",
    "external.commodity_prices.cobalt": "钴价数据缺失，相关资源品变量不足以判断",
    "external.commodity_prices.molybdenum": "钼价数据缺失，相关资源品变量不足以判断",
    "external.commodity_prices.copper.freshness": "铜价数据不够新，不能作为当前外部变量证据",
    "business_composition.segments": "主营构成分部缺失，收入结构不足以判断",
    "valuation_metrics": "估值数据缺失，估值水平不足以判断",
    "valuation_metrics.dividend_yield": "股息率数据缺失，分红维度不足以判断",
    "dividend_yield": "股息率数据缺失，分红维度不足以判断",
    "satellite.capacity_utilization_or_lease_rate": "容量利用率 / 出租率缺失，不得断言卫星资源利用充分",
    "satellite.transponder_or_bandwidth_capacity": "转发器 / 带宽容量缺失，可变现通信容量不足以判断",
    "satellite.unit_bandwidth_price": "单位带宽价格缺失，定价趋势和竞争压力不足以判断",
    "satellite.customer_structure_or_concentration": "客户结构 / 客户集中度缺失，不得断言需求稳定或定价能力强",
    "satellite.design_or_remaining_life": "卫星设计寿命 / 剩余寿命缺失，资产老化和替换 capex 风险不足以判断",
    "financial_metrics.depreciation_amortization": "折旧摊销缺失，卫星资产寿命、折旧压力和利润可比性不足以判断",
    "satellite.launch_plan": "卫星发射计划缺失，不得断言新增容量确定释放",
    "satellite.failure_or_insurance_event": "卫星故障 / 保险事件信息缺失，重大资产事件风险需要继续核查",
}


def _json_safe(value: Any) -> Any:
    try:
        json.dumps(value, ensure_ascii=False, default=str)
        return value
    except TypeError:
        if isinstance(value, dict):
            return {str(key): _json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [_json_safe(item) for item in value]
        return str(value)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _first_dict(value: Any) -> dict[str, Any]:
    for item in _as_list(value):
        if isinstance(item, dict):
            return item
    return {}


def _block_rows(raw: dict[str, Any], block_name: str) -> list[dict[str, Any]]:
    blocks = raw.get("blocks") if isinstance(raw, dict) else {}
    if not isinstance(blocks, dict):
        return []
    return [item for item in _as_list(blocks.get(block_name)) if isinstance(item, dict)]


def _pick(row: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    return {field: normalize_metric(field, row.get(field)) for field in fields}


def _load_json(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Required input file not found: {file_path}")
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {file_path}")
    return payload


def explain_missing_field(field: str) -> str:
    if field in FIELD_EXPLANATIONS:
        return FIELD_EXPLANATIONS[field]
    if field.startswith("external.commodity_prices."):
        parts = field.split(".")
        name = parts[2] if len(parts) > 2 else "commodity"
        if field.endswith(".freshness"):
            return f"{name} 商品价格新鲜度不足，外部变量不足以判断"
        return f"{name} 商品价格缺失，资源品外部变量不足以判断"
    return f"{field} 缺失，相关基本面维度不足以判断"


def normalize_metric(name: str, value: Any) -> Any:
    """Attach display metadata for ratio-like fields while preserving raw values."""

    if name not in RATIO_FIELDS:
        return value
    if value in (None, ""):
        out: dict[str, Any] = {
            "name": name,
            "raw_value": value,
            "display_value": None,
            "unit": "%",
            "unit_confidence": "low",
        }
    else:
        try:
            raw = float(value)
        except (TypeError, ValueError):
            return {
                "name": name,
                "raw_value": value,
                "display_value": None,
                "unit": "%",
                "unit_confidence": "low",
            }
        # Connector v2.3a derives R&D intensity as ``expense / revenue * 100``.
        # Keep that percent-point value intact; other ratio fields may still
        # arrive as decimals from source tables.
        percent_value = raw if name == "r_and_d_expense_ratio" else (raw * 100 if -1 <= raw <= 1 else raw)
        confidence = "high" if name == "r_and_d_expense_ratio" else ("medium" if name not in YOY_FIELDS else "low")
        out = {
            "name": name,
            "raw_value": value,
            "display_value": f"{percent_value:.2f}%",
            "unit": "%",
            "unit_confidence": confidence,
        }
    if name in YOY_FIELDS:
        out["unit_assumption"] = "raw value is treated as a percentage point value from source growth-rate fields; verify source unit before strong interpretation"
    return out


def _display(metric: Any) -> Any:
    if isinstance(metric, dict) and "display_value" in metric:
        return metric.get("display_value")
    return metric


def _neutralize_legacy_review_text(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    replacements = {
        "进入交易员 Agent 后续评估": "进入后续综合评估",
        "需要交易员重新评估": "需要后续分析层复核",
        "交给交易员进一步评估": "进入后续综合评估",
        "交易员进一步评估": "后续模块评估",
        "交易员 Agent": "后续分析层",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def _analyst_summary(fundamental: dict[str, Any]) -> Any:
    return _neutralize_legacy_review_text(
        fundamental.get("analyst_summary") or fundamental.get("trader_summary")
    )


def _normalized_invalidation_conditions(fundamental: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in _as_list(fundamental.get("invalidation_conditions")):
        if not isinstance(item, dict):
            continue
        hint = _neutralize_legacy_review_text(
            item.get("downstream_review_hint") or item.get("action_hint_for_trader")
        )
        row = {
            "condition": item.get("condition"),
            "evidence_needed": item.get("evidence_needed"),
            "downstream_review_hint": hint,
        }
        rows.append(row)
    return rows


class EvidencePackBuilder:
    """Compress raw and fundamental JSON into an AI-consumable evidence pack."""

    def build_from_files(self, fundamental_path: str | Path, raw_path: str | Path) -> dict[str, Any]:
        return self.build(_load_json(fundamental_path), _load_json(raw_path))

    def build(self, fundamental: dict[str, Any], raw: dict[str, Any] | None = None) -> dict[str, Any]:
        raw = raw or {}
        basic_info = _first_dict(_block_rows(raw, "basic_info"))
        financial = self._normalize_row(_first_dict(_block_rows(raw, "financial_indicator")))
        valuation = _first_dict(_block_rows(raw, "valuation"))
        business = [_pick(row, [
            "period",
            "segment_name",
            "classification_type",
            "revenue",
            "revenue_ratio",
            "gross_margin",
            "cost",
            "profit",
            "profit_ratio",
            "note",
        ]) for row in _block_rows(raw, "business_composition")[:12]]
        commodities = [_pick(row, [
            "commodity_name",
            "commodity_name_cn",
            "symbol",
            "price",
            "date",
            "market",
            "source_function",
            "source_priority",
            "freshness_days",
            "is_stale",
            "readiness_eligible",
            "warnings",
        ]) for row in _block_rows(raw, "commodity_prices")]
        missing_fields = list(dict.fromkeys(_as_list(fundamental.get("missing_fields")) + self._fetch_missing_fields(raw)))
        source_trace_summary = self._source_trace_summary(raw)
        data_coverage = self._data_coverage(raw)
        data_limitations = self._data_limitations(missing_fields, raw)
        risk_flags = self._risk_flags(fundamental)
        confidence_breakdown = self._confidence_breakdown(
            data_coverage=data_coverage,
            financial=financial,
            valuation=valuation,
            business=business,
            risk_flags=risk_flags,
            missing_fields=missing_fields,
        )
        supporting_evidence = self._supporting_evidence(financial, valuation, business)
        limiting_evidence = self._limiting_evidence(financial, valuation, risk_flags)
        unknown_or_missing_evidence = self._unknown_or_missing_evidence(missing_fields, financial)

        stock = {
            "code": fundamental.get("stock_code") or basic_info.get("stock_code") or raw.get("meta", {}).get("code"),
            "name": fundamental.get("stock_name") or basic_info.get("stock_name") or raw.get("meta", {}).get("stock_name"),
            "strategy_type": fundamental.get("strategy_type"),
            "sub_type": fundamental.get("sub_type"),
            "status": fundamental.get("status"),
            "confidence": fundamental.get("confidence"),
            "fundamental_score": fundamental.get("fundamental_score"),
        }
        pack = {
            "evidence_pack_version": EVIDENCE_PACK_VERSION,
            "stock": stock,
            "confidence_basis": {
                "status": fundamental.get("status"),
                "confidence": fundamental.get("confidence"),
                "score": fundamental.get("fundamental_score"),
                "analyst_summary": _analyst_summary(fundamental),
                "missing_fields": [
                    {"field": field, "explanation": explain_missing_field(str(field))}
                    for field in missing_fields
                ],
                "risk_flags_count": len(risk_flags),
                "data_coverage": data_coverage,
                "known_limits": data_limitations,
                "confidence_breakdown": confidence_breakdown,
            },
            "basic_info": basic_info,
            "financial_metrics": financial,
            "valuation_metrics": valuation,
            "business_composition": business,
            "commodity_prices": commodities,
            "risk_flags": risk_flags,
            "supporting_evidence": supporting_evidence,
            "limiting_evidence": limiting_evidence,
            "unknown_or_missing_evidence": unknown_or_missing_evidence,
            "enhanced_must_track_indicators": self._enhanced_indicators(
                strategy_type=str(fundamental.get("strategy_type") or "unknown"),
                sub_type=fundamental.get("sub_type"),
                financial=financial,
                valuation=valuation,
                business=business,
                commodities=commodities,
                risk_flags=risk_flags,
            ),
            "invalidation_conditions": _normalized_invalidation_conditions(fundamental),
            "missing_fields": [
                {"field": field, "explanation": explain_missing_field(str(field))}
                for field in missing_fields
            ],
            "data_limitations": data_limitations,
            "source_trace_summary": source_trace_summary,
            "forbidden_terms_check": check_text_safety({"fundamental": fundamental, "raw": raw}),
        }
        return _json_safe(pack)

    def _normalize_row(self, row: dict[str, Any]) -> dict[str, Any]:
        return {key: normalize_metric(str(key), value) for key, value in row.items()}

    def _fetch_missing_fields(self, raw: dict[str, Any]) -> list[str]:
        status = raw.get("fetch_status")
        if not isinstance(status, dict):
            return []
        missing: list[str] = []
        for item in status.values():
            if isinstance(item, dict):
                missing.extend(str(field) for field in _as_list(item.get("missing_fields")))
        return missing

    def _data_coverage(self, raw: dict[str, Any]) -> dict[str, Any]:
        status = raw.get("fetch_status")
        if not isinstance(status, dict):
            return {}
        coverage = {}
        for block_name, item in sorted(status.items()):
            if not isinstance(item, dict):
                continue
            missing = _as_list(item.get("missing_fields"))
            coverage[block_name] = {
                "success": bool(item.get("success")),
                "missing_fields_count": len(missing),
                "missing_fields": missing[:8],
                "warnings_count": len(_as_list(item.get("warnings"))),
                "error": item.get("error"),
                "fetched_at": item.get("fetched_at"),
            }
        return coverage

    def _source_trace_summary(self, raw: dict[str, Any]) -> list[dict[str, Any]]:
        status = raw.get("fetch_status")
        if not isinstance(status, dict):
            return []
        rows = []
        for block_name, item in sorted(status.items()):
            if not isinstance(item, dict):
                continue
            traces = [trace for trace in _as_list(item.get("source_trace")) if isinstance(trace, dict)]
            functions = sorted({str(trace.get("function_name")) for trace in traces if trace.get("function_name")})
            fields = sorted({str(trace.get("field_name")) for trace in traces if trace.get("field_name")})
            periods = sorted({str(trace.get("source_period")) for trace in traces if trace.get("source_period")})
            rows.append(
                {
                    "block_name": block_name,
                    "trace_count": len(traces),
                    "functions": functions[:5],
                    "fields": fields[:12],
                    "latest_period": periods[-1] if periods else None,
                }
            )
        return rows

    def _data_limitations(self, missing_fields: list[str], raw: dict[str, Any]) -> list[str]:
        limitations = [explain_missing_field(str(field)) for field in missing_fields]
        for error in _as_list(raw.get("errors")):
            limitations.append(f"数据抓取错误：{error}")
        return list(dict.fromkeys(limitations))

    def _confidence_breakdown(
        self,
        data_coverage: dict[str, Any],
        financial: dict[str, Any],
        valuation: dict[str, Any],
        business: list[dict[str, Any]],
        risk_flags: list[dict[str, Any]],
        missing_fields: list[str],
    ) -> list[dict[str, str]]:
        successful_blocks = [name for name, item in data_coverage.items() if item.get("success")]
        required_blocks = {"basic_info", "business_composition", "financial_indicator", "valuation"}
        missing_set = {str(item) for item in missing_fields}
        return [
            {
                "dimension": "data_coverage",
                "level": "strong" if required_blocks.issubset(set(successful_blocks)) else "medium",
                "reason": f"成功数据块包括 {', '.join(successful_blocks) or 'none'}；缺失字段 {len(missing_set)} 个。",
            },
            {
                "dimension": "financial_quality",
                "level": "medium" if financial.get("gross_margin") and financial.get("operating_cashflow") else "weak",
                "reason": "毛利率、净利率、经营现金流等核心财务字段可用，但应收账款或存货缺失会限制质量判断。",
            },
            {
                "dimension": "valuation_interpretability",
                "level": "medium" if valuation.get("pe_ttm") and valuation.get("pb") else "weak",
                "reason": "PE TTM、PB、PS 和总市值可用，但股息率缺失，且估值需要成长兑现证据配合解释。",
            },
            {
                "dimension": "growth_validation",
                "level": "weak" if any(field in missing_set for field in ("accounts_receivable", "financial_metrics.accounts_receivable")) else "medium",
                "reason": "新业务收入或订单、大客户收入占比等高判断字段仍需验证；研发费用率只代表研发强度，不代表技术壁垒已确认。",
            },
            {
                "dimension": "risk_identifiability",
                "level": "medium" if risk_flags else "weak",
                "reason": f"已识别 {len(risk_flags)} 个风险项；风险可识别，但部分风险仍缺少量化验证字段。",
            },
        ]

    def _supporting_evidence(
        self,
        financial: dict[str, Any],
        valuation: dict[str, Any],
        business: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        evidence = []
        product_rows = [row for row in business if row.get("classification_type") == "按产品分类"]
        if product_rows:
            summary = "；".join(
                f"{row.get('segment_name')}收入占比{_display(row.get('revenue_ratio'))}"
                for row in product_rows[:4]
            )
            evidence.append(
                {
                    "evidence_name": "主营构成清晰",
                    "evidence_value": summary,
                    "why_it_matters": "主营构成决定基本面分析框架和成长验证重点。",
                    "affects_dimension": "business_quality",
                    "source": "business_composition",
                    "confidence_effect": "supportive",
                }
            )
        if financial.get("gross_margin"):
            evidence.append(
                {
                    "evidence_name": "毛利率可用",
                    "evidence_value": _display(financial.get("gross_margin")),
                    "why_it_matters": "毛利率用于观察产品结构、成本和定价能力。",
                    "affects_dimension": "financial_quality",
                    "source": "financial_indicator",
                    "confidence_effect": "supportive",
                }
            )
        if financial.get("operating_cashflow") is not None:
            evidence.append(
                {
                    "evidence_name": "经营现金流可用",
                    "evidence_value": financial.get("operating_cashflow"),
                    "why_it_matters": "经营现金流用于验证利润质量。",
                    "affects_dimension": "financial_quality",
                    "source": "financial_indicator",
                    "confidence_effect": "supportive",
                }
            )
        if valuation.get("pe_ttm") is not None:
            evidence.append(
                {
                    "evidence_name": "估值字段可用",
                    "evidence_value": f"PE TTM {valuation.get('pe_ttm')}, PB {valuation.get('pb')}, PS {valuation.get('ps')}",
                    "why_it_matters": "估值字段提供成长兑现压力的观察入口。",
                    "affects_dimension": "valuation_interpretability",
                    "source": "valuation",
                    "confidence_effect": "supportive_but_requires_context",
                }
            )
        return evidence

    def _limiting_evidence(
        self,
        financial: dict[str, Any],
        valuation: dict[str, Any],
        risk_flags: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        evidence = []
        pe = valuation.get("pe_ttm")
        if isinstance(pe, (int, float)) and pe >= 40:
            evidence.append(
                {
                    "evidence_name": "估值对成长兑现要求较高",
                    "evidence_value": f"PE TTM {pe:.2f}",
                    "why_it_matters": "较高估值需要收入、利润、新业务和客户证据持续验证。",
                    "affects_dimension": "valuation_interpretability",
                    "source": "valuation",
                    "confidence_effect": "limits_confidence",
                }
            )
        revenue_yoy = financial.get("revenue_yoy")
        if isinstance(revenue_yoy, dict) and revenue_yoy.get("unit_confidence") == "low":
            evidence.append(
                {
                    "evidence_name": "收入增速单位置信度低",
                    "evidence_value": revenue_yoy,
                    "why_it_matters": "同比增速单位未完全确认时，不应做强判断。",
                    "affects_dimension": "financial_quality",
                    "source": "financial_indicator",
                    "confidence_effect": "limits_confidence",
                }
            )
        for risk in risk_flags[:4]:
            evidence.append(
                {
                    "evidence_name": str(risk.get("name")),
                    "evidence_value": risk.get("severity"),
                    "why_it_matters": risk.get("monitor_method"),
                    "affects_dimension": "risk_identifiability",
                    "source": "risk_flags",
                    "confidence_effect": "limits_confidence",
                }
            )
        return evidence

    def _unknown_or_missing_evidence(self, missing_fields: list[str], financial: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        rows = [
            {
                "evidence_name": str(field),
                "evidence_value": None,
                "why_it_matters": explain_missing_field(str(field)),
                "affects_dimension": self._dimension_for_missing(str(field)),
                "source": "missing_fields",
                "confidence_effect": "unknown_or_limits_confidence",
            }
            for field in missing_fields
        ]
        required_unknowns = [
            ("新业务收入或订单", "不能确认新业务或机器人相关业务兑现。", "growth_validation"),
            ("大客户收入占比", "不能判断客户集中度和订单持续性。", "risk_identifiability"),
            ("研发费用率", "不能判断新业务壁垒和持续成长投入强度。", "growth_validation"),
        ]
        if financial and financial.get("r_and_d_expense_ratio") not in (None, "", []):
            required_unknowns = [item for item in required_unknowns if item[0] != "研发费用率"]
        for name, why, dimension in required_unknowns:
            rows.append(
                {
                    "evidence_name": name,
                    "evidence_value": None,
                    "why_it_matters": why,
                    "affects_dimension": dimension,
                    "source": "enhanced_must_track_indicators",
                    "confidence_effect": "unknown_or_limits_confidence",
                }
            )
        return list({json.dumps(row, ensure_ascii=False, sort_keys=True): row for row in rows}.values())

    def _dimension_for_missing(self, field: str) -> str:
        if "valuation" in field or "dividend" in field:
            return "valuation_interpretability"
        if "commodity" in field:
            return "industry_cycle"
        if "accounts_receivable" in field or "inventory" in field:
            return "financial_quality"
        return "data_coverage"

    def _risk_flags(self, fundamental: dict[str, Any]) -> list[dict[str, Any]]:
        rows = []
        for item in _as_list(fundamental.get("risk_flags")):
            if not isinstance(item, dict):
                continue
            rows.append(
                {
                    "name": item.get("name") or item.get("risk_name"),
                    "severity": item.get("severity"),
                    "monitor_method": item.get("monitor_method") or item.get("reason"),
                    "evidence": item.get("evidence") or [],
                }
            )
        return rows

    def _enhanced_indicators(
        self,
        strategy_type: str,
        sub_type: str | None,
        financial: dict[str, Any],
        valuation: dict[str, Any],
        business: list[dict[str, Any]],
        commodities: list[dict[str, Any]],
        risk_flags: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if strategy_type in {"resource_swing", "resource_core"}:
            specs = [
                ("核心商品价格", "commodity_price", "commodity_prices", "industry_cycle", "核心商品价格直接影响资源股收入、利润弹性和置信度"),
                ("主营矿种收入占比", "business_mix", "business_composition", "business_quality", "矿种收入占比决定商品价格变化对公司业绩的传导强度"),
                ("毛利率", "gross_margin", "financial_indicator", "financial_quality", "毛利率体现价格、成本和资源禀赋共同作用"),
                ("经营现金流", "operating_cashflow", "financial_indicator", "financial_quality", "经营现金流验证利润质量和周期韧性"),
                ("资本开支", "capex", "financial_indicator", "risk_control", "资本开支用于观察长期资产购建现金支出，不代表产能确定释放"),
            ]
        elif strategy_type == "advanced_manufacturing_growth":
            specs = [
                ("新业务收入或订单", "new_business_revenue_or_orders", "missing", "business_quality", "新业务兑现决定成长叙事能否转化为收入证据"),
                ("合同负债", "orders_or_contract_liabilities", "financial_indicator", "business_quality", "合同负债可作为订单可见度 proxy，但不等同于真实订单或 backlog"),
                ("大客户收入占比", "major_customer_revenue_share", "missing", "risk_control", "大客户依赖会影响收入稳定性和置信度"),
                ("毛利率", "gross_margin", "financial_indicator", "financial_quality", "毛利率验证产品结构升级和定价能力"),
                ("应收账款", "accounts_receivable", "financial_indicator", "financial_quality", "应收账款影响收入质量和回款压力判断"),
                ("存货", "inventory", "financial_indicator", "financial_quality", "存货影响制造业库存周期、备货和减值压力判断"),
                ("经营现金流", "operating_cashflow", "financial_indicator", "financial_quality", "经营现金流用于验证利润含金量"),
                ("研发费用率", "r_and_d_expense_ratio", "financial_indicator", "business_quality", "研发费用率用于观察研发强度，不代表技术壁垒已确认"),
            ]
        elif strategy_type == "semiconductor_cycle":
            specs = [
                ("存货", "inventory", "financial_indicator", "industry_cycle", "存货变化影响半导体周期位置和减值风险判断"),
                ("订单 / 合同负债", "orders_or_contract_liabilities", "financial_indicator", "business_quality", "合同负债可作为订单可见度 proxy，但不等同于真实订单或 backlog"),
                ("毛利率", "gross_margin", "financial_indicator", "financial_quality", "毛利率反映产品结构、竞争和周期压力"),
                ("国产替代收入", "domestic_substitution_revenue", "missing", "business_quality", "国产替代收入验证叙事兑现程度"),
                ("研发费用率", "r_and_d_expense_ratio", "financial_indicator", "business_quality", "研发费用率用于观察研发强度，不代表技术壁垒已确认"),
                ("资本开支", "capex", "financial_indicator", "industry_cycle", "资本开支用于观察长期资产购建现金支出，不代表产能确定释放"),
            ]
        elif strategy_type == "right_trend_growth":
            specs = [
                ("收入增速", "revenue_yoy", "financial_indicator", "financial_quality", "收入增速验证高景气需求是否兑现"),
                ("净利润增速", "net_profit_yoy", "financial_indicator", "financial_quality", "净利润增速验证成长质量和经营杠杆"),
                ("毛利率", "gross_margin", "financial_indicator", "financial_quality", "毛利率验证竞争格局和产品结构"),
                ("订单持续性 / 合同负债", "orders_or_contract_liabilities", "financial_indicator", "business_quality", "合同负债可作为订单可见度 proxy，但不等同于真实订单或 backlog"),
                ("研发费用率", "r_and_d_expense_ratio", "financial_indicator", "business_quality", "研发费用率用于观察研发强度，不代表技术壁垒已确认"),
                ("客户资本开支", "customer_capex", "missing", "industry_cycle", "客户资本开支影响需求景气度"),
                ("资本开支", "capex", "financial_indicator", "industry_cycle", "资本开支用于观察长期资产购建现金支出，不代表需求或产能确定兑现"),
                ("估值消化能力", "pe_ttm", "valuation", "valuation", "估值消化能力依赖增长兑现和估值水平匹配"),
            ]
        elif strategy_type == "low_altitude_economy_infrastructure":
            specs = [
                ("low-altitude revenue share", "low_altitude_revenue_share", "business_composition", "business_quality", "Revenue share verifies whether low-altitude/general-aviation/airspace business is real business exposure rather than theme wording."),
                ("accounts receivable", "accounts_receivable", "financial_indicator", "cash_conversion", "Receivables constrain collection quality and customer/project evidence."),
                ("contract liabilities", "orders_or_contract_liabilities", "financial_indicator", "order_visibility", "Contract liabilities are only a visibility proxy, not real backlog."),
                ("operating cashflow", "operating_cashflow", "financial_indicator", "cashflow_quality", "Operating cashflow verifies basic cash conversion."),
                ("low-altitude business gross margin", "low_altitude_gross_margin", "business_composition", "margin_quality", "Segment margin is needed to assess low-altitude business economics; consolidated margin is only partial evidence."),
                ("customer structure", "customer_structure", "missing", "customer_risk", "Customer structure is required before judging demand stability or collection quality."),
                ("policy pilot to commercial order evidence", "policy_pilot_to_commercial_order", "missing", "commercialization", "Policy pilot or demonstration-zone evidence cannot be treated as commercial revenue."),
                ("safety events / accidents / regulatory penalties", "safety_or_regulatory_event", "missing", "event_risk", "Safety accidents, CAAC penalties, route suspension and airspace control must be explicit risks when present."),
            ]
            if sub_type == "aviation_operations_service":
                specs.extend([
                    ("fleet size", "fleet_size", "missing", "operating_assets", "Fleet size defines aviation operation asset base; v1 does not calculate proxy."),
                    ("aircraft type mix", "aircraft_type_mix", "missing", "operating_assets", "Aircraft type mix affects service capability and depreciation profile."),
                    ("fleet average age", "fleet_average_age", "missing", "asset_life", "Fleet age affects safety, maintenance and replacement needs."),
                    ("operating hours", "operating_hours", "missing", "operating_volume", "Operating hours validate demand and utilization; v1 does not calculate proxy."),
                    ("flight sorties", "flight_sorties", "missing", "operating_volume", "Flight sorties validate service volume; v1 does not calculate proxy."),
                    ("revenue per flight hour", "revenue_per_flight_hour", "future_data_needed", "unit_economics", "Future data only; v1 does not calculate proxy."),
                    ("depreciation and amortization", "depreciation_amortization", "missing", "profit_quality", "Depreciation and amortization help separate asset cost from operating profitability."),
                    ("EBITDA / EBITDA margin", "ebitda_margin", "future_data_needed", "operating_profitability", "Future data only; v1 does not enter EBITDA scoring."),
                    ("operating qualification / airspace resources", "operating_qualification_airspace_resources", "missing", "qualification", "Qualifications and airspace resources constrain operation capacity."),
                    ("takeoff/landing sites / bases / route resources", "sites_bases_routes", "missing", "network_resources", "Sites, bases and route resources define operation network coverage."),
                ])
            else:
                specs.extend([
                    ("contract amount on hand", "contract_amount", "missing", "order_visibility", "Contract amount is required before judging platform-system realization."),
                    ("contract delivery cycle", "contract_delivery_cycle", "missing", "delivery_risk", "Delivery cycle affects revenue recognition and execution risk."),
                    ("project acceptance progress", "project_acceptance_progress", "missing", "realization", "Project acceptance is required before judging delivery realization."),
                    ("platform dispatch volume", "platform_dispatch_volume", "missing", "operating_volume", "Platform dispatch volume validates actual operation use; v1 does not calculate proxy."),
                    ("software service revenue share", "software_service_revenue_share", "missing", "business_quality", "Software service revenue share separates recurring/platform service from project delivery."),
                    ("R&D expense ratio", "r_and_d_expense_ratio", "financial_indicator", "business_quality", "R&D expense ratio observes platform investment but does not prove delivery."),
                    ("customer renewal rate", "customer_renewal_rate", "missing", "customer_quality", "Renewal rate validates recurring demand."),
                    ("government project dependence", "government_project_dependence", "missing", "policy_dependence", "Government project dependence must not be treated as stable commercial demand."),
                    ("project collection cycle", "project_collection_cycle", "missing", "cash_conversion", "Collection cycle validates project cash conversion."),
                ])
        elif strategy_type == "life_science_cxo_services":
            specs = [
                ("CXO / CRO / CDMO related revenue share", "cxo_revenue_share", "business_composition", "business_quality", "Revenue share is the core routing threshold; it proves business structure, not order quality."),
                ("backlog / on-hand orders", "cxo_backlog", "future_data_needed", "order_visibility", "Real backlog is required before judging order visibility; v1 does not calculate a proxy."),
                ("new signed orders", "cxo_new_signed_orders", "future_data_needed", "order_visibility", "New signed orders are required before judging order-trend improvement."),
                ("contract liabilities partial_proxy", "orders_or_contract_liabilities", "financial_indicator", "order_visibility", "Contract liabilities are a partial_proxy only and do not equal real backlog."),
                ("customer concentration", "cxo_customer_concentration", "missing", "customer_risk", "Customer concentration is required before claiming stable customer demand."),
                ("overseas revenue share", "cxo_overseas_revenue_share", "missing", "overseas_risk", "Overseas revenue is needed for regulatory, geopolitical and FX exposure."),
                ("North America / U.S. revenue share", "cxo_north_america_us_revenue_share", "missing", "us_customer_risk", "North America/U.S. exposure must be explicit; v1 does not calculate proxy."),
                ("gross margin", "gross_margin", "financial_indicator", "financial_quality", "Gross margin is base operating-quality evidence; it does not prove CDMO utilization."),
                ("operating cashflow", "operating_cashflow", "financial_indicator", "cash_conversion", "Operating cashflow validates base cash conversion and collection quality."),
                ("accounts receivable", "accounts_receivable", "financial_indicator", "cash_conversion", "Receivables help assess collection pressure and project cash conversion."),
                ("collection cycle", "cxo_collection_cycle", "missing", "cash_conversion", "Collection cycle is needed to interpret receivables and service delivery quality."),
                ("capex", "capex", "financial_indicator", "capacity_input", "Capex is capacity input observation only, not capacity absorption or future order realization."),
                ("FX impact", "cxo_fx_impact", "missing", "fx_risk", "FX impact must consider both revenue and cost sides when overseas revenue is material."),
                ("overseas regulatory / geopolitical / Biosecure Act / sanction risk", "cxo_overseas_regulatory_risk", "missing", "regulatory_risk", "Overseas regulatory, Biosecure Act, sanctions and geopolitical risk must remain explicit guards."),
                ("project cancellation or delay", "cxo_project_cancellation_delay", "missing", "execution_risk", "Project cancellation/delay can affect order conversion and revenue recognition."),
                ("one-off large-order marker", "cxo_one_off_large_order_marker", "missing", "trend_quality", "Single customer/product or pandemic-related orders can distort historical comparisons."),
            ]
            if sub_type == "integrated_cxo_platform":
                specs.extend([
                    ("business-segment revenue mix", "cxo_segment_revenue_mix", "business_composition", "business_quality", "Segment mix separates drug discovery, preclinical, CMC/CDMO and clinical exposure."),
                    ("drug discovery revenue", "cxo_drug_discovery_revenue", "missing", "business_quality", "Drug discovery revenue verifies platform exposure."),
                    ("preclinical service revenue", "cxo_preclinical_revenue", "missing", "business_quality", "Preclinical revenue verifies integrated platform exposure."),
                    ("CMC / CDMO revenue", "cxo_cmc_cdmo_revenue", "missing", "business_quality", "CMC/CDMO revenue verifies downstream development/manufacturing exposure."),
                    ("customer count / active customers", "cxo_active_customers", "missing", "customer_quality", "Active-customer count is needed to assess platform demand breadth."),
                    ("major customer change", "cxo_major_customer_change", "missing", "customer_risk", "Major-customer changes can alter order visibility and margin quality."),
                    ("employee count", "cxo_employee_count", "missing", "operating_capacity", "Employee count helps assess operating capacity and possible talent risk."),
                    ("scientist / R&D staff count", "cxo_scientist_count", "missing", "operating_capacity", "Scientist/R&D staff count is a talent and delivery-capacity input."),
                    ("personnel efficiency", "cxo_personnel_efficiency", "future_data_needed", "operating_efficiency", "Future data only: CXO revenue per employee/scientist is not calculated in v1."),
                ])
            elif sub_type == "cdmo_manufacturing_services":
                specs.extend([
                    ("CDMO orders", "cxo_cdmo_orders", "future_data_needed", "order_visibility", "CDMO order evidence is required; v1 does not auto-collect external orders."),
                    ("CDMO capacity utilization", "cxo_cdmo_capacity_utilization", "future_data_needed", "capacity_absorption", "Utilization is a confidence gate; v1 does not infer it from margin/capex."),
                    ("commercial project count", "cxo_commercial_project_count", "missing", "project_mix", "Commercial project count helps assess CDMO business maturity."),
                    ("capacity expansion progress", "cxo_capacity_expansion_progress", "missing", "capacity_input", "Expansion progress is capacity input context, not utilization proof."),
                    ("unit capacity revenue", "cxo_unit_capacity_revenue", "future_data_needed", "unit_economics", "Future data only; v1 does not calculate proxy."),
                    ("capex / capacity matching", "cxo_capex_capacity_matching", "missing", "capacity_input", "Matching capex with capacity helps avoid overbuilding assumptions."),
                    ("major customer concentration", "cxo_major_customer_concentration", "missing", "customer_risk", "Major-customer concentration can amplify volatility."),
                    ("GMP / FDA / NMPA compliance event", "cxo_gmp_fda_nmpa_event", "missing", "compliance_risk", "Warning letters, inspections, GMP suspension and remediation are forced risks."),
                    ("upfront / milestone payment structure", "cxo_upfront_milestone_payment", "missing", "cash_conversion", "Payment structure affects order visibility and cash conversion."),
                    ("one-off large-order marker", "cxo_one_off_large_order_marker", "missing", "trend_quality", "CDMO samples can be distorted by single product/customer orders."),
                ])
            elif sub_type == "clinical_cro_services":
                specs.extend([
                    ("clinical project count", "cxo_clinical_project_count", "future_data_needed", "operating_volume", "Clinical project count is required before judging clinical CRO prosperity."),
                    ("clinical trial service revenue", "cxo_clinical_trial_service_revenue", "missing", "business_quality", "Clinical trial service revenue verifies clinical CRO exposure."),
                    ("SMO / data-statistics revenue", "cxo_smo_data_statistics_revenue", "missing", "business_quality", "SMO/data-statistics revenue separates service mix."),
                    ("hospital / research-center coverage", "cxo_hospital_research_center_coverage", "missing", "network_resources", "Coverage affects project execution capability."),
                    ("project acceptance progress", "cxo_project_acceptance_progress", "missing", "realization", "Acceptance progress helps assess delivery and revenue recognition."),
                    ("project cancellation or delay", "cxo_project_cancellation_delay", "missing", "execution_risk", "Cancellation/delay can impair revenue realization."),
                    ("project collection cycle", "cxo_project_collection_cycle", "missing", "cash_conversion", "Project collection cycle validates cash conversion."),
                ])
        elif strategy_type == "satellite_communication_infrastructure":
            specs = [
                ("在轨卫星数量", "in_orbit_satellite_count", "missing", "capacity", "在轨卫星数量定义运营资产基础和服务能力"),
                ("转发器 / 带宽容量", "transponder_or_bandwidth_capacity", "missing", "revenue_capacity", "转发器和带宽容量衡量可变现通信容量"),
                ("容量利用率 / 出租率", "capacity_utilization_or_lease_rate", "missing", "operating_efficiency", "容量利用率区分可用容量和实际变现容量"),
                ("单位带宽价格", "unit_bandwidth_price", "missing", "pricing_power", "单位带宽价格反映定价趋势和竞争压力"),
                ("卫星剩余寿命", "satellite_remaining_life", "missing", "asset_life", "剩余寿命影响资产老化、替换需求和服务连续性"),
                ("合同期限结构", "contract_duration_structure", "missing", "revenue_visibility", "合同期限结构影响收入可见度和续约风险"),
                ("客户集中度", "customer_concentration", "missing", "customer_risk", "客户集中度用于判断需求稳定性和回款风险"),
                ("合同负债", "orders_or_contract_liabilities", "financial_indicator", "order_visibility", "合同负债可作为订单可见度 proxy，但不等同于真实订单或 backlog"),
                ("应收账款", "accounts_receivable", "financial_indicator", "cash_conversion", "应收账款影响回款质量和现金转换"),
                ("capex", "capex", "financial_indicator", "reinvestment_need", "capex 表示长期资产购建现金支出，不等同新增容量确定释放"),
                ("折旧摊销", "depreciation_amortization", "missing", "profit_quality", "折旧摊销反映资产消耗和利润可比性"),
                ("经营现金流", "operating_cashflow", "financial_indicator", "cashflow_stability", "经营现金流验证长周期合同是否转化为现金"),
                ("毛利率", "gross_margin", "financial_indicator", "margin_quality", "毛利率观察基础服务盈利能力，但不能替代容量利用率"),
                ("商业航天新业务收入", "commercial_aerospace_new_business_revenue", "missing", "growth_realization", "新业务收入用于区分主题热度和业绩兑现"),
                ("重大卫星发射 / 故障 / 保险事件", "major_satellite_launch_failure_insurance_event", "missing", "event_risk", "重大事件可能改变容量、服务连续性、保险收益或减值风险"),
                ("EV/EBITDA", "ev_ebitda", "future_data_needed", "valuation_context", "资产密集运营商可参考 EV/EBITDA，但 v1 不进入 scoring"),
                ("EBITDA margin", "ebitda_margin", "future_data_needed", "operating_profitability", "EBITDA margin 可辅助拆分折旧影响，但 v1 不进入 scoring"),
                ("自由现金流 = 经营现金流 - capex", "free_cashflow", "derived", "cashflow_quality", "自由现金流观察资本开支后的现金生成"),
                ("债务 / EBITDA", "debt_to_ebitda", "future_data_needed", "leverage_risk", "债务 / EBITDA 可辅助判断杠杆压力，但 v1 不进入 scoring"),
            ]
        else:
            specs = [
                ("收入增速", "revenue_yoy", "financial_indicator", "financial_quality", "收入增速是基础经营趋势证据"),
                ("毛利率", "gross_margin", "financial_indicator", "financial_quality", "毛利率影响盈利质量判断"),
                ("经营现金流", "operating_cashflow", "financial_indicator", "financial_quality", "经营现金流验证利润质量"),
            ]

        return [
            self._indicator_row(name, field, source, dimension, why, financial, valuation, business, commodities, risk_flags)
            for name, field, source, dimension, why in specs
        ]

    def _indicator_row(
        self,
        name: str,
        field: str,
        source: str,
        dimension: str,
        why: str,
        financial: dict[str, Any],
        valuation: dict[str, Any],
        business: list[dict[str, Any]],
        commodities: list[dict[str, Any]],
        risk_flags: list[dict[str, Any]],
    ) -> dict[str, Any]:
        value = None
        source_date = None
        if source == "financial_indicator":
            if field == "orders_or_contract_liabilities":
                value = financial.get("contract_liabilities")
            else:
                value = financial.get(field)
            source_date = financial.get("period")
        elif source == "valuation":
            value = valuation.get(field)
            source_date = valuation.get("period")
        elif source == "business_composition":
            value = [
                {
                    "segment_name": item.get("segment_name"),
                    "revenue_ratio": item.get("revenue_ratio"),
                    "period": item.get("period"),
                }
                for item in business
            ] or None
            source_date = business[0].get("period") if business else None
        elif source == "commodity_prices":
            value = [
                {
                    "commodity_name": item.get("commodity_name"),
                    "price": item.get("price"),
                    "date": item.get("date"),
                    "readiness_eligible": item.get("readiness_eligible"),
                }
                for item in commodities
            ] or None
            source_date = max([str(item.get("date")) for item in commodities if item.get("date")] or [None])
        elif source == "derived":
            if field == "free_cashflow":
                ocf = financial.get("operating_cashflow")
                capex = financial.get("capex")
                if isinstance(ocf, (int, float)) and isinstance(capex, (int, float)):
                    value = ocf - capex
                    source_date = financial.get("period")

        related_risk = self._related_risk(name, dimension, risk_flags)
        if source == "future_data_needed":
            status = "missing / future_data_needed"
        elif source == "derived" and value not in (None, "", []):
            status = "derived_observation"
        elif field == "orders_or_contract_liabilities" and value not in (None, "", []):
            status = "partial_proxy"
        else:
            status = "available" if value not in (None, "", []) else "missing"
        scope_note = None
        if field == "orders_or_contract_liabilities":
            scope_note = "合同负债可作为订单可见度 proxy，但不等同于真实订单或 backlog。"
        elif field == "r_and_d_expense_ratio":
            scope_note = "研发费用率用于观察研发强度，不代表技术壁垒已确认。"
        elif field == "capex":
            scope_note = "capex 为购建固定资产、无形资产和其他长期资产支付现金，不代表产能确定释放。"
        elif field in {"ev_ebitda", "ebitda_margin", "debt_to_ebitda"}:
            scope_note = "v1 仅作为 must-track 和 data limitation，不进入 scoring。"
        elif field == "free_cashflow":
            scope_note = "自由现金流为经营现金流 - capex 的 derived_observation，仅用于观察资本开支后的现金生成。"
        if field in {"revenue_per_flight_hour", "platform_dispatch_volume"}:
            scope_note = "v1 records this as missing/future_data_needed only; no proxy is calculated."
        elif field in {"low_altitude_revenue_share", "low_altitude_gross_margin"}:
            scope_note = "Business composition can support segment exposure, but theme words alone are not evidence of business realization."
        elif field == "cxo_revenue_share":
            scope_note = "Revenue share proves CXO business structure only; it does not prove order quality, backlog, utilization, customer stability or pipeline success."
        elif field in {"cxo_backlog", "cxo_new_signed_orders", "cxo_cdmo_orders", "cxo_cdmo_capacity_utilization", "cxo_north_america_us_revenue_share"}:
            scope_note = "v1 records this as missing/future_data_needed only; no backlog, CDMO utilization or U.S.-exposure proxy is calculated."
        elif field in {"cxo_one_off_large_order_marker", "cxo_overseas_regulatory_risk", "cxo_gmp_fda_nmpa_event"}:
            scope_note = "Must remain an explicit risk guard when disclosure is missing or uncertain."
        return {
            "indicator_name": name,
            "why_it_matters": why,
            "current_value": value,
            "current_status": status,
            "source": source,
            "source_date": source_date,
            "scope_note": scope_note,
            "related_risk": related_risk,
            "affects_dimension": dimension,
            "follow_up_question": self._follow_up_question(name, status),
            "priority": self._priority_for_indicator(status, dimension),
        }

    def _related_risk(self, name: str, dimension: str, risk_flags: list[dict[str, Any]]) -> str | None:
        text = f"{name} {dimension}"
        for risk in risk_flags:
            risk_text = f"{risk.get('name')} {risk.get('monitor_method')}"
            if any(token and token in risk_text for token in text.split()):
                return risk.get("name")
        return None

    def _follow_up_question(self, name: str, status: str) -> str:
        if status == "missing":
            return f"后续需要补充{name}的可验证公开数据，否则该维度不足以判断。"
        return f"后续应观察{name}是否继续支持当前基本面置信度。"

    def _priority_for_indicator(self, status: str, dimension: str) -> str:
        if status == "missing" and dimension in {"business_quality", "financial_quality", "risk_control"}:
            return "high"
        if dimension in {"valuation", "valuation_interpretability", "industry_cycle"}:
            return "medium"
        return "medium" if status == "available" else "low"
