# Satellite Communication Infrastructure Framework Design Audit v1.1

Date: 2026-05-20

Revision basis:

- v1.0 design audit for `satellite_communication_infrastructure`.
- Independent Claude / Sonnet audit verdict: B, can enter implementation only after design revision.

Scope:

- Design-only revision for the new strategy framework: `satellite_communication_infrastructure`.
- Triggered by the out-of-sample generalization audit result for 601698 中国卫通.
- This stage modifies documentation only.
- No classifier, connector, pipeline, dashboard, scoring engine, code-level strategy type, `technical_skill`, or `trader_skill` change.
- No trading advice, technical analysis, target price, position sizing, or account action.

## 1. Strategy Type Definition

`satellite_communication_infrastructure` applies to asset-intensive, license / resource-driven, long-cycle operating companies that monetize scarce satellite communication infrastructure resources.

Revised core definition:

以卫星空间段资产，包括在轨卫星、轨位、频段、转发器为核心稀缺资源，以带宽、转发器、卫星通信服务变现为主要收入来源；地面段业务若存在，也必须以卫星资源变现为前提的资产密集、牌照/资源驱动、长周期运营型公司。

This definition intentionally covers satellite-resource-driven ground-segment transmission income when that income depends on monetizing satellite resources. It does not cover generic ground equipment, terminals, system integration, software, chip, remote-sensing, rocket, drone, or media businesses whose economics are not primarily driven by satellite communication infrastructure resources.

For 601698 中国卫通, the available out-of-sample evidence supports this design need: `basic_info` identifies the industry as "电信、广播电视和卫星传输服务", main business is "卫星空间段运营及相关应用服务", and 2025-12-31 business composition by industry reports "广播电视和卫星传输服务" revenue at 100.00%. The current system remains appropriately conservative, but lacks a professional framework for this business model.

## 2. Classification Boundary

### Should Classify Into This Type

- 卫星空间段运营
- 转发器 / 带宽资源运营
- 轨位 / 频段资源运营
- 卫星通信服务
- 广播电视和卫星传输服务
- 主营收入中卫星传输服务占比较高的公司
- 具备牌照 / 轨位 / 频段 / 在轨卫星资源的运营型公司
- Satellite operators that sell or lease transponder capacity, satellite bandwidth, space-segment capacity, or managed satellite communication services

### Must Exclude

- 卫星制造
- 火箭制造
- 遥感软件
- 遥感数据服务
- 测控地面系统集成
- 导航芯片
- 军工电子终端
- 通信设备制造
- 低空经济纯题材
- 无人机
- 普通传媒运营商
- 仅新闻提到商业航天但主营不相关的公司
- System integrators or equipment vendors whose revenue is mainly terminals, antennas, modules, chips, components, ground equipment, or military communication devices

### Specific Negative Sample Suggestions

These are proposed regression candidates and should be verified before implementation:

- 600118 中国卫星，待验证，疑似遥感 / 测控 / 卫星制造属性，不应归入。
- 002465 海格通信，待验证，疑似军用通信终端属性，不应归入。
- 688066 航天宏图，待验证，疑似遥感软件 / 数据服务属性，不应归入。
- 002895 中科星图，待验证，疑似遥感数据软件属性，不应归入。

## 3. Classification Keyword Design

### Positive Keywords

- 卫星空间段
- 卫星通信
- 卫星传输
- 转发器
- 频段资源
- 轨位资源
- 通信卫星
- 广播电视和卫星传输服务
- 卫星运营
- 带宽租赁
- 空间段运营
- 卫星通信服务

### Negative Exclusion Keywords

- 卫星制造
- 火箭
- 遥感软件
- 遥感数据服务
- 测控地面系统集成
- 导航芯片
- 军工电子
- 军工电子终端
- 通信设备制造
- 低空经济
- 无人机

### Classification Notes

- Positive hits from `basic_info.industry`, `basic_info.main_business`, and `business_composition` should carry more weight than news text.
- Main-business and revenue-composition evidence should be required to separate satellite communication infrastructure operators from theme-only companies.
- News-only mentions of 商业航天, 卫星互联网, 低空经济, or aerospace policy should not establish this strategy type.
- Negative keywords should demote or exclude candidates when the company's primary business is manufacturing, chips, software, remote sensing, military electronics, rockets, drones, or generic communications equipment.

