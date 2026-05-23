# Research Intelligence P1.1 Low Altitude Expansion Design Audit

Date: 2026-05-23

Revision: v1.0

Stage: Design audit only. This document adds design guidance only. It must not change code, tests, P1 schema, deterministic pipeline behavior, classifier rules, connectors, scoring, readiness, HTML renderer, Dashboard, generated output, regression fixtures, or existing artifact semantics.

Target expansion: `low_altitude_economy_infrastructure` only.

Primary sample: `000099` 中信海直, expected `strategy_type=low_altitude_economy_infrastructure`, expected `sub_type=aviation_operations_service`.

Future boundary / negative samples: `688631` can be retained for later `airspace_platform_system` validation; `688070`, `002085`, `001696`, `600967`, and `002895` can remain negative / boundary validation candidates. P1.1 implementation should first use only `000099` as the primary sample.

## 1. Expansion Positioning

P1.1 has already accepted the AI Datacenter pilot, the CXO expansion, and the Satellite expansion. This document designs the next narrow P1.1 expansion for `low_altitude_economy_infrastructure`.

The expansion remains an independent Research Intelligence artifact:

```text
evidence_pack_<code>.json
+ optional P0 research intelligence artifacts
-> research_intelligence_p1_<code>.json
-> research_questions_p1_<code>.json
-> research_questions_p1_<code>.md
```

The expansion should convert low-altitude policy, infrastructure, operation, project, financial, and risk assumptions into evidence-gated driver-factor rows and research questions. It must not become a trading system, valuation model, policy report, industry forecast, dashboard panel, connector project, technical-analysis layer, or deterministic scoring input.

## 2. Non-Negotiable Boundaries

This design is limited to `strategy_type=low_altitude_economy_infrastructure`.

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

- Policy pilot progress is not company revenue.
- Airspace reform is not company-usable airspace unless company-level approval, route, base, operation right, or project evidence exists.
- Local-government spending is not company revenue unless linked to company contracts, acceptance, revenue recognition, and collection evidence.
- Project announcements are not project acceptance.
- Contract liabilities are at most a partial proxy for prepayments or order visibility; they are not true backlog.
- Capex is not service-capacity release, utilization, flight-hour growth, or revenue conversion.
- Missing flight hours / flight sorties / platform dispatch volume prevents factual claims about operating capability, utilization, or demand realization.
- Government / SOE customer type is not payment certainty.
- Low-altitude theme, policy support, route plans, strategic cooperation, and demonstration zones are not business realization without company evidence.

## 3. Current Evidence-Pack Capability

For `000099`, current fixtures indicate that the evidence pack can usually support only a conservative P1.1 low-altitude matrix.

Current `evidence_pack` may have:

- `stock.code`, `stock.name`, `stock.strategy_type`, `stock.sub_type`.
- `stock.status`, `stock.confidence`, `stock.fundamental_score` as read-only context only.
- `basic_info.industry`.
- `basic_info.main_business`.
- `business_composition[]` with segment name, classification type, period, revenue ratio, revenue, gross margin, and profit when present.
- `financial_metrics.period`, `revenue`, `revenue_yoy`, `gross_margin`, `net_margin`, `net_profit`, `deducted_net_profit`, `operating_cashflow`, `accounts_receivable`, `contract_liabilities`, and `capex` when present.
- `valuation_metrics` as explainability context only; no target price or trading framing.
- `confidence_basis.missing_fields`, `confidence_basis.data_coverage`, and `confidence_basis.confidence_breakdown`.
- `enhanced_must_track_indicators[]`.
- `risk_flags`, `unknown_or_missing_evidence`, `missing_fields`, `data_limitations`, `source_trace_summary`, and `forbidden_terms_check`.

Current `evidence_pack` usually does not reliably have:

