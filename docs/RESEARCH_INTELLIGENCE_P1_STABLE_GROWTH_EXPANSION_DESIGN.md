# Research Intelligence P1.1 Stable Growth Expansion Design Audit

Date: 2026-05-25

Revision: v1.1

Stage: Documentation sync after implementation and acceptance. This document records the accepted Stable Growth first-version baseline and must not change code, tests, P1 schema, deterministic pipeline behavior, classifier rules, connectors, scoring, readiness, HTML renderer, Dashboard, generated output, regression fixtures, or existing artifact semantics.

Target expansion: accepted `stable_growth` first-version baseline only.

Implementation status: implemented and accepted. P1.1 Stable Growth first-version support is frozen at `stable_growth + 600406` unless a future design / implementation / acceptance cycle expands it. Acceptance recorded `missing / not_assessable = 19/33 = 57.58%`, which is expected and correct; latest recorded validation after Stable Growth acceptance is `pytest` `484 passed` and regression suite `passed=47 failed=0 total=47`.

Primary implementation sample: `600406` NARI Technology / 国电南瑞.

Validation sample: `002028` Sieyuan Electric / 思源电气.

Excluded sample: `600276` Hengrui Pharmaceuticals / 恒瑞医药 is excluded from first implementation because the refreshed classifier result remains `unknown / insufficient_data`.

## 1. Expansion Positioning

P1.1 has already frozen the accepted baseline for AI Datacenter, CXO, Satellite, Low Altitude, Resource Swing, Semiconductor, Advanced Manufacturing, and Stable Growth. This document now records the accepted narrow Stable Growth baseline: `stable_growth + 600406`.

`stable_growth` must not be interpreted as a low-risk stock recommendation, defensive-stock label, dividend-stock screen, or valuation shortcut. It is an evidence-gated research-question matrix that asks whether stable growth is actually supported by revenue quality, margin quality, cash-flow quality, collection quality, capex discipline, balance-sheet resilience, and shareholder-return durability.

The expansion remains an independent Research Intelligence artifact:

```text
evidence_pack_<code>.json
+ optional P0 research intelligence artifacts
-> research_intelligence_p1_<code>.json
-> research_questions_p1_<code>.json
-> research_questions_p1_<code>.md
```

`output/research_intelligence_p1_*` and `output/research_questions_p1_*` are generated runtime artifacts and should not be committed.

It must not become a trading system, valuation model, technical-analysis layer, dashboard panel, connector project, or deterministic scoring input.

## 2. Non-Negotiable Boundaries

This design is limited to `strategy_type=stable_growth`.

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
- feed P1.1 back into deterministic conclusions;
- treat `stable_growth` as a positive quality label by itself.

Preserve the P1.1 interpretation guards:

- Classification is not conclusion. Do not write "the company is stable_growth, therefore operations are stable".
- Revenue growth is not stable growth.
- Contract liabilities are partial proxy only and are not backlog, confirmed orders, or future revenue.
- Receivable growth is not high-quality revenue.
- Single-period operating cash-flow improvement is not long-term cash-flow stability.
- Single-period positive `revenue_yoy` plus same-direction `operating_cashflow` is only a financial observation, not stable-growth quality or multi-period stability evidence.
- Dividend or payout ratio is not sustainable shareholder return unless free cash flow, debt, capex, and earnings-quality evidence support it.
- Capex is not capacity release, utilization, future revenue, or growth conversion.
- Single-period high ROE is not long-term competitiveness.
- Valuation metrics are evidence-sufficiency context only. They must not become target price, upside / downside, buy / sell language, or position advice.

## 3. Current Evidence-Pack Capability

Current `evidence_pack` may have:

- `stock.code`, `stock.name`, `stock.strategy_type`, `stock.sub_type`.
- `stock.status`, `stock.confidence`, `stock.fundamental_score` as read-only context only.
- `basic_info.industry`.
- `basic_info.main_business`.
- `business_composition[]` with segment name, classification type, period, revenue ratio, revenue, gross margin, and profit when present.
- `financial_metrics.period`, `revenue`, `revenue_yoy`, `gross_margin`, `net_margin`, `net_profit`, `deducted_net_profit`, `operating_cashflow`, `accounts_receivable`, `contract_liabilities`, `inventory`, `capex`, `roe`, and debt / liquidity fields when present.
- `valuation_metrics` as explainability context only; no target price or trading framing.
- `confidence_basis.missing_fields`, `confidence_basis.data_coverage`, and `confidence_basis.confidence_breakdown`.
- `enhanced_must_track_indicators[]`.
- `risk_flags`, `unknown_or_missing_evidence`, `missing_fields`, `data_limitations`, `source_trace_summary`, and `forbidden_terms_check`.

Current `evidence_pack` usually does not reliably have:

- Multi-period revenue, margin, ROE, ROIC, cash-flow, receivable, inventory, capex, payout, and debt trend tables.
- Customer retention, renewal, repeat-order, churn, or revenue cohort data.
- True backlog, signed orders, delivery schedule, cancellation history, or order-to-revenue conversion.
- Customer concentration by customer, receivable balance by customer, aging, overdue receivables, DSO, or bad-debt provision detail.
- Product price, volume, unit cost, pricing formula, or price-renewal mechanism.
- Maintenance capex vs expansion capex split.
- ROIC, invested capital, WACC, or normalized return-on-capital series.
- Dividend history, payout ratio history, buyback details, free-cash-flow coverage history, or capital-allocation policy.
- Non-recurring item detail, one-off profit bridge, asset-disposal income, government subsidy split, or impairment detail.
- Independent multi-source consensus beyond source-bucket counting.

