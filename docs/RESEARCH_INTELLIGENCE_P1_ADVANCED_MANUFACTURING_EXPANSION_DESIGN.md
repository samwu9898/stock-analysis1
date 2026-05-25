# Research Intelligence P1.1 Advanced Manufacturing Expansion Design Audit

Date: 2026-05-25

Revision: v1.1

Stage: Design audit only. This document adds design guidance only. It must not change code, tests, P1 schema, deterministic pipeline behavior, classifier rules, connectors, scoring, readiness, HTML renderer, Dashboard, generated output, regression fixtures, or existing artifact semantics.

Target expansion: `advanced_manufacturing_growth` only.

Primary sample: `002050` Sanhua Intelligent Controls / 三花智控, current `strategy_type=advanced_manufacturing_growth`.

Future validation / boundary samples: `601689` Tuopu Group / 拓普集团 should be retained as the first future validation and boundary sample. Other later candidates may include advanced manufacturing companies with automotive thermal-management, actuator, robotics component, industrial automation, or precision manufacturing exposure, but P1.1 first implementation should use only `002050` as the primary sample.

## 1. Expansion Positioning

P1.1 has already frozen the accepted baseline for AI Datacenter, CXO, Satellite, Low Altitude, Resource Swing, and Semiconductor. This document designs the next narrow P1.1 expansion for `advanced_manufacturing_growth`.

The expansion remains an independent Research Intelligence artifact:

```text
evidence_pack_<code>.json
+ optional P0 research intelligence artifacts
-> research_intelligence_p1_<code>.json
-> research_questions_p1_<code>.json
-> research_questions_p1_<code>.md
```

The expansion should convert high-end manufacturing demand, automotive / EV thermal management, robotics and humanoid robotics exposure, customer adoption, product mix, financial quality, and risk assumptions into evidence-gated driver-factor rows and research questions. It must not become a trading system, valuation model, industry report, robotics theme report, connector project, dashboard panel, technical-analysis layer, or deterministic scoring input.

## 2. Non-Negotiable Boundaries

This design is limited to `strategy_type=advanced_manufacturing_growth`.

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

- High-end manufacturing demand is background until bridged to company segment revenue, orders, customers, product mix, margin, receivables, inventory, cash flow, and capex utilization evidence.
- Automotive / EV / thermal-management demand is not company revenue unless the evidence pack contains company segment exposure plus customer / order / delivery / revenue / collection evidence.
- Robotics or humanoid robotics theme exposure is not revenue realization.
- Customer capex is not company revenue.
- Customer qualification, nomination, certification, or design-win is not batch revenue unless order, shipment, acceptance, revenue recognition, and collection evidence exist.
- Contract liabilities are at most a partial proxy for prepayments or visibility; they are not true backlog.
- Capex is not capacity release, utilization, mass production, delivery, or revenue conversion.
- R&D expense and R&D ratio are input evidence only; they are not proof of technology moat, product competitiveness, yield, reliability, or customer stickiness.
- Receivable growth is not high-quality revenue by itself.
- Inventory growth or decline is not direct proof of demand strength or weakness.
- Gross margin movement cannot be attributed to product mix, price competition, or technology advantage without product, price, cost, customer, and volume evidence.
- Valuation metrics are evidence sufficiency context only. They must not become target price, upside / downside, trade timing, or position language.

## 3. Current Evidence-Pack Capability

For `002050`, current fixtures indicate that the evidence pack can usually support a conservative P1.1 advanced-manufacturing matrix.

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
- `latest_news` or `news` only as weak risk context or follow-up clue; mock / unverified news must be labeled "unverified context, not operating fact" and must not support revenue, order, customer, mass-production, collection, or valuation explainability conclusions.

For `002050`, current fixture-like data may show:

- Refrigeration and air-conditioning control component exposure as the traditional core business.
- Automotive thermal-management component exposure as a major business line.
- Robotics actuator-related component layout, but with no reliable revenue ratio, order amount, customer, or mass-production proof in the current pack.
- Revenue YoY, gross margin, operating cash flow, accounts receivable, inventory, and valuation fields as aggregate financial observations.
- Big-customer or named-customer references only as mock / unverified context unless source-traced company disclosures provide revenue share, orders, nomination, or collection data.

Current `evidence_pack` usually does not reliably have:

- High-end manufacturing demand cycle series by sub-industry.
- Automotive / EV / thermal-management market demand linked to company customers.
- Customer capex, product adoption, design-win, nomination, qualification, shipment, acceptance, or mass-production schedules.
- Robotics or humanoid robotics revenue split, order book, customer names, mass-production deliveries, accepted shipment volume, or collection evidence.
- Product-line revenue, product-line gross margin, price, volume, unit cost, or product mix upgrade detail beyond broad business composition.
- Top customer revenue share, customer concentration, customer payment terms, or customer-specific receivable balance.
- Overseas customer / export exposure split, FX sensitivity, trade restriction mapping, or overseas collection cycle.
- Contract liabilities mapped to specific customers, orders, product lines, or revenue-recognition schedules.
- Capex project mapping, acceptance, capacity, utilization, production-sales bridge, or capex-to-revenue conversion evidence.
- Inventory split by raw materials, work-in-process, finished goods, robotics products, automotive products, or refrigeration products.
- Receivable aging, overdue receivables, bad-debt provision detail, DSO, or collection quality by customer.
- Free cash flow, working-capital bridge, or longitudinal disclosure consistency unless separately computed by existing fields.
- Independent multi-source consensus beyond source-bucket counting.

## 4. Driver Factor Matrix Contract

Every advanced-manufacturing driver row must use the existing P1.1 driver-factor contract:

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

Generated `output/research_intelligence_p1_*` and `output/research_questions_p1_*` artifacts are runtime products and should not be committed.

Driver de-duplication rules:

