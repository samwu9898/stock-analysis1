# Research Intelligence P1.1 Resource Expansion Design Audit

Date: 2026-05-24

Revision: v1.1

Stage: Design audit only. This document adds design guidance only. It must not change code, tests, P1 schema, deterministic pipeline behavior, classifier rules, connectors, scoring, readiness, HTML renderer, Dashboard, generated output, regression fixtures, or existing artifact semantics.

Target expansion: `resource_core` and `resource_swing` only.

Primary sample: `000426` Xingye Silver & Tin / 兴业银锡, current `strategy_type=resource_swing`.

Future validation / boundary samples: `601899` Zijin Mining and `603993` CMOC may be retained for later `resource_core` / diversified-resource boundary validation, but P1.1 implementation first version should use only `resource_swing` and only `000426` as the primary sample.

## 1. Expansion Positioning

P1.1 has already accepted AI Datacenter, CXO, Satellite, and Low Altitude expansions after observation. This document designs the next narrow P1.1 expansion for resource companies.

The expansion remains an independent Research Intelligence artifact:

```text
evidence_pack_<code>.json
+ optional P0 research intelligence artifacts
-> research_intelligence_p1_<code>.json
-> research_questions_p1_<code>.json
-> research_questions_p1_<code>.md
```

The expansion should convert commodity, macro, FX, asset, operation, financial, and risk assumptions into evidence-gated driver-factor rows and research questions. It must not become a trading system, valuation model, commodity forecast, technical-analysis layer, dashboard panel, connector project, or deterministic scoring input.

## 2. Non-Negotiable Boundaries

This design is limited to `strategy_type=resource_core` and `strategy_type=resource_swing`.

Do not modify:

- P1 schema.
- Deterministic pipeline.
- Classifier routing.
- Data connectors.
- Scoring.
- Readiness.
- HTML Report.
- Dashboard.
- `status`.
- `confidence`.
- `score` / `fundamental_score`.
- `strategy_type`.
- `sub_type`.

Do not:

- connect trading accounts;
- output trading advice;
- output target price, position size, buy / sell / add / reduce / clear-position language, stop-loss / take-profit, profit-loss ratio, or execution instructions;
- perform technical analysis;
- use K-line / candlestick logic;
- add new data sources;
- feed P1.1 back into deterministic conclusions.

Preserve the P1.1 interpretation guards:

- Commodity price is not company revenue.
- Resource reserve / resource volume is not production volume.
- Production volume is not sales volume unless both are disclosed and reconciled.
- Capex is not capacity release, mine ramp-up, smelter utilization, or revenue conversion.
- Inventory change is not direct demand proof.
- Missing hedging disclosure means hedging status is not assessable; price risk must not be written as hedged.
- `resource_core` steadiness is not a fact unless cash flow, debt, cost position, sustaining capex, and dividend evidence support it.
- Commodity cycle context is background until bridged to company segment exposure, realized price, volume, cost, margin, cash flow, working capital, and balance-sheet evidence.

## 3. Current Evidence-Pack Capability

For `000426`, current fixtures indicate that the evidence pack can usually support only a conservative P1.1 resource matrix.

Current `evidence_pack` may have:

- `stock.code`, `stock.name`, `stock.strategy_type`, `stock.sub_type`.
- `stock.status`, `stock.confidence`, `stock.fundamental_score` as read-only context only.
- `basic_info.industry`.
- `basic_info.main_business`.
- `business_composition[]` with segment name, classification type, period, revenue ratio, revenue, gross margin, and profit when present.
- `financial_metrics.period`, `revenue`, `revenue_yoy`, `gross_margin`, `net_margin`, `net_profit`, `deducted_net_profit`, `operating_cashflow`, `accounts_receivable`, `contract_liabilities`, `inventory`, and `capex` when present.
- `valuation_metrics` as explainability context only; no target price or trading framing.
- `confidence_basis.missing_fields`, `confidence_basis.data_coverage`, and `confidence_basis.confidence_breakdown`.
- `enhanced_must_track_indicators[]`.
- `risk_flags`, `unknown_or_missing_evidence`, `missing_fields`, `data_limitations`, `source_trace_summary`, and `forbidden_terms_check`.

Current `evidence_pack` usually does not reliably have:

- Structured commodity price history by product and period.
- Realized selling price by product.
- Production volume and sales volume by metal / mine / smelter.
- Ore grade, recovery rate, concentrate grade, or resource quality.
- Reserves / resources by mine with reporting standard and date.
- Mine, smelter, or processing capacity and utilization.
- Cost curve position, cash cost, all-in sustaining cost, unit mining / processing cost.
- Hedging / derivative notional, fair value, maturity, hedge accounting, or realized gain / loss.
- USD / RMB FX exposure by revenue, cost, debt, cash, or derivative.
- Debt maturity, interest rate structure, refinancing schedule, or covenant detail.
- Sustaining capex vs expansionary capex split.
- Depreciation / depletion by mine or asset group.
- Working-capital detail by inventory type, receivable customer, payable supplier, or prepayment.
- Environmental, safety, mine accident, regulatory penalty, tailings, water, land, or permit event history.
- Longitudinal disclosure consistency.
- Independent multi-source consensus beyond source-bucket counting.

