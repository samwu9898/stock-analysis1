# Fundamental AI Analyst Layer v1

## 1. Why Dashboard v1 Is Not the Final Shape

Dashboard v1 is a local Streamlit viewer for existing `fundamental_skill` outputs. It can run `real_stock_runner`, show `fundamental_<code>.json`, show selected raw data blocks, summarize data quality, and expose source traces.

That is useful for acceptance and debugging, but it is still a data display surface. It does not build a compact evidence pack, does not generate a model-ready analyst prompt, and does not produce an AI-written fundamental research report.

## 2. Positioning

The Fundamental AI Analyst Layer is a separate layer above the deterministic `fundamental_skill` pipeline.

It consumes:

- `output/fundamental_<code>.json`
- `output/raw_<code>.json`

It produces:

- `output/evidence_pack_<code>.json`
- `output/ai_prompt_<code>.md`
- `output/research_intelligence_<code>.json` when Research Intelligence P0 is requested.
- `output/research_questions_<code>.json` and `output/research_questions_<code>.md` when Research Intelligence P0 is requested.
- `output/research_intelligence_p1_<code>.json` when Research Intelligence P1.1 is requested.
- `output/research_questions_p1_<code>.json` and `output/research_questions_p1_<code>.md` when Research Intelligence P1.1 is requested.
- `output/reports/fundamental_report_prompt_<code>.md` for the HTML report chain when requested.
- `output/reports/fundamental_report_<code>.html` only after an existing formal `FundamentalHtmlReport` JSON is rendered.

It does not mutate the deterministic pipeline, call AkShare directly, connect to accounts, introduce technical indicators, implement `technical_skill`, or implement `trader_skill`.

Research Intelligence P0 sits after `evidence_pack` generation and before any optional display/reporting layer:

```text
evidence_pack
  -> research_intelligence_<code>.json
  -> research_questions_<code>.json / .md
  -> optional AI prompt / HTML report workflows
```

In P0 it is not connected to the HTML Report main chain. It does not call an LLM, does not fetch new data, and does not infer missing facts. It is a deterministic, rule-triggered, evidence-gated artifact for discovering research questions and manual-review / IR questions.

Research Intelligence P0.1 keeps the same chain and boundaries, but sharpens question templates. The workflow remains:

```text
evidence_pack
  -> research_intelligence_<code>.json
  -> research_questions_<code>.json / .md
```

P0.1 selects more industry-specific questions from `strategy_type`, `sub_type`, `missing_evidence`, and triggered `rule_id` instead of falling back to broad missing-field wording. It still does not call an LLM, does not fetch data, does not mutate deterministic pipeline outputs, and does not connect to the HTML Report main chain.

Research Intelligence P1.1 adds the accepted driver-factor matrix artifact after the evidence pack:

```text
evidence_pack
  -> research_intelligence_p1_<code>.json
  -> research_questions_p1_<code>.json / .md
```

P1.1 currently supports only these accepted strategy types and narrow slices: `ai_datacenter_infrastructure`, `life_science_cxo_services`, `satellite_communication_infrastructure`, `low_altitude_economy_infrastructure`, the first Resource slice `resource_swing` for primary sample `000426`, the first Semiconductor slice `semiconductor_cycle` for primary sample `002371`, the first Advanced Manufacturing slice `advanced_manufacturing_growth` for primary sample `002050`, and the first Stable Growth slice `stable_growth` for primary sample `600406`. It does not support `resource_core`; `601689` remains a later Advanced Manufacturing validation / boundary sample rather than first-version support; `002028` is Stable Growth validation / boundary only; `600276` is excluded from Stable Growth first-version support. It does not call an LLM, does not fetch new data, does not connect new sources, does not mutate deterministic pipeline outputs, and does not connect to the HTML Report main chain or Dashboard.

For Satellite, the P1.1 driver matrix remains evidence-pack-only and `not_assessable` first: satellite resources, transponder / bandwidth resources, capacity utilization, customer contract duration, lease / service pricing, customer concentration, satellite remaining life, replacement capex, launch / failure / insurance evidence, and related risk bridges must remain missing or `not_assessable` unless a concrete evidence-pack field or data point supports them.