- Robotics narrative drivers must be merged or clearly divided so the output does not repeat multiple equivalent questions asking whether robotics has orders, customers, mass production, and collection evidence.
- Qualification / nomination / design-win questions must focus on customer entry status and conversion prerequisites; mass-production / delivery questions must focus on SOP, accepted shipment, revenue recognition, and collection.
- Accounts receivable / collection quality and receivables deterioration must be merged or explicitly separated between neutral collection-quality checking and negative deterioration-risk checking.
- If multiple rows are retained for the same evidence gap, generated research questions must avoid obvious repetition and must name the distinct missing bridge each row is checking.

## 5. Advanced Manufacturing Driver Factor Matrix

### 5.1 Macro / Industry / Demand Drivers

| Driver factor | required_evidence | available_evidence from current evidence_pack | missing_evidence / future data need | company_transmission_path rule | not_assessable condition | research_question | interpretation_guard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| High-end manufacturing demand cycle | Demand cycle by end market; company product exposure; customer orders / shipments; revenue, margin, receivable, inventory, and cash-flow bridge | `basic_info.industry`, `basic_info.main_business`, broad `business_composition[]`, `financial_metrics.revenue`, `gross_margin`, `operating_cashflow`, `accounts_receivable`, and `inventory` may exist | Industry demand series; customer adoption; product-level orders and shipments; customer mix; product-line price / volume | Valid only when the path cites concrete company segment and financial nodes. If the pack has only industry or theme context, use `传导路径无法从当前证据包验证`. | Mark `not_assessable` when high-end manufacturing demand lacks company product, customer, order, revenue, margin, and cash conversion bridge. | Has high-end manufacturing demand translated into disclosed company product-line revenue, orders, shipments, receivables, inventory turnover, and operating cash flow? | Do not write "high-end manufacturing is strong, company growth is certain" without company evidence. |
| Automotive / EV / thermal-management demand | EV / auto production and thermal-management demand; company thermal-management segment; customer order / nomination / mass-production evidence; revenue and margin bridge | `business_composition[]` may show automotive thermal-management component revenue ratio; `financial_metrics` may show aggregate revenue, margin, cash flow, receivables, and inventory | Auto / EV demand by customer; thermal-management product revenue and gross margin; named customer orders; delivery and mass-production schedule; collection data | A concrete path may cite automotive thermal-management segment exposure and financial fields only as exposure. Demand transmission needs customer, order, delivery, revenue, margin, and collection evidence. | Mark `not_assessable` for auto / EV demand realization when customer order, mass-production, shipment, or collection evidence is absent. | Which automotive / EV thermal-management customers, products, orders, deliveries, revenue, margin, and collections support realized demand? | Do not treat automotive or EV demand as company revenue without a company bridge. |
| Robotics / humanoid robotics theme exposure | Robotics product description; revenue split; signed orders; customer qualification / nomination / design-win; mass-production delivery; accepted shipment and collection | `basic_info.main_business` or `business_composition[].segment_name` may mention robotics actuator-related components or layout as narrative context only | Robotics revenue ratio; order amount; customer list; nomination / qualification stage; mass-production proof; delivery and collection evidence | A non-fallback robotics path requires explicit non-zero robotics `business_composition[].revenue_ratio` or `revenue`, or direct robotics order / customer / mass-production / collection field nodes. If only layout / theme / strategic wording / news exists, use `传导路径无法从当前证据包验证`. | Mark `not_assessable` when robotics is only narrative, layout, mock / unverified news, or theme exposure without independent revenue, order, customer, mass-production, and collection evidence. | Is robotics exposure supported by disclosed non-zero revenue, orders, customers, mass-production deliveries, and cash collection, or only by narrative? | Do not treat robotics or humanoid robotics theme as revenue realization. |
| Customer capex / product adoption cycle | Customer capex or adoption plan; company product mapping; customer qualification; orders; shipment / acceptance; revenue and cash bridge | Current pack may show company business segments and aggregate financials, but usually lacks customer capex or adoption stage | Customer capex by named customer; product adoption schedule; qualification / nomination / design-win; accepted orders; revenue recognition | Customer capex can be context only unless linked to company product, customer order, shipment, revenue, receivable, and cash-flow nodes. Otherwise use fallback. | Mark `not_assessable` when customer capex or adoption is external context without company order / shipment / revenue evidence. | Which customer capex or adoption programs have converted into company orders, shipments, revenue, receivables, and cash flow? | Customer capex is not company revenue. |
| Localization / import substitution | Localized product revenue; domestic customer adoption; customer qualification; batch order; accepted delivery; revenue and collection | Business text may mention domestic advanced manufacturing or component exposure; financial and segment data may exist | Localization-specific revenue; domestic customer list; qualification result; accepted order; repeat delivery; collection evidence | Valid only when localization is tied to company product revenue and customer adoption / order nodes. If localization is narrative only, use fallback. | Mark `not_assessable` when only localization / import-substitution theme exists without revenue and customer adoption evidence. | What revenue, customers, accepted orders, repeat deliveries, and collections prove localization conversion? | Localization narrative is not realized revenue. |
| Overseas customer / export exposure | Overseas revenue share; customer geography; export product mix; FX exposure; trade restriction impact; receivable and cash bridge | `business_composition[]` may include geographic segments if present; `valuation_metrics` and financials are context only | Overseas / export revenue split; top customer geography; FX gains / losses; trade restriction events; overseas receivable aging | Valid only if concrete overseas / geography / FX / customer nodes exist. Broad export possibility or customer rumor must use fallback. | Mark `not_assessable` when overseas customer, export revenue, FX, or trade-risk exposure cannot be sourced from evidence-pack fields. | How much revenue and working capital is exposed to overseas customers, export markets, FX, and trade restrictions? | Overseas customer narrative is not exposure magnitude or realized risk without company-level evidence. |

### 5.2 Company / Business Drivers