## 4. Driver Factor Matrix Contract

Every resource driver row must use the existing P1.1 driver-factor contract:

```text
driver_factor
driver_scope
required_evidence
available_evidence
missing_evidence
company_transmission_path
data_availability_status
confidence_cap
not_assessable_reason
what_was_checked
source_refs
research_question
interpretation_guard
```

For this expansion, every driver must define:

- `required_evidence`
- `available_evidence`
- `missing_evidence`
- `company_transmission_path rule`
- `not_assessable condition`
- `research_question`
- `interpretation_guard`

The matrix is evidence-pack-only for P1.1 implementation. Future connector needs are recorded as missing evidence, not implemented in this phase.

## 5. Resource Driver Factor Matrix

### 5.1 Macro / Commodity / FX Drivers

| Driver factor | required_evidence | available_evidence from current evidence_pack | missing_evidence / future connector | company_transmission_path rule | not_assessable condition | research_question | interpretation_guard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Core commodity price exposure | Main commodity products; product revenue ratio; realized selling price; production / sales volume; cost and margin bridge | `basic_info.main_business`; `business_composition[].segment_name`, `revenue_ratio`, `revenue`, `gross_margin` when product segments exist; `financial_metrics.revenue`, `gross_margin`, `operating_cashflow` | Product-level realized price; production and sales volume; unit cost; commodity price series linked to product mix | Valid only when path cites concrete product / segment exposure nodes and financial fields. If product exposure is absent or only commodity context exists, use `传导路径无法从当前证据包验证`. | Mark `not_assessable` when no product / segment exposure node exists, or when only external commodity prices exist without company product bridge. | Which commodities actually drive company revenue, margin, and cash flow, and what product-level evidence links external prices to realized company economics? | Do not treat commodity price as company revenue or use generic commodity benefit language. |
| Commodity price cycle | Commodity cycle phase; price history; inventory cycle; company realized price; revenue / margin / cash-flow sensitivity | Segment exposure and financial metrics may show after-the-fact company results; source trace may show financial statement coverage | Commodity price cycle data; realized price; product inventory; customer demand and downstream inventory; sales volume | A valid path needs company product exposure plus realized price / volume / margin nodes. If cycle is only external context, use fallback. | Mark `not_assessable` when cycle evidence cannot be linked to company realized price, volume, margin, or cash flow. | Has the commodity cycle translated into company realized price, sales volume, gross margin, working capital, and operating cash flow? | Do not write cycle up/down as company performance without realized company evidence. |
| USD / RMB FX exposure | Export revenue; USD-priced commodity sales; imported costs; foreign-currency debt; FX gains / losses; hedging | Geographic or product segments may exist; financial metrics may include revenue and profit but not FX detail | FX exposure note; currency split of revenue/cost/debt/cash; FX gain/loss; FX hedge detail | Valid only if evidence pack contains concrete overseas / currency / FX field nodes plus financial fields. Otherwise use fallback. | Mark `not_assessable` when currency denomination, overseas revenue, foreign-currency debt, or FX gain/loss evidence is absent. | What revenue, cost, debt, cash, or derivative items expose the company to USD / RMB movement, and how is that visible in profit or cash flow? | Do not infer FX exposure solely from commodity type or export possibility. |
| Interest-rate / financing-cost pressure | Debt amount; interest expense; rate structure; debt maturity; capex plan; operating cash flow; liquidity | Financial metrics may show profit, operating cash flow, and sometimes debt-related fields if available; capex may be available | Interest expense; short / long-term debt; maturity schedule; refinancing terms; restricted cash; covenants | A concrete path may cite debt / cash-flow / capex nodes when present, but cannot assess refinancing without maturity and interest data. If no debt nodes exist, use fallback. | Mark `not_assessable` when debt, interest expense, maturity, or liquidity evidence is absent. | Does financing cost or refinancing pressure constrain sustaining capex, expansion capex, liquidity, or dividend capacity? | Do not infer debt-cycle pressure from capex or industry leverage alone. |
| Global demand / inventory cycle | End-market demand; smelter / exchange / downstream inventory; company sales volume; inventory by product; receivables and cash conversion | `financial_metrics.inventory`, `accounts_receivable`, `operating_cashflow`, and revenue may be available | Global demand series; exchange inventories; downstream inventory; product-level company inventory; sales volume | Valid only when company inventory / sales / receivable / cash nodes are cited. External demand or inventory alone uses fallback. | Mark `not_assessable` when company sales volume and product inventory are missing, or external inventory cannot be bridged to company data. | Are global demand and inventory-cycle signals visible in company sales volume, product inventory, receivables, and operating cash flow? | Do not treat inventory change directly as demand judgment. |
| Policy / supply constraint | Mine permit / quota / production restriction; environmental policy; supply disruption; affected commodity; company mine / capacity / output bridge | `risk_flags`, `basic_info`, or business composition may show resource exposure; company policy impact data usually absent | Policy event connector; permit / quota parser; mine-level production restrictions; environmental inspection records | Policy or supply constraint can be context only unless path cites company mine, permit, capacity, output, or financial impact nodes. Otherwise use fallback. | Mark `not_assessable` when policy / supply constraint lacks company-specific asset or operating impact evidence. | Which policy or supply constraints affect the company's mines, smelters, permits, output, costs, or capex requirements? | Policy / supply constraint is not automatic pricing power or production impact. |

