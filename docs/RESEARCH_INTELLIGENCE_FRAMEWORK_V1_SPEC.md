# Research Intelligence Framework v1.1 Design Revision

Date: 2026-05-22

Stage: Design revision only. This document changes documentation only. It does not change code, schemas, tests, pipeline behavior, connectors, prompt builders, report renderers, generated artifacts, or regression fixtures.

## 1. Revision Summary

This v1.1 revision narrows Research Intelligence Framework P0 from a broad research platform into the smallest implementable research-assistant loop:

```text
source hierarchy / evidence classification
-> simplified strategy_type driver map
-> strategy_type-aware business-financial cross-validation
-> rule-triggered contradiction detection
-> P0/P1/P2 research questions with evidence_trigger
-> IR / manual review question list
```

The purpose is to move from "beautiful fundamental report" to "usable next-step research assistant" without overbuilding macro research, industry research, disclosure tracking, project tracking, chart rendering, HTML integration, or free-form AI contradiction generation in P0.

P0 must be deterministic-first and evidence-gated. The AI layer may help phrase summaries, but P0 contradiction detection and P0 question priority must be triggered by explicit rules and evidence conditions, not free-form model invention.

## 2. Relationship With Existing System

Research Intelligence v1.1 remains a new layer above existing artifacts:

```text
output/fundamental_<code>.json
+ output/raw_<code>.json
+ output/evidence_pack_<code>.json
  -> output/research_intelligence_<code>.json
  -> output/research_questions_<code>.json
  -> output/research_intelligence_p1_<code>.json      # P1.1 AI Datacenter pilot when requested
  -> output/research_questions_p1_<code>.json/.md     # P1.1 AI Datacenter pilot when requested
```

It does not modify existing:

- `status`;
- `confidence`;
- `fundamental_score`;
- `strategy_type`;
- `sub_type`;
- deterministic pipeline;
- connector source mappings;
- classifier rules;
- scoring engine;
- readiness planner;
- HTML report renderer;
- existing `FundamentalHtmlReport` schema.

P0 produces independent artifacts. It does not feed or alter HTML Report Generator v2.2. HTML / Dashboard integration is P2.

### 2.1 P0 / P0.1 Implementation Status

Research Intelligence P0 has been implemented and the baseline has been accepted. Research Intelligence P0.1 Template Sharpening and Fallback Template Cleanup have also been implemented and accepted.

Current accepted behavior:

- outputs independent artifacts: `output/research_intelligence_<code>.json`, `output/research_questions_<code>.json`, and `output/research_questions_<code>.md`;
- reads only `output/evidence_pack_<code>.json`;
- does not call LLMs;
- does not use network access;
- does not connect new data sources;
- does not modify `status`, `confidence`, `score`, `strategy_type`, or `sub_type`;
- does not connect to the HTML Report main chain;
- P0.1 sharpens research-question templates by `strategy_type`, `sub_type`, `missing_evidence`, and triggered `rule_id`;
- P0.1 cleans up generic fallback wording in P1/P2 questions when an industry-specific template is available;
- P0.1 preserves `evidence_trigger` enforcement for every P0 question;
- P0.1 preserves proxy guards: contract liabilities are only a partial proxy, capex is not capacity release, R&D ratio is not proof of a technology barrier, liquid-cooling POC / certification is not a batch order, and customer capex is not company revenue;
- final acceptance covered `002837`, `002050`, `603259`, and `300442`;
- latest recorded pytest result: `379 passed`;
- latest recorded regression suite result: `passed=47 failed=0 total=47`;
- generated `output/` artifacts remain runtime products and should not be committed.

This documentation sync stage is documentation-only, so pytest and the regression suite are not rerun here.

### 2.2 P0.1 Accepted Sample Coverage

P0.1 final acceptance refreshed and reviewed four runtime samples:

- `002837` Envicool: liquid-cooling customer validation, POC / testing / certification versus batch orders, liquid-cooling order evidence, room cooling versus ordinary / industrial thermal-control boundary, and revenue growth versus profit / operating cash-flow conversion.
- `002050` Sanhua Intelligent Controls: robotics or other new-business standalone revenue, orders, customers, mass-production evidence, major-customer revenue share, valuation digestion, and separation between expectation and realized evidence.
- `603259` WuXi AppTec: backlog / new orders, contract liabilities as partial proxy only, overseas / US customer exposure, Biosecure Act / overseas regulatory review, customer-loss risk, capacity utilization, project stage, and customer concentration.
- `300442` Range Intelligent Computing: customer contract type and term, cabinet / MW scale, rack-up pace, PUE, AIDC / intelligent-computing demand conversion into contracts / utilization / revenue / operating cash flow, capex-to-revenue bridge, depreciation, and power cost.