| Driver factor | required_evidence | available_evidence from current evidence_pack | missing_evidence / future data need | company_transmission_path rule | not_assessable condition | research_question | interpretation_guard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Core business revenue contribution | Traditional core segment revenue; revenue ratio; period; gross margin; total revenue bridge | For `002050`, `business_composition[]` may show refrigeration / air-conditioning component exposure and revenue ratio; financial revenue may exist | Product-level core revenue, gross margin, volume, price, and customer split | A concrete path may cite `business_composition` and financial fields as exposure only. It must not infer demand strength or customer quality. | Mark `not_assessable` when no core business segment field exists. | What share of revenue and gross margin comes from refrigeration / air-conditioning control components, and how stable is the core business evidence? | Core-business exposure is not proof of cycle strength or pricing power. |
| Automotive thermal-management business contribution | Automotive thermal-management segment revenue; revenue ratio; product definition; gross margin; customer / program bridge | For `002050`, `business_composition[]` may show automotive thermal-management component exposure and revenue ratio | Product-line revenue and gross margin; customer programs; mass-production schedule; order visibility; collection | A path may cite automotive thermal-management segment exposure and aggregate financials. It must state missing customer / order / delivery bridge when absent. | Mark `not_assessable` for realized thermal-management order quality when customer, program, delivery, and collection evidence is missing. | What revenue, margin, customer, program, delivery, and collection evidence supports automotive thermal-management growth? | Automotive thermal-management exposure is not order visibility by itself. |
| New business / robotics / emerging business revenue split | Robotics / emerging product revenue; revenue ratio; gross margin; period; total revenue bridge | Current pack may mention robotics actuator-related component layout but may not provide revenue ratio or order amount | Robotics revenue split; product list; gross margin; order amount; customer and production status | Valid only if explicit non-zero robotics / emerging business revenue, revenue ratio, or order field/value nodes exist. Layout, strategic wording, or news alone must use fallback. | Mark `not_assessable` when robotics or emerging business lacks disclosed revenue split and orders. | What disclosed non-zero revenue and gross margin, if any, comes from robotics or emerging businesses? | Do not treat new-business narrative as revenue realization. |
| Product line revenue and gross margin | Product-line revenue; revenue ratio; gross margin; period; product definition; price / volume / cost bridge | `business_composition[]` may include broad segment names and revenue ratios; segment gross margin may or may not exist | Product-level revenue; product-level gross margin; price / volume / cost; product mix history | Valid only when product-line or segment field/value nodes exist. Broad labels must be described as broad labels, not product-level proof. | Mark `not_assessable` for product mix or pricing conclusion when product-line margin, price, volume, or cost is missing. | Which product lines drive revenue and gross margin, and what product mix detail explains changes? | Do not infer product upgrade or pricing power from broad segment revenue alone. |
| Customer order visibility | Signed orders; true backlog; customer; product; delivery schedule; cancellation / pushout; shipment and revenue recognition | `financial_metrics.contract_liabilities` may exist as partial proxy only; financial revenue and cash flow may exist | Signed order table; backlog; delivery schedule; customer program order; cancellation history | A path may cite contract liabilities only as partial proxy. A valid order path needs signed order / backlog / delivery field nodes. | Mark `not_assessable` for order visibility when true backlog or signed orders are absent, even if contract liabilities exist. | What orders, backlog, delivery schedule, cancellation, shipment, and revenue-recognition evidence supports visibility? | Contract liabilities are not backlog. |
| Mass production / delivery evidence | Mass-production start; accepted shipment; delivery volume; customer acceptance; revenue recognition; collection | Current pack may contain financial revenue, but usually lacks mass-production and delivery evidence | Mass-production announcement; delivery volume; acceptance certificate; product shipment; revenue and cash collection | Valid only when mass-production / delivery field/value nodes exist. Revenue or news cannot substitute for production evidence. | Mark `not_assessable` when mass-production, delivery, acceptance, or shipment evidence is absent. | Which products have entered mass production or accepted delivery, and how does that connect to revenue and collections? | Do not treat customer qualification, nomination, design-win, or layout as batch revenue. |
| Customer concentration / top customer exposure | Top customer revenue share; customer count; customer identity / category; receivable concentration; payment terms | `risk_flags` or missing fields may mark concentration gaps; financial receivables may exist | Top-five customer revenue share; major customer change; customer receivable concentration; payment terms | Valid only when customer concentration field/value nodes exist. News or market rumors about named customers cannot substitute. | Mark `not_assessable` when top customer share, major customer change, or receivable concentration is absent. | Does top-customer concentration create order, pricing, receivable, or one-off revenue risk? | Do not infer customer stickiness or diversification from segment labels. |
| Customer qualification / nomination / design-win status | Customer qualification stage; nomination / design-win disclosure; product program; order conversion; shipment; revenue and collection | Current pack may contain business description; news is unverified context only, not a valid node | Customer qualification tracker; nomination / design-win detail; SOP / mass-production schedule; order and revenue conversion | A valid path needs qualification / nomination / design-win nodes plus order or revenue bridge. If only qualification exists, cap revenue claims. | Mark `not_assessable` for revenue conversion when qualification / design-win lacks order, shipment, revenue, and collection evidence. | Which customer qualifications, nominations, or design-wins exist, and have they converted into orders, shipments, revenue, and collection? | Qualification / nomination / design-win is not batch revenue. |
| Contract liabilities as partial proxy only | Contract liabilities; prepayment terms; linked customer / order / project; revenue-recognition schedule; comparison with revenue and cash flow | `financial_metrics.contract_liabilities`, revenue, and operating cash flow may be available | Contract note; customer / order mapping; revenue-recognition timing; prepayment terms | A path may cite contract liabilities only as partial proxy and must not label them backlog. | Mark `not_assessable` for true backlog when contract liabilities are the only order-related evidence. | What customer or order do contract liabilities correspond to, and why should they not be treated as true backlog? | Contract liabilities are at most partial proxy; they are not backlog or confirmed delivery. |
| Product mix upgrade | Product mix by old / new products; revenue and gross margin by mix; ASP / cost; customer adoption; volume and delivery | Segment revenue and gross margin may exist if disclosed; aggregate gross margin may exist | Product mix detail; ASP; unit cost; new product revenue; customer adoption and delivery | A concrete path may cite segment and margin fields as observations only. Product-mix upgrade requires product-level mix and margin evidence. | Mark `not_assessable` when product mix, price, cost, and customer adoption evidence is missing. | Is product mix upgrading, and what product-level revenue, margin, price, cost, and customer adoption evidence supports it? | Do not infer product upgrade from gross margin or broad segment mix alone. |

