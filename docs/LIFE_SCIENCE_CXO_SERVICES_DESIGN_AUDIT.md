# Life Science CXO Services Framework Design Audit v1.1

Date: 2026-05-20

Revision basis:

- v1.0 design audit for `life_science_cxo_services`.
- Independent Claude / Sonnet audit verdict: B, can enter implementation only after design revision.
- Life Science CXO Services Out-of-Sample Generalization Audit results for `603259` Wuxi AppTec, `300759` Pharmaron, `002821` Asymchem, `300347` Tigermed, and `300363` Porton Pharma Solutions.
- Current system classified all five samples as `unknown` with `status=insufficient_data` and `confidence=low`.
- The current conservative behavior is acceptable: it did not misclassify CXO / CRO / CDMO companies into generic growth, manufacturing, or theme frameworks, and did not overstate confidence.

Scope:

- Design-only revision for the proposed fundamental framework: `life_science_cxo_services`.
- This stage modifies this documentation file only.
- No classifier, connector, deterministic pipeline, dashboard, scoring engine, code-level `strategy_type`, `technical_skill`, or `trader_skill` change is included.
- No trading advice, technical analysis, target price, position sizing, timing advice, or account action.

## 1. Strategy Type Definition

`life_science_cxo_services`

This framework applies to companies whose revenue mainly comes from life-science R&D and manufacturing outsourcing services, including drug discovery services, preclinical research, clinical CRO, SMO, data/statistical services, CMC, CDMO, process development, formulation development, API CDMO, small-molecule CDMO, large-molecule CDMO, commercial manufacturing outsourcing, and integrated pharmaceutical R&D/manufacturing outsourcing platforms.

The core value drivers are not self-owned innovative drug pipelines. They are global pharmaceutical, biotech, and healthcare customers' outsourcing demand, order visibility, customer structure, delivery capability, compliance capability, capacity utilization, overseas revenue exposure, regulatory risk, geopolitical risk, cash conversion, and project execution.

This is explicitly not:

- An innovative drug pipeline company framework.
- A generic API / formulation manufacturing framework.
- A medical device framework.
- A pharmaceutical distribution framework.
- A hospital / medical service framework.
- A TCM, consumer healthcare, medical aesthetics, or drugstore framework.
- A generic testing / inspection laboratory framework.
- An AI drug-discovery software or SaaS framework.
- A theme framework triggered only by news mentions of "pharmaceutical R&D", "CRO", "CDMO", "R&D cooperation", or "pharmaceutical outsourcing".

## 2. Quantitative Classification Threshold

Classification into `life_science_cxo_services` should be centered on the revenue share of CXO / CRO / CDMO / CMC / clinical research / pharmaceutical R&D and manufacturing outsourcing services.

Recommended threshold:

- CXO/CRO/CDMO-related revenue share `>= 50%`: candidate can be directly routed into this framework, subject to exclusion guards and evidence quality.
- CXO/CRO/CDMO-related revenue share `30% - 50%`: enter boundary review; do not classify automatically.
- CXO/CRO/CDMO-related revenue share `< 30%`: default to not classify, unless there is very clear business transformation evidence plus revenue evidence.
- If revenue share cannot be confirmed, positive keyword hits should lower confidence or keep the company as `unknown` / `theme_only`.

Hard rule:

- Do not classify into this framework only because a company mentions CRO/CDMO, R&D cooperation, pharmaceutical outsourcing, clinical collaboration, or pharmaceutical R&D in news, announcements, or investor-relations text.

## 3. Mixed CXO and Innovative Drug Business Rule

Some companies may have both CXO outsourcing services and self-owned innovative drug pipelines.

Rules:

- If CXO-related revenue share is `>= 50%`, the company can classify into `life_science_cxo_services`.
- The evidence pack and AI report must label: "mixed business model; self-owned innovative drug pipeline progress is outside this framework's evaluation scope."
- Do not treat innovative drug pipeline progress as CXO business realization.
- Do not treat CXO service capability as proof of self-owned drug R&D success probability.
- If self-owned pipeline / drug sales dominate revenue, the company should not be classified into this framework even if it has a CXO subsidiary or R&D service exposure.

## 4. Sub-Type Architecture

Recommendation: v1 should introduce `sub_type`, or equivalent routing metadata, under one durable `strategy_type=life_science_cxo_services`.

