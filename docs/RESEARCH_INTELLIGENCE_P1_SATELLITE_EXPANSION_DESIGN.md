# Research Intelligence P1.1 Satellite Expansion Design Audit

Date: 2026-05-22

Revision: v1.0

Stage: Design audit only. This document adds design guidance only. It must not change code, tests, P1 schema, deterministic pipeline behavior, classifier rules, connectors, scoring, readiness, HTML renderer, Dashboard, generated output, regression fixtures, or existing artifact semantics.

Target expansion: `satellite_communication_infrastructure` only.

Primary sample: `601698` China Satcom / 中国卫通, expected `strategy_type=satellite_communication_infrastructure`.

Future validation samples: `600118`, `002465`, `688066`, and `002895` may be retained as negative / boundary validation candidates, but P1.1 implementation should first use only `601698` as the primary sample.

## 1. Expansion Positioning

P1.1 has already accepted the first `ai_datacenter_infrastructure` pilot and the `life_science_cxo_services` expansion design after multi-sample observation. This document designs the next narrow P1.1 expansion for `satellite_communication_infrastructure`.

The expansion remains an independent Research Intelligence artifact:

```text
evidence_pack_<code>.json
+ optional P0 research intelligence artifacts
-> research_intelligence_p1_<code>.json
-> research_questions_p1_<code>.json
-> research_questions_p1_<code>.md
```

The expansion should convert satellite communication infrastructure assumptions into evidence-gated driver-factor rows and research questions. It must not become a trading system, valuation model, industry report, policy report, dashboard panel, connector project, technical-analysis layer, or deterministic scoring input.

## 2. Non-Negotiable Boundaries

This design is limited to `strategy_type=satellite_communication_infrastructure`.

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

- Policy support is not business realization.
- Satellite communication demand is not company demand unless bridged to company-level customers, capacity utilization, contracts, revenue, margin, receivables, and cash flow.
- Bandwidth / transponder capacity is not utilization or revenue.
- Capex is not successful asset deployment, capacity release, or revenue conversion.
- Missing customer contracts means revenue stability cannot be written as fact.
- Contract liabilities are at most a partial proxy for prepayments or visibility; they are not true backlog.
- Business composition can identify exposure, but cannot prove utilization, customer renewal, pricing power, or remaining satellite life.
- Financial metrics can test baseline operating quality, but cannot prove satellite resource monetization without operating evidence.

## 3. Current Evidence-Pack Capability

For `601698`, current fixtures and framework documents indicate that the evidence pack can usually support only a conservative P1.1 satellite matrix.

Current `evidence_pack` may have:

- `stock.code`, `stock.name`, `stock.strategy_type`, `stock.sub_type`.
- `stock.status`, `stock.confidence`, `stock.fundamental_score` as read-only context only.
- `basic_info.industry`.
- `basic_info.main_business`.
- `business_composition[]` with segment name, classification type, period, revenue ratio, revenue, gross margin, and profit when present.
- `financial_metrics.period`, `revenue`, `revenue_yoy`, `gross_margin`, `net_margin`, `net_profit`, `deducted_net_profit`, `operating_cashflow`, `accounts_receivable`, `contract_liabilities`, `capex`, and depreciation / amortization only when exposed by existing fields.
- `valuation_metrics` as explainability context only; no target price or trading framing.
- `confidence_basis.missing_fields`, `confidence_basis.data_coverage`, and `confidence_basis.confidence_breakdown`.
- `enhanced_must_track_indicators[]`.
- `risk_flags`, `unknown_or_missing_evidence`, `missing_fields`, `data_limitations`, `source_trace_summary`, and `forbidden_terms_check`.

Current `evidence_pack` usually does not reliably have:

- Satellite communication demand time series.
- National satellite communication infrastructure policy event mapping.
- Bandwidth / transponder market demand.
- Enterprise / broadcast / emergency customer demand by company.
- In-orbit satellite resource table.
- Orbital slot / frequency resource table.
- Transponder count, bandwidth capacity, or capacity by band.
- Capacity utilization / lease rate.
- Customer contract duration.
- Lease / service pricing.
- Customer concentration / top customer revenue share.
- Satellite remaining useful life.
- Replacement capex by satellite.
- Launch schedule, launch failure, in-orbit failure, insurance claim, impairment, or replacement event history.
- Longitudinal disclosure consistency.
- Independent multi-source consensus beyond source-bucket counting.