- Low-altitude policy pilot progress mapped to the company.
- Airspace approval, route approval, base resources, or operation permissions.
- Local-government low-altitude infrastructure spending by project.
- Aviation safety event history, CAAC regulatory penalties, or compliance cost details.
- Low-altitude operation demand series by customer type.
- Flight hours, flight sorties, fleet utilization, aircraft type mix, or revenue per flight hour.
- Platform dispatch volume.
- Route, base, and airspace resource table.
- Project contracts, contract amount, project acceptance, delivery milestones, or revenue recognition schedule.
- Customer type split across government, SOE, enterprise, emergency rescue, offshore oil, tourism, logistics, inspection, or other users.
- Government / SOE collection cycle, receivable aging, bad-debt provisions, and project-level collection evidence.
- Capex-to-service-capacity bridge.
- Longitudinal disclosure consistency.
- Independent multi-source consensus beyond source-bucket counting.

## 4. Driver Factor Matrix Contract

Every low-altitude driver row must use the existing P1.1 driver-factor contract:

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

## 5. Low Altitude Driver Factor Matrix

### 5.1 Macro / Policy / Industry Drivers

| Driver factor | required_evidence | available_evidence from current evidence_pack | missing_evidence / future connector | company_transmission_path rule | not_assessable condition | research_question | interpretation_guard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Low-altitude policy pilot progress | Official policy pilot list; pilot scope; affected city / route / infrastructure segment; company-specific participation; project / contract / revenue / collection bridge | `basic_info.main_business`, `business_composition`, `risk_flags`, `supporting_evidence`, or `enhanced_must_track_indicators` may show low-altitude operation exposure if present | Future official policy connector; demonstration-zone tracker; company announcement parser; project-contract cross-check | Valid only when the path cites concrete company nodes such as `evidence_pack.business_composition[...]` plus company project / revenue / cash-flow fields. If policy has no company node, use `传导路径无法从当前证据包验证`. | Mark `not_assessable` when only policy pilot context exists or company participation / project / revenue evidence is absent. | Which policy pilots are tied to company-specific routes, bases, projects, contracts, revenue recognition, or collection evidence? | Do not write "低空经济政策向好，公司受益"; policy pilot progress is background until company realization is evidenced. |
| Airspace / route approval | Approved airspace; route approval; operating permission; base / takeoff and landing site rights; approval period; company operating volume bridge | `basic_info.main_business` may identify general aviation / low-altitude operation; current pack may include must-track indicators that mark airspace / route resources missing | Future airspace / route approval connector; CAAC / local regulator parser; route-resource disclosure parser | A valid path needs company-level approval, route, base, or operation-right field/value nodes. Main-business text alone is exposure, not approved airspace. If absent, use fallback. | Mark `not_assessable` when airspace, route, base, or operation-right evidence is absent. | What company-usable airspace, route, base, or takeoff / landing resources have been approved, and how do they connect to flight volume and revenue? | Airspace reform policy is not actual company-level usable airspace expansion. |
| Local government low-altitude infrastructure spending | Budget / tender / procurement project; project owner; winning bidder; company contract amount; delivery / acceptance; revenue and collection bridge | Current pack may show revenue, receivables, operating cash flow, contract liabilities, and business composition; local spending data is usually absent | Future government procurement connector; tender / winning-bid parser; project acceptance parser; payment tracker | Valid only if spending is linked to company project or contract nodes in `evidence_pack`; otherwise use fallback. | Mark `not_assessable` when local spending exists without company-specific contract, acceptance, revenue, and collection evidence. | Has local government low-altitude spending converted into disclosed company contracts, accepted projects, revenue, receivables, and cash collection? | Public-budget support and local spending plans are not company revenue. |
| Aviation safety / regulatory requirements | Operating licenses; safety-management disclosures; accident / incident history; CAAC penalties; compliance cost; grounding / rectification events | `risk_flags` or must-track indicators may mark safety data missing; financial fields may show revenue and cash flow but not safety compliance | Future regulator event connector; accident / incident database; annual-report safety disclosure parser; compliance-cost parser | Valid only when company safety / license / penalty / compliance nodes exist. If only regulated-industry context exists, use fallback. | Mark `not_assessable` when licenses, safety events, penalties, rectification, or compliance cost are absent. | What safety, license, penalty, rectification, or compliance-cost evidence affects service continuity, cost structure, or operating risk? | Safety and compliance are constraints; absence of event data is not proof of safety. |
| Low-altitude operation demand | Demand by emergency rescue, offshore oil, tourism, logistics, inspection, government service, and enterprise use; company customer / route / flight-volume bridge | `business_composition` may show general aviation / low-altitude service exposure; `financial_metrics.revenue`, `gross_margin`, `operating_cashflow`, and `accounts_receivable` can test company realization after the fact | Future industry demand connector; customer-type parser; operating-volume connector; contract and route parser | Valid only when company customer, route, flight-hour, sortie, revenue, and cash-flow nodes exist. External demand without company nodes uses fallback. | Mark `not_assessable` when demand is only industry-level or when customer / route / operating-volume evidence is absent. | Which low-altitude demand categories have translated into company customers, routes, flight hours, sorties, revenue, receivables, and cash flow? | Industry demand is not company demand unless the company transmission is evidenced. |

