# Low Altitude Economy Infrastructure Framework Design Audit v1.1

Date: 2026-05-20

Revision basis:

- v1.0 design audit for `low_altitude_economy_infrastructure`.
- Independent Claude / Sonnet audit verdict: B, can enter implementation only after design revision.
- Low Altitude Economy Out-of-Sample Generalization Audit results for `000099`, `688631`, `688070`, `002085`, and `001696`.

Scope:

- Design-only revision for the proposed fundamental framework: `low_altitude_economy_infrastructure`.
- This stage modifies documentation only.
- No classifier, connector, deterministic pipeline, dashboard, scoring engine, code-level `strategy_type`, `technical_skill`, or `trader_skill` change is included.
- No trading advice, technical analysis, target price, position sizing, timing advice, or account action.

## 1. Revision Summary

The v1.0 design correctly identified a recurring framework gap, but it mixed two different operating models under one framework:

- `aviation_operations_service`: general aviation / low-altitude flight operation service, represented by `000099` 中信海直.
- `airspace_platform_system`: air traffic management / dispatch / platform system business, represented by `688631` 莱斯信息.

v1.1 keeps one durable `strategy_type`, but introduces `sub_type` routing metadata so framework logic, evidence pack requirements, must-track indicators, and confidence caps can differ by business model.

The design still rejects a broad "low-altitude economy concept stock" bucket. Drone OEMs, eVTOL OEMs, aviation engines, components, auto parts, policy themes, airport operators, and aviation leasing businesses must not be pulled into this framework only because they are adjacent to low-altitude economy.

## 2. Strategy Type Definition

`low_altitude_economy_infrastructure`

Revised definition:

This framework applies to companies whose core business model is low-altitude flight operation, general aviation operation service, low-altitude air traffic management / dispatch, ground support systems, city-level low-altitude operation platforms, takeoff / landing sites, bases, routes, or platform services, and whose low-altitude infrastructure or operation exposure can be verified through revenue, contracts, customers, assets, operating volume, or project acceptance evidence.

The framework monetizes infrastructure-like resources and operation services. It should be supported by recognized revenue, segment revenue, signed contracts, customer structure, operating assets, operating volume, project acceptance, cash conversion, or other public evidence of commercialization.

This is explicitly not:

- A low-altitude economy concept-stock framework.
- A drone OEM framework.
- An eVTOL OEM framework.
- An aviation engine framework.
- An aviation component framework.
- An auto parts plus low-altitude theme framework.
- A policy pilot theme framework.
- A traditional civil airport operator framework.
- An aviation leasing / aviation finance framework.

## 3. Sub-Type Architecture

`strategy_type` remains `low_altitude_economy_infrastructure`.

The framework should route each classified company into one of the following `sub_type` values, or equivalent routing metadata if implementation chooses not to add a first-class field:

### 3.1 `aviation_operations_service`

Business model:

- General aviation operation service.
- Low-altitude flight operation service.
- Flight service, route operation, base operation, emergency aviation rescue operation, patrol / logistics / inspection operation when monetized as service revenue.

Representative positive sample:

- `000099` 中信海直.

Core economics:

- Fleet scale.
- Aircraft type mix.
- Operating hours.
- Flight sorties.
- Revenue per flight hour.
- Depreciation / amortization.
- Safety incidents and regulatory risk.
- Operating cash flow.

### 3.2 `airspace_platform_system`

Business model:

- Air traffic management.
- Low-altitude dispatch.
- Command and dispatch platform.
- Ground support system.
- City-level low-altitude operation platform.
- Platform delivery and software / system service revenue tied to low-altitude infrastructure operation.

Representative positive sample:

- `688631` 莱斯信息.

Core economics:

- Contract amount.
- Contract backlog / on-hand contracts, clearly labeled as disclosed contracts rather than inferred backlog.
- Project acceptance progress.
- Customer structure.
- Collection cycle.
- Government project dependence.
- Platform service revenue share.
- R&D investment.

### 3.3 Sub-Type Guard

The framework must not mix sub-type indicators:

- Do not evaluate an air traffic / dispatch platform company with fleet operating-hour metrics.
- Do not evaluate an aviation operation company mainly with software project delivery indicators.
- Shared financial indicators can be used for base operating quality, but sub-type-specific must-track indicators and confidence gates must follow the routed `sub_type`.