Reason:

- CXO companies share outsourcing-service economics, but their key operating indicators differ materially.
- Integrated platforms should be evaluated by business mix, active customers, segment revenue, major-customer changes, overseas exposure, and personnel efficiency.
- CDMO-heavy companies require order, capacity utilization, commercial project, capex, gross margin, compliance, and customer-concentration gates.
- Clinical CRO companies require clinical project count, project progress, SMO / data service revenue, hospital / site coverage, delivery, cancellation, and collection-cycle gates.
- Without `sub_type`, v1 risks either using overly generic must-track indicators or applying CDMO manufacturing indicators to clinical CRO companies.

The proposed `sub_type` values are:

### 4.1 `integrated_cxo_platform`

Representative positive samples:

- `603259` Wuxi AppTec.
- `300759` Pharmaron.

Business model:

- Integrated life-science outsourcing platform covering drug discovery, preclinical research, CMC/CDMO, and multiple R&D/manufacturing service lines.

Core economics:

- Segment revenue by drug discovery, preclinical, clinical, CMC/CDMO, and commercial manufacturing.
- Customer count and active customer quality.
- Major-customer changes.
- Overseas revenue exposure and U.S. / North America customer exposure.
- Backlog / new orders where disclosed.
- Gross margin, operating cash flow, accounts receivable, contract liabilities, capex, employee count, scientist / R&D staff count, and personnel efficiency.

### 4.2 `cdmo_manufacturing_services`

Representative positive samples:

- `002821` Asymchem.
- `300363` Porton Pharma Solutions.

Business model:

- CDMO / CMC / process development / commercial manufacturing outsourcing, often with stronger manufacturing and capacity-cycle characteristics.

Core economics:

- CDMO orders and new signed orders.
- Capacity utilization.
- Commercial-stage project count.
- Capacity expansion progress.
- Revenue per unit capacity.
- Capex and capacity matching.
- Gross margin by business.
- Customer concentration and overseas customer exposure.
- GMP / FDA / NMPA compliance events.
- Upfront / milestone payment structure if disclosed.

Specific sample note:

- `300363` Porton Pharma Solutions should be treated as a high-volatility CDMO sample. Historical data may be affected by one-off large orders, single-customer/product concentration, or pandemic-related order effects; historical year-on-year growth must not be used mechanically as a trend signal.

### 4.3 `clinical_cro_services`

Representative positive sample:

- `300347` Tigermed.

Business model:

- Clinical CRO, clinical trial services, SMO, data management, statistical analysis, registration support, and clinical project delivery services.

Core economics:

- Clinical project count.
- Clinical trial service revenue.
- SMO / data and statistical service revenue.
- Project acceptance / delivery progress.
- Hospital / research-center coverage.
- Project cancellation or delay.
- Collection cycle and receivable quality.
- Customer structure and overseas revenue exposure.

### 4.4 Sub-Type Effect on Evidence, Confidence, and Risk Guards

`sub_type` should affect:

- `must_track`: shared indicators apply to all, while CDMO-specific, clinical-specific, and integrated-platform-specific indicators are routed by `sub_type`.
- `confidence`: missing shared core indicators cap confidence across all sub-types; missing sub-type-critical indicators further cap confidence.
- `risk_guards`: CDMO companies must guard against inferring utilization from capex; clinical CRO companies must guard against inferring project prosperity without clinical project count or progress; integrated platforms must guard against treating total revenue growth as proof that all segments are improving.

If v1 implementation cannot add a first-class `sub_type` field, use equivalent routing metadata in evidence pack / analysis context. The design recommendation is still to preserve sub-type semantics from v1.

## 5. Classification Boundary

Should classify into `life_science_cxo_services`:

- CRO drug discovery services.
- Preclinical CRO.
- Clinical CRO.
- SMO / data statistics / clinical trial services.
- CMC services.
- CDMO / outsourced drug manufacturing.
- Commercial manufacturing outsourcing.
- Integrated pharmaceutical R&D and manufacturing outsourcing platforms.
- Companies whose revenue mainly comes from pharmaceutical R&D / manufacturing outsourcing services.

Must not classify into this framework:

- Self-owned innovative drug pipeline companies whose pipeline / drug sales dominate revenue.
- Generic drug / API / formulation manufacturing companies.
- Companies where API sales plus formulation sales exceed 60% and CDMO service revenue cannot be independently confirmed.
- Medical device companies.
- Medical device CDMO/CRO companies whose main service object is medical devices rather than drugs.
- Pharmaceutical distributors.
- Hospitals and medical service institutions.
- TCM / consumer healthcare / medical aesthetics.
- Generic testing and inspection laboratories, including non-drug-R&D outsourcing inspection companies.
- AI drug discovery / digital drug discovery platforms whose main revenue comes from software license, SaaS subscription, or technology licensing and that have no laboratory / GMP facility evidence.
- Large integrated pharmaceutical groups with only small CXO subsidiaries while group revenue is still mainly innovative drugs, generic drugs, formulations, or integrated pharmaceutical operations.
- Companies only mentioned in pharmaceutical R&D cooperation news while their main business is not CXO services.
- Diversified companies with only small or low-revenue outsourcing-service exposure.

Boundary principle:

- Classification must be based on business model and monetization evidence, not concept exposure.
- Main-business and revenue-composition evidence should outweigh news text.
- News-only "R&D cooperation", "clinical cooperation", "strategic cooperation", or "pharmaceutical R&D" mentions should default to `theme_only` or `unknown` unless supported by main-business or segment-revenue evidence.
- API companies sell products; CDMO companies sell R&D and manufacturing outsourcing services. If service revenue cannot be separated, do not automatically classify the company into this framework.

## 6. Classification Keyword Design

### Positive Keywords

- CRO
- CDMO
- CXO
- CMC
- clinical CRO
- preclinical research
- drug discovery
- drug R&D outsourcing
- R&D and manufacturing outsourcing
- pharmaceutical outsourcing service
- contract research organization
- contract development and manufacturing organization
- clinical trial service
- SMO
- data statistics service
- commercial manufacturing service
- process development
- formulation development
- API CDMO
- small-molecule CDMO
- large-molecule CDMO

### Strong Positive Conditions

Classification should require at least one strong condition:

- `basic_info`, `main_business`, or `business_composition` clearly shows that revenue mainly comes from CRO / CDMO / CXO / clinical research / pharmaceutical R&D and manufacturing outsourcing.
- Segment revenue or revenue composition shows CXO/CRO/CDMO-related revenue share `>= 50%`.
- Financial, revenue-segment, or main-business evidence supports the outsourcing-service model.

### Negative Exclusion Keywords

- self-owned pipeline
- innovative drug R&D
- new drug application
- API manufacturing
- formulation sales
- medical device
- pharmaceutical distribution
- drugstore
- TCM
- medical aesthetics
- consumer healthcare
- hospital
- generic inspection/testing
- AI drug discovery software
- SaaS subscription
- software license
- technology licensing
- strategic cooperation only
- R&D cooperation news only

Negative keywords should demote or exclude classification when they describe the company's main business. They should not exclude a true CXO platform merely because the company provides R&D-related services; the exclusion applies to self-owned pipeline, manufacturing, distribution, device, software, or consumer-healthcare economics.

## 7. Data Requirements

### Required

Required data should be realistic for the current deterministic pipeline and sufficient to avoid accidental theme-only classification:

- `basic_info`: main business, industry context, company description.
- `business_composition`: segment revenue and CXO/CRO/CDMO revenue evidence.
- CXO / CRO / CDMO related revenue or segment revenue.
- revenue / profit / gross_margin.
- operating_cashflow.
- accounts_receivable.
- contract_liabilities.
- r_and_d_expense_ratio.
- capex.
- valuation.

Required data can support classification and a conservative fundamental view. It is not enough for high confidence.

### Critical Confidence-Gating Indicators

These indicators may be unavailable or inconsistently disclosed. They should not all be hard required fields in v1, but missing values must cap confidence:

- backlog / on-hand orders.
- new signed orders.
- customer concentration.
- major-customer revenue share.
- overseas revenue share.
- North America / U.S. revenue share.
- customer geographic structure.
- CDMO capacity utilization.
- clinical project count / clinical trial service projects.
- project cancellation or delay.
- collection cycle.
- one-off large-order marker.
- geopolitical / overseas regulatory / Biosecure Act / sanction risk exposure.

### Preferred

