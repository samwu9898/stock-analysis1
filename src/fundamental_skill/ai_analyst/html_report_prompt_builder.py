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

        return f"""# Fundamental HTML Report Generator v2.1 结构化报告任务

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
- 核心结论必须像研究员写的，必须说明：公司到底靠什么赚钱、当前核心基本面命题、已被数据证明的部分、尚未被数据证明的部分、最大限制因素、未来最关键的跟踪指标。
- 每个判断必须基于 evidence pack 中的事实、source trace、derived observation 或 missing evidence。
- 缺数据必须明确写“无法判断”或“缺少数据，不足以判断”。
- 必须区分事实、proxy、推断。
- 不得编造订单、客户、行业排名、收入占比、产能释放或同业分位。
- 不得把合同负债冒充 backlog 或真实订单。
- 不得用 capex 冒充产能释放。
- 资产负债表存量 / 利润表或现金流量表期间数的 mixed stock-flow ratio 必须标注口径限制，不能据此做强判断；尤其是应收账款/收入、存货/收入、合同负债/收入。
- 不得把 confidence 当成看好程度；confidence 只表示证据置信度。
- 不输出交易建议 / 不输出目标价 / 不输出技术面。
- 不得输出仓位、账户动作、K线、均线、成交量、买卖时机或价格执行依据。
- fundamental_scenario_analysis 只写基本面情景，不写股价、不写目标价、不写交易动作。
- valuation_explanation 不得包含目标价。
- elasticity_formula 只能写基本面弹性公式，例如收入增长、毛利率稳定性、费用率控制、经营现金流、capex、新业务证据；不得输出股价、目标价、盈亏比。
- 输出必须是单个 JSON 对象，不要 Markdown 包裹，不要解释性前后缀。

## v2.1 必填增强字段

- `hero_tags`：首屏标签，3-6 个，必须是基本面研究标签，例如“高端制造成长”“汽车热管理”“现金流需复核”；不得包含交易、技术或价格执行含义。
- `research_anchor`：研究主线卡。必须包含 `main_thesis`、`key_conflict`、`current_stage`、`what_is_proven`、`what_is_unproven`。对 002050，应围绕制冷空调零部件基本盘、汽车热管理成长验证、机器人或新业务证据缺口、估值消化依赖收入/利润/现金流。
- `quality_score_breakdown`：六维质量评分，必须包含 `industry_position`、`business_quality`、`growth_realization`、`financial_quality`、`valuation_explainability`、`risk_identifiability`。每项必须包含 `score`、`max_score`、`label`、`explanation`、`evidence_basis`。这不是交易评级，不得写成买卖建议。
- `value_chain_map`：产业链图谱，必须包含 `upstream`、`company_role`、`downstream`、`profit_source`、`unproven_moats`、`key_bottlenecks`。数据不足可以写“待验证”，但不能编造客户、订单或行业份额。
- `elasticity_formula`：基本面弹性公式，必须包含 `formula_title`、`formula_text`、`key_variables`、`interpretation`、`data_limitations`。只解释收入、毛利率、费用率、现金流、capex、新业务证据。
- `tracking_plan_groups`：分层跟踪计划，必须按“财报跟踪”“公告/订单跟踪”“行业/政策跟踪”“风险复核”分组。每项包含 `indicator`、`frequency`、`why_it_matters`、`trigger_for_review`。
- `financial_ratio_caveats`：财务比例口径说明，必须覆盖“应收账款/收入”“存货/收入”“合同负债/收入”，说明 stock-flow mixed ratio 的口径限制、解释强度和后续所需数据。

## v2.2 编辑化表达要求

- Hero 和核心结论要写成研报首页语言：公司身份、主命题、证据边界、关键判断必须清晰，不要只堆字段。
- 财务质量诊断要形成可解释判断：收入质量、利润质量、现金流质量、应收、存货、capex、合同负债和自由现金流都要说明压力来源、证据强度和复核边界。
- 核心结论必须明确区分“已证明”“待验证”“关键复核”，不要把缺失证据写成确定结论。

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
