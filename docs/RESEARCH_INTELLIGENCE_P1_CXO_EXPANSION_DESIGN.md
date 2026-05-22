# Research Intelligence P1.1 CXO Expansion Design Audit

Date: 2026-05-22

Revision: v1.0

Stage: Design audit only. This document adds design guidance only. It must not change code, tests, P1 schema, deterministic pipeline behavior, classifier rules, connectors, scoring, readiness, HTML renderer, Dashboard, generated output, regression fixtures, or existing artifact semantics.

Target expansion: `life_science_cxo_services` only.

Primary sample: `603259` WuXi AppTec / 药明康德, expected `strategy_type=life_science_cxo_services`, expected `sub_type=integrated_cxo_platform`.

Future validation samples: `300759` Pharmaron, `002821` Asymchem, `300347` Tigermed, `300363` Porton Pharma Solutions.

## 1. Expansion Positioning

P1.1 has already accepted the first `ai_datacenter_infrastructure` pilot after multi-sample observation. This document designs the second P1.1 pilot expansion for `life_science_cxo_services`.

The expansion should remain an independent Research Intelligence artifact:

```text
evidence_pack_<code>.json
+ optional P0 research intelligence artifacts
-> research_intelligence_p1_<code>.json
-> research_questions_p1_<code>.json
-> research_questions_p1_<code>.md
```

The expansion should convert CXO macro / industry / company assumptions into evidence-gated driver-factor rows and research questions. It must not become a trading system, valuation model, industry report, dashboard panel, or connector project.

## 2. Non-Negotiable Boundaries

This design is limited to `strategy_type=life_science_cxo_services`.

Do not expand other `strategy_type` values in this stage.

Do not modify:

- P1 schema.
- Deterministic pipeline.
- Classifier routing.
- Data connectors.
- HTML Report.
- Dashboard.
- `status`.
- `confidence`.
- `score` / `fundamental_score`.
- `strategy_type`.
- `sub_type`.

Preserve the P1.1 interpretation guards:

- Contract liabilities are only a partial proxy for prepayments or visibility; they are not backlog.
- Capex is capacity / laboratory / manufacturing investment; it is not capacity release, utilization, order absorption, or revenue realization.
- Policy, Biosecure Act, sanction, and overseas regulation are risk / constraint drivers; they are not operating facts unless company-level evidence shows realized impact.
- Global biotech / pharma R&D demand is background only unless bridged to company customers, orders, project stage, segment revenue, receivables, and cash conversion.
- Customer capex, customer funding, or sector demand is not company revenue.
- R&D ratio is not proof of a technology moat.
- News or theme language is not order evidence.

Safety boundary:

- No trading advice.
- No target price.
- No position sizing.
- No timing or technical analysis.
- No account action.

## 3. Current Evidence-Pack Capability

The current `evidence_pack` can usually support only a conservative P1.1 CXO matrix. For `603259`, current artifacts indicate `strategy_type=life_science_cxo_services` and `sub_type=integrated_cxo_platform`; they also show usable `basic_info`, `business_composition`, `financial_metrics`, valuation context, missing-field lists, must-track indicators, risk flags, data limitations, and source trace summary.

Current `evidence_pack` may have:

- `stock.code`, `stock.name`, `stock.strategy_type`, `stock.sub_type`.
- `stock.status`, `stock.confidence`, `stock.fundamental_score` as read-only context only.
- `basic_info.main_business`, `basic_info.industry`, `basic_info.listing_date`.
- `business_composition[]` with `segment_name`, `classification_type`, `period`, `revenue`, `revenue_ratio`, `gross_margin`, `profit`, and geographic segments where available.
- `financial_metrics.period`, `revenue`, `revenue_yoy`, `gross_margin`, `net_margin`, `net_profit`, `deducted_net_profit`, `operating_cashflow`, `accounts_receivable`, `contract_liabilities`, `inventory`, `capex`, `r_and_d_expense`, `r_and_d_expense_ratio`.
- `valuation_metrics` as explainability context only.
- `confidence_basis.missing_fields`, `confidence_basis.data_coverage`, `confidence_basis.confidence_breakdown`.
- `enhanced_must_track_indicators[]` with `indicator_name`, `current_status`, `source`, `source_date`, `affects_dimension`, `priority`, and follow-up question.
- `risk_flags`, `unknown_or_missing_evidence`, `missing_fields`, `data_limitations`, `source_trace_summary`, `forbidden_terms_check`.

Current `evidence_pack` usually does not reliably have:

- Global biotech funding or pharma R&D outsourcing demand series.
- True backlog / on-hand orders.
- New signed orders.
- Order cancellation or project delay history.
- Structured customer concentration / top customer revenue share.
- U.S.-specific customer exposure.
- Biosecure Act / overseas regulatory event mapping.
- CDMO capacity utilization.
- Commercial-stage project count.
- Clinical project count / project stage.
- Collection cycle as a calculated or disclosed field.
- Capex project mapping, acceptance, utilization, and revenue bridge.
- FX exposure details.
- FDA / EMA / NMPA / GMP inspection event history.
- Longitudinal disclosure consistency.
- Independent multi-source consensus beyond source bucket counting.

## 4. CXO Driver Factor Matrix

Every driver row must use the existing P1.1 driver-factor contract:

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

The matrix below is the required `life_science_cxo_services` pilot design. It is intentionally evidence-pack-only for P1.1 implementation and explicitly identifies future connector needs.

| Driver factor | required_evidence | available_evidence from current evidence_pack | missing_evidence / future connector | company_transmission_path rule | not_assessable condition | research_question |
| --- | --- | --- | --- | --- | --- | --- |
| Global biotech / pharma R&D outsourcing demand | Global biotech funding trend; pharma R&D outsourcing trend; customer budget signal; company customer/order/revenue bridge | `business_composition` can show CXO service exposure; `financial_metrics.revenue`, `gross_margin`, `operating_cashflow`, `accounts_receivable` can test company realization after the fact; `enhanced_must_track_indicators` may mark missing order/customer fields | Future industry demand connector; biotech funding connector; pharma R&D spend connector; customer budget connector | Valid only when the path cites concrete company nodes, for example `evidence_pack.business_composition[...]` plus `financial_metrics.revenue` / `operating_cashflow` / `accounts_receivable`; otherwise use the existing P1 fallback for unverifiable transmission | Mark `not_assessable` when only macro demand is known or current pack lacks customer/order/segment bridge | Has global biotech / pharma R&D outsourcing demand translated into disclosed company customers, orders, service-line revenue, receivables, and cash conversion? |
| Backlog / new signed orders | True backlog or on-hand order disclosure; new signed orders; order period; service line; customer or project stage; revenue recognition path | `missing_fields` may include `life_science_cxo.backlog` and `life_science_cxo.new_signed_orders`; `enhanced_must_track_indicators` may record missing status; `financial_metrics.contract_liabilities` may exist only as partial proxy | Future annual-report note parser; announcement / IR connector; order table extractor | Do not create a concrete path from contract liabilities alone. A valid path needs order/backlog disclosure plus company field/value nodes. | Mark `not_assessable` when true backlog and new signed orders are absent, even if contract liabilities are available | What backlog and new signed order evidence exists by service line, customer type, project stage, and revenue recognition timing? |
| Contract liabilities as partial proxy only | Contract liabilities; prepayment terms; linked customer/order/project disclosure; revenue recognition terms; comparison with revenue and cash flow | `financial_metrics.contract_liabilities` may be available; `financial_metrics.revenue` and `operating_cashflow` may be available | Future financial-note parser; contract / order disclosure connector | A path may cite `financial_metrics.contract_liabilities`, but the interpretation guard must state partial proxy only and must not label it backlog | Mark `not_assessable` for backlog visibility if contract liabilities are the only order-related evidence | What business, customer, or project do contract liabilities correspond to, and what evidence prevents treating them as true backlog? |
| Overseas revenue / U.S. customer exposure | Overseas revenue share; U.S. or North America revenue share; customer geography; major customer region; FX exposure | `business_composition` may include geographic segments such as overseas / domestic; `missing_fields` may include `life_science_cxo.overseas_revenue_share` or `life_science_cxo.north_america_or_us_revenue_share` | Future geographic-revenue parser; top customer note parser; FX note parser | Valid only if geographic segment values or customer-region fields exist in `evidence_pack`; overseas revenue is exposure, not regulatory impact by itself | Mark `not_assessable` for U.S. exposure when only overseas aggregate is present or when geographic fields are absent | How much revenue and customer demand is exposed to overseas and U.S. customers, and what company-level evidence links that exposure to revenue, margin, receivables, or cash conversion? |
| Biosecure Act / overseas regulatory risk | Official policy/regulatory event; affected entity/business line; customer reaction or order impact; compliance or remediation disclosure; revenue/cash bridge | `risk_flags`, `missing_fields`, and `data_limitations` may mark geopolitical/regulatory risk as missing or unquantified | Future official policy connector; overseas regulator event connector; company announcement / risk section parser | Policy risk can enter as risk driver only. It cannot be a company operating fact unless there is company disclosure or financial impact evidence. | Mark `not_assessable` when risk event exists only as external policy/news with no company-specific impact node | What evidence shows whether Biosecure Act or overseas regulatory risk has affected customers, orders, projects, revenue recognition, margin, or cash collection? |
| CDMO capacity utilization | CDMO capacity; utilization rate; commercial-stage project count; capacity expansion status; CDMO revenue; gross margin; capex bridge | `business_composition` may show CMC/CDMO or manufacturing service revenue; `financial_metrics.capex`, `gross_margin`, `revenue`, `operating_cashflow` may be available; `missing_fields` may include `life_science_cxo.cdmo_capacity_utilization` | Future capacity utilization connector; annual-report operation metric parser; project/capacity announcement extractor | Capex and gross margin may be checked, but cannot become utilization path without actual utilization or project-stage evidence | Mark `not_assessable` when actual utilization, capacity, or commercial project stage is missing | Is CDMO capacity being absorbed by commercial projects and utilization, or does current evidence only show capex and revenue without utilization bridge? |
| Clinical project pipeline / project stage | Clinical project count; project stage; project progress/acceptance; cancellation/delay; clinical service revenue; collection status | For `clinical_cro_services`, `business_composition` may show clinical revenue; for integrated platforms, must-track indicators may mark clinical project data missing | Future clinical project database; annual-report project parser; announcement / IR connector | Valid only if project count/stage values are concrete evidence-pack nodes; revenue alone is not project pipeline evidence | Mark `not_assessable` when project count and stage are absent | What clinical project count, stage mix, progress, cancellation/delay, and collection evidence validates clinical CRO service demand? |
| Customer concentration | Top customer revenue share; major customer changes; active customer count; customer type/geography; one-off order marker | `enhanced_must_track_indicators`, `missing_fields`, and `risk_flags` may identify customer concentration missing; `business_composition` is not enough unless it includes customer fields | Future top-five customer parser; customer announcement / IR connector | A valid path needs customer field/value nodes; segment revenue cannot substitute for customer concentration | Mark `not_assessable` when no top customer share, active customer count, or major-customer change evidence exists | Does customer concentration or major-customer change create order, margin, receivable, or one-off revenue risk? |
| Receivables / collection cycle | Accounts receivable; revenue; operating cash flow; collection cycle or DSO; bad-debt/provision data; customer payment terms | `financial_metrics.accounts_receivable`, `revenue`, `operating_cashflow` may be available; period may be available | Future calculated collection-cycle metric; notes on payment terms and credit impairment | A concrete path may cite receivables, revenue, and cash flow; it must frame collection quality as a question, not proof of demand | Mark `not_assessable` for collection cycle if only receivables exists and no DSO/payment-term calculation is available | Are receivables and collection cycle consistent with revenue recognition, or is cash conversion lagging recognized CXO revenue? |
| Capex-to-revenue / utilization bridge | Capex; project/capacity mapping; construction progress; acceptance/start-up; utilization; service-line revenue; cash-flow bridge | `financial_metrics.capex`, `revenue`, `gross_margin`, `operating_cashflow` may be available; `business_composition` may show service-line revenue | Future project/capex announcement extractor; annual-report capex project parser; utilization connector | A valid path can cite capex plus revenue/cash fields, but must state that capex is not capacity release. Utilization/revenue bridge is missing unless explicitly disclosed. | Mark `not_assessable` for capacity release or utilization when only capex is available | Which projects or capacity does capex fund, and has the company disclosed acceptance, utilization, revenue, and operating cash-flow bridges? |
| Margin and cash conversion | Gross margin; net margin; operating cash flow; receivables; contract liabilities; service-line mix; capex/depreciation pressure | `financial_metrics.gross_margin`, `net_margin`, `operating_cashflow`, `accounts_receivable`, `contract_liabilities`, `capex`; `business_composition.gross_margin` may exist by segment | Future segment margin normalization; depreciation and FX note parser; payment term parser | A concrete path may cite margin/cash fields. It must not infer demand recovery without order/customer/project evidence. | Mark `not_assessable` for demand realization if margin/cash fields are not linked to service-line orders or projects | Do margins and operating cash flow support the quality of CXO revenue, or do receivables, capex, or mix changes indicate weaker cash conversion? |
| One-off large order / project volatility | Major customer/product order concentration; one-off order marker; project completion/cancellation; abnormal base-period explanation | `risk_flags`, `missing_fields`, `enhanced_must_track_indicators`; financial growth fields may exist but are not enough | Future major contract parser; customer/project concentration connector; longitudinal history | Growth fields alone cannot create a concrete path. A valid path needs customer/project evidence. | Mark `not_assessable` when there is no single-customer/project evidence and only growth data exists | Is current growth or margin affected by one-off large orders, customer concentration, or project volatility rather than normalized CXO demand? |