For Low Altitude, the P1.1 driver matrix also remains evidence-pack-only and `not_assessable` first. Policy pilots, airspace / route approval, local-government spending, flight hours, flight sorties, platform dispatch volume, route / base / airspace resources, project contracts / acceptance, customer type, government / SOE collection cycle, capex-to-service-capacity bridge, and safety / regulatory events must remain missing or `not_assessable` unless concrete evidence-pack fields support them. Missing flight hours, flight sorties, platform dispatch volume, airspace / route approval, project acceptance, customer type, and government / SOE collection-cycle evidence must not be fabricated into facts.

For Resource, the P1.1 first implementation supports only `resource_swing + 000426`. Commodity price is not company revenue, commodity cycle is not company performance, reserves are not production, production is not sales unless both are disclosed and reconciled, capex is not capacity release, inventory movement is not demand judgment, and missing hedging disclosure must not be written as hedged or unhedged. `resource_core` remains design-only; steadiness and dividend capacity must not be written as facts.

For Semiconductor, the P1.1 first implementation supports only `semiconductor_cycle + 002371`, with equipment sub-chain as the first-version path. The multi-sample observation has completed after upstream data refresh and P1.1 reruns: `002371` is the positive sample, `688012 / 688981 / 603501 / 300604` are validation samples, and `300308 / 300476` are boundary / negative samples. The validation samples were not forced into the `002371` equipment first-version order logic; outside first-version support, P1.1 preserved `unsupported_pilot_strategy` / `not_assessable`, exact fallback transmission path wording, source-bucket independence, and the safety boundary. Materials / fabless / foundry / OSAT are not fully implemented and remain `not_applicable` / `not_assessable` boundaries under the first version. Semiconductor cycle is not company performance, localization narrative is not revenue realization, R&D ratio is not a technology barrier or moat, customer introduction / certification / qualification is not batch revenue, contract liabilities are not backlog, capex is not capacity release / utilization / delivery / revenue conversion, inventory movement is not demand judgment, and export controls / sanctions are not company operating benefit or damage facts without company-level impact evidence. Data-side caveat: the validation run still had `latest_news` missing because the raw news block reported `Invalid regular expression: invalid escape sequence: \u`; this does not affect the P1.1 boundary smoke conclusion.

For Advanced Manufacturing, the P1.1 first implementation supports only `advanced_manufacturing_growth + 002050`. The Advanced Manufacturing multi-sample observation is complete, and the `601689` boundary data completion smoke is complete. `601689` is a later validation / boundary sample and must not be treated as first-version support. In the boundary smoke, `601689` was recognized by the classifier as `advanced_manufacturing_growth` but correctly stayed outside first-version support with `unsupported_pilot_strategy` / `not_assessable`. It was not force-fit into the `002050` three-business-layer matrix for refrigeration / air-conditioning core business, automotive thermal management, and robotics / actuator / emerging business. Robotics theme exposure is not revenue realization; strategic layout wording and `news` / `latest_news` are not valid transmission nodes; refrigeration or automotive thermal-management revenue, gross margin, cash flow, receivables, inventory, or capex cannot proxy robotics realization. Tuopu large-customer or robotics narratives must not be written as realized revenue without direct evidence. Design-win / qualification / nomination is not batch revenue; contract liabilities are not backlog; capex is not capacity release, mass production, utilization, or revenue conversion; R&D ratio is not a technology barrier; receivable growth is not high-quality revenue; inventory movement is not demand judgment; valuation metrics are evidence-sufficiency context only and must not become target price, valuation-high/low, or trading judgment. The `601689` smoke preserved fallback `company_transmission_path`, `not_assessable`, source-bucket independence, and the safety boundary. Data-side caveat: `601689` `news` / `latest_news` still reports `Invalid regular expression: invalid escape sequence: \u`; this is an upstream/news data issue and does not affect the P1.1 boundary smoke conclusion.

For Stable Growth, the P1.1 first implementation supports only `stable_growth + 600406`. `002028` is validation / boundary only and must not be treated as first-version positive support; `600276` is excluded because the refreshed classifier result remains `unknown / insufficient_data` and pharmaceutical / biotech pipeline risk can invalidate the ordinary Stable Growth premise. The accepted Stable Growth behavior intentionally keeps many rows `missing` or `not_assessable`; acceptance recorded `missing / not_assessable = 19/33 = 57.58%`. The `stable_growth` label is not operating-steadiness evidence; industry rigid demand, infrastructure, policy protection, and SOE / central-SOE attributes are not demand-durability evidence; revenue growth is not stable growth; single-period `revenue_yoy` plus same-direction operating cash flow is not multi-period stable-growth quality; contract liabilities are not backlog; receivable growth is not high-quality revenue; single-period OCF improvement is not long-term cash-flow stability; dividend / payout is not sustainable shareholder return without free cash flow, debt, capex, and earnings-quality support; single-period ROE is not long-term competitiveness; capex is not capacity release, utilization, future revenue, or growth conversion; valuation metrics are evidence-sufficiency context only and must not become valuation-high/low, target price, upside, or trading judgment. Latest recorded validation after Stable Growth acceptance: `pytest` `484 passed`; regression suite `passed=47 failed=0 total=47`.