### 5.2 Company / Asset / Operation Drivers

| Driver factor | required_evidence | available_evidence from current evidence_pack | missing_evidence / future connector | company_transmission_path rule | not_assessable condition | research_question | interpretation_guard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Commodity revenue exposure | Revenue by commodity; revenue ratio; segment gross margin; period; product definition | `business_composition[]` may provide segment names, revenue, revenue ratio, gross margin, and period; total revenue may exist | Product-level revenue if segments are aggregated; realized price; sales volume; customer mix | A valid path may cite segment revenue / ratio and total revenue. It must state exposure only, not price sensitivity unless price and volume data exist. | Mark `not_assessable` when no commodity or product segment field exists. | What share of revenue and gross margin comes from each commodity, and what segment definitions support the exposure? | Revenue exposure is not realized commodity price sensitivity by itself. |
| Production volume | Mine / product output; concentrate / metal content; period; production vs capacity; production disruptions | Usually missing; business description may show resource operations but not output | Mine-level production parser; annual-report operating metrics; product output table | Valid only when production volume field/value nodes exist. Revenue, reserves, or capacity cannot substitute. If absent, use fallback. | Mark `not_assessable` when product or mine production volume is absent. | What production volume by commodity and mine validates operating output, and how does it compare with capacity and sales volume? | Do not treat resource amount, revenue, or capacity as production. |
| Sales volume | Product sales volume; realized selling price; revenue reconciliation; inventory movement; customer / region split | Usually missing; revenue may exist | Product sales table; realized price; inventory by product; customer concentration | Valid only when sales volume field/value nodes exist. Production volume cannot substitute unless reconciled to sales and inventory. | Mark `not_assessable` when sales volume or realized price is absent. | What sales volume and realized price reconcile reported commodity revenue, and what inventory movement explains production-sales gaps? | Do not treat production volume as sales volume without reconciliation. |
| Grade / resource quality | Ore grade; recovery rate; concentrate grade; mine dilution; by-product credit; cost and margin bridge | Usually missing; business composition may show mining exposure only | Mine technical disclosure parser; reserve report parser; operating metrics | Valid only when grade / recovery / quality nodes exist. Segment gross margin may be checked but cannot prove grade quality. | Mark `not_assessable` when grade, recovery, or quality data is absent. Missing grade data does not support positive or negative quality assessment. | What ore grade and recovery evidence supports resource quality and cost position by mine or product? | Do not infer resource quality from reserve size or gross margin alone. Absence of grade data is not proof of poor resource quality; missing data can only produce `missing` / `not_assessable`, not a positive or negative quality conclusion. |
| Reserves / resources | Reserves and resources by mine; reporting standard; commodity content; grade; update date; depletion and conversion | Usually missing; main business may identify mine ownership but not reserve detail | Reserve report parser; annual-report reserve table; mine-life tracker | Valid only when reserve / resource field/value nodes exist. It must not become production, sales, or cash-flow evidence. | Mark `not_assessable` when reserve / resource quantity, grade, standard, or date is absent. | What reserves / resources are disclosed by mine, and how do grade, depletion, and conversion affect mine life? | Do not treat resource reserve as production volume or near-term output. |
| Mine / smelter / processing capacity | Mine capacity; processing capacity; smelting capacity; utilization; bottleneck; expansion status; product bridge | Usually missing; capex may be available as financial outflow only | Capacity table; utilization; project acceptance; permits; production reconciliation | Valid only when capacity field/value nodes exist. Capex or business description cannot substitute for capacity release. | Mark `not_assessable` when capacity or utilization evidence is absent. | What mine, smelter, or processing capacity is available and utilized, and where are bottlenecks? | Do not treat capex or project plans as released capacity. |
| Inventory | Inventory amount; inventory type; product inventory; raw material / concentrate / finished goods split; write-down; sales-volume bridge | `financial_metrics.inventory` may be available; revenue and operating cash flow may be available | Inventory breakdown; inventory age; commodity type; write-down detail; sales/production reconciliation | A concrete path may cite inventory, revenue, and cash-flow nodes, but demand interpretation requires product and sales-volume bridge. | Mark `not_assessable` for demand or price-cycle judgment when only aggregate inventory exists. Even if inventory decreases while revenue grows, demand remains not assessable without product-level inventory split and sales / production reconciliation. | What inventory type is building or falling, and does it reflect production-sales timing, price movement, or demand / collection pressure? | Do not treat inventory change directly as demand judgment. Inventory decline plus revenue growth is still two financial observations, not an operating demand signal. Demand judgment requires product-level inventory split, sales volume, production / sales reconciliation, or customer demand evidence. |
| Hedging / derivative exposure | Hedge notional; commodity; maturity; hedge accounting; fair value; realized / unrealized gain or loss; risk policy | Usually missing; risk flags may mention price volatility but not hedge detail | Derivative note parser; futures / hedging disclosure; fair-value movement extractor | Valid only when hedging / derivative field/value nodes exist. If disclosure is absent, use fallback and keep price risk unhedged-status unknown. | Mark `not_assessable` when hedging notional, commodity, maturity, or gain/loss evidence is absent. | Does the company use commodity or FX hedges, and what mismatch, maturity, or fair-value risk remains? | Do not write price risk as hedged when hedging disclosure is missing. |
| Cost curve position | Cash cost; all-in sustaining cost; unit mining / processing cost; by-product credit; grade; scale; peer comparison | Gross margin may exist; operating cash flow may exist | Unit cost; mine-level cost; AISC; peer cost curve; energy / labor / material cost split | A path may cite gross margin and cash flow only as financial observations. Cost-curve position needs unit cost and peer evidence. | Mark `not_assessable` when unit cost or cost-curve evidence is absent. | Where does the company sit on the cost curve, and what evidence links grade, recovery, unit cost, and margin resilience? | Do not infer low-cost position from gross margin alone. |

