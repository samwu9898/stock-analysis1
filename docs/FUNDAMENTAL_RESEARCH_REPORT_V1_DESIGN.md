# Fundamental Research Report V1 Design

Date: 2026-05-28

Stage: Fundamental Skill Research Report V1 Design, Cross-Industry Markdown
Profile Acceptance, HTML Presentation Layer Design, Three-Sample HTML
Acceptance, User Invocation / Report Orchestration Design, Three-Sample
Offline Orchestration Acceptance, and Three-Sample CLI Runtime Acceptance.

Status: design accepted, implementation accepted, Research Report V1 baseline
frozen, cross-industry Markdown profile validation accepted for `600406`,
`002371`, and `002050`, HTML renderer implementation accepted, the
three-sample HTML presentation baseline frozen, single-stock offline
orchestration implementation accepted, Chinese summary patch accepted,
`600406` / `002371` / `002050` offline runtime acceptance complete, CLI
implementation accepted, `600406` / `002371` / `002050` CLI runtime acceptance
complete, single-stock offline CLI baseline frozen, accepted manifest module
accepted, manifest-first locator hardening accepted, retained runtime manifest
review accepted, and manifest locator runtime baseline frozen. User invocation /
report orchestration design is recorded in
`docs/FUNDAMENTAL_SKILL_USER_INVOCATION_ORCHESTRATION_DESIGN.md`, the offline
orchestration closeout is recorded in
`docs/FUNDAMENTAL_SKILL_OFFLINE_ORCHESTRATION_ACCEPTANCE_SUMMARY.md`, the CLI
design is recorded in
`docs/FUNDAMENTAL_SKILL_USER_INVOCATION_CLI_DESIGN.md`, and the CLI runtime
acceptance closeout is recorded in
`docs/FUNDAMENTAL_SKILL_CLI_RUNTIME_ACCEPTANCE_SUMMARY.md`. This document
now also links the accepted artifact manifest / freshness design recorded in
`docs/FUNDAMENTAL_ACCEPTED_ARTIFACT_MANIFEST_FRESHNESS_DESIGN.md` and the
manifest locator runtime acceptance closeout recorded in
`docs/FUNDAMENTAL_ACCEPTED_MANIFEST_LOCATOR_RUNTIME_ACCEPTANCE_SUMMARY.md`.
Minimal CNInfo / official disclosure parser design is recorded in
`docs/FUNDAMENTAL_MINIMAL_CNINFO_OFFICIAL_DISCLOSURE_PARSER_DESIGN.md`. This
document also records the local sample parser acceptance summary in
`docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_PARSER_LOCAL_SAMPLE_ACCEPTANCE_SUMMARY.md`.
The real local filing parser acceptance summary is recorded in
`docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_PARSER_REAL_LOCAL_FILING_ACCEPTANCE_SUMMARY.md`.
The independent business-composition table parser design is recorded in
`docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_BUSINESS_COMPOSITION_TABLE_PARSER_DESIGN.md`.
The table schema / quality model implementation and caveat-only hardening
acceptance summary is recorded in
`docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_BUSINESS_COMPOSITION_TABLE_SCHEMA_ACCEPTANCE_SUMMARY.md`.
Those summaries validate only the parser local-file and real-local-file
minimum loops, the table-parser design boundary, and the in-memory table schema
/ quality model. They do not wire L1 official disclosure evidence into
Research Report V1. This document records the accepted design boundary; the
implementation, baseline freeze, profile acceptance, HTML acceptance,
orchestration design, offline runtime acceptance, CLI runtime acceptance, and
table schema / quality model acceptance do not modify tests, fixtures,
pipeline, scoring / readiness, Research Intelligence P1.1, Dashboard,
regression expected files, provider-primary behavior, default output, provider
raw artifacts, evidence packs, candidate reports, or review decision artifacts.
They do not run real smoke tests, read `TUSHARE_TOKEN`, use the network, call
Tushare or AkShare, connect MCP, promote fixture values, automatically merge
providers, or output buy / sell advice, target prices, position sizing,
portfolio weights, or technical trading advice.

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
`docs/FUNDAMENTAL_SKILL_USER_INVOCATION_ORCHESTRATION_DESIGN.md`, and
single-stock offline orchestration acceptance is recorded in
`docs/FUNDAMENTAL_SKILL_OFFLINE_ORCHESTRATION_ACCEPTANCE_SUMMARY.md`. The
single-stock CLI runtime acceptance is recorded in
`docs/FUNDAMENTAL_SKILL_CLI_RUNTIME_ACCEPTANCE_SUMMARY.md`. The manifest
locator runtime acceptance is recorded in
`docs/FUNDAMENTAL_ACCEPTED_MANIFEST_LOCATOR_RUNTIME_ACCEPTANCE_SUMMARY.md`.
The next recommended official-disclosure work is CSV table facts ->
`official_disclosure_facts.json` integration design. The next step is not more ad hoc
single-target HTML generation, promote-rule design, validator implementation,
fixture promotion, live CNInfo fetch, live provider report, MCP, Tushare token
work, or a Tushare primary switch.

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
15. Single-stock offline orchestration implementation acceptance.
16. Chinese summary patch acceptance.
17. `600406`, `002371`, and `002050` one-sentence offline runtime acceptance.
18. One-sentence local report invocation baseline freeze.
19. User invocation CLI / command wrapper design.
20. CLI implementation acceptance.
21. `600406`, `002371`, and `002050` CLI runtime acceptance.
22. Single-stock offline CLI baseline freeze.
23. Accepted manifest module acceptance.
24. Manifest-first locator hardening acceptance.
25. Runtime-aware test boundary acceptance.
26. Retained runtime manifest review acceptance for `600406`, `002371`, and
    `002050`.