### 5.2 Company / Operating Drivers

| Driver factor | required_evidence | available_evidence from current evidence_pack | missing_evidence / future connector | company_transmission_path rule | not_assessable condition | research_question | interpretation_guard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Low-altitude / general aviation / air-traffic-management revenue contribution | Segment revenue; revenue ratio; segment gross margin; service-line description; period; sub-type routing | `basic_info.main_business`; `business_composition[].segment_name`, `revenue_ratio`, `revenue`, `gross_margin` when present; `financial_metrics.revenue` | Future annual-report segment note parser; low-altitude-specific revenue parser when segment labels are not precise | A concrete path may cite `business_composition` and `financial_metrics.revenue`; it must describe exposure only, not utilization or demand stability. | Mark `not_assessable` when no segment / service-line revenue field exists and only theme or policy language is present. | What share of revenue is directly tied to low-altitude / general aviation / air-traffic-management services, and what period and segment definition support it? | Business composition supports exposure, not flight utilization, route quality, customer stability, or project acceptance. |
| Flight hours | Disclosed flight hours by period; service type; aircraft / route / customer mapping; revenue and cash-flow bridge | Usually missing; must-track indicators may mark `operating_hours` as missing; financial revenue can be checked but cannot substitute | Future operating-data parser; annual-report operating metric parser; regulator / company operation disclosure connector | Valid only when flight-hour field/value nodes exist. Revenue or segment ratio cannot substitute for hours. If absent, use fallback. | Mark `not_assessable` when flight hours are missing. | What disclosed flight hours validate utilization and demand realization, and how do they connect to revenue and cash conversion? | Do not infer operating capability or utilization when flight hours are missing. |
| Flight sorties | Disclosed flight sorties by period; mission type; customer / route mapping; revenue and cash-flow bridge | Usually missing; must-track indicators may mark `flight_sorties` as missing | Future sortie operating-data parser; annual-report operating metric parser | Valid only when sortie field/value nodes exist. If only revenue or main-business text exists, use fallback. | Mark `not_assessable` when flight sorties are missing. | What flight-sortie data validates actual service volume by mission type and customer, and how does it bridge to revenue? | Do not write service volume as fact without sortie evidence. |
| Platform dispatch volume | Dispatch volume; platform users; route / airspace / aircraft coverage; recurring platform revenue; project acceptance | Usually missing for `000099`; more relevant to future `airspace_platform_system` sample `688631` | Future platform-dispatch connector; city-level platform operation parser; project acceptance parser | Valid only when dispatch-volume nodes exist. It should not be inferred for aviation operators unless disclosed. | Mark `not_assessable` when dispatch volume is absent or the company is not routed to platform-system sub-type. | If a platform exists, what dispatch volume and monetization evidence supports platform utilization? | Do not mix platform metrics into aviation operation service unless company evidence supports it. |
| Route / base / airspace resources | Route list; base list; takeoff / landing sites; usable airspace; operating permissions; coverage; utilization | `basic_info.main_business` may imply operation service; current pack usually lacks route / base / airspace resources | Future route / base / airspace resource parser; regulator approval connector; company disclosure parser | Valid only if route, base, approval, or resource field/value nodes exist. Main-business text is not a resource table. | Mark `not_assessable` when route, base, airspace, or permission evidence is absent. | What routes, bases, takeoff / landing sites, and airspace resources does the company control, and how are they used? | Do not convert operating-service description into scarce-resource control. |
| Project contracts | Signed contract; customer; amount; period; service scope; revenue-recognition terms; collection schedule | `financial_metrics.contract_liabilities` may be present as partial proxy; `business_composition` and revenue may be present | Future exchange announcement connector; contract parser; customer / project note parser | A path may cite contract liabilities only as partial proxy. A valid contract path needs signed contract field/value nodes. | Mark `not_assessable` for contract visibility when signed contracts or customer/project terms are absent. | Which contracts support low-altitude / general aviation service revenue, and what amount, customer, scope, and timing are disclosed? | Contract liabilities are not backlog; strategic cooperation or framework agreement is not signed contract revenue. |
| Project acceptance / delivery | Delivery milestone; acceptance certificate; accepted amount; revenue recognition; customer payment; unresolved delivery risk | Current pack may have revenue and receivables but usually lacks acceptance / delivery milestones | Future project acceptance parser; announcement and annual-report project tracker; payment progress connector | Valid only when acceptance / delivery nodes exist. Project announcement or contract cannot substitute for acceptance. | Mark `not_assessable` when project acceptance or delivery evidence is absent. | Which projects have been delivered and accepted, and how is acceptance linked to revenue recognition and cash collection? | Do not treat project announcement, winning bid, or contract signing as acceptance. |
| Customer type | Customer split by government, SOE, enterprise, emergency rescue, offshore oil, tourism, logistics, inspection, or other users; revenue / receivable concentration by customer type | `business_composition` may imply service exposure; `financial_metrics.accounts_receivable` and `operating_cashflow` may be available | Future customer-type parser; top-five customer parser; receivable concentration and payment-term parser | Valid only when customer type or customer concentration field/value nodes exist. Segment revenue cannot substitute for customer structure. | Mark `not_assessable` when customer type, concentration, and payment terms are absent. | What customer types drive revenue, receivables, and cash collection, and where is government / SOE payment-cycle risk concentrated? | Government or SOE customer type does not imply payment certainty. |