### 5.3 Financial Drivers

| Driver factor | required_evidence | available_evidence from current evidence_pack | missing_evidence / future connector | company_transmission_path rule | not_assessable condition | research_question | interpretation_guard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Revenue sensitivity to commodity price | Product revenue ratio; realized selling price; sales volume; commodity price series; pricing formula; lag | Segment revenue / ratio and total revenue may exist; revenue YoY may exist as a financial observation only | Realized price; sales volume; pricing formula; price lag; commodity series mapped to products | Valid only if realized selling price and sales volume can both be cited with product exposure. If realized selling price or sales volume is missing, `company_transmission_path` must be `传导路径无法从当前证据包验证` and `confidence_cap=not_assessable`. Segment revenue, total revenue, and revenue YoY cannot be combined into commodity price transmission. | Mark `not_assessable` when realized selling price and sales volume are not both available. Even if segment revenue and revenue YoY both exist, revenue growth must not be attributed to commodity price. | How sensitive is revenue to each commodity after considering product mix, realized price, sales volume, pricing formula, and pricing lag? | Do not treat commodity price movement as revenue movement. Do not infer commodity price transmission from segment revenue plus revenue YoY. Revenue growth cannot be attributed to commodity price unless realized selling price and sales volume are both cited. |
| Gross margin sensitivity | Product gross margin; realized price; unit cost; energy / labor / treatment charge; by-product credit; inventory cost method | Total or segment gross margin may exist | Product margin; unit cost; cost split; treatment / refining charges; inventory accounting | A concrete path may cite gross margin fields, but sensitivity needs price and cost drivers. | Mark `not_assessable` when unit cost, realized price, or product margin bridge is missing. | Which price and cost variables explain gross margin movement by commodity or segment? | Do not infer margin leverage from commodity exposure alone. |
| Operating cash flow | Operating cash flow; revenue; receivables; payables; inventory; capex separation; commodity cycle bridge | `financial_metrics.operating_cashflow`, revenue, accounts receivable, inventory, capex may be available | Payables; cash conversion cycle; product inventory; realized price; working-capital notes | A concrete path may cite cash flow, revenue, receivables, inventory, and capex as financial nodes, but must frame quality as a question if working-capital detail is missing. | Mark `not_assessable` for cash-flow durability when working-capital detail and product cycle data are absent. | Does operating cash flow validate commodity revenue quality after receivables, inventory, payables, and price-cycle effects? | Cash flow is validation evidence, not proof of resource-core steadiness by itself. |
| Capex: sustaining vs expansionary | Capex total; sustaining capex; expansion capex; project / mine mapping; construction progress; acceptance; output bridge | `financial_metrics.capex` may be available | Capex split; project list; mine mapping; acceptance / ramp-up; funding source | A path may cite capex only as investment / cash outflow. It must not claim capacity release or output growth without project and operating nodes. | Mark `not_assessable` when capex split or project-output bridge is missing. | What portion of capex maintains existing assets versus expands capacity, and what evidence links projects to accepted capacity and output? | Do not treat capex as capacity release or production growth. |
| Debt / liquidity / refinancing pressure | Debt amount; cash; interest expense; maturity schedule; refinancing plan; covenants; operating cash flow; capex | Operating cash flow and capex may exist; debt fields may or may not exist | Debt maturity; interest-rate structure; restricted cash; refinancing events; covenants | Valid only if debt / liquidity nodes exist. Cash flow and capex alone cannot establish refinancing pressure. | Mark `not_assessable` when debt, maturity, interest expense, or liquidity evidence is absent. | Does debt maturity or financing cost pressure constrain mine operation, sustaining capex, expansion plans, or dividends? | Do not infer refinancing risk without balance-sheet and maturity evidence. |
| Depreciation / depletion | Depreciation; depletion; amortization; mine life; asset base; impairment; production units method | Usually missing unless financial fields expose depreciation / amortization | Fixed-asset note parser; mine depletion policy; impairment notes; reserve depletion | Valid only when depreciation / depletion field/value nodes exist. Profitability cannot be fully interpreted without asset-consumption evidence. | Mark `not_assessable` when depreciation / depletion or asset life evidence is absent. | How do depreciation, depletion, asset life, and reserve conversion affect reported profit and cash-flow quality? | Do not compare profitability without checking depletion and asset-life policy. |
| Working capital | Receivables; inventory; payables; prepayments; customer / supplier terms; commodity price movement; sales-volume bridge | Receivables, inventory, revenue, and operating cash flow may be available | Payables; prepayments; aging; product inventory; customer / supplier concentration; sales volume; production / sales reconciliation | A path may cite available working-capital fields but must identify missing payables, aging, product detail, and operating-volume bridge. | Mark `not_assessable` for cycle interpretation when only aggregate receivables or inventory exists. Inventory decline plus revenue growth must not be interpreted as strong demand without product-level inventory split, sales volume, production / sales reconciliation, or customer demand evidence. | Are working-capital movements driven by price, volume, inventory timing, customer collection, or supplier terms? | Do not treat aggregate working-capital movement as demand, pricing, or cash quality proof. Two financial observations, such as lower inventory and higher revenue, do not equal an operating demand signal. |
| Dividend capacity for resource_core | Operating cash flow; free cash flow after sustaining capex; debt / liquidity; cost position; reserve life; dividend policy; payout history | Operating cash flow and capex may be available; dividend fields usually missing | Dividend history; payout ratio; sustaining capex split; debt maturity; reserve life; cost curve | Valid only if cash flow, capex split, debt/liquidity, and dividend evidence exist. For `resource_swing`, treat as optional context, not core-stability proof. | Mark `not_assessable` when any core support leg is missing: cash flow, debt, sustaining capex, cost position, or dividend evidence. | Does evidence support sustainable dividend capacity after sustaining capex, debt service, reserve depletion, and commodity-cycle stress? | Do not write `resource_core` steadiness as fact unless cash flow, debt, cost, sustaining capex, reserve life, and dividend evidence support it. |

