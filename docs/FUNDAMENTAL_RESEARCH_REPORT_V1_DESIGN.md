# Fundamental Research Report V1 Design

Date: 2026-05-28

Stage: Fundamental Skill Research Report V1 Design, Cross-Industry Markdown
Profile Acceptance, HTML Presentation Layer Design, and Three-Sample HTML
Acceptance, followed by User Invocation / Report Orchestration Design.

Status: design accepted, implementation accepted, Research Report V1 baseline
frozen, cross-industry Markdown profile validation accepted for `600406`,
`002371`, and `002050`, HTML renderer implementation accepted, and the
three-sample HTML presentation baseline frozen. User invocation / report
orchestration design is recorded in
`docs/FUNDAMENTAL_SKILL_USER_INVOCATION_ORCHESTRATION_DESIGN.md`. This document
records the accepted design boundary; the implementation, baseline freeze,
profile acceptance, HTML acceptance, and orchestration design do not modify
tests, fixtures, pipeline, scoring / readiness, Research Intelligence P1.1,
Dashboard, regression expected files, provider-primary behavior, default output,
provider raw artifacts, evidence packs, candidate reports, or review decision
artifacts. They do not run real smoke tests, read `TUSHARE_TOKEN`, use the
network, call Tushare or AkShare, connect MCP, promote fixture values,
automatically merge providers, or output buy / sell advice, target prices,
position sizing, portfolio weights, or technical trading advice.

Current design inputs reviewed:

- `docs/FUNDAMENTAL_AUTO_FACT_CANDIDATE_GENERATOR_DESIGN.md`
- `docs/FUNDAMENTAL_CANDIDATE_REPORT_REVIEW_PROTOCOL_DESIGN.md`
- `docs/FUNDAMENTAL_CANDIDATE_REVIEW_DECISIONS_ARTIFACT_DESIGN.md`
- `docs/FUNDAMENTAL_GROUND_TRUTH_BENCHMARK_DESIGN.md`
- `docs/PROJECT_CONTEXT_HANDOFF.md`
- local 600406 artifacts under
  `output/provider_comparison/20260526T233804/600406`
- local
  `output/ground_truth_candidates/20260527T155056/600406/fact_candidates.json`
- local
  `output/ground_truth_candidate_reviews/20260527T172520/600406/candidate_review_decisions.json`

The first accepted runtime artifact is
`output/research_reports/20260527T103241/600406/fundamental_research_report_v1.json`.
It is an ignored runtime artifact and is not committed.

The `600406`, `002371`, and `002050` Markdown runtime artifacts have since
passed cross-industry Product Readability / Analyst Experience Review with
their respective presentation profiles. The HTML presentation layer design is
recorded in
`docs/FUNDAMENTAL_RESEARCH_REPORT_V1_HTML_PRESENTATION_DESIGN.md`, and the
three-sample HTML acceptance summary is recorded in
`docs/FUNDAMENTAL_RESEARCH_REPORT_V1_HTML_ACCEPTANCE_SUMMARY.md`. User
invocation / report orchestration design is recorded in
`docs/FUNDAMENTAL_SKILL_USER_INVOCATION_ORCHESTRATION_DESIGN.md`. The next
recommended work is user invocation / orchestration implementation, followed by
end-to-end local runs for `600406`, `002371`, and `002050`; Dashboard / batch
design should follow the accepted single-stock orchestration path. The next
step is not more ad hoc single-target HTML generation, promote-rule design,
validator implementation, fixture promotion, live provider report, official
parser / CNInfo, or a Tushare primary switch.

## 1. Goal Correction

The project target is an automated A-share fundamental analysis Skill, not a
manual spreadsheet or field-filling audit tool.

The system should behave like a professional fundamental research analyst:

- The user inputs a stock code.
- The system automatically collects or reads approved local artifacts.
- The system automatically assesses data quality.
- The system produces macro, industry, and company-level analysis.
- The system identifies research judgement, opportunities, risks, evidence
  gaps, rebuttal conditions, and follow-up variables.