27. Manifest locator runtime baseline freeze.
28. Minimal CNInfo / official disclosure parser design.
29. Official disclosure parser local-file implementation and local sample
    runtime review.
30. Real local official filing sample runtime review using the `600406` 2025
    semiannual report TXT sample.
31. Official Disclosure Business Composition Table Parser Design.
32. Business Composition Table Schema / Quality Model acceptance.
33. Local Structured Table Reader Design.

Next recommended sequence:

1. CSV reader schema / implementation for the independent table parser.
2. One local CSV structured sample runtime review.
3. Local HTML table reader design / implementation.
4. DOCX table reader design / implementation.
5. Table quality integration runtime review.
6. Add table facts to `official_disclosure_facts.json` only after source
   location, table quality, row / column alignment, unit, denominator, and
   total checks are explicit.
7. Add candidate generator integration only after a separate accepted design.
8. Add Research Report V1 integration only after a separate accepted design.
9. Start batch / dashboard design after manifest closeout, and make it depend
   on manifest-located artifacts.
10. Keep caveats, evidence labels, data-quality notes, rebuttal conditions, and
   follow-up variables visible in any future display work.
11. Later consider promote rules, validator, fixture promotion, live provider
   report, MCP, Tushare token work, and
   primary-provider switch only after a separately accepted stage.

Do not continue into promote-rule design, validator implementation, fixture
promotion, live CNInfo fetch, live provider report, MCP, Tushare token work,
or Tushare primary switch as the next step. The product line should now move
from accepted manifest locator runtime baseline, Minimal CNInfo / official
disclosure parser local + real-local-file acceptance, and Business Composition
Table Parser Design into CSV table facts -> `official_disclosure_facts.json`
integration design. The table schema / quality model implementation, Local
Structured Table Reader Design, CSV reader runtime acceptance, CSV to table
facts design, and CSV table facts runtime acceptance are already accepted /
recorded.

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
| `002371` | 北方华创 | `semiconductor_equipment_cycle` | `output/research_reports/20260528T125518/002371/fundamental_research_report_v1.md` |
| `002050` | 三花智控 | `advanced_manufacturing_thermal_management` | `output/research_reports/20260528T003826/002050/fundamental_research_report_v1.md` |

Acceptance conclusion:

- `600406` Markdown accepted.
- `002371` Markdown accepted.
- `002050` Markdown accepted.
- Presentation profile registry accepted.
- Professional analyst voice gate accepted.
- Cross-industry Markdown validation passed.
- Older `002371` Markdown / HTML runtime artifacts were superseded by the
  `20260528T125518` professional-voice regenerated artifacts; user-facing
  orchestration baseline should use the `20260528T125518` Markdown / HTML
  artifacts.

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
single-stock offline orchestration runtime is now accepted, and the next
recommended stage is user invocation CLI / command wrapper work.

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
| `002371` | 北方华创 | `semiconductor_equipment_cycle` | `output/research_reports/20260528T125518/002371/fundamental_research_report_v1.html` |
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

The next step is no longer more single-stock HTML generation. The single-stock
user invocation / offline orchestration path is implemented and accepted for
`600406`, `002371`, and `002050`; Dashboard / batch report design should wait
until the single-stock CLI / command wrapper is accepted, unless a separate
stage asks only for focused HTML visual refinement. User invocation / report
orchestration design is recorded in
`docs/FUNDAMENTAL_SKILL_USER_INVOCATION_ORCHESTRATION_DESIGN.md`, and the
offline orchestration acceptance closeout is recorded in
`docs/FUNDAMENTAL_SKILL_OFFLINE_ORCHESTRATION_ACCEPTANCE_SUMMARY.md`. Promote
rules, validator, fixture promotion, live provider report, official parser /
CNInfo, MCP, Tushare token work, and Tushare primary remain later work.

## 14. Offline orchestration acceptance addendum

Single-stock offline orchestration implementation, Chinese summary patch, and
the `600406` / `002371` / `002050` one-sentence local report invocation runtime
checks are accepted. The accepted flow is:

```text
user natural-language request
  -> normalize request
  -> safe offline flags
  -> locate local artifacts
  -> reuse accepted HTML
  -> extract Chinese summary from Markdown
  -> return HTML / Markdown / JSON paths
  -> return opportunity / risk / evidence gap / data quality
  -> not-for-trading-advice statement
```

Latest accepted results are quoted, not rerun here: targeted tests
`163 passed`, full pytest `811 passed, 1 skipped`, and regression
`passed=47 failed=0 total=47`.

The CLI runtime acceptance closeout is recorded in
`docs/FUNDAMENTAL_SKILL_CLI_RUNTIME_ACCEPTANCE_SUMMARY.md`. Manifest locator
runtime acceptance is recorded in
`docs/FUNDAMENTAL_ACCEPTED_MANIFEST_LOCATOR_RUNTIME_ACCEPTANCE_SUMMARY.md`.
Next recommended official-disclosure stage: CSV table facts ->
`official_disclosure_facts.json` integration design.

## 15. CLI runtime acceptance addendum

The CLI implementation and the `600406` / `002371` / `002050` CLI runtime
checks are accepted. The accepted flow is:

```text
Codex / user command
  -> CLI argument parsing
  -> accepted offline orchestration
  -> normalize request
  -> safe offline flags
  -> locate local artifacts
  -> reuse accepted HTML
  -> extract Chinese summary from Markdown
  -> stdout returns HTML / Markdown / JSON paths
  -> stdout returns opportunity / risk / evidence gap / data quality
  -> not-for-trading-advice statement
```

Accepted CLI commands:

```bash
python -m src.fundamental_skill.research_report.generate_report --code 600406 --format html --data-mode offline_local_artifacts
python -m src.fundamental_skill.research_report.generate_report --company-name 北方华创 --format html
python -m src.fundamental_skill.research_report.generate_report --company-name 三花智控 --format html
```

The single-stock offline CLI baseline is frozen. No additional single-stock CLI
runtime generation is recommended unless a new sample or regression check
requires it.

## 16. Accepted artifact manifest / freshness addendum

Accepted artifact manifest / freshness design is recorded in
`docs/FUNDAMENTAL_ACCEPTED_ARTIFACT_MANIFEST_FRESHNESS_DESIGN.md`.