## 4. Driver Factor Matrix Contract

Every satellite driver row must use the existing P1.1 driver-factor contract:

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

For this expansion, every driver must include:

- `required_evidence`
- `available_evidence`
- `missing_evidence`
- `company_transmission_path rule`
- `not_assessable condition`
- `research_question`
- `interpretation_guard`

The matrix is evidence-pack-only for P1.1 implementation. Future connector needs are recorded as missing evidence, not implemented in this phase.

## 5. Satellite Driver Factor Matrix

### 5.1 Macro / Policy / Industry Drivers

| Driver factor | required_evidence | available_evidence from current evidence_pack | missing_evidence / future connector | company_transmission_path rule | not_assessable condition | research_question | interpretation_guard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Satellite communication demand | Satellite communication demand series; demand by application; company customer/order/revenue bridge; capacity utilization bridge | `basic_info.main_business`; `business_composition` may show satellite transmission service exposure; `financial_metrics.revenue`, `gross_margin`, `operating_cashflow`, `accounts_receivable` can test company realization after the fact | Future industry demand connector; application demand connector; customer / order disclosure parser; utilization connector | Valid only when the path cites concrete company nodes such as `evidence_pack.business_composition[...]` plus financial fields. If demand has no company node, use `传导路径无法从当前证据包验证`. | Mark `not_assessable` when only industry demand is available or when company customer/order/utilization bridge is missing. | Has satellite communication demand translated into disclosed company customers, contracts, capacity utilization, revenue, receivables, and operating cash flow? | Do not write "satellite communication demand is improving, therefore the company benefits." Demand is background until company transmission is evidenced. |
| National satellite communication infrastructure policy | Official policy; affected infrastructure segment; implementation timeline; company qualification / license / project / contract evidence; revenue or cash bridge | `risk_flags`, `enhanced_must_track_indicators`, or `supporting_evidence` may mention policy context if present; company `basic_info` may show licensed operating profile | Future official policy connector; company announcement parser; license / qualification parser; policy project tracker | Policy can only be a driver context unless the path cites company-level policy project, license, contract, or revenue nodes in `evidence_pack`. Otherwise use fallback. | Mark `not_assessable` when policy exists without company-specific project, customer, or financial impact evidence. | Which national satellite communication infrastructure policies are linked to company-specific licenses, projects, contracts, revenue recognition, or cash collection? | Policy support is not business realization or revenue. |
| Bandwidth / transponder capacity demand | Market bandwidth demand; transponder demand; capacity shortage or oversupply evidence; company transponder / bandwidth resources; utilization and pricing | `business_composition` can show revenue exposure; financial metrics can show gross margin / revenue but not capacity demand | Future capacity-demand connector; transponder market data; company capacity disclosure parser | Valid only if concrete company capacity and utilization/pricing nodes exist. Revenue exposure alone cannot prove capacity demand. If absent, use fallback. | Mark `not_assessable` when capacity demand is external only or company capacity / utilization / pricing data is absent. | Is external bandwidth / transponder demand visible in company capacity utilization, service pricing, contract renewals, revenue, margin, and cash flow? | Do not treat capacity resources as utilization or income. |
| Enterprise / broadcast / emergency communication demand | Customer segment demand; broadcast, enterprise, emergency, maritime, aviation, or government demand; customer contract evidence; collection quality | `business_composition.segment_name` may identify broadcast / satellite transmission service; financial metrics may show revenue and cash flow | Future customer-segment parser; top customer parser; emergency communication project connector; contract duration connector | Valid only if customer segment, contract, revenue, and cash-flow nodes exist in the evidence pack. Segment label alone is not enough for demand stability. | Mark `not_assessable` when customer type, contract duration, or renewal evidence is missing. | Which customer segments support the company's satellite communication revenue, and are contract duration, renewal, pricing, receivables, and cash collection evidenced? | Do not infer stable demand from customer category labels without contract and renewal evidence. |

