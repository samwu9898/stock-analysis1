# Analysis Brief to Report V1 Compatibility Adapter Planning

Date: 2026-06-02

Status: docs-only planning. This stage does not implement an adapter, does not
modify production code, does not modify tests, does not modify Research Report
V1, does not modify the HTML renderer, does not generate runtime artifacts, and
does not define a public API.

## 1. Stage name

Analysis Brief -> Report V1 Compatibility Adapter Planning

## 2. Baseline commits

- Latest completed reassessment commit:
  `54534780ca0e61b2e39df1f3befa2f4ba0c771e1`
  (`docs: reassess report v1 html bridge reuse`).
- User-facing Analysis Brief implementation commit:
  `be197e59ebc020999c7504a035f7714de7e68868`.
- User-facing Analysis Brief acceptance summary commit:
  `e1712d1875c755c427dc60ac367f803cdca5f504`.
- Old Research Report V1 accepted baseline is recorded in
  `docs/FUNDAMENTAL_RESEARCH_REPORT_V1_RELEASE_NOTE.md`: Research Report V1 was
  accepted and baseline-frozen on 2026-05-27, with the first accepted `600406`
  JSON runtime artifact documented as an ignored output artifact.
- Old Markdown presentation baselines are recorded in
  `docs/FUNDAMENTAL_RESEARCH_REPORT_V1_MARKDOWN_PROFILE_ACCEPTANCE_SUMMARY.md`:
  `600406`, `002371`, and `002050` Markdown reports were accepted as V1 draft
  narrative profiles.
- Old HTML presentation baselines are recorded in
  `docs/FUNDAMENTAL_RESEARCH_REPORT_V1_HTML_ACCEPTANCE_SUMMARY.md`: `600406`,
  `002371`, and `002050` HTML reports were accepted, and the HTML presentation
  layer baseline was frozen.
- This planning stage references those baselines only. It does not read,
  regenerate, stage, or validate any runtime artifact.

## 3. Why this stage exists

Old Research Report V1 / HTML remains the target report product line. New
`user_facing_analysis_brief.v1` is a bridge / compact analysis draft generated
from the Evidence Chain, not a replacement report system.

The current project risk is product duplication: if Analysis Brief directly
feeds users as a final report while Report V1 / HTML continues separately, the
project will grow two inconsistent report systems with different section
taxonomies, evidence labels, and output contracts.

This stage exists because the project cannot safely move directly to adapter
implementation yet. The next safe step is to define the compatibility adapter
contract: which Analysis Brief fields may become Report V1-compatible context,
which backend grounding fields must stay out of the user-facing report, how
labels translate, and what future tests must fail closed on.

The goal is to avoid a parallel report system by making Analysis Brief a bridge
into the Report V1 product shape.

## 4. Highest product rule

证据在后台，分析在前台。

- Backend evidence / locator / `sha256` / `source_url` / page / snippet /
  `cache_path` do not enter the user-facing main report by default.
- The adapter may only convert analysis-layer content and safe evidence status
  summaries into Report V1-compatible context.
- Locator/source trace must not be directly inserted into the Report V1
  user-facing main view.
- Backend trace may support confidence, coverage, and audit decisions, but the
  user-facing narrative should remain business logic, financial interpretation,
  industry/macro context, risk, gaps, follow-up variables, and conclusion
  boundaries.

## 5. Source input contract

Future adapter required input:

- `user_facing_analysis_brief.v1`

Future adapter optional inputs:

- `live_evidence_research_pack_orchestration_result.v1`
- sanitized `backend_grounding_summary`
- optional `official_artifact_evidence_locator.v1`, only for
  availability/count/confidence hints; raw locator hits must not be passed
  through.

The adapter must reject or ignore these source shapes:

- raw Tushare payloads
- raw provider queue
- raw HTTP response
- PDF bytes
- cache file content
- arbitrary URL
- output artifact path
- live module handles or callbacks

