# AI Datacenter Infrastructure Framework Design Audit v1.1

Date: 2026-05-21

Revision basis:

- v1.0 design audit for `ai_datacenter_infrastructure`.
- Independent Claude / Sonnet audit verdict: B; can enter implementation only after design revision.
- AI Datacenter Infrastructure Out-of-Sample Generalization Audit results for `002837`, `002335`, `002518`, `300442`, `301018`, `300476`, and `300308`.

Scope:

- Design-only revision for the proposed fundamental framework: `ai_datacenter_infrastructure`.
- This stage modifies this documentation file only.
- No classifier, connector, deterministic pipeline, dashboard, tests, config, scoring engine, code-level `strategy_type`, `technical_skill`, or `trader_skill` change is included.
- No trading advice, technical analysis, target price, position sizing, timing advice, or account action.

## 1. Revision Summary

The v1.0 design correctly identified an industry-framework gap: the current system can collect generic financial and business-composition fields, but it lacks AI-datacenter-specific evidence such as datacenter revenue share, customer structure, orders, delivery, cabinet / MW resources, rack-up rate, PUE, liquid-cooling validation, and customer capex cycle.

v1.1 accepts the core framework but tightens the boundary:

- `ai_server_supply_chain_boundary` is removed as a formal `sub_type`.
- PCB, optical modules, servers, chips, semiconductor chains, internet cloud self-built datacenters, EPC contractors, generic power equipment, and military / defense system integrators become exclusion or regression samples, not framework sub-types.
- `ai_datacenter_infrastructure` must take priority over `right_trend_growth` only when positive evidence is present. Theme words alone cannot migrate a company.
- Mixed power / UPS companies and thermal-control companies require explicit boundary rules and confidence caps.
- Future proxy ideas are recorded, but v1 should not automatically calculate complex proxies.

## 2. strategy_type Definition

`ai_datacenter_infrastructure`

This framework applies to companies whose revenue and business model mainly come from AI datacenter / datacenter infrastructure construction, operation, or core supporting systems. It includes IDC / AIDC operation services, datacenter power / UPS / distribution infrastructure, and datacenter cooling / liquid cooling / precision thermal-control infrastructure.

The core value drivers are not generic AI theme exposure. They are datacenter customer demand, order conversion, delivery capability, cabinet / MW resources, rack-up and utilization, liquid-cooling penetration, power distribution capability, operating efficiency, cash conversion, capex discipline, and customer capital-expenditure cycles.

This is explicitly not:

- A generic AI computing-power supply-chain framework.
- An optical-module framework.
- A PCB framework.
- A server OEM framework.
- A chip or semiconductor framework.
- A storage / photovoltaic main-business framework.
- A generic industrial-air-conditioning or HVAC framework.
- An internet / cloud platform self-built datacenter framework.
- A construction / EPC / mechanical-electrical contractor framework.
- A military / defense system-integration framework.
- A theme framework triggered only by news mentions of AI datacenters.

## 3. Sub-Type Architecture

Recommendation: v1 should use one main `strategy_type=ai_datacenter_infrastructure` plus formal `sub_type`, or equivalent routing metadata.

Formal v1 `sub_type` values:

1. `datacenter_operator`
2. `power_ups_infrastructure`
3. `cooling_liquid_cooling_infrastructure`

Removed from formal `sub_type`:

- `ai_server_supply_chain_boundary`

Reason:

- Boundary and negative samples should support classifier exclusion rules and regression tests, but they should not become framework sub-types.
- PCB, optical modules, server OEMs, and chips are AI computing-power manufacturing chains. They are not datacenter infrastructure operation, power / UPS infrastructure, or cooling / liquid-cooling infrastructure under this framework.

### 3.1 `datacenter_operator`

Representative positive sample:

- `300442` 润泽科技.

Applicable business model:

- IDC / AIDC / datacenter operation services.
- Datacenter hosting, cabinet resources, computing-infrastructure operation, and related service revenue.

Core indicators:

- Cabinet count.
- MW scale.
- Rack-up rate / utilization.
- PUE and PUE trend.
- Customer structure and contract term.
- Revenue per cabinet and revenue per MW.
- Datacenter capex and construction-in-progress.
- Depreciation and amortization.
- EBITDA / EBITDA margin as future data needed.
- Operating cash flow.
- Average electricity price, power-cost ratio, and energy-policy exposure.

### 3.2 `power_ups_infrastructure`

Representative mixed or boundary samples:

- `002335` 科华数据.
- `002518` 科士达.

Applicable business model:

- Datacenter UPS, power supply, power distribution, and power-infrastructure equipment.
- Companies with storage / photovoltaic / new-energy businesses require explicit segment separation.

Core indicators:

- Datacenter power / UPS revenue share.
- Datacenter orders separated from storage / photovoltaic orders.
- UPS / distribution gross margin.
- Datacenter customer revenue share.
- Customer structure.
- Project acceptance and collection cycle.
- Delivery cycle.
- Accounts receivable and operating cash flow.
- Storage / photovoltaic revenue-share boundary.

### 3.3 `cooling_liquid_cooling_infrastructure`

Representative positive or boundary samples:

- `002837` 英维克.
- `301018` 申菱环境.

Applicable business model:

- Datacenter thermal control, precision air conditioning, liquid cooling, and cooling systems.
- Companies with ordinary industrial HVAC or non-datacenter thermal-control businesses require explicit segment separation.

Core indicators:

- Datacenter cooling revenue share.
- Liquid-cooling revenue share.
- Liquid-cooling technology route.
- Liquid-cooling certification stage.
- Liquid-cooling customer validation stage.
- Liquid-cooling batch orders.
- Liquid-cooling revenue recognition.
- Delivery cycle.
- Gross margin.
- Boundary with ordinary air-conditioning / industrial thermal-control business.

## 4. Priority Rule Versus `right_trend_growth`

`ai_datacenter_infrastructure` and `right_trend_growth` may overlap because datacenter-infrastructure companies can also show high growth, strong demand, or AI-related tailwinds. The framework needs an explicit routing priority.

Priority rule:

- If a company satisfies the Tier-1 positive trigger for `ai_datacenter_infrastructure`;
- and datacenter-related revenue share is confirmable, or there is clear datacenter order / customer / asset / operation evidence;
- then it should be routed to `ai_datacenter_infrastructure` before using `right_trend_growth` as a fallback explanation.

Hard constraint:

- Priority must depend on positive evidence. Do not migrate a company from `right_trend_growth` only because the text mentions AI datacenter, computing power, or infrastructure.

Reverse exclusions:

- Optical-module companies, such as `300308` 中际旭创, should remain in `right_trend_growth` or a more suitable optical-module / computing-power supply-chain framework. They should not migrate to `ai_datacenter_infrastructure`.
- AI PCB companies, such as `300476` 胜宏科技, should remain in `right_trend_growth` or another manufacturing-growth framework. They should not migrate to `ai_datacenter_infrastructure`.
- Server OEMs, chips, semiconductor equipment, and semiconductor-chain companies should not enter this framework.

## 5. Classification Boundary

Should classify into `ai_datacenter_infrastructure` when evidence supports one of the three formal sub-types:

- IDC / AIDC operation services.
- Datacenter hosting, cabinet, MW, or computing-infrastructure operation.
- Datacenter UPS, power supply, distribution, or power infrastructure.
- Datacenter thermal control, precision air conditioning, liquid cooling, or cooling infrastructure.
- Companies whose datacenter-related revenue, orders, customers, assets, cabinet / MW scale, delivery, or operating metrics can be verified.

Should not classify into this framework:

- Optical modules.
- PCB.
- Server OEMs.
- Chips / semiconductors.
- Semiconductor equipment.
- Storage / photovoltaic main businesses with only minor or unverifiable datacenter exposure.
- Generic power equipment without datacenter-specific revenue, customer, or order evidence.
- Ordinary industrial air conditioning / generic HVAC.
- Generic manufacturing companies with AI-datacenter theme language.
- Internet, cloud, or telecom service companies whose datacenters are mainly self-built for internal use.
- Construction, EPC, or mechanical-electrical general contractors whose main business is project contracting or installation, even if they build datacenter projects.
- Military / defense procurement or system-integration companies, even if projects mention datacenters.
- Companies with only news, policy, strategic-cooperation, or concept mentions but no revenue, order, customer, asset, delivery, or operating evidence.

## 6. Mixed Business Boundary Rules

### 6.1 Power / UPS Mixed With Storage, Photovoltaic, or New Energy

Rules for `002335` 科华数据, `002518` 科士达, and similar companies:

1. If datacenter UPS / power / distribution revenue can be independently confirmed and reaches a verifiable material level:
   - The company can be a candidate for `power_ups_infrastructure`.
   - The evidence pack must label storage / photovoltaic / new-energy revenue share and business boundary.
   - Confidence should be reduced by one level because mixed business weakens framework purity.

2. If datacenter power business cannot be separated from storage / photovoltaic business:
   - Do not automatically classify into `ai_datacenter_infrastructure`.
   - Label as "mixed business; segment data needed".
   - Recommend manual review.
   - Confidence cap should be `low` or `low_medium`.

3. If storage / photovoltaic business is the main business and datacenter business share is low or unverifiable:
   - Do not classify into this framework.

Guard:

- Do not mix power / UPS metrics with storage / photovoltaic metrics.
- Do not treat storage orders, photovoltaic inverter orders, or new-energy project orders as datacenter orders.

### 6.2 Cooling / Liquid Cooling Mixed With Ordinary HVAC

Rules for `301018` 申菱环境 and similar thermal-control companies:

1. If datacenter thermal-control / liquid-cooling revenue share is high, or there is clear datacenter customer contract evidence / liquid-cooling customer validation:
   - The company can be a candidate for `cooling_liquid_cooling_infrastructure`.

2. If datacenter revenue share is low-to-medium or only generic thermal-control exposure is known:
   - Treat as a boundary sample.
   - Confidence cap should be `low_medium`.
   - The evidence pack must label "datacenter cooling revenue share pending verification".

3. If datacenter revenue cannot be confirmed and the main business is clearly industrial / commercial air conditioning:
   - Do not classify into this framework.
   - Mark as ordinary industrial thermal-control / HVAC boundary sample.

Guard:

- Do not automatically classify ordinary industrial air conditioning, generic HVAC, or non-datacenter thermal-control businesses into the datacenter-cooling framework.

## 7. Structured Keyword and Trigger Logic

Tier-1 positive trigger should require AND logic:

```text
(
  "数据中心" OR "IDC" OR "AIDC" OR "智算中心" OR "算力中心"
)
AND
(
  "液冷" OR "精密温控" OR "UPS" OR "不间断电源" OR "机柜" OR "MW" OR "上架率" OR "PUE"
)
AND
(
  "收入" OR "订单" OR "合同" OR "客户" OR "运营" OR "交付"
)
AND NOT
(
  "自建数据中心" OR "EPC总包" OR "建筑施工" OR "军工" OR "国防" OR
  "光模块" OR "PCB" OR "服务器整机" OR "芯片"
)
```

High false-positive keyword rules:

- "数据中心": determine whether the company is a supplier / operator or only a self-use datacenter owner.
- "液冷": confirm it is IT / server / datacenter cooling, not industrial liquid cooling.
- "配电": require datacenter-specific product line, customer, order, or revenue evidence.
- "AI基础设施": require revenue or contract evidence.
- "机柜": determine whether it is an IDC operating asset, not generic cabinet manufacturing.

Keyword rule:

- Positive keywords can trigger candidate review, but cannot alone determine classification.
- Negative keywords should force exclusion review or boundary routing.
- Tier-1 trigger is a classification candidate rule, not a confidence rule. Confidence still depends on evidence quality.

## 8. Data Requirements

### 8.1 Required Data

- `basic_info`: required for main business, industry context, and initial exclusion review.
- `business_composition`: required to separate datacenter exposure from adjacent or mixed businesses.
- Datacenter-related revenue or segment revenue: required for meaningful framework confidence.
- Revenue / profit / gross margin: required for base operating quality.
- Operating cash flow: required for cash-conversion quality.
- Accounts receivable: required for revenue-quality and collection-cycle checks.
- Contract liabilities: required as a partial proxy for order visibility, not as confirmed backlog.
- Capex: required for operator asset expansion and supplier capacity-cycle observation.
- Valuation: required for complete fundamental context, but not sufficient for classification or confidence.

### 8.2 Critical Confidence-Gating Indicators

Shared:

- AI datacenter / datacenter-related revenue share.
- Datacenter customer revenue share.
- Major-customer concentration.
- Orders / backlog / contract evidence.
- Order-to-delivery cycle.
- Receivables and operating cash-flow matching.
- Customer capital-expenditure cycle.
- Capex conversion cycle.
- Construction-in-progress amount and expected completion schedule.
- Historical capex-to-revenue conversion efficiency.

`datacenter_operator`:

- Cabinet count.
- MW scale.
- Rack-up rate / utilization.
- PUE and PUE trend.
- Average electricity price.
- Power-cost ratio.
- Customer contract term.
- Revenue per cabinet.
- Revenue per MW.
- Datacenter capex.
- Depreciation and amortization.
- EBITDA / EBITDA margin as future data needed.

`power_ups_infrastructure`:

- Datacenter power / UPS revenue share.
- Datacenter orders separated from storage / photovoltaic orders.
- Datacenter customer revenue share.
- Customer structure.
- UPS / distribution gross margin.
- Project acceptance and collection cycle.
- Delivery cycle.
- Storage / photovoltaic revenue-share boundary.
- Accounts receivable.

`cooling_liquid_cooling_infrastructure`:

- Datacenter cooling revenue share.
- Liquid-cooling revenue share.
- Liquid-cooling technology route.
- Liquid-cooling certification stage.
- Liquid-cooling customer validation stage.
- Liquid-cooling batch orders.
- Liquid-cooling revenue recognition.
- Delivery cycle.
- Ordinary air-conditioning / industrial thermal-control revenue-share boundary.
- Gross margin.