### 5.3 Financial Drivers

| Driver factor | required_evidence | available_evidence from current evidence_pack | missing_evidence / future connector | company_transmission_path rule | not_assessable condition | research_question | interpretation_guard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Revenue stability | Revenue by period; segment revenue; contract duration; customer concentration; flight hours / sorties; renewal or recurring service evidence | `financial_metrics.revenue`; `business_composition.revenue_ratio` / `revenue` when present | Future contract-duration parser; customer concentration parser; operating-volume connector; longitudinal disclosure store | A path may cite revenue and segment fields, but must state missing contract / customer / flight-volume bridge. It cannot assert stability without those nodes. | Mark `not_assessable` for revenue stability when contract duration, customer concentration, and operating volume are missing. | Is revenue stability supported by contracts, customers, flight hours / sorties, renewal evidence, and cash collection, or only by historical revenue fields? | Historical revenue alone is not stability proof. |
| Gross margin stability | Gross margin by period; segment gross margin; service mix; aircraft utilization; fuel / maintenance / depreciation cost; pricing terms | `financial_metrics.gross_margin`; `business_composition.gross_margin` when present | Future segment-margin history; service-price parser; utilization and cost-detail parser | A concrete path may cite margin fields, but margin stability requires period comparison and operating-cost bridge. | Mark `not_assessable` when only one-period margin or no utilization / service mix / cost bridge exists. | Is gross margin stability explained by service mix, aircraft utilization, pricing, maintenance, depreciation, and compliance cost? | Do not infer pricing power or utilization from gross margin alone. |
| Operating cash flow | Operating cash flow; revenue; receivables; contract liabilities; customer payment terms; project collection history | `financial_metrics.operating_cashflow`, `revenue`, `accounts_receivable`, and `contract_liabilities` may be available | Future payment-term parser; cash-conversion calculation; project / customer collection connector | A concrete path may cite cash flow, revenue, receivables, and contract liabilities as financial nodes, but must frame collection quality as a question if payment terms are missing. | Mark `not_assessable` for customer payment quality when payment terms, receivable aging, and customer concentration are absent. | Does operating cash flow support revenue quality after considering receivables, contract liabilities, customer type, and collection cycle? | Cash flow is validation evidence, not proof of demand durability. |
| Receivables | Accounts receivable; revenue; receivable aging; bad-debt provision; customer concentration; government / SOE exposure; operating cash flow | `financial_metrics.accounts_receivable`, `revenue`, `operating_cashflow` may be available | Future receivable aging / bad-debt note parser; customer receivable concentration; payment-term connector | A path may cite receivables, revenue, and cash flow. It cannot assert collection certainty without aging and customer evidence. | Mark `not_assessable` for collection risk quality when aging, payment terms, or customer concentration are absent. | Are receivables consistent with recognized service revenue, or do aging, concentration, and payment terms indicate collection pressure? | Recognized revenue and government customer labels do not guarantee collection. |
| Government / SOE collection cycle | Customer type; payment terms; project acceptance; receivable aging; overdue receivables; cash receipts by customer or project | Current pack may have accounts receivable and operating cash flow but usually lacks customer type and aging | Future customer parser; receivable aging parser; government procurement payment tracker | Valid only when government / SOE customer and payment-cycle nodes exist. If only receivables exist, use financial observation without collection-cycle conclusion. | Mark `not_assessable` when customer type, aging, payment terms, and project payment status are absent. | How long is the collection cycle for government / SOE customers, and is payment delayed after project acceptance or service delivery? | Do not treat government / SOE customers as payment certainty. |
| Contract liabilities as partial proxy only | Contract liabilities; prepayment terms; linked customer / contract / project disclosure; revenue recognition terms; comparison with revenue and cash flow | `financial_metrics.contract_liabilities` may be available; revenue and operating cash flow may be available | Future contract-note parser; project / customer disclosure connector | A path may cite `financial_metrics.contract_liabilities`, but the interpretation guard must say partial proxy only and must not label it backlog. | Mark `not_assessable` for backlog or order visibility when contract liabilities are the only order-related evidence. | What customer, contract, or project do contract liabilities correspond to, and why should they not be treated as true backlog? | Contract liabilities are only partial proxy; they are not backlog. |
| Capex-to-service-capacity bridge | Capex; aircraft / base / platform / project mapping; delivery / acceptance; flight hours / sorties; utilization; revenue and cash-flow bridge | `financial_metrics.capex` may be available; revenue, margin, and operating cash flow may be available | Future capex project parser; fixed-asset note parser; aircraft / base / route resource tracker; utilization connector | A path may cite capex as cash outflow or investment only. It must not claim service-capacity release without project, asset, acceptance, utilization, revenue, and cash-flow nodes. | Mark `not_assessable` for service-capacity release when only capex is available. | Which aircraft, bases, routes, platforms, or projects does capex fund, and has the company disclosed acceptance, utilization, revenue, and cash-flow bridges? | Capex is not service capacity release, utilization, or revenue certainty. |
| Safety / compliance cost | Safety-management cost; maintenance cost; training cost; insurance cost; regulatory penalty; rectification cost; impact on margin and cash flow | Usually missing; gross margin and operating cash flow may be available but cannot isolate compliance cost | Future annual-report cost note parser; safety / compliance disclosure parser; penalty and insurance event connector | Valid only when safety, compliance, maintenance, insurance, penalty, or rectification cost nodes exist. Margin alone cannot substitute. | Mark `not_assessable` when cost details are absent. | What safety and compliance costs affect service continuity, gross margin, and cash conversion? | Do not infer safety-cost burden or absence from aggregate gross margin alone. |