Because `stable_growth` is inherently multi-period, many rows must remain `missing` or `not_assessable` in P1.1 when only a current evidence pack is available.

## 4. Driver Factor Matrix Contract

Every `stable_growth` driver row must use the existing P1.1 driver-factor contract:

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

The matrix is evidence-pack-only for P1.1. Future connector or data-model needs are recorded as missing evidence, not implemented in this phase.

Universal transmission rule:

- If no concrete field or data point in `evidence_pack` can verify the company transmission path, `company_transmission_path` must be exactly: `传导路径无法从当前证据包验证`.
- The corresponding `confidence_cap` must be `not_assessable`.
- The row must explain the missing bridge through `missing_evidence`, `not_assessable_reason`, and `research_question`.
- Generic labels, industry identity, or `strategy_type=stable_growth` cannot be used as transmission evidence.
- Industry type, product attributes, rigid demand, necessity wording, infrastructure attributes, policy protection, SOE / central-SOE ownership, or similar generic business attributes must not be used as company_transmission_path evidence for demand durability or revenue stability.
- Demand durability and revenue stability must come from company-level evidence such as multi-period revenue, customer retention, repeat order, pricing renewal, collection, or cash conversion evidence.
- Do not write transmission paths equivalent to "grid equipment is rigid-demand infrastructure, therefore company demand is stable". Industry context can frame a research question, but it cannot replace company-level evidence.

Research-question de-duplication rule:

- Contract-liability-related drivers must either be merged or clearly separated by missing bridge: order visibility, contract liabilities as partial proxy, and contract liabilities overread must not generate three duplicate questions about the same field.
- Receivable-related drivers must either be merged or clearly separated by missing bridge: collection quality and receivables masking collection risk must not generate duplicate questions unless one asks for aging / DSO / overdue evidence and another asks for customer or revenue bridge evidence.
- Free-cash-flow, dividend, and payout drivers should collapse into a small number of integrated questions, such as FCF quality and dividend sustainability. They must not generate four repetitive shareholder-return questions.
- If multiple driver rows are retained, generated questions must avoid obvious repetition and explicitly identify the different missing bridge for each row.

## 5. Stable Growth Driver Factor Matrix

### 5.1 Business / Demand Drivers