### 5.3 Financial Drivers

| Driver factor | required_evidence | available_evidence from current evidence_pack | missing_evidence / future data need | company_transmission_path rule | not_assessable condition | research_question | interpretation_guard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Revenue growth quality | Revenue; revenue YoY; segment revenue; recurring order / shipment; customer concentration; receivables; operating cash flow | `financial_metrics.revenue`, `revenue_yoy`, `accounts_receivable`, `operating_cashflow`; `business_composition[]` may exist | Order / shipment data; customer mix; product-line revenue; one-off order marker; collection cycle | A path may cite revenue, segment, receivable, and cash-flow fields, but growth quality remains a question without independent order / shipment / collection evidence. | Mark `not_assessable` for demand realization or growth quality conclusion when order, shipment, customer, and cash conversion bridge is absent. | Is revenue growth supported by recurring orders, shipments, customer adoption, and cash conversion, or only by reported revenue fields? | Revenue growth is not automatically high-quality growth. |
| Gross margin stability | Gross margin by period; segment gross margin; product mix; price; cost; customer mix; competition evidence | `financial_metrics.gross_margin`; `business_composition.gross_margin` when present | Product margin history; price / volume / cost; customer mix; competition and price-cut evidence | A path may cite margin fields as financial observations. Attribution requires product mix, price, cost, or customer evidence. | Mark `not_assessable` for margin cause when product mix, price, cost, or customer bridge is missing. | What product mix, pricing, cost, and customer evidence explains gross margin stability or pressure? | Do not infer pricing power, product competitiveness, or demand strength from gross margin alone. |
| Operating cash flow | Operating cash flow; revenue; receivables; inventory; payables; contract liabilities; capex; customer payment terms | `financial_metrics.operating_cashflow`, revenue, receivables, inventory, contract liabilities, and capex may be available | Payables; cash conversion cycle; receivable aging; customer payment terms; order / shipment timing | A path may cite available cash-flow and working-capital fields, but durability requires working-capital and customer / order bridge. | Mark `not_assessable` for cash-flow durability when working-capital detail and customer / order evidence are absent. | Does operating cash flow validate revenue quality after receivables, inventory, prepayments, capex, and customer payment terms? | Cash flow is validation evidence, not proof of demand durability by itself. |
| Accounts receivable / collection quality | Accounts receivable; revenue; operating cash flow; receivable aging; bad-debt provision; customer concentration; payment terms | `financial_metrics.accounts_receivable`, revenue, and operating cash flow may exist | Aging; overdue receivables; DSO; bad-debt provisions; customer receivable concentration | A path may cite receivables, revenue, and cash flow. It cannot assert collection quality without aging, terms, and customer evidence. | Mark `not_assessable` for collection quality when aging, payment terms, or customer concentration is absent. | Are receivables consistent with recognized revenue, or do aging, concentration, and payment terms indicate collection pressure? | Do not interpret receivable growth as high-quality revenue. |
| Inventory and production-sales bridge | Inventory amount; product split; raw material / WIP / finished goods; turnover; production; shipment; orders; write-down | `financial_metrics.inventory`, revenue, gross margin, and operating cash flow may exist | Inventory type split; turnover; production volume; sales volume; order / shipment bridge; write-down notes | A path may cite aggregate inventory only as a working-capital observation. Demand interpretation requires product inventory, orders, production, sales, and turnover evidence. | Mark `not_assessable` for demand or production-sales conclusion when only aggregate inventory exists. | What inventory type is building or falling, and how does it reconcile with production, shipments, orders, margin, and write-down risk? | Do not infer demand strength or weakness from inventory movement alone. |
| Capex-to-revenue / capacity utilization bridge | Capex; project mapping; capacity funded; acceptance; utilization; output / delivery; revenue and cash-flow bridge | `financial_metrics.capex`, revenue, gross margin, and operating cash flow may be available | Capex project table; fixed-asset / construction progress; capacity; utilization; output / delivery evidence | A path may cite capex as investment or cash outflow only. It must not claim capacity release, utilization, or revenue conversion. | Mark `not_assessable` when project mapping, utilization, output, or revenue bridge is absent. | Which projects does capex fund, and has the company disclosed acceptance, utilization, output, delivery, revenue, and cash-flow bridges? | Capex is not capacity release, mass production, utilization, or revenue conversion. |
| R&D expense as input evidence only | R&D expense; R&D ratio; project list; product launch; customer validation; orders; revenue conversion | `financial_metrics.r_and_d_expense` and `r_and_d_expense_ratio` may exist | R&D project milestones; product launch; validation; yield / reliability; customer adoption; order revenue | A path may cite R&D fields only as input evidence. It cannot become technology moat or product conversion unless conversion nodes exist. | Mark `not_assessable` for moat, competitiveness, or commercialization when only R&D expense / ratio is available. | What R&D spending has converted into validated products, customer adoption, orders, revenue, and margin contribution? | R&D ratio is not proof of technology moat. |
| Free cash flow / working-capital pressure | Operating cash flow; capex; receivables; inventory; payables; contract liabilities; financing cash flow; working-capital notes | Operating cash flow, capex, receivables, inventory, and contract liabilities may exist when provided | Payables; free-cash-flow calculation; cash conversion cycle; debt maturity; customer / supplier terms | A path may cite available cash-flow, capex, receivable, and inventory nodes. It must not conclude pressure or resilience without full working-capital bridge. | Mark `not_assessable` when payables, working-capital detail, debt maturity, or customer / supplier terms are missing. | Is free cash flow pressured by capex, receivables, inventory, and customer / supplier terms? | Aggregate cash flow alone is not cash-conversion quality proof. |
| Valuation explainability as evidence sufficiency only | Valuation metrics; earnings growth; margin; cash flow; new-business evidence; segment quality; risk flags | `valuation_metrics.pe_ttm`, `pb`, `market_cap` may exist; profit, margin, and cash-flow fields may exist | Forward earnings bridge; product-line profit; robotics revenue / orders; cash conversion durability; peer context if ever added | A path may cite valuation metrics only to frame evidence sufficiency questions. It must not output target price or trading implications. | Mark `not_assessable` for valuation justification when profit growth, margin, cash flow, and new-business evidence are incomplete. | 当前 evidence pack 中哪些证据足以支撑或解释当前估值背景，哪些证据仍缺失？ | Valuation is evidence sufficiency context only, not target price, upside / downside, trade advice, or a judgment that valuation is reasonable / high / low. |

