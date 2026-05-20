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
        percent_value = raw * 100 if -1 <= raw <= 1 else raw
        confidence = "medium" if name not in YOY_FIELDS else "low"
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
        unknown_or_missing_evidence = self._unknown_or_missing_evidence(missing_fields)

        stock = {
            "code": fundamental.get("stock_code") or basic_info.get("stock_code") or raw.get("meta", {}).get("code"),
            "name": fundamental.get("stock_name") or basic_info.get("stock_name") or raw.get("meta", {}).get("stock_name"),
            "strategy_type": fundamental.get("strategy_type"),
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
                financial=financial,
                valuation=valuation,
                business=business,
                commodities=commodities,
                risk_flags=risk_flags,
            ),
            "invalidation_conditions": fundamental.get("invalidation_conditions") or [],
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
                "reason": "新业务收入或订单、大客户收入占比、研发费用率未在 evidence pack 中提供，成长兑现不足以判断。",
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

    def _unknown_or_missing_evidence(self, missing_fields: list[str]) -> list[dict[str, Any]]:
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
                ("资本开支或产量成本", "capex_or_unit_cost", "missing", "risk_control", "产量、成本和资本开支决定资源项目兑现质量"),
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
                ("研发费用率", "rd_expense_ratio", "missing", "business_quality", "研发投入影响新业务壁垒和持续成长能力"),
            ]
        elif strategy_type == "semiconductor_cycle":
            specs = [
                ("存货", "inventory", "financial_indicator", "industry_cycle", "存货变化影响半导体周期位置和减值风险判断"),
                ("订单 / 合同负债", "orders_or_contract_liabilities", "financial_indicator", "business_quality", "合同负债可作为订单可见度 proxy，但不等同于真实订单或 backlog"),
                ("毛利率", "gross_margin", "financial_indicator", "financial_quality", "毛利率反映产品结构、竞争和周期压力"),
                ("国产替代收入", "domestic_substitution_revenue", "missing", "business_quality", "国产替代收入验证叙事兑现程度"),
                ("研发投入", "rd_investment", "missing", "business_quality", "研发投入影响产品迭代和壁垒"),
                ("资本开支周期", "capex_cycle", "missing", "industry_cycle", "资本开支周期影响设备和材料需求"),
            ]
        elif strategy_type == "right_trend_growth":
            specs = [
                ("收入增速", "revenue_yoy", "financial_indicator", "financial_quality", "收入增速验证高景气需求是否兑现"),
                ("净利润增速", "net_profit_yoy", "financial_indicator", "financial_quality", "净利润增速验证成长质量和经营杠杆"),
                ("毛利率", "gross_margin", "financial_indicator", "financial_quality", "毛利率验证竞争格局和产品结构"),
                ("订单持续性 / 合同负债", "orders_or_contract_liabilities", "financial_indicator", "business_quality", "合同负债可作为订单可见度 proxy，但不等同于真实订单或 backlog"),
                ("客户资本开支", "customer_capex", "missing", "industry_cycle", "客户资本开支影响需求景气度"),
                ("估值消化能力", "pe_ttm", "valuation", "valuation", "估值消化能力依赖增长兑现和估值水平匹配"),
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

        related_risk = self._related_risk(name, dimension, risk_flags)
        if field == "orders_or_contract_liabilities" and value not in (None, "", []):
            status = "partial_proxy"
        else:
            status = "available" if value not in (None, "", []) else "missing"
        scope_note = None
        if field == "orders_or_contract_liabilities":
            scope_note = "合同负债可作为订单可见度 proxy，但不等同于真实订单或 backlog。"
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