## 5. Primary Sample Design: 603259

For `603259`, the P1.1 CXO expansion should use the company as an `integrated_cxo_platform` primary sample.

The current evidence pack appears capable of checking:

- `stock.strategy_type=life_science_cxo_services`.
- `stock.sub_type=integrated_cxo_platform`.
- `basic_info.main_business`.
- `business_composition` by service line / product / geography when present.
- `financial_metrics.revenue`, `gross_margin`, `net_margin`, `operating_cashflow`, `accounts_receivable`, `contract_liabilities`, `inventory`, `capex`, `r_and_d_expense_ratio`.
- missing fields for backlog, new signed orders, customer concentration, overseas / U.S. exposure, CDMO utilization, clinical project count, regulatory risk, and project delay / cancellation.
- source trace buckets for company/business composition and financial statements where available.

Expected sample behavior:

- Some rows may be `partial` because `business_composition` and financial metrics provide company nodes.
- Macro demand, Biosecure Act impact, true backlog, new signed orders, CDMO utilization, clinical project stage, customer concentration, and collection cycle should usually remain `missing` or `not_assessable`.
- Contract liabilities may be included only as a partial proxy row and must not upgrade backlog visibility.
- Capex may be included only as an investment / bridge row and must not imply utilization or capacity release.
- Overseas revenue may be partial if geographic `business_composition` exists; U.S.-specific exposure remains missing unless separately disclosed.