### 5.4 Risk Drivers

| Driver factor | required_evidence | available_evidence from current evidence_pack | missing_evidence / future connector | company_transmission_path rule | not_assessable condition | research_question | interpretation_guard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Commodity price volatility | Product exposure; commodity price history; realized price; hedging status; margin and cash-flow sensitivity | Product exposure and financial metrics may exist; hedging detail usually absent | Commodity price series; realized price; hedge disclosure; sensitivity analysis | Valid only when company product exposure and financial nodes are cited; hedging cannot be assumed. If exposure itself is absent, use fallback. | Mark `not_assessable` when product exposure, realized price, or hedging status is absent. | How does commodity price volatility flow through product revenue, margin, hedging gain/loss, and operating cash flow? | Do not claim risk is hedged or unhedged beyond disclosed evidence. |
| Production disruption | Mine accident; maintenance shutdown; permit suspension; grade decline; equipment issue; affected output; financial impact | Risk flags may exist; financial metrics may show results but not disruptions | Mine event connector; safety / regulatory event parser; operating announcement parser | Valid only when disruption event or output field/value nodes exist. Revenue changes alone cannot identify disruption. | Mark `not_assessable` when production event and output evidence are absent. | Have mine, smelter, processing, safety, or permit disruptions affected production, cost, revenue, or cash flow? | Do not infer absence of disruption from ordinary revenue data. |
| Resource reserve depletion | Reserve base; mine life; annual production; depletion rate; exploration replacement; impairment | Usually missing | Reserve report; mine-life calculation; exploration additions; depletion note | Valid only when reserve and production nodes exist. Reserves alone do not determine near-term output; production alone does not prove reserve sufficiency. | Mark `not_assessable` when reserves, production, or depletion rate is absent. | Is reserve depletion or inadequate replacement affecting mine life, capex need, and long-term production visibility? | Do not treat resource quantity as production or mine-life proof without grade and depletion context. |
| Environmental / safety / regulatory risk | Environmental penalties; safety accidents; tailings / water / land permits; production restrictions; compliance cost; remediation capex | `risk_flags` may mention generic risk; company event data usually absent | Regulator penalty connector; mine safety database; environmental note parser; permit tracker | Valid only when company-specific event, permit, penalty, or compliance cost nodes exist. Otherwise use fallback. | Mark `not_assessable` when event / permit / compliance evidence is absent. | What environmental, safety, or regulatory events could affect output, costs, permits, capex, or cash flow? | Absence of event data is not proof of compliant or safe operations. |
| FX risk | Foreign-currency revenue / cost / debt / cash; FX gain/loss; hedge notional; sensitivity | Usually missing except possible geography hints | FX note parser; currency split; foreign-currency debt; hedge disclosure | Valid only when currency exposure or FX gain/loss nodes exist. Commodity export possibility is not enough. | Mark `not_assessable` when currency-denominated exposure or FX gain/loss evidence is absent. | What foreign-currency exposures create earnings, cash-flow, or debt-service risk, and are they hedged? | Do not infer FX risk magnitude without currency-denominated evidence. |
| Hedging loss / mismatch risk | Hedge notional; commodity / FX item hedged; maturity; fair value; realized and unrealized gain/loss; physical exposure match | Usually missing | Derivative note parser; hedge accounting notes; maturity schedule | Valid only when hedge and physical exposure nodes both exist. Missing hedging disclosure means mismatch cannot be assessed. | Mark `not_assessable` when hedge notional, fair value, maturity, or underlying exposure is absent. | Do hedges match physical exposure in volume, timing, commodity, and currency, or could hedge losses / mismatch occur? | Do not describe price risk as hedged when hedging disclosure is missing. |
| Capex overrun | Project budget; actual spend; progress; schedule; funding; acceptance; revised budget; output bridge | Capex may exist as aggregate financial field | Project-level capex; budget-vs-actual; schedule; acceptance / commissioning; funding source | Valid only when project capex and progress nodes exist. Aggregate capex cannot show overrun or completion. | Mark `not_assessable` when project budget, progress, or acceptance evidence is absent. | Are mine, smelter, or processing projects running over budget or behind schedule, and how does that affect funding and output? | Do not treat aggregate capex as project success or capacity release. |
| Debt-cycle risk | Debt maturity; refinancing; interest rates; commodity downturn stress; liquidity; capex commitments; covenant risk | Operating cash flow and capex may exist; debt detail often missing | Debt maturity parser; interest expense; covenant / refinancing notes; liquidity detail | Valid only when debt and liquidity nodes exist. Commodity volatility alone cannot establish debt-cycle risk. | Mark `not_assessable` when debt maturity, liquidity, or interest expense evidence is absent. | Under commodity-cycle stress, do debt maturities, capex commitments, and liquidity create refinancing or covenant pressure? | Do not infer debt-cycle risk without debt schedule and liquidity evidence. |

