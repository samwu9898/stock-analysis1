# Research Intelligence P1.1 Semiconductor Expansion Design Audit

Date: 2026-05-25

Revision: v1.0

Stage: Design audit only. This document adds design guidance only. It must not change code, tests, P1 schema, deterministic pipeline behavior, classifier rules, connectors, scoring, readiness, HTML renderer, Dashboard, generated output, regression fixtures, or existing artifact semantics.

Target expansion: `semiconductor_cycle` only.

Primary sample: `002371` NAURA / 北方华创, current `strategy_type=semiconductor_cycle`.

Future validation samples: `688012`, `688981`, `603501`, and `300604` may be retained for later validation if current repository data is sufficient. Boundary / negative samples such as `300308` and `300476` must not be forced into `semiconductor_cycle`.

## 1. Expansion Positioning

P1.1 has already accepted AI Datacenter, CXO, Satellite, Low Altitude, and Resource first implementation. This document designs the next narrow P1.1 expansion for `semiconductor_cycle`.

The expansion remains an independent Research Intelligence artifact:

```text
evidence_pack_<code>.json
+ optional P0 research intelligence artifacts
-> research_intelligence_p1_<code>.json
-> research_questions_p1_<code>.json
-> research_questions_p1_<code>.md
```

The expansion should convert semiconductor cycle, capex, demand, inventory, localization, export-control, company business, financial, and risk assumptions into evidence-gated driver-factor rows and research questions. It must not become a trading system, valuation model, semiconductor industry report, technology-roadmap report, connector project, dashboard panel, technical-analysis layer, or deterministic scoring input.

## 2. Non-Negotiable Boundaries

This design is limited to `strategy_type=semiconductor_cycle`.

Do not expand other `strategy_type` values in this stage.

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

- Semiconductor cycle context is background until bridged to company segment exposure, customer evidence, orders, revenue, margin, inventory, receivables, cash conversion, and capex utilization evidence.
- Do not write generic transmission such as "semiconductor cycle recovery, company benefits."
- Localization / domestic substitution narrative is not revenue realization unless company localization revenue, customer adoption, product acceptance, and collection evidence exist.
- R&D ratio is input evidence only; it is not proof of technology moat, yield, customer stickiness, or product competitiveness.
- Customer introduction, qualification, verification, or certification is not batch revenue unless order, shipment, acceptance, revenue recognition, and collection evidence exist.
- Contract liabilities are at most a partial proxy for prepayments or visibility; they are not true backlog.
- Capex is not capacity release, utilization, delivery, shipment, or revenue conversion.
- Inventory decline plus revenue growth is not direct proof of strong demand.
- Inventory increase is not direct proof of demand deterioration unless product-level inventory, orders, revenue, gross margin, and turnover evidence support the interpretation.
- Export controls, sanctions, overseas restrictions, and supply-chain constraints are risk / constraint drivers; they are not operating facts unless company-level evidence shows realized impact.

## 3. Current Evidence-Pack Capability

For `002371`, current fixtures indicate that the evidence pack can usually support only a conservative P1.1 semiconductor matrix.

Current `evidence_pack` may have:

- `stock.code`, `stock.name`, `stock.strategy_type`, `stock.sub_type`.
- `stock.status`, `stock.confidence`, `stock.fundamental_score` as read-only context only.
- `basic_info.industry`.
- `basic_info.main_business`.
- `business_composition[]` with segment name, classification type, period, revenue ratio, revenue, gross margin, and profit when present.
- `financial_metrics.period`, `revenue`, `revenue_yoy`, `gross_margin`, `net_margin`, `net_profit`, `deducted_net_profit`, `operating_cashflow`, `accounts_receivable`, `contract_liabilities`, `inventory`, `capex`, `r_and_d_expense`, and `r_and_d_expense_ratio` when present.
- `valuation_metrics` as explainability context only; no target price or trading framing.
- `confidence_basis.missing_fields`, `confidence_basis.data_coverage`, and `confidence_basis.confidence_breakdown`.
- `enhanced_must_track_indicators[]`.
- `risk_flags`, `unknown_or_missing_evidence`, `missing_fields`, `data_limitations`, `source_trace_summary`, and `forbidden_terms_check`.

Current `evidence_pack` usually does not reliably have:

- Semiconductor capex cycle series by equipment category, node, wafer type, or customer group.
- Downstream demand series by logic, memory, power, analog, automotive, AI, consumer, industrial, or foundry customers.
- Product-level inventory split by raw material, work-in-process, finished goods, consignment, slow-moving inventory, or inventory write-down.
- Customer qualification, customer adoption, production-line penetration, customer concentration, and top customer revenue share.
- Signed orders, true backlog, order cancellation, delivery schedule, acceptance schedule, or shipment volume.
- Localization revenue separated from general semiconductor revenue.
- Product generation, process-node coverage, yield, installed base, repeat order, or customer fab-line mapping.
- Export-control exposure by product, imported component, overseas customer, supplier, license, or replacement path.
- Equipment / materials / foundry / fabless / OSAT sub-chain classification with segment-specific operating metrics.
- Capex project mapping, acceptance, installed capacity, utilization, and capex-to-revenue bridge.
- R&D project conversion, product launch, mass-production validation, or revenue conversion.
- Receivable aging, payment terms, customer-specific collection, or cash conversion cycle.
- Impairment and inventory write-down detail.
- Longitudinal disclosure consistency.
- Independent multi-source consensus beyond source-bucket counting.