- Segment revenue share by drug discovery, preclinical, clinical, CDMO, CMC, and commercial manufacturing.
- Major-customer revenue share.
- TOP customer changes.
- Employee count / scientist count / R&D employee count / revenue per employee.
- Laboratory area / capacity.
- Gross margin by business segment.
- FX impact.
- Order delivery cycle.
- GMP / FDA / NMPA compliance event history.

### Optional

- Major customer announcements.
- Overseas regulatory events.
- Biosecure Act related risk.
- FDA / EMA / NMPA / overseas compliance inspections.
- Capacity expansion project progress.
- Major project cancellation or delay events.
- Upfront / milestone payment structure.

## 8. Future Proxy Design, Not v1 Calculation

Claude / Sonnet suggested three useful proxy designs. This audit records them for future work, but v1 should not automatically calculate complex proxies.

### 8.1 Backlog Proxy

- Observable field: `contract_liabilities`.
- Interpretation: `contract_liabilities` can be a `partial_proxy` for prepayments or order visibility.
- Guard: it is not true backlog, not signed order book, and not confirmed future revenue.
- Confidence cap: when only this proxy is available and real backlog / new signed orders are missing, `max_confidence` must not be high.

### 8.2 CDMO Capacity Utilization Proxy

- Observable fields: CDMO revenue, gross margin trend, capex, capacity expansion projects.
- v1 should not force capacity-utilization inference from gross margin or capex.
- Guard: capex shows investment; it does not prove utilization, absorption, or future order conversion.
- Confidence cap: if actual capacity utilization is missing for CDMO companies, confidence must not be high.

### 8.3 U.S. Customer Risk Exposure Proxy

- Observable field: North America revenue share can serve as a partial proxy for U.S. customer risk exposure if U.S.-specific data is not disclosed.
- If geographic revenue or customer-region structure is unavailable, the field must be marked `missing`.
- Guard: do not understate Biosecure Act, sanction, overseas regulatory, or geopolitical risk when U.S. / North America exposure is unknown or material.
- v1 should not automatically compute U.S. customer-risk exposure from unstructured text.

## 9. Risk Guards

The framework must enforce the following interpretation guards:

1. Do not equate the CXO concept with order recovery.
2. Do not equate contract liabilities with true backlog.
3. Do not equate capex with capacity-utilization improvement or future order realization.
4. Do not equate R&D ratio with confirmed technological moat.
5. Do not equate revenue growth directly with improving order trend.
6. Without customer-concentration data, do not assert stable customer demand.
7. Without overseas revenue / U.S. customer exposure, do not understate overseas regulatory or geopolitical risk.
8. Without backlog / new signed orders, do not judge order visibility as high.
9. Without capacity-utilization data, do not assert good CDMO capacity absorption.
10. Without clinical project count, do not judge clinical CRO prosperity.
11. Innovative drug pipeline companies must not be misclassified into the CXO outsourcing-service framework.
12. Generic pharmaceutical manufacturing companies must not be misclassified into CXO.
13. Overseas regulatory, Biosecure Act, sanction, and geopolitical risks must be explicit risk guards for relevant companies.
14. FX impact must not be ignored, especially when overseas revenue exposure is high.
15. Talent / scientist loss risk: if employee count, R&D staff, or core scientist team size falls materially, flag operational risk.
16. One-off large-order distortion: if a single product, single customer, or pandemic-related order created an abnormal revenue peak, do not use year-on-year growth mechanically as a trend signal.
17. `300363` Porton Pharma Solutions should be tagged as a high-volatility CDMO sample for regression and reporting caution.
18. GMP / FDA / NMPA compliance risk: FDA Warning Letter, NMPA inspection issue, GMP certificate suspension, or regulatory remediation must be forced into risk flags when present.
19. FX has two-way effects: for high-overseas-revenue companies, consider both revenue-side and cost-side exposure; do not describe FX only as positive or only as negative.
20. Backlog missing risk: if there is no true backlog / new signed order disclosure and only contract liabilities are available, do not judge order visibility as high.

Additional guard:

- Confidence means evidence confidence in the current `fundamental_view`; it does not mean positive strength or investment attractiveness.

## 10. Must-Track Indicators

Each must-track indicator should be represented with `why_it_matters`, `current_status`, `affects_dimension`, and `suggested_source`. If the current pipeline cannot retrieve a reliable structured value, `current_status` should be `missing`, `partial_proxy`, or `future_data_needed`, not inferred.

### 10.1 Shared Indicators

