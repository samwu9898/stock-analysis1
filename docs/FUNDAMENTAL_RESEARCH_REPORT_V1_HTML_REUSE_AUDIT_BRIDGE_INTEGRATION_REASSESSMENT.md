# Fundamental Research Report V1 / HTML Reuse Audit + Bridge Integration Reassessment

Date: 2026-06-02

Status: docs-only reassessment. No production code, tests, fixtures, output
artifacts, accepted manifest, token files, or provider/runtime artifacts are
modified by this stage.

## 1. Stage name

Research Report V1 / HTML Reuse Audit + Bridge Integration Reassessment

## 2. Baseline commits

- Latest completed stage: User-facing Analysis Brief Draft acceptance summary
  commit `e1712d1`.
- Prior implementation commit: `be197e5`.
- Old Research Report V1 accepted baseline is recorded in
  `docs/FUNDAMENTAL_RESEARCH_REPORT_V1_RELEASE_NOTE.md` with the first accepted
  `600406` Research Report V1 JSON runtime artifact documented as an ignored
  output artifact.
- Markdown presentation profiles are accepted for `600406`, `002371`, and
  `002050` in
  `docs/FUNDAMENTAL_RESEARCH_REPORT_V1_MARKDOWN_PROFILE_ACCEPTANCE_SUMMARY.md`.
- HTML presentation-layer baseline is accepted for `600406`, `002371`, and
  `002050` in
  `docs/FUNDAMENTAL_RESEARCH_REPORT_V1_HTML_ACCEPTANCE_SUMMARY.md`.
- This reassessment only references those baselines. It does not update,
  regenerate, stage, or validate any runtime artifact.

## 3. Why this stage exists

The old chain already has Research Report V1, Markdown presentation profiles,
and an HTML presentation layer. The new chain already has Evidence Chain ->
Analysis Brief Bridge Draft.

The current product risk is that the project could accidentally grow two
parallel user-facing report systems:

- Research Report V1 / Markdown / HTML as the older report product line.
- Evidence Chain -> `user_facing_analysis_brief.v1` as a newer compact user
  draft.

This stage exists to decide reuse and bridge boundaries before any new
production code. It is not a report rewrite, not a renderer rewrite, not a
public API implementation, not metric extraction, and not a formal Research
Pack stage.

## 4. Highest product rule

证据在后台，分析在前台。

- Backend evidence is for model grounding / confidence / audit.
- User-facing product focuses on business logic, financial interpretation,
  industry/macro context, risks, data gaps that matter, tracking indicators, and
  conclusion boundaries.
- `page`, `snippet`, `source_url`, `sha256`, `cache_path`, anchor map, and
  provider queue must not be default user-visible content.

## 5. Existing Research Report V1 summary

Source files inspected:

- `src/fundamental_skill/research_report/research_report_v1.py`
- `src/fundamental_skill/research_report/__init__.py`
- `src/fundamental_skill/research_report/research_report_v1_presentation.py`

Tests/docs inspected:

- `tests/test_research_report_v1.py`
- `tests/test_research_report_v1_presentation.py`
- `docs/FUNDAMENTAL_RESEARCH_REPORT_V1_RELEASE_NOTE.md`
- `docs/FUNDAMENTAL_RESEARCH_REPORT_V1_DESIGN.md`
- `docs/FUNDAMENTAL_RESEARCH_REPORT_V1_PRESENTATION_PROFILE_DESIGN.md`
- `docs/FUNDAMENTAL_RESEARCH_REPORT_V1_MARKDOWN_PROFILE_ACCEPTANCE_SUMMARY.md`

Input assumptions:

- Required input is explicit in-memory payloads: `code`,
  `fundamental_payloads`, and `evidence_pack_payloads`.
- Optional inputs are `fact_candidates`, `review_decisions`,
  `score_explainability`, and `diff_report`.
- Inputs are already materialized local artifacts. V1 does not fetch, read
  provider tokens, call providers, contact network, parse PDFs, or promote
  fixtures.
- The builder consumes dict payloads, not `user_facing_analysis_brief.v1` and
  not locator result details.

Output sections:

- `data_quality_assessment`
- `executive_summary`
- `macro_context`
- `industry_context`
- `company_fundamentals`
- `opportunity_analysis`
- `risk_analysis`
- `evidence_gaps`
- `rebuttal_conditions`
- `follow_up_variables`
- `source_artifact_refs`