## 6. Primary Sample Design: 000426

For `000426`, the P1.1 resource expansion should use the company as the primary sample for `resource_swing`.

The current evidence pack appears capable of checking:

- `stock.strategy_type=resource_swing`.
- `basic_info.industry`.
- `basic_info.main_business` indicating mining / non-ferrous resource exposure when present.
- `business_composition` indicating silver, tin, lead, zinc, copper, iron, or other product / segment exposure when present.
- `financial_metrics.revenue`, `gross_margin`, `operating_cashflow`, `accounts_receivable`, `inventory`, and `capex` when present.
- missing fields or must-track indicators for production volume, sales volume, reserves / resources, grade, capacity, hedging, cost curve, debt maturity, and environmental / safety events when present.
- source trace buckets for business composition and financial statements where available.

Expected sample behavior:

- Rows tied to `basic_info`, `business_composition`, revenue, gross margin, operating cash flow, receivables, inventory, or capex may be `partial` only when concrete `evidence_pack` field/value nodes are cited.
- Commodity price cycle, USD / RMB FX exposure, global demand / inventory cycle, policy / supply constraint, production volume, sales volume, grade, reserves, capacity, hedging, cost curve, realized price, sustaining capex, debt maturity, depreciation / depletion, and environmental / safety events should usually remain `missing` or `not_assessable`.
- Product exposure may identify what commodity rows should be asked about, but it must not become a conclusion about price benefit.
- Inventory may be included only as a working-capital observation and must not become direct demand judgment.
- Capex may be included only as investment / cash outflow observation and must not imply mine expansion, processing-capacity release, or production growth.
- Hedging status must remain unknown unless derivative / hedging evidence is present.

## 7. Differentiating `resource_core` and `resource_swing`

The same resource driver matrix can serve both strategy types, but row emphasis and interpretation guards should differ.

`resource_swing` emphasis:

- commodity price exposure;
- commodity cycle;
- realized price and volume bridge;
- margin sensitivity;
- inventory and working-capital swing;
- hedging / derivative mismatch;
- production disruption and capex overrun.

`resource_core` emphasis:

- cash-flow durability across cycles;
- cost curve position;
- reserve life and depletion;
- sustaining vs expansionary capex;
- debt / liquidity resilience;
- dividend capacity;
- environmental / safety / regulatory continuity.

Differentiation must not change `strategy_type`, `sub_type`, `status`, `confidence`, or `score`. It only changes P1.1 research-question priority and interpretation guard wording.

The builder should not write that a company is stable, defensive, low-cost, dividend-secure, or cycle-resilient merely because it is classified as `resource_core`. Those claims require evidence across cash flow, debt, cost position, sustaining capex, reserve life, and dividend policy.