## 4. Business Model Boundary

Should classify into `low_altitude_economy_infrastructure`:

- General aviation operation services.
- Low-altitude flight operation services.
- Low-altitude route / flight services.
- Aviation emergency rescue operation.
- City-level low-altitude operation platforms.
- Low-altitude air traffic management / command and dispatch platforms.
- Ground support systems.
- Takeoff / landing site, base, route, or route-resource operation.
- Low-altitude infrastructure businesses verifiable through revenue, contracts, customers, operating volume, project acceptance, operating assets, or cash-flow evidence.

Must not classify into this framework:

- Drone OEMs.
- eVTOL OEMs.
- Flying-car manufacturing.
- Aviation engines.
- Aviation components.
- Sensors, materials, battery, or other component supply chains.
- Auto parts companies with low-altitude theme exposure.
- Drone mapping software.
- Remote-sensing software.
- Defense electronics.
- Traditional civil airport passenger / cargo throughput operators.
- Aircraft leasing or aviation finance companies.
- Pure policy, announcement, strategic cooperation, concept, investor-relations, or news popularity exposure.
- Companies with no low-altitude revenue, contract, operation asset, project acceptance, cash-flow, or operating-volume evidence.

Boundary principle:

- Classification must be based on business model and monetization evidence, not theme adjacency.
- Manufacturing is not infrastructure operation.
- Policy pilots are not commercial revenue.
- Strategic cooperation is not realized contract income.
- Contract liabilities may be an order-visibility proxy, but not true backlog.

## 5. Structured Positive Keyword Design

Positive keywords must be interpreted through Tier-1 AND logic. A company that only mentions "low-altitude economy" but does not pass Tier-1 verification should default to `theme_only` or `unknown`.

### 5.1 Tier-1: `aviation_operations_service`

Trigger requires:

```text
("通航运营" OR "低空飞行服务" OR "通航运输" OR "航空应急救援")
AND
("收入" OR "运营小时" OR "飞行架次" OR "机队" OR "客户合同")
```

English equivalents can be used when source text is translated:

```text
("general aviation operation" OR "low-altitude flight service" OR "general aviation transportation" OR "aviation emergency rescue")
AND
("revenue" OR "operating hours" OR "flight sorties" OR "fleet" OR "customer contract")
```

### 5.2 Tier-1: `airspace_platform_system`

Trigger requires:

```text
("空中交通管理" OR "空管系统" OR "低空调度" OR "低空运行平台" OR "指挥调度平台")
AND
("合同" OR "项目验收" OR "客户" OR "收入" OR "平台交付")
```

English equivalents can be used when source text is translated:

```text
("air traffic management" OR "air traffic control system" OR "low-altitude dispatch" OR "low-altitude operation platform" OR "command dispatch platform")
AND
("contract" OR "project acceptance" OR "customer" OR "revenue" OR "platform delivery")
```

### 5.3 Supporting Positive Keywords

Supporting positive keywords can raise review priority but cannot classify without Tier-1 evidence:

- 低空运营
- 低空航线
- 飞行服务站
- 起降点
- 通航机场
- 低空基础设施
- 城市低空运行
- 低空物流运营
- 低空巡检服务
- 地面保障系统

## 6. Negative / Exclusion Logic

Negative exclusion keywords:

- 无人机整机
- eVTOL 整机
- 飞行汽车制造
- 航空发动机
- 航空零部件
- 汽车零部件
- 电池
- 传感器
- 复合材料
- 测绘软件
- 遥感软件
- 军工电子
- 民航机场
- 航空租赁
- 航空金融
- 仅政策试点
- 仅战略合作
- 仅概念新闻

Quantitative or quasi-quantitative exclusion rules:

- If low-altitude / general aviation / air traffic management related revenue share is below 20%, and there is no explicit contract, operation asset, project acceptance, or operating-volume evidence, do not classify into this framework.
- If traditional main business revenue share is above 60%, such as auto parts, aviation engines, drone manufacturing, defense, materials, batteries, or components, force a boundary check.
- If the main business is civil aviation passenger / cargo throughput airport operation, exclude.
- If the main business is aircraft leasing or aviation finance, exclude.
- If the main business is drone crop protection, agricultural plant protection, remote sensing, or mapping service, exclude or mark as a potential independent future framework; do not classify into this framework.
- If low-altitude exposure appears only in news, announcements, policy language, or strategic cooperation, default to `theme_only`.
- Existing `resource_swing`, `semiconductor_cycle`, `advanced_manufacturing_growth`, `right_trend_growth`, and `defense` should not catch low-altitude theme exposure by default.