### 5.2 Company / Asset Drivers

| Driver factor | required_evidence | available_evidence from current evidence_pack | missing_evidence / future connector | company_transmission_path rule | not_assessable condition | research_question | interpretation_guard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Satellite resources | In-orbit satellite list; ownership / control; orbital slot / frequency resources; service scope; capacity mapped to revenue | `basic_info.main_business` may mention satellite space-segment operation; `business_composition` may show satellite transmission services | Future annual-report resource parser; official license / orbital resource parser; company technical disclosure parser | A concrete path needs resource field/value nodes plus business or financial nodes. Main-business text alone can support exposure but not resource sufficiency. | Mark `not_assessable` when satellite count, resource rights, orbital/frequency details, or service capacity are absent. | What satellite resources and regulatory rights does the company control, and how are they linked to service revenue and operating cash flow? | Do not equate a satellite-operator description with sufficient or productive satellite resources. |
| Transponder / bandwidth resources | Transponder count; bandwidth capacity; capacity by band; available vs leased capacity; service region | `business_composition` and revenue may show monetized satellite transmission service exposure | Future transponder / bandwidth capacity parser; band-specific capacity disclosure; resource database | Valid only when transponder or bandwidth field/value nodes exist. If only revenue or business composition exists, use fallback for capacity claims. | Mark `not_assessable` when transponder count, bandwidth capacity, or available/leased split is missing. | What transponder and bandwidth resources are available, and which part is monetized by disclosed contracts or service revenue? | Capacity resources are not utilization, pricing, or revenue by themselves. |
| Capacity utilization | Capacity utilization rate; lease rate; bandwidth sold vs available; utilization by satellite / band; revenue and margin bridge | Usually missing; financial metrics may only show revenue and gross margin | Future utilization connector; annual report operating metric parser; IR / management commentary parser | Valid only if utilization values exist as evidence nodes. Revenue, gross margin, or capex cannot substitute for utilization. | Mark `not_assessable` when utilization / lease-rate evidence is absent. | Are satellite resources being used at disclosed utilization levels, and how does utilization connect to revenue, margin, receivables, and cash flow? | Do not infer high utilization from revenue level, segment share, or capacity ownership. |
| Customer contract duration | Contract start/end dates; average contract duration; renewal terms; customer type; revenue recognition schedule | `financial_metrics.contract_liabilities` may exist only as partial proxy; segment revenue may exist | Future contract parser; top customer notes; announcement / IR connector | A path may cite contract liabilities as a partial observation, but it cannot claim duration or renewal without contract terms. | Mark `not_assessable` when contract duration, renewal terms, and customer-level contract evidence are absent. | What are the contract durations and renewal terms for satellite communication customers, and how do they support or weaken revenue visibility? | Missing customer contracts means revenue stability cannot be written as fact. |
| Lease / service pricing | Unit bandwidth price; transponder lease price; service pricing formula; price changes; customer mix; gross margin bridge | `financial_metrics.gross_margin`; `business_composition.gross_margin` when present | Future price disclosure parser; contract-price extractor; industry price connector | Gross margin can be cited as financial observation, but cannot be converted into pricing power without lease/service price evidence. | Mark `not_assessable` when unit pricing or contract pricing is missing. | What evidence shows lease or service pricing by capacity type, and is pricing pressure visible in gross margin or customer mix? | Do not infer pricing power from gross margin alone. |
| Customer concentration | Top customer revenue share; customer count; customer type; contract concentration; government / broadcast / enterprise mix; receivable concentration | `risk_flags`, `missing_fields`, or must-track indicators may identify missing customer concentration; financial receivables may be available | Future top-five customer parser; customer contract / announcement connector; receivable concentration parser | A valid path needs customer field/value nodes. Segment revenue or industry labels cannot substitute for customer concentration. | Mark `not_assessable` when top customer share, active customer count, or customer concentration evidence is absent. | Does customer concentration create renewal, pricing, receivable, or one-off revenue risk? | Do not claim demand stability or diversified customers without customer evidence. |

### 5.3 Financial Drivers