This addendum establishes the future Research Report V1 artifact-selection
contract:

- The accepted manifest is the primary source of truth for user-facing HTML,
  Markdown, and JSON artifact selection.
- Timestamp-latest lookup becomes a warned fallback, not the baseline selector.
- The manifest records accepted artifacts, artifact hashes, acceptance metadata,
  lineage, superseded artifacts, and freshness metadata.
- The manifest is an ignored runtime artifact under
  `output/research_reports/accepted_manifest.json`.
- The manifest is not a fixture, not a validator, not CNInfo ingestion, not
  evidence-tier promotion, and not a report conclusion rewrite path.
- Freshness states are `current`, `unknown`, `stale`, `superseded`, and
  `invalidated`.
- `unknown` and `stale` must be visible in user-facing orchestration / CLI
  responses; `superseded` and `invalidated` must not be returned as accepted
  baselines.
- `002371` requires mixed timestamp lineage support: accepted Markdown / HTML
  are under `20260528T125518`, while accepted JSON remains under
  `20260527T220148`.

Manifest schema / writer / reader implementation, locator hardening, ignored
runtime manifest generation, and retained runtime acceptance are now accepted
for `600406`, `002371`, and `002050`. Minimal CNInfo / official disclosure
parser design, local sample acceptance, real local filing acceptance, and
business-composition table parser design plus schema / quality model
acceptance and Local Structured Table Reader Design are now recorded. CSV
reader runtime acceptance, CSV to table facts design, and CSV table facts
runtime acceptance are also recorded. The next recommended
official-disclosure stage is CSV table facts ->
`official_disclosure_facts.json` integration design. Batch / Dashboard can
start after manifest closeout and should depend on manifest-located artifacts.
Live Tushare provider mode, live CNInfo fetch, MCP, token work, validator,
fixture promotion, and Tushare primary remain later separately accepted stages.

## 17. Manifest locator runtime acceptance addendum

Accepted manifest module, manifest-first locator hardening, runtime-aware test
boundary, and retained runtime manifest review are accepted. The retained
ignored manifest is `output/research_reports/accepted_manifest.json`, remains
ignored by `.gitignore`, is not tracked or staged, and `git ls-files output`
remains empty.

Runtime manifest record:

- SHA256:
  `C1F97162A59DE113CD4C9F1A9531AEC3A915A3D6F09365098201234E6F5BEB7F`
- size: `7678`
- mtime UTC: `2026-05-28 10:17:55`
- entries: `3`
- all freshness statuses: `current`

Manifest-first runtime acceptance confirmed:

- `600406` CLI runtime accepted.
- `002371` CLI runtime accepted, with accepted HTML / Markdown under
  `20260528T125518` and accepted JSON under `20260527T220148`.
- `002050` CLI runtime accepted.
- All three CLI runs showed `Manifest 状态：used` and
  `Freshness 状态：current`.
- No `manifest_missing_warning`, timestamp fallback warning, English JSON
  summary leak, full body dump, profile cross-contamination, or positive
  trading advice was observed.

Latest accepted verification results are quoted, not rerun here: targeted
tests with retained manifest `251 passed`, full pytest with retained manifest
`899 passed, 1 skipped`, and regression `passed=47 failed=0 total=47`.

The manifest does not promote evidence labels, verify official facts, implement
CNInfo parsing, act as a validator, or promote fixtures. Future runtime updates
must pass acceptance before the manifest is updated.

## 18. Minimal CNInfo / Official Disclosure Parser Addendum

Minimal CNInfo / official disclosure parser design is recorded in
`docs/FUNDAMENTAL_MINIMAL_CNINFO_OFFICIAL_DISCLOSURE_PARSER_DESIGN.md`.
Local sample acceptance is recorded in
`docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_PARSER_LOCAL_SAMPLE_ACCEPTANCE_SUMMARY.md`.
Real local filing acceptance is recorded in
`docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_PARSER_REAL_LOCAL_FILING_ACCEPTANCE_SUMMARY.md`.

Research Report V1 relationship:

- Research Report V1 remains an offline local-artifact report layer.
- The official parser is not part of the current default runtime path.
- Future `official_disclosure_facts.json` artifacts may strengthen
  data-quality assessment by providing official main-business text, official
  business-composition facts, management-guidance placeholders, and A-share
  risk triggers.
- Accepted L1 official facts may later be cited as stronger sources after a
  separate candidate / review / acceptance integration.
- The report must keep caveats visible when official parser confidence,
  source location, denominator, period, classification type, or unit is weak.

Evidence-tier relationship:

- `L1_official_disclosure` means CNInfo / exchange / company official filing
  text with source location and parser confidence.
- `L2_multi_source_consistent` means multiple market data providers agree after
  source and period review.
- `L3_single_source_candidate` means one provider or unreviewed candidate.
- `L4_unsupported_or_missing` means hypothesis or missing evidence.
- Manifest / freshness status is not evidence tier.

Boundaries:

- Official parser output does not directly rewrite Research Report V1.
- Official parser output does not automatically overwrite provider output.
- Official parser output does not write fixtures, change scoring / readiness,
  change P1.1, change regression expected files, or update the accepted
  manifest.
- Official parser triggers are not trading signals, target-price inputs, or
  position-sizing inputs.

Local sample runtime acceptance:

- Minimal official disclosure parser local-file implementation accepted.
- Conservative Period Patch accepted.
- Local sample runtime review accepted.
- Local-file parser baseline frozen.
- Local sample:
  `output/official_disclosures/local_samples/600406_annual_report_sample.txt`.
- Runtime artifact:
  `output/official_disclosures/20260528_194020/600406/official_disclosure_facts.json`.
- Validated flow: local sample text -> `read_local_official_text` ->
  `extract_periodic_report_basics` -> `extract_main_business_candidate` ->
  `build_official_disclosure_facts` -> `write_official_disclosure_facts` ->
  `read_official_disclosure_facts` -> `validate_official_disclosure_facts`.
- Accepted result: `document_type=annual_report`, `report_period=2025A`,
  `disclosure_date=2026-04-30`, main-business candidate from `主营业务`,
  `source_documents=1`, `extracted_facts=4`, all L1 facts have source
  location, and `not_for_trading_advice=true`.

Real local filing runtime acceptance:

- Real local official filing sample runtime accepted.
- Official disclosure parser real-local-file baseline frozen.
- Input sample:
  `output/official_disclosures/local_real_samples/600406_2025_semiannual_report_real.txt`.
- Runtime artifact:
  `output/official_disclosures/20260528T125521Z/600406/official_disclosure_facts.json`.
- Input size `32961` bytes.
- Input sha256
  `7a16dca91ac2d0a9ec6def90a17fa28e820f0ebdb87cdf86a0e9a6fb0df1acc3`.
- Accepted result: `document_type=semiannual_report`,
  `report_period=2025H1`, `disclosure_date=2025-08-28`, extraction confidence
  `medium`, main-business L1 candidate from `source_section=主营业务`,
  `needs_human_review=true`, no verified fact, `source_documents=1`,
  `extracted_facts=1`, and `not_for_trading_advice=true`.
- Business composition regions were detected: `分行业`, `分产品`,
  `主营业务分行业情况`, `主营业务分产品情况`, `主营业务分地区情况`, and `分地区`.
- The artifact recorded `business_composition_section_detected` and
  `table_structure_unreliable_due_to_pdf_text_copy`.
- It did not extract revenue, cost, gross margin, revenue ratio, YoY, or
  segment as structured L1 facts because copied PDF TXT table structure is
  unreliable.

Research Report V1 boundary after official parser local-file acceptance:

- The local sample is not live CNInfo.
- The real local TXT sample is not live CNInfo and is not original parsed PDF.
- PDF table parsing is not implemented.
- The runtime artifact is ignored output, not a fixture, not a regression
  expected file, not an accepted manifest update, and not a Research Report V1
  update.
- L1 official disclosure facts are not yet candidate-generator inputs.
- L1 official disclosure facts are not yet accepted report evidence.
- No Research Report V1 builder, renderer, orchestration, CLI, scoring, P1.1,
  fixture, or accepted manifest behavior changes.

