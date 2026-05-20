# Fundamental Must-Have Indicator Coverage Audit

Date: 2026-05-19

Scope:

- Read-only audit of existing `output/evidence_pack_<code>.json` and `output/fundamental_<code>.json`.
- Covered strategy types: `resource_swing`, `resource_core`, `advanced_manufacturing_growth`, `semiconductor_cycle`, `right_trend_growth`.
- No deterministic pipeline, connector, dashboard, account integration, technical indicator, `technical_skill`, or `trader_skill` change.

Related helper:

- `scripts/audit_must_have_indicator_coverage.py`

Coverage method:

- `available`: the current evidence pack has a directly usable structured value.
- `partial`: the current evidence pack has adjacent evidence, but not the complete must-have indicator.
- `missing`: the current evidence pack has no usable structured value.
- Strict coverage counts only `available`.
- Effective coverage counts `available = 1`, `partial = 0.5`, `missing = 0`.

## Executive Summary

Across the 6 audited stocks and 54 must-have indicator rows:

| metric | value |
| --- | ---: |
| total rows | 54 |
| available | 25 |
| partial | 7 |
| missing | 22 |
| strict coverage | 46.30% |
| effective coverage | 52.78% |

The main AI report quality constraint is not front-end rendering. The main constraint is that several high-judgment fields are not present in the evidence pack as structured, source-traced data. As a result, the AI report correctly keeps saying that important dimensions are insufficiently supported.

Most reusable easy gaps are financial statement fields: inventory, accounts receivable, R&D expense ratio, and capex. Most high-impact hard gaps require announcement text, annual report extraction, research-note style curation, or manual input: orders, customer concentration, new-business revenue, customer capex, production volume, unit cost, and domestic-substitution revenue evidence.

## Must-Have Indicator Definitions

### `resource_swing` and `resource_core`

| indicator | priority | difficulty | suggested data source |
| --- | --- | --- | --- |
| 核心商品价格 | high | medium | ExternalCommodityPriceConnector; cobalt and molybdenum still need stable domestic public sources |
| 主营矿种收入占比 | high | medium | AkShare 主营构成 / `stock_zygc_em` |
| 毛利率 | high | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 经营现金流 | high | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 资本开支 | medium | medium | AkShare cash-flow statement capex-related cash outflow |
| 产量 / 成本 | medium | hard | Annual report / announcement text / manual input; segment cost is only partial context |
| 资产负债率 | medium | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 存货 | medium | easy | AkShare balance sheet amount field; do not use turnover ratios as substitutes |
| 应收账款 | medium | easy | AkShare balance sheet amount field; do not use turnover ratios as substitutes |

### `advanced_manufacturing_growth`

| indicator | priority | difficulty | suggested data source |
| --- | --- | --- | --- |
| 收入增速 | high | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 利润增速 | high | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 毛利率 | high | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 经营现金流 | high | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 应收账款 | medium | easy | AkShare balance sheet amount field |
| 存货 | medium | easy | AkShare balance sheet amount field |
| 研发费用率 | medium | easy | R&D expense plus revenue |
| 新业务收入 / 订单 | high | hard | Announcement / annual report text / curated input |
| 大客户收入占比 | high | hard | Annual report customer concentration disclosure / curated input |
| 海外收入占比 | medium | medium | AkShare 主营构成地区分类 / `stock_zygc_em` |

### `semiconductor_cycle`

| indicator | priority | difficulty | suggested data source |
| --- | --- | --- | --- |
| 收入增速 | high | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 毛利率 | high | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 存货 | medium | easy | AkShare balance sheet amount field |
| 订单 / 合同负债 | high | medium | Contract liabilities from balance sheet; order evidence from text |
| 研发费用率 | medium | easy | R&D expense plus revenue |
| 资本开支 | medium | medium | AkShare cash-flow statement capex-related cash outflow |
| 国产替代收入证据 | high | hard | Announcement / annual report text / curated input |
| 应收账款 | medium | easy | AkShare balance sheet amount field |
| 估值分位 | medium | medium | Historical valuation series and local percentile calculation |