## 6. Future Validation Samples

Use the future samples to test sub-type coverage without expanding beyond `life_science_cxo_services`:

| Sample | Expected sub_type | Validation purpose |
| --- | --- | --- |
| `300759` Pharmaron | `integrated_cxo_platform` | Confirms integrated-platform matrix generalizes beyond `603259`, especially customer, overseas, order, and service-line evidence gaps. |
| `002821` Asymchem | `cdmo_manufacturing_services` | Stress-tests CDMO capacity utilization, commercial project, capex-to-utilization bridge, overseas customer exposure, and margin/cash conversion. |
| `300347` Tigermed | `clinical_cro_services` | Stress-tests clinical project count, project stage, project progress, cancellation/delay, receivables, and collection cycle. |
| `300363` Porton Pharma Solutions | `cdmo_manufacturing_services` | Stress-tests high-volatility CDMO behavior, one-off large order risk, customer concentration, utilization, and capex bridge. |

## 7. Company Transmission Path Constraint

`company_transmission_path` remains an evidence-bound field, not a narrative field.

For the CXO expansion:

- A valid path must cite concrete current `evidence_pack` field/value nodes.
- Valid nodes include `evidence_pack.business_composition[...]`, `evidence_pack.financial_metrics.revenue`, `evidence_pack.financial_metrics.gross_margin`, `evidence_pack.financial_metrics.operating_cashflow`, `evidence_pack.financial_metrics.accounts_receivable`, `evidence_pack.financial_metrics.contract_liabilities`, `evidence_pack.financial_metrics.capex`, and relevant `enhanced_must_track_indicators[...]` statuses.
- Macro, industry, policy, regulatory, or demand language is not a company transmission path by itself.
- If no concrete company node exists, the path must use the existing P1.1 `TRANSMISSION_PATH_FALLBACK` value, represented conceptually as "传导路径无法从当前证据包验证".
- Any row using the fallback must set `confidence_cap=not_assessable`.
- A non-fallback path must not use `confidence_cap=not_assessable`.

Valid path shape:

```text
evidence_pack.business_composition[0]=segment_name: CXO/CDMO service; revenue_ratio: ...
-> evidence_pack.financial_metrics.revenue=...
-> evidence_pack.financial_metrics.operating_cashflow=...
-> missing_evidence: backlog / new signed orders / customer concentration
```

Invalid path shape:

```text
Global pharma R&D demand improves, so the company benefits.
Biosecure Act risk exists, so company orders are affected.
Capex increased, so CDMO capacity has been released.
Contract liabilities increased, so backlog is strong.
```

## 8. Not-Assessable Rules

Use `not_assessable` when evidence cannot complete the driver chain:

```text
driver signal
-> company evidence node
-> financial / operating bridge
-> missing evidence or research question
```

Specific CXO rules:

- If global biotech / pharma R&D outsourcing demand lacks company order, customer, project, revenue, or cash bridge, mark company transmission `not_assessable`.
- If true backlog and new signed orders are absent, do not assess order visibility as strong; contract liabilities alone cannot prevent `not_assessable` for backlog.
- If only contract liabilities are available, the row can be `partial` for contract-liability observation but `not_assessable` for true backlog.
- If overseas revenue exists but U.S. exposure is absent, U.S. customer risk remains `missing` or `not_assessable`.
- If Biosecure Act / overseas regulatory risk lacks company-specific impact evidence, treat it as risk context only and mark impact `not_assessable`.
- If CDMO capacity utilization is missing, do not infer utilization from capex, revenue growth, or gross margin.
- If clinical project count or stage is missing, do not assess clinical CRO project pipeline quality.
- If customer concentration is missing, do not infer customer stability from revenue or segment mix.
- If receivables exist but DSO/payment terms are absent, collection cycle is `missing` or `not_assessable`.
- If capex exists without project, acceptance, utilization, revenue, and cash-flow bridge, capacity release is `not_assessable`.
- If margin/cash metrics exist but no order/customer/project bridge exists, demand realization remains `not_assessable`.
- If fewer than two independent source buckets are available, consensus / divergence / contradiction remains `not_assessable`.

## 9. Future Data Needs

P1.1 CXO implementation should not add these connectors, but the document should tag them as future needs:

- Global biotech funding and pharma R&D outsourcing demand connector.
- Annual-report note parser for backlog, new signed orders, customer concentration, geographic revenue, U.S. / North America exposure, payment terms, FX, and risk sections.
- Exchange announcement connector for major orders, project delay/cancellation, capacity projects, and compliance events.
- Company IR / earnings-call connector for order trend, project stage, customer mix, and utilization commentary.
- CDMO capacity utilization and commercial project parser.
- Clinical project pipeline / project-stage connector.
- FDA / EMA / NMPA / GMP compliance event connector.
- Biosecure Act / overseas policy and official regulatory event connector.
- Customer / top-five customer parser and major-customer change tracker.
- Collection-cycle calculation layer using receivables, revenue, period length, and payment terms.
- Capex project mapping, acceptance, utilization, and revenue-bridge extractor.
- Longitudinal disclosure store for prior periods and prior P0/P1 outputs.

## 10. Implementation Recommendation

Recommendation: enter P1.1 CXO implementation after this design is accepted.

Minimum implementation should:

- Add a `life_science_cxo_services` driver template inside the existing P1.1 builder boundary.
- Reuse the existing P1 schema without adding fields.
- Keep the current independent P1 artifact relationship.
- Read only current `evidence_pack` and optional P0 artifacts.
- Preserve existing `company_transmission_path` schema enforcement.
- Preserve source-bucket independent counting.
- Preserve the exact P1.1 safety boundary.
- Use `603259` as the primary implementation sample.
- Use `300759`, `002821`, `300347`, and `300363` only as future validation samples after the primary sample passes manual review.

Do not implement in this phase:

- New data connectors.
- HTML / Dashboard sections.
- P1 schema changes.
- Deterministic status/confidence/score changes.
- New strategy types.
- Live web search.
- Automated industry forecasts.
- Automated policy impact conclusions.

## 11. Design Acceptance Criteria

This CXO expansion design is acceptable when:

- The expansion is limited to `life_science_cxo_services`.
- Every driver has required evidence, available evidence, missing evidence, company transmission rule, not-assessable rule, and research question.
- Current `evidence_pack` fields are separated from future connector needs.
- `603259` is the primary sample.
- `300759`, `002821`, `300347`, and `300363` are future validation samples.
- Contract liabilities are never treated as backlog.
- Capex is never treated as capacity release.
- Biosecure Act / overseas regulatory risk is never treated as operating fact without company-specific evidence.
- `company_transmission_path` remains evidence-bound and falls back to not-assessable when no company node exists.
- No P1 schema, deterministic pipeline, connector, HTML, or Dashboard change is proposed for this stage.
- No trading advice, target price, position sizing, timing, or technical analysis is included.