Next recommended step after Local Structured Table Reader Design is CSV Reader
Schema / Implementation. Do not extract numeric values from disordered TXT
tables, and do not jump directly into live
CNInfo fetch, Tushare, MCP, validator, fixture promotion, candidate generator
integration, Research Report V1 integration, Batch, or Dashboard
implementation.

## 19. Business Composition Table Parser Design Addendum

The independent table-parser design is recorded in
`docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_BUSINESS_COMPOSITION_TABLE_PARSER_DESIGN.md`.
The table schema / quality model implementation and caveat-only hardening are
accepted and frozen in
`docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_BUSINESS_COMPOSITION_TABLE_SCHEMA_ACCEPTANCE_SUMMARY.md`.

Research Report V1 relationship:

- The table parser is a future official-disclosure module, not part of the
  current report builder, renderer, orchestration, or CLI path.
- Future table facts may strengthen data-quality assessment only after
  separate candidate-generator and report-integration designs are accepted.
- L1 table facts require `source_table_id`, row / column location, table
  quality, unit, denominator, period, and source location.
- `unreliable_text_copy` and `unusable` are caveat-only table qualities and
  must not enter `table_facts`; they must not become report facts.
- The current `600406` real local TXT sample remains a boundary case: business
  composition sections were detected, but revenue, cost, gross margin, revenue
  ratio, YoY, and segment values were not extracted.

Boundaries:

- No direct Research Report V1 rewrite.
- No direct accepted manifest update.
- No fixture write or promotion.
- No candidate generator integration yet.
- No scoring / readiness / P1.1 / regression expected changes.
- No live CNInfo, provider call, token read, network, MCP, OCR
  implementation, PDF extraction implementation, or HTML / DOCX / CSV / Excel
  table reader implementation.
- No trading advice, target price, position sizing, portfolio weighting, or
  technical trading signal.

Local Structured Table Reader Design is recorded in
`docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_LOCAL_STRUCTURED_TABLE_READER_DESIGN.md`.

Next recommended official-disclosure stage:

```text
CSV table facts -> official_disclosure_facts integration design
```

CSV table facts remain separate from Research Report V1.
`official_disclosure_facts.json`, candidate generator, and Research Report V1
integration require separate accepted designs after the retained CSV table
facts runtime baseline.

## 20. Local Structured CSV Sample Runtime Acceptance Boundary

Local Structured CSV Reader implementation, delimiter warning patch, and local
structured CSV sample runtime review are now accepted. The frozen runtime
baseline is summarized in:

```text
docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_LOCAL_STRUCTURED_CSV_SAMPLE_ACCEPTANCE_SUMMARY.md
```

Research Report V1 boundary:

- the CSV sample is ignored runtime output, not a fixture;
- the normalized table review artifact is ignored runtime output;
- no accepted manifest update;
- no Research Report V1 builder, renderer, orchestration, or CLI change;
- no candidate generator integration;
- no report evidence promotion;
- no scoring / readiness / P1.1 / regression expected change.

Runtime table facts were review-only and used `structured_medium`,
`needs_human_review=true`, and caveat
`local_structured_sample_requires_human_review`. They are not Research Report
V1 facts.

Historical next recommended official-disclosure stage remained separate from
Research Report V1:

```text
CSV table facts -> official_disclosure_facts integration design
```

## 21. CSV To Table Facts Integration Design Boundary

The CSV normalized table -> business composition table facts integration design
is now recorded in:

```text
docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_CSV_TO_TABLE_FACTS_INTEGRATION_DESIGN.md
```

Research Report V1 boundary remains unchanged:

- converter design is internal to the Business Composition Table Parser;
- converter output is not report evidence by default;
- no Research Report V1 builder / renderer / orchestration / CLI changes;
- no accepted manifest update;
- no candidate generator integration;
- no fixture promotion;
- no scoring / readiness / P1.1 / regression expected change.