### `right_trend_growth`

| indicator | priority | difficulty | suggested data source |
| --- | --- | --- | --- |
| 收入增速 | high | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 利润增速 | high | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 毛利率 | high | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 经营现金流 | high | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 订单持续性 | high | hard | Announcement / annual report order disclosure / curated input |
| 客户资本开支 | medium | hard | Customer public reports, sector data, or curated input |
| 估值消化能力 | medium | medium | Valuation fields plus growth fields plus historical or peer context |
| 客户集中度 | high | hard | Annual report customer concentration disclosure / curated input |

## Stock Coverage

| stock_code | stock_name | strategy_type | total | available | partial | missing | strict coverage | effective coverage |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 000426 | 兴业银锡 | resource_swing | 9 | 5 | 1 | 3 | 55.56% | 61.11% |
| 002050 | 三花智控 | advanced_manufacturing_growth | 10 | 5 | 1 | 4 | 50.00% | 55.00% |
| 002371 | 北方华创 | semiconductor_cycle | 9 | 2 | 1 | 6 | 22.22% | 27.78% |
| 300308 | 中际旭创 | right_trend_growth | 8 | 4 | 1 | 3 | 50.00% | 56.25% |
| 601899 | 紫金矿业 | resource_core | 9 | 5 | 1 | 3 | 55.56% | 61.11% |
| 603993 | 洛阳钼业 | resource_swing | 9 | 4 | 2 | 3 | 44.44% | 55.56% |

## Strategy-Type Coverage

| strategy_type | total | available | partial | missing | strict coverage | effective coverage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| advanced_manufacturing_growth | 10 | 5 | 1 | 4 | 50.00% | 55.00% |
| resource_core | 9 | 5 | 1 | 3 | 55.56% | 61.11% |
| resource_swing | 18 | 9 | 3 | 6 | 50.00% | 58.33% |
| right_trend_growth | 8 | 4 | 1 | 3 | 50.00% | 56.25% |
| semiconductor_cycle | 9 | 2 | 1 | 6 | 22.22% | 27.78% |

The weakest strategy type is `semiconductor_cycle`: revenue growth and gross margin are present, but inventory, order or contract-liability evidence, R&D expense ratio, capex, domestic-substitution revenue evidence, receivables, and valuation percentile are not complete.

## Detail Rows