## 4. Analysis Framework

The framework should analyze satellite communication infrastructure companies as asset-intensive, licensed, long-cycle operators.

Core dimensions:

- Satellite resources and orbital slot / frequency resources: identify whether the company controls scarce operating resources, licenses, orbital slots, frequency bands, or in-orbit communication satellites.
- Transponder / bandwidth capacity: track available communication capacity and whether capacity additions or retirements change the earnings base.
- Capacity utilization / lease rate: distinguish owned capacity from economically productive capacity.
- Unit bandwidth price: monitor pricing pressure, premium capacity, and customer mix changes.
- Customer structure and contract duration: separate stable long-term institutional demand from volatile short-term or project-based demand.
- Broadcast and television, maritime, aviation, emergency response, government / SOE customers: identify demand sources and resilience.
- Policy customers vs commercial customers: assess customer behavior, payment quality, pricing power, and renewal stability separately.
- Asset life and depreciation pressure: satellite assets have finite design lives and depreciation schedules that affect reported profit.
- Capex / satellite launch cycle: capex reflects long-term asset construction, satellite procurement, launch schedules, and renewal pressure.
- Accounts receivable and collection quality: long-term customers can still create cash conversion risk.
- Contract liabilities as order-visibility proxy: useful as a proxy, but not the same as confirmed backlog, signed order book, or future revenue.
- Operating cash flow stability: critical for long-cycle, capital-intensive infrastructure operations.
- Free cash flow: operating cash flow minus capex is important for capital intensity, but should not enter v1 scoring until definitions are stable.
- Commercial aerospace new-business realization: distinguish theme exposure from recognized revenue, margin contribution, and cash flow.
- Policy and license barriers: assess entry barriers, regulatory support, and resource scarcity without treating policy as automatic earnings conversion.

## 5. Data Requirements

### Required

Required data should remain realistic and currently obtainable:

- `basic_info`
- `business_composition`
- revenue / profit / gross_margin
- operating_cashflow
- accounts_receivable
- contract_liabilities
- capex
- valuation

Required data is enough to avoid `unknown` when main business and business composition clearly support satellite communication infrastructure operation. It is not enough for high confidence.

### Critical Confidence-Gating Indicators

These indicators may not be publicly or stably obtainable, so they should not be hard `required` fields in v1. However, missing values must cap confidence:

- 容量利用率 / 出租率
- 转发器 / 带宽容量
- 单位带宽价格
- 客户结构 / 客户集中度
- 卫星设计寿命 / 剩余寿命
- 折旧摊销
- 卫星发射计划
- 卫星故障 / 保险事件

### Preferred

- 在轨卫星数量
- 轨位 / 频段资源说明
- 合同期限结构
- 海外业务占比
- 政策性客户 vs 商业客户结构

### Optional

- 政策项目
- 重大客户公告
- 商业航天新业务收入
- 公开新闻或公告中的发射 / 故障事件

### Interpretation Guards

| field | interpretation_guard |
| --- | --- |
| `contract_liabilities` | 只能作为订单可见度 proxy，不等同真实 backlog，不等同确定订单。 |
| `capex` | 只能表示长期资产购建现金支出，不等同新增容量确定释放。 |
| `r_and_d_expense_ratio` | 只能表示研发强度，不等同技术壁垒已确认。 |
| `business_composition` | 只能表示收入结构，不能单独证明卫星资源利用率或客户需求稳定。 |
| `valuation` | PE/PB/PS 只能作为参考，不足以独立判断估值合理性。 |

## 6. Risk Guards

- 不得把合同负债等同真实 backlog，不得等同确定订单。
- 不得只用 PE/PB/PS 判断估值。
- 不得把商业航天主题、政策热度或新闻热度等同业绩兑现。
- 不得在缺少容量利用率 / 出租率时断言卫星资源利用充分。
- 不得在缺少客户结构时断言需求稳定或定价能力强。
- 不得在缺少折旧 / 寿命数据时忽略资产老化风险。
- 不得在缺少发射计划时断言新增容量确定释放。
- 不得把 capex 直接解释为短期增长；capex 只能说明长期资产购建现金支出，需要结合发射、投运、折旧和收入确认。
- 不得把政策支持直接解释为收入或利润兑现。
- 不得将卫星制造、火箭、导航芯片、遥感软件、遥感数据服务、测控地面系统集成、无人机、低空经济题材误归入运营型卫星通信基础设施。
- 折旧年限会计政策风险：不得在未核实卫星折旧年限和资产寿命会计政策时跨公司比较利润率。
- 卫星故障 / 保险事件风险：若公开材料中出现卫星异常、在轨故障、保险索赔、资产减值，应显式标注，不得用正常经营数据覆盖。
- 政策性客户和定价能力风险：缺客户结构时，不得断言需求稳定或定价能力强。
- 容量利用率缺失风险：缺容量利用率 / 出租率时，不得断言卫星资源利用充分。
- 商业航天主题风险：不得把商业航天主题、政策热度或新闻热度等同业绩兑现。