The adapter must not call live modules. It must operate on explicit in-memory
objects supplied by upstream code.

## 6. Future output contract

Recommended future output schema name:

- `analysis_brief_report_v1_compatibility_payload.v1`

The adapter output must be an in-memory compatibility payload. It is not a
Report V1 artifact, not Markdown, not HTML, and not a runtime artifact.

The adapter must not:

- write `output`;
- generate HTML;
- call the Report V1 builder;
- generate Markdown/HTML runtime artifacts;
- mutate upstream inputs;
- become a third report product.

The payload exists only as safe context for a future Report V1 integration.

Recommended payload fields:

- `schema_version`
- `subject_context`
- `executive_boundary_context`
- `business_context`
- `financial_context`
- `industry_macro_context`
- `risk_context`
- `evidence_gap_context`
- `follow_up_context`
- `label_translation_summary`
- `backend_grounding_summary_sanitized`
- `blocked_reasons`
- `caveats`
- `not_for_trading_advice`

## 7. Field mapping plan

| Analysis Brief Field | Report V1 Candidate Section | Adapter Treatment | User-visible? | Backend-only? | Evidence label translation | Drop / Keep / Transform | Caveats |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `subject_summary` | `executive_summary`, `company_fundamentals` | Convert stock identity and brief subject into `subject_context`. | Yes | No | `待核验` -> `manual_review_required` unless explicit reviewed source exists. | Transform | Company name hint remains a hint unless future reviewed identity input is explicit. |
| `current_judgment_boundary` | `executive_summary`, `data_quality_assessment`, `evidence_gaps` | Convert conclusion boundary into opening caveat / data quality context. | Yes | No | `较可靠` cannot become `verified_fact`; default to `manual_review_required` or `coverage_caveat`. | Transform | Must preserve "can analyze, cannot formally conclude" boundary. |
| `business_logic` | `company_fundamentals`, `industry_context`, `opportunity_analysis` | Convert analysis points into caveated business context. | Yes | No | `数据缺口` -> `coverage_caveat`; `推理` -> `unsupported_assumption`; candidate support -> `manual_review_required`. | Transform | Do not infer main business, competitive position, segment realization, customer structure, or benefit transmission from locator/provider status. |
| `financial_interpretation` | `company_fundamentals`, `data_quality_assessment`, `evidence_gaps` | Convert into financial interpretation context without extracting metrics. | Yes | No | Provider candidate -> `auto_accepted_candidate` only if future candidate-level evidence is supplied; otherwise `manual_review_required`. | Transform | No metric extraction, no official_metric_fact, no provider-vs-official reconciliation. |
| `industry_macro_context` | `macro_context`, `industry_context`, `opportunity_analysis` | Convert framework language into macro / industry context. | Yes | No | `推理` -> `unsupported_assumption`; forward-looking variables -> `forward_tracking_variable`. | Transform | Must remain transmission framework, not prosperity forecast or company benefit claim. |
| `risk_points` | `risk_analysis`, `evidence_gaps`, `rebuttal_conditions` | Convert analysis/data/checking risks into risk context. | Yes | No | `数据缺口` -> `coverage_caveat`; `不可判断` -> `coverage_caveat` or `manual_review_required`. | Transform | Risks must remain evidence-bounded and non-trading. |
| `data_gaps_that_matter` | `evidence_gaps`, `data_quality_assessment` | Map user-relevant data gaps directly. | Yes | No | `数据缺口` -> `coverage_caveat`. | Keep / Transform | Keep only gaps that affect user analysis; raw locator gaps remain backend-only. |
| `tracking_indicators` | `follow_up_variables`, `rebuttal_conditions` | Map names and follow-up variables into tracking context. | Yes | No | Tracking variables -> `forward_tracking_variable`. | Transform | Must not become trading triggers, target prices, position rules, or technical signals. |
| `cannot_conclude_yet` | `evidence_gaps`, `rebuttal_conditions`, `data_quality_assessment` | Preserve blocked conclusions and unsupported areas. | Yes | No | `不可判断` -> `coverage_caveat`, `manual_review_required`, or rebuttal condition. | Keep / Transform | Must not be softened into a stronger conclusion by later Report V1 / HTML rendering. |
| `backend_grounding_summary` | `data_quality_assessment`, `source_artifact_refs` | Sanitize to summary flags/counts only. | No by default | Yes | Availability flags do not translate to `verified_fact`; counts only affect caveats. | Transform / Drop raw detail | Only aggregate availability/count/status can be retained. No raw trace. |
| `analysis_labels_legend` | label documentation / `label_translation_summary` | Convert into translation summary for adapter output. | Yes as label explanation | No | Map Analysis Brief labels through explicit translation table. | Transform | Report V1 labels remain authoritative after translation. |
| `markdown_preview` | None by default; possible human preview only | Do not use as adapter source of truth. | No by default | No | No label inference from rendered markdown text. | Drop | Avoid parsing generated Markdown; use structured sections instead. |