### 5.4 Risk Drivers

| Driver factor | required_evidence | available_evidence from current evidence_pack | missing_evidence / future connector | company_transmission_path rule | not_assessable condition | research_question | interpretation_guard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Airspace approval delay | Approval applications; route / airspace approval status; delay events; affected service or project; revenue impact | Usually missing; main-business text may identify exposure | Future regulator approval connector; company announcement parser; project delay tracker | Valid only when approval / delay field/value nodes exist. If absent, use fallback for delay assessment. | Mark `not_assessable` when route / airspace approval and delay evidence are absent. | Are any airspace or route approvals delayed, and which services, projects, flight volumes, or revenues are affected? | Do not infer approved airspace or absence of delay from policy direction. |
| Project acceptance delay | Project list; expected acceptance date; actual acceptance; delay reason; revenue recognition and payment impact | Revenue and receivables may be available; project acceptance usually missing | Future project tracker; acceptance announcement parser; customer payment connector | Valid only when project / acceptance / delay nodes exist. | Mark `not_assessable` when project acceptance timeline is absent. | Which projects are waiting for acceptance, and how would delays affect revenue recognition, receivables, and cash flow? | Project announcement is not acceptance; delivery is not collection. |
| Safety incident / regulatory penalty | Accident / incident; CAAC penalty; grounding / rectification; insurance claim; service interruption; financial impact | `risk_flags` may mark missing safety data; current pack usually lacks events | Future regulator / CAAC event connector; accident database; announcement parser | Valid only when event / penalty field/value nodes exist. | Mark `not_assessable` when event database or company safety disclosure is absent; do not assert no incidents. | Have safety incidents, penalties, grounding, or rectification events affected operations, costs, or customer service continuity? | Absence of evidence is not evidence of safe operations. |
| Government payment delay | Customer type; project acceptance; payment schedule; overdue receivables; receivable aging; operating cash-flow pressure | Accounts receivable and operating cash flow may be available | Future customer-type parser; receivable-aging parser; government payment tracker | Valid only when government customer and payment delay nodes exist; otherwise use financial observations without payment-certainty conclusion. | Mark `not_assessable` when government / SOE exposure and aging / overdue evidence are absent. | Is there evidence of government payment delay after service delivery or project acceptance, and how does it affect operating cash flow? | Government customer exposure is not collection certainty. |
| Utilization / flight-hour insufficiency | Fleet scale; aircraft type mix; flight hours; flight sorties; route / base usage; revenue per flight hour | Usually missing except segment revenue and financial fields | Future fleet and operating-volume parser; utilization connector | Valid only when utilization / flight-hour / sortie nodes exist. Revenue cannot substitute for utilization. | Mark `not_assessable` when flight hours, sorties, and fleet utilization are absent. | Does operating volume support fleet and service-capacity utilization, or is utilization not assessable from current evidence? | Do not state operating ability or demand stability when hours / sorties are missing. |
| Policy pilot does not convert into company revenue | Policy pilot; company project role; contract; acceptance; revenue recognition; collection | Policy context may appear in evidence rows; financial revenue may be available | Future policy-to-project tracker; contract and acceptance parser | Valid only when policy pilot and company project / financial nodes exist. If either side is absent, use fallback or mark missing bridge. | Mark `not_assessable` when policy pilot cannot be linked to company contract, acceptance, revenue, and collection evidence. | Which policy pilots have failed or not yet proven conversion into company contracts, accepted projects, revenue, and cash collection? | Do not treat policy pilot as project income. |
| Customer concentration | Top customer share; customer count; customer type; revenue concentration; receivable concentration; renewal / contract duration | `risk_flags`, `missing_fields`, or must-track indicators may identify missing customer data; financial receivables may be available | Future top-five customer parser; customer contract connector; receivable concentration parser | A valid path needs customer field/value nodes. Segment revenue or industry labels cannot substitute. | Mark `not_assessable` when top customer share, active customer count, or concentration evidence is absent. | Does customer concentration create renewal, pricing, receivable, or one-off revenue risk? | Do not infer diversified demand from service-category labels. |
| Weather / operational disruption risk | Weather disruptions; route cancellation; mission delay; service interruption; seasonal operating data; revenue / cost impact | Usually missing; financial fields cannot isolate weather disruption | Future operating event connector; route / mission cancellation parser; annual-report risk note parser | Valid only when weather / disruption event nodes exist. If absent, use fallback for event assessment. | Mark `not_assessable` when disruption event or seasonal operating data is absent. | What weather or operational disruptions affect flight hours, sorties, service delivery, cost, or customer continuity? | Do not infer operational continuity from annual revenue alone. |