| Driver factor | required_evidence | available_evidence from current evidence_pack | missing_evidence / future data need | company_transmission_path rule | not_assessable condition | research_question | interpretation_guard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Recurring revenue or repeat-order quality | Revenue by product / service; repeat-order or renewal rate; customer cohort; contract duration; revenue recognition; collection | `business_composition[]`, `financial_metrics.revenue`, `contract_liabilities`, `operating_cashflow`, and receivables may exist | Renewal / repeat-order rate; churn; customer cohort; order-to-revenue and collection bridge | Valid only when the path cites concrete product / service revenue plus repeat-order, renewal, or contract evidence. If only revenue growth or company label exists, use `传导路径无法从当前证据包验证`. | Mark `not_assessable` when repeat-order / renewal / cohort evidence is absent. | Is recurring or repeat revenue supported by disclosed renewal, repeat-order, contract, revenue-recognition, and collection evidence? | Do not treat revenue growth, historical size, or `stable_growth` label as recurring revenue. |
| Customer stability | Top customer revenue share; customer tenure; renewal / retention; customer payment behavior; receivable by customer | Aggregate revenue, receivables, operating cash flow, and business segments may exist | Top customer list; concentration trend; customer tenure; collection by customer; customer churn | Valid only when customer-specific or concentration evidence exists. Aggregate receivables and revenue can only show financial observations. | Mark `not_assessable` when customer names, concentration, tenure, or payment behavior are missing. | Which customers support stable revenue, and is their retention visible in orders, revenue, receivables, and cash collection? | Do not infer customer stability from industry position or aggregate revenue. |
| Product / service demand durability | Product / service segment revenue; end-market demand; replacement / maintenance demand; price / volume; customer use case; multi-period demand evidence | `basic_info.main_business`, `business_composition[]`, revenue and margin may exist | End-market demand series; price / volume split; product lifecycle; replacement demand; customer order evidence | A concrete path may cite segment and financial fields as exposure only. Durability needs multi-period demand, order, customer, collection, cash-conversion, or price / volume evidence. | Mark `not_assessable` when demand durability lacks multi-period product, customer, order, collection, cash-conversion, or price / volume support. | Is demand durable because company-level multi-period revenue, repeat-order, customer retention, pricing renewal, collection, or cash-conversion evidence proves it? | Do not treat industry type, product attribute, rigid demand, infrastructure, policy protection, SOE / central-SOE status, stable industry wording, or one-period revenue growth as durable demand. |
| Order visibility | Signed orders; true backlog; delivery schedule; cancellation history; shipment / acceptance; revenue recognition; collection | Contract liabilities may exist as partial proxy; revenue and cash flow may exist | True backlog; signed order table; order duration; cancellation; shipment; revenue recognition terms | Valid only when true orders / backlog or signed contract evidence exists. Contract liabilities can only create a partial-proxy path and must not be called backlog. | Mark `not_assessable` when true order / backlog evidence is absent, or when only contract liabilities exist. | What true order, backlog, delivery, cancellation, shipment, and revenue-recognition evidence supports visibility? | Contract liabilities are partial proxy only, not backlog or confirmed future revenue. |
| Contract liabilities as partial proxy only | Contract liabilities; linked customer / order / project; prepayment terms; revenue-recognition schedule; comparison with revenue and cash flow | `financial_metrics.contract_liabilities` may exist; revenue and operating cash flow may exist | Customer / order mapping; prepayment terms; project mapping; revenue-recognition schedule | Valid only as "partial proxy" when contract liabilities exist. If no linked order / customer / terms exist, path must state only the financial field, or fallback if field is absent. | Mark `not_assessable` for backlog / order visibility when contract liabilities are unlinked or absent. | What customer, order, or project do contract liabilities correspond to, and why should they remain only a partial visibility proxy? | Do not convert contract liabilities into backlog, signed orders, future revenue, or stability proof. |
| Customer concentration | Top customer revenue share; top-five customer share; segment / customer mapping; receivable by customer; trend | Business composition and aggregate receivables may exist | Top customer revenue share; customer-level receivables; concentration trend; dependency risk | Valid only when customer concentration fields or customer-specific evidence exist. | Mark `not_assessable` when top customer / top-five fields and customer receivable data are missing. | Does customer concentration support stability, or does it create dependency and collection risk? | Do not infer diversification from broad business segments alone. |
| Pricing power evidence | Price changes; price formula; volume; gross margin by product; cost pass-through; renewal pricing; customer acceptance | Gross margin and segment gross margin may exist; revenue may exist | Product price / volume; unit cost; pricing formula; contract renewal terms; competitor price evidence | A concrete path may cite gross margin as an observation, but pricing power needs price, cost, volume, and customer acceptance evidence. | Mark `not_assessable` when price / volume or renewal pricing evidence is absent. | Is margin stability supported by pricing power, cost pass-through, product mix, or temporary cost movement? | Do not infer pricing power from stable or high gross margin alone. |
| Business mix stability | Multi-period revenue mix; segment margins; product / customer mix; new / old business split; discontinued operations | Current `business_composition[]` may show one-period revenue ratio and segment margin | Multi-period segment mix; customer mix trend; product-line trend; segment restatement history | Valid only when business composition fields exist; stability requires multi-period mix evidence. | Mark `not_assessable` when only one-period mix exists or segment data is absent. | Has business mix remained stable across periods, and which product / service lines drive revenue and margin quality? | Do not treat one-period segment composition as long-term mix stability. |

### 5.2 Financial Quality Drivers

