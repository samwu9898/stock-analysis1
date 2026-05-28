# Project Context Handoff

Date: 2026-05-28

Purpose: this document is the first-stop handoff for any new Codex / AI conversation. It summarizes the current project context so future work does not depend on old chat history.

Current superseding update: Research Report V1 cross-industry Markdown profile
acceptance is complete for `600406`, `002371`, and `002050`; the HTML renderer
implementation is accepted; the three-sample HTML presentation baseline is
frozen; single-stock offline orchestration implementation is accepted; the
Chinese summary patch is accepted; `600406`, `002371`, and `002050` have all
passed one-sentence local report invocation runtime acceptance; CLI
implementation is accepted; `600406`, `002371`, and `002050` have all passed
CLI runtime acceptance; the single-stock offline CLI baseline is frozen; and
the CLI usage guide is recorded. The HTML design is recorded in
`docs/FUNDAMENTAL_RESEARCH_REPORT_V1_HTML_PRESENTATION_DESIGN.md`, the HTML
acceptance summary is recorded in
`docs/FUNDAMENTAL_RESEARCH_REPORT_V1_HTML_ACCEPTANCE_SUMMARY.md`, user
invocation / report orchestration design is recorded in
`docs/FUNDAMENTAL_SKILL_USER_INVOCATION_ORCHESTRATION_DESIGN.md`, offline
orchestration acceptance is recorded in
`docs/FUNDAMENTAL_SKILL_OFFLINE_ORCHESTRATION_ACCEPTANCE_SUMMARY.md`, the CLI
/ command wrapper design is recorded in
`docs/FUNDAMENTAL_SKILL_USER_INVOCATION_CLI_DESIGN.md`, and the CLI runtime
acceptance summary is recorded in
`docs/FUNDAMENTAL_SKILL_CLI_RUNTIME_ACCEPTANCE_SUMMARY.md`. The CLI usage
guide is recorded in `docs/FUNDAMENTAL_SKILL_CLI_USAGE_GUIDE.md`. The
accepted profiles are `stable_growth_grid_equipment`,
`semiconductor_equipment_cycle`, and
`advanced_manufacturing_thermal_management`. The next recommended stage is
batch / Dashboard design. The next step is not more ad hoc single-target HTML
generation, more single-stock CLI runtime generation, CLI usage documentation,
promote rules, validator, fixture promotion, Tushare primary, live provider
report, official parser / CNInfo, MCP, Tushare token work, or another smoke.

## 1. One-Sentence Positioning

This project is an A-share fundamental AI analysis Skill. The accepted current user-facing baseline is the Research Report V1 single-stock offline CLI, which reads local accepted artifacts and returns HTML / Markdown / JSON paths plus a short Chinese summary. It only performs fundamental research, does not provide trading advice, does not use technical analysis, does not connect to trading accounts, and by default does not use live providers, network access, tokens, or MCP.

## 2. Current Project Goal

The current target workflow is:

```text
natural-language Codex / GPT-5.5 request
  -> structured user request
  -> local report orchestration
  -> stock code
  -> real public data
  -> deterministic fundamental pipeline
  -> evidence pack
  -> optional Research Intelligence P0 research-question artifacts
  -> optional Research Intelligence P1.1 driver-matrix artifacts
  -> AI prompt / report
  -> optional Fundamental HTML Report Generator v2.1
  -> optional HTML Report Visual Audit Tool v1
  -> final HTML path + Markdown path + JSON path + short Chinese summary
  -> Dashboard v3 report reader / audit view
```

For the accepted CLI baseline, the current default path begins at local report orchestration and `offline_local_artifacts`; live provider report, official parser / CNInfo, MCP, Tushare token work, and provider-primary changes remain later separately accepted stages.

The system should let a user ask Codex / GPT-5.5 for a report in natural
language, normalize that request into a structured local-only report request,
turn an A-share stock code into auditable public-data blocks, run a
deterministic fundamental pipeline, assemble evidence for AI consumption,
optionally generate Research Intelligence P0 research-question artifacts,
optionally generate the accepted Research Intelligence P1.1 driver-matrix
artifacts for the currently supported strategy types, generate or preview an AI
analyst prompt/report, render a pure-fundamental Chinese Markdown / HTML
Research Report V1 output, return paths plus a short Chinese summary, and later
expose the result in a local Dashboard v3 reader for Chinese
fundamental-report inspection and audit.

## 3. Current Architecture

Core modules:

- `RealDataConnector`: fetches real public A-share data into raw JSON blocks.
- `Data Provider Abstraction`: Phase 1 skeleton, Phase 2 `AkShareProvider` adapter, Phase 3 `TushareProvider` mocked MVP, Phase 4 dual-source comparison dry-run tooling, Phase 4 local real-token smoke gate documentation, Phase 4 real-token smoke gate safety skeleton, Phase 4 score / confidence explainability implementation, Phase 4 explainability narrative hints patch, narrative-hints artifact review, and Phase 4 closeout / baseline freeze have been accepted. Phase 4 is documented in `docs/DATA_PROVIDER_PHASE4_DUAL_SOURCE_COMPARISON_DESIGN.md`, `docs/DATA_PROVIDER_PHASE4_LOCAL_REAL_TOKEN_SMOKE_GATE.md`, `docs/DATA_PROVIDER_PHASE4_REAL_TOKEN_SMOKE_IMPLEMENTATION_DESIGN.md`, `docs/DATA_PROVIDER_PHASE4_SCORE_CONFIDENCE_EXPLAINABILITY_DESIGN.md`, and `docs/DATA_PROVIDER_PHASE4_CLOSEOUT_RELEASE_NOTE.md`. Fundamental Research Report V1 design, implementation, baseline freeze, presentation profile registry, cross-industry Markdown profile acceptance for `600406`, `002371`, and `002050`, HTML renderer implementation, and three-sample HTML acceptance are complete; the HTML presentation baseline is frozen. User invocation / report orchestration design is recorded in `docs/FUNDAMENTAL_SKILL_USER_INVOCATION_ORCHESTRATION_DESIGN.md`, single-stock offline orchestration acceptance is recorded in `docs/FUNDAMENTAL_SKILL_OFFLINE_ORCHESTRATION_ACCEPTANCE_SUMMARY.md`, CLI / command wrapper design is recorded in `docs/FUNDAMENTAL_SKILL_USER_INVOCATION_CLI_DESIGN.md`, CLI runtime acceptance is recorded in `docs/FUNDAMENTAL_SKILL_CLI_RUNTIME_ACCEPTANCE_SUMMARY.md`, and CLI usage is recorded in `docs/FUNDAMENTAL_SKILL_CLI_USAGE_GUIDE.md`. CLI implementation is accepted, the single-stock offline CLI baseline is frozen, the CLI usage guide is recorded, and the next recommended step is batch / Dashboard design, not more ad hoc single-target HTML generation, not more single-stock CLI runtime generation, not CLI usage documentation, not promote-rule design, not manual field filling, not fixture promotion, not validator implementation, not Tushare primary switch, not live provider report, not official parser / CNInfo, not MCP, not Tushare token work, and not another Phase 4 smoke. Tushare must not become primary, AkShare / Tushare data must not be automatically merged, drift must not be automatically accepted, and the default `real_stock_runner`, deterministic pipeline, `evidence_pack`, P1.1, HTML / Dashboard, classifier, scoring / readiness, default output, `output/reports`, default `diff_report`, and regression expected files remain unchanged. `AkShareProvider` remains a thin wrapper around `RealDataConnector`.
- `ExternalCommodityPriceConnector`: adds configured commodity-price context for resource stocks.
- `FundamentalDataAdapter`: normalizes raw JSON into pipeline input.
- `StockClassifier`: classifies the stock into a fundamental `strategy_type`.
- `FrameworkSelector`: selects the framework that matches the classified strategy type.
- `DataReadinessPlanner`: checks whether current data can support the selected framework.
- `AnalysisContextBuilder`: builds deterministic analysis context, required risks, missing data, and prohibited claims.
- `FundamentalScoringEngine`: scores fundamental dimensions under strategy-specific weights and confidence constraints.
- `FundamentalResultAssembler`: assembles the final structured fundamental result.
- `AI Analyst Layer`: builds evidence packs and model-ready prompts; current primary mode is `prompt_only`.
- `Research Intelligence P0/P0.1`: independent AI analyst artifact builder that reads only `evidence_pack`, builds a research intelligence pack and research question set, and acts as a research-question discovery layer rather than a report renderer or trading system. P0.1 sharpens generic missing-evidence prompts into strategy-type-aware research questions.
- `Research Intelligence P1.1`: independent driver-factor matrix artifact builder for `ai_datacenter_infrastructure`, `life_science_cxo_services`, `satellite_communication_infrastructure`, `low_altitude_economy_infrastructure`, the first Resource slice `resource_swing + 000426`, the first Semiconductor slice `semiconductor_cycle + 002371`, the first Advanced Manufacturing slice `advanced_manufacturing_growth + 002050`, and the first Stable Growth slice `stable_growth + 600406`. It reads `evidence_pack` plus an optional P0 pack, writes `research_intelligence_p1` and `research_questions_p1` artifacts, enforces `company_transmission_path` and source-bucket independence, keeps missing evidence `not_assessable` first, and stays outside the HTML / Dashboard main chain. The Semiconductor multi-sample observation has completed: `002371` is the accepted positive sample, `688012 / 688981 / 603501 / 300604` were validation samples, and `300308 / 300476` were boundary / negative samples. Advanced Manufacturing multi-sample observation is complete, and the `601689` boundary data completion smoke is complete. Advanced Manufacturing first-version support remains limited to `advanced_manufacturing_growth + 002050`; `601689` was classified as `advanced_manufacturing_growth` but correctly stopped at `unsupported_pilot_strategy` / `not_assessable` as a later validation / boundary sample. Stable Growth first-version support remains limited to `stable_growth + 600406`; `002028` is validation / boundary only, and `600276` is excluded.
- `Fundamental HTML Report Generator v2.1`: upper AI analyst display capability that creates a model prompt for structured `FundamentalHtmlReport` JSON and renders an existing formal JSON into self-contained HTML.
- `Fundamental Skill User Invocation / Report Orchestration`: accepted
  single-stock offline natural-language Codex / GPT-5.5 entry layer. It parses
  a user request into a structured local report request, applies safe offline
  flags, locates accepted local artifacts, reuses accepted HTML, extracts a
  Chinese summary from Markdown, returns HTML / Markdown / JSON paths plus
  opportunity / risk / evidence-gap / data-quality summary, and keeps the
  default V1 path offline with no token read, no network, no provider call, no
  MCP, and no trading advice. The one-sentence local report invocation baseline
  is frozen for `600406`, `002371`, and `002050`.
- `HTML Report Visual Audit Tool v1`: local Playwright / Chromium screenshot and manifest tool for existing HTML reports.
- `Dashboard v3`: local Streamlit fundamental AI report reader / auditor. The main view is Chinese-first and highlights the top conclusion, one-line conclusion, strategy / sub-type explanations, evidence map, risks, evidence gaps, must-track indicators, confidence breakdown, data quality, report stale / mismatch status, and schema / safety / garbled guard state. Evidence Pack, Source Trace, Raw JSON, Prompt, and legacy fields are collapsed as audit material.

Flow:

```text
natural-language Codex / GPT-5.5 request
  -> structured report request
  -> local orchestration data-mode gate
  -> stock_code
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
  -> optional research_intelligence_p1 + research_questions_p1
  -> ai_prompt / ai_report
  -> html report prompt -> model-generated FundamentalHtmlReport JSON -> render_existing -> self-contained HTML
  -> visual audit screenshots + manifest
  -> final HTML path + Markdown path + JSON path + short Chinese summary
  -> Dashboard v3 report reader / audit display
```

## 4. Current Core Module Versions