### 8.3 Preferred Data

- Overseas revenue share.
- Top-customer certification.
- Customer capex guidance.
- Liquid-cooling penetration.
- Capacity utilization.
- Inventory structure.
- Unit value.
- Project acceptance progress.
- Energy-quota approval or power-resource documentation for IDC operators.

### 8.4 Optional Data

- Major-customer announcements.
- Overseas orders.
- Datacenter policy projects.
- Energy-consumption policy.
- Supply-chain certification.
- Price-competition events.
- Liquid-cooling POC / testing / certification disclosures, clearly separated from batch orders.

## 9. Proxy Rules: Record Only, Do Not Calculate in v1

Claude / Sonnet suggested several proxy ideas. v1.1 records them for future design, but v1 implementation should not automatically calculate complex proxies.

### 9.1 IDC Rack-Up Rate / Utilization Proxy

Possible observations:

- Operating cabinet count / total cabinet count, if company discloses both.
- Revenue / cabinet count, with large error and comparability limitations.

v1 rule:

- Do not automatically calculate rack-up or utilization proxies.
- Missing rack-up / utilization must cap confidence.
- If a company discloses the metric directly, use it as evidence and label the source.

### 9.2 Liquid-Cooling Revenue Share Proxy

Possible observations:

- Directly disclosed liquid-cooling product revenue.
- Major liquid-cooling contract announcements as best-effort qualitative evidence.

v1 rule:

- Do not infer liquid-cooling revenue share automatically.
- Without independently confirmed liquid-cooling revenue, do not state that liquid-cooling business has scaled.
- Liquid-cooling POC, testing, or certification is not equivalent to batch orders or revenue recognition.

### 9.3 Backlog Proxy

Possible observations:

- Contract liabilities as `partial_proxy`.
- Signed contract announcements, where disclosed.

v1 rule:

- Do not synthesize contract liabilities into real backlog.
- Contract liabilities have different meanings for equipment suppliers and IDC operators.
- If contract liabilities are used as proxy evidence, confidence must not be `high`.

## 10. Risk Guards

The framework must enforce the following guards:

1. Do not treat AI-datacenter theme exposure as order realization.
2. Do not treat customer capex expectations as company revenue certainty.
3. Do not treat contract liabilities as real backlog.
4. Do not treat capex as guaranteed capacity release.
5. Do not identify a company as AI-datacenter main business when datacenter revenue share is missing.
6. Do not mix IDC-operator indicators with equipment-supplier indicators.
7. Do not mix power / UPS business with storage / photovoltaic business.
8. Do not mix liquid cooling / precision thermal control with ordinary industrial air conditioning.
9. Do not classify PCB, optical modules, servers, or chips into this infrastructure framework.
10. Do not conclude sufficient business realization when orders, customer structure, and delivery cycle are missing.
11. Do not conclude datacenter operating efficiency when rack-up rate / utilization / PUE are missing.
12. Do not conclude liquid-cooling realization when liquid-cooling customer validation is missing.
13. Do not conclude strong revenue quality when receivables and operating cash flow do not match.
14. Treat price competition and technology-route change as explicit risks.
15. Treat energy policy, PUE constraints, and project-approval risk as datacenter-operator risks.
16. If top-three customer revenue share is high, label customer-concentration and major-customer order-cut risk; do not use revenue growth to mask single-customer risk.
17. Treat liquid-cooling technology-route risk explicitly. Cold-plate, immersion, rear-door / backplate, and other routes differ; do not infer company benefit from generic liquid-cooling demand growth.
18. Treat power quota and land-use indicator constraints explicitly. IDC construction-in-progress is not equal to available cabinets; without power quota or approval evidence, do not assert deterministic capacity release.
19. For IDC operators, compare profitability with attention to EBITDA and depreciation; do not rely only on net margin because depreciation policy can distort cross-company comparisons.
20. Do not treat liquid-cooling POC / testing / certification as batch orders or revenue recognition.
21. Do not classify internet / cloud / telecom self-built datacenters unless the monetized business is datacenter operation service rather than internal infrastructure.
22. Do not classify EPC, construction, or mechanical-electrical contractors only because they build datacenter projects.
23. Do not classify generic power-equipment companies without datacenter-specific revenue, customer, or order evidence.
24. Do not classify military / defense system-integration companies only because a project involves datacenter infrastructure.

## 11. Must-Track Indicators

Each must-track item should be represented in the evidence pack with `why_it_matters`, `current_status`, `affects_dimension`, and `suggested_source`. Some items are `future_data_needed`; this does not mean v1 should automatically collect or calculate them.