| Driver factor | required_evidence | available_evidence from current evidence_pack | missing_evidence / future data need | company_transmission_path rule | not_assessable condition | research_question | interpretation_guard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Revenue growth quality | Revenue; revenue YoY; segment revenue; price / volume; customer orders; receivables; operating cash flow; multi-period trend | `financial_metrics.revenue`, `revenue_yoy`, segment revenue, receivables, and operating cash flow may exist | Price / volume split; customer / order bridge; multi-period revenue, cash conversion, receivables, inventory, and collection trend | Valid only when revenue is checked together with cash flow, receivables, inventory, and business / customer bridge. If only revenue growth exists, use fallback for quality. | Mark `not_assessable` when revenue growth lacks multi-period cash-flow, collection, receivables, inventory, customer, order, or segment bridge. | Is revenue growth supported by cash collection, customer / order evidence, receivables / inventory discipline, and stable business mix rather than receivable build or one-off items? | Revenue growth is not stable growth or revenue quality by itself. Single-period revenue and same-direction operating cash flow remain a financial observation unless multi-period cash conversion, receivables, inventory, customer, or order evidence supports stability. |
| Gross margin stability | Multi-period gross margin; segment margin; product mix; price / cost / volume; cost pass-through; inventory accounting | Current gross margin and segment gross margin may exist | Multi-period margin series; product cost; price / volume; mix shift; cost pass-through terms | Valid only for current-period margin observation unless multi-period and driver evidence exists. | Mark `not_assessable` for stability or pricing conclusion when only one-period margin exists. | Is gross margin stable because of product mix, pricing, cost control, or temporary factors, and what evidence separates them? | Do not infer product advantage or pricing power from margin stability without product / price / cost evidence. |
| Net margin stability | Multi-period net margin; gross margin; expense ratio; tax; non-recurring items; impairment; interest expense | `net_margin`, gross margin, net profit, deducted net profit may exist | Expense breakdown; tax; impairment; non-recurring item bridge; multi-period trend | Valid only when net margin and profit fields are cited; stability needs multi-period and one-off item evidence. | Mark `not_assessable` when expense / one-off / multi-period evidence is missing. | Does net margin stability come from operating quality rather than expense timing, subsidy, asset disposal, impairment reversal, or tax effects? | Do not treat one-period net margin as durable profitability. |
| Operating cash flow conversion | Operating cash flow; revenue; net profit; receivables; inventory; payables; customer payment terms; multi-period conversion | Operating cash flow, revenue, net profit, receivables, inventory may exist | Payables; cash conversion cycle; customer terms; multi-period operating cash-flow conversion | A concrete path may cite current cash flow, revenue, profit, receivables, and inventory; long-term stability needs multi-period conversion. | Mark `not_assessable` for durable conversion when only one-period operating cash flow exists. | Does operating cash flow validate revenue and profit quality after receivables, inventory, payables, and customer payment terms? | Single-period cash-flow improvement is not long-term cash-flow stability. |
| Accounts receivable / collection quality | Receivables; revenue; receivable aging; overdue amount; bad-debt provision; DSO; customer mix; multi-period trend | `accounts_receivable`, revenue, operating cash flow may exist | Aging; overdue receivables; customer-specific receivables; bad-debt provision; DSO trend | Valid only as aggregate collection observation unless aging / overdue / customer data exists. | Mark `not_assessable` when aging, overdue, bad-debt, DSO, or customer receivable data is absent. | Are receivables consistent with revenue quality, or do they mask collection pressure and customer credit risk? | Receivable growth is not high-quality revenue and may signal collection risk. |
| Inventory / working-capital discipline | Inventory; revenue; cost of goods; product inventory split; payables; prepayments; production / sales bridge; multi-period turnover | Inventory, revenue, operating cash flow, receivables may exist | Inventory breakdown; aging; write-down; turnover; payables; product sales bridge | Valid only as aggregate working-capital observation unless inventory split and sales bridge exist. | Mark `not_assessable` for demand or discipline conclusion when only aggregate inventory exists. | Does inventory reflect disciplined working-capital management, demand mismatch, production timing, or cost inflation? | Inventory build or decline is not direct demand proof without sales and product bridge. |
| Free cash flow | Operating cash flow; capex; maintenance vs expansion capex; working capital; debt service; dividend | Operating cash flow and capex may exist; free cash flow may be derivable as observation | Capex split; working-capital detail; debt service; dividend; multi-period free-cash-flow trend | A concrete path may cite derived `operating_cashflow - capex` only as a derived observation. Sustainability needs capex split and multi-period support. | Mark `not_assessable` when capex split or multi-period free cash flow is missing. | Is free cash flow positive and repeatable after maintenance capex, working-capital needs, and debt service? | Derived free cash flow is not shareholder-return capacity unless supported by capex, debt, and earnings quality. |
| ROE / ROIC stability | Multi-period ROE; ROIC; DuPont drivers; invested capital; leverage; asset turnover; margin; one-off items | ROE may exist; net margin, revenue, debt fields may exist | ROIC; invested capital; multi-period return series; DuPont components; one-off adjustments | Valid only as current return observation unless multi-period and driver evidence exists. | Mark `not_assessable` when only single-period ROE exists or ROIC / driver evidence is absent. | Are ROE and ROIC stable because of operating return quality rather than leverage, one-off profit, or accounting effects? | Single-period high ROE is not long-term competitiveness. |
| Debt / liquidity / interest burden | Debt amount; cash; interest expense; maturity; interest coverage; operating cash flow; capex commitments; dividend | Some debt / liquidity fields may exist; operating cash flow and capex may exist | Debt maturity; interest rate; interest expense; restricted cash; covenants; refinancing schedule | Valid only when debt, liquidity, and interest fields exist. Cash flow and capex alone cannot prove financing resilience. | Mark `not_assessable` when debt, interest burden, maturity, or liquidity evidence is absent. | Can the balance sheet support operations, capex, and shareholder returns through a downturn? | Do not infer balance-sheet resilience without debt, liquidity, maturity, and cash-flow evidence. |
| Capex discipline: maintenance vs expansion | Capex total; maintenance capex; expansion capex; project mapping; utilization; revenue / cash-flow bridge; funding source | Aggregate capex may exist | Capex split; project list; acceptance; utilization; replacement need; revenue bridge; funding source | A concrete path may cite capex only as cash outflow. It must not imply capacity, utilization, or future revenue. | Mark `not_assessable` when maintenance / expansion split or project bridge is missing. | Is capex maintaining existing earnings power, expanding capacity, or consuming cash without visible revenue / utilization bridge? | Capex is not capacity release or future revenue. |

### 5.3 Shareholder-Return / Durability Drivers