- The system exposes data caveats without forcing the user to manually find
  data or fill tables.

The data-quality chain is the foundation of the research report, not the final
product. `fact_candidates.json`, `candidate_review_decisions.json`, provider
comparison artifacts, and score / confidence explainability should feed the
report's data-quality assessment and evidence labels. They should not replace
the research report itself.

The report may state whether current evidence supports, does not support, or
still cannot verify a fundamental judgement. It must not output buy / sell
advice, target price, position sizing, portfolio weights, technical trading
signals, or account-level action guidance.

## 2. Input Data Layer

Research Report V1 may read already generated local artifacts only. It should
not call providers or fetch live data in V1 implementation.

Allowed conceptual inputs:

- `fundamental_<code>.json`
- provider-separated fundamental artifacts, such as
  `akshare_fundamental.json` and `tushare_fundamental.json`
- `evidence_pack_<code>.json`
- provider-separated evidence packs, such as `akshare_evidence_pack.json` and
  `tushare_evidence_pack.json`
- `fact_candidates.json`
- `candidate_review_decisions.json`
- `score_confidence_explainability.json`
- Research Intelligence P1.1 output, if present
- provider comparison `diff_report.json` / `diff_report.md`

Input roles:

- `fundamental_<code>.json` or provider-separated fundamentals provide
  deterministic company, financial, valuation, classification, score, and
  confidence fields.
- `evidence_pack_<code>.json` or provider-separated evidence packs provide
  research evidence, source trace, missing fields, and prompt-ready context.
- `fact_candidates.json` provides auto-generated candidate facts, source
  metadata, auto-accepted candidate status, manual-review queues, and
  data-quality limitations.
- `candidate_review_decisions.json` records review outcomes and follow-up
  classes for selected candidate queue items.
- `score_confidence_explainability.json` explains score / confidence drift,
  provider caveats, derived hints, and narrative hints without changing scoring.
- P1.1 output provides research questions, driver matrices, missing evidence,
  source-bucket independence, and evidence gaps when available.
- Provider comparison diff reports identify provider differences, score drift,
  confidence drift, and fields requiring manual review.

Required boundaries:

- Use `fact_candidates.json` and `candidate_review_decisions.json` for data
  quality assessment, not as reviewed ground truth.
- Use `evidence_pack` as the primary research evidence input.
- Use P1.1 as a research-question and evidence-gap input, not as proof of
  operating facts.
- Do not treat a candidate report as reviewed ground truth.
- Do not treat a review decision as fixture promotion.
- Do not treat `confirmed_for_future_promotion` as permission to write or
  display a value as `verified_fact`.
- Do not use candidate rows to change scoring, readiness, P1.1, fixtures,
  regression expected files, provider precedence, or primary-provider behavior.

## 3. Report Structure

`research_report_v1` should have a stable section structure. Each key
judgement inside these sections must carry an evidence label from section 4.

### A. Executive Summary

Purpose: summarize the fundamental research view without investment advice.

Required content:

- one-sentence fundamental judgement;
- current evidence strength;
- primary opportunity;
- primary risk;
- largest evidence gap;
- data-quality state.

The summary must distinguish:

- what is supported by verified or auto-accepted evidence;
- what is only a candidate fact;
- what is still a caveat or unsupported assumption;
- what must be followed over time.

### B. Data Quality Assessment

Purpose: explain how usable the current data is for research judgement.

Required content:

- fields that are `auto_accepted` core fields;
- fields that remain `manual_review_required`;
- whether valuation `as_of_date` is explicit;
- whether business-composition `period` is explicit;
- whether business-composition `classification_type` is explicit;
- whether business-composition `revenue_ratio` is explicit and denominator
  safe;
- whether `main_business` has an official source;
- impact of data quality on research conclusions.

For 600406, the existing local artifacts indicate the report should surface
these caveats:

- financial and valuation candidates can have strong provider traceability;
- valuation date can be explicitly represented as `2026-05-26` in the local
  artifacts;
- `main_business` still needs official-source support;
- business composition still has period, classification, ratio, denominator,
  mapping, and provider-coverage caveats;
- score drift exists in the provider comparison and must remain review-facing,
  not automatically accepted.

### C. Macro Context

Purpose: describe macro transmission paths that matter to this type of asset.

Required content:

- interest-rate environment and its impact on valuation sensitivity, discount
  rates, financing cost, and long-duration infrastructure expectations;
- credit environment and its impact on grid customers, collection, receivables,
  and capital-expenditure cadence;
- fiscal rhythm and public infrastructure spending constraints;
- power-grid investment cycle and policy implementation rhythm;
- policy cadence around power system modernization, digital grid, UHV, and
  distribution-grid upgrades;
- follow-up macro variables that should be tracked.

The report should not make macro forecasts. It should list mechanisms and
tracking variables only.

### D. Industry Context

Purpose: place the company in its relevant industry structure.

For 600406, the expected industry context is grid equipment / stable growth.

Required content:

- grid investment cycle;
- State Grid / China Southern Power Grid tender rhythm;
- UHV, distribution grid, digital grid, and new power system investment
  directions;
- power automation, relay protection, dispatching systems, power information
  communication, and control-system relevance;
- order conversion evidence requirements;
- accounts-receivable and cash-flow risk created by project delivery and
  settlement cadence;
- evidence required to prove industry prosperity is converting into company
  fundamentals.

The report must not turn industry narrative directly into company realization.
Industry prosperity can support a research hypothesis only when connected to
company orders, revenue, margins, cash flow, contract liabilities, or segment
evidence.

### E. Company Fundamentals

Purpose: evaluate company-level financial and operating quality.

Required fields:

- revenue;
- net profit;
- gross margin;
- ROE;
- operating cash flow;
- accounts receivable;
- inventory;
- contract liabilities;
- capex;
- business composition;
- valuation metrics, including PE, PB, and market cap;
- trusted fields versus fields needing review.

The report should separate:

- financial fields that can be labelled `auto_accepted_candidate`;
- reviewed fields, if a future reviewed source exists;
- fields that remain `manual_review_required`;
- missing or caveated fields that limit conclusion strength.

### F. Opportunity Analysis

Purpose: identify opportunity paths that are evidence constrained.

Rules:

- Every opportunity must be supported by evidence or a follow-up variable.
- Do not write generic policy-positive claims without evidence constraints.
- Distinguish verified facts, auto-accepted candidates, candidate facts, and
  unverified hypotheses.
- Use P1.1 research questions as open questions when direct evidence is
  missing.

For 600406, allowed opportunity themes include:

- grid investment cycle;
- digital grid;
- UHV and distribution-grid construction;
- power automation and relay-protection demand;
- stable operating quality;
- potentially steadier cash-flow characteristics.

These themes must remain constrained by evidence labels and must not imply
company realization unless company-level evidence supports it.

### G. Risk Analysis

Purpose: state what could weaken or invalidate the fundamental judgement.

Required risk categories:

- financial risk;
- order-realization risk;
- accounts-reivable and cash-flow risk;
- margin pressure;
- policy and tender rhythm risk;
- data-quality risk;
- unclear valuation-date risk;
- unclear business-composition period, classification, or ratio risk.

Risk language should be conditional and evidence-aware. The report should not
state unverified deterioration as fact.

### H. Evidence Gaps

Purpose: make missing or weak evidence explicit.

Required gaps:

- `valuation_metrics.as_of_date`;
- `business_composition.period`;
- `business_composition.classification_type`;
- `business_composition.revenue_ratio`;
- `main_business`;
- key missing evidence from P1.1 research questions, if present.

For 600406, V1 should always check whether these gaps have been resolved in the
available artifacts. If not resolved, they must appear in the report as caveats.