| Driver factor | required_evidence | available_evidence from current evidence_pack | missing_evidence / future connector | company_transmission_path rule | not_assessable condition | research_question | interpretation_guard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Revenue stability | Revenue by period; segment revenue; customer contract duration; renewal rate; customer concentration; utilization bridge | `financial_metrics.revenue`; `business_composition` revenue ratio / revenue when present | Future contract duration parser; renewal tracker; customer concentration parser; utilization connector | A path may cite revenue and segment fields, but must state missing contract / renewal bridge. It cannot assert stability without customer contract evidence. | Mark `not_assessable` for revenue stability when contract duration, renewal, and customer concentration are missing. | Is revenue stability supported by contract duration, renewal evidence, utilization, customer concentration, and cash collection, or only by historical revenue fields? | Do not write revenue stability as fact when customer contracts are missing. |
| Gross margin stability | Gross margin by period; segment gross margin; pricing; capacity utilization; depreciation policy; customer mix | `financial_metrics.gross_margin`; `business_composition.gross_margin` when present | Future segment margin history; pricing connector; utilization connector; depreciation note parser | A concrete path may cite margin fields, but margin stability needs period comparison and operating bridge. | Mark `not_assessable` when only one-period margin or no pricing/utilization bridge exists. | Is gross margin stability explained by pricing, utilization, customer mix, and depreciation, or is current evidence only a financial snapshot? | Do not infer pricing power or stable utilization from gross margin alone. |
| Capex | Capex amount; project / satellite mapping; procurement / launch progress; acceptance or in-orbit status; revenue and cash-flow bridge | `financial_metrics.capex` may be available | Future capex project parser; satellite procurement / launch announcement tracker; construction-in-progress notes | A path may cite capex as cash outflow only. It must not claim successful asset deployment without project, launch, in-orbit, utilization, and revenue evidence. | Mark `not_assessable` for capacity release or asset deployment when only capex is available. | Which satellites, projects, or assets does capex fund, and has the company disclosed launch, in-orbit status, utilization, revenue, and cash-flow bridges? | Capex is not asset deployment success, capacity release, utilization, or revenue. |
| Depreciation | Depreciation / amortization amount; satellite asset depreciation policy; satellite useful life; impairment; segment asset detail | May be missing or only company-level if current fields expose depreciation / amortization | Future financial-note parser; fixed-asset note parser; depreciation policy extractor | Valid only if depreciation or amortization field/value nodes exist. Profitability comparison cannot ignore missing depreciation and useful-life policy. | Mark `not_assessable` when depreciation, asset life, or segment asset detail is absent. | How do depreciation policy and satellite useful life affect reported profit and margin quality? | Do not compare profitability without checking asset life and depreciation policy. |
| Operating cash flow | Operating cash flow; revenue; receivables; contract liabilities; customer payment terms; collection history | `financial_metrics.operating_cashflow`, `revenue`, `accounts_receivable`, `contract_liabilities` may be available | Future payment-term parser; cash conversion calculation; customer receivable concentration | A concrete path may cite cash flow, revenue, receivables, and contract liabilities as financial nodes, but must frame cash conversion as a question if payment terms are missing. | Mark `not_assessable` for customer payment quality if payment terms or receivable concentration are absent. | Does operating cash flow support revenue quality after considering receivables, contract liabilities, customer payment terms, and capex needs? | Cash flow quality is a validation question, not proof of stable demand. |
| Receivables | Accounts receivable; revenue; customer concentration; aging; bad-debt provision; payment terms; operating cash flow | `financial_metrics.accounts_receivable`, `revenue`, `operating_cashflow` may be available | Future receivable aging / bad-debt note parser; customer receivable concentration; payment-term parser | A concrete path may cite receivables, revenue, and cash flow. It cannot assert customer quality without aging and customer concentration. | Mark `not_assessable` for collection risk when aging, payment terms, and customer concentration are absent. | Are receivables consistent with the satellite communication revenue model, or do aging, concentration, and payment terms indicate collection risk? | Do not use customer type or long-cycle business to assume collection quality. |
| Satellite remaining life / replacement capex | Remaining useful life by satellite; design life; launch date; replacement schedule; sustaining capex; depreciation and impairment | Usually missing; capex and depreciation may be partial financial observations if present | Future satellite asset life parser; launch history connector; replacement capex tracker; impairment / insurance event parser | Valid only when remaining life or replacement schedule appears as concrete evidence. Capex cannot substitute for remaining life. | Mark `not_assessable` when satellite life, launch dates, or replacement capex schedules are missing. | What is the remaining useful life of operating satellites, and what replacement capex is required to maintain service capacity? | Do not ignore asset aging risk when remaining life is missing. |