| Driver factor | required_evidence | available_evidence from current evidence_pack | missing_evidence / future data need | company_transmission_path rule | not_assessable condition | research_question | interpretation_guard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Dividend capacity | Dividend; operating cash flow; free cash flow; capex split; debt / liquidity; profit quality; multi-period payout | Cash flow and capex may exist; dividend fields may be absent | Dividend history; payout ratio; free-cash-flow coverage; debt maturity; capex plan; capital-allocation policy | Valid only when dividend is checked against free cash flow, debt, capex, and profit quality. | Mark `not_assessable` when dividend or any support leg is missing. | Is dividend capacity covered by repeatable free cash flow after capex, debt service, and working-capital needs? | Dividend amount or yield is not sustainable return without free-cash-flow and balance-sheet support. |
| Payout sustainability | Payout ratio; earnings quality; free cash flow; capex needs; debt maturity; management policy; multi-period record | Net profit, operating cash flow, capex may exist | Payout ratio history; dividend policy; buyback history; capex commitments; debt maturity | Valid only when payout is linked to cash flow, debt, and capex evidence. | Mark `not_assessable` when payout history, free cash flow, or capex / debt support is missing. | Can payout be sustained without weakening capex discipline, liquidity, or balance-sheet resilience? | Payout ratio is not shareholder-return quality by itself. |
| Earnings quality | Net profit; deducted net profit; cash conversion; non-recurring items; impairment; subsidy; asset disposal; receivables | Net profit, deducted net profit, operating cash flow, receivables may exist | Non-recurring item detail; impairment; subsidy; asset-disposal gains; multi-period bridge | Valid only when profit fields are checked against cash flow and one-off item evidence. | Mark `not_assessable` when non-recurring item detail and multi-period evidence are missing. | Are earnings supported by operating profit and cash conversion rather than one-off gains or accounting items? | Profit growth is not earnings quality without cash-flow and one-off item checks. |
| Balance-sheet resilience | Debt, cash, liquidity, working capital, interest burden, maturity, capex commitments, off-balance-sheet obligations | Some debt / cash / working-capital fields may exist | Debt maturity; restricted cash; covenants; lease liabilities; guarantees; off-balance commitments | Valid only when debt / liquidity / maturity / obligation nodes exist. | Mark `not_assessable` when balance-sheet and maturity detail is incomplete. | Can the balance sheet absorb weaker demand, collection delays, or capex pressure? | Low apparent leverage is not resilience if maturity, liquidity, and obligations are missing. |
| Cyclicality / downturn resilience | Multi-period revenue, margin, cash flow through downturn; customer stability; pricing; backlog; working capital | Current revenue, margin, cash flow may exist | Downturn-period series; customer retention; price / volume; order cancellation; stress-period collection | Valid only with multi-period downturn evidence or explicit customer / contract resilience evidence. | Mark `not_assessable` when current pack lacks downturn-period evidence. | How did revenue, margin, cash flow, receivables, and capex behave during weak demand periods? | Stable label is not downturn resilience without multi-period evidence. |
| One-off profit / non-recurring item risk | Non-recurring gains / losses; deducted net profit; asset disposal; subsidy; fair-value gain; impairment; tax effects | Net profit and deducted net profit may exist | Detailed non-recurring item note; asset disposal; subsidy; impairment; fair-value movements; tax reconciliation | Valid only when net profit vs deducted profit or non-recurring item detail exists. | Mark `not_assessable` when one-off item detail is absent. | How much of profit depends on non-recurring items, and does recurring operating profit support stable growth? | Do not treat reported net profit as recurring earnings without non-recurring item checks. |

### 5.4 Risk Drivers

| Driver factor | required_evidence | available_evidence from current evidence_pack | missing_evidence / future data need | company_transmission_path rule | not_assessable condition | research_question | interpretation_guard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Revenue growth without cash-flow support | Revenue growth; operating cash flow; receivables; inventory; payables; customer payment terms; multi-period trend | Revenue YoY, operating cash flow, receivables, inventory may exist | Payables; customer terms; cash conversion cycle; multi-period trend; customer / order bridge | Valid only when revenue and cash-flow / working-capital fields are cited together as observations. Stability requires multi-period revenue, cash conversion, receivables, inventory, customer, or order support. | Mark `not_assessable` when cash-flow or working-capital fields are missing; mark only `partial / low` or `not_assessable` when revenue and operating cash flow are single-period only. | Is revenue growth accompanied by repeatable cash conversion, or is growth absorbed by receivables, inventory, or payment delays? | Even if single-period `revenue_yoy` is positive and `operating_cashflow` moves in the same direction, do not combine them into stable-growth quality. Single-period revenue plus OCF is a financial observation, not multi-period stability evidence; confidence can rise only with multi-period revenue, cash conversion, receivables, inventory, customer, or order support. |
| Margin stability without product / pricing evidence | Gross margin; net margin; product price; unit cost; mix; renewal pricing; customer acceptance | Gross margin and net margin may exist | Price / volume; unit cost; product mix; pricing formula; competitor pricing | Valid only as margin observation unless product / price / cost evidence exists. | Mark `not_assessable` when pricing and product evidence is missing. | Does margin stability have product, pricing, cost, and mix support, or is it an unexplained accounting observation? | Margin stability does not prove pricing power or product moat. |
| Receivables growth masking collection risk | Receivables; revenue; operating cash flow; aging; overdue; bad-debt provision; customer concentration | Receivables, revenue, operating cash flow may exist | Aging; overdue; bad-debt provision; customer receivables; DSO trend | Valid only as aggregate collection-risk observation unless aging / customer data exists. | Mark `not_assessable` for collection quality when aging and customer evidence is absent. | Are rising receivables masking weaker collection quality despite revenue growth? | Receivable growth is not revenue quality and may be a negative working-capital signal. |
| Inventory build without sales bridge | Inventory; revenue; sales volume; product inventory split; production / sales reconciliation; write-downs | Inventory and revenue may exist | Product inventory; sales volume; production volume; aging; write-down; turnover | Valid only as aggregate inventory observation unless product and sales bridge exists. | Mark `not_assessable` for demand interpretation when sales bridge is missing. | Is inventory build tied to confirmed sales / delivery timing, or does it signal demand mismatch and write-down risk? | Inventory build without sales bridge cannot be interpreted as future demand. |
| Capex expansion without revenue / utilization bridge | Capex; project list; maintenance vs expansion split; acceptance; utilization; revenue contribution; funding | Aggregate capex may exist | Project-level capex; utilization; acceptance; revenue contribution; funding source | A path may cite capex as cash outflow only. No capacity, utilization, or revenue conversion may be inferred. | Mark `not_assessable` when project / utilization / revenue bridge is absent. | Is capex disciplined, or is expansion consuming cash before utilization and revenue are verified? | Capex is not capacity release or future revenue. |
| Contract liabilities overread as backlog | Contract liabilities; true backlog; signed orders; customer / order mapping; revenue-recognition schedule | Contract liabilities may exist | True backlog; signed-order table; customer mapping; delivery / cancellation evidence | Valid only as partial-proxy risk row when contract liabilities exist. If absent, fallback. | Mark `not_assessable` for backlog when true orders or mapping are missing. | What prevents contract liabilities from being overread as backlog or confirmed future revenue? | Contract liabilities are partial proxy only. |
| Dividend overread without free cash flow | Dividend / payout; operating cash flow; capex; free cash flow; debt; liquidity; earnings quality | Operating cash flow, capex, profit may exist; dividend may be missing | Dividend / payout history; debt maturity; capex split; non-recurring items; free-cash-flow trend | Valid only when dividend is linked to all support legs. | Mark `not_assessable` when dividend, free cash flow, debt, capex, or earnings quality support is incomplete. | Could dividend or payout be overstated as durable return without free cash flow, debt, capex, and earnings-quality support? | Dividend or payout alone is not shareholder-return sustainability. |
| Stable label overread without multi-period evidence | Multi-period revenue, margin, cash flow, ROE / ROIC, receivables, inventory, capex, payout, customer evidence | Current one-period financial metrics may exist | Multi-period trend tables; customer retention; order visibility; downturn performance | Valid only when multi-period evidence exists. Otherwise fallback for stability conclusion. | Mark `not_assessable` when current evidence pack lacks multi-period stability support. | What multi-period evidence is required before using "stable" as an analytical conclusion? | `stable_growth` is a routing label, not evidence of stability. |