## 7. Samples

### 7.1 Positive Samples

- `000099` 中信海直: `sub_type=aviation_operations_service`; close fit because the audit found general aviation transportation revenue ratio of 99.13%; regression: yes.
- `688631` 莱斯信息: `sub_type=airspace_platform_system`; close fit because the audit found civil aviation air traffic management revenue ratio of 50.69%; regression: yes.

Positive samples should still carry conservative confidence if sub-type-specific operating indicators are missing.

### 7.2 Negative Samples

- `688070` 纵横股份: drone OEM and industry application; exclude from this framework; regression: yes.
- `002085` 万丰奥威: auto parts main business plus eVTOL / general aviation aircraft manufacturing theme; exclude from this framework; regression: yes.
- `001696` 宗申动力: aviation engine / machinery component boundary sample; exclude from this framework; regression: yes.
- `600967` 中航沈飞: defense aircraft OEM; exclude from this framework; regression: yes if included in A-share regression set.
- `002895` 中科星图: remote-sensing data / software; exclude from this framework; regression: yes if included.
- EHang Holdings / 亿航智能: eVTOL OEM; cross-market design reference only, not mandatory for A-share regression.

### 7.3 Boundary Samples

- Companies only mentioned in low-altitude economy news but unsupported by main business should be `theme_only` or `unknown`.
- Diversified companies with low-altitude revenue below 20% require boundary checks and should not auto-classify.

## 8. Data Requirements

Many operating data points are not disclosed consistently in public filings. v1 must not force proxy calculations. Missing values should be reported as `current_status=missing` and should cap confidence.

### 8.1 Shared Required Data

- `basic_info`.
- `business_composition`.
- `low_altitude_revenue` or general aviation / low-altitude / air traffic management related revenue.
- revenue / profit / gross_margin.
- operating_cashflow.
- accounts_receivable.
- contract_liabilities.
- valuation.

Shared required data is enough to support business-model review when main business and segment evidence are clear. It is not enough for high confidence.

### 8.2 `aviation_operations_service` Required / Gating Data

- Fleet scale.
- Aircraft type mix.
- Operating hours.
- Flight sorties.
- Revenue per flight hour, if disclosed.
- Depreciation / amortization.
- Safety incidents / regulatory penalties.
- Operating qualifications / airspace resources.

### 8.3 `airspace_platform_system` Required / Gating Data

- Contract amount.
- On-hand contracts / disclosed contract backlog.
- Project acceptance progress.
- Customer structure.
- Accounts receivable / collection cycle.
- Software service revenue share.
- R&D expense ratio.
- Government project dependence.

### 8.4 Preferred Data

Shared preferred data:

- Contract duration structure.
- Customer renewal rate.
- Single-customer revenue share.
- Evidence that policy pilots converted into commercial orders.
- Low-altitude business cash-flow contribution.
- Accounts receivable and contract liabilities matching by project / customer.
- Customer type split: government, SOE, civil aviation, city governance, industrial customer, logistics customer, emergency rescue customer.

`aviation_operations_service` preferred data:

- Fleet average age.
- Aircraft utilization rate.
- Route / base utilization.
- Maintenance cost and downtime.
- Accident and safety-management disclosure.

`airspace_platform_system` preferred data:

- Project-level acceptance milestones.
- Platform delivery schedule.
- Recurring software / maintenance revenue.
- Renewal rate or service continuation.
- Government project revenue share.

### 8.5 Optional Data

- Policy projects.
- Demonstration zone progress.
- Major customer announcements.
- Operating safety events.
- Flight accidents.
- Regulatory penalties.
- Airspace or route policy changes.
- Public disclosure of platform traffic, route openings, or service coverage.

Optional data should be labeled as context unless it is tied to revenue, contracts, assets, operating volume, project acceptance, or cash flow.

## 9. Proxy Rules: Record Only, Do Not Implement in v1

Future proxy candidates:

- Operating-hours proxy.
- Revenue per flight hour proxy.
- Platform dispatch volume proxy.

v1 must not calculate these proxies.

Reasons:

- Public disclosure is unstable.
- Proxy error can be large.
- Early low-altitude commercialization is not suitable for pseudo-precision.
- If a proxy is ever used, it must be labeled and should lower confidence rather than upgrade it.

Contract liabilities, capex, and policy pilots are also proxy-like context and must not be presented as direct proof of backlog, utilization, or realized revenue.

## 10. Interpretation Guards

| Evidence / field | Interpretation guard |
| --- | --- |
| low-altitude theme keywords | Theme exposure is not realized revenue. |
| policy pilot / demonstration zone | Policy support is not commercial income. |
| strategic cooperation | Cooperation intent is not a signed contract or recognized revenue. |
| contract_liabilities | Proxy for order visibility or prepayment only; not true backlog. |
| business_composition | Segment revenue supports business-model classification, but does not prove utilization, demand stability, or project acceptance. |
| operating_cashflow | Cash-flow quality must be interpreted with receivables and contract liabilities. |
| accounts_receivable | High receivables may indicate collection pressure even when revenue is recognized. |
| valuation | PE / PB / PS are context only and do not prove low-altitude realization. |
| capex | Capex may show asset construction or service capability, but not utilization or revenue certainty. |
| news / announcements | News is optional context, not primary classification evidence. |
| eVTOL certification or commercialization timeline | Certification expectation is not current-period revenue evidence. |
| low-altitude airspace reform policy | Policy expectation is not actual company-level usable airspace expansion. |

## 11. Risk Guards

Risk guards required for v1:

1. Do not treat low-altitude economy theme exposure as performance realization.
2. Do not treat policy pilots or demonstration zones as commercial revenue.
3. Do not treat strategic cooperation or intent orders as signed contract revenue.
4. Do not treat contract liabilities as true backlog.
5. Do not classify drone OEMs, eVTOL OEMs, aircraft OEMs, aviation engines, aviation components, or auto parts companies into this infrastructure operation framework only because of theme exposure.
6. If low-altitude revenue share is missing, do not assert low-altitude business has become the main business.
7. If operating hours, flight sorties, or dispatch volume are missing, do not assert operating efficiency or demand stability.
8. If customer structure is missing, do not assert demand stability or high collection quality.
9. If project acceptance and collection data are missing, do not assert order realization.
10. If the main business is not low-altitude infrastructure / operation service, force a business-model boundary check.
11. Existing `resource_swing`, `semiconductor_cycle`, and `advanced_manufacturing_growth` frameworks should not catch low-altitude economy theme exposure by default.
12. Label all proxies clearly in evidence pack and AI report.
13. Keep confidence conservative when framework-specific operating indicators are missing.
14. Safety incident / regulatory penalty mandatory flag: if flight accidents, CAAC penalties, grounding rectification, or airspace control events appear, explicitly mark them as major operating risks.
15. Policy-dependence risk: if government projects or policy pilot revenue share is high, mark policy dependence and do not directly infer revenue stability.
16. eVTOL commercialization timeline risk: do not treat airworthiness certification expectations or commercialization schedules as current-period revenue evidence.
17. Low-altitude airspace reform uncertainty: do not treat airspace reform policy expectations as actual expansion of company-usable airspace.
18. Sub-type mixing warning: do not use aviation operation metrics to evaluate airspace platform companies, and do not use platform contract metrics to evaluate aviation operation companies.
19. Airport operator / aviation leasing exclusion: do not classify traditional airport operation or aviation finance leasing into this framework.

Risk guards should limit unsupported interpretation. They should not become optimistic scoring boosts.

## 12. Must-Track Indicators

Each must-track indicator should appear in the evidence pack with `why_it_matters`, `current_status`, `affects_dimension`, and `suggested_source`. If the current pipeline cannot retrieve a reliable value, `current_status` should be `missing`, `available`, `proxy_available`, or `future_data_needed`.

EBITDA, EBITDA margin, depreciation / amortization, and similar fields may enter must-track indicators or data limitations in v1, but must not enter v1 scoring.

### 12.1 Shared Must-Track Indicators