Report V1 candidate sections considered by this plan:

- `executive_summary`
- `data_quality_assessment`
- `macro_context`
- `industry_context`
- `company_fundamentals`
- `opportunity_analysis`
- `risk_analysis`
- `evidence_gaps`
- `rebuttal_conditions`
- `follow_up_variables`
- `source_artifact_refs`

## 8. Label translation plan

Analysis Brief labels:

- `较可靠`
- `待核验`
- `数据缺口`
- `推理`
- `不可判断`

Report V1 labels:

- `verified_fact`
- `auto_accepted_candidate`
- `manual_review_required`
- `unsupported_assumption`
- `coverage_caveat`
- `forward_tracking_variable`

Translation rules:

| Analysis Brief Label / Signal | Report V1 Label Candidate | Rule |
| --- | --- | --- |
| `较可靠` | `verified_fact` only when explicit reviewed source / official verified input is supplied; otherwise `manual_review_required` or `coverage_caveat` | `较可靠` must not automatically equal `verified_fact`. |
| `待核验` | `manual_review_required` or `auto_accepted_candidate` | Default is `manual_review_required`; `auto_accepted_candidate` requires candidate-level future adapter input. |
| `数据缺口` | `coverage_caveat` | Use for missing coverage, insufficient source support, or analysis-limiting gaps. |
| `推理` | `unsupported_assumption` | Use for framework, hypothesis, or unsupported interpretation language. |
| `不可判断` | `coverage_caveat`, `manual_review_required`, or rebuttal condition | Use for blocked conclusions and conditions that would change future judgement. |
| `tracking_indicators` | `forward_tracking_variable` | Follow-up variables are closer to forward tracking than to factual evidence. |
| `locator_available` / `artifact_cached` / `anchor_matched` | Not `verified_fact` | These are availability/support signals only. |

`verified_fact` can only come from explicit reviewed source / official verified
input. Locator availability, artifact cache status, anchor match, provider
candidate status, and Analysis Brief "较可靠" status are never sufficient by
themselves.

## 9. Backend-only field drop rules

Future adapter must drop, or only aggregate, these fields and data shapes:

- `page_number`
- `snippet`
- `source_url`
- `sha256`
- `cache_path`
- full locator hits
- full provider queue
- full anchor map
- full official metadata
- raw PDF text
- output artifact paths
- fixture paths
- token-like strings

Allowed sanitized summary fields:

- `audit_trace_available`
- `official_anchor_available`
- `artifact_cached_available`
- `locator_available`
- `provider_candidate_present`
- `pending_verification_count`
- `official_verified_count`
- `data_gap_count`

Sanitized summary fields may influence caveats, blocked reasons, or label
translation decisions. They must not appear as raw user-facing source trace,
and they must not promote any claim to `verified_fact` without an explicit
reviewed source / official verified input.

