# Project Context Handoff

Date: 2026-05-20

Purpose: this document is the first-stop handoff for any new Codex / AI conversation. It summarizes the current project context so future work does not depend on old chat history.

## 1. One-Sentence Positioning

This project is an A-share fundamental AI analysis Skill: it only performs fundamental analysis, does not provide trading advice, does not use technical analysis, and does not connect to trading accounts.

## 2. Current Project Goal

The current target workflow is:

```text
stock code
  -> real public data
  -> deterministic fundamental pipeline
  -> evidence pack
  -> optional Research Intelligence P0 research-question artifacts
  -> AI prompt / report
  -> optional Fundamental HTML Report Generator v2.1
  -> optional HTML Report Visual Audit Tool v1
  -> Dashboard v3 report reader / audit view
```

The system should turn an A-share stock code into auditable public-data blocks, run a deterministic fundamental pipeline, assemble evidence for AI consumption, optionally generate Research Intelligence P0 research-question artifacts, generate or preview an AI analyst prompt/report, optionally render a pure-fundamental Chinese HTML report, optionally audit the HTML visually, and expose the result in a local Dashboard v3 reader for Chinese fundamental-report inspection and audit.

## 3. Current Architecture

Core modules:

- `RealDataConnector`: fetches real public A-share data into raw JSON blocks.
- `ExternalCommodityPriceConnector`: adds configured commodity-price context for resource stocks.
- `FundamentalDataAdapter`: normalizes raw JSON into pipeline input.
- `StockClassifier`: classifies the stock into a fundamental `strategy_type`.
- `FrameworkSelector`: selects the framework that matches the classified strategy type.
- `DataReadinessPlanner`: checks whether current data can support the selected framework.
- `AnalysisContextBuilder`: builds deterministic analysis context, required risks, missing data, and prohibited claims.
- `FundamentalScoringEngine`: scores fundamental dimensions under strategy-specific weights and confidence constraints.
- `FundamentalResultAssembler`: assembles the final structured fundamental result.
- `AI Analyst Layer`: builds evidence packs and model-ready prompts; current primary mode is `prompt_only`.
- `Research Intelligence P0`: independent AI analyst artifact builder that reads only `evidence_pack`, builds a research intelligence pack and research question set, and acts as a research-question discovery layer rather than a report renderer or trading system.
- `Fundamental HTML Report Generator v2.1`: upper AI analyst display capability that creates a model prompt for structured `FundamentalHtmlReport` JSON and renders an existing formal JSON into self-contained HTML.
- `HTML Report Visual Audit Tool v1`: local Playwright / Chromium screenshot and manifest tool for existing HTML reports.
- `Dashboard v3`: local Streamlit fundamental AI report reader / auditor. The main view is Chinese-first and highlights the top conclusion, one-line conclusion, strategy / sub-type explanations, evidence map, risks, evidence gaps, must-track indicators, confidence breakdown, data quality, report stale / mismatch status, and schema / safety / garbled guard state. Evidence Pack, Source Trace, Raw JSON, Prompt, and legacy fields are collapsed as audit material.

Flow:

```text
stock_code
  -> RealDataConnector
  -> raw JSON blocks
  -> FundamentalDataAdapter
  -> NormalizedFundamentalInput
  -> StockClassifier
  -> FrameworkSelector
  -> DataReadinessPlanner
  -> AnalysisContextBuilder
  -> FundamentalScoringEngine
  -> FundamentalResultAssembler
  -> FundamentalAnalysisResult
  -> AI Analyst Layer
  -> evidence_pack
  -> optional research_intelligence + research_questions
  -> ai_prompt / ai_report
  -> html report prompt -> model-generated FundamentalHtmlReport JSON -> render_existing -> self-contained HTML
  -> visual audit screenshots + manifest
  -> Dashboard v3 report reader / audit display
```

## 4. Current Core Module Versions

- `RealDataConnector v2.3a`
- `ExternalCommodityPriceConnector v1.1`
- `AI Analyst Layer prompt_only`
- `Research Intelligence P0`
- `Fundamental HTML Report Generator v2.1`
- `HTML Report Visual Audit Tool v1`
- `Dashboard v3`
- `Industry Framework Workflow`

## 5. Current strategy_type List

- `resource_swing`
- `resource_core`
- `right_trend_growth`
- `semiconductor_cycle`
- `stable_growth`
- `advanced_manufacturing_growth`
- `satellite_communication_infrastructure`
- `low_altitude_economy_infrastructure`
- `life_science_cxo_services`
- `ai_datacenter_infrastructure`
- `theme_only`
- `unknown`

## 6. Current Covered Data Fields