| indicator | why_it_matters | current_status | affects_dimension | suggested_source |
| --- | --- | --- | --- | --- |
| CXO-related revenue share | Confirms that the company is monetizing outsourcing services and supports the 50% / 30% threshold test. | partial if business composition is available; otherwise missing | classification, revenue_quality | Annual report, business composition, main-business disclosure |
| backlog / on-hand orders | Tests order visibility beyond recognized revenue. | missing or partial_proxy if only contract liabilities are available | order_visibility, growth_visibility | Annual report, management discussion, company announcements |
| new signed orders | Captures current demand trend and booking momentum. | missing | demand_trend, order_visibility | Annual report, investor presentation, announcements |
| contract liabilities | Partial proxy for prepayments/order visibility, but not true backlog. | partial_proxy if balance sheet is available | working_capital, order_proxy | Balance sheet, financial statement notes |
| customer concentration | Identifies dependence on major customers and demand fragility. | missing | customer_risk, demand_stability | Annual report top-five customer disclosure |
| major-customer revenue share | Quantifies large-customer dependency and one-off order risk. | missing | customer_risk, revenue_volatility | Annual report top-five customer disclosure |
| overseas revenue share | Measures exposure to global pharma demand and overseas regulation. | missing or partial | overseas_exposure, regulatory_risk | Annual report segment/geographic revenue |
| North America / U.S. revenue share | Partial proxy for U.S. customer exposure and Biosecure Act / sanction risk. | missing or partial_proxy if only North America data is disclosed | geopolitical_risk, customer_risk | Annual report, geographic revenue, customer disclosures |
| overseas regulatory / Biosecure Act / sanction risk | Must be explicit when overseas exposure is material or unknown. | missing unless manually surfaced | regulatory_risk, geopolitical_risk | Annual report risk section, official regulators, announcements |
| gross margin | Measures service pricing, utilization, delivery mix, and cost pressure. | partial if financials are available | margin_quality, operating_efficiency | Income statement, segment reporting |
| operating cash flow | Tests cash conversion and earnings quality. | partial if cash-flow statement is available | cash_conversion, earnings_quality | Cash-flow statement |
| accounts receivable | Indicates collection pressure and customer payment discipline. | partial if balance sheet is available | cash_conversion, credit_risk | Balance sheet, financial statement notes |
| collection cycle | Converts receivables into operating-quality evidence. | missing unless calculated or disclosed | cash_conversion, project_delivery | Financial statements, notes, calculated ratios |
| capex | Shows capacity/lab/manufacturing investment, but not utilization or order realization. | partial if cash-flow statement is available | capacity_investment, capital_intensity | Cash-flow statement, annual report |
| FX impact | Overseas revenue may create two-way translation and transaction effects. | missing | margin_quality, overseas_exposure | Annual report, financial statement notes |
| project cancellation or delay | Directly affects revenue recognition, capacity absorption, and cash collection. | missing | project_execution, demand_risk | Annual report, announcements, customer/project disclosures |
| one-off large-order marker | Prevents abnormal order peaks from being interpreted as normalized trend. | missing or future_data_needed | revenue_volatility, trend_quality | Annual report, major contract announcements, management discussion |

### 10.2 `integrated_cxo_platform`

| indicator | why_it_matters | current_status | affects_dimension | suggested_source |
| --- | --- | --- | --- | --- |
| Segment revenue share | Prevents treating a platform as a single homogeneous business. | missing or partial | business_mix, classification | Annual report segment reporting |
| Drug discovery revenue | Captures early-stage CRO exposure and customer R&D activity. | missing | demand_mix, revenue_quality | Annual report, segment disclosure |
| Preclinical service revenue | Tracks nonclinical outsourcing exposure and delivery demand. | missing | demand_mix, operating_quality | Annual report, segment disclosure |
| CMC/CDMO revenue | Measures manufacturing/service-line exposure inside integrated platforms. | missing | capacity_cycle, business_mix | Annual report, segment disclosure |
| Customer count / active customers | Tests platform breadth and repeat-customer quality. | missing | customer_quality, demand_stability | Annual report, management discussion |
| Major-customer changes | Detects concentration risk and platform customer churn. | missing | customer_risk, revenue_visibility | Annual report top customer disclosure |
| Employee count | Service capacity and delivery quality depend on staff base. | missing | service_capacity, cost_structure | Annual report, ESG report, HR disclosure |
| Scientist / R&D staff count | Tracks core scientific delivery capability and talent-risk exposure. | missing | service_capacity, operating_risk | Annual report, ESG report, HR disclosure |
| Personnel efficiency | CXO-related revenue per employee or technical staff can indicate delivery efficiency. | future_data_needed | operating_efficiency, margin_quality | Annual report, calculated after staff and revenue fields are available |