Next P1.1 step: keep the accepted Stable Growth baseline frozen at `stable_growth + 600406` unless a new design / implementation / acceptance cycle expands it. Future work can evaluate `right_trend_growth` or P1.2, but should not widen the accepted P1.1 slices implicitly.

P1.1 enforces `company_transmission_path` in schema and builder logic. If no concrete evidence-pack field value or data point can verify the company transmission path, the field must be exactly `传导路径无法从当前证据包验证` and the driver `confidence_cap` must be `not_assessable`. P1.1 also counts source independence by source bucket rather than file count, article count, or repeated API rows.

## 3. Evidence Pack

The evidence pack compresses pipeline output and raw public-data blocks into a model-friendly JSON object. It intentionally avoids passing full raw JSON to the model.

The v1 evidence pack includes:

- stock identity and deterministic fundamental status;
- confidence basis;
- basic information;
- financial metrics;
- valuation metrics;
- business composition;
- commodity price context when present;
- risk flags;
- enhanced must-track indicators;
- invalidation conditions;
- missing-field explanations;
- data limitations;
- source trace summary;
- forbidden-term safety summary.

`source_trace_summary` records block-level counts, functions, fields, and latest periods. It does not include full source trace rows.

### 3.1 Quality Patch v1: Unit Normalization

Ratio-like fields are represented with both raw and display values:

```json
{
  "name": "gross_margin",
  "raw_value": 27.796688,
  "display_value": "27.80%",
  "unit": "%",
  "unit_confidence": "medium"
}
```

For values between 0 and 1, the display value is converted to percentage form. For values that already look like percentage-point values, the display value preserves that interpretation. YoY fields such as `revenue_yoy` and `net_profit_yoy` also include `unit_assumption`; because public data sources can be inconsistent, their `unit_confidence` is conservative unless the source unit is explicitly confirmed.

### 3.2 Quality Patch v1: Confidence Breakdown

`confidence_basis` includes a five-part breakdown:

- `data_coverage`
- `financial_quality`
- `valuation_interpretability`
- `growth_validation`
- `risk_identifiability`

The AI report must explain these dimensions instead of only repeating the overall confidence level.

### 3.3 Quality Patch v1: Evidence Classification

The evidence pack classifies evidence into:

- `supporting_evidence`
- `limiting_evidence`
- `unknown_or_missing_evidence`

Each item records the evidence name, value, why it matters, affected dimension, source, and confidence effect. This is meant to make the AI report more audit-friendly and less template-like.

### 3.4 Neutral Naming Compatibility v1

The evidence pack and prompt use neutral handoff names:

- `analyst_summary` is the recommended summary field.
- `downstream_review_hint` is the recommended invalidation-condition review hint.
- `trader_summary` is deprecated but retained in the source schema for backward compatibility.
- `action_hint_for_trader` is deprecated but retained in the source schema for backward compatibility.

When reading historical JSON that only has legacy fields, the builder falls back from `trader_summary` to `analyst_summary` and from `action_hint_for_trader` to `downstream_review_hint`. Prompt construction must not primarily expose the deprecated field names. This remains a fundamental-analysis layer only: no `trader_skill`, no `technical_skill`, no trading-account connection, and no trading advice.

## 4. Enhanced Must-Track Indicators

The v1 layer adds `enhanced_must_track_indicators` because the dashboard-era indicators are not enough for AI analysis.

Each enhanced indicator contains:

- `indicator_name`
- `why_it_matters`
- `current_value`
- `current_status`
- `source`
- `source_date`
- `related_risk`
- `affects_dimension`
- `follow_up_question`
- `priority`

Strategy-specific indicator templates are used for resource stocks, advanced manufacturing growth, semiconductor cycle, right-trend growth stocks, and satellite communication infrastructure. Missing data is explicitly marked with `current_status = "missing"` rather than filled with invented values.