## 6. Proxy Boundaries

`stable_growth` needs several proxies, but each proxy has a strict boundary:

- Dividend: can be considered only after free cash flow, debt, capex, working capital, and earnings quality are checked. Dividend amount, dividend yield, or payout ratio alone cannot prove sustainable shareholder return.
- ROE: a single-period ROE value is a return observation, not durable competitiveness. ROE must be decomposed into margin, turnover, leverage, and one-off effects, and ideally cross-checked with ROIC.
- Free cash flow: `operating_cashflow - capex` may be a derived observation only. It is not durable free cash flow without maintenance / expansion capex split and multi-period evidence.
- Receivables: aggregate receivable change is a collection-risk clue, not proof of revenue quality. Aging, overdue, bad-debt provision, customer mix, and DSO are needed.
- Capex: aggregate capex is cash outflow, not capacity release, utilization, order conversion, or future revenue. Maintenance vs expansion capex must be separated before making discipline judgments.
- Contract liabilities: can only be an order-visibility partial proxy. It is not backlog, signed orders, delivery schedule, or revenue conversion.
- Valuation: PE / PB / PS or other valuation metrics may frame evidence sufficiency only. Chinese questions that cite `valuation_metrics` must use an evidence-sufficiency wording such as "当前 evidence pack 中哪些证据足以支撑或解释当前估值背景，哪些证据仍缺失？". They must not ask whether valuation is reasonable, high, low, or supported by the current price, and must not mention upside, downside, target price, buy, sell, or hold.

## 7. Differentiation From Adjacent Strategy Types

### 7.1 `stable_growth` vs `resource_core`

`resource_core` is a resource-company framework. Its stability question is built around commodity exposure, reserve / resource quality, production and sales volume, cost position, sustaining capex, commodity-cycle cash flow, balance-sheet resilience, and dividend capacity.

`stable_growth` is not commodity-first. Its stability question is built around business demand durability, repeat-order or customer stability, revenue quality, margin quality, cash conversion, collection quality, capex discipline, ROE / ROIC stability, debt burden, and payout sustainability.

Key boundary:

- If stability depends on commodity price, reserve life, production volume, unit cash cost, hedging, or sustaining capex for mines / resource assets, it belongs in `resource_core`.
- If stability depends on repeat demand, customer quality, pricing evidence, collection quality, and capital discipline across non-resource businesses, it may be a `stable_growth` question.
- `resource_core` dividend capacity must check commodity-cycle and sustaining-capex legs; `stable_growth` dividend capacity must check free cash flow, capex discipline, debt / liquidity, and earnings quality.

### 7.2 `stable_growth` vs `right_trend_growth`

`right_trend_growth` is a high-growth / trend-realization framework. It asks whether a favorable industry trend, policy demand, AI / datacenter / supply-chain expansion, or other high-growth driver has translated into company revenue, orders, margins, cash flow, and risk signals.

`stable_growth` is quality-first and durability-first. It asks whether growth is repeatable, collectible, cash-generative, margin-stable, balance-sheet-supported, and not overread from one-period growth or theme labels.

Key boundary:

- If the core research question is "has a high-growth trend realized into company revenue / orders / margins", use `right_trend_growth` or a more specific accepted expansion.
- If the core research question is "is current growth stable and high-quality after checking customers, collection, cash flow, capex, ROE / ROIC, and payout support", use `stable_growth`.
- A company can have revenue growth and still fail the `stable_growth` evidence gate if cash conversion, receivables, capex, customer stability, or multi-period evidence is weak or missing.

## 8. Primary Sample Gate

Sample Gate, implementation, and acceptance have passed for first implementation, with a narrow implementation target and conservative evidence expectations.

Stable Growth Sample Gate results:

- `600406` 国电南瑞: refreshed result is `strategy_type=stable_growth`, `status=neutral`, `confidence=high`; `financial_metrics` are available; `business_composition` has 11 segments. This is the primary implementation sample.
- `002028` 思源电气: refreshed result is `strategy_type=stable_growth`, `status=neutral`, `confidence=high`; `financial_metrics` are available; `business_composition` has 12 segments. This is the validation sample.
- `600276` 恒瑞医药: refreshed result remains `unknown / insufficient_data`. It must not be used as the primary or validation sample for first Stable Growth implementation.

First implementation scope:

- `strategy_type=stable_growth` only.
- Primary sample: `600406` 国电南瑞.
- Validation sample: `002028` 思源电气.
- Excluded sample: `600276` 恒瑞医药.
- Do not modify classifier rules or force `strategy_type`.
- Do not modify connector behavior, add data sources, or bypass current evidence-pack availability.
- Do not modify deterministic pipeline behavior, scoring, readiness, status, confidence, score, `sub_type`, HTML, Dashboard, or generated output semantics.

Implementation pre-checks for `600406`:

- Confirm which of the 11 `business_composition` segments have non-zero `revenue`, `revenue_ratio`, or `gross_margin`.
- Confirm whether `financial_metrics.roe` has an actual numeric value.
- Confirm whether `net_profit` and `deducted_net_profit` are both present, as the minimum one-off item proxy.
- Confirm actual field status for `operating_cashflow`, `accounts_receivable`, `inventory`, `capex`, `contract_liabilities`, and debt / liquidity fields.
- Confirm whether dividend / payout fields exist. If they do not exist, dividend / payout drivers must be `missing / not_assessable`.

Implementation acceptance expectations:

- For `600406`, more than 55% `missing / not_assessable` rows is expected and correct. It is not an implementation failure.
- Accepted output recorded `missing / not_assessable = 19/33 = 57.58%`.
- The `stable_growth` label must not appear inside `company_transmission_path`.
- "经营稳健" or "稳定增长" must not be used as a non-fallback conclusion.
- Industry rigid demand, infrastructure attributes, policy protection, or SOE / central-SOE ownership must not be used as demand durability evidence.
- Single-period `revenue_yoy` plus `operating_cashflow` must not generate a conclusion that growth quality is stable.
- Contract liabilities must not be written as backlog.
- Dividend / payout must not be written as sustainable shareholder return unless free cash flow, debt, capex, and earnings-quality evidence support it.
- Single-period high ROE must not be written as long-term competitiveness.
- Capex must not be written as capacity release or future revenue.
- Valuation must not be written as valuation high / low, target price, upside, or trading judgment.

Pharmaceutical / biotech exclusion caution:

- `600276` is excluded because the current classifier output remains `unknown / insufficient_data`.
- Even if a pharmaceutical company is later reclassified, innovative-drug or biotech R&D pipelines may make it unsuitable for the ordinary `stable_growth` framework.
- If a candidate has significant innovative-drug / biotech pipeline exposure, such as high R&D ratio or material clinical-stage pipeline, implementation must separately assess whether pipeline risk invalidates the `stable_growth` analytical premise.
- Do not assume that pharmaceutical companies are suitable for `stable_growth`.

## 9. Not-Assessable / Missing Evidence Rules

Use `missing` when:

- The driver has a required evidence field that is expected but absent from the current pack.
- The row can still describe what was checked and what field is missing.
- The absence itself defines a follow-up research question.

Use `not_assessable` when:

- The driver conclusion would require a company-specific transmission path that cannot be verified from evidence-pack fields.
- The row would otherwise rely on label deduction, industry narrative, generic stability wording, or a proxy beyond its boundary.
- The current evidence is single-period but the driver requires multi-period stability.
- Single-period positive `revenue_yoy` and same-direction `operating_cashflow` are the only supportive fields for a stability conclusion.
- Single-period revenue plus OCF direction is available but multi-period revenue, cash conversion, receivables, inventory, customer, or order evidence is absent.
- Contract liabilities are the only order-visibility evidence.
- Dividends or payout are present but free cash flow, debt, capex, and earnings-quality support is incomplete.
- Dividend or payout fields are absent; in this case dividend / payout drivers must be `missing / not_assessable`.
- ROE is present only as a single-period number.
- Capex exists only as an aggregate cash-outflow field.
- Receivables exist only as aggregate balance-sheet values without aging, customer, DSO, overdue, or provision evidence.
- `valuation_metrics` are present but the question would require valuation judgment rather than evidence-sufficiency framing.

When a driver is `not_assessable`, `confidence_cap` must be `not_assessable` and `company_transmission_path` must use the exact fallback phrase when no concrete field-level bridge exists:

```text
传导路径无法从当前证据包验证
```

Status mapping table:

| Evidence condition | `data_availability_status` | `confidence_cap` | Required behavior |
| --- | --- | --- | --- |
| Specific segment evidence plus financial fields, but only one period | `partial` | `low` | State the segment and financial observation only; do not conclude stability. |
| Aggregate financial fields only, with no segment bridge | `partial` | `low` | Treat as financial observation; generate a missing bridge question for segment / customer / order support. |
| Only `strategy_type=stable_growth` label, with no concrete fields | `not_assessable` | `not_assessable` | Use the fallback transmission path and do not generate a stability conclusion. |
| Driver requires multi-period evidence but only one period exists | `not_assessable` | `not_assessable` | Explain that multi-period stability cannot be assessed. |
| Expected evidence type is entirely absent | `missing` | `not_assessable` | State the absent field or evidence type and generate a research question. |
| Contradictory signals exist, such as revenue growth with worsening OCF, receivables materially increasing, inventory build, or capex pressure | `partial` | `low` | List the contradictory signals explicitly and generate a research question about the conflict. |

Valuation question rule:

- If `valuation_metrics` are referenced, Chinese generated questions must use evidence-sufficiency wording, for example: "当前 evidence pack 中哪些证据足以支撑或解释当前估值背景，哪些证据仍缺失？"
- The following valuation / trading phrasings are forbidden: "估值是否合理", "估值是否偏高/偏低", "是否支撑当前价格", "上涨空间", "下跌空间", "目标价", "买入", "卖出", and "持有".
- `valuation_metrics` can only be evidence-sufficiency context. They must not become trading judgment, valuation judgment, target-price logic, or upside / downside framing.

## 10. Future Data Needs

Future versions may need these data fields, but P1.1 design must not add new data sources:

- Multi-period financial metrics: revenue, gross margin, net margin, operating cash flow, free cash flow, receivables, inventory, capex, ROE, ROIC, debt, interest expense, and payout.
- Product / service price and volume split.
- Product-line and segment margin trends.
- True backlog, signed orders, delivery schedule, cancellation, shipment, acceptance, and revenue-recognition schedule.
- Customer concentration, customer tenure, renewal / retention, repeat-order rate, customer-specific receivables, and collection behavior.
- Receivable aging, overdue balance, bad-debt provision, DSO, and customer payment terms.
- Inventory split, aging, write-downs, turnover, and product sales bridge.
- Maintenance capex vs expansion capex, project progress, utilization, revenue contribution, and funding source.
- Debt maturity, interest-rate structure, restricted cash, covenants, refinancing needs, and off-balance-sheet obligations.
- Dividend history, payout history, buybacks, capital-allocation policy, and free-cash-flow coverage.
- Non-recurring item detail, subsidy, asset-disposal gain, impairment, fair-value movement, and tax reconciliation.
- Downturn-period performance data for revenue, margins, cash flow, receivables, capex, and payout.

## 11. Implementation Recommendation

P1.1 Stable Growth implementation and acceptance are complete. Keep the first-version baseline frozen at `stable_growth + 600406` unless a future design / implementation / acceptance cycle expands it.

Rationale:

- The Sample Gate, implementation, and acceptance have passed for `600406` as the primary sample and `002028` as the validation / boundary sample.
- `600276` remains `unknown / insufficient_data` and is excluded from first implementation.
- `stable_growth` still requires multi-period and customer / collection evidence, while current P1.1 can only use the current evidence pack. Therefore first implementation must be conservative and must preserve many `missing / not_assessable` rows.
- Implementation must not force-fit the strategy type, weaken classifier boundaries, add data sources, or reinterpret one-period observations as stable-growth conclusions.
- Acceptance recorded `missing / not_assessable = 19/33 = 57.58%`, which is expected and correct.

Frozen first-version scope:

1. Keep `strategy_type=stable_growth` first-version support limited to primary sample `600406`.
2. Use `600406` 国电南瑞 as the primary implementation sample and `002028` 思源电气 as the validation sample.
3. Keep `600276` 恒瑞医药 excluded unless a future gate separately addresses classifier status and innovative-drug / biotech pipeline suitability.
4. Preserve the exact safety boundaries: no classifier changes, no forced `strategy_type`, no new data source, no deterministic pipeline changes, no scoring / readiness changes, no HTML / Dashboard work, and no output semantics changes.
5. Preserve research-question de-duplication for contract liabilities, receivables, FCF, dividend, and payout drivers.
6. Preserve valuation question wording as evidence-sufficiency context only.

## 12. External Audit Incorporation

The external Claude audit was incorporated into v1.1 before implementation; this sync records the post-acceptance baseline.

Implemented audit focus:

- Whether the `stable_growth` matrix remains an evidence-gated research-question matrix rather than a low-risk recommendation engine.
- Whether the implementation gate prevents forced classification and sample fitting.
- Whether proxy boundaries for dividend, ROE, free cash flow, receivables, capex, and contract liabilities are strict enough.
- Whether `company_transmission_path` fallback and `confidence_cap=not_assessable` are enforceable for every row without concrete evidence-pack support.
- Whether the design clearly separates `stable_growth` from `resource_core` and `right_trend_growth`.