Evidence labels:

- `verified_fact`
- `auto_accepted_candidate`
- `manual_review_required`
- `unsupported_assumption`
- `coverage_caveat`
- `forward_tracking_variable`

Guardrails:

- Every key judgement must carry an allowed evidence label.
- `verified_fact` requires an explicit reviewed source.
- Candidate rows, review decisions, P1.1 proxy evidence, provider diffs, and
  industry narratives do not become reviewed facts.
- The builder rejects forbidden investment-action fields, secret-like payloads,
  token-like values, local secret paths, MCP URLs, `.env` references, and path
  traversal.
- The module has no provider, network, env, scoring, readiness, or validator
  runtime import.

Known limitations:

- Research Report V1 remains a V1 draft baseline, not a final formal report.
- The original accepted JSON baseline and later Markdown/HTML baselines are
  sample-limited.
- Live provider report generation and official disclosure evidence integration
  remain later work.
- Official table facts, official candidate payloads, and candidate source
  bridge outputs are not yet Report V1 evidence by default.
- `user_facing_analysis_brief.v1` cannot be passed directly into the existing
  builder without an adapter design.

Whether it is still useful:

Yes. Research Report V1 already owns the durable report skeleton, evidence
label discipline, caveat model, non-trading boundary, and user-facing report
shape. It should remain the target report product line rather than being
replaced.

What should be reused:

- Section taxonomy and conclusion-boundary language.
- Evidence label model, with a documented translation from analysis labels.
- Data-quality caveat discipline.
- Follow-up variables / rebuttal conditions as the natural destination for
  tracking indicators and cannot-conclude items.
- Markdown presentation profiles and their cross-industry isolation rules.

What should not be changed yet:

- Do not modify the Report V1 builder.
- Do not add `user_facing_analysis_brief.v1` as a direct builder input now.
- Do not reinterpret locator status as `verified_fact`.
- Do not wire official candidate payloads or metric extraction into Report V1
  in this stage.

## 6. Existing HTML presentation layer summary

Source/docs inspected:

- `src/fundamental_skill/research_report/research_report_v1_html.py`
- `tests/test_research_report_v1_html.py`
- `docs/FUNDAMENTAL_RESEARCH_REPORT_V1_HTML_PRESENTATION_DESIGN.md`
- `docs/FUNDAMENTAL_RESEARCH_REPORT_V1_HTML_ACCEPTANCE_SUMMARY.md`
- Light contract check:
  `src/fundamental_skill/ai_analyst/html_report_schema.py`,
  `src/fundamental_skill/ai_analyst/html_report_renderer.py`,
  `tests/test_html_report_schema.py`,
  `tests/test_html_report_renderer.py`,
  `tests/test_html_report_runner.py`,
  `tests/test_html_report_prompt_builder.py`,
  `docs/FUNDAMENTAL_HTML_REPORT_GENERATOR_V1_SPEC.md`, and
  `docs/skills/FUNDAMENTAL_HTML_REPORT_GENERATION_SKILL.md`.

HTML role:

- The Research Report V1 HTML layer is a presentation layer, not an analysis
  layer.
- It consumes accepted Research Report V1 Markdown as the primary narrative
  source.
- It may consume the structured Research Report V1 JSON only for display
  metadata, evidence labels, caveats, and source artifact references.

Whether HTML re-analyzes:

No. Tests and design docs explicitly preserve Markdown conclusions and prevent
the optional report dict from rewriting the narrative.

Expected input shape:

- Required: non-empty Research Report V1 Markdown.
- Optional: Research Report V1 structured payload.
- Not accepted as a direct primary input today:
  `user_facing_analysis_brief.v1`, raw provider artifacts, locator details,
  provider queues, PDF bytes, or official metric facts.

Accepted sample coverage:

- `600406` / `stable_growth_grid_equipment`
- `002371` / `semiconductor_equipment_cycle`
- `002050` / `advanced_manufacturing_thermal_management`

Known limitations:

- The Research Report V1 HTML layer is static V1 presentation, not Dashboard.
- It is not a Research Pack assembler.
- It depends on Markdown profile output and cannot decide new report semantics.
- The separate `fundamental_html_report.v1` HTML generator chain consumes a
  different structured report JSON. It is useful design context, but it is not
  the old Research Report V1 HTML baseline and should not become a shortcut
  bridge target for this stage.

Whether it should be reused later:

Yes, after compatibility planning. The right reuse path is:

```text
Evidence Chain -> Analysis Brief / compatibility context
-> future Report V1-compatible payload or Markdown
-> existing Research Report V1 HTML presentation layer
```

Why this stage does not modify HTML:

There is no accepted adapter shape yet. Modifying HTML first would either force
HTML to become an analysis layer or create a parallel `Analysis Brief HTML`
product beside Report V1 HTML. Both violate the reuse objective.

## 7. New Evidence Chain / Analysis Brief summary

Inspected files/docs:

- `src/fundamental_skill/research_planning/user_facing_analysis_brief.py`
- `tests/test_user_facing_analysis_brief.py`
- `tests/test_user_facing_analysis_brief_safety.py`
- `docs/FUNDAMENTAL_USER_FACING_ANALYSIS_BRIEF_DRAFT_THIN_SLICE_ACCEPTANCE_SUMMARY.md`
- `src/fundamental_skill/research_planning/live_evidence_research_pack_orchestration_entry.py`
- `src/fundamental_skill/research_planning/live_evidence_aware_research_pack_vertical_slice.py`
- `src/fundamental_skill/data_verification/official_artifact_evidence_locator.py`
- `docs/FUNDAMENTAL_LIVE_EVIDENCE_RESEARCH_PACK_ORCHESTRATION_ENTRY_THIN_SLICE_ACCEPTANCE_SUMMARY.md`
- `docs/FUNDAMENTAL_600406_LIVE_EVIDENCE_AWARE_RESEARCH_PACK_VERTICAL_SLICE_ACCEPTANCE_SUMMARY.md`
- `docs/FUNDAMENTAL_OFFICIAL_ARTIFACT_EVIDENCE_LOCATOR_THIN_SLICE_ACCEPTANCE_SUMMARY.md`

`user_facing_analysis_brief.v1` role:

- A user-facing analysis draft bridge.
- It turns an already-built orchestration result, and optionally a locator
  result, into fixed user-readable sections.
- It is not Report V1, not formal Research Pack, not HTML, and not a final
  report artifact.

`live_evidence_research_pack_orchestration_result.v1` role:

- A callable wrapper around explicit validated components.
- It returns readiness, vertical slice, markdown preview, evidence rollup, and
  source component summary.
- It does not fetch live data, read files, parse PDFs, write artifacts, or
  create analyst conclusions.

`official_artifact_evidence_locator.v1` role:

- Locator-only metadata from cached official PDF text layers.
- It can locate title, company, stock code, report period, section headings,
  and safe keyword hits.
- It is not metric extraction, not table extraction, not reconciliation, not
  `official_metric_fact`, and not `official_verified`.

User-facing parts:

- `subject_summary`
- `current_judgment_boundary`
- `business_logic`
- `financial_interpretation`
- `industry_macro_context`
- `risk_points`
- `data_gaps_that_matter`
- `tracking_indicators`
- `cannot_conclude_yet`
- `markdown_preview` generated only from those user-visible sections.

Backend/model-facing parts:

- `backend_grounding_summary`
- `source_component_summary`
- Evidence rollup counts and availability flags.
- Locator availability.
- Anchor/artifact/provider candidate status.
- Component schema versions.

Why it is not a Report V1 replacement:

- Its section taxonomy is compact and boundary-oriented; it does not contain
  Report V1's full macro, industry, company fundamentals, opportunities,
  risks, rebuttal, follow-up, and source artifact structure.
- Its labels are analysis confidence labels, not Report V1 evidence labels.
- It intentionally hides locator/page/snippet/source details from the user
  view.
- It has no Report V1 Markdown profile selection, no Research Report V1 HTML
  contract, and no formal artifact writer.

## 8. Mapping matrix