## 4. Driver Factor Matrix Contract

Every semiconductor driver row must use the existing P1.1 driver-factor contract:

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

## 5. Semiconductor Driver Factor Matrix

### 5.1 Macro / Industry / Cycle Drivers

| Driver factor | required_evidence | available_evidence from current evidence_pack | missing_evidence / future connector | company_transmission_path rule | not_assessable condition | research_question | interpretation_guard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Semiconductor capex cycle | Semiconductor wafer-fab capex by customer / node / category; equipment or material segment exposure; customer order / shipment / revenue bridge; margin and cash-flow bridge | `basic_info.main_business`; `business_composition[]` may show semiconductor equipment or related segment exposure; `financial_metrics.revenue`, `gross_margin`, `operating_cashflow`, `accounts_receivable`, `inventory`, `capex` may exist | Fab capex cycle data; customer capex by fab; product category order/shipment; installed base; delivery and acceptance schedule | Valid only when the path cites concrete company segment exposure plus financial fields. If only industry capex context exists, use `传导路径无法从当前证据包验证`. | Mark `not_assessable` when no company segment node exists, or when fab capex cannot be linked to company order, shipment, revenue, margin, or cash-flow evidence. | Which fab capex categories map to the company's products, customers, orders, revenue, receivables, and cash conversion? | Do not write "semiconductor capex cycle recovery, company benefits" without company evidence. |
| Downstream demand cycle | End-demand by application; foundry / IDM / packaging demand; company customer mix; product shipments; revenue and margin bridge | Company business and segment exposure may exist; financial revenue and margin may exist | Downstream demand series; customer production utilization; shipment volume; order pull-in/cut; end-market split | Valid only when company customer / product / revenue nodes are cited. External demand without company bridge uses fallback. | Mark `not_assessable` when demand is only industry-level or when customer / shipment / product bridge is absent. | Has downstream demand translated into company orders, shipments, revenue, receivables, and operating cash flow? | Downstream demand is not company demand unless company realization is evidenced. |
| Inventory cycle | Aggregate inventory; product-level inventory; inventory turnover; order/shipment; revenue; gross margin; write-down; customer inventory | `financial_metrics.inventory`, `revenue`, `gross_margin`, and `operating_cashflow` may be available | Product-level inventory split; inventory aging; turnover; order backlog; customer inventory; inventory write-down detail | A path may cite aggregate inventory and financial metrics as observations only. Demand interpretation requires product inventory, orders, revenue, margin, and turnover evidence. | Mark `not_assessable` for demand or cycle interpretation when only aggregate inventory exists. | Is inventory movement driven by demand, production ramp, long-cycle equipment delivery, safety stock, product mix, write-down, or customer timing? | Do not infer strong demand from inventory decline plus revenue growth. Do not infer demand deterioration from inventory increase without product-level and operating evidence. |
| Localization / domestic substitution | Localized product revenue; domestic customer adoption; qualification and batch order; product acceptance; revenue recognition; collection | `basic_info.main_business` and `business_composition[]` may mention semiconductor equipment / domestic substitution exposure; revenue may exist | Localization revenue split; domestic customer list; adoption rate; product line acceptance; repeat orders; collection evidence | Valid only when localization is tied to company segment revenue and customer/order/adoption evidence. If localization is narrative only, use fallback. | Mark `not_assessable` when only localization theme, policy language, or product description exists without revenue and customer adoption evidence. | What disclosed revenue, customers, orders, adoption, and collection evidence proves localization conversion? | Domestic substitution narrative is not revenue realization. |
| Export control / sanctions / overseas restriction | Official restriction; affected product / supplier / customer / geography; company exposure; substitution plan; order / cost / revenue impact | `risk_flags`, `missing_fields`, or business text may indicate semiconductor restriction risk; financial fields may exist but not isolate impact | Export-control event connector; supplier and customer exposure parser; license / restriction disclosure; imported component dependency | Policy or restriction can be risk context only unless company-specific affected product, supplier, customer, cost, order, or revenue nodes exist. Otherwise use fallback. | Mark `not_assessable` when restriction is external context without company-specific impact evidence. | Which products, suppliers, customers, or geographies are exposed to export controls, and what realized impact is visible in orders, costs, revenue, or cash flow? | Export control is not automatically positive localization demand or negative revenue impact without company bridge. |
| Equipment / materials / foundry / fabless / OSAT sub-chain difference | Explicit sub-chain classification; segment revenue; operating metrics for sub-chain; customer and product bridge; financial implications | `basic_info.industry`, `main_business`, and `business_composition[]` may identify equipment or related segments | Structured sub-chain tag; materials volume/price; foundry utilization; fabless tape-out/product cycle; OSAT utilization and customer mix | Valid only when company business and segment nodes identify a sub-chain. If sub-chain cannot be identified, use fallback for sub-chain-specific rows. | Mark `not_assessable` for sub-chain-specific cycle claims when the evidence pack does not distinguish equipment / materials / foundry / fabless / OSAT exposure. | Which sub-chain does the company actually belong to, and which cycle variables should be used for that sub-chain? | Do not apply equipment order logic to fabless, foundry utilization logic to materials, or OSAT utilization logic to equipment without evidence. |