Currently covered or surfaced fields include:

- `basic_info`
- `financial_indicator`
- `valuation`
- `business_composition`
- `commodity_prices`
- `inventory`
- `accounts_receivable`
- `contract_liabilities`
- `r_and_d_expense`
- `r_and_d_expense_ratio`
- `capex`

Missing data must be recorded as missing, warnings, source-trace gaps, or data limitations. The system must not invent values.

## 7. Current Industry Framework Status

- `resource_swing`: for resource companies whose profit is highly sensitive to commodity prices and cycles. Representative samples include `000426`, `603993`. Main boundary: commodity-price exposure and business composition must be evidenced; price context does not become a trading signal.
- `resource_core`: for large resource leaders with multi-resource assets, cash flow, reserve / production scale, and distribution characteristics. Representative sample includes `601899`. Main boundary: do not analyze a cyclical small resource stock as a core resource allocation company.
- `right_trend_growth`: for high-prosperity growth chains such as AI compute, optical modules, PCB, servers, liquid cooling, and data centers. Representative samples include `300308`, `300476`. Main boundary: theme heat or supply-chain narrative is not order or revenue realization.
- `semiconductor_cycle`: for semiconductor equipment, chips, wafers, storage, domestic substitution, and cycle-sensitive names. Representative samples include `002371`, `688008`. Main boundary: R&D and domestic substitution narratives need revenue/order validation; inventory cycle risk remains central.
- `stable_growth`: for steadier growth companies such as grid and electrical equipment where orders, cash flow, ROE, and receivables matter. Representative samples include `002028`, `600406`. Main boundary: do not apply high-beta theme-stock logic or ignore cash conversion.
- `advanced_manufacturing_growth`: for auto thermal management, robotics actuators, industrial automation, precision manufacturing, and new-energy-vehicle supply-chain growth. Representative samples include `002050`, `601689`. Main boundary: robot/new-business exposure must be verified by revenue, orders, customers, and segment data.
- `satellite_communication_infrastructure`: completed. Applies to asset-intensive, license/resource-driven satellite communication infrastructure operators that monetize in-orbit satellites, orbital/frequency resources, transponders, bandwidth, or satellite communication services. Representative sample: `601698`. Negative samples include `600118`, `002465`, `688066`, `002895`, and a news-only satellite sample. Main boundary: excludes satellite manufacturing, terminals, remote sensing, data software, military electronics, rockets, drones, and generic communication equipment.
- `low_altitude_economy_infrastructure`: completed. Applies only to low-altitude infrastructure / operation service business models, not broad concept exposure. Representative positive samples include `000099` and `688631`. Negative samples include `688070`, `002085`, `001696`, `600967`, and `002895`. Main boundary: drone OEMs, eVTOL OEMs, aircraft engines, components, auto parts, airports, aviation leasing, remote sensing, defense, policy-only, announcement-only, or theme-only companies must not be routed here.
- `life_science_cxo_services`: completed. Applies to CRO / CDMO / CXO / CMC / clinical research or pharmaceutical R&D-production outsourcing service business models. Representative positive samples include `603259`, `300759`, `002821`, `300363`, and `300347`. Negative samples include `000739`, `300012`, `300760`, `600196`, `600276`, and `600521`. Main boundary: excludes self-owned drug-pipeline companies, ordinary API / formulation manufacturing, medical devices, distribution, TCM, consumer healthcare, software-only AI drug discovery, general testing labs, and news-only CXO wording.
- `ai_datacenter_infrastructure`: completed v1. Applies to AI datacenter infrastructure business models with verifiable datacenter operation, power / UPS infrastructure, or cooling / liquid-cooling infrastructure evidence. Representative and boundary samples include `300442` Runze Technology as `datacenter_operator`, `002837` Envicool as `cooling_liquid_cooling_infrastructure`, `002335` / `002518` as `power_ups_infrastructure` boundary / mixed samples, and `301018` as a cooling / HVAC boundary sample. Negative samples include `300308` and `300476`, which remain in `right_trend_growth` because optical modules and AI PCB are supply-chain / manufacturing-growth exposures rather than AI datacenter infrastructure operators. Main boundary: theme words, AI server supply-chain exposure, optical modules, PCB, storage / photovoltaic mix, ordinary HVAC, or generic power equipment do not classify unless datacenter-specific revenue, orders, customers, assets, or operation evidence is confirmable.
- `theme_only`: for companies with thematic exposure but weak or unverified fundamental support. Representative sample: `999999_theme_a`. Main boundary: do not treat theme popularity, news heat, or policy language as realized business.
- `unknown`: for insufficient or unstable classification evidence. Representative sample: `999998_insufficient_b`. Main boundary: do not force a framework when industry, main business, financials, or business composition are not enough.