### 11.1 Shared Must-Track Indicators

| indicator | why_it_matters | current_status | affects_dimension | suggested_source |
| --- | --- | --- | --- | --- |
| AI datacenter-related revenue share | Determines whether the business is material rather than thematic. | Often missing or mixed with broader datacenter / infrastructure revenue. | classification, confidence, business realization | annual report, interim report, business composition |
| Datacenter customer revenue share | Shows direct exposure to datacenter customers. | Often unavailable. | confidence, customer quality | annual report, customer disclosures, investor Q&A |
| Major-customer concentration | High concentration can amplify customer capex-cycle and order-cut risk. | Partially available through top-five customer disclosures. | risk, revenue quality | annual report |
| Orders / backlog | Measures visibility of future delivery, when disclosed. | Often incomplete; must distinguish confirmed orders from inferred demand. | business realization, confidence | announcements, annual report, investor Q&A |
| Contract liabilities as partial proxy | May indicate prepayments but is not confirmed backlog. | Available in financial statements; v1 should not synthesize true backlog. | evidence quality, risk | financial statements |
| Order-to-delivery cycle | Determines whether orders can convert into revenue on schedule. | Usually not structured in current data. | realization, working capital | annual report, project disclosures |
| Gross margin | Reflects pricing, mix, technology route, and competition. | Usually available. | profitability, risk | financial statements |
| Operating cash flow | Tests whether revenue converts into cash. | Usually available. | revenue quality, cash conversion | cash-flow statement |
| Accounts receivable | Identifies collection pressure and customer payment cycle. | Usually available. | revenue quality, risk | balance sheet |
| Inventory | May signal stocking, delivery mismatch, or demand uncertainty. | Usually available. | working capital, realization risk | balance sheet |
| Capex | Observes capacity or infrastructure investment, not guaranteed revenue. | Usually available. | capacity cycle, cash flow | cash-flow statement, annual report |
| Capex conversion cycle | Tests whether investment has historically converted to revenue. | Future data needed; not a v1 automatic calculation. | realization, capital efficiency | annual report, historical financials |
| Construction-in-progress and expected completion | Shows committed expansion and timing uncertainty. | Often available, expected completion may be qualitative. | capacity release, risk | balance sheet, annual report |
| Historical capex-to-revenue conversion efficiency | Helps distinguish productive expansion from overbuild risk. | Future data needed; not a v1 automatic calculation. | capital efficiency, confidence | annual reports, financial statements |
| Customer capital-expenditure cycle | Datacenter demand depends on customer capex plans. | Often external and unstructured. | demand visibility, risk | customer filings, public capex guidance |
| Price-competition risk | Margin may compress as competition intensifies. | Event-driven and often qualitative. | gross margin, risk | company filings, industry news |

### 11.2 `datacenter_operator` Must-Track Indicators

| indicator | why_it_matters | current_status | affects_dimension | suggested_source |
| --- | --- | --- | --- | --- |
| Cabinet count | Base operating resource for IDC / AIDC revenue. | Sometimes disclosed, not always standardized. | classification, scale, confidence | annual report, investor presentation |
| MW scale | Power capacity is a more comparable datacenter resource metric. | Often disclosed selectively. | scale, capacity, confidence | annual report, project announcements |
| Rack-up rate / utilization | Determines whether built capacity is monetized. | Often missing; absence caps confidence. | operating efficiency, realization | annual report, investor Q&A |
| PUE | Measures energy efficiency and policy compliance. | Often missing. | operating efficiency, policy risk | annual report, ESG report |
| PUE trend | Shows whether energy efficiency is improving or deteriorating. | Future data needed. | operating risk, margin | ESG report, annual report |
| Average electricity price | Power cost can dominate IDC operating economics. | Usually not structured. | margin, risk | annual report, power-cost disclosures |
| Power cost / revenue | Tests sensitivity to energy prices and PUE. | Future data needed. | margin, operating risk | annual report, segment cost disclosure |
| PUE and power-cost linkage | Connects engineering efficiency with financial cost. | Future data needed; not v1 automatic calculation. | risk, profitability | ESG report, annual report |
| Revenue per cabinet | Helps test pricing and asset monetization. | Usually must be calculated when inputs exist; v1 should not infer if inputs are weak. | monetization, margin | segment revenue, cabinet count |
| Revenue per MW | Supports capacity monetization comparison. | Future data needed. | monetization, scale | segment revenue, MW disclosure |
| Customer contract term | Determines revenue visibility and renewal risk. | Often qualitative. | revenue visibility, risk | annual report, contract disclosures |
| Datacenter capex | Shows expansion intensity and future depreciation burden. | Usually partially available. | capex cycle, cash flow | cash-flow statement, annual report |
| Depreciation and amortization | Critical for asset-heavy operator profitability. | Usually available at company level; segment detail may be missing. | profitability, cash-flow quality | financial statements |
| EBITDA / EBITDA margin | Useful for IDC comparisons before depreciation distortion. | Future data needed. | profitability comparison | financial statements, company disclosure |
| Energy policy / power quota | Determines whether planned cabinets can actually operate. | Often qualitative or external. | capacity release, policy risk | annual report, policy documents |