## 7. Must-Track Indicators

Each must-track indicator should be represented in the evidence pack with `why_it_matters`, `current_status`, `affects_dimension`, and `suggested_source`. If the current pipeline cannot retrieve a reliable structured value, `current_status` must be `missing`.

New financial valuation / leverage indicators added in v1.1 are must-track data limitations only. They should not enter v1 scoring.

| indicator | why_it_matters | current_status | affects_dimension | suggested_source |
| --- | --- | --- | --- | --- |
| 在轨卫星数量 | Defines the operating asset base and service capacity. | missing | capacity, asset_base, growth_visibility | Annual report; company announcements; official company website; regulatory filings |
| 转发器 / 带宽容量 | Measures monetizable satellite communication capacity. | missing | revenue_capacity, pricing_power | Annual report; bond prospectus; company announcements; industry database |
| 容量利用率 / 出租率 | Distinguishes available capacity from revenue-generating capacity. | missing | operating_efficiency, demand_validation | Annual report; management discussion; investor presentations |
| 单位带宽价格 | Captures pricing trend and competitive pressure. | missing | pricing_power, margin_quality | Annual report; customer contract disclosures; industry research |
| 卫星剩余寿命 | Identifies asset aging, replacement needs, and service continuity risk. | missing | asset_life, depreciation_risk, capex_cycle | Annual report; satellite launch disclosures; company technical disclosures |
| 合同期限结构 | Shows revenue visibility and renewal risk. | missing | revenue_visibility, demand_stability | Annual report; major contract announcements; customer disclosures |
| 客户集中度 | Tests whether demand is diversified or dependent on a few customers. | missing | customer_risk, cashflow_quality | Annual report top-five customer disclosure; notes to financial statements |
| 合同负债 | Proxy for order visibility and prepayments, but not true backlog. | missing | order_visibility, working_capital | Balance sheet; financial statement notes |
| 应收账款 | Indicates collection quality and customer payment discipline. | missing | cash_conversion, credit_risk | Balance sheet; financial statement notes |
| capex | Shows long-term asset construction, satellite procurement, and launch-cycle pressure. | missing | reinvestment_need, free_cashflow | Cash flow statement; capex-related cash outflows; annual report |
| 折旧摊销 | Reflects asset consumption and pressure on reported profit. | missing | profit_quality, asset_life | Cash flow statement; financial statement notes; annual report |
| 经营现金流 | Tests whether long-cycle contracts convert into cash. | missing | cashflow_stability, financial_quality | Cash flow statement; financial indicators |
| 毛利率 | Captures service profitability and capacity economics. | missing | margin_quality, pricing_power | Financial indicators; income statement; business composition |
| 商业航天新业务收入 | Separates thematic exposure from realized revenue contribution. | missing | growth_realization, new_business_validation | Annual report segment disclosure; company announcements |
| 重大卫星发射 / 故障 / 保险事件 | Can materially change capacity, service continuity, capex, insurance proceeds, and impairment risk. | missing | event_risk, capacity_change, asset_impairment | Company announcements; exchange filings; insurance event disclosures |
| EV/EBITDA | Helps compare asset-intensive operators, but needs reliable enterprise value, debt, cash, and EBITDA definitions. | missing; future_data_needed | valuation_context, leverage_adjusted_profitability | Financial statements; valuation data; debt and cash fields; calculated metric |
| EBITDA margin | Helps separate accounting depreciation effects from operating margin, but requires stable EBITDA definition. | missing; future_data_needed | operating_profitability, depreciation_context | Income statement; cash flow statement; calculated metric |
| 自由现金流 = 经营现金流 - capex | Shows post-reinvestment cash generation for a capital-intensive operator. | missing | cashflow_quality, reinvestment_burden | Cash flow statement; calculated metric |
| 债务 / EBITDA | Helps judge leverage against operating cash earnings, but requires reliable total debt and EBITDA. | missing; future_data_needed | leverage_risk, financial_resilience | Balance sheet; income statement; cash flow statement; calculated metric |