For `satellite_communication_infrastructure`, v1 must-track indicators include satellite resources, transponder / bandwidth capacity, utilization / lease rate, unit bandwidth price, satellite remaining life, contract duration, customer concentration, contract liabilities, accounts receivable, capex, depreciation / amortization, operating cash flow, gross margin, commercial-aerospace new-business revenue, major satellite launch / failure / insurance events, EV/EBITDA, EBITDA margin, free cash flow, and debt / EBITDA. EV/EBITDA, EBITDA margin, and debt / EBITDA are data limitations only in v1 and must not enter scoring.

AI-facing prompts require these indicators to be rendered as a Markdown table with current status, value, priority, reason, and follow-up question.

## 5. Prompt-Only Workflow

Run:

```bash
python -m src.fundamental_skill.ai_analyst.runner --code 002050 --mode prompt_only
```

The runner reads existing output files, builds the evidence pack, generates the prompt, and writes both files under `output/`.

If `fundamental_<code>.json` or `raw_<code>.json` is missing, the runner asks the user to run `src.fundamental_skill.real_stock_runner` first.

## 5.1 Research Intelligence P0 Workflow

Run:

```bash
python -m src.fundamental_skill.ai_analyst.research_intelligence_runner --code 002837
```

The runner reads `output/evidence_pack_<code>.json` and writes:

- `output/research_intelligence_<code>.json`
- `output/research_questions_<code>.json`
- `output/research_questions_<code>.md`

This workflow does not call OpenAI or any other model API, does not use network access, and does not connect new data sources. It produces an independent analyst-layer artifact focused on source hierarchy, evidence classification, strategy-aware business-financial cross-validation, rule-triggered contradiction detection, P0/P1/P2 research questions with evidence triggers, and IR / manual review questions.

P0.1 accepted behavior adds template sharpening and fallback cleanup to this same workflow. P0 questions still require `evidence_trigger`; P1/P2 questions should avoid generic fallback wording when the strategy context provides a sharper question. The generated `research_intelligence` and `research_questions` files remain runtime artifacts, not committed source.

## 5.2 Research Intelligence P1.1 Driver Matrix Workflow

Run:

```bash
python -m src.fundamental_skill.ai_analyst.research_intelligence_p1_runner --code 000099
python -m src.fundamental_skill.ai_analyst.research_intelligence_p1_runner --code 000426
python -m src.fundamental_skill.ai_analyst.research_intelligence_p1_runner --code 002371
python -m src.fundamental_skill.ai_analyst.research_intelligence_p1_runner --code 002050
python -m src.fundamental_skill.ai_analyst.research_intelligence_p1_runner --code 600406
```

The runner reads `output/evidence_pack_<code>.json`, may read `output/research_intelligence_<code>.json`, and writes:

- `output/research_intelligence_p1_<code>.json`
- `output/research_questions_p1_<code>.json`
- `output/research_questions_p1_<code>.md`

This workflow is an independent driver-factor matrix artifact. Current P1.1 support is limited to `ai_datacenter_infrastructure`, `life_science_cxo_services`, `satellite_communication_infrastructure`, `low_altitude_economy_infrastructure`, `resource_swing + 000426`, `semiconductor_cycle + 002371`, `advanced_manufacturing_growth + 002050`, and `stable_growth + 600406`. It keeps policy, news, theme heat, customer capex, capex, contract liabilities, PUE / MW / cabinet metrics, utilization, liquid-cooling revenue, CXO order / backlog proxies, satellite capacity resources, satellite utilization, contract duration, pricing, customer concentration, remaining life, replacement capex, low-altitude policy pilots, airspace / route approvals, flight hours, flight sorties, platform dispatch volume, project acceptance, customer type, government / SOE collection-cycle, commodity price transmission, production / sales volume, reserves, grade, hedging, resource capex, semiconductor cycle context, localization, customer qualification / adoption, equipment sub-chain boundaries, export-control context, R&D ratio, inventory movement, semiconductor capex bridge, advanced-manufacturing robotics realization, strategic layout / news exclusion, design-win / qualification / nomination, receivable quality, inventory-demand bridge, Stable Growth demand durability, revenue quality, cash conversion, collection quality, dividend / payout sustainability, ROE / ROIC stability, capex discipline, and valuation evidence-sufficiency evidence-gated. Missing fields remain `missing` or `not_assessable`; they are not fabricated into facts.