### 5.2 Company / Business Drivers

| Driver factor | required_evidence | available_evidence from current evidence_pack | missing_evidence / future connector | company_transmission_path rule | not_assessable condition | research_question | interpretation_guard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Semiconductor-related revenue contribution | Segment revenue; revenue ratio; segment definition; period; gross margin; total revenue bridge | `business_composition[]` may provide semiconductor equipment / electronic process equipment segment, revenue ratio, revenue, gross margin, and period; total revenue may exist | More granular semiconductor-only revenue if segments are broad; product-level revenue; customer split | A concrete path may cite segment revenue / ratio and total revenue. It must describe exposure only, not demand, localization conversion, or cycle recovery. | Mark `not_assessable` when no semiconductor segment or business field exists. | What share of revenue is directly semiconductor-related, and what segment definition supports the exposure? | Segment exposure is not proof of cycle recovery or domestic substitution realization. |
| Product / equipment / material segment exposure | Product category; equipment type; material type; revenue ratio; margin; customer use case; period | `basic_info.main_business`; `business_composition[].segment_name`, `revenue_ratio`, `gross_margin` when present | Product-level revenue; etch / deposition / cleaning / materials / testing / packaging split; node and customer application | Valid only when product or segment field/value nodes exist. If product labels are broad, path must state the missing granularity. | Mark `not_assessable` for product-specific cycle transmission when product category or segment revenue is missing. | Which product or equipment/material segment drives revenue and margin, and what customer fab use case does it address? | Do not infer exposure to all semiconductor categories from one broad segment label. |
| Customer qualification / customer adoption | Customer qualification status; production-line adoption; verification stage; acceptance; batch order; repeat order; revenue and collection | Usually missing; business text may mention domestic substitution; contract liabilities may exist as partial proxy only | Customer qualification parser; customer adoption disclosure; acceptance and repeat-order tracker | Valid only when qualification/adoption field/value nodes exist plus order or revenue bridge. Main-business text cannot substitute. | Mark `not_assessable` when customer qualification, acceptance, adoption, or batch revenue evidence is absent. | Which customers have qualified and adopted the product, and has adoption converted into accepted orders, revenue, and collection? | Customer introduction, certification, or validation is not batch revenue. |
| Order visibility | Signed orders; true backlog; delivery schedule; cancellation; shipment; customer; revenue recognition | `financial_metrics.contract_liabilities` may be available as partial proxy; revenue and cash flow may exist | True backlog; new signed orders; delivery schedule; customer/order table; cancellation history | A path may cite contract liabilities only as partial proxy. A valid order path needs order/backlog disclosure plus company field/value nodes. | Mark `not_assessable` for order visibility when true backlog or signed orders are absent, even if contract liabilities exist. | What order, backlog, delivery, cancellation, and shipment evidence supports revenue visibility? | Contract liabilities are not backlog. |
| Backlog / contract liabilities as partial proxy only | Contract liabilities; prepayment terms; linked customer/order/project; revenue-recognition terms; comparison with revenue and cash flow | `financial_metrics.contract_liabilities`, revenue, and operating cash flow may be available | Contract-note parser; order disclosure; customer/project mapping; revenue-recognition schedule | A path may cite `financial_metrics.contract_liabilities`, but the guard must state partial proxy only and must not label it backlog. | Mark `not_assessable` for true backlog when contract liabilities are the only order-related evidence. | What customer, order, or project do contract liabilities correspond to, and what evidence prevents treating them as true backlog? | Contract liabilities are at most partial proxy; they are not backlog or confirmed delivery. |
| Localization revenue evidence | Domestic substitution product revenue; localized product list; domestic customer; acceptance; repeat order; gross margin; collection | Business text and segment exposure may mention localization; revenue may exist | Localization-specific revenue; domestic customer adoption; product acceptance; repeat orders; collection | Valid only when localization revenue or customer adoption nodes are present. Localization wording alone must use fallback. | Mark `not_assessable` when localization is narrative without revenue, customer adoption, or collection evidence. | Which disclosed revenue and customer evidence proves that localization has converted into company economics? | Do not treat domestic substitution narrative as realized revenue. |
| R&D intensity and product conversion | R&D expense; R&D ratio; product pipeline; project milestones; product launch; customer validation; revenue conversion | `financial_metrics.r_and_d_expense` and `r_and_d_expense_ratio` may be available; business text may identify products | R&D project list; milestone; product launch; yield / acceptance; customer validation; revenue conversion | A path may cite R&D expense or ratio as input evidence only. It cannot become technology moat unless product conversion and customer adoption nodes exist. | Mark `not_assessable` for moat, competitiveness, or product conversion when only R&D expense/ratio is available. | Which R&D projects have converted into products, customer adoption, orders, revenue, and margin? | R&D ratio is not proof of technology moat. |
| Capex-to-revenue bridge | Capex; project mapping; equipment / plant / capacity funded; acceptance; utilization; product output / delivery; revenue and cash flow | `financial_metrics.capex`, revenue, gross margin, and operating cash flow may be available | Capex project parser; construction progress; acceptance; utilization; production / delivery bridge; funding source | A path may cite capex as investment or cash outflow only. It must not claim capacity release or revenue conversion without project and utilization nodes. | Mark `not_assessable` for capacity release or revenue conversion when only aggregate capex exists. | Which projects does capex fund, and has the company disclosed acceptance, utilization, delivery, revenue, and cash-flow bridges? | Capex is not capacity release. |