### 2.3 P1.1 AI Datacenter Pilot Baseline

Research Intelligence P1.1 has entered implementation and the AI Datacenter pilot baseline has been accepted. This does not change the P0 / P0.1 / P0.2 definitions above.

Accepted P1.1 behavior:

- supports only `strategy_type=ai_datacenter_infrastructure`;
- supports only `cooling_liquid_cooling_infrastructure` and `datacenter_operator`;
- reads `output/evidence_pack_<code>.json` and may read the optional P0 pack;
- writes independent `output/research_intelligence_p1_<code>.json`, `output/research_questions_p1_<code>.json`, and `output/research_questions_p1_<code>.md`;
- does not call LLMs, use network access, connect new data sources, mutate deterministic pipeline outputs, or connect to HTML / Dashboard;
- enforces `company_transmission_path` in schema and builder logic;
- counts independent sources by source bucket;
- preserves `not_assessable` for missing PUE / MW / cabinet / utilization / liquid-cooling revenue / customer-contract bridges.

Accepted pilot samples: `002837` and `300442`. Latest recorded validation: `pytest` `402 passed`; regression suite `passed=47 failed=0 total=47`.

## 3. P0 Scope

P0 is intentionally narrow. It should implement only:

1. `source_hierarchy` / evidence classification.
2. Simplified `strategy_type` driver map.
3. Strategy-type-aware business-financial cross-validation matrix.
4. Rule-triggered contradiction detection.
5. P0/P1/P2 research questions.
6. IR / manual review question list.
7. Safety boundary checks.

P0 should answer:

- What evidence exists?
- What evidence is missing?
- Which business claims can or cannot be checked against financial data?
- Which rule-triggered contradictions or overreads appear?
- Which questions are important enough to ask IR or manually review next?

P0 should not attempt a complete research report or a full investment thesis.

## 4. Moved Out Of P0

The following items are explicitly outside P0:

| Item | New phase | Reason |
| --- | --- | --- |
| complete macro analysis | P1/Future | requires broader and more current macro data |
| complete industry analysis | P1/Future | requires industry operating datasets and peer context |
| complete consensus / divergence analysis | P1 | requires multi-source longitudinal inputs beyond current evidence pack |
| disclosure consistency | P1 | needs filing / IR history and source diffing |
| project tracking | P1 | needs project-level extraction and update history |
| full DuPont | Future | requires stable asset, equity, turnover, and leverage fields |
| HTML Report integration | P2 | display should follow stable artifacts |
| Dashboard integration | P2 | UI should not drive schema design |
| chart rendering | P2 | P0 may emit chart metadata only if cheap, but not render charts |
| peer benchmark | Future | needs peer selection and comparable metrics |
| filing parser | Future | needs PDF / filing parsing infrastructure |
| project database | Future | needs persistent project entity model |

P0 may keep long-term placeholders, but acceptance must not depend on these features.

## 5. Source Hierarchy And Evidence Classification

P0 must classify all evidence by source tier and interpretability.

| Tier | Source type | Examples | P0 role |
| --- | --- | --- | --- |
| S0 | existing system evidence | `fundamental`, `raw`, `evidence_pack`, source trace, missing fields | primary P0 input |
| S1 | official company disclosure | annual reports, quarterly reports, announcements | future direct parser; P0 may only use if present in raw/evidence |
| S2 | official regulator / exchange / market infrastructure | exchange notices, regulator records, commodity exchanges | future direct source; P0 may only use if already source-traced |
| S3 | company IR / management communication | IR Q&A, earnings calls, roadshows | not directly ingested in P0 unless present in raw/evidence |
| S4 | third-party structured data | AkShare public tables, industry associations | usable with source trace and freshness flags |
| S5 | news / media / sell-side | news feeds, brokerage commentary | hypothesis lead only, not final proof |
| S6 | channel / expert / alternative data | expert calls, channel checks, job posts | future only |

Every evidence item used by P0 should carry:

```text
source_tier
source_name
source_period
source_timestamp
evidence_type: fact | proxy | derived | inference | missing
data_availability_status: available | partial | missing | stale | not_applicable
source_confidence: high | medium | low
unit_confidence
what_was_checked
not_assessable_reason
```