### I. Rebuttal / Bear Case Conditions

Purpose: define conditional facts that would weaken an optimistic or positive
fundamental reading.

Examples for 600406:

- revenue growth slows materially;
- operating cash flow deteriorates;
- accounts receivable rises faster than revenue or collection quality weakens;
- contract liabilities decline or fail to support future order visibility;
- gross margin compresses continuously;
- State Grid / China Southern Power Grid tender rhythm weakens;
- UHV, distribution-grid, or digital-grid project cadence falls short;
- business-composition evidence does not support the assumed exposure;
- valuation metrics become stale because `as_of_date` is missing or mismatched.

These must be written as conditions, not forecasts.

### J. Follow-Up Variables

Purpose: define what the user or future automation should track after report
generation.

Required follow-up variables:

- grid investment amount;
- State Grid / China Southern Power Grid tender data;
- UHV and distribution-grid project cadence;
- digital-grid policy and tender conversion;
- accounts-receivable turnover;
- operating cash flow;
- contract liabilities;
- gross margin;
- business composition;
- valuation `as_of_date`;
- PE / PB / market cap on a same-date basis.

Follow-up variables are not evidence that something has already happened. They
should be labelled `forward_tracking_variable`.

## 4. Evidence Classification

Research Report V1 should attach an evidence label to every key judgement.

Recommended labels:

| Label | Meaning | Allowed use |
| --- | --- | --- |
| `verified_fact` | Reviewed source or future reviewed fixture confirms the fact with clear source, period, and unit. | Strongest factual claims. Rare in V1 unless reviewed ground truth exists. |
| `auto_accepted_candidate` | Candidate passed V1 automatic checks for source, period / date, unit, type, and trace, but has not been promoted to reviewed ground truth. | Financial and valuation fields that passed candidate gates. |
| `manual_review_required` | The source exists or a candidate exists, but period, unit, classification, denominator, source, or conflict review remains unresolved. | Caveated facts and blocked conclusion inputs. |
| `unsupported_assumption` | The report can state the hypothesis but current evidence does not support treating it as fact. | Industry-to-company conversion hypotheses, unverified main-business claims, or unsupported order logic. |
| `coverage_caveat` | The provider or artifact coverage is incomplete, weak, stale, or outside V1 scope. | Missing domain evidence, missing official text, provider gaps, score-drift caveats. |
| `forward_tracking_variable` | A future variable to monitor; not proof of current fact. | Tender rhythm, grid capex, project cadence, margin trend, collection quality, valuation date refresh. |

Hard rules:

- Every key judgement must carry one of these evidence labels.
- Do not label a candidate as `verified_fact`.
- Do not label `confirmed_for_future_promotion` as `verified_fact`.
- Do not use P1.1 proxy evidence as operating fact.
- Do not convert industry narrative into company realization.
- Do not use derived hints as scoring, readiness, fixture, or report-truth
  inputs unless labelled as non-scoring caveats or hypotheses.
- Do not hide data-quality caveats behind a strong executive-summary sentence.

Suggested judgement object:

```json
{
  "judgement": "Grid investment and digital-grid demand may support future revenue visibility.",
  "evidence_label": "unsupported_assumption",
  "supporting_artifacts": ["evidence_pack", "research_intelligence_p1"],
  "caveat": "Company-level tender, order, revenue, and cash-flow conversion evidence is still required.",
  "follow_up_variables": ["grid_investment_amount", "state_grid_tenders"]
}
```

## 5. Research Judgement Boundaries

Allowed:

- provide fundamental research judgement;
- state that current evidence supports, does not support, or still cannot
  verify a claim;
- explain opportunities and risks;
- identify evidence gaps;
- define rebuttal conditions;
- define follow-up variables;
- compare data quality across fields and providers;
- flag score / confidence explainability caveats.

Not allowed:

- buy / sell / hold recommendations;
- target price;
- position sizing;
- portfolio weight;
- account or execution advice;
- technical-analysis trading signals;
- treating provider-primary changes as part of report generation;
- fixture writes, scoring changes, P1.1 changes, or regression changes.

## 6. Relationship With Existing Modules

Research Report V1 is an aggregation and interpretation layer. It reads or
references existing artifacts and does not mutate them.

Relationships:

- Candidate Generator provides data-quality candidates, source trace, candidate
  status, auto-accepted fields, and manual-review queues.
- Review Decisions provide review status, follow-up classes, and caveats for
  selected candidate queue items.
- `evidence_pack` provides research evidence, source summaries, missing fields,
  and prompt-ready context.
- P1.1 provides research questions, driver matrices, evidence gaps, and
  not-assessable markers.
- Scoring / readiness provide structured scores, confidence, missing fields,
  and current deterministic result state.
- Provider comparison provides diff reports, score drift, confidence drift,
  provider caveats, derived hints, and narrative hints.

Required boundaries:

- Research Report V1 does not change candidate reports.
- Research Report V1 does not change review decisions.
- Research Report V1 does not write fixtures.
- Research Report V1 does not promote candidate facts.
- Research Report V1 does not change scoring / readiness.
- Research Report V1 does not change P1.1.
- Research Report V1 does not change provider precedence.
- Research Report V1 does not merge AkShare and Tushare.
- Research Report V1 does not write regression expected files.

## 7. Output Artifact Design

Future runtime output path:

```text
output/research_reports/<timestamp>/<code>/fundamental_research_report_v1.json
```

Later display formats may be added:

```text
output/research_reports/<timestamp>/<code>/fundamental_research_report_v1.md
output/research_reports/<timestamp>/<code>/fundamental_research_report_v1.html
```

This stage does not write any runtime output.

Recommended top-level schema:

```json
{
  "code": "600406",
  "generated_at": "YYYY-MM-DDTHH:MM:SSZ",
  "report_type": "fundamental_research_report_v1",
  "not_for_trading_advice": true,
  "data_quality_assessment": {},
  "executive_summary": {},
  "macro_context": {},
  "industry_context": {},
  "company_fundamentals": {},
  "opportunity_analysis": [],
  "risk_analysis": [],
  "evidence_gaps": [],
  "rebuttal_conditions": [],
  "follow_up_variables": [],
  "source_artifact_refs": {}
}
```

Recommended detailed fields:

```json
{
  "executive_summary": {
    "one_sentence_fundamental_judgement": {
      "text": "",
      "evidence_label": "manual_review_required"
    },
    "evidence_strength": "",
    "primary_opportunity": {},
    "primary_risk": {},
    "largest_evidence_gap": {},
    "data_quality_state": {}
  },
  "data_quality_assessment": {
    "auto_accepted_core_fields": [],
    "manual_review_required_fields": [],
    "valuation_as_of_date_status": {},
    "business_composition_status": {},
    "main_business_status": {},
    "score_confidence_explainability_status": {},
    "impact_on_research_conclusion": []
  },
  "company_fundamentals": {
    "financial_metrics": [],
    "valuation_metrics": [],
    "business_composition": [],
    "trusted_fields": [],
    "fields_needing_review": []
  },
  "source_artifact_refs": {
    "fundamental": [],
    "evidence_pack": [],
    "fact_candidates": null,
    "candidate_review_decisions": null,
    "score_confidence_explainability": null,
    "provider_diff_report": null,
    "research_intelligence_p1": []
  }
}
```

Suggested item shape for analysis lists:

```json
{
  "title": "",
  "analysis": "",
  "evidence_label": "coverage_caveat",
  "supporting_fields": [],
  "source_artifact_refs": [],
  "caveats": [],
  "follow_up_variables": []
}
```

Artifact rules:

- Generated report artifacts stay under `output/research_reports/`.
- No default production output is written unless the future CLI explicitly
  asks for this report.