| New Evidence / Brief Field | Existing Research Report V1 Section Candidate | HTML Presentation Implication | User-visible by default? | Backend-only? | Integration decision | Caveats |
| --- | --- | --- | --- | --- | --- | --- |
| subject / identity | `code`, `company_fundamentals.stock`, `executive_summary` | Header/title and quick-read identity | Yes | No | Map directly after identity consistency checks | Company name hints remain hints unless reviewed source supports them. |
| current judgment boundary | `executive_summary`, `data_quality_assessment`, `evidence_gaps` | Quick-read caveat and opening boundary | Yes | No | Reuse as executive boundary input | Must not become strong conclusion when official verification count is zero. |
| business logic | `company_fundamentals`, `company_fundamentals.business_composition`, `industry_context` | Research body company/business section | Yes | No | Map as caveated business-analysis context | Do not infer main business, competitive position, customer structure, or segment realization from status only. |
| financial interpretation | `company_fundamentals.financial_metrics`, `data_quality_assessment`, `evidence_gaps` | Research body financial section; quick-read data-quality card | Yes | No | Map to candidate/caveat narrative only | No numeric extraction; provider candidate is pending evidence unless Report V1-compatible candidates exist. |
| industry / macro context | `macro_context`, `industry_context`, `opportunity_analysis` | Research body macro/industry section | Yes | No | Reuse as framework context | Must remain transmission framework, not industry prosperity or company benefit claim. |
| risk points | `risk_analysis`, `evidence_gaps`, `rebuttal_conditions` | Risk cards / risk body | Yes | No | Map to risk-analysis prompts | Use conditional language and evidence labels. |
| data gaps that matter | `evidence_gaps`, `data_quality_assessment` | Evidence-gap card and appendix caveats | Yes | No | Map directly | Keep only user-relevant gaps; raw locator gaps stay backend. |
| tracking indicators | `follow_up_variables`, `rebuttal_conditions` | Checklist / follow-up panel | Yes | No | Map directly with `forward_tracking_variable`-like semantics | Must not become trading triggers or price/position rules. |
| cannot conclude yet | `evidence_gaps`, `rebuttal_conditions`, safety boundary | Quick-read caveat and final boundary | Yes | No | Map directly as conclusion boundary | Must not be softened away by HTML layout. |
| backend grounding summary | `data_quality_assessment`, `source_artifact_refs`, possible technical appendix | Appendix or hidden audit summary only | No | Yes | Use as model-context / audit signal, not main view | Only aggregate availability/count/status may influence labels. No raw trace. |
| evidence labels | Report V1 evidence labels | Badges / label definitions | Yes, after translation | No | Translate labels through adapter plan | `较可靠` is not automatically `verified_fact`; it requires reviewed source. |
| locator availability | `data_quality_assessment` / source metadata only | Optional appendix summary, not main narrative | No | Yes | Backend grounding only | `locator_available` or locator hit is not official verification. |
| official anchor / artifact status | `data_quality_assessment`, future source refs | Optional appendix summary and caveat count | No | Yes | Backend grounding until accepted L1 integration design | `official_anchor_matched` and `artifact_cached` do not become `verified_fact`. |
| provider candidate status | `auto_accepted_core_fields`, `manual_review_required_fields`, `data_quality_assessment` | Candidate/caveat labels visible where material | Yes, summarized | Partly | Reuse only through candidate/caveat semantics | Provider candidate cannot become official value or reconciliation result. |

Suggested analysis-label translation boundary:

| Analysis Brief label | Possible Report V1 label | Rule |
| --- | --- | --- |
| `较可靠` | `verified_fact` only when reviewed source exists; otherwise not allowed | `official_verified_count > 0` is necessary but not sufficient. |
| `待核验` | `manual_review_required` or `auto_accepted_candidate` | Depends on whether the future adapter receives candidate-level field evidence. |
| `数据缺口` | `coverage_caveat` | Default for missing or insufficient evidence. |
| `推理` | `unsupported_assumption` | Use for framework or hypothesis language. |
| `不可判断` | `coverage_caveat` / `manual_review_required` | Use for conclusion boundaries and blocked claims. |

## 9. Integration options

| Option | User value | Engineering risk | Duplication risk | Fit with handbook | Backend evidence exposure risk | Recommendation |
| --- | --- | --- | --- | --- | --- | --- |
| Option A: `user_facing_analysis_brief` as independent compact brief | Good for immediate lightweight reading and status explanation | Low short-term, medium long-term | High if treated as product report | Partial fit; useful as bridge but not final report | Low if current validators remain | Not recommended as the main product line. Keep only as bridge draft / diagnostic user preview. |
| Option B: `user_facing_analysis_brief` as preface / executive brief for Report V1 | Strong user value because it puts conclusion boundary before long report | Medium | Medium if preface diverges from Report V1 labels | Good if generated from the same Report V1-compatible context | Medium unless locator fields remain hidden | Future candidate after adapter planning, not now. |
| Option C: `user_facing_analysis_brief` as model-context adapter feeding future Report V1 integration | High structural value; prevents parallel report systems | Medium but controllable | Low | Best fit with evidence-backstage / analysis-frontstage rule | Low if adapter explicitly filters backend-only fields | Recommended next direction, but as planning first. |
| Option D: direct Report V1 integration now | Potentially high if it worked | High | High | Poor fit without accepted mapping | High; easy to expose locator/source internals or promote candidates | Not recommended. |
| Option E: direct HTML integration now | Superficially quick | High | Very high | Poor; forces HTML into analysis or new brief renderer | High | Not recommended. |