`what_was_checked` is required even when data is missing. Example: "checked financial_metrics.operating_cashflow in evidence_pack and raw financial_indicator block; field missing."

## 6. Schema Design Principles

P0 must keep `ResearchIntelligencePack` and `ResearchQuestionSet` separate.

### 6.1 Required Anti-Vagueness Fields

Any P0 diagnostic item, contradiction item, cross-validation item, or research question must support:

```text
data_availability_status
confidence_cap
not_assessable_reason
what_was_checked
```

Definitions:

- `data_availability_status`: whether the required evidence exists, partially exists, is missing, is stale, or is not applicable.
- `confidence_cap`: maximum confidence allowed for this item because of data quality. Example: `low`, `medium`, `not_assessable`.
- `not_assessable_reason`: why the system cannot assess the claim. Required when status is `missing`, `stale`, or `not_assessable`.
- `what_was_checked`: concrete fields, blocks, derived values, or evidence names checked before forming the item.

These fields prevent vague "needs further research" output without showing the evidence basis.

### 6.2 ResearchIntelligencePack

P0 suggested shape:

```json
{
  "schema_version": "research_intelligence.v1",
  "stock_code": "",
  "stock_name": "",
  "generated_at": "",
  "data_cutoff": "",
  "strategy_type": "",
  "sub_type": "",
  "source_hierarchy": [],
  "evidence_classification": [],
  "strategy_driver_map": {},
  "business_financial_cross_validation": [],
  "rule_triggered_contradictions": [],
  "manual_review_items": [],
  "ir_question_candidates": [],
  "safety_boundary": {}
}
```

P0 should not include full macro analysis, full industry analysis, disclosure consistency, project tracking, chart rendering, or HTML report sections.

### 6.3 ResearchQuestionSet

P0 suggested shape:

```json
{
  "schema_version": "research_questions.v1",
  "stock_code": "",
  "stock_name": "",
  "generated_at": "",
  "questions": [
    {
      "question": "",
      "category": "",
      "priority": "P0",
      "evidence_trigger": "",
      "trigger_rule_id": "",
      "why_it_matters": "",
      "evidence_gap": "",
      "suggested_recipient": "IR",
      "expected_answer_type": "numeric",
      "source_refs": [],
      "data_availability_status": "partial",
      "confidence_cap": "medium",
      "not_assessable_reason": "",
      "what_was_checked": []
    }
  ],
  "p0_summary": "",
  "p1_summary": "",
  "p2_summary": "",
  "do_not_conclude_until_resolved": []
}
```

P0 rule: no question may be priority `P0` unless `evidence_trigger` is present and non-empty. A question without `evidence_trigger` can be P1, P2, or excluded.

## 7. Simplified Strategy Type Driver Map

P0 driver maps should be compact and operational. They do not need full industry reports.

Each driver item should include:

```text
driver_name
why_it_matters
required_evidence
available_evidence
missing_evidence
cross_validation_checks
```

Minimum driver groups:

- demand / revenue validation;
- margin / pricing validation;
- cash conversion;
- working capital;
- capex / asset intensity;
- customer / order visibility;
- valuation explainability;
- framework-specific operating evidence.

## 8. Strategy-Type-Aware Cross-Validation

P0 cross-validation must be `strategy_type` aware. It cannot apply one generic checklist to every company.

Every cross-validation item should include:

```text
strategy_type
business_claim
financial_checks
required_evidence
available_evidence
missing_evidence
validation_status: validated | partially_validated | weak | contradicted | missing | not_assessable
data_availability_status
confidence_cap
not_assessable_reason
what_was_checked
triggered_question_ids
```

### 8.1 `ai_datacenter_infrastructure`

Validation path:

- data-center revenue / AI infrastructure revenue vs segment revenue;
- MW / cabinet / utilization / PUE claims vs disclosed operating indicators;
- liquid-cooling or power infrastructure orders vs revenue and contract liabilities;
- capex vs capacity / revenue bridge;
- receivables and operating cash flow vs project delivery claims.

Typical P0 questions:

- 数据中心或 AI 基础设施相关收入占比是多少？
- 机柜数、MW、上架率、PUE 或液冷订单是否有披露来源？
- capex 对应哪些项目，是否已有收入或利用率验证？

### 8.2 `life_science_cxo_services`

Validation path:

- CXO revenue contribution vs segment revenue;
- backlog / new orders language vs disclosed order evidence;
- overseas exposure vs revenue split;
- capex / capacity expansion vs utilization and revenue conversion;
- receivables and cash flow vs project delivery and customer quality.

Typical P0 questions:

- CXO 收入、海外收入和客户结构是否可拆分？
- 在手订单或新签订单是否有官方披露？
- capex 对应产能是否已经形成收入或利用率改善？

### 8.3 `low_altitude_economy_infrastructure`

Validation path:

- low-altitude revenue vs segment revenue;
- project contracts / acceptance vs revenue recognition;
- flight sorties / operating hours / platform dispatch volume vs operating evidence;
- receivables and cash flow vs government or project payment cycle;
- theme exposure vs actual infrastructure / operation business.

Typical P0 questions:

- 低空相关收入和项目验收是否可确认？
- 运营小时、飞行架次或平台调度量是否有披露？
- 应收和现金流是否反映项目回款压力？

### 8.4 `satellite_communication_infrastructure`

Validation path:

- satellite communications revenue vs segment revenue;
- satellite resources / bandwidth / transponder capacity vs asset evidence;
- utilization / lease rate vs revenue and margin;
- satellite remaining life, capex, depreciation vs cash-flow stability;
- customer contracts vs contract duration and receivables.

Typical P0 questions:

- 在轨卫星、带宽或转发器资源是否有可验证披露？
- 容量利用率、客户合同期限和单价是否可取得？
- capex、折旧和经营现金流是否支持基础设施属性？

### 8.5 `advanced_manufacturing_growth`

Validation path:

- traditional business vs EV / robotics / new manufacturing revenue split;
- new-business claims vs segment revenue and customer evidence;
- capex vs new capacity / new revenue bridge;
- gross margin movement vs product mix;
- receivables and operating cash flow vs customer growth.

Typical P0 questions:

- 机器人或新业务是否已经形成收入，收入占比是多少？
- 新业务客户是否有订单、量产或收入证据？
- 毛利率变化来自产品结构还是成本 / 价格因素？

### 8.6 `right_trend_growth`

Validation path:

- high-growth narrative vs revenue growth and margin;
- customer capex / order visibility vs contract liabilities and receivables;
- valuation explainability vs earnings and cash-flow support;
- capex vs growth bridge;
- news-driven claims vs segment revenue.

Typical P0 questions:

- 高景气链条是否转化为收入、利润和现金流？
- 订单或客户验证是否充分，还是只有新闻 / 主题线索？
- 估值解释是否依赖尚未兑现的利润增长？

### 8.7 `resource_core` / `resource_swing`

Validation path:

- commodity exposure vs business composition;
- resource prices vs revenue / margin / cash flow sensitivity;
- reserves / production / cost curve where available;
- capex vs sustaining or expansion needs;
- debt and cash flow vs cycle resilience.

Typical P0 questions:

- 核心商品暴露和收入占比是否可确认？
- 产量、成本和资源价格变化如何传导到利润？
- 经营现金流和债务结构能否承受周期波动？

### 8.8 `semiconductor_cycle`

Validation path:

- localization or cycle recovery narrative vs revenue growth;
- inventory build vs demand and gross margin;
- R&D intensity vs product adoption, not moat proof;
- customer / order validation vs receivables and contract liabilities;
- capex vs downstream cycle and revenue bridge.

Typical P0 questions:

- 存货变化是否与需求复苏叙事一致？
- 国产替代收入或客户导入是否有收入证据？
- R&D 强度是否仅代表投入，而非已经验证的壁垒？

### 8.9 `stable_growth`

Validation path:

- stable order / policy investment narrative vs revenue and contract liabilities;
- ROE vs cash flow and leverage;
- receivables vs revenue growth;
- debt-to-asset and cash flow vs stability claim;
- margin stability vs business mix.

Typical P0 questions:

- 稳健增长是否有现金流和回款支撑？
- 应收是否过快扩张？
- ROE 变化是否来自业务质量而非杠杆？

### 8.10 `theme_only` / `unknown`

Validation path:

- theme claim vs main business and segment revenue;
- news-only exposure vs official disclosure;
- missing business composition and missing financial anchors;
- inability to classify vs data gaps.

Typical P0 questions:

- 当前主题是否有主营收入、订单或客户证据？
- 为什么无法稳定分类，缺少哪些基础字段？
- 哪些主题相关说法不得进入正式研究结论？

## 9. Rule-Triggered Contradiction Detection