### 10.3 `cdmo_manufacturing_services`

| indicator | why_it_matters | current_status | affects_dimension | suggested_source |
| --- | --- | --- | --- | --- |
| CDMO orders | Directly validates demand for manufacturing outsourcing. | missing | order_visibility, demand_trend | Annual report, announcements, investor presentation |
| CDMO capacity utilization | Distinguishes built capacity from absorbed capacity. | missing or future_data_needed | operating_efficiency, margin_quality | Annual report, management commentary |
| Commercial-stage project count | Commercial projects usually have different visibility and margin characteristics from early-stage projects. | missing | project_quality, revenue_visibility | Annual report, project disclosure |
| GMP / FDA / NMPA compliance events | Regulatory issues can interrupt production, customer trust, or delivery. | missing unless disclosed | regulatory_risk, delivery_risk | Official regulators, annual report, announcements |
| Capacity expansion progress | Links capex to actual production capacity and timing. | missing | capacity_cycle, capex_execution | Annual report, construction/project announcements |
| Revenue per unit capacity | Tests productivity and capacity monetization. | future_data_needed | operating_efficiency, capacity_absorption | Annual report, internal calculation if capacity is disclosed |
| Capex / capacity matching | Guards against assuming capex automatically converts into orders. | partial if capex is available; capacity missing | capital_intensity, utilization_risk | Cash-flow statement, annual report |
| Major-customer concentration | CDMO can be exposed to large-customer and large-project volatility. | missing | customer_risk, order_volatility | Annual report top-five customer disclosure |
| Upfront / milestone payment structure | Payment structure affects contract liabilities, visibility proxy quality, and cash conversion. | missing | order_proxy_quality, cash_conversion | Contract disclosures, annual report, announcements |

### 10.4 `clinical_cro_services`

| indicator | why_it_matters | current_status | affects_dimension | suggested_source |
| --- | --- | --- | --- | --- |
| Clinical project count | Primary operating-volume indicator for clinical CRO demand. | missing | demand_trend, project_execution | Annual report, management discussion |
| Clinical trial service revenue | Confirms clinical CRO monetization and segment trend. | missing or partial | classification, revenue_quality | Annual report segment reporting |
| SMO / data statistics revenue | Separates clinical service lines and delivery quality. | missing | business_mix, revenue_quality | Annual report segment reporting |
| Project acceptance / progress | Determines revenue recognition and execution risk. | missing | project_delivery, earnings_quality | Annual report, project disclosure |
| Hospital / research-center coverage | Measures operating network and delivery capacity. | missing | service_capacity, competitive_position | Annual report, company website |
| Project cancellation or delay | Directly affects clinical CRO revenue, cash flow, and backlog quality. | missing | project_risk, order_visibility | Annual report, announcements |
| Collection cycle | Clinical projects can have long delivery and payment cycles. | missing unless calculated/disclosed | cash_conversion, credit_risk | Financial statements, notes |

## 11. Readiness / Confidence Rules

Conservative confidence rules:

- If only `basic_info` and financials are available: `max_confidence=low`.
- If `business_composition` is available and CXO/CRO/CDMO revenue share is confirmable: `max_confidence=low_medium`.
- If only contract-liabilities proxy exists and true backlog / new signed orders are missing: `max_confidence` must not be high.
- Under typical A-share CXO public disclosure, if true backlog / new signed orders / customer structure / overseas revenue share are unavailable, `max_confidence` should usually be capped at `medium`.
- If `contract_liabilities` is used as backlog proxy: `max_confidence` must not be high.
- If partial evidence exists among backlog / new orders / customer structure / overseas revenue share: confidence can reach `neutral` status with `medium_low` to `medium` evidence confidence, subject to sub-type gates.
- If backlog, new signed orders, customer concentration, and overseas revenue share are all missing: confidence must not be high.
- If the company is CDMO-related but capacity utilization is missing: confidence must not be high.
- If the company is clinical CRO-related but clinical project count or project progress is missing: confidence must not be high.
- If overseas revenue share is high but U.S. / North America exposure and overseas regulatory / geopolitical risk are not described: confidence must not be high.
- If support comes only from news or concept wording: classify as `theme_only` or `unknown`.
- Self-owned innovative drug pipeline companies, generic pharmaceutical manufacturers, medical device companies, pharmaceutical distributors, generic testing labs, and AI drug-discovery software companies must not classify into `life_science_cxo_services` unless the CXO revenue threshold and service-evidence rules are met.
- High-volatility CDMO samples such as `300363` Porton Pharma Solutions should trigger caution; avoid using historical year-on-year growth as a strong trend judgment when one-off order risk is present.
- `confidence` must represent evidence confidence in the current `fundamental_view`, not positive strength.