### 11.3 `power_ups_infrastructure` Must-Track Indicators

| indicator | why_it_matters | current_status | affects_dimension | suggested_source |
| --- | --- | --- | --- | --- |
| Datacenter power / UPS revenue share | Separates datacenter power business from other power equipment. | Often mixed with broader power / energy revenue. | classification, confidence | business composition, annual report |
| Datacenter orders vs storage orders | Prevents storage / photovoltaic demand from being counted as datacenter demand. | Often incomplete. | classification, realization | announcements, annual report |
| UPS / distribution orders | Tests demand realization and delivery visibility. | Often incomplete. | realization, confidence | announcements, annual report |
| Datacenter customer revenue share | Shows direct customer exposure. | Often unavailable. | confidence, customer quality | annual report, customer disclosures |
| Customer structure | Distinguishes datacenter customers from storage / photovoltaic or industrial customers. | Often partly available. | classification, risk | annual report, customer disclosures |
| Storage / photovoltaic revenue share | Prevents misclassifying storage / photovoltaic main business as datacenter infrastructure. | Often available in segment revenue. | exclusion, boundary | business composition |
| UPS / distribution gross margin | Captures pricing and product-mix economics. | Segment detail may be missing. | profitability, risk | annual report, segment disclosure |
| Project acceptance and collection cycle | Equipment revenue quality depends on acceptance and payment timing. | Often qualitative. | realization, receivables | annual report, project disclosures |
| Project delivery cycle | Determines working-capital and revenue-recognition timing. | Usually qualitative. | realization, receivables | annual report, project disclosures |
| Accounts receivable | Equipment delivery may create collection pressure. | Usually available. | revenue quality, risk | balance sheet |

### 11.4 `cooling_liquid_cooling_infrastructure` Must-Track Indicators

| indicator | why_it_matters | current_status | affects_dimension | suggested_source |
| --- | --- | --- | --- | --- |
| Datacenter cooling revenue share | Separates datacenter thermal-control business from general HVAC. | Often mixed with broader thermal-control revenue. | classification, confidence | business composition, annual report |
| Liquid-cooling revenue share | Tests whether liquid-cooling exposure is realized rather than promotional. | Often missing. | realization, confidence | annual report, investor Q&A |
| Liquid-cooling technology route | Cold plate, immersion, and rear-door / backplate routes have different adoption risks. | Often qualitative. | product risk, margin | annual report, technical disclosures |
| Liquid-cooling certification stage | Separates testing / certification from commercial order realization. | Often qualitative. | realization, confidence | announcements, investor Q&A |
| Liquid-cooling customer validation stage | Customer validation is critical before scaled revenue recognition. | Often qualitative and selectively disclosed. | realization, confidence | announcements, investor Q&A |
| Liquid-cooling batch orders | Validates commercial conversion beyond testing. | Often incomplete. | order visibility, confidence | announcements, annual report |
| Liquid-cooling revenue recognition | Confirms that orders have converted into recognized revenue. | Often missing. | realization, revenue quality | annual report, segment disclosure |
| Ordinary air-conditioning / industrial thermal-control revenue share | Prevents generic HVAC exposure from being treated as AI datacenter infrastructure. | Often available only at coarse segment level. | classification, boundary | business composition |
| Gross margin | Shows mix, pricing, and competitive pressure. | Usually available. | profitability, risk | financial statements |
| Delivery cycle | Determines order conversion and receivables. | Usually missing or qualitative. | realization, cash conversion | annual report, project disclosures |

### 11.5 Boundary / Negative Must-Track Indicators