P0 contradiction detection must be a rule engine. It should not be AI free generation.

Each rule should define:

```text
rule_id
description
required_fields
trigger_condition
severity
question_template
what_was_checked
data_availability_status_logic
confidence_cap_logic
not_assessable_reason_logic
```

If required fields are missing, the rule should emit `not_assessable` or a missing-data research question, not fabricate a contradiction.

### 9.1 Minimum P0 Rule Set

P0 should reserve at least these rules:

| rule_id | Trigger intent |
| --- | --- |
| `revenue_growth_vs_cashflow_mismatch` | revenue growth is positive while operating cash flow is weak, negative, or unavailable |
| `profit_growth_without_cashflow` | net profit growth or profit strength lacks operating cash-flow support |
| `capex_without_revenue_bridge` | capex exists or rises but no revenue / utilization / capacity bridge is available |
| `new_business_without_segment_revenue` | new-business claim appears but segment revenue evidence is missing |
| `contract_liabilities_overread_as_backlog` | contract liabilities are being treated as order backlog or confirmed future revenue |
| `r_and_d_ratio_overread_as_moat` | R&D ratio is being treated as technology moat proof |
| `inventory_build_vs_demand_claim` | inventory build conflicts with demand recovery or high-growth narrative |
| `receivables_growth_vs_revenue_growth` | receivables grow faster than revenue or receivables data is needed to validate revenue quality |
| `high_valuation_without_earnings_cashflow_support` | valuation is high but earnings / cash-flow support is weak or missing |
| `policy_theme_without_contract_revenue` | policy or theme language exists without contract, revenue, or customer evidence |
| `commodity_exposure_without_business_mix` | resource thesis exists but commodity revenue exposure or business mix is missing |
| `customer_order_claim_without_customer_evidence` | customer or order claim lacks disclosed customer / order source |
| `capacity_claim_without_utilization` | capacity or project narrative lacks utilization, acceptance, or revenue conversion evidence |
| `stable_growth_without_receivables_cashflow_check` | stable-growth claim lacks cash-flow and receivables validation |
| `classification_low_confidence_requires_review` | classification is low-confidence or unknown, requiring manual framework review |

### 9.2 Rule Output

Each triggered rule should emit:

```text
rule_id
triggered: true | false | not_assessable
severity: high | medium | low
claim_or_risk
evidence_for
evidence_against
missing_evidence
research_question_id
data_availability_status
confidence_cap
not_assessable_reason
what_was_checked
```

P0 should distinguish:

- actual contradiction;
- proxy overread;
- missing bridge;
- missing-data blocker;
- low-confidence classification blocker.

## 10. Evidence Trigger Design

Every P0 research question must have an `evidence_trigger`.

Allowed P0 triggers:

- a rule-triggered contradiction;
- a rule-triggered proxy overread;
- a missing required field for the current `strategy_type`;
- a low-confidence or unknown classification;
- source freshness or source trace failure for a critical field;
- financial metric mismatch generated by a rule;
- business claim present without required validation evidence.

Disallowed P0 triggers:

- generic curiosity;
- "would be nice to know";
- broad macro interest;
- broad industry background;
- unsourced model speculation;
- chart or display preference.

Question priority policy:

- `P0`: must have `evidence_trigger`, must affect assessability of a core business claim, financial quality claim, or strategy-type classification.
- `P1`: useful for improving confidence but not required for the immediate core validation.
- `P2`: useful background, monitoring, or future data enrichment.

If no `evidence_trigger` exists, the question cannot be P0.

## 11. IR And Manual Review Question List

P0 should produce two related but distinct lists:

| List | Purpose |
| --- | --- |
| `manual_review_items` | what the internal analyst should inspect in source files or data |
| `ir_question_candidates` | what could be asked to IR or management |

Each item should include:

```text
question
category
priority
evidence_trigger
trigger_rule_id
why_it_matters
required_answer_type: numeric | document | explanation | timeline | confirmation
related_cross_validation_item_id
source_refs
data_availability_status
confidence_cap
not_assessable_reason
what_was_checked
```

Example P0 IR questions:

- 请拆分 AI 数据中心 / 液冷 / 电力基础设施相关收入及毛利率；`evidence_trigger`: `new_business_without_segment_revenue`.
- 请说明合同负债对应的业务和客户类型，是否仅为收入可见度 proxy；`evidence_trigger`: `contract_liabilities_overread_as_backlog`.
- 请解释收入增长与经营现金流背离的原因；`evidence_trigger`: `revenue_growth_vs_cashflow_mismatch`.
- 请说明 capex 对应项目状态以及是否已有收入 / 利用率验证；`evidence_trigger`: `capex_without_revenue_bridge`.