## 8. Readiness / Confidence Rules

`confidence` means confidence in the evidence quality of the current `fundamental_view`. It does not mean positive fundamental strength, investment attractiveness, or upside.

Recommended readiness and confidence caps:

- Only `basic_info` + financials: `max_confidence = low`.
- `basic_info` + financials + `business_composition`: `max_confidence = low_medium` or `medium_low`; it must not directly become `medium` or `high`.
- If capacity utilization, customer structure, satellite life, and depreciation / amortization are missing: `max_confidence` must not be `high`.
- If `basic_info` + financials + `business_composition` + some confidence-gating indicators are available: confidence can be `medium`.
- `high` confidence requires relatively complete capacity utilization, customer structure, satellite life / depreciation, launch plan, and material event data. Under public A-share data constraints, high confidence should not be reached easily.
- If `business_composition` and financials are available, and main business clearly points to satellite communication infrastructure operation, classification can be `neutral` readiness rather than `unknown`, but the evidence confidence remains capped.
- If main business is explicitly satellite communication space-segment operation or satellite-resource-driven communication service operation, the system should be able to identify `satellite_communication_infrastructure`.
- If the only support is news mentioning commercial aerospace, satellite internet, low-altitude economy, or policy themes while the main business does not support it, classification should be `theme_only` or `unknown`.
- `insufficient_data` should remain valid when the system cannot access enough operating indicators to judge capacity, utilization, asset life, customer quality, and cash conversion.

Suggested confidence cap table:

| Available evidence | Suggested classification readiness | Maximum confidence |
| --- | --- | --- |
| News-only satellite / commercial aerospace theme | `theme_only` or `unknown` | low |
| `basic_info` + financials only | possible weak strategy match if main business supports it | low |
| `basic_info` + financials + `business_composition` | framework usable, analysis incomplete | low_medium / medium_low |
| Required data plus some confidence-gating indicators | framework usable with partial industry context | medium |
| Required data plus capacity, utilization, customer structure, satellite life / depreciation, launch plan, and event checks | framework mature | medium / high, but high should be rare in public A-share data |

## 9. AI Report Requirements

The AI report for `satellite_communication_infrastructure` must explain:

- This is an asset-intensive, license / resource-driven, long-cycle operating company.
- Ground-segment income can be relevant only when it depends on satellite resource monetization.
- Financial indicators can only explain baseline operating quality.
- When industry-specific data is missing, the report is not sufficient to judge whether commercial aerospace growth is being realized.
- Contract liabilities can only be used as an order-visibility proxy, not as true backlog or confirmed orders.
- Capex can only be interpreted as long-term asset purchase / construction cash outflow; it does not by itself prove new capacity release or near-term growth.
- Valuation should be interpreted together with asset life, cash flow stability, capacity utilization, customer structure, depreciation, leverage, and replacement capex needs.
- Missing satellite capacity, utilization, remaining life, depreciation, customer concentration, and launch plan should be called out explicitly rather than filled with assumptions.
- `confidence` describes evidence sufficiency, not positive or negative fundamental direction.

The report must not:

- output trading advice;
- use technical indicators;
- infer target price, position sizing, or buy / sell / hold recommendations;
- treat commercial aerospace policy or theme exposure as proof of earnings growth;
- claim stable demand or strong pricing power without customer and contract evidence;
- compare profitability across peers without checking depreciation policy and asset life assumptions.

## 10. Proxy Rules, Recorded For Future Use Only

Possible future proxies:

- `implied_utilization_proxy`
- `implied_bandwidth_price`

v1 implementation must not calculate these proxies.

Reasons:

- Market reference unit prices are difficult to obtain consistently.
- C / Ku / Ka band pricing can differ materially.
- Transponder-equivalent bandwidth definitions are complex.
- Estimation error may be large and could create false precision.

Proxy design can be revisited only after source stability, calculation definitions, and reporting safeguards are reviewed.

## 11. Regression Sample Suggestions

### Positive Sample