`output/research_intelligence_p1_*` and `output/research_questions_p1_*` are generated runtime artifacts and should not be committed.

## 6. Why v1 Does Not Call an API

v1 is prompt-only by design and does not automatically call an API. This keeps the deterministic pipeline stable and avoids making tests depend on network access, API keys, model availability, or provider-specific behavior.

The `--mode api` flag is reserved but intentionally not implemented in v1. It prints:

```text
API mode not implemented in v1; use prompt_only
```

## 6.1 Fundamental HTML Report Generator v2.1

Fundamental HTML Report Generator v2.1 is an upper display capability inside the AI analyst layer. It creates pure-fundamental Chinese HTML research reports and remains separate from the deterministic pipeline.

The formal HTML report chain is:

```text
evidence_pack
  -> html report prompt
  -> model-generated FundamentalHtmlReport JSON
  -> render_existing
  -> self-contained HTML
```

The prompt-only command is:

```bash
python -m src.fundamental_skill.ai_analyst.html_report_runner --code 002050 --mode prompt_only
```

This command reads existing `output/fundamental_<code>.json` and `output/raw_<code>.json`, builds the evidence pack, and writes `output/reports/fundamental_report_prompt_<code>.md`. It does not call an API and does not write a formal report JSON or HTML.

After the user has produced a valid formal `output/reports/fundamental_report_<code>.json` from the prompt, render it with:

```bash
python -m src.fundamental_skill.ai_analyst.html_report_runner --code 002050 --mode render_existing
```

`render_existing` validates the structured `FundamentalHtmlReport` JSON and writes a self-contained HTML file under `output/reports/`. The renderer is a display layer only; it must not fetch data, call models, mutate evidence, modify scoring, or infer missing facts.

The v2.1 structured `FundamentalHtmlReport` includes:

- `hero_tags`
- `research_anchor`
- `quality_score_breakdown`
- `value_chain_map`
- `elasticity_formula`
- `tracking_plan_groups`
- `financial_ratio_caveats`

These fields improve the research-report reading experience: first-screen tags, research thesis, quality-score explanation, value-chain mapping, fundamental elasticity framing, grouped tracking plan, and financial-ratio caveats. They must remain basic-fundamental explanations, not trading signals.

Skeleton mode is isolated from the formal path. Skeleton files are rendering placeholders only, live under the skeleton-specific report directory, and must not be treated as formal research reports.

## 6.2 HTML Report Visual Audit Workflow

HTML Report Visual Audit Tool v1 audits an existing local HTML report through Playwright / Chromium screenshots. It is not a renderer and does not repair report content.

Run:

```bash
python scripts/visual_audit_html_report.py \
  --html output/reports/fundamental_report_002050.html \
  --code 002050 \
  --output-dir output/visual_audit/002050
```

The workflow writes desktop first-screen, mobile first-screen, full-page screenshots, and `visual_audit_manifest.json` under `output/visual_audit/<code>/`. The current `002050` baseline has been visually audited with no horizontal overflow on desktop or mobile.

`output/reports/` and `output/visual_audit/` are generated artifacts and should not be committed.

## 7. Safety Boundary

The AI analyst layer is limited to fundamental analysis. It must not output trading advice, account actions, target prices, position sizing, technical indicators, or `technical_skill` / `trader_skill` behavior.

The prompt includes a prohibition list for policy context. Final AI reports should not contain those restricted terms as substantive recommendations. The safety module records detections and separates allowed policy context from blocked report-body usage.

The layer does not delete original evidence. It records safety findings separately.

Research Intelligence P0 inherits the same safety boundary. It must not convert contradiction rules, missing evidence, or IR questions into trading actions. It must also preserve proxy boundaries: contract liabilities are not backlog, capex is not confirmed capacity release, and R&D ratio is not proof of a technology barrier.

Additional HTML report safety boundaries:

- It must not output buy/sell/add/reduce/clear-position language, target prices, position sizing, stop-loss, take-profit, or account actions.
- It must not introduce technical analysis, K-line, moving average, volume, timing, or price-execution modules.
- It must not treat proxy evidence as fact; contract liabilities are not backlog, capex is not capacity release, and R&D intensity is not proof of a technology barrier.
- It must not let skeleton output masquerade as a formal report.
- Formal report and skeleton paths must remain isolated.
- It must not mutate the deterministic pipeline, connector, classifier, scoring, readiness, schema, dashboard, tests, or regression expected files.