### 5.4 Risk Drivers

| Driver factor | required_evidence | available_evidence from current evidence_pack | missing_evidence / future data need | company_transmission_path rule | not_assessable condition | research_question | interpretation_guard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| New business narrative without revenue | New-business description; revenue split; order / customer evidence; product launch; mass-production delivery; collection | `basic_info.main_business` or `business_composition[].segment_name` may mention robotics / emerging business layout as narrative context only | New-business revenue; orders; customer qualification; shipment; accepted delivery; collection | Valid only when new-business revenue, order, customer, or delivery field nodes exist. Narrative-only rows use fallback. | Mark `not_assessable` when new business is only layout, news, strategic wording, or theme language. | Which new businesses have disclosed revenue, customers, orders, mass-production deliveries, and collection? | New-business narrative is not income realization. |
| Robotics theme without order / customer / mass-production evidence | Robotics product exposure; signed order; customer; qualification / nomination; mass-production delivery; revenue and collection | `002050` may show robotics actuator-related component layout; current pack may lack revenue ratio and order proof | Robotics order amount; customer names; SOP / mass-production schedule; delivery volume; revenue and collection | If robotics evidence lacks order / customer / mass-production nodes, use `传导路径无法从当前证据包验证`. | Mark `not_assessable` when robotics exposure is not backed by order, customer, mass-production, revenue, and collection evidence. | Is the robotics theme backed by order, customer, mass-production, revenue, and cash collection evidence? | Do not write "humanoid robotics revenue is about to release" without evidence. |
| Customer concentration risk | Top customer share; customer count; named customer revenue; receivable concentration; renewal / program duration; payment terms | Financial receivables may exist; named-customer news may exist only as unverified context | Top-five customer parser; customer revenue share; receivable concentration; program duration; payment terms | A valid path needs customer concentration field/value nodes. News or rumor is not concentration evidence. | Mark `not_assessable` when top customer share or customer receivable concentration is absent. | Does customer concentration create revenue, pricing, receivable, or program-dependency risk? | Do not infer large-customer dependence or independence without disclosed customer data. |
| Receivables / collection deterioration | Receivables; revenue; operating cash flow; aging; overdue; bad-debt provision; customer concentration | `financial_metrics.accounts_receivable`, revenue, and operating cash flow may exist | Aging; overdue; DSO; bad-debt provision; customer payment terms; concentration | A path may cite aggregate receivables and cash flow as observations only. Deterioration requires aging / overdue / DSO / customer evidence. | Mark `not_assessable` when only aggregate receivables are available. | Are receivables deteriorating after considering aging, overdue balances, customer concentration, and operating cash flow? | Do not label receivable growth as high quality or deterioration without collection evidence. |
| Inventory build without demand bridge | Inventory; product split; turnover; orders; shipments; production; revenue; gross margin; write-down | Aggregate inventory, revenue, and gross margin may exist | Product-level inventory; turnover; order / shipment bridge; production-sales reconciliation; write-down | Valid only as aggregate working-capital observation unless product and operating bridge exists. | Mark `not_assessable` for demand conclusion when only aggregate inventory exists. | Does inventory build reflect production timing, product mix, demand, delayed shipment, or write-down risk? | Inventory growth or decline is not direct demand evidence. |
| Capex without utilization / revenue bridge | Capex; project; acceptance; capacity; utilization; output; delivery; revenue and cash flow | Capex, revenue, and operating cash flow may exist | Project-level capex; acceptance; utilization; output / delivery; revenue conversion | A path may cite capex only as investment / cash outflow. It must not imply utilization or revenue conversion. | Mark `not_assessable` for utilization or revenue conversion when project mapping and utilization are absent. | Is there risk that capex has not converted into accepted capacity, utilization, delivery, revenue, or cash flow? | Capex is not utilization or revenue conversion. |
| Gross margin pressure from product mix or price competition | Segment margin; product mix; price change; cost; customer mix; competitor / price-cut evidence; volume | Aggregate gross margin and segment gross margin may exist | Product-level margin; ASP; unit cost; competitive pricing; customer mix; warranty / quality cost | A path may cite margin fields but cannot attribute pressure without mix / price / cost / customer evidence. | Mark `not_assessable` when margin pressure attribution lacks product mix, price, cost, or customer evidence. | Is margin pressure from product mix, price competition, cost, or customer structure, and what evidence supports it? | Do not infer price competition or product upgrade from gross margin alone. |
| Overseas customer / FX / trade risk | Overseas customer share; export revenue; FX exposure; trade restriction event; affected product / customer; margin / cash impact | Geographic segment may exist if disclosed; otherwise usually absent | Overseas revenue split; FX gains / losses; currency exposure; trade policy event; customer/product impact | Valid only when company-specific overseas / FX / trade field nodes exist. Otherwise use fallback. | Mark `not_assessable` when exposure and impact nodes are absent. | Which overseas customers, export products, currencies, or trade restrictions affect revenue, margin, receivables, and cash flow? | Do not infer FX or trade risk magnitude from overseas possibility alone. |
| Product qualification or mass-production delay | Qualification stage; expected SOP / delivery date; delay event; affected product / customer; revenue and collection impact | Usually missing; news may mention layout only as unverified context, not verified milestones | Qualification tracker; design-win / nomination status; SOP delay; customer acceptance; shipment / revenue impact | Valid only when qualification or delay field/value nodes exist. Missing evidence does not prove success or failure. | Mark `not_assessable` when qualification status, mass-production schedule, or delay event is absent. | Are any products delayed in qualification or mass production, and what revenue, shipment, or collection impact is disclosed? | Do not infer smooth customer introduction or delay from missing data. |