The `low_altitude_economy_infrastructure` framework includes these `sub_type` values:

- `aviation_operations_service`
- `airspace_platform_system`

The `life_science_cxo_services` framework includes these `sub_type` values:

- `integrated_cxo_platform`
- `cdmo_manufacturing_services`
- `clinical_cro_services`

The `ai_datacenter_infrastructure` framework includes these `sub_type` values:

- `datacenter_operator`
- `power_ups_infrastructure`
- `cooling_liquid_cooling_infrastructure`

## 8. Current Testing System

The project uses:

- `pytest`
- regression suite
- schema validation
- safety validation
- garbled text guard
- negative sample tests
- industry framework regression tests

Regression fixtures live under `tests/regression/fixtures`, with expectations under `tests/regression/expected`. The standalone regression runner is `scripts/run_regression_suite.py`.

## 9. Common Commands

```bash
python -m pytest tests --basetemp=.pytest_tmp -p no:cacheprovider
python scripts/run_regression_suite.py
python -m src.fundamental_skill.real_stock_runner --code 601698 --output output/fundamental_601698.json --force-refresh
python -m src.fundamental_skill.ai_analyst.runner --code 601698 --mode prompt_only
python -m src.fundamental_skill.ai_analyst.research_intelligence_runner --code 002837
python -m src.fundamental_skill.ai_analyst.html_report_runner --code 002050 --mode prompt_only
python -m src.fundamental_skill.ai_analyst.html_report_runner --code 002050 --mode render_existing
python scripts/visual_audit_html_report.py --html output/reports/fundamental_report_002050.html --code 002050 --output-dir output/visual_audit/002050
streamlit run dashboard/fundamental_dashboard.py
```

## 10. Safety Boundaries

The system must not output:

- buy, sell, add position, reduce position, clear position, stop loss, take profit, target price, full position, or all-in style instructions;
- trading execution;
- technical analysis;
- trading-account connection.

Dashboard-specific boundaries:

- Dashboard v3 is not a trading terminal and must not connect to trading accounts.
- Dashboard v3 must not output trading advice, account actions, target prices, position sizing, or buy/sell language.
- Dashboard v3 must not add technical charts, technical indicators, `technical_skill`, or `trader_skill`.
- Dashboard v3 must not modify the deterministic pipeline, schema, classifier, connector, regression expectations, or tests as part of display-only work.

HTML report boundaries:

- Fundamental HTML Report Generator v2.1 produces pure fundamental Chinese HTML research reports, not a trading terminal.
- It must not output trading advice, target prices, account actions, position sizing, technical analysis, K-line content, or price execution language.
- It must not mutate the deterministic pipeline, `RealDataConnector`, classifier, scoring / readiness, schema, dashboard, tests, regression expected files, or output artifacts outside its generated report paths.
- Skeleton reports are rendering placeholders only and must not be presented as formal reports; skeleton and formal report paths are isolated.

Research Intelligence P0 boundaries:

- Research Intelligence P0 reads only `output/evidence_pack_<code>.json`.
- It does not call LLMs, use network access, connect new data sources, or connect trading accounts.
- It does not mutate deterministic results, `status`, `confidence`, `score`, `strategy_type`, `sub_type`, connector, classifier, scoring, readiness, result assembler, HTML renderer, or report outputs.
- It writes only independent artifacts: `output/research_intelligence_<code>.json`, `output/research_questions_<code>.json`, and `output/research_questions_<code>.md`.
- It is evidence-gated and rule-triggered; missing data should produce not-assessable diagnostics or IR / manual review questions, not invented conclusions.

Interpretation boundaries:

- `confidence` is confidence in the evidence behind the current `fundamental_view`; it is not positive strength, upside probability, or investment attractiveness.
- Proxy evidence must be explicitly labeled and must not be treated as fact.
- Contract liabilities are not backlog.
- Capex is not confirmed capacity release.
- R&D ratio is not confirmation of a technology barrier.
- Theme heat is not fundamental realization.

AI datacenter score-semantics note:

- For `ai_datacenter_infrastructure` boundary samples, the boundary cap is a `readiness_score` cap, not a direct final `fundamental_score` cap.
- Missing structured real order, customer, delivery, or sub-type revenue validation can cap `readiness_score` to `<= 39`, force `readiness_level=insufficient`, and keep final confidence at `low`.
- The final `fundamental_score` still comes from weighted scoring plus result assembly. If final `status=insufficient_data`, the general final-score cap is `<= 50`.
- Final scores around 41-47 are therefore acceptable for boundary samples such as `002335`, `002518`, and `301018` when `status=insufficient_data` and `confidence=low`.

