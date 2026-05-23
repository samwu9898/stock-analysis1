# Research Intelligence P1 Design Audit

Date: 2026-05-22

Revision: v1.1

Stage: Design audit only. This document adds design guidance only. It must not change code, tests, pipeline behavior, classifier rules, connectors, scoring, readiness, HTML renderer, Dashboard, generated output, regression fixtures, or existing artifact semantics.

Implementation status: P1.1 AI Datacenter pilot, CXO expansion, and Satellite expansion have been implemented and accepted after this v1.1 design. Current P1.1 support is limited to `ai_datacenter_infrastructure`, `life_science_cxo_services`, and `satellite_communication_infrastructure`; it outputs independent `research_intelligence_p1_<code>.json`, `research_questions_p1_<code>.json`, and `research_questions_p1_<code>.md` artifacts. AI Datacenter acceptance covered `002837` and `300442`; Satellite primary acceptance covered `601698`. Latest recorded pytest result is `423 passed`, and latest recorded regression suite result is `passed=47 failed=0 total=47`.

## 1. P1 Positioning

Research Intelligence P1 is the next independent research-intelligence layer above the accepted P0 / P0.1 / P0.2 baseline.

P0 has already established:

- independent `research_intelligence_<code>.json`, `research_questions_<code>.json`, and Markdown research-question artifacts;
- evidence-pack-only reading for the implemented baseline;
- strategy-type-aware driver maps, cross-validation, rule-triggered contradictions, and research questions;
- proxy guards for contract liabilities, capex, R&D ratio, policy / theme language, certification / POC, and customer capex;
- no mutation of `status`, `confidence`, `score`, `strategy_type`, or `sub_type`;
- no HTML / Dashboard integration in the Research Intelligence chain.

P1 should extend the research-question intelligence from company-only validation into:

```text
macro / policy / cycle driver factors
+ industry driver factors
+ multi-source consistency diagnostics
+ disclosure consistency
+ project / capex tracking
+ business-financial-risk linkage
-> independent P1 research intelligence artifact
-> independent P1 research question artifact
```

P1 is not a full macro report, not an industry report, not a valuation model, and not a trading system. It is a structured evidence-gap and research-question generator.

## 2. Non-Negotiable Boundaries

P1 must preserve the current Research Intelligence safety and architecture boundary:

- Do not modify `status`.
- Do not modify `confidence`.
- Do not modify `fundamental_score` / `score`.
- Do not modify `strategy_type`.
- Do not modify `sub_type`.
- Do not modify deterministic pipeline behavior.
- Do not modify classifier, connector, scoring, readiness, result assembler, HTML renderer, Dashboard, or output artifacts.
- Do not feed P1 back into deterministic conclusions.
- Do not integrate P1 into HTML Report v2.2 or Dashboard in P1; that is P2.
- Do not call live web / network sources in the minimum P1 implementation unless a future connector phase explicitly adds them.
- Do not treat policy, news, or theme heat as realized business.
- Do not treat capex as capacity release.
- Do not treat contract liabilities as backlog.
- Do not treat customer capex as company revenue certainty.
- Do not treat R&D ratio as technology moat proof.
- Do not make macro forecasts.
- Do not make broad industry summaries without evidence mapping.
- Do not output trading advice, target prices, position sizing, technical analysis, execution instructions, or account actions.

P1 may use stronger language only for evidence mechanics, such as:

- "not_assessable";
- "available evidence is insufficient";
- "missing bridge";
- "requires disclosure verification";
- "requires project-level tracking";
- "policy / cycle driver is background only";
- "company realization is not proven".

## 3. P1 Artifact Relationship

P1 should remain independent from P0 artifacts but may read the P0 artifact as input context.

Recommended future relationship:

```text
evidence_pack_<code>.json
+ research_intelligence_<code>.json          # optional P0 input
+ research_questions_<code>.json            # optional P0 input
-> research_intelligence_p1_<code>.json
-> research_questions_p1_<code>.json
-> research_questions_p1_<code>.md
```

P1 artifacts should not overwrite P0 artifacts. P1 should not change P0 question priority. P1 may reference P0 rule IDs and question IDs as `upstream_refs`.