`resource_core` implementation gate:

- `resource_core` is design-only in the first P1.1 Resource implementation.
- `resource_core` must not enter P1.1 implementation until at least one sample evidence pack stably provides all four required evidence groups:
  - historical operating cash flow;
  - capex split: sustaining vs expansionary;
  - debt / liquidity fields, such as interest expense, short-term debt, maturity, or liquidity;
  - dividend history or payout ratio.
- The four evidence groups are mandatory and cumulative. If any one is missing, `resource_core` remains design-only and out of first implementation scope.
- `601899` and `603993` remain later validation / boundary samples only; they do not expand first implementation scope.

## 8. Company Transmission Path Constraint

`company_transmission_path` remains an evidence-bound field, not a narrative field.

For the resource expansion:

- A valid path must cite concrete current `evidence_pack` field/value nodes.
- Valid nodes may include `evidence_pack.basic_info.main_business`, `evidence_pack.basic_info.industry`, `evidence_pack.business_composition[...]`, `evidence_pack.financial_metrics.revenue`, `evidence_pack.financial_metrics.gross_margin`, `evidence_pack.financial_metrics.operating_cashflow`, `evidence_pack.financial_metrics.accounts_receivable`, `evidence_pack.financial_metrics.inventory`, `evidence_pack.financial_metrics.capex`, and relevant `enhanced_must_track_indicators[...]` statuses.
- Commodity, macro, FX, policy, supply, demand, reserve, capacity, or hedging language is not a company transmission path by itself.
- If no concrete `evidence_pack` field or data point can be used as a company transmission node, the path must be exactly: `传导路径无法从当前证据包验证`.
- Any row using `传导路径无法从当前证据包验证` must set `confidence_cap=not_assessable`.
- A non-fallback path must not use `confidence_cap=not_assessable` unless another explicit validation failure makes the row not assessable.
- A non-fallback path should meet the concrete-field minimum standard: at least one product / segment business node and at least one concrete financial-metric value node.
- Product / segment business nodes include `business_composition[]` product / segment fields, or explicit product / metal names in `basic_info.main_business`.
- Concrete financial-metric value nodes include specific values from `financial_metrics`, such as revenue, gross margin, operating cash flow, accounts receivable, inventory, capex, or other available financial fields.
- If only the business node exists but no financial-metric value node exists, the path may be non-fallback for exposure only, but `confidence_cap` must be capped at `low`.
- If only financial-metric nodes exist but no product / business transmission starting point exists, the path must use `传导路径无法从当前证据包验证` and `confidence_cap=not_assessable`.
- If neither business node nor financial-metric value node exists, the path must use `传导路径无法从当前证据包验证` and `confidence_cap=not_assessable`.
- `company_transmission_path` must not use vague sentences such as "商品价格上涨，公司受益" or equivalent generic benefit language.

Valid path shape:

```text
evidence_pack.business_composition[0]=segment_name: silver / tin / lead-zinc product segment; revenue_ratio: ...
-> evidence_pack.financial_metrics.revenue=...
-> evidence_pack.financial_metrics.gross_margin=...
-> missing_evidence: realized price / sales volume / production volume / unit cost
```

Invalid path shape:

```text
Commodity prices improved, so company benefits.
Resource reserves are large, so production growth is supported.
Capex increased, so mine capacity has been released.
Inventory decreased, so demand is strong.
No hedging disclosure is found, so price risk is hedged.
The company is resource_core, so dividend stability is strong.
```

## 9. Not-Assessable / Missing Evidence Rules

Use `not_assessable` when evidence cannot complete the driver chain:

```text
driver signal
-> company evidence node
-> operating / financial bridge
-> missing evidence or research question
```

Resource-specific rules:

- If there is no specific `evidence_pack` field or data point for the company transmission node, set `company_transmission_path=传导路径无法从当前证据包验证` and `confidence_cap=not_assessable`.
- If only commodity price context exists, do not assess company revenue or margin sensitivity.
- For `Revenue sensitivity to commodity price`, segment revenue plus revenue YoY is not enough for commodity price transmission. If realized selling price and sales volume cannot both be cited, set `company_transmission_path=传导路径无法从当前证据包验证` and `confidence_cap=not_assessable`; do not attribute revenue growth to commodity price.
- If only product revenue exposure exists, assess exposure at most; realized price, sales volume, unit cost, and sensitivity remain missing.
- If reserves / resources are missing, do not assess mine life, depletion, or long-term production visibility.
- If reserves / resources are present but production is missing, do not treat reserves as production.
- If capex exists without project, acceptance, utilization, and output bridge, do not assess capacity release.
- If aggregate inventory exists without product split and sales / production reconciliation, do not assess demand.
- Even if inventory decreases and revenue increases at the same time, do not infer strong demand. Two financial observations do not equal operating demand evidence; demand assessment needs product-level inventory split, sales volume, production / sales reconciliation, or customer demand evidence.
- If grade data is missing, do not infer either high quality or poor quality. Absence of grade data is not proof of poor resource quality; use `missing` or `not_assessable`.
- If hedging disclosure is missing, hedging status and hedge mismatch risk are `not_assessable`; do not write price risk as hedged.
- If debt maturity, interest expense, or liquidity evidence is missing, debt-cycle and refinancing pressure are `not_assessable`.
- If cash flow, debt, cost curve, sustaining capex, reserve life, and dividend evidence are incomplete, `resource_core` dividend capacity and stability must be `not_assessable` or `partial`, never factual.
- `not_applicable` can be used only when evidence explicitly shows the driver is unrelated to the company's business.
- Examples of valid `not_applicable` evidence include `business_composition` or `basic_info.industry` explicitly showing that the company does not participate in the driver assumption's commodity, product, operation, or business model.
- Do not infer `not_applicable` from missing data. Missing data should map to `missing` or `not_assessable`, not `not_applicable`.