## 10. Recommended next slice

Recommended next stage:

```text
Analysis Brief -> Report V1 Compatibility Adapter Planning
```

Recommended nature:

- docs-only / planning-first.
- No production code implementation yet.
- No tests change unless a later implementation stage is approved.

Why this is the best next slice:

- It keeps Research Report V1 as the target product shape.
- It prevents `user_facing_analysis_brief.v1` from becoming a second report
  product.
- It defines exactly which fields can become Report V1-compatible context and
  which fields must be dropped or held as backend grounding.
- It creates a safer basis for a later bridge adapter or public wrapper.

What the next stage should do:

- Define a compatibility adapter contract, but not implement it.
- Define allowed source inputs:
  `user_facing_analysis_brief.v1`,
  `live_evidence_research_pack_orchestration_result.v1`, and optionally
  sanitized `backend_grounding_summary`.
- Define output as a future in-memory compatibility payload, not a report
  artifact.
- Define analysis-label -> evidence-label translation.
- Define backend-only field drop rules.
- Define how adapter output could later feed Report V1 preface/context without
  changing HTML first.

What the next stage should not do:

- Do not modify Research Report V1.
- Do not modify HTML.
- Do not create a public wrapper first.
- Do not do metric extraction first.
- Do not parse or read PDFs.
- Do not generate report artifacts.
- Do not create official metric facts.
- Do not reconcile provider-vs-official values.

Public wrapper decision:

- Do not build the public wrapper first if it would expose `Analysis Brief` as
  a standalone final product.
- A later wrapper with brief output only can be acceptable after the adapter
  planning document defines the bridge boundary and explicitly states that the
  wrapper is not Report V1 / HTML replacement.

Bridge adapter decision:

- Do bridge adapter planning next.
- Do not implement the adapter until the mapping contract and test acceptance
  shape are accepted.

Metric extraction decision:

- Do not start metric extraction next.
- Metric extraction should wait until official evidence -> candidate -> review
  -> Report V1 evidence flow is separately accepted.

Report V1 / HTML modification decision:

- Do not modify Report V1 or HTML in the next slice.
- Reuse them later through an accepted compatibility contract.

## 11. Explicit non-goals

- no production code change
- no tests change
- no Report V1 modification
- no HTML modification
- no output runtime artifact read/write
- no provider/live/network
- no PDF read/parse
- no official_metric_fact
- no reconciliation
- no trading advice
- no target price
- no position sizing
- no technical signal
- no accepted manifest read/write
- no fixture read/write
- no `.local_experiments` read/write
- no `tushare_token.txt` or `.env` read

## 12. Final recommendation for 主策划

Recommended next stage name:

```text
Analysis Brief -> Report V1 Compatibility Adapter Planning
```

Recommended implementation status:

- Not implementation yet.
- Keep the next slice docs-only unless 主策划 explicitly approves a following
  implementation stage.

Recommended expected file:

```text
docs/FUNDAMENTAL_ANALYSIS_BRIEF_TO_REPORT_V1_COMPATIBILITY_ADAPTER_PLANNING.md
```

Recommended risks to manage:

- Parallel report system risk if `Analysis Brief` becomes a standalone final
  product.
- Evidence-label mismatch risk between Analysis Brief labels and Report V1
  labels.
- Backend evidence leakage risk from locator/source fields.
- Premature public API risk if wrapper shape freezes before adapter planning.
- Premature metric extraction risk if official candidate evidence bypasses
  review and Report V1 boundaries.

Gemini / DeepSeek / Kimi audit:

- Not required to complete this docs-only reassessment.
- Optional before adapter implementation if 主策划 wants an external mapping
  audit for label translation, backend-only filtering, and product-boundary
  clarity.

Need 主策划 confirmation:

- Yes before any production implementation, public wrapper, bridge adapter, or
  metric extraction.
- This docs-only reassessment itself is ready for docs-only acceptance review.