## 6. Primary Sample Design: 002050

For `002050`, the P1.1 advanced-manufacturing expansion should use the company as the primary sample for `advanced_manufacturing_growth`.

The first-version matrix should explicitly distinguish three business layers:

| Layer | Why it must be separated | Expected P1.1 behavior |
| --- | --- | --- |
| Refrigeration / air-conditioning component core business | It is the traditional revenue base and should not be mixed with robotics growth narrative. | Segment exposure may be `partial` if `business_composition` provides a concrete revenue ratio. Demand, pricing power, and customer quality remain evidence-gated. |
| Automotive components / EV thermal management | It may be a major growth business and has different customer, program, delivery, margin, and receivable dynamics. | Segment exposure may be `partial`; customer programs, order visibility, mass production, collection, and concentration usually remain `missing` / `not_assessable`. |
| Robotics / actuator / emerging business | It is the highest narrative-risk layer and must not be treated as realized revenue without revenue, order, customer, and mass-production evidence. | Usually `not_assessable` unless the evidence pack contains concrete robotics revenue split, orders, customer qualification, accepted delivery, and collection nodes. |

Three-layer data isolation is mandatory:

- The three layers are: refrigeration / air-conditioning core business; automotive thermal management; and robotics / actuator / emerging business.
- Each layer's `company_transmission_path` must cite that layer's own `business_composition[]` node when making a segment exposure observation.
- Robotics / actuator / emerging business must not cite refrigeration / air-conditioning or automotive thermal-management `business_composition[]` or financial data as proxy transmission nodes.
- If the robotics layer has no independent segment and no explicit non-zero `revenue` or `revenue_ratio`, it must not use company-level `revenue_yoy`, `gross_margin`, `operating_cashflow`, `accounts_receivable`, or `inventory` as robotics transmission nodes.
- Financial performance from the traditional core business or automotive thermal-management business must not support a robotics realization conclusion.

The current evidence pack appears capable of checking:

- `stock.strategy_type=advanced_manufacturing_growth`.
- `basic_info.industry`.
- `basic_info.main_business` describing refrigeration control components, automotive thermal-management components, and robotics actuator-related component layout when present.
- `business_composition` indicating refrigeration / air-conditioning component exposure and automotive thermal-management component exposure, including revenue ratios when present.
- `financial_metrics.revenue`, `revenue_yoy`, `gross_margin`, `net_profit`, `deducted_net_profit`, `operating_cashflow`, `accounts_receivable`, and `inventory` when present.
- `valuation_metrics.pe_ttm`, `pb`, and `market_cap` only as evidence sufficiency context.
- `risk_flags`, `missing_fields`, or `enhanced_must_track_indicators` for robotics realization, big-customer exposure, receivables, and cash conversion when present.

Expected sample behavior:

- Core and automotive segment rows may be `partial` only when concrete `business_composition` field/value nodes are cited.
- Robotics / humanoid robotics rows should usually be `not_assessable` because current fixture-like data mentions layout but lacks revenue split, order amount, customer, mass-production delivery, and collection evidence.
- Big-customer exposure should remain `not_assessable` unless top customer revenue share, named customer order, customer receivable concentration, or payment terms are disclosed.
- Accounts receivable, inventory, and operating cash flow may be checked as aggregate financial observations, but they must not become customer quality, demand strength, or revenue durability conclusions without aging, turnover, customer, order, and shipment evidence.
- Valuation context should generate research questions about evidence sufficiency: profit growth, gross margin stability, cash-flow conversion, automotive thermal-management evidence, and robotics revenue / order evidence. It must not generate target price or trading language.

## 7. Company Transmission Path Constraint

`company_transmission_path` remains an evidence-bound field, not a narrative field.

For the advanced-manufacturing expansion:

- A valid path must cite concrete current `evidence_pack` field/value nodes.
- Valid nodes include concrete `evidence_pack.business_composition[...]` segment nodes with explicit field values, `evidence_pack.financial_metrics.revenue`, `evidence_pack.financial_metrics.revenue_yoy`, `evidence_pack.financial_metrics.gross_margin`, `evidence_pack.financial_metrics.operating_cashflow`, `evidence_pack.financial_metrics.accounts_receivable`, `evidence_pack.financial_metrics.inventory`, `evidence_pack.financial_metrics.contract_liabilities`, `evidence_pack.financial_metrics.capex`, `evidence_pack.financial_metrics.r_and_d_expense`, `evidence_pack.financial_metrics.r_and_d_expense_ratio`, `evidence_pack.valuation_metrics` for evidence sufficiency context only, and relevant `enhanced_must_track_indicators[...]` statuses when present.
- `evidence_pack.basic_info.main_business` is descriptive context only unless paired with a concrete segment / financial / operating field-value node. It cannot by itself be a valid business node.
- Strategic-layout wording in `basic_info.main_business` or `business_composition[].segment_name` must not become a valid robotics / new-business node. Examples include "积极布局", "开展研发", "开始涉足", "战略合作", "机器人关键零部件布局", and "执行器布局".
- Robotics / actuator / emerging-business rows may form a non-fallback path only when `business_composition[]` contains an explicit non-zero robotics / emerging-business `revenue_ratio` or `revenue`, or when other direct robotics order / customer / mass-production / collection field-value nodes exist.
- If the robotics layer has no independent `revenue_ratio` / `revenue` value, all robotics drivers must use `company_transmission_path=传导路径无法从当前证据包验证` and `confidence_cap=not_assessable`.
- `news` / `latest_news` fields must not be valid `company_transmission_path` nodes. Even when news appears indirectly through `enhanced_must_track_indicators`, `risk_flags`, or `supporting_evidence`, it must not be treated as business realization evidence.
- News may only be risk context or a follow-up clue. If cited, it must be labeled "unverified context, not operating fact".
- Mock / unverified news must not support revenue, order, customer, mass-production, collection, or valuation explainability conclusions.
- Macro, industry, EV demand, robotics theme, customer capex, customer rumors, policy, or news language is not a company transmission path by itself.
- If no concrete company node exists, `company_transmission_path` must be exactly `传导路径无法从当前证据包验证`.
- Any row using the fallback must set `confidence_cap=not_assessable`.
- A non-fallback path must not use `confidence_cap=not_assessable`.