Suggested schema namespace:

```text
research_intelligence_p1.v1
research_questions_p1.v1
```

## 4. P1 Core Output Model

Every P1 diagnostic should use the same anti-vagueness contract as P0:

```text
data_availability_status: available | partial | missing | stale | not_applicable | not_assessable
confidence_cap: high | medium | low | not_assessable
not_assessable_reason
what_was_checked
source_refs
required_evidence
available_evidence
missing_evidence
research_question
```

For macro / industry content, P1 must not output "industry outlook" paragraphs. It must output driver-factor matrices:

```text
driver_factor
driver_scope: macro | policy | industry | supply_chain | commodity | company
driver_direction_observed: positive | negative | mixed | neutral | unknown | not_assessable
required_evidence
available_evidence
missing_evidence
company_transmission_path
research_question
data_availability_status
confidence_cap
not_assessable_reason
what_was_checked
```

### 4.1 Company Transmission Path Schema / Builder Enforcement

`company_transmission_path` is an evidence-bound field, not a free-form narrative field.

P1 schema and builder validation must enforce:

- `company_transmission_path` must cite concrete evidence-pack field values, source-traced values, or specific data points as transmission nodes.
- If no evidence-pack field value or concrete data point can be used as a company transmission node, the field value must be exactly: "传导路径无法从当前证据包验证".
- For that driver row, `confidence_cap` must be `not_assessable`.
- The builder must reject, downgrade, or normalize vague transmission language before artifact serialization.
- The builder must not allow phrases equivalent to "宏观向好，公司受益", "行业空间大，公司有望受益", "policy supports demand, company benefits", or "industry demand is strong, company should benefit" as a valid transmission path.
- Prompt instructions are insufficient. This rule must live in schema validation, builder enforcement, and acceptance checks.

Valid transmission path examples must look like an evidence chain:

```text
source_refs[0].field = financial_metrics.revenue
-> evidence_pack.business_composition.segment = "..."
-> missing_evidence requires customer / order / revenue bridge
```

Invalid transmission paths:

```text
宏观向好，公司受益
行业空间大，公司有望受益
政策持续支持，公司有望兑现
```

The core rule is:

```text
macro / industry signal
-> driver factor
-> required company evidence
-> available company evidence
-> missing company evidence
-> research question
```

Anything that cannot complete this chain must be `not_assessable` or `missing`, not a conclusion.

## 5. Macro / Industry Driver Intelligence

P1 should convert macro, policy, cycle, commodity, and industry information into driver factors only. It must not produce macro forecasts or generic industry summaries.

### 5.1 Macro Driver Factors

Macro factors should be included only when they have an evidence-bound transmission path to the current `strategy_type`. A plausible but unverifiable narrative is not enough; if the current evidence pack cannot provide concrete company transmission nodes, use the required `company_transmission_path` fallback and cap confidence at `not_assessable`.

Examples:

| driver_factor | Required evidence | Existing evidence-pack availability | Future connector need |
| --- | --- | --- | --- |
| interest-rate / financing-cost pressure | debt, interest expense, cash flow, capex, debt maturity | partial: financial metrics may include debt / cash flow if present; maturity usually missing | financial statement notes, debt maturity parser |
| FX exposure | overseas revenue, foreign-currency cost, FX gains / losses | usually missing except business composition hints | annual report note parser, overseas revenue connector |
| commodity input / output price | commodity exposure, revenue mix, gross margin, commodity price series | partial for configured `commodity_prices`; business mix may exist | broader commodity connector, industry price connector |
| policy demand support | policy source, affected demand segment, company contract / revenue bridge | usually missing; policy cannot prove realization | policy-event connector plus company disclosure cross-check |
| customer capex cycle | customer capex data, company order / revenue / receivable bridge | missing for most stocks | customer / downstream capex connector |

Macro driver factors must be written as:

```text
driver_factor: "customer capex cycle"
required_evidence:
  - downstream customer capex trend
  - company customer / order disclosure
  - segment revenue bridge
  - receivables and operating cash-flow validation
available_evidence:
  - financial_metrics.revenue
  - financial_metrics.accounts_receivable if present
missing_evidence:
  - customer capex source
  - company-specific order bridge
  - customer concentration
research_question:
  - "客户资本开支变化是否已经转化为公司订单、收入、回款，而不是仅停留在行业需求假设？"
data_availability_status: partial | missing
confidence_cap: low | not_assessable
```

### 5.2 Industry Driver Factors

Industry factors must be strategy-type-aware. P1 should never apply one generic industry checklist to all companies.

Minimum industry driver groups:

- demand realization;
- pricing / gross-margin pressure;
- capacity / utilization;
- order / customer visibility;
- project acceptance / delivery;
- capex conversion;
- working-capital pressure;
- policy / regulation as a constraint, not proof;
- supply-chain bottleneck or input-cost exposure;
- industry-specific operating metrics.

Examples by current major strategy types:

| strategy_type | P1 industry driver factors |
| --- | --- |
| `ai_datacenter_infrastructure` | customer AI capex cycle, datacenter cabinet / MW demand, rack-up / utilization, PUE / power-cost pressure, liquid-cooling batch orders, power / UPS project delivery, capex-to-revenue bridge |
| `life_science_cxo_services` | global biotech funding, pharma R&D outsourcing demand, backlog / new orders, US / overseas regulatory exposure, project cancellation / delay, capacity utilization, collection cycle |
| `low_altitude_economy_infrastructure` | policy pilot progress, airspace / route approval, project acceptance, operating hours / flight sorties, platform dispatch volume, government-payment cycle |
| `satellite_communication_infrastructure` | transponder / bandwidth utilization, satellite remaining life, launch / failure / insurance events, contract duration, customer concentration, replacement capex |
| `advanced_manufacturing_growth` | new-business revenue split, mass-production orders, customer penetration, product mix, capex absorption, receivables pressure |
| `semiconductor_cycle` | inventory cycle, domestic-substitution revenue, customer qualification, order recovery, capex discipline, gross-margin recovery |
| `resource_core` / `resource_swing` | commodity price exposure, production / reserves, cost curve, sustaining capex, cash-flow cycle resilience |
| `stable_growth` | order quality, grid / infrastructure investment translation, receivables, operating cash flow, ROE source, margin stability |
| `right_trend_growth` | high-growth narrative conversion into orders, revenue, margin, and cash flow; theme heat must remain a hypothesis |

### 5.3 Required Macro / Industry Guardrails

P1 must enforce:

- policy is not revenue;
- news is not order evidence;
- industry demand is not company demand;
- a macro / policy / industry driver is not a company transmission path unless the evidence pack contains concrete company-level nodes;
- customer capex is not company revenue;
- certification / testing / POC is not batch order;
- capex is not capacity release;
- contract liabilities are not backlog;
- theme heat is not business realization.

## 6. Multi-Source Consensus / Divergence / Contradiction

P1 should introduce a structured multi-source diagnostic, but it must be conservative.

Independence is counted by source bucket, not by file count, article count, API count, or repeated mentions.

If there is only one independent source bucket, or source buckets are not independently distinguishable, consensus / divergence / contradiction must be:

```text
assessment_status: not_assessable
not_assessable_reason: "Less than two independent source buckets are available."
```

### 6.1 Source Buckets

Recommended source buckets:

| bucket | Examples | P1 role |
| --- | --- | --- |
| company_disclosure | annual report, quarterly report, announcement | highest priority when source-traced |
| exchange_regulator | exchange filings, regulator records, official notices | high priority for event validation |
| financial_statement | balance sheet, income statement, cash flow statement | high priority for financial validation |
| industry_official | industry association, exchange commodity prices, official statistics | context only unless company bridge exists |
| company_ir | IR Q&A, earnings call, investor communication | useful but must be cross-checked |
| structured_data | AkShare tables, public structured datasets, normalized data APIs | usable with trace and freshness |
| news_media | news, media, sell-side snippets | lead only; not proof |

Bucket counting rules:

- Multiple annual reports, quarterly reports, or announcements from the same company count as one `company_disclosure` bucket for independence.
- Multiple articles from the same media organization or syndicated news chain count as one `news_media` bucket.
- Multiple interfaces, tables, or endpoints derived from the same underlying dataset count as one `structured_data` bucket.
- Repeated media reports of the same claim do not become multi-source consensus.
- A source item can support evidence detail, but it cannot increase `independent_source_count` unless it belongs to a different independent source bucket.
- When fewer than two independent source buckets are available, `consensus`, `divergence`, and `contradiction` must all be marked `not_assessable`.

### 6.2 Consensus Diagnostic Shape

Suggested item:

```json
{
  "topic": "liquid-cooling order realization",
  "assessment_status": "consensus | divergence | contradiction | not_assessable",
  "source_count": 0,
  "source_bucket_count": 0,
  "independent_source_count": 0,
  "supporting_sources": [],
  "diverging_sources": [],
  "contradicting_sources": [],
  "interpretation_boundary": "",
  "required_evidence": [],
  "available_evidence": [],
  "missing_evidence": [],
  "research_question": "",
  "data_availability_status": "not_assessable",
  "confidence_cap": "not_assessable",
  "not_assessable_reason": "",
  "what_was_checked": []
}
```

### 6.3 Consensus Rules

P1 should use rule logic:

- `consensus`: at least two independent source buckets support the same fact and one is company / official / financial statement source.
- `divergence`: at least two independent source buckets describe different scope, period, unit, business segment, or event stage without direct conflict.
- `contradiction`: at least two independent source buckets conflict on a material fact after normalizing period, unit, scope, and source hierarchy.
- `not_assessable`: fewer than two independent source buckets, no source trace, stale source, missing period, or incompatible units.

P1 should not treat "many news articles repeat the same claim" as consensus unless there is independent official or financial evidence from another source bucket.

## 7. Disclosure Consistency

Disclosure consistency checks whether company claims remain consistent across time and disclosure channels. It is not a fraud detector and must not accuse management.

### 7.1 Scope

P1 disclosure consistency should cover:

- same metric across annual / quarterly reports;
- same project across announcements and financial results;
- same business segment across business composition and narrative;
- same order / customer claim across company disclosure and financial statement proxies;
- same risk disclosure across periods;
- changes in wording around capacity, utilization, backlog, project progress, customers, or regulation.

### 7.2 Minimum Diagnostic Shape

```text
disclosure_topic
claim_or_metric
periods_checked
source_refs
consistency_status: consistent | changed | unclear | contradiction | not_assessable
required_evidence
available_evidence
missing_evidence
interpretation_boundary
research_question
data_availability_status
confidence_cap
not_assessable_reason
what_was_checked
```

### 7.3 Rules

- If only the current evidence pack is available and no prior period / second disclosure exists, mark `not_assessable`.
- In single-period evidence-pack conditions, many `not_assessable` disclosure consistency outputs are expected and correct.
- Do not replace `not_assessable` with vague consistency language.
- If a term changes from "intention / cooperation / framework agreement" to "order / revenue", require contract, acceptance, revenue, or cash-flow evidence.
- If a project is mentioned without amount, timeline, customer, capacity, acceptance, or revenue recognition, mark missing evidence.
- If the source period is missing, do not infer trend.
- If a financial statement number and narrative claim appear inconsistent, emit a research question rather than a definitive accusation.

## 8. Project / Capex Tracking

P1 should introduce project tracking as a structured research layer, not as a project database in the minimum implementation.

### 8.1 Project Entity

Suggested project entity:

```text
project_id
project_name
project_type
source_refs
announcement_date
expected_timeline
planned_capex
actual_capex_observed
capacity_or_asset_description
status: announced | under_construction | trial_run | accepted | revenue_generating | delayed | cancelled | unknown | not_assessable
required_evidence
available_evidence
missing_evidence
revenue_bridge
utilization_or_acceptance_bridge
cashflow_bridge
risk_flags
research_question
data_availability_status
confidence_cap
not_assessable_reason
what_was_checked
```

### 8.2 Capex Interpretation Rules

P1 must enforce:

- capex is cash paid for long-term assets, not automatic capacity release;
- project announcement is not construction completion;
- construction completion is not utilization;
- utilization is not revenue unless revenue recognition is evidenced;
- revenue growth is not cash conversion unless operating cash flow and receivables support it;
- planned capex is not actual capex unless the cash-flow statement or disclosure verifies it;
- capacity expansion can increase depreciation, working capital, and execution risk.

### 8.3 Minimum Capex Tracking Questions

P1 should generate questions such as:

- "该 capex 对应哪些项目、资产或产能？"
- "项目是否已有投产、验收、利用率或收入确认证据？"
- "capex 增加是否已经体现在收入、毛利率、经营现金流中？"
- "新增资产是否带来折旧、能耗、维护或现金流压力？"
- "项目延期、客户变化或政策审批是否会影响兑现路径？"

## 9. Company-Level Business-Financial-Risk Linkage Upgrade

P1 should upgrade P0 cross-validation into a three-layer linkage:

```text
business claim
-> financial confirmation / contradiction / missing bridge
-> risk implication / follow-up research question
```

### 9.1 Linkage Dimensions

Minimum dimensions:

- revenue realization;
- gross-margin / pricing quality;
- order / customer visibility;
- capex / capacity conversion;
- cash conversion;
- receivables and inventory pressure;
- regulatory / policy constraint;
- customer concentration / geography risk;
- valuation explainability as evidence sufficiency, not target price.

### 9.2 Linkage Item Shape

```text
linkage_id
business_claim
business_evidence
financial_checks
risk_checks
linkage_status: supported | partially_supported | weak | contradicted | missing_bridge | not_assessable
required_evidence
available_evidence
missing_evidence
research_question
data_availability_status
confidence_cap
not_assessable_reason
what_was_checked
upstream_p0_refs
```

### 9.3 Strategy-Type Examples

`ai_datacenter_infrastructure`:

- Business claim: AI datacenter demand / liquid-cooling / power infrastructure growth.
- Financial checks: segment revenue, contract liabilities as proxy only, capex, operating cash flow, receivables.
- Risk checks: rack-up / utilization, PUE / power cost, delivery cycle, customer concentration.
- P1 question: "AI 数据中心相关需求是否已转化为公司可验证订单、交付、收入和回款？"

`life_science_cxo_services`:

- Business claim: CXO orders / backlog / capacity utilization.
- Financial checks: CXO revenue, contract liabilities as proxy only, accounts receivable, operating cash flow, capex.
- Risk checks: US / overseas regulatory risk, project cancellation, one-off order distortion.
- P1 question: "合同负债、在手订单、新签订单、项目阶段和回款之间是否能形成一致证据链？"

`low_altitude_economy_infrastructure`:

- Business claim: low-altitude infrastructure or operation business realization.
- Financial checks: segment revenue, project acceptance, receivables, operating cash flow.
- Risk checks: policy pilot progress, airspace approval, government-payment cycle, safety events.
- P1 question: "政策试点或项目公告是否已经形成验收、运营量、收入和回款证据？"

`satellite_communication_infrastructure`:

- Business claim: satellite asset monetization.
- Financial checks: revenue, gross margin, capex, depreciation, operating cash flow.
- Risk checks: capacity utilization, remaining satellite life, launch / failure events, customer concentration.
- P1 question: "卫星资源、容量利用、合同期限、折旧和现金流是否支持基础设施运营属性？"

## 10. Existing Evidence Pack vs Future Connectors

P1 should explicitly separate fields available from the current evidence pack from future connector needs.

### 10.1 Available From Current Evidence Pack

Current P1 minimum can use:

- `stock.code`, `stock.name`, `strategy_type`, `sub_type`;
- `stock.status`, `stock.confidence`, `stock.fundamental_score` as read-only context only;
- `confidence_basis.missing_fields`;
- `confidence_basis.data_coverage`;
- `confidence_basis.confidence_breakdown`;
- `basic_info`;
- `financial_metrics`;
- `valuation_metrics`;
- `business_composition`;
- `commodity_prices`;
- `risk_flags`;
- `supporting_evidence`;
- `limiting_evidence`;
- `unknown_or_missing_evidence`;
- `enhanced_must_track_indicators`;
- `invalidation_conditions`;
- `missing_fields`;
- `data_limitations`;
- `source_trace_summary`;
- `forbidden_terms_check`.