| stock_code | stock_name | strategy_type | indicator_name | coverage_status | current_value | source | source_date | missing_reason | impact_on_analysis | priority | implementation_difficulty | suggested_data_source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 002050 | 三花智控 | advanced_manufacturing_growth | 收入增速 | available | 1.36% | financial_indicator | 20260331 |  | Growth validation has a base field. | high | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 002050 | 三花智控 | advanced_manufacturing_growth | 利润增速 | available | 2.68% | financial_indicator | 20260331 |  | Profit elasticity has a base field. | high | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 002050 | 三花智控 | advanced_manufacturing_growth | 毛利率 | available | 27.80% | financial_indicator | 20260331 |  | Product structure and cost validation are supported. | high | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 002050 | 三花智控 | advanced_manufacturing_growth | 经营现金流 | available | 1105790187.12 | financial_indicator | 20260331 |  | Profit quality has a base field. | high | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 002050 | 三花智控 | advanced_manufacturing_growth | 应收账款 | missing |  | financial_indicator | 20260331 | `financial_metrics.accounts_receivable` is null or absent | Revenue quality and collection pressure are insufficiently supported. | medium | easy | AkShare balance sheet amount field |
| 002050 | 三花智控 | advanced_manufacturing_growth | 存货 | missing |  | financial_indicator | 20260331 | `financial_metrics.inventory` is null or absent | Inventory cycle and impairment pressure are insufficiently supported. | medium | easy | AkShare balance sheet amount field |
| 002050 | 三花智控 | advanced_manufacturing_growth | 研发费用率 | missing |  | missing |  | no structured field | Technology investment intensity is insufficiently supported. | medium | easy | R&D expense plus revenue |
| 002050 | 三花智控 | advanced_manufacturing_growth | 新业务收入 / 订单 | partial | 汽车零部件 40.07% | business_composition / missing | 2025-12-31 | segment exists, but new-business revenue split and order evidence are absent | New-business delivery cannot be separated from expectation. | high | hard | Announcement / annual report text / curated input |
| 002050 | 三花智控 | advanced_manufacturing_growth | 大客户收入占比 | missing |  | missing |  | no structured field | Customer dependence cannot be quantified. | high | hard | Annual report customer concentration disclosure / curated input |
| 002050 | 三花智控 | advanced_manufacturing_growth | 海外收入占比 | available | 国外销售 42.96% | business_composition | 2025-12-31 |  | Global exposure can be described with evidence. | medium | medium | AkShare 主营构成地区分类 / `stock_zygc_em` |
| 000426 | 兴业银锡 | resource_swing | 核心商品价格 | available | 白银 19253.0; 锡 410420.0 | commodity_prices | 2026-05-18 |  | Resource-cycle external variable is supported. | high | medium | Existing external commodity connector |
| 000426 | 兴业银锡 | resource_swing | 主营矿种收入占比 | available | 矿产银 39.17%; 矿产锡 29.70%; 矿产锌 17.57%; 矿产铅 3.98% | business_composition | 2025-12-31 |  | Revenue exposure is supported. | high | medium | AkShare 主营构成 / `stock_zygc_em` |
| 000426 | 兴业银锡 | resource_swing | 毛利率 | available | 69.07% | financial_indicator | 20260331 |  | Margin validation is supported. | high | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 000426 | 兴业银锡 | resource_swing | 经营现金流 | available | 1216893859.45 | financial_indicator | 20260331 |  | Profit quality has a base field. | high | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 000426 | 兴业银锡 | resource_swing | 资本开支 | missing |  | missing |  | no structured field | Expansion cycle and free-cash-flow pressure are insufficiently supported. | medium | medium | Cash-flow statement capex-related cash outflow |
| 000426 | 兴业银锡 | resource_swing | 产量 / 成本 | partial | segment revenue ratio and gross margin only | business_composition | 2025-12-31 | no production volume or unit cost | Cost curve and volume-price elasticity are insufficiently supported. | medium | hard | Annual report / announcement text / curated input |
| 000426 | 兴业银锡 | resource_swing | 资产负债率 | available | 41.40% | financial_indicator | 20260331 |  | Leverage pressure has a base field. | medium | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 000426 | 兴业银锡 | resource_swing | 存货 | missing |  | financial_indicator | 20260331 | `financial_metrics.inventory` is null or absent | Inventory cycle is insufficiently supported. | medium | easy | AkShare balance sheet amount field |
| 000426 | 兴业银锡 | resource_swing | 应收账款 | missing |  | financial_indicator | 20260331 | `financial_metrics.accounts_receivable` is null or absent | Revenue quality is insufficiently supported. | medium | easy | AkShare balance sheet amount field |
| 300308 | 中际旭创 | right_trend_growth | 收入增速 | available | 192.12% | financial_indicator | 20260331 |  | Growth validation has a base field. | high | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 300308 | 中际旭创 | right_trend_growth | 利润增速 | available | 262.28% | financial_indicator | 20260331 |  | Profit elasticity has a base field. | high | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 300308 | 中际旭创 | right_trend_growth | 毛利率 | available | 46.06% | financial_indicator | 20260331 |  | Margin validation is supported. | high | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 300308 | 中际旭创 | right_trend_growth | 经营现金流 | available | 3367573676.62 | financial_indicator | 20260331 |  | Profit quality has a base field. | high | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 300308 | 中际旭创 | right_trend_growth | 订单持续性 | missing |  | missing |  | no structured field | Sustainability of demand is insufficiently supported. | high | hard | Announcement / annual report order disclosure / curated input |
| 300308 | 中际旭创 | right_trend_growth | 客户资本开支 | missing |  | missing |  | no structured field | Demand-side dependency cannot be validated. | medium | hard | Customer public reports, sector data, or curated input |
| 300308 | 中际旭创 | right_trend_growth | 估值消化能力 | partial | PE TTM 78.21 plus growth fields | valuation + financial_indicator | 2026-05-15 | no historical percentile or peer context | Valuation context remains incomplete. | medium | medium | Historical valuation and peer context |
| 300308 | 中际旭创 | right_trend_growth | 客户集中度 | missing |  | missing |  | no structured field | Single-customer dependency cannot be quantified. | high | hard | Annual report customer concentration disclosure / curated input |
| 002371 | 北方华创 | semiconductor_cycle | 收入增速 | available | 25.80% | financial_indicator | 20260331 |  | Growth validation has a base field. | high | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 002371 | 北方华创 | semiconductor_cycle | 毛利率 | available | 40.77% | financial_indicator | 20260331 |  | Margin validation is supported. | high | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 002371 | 北方华创 | semiconductor_cycle | 存货 | missing |  | financial_indicator | 20260331 | `financial_metrics.inventory` is null or absent | Semiconductor inventory cycle is insufficiently supported. | medium | easy | AkShare balance sheet amount field |
| 002371 | 北方华创 | semiconductor_cycle | 订单 / 合同负债 | missing |  | missing |  | no order backlog or contract-liability field | Future revenue visibility is insufficiently supported. | high | medium | Contract liabilities from balance sheet; order evidence from text |
| 002371 | 北方华创 | semiconductor_cycle | 研发费用率 | missing |  | missing |  | no structured field | Technology investment intensity is insufficiently supported. | medium | easy | R&D expense plus revenue |
| 002371 | 北方华创 | semiconductor_cycle | 资本开支 | missing |  | missing |  | no structured field | Capacity cycle evidence is insufficiently supported. | medium | medium | Cash-flow statement capex-related cash outflow |
| 002371 | 北方华创 | semiconductor_cycle | 国产替代收入证据 | missing |  | missing |  | no structured field | Domestic-substitution thesis cannot be grounded in revenue evidence. | high | hard | Announcement / annual report text / curated input |
| 002371 | 北方华创 | semiconductor_cycle | 应收账款 | missing |  | financial_indicator | 20260331 | `financial_metrics.accounts_receivable` is null or absent | Revenue quality is insufficiently supported. | medium | easy | AkShare balance sheet amount field |
| 002371 | 北方华创 | semiconductor_cycle | 估值分位 | partial | PE TTM 76.95 | valuation | 2026-05-15 | point-in-time valuation only | Valuation context remains incomplete. | medium | medium | Historical valuation series and percentile calculation |
| 601899 | 紫金矿业 | resource_core | 核心商品价格 | available | 铜 104330.0; 黄金 1003.05 | commodity_prices | 2026-05-18 |  | Resource-cycle external variable is supported. | high | medium | Existing external commodity connector |
| 601899 | 紫金矿业 | resource_core | 主营矿种收入占比 | available | 金、铜等产品收入占比可用 | business_composition | 2025-12-31 |  | Revenue exposure is supported. | high | medium | AkShare 主营构成 / `stock_zygc_em` |
| 601899 | 紫金矿业 | resource_core | 毛利率 | available | 36.33% | financial_indicator | 20260331 |  | Margin validation is supported. | high | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 601899 | 紫金矿业 | resource_core | 经营现金流 | available | 27831931440.0 | financial_indicator | 20260331 |  | Profit quality has a base field. | high | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 601899 | 紫金矿业 | resource_core | 资本开支 | missing |  | missing |  | no structured field | Expansion cycle and free-cash-flow pressure are insufficiently supported. | medium | medium | Cash-flow statement capex-related cash outflow |
| 601899 | 紫金矿业 | resource_core | 产量 / 成本 | partial | segment revenue ratio and gross margin only | business_composition | 2025-12-31 | no production volume or unit cost | Cost curve and volume-price elasticity are insufficiently supported. | medium | hard | Annual report / announcement text / curated input |
| 601899 | 紫金矿业 | resource_core | 资产负债率 | available | 51.37% | financial_indicator | 20260331 |  | Leverage pressure has a base field. | medium | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 601899 | 紫金矿业 | resource_core | 存货 | missing |  | financial_indicator | 20260331 | `financial_metrics.inventory` is null or absent | Inventory cycle is insufficiently supported. | medium | easy | AkShare balance sheet amount field |
| 601899 | 紫金矿业 | resource_core | 应收账款 | missing |  | financial_indicator | 20260331 | `financial_metrics.accounts_receivable` is null or absent | Revenue quality is insufficiently supported. | medium | easy | AkShare balance sheet amount field |
| 603993 | 洛阳钼业 | resource_swing | 核心商品价格 | partial | 铜 104330.0 | commodity_prices | 2026-05-18 | cobalt and molybdenum are missing | Commodity exposure is only partly supported. | high | medium | Stable domestic public sources for cobalt and molybdenum |
| 603993 | 洛阳钼业 | resource_swing | 主营矿种收入占比 | available | 铜 26.66%; 钼 3.06%; 钴 2.99%; 铌 1.75% | business_composition | 2025-12-31 |  | Revenue exposure is supported. | high | medium | AkShare 主营构成 / `stock_zygc_em` |
| 603993 | 洛阳钼业 | resource_swing | 毛利率 | available | 22.88% | financial_indicator | 20260331 |  | Margin validation is supported. | high | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 603993 | 洛阳钼业 | resource_swing | 经营现金流 | available | 11329218827.44 | financial_indicator | 20260331 |  | Profit quality has a base field. | high | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 603993 | 洛阳钼业 | resource_swing | 资本开支 | missing |  | missing |  | no structured field | Expansion cycle and free-cash-flow pressure are insufficiently supported. | medium | medium | Cash-flow statement capex-related cash outflow |
| 603993 | 洛阳钼业 | resource_swing | 产量 / 成本 | partial | segment revenue ratio and gross margin only | business_composition | 2025-12-31 | no production volume or unit cost | Cost curve and volume-price elasticity are insufficiently supported. | medium | hard | Annual report / announcement text / curated input |
| 603993 | 洛阳钼业 | resource_swing | 资产负债率 | available | 52.03% | financial_indicator | 20260331 |  | Leverage pressure has a base field. | medium | easy | AkShare 财务摘要 / `stock_financial_abstract` |
| 603993 | 洛阳钼业 | resource_swing | 存货 | missing |  | financial_indicator | 20260331 | `financial_metrics.inventory` is null or absent | Inventory cycle is insufficiently supported. | medium | easy | AkShare balance sheet amount field |
| 603993 | 洛阳钼业 | resource_swing | 应收账款 | missing |  | financial_indicator | 20260331 | `financial_metrics.accounts_receivable` is null or absent | Revenue quality is insufficiently supported. | medium | easy | AkShare balance sheet amount field |