## 6. Primary Sample Design: 000099

For `000099`, the P1.1 low-altitude expansion should use the company as the primary sample for `aviation_operations_service`.

The current evidence pack appears capable of checking:

- `stock.strategy_type=low_altitude_economy_infrastructure`.
- `stock.sub_type=aviation_operations_service`.
- `basic_info.industry`.
- `basic_info.main_business` describing general aviation operation / low-altitude flight services.
- `business_composition` indicating general aviation transportation exposure, including revenue ratio and gross margin when present.
- `financial_metrics.revenue`, `gross_margin`, `operating_cashflow`, `accounts_receivable`, `contract_liabilities`, and `capex` when present.
- missing fields or must-track indicators for operating hours, flight sorties, fleet size, route / base / airspace resources, customer structure, project acceptance, and safety events when present.
- source trace buckets for business composition and financial statements where available.

Expected sample behavior:

- Rows tied to `basic_info`, `business_composition`, revenue, gross margin, operating cash flow, receivables, contract liabilities, or capex may be `partial` only when concrete `evidence_pack` field/value nodes are cited.
- Low-altitude policy pilot progress, airspace / route approval, local government spending, operation demand, flight hours, flight sorties, route / base / airspace resources, project acceptance, customer type, collection cycle, safety / compliance cost, and disruption events should usually remain `missing` or `not_assessable`.
- Contract liabilities may be included only as partial proxy and must not upgrade backlog or contract visibility.
- Capex may be included only as investment / cash outflow observation and must not imply service-capacity release, flight-hour growth, utilization, or revenue conversion.
- Government, SOE, emergency rescue, offshore oil, or tourism customer categories must not be inferred unless disclosed.
- Operating capability must not be written as a fact when flight hours, flight sorties, and fleet utilization are missing.