## 10. Product shape decision

- `user_facing_analysis_brief.v1` is not the final report.
- Research Report V1 remains the target long-report structure.
- HTML remains the presentation layer.
- `analysis_brief_report_v1_compatibility_payload.v1` is a bridge, not a third
  report system.
- Later Public API design should wait until adapter planning is accepted. It
  may prioritize compact brief output or Report V1 output, but it should not
  freeze a public wrapper before this compatibility boundary is accepted.

## 11. Future implementation plan

If this planning is accepted, the next stage may enter minimal adapter
implementation.

Future production expected file:

- `src/fundamental_skill/research_planning/analysis_brief_report_v1_adapter.py`

Future tests expected:

- `tests/test_analysis_brief_report_v1_adapter.py`
- `tests/test_analysis_brief_report_v1_adapter_safety.py`

Implementation constraints:

- do not modify the Research Report V1 builder;
- do not modify the HTML renderer;
- do not write `output`;
- do not generate a report artifact;
- only generate an in-memory compatibility payload;
- if modifying Report V1 becomes necessary, open a separate reassessment first.

## 12. Future adapter acceptance criteria

Future adapter acceptance should require:

- valid `user_facing_analysis_brief.v1` builds a compatibility payload;
- all user-visible sections are mapped or intentionally dropped;
- backend-only fields are dropped;
- no `page` / `snippet` / `source_url` / `sha256` / `cache_path` leak;
- label translation is correct;
- no `verified_fact` without explicit official / reviewed source;
- no Report V1 artifact is generated;
- no HTML is generated;
- no `output` / fixtures / manifest write;
- no trading advice;
- no token leak;
- no input mutation;
- non-`600406` sample passes;
- missing locator still passes;
- backend grounding summary remains sanitized.

Specific fail-closed tests should cover:

- unexpected raw input keys such as `pdf_bytes`, `raw_provider_queue`,
  `raw_http_response`, `arbitrary_url`, and `output_artifact_path`;
- backend-only trace keys nested inside any input object;
- label escalation attempts from `较可靠`, `locator_available`,
  `artifact_cached`, or `anchor_matched` to `verified_fact`;
- markdown-preview parsing attempts;
- token-like strings and local secret path strings;
- accidental calls to Report V1 writer, HTML writer, output writer, fixture
  writer, or manifest writer.

## 13. Explicit non-goals

- no production code in this stage
- no tests in this stage
- no adapter implementation
- no Report V1 modification
- no HTML modification
- no public wrapper
- no metric extraction
- no official_metric_fact
- no reconciliation
- no output artifact read/write
- no provider/live/network
- no PDF read/parse
- no trading advice

## 14. Audit decision

Docs-only planning does not require Gemini / DeepSeek / Kimi audit to complete.
The document is suitable for docs-only acceptance review by the project owner.

Future adapter implementation should be reviewed by Gemini / DeepSeek / Kimi, or
an equivalent third-party reviewer, before acceptance if the implementation
touches label translation, backend-only filtering, Report V1 integration, or
public API shape.

Recommended audit focus:

- label translation;
- backend-only filtering;
- no Report V1 replacement;
- no evidence leakage;
- no `verified_fact` promotion from locator/cache/anchor/provider status;
- no output / fixture / manifest writes;
- no trading advice.

## 15. Final recommendation

- Recommend entering docs-only acceptance review for this planning document.
- Recommend next stage can be minimal adapter implementation only after this
  planning is accepted by 主策划.
- Implementation still requires 主策划 approval before production code changes.
- Do not build the public wrapper first.
- Do not start metric extraction first.
- Do not modify Report V1 / HTML in the next stage.
- Keep the product line direction:

```text
Evidence Chain -> user_facing_analysis_brief.v1
-> analysis_brief_report_v1_compatibility_payload.v1
-> future Report V1 integration
-> existing Report V1 HTML presentation layer
```