| indicator | why_it_matters | current_status | affects_dimension | suggested_source |
| --- | --- | --- | --- | --- |
| PCB / optical-module / server / chip revenue share | Confirms whether the company belongs to another AI supply-chain framework. | Usually available through business composition. | exclusion, routing | annual report, business composition |
| Self-built datacenter language | Distinguishes self-use infrastructure from monetized datacenter-operation service. | Often appears in business descriptions or project news. | exclusion | annual report, announcements |
| EPC / construction revenue share | Prevents project contractors from entering operator / equipment frameworks. | Usually available. | exclusion | business composition, annual report |
| Generic power-equipment revenue share | Prevents broad power equipment from being treated as datacenter-specific UPS. | Often available at coarse level. | exclusion, boundary | business composition |
| Military / defense system-integration exposure | Prevents defense procurement frameworks from being absorbed. | Often requires manual review. | exclusion | annual report, customer / industry description |
| More suitable framework exists | Prevents over-absorption by AI datacenter infrastructure. | Requires framework routing review. | classification, regression tests | classifier output, framework registry |
| Downstream supply-chain exposure only | Being used in AI datacenters is not the same as infrastructure operation or core facility support. | Often qualitative. | exclusion, report explanation | business description, segment revenue |

## 12. Readiness and Confidence Rules

Confidence represents evidence confidence in the current `fundamental_view`. It does not mean positive strength or investment attractiveness.

Score-semantics clarification:

- The AI datacenter boundary cap applies to `readiness_score`, not directly to final `fundamental_score`.
- Boundary samples that lack structured real order, customer, delivery, or sub-type revenue validation should have `readiness_score <= 39`, `readiness_level=insufficient`, and `confidence=low`.
- Final `fundamental_score` is still produced by the normal weighted scoring and result-assembly flow.
- When final `status=insufficient_data`, the final `fundamental_score` is capped by the general insufficient-data rule at `<= 50`.
- Therefore a boundary sample can correctly end with final `fundamental_score` in the 41-47 range when `status=insufficient_data` and `confidence=low`; this is not a violation of the `readiness_score <= 39` boundary cap.

General rules:

- Only `basic_info` plus financials: `max_confidence = low`.
- `business_composition` exists and datacenter revenue share is confirmable: `max_confidence = low_medium`.
- Orders / backlog proxy / customer-concentration evidence is partially available: confidence can reach `medium`.
- Customer validation, delivery progress, and operating-cash-flow matching are available: confidence can reach `medium_high`, but only cautiously.
- `high` confidence requires independently verifiable key operating indicators. Under public A-share disclosure conditions, this should be exceptional.
- News-only or concept-only support: classify as `theme_only` or `unknown`.
- PCB / optical-module / server / chip companies should not classify into this framework.

`datacenter_operator` rules:

- Missing cabinet count / MW / rack-up rate / PUE: `max_confidence = low_medium`.
- Missing power quota / energy-policy constraints / contract term: must not be `high`.
- Missing depreciation / amortization or EBITDA explanation: must not make high-confidence profitability comparisons.

`power_ups_infrastructure` rules:

- Datacenter power revenue cannot be separated from storage / photovoltaic revenue: `max_confidence = low`.
- Missing datacenter order and customer-structure evidence: must not be `high`.
- If contract liabilities are used as proxy evidence: must not be `high`.

`cooling_liquid_cooling_infrastructure` rules:

- Missing datacenter cooling revenue share: `max_confidence = low_medium`.
- Missing independently confirmed liquid-cooling revenue: do not conclude liquid-cooling scale-up.
- Missing liquid-cooling customer validation or batch orders: must not be `high`.

Readiness interpretation:

- `insufficient_data`: required financial or business-composition data is missing.
- `theme_only`: AI datacenter is mentioned, but no revenue, order, customer, asset, delivery, or operating evidence supports classification.
- `boundary_review`: adjacent or mixed business requires manual or evidence-based routing.
- `ready_low_confidence`: basic classification evidence exists, but critical confidence-gating indicators are missing.
- `ready_low_medium_confidence`: segment evidence exists but key operating or order evidence is weak.
- `ready_medium_confidence`: segment evidence plus partial order / customer / delivery evidence exists.
- `ready_medium_high_confidence`: material datacenter exposure plus customer validation, delivery progress, and cash-flow matching exist.
- `high_confidence`: rare exception requiring material datacenter revenue plus independently verifiable sub-type operating evidence, customer / order evidence, and cash-conversion checks.

## 13. AI Report Requirements

The AI report for this framework must explain:

- AI datacenter infrastructure is not the same as a generic AI computing-power supply chain.
- IDC operation, power / UPS infrastructure, and cooling / liquid cooling are different business models.
- Financial metrics can explain base operating quality, but cannot by themselves prove datacenter business realization.
- Missing datacenter revenue, orders, customers, delivery, utilization, or PUE means evidence is insufficient to judge realization.
- Contract liabilities are only an order-visibility proxy, not confirmed backlog.
- Capex is only an observation of capacity or infrastructure investment, not revenue certainty.
- Customer capital-expenditure expectations are not the same as company revenue.
- PCB, optical modules, servers, and chips must not be mixed with infrastructure operation or core facility support.
- Mixed storage / photovoltaic businesses must be separated from datacenter UPS / power business.
- Ordinary industrial HVAC must be separated from datacenter cooling / liquid cooling.
- Confidence is evidence confidence in the current `fundamental_view`, not a positive or negative investment signal.