## High-Priority Missing Or Partial Indicators

| indicator | affected stock | status | why it matters |
| --- | --- | --- | --- |
| 新业务收入 / 订单 | 002050 | partial | New-business segment context exists, but order and revenue-split evidence is not structured. |
| 大客户收入占比 | 002050 | missing | Customer dependency cannot be quantified. |
| 订单持续性 | 300308 | missing | Demand durability cannot be validated from the evidence pack. |
| 客户集中度 | 300308 | missing | Customer dependency and revenue concentration risk cannot be quantified. |
| 订单 / 合同负债 | 002371 | missing | Semiconductor equipment revenue visibility is not sufficiently supported. |
| 国产替代收入证据 | 002371 | missing | The domestic-substitution thesis is not grounded in revenue or customer evidence. |
| 核心商品价格 | 603993 | partial | Copper is available, but cobalt and molybdenum remain absent. |

## Best Next-Stage Fields To Add

1. `financial_metrics.inventory` and `financial_metrics.accounts_receivable`

   These recur across almost all audited names and directly improve revenue-quality, inventory-cycle, and working-capital analysis. They are easy if mapped from balance-sheet amount fields, but should not be proxied by turnover ratios.

2. `financial_metrics.r_and_d_expense_ratio`

   This improves `advanced_manufacturing_growth` and `semiconductor_cycle` reports, especially when judging technology investment intensity. It should be computed from R&D expense and revenue.