Suggested readiness interpretation:

| Evidence state | Expected classification/readiness behavior |
| --- | --- |
| News-only CXO/CRO/CDMO wording | `theme_only` or `unknown`; confidence `low` |
| `basic_info` confirms outsourcing services but no business composition | Possible framework candidate; max confidence `low` |
| Business composition confirms CXO/CRO/CDMO revenue share `>= 50%` | Classifiable; max confidence `low_medium` until operating evidence improves |
| CXO/CRO/CDMO revenue share `30% - 50%` | Boundary review; do not classify automatically |
| CXO/CRO/CDMO revenue share `< 30%` | Default not classify unless clear transformation plus revenue evidence |
| Segment revenue plus some orders/customer/geographic evidence | Classifiable; possible `neutral`; max confidence `medium_low` to `medium` |
| Only contract-liabilities proxy for backlog | Classifiable only if business evidence is strong; confidence cannot be high |
| Full segment revenue, real orders/backlog, customer concentration, overseas exposure, and sub-type-critical indicators | Strong evidence pack; confidence may rise subject to risk guards |

## 12. AI Report Requirements

AI report constraints for this framework:

- Explain that CXO / CRO / CDMO companies provide pharmaceutical R&D and manufacturing outsourcing services; they are not self-owned innovative drug pipeline companies.
- For mixed CXO + innovative drug companies, explicitly state that the self-owned pipeline is outside this framework's evaluation scope.
- Explain that financial metrics only describe baseline operating quality.
- If orders, customer structure, overseas revenue, capacity utilization, or project progress are missing, state that evidence is insufficient to judge industry prosperity or business realization.
- Treat contract liabilities only as an order-visibility partial proxy.
- Treat capex only as capacity investment observation, not proof of capacity absorption.
- Treat R&D ratio only as R&D-intensity observation, not confirmed technology moat.
- Explicitly flag overseas regulation, geopolitical risk, Biosecure Act, sanction, and compliance risk where relevant.
- Explicitly flag talent / scientist loss risk where employee or technical staff decline is material.
- Explicitly flag one-off large-order distortion where a single customer/product or pandemic-related order may have created an abnormal revenue base.
- Do not mix CRO / CDMO companies with generic pharmaceutical manufacturing, medical devices, AI drug-discovery software, or innovative drug companies.
- Do not output trading advice, technical analysis, target prices, timing, position sizing, or account actions.

## 13. Positive and Negative Sample Suggestions

### Positive Candidates

- `603259` Wuxi AppTec: expected `strategy_type=life_science_cxo_services`, expected `sub_type=integrated_cxo_platform`; current audit shows framework gap, not misclassification risk.
- `300759` Pharmaron: expected `strategy_type=life_science_cxo_services`, expected `sub_type=integrated_cxo_platform`; similar integrated CXO evidence requirement.
- `002821` Asymchem: expected `strategy_type=life_science_cxo_services`, expected `sub_type=cdmo_manufacturing_services`; order, utilization, overseas customer, gross margin, and capex evidence are critical.
- `300363` Porton Pharma Solutions: expected `strategy_type=life_science_cxo_services`, expected `sub_type=cdmo_manufacturing_services`; high-volatility CDMO sample, useful for one-off order, utilization, and customer-concentration cautions.
- `300347` Tigermed: expected `strategy_type=life_science_cxo_services`, expected `sub_type=clinical_cro_services`; clinical projects, customer mix, overseas revenue, and collection quality are critical.