Valid path shape:

```text
evidence_pack.business_composition[0]=segment_name: refrigeration / air-conditioning components; revenue_ratio: ...
-> evidence_pack.business_composition[1]=segment_name: automotive thermal-management components; revenue_ratio: ...
-> evidence_pack.financial_metrics.revenue_yoy=...
-> evidence_pack.financial_metrics.operating_cashflow=...
-> missing_evidence: customer orders / mass-production delivery / receivable aging / product-line margin
```

Invalid path shape:

```text
Robotics industry space is large, so the company benefits.
High-end manufacturing is booming, so company growth is certain.
Customer capex increases, so company revenue will grow.
Design-win has been obtained, so batch revenue is confirmed.
Capex increased, so capacity and revenue will be released.
Contract liabilities increased, so backlog is strong.
```

## 8. Not-Assessable / Missing Evidence Rules

Use `not_assessable` when evidence cannot complete the driver chain:

```text
driver signal
-> company evidence node
-> operating / financial bridge
-> missing evidence or research question
```

Specific advanced-manufacturing rules:

- If no evidence-pack concrete field or data point supports the company transmission path, use `company_transmission_path=传导路径无法从当前证据包验证` and `confidence_cap=not_assessable`.
- If `basic_info.main_business` or `business_composition[].segment_name` contains only strategic-layout wording such as "积极布局", "开展研发", "开始涉足", "战略合作", "机器人关键零部件布局", or "执行器布局", treat it as narrative context only, not a valid business node.
- If robotics / actuator / emerging-business exposure lacks an independent non-zero `revenue_ratio` or `revenue`, or direct order, customer, mass-production delivery, and collection evidence, mark robotics realization `not_assessable` and force the fallback path.
- If customer qualification / nomination / design-win lacks shipment, accepted delivery, revenue recognition, and collection evidence, mark revenue conversion `not_assessable`.
- If contract liabilities are the only order-related evidence, order visibility and backlog remain `not_assessable`.
- If capex lacks project mapping, acceptance, utilization, output, delivery, and revenue bridge, utilization and revenue conversion remain `not_assessable`.
- If R&D expense / ratio lacks product conversion, customer validation, order, revenue, and margin evidence, moat and commercialization remain `not_assessable`.
- If receivables lack aging, payment terms, and customer concentration, collection quality remains `not_assessable`.
- If inventory lacks product split, turnover, production-sales reconciliation, order, shipment, and write-down detail, demand interpretation remains `not_assessable`.
- If valuation metrics lack profit growth, margin, cash-flow, and new-business realization evidence, valuation explainability remains an evidence-sufficiency question only.
- Aggregate inventory must not be mapped to a single business layer, especially robotics / actuator / emerging business, without product category or layer split.
- Inventory growth or decline must not be used to judge robotics demand strength or weakness. Demand interpretation requires product-level inventory split, turnover, production-sales bridge, orders, shipments, or write-down evidence.
- Valuation explainability Chinese output must use fixed evidence-sufficiency wording similar to: "当前 evidence pack 中哪些证据足以支撑或解释当前估值背景，哪些证据仍缺失？"
- Valuation explainability must not use "估值是否合理", "估值是否偏高/偏低", "是否支撑当前价格", "上涨空间 / 下跌空间", "目标价", or "买入 / 卖出 / 持有".
- Valuation can only be evidence sufficiency context and must not become a trading or valuation judgment.

Use `missing` when the evidence type is expected for the driver but absent from the pack. Use `partial` only when concrete evidence-pack nodes support a limited observation and the row explicitly lists the missing bridge.

Advanced manufacturing status mapping:

| Evidence condition | `data_availability_status` | `confidence_cap` | Required behavior |
| --- | --- | --- | --- |
| Each of the three business layers has a concrete segment node plus financial node | `partial` | `low` / `medium` | Use only as exposure or limited financial observation; do not infer realization without customer / order / production / collection bridge. |
| A business layer has only `segment_name` but no `revenue` / `revenue_ratio` | `partial` or `missing` | `low` / `not_assessable` | Do not form realization conclusions; list missing numeric revenue evidence. |
| Robotics / actuator / emerging business has no independent non-zero `revenue_ratio` / `revenue` | `not_assessable` | `not_assessable` | Force `company_transmission_path=传导路径无法从当前证据包验证` for robotics drivers. |
| Evidence explicitly shows the driver is unrelated to company business | `not_applicable` | `not_assessable` | State why the driver is outside the company business scope. |
| Expected evidence is absent or not disclosed | `missing` or `not_assessable` | `not_assessable` | Do not replace missing data with `not_applicable`. |
| Contradictory signals exist, such as revenue growth while operating cash flow worsens or accounts receivable rises materially | `partial` | `low` | List both signals in `available_evidence` and generate a research question about cash conversion / collection quality. |
| Valuation explainability has incomplete operating evidence | `not_assessable` or `partial` | `not_assessable` / `low` | Output only an evidence sufficiency question; do not say valuation is reasonable, high, or low. |

## 9. Future Data Needs

Future implementation phases may record these as missing evidence, but this design phase must not add connectors:

- Product-line revenue and gross margin for refrigeration / air-conditioning, automotive thermal management, and robotics / actuator components.
- Robotics / humanoid robotics revenue split, signed orders, customer list, qualification / nomination / design-win stage, mass-production schedule, delivery volume, and collection.
- Automotive / EV thermal-management customer programs, SOP / mass-production status, accepted delivery, order duration, and customer payment terms.
- Top-five customer revenue share, named customer concentration, receivable concentration, and major customer changes.
- Receivable aging, overdue receivables, DSO, bad-debt provision, and customer-level payment terms.
- Inventory split by product and type, turnover, production-sales reconciliation, and write-down detail.
- Capex project mapping, acceptance, capacity, utilization, output / delivery, and capex-to-revenue bridge.
- Overseas revenue split, export customer geography, FX gains / losses, currency exposure, trade restriction mapping, and overseas collection cycle.
- R&D project milestones, product conversion, validation, yield / reliability, customer adoption, and revenue contribution.
- Longitudinal disclosure history and independent source-bucket consensus.

## 10. First Implementation Scope Recommendation

Implementation gate before code changes:

- Confirm which segments are actually present in `002050 business_composition[]`.
- Confirm whether each segment has an explicit `revenue_ratio` or `revenue`.
- Confirm whether robotics / actuator-related business has an independent non-zero `revenue_ratio` or `revenue`.
- Confirm whether `enhanced_must_track_indicators[]` contains qualification / nomination / design-win / customer order status fields.
- Confirm whether `financial_metrics.contract_liabilities` has an actual numeric value.
- Confirm whether fields exist for customer concentration, receivable aging, inventory split, and capex project mapping.
- If these checks cannot confirm independent robotics revenue / order / customer / mass-production / collection evidence, robotics rows must default to `not_assessable`.

Recommended first implementation:

- Support only `strategy_type=advanced_manufacturing_growth` and only primary sample `002050`.
- Keep `601689` as future validation / boundary sample, not first-version positive implementation scope.
- Generate evidence-pack-only P1.1 driver rows and research questions.
- Split driver questions by business layer: core refrigeration / air-conditioning, automotive thermal management, and robotics / emerging business.
- Keep the three business layers separate in both driver rows and `company_transmission_path` construction.
- Treat robotics / actuator / emerging business more conservatively by default: missing independent revenue, orders, customers, mass production, or collection means `not_assessable`.
- Allow `partial` rows only for concrete core / automotive segment exposure and aggregate financial observations when field/value nodes exist.
- Force robotics realization, big-customer exposure, order visibility, mass-production evidence, capex utilization, inventory demand interpretation, and collection quality to `missing` / `not_assessable` unless concrete evidence-pack nodes support them.
- Preserve exact `company_transmission_path` fallback and `confidence_cap=not_assessable` behavior.
- Do not change classifier, connector, scoring, readiness, deterministic pipeline, HTML, Dashboard, output schema, `status`, `confidence`, `score`, `strategy_type`, or `sub_type`.

Do not include in first implementation:

- `601689` as a supported positive implementation path.
- New data connectors.
- Robotics industry forecast.
- Trading or valuation model output.
- Target price or position language.
- Trading advice, position sizing, technical analysis, or K-line logic.
- Any deterministic score / confidence mutation.

## 11. Future Validation / Boundary Samples

| Sample | Role | Validation purpose |
| --- | --- | --- |
| `002050` Sanhua Intelligent Controls | Primary sample | Tests core refrigeration / air-conditioning base, automotive thermal-management segment, robotics narrative risk, big-customer exposure gaps, receivable / inventory / operating-cash-flow checks, and valuation evidence sufficiency. |
| `601689` Tuopu Group | Future validation / boundary sample | Primary boundary test for coexistence of large-customer concentration and robotics narrative: the system must generate both customer concentration risk questions and robotics realization evidence questions without one masking the other. If automotive core business and robotics business segments are not clearly separated, trigger "层归属不可确认" or `not_assessable`. |
| Later advanced-manufacturing samples | Optional future candidates | Use only after `002050` first implementation is accepted; select companies with distinct sub-chain exposure such as industrial automation, precision components, or robotics components. |

## 12. External Audit Incorporation

Claude external audit has been incorporated in Revision v1.1.

Mandatory audit outcomes now embedded in this design:

- Robotics strategic-layout wording is excluded from valid business nodes unless independent non-zero revenue / revenue ratio or direct order / customer / mass-production / collection evidence exists.
- The three business layers for `002050` must remain isolated: refrigeration / air-conditioning core business, automotive thermal management, and robotics / actuator / emerging business.
- `news` / `latest_news` are excluded from valid `company_transmission_path` nodes and can only be unverified context or follow-up clues.
- Advanced-manufacturing status mapping is defined before implementation, including robotics forced fallback, contradictory-signal handling, and valuation evidence-sufficiency constraints.
- Driver de-duplication, aggregate-inventory constraints, and the `601689` boundary sample are explicitly scoped.

## 13. Go / No-Go Recommendation

Recommendation: proceed to P1.1 Advanced Manufacturing implementation after the Section 10 implementation gate confirms the actual `002050` evidence-pack fields and the implementation preserves the v1.1 audit constraints.

Implementation is suitable because the design has a narrow first-version target:

- `advanced_manufacturing_growth + 002050` only.
- Evidence-pack-only.
- Independent P1.1 artifacts only.
- No new connectors or deterministic pipeline changes.
- No HTML / Dashboard integration.
- No change to status, confidence, score, strategy_type, or sub_type.

The implementation should not proceed if it cannot enforce:

- exact fallback `company_transmission_path=传导路径无法从当前证据包验证`;
- `confidence_cap=not_assessable` for fallback rows;
- three-layer data isolation;
- robotics / new-business revenue gating;
- `news` / `latest_news` exclusion from valid transmission nodes;
- customer qualification / design-win / capex / contract-liability proxy guards;
- valuation explainability as fixed evidence-sufficiency wording only;
- no trading, target-price, technical-analysis, or K-line output.