Future Research Report V1 use of table facts requires separate
`official_disclosure_facts.json`, candidate generator, and report L1 evidence
integration designs. The CSV converter implementation and retained sample
runtime review are now accepted, but they do not make table facts Research
Report V1 evidence.

## 22. CSV Table Facts Runtime Acceptance Boundary

CSV table fact converter implementation, Strict Gate Patch, and retained CSV
sample -> table facts runtime review are accepted. The frozen runtime
acceptance closeout is recorded in:

```text
docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_CSV_TABLE_FACTS_RUNTIME_ACCEPTANCE_SUMMARY.md
```

Research Report V1 boundary remains unchanged:

- retained CSV sample is ignored runtime output, not a fixture;
- retained table facts runtime artifact is ignored runtime output;
- table facts are runtime-review-only;
- table facts are L1 official disclosure candidates only in a caveated,
  human-review-required sense;
- no verified fact was generated;
- no `official_disclosure_facts.json` integration yet;
- no Research Report V1 builder, renderer, orchestration, or CLI change;
- no accepted manifest update;
- no fixture promotion;
- no candidate generator integration;
- no report evidence promotion;
- no scoring / readiness / P1.1 / regression expected change.

Runtime records:

- input CSV:
  `output/official_disclosures/local_structured_table_samples/600406_h1_product.csv`;
- runtime artifact:
  `output/official_disclosures/20260529T002922/600406/csv_table_facts_review.json`;
- reader summary: headers = 7, rows = 6, raw strings preserved,
  `delimiter_sniffed`, `unit_not_detected`, `period_not_detected`,
  `classification_hint=product`, `table_quality_hint=structured_medium`, and
  no reader-generated table facts;
- converter summary: explicit `period=2025H1`, `unit=CNY`,
  `denominator=主营业务收入合计`, `classification_type=product`,
  `table_quality=structured_medium`, `needs_human_review=true`, 6
  runtime-review-only revenue facts including `电网智能`, `数能融合`, and
  `合计`, source row / column traceability, warning propagation, and no
  verified facts.

Latest accepted verification results are quoted, not rerun here: targeted
tests `424 passed`, full pytest latest `1072 passed, 1 skipped`, and
regression `passed=47 failed=0 total=47`.

Next recommended official-disclosure stage remains separate from Research
Report V1:

```text
CSV table facts -> official_disclosure_facts integration design
```

Do not directly enter live CNInfo, PDF extraction, DOCX / HTML / Excel reader,
candidate generator integration, Research Report V1 integration, fixture
promotion, accepted manifest update, validator work, scoring / P1.1 changes,
or trading advice.

## 23. Table Facts To Official Disclosure Facts Integration Design Boundary

The table facts -> `official_disclosure_facts.json` integration design is now
recorded in:

```text
docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_TABLE_FACTS_TO_OFFICIAL_DISCLOSURE_FACTS_INTEGRATION_DESIGN.md
```

Research Report V1 boundary remains unchanged:

- this is official disclosure parser artifact assembly, not report assembly;
- table facts remain caveated L1 official disclosure candidates;
- table facts are not report-ready facts;
- no verified fact is generated;
- no Research Report V1 builder, renderer, orchestration, CLI, accepted
  manifest, scoring, readiness, P1.1, or regression expected behavior changes;
- candidate generator integration remains later work;
- Research Report V1 L1 evidence integration remains later work.

Design relationship:

- future implementation may append table-derived facts to
  `official_disclosure_facts.extracted_facts[]`;
- table facts should use the `business_composition.*` namespace;
- optional `source_tables[]` may preserve normalized table trace;
- optional `table_caveats[]` may preserve table-level caveats and failed
  gates;
- `not_for_trading_advice=true` remains mandatory.

Current next recommended official-disclosure stage:

```text
Table facts -> official_disclosure_facts integration implementation
```

Do not directly enter candidate generator integration, Research Report V1
integration, fixture promotion, accepted manifest updates, live CNInfo, PDF
extraction, provider calls, token work, MCP, scoring / P1.1 changes, or trading
advice.