## 12. Long-Term Architecture Retained

v1.1 keeps the larger architecture as a roadmap, but not as P0.

### P1

- disclosure consistency;
- project tracking;
- complete consensus / divergence analysis;
- source freshness and stale-evidence engine;
- more robust rule library;
- longitudinal comparison across prior research intelligence outputs.

### P2

- HTML Report integration;
- Dashboard integration;
- exportable research-question workflows;
- chart rendering for evidence matrix, contradiction map, validation matrix, and risk heatmap;
- stale / mismatch checks between rendered reports and intelligence artifacts.

### Future

- peer benchmark engine;
- filing parser;
- project database;
- industry operating metric connectors;
- customer / supplier database;
- full DuPont;
- debt maturity and interest coverage;
- analyst-report consensus comparison if licensing permits;
- human feedback loop for resolved / stale / escalated questions.

## 13. P0 Non-Goals

P0 must not:

- call model APIs automatically;
- search the web automatically;
- ingest live brokerage reports;
- parse annual report PDFs;
- build a peer benchmark model;
- create a project database;
- generate charts;
- integrate into HTML Report Generator;
- integrate into Dashboard;
- change existing deterministic conclusions;
- change existing safety terms;
- produce trading advice.

## 14. Safety Boundary

Research Intelligence v1.1 preserves the current safety boundary:

- no trading advice;
- no buy / sell / add / reduce / clear-position recommendation;
- no target price;
- no position sizing;
- no stop-loss, take-profit, or execution checklist;
- no technical analysis;
- no K-line, moving average, volume, MACD, RSI, trendline, or price-timing module;
- no trading-account connection;
- no `technical_skill` implementation;
- no `trader_skill` implementation;
- no automatic conversion from risk or follow-up questions into trade actions.

Allowed wording:

- "需要复核";
- "需要跟踪";
- "当前证据不足";
- "建议向 IR 询问";
- "需要等待披露验证";
- "该结论应降低置信度";
- "该业务假设尚未被财务数据验证".

Disallowed wording as recommendations:

- "买入";
- "卖出";
- "加仓";
- "减仓";
- "清仓";
- "目标价";
- "止损";
- "止盈";
- "仓位";
- "短线";
- "突破";
- "均线";
- "K线";
- "技术指标".

## 15. Design Acceptance Criteria

This v1.1 design is accepted when:

- P0 is limited to source hierarchy, simplified driver map, cross-validation, rule-triggered contradictions, research questions, and IR / manual review questions;
- P0 excludes complete macro, complete industry, disclosure consistency, project tracking, full DuPont, HTML integration, Dashboard integration, and chart rendering;
- `ResearchIntelligencePack` and `ResearchQuestionSet` are separate artifacts;
- schema design requires `data_availability_status`, `confidence_cap`, `not_assessable_reason`, and `what_was_checked`;
- contradiction detection is defined as a rule engine;
- at least 10-15 contradiction / proxy / missing-bridge rules are specified;
- every P0 research question requires `evidence_trigger`;
- cross-validation is strategy-type-aware across the currently important strategy types;
- P1/P2/Future roadmap preserves the larger architecture without bloating P0;
- all safety boundaries remain unchanged.

Because this is documentation only, no pytest run is required.

## 16. Implementation Recommendation

Recommendation status: P0 implementation has proceeded and the baseline has been accepted. The original implementation constraints below remain the accepted boundary for future maintenance and P0.1 work.

Recommended P0 implementation constraints:

- add new AI analyst-layer modules or artifacts only;
- output independent `research_intelligence_<code>.json` and `research_questions_<code>.json`;
- do not modify existing deterministic pipeline behavior;
- do not modify `status`, `confidence`, `score`, `strategy_type`, or `sub_type`;
- do not modify HTML report renderer or current formal report schema;
- implement contradiction detection as a rule engine;
- require `evidence_trigger` for every P0 question;
- add focused tests for rule triggering, missing-data behavior, schema anti-vagueness fields, and safety boundary.

The highest-value first slice is:

```text
source hierarchy
+ strategy_type-aware cross-validation
+ 10-15 deterministic contradiction rules
+ evidence-triggered P0 IR question list
```