### Negative Candidates

Negative candidates should be verified before implementation and should not be treated as confirmed facts in this design document:

- `600276` Hengrui Medicine: pending verification; likely innovative drug / pharmaceutical company boundary sample; exclude if main economics come from drug R&D/pipeline/drug sales rather than CXO services.
- `600521` Huahai Pharmaceutical: pending verification; API plus small CDMO boundary sample; do not automatically classify if CDMO service revenue cannot be independently confirmed.
- `000739` Puluo Pharmaceutical: pending verification; API plus CDMO mixed boundary test; do not automatically classify without CXO revenue-share evidence.
- `300760` Mindray Medical: pending verification; medical-device boundary sample; exclude if main economics come from devices rather than pharmaceutical outsourcing services.
- `300012` Centre Testing International: pending verification; generic testing / inspection boundary sample; exclude if services are not primarily drug R&D outsourcing.
- `600196` Fosun Pharma: pending verification; integrated pharmaceutical group boundary sample; exclude if group economics remain mainly pharma, devices, distribution, or integrated healthcare rather than CXO services.
- AI drug-discovery / software-service samples: pending verification; exclude if main revenue comes from software license, SaaS subscription, or technology licensing and there is no laboratory / GMP facility evidence.
- Companies with only pharmaceutical R&D cooperation news: exclude when main business and revenue composition do not support CXO outsourcing services.

Regression design should include both close positives and close negatives. Positive cases should verify `strategy_type`, `sub_type`, conservative confidence caps, risk flags, and must-track terms. Negative cases should verify that the classifier does not pull innovative drug, API/formulation manufacturing, medical devices, generic inspection/testing, integrated pharma groups, AI drug software, or news-only cooperation names into CXO.

## 14. Implementation-Stage Recommendation

Recommendation: enter implementation stage after this design revision is accepted.

v1 should implement:

- `classifier` support for `life_science_cxo_services`.
- `sub_type` routing.
- `industry_frameworks`.
- `data_requirements`.
- `analysis_context_rules`.
- Conservative scoring configuration.
- Evidence-pack must-track indicators.
- AI report prompt constraints.
- Regression tests for positive and negative samples.

v1 should not implement:

- External CXO order-data connector.
- Automated backlog collection.
- CDMO capacity-utilization proxy.
- Automated U.S. customer risk-exposure proxy.
- Clinical project database integration.
- FDA / EMA / NMPA event connector.
- Biosecure Act news parser.
- Innovative drug pipeline framework.
- Medical device framework.
- Technical analysis.
- `trader_skill`.
- Trading advice.

## 15. Claude / Sonnet Recommendation Disposition

Accepted in v1.1:

- Quantitative classification threshold based on CXO/CRO/CDMO revenue share.
- Mixed CXO + innovative drug business rule.
- Strengthened `sub_type` architecture.
- Added API/formulation, medical-device CRO/CDMO, generic testing lab, AI drug software, and integrated pharma group misclassification boundaries.
- Recorded backlog, CDMO utilization, and U.S. customer risk-exposure proxy designs.
- Strengthened risk guards for talent loss, one-off large orders, GMP/FDA/NMPA compliance, FX two-way effects, and missing backlog.
- Expanded must-track indicators.
- Tightened confidence caps.
- Expanded positive and negative sample suggestions.

Deferred from v1 implementation:

- Automatic backlog collection.
- Automatic CDMO capacity-utilization proxy calculation.
- Automatic U.S. customer risk-exposure proxy calculation.
- External FDA / EMA / NMPA event connector.
- Biosecure Act news parser.
- Clinical project database connector.
- New innovative drug or medical-device frameworks.

## 16. Design Verdict

The out-of-sample audit shows a clear framework gap, not an unsafe overclassification problem. The system should add `life_science_cxo_services` as a business-model framework with conservative evidence gates.

The v1.1 design should proceed with `sub_type` from v1 because integrated CXO platforms, CDMO manufacturing services, and clinical CRO services require different must-track indicators and confidence caps. If engineering chooses not to add a first-class `sub_type` immediately, equivalent routing metadata should still be present in the evidence pack and analysis context.

This framework is ready to enter implementation after accepting the conservative boundaries above. Implementation must preserve the current safety posture: no technical analysis, no trading advice, no strategy overconfidence, no proxy overinterpretation, and no news-only classification.