3. `financial_metrics.capex`

   This improves resource-stock and semiconductor-cycle interpretation by adding expansion-cycle and cash-flow pressure context. It likely comes from cash-flow statement capex-related cash outflow.

4. `orders_or_contract_liabilities`

   For `semiconductor_cycle` and `right_trend_growth`, this is one of the most important bridges between reported financials and future revenue visibility. Contract liabilities may be structured from financial statements; explicit orders need text extraction or curated input.

5. `customer_concentration`

   This is essential for advanced manufacturing and right-trend growth, but likely requires annual report text extraction or manual curation.

## Fields AkShare Financial Statements Can Likely Improve

| field | expected source | notes |
| --- | --- | --- |
| inventory | balance sheet amount field | Do not map from inventory turnover ratio or days. |
| accounts_receivable | balance sheet amount field | Do not map from receivables turnover ratio or days. |
| R&D expense ratio | income statement R&D expense plus revenue | Add both numerator and ratio if possible. |
| capex | cash-flow statement purchase/construction cash outflow | Use source trace and period. |
| contract liabilities | balance sheet | Useful partial proxy for order visibility in semiconductor equipment. |
| historical valuation percentile | valuation history | Requires local historical series and percentile calculation. |

## Fields Needing Text, Research, Or Curated Input