| indicator | why_it_matters | current_status | affects_dimension | suggested_source |
| --- | --- | --- | --- | --- |
| low-altitude business revenue share | Separates real business contribution from theme exposure. | missing unless disclosed in segment revenue | classification_quality, growth_realization | business_composition; annual report segment notes |
| accounts receivable | Indicates collection pressure and project payment quality. | available when financials succeed | cash_conversion, credit_risk | balance sheet; financial indicators |
| contract liabilities | Proxy for order visibility, but not true backlog. | available when financials succeed | order_visibility_proxy, working_capital | balance sheet; financial indicators |
| operating cash flow | Tests whether recognized revenue converts into cash. | available when financials succeed | cashflow_quality, financial_quality | cash flow statement; financial indicators |
| low-altitude business gross margin | Shows segment economics and pricing / cost structure. | missing unless disclosed by segment | margin_quality, pricing_power | business_composition; annual report segment notes |
| customer structure | Tests demand stability, concentration, payment quality, and policy dependence. | missing | customer_risk, cashflow_quality | annual report top-five customer disclosure; segment notes |
| policy pilot to commercial order evidence | Prevents treating policy pilot as revenue realization. | missing | theme_to_revenue_validation | announcements; annual report; project contracts |
| operating safety events / accidents / regulatory penalties | Captures safety, compliance, and service continuity risks. | missing | regulatory_risk, operating_risk | company announcements; regulator disclosures; news context |

### 12.2 `aviation_operations_service` Must-Track Indicators

| indicator | why_it_matters | current_status | affects_dimension | suggested_source |
| --- | --- | --- | --- | --- |
| fleet scale | Defines operating capacity and capital intensity. | missing | capacity, asset_base | annual report; company disclosures |
| aircraft type mix | Determines mission coverage, pricing, cost, and depreciation profile. | missing | capacity_mix, margin_quality | annual report; fleet disclosure |
| fleet average age | Indicates maintenance burden, replacement cycle, and safety risk. | missing | asset_life, maintenance_risk | annual report; fleet disclosure |
| operating hours | Measures utilization and demand realization. | missing | operating_efficiency, demand_validation | annual report; operating data |
| flight sorties | Measures actual service volume. | missing | operating_volume, demand_validation | annual report; operating data |
| revenue per flight hour | Measures pricing and service monetization efficiency. | missing; future_data_needed | pricing_power, operating_efficiency | calculated only if reliable revenue and hours are disclosed |
| depreciation / amortization | Captures fleet asset consumption and reported profit pressure. | missing; future_data_needed | profit_quality, asset_life | cash flow statement; financial statement notes |
| EBITDA / EBITDA margin | Helps separate operating earnings from depreciation effects for asset-heavy operators. | future_data_needed | operating_profitability, depreciation_context | calculated metric; not v1 scoring |
| operating qualifications / airspace resources | Determines whether the company controls scarce permissions. | missing | license_barrier, resource_access | regulator filings; company disclosures |
| takeoff / landing sites, bases, route resources | Defines infrastructure footprint and route-service capacity. | missing | asset_base, coverage, capacity | annual report; company website; project disclosures |

### 12.3 `airspace_platform_system` Must-Track Indicators

| indicator | why_it_matters | current_status | affects_dimension | suggested_source |
| --- | --- | --- | --- | --- |
| total on-hand contract amount | Indicates revenue visibility when disclosed. | missing | revenue_visibility, growth_validation | announcements; annual report; exchange filings |
| contract delivery cycle | Shows whether contracts can convert into revenue on schedule. | missing | project_delivery, revenue_recognition | annual report; project disclosures |
| project acceptance progress | Determines whether delivered systems are accepted and revenue-recognizable. | missing | revenue_recognition, order_realization | project acceptance announcements; annual report |
| platform dispatch volume | Measures platform usage and monetization potential. | missing; future_data_needed | platform_utilization, demand_validation | platform disclosures; project reports |
| software service revenue share | Separates recurring / service revenue from one-time system integration. | missing | revenue_quality, margin_quality | business_composition; annual report segment notes |
| R&D expense ratio | Indicates platform and system development intensity. | available when financials succeed | technology_investment, growth_validation | financial indicators |
| customer renewal rate | Helps judge recurring demand and service durability. | missing | demand_stability, revenue_visibility | annual report; customer disclosures |
| government project dependence | Identifies policy and public-budget dependence. | missing | policy_dependence, collection_risk | customer disclosures; annual report |
| project collection cycle | Tests whether project revenue is collectible and repeatable. | missing | cash_conversion, project_risk | receivable aging; annual report notes |

## 13. Readiness / Confidence Rules

