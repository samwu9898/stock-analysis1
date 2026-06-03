# Research Intelligence P0/P1 -> Investment Director Research Context Pack Reuse Adapter + Missing Coverage Map Thin Slice

## Baseline Commits

- Implementation commit: `8e7526789a77dff45b6aeced6a7f51ab4c016ad5`
- Previous completed stage: Controlled Real LLM Local Manual Smoke acceptance summary commit `0019621`
- Current rulebook state: Investment Director Research Context Pack / Missing Coverage Map rules

## Stage Positioning

This stage is a research-material integration layer. It is not a rebuild of Research Intelligence from zero, not a raw Tushare dump, not a real LLM renderer adapter, not DeepSeek live integration, no LLM API, no Tushare live, not Report V1 integration, not HTML renderer work, not official metric verification, not provider-vs-official reconciliation, and it creates no runtime artifact.

The goal is to unify old Research Intelligence P0/P1, the old frontstage report snapshot, the ticker context skeleton, and an evidence-aware pack-shaped input into a DeepSeek-next-use investment-director context pack.

## Modified Files

Only these implementation files are accepted for the completed implementation commit:

- `src/fundamental_skill/research_planning/investment_director_research_context_pack.py`
- `tests/test_investment_director_research_context_pack.py`
- `tests/test_investment_director_research_context_pack_safety.py`

## Functional Summary

The implementation defines and validates these schemas and context sections:

- `investment_director_research_context_pack.v1`
- `investment_director_missing_coverage_map.v1`
- `investment_director_coverage_item.v1`
- `investment_director_collision_question.v1`
- `investment_director_collision_question_set.v1`
- `investment_director_llm_context_prompt_payload.v1`
- `investment_director_source_asset_summary.v1`
- `source_tier_and_viewpoint_context`
- `director_framework_alignment`
- `frontstage_visualization_requirements`

The pack is an explicit in-memory payload only. It rejects raw HTML, raw provider bundles, raw provider rows, raw candidate items, `source_url`, `page`, `snippet`, `sha256`, `cache_path`, token markers, `api_key`, `.env`, `tushare_token`, raw prompt text, and raw LLM response text. It does not read output runtime artifacts and does not write files.

## Old Asset Reuse Summary

The stage reuses Research Intelligence P0/P1 shaped payload semantics, source hierarchy, business-financial cross-validation, rule-triggered contradictions, driver questions, manual review items, IR questions, `not_assessable` boundaries, missing evidence, proxy guardrails, source bucket independence summaries, and old frontstage snapshot fields including core conclusion, conflicts, business composition, financial quality, valuation, quality score, risks, tracking, and data quality.

It also reuses ticker context skeleton and evidence-aware pack-shaped input semantics. It does not reuse old output artifacts and does not parse raw HTML.

## Missing Coverage Map

Missing Coverage Map is a core asset. Each item carries `requirement_id`, `name`, `status`, `currently_available_assets`, `currently_llm_visible`, `gap_description`, `required_evidence`, `next_data_task`, `priority`, `blocks_llm_depth`, `covered_semantics`, and `not_for_trading_advice`.

Allowed statuses are `covered`, `partial_but_not_llm_visible`, `framework_exists_but_missing_data`, `missing`, and `not_applicable`. `covered` has strict semantics: it must be supported by concrete available assets and visible enough for future LLM use. Gaps must carry concrete `required_evidence` and concrete `next_data_task`; vague tasks, hidden gaps, and unsupported `not_assessable` conclusions are not accepted.

## Coverage Categories

Base coverage categories:

- `macro_context`
- `international_macro`
- `fx`
- `commodity`
- `policy`
- `industry_cycle`
- `industry_consensus`
- `divergent_views`
- `opposing_views`
- `competitor_peer_benchmark`
- `upstream_downstream_prices`
- `company_business_structure`
- `business_competitiveness`
- `market_share`
- `project_progress`
- `capex_mapping`
- `r_and_d_conversion`
- `financial_statement_quality`
- `cashflow_receivable_inventory_linkage`
- `debt_financing_structure`
- `disclosure_consistency`
- `prior_promise_vs_current_delivery`
- `governance_risk`
- `regulatory_violation_risk`
- `black_swan_risk`
- `manual_research_notes`
- `ir_questions`
- `frontstage_chart_ready_sections`
- `html_report_mapping`

Patch coverage categories:

- `authoritative_data_crosscheck`
- `news_and_special_events`
- `source_tier_classification`
- `rd_staff_and_project_mapping`
- `revenue_driver_decomposition`
- `cost_driver_decomposition`
- `balance_sheet_reclassification`
- `financing_cashflow_dependency`
- `selective_disclosure_risk`
- `conclusion_first_frontstage`
- `visualization_plan`

Stable-growth coverage categories:

- `stable_cash_conversion`
- `stable_receivables_collection_quality`
- `stable_repeat_order_customer_retention`
- `stable_roe_roic_evidence_sufficiency`
- `stable_capex_discipline`
- `stable_dividend_payout_sustainability`

## Collision Questions

Collision questions are structured as `investment_director_collision_question.v1` and grouped in `investment_director_collision_question_set.v1`. Each question records the analytical collision, why it matters, which current assets support or fail to support it, what evidence is still required, and whether it blocks future LLM depth.