The AI report must not output trading advice, technical analysis, target price, position sizing, timing advice, or account action.

## 14. Sample Design

### 14.1 Positive Samples

- `300442` 润泽科技: `datacenter_operator`; IDC / AIDC operator logic is more appropriate than generic equipment-chain growth logic. Cabinet / MW / utilization / PUE evidence remains confidence-gating.
- `002837` 英维克: `cooling_liquid_cooling_infrastructure`, conditional on verifiable datacenter cooling revenue share. Datacenter cooling / liquid cooling / precision thermal-control attributes are relevant, but liquid-cooling revenue, customer validation, orders, and delivery evidence remain confidence-gating.

### 14.2 Boundary / Mixed Samples

- `002335` 科华数据: `power_ups_infrastructure` / storage mixed boundary. UPS / datacenter power / IDC / new-energy business must be separated; do not treat storage orders as datacenter orders.
- `002518` 科士达: `power_ups_infrastructure` / optical-storage mixed boundary. Datacenter power and storage / photovoltaic business must be separated; confidence depends on segment evidence.
- `301018` 申菱环境: cooling / ordinary industrial thermal-control boundary. Treat as pending verification for datacenter cooling revenue share, customer contracts, and ordinary HVAC boundary.

### 14.3 Negative Samples

- `300476` 胜宏科技: AI PCB; do not classify into this framework.
- `300308` 中际旭创: optical modules; do not classify into this framework.
- `000063` 中兴通讯: communication equipment; do not classify into this framework unless future evidence proves a separate monetized datacenter-infrastructure business. Current sample status: pending verification.
- `002230` 科大讯飞: AI application software; do not classify into this framework unless future evidence proves a separate monetized datacenter-infrastructure business. Current sample status: pending verification.
- Generic power-equipment companies: pending verification; do not classify without datacenter-specific revenue, customer, or order evidence.
- Server OEM / chip / semiconductor companies: pending verification; do not classify into this framework.
- Internet cloud vendors with self-built datacenters: pending verification; do not classify if datacenters are mainly self-use infrastructure.
- EPC / construction companies: pending verification; do not classify only because they build datacenter projects.

Uncertain samples must be labeled as pending verification. They should not be written as confirmed facts without segment, customer, order, or operating evidence.

## 15. Implementation-Stage Recommendation

This design is suitable to enter a later implementation stage after review, with the following v1 scope.

Recommended v1 implementation scope:

- Classifier.
- `sub_type` routing.
- `industry_frameworks`.
- `data_requirements`.
- `analysis_context_rules`.
- Conservative scoring configuration.
- Evidence-pack must-track indicators.
- AI prompt constraints.
- Regression tests for positive, mixed-boundary, and negative samples.

Recommended v1 exclusions:

- External datacenter operation-data connector.
- Automated IDC cabinet / MW collection.
- PUE / utilization proxy.
- Automated liquid-cooling penetration collection.
- Customer capex data connector.
- Automatic backlog synthesis.
- Optical-module / PCB / server / chip frameworks.
- Technical analysis.
- `technical_skill`.
- `trader_skill`.
- Trading advice.

Implementation should proceed only after this design is accepted and should preserve the conservative confidence rules above.

## 16. Claude / Sonnet Audit Disposition

Adopted recommendations:

- Formal `sub_type` list reduced to three values.
- `ai_server_supply_chain_boundary` removed as a formal `sub_type`.
- PCB, optical modules, servers, and chips converted to negative / boundary regression samples.
- Priority rule versus `right_trend_growth` added.
- Mixed power / UPS and storage / photovoltaic boundary rules added.
- Cooling / liquid-cooling and ordinary HVAC boundary rules added.
- Additional high-risk misclassification boundaries added: self-built datacenters, EPC / construction, generic power equipment, and military / defense systems.
- Tier-1 structured keyword trigger added.
- Expanded confidence rules added for general and sub-type-specific cases.
- Future proxy rules documented without v1 calculation.
- Additional risk guards added for customer concentration, liquid-cooling route risk, power quota, depreciation / EBITDA, and certification versus batch orders.
- Expanded must-track indicators added as v1 evidence-pack or future-data-needed items.
- Sample design revised into positive, boundary / mixed, and negative groups.

Deferred recommendations:

- IDC rack-up / utilization proxy calculation.
- Liquid-cooling revenue-share proxy calculation.
- Backlog proxy synthesis.
- External datacenter operating-data connector.
- Customer capex connector.
- Automated PUE / utilization collection.
- Optical-module / PCB / server / chip frameworks.