### 5.4 Risk Drivers

| Driver factor | required_evidence | available_evidence from current evidence_pack | missing_evidence / future connector | company_transmission_path rule | not_assessable condition | research_question | interpretation_guard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Satellite failure / launch / replacement risk | Launch schedule; launch success/failure; in-orbit anomaly; insurance claim; impairment; replacement plan; service impact | `risk_flags` or `enhanced_must_track_indicators` may mention missing event data; financial impairment fields usually absent | Future launch / anomaly / insurance event connector; exchange announcement parser; impairment note parser | Valid only when event or replacement field/value nodes exist. Normal revenue cannot prove absence of failure risk. | Mark `not_assessable` when no launch, failure, insurance, impairment, or replacement event evidence exists. | Are there satellite launch, in-orbit failure, insurance, impairment, or replacement events that affect capacity, service continuity, capex, or cash flow? | Do not use ordinary operating data to cover missing satellite-event risk. |
| Remaining useful life risk | Launch date; design life; remaining life; depreciation policy; replacement timeline; service dependency by satellite | Usually missing; depreciation may be partial if available | Future satellite technical disclosure parser; fixed-asset note parser; launch history connector | Valid only if remaining-life or design-life field/value nodes exist. | Mark `not_assessable` when remaining useful life and design life are absent. | Which satellites are approaching end of life, and what evidence links remaining life to revenue continuity and replacement capex? | Remaining life is a key risk; do not infer it from company age or capex. |
| Capacity utilization risk | Available capacity; leased capacity; utilization rate; customer cancellations; price changes; revenue and margin bridge | Revenue and gross margin may be available; utilization usually missing | Future utilization connector; customer contract renewal tracker; capacity disclosure parser | Utilization risk cannot be assessed from capacity ownership or revenue alone. Use fallback unless utilization values exist. | Mark `not_assessable` when utilization / lease-rate evidence is missing. | Does unused capacity, lower lease rate, or customer churn create revenue and margin risk? | Do not convert capacity resources into utilization or revenue. |
| Customer renewal risk | Contract duration; expiry schedule; renewal rate; customer concentration; customer type; receivable quality | Contract liabilities and revenue may be partial financial observations if present | Future contract duration / expiry parser; top-customer parser; renewal announcement tracker | Valid only if contract terms or renewal field/value nodes exist. Revenue alone cannot prove renewal quality. | Mark `not_assessable` when contract expiry, renewal rate, and customer concentration are absent. | What contract expiries or renewal dependencies could affect revenue visibility and cash collection? | Missing contract duration prevents factual claims about renewal stability. |
| Technology substitution risk | LEO / HTS / terrestrial fiber / 5G / alternative transmission substitutes; affected service lines; pricing or utilization evidence; company response | `risk_flags` may contain theme or technology risks if present; current pack usually lacks structured substitution data | Future technology / competitor event connector; policy and industry connector; company disclosure parser | Technology risk is context unless evidence pack contains company service-line exposure, pricing, utilization, or customer impact nodes. | Mark `not_assessable` when substitution is only external context without company impact evidence. | Which services face substitution from LEO, high-throughput satellites, terrestrial networks, or other technologies, and is impact visible in pricing, utilization, revenue, or margin? | Do not treat technology narratives as realized business impact without company bridge. |
| Policy / regulatory risk | License conditions; frequency / orbital resource regulation; national security constraints; policy changes; company compliance evidence; service impact | `basic_info.industry` may show regulated industry; risk flags may mention policy risk | Future license / regulatory event connector; official policy connector; company compliance disclosure parser | Valid only if regulatory event, license condition, or company compliance field/value nodes exist. Industry regulation alone is background. | Mark `not_assessable` when no company-specific policy / regulatory impact evidence exists. | What policy, license, frequency, orbital-slot, or regulatory conditions could affect company service continuity, pricing, capex, or customer contracts? | Policy and regulation are constraints, not automatic support or business realization. |