- Source references should be sanitized relative references.
- No real token, MCP URL, local secret path, private connection string, or raw
  paid-source dump may be written.
- `not_for_trading_advice` must be `true`.

## 8. 600406 国电南瑞 report V1 expected behavior

600406 is the Stable Growth / grid-equipment first-version sample.

Expected report behavior:

- Treat 600406 as a `stable_growth` grid-equipment sample.
- Emphasize grid-equipment industry logic, not generic stable-growth wording.
- Cover grid investment, State Grid / China Southern Power Grid tenders, UHV,
  distribution-grid upgrades, digital grid, power automation, relay protection,
  dispatching systems, and power information communication.
- Use the financial and valuation auto-accepted candidates as candidate-level
  evidence, not reviewed facts.
- Surface the existing valuation date clarity as a positive data-quality point
  when the artifact provides same-date PE, PB, and market-cap metadata.
- Keep `main_business` caveated until official text is available.
- Keep business composition caveated until period, classification type,
  revenue ratio, denominator scope, and provider mapping are resolved.
- Include score-drift and business-quality caveats from provider comparison and
  score / confidence explainability.
- Do not infer a strong company conclusion merely because Tushare financial
  fields are auto-accepted.
- Do not convert industry policy support into company order or revenue
  realization without company-level evidence.
- Do not treat AkShare-only main-business text or composition ratio as reviewed
  ground truth.
- Do not treat the largest segment derived hint as canonical
  `basic_info.main_business`.

Opportunity logic for 600406:

- Grid investment can be an opportunity path only when linked to tenders,
  orders, revenue, margin, cash flow, contract liabilities, or segment evidence.
- Digital grid can be an opportunity hypothesis only when linked to disclosed
  revenue, business composition, product lines, or order evidence.
- UHV and distribution-grid construction can be discussed as follow-up
  variables and industry demand paths, not as automatic company realization.
- Stable cash-flow or operating quality must be tested against operating cash
  flow, accounts receivable, contract liabilities, margin, ROE, and capex.

Risk logic for 600406:

- tender and policy cadence risk;
- order-conversion risk;
- accounts-receivable and cash-flow risk;
- gross-margin pressure;
- contract-liability decline or weak backlog proxy risk;
- business-composition period and classification risk;
- revenue-ratio denominator risk;
- `main_business` official-source gap;
- valuation `as_of_date` staleness or mismatch risk.

Expected evidence labels:

- financial and valuation candidates from the current 600406 artifact:
  `auto_accepted_candidate`;
- valuation same-date clarity:
  `auto_accepted_candidate` or `manual_review_required` depending on future
  implementation input;
- main-business official source gap: `manual_review_required` or
  `coverage_caveat`;
- business-composition period / classification / ratio caveats:
  `manual_review_required`;
- industry and policy transmission paths:
  `unsupported_assumption` unless supported by company-level evidence;
- tender, project, margin, receivable, cash-flow, and valuation-date monitoring:
  `forward_tracking_variable`.

## 9. Acceptance Criteria

Research Report V1 implementation and the first `600406` runtime artifact have
passed acceptance. Acceptance checked:

- no token read;
- no network access;
- no provider call;
- no Tushare call;
- no AkShare call;
- no MCP connection;
- no fixture write;
- no scoring / readiness change;
- no P1.1 change;
- no regression expected change;
- no HTML / Dashboard change unless separately requested;
- no investment advice, target price, position sizing, portfolio weight, or
  technical trading advice;
- every key judgement has an evidence label;
- candidates are not written as `verified_fact`;
- review decisions are not treated as fixture promotion;
- P1.1 proxies are not written as company operating facts;
- industry narrative is not written as company realization;
- data-quality caveats appear in the report;
- 600406 report explains opportunity, risk, evidence gaps, rebuttal
  conditions, and follow-up variables;
- `not_for_trading_advice=true` appears in the output;
- targeted tests `64 passed`;
- regression `passed=47 failed=0 total=47`.