### 5.3 Financial Drivers

| Driver factor | required_evidence | available_evidence from current evidence_pack | missing_evidence / future connector | company_transmission_path rule | not_assessable condition | research_question | interpretation_guard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Revenue growth quality | Revenue; revenue YoY; segment revenue; order/shipment; customer adoption; receivables; operating cash flow | `financial_metrics.revenue`, `revenue_yoy`, `business_composition[]`, receivables, and operating cash flow may exist | Order and shipment data; customer mix; product-level revenue; one-off order marker; collection cycle | A concrete path may cite revenue, segment exposure, receivables, and cash flow, but growth quality remains a question without order/shipment/customer evidence. | Mark `not_assessable` for demand quality when growth lacks order, shipment, customer, and cash conversion bridge. | Is revenue growth supported by recurring orders, shipments, customer adoption, and cash conversion, or only by reported revenue fields? | Revenue growth is not automatically demand strength or localization success. |
| Gross margin recovery or pressure | Gross margin by period; segment gross margin; product mix; pricing; cost; yield; inventory write-down; customer mix | `financial_metrics.gross_margin`; `business_composition.gross_margin` when present | Product margin; unit cost; price competition; yield; mix; warranty / service cost; write-down detail | A path may cite margin fields as financial observations. Recovery/pressure attribution requires product mix, pricing, cost, or write-down evidence. | Mark `not_assessable` when margin driver bridge is missing. | What product mix, pricing, cost, yield, and write-down evidence explains gross margin movement? | Do not infer pricing power or product competitiveness from gross margin alone. |
| Inventory level and inventory turnover | Inventory amount; turnover; product split; aging; order/shipment; revenue; margin; write-down | `financial_metrics.inventory`, revenue, gross margin, and operating cash flow may exist | Inventory turnover calculation; product-level inventory; aging; slow-moving inventory; order and shipment bridge; write-down note | A concrete path may cite aggregate inventory and revenue but must state missing product and turnover bridge. | Mark `not_assessable` for demand-cycle conclusion when turnover, product split, or order/shipment bridge is absent. | What inventory type is increasing or decreasing, and how does it relate to orders, shipment timing, margin, and write-down risk? | Aggregate inventory movement is not demand proof. |
| Receivables and cash conversion | Accounts receivable; revenue; operating cash flow; receivable aging; customer concentration; payment terms | `financial_metrics.accounts_receivable`, revenue, and operating cash flow may exist | Receivable aging; bad-debt provision; customer concentration; payment terms; DSO | A path may cite receivables, revenue, and cash flow. It cannot assert customer quality without aging and customer evidence. | Mark `not_assessable` for collection quality when aging, payment terms, and customer concentration are absent. | Are receivables and cash conversion consistent with recognized semiconductor revenue, or is collection lagging? | Recognized revenue is not collection certainty. |
| Operating cash flow | Operating cash flow; revenue; inventory; receivables; payables; contract liabilities; capex; customer payment terms | `financial_metrics.operating_cashflow`, revenue, receivables, inventory, contract liabilities, and capex may be available | Payables; cash conversion cycle; customer payment terms; order/shipment timing; product inventory | A path may cite available cash and working-capital fields, but durability and demand realization require operating bridge. | Mark `not_assessable` for cash-flow durability when working-capital detail and customer/order data are absent. | Does operating cash flow validate revenue quality after inventory, receivables, prepayments, and capex needs? | Cash flow is validation evidence, not proof of demand durability by itself. |
| Capex discipline | Capex amount; capex-to-revenue; project mapping; utilization; acceptance; return / revenue bridge; funding source | `financial_metrics.capex`, revenue, and operating cash flow may exist | Project-level capex; acceptance; utilization; production/delivery output; fixed-asset note | A path may cite capex as cash outflow/investment only. Discipline requires project and utilization bridge. | Mark `not_assessable` when project mapping, utilization, or revenue bridge is absent. | Is capex disciplined and tied to accepted projects, utilization, revenue, and operating cash flow? | Capex amount is not capacity release or revenue realization. |
| R&D expense and R&D ratio as input evidence only | R&D expense; R&D ratio; R&D project; product launch; customer validation; revenue conversion | `financial_metrics.r_and_d_expense`, `r_and_d_expense_ratio`, and revenue may exist | Product conversion; patents / process not enough alone; customer validation; orders; product revenue | A path may cite R&D fields only as input evidence. It must cap moat or product conversion claims unless conversion nodes exist. | Mark `not_assessable` for technology moat or commercialization when only R&D expense/ratio is available. | What R&D spending has converted into validated products, customer adoption, order revenue, and margin contribution? | R&D ratio is not technology moat proof. |
| Impairment / inventory write-down risk | Inventory write-down; impairment; slow-moving inventory; product obsolescence; margin pressure; inventory aging | Aggregate inventory and gross margin may exist | Inventory write-down notes; impairment notes; aging; product obsolescence; slow-moving inventory | Valid only when write-down / impairment field/value nodes exist. Aggregate inventory and margin cannot prove or disprove write-down risk. | Mark `not_assessable` when write-down, impairment, aging, or obsolescence evidence is absent. | Is there evidence of inventory write-down, impairment, slow-moving products, or obsolescence affecting margin and cash flow? | Do not infer absence of impairment risk from ordinary inventory data. |