Recommended status mapping:

| Evidence state | data_availability_status | confidence_cap |
| --- | --- | --- |
| Concrete company field/value nodes and limited bridge exist | `partial` | `low` or `medium` depending on completeness |
| Concrete company field/value nodes exist but key operating bridge is absent | `partial` | `low` |
| No concrete company transmission node exists | `not_assessable` | `not_assessable` |
| Evidence explicitly shows the driver is irrelevant to disclosed business profile | `not_applicable` | `not_assessable` |
| Evidence is expected but absent from current pack | `missing` | `not_assessable` |

## 10. Future Data Needs

Future connector or parser phases may add evidence, but they are not part of this P1.1 design stage:

- Product-level commodity revenue, realized price, sales volume, and production volume.
- Mine-level reserves / resources, grade, recovery rate, depletion, and mine life.
- Mine, smelter, and processing capacity, utilization, and bottleneck data.
- Commodity price series mapped to company products and pricing lags.
- Inventory breakdown by raw material, work-in-process, concentrate, finished goods, and write-down.
- Hedging / derivative notional, maturity, fair value, realized gain / loss, and hedge accounting.
- USD / RMB FX exposure by revenue, cost, debt, cash, and derivatives.
- Unit cost, cash cost, all-in sustaining cost, by-product credits, and peer cost-curve data.
- Sustaining vs expansionary capex, project budget, progress, acceptance, and output bridge.
- Debt maturity, interest expense, refinancing terms, restricted cash, and covenant detail.
- Depreciation / depletion policy, impairment, and asset-life notes.
- Environmental, safety, regulatory, permit, mine accident, and compliance-cost events.
- Dividend policy, payout history, free cash flow after sustaining capex, and stress-period distribution record.

## 11. Implementation Gate Recommendation

Recommendation: proceed to P1.1 Resource implementation only after this design is externally reviewed and accepted.

First implementation scope is narrowed as follows:

- enable only `resource_swing`;
- use only `000426` as the primary sample;
- keep `resource_core` design-only and out of first implementation;
- keep `601899` and `603993` only as later validation / boundary samples;
- reuse the current P1.1 independent artifact pattern;
- do not add connectors or new data sources;
- do not alter classifier, scoring, readiness, deterministic pipeline, HTML, Dashboard, or output;
- include matrix rows only where the builder can enforce evidence-bound transmission and fallback behavior.

`resource_core` may enter a later implementation only after at least one sample evidence pack stably provides all of the following:

- historical operating cash flow;
- capex split: sustaining vs expansionary;
- debt / liquidity fields, such as interest expense, short-term debt, maturity, or liquidity;
- dividend history or payout ratio.

Until all four evidence groups are available, `resource_core` remains design-only.

Acceptance expectation:

- `000426` should produce many `missing` or `not_assessable` rows because current evidence lacks realized price, volume, reserve, grade, capacity, hedging, cost curve, capex split, debt maturity, and environmental / safety event detail.
- Rows using business composition and financial metrics may be `partial`, but must not become commodity-cycle conclusions.
- If only aggregate capex is available, with no project, acceptance, capacity, output, utilization, or revenue bridge, output must not contain inferences equivalent to "产能释放", "投产", "释放", "产量增长", or capacity/output realization. Capex may be described only as cash outflow / investment observation.
- The artifact must remain independent and must not affect deterministic status, confidence, score, strategy type, subtype, reports, or dashboards.

## 12. External Audit Recommendation

Recommendation: ask Claude to perform an external design audit before implementation.

Audit focus:

- whether the resource matrix is too broad for a first `resource_swing` P1.1 implementation;
- whether `company_transmission_path=传导路径无法从当前证据包验证` and `confidence_cap=not_assessable` are sufficiently hard-gated;
- whether any row still allows commodity-price, reserve, capex, inventory, hedging, or `resource_core` stability overreach;
- whether `000426` is appropriate as the only first implementation sample;
- whether future `resource_core` samples should wait until dividend, sustaining capex, debt, cost curve, and reserve-life evidence is available.