Question categories include business-model conflicts, financial-quality conflicts, growth-evidence conflicts, source-viewpoint conflicts, disclosure-consistency conflicts, valuation-evidence conflicts, and risk-boundary conflicts. They are designed to force investigation of contradictions instead of allowing a future renderer to smooth over evidence gaps.

## Source Tier And Viewpoint Context

`source_tier_and_viewpoint_context` summarizes source hierarchy, source buckets, and independent bucket count. When fewer than two independent buckets are available, consensus, divergence, and opposing-view claims must remain `not_assessable`.

The pack does not convert market opinion prose into evidence, does not treat a single source as multi-source consensus, and does not fetch or infer external data.

## Director Framework Alignment

`director_framework_alignment` is derived from the Missing Coverage Map. It records `framework_chain`, `weak_links`, and `next_alignment_tasks`.

Weak links come from missing or partial coverage. If weak links exist, the framework cannot claim full coverage. The alignment section makes the director-level logic visible without pretending the material is complete.

## Frontstage Visualization Requirements

`frontstage_visualization_requirements` describes future display requirements only. It includes `conclusion_first_sections`, `chart_ready_sections`, `table_ready_sections`, `material_backstage_sections`, and `missing_visualization_inputs`.

It creates no HTML, chart, report, Markdown, JSON, or runtime artifact. It aligns future frontstage work with conclusion-first organization, chartification, and material-backstage requirements.

## Prompt Payload

The DeepSeek future prompt payload is a draft payload only; it does not call DeepSeek. It defines role and task boundaries and includes `analysis_requirements`, `available_materials_summary`, `core_conflicts_to_analyze`, `collision_questions`, `missing_coverage_boundaries`, `required_output_sections`, and `output_boundaries`.

The prompt payload is intentionally concise. It does not dump `source_tier_summary`, `framework_chain`, `material_backstage_sections`, or `covered_semantics`. It prohibits metric recitation, ungrounded company-benefit claims, and trading advice.

## 002050 Pilot

The 002050 pilot uses an `advanced_manufacturing_growth` scenario. It preserves the old snapshot distinction between base auto parts and the robotics gap. P1 robotics and new-business conclusions remain `not_assessable` where evidence is missing.

Auto thermal content remains partial. Customer concentration, capex-to-revenue, R&D conversion, valuation, and quality questions are surfaced. The key conflict is a verifiable base business versus new-business and growth-evidence gaps. No robotics realized revenue is asserted.

## 600406 Regression

The 600406 regression uses a `stable_growth` scenario. It does not inherit the 002050 robotics or advanced-manufacturing template and contains no hard-coded grid or Guodian NARI conclusion.

Stable-growth categories are checked, but the `stable_growth` label itself is not treated as operating-steadiness evidence. The pack emits no trading advice.

## Test Result

Targeted tests completed with `147 passed in 219.90s`. Related tests were not executed under a tiered-testing policy because this was an isolated in-memory module and did not modify wrappers, providers, Report V1, HTML, or LLM handoff. Live smoke was not executed because the stage forbids live LLM, DeepSeek, Tushare, provider, and network use.

## Safety And Boundary

This stage performed no DeepSeek live call, no LLM call, no Tushare live call, no network call, no token or env access, no output artifact read, no fixture modification, no accepted manifest modification, no Report V1 work, no HTML work, no Markdown/JSON runtime report artifact generation, no `official_metric_fact` work, no `provider_official_conflict` work, and no reconciliation work.

The pack contains no raw provider bundle, candidate item, backend trace, token, or key. Prompt boundaries block trading advice in English and Chinese, responsibility-shifting phrasing, and proxy overread.

## Tiered Testing Policy Note

For an isolated in-memory module, targeted tests are sufficient for acceptance. Related tests should be run when wrappers, providers, Report V1, HTML, or LLM handoff changes. Larger regression belongs to release or integration gates. This saves time and tokens without reducing safety for this stage.

## Untouched Restricted Areas

This stage did not touch existing Research Intelligence modules, wrappers, providers, LLM smoke code, LLM handoff code, professional quality code, ticker-only quality evaluation code, Report V1, HTML, schemas, validators, `__init__`, `output`, fixtures, manifests, `.local_experiments`, token or env files, live integrations, `official_metric_fact`, `provider_official_conflict`, reconciliation logic, or trading-advice paths.

## Current Remaining Untracked Items

Known unrelated untracked items remain out of scope:

- `.local_experiments/`
- unrelated mojibake files
- unrelated examples file

## Current Stage Conclusion

The implementation is accepted with no blocker. This summary is docs-only. The completed work provides the investment director context pack, Missing Coverage Map, source tier and viewpoint context, director framework alignment, and frontstage visualization requirements. It improves the materials that a later DeepSeek stage can see, while still not being DeepSeek live integration, an LLM renderer, Report V1, HTML, official verification, or reconciliation.

No trading advice is produced. The next stage should reassess before implementation. Reasonable next-stage candidates are DeepSeek Prompt Repair + Re-run Human Review, then Controlled Real LLM Renderer Adapter Minimal Integration if DeepSeek quality improves. The project should not directly enter Report V1/HTML work and should not productize shallow DeepSeek output.