### 5.4 Risk Drivers

| Driver factor | required_evidence | available_evidence from current evidence_pack | missing_evidence / future connector | company_transmission_path rule | not_assessable condition | research_question | interpretation_guard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Inventory overbuild | Product inventory; inventory turnover; order/shipment; backlog; revenue; gross margin; write-down; customer demand | Aggregate inventory, revenue, gross margin, and operating cash flow may exist | Product-level inventory; turnover; order/shipment; customer demand; write-down detail | Valid only for aggregate working-capital observation unless product and operating bridge exists. | Mark `not_assessable` for overbuild conclusion when only aggregate inventory is available. | Does product-level inventory exceed order/shipment needs, and is overbuild visible in turnover, margin, or write-down? | Inventory increase alone is not demand deterioration or overbuild proof. |
| Downstream capex slowdown | Customer fab capex slowdown; affected product categories; company customer/order exposure; shipment/revenue impact | Business exposure and financial metrics may exist | Customer capex by fab; order cancellation/pushout; customer exposure; shipment schedule | Valid only when slowdown is linked to company customer/order/revenue nodes. Otherwise use fallback. | Mark `not_assessable` when slowdown is external context without company exposure or impact evidence. | Which customer capex cuts or delays affect company orders, shipments, revenue, receivables, and cash flow? | Customer capex slowdown is not company revenue decline unless bridged. |
| Customer qualification failure | Qualification status; failed validation; delayed acceptance; customer loss; affected product; order/revenue impact | Usually missing; risk flags may mention customer adoption risk | Customer qualification tracker; announcement/IR parser; product acceptance evidence | Valid only when failure/delay field/value nodes exist. Missing qualification data does not prove failure or success. | Mark `not_assessable` when qualification outcome, delay, or failure evidence is absent. | Are any products failing or delaying customer qualification, and what orders or revenue are affected? | Do not infer successful adoption from product narrative or failed adoption from missing data. |
| Localization narrative without revenue | Localization claim; localized product revenue; domestic customer; accepted orders; repeat orders; cash collection | Business text may include domestic substitution wording; segment revenue may be broad | Localization revenue split; domestic customer/order mapping; accepted delivery; collection | Valid only when localization claim is connected to revenue and customer/order evidence. Narrative alone uses fallback. | Mark `not_assessable` when localization is theme language without revenue realization evidence. | Which localization claims are supported by disclosed revenue, customers, accepted orders, and collection? | Do not treat localization narrative as income realization. |
| R&D overread as moat | R&D expense/ratio; product conversion; customer validation; yield; repeat orders; gross margin | R&D expense and ratio may exist | Product conversion; technical validation; repeat order; installed base; yield / reliability evidence | A path may cite R&D fields as inputs only; moat conclusion needs product and customer evidence. | Mark `not_assessable` for moat when only R&D ratio or expense exists. | What evidence shows R&D has become product competitiveness and customer revenue rather than only expense intensity? | R&D ratio is not a moat. |
| Export control / supply-chain restriction | Restricted product / component / tool; supplier/customer exposure; license; mitigation; cost/order/revenue impact | Risk flags may exist; financial data may show results but not isolate restriction impact | Supply-chain exposure; import dependency; export license status; restriction event; mitigation cost | Valid only when company-specific restricted item, supplier/customer exposure, or realized impact nodes exist. | Mark `not_assessable` when restriction is only external context. | Which supply-chain or export restrictions affect products, components, customers, costs, or delivery schedules? | Do not convert restriction narrative into either benefit or damage without company evidence. |
| Margin pressure from product mix or price competition | Product mix; price changes; customer mix; competitors; segment margin; unit cost; gross margin trend | Gross margin and segment margin may exist | Product mix detail; price competition evidence; unit cost; customer mix; peer price data | A path may cite margin fields but cannot attribute pressure without mix/price/cost evidence. | Mark `not_assessable` when margin movement lacks product mix, price, cost, or customer evidence. | Is margin pressure from product mix, price competition, cost, or customer structure, and what evidence supports it? | Do not infer price competition or moat from gross margin alone. |
| Capex without utilization or revenue bridge | Capex; project mapping; acceptance; utilization; production/delivery output; revenue; cash-flow bridge | Capex, revenue, and operating cash flow may exist | Project capex; fixed-asset/project table; acceptance; utilization; output/delivery metrics | A path may cite capex as investment/cash outflow only. Capacity/utilization/revenue bridge requires project evidence. | Mark `not_assessable` for utilization or revenue conversion when only aggregate capex exists. | Which capex projects have been accepted and utilized, and how do they connect to delivery, revenue, and cash flow? | Capex is not utilization or revenue conversion. |

## 6. Sub-Chain Differentiation Requirement

The semiconductor matrix must distinguish equipment / materials / fabless / foundry / OSAT when evidence allows. This distinction is necessary because the relevant driver chain differs:

| Sub-chain | Primary cycle variables | Company evidence needed | Overread to avoid |
| --- | --- | --- | --- |
| Equipment | Fab capex, order intake, delivery/acceptance, customer qualification, installed base | Equipment segment revenue, order/backlog disclosure, customer qualification, delivery/acceptance, receivables, cash flow | Do not treat fab capex as company orders. |
| Materials | Wafer starts, consumable volume, price, customer qualification, recurring supply | Material product revenue, sales volume/price, customer adoption, inventory, margin, cash conversion | Do not apply equipment backlog logic to consumables. |
| Fabless | End-demand, product cycle, design wins, tape-out, inventory, channel/customer sell-through | Product revenue, customer/design-win evidence, inventory, gross margin, receivables, cash flow | Do not treat foundry capex as fabless revenue. |
| Foundry | Capacity, utilization, wafer starts, process-node mix, ASP, capex discipline | Utilization, capacity, wafer revenue, node mix, customer concentration, capex bridge | Do not treat capacity as utilization. |
| OSAT | Packaging/testing utilization, customer demand, advanced packaging mix, capex and yield | OSAT segment revenue, utilization, customer mix, capex acceptance, margin, receivables | Do not infer advanced-packaging conversion from capex alone. |

If the evidence pack cannot distinguish sub-chain exposure, sub-chain-specific driver rows must use `company_transmission_path=传导路径无法从当前证据包验证` and `confidence_cap=not_assessable`, unless a broader semiconductor exposure row can cite concrete business and financial nodes.

## 7. Primary Sample Design: 002371

For `002371`, the P1.1 semiconductor expansion should use the company as the primary sample for semiconductor equipment exposure.

The current evidence pack appears capable of checking:

- `stock.strategy_type=semiconductor_cycle`.
- `basic_info.industry`.
- `basic_info.main_business` indicating semiconductor equipment / domestic substitution exposure when present.
- `business_composition` indicating semiconductor equipment or electronic process equipment revenue exposure when present.
- `financial_metrics.revenue`, `revenue_yoy`, `gross_margin`, `operating_cashflow`, `accounts_receivable`, `contract_liabilities`, `inventory`, `capex`, `r_and_d_expense`, and `r_and_d_expense_ratio` when present.
- missing fields or must-track indicators for backlog, orders, customer qualification, inventory split, localization revenue, export-control exposure, capex utilization, and R&D conversion when present.
- source trace buckets for business composition and financial statements where available.

Expected sample behavior:

- Rows tied to `basic_info`, `business_composition`, revenue, gross margin, operating cash flow, receivables, contract liabilities, inventory, capex, or R&D fields may be `partial` only when concrete `evidence_pack` field/value nodes are cited.
- Semiconductor capex cycle, downstream demand cycle, customer qualification/adoption, true backlog, localization revenue, export-control impact, product-level inventory, capex utilization, and R&D product conversion should usually remain `missing` or `not_assessable`.
- Contract liabilities may be included only as partial proxy and must not upgrade backlog or order visibility.
- R&D expense and R&D ratio may be included only as input evidence and must not become a technology-moat conclusion.
- Capex may be included only as investment / cash outflow observation and must not imply capacity release, utilization, delivery, or revenue conversion.
- Inventory may be included only as working-capital observation and must not become direct demand judgment.

## 8. Future Validation / Boundary Samples

Use future samples only after first implementation design is accepted and current repository data availability is checked:

| Sample | Candidate role | Validation purpose |
| --- | --- | --- |
| `688012` | Equipment validation | Stress-test equipment order visibility, customer qualification, capex cycle transmission, R&D conversion, and localization evidence. |
| `688981` | Foundry validation | Stress-test foundry capacity, utilization, process-node mix, capex-to-revenue bridge, export-control risk, and customer concentration. |
| `603501` | Fabless validation | Stress-test fabless product cycle, downstream demand, channel/customer inventory, margin pressure, and R&D-to-product conversion. |
| `300604` | Materials / semiconductor supply-chain validation | Stress-test materials qualification, recurring supply, product-level revenue, inventory, gross margin, and customer adoption. |
| `300308` | Boundary / negative | AI Datacenter optical module exposure; must not be forced into `semiconductor_cycle` without classifier evidence. |
| `300476` | Boundary / negative | PCB / electronics manufacturing boundary; must not be forced into `semiconductor_cycle` without classifier evidence. |

## 9. Company Transmission Path Constraint

`company_transmission_path` remains an evidence-bound field, not a narrative field.

For the semiconductor expansion:

- A valid path must cite concrete current `evidence_pack` field/value nodes.
- Valid nodes may include `evidence_pack.basic_info.main_business`, `evidence_pack.basic_info.industry`, `evidence_pack.business_composition[...]`, `evidence_pack.financial_metrics.revenue`, `evidence_pack.financial_metrics.revenue_yoy`, `evidence_pack.financial_metrics.gross_margin`, `evidence_pack.financial_metrics.operating_cashflow`, `evidence_pack.financial_metrics.accounts_receivable`, `evidence_pack.financial_metrics.contract_liabilities`, `evidence_pack.financial_metrics.inventory`, `evidence_pack.financial_metrics.capex`, `evidence_pack.financial_metrics.r_and_d_expense`, `evidence_pack.financial_metrics.r_and_d_expense_ratio`, and relevant `enhanced_must_track_indicators[...]` statuses.
- Macro, industry, capex-cycle, downstream-demand, localization, export-control, customer-qualification, R&D, or semiconductor-theme language is not a company transmission path by itself.
- If there is no specific `evidence_pack` field or data point for the company transmission node, `company_transmission_path` must be exactly: `传导路径无法从当前证据包验证`.
- Any row using `传导路径无法从当前证据包验证` must set `confidence_cap=not_assessable`.
- A non-fallback path must not use `confidence_cap=not_assessable` unless another explicit validation failure makes the row not assessable.
- A non-fallback path should meet the concrete-field minimum standard: at least one semiconductor business / segment node and at least one concrete financial-metric value node.
- If only the business node exists but no financial-metric value node exists, the path may be non-fallback for exposure only, but `confidence_cap` must be capped at `low`.
- If only financial-metric nodes exist but no semiconductor business transmission starting point exists, the path must use `传导路径无法从当前证据包验证` and `confidence_cap=not_assessable`.
- `company_transmission_path` must not use vague sentences such as "半导体周期复苏，公司受益", "国产替代加速，公司受益", "客户导入顺利，收入有望释放", or equivalent generic benefit language.

Valid path shape:

```text
evidence_pack.business_composition[0]=segment_name: semiconductor equipment; revenue_ratio: ...
-> evidence_pack.financial_metrics.revenue=...
-> evidence_pack.financial_metrics.gross_margin=...
-> missing_evidence: true backlog / customer qualification / product-level inventory / localization revenue / capex utilization
```

Invalid path shape:

```text
Semiconductor cycle recovers, so the company benefits.
Domestic substitution accelerates, so revenue will grow.
Customer qualification means batch revenue.
Contract liabilities mean backlog.
Capex increased, so capacity has been released.
Inventory decreased and revenue increased, so demand is strong.
R&D ratio is high, so the technology moat is strong.
Export controls benefit domestic leaders.
```

## 10. Not-Assessable / Missing Evidence Rules

Use `not_assessable` when evidence cannot complete the driver chain:

```text
driver signal
-> concrete company evidence node
-> operating / financial bridge
-> missing evidence or research question
```

Semiconductor-specific rules:

- If there is no specific `evidence_pack` field or data point for the company transmission node, set `company_transmission_path=传导路径无法从当前证据包验证` and `confidence_cap=not_assessable`.
- If only semiconductor capex-cycle context exists, do not assess company order, revenue, or margin transmission.
- If downstream demand lacks customer, product, order, shipment, revenue, receivable, and cash-flow bridge, mark company demand realization `not_assessable`.
- If only aggregate inventory exists, do not assess inventory cycle as healthy or deteriorating.
- If inventory declines while revenue grows, do not infer strong demand without product-level inventory split, orders, shipments, customer demand, gross margin, and turnover evidence.
- If inventory rises, do not infer demand deterioration without product-level inventory, orders, revenue, gross margin, and turnover evidence.
- If localization evidence is only business description, policy, news, or theme language, mark localization revenue realization `not_assessable`.
- If customer qualification / certification / validation exists without batch order, shipment, acceptance, revenue recognition, and collection evidence, do not treat it as batch revenue.
- If true backlog and signed orders are absent, contract liabilities alone cannot prevent `not_assessable` for backlog or order visibility.
- If capex exists without project mapping, acceptance, utilization, delivery, revenue, and cash-flow bridge, capacity release and revenue conversion are `not_assessable`.
- If R&D expense or R&D ratio exists without product conversion and customer adoption evidence, technology moat and commercialization are `not_assessable`.
- If export-control or sanction context lacks company product, supplier, customer, cost, order, or revenue impact nodes, realized impact is `not_assessable`.
- If equipment / materials / foundry / fabless / OSAT exposure cannot be distinguished, sub-chain-specific claims are `not_assessable`.
- `not_applicable` can be used only when evidence explicitly shows the driver is unrelated to the company's business.
- Do not infer `not_applicable` from missing data. Missing data should map to `missing` or `not_assessable`, not `not_applicable`.

Recommended status mapping:

| Evidence state | data_availability_status | confidence_cap |
| --- | --- | --- |
| Concrete company field/value nodes and limited bridge exist | `partial` | `low` or `medium` depending on completeness |
| Concrete company field/value nodes exist but key operating bridge is absent | `partial` | `low` |
| No concrete company transmission node exists | `not_assessable` | `not_assessable` |
| Evidence explicitly shows the driver is irrelevant to disclosed business profile | `not_applicable` | `not_assessable` |
| Evidence is expected but absent from current pack | `missing` | `not_assessable` |

## 11. Future Data Needs

Future connector or parser phases may add evidence, but they are not part of this P1.1 design stage:

- Semiconductor capex-cycle series by equipment category, process node, customer type, wafer type, and fab project.
- Downstream demand data by logic, memory, power, analog, automotive, AI, consumer, industrial, foundry, and OSAT customers.
- Sub-chain classification and operating metrics for equipment, materials, foundry, fabless, and OSAT companies.
- Product-level semiconductor revenue, gross margin, shipment, order intake, acceptance, and delivery schedule.
- True backlog, new signed orders, order cancellation/pushout, and delivery acceptance.
- Contract-liability note parser linking prepayments to customer, order, or project where disclosed.
- Customer qualification, customer adoption, production-line penetration, repeat order, and customer concentration.
- Localization revenue split, localized product list, domestic customer adoption, and collection evidence.
- Product-level inventory split, inventory turnover, inventory aging, slow-moving inventory, and inventory write-down.
- Receivable aging, payment terms, bad-debt provision, customer receivable concentration, and cash conversion cycle.
- Export-control, sanctions, supplier restriction, imported component dependency, license status, and mitigation-cost data.
- R&D project list, milestone, product launch, customer validation, yield / reliability, and revenue conversion.
- Capex project mapping, construction progress, acceptance, utilization, delivery/output, fixed-asset transfer, and revenue/cash bridge.
- Impairment, inventory write-down, obsolete product, warranty, and after-sales cost disclosures.
- Longitudinal disclosure store for prior periods and prior P0/P1 outputs.

## 12. Implementation Gate Recommendation

Recommendation: enter P1.1 Semiconductor implementation only after this design is accepted and, preferably, externally audited.

Minimum implementation should:

- Add a `semiconductor_cycle` driver template inside the existing P1.1 builder boundary.
- Reuse the existing P1 schema without adding fields.
- Keep the current independent P1 artifact relationship.
- Read only current `evidence_pack` and optional P0 artifacts.
- Preserve existing `company_transmission_path` schema enforcement.
- Preserve source-bucket independent counting.
- Preserve the exact P1.1 safety boundary.
- Use `002371` as the only primary implementation sample.
- Keep `688012`, `688981`, `603501`, and `300604` only as later validation samples until data availability is checked.
- Keep `300308` and `300476` as boundary / negative samples and do not force them into `semiconductor_cycle`.

Do not implement in this phase:

- New data connectors.
- HTML / Dashboard sections.
- P1 schema changes.
- Deterministic status / confidence / score changes.
- Classifier changes.
- Readiness changes.
- Scoring changes.
- New strategy types.
- Live web search.
- Automated semiconductor forecasts.
- Automated policy, sanction, capex-cycle, or localization impact conclusions.
- Technical analysis or K-line logic.
- Trading advice or account actions.

Acceptance expectation:

- `002371` should produce many `missing` or `not_assessable` rows because current evidence lacks product-level inventory, true backlog, customer qualification/adoption, localization revenue, export-control impact, capex utilization, and R&D conversion detail.
- Rows using business composition and financial metrics may be `partial`, but must not become semiconductor-cycle recovery conclusions.
- Contract liabilities may be observed only as partial proxy and must not become backlog.
- Capex may be observed only as investment / cash outflow and must not become capacity release, utilization, delivery, or revenue conversion.
- R&D expense and R&D ratio may be observed only as input evidence and must not become technology moat.
- Inventory movement may be observed only as working-capital evidence and must not become direct demand conclusion.
- The artifact must remain independent and must not affect deterministic status, confidence, score, strategy type, subtype, reports, or dashboards.

## 13. External Audit Recommendation

Recommendation: ask Claude or another external reviewer to audit this design before implementation.

Audit focus:

- whether the semiconductor matrix is narrow enough for first P1.1 implementation;
- whether `company_transmission_path=传导路径无法从当前证据包验证` and `confidence_cap=not_assessable` are sufficiently hard-gated;
- whether any row still allows overreach from capex cycle, downstream demand, inventory, localization, customer qualification, contract liabilities, capex, R&D ratio, or export-control narratives;
- whether `002371` is appropriate as the only first implementation sample;
- whether future samples should be split by equipment / materials / fabless / foundry / OSAT before broad validation.

## 14. Design Acceptance Criteria

This semiconductor expansion design is acceptable when:

- The expansion is limited to `semiconductor_cycle`.
- Every driver has required evidence, available evidence, missing evidence, company transmission rule, not-assessable condition, research question, and interpretation guard.
- Current `evidence_pack` fields are separated from future connector needs.
- `002371` is the primary sample.
- Future validation and boundary samples are listed only for later validation and do not expand P1.1 implementation scope.
- Semiconductor capex cycle is never treated as company orders, revenue, or margin without company evidence.
- Downstream demand is never treated as company demand without company customer/order/shipment/revenue/cash evidence.
- Localization narrative is never treated as revenue realization.
- R&D ratio is never treated as technology moat proof.
- Customer introduction / qualification / certification is never treated as batch revenue.
- Contract liabilities are never treated as backlog.
- Capex is never treated as capacity release, utilization, delivery, or revenue conversion.
- Inventory decline plus revenue growth is never treated as direct proof of strong demand.
- Inventory increase is never treated as direct proof of demand deterioration without product-level inventory, order, revenue, margin, and turnover evidence.
- Export controls and sanctions are treated as risk / constraint context until company impact is evidenced.
- Equipment / materials / fabless / foundry / OSAT sub-chain differences are preserved when evidence permits and capped as `not_assessable` when evidence does not permit.
- `company_transmission_path` remains evidence-bound and falls back to `not_assessable` when no company node exists.
- No P1 schema, deterministic pipeline, classifier, connector, scoring, readiness, HTML, or Dashboard change is proposed for this stage.
- No trading advice, target price, position sizing, timing, technical analysis, K-line analysis, or account action is included.
