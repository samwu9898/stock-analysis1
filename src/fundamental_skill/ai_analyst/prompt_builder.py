# -*- coding: utf-8 -*-
"""Prompt builder for the prompt-only AI analyst workflow."""

from __future__ import annotations

import json
from typing import Any

from .safety import FORBIDDEN_TERMS, check_text_safety


class PromptBuilder:
    """Create a model-ready prompt from an evidence pack."""

    def build(self, evidence_pack: dict[str, Any]) -> str:
        stock = evidence_pack.get("stock", {})
        compact_pack = {
            "stock": stock,
            "confidence_basis": evidence_pack.get("confidence_basis", {}),
            "basic_info": evidence_pack.get("basic_info", {}),
            "financial_metrics": evidence_pack.get("financial_metrics", {}),
            "valuation_metrics": evidence_pack.get("valuation_metrics", {}),
            "business_composition": evidence_pack.get("business_composition", [])[:10],
            "commodity_prices": evidence_pack.get("commodity_prices", []),
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
        evidence_json = json.dumps(compact_pack, ensure_ascii=False, indent=2, default=str)
        forbidden = "、".join(FORBIDDEN_TERMS)
        prompt = f"""# A股基本面分析员任务

你是 A 股基本面分析员。请只基于下面 evidence pack 做专业基本面分析，输出结构化 JSON 报告。

## 输入股票

- 股票代码：{stock.get("code") or ""}
- 股票名称：{stock.get("name") or ""}
- 策略类型：{stock.get("strategy_type") or ""}
- 当前 deterministic fundamental 状态：{stock.get("status") or ""}
- 当前置信度：{stock.get("confidence") or ""}

## 严格边界

- 不得编造 evidence pack 没有的数据。
- 对缺失数据必须明确说明“缺失数据不足以判断”。
- 不得输出交易建议。
- 不得输出目标价格、仓位或账户动作。
- 禁止词列表：{forbidden}。
- 不得引入技术面分析、技术指标、图形形态或成交量判断。
- 不得把 supportive / neutral / negative 解释为任何执行动作。

## 分析要求

1. 解释 confidence 的依据，包括数据覆盖、缺失字段、风险项和证据一致性。
2. 必须输出一句话结论，并解释 `fundamental_view`。
3. 必须输出置信度拆解表，覆盖 `data_coverage`、`financial_quality`、`valuation_interpretability`、`growth_validation`、`risk_identifiability`。
4. 必须分成“支持证据 / 限制证据 / 无法判断项”三类说明。
5. 财务质量分析必须引用 financial_metrics 中的可用字段；缺失字段要说明不足以判断。
6. 估值分析只能基于 valuation_metrics，可用数据不足时必须说明不足以判断。
7. 主营构成分析必须使用 business_composition，并优先使用 `display_value` 展示比例。
8. risk_analysis 必须逐项解释 evidence pack 中的风险。
9. must_track_analysis 必须逐项解释 enhanced_must_track_indicators，并在 Markdown 报告中使用表格，列包含：指标、当前状态、当前值、优先级、为什么重要、后续问题。
10. invalidation_watch 只能描述需要重新评估基本面假设的条件。

## 卫星通信基础设施框架约束

如果策略类型为 `satellite_communication_infrastructure`，报告必须遵守：

- 必须说明这是资产密集、牌照 / 资源驱动、长周期运营型公司。
- 财务指标只能解释基础经营质量。
- 行业专属数据缺失时，不足以判断商业航天业务兑现。
- 合同负债只能作为订单可见度 proxy，不等同真实 backlog 或确定订单。
- capex 只能作为长期资产购建现金支出，不等同新增容量确定释放。
- PE/PB/PS 不能单独判断估值，估值需要结合资产寿命、折旧、现金流稳定性、容量利用率和客户结构。
- 缺容量利用率、客户结构、卫星寿命、折旧时，confidence 不得过高。
- 不得把商业航天主题、政策热度或新闻热度等同业绩兑现。

## 单位与证据使用要求

- 所有比例字段必须使用 `display_value`，不要直接把小数比例写成原始小数。
- 必须保留对 `raw_value` 的审慎解释，尤其是同比增速字段。
- 对 `unit_confidence=low` 的指标不得做强判断。
- 对缺失字段必须写“缺失数据不足以判断”或同等含义。
- 不得编造 evidence pack 没有的数据。

## 输出 JSON Schema

```json
{{
  "ai_report_version": "fundamental_ai_report.v1",
  "stock_code": "",
  "stock_name": "",
  "fundamental_view": "supportive_for_further_evaluation | neutral_requires_more_evidence | not_supportive | insufficient_data",
  "executive_summary": "",
  "confidence_explanation": "",
  "confidence_breakdown": [],
  "supporting_evidence": [],
  "limiting_evidence": [],
  "unknown_or_missing_evidence": [],
  "business_analysis": "",
  "financial_quality_analysis": "",
  "valuation_analysis": "",
  "industry_cycle_analysis": "",
  "risk_analysis": [],
  "must_track_analysis": [],
  "data_limitations": [],
  "invalidation_watch": [],
  "final_summary": ""
}}
```

`fundamental_view` 只能使用以下枚举之一：

- `supportive_for_further_evaluation`
- `neutral_requires_more_evidence`
- `not_supportive`
- `insufficient_data`

## Low-altitude economy infrastructure constraints

If strategy_type is `low_altitude_economy_infrastructure`, the report must state:

- sub_type: {stock.get("sub_type") or ""}
- Low-altitude economy is a sector cluster, not one single industry.
- This framework covers only infrastructure and operation service.
- The report must distinguish `aviation_operations_service` from `airspace_platform_system`.
- Financial metrics explain only base operating quality.
- Missing low-altitude revenue, contracts, customers, operation volume, or project acceptance is insufficient to judge business realization.
- Contract liabilities are only a visibility proxy, not real backlog.
- Policy pilots, demonstration zones and strategic cooperation are not commercial revenue.
- Drone/eVTOL manufacturing and low-altitude operation service must not be mixed.
- Auto-parts low-altitude theme exposure must not be routed into infrastructure operation.

## Evidence Pack

```json
{evidence_json}
```
"""
        return prompt

    def safety_summary(self, prompt: str) -> dict[str, Any]:
        return check_text_safety(prompt, allow_policy_context=True)