`confidence` means confidence in the evidence quality of the current `fundamental_view`. It does not mean positive fundamental strength, valuation attractiveness, or upside.

Shared conservative rules:

- Only `basic_info` + financials: `max_confidence = low`.
- `business_composition` is present and low-altitude / general aviation / air traffic management related revenue share is confirmable: `max_confidence = low_medium`.
- If only news, policy, or strategic cooperation supports low-altitude exposure: classify as `theme_only` or `unknown`, with `low` confidence.
- If the main business is drone OEM, eVTOL OEM, aviation engine, aviation component, auto parts, airport operation, aviation leasing, mapping software, remote-sensing software, or defense electronics: do not classify into `low_altitude_economy_infrastructure`.

`aviation_operations_service` confidence caps:

- If operating hours, flight sorties, and fleet scale are all missing: `max_confidence = low_medium`.
- If operating hours or flight sorties are available, but customer structure and safety-event records are missing: `max_confidence = medium`.
- `high` confidence requires relatively complete operating volume, customer structure, operating qualifications / airspace resources, and safety records.

`airspace_platform_system` confidence caps:

- If contract amount, project acceptance, and customer structure are all missing: `max_confidence = low_medium`.
- If contract amount is available but collection / acceptance evidence is missing: `max_confidence = medium`.
- `high` confidence requires relatively complete contract amount, project acceptance, customer structure, collection data, and government-dependence risk evidence.

Suggested confidence cap table:

| Available evidence | Suggested readiness | Maximum confidence |
| --- | --- | --- |
| News-only low-altitude theme | `theme_only` or `unknown` | low |
| `basic_info` + financials only | weak business context only | low |
| `business_composition` present, low-altitude / general aviation / air traffic management share confirmable | framework review usable | low_medium |
| `aviation_operations_service` with revenue evidence but missing fleet / hours / sorties | framework usable with warnings | low_medium |
| `aviation_operations_service` with operating hours or sorties but missing customer and safety data | partial operating context | medium |
| `airspace_platform_system` with revenue evidence but missing contract / acceptance / customer data | framework usable with warnings | low_medium |
| `airspace_platform_system` with contract amount but missing collection / acceptance | partial project context | medium |
| Required data plus sub-type-specific operating, customer, acceptance, cash conversion, and safety / compliance checks | mature evidence | medium / high, with high rare under public A-share data constraints |

Status guidance:

- `insufficient_data`: use when main business or revenue composition cannot support the framework, or when required evidence is missing.
- `neutral`: use when the business model is supported but low-altitude-specific operating indicators are incomplete.
- `theme_only`: use when news or policy wording exists but main business and revenue evidence do not support the framework.
- `unknown`: use when neither framework fit nor theme-only exposure can be established.

## 14. Scoring Notes

v1 scoring should be conservative:

- Business-model classification should be driven by `basic_info`, `business_composition`, and sub-type routing evidence.
- Revenue, gross margin, operating cash flow, accounts receivable, contract liabilities, and R&D expense ratio may support financial-quality interpretation.
- Low-altitude-specific revenue share, contract evidence, customer structure, operating volume, project acceptance, safety record, and collection quality should primarily gate confidence.
- Contract liabilities should be treated as proxy evidence, not confirmed backlog.
- Missing low-altitude-specific operating indicators should cap confidence rather than mechanically penalize score.
- Valuation fields should be context only and must not drive classification.
- Policy, news, strategic cooperation, certification expectations, and demonstration-zone exposure should not enter positive scoring unless tied to revenue, contracts, customers, assets, operating volume, project acceptance, or cash flow.
- EBITDA, EBITDA margin, depreciation / amortization, and proxy-derived metrics are v1 must-track / data-limitation candidates only; they must not enter v1 scoring.
- No technical indicators, trading timing logic, account actions, or trader-facing execution guidance.

## 15. Evidence Pack Requirements

The evidence pack should expose:

- Current `strategy_type`, `sub_type` or equivalent routing metadata, status, confidence, and confidence cap reason.
- Positive classification evidence from `basic_info` and `business_composition`.
- Tier-1 trigger result for `aviation_operations_service` or `airspace_platform_system`.
- Negative / exclusion signals when manufacturing, components, airport operation, aviation leasing, software, defense, or theme-only evidence dominates.
- Required / preferred / optional data availability.
- Low-altitude revenue share when available, otherwise explicit missing status.
- Sub-type-specific must-track indicators.
- Contract amount, project acceptance, customer structure, operating hours, flight sorties, dispatch volume, bases / routes / coverage, qualifications, airspace resources, safety events, and policy-dependence status.
- Proxy labels for contract liabilities, policy pilots, strategic cooperation, capex, and any future proxy candidates.
- Risk guard triggers.
- Source trace for each evidence block.