### Neutral Naming Compatibility v1

The `fundamental.v1` public schema keeps backward compatibility while adding neutral aliases:

- `analyst_summary` is the recommended summary field for AI and Dashboard display.
- `downstream_review_hint` is the recommended invalidation-condition review hint.
- `trader_summary` is deprecated but retained for backward compatibility with historical JSON.
- `action_hint_for_trader` is deprecated but retained for backward compatibility with historical JSON.

New deterministic outputs fill both new and old fields with the same neutral text. AI evidence packs, prompts, and Dashboard helpers prefer the neutral fields and fall back to legacy fields only for old files. Dashboard v3 does not show `trader_summary` / `action_hint_for_trader` in the main view; deprecated fields may appear only inside raw JSON or compatibility audit material. This project still does not implement `trader_skill`, does not implement `technical_skill`, does not connect to trading accounts, and does not output trading advice.

## 11. Industry Framework Extension Workflow

Follow `docs/INDUSTRY_FRAMEWORK_DEVELOPMENT_WORKFLOW.md`:

```text
Out-of-Sample Audit
  -> Design Audit
  -> Optional External Review
  -> Design Revision
  -> Implementation
  -> Acceptance
  -> Commit
```

Do not add a new industry framework only because one stock is popular or difficult to classify. Expand by durable business model, define boundaries first, then implement narrowly after design acceptance.

## 12. Current Known Limitations

- `latest_news` / AkShare news endpoints may fail.
- Many industry-specific operating data fields are still missing or not stably obtainable.
- AI report generation is currently mainly `prompt_only`; API mode is not the primary implemented workflow.
- Research Intelligence P0 has been accepted as a baseline research-question discovery artifact. The `002837` smoke passed and generated a research intelligence pack plus JSON / Markdown research question set from the existing evidence pack.
- HTML report generation v2.1 does not automatically call an API; it creates prompts and renders existing formal `FundamentalHtmlReport` JSON.
- `002050` 三花智控 is an internal successful HTML report sample candidate after v2.1 and visual audit acceptance.
- `output/`, `output/reports/`, `output/visual_audit/`, `data/`, and `cache/` are generated/runtime artifacts and should not be committed.
- Some industries remain uncovered, including banks, medical devices, and intelligent driving. CXO is covered by `life_science_cxo_services`, and AI datacenter infrastructure is covered by `ai_datacenter_infrastructure` v1, but both still have conservative public-data limits.
- AI Datacenter v1 remains limited by public data availability for orders / backlog, customer structure, cabinet count, MW scale, PUE, rack utilization, liquid-cooling revenue, customer validation, datacenter revenue split, and customer capex-cycle evidence.

## 13. Suggested Next Steps

- Keep `README.md` and `docs/PROJECT_CONTEXT_HANDOFF.md` synchronized after major project changes.
- Research Intelligence P0.1 optimization candidates: sharpen `ai_datacenter_infrastructure` question templates; distinguish liquid-cooling customer validation stage such as POC / testing / certification / batch orders; clarify datacenter room cooling versus ordinary thermal-control boundaries; sharpen the template for revenue growth not converting into profit and operating cash flow.
- HTML Report Generator v2.1 baseline does not need more repair unless the user reports a specific visual or content issue.
- Based on user feedback, continue refining the HTML research-report experience, or generate formal HTML reports for other stocks using the existing v2.1 chain.
- Keep AI Datacenter v1 conservative unless public data sources can reliably validate orders / backlog, customer structure, cabinet / MW / PUE / rack utilization, liquid-cooling revenue, datacenter revenue split, and customer capex-cycle evidence.
- Do not rush into `technical_skill` or `trader_skill`.
- Do not connect trading accounts, add target prices, introduce technical analysis, or turn reports into trading recommendations.
- Do not blindly add more fields without source stability, interpretation rules, and regression coverage.
- Every new industry framework must follow the documented workflow.

## 14. New Codex Conversation Recovery Prompt

Copy this into a new Codex / AI conversation:

```text
请先阅读 docs/PROJECT_CONTEXT_HANDOFF.md 并恢复当前项目上下文，不要改代码、不要改 config、不要改 tests、不要改 pipeline、不要改 dashboard。当前项目是 A 股基本面 AI 分析 Skill，只做基本面，不输出交易建议、不做技术面、不接交易账户。请先总结你理解的项目定位、架构、安全边界、当前 strategy_type、已完成行业框架、测试体系和下一步建议，然后等待我给出本阶段任务。
```