## 8. Dashboard v3 Reference

Dashboard v3 consumes the files generated by this layer as a local Streamlit fundamental AI analysis report reader / auditor:

- `output/ai_report_<code>.json`
- `output/ai_report_<code>.md`
- `output/evidence_pack_<code>.json`
- `output/fundamental_<code>.json`
- `output/raw_<code>.json`
- `output/ai_prompt_<code>.md`

Dashboard v3 is a Chinese-first fundamental analysis dashboard. Its main view should help the user quickly understand the current conclusion, evidence, risks, evidence gaps, must-track indicators, confidence basis, and data quality. It remains separate from the deterministic pipeline and should not mutate schema, classifier, connector, scoring, readiness, regression expectations, or source data.

Dashboard v3 is not a trading terminal. It must not connect to trading accounts, output trading advice, show target prices or position sizing, add technical indicators, introduce technical charts, implement `technical_skill`, or implement `trader_skill`.

## 9. Dashboard v3 Viewer / Auditor

Dashboard v3 is implemented as a local Streamlit AI fundamental report reader. It reads existing `ai_report`, `evidence_pack`, `fundamental`, `raw`, and `ai_prompt` files from `output/`.

It does not call model APIs and does not generate new AI reports. If `ai_report_<code>.json` is missing, it shows the prompt-only command and a prompt preview when `ai_prompt_<code>.md` exists.

The default main view is a Chinese fundamental-analysis reader:

- top conclusion area;
- one-line conclusion;
- `strategy_type` / `sub_type` Chinese explanations;
- evidence map for supporting evidence, limiting factors, and missing evidence;
- risk warnings and evidence gaps;
- must-track indicator table;
- confidence breakdown;
- data quality and missing-data summary;
- report stale / mismatch detection;
- schema / safety / garbled guard status.

Report stale / mismatch detection compares the AI report against the current fundamental result and evidence pack, including stock code, framework, sub-type, status / view consistency, generation time, file modification time, and validation status. If the AI report is stale, inconsistent, schema-invalid, safety-invalid, or garbled, Dashboard v3 must not present it as the trusted main report; it should show deterministic conclusions and audit material while prompting regeneration.

Evidence Pack, Source Trace, Raw JSON, fundamental JSON, fetch status, and Prompt preview are kept as collapsed audit material by default. Deprecated compatibility fields `trader_summary` and `action_hint_for_trader` must not appear in the main view; they may appear only inside raw JSON or legacy compatibility audit material.

## 10. Evidence Pack v2.2a Field Note

After `RealDataConnector v2.2a`, the evidence pack can surface these additional `financial_metrics` fields when present in raw JSON:

- `inventory`
- `accounts_receivable`
- `contract_liabilities`

The fields are sourced from `stock_financial_report_sina(indicator="资产负债表")`, with period binding from `报告日`. `inventory` and `accounts_receivable` can clear working-capital missing indicators when their values are present. `contract_liabilities` can only be shown as an order-visibility proxy and must keep the scope note that it is not real orders or backlog.

The AI analyst layer must continue marking capex ratio, customer concentration, new-business orders, domestic-substitution revenue, production/unit cost, cobalt price, and molybdenum price as missing or outside scope until separate source-expansion work is completed.

## 11. Evidence Pack v2.3a Field Note

After `RealDataConnector v2.3a`, the evidence pack can surface three additional `financial_metrics` fields when present in raw JSON:

- `r_and_d_expense`
- `r_and_d_expense_ratio`
- `capex`

The fields are sourced from `stock_financial_report_sina`. Amount fields keep `unit="raw_statement_unit"` and `unit_confidence=low`; `r_and_d_expense_ratio` keeps `unit="%"` and `unit_confidence=high`. All three are cumulative as reported.

The AI analyst layer must not over-interpret these fields:

- R&D expense ratio can improve the current status of R&D-intensity indicators, but it represents R&D intensity only and does not confirm a technology barrier.
- Capex can improve capital-expenditure observation items, but it represents long-term-asset purchase/construction cash outflow only and does not confirm capacity release.

The layer still does not surface or infer `capex_ratio`, `depreciation_amortization`, customer concentration, new-business orders, domestic-substitution revenue, production/unit cost, technical indicators, `technical_skill`, or `trader_skill`.