## 10. Roadmap

Completed sequence:

1. This design document.
2. Research Report V1 implementation.
3. First report generation from existing 600406 local artifacts.
4. 600406 report artifact acceptance.
5. Research Report V1 baseline freeze / documentation sync.
6. Initial product readability review for the `600406` refined Markdown
   artifact.
7. Presentation profile design for multi-strategy Markdown / future HTML
   presentation.
8. Presentation profile registry acceptance.
9. `600406`, `002371`, and `002050` real-sample Markdown profile acceptance.
10. Cross-industry Markdown validation.
11. HTML renderer implementation acceptance.
12. `600406`, `002371`, and `002050` HTML runtime artifact acceptance.
13. HTML presentation layer three-sample baseline freeze.
14. User invocation / report orchestration design.

Next recommended sequence:

1. Commit the user invocation / report orchestration design documentation patch.
2. Implement the single-stock user invocation / orchestration path.
3. Run an end-to-end local orchestration for `600406`, then cross-profile local
   runs for `002371` and `002050`.
4. Evaluate Dashboard / batch report design after the single-stock path is
   accepted, or separately do focused HTML visual refinement if requested.
5. Keep caveats, evidence labels, data-quality notes, rebuttal conditions, and
   follow-up variables visible in any future display work.
6. Later consider promote rules, validator, fixture promotion, live provider
   report, official parser / CNInfo, and primary-provider switch only after the
   report product experience is reviewed.

Do not continue into promote-rule design, validator implementation, fixture
promotion, live provider report, official parser / CNInfo, or Tushare primary
switch as the next step. The product line should now move from accepted
single-report HTML generation into user-facing invocation / orchestration.

## 11. Presentation profile design addendum

The `600406` refined Markdown report has passed initial product readability
review and can remain as the investment-manager draft baseline. The subsequent
`002371` and `002050` Markdown reports have also passed profile-specific
readability review, confirming that the presentation layer no longer leaks the
`600406` / grid-equipment language into semiconductor equipment or thermal
management reports.

Use `docs/FUNDAMENTAL_RESEARCH_REPORT_V1_PRESENTATION_PROFILE_DESIGN.md` and
`docs/FUNDAMENTAL_RESEARCH_REPORT_V1_MARKDOWN_PROFILE_ACCEPTANCE_SUMMARY.md` as
the accepted references for the profile layer. The accepted profile layer
separates the common report skeleton from industry-specific Chinese language,
opportunity ordering, risk ordering, evidence-gap focus, and follow-up
variables.

The profile layer remains presentation-only. It must not change the Research
Report V1 JSON builder, candidate generator, review decisions, scoring /
readiness, P1.1, data artifacts, provider behavior, regression expected files,
or evidence labels. It must prevent cross-contamination between
`stable_growth_grid_equipment`, `semiconductor_equipment_cycle`, and
`advanced_manufacturing_thermal_management`, and must fall back to
`generic_fundamental_report` when the profile cannot be selected reliably.

## 12. Cross-industry Markdown profile acceptance

The following runtime Markdown artifacts are accepted as real-sample validation
for the first three presentation profiles:

| code | company | profile | accepted runtime artifact |
| --- | --- | --- | --- |
| `600406` | 国电南瑞 | `stable_growth_grid_equipment` | `output/research_reports/20260527T210301/600406/fundamental_research_report_v1.md` |
| `002371` | 北方华创 | `semiconductor_equipment_cycle` | `output/research_reports/20260527T220148/002371/fundamental_research_report_v1.md` |
| `002050` | 三花智控 | `advanced_manufacturing_thermal_management` | `output/research_reports/20260528T003826/002050/fundamental_research_report_v1.md` |

Acceptance conclusion:

- `600406` Markdown accepted.
- `002371` Markdown accepted.
- `002050` Markdown accepted.
- Presentation profile registry accepted.
- Professional analyst voice gate accepted.
- Cross-industry Markdown validation passed.