| field | reason |
| --- | --- |
| new-business revenue / orders | Often disclosed in narrative form and may not align with standard segment tables. |
| major-customer revenue share | Usually appears in annual report customer concentration disclosure. |
| customer concentration | Same disclosure family as major-customer revenue share. |
| customer capex | Requires customer-side reports or curated industry data. |
| order durability | Requires order backlog, contract, customer program, or management discussion evidence. |
| domestic-substitution revenue evidence | Requires text-level evidence tied to customers, revenue, or product validation. |
| production volume / unit cost | Resource annual reports often disclose this outside generic financial tables. |
| cobalt and molybdenum commodity prices | Current connector audit says stable domestic primary sources are not yet promoted. |

## Fields Not Recommended Right Now

| field | reason |
| --- | --- |
| technical-price modules | Outside the fundamental-skill boundary and not needed for this audit. |
| account or execution fields | Outside project scope and not relevant to evidence-pack quality. |
| price targets or position-style fields | Would pull the project away from source-grounded fundamental evidence. |
| low-source-quality commodity proxies | Especially for cobalt and molybdenum; stale, foreign-reference-only, or ambiguous units should stay excluded. |
| news-only sentiment fields | News can help context, but it should not replace structured fundamentals or source-traced text evidence. |

## Impact On Existing Reports

No existing report should be downgraded merely because this audit finds missing fields. The current behavior is directionally correct: when must-have indicators are absent, the AI report should keep the analysis bounded and state what cannot be judged. The improvement path is to add source-traced data fields later, not to force stronger language into the report.

## Next-Stage Recommendation

The next stage should be a data-field design pass, not a dashboard pass:

1. Add a schema proposal for balance-sheet amount fields: inventory and accounts receivable.
2. Add R&D expense and R&D expense ratio.
3. Add capex from cash-flow statement fields.
4. Design a small curated-input/text-extraction interface for orders, customer concentration, production volume, unit cost, and domestic-substitution revenue evidence.
5. Keep cobalt and molybdenum as explicit external commodity gaps until stable domestic sources are confirmed.