These support:

- company-level business-financial-risk linkage;
- missing evidence classification;
- limited driver-factor mapping;
- capex guardrails using `financial_metrics.capex`;
- contract-liability guardrails using `financial_metrics.contract_liabilities`;
- commodity context when `commodity_prices` is available;
- source-trace and data-coverage diagnostics.

### 10.2 Not Reliably Available Today

The current evidence pack usually does not provide:

- direct macro indicators;
- policy event database;
- full annual report note parser;
- company announcement parser;
- IR Q&A history;
- earnings-call transcript history;
- project-level announcement extraction;
- project status history;
- order / backlog structured disclosure;
- customer / supplier database;
- customer capex data;
- peer operating metrics;
- industry operating datasets;
- capacity utilization;
- detailed debt maturity;
- geographic revenue split;
- regulatory event history;
- comparable multi-source longitudinal evidence.

These must be marked `missing`, `future_data_needed`, or `not_assessable`.

### 10.3 Future Connector Candidates

Future P1 / P2 / Future data sources:

- official filing / annual report parser;
- exchange announcement connector;
- company IR Q&A connector;
- financial-statement note parser;
- project / capex announcement extractor;
- policy-event connector;
- industry operating metric connector;
- customer / supplier / customer-capex connector;
- official statistics connector;
- commodity and input-price connector expansion;
- peer selection and peer metrics connector;
- transcript / management communication connector;
- longitudinal artifact store for prior P0 / P1 outputs.

## 11. P1.1 / P1.2 / P1.3a / P1.3b / P1.4 Minimum Split

P1 should be implemented in small independent slices.

### 11.1 P1.1: Evidence-Pack-Only Driver Factor Matrix

Goal:

- Add `research_intelligence_p1_<code>.json` and `research_questions_p1_<code>.json` as independent artifacts.
- Read only existing `evidence_pack` and optionally P0 artifacts.
- Convert macro / industry / company context into driver-factor rows.
- Use `not_assessable` for unavailable multi-source, disclosure, and project claims.
- Historical first version implemented one pilot `strategy_type` only: `ai_datacenter_infrastructure`.
- The pilot covers two `sub_type` values only:
  - `cooling_liquid_cooling_infrastructure`;
  - `datacenter_operator`.
- Do not implement all `strategy_type` values in any single P1.1 step; expand only through accepted narrow P1.1 expansion phases.
- Put all other `strategy_type` values into P1.1 expansion or a later phase.
- Use 002837 and 300442 to validate the driver factor matrix, `not_assessable` behavior, and `company_transmission_path` enforcement before expanding.

Pre-implementation requirements:

- Complete `company_transmission_path` schema / builder enforcement from section 4.1.
- Complete independent source-bucket counting rules from section 6.1.
- Complete the P1.1 pilot narrowing in this section.
- Expand beyond the pilot only after manual quality review accepts the pilot artifacts.

Minimum modules:

- P1 schema;
- evidence-pack field classifier;
- strategy-type driver-factor templates;
- research-question generator;
- safety validation.

Acceptance:

- no code outside AI analyst Research Intelligence P1 module path if implemented later;
- no deterministic field mutation;
- no HTML / Dashboard integration;
- every macro / industry item has driver factor + required evidence + available evidence + missing evidence + research question;
- every driver row either has evidence-bound `company_transmission_path` nodes or the exact fallback "传导路径无法从当前证据包验证" with `confidence_cap: not_assessable`;
- historical pilot coverage was limited to `ai_datacenter_infrastructure` / `cooling_liquid_cooling_infrastructure` / `datacenter_operator`;
- no macro forecast and no broad industry summary.

### 11.2 P1.2: Multi-Source Consensus / Divergence / Contradiction Shell

Goal:

- Add multi-source assessment structure.
- Use current source trace and evidence-pack source buckets.
- Mark `not_assessable` whenever fewer than two independent source buckets exist.

Minimum behavior:

- topic-level source grouping;
- independent source count;
- consensus / divergence / contradiction / not_assessable status;
- source hierarchy guardrails;
- research questions for insufficient source independence.

Acceptance:

- repeated news / same-source items do not become consensus;
- evidence from fewer than two independent source buckets always becomes `not_assessable` for consensus / divergence / contradiction;
- contradictions require period, unit, scope, and source normalization.

### 11.3a P1.3a: Project / Capex Tracking Shell

Goal:

- Add project / capex tracking sections as evidence-gated shells.
- Use current evidence pack where possible, especially capex fields, must-track indicators, limitations, and missing-evidence rows.
- Do not build a full project database.
- Produce capex bridge diagnostics before claiming project realization.

Minimum behavior:

- project entity extraction only from available evidence rows / must-track indicators / limitations;
- capex bridge diagnostics;
- project research questions for missing acceptance, utilization, revenue, and cash-flow bridge.

Acceptance:

- capex never implies capacity release;
- project announcement never implies revenue;
- contract liabilities never imply backlog;
- capex bridge can diagnose missing project, acceptance, utilization, revenue, and cash-flow evidence using the current evidence pack;
- project / capex items without concrete evidence remain `missing` or `not_assessable`.

### 11.3b P1.3b: Disclosure Consistency Shell

Goal:

- Add disclosure consistency sections as an evidence-gated shell.
- Depend on multiple periods or multiple disclosure channels before assessing consistency.
- Avoid filling single-period evidence gaps with vague wording.

Minimum behavior:

- identify disclosure topics from current evidence where possible;
- check whether prior-period or second-disclosure evidence exists;
- mark disclosure consistency as `not_assessable` when only a single-period evidence pack is available;
- generate research questions for missing prior-period, source-period, metric-definition, project-stage, or channel-cross-check evidence.

Acceptance:

- in a single-period `evidence_pack`, a high share of `not_assessable` Disclosure Consistency output is correct behavior, not a defect;
- missing prior disclosure history yields `not_assessable`;
- do not use vague language to fill `not_assessable`;
- do not infer trend, improvement, deterioration, contradiction, or management inconsistency without multiple periods or independent disclosure channels.

### 11.4 P1.4: Business-Financial-Risk Linkage Upgrade

Goal:

- Upgrade P0 cross-validation into P1 linkage items connecting business claim, financial evidence, and risk implication.

Minimum behavior:

- strategy-type linkage templates;
- linkage statuses: supported, partially_supported, weak, contradicted, missing_bridge, not_assessable;
- prioritization of P1 questions by research usefulness, not deterministic scoring impact;
- upstream P0 refs when available.

Acceptance:

- no change to P0 priority or deterministic status;
- valuation context remains explainability only, with no target price;
- risk linkage produces research questions, not trade actions.

## 12. P1 Should Not Implement

P1 should not implement:

- macro forecasting;
- generic industry report writing;
- market timing;
- technical analysis;
- target price or implied upside;
- buy / sell / add / reduce / clear-position language;
- position sizing;
- stop-loss / take-profit;
- trading-account connection;
- live brokerage-report ingestion;
- full peer benchmark engine;
- full annual report PDF parser;
- full project database;
- Dashboard UI;
- HTML Report v2.2 sections;
- chart rendering;
- deterministic score changes;
- classifier rerouting;
- readiness-rule changes;
- connector expansion in the minimum P1.1 implementation;
- automatic web search;
- model-generated contradictions without rule / evidence gates.

## 13. Relationship With HTML Report v2.2

P1 is upstream research intelligence, not presentation.

In P1:

- do not modify `FundamentalHtmlReport` schema;
- do not modify `html_report_prompt_builder`;
- do not modify `html_report_renderer`;
- do not add report sections;
- do not add Dashboard cards;
- do not make HTML depend on P1 artifacts.

Future P2 may integrate stable P1 artifacts into HTML / Dashboard as read-only display sections:

- driver-factor matrix;
- consensus / divergence status;
- disclosure consistency warnings;
- project / capex tracker;
- P1 research questions.

P2 integration should only happen after P1 artifacts are stable and tested. HTML should display P1 limitations visibly and must not convert P1 research questions into conclusions.

## 14. Safety Boundary

P1 remains a fundamental research artifact only.

Forbidden:

- trading advice;
- buy / sell / add / reduce / clear-position language;
- target price;
- upside / downside trading framing;
- position sizing;
- stop-loss / take-profit;
- execution checklist;
- technical analysis;
- K-line, moving average, volume, MACD, RSI, trendline, breakout, support / resistance;
- trading-account connection;
- `technical_skill`;
- `trader_skill`;
- account actions or portfolio instructions.

Allowed:

- "需要补充证据";
- "当前无法判断";
- "多源一致性 not_assessable";
- "该政策 / 行业因素尚未转化为公司业务证据";
- "capex 需要项目、验收、利用率、收入和现金流桥接";
- "合同负债仅可作为订单可见度 proxy，不等同 backlog";
- "该风险应作为后续研究问题跟踪".

## 15. Design Acceptance Criteria

This P1 design is acceptable when:

- macro and industry content is converted into driver factors, not forecasts or generic summaries;
- every driver factor includes required evidence, available evidence, missing evidence, and a research question;
- `company_transmission_path` is schema- and builder-enforced as an evidence-bound field;
- unverifiable transmission paths use exactly "传导路径无法从当前证据包验证" and `confidence_cap: not_assessable`;
- multi-source consensus / divergence / contradiction is `not_assessable` without at least two independent source buckets;
- independent source counting uses source buckets rather than files, repeated announcements, repeated media articles, or multiple APIs from the same underlying dataset;
- disclosure consistency is `not_assessable` without multiple periods or multiple disclosure sources;
- single-period Disclosure Consistency producing many `not_assessable` rows is accepted as correct behavior;
- project / capex tracking does not treat capex as capacity release;
- contract liabilities are never treated as backlog;
- policy, news, and theme heat are never treated as business realization;
- P1.1 first implementation was narrowed to the `ai_datacenter_infrastructure` pilot covering `cooling_liquid_cooling_infrastructure` and `datacenter_operator`, before later accepted CXO and Satellite expansions;
- 002837 and 300442 are used for pilot quality validation before expansion;
- P1 remains an independent Research Intelligence artifact;
- P1 does not modify status, confidence, score, strategy_type, or sub_type;
- HTML / Dashboard integration is explicitly deferred to P2;
- safety boundary excludes trading, technical analysis, target price, and account actions.

## 16. Implementation Recommendation

P1.1 implementation status: implemented / accepted for the AI Datacenter pilot, CXO expansion, and Satellite expansion. The accepted baseline includes `ai_datacenter_infrastructure`, `life_science_cxo_services`, and `satellite_communication_infrastructure`, with `601698` as the Satellite primary acceptance sample. The implementation includes `company_transmission_path` schema + builder enforcement, source-bucket independent counting, conservative `not_assessable` handling, and independent P1 JSON / Markdown artifacts. It remains outside connectors, HTML display, Dashboard display, project database, peer benchmark, all-strategy expansion, and live macro / policy data. Latest recorded validation after Satellite acceptance: pytest `423 passed`; regression suite `passed=47 failed=0 total=47`.

Historical pre-implementation gate: P1.1 implementation was allowed only after this v1.1 design was accepted and the three required preconditions were complete:

- `company_transmission_path` schema / builder enforcement;
- source-bucket-based independent-source counting;
- P1.1 pilot narrowing to `ai_datacenter_infrastructure`.

The implemented first slice is P1.1:

```text
evidence-pack-only P1 schema
+ pilot strategy-type driver-factor templates for ai_datacenter_infrastructure only
+ macro / industry / company driver factor matrix
+ company_transmission_path enforcement
+ explicit not_assessable handling for unavailable multi-source, disclosure, and project data
+ independent P1 JSON / Markdown artifacts
```

The accepted baseline did not start with connectors, HTML display, Dashboard display, project database, peer benchmark, all-strategy expansion, or live macro / policy data. The first value of P1 remains making the current evidence boundaries sharper and converting missing macro / industry / project assumptions into answerable research questions.

After P1.1 Satellite artifacts pass multi-sample observation beyond `601698`, decide whether another narrow P1.1 expansion is warranted. Do not move directly into P1.2 / P1.3 before the current P1.1 expansion behavior is observed across more samples.