The evidence pack must support conservative AI reporting without inviting unsupported claims.

## 16. AI Report Requirements

AI reports for `low_altitude_economy_infrastructure` must explain:

- Low-altitude economy is not a single industry; it is an industrial cluster.
- This framework covers only low-altitude infrastructure / operation services.
- The report must state the routed `sub_type` when available and use the correct sub-type logic.
- Financial metrics can explain base operating quality only.
- Missing low-altitude revenue, contracts, customers, operating volume, project acceptance, utilization, or safety / compliance evidence means there is insufficient evidence to judge low-altitude business realization.
- Contract liabilities are only an order-visibility proxy.
- Policy pilots and strategic cooperation do not prove commercial maturity.
- eVTOL airworthiness certification expectations and commercialization timelines do not prove current-period revenue realization.
- Low-altitude airspace reform policy does not prove actual company-level usable airspace expansion.
- Drone OEM, eVTOL OEM, aviation components, auto parts, airport operation, aviation leasing, and low-altitude operation service must not be mixed together.
- The report must not output trading advice, target prices, position sizing, timing advice, account actions, or technical analysis.

Suggested AI report quality guards:

- Theme-as-realization guard.
- Proxy-as-fact guard.
- Manufacturing-vs-operation boundary guard.
- Sub-type-mixing guard.
- Unsupported-certainty guard.
- Safety / regulatory-event guard.
- Schema / safety / garbled-text guard.

## 17. Regression Test Plan

Positive:

- `000099`: expected `strategy_type=low_altitude_economy_infrastructure`; expected `sub_type=aviation_operations_service`; expected status `neutral` or `insufficient_data` depending on available operating indicators; expected confidence `low` or `low_medium`; must include fleet / operating-hour / flight-sortie / safety must-track indicators.
- `688631`: expected `strategy_type=low_altitude_economy_infrastructure`; expected `sub_type=airspace_platform_system`; expected status `neutral` or `insufficient_data`; expected confidence `low` or `low_medium`; must include contract / acceptance / customer / collection / R&D must-track indicators.

Negative:

- `688070`: expected `strategy_type != low_altitude_economy_infrastructure`; reason: drone OEM / industry application, not infrastructure operation.
- `002085`: expected `strategy_type != low_altitude_economy_infrastructure`; reason: auto parts main business plus aircraft manufacturing / eVTOL theme, not infrastructure operation.
- `001696`: expected `strategy_type != low_altitude_economy_infrastructure`; reason: aviation engine / machinery component exposure, not infrastructure operation.
- `600967`: expected `strategy_type != low_altitude_economy_infrastructure`; reason: defense aircraft OEM.
- `002895`: expected `strategy_type != low_altitude_economy_infrastructure`; reason: remote-sensing data / software.

Cross-market design reference:

- EHang Holdings / 亿航智能: eVTOL OEM; should be excluded conceptually, but is not mandatory for A-share regression.

Boundary:

- News-only low-altitude economy mention: expected `theme_only` or `unknown`.
- Diversified company with low-altitude revenue below 20% and no contracts / assets / acceptance evidence: boundary check, no automatic classification.

Drift-sensitive existing frameworks:

- Existing `semiconductor_cycle` samples should not drift because low-altitude drone / component keywords appear.
- Existing `resource_swing` samples should not absorb low-altitude manufacturing or theme samples.
- Existing `advanced_manufacturing_growth` samples should not become a catch-all for eVTOL / drone / component theme exposure.
- Existing `defense` samples should not classify into this framework only because of aviation or low-altitude keywords.
- Existing `satellite_communication_infrastructure` samples should remain unchanged.

AI / safety checks:

- AI report schema passes.
- Safety check passes.
- No trading advice.
- No technical analysis.
- No theme-as-realization language.
- Proxy fields are labeled.
- Sub-type is not mixed.

## 18. v1 Implementation Scope

When implementation is explicitly authorized, v1 may include:

- Classifier rules for `low_altitude_economy_infrastructure`.
- `sub_type` field or equivalent routing metadata.
- Industry framework definitions / configuration.
- Data requirements and readiness rules.
- Analysis context rules and conservative confidence caps.
- Conservative scoring configuration.
- Evidence pack framework-specific and sub-type-specific must-track indicators.
- AI report prompt constraints and interpretation guards.
- Positive and negative regression tests.
- Schema changes only if required by the accepted implementation plan.

Implementation must be traceable to this design audit and should remain narrow.

## 19. Deferred / Not-in-v1 Items

v1 must not implement:

- Low-altitude external operating data connector.
- Real-time operating hours / flight sorties collection.
- Airspace / route data ingestion.
- Proxy calculations.
- eVTOL OEM framework.
- Drone OEM framework.
- Aviation component framework.
- EBITDA scoring.
- Trading account integration.
- Technical analysis.
- `technical_skill`.
- `trader_skill`.
- Trading advice.

Deferred because of scope control and public-data availability:

- Project-level low-altitude economics.
- Detailed route utilization datasets.
- Real-time platform dispatch volume.
- Airspace resource database integration.
- Safety incident database automation.
- Peer valuation model for low-altitude operation platforms.
- Operating-hours proxy, revenue-per-flight-hour proxy, and platform-dispatch-volume proxy.

## 20. Accepted Claude / Sonnet Suggestions

Accepted:

- Introduce `sub_type` architecture while keeping one `strategy_type`.
- Split business logic into `aviation_operations_service` and `airspace_platform_system`.
- Revise the definition to include operating volume and project acceptance evidence.
- Strengthen classification boundary with airport operator and aviation leasing exclusions.
- Add Tier-1 AND keyword logic.
- Add quantitative / quasi-quantitative exclusion rules: below 20% related revenue without support excludes; above 60% traditional main business forces boundary check.
- Split data requirements and must-track indicators by sub-type.
- Add safety incident, regulatory penalty, policy-dependence, eVTOL commercialization-timeline, airspace reform, sub-type-mixing, airport, and leasing risk guards.
- Quantify confidence caps by sub-type.
- Record future proxy candidates but keep them out of v1 implementation.
- Add `600967`, `002895`, and EHang / 亿航智能 as negative or reference samples.
- Adjust v1 implementation scope to include `sub_type` routing metadata and exclude proxy calculations / EBITDA scoring.

## 21. Deferred Claude / Sonnet Suggestions

Deferred:

- Implementing external low-altitude operating data connectors.
- Calculating operating-hours, revenue-per-flight-hour, or platform-dispatch-volume proxies.
- Adding EBITDA or EBITDA margin to scoring.
- Adding separate eVTOL OEM, drone OEM, or aviation component frameworks.
- Using cross-market EHang / 亿航智能 as mandatory A-share regression.
- Treating unstable operating data as required hard fields in v1.

Reasons:

- Public data disclosure is unstable.
- Proxy error is high during early commercialization.
- v1 should avoid pseudo-precision.
- The accepted workflow requires design approval before code changes.

## 22. Acceptance Criteria

The framework can enter implementation only after design review accepts these v1.1 boundaries.

Implementation acceptance criteria:

- `000099` classifies correctly with `sub_type=aviation_operations_service` when evidence supports the business model.
- `688631` classifies correctly with `sub_type=airspace_platform_system` when evidence supports the business model.
- `688070`, `002085`, `001696`, `600967`, and `002895` do not classify into the framework.
- Close negative samples with low-altitude theme exposure are excluded.
- News-only and policy-only samples are `theme_only` or `unknown`.
- Existing `resource_swing`, `semiconductor_cycle`, `advanced_manufacturing_growth`, `defense`, and `satellite_communication_infrastructure` samples do not drift unexpectedly.
- Confidence remains conservative when sub-type-specific operating indicators are incomplete.
- Theme-only and proxy-only evidence triggers guards.
- Contract liabilities are labeled as proxy, not backlog.
- Must-track indicators are framework-specific and sub-type-specific.
- Evidence pack supports the AI report.
- AI report passes schema, safety, and quality checks.
- No trading advice is produced.
- No technical analysis is introduced.
- `pytest` and regression suite pass when code changes are made in a later stage.

Documentation-only note:

- This v1.1 design revision does not require tests because it changes documentation only.
