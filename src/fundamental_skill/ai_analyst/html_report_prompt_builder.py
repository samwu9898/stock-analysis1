# -*- coding: utf-8 -*-
"""Prompt builder for Fundamental HTML Report structured JSON v1."""

from __future__ import annotations

import json
from typing import Any

from .html_report_schema import REPORT_VERSION, schema_example


class HtmlReportPromptBuilder:
    """Create the Codex/GPT prompt for the professional Chinese HTML report JSON."""

    def build(self, evidence_pack: dict[str, Any]) -> str:
        stock = evidence_pack.get("stock") if isinstance(evidence_pack.get("stock"), dict) else {}
        compact_pack = self._compact_evidence_pack(evidence_pack)
        compact_pack["derived_metrics_v1"] = derive_metrics_v1(evidence_pack)
        evidence_json = json.dumps(compact_pack, ensure_ascii=False, indent=2, default=str)
        schema_json = json.dumps(schema_example(), ensure_ascii=False, indent=2, default=str)

        return f"""# Fundamental HTML Report Generator v1 结构化报告任务

你是 A 股基本面研究员。请只基于下面的 evidence pack，生成符合 `{REPORT_VERSION}` 的结构化 JSON。最终 JSON 会被 HTML renderer 渲染为专业中文基本面研报。

## 股票

- 股票代码：{stock.get("code") or ""}
- 公司名称：{stock.get("name") or ""}
- strategy_type：{stock.get("strategy_type") or ""}
- sub_type：{stock.get("sub_type") or ""}
- deterministic status：{stock.get("status") or ""}
- evidence confidence：{stock.get("confidence") or ""}

## 输出要求

- 必须输出中文。
- 必须解释，不得只复述数据；最终报告要像专业基本面研究报告，而不是字段摘要。
- 每个判断必须基于 evidence pack 中的事实、source trace、derived observation 或 missing evidence。
- 缺数据必须明确写“无法判断”或“缺少数据，不足以判断”。
- 必须区分事实、proxy、推断。
- 不得编造订单、客户、行业排名、收入占比、产能释放或同业分位。
- 不得把合同负债冒充 backlog 或真实订单。
- 不得用 capex 冒充产能释放。
- 不得把 confidence 当成看好程度；confidence 只表示证据置信度。
- 不输出交易建议 / 不输出目标价 / 不输出技术面。
- 不得输出仓位、账户动作、K线、均线、成交量、买卖时机或价格执行依据。
- fundamental_scenario_analysis 只写基本面情景，不写股价、不写目标价、不写交易动作。
- valuation_explanation 不得包含目标价。
- 输出必须是单个 JSON 对象，不要 Markdown 包裹，不要解释性前后缀。

## 结构化 JSON Schema 要求

必须严格匹配以下字段结构。不要新增交易、技术面或价格执行相关字段。

```json
{schema_json}
```

## 派生指标 v1

以下指标仅在源字段可用时计算；缺失时已经标记为 missing。`free_cashflow` 是 derived observation；合同负债相关比例只能作为 proxy。

```json
{json.dumps(compact_pack["derived_metrics_v1"], ensure_ascii=False, indent=2, default=str)}
```

## Evidence Pack

```json
{evidence_json}
```
"""

    def _compact_evidence_pack(self, evidence_pack: dict[str, Any]) -> dict[str, Any]:
        return {
            "stock": evidence_pack.get("stock", {}),
            "confidence_basis": evidence_pack.get("confidence_basis", {}),
            "basic_info": evidence_pack.get("basic_info", {}),
            "financial_metrics": evidence_pack.get("financial_metrics", {}),
            "valuation_metrics": evidence_pack.get("valuation_metrics", {}),
            "business_composition": evidence_pack.get("business_composition", [])[:12],
            "risk_flags": evidence_pack.get("risk_flags", []),
            "supporting_evidence": evidence_pack.get("supporting_evidence", []),
            "limiting_evidence": evidence_pack.get("limiting_evidence", []),
            "unknown_or_missing_evidence": evidence_pack.get("unknown_or_missing_evidence", []),
            "enhanced_must_track_indicators": evidence_pack.get("enhanced_must_track_indicators", []),
            "invalidation_conditions": evidence_pack.get("invalidation_conditions", []),
            "missing_fields": evidence_pack.get("missing_fields", []),
            "data_limitations": evidence_pack.get("data_limitations", []),
            "source_trace_summary": evidence_pack.get("source_trace_summary", []),
        }


def _metric_raw(value: Any) -> float | None:
    if isinstance(value, dict):
        value = value.get("raw_value")
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _derived_ratio(numerator: Any, denominator: Any, name: str, note: str | None = None) -> dict[str, Any]:
    num = _metric_raw(numerator)
    den = _metric_raw(denominator)
    if num is None or den in (None, 0):
        return {"name": name, "status": "missing", "value": None, "display_value": None, "note": note}
    value = num / den
    return {
        "name": name,
        "status": "derived",
        "value": value,
        "display_value": f"{value * 100:.2f}%",
        "note": note,
    }


def derive_metrics_v1(evidence_pack: dict[str, Any]) -> dict[str, Any]:
    financial = evidence_pack.get("financial_metrics") if isinstance(evidence_pack.get("financial_metrics"), dict) else {}
    revenue = financial.get("revenue")
    net_profit = financial.get("net_profit")
    operating_cashflow = financial.get("operating_cashflow")
    accounts_receivable = financial.get("accounts_receivable")
    inventory = financial.get("inventory")
    capex = financial.get("capex")
    contract_liabilities = financial.get("contract_liabilities")

    ocf = _metric_raw(operating_cashflow)
    capex_value = _metric_raw(capex)
    if ocf is None or capex_value is None:
        free_cashflow = {
            "name": "free_cashflow",
            "status": "missing",
            "value": None,
            "display_value": None,
            "note": "operating_cashflow 或 capex 缺失，无法计算。",
        }
    else:
        free_cashflow = {
            "name": "free_cashflow",
            "status": "derived",
            "value": ocf - capex_value,
            "display_value": str(ocf - capex_value),
            "note": "derived observation: operating_cashflow - capex。",
        }

    return {
        "operating_cashflow_to_net_profit": _derived_ratio(
            operating_cashflow,
            net_profit,
            "operating_cashflow_to_net_profit",
            "观察利润现金含量；字段缺失时不得判断。",
        ),
        "operating_cashflow_to_revenue": _derived_ratio(
            operating_cashflow,
            revenue,
            "operating_cashflow_to_revenue",
            "观察收入现金转化。",
        ),
        "free_cashflow": free_cashflow,
        "accounts_receivable_to_revenue": _derived_ratio(
            accounts_receivable,
            revenue,
            "accounts_receivable_to_revenue",
            "观察应收压力。",
        ),
        "inventory_to_revenue": _derived_ratio(
            inventory,
            revenue,
            "inventory_to_revenue",
            "观察存货压力。",
        ),
        "capex_to_revenue": _derived_ratio(
            capex,
            revenue,
            "capex_to_revenue",
            "capex 是长期资产购建现金支出，不等于产能释放。",
        ),
        "contract_liabilities_to_revenue": _derived_ratio(
            contract_liabilities,
            revenue,
            "contract_liabilities_to_revenue",
            "合同负债只可作为订单可见度 proxy，不等于真实订单或 backlog。",
        ),
    }