## 6. Primary Sample Design: 601698

For `601698`, the P1.1 satellite expansion should use the company as the primary sample for a satellite-resource-driven communication infrastructure operator.

The current evidence pack appears capable of checking:

- `stock.strategy_type=satellite_communication_infrastructure`.
- `basic_info.industry`.
- `basic_info.main_business`.
- `business_composition` indicating satellite / broadcast / transmission service exposure when present.
- `financial_metrics.revenue`, `gross_margin`, `operating_cashflow`, `accounts_receivable`, `contract_liabilities`, and `capex`.
- missing fields or must-track indicators for capacity utilization, customer structure, satellite life, depreciation, transponder / bandwidth resources, contract duration, and launch / failure events when present.
- source trace buckets for business composition and financial statements where available.

Expected sample behavior:

- Rows tied to `basic_info`, `business_composition`, revenue, gross margin, operating cash flow, receivables, contract liabilities, or capex may be `partial` only when concrete `evidence_pack` field/value nodes are cited.
- Satellite communication demand, policy support, bandwidth / transponder demand, customer demand, utilization, contract duration, lease pricing, customer concentration, remaining life, replacement capex, and launch / failure events should usually remain `missing` or `not_assessable`.
- Capex may be included only as cash outflow / investment observation and must not imply asset deployment success, launch success, utilization, or revenue conversion.
- Capacity resources, if disclosed, may identify the asset base, but must not be treated as utilization or income.
- Customer contracts, renewals, and concentration must not be inferred from revenue or customer category labels.

## 7. Company Transmission Path Constraint

`company_transmission_path` remains an evidence-bound field, not a narrative field.

For the satellite expansion:

- A valid path must cite concrete current `evidence_pack` field/value nodes.
- Valid nodes may include `evidence_pack.basic_info.main_business`, `evidence_pack.basic_info.industry`, `evidence_pack.business_composition[...]`, `evidence_pack.financial_metrics.revenue`, `evidence_pack.financial_metrics.gross_margin`, `evidence_pack.financial_metrics.operating_cashflow`, `evidence_pack.financial_metrics.accounts_receivable`, `evidence_pack.financial_metrics.contract_liabilities`, `evidence_pack.financial_metrics.capex`, and relevant `enhanced_must_track_indicators[...]` statuses.
- Macro, industry, policy, technology, demand, or customer-category language is not a company transmission path by itself.
- If no concrete company node exists, the path must use the exact P1.1 `TRANSMISSION_PATH_FALLBACK` value: `传导路径无法从当前证据包验证`.
- Any row using the fallback must set `confidence_cap=not_assessable`.
- A non-fallback path must not use `confidence_cap=not_assessable`.

Valid path shape:

```text
evidence_pack.business_composition[0]=segment_name: satellite transmission service; revenue_ratio: ...
-> evidence_pack.financial_metrics.revenue=...
-> evidence_pack.financial_metrics.operating_cashflow=...
-> missing_evidence: transponder capacity / utilization / customer contract duration / customer concentration
```

Invalid path shape:

```text
Satellite communication demand improves, so the company benefits.
Policy supports satellite infrastructure, so company revenue will be realized.
The company owns satellite resources, so utilization is high.
Capex increased, so satellite capacity has been successfully deployed.
Long-cycle customers imply revenue stability.
```

## 8. Not-Assessable / Missing Evidence Rules

Use `not_assessable` when evidence cannot complete the driver chain:

```text
driver signal
-> concrete company evidence node
-> operating / financial bridge
-> missing evidence or research question
```

Specific satellite rules:

- If no evidence-pack field or data point can verify the company transmission path, `company_transmission_path` must be exactly `传导路径无法从当前证据包验证`.
- Any row using that fallback must set `confidence_cap=not_assessable`.
- If satellite communication demand lacks company customer, contract, utilization, revenue, receivables, and cash-flow bridge, mark company transmission `not_assessable`.
- If national policy lacks company-specific project, license, contract, or financial impact evidence, treat it as policy context only and mark realization `not_assessable`.
- If bandwidth / transponder demand lacks company capacity and utilization / pricing bridge, mark `not_assessable`.
- If satellite resources exist but utilization, contract, pricing, or revenue bridge is absent, do not assess monetization quality.
- If transponder / bandwidth resources are missing, do not infer capacity base from revenue.
- If capacity utilization is missing, do not infer utilization from revenue, gross margin, business composition, or capex.
- If customer contract duration is missing, do not write revenue stability or renewal visibility as fact.
- If lease / service pricing is missing, do not infer pricing power from gross margin alone.
- If customer concentration is missing, do not infer customer stability or diversification from segment revenue.
- If capex exists without project, launch, in-orbit status, utilization, revenue, and cash-flow bridge, capacity release and asset deployment success are `not_assessable`.
- If depreciation, satellite useful life, or asset-life policy is missing, do not make profitability comparisons that depend on asset life.
- If satellite remaining life or replacement capex is missing, mark asset-aging and replacement-cycle assessment `not_assessable`.
- If launch, failure, insurance, impairment, or replacement events are absent from evidence, do not assert absence of event risk.
- If fewer than two independent source buckets are available, consensus / divergence / contradiction remains `not_assessable`.

## 9. Future Data Needs

P1.1 satellite implementation should not add connectors, but the document should tag these as future needs:

- Satellite communication demand connector by application segment.
- National satellite communication infrastructure policy connector.
- Official license / orbital slot / frequency resource parser.
- Annual-report note parser for satellite resources, transponder / bandwidth capacity, depreciation, useful life, impairment, and customer concentration.
- Transponder / bandwidth resource and capacity disclosure parser.
- Capacity utilization / lease-rate connector.
- Contract duration, renewal, and expiry parser.
- Lease / service pricing extractor.
- Customer segment and top-five customer parser.
- Receivable aging, bad-debt provision, and customer receivable concentration parser.
- Satellite launch history, in-orbit anomaly, failure, insurance claim, and replacement event connector.
- Replacement capex tracker by satellite or project.
- Technology substitution monitor for LEO, high-throughput satellites, terrestrial fiber, 5G / 6G, and other transmission alternatives.
- Longitudinal disclosure store for prior periods and prior P0/P1 outputs.

## 10. Implementation Recommendation

Recommendation: enter P1.1 Satellite implementation after this design is accepted.

Minimum implementation should:

- Add a `satellite_communication_infrastructure` driver template inside the existing P1.1 builder boundary.
- Reuse the existing P1 schema without adding fields.
- Keep the current independent P1 artifact relationship.
- Read only current `evidence_pack` and optional P0 artifacts.
- Preserve existing `company_transmission_path` schema enforcement.
- Preserve source-bucket independent counting.
- Preserve the exact P1.1 safety boundary.
- Use `601698` as the only primary implementation sample.
- Use future validation samples only after the primary sample passes manual review.

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

This satellite expansion design is acceptable when:

- The expansion is limited to `satellite_communication_infrastructure`.
- Every driver has required evidence, available evidence, missing evidence, company transmission rule, not-assessable condition, research question, and interpretation guard.
- Current `evidence_pack` fields are separated from future connector needs.
- `601698` is the primary sample.
- Future validation samples are listed only for later validation and do not expand P1.1 implementation scope.
- Policy support is never treated as business realization.
- Satellite communication demand is never treated as company demand without company evidence.
- Capacity resources are never treated as utilization or revenue.
- Capex is never treated as asset deployment success, capacity release, utilization, or revenue conversion.
- Customer contract absence prevents factual revenue-stability claims.
- `company_transmission_path` remains evidence-bound and falls back to `not_assessable` when no company node exists.
- No P1 schema, deterministic pipeline, classifier, connector, scoring, readiness, HTML, or Dashboard change is proposed for this stage.
- No trading advice, target price, position sizing, timing, technical analysis, K-line analysis, or account action is included.