## 7. Company Transmission Path Constraint

`company_transmission_path` remains an evidence-bound field, not a narrative field.

For the low-altitude expansion:

- A valid path must cite concrete current `evidence_pack` field/value nodes.
- Valid nodes may include `evidence_pack.basic_info.main_business`, `evidence_pack.basic_info.industry`, `evidence_pack.business_composition[...]`, `evidence_pack.financial_metrics.revenue`, `evidence_pack.financial_metrics.gross_margin`, `evidence_pack.financial_metrics.operating_cashflow`, `evidence_pack.financial_metrics.accounts_receivable`, `evidence_pack.financial_metrics.contract_liabilities`, `evidence_pack.financial_metrics.capex`, and relevant `enhanced_must_track_indicators[...]` statuses.
- Macro, policy, industry, airspace reform, local-government spending, demand, or customer-category language is not a company transmission path by itself.
- If no concrete evidence-pack field or data point can verify the company transmission path, the path must use the exact P1.1 fallback value: `传导路径无法从当前证据包验证`.
- Any row using the fallback must set `confidence_cap=not_assessable`.
- A non-fallback path must not use `confidence_cap=not_assessable`.

Valid path shape:

```text
evidence_pack.business_composition[0]=segment_name: general aviation transportation; revenue_ratio: ...
-> evidence_pack.financial_metrics.revenue=...
-> evidence_pack.financial_metrics.operating_cashflow=...
-> missing_evidence: flight hours / flight sorties / route resources / customer type / safety events
```

Invalid path shape:

```text
Low-altitude policy support improves, so the company benefits.
Airspace reform is progressing, so company flight volume will increase.
Local governments are spending on low-altitude infrastructure, so company revenue will grow.
Project announcement means project acceptance.
Contract liabilities mean backlog.
Capex means service capacity has been released.
Government customers imply collection certainty.
```

## 8. Not-Assessable / Missing Evidence Rules

Use `not_assessable` when evidence cannot complete the driver chain:

```text
driver signal
-> concrete company evidence node
-> operating / financial bridge
-> missing evidence or research question
```

Specific low-altitude rules:

- If no evidence-pack field or data point can verify the company transmission path, `company_transmission_path` must be exactly `传导路径无法从当前证据包验证`.
- Any row using that fallback must set `confidence_cap=not_assessable`.
- If policy pilot progress lacks company-specific route, base, project, contract, revenue, and collection evidence, mark realization `not_assessable`.
- If airspace or route approval evidence is absent, do not infer usable airspace from airspace reform policy.
- If local-government spending lacks company-specific contract, acceptance, revenue, and collection evidence, mark company transmission `not_assessable`.
- If low-altitude operation demand lacks customer, route, flight-hour, sortie, revenue, receivable, and cash-flow bridge, mark company demand realization `not_assessable`.
- If flight hours or flight sorties are missing, do not assert utilization, operating capability, demand stability, or revenue per flight hour.
- If platform dispatch volume is missing, do not infer platform usage from project labels or revenue.
- If route, base, or airspace resources are missing, do not infer scarce resource control from main-business text.
- If project contracts are absent, contract liabilities alone cannot prevent `not_assessable` for true contract visibility or backlog.
- If project acceptance is absent, do not treat project announcements, winning bids, or signed contracts as accepted / revenue-recognized projects.
- If customer type and customer concentration are absent, do not assert diversified demand, government order stability, or payment certainty.
- If receivable aging, payment terms, and customer concentration are absent, collection cycle remains `missing` or `not_assessable`.
- If capex exists without asset / project / acceptance / utilization / revenue / cash-flow bridge, service-capacity release is `not_assessable`.
- If safety events, penalties, rectification, or compliance costs are absent, do not assert absence of safety risk.
- If fewer than two independent source buckets are available, consensus / divergence / contradiction remains `not_assessable`.