- `RealDataConnector v2.3a`
- `Data Provider Abstraction Phase 4 dry-run + real-token smoke gate + explainability frozen`: `TushareClient` mocked abstraction and `TushareProvider` mocked mapping accepted; `ProviderRouter` optional modes remain `auto`, `akshare`, `tushare`, and `dual_compare`; `compare_providers`, `comparison_artifacts`, `diff_classifier`, `token_leak_scanner`, `real_token_smoke_gate`, `tushare_sdk_transport`, and `score_confidence_explainability.py` are accepted isolated tooling. Phase 4 artifact writes, when explicitly enabled, are isolated under `output/provider_comparison/<timestamp>/<code>/`; `score_confidence_explainability.json` is written only under `output/provider_comparison/<timestamp>/<code>/` when explicit `--explainability` is enabled. Default dry-run does not generate `output/provider_comparison`, does not write production output, does not run HTML, and does not run Research Intelligence P1.1. `--include-p1` is off by default. The real-token smoke path requires explicit `--real-token-smoke --provider-transport sdk`, fails closed without a token before SDK calls, rejects `--token`, and keeps `http` / `mcp-local` reserved fail-closed; `--explainability` cannot be combined with `--real-token-smoke` in V1. Research Report V1 is implemented, baseline frozen, profile registry accepted, cross-industry Markdown validation accepted, HTML renderer implementation accepted, the three-sample HTML baseline frozen, user invocation / report orchestration design recorded, single-stock offline orchestration accepted for `600406`, `002371`, and `002050`, CLI / command wrapper design recorded, CLI implementation accepted, single-stock offline CLI baseline frozen, and CLI usage guide recorded; the next recommended step is batch / Dashboard design, not another Phase 4 smoke, not more single-target HTML generation, not more single-stock CLI runtime generation, not CLI usage documentation, not promote-rule design, not validator implementation, not fixture promotion, and not Tushare primary switch.
- `Fundamental Ground Truth Benchmark Design`: documentation-only design for a reviewed factual benchmark covering canonical `basic_info`, `financial_metrics`, `valuation_metrics`, and `business_composition` fields. It defines the V1 sample pool, source priority, tolerance rules, future fixture shape, future validator boundary, and its relationship with regression, Tushare block-level primary design, and P1.1 deep validation. It does not make the user manually find most values; reviewed ground truth should be populated only after automatic candidate generation and auto-accept / human-review gates.
- `Fundamental Auto Fact Candidate Generator Design`: documentation-only design for an automated candidate layer that extracts provider fact candidates from Tushare / AkShare / existing provider artifacts / future CNInfo or announcement parsers, records source trace, period, unit, confidence, conflict status, and review status, and routes only accepted or human-reviewed facts toward the ground-truth fixture. It does not add code, alter the fixture, implement a validator, call providers, read tokens, connect MCP, modify pipeline behavior, switch primary providers, or change regression expected files.
- `Fundamental Candidate Report Review Protocol Design`: documentation-only design for converting `manual_review_priority_queue` into a few high-value review actions. The first `600406` plan prioritizes `valuation_metrics.as_of_date`, `business_composition.period`, `business_composition.classification_type`, and `business_composition.revenue_ratio`; the design is accepted and is now followed by the review decisions artifact design. It explicitly does not promote fixtures, run validators, call providers, read tokens, connect MCP, switch primary behavior, or merge AkShare / Tushare.
- `Fundamental Candidate Review Decisions Artifact Design`: documentation-only design for `candidate_review_decisions.json`, the intermediate audit artifact between `fact_candidates.json` / `manual_review_priority_queue` and future promote rules. It defines runtime output path, schema, outcome enum, follow-up enum, summary counts, and the first `600406` Priority A / B decision plan. It is not ground truth, not fixture promotion, not a validator, not a provider merge, and not an investment-advice artifact.
- `Fundamental Research Report V1`: design accepted, implementation accepted, first `600406` runtime artifact accepted, baseline frozen, presentation profile registry accepted, cross-industry Markdown profile validation accepted for `600406`, `002371`, and `002050`, HTML renderer implementation accepted, three-sample HTML baseline frozen, single-stock offline orchestration accepted, CLI implementation accepted, single-stock offline CLI baseline frozen, and CLI usage guide recorded. The accepted modules are `src/fundamental_skill/research_report/research_report_v1.py`, `src/fundamental_skill/research_report/research_report_v1_html.py`, `src/fundamental_skill/research_report/__init__.py`, and `tests/test_research_report_v1.py`; the first accepted ignored runtime artifact is `output/research_reports/20260527T103241/600406/fundamental_research_report_v1.json`. The accepted Markdown artifacts are listed in `docs/FUNDAMENTAL_RESEARCH_REPORT_V1_MARKDOWN_PROFILE_ACCEPTANCE_SUMMARY.md`, the accepted HTML artifacts are listed in `docs/FUNDAMENTAL_RESEARCH_REPORT_V1_HTML_ACCEPTANCE_SUMMARY.md`, the offline orchestration acceptance summary is listed in `docs/FUNDAMENTAL_SKILL_OFFLINE_ORCHESTRATION_ACCEPTANCE_SUMMARY.md`, the CLI runtime acceptance summary is listed in `docs/FUNDAMENTAL_SKILL_CLI_RUNTIME_ACCEPTANCE_SUMMARY.md`, and the CLI usage guide is listed in `docs/FUNDAMENTAL_SKILL_CLI_USAGE_GUIDE.md`. It returns from the data-quality audit chain to professional fundamental research output with executive summary, data quality, macro context, industry context, company fundamentals, opportunities, risks, evidence gaps, rebuttal conditions, follow-up variables, evidence labels, source artifact references, and accepted presentation-layer HTML. It reads existing local artifacts only and does not call providers, read tokens, connect MCP, write fixtures, alter scoring / readiness, alter P1.1, switch Tushare primary, merge AkShare / Tushare, or provide trading advice.
- `Fundamental Skill User Invocation / Report Orchestration`:
  accepted single-stock offline Codex / GPT-5.5 natural-language entry point.
  It defines request parsing, schema normalization, data modes, single-stock
  artifact orchestration, missing-artifact behavior, final response shape,
  CLI command-wrapper boundary, and Dashboard / batch relationship. It keeps the
  current V1 default at `offline_local_artifacts`, `no_live_provider`,
  `allow_network=false`, `allow_token_read=false`, and
  `strict_evidence_boundary=true`; `600406`, `002371`, and `002050` runtime
  invocations are accepted and the one-sentence local report invocation
  baseline is frozen. The CLI / command wrapper design is recorded in
  `docs/FUNDAMENTAL_SKILL_USER_INVOCATION_CLI_DESIGN.md`; CLI implementation
  and `600406` / `002371` / `002050` CLI runtime acceptance are recorded in
  `docs/FUNDAMENTAL_SKILL_CLI_RUNTIME_ACCEPTANCE_SUMMARY.md`; the
  single-stock offline CLI baseline is frozen. CLI usage is recorded in
  `docs/FUNDAMENTAL_SKILL_CLI_USAGE_GUIDE.md`.
- `ExternalCommodityPriceConnector v1.1`
- `AI Analyst Layer prompt_only`
- `Research Intelligence P0/P0.1`
- `Research Intelligence P1.1 AI Datacenter / CXO / Satellite / Low Altitude / Resource / Semiconductor / Advanced Manufacturing / Stable Growth expansions`
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

- `resource_swing`: for resource companies whose profit is highly sensitive to commodity prices and cycles. Representative samples include `000426`, `603993`. P1.1 Resource first implementation supports only `000426`; `603993` remains a later validation / boundary sample. Main boundary: commodity-price exposure and business composition must be evidenced; price context does not become company revenue, company performance, or a trading signal.
- `resource_core`: for large resource leaders with multi-resource assets, cash flow, reserve / production scale, and distribution characteristics. Representative sample includes `601899`. Main boundary: do not analyze a cyclical small resource stock as a core resource allocation company. P1.1 Resource first implementation does not support `resource_core`; it remains design-only until operating cash flow history, sustaining-vs-expansionary capex split, debt / liquidity fields, and dividend history or payout ratio are stably available.
- `right_trend_growth`: for high-prosperity growth chains such as AI compute, optical modules, PCB, servers, liquid cooling, and data centers. Representative samples include `300308`, `300476`. Main boundary: theme heat or supply-chain narrative is not order or revenue realization.
- `semiconductor_cycle`: for semiconductor equipment, chips, wafers, storage, domestic substitution, and cycle-sensitive names. Representative samples include `002371`, `688008`. P1.1 Semiconductor first implementation supports only `002371` as the primary sample, with equipment sub-chain as the first-version path. `688012 / 688981 / 603501 / 300604` have completed validation observation after upstream raw / fundamental / evidence-pack refresh and P1.1 rerun; they were not forced into `002371` equipment first-version order logic and remain outside first-version support unless a future design / implementation / acceptance cycle expands the scope. `300308 / 300476` remain boundary / negative samples and must not be forced into semiconductor P1.1 support. Materials / fabless / foundry / OSAT are not fully implemented in the first version and are handled only as `not_applicable` / `not_assessable` boundaries under `002371`. Main boundary: R&D and domestic substitution narratives need revenue/order validation; inventory cycle risk remains central.
- `stable_growth`: for steadier growth companies such as grid and electrical equipment where orders, cash flow, ROE, receivables, capex discipline, and shareholder-return support matter. P1.1 Stable Growth first implementation supports only `stable_growth + 600406` as the primary sample path. `002028` is validation / boundary only and must not be treated as first-version positive support; `600276` is excluded because the refreshed classifier result remains `unknown / insufficient_data` and pharmaceutical / biotech pipeline risk can invalidate the ordinary Stable Growth premise. Main boundary: the `stable_growth` label is not operating-steadiness evidence; industry rigid demand, infrastructure, policy protection, and SOE / central-SOE attributes are not demand-durability evidence; revenue growth is not stable growth; single-period `revenue_yoy` plus operating cash flow is not multi-period quality; contract liabilities are not backlog; receivable growth is not high-quality revenue; single-period OCF improvement is not long-term cash-flow stability; dividend / payout requires free cash flow, debt, capex, and earnings-quality support; single-period ROE is not long-term competitiveness; capex is not capacity release, utilization, future revenue, or growth conversion; valuation metrics are evidence-sufficiency context only.
- `advanced_manufacturing_growth`: for auto thermal management, robotics actuators, industrial automation, precision manufacturing, and new-energy-vehicle supply-chain growth. P1.1 Advanced Manufacturing first implementation supports only `advanced_manufacturing_growth + 002050` as the primary sample path; `601689` remains a later validation / boundary sample and must not be treated as first-version support. The `601689` boundary smoke confirmed that even when the classifier recognizes `advanced_manufacturing_growth`, P1.1 keeps it at `unsupported_pilot_strategy` / `not_assessable` and does not apply the `002050` refrigeration / air-conditioning, automotive thermal-management, and robotics / actuator / emerging-business matrix. Main boundary: robot/new-business exposure must be verified by independent non-zero revenue, orders, customers, mass-production, delivery, and collection evidence; refrigeration / air-conditioning and automotive thermal-management data cannot proxy robotics realization.
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