Cross-contamination result:

- `600406` did not inherit semiconductor or robot / new-business language.
- `002371` did not inherit grid or thermal-management language.
- `002050` did not inherit grid or semiconductor-equipment language.
- The V1 hard-fail term-isolation strategy is effective for the three accepted
  samples.

Latest verification results are quoted from the acceptance input and were not
rerun in the documentation-only acceptance-summary stage: targeted tests
`86 passed`, full pytest `734 passed, 1 skipped`, and regression
`passed=47 failed=0 total=47`.

The HTML presentation layer design is recorded in
`docs/FUNDAMENTAL_RESEARCH_REPORT_V1_HTML_PRESENTATION_DESIGN.md`, and the
three-sample HTML acceptance summary is recorded in
`docs/FUNDAMENTAL_RESEARCH_REPORT_V1_HTML_ACCEPTANCE_SUMMARY.md`. HTML must
consume Markdown / presentation-layer output or the Research Report V1
structured payload, must not re-analyze or alter conclusions, must not hide
caveats, and must not call providers, use the network, read tokens, connect
MCP, or change promote rules, validators, fixtures, scoring, readiness, P1.1,
or provider primary behavior. The HTML presentation baseline is frozen; the
next recommended stage is Dashboard / batch report design or HTML visual
refinement.

## 13. HTML presentation layer design and acceptance addendum

The HTML presentation layer is accepted as a display-only design boundary, the
renderer implementation is accepted, and the three-sample baseline is frozen.
The renderer consumes accepted Markdown as the preferred input and may consume
`fundamental_research_report_v1.json` only to supplement display metadata,
cards, evidence labels, source references, and data-quality caveats. It must
not generate conclusions from raw provider artifacts or bypass the Markdown
profile / professional voice gate.

HTML runtime output is written only when explicitly requested:

```text
output/research_reports/<timestamp>/<code>/fundamental_research_report_v1.html
```

Runtime HTML artifacts remain ignored output and must pass secret scanning
before writing. They must not contain tokens, MCP URLs, local secret paths,
`.env` paths, provider raw dumps, or paid-source long text. They must visibly
preserve `not_for_trading_advice`, evidence labels, data-quality caveats,
evidence gaps, rebuttal conditions, and follow-up variables.

Accepted HTML runtime artifacts:

| code | company | profile | accepted runtime artifact |
| --- | --- | --- | --- |
| `600406` | 国电南瑞 | `stable_growth_grid_equipment` | `output/research_reports/20260528T012952/600406/fundamental_research_report_v1.html` |
| `002371` | 北方华创 | `semiconductor_equipment_cycle` | `output/research_reports/20260528T090024/002371/fundamental_research_report_v1.html` |
| `002050` | 三花智控 | `advanced_manufacturing_thermal_management` | `output/research_reports/20260528T091133/002050/fundamental_research_report_v1.html` |

Acceptance confirmed artifact boundary, secret scan, external resource scan,
HTML structure, content consistency, profile isolation, caveat visibility, and
initial UI readability. Latest accepted verification results are quoted, not
rerun here: targeted tests `124 passed`; regression
`passed=47 failed=0 total=47`.

The accepted renderer module is
`src/fundamental_skill/research_report/research_report_v1_html.py` with a
renderer shaped around:

```python
render_research_report_v1_html(markdown: str, report: dict | None = None) -> str
```

The writer should keep a strict output boundary under `output/research_reports/`.

The next step is no longer more single-stock HTML generation. Dashboard / batch
report design should wait until the single-stock user invocation /
orchestration path is implemented and accepted, unless a separate stage asks
only for focused HTML visual refinement. User invocation / report orchestration
design is recorded in
`docs/FUNDAMENTAL_SKILL_USER_INVOCATION_ORCHESTRATION_DESIGN.md`. Promote rules,
validator, fixture promotion, live provider report, official parser / CNInfo,
and Tushare primary remain later work.