## 9. Future Data Needs

P1.1 low-altitude implementation should not add connectors, but the document should tag these as future needs:

- Official low-altitude policy pilot and demonstration-zone connector.
- Airspace, route, base, takeoff / landing site, and operating-permission connector.
- Local government procurement, budget, tender, and winning-bid connector.
- Annual-report note parser for low-altitude / general aviation revenue, customer type, fleet, aircraft type mix, safety, and operating qualifications.
- Flight hours, flight sorties, fleet utilization, and revenue-per-flight-hour operating metric parser.
- Platform dispatch volume connector for future `airspace_platform_system` samples.
- Project contract, project delivery, project acceptance, and revenue-recognition tracker.
- Customer-type and top-five customer parser, including government, SOE, enterprise, emergency rescue, offshore oil, tourism, logistics, and inspection users.
- Receivable aging, bad-debt provision, payment-term, and project collection-cycle parser.
- Capex project mapping, aircraft / base / route / platform asset tracker, and service-capacity bridge extractor.
- Aviation safety incident, CAAC penalty, grounding, rectification, insurance, and compliance-cost connector.
- Weather, route cancellation, operational disruption, and service-interruption event tracker.
- Longitudinal disclosure store for prior periods and prior P0/P1 outputs.

## 10. Implementation Recommendation

Recommendation: enter P1.1 Low Altitude implementation after this design is accepted.

Minimum implementation should:

- Add a `low_altitude_economy_infrastructure` driver template inside the existing P1.1 builder boundary.
- Reuse the existing P1 schema without adding fields.
- Keep the current independent P1 artifact relationship.
- Read only current `evidence_pack` and optional P0 artifacts.
- Preserve existing `company_transmission_path` schema enforcement.
- Preserve source-bucket independent counting.
- Preserve the exact P1.1 safety boundary.
- Use `000099` as the only primary implementation sample.
- Keep future boundary / negative samples for later observation only.

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
- Automated industry forecasts.
- Automated policy impact conclusions.
- Technical analysis or K-line logic.
- Trading advice or account actions.

## 11. Design Acceptance Criteria

This low-altitude expansion design is acceptable when:

- The expansion is limited to `low_altitude_economy_infrastructure`.
- Every driver has required evidence, available evidence, missing evidence, company transmission rule, not-assessable condition, research question, and interpretation guard.
- Current `evidence_pack` fields are separated from future connector needs.
- `000099` is the primary sample.
- Future boundary / negative samples are listed only for later validation and do not expand P1.1 implementation scope.
- Policy pilots are never treated as project revenue.
- Airspace reform is never treated as company-usable airspace without company evidence.
- Local-government spending is never treated as company revenue without contract, acceptance, revenue, and collection evidence.
- Project announcements are never treated as project acceptance.
- Contract liabilities are never treated as backlog.
- Capex is never treated as service-capacity release, utilization, flight-hour growth, or revenue conversion.
- Flight hours, flight sorties, and platform dispatch volume are never written as facts when missing.
- Government / SOE customer type is never treated as collection certainty.
- `company_transmission_path` remains evidence-bound and falls back to `not_assessable` when no company node exists.
- No P1 schema, deterministic pipeline, classifier, connector, scoring, readiness, HTML, or Dashboard change is proposed for this stage.
- No trading advice, target price, position sizing, timing, technical analysis, K-line analysis, or account action is included.