The planned Ground Truth Benchmark is separate from the current regression suite:
regression prevents output drift, while the benchmark will verify selected field
facts that were generated as provider / official-parser candidates and then
accepted by automatic gates or human review. It must not be mixed directly into
the existing regression expected files.

Regression fixtures live under `tests/regression/fixtures`, with expectations under `tests/regression/expected`. The standalone regression runner is `scripts/run_regression_suite.py`.

## 9. Common Commands

```bash
python -m pytest tests --basetemp=.pytest_tmp -p no:cacheprovider
python scripts/run_regression_suite.py
python -m src.fundamental_skill.data_providers.compare_providers --codes 600406,002050 --providers akshare,tushare --output-dir output/provider_comparison --dry-run
python -m src.fundamental_skill.real_stock_runner --code 601698 --output output/fundamental_601698.json --force-refresh
python -m src.fundamental_skill.ai_analyst.runner --code 601698 --mode prompt_only
python -m src.fundamental_skill.ai_analyst.research_intelligence_runner --code 002837
python -m src.fundamental_skill.ai_analyst.research_intelligence_p1_runner --code 000099
python -m src.fundamental_skill.ai_analyst.research_intelligence_p1_runner --code 000426
python -m src.fundamental_skill.ai_analyst.research_intelligence_p1_runner --code 002371
python -m src.fundamental_skill.ai_analyst.research_intelligence_p1_runner --code 002050
python -m src.fundamental_skill.ai_analyst.research_intelligence_p1_runner --code 600406
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
- P0.1 keeps this boundary while sharpening question text by `strategy_type`, `sub_type`, `missing_evidence`, and triggered `rule_id`; it does not change deterministic `status`, `confidence`, `score`, `strategy_type`, or `sub_type`, and it does not connect to the HTML Report main chain.

Interpretation boundaries:

- `confidence` is confidence in the evidence behind the current `fundamental_view`; it is not positive strength, upside probability, or investment attractiveness.
- Proxy evidence must be explicitly labeled and must not be treated as fact.
- Contract liabilities are not backlog.
- Capex is not confirmed capacity release.
- R&D ratio is not confirmation of a technology barrier.
- Theme heat is not fundamental realization.
- Resource P1.1 guardrails: commodity price is not company revenue; commodity cycle is not company performance; reserves are not production; production is not sales unless both are disclosed and reconciled; capex is not capacity release; inventory movement is not demand judgment; missing hedging disclosure is neither hedged nor unhedged; `resource_core` steadiness / dividend capacity must not be written as fact.
- Semiconductor P1.1 guardrails: semiconductor cycle is not company performance; localization narrative is not revenue realization; R&D ratio is not a technology barrier or moat; customer introduction / certification / qualification is not batch revenue; contract liabilities are not backlog; capex is not capacity release, utilization, delivery, or revenue conversion; inventory movement is not demand judgment; export controls / sanctions are not company operating benefit or damage facts without company-level impact evidence.
- Advanced Manufacturing P1.1 guardrails: robotics theme is not revenue realization; strategic layout wording and `news` / `latest_news` are not valid `company_transmission_path` nodes; refrigeration / air-conditioning and automotive thermal-management financial data cannot proxy robotics realization; design-win / qualification / nomination is not batch revenue; contract liabilities are not backlog; capex is not capacity release, mass production, utilization, or revenue conversion; R&D ratio is not a technology barrier; receivable growth is not high-quality revenue; inventory movement is not demand judgment; valuation metrics are evidence-sufficiency context only and must not become target price, valuation-high/low, or trading judgment.
- Stable Growth P1.1 guardrails: the `stable_growth` label is not operating-steadiness evidence; industry rigid demand, infrastructure, policy protection, and SOE / central-SOE attributes are not demand-durability evidence; revenue growth is not stable growth; single-period `revenue_yoy` plus same-direction operating cash flow is not multi-period stable-growth quality; contract liabilities are not backlog; receivable growth is not high-quality revenue; single-period OCF improvement is not long-term cash-flow stability; dividend / payout is not sustainable shareholder return without free cash flow, debt, capex, and earnings-quality support; single-period ROE is not long-term competitiveness; capex is not capacity release, utilization, future revenue, or growth conversion; valuation metrics are evidence-sufficiency context only and must not become valuation-high/low, target price, upside, or trading judgment.

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
- Research Intelligence P0 has been accepted as a baseline research-question discovery artifact.
- Research Intelligence P0.1 Template Sharpening and Fallback Template Cleanup have passed final acceptance. The latest acceptance refreshed and reviewed `002837`, `002050`, `603259`, and `300442`; pytest recorded `379 passed`, and the regression suite recorded `passed=47 failed=0 total=47`.
- Research Intelligence P1.1 AI Datacenter pilot, CXO expansion, Satellite expansion, Low Altitude expansion, Resource first implementation, Semiconductor first implementation, Advanced Manufacturing first implementation, and Stable Growth first implementation have been implemented and accepted. Current P1.1 support is intentionally limited to `ai_datacenter_infrastructure`, `life_science_cxo_services`, `satellite_communication_infrastructure`, `low_altitude_economy_infrastructure`, `resource_swing` for primary sample `000426`, `semiconductor_cycle` for primary sample `002371`, `advanced_manufacturing_growth` for primary sample `002050`, and `stable_growth` for primary sample `600406`; it does not expand to all `strategy_type` values. AI Datacenter acceptance covered `002837` and `300442`; Satellite primary acceptance covered `601698`; Low Altitude primary acceptance covered `000099`; Resource primary acceptance covered `000426`; Semiconductor primary acceptance covered `002371`; Advanced Manufacturing primary acceptance covered `002050`; Stable Growth primary acceptance covered `600406`. `resource_core` is design-only, `601899 / 603993` remain later Resource validation / boundary samples, `601689` remains a later Advanced Manufacturing validation / boundary sample, `002028` is Stable Growth validation / boundary only, and `600276` is excluded from Stable Growth first-version support. Semiconductor multi-sample observation is complete: validation samples `688012 / 688981 / 603501 / 300604` were refreshed through upstream data and P1.1, boundary samples `300308 / 300476` were not forced into semiconductor support, and no validation sample was incorrectly mapped to the `002371` equipment first-version logic. Advanced Manufacturing multi-sample observation is complete, and the `601689` boundary data completion smoke is complete: `601689` was classified as `advanced_manufacturing_growth` but correctly returned `unsupported_pilot_strategy` / `not_assessable`, preserved fallback `company_transmission_path`, source-bucket independence, and safety boundary behavior, and was not force-fit into the `002050` three-business-layer matrix or Tuopu large-customer / robotics revenue realization narrative. Stable Growth acceptance recorded `missing / not_assessable = 19/33 = 57.58%`, which is expected and correct. Data-side caveat: `601689` `news` / `latest_news` still reports `Invalid regular expression: invalid escape sequence: \u`; this is an upstream/news data issue and does not affect the P1.1 boundary smoke conclusion. Latest recorded pytest result is `484 passed`, and latest recorded regression suite result is `passed=47 failed=0 total=47`.
- `output/research_intelligence_p1_*` and `output/research_questions_p1_*` are generated runtime artifacts and should not be committed.
- P0.1 sample acceptance coverage:
  - `002837` Envicool: liquid-cooling customer validation, batch-order distinction, room cooling versus ordinary thermal-control boundary.
  - `002050` Sanhua Intelligent Controls: robotics / new-business revenue, orders, customers, major-customer revenue share, and valuation digestion evidence.
  - `603259` WuXi AppTec: backlog, new orders, contract-liability proxy guard, overseas / US customers, Biosecure Act / overseas regulatory risk, and capacity utilization.
  - `300442` Range Intelligent Computing: cabinet / MW scale, rack-up rate, PUE, customer contracts, capex-to-revenue bridge, depreciation, and power cost.
- HTML report generation v2.1 does not automatically call an API; it creates prompts and renders existing formal `FundamentalHtmlReport` JSON.
- Data Provider Abstraction Phase 2 is accepted. The default real-stock path still directly uses `RealDataConnector`; `ProviderRouter` is not connected to the production runner. Phase 2 did not connect real Tushare, read real tokens, read local MCP config, call MCP, add network calls, change deterministic pipeline behavior, change P1.1, change HTML / Dashboard, or change regression expected outputs. Latest recorded verification after Phase 2 acceptance: pytest `520 passed`; regression suite `passed=47 failed=0 total=47`.
- Tushare migration Phase 3 mocked MVP is implemented and accepted. Phase 3 includes `TushareClient` abstraction, mocked transport, mocked response mapping for `basic_info`, `financial_indicator`, `valuation`, `business_composition`, explicit missing / fallback `news`, `fetch_status` / `errors` / `source_trace`, token safety, no-token fail-closed behavior, and mock tests only. Canonical raw output remains `meta`, `blocks`, `fetch_status`, and `errors`; canonical raw blocks remain `basic_info`, `financial_indicator`, `valuation`, `business_composition`, and `news`. Mocked tests cover `stock_basic -> basic_info`, `income / balancesheet / cashflow / fina_indicator -> financial_indicator`, `daily_basic -> valuation`, `fina_mainbz -> business_composition`, and `news -> missing / fallback`. Phase 3 did not do real token smoke, MCP integration, real network calls in tests, `provider=auto` primary switch, dual-source comparison, news replacement, `commodity_prices` replacement, industry-specific operating indicators, minute / realtime technical data, classifier / scoring / readiness changes, `evidence_pack` schema changes, HTML / P1.1 changes, or regression expected changes. Real tokens must never be written to code, docs, tests, logs, output, commits, or review comments; docs may only use `<TUSHARE_TOKEN>` as a placeholder, and MCP URL text from local config must not enter the repository. Latest Phase 3 verification: targeted tests `36 passed`; full `pytest` `541 passed`; regression suite `passed=47 failed=0 total=47`.
- Provider migration roadmap snapshot: Phase 0 completed; Phase 1 accepted; Phase 2 accepted; Phase 3 accepted; Phase 4 dry-run accepted; Phase 4 local real-token smoke gate documentation completed; Phase 4 real-token smoke gate safety skeleton implemented and accepted; third local real-token smoke review completed as `partial_pass_data_review_required`; Phase 4 score / confidence explainability design, implementation, acceptance, narrative hints patch, narrative-hints artifact review, and closeout baseline freeze completed. Fundamental Ground Truth Benchmark Design is recorded in `docs/FUNDAMENTAL_GROUND_TRUTH_BENCHMARK_DESIGN.md`, the fixture skeleton is present, Auto Fact Candidate Generator Design is recorded in `docs/FUNDAMENTAL_AUTO_FACT_CANDIDATE_GENERATOR_DESIGN.md`, Candidate Report Review Protocol Design is recorded and accepted in `docs/FUNDAMENTAL_CANDIDATE_REPORT_REVIEW_PROTOCOL_DESIGN.md`, Candidate Review Decisions Artifact Design is recorded in `docs/FUNDAMENTAL_CANDIDATE_REVIEW_DECISIONS_ARTIFACT_DESIGN.md`, Research Report V1 design, implementation, baseline freeze, presentation profile registry acceptance, cross-industry Markdown profile acceptance, HTML renderer implementation, three-sample HTML acceptance, single-stock offline orchestration acceptance, CLI implementation acceptance, single-stock offline CLI runtime acceptance, and CLI usage documentation are complete. User Invocation / Report Orchestration Design is recorded in `docs/FUNDAMENTAL_SKILL_USER_INVOCATION_ORCHESTRATION_DESIGN.md`, the offline acceptance summary is recorded in `docs/FUNDAMENTAL_SKILL_OFFLINE_ORCHESTRATION_ACCEPTANCE_SUMMARY.md`, CLI / command wrapper design is recorded in `docs/FUNDAMENTAL_SKILL_USER_INVOCATION_CLI_DESIGN.md`, CLI runtime acceptance is recorded in `docs/FUNDAMENTAL_SKILL_CLI_RUNTIME_ACCEPTANCE_SUMMARY.md`, and CLI usage is recorded in `docs/FUNDAMENTAL_SKILL_CLI_USAGE_GUIDE.md`. Next is batch / Dashboard design, not another Phase 4 smoke, not more ad hoc single-target HTML generation, not more single-stock CLI runtime generation, not CLI usage documentation, not manual field filling, not fixture promotion, not validator implementation, not promote-rule design, and not Tushare primary switch. Later work can evaluate promote rules, controlled fixture promotion, Tushare block-level primary design, P1.1 deep validation, `fina_mainbz` `type=P/D/I` ratio derivation, live provider report, official parser / CNInfo, MCP, Tushare token work, and sidecar data availability design.
- Data Provider Phase 4 dual-source comparison dry-run tooling is implemented and accepted. Phase 4 remains comparison-only / local-acceptance-gated: `AkShareProvider -> raw dict -> FundamentalSkillPipeline.analyze_from_dict -> EvidencePackBuilder.build` versus `TushareProvider -> raw dict -> FundamentalSkillPipeline.analyze_from_dict -> EvidencePackBuilder.build`. Added modules are `compare_providers`, `comparison_artifacts`, `diff_classifier`, `token_leak_scanner`, `real_token_smoke_gate`, `tushare_sdk_transport`, and `score_confidence_explainability.py`. Default dry-run does not generate `output/provider_comparison`, does not write production output, does not run HTML, and does not run P1.1. Artifact writes, when explicitly enabled, are allowed only under `output/provider_comparison/<timestamp>/<code>/`; `score_confidence_explainability.json` is allowlisted only for explicit `--explainability` and does not change default `diff_report.json` / `diff_report.md`. The accepted artifact can include top-level `narrative_hints[]`; each hint is reviewer-facing only, has `automatic_acceptance=false` and `not_for_scoring=true`, does not change score / confidence / drift acceptance, does not enter scoring / classifier / readiness, does not write back canonical fields, and is not a primary-switch or automatic-merge basis. Forbidden writes include `output/raw_<code>.json`, `output/fundamental_<code>.json`, `output/evidence_pack_<code>.json`, `output/reports`, default output, and report output. P1.1 comparison is off by default and requires `--include-p1`; real-token smoke requires explicit `--real-token-smoke --provider-transport sdk`, rejects CLI token input, fails closed with no token before SDK calls, and keeps `http` / `mcp-local` reserved fail-closed; `--explainability` cannot be combined with `--real-token-smoke` in V1. The gate scans repo tracked files, staged diff, docs / tests / source, target output, payloads, and diff reports; it baselines `output/reports` and default output path sets plus SHA-256 hashes; cleanup is limited to a strict timestamp directory under `output/provider_comparison`. The diff classifier marks `strategy_type_drift`, classification / confidence / score / P1 drift as `review_required`, treats secret-risk findings as blockers, adds reviewer-aid drift subcategory values for explainability, and does not automatically accept drift. The token scanner covers secret-like credential patterns and emits only location plus `<masked>`. Latest explainability narrative-hints acceptance verification: targeted tests `27 passed`; full `pytest` `648 passed, 1 skipped`; regression suite `passed=47 failed=0 total=47`.
- Data Provider Phase 4 third local real-token smoke review artifact root was `output/provider_comparison/20260526T233804`. Current conclusion is `partial_pass_data_review_required`: token leak, artifact-boundary failure, default output pollution, `output/reports` modification, and regression expected modification were not observed; Tushare endpoints were usable; non-news blocks were non-empty; canonical shape was correct; `market_cap` units and `gross_margin` were corrected; business-level `gross_margin` was derived; there was no `missing_field_regression`, `strategy_type_drift`, or `classification_drift`. Remaining score drift and confidence drift for `000426` / `002837` are now covered by accepted comparison-only explainability tooling. Latest third-smoke verification: full `pytest` `630 passed, 1 skipped`; regression suite `passed=47 failed=0 total=47`. Latest explainability implementation verification: targeted tests `38 passed`; full `pytest` `644 passed, 1 skipped`; regression suite `passed=47 failed=0 total=47`. Do not switch Tushare primary, do not automatically merge, do not automatically accept drift, and do not run another real-token smoke unless later provider mapping or sidecar execution changes require it.
- Data Provider Phase 4 narrative hints patch is accepted as an explainability extension. Accepted hint coverage: `600406` `business_quality_main_business_gap` / `business_ratio_missing`; `002050` `advanced_manufacturing_business_exposure_gap`; `002371` `semiconductor_business_text_or_ratio_gap` / `semiconductor_financial_inputs_available`; `603259` `cxo_domain_proxy_gap`; `000426` `external_sidecar_missing` / `commodity_context_provider_independent`; `002837` `domain_evidence_missing` / `liquid_cooling_revenue_share_missing` / `orders_customer_validation_batch_delivery_missing`. Latest narrative-hints verification: targeted tests `27 passed`; full `pytest` `648 passed, 1 skipped`; regression suite `passed=47 failed=0 total=47`.
- Data Provider Phase 4 closeout / baseline freeze is complete. Tushare is usable for comparison but remains non-primary; AkShare / Tushare data must not be automatically merged; drift must not be automatically accepted. The third-smoke artifact root is timestamp `20260526T233804` under `output/provider_comparison/`; it can remain as a local, ignored, untracked review artifact. Ground Truth Benchmark, Auto Fact Candidate Generator, Candidate Report Review Protocol, Candidate Review Decisions Artifact, Research Report V1, User Invocation / Report Orchestration, and User Invocation CLI / Command Wrapper are documented; Research Report V1 implementation and baseline freeze are complete, the `600406`, `002371`, and `002050` Markdown profiles have passed cross-industry acceptance, the HTML renderer implementation is accepted, the three-sample HTML baseline is frozen, the three-sample offline orchestration runtime baseline is frozen, the single-stock offline CLI baseline is frozen, and the CLI usage guide is recorded. The next recommended phase is batch / Dashboard design.
- `002050` 三花智控 is an internal successful HTML report sample candidate after v2.1 and visual audit acceptance.
- `output/`, `output/reports/`, `output/visual_audit/`, `data/`, and `cache/` are generated/runtime artifacts and should not be committed.
- Some industries remain uncovered, including banks, medical devices, and intelligent driving. CXO is covered by `life_science_cxo_services`, and AI datacenter infrastructure is covered by `ai_datacenter_infrastructure` v1, but both still have conservative public-data limits.
- AI Datacenter v1 remains limited by public data availability for orders / backlog, customer structure, cabinet count, MW scale, PUE, rack utilization, liquid-cooling revenue, customer validation, datacenter revenue split, and customer capex-cycle evidence.

## 13. Suggested Next Steps

- Current Research Report V1 presentation and invocation step: the HTML
  renderer implementation is accepted, the three-sample HTML baseline is
  frozen, single-stock offline orchestration implementation is accepted, the
  Chinese summary patch is accepted, and `600406`, `002371`, and `002050` have
  passed one-sentence local report invocation runtime acceptance. CLI
  implementation is accepted, `600406`, `002371`, and `002050` have passed CLI
  runtime acceptance, and the single-stock offline CLI baseline is frozen. User
  invocation / report orchestration design is recorded in
  `docs/FUNDAMENTAL_SKILL_USER_INVOCATION_ORCHESTRATION_DESIGN.md`, the
  offline acceptance summary is recorded in
  `docs/FUNDAMENTAL_SKILL_OFFLINE_ORCHESTRATION_ACCEPTANCE_SUMMARY.md`, the
  CLI / command wrapper design is recorded in
  `docs/FUNDAMENTAL_SKILL_USER_INVOCATION_CLI_DESIGN.md`, and the CLI runtime
  acceptance summary is recorded in
  `docs/FUNDAMENTAL_SKILL_CLI_RUNTIME_ACCEPTANCE_SUMMARY.md`. CLI usage is
  recorded in `docs/FUNDAMENTAL_SKILL_CLI_USAGE_GUIDE.md`. Next useful
  direction is batch / Dashboard design. HTML must
  consume Markdown / presentation-layer output or the Research Report V1
  structured payload; it must not re-analyze, change conclusions, hide caveats,
  call providers, use the network, read tokens, connect MCP, change tests,
  change scoring / readiness, change P1.1, change fixtures, or change
  regression expected files.
- Keep `README.md` and `docs/PROJECT_CONTEXT_HANDOFF.md` synchronized after major project changes.
- Keep `docs/DATA_PROVIDER_ABSTRACTION_TUSHARE_MIGRATION_DESIGN.md` synchronized with the accepted provider-migration phase boundary.
- For data-source migration and research-report output, score / confidence explainability implementation and narrative hints are accepted, the Fundamental Ground Truth Benchmark fixture skeleton is present, the Auto Fact Candidate Generator design is documented, the `600406` V1.1 candidate report has been generated and passed usability review / audit, Candidate Report Review Protocol Design is accepted, Candidate Review Decisions Artifact Design is documented, `600406` `candidate_review_decisions.json` exists as an intermediate audit artifact, Research Report V1 design, implementation, baseline freeze, presentation profile registry, cross-industry Markdown profile acceptance, HTML renderer implementation, three-sample HTML acceptance, three-sample offline orchestration acceptance, CLI implementation acceptance, three-sample CLI runtime acceptance, and CLI usage documentation are complete. User Invocation / Report Orchestration Design, CLI / Command Wrapper Design, CLI Runtime Acceptance Summary, and CLI Usage Guide are recorded. Next useful step is batch / Dashboard design. Promote-rule design, controlled fixture promotion, standalone validator, `fina_mainbz` `type=P/D/I` selected-period ratio derivation evaluation, Tushare primary switch, live provider report, official parser / CNInfo, MCP, Tushare token work, and sidecar policy design should remain later work. Do not run another real-token smoke unless later provider mapping or sidecar execution changes require it, do not request or read a token, do not connect MCP or read local MCP config, do not call Tushare or use the network, do not switch `provider=auto` primary behavior, do not auto-merge AkShare / Tushare data, do not auto-accept drift, and do not wire provider routing into the default production runner without a separate acceptance cycle.
- Research Intelligence P0.1 baseline does not need more repair unless new samples reveal generic fallback wording or weak industry context. Next useful directions are multi-sample real use, P1 design, or longitudinal resolved-question workflows.
- For Research Intelligence P1.1, the accepted Resource baseline should remain frozen at `resource_swing + 000426` until later validation is explicitly designed. Do not expand `resource_core`, `601899`, or `603993` in P1.1 without a new design / implementation / acceptance cycle, and do not jump directly into P1.2 or P1.3 before current P1.1 artifact behavior is observed across more samples.
- For Research Intelligence P1.1, the accepted Semiconductor baseline should remain frozen at `semiconductor_cycle + 002371`, the accepted Advanced Manufacturing baseline should remain frozen at `advanced_manufacturing_growth + 002050`, and the accepted Stable Growth baseline should remain frozen at `stable_growth + 600406` unless a new design / implementation / acceptance cycle expands them. Do not expand `601689`, `002028`, `600276`, `688012`, `688981`, `603501`, `300604`, `300308`, or `300476` into first-version support without a new design / implementation / acceptance cycle. Future work can evaluate `right_trend_growth` or P1.2, but should not widen the accepted P1.1 slices implicitly.
- HTML Report Generator v2.1 baseline does not need more repair unless the user reports a specific visual or content issue.
- Based on user feedback, continue with batch / Dashboard design. Do not
  continue generating more ad hoc single-stock Research Report V1 HTML
  artifacts, do not continue single-stock CLI runtime generation, and do not
  redo CLI usage documentation unless a new sample, regression check, or
  usage-surface change explicitly requests that scope.
- Keep AI Datacenter v1 conservative unless public data sources can reliably validate orders / backlog, customer structure, cabinet / MW / PUE / rack utilization, liquid-cooling revenue, datacenter revenue split, and customer capex-cycle evidence.
- Do not rush into `technical_skill` or `trader_skill`.
- Do not connect trading accounts, add target prices, introduce technical analysis, or turn reports into trading recommendations.
- Do not blindly add more fields without source stability, interpretation rules, and regression coverage.
- Every new industry framework must follow the documented workflow.

## 14. Research Report V1 Markdown And HTML Acceptance Update

Research Report V1 design, implementation, baseline freeze, presentation
profile registry, cross-industry Markdown profile validation, and HTML
presentation layer design are accepted.
Use
`docs/FUNDAMENTAL_RESEARCH_REPORT_V1_MARKDOWN_PROFILE_ACCEPTANCE_SUMMARY.md` as
the current Markdown acceptance summary. Use
`docs/FUNDAMENTAL_RESEARCH_REPORT_V1_HTML_ACCEPTANCE_SUMMARY.md` as the current
HTML acceptance summary. Use
`docs/FUNDAMENTAL_SKILL_OFFLINE_ORCHESTRATION_ACCEPTANCE_SUMMARY.md` as the
current offline orchestration acceptance summary. The HTML renderer
implementation is accepted, the three-sample HTML validation passed, the HTML
presentation layer baseline is frozen, and the one-sentence local report
invocation baseline is frozen.

Older `002371` Markdown / HTML runtime artifacts were superseded by the
`20260528T125518` professional-voice regenerated artifacts; user-facing
orchestration baseline should use the `20260528T125518` Markdown / HTML
artifacts.

Accepted Markdown runtime artifacts:

- `600406` 国电南瑞:
  `output/research_reports/20260527T210301/600406/fundamental_research_report_v1.md`
- `002371` 北方华创:
  `output/research_reports/20260528T125518/002371/fundamental_research_report_v1.md`
- `002050` 三花智控:
  `output/research_reports/20260528T003826/002050/fundamental_research_report_v1.md`

Accepted HTML runtime artifacts:

| code | company | profile | accepted HTML artifact |
| --- | --- | --- | --- |
| `600406` | 国电南瑞 | `stable_growth_grid_equipment` | `output/research_reports/20260528T012952/600406/fundamental_research_report_v1.html` |
| `002371` | 北方华创 | `semiconductor_equipment_cycle` | `output/research_reports/20260528T125518/002371/fundamental_research_report_v1.html` |
| `002050` | 三花智控 | `advanced_manufacturing_thermal_management` | `output/research_reports/20260528T091133/002050/fundamental_research_report_v1.html` |

Accepted offline orchestration runtime artifacts:

| code | company | selected HTML artifact | selected Markdown artifact | selected JSON artifact | acceptance result |
| --- | --- | --- | --- | --- | --- |
| `600406` | 国电南瑞 | `output/research_reports/20260528T012952/600406/fundamental_research_report_v1.html` | `output/research_reports/20260527T210301/600406/fundamental_research_report_v1.md` | `output/research_reports/20260527T103241/600406/fundamental_research_report_v1.json` | Runtime accepted. |
| `002371` | 北方华创 | `output/research_reports/20260528T125518/002371/fundamental_research_report_v1.html` | `output/research_reports/20260528T125518/002371/fundamental_research_report_v1.md` | `output/research_reports/20260527T220148/002371/fundamental_research_report_v1.json` | Runtime accepted. |
| `002050` | 三花智控 | `output/research_reports/20260528T091133/002050/fundamental_research_report_v1.html` | `output/research_reports/20260528T003826/002050/fundamental_research_report_v1.md` | `output/research_reports/20260527T222558/002050/fundamental_research_report_v1.json` | Runtime accepted. |

Accepted CLI runtime artifacts:

| code | company | command | selected HTML artifact | selected Markdown artifact | selected JSON artifact | exit code | acceptance result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `600406` | 国电南瑞 | `python -m src.fundamental_skill.research_report.generate_report --code 600406 --format html --data-mode offline_local_artifacts` | `output/research_reports/20260528T012952/600406/fundamental_research_report_v1.html` | `output/research_reports/20260527T210301/600406/fundamental_research_report_v1.md` | `output/research_reports/20260527T103241/600406/fundamental_research_report_v1.json` | `0` | CLI runtime accepted. |
| `002371` | 北方华创 | `python -m src.fundamental_skill.research_report.generate_report --company-name 北方华创 --format html` | `output/research_reports/20260528T125518/002371/fundamental_research_report_v1.html` | `output/research_reports/20260528T125518/002371/fundamental_research_report_v1.md` | `output/research_reports/20260527T220148/002371/fundamental_research_report_v1.json` | `0` | CLI runtime accepted. |
| `002050` | 三花智控 | `python -m src.fundamental_skill.research_report.generate_report --company-name 三花智控 --format html` | `output/research_reports/20260528T091133/002050/fundamental_research_report_v1.html` | `output/research_reports/20260528T003826/002050/fundamental_research_report_v1.md` | `output/research_reports/20260527T222558/002050/fundamental_research_report_v1.json` | `0` | CLI runtime accepted. |

Accepted profiles:

- `stable_growth_grid_equipment` for `600406`.
- `semiconductor_equipment_cycle` for `002371`.
- `advanced_manufacturing_thermal_management` for `002050`.

Final status:

- `600406` Markdown accepted.
- `002371` Markdown accepted.
- `002050` Markdown accepted.
- `600406` HTML accepted.
- `002371` HTML accepted.
- `002050` HTML accepted.
- Presentation profile registry accepted.
- Professional analyst voice gate accepted.
- Cross-industry Markdown validation passed.
- Three-sample HTML validation passed.
- HTML presentation layer baseline frozen.
- User invocation / report orchestration design recorded.
- Single-stock offline orchestration implementation accepted.
- Chinese summary patch accepted.
- `600406` runtime accepted.
- `002371` runtime accepted.
- `002050` runtime accepted.
- One-sentence local report invocation baseline frozen.
- CLI implementation accepted.
- `600406` CLI runtime accepted.
- `002371` CLI runtime accepted.
- `002050` CLI runtime accepted.
- Single-stock offline CLI baseline frozen.

Cross-contamination result:

- `600406` did not inherit semiconductor or robot / new-business language.
- `002371` did not inherit grid or thermal-management language.
- `002050` did not inherit grid or semiconductor-equipment language.
- Current V1 hard-fail term isolation is effective for the three accepted
  samples.
- Future cross-industry terms require a separately designed
  evidence-label-aware allowlist.

Latest verification results are quoted from the accepted inputs and were not
rerun in the documentation-only summary stages: Markdown targeted tests
`86 passed`, Markdown full pytest `734 passed, 1 skipped`, HTML targeted tests
`124 passed`, CLI runtime targeted tests `163 passed`, latest full
pytest `811 passed, 1 skipped`, and regression
`passed=47 failed=0 total=47`.

HTML presentation layer design:

- design doc:
  `docs/FUNDAMENTAL_RESEARCH_REPORT_V1_HTML_PRESENTATION_DESIGN.md`
- acceptance summary:
  `docs/FUNDAMENTAL_RESEARCH_REPORT_V1_HTML_ACCEPTANCE_SUMMARY.md`
- preferred input: accepted Markdown presentation output;
- optional input: `fundamental_research_report_v1.json` for display metadata,
  cards, evidence labels, source refs, and caveats only;
- accepted output pattern:
  `output/research_reports/<timestamp>/<code>/fundamental_research_report_v1.html`
- baseline status: HTML renderer implementation accepted; `600406`, `002371`,
  and `002050` HTML accepted; three-sample HTML baseline frozen;
- strict boundary: no re-analysis, no conclusion changes, no hidden caveats,
  no provider calls, no network, no token reads, no MCP, no raw provider dump,
  no default output, no fixtures, no regression expected changes, no scoring /
  readiness changes, no P1.1 changes, and no trading advice.

User invocation / report orchestration acceptance:

- design doc:
  `docs/FUNDAMENTAL_SKILL_USER_INVOCATION_ORCHESTRATION_DESIGN.md`
- acceptance summary:
  `docs/FUNDAMENTAL_SKILL_OFFLINE_ORCHESTRATION_ACCEPTANCE_SUMMARY.md`
- CLI / command wrapper design:
  `docs/FUNDAMENTAL_SKILL_USER_INVOCATION_CLI_DESIGN.md`
- CLI runtime acceptance summary:
  `docs/FUNDAMENTAL_SKILL_CLI_RUNTIME_ACCEPTANCE_SUMMARY.md`
- CLI usage guide:
  `docs/FUNDAMENTAL_SKILL_CLI_USAGE_GUIDE.md`
- entry point: natural-language Codex / GPT-5.5 request;
- default request mode: `offline_local_artifacts`, `no_live_provider`,
  `allow_network=false`, `allow_token_read=false`;
- output response: HTML path, Markdown path, JSON path, short Chinese summary,
  maximum opportunity, maximum risk, maximum evidence gap, data-quality status,
  and not-for-trading-advice statement;
- boundary: no token read, no network, no provider call, no MCP, no free-form
  model report outside the artifact chain, no hidden caveats, no target price,
  no position sizing, and no technical trading signal.
- validated CLI flow: Codex / user command -> CLI argument parsing -> accepted
  offline orchestration -> normalize request -> safe offline flags -> locate
  local artifacts -> reuse accepted HTML -> extract Chinese summary from
  Markdown -> stdout returns HTML / Markdown / JSON paths plus opportunity /
  risk / evidence gap / data quality and the not-for-trading-advice statement.
- accepted CLI baseline: `600406`, `002371`, and `002050` exit code `0`,
  Chinese operational stdout, correct selected artifacts, no English JSON
  summary leak, no full report body dump, no cross-profile contamination,
  artifact boundary passed, token / secret / provider scan passed, and
  forbidden output check passed.

Next recommended stage: batch / Dashboard design. Do not continue single-stock
CLI runtime generation or redo CLI usage documentation unless a new sample,
regression check, or usage-surface change requires it.
Promote rules, validator, fixture promotion, live provider report, official
parser / CNInfo, MCP, Tushare token work, and Tushare primary remain later work.

## 15. User Invocation / Orchestration Recovery Notes

When resuming this project, treat
`docs/FUNDAMENTAL_SKILL_USER_INVOCATION_ORCHESTRATION_DESIGN.md` as the current
product-stage design and
`docs/FUNDAMENTAL_SKILL_OFFLINE_ORCHESTRATION_ACCEPTANCE_SUMMARY.md` as the
current offline runtime acceptance closeout. Treat
`docs/FUNDAMENTAL_SKILL_USER_INVOCATION_CLI_DESIGN.md` as the current
command-wrapper design, and
`docs/FUNDAMENTAL_SKILL_CLI_RUNTIME_ACCEPTANCE_SUMMARY.md` as the current CLI
runtime acceptance closeout. Treat `docs/FUNDAMENTAL_SKILL_CLI_USAGE_GUIDE.md`
as the current CLI usage guide. The single-stock offline CLI baseline is
frozen. The next work should enter batch / Dashboard design.

Default invocation must be local-only and must not read `TUSHARE_TOKEN`, use
the network, call Tushare / AkShare, connect MCP, change tests, change
fixtures, change scoring / readiness, change P1.1, change regression expected
files, write runtime artifacts into git, or provide trading advice.

## 16. New Codex Conversation Recovery Prompt

Copy this into a new Codex / AI conversation:

```text
请先阅读 docs/PROJECT_CONTEXT_HANDOFF.md 并恢复当前项目上下文，不要改代码、不要改 config、不要改 tests、不要改 pipeline、不要改 dashboard。当前项目是 A 股基本面 AI 分析 Skill，只做基本面，不输出交易建议、不做技术面、不接交易账户。请先总结你理解的项目定位、架构、安全边界、当前 strategy_type、已完成行业框架、测试体系和下一步建议，然后等待我给出本阶段任务。
```