- 601698 中国卫通: positive sample. Current evidence supports a satellite communication infrastructure operating profile, but confidence should remain limited until industry-specific operating data is added.

### Cross-Market Reference Samples

- 亚洲卫星: if data can be obtained, use only as design reference, not as mandatory A-share regression.
- SES: international peer indicator reference only, not part of current A-share regression.
- Eutelsat: international peer indicator reference only, not part of current A-share regression.

### Specific Negative Samples

- 600118 中国卫星，待验证，疑似遥感 / 测控 / 制造属性。
- 002465 海格通信，待验证，疑似军用通信终端属性。
- 688066 航天宏图，待验证，疑似遥感软件 / 数据服务。
- 002895 中科星图，待验证，疑似遥感数据软件。

### Negative Sample Categories

- 通信设备制造
- 卫星制造
- 遥感软件
- 遥感数据服务
- 导航芯片
- 军工电子
- 军工电子终端
- 测控地面系统集成
- 低空经济题材
- 火箭制造
- 无人机
- 普通传媒运营商
- 新闻中提及商业航天但主营不相关的公司

### Boundary Samples

- Companies that only mention commercial aerospace, satellite internet, or low-altitude economy in news while main business and business composition do not support satellite-resource-driven communication infrastructure should classify as `theme_only` or `unknown`.

## 12. Implementation-Stage Suggestions

If this v1.1 design audit is accepted, the next implementation stage can cover:

- classifier
- framework
- data_requirements
- analysis_context_rules
- evidence_pack must-track
- regression tests
- AI report prompt constraints

v1 should not implement:

- utilization proxy
- EV/EBITDA scoring
- EV/transponder valuation
- cross-market data ingestion
- LEO constellation framework
- direct external satellite operational data connector

Implementation should remain deterministic and auditable:

- use high-weight evidence from industry, main business, and business composition;
- use news only as low-weight context;
- add negative keyword exclusions for manufacturing, chips, software, remote sensing, measurement and control ground-system integration, rockets, drones, and low-altitude-economy themes;
- cap confidence when critical confidence-gating indicators are missing;
- keep AI report prompts conservative and evidence-bound;
- keep new v1.1 financial indicators as must-track limitations only unless a later scoring design explicitly approves them.

## 13. Design Verdict

Recommendation: proceed to implementation stage after review, with v1 scope limits.

Rationale:

- The current out-of-sample result is conservative and avoids overconfidence, which is desirable.
- 601698 中国卫通 exposes a real framework gap: the system can fetch basic financial and business-composition data but cannot express the operating logic of satellite communication infrastructure.
- Claude / Sonnet's B verdict is accepted: implementation is reasonable only after narrowing the definition, strengthening exclusions, separating required data from confidence-gating indicators, and capping confidence more conservatively.
- A dedicated strategy type is justified because the economics differ from generic telecom, media, equipment manufacturing, defense electronics, remote sensing, satellite manufacturing, and commercial aerospace themes.
- Implementation should be staged and guarded by strict classification boundaries, confidence caps, interpretation guards, and must-track missing-data disclosure.

## 14. Claude / Sonnet Audit Integration Status

Accepted into v1.1:

- Revised strategy definition to include satellite-resource-driven ground-segment income.
- Stronger positive and negative classification boundaries.
- Specific negative regression sample suggestions with `待验证` labels.
- Required data kept realistic; confidence-gating indicators separated from hard requirements.
- Interpretation guards for `contract_liabilities`, `capex`, `r_and_d_expense_ratio`, `business_composition`, and `valuation`.
- Additional risk guards for depreciation policy, satellite failures / insurance events, customer structure, utilization, and commercial aerospace theme risk.
- More conservative confidence rules and explicit statement that confidence is evidence confidence, not positive strength.
- New must-track indicators: EV/EBITDA, EBITDA margin, free cash flow, and debt / EBITDA.
- Future proxy rules recorded but explicitly excluded from v1 implementation.
- Regression design split into positive, cross-market reference, specific negative, negative category, and boundary samples.
- v1 implementation scope and v1 exclusions clarified.

Deferred from v1 implementation:

- `implied_utilization_proxy`
- `implied_bandwidth_price`
- EV/EBITDA scoring
- EV/transponder valuation
- cross-market data ingestion
- LEO constellation framework
- direct external satellite operational data connector
